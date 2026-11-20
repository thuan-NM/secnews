# SRS — Software Requirements Specification

2026-11-20 · v0.3 (MVP)

## 1. Mục tiêu và phạm vi MVP

MVP là một script Python chạy bằng cron mỗi 15 phút. Script đọc vài nguồn RSS và danh mục CISA KEV, lọc theo watchlist, có thể tóm tắt bằng LLM, rồi gửi vào một nhóm Telegram. Không có server chạy nền, không có UI.

SRS nói hệ thống làm gì; [SAD](SAD.md) nói kiến trúc; [SDD](SDD.md) nói cách code. Ba tài liệu nối với nhau bằng mã FR-xx.

**Trong phạm vi**

- Nguồn: CISA KEV và các feed RSS/Atom khai báo trong config (tin bảo mật, release của sản phẩm đang dùng).
- Mọi CVE mới vào KEV đều được gửi: khớp watchlist thì gửi ngay, không khớp thì gom vào bản tin sáng. Bài RSS chỉ gửi khi khớp watchlist.
- Chống trùng: không gửi lại bài đã gửi, không gửi lại cùng CVE trong 7 ngày.
- LLM là tuỳ chọn: tóm tắt tiếng Việt dạng JSON; tắt LLM thì hệ thống vẫn chạy.
- Báo lỗi vào chat riêng của admin.

**Thuật ngữ**

| Thuật ngữ | Nghĩa |
| --- | --- |
| KEV | Danh mục lỗ hổng đã bị khai thác thực tế của CISA |
| Watchlist | Danh sách sản phẩm và từ khoá team quan tâm |
| ALERT | Tin gửi ngay trong lần chạy |
| DIGEST | Tin gom lại, gửi một lần lúc 08:30 |

