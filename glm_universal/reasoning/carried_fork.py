"""``glm_universal.reasoning.carried_fork`` -- the six candidates, carried.

The question
------------
At coset weight 4 the complete Golay decoder
(:mod:`glm_universal.substrate.golay_decode`) finds **six** equidistant
codewords and refuses to choose.  The owner's instruction for this round was
to stop there no longer: *carry all six until a later decision resolves them,
pruned or proven incorrect, and escalate to the Leech lattice where that
extends what the machine can do with the information.*
``studies/CARRIED_FORK_STUDY.md`` declares four experiments, K1-K4, before
this module existed; :func:`carried_fork_report` measures them.

The object
----------
A :class:`CarriedFork` is the received word, its candidates, the candidates
still **live**, and a **ledger** of :class:`Elimination` records.  Every stage
that removes a candidate names itself, gives a reason, and names the
assumption under which the removal is sound.  Three rules hold for every
fork, and ``RequestProject/GLM/CarriedFork.lean`` proves them:

1. the live candidates and the ledger always partition the candidates;
2. a fork is ``resolved`` exactly when one candidate is live, ``open`` when
   more than one is, ``contradicted`` when none is -- nothing is ever picked
   by enumeration order;
3. if every stage removed only non-truths and the truth was a candidate,
   a resolved fork holds the truth (``GLM.CarriedFork.resolved_eq_truth``).

The stages
----------
``context``        a declared predicate is false of the candidate; for
                   ``classify`` the predicate is *is a declared case*, and the
                   assumption is the **closed world** (the truth is a
                   declared case).
``second reading`` the candidate is absent from the fork of another read of
                   the same carrier.
``unsure set``     the candidate's tetrad touches a coordinate the reader
                   marked sure; sound when errors fall only on unsure
                   coordinates.  Two tetrads of one sextet are disjoint, so
                   an unsure set of at most seven coordinates always resolves
                   (``GLM.CarriedFork.unsure_resolves``).
``escalation``     a rational (soft) reading lifted to the Leech lattice picks
                   the candidates under the nearest vertices of the deep hole
                   the hard word lifts to.  This is an **estimate**: it is
                   returned beside the fork as an :class:`Escalation` and never
                   written into the certified ledger.

The Leech lift
--------------
The hard word ``y`` lifts to the point ``2y`` in the coordinates of
:mod:`glm_universal.substrate.leech2` (minimal norm 32).  At coset weight 4
that point is at raw squared distance 16 -- the covering radius squared --
from exactly 48 Leech points, eight over each candidate, and
:func:`glm_universal.reasoning.deep_holes.hole_diagram` certifies them as a
deep hole of type ``A_1^24``: the Niemeier lattice whose glue code is the
Golay code itself.  Escalating a *hard* word therefore carries 48 points where
the code carried 6 and resolves nothing; what the lattice adds is a metric in
which a *soft* reading can be placed.

Exactness
---------
``int`` masks and :class:`fractions.Fraction` only.  No float, no RNG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations, product
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2
from ..substrate.golay_decode import (_deterministic_errors, decode_complete,
                                      legacy_snap_decode)
from ..substrate.linalg import popcount
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET

__all__ = [
    "N", "FULL", "STAGES", "CLOSED_WORLD",
    "Elimination", "CarriedFork", "Escalation",
    "carry", "leech_hole", "certify_hole", "escalate",
    "soft_reading", "x1_probe", "case_set",
    "k1_context", "k2_second_reading", "k3_unsure", "k4a_hard_lift",
    "k4b_soft", "k1_then_second_read", "carried_fork_report",
]

N = 24
FULL = (1 << N) - 1

#: The stages a candidate can leave the fork by, in the order of the study.
STAGES: Tuple[str, ...] = ("context", "second reading", "unsure set")

#: The assumption the context stage rests on when the predicate is the set of
#: declared cases.  Every answer that stage gives quotes it.
CLOSED_WORLD = ("closed world: the carrier is one of the declared cases, so a "
                "candidate that is not a declared case is not the truth")


def _bits(mask: int) -> Tuple[int, ...]:
    return tuple((mask >> i) & 1 for i in range(N))


def _support(mask: int) -> Tuple[int, ...]:
    return tuple(i for i in range(N) if (mask >> i) & 1)


# ===========================================================================
# 1.  THE FORK
# ===========================================================================

@dataclass(frozen=True)
class Elimination:
    """One candidate leaving the fork: by which stage, why, and on what
    assumption the removal is sound."""

    candidate: int
    stage: str
    reason: str
    assumption: str


@dataclass(frozen=True)
class CarriedFork:
    """A deep-hole read carried forward with every candidate it could be.

    ``candidates`` are the nearest codewords (six at coset weight 4, one
    below it), sorted; ``live`` the ones no stage has removed; ``ledger`` the
    removals in the order they happened.
    """

    received: int
    weight: int
    candidates: Tuple[int, ...]
    live: Tuple[int, ...]
    ledger: Tuple[Elimination, ...] = field(default=())

    # -- state ---------------------------------------------------------------
    @property
    def status(self) -> str:
        if len(self.live) == 1:
            return "resolved"
        return "open" if self.live else "contradicted"

    @property
    def value(self) -> Optional[int]:
        """The single live candidate of a resolved fork, else ``None``."""
        return self.live[0] if self.status == "resolved" else None

    def tetrad(self, candidate: int) -> int:
        """The error pattern that separates the read from ``candidate``."""
        return self.received ^ candidate

    @property
    def assumptions(self) -> Tuple[str, ...]:
        """Every assumption the current live set rests on, once each."""
        seen: List[str] = []
        for e in self.ledger:
            if e.assumption not in seen:
                seen.append(e.assumption)
        return tuple(seen)

    def partition_holds(self) -> bool:
        """Rule 1: live and eliminated partition the candidates."""
        gone = [e.candidate for e in self.ledger]
        return (len(set(gone)) == len(gone)
                and not set(gone) & set(self.live)
                and sorted(gone + list(self.live)) == sorted(self.candidates))

    # -- the stages ------------------------------------------------------------
    def prune(self, stage: str, keep: Callable[[int], bool], reason: str,
              assumption: str) -> "CarriedFork":
        """Remove every live candidate ``keep`` rejects, recording why."""
        if stage not in STAGES:
            raise ValueError(f"prune: unknown stage {stage!r}")
        kept, out = [], list(self.ledger)
        for c in self.live:
            if keep(c):
                kept.append(c)
            else:
                out.append(Elimination(c, stage, reason, assumption))
        return CarriedFork(self.received, self.weight, self.candidates,
                           tuple(kept), tuple(out))

    def restrict_to_cases(self, cases: Sequence[int]) -> "CarriedFork":
        """The context stage for ``classify``: keep the declared cases."""
        declared = frozenset(cases)
        return self.prune("context", lambda c: c in declared,
                          "not a declared case", CLOSED_WORLD)

    def intersect(self, other: "CarriedFork") -> "CarriedFork":
        """The second-reading stage: keep what the other read also allows."""
        allowed = frozenset(other.candidates)
        return self.prune(
            "second reading", lambda c: c in allowed,
            f"not a nearest codeword of the second read {other.received:#08x}",
            "both reads are of one carrier, each within coset weight 4")

    def rule_out_sure(self, unsure: int) -> "CarriedFork":
        """The unsure-set stage: a candidate whose tetrad touches a
        coordinate marked sure is proven incorrect."""
        sure = FULL & ~unsure
        return self.prune(
            "unsure set", lambda c: not (self.tetrad(c) & sure),
            f"its tetrad touches a coordinate marked sure (unsure set "
            f"{_support(unsure)})",
            "errors fall only on coordinates the reader marked unsure")


def carry(received: int) -> CarriedFork:
    """Read ``received`` with the complete decoder and carry every candidate."""
    d = decode_complete(received)
    cands = tuple(sorted(d.candidates))
    return CarriedFork(received=received, weight=d.weight, candidates=cands,
                       live=cands)


# ===========================================================================
# 2.  THE LEECH LIFT AND THE ESCALATED READING
# ===========================================================================

def leech_hole(fork: CarriedFork) -> Dict[int, Tuple[Tuple[int, ...], ...]]:
    """``candidate -> its Leech points at the covering radius from 2y``.

    Each candidate ``c`` contributes the points ``2c + 4z`` with ``z``
    supported on its tetrad and each move towards ``2y`` (``0 -> 4`` where
    ``y`` has a 1, ``2 -> -2`` where it has a 0) -- every such point is at raw
    squared distance 16 from ``2y`` -- kept when the Leech congruences admit
    it.
    """
    y = fork.received
    center = tuple(2 * b for b in _bits(y))
    out: Dict[int, Tuple[Tuple[int, ...], ...]] = {}
    for c in fork.candidates:
        base = [2 * b for b in _bits(c)]
        tet = _support(fork.tetrad(c))
        pts = []
        for z in product((0, 1), repeat=len(tet)):
            v = list(base)
            for i, flip in zip(tet, z):
                if flip:
                    v[i] += 4 if base[i] == 0 else -4
            if leech2.in_leech(v):
                if sum((a - b) ** 2 for a, b in zip(v, center)) != 16:
                    raise AssertionError("leech_hole: vertex off the radius")
                pts.append(tuple(v))
        out[c] = tuple(pts)
    return out


def certify_hole(fork: CarriedFork) -> Dict[str, object]:
    """Certify the lift of a weight-4 read as a deep hole, by the classifier
    of :mod:`glm_universal.reasoning.deep_holes` (barycentre identity)."""
    from . import deep_holes as dh
    hole = leech_hole(fork)
    verts = [v for pts in hole.values() for v in pts]
    center = [2 * b for b in _bits(fork.received)]
    diag = dh.hole_diagram(verts, center=center)
    return {
        "vertices": len(verts),
        "per_candidate": sorted({len(p) for p in hole.values()}),
        "root_system": diag["root_system"],
        "certified": bool(diag["certified_complete"]),
    }


@dataclass(frozen=True)
class Escalation:
    """An escalated reading of a fork: an **estimate**, never a certificate.

    ``nearest`` are the live candidates under the hole vertices nearest to the
    lifted soft reading; ``distances`` the exact raw squared distance from the
    lifted reading to each live candidate's nearest vertex; ``margin`` the gap
    between the best and the second-best candidate (``None`` with one live).
    """

    nearest: Tuple[int, ...]
    distances: Tuple[Tuple[int, Fraction], ...]
    margin: Optional[Fraction]
    euclidean_nearest: Tuple[int, ...]

    @property
    def estimate(self) -> Optional[int]:
        return self.nearest[0] if len(self.nearest) == 1 else None


def escalate(fork: CarriedFork, soft: Sequence[Fraction]) -> Escalation:
    """Place the soft reading ``soft`` (``0`` = bit 0, ``1`` = bit 1) at
    ``2*soft`` in Leech coordinates and rank the live candidates by their
    nearest hole vertex; beside it, the plain Euclidean ranking of the live
    candidates as 0/1 vectors."""
    target = [2 * Fraction(s) for s in soft]
    hole = leech_hole(fork)
    dist: List[Tuple[int, Fraction]] = []
    for c in fork.live:
        pts = hole.get(c) or (tuple(2 * b for b in _bits(c)),)
        dist.append((c, min(sum((Fraction(v) - t) ** 2
                                for v, t in zip(p, target)) for p in pts)))
    best = min(d for _, d in dist)
    nearest = tuple(c for c, d in dist if d == best)
    rest = sorted(d for _, d in dist if d != best)
    margin = (rest[0] - best) if rest else (None if len(dist) == 1
                                             else Fraction(0))
    eu = [(c, sum((Fraction(s) - b) ** 2 for s, b in zip(soft, _bits(c))))
          for c in fork.live]
    eb = min(d for _, d in eu)
    return Escalation(nearest=nearest, distances=tuple(dist), margin=margin,
                      euclidean_nearest=tuple(c for c, d in eu if d == eb))


# ===========================================================================
# 3.  THE DECLARED PROBES
# ===========================================================================

def x1_probe() -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """The probe of X1: 64 codewords at stride 64, 12 weight-4 errors."""
    stride = len(GOLAY_MASKS) // 64
    return (tuple(GOLAY_MASKS[i * stride] for i in range(64)),
            tuple(_deterministic_errors(4, 12)))


def case_set(k: int) -> Tuple[int, ...]:
    """``S_k``: the codewords at indices ``1 + j*floor(4096/k)``."""
    step = len(GOLAY_MASKS) // k
    return tuple(GOLAY_MASKS[1 + j * step] for j in range(k))


def _weight4_errors() -> Tuple[int, ...]:
    return tuple(sum(1 << i for i in s) for s in combinations(range(N), 4))


def soft_reading(i: int, truth: int, error: int) -> Tuple[Fraction, ...]:
    """The declared soft ensemble of K4b for read ``i``."""
    hard = truth ^ error
    out = []
    for j in range(N):
        if (error >> j) & 1:
            rho = Fraction((5 * i + 3 * j) % 4 + 1, 8)
        else:
            rho = Fraction((7 * i + 11 * j) % 8 + 1, 8)
        out.append((1 + rho) / 2 if (hard >> j) & 1 else (1 - rho) / 2)
    return tuple(out)


# ===========================================================================
# 4.  THE EXPERIMENTS
# ===========================================================================

def k1_context(sizes: Sequence[int] = (2, 4, 8, 16, 32)) -> Dict[str, object]:
    """K1: the fork pruned to the declared cases, against Phase 64's refusal."""
    from .python_substrate import classify
    errors = _weight4_errors()
    words, errs = x1_probe()
    rows = []
    for k in sizes:
        cases = case_set(k)
        reads = answered = correct = wrong = open_ = contradicted = 0
        control_answered = 0
        for c in cases:
            for e in errors:
                reads += 1
                fork = carry(c ^ e).restrict_to_cases(cases)
                if fork.status == "resolved":
                    answered += 1
                    correct += fork.value == c
                    wrong += fork.value != c
                elif fork.status == "open":
                    open_ += 1
                else:
                    contradicted += 1
        # the control, on a stride sample (it refuses every weight-4 read)
        for c in cases:
            for e in errors[::97]:
                control_answered += classify(c ^ e, cases).verdict == "branch"
        hostile = hostile_answered = hostile_control = 0
        declared = frozenset(cases)
        for w in words:
            if w in declared:
                continue
            for e in errs:
                hostile += 1
                hostile_answered += carry(w ^ e).restrict_to_cases(
                    cases).status == "resolved"
                hostile_control += classify(w ^ e, cases).verdict == "branch"
        rows.append({"k": k, "reads": reads, "answered": answered,
                     "correct": correct, "wrong": wrong, "open": open_,
                     "contradicted": contradicted,
                     "answered_share": Fraction(answered, reads),
                     "control_answered_on_sample": control_answered,
                     "hostile_reads": hostile,
                     "hostile_answered_all_wrong": hostile_answered,
                     "hostile_control_answered": hostile_control})
    passed = all(r["wrong"] == 0 and 10 * r["answered"] >= 9 * r["reads"]
                 for r in rows)
    return {"rows": rows,
            "reads": sum(r["reads"] for r in rows),
            "answered": sum(r["answered"] for r in rows),
            "wrong": sum(r["wrong"] for r in rows),
            "assumption": CLOSED_WORLD,
            "pass_mark": "0 wrong, required; at least 90% answered at every k",
            "passed": passed, "faculty": "refuse -> derive"}


