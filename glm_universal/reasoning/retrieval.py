"""``glm_universal.reasoning.retrieval`` -- the address book, used as an index.

The question this module answers
--------------------------------
:mod:`glm_universal.reasoning.lean_address` gives every declaration of the Lean
development a deterministic Leech address and measures that *nearest by
address* shares a source file far more often than chance.  That is an
observation about a table.  This module asks the next question, which is the
one that decides whether the substrate has a **functional** role rather than a
descriptive one:

    Given a question -- a declaration, or a bare Lean goal -- can the address
    book *retrieve* the declarations that are relevant to it, and does it beat
    the controls?

Nothing here is a float.  Distances are integer squared Euclidean distances,
overlaps are exact :class:`~fractions.Fraction` ratios, and every rate reported
is a ``Fraction``.

What counts as a hit
--------------------
A retrieved declaration is *relevant* to a query declaration when it is a
**relative**: it lives in the same source file, or it cites the query, or the
query cites it.  Neither relation is anywhere in the feature map -- the address
is built from twenty four syntactic counts and knows nothing of file names --
so "the neighbours are relatives" is a prediction the scheme can fail.

The eight schemes, scored on the same queries
---------------------------------------------
``address``
    The subject of the experiment: rank the corpus by squared distance between
    Leech addresses.

``features``
    **The ablation that asks what the lattice contributes.**  Identical, but
    ranking on the raw 24-count feature vectors with no quantisation.  If this
    scores the same as ``address``, then the lattice is carrying the features
    faithfully and adding nothing of its own to the ranking -- which is what
    the measurement finds, and it is stated rather than hidden.

``lexical``
    A *second* address scheme, built to give the geometry the one thing the
    structural feature map deliberately throws away: the identifiers.  A
    statement's identifier tokens are counted by their initial letter into 24
    buckets (:func:`lexical_vector`) -- a stated, recoverable projection, not a
    digest -- and the result is quantised to the lattice exactly as the
    structural vector is.  This is the fair test of "would the lattice do
    better if it were given the words?".

``text``
    **The strong control.**  Rank by exact Jaccard overlap of identifier tokens
    between the query text and the candidate's statement -- what a plain
    lexical search over the sources does.  No lattice, no feature map, no
    address book.  A retrieval layer that cannot beat this has not earned its
    place in the pipeline, and the honest report is that on this task it does
    not.

``name``
    Name-substring search: rank by how many of the query's identifier tokens
    appear in the candidate's fully qualified name.

``digest``
    The determinism-only control of directive D3 -- addresses derived from the
    SHA-256 of the name, which know nothing about the declaration.

``shuffled``
    The feature addresses re-assigned by a seeded permutation: the same
    geometry with the pairing destroyed.

``random``
    A seeded permutation of the corpus, ignoring the query entirely.

Alongside them, ``chance`` is computed exactly rather than simulated: for each
query, the probability that a uniformly chosen set of ``k`` distinct other
declarations contains at least one relative.

What is proved, and where
-------------------------
``RequestProject/GLM/Retrieval.lean`` carries the part that is a theorem rather
than a measurement, and it is the part that survives whatever the hit rates
turn out to be:

* ``ranked_eq_of_perm`` -- the ranking does not depend on the order the corpus
  was read in, because ties are broken by name and never by arrival;
* ``topk_prefix`` / ``hit_mono`` -- widening ``k`` adds candidates at the end
  and never reorders or drops one;
* ``mem_topk`` -- the index cannot return a declaration that is not in the
  corpus;
* ``filterRadius_eq_nil_certifies_absence`` -- an empty shortlist is a *proof*
  that nothing lies within the radius, which is the refusal boundary of this
  layer;
* ``complete_shortlist`` -- everything within feature distance ``r`` of the
  query is within address distance ``r + 2ρ``, so a radius search over the
  addresses never misses what a search over the features would have found.
  :func:`shortlist_report` checks that bound against the real corpus.

The verdict, in one line
------------------------
Address retrieval carries real information -- several times the hit rate of the
digest, the reshuffle and chance, and well above name search -- and it is
beaten decisively by a plain lexical search over the statement text; the
lattice quantisation neither costs nor adds ranking accuracy over the raw
features; and giving the geometry the identifiers instead of the syntax does
not close the gap.  What the lattice does earn here is exactness: the lossless
read-back of :mod:`~glm_universal.reasoning.lean_address` and the two
guarantees above -- a complete shortlist and a certified absence.
``studies/ADDRESS_RETRIEVAL_STUDY.md`` states it with the numbers.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from .. import integrity
from . import lean_address as la

# ===========================================================================
#  Corpus, relatives and chance
# ===========================================================================

#: How many candidates a retrieval returns unless told otherwise.
K_DEFAULT = 5

#: Sizes of ``k`` the report scores, so that ``hit_mono`` can be seen holding.
K_LADDER: Tuple[int, ...] = (1, 3, 5, 10)


def corpus() -> Tuple[str, ...]:
    """Every addressed declaration, in the address book's order."""
    book = la.address_book()
    return tuple(book["order"]) if book else ()


