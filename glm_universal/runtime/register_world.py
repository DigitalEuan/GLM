"""``glm_universal.runtime.register_world`` -- the register against the world.

Round 6 of the order of work (candidate C, Phase 93,
``studies/REGISTER_WORLD_STUDY.md``).  Phase 63 let one question ask whether
one atomic weight was consistent with a 30-row table transcribed by hand.
This module is the whole report: every row of the element register, in the
three fields an outside source holds, compared with that source.

The sources are frozen, not fetched: ``data_objects/_data/world_ciaaw_2024.json``
(CIAAW standard atomic weights, 118 rows) and
``data_objects/_data/world_nist_ie.json`` (NIST ASD ionization energies and
ground-state configurations of the neutral atoms, 108 rows).  Each carries its
URL, its retrieval date and the SHA-256 of the page it was parsed from.

**The register is never written.**  Nothing here opens a file for writing; a
discrepancy is a row of the report, and what to do about it is a person's
decision.  The verdicts and the reading rules are stated, before any code, at
the head of :mod:`glm_universal.evaluation.register_world_cases`; the
soundness of each is proved in ``RequestProject/GLM/RegisterWorld.lean``.

Everything is exact ``Fraction`` arithmetic; no float is constructed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..data_objects import elements as el
from ..integrity import sha256_hex
from ..reasoning.intervals import Interval

__all__ = [
    "VERDICTS", "WORLD_FIELDS", "WorldValue", "WorldCell", "WorldRefusal",
    "world_weights", "world_energies", "world_configurations",
    "occupation", "compare_number", "compare_configuration",
    "cell", "world_table", "counts", "discrepant_rows",
    "molecule_cell", "molecule_table", "mutation_audit",
    "register_digest", "sources", "world_report",
]

_DATA = Path(__file__).resolve().parent.parent / "data_objects" / "_data"
_CIAAW = _DATA / "world_ciaaw_2024.json"
_NIST = _DATA / "world_nist_ie.json"
_REGISTER = _DATA / "elements_118.json"

#: The six verdicts a cell may receive; every cell receives exactly one.
VERDICTS: Tuple[str, ...] = (
    "agrees", "agrees_at_stated_precision", "discrepant",
    "world_silent", "register_silent", "both_silent",
)

#: The fields an outside source is declared for, with the source.
WORLD_FIELDS: Dict[str, str] = {
    "atomic_weight_u": "CIAAW standard atomic weights (2024 table)",
    "ionization_energy_eV": "NIST ASD ionization energies (neutral atoms)",
    "electron_configuration": "NIST ASD ground-state configurations",
}

#: The refusal codes a question about one cell may carry.
REFUSAL_CODES = ("WORLD_SILENT", "REGISTER_SILENT", "STANDARD_UNDECLARED")


class WorldRefusal(ValueError):
    """A question about the world the declared sources cannot answer."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class WorldValue:
    """One outside value: its interval (or configuration text), as published."""

    text: str
    interval: Optional[Interval]
    mark: str = ""

    def describe(self) -> str:
        if self.interval is None:
            return self.text
        if self.text.startswith("["):
            return self.text
        lo, hi = _dec(self.interval.lo), _dec(self.interval.hi)
        kind = {"()": ", a theoretical value", "[]": ", a semi-empirical "
                "value"}.get(self.mark, "")
        return f"{self.text} = [{lo}, {hi}]{kind}"


@dataclass(frozen=True)
class WorldCell:
    """One register cell against the world: the verdict and both sides."""

    symbol: str
    z: int
    field: str
    verdict: str
    register: str
    world: str
    detail: str


