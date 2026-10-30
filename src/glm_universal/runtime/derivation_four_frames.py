"""``glm_universal.runtime.derivation_four_frames`` -- Phase 119's readings
(``studies/DERIVATION_FOUR_STUDY.md``).

Phase 118 (:mod:`.derivation_three_frames`) left four lines, and the earlier
frames hand over to this module at exactly those points:

* ``prove information inequality`` -- a four-variable claim that stays
  ``NOT_SHANNON`` past the Zhang-Yeung instances and the pool of laws goes to
  :func:`chain_reading` (chained copies,
  :mod:`glm_universal.reasoning.copy_chain`); a claim on five variables,
  refused ``TOO_MANY_VARIABLES`` before, goes to :func:`five_reading`;
* ``derive rate distortion function`` -- a distortion matrix, refused
  ``UNSUPPORTED`` before, goes to :func:`rd_reading`
  (:mod:`glm_universal.reasoning.general_rd`);
* ``solve eigenvalue problem`` -- Robin conditions at both ends, a symbolic
  coefficient, a negative coefficient on a symbolic interval
  (``TRANSCENDENTAL`` / ``UNSUPPORTED`` from Phase 118's layer) go to
  :func:`robin_reading` (:mod:`glm_universal.reasoning.robin_two`); and a
  Dirichlet end with ``h > 0`` on a symbolic interval gains the closed-form
  bounds of :func:`bounds_addition`.

``ENABLED[0] = False`` restores Phase 118's readings exactly.  Every reading
is gated by its column-3 script (:mod:`.derivation_four_scripts`); ``mutate``
alters the claim so that the same script must reject it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from ..reasoning import copy_chain as CC
from ..reasoning import general_rd as GR
from ..reasoning import info_inequality as II
from ..reasoning import non_shannon as NS
from ..reasoning import robin as RB
from ..reasoning import robin_two as R2
from . import derivation_four_scripts as S4
from . import derivation_three_scripts as S3
from . import derivation_two_scripts as DS
from .question_frames import Reading

__all__ = ["ENABLED", "chain_reading", "five_reading", "rd_reading",
           "robin_reading", "bounds_addition", "LEAN_FILES", "case_samples"]

#: The switch: ``False`` restores Phase 118's readings.
ENABLED = [True]

LEAN_FILES = ("RequestProject/GLM/CopyLemma.lean",
              "RequestProject/GLM/RobinBoth.lean")


def _refusal(frame: str, code: str, why: str, col1: str, backing: str
             ) -> Reading:
    return Reading(frame, False, why, col1, f"refused {code}",
                   f"print('REFUSED {code} VERIFIED True')\n", code=code,
                   backing=backing)


def _mutated_claim(pr: II.Problem) -> str:
    first = pr.names[0]
    return (pr.claim_text + f" + H({first})" if pr.op != "<=" else
            f"H({first}) + " + pr.claim_text)


# ===========================================================================
# 1.  CHAINS OF COPIES
# ===========================================================================

def _chain_line(pr: II.Problem, k: int, ch: CC.Chain) -> str:
    terms = [(c, II.elemental_text(e, ch.names)) for e, c in ch.lam]
    terms += [(c, "[" + II._given_lhs(pr.given_texts[j]) + "]")
              for j, c in ch.mu]
    terms += [(c, "[" + ch.conditions[j][0].split(" = ")[0] + " - " +
               ch.conditions[j][0].split(" = ")[1] + "]"
               if not ch.conditions[j][0].endswith("= 0") else
               "[" + ch.conditions[j][0][:-4] + "]") for j, c in ch.nu]
    return f"{II._claim_side(pr, k)} = " + II._signed(terms)


def chain_report(pr: II.Problem, chains: List[CC.Chain], mutate: bool
                 ) -> Tuple[str, str, str]:
    """``(value, column 2, script)`` of a ``proved_by_copies`` reading."""
    claim = _mutated_claim(pr) if mutate else pr.claim_text
    data = [([(s.name, s.of, s.base) for s in ch.steps], ch.lam, ch.mu, ch.nu)
            for ch in chains]
    script = S4.chain_script(pr.names, pr.given_texts, claim, data)
    givens = f" given {', '.join(pr.given_texts)}" if pr.givens else ""
    steps = "; ".join(ch.text() for ch in chains)
    lines = "; ".join(_chain_line(pr, k, ch) for k, ch in enumerate(chains))
    value = (f"{pr.claim_text} holds{givens}: with {steps} -- each a copy "
             f"by the copy lemma (the same joint law with every subset of its "
             f"base, and conditionally independent of everything else given "
             f"the base) -- {lines}, where every elemental term is >= 0 and "
             f"every bracketed copy condition is 0. The copy lemma is proved "
             f"for every finite distribution (GLM.CopyLemma.copy_lemma), so "
             f"nothing in the derivation is assumed")
    col2 = (f"no Shannon-type certificate (NOT_SHANNON), none over the "
            f"twelve Zhang-Yeung instances, and no counterexample in the pool "
            f"of rational laws (Phase 118); exact linear programming over the "
            f"elemental inequalities of {', '.join(chains[0].names)} with the "
            f"copy conditions as equalities finds the certificate "
            f"(single copies tried first, then two copies of the same "
            f"variable over the same base, the second also over the first)")
    return value, col2, script


def chain_reading(pr: II.Problem, v: II.Verdict, frame: str, col1: str,
                  mutate: bool = False) -> Optional[Reading]:
    """The reading by chained copies, or ``None`` (Phase 118's reading then
    stands)."""
    if not ENABLED[0]:
        return None
    chains = CC.decide_chain(pr)
    if chains is None:
        return None
    value, col2, script = chain_report(pr, chains, mutate)
    return Reading(frame, True, value, col1, col2, script,
                   backing="reasoning.copy_chain (chained copies, exact "
                           "simplex)")


# ===========================================================================
# 2.  FIVE VARIABLES
# ===========================================================================

def five_reading(text: str, frame: str, col1: str, mutate: bool = False
                 ) -> Optional[Reading]:
    """The five-variable reading; a refusal for six or more; ``None`` when
    the switch is off."""
    if not ENABLED[0]:
        return None
    backing = ("reasoning.copy_chain (exact simplex on five variables, "
               "Zhang-Yeung on every four, lifted rational laws)")
    try:
        pr = CC.parse_five(text)
    except II.InequalityError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing)
    f = CC.decide_five(pr)
    v = f.shannon
    col1 = col1 or (f"does {pr.claim_text} follow from "
                    f"{', '.join(pr.given_texts) or 'the Shannon inequalities'}"
                    f" alone?")
    claim = _mutated_claim(pr) if mutate else pr.claim_text
    givens = f" given {', '.join(pr.given_texts)}" if pr.givens else ""
    if f.kind == "proved":
        script = DS.inequality_script(pr.names, pr.given_texts, claim,
                                      "proved", v.certificates,
                                      label="INEQUALITY-5")
        return Reading(
            frame, True, f"{pr.claim_text} holds{givens}: " +
            "; ".join(v.lines()) + ", and every term on the right is an "
            "elemental Shannon inequality (>= 0)", col1,
            "Shannon-type certificate found by exact linear programming over "
            "the elemental inequalities of " + ", ".join(pr.names) +
            " (Phase 107's search, now read on five variables)", script,
            backing=backing)
    if f.kind == "NOT_VALID":
        h = v.entropies
        claimed = II._value(pr.claims[v.violated], h)
        if mutate:
            claimed += 1
        script = DS.inequality_script(pr.names, pr.given_texts,
                                      pr.claim_text, "NOT_VALID", [],
                                      v.distribution, v.violated, claimed,
                                      label="COUNTEREXAMPLE-5")
        bits, forms = v.distribution
        return Reading(
            frame, False,
            f"{pr.claim_text} does not follow" +
            (f" from {', '.join(pr.given_texts)}" if pr.givens else "") +
            f": with {II.show_linear(forms, pr.names, bits)} every given "
            f"holds and the claim fails by "
            f"{-II._value(pr.claims[v.violated], h)} bit(s)", col1,
            "a distribution of linear functions of fair bits, found by the "
            "GF(2) search on five variables", script, code="NOT_VALID",
            backing=backing)
    if f.kind == "proved_non_shannon":
        zys = [(inst,) + NS.zy_copy_certificate(*inst)
               for inst in f.instances()]
        script = S4.five_zy_script(pr.names, pr.given_texts, claim,
                                   f.certificates, zys)
        b = NS.Beyond("proved_non_shannon", pr, f.certificates)
        insts = ", ".join("(" + ",".join(i[:2]) + ";" + ",".join(i[2:]) + ")"
                          for i in f.instances())
        return Reading(
            frame, True,
            f"{pr.claim_text} holds{givens}: " + "; ".join(b.lines()) +
            f"; every elemental term is >= 0 and ZY(a,b;c,d) = I(a;b) + "
            f"I(a;c,d) + 3*I(c;d|a) + I(c;d|b) - 2*I(c;d) >= 0 for every "
            f"distribution (Zhang-Yeung, proved for every finite distribution "
            f"in GLM.CopyLemma.zhang_yeung_entropic)", col1,
            f"no Shannon-type certificate on five variables; exact linear "
            f"programming over the elemental inequalities and the 60 "
            f"Zhang-Yeung instances on every four of the five finds one "
            f"using {insts}", script, backing=backing)
    if f.kind == "NOT_VALID_ENTROPIC":
        claimed = dict(f.violation)
        if mutate:
            claimed[2] = claimed.get(2, Fraction(0)) + 1
        script = S3.beyond_script(pr.names, pr.given_texts, pr.claim_text,
                                  "NOT_VALID_ENTROPIC", law=f.law,
                                  violated=f.violated, claimed_value=claimed,
                                  label="ENTROPIC-COUNTEREXAMPLE-5")
        gap = {p: -e for p, e in f.violation.items()}
        z, w = f.lifting
        how = (f"{z} constant" if w is None else f"{z} equal to {w}")
        return Reading(
            frame, False,
            f"{pr.claim_text} does not follow" +
            (f" from {', '.join(pr.given_texts)}" if pr.givens else "") +
            f": the law {NS.law_text(f.law, pr.names)} meets every given and "
            f"violates the claim by {NS.lf_text(gap)} bits, which is > 0 "
            f"(decided exactly by comparing two integers)", col1,
            f"no Shannon-type certificate and no GF(2) counterexample on five "
            f"variables, no certificate over the Zhang-Yeung instances; a "
            f"rational law of four variables lifted with {how}", script,
            code="NOT_VALID", backing=backing)
    pm = v.polymatroid
    claimed = II._value(pr.claims[v.violated], pm)
    if mutate:
        claimed += 1
    script = DS.inequality_script(pr.names, pr.given_texts, pr.claim_text,
                                  "NOT_SHANNON", [], None, v.violated,
                                  claimed, pm)
    return Reading(
        frame, False,
        f"{pr.claim_text} is undecided here: it has no Shannon-type proof (a "
        f"polymatroid on five variables violates it), no certificate over the "
        f"Zhang-Yeung instances on every four, and none of the "
        f"{f.searched} lifted rational laws violates it", col1,
        "exact linear programming: infeasible; Farkas witness given", script,
        code="NOT_SHANNON", backing=backing)


# ===========================================================================
# 3.  RATE DISTORTION, ANY DISTORTION MATRIX
# ===========================================================================

def rd_reading(text: str, frame: str, col1: str, mutate: bool = False
               ) -> Optional[Reading]:
    """The reading for a distortion matrix; ``None`` when the switch is off
    or the text gives no matrix (Phase 107's refusal then stands)."""
    if not ENABLED[0] or "[[" not in text:
        return None
    backing = ("reasoning.general_rd (rigorous enclosures: a channel within "
               "the distortion, a dual point)")
    try:
        p, d, at = GR.parse_rd(text)
        g = GR.general_rd(p, d, at)
    except GR.RDError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing)
    texts = []
    for e in g.points:
        dec = e.decimal()
        if dec is None:                              # pragma: no cover
            return _refusal(frame, "NO_ENCLOSURE", f"R({e.D}) sits on a "
                            f"rounding boundary at six decimals",
                            col1 or text, backing)
        texts.append(dec)
    shown = list(texts)
    if mutate and shown:
        shown[0] = "1" + shown[0]
    script = S4.rd_script(g.probs, g.d, g.d_min, g.d_max,
                          [(e.D, e.channel, e.t, e.q, s)
                           for e, s in zip(g.points, shown)])
    vals = ", ".join(f"R({e.D}) = {s}" for e, s in zip(g.points, texts))
    value = (f"D_min = {g.d_min}, D_max = {g.d_max}; R(D) is not defined "
             f"below D_min, R(D) = 0 for D >= {g.d_max} (the constant "
             f"reproduction of letter {g.y_star}); "
             + (f"{vals} (bits, each to six decimals between two rigorous "
                f"bounds)" if g.points else "nothing lies between them"))
    col2 = ("upper bound: a channel Q(y|x) of expected distortion <= D "
            "(checked exactly) has I(X;Xh) >= R(D); the channel is the "
            "Blahut-Arimoto channel q(y) t^d(x,y)/Z(x) at two rational "
            "slopes, time-shared to distortion D. Lower bound: for weights "
            "mu(x) with sum_x p(x) mu(x) t^d(x,y) <= 1 for every y (checked "
            "exactly), every channel of distortion <= D has I >= "
            "sum_x p(x) log2 mu(x) + D log2 t (GLM.NonShannon."
            "rd_dual_lower_bound); logarithms bracketed in integer fixed "
            "point. D_min = sum_x p(x) min_y d(x,y), D_max = min_y "
            "sum_x p(x) d(x,y)")
    return Reading(frame, True, value, col1 or text, col2, script,
                   backing=backing)


