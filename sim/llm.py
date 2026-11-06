"""Model clients and routing.

Two jobs, two models:
  employee  - many short, repetitive role-play turns  -> Claude Haiku 5.5, effort low
  grader    - one careful judgment per session        -> Claude Opus 5.5, effort high
Override with MFS_EMPLOYEE_MODEL / MFS_EMPLOYEE_EFFORT / MFS_GRADER_MODEL / MFS_GRADER_EFFORT.

OfflineClient is a deterministic stand-in so the app and tests run with no key.
"""
import json, os, re, time
from .usage import Ledger

ROUTES = {
    "employee": {"model": os.environ.get("MFS_EMPLOYEE_MODEL", "claude-haiku-5-5"),
                 "effort": os.environ.get("MFS_EMPLOYEE_EFFORT", "low")},
    "grader": {"model": os.environ.get("MFS_GRADER_MODEL", "claude-opus-5-5"),
               "effort": os.environ.get("MFS_GRADER_EFFORT", "high")},
}
# Server-side refusal fallback is available on Opus/Sonnet 5.5 (not Haiku).
FALLBACK_OK = ("claude-opus-", "claude-sonnet-", "claude-fable-")


class RefusalError(RuntimeError):
    pass


class ClaudeClient:
    name = "claude"

    def __init__(self, role, ledger, model=None, effort=None, sdk=None):
        import anthropic  # only needed in live mode
        self.role, self.ledger = role, ledger
        self.model = model or ROUTES[role]["model"]
        self.effort = effort or ROUTES[role]["effort"]
        self.sdk = sdk or anthropic.Anthropic(api_key=api_key())

    def __call__(self, system, messages, max_tokens=4000, session="-"):
        self.ledger.check()
        kw = dict(model=self.model, max_tokens=max_tokens, messages=messages,
                  # The system prompt is identical for every turn of a scenario: cache it.
                  system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                  output_config={"effort": self.effort})
        t0 = time.time()
        if self.model.startswith(FALLBACK_OK):
            resp = self.sdk.beta.messages.create(**kw, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            resp = self.sdk.messages.create(**kw)
        self.ledger.record(session=session, role=self.role, model=self.model, effort=self.effort,
                           usage=resp.usage, latency_s=time.time() - t0)
        if resp.stop_reason == "refusal":
            raise RefusalError("The model declined this turn. Try rephrasing.")
        return "".join(b.text for b in resp.content if b.type == "text")


class OfflineClient:
    """Marker type: engine.py uses rule-based fallbacks when it sees this client."""
    name = "offline"


# Some hosted sandboxes (e.g. Claude Code cloud sessions) reserve ANTHROPIC_API_KEY
# and do not pass it through, so a second name is accepted too.
KEY_VARS = ("ANTHROPIC_API_KEY", "HR_APPS_ANTHROPIC_KEY")


def api_key():
    return next((os.environ[v] for v in KEY_VARS if os.environ.get(v)), None)


def make_clients(ledger=None):
    if not api_key():
        return {"employee": OfflineClient(), "grader": OfflineClient()}
    ledger = ledger or Ledger()
    return {role: ClaudeClient(role, ledger) for role in ROUTES}


def parse_json(text):
    """Pull the first JSON object out of a model reply."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model reply: " + text[:200])
    return json.loads(m.group(0))
