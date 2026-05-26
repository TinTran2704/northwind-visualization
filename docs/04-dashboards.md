# 04 - Dashboard Specs

> Spec thiết kế cho từng dashboard. Mỗi dashboard = 1 tab trong Metabase.

## Dashboard 1: Sales Overview

**Mục đích**: Tổng quan doanh số toàn công ty — dành cho CEO/Sales VP.

**Filter (Dashboard-level):**
- Date range (order_date)
- Category (multi-select)

**Layout (12-column grid):**

```
┌─────────┬─────────┬─────────┬─────────┐
│Total    │Order    │Avg Order│Top      │
│Revenue  │Count    │Value    │Category │
│ [KPI]   │ [KPI]   │ [KPI]   │ [KPI]   │
├─────────────────────────────────────────┤
│  Revenue by Month (Line Chart)          │
│  [Full width]                           │
├───────────────────┬─────────────────────┤
│ Revenue by        │ Sales by Quarter    │
│ Category (Bar)    │ (Bar grouped)       │
├───────────────────┴─────────────────────┤
│ Top 10 Customers (Table)                │
└─────────────────────────────────────────┘
```

**Cards:**

| Card | Question | Type | Size |
|---|---|---|---|
| Total Revenue | Q1 (sum net_amount) | Number (KPI) | 3 cols |
| Order Count | Q1 (sum order_count) | Number | 3 cols |
| Avg Order Value | Q5 (avg) | Number | 3 cols |
| Top Category | Q2 (first row) | Number | 3 cols |
| Revenue Trend | Q1 | Line chart | 12 cols |
| Category Breakdown | Q2 | Bar horizontal | 6 cols |
| Quarterly Sales | Q4 | Bar grouped | 6 cols |
| Top 10 Customers | Q3 | Table | 12 cols |

---

## Dashboard 2: Product Performance

**Mục đích**: Phân tích hiệu suất sản phẩm — dành cho Product Manager.

**Filters:** Date range, Category

**Layout:**

```
┌──────────────────────┬──────────────────┐
│ Category Revenue     │ Category         │
│ (Bar horizontal)     │ Distribution     │
│                      │ (Pie)            │
├──────────────────────┴──────────────────┤
│ Top 10 Products (Table)                 │
├─────────────────────────────────────────┤
│ Discount Analysis by Category (Bar)     │
└─────────────────────────────────────────┘
```

---

## Dashboard 3: Customer Geography

**Mục đích**: Phân bổ khách hàng địa lý — dành cho Marketing.

**Filters:** Region, Year

**Layout:**

```
┌─────────────────────────────────────────┐
│ Revenue by Country (Pin Map)            │
│ [Full width, tall]                      │
├───────────────────┬─────────────────────┤
│ Revenue by Region │ Top Countries Table │
│ (Bar)             │                     │
└───────────────────┴─────────────────────┘
```

**Notes:**
- Pin Map cần set `customer_country` column semantic type = "Country"
- Color: gradient blue (light = ít revenue, dark = nhiều)

---

## Dashboard 4: Employee Performance

**Mục đích**: Hiệu suất sales rep.

**Filters:** Date range, Employee name

**Layout:**

```
┌─────────┬─────────┬─────────┐
│Total    │Top Rep  │Best     │
│Orders   │Revenue  │Avg Order│
├─────────┴─────────┴─────────┤
│ Sales Rep Comparison (Bar)  │
├─────────────────────────────┤
│ Employee Details (Table)    │
└─────────────────────────────┘
```

---

## Dashboard 5: Operations — ETL Health

**Mục đích**: Monitoring pipeline ETL — dành cho Data Engineer (bạn).

**Filters:** Date range, Status

**Layout:**

```
┌─────────┬─────────┬─────────┐
│Last Run │Rows     │Quality  │
│Status   │Loaded   │Score    │
├─────────┴─────────┴─────────┤
│ ETL Run History (Table)     │
│ color: SUCCESS=green,       │
│        FAILED=red           │
└─────────────────────────────┘
```

**SQL cho Quality Score KPI:**
```sql
SELECT
    ROUND(AVG(quality_score) * 100, 1) AS avg_quality_pct
FROM warehouse.dim_audit
WHERE etl_run_timestamp >= NOW() - INTERVAL '7 days'
  AND audit_sk != -1
```

---

## Tips tạo Dashboard trong Metabase

1. **Tạo Questions trước, Dashboard sau** — không tạo chart trong dashboard.
2. **Dashboard filter** → Add filter → link tới columns tương ứng trong mỗi card.
3. **Click vào số KPI** → Drilldown tự động → cấu hình click behavior.
4. **Text card** → thêm header, separator, mô tả cho từng section.
5. **Auto-refresh** → Dashboard settings → Refresh every 5 minutes (cho Ops dashboard).
6. **Subscriptions** → Email dashboard PDF vào 8h sáng mỗi thứ 2 (cần cấu hình SMTP).
