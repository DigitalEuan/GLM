"""
conditional_lobe.py — Conditional Reasoning in Lingo
=====================================================

The mind reasons about conditional patterns in the GLM's native language.

"CHARGE_SWAP only for CLUSTERs with NODE_CARDINALITY ≥ 4"

This is semantic intelligence: understanding that a transformation
isn't global — it applies only when a CONDITION is met.

The mind detects conditions by comparing what changed vs what didn't
across train pairs. If all changed objects share a property (size ≥ N)
and all preserved objects don't, the mind has found the condition.

This is harder than pure mathematics. It requires:
1. Object-level perception (what are the entities?)
2. Property extraction (what properties do they have?)
3. Differential analysis (what changed vs what didn't?)
4. Condition induction (what distinguishes changed from preserved?)
5. Lingo expression (how to state the condition in UBP-Lingo?)
6. Application (how to apply the condition to new inputs?)
"""

from __future__ import annotations
import os, sys, math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid


# ═══════════════════════════════════════════════════════════════════════════════
# Object Extraction — What Are the Entities?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GridObject:
    """A connected component — an entity in the substrate."""
    colour: int
    size: int
    cells: List[Tuple[int, int]]
    centroid: Tuple[float, float] = (0.0, 0.0)
    bounding_box: Tuple[int, int, int, int] = (0, 0, 0, 0)
    aspect_ratio: float = 1.0
    is_linear: bool = False
    is_rectangular: bool = False

    @property
    def lingo_description(self) -> str:
        """Describe this object in Lingo terms."""
        parts = [f"CLUSTER(colour={self.colour}, size={self.size})"]
        if self.is_linear:
            parts.append("LINEAR")
        if self.is_rectangular:
            parts.append("RECTANGULAR")
        return " ".join(parts)


def extract_objects(grid: Grid) -> List[GridObject]:
    """Extract connected components as GridObjects."""
    h, w = grid.height, grid.width
    visited = set()
    objects = []

    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            cells = []
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                if grid.cells[cr][cc] != colour:
                    continue
                visited.add((cr, cc))
                cells.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        queue.append((nr, nc))

            obj = GridObject(colour=colour, size=len(cells), cells=cells)
            if cells:
                rows = [r for r, c in cells]
                cols = [c for r, c in cells]
                obj.centroid = (sum(rows)/len(cells), sum(cols)/len(cells))
                obj.bounding_box = (min(rows), min(cols), max(rows), max(cols))
                bh = max(rows) - min(rows) + 1
                bw = max(cols) - min(cols) + 1
                obj.aspect_ratio = bw / max(bh, 1)
                obj.is_linear = (bh == 1 or bw == 1)
                obj.is_rectangular = (len(cells) == bh * bw)
            objects.append(obj)

    return objects


# ═══════════════════════════════════════════════════════════════════════════════
# Conditional Pattern — What's the Rule?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConditionalPattern:
    """A conditional transformation rule expressed in Lingo."""
    # The condition (when does the rule apply?)
    condition_type: str = ""  # "size_threshold", "colour_match", "always", "never"
    condition_param: Any = None  # e.g., 4 for size ≥ 4
    condition_colour: Optional[int] = None  # e.g., 2 for colour == 2

    # The action (what happens when the condition is met?)
    action_type: str = ""  # "charge_swap", "region_fill", "compaction_flow", etc.
    action_params: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"from_colour": 2, "to_colour": 6}

    # Confidence
    confidence: float = 0.0

    # Lingo expression
    lingo: str = ""

    # Human description
    human: str = ""

    @property
    def is_conditional(self) -> bool:
        return self.condition_type not in ("always", "never", "")

    def describe_in_lingo(self) -> str:
        """Express this pattern in UBP-Lingo."""
        if not self.lingo:
            # Build the Lingo expression
            action_lingo = _action_to_lingo(self.action_type, self.action_params)
            if self.condition_type == "always":
                self.lingo = action_lingo
            elif self.condition_type == "size_threshold":
                self.lingo = f"{action_lingo} IF NODE_CARDINALITY ≥ {self.condition_param}"
                if self.condition_colour is not None:
                    self.lingo += f" AND CHARGE_VALUE = {self.condition_colour}"
            elif self.condition_type == "colour_match":
                self.lingo = f"{action_lingo} IF CHARGE_VALUE = {self.condition_colour}"
            else:
                self.lingo = action_lingo
        return self.lingo

    def describe_in_human(self) -> str:
        """Express this pattern in human language."""
        if not self.human:
            action_human = _action_to_human(self.action_type, self.action_params)
            if self.condition_type == "always":
                self.human = action_human
            elif self.condition_type == "size_threshold":
                self.human = f"{action_human} only for components with size ≥ {self.condition_param}"
                if self.condition_colour is not None:
                    self.human += f" and colour {self.condition_colour}"
            elif self.condition_type == "colour_match":
                self.human = f"{action_human} only for cells with colour {self.condition_colour}"
            else:
                self.human = action_human
        return self.human


