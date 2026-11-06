"""Spend tracking. Every model call is written to runs/usage.jsonl with its tokens and
dollar cost, and a budget cap stops calls before they happen once it is spent.

    python -m sim.usage          # spend report by role, model and day
"""
import json, os, threading, time
from collections import defaultdict
from pathlib import Path

# USD per million tokens, Anthropic first-party list prices (checked 2026-11-06).
# cache_write is 1.25x input for the default 5-minute cache.
PRICES = {
    "claude-opus-5-5":   {"input": 4.00, "output": 20.00, "cache_read": 0.20, "cache_write": 5.00},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20, "cache_write": 2.50},
    "claude-haiku-5-5":  {"input": 0.10, "output": 0.50,  "cache_read": 0.01, "cache_write": 0.125},
}

LEDGER_PATH = Path(__file__).resolve().parent.parent / "runs" / "usage.jsonl"


class BudgetExceeded(RuntimeError):
    pass


def cost(model, input_tokens=0, output_tokens=0, cache_read=0, cache_write=0):
    p = PRICES.get(model)
    if p is None:  # unknown model: price it as Opus so the estimate errs high
        p = PRICES["claude-opus-5-5"]
    return (input_tokens * p["input"] + output_tokens * p["output"] +
            cache_read * p["cache_read"] + cache_write * p["cache_write"]) / 1e6


class Ledger:
    def __init__(self, path=LEDGER_PATH, budget_usd=None):
        self.path = Path(path)
        self.budget = float(budget_usd if budget_usd is not None else os.environ.get("MFS_BUDGET_USD", 5))
        self.lock = threading.Lock()
        self.rows = []
        if self.path.exists():
            self.rows = [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def total(self, session=None):
        return sum(r["usd"] for r in self.rows if session is None or r["session"] == session)

    def check(self):
        """Call before every model request."""
        if self.total() >= self.budget:
            raise BudgetExceeded(f"Budget of ${self.budget:.2f} reached (spent ${self.total():.4f}). "
                                 "Raise MFS_BUDGET_USD to continue.")

    def record(self, *, session, role, model, effort, usage, latency_s):
        u = {"input": getattr(usage, "input_tokens", 0) or 0,
             "output": getattr(usage, "output_tokens", 0) or 0,
             "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
             "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0}
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "session": session, "role": role, "model": model,
               "effort": effort, **u, "latency_s": round(latency_s, 2),
               "usd": round(cost(model, u["input"], u["output"], u["cache_read"], u["cache_write"]), 6)}
        with self.lock:
            self.rows.append(row)
            self.path.parent.mkdir(exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return row

    def summary(self, session=None):
        rows = [r for r in self.rows if session is None or r["session"] == session]
        by_role = defaultdict(lambda: {"calls": 0, "usd": 0.0, "output": 0})
        for r in rows:
            b = by_role[f"{r['role']} ({r['model']})"]
            b["calls"] += 1; b["usd"] += r["usd"]; b["output"] += r["output"]
        return {"usd": round(sum(r["usd"] for r in rows), 4), "calls": len(rows),
                "by_role": {k: {**v, "usd": round(v["usd"], 4)} for k, v in by_role.items()},
                "budget_usd": self.budget, "total_usd": round(self.total(), 4)}


def report(path=LEDGER_PATH):
    led = Ledger(path)
    if not led.rows:
        print("No paid calls yet."); return
    days = defaultdict(float)
    for r in led.rows:
        days[r["ts"][:10]] += r["usd"]
    s = led.summary()
    sessions = {r["session"] for r in led.rows}
    print(f"Total ${s['total_usd']:.4f} of ${s['budget_usd']:.2f} budget, {s['calls']} calls, "
          f"{len(sessions)} sessions, ${s['total_usd'] / len(sessions):.4f} per session")
    for k, v in sorted(s["by_role"].items(), key=lambda kv: -kv[1]["usd"]):
        print(f"  {k:40s} {v['calls']:5d} calls  ${v['usd']:.4f}  ({100 * v['usd'] / max(s['total_usd'], 1e-9):.0f}%)")
    for d, usd in sorted(days.items()):
        print(f"  {d}  ${usd:.4f}")


if __name__ == "__main__":
    report()
