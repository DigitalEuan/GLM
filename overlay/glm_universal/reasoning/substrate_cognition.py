"""``glm_universal.reasoning.substrate_cognition`` -- the supplied list, run.

What this module is
-------------------
The measuring half of ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md``.
``source_material/substrate_native_cognitive_1.txt`` proposes concepts meant
to make the substrate *generate* reasoning rather than route it. That study's
section 2 declares one experiment per concept that can be run. It fixes a
probe set, a control and a pass mark, and it was committed before this module
existed. This module runs those experiments and nothing else.

Every experiment is exact (integers and :class:`~fractions.Fraction`, D7),
seed-free and deterministic. Each returns a dictionary with its figures, its
declared pass mark, whether the mark was met, and the faculty it would move
under D15. :func:`cognition_report` gathers them.

=====  ==========================================  ================================
id     concept of the supplied list                 function
=====  ==========================================  ================================
X1     5, generative branching at the deep hole     :func:`fork_experiment`
X2     8, dynamic abstraction via the dyadic tower  :func:`dyadic_experiment`
X3     1 and 9, TAX as a loss, vacuum seeking       :func:`tax_experiment`
X4     2, reversible backtracking; exact            :func:`reversible_experiment`
       heuristics first
X5     7, wobble-signature analogy                  :func:`wobble_experiment`
X6     rational intervals and a refusal contract    :func:`interval_experiment`
X7     absent derivations with certificates         :func:`certificate_experiment`
X8     homographic (Moebius) transforms             :func:`mobius_experiment`
X9     the Lorentzian lattice ``II_{25,1}``         :func:`lorentzian_experiment`
Y1     the interval layer, reached by a question    :func:`interval_wired_experiment`
Y2     7 refined: rational recognition              :func:`recognition_experiment`
Y3     4 and E5: dimensional derivation             :func:`dimensional_experiment`
Y4     1 and 9 refined: descent inside the coset    :func:`coset_descent_experiment`
Y5     E3: nested holdouts for chemistry estimates  :func:`nested_holdout_experiment`
Y8     R1: the planner as the default path          :func:`planner_default_experiment`
=====  ==========================================  ================================

Y1 to Y5 are round two (Phase 63), declared in section 6 of the study before
this code was written.

The theorems these measurements lean on are in
``RequestProject/GLM/SubstrateCognition.lean``: the fork never answers wrongly
(``GLM.SubstrateCognition.fork_answer_correct``); two offset towers are
distance-faithful where one is not (``GLM.SubstrateCognition.two_towers`` and
``GLM.SubstrateCognition.one_tower_not_faithful``); a lattice-periodic loss
cannot tell a point from its translate
(``GLM.SubstrateCognition.periodic_argmin_translate``); the two gates freeze a
triple whose first bit is clear (``GLM.SubstrateCognition.gates_fix_of_control_clear``);
disjoint intervals decide an order and overlapping ones cannot
(``GLM.SubstrateCognition.interval_lt_sound`` and
``GLM.SubstrateCognition.interval_overlap_undecided``); the Bezout and
impossibility certificates are sound
(``GLM.SubstrateCognition.bezout_certificate_sound`` and
``GLM.SubstrateCognition.no_solution_of_not_dvd``); and the Weyl vector of
``II_{25,1}`` is null (``GLM.SubstrateCognition.weyl_vector_null``).
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from ..substrate import leech2
from ..substrate.golay_decode import (_deterministic_errors, coset_table,
                                      decode_complete, legacy_snap_decode)
from ..substrate.linalg import popcount
from ..substrate.mog import GOLAY_MASKS
from . import analogy as an
from . import certificates as cert
from . import exact_real as xr
from . import wobble as wb
from .coherence import tax_shell0
from .engine import tax_of
#  The interval layer lives in its own module so the planner can read it
#  without importing this one.
from .intervals import (IUPAC_WEIGHTS, Interval, compare_intervals,
                        standard_interval as _standard)

__all__ = [
    "sextet_check", "fork_experiment", "farey", "conflation_level",
    "dyadic_experiment", "tax_experiment", "gate_orbit_distances",
    "reachability_certificate", "reversible_experiment", "wobble_experiment",
    "Interval", "compare_intervals", "IUPAC_WEIGHTS", "interval_experiment",
    "certificate_experiment", "cf_terms", "mobius_stream",
    "mobius_experiment", "lorentzian_experiment", "held_overlap_census",
    "interval_wired_experiment", "RECOGNITION_TICKS", "RECOGNITION_MAX_DEN",
    "recognition_experiment", "dimensional_experiment",
    "coset_descent_experiment", "nested_holdout_experiment",
    "planner_default_experiment", "round_two_report", "WIRED",
    "cognition_report",
]


# ===========================================================================
# X1.  THE DEEP-HOLE FORK
# ===========================================================================

FULL = (1 << 24) - 1


def sextet_check() -> Dict[str, object]:
    """In every weight-4 coset the six leaders are disjoint and cover 24."""
    cosets = sextets = 0
    for leaders in coset_table().values():
        if popcount(leaders[0]) != 4:
            continue
        cosets += 1
        union, disjoint = 0, True
        for mask in leaders:
            if union & mask:
                disjoint = False
            union |= mask
        if len(leaders) == 6 and disjoint and union == FULL:
            sextets += 1
    return {"weight4_cosets": cosets, "sextets": sextets,
            "all_sextets": cosets == sextets == 1771}


def fork_experiment(codewords: int = 64, errors: int = 12) -> Dict[str, object]:
    """Two ambiguous reads of one codeword, each refused alone, intersected."""
    stride = len(GOLAY_MASKS) // codewords
    words = [GOLAY_MASKS[i * stride] for i in range(codewords)]
    errs = _deterministic_errors(4, errors)
    single_refused = truth_in_fork = reads = 0
    answered = correct = wrong = refused = pairs = 0
    legacy_right = legacy_wrong = 0
    for c in words:
        forks = []
        for e in errs:
            d = decode_complete(c ^ e)
            reads += 1
            if d.status == "ambiguous":
                single_refused += 1
            fork = frozenset(d.candidates)
            if c in fork:
                truth_in_fork += 1
            forks.append(fork)
            if legacy_snap_decode(c ^ e)[0] == c:
                legacy_right += 1
            else:
                legacy_wrong += 1
        for i in range(len(errs)):
            for j in range(i + 1, len(errs)):
                pairs += 1
                both = forks[i] & forks[j]
                if len(both) == 1:
                    answered += 1
                    if c in both:
                        correct += 1
                    else:
                        wrong += 1
                else:
                    refused += 1
    # The case the fork must refuse: two tetrads that split one octad.  Both
    # forks then hold the codeword and the codeword plus that octad.
    octad = next(w for w in GOLAY_MASKS if popcount(w) == 8)
    support = [i for i in range(24) if (octad >> i) & 1]
    e1 = sum(1 << i for i in support[:4])
    e2 = sum(1 << i for i in support[4:])
    c0 = GOLAY_MASKS[0]
    shared = frozenset(decode_complete(c0 ^ e1).candidates) & \
        frozenset(decode_complete(c0 ^ e2).candidates)
    return {
        "refusal_witness_shared": len(shared),
        "refusal_witness_is_truth_and_octad": shared == {c0, c0 ^ octad},
        "codewords": codewords, "errors_per_codeword": len(errs),
        "reads": reads, "single_read_refused": single_refused,
        "truth_in_fork": truth_in_fork,
        "double_reads": pairs, "fork_answered": answered,
        "fork_correct": correct, "fork_wrong": wrong,
        "fork_refused": refused,
        "legacy_right": legacy_right, "legacy_wrong": legacy_wrong,
        "chance_rate": Fraction(1, 6),
        "pass_mark": "0 wrong, required; addressing moved if at least half "
                     "of the double reads are answered",
        "passed": wrong == 0 and 2 * answered >= pairs,
        "faculty": "address",
        **{f"sextet_{k}": v for k, v in sextet_check().items()},
    }


# ===========================================================================
# X2.  DYADIC ABSTRACTION
# ===========================================================================

def farey(order: int) -> Tuple[Fraction, ...]:
    """The Farey fractions of ``order`` strictly inside ``(0, 1)``."""
    return tuple(sorted({Fraction(p, q) for q in range(2, order + 1)
                         for p in range(1, q)}))


def _cell(x: Fraction, n: int, offset: Fraction = Fraction(0)) -> int:
    v = x * (1 << n) + offset
    return v.numerator // v.denominator


def conflation_level(x: Fraction, y: Fraction, cap: int = 64) -> int:
    """The deepest ``n <= cap`` at which ``x, y`` share a cell; -1 if none."""
    level = -1
    for n in range(cap + 1):
        if _cell(x, n) != _cell(y, n):
            break
        level = n
    return level


def dyadic_experiment(order: int = 16, levels: int = 7) -> Dict[str, object]:
    """Pairs near enough to share a parent, and whether one tower sees it."""
    pts = farey(order)
    third = Fraction(1, 3)
    rows = []
    one_total = two_total = 0
    for n in range(levels):
        radius = Fraction(1, 3 * (1 << n))
        near = one_miss = two_miss = 0
        for i, x in enumerate(pts):
            for y in pts[i + 1:]:
                if abs(x - y) >= radius:
                    continue
                near += 1
                same_one = _cell(x, n) == _cell(y, n)
                same_two = same_one or _cell(x, n, third) == _cell(y, n, third)
                one_miss += not same_one
                two_miss += not same_two
        rows.append({"level": n, "near_pairs": near,
                     "one_tower_misses": one_miss,
                     "two_tower_misses": two_miss})
        one_total += one_miss
        two_total += two_miss
    # The supplied list's own example.
    a, b = Fraction(1, 7), Fraction(4, 27)
    return {
        "points": len(pts), "rows": tuple(rows),
        "one_tower_misses": one_total, "two_tower_misses": two_total,
        "example_1_7_vs_4_27_level": conflation_level(a, b),
        "pass_mark": "one tower is distance-faithful only if it misses no "
                     "near pair",
        "passed": one_total == 0,
        "two_towers_faithful": two_total == 0,
        "faculty": "none",
    }


# ===========================================================================
# X3.  TAX AS A LOSS
# ===========================================================================

_TAX_POINTS: Tuple[Tuple[Fraction, ...], ...] = (
    tuple([Fraction(1, 3)] * 12 + [Fraction(-2, 5)] * 12),
    tuple(Fraction(k, 7) for k in range(24)),
    tuple([Fraction(3, 2), Fraction(-1, 2)] * 12),
)

_DESCENT_STARTS: Tuple[Tuple[int, ...], ...] = (
    tuple([2] * 8 + [0] * 16),
    tuple([4, 4] + [0] * 22),
    tuple(range(-12, 12)),
    tuple([1, -1] * 12),
    tuple([3] * 24),
    tuple([0] * 23 + [9]),
)


def _descend_shell0(start: Sequence[int]) -> Tuple[Tuple[int, ...], int]:
    """Greedy exact descent on ``HW Y + |v|^2 / 8`` by single-coordinate steps."""
    v = list(start)
    steps = 0
    while True:
        here = tax_shell0(v)
        best, move = here, None
        for i in range(24):
            for d in (-1, 1):
                v[i] += d
                t = tax_shell0(v)
                v[i] -= d
                if t < best:
                    best, move = t, (i, d)
        if move is None:
            return tuple(v), steps
        v[move[0]] += move[1]
        steps += 1


def tax_experiment(translates: int = 3) -> Dict[str, object]:
    """Engine TAX is lattice-periodic; coherence TAX descends to zero."""
    gen = leech2.minimal_vectors()
    lams = [next(gen) for _ in range(translates)]
    invariant = checked = 0
    zero_on_lattice = all(
        an.nearest_lattice_point([Fraction(x) for x in lam]).distance2 == 0
        for lam in lams)
    for v in _TAX_POINTS:
        base = tax_of(an.nearest_lattice_point(list(v)).distance2)
        for lam in lams:
            w = [a + b for a, b in zip(v, lam)]
            checked += 1
            if tax_of(an.nearest_lattice_point(w).distance2) == base:
                invariant += 1
    ends = [_descend_shell0(s) for s in _DESCENT_STARTS]
    to_zero = sum(1 for end, _ in ends if not any(end))
    return {
        "engine_tax_translates_checked": checked,
        "engine_tax_invariant": invariant,
        "engine_tax_zero_on_lattice_points": zero_on_lattice,
        "coherence_starts": len(ends),
        "coherence_descents_to_zero": to_zero,
        "coherence_steps": tuple(s for _, s in ends),
        "pass_mark": "generative only if the minimiser carries information "
                     "about the start beyond its nearest-point decode "
                     "(engine TAX), or beyond nothing (coherence TAX)",
        "passed": not (invariant == checked and to_zero == len(ends)),
        "faculty": "none",
    }


# ===========================================================================
# X4.  REVERSIBLE BACKTRACKING, AND IMPOSSIBILITY FIRST
# ===========================================================================

_BLOCKS = tuple((3 * b, 3 * b + 1, 3 * b + 2) for b in range(8))
_MOVES = tuple((g, b) for b in range(8) for g in ("toffoli", "fredkin"))


def _gate3(gate: str, t: int) -> int:
    """A gate on a 3-bit value ``t = a + 2b + 4c`` (bits in coordinate order)."""
    a, b, c = t & 1, (t >> 1) & 1, (t >> 2) & 1
    if gate == "toffoli":
        c ^= a & b
    elif a:
        b, c = c, b
    return a | (b << 1) | (c << 2)


def _apply(state: int, move: Tuple[str, int]) -> int:
    gate, block = move
    shift = 3 * block
    t = (state >> shift) & 7
    return (state & ~(7 << shift)) | (_gate3(gate, t) << shift)


def gate_orbit_distances() -> Dict[Tuple[int, int], int]:
    """Least number of gate applications taking one triple to another.

    Computed by breadth-first search over the eight 3-bit values under the
    two gates, not stored.
    """
    out: Dict[Tuple[int, int], int] = {}
    for s in range(8):
        frontier, seen, d = [s], {s: 0}, 0
        while frontier:
            d += 1
            nxt = []
            for t in frontier:
                for g in ("toffoli", "fredkin"):
                    u = _gate3(g, t)
                    if u not in seen:
                        seen[u] = d
                        nxt.append(u)
            frontier = nxt
        for t, dist in seen.items():
            out[(s, t)] = dist
    return out


def reachability_certificate(source: int, target: int) -> Optional[int]:
    """The exact least number of moves, or ``None`` with an orbit obstruction."""
    dist = gate_orbit_distances()
    total = 0
    for b in range(8):
        pair = ((source >> 3 * b) & 7, (target >> 3 * b) & 7)
        if pair not in dist:
            return None
        total += dist[pair]
    return total


def _search(source: int, target: int, depth: int) -> Dict[str, object]:
    """Iterative-deepening DFS that backtracks by re-applying the same gate."""
    expanded = restored = unrestored = 0
    for limit in range(depth + 1):
        state = source
        path: List[int] = []
        found = False

        def dfs(level: int) -> bool:
            nonlocal state, expanded, restored, unrestored
            if state == target:
                return True
            if level == limit:
                return False
            for m, move in enumerate(_MOVES):
                before = state          # kept only to audit the undo
                state = _apply(state, move)
                expanded += 1
                path.append(m)
                if dfs(level + 1):
                    return True
                path.pop()
                state = _apply(state, move)     # the undo: the same gate
                if state == before:
                    restored += 1
                else:                            # pragma: no cover
                    unrestored += 1
            return False

        found = dfs(0)
        if found:
            return {"found_depth": limit, "expanded": expanded,
                    "restored": restored, "unrestored": unrestored}
    return {"found_depth": None, "expanded": expanded, "restored": restored,
            "unrestored": unrestored}


def _reversible_pairs(count: int) -> Tuple[Tuple[int, int], ...]:
    out = []
    for i in range(count):
        source = FULL * i // (count - 1)
        if i % 2 == 0:
            target = source
            for k in range(i % 5):
                target = _apply(target, _MOVES[(i + 5 * k) % len(_MOVES)])
        else:
            target = source ^ (1 << (3 * (i % 8)))   # flip a control bit
        out.append((source, target))
    return tuple(out)


def reversible_experiment(count: int = 32, depth: int = 4) -> Dict[str, object]:
    """Search with gate-undo backtracking beside the orbit certificate."""
    agree = disagree = 0
    expanded_search = restored = unrestored = 0
    certified_impossible = 0
    for source, target in _reversible_pairs(count):
        certificate = reachability_certificate(source, target)
        run = _search(source, target, depth)
        expanded_search += run["expanded"]          # type: ignore[operator]
        restored += run["restored"]                  # type: ignore[operator]
        unrestored += run["unrestored"]              # type: ignore[operator]
        if certificate is None:
            certified_impossible += 1
        expected = certificate if certificate is not None \
            and certificate <= depth else None
        if run["found_depth"] == expected:
            agree += 1
        else:
            disagree += 1
    move_bits = (len(_MOVES) - 1).bit_length()
    return {
        "pairs": count, "depth": depth, "moves": len(_MOVES),
        "certificate_agrees": agree, "certificate_disagrees": disagree,
        "certified_impossible": certified_impossible,
        "search_nodes_expanded": expanded_search,
        "certificate_cost_per_pair": 8,
        "undo_restored_exactly": restored, "undo_not_exact": unrestored,
        "path_memory_bits": depth * move_bits + 24,
        "snapshot_memory_bits": (depth + 1) * 24,
        "pass_mark": "0 disagreements between certificate and search, and "
                     "0 restorations that are not exact",
        "passed": disagree == 0 and unrestored == 0,
        "faculty": "refuse",
    }


# ===========================================================================
# X5.  WOBBLE-SIGNATURE ANALOGY
# ===========================================================================

def _columns(bits: Sequence[int]) -> Tuple[object, ...]:
    return (wb.ones_count(bits), wb.transitions(bits),
            wb.longest_run(bits, 0), wb.longest_run(bits, 1),
            wb.mean_run_length(bits))


def wobble_experiment(steps: int = wb.WOBBLE_STEPS) -> Dict[str, object]:
    """Each target against a structureless dyadic decoy within ``2^-40``."""
    rows = []
    same = 0
    for name, _notation, t in wb.signature_targets():
        decoy = Fraction((t * (1 << 40)).numerator // (t * (1 << 40)).denominator,
                         1 << 40)
        a, b = wb.stream_bits(t, steps), wb.stream_bits(decoy, steps)
        identical = _columns(a) == _columns(b)
        same += identical
        rows.append({"name": name, "decoy_matches": identical,
                     "stream_identical": a == b})
    return {
        "targets": len(rows), "decoys_matching": same, "rows": tuple(rows),
        "pass_mark": "structure beyond magnitude only if most decoys are "
                     "separated",
        "passed": 2 * same < len(rows),
        "faculty": "none",
    }


# ===========================================================================
# X6.  RATIONAL INTERVALS AND THE REFUSAL CONTRACT
# ===========================================================================

_ELEMENTS_JSON = (Path(__file__).resolve().parent.parent / "data_objects"
                  / "_data" / "elements_118.json")


def _register_strings() -> Dict[str, str]:
    raw = json.loads(_ELEMENTS_JSON.read_text(encoding="utf-8"))
    return {rec["symbol"]: rec["atomic_weight_u"] for rec in raw["elements"]
            if rec["atomic_weight_u"] is not None}


def interval_experiment() -> Dict[str, object]:
    """The element register against the standard table, as intervals."""
    held = _register_strings()
    rows = []
    point_different = inside = precision_only = inconsistent = 0
    for row in IUPAC_WEIGHTS:
        symbol = row[0]
        standard, central = _standard(row)
        text = held[symbol]
        value = Fraction(text)
        as_held = Interval.as_held(value, "register")
        differs = central is not None and value != central
        point_different += differs
        if standard.contains(value):
            verdict = "consistent"
            inside += 1
        elif standard.overlaps(as_held):
            verdict = "consistent at the register's stated precision"
            precision_only += 1
        else:
            verdict = "inconsistent"
            inconsistent += 1
        rows.append({"symbol": symbol, "register": text,
                     "standard": (standard.lo, standard.hi),
                     "point_differs": differs, "verdict": verdict})
    # Ordering: every consecutive pair of the table, point against interval.
    ordering = refused = disagree = 0
    for r1, r2 in zip(IUPAC_WEIGHTS, IUPAC_WEIGHTS[1:]):
        i1, _ = _standard(r1)
        i2, _ = _standard(r2)
        v1, v2 = Fraction(held[r1[0]]), Fraction(held[r2[0]])
        point = "lt" if v1 < v2 else ("gt" if v1 > v2 else "eq")
        verdict = compare_intervals(i1, i2)
        ordering += 1
        if verdict == "overlap":
            refused += 1
        elif verdict != point:
            disagree += 1
    return {
        "elements": len(rows), "rows": tuple(rows),
        "point_comparison_differs": point_different,
        "inside_standard": inside,
        "consistent_at_stated_precision": precision_only,
        "inconsistent": inconsistent,
        "ordering_questions": ordering, "ordering_refused": refused,
        "ordering_disagreements": disagree,
        "pass_mark": "at least one point-comparison 'wrong' turned into a "
                     "stated-precision verdict, with no wrong ordering",
        "passed": precision_only >= 1 and disagree == 0,
        "faculty": "refuse",
    }


# ===========================================================================
# X7.  ABSENT DERIVATIONS WITH CERTIFICATES
# ===========================================================================

def certificate_experiment(session=None) -> Dict[str, object]:
    """The declared certificate set through the planner and the grammar."""
    from ..evaluation.certificates_heldout import CERTIFICATES
    from ..evaluation.heldout import score_answer
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    planned: Dict[str, int] = {}
    grammar: Dict[str, int] = {}
    for item in CERTIFICATES:
        got = session.ask_planned(item.question)
        v = score_answer(item, got.ok, got.answer or "")
        planned[v] = planned.get(v, 0) + 1
        base = session.ask(item.question)
        w = score_answer(item, base.ok, base.answer or "")
        grammar[w] = grammar.get(w, 0) + 1
    return {
        "questions": len(CERTIFICATES),
        "planner": dict(sorted(planned.items())),
        "grammar": dict(sorted(grammar.items())),
        "worked": cert.certificates_report()["all_checked"],
        "pass_mark": "0 wrong answers, and every declared refusal refused",
        "passed": planned.get("wrong", 0) == 0 and planned.get(
            "correct-refusal", 0) == sum(1 for q in CERTIFICATES
                                         if q.expect is None),
        "faculty": "derive",
    }


# ===========================================================================
# X8.  HOMOGRAPHIC (MOEBIUS) TRANSFORMS ON CONTINUED FRACTIONS
# ===========================================================================

def cf_terms(x: "xr.ExactReal", count: int, start: int = 64) -> Tuple[int, ...]:
    """The first ``count`` certified continued-fraction terms of ``x``.

    Both ends of the interval ``x.at(k) +- 2^-k`` are expanded and only the
    common prefix is kept, so a term is emitted only when every value still
    possible agrees on it. The precision doubles until ``count`` terms are
    certified.
    """
    k = start
    while True:
        mid = x.at(k)
        eps = Fraction(1, 1 << k)
        lo, hi = xr.continued_fraction(mid - eps, count + 2), \
            xr.continued_fraction(mid + eps, count + 2)
        common: List[int] = []
        for a, b in zip(lo[:-1], hi[:-1]):
            if a != b:
                break
            common.append(a)
        if len(common) >= count:
            return tuple(common[:count])
        k *= 2


def mobius_stream(a: int, b: int, c: int, d: int,
                  terms: Sequence[int]) -> Iterator[int]:
    """Gosper's algorithm: the continued fraction of ``(a x + b)/(c x + d)``.

    ``terms`` is the continued fraction of ``x``. A term of the output is
    emitted only when both ends of the range the unread tail allows have the
    same floor and no pole lies between them.
    """
    ingested = False
    for t in terms:
        a, b, c, d = a * t + b, a, c * t + d, c
        ingested = True
        while ingested and c != 0 and c + d != 0 and \
                (c > 0) == (c + d > 0):
            q1 = a // c
            q2 = (a + b) // (c + d)
            if q1 != q2:
                break
            yield q1
            a, b, c, d = c, d, a - q1 * c, b - q1 * d


def _bits(error: Fraction) -> int:
    """The largest ``k`` with ``|error| <= 2^-k`` (64 for an exact hit)."""
    error = abs(error)
    if error == 0:
        return 64
    k = 0
    while error <= Fraction(1, 1 << (k + 1)):
        k += 1
    return k


def mobius_experiment(steps: int = 64) -> Dict[str, object]:
    """The transform checked against the exact-real layer, and the two fuels."""
    reals = (("phi", xr.phi()), ("sqrt 2", xr.parse_real("sqrt(2)")),
             ("e", xr.e()), ("pi", xr.pi()))
    rows = []
    agree = checked = 0
    for name, x in reals:
        terms = cf_terms(x, steps)
        # the transform (2x + 1) / (x + 3), checked convergent by convergent
        out = []
        for q in mobius_stream(2, 1, 1, 3, terms):
            out.append(q)
            if len(out) >= 24:
                break
        target = ((x * 2 + 1).at(200)) / ((x + 3).at(200))
        ok = True
        for conv in xr.convergents(out)[:-1]:
            checked += 1
            # a convergent p/q of the true value lies within 1/q^2 of it
            q = conv.denominator
            if abs(conv - target) < Fraction(1, q * q) + Fraction(1, 1 << 150):
                agree += 1
            else:
                ok = False
        cf_bits = _bits(xr.convergents(terms)[-1] - x.at(400))
        tail = x - terms[0]
        ds_bits = _bits(xr.real_delta_sigma_average(tail, steps)
                        - tail.at(400))
        rows.append({"name": name, "output_terms": len(out),
                     "output_checked": ok, "cf_bits_after_steps": cf_bits,
                     "delta_sigma_bits_after_steps": ds_bits})
    return {
        "steps": steps, "rows": tuple(rows),
        "convergents_checked": checked, "convergents_agree": agree,
        "pass_mark": "the transform's output agrees with the exact-real "
                     "value at every emitted convergent",
        "passed": agree == checked and checked > 0,
        "faculty": "derive",
    }


# ===========================================================================
# X9.  THE LORENTZIAN LATTICE
# ===========================================================================

def lorentzian_experiment() -> Dict[str, object]:
    """The Weyl vector ``(0, 1, ..., 24 | 70)`` of ``II_{25,1}`` is null."""
    space = sum(k * k for k in range(25))
    return {"space_norm": space, "time_norm": 70 * 70,
            "null": space == 70 * 70,
            "signature_even_unimodular": (25 - 1) % 8 == 0,
            "pass_mark": "a first concrete step only; no dynamics claimed",
            "passed": space == 70 * 70, "faculty": "none"}


# ===========================================================================
# ROUND TWO (Phase 63) -- the declarations of section 6 of the study
# ===========================================================================

def _score_set(session, items) -> Dict[str, object]:
    """A declared question set through the planner and through the grammar."""
    from ..evaluation.heldout import score_answer
    planned: Dict[str, int] = {}
    grammar: Dict[str, int] = {}
    for item in items:
        got = session.ask_planned(item.question)
        v = score_answer(item, got.ok, got.answer or "")
        planned[v] = planned.get(v, 0) + 1
        base = session.ask(item.question)
        w = score_answer(item, base.ok, base.answer or "")
        grammar[w] = grammar.get(w, 0) + 1
    refusals = sum(1 for q in items if q.expect is None)
    return {"questions": len(items),
            "planner": dict(sorted(planned.items())),
            "grammar": dict(sorted(grammar.items())),
            "declared_refusals": refusals,
            "set_passed": planned.get("wrong", 0) == 0
            and planned.get("correct-refusal", 0) == refusals}


def _session(session):
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    return session


def held_overlap_census() -> Dict[str, object]:
    """How often the ordering guard (Y1c) could fire on the registers.

    Every pair of elements by atomic weight, and every pair of molecules by
    molar mass, each value read at its held precision: the number of pairs
    whose intervals overlap while their points differ, which is exactly the
    set of orderings the guard turns into refusals.
    """
    out: Dict[str, object] = {}
    from ..data_objects import elements as _el
    weights = [Fraction(e.atomic_weight_u) for e in
               _el.load_element_register() if e.atomic_weight_u is not None]
    out["element_pairs"], out["element_overlaps"] = _overlaps(weights)
    try:
        from ..data_objects import molecules as _mol
        masses = [Fraction(m.molar_mass_u) for m in _mol.load_molecule_register()
                  if getattr(m, "molar_mass_u", None) is not None]
    except (ImportError, AttributeError):             # pragma: no cover
        masses = []
    out["molecule_pairs"], out["molecule_overlaps"] = _overlaps(masses)
    return out


def _overlaps(values: Sequence[Fraction]) -> Tuple[int, int]:
    held = sorted((Interval.as_held(v).lo, Interval.as_held(v).hi, v)
                  for v in values)
    pairs = len(values) * (len(values) - 1) // 2
    hits = 0
    for i, (lo, hi, v) in enumerate(held):
        for lo2, hi2, v2 in held[i + 1:]:
            if lo2 > hi:
                break
            if v2 != v:
                hits += 1
    return pairs, hits


def interval_wired_experiment(session=None) -> Dict[str, object]:
    """Y1: the interval layer reached by a question."""
    from ..evaluation.cognition_heldout import INTERVAL_QUESTIONS
    session = _session(session)
    scored = _score_set(session, INTERVAL_QUESTIONS)
    census = held_overlap_census()
    return {**scored, **{f"guard_{k}": v for k, v in census.items()},
            "pass_mark": "0 wrong on the declared Y1 questions, every "
                         "declared refusal refused, and no answer of the "
                         "existing held-out sets changed",
            "passed": scored["set_passed"],
            "faculty": "derive"}


#: The stream length and the denominator bound of experiment Y2(b).
RECOGNITION_TICKS: int = 512
RECOGNITION_MAX_DEN: int = 16


def recognition_experiment(session=None) -> Dict[str, object]:
    """Y2: rational recognition from a window, and from a quoted decimal."""
    from ..evaluation.cognition_heldout import FRACTION_QUESTIONS
    session = _session(session)
    exact = wrong = missed = 0
    for x in farey(RECOGNITION_MAX_DEN):
        kind, got = cert.recognise_stream(
            xr.delta_sigma_bits(x, RECOGNITION_TICKS), RECOGNITION_MAX_DEN)
        if kind == "rational" and got == x:
            exact += 1
        elif kind == "rational":
            wrong += 1
        else:
            missed += 1
    rows = []
    excluded = decoy_same = 0
    others = [t for t in wb.signature_targets() if t[0] != "1/3"]
    for name, _notation, t in others:
        decoy = Fraction((t * (1 << 40)).numerator
                         // (t * (1 << 40)).denominator, 1 << 40)
        kt, ft = cert.recognise_stream(
            xr.delta_sigma_bits(t, RECOGNITION_TICKS), RECOGNITION_MAX_DEN)
        kd, fd = cert.recognise_stream(
            xr.delta_sigma_bits(decoy, RECOGNITION_TICKS), RECOGNITION_MAX_DEN)
        excluded += kt == "excluded"
        decoy_same += (kt, ft) == (kd, fd)
        rows.append({"name": name, "verdict": kt, "simplest": ft,
                     "decoy_verdict": kd})
    width_ok = Fraction(1, RECOGNITION_TICKS) < Fraction(
        1, RECOGNITION_MAX_DEN ** 2)
    scored = _score_set(session, FRACTION_QUESTIONS)
    farey_n = len(farey(RECOGNITION_MAX_DEN))
    return {
        "ticks": RECOGNITION_TICKS, "max_den": RECOGNITION_MAX_DEN,
        "farey_targets": farey_n, "recognised_exactly": exact,
        "recognised_wrongly": wrong, "not_recognised": missed,
        "window_below_uniqueness_width": width_ok,
        "irrational_targets": len(rows), "certified_excluded": excluded,
        "decoy_same_verdict": decoy_same, "rows": tuple(rows),
        "decimal": scored,
        "pass_mark": "every Farey fraction of order 16 recognised exactly, "
                     "0 wrong, and every non-rational target certified not a "
                     "fraction of denominator at most 16",
        "passed": exact == farey_n and wrong == 0 and excluded == len(rows)
        and scored["set_passed"],
        "faculty": "address",
    }


def dimensional_experiment(session=None) -> Dict[str, object]:
    """Y3: dimensional derivation with certificates, on the declared set."""
    from ..evaluation.cognition_heldout import DIMENSION_QUESTIONS
    session = _session(session)
    scored = _score_set(session, DIMENSION_QUESTIONS)
    return {**scored,
            "pass_mark": "0 wrong on the declared Y3 questions, and every "
                         "declared refusal refused",
            "passed": scored["set_passed"], "faculty": "derive"}


def _golay_basis() -> Tuple[int, ...]:
    """Twelve independent codewords, taken greedily in register order."""
    basis: List[int] = []
    span = {0}
    for w in GOLAY_MASKS:
        if w in span:
            continue
        basis.append(w)
        span |= {s ^ w for s in span}
        if len(basis) == 12:
            break
    return tuple(basis)


def coset_descent_experiment(codewords: int = 64,
                             errors: int = 12) -> Dict[str, object]:
    """Y4: vacuum seeking inside the coset of the word read."""
    per_weight = [tax_shell0([1] * w + [0] * (24 - w)) for w in range(25)]
    monotone = all(a < b for a, b in zip(per_weight, per_weight[1:]))
    stride = len(GOLAY_MASKS) // codewords
    words = [GOLAY_MASKS[i * stride] for i in range(codewords)]
    basis = _golay_basis()
    reads = agree = ties = greedy_reached = 0
    for c in words:
        for weight in range(5):
            for e in _deterministic_errors(weight, errors):
                r = c ^ e
                reads += 1
                best = min(popcount(r ^ w) for w in GOLAY_MASKS)
                argmin = tuple(sorted(w for w in GOLAY_MASKS
                                      if popcount(r ^ w) == best))
                d = decode_complete(r)
                ties += len(argmin) > 1
                if len(argmin) == 1:
                    ok = d.status in ("codeword", "corrected") and \
                        d.corrected == argmin[0]
                else:
                    ok = d.status == "ambiguous" and \
                        tuple(sorted(d.candidates)) == argmin
                # the TAX of the minimiser, computed on the vector itself
                v = r ^ argmin[0]
                ok = ok and tax_shell0([(v >> i) & 1 for i in range(24)]) \
                    == per_weight[best]
                agree += ok
                # greedy descent: add a generator while that lowers TAX
                cur = r
                while True:
                    step = min(basis, key=lambda g: popcount(cur ^ g))
                    if popcount(cur ^ step) < popcount(cur):
                        cur ^= step
                    else:
                        break
                greedy_reached += popcount(cur) == best
    return {
        "tax_monotone_in_weight": monotone, "reads": reads,
        "agree_with_decoder": agree, "ties": ties,
        "greedy_reached_minimum": greedy_reached,
        "pass_mark": "the coset TAX-minimiser agrees with the complete "
                     "decoder on every read",
        "passed": monotone and agree == reads,
        "faculty": "none",
    }


# -- Y5: nested holdouts -----------------------------------------------------

def _loo_linear(pairs: Sequence[Tuple[Fraction, Fraction]]
                ) -> Optional[Fraction]:
    """Leave-one-out mean error of the least-squares line, closed form."""
    from .element_completion import _fit
    n = len(pairs)
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs)
    sxy = sum(x * y for x, y in pairs)
    errors: List[Fraction] = []
    for x, y in pairs:
        rest = _fit((n - 1, sx - x, sy - y, sxx - x * x, sxy - x * y))
        if rest is not None:
            errors.append(abs(y - (rest[0] * x + rest[1])))
    return sum(errors) / len(errors) if errors else None


def _group_predict(known: Dict[int, List[Tuple[int, Fraction]]], group: int,
                   period: int) -> Optional[Fraction]:
    """The group rule of ``element_completion``, over a given known set."""
    pool = known.get(group, [])
    if not pool:
        return None
    below = [k for k in pool if k[0] < period]
    above = [k for k in pool if k[0] > period]
    if below and above:
        low, high = max(below), min(above)
    else:
        near = sorted(below or above,
                      key=lambda k: (abs(k[0] - period), k[0]))[:2]
        if len(near) == 1:
            return near[0][1]
        low, high = sorted(near)
    if high[0] == low[0]:
        return None
    return low[1] + (high[1] - low[1]) * Fraction(period - low[0],
                                                  high[0] - low[0])


def _mean_rest_error(values: Sequence[Fraction]) -> Optional[Fraction]:
    from .element_completion import _mean_error
    return _mean_error(values)


def nested_holdout_experiment() -> Dict[str, object]:
    """Y5: choose the rule again without the held-out element, then score.

    The ordinary report picks each field's rule on the same leave-one-out
    errors it then quotes.  Here every element that carries the field is
    held out in turn; on the remaining elements alone every candidate rule
    (a line on each other field, and the group rule) is scored by the same
    leave-one-out skill and gated the same way; the winner, fitted on the
    remaining elements, predicts the held-out one.  The constant rule (the
    mean of the remaining elements) is scored on the same folds.
    """
    from . import element_completion as ec
    from ..data_objects import elements as _el
    elements = _el.load_element_register()
    positions = ec._positions()
    rows = []
    for field, rule in sorted(ec.admitted_rules().items()):
        have = [e for e in elements if ec._value(e, field) is not None]
        outer_err: List[Fraction] = []
        const_err: List[Fraction] = []
        same_rule = no_rule = no_input = 0
        for held in have:
            rest = [e for e in have if e is not held]
            y_rest = [ec._value(e, field) for e in rest]
            base = _mean_rest_error(y_rest)
            best: Optional[Tuple[Fraction, str, str]] = None
            for predictor in ec.FIELDS:
                if predictor == field:
                    continue
                pairs = [(ec._value(e, predictor), ec._value(e, field))
                         for e in rest if ec._value(e, predictor) is not None]
                if len(pairs) < ec.GATE_MINIMUM:
                    continue
                loo = _loo_linear(pairs)
                pb = _mean_rest_error([y for _, y in pairs])
                if loo is None or not pb:
                    continue
                cand = (loo / pb, "linear", predictor)
                if best is None or cand < best:
                    best = cand
            # the group rule, scored leave-one-out on the rest alone
            known: Dict[int, List[Tuple[int, Fraction]]] = {}
            for e in rest:
                p = positions.get(e.symbol)
                if p is not None:
                    known.setdefault(p.group, []).append(
                        (p.period, ec._value(e, field)))
            g_err: List[Fraction] = []
            for e in rest:
                p = positions.get(e.symbol)
                if p is None:
                    continue
                v = ec._value(e, field)
                pool = {k: [x for x in lst if not (k == p.group and x ==
                                                  (p.period, v))]
                        for k, lst in known.items() if k == p.group}
                pred = _group_predict(pool, p.group, p.period)
                if pred is not None:
                    g_err.append(abs(v - pred))
            if len(g_err) >= ec.GATE_MINIMUM and base:
                cand = (sum(g_err) / len(g_err) / base, "group",
                        "group and period")
                if best is None or cand < best:
                    best = cand
            if best is None or best[0] > ec.GATE_SKILL:
                no_rule += 1
                continue
            same_rule += (best[1], best[2]) == (rule.family, rule.predictor)
            actual = ec._value(held, field)
            if best[1] == "linear":
                xh = ec._value(held, best[2])
                pairs = [(ec._value(e, best[2]), ec._value(e, field))
                         for e in rest if ec._value(e, best[2]) is not None]
                n = len(pairs)
                fit = ec._fit((n, sum(x for x, _ in pairs),
                               sum(y for _, y in pairs),
                               sum(x * x for x, _ in pairs),
                               sum(x * y for x, y in pairs)))
                pred = None if xh is None or fit is None else \
                    fit[0] * xh + fit[1]
            else:
                p = positions.get(held.symbol)
                pred = None if p is None else \
                    _group_predict(known, p.group, p.period)
            if pred is None:
                no_input += 1
                continue
            outer_err.append(abs(actual - pred))
            const_err.append(abs(actual - sum(y_rest) / len(y_rest)))
        nested = (sum(outer_err) / sum(const_err)) if outer_err and \
            sum(const_err) else None
        rows.append({
            "field": field, "rule": f"{rule.family}:{rule.predictor}",
            "reported_skill_3dp": ec.round_to_thousandths(rule.skill),
            "nested_skill_3dp": ec.round_to_thousandths(nested),
            "folds": len(have), "scored_folds": len(outer_err),
            "same_rule_chosen": same_rule, "no_rule_passed": no_rule,
            "inputs_absent": no_input,
            "survives": nested is not None and nested <= ec.GATE_SKILL,
        })
    return {"fields": len(rows), "rows": tuple(rows),
            "surviving": sum(1 for r in rows if r["survives"]),
            "pass_mark": "none: a measurement of how much selection "
                         "flattered each rule",
            "passed": True, "faculty": "none"}


def _contract_outcome(case, ok: bool, answer: str) -> str:
    """One contract case scored by the evaluation harness's own rule."""
    from ..evaluation import harness as _h
    lowered = (answer or "").lower()
    refused = (not ok) or any(m in lowered for m in _h.REFUSAL_MARKERS)
    if case.expect == "refusal":
        return "refused_as_expected" if refused else "wrong_answer"
    if refused:
        return "unexpected_refusal"
    return "wrong_answer" if _h._missing(case, answer) else "correct"


