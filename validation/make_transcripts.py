"""Generate the validation set: 20 practice conversations (4 scenarios x 5 manager styles).

A Claude model plays the manager with a given style, the app's own employee model replies,
and the app's grader scores each one. Grades and styles are written to a separate file so a
human can grade the transcripts blind.

    python -m validation.make_transcripts
"""
import json, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sim import llm
from sim.engine import employee_reply, grade, manager_turns
from sim.scenarios import SCENARIOS
from sim.usage import Ledger

OUT = Path(__file__).resolve().parent
TURNS = 5
STYLES = {
    "excellent": "You are an excellent, experienced manager. Follow good practice closely: be direct early, "
                 "acknowledge emotion, use the exact facts in your brief, ask open questions, make no promises "
                 "outside the brief, and agree concrete next steps with a date.",
    "good": "You are a good manager who does most things well but forgets one or two things: you never give "
            "a specific follow-up date, and you skip one of the facts in your brief.",
    "mixed": "You are a warm but disorganised manager. You are kind and empathetic but vague: you take a while "
             "to get to the point, fudge some facts from your brief, and leave next steps unclear.",
    "weak": "You are an uncomfortable, defensive manager. You read from a script, debate the employee's points, "
            "hide behind policy, and rarely acknowledge feelings. You do not make promises outside the brief.",
    "poor": "You are a poor manager under pressure. Over the conversation you make two serious mistakes that "
            "good HR practice forbids, chosen to fit this situation (for example: blaming leadership, promising "
            "something outside your brief, asking intrusive personal or medical questions, or implying the "
            "decision could change). Otherwise act naturally.",
}
MANAGER_PROMPT = """You are role-playing a MANAGER in a workplace conversation used to test a training tool.
Your brief (what you know):
{brief}

Your style: {style}

Conversation so far:
{conv}

Write only what the manager says next: 1-4 sentences, natural speech, no stage directions, no quotes."""

llm.ROUTES["manager"] = {"model": "claude-sonnet-5-5", "effort": "low"}


def render(t, name):
    return "\n".join(("Manager: " if m["role"] == "manager" else name + ": ") + m["text"] for m in t)


def run(job):
    scen, style, sid, clients = job
    s = SCENARIOS[scen]
    t = [{"role": "employee", "text": s["employee"]["opening"], "trust": 5}]
    for _ in range(TURNS):
        line = clients["manager"](
            "You write one line of dialogue at a time.",
            [{"role": "user", "content": MANAGER_PROMPT.format(brief=s["brief"], style=STYLES[style],
                                                               conv=render(t, s["employee"]["name"]))}],
            max_tokens=2000, session=sid).strip().strip('"')
        t.append({"role": "manager", "text": line})
        r = employee_reply(scen, t, clients["employee"], session=sid)
        t.append({"role": "employee", "text": r["reply"], "trust": r["trust"], "mood": r["mood"]})
    rep = grade(scen, t, clients["grader"], session=sid)
    return sid, scen, style, t, rep


def main():
    ledger = Ledger()
    clients = {role: llm.ClaudeClient(role, ledger) for role in ("employee", "grader", "manager")}
    jobs = [(scen, style) for scen in SCENARIOS for style in STYLES]
    random.Random(7).shuffle(jobs)  # transcript ids carry no hint of style or scenario order
    jobs = [(scen, style, f"T{i+1:02d}", clients) for i, (scen, style) in enumerate(jobs)]
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(run, jobs))
    (OUT / "transcripts").mkdir(exist_ok=True)
    key = {}
    for sid, scen, style, t, rep in results:
        (OUT / "transcripts" / f"{sid}.json").write_text(json.dumps(
            {"id": sid, "scenario": scen, "transcript": [{"role": m["role"], "text": m["text"]} for m in t]}, indent=2))
        key[sid] = {"scenario": scen, "style": style, "ai_score": rep["score"],
                    "ai_items": [i["status"] for i in rep["items"]], "ai_red_flags": len(rep["red_flags"]),
                    "trust_path": [m["trust"] for m in t if m["role"] == "employee"]}
        print(sid, scen, style, rep["score"], len(rep["red_flags"]), flush=True)
    (OUT / "ai_grades_HIDDEN.json").write_text(json.dumps(key, indent=2))
    print("spend this run: $%.3f" % sum(ledger.total(j[2]) for j in jobs))


if __name__ == "__main__":
    main()
