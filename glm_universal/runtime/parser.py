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

__all__ = [
    "QueryError", "QueryKind", "KINDS", "VERBS", "DOMAIN_PRIORITY",
    "SEMANTICS_KEYWORDS", "Query", "ConceptIndex", "normalise", "tokenise",
    "levenshtein", "split_analogy", "split_equation", "parse_query",
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
    "spatial", "unknown",
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
}

#: Fixed order used to break a cross-domain name collision.  A surface form
#: that exists in two registers resolves to the earlier domain here, and the
#: collision is reported in :attr:`Query.trace` rather than hidden.
DOMAIN_PRIORITY: Tuple[str, ...] = (
    "physics", "chemistry", "mathematics", "spatial", "lexicon",
)

#: Words that pin the comparison semantics of a ``verify`` query.  The
#: verifier supports two: ``"scalar"`` compares dimension and decimal scale,
#: ``"full"`` additionally compares tensor rank and P/T/C parity.
SEMANTICS_KEYWORDS: Dict[str, str] = {
    "dimensionally": "scalar", "dimensional": "scalar", "units": "scalar",
    "unit": "scalar", "scalar": "scalar", "magnitude": "scalar",
    "tensor": "full", "full": "full", "rank": "full", "parity": "full",
    "vector": "full",
}

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

    Generated from the carrier's own name and from the two attribute keys the
    registers actually use for human-readable naming -- ``"name"`` for the
    chemical elements (whose carrier name is the symbol) and ``"symbol"`` for
    the physical quantities (whose carrier name is already the long form).
    Nothing is invented: an alias exists only if the register supplies it.
    """
    out: List[str] = [normalise(obj.name)]
    attrs = getattr(obj, "attributes", {}) or {}
    for key in ("name", "symbol"):
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            out.append(normalise(value))
    return tuple(a for a in dict.fromkeys(out) if a)


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


def _detect_semantics(lowered: str) -> Tuple[str, str, Optional[str]]:
    """``(semantics, why, matched_word)`` for a verify query.

    Defaults to ``"scalar"``.  An equation typed without qualification is read
    as a statement about dimensions and decimal scale; asking additionally for
    tensor rank and P/T/C parity is the stricter reading and must be requested
    with a word from :data:`SEMANTICS_KEYWORDS`.  The choice is always
    reported, never silent.

    The matched word is returned so the caller can strip it from the
    expression: a qualifier such as ``"tensor"`` in ``"check tensor force =
    ..."`` is a directive about how to compare, not an operand, and leaving it
    in the expression would make the left side an unknown concept.
    """
    for word in sorted(SEMANTICS_KEYWORDS, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", lowered):
            return (SEMANTICS_KEYWORDS[word],
                    f"keyword {word!r} selected {SEMANTICS_KEYWORDS[word]!r} "
                    f"semantics",
                    word)
    return "scalar", ("no semantics keyword present; defaulted to 'scalar' "
                      "(dimension and decimal scale)"), None


def _strip_semantics_qualifier(body: str, word: Optional[str]) -> str:
    """Remove a semantics qualifier used as a directive, not as an operand.

    Only two positions count as directive use: a leading qualifier
    (``"tensor force = ..."``) and a trailing ``"under <word> semantics"``
    phrase.  A qualifier anywhere else is left alone, because there it is
    plausibly part of an expression and silently deleting it would change the
    equation being audited.
    """
    if not word:
        return body
    out = re.sub(rf"\b(under|in|with)\s+{re.escape(word)}\s+semantics\b\s*$",
                 "", body.strip(), flags=re.IGNORECASE)
    out = re.sub(rf"^\s*{re.escape(word)}(\s+semantics)?(?![a-z0-9_])", "",
                 out, flags=re.IGNORECASE)
    return out.strip(" ,:")


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
    """A dotted subspace name if one is written out, e.g. ``physics.dimension``."""
    m = re.search(r"(?<![a-z0-9_.])"
                  r"(physics|chemistry)\.[a-z_]+", lowered)
    return m.group(0) if m else None


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
            trace.append(
                f"operands span domains {unique}; leaving the query "
                f"cross-domain")
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
    if "::" in cleaned:
        a, b, c, _d = split_analogy(cleaned)
        trace.append("rule 'analogy_operator': found '::'")
        operands, settled = _resolve_operands((a, b, c), index, domain, trace)
        subspace = _extract_subspace(lowered)
        options: Dict[str, object] = {}
        if subspace:
            options["subspace"] = subspace
            trace.append(f"explicit subspace {subspace!r}")
        limit = _extract_int_option(lowered, ("top", "limit"))
        if limit is not None:
            options["limit"] = limit
        return Query(raw=text, normalised=cleaned, kind="analogy",
                     domain=settled, operands=operands, options=options,
                     rule="analogy_operator", trace=tuple(trace))

    # -- rule 2 and 4: directive keywords -----------------------------------
    verb = _match_verb(lowered)
    equals = _top_level_equals(cleaned)

    if verb is not None and verb[2] and verb[1] != "verify":
        # A leading directive that is not 'verify' takes precedence over an
        # '=' later in the line, which in that position is an argument.
        return _build_keyword_query(text, cleaned, lowered, verb, index,
                                    domain, trace, rule="explicit_verb")

    # -- rule 3: an equation ------------------------------------------------
    if len(equals) == 1:
        body = cleaned
        if verb is not None and verb[1] == "verify":
            body = _strip_verb(cleaned, verb[0])
            trace.append(f"rule 'equation': stripped directive {verb[0]!r}")
        else:
            trace.append("rule 'equation': single top-level '='")
        semantics, why, word = _detect_semantics(lowered)
        trace.append(why)
        stripped = _strip_semantics_qualifier(body, word)
        if stripped != body.strip(" ,:"):
            trace.append(f"removed the semantics qualifier {word!r} from the "
                         f"expression; it directs the comparison rather than "
                         f"naming a quantity")
            body = stripped
        lhs, rhs = split_equation(body)
        return Query(raw=text, normalised=cleaned, kind="verify",
                     domain=domain or "physics",
                     operands=(lhs, rhs),
                     options={"semantics": semantics},
                     rule="equation", trace=tuple(trace))
    if len(equals) > 1:
        raise QueryError(
            f"parse_query: {len(equals)} top-level '=' signs in {text!r}; "
            f"a chained equality is not a single relation")

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


def _build_keyword_query(text: str, cleaned: str, lowered: str,
                         verb: Tuple[str, str, bool], index: ConceptIndex,
                         domain: Optional[str], trace: List[str],
                         rule: str) -> Query:
    """Finish a query classified by a directive keyword."""
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
        names = _split_list(
            _strip_count_phrase(remainder, ("into", "k", "clusters")))
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
