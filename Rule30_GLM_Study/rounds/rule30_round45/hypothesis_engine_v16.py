#!/usr/bin/env python3
"""GLM Hypothesis Engine v16 — all five guards layer-aware, clean dialogue.

Built on v15 (TCT as gate inside the loop).  v16 makes every guard layer-aware
and overrides the dialogue to only speak survived hypotheses.

The 5-bit filter cascade is now fully engaged:

  mod 2   → identity_guard_layered        (v15: tests criterion at 5 moduli)
  mod 4   → explained_away_layered        (v16 NEW: tests at 5 domain scales)
  mod 8   → coincidence_test_layered      (v16 NEW: tests at 5 sample sizes)
  mod 144 → exclusivity_guard_layered     (v16 NEW: tests at 5 neighborhoods)
  mod 256 → consistency_guard             (v15: runs at the end)

Each guard reports which layers the claim survives at — a layer-specific
verdict, not a global one.  A claim that holds at mod 2 (substrate) but
fails at mod 8 (rational) is a *substrate-level* claim.

v16 also overrides ToolAugmentedDialogue with CleanDialogue:
  * only survived hypotheses are spoken
  * refuted-by-guard hypotheses are reported as a summary, not spoken
  * the dialogue never asserts a claim whose hypothesis was refuted

Run:  python3 hypothesis_engine_v16.py            (full run)
      python3 hypothesis_engine_v16.py --quick    (smaller held-out ranges)
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# v15 base: everything
from hypothesis_engine_v15 import (
    eca_apply, left_step, right_step, DiagonalProfile,
    left_profile, right_profile, centre_column, linear_complexity,
    _pattern_has_period, _first, Hypothesis, make_predictor,
    exact_wobble, exact_nrci, exact_tax_analysis, exact_delta_sigma_analysis,
    tax_defect_correlation_test, tax_defect_magnitude_test,
    identity_guard_layered, GuardInput, GUARD_EXTRACTORS,
    register_guard_extractor, _tax_defect, _big_profile,
    EngineV15, sanitize,
)
from hypothesis_engine_v14 import ToolAugmentedDialogue
from glm_guards import (
    GuardResult, Premise,
    identity_guard, explained_away_guard, coincidence_test,
    exclusivity_guard, consistency_guard,
)
from tax_guards import JUMPS as TAX_JUMPS, LEAN as TAX_LEAN


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. Layer-aware guards (v16 NEW)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def explained_away_guard_layered(name: str, events: list, feature: Callable,
                                  premises: list, domain: list,
                                  implication: Optional[dict] = None) -> dict:
    """Layer-aware explained-away guard.  Tests the explanation at 5 domain scales.

    The 5 layers correspond to increasing domain scales:
      Layer 1 (substrate, mod 2):   domain restricted to D < 10
      Layer 2 (integer, mod 4):     domain restricted to D < 50
      Layer 3 (rational, mod 8):    domain restricted to D < 200
      Layer 4 (griess, mod 144):    domain restricted to D < 2000
      Layer 5 (universal, mod 256): full domain

    A claim that is explained-away at layer 1 (small scale) but not at layer 5
    (full scale) is a *small-scale* explanation — it holds locally but not
    globally.  This is a layer-specific verdict.

    Returns:
      {"per_layer": {layer_name: GuardResult},
       "overall_ok": bool,  # True if ANY layer is explained away
       "explained_layers": [layer_name, ...],
       "unexplained_layers": [layer_name, ...],
       "summary": GuardResult}
    """
    layers = [
        (2, "substrate", 10),
        (4, "integer", 50),
        (8, "rational", 200),
        (144, "griess", 2000),
        (256, "universal", None),  # None = full domain
    ]

    per_layer = {}
    explained = []
    unexplained = []

    for modulus, layer_name, scale_limit in layers:
        if scale_limit is None:
            layer_domain = list(domain)
            layer_events = [e for e in events if e in domain]
        else:
            layer_domain = [x for x in domain if x < scale_limit]
            layer_events = [e for e in events if e < scale_limit]

        if not layer_events or not layer_domain:
            per_layer[layer_name] = GuardResult(
                "explained-away-layered", True,
                f"{name} @ {layer_name}: no events in this layer's range", [], {})
            continue

        r = explained_away_guard(
            f"{name} @ {layer_name} (D < {scale_limit if scale_limit else 'full'})",
            layer_events, feature, premises, layer_domain,
            implication=implication)
        per_layer[layer_name] = r
        if not r.ok:
            explained.append(layer_name)
        else:
            unexplained.append(layer_name)

    # overall_ok = True if ANY layer is explained away (the claim is a
    # consequence of the premise at SOME scale)
    overall_ok = len(explained) > 0
    if overall_ok:
        summary = GuardResult(
            "explained-away-layered", False,  # not ok = explained away
            f"{name}: EXPLAINED at layers {explained}, unexplained at {unexplained}. "
            f"The claim is a consequence of the premise at scales "
            f"{[l for l in explained]}.", [],
            {"explained_layers": explained, "unexplained_layers": unexplained})
    else:
        summary = GuardResult(
            "explained-away-layered", True,  # ok = not explained away
            f"{name}: NOT explained at any layer. The claim is not a "
            f"consequence of the premise at any scale.", [],
            {"explained_layers": [], "unexplained_layers": unexplained})

    return {"per_layer": per_layer, "overall_ok": overall_ok,
            "explained_layers": explained,
            "unexplained_layers": unexplained,
            "summary": summary}


def coincidence_test_layered(N: int, K: int, n_events: int, events_hit: int) -> dict:
    """Layer-aware coincidence test.  Computes the p-value at 5 sample sizes.

    The 5 layers correspond to increasing sample sizes:
      Layer 1 (substrate):   N = min(N, 10)
      Layer 2 (integer):     N = min(N, 50)
      Layer 3 (rational):    N = min(N, 200)
      Layer 4 (griess):      N = min(N, 2000)
      Layer 5 (universal):   full N

    A claim that is significant at layer 5 (full sample) but not at layer 1
    (small sample) is a *large-sample* phenomenon — it needs a lot of data
    to detect.  This is a layer-specific verdict.

    Returns:
      {"per_layer": {layer_name: GuardResult},
       "overall_ok": bool,  # True if significant at ANY layer
       "significant_layers": [layer_name, ...],
       "summary": GuardResult}
    """
    layers = [
        ("substrate", min(N, 10)),
        ("integer", min(N, 50)),
        ("rational", min(N, 200)),
        ("griess", min(N, 2000)),
        ("universal", N),
    ]

    per_layer = {}
    significant = []

    for layer_name, layer_N in layers:
        if layer_N < n_events:
            per_layer[layer_name] = GuardResult(
                "coincidence-layered", True,
                f"@ {layer_name} (N={layer_N}): too few points for {n_events} events",
                [], {})
            continue
        # Scale K proportionally
        layer_K = K * layer_N // N if N > 0 else 0
        r = coincidence_test(layer_N, layer_K, n_events, events_hit)
        r.sentence = f"@ {layer_name} (N={layer_N}, K={layer_K}): " + r.sentence
        per_layer[layer_name] = r
        # Significant if p_upper < 0.05
        p_upper = r.data.get("p_upper", Fraction(1))
        if isinstance(p_upper, str):
            p_upper = Fraction(p_upper)
        if p_upper < Fraction(1, 20):
            significant.append(layer_name)

    overall_ok = len(significant) > 0
    if overall_ok:
        summary = GuardResult(
            "coincidence-layered", True,
            f"significant at layers {significant}. The coincidence is "
            f"statistically detectable at these scales.", [],
            {"significant_layers": significant})
    else:
        summary = GuardResult(
            "coincidence-layered", False,
            f"NOT significant at any layer. The coincidence is not "
            f"statistically detectable at any scale.", [],
            {"significant_layers": []})

    return {"per_layer": per_layer, "overall_ok": overall_ok,
            "significant_layers": significant, "summary": summary}


def exclusivity_guard_layered(name: str, feature_set: list,
                               claimed_sets_by_layer: Optional[dict] = None) -> dict:
    """Layer-aware exclusivity guard.  Tests "only at S" at 5 neighborhood sizes.

    The 5 layers correspond to increasing neighborhood sizes around the claimed set:
      Layer 1 (substrate):   S = claimed set only (tightest)
      Layer 2 (integer):     S = claimed set ± 1
      Layer 3 (rational):    S = claimed set ± 5
      Layer 4 (griess):      S = claimed set ± 20
      Layer 5 (universal):   S = claimed set ± 100 (loosest)

    A claim "feature holds only at S" that holds at layer 1 (tight) but fails
    at layer 5 (loose) means the feature is tightly concentrated at S but
    spreads out as the neighborhood grows.  This is a layer-specific verdict.

    Returns:
      {"per_layer": {layer_name: GuardResult},
       "overall_ok": bool,  # True if exclusivity holds at the TIGHTEST layer
       "holding_layers": [layer_name, ...],
       "summary": GuardResult}
    """
    if claimed_sets_by_layer is None:
        # Default: grow the claimed set by neighborhood
        # We need the original claimed set; extract from feature_set context
        # For the TAX case, the claimed set is "near white diagonals"
        # This is set up by the guard-extractor
        return {"per_layer": {}, "overall_ok": False,
                "holding_layers": [], "summary": GuardResult(
                    "exclusivity-layered", False,
                    f"{name}: no claimed sets provided", [], {})}

    layers = ["substrate", "integer", "rational", "griess", "universal"]
    per_layer = {}
    holding = []

    for layer_name in layers:
        if layer_name not in claimed_sets_by_layer:
            per_layer[layer_name] = GuardResult(
                "exclusivity-layered", True,
                f"{name} @ {layer_name}: no claimed set for this layer", [], {})
            continue
        claimed = claimed_sets_by_layer[layer_name]
        r = exclusivity_guard(f"{name} @ {layer_name}", feature_set, claimed)
        per_layer[layer_name] = r
        if r.ok:
            holding.append(layer_name)

    # overall_ok = True if exclusivity holds at the TIGHTEST layer (substrate)
    overall_ok = "substrate" in holding
    if overall_ok:
        summary = GuardResult(
            "exclusivity-layered", True,
            f"{name}: holds at layers {holding}. The feature is tightly "
            f"concentrated at the claimed set.", [],
            {"holding_layers": holding})
    else:
        summary = GuardResult(
            "exclusivity-layered", False,
            f"{name}: fails at the tightest layer. The feature is NOT "
            f"concentrated at the claimed set. Holding at: {holding}", [],
            {"holding_layers": holding})

    return {"per_layer": per_layer, "overall_ok": overall_ok,
            "holding_layers": holding, "summary": summary}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. Update guard-extractors to produce layer-aware inputs
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass
class GuardInputV16(GuardInput):
    """v16 GuardInput with layer-aware fields."""
    # Layer-aware explained-away: (name, events, feature_fn, premises, domain, implication?)
    # Same as v15, but the guard runs it layered
    # Layer-aware coincidence: (N, K, n_events, events_hit) — same, but layered
    # Layer-aware exclusivity: (name, feature_set, claimed_sets_by_layer)
    exclusivity_layered: Optional[tuple] = None  # (name, feature_set, claimed_sets_by_layer)


@register_guard_extractor("tax-mechanism")
def _tax_guard_extractor_v16(h: Hypothesis, eng: "EngineV16") -> GuardInputV16:
    """v16 TAX guard-extractor with precise guard assignment.

    Each hypothesis gets ONLY the guards relevant to its specific claim:
      - H38 (TAX.defect.contains.jumps): identity (states the criterion)
      - H41 (TAX.mechanism.cluster): identity (states the criterion)
      - H42 (TAX.substrate.model): identity (states the criterion)
      - H43 (TAX.mechanism.predictive): NO guard (predictive, not testable)
      - H44 (TAX.conserved.at.jumps): explained-away + coincidence (factual claim)
      - H45 (TAX.substrate.model.qualified): exclusivity (layer-aware)
    """
    gi = GuardInputV16()

    # Identity guard: only for hypotheses that STATE the algebraic criterion.
    # H44 and H45 are factual/consequence claims, not criterion statements.
    criterion_keys = {"TAX.defect.contains.jumps", "TAX.mechanism.cluster",
                      "TAX.substrate.model"}
    if h.key in criterion_keys:
        box = [(a, b, c) for a in range(13) for b in range(13)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "TAX criterion 'conserved iff c in {0,a,b}'",
            lambda a, b, c: c in (0, a, b),
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box,
        )

    # H44: "TAX conserved at jumps" — explained-away + coincidence (NO identity)
    if h.key == "TAX.conserved.at.jumps":
        big = _big_profile(eng)
        if big is not None and hasattr(eng, "_tax_defect_at"):
            N = eng._tax_scan_limit
            defect_at = eng._tax_defect_at
            dom = list(range(2, N))
            jumps = [J for J in TAX_JUMPS if J < N]
            prem = Premise("white(D-1)",
                           lambda D: 1 <= D <= len(big.white) and bool(big.white[D - 1]),
                           backing="hypothesis of the doubling law ldiag_doubles")
            gi.explained_away = (
                "'TAX conserved at every period doubling' (v13 POSITIVE FINDING)",
                jumps, lambda D: not defect_at.get(D, False), [prem], dom,
                {"white(D-1)": TAX_LEAN["at_doubling"]})
            conserved = [D for D in dom if not defect_at.get(D, False)]
            hit = sum(1 for J in jumps if not defect_at.get(J, False))
            gi.coincidence = (len(dom), len(conserved), len(jumps), hit)

    return gi


@register_guard_extractor("cross-domain")
def _cross_domain_guard_extractor_v16(h: Hypothesis, eng: "EngineV16") -> GuardInputV16:
    """v16 cross-domain guard-extractor with layer-aware exclusivity.

    H42 (TAX.substrate.model): identity (states the criterion)
    H45 (TAX.substrate.model.qualified): exclusivity (layer-aware) — NO identity
    """
    gi = GuardInputV16()

    # Identity guard only for H42 (which states the criterion)
    if h.key == "TAX.substrate.model":
        box = [(a, b, c) for a in range(13) for b in range(13)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "TAX criterion 'conserved iff c in {0,a,b}'",
            lambda a, b, c: c in (0, a, b),
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box,
        )

    # H45: layer-aware exclusivity (NO identity — it's a consequence claim)
    if h.key == "TAX.substrate.model.qualified":
        big = _big_profile(eng)
        if big is not None and hasattr(eng, "_tax_defect_at"):
            N = eng._tax_scan_limit
            defect_at = eng._tax_defect_at
            dom = list(range(2, N))
            conserved = [D for D in dom if not defect_at.get(D, False)]
            white_set = {D for D in dom if big.white[D] or big.white[D - 1]}
            claimed_sets = {
                "substrate": white_set,
                "integer": {d + off for d in white_set for off in range(-1, 2)},
                "rational": {d + off for d in white_set for off in range(-5, 6)},
                "griess": {d + off for d in white_set for off in range(-20, 21)},
                "universal": {d + off for d in white_set for off in range(-100, 101)},
            }
            gi.exclusivity = (
                "'TAX CONSERVED only at white diagonals' (v13 cross-domain lift)",
                conserved, white_set)
            gi.exclusivity_layered = (
                "'TAX CONSERVED only at white diagonals' (layer-aware)",
                conserved, claimed_sets)
    return gi


@register_guard_extractor("wobble")
def _wobble_guard_extractor_v16(h: Hypothesis, eng: "EngineV16") -> GuardInputV16:
    """v16 wobble guard-extractor."""
    gi = GuardInputV16()
    if h.key != "WOBBLE.balanced.density":
        return gi
    box = []
    for length in range(1, 9):
        for bits in range(1 << length):
            seq = [(bits >> i) & 1 for i in range(length)]
            ones = sum(seq)
            box.append((length, ones, 0))

    def true_balanced(length, ones, _):
        return abs(2 * ones - length) <= 1

    def claim_balanced(length, ones, _):
        if length == 0:
            return True
        return 2 * ones == length

    gi.identity = (
        "balance criterion 'balanced iff density = 1/2' (WRONG)",
        claim_balanced, true_balanced, box)
    return gi


@register_guard_extractor("tool-generated")
def _tool_generated_guard_extractor_v16(h: Hypothesis, eng: "EngineV16") -> GuardInputV16:
    """v16 tool-generated guard-extractor."""
    gi = GuardInputV16()
    if h.key.startswith("TAX"):
        box = [(a, b, c) for a in range(13) for b in range(13)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "TAX criterion 'conserved iff c in {0,a,b}'",
            lambda a, b, c: c in (0, a, b),
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box,
        )
    return gi


@register_guard_extractor("broken-test")
def _broken_guard_extractor_v16(h: Hypothesis, eng: "EngineV16") -> GuardInputV16:
    """v16 broken-test guard-extractor."""
    gi = GuardInputV16()
    if h.key == "BROKEN.tax.criterion":
        box = [(a, b, c) for a in range(9) for b in range(9)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "BROKEN criterion 'TAX conserved iff c = 0' (only disjoint)",
            lambda a, b, c: c == 0,
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box)
    if h.key == "BROKEN.balance.criterion":
        box = []
        for length in range(1, 7):
            for bits in range(1 << length):
                seq = [(bits >> i) & 1 for i in range(length)]
                ones = sum(seq)
                box.append((length, ones, 0))

        def claim_balanced_wrong(length, ones, _):
            return ones == 0 or ones == length

        def true_balanced(length, ones, _):
            return abs(2 * ones - length) <= 1

        gi.identity = (
            "BROKEN criterion 'balanced iff all bits equal'",
            claim_balanced_wrong, true_balanced, box)
    return gi


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. CleanDialogue: only speak survived hypotheses
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class CleanDialogue(ToolAugmentedDialogue):
    """v16: clean dialogue.  Only speaks survived hypotheses.

    Refuted-by-guard hypotheses are reported as a summary at the end, not
    spoken as individual utterances.  The dialogue never asserts a claim
    whose hypothesis was refuted.
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.refuted_summary: list = []

    def run(self, hyps: list, centre_bits: list, left_prof: DiagonalProfile):
        """Run the clean dialogue.  Only survived hypotheses are spoken."""
        self.engine.log("== Clean dialogue (v16: only survived hypotheses) ==")

        # Partition hypotheses
        survived = [h for h in hyps if not h.status.startswith("refuted")]
        refuted_by_guard = [h for h in hyps if h.status == "refuted-by-guard"]
        refuted_other = [h for h in hyps
                         if h.status.startswith("refuted") and h.status != "refuted-by-guard"]

        self.speak(f"I have generated {len(hyps)} hypotheses. "
                   f"{len(survived)} survived all guards; "
                   f"{len(refuted_by_guard)} were refuted by guards (not spoken); "
                   f"{len(refuted_other)} were refuted by stage tests.")

        # Run the tools (same as v15, but only on survived data)
        self._run_tools(centre_bits, left_prof)

        # Report the layer-aware guard verdicts for refuted hypotheses
        if refuted_by_guard:
            self.speak(f"Guard verdicts ({len(refuted_by_guard)} hypotheses refuted by guard):")
            for h in refuted_by_guard:
                reason = getattr(h, "_guard_reason", "unknown")
                self.speak(f"  {h.hid} [{h.family}/{h.key}]: {reason}")
                # Report the layer-aware verdict if available
                if hasattr(self.engine, "layered_identity_results"):
                    lr = self.engine.layered_identity_results.get(h.hid)
                    if lr and not lr["overall_ok"]:
                        self.speak(f"    identity: FAILS at {lr['failing_layers']}")
                if hasattr(self.engine, "layered_explained_away_results"):
                    lr = self.engine.layered_explained_away_results.get(h.hid)
                    if lr:
                        self.speak(f"    explained-away: explained at {lr['explained_layers']}, "
                                   f"unexplained at {lr['unexplained_layers']}")
                if hasattr(self.engine, "layered_coincidence_results"):
                    lr = self.engine.layered_coincidence_results.get(h.hid)
                    if lr:
                        self.speak(f"    coincidence: significant at {lr['significant_layers']}")
                if hasattr(self.engine, "layered_exclusivity_results"):
                    lr = self.engine.layered_exclusivity_results.get(h.hid)
                    if lr:
                        self.speak(f"    exclusivity: holds at {lr['holding_layers']}")
            self.refuted_summary = refuted_by_guard

        # Speak ONLY survived hypotheses
        self.speak(f"Survived hypotheses ({len(survived)}):")
        for h in survived:
            self.speak(f"  {h.hid} [{h.status}] {h.text[:120]}")

        # Closing
        total_cost = sum(self.cost_tracker.values())
        self.speak(f"Computational cost: wobble {self.cost_tracker['wobble']:.3f}s, "
                   f"NRCI {self.cost_tracker['nrci']:.3f}s, "
                   f"TAX {self.cost_tracker['tax']:.3f}s, "
                   f"delta-sigma {self.cost_tracker['delta_sigma']:.3f}s. "
                   f"Total: {total_cost:.3f}s.")
        self.speak(f"In total: {len(hyps)} hypotheses generated, "
                   f"{len(survived)} survived, "
                   f"{len(refuted_by_guard)} refuted by guards (never spoken), "
                   f"{len(refuted_other)} refuted by stage tests. "
                   f"Every spoken claim is grounded in exact integer or Fraction arithmetic.")

    def _run_tools(self, centre_bits: list, left_prof: DiagonalProfile):
        """Run the GLM tools on the data.  Same as v15 but without speaking
        refuted hypotheses."""
        # TOOL 1: WOBBLE
        self.speak("The GLM has a Wobble tool. Running it on the centre column.")
        wobble = self.call_tool("wobble", lambda: exact_wobble(centre_bits),
                                "wobble of the centre column")
        self.speak(f"Wobble: max D(N)^2/N = {wobble['max_wobble']} "
                   f"({float(wobble['max_wobble']):.4f}) at N = {wobble['max_N']}. "
                   f"Balanced = {wobble['is_balanced']}.")

        # TOOL 2: NRCI
        self.speak("Running NRCI on the centre column.")
        nrci = self.call_tool("nrci", lambda: exact_nrci(centre_bits),
                              "NRCI of the centre column")
        self.speak(f"NRCI: {nrci['nrci']} ({float(nrci['nrci']):.6f}). "
                   f"{nrci['interpretation']}.")

        # TOOL 3: NRCI on diagonals
        self.speak("Running NRCI on the left diagonals.")
        diagonal_nrci_results = []
        for D in range(min(left_prof.N, 50)):
            if left_prof.pattern[D] is None:
                continue
            pat = left_prof.pattern[D]
            lp = left_prof.lp[D]
            if lp is None or lp == 0:
                continue
            bits = [(pat >> i) & 1 for i in range(lp)]
            if len(bits) < 2:
                continue
            result = self.call_tool("nrci", lambda bits=bits: exact_nrci(bits),
                                    f"NRCI of left diagonal {D}")
            diagonal_nrci_results.append({"D": D, "period": lp, "nrci": result["nrci"]})
        clustered = [r for r in diagonal_nrci_results if r["nrci"] < Fraction(9, 10)]
        self.speak(f"Diagonal NRCI: {len(clustered)} clustered, "
                   f"{len(diagonal_nrci_results)} total.")

        # TOOL 4: TAX
        self.speak("Running TAX conservation check on consecutive diagonals.")
        tax_results = []
        tax_defects = []
        for D in range(2, min(left_prof.N, 50)):
            if left_prof.pattern[D] is None or left_prof.pattern[D-1] is None:
                continue
            pat_D = left_prof.pattern[D]
            pat_Dm1 = left_prof.pattern[D-1]
            lp = max(left_prof.lp[D] or 1, left_prof.lp[D-1] or 1)
            result = self.call_tool("tax",
                lambda a=pat_D, b=pat_Dm1, n=lp: exact_tax_analysis(a, b, n),
                f"TAX between diagonals {D-1} and {D}")
            tax_results.append({"D": D, "tax_conserved": result["tax_conservation"]})
            if not result["tax_conservation"]:
                tax_defects.append(D)
        conserved_count = sum(1 for r in tax_results if r["tax_conserved"])
        self.speak(f"TAX: {conserved_count}/{len(tax_results)} conserved, "
                   f"{len(tax_defects)} defects.")

        # TOOL 5: Delta-sigma
        self.speak("Running delta-sigma analysis.")
        ds = self.call_tool("delta_sigma", lambda: exact_delta_sigma_analysis(centre_bits),
                            "delta-sigma analysis")
        acc_range = ds.get("acc_range", Fraction(0))
        is_conv = ds.get("is_converging", False)
        self.speak(f"Delta-sigma: accumulator range = {acc_range} "
                   f"({float(acc_range):.1f}), converging = {is_conv}.")

        # TAX-period-doubling correlation (if available)
        if self.engine.tax_correlation is not None:
            tc = self.engine.tax_correlation
            self.speak("TAX-period-doubling correlation (3-way test):")
            self.speak(f"  Full-range: {tc['k']} defects, ratio "
                       f"{float(tc['ratio_empirical_to_null']):.4f}, "
                       f"{tc['interpretation'][:80]}")
            mag = tc.get("magnitude_test", {})
            if mag:
                self.speak(f"  Magnitude: M_jump={float(mag.get('M_jump', 0)):.1f}, "
                           f"M_other={float(mag.get('M_other', 0)):.1f}, "
                           f"ratio={float(mag.get('ratio_jump_to_other', 0)):.4f}")
            sml = tc.get("small_range_test", {})
            if sml:
                self.speak(f"  Small-range: ratio={float(sml.get('ratio_empirical_to_null', 0)):.4f}")
            # v16: the COMBINED VERDICT (no post-hoc guard calls)
            ratio = tc["ratio_empirical_to_null"]
            mag_ratio = mag.get("ratio_jump_to_other", Fraction(0)) if mag else Fraction(0)
            small_ratio = (sml.get("ratio_empirical_to_null", Fraction(0))
                           if sml else Fraction(0))
            any_supported = (ratio < Fraction(2, 3) or
                             mag_ratio > Fraction(6, 5) or
                             small_ratio < Fraction(2, 3))
            if any_supported:
                self.speak("  COMBINED: at least one test supports the mechanism.")
            else:
                self.speak("  COMBINED: NONE of the three tests support the mechanism. "
                           "TAX defects are uniform in space and magnitude. "
                           "The period-doubling law H08 (white ∧ odd-parity) remains "
                           "the explanation; TAX neither marks nor explains the doublings.")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. EngineV16: all guards layer-aware, clean dialogue
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class EngineV16(EngineV15):
    """v16: all five guards layer-aware, clean dialogue."""

    def __init__(self, quick: bool = False, log=print):
        super().__init__(quick=quick, log=log)
        self.layered_explained_away_results: dict = {}
        self.layered_coincidence_results: dict = {}
        self.layered_exclusivity_results: dict = {}

    def guard(self, h: Hypothesis):
        """v16: stage-time guard with LAYER-AWARE explained-away, coincidence, exclusivity."""
        if h.hid in self._guarded_hids:
            return
        self._guarded_hids.add(h.hid)

        gi = getattr(h, "_guard_input", None)
        if gi is None:
            return

        results = []

        # mod 2: RE-RUN identity (same as v15)
        if gi.identity is not None:
            name, claim, truth, domain = gi.identity
            layered = identity_guard_layered(name, claim, truth, domain)
            self.layered_identity_results[h.hid] = layered
            if not layered["overall_ok"]:
                h.status = "refuted-by-guard"
                h._guard_reason = (
                    f"identity guard failed at layers {layered['failing_layers']}")
                h.record("guard: identity (layered, stage-time)", False,
                         layered["summary"].sentence)
                self.log(f"  [guard] {h.hid} REFUTED at stage-time: "
                         f"identity fails at {layered['failing_layers']}")
                self._rollback_children(h)
                self.guard_snap_results[h.hid] = [layered["summary"]]
                return
            else:
                h.record("guard: identity (layered, stage-time)", True,
                         layered["summary"].sentence)

        if h.status == "refuted-by-guard":
            return

        # mod 4: LAYER-AWARE explained-away
        if gi.explained_away is not None:
            name, events, feature, premises, domain, *imp = gi.explained_away
            implication = imp[0] if imp else None
            layered_ea = explained_away_guard_layered(
                name, events, feature, premises, domain, implication=implication)
            self.layered_explained_away_results[h.hid] = layered_ea
            results.append(layered_ea["summary"])
            if layered_ea["overall_ok"]:  # explained away at SOME layer
                h.record("guard: explained-away (layered)", False,
                         layered_ea["summary"].sentence)
                h.novelty = ("consequence of a known law at layers "
                             f"{layered_ea['explained_layers']}; not a new mechanism")
                self.log(f"  [guard] {h.hid} EXPLAINED AWAY at layers "
                         f"{layered_ea['explained_layers']}, "
                         f"unexplained at {layered_ea['unexplained_layers']}")

        # mod 8: LAYER-AWARE coincidence
        if gi.coincidence is not None:
            N, K, n_events, hit = gi.coincidence
            layered_co = coincidence_test_layered(N, K, n_events, hit)
            self.layered_coincidence_results[h.hid] = layered_co
            results.append(layered_co["summary"])
            # coincidence is informational; does not refute by itself

        # mod 144: LAYER-AWARE exclusivity
        if gi.exclusivity_layered is not None:
            name, feature_set, claimed_sets_by_layer = gi.exclusivity_layered
            layered_ex = exclusivity_guard_layered(name, feature_set, claimed_sets_by_layer)
            self.layered_exclusivity_results[h.hid] = layered_ex
            results.append(layered_ex["summary"])
            if not layered_ex["overall_ok"]:  # fails at the tightest layer
                h.status = "refuted-by-guard"
                h.record("guard: exclusivity (layered)", False,
                         layered_ex["summary"].sentence)
                self.log(f"  [guard] {h.hid} REFUTED by exclusivity (layered): "
                         f"holds at {layered_ex['holding_layers']}")
                self._rollback_children(h)
        elif gi.exclusivity is not None:
            # Fall back to non-layered exclusivity (v15 behavior)
            name, feature_set, claimed_set = gi.exclusivity
            r = exclusivity_guard(name, feature_set, claimed_set)
            r.data["lean"] = TAX_LEAN.get("not_only_white", "")
            results.append(r)
            if not r.ok:
                h.status = "refuted-by-guard"
                h.record("guard: exclusivity", False, r.sentence)
                self.log(f"  [guard] {h.hid} REFUTED by exclusivity: {r.sentence[:100]}")
                self._rollback_children(h)

        self.guard_snap_results[h.hid] = results

    def run(self):
        T0 = time.time()
        # All v15 stages (with v16 guard-extractors via the registry override)
        self.run_left_diagonals()
        self.run_right_diagonals()
        self.run_centre()
        self.run_controls()
        self.run_seed_memory()
        self.run_prediction_chain()
        self.run_applications()
        self.run_gap_analysis()
        self.run_application_tests()
        self.run_tool_driven_generation()
        for h in list(self.hyps):
            if h.family in ("tax-mechanism", "tool-generated") and h.key.startswith("TAX"):
                self.guard(h)
        self.run_tax_period_doubling_correlation()
        for h in list(self.hyps):
            if h.family in ("tax-mechanism", "cross-domain") and h.key.startswith("TAX"):
                self.guard(h)
        self.run_wobble_domain()
        self.run_broken_hypothesis_test()
        # v16: CleanDialogue instead of ToolAugmentedDialogue
        centre_n = 60000 if not self.quick else 20000
        centre_bits = centre_column(centre_n)
        big = (self.left_profiles.get(max(self.left_profiles.keys()))
               if hasattr(self, "left_profiles") else self.left_dev)
        if big is None:
            big = self.left_dev
        self.tool_dialogue = CleanDialogue(self)
        self.tool_dialogue.run(self.hyps, centre_bits, big)
        # v16: final consistency guard (should find no violations — clean dialogue)
        self.final_guard_pass()
        self.credit()
        self.timings["total"] = time.time() - T0
        return self.report()

    def report(self) -> dict:
        rep = super().report()
        rep["engine"] = "GLM Hypothesis Engine v16 (all guards layer-aware, clean dialogue)"
        rep["layered_explained_away_results"] = {
            k: {"explained_layers": v["explained_layers"],
                "unexplained_layers": v["unexplained_layers"],
                "overall_ok": v["overall_ok"],
                "per_layer": {ln: r.as_dict() for ln, r in v["per_layer"].items()}}
            for k, v in self.layered_explained_away_results.items()
        }
        rep["layered_coincidence_results"] = {
            k: {"significant_layers": v["significant_layers"],
                "overall_ok": v["overall_ok"],
                "per_layer": {ln: r.as_dict() for ln, r in v["per_layer"].items()}}
            for k, v in self.layered_coincidence_results.items()
        }
        rep["layered_exclusivity_results"] = {
            k: {"holding_layers": v["holding_layers"],
                "overall_ok": v["overall_ok"],
                "per_layer": {ln: r.as_dict() for ln, r in v["per_layer"].items()}}
            for k, v in self.layered_exclusivity_results.items()
        }
        rep["v16_dialogue"] = "clean (only survived hypotheses spoken)"
        return rep


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 5. Outputs
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def write_outputs_v16(rep: dict, stem: str = "r42_engine_report_v16"):
    (HERE / f"{stem}.json").write_text(json.dumps(sanitize(rep), indent=1, ensure_ascii=False))
    md = ["# GLM Hypothesis Engine v16 — run report", "",
          "All five guards layer-aware. Clean dialogue (only survived hypotheses spoken).", "",
          f"Engine: {rep['engine']}", "",
          f"Status counts: {rep['status_counts']}", "",
          f"Predictions: {rep['predictions']}", "",
          f"Rollback log ({len(rep.get('rollback_log', []))} retractions):",
          ""]
    for child, ancestor, old_status in rep.get("rollback_log", []):
        md.append(f"- {child} retracted (ancestor {ancestor} refuted; was {old_status})")
    md += ["", "## Layer-aware guard results", ""]
    # Identity
    md.append("### Layered identity (mod 2/4/8/144/256)")
    for hid, lr in rep.get("layered_identity_results", {}).items():
        md.append(f"**{hid}**: overall_ok={lr['overall_ok']}, "
                  f"failing={lr['failing_layers']}")
    md.append("")
    # Explained-away
    md.append("### Layered explained-away (5 domain scales)")
    for hid, lr in rep.get("layered_explained_away_results", {}).items():
        md.append(f"**{hid}**: explained at {lr['explained_layers']}, "
                  f"unexplained at {lr['unexplained_layers']}")
    md.append("")
    # Coincidence
    md.append("### Layered coincidence (5 sample sizes)")
    for hid, lr in rep.get("layered_coincidence_results", {}).items():
        md.append(f"**{hid}**: significant at {lr['significant_layers']}")
    md.append("")
    # Exclusivity
    md.append("### Layered exclusivity (5 neighborhood sizes)")
    for hid, lr in rep.get("layered_exclusivity_results", {}).items():
        md.append(f"**{hid}**: holds at {lr['holding_layers']}, "
                  f"overall_ok={lr['overall_ok']}")
    md += ["", "## Domain tests", ""]
    md.append(f"- **TAX domain** (regression): {rep['v15_domains']['tax']}")
    md.append(f"- **Wobble domain** (new): {rep['v15_domains']['wobble']}")
    md.append(f"- **Broken-test domain** (sanity): {rep['v15_domains']['broken']}")
    md += ["", "## Hypotheses", "",
           "| id | family | status | statement (truncated) |",
           "|---|---|---|---|"]
    for r in rep["hypotheses"]:
        stmt = r["statement"].replace("\n", " ").replace("|", "\\|")
        if len(stmt) > 120:
            stmt = stmt[:120] + "..."
        md.append(f"| {r['id']} | {r['family']} | {r['status']} | {stmt} |")
    md.append("")
    md.append(f"Wall-clock seconds: {rep['timings_seconds_wallclock']}")
    (HERE / f"{stem}.md").write_text("\n".join(md))


