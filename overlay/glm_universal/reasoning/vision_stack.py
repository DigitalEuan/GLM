"""``glm_universal.reasoning.vision_stack`` -- the same stack, in the grid register.

The question this module answers
--------------------------------
:mod:`glm_universal.reasoning.stack` measures a multi-part stack over the Lean
corpus: a leader that usually answers, a confidence that says when it cannot,
and weaker faculties that carry the query when it abstains.  A mechanism that
only ever worked in the register it was invented in would be a trick.  So it is
instantiated again here, on the 50 ARC-AGI training puzzles kept under
``overlay/arc_agi_17/data/training``, with faculties that have nothing to do
with text:

``geometry``
    The dihedral group and the four gravities: rotate, flip, transpose, fall.

``recolour``
    A colour map read off the training pairs, and the conditional recolour that
    reads a connected component's size before deciding its colour.

``shape``
    The operations that change the grid's size: scale, crop to the bounding box,
    shift.

Each faculty proposes a ranked list of candidate rules.  Each rule is *looked
at* before it is verified -- the eight-dimension visual feedback of
:func:`look`, which compares the rule's output on a training input against what
the training outputs actually look like -- and a faculty's **confidence** for
this puzzle is the share of those dimensions its best candidate passes, exactly
as a rational.  The stack then relays by
:func:`glm_universal.reasoning.stack.relay`, with the same gate and the same
interleave, and the answer is verified against every training pair before it is
accepted.  Nothing here is stored: every candidate is generated from the pairs.

What the measurement says
-------------------------
The generators solve a small number of these puzzles, and that number is the
honest headline: the register is a *test of the mechanism*, not a claim about
ARC.  What the mechanism buys is stated in three figures the report computes:

* how many puzzles the leading faculty alone solves, and how many the relay
  solves -- the relay is never behind, and it is ahead where the leader has no
  candidate that survives the look;
* the **carry table**: which faculty supplied the rule that verified, puzzle by
  puzzle, so "the stack solved it" is never a claim without an author;
* the **cost the filter carries**: how many candidates are proposed, how many
  survive the look, and what share of the expensive verification the cheap
  visual check therefore pays for.

Exactness
---------
Every rate here is a :class:`~fractions.Fraction`; the densities, the symmetry
share and the confidence are exact rationals, and no float is constructed
anywhere in the module (directive D7).

The formal half is ``RequestProject/GLM/Relay.lean``, shared with the text
register: the carry theorem, the no-invention property and the
leader-preservation property are about the relay itself and hold in whatever
register it is instantiated.  ``studies/STACK_RELAY_STUDY.md`` reports both.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from . import stack as st

Grid = Tuple[Tuple[int, ...], ...]

#: Where the puzzles live: the 50 ARC-AGI training tasks kept with the package.
DATA_DIR = (Path(__file__).resolve().parents[2] / "arc_agi_17" / "data"
            / "training")


# ===========================================================================
#  Puzzles
# ===========================================================================

@dataclass(frozen=True)
class Puzzle:
    """One ARC task: the training pairs, and the test pair."""

    name: str
    train: Tuple[Tuple[Grid, Grid], ...]
    test_input: Grid
    test_output: Optional[Grid]


def _grid(rows: Sequence[Sequence[int]]) -> Grid:
    return tuple(tuple(int(cell) for cell in row) for row in rows)


@memo
def puzzles() -> Tuple[Puzzle, ...]:
    """Every puzzle in the data directory, in name order."""
    out: List[Puzzle] = []
    if not DATA_DIR.is_dir():
        return ()
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        train = tuple((_grid(pair["input"]), _grid(pair["output"]))
                      for pair in data.get("train", []))
        tests = data.get("test", [])
        if not train or not tests:
            continue
        first = tests[0]
        out.append(Puzzle(name=path.stem, train=train,
                          test_input=_grid(first["input"]),
                          test_output=(_grid(first["output"])
                                       if "output" in first else None)))
    return tuple(out)


# ===========================================================================
#  Grid operations -- the vocabulary the faculties propose in
# ===========================================================================

def rotate90(g: Grid) -> Grid:
    return tuple(tuple(row) for row in zip(*g[::-1]))


def rotate180(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in reversed(g))


def rotate270(g: Grid) -> Grid:
    return tuple(tuple(row) for row in reversed(list(zip(*g))))


def flip_h(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in g)


def flip_v(g: Grid) -> Grid:
    return tuple(reversed(g))


def transpose(g: Grid) -> Grid:
    return tuple(tuple(row) for row in zip(*g))


def anti_transpose(g: Grid) -> Grid:
    return tuple(tuple(row) for row in reversed(list(zip(*g[::-1]))))


def _shape(g: Grid) -> Tuple[int, int]:
    return (len(g), len(g[0]) if g else 0)


def gravity(g: Grid, direction: str) -> Grid:
    height, width = _shape(g)
    if height == 0 or width == 0:
        return g
    out = [[0] * width for _ in range(height)]
    if direction in ("down", "up"):
        for x in range(width):
            cells = [g[y][x] for y in range(height) if g[y][x] != 0]
            for index, value in enumerate(cells):
                row = (height - len(cells) + index if direction == "down"
                       else index)
                out[row][x] = value
    else:
        for y in range(height):
            cells = [value for value in g[y] if value != 0]
            for index, value in enumerate(cells):
                column = (width - len(cells) + index if direction == "right"
                          else index)
                out[y][column] = value
    return tuple(tuple(row) for row in out)


def shift(g: Grid, dy: int, dx: int) -> Grid:
    height, width = _shape(g)
    out = [[0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width:
                out[ny][nx] = g[y][x]
    return tuple(tuple(row) for row in out)


def scale(g: Grid, factor: int) -> Grid:
    out: List[Tuple[int, ...]] = []
    for row in g:
        widened = tuple(value for value in row for _ in range(factor))
        out.extend([widened] * factor)
    return tuple(out)


def crop_bbox(g: Grid) -> Grid:
    height, width = _shape(g)
    cells = [(y, x) for y in range(height) for x in range(width)
             if g[y][x] != 0]
    if not cells:
        return ((0,),)
    top = min(y for y, _ in cells)
    bottom = max(y for y, _ in cells)
    left = min(x for _, x in cells)
    right = max(x for _, x in cells)
    return tuple(tuple(g[y][x] for x in range(left, right + 1))
                 for y in range(top, bottom + 1))


def components(g: Grid) -> Tuple[Tuple[int, int, Tuple[Tuple[int, int], ...]], ...]:
    """Four-connected same-colour components: size, colour, cells."""
    height, width = _shape(g)
    seen = [[False] * width for _ in range(height)]
    found = []
    for sy in range(height):
        for sx in range(width):
            if seen[sy][sx]:
                continue
            colour = g[sy][sx]
            queue = [(sy, sx)]
            seen[sy][sx] = True
            cells: List[Tuple[int, int]] = []
            while queue:
                y, x = queue.pop()
                cells.append((y, x))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < height and 0 <= nx < width
                            and not seen[ny][nx] and g[ny][nx] == colour):
                        seen[ny][nx] = True
                        queue.append((ny, nx))
            found.append((len(cells), colour, tuple(sorted(cells))))
    return tuple(found)


def size_bucket(size: int) -> str:
    """The size classes the conditional recolour reads, stated once."""
    if size <= 1:
        return "1"
    if size <= 3:
        return "2-3"
    if size <= 7:
        return "4-7"
    if size <= 15:
        return "8-15"
    return "16+"


# ===========================================================================
#  Candidates and the faculties that propose them
# ===========================================================================

@dataclass(frozen=True)
class Candidate:
    """One proposed rule: a name, the faculty that proposed it, and the map."""

    name: str
    faculty: str
    apply: Callable[[Grid], Grid] = field(compare=False)
    words: str = ""

    def run(self, grid: Grid) -> Optional[Grid]:
        try:
            return self.apply(grid)
        except Exception:
            return None


#: The word form of every operation, so a rule can be said as well as run.
WORDS: Dict[str, str] = {
    "identity": "the grid stays the same",
    "rotate_90": "rotate a quarter turn clockwise",
    "rotate_180": "rotate a half turn",
    "rotate_270": "rotate a quarter turn anticlockwise",
    "flip_horizontal": "mirror left to right",
    "flip_vertical": "mirror top to bottom",
    "transpose": "reflect in the main diagonal",
    "anti_transpose": "reflect in the anti-diagonal",
    "gravity_down": "the coloured cells fall to the bottom",
    "gravity_up": "the coloured cells rise to the top",
    "gravity_left": "the coloured cells slide to the left",
    "gravity_right": "the coloured cells slide to the right",
    "recolour": "every cell of one colour becomes another",
    "conditional_recolour": "a shape's colour is decided by how big it is",
    "scale_2": "every cell becomes a two by two block",
    "scale_3": "every cell becomes a three by three block",
    "crop_bbox": "keep the bounding box of the coloured cells",
}

#: Which word the reverse direction of the cross-domain check reads.
PHRASES: Dict[str, str] = {
    "quarter turn clockwise": "rotate_90",
    "half turn": "rotate_180",
    "quarter turn anticlockwise": "rotate_270",
    "mirror left to right": "flip_horizontal",
    "mirror top to bottom": "flip_vertical",
    "main diagonal": "transpose",
    "anti-diagonal": "anti_transpose",
    "fall to the bottom": "gravity_down",
    "rise to the top": "gravity_up",
    "slide to the left": "gravity_left",
    "slide to the right": "gravity_right",
    "bounding box": "crop_bbox",
}


def read_words(text: str) -> Optional[str]:
    """The cross-domain faculty's reverse direction: words to an operation."""
    lowered = text.lower()
    for phrase, operation in PHRASES.items():
        if phrase in lowered:
            return operation
    return None


