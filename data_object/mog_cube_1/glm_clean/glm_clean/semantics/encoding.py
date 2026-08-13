"""
encoding.py — how a word, and then a sentence, becomes a MOG object.

THE ENCODING PRINCIPLE (v5)
---------------------------
Each of the 24 MOG cells IS a semantic class taken from WordNet (a
lexicographer file such as `noun.food`, or a hypernym such as `organism.n.01`).
Which 24 classes those are is not decided by hand: it is searched (see
learn.py).  A word's data object then literally says which of the 24
fundamental categories the word belongs to:

    provision(noun)[c] = 1  iff  the noun's WordNet classes meet cell c

A verb slot carries what it expects, estimated from corpus counts:

    required(verb, slot)   cells nearly every attested argument carries
    forbidden(verb, slot)  cells no attested argument carries, although they
                           are common in that slot overall

and the violation object of one argument is

    violation = (required AND NOT provision) OR (provision AND forbidden)

"the argument lacks something the verb needs" or "the argument brings something
the verb never takes".  Empty violation object = the slot is licensed.

TWO WAYS TO LAY A SENTENCE OUT ON THE GRID
------------------------------------------
  mode "complex"  one 24-cell MOG object per role (subject, object, frame).
                  Full resolution; a sentence is a small complex of objects.
  mode "packed"   the classic single 4x6 grid, 6 cells per role:
                  row0 subject | row1 object | row2 frame | row3 spare.
                  The 24 classes are folded onto 6 cells per row, which loses
                  resolution.  Both are measured in the experiments.

WHY GOLAY
---------
  * TAX(v) = HW(v)*Y + ||v||^2/8 = HW(v)*Q for a 0/1 object.
  * A violation object of weight <= 3 is the unique minimum-weight member of
    its coset, so the substrate can name exactly which cells failed and hence
    which word to change.  At weight 4 there are six equally light candidates
    and the diagnosis becomes ambiguous.  (Both facts are proved in
    RequestProject/GolaySemantics.lean.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from ..substrate import GOLAY_ENGINE, SUBSTRATE, popcount
from .features import (ANIMATE_OBJ_FRAMES, ANIMATE_SUBJ_FRAMES,
                       INTRANSITIVE_FRAMES, THING_OBJ_FRAMES,
                       THING_SUBJ_FRAMES, TRANSITIVE_FRAMES, ClassInventory,
                       Lexicon, is_animate, verb_frames)

_C = SUBSTRATE.get_constants(50)
Y = _C["Y"]
Q = _C["Q"]
B_BUDGET = _C["B"]


# ══════════════════════════════════════════════════════════════════════════════
# Layout: which semantic classes occupy which MOG cells
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Layout:
    """Cell `c` is occupied by the set of WordNet classes `cells[c]`.

    A cell fires for a noun when the noun belongs to any class in the cell.
    A partition (each class in exactly one cell) and a selection (one class per
    cell, most classes unused) are both special cases.
    """

    m: int
    cells: List[FrozenSet[int]]
    name: str = "layout"
    _class_mask: List[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.rebuild()

    def rebuild(self, n_classes: Optional[int] = None) -> None:
        n = n_classes if n_classes is not None else (
            1 + max((max(c) for c in self.cells if c), default=-1))
        masks = [0] * n
        for ci, members in enumerate(self.cells):
            for cl in members:
                if cl < n:
                    masks[cl] |= 1 << ci
        self._class_mask = masks

    def provision(self, class_ids: Iterable[int]) -> int:
        p = 0
        mask = self._class_mask
        for c in class_ids:
            if c < len(mask):
                p |= mask[c]
        return p

    def labels(self, inv: ClassInventory) -> List[str]:
        return [",".join(sorted(short(inv.classes[c]) for c in cell)) or "-"
                for cell in self.cells]

    def copy(self) -> "Layout":
        return Layout(self.m, [frozenset(c) for c in self.cells], self.name)


def short(cls_name: str) -> str:
    if cls_name.startswith("LEX:"):
        return cls_name[4:]
    return cls_name.split(".")[0]


def selection_layout(inv: ClassInventory, class_names: Sequence[str],
                     name: str = "selection") -> Layout:
    cells = [frozenset({inv.index[c]}) for c in class_names]
    return Layout(m=len(cells), cells=cells, name=name)


def fold(layout: Layout, groups: Sequence[Sequence[int]], name: str) -> Layout:
    """Fold an m-cell layout onto len(groups) cells (used by 'packed' mode)."""
    cells = [frozenset().union(*[layout.cells[i] for i in g]) if g else frozenset()
             for g in groups]
    return Layout(m=len(cells), cells=list(cells), name=name)


# ══════════════════════════════════════════════════════════════════════════════
# The selection model (fitted in learn.py)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SlotModel:
    required: Dict[str, int]
    forbidden: Dict[str, int]
    back_required: Dict[str, int]     # keyed by the verb's WordNet lexname
    back_forbidden: Dict[str, int]

    def masks(self, verb: str, verb_lexname: Optional[str]) -> Tuple[int, int]:
        if verb in self.required:
            return self.required[verb], self.forbidden[verb]
        if verb_lexname is not None and verb_lexname in self.back_required:
            return self.back_required[verb_lexname], self.back_forbidden[verb_lexname]
        return 0, 0                    # no evidence -> no opinion


@dataclass
class SelectionModel:
    """Cells are semantic classes; a verb slot has a required and a forbidden
    mask over them."""

    layout: Layout
    subj: SlotModel
    obj: SlotModel

    @property
    def m(self) -> int:
        return self.layout.m

    def slot(self, name: str) -> SlotModel:
        return self.subj if name == "subj" else self.obj

    def violation(self, verb: str, slot: str, provision: int,
                  verb_lexname: Optional[str]) -> int:
        req, forb = self.slot(slot).masks(verb, verb_lexname)
        return (req & ~provision & ((1 << self.layout.m) - 1)) | (provision & forb)

    def cell_labels(self, inv: ClassInventory) -> List[str]:
        return self.layout.labels(inv)


# ══════════════════════════════════════════════════════════════════════════════
# The frame object: WordNet's own sentence frames
# ══════════════════════════════════════════════════════════════════════════════

FRAME_CELL_NAMES = (
    "subject should be animate",
    "subject should be a thing",
    "object missing (verb is transitive)",
    "object present (verb is intransitive)",
    "object should be animate",
    "object should be a thing",
)


def frame_bits(lex: Lexicon, subject: Optional[str], verb: str,
               object_: Optional[str]) -> int:
    fr = verb_frames(lex, verb)
    if not fr:
        return 0
    bits = [0] * 6
    wants_anim_subj = bool(fr & ANIMATE_SUBJ_FRAMES)
    wants_thing_subj = bool(fr & THING_SUBJ_FRAMES)
    if subject is not None:
        subj_anim = is_animate(lex, subject)
        if wants_anim_subj and not wants_thing_subj and not subj_anim:
            bits[0] = 1
        if wants_thing_subj and not wants_anim_subj and subj_anim:
            bits[1] = 1
    if object_ is None and (fr & TRANSITIVE_FRAMES) and not (fr & INTRANSITIVE_FRAMES):
        bits[2] = 1
    if object_ is not None and (fr & INTRANSITIVE_FRAMES) and not (fr & TRANSITIVE_FRAMES):
        bits[3] = 1
    if object_ is not None:
        obj_anim = is_animate(lex, object_)
        wants_anim_obj = bool(fr & ANIMATE_OBJ_FRAMES)
        wants_thing_obj = bool(fr & THING_OBJ_FRAMES)
        if wants_anim_obj and not wants_thing_obj and not obj_anim:
            bits[4] = 1
        if wants_thing_obj and not wants_anim_obj and obj_anim:
            bits[5] = 1
    n = 0
    for b in bits:
        n = (n << 1) | b
    return n


# ══════════════════════════════════════════════════════════════════════════════
# Utterance
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Utterance:
    subject: Optional[str]
    verb: str
    object: Optional[str]
    subj_obj: int            # 24-cell violation object for the subject slot
    obj_obj: int             # 24-cell violation object for the object slot
    frame_obj: int           # 6 used cells, placed in a 24-cell object
    mode: str = "complex"

    @property
    def objects(self) -> Tuple[int, int, int]:
        return (self.subj_obj, self.obj_obj, self.frame_obj)

    @property
    def weight(self) -> int:
        return sum(popcount(o) for o in self.objects)

    @property
    def tax(self):
        return self.weight * Q

    @property
    def nrci(self):
        return B_BUDGET / (B_BUDGET + self.tax)

    def syndromes(self) -> Tuple[int, int, int]:
        return tuple(GOLAY_ENGINE.syndrome_int(o) for o in self.objects)

    @property
    def diagnosable(self) -> bool:
        """Each role object must be the unique lightest member of its coset."""
        for o in self.objects:
            leaders = GOLAY_ENGINE.coset_leaders(o)
            if len(leaders) != 1 or leaders[0] != o:
                return False
        return True

    def text(self) -> str:
        return " ".join(p for p in (self.subject, self.verb, self.object) if p)

    def describe(self, labels: Sequence[str]) -> str:
        labs = list(labels)
        out = [f"[{self.subject or '-'} | {self.verb} | {self.object or '-'}]  "
               f"HW={self.weight}  TAX={float(self.tax):.4f}  "
               f"NRCI={float(self.nrci):.4f}  diagnosable={self.diagnosable}"]
        for tag, o in (("subject", self.subj_obj), ("object", self.obj_obj)):
            if o:
                names = [labs[i] for i in range(len(labs)) if (o >> i) & 1]
                out.append(f"   {tag:8s} violated: {', '.join(names)}")
        if self.frame_obj:
            names = [FRAME_CELL_NAMES[i] for i in range(6)
                     if (self.frame_obj >> i) & 1]
            out.append(f"   {'frame':8s} violated: {', '.join(names)}")
        return "\n".join(out)


class Composer:
    """Turns (subject, verb, object) into MOG objects."""

    def __init__(self, lex: Lexicon, inv: ClassInventory, model: SelectionModel,
                 use_frame: bool = True, mode: str = "complex"):
        self.lex = lex
        self.inv = inv
        self.model = model
        self.layout = getattr(model, "layout", None)
        self.use_frame = use_frame
        self.mode = mode
        self._prov: Dict[str, int] = {}
        self._vlex: Dict[str, Optional[str]] = {}

    def provision(self, noun: str) -> int:
        """For a rule encoder the 'provision' handed on is the full class set."""
        p = self._prov.get(noun)
        if p is None:
            if self.layout is not None:
                p = self.layout.provision(self.inv.of(noun))
            else:
                p = 0
                for c in self.inv.of(noun):
                    p |= 1 << c
            self._prov[noun] = p
        return p

    def verb_lexname(self, verb: str) -> Optional[str]:
        if verb not in self._vlex:
            r = self.lex.verbs.get(verb)
            self._vlex[verb] = r["lexname"] if r else None
        return self._vlex[verb]

    def slot_violation(self, verb: str, slot: str, noun: Optional[str]) -> int:
        if noun is None:
            return 0
        vf = getattr(self.model, "violation_for", None)
        if vf is not None:
            return vf(verb, slot, noun)
        return self.model.violation(verb, slot, self.provision(noun),
                                    self.verb_lexname(verb))

    def compose(self, subject: Optional[str], verb: str,
                object_: Optional[str]) -> Utterance:
        s = self.slot_violation(verb, "subj", subject)
        o = self.slot_violation(verb, "obj", object_)
        f = frame_bits(self.lex, subject, verb, object_) if self.use_frame else 0
        return Utterance(subject, verb, object_, s, o, f, self.mode)

    # ── the snap: minimal repair of a broken utterance ───────────────────
    def diagnose(self, u: Utterance) -> Dict[str, object]:
        out = {}
        for tag, o in (("subject", u.subj_obj), ("object", u.obj_obj),
                       ("frame", u.frame_obj)):
            leaders = GOLAY_ENGINE.coset_leaders(o)
            out[tag] = {
                "weight": popcount(o),
                "n_leaders": len(leaders),
                "exact": len(leaders) == 1 and leaders[0] == o,
                "syndrome": GOLAY_ENGINE.syndrome_int(o),
            }
        return out
