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
TITLE_MAX = 300
sleep = time.sleep   # test thay bằng hàm giả
_last_sent = 0.0


class TelegramError(Exception):
    pass


def esc(s):
    return html.escape(s or "")


def render_alert(e, cves, matched, s):
    lines = [
        f"<b>[ALERT] {esc(e.title[:TITLE_MAX])}</b>",
        f"{esc(', '.join(cves))} · Đang bị khai thác (CISA KEV)",
        f"Khớp watchlist: {esc(', '.join(matched))}",
        "",
        esc(s.summary_vi) if s else esc(e.snippet[:300]),
    ]
    if s and s.action_vi:
        lines.append(f"Hành động: {esc(s.action_vi)}")
    lines.append(f'<a href="{esc(e.url)}">Đọc bài gốc</a>')
    return "\n".join(lines)


def render_digest(items, day):
    """items: list (key, title, url, dòng tóm tắt). Trả list (text, [keys]) mỗi tin ≤ LIMIT ký tự."""
    header = f"<b>Bản tin bảo mật {day:%d/%m}</b>"
    msgs, parts, keys = [], [header], []
    for key, title, url, line in items:
        block = f'<a href="{esc(url)}">{esc(title[:TITLE_MAX])}</a>\n{esc(line[:400])}'
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
        print(f"--- tới {chat_id} ---\n{text}\n", flush=True)
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
