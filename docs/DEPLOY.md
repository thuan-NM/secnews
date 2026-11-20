# DEPLOY — Triển khai SecNews lên VPS

Hướng dẫn đưa bot lên một VPS Linux và chạy bằng crontab, theo [SAD §4](SAD.md). Làm lần lượt từ bước 1 đến bước 7.

## 1. Yêu cầu

| Thứ | Yêu cầu |
| --- | --- |
| Hệ điều hành | Linux có `cron` và `flock` (gói `util-linux`, có sẵn trên Ubuntu/Debian) |
| Python | 3.10 trở lên, kèm `python3-venv` |
| Mạng ra ngoài | HTTPS tới `raw.githubusercontent.com`, `github.com`, `api.telegram.org`, `api.openai.com` và các feed RSS trong config |
| Mạng vào | Không cần; bot không mở cổng nào |
| Ổ đĩa | Dưới 100 MB, gồm venv và `secnews.db` |

Kiểm nhanh:

```bash
python3 --version          # ≥ 3.10
which flock crontab git
```

## 2. Ba file mang từ máy local lên

Ba file này không nằm trong git. Copy chúng từ thư mục dự án trên máy đang chạy thử.

| File | Chứa gì | Ghi chú |
| --- | --- | --- |
| `.env` | `TELEGRAM_BOT_TOKEN`, `LLM_API_KEY` | Bí mật. Chỉ copy qua `scp`, không gửi qua chat hay email |
| `config.yaml` | `chat_id`, `admin_chat_id`, LLM, nguồn, watchlist | Không có bí mật |
| `data/secnews.db` | Lịch sử bài đã thấy | Nên mang theo để server không coi ~1.800 bài cũ là tin mới |

Mẫu `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=<token từ @BotFather>
LLM_API_KEY=<OpenAI API key>
```

Từ máy Windows (Git Bash), trong thư mục dự án:

```bash
ssh user@vps 'sudo mkdir -p /opt/secnews && sudo chown $USER /opt/secnews'
scp .env config.yaml user@vps:/tmp/
scp data/secnews.db user@vps:/tmp/
```

## 3. Cài code

```bash
cd /opt/secnews
git clone https://github.com/thuan-NM/secnews.git .
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p data logs
mv /tmp/.env /tmp/config.yaml .
mv /tmp/secnews.db data/
chmod 600 .env
```

Không mang `secnews.db` theo thì phải nạp lịch sử trước khi gửi thật, nếu không group nhận cả loạt tin cũ:

```bash
.venv/bin/python -m secnews run --dry-run > /dev/null
```

## 4. Kiểm trước khi bật lịch

```bash
.venv/bin/python -m pytest -q                       # mọi test phải pass
.venv/bin/python -m secnews run --dry-run           # in tin ra màn hình, không gửi
.venv/bin/python -m secnews run                     # chạy thật một lần
```

`run` không lỗi và in `run xong: ...` là được. Nguồn nào in `403 Forbidden` thì xem mục 8.

## 5. Bật crontab

Kiểm timezone của VPS:

```bash
timedatectl | grep "Time zone"
```

Mở `crontab -e` và thêm các dòng dưới. Nếu VPS chạy giờ UTC thì digest dùng `30 1`, tức 08:30 giờ Việt Nam. Nếu VPS đặt `Asia/Ho_Chi_Minh` thì đổi thành `30 8`.

```text
*/15 * * * *  cd /opt/secnews && flock -n /tmp/secnews.lock .venv/bin/python -m secnews run    >> logs/run.log 2>&1
30 1 * * *    cd /opt/secnews && flock /tmp/secnews.lock    .venv/bin/python -m secnews digest >> logs/run.log 2>&1
0 20 * * *    cd /opt/secnews && .venv/bin/python -c "import sqlite3; sqlite3.connect('data/secnews.db').backup(sqlite3.connect('data/secnews.backup.db'))"
```

- Dòng 1 lấy tin mỗi 15 phút và gửi ALERT ngay.
- Dòng 2 gửi bản tin digest mỗi sáng.
- Dòng 3 sao lưu DB mỗi ngày (SAD §4). Mất DB thì tệ nhất là gửi lại tin vài ngày gần nhất.
- `flock` chặn hai lần chạy chồng nhau: lần `run` sau bỏ qua nếu lần trước chưa xong, còn `digest` thì chờ.

Kiểm cron đã nhận:

```bash
crontab -l
# chờ 15 phút rồi:
tail -n 5 logs/run.log
```

## 6. Chuyển từ group test sang group thật

1. Thêm bot vào group thật, rồi gõ `/start@<tên_bot>` trong group.
2. Lấy `chat_id`:

   ```bash
   . ./.env && curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | grep -o '"chat":{"id":-[0-9]*,"title":"[^"]*"'
   ```

3. Sửa `chat_id` trong `config.yaml`. Không cần khởi động lại gì, lần cron tới sẽ đọc config mới.

## 7. Cập nhật phiên bản

```bash
cd /opt/secnews
git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

Không cần dừng cron. `config.yaml`, `.env` và `data/` không bị `git pull` ghi đè.

## 8. Sự cố thường gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
| --- | --- |
| Nguồn báo `403 Forbidden` | Trang chặn IP của VPS. Với KEV, dùng mirror `https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json`. Với RSS, đổi feed khác hoặc xoá nguồn |
| Admin nhận "nguồn X lỗi 5 lần liên tiếp" | Nguồn chết 5 lần chạy liền. Bot chỉ báo 1 lần; nguồn chạy lại thì bộ đếm tự về 0 |
| Admin nhận "run lỗi: ..." | Script dừng giữa chừng. Xem chi tiết trong `logs/run.log` |
| `thiếu TELEGRAM_BOT_TOKEN` | `.env` sai chỗ hoặc thiếu dòng. File phải nằm ở `/opt/secnews/.env` |
| `Unsupported value: 'temperature'` trong log | Model chỉ nhận temperature mặc định. Đặt `llm.temperature: null` |
| Không thấy tin nào | Xem [USAGE §2](USAGE.md#2-khi-nào-bot-gửi-tin): bot chỉ gửi tin mới, theo luật KEV và watchlist |
| `logs/run.log` quá lớn | Thêm logrotate, hoặc `: > logs/run.log` khi cần |

## 9. Bảo mật

- `.env` để quyền `600` và không bao giờ commit (đã nằm trong `.gitignore`).
- Token hoặc key bị lộ thì revoke ngay: bot token qua @BotFather `/revoke`, OpenAI key ở trang API keys. Sau đó sửa `.env`; lần cron tới sẽ dùng key mới.
- Log và tin báo admin đã che token, nhưng vẫn không nên chia sẻ `logs/run.log` ra ngoài.