def _action_to_lingo(action_type: str, params: Dict) -> str:
    """Convert action type to Lingo expression."""
    if action_type == "charge_swap":
        src = params.get("from_colour", "?")
        dst = params.get("to_colour", "?")
        return f"CHARGE_SWAP({src}→{dst})"
    elif action_type == "region_fill":
        fill = params.get("fill_colour", "?")
        return f"REGION_FILL(colour={fill})"
    elif action_type == "compaction_flow":
        return "COMPACTION_FLOW"
    elif action_type == "cluster_union":
        return "CLUSTER_UNION"
    elif action_type == "cluster_fission":
        return "CLUSTER_FISSION"
    return action_type.upper()


def _action_to_human(action_type: str, params: Dict) -> str:
    """Convert action type to human description."""
    if action_type == "charge_swap":
        src = params.get("from_colour", "?")
        dst = params.get("to_colour", "?")
        return f"change colour {src} to {dst}"
    elif action_type == "region_fill":
        fill = params.get("fill_colour", "?")
        return f"fill with colour {fill}"
    elif action_type == "compaction_flow":
        return "compact to bottom (gravity)"
    return action_type


# ═══════════════════════════════════════════════════════════════════════════════
# Condition Induction — Find the Rule
# ═══════════════════════════════════════════════════════════════════════════════

def induce_conditional_pattern(task: ARCTask) -> Optional[ConditionalPattern]:
    """
    Induce the conditional transformation pattern from train pairs.
    
    This is the core of conditional reasoning: the mind compares what
    changed vs what didn't across all train pairs and finds the condition
    that distinguishes them.
    """
    # Collect objects and their fates across all train pairs
    all_fates = []  # List of (object_properties, changed, new_colour)

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue

        inp_objects = extract_objects(pair.input)
        out_objects = extract_objects(pair.output)

        # Match input objects to output objects by overlap
        for inp_obj in inp_objects:
            # Find the output cells that overlap with this input object
            out_colours = []
            for r, c in inp_obj.cells:
                out_colours.append(pair.output.cells[r][c])

            # Did this object change?
            unique_out = set(out_colours)
            if len(unique_out) == 1:
                out_colour = next(iter(unique_out))
                changed = (out_colour != inp_obj.colour)
            else:
                # Mixed — partial change
                most_common = Counter(out_colours).most_common(1)[0]
                out_colour = most_common[0]
                changed = (out_colour != inp_obj.colour)

            all_fates.append({
                "colour": inp_obj.colour,
                "size": inp_obj.size,
                "is_linear": inp_obj.is_linear,
                "is_rectangular": inp_obj.is_rectangular,
                "changed": changed,
                "new_colour": out_colour if changed else inp_obj.colour,
            })

    if not all_fates:
        return None

    # Separate changed vs preserved
    changed = [f for f in all_fates if f["changed"]]
    preserved = [f for f in all_fates if not f["changed"]]

    if not changed:
        return None  # Nothing changes

    if not preserved:
        # Everything changes — unconditional
        return _induce_unconditional(changed)

    # Find the condition that distinguishes changed from preserved
    return _find_condition(changed, preserved)


def _induce_unconditional(changed: List[Dict]) -> Optional[ConditionalPattern]:
    """All objects change — find the unconditional rule."""
    # Check: is it a uniform colour swap?
    colour_changes = defaultdict(set)
    for f in changed:
        colour_changes[f["colour"]].add(f["new_colour"])

    # If each input colour maps to exactly one output colour, it's a colour map
    colour_map = {}
    for src, dsts in colour_changes.items():
        if len(dsts) == 1:
            colour_map[src] = next(iter(dsts))
        else:
            return None  # Inconsistent

    if len(colour_map) == 1:
        src, dst = list(colour_map.items())[0]
        return ConditionalPattern(
            condition_type="always",
            action_type="charge_swap",
            action_params={"from_colour": src, "to_colour": dst},
            confidence=0.9,
        )

    if len(colour_map) == 2:
        items = list(colour_map.items())
        if items[0][1] == items[1][0] and items[1][1] == items[0][0]:
            return ConditionalPattern(
                condition_type="always",
                action_type="charge_swap",
                action_params={"from_colour": items[0][0], "to_colour": items[0][1]},
                confidence=0.9,
            )

    return None


