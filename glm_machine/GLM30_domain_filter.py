# ══════════════════════════════════════════════════════════════════════════════
# §30  DOMAIN FILTER (v3.19.0 — KB recall noise reduction)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   The user feedback identified "Hallucination/KB bleed: References to
#   unrelated 'laws,' '2D Dissonance Matrix,' 'Aspirin,' or physics concepts
#   in pure math contexts" as a key weakness. This module classifies the
#   domain of each query and tells the runtime whether to suppress KB recall
#   entirely (for pure-math queries) or filter recalled entries by domain.
#
#   This addresses Feedback Item #2 (Noise Reduction) from the v3.19 push.
#
# WHAT THIS MODULE DOES
#
#   * `classify_domain(query, qtype, comp_res, sym_res, delib_res) -> str`
#     Returns one of: "pure_math" | "physics" | "chemistry" | "general"
#
#   * `should_suppress_recall(domain) -> bool`
#     Returns True for "pure_math" — KB recall is skipped entirely.
#
#   * `filter_recalled_by_domain(recalled, domain) -> list`
#     For non-pure-math domains, filters out entries whose ubp_id prefix
#     doesn't match the detected domain. E.g. a physics query won't get
#     MOLECULE_* or ELEM_* entries (unless they're directly named in the
#     query).
#
# CLASSIFICATION HEURISTICS
#
#   The classifier uses multiple signals, in priority order:
#
#   1. STRONG math signals (any one → pure_math):
#      - delib_res is not None (deliberation patterns are all olympiad-math)
#      - sym_res with kind in (differentiate, integrate, solve, simplify,
#        partial_diff, taylor, limit, sum) AND no physics keywords
#      - query contains proof markers: "prove", "show that", "demonstrate"
#      - query contains math problem markers: "divisible", "irreducible",
#        "gcd", "lcm", "subset", "triangle", "tetrahedron", "median",
#        "hypotenuse", "balls into boxes", "C(n,k)", "n choose k"
#
#   2. STRONG physics signals (any one → physics):
#      - query contains physics keywords: "hamiltonian", "lagrangian",
#        "wavefunction", "schrodinger", "heisenberg", "weyl", "majorana",
#        "boson", "fermion", "quark", "lepton", "proton", "neutron",
#        "electron", "photon", "gluon", "graviton", "lattice", "golay",
#        "leech", "monster", "anomaly" (in physics context)
#
#   3. STRONG chemistry signals (any one → chemistry):
#      - query contains chemistry keywords: "molecule", "compound",
#        "reaction", "bond", "valence", "atomic", "element", "hydrogen",
#        "helium", "carbon", "oxygen", "nitrogen", "water", "aspirin",
#        "methanol", "benzene"
#
#   4. DEFAULT: "general" (no filtering)
#
#   When signals conflict (e.g. "lattice" is both math and physics), the
#   classifier looks at the broader context: if other math signals are
#   present, it's math; if other physics signals are present, it's physics.
#
# AMBIGUOUS WORDS (handled specially)
#   - "lattice": math (lattice theory) vs physics (crystal lattice) —
#     resolved by context
#   - "anomaly": math (anomalous cancellation) vs physics (Weyl anomaly) —
#     resolved by context
#   - "matrix": math (linear algebra) vs physics (density matrix) —
#     resolved by context
#   - "energy": physics (default) — but in math context ("energy of a
#     graph") it's math
#
# AUTHOR
#   Z.ai v3.19 development push — 2026-07-06
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════════════
#  KEYWORD SETS
# ══════════════════════════════════════════════════════════════════════════════

