#!/usr/bin/env python3
"""GLM Hypothesis Engine v17 - the TCT gate cascade, made to work.

Built on v16 (all guards layer-aware, clean dialogue), v15 (TCT gate inside the loop,
transitive rollback) and v14 (observatory, tools, Round 42 guards).  Standard library only;
exact integer / Fraction arithmetic only.

What v17 changes (each item is a defect of v15/v16 found by running them; see V17_REPORT.md)

 1. Runs as shipped.  All modules it needs are in this folder; outputs go to --out DIR.
 2. Honest layers (glm_layers.py).  The five GLM layer names are kept, each with its real scale
    (box size, domain cut-off, sample size, neighbourhood, range of n, set of seeds).  No "mod 144 /
    mod 256" label is attached to a size cut-off any more.
 3. Correct aggregation.  Universal claims: refuted at the first failing layer (passing layers form
    a prefix, checked at run time).  Statistics and explanations: the verdict is the verdict at the
    LARGEST scale (v16: "explained at ANY scale", which an empty layer satisfies vacuously).
    Coincidence: every layer recounts N, K, events and hits (v16 kept hits fixed while shrinking N).
 4. The TCT gate is a cascade run after EVERY stage (inside the loop), on every hypothesis the
    stage created or changed:
        claim-class gate  -> what kind of evidence can settle this claim at all?
        recompute gate    -> re-derive reported numbers and comparisons from the data
        escalation gate   -> read a surviving universal claim at larger scales before speaking it
        implication gate  -> an "A implies B" claim needs a checked edge
        ledger gate       -> Lean-checked provisions (FORMAL / CERT) decide, with the Lean name
    A gate may only lower a claim to what its evidence supports; only the ledger gate raises a
    claim to "proved" (Lean: GateLoop.cascade_sound - sound gates never refute a true claim).
 5. Typed, order-independent transitive rollback.  Only edges where the child DEPENDS on the parent
    (prediction, lift, transport) propagate a refutation; derived edges (cut, narrow, mechanism read
    off a counterexample, control) do not, because a narrowed claim does not need its refuted
    parent (Lean: GateLoop.derived_edge_unsound).  The retracted set is the least closed set,
    computed as a fixpoint (Lean: GateLoop.loop_eq_retracted, retracted_union): the set of claims no longer asserted does not depend on the order in
    which refutations arrive.
 6. The arrow.  Every hypothesis carries its read trajectory: the layers read and the verdict at
    each.  The read layer only goes up; the direction is "converging" (verdict stable between the
    last two reads) or "flipped at <layer>".  This is the owner's Wobble/Observer proposal: the
    observer's read position and the direction the run is converging towards.
 7. Clean trajectory dialogue.  Only claims whose status is backed are spoken, each with its
    backing: proved (Lean name), verified exactly (finite claim, whole range computed), survives to
    a stated scale (open beyond), open, estimate.  Refuted, retracted, untested and unchecked claims
    are summarised, never asserted.  The consistency check verifies this.

Run:  python3 hypothesis_engine_v17.py [--quick] [--no-ledger] [--out DIR]
"""

from __future__ import annotations

import json
import re
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from hypothesis_engine_v14 import Hypothesis, centre_column, exact_wobble, sanitize  # noqa: E402
from hypothesis_engine_v15 import GUARD_EXTRACTORS, GuardInput, _big_profile  # noqa: E402
from hypothesis_engine_v16 import EngineV16, CleanDialogue  # noqa: E402  (registers v16 extractors)
from glm_guards import Premise  # noqa: E402
from tax_guards import JUMPS as TAX_JUMPS, LEAN as TAX_LEAN  # noqa: E402
from glm_layers import (LAYER_NAMES, LayerProfile, identity_layered, explained_away_layered,  # noqa: E402
                        coincidence_layered, exclusivity_layered, escalation_profile)
from needs_rule30 import centre_bits, lc_profile, ldiag  # noqa: E402  (exact tools, Round 44)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 0. Status vocabulary
# ═════════════════════════════════════════════════════════════════════════════════════════════

PROVED = "proved"                       # Lean FORMAL / CERT, name attached
VERIFIED = "verified-exact"             # finite claim, the whole finite range computed exactly
SURVIVES_TO = "survives-to"             # universal claim, survives every scale read; open beyond
OPEN = "open"
ESTIMATE = "estimate"
MEASURED = "measured"                   # a measurement, not a claim about all cases
UNTESTED = "untested"                   # analogy / proposal / trend: no executable test
UNCHECKED = "unchecked-implication"
RETRACTED = "retracted"                 # depends on a refuted parent

SPEAKABLE = {PROVED, VERIFIED, SURVIVES_TO, OPEN, ESTIMATE, MEASURED}


def is_refuted(status: str) -> bool:
    return status.startswith("refuted")


def answer_of(status: str) -> Optional[bool]:
    """What the final status asserts about the claim as stated: True / False / None (no verdict)."""
    if status in (PROVED, VERIFIED):
        return True
    if is_refuted(status):
        return False
    return None


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 1. Claim classes: what kind of evidence can settle a claim?
# ═════════════════════════════════════════════════════════════════════════════════════════════
#   finite      a finite statement: an exact computation of the whole range settles it
#   Pi1         "for every index ...": data can refute, never prove; survives-to-scale at best
#   Pi2         "infinitely many / unbounded": no finite data settles it (NeedsWheel.lean)
#   implication "A follows from B": a claim about all models; needs a checked edge
#   comparison  a reported comparison between two measured numbers: recompute it
#   measurement a reported measurement: recompute it; not a universal claim
#   estimate    an extrapolation
#   analogy / proposal / meta / trend: no executable test

