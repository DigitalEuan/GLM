"""``glm_universal.runtime.parser`` -- deterministic semantic query parsing.

This module turns a natural-language or symbolic query into a typed
:class:`Query`.  It does so with a fixed grammar and a fixed keyword table --
there is no language model, no embedding, no statistical scoring and no
randomness anywhere in the path.  The same string always parses to the same
:class:`Query`, and every parse decision is recorded in
:attr:`Query.trace` so the choice can be read back rather than guessed at.

How a query is classified
-------------------------
Rules are applied in a fixed priority order and the **first** one that fires
wins.  The rule that fired is named in :attr:`Query.rule`.

1. ``analogy_operator`` -- the string contains ``::``, the proportional
   analogy operator, as in ``force : energy :: pressure : ?``.
2. ``explicit_verb`` -- the string opens with a directive keyword from
   :data:`VERBS`, as in ``describe carbon``.
3. ``equation`` -- the string contains a single top-level ``=`` that is not
   part of ``==``, ``!=``, ``<=`` or ``>=``, as in ``force = mass *
   acceleration``.
4. ``keyword`` -- a keyword from :data:`VERBS` appears anywhere in the token
   stream.
5. ``bare_concept`` -- the whole string resolves to one register concept, in
   which case the intent is taken to be ``describe``.
6. ``unresolved`` -- nothing matched.  The query is returned with kind
   ``"unknown"`` and a list of the nearest known concept names by exact
   integer Levenshtein distance, so the failure is actionable.

Concept resolution
------------------
:class:`ConceptIndex` maps a normalised surface form to a register entry.  It
is built by :class:`~glm_universal.runtime.session.GeometricSession` from the
loaded registers, so the parser itself imports no register and stays cheap.
Aliases are generated deterministically: the object name, its lowercase form,
its spaced form, its chemical symbol, and its full element name.

Invariants
----------
Exact and float-free (this module performs no arithmetic beyond integer
counting and integer edit distance), deterministic, and standard library
only.  Ambiguous surface forms are resolved by a fixed domain priority, never
by a tie-break that depends on dictionary insertion order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..language.descriptions import DESCRIBED_KINDS

__all__ = [
    "QueryError", "QueryKind", "KINDS", "VERBS", "DOMAIN_PRIORITY",
    "Query", "ConceptIndex", "normalise", "tokenise",
    "levenshtein", "split_analogy", "split_equation", "parse_query",
    "DESCRIBED_KINDS",
]


class QueryError(ValueError):
    """Raised when a query is structurally malformed.

    A query that is merely *unrecognised* is not an error: it comes back as a
    :class:`Query` of kind ``"unknown"`` carrying suggestions.  This exception
    is for input that is positively broken -- an analogy with the wrong number
    of terms, an equation with an empty side.
    """


#: The intents the runtime can act on.  ``"unknown"`` is a terminal kind, not
#: a failure mode: it is returned with diagnostics rather than raised.
QueryKind = str

KINDS: Tuple[str, ...] = (
    "verify", "analogy", "describe", "nearest", "product", "cluster",
    "spatial", "project", "trilinear", "coherence", "report", "angle",
    "task", "pi_groups", "meaning", "real", "compare", "measure",
    "comparative", "derive",
    "unknown",
)

#: Directive keyword -> intent.  Longest surface form is matched first, so
#: ``"nearest neighbours"`` cannot be shadowed by ``"nearest"``.
VERBS: Dict[str, str] = {
    # verify
    "verify": "verify", "check": "verify", "audit": "verify",
    "is it true that": "verify", "does it hold that": "verify",
    "dimensionally consistent": "verify", "holds": "verify",
    # analogy
    "analogy": "analogy", "analogous": "analogy", "is to": "analogy",
    # describe
    "describe": "describe", "dossier": "describe", "profile": "describe",
    "what is": "describe", "tell me about": "describe", "explain": "describe",
    "address": "describe",
    # nearest
    "nearest": "nearest", "closest": "nearest", "neighbours": "nearest",
    "neighbors": "nearest", "similar to": "nearest", "rank by distance":
    "nearest",
    # product
    "sakuma": "product", "norton-sakuma": "product", "algebra product":
    "product", "axis product": "product", "2a product": "product",
    "subalgebra": "product",
    # cluster
    "cluster": "cluster", "dendrogram": "cluster", "linkage": "cluster",
    "group together": "cluster",
    # spatial
    "grid": "spatial", "mog grid": "spatial", "facet": "spatial",
    "spatial": "spatial", "layout of": "spatial", "trio": "spatial",
    "sextet": "spatial", "octad": "spatial", "brick": "spatial",
    # project -- walk the dimension-projection layers (v0.5.3)
    "project": "project", "escalate": "project", "layered view": "project",
    "dimension projection": "project",
    # trilinear -- the invariant trilinear form (v0.5.3)
    "trilinear": "trilinear", "threefold": "trilinear",
    # coherence -- the five-shell NRCI (v0.5.3)
    "coherence": "coherence", "nrci": "coherence", "tax": "coherence",
    # report -- on-demand recomputation of facts (v0.5.4)
    "report": "report", "facts": "report", "recompute": "report",
    "census": "report",
    # angle -- exact cosine comparison (v0.5.4)
    "angle": "angle", "angular": "angle", "cosine": "angle",
    # task -- run a worked end-to-end task through the whole pipeline
    "task": "task", "solve task": "task", "puzzle": "task",
    "worked example": "task",
    # pi_groups -- Buckingham-Pi over a set of quantities (v1.0.0)
    "pi groups": "pi_groups", "pi_groups": "pi_groups",
    "buckingham": "pi_groups", "buckingham-pi": "pi_groups",
    "dimensionless groups": "pi_groups", "dimensionless": "pi_groups",
    # meaning -- reference resolution and derived relations (v1.1.0).
    # The operands are raw notations, not register names: the whole point
    # is that a term is looked up by what it denotes, so it must reach the
    # resolver unresolved by any name index.
    # real -- values that are not carriers: irrationals as processes
    # (v1.2.0).  The operand is a notation such as "sqrt(2)", "pi" or
    # "phi", carried through verbatim: it names no register entry, which
    # is the whole point.
    "approximate": "real", "irrational": "real", "real value": "real",
    "to precision": "real",
    # compare -- order two real values, each given as a written expression
    # (v1.2.0).  Inequality between two processes is decidable and is
    # decided; equality is not, and comes back as 'not distinguished'.
    "compare": "compare", "greater than": "compare",
    "bigger than": "compare", "larger than": "compare",
    "less than": "compare", "smaller than": "compare",
    "equal to": "compare", "the same as": "compare",
    "which is bigger": "compare", "which is larger": "compare",
    # measure -- a measure word read against a comparison class (v1.5.0).
    # 'measure hot in tea' answers with a magnitude; 'measure 300 in tea'
    # answers with a word.  The operands are a scale word or a magnitude and
    # a class name, neither of which is a register entry, so they are carried
    # through in options rather than resolved by the name index.
    "measure": "measure", "how much": "measure",
    "relative measure": "measure", "measure word": "measure",
    "how far up": "measure",
    # derive -- one coordinate of one object, answered off the domain
    # descriptions rather than off a hand-written phrase (v1.11.0).
    # 'derive span_ratio of tea' answers; 'derive cents of perfect_fifth'
    # is refused, because no description derives it.  Both operands are
    # carried through unresolved: the coordinate is a description's name for
    # a coordinate, not a register entry.
    "derive": "derive", "derivation of": "derive",
    "coordinate": "derive", "which coordinate": "derive",
    "what derives": "derive",
    "meaning": "meaning", "meaning of": "meaning", "means": "meaning",
    "denotes": "meaning", "denotation": "meaning", "refers to": "meaning",
    "ground": "meaning", "grounding": "meaning", "relate": "meaning",
    "same meaning": "meaning",
}

#: Fixed order used to break a cross-domain name collision.  A surface form
#: that exists in two registers resolves to the earlier domain here, and the
#: collision is reported in :attr:`Query.trace` rather than hidden.
DOMAIN_PRIORITY: Tuple[str, ...] = (
    "physics", "chemistry", "molecules", "mathematics", "spatial",
    "harmonics", "economics", "lexicon",
)

#: Applied to the raw string before tokenising.  Politeness and filler carry
#: no semantics and would otherwise pollute keyword matching.
_FILLER: Tuple[str, ...] = (
    "please", "could you", "can you", "would you", "i want to know",
    "i would like to know", "kindly",
)

#: Generic interrogative openers.  They do carry an intent -- ``"what is X"``
#: is a ``describe`` -- but only when nothing more specific is present.  A
#: query such as ``"what is the nearest 3 to pressure"`` is a ``nearest``
#: query wearing a polite opener, so a weak opener yields to any other verb
#: found later in the string.
_WEAK_OPENERS: Tuple[str, ...] = (
    "what is", "tell me about", "explain", "profile", "address",
)

_TOKEN_RE = re.compile(r"::|[A-Za-z_][A-Za-z0-9_.]*|\d+|\S")
_WORD_RE = re.compile(r"[^a-z0-9]+")


def normalise(text: str) -> str:
    """Fold a surface form to its register-lookup key.

    Lowercases, replaces every run of non-alphanumeric characters with a
    single underscore, and strips leading and trailing underscores.  So
    ``"Speed of Light"``, ``"speed-of-light"`` and ``"speed_of_light"`` all
    normalise to ``"speed_of_light"``.
    """
    return _WORD_RE.sub("_", text.strip().lower()).strip("_")


def tokenise(text: str) -> List[str]:
    """Split a query into identifier, number, operator and ``::`` tokens.

    Identifiers keep internal dots so that a dotted subspace name such as
    ``physics.dimension`` survives as one token.
    """
    return _TOKEN_RE.findall(text)


def levenshtein(a: str, b: str) -> int:
    """Exact integer edit distance, used only to suggest near-miss names.

    Plain dynamic programming over two rows.  Integer throughout -- no
    normalised similarity ratio is computed, because a ratio would be a float
    and this package does not construct floats.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1,
                               current[j - 1] + 1,
                               previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def _strip_filler(text: str) -> str:
    out = text.strip()
    lowered = out.lower()
    changed = True
    while changed:
        changed = False
        for filler in _FILLER:
            if lowered.startswith(filler):
                out = out[len(filler):].lstrip(" ,:")
                lowered = out.lower()
                changed = True
    return out.rstrip("?").strip()


