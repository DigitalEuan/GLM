"""The benchmark suites: five questions with external ground truth.

Each suite states its contract in an :class:`~glm_universal.benchmarks.
harness.EvidenceTier` before it runs, scores a population, and reports what
it found that was not a pass.  Nothing here consults the system for the right
answer: the ground truth is a textbook dimensional relation, the periodic
table, a pair of antonyms, or a theorem about the binary Golay code.

| suite | tier | asks |
|---|---|---|
| ``physics_equations`` | curated | does the verifier accept true equations and refuse false ones? |
| ``golay_correction`` | exhaustive | does the decoder correct every error it guarantees to correct? |
| ``analogy_chemistry`` | curated | do periodic-table analogies resolve to the right element? |
| ``analogy_semantic`` | curated | do antonym and scale analogies resolve to the right word? |
| ``analogy_physics`` | curated | do dimensional analogies land in the right dimension? |

Two of them are designed to be able to fail, and do.  ``physics_equations``
carries one textbook identity that EXT10 refuses, and ``analogy_physics``
carries one relation that is an inverse rather than a displacement and so
lies outside the model the solver implements.  Both are reported as findings
with the reason, not filed away.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from glm_universal.data_objects import physics as do_physics
from glm_universal.reasoning import verifier as ve
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import golay_decode as gdc

from .harness import (EvidenceTier, Finding, Suite, SuiteScore, TaskOutcome,
                      register)

__all__ = [
    "PHYSICS_EQUATIONS_TRUE", "PHYSICS_EQUATIONS_FALSE",
    "CHEMISTRY_ANALOGIES", "SEMANTIC_ANALOGIES", "PHYSICS_ANALOGIES",
    "run_physics_equations", "run_golay_correction",
    "run_analogy_chemistry", "run_analogy_semantic", "run_analogy_physics",
]


# ===========================================================================
# 0.  SHARED FIXTURES
# ===========================================================================

_SESSION: Optional[GeometricSession] = None


def _session() -> GeometricSession:
    """One session for every suite: loading the registers is the slow part."""
    global _SESSION
    if _SESSION is None:
        _SESSION = GeometricSession()
    return _SESSION


_REGISTER: Optional[Dict[str, do_physics.Quantity]] = None


def _register() -> Dict[str, do_physics.Quantity]:
    global _REGISTER
    if _REGISTER is None:
        _REGISTER = {q.name: q for q in do_physics.load_physics_register()}
    return _REGISTER


def _answer(query: str, domain: Optional[str] = None) -> str:
    """The analogy answer for a query, or ``"<error>"`` when it refuses."""
    solution = _session().ask(query, domain)
    if not solution.ok:
        return f"<{solution.error}>"
    return str(solution.expected.get("answer", "<no answer>"))


def _nearest(name: str, domain: Optional[str] = None) -> str:
    """The baseline answer: the nearest carrier to ``name``, ignoring a:b.

    A system that had no analogy mechanism at all, but did have the register
    and the metric, would answer an analogy this way.  Anything the analogy
    solver scores above this is what the displacement bought.
    """
    solution = _session().ask(f"nearest {name}", domain)
    if not solution.ok:
        return f"<{solution.error}>"
    return str(solution.expected.get("nearest", "<no answer>"))


# ===========================================================================
# 1.  PHYSICS EQUATIONS -- sensitivity *and* specificity
# ===========================================================================
#
# The package's frozen relation tables contain only true statements, so they
# measure whether the verifier accepts what it should.  They cannot measure
# whether it refuses what it should: a verifier that returned True for
# everything would pass them all.  This suite supplies the missing half.
# ---------------------------------------------------------------------------

PHYSICS_EQUATIONS_TRUE: Tuple[Tuple[str, str], ...] = (
    ("force", "mass * acceleration"),
    ("energy", "force * length"),
    ("power", "energy / time"),
    ("pressure", "force / area"),
    ("momentum", "mass * velocity"),
    ("charge", "current * time"),
    ("velocity", "length / time"),
    ("acceleration", "velocity / time"),
    ("density", "mass / volume"),
    ("voltage", "power / current"),
    ("resistance", "voltage / current"),
    ("capacitance", "charge / voltage"),
    ("frequency", "1 / time"),
    ("area", "length * length"),
    ("volume", "area * length"),
    ("action", "energy * time"),
    ("entropy", "energy / temperature"),
    ("magnetic_flux", "voltage * time"),
    ("inductance", "magnetic_flux / current"),
    ("angular_momentum", "momentum * length"),
)

PHYSICS_EQUATIONS_FALSE: Tuple[Tuple[str, str], ...] = (
    ("force", "mass * velocity"),
    ("energy", "mass * velocity"),
    ("power", "energy * time"),
    ("pressure", "force * area"),
    ("velocity", "acceleration"),
    ("charge", "current / time"),
    ("density", "mass * volume"),
    ("resistance", "voltage * current"),
    ("torque", "energy"),
    ("frequency", "time"),
)

_EQUATION_TIER = EvidenceTier(
    tier="curated",
    population=f"{len(PHYSICS_EQUATIONS_TRUE)} dimensionally true equations "
               f"and {len(PHYSICS_EQUATIONS_FALSE)} dimensionally false ones, "
               f"listed in this module",
    ground_truth="standard SI dimensional analysis, written down before the "
                 "verifier was run; the false cases are minimal mutations of "
                 "true ones (a factor moved from numerator to denominator, a "
                 "quantity replaced by one of different dimension)",
    pass_criterion="the verifier's scalar-semantics verdict equals the "
                   "declared truth value",
    baseline="accept every equation, which scores exactly the true fraction "
             "of the population; a verifier that beats it is discriminating "
             "and not merely agreeable",
    null_result="a score at or below the baseline, meaning the verifier "
                "cannot refuse a false equation",
)


def run_physics_equations() -> SuiteScore:
    """Score the verifier on true *and* false dimensional equations."""
    cases = ([(lhs, rhs, True) for lhs, rhs in PHYSICS_EQUATIONS_TRUE]
             + [(lhs, rhs, False) for lhs, rhs in PHYSICS_EQUATIONS_FALSE])

    outcomes: List[TaskOutcome] = []
    divergences: List[str] = []
    for lhs, rhs, truth in cases:
        scalar = ve.verify_expression_pair(lhs, rhs, "scalar")
        full = ve.verify_expression_pair(lhs, rhs, "full")
        if scalar.holds != full.holds:
            divergences.append(f"{lhs} = {rhs}")
        note = ""
        if scalar.holds != truth:
            note = (f"lhs {scalar.lhs_dimension or '?'} vs rhs "
                    f"{scalar.rhs_dimension or '?'}")
        outcomes.append(TaskOutcome(
            task=f"{lhs} = {rhs}",
            passed=scalar.holds == truth,
            expected="holds" if truth else "refused",
            observed="holds" if scalar.holds else "refused",
            note=note))

    true_count = len(PHYSICS_EQUATIONS_TRUE)
    baseline = Fraction(true_count, len(cases))

    findings = [
        Finding(
            key="scalar_vs_full_semantics",
            statement=f"{len(divergences)} of {len(cases)} equations are "
                      f"accepted under scalar semantics and refused under "
                      f"full tensor semantics.",
            detail="; ".join(divergences) or "none",
        ),
    ]
    angular = next((o for o in outcomes
                    if o.task == "angular_momentum = momentum * length"), None)
    if angular is not None and not angular.passed:
        findings.append(Finding(
            key="ext10_refuses_angular_momentum",
            statement="EXT10 refuses the textbook identity "
                      "`angular_momentum = momentum * length`.",
            detail="This is the basis boundary, not an arithmetic error: "
                   "EXT10 carries plane angle as a dimension, so angular "
                   "momentum is L^2 M T^-1 A^-1 while momentum times length "
                   "is L^2 M T^-1.  The identity is true in SI7, where the "
                   "angle exponent does not exist, and false in EXT10, which "
                   "is exactly the layer handoff the information-loss study "
                   "describes: a statement true at one resolution and "
                   "untrue at the next.",
        ))

    return SuiteScore(
        name="physics_equations",
        question="Does the verifier accept true dimensional equations and "
                 "refuse false ones?",
        tier=_EQUATION_TIER,
        outcomes=tuple(outcomes),
        baseline_score=baseline,
        findings=tuple(findings),
        measurements={
            "true_cases": str(true_count),
            "false_cases": str(len(PHYSICS_EQUATIONS_FALSE)),
            "true_accepted": str(sum(
                1 for o in outcomes
                if o.expected == "holds" and o.passed)),
            "false_refused": str(sum(
                1 for o in outcomes
                if o.expected == "refused" and o.passed)),
            "scalar_full_divergences": str(len(divergences)),
        },
    )


# ===========================================================================
# 2.  GOLAY CORRECTION -- exhaustive, with the failure modes measured
# ===========================================================================

_GOLAY_TIER = EvidenceTier(
    tier="exhaustive",
    population="every error pattern of Hamming weight 0, 1, 2 or 3 on 24 "
               "coordinates -- 1 + 24 + 276 + 2024 = 2325 patterns.  The "
               "code is linear, so decoding an error added to the zero "
               "codeword decides the same question for every codeword; the "
               "suite checks that invariance on a fixed non-zero codeword "
               "rather than assuming it.",
    ground_truth="the minimum distance of the binary Golay code is 8, so "
                 "every pattern of weight at most 3 is nearer to the sent "
                 "codeword than to any other -- a theorem, independent of "
                 "the decoder under test",
    pass_criterion="`decode_complete` returns exactly one nearest codeword, "
                   "it is the sent one, and the decoding is flagged "
                   "`guaranteed`",
    baseline="return the received word unchanged, which is right only when "
             "no error occurred: 1 of 2325",
    null_result="any pattern inside the packing radius that decodes to the "
                "wrong codeword, or reports a tie",
)


def _weight_patterns(weight: int):
    """Every 24-bit mask of exactly this Hamming weight."""
    for positions in itertools.combinations(range(24), weight):
        mask = 0
        for index in positions:
            mask |= 1 << index
        yield mask


def run_golay_correction() -> SuiteScore:
    """Score the complete decoder inside the radius it guarantees."""
    outcomes: List[TaskOutcome] = []
    for weight in range(4):
        for mask in _weight_patterns(weight):
            decoding = gdc.decode_complete(mask)
            ok = (decoding.corrected == 0
                  and len(decoding.candidates) == 1
                  and decoding.guaranteed)
            outcomes.append(TaskOutcome(
                task=f"weight {weight} pattern {mask:#08x}",
                passed=ok,
                expected="corrected to 0, uniquely, guaranteed",
                observed=f"{decoding.status}, "
                         f"{len(decoding.candidates)} candidate(s), "
                         f"guaranteed={decoding.guaranteed}"))

    # -- linearity: the same errors on a non-zero codeword -------------------
    sent = min(m for m in gdc.GOLAY.codeword_masks if m != 0)
    linear_ok = True
    for weight in range(4):
        for mask in itertools.islice(_weight_patterns(weight), 40):
            if gdc.decode_complete(sent ^ mask).corrected != sent:
                linear_ok = False
                break
        if not linear_ok:
            break

    # -- the two failure modes, measured rather than asserted ---------------
    ambiguous_at_4 = sum(1 for mask in _weight_patterns(4)
                         if gdc.decode_complete(mask).status == "ambiguous")
    total_at_4 = sum(1 for _ in _weight_patterns(4))
    miscorrected_at_5 = sum(
        1 for mask in _weight_patterns(5)
        if gdc.decode_complete(mask).corrected not in (None, 0))
    total_at_5 = sum(1 for _ in _weight_patterns(5))

    # -- what the retired decoder did on the same population ----------------
    legacy_hits = sum(1 for weight in range(4)
                      for mask in _weight_patterns(weight)
                      if gdc.legacy_snap_decode(mask)[0] == 0)

    findings = (
        Finding(
            key="weight_4_is_ambiguous",
            statement=f"{ambiguous_at_4} of {total_at_4} weight-4 patterns "
                      f"are equidistant from six codewords.",
            detail="One past the packing radius the nearest codeword stops "
                   "being unique.  The decoder reports `ambiguous` and "
                   "returns all six rather than picking one, so the boundary "
                   "is visible to the caller instead of being hidden by a "
                   "silent tie-break.",
        ),
        Finding(
            key="weight_5_is_confidently_wrong",
            statement=f"{miscorrected_at_5} of {total_at_5} weight-5 "
                      f"patterns decode to a unique, wrong codeword.",
            detail="A weight-5 error is the complement, inside a unique "
                   "octad of the Steiner system S(5,8,24), of a weight-3 "
                   "error, so the received word sits at distance 3 from the "
                   "wrong codeword and 5 from the right one.  Every "
                   "nearest-codeword rule is unique, confident and wrong "
                   "here; the remedy is a declared channel radius, not a "
                   "better decoder.  This is a null result for correction "
                   "beyond the radius and is reported as one.",
        ),
    )

    return SuiteScore(
        name="golay_correction",
        question="Does the complete decoder correct every error the code "
                 "guarantees, and say so when it cannot?",
        tier=_GOLAY_TIER,
        outcomes=tuple(outcomes),
        baseline_score=Fraction(1, len(outcomes)),
        findings=findings,
        measurements={
            "patterns_scored": str(len(outcomes)),
            "legacy_snap_correct": f"{legacy_hits}/{len(outcomes)}",
            "linearity_spot_check": str(linear_ok),
            "ambiguous_at_weight_4": f"{ambiguous_at_4}/{total_at_4}",
            "miscorrected_at_weight_5": f"{miscorrected_at_5}/{total_at_5}",
        },
    )


# ===========================================================================
# 3.  ANALOGY -- three registers, three kinds of ground truth
# ===========================================================================

CHEMISTRY_ANALOGIES: Tuple[Tuple[str, str, str, str], ...] = (
    ("Li", "Na", "Be", "Mg"),
    ("Na", "K", "Mg", "Ca"),
    ("C", "Si", "N", "P"),
    ("F", "Cl", "O", "S"),
    ("Li", "Be", "Na", "Mg"),
    ("N", "O", "P", "S"),
    ("K", "Ca", "Rb", "Sr"),
    ("Cl", "Br", "S", "Se"),
    ("Ne", "Ar", "Na", "K"),
    ("He", "Ne", "Ar", "Kr"),
    ("B", "Al", "C", "Si"),
    ("H", "Li", "He", "Ne"),
)

_CHEMISTRY_TIER = EvidenceTier(
    tier="curated",
    population=f"{len(CHEMISTRY_ANALOGIES)} four-term analogies over the "
               f"118-element register, each a move by one group or one "
               f"period",
    ground_truth="the periodic table: the answer is the element standing to "
                 "C as B stands to A",
    pass_criterion="the solver's answer is that element's symbol, exactly",
    baseline="answer with the nearest carrier to C, ignoring the "
             "displacement A -> B entirely",
    null_result="a score at or below that baseline, meaning the "
                "displacement carried no information",
)


# The three cases that used to miss are recorded in
# ``ANALOGY_LAYER_STUDY.md``.  Two of them were missing relations, now
# stated in the register: ``proton opposite_of electron`` and ``rotate
# form_of move`` / ``accelerate form_of move``.  The third was a wrong
# target: ``cause : effect :: force : ?`` was curated as ``motion``, but the
# effect a force produces is the one the register names, ``force causes
# acceleration`` -- Newton's second law, not a gloss -- so the target was
# corrected to ``acceleration`` rather than the register bent to fit it.
SEMANTIC_ANALOGIES: Tuple[Tuple[str, str, str, str], ...] = (
    ("hot", "cold", "fast", "slow"),
    ("large", "small", "strong", "weak"),
    ("fast", "slow", "hot", "cold"),
    ("strong", "weak", "large", "small"),
    ("north", "south", "hot", "cold"),
    ("solid", "liquid", "liquid", "gas"),
    ("heavy", "light_adj", "large", "small"),
    ("cause", "effect", "force", "acceleration"),
    ("electron", "proton", "north", "south"),
    ("accelerate", "move", "rotate", "move"),
)

_SEMANTIC_TIER = EvidenceTier(
    tier="curated",
    population=f"{len(SEMANTIC_ANALOGIES)} four-term analogies over the "
               f"95-word semantic register: five antonym pairs, one "
               f"phase-of-matter succession, one part-whole pair, one "
               f"cause-effect pair, one polarity pair and one "
               f"manner-of-motion pair",
    ground_truth="ordinary English: the fourth word is fixed by the "
                 "relation the first two stand in",
    pass_criterion="the solver's answer is that word, exactly",
    baseline="answer with the nearest carrier to C, ignoring the "
             "displacement A -> B entirely",
    null_result="a score at or below that baseline; in particular an "
                "encoding that placed antonyms at the same point could not "
                "beat it",
)


# (a, b, c, target).  ``target`` names a register quantity whose *dimension*
# is the right answer; the analogy is scored dimensionally because the
# register holds many distinct quantities of the same dimension and a
# name-level score would be measuring the tie-break, not the reasoning.
PHYSICS_ANALOGIES: Tuple[Tuple[str, str, str, str], ...] = (
    ("velocity", "acceleration", "momentum", "force"),
    ("length", "area", "area", "volume"),
    ("area", "volume", "length", "area"),
    ("velocity", "momentum", "acceleration", "force"),
    ("energy", "power", "momentum", "force"),
    ("length", "velocity", "velocity", "acceleration"),
    ("power", "energy", "force", "momentum"),
    ("force", "pressure", "energy", "surface_tension"),
    ("mass", "density", "charge", "charge_density"),
    ("volume", "volumetric_flow", "mass", "mass_flow"),
    ("energy", "entropy", "power", "entropy_production_rate"),
    ("acceleration", "angular_acceleration", "velocity", "angular_velocity"),
    ("length", "wavenumber", "time", "frequency"),
)

_PHYSICS_ANALOGY_TIER = EvidenceTier(
    tier="curated",
    population=f"{len(PHYSICS_ANALOGIES)} four-term analogies over the "
               f"physics register, each a standard dimensional relation "
               f"(per unit time, per unit area, per unit temperature, times "
               f"a length, and one reciprocal)",
    ground_truth="SI dimensional analysis: the target quantity is named in "
                 "the task and its exponent vector is read from the "
                 "register, not from the solver",
    pass_criterion="the answer's EXT10 exponent vector equals the target's.  "
                   "Name equality is reported as a separate measurement: "
                   "many register entries share a dimension, so requiring a "
                   "particular name would score the tie-break rather than "
                   "the analogy",
    baseline="answer with the nearest carrier to C, ignoring the "
             "displacement A -> B entirely, scored the same way",
    null_result="a score at or below that baseline",
)


def _score_named_analogies(name: str, question: str, tier: EvidenceTier,
                           cases: Sequence[Tuple[str, str, str, str]],
                           domain: str) -> SuiteScore:
    """Score analogies whose right answer is one particular name."""
    outcomes: List[TaskOutcome] = []
    baseline_hits = 0
    for a, b, c, expected in cases:
        got = _answer(f"{a} : {b} :: {c} : ?", domain)
        outcomes.append(TaskOutcome(
            task=f"{a} : {b} :: {c} : ?",
            passed=got == expected,
            expected=expected,
            observed=got))
        if _nearest(c, domain) == expected:
            baseline_hits += 1
    baseline = Fraction(baseline_hits, len(cases))

    misses = [f"{o.task} -> {o.observed} (wanted {o.expected})"
              for o in outcomes if not o.passed]
    findings = (
        Finding(
            key="misses",
            statement=f"{len(misses)} of {len(outcomes)} analogies resolve "
                      f"to the wrong carrier.",
            detail="; ".join(misses) or "none",
        ),
    )
    return SuiteScore(
        name=name, question=question, tier=tier,
        outcomes=tuple(outcomes), baseline_score=baseline,
        findings=findings,
        measurements={"baseline_hits": f"{baseline_hits}/{len(cases)}",
                      "domain": domain},
    )


def run_analogy_chemistry() -> SuiteScore:
    """Score periodic-table analogies against the periodic table."""
    return _score_named_analogies(
        "analogy_chemistry",
        "Do periodic-table analogies resolve to the right element?",
        _CHEMISTRY_TIER, CHEMISTRY_ANALOGIES, "chemistry")


def run_analogy_semantic() -> SuiteScore:
    """Score antonym and succession analogies against ordinary English."""
    return _score_named_analogies(
        "analogy_semantic",
        "Do antonym and scale analogies resolve to the right word?",
        _SEMANTIC_TIER, SEMANTIC_ANALOGIES, "lexicon")


def run_analogy_physics() -> SuiteScore:
    """Score dimensional analogies by dimension, and report names too."""
    register = _register()
    outcomes: List[TaskOutcome] = []
    baseline_hits = 0
    name_hits = 0
    for a, b, c, target in cases_with_targets():
        wanted = register[target].exps_ext10
        got = _answer(f"{a} : {b} :: {c} : ?", "physics")
        got_exps = register[got].exps_ext10 if got in register else None
        passed = got_exps == wanted
        name_hits += got == target
        outcomes.append(TaskOutcome(
            task=f"{a} : {b} :: {c} : ?",
            passed=passed,
            expected=f"{target} [{register[target].dimension_string()}]",
            observed=(f"{got} [{register[got].dimension_string()}]"
                      if got in register else got),
            note="" if passed else "wrong dimension"))
        near = _nearest(c, "physics")
        if near in register and register[near].exps_ext10 == wanted:
            baseline_hits += 1

    reciprocal = next((o for o in outcomes
                       if o.task == "length : wavenumber :: time : ?"), None)
    findings = [
        Finding(
            key="name_level_score",
            statement=f"Scored by name rather than by dimension the suite "
                      f"gets {name_hits} of {len(outcomes)}.",
            detail="The gap is the register's dimensional degeneracy: many "
                   "quantities share an exponent vector, and which of them "
                   "the metric returns is decided by the coordinates outside "
                   "the exponent block, not by the analogy.",
        ),
    ]
    if reciprocal is not None and not reciprocal.passed:
        findings.append(Finding(
            key="reciprocal_relations_are_out_of_model",
            statement="`length : wavenumber :: time : frequency` fails.",
            detail="The solver models an analogy as a fixed displacement "
                   "b - a added to c.  Length to wavenumber is not a "
                   "displacement but an inversion, and the displacement "
                   "-2L applied to time gives L^-2 T rather than T^-1.  The "
                   "task is correct and the answer is wrong for a reason "
                   "that is structural: reciprocal relations are outside the "
                   "additive model, and no amount of tuning inside it will "
                   "reach them.",
        ))
    elif reciprocal is not None:
        findings.append(Finding(
            key="reciprocal_relations_are_in_model",
            statement="`length : wavenumber :: time : frequency` now holds.",
            detail="It is not the displacement solver that reaches it.  The "
                   "named-relation layer recognises that every EXT10 "
                   "exponent of wavenumber is the negative of length's, "
                   "names the step a reciprocal, and reflects time's "
                   "exponent vector instead of translating it, which fixes "
                   "the answer's dimension at T^-1 exactly.  The additive "
                   "model is still unable to reach the case; it is no "
                   "longer the only model on offer.",
        ))

    return SuiteScore(
        name="analogy_physics",
        question="Do dimensional analogies land in the right dimension?",
        tier=_PHYSICS_ANALOGY_TIER,
        outcomes=tuple(outcomes),
        baseline_score=Fraction(baseline_hits, len(outcomes)),
        findings=tuple(findings),
        measurements={
            "name_level_hits": f"{name_hits}/{len(outcomes)}",
            "baseline_hits": f"{baseline_hits}/{len(outcomes)}",
            "domain": "physics",
        },
    )


def cases_with_targets() -> Tuple[Tuple[str, str, str, str], ...]:
    """The physics analogies, checked against the register before use."""
    register = _register()
    missing = sorted({t for _, _, _, t in PHYSICS_ANALOGIES
                      if t not in register})
    if missing:
        raise KeyError(f"analogy_physics: target quantities absent from the "
                       f"register: {missing}")
    return PHYSICS_ANALOGIES


# ===========================================================================
# 4.  REGISTRATION
# ===========================================================================

register(Suite(
    name="physics_equations",
    question="Does the verifier accept true dimensional equations and "
             "refuse false ones?",
    tier=_EQUATION_TIER,
    runner=run_physics_equations))

register(Suite(
    name="golay_correction",
    question="Does the complete decoder correct every error the code "
             "guarantees, and say so when it cannot?",
    tier=_GOLAY_TIER,
    runner=run_golay_correction))

register(Suite(
    name="analogy_chemistry",
    question="Do periodic-table analogies resolve to the right element?",
    tier=_CHEMISTRY_TIER,
    runner=run_analogy_chemistry))

register(Suite(
    name="analogy_semantic",
    question="Do antonym and scale analogies resolve to the right word?",
    tier=_SEMANTIC_TIER,
    runner=run_analogy_semantic))

register(Suite(
    name="analogy_physics",
    question="Do dimensional analogies land in the right dimension?",
    tier=_PHYSICS_ANALOGY_TIER,
    runner=run_analogy_physics))
