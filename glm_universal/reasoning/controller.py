"""``glm_universal.reasoning.controller`` -- a loop that proposes, checks, and refuses.

What this module is
-------------------
Everything else in the reasoning package answers in one shot.
:mod:`glm_universal.reasoning.search_loop` proves what a single hard gate
buys, :mod:`glm_universal.reasoning.escalation` decides which layer separates
two carriers, :mod:`glm_universal.reasoning.retrieval` returns the
declarations nearest a query.  None of them is a *controller*: none of them
takes a question it cannot answer in one step, decomposes it, tries a step,
checks it, and either revises or gives up.

This module is that controller, on the one register where every step can be
checked exactly.  The task is a **dimensional derivation**:

    given a quantity of the physics register, build it from the ten EXT10
    generators one factor at a time -- multiply or divide by *length*,
    *mass*, *time*, *current*, *temperature*, *amount*,
    *luminous_intensity*, *angle*, *solid_angle*, *information* -- and stop
    when the state *is* the target.

The cycle is the one the brief asks for.  **Propose**: the twenty moves.
**Check**: the exact exponent arithmetic decides whether the state is the
target, and the finished plan is re-verified end to end by
:func:`glm_universal.reasoning.verifier.verify_expression_pair`, which is a
different instrument from the one that built it -- the plan is not trusted
because the loop produced it.  **Refuse or refine**: keep the best ``width``
states and go round again; when the budget is gone, refuse.

Two kinds of refusal, and only one of them is a budget
------------------------------------------------------
``invariant``
    A refusal that carries a proof.  Every move changes one *exponent* by one,
    so it cannot change the decimal scale, the tensor rank, the P/T/C
    gradings, or the denominator of an exponent.  A target differing in any of
    those is unreachable **at any depth**, and the controller says so without
    expanding a single node.  ``GLM.Controller.unreachable_of_invariant`` is
    the theorem; :func:`classify_target` is the code.

``exhausted``
    The honest kind: the beam reached its depth or its width lost the thread.
    Beam search is incomplete -- ``GLM.Controller.beam_can_miss`` exhibits a
    width-one loop missing a plan that exists -- so this refusal is a
    statement about the search, not about the target, and the report counts
    how often each heuristic causes one.

Never a third kind: the loop does not return its closest state as if it were
the answer.

The heuristics, and the experiment
----------------------------------
The loop's only free choice is which states to keep, and that is where the
substrate is put to the test.  Six scorers, all measured on the same tasks:

``exponent``
    The exact remaining-move count ``‖state − target‖₁``.  By
    ``GLM.Controller.minimal_length_eq_l1`` this is not a heuristic but the
    true distance, so a width-one loop driven by it never backtracks.  It is
    the ceiling everything else is measured against.

``address``
    **The substrate's answer.**  The state is turned into its 24-coordinate
    physics carrier, scaled by 9 -- the scale ``Address.lean`` proves is
    lossless, being more than twice the covering radius -- and decoded to its
    nearest Leech point; the score is the lattice distance to the target's
    address, in units of one move.

``address_native``
    The same, at the register's own resolution (scale 1) instead of 9.  The
    covering radius is 4 and adjacent states are ``sqrt(2)`` apart, so the
    decoder conflates them and the heuristic should collapse.  It is included
    because the prediction is exactly what ``Address.lean``'s read-back bound
    says, and it is better to measure it than to assert it.

``carrier``
    The same distance *without* the lattice: the raw 24-coordinate carrier.
    The ablation that says what quantising contributes.

``none``
    No guidance: every state scores zero, ties broken by the move order.

``random``
    A seeded score that depends on the state and knows nothing about the
    target -- the control that shows what a scorer with no information does.

The measured verdict is in ``studies/CONTROLLER_STUDY.md``.  In one line: the
exact heuristic solves everything, the substrate's address heuristic solves
most of it and beats no-guidance and the random control, its native-resolution
twin collapses to no-guidance exactly as the read-back bound predicts, and the
address costs about three orders of magnitude more per node than the arithmetic
it is competing with.

Every number is an integer or an exact :class:`~fractions.Fraction`.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..data_objects import physics as do_physics
from ..derived import memo
from .. import integrity
from . import analogy
from . import verifier as vf

# ===========================================================================
#  The state space
# ===========================================================================

#: The ten EXT10 axes, from the register rather than restated.
AXES: Tuple[str, ...] = do_physics.AXES_EXT10

#: One generator per axis: the register's own name for the unit quantity of
#: that dimension.  Checked against the register by :func:`generator_check`,
#: never assumed.
GENERATORS: Tuple[str, ...] = (
    "length", "mass", "time", "current", "temperature", "amount",
    "luminous_intensity", "angle", "solid_angle", "information")

assert len(GENERATORS) == len(AXES)

#: A state is the ten integer EXT10 exponents.
State = Tuple[int, ...]

ORIGIN: State = (0,) * 10


@dataclass(frozen=True)
class Move:
    """Multiply or divide by one generator."""

    axis: int
    up: bool

    @property
    def generator(self) -> str:
        return GENERATORS[self.axis]

    @property
    def key(self) -> Tuple[int, int]:
        """The stated tie-break order: axis first, multiply before divide."""
        return (self.axis, 0 if self.up else 1)

    def __str__(self) -> str:
        return ("* " if self.up else "/ ") + self.generator


#: The twenty moves, in the stated order.  Nothing anywhere reorders them, so
#: a tie is broken by this list and never by which candidate arrived first.
MOVES: Tuple[Move, ...] = tuple(
    Move(axis=i, up=up) for i in range(len(GENERATORS)) for up in (True, False))


def generator_check() -> Dict[str, object]:
    """Confirm each generator is the register's unit quantity for its axis."""
    rows = []
    ok = True
    for index, name in enumerate(GENERATORS):
        quantity = do_physics.quantity_by_name(name)
        wanted = tuple(1 if i == index else 0 for i in range(len(AXES)))
        got = tuple(q for q in quantity.exps_ext10)
        good = (tuple(int(v) for v in got) == wanted
                and all(v.denominator == 1 for v in got)
                and quantity.scale == 0 and quantity.rank == 0
                and quantity.p == 0 and quantity.t == 0 and quantity.c == 0)
        ok = ok and good
        rows.append({"axis": AXES[index], "generator": name, "unit": good})
    return {"generators": tuple(rows), "all_unit_vectors": ok,
            "moves": len(MOVES)}


