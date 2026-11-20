from pathlib import Path

import httpx
import pytest
import respx

from secnews import sources

FIX = Path(__file__).parent / "fixtures"


@respx.mock
def test_fetch_rss_keys_and_snippet():
    respx.get("https://feed").respond(200, content=(FIX / "feed.xml").read_bytes())
    es = sources.fetch_rss("https://feed", "news")
    assert [e.key for e in es] == ["guid-1", "https://news.example/ios", "guid-3"]
    assert es[0].title == "Keycloak fixes CVE-2026-1111 & more"
    assert es[0].snippet == "Keycloak 26.1 patches cve-2026-1111."
    assert all(e.source == "news" and len(e.snippet) <= 500 for e in es)


@respx.mock
def test_fetch_rss_http_error_raises():
    respx.get("https://feed").respond(503)
    with pytest.raises(httpx.HTTPStatusError):
        sources.fetch_rss("https://feed", "news")


@respx.mock
def test_fetch_rss_garbage_raises():
    respx.get("https://feed").respond(200, content=b"<html>not a feed")
    with pytest.raises(ValueError):
        sources.fetch_rss("https://feed", "news")


@respx.mock
def test_fetch_kev():
    respx.get("https://kev").respond(200, content=(FIX / "kev.json").read_bytes())
    es, cves = sources.fetch_kev("https://kev", "cisa-kev")
    assert cves == {"CVE-2026-2222", "CVE-2026-3333"}
    assert es[0].key == "kev:CVE-2026-2222"
    assert es[0].extra["product"] == "iOS and iPadOS"
    assert es[0].url == "https://nvd.nist.gov/vuln/detail/CVE-2026-2222"
