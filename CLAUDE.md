# CLAUDE.md — Hướng dẫn cho Claude Code

> File này được Claude Code đọc tự động khi vào project. Đây là **single source of truth** về quy ước dự án.

## Bối cảnh dự án

Đây là **tầng visualization** cho hệ thống ETL Northwind. Repo này KHÔNG xây dựng ETL pipeline — đó là việc của [northwind-etl-pipeline](https://github.com/TinTran2704/northwind-etl-pipeline). Repo này chỉ:

- Setup Metabase container kết nối tới PostgreSQL warehouse từ ETL repo
- Document các saved Questions (SQL queries)
- Document spec các Dashboards
- Lưu screenshots + JSON exports để portfolio

**Tech stack:**
- Metabase v0.50+ (Docker)
- PostgreSQL 16 (external, từ ETL repo)
- Markdown specs

## ⚠️ Quy tắc tuyệt đối

1. **Không tạo Python/code logic ở repo này.** Mọi data transformation thuộc về ETL repo hoặc dbt layer.
2. **Mọi SQL query phải đi vào `docs/03-questions.md`** trước khi tạo trong Metabase UI — để có version control.
3. **Luôn dùng `analytics_marts.mart_*` khi có thể**, chỉ fallback về `warehouse.*` khi mart chưa cover.
4. **Filter `is_current = true` và `*_sk != -1`** trong mọi query SCD2 dim — không có ngoại lệ.
5. **Dùng tên container `etl_postgres` (không phải localhost)** trong connection string — Metabase ở cùng Docker network.
6. **Không commit `.env`** — chỉ commit `.env.example`.
7. **Không commit screenshots có chứa thông tin nhạy cảm** (real customer names, financial data nội bộ).

## Cấu trúc tài liệu

| Doc | Khi nào đọc |
|---|---|
| `docs/01-setup.md` | Khi user hỏi setup, kết nối, troubleshoot Metabase |
| `docs/02-data-model.md` | Khi user hỏi schema, viết SQL mới, hoặc semantic types |
| `docs/03-questions.md` | Khi user yêu cầu thêm/sửa Question — UPDATE FILE NÀY trước UI |
| `docs/04-dashboards.md` | Khi user thiết kế dashboard mới — UPDATE spec trước khi build |
| `docs/05-collections.md` | Khi user hỏi tổ chức folder, permissions |
| `docs/06-best-practices.md` | Khi user gặp vấn đề performance, naming, export |

## Quy ước SQL trong file Markdown

Khi viết SQL trong `docs/03-questions.md`:

```sql
-- ✅ TỐT
SELECT
    customer_name,
    SUM(net_amount) AS total_revenue
FROM analytics_marts.mart_sales_wide
GROUP BY customer_name
ORDER BY total_revenue DESC

-- ❌ TỆ — không format, không alias rõ
SELECT customer_name, SUM(net_amount) FROM mart_sales_wide GROUP BY 1 ORDER BY 2 DESC
```

**Yêu cầu:**
- UPPERCASE keywords (SELECT, FROM, WHERE, GROUP BY)
- Mỗi column trên 1 dòng nếu nhiều hơn 3 columns
- Alias rõ nghĩa: `total_revenue` thay vì `sum`
- Indent 4 spaces
- Always specify schema: `analytics_marts.mart_sales_wide`
- Order columns trong SELECT: keys → dimensions → measures

## Quy trình làm việc

Khi user yêu cầu "thêm Question X":

1. **Đọc** `docs/02-data-model.md` để biết bảng nào dùng.
2. **Viết SQL** vào `docs/03-questions.md` với format chuẩn.
3. **Đề xuất** visualization type (Bar/Line/Pie/Table/Map).
4. **Hướng dẫn user** copy SQL vào Metabase UI:
   - "Vào Metabase → New Question → SQL Editor → paste SQL → Save vào Collection X"
5. **Không** tự tạo trong Metabase UI vì Claude Code không có quyền access browser.

Khi user yêu cầu "thêm Dashboard Y":

1. **Đọc** `docs/04-dashboards.md` để theo format spec.
2. **Vẽ layout** dạng ASCII grid (như các dashboards đã có).
3. **List ra các cards** với references tới Questions cụ thể (Q1, Q2...).
4. **Update** `docs/04-dashboards.md`.

## Khi gặp ambiguity

Nếu user nói "thêm chart về sales" mà không rõ chi tiết:

❌ KHÔNG tự đoán và viết 10 queries random.

✅ Hỏi lại:
- Audience nào (CEO, Sales, Marketing)?
- Granularity (daily/monthly/yearly)?
- Dimension (by customer/product/region)?
- Chart type preferred?

## Anti-patterns cần tránh

- ❌ Tạo file Python/Jupyter — đây là repo visualization, không phải analytics code.
- ❌ Viết SQL phức tạp nối nhiều dim khi có mart có sẵn.
- ❌ Forget `is_current = true` trên SCD2 dim.
- ❌ Commit Metabase H2 DB binary file vào git.
- ❌ Hardcode credentials vào SQL.

## Workflow check trước khi báo "done"

- [ ] SQL được viết trong `docs/03-questions.md` (không phải chỉ trong Metabase UI)
- [ ] Filter Unknown member (`*_sk != -1`)
- [ ] Filter SCD2 (`is_current = true`) nếu join trực tiếp dim
- [ ] Visualization type được suggest rõ ràng
- [ ] Nếu thêm Question → update Collection structure trong `docs/05-collections.md`
- [ ] Nếu thêm Dashboard → update `docs/04-dashboards.md` layout
