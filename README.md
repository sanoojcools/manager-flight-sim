# Manager Flight Simulator

**Practise the hardest conversations a manager has, on a simulated employee, and get graded against the playbook.**

Modelled on the pattern that won 1st place at Anthropic's *Built with Opus 4.7* hackathon (Medkit: doctors treat
simulated patients and are graded against clinical guidelines). Here the patient is an employee and the guidelines
are an HR playbook.

## What it does

1. Pick a scenario: **role eliminated**, **below-expectations rating**, **raise request declined**, **return-to-office pushback**.
2. Read your brief. It holds only what a real manager would know.
3. Talk to the employee. They have a hidden backstory (a declined outside offer, a sick parent, an undisclosed health
   condition) that comes out only if you earn it. A live **trust meter** shows how it's landing.
4. End the conversation and get a **scorecard**: each playbook item is marked met, partial or missed with the exact line
   you said, plus red flags (promises outside policy, blame, intrusive questions), your best moment, and a rewrite of your weakest line.

The score is computed from the item verdicts (met = 1, partial = 0.5, each red flag -25), never picked by the model, so
it is reproducible and auditable. Every finished session is saved to `runs/` for later validation.

## Run it

Python 3.10+. Offline mode needs nothing else; live mode needs `pip install -r requirements.txt`.

```bash
python -m sim.server                 # offline demo mode, no key: scripted employee, keyword grader
export ANTHROPIC_API_KEY=sk-ant-...  # live mode: Claude plays the employee and grades
# (In a Claude Code cloud session, name the variable HR_APPS_ANTHROPIC_KEY instead; the sandbox does not pass ANTHROPIC_API_KEY through.)
export MFS_BUDGET_USD=5              # hard spending cap for the app (default $5)
python -m sim.server                 # open http://localhost:8000
python -m sim.usage                  # spend report
python -m unittest -v tests.test_sim tests.test_spend
```

The employee runs on Claude Haiku 5.5 at low effort (many quick turns); the grader runs on Claude Opus 5.5 at
high effort (one careful judgment). Every call is logged with its cost. See [COSTS.md](COSTS.md).

## Does the grader agree with a human expert?

An AI grader is only useful if it judges the way an experienced HR leader would. `validation/` holds the test:

- 20 practice conversations (4 scenarios x 5 manager styles, from excellent to poor), made with
  `python -m validation.make_transcripts`. A Claude model plays the manager; the app's own employee and grader do the rest.
- A certified Amazon Bar Raiser grades all 20 blind, without seeing the AI's grades (kept out of this repo until then).
- `python -m validation.compare <grades folder>` reports quadratic-weighted kappa on score bands, item-level
  agreement and red-flag agreement.

**Result: pending.** It will be published here, good or bad.

Measured cost and the first live test: [COSTS.md](COSTS.md) and [docs/first-live-runs.md](docs/first-live-runs.md).
`web/explainer.html` is a one-page explainer of why this matters for CHROs, managers, employees, L&D teams and hiring panels.

## Next

- Add more raters (HR leaders grading one transcript each) to move from one expert to a panel.
- More scenarios: PIP start, harassment complaint intake, a counter-offer, delivering a promotion "no".
- Voice mode, so the practice feels like the real room.

## Ground rules

All people and companies in the scenarios are fictional. Playbooks are the author's own good-practice summaries,
not legal advice.
