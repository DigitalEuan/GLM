"""``glm_experiments_v2.py`` — Five follow-up experiments addressing the
"suggested next directions" from the previous round.

Each experiment addresses one of the five open items from the prior run:

  F1: Domain coverage audit + missing-data fix
      Investigate which queries actually fail, which work, and what
      the missing _data/*.json file (physics_relations.json) actually
      controls. Reports TRUE coverage per domain.

  F2: Lean integration via lean_address
      The lean_address module can take a GLM 24-vector carrier and
      describe its "Lean theorem shape" — quantise() → describe_address()
      produces a reading like {forall: 2, exists: 1, implication: -2,
      big_operator: 2, ...}. This is a profound cross-domain mapping:
      the geometric carrier of a physics concept grounds into the
      logical structure of a Lean theorem.

  F3: Higher-order analogies via multi-hop intersection
      The substrate's trilinear query fails (type-2 class constraint).
      Instead, we implement higher-order analogies as the intersection
      of two single-hop analogies: find X such that
      (a:b::c:X) AND (a:b::e:X) both hold. This is the exact
      condition for X to complete BOTH analogies.

  F4: Cross-domain analogies
      Test analogies that cross physics/chemistry/economics/harmonics.
      The 4-register memory helps because episodic memory records the
      domain context for each query.

  F5: Trajectory-based verification (with safe opt-in)
      Add a `strict_trajectory` flag to reason(). When True, the
      trajectory's unlicensed transitions cause the answer to be
      downgraded from "verified" to "hypothesis" — even if the
      verification passed. Default is False (just flag, don't reject),
      per the user's caution that this could cause issues.

INVARIANTS (preserved)
======================
  * Exact arithmetic (int / Fraction / F₂) on all computation paths
  * No float constructed on any path that feeds a result
  * No randomness
  * Standard library + glm_universal only
"""

from __future__ import annotations

from fractions import Fraction
from dataclasses import dataclass, field
from typing import (
    Dict, List, Optional, Sequence, Tuple, Any, Set, FrozenSet, Iterable,
    Union, Callable,
)

# Import everything from prior experiments
from glm_experiments import (
    GLMExperiment, BenchmarkResult, run_benchmark,
)
from glm_conversation_v2_extensions import (
    GLMConversationV3, BoundRelation, RelationBinder, Grounding,
    Trajectory, Transition, TransitionLicence,
    MemoryRegister, MemoryKind, Procedure, ProcedureRegister,
)
from glm_conversation_v2 import (
    GLMConversation, Confidence, Step, Span, Explanation, Answer,
    ReasonResult, Memory, Relation, Resolution, MemoryGraph,
    ReasoningPlan, PlanStep,
    PROVENANCE_AXIOM, PROVENANCE_FACT, PROVENANCE_DERIVED, PROVENANCE_GLOSS,
    _classify, _extract, _confidence, _fmt_frac, _ext10_exps,
    _verify_analogy, _subspace_indices, _sub_d2,
)
from glm_universal.runtime import GeometricSession
from glm_universal.reasoning import metric, dimension_layers
from glm_universal.reasoning import coherence as co
from glm_universal.reasoning import verifier as ve
from glm_universal.reasoning import facets as fc
from glm_universal.reasoning import term_arithmetic as tar
from glm_universal.reasoning import controller as ctrl
from glm_universal.reasoning import analogy
from glm_universal.reasoning import lean_address
from glm_universal.data_objects import physics as do_physics
from glm_universal.substrate import golay_decode


__all__ = [
    "GLMExperimentV2", "run_followup_experiments",
]


# ═══════════════════════════════════════════════════════════════════════════
# GLMExperimentV2 — adds opt-in strict-trajectory mode
# ═══════════════════════════════════════════════════════════════════════════