CLAIM_CLASS = {
    "LD.period.divides.8": "Pi1", "LD.preperiod.gt.D": "Pi1", "LD.preperiod.envelope": "Pi1",
    "LD.white.finite": "Pi1", "LD.period.divides.8.below": "finite",
    "LD.period.divides.16": "Pi1", "LD.period.law.simple": "Pi1", "LD.period.law": "Pi1",
    "LD.first.period.32": "finite", "LD.period.divides.16.below": "finite",
    "LD.periods.unbounded": "Pi2", "LD.seed.independent": "Pi1", "LD.seed.forgetting": "Pi1",
    "RD.lp.le.2^D": "Pi1", "RD.lp.gt.half": "Pi1", "RD.periodic.or.anti": "Pi1",
    "CC.no.short.period": "finite", "CC.balance.sqrt": "Pi1", "CC.balance.sqrt.2": "Pi1",
    "CC.lc.half": "Pi1", "CC.lc.half.2": "Pi1", "CC.words.early": "Pi1",
    "APP.lattice.addressing": "analogy", "APP.rcalculus.model": "proposal",
    "APP.evidence.prediction": "meta", "APP.deephole.ladder": "analogy",
    "APP.retrieval.uniformity": "proposal", "APP.conversation.reset": "analogy",
    "GAP.ratio.growing": "trend", "GAP.next.estimate": "estimate", "GAP.chain.explanation": "meta",
    "GAP.centre.diagonal.connection": "implication", "GAP.unbounded.undecidable": "implication",
    "APPTEST.ladder.spacing": "analogy", "APPTEST.rcalculus.match": "measurement",
    "APPTEST.uniformity.benchmark": "comparison",
    "NRCI.clustered.equals.jumps": "Pi1", "TAX.defect.contains.jumps": "Pi1",
    "WOBBLE.transportable": "Pi1", "DS.accumulator.growing": "trend",
    "TAX.mechanism.cluster": "mechanism", "TAX.substrate.model": "analogy",
    "TAX.mechanism.predictive": "estimate", "TAX.conserved.at.jumps": "finite",
    "TAX.substrate.model.qualified": "Pi1", "WOBBLE.balanced.density": "Pi1",
    "WOBBLE.sturmian": "Pi1", "BROKEN.tax.criterion": "Pi1", "BROKEN.balance.criterion": "Pi1",
}

NO_TEST_CLASSES = {"analogy", "proposal", "meta", "trend"}

# Edges along which a refutation propagates: the child's claim USES the parent's claim.
DEPENDENT_ORIGINS = {"prediction", "lift", "analogy", "transport"}
# Derived edges (no propagation): cut, narrow, mechanism (read off a counterexample), control,
# recompute (a corrected restatement).


_FINITE_RANGE = re.compile(r"(D\s*<\s*\d+|D\s*∈\s*\{|n\s*≤\s*\d+\s*only|≤\s*\d+\s*and preperiod\s*≤\s*\d+|"
                           r"first left diagonal with|first \d+ bits|is D = \d+)")


def auto_claim_class(text: str, origin: str = "") -> str:
    """Classify a claim from its sentence alone (no per-key knowledge).

    This is the automatic guard-extractor that the v16 report proposed as the next step.  It is
    measured against the hand-written registry in run_round45.py (`auto` condition)."""
    t = text.lower()
    if any(w in t for w in ("implied by", "follows from", " implies ", "because the", "is the cause")):
        return "implication"
    if any(w in t for w in ("deliberately broken",)):
        return "Pi1"
    if "estimat" in t or "extrapolat" in t:
        return "estimate"
    if any(w in t for w in ("infinitely many", "unbounded", "without bound")):
        return "Pi2"
    if "match:" in t:
        return "measurement"
    if re.search(r"\b(more|less) uniform than\b", t):
        return "comparison"
    if any(w in t for w in ("analogous", "analogy", "same structure", "is a model", "physical instance",
                            "dyadic tower", "can be compared", "provide an", "provides an",
                            "benchmark", "fingerprint", "forward-looking", "predicts where",
                            "is evidence", "cross-domain")):
        return "analogy"
    if any(w in t for w in ("grows with", "growing", "increasing trend")):
        return "trend"
    if _FINITE_RANGE.search(text):
        return "finite"
    if origin == "analysis" and not any(w in t for w in ("every", "for all", "exactly", "only")):
        return "meta"
    return "Pi1"


USE_REGISTRY = True        # run_round45.py switches this off for the `auto` condition


def claim_class(h: Hypothesis) -> str:
    if USE_REGISTRY and h.key in CLAIM_CLASS:
        return CLAIM_CLASS[h.key]
    return auto_claim_class(h.text, h.origin)


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 2. The ledger gate: Lean-checked provisions (FORMAL / CERT).  Every name below exists in the
#    Lean package RequestProject/GLM (all cited names checked against the Lean ledger, Round 45).
# ═════════════════════════════════════════════════════════════════════════════════════════════

def _lc_bound(h):
    m = re.search(r"≤\s*(\d+)\s*for all n", h.text)
    return int(m.group(1)) if m else None


def _sqrt_const(h):
    m = re.search(r"≤\s*(\d+)·√N", h.text)
    return int(m.group(1)) if m else None


def _ledger_lc(h):
    b = _lc_bound(h)
    if b is None:
        return None
    if b <= 10:
        return (False, "CERT", "GLM.HypothesisEngine.WheelChecks.wheel_H19_false "
                "(2·L(11101) − 11101 ≥ 11)")
    if b <= 12:
        return (False, "CERT", "GLM.HypothesisEngine.WheelChecks.ledger_C160_overstated "
                "(2·L(19521) − 19521 ≥ 13)")
    return None


def _ledger_balance(h):
    c = _sqrt_const(h)
    if c is not None and c * c * 24979 >= 175561:
        return ("partial", "CERT", "GLM.Rule30 WobbleCertificate.wobble_sq_ratio_cert "
                "(max D(N)²/N on N ≤ 10^6 is 175561/24979, so the bound holds to 10^6)", 10 ** 6)
    return None


def _ledger_no_short_period(h):
    m = re.search(r"p\s*≤\s*(\d+)\s*and preperiod\s*≤\s*(\d+)", h.text)
    if not m:
        return None
    p, tau = int(m.group(1)), int(m.group(2))
    if p <= 64 and tau <= 10000:
        return (True, "CERT", "GLM.HypothesisEngine.WheelChecks.wheel_H16_true")
    if p <= 64 and tau <= 30000:
        return (True, "CERT", "GLM.HypothesisEngine.GateLoopData.centre_no_short_period_30000 "
                "(Round 45)")
    return None


