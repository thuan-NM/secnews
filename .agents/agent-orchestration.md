# Agent orchestration

Read this guide before you split work across agents, choose a model or effort level, or delegate between Claude Code and Codex. It applies to both providers. Agents propose a team; the user confirms it. No agent starts a multi-agent plan on its own.

SecNews is small: seven Python files and one SQLite file. Most tasks in [TASKS](../docs/TASKS.md) are L0–L1 and need one agent.

## Usage budget

- Claude Code runs on a Claude Pro plan, and Codex runs on a ChatGPT Plus plan. Each plan has a rolling five-hour limit and a weekly limit shared across its models. Subagents and cross-provider tasks draw from the same allowance as the main session.
- Pro includes Opus, Sonnet and Haiku. Fable is billed as usage credits, outside the plan. Anthropic's Claude Code guidance is to use Sonnet for most coding, keep Opus for complex architecture and multi-step reasoning, and use Haiku for simple subagent work.
- OpenAI's October 2026 Plus estimates per five hours are 5–45 local messages for GPT-6 Astra, 15–160 for GPT-6.1 Sol and 350–3,000 for GPT-6 Luna. GPT-6.1 Terra has no published row. Astra uses the allowance fastest.
- Before L3 work, check the remaining allowance (`/usage` in Claude Code, and the usage page for Codex).

## Default to one agent

1. Triage every task: pick the workflow and level below, and state them in one line before working.
2. L0–L1: work as one agent. Start no subagent.
3. L2–L3: write a team proposal and wait for the user's confirmation before starting any subagent or cross-provider task. The user may change models, effort or stages.
4. Ask again before using GPT-6 Astra or Claude Fable, before escalating a model, before a second review round, and before any stage the confirmed proposal did not include.
5. Subagents never start other agents.

```text
Task: <E?-?? from TASKS> — FR/NFR/AC: <IDs>
Workflow: feature | debug | refactor | optimize | spec-change | ai-agent
Level: L2 | L3 — risk flags: <flags or none>
Stages:
  1. secnews_scout (Haiku 5.5 low | gpt-6-luna low): <what it finds>
  2. lead (Opus 5.5 medium | gpt-6.1-sol medium): <plan output>
  3. secnews_builder (Sonnet 5.5 medium | gpt-6.1-terra medium): <slice>
  4. python -m pytest
  5. secnews_reviewer (<same or other provider>): <what it checks>
Skipped stages and why: <...>
Confirmation points: <...>
```

## Levels

| Level | When | Team | Review |
| --- | --- | --- | --- |
| L0 | Typo, link, one-line config or wording, ticking TASKS | One agent at low effort | None |
| L1 | One to three files, one task, known behavior, tests written alongside | One agent at medium effort | The agent runs the checks |
| L2 | Several files or a whole epic, new integration tests | Lead, builder, reviewer from the same provider | `secnews_reviewer` from the same provider |
| L3 | Any risk flag below | Lead at high effort, builder at high effort, confirmed plan before building | `secnews_reviewer` from the other provider |

Risk flags put a task at L3:

- Deduplication and send bookkeeping: `seen`, `cve_recent`, `mark_sent`, `sent_at` (FR-04, FR-05, NFR-02). A bug here spams or silences the group.
- Message rendering and escaping, or LLM prompts and output handling (FR-09, FR-10, NFR-04). Article content is untrusted.
- Secrets handling: `.env`, tokens, logging (NFR-03).
- SQLite schema changes or anything that can delete `secnews.db`.
- Crontab, `flock` or VPS deployment (SAD §4).
- Edits to `docs/SRS.md`, `docs/SAD.md` or `docs/SDD.md`.

## Roles, models and effort

The lead is the provider of the user's session. At L3 the reviewer comes from the other provider, so the two models check each other's blind spots.

| Role | Responsibility | Claude (Pro) | Codex (Plus) |
| --- | --- | --- | --- |
| Single agent (L0–L1) | The whole task | Sonnet 5.5, low or medium; suggest `/model sonnet` | `gpt-6.1-terra`, low or medium |
| Lead | Triage, plan, investigation, integration, handoff | Opus 5.5, medium; high at L3 | `gpt-6.1-sol`, medium; high at L3 |
| `secnews_scout` | Locate code, callers, tests and spec sections; return `path:line`, never file dumps | Haiku 5.5, low | `gpt-6-luna`, low |
| `secnews_builder` | Implement a written plan and its tests | Sonnet 5.5, medium; high at L3 | `gpt-6.1-terra`, medium; high at L3 |
| `secnews_reviewer` | Independent review of a diff against its brief and FR/AC IDs | Opus 5.5, high | `gpt-6.1-sol`, high |
| Very hard problems, after user confirmation | Only when the lead failed at high effort | Fable 5.1 (usage credits) | `gpt-6-astra` |

Verification is not a model role. The lead runs `python -m pytest`, focused tests and `python -m secnews run --dry-run` directly. Use `secnews_scout` only to summarize output too long to read.

