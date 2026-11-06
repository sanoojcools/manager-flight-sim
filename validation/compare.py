"""Compare a human's blind grades with the AI grader's.

    python -m validation.compare <folder of grade JSON files, one per transcript> [ai grades file]

Reports quadratic-weighted kappa on the 0-100 score (binned into 4 bands), item-level
agreement on met / partial / missed, and red-flag agreement.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANDS = (25, 50, 75)  # 0-24 poor, 25-49 weak, 50-74 fair, 75-100 strong


GUT_BAND = {1: 0, 2: 1, 3: 2, 4: 3, 5: 3}  # Poor, Weak, Mixed, Good, Excellent


def band(score):
    return sum(score >= b for b in BANDS)


def human_band(g):
    """Item-based score when the playbook items were filled in, else the overall rating (quick mode)."""
    return band(g["score"]) if g.get("score") is not None else GUT_BAND[int(g["gut"])]


def qwk(a, b, k=4):
    n = len(a)
    if n == 0:
        return None
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x][y] += 1
    ha = [sum(r) for r in obs]
    hb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = (i - j) ** 2 / (k - 1) ** 2
            num += w * obs[i][j]
            den += w * ha[i] * hb[j] / n
    return 1 - num / den if den else 1.0


def main(folder, ai_file=None):
    ai = json.loads(Path(ai_file or HERE / "ai_grades_HIDDEN.json").read_text())
    human = {}
    for f in Path(folder).rglob("*.json"):
        g = json.loads(f.read_text())
        g = g.get("data", g)
        if "items" in g:
            human[g.get("id", f.stem)] = g
    ids = sorted(set(ai) & set(human))
    h_b = [human_band(human[i]) for i in ids]
    a_b = [band(ai[i]["ai_score"]) for i in ids]
    items = [(x, y) for i in ids for x, y in zip(human[i]["items"], ai[i]["ai_items"]) if x]
    flags = [(len(human[i]["flags"]) > 0, ai[i]["ai_red_flags"] > 0) for i in ids]
    print(f"Transcripts compared: {len(ids)}")
    print(f"Score bands, quadratic-weighted kappa: {qwk(h_b, a_b):.2f}")
    print(f"Exact band match: {sum(x == y for x, y in zip(h_b, a_b))}/{len(ids)}")
    print(f"Mean band (0-3): human {sum(h_b)/len(ids):.2f}, AI {sum(a_b)/len(ids):.2f}")
    if items:
        print(f"Playbook item agreement: {sum(x == y for x, y in items)}/{len(items)} ({100*sum(x == y for x, y in items)/len(items):.0f}%)")
    print(f"Any-red-flag agreement: {sum(x == y for x, y in flags)}/{len(flags)}")
    print("\nid   scenario      style      human  AI   gut")
    for i in ids:
        print(f"{i}  {ai[i]['scenario']:<12}  {ai[i]['style']:<9}  {str(human[i].get('score')):>5}  {ai[i]['ai_score']:>3}   {human[i].get('gut')}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
