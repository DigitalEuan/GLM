"""``glm_universal.reasoning.lean_address`` -- Leech addresses for Lean declarations.

The question this module answers
--------------------------------
The formal development under ``RequestProject/GLM/`` has grown to hundreds of
declarations.  Can each one be given a **deterministic Leech address**, so that
the machine can hold a Lean result the same way it holds a physical quantity --
as a point of the 24-dimensional lattice -- and so that "nearby address" means
something?

The answer this module measures is: **yes to determinism, partly to meaning,
and the two are not the same thing.**  An address is a *resolution*, exactly in
the sense of :mod:`glm_universal.reasoning.dimension_layers` and
``RequestProject/GLM/Layers.lean``: it shows whatever its coordinates carry and
conflates everything else.  So the honest report is not "the address means the
declaration" but three measured numbers --

* how many declarations get **distinct** addresses (injectivity),
* how often the feature vector is **read back exactly** from the address
  (round-trip fidelity, i.e. how much the quantiser costs), and
* whether address distance **tracks** anything a reader would call related
  (measured against two null models, not against intuition).

Nothing here is a float.  Coordinates are integers, distances are integers
(squared Euclidean), and rates are exact :class:`~fractions.Fraction`.

How an address is built
-----------------------
Three schemes are computed for every declaration, so that the interesting one
can be scored against controls:

``feature``
    The structural scheme.  A declaration is reduced to the 24 integer counts
    listed in :data:`FEATURE_NAMES` -- how many quantifiers, implications,
    equalities, order relations, big operators; which carrier types it names;
    how long the statement is; how many other declarations of the development
    it cites and how many cite it; how deep its namespace is; what kind of
    declaration it is.  The vector is multiplied by :data:`SCALE` and sent to
    its **nearest Leech point** by the exact decoder in
    :func:`glm_universal.reasoning.analogy.nearest_lattice_point`.  Note what
    is *not* in the vector: the name, the file, the namespace string.  So
    "declarations from one file land near each other" is a prediction the
    scheme can fail, not something built into it.

``hash_control``
    **A control, not an addressing scheme.**  SHA-256 of the fully qualified
    name, twenty four bytes of it reduced to the same coordinate range,
    decoded to the nearest Leech point.  Perfectly deterministic and perfectly
    stable -- and by construction it knows nothing whatever about the
    declaration.  It is computed here for one purpose: to show, in the same
    table and on the same statistics, what an address looks like when it
    carries no information about its subject.  Nothing in the package ever
    addresses anything by digest.  The standing rule, recorded as directive D3
    of ``PROJECT_DIRECTIVES.md``, is: *a digest addresses integrity, never
    meaning; anything that must mean something encodes recoverable information
    about its subject.*

``shuffled``
    The null model that controls for the geometry itself.  It is the multiset
    of ``feature`` addresses re-assigned to declarations by a seeded
    permutation, so it has exactly the same distances available to it and only
    the pairing is destroyed.  Any separation ``feature`` shows over
    ``shuffled`` is separation the features supplied.

Speaking Lean back
------------------
:func:`describe_address` inverts the quantiser: divide by :data:`SCALE`, round
to the nearest integer, and read the coordinates off as the sentence they came
from ("a universally quantified equality over Fin, cited by 4 results").  It
succeeds exactly when the quantisation error stayed below half a scale unit in
every coordinate, and :func:`round_trip_report` counts how often that happens.
That count *is* the fidelity of the claim "the address means the declaration".

The cache, and why it is hash-guarded
-------------------------------------
One nearest-point decode costs about a tenth of a second, and the development
has hundreds of declarations, so the addresses are computed once and stored in
``reasoning/_data/lean_addresses.json`` next to the SHA-256 digest of the Lean
tree they were computed from (:func:`glm_universal.signoff.ledger.tree_digest`).
Every read re-computes that digest.  If a single byte of a single ``.lean``
file changes, the digest changes, and the report says ``stale`` instead of
quietly answering from a cache that no longer describes the sources.  That is
the sign-off discipline of :mod:`glm_universal.signoff` applied to a derived
artefact: *unchanged input plus recorded digest is a licence to reuse; anything
else is recomputed.*

Regenerate with::

    python -m glm_universal.tools lean-address --write

What is proved, and where
-------------------------
``RequestProject/GLM/Address.lean`` carries the part that is a theorem rather
than a measurement: a quantiser onto any subset of a metric space moves a point
by at most the covering radius, so addresses of nearby declarations are nearby
(``GLM.Address.Quantiser.dist_le``); two declarations further apart than
twice the covering radius cannot share an address
(``GLM.Address.Quantiser.ne_of_far``); and -- the part that matters for
"meaning" -- equal features force equal addresses
(``GLM.Address.address_congr``), so the address can carry no distinction the
feature map has already thrown away.  The conflation classes of that map are
exactly the boundary of a layer in the sense of ``Layers.lean``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from .. import integrity
from . import analogy
from . import llvq_table

# ===========================================================================
#  Locating the Lean development
# ===========================================================================

_HERE = Path(__file__).resolve()

#: Candidate locations of the Lean sources, relative to this file.  The first
#: is the overlay's own copy, the second the repository checkout above it.
_LEAN_CANDIDATES = (
    _HERE.parent.parent.parent / "glm_lean" / "RequestProject" / "GLM",
    _HERE.parent.parent.parent.parent / "RequestProject" / "GLM",
)

DATA_PATH = _HERE.parent / "_data" / "lean_addresses.json"

SCHEMA = 1


def lean_root() -> Optional[Path]:
    """The directory holding the Lean development, or ``None``."""
    for candidate in _LEAN_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return None


def lean_files() -> Tuple[Path, ...]:
    """Every ``.lean`` file of the development, in a stable order."""
    root = lean_root()
    if root is None:
        return ()
    return tuple(sorted(root.rglob("*.lean")))


def tree_digest() -> str:
    """SHA-256 over the Lean sources: name and content of every file.

    The same canonical form :mod:`glm_universal.signoff.ledger` uses -- sorted
    relative paths, each followed by the SHA-256 of its bytes -- so a change
    anywhere in the tree changes this string.  The digest itself is computed
    by :mod:`glm_universal.integrity`, one module above the core: directive
    D3 says a digest addresses integrity and never meaning, and the core
    therefore does not hash at all.
    """
    root = lean_root()
    if root is None:
        return "absent"
    return integrity.tree_digest(lean_files(), root)


# ===========================================================================
#  Parsing the sources
# ===========================================================================

_DECL = re.compile(
    r"^(?:@\[[^\]]*\]\s*)?"
    r"(?:(?:private|protected|noncomputable|partial|unsafe|scoped)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|inductive|instance|example)\b"
    r"(?:\s+([^\s:({\[\]]+))?")

_NAMESPACE = re.compile(r"^namespace\s+(\S+)")
_END = re.compile(r"^end\s*(\S*)")

#: Which integer goes in the ``kind`` coordinate.
KIND_CODE = {
    "theorem": 1,
    "lemma": 1,
    "def": 2,
    "abbrev": 2,
    "structure": 3,
    "inductive": 3,
    "instance": 4,
    "example": 5,
}


@dataclass(frozen=True)
class Declaration:
    """One top-level declaration of the Lean development."""

    name: str            # fully qualified, e.g. GLM.Info.Layer.Visible.mono
    kind: str            # theorem | lemma | def | abbrev | structure | ...
    file: str            # path relative to the development root
    line: int            # 1-based line of the declaration keyword
    namespace: str       # the enclosing namespace, possibly ""
    statement: str       # the text between the name and the first ':=' 
    body: str            # everything after that

    @property
    def short(self) -> str:
        """The name without its namespace."""
        return self.name.rsplit(".", 1)[-1] if "." in self.name else self.name


def _split_statement(text: str) -> Tuple[str, str]:
    """Statement and body: everything up to the first top-level ``:=``."""
    depth = 0
    i = 0
    while i < len(text) - 1:
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and ch == ":" and text[i + 1] == "=":
            return text[:i], text[i + 2:]
        i += 1
    return text, ""


def _comment_depth_after(line: str, depth: int) -> int:
    """Block-comment nesting depth at the end of ``line``.

    Lean's block comments ``/- ... -/`` nest, and a documentation comment
    ``/-- ... -/`` is one of them.  A line comment ``--`` outside a block runs
    to the end of the line and cannot open one.
    """
    i = 0
    while i < len(line):
        if depth == 0 and line.startswith("--", i):
            break
        if line.startswith("/-", i):
            depth += 1
            i += 2
            continue
        if depth > 0 and line.startswith("-/", i):
            depth -= 1
            i += 2
            continue
        i += 1
    return depth


def parse_file(path: Path, relative_to: Optional[Path] = None
               ) -> Tuple[Declaration, ...]:
    """Every top-level declaration of one Lean file, in source order.

    A line-based reader, not a Lean parser: a declaration is a line beginning
    at column zero with one of the declaration keywords, and it runs to the
    next such line, the next ``namespace`` or the matching ``end``.  The Lean
    development this package ships is written in exactly that style, and
    :func:`parser_agreement` measures the agreement against the compiler's own
    list rather than assuming it.
    """
    rel = str(path.relative_to(relative_to)) if relative_to else path.name
    lines = path.read_text(encoding="utf-8").splitlines()
    stack: List[str] = []
    out: List[Declaration] = []
    pending: Optional[Tuple[str, str, int, List[str], str]] = None

    def flush() -> None:
        nonlocal pending
        if pending is None:
            return
        kind, name, line, text, ns = pending
        statement, body = _split_statement("\n".join(text))
        out.append(Declaration(name=name, kind=kind, file=rel, line=line,
                               namespace=ns, statement=statement, body=body))
        pending = None

    depth = 0
    for number, line in enumerate(lines, 1):
        in_comment = depth > 0
        depth = _comment_depth_after(line, depth)
        if in_comment:
            # Inside a block comment nothing is a declaration; the text still
            # belongs to whatever declaration is open, if any.
            if pending is not None:
                pending[3].append(line)
            continue
        match = _DECL.match(line)
        if match:
            flush()
            short = match.group(2) or f"_example_{number}"
            ns = ".".join(stack)
            full = f"{ns}.{short}" if ns else short
            pending = (match.group(1), full, number, [line], ns)
            continue
        if line.startswith("namespace "):
            flush()
            stack.append(_NAMESPACE.match(line).group(1))
            continue
        if line.startswith("end"):
            closing = _END.match(line)
            if closing and stack and closing.group(1) == stack[-1]:
                flush()
                stack.pop()
                continue
        if pending is not None:
            pending[3].append(line)
    flush()
    return tuple(out)


_declaration_cache: Optional[Tuple[Declaration, ...]] = None


def declarations(refresh: bool = False) -> Tuple[Declaration, ...]:
    """Every declaration of the development, ordered by file then line."""
    global _declaration_cache
    if _declaration_cache is not None and not refresh:
        return _declaration_cache
    root = lean_root()
    if root is None:
        _declaration_cache = ()
        return _declaration_cache
    out: List[Declaration] = []
    for path in lean_files():
        out.extend(parse_file(path, relative_to=root))
    _declaration_cache = tuple(out)
    return _declaration_cache


def declaration(name: str) -> Optional[Declaration]:
    """Look a declaration up by full name, or by short name if unambiguous."""
    table = {d.name: d for d in declarations()}
    if name in table:
        return table[name]
    hits = [d for d in declarations() if d.short == name or d.name.endswith("." + name)]
    if len(hits) == 1:
        return hits[0]
    return None


# ===========================================================================
#  The feature map
# ===========================================================================

#: The 24 coordinates, in order.  Each is a small non-negative integer, capped
#: at :data:`CAP` so that no single declaration can dominate the geometry.
FEATURE_NAMES: Tuple[str, ...] = (
    "forall", "exists", "implication", "iff", "conjunction", "disjunction",
    "negation", "equality", "order", "divisibility", "big_operator",
    "numeral", "binder", "nat", "int", "rat_real", "fin", "collection",
    "prop_bool", "statement_size", "cites", "cited_by", "namespace_depth",
    "kind",
)

assert len(FEATURE_NAMES) == 24

#: No coordinate exceeds this before scaling.
CAP = 12

#: The feature vector is multiplied by this before being decoded.  Nine, and
#: not the obvious eight, for two measured reasons that :func:`scale_sweep`
#: reproduces:
#:
#: * **Lossless.**  The covering radius of the lattice in this integer model is
#:   :data:`COVERING_RADIUS` ``= 4``, so quantising moves no coordinate by more
#:   than 4; any scale of 8 or more therefore keeps every coordinate inside
#:   half a step and the feature vector is recovered exactly.  Below that it is
#:   not: at scale 4 the default :func:`scale_sweep` sample loses about half
#:   of its declarations on the way back.
#: * **Not degenerate.**  ``8 Z^24`` is *contained* in the lattice, so at scale
#:   8 every scaled feature vector is already a lattice point and the decoder
#:   does nothing at all -- the "Leech address" would be a relabelled cube.  At
#:   scale 9 every point moves, so the address really is a lattice point chosen
#:   by the decoder, in the same space and the same metric as the package's
#:   physical carriers.
#:
#: Nine is the smallest scale that is both.
SCALE = 9

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_.'!?]*")
_NUMERAL = re.compile(r"(?<![A-Za-z0-9_])\d+")


def _count(text: str, *needles: str) -> int:
    return sum(text.count(n) for n in needles)


def _statement_equalities(text: str) -> int:
    """``=`` signs that are genuine equalities, not part of another token."""
    total = 0
    for i, ch in enumerate(text):
        if ch != "=":
            continue
        before = text[i - 1] if i else " "
        after = text[i + 1] if i + 1 < len(text) else " "
        if before in ":=<>!≤≥" or after in "=>":
            continue
        total += 1
    return total


def _cited_names(decl: Declaration, index: Mapping[str, str]) -> frozenset:
    """Which other declarations of the development this one names.

    ``index`` maps every short name and every full name to a full name.  A
    token counts as a citation when it resolves through that index to a
    declaration other than this one.
    """
    text = decl.statement + "\n" + decl.body
    found = set()
    for token in _TOKEN.findall(text):
        target = index.get(token)
        if target is None and "." in token:
            target = index.get(token.rsplit(".", 1)[-1])
        if target is not None and target != decl.name:
            found.add(target)
    return frozenset(found)


def citation_index() -> Dict[str, str]:
    """Short and full names to full names; ambiguous short names are dropped."""
    full = {d.name for d in declarations()}
    short_counts: Dict[str, int] = {}
    for d in declarations():
        short_counts[d.short] = short_counts.get(d.short, 0) + 1
    index: Dict[str, str] = {name: name for name in full}
    for d in declarations():
        if short_counts[d.short] == 1:
            index.setdefault(d.short, d.name)
        # the namespace-qualified tail is unambiguous when the full name is
        tail = d.name.split(".")
        if len(tail) >= 2:
            index.setdefault(".".join(tail[-2:]), d.name)
    return index


@memo
def citation_graph() -> Dict[str, frozenset]:
    """For every declaration, the set of development declarations it names."""
    index = citation_index()
    return {d.name: _cited_names(d, index) for d in declarations()}


def _clamp(value: int) -> int:
    return CAP if value > CAP else (0 if value < 0 else value)


def features_of(decl: Declaration, cites: int = 0, cited_by: int = 0
                ) -> Tuple[int, ...]:
    """The 24 structural counts of one declaration.

    Only the *statement* supplies the syntactic counts: a proof is a route to a
    result, not the result, and two proofs of one theorem should address the
    same point.  The two citation counts come from the whole development and
    are supplied by the caller, which has the graph.
    """
    s = decl.statement
    vector = (
        _count(s, "∀"),
        _count(s, "∃"),
        _count(s, "→", "->"),
        _count(s, "↔", "<->"),
        _count(s, "∧"),
        _count(s, "∨"),
        _count(s, "¬", "≠"),
        _statement_equalities(s),
        _count(s, "≤", "≥", "<", ">") - _count(s, "<->", "->"),
        _count(s, "∣", "%"),
        _count(s, "∑", "∏"),
        len(_NUMERAL.findall(s)),
        s.count("("),
        _count(s, "ℕ", "Nat"),
        _count(s, "ℤ", "Int"),
        _count(s, "ℚ", "ℝ", "Rat", "Real"),
        _count(s, "Fin "),
        _count(s, "Finset", "Set ", "List", "Multiset"),
        _count(s, "Prop", "Bool", "Decidable"),
        len(s.split()) // 4,
        cites,
        cited_by,
        decl.namespace.count(".") + (1 if decl.namespace else 0),
        KIND_CODE.get(decl.kind, 6),
    )
    return tuple(_clamp(v) for v in vector)


@memo
def feature_table() -> Dict[str, Tuple[int, ...]]:
    """Every declaration's feature vector, citation counts included."""
    graph = citation_graph()
    fan_out: Dict[str, int] = {name: 0 for name in graph}
    for source, targets in graph.items():
        for target in targets:
            fan_out[target] = fan_out.get(target, 0) + 1
    return {d.name: features_of(d, len(graph[d.name]), fan_out[d.name])
            for d in declarations()}


