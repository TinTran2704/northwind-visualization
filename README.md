# Northwind Analytics — Metabase Dashboards

> Tầng visualization cho hệ thống ETL Northwind Data Warehouse.
> Kết nối trực tiếp vào PostgreSQL warehouse được build bởi [northwind-etl-pipeline](https://github.com/TinTran2704/northwind-etl-pipeline).

[![CI](https://github.com/TinTran2704/northwind-analytics-metabase/actions/workflows/ci.yml/badge.svg)](https://github.com/TinTran2704/northwind-analytics-metabase/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Stack

| Layer | Tech |
|---|---|
| BI Tool | Metabase v0.50+ |
| Data Source | PostgreSQL 16 (warehouse từ ETL repo) |
| Container | Docker Compose |

## Quickstart

```bat
rem 1. Đảm bảo ETL repo đang chạy (Postgres phải up)
cd ..\northwind-etl-pipeline && docker compose up -d postgres

rem 2. Clone và setup repo này
copy .env.example .env        rem chỉnh METABASE_PASSWORD
make up                       rem khởi động Metabase, chờ healthy
rem → Mở http://localhost:3000, hoàn thành wizard lần đầu

make setup                    rem cài semantic types + 13 questions + 5 dashboards
make export                   rem lưu config ra JSON (commit được)
```

Chi tiết: [`docs/01-setup.md`](docs/01-setup.md)

## Cấu trúc thư mục

```
northwind-analytics-metabase/
├── README.md                  ← File này
├── CLAUDE.md                  ← Hướng dẫn cho Claude Code agent
├── CONTRIBUTING.md            ← Hướng dẫn contribute
├── LICENSE                    ← MIT
├── docker-compose.yml         ← Metabase container
├── .env.example
├── .gitignore
├── .markdownlint.json
│
├── .github/
│   ├── workflows/ci.yml       ← Lint markdown + verify compose
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docs/
│   ├── 01-setup.md            ← Setup & troubleshooting
│   ├── 02-data-model.md       ← Schema warehouse cho Metabase
│   ├── 03-questions.md        ← 13+ saved queries (SQL)
│   ├── 04-dashboards.md       ← Spec 5 dashboards
│   ├── 05-collections.md      ← Cấu trúc folder + permissions
│   └── 06-best-practices.md   ← Naming, pitfalls, backup
│
├── metabase-config/exports/   ← JSON exports của Questions/Dashboards
└── screenshots/               ← Screenshots cho README/CV
```

## Dashboards

| Dashboard | Audience | Doc |
|---|---|---|
| Sales Overview | CEO, Sales VP | [docs/04](docs/04-dashboards.md#dashboard-1-sales-overview) |
| Product Performance | Product Manager | [docs/04](docs/04-dashboards.md#dashboard-2-product-performance) |
| Customer Geography | Marketing | [docs/04](docs/04-dashboards.md#dashboard-3-customer-geography) |
| Employee Performance | Sales Manager | [docs/04](docs/04-dashboards.md#dashboard-4-employee-performance) |
| ETL Pipeline Health | Data Engineer | [docs/04](docs/04-dashboards.md#dashboard-5-operations--etl-health) |

## Dashboards Preview

> Chụp screenshots sau khi setup xong (`make screenshot` để xem checklist).

| Sales Overview | Product Performance |
|---|---|
| *(screenshots/sales_overview_main_*.png)* | *(screenshots/product_performance_*.png)* |

| Customer Geography | ETL Health |
|---|---|
| *(screenshots/customer_geography_*.png)* | *(screenshots/etl_health_*.png)* |

---

## Reproduce trên máy khác

Có 2 cách để restore toàn bộ config:

### Cách A — Import từ JSON exports (nhanh, ~2 phút)

> Dùng khi đã có `metabase-config/exports/` được commit vào repo.

```bat
rem 1. Clone repo (đã có exports/ trong đó)
git clone https://github.com/TinTran2704/northwind-analytics-metabase

rem 2. Khởi động ETL repo (Postgres phải chạy trước)
cd ..\northwind-etl-pipeline && docker compose up -d postgres

rem 3. Start Metabase
cd ..\northwind-analytics-metabase
copy .env.example .env        rem chỉnh METABASE_USER và METABASE_PASSWORD
make up

rem 4. Hoàn thành setup wizard tại http://localhost:3000
rem    (dùng đúng email/password như trong .env)

rem 5. Recreate tất cả Questions + Dashboards từ JSON
make import
```

### Cách B — Tạo lại từ docs (full setup, ~5 phút)

> Dùng khi không có exports, hoặc muốn tạo fresh từ specs trong docs/.

```bat
rem Bước 1-4 giống Cách A, sau đó:
make setup    rem chạy scripts 01 → 02 → 03 theo thứ tự
make export   rem lưu config thành JSON để commit
```

### Lưu ý khi setup lần đầu

- Password `admin123` bị Metabase từ chối (quá phổ biến) — dùng `Northwind@2024` hoặc mạnh hơn
- Database connection trong Metabase phải dùng hostname `etl_postgres` (container name), không phải `localhost`
- Nếu `make import` báo `Database 'Northwind DW' not found` → kết nối DB trong Metabase Admin trước

## Liên kết

- **ETL Pipeline repo**: [northwind-etl-pipeline](https://github.com/TinTran2704/northwind-etl-pipeline)
- **Metabase docs**: https://www.metabase.com/docs

## License

MIT — xem [LICENSE](LICENSE)
