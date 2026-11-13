"""``glm_universal.reasoning.leech_lean`` -- the leechlean addressing of the
repository's own Lean development, on the GLM's answering path.

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22; absorbed ahead of the owner's Lean build on the measurements of
``studies/LEECHLEAN_STUDY.md`` and a standalone Lean check
(``IntakeChecks/LeechLeanGolay.lean``, ``IntakeChecks/LeechLeanCodec.lean``,
compiled under the pinned toolchain ``leanprover/lean4:v4.28.0``); every
answer says so while the register ``wheels/_data/provisional.json`` lists the
item (``glm_universal.wheels.provisional_status``).*

What the item is
----------------
The leechlean item maps every recurring **part** of this repository's Lean
development -- a token, a bigram of structural tokens, a declaration frame or
a tactic head -- to an **address** in the Leech lattice Λ₂₄ (the ×√8 integer
model: a 24-integer vector, a true lattice point, integer-model norm² eight
times the true norm).  A file becomes a tick stream of addresses, the
transition between ticks is a **move** d = B − A (a lattice vector), and the
Λ/2Λ class of a move is its shadow in the Monster's 2²⁴-class index space.
The address codebook (39,992 parts, 39,992 distinct addresses, no
collisions), the library graph (29,422 parts joined by 80,375 directed
joinings under 55,269 (part, frame) attestations over the 442-file corpus)
and the recorded experiments are the item's own bundled data, taken as data;
the item's Python battery (``tests/test_leechlean_in_glm.py``) cross-checks
its engine against this package's substrate module by module before
anything here is trusted.

What this module is
-------------------
The **engine adapter**: pure Python over the substrate's exact machinery --
the Golay code of ``substrate/mog.py``, the Leech membership predicate, the
Λ/2Λ class map with its type-2 table and the exact nearest-point decoder of
``substrate/leech2.py`` / ``reasoning/analogy.py`` -- plus the lexer ported
byte-exactly from the item's ``lean_parts.py``.  The package has no numpy
and this module does not add one: the bulk instruments stay in the item;
what runs here is what a query needs.  Nothing constructs a float: the
tick streams, energies, distances and classes are integers and exact
fractions, and the one place the item used a float pipeline (addressing a
genuinely new part on the fly) is replaced by an exact integer-energy rule
(:func:`address_new_part`).

The answer surface is :mod:`.leech_lean_tools` (``tool leechlean ...``); the
measurement is :mod:`.leech_lean_study`.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .. import constants as C
from ..substrate import leech2, mog

__all__ = [
    "ITEM", "MODULE", "Tok", "tokenize", "decl_frames", "tick_frames", "DECL_KW",
    "PartInfo", "codebook_state", "library_state", "part_info", "address_of_part",
    "text_of_part", "is_lattice_point", "class_of", "class_type_of", "energy_of",
    "encode_text", "decode_stream", "file_report", "classify_ticks",
    "continuations", "attestations_of", "universal_core", "granularity_counts",
    "moves_of_stream", "move_report", "corrupt_stream", "sieve_tick", "sieve_report",
    "repair_stream", "address_new_part", "stitch_text", "resolve_lean_path",
    "GRADES", "BITS_PER_SHELL", "CORE",
]

#: The intake item this module came from, and its name in the register of
#: provisional families.
ITEM = "leechlean"
MODULE = "reasoning/leech_lean"

#: One bit of surprisal is four units of true Leech energy (the item's law:
#: the address target is sqrt(32 E) in the integer model, so |A|^2/8 = 4 E).
BITS_PER_SHELL = 4

#: The granularity grades of a part key, with the count the codebook holds
#: for each (the study's question 9 pins them).
GRADES = ("token", "bigram", "frame", "tactic")


# ===========================================================================
# 1.  the lexer, ported byte-exactly from the item's lean_parts.py
# ===========================================================================

KEYWORDS = frozenset("""
theorem def lemma instance abbrev example structure inductive class
axiom import open namespace end section variable universe set_option
noncomputable partial unsafe opaque by let have show from in do if then else
match with at as return mut for while try catch finally deriving where extends
private protected public macro syntax elab attr
fun forall exists
""".split())

HASH_COMMANDS = frozenset(("#check", "#eval", "#print", "#reduce", "#explain",
                           "#minimports", "#exit"))

SYMBOLS = ["<;>", ":=", "=>", "<|", "|>", "<=", ">=", "==", "!=", "/=",
           "&&", "||", "++", "::", "..", "<>", "!}"]
_SINGLE_SYM = set("()[]{}<>|=+-*/^.,;:!?'@$&~#⟨⟩⟦⟧‹›«»∘·×∑∀∃∈∉∧∨¬→←↔≤≥≠≈⁻¹₀₁₂₃₄₅₆₇₈₉᾿")

_IDENT_START = re.compile(r"[A-Za-z_\u0374-\u03ff\u2070-\u218f\U0001d400-\U0001d7ff]")
_IDENT_CONT = re.compile(r"[A-Za-z0-9_.'!?\u0374-\u03ff\u2070-\u218f\U0001d400-\U0001d7ff]")
_NUM_START = re.compile(r"[0-9]")
_NUM_CONT = re.compile(r"[0-9a-zA-Z_]")


@dataclass
class Tok:
    """One lexer token; ``key`` is the part key ``kind:text``."""
    kind: str
    text: str
    line: int
    col: int

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.text}"


def tokenize(text: str) -> List[Tok]:
    """Lex one Lean 4 file into tokens whose concatenation is the file.

    Ported byte-exactly from the item's ``lean_parts.tokenize`` (its round
    trip over the whole corpus is checked by the item battery and by
    ``tests/test_leech_lean.py`` here): nested block comments, line
    comments, string and char literals, backtick-quoted identifiers, numeric
    literals and Unicode identifiers are all kept verbatim.
    """
    out: List[Tok] = []
    i, n = 0, len(text)
    line, col = 1, 0

    def emit(kind: str, start: int, end: int):
        out.append(Tok(kind, text[start:end], line, col))

    while i < n:
        c = text[i]
        if c == "\n":
            j = i
            while j < n and text[j] in "\n":
                j += 1
            emit("ws", i, j)
            line += j - i
            col = 0
            i = j
            continue
        if c in " \t\r\f\v":
            j = i
            while j < n and text[j] in " \t\r\f\v":
                j += 1
            emit("ws", i, j)
            col += j - i
            i = j
            continue
        if c == "-" and i + 1 < n and text[i + 1] == "-":
            j = text.find("\n", i)
            j = n if j < 0 else j
            emit("comment", i, j)
            col += j - i
            i = j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "-":
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/-", j):
                    depth += 1
                    j += 2
                elif text.startswith("-/", j):
                    depth -= 1
                    j += 2
                else:
                    j += 1
            emit("comment", i, j)
            col += j - i
            i = j
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            emit("str", i, j)
            col += j - i
            i = j
            continue
        if c == "`":
            j = i + 1
            if j < n and _IDENT_START.match(text[j]):
                k = j + 1
                while k < n and _IDENT_CONT.match(text[k]):
                    k += 1
                emit("ident", i, k)
                col += k - i
                i = k
                continue
            emit("sym", i, i + 1)
            col += 1
            i += 1
            continue
        if c == "#":
            k = i + 1
            while k < n and _IDENT_CONT.match(text[k]):
                k += 1
            word = text[i:k]
            emit("kw" if word in HASH_COMMANDS else "sym", i, k)
            col += k - i
            i = k
            continue
        if _NUM_START.match(c):
            j = i + 1
            while j < n and _NUM_CONT.match(text[j]):
                j += 1
            while j < n and text[j] == "." and j + 1 < n and _NUM_START.match(text[j + 1]):
                j += 1
                while j < n and _NUM_CONT.match(text[j]):
                    j += 1
            emit("num", i, j)
            col += j - i
            i = j
            continue
        if _IDENT_START.match(c):
            j = i + 1
            while j < n and _IDENT_CONT.match(text[j]):
                j += 1
            word = text[i:j]
            emit("kw" if word in KEYWORDS else "ident", i, j)
            col += j - i
            i = j
            continue
        matched = False
        for s in SYMBOLS:
            if text.startswith(s, i):
                emit("sym", i, i + len(s))
                col += len(s)
                i += len(s)
                matched = True
                break
        if matched:
            continue
        if c in _SINGLE_SYM:
            emit("sym", i, i + 1)
            col += 1
            i += 1
            continue
        emit("sym", i, i + 1)
        col += 1
        i += 1
    return out


DECL_KW = frozenset(("theorem", "def", "lemma", "instance", "abbrev",
                    "example", "structure", "inductive", "class", "axiom",
                    "opaque"))


def structural(toks: Sequence[Tok]) -> List[Tuple[int, Tok]]:
    """Indices and tokens of the non-ws, non-comment tokens."""
    return [(i, t) for i, t in enumerate(toks)
            if t.kind not in ("ws", "comment")]


def decl_frames(toks: Sequence[Tok]) -> List[str]:
    """One frame part per top-level declaration (the item's convention)."""
    st = structural(toks)
    starts = [k for k, (_, t) in enumerate(st)
              if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
    frames: List[str] = []
    for idx, k in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(st)
        body = None
        for j in range(k + 1, end):
            if st[j][1].kind == "sym" and st[j][1].text == ":=":
                nxt = st[j + 1][1] if j + 1 < end else None
                body = "by" if (nxt is not None and nxt.kind == "kw"
                                and nxt.text == "by") else "term"
                break
        stmt_len = 0
        for j in range(k + 1, end):
            if st[j][1].kind == "sym" and st[j][1].text == ":=":
                stmt_len = j - k - 1
                break
        bucket = min(int(stmt_len).bit_length(), 8) if stmt_len else 0
        frames.append(f"f:{st[k][1].text}|body={body}|len2={bucket}")
    return frames


TOP_FRAME = "f:top"


def tick_frames(toks: Sequence[Tok]) -> List[str]:
    """The enclosing declaration frame of every token ('f:top' before the
    first declaration) -- ported from the item's ``library.tick_frames``."""
    st = structural(toks)
    starts = [i for i, (_, t) in enumerate(st)
              if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
    frames = decl_frames(toks) if starts else []
    out = [TOP_FRAME] * len(toks)
    if not starts:
        return out
    st_idx = [i for i, _ in st]
    for si, i0 in enumerate(starts):
        lo = st_idx[i0]
        hi = st_idx[starts[si + 1]] if si + 1 < len(starts) else len(toks)
        fk = frames[si] if si < len(frames) else TOP_FRAME
        for j in range(lo, hi):
            out[j] = fk
    return out


# ===========================================================================
# 2.  the state: the codebook (the item's data) and the library graph
# ===========================================================================

@dataclass(frozen=True)
class PartInfo:
    """One codebook part: its address and the recorded facts about it."""
    key: str
    address: Tuple[int, ...]
    count: int
    energy: int
    grade: str
    displaced: bool

    @property
    def text(self) -> str:
        return self.key.split(":", 1)[1]


@dataclass
class Codebook:
    """The item's 39,992-part codebook, loaded lazily from the item folder."""
    parts: Dict[str, PartInfo]
    cells: Dict[Tuple[int, ...], str]
    occupied: set

    def __len__(self) -> int:
        return len(self.parts)


@dataclass
class LibraryCore:
    """The library graph (the item's ``library_core.npz`` as gzipped JSON)."""
    part_files: Dict[str, int]
    edge_count: Dict[Tuple[str, str], int]
    edge_files: Dict[Tuple[str, str], int]
    ctx_files: Dict[Tuple[str, str], int]
    n_files: int
    n_tokens: int
    out: Dict[str, List[Tuple[str, int]]]


_CODEBOOK: Optional[Codebook] = None
_CORE: Optional[LibraryCore] = None
_REPERTOIRE: Optional[Dict[Tuple[int, ...], int]] = None


def codebook_state() -> Codebook:
    """The item's codebook, loaded once (a clean refusal if the item is
    absent: the GLM never answers from a folder it cannot see)."""
    global _CODEBOOK
    if _CODEBOOK is not None:
        return _CODEBOOK
    path = C.source_material_item(ITEM) / "data" / "codebook.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"the leechlean codebook is not where the item folder puts it "
            f"({path}); the item must stay in source_material/")
    raw = json.loads(path.read_text(encoding="utf-8"))
    parts: Dict[str, PartInfo] = {}
    for key, rec in raw["parts"].items():
        parts[key] = PartInfo(key=key,
                              address=tuple(int(v) for v in rec["address"]),
                              count=int(rec["count"]),
                              energy=int(rec["energy"]),
                              grade=str(rec["granularity"]),
                              displaced=bool(rec["displaced"]))
    if len(parts) != len({p.address for p in parts.values()}):
        raise ValueError("the codebook is not injective")
    _CODEBOOK = Codebook(parts=parts,
                        cells={p.address: k for k, p in parts.items()},
                        occupied={p.address for p in parts.values()})
    return _CODEBOOK


def library_state() -> LibraryCore:
    """The library graph, loaded once from the derived JSON (see
    ``reasoning/_data/leech_lean_core.json.gz``, generated from the item's
    ``library_core.npz``; pure JSON so the package needs no numpy)."""
    global _CORE
    if _CORE is not None:
        return _CORE
    path = Path(__file__).resolve().parent / "_data" / "leech_lean_core.json.gz"
    if not path.is_file():
        raise FileNotFoundError(
            f"the leechlean library core is missing ({path}); it is generated "
            f"from the item's data/library_core.npz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        raw = json.load(fh)
    edge_count: Dict[Tuple[str, str], int] = {}
    edge_files: Dict[Tuple[str, str], int] = {}
    out: Dict[str, List[Tuple[str, int]]] = {}
    for e in raw["joinings"]:
        k = (e["u"], e["v"])
        edge_count[k] = int(e["count"])
        edge_files[k] = int(e["files"])
        out.setdefault(e["u"], []).append((e["v"], int(e["count"])))
    for v in out.values():
        v.sort(key=lambda t: (-t[1], t[0]))
    ctx = {(c["part"], c["frame"]): int(c["files"]) for c in raw["contexts"]}
    _CORE = LibraryCore(part_files={p: int(n) for p, n in raw["parts"].items()},
                        edge_count=edge_count, edge_files=edge_files,
                        ctx_files=ctx, n_files=int(raw["n_library_files"]),
                        n_tokens=int(raw["n_library_tokens"]), out=out)
    return _CORE


def repertoire() -> Dict[Tuple[int, ...], int]:
    """The corpus's move repertoire: every joining of the library graph as a
    move d = B - A with its count (computed once; 80,375 joinings)."""
    global _REPERTOIRE
    if _REPERTOIRE is not None:
        return _REPERTOIRE
    cb = codebook_state()
    core = library_state()
    rep: Dict[Tuple[int, ...], int] = {}
    for (u, v), c in core.edge_count.items():
        a, b = cb.parts[u].address, cb.parts[v].address
        d = tuple(b[i] - a[i] for i in range(24))
        rep[d] = rep.get(d, 0) + c
    _REPERTOIRE = rep
    return _REPERTOIRE


# ===========================================================================
# 3.  the lattice facts of an address (all through the substrate)
# ===========================================================================

def address_of_part(key: str) -> Optional[Tuple[int, ...]]:
    """The Leech address of a part key, or ``None`` if the codebook has it
    not."""
    p = codebook_state().parts.get(key)
    return p.address if p is not None else None


def text_of_part(key: str) -> str:
    return key.split(":", 1)[1]


def part_info(key: str) -> Optional[PartInfo]:
    return codebook_state().parts.get(key)


def is_lattice_point(addr: Sequence[int]) -> bool:
    """The exact membership predicate of the substrate (``leech2.in_leech``)."""
    return leech2.in_leech([int(v) for v in addr])


def energy_of(addr: Sequence[int]) -> int:
    """True lattice energy of an address: integer-model norm²/8."""
    return sum(int(v) * int(v) for v in addr) // 8


def class_of(addr: Sequence[int]) -> int:
    """The Λ/2Λ class of a lattice point, as the substrate's 24-bit int
    (coordinates in the Leech basis, mod 2)."""
    return leech2.class_of([int(v) for v in addr])


def class_type_of(addr: Sequence[int]) -> int:
    """The class type of an address: 0 (zero class), 2 (a minimal-vector
    class, one of the 98,280 Griess X_r classes), 3 (q = 1) or 4 (frames),
    through the substrate's own type-2 table and q-form."""
    cls = class_of(addr)
    if cls == 0:
        return 0
    if cls in leech2.type2_classes():
        return 2
    return 3 if leech2.q_form(cls) == 1 else 4


# ===========================================================================
# 4.  the codec: a file is a tick stream of addresses
# ===========================================================================

def resolve_lean_path(arg: str) -> Path:
    """A Lean file of this repository by repo-relative path under ``src/lean``
    (or an absolute path); a clean refusal if there is no such file."""
    p = Path(arg)
    if p.is_absolute():
        if p.is_file():
            return p
        raise FileNotFoundError(f"no such file: {arg}")
    root = C.REPOSITORY_ROOT / "src" / "lean"
    for cand in (root / arg, root / f"{arg}.lean"):
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        f"no such Lean file under src/lean: {arg}")


def encode_text(text: str) -> Tuple[List[str], List[Tuple[int, ...]]]:
    """A text as (part keys, addresses), one tick per token; a clean refusal
    naming the first part the codebook has not."""
    cb = codebook_state()
    keys: List[str] = []
    addrs: List[Tuple[int, ...]] = []
    for t in tokenize(text):
        p = cb.parts.get(t.key)
        if p is None:
            raise KeyError(t.key)
        keys.append(t.key)
        addrs.append(p.address)
    return keys, addrs


def decode_stream(addrs: Sequence[Sequence[int]]) -> str:
    """An address stream back to exact text (the codebook is injective)."""
    cb = codebook_state()
    out = []
    for a in addrs:
        key = cb.cells.get(tuple(int(v) for v in a))
        if key is None:
            raise KeyError(tuple(int(v) for v in a))
        out.append(text_of_part(key))
    return "".join(out)


@dataclass
class FileReport:
    """The measured facts of one encoded file."""
    path: Path
    ticks: int
    round_trip: bool
    on_lattice: int
    energy: int
    path2: int
    net2: int
    ctx: int
    part_known: int
    new_ticks: int
    frames: List[str]


def classify_ticks(toks: Sequence[Tok], keys: Sequence[str]
                   ) -> Tuple[List[str], List[str]]:
    """Per-tick status against the library: 'new' (the part has no address
    -- not even in the extended codebook), 'ctx' (part and frame attested in
    the library), 'part' (addressed but unattested under this frame)."""
    core = library_state()
    cb = codebook_state()
    frames = tick_frames(toks)
    status: List[str] = []
    for k, f in zip(keys, frames):
        if k not in cb.parts:
            status.append("new")
        elif core.ctx_files.get((k, f), 0) > 0:
            status.append("ctx")
        else:
            status.append("part")
    return status, frames


def file_report(path: Path) -> FileReport:
    """Encode one file of the repository, verify the round trip and measure
    the journey (energy, path², net², the verification frontier)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    toks = tokenize(text)
    keys = [t.key for t in toks]
    cb = codebook_state()
    addrs: List[Tuple[int, ...]] = []
    missing: List[str] = []
    for k in keys:
        p = cb.parts.get(k)
        if p is None:
            missing.append(k)
        else:
            addrs.append(p.address)
    if missing:
        raise KeyError(missing[0])
    round_trip = decode_stream(addrs) == text
    on_lattice = sum(1 for a in addrs if is_lattice_point(a))
    energy = sum(energy_of(a) for a in addrs)
    steps = [(tuple(addrs[i + 1][j] - addrs[i][j] for j in range(24)))
             for i in range(len(addrs) - 1)]
    path2 = sum(sum(v * v for v in d) for d in steps)
    net = tuple(addrs[-1][j] - addrs[0][j] for j in range(24)) if addrs else (0,) * 24
    net2 = sum(v * v for v in net)
    status, frames = classify_ticks(toks, keys)
    return FileReport(path=path, ticks=len(addrs), round_trip=round_trip,
                      on_lattice=on_lattice, energy=energy, path2=path2,
                      net2=net2, ctx=status.count("ctx"),
                      part_known=status.count("part"),
                      new_ticks=status.count("new"), frames=frames)


# ===========================================================================
# 5.  the move algebra between addresses
# ===========================================================================

def moves_of_stream(addrs: Sequence[Sequence[int]]) -> List[Tuple[int, ...]]:
    """The moves d = B − A of an address stream, in tick order."""
    return [tuple(int(addrs[i + 1][j]) - int(addrs[i][j]) for j in range(24))
            for i in range(len(addrs) - 1)]


@dataclass
class MoveReport:
    """The measured facts of one stream's moves."""
    moves: int
    distinct: int
    known_moves: int
    mean_norm2_num: int     # mean |d|^2 as an exact fraction numerator/..
    mean_norm2_den: int     # ..denominator over the distinct moves
    top: List[Tuple[Tuple[int, ...], int, int]]
    types: Dict[int, int]
    class_law: bool
    composed_known: Optional[bool]


def move_report(addrs: Sequence[Sequence[int]]) -> MoveReport:
    """The move report of one stream: counts, norms, Λ/2Λ class types, the
    class law live on its two most common moves, and whether their composed
    move is back in the corpus repertoire."""
    from collections import Counter
    rep = repertoire()
    moves = moves_of_stream(addrs)
    counts = Counter(moves)
    distinct = len(counts)
    known = sum(c for d, c in counts.items() if d in rep)
    norm_sum = sum(sum(v * v for v in d) for d in counts)
    types: Dict[int, int] = {}
    for d in counts:
        t = class_type_of(d)
        types[t] = types.get(t, 0) + counts[d]
    top = counts.most_common(5)
    class_law = True
    if len(top) >= 2:
        d1, d2 = top[0][0], top[1][0]
        c1, c2 = class_of(d1), class_of(d2)
        class_law = class_of(tuple(a + b for a, b in zip(d1, d2))) == (c1 ^ c2)
    composed_known: Optional[bool] = None
    if len(top) >= 2:
        composed_known = tuple(a + b for a, b in zip(top[0][0], top[1][0])) in rep
    g = len(counts)
    return MoveReport(moves=len(moves), distinct=distinct, known_moves=known,
                      mean_norm2_num=norm_sum, mean_norm2_den=g,
                      top=[(d, c, sum(v * v for v in d)) for d, c in top],
                      types=dict(sorted(types.items())), class_law=class_law,
                      composed_known=composed_known)


# ===========================================================================
# 6.  the sieve and the repair of corrupted streams
# ===========================================================================

_GOLAY: Optional[frozenset] = None


def _golay_set() -> frozenset:
    """The 4096 codeword masks of the substrate's Golay code."""
    global _GOLAY
    if _GOLAY is None:
        _GOLAY = frozenset(mog.GolayCode().codeword_masks)
    return _GOLAY


def sieve_tick(x: Sequence[int]) -> str:
    """The first Leech congruence a 24-integer point breaks: 'mod2' (the
    parities differ), 'mod4-golay' (a mod-4 support is not a codeword),
    'mod8-sum' (the coordinate sum), or 'clean' (a lattice point)."""
    v = [int(c) for c in x]
    if len(v) != 24:
        raise ValueError("a Leech address has 24 coordinates")
    m = v[0] % 2
    if any(c % 2 != m for c in v):
        return "mod2"
    gs = _golay_set()
    for res in (2, 3):
        mask = 0
        for i, c in enumerate(v):
            if c % 4 == res:
                mask |= 1 << i
        if mask not in gs:
            return "mod4-golay"
    if (sum(v) - 4 * m) % 8 != 0:
        return "mod8-sum"
    return "clean"


def sieve_report(addrs: Sequence[Sequence[int]]) -> Dict[str, int]:
    """The sieve over a stream: which congruence each tick breaks."""
    out = {"mod2": 0, "mod4-golay": 0, "mod8-sum": 0, "clean": 0}
    for a in addrs:
        out[sieve_tick(a)] += 1
    return out


def corrupt_stream(addrs: Sequence[Sequence[int]], model: str, seed: int,
                   k: int = 1) -> List[Tuple[int, ...]]:
    """Corrupt an address stream, exactly and deterministically: 'flip'
    shifts one uniformly chosen coordinate of every tick by ±k; 'slip' adds
    a minimal vector to every tick (staying on the lattice, the case the
    sieve alone cannot see)."""
    import random
    rng = random.Random(seed)
    out: List[Tuple[int, ...]] = []
    if model == "flip":
        for a in addrs:
            v = list(int(c) for c in a)
            i = rng.randrange(24)
            v[i] += rng.choice((-k, k))
            out.append(tuple(v))
        return out
    if model == "slip":
        mvs = list(leech2.minimal_vectors())
        for a in addrs:
            v = [int(c) + int(s) for c, s in
                 zip(a, mvs[rng.randrange(len(mvs))])]
            out.append(tuple(v))
        return out
    raise ValueError(f"unknown corruption model {model!r}")


def repair_stream(addrs: Sequence[Sequence[int]]
                  ) -> Tuple[List[Optional[str]], Dict[str, int]]:
    """Repair a corrupted stream, class-assisted: a clean tick keeps its
    part when its Λ/2Λ class holds exactly one codebook part; a class with
    several members is resolved by exact integer distance within it; a
    class with none (the minimal-vector slip case: the point is on the
    lattice but the slip moved it to a foreign class) is resolved by the
    nearest codebook part within the minimal-vector reach of ±4 per
    coordinate (a coordinate-bucket index replaces the item's kd-tree; the
    package has no numpy).  Returns the repaired part keys (``None`` where
    nothing resolves) and the sieve's report."""
    cb = codebook_state()
    by_class: Dict[int, List[str]] = {}
    buckets: Dict[Tuple[int, int], List[str]] = {}
    for key, p in cb.parts.items():
        by_class.setdefault(class_of(p.address), []).append(key)
        buckets.setdefault((p.address[0], p.address[1]), []).append(key)
    report = sieve_report(addrs)

    def nearest_part(v: Sequence[int]) -> Optional[str]:
        best: Optional[str] = None
        best_d = -1
        for a0 in range(v[0] - 4, v[0] + 5):
            for a1 in range(v[1] - 4, v[1] + 5):
                for key in buckets.get((a0, a1), ()):
                    p = cb.parts[key]
                    d = sum((x - y) * (x - y) for x, y in zip(p.address, v))
                    if best is None or d < best_d or (d == best_d and key < best):
                        best, best_d = key, d
        return best

    out: List[Optional[str]] = []
    for a in addrs:
        v = [int(c) for c in a]
        if sieve_tick(v) != "clean":
            v = [int(c) for c in _nearest_lattice(v)]
        members = by_class.get(class_of(v), [])
        if len(members) == 1:
            out.append(members[0])
            continue
        if len(members) > 1:
            best, best_d = None, -1
            for key in members:
                p = cb.parts[key]
                d = sum((x - y) * (x - y) for x, y in zip(p.address, v))
                if best is None or d < best_d or (d == best_d and key < best):
                    best, best_d = key, d
            out.append(best)
            continue
        out.append(nearest_part(v))
    stats = dict(report)
    stats["n"] = len(addrs)
    stats["resolved"] = sum(1 for k in out if k is not None)
    return out, stats


def _nearest_lattice(v: Sequence[int]) -> Tuple[int, ...]:
    """The exact nearest Leech point (``reasoning.analogy``), as integers."""
    from ..reasoning import analogy
    return tuple(analogy.nearest_lattice_point(
        [Fraction(int(c)) for c in v]).point)


# ===========================================================================
# 7.  the library: queries, attestation, and stitching new parts
# ===========================================================================

def continuations(key: str) -> List[Tuple[str, int]]:
    """The library's joinings out of a part, heaviest first."""
    return library_state().out.get(key, [])


def attestations_of(key: str) -> List[Tuple[str, int]]:
    """The declaration frames a part is attested under, most files first."""
    core = library_state()
    out = [(f, n) for (k, f), n in core.ctx_files.items() if k == key]
    out.sort(key=lambda t: (-t[1], t[0]))
    return out


def universal_core(min_files: int) -> List[str]:
    """The parts the library uses in at least ``min_files`` of its files."""
    core = library_state()
    return sorted(k for k, n in core.part_files.items() if n >= min_files)


def granularity_counts() -> Dict[str, int]:
    """The codebook's parts per granularity (token, bigram, frame, tactic)."""
    out: Dict[str, int] = {g: 0 for g in GRADES}
    for p in codebook_state().parts.values():
        if p.grade in out:
            out[p.grade] += 1
    return out


def _integer_surprisal(count: int, total: int) -> int:
    """The exact integer-surprisal rule of the port: the least e with
    2^e * count >= total (an upper byte of the item's -log2 f in bits, with
    no float anywhere)."""
    e = 0
    while (1 << e) * count < total:
        e += 1
    return e


def _identity_direction(key: str) -> List[int]:
    """A deterministic integer direction from the part key (the port's
    exact stand-in for the item's hashed PPMI channels)."""
    h = hashlib.sha256(key.encode("utf-8")).digest()
    return [1 + (h[i] * 251 + h[i + 8] * 31) % 997 for i in range(16)]


def address_new_part(key: str, count: int = 1
                     ) -> Tuple[Tuple[int, ...], int, int]:
    """Address a genuinely new part on the fly, exactly.

    The rule is the item's, with its float pipeline replaced by exact
    arithmetic: the direction is the part's role channel one-hot blended
    with a deterministic integer direction (no normalisation by a square
    root -- the ray is walked rationally); the target is the first point of
    that ray whose integer-model squared norm reaches 32 * E with
    E = :func:`_integer_surprisal` (one bit of surprisal = four units of
    true lattice energy); the target is quantised by the exact nearest-point
    decoder; a taken cell displaces the target outward by rational fifteens
    (the item's radial quantum 3/20 per step, capped as in the item), and
    the extended codebook stays injective.  Returns the fresh address, the
    integer-surprisal E and the displacement steps taken.
    """
    cb = codebook_state()
    if key in cb.parts:
        return cb.parts[key].address, 0, 0
    total = library_state().n_tokens
    e = _integer_surprisal(max(count, 1), total)
    role = [0] * 8
    ch = {"kw": 1, "ident": 2, "sym": 3, "num": 4, "str": 4, "ws": 0,
          "comment": 0}.get(key.split(":", 1)[0], 2)
    role[min(ch, 7)] = 1
    direction = role + _identity_direction(key)
    steps = 0
    j = 0
    while True:
        # target: p/q * direction with |T|^2 the first multiple past 32 E
        q = 20 + 3 * j          # the item's radial quantum, exact
        s = sum(v * v for v in direction)
        p = 1
        while p * p * s < (32 * e) * q * q:
            p += 1
        target = [Fraction(v * p, q) for v in direction]
        pt = _nearest_lattice(target)
        if pt not in cb.occupied:
            cb.occupied.add(pt)
            cb.cells[pt] = key
            cb.parts[key] = PartInfo(key=key, address=pt, count=count,
                                     energy=energy_of(pt), grade="token",
                                     displaced=j > 0)
            return pt, e, steps
        j += 1
        steps += 1
        if j > 40:
            raise RuntimeError(f"{key!r} could not be addressed on the fly")


def stitch_text(text: str) -> Dict[str, object]:
    """Author a snippet against the library: classify every tick (ctx /
    part / new), address the genuinely new parts on the fly, and project the
    whole tick stream back through the extended codebook -- byte-exact.

    Returns the tick statuses, the new parts with their fresh addresses and
    integer-surprisal energies, and the projection check."""
    toks = tokenize(text)
    keys = [t.key for t in toks]
    status, frames = classify_ticks(toks, keys)
    cb = codebook_state()
    new_parts: List[Tuple[str, Tuple[int, ...], int, int]] = []
    for k, st in zip(keys, status):
        if st == "new":
            addr, e, j = address_new_part(k)
            new_parts.append((k, addr, e, j))
    addrs = [cb.parts[k].address for k in keys]
    projected = decode_stream(addrs)
    return {"ticks": len(keys), "status": status, "new_parts": new_parts,
            "byte_exact": projected == text,
            "n_ctx": status.count("ctx"), "n_part": status.count("part"),
            "n_new": status.count("new")}
