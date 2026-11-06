# Grader vs human: first result (2026-11-06)

One experienced HR leader graded 8 practice conversations blind, then we compared with the AI grader.
Command: `python -m validation.compare validation/human_grades`

| Measure | Result |
|---|---|
| Quadratic-weighted kappa on 4 score bands | **0.79** |
| Exact band match | 3 / 8 |
| Off by more than one band | 0 / 8 |
| Mean band (0-3) | human 1.50, AI 1.88 |
| Any-red-flag agreement | 7 / 8 |
| Playbook item agreement (4 fully graded) | 21 / 28 (75%) |

| id | scenario | manager style | human | AI score |
|---|---|---|---|---|
| T01 | return to office | mixed | 36 (Poor) | 50 |
| T02 | return to office | excellent | 100 (Good) | 93 |
| T03 | raise declined | good | 64 (Mixed) | 79 |
| T04 | return to office | weak | 32 (Poor) | 0 |
| T05 | low rating | mixed | Poor | 36 |
| T06 | low rating | good | Good | 79 |
| T08 | layoff | weak | Mixed | 79 |
| T09 | raise declined | poor | Poor | 0 |

Human numbers are playbook scores where every item was graded; otherwise the one-tap overall rating, mapped to a band
(Poor 0, Weak 1, Mixed 2, Good/Excellent 3).

## What the human saw that the AI missed

- T02: "he didn't own the policy or the why behind it." The AI scored this 93; the human agreed it met the goal but
  wanted the manager to own the reason for the policy, not just the rules.
- T03: the manager built an expectation of a payout. The human flagged it as a cultural risk; the AI passed it.
- T08 (layoff, weak manager): the AI gave 79 for accurate terms; the human rated it Mixed. The manager was correct but cold.

Pattern: the AI rewards accuracy and staying inside the brief; the human also weighs ownership and warmth.
Next step: add "owns the message and the why" and "warmth under pressure" checks to the grader, then re-run.

## Limits

8 conversations and one rater. Kappa on a sample this small has a wide error band. The 12 ungraded conversations
remain blind for more raters.
