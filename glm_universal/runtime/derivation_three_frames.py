"""``glm_universal.runtime.derivation_three_frames`` -- Phase 118's readings
(``studies/DERIVATION_THREE_STUDY.md``).

Three of Phase 107's operations (:mod:`.derivation_two_frames`) stop where
that round's study §6 drew the line; this module carries each of them past
it, and :mod:`.derivation_two_frames` hands over at exactly that point:

* ``prove information inequality`` -- where the Shannon-type search ends in
  ``NOT_SHANNON``, :func:`beyond_reading` tries a certificate over the
  elemental and Zhang-Yeung inequalities, each instance derived from one
  copy, and then an exact counterexample from a pool of rational laws
  (:mod:`glm_universal.reasoning.non_shannon`);
* ``derive rate distortion function`` -- where the Shannon lower bound stops
  being tight (Phase 107's ``NOT_TIGHT`` gap), :func:`rd_full_reading`
  derives the function on the rest of the range, with a rational test
  channel and a rational dual point that meet
  (:mod:`glm_universal.reasoning.hamming_rd`);
* ``solve eigenvalue problem`` -- where a Robin condition made Phase 107
  refuse ``TRANSCENDENTAL``, :func:`robin_reading` gives the
  characteristic equation, one root per declared interval, the negative
  eigenvalue when there is one, and certified enclosures on a numeric
  interval (:mod:`glm_universal.reasoning.robin`).

``ENABLED[0] = False`` restores Phase 107's readings exactly.  Each reading
is gated by its column-3 script
(:mod:`glm_universal.runtime.derivation_three_scripts`); ``mutate`` alters
the claim so that the same script must reject it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence

from ..reasoning import hamming_rd as HR
from ..reasoning import info_inequality as II
from ..reasoning import non_shannon as NS
from ..reasoning import robin as RB
from . import derivation_three_scripts as S3
from .question_frames import Reading

__all__ = ["ENABLED", "beyond_reading", "rd_full_reading", "robin_reading",
           "LEAN_FILE_NAME"]

#: The switch: ``False`` restores Phase 107's readings.
ENABLED = [True]

LEAN_FILE_NAME = "RequestProject/GLM/NonShannon.lean"

_ZY_WORDS = ("ZY(a,b;c,d) is the Zhang-Yeung inequality I(a;b) + I(a;c,d) + "
             "3*I(c;d|a) + I(c;d|b) - 2*I(c;d) >= 0")


# ===========================================================================
# 1.  PAST THE SHANNON CONE
# ===========================================================================

def beyond_script_for(pr: II.Problem, b: NS.Beyond, claim: str,
                      claimed=None) -> str:
    if b.kind == "proved_non_shannon":
        zys = []
        for inst in b.instances():
            lam5, mu5 = NS.zy_copy_certificate(*inst)
            zys.append((inst, lam5, mu5))
        return S3.beyond_script(pr.names, pr.given_texts, claim, b.kind,
                                b.certificates, zys)
    return S3.beyond_script(pr.names, pr.given_texts, claim, b.kind,
                            law=b.law, violated=b.violated,
                            claimed_value=claimed if claimed is not None
                            else b.violation)


def beyond_reading(pr: II.Problem, v: II.Verdict, frame: str, col1: str,
                   mutate: bool = False) -> Optional[Reading]:
    """The reading past the Shannon cone, or ``None`` when the claim stays
    ``NOT_SHANNON`` (Phase 107's reading then stands, with the note of
    :func:`undecided_note`)."""
    if not ENABLED[0]:
        return None
    b = NS.decide_beyond(pr, v)
    backing = ("reasoning.non_shannon (Zhang-Yeung by one copy; exact "
               "entropies of rational laws)")
    givens = f" given {', '.join(pr.given_texts)}" if pr.givens else ""
    if b.kind == "proved_non_shannon":
        claim = pr.claim_text
        if mutate:
            first = pr.names[0]
            claim = claim + f" + H({first})" if pr.op != "<=" else \
                f"H({first}) + " + claim
        script = beyond_script_for(pr, b, claim)
        derivs = "; ".join(NS.zy_certificate_text(*i) for i in b.instances())
        insts = ", ".join("(" + ",".join(i[:2]) + ";" + ",".join(i[2:]) + ")"
                          for i in b.instances())
        value = (f"{pr.claim_text} holds{givens}: " + "; ".join(b.lines()) +
                 f"; every elemental term is >= 0 and {_ZY_WORDS}, which "
                 f"has no Shannon-type proof (a polymatroid violates it) and "
                 f"holds for every distribution: with R a copy of c over "
                 f"(a, d) -- the same joint law with every subset of {{a, d}}"
                 f", and I(R; b, c | a, d) = 0 -- it is a Shannon-type "
                 f"identity over five variables ({derivs}). The copy lemma "
                 f"(such an R exists for every law of four variables: "
                 f"p(a,b,c,d)*p(r|a,d)) is the one step used here without "
                 f"being re-derived")
        col2 = (f"no Shannon-type certificate (Phase 107's search: "
                f"NOT_SHANNON); exact linear programming over the elemental "
                f"inequalities of {', '.join(pr.names)} and the twelve "
                f"Zhang-Yeung instances finds one using {insts}; each "
                f"instance's five-variable certificate found once by the same "
                f"simplex and relabelled (GLM.NonShannon.zhang_yeung_of_copy)")
        return Reading(frame, True, value, col1, col2, script,
                       backing=backing)
    if b.kind == "NOT_VALID_ENTROPIC":
        claimed = dict(b.violation)
        if mutate:
            claimed[2] = claimed.get(2, Fraction(0)) + 1
        script = beyond_script_for(pr, b, pr.claim_text, claimed)
        gap = {p: -e for p, e in b.violation.items()}
        value = (f"{pr.claim_text} does not follow" +
                 (f" from {', '.join(pr.given_texts)}" if pr.givens else "") +
                 f": the law {NS.law_text(b.law, pr.names)} -- not a law of "
                 f"linear functions of fair bits -- meets every given and "
                 f"violates the claim by {NS.lf_text(gap)} bits, which is "
                 f"> 0 (decided exactly by comparing two integers)")
        col2 = (f"no Shannon-type certificate and no counterexample of linear "
                f"functions of fair bits (Phase 107: NOT_SHANNON); no "
                f"certificate over the Zhang-Yeung instances either; law "
                f"{b.searched} of the search pool, screened in integer fixed point "
                f"and decided in exact sums of logarithms of primes")
        return Reading(frame, False, value, col1, col2, script,
                       code="NOT_VALID", backing=backing)
    return None


def undecided_note(pr: II.Problem) -> str:
    if not ENABLED[0]:
        return ""
    return (f"; past the Shannon cone the claim has no certificate over the "
            f"Zhang-Yeung instances either, and none of the "
            f"{len(NS.law_pool(len(pr.names)))} rational laws of the search "
            f"pool violates it")


# ===========================================================================
# 2.  RATE DISTORTION PAST THE TIGHT RANGE
# ===========================================================================

def rd_full_reading(source: str, frame: str, col1: str,
                    mutate: bool = False) -> Optional[Reading]:
    """The whole-range reading for a source whose Shannon lower bound stops
    short of ``D_max``; ``None`` if the switch is off or the source is not
    of that kind."""
    if not ENABLED[0]:
        return None
    try:
        r = HR.hamming_rd(source)
    except Exception:
        return None
    if r.slb_end >= r.d_max:
        return None
    script = S3.rd_full_script(r.probs, [(p.lo, p.hi, p.k) for p in r.pieces],
                               mutate=mutate)
    parts = []
    for p in r.pieces:
        parts.append(f"R(D) = {p.formula} for {p.lo} <= D <= {p.hi} "
                     f"(reproducing the {p.k} most likely letters)")
    value = ("; ".join(parts) + f"; R(D) = 0 for D >= {r.d_max} (bits). "
             f"Past D = {r.slb_end} the Shannon lower bound is not met "
             f"(NOT_TIGHT for the bound), and the function there is the "
             f"piece that reproduces fewer letters")
    col2 = ("on each piece, with T = D - (1 - P_k), lambda = 1 - D and "
            "beta = T/((k - 1)*(1 - D)): the test channel q(j) = (p_j/lambda "
            "- beta)/(1 - beta) on the top k letters, P(x, j) = "
            "lambda*q(j)*beta^[x != j] for x among them and p_x*q(j) off "
            "them, has the source marginal, distortion exactly D and "
            "I(X;Xh) = R(D); the dual point mu(x) = lambda/p_x on the top k, "
            "1/beta off them, meets sum_x p_x*mu(x)*beta^d(x,y) <= 1 for "
            "every y (= 1 on the top k; off them because p_y <= T/(k - 1)), "
            "so by the dual bound (GLM.NonShannon.rd_dual_lower_bound) no "
            "channel with distortion <= D has a smaller rate -- and the two "
            "values are the same sum of logarithms")
    return Reading(frame, True, value, col1, col2, script,
                   backing="reasoning.hamming_rd (Erokhin's pieces, a "
                           "rational test channel and dual point)")


# ===========================================================================
# 3.  ROBIN EIGENVALUES
# ===========================================================================

def robin_reading(parts: Sequence[str], frame: str, col1: str,
                  mutate: bool = False) -> Optional[Reading]:
    """The Robin reading, or a refusal with the Robin layer's own code; or
    ``None`` when the switch is off."""
    if not ENABLED[0]:
        return None
    backing = "reasoning.robin (sign analysis; certified enclosures)"
    try:
        r = RB.robin_problem(parts[0], parts[1:])
    except RB.RobinError as e:
        if e.code in ("TRANSCENDENTAL", "UNSUPPORTED"):   # Phase 119
            from . import derivation_four_frames as D4
            two = D4.robin_reading(parts, frame, col1, mutate)
            if two is not None:
                return two
        return Reading(frame, False, e.why, col1, f"refused {e.code}",
                       f"print('REFUSED {e.code} VERIFIED True')\n",
                       code=e.code, backing=backing)
    mults = [RB.interval_mults(r.case, n) for n in (1, 2, 3)]
    lams = [RB.decimal_text(a, b) for a, b in r.eigenvalues()]
    neg = (RB.decimal_text(*r.negative_value) if r.negative_value else None)
    shown_mults, shown_lams = list(mults), list(lams)
    if mutate:
        if shown_lams:
            shown_lams[0] = "1" + shown_lams[0]
        else:
            shown_mults = [(a + Fraction(1, 2), b + Fraction(1, 2))
                           for a, b in mults]
    script = S3.robin_script(r.family, r.h, r.L, shown_mults, r.roots,
                             shown_lams, r.negative_mu, neg, r.case)
    value = (f"lambda_n = k_n^2, where k_n is the root of {r.equation} in "
             f"{r.interval}; {r.y} = {r.eigenfunction}")
    if r.zero_eigen:
        value += f"; also lambda = 0 with {r.y} = {r.x}"
    if r.negative is not None:
        value += f"; also {r.negative}"
        if neg is not None:
            value += f" (lambda = {neg})"
    if not r.zero_eigen and r.negative is None:
        value += "; no eigenvalue <= 0"
    if lams:
        value += ("; on this interval lambda_1 = " + lams[0] +
                  ", lambda_2 = " + lams[1] + ", lambda_3 = " + lams[2] +
                  " (each between two rationals where the characteristic "
                  "function has opposite certified signs)")
    fn = "sin" if r.family == "D" else "cos"
    col2 = (r.sign_text + f". Normalised by int_0^{r.length} {fn}^2(k_n*x) dx"
            f" = {r.length}/2 {'-' if fn == 'sin' else '+'} "
            f"sin(2*k_n*{r.length})/(4*k_n). The eigenvalues have no closed "
            f"form; GLM.NonShannon.robin_root_exists proves the root in each "
            f"interval for a Dirichlet end and h > 0, and robin_eigenfunction "
            f"that sin(k_n*x) then solves the problem")
    from . import derivation_four_frames as D4
    extra = D4.bounds_addition(r, mutate)
    if extra is not None:                      # Phase 119, closed-form bounds
        value += extra[0]
        script += "\n" + extra[1]
    return Reading(frame, True, value, col1, col2, script, backing=backing)
