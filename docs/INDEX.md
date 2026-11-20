# SecNews Telegram Pipeline — Spec v0.3 (MVP)

Bộ spec cho bot tự động gom tin bảo mật và gửi vào nhóm Telegram.

| File | Nội dung |
| --- | --- |
| [SRS.md](SRS.md) | Hệ thống phải làm gì: 13 FR, 6 NFR, phạm vi, tiêu chí nghiệm thu |
| [SAD.md](SAD.md) | Kiến trúc: sơ đồ, công nghệ, 7 ADR, triển khai bằng crontab |
| [SDD.md](SDD.md) | Thiết kế code: 7 file Python, schema SQLite, JSON từ LLM, config, test |
| [DEPLOY.md](DEPLOY.md) | Triển khai lên VPS: file cần mang lên, cài đặt, crontab, sự cố |
| [USAGE.md](USAGE.md) | Sử dụng: bot gửi gì và khi nào, lệnh, chỉnh watchlist/nguồn/LLM, FAQ |
| [TASKS.md](TASKS.md) | 9 epic, 46 task, trạng thái và tiến độ |
| `sad-architecture.png` | Sơ đồ kiến trúc dùng trong SAD |

## Cách dùng bộ spec

1. Đọc SRS để biết phải làm gì, SAD để biết chọn công nghệ gì, SDD để biết code thế nào.
2. Làm việc theo [TASKS.md](TASKS.md): mỗi lần bắt đầu một task thì đổi trạng thái, xong thì tick và ghi ngày.
3. Mỗi commit ghi mã task, ví dụ `E4-01: thêm extract_cves`.

Quy tắc giữ scope: không có mã FR trong SRS thì không code. Ý tưởng mới ghi vào mục Backlog trong TASKS.md.
