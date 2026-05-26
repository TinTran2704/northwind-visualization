# 03 - Questions (Saved Queries)

> Danh sách tất cả saved questions cần tạo trong Metabase, kèm SQL.
> Tổ chức theo Collections để dễ tìm.

## Collection structure

```
Our analytics/
├── 📁 Sales/
│   ├── Total Revenue by Month
│   ├── Revenue by Category
│   ├── Top 10 Customers
│   ├── Sales by Quarter
│   └── Average Order Value
├── 📁 Products/
│   ├── Top 10 Products by Revenue
│   ├── Category Breakdown
│   └── Discount Analysis
├── 📁 Geography/
│   ├── Revenue by Country
│   └── Revenue by Region
├── 📁 Employees/
│   ├── Sales Rep Performance
│   └── Orders by Employee
├── 📁 Operations/
│   ├── Shipping Time Analysis
│   └── ETL Pipeline Health
```

---

## Sales Questions

### Q1: Total Revenue by Month

**SQL:**
```sql
SELECT
    order_year,
    order_month,
    order_month_name,
    SUM(net_amount) AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_month, order_month_name
ORDER BY order_year, order_month
```

**Visualization**: Line chart — X: order_month_name, Y: total_revenue  
**Filter**: Date range picker trên order_year

---

### Q2: Revenue by Category

```sql
SELECT
    category_name,
    SUM(net_amount)      AS total_revenue,
    SUM(quantity)        AS total_units,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY total_revenue DESC
```

**Visualization**: Bar chart (horizontal) — Y: category_name, X: total_revenue

---

### Q3: Top 10 Customers

```sql
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
LIMIT 10
```

**Visualization**: Table với conditional formatting trên total_revenue

---

### Q4: Sales by Quarter

```sql
SELECT
    order_year,
    order_quarter,
    CONCAT(order_year, ' Q', order_quarter) AS quarter_label,
    SUM(net_amount) AS total_revenue
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_quarter
ORDER BY order_year, order_quarter
```

**Visualization**: Bar chart grouped by year

---

### Q5: Average Order Value Trend

```sql
SELECT
    order_year,
    order_month,
    order_month_name,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY order_year, order_month, order_month_name
ORDER BY order_year, order_month
```

---

## Product Questions

### Q6: Top 10 Products by Revenue

```sql
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
LIMIT 10
```

**Visualization**: Table

---

### Q7: Category Breakdown — Pie

```sql
SELECT
    category_name,
    SUM(net_amount) AS revenue,
    ROUND(SUM(net_amount) * 100.0 / SUM(SUM(net_amount)) OVER (), 1) AS pct
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY revenue DESC
```

**Visualization**: Pie chart

---

### Q8: Discount Analysis by Category

```sql
SELECT
    category_name,
    ROUND(AVG(discount) * 100, 1)   AS avg_discount_pct,
    ROUND(MIN(discount) * 100, 1)   AS min_discount_pct,
    ROUND(MAX(discount) * 100, 1)   AS max_discount_pct,
    SUM(net_amount)                  AS total_revenue,
    SUM(quantity * unit_price) - SUM(net_amount) AS total_discount_given
FROM analytics_marts.mart_sales_wide
GROUP BY category_name
ORDER BY avg_discount_pct DESC
```

---

## Geography Questions

### Q9: Revenue by Country — Map

```sql
SELECT
    customer_country         AS country_code,
    customer_country_name    AS country,
    customer_region          AS region,
    SUM(net_amount)          AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count
FROM analytics_marts.mart_sales_wide
GROUP BY customer_country, customer_country_name, customer_region
ORDER BY total_revenue DESC
```

**Visualization**: Pin Map (set country_code column type = Country)

---

### Q10: Revenue by Region

```sql
SELECT
    customer_region,
    SUM(net_amount)          AS total_revenue,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_code) AS unique_customers
FROM analytics_marts.mart_sales_wide
GROUP BY customer_region
ORDER BY total_revenue DESC
```

---

## Employee Questions

### Q11: Sales Rep Performance

```sql
SELECT
    employee_name,
    employee_title,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(net_amount)          AS total_revenue,
    ROUND(SUM(net_amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT customer_code) AS unique_customers
FROM analytics_marts.mart_sales_wide
GROUP BY employee_name, employee_title
ORDER BY total_revenue DESC
```

---

## Operations Questions

### Q12: ETL Pipeline Health

```sql
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
LIMIT 20
```

**Visualization**: Table — conditional formatting: SUCCESS=green, FAILED=red

---

### Q13: Shipping Time Analysis

```sql
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
GROUP BY s.company_name
```
