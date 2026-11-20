# Contributor guide

This directory is the repository's coding harness. It gives an agent enough context to change SecNews without guessing which file owns a behavior or which check is meaningful. [AGENTS.md](../AGENTS.md) is the mandatory entry point and routing table; the guides below are the detailed source of truth for their subjects.

## What this project currently contains

- `docs/` holds the MVP spec v0.2: [SRS](../docs/SRS.md), [SAD](../docs/SAD.md), [SDD](../docs/SDD.md), the architecture diagram and [TASKS](../docs/TASKS.md).
- `secnews/` implements FR-01…FR-13 (epics E1–E8). E9 (VPS deployment) is not done; see TASKS for status and the Backlog.
- `tests/` covers AC-01, AC-02, AC-04, AC-05, AC-06 offline with fixtures, `respx` for HTTP and a fake OpenAI client (`fake_llm` in `tests/conftest.py`; openai 3.x uses `httpx2`, which `respx` cannot intercept). AC-03 needs a real run.
- Setup: `uv venv .venv && uv pip install -r requirements.txt`, copy `config.example.yaml` to `config.yaml` and `.env.example` to `.env`. Verify with `.venv/Scripts/python.exe -m pytest -q` (Windows) or `.venv/bin/python -m pytest -q`.

Layout (SDD §1):

```text
secnews/
  __main__.py    CLI: run | digest, --dry-run
  config.py      reads config.yaml + .env
  db.py          SQLite: items, source_errors
  sources.py     fetch_rss(), fetch_kev()
  filters.py     extract_cves(), match_watchlist(), classify()
  summarize.py   optional LLM call, JSON validation
  telegram.py    render, split, send, handle 429
tests/           pytest; fixtures in tests/fixtures
config.yaml      sources, watchlist, llm, chat_id (no secrets)
.env             TELEGRAM_BOT_TOKEN, LLM_API_KEY (never committed)
```

## Domain context

- **KEV:** CISA's catalog of vulnerabilities exploited in the wild.
- **Watchlist:** products, aliases and keywords the team cares about, in `config.yaml`.
- **ALERT:** CVE in KEV and watchlist match; sent in the same run.
- **DIGEST:** watchlist match only; sent once at 08:30 Vietnam time.
- **SKIP:** everything else, and any CVE already sent or queued in the last 7 days (FR-05).

Telegram limits from SRS §1: at most 20 messages per minute per group, 4,096 characters per message. The code splits at 4,000 and waits 3.5 s between messages.

## Guide map

| Guide | Owns |
| --- | --- |
| [Agent orchestration](agent-orchestration.md) | Triage levels, user-confirmed teams, model and effort per role for Claude Code and Codex, briefs, stop-loss |

## How to use the rules

1. Identify the task ID, the behavior being changed and its FR/NFR/AC. The user's request and the spec take priority over assumptions and old prose.
2. Read only the documents matched by `AGENTS.md`, then inspect the concrete implementation.
3. Keep one owner for each rule. Update a guide when its rule changes; keep `AGENTS.md` and this index focused on routing.
4. Keep the spec and implementation boundary explicit. Build behavior from the owning FR and SDD section, then update TASKS.

Do not treat a green test run, an empty search result or polished prose as proof of runtime behavior. `--dry-run` output and a send to the test group are the evidence for messages.
