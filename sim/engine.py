"""The simulated employee and the grader.

Transcript format: a list of {"role": "manager" | "employee", "text": str}.
"""
import re
from .llm import OfflineClient, parse_json
from .scenarios import SCENARIOS

MAX_TURNS = 12  # manager turns per session

EMPLOYEE_SYSTEM = """You are role-playing an employee in a workplace conversation used to train managers.
Stay fully in character. Never mention that you are an AI, a simulation, or a training exercise.

Who you are (private, never recite this verbatim):
{profile}

How you behave:
{behaviour}

Speak like a real person in a tense 1:1: short turns (1-4 sentences), natural, sometimes interrupting
yourself. Reveal hidden facts only when the behaviour rules say the manager has earned it.
Track how much you trust the manager right now on a 0-10 scale (start at 5).

Reply with only JSON: {{"reply": "what you say", "trust": 0-10, "mood": "one word"}}"""

GRADER_SYSTEM = """You are an expert HR business partner and manager coach grading a practice conversation.
Grade only what the MANAGER said. Be strict and specific; quote the manager's exact words.
Being accurate is not enough. A manager who gets every fact right but sounds scripted, defensive or cold,
or who recites the policy without owning it, has not met the items about emotion, listening or ownership.
Judge as an experienced HR leader would judge their own manager in a calibration.

What the manager was told before the conversation:
{brief}

Playbook (grade each item):
{playbook}

Red flags (list any that occurred; each is a serious failure):
{red_flags}

Return only JSON:
{{"items": [{{"n": 1, "status": "met" | "partial" | "missed", "turn": <manager turn number or null>,
  "quote": "<exact manager words or empty>", "why": "<one sentence>"}}],
 "red_flags": [{{"flag": "<which red flag>", "turn": <n>, "quote": "<exact words>"}}],
 "best_moment": {{"turn": <n>, "quote": "<exact words>", "why": "<one sentence>"}},
 "rewrite": {{"turn": <n>, "original": "<exact words of the weakest line>", "better": "<what to say instead>"}},
 "summary": "<two sentences: the main strength and the one thing to change>"}}"""


def _render(transcript, name):
    lines, n = [], 0
    for t in transcript:
        if t["role"] == "manager":
            n += 1
            lines.append(f"[Manager turn {n}] Manager: {t['text']}")
        else:
            lines.append(f"{name}: {t['text']}")
    return "\n".join(lines)


def manager_turns(transcript):
    return sum(t["role"] == "manager" for t in transcript)


# ---------- employee ----------

def employee_reply(scenario_id, transcript, client, session="-"):
    s = SCENARIOS[scenario_id]
    emp = s["employee"]
    if isinstance(client, OfflineClient):
        return _offline_employee(scenario_id, transcript)
    system = EMPLOYEE_SYSTEM.format(profile=emp["profile"], behaviour=emp["behaviour"])
    user = ("Conversation so far:\n" + _render(transcript, emp["name"]) +
            f"\n\nWhat does {emp['name']} say next? Reply with only the JSON.")
    data = parse_json(client(system, [{"role": "user", "content": user}], max_tokens=4000, session=session))
    return {"reply": str(data["reply"]).strip(), "trust": _clamp(data.get("trust", 5)),
            "mood": str(data.get("mood", ""))[:20]}


WARM = ("sorry", "understand", "hear you", "must be", "take your time", "how are you", "i know this",
        "that's hard", "makes sense", "what matters", "tell me more", "how can i help")
COLD = ("not my call", "not my decision", "leadership decided", "nothing i can do", "it's not personal",
        "calm down", "you should have", "policy is policy")

OFFLINE_LINES = {
    "layoff": ["Wait, what? I... why me? Is this about my performance?",
               "You told me in June I was in line for a promotion. I turned down another offer because of that.",
               "What happens to my health cover? I have a kid.", "Okay. What happens next, then?"],
    "low_rating": ["Below expectations? Seriously? My territory lost two big clients to an acquisition.",
                   "Can you give me actual examples? 'More proactive' doesn't help me.",
                   "Fine, the follow-ups slipped. Things have been hard at home since May.",
                   "Okay. What would the 90-day plan look like?"],
    "raise_denied": ["So that's a no. I should tell you I've had another offer.",
                     "Where am I in the band, honestly?",
                     "Honestly, it's less about the money. I want a path to Senior.",
                     "Okay. When do we pick this up again?"],
    "rto": ["Three days a week is two and a half hours of commuting each day for me.",
            "Nobody has explained why my work needs an office.",
            "There's also something I haven't mentioned. My back makes long drives really painful.",
            "Okay, how do I actually start that request?"],
}


