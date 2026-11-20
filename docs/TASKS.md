# TASKS — Epic, task và tiến độ

Công việc chia thành 9 epic. Mỗi epic gom các task cùng một mảng chức năng, nối về FR/NFR/AC trong [SRS](SRS.md) và mục tương ứng trong [SDD](SDD.md).

**Mã task:** `E<số epic>-<số task>`, ví dụ `E4-02`. Commit ghi mã task: `E4-02: thêm match_watchlist`.

**Trạng thái:** `[ ]` chưa làm · `[~]` đang làm · `[x]` xong · `[-]` bỏ (ghi lý do ở cột Ghi chú)

**Cách cập nhật:** đổi checkbox, điền ngày xong, cập nhật bảng Tổng quan. Epic chỉ tính xong khi mọi mục "Xong khi" đều đạt.

## Tổng quan

Thứ tự làm đề xuất: E1 → E2 → E3 → E4 → E5 → E6 → E7 → E8 → E9. E6 (LLM) là Should, có thể làm sau E9 nếu cần ra mắt sớm.

| Epic | Tên | FR/NFR chính | Ưu tiên | Task | Xong | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Chuẩn bị và khung dự án | NFR-03, FR-13 | Must | 6 | 5 | Còn group thật (E1-02) |
| E2 | Config và lưu trữ | FR-01, FR-04, FR-05, NFR-06 | Must | 6 | 6 | Xong |
| E3 | Thu thập nguồn | FR-02, FR-04 | Must | 4 | 4 | Xong |
| E4 | Lọc và phân loại | FR-03, FR-05, FR-06, FR-07 | Must | 5 | 5 | Xong |
| E5 | Dựng tin và gửi Telegram | FR-08, FR-10, FR-11, FR-13 | Must | 7 | 7 | Xong |
| E6 | Tóm tắt bằng LLM | FR-09, NFR-04 | Should | 4 | 4 | Xong |
| E7 | Giám sát và báo lỗi | FR-12 | Should | 3 | 3 | Xong |
| E8 | Kiểm thử nghiệm thu | AC-01 → AC-06, NFR-02, NFR-03 | Must | 5 | 5 | Xong |
| E9 | Triển khai và vận hành | NFR-01, NFR-05 | Must | 6 | 0 | Chưa làm |
| **Tổng** | | | | **46** | **39** | |

---

## E1 — Chuẩn bị và khung dự án

**Mục tiêu:** có bot, group, repo Python chạy được lệnh rỗng.
**Xong khi:** `python -m secnews run --dry-run` chạy không lỗi; `.env` không nằm trong git.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E1-01 | Tạo bot qua @BotFather, lưu token vào `.env` | NFR-03 | 2026-11-20 | |
| [~] | E1-02 | Tạo group test và group thật, thêm bot, lấy `chat_id` từng group | FR-08 |  | Group test xong, còn group thật |
| [x] | E1-03 | Lấy `admin_chat_id` (chat riêng với bot) | FR-12 | 2026-11-20 | |
| [x] | E1-04 | Tạo `requirements.txt`: `httpx`, `feedparser`, `openai`, `pydantic`, `pyyaml`, `pytest`, `respx` | SAD §2 | 2026-11-20 | |
| [x] | E1-05 | Dựng 7 file trong `secnews/` theo SDD §1, mỗi file chỉ có hàm rỗng | SDD §1 | 2026-11-20 | |
| [x] | E1-06 | `__main__.py`: CLI `run` / `digest`, cờ `--dry-run` | FR-13 | 2026-11-20 | |

## E2 — Config và lưu trữ

**Mục tiêu:** đọc được config, có SQLite với đủ hàm cho luồng `run` và `digest`.
**Xong khi:** thêm một feed mới chỉ cần sửa `config.yaml`; unit test của `db.py` pass.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E2-01 | Viết `config.yaml` mẫu theo SDD §4 (nguồn, watchlist, llm, chat_id) | FR-01 | 2026-11-20 | |
| [x] | E2-02 | `config.py`: đọc `config.yaml` + `.env`, báo lỗi rõ khi thiếu trường bắt buộc | FR-01, NFR-03, NFR-06 | 2026-11-20 | |
| [x] | E2-03 | `db.py`: tạo bảng `items`, `source_errors` theo SDD §2.1 | SDD §2.1 | 2026-11-20 | |
| [x] | E2-04 | `db.py`: `seen(key)`, `save(...)`, `mark_sent(key)` | FR-04 | 2026-11-20 | |
| [x] | E2-05 | `db.py`: `cve_recent(cves, days=7)` dùng `json_each` | FR-05 | 2026-11-20 | |
| [x] | E2-06 | `db.py`: `record_error`, `reset_error`; `record_error` trả về số lần lỗi liên tiếp | FR-12 | 2026-11-20 | |

## E3 — Thu thập nguồn

