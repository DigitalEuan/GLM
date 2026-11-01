#!/usr/bin/env python3
"""GLM Hypothesis Engine v15 — TCT as gate inside the loop.

Built on v14 (which adds reasoning guards post-hoc).  v15 moves the guards
INSIDE the construction: every hypothesis is guarded at construction time
(the identity guard, layered across mod 2/4/8/144/256), and guarded again
after its stage-specific test (the explained-away, coincidence, and
exclusivity guards).  The consistency guard runs at the end, with
transitive rollback.

The architecture maps onto the Master GLM Operator Equation:

  Master Equation              v15
  ─────────────                ───
  new()                        self.new()  ── runs identity_guard_layered
                                  (the construction-time snap)
  stage tests h                stage tests h
  self.guard(h)                ── runs explained_away, coincidence, exclusivity
                                  (the stage-time snap)
  ...all stages complete...
  final consistency pass       ── runs consistency_guard with transitive rollback
                                  (the final snap)

The 5 guards map onto the 5-bit filter cascade:
  mod 2   → identity (does the claim match the truth?)
  mod 4   → explained-away (is the claim a consequence of a known law?)
  mod 8   → coincidence (is the statistical significance real?)
  mod 144 → exclusivity (does "only at S" hold?)
  mod 256 → consistency (do all utterances match final statuses?)

Three test domains:
  1. TAX/period-doubling (regression — should reproduce v14's findings
     but with transitive rollback)
  2. Wobble/balance (new — tests the identity guard on a different
     algebraic criterion)
  3. Deliberately-broken hypotheses (sanity check — verifies the guards
     fire when they should)

Run:  python3 hypothesis_engine_v15.py            (full run)
      python3 hypothesis_engine_v15.py --quick    (smaller held-out ranges)
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

# v14 base: observatory, tools, engine stages, dialogue
from hypothesis_engine_v14 import (
    eca_apply, left_step, right_step, DiagonalProfile,
    left_profile, right_profile, centre_column, linear_complexity,
    _pattern_has_period, _first, Hypothesis, make_predictor,
    exact_wobble, exact_nrci, exact_tax_analysis, exact_delta_sigma_analysis,
    tax_defect_correlation_test, tax_defect_magnitude_test,
    ToolAugmentedDialogue, sanitize,
)
from hypothesis_engine_v14 import Engine as EngineV14

# v14 guards: the 5-guard cascade
from glm_guards import (
    GuardResult, Premise,
    identity_guard, explained_away_guard, coincidence_test,
    exclusivity_guard, consistency_guard,
)

# v14 TAX-specific guard wiring (restructured for inside-the-loop use)
from tax_guards import JUMPS as TAX_JUMPS, LEAN as TAX_LEAN


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The layer-aware identity guard  (v15's key new guard)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def identity_guard_layered(name: str, claim: Callable, truth: Callable,
                           domain: list, layers: Optional[list] = None) -> dict:
    """Test `claim(x) == truth(x)` at each layer's modulus.

    The Master Equation's 5-bit filters classify the input by its deep-hole type
    at mod 2, 4, 8, 144, 256.  The layered identity guard does the same for an
    algebraic criterion: it tests the claim at each modulus and reports which
    layers the claim survives at.

    A criterion that holds at mod 2 (substrate) but fails at mod 8 (rational)
    is a *substrate-level* criterion — it is correct in the coarse view but
    wrong in the fine view.  This is a much more nuanced verdict than "wrong".

    Returns:
      {"per_layer": {layer_name: GuardResult},
       "overall_ok": bool,
       "failing_layers": [layer_name, ...],
       "summary": GuardResult}
    """
    if layers is None:
        layers = [(2, "substrate"), (4, "integer"), (8, "rational"),
                  (144, "griess"), (256, "universal")]

    per_layer = {}
    for modulus, layer_name in layers:
        # Project the domain onto the modulus: reduce each tuple mod m.
        # This is the "what does this layer see?" operation.
        seen = set()
        layered_domain = []
        for case in domain:
            layered_case = tuple(x % modulus for x in case)
            if layered_case not in seen:
                seen.add(layered_case)
                layered_domain.append(layered_case)
        r = identity_guard(f"{name} @ {layer_name} (mod {modulus})",
                           claim, truth, layered_domain)
        per_layer[layer_name] = r

    failing = [ln for ln, r in per_layer.items() if not r.ok]
    overall_ok = not failing
    if overall_ok:
        summary = GuardResult("identity-layered", True,
                              f"{name}: holds at ALL 5 layers (mod 2/4/8/144/256).",
                              [], {"failing_layers": []})
    else:
        summary = GuardResult("identity-layered", False,
                              f"{name}: FAILS at layers {failing}. "
                              f"The criterion is correct at some layers but wrong at others — "
                              f"a layer-specific verdict, not a global one.",
                              [], {"failing_layers": failing})
    return {"per_layer": per_layer, "overall_ok": overall_ok,
            "failing_layers": failing, "summary": summary}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. GuardInput: what a guard-extractor returns for one hypothesis
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass
class GuardInput:
    """Inputs for the 5-guard cascade, specific to one hypothesis.

    Each field is Optional; a hypothesis may only populate the fields relevant
    to its claim.  The guard-snap runs only the guards whose input is present.
    """
    # mod 2: identity (layered) — (name, claim_fn, truth_fn, domain)
    identity: Optional[tuple] = None
    # mod 4: explained-away — (name, events, feature_fn, premises, domain, implication?)
    explained_away: Optional[tuple] = None
    # mod 8: coincidence — (N, K, n_events, events_hit)
    coincidence: Optional[tuple] = None
    # mod 144: exclusivity — (name, feature_set, claimed_set)
    exclusivity: Optional[tuple] = None
    # mod 256: consistency is always run on the full utterance stream


# Guard-extractor registry: family → extractor_fn(hypothesis, engine) → GuardInput
GUARD_EXTRACTORS: dict = {}


def register_guard_extractor(family: str):
    """Decorator: register a guard-extractor for a hypothesis family."""
    def deco(fn):
        GUARD_EXTRACTORS[family] = fn
        return fn
    return deco


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. Guard-extractors for each domain
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _tax_defect(a, b, c):
    return a * a + b * b - 2 * c * c - (a + b - 2 * c) ** 2


@register_guard_extractor("tax-mechanism")
def _tax_guard_extractor(h: Hypothesis, eng: "EngineV15") -> GuardInput:
    """Guard-extractor for the TAX-mechanism family.

    For each TAX hypothesis, produce the guard inputs that test its specific
    claim.  The identity guard tests the TAX criterion — the foundation of
    ALL TAX hypotheses.  If the criterion is wrong (it is: v14 found 276
    counterexamples), every hypothesis that uses the TAX tool is tainted.
    The explained-away guard checks if "TAX conserved at jumps" is forced by
    white(D-1); the exclusivity guard checks if "TAX conserved only at white
    diagonals" holds.
    """
    gi = GuardInput()

    # The TAX criterion is the foundation of every TAX hypothesis.  Test it
    # for every hypothesis in this family — if the criterion is wrong, the
    # hypothesis is tainted at construction.
    box = [(a, b, c) for a in range(13) for b in range(13)
           for c in range(min(a, b) + 1)]
    gi.identity = (
        "TAX criterion 'conserved iff c in {0,a,b}'",
        lambda a, b, c: c in (0, a, b),
        lambda a, b, c: _tax_defect(a, b, c) == 0,
        box,
    )

    # Hypothesis-specific guards
    if h.key == "TAX.conserved.at.jumps":
        # Explained-away: is "TAX conserved at every jump" forced by white(D-1)?
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
                jumps,
                lambda D: not defect_at.get(D, False),
                [prem], dom,
                {"white(D-1)": TAX_LEAN["at_doubling"]},
            )
            # Also the coincidence test: how surprising is "all 4 jumps have defect 0"?
            conserved = [D for D in dom if not defect_at.get(D, False)]
            hit = sum(1 for J in jumps if not defect_at.get(J, False))
            gi.coincidence = (len(dom), len(conserved), len(jumps), hit)

    if h.key == "TAX.substrate.model.qualified":
        # Exclusivity: "TAX conserved ONLY at the white diagonals"
        big = _big_profile(eng)
        if big is not None and hasattr(eng, "_tax_defect_at"):
            N = eng._tax_scan_limit
            defect_at = eng._tax_defect_at
            dom = list(range(2, N))
            conserved = [D for D in dom if not defect_at.get(D, False)]
            near_white = [D for D in dom if big.white[D] or big.white[D - 1]]
            gi.exclusivity = (
                "'TAX CONSERVED only at white diagonals' (v13 cross-domain lift)",
                conserved, near_white,
            )

    return gi


@register_guard_extractor("wobble")
def _wobble_guard_extractor(h: Hypothesis, eng: "EngineV15") -> GuardInput:
    """Guard-extractor for the wobble/balance family.

    For each wobble hypothesis, produce the guard inputs that test the
    balance criterion.  The identity guard tests "balanced iff density = 1/2"
    (a WRONG criterion) vs the true definition "balanced iff |D(N)| <= 1 for
    every prefix".  But ONLY for hypotheses that actually state the balance
    criterion — the transport and Sturmian hypotheses do not state it.
    """
    gi = GuardInput()

    # Only apply the identity guard to the hypothesis that explicitly states
    # the (wrong) balance criterion.
    if h.key != "WOBBLE.balanced.density":
        return gi

    # The Sturmian criterion: a binary sequence is balanced iff
    # |#ones - #zeros| <= 1 for every prefix.  (This is the true definition.)
    # A common wrong criterion: "balanced iff density = 1/2".
    # Test on small binary sequences (lengths 1-8).
    box = []
    for length in range(1, 9):
        for bits in range(1 << length):
            seq = [(bits >> i) & 1 for i in range(length)]
            ones = sum(seq)
            box.append((length, ones, 0))  # (length, ones, ignored)

    def true_balanced(length, ones, _):
        # |2*ones - length| <= 1 for every prefix — but here we only have
        # the full sequence, so test the final prefix.
        return abs(2 * ones - length) <= 1

    def claim_balanced(length, ones, _):
        # Wrong criterion: "density = 1/2"
        if length == 0:
            return True
        return 2 * ones == length

    gi.identity = (
        "balance criterion 'balanced iff density = 1/2' (WRONG)",
        claim_balanced, true_balanced, box,
    )

    return gi


@register_guard_extractor("cross-domain")
def _cross_domain_guard_extractor(h: Hypothesis, eng: "EngineV15") -> GuardInput:
    """Guard-extractor for the cross-domain family (TAX substrate model).

    These hypotheses depend on the TAX tool's criterion, so the identity
    guard tests the TAX criterion for them too.
    """
    gi = GuardInput()
    if h.key.startswith("TAX"):
        box = [(a, b, c) for a in range(13) for b in range(13)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "TAX criterion 'conserved iff c in {0,a,b}'",
            lambda a, b, c: c in (0, a, b),
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box,
        )
    # Exclusivity for the "TAX conserved only at white diagonals" claim
    if h.key == "TAX.substrate.model.qualified":
        big = _big_profile(eng)
        if big is not None and hasattr(eng, "_tax_defect_at"):
            N = eng._tax_scan_limit
            defect_at = eng._tax_defect_at
            dom = list(range(2, N))
            conserved = [D for D in dom if not defect_at.get(D, False)]
            near_white = [D for D in dom if big.white[D] or big.white[D - 1]]
            gi.exclusivity = (
                "'TAX CONSERVED only at white diagonals' (v13 cross-domain lift)",
                conserved, near_white,
            )
    return gi


@register_guard_extractor("tool-generated")
def _tool_generated_guard_extractor(h: Hypothesis, eng: "EngineV15") -> GuardInput:
    """Guard-extractor for the tool-generated family.

    Only applies to TAX-related tool-generated hypotheses (TAX.defect.contains.jumps).
    Other tool-generated hypotheses (NRCI, WOBBLE, DS) do not use the TAX criterion.
    """
    gi = GuardInput()
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
def _broken_guard_extractor(h: Hypothesis, eng: "EngineV15") -> GuardInput:
    """Guard-extractor for the deliberately-broken test family.

    This family exists to verify the guards fire.  Each hypothesis has a
    deliberately wrong criterion; the identity guard should catch it.
    """
    gi = GuardInput()

    if h.key == "BROKEN.tax.criterion":
        # Wrong criterion: "TAX conserved iff c = 0" (only disjoint patterns)
        # The true criterion is defect == 0, which holds for many c > 0 cases.
        box = [(a, b, c) for a in range(9) for b in range(9)
               for c in range(min(a, b) + 1)]
        gi.identity = (
            "BROKEN criterion 'TAX conserved iff c = 0' (only disjoint)",
            lambda a, b, c: c == 0,
            lambda a, b, c: _tax_defect(a, b, c) == 0,
            box,
        )

    if h.key == "BROKEN.balance.criterion":
        # Wrong criterion: "balanced iff all bits are equal"
        box = []
        for length in range(1, 7):
            for bits in range(1 << length):
                seq = [(bits >> i) & 1 for i in range(length)]
                ones = sum(seq)
                box.append((length, ones, 0))

        def claim_balanced_wrong(length, ones, _):
            # "all bits equal" means ones = 0 or ones = length
            return ones == 0 or ones == length

        def true_balanced(length, ones, _):
            return abs(2 * ones - length) <= 1

        gi.identity = (
            "BROKEN criterion 'balanced iff all bits equal'",
            claim_balanced_wrong, true_balanced, box,
        )

    return gi


def _big_profile(eng):
    if hasattr(eng, "left_profiles") and eng.left_profiles:
        return eng.left_profiles[max(eng.left_profiles)]
    return getattr(eng, "left_dev", None)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. EngineV15: TCT as gate inside the loop
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class EngineV15(EngineV14):
    """v15: TCT as gate inside the loop.  Guard cascade IS the snap.

    Architecture:
      1. self.new() runs the identity guard (layered) at construction time.
         A hypothesis with a wrong algebraic criterion is refuted immediately.
      2. After each stage tests its hypotheses, self.guard(h) runs the
         explained-away, coincidence, and exclusivity guards.
      3. After all stages, self.final_guard_pass() runs the consistency guard
         with transitive rollback.

    The 5 guards map onto the 5-bit filter cascade (mod 2/4/8/144/256).
    """

    def __init__(self, quick: bool = False, log=print):
        super().__init__(quick=quick, log=log)
        # v15 state
        self.guard_snap_results: dict = {}     # hid → list[GuardResult]
        self.layered_identity_results: dict = {}  # hid → layered dict
        self.rollback_log: list = []           # [(child_hid, ancestor_hid, reason)]
        self._guarded_hids: set = set()        # hids already stage-guarded

    # ─────────────────────────────────────────────────────────────────────────
    # The guarded constructor (construction-time snap: identity guard)
    # ─────────────────────────────────────────────────────────────────────────
    def new(self, **kw) -> Hypothesis:
        """v15: guarded constructor.  Runs the identity guard at construction.

        This is the construction-time snap.  A hypothesis whose algebraic
        criterion is wrong (at any layer) is refuted immediately, before any
        stage-specific test runs.

        v15 transitive rollback (construction-time): if the hypothesis's parent
        is already refuted-by-guard, the hypothesis is also refuted (inherited
        rollback).  This handles the case where a child is created AFTER its
        parent was refuted — the construction-time check catches what the
        stage-time rollback cannot.
        """
        self.counter += 1
        h = Hypothesis(hid=f"H{self.counter:02d}", **kw)

        # v15 transitive rollback (construction-time): check if parent is refuted
        parent_hid = kw.get("parent")
        if parent_hid is not None:
            parent = next((p for p in self.hyps if p.hid == parent_hid), None)
            if parent is not None and parent.status == "refuted-by-guard":
                h.status = "refuted-by-guard"
                h._guard_reason = f"parent {parent_hid} refuted by guard (inherited)"
                h.record("guard: inherited rollback", False,
                         f"parent {parent_hid} was refuted by guard; "
                         f"this hypothesis is retracted by inheritance")
                self.rollback_log.append((h.hid, parent_hid, "never-tested"))
                self.log(f"  [guard] {h.hid} RETRACTED at construction: "
                         f"parent {parent_hid} refuted")
                h._guard_input = None
                self.hyps.append(h)
                return h

        # Run the identity guard (layered) if this family has an extractor
        extractor = GUARD_EXTRACTORS.get(h.family)
        if extractor is not None:
            try:
                gi = extractor(h, self)
            except Exception as e:
                gi = GuardInput()
                self.log(f"  [guard] extractor for {h.family} failed: {e}")
            if gi.identity is not None:
                name, claim, truth, domain = gi.identity
                layered = identity_guard_layered(name, claim, truth, domain)
                self.layered_identity_results[h.hid] = layered
                if not layered["overall_ok"]:
                    h.status = "refuted-by-guard"
                    h._guard_reason = (
                        f"identity guard failed at layers {layered['failing_layers']}")
                    h.record("guard: identity (layered)", False,
                             layered["summary"].sentence)
                    self.log(f"  [guard] {h.hid} REFUTED at construction: "
                             f"identity fails at {layered['failing_layers']}")
                else:
                    h.record("guard: identity (layered)", True,
                             layered["summary"].sentence)
            # Store the GuardInput for the stage-time guard
            h._guard_input = gi
        else:
            h._guard_input = None

        self.hyps.append(h)
        return h

    # ─────────────────────────────────────────────────────────────────────────
    # The stage-time guard (after the stage tests h)
    # ─────────────────────────────────────────────────────────────────────────
    def guard(self, h: Hypothesis):
        """v15: stage-time guard.  Re-runs identity, then runs explained-away,
        coincidence, exclusivity.

        Called by stages after they test h.  The stage may have OVERWRITTEN
        h.status (e.g., from "refuted-by-guard" to "law-holds").  The stage-time
        guard re-runs the identity guard to catch this: if the identity guard
        fails, the stage's verdict is overridden and h is refuted.

        If any guard fails, h is refuted and its children are rolled back
        transitively.
        """
        if h.hid in self._guarded_hids:
            return  # already guarded
        self._guarded_hids.add(h.hid)

        gi = getattr(h, "_guard_input", None)
        if gi is None:
            return  # no extractor for this family

        results = []

        # mod 2: RE-RUN the identity guard (the stage may have overwritten
        # the construction-time verdict).  This is the key v15 fix: the
        # identity guard is authoritative — if the criterion is wrong, no
        # amount of stage-specific testing can rescue the hypothesis.
        if gi.identity is not None:
            name, claim, truth, domain = gi.identity
            layered = identity_guard_layered(name, claim, truth, domain)
            self.layered_identity_results[h.hid] = layered
            if not layered["overall_ok"]:
                h.status = "refuted-by-guard"
                h._guard_reason = (
                    f"identity guard failed at layers {layered['failing_layers']} "
                    f"(re-run at stage time; stage had set {h.status})")
                h.record("guard: identity (stage-time re-run)", False,
                         layered["summary"].sentence)
                self.log(f"  [guard] {h.hid} REFUTED at stage-time: "
                         f"identity fails at {layered['failing_layers']} "
                         f"(stage had set status)")
                self._rollback_children(h)
                self.guard_snap_results[h.hid] = [layered["summary"]]
                return
            else:
                h.record("guard: identity (stage-time re-run)", True,
                         layered["summary"].sentence)

        # If the construction-time guard already refuted h, don't run the
        # other guards.
        if h.status == "refuted-by-guard":
            return

        # mod 4: explained-away
        if gi.explained_away is not None:
            name, events, feature, premises, domain, *imp = gi.explained_away
            implication = imp[0] if imp else None
            r = explained_away_guard(name, events, feature, premises, domain,
                                     implication=implication)
            results.append(r)
            if not r.ok:
                h.record("guard: explained-away", False, r.sentence)
                h.novelty = "consequence of a known law; not a new mechanism"
                self.log(f"  [guard] {h.hid} EXPLAINED AWAY: {r.sentence[:100]}")

        # mod 8: coincidence
        if gi.coincidence is not None:
            N, K, n_events, hit = gi.coincidence
            r = coincidence_test(N, K, n_events, hit)
            r.sentence = "statistics alone: " + r.sentence
            results.append(r)
            # coincidence is informational; it does not refute by itself

        # mod 144: exclusivity
        if gi.exclusivity is not None:
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

    # ─────────────────────────────────────────────────────────────────────────
    # Transitive rollback
    # ─────────────────────────────────────────────────────────────────────────
    def _rollback_children(self, h: Hypothesis):
        """Retract every hypothesis whose ancestor chain includes h."""
        for c in self.hyps:
            if c.parent == h.hid and c.status != "refuted-by-guard":
                old_status = c.status
                c.status = "refuted-by-guard"
                c._rollback_reason = f"ancestor {h.hid} refuted by guard"
                c.record("guard: rollback", False,
                         f"retracted because ancestor {h.hid} was refuted "
                         f"(was {old_status})")
                self.rollback_log.append((c.hid, h.hid, old_status))
                self.log(f"  [guard] {c.hid} ROLLED BACK (ancestor {h.hid} refuted)")
                self._rollback_children(c)

    # ─────────────────────────────────────────────────────────────────────────
    # The final guard pass (consistency, with rollback)
    # ─────────────────────────────────────────────────────────────────────────
    def final_guard_pass(self):
        """v15: final consistency guard with transitive rollback.

        Maps to mod 256 (byte-level): does every utterance match the final
        status of the hypothesis it asserts?
        """
        if self.tool_dialogue is None:
            return
        utterances = [u["text"] if isinstance(u, dict) else str(u)
                      for u in self.tool_dialogue.utterances]
        # Build the claims map: which hypothesis does each utterance assert?
        # For simplicity, we check claims about TAX.defect.contains.jumps
        # (the "NECESSARY" claim that was refuted).
        statuses = {h.hid: h.status for h in self.hyps}
        claims = {}
        for h in self.hyps:
            if h.key == "TAX.defect.contains.jumps":
                claims[h.hid] = [r"TAX (conservation )?breakdown is NECESSARY",
                                 r"TAX defect is NECESSARY",
                                 r"jumps share bits \(necessary"]
        # Also include hypothesis texts and evidence details
        all_texts = list(utterances) + [h.text for h in self.hyps]
        for h in self.hyps:
            all_texts += [e.get("detail", "") for e in h.evidence]
        r = consistency_guard(statuses, claims, all_texts)
        self.guard_snap_results["_final_consistency"] = [r]
        if not r.ok:
            self.log(f"  [guard] FINAL CONSISTENCY: {r.sentence}")
            # The consistency guard flags utterances; the rollback was already
            # done by the stage-time guards.  We log the finding.

    # ─────────────────────────────────────────────────────────────────────────
    # v15 run: guards inside the loop, not post-hoc
    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        T0 = time.time()
        # Stage A-D2: left/right diagonals, centre, controls, seed memory
        self.run_left_diagonals()
        self.run_right_diagonals()
        self.run_centre()
        self.run_controls()
        self.run_seed_memory()
        # Stage A2: prediction chain
        self.run_prediction_chain()
        # Stage F-H: applications, gap analysis, application tests
        self.run_applications()
        self.run_gap_analysis()
        self.run_application_tests()
        # Stage I: tool-driven generation (TAX hypotheses)
        self.run_tool_driven_generation()
        # v15: guard the TAX hypotheses after their stage
        for h in list(self.hyps):
            if h.family in ("tax-mechanism", "tool-generated") and h.key.startswith("TAX"):
                self.guard(h)
        # Stage J: TAX-period-doubling correlation
        self.run_tax_period_doubling_correlation()
        # v15: guard the correlation hypotheses
        for h in list(self.hyps):
            if h.family in ("tax-mechanism", "cross-domain") and h.key.startswith("TAX"):
                self.guard(h)
        # v15 NEW: wobble domain
        self.run_wobble_domain()
        # v15 NEW: broken-hypothesis sanity check
        self.run_broken_hypothesis_test()
        # Tool-augmented dialogue
        centre_n = 60000 if not self.quick else 20000
        centre_bits = centre_column(centre_n)
        big = (self.left_profiles.get(max(self.left_profiles.keys()))
               if hasattr(self, "left_profiles") else self.left_dev)
        if big is None:
            big = self.left_dev
        self.tool_dialogue = ToolAugmentedDialogue(self)
        self.tool_dialogue.run(self.hyps, centre_bits, big)
        # v15: final consistency guard (no post-hoc guard_tax_section)
        self.final_guard_pass()
        self.credit()
        self.timings["total"] = time.time() - T0
        return self.report()

    # ─────────────────────────────────────────────────────────────────────────
    # v15 NEW: wobble/balance domain
    # ─────────────────────────────────────────────────────────────────────────
    def run_wobble_domain(self):
        """v15 NEW: a second domain to test the guards.

        Generates hypotheses about the centre column's balance, with a
        deliberately-wrong criterion ("balanced iff density = 1/2") that the
        identity guard should catch.
        """
        t0 = time.time()
        self.log("== Wobble/balance domain (v15 NEW) ==")
        centre_n = 60000 if not self.quick else 20000
        c = centre_column(centre_n)
        w = exact_wobble(c)

        # Hypothesis 1: "the centre column is balanced" (using the WRONG criterion
        # "density = 1/2").  The identity guard should catch that the criterion
        # is wrong (balanced means |D(N)| <= 1 for every prefix, not density = 1/2).
        h1 = self.new(
            family="wobble", origin="analysis",
            key="WOBBLE.balanced.density",
            text=f"the centre column is balanced, where 'balanced' means "
                 f"density = 1/2 (WRONG criterion: the true definition is "
                 f"|2·#ones(N) − N| ≤ 1 for every prefix). "
                 f"Actual max wobble = {w['max_wobble']} "
                 f"({float(w['max_wobble']):.4f}) at N={w['max_N']}. "
                 f"is_balanced (true def) = {w['is_balanced']}.",
            lean="-- WOBBLE.balanced.density: balanced iff density = 1/2 (WRONG)")
        if h1.status != "refuted-by-guard":
            h1.status = "survives" if w["is_balanced"] else "refuted-heldout"
            h1.record("wobble test", w["is_balanced"],
                      f"max wobble = {w['max_wobble']}, is_balanced = {w['is_balanced']}")
        self.guard(h1)

        # Hypothesis 2: "the wobble maximum is the same across Rule 30 seeds"
        # (This is a transport claim; test it on two seeds.)
        c11 = centre_column(min(centre_n, 20000), rule=30, seed=0b11)
        c101 = centre_column(min(centre_n, 20000), rule=30, seed=0b101)
        w11 = exact_wobble(c11)
        w101 = exact_wobble(c101)
        same = (w11["max_wobble"] == w101["max_wobble"])
        h2 = self.new(
            family="wobble", origin="analysis",
            key="WOBBLE.transportable",
            text=f"the wobble maximum D(N)^2/N is the same across Rule 30 seeds: "
                 f"seed 1 → {w['max_wobble']}, seed 11 → {w11['max_wobble']}, "
                 f"seed 101 → {w101['max_wobble']}. "
                 f"{'SAME' if same else 'DIFFERENT'}.",
            lean="-- WOBBLE.transportable: wobble maximum is seed-independent")
        h2.status = "survives" if same else "refuted-heldout"
        h2.record("wobble transport", same,
                  f"values: {w['max_wobble']}, {w11['max_wobble']}, {w101['max_wobble']}")
        self.guard(h2)

        # Hypothesis 3: "the centre column is Sturmian" (a strong claim — Sturmian
        # means balanced AND aperiodic).  Test the aperiodicity part.
        is_aperiodic = True
        P = 64
        for p in range(1, P + 1):
            for t in range(len(c) - p):
                if c[t] != c[t + p]:
                    is_aperiodic = False
                    break
            if not is_aperiodic:
                break
        h3 = self.new(
            family="wobble", origin="analysis",
            key="WOBBLE.sturmian",
            text=f"the centre column is Sturmian (balanced AND aperiodic with "
                 f"irrational slope). balanced={w['is_balanced']}, "
                 f"aperiodic (no period ≤ {P}) = {is_aperiodic}. "
                 f"Sturmian requires both; the centre column is "
                 f"{'Sturmian' if w['is_balanced'] and is_aperiodic else 'NOT Sturmian'}.",
            lean="-- WOBBLE.sturmian: balanced ∧ aperiodic")
        h3.status = "survives" if (w["is_balanced"] and is_aperiodic) else "refuted-heldout"
        h3.record("sturmian test", w["is_balanced"] and is_aperiodic,
                  f"balanced={w['is_balanced']}, aperiodic={is_aperiodic}")
        self.guard(h3)

        self.log(f"  wobble domain: 3 hypotheses, "
                 f"{sum(1 for h in [h1,h2,h3] if h.status.startswith('refuted'))} refuted")
        self.timings["wobble-domain"] = time.time() - t0

    # ─────────────────────────────────────────────────────────────────────────
    # v15 NEW: deliberately-broken hypothesis test (sanity check)
    # ─────────────────────────────────────────────────────────────────────────
    def run_broken_hypothesis_test(self):
        """v15 NEW: deliberately create hypotheses with wrong criteria.

        This is a sanity check: the identity guard SHOULD catch these.  If it
        doesn't, the guard is broken.
        """
        t0 = time.time()
        self.log("== Broken-hypothesis sanity test (v15 NEW) ==")

        # Broken hypothesis 1: "TAX conserved iff c = 0" (only disjoint patterns)
        # The true criterion is defect == 0, which holds for many c > 0 cases.
        h1 = self.new(
            family="broken-test", origin="test",
            key="BROKEN.tax.criterion",
            text="DELIBERATELY BROKEN: 'TAX conserved iff c = 0 (disjoint patterns)'. "
                 "The identity guard should catch that this is wrong (the true "
                 "criterion is defect == 0, which holds for c > 0 cases like "
                 "a=5, b=8, c=2).",
            lean="-- BROKEN: conserved iff c = 0 (should be refuted by guard)")
        # The identity guard ran in self.new(); check it fired
        if h1.status == "refuted-by-guard":
            self.log(f"  [PASS] {h1.hid} correctly refuted by identity guard")
        else:
            self.log(f"  [FAIL] {h1.hid} was NOT refuted — guard is broken!")
        self.guard(h1)

        # Broken hypothesis 2: "balanced iff all bits equal"
        h2 = self.new(
            family="broken-test", origin="test",
            key="BROKEN.balance.criterion",
            text="DELIBERATELY BROKEN: 'balanced iff all bits are equal'. "
                 "The identity guard should catch that this is wrong (the true "
                 "criterion is |2·ones - length| <= 1, which holds for mixed "
                 "sequences like 010).",
            lean="-- BROKEN: balanced iff all bits equal (should be refuted)")
        if h2.status == "refuted-by-guard":
            self.log(f"  [PASS] {h2.hid} correctly refuted by identity guard")
        else:
            self.log(f"  [FAIL] {h2.hid} was NOT refuted — guard is broken!")
        self.guard(h2)

        self.log(f"  broken-test: 2 hypotheses, both should be refuted-by-guard")
        self.timings["broken-test"] = time.time() - t0

    # ─────────────────────────────────────────────────────────────────────────
    # v15 report
    # ─────────────────────────────────────────────────────────────────────────
    def report(self) -> dict:
        rep = super().report()
        rep["engine"] = "GLM Hypothesis Engine v15 (TCT as gate inside the loop)"
        rep["guard_snap_results"] = {k: [g.as_dict() for g in v]
                                     for k, v in self.guard_snap_results.items()}
        rep["layered_identity_results"] = {
            k: {"overall_ok": v["overall_ok"],
                "failing_layers": v["failing_layers"],
                "per_layer": {ln: r.as_dict() for ln, r in v["per_layer"].items()}}
            for k, v in self.layered_identity_results.items()
        }
        rep["rollback_log"] = [(c, a, s) for c, a, s in self.rollback_log]
        rep["v15_domains"] = {
            "tax": "regression (should reproduce v14 findings with rollback)",
            "wobble": "new domain (tests identity guard on balance criterion)",
            "broken": "sanity check (verifies guards fire on deliberately-wrong criteria)",
        }
        return rep


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 5. Outputs
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def write_outputs_v15(rep: dict, stem: str = "r42_engine_report_v15"):
    (HERE / f"{stem}.json").write_text(json.dumps(sanitize(rep), indent=1, ensure_ascii=False))
    md = ["# GLM Hypothesis Engine v15 — run report", "",
          "TCT as gate inside the loop. Guard cascade IS the snap.", "",
          f"Engine: {rep['engine']}", "",
          f"Status counts: {rep['status_counts']}", "",
          f"Predictions: {rep['predictions']}", "",
          f"Rollback log ({len(rep.get('rollback_log', []))} retractions):",
          ""]
    for child, ancestor, old_status in rep.get("rollback_log", []):
        md.append(f"- {child} retracted (ancestor {ancestor} refuted; was {old_status})")
    md += ["", "## Layered identity results", ""]
    for hid, lr in rep.get("layered_identity_results", {}).items():
        md.append(f"**{hid}**: overall_ok={lr['overall_ok']}, "
                  f"failing_layers={lr['failing_layers']}")
        for layer_name, r in lr["per_layer"].items():
            md.append(f"  - {layer_name}: {'ok' if r['ok'] else 'FLAG'} — {r['sentence'][:120]}")
        md.append("")
    md += ["", "## Domain tests", ""]
    md.append(f"- **TAX domain** (regression): {rep['v15_domains']['tax']}")
    md.append(f"- **Wobble domain** (new): {rep['v15_domains']['wobble']}")
    md.append(f"- **Broken-test domain** (sanity): {rep['v15_domains']['broken']}")
    md += ["", "## Hypotheses", "",
           "| id | family | origin | status | statement (truncated) |",
           "|---|---|---|---|---|"]
    for r in rep["hypotheses"]:
        stmt = r["statement"].replace("\n", " ").replace("|", "\\|")
        if len(stmt) > 120:
            stmt = stmt[:120] + "..."
        md.append(f"| {r['id']} | {r['family']} | {r['origin']} | {r['status']} | {stmt} |")
    md.append("")
    md.append(f"Wall-clock seconds: {rep['timings_seconds_wallclock']}")
    (HERE / f"{stem}.md").write_text("\n".join(md))


def main():
    quick = "--quick" in sys.argv
    eng = EngineV15(quick=quick)
    rep = eng.run()
    stem = "r42_engine_report_v15_quick" if quick else "r42_engine_report_v15"
    write_outputs_v15(rep, stem)
    print()
    print("Engine:", rep["engine"])
    print("Status counts:", rep["status_counts"])
    print("Predictions:", rep["predictions"])
    print()
    print("v15 layered identity results:")
    for hid, lr in rep.get("layered_identity_results", {}).items():
        verdict = "OK" if lr["overall_ok"] else f"FAILS at {lr['failing_layers']}"
        print(f"  {hid}: {verdict}")
    print()
    print(f"Rollback log ({len(rep.get('rollback_log', []))} retractions):")
    for child, ancestor, old_status in rep.get("rollback_log", []):
        print(f"  {child} ← {ancestor} (was {old_status})")
    print()
    print("Domain tests:")
    for domain, desc in rep.get("v15_domains", {}).items():
        print(f"  {domain}: {desc}")
    print()
    # Summary: which broken-test hypotheses were caught?
    broken_caught = 0
    broken_total = 0
    for h in rep["hypotheses"]:
        if h["family"] == "broken-test":
            broken_total += 1
            if h["status"] == "refuted-by-guard":
                broken_caught += 1
    print(f"Broken-test sanity: {broken_caught}/{broken_total} deliberately-wrong "
          f"hypotheses caught by the identity guard")
    print()
    print("Wall-clock:", rep["timings_seconds_wallclock"])


if __name__ == "__main__":
    main()
