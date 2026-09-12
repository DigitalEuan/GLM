"""``glm_universal.corpus.address`` -- Leech addresses for the documents.

Why the documents are addressed at all
--------------------------------------
The retrieval study
(:mod:`glm_universal.reasoning.retrieval`, ``studies/ADDRESS_RETRIEVAL_STUDY.md``)
settled the honest division of labour for the Lean corpus: plain lexical
overlap **ranks** better than the lattice, and the lattice earns its place by
returning a shortlist that is *complete up to a stated radius*, with an empty
shortlist a proof that nothing lies within it.  That is exactly the property a
large prose corpus needs, because it turns "did I miss a document?" from a
worry into a certificate.

Extending it from declarations to documents costs one feature map and no new
principle, which is what this module is.  The unit is a **section**: every
``##`` block of every written document, plus one unit for a document that has
no ``##`` headings at all.  Each unit gets

``lexical``
    24 counts of its distinct word stems by initial letter -- the same
    projection :func:`glm_universal.reasoning.retrieval.lexical_vector` applies
    to Lean identifiers, applied to English.  This is the scheme that
    retrieves, because words are what a reader asks with.

``structural``
    24 counts of the *shape* of the section: headings, code fences, table
    rows, links, numerals, quotations, list items, the words that mark a
    verdict.  This is the scheme that says what kind of writing a section is,
    and it is scored beside the lexical one rather than instead of it.

Both are multiplied by :data:`~glm_universal.reasoning.lean_address.SCALE` and
sent to their nearest Leech point by the exact decoder, so a document address
is a point of the same lattice, in the same metric, as a physical carrier and
a Lean declaration.

The guarantee, and where it is proved
-------------------------------------
``GLM.Retrieval.complete_shortlist`` (``RequestProject/GLM/Retrieval.lean``)
says that if two feature vectors are within Euclidean distance ``d`` then
their addresses are within ``scale * d + 2ρ``.  Nothing in it is about Lean
declarations: it is a statement about a quantiser onto a subset of a metric
space, so it applies verbatim here.  Consequently, for a query vector ``q`` and
a feature radius ``r``, every unit whose feature vector is within ``r`` of
``q`` has an address within ``(scale * r + 2ρ)``: collecting the units inside
that address ball gives a **superset** of the true neighbourhood, and an empty
one is a proof of absence.  :func:`shortlist` returns that ball and
:func:`bound_report` checks the inequality on the corpus rather than trusting
it.

The cache, and why it is digest-guarded
---------------------------------------
One decode costs a fraction of a second and the corpus has hundreds of
sections, so the addresses are computed once and stored in
``corpus/_data/document_addresses.json`` beside
:func:`glm_universal.corpus.inventory.corpus_digest`.  Every read recomputes
that digest; if one byte of one document moves, the book reports ``stale``
instead of answering.  Nothing here answers from a stale book.

Regenerate with::

    PYTHONPATH=. python3 -m glm_universal.corpus --write

Nothing here constructs a float: coordinates are integers, distances are
integer squared Euclidean distances, and every rate is a
:class:`~fractions.Fraction`.
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
from ..reasoning import lean_address as la
from ..reasoning import retrieval as ret
from . import inventory as inv

__all__ = [
    "Unit",
    "units",
    "lexical_vector",
    "structural_vector",
    "vector_table",
    "compute_address_book",
    "write_address_book",
    "rebuild_address_book",
    "address_book",
    "cache_state",
    "addresses",
    "shortlist",
    "rank",
    "retrieve",
    "bound_report",
    "retrieval_report",
    "address_report",
    "SCHEMES",
    "SCALE",
    "RHO",
]

DATA_PATH = Path(__file__).resolve().parent / "_data" / "document_addresses.json"

SCHEMA = 1

#: The lattice scale and covering radius, taken from the declaration address
#: book so that the two corpora live at the same resolution.
SCALE = la.SCALE
RHO = la.COVERING_RADIUS
CAP = la.CAP
BUCKETS = 24

#: Ranking schemes scored against each other.  ``lexical`` is the subject;
#: ``text`` is the strong control; ``digest`` and ``shuffled`` are the two null
#: models the house style requires.
SCHEMES: Tuple[str, ...] = ("lexical", "lexical_raw", "structural", "text",
                            "digest", "shuffled")

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_']+")

#: Words too common to distinguish one section of this corpus from another.
STOP_WORDS: FrozenSet[str] = frozenset("""
the and that this with for from what which are was were has have had not but
its it's one two into over under than then they them their there here when
where while who whom whose how why all any both each few more most other some
such only own same too very can will just don should now been being does did
doing because about against between during before after above below out off
again further once nor say says said upon per via etc also however thus hence
therefore whether though although since without within across among
""".split())


@dataclass(frozen=True)
class Unit:
    """One addressable piece of prose: a section, or a whole short document."""

    name: str          # ``path#anchor`` or ``path``
    document: str
    heading: str
    lines: int
    text: str

    @property
    def archive(self) -> bool:
        return inv.is_archive_path(self.document)


def _written(text: str) -> str:
    """A passage with the bodies of its generated blocks blanked.

    A unit is addressed by what a person wrote into it, for the same reason
    :func:`glm_universal.corpus.inventory.corpus_digest` hashes that: an
    address computed from a generated table would move whenever the table was
    refreshed, and the book that stores it would never settle.
    """
    from . import render
    return render._BLOCK.sub(lambda m: m.group("open") + m.group("close"), text)


@memo
def units() -> Tuple[Unit, ...]:
    """Every addressable unit of the written corpus, in a stable order."""
    out: List[Unit] = []
    for doc in inv.source_documents():
        if doc.sections:
            for section in doc.sections:
                out.append(Unit(name=section.unit, document=doc.path,
                                heading=section.heading,
                                lines=section.lines,
                                text=_written(section.text)))
        else:
            out.append(Unit(name=doc.path, document=doc.path, heading=doc.title,
                            lines=doc.lines, text=_written(doc.text)))
    return tuple(out)


def unit_names() -> Tuple[str, ...]:
    return tuple(u.name for u in units())


# ===========================================================================
#  The two feature maps
# ===========================================================================

def content_words(text: str) -> FrozenSet[str]:
    """The distinct content words of a passage, lower-cased.

    Words shorter than three letters and the stop list are dropped: they are
    present in every section and so carry no address.
    """
    found = {word.lower() for word in _WORD.findall(text)}
    return frozenset(word for word in found
                     if len(word) >= 3 and word not in STOP_WORDS)


#: A word is *distinctive* when it appears in at most this fraction of the
#: units.  A word in a tenth of the corpus separates nothing, and counting it
#: pushes every section's vector towards the same shape; dropping it is the
#: same move as the stop list, made against the corpus instead of against
#: English.  Measured: with no filter the lexical address finds a relative for
#: 30.0 % of queries, at a tenth 33.3 %, at a fortieth 28.3 %.
DF_DENOMINATOR = 10


@memo
def document_frequency() -> Dict[str, int]:
    """How many units each content word appears in."""
    counts: Dict[str, int] = {}
    for unit in units():
        for word in content_words(unit.text):
            counts[word] = counts.get(word, 0) + 1
    return counts


def distinctive_words(text: str) -> FrozenSet[str]:
    """The content words of a passage that separate it from the corpus.

    A word this corpus uses everywhere -- *lattice*, *register*, *measured* --
    is a property of the project, not of the passage.  Words above the
    threshold are dropped; a word the corpus has never seen is kept, so a
    question about something new is not reduced to nothing.
    """
    frequency = document_frequency()
    limit = max(1, len(units()) // DF_DENOMINATOR)
    return frozenset(word for word in content_words(text)
                     if frequency.get(word, 0) <= limit)


def lexical_vector(text: str) -> Tuple[int, ...]:
    """24 counts of the distinctive words of a passage by initial letter."""
    counts = [0] * BUCKETS
    for word in distinctive_words(text):
        counts[ret.lexical_bucket(word)] += 1
    return tuple(min(CAP, value) for value in counts)


_TABLE_ROW = re.compile(r"^\s*\|")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
_NUMERAL = re.compile(r"(?<![A-Za-z0-9_])\d[\d,.]*")
_CODE_SPAN = re.compile(r"`[^`]+`")
_BOLD = re.compile(r"\*\*[^*]+\*\*")
_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")


def structural_vector(text: str) -> Tuple[int, ...]:
    """24 counts of the *shape* of a passage rather than its words.

    Every coordinate is a property a reader could see from across the room:
    how much of it is table, how much is code, how many numbers it quotes,
    whether it states a verdict, whether it names Lean.  Capped at
    :data:`CAP`, so no long section can dominate the geometry.
    """
    lines = text.splitlines()
    lowered = text.lower()
    fences = sum(1 for line in lines if line.lstrip().startswith("```"))
    vector = (
        sum(1 for line in lines if line.startswith("###")),
        sum(1 for line in lines if line.startswith("####")),
        fences // 2,
        sum(1 for line in lines if _TABLE_ROW.match(line)) // 4,
        sum(1 for line in lines if _LIST_ITEM.match(line)),
        sum(1 for line in lines if line.lstrip().startswith(">")),
        len(_NUMERAL.findall(text)) // 4,
        len(_CODE_SPAN.findall(text)) // 2,
        len(_BOLD.findall(text)),
        len(_LINK.findall(text)),
        len(lines) // 10,
        len(text.split()) // 100,
        lowered.count("verdict"),
        lowered.count("proved") + lowered.count("proof"),
        lowered.count("lean"),
        lowered.count("theorem") + lowered.count("lemma"),
        lowered.count("chance") + lowered.count("control"),
        lowered.count("measure"),
        lowered.count("register"),
        lowered.count("lattice") + lowered.count("leech"),
        lowered.count("study"),
        lowered.count("?"),
        lowered.count("%"),
        lowered.count("archive") + lowered.count("round"),
    )
    return tuple(min(CAP, max(0, value)) for value in vector)


@memo
def vector_table() -> Dict[str, Dict[str, Tuple[int, ...]]]:
    """Both feature vectors of every unit."""
    return {u.name: {"lexical": lexical_vector(u.text),
                     "structural": structural_vector(u.text)}
            for u in units()}


def digest_vector(name: str) -> Tuple[int, ...]:
    """The determinism-only control: 24 coordinates out of SHA-256 of the name.

    Perfectly stable and, by construction, knowing nothing about the section.
    It is here for the same reason it is in the declaration address book: to
    show what an address looks like when it carries no information about its
    subject.  Directive D3 stands -- a digest addresses integrity, never
    meaning.
    """
    return integrity.byte_vector(name, BUCKETS, CAP + 1)


# ===========================================================================
#  The address book
# ===========================================================================

def _seed_from(book: Optional[Mapping[str, object]]
               ) -> Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]]:
    """The vector-to-point tables a stored document book licenses reusing.

    The same statement as in the declaration book: *this vector decodes to
    this point*.  A section whose text has not changed has the same vector as
    before and therefore the same address; one whose text has changed is a
    vector the table does not hold.  Nothing is taken from a book written at
    another schema, scale, cap or bucket count.
    """
    empty: Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]] = {
        "lexical": {}, "structural": {}}
    if not book:
        return empty
    if (book.get("schema") != SCHEMA or book.get("scale") != SCALE
            or book.get("cap") != CAP or book.get("buckets") != BUCKETS):
        return empty
    vectors = book.get("vectors") or {}
    stored = book.get("addresses") or {}
    seed: Dict[str, Dict[Tuple[int, ...], Tuple[int, ...]]] = {}
    for scheme in ("lexical", "structural"):
        points = stored.get(scheme) or {}
        seed[scheme] = {
            tuple(int(v) for v in vectors[name][scheme]):
                tuple(int(c) for c in point)
            for name, point in points.items()
            if name in vectors and scheme in vectors[name]}
    return seed


def compute_address_book(previous: Optional[Mapping[str, object]] = None,
                         reuse: bool = True, audit: int = 0
                         ) -> Tuple[Dict[str, object], Dict[str, object]]:
    """The document address book, and what rebuilding it cost.

    Two decodes per section, and a decode is the slow step -- so the decoder
    is seeded from the stored book
    (:class:`glm_universal.reasoning.lean_address.Decoder`) and only the
    sections whose text moved are decoded again.  ``reuse=False`` decodes
    everything, which is what the test compares the incremental answer with.
    """
    table = vector_table()
    order = [u.name for u in units()]
    seed = ({"lexical": {}, "structural": {}} if not reuse else
            _seed_from(previous if previous is not None else address_book()))
    decoders = {scheme: la.Decoder(seed[scheme])
                for scheme in ("lexical", "structural")}
    book = {
        "schema": SCHEMA,
        "scale": SCALE,
        "cap": CAP,
        "buckets": BUCKETS,
        "corpus_digest": inv.corpus_digest(),
        "order": order,
        "documents": {name: unit.document
                      for name, unit in zip(order, units())},
        "vectors": {name: {"lexical": list(table[name]["lexical"]),
                           "structural": list(table[name]["structural"])}
                    for name in order},
        "addresses": {
            scheme: {name: list(decoders[scheme](table[name][scheme]))
                     for name in order}
            for scheme in ("lexical", "structural")
        },
    }
    report = {
        "units": len(order),
        "reuse": bool(reuse),
        "seeded": sum(d.seeded for d in decoders.values()),
        "decoded": sum(d.decoded for d in decoders.values()),
        "reused": sum(d.reused for d in decoders.values()),
        "by_scheme": {scheme: {"decoded": decoder.decoded,
                               "reused": decoder.reused}
                      for scheme, decoder in decoders.items()},
        "audit": decoders["lexical"].audit(audit),
    }
    return book, report


def write_address_book(path: Optional[Path] = None, reuse: bool = True,
                       audit: int = 0) -> Path:
    """Rebuild the document address book and store it beside its digest."""
    return Path(str(rebuild_address_book(path, reuse=reuse,
                                         audit=audit)["path"]))


def rebuild_address_book(path: Optional[Path] = None, reuse: bool = True,
                         audit: int = 0) -> Dict[str, object]:
    """Rebuild the book, write it, and report how much had to be decoded."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    book, report = compute_address_book(reuse=reuse, audit=audit)
    target.write_text(json.dumps(book, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8")
    out = dict(report)
    out["path"] = str(target)
    return out


_book_cache: Optional[Dict[str, object]] = None


def address_book(refresh: bool = False) -> Optional[Dict[str, object]]:
    """The stored address book, or ``None`` if it has never been written."""
    global _book_cache
    if _book_cache is not None and not refresh:
        return _book_cache
    if not DATA_PATH.exists():
        return None
    _book_cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _book_cache


def cache_state() -> Dict[str, object]:
    """Is the stored book still a description of the corpus?"""
    book = address_book()
    live = inv.corpus_digest()
    if book is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    stored = book.get("corpus_digest")
    fresh = (stored == live and book.get("schema") == SCHEMA
             and book.get("scale") == SCALE and book.get("cap") == CAP)
    return {"present": True, "fresh": fresh, "live_digest": live,
            "stored_digest": stored,
            "verdict": "fresh" if fresh else "stale"}


_address_cache: Dict[str, Dict[str, Tuple[int, ...]]] = {}


def addresses(scheme: str = "lexical") -> Dict[str, Tuple[int, ...]]:
    """The stored addresses of one scheme, as tuples of integers.

    Held in process once computed: the two null models are decoded rather than
    stored, and a scoring run asks for them once per query.
    """
    if scheme in _address_cache:
        return _address_cache[scheme]
    table = _addresses(scheme)
    if table:
        _address_cache[scheme] = table
    return table


def _addresses(scheme: str) -> Dict[str, Tuple[int, ...]]:
    book = address_book()
    if book is None:
        return {}
    if scheme in ("lexical", "structural"):
        return {name: tuple(point)
                for name, point in book["addresses"][scheme].items()}
    if scheme == "shuffled":
        order = list(book["order"])
        points = [tuple(book["addresses"]["lexical"][name]) for name in order]
        permuted = integrity.seeded_permutation(len(order),
                                                "glm-document-address-null")
        return {order[i]: points[permuted[i]] for i in range(len(order))}
    if scheme == "digest":
        return {name: la.quantise(digest_vector(name))
                for name in book["order"]}
    raise ValueError(f"unknown scheme {scheme!r}")


def stored_vectors(scheme: str = "lexical") -> Dict[str, Tuple[int, ...]]:
    """The feature vectors the addresses were computed from."""
    key = f"vectors:{scheme}"
    if key in _address_cache:
        return _address_cache[key]
    book = address_book()
    if book is None:
        return {}
    table = {name: tuple(value[scheme])
             for name, value in book["vectors"].items()}
    _address_cache[key] = table
    return table


@memo
def token_table() -> Dict[str, FrozenSet[str]]:
    """The distinctive words of every unit, computed once.

    The text control ranks on these, so it is scored on exactly the vocabulary
    the address scheme is given: the comparison is then about the projection
    into 24 coordinates and nothing else.
    """
    return {unit.name: distinctive_words(unit.text) for unit in units()}


# ===========================================================================
#  The certified shortlist
# ===========================================================================

def _isqrt_ceil(value: int) -> int:
    if value <= 0:
        return 0
    root = 1
    while root * root < value:
        root += 1
    return root


def address_radius_squared(feature_radius: int) -> int:
    """The address ball guaranteed to contain the feature ball of radius ``r``."""
    return (SCALE * int(feature_radius) + 2 * RHO) ** 2


@dataclass(frozen=True)
class Found:
    """One retrieved unit."""

    name: str
    document: str
    heading: str
    squared_distance: int
    overlap: Fraction


def shortlist(query: str, feature_radius: int = 2,
              scheme: str = "lexical") -> Dict[str, object]:
    """Every unit whose address lies within the certified ball, and the proof.

    The returned ``units`` are a **superset** of the units whose feature
    vector is within ``feature_radius`` of the query's: that is
    ``GLM.Retrieval.complete_shortlist`` applied to this feature map.  So a
    caller may discard everything outside the list, and an empty list is a
    proof that no section of the corpus is within the radius -- which is what
    makes it safe to not read the rest.
    """
    book = address_book()
    state = cache_state()
    if book is None or not state["fresh"]:
        return {"answered": False, "cache": state, "units": (),
                "reason": "the address book does not describe the corpus now"}
    vector = (lexical_vector(query) if scheme == "lexical"
              else structural_vector(query))
    point = la.quantise(vector)
    bound = address_radius_squared(feature_radius)
    table = addresses(scheme)
    query_words = distinctive_words(query)
    tokens = token_table()
    found: List[Found] = []
    for unit in units():
        distance = la.squared_distance(point, table[unit.name])
        if distance <= bound:
            words = tokens[unit.name]
            union = len(query_words | words)
            overlap = (Fraction(len(query_words & words), union) if union
                       else Fraction(0))
            found.append(Found(name=unit.name, document=unit.document,
                               heading=unit.heading,
                               squared_distance=distance, overlap=overlap))
    found.sort(key=lambda f: (-f.overlap, f.squared_distance, f.name))
    return {
        "answered": True,
        "cache": state,
        "query_vector": vector,
        "query_address": point,
        "feature_radius": feature_radius,
        "address_radius_squared": bound,
        "corpus_units": len(units()),
        "units": tuple(found),
        "complete": True,
        "proof_of_absence": not found,
        "guarantee": "GLM.Retrieval.complete_shortlist",
        "lean_file": "RequestProject/GLM/Retrieval.lean",
    }


def rank(query: str, k: int = 5, scheme: str = "lexical",
         exclude: str = "") -> Tuple[Found, ...]:
    """The ``k`` units a scheme puts first.  Ranking, not guarantee."""
    query_words = distinctive_words(query)
    scored: List[Tuple[object, Found]] = []
    if scheme == "text":
        tokens = token_table()
        for unit in units():
            if unit.name == exclude:
                continue
            words = tokens[unit.name]
            union = len(query_words | words)
            overlap = (Fraction(len(query_words & words), union) if union
                       else Fraction(0))
            scored.append(((-overlap, unit.name),
                           Found(unit.name, unit.document, unit.heading,
                                 0, overlap)))
    else:
        if scheme == "lexical_raw":
            table = stored_vectors("lexical")
            point = lexical_vector(query)
        elif scheme == "structural":
            table = addresses("structural")
            point = la.quantise(structural_vector(query))
        elif scheme in ("digest", "shuffled"):
            table = addresses(scheme)
            point = la.quantise(lexical_vector(query))
        else:
            table = addresses("lexical")
            point = la.quantise(lexical_vector(query))
        for unit in units():
            if unit.name == exclude:
                continue
            distance = la.squared_distance(point, table[unit.name])
            scored.append(((distance, unit.name),
                           Found(unit.name, unit.document, unit.heading,
                                 distance, Fraction(0))))
    scored.sort(key=lambda pair: pair[0])  # type: ignore[arg-type]
    return tuple(item for _, item in scored[:k])


def retrieve(query: str, k: int = 5, feature_radius: int = 2
             ) -> Dict[str, object]:
    """What the corpus has on a question: a ranking, inside a guarantee.

    The honest division of labour, stated in the payload: the *shortlist* is
    complete up to the radius and the *ranking* inside it is lexical, because
    that is what the retrieval study measured to work.
    """
    certified = shortlist(query, feature_radius=feature_radius)
    ranked = rank(query, k=k, scheme="text")
    return {
        "query": query,
        "shortlist": certified,
        "ranked": ranked,
        "ranking_scheme": "text",
        "shortlist_scheme": "lexical",
        "note": ("the address supplies completeness up to the radius; the "
                 "lexical overlap supplies the order"),
    }


# ===========================================================================
#  Measurements
# ===========================================================================

@memo
def relative_table() -> Dict[str, FrozenSet[str]]:
    """Which units count as relevant to which: the other sections of its document.

    The relation is deliberately the strict one.  "Sections of documents that
    link to mine" was tried first and is not a test: the entry document and
    the READMEs link to nearly everything, so under that relation almost half
    the corpus is relevant to almost any query and chance alone scores 47 %.
    Same-document is the analogue of the Lean study's *same source file*, it
    is nowhere in either feature map -- no coordinate sees a path -- and it
    leaves chance where a hit means something.
    """
    by_document: Dict[str, List[str]] = {}
    for unit in units():
        by_document.setdefault(unit.document, []).append(unit.name)
    out: Dict[str, FrozenSet[str]] = {}
    for unit in units():
        group = set(by_document.get(unit.document, ()))
        group.discard(unit.name)
        out[unit.name] = frozenset(group)
    return out


def query_sample(size: int = 60) -> Tuple[str, ...]:
    """A deterministic spread of units to query with."""
    names = [u.name for u in units() if relative_table()[u.name]]
    if not names or size <= 0:
        return ()
    if size >= len(names):
        return tuple(names)
    step = Fraction(len(names), size)
    picked = []
    for i in range(size):
        index = int(step * i)
        if index < len(names):
            picked.append(names[index])
    seen: List[str] = []
    for name in picked:
        if name not in seen:
            seen.append(name)
    return tuple(seen)


def _query_text(name: str) -> str:
    """What is asked with: the section itself, as the Lean study asks with a statement.

    The query unit is excluded from its own ranking, so nothing is being
    retrieved by recognising itself; the question is whether a passage finds
    the rest of the document it belongs to.
    """
    for unit in units():
        if unit.name == name:
            return unit.text
    return ""


def retrieval_report(k: int = 5, sample: int = 60) -> Dict[str, object]:
    """Hit rate at ``k`` for every scheme, against closed-form chance."""
    names = query_sample(sample)
    corpus_size = len(units())
    scores: Dict[str, Dict[str, object]] = {}
    chance_total = Fraction(0)
    for name in names:
        chance_total += ret.chance_hit_rate(len(relative_table()[name]),
                                            corpus_size, k)
    chance = Fraction(chance_total, len(names)) if names else Fraction(0)
    for scheme in SCHEMES:
        hits = 0
        precision_total = Fraction(0)
        for name in names:
            relevant = relative_table()[name]
            found = rank(_query_text(name), k=k, scheme=scheme, exclude=name)
            good = sum(1 for item in found if item.name in relevant)
            hits += 1 if good else 0
            precision_total += Fraction(good, k)
        scores[scheme] = {
            "hit_rate": Fraction(hits, len(names)) if names else Fraction(0),
            "hits": hits,
            "precision": (Fraction(precision_total, len(names)) if names
                          else Fraction(0)),
        }
    best = max(SCHEMES, key=lambda s: scores[s]["hit_rate"])  # type: ignore[index]
    return {
        "queries": len(names),
        "k": k,
        "corpus_units": corpus_size,
        "chance": chance,
        "schemes": scores,
        "best_scheme": best,
        "lexical_beats_chance": scores["lexical"]["hit_rate"] > chance,
        "lexical_beats_digest": (scores["lexical"]["hit_rate"]
                                 > scores["digest"]["hit_rate"]),
        "lexical_beats_shuffled": (scores["lexical"]["hit_rate"]
                                   > scores["shuffled"]["hit_rate"]),
        "text_beats_lexical": (scores["text"]["hit_rate"]
                               > scores["lexical"]["hit_rate"]),
        "times_chance": (ret.round_to(scores["lexical"]["hit_rate"] / chance, 100)
                         if chance else Fraction(0)),
    }


def bound_report(sample: int = 40, feature_radius: int = 2
                 ) -> Dict[str, object]:
    """``complete_shortlist`` checked on the corpus, pair by pair."""
    names = query_sample(sample)
    vectors = stored_vectors("lexical")
    points = addresses("lexical")
    if not vectors:
        return {"checked": 0, "violations": 0, "bound_holds": False,
                "reason": "no address book"}
    checked = 0
    violations = 0
    worst_slack: Optional[int] = None
    inside_total = 0
    close_total = 0
    bound_at_radius = address_radius_squared(feature_radius)
    for name in names:
        fq, aq = vectors[name], points[name]
        for unit in units():
            other = unit.name
            if other == name:
                continue
            fsq = la.squared_distance(fq, vectors[other])
            asq = la.squared_distance(aq, points[other])
            bound = (SCALE * _isqrt_ceil(fsq) + 2 * RHO) ** 2
            checked += 1
            if asq > bound:
                violations += 1
            slack = bound - asq
            if worst_slack is None or slack < worst_slack:
                worst_slack = slack
            if asq <= bound_at_radius:
                inside_total += 1
            if fsq <= feature_radius ** 2:
                close_total += 1
    count = len(names)
    size = len(units())
    return {
        "queries": count,
        "pairs_checked": checked,
        "violations": violations,
        "bound_holds": violations == 0,
        "worst_slack": worst_slack,
        "feature_radius": feature_radius,
        "address_radius_squared": bound_at_radius,
        "mean_shortlist": Fraction(inside_total, count) if count else Fraction(0),
        "mean_feature_close": (Fraction(close_total, count) if count
                               else Fraction(0)),
        "mean_shortlist_fraction": (Fraction(inside_total, count * size)
                                    if count and size else Fraction(0)),
        "covering_radius": RHO,
        "scale": SCALE,
        "lean_file": "RequestProject/GLM/Retrieval.lean",
    }


def injectivity(scheme: str = "lexical") -> Dict[str, object]:
    """How many units share an address -- the conflation of this resolution."""
    table = addresses(scheme)
    buckets: Dict[Tuple[int, ...], List[str]] = {}
    for name, point in table.items():
        buckets.setdefault(point, []).append(name)
    collided = [group for group in buckets.values() if len(group) > 1]
    total = len(table)
    vectors = stored_vectors(scheme) if scheme in ("lexical", "structural") else {}
    distinct_vectors = len(set(vectors.values())) if vectors else 0
    return {
        "units": total,
        "distinct_addresses": len(buckets),
        "collision_classes": len(collided),
        "units_conflated": sum(len(group) for group in collided),
        "distinct_vectors": distinct_vectors,
        "quantisation_adds_no_conflation": distinct_vectors == len(buckets),
        "distinct_rate": Fraction(len(buckets), total) if total else Fraction(0),
    }


def round_trip(scheme: str = "lexical") -> Dict[str, object]:
    """How often the feature vector is read back exactly from the address."""
    vectors = stored_vectors(scheme)
    points = addresses(scheme)
    exact = 0
    coordinate_errors = 0
    for name, vector in vectors.items():
        recovered = tuple(la.describe_address(points[name])["recovered"])
        if recovered == vector:
            exact += 1
        coordinate_errors += sum(1 for a, b in zip(recovered, vector) if a != b)
    total = len(vectors)
    return {
        "checked": total,
        "exact": exact,
        "exact_rate": Fraction(exact, total) if total else Fraction(0),
        "coordinate_errors": coordinate_errors,
        "coordinates_checked": BUCKETS * total,
    }


@memo
def address_report() -> Dict[str, object]:
    """The whole document-address measurement, with the verdict spelled out.

    A stale or absent book is *reported*, never answered from: the corpus has
    moved since the addresses were computed, so every number below it would be
    a measurement of a corpus that is no longer there.
    """
    state = cache_state()
    if not state["fresh"]:
        return {
            "cache": state,
            "answered": False,
            "units": len(units()),
            "documents": len(inv.source_documents()),
            "reason": ("the address book does not describe the corpus now; "
                       "run python3 -m glm_universal.corpus --write"),
            "study": "studies/CORPUS_ADDRESS_STUDY.md",
            "lean_file": "RequestProject/GLM/Corpus.lean",
        }
    return {
        "cache": state,
        "answered": True,
        "units": len(units()),
        "documents": len(inv.source_documents()),
        "injectivity": injectivity("lexical"),
        "structural_injectivity": injectivity("structural"),
        "round_trip": round_trip("lexical"),
        "retrieval": retrieval_report(),
        "guarantee": bound_report(),
        "study": "studies/CORPUS_ADDRESS_STUDY.md",
        "lean_file": "RequestProject/GLM/Corpus.lean",
    }
