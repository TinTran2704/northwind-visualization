"""
Set Metabase semantic types for Northwind DW fields.

Idempotent — safe to run multiple times.
Source of truth: docs/02-data-model.md § Metabase Table Metadata Settings
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from scripts.metabase_client import client_from_env

# ---------------------------------------------------------------------------
# Semantic type mapping: {schema}.{table} → {field: metabase_type}
# Metabase type reference: https://www.metabase.com/docs/latest/api/field
# ---------------------------------------------------------------------------
FIELD_TYPES: dict[tuple[str, str], dict[str, str]] = {
    ("warehouse", "fact_sales"): {
        "net_amount":        "type/Currency",
        "unit_price":        "type/Currency",
        "discount_amount":   "type/Currency",
        "freight_allocated": "type/Currency",
        "quantity":          "type/Quantity",
        "order_id":          "type/PK",
    },
    ("warehouse", "dim_customer"): {
        "country_code": "type/Country",
        "city":         "type/City",
        "postal_code":  "type/ZipCode",
        "company_name": "type/Name",
        # phone: Metabase v0.50 removed type/Phone — no semantic type available
    },
    ("warehouse", "dim_geography"): {
        "country_code": "type/Country",
        "country_name": "type/Name",
    },
    ("warehouse", "dim_date"): {
        "full_date": "type/CreationTimestamp",
    },
}


def main() -> None:
    client = client_from_env()
    db_id = client.get_database_id("Northwind DW")

    total = skipped = updated = errors = 0

    for (schema, table_name), field_map in FIELD_TYPES.items():
        print(f"\n── {schema}.{table_name} ──")

        try:
            table_id = client.get_table_id(db_id, table_name, schema)
            existing = client.get_table_fields(table_id)
        except Exception as exc:
            print(f"  [ERROR] Could not load table: {exc}")
            errors += 1
            continue

        for field_name, target_type in field_map.items():
            total += 1
            field_id = existing.get(field_name)

            if field_id is None:
                print(f"  [SKIP]  {field_name!r} — column not found in DB")
                skipped += 1
                continue

            try:
                client.set_field_semantic_type(field_id, target_type)
                print(f"  [OK]    {field_name} → {target_type}")
                updated += 1
            except Exception as exc:
                print(f"  [ERROR] {field_name}: {exc}")
                errors += 1

    print(f"\n{'='*50}")
    print(f"Done — {updated} updated, {skipped} skipped, {errors} errors  (of {total} fields)")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
