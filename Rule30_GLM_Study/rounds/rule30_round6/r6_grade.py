"""Grade a GLM's answers to r6_reasoning_suite.json.

answers.json: {"<id>": {"verdict": "ACCEPT"|"REJECT", "missing_hypothesis": "..."}, ...}
Prints verdict accuracy overall and on held-out items.  Missing-hypothesis text is listed
next to the reference answer for a human (or the GLM's own checker) to judge."""
import json
import sys
from pathlib import Path

suite = json.loads(Path(__file__).with_name("r6_reasoning_suite.json").read_text())["items"]
ans = json.loads(Path(sys.argv[1]).read_text())
tot = ok = tot_h = ok_h = 0
for it in suite:
    a = ans.get(it["id"], {})
    hit = a.get("verdict") == it["verdict"]
    tot += 1; ok += hit
    if it.get("held_out"):
        tot_h += 1; ok_h += hit
    if it["verdict"] == "REJECT":
        print(f"{it['id']}: verdict {'OK ' if hit else 'BAD'} | expected missing hypothesis: "
              f"{it['missing_hypothesis']}\n      given: {a.get('missing_hypothesis')}")
print(f"verdicts {ok}/{tot}; held-out {ok_h}/{tot_h}")