def _named(name: str, faculty: str,
           apply: Callable[[Grid], Grid]) -> Candidate:
    base = name.split("|")[0]
    return Candidate(name=name, faculty=faculty, apply=apply,
                     words=WORDS.get(base, name))


def geometry_candidates(puzzle: Puzzle) -> Tuple[Candidate, ...]:
    """The dihedral group and the four gravities."""
    out = [
        _named("identity", "geometry", lambda g: g),
        _named("rotate_90", "geometry", rotate90),
        _named("rotate_180", "geometry", rotate180),
        _named("rotate_270", "geometry", rotate270),
        _named("flip_horizontal", "geometry", flip_h),
        _named("flip_vertical", "geometry", flip_v),
        _named("transpose", "geometry", transpose),
        _named("anti_transpose", "geometry", anti_transpose),
    ]
    for direction in ("down", "up", "left", "right"):
        out.append(_named(f"gravity_{direction}", "geometry",
                          lambda g, d=direction: gravity(g, d)))
    return tuple(out)


def _colour_map(puzzle: Puzzle) -> Optional[Dict[int, int]]:
    mapping: Dict[int, int] = {}
    for source, target in puzzle.train:
        if _shape(source) != _shape(target):
            return None
        for row_in, row_out in zip(source, target):
            for a, b in zip(row_in, row_out):
                if mapping.setdefault(a, b) != b:
                    return None
    return mapping if any(a != b for a, b in mapping.items()) else None