**Mục tiêu:** lấy được bài từ RSS/Atom và CISA KEV dưới cùng một dạng entry.
**Xong khi:** chạy `--dry-run` in ra số bài mỗi nguồn; một nguồn lỗi không làm dừng nguồn khác.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E3-01 | Định nghĩa entry chung: `key`, `source`, `url`, `title`, `snippet`, `raw` | SDD §2.1 | 2026-11-20 | |
| [x] | E3-02 | `fetch_rss()`: key = GUID, không có thì URL; snippet 500 ký tự đã bỏ HTML | FR-02, FR-04 | 2026-11-20 | |
| [x] | E3-03 | `fetch_kev()`: trả entries (key `kev:<CVE>`) và tập CVE trong KEV | FR-02 | 2026-11-20 | |
| [x] | E3-04 | Vòng lặp nguồn trong `run()`: bắt lỗi từng nguồn, ghi `record_error`, chạy tiếp | FR-02 | 2026-11-20 | |

## E4 — Lọc và phân loại

**Mục tiêu:** mỗi bài được gán đúng `ALERT`, `DIGEST` hoặc `SKIP`.
**Xong khi:** unit test cho `extract_cves`, `match_watchlist`, `classify` pass; một CVE không vào 2 tin trong 7 ngày.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E4-01 | `extract_cves()`: regex `CVE-\d{4}-\d{4,}`, viết hoa, bỏ trùng + unit test | FR-03 | 2026-11-20 | |
| [x] | E4-02 | `match_watchlist()`: khớp nguyên từ, không phân biệt hoa thường (`ios` không khớp `bios`) + unit test | FR-06 | 2026-11-20 | |
| [x] | E4-03 | Với entry KEV, `match_watchlist()` so trên `vendorProject` và `product` | FR-06 | 2026-11-20 | |
| [x] | E4-04 | `classify()`: KEV + watchlist → ALERT; chỉ watchlist → DIGEST; còn lại SKIP + unit test | FR-07 | 2026-11-20 | |
| [x] | E4-05 | Nối vào `run()`: bỏ bài đã thấy, hạ xuống SKIP nếu `cve_recent`, lưu DB | FR-04, FR-05 | 2026-11-20 | |

## E5 — Dựng tin và gửi Telegram

**Mục tiêu:** ALERT gửi ngay, DIGEST gửi lúc 08:30, tin luôn đúng định dạng và an toàn.
**Xong khi:** gửi được ALERT và digest vào group test; bài chứa `<script>` hiện dạng text.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E5-01 | `render_alert()` theo SDD §3.3, mọi text qua `html.escape` | FR-10, NFR-04 | 2026-11-20 | |
| [x] | E5-02 | `render_digest()`: tiêu đề `Bản tin bảo mật dd/mm`, mỗi bài 1 dòng link + 1 dòng tóm tắt | FR-08, FR-10 | 2026-11-20 | |
| [x] | E5-03 | Tách tin ≤ 4.000 ký tự, không cắt giữa một bài + unit test | FR-10 | 2026-11-20 | |
| [x] | E5-04 | `send()`: `parse_mode=HTML`, tắt link preview, nghỉ 3,5 s giữa tin | FR-08 | 2026-11-20 | |
| [x] | E5-05 | `--dry-run`: in tin ra màn hình thay vì gửi | FR-13 | 2026-11-20 | |
| [x] | E5-06 | Lỗi 429: ngủ `retry_after` rồi thử lại, tối đa 3 lần; lỗi khác ném exception | FR-11 | 2026-11-20 | |
| [x] | E5-07 | Lệnh `digest`: lấy bài DIGEST chưa gửi, gửi lần lượt, ghi `sent_at`; không có bài thì không gửi | FR-08 | 2026-11-20 | |

## E6 — Tóm tắt bằng LLM (Should)

**Mục tiêu:** tin có tóm tắt tiếng Việt; LLM lỗi hay tắt thì tin vẫn đi.
**Xong khi:** AC-04 pass; LLM không thể chèn link vào tin.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E6-01 | `summarize()`: gọi LiteLLM qua `openai` SDK, `temperature=0.2`, timeout 30 s, không truyền tool | FR-09, NFR-04 | 2026-11-20 | |
| [x] | E6-02 | Prompt theo SDD §3.2: nội dung trong `<article>`, tối đa 3.000 ký tự | FR-09, NFR-04 | 2026-11-20 | |
| [x] | E6-03 | Kiểm JSON bằng pydantic, xoá URL trong `summary_vi`/`action_vi`; lỗi bất kỳ trả `None` | FR-09 | 2026-11-20 | |
| [x] | E6-04 | `llm.enabled: false` thì bỏ qua, tin dùng snippet; áp dụng cho cả ALERT và digest | FR-09 | 2026-11-20 | |

## E7 — Giám sát và báo lỗi (Should)

