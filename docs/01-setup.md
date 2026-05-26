# 01 - Setup & Kết nối

## Yêu cầu

- Docker Desktop đang chạy
- **ETL repo đang chạy** — PostgreSQL phải up với schema `warehouse.*`
- ETL repo: `northwind-etl-pipeline` đã chạy `docker compose up -d postgres` và pipeline đã load data

## Bước 1 — Verify ETL Postgres còn sống

```cmd
docker ps | findstr etl_postgres
docker exec etl_postgres psql -U etl_user -d northwind_dw -c "SELECT COUNT(*) FROM warehouse.fact_sales;"
```

Phải thấy `1716` (hoặc số rows bạn đã load).

## Bước 2 — Verify network shared

```cmd
docker network ls | findstr etl
```

Phải thấy `etl_network`. Đây là network mà Metabase sẽ join vào để reach Postgres.

Nếu chưa có (lần đầu):
```cmd
cd ..\northwind-etl-pipeline
docker compose up -d postgres
```

## Bước 3 — Start Metabase

```cmd
cd northwind-analytics-metabase
copy .env.example .env
docker compose up -d
```

Đợi ~60-90 giây (lần đầu Metabase init H2 DB). Verify:

```cmd
docker logs northwind_metabase | findstr "Metabase Initialization COMPLETE"
```

Hoặc poll health:
```cmd
curl http://localhost:3000/api/health
```

Trả về `{"status":"ok"}` là OK.

## Bước 4 — Setup wizard lần đầu

Mở http://localhost:3000

### Step 1: Tạo admin account
- Email: `admin@etl.local`
- Password: `admin` (sửa nếu cần)

### Step 2: Add your data — Kết nối PostgreSQL
Điền vào form:

| Field | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | Northwind DW |
| Host | `etl_postgres` |
| Port | `5432` |
| Database name | `northwind_dw` |
| Username | `etl_user` |
| Password | `etl_password` |

> **Lưu ý**: Dùng tên container `etl_postgres` (không phải `localhost`) vì Metabase và Postgres cùng Docker network.

Click **Test connection** → phải thấy ✅ `Success`

### Step 3: Usage data
Chọn `Opt-out` nếu không muốn gửi analytics cho Metabase.

### Step 4: Done!
Redirect về Home dashboard.

## Bước 5 — Verify data accessible

Sau khi setup, vào **Browse Data** → chọn **Northwind DW**:

Phải thấy 3 schemas:
- `warehouse` — dim_customer, dim_product, fact_sales...
- `staging` — error_events
- `metadata` — etl_runs

Vào `warehouse.fact_sales` → **Explore** → phải thấy 1716+ rows.

## Troubleshooting

### Metabase không reach được Postgres

```
Error: Connection to etl_postgres:5432 refused
```

**Fix**: Kiểm tra Metabase có join đúng network không:
```cmd
docker inspect northwind_metabase | findstr etl_network
```

Nếu không có → `docker compose down && docker compose up -d` (rebuild với network config mới).

### Metabase trắng trang sau 3000

Đợi thêm — lần đầu có thể mất 2-3 phút. Xem log:
```cmd
docker logs -f northwind_metabase
```

### Quên password admin

```cmd
docker exec -it northwind_metabase java -jar /app/metabase.jar reset-password admin@etl.local
```
