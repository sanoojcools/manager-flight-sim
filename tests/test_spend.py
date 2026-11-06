import tempfile, unittest
from types import SimpleNamespace as NS
from sim import engine
from sim.llm import ClaudeClient, RefusalError
from sim.usage import BudgetExceeded, Ledger, cost


class FakeSDK:
    """Records what would be sent to the API and returns a canned response."""
    def __init__(self, text='{"reply": "Hi", "trust": 5, "mood": "ok"}', stop="end_turn"):
        self.sent = []
        resp = NS(content=[NS(type="text", text=text)], stop_reason=stop,
                  usage=NS(input_tokens=1000, output_tokens=200, cache_read_input_tokens=0,
                           cache_creation_input_tokens=0))
        def create(**kw):
            self.sent.append(kw)
            return resp
        self.messages = NS(create=create)
        self.beta = NS(messages=NS(create=create))


def ledger(budget=5):
    return Ledger(tempfile.mktemp(suffix=".jsonl"), budget_usd=budget)


class SpendTests(unittest.TestCase):
    def test_prices(self):
        self.assertAlmostEqual(cost("claude-haiku-5-5", 1_000_000, 1_000_000), 0.60)
        self.assertAlmostEqual(cost("claude-opus-5-5", 1_000_000, 1_000_000), 24.00)

    def test_routing_cheap_employee_deep_grader(self):
        led, sdk = ledger(), FakeSDK()
        emp = ClaudeClient("employee", led, sdk=sdk)
        t = [{"role": "employee", "text": "Hi"}, {"role": "manager", "text": "Hello"}]
        engine.employee_reply("layoff", t, emp, session="s1")
        sent = sdk.sent[0]
        self.assertEqual((sent["model"], sent["output_config"]["effort"]), ("claude-haiku-5-5", "low"))
        self.assertNotIn("temperature", sent)   # current models reject non-default sampling
        self.assertNotIn("fallbacks", sent)     # Haiku has no server-side fallback
        self.assertEqual(sent["system"][0]["cache_control"], {"type": "ephemeral"})

        sdk2 = FakeSDK('{"items": []}')
        grader = ClaudeClient("grader", led, sdk=sdk2)
        engine.grade("layoff", [{"role": "manager", "text": "x"}], grader, session="s1")
        g = sdk2.sent[0]
        self.assertEqual((g["model"], g["output_config"]["effort"], g["fallbacks"]),
                         ("claude-opus-5-5", "high", "default"))

        s = led.summary("s1")
        self.assertEqual(s["calls"], 2)
        self.assertAlmostEqual(s["usd"], round(cost("claude-haiku-5-5", 1000, 200) +
                                               cost("claude-opus-5-5", 1000, 200), 4))

    def test_budget_stops_calls_before_spending(self):
        led, sdk = ledger(budget=0.001), FakeSDK()
        c = ClaudeClient("grader", led, sdk=sdk)
        c("sys", [{"role": "user", "content": "x"}])   # costs $0.008, crosses the budget
        with self.assertRaises(BudgetExceeded):
            c("sys", [{"role": "user", "content": "x"}])
        self.assertEqual(len(sdk.sent), 1)

    def test_ledger_survives_restart(self):
        led = ledger()
        ClaudeClient("employee", led, sdk=FakeSDK())("sys", [{"role": "user", "content": "x"}], session="a")
        self.assertEqual(Ledger(led.path).summary()["calls"], 1)

    def test_refusal_is_recorded_then_raised(self):
        led = ledger()
        c = ClaudeClient("grader", led, sdk=FakeSDK(stop="refusal"))
        with self.assertRaises(RefusalError):
            c("sys", [{"role": "user", "content": "x"}])
        self.assertEqual(led.summary()["calls"], 1)


if __name__ == "__main__":
    unittest.main()
