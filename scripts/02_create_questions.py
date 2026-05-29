"""
Create Collections + all 13 Questions from docs/03-questions.md.

Idempotent — safe to run multiple times.
Existing questions (matched by name inside the same collection) are skipped.
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
# Question definitions — order, name, collection, SQL, display
# ---------------------------------------------------------------------------

QUESTIONS = [
    # ── Sales ────────────────────────────────────────────────────────────
    {
        "name": "Q1: Total Revenue by Month",
        "collection": "Sales",
        "display": "line",
        "sql": """\
SELECT
    order_year,
    order_month,
    order_month_name,
    SUM(net_amount) AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_month, order_month_name
ORDER BY order_year, order_month""",
    },
    {
        "name": "Q2: Revenue by Category",
        "collection": "Sales",
        "display": "bar",
        "sql": """\
SELECT
    category_name,
    SUM(net_amount)      AS total_revenue,
    SUM(quantity)        AS total_units,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY total_revenue DESC""",
    },
    {
        "name": "Q3: Top 10 Customers",
        "collection": "Sales",
        "display": "table",
        "sql": """\
SELECT
    customer_code,
    customer_name,
    customer_country,
    SUM(net_amount)          AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM analytics_marts.mart_sales_wide
GROUP BY customer_code, customer_name, customer_country
ORDER BY total_revenue DESC
LIMIT 10""",
    },
    {
        "name": "Q4: Sales by Quarter",
        "collection": "Sales",
        "display": "bar",
        "sql": """\
SELECT
    order_year,
    order_quarter,
    CONCAT(order_year, ' Q', order_quarter) AS quarter_label,
    SUM(net_amount) AS total_revenue
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_quarter
ORDER BY order_year, order_quarter""",
    },
    {
        "name": "Q5: Average Order Value Trend",
        "collection": "Sales",
        "display": "line",
        "sql": """\
SELECT
    order_year,
    order_month,
    order_month_name,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_month, order_month_name
ORDER BY order_year, order_month""",
    },
    # ── Products ─────────────────────────────────────────────────────────
    {
        "name": "Q6: Top 10 Products by Revenue",
        "collection": "Products",
        "display": "table",
        "sql": """\
SELECT
    product_name,
    category_name,
    SUM(quantity)       AS total_units,
    SUM(net_amount)     AS total_revenue,
    ROUND(AVG(unit_price), 2) AS avg_price,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM analytics_marts.mart_sales_wide
GROUP BY product_name, category_name
ORDER BY total_revenue DESC
LIMIT 10""",
    },
    {
        "name": "Q7: Category Breakdown — Pie",
        "collection": "Products",
        "display": "pie",
        "sql": """\
SELECT
    category_name,
    SUM(net_amount) AS revenue,
    ROUND(SUM(net_amount) * 100.0 / SUM(SUM(net_amount)) OVER (), 1) AS pct
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY revenue DESC""",
    },
    {
        "name": "Q8: Discount Analysis by Category",
        "collection": "Products",
        "display": "table",
        "sql": """\
SELECT
    category_name,
    ROUND(AVG(discount) * 100, 1)   AS avg_discount_pct,
    ROUND(MIN(discount) * 100, 1)   AS min_discount_pct,
    ROUND(MAX(discount) * 100, 1)   AS max_discount_pct,
    SUM(net_amount)                  AS total_revenue,
    SUM(quantity * unit_price) - SUM(net_amount) AS total_discount_given
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY avg_discount_pct DESC""",
    },
    # ── Geography ────────────────────────────────────────────────────────
    {
        "name": "Q9: Revenue by Country — Map",
        "collection": "Geography",
        "display": "map",
        "sql": """\
SELECT
    customer_country         AS country_code,
    customer_country_name    AS country,
    customer_region          AS region,
    SUM(net_amount)          AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY customer_country, customer_country_name, customer_region
ORDER BY total_revenue DESC""",
    },
    {
        "name": "Q10: Revenue by Region",
        "collection": "Geography",
        "display": "bar",
        "sql": """\
