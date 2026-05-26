# Contributing

Cảm ơn bạn quan tâm đến dự án! Đây là hướng dẫn ngắn về cách contribute.

## Setup local

1. Clone repo
2. Đảm bảo [northwind-etl-pipeline](https://github.com/TinTran2704/northwind-etl-pipeline) đã chạy
3. Copy `.env.example` → `.env`
4. `docker compose up -d`
5. Mở http://localhost:3000

Chi tiết xem `docs/01-setup.md`.

## Branch strategy

- `main` — protected, luôn deployable
- `feature/<name>` — tính năng mới (dashboard, question collection)
- `fix/<name>` — sửa lỗi SQL, query performance
- `docs/<name>` — chỉ update docs

## Commit message — Conventional Commits

```
feat(dashboard): add sales overview dashboard
fix(query): correct revenue aggregation for SCD2
docs(setup): update connection troubleshooting
refactor(questions): consolidate top-customer queries
```

## Workflow khi thêm Question

1. Tạo branch: `git checkout -b feature/add-quarterly-revenue-question`
2. Viết SQL vào `docs/03-questions.md` (theo format đã có)
3. Test SQL trong Metabase SQL Editor
4. Tạo Question trong Metabase UI từ SQL đó
5. Screenshot kết quả vào `screenshots/`
6. Commit + push + tạo PR

## Workflow khi thêm Dashboard

1. Update `docs/04-dashboards.md` với spec layout
2. List tất cả Questions cần thiết
3. Verify mọi Question đã có trong `docs/03-questions.md`
4. Build dashboard trong Metabase UI
5. Screenshot toàn bộ dashboard
6. Update README badge/screenshot section

## Quy tắc SQL

- Dùng `analytics_marts.mart_*` khi có thể
- Filter `*_sk != -1` (Unknown member)
- Filter `is_current = true` khi join SCD2 dim trực tiếp
- UPPERCASE keywords, alias rõ nghĩa
- Schema-qualified: `analytics_marts.mart_sales_wide` không phải `mart_sales_wide`

## Định dạng Markdown

- Heading: `##` cho section, `###` cho subsection
- Table có header rõ ràng
- Code block có ngôn ngữ: ```` ```sql ````
- Link external: `[text](url)`

## Pull Request Checklist

- [ ] Branch name theo convention
- [ ] Commit messages theo Conventional Commits
- [ ] SQL đã được test trên local Metabase
- [ ] Docs đã update (nếu thêm/sửa Question hoặc Dashboard)
- [ ] Screenshot đã thêm vào `screenshots/`
- [ ] Không commit `.env` hay file binary nhạy cảm
