"""``glm_universal.engineering.oscillator_junction`` -- the W9/W13 junction,
tried four ways.

Phase 158 (``studies/OSCILLATOR_JUNCTION_STUDY.md``).  The junction between
wave kinematics (W9) and the mass-spring oscillator (W13) is tried four ways
under one rule declared before the measurement (§2):

* **A** ``turn_and_rate`` -- W9/W13 joins ``frequency`` and ``angle`` (as
  Phase 157 shipped it; the control);
* **B** ``rate_only`` -- W9/W13 joins ``frequency`` only; ``angle`` is split
  (**shipped**, :data:`SHIPPED`);
* **C** ``apart`` -- no W9/W13 junction;
* **D** ``reference_circle`` -- W9/W13 joins ``frequency`` and ``angle``, and
  Phase 66's W4/W9 junction is not used in the fifteen-wheel union.

Every variant keeps the fifteen wheels and every other junction; the frame
and the census are those of :mod:`glm_universal.engineering.domains`, which
take the junction table as a parameter (this module reads that module and
does not modify it).  Each variant is measured on three sets (§2.2):

1. **the battery** (:func:`variant_battery`) -- the 32 declared questions of
   ``evaluation/domain_cases.py``, compared as relations up to a positive
   rational multiple;
2. **the preservation set** (:func:`preservation_set`, :func:`preservation`)
   -- every question variant A answers among every two-input question over
   the names of the ten Phase 66 wheels and every three-input question over
   the names of W4 and W9 (24,150 questions); a variant *keeps* a question
   when it answers it with the same relation;
3. **the census** (:func:`variant_census`) -- the census of the union of
   ``DOMAIN_WHEELS_STUDY.md`` §2.5 under the variant's table, its gained rows
   read as that study's post-hoc reading (a one-wheel answer is in-wheel; a
   label matches up to any non-zero multiple), and graded (§2.3,
   :func:`grade_census`): an answer is *oscillator-attributable* when it uses
   W13, *not entailed* when it also uses W4, *entailed* otherwise.

The marks (§2.4): O1 battery (the same answered questions as A, every
refusal, no wrong answer), O2 preservation (nothing lost), O3 no rotor (no
not-entailed oscillator answer), O4 proved (``OscillatorJunction.lean``
holds the theorems of §5 with no ``sorry``).  :func:`choose` applies the
declared choice: among the variants meeting O1 and O2, the fewest
not-entailed answers, then more labelled entailed answers, then fewer
junction names; if none meets both, A stays.

:func:`probes` answers, per variant, the questions §§5 and 7.1 name (the
rotor chain, the reference-circle identity, the wave's period, the shaft
power through a wave, ...) -- seconds, not a mark; :func:`proved_agreement`
checks that the frame's answers agree with the five Lean theorems.

A mark whose set is not measured is reported missed, never assumed: without
``evaluation/domain_cases.py`` (lost in the October 2026 reorganisation) the
battery and the labels are unavailable, so O1 is missed and the labelled /
other split of the entailed answers is ``None``.  :func:`measure` takes the
battery, probes and the Lean check only (seconds); ``measure(v, full=True)``
(:func:`measure_full`) adds the preservation set (minutes) and the census
(about half an hour or more per variant), which is what ``oscjunction
--write`` stores.

Exact and float-free (D7).

*Created 29 October 2026 (Iteration 6, Phase R2) as a stub.*
*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from
studies/OSCILLATOR_JUNCTION_STUDY.md (§§2, 5, 7), the variant definitions in
glm_universal/wheels/junctions/oscillator.py, the CLI handler
``_oscjunction`` in glm_universal/tools.py, tests/test_wheels.py and
RequestProject/GLM/OscillatorJunction.lean (read-only).*
"""
from __future__ import annotations

import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import integrity
from ..wheels import ALL_WHEELS
from ..wheels.junctions.oscillator import (
    VARIANTS, VARIANT_READINGS, SHIPPED, LEAN_FILE, LEAN_THEOREMS,
    junction_for_variant,
)
from . import domains as dmn
from . import wheels as wh