# ===========================================================================
# 1.  THE CONCEPT INDEX
# ===========================================================================

@dataclass(frozen=True)
class ConceptIndex:
    """A deterministic surface-form -> ``(domain, name)`` lookup.

    Parameters
    ----------
    entries
        Normalised alias -> the tuple of ``(domain, name)`` pairs it can mean,
        already sorted by :data:`DOMAIN_PRIORITY` then by name.  A one-element
        tuple is an unambiguous alias.

    Notes
    -----
    The index is built once per session by
    :meth:`~glm_universal.runtime.session.GeometricSession.index` and is
    immutable thereafter, so a lookup never depends on when it is made.
    """

    entries: Mapping[str, Tuple[Tuple[str, str], ...]] = field(
        default_factory=dict)

    @staticmethod
    def build(registers: Mapping[str, Sequence]) -> "ConceptIndex":
        """Index every carrier in ``registers`` under its generated aliases.

        Parameters
        ----------
        registers
            Domain name -> sequence of
            :class:`~glm_universal.data_objects.base.DataObject`.
        """
        staged: Dict[str, List[Tuple[str, str]]] = {}
        for domain in sorted(registers):
            for obj in registers[domain]:
                for alias in _aliases_for(obj):
                    staged.setdefault(alias, [])
                    pair = (domain, obj.name)
                    if pair not in staged[alias]:
                        staged[alias].append(pair)
        rank = {d: i for i, d in enumerate(DOMAIN_PRIORITY)}
        frozen = {
            alias: tuple(sorted(pairs,
                                key=lambda p: (rank.get(p[0], len(rank)), p[1])))
            for alias, pairs in staged.items()
        }
        return ConceptIndex(entries=frozen)

    def lookup(self, surface: str,
               domain: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """Resolve one surface form, or ``None``.

        With ``domain`` given, only that domain's candidates are considered;
        without it, the first candidate under :data:`DOMAIN_PRIORITY` wins.
        """
        candidates = self.entries.get(normalise(surface))
        if not candidates:
            return None
        if domain is None:
            return candidates[0]
        for cand in candidates:
            if cand[0] == domain:
                return cand
        return None

    def candidates(self, surface: str) -> Tuple[Tuple[str, str], ...]:
        """Every ``(domain, name)`` a surface form could mean."""
        return self.entries.get(normalise(surface), ())

    def is_ambiguous(self, surface: str) -> bool:
        """Whether a surface form names carriers in more than one domain."""
        cands = self.candidates(surface)
        return len({d for d, _ in cands}) > 1

    def suggest(self, surface: str, limit: int = 5,
                max_distance: int = 6) -> Tuple[str, ...]:
        """The closest known aliases to an unresolved surface form.

        Ranked by exact integer :func:`levenshtein` distance, then
        alphabetically so the list is stable.  Aliases further than
        ``max_distance`` edits away are dropped rather than padded in.
        """
        key = normalise(surface)
        if not key:
            return ()
        scored = []
        for alias in self.entries:
            d = levenshtein(key, alias)
            if d <= max_distance:
                scored.append((d, alias))
        scored.sort()
        return tuple(alias for _, alias in scored[:limit])

    def size(self) -> int:
        """How many distinct aliases the index holds."""
        return len(self.entries)


def _aliases_for(obj) -> Tuple[str, ...]:
    """Every surface form that should resolve to ``obj``, normalised.

    Generated from the carrier's own name and from the attribute keys the
    registers actually use for human-readable naming -- ``"name"`` for the
    chemical elements (whose carrier name is the symbol), ``"symbol"`` for
    the physical quantities (whose carrier name is already the long form),
    and, for molecules, ``"formula"`` and ``"hill_formula"``.  Nothing is
    invented: an alias exists only if the register supplies it.

    A short physics symbol that collides with an element symbol (``Li``,
    ``Na``, ``Be``, ``B``, ``F``, ``P``, ``S``, ``K``, ``Ar``, etc.) is
    *suppressed* on the physics side.  These one- and two-letter strings
    overwhelmingly mean the element to a human reader, and the existing
    DOMAIN_PRIORITY (physics first) would otherwise resolve ``Li`` to
    ``acoustic_intensity_level`` instead of lithium.  The physics concept
    is still reachable by its long name (``acoustic_intensity_level``)
    and by its symbol within an explicit domain hint.
    """
    out: List[str] = [normalise(obj.name)]
    attrs = getattr(obj, "attributes", {}) or {}
    domain = getattr(obj, "domain", "")
    is_physics = (domain == "physics")
    keys = ("name", "symbol")
    if domain == "molecules":
        # A molecule is named as often by its formula as by its name, and
        # the register supplies both.  Indexing them is what makes
        # ``describe C6H12O6`` reach the carrier rather than only the
        # denotation the reference resolver can build for any formula.
        keys = keys + ("formula", "hill_formula")
    for key in keys:
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            n = normalise(value)
            # Suppress short physics symbols that collide with element
            # symbols.  See _CHEMISTRY_SYMBOLS below for the table.
            if is_physics and len(n) <= 2 and n in _CHEMISTRY_SYMBOLS:
                continue
            out.append(n)
    return tuple(a for a in dict.fromkeys(out) if a)


#: The set of one- and two-letter normalised chemical element symbols.
#: Used by :func:`_aliases_for` to suppress physics symbol aliases that
#: would collide with element symbols.  Built once at import time from
#: the periodic table data; this is the authoritative set of 118 symbols.
_CHEMISTRY_SYMBOLS: frozenset = frozenset({
    "h", "he", "li", "be", "b", "c", "n", "o", "f", "ne",
    "na", "mg", "al", "si", "p", "s", "cl", "ar", "k", "ca",
    "sc", "ti", "v", "cr", "mn", "fe", "co", "ni", "cu", "zn",
    "ga", "ge", "as", "se", "br", "kr", "rb", "sr", "y", "zr",
    "nb", "mo", "tc", "ru", "rh", "pd", "ag", "cd", "in", "sn",
    "sb", "te", "i", "xe", "cs", "ba", "la", "ce", "pr", "nd",
    "pm", "sm", "eu", "gd", "tb", "dy", "ho", "er", "tm", "yb",
    "lu", "hf", "ta", "w", "re", "os", "ir", "pt", "au", "hg",
    "tl", "pb", "bi", "po", "at", "rn", "fr", "ra", "ac", "th",
    "pa", "u", "np", "pu", "am", "cm", "bk", "cf", "es", "fm",
    "md", "no", "lr", "rf", "db", "sg", "bh", "hs", "mt", "ds",
    "rg", "cn", "nh", "fl", "mc", "lv", "ts", "og",
})


# ===========================================================================
# 2.  THE PARSED QUERY
# ===========================================================================

@dataclass(frozen=True)
class Query:
    """A parsed query: what was asked, of which domain, and how we decided.

    Attributes
    ----------
    raw
        The string exactly as supplied.
    normalised
        The string after filler-stripping, which is what the rules saw.
    kind
        One of :data:`KINDS`.
    domain
        The register the query is about, or ``None`` when it is cross-domain
        or undetermined.
    operands
        Kind-specific positional arguments, already resolved to register names
        where the rule could resolve them.  For ``verify`` this is
        ``(lhs_text, rhs_text)``; for ``analogy``, ``(a, b, c)``; for
        ``describe``/``spatial``/``nearest``, ``(name,)``.
    options
        Kind-specific keyword arguments -- ``semantics`` for ``verify``,
        ``subspace`` and ``limit`` for ``analogy`` and ``nearest``, ``k`` for
        ``cluster``.
    rule
        Which classification rule fired.  See the module docstring.
    trace
        Ordered, human-readable record of every parse decision, including
        rejected alternatives and detected ambiguities.
    suggestions
        For kind ``"unknown"``, the nearest known aliases.
    """

    raw: str
    normalised: str
    kind: QueryKind
    domain: Optional[str] = None
    operands: Tuple[str, ...] = ()
    options: Mapping[str, object] = field(default_factory=dict)
    rule: str = "unresolved"
    trace: Tuple[str, ...] = ()
    suggestions: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "raw": self.raw,
            "normalised": self.normalised,
            "kind": self.kind,
            "domain": self.domain,
            "operands": list(self.operands),
            "options": dict(self.options),
            "rule": self.rule,
            "trace": list(self.trace),
            "suggestions": list(self.suggestions),
        }