# Strong math signals — any one of these in a query strongly suggests pure_math
_MATH_KEYWORDS = {
    # Number theory
    "divisible", "irreducible", "gcd", "lcm", "prime", "primality",
    "modulo", "modular", "congruence", "fermat", "chinese remainder",
    # Algebra
    "polynomial", "root", "factor", "factorise", "factorize",
    "quadratic", "cubic", "quartic", "coefficients",
    # Calculus
    "derivative", "integral", "differentiate", "integrate",
    "limit", "taylor", "series", "converge", "diverge",
    # Combinatorics
    "combinatoric", "permutation", "combination", "subset",
    "stars and bars", "balls", "boxes", "n choose k", "c(n,k)",
    "binomial", "pigeonhole",
    # Geometry
    "triangle", "tetrahedron", "median", "hypotenuse", "altitude",
    "circumradius", "inradius", "polygon", "vertices", "edges",
    "pythag", "euclidean", "apollonius", "heron",
    # Linear algebra
    "matrix", "determinant", "eigenvalue", "eigenvector", "trace",
    "rank", "null space", "kernel", "vector space", "linear combination",
    # Proof markers
    "prove", "proof", "show that", "demonstrate", "verify that",
    "hence", "therefore", "thus", "q.e.d", "qed",
    # Math notation markers
    "∀", "∃", "∈", "⊆", "√", "∫", "∑", "∏", "≤", "≥", "≠", "→",
}

# Strong physics signals
_PHYSICS_KEYWORDS = {
    # Quantum mechanics
    "hamiltonian", "lagrangian", "wavefunction", "schrodinger", "schroedinger",
    "heisenberg", "weyl", "majorana", "boson", "fermion", "quark",
    "lepton", "proton", "neutron", "electron", "photon", "gluon",
    "graviton", "spinor", "baryon", "hadron", "meson",
    # Relativity / cosmology
    "schwarzschild", "lorentz", "einstein", "spacetime", "curvature",
    # Solid state / lattice physics
    "brillouin", "reciprocal lattice", "phonon", "bandgap", "band gap",
    # Particle physics
    "qft", "quantum field", "gauge", "yang-mills", "higgs",
    "standard model", "particle physics",
    # UBP-specific physics
    "nrci", "golay", "leech", "monster", "substrate",
    "coherence", "tilt", "manifold",
    # Thermodynamics
    "entropy", "enthalpy", "boltzmann", "maxwell",
    # Physics concepts that default to physics in GLM context
    "energy", "force", "mass", "momentum", "gravity", "electric",
    "magnetic", "electromagnetic", "kinetic", "potential",
}

# Strong chemistry signals
_CHEMISTRY_KEYWORDS = {
    "molecule", "molecular", "compound", "reaction", "reactant",
    "product", "bond", "covalent", "ionic", "valence", "oxidation",
    "reduction", "acid", "base", "ph ", "catalyst", "polymer",
    # Element names (when used in chemistry context)
    "hydrogen", "helium", "lithium", "carbon", "nitrogen", "oxygen",
    "fluorine", "neon", "sodium", "magnesium", "aluminium", "aluminum",
    "silicon", "phosphorus", "sulfur", "chlorine", "argon", "potassium",
    "calcium", "iron", "copper", "zinc", "silver", "gold", "mercury",
    "lead", "uranium",
    # Compound names
    "water", "methanol", "ethanol", "benzene", "aspirin", "glucose",
    "ammonia", "methane", "ethylene", "acetylene", "acetone",
}

# Words that are ambiguous between math and physics — resolved by context
# (Note: "energy", "force", "mass", "momentum" are physics by default in GLM
# context — they're in _PHYSICS_KEYWORDS. Only truly ambiguous words stay here.)
_AMBIGUOUS_KEYWORDS = {
    "lattice", "anomaly", "matrix", "operator", "tensor", "field",
    "symmetry", "phase", "frequency", "wavelength", "amplitude",
    "resonance",
}