def k2_second_reading() -> Dict[str, object]:
    """K2: X1 reproduced through the fork's intersection stage."""
    words, errs = x1_probe()
    pairs = answered = correct = wrong = refused = 0
    for c in words:
        forks = [carry(c ^ e) for e in errs]
        for i, j in combinations(range(len(forks)), 2):
            pairs += 1
            both = forks[i].intersect(forks[j])
            if both.status == "resolved":
                answered += 1
                correct += both.value == c
                wrong += both.value != c
            else:
                refused += 1
    octad = next(w for w in GOLAY_MASKS if popcount(w) == 8)
    sup = _support(octad)
    e1 = sum(1 << i for i in sup[:4])
    e2 = sum(1 << i for i in sup[4:])
    c0 = GOLAY_MASKS[0]
    witness = carry(c0 ^ e1).intersect(carry(c0 ^ e2))
    ok_witness = set(witness.live) == {c0, c0 ^ octad}
    return {"double_reads": pairs, "answered": answered, "correct": correct,
            "wrong": wrong, "refused": refused,
            "witness_live": len(witness.live),
            "witness_is_truth_and_octad": ok_witness,
            "pass_mark": "4224 of 4224 answered, 0 wrong; the witness keeps "
                         "exactly the truth and the truth plus the octad",
            "passed": (pairs == answered == 4224 and wrong == 0
                       and ok_witness),
            "faculty": "address"}


