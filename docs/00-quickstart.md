# 00 - Quickstart — Chạy lần đầu

> Làm theo file này theo thứ tự để có Metabase chạy + kết nối tới warehouse trong < 10 phút.

## Pre-check

Trước khi bắt đầu, verify ETL repo đã chạy và có data:

```cmd
:: 1. ETL Postgres đang chạy?
docker ps | findstr etl_postgres
:: Phải thấy: etl_postgres ... Up X minutes (healthy)

:: 2. Warehouse có data?
docker exec etl_postgres psql -U etl_user -d northwind_dw -c "SELECT COUNT(*) FROM warehouse.fact_sales;"
:: Phải trả về > 1700

:: 3. Network etl_network tồn tại?
docker network ls | findstr etl_network
:: Phải thấy: etl_network ... bridge
```

Nếu một trong 3 fail → quay lại `northwind-etl-pipeline` chạy `docker compose up -d postgres` và pipeline trước.

---

## Bước 1: Setup Metabase repo

```cmd
:: Vào thư mục Metabase repo (cùng cấp với ETL repo)
cd C:\TinTran\Project\northwind-analytics-metabase

:: Copy env
copy .env.example .env

:: Start Metabase
docker compose up -d
```

Đợi ~60-90 giây cho lần init đầu. Check status:

```cmd
docker logs northwind_metabase --tail 5
:: Khi thấy "Metabase Initialization COMPLETE" → ready
```

Hoặc poll health:
```cmd
curl http://localhost:3000/api/health
:: Phải trả về: {"status":"ok"}
```

---

## Bước 2: Setup wizard lần đầu

Mở browser: **http://localhost:3000**

### Step 2.1 — Language
Chọn **English** (hoặc Vietnamese nếu có).

### Step 2.2 — Tạo admin
| Field | Value gợi ý |
|---|---|
| First name | Tin |
| Last name | Tran |
| Email | `admin@etl.local` |
| Company | `Northwind Demo` |
| Password | `admin123` (đổi tùy ý, phải ≥ 6 ký tự + có số) |

### Step 2.3 — Add your data
**Chọn "I'll add my data later"** rồi click Next — sẽ kết nối ở bước riêng để có nhiều lựa chọn hơn.

### Step 2.4 — Usage data
Tùy chọn — `Opt-out` nếu bạn muốn riêng tư.

### Step 2.5 — Done!
Vào dashboard chính.

---

## Bước 3: Kết nối PostgreSQL — Chọn 1 trong 2 cách

### Option A — Shared Docker Network (khuyến nghị)

Trong Metabase: **Settings (góc phải)** → **Admin settings** → **Databases** → **Add database**

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | `Northwind DW` |
| Host | `etl_postgres` |
| Port | `5432` |
| Database name | `northwind_dw` |
| Username | `etl_user` |
| Password | `etl_password` |
| Schemas | Để trống (sync tất cả) |
| Use a secure connection (SSL) | OFF |

Click **Save**. Nếu thấy ✅ "Successfully connected" → done.

### Option B — Host Network (nếu Option A fail)

Cùng form như trên nhưng đổi Host:

| Field | Value |
|---|---|
| Host | `host.docker.internal` |
| Port | `5432` |
| (còn lại giống Option A) | |

> `host.docker.internal` là alias đặc biệt cho phép container reach host machine. Hoạt động cả Windows/Mac/Linux (Linux cần `extra_hosts` đã có trong compose).

### Option C — Nếu vẫn fail

Test connection trực tiếp:
```cmd
:: Test từ container Metabase
docker exec northwind_metabase nc -zv etl_postgres 5432
:: Phải thấy: "etl_postgres (172.x.x.x:5432) open"

:: Nếu thấy "Connection refused" → kiểm tra network
docker inspect northwind_metabase | findstr etl_network
:: Phải có etl_network trong NetworkSettings
```

---

## Bước 4: Verify data sync xong

Sau khi connect, Metabase tự scan schema (1-2 phút).

**Browse Data** (sidebar trái) → **Northwind DW** → phải thấy:

```
warehouse/
  ├── dim_audit
  ├── dim_customer
  ├── dim_date
  ├── dim_employee
  ├── dim_geography
  ├── dim_product
  ├── dim_shipper
  ├── fact_sales              ← Click vào đây
  └── agg_sales_monthly
staging/
  └── error_events
metadata/
  └── etl_runs
```

Click `fact_sales` → **Explore** → phải thấy ~1716 rows. ✅

---

## Bước 5: Test SQL query đầu tiên

**New (+)** (góc phải header) → **SQL query** → chọn database `Northwind DW` → paste:

```sql
SELECT
    d.year,
    d.month_name,
    COUNT(DISTINCT f.order_id) AS order_count,
    ROUND(SUM(f.net_amount)::numeric, 2) AS total_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.order_date_sk = d.date_sk
WHERE f.customer_sk != -1
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
LIMIT 12
```

Click **Get answer** → phải thấy 12 rows revenue theo tháng. ✅

---

## Bước 6: Set semantic types (giúp Metabase auto-detect chart)

**Admin settings** → **Data Model** → chọn **Northwind DW** → **warehouse** → **fact_sales**:

| Column | Click "Type" → Set |
|---|---|
| net_amount | Currency → USD |
| unit_price | Currency → USD |
| discount_amount | Currency → USD |
| freight_allocated | Currency → USD |
| quantity | Quantity |
| order_id | Entity Key |

Sang **dim_customer**:

| Column | Set |
|---|---|
| country_code | Country |
| city | City |
| postal_code | Zip Code |
| company_name | Name |
| phone | Phone |

Sang **dim_date**:

| Column | Set |
|---|---|
| full_date | Creation date |

---

## ✅ Bạn đã sẵn sàng!

Tiếp theo:
- [`docs/03-questions.md`](03-questions.md) — Copy SQL build các Questions
- [`docs/04-dashboards.md`](04-dashboards.md) — Build Dashboards
- [`docs/05-collections.md`](05-collections.md) — Tổ chức folder

---

## Troubleshooting nhanh

### Metabase trắng trang sau khi mở localhost:3000
Đợi thêm 60-90 giây. Lần đầu phải init H2 DB.

### "Could not connect to host etl_postgres"
ETL repo chưa start hoặc network không shared. Chạy:
```cmd
cd ..\northwind-etl-pipeline
docker compose up -d postgres
```

### "FATAL: password authentication failed"
Mismatch credentials. Verify `.env` của ETL repo:
```cmd
cd ..\northwind-etl-pipeline
type .env | findstr ETL_DW
```
Dùng đúng giá trị đó trong Metabase connection form.

### Container start được nhưng UI 404
Healthcheck chưa pass. Wait + retry:
```cmd
docker compose restart metabase
timeout /t 60
curl http://localhost:3000/api/health
```

### Muốn reset toàn bộ Metabase
```cmd
docker compose down -v
docker compose up -d
:: Phải làm lại setup wizard
```
