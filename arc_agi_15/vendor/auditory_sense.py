"""
auditory_sense.py — periodicity / rhythm detection for grids (v2)
==================================================================

v2: GENERATIVE audition.  The ear doesn't just hear — it predicts.

When the ear detects a tile/row/col period in train, and a matching
or extendable period in the test input, it can GENERATE a candidate
prediction by extending the pattern.

Generative modes:
  - TILE_EXTEND: if train shows a 2x2 tile becoming a 4x4 tile of the
                 same pattern, apply the same extension to the test tile.
  - PERIOD_CONTINUE: if train has row period P, predict the next P rows.
  - RHYTHM_MAP: if train rhythm is "tile" and test rhythm is "row",
                transform the test into a tile pattern.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict, Counter
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask


# ══════════════════════════════════════════════════════════════════════════════
# Period detection (from v1)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Period:
    kind: str
    length: int
    confidence: float
    key: Any = None


def detect_row_period(grid: Grid) -> Optional[Period]:
    h, w = grid.shape
    if h < 2: return None
    for P in range(1, h // 2 + 1):
        matches = sum(1 for r in range(h - P) for c in range(w)
                       if grid.cells[r][c] == grid.cells[r + P][c])
        total = (h - P) * w
        conf = matches / total if total > 0 else 0
        if conf >= 0.9:
            return Period(kind="row", length=P, confidence=conf,
                          key=[grid.cells[r][:] for r in range(P)])
    return None


def detect_col_period(grid: Grid) -> Optional[Period]:
    h, w = grid.shape
    if w < 2: return None
    for P in range(1, w // 2 + 1):
        matches = sum(1 for r in range(h) for c in range(w - P)
                       if grid.cells[r][c] == grid.cells[r][c + P])
        total = h * (w - P)
        conf = matches / total if total > 0 else 0
        if conf >= 0.9:
            key = [[grid.cells[r][c] for r in range(h)] for c in range(P)]
            return Period(kind="col", length=P, confidence=conf, key=key)
    return None


def detect_tile_period(grid: Grid) -> Optional[Period]:
    h, w = grid.shape
    best: Optional[Period] = None
    for Ph in range(1, h // 2 + 1):
        for Pw in range(1, w // 2 + 1):
            if Ph == 1 and Pw == 1:
                if len(set(grid.cells[r][c] for r in range(h) for c in range(w))) == 1:
                    pass
                else:
                    continue
            matches = sum(1 for r in range(h) for c in range(w)
                          if grid.cells[r][c] == grid.cells[r % Ph][c % Pw])
            total = h * w
            conf = matches / total if total > 0 else 0
            if conf >= 0.95:
                tile = [[grid.cells[r][c] for c in range(Pw)] for r in range(Ph)]
                p = Period(kind="tile", length=Ph * Pw, confidence=conf,
                           key={"tile": tile, "ph": Ph, "pw": Pw})
                if best is None or Ph * Pw < best.length:
                    best = p
    return best


def detect_block_period(grid: Grid) -> Optional[Period]:
    h, w = grid.shape
    for B in [2, 3, 4]:
        if h % B != 0 or w % B != 0: continue
        nh, nw = h // B, w // B
        if nh < 2 or nw < 2: continue
        first = tuple(tuple(grid.cells[r][c] for c in range(B)) for r in range(B))
        matches = 0
        total = 0
        for br in range(nh):
            for bc in range(nw):
                blk = tuple(tuple(grid.cells[br*B + r][bc*B + c]
                                   for c in range(B)) for r in range(B))
                if blk == first:
                    matches += 1
                total += 1
        conf = matches / total if total > 0 else 0
        if conf >= 0.8:
            return Period(kind="block", length=B, confidence=conf,
                          key={"block_size": B, "first_block": first})
    return None


@dataclass
class RhythmSignature:
    row_period: Optional[Period] = None
    col_period: Optional[Period] = None
    tile_period: Optional[Period] = None
    block_period: Optional[Period] = None

    def has_rhythm(self) -> bool:
        return any([self.row_period, self.col_period,
                    self.tile_period, self.block_period])

    def dominant(self) -> Optional[str]:
        all_periods = [p for p in [self.row_period, self.col_period,
                                    self.tile_period, self.block_period] if p]
        if not all_periods: return None
        priority = {"tile": 4, "block": 3, "row": 2, "col": 1}
        return max(all_periods, key=lambda p: priority.get(p.kind, 0)).kind

    def as_dict(self) -> Dict[str, Any]:
        return {
            "row": {"length": self.row_period.length, "confidence": self.row_period.confidence}
                   if self.row_period else None,
            "col": {"length": self.col_period.length, "confidence": self.col_period.confidence}
                   if self.col_period else None,
            "tile": {"length": self.tile_period.length, "confidence": self.tile_period.confidence}
                    if self.tile_period else None,
            "block": {"length": self.block_period.length, "confidence": self.block_period.confidence}
                     if self.block_period else None,
            "dominant": self.dominant(),
            "has_rhythm": self.has_rhythm(),
        }


def hear_grid(grid: Grid) -> RhythmSignature:
    return RhythmSignature(
        row_period=detect_row_period(grid),
        col_period=detect_col_period(grid),
        tile_period=detect_tile_period(grid),
        block_period=detect_block_period(grid),
    )


def rhythm_match(sig_a: RhythmSignature, sig_b: RhythmSignature) -> float:
    if not sig_a.has_rhythm() and not sig_b.has_rhythm():
        return 0.5
    if sig_a.has_rhythm() != sig_b.has_rhythm():
        return 0.0
    if sig_a.dominant() == sig_b.dominant():
        return 1.0
    return 0.2


# ══════════════════════════════════════════════════════════════════════════════
# v2: GENERATIVE AUDITION
# ══════════════════════════════════════════════════════════════════════════════

def _extract_tile(grid: Grid, ph: int, pw: int) -> List[List[int]]:
    """Extract the top-left ph×pw tile from a grid."""
    return [[grid.cells[r % grid.height][c % grid.width]
             for c in range(pw)] for r in range(ph)]


def _tile_to_grid(tile: List[List[int]], target_h: int, target_w: int) -> Grid:
    """Tile a small pattern to fill a target_h × target_w grid."""
    ph, pw = len(tile), len(tile[0]) if tile else 1
    out = [[tile[r % ph][c % pw] for c in range(target_w)] for r in range(target_h)]
    return Grid(out)


def predict_via_tile_extend(task: ARCTask) -> Optional[Grid]:
    """If train shows a tile becoming a tiled grid of the same pattern,
    apply the same to the test input.

    Looks for: train[0].input is a small tile, train[0].output is that
    tile repeated to fill a larger grid.  If so, the test input is
    likely also a small tile that should be repeated.
    """
    test_input = task.test[0].input

    for pair in task.train:
        in_h, in_w = pair.input.shape
        out_h, out_w = pair.output.shape

        # Case 1: input is small, output is a tiled version
        if (out_h >= in_h and out_w >= in_w and
                out_h % in_h == 0 and out_w % in_w == 0 and
                (out_h > in_h or out_w > in_w)):
            # Check if output is the input tiled
            matches = 0
            total = out_h * out_w
            for r in range(out_h):
                for c in range(out_w):
                    if pair.output.cells[r][c] == pair.input.cells[r % in_h][c % in_w]:
                        matches += 1
            if matches / total >= 0.95:
                # Confirmed: output is input tiled.
                # Apply same to test input — but we need to know the target size.
                # Use the output size of the largest train pair.
                target_h, target_w = out_h, out_w
                # If test input is already the target size, just tile it
                if test_input.shape == (target_h, target_w):
                    return _tile_to_grid(
                        [row[:] for row in test_input.cells[:in_h]],
                        target_h, target_w
                    ) if test_input.shape[0] >= in_h and test_input.shape[1] >= in_w else None
                # If test input is small (a tile), tile it to target size
                if test_input.shape[0] <= in_h and test_input.shape[1] <= in_w:
                    return _tile_to_grid(
                        [row[:] for row in test_input.cells],
                        target_h, target_w
                    )
    return None


def predict_via_period_continue(task: ARCTask) -> Optional[Grid]:
    """If the test input has a row/col period, predict by continuing the period.

    For example, if test input is 4 rows with period 2, predict a 6-row
    output where rows 5-6 continue the period.
    """
    test_input = task.test[0].input
    test_rhythm = hear_grid(test_input)

    # Look at train to see if output extends input rows/cols
    extends_rows = False
    extends_cols = False
    target_h, target_w = test_input.shape
    for pair in task.train:
        if pair.output.shape[0] > pair.input.shape[0]:
            extends_rows = True
            target_h = max(target_h, pair.output.shape[0])
        if pair.output.shape[1] > pair.input.shape[1]:
            extends_cols = True
            target_w = max(target_w, pair.output.shape[1])

    if not (extends_rows or extends_cols):
        return None

    # If test has a row period, extend by repeating
    if extends_rows and test_rhythm.row_period:
        P = test_rhythm.row_period.length
        h, w = test_input.shape
        if target_h > h and target_h % P == 0:
            out_cells = []
            for r in range(target_h):
                src_r = r % P
                if src_r < h:
                    out_cells.append(test_input.cells[src_r][:])
                else:
                    # Use the period key
                    out_cells.append(test_rhythm.row_period.key[src_r][:])
            # Make sure width matches target
            for i, row in enumerate(out_cells):
                if len(row) < target_w:
                    # Extend by col period if available
                    if test_rhythm.col_period:
                        Pw = test_rhythm.col_period.length
                        row = [row[c % Pw] if c < len(row) else row[c % len(row)]
                               for c in range(target_w)]
                    else:
                        row = row + [0] * (target_w - len(row))
                    out_cells[i] = row
            return Grid(out_cells[:target_h])

    return None


def predict_via_rhythm_transform(task: ARCTask) -> Optional[Grid]:
    """If train transforms one rhythm into another, apply the same transform to test.

    Example: train shows a "tile" pattern becoming a "row" pattern.
    If test has a "tile" pattern, predict the corresponding "row" pattern.
    """
    test_input = task.test[0].input
    test_rhythm = hear_grid(test_input)

    for pair in task.train:
        in_rhythm = hear_grid(pair.input)
        out_rhythm = hear_grid(pair.output)

        # If train input rhythm matches test input rhythm
        if (in_rhythm.dominant() and test_rhythm.dominant() and
                in_rhythm.dominant() == test_rhythm.dominant()):

            # If train output has a different rhythm, apply the transform
            if (out_rhythm.dominant() and
                    out_rhythm.dominant() != in_rhythm.dominant()):

                # Case: tile → row (extract first row of tile and repeat)
                if (in_rhythm.tile_period and out_rhythm.row_period):
                    tile_info = in_rhythm.tile_period.key
                    test_tile_info = test_rhythm.tile_period.key
                    if test_tile_info:
                        # Apply the same transform: take the test tile and
                        # produce the row-period output
                        test_tile = test_tile_info["tile"]
                        # The transform might be "flatten the tile to a row"
                        # Check what train did
                        train_tile = tile_info["tile"]
                        train_ph, train_pw = tile_info["ph"], tile_info["pw"]
                        # If train output is the first row of the tile repeated
                        if pair.output.shape[0] > 0:
                            first_row = pair.output.cells[0][:]
                            # Check if first row equals first row of tile
                            if first_row == train_tile[0]:
                                # Apply same to test
                                test_first_row = test_tile[0]
                                target_h = pair.output.shape[0]
                                target_w = pair.output.shape[1]
                                if test_input.shape == (target_h, target_w) or True:
                                    out_cells = [test_first_row[:] for _ in range(target_h)]
                                    return Grid(out_cells)

    return None


def predict_generative(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Try all generative auditory predictions.

    Returns (prediction, source, diagnostics) or (None, "none", {}).
    """
    # Try tile extend
    pred = predict_via_tile_extend(task)
    if pred is not None:
        # Verify against train
        if _passes_train_period(task, pred):
            return pred, "auditory_tile_extend", {"rhythm": "tile_extend"}

    # Try period continue
    pred = predict_via_period_continue(task)
    if pred is not None:
        if _passes_train_period(task, pred):
            return pred, "auditory_period_continue", {"rhythm": "period_continue"}

    # Try rhythm transform
    pred = predict_via_rhythm_transform(task)
    if pred is not None:
        if _passes_train_period(task, pred):
            return pred, "auditory_rhythm_transform", {"rhythm": "rhythm_transform"}

    return None, "none", {}