def planner_default_experiment(session=None) -> Dict[str, object]:
    """Y8 (R1): the contract cases through the grammar and through the planner.

    In-process, with the harness's scoring rule.  The same comparison through
    the command line in fresh interpreters is recorded in the study (section
    7); the switch to the planner as the default is licensed only if no
    outcome changes for the worse.  It asks all 177 cases twice and takes
    minutes, so :func:`cognition_report` does not run it; ``tools cognition
    --contract`` does.
    """
    from ..evaluation.cases import CASES
    session = _session(session)
    grammar: Dict[str, int] = {}
    planned: Dict[str, int] = {}
    changed_answers = worse = 0
    for case in CASES:
        g = session.ask(case.question)
        p = session.ask_planned(case.question)
        og = _contract_outcome(case, g.ok, g.answer or "")
        op = _contract_outcome(case, p.ok, p.answer or "")
        grammar[og] = grammar.get(og, 0) + 1
        planned[op] = planned.get(op, 0) + 1
        changed_answers += (g.answer or "") != (p.answer or "")
        worse += og in ("correct", "refused_as_expected") and \
            op not in ("correct", "refused_as_expected")
    return {"cases": len(CASES), "grammar": dict(sorted(grammar.items())),
            "planner": dict(sorted(planned.items())),
            "answers_changed": changed_answers, "outcomes_worse": worse,
            "pass_mark": "no contract case's outcome becomes worse",
            "passed": worse == 0 and planned.get("wrong_answer", 0) == 0,
            "faculty": "none"}


