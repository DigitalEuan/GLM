"""Lexical carriers: relational triples and syntactic features in 24 dimensions.

The problem this module refuses to solve badly
----------------------------------------------
The tempting way to put a word in a vector is to hash it.  Hashing is not
invertible, so a hashed carrier cannot be decoded, and a "lossless" claim over
hashed carriers is false by construction.  Worse, Python's ``hash`` on ``str``
is salted per process, so a hashed embedding would not even be *deterministic*
across runs -- violating the package's no-randomness invariant silently.

So this module interns instead.  A :class:`Vocabulary` assigns each token a
stable integer index in **first-registration order**, and the carrier stores
indices.  Decoding looks the index back up.  The mapping is exact and
reversible, the vocabulary is an explicit object the caller owns, and the
determinism is a property of the data structure rather than a hope about the
interpreter.

The 24-coordinate layout
------------------------
A :class:`Concept` is a subject with typed relations to other tokens and a
small bag of syntactic features::

    0       subject index
    1       part-of-speech code
    2       arity                     number of relations actually present
    3..5    feature slots             three syntactic feature codes
    6       feature mask              which of slots 3..5 are populated
    7..14   predicate indices         up to eight relations
    15..22  object indices            aligned with the predicates
    23      vocabulary checksum       sum of all indices, mod 2^20

Coordinate 23 is redundant.  It is a cheap integrity coordinate: a carrier
whose indices have been perturbed fails the checksum on decode instead of
silently resolving to different words.

Eight relations is a real ceiling, and :class:`LexiconCodec` raises when a
concept exceeds it rather than truncating.  A truncating encoder would still
pass a substrate round-trip test while quietly losing the ninth relation --
exactly the failure the two-legged round-trip contract in :mod:`.base` exists
to catch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .base import Codec, DataObject, Scalar

__all__ = [
    "LEXICON_LAYOUT", "MAX_RELATIONS", "MAX_FEATURES", "CHECKSUM_MODULUS",
    "POS_CODES", "FEATURE_CODES", "Vocabulary", "Concept", "LexiconCodec",
    "default_vocabulary", "lexicon_objects",
]

MAX_RELATIONS = 8
MAX_FEATURES = 3
CHECKSUM_MODULUS = 1 << 20

LEXICON_LAYOUT: Tuple[str, ...] = (
    ("subject", "pos", "arity")
    + tuple(f"feature{i}" for i in range(MAX_FEATURES))
    + ("feature_mask",)
    + tuple(f"predicate{i}" for i in range(MAX_RELATIONS))
    + tuple(f"object{i}" for i in range(MAX_RELATIONS))
    + ("checksum",)
)
assert len(LEXICON_LAYOUT) == 24

#: Part-of-speech codes.  ``0`` means unspecified.
POS_CODES: Dict[str, int] = {
    "unspecified": 0, "noun": 1, "verb": 2, "adjective": 3, "adverb": 4,
    "pronoun": 5, "preposition": 6, "conjunction": 7, "determiner": 8,
    "numeral": 9, "particle": 10, "interjection": 11,
}

#: Syntactic / semantic feature codes.  ``0`` means an empty slot.
FEATURE_CODES: Dict[str, int] = {
    "none": 0, "singular": 1, "plural": 2, "animate": 3, "inanimate": 4,
    "abstract": 5, "concrete": 6, "countable": 7, "mass": 8, "definite": 9,
    "indefinite": 10, "transitive": 11, "intransitive": 12, "past": 13,
    "present": 14, "future": 15, "comparative": 16, "superlative": 17,
}


class Vocabulary:
    """A stable, insertion-ordered token <-> index map.

    Index ``0`` is reserved for the empty slot, so a real token never has
    index ``0`` and an unused relation slot is unambiguous.
    """

    def __init__(self, tokens: Sequence[str] = ()) -> None:
        self._tokens: List[str] = [""]
        self._index: Dict[str, int] = {"": 0}
        for token in tokens:
            self.intern(token)

    def intern(self, token: str) -> int:
        """Index of ``token``, registering it on first sight."""
        if not isinstance(token, str):
            raise TypeError("Vocabulary: tokens must be strings")
        if token in self._index:
            return self._index[token]
        idx = len(self._tokens)
        self._tokens.append(token)
        self._index[token] = idx
        return idx

    def index(self, token: str) -> int:
        """Index of an already-registered token."""
        try:
            return self._index[token]
        except KeyError:
            raise KeyError(f"Vocabulary: {token!r} is not registered") from None

    def token(self, index: int) -> str:
        """The token at an index."""
        if not 0 <= index < len(self._tokens):
            raise KeyError(f"Vocabulary: index {index} out of range")
        return self._tokens[index]

    def __len__(self) -> int:
        return len(self._tokens)

    def __contains__(self, token: object) -> bool:
        return token in self._index

    def tokens(self) -> Tuple[str, ...]:
        """Every registered token, in index order (slot 0 first)."""
        return tuple(self._tokens)


@dataclass(frozen=True)
class Concept:
    """A lexical concept: a subject, its relations, and its features."""

    subject: str
    pos: str = "unspecified"
    relations: Tuple[Tuple[str, str], ...] = ()
    features: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.pos not in POS_CODES:
            raise ValueError(f"Concept: unknown part of speech {self.pos!r}")
        if len(self.relations) > MAX_RELATIONS:
            raise ValueError(
                f"Concept {self.subject!r}: {len(self.relations)} relations "
                f"exceeds the carrier's {MAX_RELATIONS}; split the concept "
                f"rather than losing a relation")
        if len(self.features) > MAX_FEATURES:
            raise ValueError(
                f"Concept {self.subject!r}: {len(self.features)} features "
                f"exceeds the carrier's {MAX_FEATURES}")
        for f in self.features:
            if f not in FEATURE_CODES:
                raise ValueError(f"Concept: unknown feature {f!r}")

    @property
    def arity(self) -> int:
        """Number of relations carried."""
        return len(self.relations)

    def triples(self) -> Tuple[Tuple[str, str, str], ...]:
        """The concept as ``(subject, predicate, object)`` triples."""
        return tuple((self.subject, p, o) for p, o in self.relations)


class LexiconCodec(Codec):
    """Interning codec: tokens become indices, indices become coordinates."""

    domain = "lexicon"
    layout = LEXICON_LAYOUT

    def __init__(self, vocabulary: Optional[Vocabulary] = None) -> None:
        self.vocabulary = vocabulary if vocabulary is not None else Vocabulary()

    def encode(self, source: Concept) -> DataObject:
        """Intern every token of the concept and lay the indices out."""
        v = self.vocabulary
        subject = v.intern(source.subject)
        preds = [v.intern(p) for p, _o in source.relations]
        objs = [v.intern(o) for _p, o in source.relations]
        preds += [0] * (MAX_RELATIONS - len(preds))
        objs += [0] * (MAX_RELATIONS - len(objs))

        feats = [FEATURE_CODES[f] for f in source.features]
        mask = (1 << len(feats)) - 1
        feats += [0] * (MAX_FEATURES - len(feats))

        carrier: List[Scalar] = [subject, POS_CODES[source.pos], source.arity]
        carrier.extend(feats)
        carrier.append(mask)
        carrier.extend(preds)
        carrier.extend(objs)
        checksum = (subject + sum(preds) + sum(objs)) % CHECKSUM_MODULUS
        carrier.append(checksum)

        return DataObject(
            name=source.subject, domain=self.domain, carrier=carrier,
            attributes={
                "kind": "lexical_concept",
                "pos": source.pos,
                "arity": source.arity,
                "triples": [list(t) for t in source.triples()],
                "features": list(source.features),
            },
            layout=LEXICON_LAYOUT,
            provenance={
                "embedding": ("interned vocabulary indices; no hashing, so "
                              "the map is invertible and run-stable"),
                "vocabulary_size": len(v),
            },
        )

    def decode(self, obj: DataObject) -> Concept:
        """Resolve the indices back to tokens.  Raises on a checksum mismatch."""
        v = self.vocabulary
        c = [int(x) for x in obj.carrier]
        subject, pos_code, arity = c[0], c[1], c[2]
        feats_raw = c[3:3 + MAX_FEATURES]
        mask = c[3 + MAX_FEATURES]
        preds = c[7:7 + MAX_RELATIONS]
        objs = c[7 + MAX_RELATIONS:7 + 2 * MAX_RELATIONS]
        checksum = c[23]

        expected = (subject + sum(preds) + sum(objs)) % CHECKSUM_MODULUS
        if checksum != expected:
            raise ValueError(
                f"lexicon.decode: checksum mismatch for {obj.name!r} "
                f"({checksum} != {expected}); the carrier is corrupt")

        pos = next(k for k, code in POS_CODES.items() if code == pos_code)
        inverse_feature = {code: k for k, code in FEATURE_CODES.items()}
        features = tuple(inverse_feature[feats_raw[i]]
                         for i in range(MAX_FEATURES) if (mask >> i) & 1)
        relations = tuple((v.token(preds[i]), v.token(objs[i]))
                          for i in range(arity))
        return Concept(subject=v.token(subject), pos=pos,
                       relations=relations, features=features)


# ===========================================================================
# A DETERMINISTIC SAMPLE LEXICON
# ===========================================================================

#: A small relational lexicon spanning the four other domains, so that the
#: lexical layer can be exercised without inventing a corpus.
SAMPLE_CONCEPTS: Tuple[Concept, ...] = (
    Concept("electron", "noun",
            (("is_a", "lepton"), ("has_property", "charge"),
             ("has_property", "spin"), ("participates_in", "ionisation")),
            ("singular", "concrete")),
    Concept("energy", "noun",
            (("is_a", "physical_quantity"), ("measured_in", "joule"),
             ("conserved_under", "time_translation")),
            ("abstract", "mass")),
    Concept("hydrogen", "noun",
            (("is_a", "chemical_element"), ("has_property", "atomic_number"),
             ("bonds_with", "oxygen"), ("forms", "water")),
            ("singular", "concrete", "countable")),
    Concept("oxidise", "verb",
            (("acts_on", "metal"), ("produces", "oxide"),
             ("inverse_of", "reduce")),
            ("transitive", "present")),
    Concept("lattice", "noun",
            (("is_a", "mathematical_object"), ("has_property", "dimension"),
             ("has_property", "minimum_norm"), ("example_of", "leech")),
            ("singular", "abstract")),
    Concept("reflect", "verb",
            (("acts_on", "vector"), ("preserves", "inner_product"),
             ("generates", "coxeter_group")),
            ("transitive",)),
    Concept("golay", "noun",
            (("is_a", "error_correcting_code"), ("has_property", "length"),
             ("has_property", "minimum_distance"), ("shadows", "hexacode"),
             ("indexes", "octad")),
            ("singular", "abstract")),
    Concept("monster", "noun",
            (("is_a", "sporadic_group"), ("acts_on", "leech"),
             ("contains", "involution")),
            ("singular", "abstract")),
    Concept("bare_token", "unspecified", (), ()),
    Concept("saturated", "adjective",
            tuple((f"relation_{i}", f"target_{i}") for i in range(MAX_RELATIONS)),
            ("comparative", "superlative", "abstract")),
)


def default_vocabulary() -> Vocabulary:
    """A vocabulary pre-interned over :data:`SAMPLE_CONCEPTS`, in order."""
    v = Vocabulary()
    for concept in SAMPLE_CONCEPTS:
        v.intern(concept.subject)
        for p, o in concept.relations:
            v.intern(p)
            v.intern(o)
    return v


def lexicon_objects() -> Tuple[Tuple[DataObject, ...], LexiconCodec]:
    """The sample lexicon encoded, together with the codec that owns its map.

    The codec is returned alongside the objects because decoding needs the
    same vocabulary; handing back carriers without their vocabulary would be
    handing back something that cannot be read.
    """
    codec = LexiconCodec(default_vocabulary())
    return tuple(codec.encode(c) for c in SAMPLE_CONCEPTS), codec
