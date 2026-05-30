"""
Main runner — creates all Collections, Questions, and Dashboards from YAML config.

Steps:
  1. setup_collections  — create/find Northwind + sub-collections
  2. setup_questions    — create questions from config/metabase/questions.yaml
  3. setup_dashboards   — create dashboards from config/metabase/dashboards.yaml

Idempotent: each step checks existence before creating.
State saved to scripts/state.json for debugging.

Run:
    .venv\\Scripts\\python scripts/setup_metabase.py
"""
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import yaml
from dotenv import load_dotenv

load_dotenv()

from scripts.metabase_client import MetabaseClient, MetabaseAPIError, client_from_env

CONFIG_DIR  = Path(__file__).parent.parent / "config" / "metabase"
STATE_PATH  = Path(__file__).parent / "state.json"

QUESTIONS_YAML  = CONFIG_DIR / "questions.yaml"
DASHBOARDS_YAML = CONFIG_DIR / "dashboards.yaml"


# ---------------------------------------------------------------------------
# Step 1 — Collections
# ---------------------------------------------------------------------------

def setup_collections(
    client: MetabaseClient,
    questions_cfg: dict,
    dashboards_cfg: dict,
) -> dict[str, int]:
    """
    Create/find all required collections.
    Returns {collection_name: collection_id}.
    """
    print("\n── Step 1: Collections ──")

    root_name = dashboards_cfg.get("root_collection", "Northwind")
    root_id   = client.find_or_create_collection(root_name)
    print(f"  [OK] {root_name} (root) → id={root_id}")

    # Gather all collection names needed
    needed: set[str] = set()
    for q in questions_cfg.get("questions", []):
        needed.add(q["collection"])
    for d in dashboards_cfg.get("dashboards", []):
        needed.add(d["collection"])

    col_ids: dict[str, int] = {root_name: root_id}
    for name in sorted(needed):
        cid = client.find_or_create_collection(name, parent_id=root_id)
        col_ids[name] = cid
        print(f"  [OK] {root_name}/{name} → id={cid}")

    return col_ids


# ---------------------------------------------------------------------------
# Step 2 — Questions
# ---------------------------------------------------------------------------

def setup_questions(
    client: MetabaseClient,
    db_id: int,
    col_ids: dict[str, int],
    questions_cfg: dict,
) -> dict[str, int]:
    """
    Create questions from YAML.  Skips existing questions (same name + collection).
    Returns {question_name: card_id}.
    """
    print("\n── Step 2: Questions ──")
    question_ids: dict[str, int] = {}
    created = skipped = errors = 0

    for q in questions_cfg.get("questions", []):
        name    = q["name"]
        col_id  = col_ids.get(q["collection"])
        if col_id is None:
            print(f"  [ERROR] Unknown collection '{q['collection']}' for '{name}'")
            errors += 1
            continue

        existing_id = client.find_question(name, col_id)
        if existing_id is not None:
            print(f"  [SKIP]    {name}")
            question_ids[name] = existing_id
            skipped += 1
            continue

        try:
            payload = {
                "name":          name,
                "display":       q.get("display", "table"),
                "collection_id": col_id,
                "dataset_query": {
                    "type":     "native",
                    "database": db_id,
                    "native":   {"query": q["sql"].strip()},
                },
                "visualization_settings": q.get("visualization_settings") or {},
            }
            card_id = client.create_question(payload)
            question_ids[name] = card_id
            print(f"  [CREATED] {name} → card_id={card_id}  ({q.get('display','table')})")
            created += 1
        except MetabaseAPIError as exc:
            print(f"  [ERROR]   {name}: {exc}")
            errors += 1

    print(f"  → {created} created | {skipped} skipped | {errors} errors")
    return question_ids


# ---------------------------------------------------------------------------
# Step 3 — Dashboards
# ---------------------------------------------------------------------------

