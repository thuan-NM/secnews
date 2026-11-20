"""CLI: python -m secnews run|digest [--dry-run] (FR-02…FR-08, FR-12, FR-13; SDD §1)."""
import argparse
import logging
import sys
import traceback
from datetime import datetime, timedelta, timezone

from . import config as config_mod
from . import telegram
from .db import DB
from .filters import classify, extract_cves, match_watchlist
from .sources import fetch_kev, fetch_rss
from .summarize import Summary, summarize

log = logging.getLogger("secnews")

ERROR_THRESHOLD = 5          # FR-12: báo admin đúng ở lần lỗi liên tiếp thứ 5
VN = timezone(timedelta(hours=7))


def redact(text, cfg):
    for secret in (cfg.bot_token, cfg.llm.api_key) if cfg else ():
        if secret:
            text = text.replace(secret, "***")
    return text


def notify_admin(cfg, text, dry_run):
    """Nhắn admin; tự nuốt lỗi để không che lỗi gốc."""
    if not cfg.admin_chat_id:
        return
    try:
        telegram.send(telegram.esc(redact(text, cfg))[:3500], cfg.bot_token, cfg.admin_chat_id, dry_run)
    except Exception as ex:
        log.error("không nhắn được admin: %s", redact(str(ex), cfg))


def _summary(cfg, db, e):
    if not cfg.llm.enabled:
        return None
    s = summarize(e.title, e.text or e.snippet, cfg.llm)
    if s:
        db.set_summary(e.key, s.model_dump_json())
    return s


def run(cfg, db, dry_run=False):
    kev_src = next((s for s in cfg.sources if s.type == "kev"), None)
    kev_entries, kev_cves, kev_failed = [], set(), False
    if kev_src:
        try:
            kev_entries, kev_cves = fetch_kev(kev_src.url, kev_src.name)
        except Exception as ex:
            kev_failed = True    # lần này chỉ còn DIGEST, không có ALERT
            _source_error(cfg, db, kev_src.name, ex, dry_run)
    counts = {}
    for src in cfg.sources:
        if src.type == "kev":
            if kev_failed:
                continue
            entries = kev_entries
        else:
            try:
                entries = fetch_rss(src.url, src.name)
            except Exception as ex:
                _source_error(cfg, db, src.name, ex, dry_run)
                continue
        db.reset_error(src.name)
        for e in entries:
            if db.seen(e.key):
                continue
            cves = extract_cves(e)
            matched = match_watchlist(e, cfg.watchlist)
            tier = classify(cves, matched, kev_cves)
            if tier != "SKIP" and db.cve_recent(cves, days=7):
                tier = "SKIP"
            db.save(e, cves, matched, tier)
            counts[tier] = counts.get(tier, 0) + 1
            if tier == "ALERT":
                s = _summary(cfg, db, e)
                telegram.send(telegram.render_alert(e, cves, matched, s), cfg.bot_token, cfg.chat_id, dry_run)
                db.mark_sent(e.key)
    log.info("run xong: %s", counts or "không có bài mới")


def _source_error(cfg, db, name, ex, dry_run):
    msg = redact(f"{type(ex).__name__}: {ex}", cfg)
    n = db.record_error(name, msg)
    log.warning("nguồn %s lỗi (lần %d): %s", name, n, msg)
    if n == ERROR_THRESHOLD:
        notify_admin(cfg, f"[secnews] nguồn {name} lỗi {n} lần liên tiếp: {msg}", dry_run)


def digest(cfg, db, dry_run=False, now=None):
    rows = db.pending_digest()
    if not rows:
        log.info("digest: không có bài")
        return
    items = []
    for r in rows:
        s = Summary.model_validate_json(r["summary"]) if r["summary"] else None
        if s is None and cfg.llm.enabled:
            s = summarize(r["title"], r["snippet"], cfg.llm)
            if s:
                db.set_summary(r["key"], s.model_dump_json())
        items.append((r["key"], r["title"] or "", r["url"] or "", s.summary_vi if s else (r["snippet"] or "")[:300]))
    for text, keys in telegram.render_digest(items, now or datetime.now(VN)):
        telegram.send(text, cfg.bot_token, cfg.chat_id, dry_run)
        for k in keys:
            db.mark_sent(k)
    log.info("digest: gửi %d bài", len(items))


def main(argv=None):
    p = argparse.ArgumentParser(prog="secnews")
    p.add_argument("command", choices=["run", "digest"])
    p.add_argument("--dry-run", action="store_true", help="in tin ra màn hình thay vì gửi")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--env", default=".env")
    args = p.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):   # Windows/cron có thể không mặc định UTF-8
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    for noisy in ("httpx", "httpcore", "openai"):   # httpx log URL có token (NFR-03)
        logging.getLogger(noisy).setLevel(logging.WARNING)

    cfg = None
    try:
        cfg = config_mod.load(args.config, args.env)
        db = DB(cfg.db_path)
        (run if args.command == "run" else digest)(cfg, db, args.dry_run)
        return 0
    except Exception as ex:
        log.error(redact(traceback.format_exc(), cfg))
        if cfg:
            notify_admin(cfg, f"[secnews] {args.command} lỗi: {type(ex).__name__}: {ex}", args.dry_run)
        return 1


if __name__ == "__main__":
    sys.exit(main())
