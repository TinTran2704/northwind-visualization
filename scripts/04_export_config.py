"""
Export all Questions and Dashboards to portable JSON files.

Output:
  metabase-config/exports/questions/{collection_slug}__{question_slug}.json
  metabase-config/exports/dashboards/{collection_slug}__{dashboard_slug}.json

JSON stores only data needed to recreate — no internal Metabase IDs.
Run: python scripts/04_export_config.py
"""
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from scripts.metabase_client import client_from_env

EXPORTS_ROOT = Path(__file__).parent.parent / "metabase-config" / "exports"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text.strip("_")


def get_collection_path(client, collection_id: int | None, cache: dict) -> str:
    """Resolve collection_id → 'Northwind/Sales' style path."""
    if collection_id is None:
        return "Our analytics"
    if collection_id in cache:
        return cache[collection_id]

    resp = client.session.get(f"{client.base_url}/api/collection/{collection_id}", timeout=30)
    resp.raise_for_status()
    col = resp.json()
    name = col["name"]
    parent_id = col.get("parent_id")

    if parent_id:
        parent_path = get_collection_path(client, parent_id, cache)
        path = f"{parent_path}/{name}"
    else:
        path = name

    cache[collection_id] = path
    return path


def export_questions(client, db_name: str) -> int:
    out_dir = EXPORTS_ROOT / "questions"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n── Exporting Questions ──")
    all_cards = client.list_all_questions()
    col_cache: dict = {}
    count = 0

    for name, card_id in all_cards.items():
        # Skip sample/internal questions
        if name.startswith("__"):
            continue

        resp = client.session.get(f"{client.base_url}/api/card/{card_id}", timeout=30)
        resp.raise_for_status()
        card = resp.json()

        # Only export native SQL questions
        if card.get("query_type") != "native":
            continue

        col_id   = card.get("collection_id")
        col_path = get_collection_path(client, col_id, col_cache)
        col_slug = slugify(col_path.split("/")[-1])   # last segment only
        q_slug   = slugify(name)
        sql      = card.get("dataset_query", {}).get("native", {}).get("query", "")

        payload = {
            "name":            name,
            "collection_path": col_path,
            "database_name":   db_name,
            "sql":             sql,
            "display":         card.get("display", "table"),
            "description":     card.get("description") or "",
        }

        filename = out_dir / f"{col_slug}__{q_slug}.json"
        filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] {filename.name}")
        count += 1

    return count


def export_dashboards(client) -> int:
    out_dir = EXPORTS_ROOT / "dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n── Exporting Dashboards ──")
    col_cache: dict = {}

    # List all dashboards via /api/dashboard (returns dashboards visible to current user)
    resp = client.session.get(f"{client.base_url}/api/dashboard", timeout=30)
    resp.raise_for_status()
    body = resp.json()
    all_dashes = body if isinstance(body, list) else body.get("data", [])
    count = 0

    for item in all_dashes:
        dash_id = item["id"]
        resp2 = client.session.get(f"{client.base_url}/api/dashboard/{dash_id}", timeout=30)
        resp2.raise_for_status()
        dash = resp2.json()

        col_id   = dash.get("collection_id")
        col_path = get_collection_path(client, col_id, col_cache)
        col_slug = slugify(col_path.split("/")[-1])
        d_slug   = slugify(dash["name"])

        cards = []
        for dc in dash.get("dashcards", []):
            card = dc.get("card") or {}
            if not card:
                continue
            cards.append({
                "question_name": card.get("name", ""),
                "row":    dc["row"],
                "col":    dc["col"],
                "size_x": dc["size_x"],
                "size_y": dc["size_y"],
            })

        payload = {
            "name":            dash["name"],
            "collection_path": col_path,
            "description":     dash.get("description") or "",
            "cards":           cards,
        }

        filename = out_dir / f"{col_slug}__{d_slug}.json"
        filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] {filename.name}  ({len(cards)} cards)")
        count += 1

    return count


def main() -> None:
    client  = client_from_env()
    db_name = "Northwind DW"

    q_count  = export_questions(client, db_name)
    d_count  = export_dashboards(client)

    print(f"\n{'='*55}")
    print(f"Exported {q_count} questions  →  metabase-config/exports/questions/")
    print(f"Exported {d_count} dashboards →  metabase-config/exports/dashboards/")


if __name__ == "__main__":
    main()
