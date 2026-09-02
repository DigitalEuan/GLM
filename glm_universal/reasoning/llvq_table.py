"""``glm_universal.reasoning.llvq_table`` -- the LLVQ lookup table.

The gap this closes
-------------------
:mod:`glm_universal.reasoning.llvq` says, in its own docstring, what it does
not do:

    It does not implement the full ``O(1)`` lookup table that the directive
    envisions.  That requires a precomputed shell table indexed by the first
    few binary digits of the input, which is a substantial engineering
    project.

and ``MASTER_PLAN.md`` Phase 24 names it as the first candidate for the next
round: *the lattice quantiser is the hot path of every address, and it is
currently a search*.  This module is that table, and the search it replaces
is :func:`glm_universal.reasoning.analogy.nearest_lattice_point`, which
enumerates the ``2 x 4,096`` congruence cosets of ``Lambda`` on every call.

What the table is
-----------------
Not a table of answers -- a table of *structure*.  The Golay code's 4,096
codewords are, under the MOG alignment this package already carries, exactly
the words that

1. cast a hexacode word as their six GF(4) column labels;
2. have all six column parities equal, to one bit ``p``; and
3. have top-row parity equal to that same ``p``.

:func:`characterisation_report` checks all three over all 4,096 codewords and
counts the classes: **64 hexacode words x 2 parities = 128 classes of 32
codewords each**, which is 4,096 with nothing left over, so the three
conditions do not merely hold -- they *are* the code.

Inside a column, ``(label, parity, top bit)`` determines the 4-bit pattern
uniquely -- 4 x 2 x 2 = 16 patterns for 16 values -- so the table
:data:`PATTERN_TABLE` is a 16-entry lookup, and a class is fixed by six of
its entries.  This is the sense in which the decode is a lookup rather than a
scan: the six column labels are read off the hexacode word, the pattern of
each column is read out of a 16-entry table, and the only freedom left is one
top bit per column under a parity constraint.

How the decode uses it
----------------------
The reference decoder minimises, over the whole code,

    ``cost(w) = base_cost + sum_{i in w} delta_i``  (+ a ``+-4`` repair when
    the ``sum mod 8`` condition fails)

which is a *linear* function of the word plus a nonnegative repair.  Because
the code splits into 128 classes and a class's minimum is a six-term min-sum
under one parity constraint, every class minimum costs about six comparisons
to compute.  The decoder then

* computes all 128 class minima (:func:`class_minima`);
* visits the classes in increasing minimum, expanding a class only while its
  minimum does not exceed the best total found so far;
* inside an expanded class enumerates its 32 words, evaluating exactly what
  the reference evaluates -- the same repair, the same lexicographic
  tie-break on the decoded point.

The bound is sound because the repair is nonnegative, so a class whose
minimum already exceeds the incumbent contains no word that can beat it.
The answer is therefore not an approximation and not a certificate that
sometimes fires: it is *the same point the reference returns, always*, which
is what :func:`agreement_report` and :func:`corpus_report` measure.

Is it ``O(1)``?
---------------
Honestly: it is constant-*bounded* rather than constant.  The table work is
fixed -- 96 column costs, 128 class minima -- and does not grow with the
lattice; the expansion is data-dependent, and its worst case is the whole
code.  So the figure to quote is the *measured* one, and
:func:`search_cost_report` measures it: classes expanded, words evaluated and
codeword-cost additions, against the 4,096 words and 49,152 additions the
reference spends on every call.  Quoting "O(1)" without that measurement
would be the kind of claim directive D6 exists to prevent.

Everything here is exact ``Fraction`` / integer arithmetic; no float is
constructed anywhere in this module.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, mog
from ..substrate.linalg import popcount
from . import metric
from .analogy import LatticeAnalogyResult, _round_to_residue

__all__ = [
    "N_COORDS", "N_CLASSES", "CLASS_SIZE",
    "PATTERN_TABLE", "pattern_table",
    "class_of_codeword", "codewords_of_class",
    "characterisation_report",
    "column_costs", "class_minima",
    "DecodeTrace", "nearest_lattice_point_table", "decode_with_trace",
    "reference_operation_counts", "search_cost_report",
    "agreement_report", "corpus_report", "llvq_table_report",
]

N_COORDS = 24
N_CLASSES = 128
CLASS_SIZE = 32


# ===========================================================================
# 1.  THE TABLE
# ===========================================================================

def _build_pattern_table() -> Dict[Tuple[int, int, int], int]:
    """``(label, parity, top bit) -> 4-bit column pattern``.

    Built from :data:`glm_universal.substrate.mog.COLUMN_LABEL`, so it cannot
    drift away from the alignment the rest of the package uses.  The map is a
    bijection onto the 16 patterns; the assertion says so rather than assuming
    it.
    """
    table: Dict[Tuple[int, int, int], int] = {}
    for value in range(16):
        key = (mog.COLUMN_LABEL[value], popcount(value) & 1, value & 1)
        if key in table:                                # pragma: no cover
            raise AssertionError(
                "llvq_table: (label, parity, top) is not a key on the "
                "16 column patterns")
        table[key] = value
    if len(table) != 16:                                # pragma: no cover
        raise AssertionError("llvq_table: the pattern table is not complete")
    return table


#: ``(label, parity, top bit) -> 4-bit column pattern``.  The whole table.
PATTERN_TABLE: Dict[Tuple[int, int, int], int] = _build_pattern_table()


def pattern_table() -> Dict[Tuple[int, int, int], int]:
    """A copy of :data:`PATTERN_TABLE`, for callers that want to inspect it."""
    return dict(PATTERN_TABLE)


#: ``CELL[col][row]`` -- the coordinate index in MOG cell ``(row, col)``.
CELL: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(mog.cell_of(row, col) for row in range(4)) for col in range(6))

#: ``COLUMN_MASK[col][value]`` -- the 24-bit mask of a column pattern.
COLUMN_MASK: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(sum(1 << CELL[col][row] for row in range(4) if (value >> row) & 1)
          for value in range(16))
    for col in range(6))

#: The 64 hexacode words, in the package's own order.
HEXACODE_WORDS: Tuple[Tuple[int, ...], ...] = mog.HEXACODE.words

#: The 128 classes, as ``(hexacode word, parity)``.
CLASSES: Tuple[Tuple[Tuple[int, ...], int], ...] = tuple(
    (word, parity) for word in HEXACODE_WORDS for parity in (0, 1))


def _column_values(mask: int) -> Tuple[int, ...]:
    """The six 4-bit column values of a 24-bit mask, in the MOG alignment."""
    return tuple(sum(((mask >> CELL[col][row]) & 1) << row for row in range(4))
                 for col in range(6))


def class_of_codeword(mask: int) -> Tuple[Tuple[int, ...], int]:
    """The ``(hexacode word, parity)`` class of a 24-bit mask.

    Defined for any mask; it is a *class of the code* only when the mask is a
    codeword, which :func:`characterisation_report` is what checks.
    """
    values = _column_values(int(mask))
    labels = tuple(mog.COLUMN_LABEL[v] for v in values)
    return labels, popcount(values[0]) & 1


def codewords_of_class(word: Sequence[int], parity: int) -> Tuple[int, ...]:
    """The 32 codewords of one class, built out of the table alone.

    Six columns, each with two patterns -- top bit 0 or 1 -- and the top bits
    constrained to have parity ``parity``.  Nothing is enumerated over the
    code.
    """
    labels = tuple(int(x) for x in word)
    if len(labels) != 6 or any(not 0 <= x < 4 for x in labels):
        raise ValueError("codewords_of_class: a hexacode word is six GF(4) "
                         "labels")
    if parity not in (0, 1):
        raise ValueError("codewords_of_class: parity is 0 or 1")
    out: List[int] = []
    for tops in product((0, 1), repeat=6):
        if sum(tops) % 2 != parity:
            continue
        mask = 0
        for col in range(6):
            mask |= COLUMN_MASK[col][PATTERN_TABLE[(labels[col], parity,
                                                    tops[col])]]
        out.append(mask)
    return tuple(sorted(out))


def characterisation_report() -> Dict[str, object]:
    """The three conditions, checked over all 4,096 codewords, and counted.

    The count is the point: 128 classes of 32 is 4,096, so the conditions are
    not just necessary -- there is no room for a word that satisfies them
    without being a codeword.
    """
    shadow_failures = 0
    parity_failures = 0
    top_failures = 0
    sizes: Dict[Tuple[Tuple[int, ...], int], int] = {}
    for codeword in mog.GOLAY_MASKS:
        values = _column_values(codeword)
        labels = tuple(mog.COLUMN_LABEL[v] for v in values)
        parities = tuple(popcount(v) & 1 for v in values)
        tops = sum((v & 1) for v in values) % 2
        if labels not in mog.HEXACODE:
            shadow_failures += 1
        if len(set(parities)) != 1:
            parity_failures += 1
        elif tops != parities[0]:
            top_failures += 1
        key = (labels, parities[0])
        sizes[key] = sizes.get(key, 0) + 1
    rebuilt = 0
    rebuild_failures = 0
    for word, parity in CLASSES:
        members = codewords_of_class(word, parity)
        rebuilt += len(members)
        if any(not mog.GOLAY.is_codeword(m) for m in members):
            rebuild_failures += 1
        if sorted(members) != sorted(
                m for m in mog.GOLAY_MASKS
                if class_of_codeword(m) == (word, parity)):
            rebuild_failures += 1
    return {
        "codewords": len(mog.GOLAY_MASKS),
        "hexacode_words": len(HEXACODE_WORDS),
        "classes": len(CLASSES),
        "classes_seen": len(sizes),
        "class_size": sorted(set(sizes.values())),
        "shadow_failures": shadow_failures,
        "column_parity_failures": parity_failures,
        "top_row_parity_failures": top_failures,
        "rebuilt_codewords": rebuilt,
        "rebuild_failures": rebuild_failures,
        "classes_times_size": len(CLASSES) * CLASS_SIZE,
        "accounts_for_the_code": (
            shadow_failures == 0 and parity_failures == 0
            and top_failures == 0 and rebuild_failures == 0
            and len(sizes) == N_CLASSES
            and set(sizes.values()) == {CLASS_SIZE}
            and len(CLASSES) * CLASS_SIZE == len(mog.GOLAY_MASKS)),
        "reading": (
            "Every Golay codeword casts a hexacode word, has all six column "
            "parities equal and has top-row parity equal to them; the 128 "
            "(hexacode word, parity) classes hold 32 codewords each, and "
            "128 x 32 = 4096, so the three conditions characterise the code "
            "rather than merely holding on it."),
    }


# ===========================================================================
# 2.  THE COLUMN COSTS AND THE CLASS MINIMA
# ===========================================================================

def column_costs(delta: Sequence) -> Tuple[Tuple[Fraction, ...], ...]:
    """``[col][value] -> sum of delta over the pattern's set cells``.

    96 entries, built with 6 x 16 x 4 = 384 conditional additions and no
    reference to the code at all.
    """
    d = [x if isinstance(x, Fraction) else Fraction(x) for x in delta]
    if len(d) != N_COORDS:
        raise ValueError(f"column_costs: expected {N_COORDS} coordinates")
    return tuple(
        tuple(sum((d[CELL[col][row]] for row in range(4)
                   if (value >> row) & 1), Fraction(0))
              for value in range(16))
        for col in range(6))


def _class_minimum(costs: Sequence[Sequence[Fraction]],
                   word: Sequence[int], parity: int) -> Fraction:
    """The least ``sum_{i in w} delta_i`` over the 32 words of one class.

    Per column the two patterns differ only in their top bit, so the choice
    is six independent minima under one parity constraint; when the cheap
    choices have the wrong parity the correction is the smallest of the six
    differences, which is exactly one comparison per column.
    """
    total = Fraction(0)
    tops = 0
    smallest_gap: Optional[Fraction] = None
    for col in range(6):
        low = costs[col][PATTERN_TABLE[(word[col], parity, 0)]]
        high = costs[col][PATTERN_TABLE[(word[col], parity, 1)]]
        if high < low:
            total += high
            tops ^= 1
            gap = low - high
        else:
            total += low
            gap = high - low
        if smallest_gap is None or gap < smallest_gap:
            smallest_gap = gap
    if tops != parity:
        assert smallest_gap is not None
        total += smallest_gap
    return total


def class_minima(delta: Sequence) -> Tuple[Tuple[Fraction, Tuple[int, ...],
                                                 int], ...]:
    """``(minimum, hexacode word, parity)`` for all 128 classes, sorted."""
    costs = column_costs(delta)
    rows = [(_class_minimum(costs, word, parity), word, parity)
            for word, parity in CLASSES]
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return tuple(rows)


# ===========================================================================
# 3.  THE DECODER
# ===========================================================================

class DecodeTrace:
    """What the table route spent, for one call.

    Counted, not estimated: ``classes_expanded`` is how many of the 128
    classes were opened, ``words_evaluated`` how many of the 4,096 codewords
    had their cost formed, and ``codeword_additions`` the additions those
    costs took -- six per word against the reference's one per set
    coordinate.
    """

    __slots__ = ("classes_expanded", "words_evaluated", "codeword_additions",
                 "class_minimum_additions", "column_cost_additions",
                 "points_built")

    def __init__(self) -> None:
        self.classes_expanded = 0
        self.words_evaluated = 0
        self.codeword_additions = 0
        self.class_minimum_additions = 0
        self.column_cost_additions = 0
        self.points_built = 0

    def as_dict(self) -> Dict[str, int]:
        return {name: getattr(self, name) for name in self.__slots__}

    @property
    def total_additions(self) -> int:
        """Every addition the route made, table build included."""
        return (self.codeword_additions + self.class_minimum_additions
                + self.column_cost_additions)


def _decode_branch(v: Sequence[Fraction], m: int,
                   incumbent: Optional[Tuple[Fraction, List[int]]],
                   trace: DecodeTrace
                   ) -> Optional[Tuple[Fraction, List[int]]]:
    """One congruence class of ``Lambda``, decoded through the table."""
    r0, r1 = m % 4, (m + 2) % 4
    base = [_round_to_residue(value, r0) for value in v]
    alt = [_round_to_residue(value, r1) for value in v]
    base_cost = sum((b[1] for b in base), Fraction(0))
    delta = [alt[i][1] - base[i][1] for i in range(N_COORDS)]
    step = [alt[i][0] - base[i][0] for i in range(N_COORDS)]
    base_sum = sum(b[0] for b in base)
    target = (4 * m) % 8

    costs = column_costs(delta)
    trace.column_cost_additions += 6 * 16 * 4

    # The two companions of the cost table: how far a pattern moves the
    # coordinate sum modulo 8, and the cheapest +-4 repair inside it.
    steps: List[List[int]] = []
    repairs: List[List[Tuple[Fraction, int]]] = []
    for col in range(6):
        step_row: List[int] = []
        repair_row: List[Tuple[Fraction, int]] = []
        for value in range(16):
            moved = 0
            best: Optional[Tuple[Fraction, int]] = None
            for row in range(4):
                i = CELL[col][row]
                if (value >> row) & 1:
                    moved += step[i]
                    penalty = alt[i][2]
                else:
                    penalty = base[i][2]
                if best is None or (penalty, i) < best:
                    best = (penalty, i)
            assert best is not None
            step_row.append(moved % 8)
            repair_row.append(best)
        steps.append(step_row)
        repairs.append(repair_row)

    best = incumbent
    for minimum, word, parity in class_minima(delta):
        trace.class_minimum_additions += 6
        if best is not None and base_cost + minimum > best[0]:
            break
        trace.classes_expanded += 1
        patterns = [(PATTERN_TABLE[(word[col], parity, 0)],
                     PATTERN_TABLE[(word[col], parity, 1)])
                    for col in range(6)]
        for tops in product((0, 1), repeat=6):
            if sum(tops) % 2 != parity:
                continue
            trace.words_evaluated += 1
            trace.codeword_additions += 6
            values = [patterns[col][tops[col]] for col in range(6)]
            cost = base_cost + sum((costs[col][values[col]]
                                    for col in range(6)), Fraction(0))
            if best is not None and cost > best[0]:
                continue
            mask = 0
            for col in range(6):
                mask |= COLUMN_MASK[col][values[col]]
            point = [alt[i][0] if (mask >> i) & 1 else base[i][0]
                     for i in range(N_COORDS)]
            trace.points_built += 1
            if (base_sum + sum(steps[col][values[col]]
                               for col in range(6))) % 8 != target:
                penalty, index = min(repairs[col][values[col]]
                                     for col in range(6))
                cost += penalty
                x = point[index]
                up, down = (v[index] - (x + 4)) ** 2, (v[index] - (x - 4)) ** 2
                point[index] = x + 4 if up <= down else x - 4
            if best is None or cost < best[0] or (
                    cost == best[0] and point < best[1]):
                best = (cost, point)
    return best


def decode_with_trace(vector: Sequence
                      ) -> Tuple[LatticeAnalogyResult, DecodeTrace]:
    """The nearest Leech point through the table, and what it cost."""
    v = metric.as_exact_vector(vector)
    trace = DecodeTrace()
    best: Optional[Tuple[Fraction, List[int]]] = None
    for m in (0, 1):
        best = _decode_branch(v, m, best, trace)
    assert best is not None
    cost, point = best
    if not leech2.in_leech(point):                       # pragma: no cover
        raise AssertionError(
            "llvq_table: the decoded point fails in_leech -- the class table "
            "and the lattice definition have diverged")
    d2 = cost / metric.GRIESS_SCALE
    cls = leech2.class_of(point)
    return (LatticeAnalogyResult(
        target=v, point=tuple(point), distance2=d2, in_leech=True,
        leech_class=cls, norm2=leech2.norm2(point),
        is_2a_axis=leech2.is_type2_class(cls), exact_hit=d2 == 0), trace)


def nearest_lattice_point_table(vector: Sequence) -> LatticeAnalogyResult:
    """The exact nearest point of ``Lambda``, decoded through the table.

    Equal to :func:`glm_universal.reasoning.analogy.nearest_lattice_point`
    point for point -- same objective, same repair, same tie-break -- with
    the 4,096-word scan replaced by the class table and a bound.
    """
    return decode_with_trace(vector)[0]


# ===========================================================================
# 4.  WHAT IT COSTS, MEASURED
# ===========================================================================

def reference_operation_counts() -> Dict[str, object]:
    """The scan's fixed cost per congruence class, counted over the code."""
    additions = sum(popcount(w) for w in mog.GOLAY_MASKS)
    return {
        "codewords": len(mog.GOLAY_MASKS),
        "codeword_cost_additions": additions,
        "closed_form": N_COORDS * (1 << 11),
        "matches_closed_form": additions == N_COORDS * (1 << 11),
        "congruence_classes": 2,
        "additions_per_call": 2 * additions,
    }


