"""Run the Round 11 claim suite through the GLM command line and grade it.

From a GLM checkout (the directory holding GLM.py), after the Round 11 setup:
    PYTHONPATH=. python3 rule30_round11/r11_benchmark.py > rule30_round11/r11_benchmark_output.txt
Every claim is sent as `GLM.py -q "tool claim <claim>"` in a fresh interpreter.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
suite = json.load(open(os.path.join(HERE, "r11_reasoning_suite.json")))
score, rows = {}, []
for it in suite["items"]:
    p = subprocess.run([sys.executable, "GLM.py", "-q", "tool claim " + it["claim"]],
                       capture_output=True, text=True, timeout=600)
    out = p.stdout
    got = "REFUSE"
    for v in ("ACCEPT", "REJECT", "OPEN"):
        if f"VERDICT  {v}" in out:
            got = v
    body = out.split("MISSING HYPOTHESIS", 1)[-1].lower()
    ok = got == it["verdict"]
    if ok and it["verdict"] == "REJECT" and it["keyword"]:
        ok = it["keyword"].lower() in body
    sp = it["split"]
    score.setdefault(sp, [0, 0])
    score[sp][0] += ok
    score[sp][1] += 1
    rows.append((it["id"], sp, it["verdict"], got, "PASS" if ok else "FAIL", it["claim"]))
    print(f"== {it['id']} [{sp}] expected {it['verdict']}, got {got}: "
          f"{'PASS' if ok else 'FAIL'}\nCLAIM  {it['claim']}")
    for line in out.splitlines():
        if line.startswith(("ANSWER", "MISSING", "WITNESS", "NEXT", "REFUSED", "UNSOLVED", "(")):
            print("   " + line[:400])
print("\nSCORE by split: " + "; ".join(f"{k}: {a}/{b}" for k, (a, b) in score.items()))
