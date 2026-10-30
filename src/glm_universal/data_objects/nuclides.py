"""``glm_universal.data_objects.nuclides`` -- the nuclide register (Phase 120).

What it holds
-------------
The ground state of every nuclide in two outside tables, joined on
``(Z, A)`` and frozen into ``_data/world_ame2020.json``:

* **AME2020** -- the Atomic Mass Evaluation 2020, ``mass_1.mas20.txt``
  (W. J. Huang, M. Wang, F. G. Kondev, G. Audi and S. Naimi, Chinese Physics
  C45, 030002, and M. Wang et al., C45, 030003, 2021): the **mass excess**
  ``Delta = (M - A u) c^2`` in keV, stored as the table's decimal string and
  read as an exact :class:`~fractions.Fraction`;
* **NUBASE2020** -- ``nubase_4.mas20.txt`` (F. G. Kondev, M. Wang,
  W. J. Huang, S. Naimi and G. Audi, Chinese Physics C45, 030001, 2021): the
  **half-life** as printed (``stbl`` for stable, ``p-unst`` for particle
  unstable, otherwise a value and a unit) and the **decay modes**.

Both files were fetched from the IAEA Nuclear Data Section's AMDC mirror and
frozen with the SHA-256 of each raw file, the URL and the retrieval date; the
register is never re-fetched at run time.

Reading rules
-------------
* A value the table marks ``#`` comes from systematics, not measurement; it
  is kept, and its row carries ``estimated = True``.  Nothing here treats an
  estimated mass as a measured one unless the caller asks for it.
* Mass excesses are of **neutral atoms**, so a beta-minus or electron-capture
  Q-value is the difference of two mass excesses, and a binding energy is
  ``Z Delta(1H) + N Delta(n) - Delta(Z, A)``; both are exact.
* No float is constructed (D7): every number is an ``int`` or a
  ``Fraction`` read from a decimal string.

The parser that produced the frozen file is :func:`parse_ame` and
:func:`parse_nubase`, kept here so the reading can be repeated from the raw
files; the run-time path reads only the frozen JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

__all__ = ["Nuclide", "REGISTER_FILE", "register", "nuclide", "sources",
           "mass_excess", "binding", "binding_per_nucleon", "q_value",
           "separation_n", "is_stable", "half_life_seconds", "isotopes",
           "isobars", "parse_ame", "parse_nubase", "freeze", "dec",
           "SYMBOLS"]

REGISTER_FILE = Path(__file__).resolve().parent / "_data" / "world_ame2020.json"


@dataclass(frozen=True)
class Nuclide:
    """One ground state: its numbers as printed and their exact readings."""

    z: int
    a: int
    symbol: str
    mass_excess_text: Optional[str]      # keV, as printed (no '#')
    estimated: bool                      # '#' in AME2020: from systematics
    half_life: str                       # 'stbl', 'p-unst', '' or a value
    unit: str                            # NUBASE unit ('s', 'ms', 'y', ...)
    decay: str                           # NUBASE decay modes, as printed

    @property
    def n(self) -> int:
        return self.a - self.z

    @property
    def name(self) -> str:
        return f"{self.a}{self.symbol}"

    @property
    def mass_excess(self) -> Optional[Fraction]:
        return None if self.mass_excess_text is None else \
            Fraction(self.mass_excess_text)

    def row(self) -> Tuple:
        return (self.z, self.a, self.symbol, self.mass_excess_text,
                1 if self.estimated else 0, self.half_life, self.unit,
                self.decay)


@lru_cache(maxsize=1)
def _frozen() -> dict:
    return json.loads(REGISTER_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def register() -> Dict[Tuple[int, int], Nuclide]:
    """Every ground state, keyed ``(Z, A)``."""
    out: Dict[Tuple[int, int], Nuclide] = {}
    for z, a, sym, me, est, hl, unit, decay in _frozen()["nuclides"]:
        out[(z, a)] = Nuclide(z, a, sym, me, bool(est), hl, unit, decay)
    return out


def sources() -> List[dict]:
    """The two outside sources, with URL, retrieval date and raw SHA-256."""
    return list(_frozen()["sources"])


#: Element symbols by Z, as the tables print them (``n`` for the neutron).
@lru_cache(maxsize=1)
def _symbols() -> Dict[int, str]:
    return {k[0]: v.symbol for k, v in register().items()}


def SYMBOLS() -> Dict[int, str]:
    return dict(_symbols())


def nuclide(z: int, a: int) -> Nuclide:
    try:
        return register()[(z, a)]
    except KeyError:
        raise KeyError(f"no ground state Z={z}, A={a} in AME2020/NUBASE2020")


def mass_excess(z: int, a: int, allow_estimated: bool = False) -> Fraction:
    """``Delta(Z, A)`` in keV, exact.  An estimated value raises unless
    ``allow_estimated``."""
    nu = nuclide(z, a)
    if nu.mass_excess is None:
        raise KeyError(f"{nu.name}: no mass excess in AME2020")
    if nu.estimated and not allow_estimated:
        raise ValueError(f"{nu.name}: mass excess from systematics (#)")
    return nu.mass_excess


def binding(z: int, a: int, allow_estimated: bool = False) -> Fraction:
    """Total binding energy in keV: ``Z Delta(1H) + N Delta(n) - Delta``."""
    return (z * mass_excess(1, 1) + (a - z) * mass_excess(0, 1)
            - mass_excess(z, a, allow_estimated))


def binding_per_nucleon(z: int, a: int, allow_estimated: bool = False
                        ) -> Fraction:
    return binding(z, a, allow_estimated) / a


def q_value(parent: Tuple[int, int], *daughters: Tuple[int, int],
            allow_estimated: bool = False) -> Fraction:
    """``Delta(parent) - sum Delta(daughters)`` in keV (neutral atoms)."""
    return mass_excess(*parent, allow_estimated=allow_estimated) - sum(
        (mass_excess(*d, allow_estimated=allow_estimated)
         for d in daughters), Fraction(0))


def separation_n(z: int, a: int, allow_estimated: bool = False) -> Fraction:
    """One-neutron separation energy ``S_n(Z, A) = B(Z, A) - B(Z, A - 1)``."""
    return binding(z, a, allow_estimated) - binding(z, a - 1, allow_estimated)


def is_stable(z: int, a: int) -> bool:
    """NUBASE2020 prints ``stbl``."""
    nu = register().get((z, a))
    return bool(nu) and nu.half_life == "stbl"


#: Seconds per NUBASE unit, exact.
_YEAR = Fraction(3652422, 10000) * 86400   # NUBASE's year: 365.2422 days
_UNIT_SECONDS: Dict[str, Fraction] = {
    "ys": Fraction(1, 10 ** 24), "zs": Fraction(1, 10 ** 21),
    "as": Fraction(1, 10 ** 18), "fs": Fraction(1, 10 ** 15),
    "ps": Fraction(1, 10 ** 12), "ns": Fraction(1, 10 ** 9),
    "us": Fraction(1, 10 ** 6), "ms": Fraction(1, 10 ** 3),
    "s": Fraction(1), "m": Fraction(60), "h": Fraction(3600),
    "d": Fraction(86400), "y": _YEAR, "ky": _YEAR * 10 ** 3,
    "My": _YEAR * 10 ** 6, "Gy": _YEAR * 10 ** 9, "Ty": _YEAR * 10 ** 12,
    "Py": _YEAR * 10 ** 15, "Ey": _YEAR * 10 ** 18, "Zy": _YEAR * 10 ** 21,
    "Yy": _YEAR * 10 ** 24,
}


def dec(text: str) -> Fraction:
    """An exact reading of a printed decimal, with an optional exponent."""
    t = text.strip().replace("#", "")
    if not t:
        raise ValueError("empty number")
    if "e" in t.lower():
        m, e = t.lower().split("e")
        return Fraction(m) * Fraction(10) ** int(e)
    return Fraction(t)


def half_life_seconds(z: int, a: int) -> Optional[Fraction]:
    """The half-life in seconds, exact; ``None`` for stable, particle
    unstable, unmeasured, or a value with a bound sign (``>``, ``<``)."""
    nu = register().get((z, a))
    if nu is None or nu.half_life in ("stbl", "p-unst", ""):
        return None
    t = nu.half_life.replace("#", "").strip()
    if not t or t[0] in "<>~" or nu.unit not in _UNIT_SECONDS:
        return None
    try:
        return dec(t) * _UNIT_SECONDS[nu.unit]
    except (ValueError, ZeroDivisionError):
        return None


def isotopes(z: int) -> List[Nuclide]:
    return sorted((v for k, v in register().items() if k[0] == z),
                  key=lambda v: v.a)


def isobars(a: int) -> List[Nuclide]:
    return sorted((v for k, v in register().items() if k[1] == a),
                  key=lambda v: v.z)


# ---------------------------------------------------------------------------
# The parser that produced the frozen file (not on the run-time path).
# ---------------------------------------------------------------------------

def parse_ame(text: str) -> Dict[Tuple[int, int], Tuple[str, str, bool]]:
    """``(Z, A) -> (symbol, mass excess text, estimated)`` from
    ``mass_1.mas20.txt`` (fixed columns, after the header)."""
    out: Dict[Tuple[int, int], Tuple[str, str, bool]] = {}
    started = False
    for ln in text.splitlines():
        if "MASS EXCESS" in ln and "BINDING" in ln:
            started = True
            continue
        if not started or len(ln) < 60:
            continue
        try:
            z, a = int(ln[9:14]), int(ln[14:19])
        except ValueError:
            continue
        sym = ln[20:22].strip()
        me = ln[28:42].strip()
        if not me or not sym:
            continue
        out[(z, a)] = (sym, me.replace("#", ""), "#" in me)
    return out


def parse_nubase(text: str) -> Dict[Tuple[int, int], Tuple[str, str, str, str]]:
    """``(Z, A) -> (symbol, half-life, unit, decay modes)`` for the ground
    states (``i = 0``) of ``nubase_4.mas20.txt``."""
    out: Dict[Tuple[int, int], Tuple[str, str, str, str]] = {}
    for ln in text.splitlines():
        if ln.startswith("#") or len(ln) < 80:
            continue
        if ln[7] != "0":
            continue
        a, z = int(ln[0:3]), int(ln[4:7])
        name = ln[11:16].strip()
        sym = name.lstrip("0123456789")
        hl = ln[69:78].strip()
        unit = ln[78:80].strip()
        decay = ln[119:209].strip() if len(ln) > 119 else ""
        out[(z, a)] = (sym, hl, unit, decay)
    return out


def freeze(ame_text: str, nubase_text: str,
           sources_meta: Iterable[dict]) -> dict:
    """The frozen register: every ``(Z, A)`` either table holds."""
    ame, nub = parse_ame(ame_text), parse_nubase(nubase_text)
    rows = []
    for key in sorted(set(ame) | set(nub)):
        z, a = key
        sym = (ame.get(key) or nub.get(key))[0]
        me = ame[key][1] if key in ame else None
        est = ame[key][2] if key in ame else False
        hl, unit, decay = nub[key][1:] if key in nub else ("", "", "")
        rows.append([z, a, sym, me, 1 if est else 0, hl, unit, decay])
    return {
        "source": "AME2020 (mass_1.mas20.txt) and NUBASE2020 "
                  "(nubase_4.mas20.txt), ground states, joined on (Z, A)",
        "sources": list(sources_meta),
        "reading": "mass excess in keV of the neutral atom, as printed; "
                   "estimated = 1 where the table prints '#' (systematics); "
                   "half-life as printed by NUBASE2020 ('stbl' stable, "
                   "'p-unst' particle unstable), unit as printed; decay "
                   "modes as printed",
        "count": len(rows),
        "nuclides": rows,
    }