__all__ = [
    "VARIANTS", "VARIANT_READINGS", "SHIPPED", "LEAN_FILE", "LEAN_THEOREMS",
    "junction_for_variant", "variant_tables", "junctions", "PROBES",
    "probes", "PROVED", "proved_agreement", "variant_battery",
    "preservation_questions", "preservation_set", "preservation",
    "variant_census", "grade_census", "marks_of", "choose", "measure",
    "measure_full", "write", "report", "module_digest", "DATA_PATH",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "oscillator_junction.json"
_DATA_PATH = DATA_PATH          # the stub's name, kept

#: The variant every other is compared with (§2.2: the preservation set is
#: what A answers; O1 compares the battery with A's).
CONTROL = "A"


# ===========================================================================
# 1.  THE FOUR JUNCTION TABLES
# ===========================================================================

def variant_tables(variant: str) -> Tuple[Dict[Tuple[str, str], Tuple[str, ...]],
                                          Dict[Tuple[str, str], Tuple[str, ...]]]:
    """``(domain table, Phase 66 table)`` of ``variant`` (§2.1): only the
    W9/W13 entry (and, for D, the W4/W9 junction) differ from the shipped
    tables.  ``KeyError`` on an unknown variant."""
    names = junction_for_variant(variant)          # KeyError when unknown
    domain = {k: tuple(v) for k, v in dmn.DOMAIN_JUNCTION_TABLE.items()
              if k != ("W9", "W13")}
    if names:
        domain[("W9", "W13")] = tuple(names)
    phase66 = {k: tuple(v) for k, v in dmn.PHASE66_JUNCTIONS.items()}
    if variant == "D":
        phase66.pop(("W4", "W9"), None)
    return domain, phase66


def junctions(variant: str) -> Dict[Tuple[str, str], Tuple[str, ...]]:
    """The fifteen-wheel union's junction table under ``variant``."""
    domain, phase66 = variant_tables(variant)
    return dmn.union_junctions(domain, phase66)


def _items(table: Mapping[Tuple[str, str], Sequence[str]]):
    return tuple((a, b, tuple(v)) for (a, b), v in sorted(table.items()))


def _table(items) -> Dict[Tuple[str, str], Tuple[str, ...]]:
    return {(a, b): tuple(v) for a, b, v in items}


def _junction_names(variant: str) -> int:
    """How many names the variant's W9/W13 (and W4/W9) entries join -- the
    last tie-break of §2.4."""
    domain, phase66 = variant_tables(variant)
    return len(domain.get(("W9", "W13"), ())) + len(phase66.get(("W4", "W9"), ()))


# ===========================================================================
# 2.  PROBES AND THE LEAN THEOREMS
# ===========================================================================

#: The questions §§5 and 7.1 name, each ``(label, target, inputs)``.
PROBES: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("rotor chain", "angular_frequency", ("power", "torque")),
    ("rotor chain (angular momentum)", "angular_frequency",
     ("angular_momentum", "moment_of_inertia")),
    ("reference circle", "angular_frequency", ("angular_velocity",)),
    ("spring law through the wave", "spring_constant",
     ("angular_velocity", "mass")),
    ("wave period", "wavelength", ("period", "wave_speed")),
    ("photon period", "energy", ("planck_constant", "period")),
    ("one turn per period", "angular_velocity", ("angle", "period")),
    ("shaft power through a wave", "power", ("angle", "frequency", "torque")),
    ("flywheel through a wave", "angular_momentum",
     ("angle", "frequency", "moment_of_inertia")),
)

#: The five theorems of ``OscillatorJunction.lean`` (§5) as frame questions:
#: ``theorem -> (variant, probe label, answered?)``.
PROVED: Dict[str, Tuple[str, str, bool]] = {
    "rotor_chain_turn_and_rate": ("A", "rotor chain", True),
    "rotor_chain_refused_rate_only": ("B", "rotor chain", False),
    "wave_period_rate_only": ("B", "wave period", True),
    "rotor_chain_refused_reference_circle": ("D", "rotor chain", False),
    "reference_circle_identity": ("D", "reference circle", True),
}


def probes(variant: str) -> List[Dict[str, Any]]:
    """The frame's answer to every probe question under ``variant``."""
    table = junctions(variant)
    out = []
    for label, target, inputs in PROBES:
        a = dmn.derive_domains(target, inputs, table)
        out.append({"probe": label, "target": target, "inputs": list(inputs),
                    "answered": a.answered, "equation": a.equation,
                    "wheels": list(a.wheels),
                    "reason": "" if a.answered else a.reason})
    return out