def _conditional_rule(puzzle: Puzzle) -> Optional[Dict[Tuple[int, str], int]]:
    votes: Dict[Tuple[int, str], set] = {}
    for source, target in puzzle.train:
        if _shape(source) != _shape(target):
            return None
        for size, colour, cells in components(source):
            outputs = {target[y][x] for y, x in cells}
            if len(outputs) != 1:
                return None
            votes.setdefault((colour, size_bucket(size)), set()).update(outputs)
    rule = {key: next(iter(values)) for key, values in votes.items()
            if len(values) == 1}
    return rule or None


def apply_conditional(grid: Grid, rule: Dict[Tuple[int, str], int]) -> Grid:
    out = [list(row) for row in grid]
    for size, colour, cells in components(grid):
        target = rule.get((colour, size_bucket(size)))
        if target is not None:
            for y, x in cells:
                out[y][x] = target
    return tuple(tuple(row) for row in out)


def recolour_candidates(puzzle: Puzzle) -> Tuple[Candidate, ...]:
    """A flat colour map, and the component-size rule that refines it."""
    out: List[Candidate] = []
    mapping = _colour_map(puzzle)
    if mapping is not None:
        out.append(_named("recolour", "recolour",
                          lambda g, m=mapping: tuple(
                              tuple(m.get(value, value) for value in row)
                              for row in g)))
    rule = _conditional_rule(puzzle)
    if rule is not None:
        out.append(_named("conditional_recolour", "recolour",
                          lambda g, r=rule: apply_conditional(g, r)))
    return tuple(out)


