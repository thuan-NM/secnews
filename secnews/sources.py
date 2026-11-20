"""Lấy bài từ RSS/Atom và CISA KEV (FR-02, FR-04)."""
import html
import re
from dataclasses import dataclass, field

import feedparser
import httpx

TIMEOUT = 30
HEADERS = {"User-Agent": "secnews/0.2"}
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


@dataclass
class Entry:
    key: str        # GUID của feed, không có thì URL; KEV dùng 'kev:' + CVE ID
    source: str
    url: str
    title: str
    snippet: str    # 500 ký tự đầu, đã bỏ HTML
    text: str = ""  # toàn bộ nội dung đã bỏ HTML, dùng để trích CVE và tóm tắt
    extra: dict = field(default_factory=dict)  # KEV: vendorProject, product


def strip_html(s):
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", s or ""))).strip()


def _get(url):
    r = httpx.get(url, timeout=TIMEOUT, follow_redirects=True, headers=HEADERS)
    r.raise_for_status()
    return r


def fetch_rss(url, name):
    feed = feedparser.parse(_get(url).content)
    if feed.bozo and not feed.entries:
        raise ValueError(f"feed không đọc được: {feed.get('bozo_exception')}")
    out = []
    for it in feed.entries:
        link = it.get("link", "")
        key = it.get("id") or link
        if not key:
            continue
        body = it["content"][0].get("value", "") if it.get("content") else it.get("summary", "")
        text = strip_html(body)
        out.append(Entry(key, name, link, strip_html(it.get("title", "")), text[:500], text))
    return out


def fetch_kev(url, name):
    """Trả (entries, tập CVE trong KEV)."""
    vulns = _get(url).json()["vulnerabilities"]
    entries, cves = [], set()
    for v in vulns:
        cve = v["cveID"].upper()
        cves.add(cve)
        text = f"{v.get('shortDescription', '')} {v.get('requiredAction', '')}".strip()
        entries.append(Entry(
            key=f"kev:{cve}",
            source=name,
            url=f"https://nvd.nist.gov/vuln/detail/{cve}",
            title=v.get("vulnerabilityName") or cve,
            snippet=text[:500],
            text=f"{cve} {text}",
            extra={"vendorProject": v.get("vendorProject", ""), "product": v.get("product", ""),
                   "dateAdded": v.get("dateAdded", "")},
        ))
    return entries, cves