# ===========================================================================
# 3.  STRUCTURAL SPLITTERS
# ===========================================================================

def split_analogy(text: str) -> Tuple[str, str, str, str]:
    """Split ``A : B :: C : D`` into its four terms.

    The fourth term is returned as written, which is normally ``"?"``.

    Raises
    ------
    QueryError
        If there is not exactly one ``::``, or either half does not hold
        exactly one ``:``.
    """
    halves = text.split("::")
    if len(halves) != 2:
        raise QueryError(
            f"analogy: expected exactly one '::' operator, found "
            f"{len(halves) - 1} in {text!r}")
    left, right = halves
    lterms = [t.strip() for t in left.split(":")]
    rterms = [t.strip() for t in right.split(":")]
    if len(lterms) != 2 or len(rterms) != 2:
        raise QueryError(
            f"analogy: expected 'A : B :: C : ?', got {text!r}")
    if not lterms[0] or not lterms[1] or not rterms[0]:
        raise QueryError(f"analogy: an operand is empty in {text!r}")
    return lterms[0], lterms[1], rterms[0], rterms[1]


def _top_level_equals(text: str) -> List[int]:
    """Positions of ``=`` signs that are not part of a comparison operator."""
    out = []
    for i, ch in enumerate(text):
        if ch != "=":
            continue
        before = text[i - 1] if i else ""
        after = text[i + 1] if i + 1 < len(text) else ""
        if before in "=!<>" or after == "=":
            continue
        out.append(i)
    return out