def shape_candidates(puzzle: Puzzle) -> Tuple[Candidate, ...]:
    """The operations that change the grid's size or position."""
    out = [
        _named("scale_2", "shape", lambda g: scale(g, 2)),
        _named("scale_3", "shape", lambda g: scale(g, 3)),
        _named("crop_bbox", "shape", crop_bbox),
    ]
    for distance in (1, 2):
        for dy, dx, label in ((distance, 0, "down"), (-distance, 0, "up"),
                              (0, distance, "right"), (0, -distance, "left")):
            out.append(Candidate(
                name=f"shift_{label}_{distance}", faculty="shape",
                apply=lambda g, dy=dy, dx=dx: shift(g, dy, dx),
                words=f"everything moves {distance} to the {label}"))
    return tuple(out)


#: The faculties, in the order the relay reads them.
FACULTIES: Tuple[str, ...] = ("recolour", "geometry", "shape")

#: The quota each faculty keeps at the front of a relayed answer.
QUOTAS: Tuple[Tuple[str, int], ...] = (("recolour", 2), ("geometry", 2),
                                       ("shape", 1))

#: Which faculty leads: the one that reads the puzzle's own pairs.
LEADER = "recolour"


def candidates_of(puzzle: Puzzle, faculty: str) -> Tuple[Candidate, ...]:
    if faculty == "geometry":
        return geometry_candidates(puzzle)
    if faculty == "recolour":
        return recolour_candidates(puzzle)
    if faculty == "shape":
        return shape_candidates(puzzle)
    raise ValueError(f"unknown faculty {faculty!r}")


# ===========================================================================
#  The look: eight cheap dimensions, before the expensive gate
# ===========================================================================

#: The dimensions the visual filter checks, named so a failure can be read.
DIMENSIONS: Tuple[str, ...] = ("palette", "size", "aspect", "components",
                               "symmetry", "density", "colours", "change")


def _density(g: Grid) -> Fraction:
    height, width = _shape(g)
    if height == 0 or width == 0:
        return Fraction(0)
    filled = sum(1 for row in g for value in row if value != 0)
    return Fraction(filled, height * width)


def _symmetries(g: Grid) -> frozenset:
    out = set()
    if g and all(row == tuple(reversed(row)) for row in g):
        out.add("h")
    if g == tuple(reversed(g)):
        out.add("v")
    return frozenset(out)


