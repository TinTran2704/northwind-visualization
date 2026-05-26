# 05 - Collections & Permissions

## Cách tổ chức Collections

```
Our analytics/              ← Root (tất cả mọi người thấy)
├── 📁 Executive/           ← CEO, VP xem
│   ├── Sales Overview Dashboard
│   └── KPI Summary
│
├── 📁 Sales/               ← Sales team
│   ├── Questions/
│   │   ├── Revenue by Month
│   │   ├── Top Customers
│   │   └── ...
│   └── Product Performance Dashboard
│
├── 📁 Marketing/           ← Marketing team
│   ├── Customer Geography Dashboard
│   └── Questions/
│
├── 📁 Data Engineering/    ← DE team (bạn)
│   ├── ETL Health Dashboard
│   └── Questions/
│       ├── ETL Pipeline History
│       └── Data Quality Scores
│
└── 📁 Drafts/              ← Work in progress, không share
```

## Groups & Permissions (nếu có nhiều người dùng)

| Group | Collection Access | Data Access |
|---|---|---|
| All Users | View Our analytics/ | View |
| Sales | Curate Sales/ | View + Download |
| Marketing | Curate Marketing/ | View |
| Data Engineering | Curate Data Engineering/ | Full Access |
| Admins | Curate All | Admin |

Trong demo cá nhân (solo): dùng 1 account admin là đủ.