# ===========================================================================
# 4.  ROBIN
# ===========================================================================

def case_samples(r: R2.RobinTwo, case: R2.RobinCase
                 ) -> List[Tuple[Fraction, Fraction]]:
    """Sample ``(h, L)`` points inside a case's class."""
    Ls = [r.L] if r.L is not None else [Fraction(1, 2), Fraction(1),
                                        Fraction(3)]
    if r.h is not None:                        # negative h, symbolic L
        c = -1 / r.h
        Lc = {"D-weak": [c / 2, c / 3], "D-0": [c],
              "D-neg": [2 * c, 3 * c]}[case.case]
        return [(r.h, L) for L in Lc]
    out = []
    for L in Ls:
        hs = {"D+": [Fraction(1), Fraction(3)], "D0": [Fraction(0)],
              "D-weak": [-1 / (2 * L)], "D-0": [-1 / L],
              "D-neg": [-2 / L, -3 / L], "N+": [Fraction(1), Fraction(3)],
              "N0": [Fraction(0)], "N-": [Fraction(-1), Fraction(-3)]
              }[case.case]
        out += [(h, L) for h in hs]
    return out


def case_mults(case: str) -> List[Tuple[Fraction, Fraction]]:
    if case == "D0":
        return [(Fraction(2 * n - 1, 2),) * 2 for n in (1, 2, 3)]
    if case == "N0":
        return [(Fraction(n - 1),) * 2 for n in (2, 3, 4)]
    return [RB.interval_mults(case, n) for n in (1, 2, 3)]