LEDGER = {
    "LD.period.divides.8": lambda h: (False, "CERT",
                                      "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight"),
    "LD.period.divides.8.below": lambda h: (True, "CERT",
                                            "LeftDiagonalPeriodsData.leftDiag_period_eight_below_400")
    if "D < 400" in h.text else None,
    "LD.period.divides.16": lambda h: (False, "CERT",
                                       "LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen"),
    "LD.period.divides.16.below": lambda h: (True, "CERT",
                                             "LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867")
    if "D < 87867" in h.text else None,
    "LD.first.period.32": lambda h: (True, "CERT",
                                     "LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + "
                                     "leftDiag_period_sixteen_below_87867")
    if "87867" in h.text else None,
    "LD.white.finite": lambda h: (False, "FORMAL",
                                  "WhiteDiagonals.ldiag_infinitely_many_white; "
                                  "LeftDiagonalPeriodsData.leftDiag_white_below_87868"),
    "LD.period.law": lambda h: (True, "FORMAL",
                                "LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, "
                                "ldiag_keeps_of_even"),
    "LD.periods.unbounded": lambda h: ("open", "FORMAL",
                                       "open (ledger C359); proved reduction "
                                       "WhiteDiagonals.ldiag_periods_unbounded_iff"),
    "LD.seed.forgetting": lambda h: (True, "FORMAL",
                                     "LeftDiagonalPeriods.first_difference_after_white; "
                                     "LeftDiagonalPeriodsData.seed_first_difference"),
    "LD.preperiod.gt.D": lambda h: ("partial", "CERT",
                                    "LeftDiagonalPeriodsData.centerCol_read_in_transient "
                                    "(20 ≤ D < 20000 only)", 20000),
    "RD.lp.le.2^D": lambda h: (True, "FORMAL", "Diagonals.rdiag_periodic"),
    "RD.lp.gt.half": lambda h: (True, "FORMAL", "Diagonals.rdiag_not_periodic"),
    "RD.periodic.or.anti": lambda h: (True, "FORMAL",
                                      "RightDiagonalBalance.runningXor_periodic_or_antiPeriodic"),
    "CC.no.short.period": _ledger_no_short_period,
    "CC.balance.sqrt": _ledger_balance,
    "CC.balance.sqrt.2": _ledger_balance,
    "CC.lc.half": _ledger_lc,
    "CC.lc.half.2": _ledger_lc,
    "TAX.conserved.at.jumps": lambda h: (True, "FORMAL", "TaxChecks.tax_conserved_at_doubling"),
    "TAX.mechanism.cluster": lambda h: (False, "FORMAL",
                                        "the law is proved from the left step alone: "
                                        "LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even"),
    "TAX.substrate.model.qualified": lambda h: (False, "CERT",
                                                "TaxChecksData.tax_conserved_not_only_white"),
    "TAX.defect.contains.jumps": lambda h: (False, "FORMAL", "TaxChecks.docstring_criterion_wrong"),
}

IMPLICATIONS = {
    "GAP.centre.diagonal.connection": (False, "FORMAL",
                                       "DialogueChecks.transient_read_does_not_imply_aperiodic"),
    "GAP.unbounded.undecidable": (False, "FORMAL",
                                  "NeedsWheel.finite_data_never_forces_infinitely_many"),
}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 3. The escalation gate: read surviving universal claims at larger scales
# ═════════════════════════════════════════════════════════════════════════════════════════════

def _esc_lc(h, eng):
    b = _lc_bound(h)
    if b is None:
        return None
    top = 12000 if eng.quick else 20000
    scales = [3000, 6000, 9000, 12000, top] if not eng.quick else [3000, 4500, 6000, 9000, top]

    def check(n):
        prof = lc_profile(n)
        for i, L in enumerate(prof):
            if abs(2 * L - (i + 1)) > b:
                return False, f"n = {i + 1}: |2·L(n) − n| = {abs(2 * L - (i + 1))} > {b}"
        return True, None
    return f"|2·L(n) − n| ≤ {b} on n ≤ scale", scales, check


def _esc_balance(h, eng):
    c = _sqrt_const(h)
    if c is None:
        return None
    top = 20000 if eng.quick else 100000
    scales = [4000, 8000, 12000, 16000, top] if eng.quick else [4000, 10000, 20000, 50000, top]

    def check(n):
        bits = centre_bits(top)[:n]
        d = 0
        for i, x in enumerate(bits, 1):
            d += 1 if x else -1
            if d * d > c * c * i:
                return False, f"N = {i}: |D(N)| = {abs(d)} > {c}·√N"
        return True, None
    return f"|D(N)| ≤ {c}·√N on N ≤ scale", scales, check


def _seed_ladder():
    w2 = [0b1, 0b11, 0b101]
    w4 = w2 + [s for s in range(0b111, 1 << 4, 2) if s not in w2]
    w5 = w4 + [s for s in range(1 << 4, 1 << 5) if s & 1]
    w6 = w5 + [s for s in range(1 << 5, 1 << 6) if s & 1]
    w7 = w6 + [s for s in range(1 << 6, 1 << 7) if s & 1]
    return [w2, w4, w5, w6, w7]


def _esc_wobble_transport(h, eng):
    N = 5000 if eng.quick else 20000
    ladder = _seed_ladder()
    base = exact_wobble(centre_column(N, seed=1))["max_wobble"]

    def check(seeds):
        distinct = {}
        for s in seeds:
            c = tuple(centre_column(N, seed=s))
            distinct.setdefault(c, s)
            w = exact_wobble(list(c))["max_wobble"]
            if w != base:
                return False, (f"seed {bin(s)}: max D(N)²/N = {w} ≠ {base} (seed 1), N ≤ {N}; "
                               f"{len(distinct)} distinct centre columns among the seeds read")
        return True, None
    scales = [f"{len(x)} seeds (width ≤ {max(x).bit_length()})" for x in ladder]
    seeds_by_label = dict(zip(scales, ladder))
    return (f"wobble maximum equal to seed 1's on N ≤ {N}", scales,
            lambda label: check(seeds_by_label[label]))