def _find_condition(changed: List[Dict], preserved: List[Dict]) -> Optional[ConditionalPattern]:
    """Find the condition that distinguishes changed from preserved objects."""
    
    # Test 1: Size threshold
    size_condition = _test_size_threshold(changed, preserved)
    if size_condition:
        return size_condition

    # Test 2: Colour match
    colour_condition = _test_colour_condition(changed, preserved)
    if colour_condition:
        return colour_condition

    # Test 3: Shape condition
    shape_condition = _test_shape_condition(changed, preserved)
    if shape_condition:
        return shape_condition

    return None


def _test_size_threshold(changed: List[Dict], preserved: List[Dict]) -> Optional[ConditionalPattern]:
    """Test if the condition is a size threshold."""
    if not changed or not preserved:
        return None

    changed_sizes = set(f["size"] for f in changed)
    preserved_sizes = set(f["size"] for f in preserved)

    # Find: all changed sizes ≥ threshold AND all preserved sizes < threshold
    min_changed = min(changed_sizes)
    max_preserved = max(preserved_sizes)

    if max_preserved < min_changed:
        threshold = min_changed

        # Check: is the condition colour-specific?
        changed_colours = set(f["colour"] for f in changed)
        preserved_colours = set(f["colour"] for f in preserved)

        # If changed and preserved have the same colour, the condition is size-only
        shared_colours = changed_colours & preserved_colours
        condition_colour = None
        if shared_colours:
            # Size-only condition (colour doesn't matter)
            condition_colour = None
        elif len(changed_colours) == 1:
            # Colour-specific condition
            condition_colour = next(iter(changed_colours))

        # Find the action
        action, params = _find_action(changed)
        if not action:
            return None

        pattern = ConditionalPattern(
            condition_type="size_threshold",
            condition_param=threshold,
            condition_colour=condition_colour,
            action_type=action,
            action_params=params,
            confidence=0.9,
        )
        pattern.describe_in_lingo()
        pattern.describe_in_human()
        return pattern

    return None


def _test_colour_condition(changed: List[Dict], preserved: List[Dict]) -> Optional[ConditionalPattern]:
    """Test if the condition is colour-based."""
    changed_colours = set(f["colour"] for f in changed)
    preserved_colours = set(f["colour"] for f in preserved)

    # If changed and preserved have NO shared colours, the condition is colour-based
    shared = changed_colours & preserved_colours
    if not shared and len(changed_colours) == 1:
        colour = next(iter(changed_colours))
        action, params = _find_action(changed)
        if action:
            pattern = ConditionalPattern(
                condition_type="colour_match",
                condition_colour=colour,
                action_type=action,
                action_params=params,
                confidence=0.8,
            )
            pattern.describe_in_lingo()
            pattern.describe_in_human()
            return pattern

    return None


def _test_shape_condition(changed: List[Dict], preserved: List[Dict]) -> Optional[ConditionalPattern]:
    """Test if the condition is shape-based (linear vs non-linear)."""
    changed_linear = set(f["is_linear"] for f in changed)
    preserved_linear = set(f["is_linear"] for f in preserved)

    # If all changed are linear and all preserved are non-linear (or vice versa)
    if changed_linear == {True} and preserved_linear == {False}:
        action, params = _find_action(changed)
        if action:
            return ConditionalPattern(
                condition_type="shape_match",
                condition_param="linear",
                action_type=action,
                action_params=params,
                confidence=0.7,
            )

    if changed_linear == {False} and preserved_linear == {True}:
        action, params = _find_action(changed)
        if action:
            return ConditionalPattern(
                condition_type="shape_match",
                condition_param="non_linear",
                action_type=action,
                action_params=params,
                confidence=0.7,
            )

    return None


def _find_action(changed: List[Dict]) -> Tuple[str, Dict]:
    """Find the action applied to changed objects."""
    # Check: colour swap
    colour_changes = defaultdict(set)
    for f in changed:
        colour_changes[f["colour"]].add(f["new_colour"])

    for src, dsts in colour_changes.items():
        if len(dsts) == 1:
            dst = next(iter(dsts))
            if src != dst:
                return "charge_swap", {"from_colour": src, "to_colour": dst}

    return "", {}