def look(candidate: Candidate, puzzle: Puzzle) -> Dict[str, bool]:
    """The eight-dimension visual feedback, on the first training pair.

    Cheap by construction: it runs the candidate once and compares summary
    properties of the result against the training *outputs*.  A candidate that
    fails here is never verified, which is where the filter faculty earns its
    place -- the verification gate is the expensive step and the look pays for
    most of it.
    """
    source, _ = puzzle.train[0]
    produced = candidate.run(source)
    if produced is None or not produced or not produced[0]:
        return {name: False for name in DIMENSIONS}
    out_colours = {value for _, target in puzzle.train
                   for row in target for value in row}
    out_shapes = {_shape(target) for _, target in puzzle.train}
    out_components = {len(components(target)) for _, target in puzzle.train}
    out_symmetries = {_symmetries(target) for _, target in puzzle.train}
    out_palette_sizes = {len({value for row in target for value in row})
                         for _, target in puzzle.train}
    out_densities = {_density(target) for _, target in puzzle.train}
    out_aspects = {Fraction(len(target), len(target[0]))
                   for _, target in puzzle.train if target and target[0]}
    seen_colours = {value for row in produced for value in row}
    shape = _shape(produced)
    return {
        "palette": seen_colours <= out_colours,
        "size": shape in out_shapes,
        "aspect": (Fraction(shape[0], shape[1]) in out_aspects
                   if shape[1] else False),
        "components": len(components(produced)) in out_components,
        "symmetry": _symmetries(produced) in out_symmetries,
        "density": _density(produced) in out_densities,
        "colours": len(seen_colours) in out_palette_sizes,
        "change": (produced == puzzle.train[0][1]) or any(
            candidate.run(a) != a for a, _ in puzzle.train),
    }


def look_score(candidate: Candidate, puzzle: Puzzle) -> Fraction:
    """How many of the eight dimensions the candidate passes, exactly."""
    marks = look(candidate, puzzle)
    return Fraction(sum(1 for value in marks.values() if value),
                    len(DIMENSIONS))


def survives(candidate: Candidate, puzzle: Puzzle) -> bool:
    """Whether the look lets a candidate through to the verification gate."""
    return all(look(candidate, puzzle).values())


def verifies(candidate: Candidate, puzzle: Puzzle) -> bool:
    """The expensive gate: the rule reproduces every training pair exactly."""
    for source, target in puzzle.train:
        if candidate.run(source) != target:
            return False
    return True


def cross_domain_ok(candidate: Candidate) -> bool:
    """The cross-domain check: the rule's words name the rule again.

    A candidate is said in words and the words are read back to an operation;
    a rule whose description does not round-trip is one the stack cannot
    explain, and the check is reported rather than enforced -- the two
    generated rules (`recolour`, `conditional_recolour`) have no fixed phrase
    because their content is the table they carry.
    """
    read = read_words(candidate.words)
    return read is not None and read == candidate.name.split("|")[0]


# ===========================================================================
#  The stack over one puzzle
# ===========================================================================

@dataclass(frozen=True)
class Attempt:
    """What the stack did with one puzzle."""

    puzzle: str
    proposed: int
    survived: int
    verified: Optional[str]
    faculty: Optional[str]
    leader_verified: Optional[str]
    confidence: Fraction
    gate_fired: bool
    solved_test: Optional[bool]
    cross_domain: int

    def as_json(self) -> Dict[str, object]:
        return {"puzzle": self.puzzle, "proposed": self.proposed,
                "survived": self.survived, "verified": self.verified,
                "faculty": self.faculty, "confidence": str(self.confidence),
                "gate_fired": self.gate_fired,
                "solved_test": self.solved_test}


def ranked_answers(puzzle: Puzzle) -> Dict[str, st.Answer]:
    """Each faculty's candidates, best first by the look, with its confidence."""
    out: Dict[str, st.Answer] = {}
    for faculty in FACULTIES:
        scored = sorted(
            ((look_score(candidate, puzzle), candidate.name)
             for candidate in candidates_of(puzzle, faculty)),
            key=lambda pair: (-pair[0], pair[1]))
        out[faculty] = st.Answer(
            faculty=faculty,
            names=tuple(name for _, name in scored),
            confidence=scored[0][0] if scored else Fraction(0))
    return out


#: The gate: a leader that passes fewer than this share of the look's
#: dimensions is judged to have nothing for this puzzle.
GATE = Fraction(7, 8)


