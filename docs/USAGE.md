# USAGE — Hướng dẫn sử dụng SecNews

Bot đọc CISA KEV và các feed RSS, lọc theo watchlist, tóm tắt bằng LLM rồi gửi vào nhóm Telegram. Cài đặt xem [DEPLOY](DEPLOY.md). Yêu cầu chi tiết xem [SRS](SRS.md).

## 1. Bot gửi gì

| Tin | Điều kiện | Gửi khi nào |
| --- | --- | --- |
| **ALERT** | CVE mới vào KEV (đang bị khai thác) **và** khớp watchlist | Ngay trong lần `run` kế tiếp (≤ 15 phút) |
| **DIGEST** | CVE mới vào KEV nhưng không khớp watchlist, hoặc bài RSS khớp watchlist | Gom lại, gửi một bản tin lúc 08:30 |
| Không gửi | Bài RSS không khớp watchlist; CVE đã gửi hoặc đang chờ digest trong 7 ngày qua; bài đã thấy | — |

Mẫu ALERT:

```text
[ALERT] Apple iOS and iPadOS Use-After-Free Vulnerability
CVE-2026-12345 · Đang bị khai thác (CISA KEV)
Khớp watchlist: ios, ipados

<tóm tắt tiếng Việt từ LLM, hoặc đoạn đầu bài nếu LLM tắt/lỗi>
Hành động: <việc cần làm>
Đọc bài gốc
```

Mẫu digest:

```text
Bản tin bảo mật 21/11

[KEV] CVE-2026-90817 · <tên lỗ hổng>
<tóm tắt>

<tiêu đề bài RSS>
<tóm tắt>
```

Digest dài quá 4.000 ký tự thì được tách thành nhiều tin; không bài nào bị cắt đôi.

## 2. Khi nào bot gửi tin

Bot không chạy liên tục. Nó chỉ gửi khi một lệnh được chạy, do cron gọi hoặc do bạn gõ tay.

- `run` (cron mỗi 15 phút): lấy tin mới. ALERT gửi ngay; DIGEST lưu vào DB chờ đến 08:30.
- `digest` (cron 08:30): gửi mọi bài DIGEST đang chờ. Không có bài thì không gửi gì.

"Mới" nghĩa là bot chưa từng thấy bài đó trong `data/secnews.db`. CISA thường cập nhật KEV vài lần mỗi tuần, nên có ngày không có ALERT hay digest nào. Đó là bình thường.

## 3. Lệnh

Chạy trong thư mục dự án (`/opt/secnews` trên VPS). Trên Windows thay `.venv/bin/python` bằng `.venv/Scripts/python.exe`.

```bash
.venv/bin/python -m secnews run                # lấy tin, gửi ALERT
.venv/bin/python -m secnews digest             # gửi bản tin tổng hợp
.venv/bin/python -m secnews run --dry-run      # in ra màn hình thay vì gửi
.venv/bin/python -m secnews run --config other.yaml --env other.env
```

`--dry-run` vẫn ghi vào DB, nên bài đã in ra sẽ không được gửi lại. Dùng nó để nạp lịch sử lần đầu, hoặc để thử với một `db_path` riêng.

## 4. Chỉnh config

Sửa `config.yaml`; lần chạy tới tự đọc lại, không cần khởi động lại.

### Watchlist

```yaml
watchlist:
  products: [keycloak, unbound, [ios, iphone os], fortinet]   # [tên, alias...] cho tên khác
  keywords: [mdm, apns]
```

- Khớp nguyên từ, không phân biệt hoa thường: `ios` khớp "iOS 26" nhưng không khớp "BIOS".
- `ios` cũng khớp "Cisco IOS". Muốn tránh thì dùng tên cụ thể hơn, ví dụ `[ios, ipados, iphone]`.
- Với KEV, bot chỉ so trên `vendorProject` và `product` (ví dụ "Apple", "iOS and iPadOS").
- Watchlist càng rộng thì càng nhiều ALERT. Nên chạy `--dry-run` vài ngày sau khi đổi để xem lượng tin.

### Thêm nguồn RSS

```yaml
sources:
  - { name: thehackernews, type: rss, url: https://feeds.feedburner.com/TheHackersNews }
```

`name` phải duy nhất. Chỉ hỗ trợ `rss` (RSS/Atom) và `kev`. Nguồn lỗi không làm dừng nguồn khác.

### LLM

```yaml
llm:
  enabled: true                       # false = dùng đoạn đầu bài, không gọi LLM
  base_url: https://api.openai.com/v1 # hoặc LiteLLM
  model: gpt-6-luna
  temperature: null                   # null cho model chỉ nhận mặc định (gpt-6-*, gpt-5*); 0.2 cho gpt-4.1-mini
```

Key nằm trong `.env` (`LLM_API_KEY`). LLM lỗi, timeout hay trả sai định dạng thì tin vẫn được gửi, dùng đoạn đầu bài. LLM chỉ viết phần tóm tắt; tiêu đề, CVE và link luôn lấy từ dữ liệu gốc, và mọi link trong tóm tắt bị xoá.

### Group và admin

```yaml
chat_id: -100xxxxxxxxxx   # group nhận tin
admin_chat_id: 123456789  # chat riêng nhận báo lỗi; 0 = tắt
```

Admin nhận tin khi script lỗi, hoặc khi một nguồn lỗi đúng 5 lần liên tiếp.

## 5. Câu hỏi thường gặp

**Sao không thấy tin mới?** KEV chưa có CVE mới và RSS chưa có bài khớp watchlist; hoặc cron chưa chạy. Xem `tail logs/run.log`: dòng `run xong: không có bài mới` nghĩa là bot vẫn chạy bình thường.

**Muốn nhận tin cho mọi CVE trên đời?** Bot chỉ theo KEV (CVE đang bị khai thác) và RSS. NVD với hàng trăm CVE mỗi ngày nằm ngoài phạm vi MVP (SRS §4).

**Một CVE xuất hiện ở 3 báo thì nhận mấy tin?** Một tin. Cùng CVE trong 7 ngày chỉ gửi lần đầu.

**Muốn gửi lại một tin?** Xoá dòng của bài đó trong DB rồi chạy lại:

```bash
.venv/bin/python -c "import sqlite3; c=sqlite3.connect('data/secnews.db'); c.execute(\"DELETE FROM items WHERE key='kev:CVE-2026-12345'\"); c.commit()"
```

**Đổi bot hoặc key?** Sửa `.env`. Bot mới thì phải thêm vào group và lấy lại `chat_id` ([DEPLOY §6](DEPLOY.md#6-chuyển-từ-group-test-sang-group-thật)).