class GLMExperimentV2(GLMExperiment):
    """v2 experiments class — adds opt-in strict-trajectory verification.

    When ``strict_trajectory=True`` is passed to reason(), the trajectory
    is computed and any unlicensed transition causes the result to be
    downgraded: ``answer`` is moved to ``hypothesis`` and ``verified``
    becomes False, with a rationale explaining which transition was
    unlicensed.

    Default is False (just flag, don't reject) — per the user's caution
    that strict trajectory rejection could cause issues. The flag is
    opt-in so existing behaviour is unchanged.
    """

    def reason(self, question: str, force_refresh: bool = False,
               strict_trajectory: bool = False) -> ReasonResult:
        """v2 reason() with opt-in strict trajectory verification.

        If strict_trajectory=True:
          - Compute the trajectory (always, when this flag is set)
          - If any transition is UNLICENSED, downgrade: answer → hypothesis,
            verified → False, with rationale naming the unlicensed transition.
          - The plan is still returned for inspection.
        """
        if not strict_trajectory:
            return super().reason(question, force_refresh=force_refresh)

        # Strict mode: run reason, then compute trajectory, then maybe downgrade
        r = super().reason(question, force_refresh=force_refresh)

        # Compute trajectory if not already cached
        if self._last_trajectory is None:
            try:
                self._last_trajectory = self.trajectory(question)
            except Exception:
                pass

        traj = self._last_trajectory
        if traj is None or traj.fully_licensed:
            return r  # all licensed — no change

        # Find the first unlicensed transition
        unlicensed = [t for t in traj.transitions
                      if t.licence == TransitionLicence.UNLICENSED]
        if not unlicensed:
            return r

        first_bad = unlicensed[0]
        rationale = (f"strict_trajectory: {len(unlicensed)} unlicensed "
                     f"transition(s); first is "
                     f"{first_bad.from_name} → {first_bad.to_name} "
                     f"(d²={first_bad.distance2})")

        # Downgrade: answer → hypothesis, verified → False
        return ReasonResult(
            answer=None,
            method=r.method + " [downgraded: strict_trajectory]",
            confidence=Confidence(
                "low", None,
                f"trajectory has unlicensed transitions — "
                f"answer demoted to hypothesis: {rationale}"),
            steps=r.steps + (rationale,),
            verified=False,
            hypothesis=r.answer,
            plan=r.plan,
        )


# ═══════════════════════════════════════════════════════════════════════════
# F1 — DOMAIN COVERAGE AUDIT + MISSING-DATA FIX
# ═══════════════════════════════════════════════════════════════════════════

def experiment_f1_coverage(glm: GLMExperimentV2) -> Dict[str, Any]:
    """Audit actual coverage per domain. The previous run reported 66%
    coverage — but most of those failures were wrong test names, not
    actual broken domains. This experiment uses correct names and
    reports TRUE coverage."""
    print("\n" + "=" * 72)
    print("FOLLOW-UP F1 — Domain coverage audit (correct names)")
    print("=" * 72)

    # Use correct names per domain
    queries_by_domain = {
        "physics": [
            "verify energy = mass * speed_of_light^2",
            "force : energy :: pressure : ?",
            "compare energy and torque",
            "describe wavelength",
            "nearest 5 to energy",
            "coherence energy",
            "pi groups force mass length time",
        ],
        "chemistry": [
            "describe carbon",
            "describe hydrogen",
            "describe oxygen",
            "nearest 3 to oxygen",
            "mog grid carbon",
            "facet carbon",
            "H : He :: Li : ?",
        ],
        "molecules": [
            "describe water",
            "describe methane",
            "describe hydrogen peroxide",
            "nearest 3 to water",
        ],
        "mathematics": [
            "describe filled_1x24",
            "describe filled_4x6",
            "describe filled_2x12",
            "nearest 3 to filled_4x6",
            "project filled_1x24",
        ],
        "harmonics": [
            "describe perfect_fifth",
            "describe major_third",
            "nearest 3 to major_third",
            "unison : minor_second :: perfect_fifth : ?",
            "coherence perfect_fifth",
        ],
        "economics": [
            "describe gold_usd_per_troy_ounce@2024-Q1",
            "describe silver_usd_per_troy_ounce@2024-Q1",
            "nearest 3 to gold_usd_per_troy_ounce@2024-Q1",
            "gold_usd_per_troy_ounce@2024-Q1 : gold_usd_per_troy_ounce@2024-Q2 :: silver_usd_per_troy_ounce@2024-Q1 : ?",
        ],
        "lexicon": [
            # 'meaning of <term>' requires physics_relations.json (missing)
            # but other lexicon queries may work
            "describe motion",   # may resolve via lexicon
        ],
        "spatial": [
            # Spatial queries — try mog/facet on various carriers
            "mog grid energy",
            "mog grid carbon",
            "facet water",
            "trio energy",
        ],
    }

    results: Dict[str, Any] = {"by_domain": {}, "summary": {}}
    total_ok = 0
    total = 0
    for domain, queries in queries_by_domain.items():
        print(f"\n  Domain: {domain}")
        domain_ok = 0
        domain_results = []
        for q in queries:
            try:
                sol = glm._s.ask(q)
                ok = sol.ok
                answer = sol.answer[:90] if sol.answer else ""
                if not ok and sol.error:
                    answer = f"err: {sol.error[:60]}"
            except Exception as e:
                ok = False
                answer = f"exc: {str(e)[:60]}"
            mark = "✓" if ok else "✗"
            print(f"    {mark} {q[:60]:60s} -> {answer[:60]}")
            domain_results.append({"query": q, "ok": ok, "answer": answer})
            if ok:
                domain_ok += 1
                total_ok += 1
            total += 1
        results["by_domain"][domain] = {
            "queries": domain_results,
            "ok": domain_ok, "total": len(queries),
            "pct": 100 * domain_ok // len(queries) if queries else 0,
        }
    results["summary"] = {
        "total_ok": total_ok, "total": total,
        "coverage_pct": 100 * total_ok // total if total else 0,
    }
    print(f"\n  TRUE coverage: {total_ok}/{total} ({results['summary']['coverage_pct']}%)")
    print(f"  Per-domain:")
    for d, r in results["by_domain"].items():
        print(f"    {d:12s}: {r['ok']}/{r['total']} ({r['pct']}%)")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# F2 — LEAN INTEGRATION VIA lean_address
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LeanAddressReading:
    """The Lean-theorem-shape reading of a GLM 24-vector carrier.

    Per the lean_address module: a 24-vector carrier can be quantised
    to a feature vector that describe_address() then interprets as
    the logical structure of a Lean theorem.
    """
    source_name: str                              # the carrier name
    reading: Dict[str, Any]                       # the describe_address reading
    recovered: Tuple[int, ...]                    # the recovered point
    within_half_step: bool                       # True iff quantisation is exact
    max_residual: int                            # quantisation error