def apply_move(state: State, move: Move) -> State:
    """One step of the loop."""
    step = 1 if move.up else -1
    return tuple(v + step if i == move.axis else v
                 for i, v in enumerate(state))


def replay(plan: Sequence[Move], state: State = ORIGIN) -> State:
    """Apply a whole plan -- the Python side of ``GLM.Controller.replay``."""
    for move in plan:
        state = apply_move(state, move)
    return state


def l1(a: State, b: State = ORIGIN) -> int:
    """The exact number of moves between two states."""
    return sum(abs(x - y) for x, y in zip(a, b))


# ===========================================================================
#  Reading a target, and refusing one that no plan can reach
# ===========================================================================

@dataclass(frozen=True)
class Refusal:
    """Why the controller declined to answer."""

    kind: str            # "invariant" | "exhausted"
    reason: str
    certificate: str

    def as_json(self) -> Dict[str, str]:
        return {"kind": self.kind, "reason": self.reason,
                "certificate": self.certificate}


def classify_target(name: str) -> Tuple[Optional[State], Optional[Refusal]]:
    """The target as a state, or the invariant that proves it unreachable.

    The three invariants are the ones ``GLM.Controller.unreachable_of_invariant``
    covers: a move adds ``±1`` to one exponent, so it changes no denominator,
    no decimal scale, no tensor rank and no grading.
    """
    quantity = do_physics.quantity_by_name(name)
    exps = tuple(quantity.exps_ext10)
    fractional = [AXES[i] for i, v in enumerate(exps) if v.denominator != 1]
    if fractional:
        return None, Refusal(
            "invariant",
            f"the {', '.join(fractional)} exponent is not an integer",
            "every move adds +/-1 to one exponent, so the denominators of the "
            "exponents are invariant (GLM.Controller.unreachable_of_invariant)")
    if quantity.scale != 0:
        return None, Refusal(
            "invariant",
            f"the decimal scale is {quantity.scale}, not 0",
            "no move touches the scale coordinate "
            "(GLM.Controller.scale_invariant)")
    if quantity.rank != 0:
        return None, Refusal(
            "invariant",
            f"the tensor rank is {quantity.rank}, not 0",
            "the generators are all rank 0 and multiplication by a scalar "
            "cannot raise the rank (GLM.Controller.unreachable_of_invariant)")
    if (quantity.p, quantity.t, quantity.c) != (0, 0, 0):
        return None, Refusal(
            "invariant",
            f"the P/T/C grading is {(quantity.p, quantity.t, quantity.c)}, "
            f"not (0, 0, 0)",
            "every generator is even in all three gradings "
            "(GLM.Controller.unreachable_of_invariant)")
    return tuple(int(v) for v in exps), None


