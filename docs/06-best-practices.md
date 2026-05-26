# 06 - Best Practices Metabase

## Naming Convention

| Element | Pattern | Ví dụ |
|---|---|---|
| Question | `[Entity] — [Metric] by [Dimension]` | `Sales — Revenue by Month` |
| Dashboard | `[Audience] — [Purpose]` | `Sales — Performance Overview` |
| Collection | PascalCase, tên phòng ban | `DataEngineering`, `Sales` |

## Query Best Practices

### 1. Luôn dùng mart tables khi có thể

```sql
-- ✅ TỐT: mart đã denormalize
SELECT customer_name, SUM(net_amount)
FROM analytics_marts.mart_sales_wide
GROUP BY customer_name

-- ❌ TRÁNH: join nhiều dim thủ công
SELECT c.company_name, SUM(f.net_amount)
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c ON f.customer_sk = c.customer_sk
WHERE c.is_current = true AND c.customer_sk != -1
GROUP BY c.company_name
```

### 2. Filter Unknown members

```sql
-- Mọi query warehouse phải filter -1
WHERE customer_sk != -1
  AND product_sk != -1
  AND employee_sk != -1
```

### 3. SCD2 — luôn filter is_current

```sql
-- Khi query dim trực tiếp
SELECT * FROM warehouse.dim_customer
WHERE is_current = true  -- ← BẮT BUỘC
```

### 4. Date join đúng cách

```sql
-- dim_date join bằng INT (YYYYMMDD), không phải DATE cast
JOIN warehouse.dim_date d ON f.order_date_sk = d.date_sk
-- Không làm: WHERE d.full_date::int = f.order_date_sk
```

### 5. Aggregate trước khi visualize

Metabase render chậm nếu query trả > 10,000 rows cho chart.  
Pre-aggregate trong SQL hoặc dùng `mart_sales_monthly`.

## Dashboard Best Practices

1. **KPI cards trên đầu** — số tổng quan ngay, scroll down xem chi tiết.
2. **Filter linked** — mọi card phải respond cùng filter.
3. **Click behavior** — set "Drill-through" để click vào bar → xem detail.
4. **Đặt tên card rõ ràng** — "Total Revenue (USD)" thay vì "sum(net_amount)".
5. **Số format** — set currency format cho revenue ($), integer cho count.
6. **Color consistent** — dùng cùng màu cho cùng category xuyên suốt dashboard.

## Metabase Pitfalls

| Vấn đề | Nguyên nhân | Fix |
|---|---|---|
| Double-count revenue | Quên filter `is_current=true` | Thêm vào mọi query |
| Map không hiển thị | Column chưa set semantic type Country | Admin → Data Model → set |
| Question chạy chậm | Không có index | Đã có index trên fact_sales |
| KPI số lạ | Include Unknown member (-1) | Filter `!= -1` |

## Export/Backup

Metabase không có native export Questions/Dashboards dạng code.  
Workaround: dùng [metabase-backup](https://github.com/tzmfreedom/metabase-backup) hoặc tự document SQL trong `docs/03-questions.md`.

```cmd
# Manual backup H2 database
docker exec northwind_metabase tar czf /tmp/metabase-backup.tar.gz /metabase-data
docker cp northwind_metabase:/tmp/metabase-backup.tar.gz ./metabase-config/backup.tar.gz
```