def _dec(x: Fraction) -> str:
    """An exact terminating decimal, written without a float."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    den = x.denominator
    places = 0
    while (10 ** places) % den:
        places += 1
        if places > 40:
            return f"{sign}{x}"
    scaled = x.numerator * (10 ** places // den)
    whole, frac = divmod(scaled, 10 ** places)
    if places == 0:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{str(frac).rjust(places, '0')}"


def _plus_minus_last_places(text: str) -> Interval:
    """CIAAW ``v(u)``: ``u`` counts units of the last place of ``v``."""
    m = re.fullmatch(r"(\d+)\.(\d+)\((\d+)\)", text)
    if not m:
        raise ValueError(f"not a CIAAW value: {text!r}")
    value = Fraction(f"{m.group(1)}.{m.group(2)}")
    unit = Fraction(int(m.group(3)), 10 ** len(m.group(2)))
    return Interval(value - unit, value + unit, "CIAAW")


def _quoted_interval(text: str) -> Interval:
    """A decimal with no stated uncertainty, read at the precision quoted."""
    return Interval.as_held(Fraction(text), "quoted")


@lru_cache(maxsize=1)
def world_weights() -> Dict[str, WorldValue]:
    """Symbol -> the CIAAW standard atomic weight, or a silent value."""
    raw = json.loads(_CIAAW.read_text(encoding="utf-8"))
    out: Dict[str, WorldValue] = {}
    for row in raw["elements"]:
        text = row["standard_atomic_weight"]
        if text is None:
            out[row["symbol"]] = WorldValue("no standard atomic weight", None)
            continue
        if text.startswith("["):
            lo, hi = (part.replace(" ", "") for part in text[1:-1].split(","))
            interval = Interval(Fraction(lo), Fraction(hi), "CIAAW")
        else:
            interval = _plus_minus_last_places(text)
        out[row["symbol"]] = WorldValue(text, interval)
    return out


@lru_cache(maxsize=1)
def _nist() -> Dict[str, object]:
    return json.loads(_NIST.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def world_energies() -> Dict[int, WorldValue]:
    """Atomic number -> the NIST first ionization energy (only where held)."""
    out: Dict[int, WorldValue] = {}
    for row in _nist()["spectra"]:  # type: ignore[union-attr]
        value = row["ionization_energy_eV"]
        if value is None:
            continue
        unc = row["uncertainty_eV"]
        interval = (Interval.plus_minus(value, unc, "NIST") if unc
                    else _quoted_interval(value))
        text = value if not unc else f"{value} +/- {unc}"
        out[int(row["z"])] = WorldValue(f"{text} eV", interval,
                                        str(row["mark"]))
    return out


@lru_cache(maxsize=1)
def world_configurations() -> Dict[int, str]:
    """Atomic number -> the NIST ground-state configuration as published."""
    return {int(row["z"]): str(row["ground_shells"])
            for row in _nist()["spectra"]  # type: ignore[union-attr]
            if row["ground_shells"]}


_TAG = re.compile(r"\((?:predicted|calculated)\)")


def occupation(text: str) -> Dict[str, int]:
    """A configuration as the map subshell -> electrons, cores expanded.

    Both spellings are read -- the register's ``[Ar]4s2 3d6`` and the
    database's ``[Ar].3d6.4s2`` -- and the order the subshells are written in
    is not part of the result.  An unreadable token raises ``ValueError``.
    """
    cores: Dict[str, str] = _nist()["cores"]  # type: ignore[assignment]
    body = _TAG.sub("", text).strip()
    out: Dict[str, int] = {}

    def add(token: str) -> None:
        m = re.fullmatch(r"(\d)([spdfg])(\d*)", token)
        if not m:
            raise ValueError(f"not a subshell: {token!r} in {text!r}")
        key = m.group(1) + m.group(2)
        out[key] = out.get(key, 0) + int(m.group(3) or 1)

    m = re.match(r"\[([A-Z][a-z]?)\]", body)
    if m:
        if m.group(1) not in cores:
            raise ValueError(f"no core {m.group(1)!r} is declared")
        for token in cores[m.group(1)].split("."):
            add(token)
        body = body[m.end():]
    for token in re.split(r"[.\s]+", body.strip(". ")):
        if token:
            add(token)
    return out


def compare_number(register: Optional[Fraction],
                   world: Optional[Interval]) -> str:
    """The verdict of one numeric cell (the reading of the declaration)."""
    if world is None:
        return "both_silent" if register is None else "world_silent"
    if register is None:
        return "register_silent"
    if world.contains(register):
        return "agrees"
    if world.overlaps(Interval.as_held(register)):
        return "agrees_at_stated_precision"
    return "discrepant"


def compare_configuration(register: Optional[str],
                          world: Optional[str]) -> str:
    """The verdict of one configuration cell: equal occupations agree."""
    if not world:
        return "both_silent" if not register else "world_silent"
    if not register:
        return "register_silent"
    return "agrees" if occupation(register) == occupation(world) \
        else "discrepant"


def _numeric_cell(element: el.Element, field: str) -> WorldCell:
    held = getattr(element, field)
    held = None if held is None else Fraction(held)
    if field == "atomic_weight_u":
        wv: Optional[WorldValue] = world_weights().get(element.symbol)
    else:
        wv = world_energies().get(element.z)
    interval = None if wv is None else wv.interval
    verdict = compare_number(held, interval)
    register = "none" if held is None else _dec(held)
    world = "none" if wv is None else wv.describe()
    if held is not None:
        hi = Interval.as_held(held)
        register += f" (read at its precision as [{_dec(hi.lo)}, {_dec(hi.hi)}])"
    detail = {
        "agrees": "the register's value lies inside the world's interval",
        "agrees_at_stated_precision": (
            "the register's value lies outside the world's interval, but read "
            "at the precision it is held to it meets it"),
        "discrepant": "no value both allow exists",
        "world_silent": "the world holds no value",
        "register_silent": "the register holds no value",
        "both_silent": "neither holds a value",
    }[verdict]
    if verdict == "discrepant" and held is not None and interval is not None:
        side = "below" if Interval.as_held(held).hi < interval.lo else "above"
        detail = f"the register lies wholly {side} the world: {detail}"
    return WorldCell(element.symbol, element.z, field, verdict, register,
                     world, detail)


def _configuration_cell(element: el.Element) -> WorldCell:
    world = world_configurations().get(element.z)
    verdict = compare_configuration(element.electron_configuration, world)
    detail = {"agrees": "the two occupations are equal",
              "discrepant": "the occupations differ"}.get(verdict, "")
    if verdict == "discrepant":
        a = occupation(element.electron_configuration)
        b = occupation(world or "")
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        detail += ": " + ", ".join(
            f"{k} {a.get(k, 0)} against {b.get(k, 0)}" for k in diff)
    elif verdict == "world_silent":
        detail = "the snapshot holds no configuration for this element"
    return WorldCell(element.symbol, element.z, "electron_configuration",
                     verdict, element.electron_configuration or "none",
                     world or "none", detail)


def cell(symbol: str, field: str) -> WorldCell:
    """One register cell against the world, by symbol and field."""
    if field not in WORLD_FIELDS:
        raise WorldRefusal("STANDARD_UNDECLARED",
                           f"no outside source is declared for {field}; the "
                           f"declared ones are {', '.join(WORLD_FIELDS)}")
    element = el.element_by_symbol(symbol)
    if field == "electron_configuration":
        return _configuration_cell(element)
    return _numeric_cell(element, field)


@lru_cache(maxsize=1)
def world_table() -> Tuple[WorldCell, ...]:
    """Every cell of the three world-checked fields, in atomic-number order."""
    return tuple(cell(element.symbol, field)
                 for element in el.load_element_register()
                 for field in WORLD_FIELDS)


def counts() -> Dict[str, Dict[str, int]]:
    """Field -> verdict -> how many cells received it."""
    out: Dict[str, Dict[str, int]] = {
        f: {v: 0 for v in VERDICTS} for f in WORLD_FIELDS}
    for c in world_table():
        out[c.field][c.verdict] += 1
    return out


def discrepant_rows(field: str) -> Tuple[str, ...]:
    """The symbols whose cell in ``field`` is discrepant, by atomic number."""
    if field not in WORLD_FIELDS and field != "molar_mass_u":
        raise WorldRefusal("STANDARD_UNDECLARED",
                           f"no outside source is declared for {field}")
    if field == "molar_mass_u":
        return tuple(r["name"] for r in molecule_table()
                     if r["verdict"] == "discrepant")
    return tuple(c.symbol for c in world_table()
                 if c.field == field and c.verdict == "discrepant")


# -- molecules: the weights carried through a formula ------------------------

def molecule_cell(name: str) -> Dict[str, object]:
    """A molecule's molar mass against the standard weights of its elements."""
    from ..data_objects import molecules as mo
    molecule = mo.molecule_by_name(name)
    weights = world_weights()
    held_lo = held_hi = world_lo = world_hi = Fraction(0)
    point = Fraction(0)
    silent: List[str] = []
    missing: List[str] = []
    for symbol, count in sorted(molecule.counts.items()):
        w = el.element_by_symbol(symbol).atomic_weight_u
        if w is None:
            missing.append(symbol)
            continue
        w = Fraction(w)
        held = Interval.as_held(w)
        point += count * w
        held_lo += count * held.lo
        held_hi += count * held.hi
        wv = weights.get(symbol)
        if wv is None or wv.interval is None:
            silent.append(symbol)
            continue
        world_lo += count * wv.interval.lo
        world_hi += count * wv.interval.hi
    if missing:
        verdict = "register_silent"
    elif silent:
        verdict = "world_silent"
    else:
        world = Interval(world_lo, world_hi, "CIAAW")
        if world.contains(point):
            verdict = "agrees"
        elif world.overlaps(Interval(held_lo, held_hi)):
            verdict = "agrees_at_stated_precision"
        else:
            verdict = "discrepant"
    return {"name": molecule.name, "formula": molecule.formula,
            "verdict": verdict, "point": point,
            "held": (held_lo, held_hi),
            "world": None if (silent or missing) else (world_lo, world_hi),
            "silent_elements": tuple(silent),
            "elements": tuple(sorted(molecule.counts))}