def _ldiag_pre(N):
    return ldiag(N)["pre"]


def _esc_preperiod_gt(h, eng):
    top = 5000 if eng.quick else 20000
    scales = [1000, 2000, 3000, 4000, top] if eng.quick else [2000, 5000, 10000, 15000, top]

    def check(n):
        pre = _ldiag_pre(top)
        for D in range(20, n):
            if not pre[D] > D:
                return False, f"D = {D}: preperiod {pre[D]} ≤ D"
        return True, None
    return "preperiod(D) > D for 20 ≤ D < scale", scales, check


def _esc_preperiod_env(h, eng):
    m = re.search(r"(\d+)/(\d+)\s*≤\s*pre\(D\)/D\s*≤\s*(\d+)/(\d+)", h.text)
    if not m:
        return None
    lo = Fraction(int(m.group(1)), int(m.group(2)))
    hi = Fraction(int(m.group(3)), int(m.group(4)))
    top = 5000 if eng.quick else 20000
    scales = [1000, 2000, 3000, 4000, top] if eng.quick else [2000, 5000, 10000, 15000, top]

    def check(n):
        pre = _ldiag_pre(top)
        for D in range(20, n):
            r = Fraction(pre[D], D)
            if not lo <= r <= hi:
                return False, f"D = {D}: pre(D)/D = {r} outside [{lo}, {hi}]"
        return True, None
    return f"{lo} ≤ pre(D)/D ≤ {hi} for 20 ≤ D < scale", scales, check


