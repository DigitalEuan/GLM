#!/usr/bin/env python3
"""Apply the Round 42 guards (`glm_guards.py`) to the TAX section of a v13-style engine.

`guard_tax_section(eng, utterances, mutate)` takes an Engine that has run
`run_tool_driven_generation` and `run_tax_period_doubling_correlation` (it reads
`eng._tax_defect_at`, `eng._tax_scan_limit`, the largest left profile and `eng.hyps`), and returns
a list of `GuardResult`s.  With `mutate=True` it also writes the outcome into the hypotheses:
a guard that refutes a hypothesis sets its status to `refuted-by-guard`, a guard that explains a
"finding" away sets its novelty to "consequence of a known law".

Lean backing (RequestProject/GLM/HypothesisEngine/):
  TaxChecks.lean      tax_defect_eq, tax_conserved_iff_defect_zero, docstring_criterion_wrong,
                      tax_conserved_of_right_empty, tax_conserved_at_doubling
  TaxChecksData.lean  tax_conserved_pairs_below_400, tax_conserved_nontrivial_below_400,
                      tax_conserved_not_only_white
"""

from __future__ import annotations

from glm_guards import (Premise, coincidence_test, consistency_guard, exclusivity_guard,
                        explained_away_guard, identity_guard)

JUMPS = [3, 8, 29, 400, 87867]          # least periods 2, 4, 8, 16, 32 first occur here (CERT)

LEAN = {
    "criterion": "GLM.HypothesisEngine.Tax.docstring_criterion_wrong",
    "closed_form": "GLM.HypothesisEngine.Tax.tax_defect_eq",
    "Y_free": "GLM.HypothesisEngine.Tax.tax_conserved_iff_defect_zero",
    "white_pair": "GLM.HypothesisEngine.Tax.tax_conserved_of_right_empty",
    "at_doubling": "GLM.HypothesisEngine.Tax.tax_conserved_at_doubling",
    "not_only_white": "GLM.HypothesisEngine.Tax.tax_conserved_not_only_white",
}


def _defect(a, b, c):
    return a * a + b * b - 2 * c * c - (a + b - 2 * c) ** 2


def _big_profile(eng):
    if hasattr(eng, "left_profiles") and eng.left_profiles:
        return eng.left_profiles[max(eng.left_profiles)]
    return eng.left_dev


def guard_tax_section(eng, utterances: list, mutate: bool = False) -> list:
    results = []
    big = _big_profile(eng)
    N = eng._tax_scan_limit
    defect_at = eng._tax_defect_at
    dom = list(range(2, N))
    conserved = [D for D in dom if not defect_at.get(D, False)]
    jumps = [J for J in JUMPS if J < N]
    white = big.white

    # 1. the stated criterion
    box = [(a, b, c) for a in range(13) for b in range(13) for c in range(min(a, b) + 1)]
    r = identity_guard("v13 docstring 'conserved iff w(a AND b) in {0, w(a), w(b)}'",
                       lambda a, b, c: c in (0, a, b), lambda a, b, c: _defect(a, b, c) == 0, box)
    r.data["lean"] = LEAN["criterion"]
    results.append(r)
    r = identity_guard("closed form 'defect = -2(3c^2 - 2c(a+b) + ab)'",
                       lambda a, b, c: _defect(a, b, c) == -2 * (3 * c * c - 2 * c * (a + b) + a * b),
                       lambda a, b, c: True, box)
    r.data["lean"] = LEAN["closed_form"]
    results.append(r)

    # 2. "TAX is conserved at every jump" -- a finding, or a consequence of white(D-1)?
    prem = Premise("white(D-1)", lambda D: 1 <= D <= len(white) and bool(white[D - 1]),
                   backing="hypothesis of the doubling law ldiag_doubles")
    r = explained_away_guard("'TAX is conserved at every period doubling' (v13 POSITIVE FINDING)",
                             jumps, lambda D: not defect_at.get(D, False), [prem], dom,
                             implication={"white(D-1)": LEAN["at_doubling"]})
    results.append(r)
    # the same coincidence, judged by an exact test only (what a statistics-only engine would say)
    hit = sum(1 for J in jumps if not defect_at.get(J, False))
    r2 = coincidence_test(len(dom), len(conserved), len(jumps), hit)
    r2.sentence = ("statistics alone: " + r2.sentence +
                   " A statistics-only engine would call this significant; the explained-away "
                   "guard shows it is forced by white(D-1).")
    results.append(r2)

    # 3. "TAX is conserved ONLY at the white diagonals"
    near_white = [D for D in dom if white[D] or white[D - 1]]
    r = exclusivity_guard("'TAX is CONSERVED only at the white diagonals' (v13 cross-domain lift)",
                          conserved, near_white)
    r.data["lean"] = LEAN["not_only_white"]
    results.append(r)

    # 4. summaries that outlive the evidence
    statuses = {h.hid: h.status for h in eng.hyps}
    h38 = [h for h in eng.hyps if h.key == "TAX.defect.contains.jumps"]
    claims = {}
    if h38:
        claims[h38[0].hid] = [r"TAX (conservation )?breakdown is NECESSARY",
                              r"TAX defect is NECESSARY", r"jumps share bits \(necessary"]
    texts = [u["text"] if isinstance(u, dict) else str(u) for u in utterances]
    texts += [h.text for h in eng.hyps]
    for h in eng.hyps:
        texts += [e.get("detail", "") for e in h.evidence]
    r = consistency_guard(statuses, claims, texts)
    results.append(r)

    if mutate:
        for h in eng.hyps:
            if h.key == "TAX.conserved.at.jumps" and not results[2].ok:
                h.record("guard: explained-away", True, results[2].sentence)
                h.novelty = "consequence of a known law (white(D-1)); not a new mechanism"
            if h.key == "TAX.substrate.model.qualified" and not results[4].ok:
                h.status = "refuted-by-guard"
                h.record("guard: exclusivity", False, results[4].sentence)
            if h.key in ("TAX.mechanism.cluster", "TAX.substrate.model") and not results[5].ok:
                h.record("guard: consistency", False,
                         "this text cites 'TAX breakdown is NECESSARY for a jump', which the engine "
                         "itself refuted (every jump has defect 0).")
    return results


def corrected_sentences(results: list) -> list:
    """Plain sentences that replace v13's fixed TAX conclusions."""
    out = []
    for r in results:
        out.append(("OK   " if r.ok else "FLAG ") + r.sentence)
    out.append("Corrected conclusion: TAX conservation is the same as 3c^2 - 2c(a+b) + ab = 0 "
               "for the weights a, b and overlap c (any Y). It holds whenever one pattern is white, "
               "so it holds at every period doubling (white(D-1)); it also holds at many pairs with "
               "no white member. TAX defects therefore neither mark nor explain the doublings; the "
               "doubling law white(D-1) and odd(D-2) remains the explanation.")
    return out