SELECT
    customer_region,
    SUM(net_amount)          AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_code) AS unique_customers
FROM analytics_marts.mart_sales_wide
GROUP BY customer_region
ORDER BY total_revenue DESC""",
    },
    # ── Employees ────────────────────────────────────────────────────────
    {
        "name": "Q11: Sales Rep Performance",
        "collection": "Employees",
        "display": "table",
        "sql": """\
SELECT
    employee_name,
    employee_title,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(net_amount)          AS total_revenue,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT customer_code) AS unique_customers
FROM analytics_marts.mart_sales_wide
GROUP BY employee_name, employee_title
ORDER BY total_revenue DESC""",
    },
    # ── Operations ───────────────────────────────────────────────────────
    {
        "name": "Q12: ETL Pipeline Health",
        "collection": "Operations",
        "display": "table",
        "sql": """\
SELECT
    batch_id,
    status,
    started_at,
    ended_at,
    ROUND(EXTRACT(EPOCH FROM (ended_at - started_at)), 1) AS duration_sec,
    rows_extracted,
    rows_loaded,
    rows_rejected,
    error_summary
FROM metadata.etl_runs
ORDER BY started_at DESC
LIMIT 20""",
    },
    {
        "name": "Q13: Shipping Time Analysis",
        "collection": "Operations",
        "display": "table",
        "sql": """\
SELECT
    shipper_name,
    AVG(
        CASE
            WHEN shipped_date_sk IS NOT NULL AND shipped_date_sk != 19000101
            THEN (
                SELECT EXTRACT(DAY FROM (s_date.full_date - o_date.full_date))
                FROM warehouse.dim_date s_date, warehouse.dim_date o_date
                WHERE s_date.date_sk = f.shipped_date_sk
                  AND o_date.date_sk = f.order_date_sk
            )
        END
    ) AS avg_shipping_days,
    COUNT(DISTINCT f.order_id) AS order_count
FROM warehouse.fact_sales f
JOIN warehouse.dim_shipper s ON f.shipper_sk = s.shipper_sk
WHERE s.shipper_sk != -1
GROUP BY s.company_name""",
    },
]

FOLDER_NAMES = ["Sales", "Products", "Geography", "Employees", "Operations"]


def main() -> None:
    client = client_from_env()
    db_id  = client.get_database_id("Northwind DW")

    # Root collection created in test_connection
    root_id = client.get_collection_id("Northwind")

    # ── Step 1: create sub-collections ───────────────────────────────────
    print("\n── Creating sub-collections ──")
    folder_ids: dict[str, int] = {}
    for folder in FOLDER_NAMES:
        cid = client.get_or_create_subcollection(folder, parent_id=root_id)
        folder_ids[folder] = cid
        print(f"  [OK] {folder} → collection_id={cid}")

    # ── Step 2: create questions ──────────────────────────────────────────
    print("\n── Creating questions ──")
    created = skipped = errors = 0

    for q in QUESTIONS:
        col_id     = folder_ids[q["collection"]]
        existing   = client.list_collection_cards(col_id)

        if q["name"] in existing:
            print(f"  [SKIP]    {q['name']}")
            skipped += 1
            continue

        try:
            card_id = client.create_native_question(
                name          = q["name"],
                sql           = q["sql"],
                collection_id = col_id,
                database_id   = db_id,
                display       = q["display"],
            )
            print(f"  [CREATED] {q['name']} → card_id={card_id}  ({q['display']})")
            created += 1
        except Exception as exc:
            print(f"  [ERROR]   {q['name']}: {exc}")
            errors += 1

    # ── Summary ───────────────────────────────────────────────────────────
    total = len(QUESTIONS)
    print(f"\n{'='*55}")
    print(f"Questions — {created} created | {skipped} skipped | {errors} errors  (of {total})")
    print(f"Collections — {len(folder_ids)} folders under 'Northwind'")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