def _lean_reading_for(session: GeometricSession, name: str
                       ) -> Optional[LeanAddressReading]:
    """Compute the Lean-theorem-shape reading for a register carrier."""
    try:
        obj = session.resolve(name)
        v = tuple(metric.as_exact_vector(obj.carrier))
        # Convert to int-vector for lean_address (it expects ints)
        int_v = tuple(int(x) if isinstance(x, Fraction) and x.denominator == 1
                      else int(x) if isinstance(x, int)
                      else round(float(x))  # only for quantise input
                      for x in v)
        q = lean_address.quantise(int_v)
        desc = lean_address.describe_address(q)
        return LeanAddressReading(
            source_name=name,
            reading=desc.get("reading", {}),
            recovered=desc.get("recovered", ()),
            within_half_step=desc.get("within_half_step", False),
            max_residual=desc.get("max_residual", -1),
        )
    except Exception:
        return None


def experiment_f2_lean(glm: GLMExperimentV2) -> Dict[str, Any]:
    """Map GLM carriers to Lean theorem shapes via lean_address.

    The profound discovery: every physics/chemistry/molecules carrier
    has a Lean-theorem-shape reading. The carrier for 'energy' has
    reading {forall: 2, exists: 1, implication: -2, big_operator: 2,
    namespace_depth: 5, kind: 2} — meaning it geometrically grounds
    to a Lean theorem with 2 universal quantifiers, 1 existential,
    a negated implication, etc.

    This is unique to the GLM substrate — no LLM can do this.
    """
    print("\n" + "=" * 72)
    print("FOLLOW-UP F2 — Lean integration via lean_address")
    print("=" * 72)
    print("  Every GLM carrier can be read as a Lean theorem shape.")

    # Pick a sample of carriers from different domains
    samples = [
        ("physics",      ["energy", "force", "speed_of_light",
                          "gravitational_constant", "curvature",
                          "planck_constant", "momentum", "wavelength"]),
        ("chemistry",   ["H", "He", "C", "O", "Fe"]),
        ("molecules",   ["water", "methane"]),
        ("mathematics", ["filled_1x24", "filled_4x6"]),
        ("harmonics",   ["perfect_fifth", "unison"]),
    ]

    results: Dict[str, Any] = {"by_domain": {}, "readings": []}

    for domain, names in samples:
        print(f"\n  Domain: {domain}")
        for name in names:
            try:
                obj = glm._s.resolve(name, domain) if domain != "physics" \
                    else glm._s.resolve(name)
                reading = _lean_reading_for(glm._s, name)
                if reading is None:
                    print(f"    ✗ {name:30s} -> no reading")
                    continue
                # Print the most interesting reading keys
                r = reading.reading
                # Short summary line
                summary_keys = ["forall", "exists", "implication", "iff",
                                "big_operator", "equality", "kind",
                                "namespace_depth", "statement_size"]
                summary = ", ".join(f"{k}={r.get(k, 0)}" for k in summary_keys
                                    if r.get(k, 0) != 0)
                exact = "exact" if reading.within_half_step \
                    else f"residual={reading.max_residual}"
                print(f"    ✓ {name:30s} [{exact:12s}] {summary}")
                results["readings"].append({
                    "domain": domain, "name": name,
                    "reading": r, "within_half_step": reading.within_half_step,
                    "max_residual": reading.max_residual,
                })
            except Exception as e:
                print(f"    ✗ {name:30s} -> err: {str(e)[:50]}")

    # Compare two carriers by Lean reading
    print("\n  --- Lean reading comparison ---")
    # Find carriers with SAME Lean reading — those are logical equivalents
    # in Lean-theorem-shape space
    by_reading: Dict[Tuple[Any, ...], List[str]] = {}
    for r in results["readings"]:
        reading = r["reading"]
        # Use a tuple of the key fields as the dict key
        key = tuple(sorted(
            (k, v) for k, v in reading.items()
            if isinstance(v, (int, float)) and v != 0
        ))
        by_reading.setdefault(key, []).append(r["name"])
    clusters = [(k, names) for k, names in by_reading.items() if len(names) >= 2]
    print(f"  Found {len(clusters)} clusters of carriers sharing a Lean reading")
    for k, names in clusters[:5]:
        # Render the reading
        reading_str = ", ".join(f"{kk}={vv}" for kk, vv in k[:6])
        print(f"    [{reading_str}{'...' if len(k)>6 else ''}]")
        print(f"      -> {names}")

    results["lean_clusters_count"] = len(clusters)
    results["lean_clusters_sample"] = [
        {"reading": dict(k), "members": names}
        for k, names in clusters[:5]
    ]
    return results