def split_equation(text: str) -> Tuple[str, str]:
    """Split ``lhs = rhs`` at its single top-level ``=``.

    Raises
    ------
    QueryError
        If there is not exactly one such ``=``, or a side is empty.
    """
    positions = _top_level_equals(text)
    if len(positions) != 1:
        raise QueryError(
            f"equation: expected exactly one top-level '=', found "
            f"{len(positions)} in {text!r}")
    cut = positions[0]
    lhs, rhs = text[:cut].strip(), text[cut + 1:].strip()
    if not lhs or not rhs:
        raise QueryError(f"equation: an empty side in {text!r}")
    return lhs, rhs


# ===========================================================================
# 4.  THE CLASSIFIER
# ===========================================================================

def _verb_hits(lowered: str) -> List[Tuple[int, str, str]]:
    """Every directive keyword present, as ``(position, keyword, kind)``.

    A keyword only counts on a word boundary, so ``"check"`` does not fire
    inside ``"checksum"``.  Longer keywords are considered first, and a hit is
    dropped if it lies inside one already accepted, so ``"nearest
    neighbours"`` cannot also register as ``"nearest"``.
    """
    hits: List[Tuple[int, str, str]] = []
    claimed: List[Tuple[int, int]] = []
    for keyword in sorted(VERBS, key=len, reverse=True):
        start = 0
        while True:
            idx = lowered.find(keyword, start)
            if idx < 0:
                break
            start = idx + 1
            end = idx + len(keyword)
            before_ok = idx == 0 or not (lowered[idx - 1].isalnum()
                                         or lowered[idx - 1] == "_")
            after_ok = end >= len(lowered) or not (lowered[end].isalnum()
                                                   or lowered[end] == "_")
            if not (before_ok and after_ok):
                continue
            if any(a <= idx and end <= b for a, b in claimed):
                continue
            claimed.append((idx, end))
            hits.append((idx, keyword, VERBS[keyword]))
    hits.sort()
    return hits


def _match_verb(lowered: str) -> Optional[Tuple[str, str, bool]]:
    """The governing directive keyword: ``(keyword, kind, at_start)``.

    A keyword at position 0 governs the query -- unless it is one of the
    :data:`_WEAK_OPENERS`, in which case a more specific keyword later in the
    string takes over.  Otherwise the earliest keyword wins.
    """
    hits = _verb_hits(lowered)
    if not hits:
        return None
    idx, keyword, kind = hits[0]
    if keyword in _WEAK_OPENERS:
        for other_idx, other_kw, other_kind in hits[1:]:
            if other_kw not in _WEAK_OPENERS:
                return (other_kw, other_kind, other_idx == 0)
    return (keyword, kind, idx == 0)


def _strip_verb(text: str, keyword: str) -> str:
    lowered = text.lower()
    idx = lowered.find(keyword)
    if idx < 0:
        return text
    return (text[:idx] + text[idx + len(keyword):]).strip(" ,:")


def _extract_int_option(lowered: str, names: Sequence[str]) -> Optional[int]:
    """First integer following any of ``names``, e.g. ``top 5`` -> ``5``."""
    for name in names:
        m = re.search(rf"(?<![a-z0-9_]){re.escape(name)}\s*=?\s*(\d+)", lowered)
        if m:
            return int(m.group(1))
    return None


def _strip_count_phrase(text: str, names: Sequence[str]) -> str:
    """Remove a ``<name> <digits>`` count phrase, and any leading bare count.

    ``"carbon, nitrogen and helium into 2"`` -> ``"carbon, nitrogen and
    helium"``; ``"3 to pressure"`` -> ``"to pressure"``.  Without this the
    count would survive into an operand and fail to resolve against the
    register.
    """
    out = text
    for name in names:
        out = re.sub(rf"(?<![a-z0-9_]){re.escape(name)}\s*=?\s*\d+", " ", out,
                     flags=re.IGNORECASE)
    out = re.sub(r"^\s*\d+\b", " ", out)
    return re.sub(r"\s+", " ", out).strip(" ,:")


def _strip_weak_openers(text: str) -> str:
    """Drop a leading generic interrogative such as ``"what is"``."""
    out = text.strip(" ,:")
    lowered = out.lower()
    for opener in sorted(_WEAK_OPENERS, key=len, reverse=True):
        if lowered.startswith(opener):
            return out[len(opener):].strip(" ,:")
    return out


def _extract_subspace(lowered: str) -> Optional[str]:
    """A dotted subspace name if one is written out, e.g. ``physics.dimension``.

    All three registers that define subspaces are read, ``lexicon`` included:
    ``lexicon.primitives`` is the default an untagged lexicon analogy already
    uses, and it was previously impossible to *ask* for, so a query could not
    request the geometric solve in the one register where the named-relation
    layer answers most often.
    """
    m = re.search(r"(?<![a-z0-9_.])"
                  r"(physics|chemistry|lexicon)\.[a-z_]+", lowered)
    return m.group(0) if m else None


#: How a cluster query may name its linkage rule.  ``single`` merges the two
#: closest clusters (nearest neighbour), ``complete`` the two whose furthest
#: members are closest (furthest neighbour); both are exact.
LINKAGE_PATTERN = re.compile(
    r"(?:(single|complete|furthest|farthest)[-\s]+linkage"
    r"|linkage\s*[=:]?\s*(single|complete|furthest|farthest))",
    re.IGNORECASE)


def _extract_linkage(lowered: str) -> Optional[str]:
    """The linkage rule a cluster query asks for, or ``None`` for the default."""
    match = LINKAGE_PATTERN.search(lowered)
    if match is None:
        return None
    word = (match.group(1) or match.group(2)).lower()
    return "single" if word == "single" else "complete"


