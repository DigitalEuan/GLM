"""``glm_universal.runtime.derivation_two_frames`` -- the rest of track P as
question frames (Phase 107, ``studies/DERIVATION_TWO_STUDY.md``).

Eight operations, each read from one line of text and gated by its
column-3 script (:mod:`glm_universal.runtime.derivation_two_scripts`):

* ``prove information inequality: GIVENS |- CLAIM`` --
  :mod:`glm_universal.reasoning.info_inequality`;
* ``decide unique decodability: W1, W2, ...`` and ``construct prefix code
  with lengths L1, L2, ... [over D symbols]``, ``derive rate distortion
  function for SOURCE source with hamming distortion`` and ``derive rate
  posterior for k = K errors in n = N bits [on the machine's grid]`` --
  :mod:`glm_universal.reasoning.coding_theory`;
* ``derive maximum entropy density on SUPPORT [with CONSTRAINTS]`` --
  :mod:`glm_universal.reasoning.maxent`;
* ``solve eigenvalue problem for Y(X): d2(Y)/dX2 + lambda*Y = 0; BC; BC``
  and ``derive transmission coefficient for V(x) = ...[, E > V0]`` --
  :mod:`glm_universal.reasoning.spectral`;
* ``derive decimation-in-frequency fft for N = ...`` (or ``-time``) --
  :mod:`glm_universal.reasoning.fft_derivation`.

And eleven **outside frames** for the class-P questions of the outside set
that Phase 106 left: each recognises the situation, writes the problem in
the operation's terms -- the ring's Hamiltonian as ``psi'' + (2 I E /
hbar^2) psi = 0`` with periodic conditions, the delta barrier as a
potential at one point, the Markov chain as the given ``I(X;Z|Y) = 0`` --
and hands it to the operation.  Three of them (Kraft-McMillan, compactness,
Tarski) rest on a theorem of ``RequestProject/GLM/DerivationsTwo.lean``:
what the machine computes there is named as such (a worked code and its
counting bound; the propositional core, proved by the G4ip prover of Phase
106), and the theorem is cited as what carries the general statement.
Where a question also asks for an account (*explain the physical
significance*), the computed part is answered and the rest is named as the
refusal ``EXPLANATION`` inside the reading.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning import coding_theory as CT
from ..reasoning import fft_derivation as FD
from ..reasoning import info_inequality as II
from ..reasoning import maxent as ME
from ..reasoning import spectral as SP
from ..reasoning import symbolic as S
from . import derivation_three_frames as D3
from . import derivation_four_frames as D4
from . import derivation_two_scripts as DS
from .question_frames import Frame, Reading

__all__ = ["PREFIXES", "match_raw", "read_operation", "OPERATION_FRAME",
           "OUTSIDE_P2_FRAMES", "MUTATE", "mutated_operation",
           "mutated_outside", "LEAN_FILE_NAME"]

INEQ = "prove information inequality:"
UD = "decide unique decodability:"
PREFIX = "construct prefix code with lengths "
RD = "derive rate distortion function for "
MAXENT = "derive maximum entropy density on "
EIGEN = "solve eigenvalue problem for "
SCATTER = "derive transmission coefficient for "
FFT_DIF = "derive decimation-in-frequency fft for "
FFT_DIT = "derive decimation-in-time fft for "
POSTERIOR = "derive rate posterior for "
PREFIXES = (INEQ, UD, PREFIX, RD, MAXENT, EIGEN, SCATTER, FFT_DIF, FFT_DIT,
            POSTERIOR)

LEAN_FILE_NAME = "RequestProject/GLM/DerivationsTwo.lean"

#: Set by the mutated readings: every claim is altered (the column-3
#: control: its script must reject it).
MUTATE = [False]


def _refusal(frame: str, code: str, why: str, col1: str,
             script: Optional[str] = None, backing: str = "") -> Reading:
    return Reading(frame, False, why, col1, f"refused {code}",
                   script or f"print('REFUSED {code} VERIFIED True')\n",
                   code=code, backing=backing or "reasoning (Phase 107)")


# ===========================================================================
# 1.  INFORMATION INEQUALITIES
# ===========================================================================

def inequality_reading(text: str, frame: str = "information_inequality",
                       col1: str = "") -> Reading:
    backing = "reasoning.info_inequality (exact simplex, GF(2) distributions)"
    try:
        pr = II.parse_problem(text)
    except II.InequalityError as e:
        if e.code == "TOO_MANY_VARIABLES":     # Phase 119, five variables
            five = D4.five_reading(text, frame, col1 or text, MUTATE[0])
            if five is not None:
                return five
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    v = II.decide(pr)
    col1 = col1 or (f"does {pr.claim_text} follow from "
                    f"{', '.join(pr.given_texts) or 'the Shannon inequalities'}"
                    f" alone?")
    claim = pr.claim_text
    if MUTATE[0]:
        first = pr.names[0]
        claim = claim + f" + H({first})" if pr.op != "<=" else \
            f"H({first}) + " + claim
    if v.kind == "proved":
        lines = v.lines()
        script = DS.inequality_script(pr.names, pr.given_texts, claim,
                                      "proved", v.certificates,
                                      label="INEQUALITY")
        eq_terms = sorted({II.elemental_text(e, pr.names)
                           for lam, _ in v.certificates for e, _ in lam})
        equality = ("; equality holds exactly when " +
                    " = ".join(eq_terms) + " = 0" if eq_terms and pr.op != "="
                    else "")
        given_note = (" ([...] marks a given, equal to 0)"
                      if pr.givens else "")
        return Reading(
            frame, True,
            f"{pr.claim_text} holds" +
            (f" given {', '.join(pr.given_texts)}" if pr.givens else "") +
            ": " + "; ".join(lines) + given_note + ", and every term on the "
            "right is an elemental Shannon inequality (>= 0)" + equality,
            col1,
            "Shannon-type certificate found by exact linear programming over "
            "the elemental inequalities of " + ", ".join(pr.names) + ": " +
            "; ".join(lines), script, backing=backing)
    if v.kind == "NOT_VALID":
        bits, forms = v.distribution
        h = v.entropies
        claimed = II._value(pr.claims[v.violated], h)
        if MUTATE[0]:
            claimed += 1
        script = DS.inequality_script(pr.names, pr.given_texts,
                                      pr.claim_text, "NOT_VALID", [],
                                      v.distribution, v.violated, claimed,
                                      label="COUNTEREXAMPLE")
        hs = ", ".join(f"H({','.join(sorted(s, key=pr.names.index))}) = "
                       f"{h[s]}" for s in sorted(h, key=lambda s: (len(s),
                       [pr.names.index(x) for x in s])))
        dist = II.show_linear(forms, pr.names, bits)
        comp = (" For three variables and givens of this kind the search "
                "is complete, so no proof exists." if v.complete else "")
        return Reading(
            frame, False,
            f"{pr.claim_text} does not follow" +
            (f" from {', '.join(pr.given_texts)}" if pr.givens else "") +
            f": with {dist} every given holds and the claim fails by "
            f"{-II._value(pr.claims[v.violated], h)} bit(s){comp}",
            col1, f"entropies in bits: {hs}", script, code="NOT_VALID",
            backing=backing)
    beyond = D3.beyond_reading(pr, v, frame, col1, MUTATE[0])
    if beyond is not None:                     # Phase 118, past the cone
        return beyond
    chain = D4.chain_reading(pr, v, frame, col1, MUTATE[0])
    if chain is not None:                      # Phase 119, chained copies
        return chain
    pm = v.polymatroid
    claimed = II._value(pr.claims[v.violated], pm)
    if MUTATE[0]:
        claimed += 1
    script = DS.inequality_script(pr.names, pr.given_texts, pr.claim_text,
                                  "NOT_SHANNON", [], None, v.violated,
                                  claimed, pm)
    pms = ", ".join(f"h({''.join(sorted(s, key=pr.names.index))}) = {c}"
                    for s, c in sorted(pm.items(), key=lambda t: (
                        len(t[0]), [pr.names.index(x) for x in t[0]])))
    return Reading(
        frame, False,
        f"{pr.claim_text} is undecided here: it has no Shannon-type proof "
        f"(the polymatroid {pms} meets every elemental inequality and "
        f"violates it) and no distribution of linear functions of fair bits "
        f"violates it; a non-Shannon inequality or a non-linear distribution "
        f"would be needed to decide it" + D3.undecided_note(pr),
        col1, "exact linear programming: infeasible; Farkas witness given",
        script, code="NOT_SHANNON", backing=backing)


# ===========================================================================
# 2.  CODES
# ===========================================================================

def code_reading(text: str, frame: str = "unique_decodability",
                 col1: str = "") -> Reading:
    backing = "reasoning.coding_theory (Sardinas-Patterson, Kraft)"
    try:
        v = CT.decide_code(text)
    except CT.CodingError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    col1 = col1 or f"is the code {{{', '.join(v.words)}}} uniquely decodable?"
    kraft = v.kraft + (Fraction(1, 64) if MUTATE[0] else 0)
    script = DS.code_script(v.words, v.d, v.unique, v.prefix_free, kraft,
                            v.ambiguous, v.prefix_code)
    layers = "; ".join(f"S{i + 1} = {{{', '.join(L)}}}"
                       for i, L in enumerate(v.layers))
    if not v.unique:
        s, p1, p2 = v.ambiguous
        return Reading(
            frame, False,
            f"not uniquely decodable: {s} = {'.'.join(p1)} = "
            f"{'.'.join(p2)}; Kraft sum {v.kraft}" +
            (" > 1, as McMillan's theorem requires of any code that is not"
             if v.kraft > 1 else ""),
            col1, f"Sardinas-Patterson dangling suffixes: {layers or 'none'}"
                  f"; a codeword dangles", script, code="NOT_UD",
            backing=backing)
    kind = "a prefix code" if v.prefix_free else \
        "uniquely decodable but not prefix-free"
    return Reading(
        frame, True,
        f"uniquely decodable ({kind}); Kraft sum over {v.d} symbols = "
        f"{v.kraft} <= 1; a prefix code with the same lengths: "
        f"{', '.join(v.prefix_code)}",
        col1, f"Sardinas-Patterson dangling suffixes: {layers or 'none'}; no "
              f"codeword dangles. The prefix code is the canonical one "
              f"(Kraft's construction)", script, backing=backing)


def prefix_reading(text: str, frame: str = "prefix_code",
                   col1: str = "") -> Reading:
    backing = "reasoning.coding_theory.canonical_prefix_code"
    m = re.search(r"\bover\s+(\d+)\s+symbols?\s*$", text)
    d = int(m.group(1)) if m else 2
    body = text[:m.start()] if m else text
    try:
        lengths = [int(x) for x in body.split(",")]
    except ValueError:
        return _refusal(frame, "UNREADABLE", "write lengths L1, L2, ...",
                        col1 or text, backing=backing)
    col1 = col1 or f"a prefix code over {d} symbols with lengths {lengths}"
    try:
        code = CT.canonical_prefix_code(lengths, d)
    except CT.CodingError as e:
        return _refusal(frame, e.code, e.why, col1,
                        DS.kraft_refusal_script(lengths, d)
                        if e.code == "KRAFT_VIOLATED" else None, backing)
    shown = list(code)
    if MUTATE[0]:
        shown[-1] = shown[0]
    k = CT.kraft_sum(lengths, d)
    return Reading(frame, True, f"prefix code {', '.join(code)} (Kraft sum "
                                f"{k} <= 1)", col1,
                   "canonical construction: lengths in increasing order, each "
                   "codeword the previous one plus 1, shifted to its length",
                   DS.prefix_script(lengths, d, shown), backing=backing)


# ===========================================================================
# 3.  RATE DISTORTION AND THE RATE POSTERIOR
# ===========================================================================

_LETTER_SAMPLES = (Fraction(1, 3), Fraction(2, 5), Fraction(1, 4),
                   Fraction(1, 2))


def rd_reading(text: str, frame: str = "rate_distortion",
               col1: str = "") -> Reading:
    backing = "reasoning.coding_theory.hamming_rate_distortion"
    m = re.match(r"(.*?)\s+source\s+with\s+(.*?)(?:\s+distortion)?\s*$",
                 text.strip())
    if not m:
        return _refusal(frame, "UNREADABLE", "write SOURCE source with "
                        "hamming distortion", col1 or text, backing=backing)
    try:
        r = CT.hamming_rate_distortion(m.group(1), m.group(2))
    except CT.CodingError as e:
        if e.code == "UNSUPPORTED":            # Phase 119, any distortion
            general = D4.rd_reading(text, frame, col1, MUTATE[0])
            if general is not None:
                return general
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    col1 = col1 or f"R(D) for a {r.source_text} source under Hamming " \
                   f"distortion"
    if r.gap:                                  # Phase 118, past the bound
        full = D3.rd_full_reading(m.group(1), frame, col1, MUTATE[0])
        if full is not None:
            return full
    if r.letter is not None:
        samples = [([1 - p, p], p, p) for p in _LETTER_SAMPLES]
    else:
        samples = [(r.probs, r.tight_end_value, r.zero_from_value)]
    script = DS.rd_script(r.m, r.probs, samples, Fraction(1),
                          None, None, r.gap, mutate=MUTATE[0])
    if r.letter is not None:
        p = r.letter
        value = (f"R(D) = H({p}) - H(D) for 0 <= D <= {p}; R(D) = 0 for "
                 f"D >= {p} (taking {p} <= 1/2; H is the binary entropy in "
                 f"bits)")
    else:
        value = f"R(D) = {r.function} for 0 <= D <= {r.tight_end}"
        if r.gap:
            value += (f"; R(D) = 0 for D >= {r.zero_from}; between "
                      f"{r.tight_end} and {r.zero_from} refused NOT_TIGHT "
                      f"(the Shannon lower bound is not met there, so it is "
                      f"not printed as the function)")
        else:
            value += f"; R(D) = 0 for D >= {r.zero_from}"
        value += " (bits)"
    pen = {2: "", 3: " - D"}.get(r.m, f" - D*log2({r.m - 1})")
    col2 = (f"lower bound: I(X;Xh) = H(X) - H(X|Xh) >= H(X) - H(X - Xh) >= "
            f"H(X) - H(D){pen} (conditioning reduces entropy; an error "
            f"nonzero with probability <= D is most uncertain when uniform "
            f"off zero). Achieved by the backward channel X = Xh + Z, "
            f"P(Z != 0) = D: q = " + ", ".join(r.channel) +
            f", a distribution exactly while D <= {r.tight_end}. "
            f"At D = {r.zero_from} the constant reconstruction already meets "
            f"the distortion, so R = 0 beyond")
    return Reading(frame, True, value, col1, col2, script, backing=backing)


def posterior_reading(text: str, frame: str = "rate_posterior_derivation",
                      col1: str = "") -> Reading:
    backing = "reasoning.coding_theory.rate_posterior"
    t = text.strip()
    on_grid = "grid" in t
    m = re.search(r"k\s*=\s*(\d+)\s+errors?\s+in\s+n\s*=\s*(\d+)\s+bits", t)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
    elif re.search(r"\bk\s+errors?\s+in\s+n\s+bits", t):
        k = n = None
    else:
        return _refusal(frame, "UNREADABLE", "write k = K errors in n = N bits",
                        col1 or t, backing=backing)
    try:
        post = CT.rate_posterior(k, n, on_grid)
    except CT.CodingError as e:
        return _refusal(frame, e.code, e.why, col1 or t, backing=backing)
    col1 = col1 or ("the posterior of the bit-flip rate p after " +
                    (f"{k} flips in {n} bits" if k is not None
                     else "k flips in n bits"))
    cases = [(k, n, post.constant_value)] if k is not None else \
        [(kk, nn, CT.rate_posterior(kk, nn).constant_value)
         for kk, nn in ((3, 20), (1, 7), (0, 5), (5, 5), (2, 9))]
    if MUTATE[0]:
        cases = [(a, b, c + 1) for a, b, c in cases]
    grid = [g for g, _ in post.grid] if post.grid else None
    script = DS.posterior_script(cases, grid, post.peak, post.guard)
    value = (f"posterior density f(p | k, n) = {post.density} on [0, 1] "
             f"(uniform prior: Beta(k + 1, n - k + 1)); mode {post.mode}; "
             f"increasing on [0, {post.mode}] and decreasing after")
    if k is None:
        value = (f"posterior density f(p | k, n) = (n + 1)!/(k!*(n - k)!)*"
                 f"p^k*(1 - p)^(n - k) on [0, 1] (uniform prior: "
                 f"Beta(k + 1, n - k + 1)); mode k/n; d/dp ln f = k/p - "
                 f"(n - k)/(1 - p) > 0 for p < k/n, so f increases on "
                 f"[0, k/n] and decreases after")
    if post.grid:
        from ..reasoning.exact_forms import decimal
        gp = ", ".join(f"{g}: {decimal(x, 4)}" for g, x in post.grid)
        value += (f". On the machine's grid (uniform prior): {gp}; the peak "
                  f"is {post.peak}")
        if post.peak == post.guard:
            value += (f", the guard rate -- the reading the machine refuses "
                      f"RATE_GRID_EXCEEDED, since the rate may lie above "
                      f"every rate it hunted floors at")
    col2 = ("Bayes with a uniform prior: f(p) proportional to p^k (1-p)^(n-k); "
            "the normalising integral is the Beta function k!(n-k)!/(n+1)!")
    return Reading(frame, True, value, col1, col2, script, backing=backing)


# ===========================================================================
# 4.  MAXIMUM ENTROPY
# ===========================================================================

_SAMPLE_PARAMS = ({"mu": Fraction(3, 2), "var": Fraction(4)},
                  {"mu": Fraction(-2, 7), "var": Fraction(5, 3)},
                  {"mu": Fraction(0), "var": Fraction(1, 9)})


def maxent_reading(text: str, frame: str = "maximum_entropy",
                   col1: str = "") -> Reading:
    backing = "reasoning.maxent (log-partition function)"
    m = re.match(r"(\(.*?\)|\[.*?\]|\[.*?\))\s*(?:with\s+(.*))?$", text.strip())
    if not m:
        return _refusal(frame, "UNREADABLE", "write SUPPORT [with ...]",
                        col1 or text, backing=backing)
    try:
        r = ME.maximum_entropy(m.group(1), m.group(2) or "")
    except ME.MaxEntError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    col1 = col1 or f"the density of greatest differential entropy on " \
                   f"{r.support}" + (f" with {m.group(2)}" if m.group(2)
                                    else "")
    hr = {"gaussian": Fraction(1, 2), "exponential": Fraction(1),
          "uniform": Fraction(0)}[r.family]
    if MUTATE[0]:
        hr += 1
    if r.family == "gaussian":
        mu, var = r.params["mu"], r.params["var"]
        samples = [{"mu": sp["mu"] if mu != "0" else Fraction(0),
                    "var": sp["var"]} for sp in _SAMPLE_PARAMS]
        sub = (var, "var", mu, "mu")
        mult = {"l1": _py_sub(r.multipliers["l1"], *sub),
                "l2": _py_sub(r.multipliers["l2"], *sub),
                "l0r": _py_sub(_l0_rational(r.multipliers["l0"]), *sub)}
    elif r.family == "exponential":
        samples = [{"mu": sp["var"]} for sp in _SAMPLE_PARAMS]
        mult = {"l1": _py_sub(r.multipliers["l1"], r.params["mu"], "mu")}
    else:
        samples = [{"width": sp["var"]} for sp in _SAMPLE_PARAMS]
        mult = {}
    script = DS.maxent_script(r.family, samples, mult, hr)
    value = (f"f*(x) = {r.density}: h = {r.entropy} nats "
             f"(= {r.entropy_bits} bits), and every density on "
             f"{r.support}" + (f" with the same constraints" if r.constraints
                               else "") +
             f" has h(f) = h(f*) - D(f || f*) <= h(f*), with equality only "
             f"for f = f*")
    col2 = (f"candidate f* = exp(l0 + sum l_i T_i); {r.partition}; " +
            "; ".join(r.moments) + ("; " if r.moments else "") +
            "multipliers " + ", ".join(f"{k} = {v}" for k, v in
                                       r.multipliers.items()) +
            "; since log f* is affine in the constrained T_i, "
            "-int f log f* = -l0 - sum l_i c_i = h(f*) for every such f")
    return Reading(frame, True, value, col1, col2, script, backing=backing)


def _l0_rational(l0: str) -> str:
    """The rational part of ``l0`` (the text before ``- (1/2)*ln(``)."""
    head = l0.split("- (1/2)*ln(")[0].strip()
    return head or "0"


def _py_sub(text: str, *pairs: str) -> str:
    out = text
    for i in range(0, len(pairs), 2):
        a, b = pairs[i], pairs[i + 1]
        if a == "0":
            continue
        a_core = a.replace("^2", "") if a.endswith("^2") else a
        if a.endswith("^2"):
            out = re.sub(rf"\b{re.escape(a_core)}\^2\b", f"({b})", out)
            out = re.sub(rf"\b{re.escape(a_core)}\b", f"({b})**F(1,2)", out)
        else:
            out = re.sub(rf"\b{re.escape(a)}\b", f"({b})", out)
    return out


# ===========================================================================
# 5.  EIGENVALUE PROBLEMS AND SCATTERING
# ===========================================================================

def eigen_reading(text: str, frame: str = "eigenvalue_problem",
                  col1: str = "", source: str = "") -> Reading:
    backing = "reasoning.spectral.eigenvalue_problem"
    head, _, body = text.partition(":")
    parts = [p.strip() for p in body.split(";") if p.strip()]
    if not parts:
        return _refusal(frame, "UNREADABLE", "no equation", col1 or text,
                        backing=backing)
    try:
        e = SP.eigenvalue_problem(parts[0], parts[1:])
    except SP.SpectralError as err:
        if err.code == "TRANSCENDENTAL":       # Phase 118, a Robin end
            rob = D3.robin_reading(parts, frame, col1 or text, MUTATE[0])
            if rob is not None:
                return rob
        return _refusal(frame, err.code, err.why, col1 or text,
                        backing=backing)
    col1 = col1 or f"the eigenvalues and normalised eigenfunctions of " \
                   f"{parts[0]} with {'; '.join(parts[1:])}"
    lam = e.eigenvalue
    if MUTATE[0]:
        lam = f"2*({lam})"
    if e.kinds == ("P", "P"):
        fn, amp = "exp", (Fraction(1), -1)
        idx = [0, 1, 2, 3, -1, -2]
    else:
        fn = "sin" if e.kinds[0] == "D" else "cos"
        amp = (Fraction(2), -1)
        idx = [1, 2, 3, 4, 5]
    length = e.length.replace(" ", "")
    script = DS.eigen_script(e.kinds, lam, length, fn, amp, idx,
                             e.zero_eigen, e.freq)
    value = (f"lambda_{'m' if e.kinds == ('P', 'P') else 'n'} = "
             f"{e.eigenvalue}, {e.index}; {e.y} = {e.eigenfunction}")
    col2 = (f"{e.negative}. {e.zero_text}. lambda = k^2 > 0: "
            f"{e.y} = A*cos(k*{e.x}) + B*sin(k*{e.x}); {e.characteristic}. "
            f"Normalised by {e.normalisation}")
    return Reading(frame, True, value, col1, col2, script, backing=backing)


def scattering_reading(text: str, frame: str = "transmission",
                       col1: str = "") -> Reading:
    backing = "reasoning.spectral.transmission"
    m = re.match(r"V\(x\)\s*=\s*([^,]*)(?:,\s*(.*))?$", text.strip())
    if not m:
        return _refusal(frame, "UNREADABLE", "write V(x) = ...", col1 or text,
                        backing=backing)
    try:
        sc = SP.transmission(m.group(1), m.group(2))
    except SP.SpectralError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    col1 = col1 or f"the transmission coefficient of V(x) = {sc.potential}"
    kind = ("below" if sc.below else
            "step+delta" if sc.has_step and sc.has_delta else
            "step" if sc.has_step else "delta")
    claim = sc.T_text
    energy = sc.T_energy
    if kind == "step+delta":
        claim = "4*k1*k2/((k1 + k2)^2 + g^2)"
    claim_py = claim + (" + 1" if MUTATE[0] else "")
    energy_py = energy.replace(sc.strength.lstrip("-"), "a") if energy else None
    script = DS.scattering_script(kind, claim_py, energy_py)
    defs = []
    if sc.has_step:
        defs.append("k1 = sqrt(2*m*E)/hbar")
        defs.append("kappa = sqrt(2*m*(V0 - E))/hbar" if sc.below
                    else "k2 = sqrt(2*m*(E - V0))/hbar")
    else:
        defs.append("k = sqrt(2*m*E)/hbar")
    if sc.has_delta:
        defs.append(f"g = 2*m*{sc.strength.lstrip('-')}/hbar^2" if not
                    sc.strength.startswith("-") else
                    f"g = -2*m*{sc.strength.lstrip('-')}/hbar^2")
    if sc.below:
        value = ("T = 0: below the step the transmitted wave decays as "
                 "exp(-kappa*x) and carries no current; |r|^2 = 1, total "
                 "reflection")
    elif energy:
        value = f"T = {energy} (= {sc.T_text}), R = 1 - T"
    else:
        value = f"T = {sc.T_text}, R = 1 - T"
    value += " (" + ", ".join(defs) + ")"
    if sc.has_step:
        waves = ("psi = exp(i*k1*x) + r*exp(-i*k1*x) for x < 0, " +
                 ("t*exp(-kappa*x)" if sc.below else "t*exp(i*k2*x)") +
                 " for x > 0")
        flux = ("|r|^2 = 1 checked as an identity" if sc.below else
                "T = (k2/k1)*|t|^2, R = |r|^2, R + T = 1 checked as an "
                "identity")
    else:
        waves = ("psi = exp(i*k*x) + r*exp(-i*k*x) for x < 0, t*exp(i*k*x) "
                 "for x > 0")
        flux = "T = |t|^2, R = |r|^2, R + T = 1 checked as an identity"
    col2 = ("-hbar^2/(2*m)*psi'' + V*psi = E*psi; " + waves + "; " +
            "; ".join(sc.equations) + "; solved for r and t by Cramer's "
            "rule; " + flux)
    return Reading(frame, True, value, col1, col2, script, backing=backing)


# ===========================================================================
# 6.  THE FFT
# ===========================================================================

def fft_reading(text: str, kind: str, frame: str = "fft_derivation",
                col1: str = "") -> Reading:
    backing = "reasoning.fft_derivation"
    m = re.match(r"N\s*=\s*(\d+)\s*$", text.strip())
    if not m:
        return _refusal(frame, "UNREADABLE", "write N = 8", col1 or text,
                        backing=backing)
    try:
        f = FD.derive_fft(int(m.group(1)), kind)
    except FD.FFTError as e:
        return _refusal(frame, e.code, e.why, col1 or text, backing=backing)
    col1 = col1 or f"the radix-2 decimation-in-{'frequency' if kind == 'dif' else 'time'} FFT for N = {f.n}"
    flies = [(b.stage, b.top, b.bottom, b.twiddle) for b in f.butterflies]
    if MUTATE[0] and flies:
        s, a, b, e = flies[-1]
        flies[-1] = (s, a, b, e + 1)
    script = DS.fft_script(f.n, kind, flies, f.input_order, f.output_order,
                           f.stages, sum(1 for x in flies if x[3] % f.n))
    if kind == "dif":
        split = f"{FD.SPLIT_EVEN}; {FD.SPLIT_ODD}"
        bfly = "butterfly (a, b) -> (a + b, (a - b)*W_N^e)"
        order = f"inputs in natural order, outputs in bit-reversed order " \
                f"{f.output_order}"
    else:
        split = FD.DIT_SPLIT
        bfly = "butterfly (a, b) -> (a + W_N^e*b, a - W_N^e*b)"
        order = f"inputs in bit-reversed order {f.input_order}, outputs in " \
                f"natural order"
    value = (f"{split}. {f.stages} stages of {f.n // 2} butterflies "
             f"({len(f.butterflies)} in all), {bfly}; {f.nontrivial_twiddles} "
             f"multiplications by a twiddle other than W^0; {order}")
    col2 = "; ".join(f.stage_lines())
    return Reading(frame, True, value, col1, col2, script, backing=backing)


# ===========================================================================
# 7.  THE OPERATIONS
# ===========================================================================

def match_raw(text: str) -> Optional[dict]:
    t = text.strip()
    low = t.lower()
    for p in PREFIXES:
        if low.startswith(p):
            return {"raw": t, "op": p}
    return None


def read_operation(text: str) -> Reading:
    t = text.strip()
    low = t.lower()
    for p in PREFIXES:
        if low.startswith(p):
            rest = t[len(p):].strip()
            break
    else:                                                # pragma: no cover
        return _refusal("derivation_two", "UNREADABLE", "no operation", t)
    if p == INEQ:
        return inequality_reading(rest)
    if p == UD:
        return code_reading(rest)
    if p == PREFIX:
        return prefix_reading(rest)
    if p == RD:
        return rd_reading(rest)
    if p == MAXENT:
        return maxent_reading(rest)
    if p == EIGEN:
        return eigen_reading(t[len("solve eigenvalue problem for "):])
    if p == SCATTER:
        return scattering_reading(rest)
    if p in (FFT_DIF, FFT_DIT):
        return fft_reading(rest, "dif" if p == FFT_DIF else "dit")
    return posterior_reading(rest)


def _match_op(t: str) -> Optional[dict]:
    return None                   # read on the raw text, see match_raw


OPERATION_FRAME = Frame("derivation_two", "information inequalities; codes; "
                        "rate distortion; maximum entropy; eigenvalue "
                        "problems; transmission; the FFT; the rate posterior",
                        _match_op, lambda g: read_operation(g["raw"]),
                        source="P2")


def mutated_operation(text: str) -> Reading:
    MUTATE[0] = True
    try:
        return read_operation(text)
    finally:
        MUTATE[0] = False


# ===========================================================================
# 8.  THE OUTSIDE FRAMES (the rest of class P)
# ===========================================================================

def _m_delta_barrier(t: str) -> Optional[dict]:
    if "delta" in t and "transmission" in t and "schr" in t and \
            re.search(r"v\(x\)\s*=\s*(α|alpha)\s*(δ|delta)\(x\)", t):
        return {}
    return None


def _a_delta_barrier(g: dict) -> Reading:
    rd = scattering_reading("V(x) = alpha*delta(x)", frame="delta_barrier",
                            col1="a particle of mass m and energy E > 0 on "
                                 "V(x) = alpha*delta(x): T(E)")
    if rd.answered:
        rd.value = ("-hbar^2/(2*m)*psi'' + alpha*delta(x)*psi = E*psi; for "
                    "x != 0 free waves with k = sqrt(2*m*E)/hbar; psi "
                    "continuous at 0 and psi'(0+) - psi'(0-) = "
                    "(2*m*alpha/hbar^2)*psi(0) (integrate the equation "
                    "across 0). " + rd.value)
    return rd


def _m_ring(t: str) -> Optional[dict]:
    if "ring" in t and "rigid rotor" in t and "eigenvalues" in t and \
            "phi" in t:
        return {}
    return None


def _a_ring(g: dict) -> Reading:
    rd = eigen_reading("psi(phi): d2(psi)/dphi2 + lambda*psi = 0; "
                       "psi(0) = psi(2*pi); d(psi)/dphi(0) = "
                       "d(psi)/dphi(2*pi)", frame="particle_on_ring",
                       col1="a particle on a ring, H = -(hbar^2/(2*I))*"
                            "d^2/dphi^2: normalised eigenfunctions and "
                            "energies")
    if rd.answered:
        rd.value = ("H*psi = E*psi reads psi'' + lambda*psi = 0 with "
                    "lambda = 2*I*E/hbar^2; psi must be single-valued on the "
                    "ring, psi(phi + 2*pi) = psi(phi) (and so psi'), which "
                    "makes the problem periodic on [0, 2*pi]. " + rd.value +
                    "; so E_m = m^2*hbar^2/(2*I) with m = 0, +-1, +-2, ... "
                    "(each level m != 0 twofold: +m and -m), psi_m(phi) = "
                    "exp(i*m*phi)/sqrt(2*pi)")
    return rd


def _m_fft_dif(t: str) -> Optional[dict]:
    if "decimation-in-frequency" in t and "butterfly" in t and \
            "derive" in t:
        return {}
    return None


def _a_fft_dif(g: dict) -> Reading:
    rd = fft_reading("N = 8", "dif", frame="fft_dif",
                     col1="the radix-2 decimation-in-frequency FFT for "
                          "N = 2^v, and its butterfly")
    if rd.answered:
        rd.value = ("with W_N = exp(-2*pi*i/N) and W_N^(N/2) = -1, split "
                    "x into x[n] and x[n + N/2], n < N/2: X[k] = "
                    "sum_{n=0}^{N/2-1} (x[n] + (-1)^k*x[n + N/2])*W_N^(n*k); "
                    "even and odd k decouple: " + FD.SPLIT_EVEN + "; " +
                    FD.SPLIT_ODD + " -- two N/2-point DFTs. The butterfly: "
                    "a = x[n], b = x[n + N/2] -> a + b and (a - b)*W_N^n; "
                    "repeated log2(N) times. Worked for N = 8: " + rd.value)
    return rd


_DEPENDENT = ((Fraction(1, 2), Fraction(0)), (Fraction(1, 4), Fraction(1, 4)))
_INDEPENDENT = ((Fraction(1, 6), Fraction(1, 3)),
                (Fraction(1, 6), Fraction(1, 3)))


def _kl_script(mutate: bool) -> str:
    """The KL identity I(X;Y) = D(p(x,y) || p(x)p(y)) exactly, and its sign,
    on a dependent and an independent joint law."""
    tables = [_DEPENDENT, _INDEPENDENT]
    body = "TABLES = [" + ", ".join(
        "[" + ", ".join("[" + ", ".join(DS._q(x) for x in row) + "]"
                        for row in tb) + "]" for tb in tables) + "]"
    return DS._LOGFORM + "\n" + body + f"\nMUTANT = {mutate!r}\n" + r'''
for k, P in enumerate(TABLES):
    px = [sum(r) for r in P]; py = [sum(c) for c in zip(*P)]
    hx, hy = entropy(px), entropy(py)
    hxy = entropy([x for r in P for x in r])
    I = lf_add(lf_add(hx, hy), hxy, -1)
    D = {}
    for i, r in enumerate(P):
        for j, x in enumerate(r):
            if x:
                D = lf_add(D, log2form(x / (px[i] * py[j])), x)
    if MUTANT:
        D = lf_add(D, {3: F(1)})
    assert I == D, ('I != D', I, D)
    lo, hi = lf_bounds(D)
    independent = all(P[i][j] == px[i] * py[j] for i in range(2) for j in range(2))
    if independent:
        assert D == {}, 'D = 0 for a product law'
    else:
        assert lo > 0, 'D > 0 for a dependent law'
print('KL: I(X;Y) = D(p(x,y) || p(x)p(y)) exactly; > 0 dependent, = 0 independent VERIFIED True')
'''


def _m_mutual_information(t: str) -> Optional[dict]:
    if "mutual information" in t and "non-negative" in t and \
            "kullback" in t:
        return {}
    return None


def _a_mutual_information(g: dict) -> Reading:
    rd = inequality_reading("|- I(X;Y) >= 0", frame="mutual_information",
                            col1="I(X;Y) >= 0, the equality condition, "
                                 "through the Kullback-Leibler divergence")
    if not rd.answered:
        return rd
    rd.value = ("I(X;Y) = sum_{x,y} p(x,y)*log(p(x,y)/(p(x)*p(y))) = "
                "D(p(x,y) || p(x)*p(y)), the divergence of the joint law from "
                "the product of its marginals. Gibbs' inequality (from "
                "ln t <= t - 1, equality only at t = 1): D(p || q) >= 0 for "
                "distributions p, q, with equality exactly when p = q. Hence "
                "I(X;Y) >= 0, and I(X;Y) = 0 exactly when p(x,y) = "
                "p(x)*p(y) for every x, y -- X and Y independent. "
                "(Gibbs' inequality and this corollary are proved in " +
                LEAN_FILE_NAME + ": gibbs_inequality, "
                "mutual_information_nonneg.) As a Shannon inequality: " +
                rd.value)
    rd.script = _kl_script(MUTATE[0])
    rd.column2 = ("checked exactly on two joint laws: [[1/2, 0], [1/4, "
                  "1/4]] (dependent: D > 0) and [[1/6, 1/3], [1/6, 1/3]] "
                  "(independent: D = 0); " + rd.column2)
    return rd


def _m_data_processing(t: str) -> Optional[dict]:
    if "data processing inequality" in t and "markov" in t:
        return {}
    return None


def _a_data_processing(g: dict) -> Reading:
    rd = inequality_reading("I(X;Z|Y) = 0 |- I(X;Y) >= I(X;Z)",
                            frame="data_processing",
                            col1="X -> Y -> Z Markov (I(X;Z|Y) = 0): is "
                                 "I(X;Y) >= I(X;Z)?")
    if not rd.answered:
        return rd
    rd.value = ("the Markov chain X -> Y -> Z means I(X;Z|Y) = 0. The chain "
                "rule expands I(X;Y,Z) both ways: I(X;Z) + I(X;Y|Z) = "
                "I(X;Y) + I(X;Z|Y), so I(X;Y) - I(X;Z) = I(X;Y|Z) - "
                "I(X;Z|Y) = I(X;Y|Z) >= 0. " + rd.value +
                ". Read as a statement about processing: Z is computed from "
                "Y alone, and no such processing raises what is known about "
                "X. Its wider physical significance: refused EXPLANATION (an "
                "account, not a derivation)")
    return rd


def _m_gaussian_entropy(t: str) -> Optional[dict]:
    if "differential entropy" in t and "gaussian" in t and "maxim" in t:
        return {}
    return None


def _a_gaussian_entropy(g: dict) -> Reading:
    rd = maxent_reading("(-inf, inf) with mean mu and variance sigma^2",
                        frame="gaussian_entropy",
                        col1="h(X) for X ~ N(mu, sigma^2), and the maximum "
                             "at fixed variance")
    if rd.answered:
        rd.value = ("for the Gaussian density f(x) = exp(-(x - mu)^2/"
                    "(2*sigma^2))/sqrt(2*pi*sigma^2): h = -E ln f = "
                    "(1/2)*ln(2*pi*sigma^2) + E(X - mu)^2/(2*sigma^2) = "
                    "(1/2)*ln(2*pi*sigma^2) + 1/2, i.e. "
                    "h = (1/2)*ln(2*pi*e*sigma^2) nats. Maximality, as the "
                    "maximum-entropy derivation gives it: " + rd.value)
    return rd


def _kraft_script(mutate: bool) -> str:
    """The McMillan counting bound on a uniquely decodable code that is not
    prefix-free: N_L (n-tuples of codewords of total length L) <= 2^L, so
    K^n <= n*l_max - n + 1."""
    return r'''
from fractions import Fraction as F
from itertools import product
W = ['0', '01', '011']
''' + f"MUTANT = {mutate!r}\n" + r'''
lmax = max(map(len, W))
K = sum(F(1, 2 ** len(w)) for w in W)
for n in range(1, 6):
    strings = {}
    for tup in product(W, repeat=n):
        s = ''.join(tup)
        strings[s] = strings.get(s, 0) + 1
    assert all(c == 1 for c in strings.values()), 'two tuples give one string'
    NL = {}
    for s in strings:
        NL[len(s)] = NL.get(len(s), 0) + 1
    assert all(NL[L] <= 2 ** L for L in NL)
    Kn = sum(F(c, 2 ** L) for L, c in NL.items())
    assert Kn == K ** n
    assert Kn <= n * lmax - n + 1
claim = F(7, 8) + (F(1, 4) if MUTANT else 0)
assert K == claim and K <= 1
print('KRAFT-McMILLAN: K =', K, '; K^n <= n*l_max - n + 1 for n <= 5 VERIFIED True')
'''


def _m_kraft(t: str) -> Optional[dict]:
    if "kraft" in t and "mcmillan" in t and "uniquely decodable" in t:
        return {}
    return None


def _a_kraft(g: dict) -> Reading:
    rd = code_reading("0, 01, 011", frame="kraft_mcmillan",
                      col1="the Kraft-McMillan inequality for uniquely "
                           "decodable codes, and why it binds")
    if not rd.answered:
        return rd
    rd.value = ("for a uniquely decodable code over D symbols with lengths "
                "l_1, ..., l_m: sum_i D^(-l_i) <= 1. Proof (McMillan): "
                "with K = sum_i D^(-l_i), K^n = sum over n-tuples of "
                "codewords of D^(-(total length)) = sum_{L=n}^{n*l_max} "
                "N_L*D^(-L), where N_L counts the n-tuples of total length L. "
                "Unique decodability makes distinct tuples distinct strings, "
                "so N_L <= D^L and K^n <= n*l_max - n + 1. If K > 1 the left "
                "side grows exponentially in n and the right linearly, a "
                "contradiction; so K <= 1 -- the same bound Kraft's "
                "inequality places on prefix codes. Conversely every length "
                "vector with K <= 1 has a prefix code (Kraft's canonical "
                "construction), so a uniquely decodable code can always be "
                "replaced by a prefix code with the same lengths: the "
                "constraint is what limits how short codewords can be "
                "(shortening one forces others longer) and it is what gives "
                "the average length the entropy as its floor. Proved for "
                "every code in " + LEAN_FILE_NAME + " (kraft_mcmillan). "
                "Worked on the code {0, 01, 011}: " + rd.value)
    rd.script = _kraft_script(MUTATE[0])
    rd.column2 = ("the counting bound re-counted for n = 1..5 on {0, 01, "
                  "011}; " + rd.column2)
    return rd


def _m_rate_distortion(t: str) -> Optional[dict]:
    if "rate-distortion" in t and "bernoulli(p)" in t and "hamming" in t:
        return {}
    return None


def _a_rate_distortion(g: dict) -> Reading:
    rd = rd_reading("bernoulli(p) source with hamming distortion",
                    frame="binary_rate_distortion",
                    col1="R(D) of a Bernoulli(p) source, p <= 1/2, under "
                         "Hamming distortion")
    if rd.answered:
        rd.value = (rd.value + ". For D > p: R(D) = 0 -- always sending "
                    "Xh = 0 has distortion P(X = 1) = p < D at zero rate, so "
                    "no information need be sent")
    return rd


def _core_reading(frame: str, premises: Sequence[str], goal: str) -> Tuple[
        str, str]:
    from ..reasoning import proof_search as PS
    prem, g = PS.parse_sequent(", ".join(premises) + " |- " + goal)
    v = PS.decide(prem, g)
    lines = PS.proof_lines(v.proof) if v.proof is not None else []
    return v.kind, "; ".join(x.strip() for x in lines)


def _m_compactness(t: str) -> Optional[dict]:
    if "compactness" in t and "arbitrarily large finite models" in t and \
            "infinite model" in t:
        return {}
    return None


def _a_compactness(g: dict) -> Reading:
    prem = ["FinSat", "FinSat -> Sat", "Sat -> (ModelT & Infinite)"]
    goal = "ModelT & Infinite"
    kind, proof = _core_reading("compactness", prem, goal)
    goal_s = goal if not MUTATE[0] else "ModelT & Infinite & Finite"
    script = DS.proof_core_script(prem, goal_s, label="COMPACTNESS CORE")
    value = ("for n >= 2 let sigma_n say 'there are at least n elements' "
             "(exists x1 ... xn, xi != xj for i < j), a first-order "
             "sentence. Let T' = T + {sigma_n : n >= 2}. Any finite subset "
             "of T' lies in T + {sigma_2, ..., sigma_N} for some N; T has a "
             "finite model with at least N elements, which satisfies all of "
             "these, so every finite subset of T' has a model (FinSat). By "
             "compactness T' has a model M (FinSat -> Sat). M satisfies T "
             "and every sigma_n, so M is infinite: T has an infinite model. "
             "Proved over Mathlib's first-order logic in " + LEAN_FILE_NAME +
             " (infinite_model_of_large_finite_models, from "
             "isSatisfiable_iff_isFinitelySatisfiable); the propositional "
             "core, " + ", ".join(prem) + " |- " + goal + ", proved " + kind +
             "ly by G4ip: " + proof)
    return Reading("compactness_infinite_model", True, value,
                   "if T has arbitrarily large finite models, does it have "
                   "an infinite model?",
                   "the core sequent re-decided by truth table; the "
                   "first-order steps are the Lean theorem's", script,
                   backing="Lean theorem (" + LEAN_FILE_NAME + ") + "
                           "reasoning.proof_search for the core")


def _m_tarski(t: str) -> Optional[dict]:
    if "tarski" in t and "diagonal lemma" in t and "truth" in t:
        return {}
    return None


def _a_tarski(g: dict) -> Reading:
    prem = ["D <-> ~TD", "TD <-> D"]
    goal = "false"
    kind, proof = _core_reading("tarski", prem, goal)
    script = DS.proof_core_script(prem if not MUTATE[0] else prem[:1], goal,
                                  label="TARSKI CORE")
    value = ("suppose a formula True(x) of arithmetic defined truth: for "
             "every sentence S, N |= True(#S) <-> S, with #S the Goedel "
             "number of S. The diagonal lemma, applied to the formula "
             "~True(x), gives a sentence D with N |= D <-> ~True(#D). Then "
             "True(#D) <-> D <-> ~True(#D), a contradiction; so the set of "
             "Goedel numbers of true sentences is not definable in "
             "arithmetic. The contradiction step is propositional: with "
             "TD = True(#D), the sequent D <-> ~TD, TD <-> D |- false is "
             "proved " + kind + "ly by G4ip (" + proof + "). The argument "
             "in general form -- any interpretation with diagonal "
             "sentences and negation has no truth predicate -- is proved in "
             + LEAN_FILE_NAME + " (tarski_undefinability, the same diagonal "
             "step as lawvere_fixed_point). Why truth must therefore live in a "
             "metalanguage: refused EXPLANATION (an account, not a "
             "derivation)")
    return Reading("tarski_undefinability", True, value,
                   "is arithmetical truth definable in arithmetic?",
                   "the core sequent re-decided by truth table; the "
                   "diagonal lemma is the Lean theorem's hypothesis",
                   script, backing="Lean theorem (" + LEAN_FILE_NAME + ") + "
                                   "reasoning.proof_search for the core")


def _m_rate_grid(t: str) -> Optional[dict]:
    if "rate_grid_exceeded" in t and "posterior" in t and \
            "binary symmetric channel" in t:
        return {}
    return None


def _a_rate_grid(g: dict) -> Reading:
    rd = posterior_reading("k errors in n bits", frame="rate_grid_posterior",
                           col1="the posterior of a BSC's flip rate after k "
                                "errors in n bits, and the guard point")
    if not rd.answered:
        return rd
    demo = posterior_reading("k = 3 errors in n = 20 bits on the machine's "
                             "grid")
    rd.value = (rd.value + ". If k/n exceeds every grid rate below the "
                "guard, f is increasing all the way to the guard, so on a "
                "grid capped at the guard the largest posterior mass sits at "
                "the guard itself. Worked on the machine's grid: " +
                demo.value.split(". On the machine's grid (uniform prior): ")
                [-1])
    rd.disputes = (
        "the machine's guard rate is 1/5, not 1/10: 1/10 is the largest "
        "rate floors were hunted at (reasoning.rate_posterior.GRID)",
        "the refusal is not numerical instability: the posterior is computed "
        "exactly in rationals; it refuses because the reads say the rate may "
        "lie above every rate a floor was hunted at",
        "the machine's own likelihood is the coset mass of a read (the true "
        "codeword unknown), not p^k (1-p)^(n-k) for a known error count; the "
        "derivation above is the textbook case the question asks for")
    rd.script = demo.script        # mutated with the reading under MUTATE
    return rd


OUTSIDE_P2_FRAMES: Tuple[Frame, ...] = (
    Frame("delta_barrier", "a delta-function barrier: Schroedinger matching "
          "and T(E)", _m_delta_barrier, _a_delta_barrier, "P2"),
    Frame("particle_on_ring", "a particle on a ring: periodic eigenvalue "
          "problem", _m_ring, _a_ring, "P2"),
    Frame("fft_dif", "the radix-2 decimation-in-frequency FFT", _m_fft_dif,
          _a_fft_dif, "P2"),
    Frame("mutual_information", "I(X;Y) >= 0 through the KL divergence",
          _m_mutual_information, _a_mutual_information, "P2"),
    Frame("data_processing", "the data processing inequality",
          _m_data_processing, _a_data_processing, "P2"),
    Frame("gaussian_entropy", "the differential entropy of a Gaussian and "
          "its maximality", _m_gaussian_entropy, _a_gaussian_entropy, "P2"),
    Frame("kraft_mcmillan", "the Kraft-McMillan inequality", _m_kraft,
          _a_kraft, "P2"),
    Frame("binary_rate_distortion", "R(D) of a Bernoulli source",
          _m_rate_distortion, _a_rate_distortion, "P2"),
    Frame("compactness_infinite_model", "compactness: arbitrarily large "
          "finite models give an infinite one", _m_compactness,
          _a_compactness, "P2"),
    Frame("tarski_undefinability", "Tarski: truth is not definable",
          _m_tarski, _a_tarski, "P2"),
    Frame("rate_grid_posterior", "the BSC rate posterior and the guard "
          "point", _m_rate_grid, _a_rate_grid, "P2"),
)


def mutated_outside(frame: Frame, givens: dict) -> Reading:
    MUTATE[0] = True
    try:
        return frame.answer(givens)
    finally:
        MUTATE[0] = False