def setup_dashboards(
    client: MetabaseClient,
    question_ids: dict[str, int],
    col_ids: dict[str, int],
    dashboards_cfg: dict,
) -> dict[str, int]:
    """
    Create dashboards and add cards per YAML layout.
    Skips dashboards that already exist.
    Returns {dashboard_name: dashboard_id}.
    """
    print("\n── Step 3: Dashboards ──")
    dashboard_ids: dict[str, int] = {}
    d_created = d_skipped = c_added = c_warn = 0

    for dash in dashboards_cfg.get("dashboards", []):
        name   = dash["name"]
        col_id = col_ids.get(dash["collection"])
        if col_id is None:
            print(f"\n  [ERROR] Unknown collection '{dash['collection']}' for dashboard '{name}'")
            continue

        existing_id = client.find_dashboard(name, col_id)
        if existing_id is not None:
            print(f"\n  [SKIP]  Dashboard '{name}' → id={existing_id}")
            dashboard_ids[name] = existing_id
            d_skipped += 1
            continue

        try:
            dash_id = client.create_dashboard(name, col_id)
            dashboard_ids[name] = dash_id
            print(f"\n  [NEW]   Dashboard '{name}' → id={dash_id}")
            d_created += 1
        except MetabaseAPIError as exc:
            print(f"\n  [ERROR] Dashboard '{name}': {exc}")
            continue

        current_card_ids: set[int] = set()

        for card_spec in dash.get("cards", []):
            q_name  = card_spec["question"]
            card_id = question_ids.get(q_name)

            if card_id is None:
                print(f"    [WARN] Question not found: '{q_name}'")
                c_warn += 1
                continue

            if card_id in current_card_ids:
                continue   # same card already added this run

            try:
                client.add_dashcard(
                    dashboard_id = dash_id,
                    card_id      = card_id,
                    row          = card_spec["row"],
                    col          = card_spec["col"],
                    size_x       = card_spec["size_x"],
                    size_y       = card_spec["size_y"],
                )
                current_card_ids.add(card_id)
                print(f"    [ADD]  {q_name}  [{card_spec['size_x']}x{card_spec['size_y']} @ row={card_spec['row']},col={card_spec['col']}]")
                c_added += 1
            except MetabaseAPIError as exc:
                print(f"    [ERROR] {q_name}: {exc}")
                c_warn += 1

        client.publish_dashboard(dash_id)

    print(f"\n  → {d_created} dashboards created | {d_skipped} skipped")
    print(f"  → {c_added} cards added | {c_warn} warnings")
    return dashboard_ids


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def save_state(col_ids: dict, q_ids: dict, d_ids: dict) -> None:
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collections":  col_ids,
        "questions":    q_ids,
        "dashboards":   d_ids,
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nState saved → {STATE_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    questions_cfg  = yaml.safe_load(QUESTIONS_YAML.read_text(encoding="utf-8"))
    dashboards_cfg = yaml.safe_load(DASHBOARDS_YAML.read_text(encoding="utf-8"))

    client = client_from_env()

    db_id = client.find_database("Northwind DW")
    if db_id is None:
        print("[ERROR] Database 'Northwind DW' not found in Metabase.")
        print("  → Go to http://localhost:3000/admin/databases/create and add PostgreSQL connection.")
        sys.exit(1)
    print(f"\nDatabase 'Northwind DW' → id={db_id}")

    col_ids      = setup_collections(client, questions_cfg, dashboards_cfg)
    question_ids = setup_questions(client, db_id, col_ids, questions_cfg)
    dashboard_ids = setup_dashboards(client, question_ids, col_ids, dashboards_cfg)

    save_state(col_ids, question_ids, dashboard_ids)

    total_q = len(questions_cfg.get("questions", []))
    total_d = len(dashboards_cfg.get("dashboards", []))
    print(f"\n{'='*55}")
    print(f"Done!  {total_q} questions + {total_d} dashboards configured.")
    print(f"Open http://localhost:3000 to verify.")


if __name__ == "__main__":
    main()