def _strip_linkage_phrase(text: str) -> str:
    """Remove the linkage phrase so it is not mistaken for a concept name.

    Case is preserved: a chemical formula such as ``PbCl2`` names no register
    entry, and the molecule formula parser it falls through to reads the
    capitalisation as element symbols.
    """
    cleaned = LINKAGE_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\b(with|using|by|under)\s*$", " ", cleaned.strip(),
                     flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip(" ,;")


def _common_register(surfaces: Sequence[str],
                     index: ConceptIndex) -> Optional[str]:
    """A single register in which every surface form resolves, if there is one.

    Used to rescue a query whose operands were split across registers by
    :data:`DOMAIN_PRIORITY` alone -- ``heat : temperature :: force : ?`` sends
    ``heat`` to the lexicon and ``force`` to physics, yet all three words are
    lexicon concepts.  Registers are tried in domain-priority order, so the
    choice is deterministic; ``None`` means no register holds them all, and
    the query really is cross-domain.
    """
    shared: Optional[set] = None
    for surface in surfaces:
        here = {d for d, _ in index.candidates(surface)}
        if not here:
            return None
        shared = here if shared is None else (shared & here)
        if not shared:
            return None
    if not shared:
        return None
    for domain in DOMAIN_PRIORITY:
        if domain in shared:
            return domain
    return sorted(shared)[0]


def _resolve_operands(surfaces: Sequence[str], index: ConceptIndex,
                      domain: Optional[str],
                      trace: List[str]) -> Tuple[Tuple[str, ...],
                                                 Optional[str]]:
    """Resolve surface forms to register names, inferring the domain.

    Returns the resolved names (unresolved surfaces are passed through
    unchanged, so the solver can report a precise failure) and the domain the
    resolution settled on.
    """
    resolved: List[str] = []
    domains_seen: List[str] = []
    for surface in surfaces:
        hit = index.lookup(surface, domain)
        if hit is None and domain is not None:
            # The hint was wrong for this operand; say so instead of failing
            # silently in the solver.
            loose = index.lookup(surface, None)
            if loose is not None:
                trace.append(
                    f"operand {surface!r} is not in domain {domain!r}; it "
                    f"resolves in {loose[0]!r} -- keeping the hinted domain "
                    f"and leaving the operand unresolved")
        if hit is None:
            resolved.append(surface)
            continue
        if index.is_ambiguous(surface) and domain is None:
            others = [d for d, _ in index.candidates(surface)]
            trace.append(
                f"operand {surface!r} is ambiguous across {others}; "
                f"resolved to {hit[0]!r} by fixed domain priority")
        resolved.append(hit[1])
        domains_seen.append(hit[0])
    settled = domain
    if settled is None and domains_seen:
        unique = sorted(set(domains_seen))
        if len(unique) == 1:
            settled = unique[0]
            trace.append(f"domain inferred as {settled!r} from the operands")
        else:
            # The surface forms landed in different registers only because
            # each was resolved on its own by domain priority.  Before
            # giving up, look for a single register that holds *all* of
            # them: carriers from different registers do not share a
            # coordinate layout, so an answer is only meaningful inside one.
            shared = _common_register(surfaces, index)
            if shared is None:
                trace.append(
                    f"operands span domains {unique} and no single register "
                    f"holds all of them; leaving the query cross-domain")
            else:
                trace.append(
                    f"operands span domains {unique} under domain priority, "
                    f"but all of them also resolve in {shared!r}; the query "
                    f"was coerced to that register")
                resolved = []
                for surface in surfaces:
                    hit = index.lookup(surface, shared)
                    resolved.append(surface if hit is None else hit[1])
                settled = shared
    return tuple(resolved), settled


def parse_query(text: str, index: Optional[ConceptIndex] = None,
                domain: Optional[str] = None) -> Query:
    """Parse one query string into a typed :class:`Query`.

    Parameters
    ----------
    text
        The query.  Natural language, symbolic, or a bare concept name.
    index
        The session's concept index.  Optional: without it the structural
        rules still fire, but no operand is resolved to a register name and
        no suggestion can be offered.
    domain
        A domain hint, normally from the CLI's ``--domain``.  It restricts
        operand resolution rather than overriding the detected intent.

    Returns
    -------
    Query
        Always -- an unrecognised query comes back with kind ``"unknown"``.

    Raises
    ------
    QueryError
        Only for structurally malformed input: a mis-shaped analogy, an
        equation with an empty side, or an empty query.
    """
    if index is None:
        index = ConceptIndex()
    if not text or not text.strip():
        raise QueryError("parse_query: empty query")

    cleaned = _strip_filler(text)
    lowered = cleaned.lower()
    trace: List[str] = [f"normalised to {cleaned!r}"]
    if domain is not None:
        trace.append(f"domain hint {domain!r} supplied")

    # -- rule 1: the analogy operator ---------------------------------------
    # Described, not coded: the shape is an operator with an operand on each
    # side, its inner operator cuts each side again, and the two trailing
    # options are described values rather than option scanners.
    analogy = _described_infix_query(text, cleaned, "analogy", index,
                                     domain, trace)
    if analogy is not None:
        return analogy

    # -- rule 1b: the comparative between two measured uses ------------------
    # Before the directive keywords, because 'larger than' is also an
    # exact-real comparison keyword and the two are told apart by the shape
    # of the operands rather than by the word.  Described as a *nested*
    # shape: the operands are not text but readings, and each side has to
    # match the measure shape itself.
    comparative = _described_nested_query(text, cleaned, "comparative",
                                          domain, trace)
    if comparative is not None:
        return comparative

    # -- rule 2 and 4: directive keywords -----------------------------------
    verb = _match_verb(lowered)
    equals = _top_level_equals(cleaned)

    if verb is not None and verb[2] and verb[1] != "verify":
        # A leading directive that is not 'verify' takes precedence over an
        # '=' later in the line, which in that position is an argument.
        return _build_keyword_query(text, cleaned, lowered, verb, index,
                                    domain, trace, rule="explicit_verb")

    # -- rule 3: an equation ------------------------------------------------
    # Described: the operator is the '=' that no comparison operator touches,
    # the two sides are the operands, the optional verb is the opening, and
    # the semantics qualifier is a described *modifier* -- a word that
    # directs the reading rather than naming a thing.
    if equals:
        equation = _described_infix_query(text, cleaned, "verify", index,
                                          domain, trace)
        if equation is not None:
            return equation

    if verb is not None:
        return _build_keyword_query(text, cleaned, lowered, verb, index,
                                    domain, trace, rule="keyword")

    # -- rule 5: a bare concept name ----------------------------------------
    hit = index.lookup(cleaned, domain)
    if hit is not None:
        trace.append(f"rule 'bare_concept': {cleaned!r} is a "
                     f"{hit[0]} register entry; reading intent as 'describe'")
        return Query(raw=text, normalised=cleaned, kind="describe",
                     domain=hit[0], operands=(hit[1],), rule="bare_concept",
                     trace=tuple(trace))

    # -- rule 6: unresolved -------------------------------------------------
    trace.append("no rule fired")
    return Query(raw=text, normalised=cleaned, kind="unknown", domain=domain,
                 operands=(cleaned,), rule="unresolved", trace=tuple(trace),
                 suggestions=index.suggest(cleaned))


