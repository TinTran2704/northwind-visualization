"""
Import Questions and Dashboards from JSON exports into a fresh Metabase instance.

Reads from:
  metabase-config/exports/questions/*.json
  metabase-config/exports/dashboards/*.json

Idempotent — skips questions/dashboards that already exist by name in the same collection.
Run: python scripts/05_import_config.py
"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from scripts.metabase_client import client_from_env

EXPORTS_ROOT = Path(__file__).parent.parent / "metabase-config" / "exports"


def resolve_collection(client, collection_path: str, col_cache: dict) -> int:
    """
    Given 'Northwind/Sales', get or create each level and return leaf collection_id.
    Uses a local cache to avoid repeated API calls.
    """
    if collection_path in col_cache:
        return col_cache[collection_path]

    parts = [p.strip() for p in collection_path.split("/")]
    parent_id: int | None = None

    for i, part in enumerate(parts):
        path_so_far = "/".join(parts[: i + 1])
        if path_so_far in col_cache:
            parent_id = col_cache[path_so_far]
            continue

        if parent_id is None:
            # Top-level: use get_collection_id (creates if missing)
            cid = client.get_collection_id(part)
        else:
            cid = client.get_or_create_subcollection(part, parent_id=parent_id)

        col_cache[path_so_far] = cid
        parent_id = cid

    col_cache[collection_path] = parent_id  # type: ignore[assignment]
    return parent_id  # type: ignore[return-value]


def import_questions(client, db_id: int) -> tuple[int, int, int]:
    q_dir = EXPORTS_ROOT / "questions"
    if not q_dir.exists():
        print("  [WARN] No questions export directory found.")
        return 0, 0, 0

    files   = sorted(q_dir.glob("*.json"))
    col_cache: dict = {}
    created = skipped = errors = 0

    print(f"\n── Importing {len(files)} Questions ──")

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        name     = data["name"]
        col_path = data["collection_path"]
        sql      = data["sql"]
        display  = data.get("display", "table")

        try:
            col_id   = resolve_collection(client, col_path, col_cache)
            existing = client.list_collection_cards(col_id)

            if name in existing:
                print(f"  [SKIP]    {name}")
                skipped += 1
            else:
                card_id = client.create_native_question(
                    name=name, sql=sql,
                    collection_id=col_id,
                    database_id=db_id,
                    display=display,
                )
                print(f"  [CREATED] {name} → card_id={card_id}")
                created += 1
        except Exception as exc:
            print(f"  [ERROR]   {name}: {exc}")
            errors += 1

    return created, skipped, errors


def import_dashboards(client) -> tuple[int, int, int]:
    d_dir = EXPORTS_ROOT / "dashboards"
    if not d_dir.exists():
        print("  [WARN] No dashboards export directory found.")
        return 0, 0, 0

    files   = sorted(d_dir.glob("*.json"))
    col_cache: dict = {}
    created = skipped = errors = 0

    print(f"\n── Importing {len(files)} Dashboards ──")

    # Build question name → id lookup
    all_questions = client.list_all_questions()

    for f in files:
        data     = json.loads(f.read_text(encoding="utf-8"))
        name     = data["name"]
        col_path = data["collection_path"]

        try:
            col_id  = resolve_collection(client, col_path, col_cache)
            existing = client.list_collection_dashboards(col_id)

            if name in existing:
                print(f"\n  [SKIP]  Dashboard '{name}'")
                skipped += 1
                continue

            dash_id = client.create_dashboard(name, col_id)
            print(f"\n  [NEW]   Dashboard '{name}' → dashboard_id={dash_id}")
            created += 1

            for card_spec in data.get("cards", []):
                q_name  = card_spec["question_name"]
                card_id = all_questions.get(q_name)
                if card_id is None:
                    print(f"    [WARN] Question not found: '{q_name}'")
                    errors += 1
                    continue
                client.add_card_to_dashboard(
                    dashboard_id = dash_id,
                    card_id      = card_id,
                    row          = card_spec["row"],
                    col          = card_spec["col"],
                    size_x       = card_spec["size_x"],
                    size_y       = card_spec["size_y"],
                )
                print(f"    [ADD]  {q_name}")

        except Exception as exc:
            print(f"  [ERROR] '{name}': {exc}")
            errors += 1

    return created, skipped, errors


def main() -> None:
    client = client_from_env()

    q_dir = EXPORTS_ROOT / "questions"
    d_dir = EXPORTS_ROOT / "dashboards"
    q_files = list(q_dir.glob("*.json")) if q_dir.exists() else []
    d_files = list(d_dir.glob("*.json")) if d_dir.exists() else []

    if not q_files and not d_files:
        print(f"[ERROR] No export files found in {EXPORTS_ROOT}")
        print("Run python scripts/04_export_config.py first.")
        sys.exit(1)

    db_id = client.get_database_id("Northwind DW")

    qc, qs, qe = import_questions(client, db_id)
    dc, ds, de = import_dashboards(client)

    print(f"\n{'='*55}")
    print(f"Questions  — {qc} created | {qs} skipped | {qe} errors")
    print(f"Dashboards — {dc} created | {ds} skipped | {de} errors")

    if qe + de:
        sys.exit(1)


if __name__ == "__main__":
    main()