# ===========================================================================
#  Quantising to the lattice
# ===========================================================================

def quantise(vector: Sequence[int]) -> Tuple[int, ...]:
    """The nearest Leech point to ``SCALE`` times a feature vector.

    Decoded through the LLVQ class table
    (:func:`glm_universal.reasoning.llvq_table.nearest_lattice_point_table`),
    which is the same objective the 4,096-word scan in
    :func:`glm_universal.reasoning.analogy.nearest_lattice_point` minimises,
    with the scan replaced by 128 class minima and a bound.  The scan is kept
    as the thing to agree with rather than deleted:
    :func:`glm_universal.reasoning.llvq_table.corpus_report` decodes the whole
    corpus both ways and requires every address to be unchanged, and
    ``tests/test_llvq_table.py`` fails if one moves.
    """
    scaled = [Fraction(int(v) * SCALE) for v in vector]
    return tuple(int(c) for c in
                 llvq_table.nearest_lattice_point_table(scaled).point)


def name_hash_vector(name: str) -> Tuple[int, ...]:
    """The determinism-only control: 24 coordinates out of SHA-256.

    The bytes are reduced modulo ``CAP + 1`` so that the control lives in the
    same box as the feature vectors and the comparison is about *what the
    coordinates know*, not about their size.
    """
    return integrity.byte_vector(name, 24, CAP + 1)


