"""
Create 5 Dashboards per docs/04-dashboards.md specs.

Idempotent — existing dashboards (matched by name in collection) are skipped.
State saved to metabase-config/exports/dashboard_state.json for debugging.
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

# ---------------------------------------------------------------------------
# Dashboard specs
# Each card: {question, row, col, size_x, size_y}
# Grid is 12 columns wide; size_y unit ≈ 1 row of ~100px
# ---------------------------------------------------------------------------

DASHBOARDS = [
    {
        "name": "Sales Overview",
        "collection": "Executive",        # created as sub of Northwind
        "cards": [
            # Row 0 — full-width revenue trend
            {"question": "Q1: Total Revenue by Month",      "row": 0,  "col": 0, "size_x": 12, "size_y": 4},
            # Row 4 — category + quarterly side by side
            {"question": "Q2: Revenue by Category",         "row": 4,  "col": 0, "size_x":  6, "size_y": 4},
            {"question": "Q4: Sales by Quarter",            "row": 4,  "col": 6, "size_x":  6, "size_y": 4},
            # Row 8 — top customers table
            {"question": "Q5: Average Order Value Trend",   "row": 8,  "col": 0, "size_x":  6, "size_y": 4},
            {"question": "Q3: Top 10 Customers",            "row": 8,  "col": 6, "size_x":  6, "size_y": 4},
        ],
    },
    {
        "name": "Product Performance",
        "collection": "Sales",
        "cards": [
            # Row 0 — category bar + pie
            {"question": "Q2: Revenue by Category",         "row": 0,  "col": 0, "size_x":  6, "size_y": 4},
            {"question": "Q7: Category Breakdown — Pie", "row": 0, "col": 6, "size_x":  6, "size_y": 4},
            # Row 4 — top products
            {"question": "Q6: Top 10 Products by Revenue",  "row": 4,  "col": 0, "size_x": 12, "size_y": 6},
            # Row 10 — discount analysis
            {"question": "Q8: Discount Analysis by Category", "row": 10, "col": 0, "size_x": 12, "size_y": 4},
        ],
    },
    {
        "name": "Customer Geography",
        "collection": "Marketing",        # created as sub of Northwind
        "cards": [
            # Row 0 — map full width
            {"question": "Q9: Revenue by Country — Map", "row": 0, "col": 0, "size_x": 12, "size_y": 6},
            # Row 6 — region bar + top customers
            {"question": "Q10: Revenue by Region",          "row": 6,  "col": 0, "size_x":  6, "size_y": 4},
            {"question": "Q3: Top 10 Customers",            "row": 6,  "col": 6, "size_x":  6, "size_y": 4},
        ],
    },
    {
        "name": "Employee Performance",
        "collection": "Sales",
        "cards": [
            # Full-width sales rep table
            {"question": "Q11: Sales Rep Performance",      "row": 0,  "col": 0, "size_x": 12, "size_y": 8},
        ],
    },
    {
        "name": "ETL Pipeline Health",
        "collection": "Operations",
        "cards": [
            # ETL run history + shipping
            {"question": "Q12: ETL Pipeline Health",        "row": 0,  "col": 0, "size_x": 12, "size_y": 6},
            {"question": "Q13: Shipping Time Analysis",     "row": 6,  "col": 0, "size_x": 12, "size_y": 4},
        ],
    },
]

# Collections that need to exist (besides the 5 already created by script 02)
EXTRA_COLLECTIONS = ["Executive", "Marketing"]


def main() -> None:
    client = client_from_env()

    # ── Question lookup ───────────────────────────────────────────────
    print("Loading all questions...")
    all_questions = client.list_all_questions()
    print(f"  Found {len(all_questions)} questions\n")

    # ── Collection setup ──────────────────────────────────────────────
    root_id = client.get_collection_id("Northwind")

    # Build collection name → id map from all sub-collections
    print("── Resolving collections ──")
    col_ids: dict[str, int] = {}

    # Fetch all current sub-collections of Northwind
    resp_cols = client.session.get(
        f"{client.base_url}/api/collection/{root_id}/items",
        params={"models": "collection"},
        timeout=30,
    )
    for item in resp_cols.json().get("data", []):
        if item.get("model") == "collection":
            col_ids[item["name"]] = item["id"]

    # Create any missing ones
    needed = {d["collection"] for d in DASHBOARDS}
    for name in sorted(needed):
        if name not in col_ids:
            cid = client.get_or_create_subcollection(name, parent_id=root_id)
            col_ids[name] = cid
            print(f"  [NEW]   {name} → collection_id={cid}")
        else:
            print(f"  [OK]    {name} → collection_id={col_ids[name]}")

    # ── Dashboard creation ────────────────────────────────────────────
    state: dict = {"dashboards": []}
    created_count = skipped_count = card_added = card_skipped = errors = 0

    for spec in DASHBOARDS:
        col_id = col_ids[spec["collection"]]
        existing_dashes = client.list_collection_dashboards(col_id)

        if spec["name"] in existing_dashes:
            dashboard_id = existing_dashes[spec["name"]]
            print(f"\n  [SKIP]  Dashboard '{spec['name']}' already exists → id={dashboard_id}")
            skipped_count += 1
        else:
            dashboard_id = client.create_dashboard(spec["name"], col_id)
            print(f"\n  [NEW]   Dashboard '{spec['name']}' → dashboard_id={dashboard_id}")
            created_count += 1

        # ── Add cards ────────────────────────────────────────────────
        current_cards   = client.get_dashboard_cards(dashboard_id)
        current_card_ids = {dc.get("card_id") for dc in current_cards}
        dashboard_state  = {"name": spec["name"], "id": dashboard_id, "cards": []}

        for card_spec in spec["cards"]:
            q_name  = card_spec["question"]
            card_id = all_questions.get(q_name)

            if card_id is None:
                print(f"    [WARN]  Question not found: '{q_name}' — skipping")
                errors += 1
                continue

            if card_id in current_card_ids:
                print(f"    [SKIP]  {q_name}")
                card_skipped += 1
            else:
                try:
                    client.add_card_to_dashboard(
                        dashboard_id = dashboard_id,
                        card_id      = card_id,
                        row          = card_spec["row"],
                        col          = card_spec["col"],
                        size_x       = card_spec["size_x"],
                        size_y       = card_spec["size_y"],
                    )
                    print(f"    [ADD]   {q_name}  [{card_spec['size_x']}x{card_spec['size_y']} @ row={card_spec['row']},col={card_spec['col']}]")
                    card_added += 1
                    current_card_ids.add(card_id)   # prevent duplicate within same run
                except Exception as exc:
                    print(f"    [ERROR] {q_name}: {exc}")
                    errors += 1

            dashboard_state["cards"].append({
                "question": q_name,
                "card_id":  card_id,
                "row":      card_spec["row"],
                "col":      card_spec["col"],
                "size_x":   card_spec["size_x"],
                "size_y":   card_spec["size_y"],
            })

        state["dashboards"].append(dashboard_state)

    # ── Save state ────────────────────────────────────────────────────
    state_path = Path(__file__).parent.parent / "metabase-config" / "exports" / "dashboard_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nState saved → {state_path}")

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"Dashboards — {created_count} created | {skipped_count} skipped")
    print(f"Cards      — {card_added} added    | {card_skipped} skipped | {errors} errors")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