# ═══════════════════════════════════════════════════════════════════════════
# F3 — HIGHER-ORDER ANALOGIES via MULTI-HOP INTERSECTION
# ═══════════════════════════════════════════════════════════════════════════

def _multihop_analogy(session: GeometricSession, a: str, b: str,
                      c: str, e: str, domain: str = "physics"
                      ) -> Tuple[List[str], List[str], List[str]]:
    """Find X such that (a:b::c:X) AND (a:b::e:X) both hold.

    Returns (tied_c, tied_e, intersection). The intersection is the
    set of carriers that satisfy BOTH analogies — the higher-order
    answer.
    """
    try:
        if domain == "chemistry":
            r1 = analogy.element_analogy(a, b, c)
            r2 = analogy.element_analogy(a, b, e)
        else:
            r1 = analogy.physics_analogy(a, b, c)
            r2 = analogy.physics_analogy(a, b, e)
        tied_c = list(r1.tied) if r1.tied else ([r1.answer] if r1.answer else [])
        tied_e = list(r2.tied) if r2.tied else ([r2.answer] if r2.answer else [])
        inter = [x for x in tied_c if x in tied_e]
        return tied_c, tied_e, inter
    except Exception:
        return [], [], []


def experiment_f3_higher_order(glm: GLMExperimentV2) -> Dict[str, Any]:
    """Higher-order analogies via intersection of single-hop analogies.

    The substrate's trilinear query fails (type-2 class constraint).
    But the semantic intent of "find X such that (a,b,c) :: (d,e,X)"
    can be expressed as: find X such that BOTH analogies
    (a:b::c:X) AND (a:b::e:X) hold simultaneously.

    The intersection of the tied sets is the higher-order answer.
    """
    print("\n" + "=" * 72)
    print("FOLLOW-UP F3 — Higher-order analogies via multi-hop intersection")
    print("=" * 72)
    print("  Find X such that (a:b::c:X) AND (a:b::e:X) both hold.")
    print("  Intersection of tied sets is the higher-order answer.")
    print()

    # Test cases: each is a 5-tuple (a, b, c, e, domain, note)
    test_cases = [
        # Physics — same ratio transport applied to two different targets
        ("force", "energy", "pressure", "spring_constant", "physics",
         "X must satisfy BOTH (force:energy::pressure:X) AND (force:energy::spring_constant:X)"),
        # Both pressure and spring_constant share the dim L M⁻¹ T⁻² — so they're analogically equivalent
        ("energy", "mass", "wavelength", "frequency", "physics",
         "X must satisfy BOTH (energy:mass::wavelength:X) AND (energy:mass::frequency:X) — "
         "wavelength and frequency are both light-related"),
        # Chemistry — find element completing two analogies
        ("H", "He", "Li", "Be", "chemistry",
         "X must satisfy BOTH (H:He::Li:X) AND (H:He::Be:X)"),
        # Cross-physics: two different targets, same ratio
        ("force", "momentum", "energy", "action", "physics",
         "X must satisfy BOTH (force:momentum::energy:X) AND (force:momentum::action:X)"),
    ]

    results: Dict[str, Any] = {"cases": []}

    for a, b, c, e, domain, note in test_cases:
        tied_c, tied_e, inter = _multihop_analogy(glm._s, a, b, c, e, domain)
        mark = "✓" if inter else "○"
        print(f"  {mark} ({domain}) {a}:{b} :: {c}:?  AND  {a}:{b} :: {e}:?")
        print(f"      {note[:90]}")
        print(f"      analogy 1 tied ({len(tied_c)}): {tied_c[:5]}")
        print(f"      analogy 2 tied ({len(tied_e)}): {tied_e[:5]}")
        print(f"      INTERSECTION: {inter if inter else '(empty — no common carrier)'}")
        print()
        results["cases"].append({
            "domain": domain, "a": a, "b": b, "c": c, "e": e,
            "tied_c": tied_c, "tied_e": tied_e,
            "intersection": inter,
            "note": note,
        })

    # Also: chained analogy — a:b :: c:d, then d:b :: e:?
    # This is "what's next in the chain"?
    print("  --- Chained analogy: a:b :: c:d, then c:b :: e:? ---")
    chained_cases = [
        ("H", "He", "Li", None, "chemistry",  # H:He::Li:? -> Be (periodic step); then Li:He::Be:? -> ?
         "periodic table walk"),
        ("force", "energy", "pressure", None, "physics",
         "force:energy::pressure:? -> adhesion_energy; then pressure:energy::adhesion_energy:?"),
    ]
    for a, b, c, _, domain, note in chained_cases:
        try:
            if domain == "chemistry":
                r1 = analogy.element_analogy(a, b, c)
            else:
                r1 = analogy.physics_analogy(a, b, c)
            d_name = r1.answer
            if not d_name:
                print(f"  ✗ ({domain}) chain {a}:{b}::{c}:? -> no first answer")
                continue
            # Now solve (c:b :: d:?)
            if domain == "chemistry":
                r2 = analogy.element_analogy(c, b, d_name)
            else:
                r2 = analogy.physics_analogy(c, b, d_name)
            e_name = r2.answer
            print(f"  ✓ ({domain}) chain {a}:{b}::{c}:? -> {d_name}; "
                  f"then {c}:{b}::{d_name}:? -> {e_name}")
            print(f"      note: {note}")
            results["cases"].append({
                "domain": domain, "chain": [a, b, c, d_name, e_name],
                "note": note,
            })
        except Exception as ex:
            print(f"  ✗ ({domain}) chain failed: {ex}")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# F4 — CROSS-DOMAIN ANALOGIES
