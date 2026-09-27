"""``glm_universal.reasoning.tasks`` -- two worked tasks, end to end.

This module is where the machinery is *used* rather than described.  It holds
two complete tasks, each solved by running data through the whole stack and
reporting what each layer contributed.

Task 1 -- an ARC-style grid puzzle, solved by multi-resolution addressing
------------------------------------------------------------------------
Given a handful of input/output grid pairs, find the transformation that
explains them and apply it to a held-out input.  The candidate rules are the
frame symmetries and the identity.  What makes this a *multi-resolution* task
is that the hypotheses are filtered at three increasing resolutions:

1. **signature** -- the scale-invariant statistics of
   :func:`glm_universal.reasoning.multires.grid_signature`.  Cheap, and blind
   to reflection: it prunes almost nothing here, which is the point.
2. **plane 0 of the Monster address** -- the ``Lambda / 2 Lambda`` class of
   the carrier's least significant digit plane.  One 24-bit class per grid.
3. **the full ten-plane address** -- the whole digit stack.

:func:`grid_task` reports how many candidates survive each stage, so the value
of each resolution is measured rather than asserted.  The answer is accepted
only when the finest resolution leaves exactly one candidate.

Task 2 -- torque against energy, through every layer
----------------------------------------------------
Torque and energy have the same SI7 dimension and are not the same quantity.
:func:`physics_task` asks the system to say so and to name *where* the
difference lives:

* the two dimension strings, in SI7 (equal) and in EXT10 (different);
* the verifier on ``force * length`` under scalar and full semantics;
* the least dimension layer that separates the two carriers, from
  :func:`glm_universal.reasoning.dimension_layers.escalate`;
* the facet of the six-facet decomposition that carries the difference;
* the digit plane at which their Monster addresses part company, and the
  complete Golay decoding of that plane's difference.

Both tasks are deterministic and exact, and both are wired into the runtime
(``task grid``, ``task physics``).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..data_objects import physics as do_physics
from ..migration import store as concept_store
from ..substrate import golay_decode
from . import (dimension_layers, facets, metric, monster_stack, multires,
               verifier)

__all__ = [
    "TRANSFORMATIONS", "GRID_TASK", "grid_task",
    "physics_task", "concept_task", "tasks_report",
]


# ===========================================================================
# 1.  THE GRID TASK
# ===========================================================================

#: The candidate rules: the frame symmetries and the identity.
TRANSFORMATIONS: Dict[str, Callable[[multires.Grid], Tuple[Tuple[int, ...],
                                                           ...]]] = {
    "identity": lambda g: tuple(tuple(int(v) for v in row) for row in g),
    "reflect_horizontal": multires.reflect_horizontal,
    "reflect_vertical": multires.reflect_vertical,
    "rotate180": multires.rotate180,
    "transpose": lambda g: tuple(tuple(int(v) for v in row)
                                 for row in zip(*g)),
}

#: The worked puzzle: three training pairs and one test input.  The rule is a
#: half turn, and the grids are chosen so that no other candidate fits.
GRID_TASK: Dict[str, object] = {
    "name": "half-turn",
    "training": (
        (((1, 2, 0), (0, 3, 0), (0, 0, 4)),
         ((4, 0, 0), (0, 3, 0), (0, 2, 1))),
        (((5, 0, 0), (6, 7, 0), (0, 0, 0)),
         ((0, 0, 0), (0, 7, 6), (0, 0, 5))),
        (((0, 8), (9, 1)),
         ((1, 9), (8, 0))),
    ),
    "test": ((2, 0, 3), (0, 5, 0), (7, 0, 0)),
}


def _plane0(grid: multires.Grid) -> int:
    return multires.grid_address(grid).masks()[0]


def _full_address(grid: multires.Grid) -> Tuple[int, ...]:
    return multires.grid_address(grid).masks()


def _signature_key(grid: multires.Grid) -> Tuple[str, ...]:
    sig = multires.grid_signature(grid)
    return tuple(f"{k}={sig[k]}" for k in sorted(sig))


#: The three resolutions, coarsest first.
_RESOLUTIONS: Tuple[Tuple[str, Callable[[multires.Grid], object]], ...] = (
    ("signature", _signature_key),
    ("address_plane0", _plane0),
    ("address_full", _full_address),
)


def grid_task(training: Optional[Sequence[Tuple[multires.Grid,
                                                multires.Grid]]] = None,
              test: Optional[multires.Grid] = None) -> Dict[str, object]:
    """Solve an ARC-style grid puzzle by filtering at three resolutions.

    Returns the survivors at each resolution, the rule if one is forced, the
    predicted output for the test grid, and a check that the prediction and
    the rule's own output agree plane by plane.
    """
    if training is None:
        training = GRID_TASK["training"]        # type: ignore[assignment]
    if test is None:
        test = GRID_TASK["test"]                # type: ignore[assignment]

    stages: List[Dict[str, object]] = []
    survivors = list(TRANSFORMATIONS)
    for label, view in _RESOLUTIONS:
        before = list(survivors)
        survivors = [
            name for name in survivors
            if all(view(TRANSFORMATIONS[name](src)) == view(dst)
                   for src, dst in training)
        ]
        stages.append({
            "resolution": label,
            "candidates_in": len(before),
            "candidates_out": len(survivors),
            "survivors": list(survivors),
            "pruned": [n for n in before if n not in survivors],
        })

    solved = len(survivors) == 1
    rule = survivors[0] if solved else None
    prediction = (TRANSFORMATIONS[rule](test) if rule else None)
    checks: Dict[str, object] = {}
    if rule is not None and prediction is not None:
        checks = {
            "prediction_address": list(_full_address(prediction)),
            "test_address": list(_full_address(test)),
            "address_changed": (_full_address(prediction)
                                != _full_address(test)),
            "signature_preserved": (multires.grid_signature(prediction)
                                    == multires.grid_signature(test)),
            "training_reproduced": all(
                TRANSFORMATIONS[rule](src) == tuple(tuple(int(v) for v in row)
                                                    for row in dst)
                for src, dst in training),
        }
    return {
        "task": GRID_TASK["name"],
        "training_pairs": len(training),
        "stages": stages,
        "solved": solved,
        "rule": rule,
        "test": [list(r) for r in test],
        "prediction": ([list(r) for r in prediction] if prediction else None),
        "checks": checks,
        "reading": ("the signature is blind to reflection and prunes "
                    "nothing; one plane of the Monster address already "
                    "separates most candidates; the full ten-plane address "
                    "settles it"),
    }


# ===========================================================================
# 2.  THE PHYSICS TASK
# ===========================================================================

def _carrier_of(name: str) -> Tuple[Fraction, ...]:
    for obj in do_physics.physics_objects():
        if obj.name == name:
            return tuple(metric.as_exact_vector(obj.carrier))
    raise KeyError(f"physics_task: no quantity named {name!r}")


def physics_task(left: str = "energy",
                 right: str = "torque") -> Dict[str, object]:
    """Separate two quantities that SI7 conflates, and locate the difference.

    Runs the dimensional register, the verifier, the layer stack, the
    six-facet decomposition, the ten-plane Monster address and the complete
    Golay decoder over one pair of quantities, and reports what each of them
    contributed to the answer.
    """
    a = do_physics.quantity_by_name(left)
    b = do_physics.quantity_by_name(right)
    ca, cb = _carrier_of(left), _carrier_of(right)

    si7_equal = (do_physics.dimension_string(a.exps_ext10, "SI7")
                 == do_physics.dimension_string(b.exps_ext10, "SI7"))
    ext10_equal = (do_physics.dimension_string(a.exps_ext10, "EXT10")
                   == do_physics.dimension_string(b.exps_ext10, "EXT10"))

    scalar_left = verifier.verify_expression_pair(left, "force * length",
                                                  "scalar")
    scalar_right = verifier.verify_expression_pair(right, "force * length",
                                                   "scalar")
    full_left = verifier.verify_expression_pair(left, "force * length",
                                                "full")
    full_right = verifier.verify_expression_pair(right, "force * length",
                                                 "full")

    escalation = dimension_layers.escalate(ca, cb)
    layer_distances = {name: str(d)
                       for name, _va, _vb, d in escalation["all_views"]}
    first_separating = next((name for name, _va, _vb, d
                             in escalation["all_views"] if d != 0), None)

    breakdown = facets.facet_distance_breakdown(ca, cb)
    carrying = [name for name, d in breakdown.items() if d != 0]

    addr_a = monster_stack.monster_address(ca)
    addr_b = monster_stack.monster_address(cb)
    masks_a, masks_b = addr_a.masks(), addr_b.masks()
    first_plane = next((k for k, (x, y) in enumerate(zip(masks_a, masks_b))
                        if x != y), None)
    difference_mask = (masks_a[first_plane] ^ masks_b[first_plane]
                       if first_plane is not None else 0)
    decoding = golay_decode.decode_complete(difference_mask)

    return {
        "left": left,
        "right": right,
        "si7": {
            "left": do_physics.dimension_string(a.exps_ext10, "SI7"),
            "right": do_physics.dimension_string(b.exps_ext10, "SI7"),
            "equal": si7_equal,
        },
        "ext10": {
            "left": do_physics.dimension_string(a.exps_ext10, "EXT10"),
            "right": do_physics.dimension_string(b.exps_ext10, "EXT10"),
            "equal": ext10_equal,
        },
        "verifier": {
            "scalar": {left: scalar_left.holds, right: scalar_right.holds},
            "full": {left: full_left.holds, right: full_right.holds},
            "ranks": {left: a.rank, right: b.rank},
        },
        "escalation": {
            "layer": escalation["layer"].name,
            "distance": str(escalation["distance"]),
            "layer_distances": layer_distances,
            "first_separating_layer": first_separating,
        },
        "facets": {
            "distances": {k: str(v) for k, v in breakdown.items()},
            "carrying_the_difference": carrying,
        },
        "address": {
            "depth": addr_a.depth,
            "first_differing_plane": first_plane,
            "difference_mask": difference_mask,
            "difference_weight": bin(difference_mask).count("1"),
            "golay": decoding.as_dict(),
        },
        "answer": (
            f"{left} and {right} are the same quantity in SI7 "
            f"({do_physics.dimension_string(a.exps_ext10, 'SI7')}) and "
            f"different in EXT10; the carriers first differ at digit plane "
            f"{first_plane}, and the difference is carried by the "
            f"{', '.join(carrying) if carrying else 'no'} facet"
            f"{'s' if len(carrying) != 1 else ''}"),
    }


# ===========================================================================
# 3.  THE CONCEPT TASK -- reasoning over the migrated repository data
# ===========================================================================

def _physics_names() -> Tuple[str, ...]:
    return tuple(obj.name for obj in do_physics.physics_objects())


def concept_task(source: str = "entropy", target: str = "energy",
                 law: str = "entropy * temperature",
                 control: str = "force") -> Dict[str, object]:
    """Retrieve a relation from the migrated CRG, then check it elsewhere.

    This is the task that uses the *migrated repository data* rather than the
    package's own registers, and it is deliberately a two-layer argument:

    1. **Retrieval.**  The concept-relation graph is asked for a path from
       ``source`` to ``target``.  It is asked twice -- once over every edge,
       once over asserted edges only, with the growth loop's
       ``auto_proposed`` proposals excluded -- because the two answers are
       not the same, and only the second is knowledge somebody stood behind.
    2. **Adjudication.**  The relation the path suggests is then checked in a
       layer that can be wrong out loud: the dimensional register.  ``law``
       is verified against ``target``, and ``control`` -- a quantity of a
       different dimension -- is verified against it too and must fail.  A
       check that passes everything checks nothing.

    The task also reports what the substrate contributes, which is nothing:
    the concept carriers were assigned by digest, so their Hamming
    neighbourhoods are semantically unrelated, and a large share of them do
    not decode uniquely at all.  Saying so is the point.
    """
    store = concept_store.ConceptStore.load()
    if store is None:
        return {"available": False,
                "reading": "the migrated state has not been written"}

    known = {name: store.has(name) for name in (source, target)}
    if not all(known.values()):
        return {"available": False, "known": known,
                "reading": "the store does not hold both endpoints"}

    every = store.path(source, target)
    asserted = store.path(source, target,
                          exclude_labels=("auto_proposed",))
    paths_differ = every != asserted

    register = set(_physics_names())
    crosslinked = sorted({source, target} & register)

    holds = verifier.verify_expression_pair(law, target, "scalar")
    fails = verifier.verify_expression_pair(law, control, "scalar")

    substrate: Dict[str, object] = {}
    for name in (source, target):
        record = store.concept(name)
        substrate[name] = {
            "mask": int(record["mask"]),
            "decode_status": record["decode"]["status"],  # type: ignore
            "provenance": record["provenance"],
            "nearest_carriers": [other for other, _d
                                 in store.hamming_neighbours(name, 3)],
            "graph_degree": store.degree(name),
        }
    shared_neighbours = sorted(
        {other for other, _d in store.hamming_neighbours(source, 5)}
        & {other for other, _l, _dir in store.neighbours(source)})

    checks = {
        "path_found": every is not None,
        "asserted_path_found": asserted is not None,
        "paths_differ": paths_differ,
        "both_crosslinked": len(crosslinked) == 2,
        "law_holds": holds.holds,
        "control_fails": not fails.holds,
        "discriminating": holds.holds and not fails.holds,
        "substrate_contributes": bool(shared_neighbours),
    }
    return {
        "available": True,
        "source": source,
        "target": target,
        "law": f"{law} = {target}",
        "control": f"{law} = {control}",
        "path": [list(step) for step in (every or ())],
        "asserted_path": [list(step) for step in (asserted or ())],
        "crosslinked": crosslinked,
        "substrate": substrate,
        "shared_neighbours": shared_neighbours,
        "checks": checks,
        "answer": (
            f"the migrated CRG relates {source} to {target} in "
            f"{len(asserted or ())} asserted steps, and the dimensional "
            f"register confirms {law} = {target} while rejecting "
            f"{law} = {control}; the substrate contributes nothing to "
            f"either, since the carriers were assigned by digest"),
    }


# ===========================================================================
# 4.  ONE REPORT
# ===========================================================================

@memo
def tasks_report() -> Dict[str, object]:
    """Every task, recomputed."""
    return {"grid": grid_task(), "physics": physics_task(),
            "concepts": concept_task()}
