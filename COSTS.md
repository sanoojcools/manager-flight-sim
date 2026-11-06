# Keeping API spend smart and visible

## 1. Route by the kind of thinking

| Job | How often | Model and effort | Why |
| --- | --- | --- | --- |
| Simulated employee, one reply per turn | 5-12 times per session | Claude Haiku 5.5, effort `low` | Short in-character replies. Speed matters more than depth. |
| Grader, one scorecard per session | Once per session | Claude Opus 5.5, effort `high` | The judgment is the product, so it gets the strongest model. |

List prices (USD per million tokens, checked 2026-11-06): Haiku 5.5 $0.10 in / $0.50 out, Opus 5.5 $4 in / $20 out,
Sonnet 5.5 $2 in / $10 out. That makes Haiku about 40x cheaper than Opus per token.

Change routing without touching code:

```bash
export MFS_EMPLOYEE_MODEL=claude-sonnet-5-5   # if Haiku's role-play feels flat
export MFS_GRADER_EFFORT=medium               # if scorecards hold up at lower effort
```

Do not downgrade the grader until you have checked it against human HR leaders' scores. A cheap wrong grade is
worse than a correct grade that costs more.

## 2. Track every call

- Every API call is written to `runs/usage.jsonl` with its role, model, effort, tokens, latency and dollar cost.
- The app shows this session's cost and your running total next to the chat, and a per-role breakdown on the scorecard.
- `python -m sim.usage` prints totals by role, model and day, plus your cost per session.
- `GET /api/usage` returns the same figures as JSON.

## 3. Cap it

- `MFS_BUDGET_USD` (default $5) is a hard stop inside the app. Once the ledger reaches it, no further calls are made.
- Set a monthly spend limit on your workspace in the Anthropic Console as the final backstop. It also covers
  anything outside this app.
- Use a separate API key and workspace for this project, so its spend shows up on its own line in the Console.

## Measured cost per session (first live runs, 2026-11-06)

7 practice sessions across all four scenarios, 4-5 manager turns each, plus one smoke-test call:

| | Per session | Share |
| --- | --- | --- |
| Employee turns (Haiku 5.5, low) | about $0.001 for 5 turns | 1% |
| Scorecard (Opus 5.5, high) | $0.049-0.070 | 99% |
| **Total** | **$0.050-0.070, average $0.057** | |

At that rate the $5 default cap covers about 85 sessions. A full 12-turn session will cost a little more, mostly
because the grader reads a longer transcript. Prompt caching does not kick in yet: the system prompts are shorter
than the minimum cacheable length, so `cache_read` stays at 0. That costs almost nothing at this size.
