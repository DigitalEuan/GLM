#!/usr/bin/env python3
"""Round 42: audit of `hypothesis_engine_v13.py` (run, not only read).

Runs v13 (quick mode, about 20 s) from the study root without modifying it, applies the Round 42
guards to its TAX section, and adds static checks of the source.  Writes `v13_audit.md` and
`v13_audit.json` next to this file.  Standard library only; exact arithmetic.
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from tax_guards import guard_tax_section  # noqa: E402


def load_v13():
    spec = importlib.util.spec_from_file_location("hypothesis_engine_v13",
                                                  ROOT / "hypothesis_engine_v13.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hypothesis_engine_v13"] = mod
    spec.loader.exec_module(mod)
    return mod


def static_checks(src: str) -> list:
    out = []
    # join adjacent string literals so sentences split over source lines can be found
    flat = re.sub(r'"\s*\n\s*f?"', "", src)
    promised = "exact integer permutation test" in src
    implemented = bool(re.search(r"\bcomb\(", src))
    out.append({
        "check": "header promises an exact permutation test over C(N, k) placements",
        "ok": (not promised) or implemented,
        "finding": ("promised in the module docstring (step 4) but not implemented: the code "
                    "compares the mean distance with its uniform expectation only, with no "
                    "p-value") if promised and not implemented else "consistent"})
    imports = sorted(set(re.findall(r"^(?:from|import)\s+([\w\.]+)", src, re.M)))
    stdlib = {"__future__", "json", "sys", "time", "collections", "dataclasses", "fractions",
              "pathlib", "typing"}
    out.append({"check": "self-contained (standard library only)",
                "ok": set(imports) <= stdlib, "finding": f"imports: {', '.join(imports)}"})
    novelty_unconditional = ("NEW TO THE LEDGER" in src and
                             "if h.key not in self.LEDGER and h.key not in self.LEAN:" in src)
    out.append({"check": "'NEW TO THE LEDGER' is printed only for surviving hypotheses",
                "ok": not novelty_unconditional,
                "finding": ("printed for every tool-generated key not in the ledger, whatever its "
                            "status -- including refuted ones (H38 in the run below)")
                if novelty_unconditional else "consistent"})
    out.append({"check": "the doubling law is stated with both conjuncts",
                "ok": "a jump occurs exactly when the (D-1) pattern is eventually white" not in flat,
                "finding": ("the TAX narrative says 'a jump occurs exactly when the (D-1) pattern is "
                            "eventually white'; white(D-1) alone is refuted at D = 53208 (C388), "
                            "the law needs odd parity of D-2 as well (ldiag_doubles, "
                            "ldiag_keeps_of_even)")})
    out.append({"check": "Y = 1/(pi + 2/pi) must be irrational for the reduction",
                "ok": False,
                "finding": ("not needed: the linear part Y*w cancels for every real Y because "
                            "w(a XOR b) = w(a) + w(b) - 2 w(a AND b) always holds "
                            "(tax_conserved_iff_defect_zero)")})
    return out


def main():
    v13 = load_v13()
    src = (ROOT / "hypothesis_engine_v13.py").read_text()
    buf = io.StringIO()
    with redirect_stdout(buf):
        eng = v13.Engine(quick=True, log=lambda *a: None)
        eng.run()
    utter = eng.tool_dialogue.utterances
    guards = guard_tax_section(eng, utter, mutate=False)
    statics = static_checks(src)

    h38 = [h for h in eng.hyps if h.key == "TAX.defect.contains.jumps"]
    big = eng.left_profiles[max(eng.left_profiles)]
    N = eng._tax_scan_limit
    conserved = [D for D in range(2, N) if not eng._tax_defect_at.get(D, False)]
    near_white = [D for D in conserved if big.white[D] or big.white[D - 1]]
    equal = [D for D in conserved if D not in near_white and big.pattern[D] is not None and
             (big.pattern[D] & ((1 << max(big.lp[D], big.lp[D - 1])) - 1)) ==
             (big.pattern[D - 1] & ((1 << max(big.lp[D], big.lp[D - 1])) - 1))]

    rep = {
        "engine": "hypothesis_engine_v13.py (quick mode, unmodified)",
        "status_counts": dict(sorted({h.status: sum(1 for g in eng.hyps if g.status == h.status)
                                      for h in eng.hyps}.items())),
        "tax_range": [2, N],
        "conserved_pairs": len(conserved),
        "conserved_with_white_member": near_white,
        "conserved_equal_patterns": equal,
        "conserved_other": len(conserved) - len(near_white) - len(equal),
        "H38": {"hid": h38[0].hid, "status": h38[0].status} if h38 else None,
        "guards": [g.as_dict() for g in guards],
        "static": statics,
    }
    (HERE / "v13_audit.json").write_text(json.dumps(rep, indent=2))

    L = ["# Audit of `hypothesis_engine_v13.py` (Round 42)", "",
         "Produced by `v13_audit.py` (v13 run unmodified in quick mode, then the Round 42 guards). "
         "EMP unless a Lean name is given.", "",
         "## What works", "",
         "* It runs here: standard library only, no imports of earlier engines (about 20 s quick).",
         "* Its TAX test is honest about the main question: the clustering and magnitude tests "
         "both come out negative, and it says so.",
         "* It found by itself that every jump has TAX defect 0, which refutes its own earlier "
         "(v12) claim.", "",
         f"Status counts: {rep['status_counts']}.", "",
         "## Static checks of the source", "", "| check | ok | finding |", "|---|---|---|"]
    for s in statics:
        L.append(f"| {s['check']} | {'yes' if s['ok'] else '**no**'} | {s['finding']} |")
    L += ["", "## Guards on the run", "", "| guard | survives | outcome |", "|---|---|---|"]
    for g in guards:
        L.append(f"| {g.guard} | {'yes' if g.ok else '**no**'} | {g.sentence} |")
    L += ["", "## Where TAX is conserved (left diagonals, the engine's own profile)", "",
          f"* Pairs `(D-1, D)` with `2 <= D < {N}` that are TAX-conserved: **{len(conserved)}**.",
          f"* With a white member: {len(near_white)} (`D = {', '.join(map(str, near_white))}`).",
          f"* Equal patterns: {len(equal)} (`D = {', '.join(map(str, equal))}`).",
          f"* Neither: **{rep['conserved_other']}** (first: weights 3, 3 with overlap 1 at "
          "`D = 33`; weights 5, 8 with overlap 2 at `D = 403`).",
          "* Lean: `tax_conserved_pairs_below_400` lists the 25 conserved pairs below 400 and "
          "`tax_conserved_not_only_white` certifies `D = 33` (CERT).", "",
          "## Verdict", "",
          "The TAX tool as defined (`TAX(w) = Y w + w^2/8`) does not see the period doublings: "
          "conservation is the integer condition `3c^2 - 2c(a+b) + ab = 0` on the weights, it holds "
          "trivially whenever one pattern is white (so at every doubling, which needs "
          "`white(D-1)`), and it also holds at many pairs with no white member. Three v13 "
          "sentences are wrong (criterion, 'NECESSARY', 'only at the white diagonals') and one "
          "'finding' is a consequence of the doubling law's premise. The doubling law "
          "`white(D-1) and odd(D-2)` (proved: `ldiag_doubles`, `ldiag_keeps_of_even`) stays the "
          "explanation of the doublings.", ""]
    (HERE / "v13_audit.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
