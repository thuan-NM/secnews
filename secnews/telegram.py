"""Dựng tin, tách tin dài, gửi, xử lý 429 (FR-08, FR-10, FR-11, FR-13; SDD §3.3)."""
import html
import logging
import time

import httpx

log = logging.getLogger(__name__)

API = "https://api.telegram.org"
LIMIT = 4000         # dưới mức 4.096 của Telegram; đếm trên chuỗi HTML nên luôn dư
PACE = 3.5           # giây giữa hai tin, để dưới 20 tin/phút
MAX_RETRIES = 3
CVE_SHOW = 10        # ALERT chỉ liệt kê tối đa 10 CVE
URL_MAX = 1000       # href dài hơn thì bỏ link, giữ chữ
sleep = time.sleep   # test thay bằng hàm giả
_last_sent = 0.0


class TelegramError(Exception):
    pass


def esc(s):
    return html.escape(s or "")


def esc_fit(s, budget):
    """Escape rồi cắt sao cho chuỗi HTML ≤ budget; cắt trên text gốc nên không vỡ entity."""
    s = (s or "")[:budget]
    out = esc(s)
    while len(out) > budget:
        s = s[: len(s) - (len(out) - budget)]
        out = esc(s)
    return out


def _link(url, label):
    href = esc(url)
    return f'<a href="{href}">{label}</a>' if url and len(href) <= URL_MAX else label


def render_alert(e, cves, matched, s):
    shown = ", ".join(cves[:CVE_SHOW]) + (f" (+{len(cves) - CVE_SHOW} CVE)" if len(cves) > CVE_SHOW else "")
    lines = [
        f"<b>[ALERT] {esc_fit(e.title, 400)}</b>",
        f"{esc(shown)} · Đang bị khai thác (CISA KEV)",
        f"Khớp watchlist: {esc_fit(', '.join(matched), 200)}",
        "",
        esc_fit(s.summary_vi, 1000) if s else esc_fit(e.snippet[:300], 1000),
    ]
    if s and s.action_vi:
        lines.append(f"Hành động: {esc_fit(s.action_vi, 400)}")
    lines.append(_link(e.url, "Đọc bài gốc"))
    return "\n".join(lines)


def render_digest(items, day):
    """items: list (key, title, url, dòng tóm tắt). Trả list (text, [keys]) mỗi tin ≤ LIMIT ký tự."""
    header = f"<b>Bản tin bảo mật {day:%d/%m}</b>"
    msgs, parts, keys = [], [header], []
    for key, title, url, line in items:
        # mỗi bài tối đa ~2.400 ký tự HTML nên luôn vừa một tin, kể cả kèm header
        block = f"{_link(url, esc_fit(title, 400))}\n{esc_fit(line[:400], 1000)}"
        # không bao giờ cắt giữa một bài: đầy thì mở tin mới
        if keys and len("\n\n".join(parts + [block])) > LIMIT:
            msgs.append(("\n\n".join(parts), keys))
            parts, keys = [], []
        parts.append(block)
        keys.append(key)
    if keys:
        msgs.append(("\n\n".join(parts), keys))
    return msgs


def _json(r):
    try:
        return r.json()
    except ValueError:
        return {}


def send(text, token, chat_id, dry_run=False):
    global _last_sent
    if dry_run:
        print(f"--- dry-run ---\n{text}\n", flush=True)  # không in chat_id (NFR-03)
        return
    if not token:
        raise TelegramError("thiếu TELEGRAM_BOT_TOKEN trong .env")
    wait = PACE - (time.monotonic() - _last_sent)
    if wait > 0:
        sleep(wait)
    body = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True}}
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = httpx.post(f"{API}/bot{token}/sendMessage", json=body, timeout=30)
        except httpx.HTTPError as ex:
            # không đưa URL (chứa token) vào exception hay log (NFR-03)
            raise TelegramError(f"không gọi được Telegram: {type(ex).__name__}") from None
        _last_sent = time.monotonic()
        if r.status_code == 429 and attempt < MAX_RETRIES:
            retry = _json(r).get("parameters", {}).get("retry_after", 5)
            log.warning("Telegram 429, chờ %ss", retry)
            sleep(retry)
            continue
        if r.status_code != 200 or not _json(r).get("ok"):
            raise TelegramError(f"Telegram {r.status_code}: {_json(r).get('description', '')}")
        return