@memo
def file_of() -> Dict[str, str]:
    """The source file of each declaration."""
    book = la.address_book()
    if book is None:
        return {}
    return {name: book["declarations"][name]["file"] for name in book["order"]}


@memo
def relative_table() -> Dict[str, FrozenSet[str]]:
    """For every declaration, the declarations counted as relevant to it.

    Same file, or joined by a citation in either direction.  Both relations
    are properties of the development, not of the address: the feature map
    contains neither the file name nor the direction of a citation.
    """
    names = corpus()
    files = file_of()
    by_file: Dict[str, List[str]] = {}
    for name in names:
        by_file.setdefault(files[name], []).append(name)
    graph = la.citation_graph()
    linked: Dict[str, set] = {name: set(graph.get(name, ())) for name in names}
    for source, targets in graph.items():
        for target in targets:
            if target in linked:
                linked[target].add(source)
    out: Dict[str, FrozenSet[str]] = {}
    for name in names:
        group = set(by_file[files[name]])
        group.update(linked[name])
        group.discard(name)
        out[name] = frozenset(group & set(names))
    return out


def relatives(name: str) -> FrozenSet[str]:
    """The declarations a retrieval for ``name`` ought to find."""
    return relative_table().get(name, frozenset())


def chance_hit_rate(relatives_count: int, corpus_size: int, k: int
                    ) -> Fraction:
    """Exactly the probability that ``k`` random draws contain a relative.

    ``1 - C(m - r, k) / C(m, k)`` with ``m = corpus_size - 1`` candidates of
    which ``r`` are relatives -- computed as a product of rationals, so the
    answer is exact and no factorial is built.
    """
    m = corpus_size - 1
    r = relatives_count
    if k <= 0 or m <= 0:
        return Fraction(0)
    if r >= m or k > m - r:
        return Fraction(1)
    miss = Fraction(1)
    for i in range(k):
        miss *= Fraction(m - r - i, m - i)
    return 1 - miss


# ===========================================================================
#  Reading a query
# ===========================================================================

_HEAD = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?"
    r"(?:(?:private|protected|noncomputable|partial|unsafe|scoped)\s+)*"
    r"(?:theorem|lemma|def|abbrev|structure|inductive|instance|example)\s+\S+")

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def strip_declaration_head(text: str) -> str:
    """Drop a leading ``theorem NAME`` so a statement reads as a goal.

    A query is what a proof search has in its hand: the statement, without the
    name that has not been chosen yet.  Leaving the name in would hand the
    name-search control the answer.
    """
    return _HEAD.sub("", text, count=1)


def identifier_tokens(text: str) -> FrozenSet[str]:
    """The identifiers of a fragment of Lean, lower-cased."""
    return frozenset(token.lower() for token in _IDENT.findall(text))


def name_tokens(name: str) -> FrozenSet[str]:
    """A fully qualified name split into words: dots, underscores, camel case."""
    out = set()
    for part in re.split(r"[._]", name):
        for word in re.findall(r"[A-Z]?[a-z0-9']+|[A-Z]+(?![a-z])", part):
            out.add(word.lower())
    return frozenset(out)


def goal_features(text: str, exclude: Optional[str] = None) -> Tuple[int, ...]:
    """The 24 structural counts of a free-text goal.

    The same map :func:`glm_universal.reasoning.lean_address.features_of`
    applies to a declaration, with the two coordinates a bare goal cannot know
    -- how many results cite it, and how deep its namespace is -- set to zero,
    and its kind read as a theorem.  ``cites`` *is* computable from the text,
    and is computed.  The cost of those unknowns is measured rather than
    assumed: :func:`goal_query_report` scores goal queries against the same
    controls and the gap is in the study.
    """
    decl = la.Declaration(name="?query", kind="theorem", file="", line=0,
                          namespace="", statement=text, body="")
    index = la.citation_index()
    cites = set()
    for token in la._TOKEN.findall(text):
        target = index.get(token)
        if target is None and "." in token:
            target = index.get(token.rsplit(".", 1)[-1])
        if target is not None and target != exclude:
            cites.add(target)
    return la.features_of(decl, len(cites), 0)