# ubp_id prefixes for each domain (used by filter_recalled_by_domain)
_DOMAIN_PREFIXES = {
    "physics":   ("LAW_", "PARTICLE_", "PVE_"),
    "chemistry": ("ELEM_", "MOLECULE_", "REACTION_"),
    "math":      ("MATH_",),
    "general":   (),  # no filtering
}


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════
def classify_domain(query: str,
                    qtype: str = "",
                    comp_res: Optional[Dict] = None,
                    sym_res: Optional[Dict] = None,
                    delib_res: Optional[Dict] = None) -> str:
    """Classify the domain of a query.

    Returns one of: "pure_math" | "physics" | "chemistry" | "general"

    Priority:
      1. Strong deliberation signal → pure_math
      2. Strong symbolic math signal (no physics keywords) → pure_math
      3. Keyword counting with conflict resolution for ambiguous words
      4. Default: "general"
    """
    q = (query or "").lower()

    # ── Signal 1: Deliberation is always pure_math ───────────────────────
    if delib_res is not None:
        return "pure_math"

    # ── Signal 2: Symbolic math with no physics keywords ─────────────────
    if sym_res is not None:
        sym_kind = sym_res.get("computation", {}).get("kind", "")
        # All symbolic kinds are math — check if any physics keywords appear
        physics_in_query = any(kw in q for kw in _PHYSICS_KEYWORDS)
        chemistry_in_query = any(kw in q for kw in _CHEMISTRY_KEYWORDS)
        if not physics_in_query and not chemistry_in_query:
            return "pure_math"

    # ── Signal 3: Compute with pure-math kinds ───────────────────────────
    if comp_res is not None:
        comp_kind = comp_res.get("computation", {}).get("kind", "")
        pure_math_kinds = {"gcd", "lcm", "prime", "factorial", "combination",
                          "power", "arith", "sqrt"}
        physics_in_query = any(kw in q for kw in _PHYSICS_KEYWORDS)
        chemistry_in_query = any(kw in q for kw in _CHEMISTRY_KEYWORDS)
        if comp_kind in pure_math_kinds and not physics_in_query and not chemistry_in_query:
            return "pure_math"

    # ── Signal 4: Keyword counting ───────────────────────────────────────
    math_count = sum(1 for kw in _MATH_KEYWORDS if kw in q)
    physics_count = sum(1 for kw in _PHYSICS_KEYWORDS if kw in q)
    chemistry_count = sum(1 for kw in _CHEMISTRY_KEYWORDS if kw in q)

    # Count ambiguous keywords — assign them to whichever domain is stronger
    ambiguous_in_query = [kw for kw in _AMBIGUOUS_KEYWORDS if kw in q]
    for _ in ambiguous_in_query:
        if physics_count > math_count:
            physics_count += 1
        elif math_count > physics_count:
            math_count += 1
        # If tied, don't assign (leave ambiguous)

    # qtype "proof" is a strong math signal
    if qtype == "proof":
        math_count += 2

    # ── Decide ───────────────────────────────────────────────────────────
    if math_count > 0 and math_count >= max(physics_count, chemistry_count):
        return "pure_math"
    if physics_count > 0 and physics_count >= max(math_count, chemistry_count):
        return "physics"
    if chemistry_count > 0 and chemistry_count >= max(math_count, physics_count):
        return "chemistry"

    return "general"


def should_suppress_recall(domain: str) -> bool:
    """Should KB recall be skipped entirely for this domain?

    True for pure_math — the feedback was that math queries shouldn't get
    chemistry/physics KB recalls at all.
    """
    return domain == "pure_math"