def squared_distance(a: Sequence[int], b: Sequence[int]) -> int:
    """Squared Euclidean distance -- an integer, since both are integer points."""
    return sum((int(x) - int(y)) ** 2 for x, y in zip(a, b))


def describe_address(point: Sequence[int]) -> Dict[str, object]:
    """Read a lattice point back as the sentence it was made from.

    Divides by :data:`SCALE`, rounds each coordinate to the nearest integer and
    names the result.  ``exact`` records whether every coordinate landed within
    half a scale unit, which is the condition under which the read-back is the
    original feature vector.
    """
    recovered = []
    residuals = []
    for value in point:
        magnitude = abs(int(value))
        # nearest integer to |value|/SCALE, ties away from zero, then signed:
        # integer floor division rounds towards minus infinity, so the sign is
        # taken out before dividing and put back afterwards
        q = (2 * magnitude + SCALE) // (2 * SCALE)
        if int(value) < 0:
            q = -q
        recovered.append(q)
        residuals.append(int(value) - q * SCALE)
    exact = all(abs(r) * 2 <= SCALE for r in residuals)
    return {
        "recovered": tuple(recovered),
        "residuals": tuple(residuals),
        "max_residual": max((abs(r) for r in residuals), default=0),
        "within_half_step": exact,
        "reading": {name: value
                    for name, value in zip(FEATURE_NAMES, recovered)},
    }