def _described_query(text: str, cleaned: str, kind: str,
                     domain: Optional[str], trace: List[str],
                     rule: str) -> Query:
    """Finish a query whose shape is *described* rather than coded here.

    The three kinds that used to have a branch apiece in
    :func:`_build_keyword_query` come through here.  The matching is
    :func:`glm_universal.language.build.parse`, which knows nothing about
    any kind; this function only decides what the runtime does with the
    outcome, and even that is read off the description:

    * a match becomes a :class:`Query` whose options are the filled slots,
      named for the options they fill;
    * a decline at a boundary the description marks ``raises`` is a
      :class:`QueryError` with the description's own sentence -- which is
      what the ``derive`` branch did with a question naming only one thing;
    * a decline at any other described boundary is answered with the slot
      left empty, which is what the ``measure`` and ``task`` branches did;
    * a question whose opening is buried in undescribed text is *declined*.
      The deleted branches would have answered it with the stray words
      inside an option; that narrowing is the commitment recorded in
      :func:`glm_universal.language.build.narrowing`, with a witness each.
    """
    from ..language.build import Match, parse as described_parse
    from ..language.descriptions import question_by_kind

    spec = question_by_kind(kind)
    outcome = described_parse(cleaned)
    trace.append(f"the {kind!r} question shape is described, not coded: "
                 f"{spec.render()}")
    trace.extend(outcome.trace)
    if isinstance(outcome, Match):
        options: Dict[str, object] = dict(outcome.fills)
        trace.append(f"slots filled off the description: "
                     f"{ {k: v for k, v in options.items()} }")
        return Query(raw=text, normalised=cleaned, kind=outcome.kind,
                     domain=domain, operands=(), options=options,
                     rule=rule, trace=tuple(trace))

    if outcome.boundary == "unrecognised_opening":
        trace.append(
            f"the {kind!r} opening is not at the head of the question and "
            f"the preamble does not describe what precedes it; the surface "
            f"declines rather than reading the leading words into a slot")
        return Query(raw=text, normalised=cleaned, kind="unknown",
                     domain=domain, operands=(cleaned,),
                     rule="undescribed_opening", trace=tuple(trace))

    try:
        described = spec.refusal(outcome.boundary)
    except KeyError:
        described = None
    if described is not None and described.raises:
        raise QueryError(f"parse_query: {text!r} -- {outcome.reason}")
    trace.append(f"declined at {outcome.boundary!r}: {outcome.reason}; the "
                 f"slot is left empty and the solver states the boundary")
    empty: Dict[str, object] = {name: "" for name in spec.options}
    return Query(raw=text, normalised=cleaned, kind=kind,
                 domain=domain, operands=(), options=empty,
                 rule=rule, trace=tuple(trace))


#: Where a described infix kind's operands go, and what domain it settles
#: in.  ``resolve`` means the operands are looked up in the concept index --
#: an analogy's terms name register entries -- and the domain is whatever
#: the lookup settles on; the other two carry their operands through
#: unresolved, because an equation's sides and a comparison's sides are
#: notations read by a grammar rather than names.
_INFIX_DELIVERY: Dict[str, Tuple[str, Optional[str]]] = {
    "analogy": ("resolve", None),
    "verify": ("operands", "physics"),
    "compare": ("options", "mathematics"),
}


def _described_infix_query(text: str, cleaned: str, kind: str,
                           index: ConceptIndex, domain: Optional[str],
                           trace: List[str]) -> Optional[Query]:
    """Read one *infix*-shaped kind off its description, or return ``None``.

    ``None`` means the question holds none of that shape's operators, so the
    rule did not fire and the caller carries on -- the same thing the
    deleted branch's guard did.  A decline at a boundary the description
    marks ``raises`` is a :class:`QueryError` carrying the description's own
    sentence, and a decline at any other described boundary leaves the rule
    unfired, exactly as the branch's structural checks did.

    Nothing here knows what an analogy, an equation or a comparison is: the
    shape says which operator cuts the question, which operands the cut
    produces, which of them the runtime is given, which words may direct the
    reading (a *modifier*) and which values may follow the operands (a
    *trailing option*).  This function only decides where the pieces go.
    """
    from ..language.descriptions import infix_by_kind
    from ..language.infix import InfixMatch, match_infix

    spec = infix_by_kind(kind)
    outcome = match_infix(spec, cleaned)
    if not isinstance(outcome, InfixMatch):
        if outcome.boundary == "no_operator":
            return None
        try:
            described = spec.refusal(outcome.boundary)
        except KeyError:
            described = None
        if described is not None and described.raises:
            raise QueryError(f"parse_query: {text!r} -- {outcome.reason}")
        trace.append(f"the {kind!r} shape declined at "
                     f"{outcome.boundary!r}: {outcome.reason}")
        return None

    trace.append(f"rule {kind + '_shape'!r}: the shape is described, not "
                 f"coded: {spec.render()}")
    trace.extend(outcome.trace)
    delivery, settled_domain = _INFIX_DELIVERY[kind]
    carried = outcome.carried(spec)
    options: Dict[str, object] = dict(outcome.options)
    if delivery == "resolve":
        operands, settled = _resolve_operands(
            tuple(carried[name] for name in spec.carried), index, domain,
            trace)
        return Query(raw=text, normalised=cleaned, kind=kind,
                     domain=settled, operands=operands, options=options,
                     rule=f"{kind}_shape", trace=tuple(trace))
    if delivery == "operands":
        return Query(raw=text, normalised=cleaned, kind=kind,
                     domain=domain or settled_domain,
                     operands=tuple(carried[name] for name in spec.carried),
                     options=options, rule=f"{kind}_shape",
                     trace=tuple(trace))
    options.update(carried)
    return Query(raw=text, normalised=cleaned, kind=kind,
                 domain=settled_domain, operands=(), options=options,
                 rule=f"{kind}_shape", trace=tuple(trace))


