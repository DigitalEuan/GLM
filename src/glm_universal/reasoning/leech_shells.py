"""``glm_universal.reasoning.leech_shells`` -- every Leech shell counted from
the lattice's definition (Phase 164).

*Created 19 October 2026.* Last altered 22 October 2026 (Phase 180: the
procedure's correctness for every shell is a theorem of
``GLM.LeechShellCount``; ``proved_shells_check`` reads the proved sizes back
from the Lean file).  Altered 19 October 2026 (Phase 165: the minimal shell
enumerated from the three parameter families of ``GLM.LeechKissing``, whose
count is now a theorem).

Phase 163 had the machine count the Golay code from its generator rows and
form the kissing number as ``128 * octads + 4 * C(24,2) + 24 * codewords``.
That *shapes rule* was declared, not derived, and only the minimal shell was
counted: the shell catalogue of :mod:`glm_universal.reasoning.llvq` was a
stored table, and its fifth entry was wrong (``34,408,430,950`` where the
lattice has ``34,417,656,000`` vectors of norm 12).  This module derives every
shell from the definition of the lattice and nothing else
(``studies/LEECH_SHELLS_STUDY.md``).

The definition (Conway's construction from the Golay code ``C``, coordinates
scaled by ``sqrt 8``): an integer vector ``x`` of length 24 is in the Leech
lattice when

* every coordinate has the same parity ``m`` (0 or 1);
* for ``m = 0`` the coordinates ``= 2 (mod 4)`` sit on a codeword of ``C``;
  for ``m = 1`` the coordinates ``= 1 (mod 4)`` sit on a codeword;
* the coordinates sum to ``4 m (mod 8)``.

A vector of true norm ``2 t`` has ``sum x_i^2 = 16 t``.

How the count goes.  For a codeword ``c`` of weight ``w`` the coordinates on
``c`` and off it range over two fixed residue classes mod 4, and the sign
freedom is entirely inside those classes, so the number of lattice vectors
whose pattern is ``c`` depends on ``w`` only.  The machine therefore

1. counts the code's weight distribution by walking it (``weight_census``:
   ``1, 759, 2576, 759, 1``, the census of
   ``GLM.LeechMachine.machine_octads`` extended to every weight);
2. for each weight ``w`` forms the two one-coordinate generating functions
   (value classes ``2 + 4Z`` on ``c``, ``4Z`` off it for ``m = 0``;
   ``1 + 4Z`` on ``c``, ``3 + 4Z`` off it for ``m = 1``), each a polynomial in
   the squared value with a coefficient vector over the sum mod 8, and takes
   ``w`` and ``24 - w`` powers of them (``pattern_count``);
3. reads off the coefficient at norm ``16 t`` with sum ``4 m (mod 8)``, and
   sums ``A_w`` times it over the weights (``shell_count``).

Nothing in the count is a stored shell size, a shape or a sign factor: the
minimal shell's shapes (``2^7`` signs on an octad, four signed pairs, the odd
shape on any codeword) come out of step 2 (``minimal_shapes``) and are proved
from the same definition in ``GLM.LeechShells.minimal_shape``.

Since Phase 165 (``studies/LEECH_KISSING_STUDY.md``) the minimal shell is
also proved both ways and counted in Lean: ``GLM.LeechKissing.minimal_iff``
(a vector is minimal exactly when it has one of the three shapes with its
support and sign condition) and ``GLM.LeechKissing.leech_kissing_number``
(the set of minimal vectors has 196,560 elements).  ``minimal_shell_vectors``
builds the same finite set the Lean file builds, from the same three
parameter families, and ``minimal_shell_check`` tests every one of its
vectors against the definition.

Since Phase 180 (``studies/LEECH_SHELL_COUNT_STUDY.md``) the procedure
itself is proved: ``GLM.LeechShellCount.shellArr_correct`` states that for
*every* ``t`` the number of lattice vectors of squared length ``16 t`` equals
the census-weighted generating-function count, written in Lean as the same
three steps (one-coordinate generating functions, truncated powers and
products, the coefficient at ``(16 t, 4 m)``).  The argument "the count on a
codeword depends only on its weight" is the theorem ``prod_pattern``;
``leech_shell_sizes`` gives the first eight shells as theorems about the
definition.  ``proved_shells_check`` reads those eight sizes from the Lean
file and sets them beside this module's count and the theta series.

The check.  The theta series of the lattice is also a modular form,
``E_4^3 - 720 Delta`` (:func:`glm_universal.substrate.leech2.theta_series`),
which knows nothing of the Golay code.  The two derivations are independent;
``shell_report`` compares them shell by shell, and a disagreement is a
failure, not a correction of either.

Exactness: integers only.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "weight_census", "pattern_count",
    "shell_count", "shells", "minimal_shapes", "modular_shells",
    "shell_report", "KISSING_LEAN_FILE", "KISSING_LEAN_THEOREMS",
    "minimal_shell_vectors", "minimal_shell_check",
    "SHELL_COUNT_LEAN_FILE", "SHELL_COUNT_LEAN_THEOREMS", "proved_shell_sizes",
    "proved_shells_check",
]

LEAN_FILE: str = "RequestProject/GLM/LeechShells.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "minimal_shape", "minimal_even_support", "minimal_odd_pattern",
    "shellCount_eq", "shells_from_census")

KISSING_LEAN_FILE: str = "RequestProject/GLM/LeechKissing.lean"
KISSING_LEAN_THEOREMS: Tuple[str, ...] = (
    "mem_minimalShell", "card_minimalShell", "leech_kissing_number",
    "minimal_iff")

SHELL_COUNT_LEAN_FILE: str = "RequestProject/GLM/LeechShellCount.lean"
SHELL_COUNT_LEAN_THEOREMS: Tuple[str, ...] = (
    "coeff_prod", "prod_pattern", "card_shellSet", "card_fib",
    "shell_card_gf", "mul_coeff", "rep_mul", "rep_pow", "patternArr_eq",
    "shellArr_correct", "shellFast_correct", "shellCount_correct",
    "leech_shell_sizes")

_N = 24


def _popcount(x: int) -> int:
    return bin(x).count("1")


def weight_census() -> Dict[int, int]:
    """The Golay code's weight distribution, counted by walking its 4,096
    codewords from the generator (``substrate.mog.GolayCode``) in Gray-code
    order, one generator row added per step."""
    from ..substrate.mog import GolayCode
    g = GolayCode()
    rows = [g.encode_mask(1 << r) for r in range(12)]
    word = 0
    census: Dict[int, int] = {0: 1}
    for i in range(1, 1 << 12):
        r = (i & -i).bit_length() - 1      # the bit the Gray code flips
        word ^= rows[r]
        w = _popcount(word)
        census[w] = census.get(w, 0) + 1
    return dict(sorted(census.items()))


def _one_coordinate(residue: int, limit: int) -> Dict[int, List[int]]:
    """The values ``v = residue (mod 4)`` with ``v^2 <= limit``, as
    ``{v^2: [number of v with that square and v = s (mod 8)] for s < 8}``."""
    out: Dict[int, List[int]] = {}
    r = 0
    while r * r <= limit:
        for v in {r, -r}:
            if v % 4 == residue:
                out.setdefault(v * v, [0] * 8)[v % 8] += 1
        r += 1
    return out


def _times(a: Dict[int, List[int]], b: Dict[int, List[int]],
           limit: int) -> Dict[int, List[int]]:
    out: Dict[int, List[int]] = {}
    for na, ca in a.items():
        for nb, cb in b.items():
            n = na + nb
            if n > limit:
                continue
            cell = out.setdefault(n, [0] * 8)
            for sa, xa in enumerate(ca):
                if xa:
                    for sb, xb in enumerate(cb):
                        if xb:
                            cell[(sa + sb) % 8] += xa * xb
    return out


def _power(a: Dict[int, List[int]], k: int, limit: int
           ) -> Dict[int, List[int]]:
    out: Dict[int, List[int]] = {0: [1] + [0] * 7}
    for _ in range(k):
        out = _times(out, a, limit)
    return out


def pattern_count(m: int, w: int, t: int) -> int:
    """The number of lattice vectors of norm ``16 t`` (true norm ``2 t``)
    with parity ``m`` whose residue pattern is one fixed codeword of weight
    ``w``."""
    limit = 16 * t
    on, off = (2, 0) if m == 0 else (1, 3)
    poly = _times(_power(_one_coordinate(on, limit), w, limit),
                  _power(_one_coordinate(off, limit), _N - w, limit), limit)
    return poly.get(limit, [0] * 8)[(4 * m) % 8]


def shell_count(t: int, census: Dict[int, int] = None) -> int:
    """The number of Leech vectors of true norm ``2 t``, from the weight
    census and the definition."""
    census = weight_census() if census is None else census
    return sum(a * pattern_count(m, w, t)
               for w, a in census.items() for m in (0, 1))


def shells(top: int = 6) -> List[Tuple[int, int]]:
    """``[(t, count)]`` for ``t = 0 .. top``."""
    census = weight_census()
    return [(t, shell_count(t, census)) for t in range(top + 1)]


def minimal_shapes() -> Dict[str, int]:
    """The minimal shell split by what step 2 found, per codeword weight:
    the even vectors on an octad, the even vectors on the zero word, and
    the odd vectors on any codeword (with the per-codeword factors)."""
    census = weight_census()
    out = {}
    for m in (0, 1):
        for w, a in census.items():
            k = pattern_count(m, w, 2)
            if k:
                out[f"m={m} w={w}"] = k
                out[f"m={m} w={w} codewords"] = a
    return out


def modular_shells(top: int = 6) -> List[int]:
    """The theta series as the modular form ``E_4^3 - 720 Delta``; entry
    ``t`` counts the vectors of true norm ``2 t``."""
    from ..substrate.leech2 import theta_series
    return list(theta_series(top))


def shell_report(top: int = 6) -> Dict[str, object]:
    """Both derivations side by side."""
    from . import llvq
    ours = shells(top)
    mod = modular_shells(top)
    rows = [{"t": t, "norm": 2 * t, "golay": c, "modular": mod[t],
             "agree": c == mod[t]} for t, c in ours]
    return {"census": weight_census(), "rows": rows,
            "agree": all(r["agree"] for r in rows),
            "minimal_shapes": minimal_shapes(),
            "catalogue": [(s["norm2_8n"], s["count"])
                          for s in llvq.shell_summary()]}


def _codewords() -> List[int]:
    """The 4,096 codewords as 24-bit masks, walked from the generator."""
    from ..substrate.mog import GolayCode
    g = GolayCode()
    rows = [g.encode_mask(1 << r) for r in range(12)]
    word, out = 0, [0]
    for i in range(1, 1 << 12):
        word ^= rows[(i & -i).bit_length() - 1]
        out.append(word)
    return out


def minimal_shell_vectors() -> List[Tuple[int, ...]]:
    """The minimal shell as the explicit list ``GLM.LeechKissing.minimalShell``
    is built from: (octad, even set of minus signs in it) to eight ``+-2``;
    (pair of positions, any set of minus signs) to two ``+-4``; (codeword
    ``c``, position ``k``) to ``1`` on ``c``, ``-1`` off it, and at ``k`` the
    value ``-3`` if ``k`` is on ``c``, else ``3``."""
    from itertools import combinations
    out: List[Tuple[int, ...]] = []
    words = _codewords()
    for c in words:
        if _popcount(c) != 8:
            continue
        supp = [i for i in range(_N) if c >> i & 1]
        for signs in range(1 << 8):
            if _popcount(signs) % 2:
                continue
            x = [0] * _N
            for j, i in enumerate(supp):
                x[i] = -2 if signs >> j & 1 else 2
            out.append(tuple(x))
    for i, j in combinations(range(_N), 2):
        for si in (4, -4):
            for sj in (4, -4):
                x = [0] * _N
                x[i], x[j] = si, sj
                out.append(tuple(x))
    for c in words:
        base = [1 if c >> i & 1 else -1 for i in range(_N)]
        for k in range(_N):
            x = list(base)
            x[k] = -3 if c >> k & 1 else 3
            out.append(tuple(x))
    return out


def _is_leech(x: Tuple[int, ...], codeset: set) -> bool:
    """Membership straight from the definition (Conway's construction)."""
    m = x[0] % 2
    if any(v % 2 != m for v in x):
        return False
    target = 2 if m == 0 else 1
    mask = sum(1 << i for i, v in enumerate(x) if v % 4 == target)
    return mask in codeset and sum(x) % 8 == 4 * m


def minimal_shell_check() -> Dict[str, int]:
    """Every vector of ``minimal_shell_vectors`` tested against the
    definition: how many there are, how many are distinct, how many are in
    the lattice, and how many have squared length 32 (true norm 4)."""
    vecs = minimal_shell_vectors()
    codeset = set(_codewords())
    return {"vectors": len(vecs), "distinct": len(set(vecs)),
            "in_lattice": sum(_is_leech(x, codeset) for x in vecs),
            "norm_32": sum(sum(v * v for v in x) == 32 for x in vecs)}


def proved_shell_sizes() -> Dict[int, int]:
    """The shell sizes ``GLM.LeechShellCount.leech_shell_sizes`` proves, read
    from the Lean file's statement (``{x | IsLeech x ∧ normSq x = N}.ncard =
    V``), keyed by ``t = N / 16``.  Nothing is stored here: an edit to the
    theorem moves this reading."""
    import re
    from pathlib import Path
    path = (Path(__file__).resolve().parents[2] / "lean"
            / SHELL_COUNT_LEAN_FILE)
    text = path.read_text(encoding="utf-8")
    start = text.index("theorem leech_shell_sizes")
    body = text[start:text.index(":= by", start)]
    out: Dict[int, int] = {}
    for n, v in re.findall(r"normSq x = (\d+)\}\.ncard = (\d+)", body):
        out[int(n) // 16] = int(v)
    return out


def proved_shells_check(top: int = 7) -> Dict[str, object]:
    """The proved sizes beside this module's count and the theta series, for
    ``t = 0 .. top``: every row should agree three ways."""
    proved = proved_shell_sizes()
    ours = dict(shells(top))
    mod = modular_shells(top)
    rows = [{"t": t, "proved": proved.get(t), "golay": ours[t],
             "modular": mod[t],
             "agree": proved.get(t) == ours[t] == mod[t]}
            for t in range(top + 1)]
    return {"rows": rows, "proved_rows": sum(1 for r in rows if r["proved"]
                                              is not None),
            "agree": all(r["agree"] for r in rows)}
