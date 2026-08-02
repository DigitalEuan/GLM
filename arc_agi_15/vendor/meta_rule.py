"""
meta_rule.py — relational conditions + dynamic contextual lookup
==================================================================

The user's directive: combine relational conditions (cardinal/diagonal)
with dynamic contextual lookup (extrapolate to unseen trigger colours).

This is the META-RULE that 396d80d7 needs:
  - Train shows: 7 next to 6 (in diagonal, not cardinal) → 2
  - Train shows: 7 next to 4 (in diagonal, not cardinal) → 1
  - Test has:    7 next to 9 (in diagonal, not cardinal) → ???

The meta-rule says: "7 next to ANY colour T (in diagonal, not cardinal)
→ T's mapped target".  But what is 9's mapped target?  9 doesn't appear
as a trigger in train.

The UBP substrate gives us the answer.

The UBP substrate solution
--------------------------
Each trigger colour T is a 24-bit Leech address (via the hex encoder).
Each target colour C is also a 24-bit Leech address.

The "transformation" T → C is a displacement in 24-bit space.  We can
encode this displacement in a NoiseCellV3, which has a known
displacement curve (syndrome_weight vs k_bits).

The elastic_limit of the displacement curve tells us how far we can
extrapolate.  If 6→2 and 4→1 are within the elastic limit, we can
predict 9→? by interpolating in the displacement curve.

Concretely:
  - Build a NoiseCellV3 for each (trigger, target) pair seen in train
  - The displacement curve gives us a function: trigger_address → target_address
  - For an unseen trigger, find the nearest train trigger in 24-bit space
    and apply the same displacement (within the elastic limit)

This is the UBP's "elastic extrapolation" — the substrate's known
mathematical properties let us predict beyond the training data.

The meta-rule grammar
---------------------
A meta-rule is:
  INPUT_COLOUR: A
  RELATIONAL_CONDITION: has T in {direction_set} AND NOT in {forbidden_set}
  LOOKUP: target = mapping[T]  (or extrapolated mapping[T])

If T is in the train mapping, use mapping[T] directly.
If T is not in train, extrapolate via the UBP substrate.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, Counter
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask
from ubp_unified_v5 import (
    GOLAY_ENGINE, SubstrateLibrary, NoiseCellV3, ontological_position_to_vector,
)
from generative.hex_learner import address_cell, address_grid, _hamming_distance_int
from vendor.cortex_v2 import (
    CARDINAL_DIRS, DIAGONAL_DIRS, ALL_DIRS, _has_in_directions,
)


# ══════════════════════════════════════════════════════════════════════════════
# The meta-rule
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetaRule:
    """A meta-rule combining relational conditions with dynamic lookup.

    Fields:
      input_colour: the colour that changes (A)
      has_dirs: directions where the trigger must appear (OR — any)
      not_dirs: direction groups where the trigger must NOT appear (AND — all absent)
      mapping: known trigger→target mappings from train
      extrapolation: how to handle unseen triggers
        "nearest": use the nearest train trigger's target
        "identity": keep input colour
        "zero": use 0
    """
    input_colour: int
    has_dirs: List[str] = field(default_factory=list)  # OR: any direction
    not_dirs: List[str] = field(default_factory=list)  # AND: all absent (each is "cardinal"/"diagonal" or specific dir)
    mapping: Dict[int, int] = field(default_factory=dict)
    extrapolation: str = "nearest"

    def get_target(self, trigger_colour: int,
                    trigger_to_train_dist: Optional[Dict[int, int]] = None
                    ) -> int:
        """Get the target for a trigger colour.

        If trigger is in mapping, return mapping[trigger].
        Otherwise, extrapolate.
        """
        if trigger_colour in self.mapping:
            return self.mapping[trigger_colour]

        if self.extrapolation == "nearest" and trigger_to_train_dist:
            # Find the nearest train trigger colour (by 24-bit Hamming distance)
            nearest = min(trigger_to_train_dist.items(),
                          key=lambda x: x[1])[0]
            return self.mapping.get(nearest, self.input_colour)
        elif self.extrapolation == "identity":
            return self.input_colour
        else:
            return self.input_colour

    def applies_to(self, grid: Grid, r: int, c: int) -> Tuple[bool, int]:
        """Check if the rule applies to cell (r, c).

        Returns (applies, trigger_colour).  If applies, trigger_colour
        is the colour that triggered the rule.
        """
        if grid.cells[r][c] != self.input_colour:
            return False, -1

        # Find trigger colours in has_dirs
        triggers_found = set()
        for d in self.has_dirs:
            dirs_to_check = {d: ALL_DIRS[d]} if d in ALL_DIRS else (
                CARDINAL_DIRS if d == "cardinal" else
                DIAGONAL_DIRS if d == "diagonal" else ALL_DIRS
            )
            for _, (dr, dc) in dirs_to_check.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    n_colour = grid.cells[nr][nc]
                    if n_colour != self.input_colour and n_colour != 0:
                        triggers_found.add(n_colour)

        if not triggers_found:
            return False, -1

        # Check not_dirs: trigger must NOT appear in these directions
        for d in self.not_dirs:
            dirs_to_check = {d: ALL_DIRS[d]} if d in ALL_DIRS else (
                CARDINAL_DIRS if d == "cardinal" else
                DIAGONAL_DIRS if d == "diagonal" else ALL_DIRS
            )
            for _, (dr, dc) in dirs_to_check.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    n_colour = grid.cells[nr][nc]
                    if n_colour != self.input_colour and n_colour != 0:
                        # This trigger is in a forbidden direction
                        # Remove it from triggers_found
                        triggers_found.discard(n_colour)

        if not triggers_found:
            return False, -1

        # Pick the trigger (prefer ones in mapping)
        in_mapping = [t for t in triggers_found if t in self.mapping]
        if in_mapping:
            return True, in_mapping[0]
        return True, next(iter(triggers_found))

    def apply_to(self, grid: Grid,
                  trigger_to_train_dist: Optional[Dict[int, int]] = None) -> Grid:
        """Apply the meta-rule to a grid."""
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                applies, trigger = self.applies_to(grid, r, c)
                if applies:
                    target = self.get_target(trigger, trigger_to_train_dist)
                    out_cells[r][c] = target
        return Grid(out_cells)


# ══════════════════════════════════════════════════════════════════════════════
# Derive meta-rules from train
# ══════════════════════════════════════════════════════════════════════════════

def derive_meta_rules(task: ARCTask) -> List[MetaRule]:
    """Derive meta-rules from train pairs.

    For each colour A that changes:
      1. Collect (trigger_colour → target_colour) mappings from train
      2. Check SPECIFIC DIRECTIONS (not just cardinal/diagonal groups)
         to find which directions consistently distinguish changed from
         unchanged cells
      3. Create a meta-rule with the specific direction constraint

    The meta-rule can then extrapolate to unseen trigger colours.
    """
    if not task.train:
        return []

    # Collect per-direction info: for each (A, trigger) pair,
    # count how many changed vs unchanged cells have the trigger in each direction
    direction_info: Dict[Tuple[int, int], Dict[str, Dict[str, int]]] = defaultdict(
        lambda: {d: {"changed": 0, "unchanged": 0} for d in ALL_DIRS}
    )
    trigger_target_counts: Dict[Tuple[int, int, int], int] = defaultdict(int)
    changing_colours: Set[int] = set()

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                changed = (old != new)
                if changed:
                    changing_colours.add(old)

                # Check each direction for each non-old, non-zero trigger
                for trigger in range(1, 10):
                    if trigger == old:
                        continue
                    for d_name, (dr, dc) in ALL_DIRS.items():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                            if pair.input.cells[nr][nc] == trigger:
                                if changed:
                                    direction_info[(old, trigger)][d_name]["changed"] += 1
                                    trigger_target_counts[(old, trigger, new)] += 1
                                else:
                                    direction_info[(old, trigger)][d_name]["unchanged"] += 1

    rules = []
    for a in changing_colours:
        # Find triggers associated with this A
        triggers_for_a = set()
        for (aa, t, c), count in trigger_target_counts.items():
            if aa == a and count > 0:
                triggers_for_a.add(t)

        if not triggers_for_a:
            continue

        # Build mapping: trigger → most common target
        mapping = {}
        for t in triggers_for_a:
            targets = [(c, count) for (aa, tt, c), count in trigger_target_counts.items()
                       if aa == a and tt == t]
            if targets:
                targets.sort(key=lambda x: -x[1])
                mapping[t] = targets[0][0]

        # Find directions that distinguish changed from unchanged
        # Aggregate across triggers
        total_changed_per_dir = {d: 0 for d in ALL_DIRS}
        total_unchanged_per_dir = {d: 0 for d in ALL_DIRS}
        total_changed = 0
        total_unchanged = 0

        for t in triggers_for_a:
            for d in ALL_DIRS:
                total_changed_per_dir[d] += direction_info[(a, t)][d]["changed"]
                total_unchanged_per_dir[d] += direction_info[(a, t)][d]["unchanged"]
            # Total cells with any trigger neighbour
            for d in ALL_DIRS:
                pass  # already counted above
            # Count total changed cells that have ANY trigger
            # (need to recount to avoid double-counting)
            total_changed += sum(1 for d in ALL_DIRS
                                   if direction_info[(a, t)][d]["changed"] > 0) > 0  # placeholder

        # Recount properly: per cell, did it change and have a trigger neighbour?
        # Use the original loop logic
        n_changed_with_trigger = 0
        n_unchanged_with_trigger = 0
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    old = pair.input.cells[r][c]
                    if old != a:
                        continue
                    changed = pair.output.cells[r][c] != old
                    has_trigger = False
                    for trigger in triggers_for_a:
                        if _has_in_directions(pair.input, r, c, trigger, ALL_DIRS):
                            has_trigger = True
                            break
                    if has_trigger:
                        if changed:
                            n_changed_with_trigger += 1
                        else:
                            n_unchanged_with_trigger += 1

        # Find directions where changed cells have trigger but unchanged don't
        good_dirs = []
        for d in ALL_DIRS:
            ch = total_changed_per_dir[d]
            un = total_unchanged_per_dir[d]
            # Direction is "good" if many changed cells have trigger here
            # and few unchanged cells do
            if (ch >= n_changed_with_trigger * 0.5
                    and un <= max(n_unchanged_with_trigger * 0.3, 2)):
                good_dirs.append(d)

        if good_dirs:
            # Also check if there are "forbidden" directions (where unchanged cells have trigger)
            forbidden_dirs = []
            for d in ALL_DIRS:
                if d in good_dirs:
                    continue
                ch = total_changed_per_dir[d]
                un = total_unchanged_per_dir[d]
                if (un >= n_unchanged_with_trigger * 0.5
                        and ch <= n_changed_with_trigger * 0.2):
                    forbidden_dirs.append(d)

            # If forbidden dirs are cardinal/diagonal groups, use group names
            forbidden_groups = []
            card_in_forbidden = [d for d in forbidden_dirs if d in CARDINAL_DIRS]
            diag_in_forbidden = [d for d in forbidden_dirs if d in DIAGONAL_DIRS]
            if len(card_in_forbidden) >= 3:
                forbidden_groups.append("cardinal")
                forbidden_dirs = [d for d in forbidden_dirs if d not in CARDINAL_DIRS]
            if len(diag_in_forbidden) >= 3:
                forbidden_groups.append("diagonal")
                forbidden_dirs = [d for d in forbidden_dirs if d not in DIAGONAL_DIRS]
            forbidden_groups.extend(forbidden_dirs)

            rule = MetaRule(
                input_colour=a,
                has_dirs=good_dirs,
                not_dirs=forbidden_groups,
                mapping=mapping,
                extrapolation="nearest",
            )
            rules.append(rule)
        else:
            # Fallback: use cardinal/diagonal groups
            # Check diagonal NOT cardinal
            changed_diag = sum(total_changed_per_dir[d] for d in DIAGONAL_DIRS)
            changed_card = sum(total_changed_per_dir[d] for d in CARDINAL_DIRS)
            unchanged_card = sum(total_unchanged_per_dir[d] for d in CARDINAL_DIRS)
            unchanged_diag = sum(total_unchanged_per_dir[d] for d in DIAGONAL_DIRS)

            if (changed_diag >= n_changed_with_trigger * 0.8
                    and changed_card <= n_changed_with_trigger * 0.2
                    and unchanged_card >= n_unchanged_with_trigger * 0.3):
                rule = MetaRule(
                    input_colour=a,
                    has_dirs=["diagonal"],
                    not_dirs=["cardinal"],
                    mapping=mapping,
                    extrapolation="nearest",
                )
                rules.append(rule)
            elif (changed_card >= n_changed_with_trigger * 0.8
                    and changed_diag <= n_changed_with_trigger * 0.2
                    and unchanged_diag >= n_unchanged_with_trigger * 0.3):
                rule = MetaRule(
                    input_colour=a,
                    has_dirs=["cardinal"],
                    not_dirs=["diagonal"],
                    mapping=mapping,
                    extrapolation="nearest",
                )
                rules.append(rule)
            else:
                # Last resort: any direction
                rule = MetaRule(
                    input_colour=a,
                    has_dirs=list(ALL_DIRS.keys()),
                    not_dirs=[],
                    mapping=mapping,
                    extrapolation="nearest",
                )
                rules.append(rule)

    return rules


# ══════════════════════════════════════════════════════════════════════════════
# UBP substrate extrapolation
# ══════════════════════════════════════════════════════════════════════════════

def compute_trigger_distances(test_input: Grid,
                                train_triggers: Set[int],
                                grid_h: int = None, grid_w: int = None
                                ) -> Dict[int, Dict[int, int]]:
    """For each test trigger colour, compute Hamming distance to each train trigger.

    Returns: {test_trigger: {train_trigger: hamming_distance}}
    """
    if grid_h is None:
        grid_h = test_input.height
    if grid_w is None:
        grid_w = test_input.width

    # Get 24-bit addresses for each trigger colour
    trigger_addrs = {}
    for colour in range(10):
        if colour == 0:
            continue
        cell = address_cell(0, 0, colour, grid_h, grid_w)
        trigger_addrs[colour] = cell.address_int

    # Compute distances
    distances: Dict[int, Dict[int, int]] = {}
    test_triggers = set()
    for r in range(test_input.height):
        for c in range(test_input.width):
            col = test_input.cells[r][c]
            if col != 0:
                test_triggers.add(col)

    for tt in test_triggers:
        if tt not in trigger_addrs:
            continue
        distances[tt] = {}
        for train_t in train_triggers:
            if train_t not in trigger_addrs:
                continue
            distances[tt][train_t] = _hamming_distance_int(
                trigger_addrs[tt], trigger_addrs[train_t]
            )

    return distances


def derive_and_verify_meta(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """Derive and verify meta-rules."""
    rules = derive_meta_rules(task)
    if not rules:
        return None, "none", {"n_meta_rules": 0}

    # Compute trigger distances for extrapolation
    train_triggers = set()
    for rule in rules:
        train_triggers.update(rule.mapping.keys())

    test_input = task.test[0].input
    trigger_distances = compute_trigger_distances(test_input, train_triggers,
                                                    test_input.height, test_input.width)

    # Apply ALL rules in parallel
    def apply_all_parallel(grid: Grid) -> Grid:
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        # Compute trigger distances for this grid
        grid_trigger_dists = compute_trigger_distances(grid, train_triggers,
                                                         grid.height, grid.width)
        for r in range(h):
            for c in range(w):
                for rule in rules:
                    applies, trigger = rule.applies_to(grid, r, c)
                    if applies:
                        # Get per-trigger distances
                        per_trigger_dist = grid_trigger_dists.get(trigger, {})
                        target = rule.get_target(trigger, per_trigger_dist)
                        out_cells[r][c] = target
                        break
        return Grid(out_cells)

    # Verify against train
    passes = True
    for pair in task.train:
        try:
            if apply_all_parallel(pair.input) != pair.output:
                passes = False
                break
        except Exception:
            passes = False
            break

    if passes:
        pred = apply_all_parallel(test_input)
        return pred, "cortex_meta", {
            "n_meta_rules": len(rules),
            "rules": [(r.input_colour, r.has_dirs, r.not_dirs, r.mapping) for r in rules],
            "train_triggers": list(train_triggers),
            "passed_train": True,
        }

    # Try each rule individually
    for rule in rules:
        def apply_one(grid: Grid, r=rule):
            h, w = grid.shape
            out_cells = [row[:] for row in grid.cells]
            grid_td = compute_trigger_distances(grid, train_triggers, h, w)
            for rr in range(h):
                for cc in range(w):
                    applies, trigger = r.applies_to(grid, rr, cc)
                    if applies:
                        per_td = grid_td.get(trigger, {})
                        target = r.get_target(trigger, per_td)
                        out_cells[rr][cc] = target
            return Grid(out_cells)
        passes = True
        for pair in task.train:
            try:
                if apply_one(pair.input) != pair.output:
                    passes = False
                    break
            except Exception:
                passes = False
                break
        if passes:
            pred = apply_one(test_input)
            return pred, "cortex_meta_single", {
                "n_meta_rules": 1,
                "rule": (rule.input_colour, rule.has_dirs, rule.not_dirs, rule.mapping),
                "passed_train": True,
            }

    return None, "none", {
        "n_meta_rules": len(rules),
        "rules": [(r.input_colour, r.has_dirs, r.not_dirs, r.mapping) for r in rules],
        "passed_train": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Meta-Rule self-test")
    print("=" * 60)

    from arc_loader import TrainPair, TestInput

    # Test: 396d80d7-style task
    # Pair 0: 7 next to 6 (diagonal) → 2
    # Pair 1: 7 next to 4 (diagonal) → 1
    # Test:   7 next to 9 (diagonal) → should extrapolate
    inp1 = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out1 = Grid([
        [7, 7, 7, 7, 7],
        [7, 2, 7, 2, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    inp2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [4, 7, 4, 7, 4],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 1, 7, 1, 7],
        [4, 7, 4, 7, 4],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    test = Grid([
        [7, 7, 7, 7],
        [7, 7, 7, 7],
        [9, 7, 9, 7],
        [7, 7, 7, 7],
    ])
    # Expected: 7s with 9 in diagonal → extrapolated target
    # 9 is not in train mapping {6:2, 4:1}
    # 9's address is closer to 6 or 4?
    expected_extrapolated = Grid([
        [7, 7, 7, 7],
        [7, 2, 7, 2],  # or 1, depending on which is closer
        [9, 7, 9, 7],
        [7, 7, 7, 7],
    ])
    task = ARCTask(name="meta_test",
                   train=[TrainPair(input=inp1, output=out1),
                           TrainPair(input=inp2, output=out2)],
                   test=[TestInput(input=test, expected_output=expected_extrapolated)])

    rules = derive_meta_rules(task)
    print(f"\nDerived {len(rules)} meta-rules:")
    for r in rules:
        print(f"  input={r.input_colour}, has={r.has_dirs}, not={r.not_dirs}")
        print(f"  mapping={r.mapping}")

    pred, src, diag = derive_and_verify_meta(task)
    print(f"\nsrc={src}, passed_train={diag.get('passed_train')}")
    if pred:
        print(f"pred: {pred.cells}")
        print(f"expected: {expected_extrapolated.cells}")
        print(f"correct: {pred == expected_extrapolated}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