def _passes_train_period(task: ARCTask, pred_fn_or_grid) -> bool:
    """Verify a prediction against train pairs.

    For auditory predictions, we can't easily verify because the prediction
    is for the test input.  But we can check that the predicted grid
    has the same rhythm structure as the train outputs.
    """
    # If it's a Grid (test prediction), check it has SOME rhythm
    if isinstance(pred_fn_or_grid, Grid):
        sig = hear_grid(pred_fn_or_grid)
        # At least one train output should have a rhythm
        for pair in task.train:
            out_sig = hear_grid(pair.output)
            if out_sig.has_rhythm() and sig.has_rhythm():
                return True
        # Or if no train output has rhythm, accept any non-empty pred
        if not any(hear_grid(p.output).has_rhythm() for p in task.train):
            return True
        return False
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Auditory Sense v2 self-test")
    print("=" * 60)

    from arc_loader import TrainPair, TestInput

    # Test 1: tile extend
    print("\n[Test 1] Tile extend")
    inp = Grid([[1, 2], [3, 4]])
    out = Grid([[1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]])
    test = Grid([[5, 6], [7, 8]])
    task = ARCTask(name="tile_ext",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=test, expected_output=Grid(
                       [[5, 6, 5, 6], [7, 8, 7, 8], [5, 6, 5, 6], [7, 8, 7, 8]]))])
    pred, src, _ = predict_generative(task)
    print(f"  src={src}, pred={'OK' if pred == task.test[0].expected_output else 'X'}")
    if pred:
        print(f"  pred: {pred.cells}")

    # Test 2: row period continue
    print("\n[Test 2] Row period continue")
    inp2 = Grid([[1, 2, 3], [4, 5, 6], [1, 2, 3], [4, 5, 6]])
    out2 = Grid([[1, 2, 3], [4, 5, 6], [1, 2, 3], [4, 5, 6], [1, 2, 3], [4, 5, 6]])
    test2 = Grid([[7, 8, 9], [1, 2, 3], [7, 8, 9], [1, 2, 3]])
    task2 = ARCTask(name="row_per",
                    train=[TrainPair(input=inp2, output=out2)],
                    test=[TestInput(input=test2, expected_output=Grid(
                        [[7, 8, 9], [1, 2, 3], [7, 8, 9], [1, 2, 3], [7, 8, 9], [1, 2, 3]]))])
    pred2, src2, _ = predict_generative(task2)
    print(f"  src={src2}, pred={'OK' if pred2 == task2.test[0].expected_output else 'X'}")
    if pred2:
        print(f"  pred: {pred2.cells}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
