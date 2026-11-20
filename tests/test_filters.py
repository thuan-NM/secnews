import pytest

from secnews.filters import classify, extract_cves, match_watchlist
from secnews.sources import Entry

WL = [("keycloak", ["keycloak"]), ("ios", ["ios", "iphone os"]), ("mdm", ["mdm"])]


def e(title, text="", extra=None):
    return Entry("k", "s", "u", title, text[:500], text, extra or {})


def test_extract_cves_upper_dedupe_order():
    assert extract_cves(e("CVE-2026-1111 and cve-2026-22222", "again CVE-2026-1111, CVE-26-1")) == [
        "CVE-2026-1111", "CVE-2026-22222"]


@pytest.mark.parametrize("title, expected", [
    ("Apple iOS 26.2 fixes bugs", ["ios"]),
    ("New BIOS update", []),                 # ios không khớp bios
    ("iOS-based MDM servers", ["ios", "mdm"]),
    ("IPHONE OS legacy", ["ios"]),           # alias, không phân biệt hoa thường
    ("keycloaks", []),                       # khớp nguyên từ
])
def test_match_watchlist(title, expected):
    assert match_watchlist(e(title), WL) == expected


def test_match_watchlist_kev_uses_vendor_product_only():
    kev = e("Unrelated title mentions keycloak", extra={"vendorProject": "Apple", "product": "iOS and iPadOS"})
    assert match_watchlist(kev, WL) == ["ios"]


def test_match_special_chars():
    assert match_watchlist(e("Bug in C++ runtime"), [("c++", ["c++"])]) == ["c++"]


@pytest.mark.parametrize("cves, matched, tier", [
    (["CVE-1"], ["ios"], "ALERT"),
    (["CVE-2"], ["ios"], "DIGEST"),
    ([], ["ios"], "DIGEST"),
    (["CVE-1"], [], "SKIP"),
])
def test_classify(cves, matched, tier):
    assert classify(cves, matched, {"CVE-1"}) == tier
