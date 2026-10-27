"""Round 40, H9 (run-up universality): a stretch of left diagonals driven at its outer edge by the
true eventual patterns, started from ANY filling, reproduces the true eventual pattern after a white
diagonal once the stretch before the white (the run-up c) is long enough.
Validated against the full automaton (./patdump, exact settling certificate) at the known whites."""
import subprocess, json
def pats(Ds):
    out = subprocess.run(["./patdump", "100000", "1"] + [str(d) for d in Ds], capture_output=True, text=True).stdout
    return {int(l.split()[1]): int(l.split()[2], 16) for l in out.split("\n") if l.startswith("PAT")}
res = {}
for w in [28, 399, 53207, 58286, 87866]:
    for c in [10, 30, 100, 300, 1000, 3000, 10000]:
        if c > w - 3: continue
        w0 = w - c
        P = pats([w0 - 2, w0 - 1, w + 1])
        A, B, truth = P[w0 - 2], P[w0 - 1], P[w + 1]
        ok = 0; n = 8
        for fs in range(n):
            out = subprocess.run(["./localband", "64", format(A, "x"), format(B, "x"), str(c + 50), str(fs), "64"],
                                 capture_output=True, text=True).stdout
            lines = [l for l in out.split("\n") if l.startswith("WHITE") and int(l.split()[1]) == c]
            if lines:
                pat = int(lines[0].split()[-1], 16) & ((1 << 64) - 1)
                ok += (pat == truth)
        res[f"w={w} c={c}"] = f"{ok}/{n}"
        print(w, c, f"{ok}/{n}", flush=True)
json.dump(res, open("r40_runup_validation.json", "w"), indent=1)
