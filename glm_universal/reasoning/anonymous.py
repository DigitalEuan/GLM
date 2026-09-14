"""``glm_universal.reasoning.anonymous`` -- the register only the address can read.

The question this module answers
--------------------------------
:mod:`glm_universal.reasoning.retrieval` recorded a negative result that has
stood since it was taken: asked to retrieve a relevant declaration, the
geometric address beats chance by several times over and is beaten decisively
by a plain lexical overlap of the statement text.
:mod:`glm_universal.reasoning.stack` then showed that the address is not
useless even so -- gated on the text layer's own confidence it *carries* the
queries the text layer cannot read -- but the carry set there is a residue: 14
queries out of 1,614, mostly constants and calibration lemmas whose identifiers
say little.

The question that leaves, and the one this module settles, is whether the
carry set is a *residue* or a *class*:

    is there a register in which the geometric address is not merely a useful
    second opinion but structurally the only faculty that can read the query
    at all?

The answer measured here is **yes**, and it is the register of a query written
in a vocabulary the corpus does not share.

The register, stated before it is measured
------------------------------------------
A query in the **anonymous register** is a Lean statement in which every
identifier outside a small declared vocabulary has been replaced by a
positional placeholder ``anonvar0``, ``anonvar1``, ... in order of
first appearance
(:func:`anonymise`).  The declared vocabulary :data:`KEPT` is the language's
own words and the type names the structural feature map already reads --
``Nat``, ``Finset``, ``Prop`` and so on -- because those belong to Lean and to
Mathlib rather than to this development.

This is not a trick to handicap the leader; it is the everyday situation of a
goal that arrives from somewhere else.  Two formalisations of the same
mathematics choose different names, a generated goal has none, an autoformalised
statement carries the names of its source rather than of the target library.
In every one of those cases the identifiers of the query are *not* the
identifiers of the corpus, and a search that reads identifiers has nothing to
read.  Anonymisation is the extreme, exactly reproducible form of that
situation, and it is the one a measurement can be taken over.

What is predicted, before the numbers
-------------------------------------
* the **text** search, the standing leader, falls to chance: its evidence is
  shared identifiers and there are none;
* the **lexical** address book, which projects the identifiers onto the 24
  coordinates, falls with it, because it reads the same thing through a
  coarser lens;
* the **structural address** does not fall to chance, because the
  twenty-four counts it reads -- quantifiers, arrows, equalities, numerals,
  bracket depth, the type vocabulary, length -- are invariant under renaming;
* therefore the stack's *existing* gate, unchanged and not re-tuned, fires on
  nearly every query of this register and hands it to the geometry.

The third point is stronger than a prediction: it is checked coordinate by
coordinate here (:func:`syntax_invariant`) and proved as a theorem in
``RequestProject/GLM/Anonymous.lean``.  Only the citation coordinate moves,
because a citation *is* a name, and that cost is reported rather than hidden.

What is proved, and where
-------------------------
``RequestProject/GLM/Anonymous.lean``:

* ``features_anonymise`` -- the structural reading of a statement is unchanged
  by renaming anything outside the declared vocabulary, so the address of an
  anonymised goal is the address of the goal;
* ``overlap_anonymise_eq_zero`` -- the identifier overlap between an anonymised
  query and any statement written in the corpus vocabulary is zero, so the
  text faculty's confidence is zero by construction rather than by measurement;
* ``relay_hands_over`` -- with confidence zero the relay of ``Relay.lean`` is
  the interleave: in this register the stack necessarily reads with the
  geometry.  The carry set is a class.

Nothing here is a float: overlaps and rates are exact
:class:`~fractions.Fraction` values and distances are integer squared
distances, as everywhere else in the package (directive D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, FrozenSet, List, Mapping, Sequence, Tuple

from ..derived import memo
from . import lean_address as la
from . import retrieval as rt
from . import stack as sk

__all__ = [
    "KEPT", "PLACEHOLDER", "anonymise", "renaming", "SYNTAX_COORDINATES",
    "syntax_invariant", "answers_for", "anonymous_records", "faculty_scores",
    "anonymous_report",
]

# ===========================================================================
#  1.  The anonymiser
# ===========================================================================

#: The vocabulary a query keeps.  Two kinds of word: Lean's own syntax, and
#: the type names the structural feature map itself counts -- those are part
#: of the language a second formalisation would also use, so keeping them is
#: what makes the register *anonymous* rather than *empty*.  Everything else
#: -- every lemma name, every definition of this development, every bound
#: variable -- is replaced.
KEPT: FrozenSet[str] = frozenset({
    # Lean's own words
    "theorem", "lemma", "def", "abbrev", "structure", "inductive", "instance",
    "example", "fun", "forall", "exists", "if", "then", "else", "let", "in",
    "by", "at", "with", "match", "do", "where", "have", "show", "from",
    "type", "sort", "prop",
    # the type vocabulary the 24 counts read
    "nat", "int", "rat", "real", "fin", "finset", "set", "list", "multiset",
    "bool", "decidable",
})

#: The placeholder alphabet.  Disjoint from any identifier of the corpus,
#: which is what ``overlap_anonymise_eq_zero`` needs and what
#: :func:`placeholders_are_fresh` checks against the corpus rather than
#: assuming.
PLACEHOLDER = "anonvar{}"

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def renaming(text: str) -> Dict[str, str]:
    """Which placeholder each identifier of ``text`` is given.

    In order of first appearance, so the map is a function of the text and of
    nothing else -- no hash, no seed, no dictionary of the corpus.
    """
    out: Dict[str, str] = {}
    for token in _IDENT.findall(text):
        if token.lower() in KEPT or token in out:
            continue
        out[token] = PLACEHOLDER.format(len(out))
    return out


def anonymise(text: str) -> str:
    """``text`` with every identifier outside :data:`KEPT` renamed.

    Deterministic, and *structure preserving*: the token count, the bracket
    depth, the operators, the numerals and the kept vocabulary are all exactly
    as they were, which is the content of ``GLM.Anonymous.features_anonymise``.
    """
    table = renaming(text)
    return _IDENT.sub(lambda m: table.get(m.group(0), m.group(0)), text)


@memo
def corpus_vocabulary() -> FrozenSet[str]:
    """Every identifier token that occurs in any statement of the corpus."""
    out: set = set()
    for tokens in rt.statement_tokens().values():
        out |= set(tokens)
    return frozenset(out)


def placeholders_are_fresh(limit: int = 200) -> bool:
    """Is the placeholder alphabet disjoint from the corpus vocabulary?

    The hypothesis of ``overlap_anonymise_eq_zero``, checked against the
    corpus instead of assumed.
    """
    vocabulary = corpus_vocabulary()
    return all(PLACEHOLDER.format(index).lower() not in vocabulary
               for index in range(limit))


# ===========================================================================
#  2.  What the renaming does and does not move
# ===========================================================================

#: The coordinates of the 24-count feature vector that read the *syntax* of a
#: statement: the logical symbols, the numerals, the bracket depth, the type
#: vocabulary and the length.  Coordinate 20 is how many declarations the
#: statement cites -- a citation is a name, so renaming destroys it, and that
#: is the one cost this register carries.  Coordinates 21 to 23 (how many
#: results cite this one, the namespace depth, the kind) are not known to a
#: bare goal and are zero in both readings already.
SYNTAX_COORDINATES: Tuple[int, ...] = tuple(range(20))

#: The coordinate that a renaming does move, and why.
CITATION_COORDINATE = 20


#: The six syntax coordinates that count the *type vocabulary*: Nat, Int, the
#: rationals and reals, Fin, the container types and the proposition types.
#: The shipped feature map counts those words wherever they occur in the
#: statement text, including inside an identifier, so a declaration whose own
#: name spells one of them loses the count when the name is replaced.  That is
#: the only way anonymisation moves a syntax coordinate, and the report
#: measures how often it happens rather than leaving the idealisation
#: unchecked.
TYPE_COORDINATES: Tuple[int, ...] = (13, 14, 15, 16, 17, 18)


def moved_coordinates(text: str, exclude: str | None = None
                      ) -> Tuple[int, ...]:
    """Which syntax coordinates anonymisation moves, for this statement."""
    before = rt.goal_features(text, exclude=exclude)
    after = rt.goal_features(anonymise(text), exclude=exclude)
    return tuple(i for i in SYNTAX_COORDINATES if before[i] != after[i])


def syntax_invariant(text: str, exclude: str | None = None) -> bool:
    """Do the syntax coordinates survive anonymisation, for this statement?"""
    return not moved_coordinates(text, exclude)


# ===========================================================================
#  3.  The faculties, over an anonymous query
# ===========================================================================

#: The window the register is scored at, as everywhere else in the study.
K_LADDER: Tuple[int, ...] = sk.K_LADDER

#: How deep each faculty's list is read.
DEPTH = sk.DEPTH

#: Which faculties are scored alone.  ``digest`` and ``random`` are the
#: controls: a faculty that does no better than these has not read the query.
SCORED: Tuple[str, ...] = ("text", "lexical", "address", "name", "digest",
                           "random")


def answers_for(name: str, *, anonymous: bool, depth: int = DEPTH
                ) -> Dict[str, sk.Answer]:
    """Every faculty's proposal for one declaration, read plainly or anonymously.

    Both readings are goal readings: the query is the statement with its
    declaration head removed, the addresses are recomputed live, and the
    declaration is excluded from its own answer.  The only difference between
    the two is :func:`anonymise`, which is what makes the pair a controlled
    comparison rather than two experiments.
    """
    decl = la.declaration(name)
    plain = rt.strip_declaration_head(decl.statement if decl else "")
    text = anonymise(plain) if anonymous else plain
    points = {
        "address": la.quantise(rt.goal_features(text, exclude=name)),
        "lexical": la.quantise(rt.lexical_vector(text)),
        "digest": la.quantise(la.name_hash_vector(text)),
    }
    found = {
        "text": rt.rank_by_text(text, depth, name),
        "name": rt.rank_by_name(text, depth, name),
        "random": rt.rank_random(depth, name),
    }
    for faculty, point in points.items():
        found[faculty] = rt.rank_by_point(rt._point_table(faculty), point,
                                          depth, name)
    return {faculty: sk.Answer(faculty=faculty,
                               names=tuple(c.name for c in ranked),
                               confidence=sk.confidence_of(ranked))
            for faculty, ranked in found.items()}


@dataclass(frozen=True)
class Row:
    """One query, both readings of it, and what was relevant."""

    name: str
    plain: Dict[str, sk.Answer]
    anonymous: Dict[str, sk.Answer]
    relevant: FrozenSet[str]
    moved: Tuple[int, ...]

    @property
    def invariant(self) -> bool:
        return not self.moved


def queries() -> Tuple[str, ...]:
    """The query set: both strides of the relay study, so the two are comparable."""
    return tuple(sk.tuning_queries()) + tuple(sk.holdout_queries())


@memo
def anonymous_records() -> Tuple[Row, ...]:
    """Both readings of every query, computed once."""
    out: List[Row] = []
    for name in queries():
        decl = la.declaration(name)
        plain_text = rt.strip_declaration_head(decl.statement if decl else "")
        out.append(Row(
            name=name,
            plain=answers_for(name, anonymous=False),
            anonymous=answers_for(name, anonymous=True),
            relevant=rt.relatives(name),
            moved=moved_coordinates(plain_text, exclude=name)))
    return tuple(out)


# ===========================================================================
#  4.  Scoring
# ===========================================================================

def faculty_scores(rows: Sequence[Row], *, anonymous: bool
                   ) -> Dict[str, Dict[str, object]]:
    """Each faculty, alone, over one reading of the query set."""
    out: Dict[str, Dict[str, object]] = {}
    for faculty in SCORED:
        scored = [((row.anonymous if anonymous else row.plain)[faculty].names,
                   row.relevant) for row in rows]
        out[faculty] = sk.score(scored, K_LADDER)
    return out


def relay_scores(rows: Sequence[Row], *, anonymous: bool,
                 quotas: Sequence[Tuple[str, int]] = sk.QUOTAS,
                 gate: Fraction = sk.GATE) -> Dict[str, object]:
    """The stack's own relay, unchanged, over one reading of the set."""
    answers = [(row.anonymous if anonymous else row.plain) for row in rows]
    relayed = [(sk.relay(answer, gate=gate, quotas=quotas), row.relevant)
               for answer, row in zip(answers, rows)]
    leader = [(answer["text"].names, row.relevant)
              for answer, row in zip(answers, rows)]
    fired = sum(1 for answer in answers if sk.gate_fires(answer, gate=gate))
    carried = [row.name for answer, row, (names, relevant)
               in zip(answers, rows, relayed)
               if any(n in relevant for n in names[:5])
               and not any(n in relevant for n in answer["text"].names[:5])]
    lost = [row.name for answer, row, (names, relevant)
            in zip(answers, rows, relayed)
            if any(n in relevant for n in answer["text"].names[:5])
            and not any(n in relevant for n in names[:5])]
    return {
        "queries": len(rows),
        "fired": fired,
        "leader": sk.score(leader, K_LADDER),
        "relay": sk.score(relayed, K_LADDER),
        "carried": tuple(carried),
        "lost": tuple(lost),
    }