**Mục tiêu:** admin biết khi bot hỏng mà không bị spam.
**Xong khi:** AC-06 pass; nguồn lỗi liên tục chỉ sinh đúng 1 tin cho admin.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E7-01 | `__main__.py` bắt exception toàn cục, nhắn admin rồi thoát với mã lỗi | FR-12 | 2026-11-20 | |
| [x] | E7-02 | Nhắn admin khi một nguồn lỗi đúng lần thứ 5 liên tiếp (không nhắn lại lần 6, 7…) | FR-12 | 2026-11-20 | |
| [x] | E7-03 | Ghi log ra stdout (cron đẩy vào `logs/run.log`), không in token hay API key | NFR-03 | 2026-11-20 | |

## E8 — Kiểm thử nghiệm thu

**Mục tiêu:** chứng minh MVP đạt 6 tiêu chí AC trong SRS §5.
**Xong khi:** `pytest` pass toàn bộ, gồm AC-01, AC-02, AC-04, AC-05, AC-06.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [x] | E8-01 | Fixtures trong `tests/fixtures`: feed mẫu, KEV mẫu, bài chứa `<script>`, digest ~9.000 ký tự | — | 2026-11-20 | |
| [x] | E8-02 | Test AC-01: chạy 2 lần cùng feed → 1 tin | AC-01, NFR-02 | 2026-11-20 | |
| [x] | E8-03 | Test AC-02: 3 nguồn cùng một CVE trong 2 ngày → 1 tin | AC-02 | 2026-11-20 | |
| [x] | E8-04 | Test AC-04, AC-05, AC-06 (giả Telegram 429, LLM lỗi, nguồn chết bằng `respx`) | AC-04, AC-05, AC-06 | 2026-11-20 | |
| [x] | E8-05 | Grep repo và log: không có bot token hay LLM key | NFR-03 | 2026-11-20 | |

## E9 — Triển khai và vận hành

**Mục tiêu:** bot chạy thật trên VPS và team thấy lượng tin hợp lý.
**Xong khi:** AC-03 pass; chạy group thật 2 tuần không có phàn nàn về lượng tin.

| | ID | Task | Liên quan | Xong ngày | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| [ ] | E9-01 | Cài lên VPS `/opt/secnews`: venv, `config.yaml`, `.env`, `data/`, `logs/` | NFR-05 | | |
| [ ] | E9-02 | Thêm 2 dòng crontab theo SAD §4, kiểm timezone VPS | FR-08, NFR-05 | | |
| [ ] | E9-03 | Backup `secnews.db` hằng ngày | SAD §4 | | |
| [ ] | E9-04 | Chạy `--dry-run` 1 tuần, chỉnh watchlist | SAD §4 | | |
| [ ] | E9-05 | Gửi vào group test, đo NFR-01 (`dateAdded` KEV so với `sent_at`) | AC-03, NFR-01 | | |
| [ ] | E9-06 | Chuyển sang group thật, chạy 2 tuần, hỏi team lượng tin có phiền không | SRS §5 | | |

---

## Backlog (chỉ xem sau khi MVP chạy ổn 2 tuần)

Ghi ý tưởng mới ở đây, không code khi chưa có mã FR. Xem bảng "Ngoài phạm vi" ở SRS §4.

| Ý tưởng | Ngày ghi | Ghi chú |
| --- | --- | --- |
| Chỉ ALERT các entry KEV có `dateAdded` gần đây | 2026-11-20 | Lần chạy đầu với DB trống sinh 78 ALERT cũ (từ 2008). Hiện dựa vào tuần `--dry-run` để nạp lịch sử (SAD §4). Cần FR mới nếu muốn chặn trong code |
| Gửi lại ALERT đã lưu nhưng gửi thất bại | 2026-11-20 | Theo SDD §1, ALERT được lưu trước khi gửi; Telegram lỗi thì tin đó mất (admin vẫn được báo). Cần FR mới |

## Nhật ký

Ghi ngắn mỗi khi xong một epic hoặc gặp vấn đề lớn.

| Ngày | Ghi chú |
| --- | --- |
| 2026-11-20 | Dựng repo, chuyển spec vào `docs/`, tạo TASKS.md |
| 2026-11-20 | Chia lại task theo 9 epic |
| 2026-11-20 | E1–E8 xong: 66 test pass. Lead Opus 5.5 tự code (không dùng builder), 3 review Codex gpt-6.1-sol high (E2, E3–E5, E6–E8), 1 vòng, 7 lỗi đã sửa |
| 2026-11-20 | Chạy thử `--dry-run` với feed thật: cisa.gov và bleepingcomputer trả 403 từ máy dev (chặn IP); mirror `cisagov/kev-data` trên GitHub chạy được. Watchlist `ios` khớp cả Cisco IOS — chỉnh ở E9-04 |
| 2026-11-20 | Chạy thật local: `digest` gửi 2 bài vào group test kèm tóm tắt `gpt-6-luna`; `run` chạy sạch |
| 2026-11-20 | Spec v0.3 (user duyệt): FR-07 đổi thành mọi CVE mới vào KEV đều gửi; ngoài watchlist thì vào DIGEST. Chưa chạy review Codex cho thay đổi này |