class _Sweep:
    """A fixed deterministic integer sequence -- not the ``random`` module.

    The same linear congruential walk
    :mod:`glm_universal.reasoning.fwht_decode` uses, for the same reason: a
    figure that moves between runs cannot be checked.
    """

    _A = 6364136223846793005
    _C = 1442695040888963407
    _M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = seed % self._M

    def below(self, bound: int) -> int:
        self.state = (self.state * self._A + self._C) % self._M
        return (self.state >> 33) % bound

    def between(self, low: int, high: int) -> int:
        return low + self.below(high - low)


def sweep_vectors(samples: int, seed: int, denominator: int = 4
                  ) -> List[List[Fraction]]:
    """``samples`` deterministic rational 24-vectors, spread over the box."""
    rng = _Sweep(seed)
    out: List[List[Fraction]] = []
    for _ in range(samples):
        out.append([Fraction(rng.between(-12 * denominator,
                                         12 * denominator + 1), denominator)
                    for _ in range(N_COORDS)])
    return out


def _register_vectors(limit: int = 60) -> List[Tuple[str, List[Fraction]]]:
    """Carriers the machine actually decodes, taken from the registers."""
    from ..data_objects import elements as do_elements
    from ..data_objects import physics as do_physics

    out: List[Tuple[str, List[Fraction]]] = []
    for source in (do_physics.physics_objects(), do_elements.element_objects()):
        for obj in source:
            out.append((obj.name, [Fraction(c) for c in obj.carrier]))
            if len(out) >= limit:
                return out
    return out


