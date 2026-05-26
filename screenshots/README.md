# Screenshots

Thư mục lưu screenshots của Metabase dashboards/questions để dùng trong README và CV.

## Quy ước đặt tên

```
{dashboard_name}_{view}_{date}.png

Ví dụ:
sales_overview_main_2025-05-15.png
sales_overview_filters_2025-05-15.png
product_performance_top10_2025-05-15.png
etl_health_failed_run_2025-05-15.png
```

## Cách chụp

1. Mở dashboard trong Metabase
2. Đợi data load hoàn toàn
3. Snipping Tool (Windows) hoặc Cmd+Shift+4 (Mac)
4. Crop sát rìa dashboard
5. Resize về 1920x1080 hoặc 1280x720 nếu quá lớn

## Sử dụng trong README

```markdown
![Sales Overview Dashboard](screenshots/sales_overview_main_2025-05-15.png)
```

## Lưu ý

- ❌ KHÔNG chụp data có thông tin nhạy cảm thật (customer thật, doanh số nội bộ)
- ✅ Northwind là dataset public, OK để show
- File ảnh trong folder này đã có trong `.gitignore` (chỉ pattern `*.png`), nhưng folder vẫn được commit qua `.gitkeep`
- Nếu muốn commit ảnh: thêm vào `.gitignore` exception
