"""Đọc config.yaml + .env (FR-01, NFR-03, NFR-06)."""
import os
from dataclasses import dataclass, field

import yaml


class ConfigError(Exception):
    pass


@dataclass
class Source:
    name: str
    type: str  # rss | kev
    url: str


@dataclass
class LLM:
    enabled: bool = False
    base_url: str = ""
    model: str = ""
    api_key: str = ""


@dataclass
class Config:
    chat_id: int
    admin_chat_id: int
    sources: list[Source]
    watchlist: list[tuple[str, list[str]]]  # (tên hiển thị, [tên, alias...])
    llm: LLM = field(default_factory=LLM)
    bot_token: str = ""
    db_path: str = "data/secnews.db"


def read_env(path):
    """Đọc KEY=VALUE từ .env; biến môi trường đã có thì giữ nguyên."""
    env = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    env.update({k: v for k, v in os.environ.items() if k in ("TELEGRAM_BOT_TOKEN", "LLM_API_KEY")})
    return env


def _watchlist(raw):
    """products: mỗi mục là tên hoặc list [tên, alias...]; keywords: list từ khoá."""
    out = []
    for item in (raw.get("products") or []) + (raw.get("keywords") or []):
        terms = [str(t) for t in item] if isinstance(item, list) else [str(item)]
        if not terms or not all(t.strip() for t in terms):
            raise ConfigError(f"watchlist: mục rỗng {item!r}")
        out.append((terms[0], terms))
    return out


def load(path="config.yaml", env_path=".env"):
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise ConfigError(f"không thấy {path}; copy từ config.example.yaml") from None
    for key in ("chat_id", "sources", "watchlist"):
        if not raw.get(key):
            raise ConfigError(f"{path}: thiếu '{key}'")
    sources = []
    for s in raw["sources"]:
        if not isinstance(s, dict) or not all(s.get(k) for k in ("name", "type", "url")):
            raise ConfigError(f"{path}: nguồn cần name, type, url: {s!r}")
        if s["type"] not in ("rss", "kev"):
            raise ConfigError(f"{path}: nguồn {s['name']} có type '{s['type']}', chỉ nhận rss | kev")
        sources.append(Source(s["name"], s["type"], s["url"]))
    env = read_env(env_path)
    llm_raw = raw.get("llm") or {}
    llm = LLM(
        enabled=bool(llm_raw.get("enabled", False)),
        base_url=llm_raw.get("base_url", ""),
        model=llm_raw.get("model", ""),
        api_key=env.get("LLM_API_KEY", ""),
    )
    if llm.enabled and not (llm.base_url and llm.model):
        raise ConfigError(f"{path}: llm.enabled cần base_url và model")
    try:
        chat_id, admin_chat_id = int(raw["chat_id"]), int(raw.get("admin_chat_id") or 0)
    except (TypeError, ValueError):
        raise ConfigError(f"{path}: chat_id và admin_chat_id phải là số") from None
    return Config(
        chat_id=chat_id,
        admin_chat_id=admin_chat_id,
        sources=sources,
        watchlist=_watchlist(raw["watchlist"]),
        llm=llm,
        bot_token=env.get("TELEGRAM_BOT_TOKEN", ""),
        db_path=raw.get("db_path", "data/secnews.db"),
    )