def proved_agreement(found: Optional[Mapping[str, List[Dict[str, Any]]]] = None
                     ) -> Dict[str, Any]:
    """Whether the frame answers (or refuses) each question a theorem of §5
    is about, as the theorem says.  ``found`` maps a variant to its
    :func:`probes` (computed when absent)."""
    found = dict(found or {})
    rows = []
    for thm, (variant, label, answered) in PROVED.items():
        if variant not in found:
            found[variant] = probes(variant)
        got = next(p for p in found[variant] if p["probe"] == label)
        rows.append({"theorem": thm, "variant": variant, "probe": label,
                     "expected_answered": answered,
                     "answered": got["answered"],
                     "agrees": got["answered"] == answered})
    return {"agree": sum(r["agrees"] for r in rows), "theorems": len(rows),
            "rows": rows}


# ===========================================================================
# 3.  THE BATTERY
# ===========================================================================

def variant_battery(variant: str,
                    cases: Optional[Sequence[Any]] = None) -> Dict[str, Any]:
    """The declared battery under ``variant``'s table
    (:func:`glm_universal.engineering.domains.battery`)."""
    return dmn.battery(cases, junctions=junctions(variant))


def _battery_o1(bat: Mapping[str, Any], control: Mapping[str, Any]) -> bool:
    """O1: the same questions answered with the declared formula as A, every
    declared refusal, no wrong answer (and a battery to read at all)."""
    if not bat.get("available") or not control.get("available"):
        return False
    right = {r["id"] for r in bat["rows"] if r["grade"] == "correct"}
    right_a = {r["id"] for r in control["rows"] if r["grade"] == "correct"}
    t = bat["tally"]
    return (right == right_a and t["wrong"] == 0
            and t["correct_refusals"] == t["refusal_cases"])


# ===========================================================================
# 4.  THE PRESERVATION SET
# ===========================================================================

def preservation_questions() -> List[Tuple[str, Tuple[str, ...]]]:
    """§2.2(2): every two-input question over the names of the ten wheels
    of Phase 66 and every three-input question over the names of W4 and W9,
    as ``(target, inputs)`` (24,150 questions)."""
    ten = ALL_WHEELS[:10]
    n10 = sorted({q for w in ten for q in wh.wheel_quantities(w)})
    w49 = sorted({q for w in ten if w.id in ("W4", "W9")
                  for q in wh.wheel_quantities(w)})
    out: List[Tuple[str, Tuple[str, ...]]] = []
    for t in n10:
        out.extend((t, yz) for yz in
                   itertools.combinations([q for q in n10 if q != t], 2))
    for t in w49:
        out.extend((t, c) for c in
                   itertools.combinations([q for q in w49 if q != t], 3))
    return out


def _answer_row(args) -> Optional[Tuple[str, Tuple[str, ...], str]]:
    target, inputs, items = args
    a = dmn.derive_domains(target, inputs, _table(items))
    return (target, tuple(inputs), a.equation) if a.answered else None


def preservation_set(variant: str = CONTROL, jobs: int = 1,
                     questions: Optional[Sequence[Tuple[str, Tuple[str, ...]]]] = None
                     ) -> List[Tuple[str, Tuple[str, ...], str]]:
    """The questions ``variant`` (A by the declared rule) answers among
    :func:`preservation_questions`, with its equation.  Minutes; ``jobs``
    processes."""
    qs = preservation_questions() if questions is None else list(questions)
    items = _items(junctions(variant))
    work = [(t, ins, items) for t, ins in qs]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(_answer_row, work, chunksize=128))
    else:
        rows = [_answer_row(w) for w in work]
    return [r for r in rows if r is not None]


def preservation(variant: str,
                 reference: Sequence[Tuple[str, Tuple[str, ...], str]]
                 ) -> Dict[str, Any]:
    """How many questions of the preservation set ``variant`` keeps (answers
    with the same relation, up to a positive multiple)."""
    table = junctions(variant)
    lost = []
    for target, inputs, eq in reference:
        a = dmn.derive_domains(target, inputs, table)
        if not (a.answered and dmn.same_relation(a.equation, eq)):
            lost.append({"target": target, "inputs": list(inputs),
                         "shipped": eq,
                         "variant": a.equation if a.answered else None})
    return {"questions": len(reference), "kept": len(reference) - len(lost),
            "lost": len(lost), "lost_rows": lost}


# ===========================================================================
# 5.  THE CENSUS AND ITS GRADING
# ===========================================================================

