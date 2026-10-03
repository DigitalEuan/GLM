"""``glm_universal.reasoning.second_view`` -- one carrier, read through several views.

The question
------------
Phase 65 carried the six candidates of a deep-hole Golay read as a fork and
resolved it, among other ways, by a **second reading**: the fork of another
read of the same carrier.  X1 measured it (4,224 of 4,224 double reads, 0
wrong) and the dialect wired it as ``agree`` -- but only a caller who already
held two reads could use it.  ``studies/SECOND_VIEW_STUDY.md`` (Phase 96,
round 8 of the order of work) asks for the runtime to produce the second view
itself, declares nine marks before this module existed
(:mod:`glm_universal.evaluation.second_view_cases`), and
:func:`second_view_report` measures them.

The object
----------
A :class:`FramedRegister` stores one codeword in several **views**.  View
``k`` holds the codeword rotated down by ``k`` coordinates; it is read back by
rotating up by ``k``.  A **common-mode burst** -- one error on the same stored
positions of every view -- is read through view ``k`` as ``rot(e, k)``, so the
frames are what make the views differ.  A read carries the fork of view 0 and
prunes it by the fork of every further view (the second-reading stage of
:class:`~glm_universal.reasoning.carried_fork.CarriedFork`, with the reason
naming the frame); nothing is chosen by order.

What is proved rather than measured is in
``RequestProject/GLM/SecondView.lean``: the fork of a four-error read is the
truth and the truth plus each octad through the error, so several views leave
exactly the truth and the truth plus each octad through the union of their
errors; one second frame -- any permutation whatever -- leaves some burst
open; the frames ``(0, 1, 3)`` leave none; and the soft reading made of the
views' mean ranks a fork exactly as the sum of view distances does, whose
minimum is the intersection.

Exactness: integers and :class:`~fractions.Fraction` only.  Determinism: no
random source; every probe is a stride or a census.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import second_view_cases as C
from ..evaluation import unpacking_cases as U
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from .carried_fork import CarriedFork, carry, escalate, x1_probe

__all__ = [
    "N", "FULL", "FRAMES", "rot", "store_views", "align", "read_views",
    "soft_mean", "FramedRegister", "OCTADS", "octads_through",
    "v1_two_views", "v2_three_views", "v3_single_frames", "v4_x1_register",
    "v5_inside_radius", "weight5_report", "v6_composition",
    "v7_soft_channel", "x1_three_views_post_hoc", "second_view_report",
    "read_on_demand", "r1_on_demand_common", "r2_on_demand_inside",
    "r3_on_demand_weight5", "fresh_probe", "r4_r6_independent",
    "r7_frame_census", "on_demand_report",
]

N = 24
FULL = (1 << N) - 1

#: The declared frames of the framed register (rotation offsets).
FRAMES: Tuple[int, ...] = C.FRAMES

#: The assumption every view-stage elimination rests on.
ONE_CARRIER = ("every view is a read of one stored carrier, each within "
               "coset weight 4")


# ===========================================================================
# 1.  THE FRAMES
# ===========================================================================

def rot(word: int, k: int) -> int:
    """Rotate a 24-bit word up by ``k``: bit ``i`` moves to ``(i + k) mod 24``."""
    k %= N
    return ((word << k) | (word >> (N - k))) & FULL


def store_views(codeword: int, frames: Sequence[int] = FRAMES
                ) -> Tuple[int, ...]:
    """The stored words of ``codeword``: view ``k`` holds it rotated down by
    ``k``."""
    if codeword not in GOLAY_SET:
        raise ValueError(f"store_views: {codeword:#x} is not a Golay codeword")
    return tuple(rot(codeword, -k) for k in frames)


def align(stored: int, k: int) -> int:
    """A stored word of view ``k`` read back in the canonical frame."""
    return rot(stored, k)


def read_views(views: Sequence[int], frames: Sequence[int] = FRAMES
               ) -> CarriedFork:
    """Read one carrier through its views, in frame order.

    The fork of view 0 is carried; every further view prunes it to the
    candidates its own fork allows (the second-reading stage), and the ledger
    names the frame that removed each candidate.
    """
    if not views:
        raise ValueError("read_views: at least one view is needed")
    if len(views) > len(frames):
        raise ValueError(f"read_views: {len(views)} views for "
                         f"{len(frames)} frames")
    aligned = [align(w, k) for w, k in zip(views, frames)]
    fork = carry(aligned[0])
    for k, word in zip(frames[1:], aligned[1:]):
        allowed = frozenset(carry(word).candidates)
        fork = fork.prune(
            "second reading", lambda c, a=allowed: c in a,
            f"not a nearest codeword of view {k} (frame rotation {k}, read "
            f"back as {word:#08x})", ONE_CARRIER)
    return fork


def read_on_demand(views: Sequence[int], frames: Sequence[int] = FRAMES,
                   first: int = 2) -> Tuple[CarriedFork, int]:
    """Read one carrier through its views, taking a further view only while
    the fork is still open (Phase 97).

    The first ``first`` views are always read; each further view is read
    only when the views so far leave more than one live candidate.  Inside
    the fault model (every view within coset weight 4 of the carrier) the
    carrier is in every view's fork, so once the fork is resolved a further
    view can only keep it: the answer is the answer of reading every view,
    and ``RequestProject/GLM/OnDemandView.lean`` states it.  Outside the
    fault model a further view could have refused what the first views
    answered, so the saving has a price there, which the study measures.
    Returns the fork and the number of views read.
    """
    if not views:
        raise ValueError("read_on_demand: at least one view is needed")
    if len(views) > len(frames):
        raise ValueError(f"read_on_demand: {len(views)} views for "
                         f"{len(frames)} frames")
    taken = min(max(first, 1), len(views))
    fork = read_views(views[:taken], frames[:taken])
    while fork.status == "open" and taken < len(views):
        k = frames[taken]
        word = align(views[taken], k)
        allowed = frozenset(carry(word).candidates)
        fork = fork.prune(
            "second reading", lambda c, a=allowed: c in a,
            f"not a nearest codeword of view {k} (frame rotation {k}, read "
            f"back as {word:#08x}; read on demand because the fork was "
            "open)", ONE_CARRIER)
        taken += 1
    return fork, taken


def soft_mean(views: Sequence[int], frames: Sequence[int] = FRAMES
              ) -> Tuple[Fraction, ...]:
    """The machine's own soft reading: the mean of the aligned views,
    coordinate by coordinate."""
    aligned = [align(w, k) for w, k in zip(views, frames)]
    n = len(aligned)
    return tuple(Fraction(sum((a >> j) & 1 for a in aligned), n)
                 for j in range(N))


@dataclass
class FramedRegister:
    """One codeword held in several views; a read takes every view.

    ``inject`` applies a common-mode burst (the same stored positions in
    every view); ``inject_each`` gives each view its own error.
    """

    codeword: int
    frames: Tuple[int, ...] = FRAMES
    stored: Tuple[int, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.stored:
            self.stored = store_views(self.codeword, self.frames)

    def inject(self, burst: int) -> "FramedRegister":
        return FramedRegister(self.codeword, self.frames,
                              tuple(w ^ burst for w in self.stored))

    def inject_each(self, errors: Sequence[int]) -> "FramedRegister":
        if len(errors) != len(self.stored):
            raise ValueError("inject_each: one error per view")
        return FramedRegister(self.codeword, self.frames,
                              tuple(w ^ e for w, e in zip(self.stored, errors)))

    def read(self) -> CarriedFork:
        return read_views(self.stored, self.frames)

    def read_on_demand(self) -> Tuple[CarriedFork, int]:
        """The read with the third view on demand: ``(fork, views read)``."""
        return read_on_demand(self.stored, self.frames)


# ===========================================================================
# 2.  THE OCTADS, FOR THE PREDICTIONS
# ===========================================================================

OCTADS: Tuple[int, ...] = tuple(c for c in GOLAY_MASKS
                                if bin(c).count("1") == 8)


def octads_through(u: int) -> int:
    """How many octads contain the support of ``u``."""
    if bin(u).count("1") > 8:
        return 0
    return sum(1 for o in OCTADS if u & o == u)


def _tetrads() -> Tuple[int, ...]:
    return tuple(sum(1 << i for i in s) for s in combinations(range(N), 4))


def _bursts(weight: int) -> Tuple[int, ...]:
    return tuple(sum(1 << i for i in s)
                 for s in combinations(range(N), weight))


def probe_codewords(limit: Optional[int] = None) -> Tuple[int, ...]:
    """X1's codeword probe: every 64th codeword of the sorted 4,096."""
    words = tuple(GOLAY_MASKS[i * C.CODEWORD_STRIDE]
                  for i in range(len(GOLAY_MASKS) // C.CODEWORD_STRIDE))
    return words if limit is None else words[:limit]


# ===========================================================================
# 3.  THE MARKS
# ===========================================================================

def v1_two_views(limit: Optional[int] = None) -> Dict[str, object]:
    """V1: the two-view register's live count, against the prediction."""
    frames = C.PAIR_FRAMES
    tets = _tetrads()
    predicted = {e: 1 + octads_through(e | rot(e, frames[1])) for e in tets}
    reads = wrong = mismatched = resolved = truth_missing = 0
    for c in probe_codewords(limit):
        stored = store_views(c, frames)
        for e in tets:
            fork = read_views([w ^ e for w in stored], frames)
            reads += 1
            if c not in fork.live:
                truth_missing += 1
            if len(fork.live) != predicted[e]:
                mismatched += 1
            if fork.status == "resolved":
                resolved += 1
                if fork.value != c:
                    wrong += 1
    open_bursts = sum(1 for v in predicted.values() if v > 1)
    return {"reads": reads, "resolved": resolved, "wrong": wrong,
            "mismatched": mismatched, "truth_missing": truth_missing,
            "open_bursts": open_bursts,
            "open_live_counts": sorted({v for v in predicted.values()
                                        if v > 1}),
            "met": (wrong == 0 and mismatched == 0 and truth_missing == 0)}


def v2_three_views(limit: Optional[int] = None) -> Dict[str, object]:
    """V2: three views, every common-mode weight-4 burst."""
    tets = _tetrads()
    reads = resolved = wrong = 0
    for c in probe_codewords(limit):
        stored = store_views(c)
        for e in tets:
            fork = read_views([w ^ e for w in stored])
            reads += 1
            if fork.status == "resolved":
                resolved += 1
                if fork.value != c:
                    wrong += 1
    return {"reads": reads, "resolved": resolved, "wrong": wrong,
            "met": resolved == reads and wrong == 0}


def v3_single_frames() -> Dict[str, object]:
    """V3: each single second frame ``k = 1..23`` leaves some burst open."""
    tets = _tetrads()
    c = probe_codewords(1)[0]
    table = {}
    for k in range(1, N):
        stored = store_views(c, (0, k))
        open_ = 0
        for e in tets:
            if read_views([w ^ e for w in stored], (0, k)).status != "resolved":
                open_ += 1
        table[k] = open_
    return {"open_by_frame": table, "least_open": min(table.values()),
            "met": all(v > 0 for v in table.values())}


def v4_x1_register() -> Dict[str, object]:
    """V4: X1's probe through the two-view register, independent faults."""
    words, errors = x1_probe()
    reads = resolved = wrong = 0
    for c in words:
        reg = FramedRegister(c, C.PAIR_FRAMES)
        for e1, e2 in combinations(errors, 2):
            fork = reg.inject_each((e1, e2)).read()
            reads += 1
            if fork.status == "resolved":
                resolved += 1
                if fork.value != c:
                    wrong += 1
    return {"reads": reads, "resolved": resolved, "wrong": wrong,
            "met": reads == 4224 and resolved == reads and wrong == 0}


def v5_inside_radius(limit: Optional[int] = None) -> Dict[str, object]:
    """V5: every common-mode burst of weight <= 3, two and three views."""
    bursts = tuple(b for w in range(4) for b in _bursts(w))
    out = {}
    for name, frames in (("two", C.PAIR_FRAMES), ("three", FRAMES)):
        reads = right = 0
        for c in probe_codewords(limit):
            stored = store_views(c, frames)
            for e in bursts:
                fork = read_views([w ^ e for w in stored], frames)
                reads += 1
                right += int(fork.value == c)
        out[name] = {"reads": reads, "right": right}
    out["bursts"] = len(bursts)
    out["met"] = all(out[n]["reads"] == out[n]["right"]
                     for n in ("two", "three"))
    return out


def weight5_report(limit: Optional[int] = None) -> Dict[str, object]:
    """Reported, not a mark: common-mode bursts of weight 5."""
    bursts = _bursts(5)
    rows = {}
    for name, frames in (("single", (0,)), ("two", C.PAIR_FRAMES),
                         ("three", FRAMES)):
        row = {"reads": 0, "answered": 0, "wrong": 0, "open": 0,
               "contradicted": 0}
        for c in probe_codewords(limit):
            stored = store_views(c, frames)
            for e in bursts:
                fork = read_views([w ^ e for w in stored], frames)
                row["reads"] += 1
                if fork.status == "resolved":
                    row["answered"] += 1
                    row["wrong"] += int(fork.value != c)
                elif fork.status == "open":
                    row["open"] += 1
                else:
                    row["contradicted"] += 1
        rows[name] = row
    return rows


def fresh_case_set(k: int) -> Tuple[int, ...]:
    """``S'_k``: the codewords at indices ``2 + j * floor(4096 / k)``."""
    step = len(GOLAY_MASKS) // k
    return tuple(GOLAY_MASKS[C.FRESH_CASE_OFFSET + j * step] for j in range(k))


def v6_composition(sizes: Sequence[int] = C.CASE_SIZES) -> Dict[str, object]:
    """V6 (J1): the context stage, then the second view, on a fresh probe."""
    tets = _tetrads()
    second = C.PAIR_FRAMES[1]
    unions = {e: e | rot(e, second) for e in tets}
    rows = []
    for k in sizes:
        cases = fresh_case_set(k)
        declared = frozenset(cases)
        reads = ctx_answered = ctx_wrong = answered = wrong = open_ = 0
        predicted_open = 0
        for c in cases:
            stored = store_views(c, C.PAIR_FRAMES)
            octad_gaps = [c ^ d for d in cases
                          if d != c and bin(c ^ d).count("1") == 8]
            for e in tets:
                reads += 1
                u = unions[e]
                if any(u & o == u for o in octad_gaps):
                    predicted_open += 1
                fork = carry(stored[0] ^ e).restrict_to_cases(cases)
                if fork.status == "resolved":
                    ctx_answered += 1
                    ctx_wrong += int(fork.value != c)
                aligned = align(stored[1] ^ e, second)
                allowed = frozenset(carry(aligned).candidates)
                fork = fork.prune(
                    "second reading", lambda x, a=allowed: x in a,
                    f"not a nearest codeword of view {second}", ONE_CARRIER)
                if fork.status == "resolved":
                    answered += 1
                    wrong += int(fork.value != c)
                elif fork.status == "open":
                    open_ += 1
                assert all(x in declared for x in fork.live)
        rows.append({"k": k, "reads": reads,
                     "context_answered": ctx_answered,
                     "context_wrong": ctx_wrong,
                     "answered": answered, "wrong": wrong, "open": open_,
                     "predicted_open": predicted_open,
                     "share": Fraction(answered, reads)})
    need = Fraction(*C.SHARE_MARK)
    met = all(r["wrong"] == 0 and r["open"] == r["predicted_open"]
              and r["share"] >= need for r in rows)
    return {"rows": rows, "met": met,
            "reads": sum(r["reads"] for r in rows),
            "answered": sum(r["answered"] for r in rows),
            "wrong": sum(r["wrong"] for r in rows)}


#: Phase 82's declared grid of rates.
RATE_GRID: Tuple[Fraction, ...] = (Fraction(1, 1000), Fraction(1, 100),
                                   Fraction(1, 50), Fraction(1, 20),
                                   Fraction(1, 10), Fraction(1, 5))


def _view_distance(aligned: Sequence[int], c: int) -> int:
    return sum(bin(a ^ c).count("1") for a in aligned)


def _soft_check(views: Sequence[int], frames: Sequence[int], truth: int
                ) -> Tuple[bool, bool, bool]:
    """``(escalation == intersection, rate ranking == D ranking, escalation
    resolves something the intersection leaves open)`` for one read."""
    aligned = [align(w, k) for w, k in zip(views, frames)]
    fork = read_views(views, frames)
    base = carry(aligned[0])
    esc = escalate(base, soft_mean(views, frames))
    same = set(esc.nearest) == set(fork.live)
    dist = {c: _view_distance(aligned, c) for c in base.candidates}
    best = min(dist.values())
    by_d = {c for c, d in dist.items() if d == best}
    total = N * len(aligned)
    rate_same = True
    for p in RATE_GRID:
        like = {c: p ** d * (1 - p) ** (total - d) for c, d in dist.items()}
        top = max(like.values())
        if {c for c, v in like.items() if v == top} != by_d:
            rate_same = False
    gained = len(esc.nearest) == 1 and fork.status != "resolved"
    return same, rate_same, gained


def v7_soft_channel(limit: int = 2) -> Dict[str, object]:
    """V7 (J3): the escalation on the views' own soft reading."""
    tets = _tetrads()
    out = {}
    probes = []
    for c in probe_codewords(limit):
        st2 = store_views(c, C.PAIR_FRAMES)
        st3 = store_views(c)
        probes.extend(("two", [w ^ e for w in st2], C.PAIR_FRAMES, c)
                      for e in tets)
        probes.extend(("three", [w ^ e for w in st3], FRAMES, c)
                      for e in tets)
    words, errors = x1_probe()
    for c in words:
        st = store_views(c, C.PAIR_FRAMES)
        probes.extend(("x1", [st[0] ^ e1, st[1] ^ e2], C.PAIR_FRAMES, c)
                      for e1, e2 in combinations(errors, 2))
    for name, views, frames, truth in probes:
        row = out.setdefault(name, {"reads": 0, "equal": 0, "rate_equal": 0,
                                    "gained": 0})
        same, rate_same, gained = _soft_check(views, frames, truth)
        row["reads"] += 1
        row["equal"] += int(same)
        row["rate_equal"] += int(rate_same)
        row["gained"] += int(gained)
    met = all(r["equal"] == r["reads"] and r["rate_equal"] == r["reads"]
              for r in out.values())
    return {"rows": out, "met": met}


def x1_three_views_post_hoc() -> Dict[str, object]:
    """Post hoc, not a mark (taken after V4 was missed): X1's probe through
    the three-view register, each view with its own error -- every triple of
    the 12 declared errors on every probe codeword."""
    words, errors = x1_probe()
    reads = resolved = wrong = 0
    for c in words:
        reg = FramedRegister(c)
        for triple in combinations(errors, 3):
            fork = reg.inject_each(triple).read()
            reads += 1
            if fork.status == "resolved":
                resolved += 1
                wrong += int(fork.value != c)
    return {"reads": reads, "resolved": resolved, "wrong": wrong}


def second_view_report(full: bool = True) -> Dict[str, object]:
    """Every mark of the study.  ``full=False`` samples the probe codewords
    (one instead of 64) and skips the slow soft channel and composition."""
    limit = None if full else 1
    out: Dict[str, object] = {
        "frames": FRAMES,
        "V1": v1_two_views(limit),
        "V2": v2_three_views(limit),
        "V3": v3_single_frames(),
        "V4": v4_x1_register(),
        "V5": v5_inside_radius(limit),
        "weight5": weight5_report(limit),
        "post_hoc_x1_three": x1_three_views_post_hoc(),
    }
    if full:
        out["V6"] = v6_composition()
        out["V7"] = v7_soft_channel()
    else:
        out["V6"] = v6_composition(sizes=(2, 4))
        out["V7"] = v7_soft_channel(limit=0)
    return out


# ===========================================================================
# 4.  PHASE 97: THE THIRD VIEW ON DEMAND, AND INDEPENDENT FAULTS RE-DECLARED
# ===========================================================================

def r1_on_demand_common(limit: Optional[int] = None) -> Dict[str, object]:
    """R1: on demand against three views, every common-mode four-error
    burst on Phase 96's probe."""
    tets = _tetrads()
    reads = same = third = wrong = resolved = 0
    for c in probe_codewords(limit):
        stored = store_views(c)
        for e in tets:
            views = [w ^ e for w in stored]
            fork, taken = read_on_demand(views)
            full = read_views(views)
            reads += 1
            third += int(taken == 3)
            same += int(fork.status == full.status
                        and set(fork.live) == set(full.live))
            if fork.status == "resolved":
                resolved += 1
                wrong += int(fork.value != c)
    n = len(probe_codewords(limit))
    want = U.PREDICTED_COMMON["third_reads"] * n // 64
    return {"reads": reads, "same_as_three": same, "third_reads": third,
            "views_read": 2 * reads + third, "resolved": resolved,
            "wrong": wrong, "predicted_third_reads": want,
            "met": same == reads and third == want and wrong == 0
            and resolved == reads}


def r2_on_demand_inside(limit: Optional[int] = None) -> Dict[str, object]:
    """R2: every common-mode burst of weight at most 3: answered right, the
    third view never read."""
    bursts = tuple(b for w in range(4) for b in _bursts(w))
    reads = right = third = 0
    for c in probe_codewords(limit):
        stored = store_views(c)
        for e in bursts:
            fork, taken = read_on_demand([w ^ e for w in stored])
            reads += 1
            right += int(fork.value == c)
            third += int(taken == 3)
    return {"reads": reads, "right": right, "third_reads": third,
            "met": right == reads and third == 0}


def r3_on_demand_weight5(limit: Optional[int] = None) -> Dict[str, object]:
    """R3: weight-5 bursts, outside the fault model: the on-demand verdict
    against the two-view register's, and the wrong answers it gives."""
    bursts = _bursts(5)
    row = {"reads": 0, "answered": 0, "wrong": 0, "open": 0,
           "contradicted": 0, "third_reads": 0, "same_as_two": 0}
    for c in probe_codewords(limit):
        stored = store_views(c)
        for e in bursts:
            views = [w ^ e for w in stored]
            two = read_views(views[:2], FRAMES[:2])
            fork, taken = read_on_demand(views)
            row["reads"] += 1
            row["third_reads"] += int(taken == 3)
            row["same_as_two"] += int(fork.status == two.status
                                      and set(fork.live) == set(two.live))
            if fork.status == "resolved":
                row["answered"] += 1
                row["wrong"] += int(fork.value != c)
            elif fork.status == "open":
                row["open"] += 1
            else:
                row["contradicted"] += 1
    n = len(probe_codewords(limit))
    want = U.PREDICTED_COMMON["weight5_wrong"]
    row["predicted_wrong"] = want if n == 64 else None
    row["met"] = (row["same_as_two"] == row["reads"]
                  and (n != 64 or row["wrong"] == want))
    return row


def fresh_probe() -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """R4-R6: the fresh codewords (offset 32, stride 64) and the fresh
    errors (indices ``5 + 883 j`` of the lexicographic four-sets)."""
    words = tuple(GOLAY_MASKS[U.FRESH_CODEWORD_OFFSET
                              + i * U.FRESH_CODEWORD_STRIDE]
                  for i in range(len(GOLAY_MASKS) // U.FRESH_CODEWORD_STRIDE))
    tets = _tetrads()
    errors = tuple(tets[U.FRESH_ERROR_START + j * U.FRESH_ERROR_STRIDE]
                   for j in range(U.FRESH_ERROR_COUNT))
    return words, errors


def r4_r6_independent(limit: Optional[int] = None) -> Dict[str, object]:
    """R4 (two views), R5 (three views) and R6 (on demand), each view with
    its own error from the fresh list, on the fresh codewords."""
    from itertools import permutations
    words, errors = fresh_probe()
    if limit is not None:
        words = words[:limit]
    second, third = FRAMES[1], FRAMES[2]
    r4 = {"reads": 0, "resolved": 0, "wrong": 0, "mismatched": 0,
          "truth_missing": 0}
    r5 = dict(r4)
    r6 = {"reads": 0, "same_as_three": 0, "third_reads": 0,
          "third_when_open": 0, "wrong": 0}
    pair_live = {(a, b): 1 + octads_through(a | rot(b, second))
                 for a, b in permutations(errors, 2)}
    triple_live = {(a, b, d): 1 + octads_through(a | rot(b, second)
                                                 | rot(d, third))
                   for a, b, d in permutations(errors, 3)}
    for c in words:
        reg = FramedRegister(c)
        reg2 = FramedRegister(c, C.PAIR_FRAMES)
        for (a, b), live in pair_live.items():
            fork = reg2.inject_each((a, b)).read()
            r4["reads"] += 1
            r4["truth_missing"] += int(c not in fork.live)
            r4["mismatched"] += int(len(fork.live) != live)
            if fork.status == "resolved":
                r4["resolved"] += 1
                r4["wrong"] += int(fork.value != c)
        for (a, b, d), live in triple_live.items():
            hit = reg.inject_each((a, b, d))
            fork = hit.read()
            r5["reads"] += 1
            r5["truth_missing"] += int(c not in fork.live)
            r5["mismatched"] += int(len(fork.live) != live)
            if fork.status == "resolved":
                r5["resolved"] += 1
                r5["wrong"] += int(fork.value != c)
            lazy, taken = hit.read_on_demand()
            two_open = pair_live[(a, b)] > 1
            r6["reads"] += 1
            r6["same_as_three"] += int(lazy.status == fork.status
                                       and set(lazy.live) == set(fork.live))
            r6["third_reads"] += int(taken == 3)
            r6["third_when_open"] += int((taken == 3) == two_open)
            if lazy.status == "resolved":
                r6["wrong"] += int(lazy.value != c)
    for r in (r4, r5):
        r["open"] = r["reads"] - r["resolved"]
        r["met"] = (r["wrong"] == 0 and r["mismatched"] == 0
                    and r["truth_missing"] == 0)
    r4["open_pairs"] = sum(1 for v in pair_live.values() if v > 1)
    r5["open_triples"] = sum(1 for v in triple_live.values() if v > 1)
    r6["met"] = (r6["same_as_three"] == r6["reads"]
                 and r6["third_when_open"] == r6["reads"]
                 and r6["wrong"] == 0)
    return {"R4": r4, "R5": r5, "R6": r6}


def _octad_subsets() -> frozenset:
    """Every subset of four or more points of some octad."""
    out = set()
    for o in OCTADS:
        pts = [i for i in range(N) if (o >> i) & 1]
        for size in range(4, 9):
            for s in combinations(pts, size):
                out.add(sum(1 << i for i in s))
    return frozenset(out)


def r7_frame_census(count: int = U.CENSUS_COUNT) -> Dict[str, object]:
    """R7: for each census first error and each single second frame, the
    number of second errors that leave two views open."""
    tets = _tetrads()
    inside = _octad_subsets()
    rows = []
    for j in range(count):
        e = tets[j * U.CENSUS_STRIDE]
        counts = set()
        for k in range(1, N):
            counts.add(sum(1 for f in tets if (e | rot(f, k)) in inside))
        rows.append({"first": e, "counts": sorted(counts)})
    ok = all(r["counts"] == [U.OPEN_SECONDS] for r in rows)
    return {"first_errors": count, "frames": N - 1, "rows": rows,
            "declared": U.OPEN_SECONDS, "met": ok}


def on_demand_report(full: bool = True) -> Dict[str, object]:
    """R1-R7.  ``full=False`` samples one probe codeword and two census
    first errors."""
    limit = None if full else 1
    out: Dict[str, object] = {
        "R1": r1_on_demand_common(limit),
        "R2": r2_on_demand_inside(limit),
        "R3": r3_on_demand_weight5(limit),
    }
    out.update(r4_r6_independent(limit))
    out["R7"] = r7_frame_census(U.CENSUS_COUNT if full else 2)
    return out
