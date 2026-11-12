"""
features.py — the class inventory.

A word's meaning enters the GLM as a set of *semantic classes* taken from
WordNet.  For a noun those are

    * its lexicographer file  (noun.animal, noun.food, noun.artifact, ...)
      — WordNet's own 26-way top-level partition of the noun vocabulary, and
    * every synset on its hypernym path (canine -> carnivore -> mammal ->
      animal -> organism -> ... ), filtered to the ancestors that are neither
      near-universal nor near-unique in the working vocabulary.

Nothing is hashed and nothing is invented word-by-word: "dog" is
{noun.animal, animal.n.01, organism.n.01, ...} because Princeton says so.

For a verb we read the lexicographer file and the WordNet *sentence frames*,
which are WordNet's own selectional restrictions:

    1  Something ----s                  8  Somebody ----s something
    2  Somebody ----s                   9  Somebody ----s somebody
   10  Something ----s somebody        11  Something ----s something
   ...

so `eat` (frame 8) says: animate subject, inanimate object.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Sequence, Set, Tuple

DATA = Path(__file__).resolve().parent.parent.parent / "data"

# ── WordNet sentence-frame semantics (verbatim from the WordNet docs) ────────
FRAME_TEXT = {
    1: "Something ----s",
    2: "Somebody ----s",
    3: "It is ----ing",
    4: "Something is ----ing PP",
    5: "Something ----s something Adjective/Noun",
    6: "Something ----s Adjective/Noun",
    7: "Somebody ----s Adjective",
    8: "Somebody ----s something",
    9: "Somebody ----s somebody",
    10: "Something ----s somebody",
    11: "Something ----s something",
    12: "Something ----s to somebody",
    13: "Somebody ----s on something",
    14: "Somebody ----s somebody something",
    15: "Somebody ----s something to somebody",
    16: "Somebody ----s something from somebody",
    17: "Somebody ----s somebody with something",
    18: "Somebody ----s somebody of something",
    19: "Somebody ----s something on somebody",
    20: "Somebody ----s somebody PP",
    21: "Somebody ----s something PP",
    22: "Somebody ----s PP",
    23: "Somebody's (body part) ----s",
    24: "Somebody ----s somebody to INFINITIVE",
    25: "Somebody ----s somebody INFINITIVE",
    26: "Somebody ----s that CLAUSE",
    27: "Somebody ----s to somebody",
    28: "Somebody ----s to INFINITIVE",
    29: "Somebody ----s whether INFINITIVE",
    30: "Somebody ----s somebody into V-ing something",
    31: "Somebody ----s something with something",
    32: "Somebody ----s INFINITIVE",
    33: "Somebody ----s VERB-ing",
    34: "It ----s that CLAUSE",
    35: "Something ----s INFINITIVE",
}
ANIMATE_SUBJ_FRAMES = {2, 7, 8, 9, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                       24, 25, 26, 27, 28, 29, 30, 31, 32, 33}
THING_SUBJ_FRAMES = {1, 4, 5, 6, 10, 11, 12, 35}
ANIMATE_OBJ_FRAMES = {9, 10, 17, 18, 20, 24, 25, 30}
THING_OBJ_FRAMES = {5, 8, 11, 14, 15, 16, 19, 21, 31}
TRANSITIVE_FRAMES = ANIMATE_OBJ_FRAMES | THING_OBJ_FRAMES
INTRANSITIVE_FRAMES = {1, 2, 3, 4, 22, 23, 27, 28, 32, 33}

ANIMATE_ANCESTORS = {"person.n.01", "animal.n.01", "causal_agent.n.01",
                     "organism.n.01"}
ANIMATE_LEXNAMES = {"noun.person", "noun.animal"}


@dataclass
class Lexicon:
    nouns: Dict[str, dict]
    verbs: Dict[str, dict]

    @classmethod
    def load(cls, path: Path | None = None) -> "Lexicon":
        p = path or (DATA / "wordnet_lexicon.json")
        raw = json.loads(p.read_text())
        return cls(nouns=raw["nouns"], verbs=raw["verbs"])


@dataclass
class ClassInventory:
    """The list of semantic classes used as the GLM's feature alphabet."""

    classes: List[str]
    index: Dict[str, int] = field(init=False)
    noun_classes: Dict[str, FrozenSet[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.index = {c: i for i, c in enumerate(self.classes)}

    # ── construction ─────────────────────────────────────────────────────
    @classmethod
    def build(cls, lex: Lexicon, min_df: float = 0.005, max_df: float = 0.45,
              use_ancestors: bool = True, senses: int = 1) -> "ClassInventory":
        akey = "ancestors" if senses == 1 else "ancestors3"
        lkey = None if senses == 1 else "lexnames3"
        n = len(lex.nouns)
        df: Dict[str, int] = {}
        for w, r in lex.nouns.items():
            seen = ({"LEX:" + r["lexname"]} if lkey is None else
                    {"LEX:" + x for x in r.get(lkey, [r["lexname"]])})
            if use_ancestors:
                seen |= set(r.get(akey, r["ancestors"]))
            for c in seen:
                df[c] = df.get(c, 0) + 1
        keep = [c for c, d in df.items()
                if c.startswith("LEX:") or (min_df * n <= d <= max_df * n)]
        keep.sort()
        inv = cls(classes=keep)
        for w, r in lex.nouns.items():
            names = ({r["lexname"]} if lkey is None
                     else set(r.get(lkey, [r["lexname"]])))
            s = {inv.index["LEX:" + x] for x in names if "LEX:" + x in inv.index}
            if use_ancestors:
                for a in r.get(akey, r["ancestors"]):
                    j = inv.index.get(a)
                    if j is not None:
                        s.add(j)
            inv.noun_classes[w] = frozenset(s)
        return inv

    # ── queries ──────────────────────────────────────────────────────────
    def of(self, noun: str) -> FrozenSet[int]:
        return self.noun_classes.get(noun, frozenset())

    def __len__(self) -> int:
        return len(self.classes)


def is_animate(lex: Lexicon, noun: str) -> bool:
    r = lex.nouns.get(noun)
    if r is None:
        return False
    if r["lexname"] in ANIMATE_LEXNAMES:
        return True
    return bool(ANIMATE_ANCESTORS & set(r["ancestors"]))


def verb_frames(lex: Lexicon, verb: str) -> Set[int]:
    r = lex.verbs.get(verb)
    if r is None:
        return set()
    return set(r["frames_top3"]) or set(r["frames"])