**Ràng buộc:** bot gửi tối đa 20 tin/phút vào một group ([Telegram Bots FAQ](https://core.telegram.org/bots/faq)); mỗi tin tối đa 4.096 ký tự ([Telegram Bot API](https://core.telegram.org/bots/api)).

## 2. Yêu cầu chức năng

MVP có 13 yêu cầu. **Must** bắt buộc phải có; **Should** làm nếu kịp, thiếu vẫn phát hành được.

| ID | Yêu cầu | Ưu tiên |
| --- | --- | --- |
| FR-01 | Đọc danh sách nguồn (RSS/Atom, KEV) và watchlist từ `config.yaml` | Must |
| FR-02 | Mỗi lần chạy lấy tin từ tất cả nguồn; nguồn lỗi thì bỏ qua và chạy tiếp nguồn khác | Must |
| FR-03 | Trích CVE ID từ tiêu đề và nội dung | Must |
| FR-04 | Không xử lý lại bài đã thấy (khoá là GUID của feed, không có thì URL) | Must |
| FR-05 | Không gửi lại một CVE đã gửi hoặc đang chờ digest trong 7 ngày, kể cả khi tới từ nguồn khác | Must |
| FR-06 | Khớp watchlist theo tên sản phẩm, alias, từ khoá; không phân biệt hoa thường, khớp nguyên từ | Must |
| FR-07 | Phân loại: có CVE trong KEV và khớp watchlist → ALERT; entry mới của KEV không khớp watchlist, hoặc bài chỉ khớp watchlist → DIGEST; còn lại bỏ qua | Must |
| FR-08 | ALERT gửi ngay trong lần chạy; DIGEST gửi một bản tin tổng hợp lúc 08:30 mỗi ngày | Must |
| FR-09 | Khi bật LLM: tóm tắt tiếng Việt dạng JSON; LLM lỗi hoặc tắt thì dùng tiêu đề và đoạn đầu bài | Should |
| FR-10 | Tin nhắn dựng bằng template HTML, mọi text đều escape; digest dài quá 4.096 ký tự thì tách thành nhiều tin | Must |
| FR-11 | Telegram trả lỗi 429 thì chờ đúng `retry_after` rồi gửi lại | Must |
| FR-12 | Script lỗi, hoặc một nguồn lỗi 5 lần liên tiếp, thì nhắn vào chat admin | Should |
| FR-13 | Có cờ `--dry-run` để in tin ra màn hình thay vì gửi | Should |

## 3. Yêu cầu phi chức năng

| ID | Yêu cầu | Cách kiểm |
| --- | --- | --- |
| NFR-01 | Tin ALERT tới group trong ≤ 30 phút sau khi CVE vào KEV | So `dateAdded` của KEV với `sent_at` |
| NFR-02 | Không gửi trùng: chạy hai lần trên cùng dữ liệu không sinh tin mới | Test AC-01 |
| NFR-03 | Bot token và LLM key chỉ nằm trong `.env`, không có trong repo hay log | Grep repo và log |
| NFR-04 | Nội dung bài báo là không tin cậy: LLM chỉ trả JSON, không được gọi tool; text luôn được escape khi dựng tin | Test với bài chứa `<script>` và câu lệnh lạ |
| NFR-05 | Chạy trên VPS nhỏ: một file SQLite, không có service nền ngoài cron | Xem `crontab -l` và `ps` |
| NFR-06 | Thêm nguồn RSS mới chỉ cần sửa config, không sửa code | Thêm thử một feed |

## 4. Ngoài phạm vi và cách giữ scope

Quy tắc: **không có mã FR thì không code.** Ý tưởng mới ghi vào backlog và chỉ được xem xét sau khi MVP đã chạy ổn 2 tuần.

| Không làm trong MVP | Khi nào xem lại |
| --- | --- |
| Lấy CVSS/EPSS từ NVD, chấm điểm nhiều yếu tố | Khi luật KEV + watchlist bỏ sót tin quan trọng |
| Gộp các tin gần giống nhau nhưng không có CVE | Khi digest bị trùng nhiều |
| Telegram Topics, tin cập nhật dạng reply | v1.1 |
| Bot command (`/watch`, `/search`) | v1.1 |
| Nhiều group, watchlist riêng từng người, dashboard | v2 |
| Scrape trang không có RSS hoặc cần đăng nhập | Không làm |
| Đối chiếu CVE với version đang chạy thật | Sản phẩm khác |

| Version | Ngày | Thay đổi |
| --- | --- | --- |
| 0.3 | 2026-11-20 | FR-07: mọi CVE mới vào KEV đều được gửi; không khớp watchlist thì vào DIGEST |
| 0.2 | 2026-11-19 | Rút gọn thành MVP: cron + script + SQLite, bỏ NVD/EPSS, outbox, scheduler |
| 0.1 | 2026-11-19 | Bản đầy đủ đầu tiên |

## 5. Tiêu chí nghiệm thu

MVP xong khi 6 tiêu chí dưới đây pass, và sau 2 tuần chạy thật team thấy lượng tin không gây phiền.

| ID | Kiểm cho | Tình huống | Kết quả mong đợi |
| --- | --- | --- | --- |
| AC-01 | FR-04, NFR-02 | Chạy hai lần với cùng một feed | Chỉ có 1 tin được gửi |
| AC-02 | FR-05 | 3 nguồn cùng đưa tin về một CVE trong 2 ngày | Chỉ có 1 tin |
| AC-03 | FR-07, FR-08, NFR-01 | Một CVE mới vào KEV, sản phẩm có trong watchlist | ALERT tới group trong ≤ 30 phút |
| AC-04 | FR-09 | LLM lỗi hoặc bị tắt | Tin vẫn được gửi, dùng tiêu đề và đoạn đầu bài |
| AC-05 | FR-10, NFR-04 | Digest khoảng 9.000 ký tự, có bài chứa `<script>` | Nhiều tin, mỗi tin ≤ 4.096 ký tự, thẻ hiển thị dạng text |
| AC-06 | FR-02, FR-12 | Một nguồn không truy cập được | Các nguồn khác vẫn chạy; lần lỗi thứ 5 admin nhận đúng 1 tin |