def sentence(features: Sequence[int]) -> str:
    """A one-line English reading of a feature vector.

    This is the "speaking Lean" surface: what the machine can say about a
    declaration knowing only its address.
    """
    f = dict(zip(FEATURE_NAMES, (int(v) for v in features)))
    kinds = {1: "a theorem", 2: "a definition", 3: "a structure",
             4: "an instance", 5: "an example"}
    parts = [kinds.get(f["kind"], "a declaration")]
    if f["forall"]:
        parts.append(f"universally quantified ({f['forall']}x)")
    if f["exists"]:
        parts.append(f"with {f['exists']} existential(s)")
    shape = []
    if f["iff"]:
        shape.append("a biconditional")
    if f["equality"]:
        shape.append(f"{f['equality']} equality/-ies")
    if f["order"]:
        shape.append(f"{f['order']} order relation(s)")
    if f["divisibility"]:
        shape.append("a divisibility")
    if shape:
        parts.append("stating " + ", ".join(shape))
    carriers = [label for key, label in
                (("nat", "N"), ("int", "Z"), ("rat_real", "Q/R"),
                 ("fin", "Fin"), ("collection", "a collection"),
                 ("prop_bool", "Prop/Bool"))
                if f[key]]
    if carriers:
        parts.append("over " + ", ".join(carriers))
    if f["big_operator"]:
        parts.append("with a big operator")
    parts.append(f"citing {f['cites']} and cited by {f['cited_by']}")
    return ", ".join(parts)


