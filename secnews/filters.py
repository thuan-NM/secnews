"""Trích CVE, khớp watchlist, phân loại (FR-03, FR-06, FR-07; SDD §3.1)."""
import re

_CVE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def extract_cves(e):
    found = (m.upper() for m in _CVE.findall(f"{e.title}\n{e.text or e.snippet}"))
    return list(dict.fromkeys(found))


def _term_re(term):
    # khớp nguyên từ; dùng lookaround thay \b để từ như "c++" hay ".net" vẫn khớp
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)


def match_watchlist(e, watchlist):
    """Trả tên hiển thị của các mục watchlist khớp. Entry KEV chỉ so vendorProject + product."""
    if "vendorProject" in e.extra:
        hay = f"{e.extra['vendorProject']} {e.extra['product']}"
    else:
        hay = f"{e.title}\n{e.text or e.snippet}"
    return [name for name, terms in watchlist if any(_term_re(t).search(hay) for t in terms)]


def classify(cves, matched, kev_cves, is_kev=False):
    """FR-07 (v0.3): mọi CVE mới vào KEV đều được gửi; khớp watchlist thì ALERT, không thì DIGEST."""
    if matched and any(c in kev_cves for c in cves):
        return "ALERT"
    if matched or is_kev:
        return "DIGEST"
    return "SKIP"