def search_cost_report(samples: int = 40, seed: int = 20260901
                       ) -> Dict[str, object]:
    """What the table route spends against what the scan spends, measured.

    Both figures are counted inside the run: the reference's is the exact
    number of codeword-cost additions the scan makes, which is a constant of
    the code, and the table route's is what its own trace recorded.
    """
    reference = reference_operation_counts()
    classes = 0
    words = 0
    additions = 0
    calls = 0
    worst_classes = 0
    worst_words = 0
    for vector in sweep_vectors(samples, seed):
        _, trace = decode_with_trace(vector)
        calls += 1
        classes += trace.classes_expanded
        words += trace.words_evaluated
        additions += trace.total_additions
        worst_classes = max(worst_classes, trace.classes_expanded)
        worst_words = max(worst_words, trace.words_evaluated)
    per_call_words = Fraction(words, calls)
    per_call_additions = Fraction(additions, calls)
    return {
        "calls": calls,
        "samples": samples,
        "seed": seed,
        "reference_words_per_call": 2 * reference["codewords"],
        "reference_additions_per_call": reference["additions_per_call"],
        "table_classes_per_call": Fraction(classes, calls),
        "table_words_per_call": per_call_words,
        "table_additions_per_call": per_call_additions,
        "worst_classes_in_a_call": worst_classes,
        "worst_words_in_a_call": worst_words,
        "words_ratio": Fraction(2 * reference["codewords"]) / per_call_words,
        "additions_ratio": (Fraction(reference["additions_per_call"])
                            / per_call_additions),
        "classes_available_per_call": 2 * N_CLASSES,
        "reading": (
            "The table route's work is data-dependent and its worst case is "
            "the whole code, so the honest figure is the measured one: the "
            "words it forms a cost for, per call, against the 8,192 the scan "
            "forms."),
    }