def filter_recalled_by_domain(recalled: List[Dict[str, Any]],
                              domain: str,
                              query_words: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Filter a list of recalled KB entries by domain.

    For "pure_math" — returns [] (caller should have used should_suppress_recall).
    For "physics" — keeps LAW_, PARTICLE_, PVE_ entries; drops ELEM_/MOLECULE_.
    For "chemistry" — keeps ELEM_, MOLECULE_, REACTION_; drops LAW_/PARTICLE_.
    For "general" — keeps everything.

    query_words: if provided, entries whose name or ubp_id directly matches
    a query word are ALWAYS kept (the user explicitly named them).
    """
    if not recalled:
        return []
    if domain == "pure_math":
        return []
    if domain == "general":
        return recalled

    allowed_prefixes = _DOMAIN_PREFIXES.get(domain, ())
    if not allowed_prefixes:
        return recalled

    query_words_lower = {w.lower() for w in (query_words or [])}

    filtered = []
    for entry in recalled:
        ubp_id = entry.get("ubp_id", "")
        name = entry.get("name", "")
        # Always keep entries that directly match a query word
        if name.lower() in query_words_lower or ubp_id.lower() in query_words_lower:
            filtered.append(entry)
            continue
        # Otherwise, check prefix
        if ubp_id.startswith(allowed_prefixes):
            filtered.append(entry)
    return filtered


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM30_domain_filter",
        "version": "3.19.0",
        "operations": ["classify_domain", "should_suppress_recall",
                       "filter_recalled_by_domain"],
        "domains": ["pure_math", "physics", "chemistry", "general"],
        "math_keywords": len(_MATH_KEYWORDS),
        "physics_keywords": len(_PHYSICS_KEYWORDS),
        "chemistry_keywords": len(_CHEMISTRY_KEYWORDS),
        "ambiguous_keywords": len(_AMBIGUOUS_KEYWORDS),
    }


if __name__ == "__main__":
    print("=== GLM30 Domain Filter v3.19.0 — self-test ===")
    print(status())
    print()

    test_cases = [
        # (query, qtype, comp_res, sym_res, delib_res, expected_domain)
        ("Prove that the fraction (21n+4)/(14n+3) is irreducible",
         "proof", None, None,
         {"pattern": "gcd_proof", "answer": "Irreducible (GCD=1)"},
         "pure_math"),
        ("What is gcd(54, 24)?",
         "computation",
         {"computation": {"kind": "gcd"}, "result": {"exact": "6"}},
         None, None, "pure_math"),
        ("Find the determinant of [[1,2,3],[4,5,6],[7,8,10]]",
         "computation",
         {"computation": {"kind": "determinant"}, "result": {"exact": "-3"}},
         None, None, "pure_math"),
        ("differentiate x^3 * sin(x)",
         "computation", None,
         {"computation": {"kind": "differentiate"}, "result": {"exact": "..."}},
         None, "pure_math"),
        ("Tell me about the hamiltonian and time",
         "explanation", None, None, None, "physics"),
        ("Define oxygen",
         "definition", None, None, None, "chemistry"),
        ("What is the chemical element oxygen?",
         "definition", None, None, None, "chemistry"),
        ("How many ways to put 10 balls into 4 boxes?",
         "computation", None, None, None, "pure_math"),
        ("Discuss the weyl anomaly",
         "explanation", None, None, None, "physics"),
        ("What is energy?",
         "definition", None, None, None, "physics"),  # "energy" defaults to physics
        ("Compute the eigenvalues of [[2,0],[0,-1]]",
         "computation",
         {"computation": {"kind": "eigenvalues"}, "result": {"exact": "..."}},
         None, None, "pure_math"),
    ]

    all_ok = True
    for query, qtype, comp, sym, delib, expected in test_cases:
        domain = classify_domain(query, qtype, comp, sym, delib)
        ok = (domain == expected)
        if not ok:
            all_ok = False
        suppress = should_suppress_recall(domain)
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {query[:55]!r}...")
        print(f"         domain={domain!r} expected={expected!r} suppress_recall={suppress}")

    print()
    # Test filter_recalled_by_domain
    print("--- filter_recalled_by_domain tests ---")
    sample_recalled = [
        {"ubp_id": "LAW_ANOMALY_001", "name": "Law of Coherence-Based Anomaly Detection"},
        {"ubp_id": "ELEM_O_008", "name": "Oxygen"},
        {"ubp_id": "MOLECULE_H2O_001", "name": "Water"},
        {"ubp_id": "PARTICLE_ELECTRON_001", "name": "Electron"},
        {"ubp_id": "MATH_PRIME_001", "name": "Prime Number Theorem"},
    ]
    for domain in ["pure_math", "physics", "chemistry", "general"]:
        filtered = filter_recalled_by_domain(sample_recalled, domain)
        print(f"  {domain}: kept {len(filtered)}/{len(sample_recalled)} — "
              f"{[e['ubp_id'] for e in filtered]}")

    print()
    print(f"{'ALL PASS' if all_ok else 'SOME FAILED'}")
