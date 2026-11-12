"""
generate.py — the GLM speaking.

Generation is search over the substrate: pick a verb, then pick the arguments
whose MOG violation objects are empty (TAX = 0, NRCI = 1).  Nothing is sampled
from a language model and no word list is hand-written; the only inputs are the
WordNet class of each word and the corpus-estimated expectations of each verb.

Surface realisation is deliberately minimal — a determiner, the subject, the
verb in the third person singular, a determiner and the object — because the
point of the exercise is the semantic licensing, not the morphology.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..substrate import popcount
from .encoding import Composer, Utterance
from .features import Lexicon

VOWELS = "aeiou"
IRREGULAR_3SG = {"be": "is", "have": "has", "do": "does", "go": "goes",
                 "say": "says", "can": "can", "will": "will"}


def third_person(verb: str) -> str:
    if verb in IRREGULAR_3SG:
        return IRREGULAR_3SG[verb]
    if verb.endswith(("s", "x", "z", "ch", "sh", "o")):
        return verb + "es"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in VOWELS:
        return verb[:-1] + "ies"
    return verb + "s"


MASS_LEXNAMES = {"noun.substance", "noun.feeling", "noun.attribute",
                 "noun.cognition", "noun.state", "noun.time", "noun.act",
                 "noun.phenomenon", "noun.process", "noun.communication"}


def np(lex: Lexicon, noun: str) -> str:
    r = lex.nouns.get(noun)
    if r is not None and r["lexname"] in MASS_LEXNAMES:
        return noun
    return ("an " if noun[:1] in VOWELS else "a ") + noun


def realise(lex: Lexicon, subject: Optional[str], verb: str,
            object_: Optional[str]) -> str:
    parts = []
    if subject:
        s = np(lex, subject)
        parts.append(s[0].upper() + s[1:])
    parts.append(third_person(verb))
    if object_:
        parts.append(np(lex, object_))
    return " ".join(parts) + "."


@dataclass
class Generated:
    utterance: Utterance
    text: str
    weight: int


class Speaker:
    """Generates sentences whose MOG objects are (nearly) empty."""

    def __init__(self, comp: Composer, lex: Lexicon, nouns: Sequence[str],
                 verbs: Sequence[str]):
        self.comp = comp
        self.lex = lex
        self.nouns = list(nouns)
        self.verbs = list(verbs)

    def candidates(self, verb: str, slot: str, limit: int = 0) -> List[str]:
        """Nouns with an empty violation object in this slot of this verb."""
        out = []
        for n in self.nouns:
            if popcount(self.comp.slot_violation(verb, slot, n)) == 0:
                out.append(n)
                if limit and len(out) >= limit:
                    break
        return out

    def best(self, verb: str, slot: str, k: int = 5) -> List[Tuple[str, int]]:
        scored = [(n, popcount(self.comp.slot_violation(verb, slot, n)))
                  for n in self.nouns]
        scored.sort(key=lambda x: x[1])
        return scored[:k]

    def speak(self, verb: str, rnd: random.Random,
              max_weight: int = 0) -> Optional[Generated]:
        subs = self.candidates(verb, "subj")
        objs = self.candidates(verb, "obj")
        if not subs or not objs:
            return None
        for _ in range(40):
            s = rnd.choice(subs)
            o = rnd.choice(objs)
            if s == o:
                continue
            u = self.comp.compose(s, verb, o)
            if u.weight <= max_weight:
                return Generated(u, realise(self.lex, s, verb, o), u.weight)
        return None

    def speak_many(self, n: int, seed: int = 0, max_weight: int = 0
                   ) -> List[Generated]:
        rnd = random.Random(seed)
        out: List[Generated] = []
        verbs = list(self.verbs)
        rnd.shuffle(verbs)
        for v in verbs:
            g = self.speak(v, rnd, max_weight)
            if g is not None:
                out.append(g)
            if len(out) >= n:
                break
        return out


# ══════════════════════════════════════════════════════════════════════════════
# Repair: what the substrate says is wrong, and the smallest fix
# ══════════════════════════════════════════════════════════════════════════════

def repair(speaker: Speaker, subject: str, verb: str, object_: str,
           k: int = 3) -> Dict[str, object]:
    """Diagnose a broken sentence and propose the smallest replacement."""
    comp = speaker.comp
    u = comp.compose(subject, verb, object_)
    diag = comp.diagnose(u)
    fixes: Dict[str, List[Tuple[str, int]]] = {}
    if popcount(u.subj_obj):
        fixes["subject"] = speaker.best(verb, "subj", k)
    if popcount(u.obj_obj):
        fixes["object"] = speaker.best(verb, "obj", k)
    return {"utterance": u, "diagnosis": diag, "suggestions": fixes}
