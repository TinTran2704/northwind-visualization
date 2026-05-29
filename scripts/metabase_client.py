"""
Metabase REST API client for automating Questions and Dashboards.
"""
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class MetabaseClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._authenticate(username, password)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _authenticate(self, username: str, password: str) -> None:
        url = f"{self.base_url}/api/session"
        payload = {"username": username, "password": password}
        logger.info("POST %s (authenticating as %s)", url, username)
        resp = self.session.post(url, json=payload, timeout=30)
        self._raise_for_status(resp, "Authentication failed")
        token = resp.json()["id"]
        self.session.headers.update({"X-Metabase-Session": token})
        logger.info("Authenticated — session token acquired")

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    def get_database_id(self, name: str) -> int:
        url = f"{self.base_url}/api/database"
        logger.info("GET %s", url)
        resp = self.session.get(url, timeout=30)
        self._raise_for_status(resp, "Failed to list databases")
        databases = resp.json().get("data", resp.json())
        for db in databases:
            if db["name"] == name:
                logger.info("Found database '%s' → id=%s", name, db["id"])
                return db["id"]
        raise ValueError(f"Database '{name}' not found. Available: {[d['name'] for d in databases]}")

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def get_collection_id(self, name: str) -> int:
        url = f"{self.base_url}/api/collection"
        logger.info("GET %s", url)
        resp = self.session.get(url, timeout=30)
        self._raise_for_status(resp, "Failed to list collections")
        body = resp.json()
        for col in (body if isinstance(body, list) else body.get("data", [])):
            if col["name"] == name:
                logger.info("Found collection '%s' → id=%s", name, col["id"])
                return col["id"]
        logger.info("Collection '%s' not found — creating it", name)
        return self._create_collection(name)

    def get_or_create_subcollection(self, name: str, parent_id: int) -> int:
        """Find a child collection by name under parent_id, creating it if absent."""
        url = f"{self.base_url}/api/collection/{parent_id}/items"
        logger.info("GET %s (looking for sub-collection '%s')", url, name)
        resp = self.session.get(url, params={"models": "collection"}, timeout=30)
        self._raise_for_status(resp, f"Failed to list items in collection {parent_id}")
        for item in resp.json().get("data", []):
            if item.get("model") == "collection" and item["name"] == name:
                logger.info("Found sub-collection '%s' → id=%s", name, item["id"])
                return item["id"]
        return self._create_collection(name, parent_id=parent_id)

    def list_collection_cards(self, collection_id: int) -> dict[str, int]:
        """Return {card_name: card_id} for all cards in a collection."""
        url = f"{self.base_url}/api/collection/{collection_id}/items"
        logger.info("GET %s (list cards)", url)
        resp = self.session.get(url, params={"models": "card"}, timeout=30)
        self._raise_for_status(resp, f"Failed to list cards in collection {collection_id}")
        return {
            item["name"]: item["id"]
            for item in resp.json().get("data", [])
            if item.get("model") == "card"
        }

    def _create_collection(self, name: str, parent_id: int | None = None) -> int:
        url = f"{self.base_url}/api/collection"
        payload: dict = {"name": name, "color": "#509EE3"}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        logger.info("POST %s (create collection '%s' parent=%s)", url, name, parent_id)
        resp = self.session.post(url, json=payload, timeout=30)
        self._raise_for_status(resp, f"Failed to create collection '{name}'")
        col_id = resp.json()["id"]
        logger.info("Created collection '%s' → id=%s", name, col_id)
        return col_id

    # ------------------------------------------------------------------
    # Questions (Cards)
    # ------------------------------------------------------------------

    def create_native_question(
        self,
        name: str,
        sql: str,
        collection_id: int,
        database_id: int,
        display: str = "table",
    ) -> int:
        url = f"{self.base_url}/api/card"
        payload = {
            "name": name,
            "display": display,
            "collection_id": collection_id,
            "dataset_query": {
                "type": "native",
                "database": database_id,
                "native": {"query": sql},
            },
            "visualization_settings": {},
        }
        logger.info("POST %s (create question '%s')", url, name)
        resp = self.session.post(url, json=payload, timeout=30)
        self._raise_for_status(resp, f"Failed to create question '{name}'")
        card_id = resp.json()["id"]
        logger.info("Created question '%s' → card_id=%s", name, card_id)
        return card_id

    def update_question(self, card_id: int, **kwargs) -> dict:
        url = f"{self.base_url}/api/card/{card_id}"
        logger.info("PUT %s (update card_id=%s)", url, card_id)
        resp = self.session.put(url, json=kwargs, timeout=30)
        self._raise_for_status(resp, f"Failed to update card {card_id}")
        logger.info("Updated card_id=%s", card_id)
        return resp.json()

    # ------------------------------------------------------------------
    # Dashboards
    # ------------------------------------------------------------------

    def create_dashboard(self, name: str, collection_id: int) -> int:
        url = f"{self.base_url}/api/dashboard"
        payload = {"name": name, "collection_id": collection_id}
        logger.info("POST %s (create dashboard '%s')", url, name)
        resp = self.session.post(url, json=payload, timeout=30)
        self._raise_for_status(resp, f"Failed to create dashboard '{name}'")
        dashboard_id = resp.json()["id"]
        logger.info("Created dashboard '%s' → dashboard_id=%s", name, dashboard_id)
        return dashboard_id

    def add_card_to_dashboard(
        self,
        dashboard_id: int,
        card_id: int,
        row: int,
        col: int,
        size_x: int,
        size_y: int,
    ) -> dict:
        url = f"{self.base_url}/api/dashboard/{dashboard_id}/cards"
        payload = {
            "cardId": card_id,
            "row": row,
            "col": col,
            "size_x": size_x,
            "size_y": size_y,
        }
        logger.info(
            "POST %s (add card_id=%s to dashboard_id=%s at row=%s col=%s)",
            url, card_id, dashboard_id, row, col,
        )
        resp = self.session.post(url, json=payload, timeout=30)
        self._raise_for_status(resp, f"Failed to add card {card_id} to dashboard {dashboard_id}")
        logger.info("Added card_id=%s to dashboard_id=%s", card_id, dashboard_id)
        return resp.json()

    # ------------------------------------------------------------------
    # Table / Field lookup
    # ------------------------------------------------------------------

    def get_table_fields(self, table_id: int) -> dict[str, int]:
        """Return {field_name: field_id} for a given table."""
        url = f"{self.base_url}/api/table/{table_id}/query_metadata"
        logger.info("GET %s", url)
        resp = self.session.get(url, timeout=30)
        self._raise_for_status(resp, f"Failed to get fields for table {table_id}")
        return {f["name"]: f["id"] for f in resp.json().get("fields", [])}

    def get_table_id(self, database_id: int, table_name: str, schema: str = "warehouse") -> int:
        """Find table_id by name + schema inside a database."""
        url = f"{self.base_url}/api/database/{database_id}/metadata"
        logger.info("GET %s (looking for %s.%s)", url, schema, table_name)
        resp = self.session.get(url, timeout=60)
        self._raise_for_status(resp, f"Failed to get metadata for database {database_id}")
        for tbl in resp.json().get("tables", []):
            if tbl["name"] == table_name and tbl.get("schema") == schema:
                logger.info("Found table %s.%s → id=%s", schema, table_name, tbl["id"])
                return tbl["id"]
        raise ValueError(f"Table '{schema}.{table_name}' not found in database {database_id}")

    # ------------------------------------------------------------------
    # Field metadata
    # ------------------------------------------------------------------

    def set_field_semantic_type(self, field_id: int, semantic_type: str) -> dict:
        url = f"{self.base_url}/api/field/{field_id}"
        payload = {"semantic_type": semantic_type}
        logger.info("PUT %s (field_id=%s → semantic_type=%s)", url, field_id, semantic_type)
        resp = self.session.put(url, json=payload, timeout=30)
        self._raise_for_status(resp, f"Failed to set semantic type for field {field_id}")
        logger.info("Updated field_id=%s semantic_type=%s", field_id, semantic_type)
        return resp.json()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(resp: requests.Response, message: str) -> None:
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise requests.HTTPError(
                f"{message} — HTTP {resp.status_code}: {detail}",
                response=resp,
            ) from exc


def client_from_env() -> MetabaseClient:
    """Convenience factory that reads credentials from environment variables."""
    return MetabaseClient(
        base_url=os.environ["METABASE_URL"],
        username=os.environ["METABASE_USER"],
        password=os.environ["METABASE_PASSWORD"],
    )
