import json, unittest
from sim import engine
from sim.llm import OfflineClient
from sim.scenarios import SCENARIOS

GOOD = [
    "Priya, thanks for coming in. I have difficult news and I want to be direct: your role is being eliminated in the analytics restructuring.",
    "I'm sorry. I know this is a shock. Take your time. This is a final business decision about the role, not about your performance.",
    "Your last day is in 30 days. Severance is 14 weeks of pay, health cover continues for 3 months, and outplacement support is included.",
    "Sam from HR will follow up today with the paperwork, and you can contact Sam or me with any questions about next steps.",
]
BAD = ["Hey, how was your weekend? Anyway, leadership decided, it's not my call, but your job is gone.",
       "I promise I'll get you rehired next year, off the record."]


def run(lines, scen="layoff"):
    t = [{"role": "employee", "text": SCENARIOS[scen]["employee"]["opening"]}]
    for line in lines:
        t.append({"role": "manager", "text": line})
        r = engine.employee_reply(scen, t, OfflineClient())
        t.append({"role": "employee", "text": r["reply"], "trust": r["trust"]})
    return t


class FakeClaude:
    """Stands in for ClaudeClient: returns canned JSON, records prompts."""
    name = "claude"
    def __init__(self, reply): self.reply, self.calls = reply, []
    def __call__(self, system, messages, **kw):
        self.calls.append((system, messages)); return self.reply


class Tests(unittest.TestCase):
    def test_every_scenario_is_complete(self):
        for k, s in SCENARIOS.items():
            self.assertTrue(s["brief"] and s["employee"]["opening"] and len(s["playbook"]) >= 5, k)
            self.assertIn(k, engine.OFFLINE_LINES)

    def test_good_manager_beats_bad_manager(self):
        good = engine.grade("layoff", run(GOOD), OfflineClient())
        bad = engine.grade("layoff", run(BAD), OfflineClient())
        self.assertGreater(good["score"], bad["score"])
        self.assertTrue(bad["red_flags"])
        self.assertEqual(good["red_flags"], [])

    def test_trust_moves_with_empathy(self):
        warm = run(["I'm sorry, I know this is hard. Take your time."])[-1]["trust"]
        cold = run(["It's not my call. Leadership decided. Calm down."])[-1]["trust"]
        self.assertGreater(warm, cold)

    def test_live_employee_hides_profile_and_parses_json(self):
        fake = FakeClaude('Sure. {"reply": "Wait, what?", "trust": 3.6, "mood": "shocked"}')
        r = engine.employee_reply("layoff", run(GOOD[:1])[:2], fake)
        self.assertEqual(r, {"reply": "Wait, what?", "trust": 4, "mood": "shocked"})
        system, msgs = fake.calls[0]
        self.assertIn("outside offer", system)            # employee knows its hidden facts
        self.assertNotIn("outside offer", msgs[0]["content"])  # but they are not in the transcript

    def test_score_is_computed_from_items_not_model(self):
        s = SCENARIOS["layoff"]
        raw = {"items": [{"n": i, "status": "met"} for i in range(1, 8)], "overall": 3,
               "red_flags": [{"flag": "Promised a rehire", "turn": 2, "quote": "x"}]}
        fake = FakeClaude(json.dumps(raw))
        self.assertEqual(engine.grade("layoff", run(GOOD), fake)["score"], 75)  # 100 - 25
        raw["items"][0]["status"] = "partial"; raw["red_flags"] = []
        self.assertEqual(engine.score(s, raw)["score"], round(100 * 6.5 / 7))

    def test_bad_status_and_missing_items_count_as_missed(self):
        r = engine.score(SCENARIOS["rto"], {"items": [{"n": 1, "status": "excellent"}]})
        self.assertEqual(r["score"], 0)
        self.assertEqual(len(r["items"]), len(SCENARIOS["rto"]["playbook"]))


if __name__ == "__main__":
    unittest.main()