def goal_address(text: str, exclude: Optional[str] = None) -> Tuple[int, ...]:
    """Address a free-text goal: one decode, the same quantiser as the book."""
    return la.quantise(goal_features(text, exclude))


# ===========================================================================
#  The lexical projection -- giving the geometry the identifiers
# ===========================================================================

#: The alphabet is folded onto the lattice's 24 coordinates: ``a`` to ``x``
#: keep their own bucket and ``y``, ``z`` join ``a`` and ``b``.  Anything that
#: does not start with a letter -- ``_foo`` -- lands in the last bucket.  The
#: partition is *stated*, so a coordinate can be read back as "how many
#: identifiers beginning with h", which is what distinguishes it from a digest
#: (directive D3).
LEXICAL_BUCKETS = 24

#: No lexical coordinate exceeds this, as for the structural vector.
LEXICAL_CAP = la.CAP


def lexical_bucket(token: str) -> int:
    """Which of the 24 coordinates an identifier contributes to."""
    if not token:
        return LEXICAL_BUCKETS - 1
    head = token[0]
    if "a" <= head <= "z":
        return (ord(head) - ord("a")) % LEXICAL_BUCKETS
    return LEXICAL_BUCKETS - 1


def lexical_vector(text: str) -> Tuple[int, ...]:
    """24 counts of the distinct identifiers of ``text`` by initial letter."""
    counts = [0] * LEXICAL_BUCKETS
    for token in identifier_tokens(text):
        counts[lexical_bucket(token)] += 1
    return tuple(min(LEXICAL_CAP, value) for value in counts)


@memo
def lexical_table() -> Dict[str, Tuple[int, ...]]:
    """Every declaration's lexical vector, read from its statement."""
    return {d.name: lexical_vector(d.statement) for d in la.declarations()}


LEXICAL_PATH = Path(__file__).resolve().parent / "_data" / "lean_lexical_addresses.json"

SCHEMA = 1


def compute_lexical_book() -> Dict[str, object]:
    """Quantise every lexical vector.  Slow: one decode per declaration."""
    table = lexical_table()
    order = [d.name for d in la.declarations()]
    return {
        "schema": SCHEMA,
        "scale": la.SCALE,
        "cap": LEXICAL_CAP,
        "buckets": LEXICAL_BUCKETS,
        "tree_digest": la.tree_digest(),
        "order": order,
        "vectors": {name: list(table[name]) for name in order},
        "addresses": {name: list(la.quantise(table[name])) for name in order},
    }


