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

## Quickstart (< 10 phút)

```bash
# 1. Đảm bảo ETL repo đang chạy
cd ../northwind-etl-pipeline
docker compose up -d postgres

# 2. Setup Metabase
cd ../northwind-analytics-metabase
copy .env.example .env
docker compose up -d

# 3. Mở http://localhost:3000 → setup wizard
```

**Hướng dẫn chi tiết step-by-step**: [`docs/00-quickstart.md`](docs/00-quickstart.md)  
**Setup nâng cao + troubleshooting**: [`docs/01-setup.md`](docs/01-setup.md)

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
│   ├── 00-quickstart.md       ← ⭐ Đọc đầu tiên — step-by-step setup
│   ├── 01-setup.md            ← Setup & troubleshooting chi tiết
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

## Liên kết

- **ETL Pipeline repo**: [northwind-etl-pipeline](https://github.com/TinTran2704/northwind-etl-pipeline)
- **Metabase docs**: https://www.metabase.com/docs

## License

MIT — xem [LICENSE](LICENSE)