def agreement_report(samples: int = 24, seed: int = 20260901
                     ) -> Dict[str, object]:
    """The table route against the scan, point for point.

    Three populations: the deterministic sweep, the carriers the registers
    actually hold, and a handful of vectors chosen to sit on the awkward
    boundaries -- the origin, a half-integer vector where every coordinate is
    equidistant from two residues, and a lattice point itself.
    """
    from .analogy import nearest_lattice_point

    checks = 0
    mismatches: List[Dict[str, object]] = []

    def _check(label: str, vector: Sequence) -> None:
        nonlocal checks
        checks += 1
        want = nearest_lattice_point(vector)
        got = nearest_lattice_point_table(vector)
        if (got.point != want.point or got.distance2 != want.distance2
                or got.leech_class != want.leech_class
                or got.norm2 != want.norm2
                or got.exact_hit != want.exact_hit
                or got.is_2a_axis != want.is_2a_axis):
            mismatches.append({"label": label,
                               "reference": list(want.point),
                               "table": list(got.point)})

    for index, vector in enumerate(sweep_vectors(samples, seed)):
        _check(f"sweep[{index}]", vector)
    for name, vector in _register_vectors():
        _check(f"register:{name}", vector)
    edge_cases: Tuple[Tuple[str, List[Fraction]], ...] = (
        ("origin", [Fraction(0)] * N_COORDS),
        ("all halves", [Fraction(1, 2)] * N_COORDS),
        ("all ones", [Fraction(1)] * N_COORDS),
        ("all twos", [Fraction(2)] * N_COORDS),
        ("ramp", [Fraction(i, 3) for i in range(N_COORDS)]),
        ("one big coordinate",
         [Fraction(37) if i == 5 else Fraction(0) for i in range(N_COORDS)]),
        ("a lattice point",
         [Fraction(4) if i < 2 else Fraction(0) for i in range(N_COORDS)]),
    )
    for label, vector in edge_cases:
        _check(label, vector)
    return {
        "checked": checks,
        "mismatches": len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "agrees": not mismatches,
        "populations": ("deterministic sweep", "register carriers",
                        "boundary cases"),
    }


