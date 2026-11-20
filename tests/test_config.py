import pytest

from secnews import config


def write(tmp_path, text, env=""):
    (tmp_path / "config.yaml").write_text(text, encoding="utf-8")
    (tmp_path / ".env").write_text(env, encoding="utf-8")
    return str(tmp_path / "config.yaml"), str(tmp_path / ".env")


BASE = """
chat_id: -1001
admin_chat_id: 42
sources:
  - { name: kev, type: kev, url: https://k }
  - { name: feed, type: rss, url: https://f }
watchlist:
  products: [keycloak, [ios, iphone os]]
  keywords: [mdm]
"""


def test_load_ok(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    cfg = config.load(*write(tmp_path, BASE, "TELEGRAM_BOT_TOKEN=abc\nLLM_API_KEY='k'\n"))
    assert cfg.chat_id == -1001 and cfg.admin_chat_id == 42
    assert [s.type for s in cfg.sources] == ["kev", "rss"]
    assert cfg.watchlist == [("keycloak", ["keycloak"]), ("ios", ["ios", "iphone os"]), ("mdm", ["mdm"])]
    assert cfg.bot_token == "abc" and cfg.llm.api_key == "k" and cfg.llm.enabled is False


def test_env_var_overrides_file(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fromenv")
    assert config.load(*write(tmp_path, BASE, "TELEGRAM_BOT_TOKEN=file\n")).bot_token == "fromenv"


@pytest.mark.parametrize("text, msg", [
    (BASE.replace("chat_id: -1001\n", ""), "chat_id"),
    (BASE.replace("type: rss", "type: html"), "rss | kev"),
    (BASE.replace("url: https://f", "url: ''"), "name, type, url"),
    (BASE + "llm: { enabled: true }\n", "base_url"),
    (BASE.replace("-1001", "-100xxx"), "phải là số"),
])
def test_load_errors(tmp_path, text, msg):
    with pytest.raises(config.ConfigError, match=msg):
        config.load(*write(tmp_path, text))


def test_example_config_parses_except_placeholder_chat_id(tmp_path):
    text = open("config.example.yaml", encoding="utf-8").read().replace("-100xxxxxxxxxx", "-1001")
    cfg = config.load(*write(tmp_path, text))
    assert {s.name for s in cfg.sources} == {"cisa-kev", "bleepingcomputer", "keycloak-releases"}


@pytest.mark.parametrize("wl", ["[ios]", "{products: ios}", "{keywords: {a: 1}}", "{products: [{a: 1}]}"])
def test_bad_watchlist_shapes_raise_config_error(tmp_path, wl):
    text = BASE.split("watchlist:")[0] + f"watchlist: {wl}\n"
    with pytest.raises(config.ConfigError):
        config.load(*write(tmp_path, text))


@pytest.mark.parametrize("text", ["- just\n- a list\n", BASE.replace("sources:\n  - { name: kev, type: kev, url: https://k }\n  - { name: feed, type: rss, url: https://f }", "sources: oops")])
def test_bad_top_level_shapes_raise_config_error(tmp_path, text):
    with pytest.raises(config.ConfigError):
        config.load(*write(tmp_path, text))


def test_llm_temperature_null(tmp_path):
    text = BASE + "llm: { enabled: true, base_url: https://x/v1, model: gpt-6-luna, temperature: null }
"
    cfg = config.load(*write(tmp_path, text))
    assert cfg.llm.temperature is None and config.load(*write(tmp_path, BASE)).llm.temperature == 0.2