def _esc_words(h, eng):
    m = re.search(r"first ⌈(\d+)/(\d+)·k·2\^k⌉", h.text)
    if not m:
        return None
    r = Fraction(int(m.group(1)), int(m.group(2)))
    ks = [9, 10, 11, 12, 12] if eng.quick else [9, 10, 11, 12, 13]
    need = -(-r * ks[-1] * 2 ** ks[-1] // 1)
    import math

    def check(k):
        lim = math.ceil(r * k * 2 ** k)
        bits = centre_bits(int(need))[:lim]
        seen, w, full = set(), 0, (1 << k) - 1
        for i, b in enumerate(bits):
            w = ((w << 1) | b) & full
            if i >= k - 1:
                seen.add(w)
        if len(seen) == 1 << k:
            return True, None
        missing = next(x for x in range(1 << k) if x not in seen)
        return False, f"k = {k}: the word {missing:0{k}b} does not occur in the first {lim} bits"
    return f"every word of length k occurs in the first ⌈{r}·k·2^k⌉ bits, k = scale", ks, check


ESCALATIONS = {
    "CC.words.early": _esc_words,
    "CC.lc.half": _esc_lc, "CC.lc.half.2": _esc_lc,
    "CC.balance.sqrt": _esc_balance, "CC.balance.sqrt.2": _esc_balance,
    "WOBBLE.transportable": _esc_wobble_transport,
    "LD.preperiod.gt.D": _esc_preperiod_gt, "LD.preperiod.envelope": _esc_preperiod_env,
}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 4. The recompute gate: re-derive a reported comparison from the data
# ═════════════════════════════════════════════════════════════════════════════════════════════

def _two_bit_gap(bits):
    counts = {}
    for i in range(len(bits) - 1):
        w = (bits[i] << 1) | bits[i + 1]
        counts[w] = counts.get(w, 0) + 1
    return max(counts.values()) - min(counts.values())


def _recompute_uniformity(h, eng):
    n = 60000
    gap_c = _two_bit_gap(list(centre_bits(n)))
    gap_tm = _two_bit_gap([bin(i).count("1") % 2 for i in range(n)])
    truth_word = "more" if gap_c < gap_tm else "less"
    m = re.search(r"centre column is (more|less) uniform", h.text)
    stated = m.group(1) if m else None
    m2 = re.search(r"2-bit uniformity gap = (\d+)", h.text)
    stated_gap = int(m2.group(1)) if m2 else None
    ok = (stated == truth_word) and (stated_gap in (None, gap_c))
    detail = (f"recomputed on {n} bits: centre 2-bit gap = {gap_c}, Thue–Morse 2-bit gap = {gap_tm}; "
              f"a smaller gap is more uniform, so the centre column is {truth_word} uniform than "
              f"Thue–Morse (stated: '{stated}', stated gap {stated_gap})")
    corrected = (f"the centre column's 2-bit block counts on its first {n} bits are {truth_word} "
                 f"uniform than Thue–Morse's: max−min count gap {gap_c} vs {gap_tm} (exact)")
    return ok, detail, corrected


RECOMPUTE = {"APPTEST.uniformity.benchmark": _recompute_uniformity}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 5. Engine v17
# ═════════════════════════════════════════════════════════════════════════════════════════════

class EngineV17(EngineV16):
    """v17: TCT gate cascade after every stage; honest layers; typed fixpoint rollback; arrow."""

    def __init__(self, quick: bool = False, log=print, use_ledger: bool = True):
        super().__init__(quick=quick, log=log)
        self.use_ledger = use_ledger
        self.profiles: dict = {}            # hid -> [LayerProfile]
        self.trajectory: dict = {}          # hid -> [(gate, layer_index, verdict)]
        self.gate_log: list = []            # (stage, hid, gate, old, new, reason)
        self.stage_status: dict = {}        # hid -> status set by the stage (before gates)
        self.gate_status: dict = {}         # hid -> status after the gate cascade
        self.backing: dict = {}             # hid -> backing string for the final status
        self.conflicts: list = []
        self.shape_violations: list = []
        self.corrections: list = []
        self.stage_defects: list = []       # (hid, stage status, reason)
        self.current_stage = "construction"

    # ── helpers ─────────────────────────────────────────────────────────────────────────────
    def _note(self, h, gate, old, new, reason):
        self.gate_log.append({"stage": self.current_stage, "hid": h.hid, "gate": gate,
                              "from": old, "to": new, "reason": reason})
        h.record(f"v17 gate: {gate}", not is_refuted(new), reason)

    def _add_profile(self, h, prof: LayerProfile):
        old = self.profiles.setdefault(h.hid, [])
        if any(p.guard == prof.guard and p.name == prof.name and p.verdicts == prof.verdicts
               for p in old):
            return                          # a re-run of the same read adds nothing
        old.append(prof)
        if not prof.shape_ok():
            self.shape_violations.append((h.hid, prof.summary()))
        for i, v in enumerate(prof.verdicts):
            if v is not None:
                self.trajectory.setdefault(h.hid, []).append((prof.guard, i, v))

    def status_of(self, h) -> str:
        return self.gate_status.get(h.hid, h.status)

    # ── construction-time snap (identity guard, honest layers) ──────────────────────────────
    def new(self, **kw) -> Hypothesis:
        self.counter += 1
        h = Hypothesis(hid=f"H{self.counter:02d}", **kw)
        h._guard_input = None
        parent_hid = kw.get("parent")
        if parent_hid is not None and h.origin in DEPENDENT_ORIGINS:
            parent = next((p for p in self.hyps if p.hid == parent_hid), None)
            if parent is not None and is_refuted(self.status_of(parent)):
                h.status = RETRACTED
                h._guard_reason = f"depends on {parent_hid}, already refuted (inherited at construction)"
                self.rollback_log.append((h.hid, parent_hid, "never-tested"))
                self.hyps.append(h)
                return h
        extractor = GUARD_EXTRACTORS.get(h.family)
        if extractor is not None:
            try:
                gi = extractor(h, self)
            except Exception as e:  # pragma: no cover - extractor bugs are reported, not fatal
                gi = GuardInput()
                self.log(f"  [v17] extractor for {h.family} failed: {e}")
            h._guard_input = gi
            if gi.identity is not None:
                self._identity(h, gi)
        self.hyps.append(h)
        return h

    def _identity(self, h, gi):
        name, claim, truth, domain = gi.identity
        prof = identity_layered(name, claim, truth, domain)
        self.layered_identity_results[h.hid] = {
            "overall_ok": bool(prof.verdict()), "failing_layers": prof.failing(),
            "per_layer": {}, "summary": None}
        self._add_profile(h, prof)
        if prof.verdict() is False:
            h.status = "refuted-by-guard"
            h._guard_reason = (f"identity fails; first failure at "
                               f"{LAYER_NAMES[prof.first_fail()]} ({prof.scales[prof.first_fail()]}), "
                               f"counterexample {prof.witness}")
            h.record("guard: identity (layered, v17)", False, prof.summary())
        else:
            h.record("guard: identity (layered, v17)", True, prof.summary())

    # ── stage-time guard (explained-away / coincidence / exclusivity, honest aggregation) ───
    def guard(self, h: Hypothesis):
        if h.hid in self._guarded_hids:
            return
        self._guarded_hids.add(h.hid)
        gi = getattr(h, "_guard_input", None)
        if gi is None:
            return
        if gi.identity is not None:
            self._identity(h, gi)          # the stage may have overwritten the status
            if is_refuted(h.status):
                self._rollback_closure()
                return
        if is_refuted(h.status):
            return
        if gi.explained_away is not None:
            name, events, feature, premises, domain, *imp = gi.explained_away
            prof = explained_away_layered(name, events, feature, premises, domain,
                                          imp[0] if imp else None)
            self._add_profile(h, prof)
            self.layered_explained_away_results[h.hid] = {
                "explained_layers": prof.passing(), "unexplained_layers": prof.failing(),
                "overall_ok": bool(prof.verdict()), "per_layer": {}}
            if prof.verdict():
                h.novelty = ("consequence of a known law (explained at the largest scale, "
                             f"{prof.scales[prof.read_layers()[-1]]}); not a new mechanism")
            h.record("guard: explained-away (layered, v17)", not prof.verdict(), prof.summary())
            # Coincidence, recounted per layer, on the raw data of this claim.
            raw = self._tax_raw()
            if raw is not None:
                dom, conserved, jumps = raw
                cprof = coincidence_layered(dom, set(conserved), jumps)
                self._add_profile(h, cprof)
                self.layered_coincidence_results[h.hid] = {
                    "significant_layers": cprof.passing(), "overall_ok": bool(cprof.verdict()),
                    "per_layer": {}}
                h.record("guard: coincidence (layered, v17)", True, cprof.summary())
        if h.key == "TAX.substrate.model.qualified" or gi.exclusivity is not None or \
                getattr(gi, "exclusivity_layered", None) is not None:
            ex = self._tax_exclusivity()
            if ex is not None:
                feature_set, claimed = ex
                prof = exclusivity_layered("TAX conserved only at white diagonals", feature_set,
                                           claimed)
                self._add_profile(h, prof)
                self.layered_exclusivity_results[h.hid] = {
                    "holding_layers": prof.passing(), "overall_ok": bool(prof.verdict()),
                    "per_layer": {}}
                if prof.verdict() is False:
                    h.status = "refuted-by-guard"
                    h._guard_reason = f"exclusivity fails as stated; counterexample D = {prof.witness}"
                    h.record("guard: exclusivity (layered, v17)", False, prof.summary())
                    self._rollback_closure()

    def _tax_raw(self):
        big = _big_profile(self)
        if big is None or not hasattr(self, "_tax_defect_at"):
            return None
        N = self._tax_scan_limit
        dom = list(range(2, N))
        conserved = [D for D in dom if not self._tax_defect_at.get(D, False)]
        jumps = [J for J in TAX_JUMPS if J < N]
        return dom, conserved, jumps

    def _tax_exclusivity(self):
        big = _big_profile(self)
        raw = self._tax_raw()
        if raw is None:
            return None
        dom, conserved, _ = raw
        white = {D for D in dom if D < len(big.white) and (big.white[D] or big.white[D - 1])}
        return conserved, white

    # ── the TCT gate cascade ────────────────────────────────────────────────────────────────
    def tct_gate(self, h: Hypothesis):
        """Run the gate cascade on h, from the status its stage gave it.  Returns the new status."""
        st = h.status
        self.stage_status[h.hid] = st
        if st == RETRACTED:
            self.gate_status[h.hid] = st
            return st
        cls = claim_class(h)
        new, backing = st, ""

        # (a) claim-class gate: no-test classes say nothing, whatever the stage said
        if not is_refuted(st) and cls in NO_TEST_CLASSES:
            new, backing = UNTESTED, f"class '{cls}': no executable test was given"
        if not is_refuted(st) and cls == "estimate":
            new, backing = ESTIMATE, "an extrapolation; not checked"
        if not is_refuted(st) and cls == "measurement":
            new, backing = MEASURED, "a reported measurement, not a claim about all cases"
        if not is_refuted(st) and cls == "Pi2":
            new, backing = OPEN, "an 'infinitely many / unbounded' claim: no finite data settles it"

        # (b) recompute gate
        if h.key in RECOMPUTE and not is_refuted(st):
            ok, detail, corrected = RECOMPUTE[h.key](h, self)
            if ok:
                new, backing = VERIFIED, detail
            else:
                new, backing = "refuted-by-recompute", detail
                if h.hid not in {c["parent"] for c in self.corrections}:
                    self.corrections.append({"parent": h.hid, "text": corrected, "detail": detail})

        # (c) implication gate
        if cls == "implication" and not is_refuted(st):
            edge = IMPLICATIONS.get(h.key) if self.use_ledger else None
            if edge is None:
                new, backing = UNCHECKED, "an implication with no checked edge"
            else:
                verdict, kind, name = edge
                new = PROVED if verdict else "refuted-by-ledger"
                backing = f"{kind} {name}"

        # (d0) refutation audit: a stage refutation of a claim we can re-read must be reproduced
        #      by a counterexample; a refutation without one is a stage defect (e.g. v14 counted
        #      "the data ran out before the word appeared" as a refutation of CC.words.early).
        if st == "refuted-heldout" and cls == "Pi1" and h.key in ESCALATIONS:
            spec = ESCALATIONS[h.key](h, self)
            if spec is not None:
                desc, scales, check = spec
                prof = escalation_profile(desc, scales, check)
                self._add_profile(h, prof)
                if prof.verdict() is not False:
                    new = "survives"
                    self.stage_defects.append((h.hid, st, "refutation not reproduced: no "
                                               f"counterexample on scales up to {prof.scales[-1]}"))

        # (d) escalation gate: universal claims that survived their stage
        esc_reached = None
        if cls == "Pi1" and new in ("survives", "law-holds") and h.key in ESCALATIONS and \
                not any(d[0] == h.hid for d in self.stage_defects):
            spec = ESCALATIONS[h.key](h, self)
            if spec is not None:
                desc, scales, check = spec
                prof = escalation_profile(desc, scales, check)
                self._add_profile(h, prof)
                if prof.verdict() is False:
                    new = "refuted-on-escalation"
                    backing = f"escalation: {prof.witness} (scale {prof.scales[prof.first_fail()]})"
                else:
                    esc_reached = prof.scales[-1]
                    new, backing = SURVIVES_TO, f"escalation: survives every scale read, up to {esc_reached}"
        if any(d[0] == h.hid for d in self.stage_defects) and new == "survives":
            d = next(d for d in self.stage_defects if d[0] == h.hid)
            new, backing = SURVIVES_TO, f"stage said {d[1]}, but the {d[2]}"
        if cls == "Pi1" and new in ("survives", "law-holds"):
            new, backing = SURVIVES_TO, f"survives its stage range ({h.status}); a universal claim"
        if cls == "finite" and new in ("survives", "law-holds", "prediction-confirmed"):
            new, backing = SURVIVES_TO, "finite claim; the engine's own range does not cover it all"
        if cls == "mechanism" and not is_refuted(new):
            new, backing = SURVIVES_TO, "a mechanism reading; universal"

        # (e) ledger gate (Lean is authoritative)
        if self.use_ledger and h.key in LEDGER:
            entry = LEDGER[h.key](h)
            if entry is not None:
                verdict, kind = entry[0], entry[1]
                name = entry[2]
                if verdict is True:
                    if is_refuted(new):
                        self.conflicts.append((h.hid, new, f"Lean proves it: {name}"))
                    new, backing = PROVED, f"{kind} {name}"
                elif verdict is False:
                    if new in (PROVED, VERIFIED):
                        self.conflicts.append((h.hid, new, f"Lean refutes it: {name}"))
                    if not is_refuted(new):
                        new = "refuted-by-ledger"
                    backing = (backing + "; " if backing and is_refuted(new) else "") + f"{kind} {name}"
                elif verdict == "open":
                    if not is_refuted(new):
                        new, backing = OPEN, f"{kind} {name}"
                elif verdict == "partial" and new == SURVIVES_TO:
                    backing = backing + f"; {kind} {name}"
        if is_refuted(new) and not backing:
            fails = [e for e in h.evidence if not e.get("ok", True)]
            backing = (getattr(h, "_guard_reason", "") or
                       (f"stage test: {fails[-1]['stage']}: {fails[-1]['detail']}" if fails else st))
        if new != st:
            self._note(h, "cascade", st, new, backing)
        self.gate_status[h.hid] = new
        self.backing[h.hid] = backing or self.backing.get(h.hid, "")
        return new

    # ── typed transitive rollback, as a fixpoint ────────────────────────────────────────────
    def _rollback_closure(self):
        """Retract every hypothesis that depends (transitively) on a refuted one.

        Least fixpoint of: retracted ⊇ {c | c depends on p, p refuted or retracted}.  The order in
        which refutations arrive does not matter (Lean: GateLoop.retracted_union)."""
        changed = True
        by_id = {h.hid: h for h in self.hyps}
        while changed:
            changed = False
            for c in self.hyps:
                if c.parent is None or c.origin not in DEPENDENT_ORIGINS:
                    continue
                p = by_id.get(c.parent)
                if p is None:
                    continue
                ps = self.status_of(p)
                cs = self.status_of(c)
                if (is_refuted(ps) or ps == RETRACTED) and cs != RETRACTED and not is_refuted(cs):
                    if cs == PROVED:
                        self.conflicts.append((c.hid, cs, f"depends on refuted {p.hid}"))
                        continue
                    if not any(r[0] == c.hid for r in self.rollback_log):
                        self.rollback_log.append((c.hid, p.hid, cs))
                    c.record("v17 rollback", False, f"retracted: depends on {p.hid} ({ps})")
                    c.status = RETRACTED
                    self.gate_status[c.hid] = RETRACTED
                    self.backing[c.hid] = f"depends on {p.hid} ({ps})"
                    changed = True

    # v15/v16 call this from inside guards; route it to the fixpoint.
    def _rollback_children(self, h: Hypothesis):
        self._rollback_closure()

    # ── stages, with the gate inside the loop ───────────────────────────────────────────────
    def _stage(self, name: str, fn: Callable):
        self.current_stage = name
        before = {h.hid: h.status for h in self.hyps}
        fn()
        for h in list(self.hyps):
            if h.hid not in before or before[h.hid] != h.status or h.hid not in self.gate_status:
                self.tct_gate(h)
        self._rollback_closure()

    def _guard_tax(self, families):
        for h in list(self.hyps):
            if h.family in families and h.key.startswith("TAX"):
                self.guard(h)

    def run(self):
        T0 = time.time()
        self._stage("left-diagonals", self.run_left_diagonals)
        self._stage("right-diagonals", self.run_right_diagonals)
        self._stage("centre", self.run_centre)
        self._stage("controls", self.run_controls)
        self._stage("seed-memory", self.run_seed_memory)
        self._stage("prediction-chain", self.run_prediction_chain)
        self._stage("applications", self.run_applications)
        self._stage("gap-analysis", self.run_gap_analysis)
        self._stage("application-tests", self.run_application_tests)
        self._stage("tool-generation", self.run_tool_driven_generation)
        self._stage("tax-guards-1", lambda: self._guard_tax(("tax-mechanism", "tool-generated")))
        self._stage("tax-correlation", self.run_tax_period_doubling_correlation)
        self._stage("tax-guards-2", lambda: self._guard_tax(("tax-mechanism", "cross-domain")))
        self._stage("wobble-domain", self.run_wobble_domain)
        self._stage("broken-test", self.run_broken_hypothesis_test)
        self._stage("corrections", self._emit_corrections)
        # final snap: re-gate everything (statuses may have been changed by later stages)
        self.current_stage = "final"
        for h in self.hyps:
            if h.status != self.stage_status.get(h.hid) and self.gate_status.get(h.hid) != h.status:
                self.tct_gate(h)
        self._rollback_closure()
        for h in self.hyps:
            h.status = self.gate_status.get(h.hid, h.status)
        self.tool_dialogue = TrajectoryDialogue(self)
        self.tool_dialogue.run(self.hyps, centre_column(20000 if self.quick else 60000),
                               _big_profile(self) or self.left_dev)
        self.final_guard_pass()
        self.v17_consistency = self.tool_dialogue.check()
        self.credit()
        self.timings["total"] = time.time() - T0
        return self.report()

    def _emit_corrections(self):
        for c in self.corrections:
            if any(getattr(h, "_corrects", None) == c["parent"] for h in self.hyps):
                continue
            h = self.new(family="application-test", origin="recompute", parent=c["parent"],
                         key="APPTEST.uniformity.benchmark.corrected", text=c["text"],
                         lean="-- exact recomputation")
            h._corrects = c["parent"]
            h.status = VERIFIED
            h.record("recompute", True, c["detail"])
            self.backing[h.hid] = "exact recomputation: " + c["detail"]
            CLAIM_CLASS["APPTEST.uniformity.benchmark.corrected"] = "finite"

    # ── report ──────────────────────────────────────────────────────────────────────────────
    def arrow_of(self, h) -> dict:
        tr = self.trajectory.get(h.hid, [])
        if not tr:
            return {"read_layer": None, "direction": "not read"}
        top = max(i for _, i, _ in tr)
        per_guard = {}
        for g, i, v in tr:
            per_guard.setdefault(g, []).append((i, v))
        flips = []
        for g, seq in per_guard.items():
            vs = [v for _, v in seq]
            if len(vs) >= 2 and vs[-1] != vs[-2]:
                flips.append(f"{g} flipped at {LAYER_NAMES[seq[-1][0]]}")
        return {"read_layer": LAYER_NAMES[top], "read_index": top,
                "direction": "; ".join(flips) if flips else "converging"}

    def report(self) -> dict:
        rep = super().report()
        rep["engine"] = "GLM Hypothesis Engine v17 (TCT gate cascade, honest layers, typed rollback)"
        rep["use_ledger"] = self.use_ledger
        rep["layer_profiles"] = {k: [p.as_dict() for p in v] for k, v in self.profiles.items()}
        rep["arrows"] = {h.hid: self.arrow_of(h) for h in self.hyps}
        rep["gate_log"] = self.gate_log
        rep["final"] = [{"id": h.hid, "key": h.key, "class": claim_class(h), "origin": h.origin,
                         "parent": h.parent, "stage_status": self.stage_status.get(h.hid),
                         "status": h.status, "answer": answer_of(h.status),
                         "backing": self.backing.get(h.hid, ""), "statement": h.text}
                        for h in self.hyps]
        rep["conflicts"] = self.conflicts
        rep["shape_violations"] = self.shape_violations
        rep["stage_defects"] = self.stage_defects
        rep["v17_consistency"] = getattr(self, "v17_consistency", None)
        return rep


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 6. The trajectory dialogue: speak only backed claims, each with its backing
# ═════════════════════════════════════════════════════════════════════════════════════════════

class TrajectoryDialogue(CleanDialogue):
    ORDER = [PROVED, VERIFIED, SURVIVES_TO, MEASURED, OPEN, ESTIMATE]
    HEAD = {PROVED: "Proved in Lean", VERIFIED: "Verified exactly (finite claim, whole range)",
            SURVIVES_TO: "Survives every scale read (a universal claim: open beyond that scale)",
            MEASURED: "Measured (not a claim about all cases)",
            OPEN: "Open", ESTIMATE: "Estimates (unchecked extrapolations)"}

    def run(self, hyps, centre_bits, left_prof):
        eng = self.engine
        self.spoken_ids = []
        groups = {}
        for h in hyps:
            groups.setdefault(h.status, []).append(h)
        n_ref = sum(len(v) for k, v in groups.items() if is_refuted(k))
        self.speak(f"I generated {len(hyps)} hypotheses. Backed and spoken: "
                   f"{sum(len(groups.get(s, [])) for s in self.ORDER)}. Refuted: {n_ref}. "
                   f"Retracted (depend on a refuted claim): {len(groups.get(RETRACTED, []))}. "
                   f"Untested: {len(groups.get(UNTESTED, []))}. "
                   f"Unchecked implications: {len(groups.get(UNCHECKED, []))}.")
        self._run_tools(centre_bits, left_prof)
        for s in self.ORDER:
            if not groups.get(s):
                continue
            self.speak(f"{self.HEAD[s]} ({len(groups[s])}):")
            for h in groups[s]:
                self.speak(f"  {h.hid}: {h.text[:140]} — {eng.backing.get(h.hid, '')[:160]}")
                self.spoken_ids.append(h.hid)
        refuted = [h for h in hyps if is_refuted(h.status)]
        if refuted:
            self.speak(f"Not asserted — refuted ({len(refuted)}), with the gate that decided:")
            for h in refuted:
                reason = eng.backing.get(h.hid) or getattr(h, "_guard_reason", "") or h.status
                self.speak(f"  {h.hid} [{h.key}] {h.status}: {reason[:160]}")
        for s, label in ((RETRACTED, "retracted"), (UNTESTED, "untested"),
                         (UNCHECKED, "unchecked implications")):
            if groups.get(s):
                self.speak(f"Not asserted — {label}: " + ", ".join(h.hid for h in groups[s]) + ".")
        arrows = [eng.arrow_of(h) for h in hyps]
        flipped = [h.hid for h, a in zip(hyps, arrows) if "flipped" in a["direction"]]
        self.speak(f"Arrow: {sum(1 for a in arrows if a['read_layer'])} hypotheses were read at "
                   f"layers; the read layer never decreased. Verdict flipped on the last read for "
                   f"{flipped or 'none'}; all others converged.")

    def check(self) -> dict:
        """Consistency: no spoken hypothesis is refuted/retracted/untested; each has a backing."""
        eng = self.engine
        by_id = {h.hid: h for h in eng.hyps}
        bad = [i for i in self.spoken_ids if by_id[i].status not in SPEAKABLE]
        unbacked = [i for i in self.spoken_ids if not eng.backing.get(i)]
        return {"spoken": len(self.spoken_ids), "spoken_not_speakable": bad,
                "spoken_without_backing": unbacked, "ok": not bad}


# ═════════════════════════════════════════════════════════════════════════════════════════════
# 7. Outputs
# ═════════════════════════════════════════════════════════════════════════════════════════════

def write_outputs(rep: dict, out: Path, stem: str):
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}.json").write_text(json.dumps(sanitize(rep), indent=1, ensure_ascii=False))
    lines = [f"# {rep['engine']}", "", f"quick = {rep['quick']}, ledger gate = {rep['use_ledger']}", "",
             "| id | key | class | stage status | final status | arrow | backing |", "|---|---|---|---|---|---|---|"]
    for r in rep["final"]:
        a = rep["arrows"][r["id"]]
        arrow = "—" if a["read_layer"] is None else f"{a['read_layer']} ({a['direction']})"
        lines.append(f"| {r['id']} | `{r['key']}` | {r['class']} | {r['stage_status']} | "
                     f"**{r['status']}** | {arrow} | {str(r['backing'])[:150].replace('|', '/')} |")
    lines += ["", "## Layer profiles", ""]
    for hid, profs in rep["layer_profiles"].items():
        for p in profs:
            lines.append(f"* {hid}: {p['summary']}")
    lines += ["", "## Rollback log", ""] + [f"* {c} ← {p} (was {s})" for c, p, s in rep["rollback_log"]]
    lines += ["", f"Conflicts (gate vs Lean): {rep['conflicts'] or 'none'}",
              f"Layer-shape violations: {rep['shape_violations'] or 'none'}",
              f"Stage refutations not reproduced: {rep.get('stage_defects') or 'none'}",
              f"Dialogue consistency: {rep['v17_consistency']}", "",
              "## Dialogue", ""]
    lines += [f"> {u['text'] if isinstance(u, dict) else u}" for u in rep.get("tool_dialogue", [])]
    (out / f"{stem}.md").write_text("\n".join(lines) + "\n")


def main():
    quick = "--quick" in sys.argv
    use_ledger = "--no-ledger" not in sys.argv
    out = HERE / "out"
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    quiet = "--quiet" in sys.argv
    eng = EngineV17(quick=quick, use_ledger=use_ledger,
                    log=(lambda *a, **k: None) if quiet else print)
    rep = eng.run()
    stem = "engine_v17" + ("_quick" if quick else "") + ("" if use_ledger else "_noledger")
    write_outputs(rep, out, stem)
    from collections import Counter
    print(f"\n{rep['engine']}")
    print("final statuses:", dict(Counter(r["status"] for r in rep["final"])))
    print("conflicts:", rep["conflicts"] or "none", "| shape violations:",
          rep["shape_violations"] or "none")
    print("dialogue consistency:", rep["v17_consistency"])
    print(f"wrote {out / (stem + '.json')} and .md; wall-clock {rep['timings_seconds_wallclock'].get('total', 0):.1f}s")


if __name__ == "__main__":
    main()