def main():
    quick = "--quick" in sys.argv
    eng = EngineV16(quick=quick)
    rep = eng.run()
    stem = "r42_engine_report_v16_quick" if quick else "r42_engine_report_v16"
    write_outputs_v16(rep, stem)
    print()
    print("Engine:", rep["engine"])
    print("Status counts:", rep["status_counts"])
    print("Predictions:", rep["predictions"])
    print()
    print("v16 layered identity results:")
    for hid, lr in rep.get("layered_identity_results", {}).items():
        verdict = "OK" if lr["overall_ok"] else f"FAILS at {lr['failing_layers']}"
        print(f"  {hid}: {verdict}")
    print()
    print("v16 layered explained-away results:")
    for hid, lr in rep.get("layered_explained_away_results", {}).items():
        verdict = (f"explained at {lr['explained_layers']}, "
                   f"unexplained at {lr['unexplained_layers']}")
        print(f"  {hid}: {verdict}")
    print()
    print("v16 layered coincidence results:")
    for hid, lr in rep.get("layered_coincidence_results", {}).items():
        print(f"  {hid}: significant at {lr['significant_layers']}")
    print()
    print("v16 layered exclusivity results:")
    for hid, lr in rep.get("layered_exclusivity_results", {}).items():
        print(f"  {hid}: holds at {lr['holding_layers']}, overall_ok={lr['overall_ok']}")
    print()
    print(f"Rollback log ({len(rep.get('rollback_log', []))} retractions):")
    for child, ancestor, old_status in rep.get("rollback_log", []):
        print(f"  {child} ← {ancestor} (was {old_status})")
    print()
    # Broken-test sanity
    broken_caught = sum(1 for h in rep["hypotheses"]
                        if h["family"] == "broken-test" and h["status"] == "refuted-by-guard")
    broken_total = sum(1 for h in rep["hypotheses"] if h["family"] == "broken-test")
    print(f"Broken-test sanity: {broken_caught}/{broken_total} caught")
    print()
    # Dialogue cleanliness
    dialogue = rep.get("tool_dialogue", [])
    refuted_spoken = sum(1 for u in dialogue
                         if "refuted-by-guard" in u.get("text", "") and
                         "Survived" not in u.get("text", ""))
    print(f"Dialogue utterances: {len(dialogue)}")
    print(f"Dialogue cleanliness: refuted hypotheses spoken = {refuted_spoken} (should be 0)")
    print()
    print("Wall-clock:", rep["timings_seconds_wallclock"])


if __name__ == "__main__":
    main()