def attempt(puzzle: Puzzle, *, gate: Fraction = GATE,
            quotas: Sequence[Tuple[str, int]] = QUOTAS) -> Attempt:
    """Run the stack on one puzzle and record who carried it."""
    table = {candidate.name: candidate
             for faculty in FACULTIES
             for candidate in candidates_of(puzzle, faculty)}
    answers = ranked_answers(puzzle)
    order = st.relay(answers, leader=LEADER, gate=gate, quotas=quotas)
    fired = st.gate_fires(answers, leader=LEADER, gate=gate)
    survived = [name for name in order if survives(table[name], puzzle)]
    verified = next((name for name in survived
                     if verifies(table[name], puzzle)), None)
    leader_order = answers[LEADER].names
    leader_verified = next(
        (name for name in leader_order
         if survives(table[name], puzzle) and verifies(table[name], puzzle)),
        None)
    solved: Optional[bool] = None
    if verified is not None and puzzle.test_output is not None:
        solved = table[verified].run(puzzle.test_input) == puzzle.test_output
    return Attempt(
        puzzle=puzzle.name,
        proposed=len(order),
        survived=len(survived),
        verified=verified,
        faculty=table[verified].faculty if verified else None,
        leader_verified=leader_verified,
        confidence=answers[LEADER].confidence,
        gate_fired=fired,
        solved_test=solved,
        cross_domain=sum(1 for name in order
                         if cross_domain_ok(table[name])))


@memo
def vision_report() -> Dict[str, object]:
    """The register, measured: who carries what, and what the filter saves.

    Three numbers decide whether the mechanism transports:

    ``relay_solves`` against ``leader_solves``
        how many puzzles the stack answers against how many the leading
        faculty answers alone.  The relay is never behind -- that is
        ``GLM.Relay.relay_confident`` in the arithmetic -- and it is ahead
        wherever the leader has nothing that survives the look.

    ``carry``
        which faculty supplied the rule that verified, puzzle by puzzle.

    ``filter_saving``
        the share of proposals the cheap look removes before the expensive
        verification gate sees them.
    """
    rows = tuple(attempt(puzzle) for puzzle in puzzles())
    proposed = sum(row.proposed for row in rows)
    survived = sum(row.survived for row in rows)
    relay_solved = tuple(row.puzzle for row in rows if row.verified)
    leader_solved = tuple(row.puzzle for row in rows if row.leader_verified)
    carried = tuple(row.puzzle for row in rows
                    if row.verified and not row.leader_verified)
    test_solved = tuple(row.puzzle for row in rows if row.solved_test)
    carry: Dict[str, List[str]] = {}
    for row in rows:
        if row.faculty:
            carry.setdefault(row.faculty, []).append(row.puzzle)
    return {
        "puzzles": len(rows),
        "gate": GATE,
        "quotas": QUOTAS,
        "leader": LEADER,
        "proposed": proposed,
        "survived": survived,
        "filter_saving": (Fraction(proposed - survived, proposed)
                          if proposed else Fraction(0)),
        "gate_fired": sum(1 for row in rows if row.gate_fired),
        "relay_solves": len(relay_solved),
        "relay_solved": relay_solved,
        "leader_solves": len(leader_solved),
        "leader_solved": leader_solved,
        "carried": carried,
        "test_solved": test_solved,
        "carry": {faculty: tuple(names) for faculty, names
                  in sorted(carry.items())},
        "cross_domain_readable": sum(row.cross_domain for row in rows),
        "verdict": {
            "relay_never_behind_leader": len(relay_solved) >= len(leader_solved),
            "relay_ahead_of_leader": len(relay_solved) > len(leader_solved),
            "filter_removes_most_candidates": (
                Fraction(proposed - survived, proposed) > Fraction(1, 2)
                if proposed else False),
            "more_than_one_faculty_carries": len(carry) > 1,
        },
        "rows": tuple(row.as_json() for row in rows),
        "lean_file": "RequestProject/GLM/Relay.lean",
        "study": "studies/STACK_RELAY_STUDY.md",
    }
