"""
Thin wrapper around the Metabase REST API.

Usage:
    from scripts.metabase_client import MetabaseClient, client_from_env
    client = client_from_env()
    db_id = client.find_database("Northwind DW")
"""
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class MetabaseAPIError(Exception):
    def __init__(self, status_code: int, detail: Any, url: str) -> None:
        super().__init__(f"HTTP {status_code} at {url}: {detail}")
        self.status_code = status_code
        self.detail = detail


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class MetabaseClient:
    def __init__(self, url: str, username: str, password: str) -> None:
        self.base_url = url.rstrip("/")
        self.session  = requests.Session()
        self._authenticate(username, password)

    # ── Low-level HTTP ──────────────────────────────────────────────────

    def _authenticate(self, username: str, password: str) -> None:
        url  = f"{self.base_url}/api/session"
        resp = self.session.post(url, json={"username": username, "password": password}, timeout=30)
        logger.info("POST %s → %s", url, resp.status_code)
        self._check(resp)
        self.session.headers["X-Metabase-Session"] = resp.json()["id"]
        logger.info("Authenticated as %s", username)

    def get(self, endpoint: str, **params) -> Any:
        url  = f"{self.base_url}{endpoint}"
        resp = self.session.get(url, params=params or None, timeout=60)
        logger.info("GET %s → %s", url, resp.status_code)
        self._check(resp)
        return resp.json()

    def post(self, endpoint: str, payload: dict) -> Any:
        url  = f"{self.base_url}{endpoint}"
        resp = self.session.post(url, json=payload, timeout=30)
        logger.info("POST %s → %s", url, resp.status_code)
        self._check(resp)
        return resp.json()

    def put(self, endpoint: str, payload: dict) -> Any:
        url  = f"{self.base_url}{endpoint}"
        resp = self.session.put(url, json=payload, timeout=30)
        logger.info("PUT %s → %s", url, resp.status_code)
        self._check(resp)
        return resp.json()

    def _check(self, resp: requests.Response) -> None:
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise MetabaseAPIError(resp.status_code, detail, resp.url)

    # ── High-level helpers ──────────────────────────────────────────────

    def find_database(self, name: str) -> int | None:
        data = self.get("/api/database")
        dbs  = data.get("data", data) if isinstance(data, dict) else data
        for db in dbs:
            if db["name"] == name:
                logger.info("Found database '%s' → id=%s", name, db["id"])
                return db["id"]
        return None

    def find_or_create_collection(self, name: str, parent_id: int | None = None) -> int:
        if parent_id is not None:
            items = self.get(f"/api/collection/{parent_id}/items", models="collection")
            cols  = [i for i in items.get("data", []) if i.get("model") == "collection"]
        else:
            body = self.get("/api/collection")
            cols = body if isinstance(body, list) else body.get("data", [])

        for col in cols:
            if col["name"] == name:
                logger.info("Found collection '%s' → id=%s", name, col["id"])
                return col["id"]

        payload: dict = {"name": name, "color": "#509EE3"}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        result = self.post("/api/collection", payload)
        logger.info("Created collection '%s' → id=%s", name, result["id"])
        return result["id"]

    def find_question(self, name: str, collection_id: int) -> int | None:
        items = self.get(f"/api/collection/{collection_id}/items", models="card")
        for item in items.get("data", []):
            if item.get("model") == "card" and item["name"] == name:
                return item["id"]
        return None

    def find_dashboard(self, name: str, collection_id: int) -> int | None:
        items = self.get(f"/api/collection/{collection_id}/items", models="dashboard")
        for item in items.get("data", []):
            if item.get("model") == "dashboard" and item["name"] == name:
                return item["id"]
        return None

    def create_question(self, payload: dict) -> int:
        result = self.post("/api/card", payload)
        logger.info("Created question '%s' → card_id=%s", payload.get("name"), result["id"])
        return result["id"]

    def create_dashboard(self, name: str, collection_id: int) -> int:
        result = self.post("/api/dashboard", {"name": name, "collection_id": collection_id})
        logger.info("Created dashboard '%s' → id=%s", name, result["id"])
        return result["id"]

    def add_dashcard(
        self,
        dashboard_id: int,
        card_id: int,
        row: int,
        col: int,
        size_x: int,
        size_y: int,
        visualization_settings: dict | None = None,
    ) -> None:
        # Metabase v0.47+: PUT replaces the full cards list
        dash = self.get(f"/api/dashboard/{dashboard_id}")
        kept = [
            {
                "id":                    dc["id"],
                "card_id":               dc.get("card_id"),
                "row":                   dc["row"],
                "col":                   dc["col"],
                "size_x":                dc["size_x"],
                "size_y":                dc["size_y"],
                "series":                dc.get("series", []),
                "parameter_mappings":    dc.get("parameter_mappings", []),
                "visualization_settings": dc.get("visualization_settings", {}),
            }
            for dc in dash.get("dashcards", [])
        ]
        kept.append({
            "id":                    -1,
            "card_id":               card_id,
            "row":                   row,
            "col":                   col,
            "size_x":                size_x,
            "size_y":                size_y,
            "series":                [],
            "parameter_mappings":    [],
            "visualization_settings": visualization_settings or {},
        })
        self.put(f"/api/dashboard/{dashboard_id}/cards", {"cards": kept})
        logger.info("Added card_id=%s to dashboard_id=%s", card_id, dashboard_id)

    def publish_dashboard(self, dashboard_id: int) -> str:
        """Enable public sharing and return the public URL (best-effort)."""
        try:
            result = self.post(f"/api/dashboard/{dashboard_id}/public_link", {})
            uuid   = result.get("uuid", "")
            url    = f"{self.base_url}/public/dashboard/{uuid}"
            logger.info("Published dashboard %s → %s", dashboard_id, url)
            return url
        except MetabaseAPIError as exc:
            logger.warning("Public sharing not enabled (skipping): %s", exc)
            return f"{self.base_url}/dashboard/{dashboard_id}"

    # ── Backward-compat wrappers (for scripts 01, 04, 05) ──────────────

    def get_database_id(self, name: str) -> int:
        result = self.find_database(name)
        if result is None:
            raise ValueError(f"Database '{name}' not found")
        return result

    def get_collection_id(self, name: str) -> int:
        return self.find_or_create_collection(name)

    def get_or_create_subcollection(self, name: str, parent_id: int) -> int:
        return self.find_or_create_collection(name, parent_id=parent_id)

    def list_all_questions(self) -> dict[str, int]:
        cards = self.get("/api/card")
        return {c["name"]: c["id"] for c in (cards if isinstance(cards, list) else [])}

    def list_collection_cards(self, collection_id: int) -> dict[str, int]:
        items = self.get(f"/api/collection/{collection_id}/items", models="card")
        return {i["name"]: i["id"] for i in items.get("data", []) if i.get("model") == "card"}

    def list_collection_dashboards(self, collection_id: int) -> dict[str, int]:
        items = self.get(f"/api/collection/{collection_id}/items", models="dashboard")
        return {i["name"]: i["id"] for i in items.get("data", []) if i.get("model") == "dashboard"}

    def create_native_question(
        self,
        name: str,
        sql: str,
        collection_id: int,
        database_id: int,
        display: str = "table",
    ) -> int:
        return self.create_question({
            "name":          name,
            "display":       display,
            "collection_id": collection_id,
            "dataset_query": {
                "type":     "native",
                "database": database_id,
                "native":   {"query": sql},
            },
            "visualization_settings": {},
        })

    def add_card_to_dashboard(
        self,
        dashboard_id: int,
        card_id: int,
        row: int,
        col: int,
        size_x: int,
        size_y: int,
    ) -> dict:
        self.add_dashcard(dashboard_id, card_id, row, col, size_x, size_y)
        return {}

    def get_dashboard_cards(self, dashboard_id: int) -> list:
        return self.get(f"/api/dashboard/{dashboard_id}").get("dashcards", [])

    def get_table_id(self, database_id: int, table_name: str, schema: str = "warehouse") -> int:
        data = self.get(f"/api/database/{database_id}/metadata")
        for tbl in data.get("tables", []):
            if tbl["name"] == table_name and tbl.get("schema") == schema:
                return tbl["id"]
        raise ValueError(f"Table '{schema}.{table_name}' not found in database {database_id}")

    def get_table_fields(self, table_id: int) -> dict[str, int]:
        data = self.get(f"/api/table/{table_id}/query_metadata")
        return {f["name"]: f["id"] for f in data.get("fields", [])}

    def set_field_semantic_type(self, field_id: int, semantic_type: str) -> dict:
        return self.put(f"/api/field/{field_id}", {"semantic_type": semantic_type})


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def client_from_env() -> MetabaseClient:
    return MetabaseClient(
        url      = os.environ["METABASE_URL"],
        username = os.environ["METABASE_USER"],
        password = os.environ["METABASE_PASSWORD"],
    )