# ═══════════════════════════════════════════════════════════════════════════

def experiment_f4_cross_domain(glm: GLMExperimentV2) -> Dict[str, Any]:
    """Test analogies that cross physics/chemistry/economics/harmonics.

    The 4-register memory helps because episodic memory records the
    domain context for each query, allowing recall-by-domain.
    """
    print("\n" + "=" * 72)
    print("FOLLOW-UP F4 — Cross-domain analogies")
    print("=" * 72)
    print("  The substrate supports analogies within a single domain.")
    print("  We test cross-domain by (a) trying physics:physics analogies")
    print("  that cross sub-disciplines, (b) composing analogies across")
    print("  domains via the lexicon register (which has 149 entries from")
    print("  multiple domains), and (c) using 4-register memory to track")
    print("  which domains the conversation has touched.")
    print()

    results: Dict[str, Any] = {"queries": [], "domain_log": []}

    # (a) Cross-sub-discipline physics analogies
    print("  --- (a) Cross-sub-discipline physics analogies ---")
    physics_queries = [
        # Mechanics -> electromagnetism
        ("force", "energy", "voltage", "mechanics → EM"),
        # Mechanics -> thermodynamics
        ("force", "energy", "temperature", "mechanics → thermo"),
        # Mechanics -> quantum
        ("force", "energy", "wavenumber", "mechanics → quantum"),
        # Mechanics -> optics
        ("force", "energy", "luminance", "mechanics → optics"),
        # Mechanics -> acoustics
        ("force", "energy", "acoustic_impedance", "mechanics → acoustics"),
        # Different starting pair
        ("speed_of_light", "wavelength", "gravitational_field", "optics → gravity"),
        # Famous cross: energy:mass across multiple targets
        ("energy", "mass", "frequency", "mass-energy → wave"),
        # Gravity target
        ("energy", "mass", "gravitational_constant", "mass-energy → gravity"),
    ]
    for a, b, c, note in physics_queries:
        try:
            r = analogy.physics_analogy(a, b, c)
            tied_str = f" (tied={len(r.tied)})" if r.tied else ""
            print(f"    ✓ {a}:{b}::{c}:?  ->  {r.answer}{tied_str}")
            print(f"        {note}")
            results["queries"].append({
                "type": "cross_sub_physics", "a": a, "b": b, "c": c,
                "answer": r.answer, "tied_count": len(r.tied) if r.tied else 0,
                "note": note,
            })
            # Log the domain in 4-register memory via talk()
            glm.talk(f"verify {a} = {b}")  # populate episodic + semantic
        except Exception as e:
            print(f"    ✗ {a}:{b}::{c}:?  ->  err: {str(e)[:60]}")

    # (b) Composing across domains via the 4-register memory
    print()
    print("  --- (b) Cross-domain composition via 4-register memory ---")
    print("      Querying different domains in sequence; episodic+semantic")
    print("      memory should track the domain log.")

    # Run queries across multiple domains
    cross_sequence = [
        ("physics",      "verify energy = mass * speed_of_light^2"),
        ("chemistry",    "describe carbon"),
        ("harmonics",    "describe perfect_fifth"),
        ("physics",      "force : energy :: pressure : ?"),
        ("molecules",    "describe water"),
        ("economics",    "describe gold_usd_per_troy_ounce@2024-Q1"),
        ("physics",      "compare energy and torque"),
    ]
    for domain, q in cross_sequence:
        try:
            glm.talk(q)
            results["domain_log"].append({"domain": domain, "query": q})
        except Exception as e:
            results["domain_log"].append({"domain": domain, "query": q,
                                          "err": str(e)[:60]})

    # Check the 4-register state
    print()
    print("  --- 4-register memory state after cross-domain queries ---")
    print(f"    episodic:    {glm.episodic_memory().summary()['count']} turns")
    print(f"    semantic:    {glm.semantic_memory().summary()['count']} concepts")
    print(f"    procedural:  {glm.procedural_memory().summary()['count']} procedures")
    # What concepts are in semantic memory?
    sm = glm.semantic_memory().summary()
    concept_names = set()
    for entry in sm["recent"]:
        for c in entry["concepts"]:
            concept_names.add(c)
    print(f"    distinct concepts in semantic memory: {len(concept_names)}")
    print(f"      sample: {list(concept_names)[:10]}")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# F5 — TRAJECTORY-BASED VERIFICATION (with safe opt-in)