@lru_cache(maxsize=1)
def molecule_table() -> Tuple[Dict[str, object], ...]:
    """Every molecule of the register, checked through its elements."""
    from ..data_objects import molecules as mo
    return tuple(molecule_cell(m.name) for m in mo.load_molecule_register())


# -- the audits ---------------------------------------------------------------

def mutation_audit() -> Dict[str, object]:
    """R4: injected errors are caught, and the world's own value never is.

    For every numeric cell where both sides hold a value: (a) the register
    value replaced by one held at the same precision but lying wholly above
    the world's interval -- at least two units of the register's last place
    past the world's upper end, with a last digit that is not zero so that it
    is read at that precision -- must be ``discrepant``; (b) the world's
    central value rounded to the register's precision must never be.
    """
    injected = caught = honest = flagged = 0
    missed: List[str] = []
    wrongly: List[str] = []
    for element in el.load_element_register():
        for field in ("atomic_weight_u", "ionization_energy_eV"):
            held = getattr(element, field)
            wv = (world_weights().get(element.symbol)
                  if field == "atomic_weight_u"
                  else world_energies().get(element.z))
            if held is None or wv is None or wv.interval is None:
                continue
            held = Fraction(held)
            h = Interval.as_held(held)
            unit = h.hi - h.lo
            if unit == 0:
                continue
            # (a) a value at the same precision wholly above the world
            k = (wv.interval.hi // unit) + 2
            if k % 10 == 0:         # a trailing zero would widen the reading
                k += 1
            moved = k * unit
            injected += 1
            if compare_number(moved, wv.interval) == "discrepant":
                caught += 1
            else:
                missed.append(f"{element.symbol}.{field}")
            # (b) the world's centre, rounded to the register's precision
            centre = (wv.interval.lo + wv.interval.hi) / 2
            rounded = Fraction(round(centre / unit)) * unit
            honest += 1
            if compare_number(rounded, wv.interval) == "discrepant":
                flagged += 1
                wrongly.append(f"{element.symbol}.{field}")
    return {"injected": injected, "caught": caught, "missed": tuple(missed),
            "honest": honest, "flagged": flagged, "wrongly": tuple(wrongly),
            "holds": caught == injected and flagged == 0}


def register_digest() -> Dict[str, object]:
    """R2: the register file's digest and a digest of every loaded value."""
    raw = _REGISTER.read_bytes()
    values = repr(tuple(
        tuple(getattr(e, f) for f in ("symbol", "electron_configuration",
                                      "atomic_weight_u",
                                      "ionization_energy_eV"))
        for e in el.load_element_register())).encode("utf-8")
    return {"file_sha256": sha256_hex(raw),
            "values_sha256": sha256_hex(values)}


def sources() -> Tuple[Dict[str, object], ...]:
    """The two frozen sources, with what makes each one checkable."""
    out = []
    for path in (_CIAAW, _NIST):
        raw = json.loads(path.read_text(encoding="utf-8"))
        out.append({"file": path.name, "source": raw["source"],
                    "url": raw["url"], "retrieved": raw["retrieved"],
                    "raw_sha256": raw["raw_sha256"], "rows": raw["count"]})
    return tuple(out)


def world_report() -> Dict[str, object]:
    """The whole discrepancy report, recomputed on call."""
    table = world_table()
    by_field = counts()
    listed = {f: tuple({"symbol": c.symbol, "register": c.register,
                        "world": c.world, "detail": c.detail}
                       for c in table if c.field == f
                       and c.verdict in ("discrepant", "register_silent",
                                         "agrees_at_stated_precision"))
              for f in WORLD_FIELDS}
    molecules = molecule_table()
    mol_counts: Dict[str, int] = {v: 0 for v in VERDICTS}
    for row in molecules:
        mol_counts[str(row["verdict"])] += 1
    return {
        "sources": sources(),
        "cells": len(table),
        "accounted": (len(table) == len(el.load_element_register())
                      * len(WORLD_FIELDS)
                      and all(c.verdict in VERDICTS for c in table)),
        "counts": by_field,
        "discrepant": {f: discrepant_rows(f) for f in WORLD_FIELDS},
        "listed": listed,
        "molecules": {"rows": len(molecules), "counts": mol_counts,
                      "discrepant": tuple(r["name"] for r in molecules
                                          if r["verdict"] == "discrepant")},
        "limits": (
            "The register is compared, never corrected: a discrepancy is a "
            "row of this report.  Three fields are checked because those are "
            "the fields the two frozen sources hold; every other field is "
            "refused STANDARD_UNDECLARED rather than guessed at."),
    }