def round_two_report(session=None) -> Dict[str, object]:
    """Every round-two experiment, with its pass mark and faculty."""
    session = _session(session)
    return {
        "Y1": interval_wired_experiment(session),
        "Y2": recognition_experiment(session),
        "Y3": dimensional_experiment(session),
        "Y4": coset_descent_experiment(),
        "Y5": nested_holdout_experiment(),
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

#: The experiments a question put to the machine can reach.  X7 was wired in
#: the first round; round two wires the interval layer (Y1, which carries X6
#: to a question), rational recognition from a quoted decimal (Y2) and
#: dimensional derivation (Y3), all as frames of the typed planner.  The
#: others are measured here and reached by nothing on the runtime's path, so
#: a met pass mark is a candidate for wiring, not a faculty moved.
WIRED: Tuple[str, ...] = ("X6", "X7", "Y1", "Y2", "Y3")


def cognition_report(session=None) -> Dict[str, object]:
    """Every experiment of the study, with its pass mark and faculty."""
    session = _session(session)
    runs = {
        "X1": fork_experiment(),
        "X2": dyadic_experiment(),
        "X3": tax_experiment(),
        "X4": reversible_experiment(),
        "X5": wobble_experiment(),
        "X6": interval_experiment(),
        "X7": certificate_experiment(session),
        "X8": mobius_experiment(),
        "X9": lorentzian_experiment(),
    }
    runs.update(round_two_report(session))
    for key, run in runs.items():
        run["wired"] = key in WIRED
    moved = {k: v["faculty"] for k, v in runs.items()
             if v["passed"] and v["wired"] and v["faculty"] != "none"}
    candidates = {k: v["faculty"] for k, v in runs.items()
                  if v["passed"] and not v["wired"] and v["faculty"] != "none"}
    return {"experiments": runs, "passed": tuple(k for k, v in runs.items()
                                                 if v["passed"]),
            "moved": moved, "met_but_unwired": candidates}