The agent definitions are in `.claude/agents/` and `.codex/agents/`, and their files set the default model and effort. When the confirmed plan uses a different effort, such as a builder at high effort for L3, the lead sets it when starting the agent. Raise effort before moving to a stronger model, and move one step at a time.

## Workflows

**Feature.** At L1, one agent follows the `lean-build` skill. At L2–L3:

1. `secnews_scout` writes the spec brief: the task ID, its FR/NFR/AC rows from SRS, the SDD section and code entry points.
2. The lead plans: acceptance check, slice, files, tests named by AC or task ID, and open spec points for the user. At L3, the user confirms the plan before building.
3. `secnews_builder` implements and runs focused tests.
4. The lead runs `python -m pytest` and, for message changes, `--dry-run`.
5. `secnews_reviewer` reviews, and the lead fixes small findings directly.
6. The lead ticks the task in TASKS.

**Debug.**

1. Reproduce with a failing command or a fixture in `tests/fixtures`. `secnews_scout` summarizes long logs.
2. If the cause is known, follow the `surgical-patch` skill: one agent at L1, otherwise the builder.
3. If the cause is unknown or intermittent, the lead investigates with the `investigate-first` skill at high effort and ranks hypotheses by evidence.
4. After two rejected hypotheses, propose a second opinion from the other provider. Send the symptom, the evidence and the rejected hypotheses, not the transcript.
5. Every fix comes with a regression test that fails before the fix and passes after it.

**Refactor.**

1. Lock behavior first. If coverage is missing, `secnews_builder` writes characterization tests before any structural edit.
2. Use `secnews_scout` to list the callers.
3. The lead plans ordered steps that each move one responsibility between the files in SDD §1, following the `safe-refactor` skill.
4. `secnews_builder` applies the steps at low or medium effort, and the lead verifies after each step.
5. `secnews_reviewer` confirms that behavior is unchanged. A change to the CLI, `config.yaml` format or DB schema makes the task L3.

**Optimize.**

1. Start only with a named metric, workload and baseline, for example run time against N feeds or NFR-01 latency. If they are missing, ask.
2. Measure with commands, and use `secnews_scout` to summarize the output.
3. The lead analyzes at high effort, `secnews_builder` changes the code, and the lead re-measures the same workload.
4. Changes to send ordering, retries, the 3.5 s pacing or the 4,000-character split are contract changes and make the task L3.

**Spec change.** Always L3. Rule: no FR code, no code; a new idea goes to the Backlog first.

1. The user approves the proposal before any edit.
2. The lead edits the owning document at high effort: SRS for requirements, SAD for architecture and ADRs, SDD for design. Add a row to the SRS version table.
3. `secnews_scout` lists every restated count, ID and cross-reference with `path:line` (FR/NFR/AC counts in `docs/INDEX.md`, task rows in TASKS).
4. `secnews_builder` updates TASKS, tests and fixtures to match.
5. Run a link check and `git diff --check`.
6. The cross-provider `secnews_reviewer` checks SRS, SAD and SDD for consistency.

**AI agent.** Changes to `summarize.py` prompts or LLM output handling (FR-09). Usually L3 because LLM output reaches the group.

1. The lead writes the contract from SDD §2.2 and §3.2 at high effort: input, JSON schema, timeout, fallback to snippet.
2. `secnews_builder` implements with a faked LLM in tests, including invalid JSON, timeout and output containing URLs or injected instructions.
3. A live LLM call runs only with user authorization. Record the model, the number of runs and the cost.
4. The cross-provider `secnews_reviewer` checks the contract and its failure paths.

## Briefs and results

A brief to any subagent or delegate fits in about 40 lines:

```text
Goal and acceptance check:
Task ID, workflow, level, risk flags:
SRS rows (FR/NFR/AC) and SDD sections:
Files in scope:
Non-goals:
Verification command:
Attempt limit: 2
Return: the result format below
```

A result fits in about 30 lines: changed files or findings with `path:line`, checks run with their results, FR/AC IDs done and deferred, and open issues or blockers. Do not return transcripts or whole files.

A subagent that has a brief skips the `AGENTS.md` startup reading. It reads only the guides and files the brief names, and it follows the `AGENTS.md` working rules.

## Delegate to the other provider

- In T3 Code, use `delegate_task` to the other provider with the model and effort from the role table, and pass the brief.
- In a terminal, run the other CLI non-interactively:
  - Claude to Codex: `codex exec -m gpt-6.1-sol -c model_reasoning_effort=high -s read-only "<brief>"`
  - Codex to Claude: `claude -p --agent secnews_reviewer "<brief>"`

A delegated reviewer only reports findings. The lead applies the fixes.

## Stop-loss and measurement

- Each stage gets at most two attempts. After the second failure, stop and propose the next step to the user: higher effort, then the stronger model, then the other provider.
- Hold at most two review rounds. Never resend the same brief to the same delegate.
- An L2–L3 handoff reports the task ID, the workflow, the level, each stage with its model and effort, the attempts and review rounds, and the outcome. Note it in the TASKS log. Revise the role table from these records after about 20 tasks.
