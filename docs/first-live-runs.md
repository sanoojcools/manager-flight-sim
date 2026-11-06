# First live runs: Manager Flight Simulator and Review Receipts (2026-11-06)

Key: `HR_APPS_ANTHROPIC_KEY` from the Default cloud environment. Offline tests still pass (11 + 8).
No live-API errors in either app: the Haiku and Opus calls, effort settings, the server-side fallback beta and JSON
parsing all worked first time.

## Spend

| App | Sessions | Total | Per session | Where the money goes |
| --- | --- | --- | --- | --- |
| Manager Flight Simulator | 7 (+1 smoke call) | $0.40 | $0.050-0.070, avg $0.057 | Opus grader 99%, Haiku employee 1% |
| Review Receipts | 2 | $0.12 | $0.048 (Amira), $0.067 (Jordan) | Opus verifier ~100% |
| **Both** | | **$0.52 of the $10 combined caps** | | |

A session takes about 30 seconds end to end (five employee turns plus the scorecard).

## Flight Sim sessions (scripted manager lines, 4-5 turns each)

| Scenario | Manager style | Score | Red flags |
| --- | --- | --- | --- |
| Role eliminated | Good | 79 | 0 |
| Below-expectations rating | Good | 86 | 0 |
| Raise declined | Good | 79 | 0 |
| Return to office | Good | 64 (twice) | 0 |
| Return to office | Deliberately bad | 0 | 2, then 4 after the fix below |

**Grader quality: strong.** Every verdict quoted the manager's exact words and the reasons were specific. It caught
real gaps a lenient grader would miss: in the layoff, the manager twice ignored Priya's question about her daughter's
health cover; in the raise talk, the manager never answered "who signs off on Senior". The rewrites are usable
coaching lines. The bad-manager run scored 0 with every playbook item missed.

**Employee quality: good, one bug (fixed).** Haiku stays in character, pushes back realistically, and the trust
meter moves sensibly (bad manager: 5 to 3; good manager: 5 to 6). Hidden facts surfaced when earned (Daniel's back
condition) and stayed hidden when not (Marcus's sick parent never came out in 5 turns).

## Fixes made (in `sim/scenarios.py`)

1. **Daniel got the policy wrong** in all three RTO runs ("four days", "five days"), because his profile never said
   what the policy was. The grader then docked the manager for not correcting it. Added the policy (3 days, Tue-Thu)
   to his profile. Re-run: he now says "three days" correctly.
2. **Marcus mixed up his clients.** He said Helix and Orbis were the ones lost to the acquisition. Named the acquired
   clients (Vantage and Corvel) so they no longer collide with the escalation evidence.
3. **"It's not my call / policy is policy" was not a red flag in the RTO scenario.** Added it, matching the layoff
   scenario. The bad-manager re-run now shows 4 red flags.

COSTS.md now has the measured numbers in place of the estimate.

## Review Receipts

Both samples ran cleanly, and the citation audit rejected 0 quotes (every quote the model cited is word for word in
the evidence pack).

- **Jordan:** 7 claims, 2 supported, 5 contradicted, 6 bias flags, evidence score 29. Matches the README exactly. It
  correctly cleared Jordan of the outage, flagged "abrasive and aggressive" as personality language, and flagged "less
  committed" around a family emergency as protected. It also spotted the Q2 payment OKR the review left out.
- **Amira:** 6 claims, 3 supported, 1 contradicted ("consistently beat her hiring targets"), 2 opinions, 4 bias
  flags including "culture fit". Spotted the ignored 4.6/5 candidate-experience score.

## Worth knowing

- Prompt caching never triggers: system prompts are below the minimum cacheable length. Harmless at this size.
- Saved transcripts and scorecards are in each app's `runs/` folder.