def k3_unsure(extras: Sequence[int] = (0, 1, 2, 3, 4)) -> Dict[str, object]:
    """K3: candidates proven incorrect by an unsure set around the error."""
    words, errs = x1_probe()
    rows = []
    for r in extras:
        answered = correct = wrong = refused = two_tetrad_refusals = 0
        for c in words:
            for e in errs:
                rest = [j for j in range(N) if not (e >> j) & 1][:r]
                unsure = e | sum(1 << j for j in rest)
                fork = carry(c ^ e)
                cut = fork.rule_out_sure(unsure)
                if cut.status == "resolved":
                    answered += 1
                    correct += cut.value == c
                    wrong += cut.value != c
                else:
                    refused += 1
                    tets = [fork.tetrad(x) for x in cut.live]
                    if len(tets) == 2 and (tets[0] | tets[1]) == unsure:
                        two_tetrad_refusals += 1
        rows.append({"extra": r, "unsure_size": 4 + r, "reads": answered +
                     refused, "answered": answered, "correct": correct,
                     "wrong": wrong, "refused": refused,
                     "refusals_that_are_two_tetrads": two_tetrad_refusals})
    passed = all(row["wrong"] == 0 for row in rows) and all(
        row["answered"] == row["reads"] for row in rows
        if row["unsure_size"] <= 7) and all(
        row["refused"] == row["refusals_that_are_two_tetrads"]
        for row in rows)
    return {"rows": rows,
            "pass_mark": "0 wrong; all answered when |U| <= 7; every refusal "
                         "at |U| = 8 is the union of two tetrads",
            "passed": passed, "faculty": "refuse"}