# ===========================================================================
#  The stored address book
# ===========================================================================

def compute_address_book() -> Dict[str, object]:
    """Compute every address from the sources.  Slow: one decode each."""
    table = feature_table()
    order = [d.name for d in declarations()]
    meta = {d.name: {"kind": d.kind, "file": d.file, "line": d.line}
            for d in declarations()}
    feature_addresses = {}
    hash_addresses = {}
    for name in order:
        feature_addresses[name] = list(quantise(table[name]))
        hash_addresses[name] = list(quantise(name_hash_vector(name)))
    return {
        "schema": SCHEMA,
        "scale": SCALE,
        "cap": CAP,
        "tree_digest": tree_digest(),
        "order": order,
        "declarations": meta,
        "features": {name: list(table[name]) for name in order},
        "addresses": {
            "feature": feature_addresses,
            "hash_control": hash_addresses,
        },
    }


def write_address_book(path: Optional[Path] = None) -> Path:
    """Recompute the address book and store it beside its tree digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    book = compute_address_book()
    target.write_text(json.dumps(book, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8")
    return target


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
    """Is the stored address book still a description of the sources?

    This is the sign-off test in miniature: the digest recorded when the book
    was written, the digest of the tree now, and a verdict.
    """
    book = address_book()
    live = tree_digest()
    if book is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    stored = book.get("tree_digest")
    fresh = (stored == live and book.get("schema") == SCHEMA
             and book.get("scale") == SCALE and book.get("cap") == CAP)
    return {"present": True, "fresh": fresh, "live_digest": live,
            "stored_digest": stored,
            "verdict": "fresh" if fresh else "stale"}


def addresses(scheme: str = "feature") -> Dict[str, Tuple[int, ...]]:
    """The stored addresses of one scheme, as tuples.

    ``shuffled`` is derived here rather than stored: it is the ``feature``
    addresses re-assigned by a deterministic permutation.
    """
    book = address_book()
    if book is None:
        return {}
    if scheme in ("feature", "hash_control"):
        return {name: tuple(point)
                for name, point in book["addresses"][scheme].items()}
    if scheme == "shuffled":
        order = list(book["order"])
        points = [tuple(book["addresses"]["feature"][name]) for name in order]
        permuted = _seeded_permutation(len(order))
        return {order[i]: points[permuted[i]] for i in range(len(order))}
    raise ValueError(f"unknown scheme {scheme!r}")


SCHEMES = ("feature", "hash_control", "shuffled")


def _seeded_permutation(n: int) -> List[int]:
    """A deterministic permutation of ``range(n)`` -- the null model.

    Supplied by :mod:`glm_universal.integrity`, because a shuffle needs a
    reproducible pseudo-random stream and the core computes no digests.  The
    permutation carries no information about the declarations it reorders;
    that is exactly its purpose.
    """
    return integrity.seeded_permutation(n, "glm-lean-address-null")


# ===========================================================================
#  Measurements
# ===========================================================================

def injectivity(scheme: str = "feature") -> Dict[str, object]:
    """How many declarations share an address -- the conflation of the layer."""
    table = addresses(scheme)
    buckets: Dict[Tuple[int, ...], List[str]] = {}
    for name, point in table.items():
        buckets.setdefault(point, []).append(name)
    classes = sorted(buckets.values(), key=lambda names: (-len(names), names[0]))
    collided = [names for names in classes if len(names) > 1]
    conflated = sum(len(names) for names in collided)
    total = len(table)
    book = address_book()
    distinct_features = (
        len({tuple(book["features"][name]) for name in table})
        if book is not None else 0)
    return {
        "declarations": total,
        "distinct_feature_vectors": distinct_features,
        "quantisation_adds_no_conflation": distinct_features == len(buckets),
        "distinct_addresses": len(buckets),
        "collision_classes": len(collided),
        "declarations_conflated": conflated,
        "injective": not collided,
        "distinct_rate": Fraction(len(buckets), total) if total else Fraction(0),
        "largest_class_size": len(classes[0]) if classes else 0,
        "largest_class": tuple(classes[0]) if classes else (),
    }


def round_trip_report(scheme: str = "feature") -> Dict[str, object]:
    """How often the feature vector survives the trip to the lattice and back."""
    book = address_book()
    if book is None:
        return {"checked": 0, "exact": 0, "exact_rate": Fraction(0)}
    table = addresses(scheme)
    exact = 0
    worst = 0
    worst_name = ""
    coordinate_errors = 0
    for name, point in table.items():
        original = tuple(book["features"][name])
        reading = describe_address(point)
        if reading["recovered"] == original:
            exact += 1
        errors = sum(1 for a, b in zip(reading["recovered"], original) if a != b)
        coordinate_errors += errors
        if errors > worst:
            worst, worst_name = errors, name
    total = len(table)
    return {
        "checked": total,
        "exact": exact,
        "exact_rate": Fraction(exact, total) if total else Fraction(0),
        "coordinate_errors": coordinate_errors,
        "coordinates_checked": 24 * total,
        "worst_declaration": worst_name,
        "worst_coordinate_errors": worst,
    }


def _pair_statistics(scheme: str) -> Dict[str, object]:
    """Mean squared address distance, same file against different file."""
    book = address_book()
    table = addresses(scheme)
    names = [n for n in book["order"] if n in table] if book else []
    files = {n: book["declarations"][n]["file"] for n in names} if book else {}
    same_total = same_count = 0
    cross_total = cross_count = 0
    for i, a in enumerate(names):
        pa = table[a]
        fa = files[a]
        for b in names[i + 1:]:
            distance = squared_distance(pa, table[b])
            if files[b] == fa:
                same_total += distance
                same_count += 1
            else:
                cross_total += distance
                cross_count += 1
    same_mean = Fraction(same_total, same_count) if same_count else Fraction(0)
    cross_mean = Fraction(cross_total, cross_count) if cross_count else Fraction(0)
    return {
        "same_file_pairs": same_count,
        "cross_file_pairs": cross_count,
        "same_file_mean_squared_distance": same_mean,
        "cross_file_mean_squared_distance": cross_mean,
        "ratio": (same_mean / cross_mean) if cross_mean else Fraction(0),
    }


def _neighbour_statistics(scheme: str) -> Dict[str, object]:
    """For each declaration, is its nearest neighbour by address a relative?

    "Relative" is read two ways, neither of them baked into the feature map:
    same source file, and cited-or-citing.  Ties are counted as a hit only if
    *every* tied nearest neighbour is a relative, so the statistic cannot be
    inflated by a large collision class.
    """
    book = address_book()
    table = addresses(scheme)
    names = [n for n in book["order"] if n in table] if book else []
    files = {n: book["declarations"][n]["file"] for n in names} if book else {}
    graph = citation_graph()
    linked = {n: set(graph.get(n, ())) for n in names}
    for source, targets in graph.items():
        for target in targets:
            if target in linked:
                linked[target].add(source)

    same_file_hits = 0
    linked_hits = 0
    tie_total = 0
    for a in names:
        pa = table[a]
        best = None
        winners: List[str] = []
        for b in names:
            if b == a:
                continue
            distance = squared_distance(pa, table[b])
            if best is None or distance < best:
                best, winners = distance, [b]
            elif distance == best:
                winners.append(b)
        tie_total += len(winners)
        if winners and all(files[w] == files[a] for w in winners):
            same_file_hits += 1
        if winners and all(w in linked[a] for w in winners):
            linked_hits += 1
    total = len(names)
    # chance: the mean probability that a uniformly chosen other declaration
    # shares a file / is linked
    chance_same = Fraction(0)
    chance_linked = Fraction(0)
    if total > 1:
        per_file: Dict[str, int] = {}
        for n in names:
            per_file[files[n]] = per_file.get(files[n], 0) + 1
        chance_same = Fraction(
            sum(per_file[files[n]] - 1 for n in names), total * (total - 1))
        chance_linked = Fraction(
            sum(len(linked[n]) for n in names), total * (total - 1))
    return {
        "declarations": total,
        "same_file_nearest": same_file_hits,
        "same_file_rate": Fraction(same_file_hits, total) if total else Fraction(0),
        "same_file_chance": chance_same,
        "linked_nearest": linked_hits,
        "linked_rate": Fraction(linked_hits, total) if total else Fraction(0),
        "linked_chance": chance_linked,
        "mean_tie_size": Fraction(tie_total, total) if total else Fraction(0),
    }


@memo
def separation_report() -> Dict[str, object]:
    """The three schemes, scored side by side on the same declarations."""
    out: Dict[str, object] = {}
    for scheme in SCHEMES:
        out[scheme] = {
            "pairs": _pair_statistics(scheme),
            "neighbours": _neighbour_statistics(scheme),
            "injectivity": injectivity(scheme),
        }
    feature = out["feature"]["neighbours"]
    control = out["hash_control"]["neighbours"]
    null = out["shuffled"]["neighbours"]
    out["verdict"] = {
        "feature_beats_hash_control": feature["same_file_rate"] > control["same_file_rate"],
        "feature_beats_shuffle": feature["same_file_rate"] > null["same_file_rate"],
        "feature_beats_chance": feature["same_file_rate"] > feature["same_file_chance"],
        "hash_is_chance_like":
            abs(control["same_file_rate"] - control["same_file_chance"])
            <= Fraction(1, 20),
        "linked_beats_chance": feature["linked_rate"] > feature["linked_chance"],
    }
    return out


#: The covering radius of the Leech lattice in this integer model.  The
#: lattice is scaled here so that its minimal squared norm is 32; in the
#: normalisation with minimum 4 the covering radius is ``sqrt(2)``, and the two
#: models differ by a factor of ``sqrt(8)``, so the radius here is exactly 4.
COVERING_RADIUS = 4


def readback_guarantee() -> Dict[str, object]:
    """Why the address *is* the feature vector, rather than approximating it.

    Quantising ``SCALE * f`` moves it by at most the covering radius, so every
    coordinate of the address is within :data:`COVERING_RADIUS` of
    ``SCALE * f_i``.  With ``SCALE >= 2 * COVERING_RADIUS`` that is at most
    half a step, so rounding the address back to the nearest multiple of
    ``SCALE`` returns ``f`` exactly -- for every declaration, not for most of
    them.  ``SCALE = 9`` clears the bound and, unlike 8, leaves the decoder
    something to do.

    The bound is a theorem (``RequestProject/GLM/Address.lean``,
    ``readback_exact``); what this function adds is the measurement that the
    corpus obeys it, and by how much room to spare.
    """
    book = address_book()
    if book is None:
        return {"available": False}
    worst = 0
    worst_name = ""
    moved = 0
    for name, point in addresses("feature").items():
        residual = describe_address(point)["max_residual"]
        if residual > worst:
            worst, worst_name = residual, name
        scaled = tuple(book["scale"] * v for v in book["features"][name])
        if tuple(point) != scaled:
            moved += 1
    return {
        "available": True,
        "scale": book["scale"],
        "covering_radius": COVERING_RADIUS,
        "scale_is_at_least_twice_radius": book["scale"] >= 2 * COVERING_RADIUS,
        "half_step": Fraction(book["scale"], 2),
        "worst_observed_residual": worst,
        "worst_declaration": worst_name,
        "moved_by_the_decoder": moved,
        "declarations": len(addresses("feature")),
        "bound_respected": worst <= COVERING_RADIUS,
        "lossless": 2 * worst <= book["scale"],
    }


def scale_sweep(scales: Sequence[int] = (4, 6, 8, 9, 12, 16),
                sample: int = 60) -> Dict[str, object]:
    """Why :data:`SCALE` is 9: fidelity against scale, measured not asserted.

    Decoding is the expensive step, so this runs on the first ``sample``
    declarations in source order.  For each scale it reports how many of them
    keep their feature vector through the round trip and how many distinct
    addresses they receive.
    """
    global SCALE
    table = feature_table()
    names = [d.name for d in declarations()][:sample]
    original = SCALE
    rows = []
    try:
        for scale in scales:
            SCALE = scale
            points = {name: quantise(table[name]) for name in names}
            exact = sum(1 for name in names
                        if describe_address(points[name])["recovered"]
                        == table[name])
            moved = sum(1 for name in names
                        if points[name]
                        != tuple(scale * v for v in table[name]))
            worst = max((describe_address(points[name])["max_residual"]
                         for name in names), default=0)
            rows.append({
                "scale": scale,
                "sample": len(names),
                "exact": exact,
                "exact_rate": Fraction(exact, len(names)) if names else Fraction(0),
                "moved_by_the_decoder": moved,
                "worst_residual": worst,
                "distinct": len(set(points.values())),
                "lossless": exact == len(names),
                "degenerate": moved == 0,
            })
    finally:
        SCALE = original
    return {"rows": tuple(rows), "chosen": original}


def parser_agreement(reference: Optional[Sequence[str]] = None
                     ) -> Dict[str, object]:
    """Agreement between the line reader and a reference list of names.

    ``reference`` is the compiler's own list of declarations, produced by
    ``lake env lean`` over a file that imports the development (see
    ``STATUS.md`` for the command).  Without one, the function reports what it
    can check on its own: that no name is claimed twice.
    """
    parsed = [d.name for d in declarations()]
    duplicates = sorted({n for n in parsed if parsed.count(n) > 1})
    if reference is None:
        return {"parsed": len(parsed), "duplicates": tuple(duplicates),
                "reference_supplied": False}
    ref = set(reference)
    got = set(parsed)
    return {
        "parsed": len(parsed),
        "reference": len(ref),
        "reference_supplied": True,
        "agreed": len(got & ref),
        "missed": tuple(sorted(ref - got)[:20]),
        "spurious": tuple(sorted(got - ref)[:20]),
        "agreement_rate": Fraction(len(got & ref), len(ref)) if ref else Fraction(0),
        "duplicates": tuple(duplicates),
    }


# ===========================================================================
#  Speaking
# ===========================================================================

def speak(name: str, neighbours: int = 3) -> Dict[str, object]:
    """Everything the machine can say about one Lean declaration.

    The address, the reading of the address, and the declarations nearest to
    it -- which is the operation "GLM speaks Lean" actually consists of.
    """
    decl = declaration(name)
    if decl is None:
        return {"found": False, "query": name}
    table = addresses("feature")
    point = table.get(decl.name)
    book = address_book()
    features = tuple(book["features"][decl.name]) if book else ()
    if point is None:
        return {"found": True, "addressed": False, "name": decl.name,
                "kind": decl.kind, "file": decl.file, "line": decl.line}
    reading = describe_address(point)
    ranked = sorted(
        ((squared_distance(point, other), other_name)
         for other_name, other in table.items() if other_name != decl.name),
        key=lambda pair: (pair[0], pair[1]))
    return {
        "found": True,
        "addressed": True,
        "name": decl.name,
        "kind": decl.kind,
        "file": decl.file,
        "line": decl.line,
        "features": features,
        "address": point,
        "norm": squared_distance(point, (0,) * 24),
        "reading": reading["reading"],
        "read_back_exact": reading["recovered"] == features,
        "sentence": sentence(reading["recovered"]),
        "neighbours": tuple({"name": n, "squared_distance": d,
                             "file": book["declarations"][n]["file"]}
                            for d, n in ranked[:neighbours]),
    }


def lean_address_report(sample: Optional[Sequence[str]] = None
                        ) -> Dict[str, object]:
    """The whole study, ready for the runtime to narrate."""
    state = cache_state()
    book = address_book()
    if book is None:
        return {"cache": state, "available": False}
    files: Dict[str, int] = {}
    kinds: Dict[str, int] = {}
    for name in book["order"]:
        meta = book["declarations"][name]
        files[meta["file"]] = files.get(meta["file"], 0) + 1
        kinds[meta["kind"]] = kinds.get(meta["kind"], 0) + 1
    chosen = list(sample) if sample else [
        "GLM.HigherLattices.BarnesWall.norm_dvd_eight",
        "GLM.Info.Layer.Visible.mono",
        "GLM.Address.address_congr",
    ]
    spoken = tuple(speak(name) for name in chosen)
    return {
        "available": True,
        "cache": state,
        "corpus": {
            "files": len(files),
            "declarations": len(book["order"]),
            "by_kind": dict(sorted(kinds.items())),
            "largest_file": max(files.items(), key=lambda kv: (kv[1], kv[0]))[0],
            "largest_file_declarations": max(files.values()),
        },
        "features": {"names": FEATURE_NAMES, "cap": CAP, "scale": book["scale"]},
        "round_trip": round_trip_report("feature"),
        "guarantee": readback_guarantee(),
        "separation": separation_report(),
        "spoken": tuple(s for s in spoken if s.get("found")),
    }