def write_lexical_book(path: Optional[Path] = None) -> Path:
    """Recompute the lexical address book and store it beside its digest."""
    target = Path(path) if path is not None else LEXICAL_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(compute_lexical_book(), indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    return target


_lexical_cache: Optional[Dict[str, object]] = None


def lexical_book(refresh: bool = False) -> Optional[Dict[str, object]]:
    """The stored lexical address book, or ``None`` if never written."""
    global _lexical_cache
    if _lexical_cache is not None and not refresh:
        return _lexical_cache
    if not LEXICAL_PATH.exists():
        return None
    _lexical_cache = json.loads(LEXICAL_PATH.read_text(encoding="utf-8"))
    return _lexical_cache


def lexical_cache_state() -> Dict[str, object]:
    """Fresh, stale or absent -- the same guard the address book carries."""
    book = lexical_book()
    live = la.tree_digest()
    if book is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    stored = book.get("tree_digest")
    fresh = (stored == live and book.get("schema") == SCHEMA
             and book.get("scale") == la.SCALE)
    return {"present": True, "fresh": fresh, "live_digest": live,
            "stored_digest": stored,
            "verdict": "fresh" if fresh else "stale"}


def lexical_addresses() -> Dict[str, Tuple[int, ...]]:
    """The stored lexical addresses, as tuples; empty if never written."""
    book = lexical_book()
    if book is None:
        return {}
    return {name: tuple(point) for name, point in book["addresses"].items()}


# ===========================================================================
#  The rankers
# ===========================================================================

#: Every scheme scored side by side.  ``address`` is the subject; ``features``
#: and ``lexical`` are the two ablations; the rest are controls.
SCHEMES: Tuple[str, ...] = (
    "address", "features", "lexical", "text", "name", "digest", "shuffled",
    "random")

#: The schemes that read a point of the lattice.
POINT_SCHEMES: Tuple[str, ...] = ("address", "lexical", "digest", "shuffled")


@dataclass(frozen=True)
class Candidate:
    """One retrieved declaration."""

    name: str
    file: str
    score: Fraction          # smaller is nearer for a distance, see ``metric``
    metric: str              # "squared_distance" or "overlap"

    def as_json(self) -> Dict[str, object]:
        return {"name": self.name, "file": self.file,
                "score": str(self.score), "metric": self.metric}


def _point_table(scheme: str) -> Dict[str, Tuple[int, ...]]:
    if scheme == "address":
        return la.addresses("feature")
    if scheme == "digest":
        return la.addresses("hash_control")
    if scheme == "shuffled":
        return la.addresses("shuffled")
    if scheme == "features":
        book = la.address_book()
        return ({name: tuple(book["features"][name]) for name in book["order"]}
                if book else {})
    if scheme == "lexical":
        return lexical_addresses()
    raise ValueError(f"scheme {scheme!r} is not a point scheme")


def rank_by_point(table: Mapping[str, Tuple[int, ...]],
                  point: Sequence[int], k: int,
                  exclude: Optional[str] = None,
                  candidates: Optional[Sequence[str]] = None
                  ) -> Tuple[Candidate, ...]:
    """The ``k`` nearest entries of ``table`` to ``point``.

    Ties are broken by name, in ascending order -- the rule
    ``GLM.Retrieval.Prec`` states and ``ranked_eq_of_perm`` needs, so that the
    answer does not depend on the order the corpus was read in.
    """
    files = file_of()
    names = candidates if candidates is not None else tuple(table)
    scored = []
    for name in names:
        if name == exclude or name not in table:
            continue
        distance = la.squared_distance(point, table[name])
        scored.append((distance, name))
    scored.sort()
    return tuple(Candidate(name=name, file=files.get(name, ""),
                           score=Fraction(distance),
                           metric="squared_distance")
                 for distance, name in scored[:k])


@memo
def statement_tokens() -> Dict[str, FrozenSet[str]]:
    """The identifier tokens of every declaration's statement."""
    return {d.name: identifier_tokens(d.statement) for d in la.declarations()}


def rank_by_text(text: str, k: int, exclude: Optional[str] = None,
                 candidates: Optional[Sequence[str]] = None
                 ) -> Tuple[Candidate, ...]:
    """The strong control: exact Jaccard overlap of identifier tokens."""
    files = file_of()
    query = identifier_tokens(text)
    table = statement_tokens()
    names = candidates if candidates is not None else corpus()
    scored = []
    for name in names:
        if name == exclude:
            continue
        other = table.get(name, frozenset())
        union = len(query | other)
        overlap = Fraction(len(query & other), union) if union else Fraction(0)
        scored.append((-overlap, name))
    scored.sort()
    return tuple(Candidate(name=name, file=files.get(name, ""),
                           score=-overlap, metric="overlap")
                 for overlap, name in scored[:k])


def rank_by_name(text: str, k: int, exclude: Optional[str] = None,
                 candidates: Optional[Sequence[str]] = None
                 ) -> Tuple[Candidate, ...]:
    """Name-substring search: query words found in the candidate's name."""
    files = file_of()
    query = identifier_tokens(text)
    names = candidates if candidates is not None else corpus()
    scored = []
    for name in names:
        if name == exclude:
            continue
        shared = len(query & name_tokens(name))
        scored.append((-shared, name))
    scored.sort()
    return tuple(Candidate(name=name, file=files.get(name, ""),
                           score=Fraction(-shared), metric="overlap")
                 for shared, name in scored[:k])


@memo
def _random_order() -> Tuple[str, ...]:
    names = corpus()
    permutation = integrity.seeded_permutation(len(names),
                                               "glm-retrieval-random-control")
    return tuple(names[i] for i in permutation)


def rank_random(k: int, exclude: Optional[str] = None,
                candidates: Optional[Sequence[str]] = None
                ) -> Tuple[Candidate, ...]:
    """The control that ignores the query: a seeded permutation of the corpus."""
    files = file_of()
    allowed = set(candidates) if candidates is not None else None
    out = []
    for name in _random_order():
        if name == exclude or (allowed is not None and name not in allowed):
            continue
        out.append(Candidate(name=name, file=files.get(name, ""),
                             score=Fraction(0), metric="overlap"))
        if len(out) == k:
            break
    return tuple(out)


def rank(scheme: str, *, text: str = "", point: Optional[Sequence[int]] = None,
         k: int = K_DEFAULT, exclude: Optional[str] = None,
         candidates: Optional[Sequence[str]] = None) -> Tuple[Candidate, ...]:
    """One scheme's ranking, dispatched.

    ``point`` is required for the point schemes and ignored otherwise;
    ``text`` is required for ``text`` and ``name``.
    """
    if scheme in POINT_SCHEMES or scheme == "features":
        if point is None:
            raise ValueError(f"scheme {scheme!r} needs a point")
        return rank_by_point(_point_table(scheme), point, k, exclude,
                             candidates)
    if scheme == "text":
        return rank_by_text(text, k, exclude, candidates)
    if scheme == "name":
        return rank_by_name(text, k, exclude, candidates)
    if scheme == "random":
        return rank_random(k, exclude, candidates)
    raise ValueError(f"unknown scheme {scheme!r}")


# ===========================================================================
#  The functional surface: retrieve
# ===========================================================================

def retrieve(query: str, k: int = K_DEFAULT, scheme: str = "address"
             ) -> Dict[str, object]:
    """Answer a query with the ``k`` nearest declarations.

    ``query`` is either the name of a declaration of the development -- in
    which case its stored address is used and it is excluded from its own
    answer -- or a fragment of Lean, which is addressed live by
    :func:`goal_address`.  The mode is reported, never guessed at silently.
    """
    decl = la.declaration(query)
    if decl is not None and decl.name in set(corpus()):
        mode = "declaration"
        exclude = decl.name
        text = strip_declaration_head(decl.statement)
        point: Optional[Tuple[int, ...]]
        if scheme == "address":
            point = la.addresses("feature").get(decl.name)
        elif scheme == "features":
            book = la.address_book()
            point = tuple(book["features"][decl.name]) if book else None
        elif scheme == "lexical":
            point = lexical_addresses().get(decl.name)
        elif scheme == "digest":
            point = la.addresses("hash_control").get(decl.name)
        elif scheme == "shuffled":
            point = la.addresses("shuffled").get(decl.name)
        else:
            point = None
    else:
        mode = "goal"
        exclude = None
        text = strip_declaration_head(query)
        if scheme == "address":
            point = goal_address(text)
        elif scheme == "features":
            point = goal_features(text)
        elif scheme == "lexical":
            point = la.quantise(lexical_vector(text))
        elif scheme in ("digest", "shuffled"):
            point = la.quantise(la.name_hash_vector(text))
        else:
            point = None
    found = rank(scheme, text=text, point=point, k=k, exclude=exclude)
    return {
        "query": query,
        "mode": mode,
        "scheme": scheme,
        "k": k,
        "point": tuple(point) if point is not None else None,
        "candidates": tuple(c.as_json() for c in found),
        "names": tuple(c.name for c in found),
    }


# ===========================================================================
#  Measurement
# ===========================================================================

#: How many declarations the declaration-query experiment asks about.  Every
#: ``len(corpus) // SAMPLE``-th declaration in the address book's order: a
#: stated stride rather than a random sample, so the set is reproducible
#: without a seed.
SAMPLE = 200

#: The goal-query experiment decodes one address per query, so it asks fewer.
GOAL_SAMPLE = 100


def query_sample(size: int) -> Tuple[str, ...]:
    """A deterministic spread of ``size`` declarations across the corpus."""
    names = corpus()
    if not names:
        return ()
    stride = max(1, len(names) // size)
    chosen = names[::stride]
    return tuple(name for name in chosen if relatives(name))


def _score(found: Sequence[Candidate], relevant: FrozenSet[str], k: int
           ) -> Tuple[int, int, Fraction]:
    """Hit, hits-in-window and reciprocal rank for one ranking."""
    marks = [c.name in relevant for c in found[:k]]
    if not any(marks):
        return 0, 0, Fraction(0)
    return 1, sum(marks), Fraction(1, marks.index(True) + 1)


@memo
def declaration_query_report() -> Dict[str, object]:
    """The experiment: a declaration is the query, its relatives the answer.

    Every scheme is scored on the same queries, at every ``k`` of
    :data:`K_LADDER`, and ``chance`` is computed exactly.  The ablations are
    what make the report worth reading: ``features`` says what the lattice
    contributes over the raw counts, and ``lexical`` says what it would
    contribute if it were given the identifiers instead of the syntax.
    """
    names = query_sample(SAMPLE)
    size = len(corpus())
    top = max(K_LADDER)
    totals = {scheme: {k: {"hit": 0, "found": 0, "rr": Fraction(0)}
                       for k in K_LADDER} for scheme in SCHEMES}
    chance = {k: Fraction(0) for k in K_LADDER}
    decls = {d.name: d for d in la.declarations()}
    for name in names:
        relevant = relatives(name)
        text = strip_declaration_head(decls[name].statement)
        for scheme in SCHEMES:
            if scheme in POINT_SCHEMES or scheme == "features":
                point = _point_table(scheme).get(name)
                if point is None:
                    continue
                found = rank_by_point(_point_table(scheme), point, top, name)
            elif scheme == "text":
                found = rank_by_text(text, top, name)
            elif scheme == "name":
                found = rank_by_name(text, top, name)
            else:
                found = rank_random(top, name)
            for k in K_LADDER:
                hit, hits, rr = _score(found, relevant, k)
                totals[scheme][k]["hit"] += hit
                totals[scheme][k]["found"] += hits
                totals[scheme][k]["rr"] += rr
        for k in K_LADDER:
            chance[k] += chance_hit_rate(len(relevant), size, k)
    count = len(names)
    rows = {}
    for scheme in SCHEMES:
        rows[scheme] = {
            k: {
                "hits": totals[scheme][k]["hit"],
                "hit_rate": Fraction(totals[scheme][k]["hit"], count)
                            if count else Fraction(0),
                "precision": Fraction(totals[scheme][k]["found"], k * count)
                             if count else Fraction(0),
                "mrr": totals[scheme][k]["rr"] / count if count else Fraction(0),
            } for k in K_LADDER
        }
    return {
        "queries": count,
        "corpus": size,
        "k_ladder": K_LADDER,
        "schemes": rows,
        "chance": {k: chance[k] / count if count else Fraction(0)
                   for k in K_LADDER},
        "mean_relatives": (Fraction(sum(len(relatives(n)) for n in names), count)
                           if count else Fraction(0)),
    }


@memo
def goal_query_report() -> Dict[str, object]:
    """The functional case: the query is a bare goal, addressed live.

    The declaration is *not* in the book as far as the query is concerned --
    its address is recomputed from the statement text alone, so the two
    coordinates a goal cannot know (how many results cite it, how deep its
    namespace sits) are zero rather than correct.  What that costs is the
    difference between this table and :func:`declaration_query_report`.
    """
    names = query_sample(GOAL_SAMPLE)
    size = len(corpus())
    top = max(K_LADDER)
    schemes = ("address", "lexical", "text", "name", "digest", "random")
    totals = {scheme: {k: {"hit": 0, "found": 0, "rr": Fraction(0)}
                       for k in K_LADDER} for scheme in schemes}
    decls = {d.name: d for d in la.declarations()}
    reproduced = 0
    book = la.address_book()
    for name in names:
        relevant = relatives(name)
        text = strip_declaration_head(decls[name].statement)
        features = goal_features(text, exclude=name)
        if book is not None and features == tuple(book["features"][name]):
            reproduced += 1
        for scheme in schemes:
            if scheme == "address":
                found = rank_by_point(_point_table("address"),
                                      la.quantise(features), top, name)
            elif scheme == "lexical":
                found = rank_by_point(_point_table("lexical"),
                                      la.quantise(lexical_vector(text)), top,
                                      name)
            elif scheme == "digest":
                found = rank_by_point(_point_table("digest"),
                                      la.quantise(la.name_hash_vector(text)),
                                      top, name)
            elif scheme == "text":
                found = rank_by_text(text, top, name)
            elif scheme == "name":
                found = rank_by_name(text, top, name)
            else:
                found = rank_random(top, name)
            for k in K_LADDER:
                hit, hits, rr = _score(found, relevant, k)
                totals[scheme][k]["hit"] += hit
                totals[scheme][k]["found"] += hits
                totals[scheme][k]["rr"] += rr
    count = len(names)
    rows = {scheme: {k: {
        "hits": totals[scheme][k]["hit"],
        "hit_rate": Fraction(totals[scheme][k]["hit"], count) if count else Fraction(0),
        "precision": Fraction(totals[scheme][k]["found"], k * count) if count else Fraction(0),
        "mrr": totals[scheme][k]["rr"] / count if count else Fraction(0),
    } for k in K_LADDER} for scheme in schemes}
    return {
        "queries": count,
        "corpus": size,
        "schemes": rows,
        "features_reproduced": reproduced,
        "note": "a goal cannot know its citation count or its namespace",
    }


#: The shortlist sizes the hybrid sweep tries.
SHORTLIST_SIZES: Tuple[int, ...] = (50, 100, 200, 400, 800)


@memo
def hybrid_report() -> Dict[str, object]:
    """Does an address shortlist help the lexical search that beats it?

    Prune the corpus to the ``m`` nearest by address, then rank what survives
    by text overlap.  If the pruning were harmless the hit rate would stay at
    the text control's and the search would look at a fraction of the corpus;
    what the numbers show is that every shortlist costs accuracy, so the
    address is not a free filter for this task.
    """
    names = query_sample(SAMPLE)
    decls = {d.name: d for d in la.declarations()}
    table = _point_table("address")
    k = K_DEFAULT
    rows = []
    totals = {m: {"hit": 0, "found": 0} for m in SHORTLIST_SIZES}
    for name in names:
        relevant = relatives(name)
        text = strip_declaration_head(decls[name].statement)
        ranked = rank_by_point(table, table[name], max(SHORTLIST_SIZES), name)
        for m in SHORTLIST_SIZES:
            shortlist = tuple(c.name for c in ranked[:m])
            found = rank_by_text(text, k, name, candidates=shortlist)
            hit, hits, _ = _score(found, relevant, k)
            totals[m]["hit"] += hit
            totals[m]["found"] += hits
    count = len(names)
    size = len(corpus())
    for m in SHORTLIST_SIZES:
        rows.append({
            "shortlist": m,
            "fraction_of_corpus": Fraction(m, size) if size else Fraction(0),
            "hit_rate": Fraction(totals[m]["hit"], count) if count else Fraction(0),
            "precision": Fraction(totals[m]["found"], k * count) if count else Fraction(0),
        })
    text_row = declaration_query_report()["schemes"]["text"][k]
    best = max(rows, key=lambda row: row["hit_rate"]) if rows else None
    return {
        "queries": count,
        "k": k,
        "rows": tuple(rows),
        "text_alone": {"hit_rate": text_row["hit_rate"],
                       "precision": text_row["precision"]},
        "any_shortlist_beats_text": bool(
            best is not None and best["hit_rate"] > text_row["hit_rate"]),
    }


#: The covering radius of the lattice in the integer model, from
#: :data:`glm_universal.reasoning.lean_address.COVERING_RADIUS`.
RHO = la.COVERING_RADIUS


@memo
def shortlist_report() -> Dict[str, object]:
    """The Lean guarantee, checked against the corpus.

    ``GLM.Retrieval.complete_shortlist`` says that if two feature vectors are
    within Euclidean distance ``d`` then their addresses are within
    ``d + 2ρ``.  Squared distances are what the code holds, so the check is
    ``sqrt(address_sq) <= scale * sqrt(feature_sq) + 2ρ``, done in integers by
    squaring both sides only after the cross term is bounded -- here it is done
    exactly by comparing ``address_sq`` against ``(scale * f + 2ρ)²`` with
    ``f`` the integer ceiling of ``sqrt(feature_sq)``, which is an upper bound
    on the true distance and therefore a *stricter* test than the theorem.

    It also measures the practical half: at feature radius ``r`` how large the
    guaranteed-complete address shortlist is, as a fraction of the corpus.
    """
    names = query_sample(50)
    features = _point_table("features")
    addresses = _point_table("address")
    scale = la.SCALE
    checked = 0
    violations = 0
    worst_slack: Optional[int] = None
    for name in names:
        fq, aq = features[name], addresses[name]
        for other in corpus():
            if other == name:
                continue
            fsq = la.squared_distance(fq, features[other])
            asq = la.squared_distance(aq, addresses[other])
            f_ceil = _isqrt_ceil(fsq)
            bound = (scale * f_ceil + 2 * RHO) ** 2
            checked += 1
            if asq > bound:
                violations += 1
            slack = bound - asq
            if worst_slack is None or slack < worst_slack:
                worst_slack = slack
    # the pruning the bound buys, at a feature radius of two counts
    radius = 2
    bound = (scale * radius + 2 * RHO) ** 2
    inside_total = 0
    close_total = 0
    for name in names:
        fq, aq = features[name], addresses[name]
        inside_total += sum(1 for other in corpus() if other != name
                            and la.squared_distance(aq, addresses[other]) <= bound)
        close_total += sum(1 for other in corpus() if other != name
                           and la.squared_distance(fq, features[other]) <= radius ** 2)
    count = len(names)
    size = len(corpus())
    return {
        "queries": count,
        "pairs_checked": checked,
        "violations": violations,
        "bound_holds": violations == 0,
        "worst_slack": worst_slack,
        "feature_radius": radius,
        "address_radius_squared": bound,
        "mean_shortlist": Fraction(inside_total, count) if count else Fraction(0),
        "mean_feature_close": Fraction(close_total, count) if count else Fraction(0),
        "mean_shortlist_fraction": (Fraction(inside_total, count * size)
                                    if count and size else Fraction(0)),
        "covering_radius": RHO,
        "scale": scale,
        "lean_file": "RequestProject/GLM/Retrieval.lean",
    }


def _isqrt_ceil(value: int) -> int:
    """The least integer whose square is at least ``value``."""
    if value <= 0:
        return 0
    root = 1
    while root * root < value:
        root += 1
    return root


def round_to(value: Fraction, denominator: int = 1000) -> Fraction:
    """``value`` rounded to the nearest multiple of ``1/denominator``.

    An exact rational rounded to a *stated* precision, for the sentences the
    runtime speaks: the closed-form chance of a hit has a denominator in the
    tens of quadrillions, and "7.26 times chance" is the readable form of the
    same fact.  Nothing downstream computes with the rounded value; the exact
    one stays in the report beside it.
    """
    scaled = value * denominator
    whole = (scaled.numerator * 2 + scaled.denominator) // (2 * scaled.denominator)
    return Fraction(whole, denominator)


@memo
def retrieval_report() -> Dict[str, object]:
    """The whole study, with the verdict spelled out.

    The verdict is a set of comparisons, not an adjective: which schemes the
    address beats, which beats it, whether the lattice adds anything over the
    raw features, and whether the guarantee holds on the corpus.
    """
    declarations = declaration_query_report()
    goals = goal_query_report()
    hybrid = hybrid_report()
    guarantee = shortlist_report()
    k = K_DEFAULT
    rows = declarations["schemes"]
    address = rows["address"][k]
    verdict = {
        "address_beats_chance": address["hit_rate"] > declarations["chance"][k],
        "address_beats_digest": address["hit_rate"] > rows["digest"][k]["hit_rate"],
        "address_beats_shuffled": address["hit_rate"] > rows["shuffled"][k]["hit_rate"],
        "address_beats_random": address["hit_rate"] > rows["random"][k]["hit_rate"],
        "address_beats_name": address["hit_rate"] > rows["name"][k]["hit_rate"],
        "address_beats_text": address["hit_rate"] > rows["text"][k]["hit_rate"],
        "text_beats_address": rows["text"][k]["hit_rate"] > address["hit_rate"],
        "lattice_matches_raw_features":
            address["hit_rate"] == rows["features"][k]["hit_rate"],
        "lexical_beats_structural":
            rows["lexical"][k]["hit_rate"] > address["hit_rate"],
        "lexical_beats_text":
            rows["lexical"][k]["hit_rate"] > rows["text"][k]["hit_rate"],
        "hybrid_beats_text": hybrid["any_shortlist_beats_text"],
        "guarantee_holds": guarantee["bound_holds"],
    }
    ratio = (address["hit_rate"] / declarations["chance"][k]
             if declarations["chance"][k] else Fraction(0))
    return {
        "cache": la.cache_state(),
        "lexical_cache": lexical_cache_state(),
        "k": k,
        "times_chance_rounded": round_to(ratio, 100),
        "chance_rounded": {kk: round_to(declarations["chance"][kk], 1000)
                           for kk in K_LADDER},
        "declaration_queries": declarations,
        "goal_queries": goals,
        "hybrid": hybrid,
        "guarantee": guarantee,
        "times_chance": ratio,
        "verdict": verdict,
        "lean_file": "RequestProject/GLM/Retrieval.lean",
        "study": "studies/ADDRESS_RETRIEVAL_STUDY.md",
    }