def _described_nested_query(text: str, cleaned: str, kind: str,
                            domain: Optional[str],
                            trace: List[str]) -> Optional[Query]:
    """Read a *nested*-shaped kind off its description, or return ``None``.

    A nested shape's operands are themselves shapes, so there are two ways
    for the rule not to fire and they are told apart: the question holds no
    operator of the described form at all, or it holds one and a side is not
    a use of the nested shape.  Both leave the rule unfired -- ``is sqrt(2)
    greater than 7/5`` is the second, and it goes on to be read as an
    exact-real comparison -- and the boundary is written into the trace so
    that the difference is visible rather than inferred.
    """
    from ..language.descriptions import nested_by_kind
    from ..language.nested import NestedMatch, match_nested

    spec = nested_by_kind(kind)
    outcome = match_nested(spec, cleaned)
    if not isinstance(outcome, NestedMatch):
        if outcome.boundary != "no_operator":
            trace.append(f"the {kind!r} shape declined at "
                         f"{outcome.boundary!r}: {outcome.reason}")
        return None
    trace.append(f"rule {kind!r}: the shape is described, not coded: "
                 f"{spec.render()}")
    trace.extend(outcome.trace)
    trace.append("the direction the marker asserts is read off the measure "
                 "register rather than decided here")
    return Query(raw=text, normalised=cleaned, kind=kind,
                 domain=domain or "lexicon", operands=(),
                 options=dict(outcome.options), rule=kind,
                 trace=tuple(trace))