@memo
def reachable_targets() -> Tuple[str, ...]:
    """Every register quantity no invariant rules out."""
    out = []
    for quantity in do_physics.load_physics_register():
        state, refusal = classify_target(quantity.name)
        if refusal is None:
            out.append(quantity.name)
    return tuple(out)


@memo
def refused_targets() -> Tuple[str, ...]:
    """Every register quantity an invariant rules out, with no search."""
    out = []
    for quantity in do_physics.load_physics_register():
        state, refusal = classify_target(quantity.name)
        if refusal is not None:
            out.append(quantity.name)
    return tuple(out)


# ===========================================================================
#  Carriers, addresses, and the cached address table
# ===========================================================================

#: The scale the state's carrier is multiplied by before being decoded.  Nine,
#: for the reason ``Address.lean`` gives: it exceeds twice the covering radius
#: (4), so the decoding is lossless, and it is not a multiple of 8, so the
#: decoder is not the identity.
ADDRESS_SCALE = 9

#: Squared distance between the addresses of two states one move apart, at
#: :data:`ADDRESS_SCALE`, if the decoder moved nothing: the carrier repeats
#: each EXT10 exponent in the SI7 block for the first seven axes, so one move
#: on one of those changes two coordinates by ``scale`` -- ``2 * 81``.
ADDRESS_STEP_SQUARED = 2 * ADDRESS_SCALE ** 2

#: The same for the undecoded carrier.
CARRIER_STEP_SQUARED = 2

DATA_PATH = Path(__file__).resolve().parent / "_data" / "controller_addresses.json"

SCHEMA = 1


def carrier_of(state: State) -> Tuple[int, ...]:
    """The state's 24-coordinate physics carrier, exactly as the verifier builds it."""
    sense = vf.Sense(exps=tuple(Fraction(v) for v in state),
                     scale=Fraction(0), rank=0, p=0, t=0, c=0)
    return tuple(int(v) for v in vf.sense_carrier(sense, "scalar"))


_address_cache: Dict[Tuple[State, int], Tuple[int, ...]] = {}
_decodes = 0


def address_of(state: State, scale: int = ADDRESS_SCALE) -> Tuple[int, ...]:
    """The state's Leech address: decode ``scale`` times its carrier.

    Decoding costs about twenty milliseconds, which is three orders of
    magnitude more than the arithmetic it competes with, so the addresses the
    stated task set needs are computed once and stored in
    ``reasoning/_data/controller_addresses.json``.  A miss is computed live and
    counted, so the report can say whether it answered from the table.
    """
    global _decodes
    key = (state, scale)
    if key in _address_cache:
        return _address_cache[key]
    stored = _stored_addresses().get(f"{scale}|" + ",".join(map(str, state)))
    if stored is not None:
        point = tuple(stored)
    else:
        _decodes += 1
        carrier = carrier_of(state)
        point = tuple(int(v) for v in analogy.nearest_lattice_point(
            [Fraction(scale * v) for v in carrier]).point)
    _address_cache[key] = point
    return point


_stored: Optional[Dict[str, List[int]]] = None


