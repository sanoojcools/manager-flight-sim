"""Re-grade transcripts with the current grader, for the ones a human has graded.

    python -m validation.regrade <human grades folder> <output file>

Writes the same shape as ai_grades_HIDDEN.json (only for the graded ids), so
`python -m validation.compare <folder> <output file>` compares the new grader.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sim import llm
from sim.engine import grade
from sim.usage import Ledger

HERE = Path(__file__).resolve().parent


def main(folder, out):
    old = json.loads((HERE / "ai_grades_HIDDEN.json").read_text())
    ids = sorted({json.loads(f.read_text()).get("id", f.stem) for f in Path(folder).rglob("*.json")} & set(old))
    client = llm.make_clients(Ledger())["grader"]

    def one(i):
        t = json.loads((HERE / "transcripts" / f"{i}.json").read_text())
        g = grade(t["scenario"], t["transcript"], client, session=f"regrade-{i}")
        return i, {**old[i], "ai_score": g["score"], "ai_items": [x["status"] for x in g["items"]],
                   "ai_red_flags": len(g["red_flags"]), "summary": g["summary"]}

    with ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(one, ids))
    Path(out).write_text(json.dumps(res, indent=2))
    for i in ids:
        print(i, old[i]["ai_score"], "->", res[i]["ai_score"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
