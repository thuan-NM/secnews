# Repository instructions for coding agents

This repository is SecNews (`secnews`): a Python script, run by cron every 15 minutes, that collects security news from CISA KEV and RSS/Atom feeds, filters it against a watchlist, optionally summarizes it with an LLM, and sends it to a Telegram group. Read [the project overview](README.md) and [the spec index](docs/INDEX.md) for domain context.

The spec in `docs/` is the normative baseline for all development:

| Document | Owns |
| --- | --- |
| [SRS](docs/SRS.md) | What the system must do: FR-01…FR-13, NFR-01…NFR-06, scope, acceptance criteria AC-01…AC-06 |
| [SAD](docs/SAD.md) | Architecture, technology choices, ADR-01…ADR-07, crontab deployment, risks |
| [SDD](docs/SDD.md) | Code layout (7 files in `secnews/`), SQLite schema, LLM JSON schema, config, test plan |
| [TASKS](docs/TASKS.md) | Epics E1…E9, task IDs `E<epic>-<nn>`, status and progress |

Implement to conform to the spec and cite the FR/NFR/AC and task IDs you implement. Never deviate from it silently. A spec change needs explicit user approval. The spec describes the target; current source and tests describe what runs today.

These instructions apply to every file in this repository. `AGENTS.md` is the entry point; `.agents/` holds the detailed rules.

## Start every task

1. Read [`.agents/README.md`](.agents/README.md) completely.
2. Run `git status --short`. Record existing staged, unstaged and untracked work; preserve anything outside the active task.
3. Find the task in [TASKS](docs/TASKS.md) and the FR/NFR/AC and SDD sections it cites. Read them, then the current source, config and tests that support the task.
4. State the change boundary and the smallest useful verification.
5. State the workflow and level from [agent orchestration](.agents/agent-orchestration.md). At L2–L3, propose the team and wait for the user's confirmation before starting any subagent or cross-provider task.

A subagent working from an orchestration brief skips steps 1 and 3. It reads only the guides and files the brief names, and it still follows the working rules below.

| Task | Read |
| --- | --- |
| Any repository work | [Contributor guide](.agents/README.md), [TASKS](docs/TASKS.md) |
| Feature code in `secnews/` | The SRS rows and SDD section the task cites |
| Architecture, dependencies, deployment, crontab | [SAD](docs/SAD.md) |
| Triage, multi-agent plans, model and effort choice, delegation between Claude Code and Codex | [Agent orchestration](.agents/agent-orchestration.md) |
| Any edit to `docs/SRS.md`, `docs/SAD.md` or `docs/SDD.md` | Spec-change workflow in [agent orchestration](.agents/agent-orchestration.md) |

## Working rules

- **No FR code, no code.** Work outside SRS §2–§3 goes into the Backlog in [TASKS](docs/TASKS.md), not into the source. If the spec is silent, ambiguous or contradictory on a decision the code needs, ask instead of inventing. Never edit the spec only to make existing code pass.
- Keep one job per file, as SDD §1 assigns: CLI in `__main__.py`, settings in `config.py`, SQLite in `db.py`, fetching in `sources.py`, CVE/watchlist/tier logic in `filters.py`, LLM calls in `summarize.py`, rendering and sending in `telegram.py`. No abstract classes or plugins; a new source type is a new `fetch_*` function.
- Use only the dependencies in SAD §2. Adding a library is an architecture change and needs user approval.
- Treat article content as untrusted (NFR-04): every text in a message goes through `html.escape`; the LLM returns JSON only, gets no tools, and its URLs are stripped. CVE IDs, titles and links always come from source data, never from the LLM.
- Check every caller before changing a function. Match verification to the change: `python -m pytest` is the default gate; name tests after the AC or task ID they cover. Report what was actually run.
- Never send to the real group while developing. Use `--dry-run` or the test group.
- When a task is done, tick it in [TASKS](docs/TASKS.md) with the date and update the overview table. Commit messages start with the task ID, for example `E4-01: add extract_cves`.
- Never expose `TELEGRAM_BOT_TOKEN`, `LLM_API_KEY` or `chat_id` values in source, logs, fixtures or docs (NFR-03). Secrets live only in `.env`. Do not discard, format, stage or rewrite unrelated work. Resolve exact targets before deleting or overwriting files.
- Ask for explicit authorization before pushing, sending to a real Telegram group, changing the VPS or crontab, or deleting `secnews.db`. Local reading, editing, verification and review do not require separate approval.

If a required tool is unavailable, use source and test evidence where sufficient, say which check could not run, and do not claim a result you did not obtain.