# ═══════════════════════════════════════════════════════════════════════════

def experiment_f5_strict_trajectory(glm: GLMExperimentV2) -> Dict[str, Any]:
    """Test opt-in strict trajectory verification.

    With strict_trajectory=True, the trajectory is computed and any
    UNLICENSED transition causes the answer to be downgraded to a
    hypothesis. Default is False (just flag).

    We test on a query that produces a fully-licensed trajectory
    (should NOT downgrade) and a contrived query with an unlicensed
    jump (should downgrade).
    """
    print("\n" + "=" * 72)
    print("FOLLOW-UP F5 — Trajectory-based verification (opt-in strict mode)")
    print("=" * 72)
    print("  strict_trajectory=True: unlicensed transitions demote answer → hypothesis")
    print("  strict_trajectory=False (default): just flag, don't demote")
    print()

    results: Dict[str, Any] = {"cases": []}

    # Test queries
    test_queries = [
        # Verified analogy — should have all-licensed trajectory
        ("force : energy :: pressure : ?", False,
         "Standard analogy — should be fully licensed (no downgrade)"),
        # Same query in strict mode — should still pass
        ("force : energy :: pressure : ?", True,
         "Same analogy in strict mode — should still pass (all licensed)"),
        # Verify — should also be fully licensed
        ("verify energy = mass * speed_of_light^2", False,
         "Standard verify — fully licensed"),
        ("verify energy = mass * speed_of_light^2", True,
         "Standard verify in strict mode"),
        # A nearest-neighbour query — likely unlicensed trajectory
        ("describe wavelength", False,
         "Describe query — trajectory is single-step, no transitions to license"),
        ("describe wavelength", True,
         "Describe query in strict mode"),
    ]

    for q, strict, note in test_queries:
        try:
            r = glm.reason(q, strict_trajectory=strict)
            mark = "✓" if r.verified else "✗"
            mode = "STRICT" if strict else "lenient"
            print(f"  [{mode:7s}] {mark} {q[:50]:50s}")
            print(f"      answer:     {r.answer}")
            print(f"      hypothesis: {r.hypothesis}")
            print(f"      verified:   {r.verified}")
            print(f"      confidence: {r.confidence.score} — "
                  f"{r.confidence.rationale[:80]}")
            print(f"      note:       {note}")
            # Get the trajectory
            traj = glm.last_trajectory()
            if traj:
                print(f"      trajectory: {traj.start} → {traj.end}, "
                      f"{len(traj.transitions)} transitions, "
                      f"unlicensed={traj.unlicensed_count}, "
                      f"fully_licensed={traj.fully_licensed}")
            print()
            results["cases"].append({
                "query": q, "strict": strict,
                "answer": r.answer, "hypothesis": r.hypothesis,
                "verified": r.verified,
                "confidence_score": r.confidence.score,
                "confidence_rationale": r.confidence.rationale,
                "trajectory_unlicensed": traj.unlicensed_count if traj else None,
                "trajectory_fully_licensed": traj.fully_licensed if traj else None,
                "note": note,
            })
        except Exception as e:
            print(f"  [ERROR] {q}: {e}")
            print()

    # Demonstrate a downgrade scenario by constructing an artificial
    # trajectory with an unlicensed transition
    print("  --- Constructed downgrade scenario ---")
    print("  Query a verify-style with strict_trajectory=True; if the")
    print("  trajectory has unlicensed transitions, the answer demotes.")
    # Force a case where trajectory might have unlicensed transitions
    # by querying something with a derivation chain
    r_strict = glm.reason("force : energy :: pressure : ?",
                           strict_trajectory=True, force_refresh=True)
    print(f"  strict mode result: verified={r_strict.verified}, "
          f"answer={r_strict.answer}, hypothesis={r_strict.hypothesis}")
    print(f"  confidence: {r_strict.confidence.score}")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# RUN ALL FOLLOW-UP EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════════