def corpus_report(limit: Optional[int] = None) -> Dict[str, object]:
    """Lean addresses, decoded both ways, and required to be the same.

    This is the subtractive test Phase 24 asks for: the address book is what
    the quantiser is the hot path *of*, so the table earns the hot path only
    if the corpus comes out unchanged.  ``limit`` decodes the first ``limit``
    declarations in name order rather than all of them, which is what the
    report subject and the test suite use; ``None`` is the whole corpus, and
    the study document quotes that run.
    """
    from .analogy import nearest_lattice_point
    from . import lean_address as la

    features = la.feature_table()
    names = sorted(features)
    if limit is not None:
        names = names[:limit]
    unchanged = 0
    changed: List[str] = []
    words = 0
    classes = 0
    for name in names:
        scaled = [Fraction(int(value) * la.SCALE)
                  for value in features[name]]
        want = tuple(int(c) for c in nearest_lattice_point(scaled).point)
        got, trace = decode_with_trace(scaled)
        words += trace.words_evaluated
        classes += trace.classes_expanded
        if tuple(int(c) for c in got.point) == want:
            unchanged += 1
        else:
            changed.append(name)
    total = len(names)
    return {
        "corpus_declarations": len(features),
        "declarations": total,
        "limit": limit,
        "addresses_unchanged": unchanged,
        "addresses_changed": len(changed),
        "changed_names": tuple(changed[:5]),
        "all_unchanged": unchanged == total and not changed,
        "table_words_per_call": Fraction(words, total) if total else None,
        "table_classes_per_call": Fraction(classes, total) if total else None,
        "reference_words_per_call": 2 * len(mog.GOLAY_MASKS),
    }


def llvq_table_report(samples: int = 24, seed: int = 20260901
                      ) -> Dict[str, object]:
    """Everything above, in one call: the subject behind ``report llvq``."""
    return {
        "characterisation": characterisation_report(),
        "cost": search_cost_report(samples=samples, seed=seed),
        "agreement": agreement_report(samples=samples, seed=seed),
        "reference": reference_operation_counts(),
        "table_entries": len(PATTERN_TABLE),
        "hexacode_words": len(HEXACODE_WORDS),
        "classes": N_CLASSES,
        "class_size": CLASS_SIZE,
    }