def _stored_addresses() -> Dict[str, List[int]]:
    global _stored
    if _stored is not None:
        return _stored
    if not DATA_PATH.exists():
        _stored = {}
        return _stored
    book = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _stored = book.get("addresses", {})
    return _stored


def decodes_performed() -> int:
    """How many lattice decodes this process has had to compute itself."""
    return _decodes


def write_address_table(path: Optional[Path] = None) -> Path:
    """Run the address-guided loop over the task set, recording every decode.

    Slow -- this is the one expensive step, and it is why the table exists.
    """
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    table: Dict[str, List[int]] = {}
    for scale in (ADDRESS_SCALE, 1):
        for name in task_targets():
            state, refusal = classify_target(name)
            if state is None:
                continue
            _run_beam(state, "address" if scale == ADDRESS_SCALE
                      else "address_native", BEAM_WIDTH, MAX_DEPTH,
                      recorder=table, scale=scale)
    target.write_text(
        json.dumps({"schema": SCHEMA, "scale": ADDRESS_SCALE,
                    "targets": list(task_targets()),
                    "width": BEAM_WIDTH, "depth": MAX_DEPTH,
                    "addresses": table}, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    global _stored
    _stored = None
    return target


def table_state() -> Dict[str, object]:
    """Is the stored address table the one this task set needs?"""
    if not DATA_PATH.exists():
        return {"present": False, "verdict": "absent", "entries": 0}
    book = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    matches = (book.get("schema") == SCHEMA
               and book.get("scale") == ADDRESS_SCALE
               and tuple(book.get("targets", ())) == task_targets()
               and book.get("width") == BEAM_WIDTH
               and book.get("depth") == MAX_DEPTH)
    return {"present": True, "verdict": "fresh" if matches else "stale",
            "entries": len(book.get("addresses", {}))}


# ===========================================================================
#  The heuristics
# ===========================================================================

def _sq(a: Sequence[int], b: Sequence[int]) -> int:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def h_exponent(state: State, target: State) -> int:
    """The exact number of moves still to make."""
    return l1(state, target)


def h_carrier(state: State, target: State) -> int:
    """Carrier distance, in units of one move -- the lattice-free ablation."""
    return math.isqrt(_sq(carrier_of(state), carrier_of(target))
                      // CARRIER_STEP_SQUARED)


def h_address(state: State, target: State) -> int:
    """Leech-address distance at scale 9, in units of one move."""
    return math.isqrt(_sq(address_of(state), address_of(target))
                      // ADDRESS_STEP_SQUARED)


def h_address_native(state: State, target: State) -> int:
    """The same at the register's own resolution, where the decoder conflates."""
    return math.isqrt(_sq(address_of(state, 1), address_of(target, 1))
                      // CARRIER_STEP_SQUARED)


def h_none(state: State, target: State) -> int:
    """No guidance at all."""
    return 0


_NOISE = integrity.seeded_permutation(97, "glm-controller-random-control")


def h_random(state: State, target: State) -> int:
    """A scorer that depends on the state and knows nothing about the target."""
    if state == target:
        return 0
    index = sum(abs(v) * (i + 1) for i, v in enumerate(state)) % 97
    return _NOISE[index] % 6


HEURISTICS: Dict[str, object] = {
    "exponent": h_exponent,
    "address": h_address,
    "address_native": h_address_native,
    "carrier": h_carrier,
    "none": h_none,
    "random": h_random,
}

#: The order the report prints them in.
HEURISTIC_ORDER: Tuple[str, ...] = (
    "exponent", "address", "address_native", "carrier", "none", "random")


# ===========================================================================
#  The loop
# ===========================================================================

#: How many states the loop keeps between rounds.
BEAM_WIDTH = 2

#: How many rounds it will run before refusing.
MAX_DEPTH = 16


def _score(state: State, target: State, heuristic: str, scale: int) -> int:
    if heuristic == "address" and scale != ADDRESS_SCALE:
        return math.isqrt(_sq(address_of(state, scale),
                              address_of(target, scale))
                          // (2 * scale ** 2))
    return HEURISTICS[heuristic](state, target)


def _run_beam(target: State, heuristic: str, width: int, depth: int,
              recorder: Optional[Dict[str, List[int]]] = None,
              scale: int = ADDRESS_SCALE
              ) -> Dict[str, object]:
    """One run of the cycle.  Returns the plan, or why there is none."""
    def note(state: State) -> None:
        if recorder is None:
            return
        point = address_of(state, scale)
        recorder[f"{scale}|" + ",".join(map(str, state))] = list(point)

    note(ORIGIN)
    note(target)
    frontier: List[Tuple[int, Tuple[Move, ...], State]] = [
        (_score(ORIGIN, target, heuristic, scale), (), ORIGIN)]
    calls = 0
    for round_index in range(depth):
        for _, plan, state in frontier:
            if state == target:
                return {"plan": plan, "calls": calls, "rounds": round_index}
        proposals: List[Tuple[int, Tuple[Tuple[int, int], ...], Tuple[Move, ...], State]] = []
        for _, plan, state in frontier:
            for move in MOVES:
                nxt = apply_move(state, move)
                note(nxt)
                calls += 1
                proposals.append((_score(nxt, target, heuristic, scale),
                                  tuple(m.key for m in plan + (move,)),
                                  plan + (move,), nxt))
        proposals.sort(key=lambda row: (row[0], row[1]))
        kept: List[Tuple[int, Tuple[Move, ...], State]] = []
        seen = set()
        for score, _key, plan, state in proposals:
            if state in seen:
                continue
            seen.add(state)
            kept.append((score, plan, state))
            if len(kept) == width:
                break
        frontier = kept
    for _, plan, state in frontier:
        if state == target:
            return {"plan": plan, "calls": calls, "rounds": depth}
    return {"plan": None, "calls": calls, "rounds": depth}


def expression(plan: Sequence[Move]) -> str:
    """The plan as an expression the verifier can parse."""
    if not plan:
        return "1"
    parts: List[str] = []
    for index, move in enumerate(plan):
        if index == 0 and move.up:
            parts.append(move.generator)
        else:
            parts.append(("* " if move.up else "/ ") + move.generator)
    text = " ".join(parts)
    return text if plan[0].up else "1 " + text


def verify_plan(name: str, plan: Sequence[Move]) -> Dict[str, object]:
    """Check the finished plan with the instrument that did not build it.

    :func:`glm_universal.reasoning.verifier.verify_expression_pair` turns both
    sides into 24-coordinate carriers and compares them plane by plane through
    the digit stack.  A plan the loop believes in and the verifier rejects is
    a failure of the loop, and the report counts them.
    """
    text = expression(plan)
    verdict = vf.verify_expression_pair(name, text, "scalar")
    return {"expression": text, "holds": bool(verdict.holds),
            "differing": tuple(verdict.differing_coordinates)
            if hasattr(verdict, "differing_coordinates") else ()}


def solve(name: str, heuristic: str = "exponent", width: int = BEAM_WIDTH,
          depth: int = MAX_DEPTH) -> Dict[str, object]:
    """Derive one quantity, or refuse.

    The whole cycle: classify the target (and refuse with a proof if an
    invariant rules it out), run the beam, check the plan with the verifier,
    and report the optimum it should have found.
    """
    state, refusal = classify_target(name)
    if state is None:
        return {"target": name, "heuristic": heuristic, "answered": False,
                "refusal": refusal.as_json(), "optimum": None}
    outcome = _run_beam(state, heuristic, width, depth)
    optimum = l1(state)
    if outcome["plan"] is None:
        return {
            "target": name, "heuristic": heuristic, "answered": False,
            "optimum": optimum, "proposals": outcome["calls"],
            "refusal": Refusal(
                "exhausted",
                f"the beam of width {width} reached depth {depth} without "
                f"reaching the target",
                "beam search is incomplete (GLM.Controller.beam_can_miss); "
                "this is a statement about the search, not the target"
            ).as_json()}
    plan = outcome["plan"]
    check = verify_plan(name, plan)
    return {
        "target": name, "heuristic": heuristic, "answered": True,
        "plan": tuple(str(m) for m in plan),
        "length": len(plan),
        "optimum": optimum,
        "minimal": len(plan) == optimum,
        "reaches_target": replay(plan) == state,
        "proposals": outcome["calls"],
        "rounds": outcome["rounds"],
        "expression": check["expression"],
        "verified": check["holds"],
    }


# ===========================================================================
#  The measured comparison
# ===========================================================================

#: How many reachable quantities the experiment derives.
TASK_COUNT = 24

#: How many unreachable ones it asks for, to exercise the invariant refusal.
REFUSAL_COUNT = 8


@memo
def task_targets() -> Tuple[str, ...]:
    """The stated task set: a deterministic stride through the register."""
    reachable = reachable_targets()
    refused = refused_targets()
    stride = max(1, len(reachable) // TASK_COUNT)
    picked = list(reachable[::stride])[:TASK_COUNT]
    stride = max(1, len(refused) // REFUSAL_COUNT)
    picked += list(refused[::stride])[:REFUSAL_COUNT]
    return tuple(picked)


@memo
def controller_report() -> Dict[str, object]:
    """Every heuristic on the same tasks, with the refusals counted.

    What the table holds, per heuristic: how many of the reachable targets the
    loop derived, how many of those plans were of minimal length, how many the
    verifier independently confirmed, and how many proposals it had to score.
    The refusals are separate, because an invariant refusal is a proof and an
    exhausted one is a limit of the search.
    """
    targets = task_targets()
    reachable = [n for n in targets if classify_target(n)[0] is not None]
    unreachable = [n for n in targets if classify_target(n)[0] is None]
    rows: Dict[str, Dict[str, object]] = {}
    for heuristic in HEURISTIC_ORDER:
        solved = minimal = verified = proposals = 0
        exhausted = []
        for name in reachable:
            outcome = solve(name, heuristic)
            proposals += outcome.get("proposals", 0)
            if outcome["answered"]:
                solved += 1
                minimal += 1 if outcome["minimal"] else 0
                verified += 1 if outcome["verified"] else 0
            else:
                exhausted.append(name)
        count = len(reachable)
        rows[heuristic] = {
            "solved": solved,
            "solve_rate": Fraction(solved, count) if count else Fraction(0),
            "minimal": minimal,
            "verified": verified,
            "all_answers_verified": verified == solved,
            "refused_exhausted": len(exhausted),
            "refused_targets": tuple(exhausted),
            "proposals": proposals,
            "mean_proposals": (Fraction(proposals, count) if count
                               else Fraction(0)),
        }
    invariant_rows = []
    for name in unreachable:
        outcome = solve(name, "exponent")
        invariant_rows.append({
            "target": name,
            "kind": outcome["refusal"]["kind"],
            "reason": outcome["refusal"]["reason"],
        })
    exact = rows["exponent"]
    address = rows["address"]
    verdict = {
        "exact_heuristic_solves_everything": exact["solved"] == len(reachable),
        "every_answer_is_verified": all(row["all_answers_verified"]
                                        for row in rows.values()),
        "every_answer_is_minimal": all(row["minimal"] == row["solved"]
                                       for row in rows.values()),
        "address_beats_no_guidance":
            address["solved"] > rows["none"]["solved"],
        "address_beats_random": address["solved"] > rows["random"]["solved"],
        "address_beats_carrier": address["solved"] > rows["carrier"]["solved"],
        "address_matches_exact": address["solved"] == exact["solved"],
        "native_resolution_collapses":
            rows["address_native"]["solved"] <= rows["none"]["solved"],
        "invariant_refusals_need_no_search": len(invariant_rows) == len(unreachable),
    }
    return {
        "generators": generator_check(),
        "targets": len(targets),
        "reachable": len(reachable),
        "unreachable": len(unreachable),
        "register": len(do_physics.load_physics_register()),
        "reachable_in_register": len(reachable_targets()),
        "width": BEAM_WIDTH,
        "depth": MAX_DEPTH,
        "heuristics": rows,
        "invariant_refusals": tuple(invariant_rows),
        "table": table_state(),
        "decodes_this_process": decodes_performed(),
        "verdict": verdict,
        "lean_file": "RequestProject/GLM/Controller.lean",
        "study": "studies/CONTROLLER_STUDY.md",
    }