def variant_census(variant: str, jobs: int = 1,
                   names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """The census of the union (DOMAIN_WHEELS_STUDY.md §2.5) under
    ``variant``'s table -- about half an hour or more over all the names."""
    return dmn.census(junctions=junctions(variant), names=names, jobs=jobs)


def grade_census(cen: Mapping[str, Any],
                 labels: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """§2.3 over a census's gained rows, read post hoc (one-wheel answers
    are in-wheel; a label matches up to any non-zero multiple): the distinct
    oscillator-attributable answers (W13 among the wheels), *not entailed*
    when they also use W4, *entailed* otherwise, the entailed split by
    whether they match a label (``None`` without labels)."""
    if labels is None:
        labels = dmn._labels()
    rows = [r for r in cen.get("rows", []) if not r.get("one_wheel")]

    def labelled(t: str, formula: str) -> Optional[bool]:
        if labels is None:
            return None
        return any(dmn.same_relation_any(f"{t} = {formula}", lab)
                   for lab in labels)

    right = None if labels is None else sum(
        1 for r in rows if labelled(r["t"], r["formula"]))
    distinct: Dict[Tuple[str, str], Tuple[str, ...]] = {}
    for r in rows:
        if "W13" in r["wheels"]:
            distinct.setdefault((r["t"], r["formula"]), tuple(r["wheels"]))
    not_entailed = sorted(f"{t} = {f}" for (t, f), w in distinct.items()
                          if "W4" in w)
    entailed = sorted(((t, f) for (t, f), w in distinct.items()
                       if "W4" not in w))
    if labels is None:
        e_lab = e_other = None
    else:
        e_lab = sum(1 for t, f in entailed if labelled(t, f))
        e_other = len(entailed) - e_lab
    return {"gained_reread": len(rows), "right": right,
            "oscillator": len(distinct),
            "not_entailed": len(not_entailed),
            "not_entailed_answers": not_entailed,
            "entailed": len(entailed),
            "entailed_answers": [f"{t} = {f}" for t, f in entailed],
            "entailed_labelled": e_lab, "entailed_other": e_other,
            "labelled": labels is not None}


# ===========================================================================
# 6.  MARKS, THE CHOICE, MEASURE / WRITE / REPORT
# ===========================================================================

def _lean() -> Dict[str, Any]:
    return dmn.lean_check(LEAN_FILE, LEAN_THEOREMS)


def marks_of(m: Mapping[str, Any]) -> Dict[str, bool]:
    """O1-O4 of one measured variant (a set not measured is missed)."""
    return {"O1": bool(m.get("O1")),
            "O2": m.get("lost") == 0,
            "O3": m.get("not_entailed") == 0,
            "O4": bool(m.get("O4"))}


def choose(measured: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """§2.4: among the variants meeting O1 and O2, the fewest not-entailed
    oscillator answers, then more labelled entailed answers, then fewer
    junction names; if none meets both, A stays."""
    ok = [v for v in VARIANTS if v in measured
          and measured[v].get("O1") and measured[v].get("O2")]
    if not ok:
        return {"chosen": CONTROL,
                "why": "no variant meets O1 and O2 (as measured): A stays"}

    def key(v: str):
        m = measured[v]
        ne = m.get("not_entailed")
        el = m.get("entailed_labelled")
        return (ne if ne is not None else 10 ** 9,
                -(el if el is not None else 0), _junction_names(v),
                VARIANTS.index(v))

    best = min(ok, key=key)
    return {"chosen": best,
            "why": f"meets O1 and O2 among {', '.join(ok)}; fewest "
                   f"not-entailed oscillator answers"}


def measure(variant: str, full: bool = False, jobs: int = 1,
            reference: Optional[Sequence[Tuple[str, Tuple[str, ...], str]]] = None
            ) -> Dict[str, Any]:
    """Measure one variant.  Always: the battery (against A's), the probes
    and the Lean check (seconds).  ``full=True`` adds the preservation set
    (``reference``: A's answers, computed when absent -- minutes) and the
    census (half an hour or more); without it O2 and O3 are not measured
    (missed) and their counts are ``None``.  ``KeyError`` on an unknown
    variant."""
    if variant not in VARIANTS:
        raise KeyError(f"unknown variant {variant!r}")
    bat = variant_battery(variant)
    control = bat if variant == CONTROL else variant_battery(CONTROL)
    lean = _lean()
    out: Dict[str, Any] = {
        "variant": variant, "reading": VARIANT_READINGS[variant],
        "junction": list(junction_for_variant(variant)),
        "battery": dict(bat["tally"]),
        "battery_available": bool(bat.get("available")),
        "battery_rows": bat.get("rows", []),
        "probes": probes(variant),
        "full": bool(full),
        "lost": None, "preservation_questions": None,
        "not_entailed": None, "entailed_labelled": None,
        "entailed_other": None, "census": None,
        "O1": _battery_o1(bat, control),
        "O4": dmn._lean_clean(lean),
    }
    unmeasured = []
    if not bat.get("available"):
        unmeasured.append("O1: " + bat.get("reason", "no battery"))
    if full:
        ref = (preservation_set(CONTROL, jobs=jobs) if reference is None
               else list(reference))
        keep = preservation(variant, ref)
        out["lost"] = keep["lost"]
        out["lost_rows"] = keep["lost_rows"]
        out["preservation_questions"] = len(preservation_questions())
        out["shipped_answers"] = len(ref)
        cen = variant_census(variant, jobs=jobs)
        grade = grade_census(cen)
        out["census"] = {k: v for k, v in cen.items() if k != "rows"}
        out.update({k: grade[k] for k in ("not_entailed", "entailed_labelled",
                                          "entailed_other")})
        out["grading"] = grade
        if not grade["labelled"]:
            unmeasured.append("labels: DOMAIN_LABELS of "
                              "evaluation/domain_cases.py are not present; "
                              "entailed answers are not split")
    else:
        unmeasured.append("O2, O3: the preservation set and the census are "
                          "not taken (measure(v, full=True); oscjunction "
                          "--write)")
    out["O2"] = out["lost"] == 0
    out["O3"] = out["not_entailed"] == 0
    out["unmeasured"] = unmeasured
    return out


def measure_full(variant: str) -> Dict[str, Any]:
    """:func:`measure` with the preservation set and the census (what
    ``oscjunction --write`` stores); picklable for a process pool."""
    return measure(variant, full=True)


_SOURCES: Tuple[str, ...] = (
    "engineering/oscillator_junction.py", "engineering/domains.py",
    "engineering/union.py", "engineering/wheels.py",
    "wheels/junctions/oscillator.py", "wheels/junctions/domain.py",
    "wheels/junctions/phase66.py",
)


def module_digest() -> str:
    root = _HERE.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def write(measurements: Mapping[str, Mapping[str, Any]]) -> str:
    """Store the four variant measurements (from :func:`measure_full`) in
    ``engineering/_data/oscillator_junction.json`` beside the digest of the
    code, with the choice of §2.4 computed from them."""
    variants = {v: dict(measurements[v]) for v in VARIANTS if v in measurements}
    for m in variants.values():
        m.update(marks_of(m))
    data = {
        "variants": variants,
        "choice": choose(variants),
        "shipped": SHIPPED,
        "lean": _lean(),
        "source_digest": module_digest(),
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=1, sort_keys=True,
                                    ensure_ascii=False, default=str) + "\n",
                         encoding="utf-8")
    return str(DATA_PATH)


def _read() -> Optional[Dict[str, Any]]:
    """The stored measurement, or ``None`` if absent or unreadable."""
    if not DATA_PATH.exists():
        return None
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def report() -> Dict[str, Any]:
    """The oscillator-junction report the ``oscjunction`` CLI prints.

    With no stored measurement: ``measured`` False, ``chosen`` the shipped
    variant (B) and the reason.  Otherwise the per-variant measurements
    (``marks``: variant -> its battery tally, lost, not-entailed / entailed
    counts and O1-O4), the choice the declared rule makes from them,
    ``fresh`` (the digest of the code that took them is the code now), the
    preservation-set size and how many of its questions A answers."""
    stored = _read()
    if stored is None:
        return {"measured": False, "chosen": SHIPPED, "shipped": SHIPPED,
                "reason": "the four measurements are not stored "
                          "(python3 -m glm_universal.tools oscjunction "
                          "--write takes them)"}
    variants = stored.get("variants", {})
    marks: Dict[str, Dict[str, Any]] = {}
    for v in VARIANTS:
        m = dict(variants.get(v, {"variant": v, "battery": {"questions": 0},
                                  "lost": None, "not_entailed": None,
                                  "entailed_labelled": None,
                                  "entailed_other": None}))
        m.update(marks_of(m))
        marks[v] = m
    choice = choose(marks)
    ref = marks.get(CONTROL, {})
    return {
        "measured": True,
        "fresh": stored.get("source_digest") == module_digest(),
        "chosen": choice["chosen"], "why": choice["why"],
        "shipped": SHIPPED,
        "preservation_questions": ref.get("preservation_questions"),
        "shipped_answers": ref.get("shipped_answers"),
        "marks": marks,
        "lean": stored.get("lean", {}),
    }