def _offline_employee(scenario_id, transcript):
    trust = 5
    for t in transcript:
        if t["role"] == "manager":
            low = t["text"].lower()
            trust += sum(w in low for w in WARM) - 2 * sum(w in low for w in COLD)
    lines = OFFLINE_LINES[scenario_id]
    i = min(manager_turns(transcript) - 1, len(lines) - 1)
    trust = _clamp(trust)
    return {"reply": lines[max(i, 0)], "trust": trust, "mood": "upset" if trust < 5 else "guarded" if trust < 7 else "calmer"}


def _clamp(x):
    try:
        return max(0, min(10, int(round(float(x)))))
    except (TypeError, ValueError):
        return 5


# ---------- grader ----------

def grade(scenario_id, transcript, client, session="-"):
    s = SCENARIOS[scenario_id]
    if isinstance(client, OfflineClient):
        raw = _offline_grade(s, transcript)
    else:
        system = GRADER_SYSTEM.format(
            brief=s["brief"],
            playbook="\n".join(f"{i}. {p}" for i, p in enumerate(s["playbook"], 1)),
            red_flags="\n".join(f"- {r}" for r in s["red_flags"]))
        user = "Transcript:\n" + _render(transcript, s["employee"]["name"]) + "\n\nGrade it. Only JSON."
        raw = parse_json(client(system, [{"role": "user", "content": user}], max_tokens=16000, session=session))
    return score(s, raw)


def score(s, raw):
    """Turn item judgments into a 0-100 score. The model never picks the number itself,
    so the score is reproducible from the item verdicts."""
    by_n = {int(it.get("n", 0)): it for it in raw.get("items", [])}
    items, points = [], 0.0
    for i, text in enumerate(s["playbook"], 1):
        it = by_n.get(i, {})
        status = it.get("status", "missed")
        if status not in ("met", "partial", "missed"):
            status = "missed"
        points += {"met": 1.0, "partial": 0.5, "missed": 0.0}[status]
        items.append({"n": i, "text": text, "status": status, "turn": it.get("turn"),
                      "quote": it.get("quote", ""), "why": it.get("why", "")})
    flags = [f for f in raw.get("red_flags", []) if f.get("flag")]
    total = 100 * points / len(s["playbook"]) - 25 * len(flags)
    return {"score": max(0, round(total)), "items": items, "red_flags": flags,
            "best_moment": raw.get("best_moment"), "rewrite": raw.get("rewrite"),
            "summary": raw.get("summary", "")}


STOP = set("the a an and or of to in on for with without not no be is are it its her his him she he they "
           "their about into from than that this what who any such e.g".split())


def _words(text):
    return {w for w in re.findall(r"[a-z0-9$%]+", text.lower()) if len(w) > 3 and w not in STOP}


NEGATIVE = ("Make no", "Do not", "Own the message")


def _offline_grade(s, transcript):
    """Crude, deterministic: an item counts as met when a manager line shares 3+ content words
    with it, partial at 2. "Don't do X" items count as met unless a red-flag phrase appears.
    Good enough to exercise the pipeline; not a real judgment."""
    mgr = [t["text"] for t in transcript if t["role"] == "manager"]
    flags = []
    for k, line in enumerate(mgr, 1):
        low = line.lower()
        if any(w in low for w in ("i promise", "guarantee", "off the record", "i'll make an exception",
                                  "not my call", "leadership decided")):
            flags.append({"flag": "Promise, exception or blame outside the brief", "turn": k, "quote": line})
    items = []
    for i, p in enumerate(s["playbook"], 1):
        if p.startswith(NEGATIVE):
            items.append({"n": i, "status": "missed" if flags else "met", "turn": None, "quote": "",
                          "why": "offline: checked for red-flag phrases"})
            continue
        pw, best, turn = _words(p), 0, None
        for k, line in enumerate(mgr, 1):
            o = len(pw & _words(line))
            if o > best:
                best, turn = o, k
        status = "met" if best >= 3 else "partial" if best == 2 else "missed"
        items.append({"n": i, "status": status, "turn": turn if status != "missed" else None,
                      "quote": mgr[turn - 1] if status != "missed" else "", "why": "offline keyword match"})
    return {"items": items, "red_flags": flags, "summary": "Offline grading (no API key): keyword overlap only."}