# ═══════════════════════════════════════════════════════════════════════════════
# Conditional Application — Apply the Rule
# ═══════════════════════════════════════════════════════════════════════════════

def apply_conditional_pattern(grid: Grid, pattern: ConditionalPattern) -> Optional[Grid]:
    """Apply a conditional pattern to a grid."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False

    if pattern.condition_type == "always":
        # Apply to all cells
        if pattern.action_type == "charge_swap":
            src = pattern.action_params["from_colour"]
            dst = pattern.action_params["to_colour"]
            for r in range(h):
                for c in range(w):
                    if cells[r][c] == src:
                        cells[r][c] = dst
                        changed = True

    elif pattern.condition_type == "size_threshold":
        # Apply only to objects with size ≥ threshold
        objects = extract_objects(grid)
        for obj in objects:
            if obj.size < pattern.condition_param:
                continue
            if pattern.condition_colour is not None and obj.colour != pattern.condition_colour:
                continue
            if pattern.action_type == "charge_swap":
                src = pattern.action_params["from_colour"]
                dst = pattern.action_params["to_colour"]
                if obj.colour == src:
                    for r, c in obj.cells:
                        cells[r][c] = dst
                        changed = True

    elif pattern.condition_type == "colour_match":
        # Apply only to objects with matching colour
        if pattern.action_type == "charge_swap":
            src = pattern.action_params["from_colour"]
            dst = pattern.action_params["to_colour"]
            for r in range(h):
                for c in range(w):
                    if cells[r][c] == src:
                        cells[r][c] = dst
                        changed = True

    elif pattern.condition_type == "shape_match":
        # Apply only to objects with matching shape
        objects = extract_objects(grid)
        for obj in objects:
            is_match = (pattern.condition_param == "linear" and obj.is_linear) or \
                       (pattern.condition_param == "non_linear" and not obj.is_linear)
            if not is_match:
                continue
            if pattern.action_type == "charge_swap":
                src = pattern.action_params["from_colour"]
                dst = pattern.action_params["to_colour"]
                if obj.colour == src:
                    for r, c in obj.cells:
                        cells[r][c] = dst
                        changed = True

    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify_conditional_pattern(task: ARCTask, pattern: ConditionalPattern) -> bool:
    """Verify a conditional pattern on train pairs."""
    checked = 0
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        result = apply_conditional_pattern(pair.input, pattern)
        if result is None or result.cells != pair.output.cells:
            return False
        checked += 1
    return checked > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Integration with Substrate Mind
# ═══════════════════════════════════════════════════════════════════════════════

def conditional_solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Solve a task using conditional Lingo reasoning.
    
    1. Induce the conditional pattern from train pairs
    2. Express it in Lingo
    3. Apply it to the test input
    4. Verify on train pairs
    """
    pattern = induce_conditional_pattern(task)
    if pattern is None:
        return None

    test = task.test[0].input
    result = apply_conditional_pattern(test, pattern)
    if result is None:
        return None

    if verify_conditional_pattern(task, pattern):
        return result, f"conditional_{pattern.condition_type}"

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Report — The Mind's Conditional Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

def conditional_report(task: ARCTask) -> str:
    """Generate a report of the mind's conditional reasoning."""
    pattern = induce_conditional_pattern(task)

    lines = [f"═══ Conditional Reasoning: {task.name} ═══"]

    if pattern is None:
        lines.append("  No conditional pattern detected.")
        return "\n".join(lines)

    lines.append(f"")
    lines.append(f"Condition: {pattern.condition_type}")
    if pattern.condition_param is not None:
        lines.append(f"  Parameter: {pattern.condition_param}")
    if pattern.condition_colour is not None:
        lines.append(f"  Colour: {pattern.condition_colour}")
    lines.append(f"Action: {pattern.action_type} {pattern.action_params}")
    lines.append(f"Confidence: {pattern.confidence:.2f}")
    lines.append(f"")
    lines.append(f"Lingo: {pattern.describe_in_lingo()}")
    lines.append(f"Human: {pattern.describe_in_human()}")

    # Verify
    verified = verify_conditional_pattern(task, pattern)
    lines.append(f"")
    lines.append(f"Verified on train pairs: {'✓ PASS' if verified else '✗ FAIL'}")

    return "\n".join(lines)