def k4a_hard_lift(limit: Optional[int] = None) -> Dict[str, object]:
    """K4a: every weight-4 coset lifts to a certified A_1^24 deep hole."""
    from ..substrate.golay_decode import coset_table
    reps = sorted(min(leaders) for leaders in coset_table().values()
                  if popcount(leaders[0]) == 4)
    if limit is not None:
        reps = reps[:limit]
    ok = 0
    systems: Dict[str, int] = {}
    counts: Dict[int, int] = {}
    for y in reps:
        cert = certify_hole(carry(y))
        systems[cert["root_system"]] = systems.get(cert["root_system"], 0) + 1
        counts[cert["vertices"]] = counts.get(cert["vertices"], 0) + 1
        ok += (cert["certified"] and cert["vertices"] == 48
               and cert["per_candidate"] == [8]
               and cert["root_system"] == "A_1^24")
    return {"cosets": len(reps), "certified_a1_24_with_48": ok,
            "root_systems": systems, "vertex_counts": counts,
            "complete": limit is None,
            "pass_mark": "1771 of 1771",
            "passed": limit is None and ok == len(reps) == 1771,
            "faculty": "none (structural)"}


def k4b_soft(with_leech_decoder: bool = True) -> Dict[str, object]:
    """K4b and K4c: the soft reading, escalated and certified-cut."""
    from . import fwht_decode as fd
    words, errs = x1_probe()
    reads = est_right = est_wrong = est_tied = agree_eu = 0
    snap_right = soft_ml_right = soft_ml_in_fork = 0
    leech_right = leech_vertex = leech_even = leech_right_on_tied = 0
    cut_answered = cut_right = cut_wrong = cut_open_est_right = 0
    cut_open = cut_open_est_wrong = 0
    margins_wrong: List[Fraction] = []
    i = 0
    for c in words:
        for e in errs:
            soft = soft_reading(i, c, e)
            i += 1
            reads += 1
            fork = carry(c ^ e)
            esc = escalate(fork, soft)
            agree_eu += set(esc.nearest) == set(esc.euclidean_nearest)
            if esc.estimate is None:
                est_tied += 1
            elif esc.estimate == c:
                est_right += 1
            else:
                est_wrong += 1
                margins_wrong.append(esc.margin)
            snap_right += legacy_snap_decode(c ^ e)[0] == c
            ml = fd.decode_soft([1 - 2 * s for s in soft])["codewords"]
            soft_ml_right += tuple(ml) == (c,)
            soft_ml_in_fork += all(w in fork.candidates for w in ml)
            if with_leech_decoder:
                pt = fd.nearest_lattice_point_fwht([2 * s for s in soft]).point
                if all(v % 2 == 0 for v in pt):
                    leech_even += 1
                    word = sum(1 << j for j in range(N) if pt[j] % 4 == 2)
                    leech_right += word == c
                    if esc.estimate is None:
                        leech_right_on_tied += word == c
                hole = leech_hole(fork)
                leech_vertex += any(tuple(pt) in pts for pts in hole.values())
            # K4c: the ensemble's promise (a wrong bit has rho <= 1/2)
            unsure = sum(1 << j for j in range(N) if abs(2 * soft[j] - 1)
                         <= Fraction(1, 2))
            cut = fork.rule_out_sure(unsure)
            if cut.status == "resolved":
                cut_answered += 1
                cut_right += cut.value == c
                cut_wrong += cut.value != c
            elif cut.status == "open":
                cut_open += 1
                rest = escalate(cut, soft).estimate
                cut_open_est_right += rest == c
                cut_open_est_wrong += rest is not None and rest != c
    out = {
        "reads": reads, "estimate_right": est_right,
        "estimate_wrong": est_wrong, "estimate_tied": est_tied,
        "estimate_right_share": Fraction(est_right, reads),
        "wrong_margins": sorted(set(margins_wrong)),
        "leech_and_euclidean_agree": agree_eu,
        "snap_right": snap_right,
        "soft_ml_right": soft_ml_right, "soft_ml_in_fork": soft_ml_in_fork,
        "certified_cut_answered": cut_answered,
        "certified_cut_right": cut_right, "certified_cut_wrong": cut_wrong,
        "cut_left_open": cut_open,
        "cut_then_estimate_right": cut_open_est_right,
        "cut_then_estimate_wrong": cut_open_est_wrong,
        "pass_mark_k4b": "estimate right on at least 90% of 768; wrong "
                         "reported; Leech and Euclidean agree on every read",
        "pass_mark_k4c": "0 wrong from the certified cut",
    }
    if with_leech_decoder:
        out.update({"leech_decoder_even": leech_even,
                    "leech_decoder_right": leech_right,
                    "leech_decoder_on_hole_vertex": leech_vertex,
                    "leech_decoder_right_on_tied_reads": leech_right_on_tied,
                    "leech_decoder_note": "the unconstrained decoder breaks "
                    "exact ties lexicographically, so its count on tied "
                    "reads is an order artefact, not a resolution"})
    out["passed_k4b"] = (10 * est_right >= 9 * reads and agree_eu == reads)
    out["passed_k4c"] = cut_wrong == 0
    return out


