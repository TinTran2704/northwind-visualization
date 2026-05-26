# 02 - Data Model cho Metabase

> Giải thích schema warehouse để build questions/dashboards đúng cách.

## Schemas trong northwind_dw

| Schema | Vai trò | Dùng trong Metabase? |
|---|---|---|
| `warehouse` | Dimensional model (Star Schema) | ✅ Primary |
| `analytics_staging` | dbt staging views | ✅ Secondary |
| `analytics_marts` | dbt mart tables | ✅ Best choice |
| `staging` | Error events, internal | ⚠️ Ít dùng |
| `metadata` | ETL run history | ✅ Ops monitoring |

## Recommendation: Dùng analytics_marts khi có thể

`analytics_marts` (từ dbt) đã denormalize sẵn:
- `mart_sales_wide` — 1 table có đủ mọi dimension, không cần join
- `mart_sales_monthly` — pre-aggregated theo tháng

Nếu chưa có dbt, dùng `warehouse` schema trực tiếp.

## Star Schema (warehouse schema)

```
                    dim_date
                      │ order_date_sk
                      │
  dim_customer ───── fact_sales ───── dim_product
                      │
                      │ employee_sk
                    dim_employee
                      │
                      │ shipper_sk
                    dim_shipper
                      │
                    dim_geography (ship_geography_sk)
                      │
                    dim_audit
```

## Các bảng quan trọng

### fact_sales (transaction grain)

| Column | Type | Mô tả |
|---|---|---|
| order_id | INT | Degenerate dimension |
| order_date_sk | INT | FK → dim_date (YYYYMMDD) |
| customer_sk | BIGINT | FK → dim_customer |
| product_sk | BIGINT | FK → dim_product |
| employee_sk | BIGINT | FK → dim_employee |
| quantity | INT | Số lượng |
| unit_price | DECIMAL | Đơn giá |
| discount | DECIMAL | Chiết khấu 0-1 |
| net_amount | DECIMAL | Doanh thu thực |

### dim_customer (SCD Type 2)

⚠️ **Quan trọng**: Bảng này có nhiều versions của cùng 1 customer. Khi query analytics, **luôn filter `is_current = true`** để tránh double-count.

```sql
SELECT * FROM warehouse.dim_customer
WHERE is_current = true
  AND customer_sk != -1   -- Bỏ "Unknown" member
```

### dim_date

Bảng date dimension pre-built từ 1990-2030. Join qua `date_sk` (INT format YYYYMMDD).

```sql
-- Ví dụ: lấy order_date dạng DATE
SELECT
  d.full_date,
  d.year,
  d.quarter,
  d.month_name,
  f.net_amount
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.order_date_sk = d.date_sk
```

### mart_sales_wide (recommended cho Metabase)

Đã join sẵn tất cả dims, chỉ cần query 1 bảng:

| Column | Mô tả |
|---|---|
| order_id, line_number | Keys |
| order_date | DATE |
| order_year, order_quarter, order_month | Time breakdown |
| customer_code, customer_name | Customer |
| customer_country, customer_region | Geography |
| product_name, category_name | Product |
| employee_name | Sales rep |
| quantity, net_amount | Measures |

## Metabase Table Metadata Settings

Sau khi kết nối DB, vào **Admin → Data Model** để set:

### Visibility
- `dim_audit` → Hidden (internal)
- `staging.error_events` → Hidden
- `metadata.etl_runs` → Hidden (trừ khi muốn ops dashboard)

### Semantic Types (giúp Metabase auto-suggest)

| Column | Semantic Type |
|---|---|
| net_amount, total_revenue | Currency |
| order_date, full_date | Date |
| country_code | Country |
| customer_name, company_name | Name |
| quantity | Quantity |

### Foreign Keys
Set FK relationship để Metabase tự suggest joins:
- `fact_sales.customer_sk` → FK → `dim_customer.customer_sk`
- `fact_sales.product_sk` → FK → `dim_product.product_sk`
- `fact_sales.order_date_sk` → FK → `dim_date.date_sk`