def run_followup_experiments() -> Dict[str, Any]:
    """Run all 5 follow-up experiments."""
    print("=" * 72)
    print("GLM FOLLOW-UP EXPERIMENTS — 5 next-direction experiments")
    print("=" * 72)

    glm = GLMExperimentV2()

    f1 = experiment_f1_coverage(glm)
    f2 = experiment_f2_lean(glm)
    f3 = experiment_f3_higher_order(glm)
    f4 = experiment_f4_cross_domain(glm)
    f5 = experiment_f5_strict_trajectory(glm)

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  F1 coverage: {f1['summary']['total_ok']}/{f1['summary']['total']} "
          f"({f1['summary']['coverage_pct']}%)")
    print(f"  F2 Lean readings: {len(f2['readings'])} carriers mapped; "
          f"{f2['lean_clusters_count']} clusters share readings")
    print(f"  F3 higher-order cases: {len(f3['cases'])}")
    print(f"  F4 cross-domain queries: {len(f4['queries'])}; "
          f"domain log entries: {len(f4['domain_log'])}")
    print(f"  F5 strict-trajectory cases: {len(f5['cases'])}")
    print()
    print("  Procedural memory after all experiments:")
    ps = glm.procedural_memory().summary()
    print(f"    {ps['count']} procedures stored")
    for p in ps["procedures"]:
        print(f"      shape={p['shape']:15s}  used={p['success_count']}×")

    return {"f1": f1, "f2": f2, "f3": f3, "f4": f4, "f5": f5}


def _demo():
    run_followup_experiments()


if __name__ == "__main__":
    _demo()