def _extra(r: R2.RobinTwo, c: R2.RobinCase) -> str:
    L = r.length
    if c.nonpositive == "zero":
        return (f", and lambda = 0 with {r.y} = {r.x}" if r.family == "D"
                else f", and lambda = 0 with {r.y} = 1")
    if c.nonpositive == "negative":
        if r.family == "D":
            rhs = "-mu/h" if r.h is None else RB._coef_k(-1 / r.h).replace(
                "k", "mu")
            return (f", and one negative eigenvalue lambda = -mu^2 with "
                    f"tanh(mu*{L}) = {rhs} ({r.y} = sinh(mu*{r.x}))")
        return (f", and one negative eigenvalue lambda = -mu^2 with "
                f"mu*tanh(mu*{L}) = -h ({r.y} = cosh(mu*{r.x}))")
    return ", and no eigenvalue <= 0"


def robin_reading(parts: Sequence[str], frame: str, col1: str,
                  mutate: bool = False) -> Optional[Reading]:
    """The Phase 119 Robin reading or a refusal with its own code; ``None``
    when the switch is off."""
    if not ENABLED[0]:
        return None
    backing = "reasoning.robin_two (sign analysis by cases; enclosures)"
    try:
        r = R2.robin_two(parts[0], parts[1:])
    except RB.RobinError as e:
        return _refusal(frame, e.code, e.why, col1, backing)
    if r.kind == "both":
        lams = [RB.decimal_text(a, b) for a, b in r.eigenvalues()]
        shown, shift = list(lams), Fraction(0)
        if mutate:
            if shown:
                shown[0] = "1" + shown[0]
            else:
                shift = Fraction(1, 2)
        script = S4.robin_both_script(r.a, r.b, r.L, r.roots, shown,
                                      r.equation, shift)
        value = (f"lambda_n = k_n^2, where k_n is the root of {r.equation} "
                 f"in {r.interval}; {r.y} = {r.eigenfunction}; no eigenvalue "
                 f"<= 0")
        if lams:
            value += (f"; on this interval lambda_1 = {lams[0]}, lambda_2 = "
                      f"{lams[1]}, lambda_3 = {lams[2]} (each between two "
                      f"rationals where the characteristic function has "
                      f"opposite certified signs)")
        col2 = (r.sign_text + ". GLM.RobinBoth.robin_both_root_exists proves "
                "a root in each interval for a, b, L > 0 and "
                "robin_both_eigenfunction that k*cos(k*x) + a*sin(k*x) then "
                "meets both conditions")
        return Reading(frame, True, value, col1, col2, script,
                       backing=backing)
    cases = [(case_samples(r, c), case_mults(c.case),
              c.nonpositive) for c in r.cases]
    if mutate:
        s, m, np_ = cases[0]
        cases[0] = (s, m, "negative" if np_ != "negative" else "none")
    script = S4.robin_cases_script(r.family, cases)
    pieces = []
    for c in r.cases:
        where = c.interval if c.interval.startswith("k_n =") else \
            f"k_n in {c.interval}"
        pieces.append(f"if {c.condition}: {where}{_extra(r, c)}")
    value = (f"lambda_n = k_n^2 with k_n the roots of {r.equation}, "
             f"{r.y} = {r.eigenfunction}, by cases: " + "; ".join(pieces))
    col2 = (r.sign_text + ". The case split is exhaustive; inside each case "
            "the shape of the spectrum does not change, and the sign "
            "analysis is Phase 118's (GLM.NonShannon.robin_root_exists for "
            "h > 0)")
    return Reading(frame, True, value, col1, col2, script, backing=backing)


def bounds_addition(r: "RB.Robin", mutate: bool = False
                    ) -> Optional[Tuple[str, str]]:
    """For a Dirichlet end, ``h > 0`` and a symbolic interval: ``(text to
    append, script)``; ``None`` otherwise or when the switch is off."""
    if not ENABLED[0]:
        return None
    b = R2.bounds_for(r)
    if b is None:
        return None
    lo, hi = b
    text = (f"; and {lo} < k_n*{r.length} < {hi} (k_n*{r.length} - (n - "
            f"1/2)*pi = arctan({r.h}*{r.length}/(k_n*{r.length})), "
            f"GLM.RobinBoth.robin_root_arctan and robin_root_bounds)")
    shown = (hi, lo) if mutate else (lo, hi)
    return text, S4.robin_bounds_script(r.h, *shown)