def k1_then_second_read(k: int = 32) -> Dict[str, object]:
    """Post hoc, not a declared mark: the forks K1 leaves open, carried to a
    second read of the same carrier (the next error of the declared list)."""
    errors = _weight4_errors()
    cases = case_set(k)
    carried = resolved = wrong = still_open = 0
    for c in cases:
        for idx, e in enumerate(errors):
            fork = carry(c ^ e).restrict_to_cases(cases)
            if fork.status != "open":
                continue
            carried += 1
            second = carry(c ^ errors[(idx + 1) % len(errors)])
            after = fork.intersect(second)
            if after.status == "resolved":
                resolved += 1
                wrong += after.value != c
            else:
                still_open += 1
    return {"k": k, "carried_open": carried, "resolved_by_second_read":
            resolved, "wrong": wrong, "still_open": still_open,
            "declared": False}


def carried_fork_report(full: bool = True) -> Dict[str, object]:
    """K1-K4 against the marks declared in ``studies/CARRIED_FORK_STUDY.md``.

    ``full=False`` samples the hard-lift census (64 cosets) and skips the
    unconstrained Leech decoder, for a quick read.
    """
    k1 = k1_context()
    k2 = k2_second_reading()
    k3 = k3_unsure()
    k4a = k4a_hard_lift(None if full else 64)
    k4b = k4b_soft(with_leech_decoder=full)
    composed = k1_then_second_read()
    marks = {"K1": k1["passed"], "K2": k2["passed"], "K3": k3["passed"],
             "K4a": k4a["passed"], "K4b": k4b["passed_k4b"],
             "K4c": k4b["passed_k4c"]}
    return {"K1": k1, "K2": k2, "K3": k3, "K4a": k4a, "K4b": k4b,
            "post_hoc_composition": composed, "marks": marks,
            "met": sorted(k for k, v in marks.items() if v),
            "not_met": sorted(k for k, v in marks.items() if not v),
            "lean_file": "RequestProject/GLM/CarriedFork.lean"}
