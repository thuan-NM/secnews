# TASKS — Kế hoạch và tiến độ

Mỗi task nối về FR/NFR/AC trong [SRS](SRS.md) và mục tương ứng trong [SDD](SDD.md). Làm lần lượt theo milestone; trong một milestone có thể đổi thứ tự.

**Trạng thái:** `[ ]` chưa làm · `[~]` đang làm · `[x]` xong · `[-]` bỏ (ghi lý do)

**Cách cập nhật:** đổi checkbox, điền ngày xong vào cột cuối, cập nhật bảng Tiến độ. Commit ghi mã task, ví dụ `T-05: thêm extract_cves`.

## Tiến độ

| Milestone | Mục tiêu | Task | Xong |
| --- | --- | --- | --- |
| M0 | Chuẩn bị | 4 | 0 |
| M1 | Khung code + config + DB | 5 | 0 |
| M2 | Lấy tin + lọc | 5 | 0 |
| M3 | Dựng tin + gửi Telegram | 5 | 0 |
| M4 | LLM tóm tắt (Should) | 3 | 0 |
| M5 | Báo lỗi + test nghiệm thu | 4 | 0 |
| M6 | Triển khai + chạy thử | 5 | 0 |
| **Tổng** | | **31** | **0** |

## M0 — Chuẩn bị

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-01 | Tạo bot qua @BotFather, lưu token vào `.env` | NFR-03 | |
| [ ] | T-02 | Tạo group test + group thật, thêm bot, lấy `chat_id`; lấy `admin_chat_id` | FR-08, FR-12 | |
| [ ] | T-03 | Chọn danh sách feed RSS/Atom ban đầu và watchlist | FR-01 | |
| [ ] | T-04 | Tạo repo Python: `pyproject.toml`/`requirements.txt` (`httpx`, `feedparser`, `openai`, `pydantic`, `pyyaml`, `pytest`, `respx`), `.gitignore` có `.env`, `data/`, `logs/` | NFR-03 | |

## M1 — Khung code, config, DB

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-05 | Dựng 7 file trong `secnews/` theo SDD §1, chạy được `python -m secnews run --dry-run` (chưa làm gì) | FR-13 | |
| [ ] | T-06 | `config.py`: đọc `config.yaml` + `.env`, báo lỗi rõ khi thiếu trường | FR-01, NFR-06 | |
| [ ] | T-07 | `db.py`: tạo 2 bảng theo SDD §2.1; hàm `seen`, `save`, `mark_sent` | FR-04 | |
| [ ] | T-08 | `db.py`: `cve_recent(cves, days=7)` bằng `json_each` | FR-05 | |
| [ ] | T-09 | `db.py`: `record_error`, `reset_error` trên bảng `source_errors` | FR-12 | |

## M2 — Lấy tin và lọc

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-10 | `sources.py`: `fetch_rss()` — key = GUID hoặc URL, snippet 500 ký tự đã bỏ HTML | FR-02, FR-04 | |
| [ ] | T-11 | `sources.py`: `fetch_kev()` — trả entries (key `kev:<CVE>`) và tập CVE | FR-02 | |
| [ ] | T-12 | `filters.py`: `extract_cves()` + unit test | FR-03 | |
| [ ] | T-13 | `filters.py`: `match_watchlist()` khớp nguyên từ, không phân biệt hoa thường (`ios` ≠ `bios`); KEV so `vendorProject`/`product` + unit test | FR-06 | |
| [ ] | T-14 | `filters.py`: `classify()` + luồng `run()` theo SDD §1 (nguồn lỗi thì bỏ qua) | FR-02, FR-07 | |

## M3 — Dựng tin và gửi Telegram

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-15 | `telegram.py`: `render_alert()` theo SDD §3.3, mọi text qua `html.escape` | FR-10, NFR-04 | |
| [ ] | T-16 | `telegram.py`: `render_digest()` + tách tin ≤ 4.000 ký tự, không cắt giữa bài | FR-10 | |
| [ ] | T-17 | `telegram.py`: `send()` — `parse_mode=HTML`, tắt link preview, nghỉ 3,5 s giữa tin; `--dry-run` thì in ra | FR-08, FR-13 | |
| [ ] | T-18 | Xử lý 429: ngủ `retry_after`, thử lại tối đa 3 lần | FR-11 | |
| [ ] | T-19 | Lệnh `digest`: lấy bài DIGEST chưa gửi, gửi, ghi `sent_at`; không có bài thì không gửi | FR-08 | |

## M4 — LLM tóm tắt (Should)

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-20 | `summarize.py`: gọi LiteLLM qua `openai` SDK, prompt theo SDD §3.2, timeout 30 s, không tool | FR-09, NFR-04 | |
| [ ] | T-21 | Kiểm JSON bằng pydantic, xoá URL trong output; lỗi bất kỳ thì trả `None` | FR-09 | |
| [ ] | T-22 | `llm.enabled: false` thì bỏ qua toàn bộ, tin dùng snippet | FR-09 | |

## M5 — Báo lỗi và test nghiệm thu

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-23 | Nhắn admin khi script lỗi và khi nguồn lỗi đúng lần thứ 5 | FR-12 | |
| [ ] | T-24 | Fixtures trong `tests/fixtures`: feed mẫu, KEV mẫu, bài chứa `<script>` | — | |
| [ ] | T-25 | Integration test AC-01, AC-04, AC-06 (giả Telegram/LLM bằng `respx`) | AC-01, AC-04, AC-06 | |
| [ ] | T-26 | Test AC-02, AC-05; grep repo/log không có token | AC-02, AC-05, NFR-03 | |

## M6 — Triển khai và chạy thử

| | ID | Task | Liên quan | Xong ngày |
| --- | --- | --- | --- | --- |
| [ ] | T-27 | Cài lên VPS `/opt/secnews`: venv, `config.yaml`, `.env`, `data/`, `logs/` | NFR-05 | |
| [ ] | T-28 | Thêm 2 dòng crontab theo SAD §4 (kiểm timezone VPS) + backup `secnews.db` hằng ngày | FR-08, NFR-05 | |
| [ ] | T-29 | Chạy `--dry-run` 1 tuần, chỉnh watchlist | AC-03 | |
| [ ] | T-30 | Gửi vào group test, đo NFR-01 (`dateAdded` KEV so `sent_at`) | AC-03, NFR-01 | |
| [ ] | T-31 | Chuyển sang group thật, chạy 2 tuần, hỏi team lượng tin có phiền không | §5 SRS | |

## Backlog (chỉ xem sau khi MVP chạy ổn 2 tuần)

Ghi ý tưởng mới ở đây, không code khi chưa có mã FR. Xem bảng "Ngoài phạm vi" ở SRS §4.

| Ý tưởng | Ngày ghi | Ghi chú |
| --- | --- | --- |
| | | |

## Nhật ký

Ghi ngắn mỗi khi xong milestone hoặc gặp vấn đề lớn.

| Ngày | Ghi chú |
| --- | --- |
| 2026-11-20 | Dựng repo, chuyển spec vào `docs/`, tạo TASKS.md |