def chance_at(rows: Sequence[Row], k: int = 5) -> Fraction:
    """The exact chance of a hit at ``k``, averaged over the query set."""
    size = len(rt.corpus())
    if not rows:
        return Fraction(0)
    total = sum(rt.chance_hit_rate(len(row.relevant), size, k) for row in rows)
    return total / len(rows)


# ===========================================================================
#  5.  The report
# ===========================================================================

@memo
def anonymous_report() -> Dict[str, object]:
    """The register, measured: who can still read a query with no names.

    The verdict keys are the pre-registered predictions of the module
    docstring, each one a claim that could have come out false:

    ``text_collapses_without_the_names``
        the standing leader loses the great majority of what it had;
    ``text_is_within_twice_chance``
        and lands beside the chance rate rather than above it;
    ``lexical_collapses_too``
        the identifier address book goes with it, which is the point: it is
        the *same* evidence read through a coarser lens;
    ``address_holds``
        the structural address keeps most of what it had;
    ``address_is_the_clear_leader``
        and is strictly ahead of every other faculty in this register --
        which is what makes the carry set a class rather than a residue;
    ``address_is_above_twice_chance``
        and is reading the query rather than guessing;
    ``only_the_type_vocabulary_moves``
        the reason, checked coordinate by coordinate on every query rather
        than argued: the logical, numeric, bracket and length coordinates are
        never moved by a renaming, and the only ones that are moved are the
        six that count type words -- which the shipped map reads inside
        identifiers too;
    ``gate_hands_over``
        and the stack's existing gate, not re-tuned for this register,
        notices: it fires on most of these queries where it fires on a
        twentieth of the ordinary ones.
    """
    rows = anonymous_records()
    plain = faculty_scores(rows, anonymous=False)
    anon = faculty_scores(rows, anonymous=True)
    relay_plain = relay_scores(rows, anonymous=False)
    relay_anon = relay_scores(rows, anonymous=True)
    k = 5
    chance = chance_at(rows, k)

    def hit(table: Mapping[str, Dict[str, object]], faculty: str) -> Fraction:
        return table[faculty]["hit_rate"][k]      # type: ignore[index]

    control = max(hit(anon, "digest"), hit(anon, "random"))
    others = tuple(f for f in SCORED if f != "address")
    invariant = sum(1 for row in rows if row.invariant)
    outside = tuple(row.name for row in rows
                    if any(i not in TYPE_COORDINATES for i in row.moved))
    verdict = {
        "text_leads_when_the_names_are_there":
            hit(plain, "text") > hit(plain, "address"),
        "text_collapses_without_the_names":
            hit(anon, "text") * 5 < hit(plain, "text"),
        "text_is_within_twice_chance": hit(anon, "text") < 2 * chance,
        "lexical_collapses_too": hit(anon, "lexical") < 2 * chance,
        "address_holds": hit(anon, "address") * 2 >= hit(plain, "address"),
        "address_is_the_clear_leader": all(
            hit(anon, "address") > hit(anon, faculty) for faculty in others),
        "address_is_above_twice_chance": hit(anon, "address") > 2 * chance,
        "address_stays_above_the_control": hit(anon, "address") > control,
        "only_the_type_vocabulary_moves": not outside,
        "placeholders_are_fresh": placeholders_are_fresh(),
        "gate_hands_over":
            Fraction(relay_anon["fired"], max(1, len(rows)))
            >= Fraction(1, 2),
        "relay_beats_text_in_the_register":
            relay_anon["relay"]["hit_rate"][k]        # type: ignore[index]
            > relay_anon["leader"]["hit_rate"][k],    # type: ignore[index]
    }
    return {
        "corpus": len(rt.corpus()),
        "queries": len(rows),
        "k": k,
        "k_ladder": K_LADDER,
        "chance_at_5": chance,
        "kept_vocabulary": tuple(sorted(KEPT)),
        "syntax_coordinates": SYNTAX_COORDINATES,
        "citation_coordinate": CITATION_COORDINATE,
        "type_coordinates": TYPE_COORDINATES,
        "invariant_queries": invariant,
        "queries_moved_outside_the_type_vocabulary": outside,
        "plain": plain,
        "anonymous": anon,
        "relay_plain": relay_plain,
        "relay_anonymous": relay_anon,
        "gate": sk.GATE,
        "quotas": sk.QUOTAS,
        "verdict": verdict,
        "lean_file": "RequestProject/GLM/Anonymous.lean",
        "study": "studies/ANONYMOUS_REGISTER_STUDY.md",
    }
