"""Tiny web server (standard library; the anthropic package is needed only in live mode).

    python -m sim.server            # http://localhost:8000
"""
import json, os, sys, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .engine import MAX_TURNS, employee_reply, grade, manager_turns
from .llm import make_clients
from .usage import BudgetExceeded, Ledger
from .scenarios import SCENARIOS, public

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
SESSIONS = {}
LEDGER = Ledger()
CLIENTS = make_clients(LEDGER)
MODE = CLIENTS["grader"].name


def start(scenario_id):
    if scenario_id not in SCENARIOS:
        raise KeyError("unknown scenario")
    sid = uuid.uuid4().hex[:12]
    opening = SCENARIOS[scenario_id]["employee"]["opening"]
    SESSIONS[sid] = {"scenario": scenario_id, "started": time.time(),
                     "transcript": [{"role": "employee", "text": opening, "trust": 5}]}
    return {"session": sid, "scenario": public(scenario_id), "mode": MODE, "max_turns": MAX_TURNS}


def say(sid, text):
    s = SESSIONS[sid]
    text = text.strip()[:2000]
    if not text:
        raise ValueError("empty message")
    if manager_turns(s["transcript"]) >= MAX_TURNS:
        raise ValueError("turn limit reached; ask for your scorecard")
    s["transcript"].append({"role": "manager", "text": text})
    r = employee_reply(s["scenario"], s["transcript"], CLIENTS["employee"], session=sid)
    s["transcript"].append({"role": "employee", "text": r["reply"], "trust": r["trust"], "mood": r["mood"]})
    return {**r, "turns_left": MAX_TURNS - manager_turns(s["transcript"]), "spend": LEDGER.summary(sid)}


def finish(sid):
    s = SESSIONS[sid]
    if manager_turns(s["transcript"]) == 0:
        raise ValueError("say something first")
    report = grade(s["scenario"], s["transcript"], CLIENTS["grader"], session=sid)
    report["trust_path"] = [t["trust"] for t in s["transcript"] if t["role"] == "employee"]
    report["spend"] = LEDGER.summary(sid)
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{time.strftime('%Y%m%d-%H%M%S')}-{s['scenario']}-{sid}.json").write_text(
        json.dumps({"scenario": s["scenario"], "mode": MODE, "transcript": s["transcript"],
                    "report": report}, indent=2))
    return report


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, (ROOT / "web" / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/scenarios":
            return self._send(200, {"mode": MODE, "scenarios": [public(k) for k in SCENARIOS]})
        if self.path == "/api/usage":
            return self._send(200, LEDGER.summary())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            n = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/start":
                return self._send(200, start(body.get("scenario", "")))
            if self.path == "/api/say":
                return self._send(200, say(body["session"], body.get("text", "")))
            if self.path == "/api/grade":
                return self._send(200, finish(body["session"]))
            self._send(404, {"error": "not found"})
        except BudgetExceeded as e:
            self._send(402, {"error": str(e)})
        except (KeyError, ValueError) as e:
            self._send(400, {"error": str(e).strip("'")})
        except Exception as e:  # model or network failure: show it, don't crash the server
            self._send(502, {"error": f"{type(e).__name__}: {e}"})

    def log_message(self, *a):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8000))
    print(f"Manager Flight Simulator on http://localhost:{port}  (mode: {MODE})")
    if MODE != "offline":
        print(f"  employee: {CLIENTS['employee'].model} effort={CLIENTS['employee'].effort}  |  "
              f"grader: {CLIENTS['grader'].model} effort={CLIENTS['grader'].effort}  |  "
              f"spent ${LEDGER.total():.4f} of ${LEDGER.budget:.2f} budget")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