def _build_keyword_query(text: str, cleaned: str, lowered: str,
                         verb: Tuple[str, str, bool], index: ConceptIndex,
                         domain: Optional[str], trace: List[str],
                         rule: str) -> Query:
    """Finish a query classified by a directive keyword.

    Three of the kinds it can produce -- ``derive``, ``measure`` and
    ``task`` -- have no branch here at all: their shapes are described in
    :mod:`glm_universal.language.descriptions` and read by one generic
    matcher.  See :func:`_described_query`.
    """
    keyword, kind, _at_start = verb
    trace.append(f"rule {rule!r}: keyword {keyword!r} -> kind {kind!r}")
    remainder = _strip_weak_openers(_strip_verb(cleaned, keyword))
    options: Dict[str, object] = {}

    if kind == "product":
        labels = [int(t) for t in re.findall(r"(?<![\w.])(\d+)(?![\w.])",
                                             remainder)]
        # 'sakuma 2a product' would otherwise donate its '2'.
        labels = [n for n in labels if n > 2]
        if len(labels) >= 2:
            operands = (str(labels[0]), str(labels[1]))
            trace.append(f"explicit class labels {labels[:2]}")
        elif len(labels) == 1:
            operands = (str(labels[0]),)
            trace.append(f"one seed class {labels[0]}; the partner axis will "
                         f"be the first 2A partner in sorted class order")
        else:
            operands = ()
            trace.append("no class labels given; the solver will use the "
                         "first 2A pair in sorted class order")
        return Query(raw=text, normalised=cleaned, kind=kind,
                     domain="mathematics", operands=operands, options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "cluster":
        k = _extract_int_option(lowered, ("into", "k", "clusters"))
        if k is not None:
            options["k"] = k
            trace.append(f"cluster count k={k}")
        linkage = _extract_linkage(lowered)
        if linkage is not None:
            options["linkage"] = linkage
            trace.append(f"linkage {linkage!r} requested")
        names = _split_list(_strip_linkage_phrase(
            _strip_count_phrase(remainder, ("into", "k", "clusters"))))
        operands, settled = _resolve_operands(names, index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind=kind, domain=settled,
                     operands=operands, options=options, rule=rule,
                     trace=tuple(trace))

    if kind == "nearest":
        limit = _extract_int_option(lowered, ("top", "limit", "nearest"))
        if limit is not None:
            options["limit"] = limit
        subspace = _extract_subspace(lowered)
        if subspace:
            options["subspace"] = subspace
        # Connectives first, so a bare leading count is actually leading.
        target = _strip_connectives(_strip_count_phrase(
            _strip_connectives(remainder), ("top", "limit", "nearest")))
        operands, settled = _resolve_operands((target,), index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind=kind, domain=settled,
                     operands=operands, options=options, rule=rule,
                     trace=tuple(trace))

    if kind == "project":
        # 'project A B' or 'escalate A against B' -- two operands.
        # If the user wrote 'project carbon, oxygen' or 'project carbon
        # and oxygen' that's the comma/and form; if they wrote 'project
        # carbon oxygen' that's the whitespace form.  Try comma/and
        # first, fall back to whitespace split.
        names = _split_list(_strip_connectives(remainder))
        if len(names) < 2:
            # Whitespace fallback: split on whitespace, drop any
            # connectives.
            ws_parts = [p for p in remainder.split()
                        if p.lower() not in _CONNECTIVES
                        and p not in (",", "and", "vs", "versus")]
            if len(ws_parts) >= 2:
                names = tuple(ws_parts[:2])
        if len(names) < 2:
            trace.append("project needs two operands, A and B; "
                         "falling back to describe")
            target = _strip_connectives(remainder)
            operands, settled = _resolve_operands((target,), index,
                                                    domain, trace)
            return Query(raw=text, normalised=cleaned, kind="describe",
                         domain=settled, operands=operands, options=options,
                         rule=rule, trace=tuple(trace))
        operands, settled = _resolve_operands(names[:2], index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind="project",
                     domain=settled, operands=operands, options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "trilinear":
        # 'trilinear A B C' -- three operands.  Same comma/and-first
        # then whitespace-fallback split as 'project'.
        names = _split_list(_strip_connectives(remainder))
        if len(names) < 3:
            ws_parts = [p for p in remainder.split()
                        if p.lower() not in _CONNECTIVES
                        and p not in (",", "and", "vs", "versus")]
            if len(ws_parts) >= 3:
                names = tuple(ws_parts[:3])
        if len(names) < 3:
            trace.append("trilinear needs three operands, A B and C; "
                         "falling back to describe")
            target = _strip_connectives(remainder)
            operands, settled = _resolve_operands((target,), index,
                                                    domain, trace)
            return Query(raw=text, normalised=cleaned, kind="describe",
                         domain=settled, operands=operands, options=options,
                         rule=rule, trace=tuple(trace))
        operands, settled = _resolve_operands(names[:3], index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind="trilinear",
                     domain=settled, operands=operands, options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "report":
        # 'report <subject>' -- the subject names what to recompute.
        # Recognised subjects: relations, leech distribution, theta,
        # subalgebra, trilinear.
        target = _strip_connectives(remainder).lower()
        options["subject"] = target
        return Query(raw=text, normalised=cleaned, kind="report",
                     domain=domain, operands=(), options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "pi_groups":
        # 'pi groups force, mass, acceleration, length, time' -- two or
        # more quantities, comma/and separated or whitespace separated.
        names = _split_list(_strip_connectives(remainder))
        if len(names) < 2:
            ws_parts = [p for p in remainder.split()
                        if p.lower() not in _CONNECTIVES
                        and p not in (",", "and", "vs", "versus")]
            if len(ws_parts) >= 2:
                names = tuple(ws_parts)
        if len(names) < 2:
            trace.append("pi groups needs at least two quantities")
            return Query(raw=text, normalised=cleaned, kind="unknown",
                         domain=domain, operands=(remainder,), rule=rule,
                         trace=tuple(trace),
                         suggestions=index.suggest(remainder))
        operands, settled = _resolve_operands(names, index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind="pi_groups",
                     domain=settled, operands=operands, options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "meaning":
        # 'meaning <term>' or 'relate <term> <term>' -- the operands are
        # notations to be resolved by reference, so they are carried through
        # verbatim in options rather than resolved against the name index.
        names = _split_list(_strip_connectives(remainder))
        if len(names) < 2:
            ws_parts = [p for p in remainder.split()
                        if p.lower() not in _CONNECTIVES
                        and p not in (",", "and", "vs", "versus")]
            if len(ws_parts) >= 2:
                names = tuple(ws_parts[:2])
        if not names:
            names = (_strip_connectives(remainder),)
        options["terms"] = tuple(names[:2])
        trace.append(f"meaning terms {tuple(names[:2])!r} pass to the "
                     f"reference resolver unchanged")
        return Query(raw=text, normalised=cleaned, kind="meaning",
                     domain=domain, operands=(), options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "real":
        # 'approximate sqrt(2) to 20 places' -- the operand is a notation for
        # a real number, not a register name, so it is passed through
        # verbatim.  An optional place count sets the precision.
        places_match = re.search(
            r"(?<![a-z0-9_])(\d+)\s*(?:decimal\s*)?(?:places|digits|dp)\b",
            lowered)
        if places_match:
            options["places"] = int(places_match.group(1))
        target = re.sub(
            r"\bto\s*\d+\s*(?:decimal\s*)?(?:places|digits|dp)\b", " ",
            remainder, flags=re.IGNORECASE)
        target = re.sub(
            r"(?<![a-z0-9_])\d+\s*(?:decimal\s*)?(?:places|digits|dp)\b",
            " ", target, flags=re.IGNORECASE)
        options["notation"] = _strip_connectives(
            re.sub(r"\s+", " ", target)).strip()
        trace.append(f"real notation {options['notation']!r} passes to the "
                     f"exact-real constructor unresolved")
        return Query(raw=text, normalised=cleaned, kind="real",
                     domain="mathematics", operands=(), options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "compare":
        # Two shapes, one kind, and both of them described: the relational
        # form is an infix operator between two notations, and the list form
        # is an opening followed by one slot whose filling is a *list*.
        # Neither is coded here.
        relational = _described_infix_query(text, cleaned, "compare", index,
                                            domain, trace)
        if relational is not None:
            return relational
        return _described_query(text, cleaned, "compare", domain, trace, rule)

    if kind in DESCRIBED_KINDS:
        # 'derive span_ratio of tea', 'measure hot in tea', 'task grid' --
        # three kinds that used to have a hand-written branch each here.
        # They are now read off `glm_universal.language.descriptions`
        # through the one generic matcher: the shape says which words open
        # the question, which words separate its slots, which slots are
        # optional and which boundaries it refuses at, and this function
        # only turns the result into a `Query`.  Nothing here knows what a
        # coordinate, a measure word or a task is.
        return _described_query(text, cleaned, kind, domain, trace, rule)

    if kind == "angle":
        # 'angle A B' -- two operands for the cosine comparison.
        names = _split_list(_strip_connectives(remainder))
        if len(names) < 2:
            ws_parts = [p for p in remainder.split()
                        if p.lower() not in _CONNECTIVES
                        and p not in (",", "and", "vs", "versus")]
            if len(ws_parts) >= 2:
                names = tuple(ws_parts[:2])
        if len(names) < 2:
            trace.append("angle needs two operands, A and B; "
                         "falling back to describe")
            target = _strip_connectives(remainder)
            operands, settled = _resolve_operands((target,), index,
                                                    domain, trace)
            return Query(raw=text, normalised=cleaned, kind="describe",
                         domain=settled, operands=operands, options=options,
                         rule=rule, trace=tuple(trace))
        operands, settled = _resolve_operands(names[:2], index, domain, trace)
        return Query(raw=text, normalised=cleaned, kind="angle",
                     domain=settled, operands=operands, options=options,
                     rule=rule, trace=tuple(trace))

    if kind == "verify":
        # A verify keyword with no '=' in the line: nothing to compare.
        trace.append("verify keyword present but no top-level '=' found")
        return Query(raw=text, normalised=cleaned, kind="unknown",
                     domain=domain, operands=(remainder,), rule=rule,
                     trace=tuple(trace),
                     suggestions=index.suggest(remainder))

    if kind == "analogy":
        trace.append("analogy keyword present but no '::' operator found")
        return Query(raw=text, normalised=cleaned, kind="unknown",
                     domain=domain, operands=(remainder,), rule=rule,
                     trace=tuple(trace),
                     suggestions=index.suggest(remainder))

    # describe and spatial both take one concept
    target = _strip_connectives(remainder)
    operands, settled = _resolve_operands((target,), index, domain, trace)
    return Query(raw=text, normalised=cleaned, kind=kind, domain=settled,
                 operands=operands, options=options, rule=rule,
                 trace=tuple(trace))


_CONNECTIVES = ("the ", "of the ", "of ", "for ", "to ", "a ", "an ")


def _strip_connectives(text: str) -> str:
    out = text.strip(" ,:")
    lowered = out.lower()
    changed = True
    while changed:
        changed = False
        for word in _CONNECTIVES:
            if lowered.startswith(word):
                out = out[len(word):].lstrip()
                lowered = out.lower()
                changed = True
    return out


def _split_list(text: str) -> Tuple[str, ...]:
    """Split a comma- or ``and``-separated operand list."""
    body = _strip_connectives(text)
    parts = re.split(r",|\band\b", body)
    return tuple(p.strip() for p in parts if p.strip())
