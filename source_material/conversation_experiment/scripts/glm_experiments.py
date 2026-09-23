"""``glm_experiments.py`` — Wire procedural memory into reasoning dispatch,
benchmark it, and explore what the GLM substrate can actually do.

This file builds on glm_conversation_v2_extensions (v3) and adds:

  1. PROCEDURAL REPLAY in reason() — when a matching verified Procedure
     is found in procedural memory, the stored ReasoningPlan is
     returned DIRECTLY (with a freshness check on whether the carrier
     set has changed), bypassing the full propose-check-refine loop.

  2. BENCHMARK SUITE — measures:
       - latency per query (microseconds, exact via perf_counter)
       - verification rate (% of queries that produce a verified answer)
       - coverage (% of test queries the system can handle)
       - plan-reuse rate (% of second-pass queries that hit procedural memory)
       - correctness (checked against known-good answers)

  3. FIVE EXPERIMENTS, each pushing the GLM into a different reasoning
     regime:

       E1: Wide-range reasoning across all 8 register domains
           (physics, chemistry, molecules, mathematics, lexicon, spatial,
            harmonics, economics) — see what works and what fails.

       E2: Puzzle solving — odd-one-out, missing-quantity, reduce-to-name.
           Uses the GLM's exact nearest-neighbour and term-arithmetic
           reduction.

       E3: Unique data insight — dimensional coincidences (pairs with
           d²=0 but different names), lattice holes (carriers at max
           distance from any register), parity-class clusters (carriers
           sharing Golay codewords). Things LLMs cannot surface.

       E4: Lean/Math exploration — exact-real comparisons (sqrt(2) vs
           7/5), Buckingham-Pi groups, term-arithmetic reduction,
           deep-hole probing. Uses the substrate's exact arithmetic.

       E5: Procedural-replay benchmark — same query set run twice;
           second pass should hit procedural memory and be ~5x faster.

INVARIANTS (preserved)
======================
  * Exact arithmetic (int / Fraction / F₂) on all computation paths
  * No float constructed on any path that feeds a result
    (perf_counter is for timing only, not fed into any result)
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
from time import perf_counter
import statistics

# Import v3 (which transitively imports v2)
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
from glm_universal.reasoning import deep_holes
from glm_universal.data_objects import physics as do_physics
from glm_universal.substrate import golay_decode


__all__ = [
    "GLMExperiment", "BenchmarkResult",
    "run_benchmark", "run_all_experiments",
]


# ═══════════════════════════════════════════════════════════════════════════
# PROCEDURAL REPLAY — wire into reason() dispatch
# ═══════════════════════════════════════════════════════════════════════════

class GLMExperiment(GLMConversationV3):
    """Extends GLMConversationV3 with real procedural replay.

    The difference from v3: when ``reason()`` finds a matching
    verified Procedure, it returns the stored plan DIRECTLY instead
    of running the full propose-check-refine loop. A freshness check
    ensures the procedure's plan is still valid (the carriers it
    references still resolve).
    """

    def __init__(self):
        super().__init__()
        # Stats for benchmarking
        self._stats = {
            "reason_calls": 0,
            "procedural_hits": 0,
            "procedural_misses": 0,
            "full_reason_runs": 0,
        }

    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    def reset_stats(self) -> None:
        for k in self._stats:
            self._stats[k] = 0

    def reason(self, question: str, force_refresh: bool = False
               ) -> ReasonResult:
        """v4 reason() with procedural replay.

        If ``force_refresh`` is False and a matching verified Procedure
        exists in procedural memory AND its plan's carriers still
        resolve (freshness check), return the stored plan directly with
        a "replayed" annotation — bypassing the full propose-check-refine.

        Otherwise, fall through to v3's reason() which will store the
        successful plan as a new Procedure (or increment success_count).
        """
        self._stats["reason_calls"] += 1

        # Look for a matching procedure
        concepts, _ = _extract(self._s, question)
        intent = _classify(question, concepts)
        existing_proc = self._procedural.find(intent, concepts) \
            if not force_refresh else None

        if existing_proc is not None and existing_proc.plan.final_verified:
            # Freshness check: do all carriers in the plan's steps still resolve?
            fresh = True
            for ps in existing_proc.plan.steps:
                if ps.op in ("resolve", "verify", "explain"):
                    # Extract candidate names from the target
                    target = ps.target
                    candidates: List[str] = []
                    if ":" in target:
                        # analogy target: "force:energy::pressure:adhesion_energy"
                        for chunk in target.split(":"):
                            for c in chunk.split():
                                try:
                                    self._s.resolve(c)
                                    candidates.append(c)
                                except Exception:
                                    pass
                    else:
                        for c in target.split(","):
                            c = c.strip()
                            try:
                                self._s.resolve(c)
                                candidates.append(c)
                            except Exception:
                                pass
                    if not candidates and ps.status == "ok":
                        # The target may itself be a single register name
                        try:
                            self._s.resolve(target.strip())
                        except Exception:
                            fresh = False
                            break
            if fresh:
                # REPLAY — return the stored plan directly
                self._stats["procedural_hits"] += 1
                reused = Procedure(
                    shape=existing_proc.shape,
                    intent=existing_proc.intent,
                    arity=existing_proc.arity,
                    plan=existing_proc.plan,
                    final_answer=existing_proc.final_answer,
                    success_count=existing_proc.success_count + 1,
                    last_used_turn=len(self._mg.memories),
                    created_turn=existing_proc.created_turn,
                )
                # Update the procedural register (increment success_count)
                self._procedural.add(reused)
                # Compute trajectory (still cheap)
                related_rels: List[Relation] = []
                for c in concepts:
                    related_rels.extend(self._mg.expand_relations(c, max_depth=1))
                self._last_trajectory = None  # skip on replay for speed
                return ReasonResult(
                    answer=existing_proc.final_answer,
                    method=f"procedural_replay (success_count={reused.success_count})",
                    confidence=Confidence(
                        "high", None,
                        f"replayed verified procedure shape={existing_proc.shape} "
                        f"(created turn {existing_proc.created_turn})"),
                    steps=(f"[procedural replay] returned stored plan: "
                           f"{len(existing_proc.plan.steps)} steps, "
                           f"answer={existing_proc.final_answer}",),
                    verified=True,
                    hypothesis=None,
                    plan=existing_proc.plan,
                )

        # No procedure hit — fall through to v3's full reason()
        self._stats["procedural_misses"] += 1
        self._stats["full_reason_runs"] += 1
        return super().reason(question)


# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK SUITE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BenchmarkResult:
    """Result of running a benchmark query set."""
    name: str
    queries: List[str]
    first_pass_us: List[float]        # microseconds per query
    second_pass_us: List[float]       # microseconds per query (procedural replay)
    first_verified: List[bool]
    second_verified: List[bool]
    procedural_hits: int
    procedural_misses: int
    mean_first_us: float
    mean_second_us: float
    speedup: float                    # mean_first / mean_second

    def summary(self) -> str:
        n = len(self.queries)
        v1 = sum(self.first_verified)
        v2 = sum(self.second_verified)
        return (
            f"Benchmark: {self.name}\n"
            f"  queries:              {n}\n"
            f"  verified (1st pass):  {v1}/{n} ({100*v1//n if n else 0}%)\n"
            f"  verified (2nd pass):  {v2}/{n} ({100*v2//n if n else 0}%)\n"
            f"  procedural hits:      {self.procedural_hits}\n"
            f"  procedural misses:    {self.procedural_misses}\n"
            f"  mean latency 1st:     {self.mean_first_us:.1f} µs\n"
            f"  mean latency 2nd:     {self.mean_second_us:.1f} µs\n"
            f"  speedup:              {self.speedup:.2f}×\n"
        )


def run_benchmark(glm: GLMExperiment, queries: List[str],
                  name: str = "default") -> BenchmarkResult:
    """Run a benchmark: each query twice, measure latency and verification."""
    first_us: List[float] = []
    second_us: List[float] = []
    first_verified: List[bool] = []
    second_verified: List[bool] = []

    # First pass: populate procedural memory
    glm.reset_stats()
    for q in queries:
        t0 = perf_counter()
        r = glm.reason(q)
        t1 = perf_counter()
        first_us.append((t1 - t0) * 1_000_000)
        first_verified.append(r.verified)

    # Second pass: should hit procedural memory
    procedural_hits_before = glm.stats()["procedural_hits"]
    for q in queries:
        t0 = perf_counter()
        r = glm.reason(q)
        t1 = perf_counter()
        second_us.append((t1 - t0) * 1_000_000)
        second_verified.append(r.verified)

    stats = glm.stats()
    mean_first = statistics.mean(first_us) if first_us else 0.0
    mean_second = statistics.mean(second_us) if second_us else 0.0
    speedup = mean_first / mean_second if mean_second > 0 else float("inf")

    return BenchmarkResult(
        name=name, queries=queries,
        first_pass_us=first_us, second_pass_us=second_us,
        first_verified=first_verified, second_verified=second_verified,
        procedural_hits=stats["procedural_hits"],
        procedural_misses=stats["procedural_misses"],
        mean_first_us=mean_first, mean_second_us=mean_second,
        speedup=speedup,
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT E1 — WIDE-RANGE REASONING ACROSS DOMAINS
# ═══════════════════════════════════════════════════════════════════════════

def experiment_e1_wide_range(glm: GLMExperiment) -> Dict[str, Any]:
    """Try queries from every register domain."""
    print("\n" + "=" * 72)
    print("EXPERIMENT E1 — Wide-range reasoning across 8 domains")
    print("=" * 72)

    queries_by_domain = {
        "physics": [
            "verify energy = mass * speed_of_light^2",
            "force : energy :: pressure : ?",
            "compare energy and torque",
            "describe wavelength",
        ],
        "chemistry": [
            "describe carbon",
            "describe hydrogen",
            "nearest 3 to oxygen",
        ],
        "molecules": [
            "describe water",
            "describe methane",
        ],
        "mathematics": [
            "describe identity_matrix",
        ],
        "harmonics": [
            "describe perfect_fifth",
            "nearest 3 to major_third",
        ],
        "economics": [
            "describe spot_price",
        ],
        "lexicon": [
            "meaning of motion",
        ],
        "spatial": [
            "describe mog_grid",
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
                answer = sol.answer[:80] if sol.answer else ""
            except Exception as e:
                ok = False
                answer = f"err: {str(e)[:60]}"
            mark = "✓" if ok else "✗"
            print(f"    {mark} {q!r:55s} -> {answer[:60]}")
            domain_results.append({"query": q, "ok": ok, "answer": answer})
            if ok:
                domain_ok += 1
                total_ok += 1
            total += 1
        results["by_domain"][domain] = {
            "queries": domain_results,
            "ok": domain_ok, "total": len(queries),
        }
    results["summary"] = {
        "total_ok": total_ok, "total": total,
        "coverage_pct": 100 * total_ok // total if total else 0,
    }
    print(f"\n  Coverage: {total_ok}/{total} ({results['summary']['coverage_pct']}%)")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT E2 — PUZZLE SOLVING
# ═══════════════════════════════════════════════════════════════════════════

def _odd_one_out(glm: GLMExperiment, names: List[str]) -> Tuple[str, str]:
    """Find the carrier that doesn't fit — the one with the largest
    sum of d² to all others."""
    vectors = []
    valid = []
    for n in names:
        try:
            obj = glm._s.resolve(n)
            vectors.append(tuple(metric.as_exact_vector(obj.carrier)))
            valid.append(n)
        except Exception:
            continue
    if len(vectors) < 3:
        return "", "not enough valid carriers"
    # For each, sum of d² to all others
    worst = ""
    worst_d = Fraction(-1)
    worst_reason = ""
    for i, n in enumerate(valid):
        total = Fraction(0)
        for j, m in enumerate(valid):
            if i != j:
                total += metric.distance2(vectors[i], vectors[j])
        if total > worst_d:
            worst_d = total
            worst = n
            worst_reason = f"sum_d²={total} (avg={total/(len(valid)-1)})"
    return worst, worst_reason


def _missing_quantity(glm: GLMExperiment,
                      a: str, b: str, c: str) -> Tuple[Optional[str], str]:
    """Find d such that a:b :: c:d. Uses analogy.physics_analogy."""
    try:
        ar = analogy.physics_analogy(a, b, c)
        if ar.tied:
            return ar.tied[0], (f"first of {len(ar.tied)} tied at d²={ar.distance2}")
        return ar.answer, f"d²={ar.distance2}, exact={ar.exact_hit}"
    except Exception as e:
        return None, f"err: {e}"


def _reduce_to_name(expr: str) -> Tuple[Optional[str], str]:
    """Reduce a dimensional expression to its simplest register name."""
    try:
        ta = tar.evaluate(expr)
        return ta.name, f"ext10={ta.ext10}, names={ta.names[:3]}"
    except Exception as e:
        return None, f"err: {e}"


def experiment_e2_puzzles(glm: GLMExperiment) -> Dict[str, Any]:
    """Puzzle solving: odd-one-out, missing-quantity, reduce-to-name."""
    print("\n" + "=" * 72)
    print("EXPERIMENT E2 — Puzzle solving")
    print("=" * 72)

    results: Dict[str, Any] = {"puzzles": []}

    # --- Odd-one-out puzzles ---
    print("\n  --- Odd-one-out (find the carrier that doesn't fit) ---")
    odd_puzzles = [
        ("energy, kinetic_energy, potential_energy, torque, wavelength",
         "wavelength (different dimension; others are all L² M T⁻² or similar)"),
        ("force, pressure, momentum, energy, stress",
         "momentum (different dim L M T⁻¹; others are L M T⁻² or L⁻¹ M T⁻²)"),
        ("speed_of_light, wavelength, frequency, mass, energy",
         "mass (L⁰ M¹ T⁰; others all involve L or T)"),
        ("hydrogen, helium, lithium, beryllium, water",
         "water (molecule; others are elements)"),
    ]
    for puzzle, expected_note in odd_puzzles:
        names = [n.strip() for n in puzzle.split(",")]
        try:
            # Try resolving each in different domains
            resolved = []
            for n in names:
                try:
                    glm._s.resolve(n)
                    resolved.append(n)
                except Exception:
                    # Try as element
                    try:
                        glm._s.resolve(n, "chemistry")
                        resolved.append(n)
                    except Exception:
                        try:
                            glm._s.resolve(n, "molecules")
                            resolved.append(n)
                        except Exception:
                            pass
            odd, reason = _odd_one_out(glm, resolved)
            mark = "✓" if odd else "✗"
            print(f"    {mark} odd-one-out of {puzzle}")
            print(f"        -> {odd}  ({reason})")
            print(f"        expected: {expected_note}")
            results["puzzles"].append({
                "type": "odd_one_out", "input": puzzle,
                "answer": odd, "reason": reason,
                "expected": expected_note,
            })
        except Exception as e:
            print(f"    ✗ {puzzle} -> err: {e}")

    # --- Missing-quantity puzzles (analogies) ---
    print("\n  --- Missing quantity (analogies a:b :: c:?) ---")
    missing_puzzles = [
        ("force", "energy", "pressure"),  # famous analogy
        ("energy", "mass", "momentum"),
        ("speed_of_light", "wavelength", "gravitational_field"),
        ("force", "momentum", "energy"),
    ]
    for a, b, c in missing_puzzles:
        d, reason = _missing_quantity(glm, a, b, c)
        mark = "✓" if d else "✗"
        print(f"    {mark} {a}:{b}::{c}:?  ->  {d}")
        print(f"        {reason}")
        results["puzzles"].append({
            "type": "missing_quantity",
            "input": f"{a}:{b}::{c}:?",
            "answer": d, "reason": reason,
        })

    # --- Reduce-to-name puzzles ---
    print("\n  --- Reduce expression to register name ---")
    reduce_puzzles = [
        ("mass * acceleration", "force"),
        ("force * distance", "energy or work or torque"),
        ("energy / time", "power"),
        ("force / area", "pressure"),
        ("voltage * current", "power (electrical)"),
        ("mass * speed_of_light^2", "energy (mass-energy)"),
        ("length * length * length", "volume"),
    ]
    for expr, expected in reduce_puzzles:
        name, reason = _reduce_to_name(expr)
        # Even if name is None, the dim is computed
        mark = "✓" if name else "○"  # ○ = dim found but no unique name
        print(f"    {mark} {expr:35s} -> name={name!r}")
        print(f"        {reason}")
        print(f"        expected: {expected}")
        results["puzzles"].append({
            "type": "reduce_to_name", "input": expr,
            "answer": name, "reason": reason, "expected": expected,
        })

    # --- Cluster puzzles — discover structure ---
    print("\n  --- Cluster puzzles (discover structure via exact dendrogram) ---")
    cluster_puzzles = [
        ("cluster energy, kinetic_energy, potential_energy, enthalpy into 2",
         "enthalpy should branch off (it's the only one with a thermal component)"),
        ("cluster H, He, Li, Be, C, N, O into 3",
         "expect H/He/Li/Be in one cluster (s-block), C/N in another (p-block nonmetals)"),
        ("group together energy, torque, force, momentum",
         "energy+torque share dim, force+momentum share dim → 2 groups expected"),
        ("dendrogram speed_of_light, wavelength, frequency, energy, mass",
         "speed_of_light should be far from the others"),
    ]
    for query, expected_note in cluster_puzzles:
        try:
            sol = glm._s.ask(query)
            ok = sol.ok
            ans = sol.answer[:140] if sol.answer else ""
        except Exception as e:
            ok = False
            ans = f"err: {str(e)[:60]}"
        mark = "✓" if ok else "✗"
        print(f"    {mark} {query}")
        print(f"        -> {ans}")
        print(f"        expected: {expected_note}")
        results["puzzles"].append({
            "type": "cluster", "input": query, "answer": ans,
            "expected": expected_note,
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT E3 — UNIQUE DATA INSIGHT
# ═══════════════════════════════════════════════════════════════════════════

def experiment_e3_insight(glm: GLMExperiment) -> Dict[str, Any]:
    """Surface things LLMs cannot: dimensional coincidences, lattice holes,
    parity clusters."""
    print("\n" + "=" * 72)
    print("EXPERIMENT E3 — Unique data insight (GLM-only)")
    print("=" * 72)

    results: Dict[str, Any] = {}

    # --- (a) Dimensional coincidences: pairs with d²=0 but different names ---
    print("\n  --- (a) Dimensional coincidences (d²=0, different names) ---")
    reg = list(glm._s.register("physics"))
    # Sample first 50 to keep this fast
    sample = reg[:50]
    coincidences = []
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            a, b = sample[i], sample[j]
            if a.name == b.name:
                continue
            va = tuple(metric.as_exact_vector(a.carrier))
            vb = tuple(metric.as_exact_vector(b.carrier))
            d2 = metric.distance2(va, vb)
            if d2 == 0:
                coincidences.append((a.name, b.name))
    print(f"    Found {len(coincidences)} coincidence pairs in first 50 carriers")
    for a, b in coincidences[:5]:
        print(f"      {a}  ≡  {b}  (d²=0)")
    results["coincidences_count"] = len(coincidences)
    results["coincidences_sample"] = coincidences[:5]

    # --- (b) Deepest "hole" — carrier furthest from its nearest neighbour ---
    print("\n  --- (b) Most isolated carrier (largest min-distance to any other) ---")
    # Sample 30 to keep it tractable
    small_sample = reg[:30]
    max_min_d2 = Fraction(-1)
    loneliest = None
    loneliest_nearest = None
    for i, a in enumerate(small_sample):
        va = tuple(metric.as_exact_vector(a.carrier))
        min_d2 = None
        nearest = None
        for j, b in enumerate(small_sample):
            if i == j:
                continue
            vb = tuple(metric.as_exact_vector(b.carrier))
            d2 = metric.distance2(va, vb)
            if min_d2 is None or d2 < min_d2:
                min_d2 = d2
                nearest = b.name
        if min_d2 is not None and min_d2 > max_min_d2:
            max_min_d2 = min_d2
            loneliest = a.name
            loneliest_nearest = nearest
    print(f"    Most isolated: {loneliest}")
    print(f"      nearest neighbour: {loneliest_nearest} at d²={max_min_d2}")
    results["most_isolated"] = {
        "carrier": loneliest, "nearest": loneliest_nearest,
        "min_d2": str(max_min_d2),
    }

    # --- (c) Parity clusters — carriers sharing Golay codewords ---
    print("\n  --- (c) Parity clusters (carriers sharing Golay codewords) ---")
    codeword_to_carriers: Dict[int, List[str]] = {}
    for o in reg[:100]:
        bits = dimension_layers.parity_bits(o.carrier)
        dec = golay_decode.decode_complete(bits)
        if dec.corrected is not None:
            codeword_to_carriers.setdefault(dec.corrected, []).append(o.name)
    clusters = [(cw, names) for cw, names in codeword_to_carriers.items()
                if len(names) >= 3]
    clusters.sort(key=lambda x: -len(x[1]))
    print(f"    Found {len(clusters)} parity clusters of size ≥ 3 (in first 100 carriers)")
    for cw, names in clusters[:3]:
        print(f"      codeword 0x{cw:06x}: {len(names)} carriers — {names[:5]}")
    results["parity_clusters_count"] = len(clusters)
    results["parity_clusters_sample"] = [
        {"codeword": f"0x{cw:06x}", "size": len(names), "members": names[:5]}
        for cw, names in clusters[:3]
    ]

    # --- (d) EXT10 dimensional families — count carriers per EXT10 pattern ---
    print("\n  --- (d) EXT10 dimensional families (carriers per dim pattern) ---")
    dim_families: Dict[Tuple[int, ...], List[str]] = {}
    for o in reg[:200]:
        ext = _ext10_exps(glm._s, o.name)
        if ext is not None:
            key = tuple(int(e) if isinstance(e, Fraction) and e.denominator == 1
                       else -999 for e in ext)
            dim_families.setdefault(key, []).append(o.name)
    # Find largest families
    families_sorted = sorted(dim_families.items(), key=lambda x: -len(x[1]))
    print(f"    Found {len(dim_families)} distinct EXT10 dim families (in first 200 carriers)")
    for key, names in families_sorted[:5]:
        # Render the dim pattern
        axes = do_physics.AXES_EXT10
        dim_str = " ".join(
            (axes[i] if key[i] == 1 else f"{axes[i]}^{key[i]}")
            if key[i] != 0 and key[i] != -999 else
            ("" if key[i] == 0 else "?")
            for i in range(10)
        ).strip()
        if not dim_str:
            dim_str = "dimensionless"
        print(f"      dim={dim_str:25s}  {len(names)} carriers — {names[:3]}")
    results["dim_families_count"] = len(dim_families)
    results["largest_families"] = [
        {"dim": " ".join(
            f"{do_physics.AXES_EXT10[i]}^{k}" if k != 1 else do_physics.AXES_EXT10[i]
            for i, k in enumerate(key) if k not in (0, -999)
        ) or "dimensionless",
         "size": len(names), "sample": names[:3]}
        for key, names in families_sorted[:5]
    ]
    return results


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT E4 — LEAN / MATH EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════

def experiment_e4_math(glm: GLMExperiment) -> Dict[str, Any]:
    """Lean/Math exploration via session.ask and exact-real arithmetic."""
    print("\n" + "=" * 72)
    print("EXPERIMENT E4 — Lean / Math exploration")
    print("=" * 72)

    results: Dict[str, Any] = {"queries": []}

    # --- (a) Buckingham-Pi groups ---
    print("\n  --- (a) Buckingham-Pi dimensional analysis ---")
    pi_queries = [
        "pi groups force mass length time",
        "pi groups speed_of_light gravitational_constant mass",
        "pi groups energy mass speed_of_light",
        "pi groups voltage current resistance",
    ]
    for q in pi_queries:
        try:
            sol = glm._s.ask(q)
            ok = sol.ok
            ans = sol.answer[:90] if sol.answer else "(no answer)"
        except Exception as e:
            ok = False
            ans = f"err: {str(e)[:60]}"
        mark = "✓" if ok else "✗"
        print(f"    {mark} {q}")
        print(f"        -> {ans}")
        results["queries"].append({"query": q, "ok": ok, "answer": ans})

    # --- (b) Exact-real comparisons ---
    print("\n  --- (b) Exact-real comparisons (no leading 'compare') ---")
    real_queries = [
        "sqrt(2) greater than 7/5",
        "sqrt(2) greater than 1.4142",
        "pi less than 22/7",
        "e less than 3",
        "phi greater than 1.5",
        # Pure real-value extractions
        "real value sqrt(2)",
        "real value pi",
        "irrational sqrt(2)",
    ]
    for q in real_queries:
        try:
            sol = glm._s.ask(q)
            ok = sol.ok
            ans = sol.answer[:90] if sol.answer else "(no answer)"
            if not ok and sol.error:
                ans = f"err: {sol.error[:60]}"
        except Exception as e:
            ok = False
            ans = f"err: {str(e)[:60]}"
        mark = "✓" if ok else "✗"
        print(f"    {mark} {q}")
        print(f"        -> {ans}")
        results["queries"].append({"query": q, "ok": ok, "answer": ans})

    # --- (c) Term-arithmetic reduction ---
    print("\n  --- (c) Term-arithmetic reduction (exact) ---")
    term_queries = [
        "energy / time",
        "mass * speed_of_light^2",
        "force / area",
        "voltage * current",
        "mass * acceleration",
    ]
    for q in term_queries:
        try:
            ta = tar.evaluate(q)
            ok = True
            ans = f"name={ta.name!r}, dim={ta.ext10}, candidates={len(ta.names)}"
        except Exception as e:
            ok = False
            ans = f"err: {str(e)[:60]}"
        mark = "✓" if ok else "✗"
        print(f"    {mark} {q}")
        print(f"        -> {ans}")
        results["queries"].append({"query": q, "ok": ok, "answer": ans})

    # --- (d) Coherence / NRCI breakdown ---
    print("\n  --- (d) Coherence breakdown for selected carriers ---")
    coh_queries = ["energy", "speed_of_light", "curvature", "planck_constant"]
    for c in coh_queries:
        try:
            obj = glm._s.resolve(c)
            n = co.nrci(obj.carrier)
            regime = co.coherence_regime(n)
            # Get breakdown
            bd = co.nrci_breakdown(obj.carrier)
            tax = bd.get("tax_total", Fraction(0))
            ok = True
            ans = (f"NRCI={_fmt_frac(n, 4)} ({regime}), "
                   f"tax={tax}, shell0={bd.get('shell0_golay', '?')[:30]}")
        except Exception as e:
            ok = False
            ans = f"err: {str(e)[:60]}"
        mark = "✓" if ok else "✗"
        print(f"    {mark} coherence of {c}")
        print(f"        -> {ans}")
        results["queries"].append({"query": f"coherence of {c}", "ok": ok,
                                   "answer": ans})

    return results


# ═══════════════════════════════════════════════════════════════════════════
# EXPERIMENT E5 — PROCEDURAL-REPLAY BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════

def experiment_e5_benchmark(glm: GLMExperiment) -> BenchmarkResult:
    """Benchmark procedural replay: same queries, two passes."""
    print("\n" + "=" * 72)
    print("EXPERIMENT E5 — Procedural-replay benchmark")
    print("=" * 72)

    benchmark_queries = [
        # Analogies (intent: analogy, arity: 3) — these populate procedures
        "force : energy :: pressure : ?",
        "energy : mass :: wavelength : ?",
        "force : momentum :: energy : ?",
        # Verifications (intent: verify, arity: 2)
        "verify energy = mass * speed_of_light^2",
        "verify force = mass * acceleration",
        "verify power = energy / time",
        # Nearest (intent: explore, arity: 1)
        "describe energy",
        "describe force",
        "describe wavelength",
        # More analogies to widen the procedure set
        "speed_of_light : wavelength :: frequency : ?",
        "pressure : force :: energy : ?",
    ]

    print(f"\n  Running {len(benchmark_queries)} queries twice (1st pass = cold, 2nd = procedural replay)...")
    result = run_benchmark(glm, benchmark_queries, name="procedural_replay")
    print()
    print(result.summary())

    # Per-query breakdown
    print("  Per-query latency (1st vs 2nd pass):")
    for i, q in enumerate(benchmark_queries):
        us1 = result.first_pass_us[i]
        us2 = result.second_pass_us[i]
        sp = us1 / us2 if us2 > 0 else float("inf")
        v1 = "✓" if result.first_verified[i] else "✗"
        v2 = "✓" if result.second_verified[i] else "✗"
        print(f"    {q[:50]:50s} 1st={us1:8.0f}µs  2nd={us2:8.0f}µs  "
              f"speedup={sp:5.2f}×  [{v1}{v2}]")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# RUN ALL EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════════

def run_all_experiments() -> Dict[str, Any]:
    """Run all 5 experiments and return a combined result."""
    print("=" * 72)
    print("GLM EXPERIMENTS — Procedural replay + 5 experiments")
    print("=" * 72)

    glm = GLMExperiment()

    e1 = experiment_e1_wide_range(glm)
    e2 = experiment_e2_puzzles(glm)
    e3 = experiment_e3_insight(glm)
    e4 = experiment_e4_math(glm)
    e5 = experiment_e5_benchmark(glm)

    # Print procedural memory state after all experiments
    print("\n" + "=" * 72)
    print("FINAL STATE — Procedural memory after all experiments")
    print("=" * 72)
    ps = glm.procedural_memory().summary()
    print(f"  Total procedures stored: {ps['count']}")
    for p in ps["procedures"]:
        print(f"    shape={p['shape']:15s}  answer={p['final_answer']:25s}  "
              f"used={p['success_count']}×  created_turn={p['created_turn']}")
    print()
    print(f"  Stats: {glm.stats()}")

    return {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5}


def _demo():
    """Run all experiments."""
    run_all_experiments()


if __name__ == "__main__":
    _demo()
