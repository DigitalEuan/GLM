"""``glm_universal.sandbox.lean_generation`` -- Lean written from a carrier, and
the check that never read it.

What it is
----------
The conversational material supplied with Phase 54 reads a carrier as a **Lean
theorem shape**: it quantises the carrier to a lattice point with the shipped
:mod:`glm_universal.reasoning.lean_address`, reads the point back as the 24
structural counts of a declaration -- how many quantifiers, how many
implications, what kind of declaration -- and emits Lean source with those
counts.  Twelve of those declarations are in the material as
``lean/glm_generated_theorems.lean``, each ending ``:= by sorry``.

It also ships a ``round_trip_check`` that reports the generation *faithful*.

Why it is in the sandbox
------------------------
Because neither of the two things it claims is true, and because directive
**D8** says what the third thing would have to be.  This module is the
generator restated so that the claims can be measured rather than repeated,
with the promotion checklist at the bottom saying what would have to hold for
any of it to leave the sandbox.

**The supplied check never reads what was generated.**  Its own comment says
so -- *we can't actually parse the source without lean files set up* -- and
what it does instead is re-quantise the original carrier and compare the
result with the reading it generated *from*.  That comparison is between a
value and itself.  :func:`supplied_check_is_vacuous` makes the point the only
way worth making it: it runs the same check against a generator that emits the
empty string, and the check still passes.

**The real round trip fails.**  :func:`round_trip` writes the generated source
out, reads it back with the shipped ``lean_address.parse_file`` -- the same
reader the whole address book is built on -- and re-takes the 24 counts.  On
the twelve carriers the supplied file was generated from, **0 of 12** come
back as the reading they were generated from, agreeing on between 14 and 21 of
the 24 coordinates, and only **1 of the 12** readings is one a declaration
could actually have.  Three causes, all structural: the reading of a
physical carrier is not in the range a declaration's counts live in (kind
codes of 8, 16 and 20 where only 1-5 name a declaration kind, and negative
quantifier counts), the generator takes the absolute value of a negative count
rather than refusing it, and the counts it does not control -- statement size,
parenthesis depth, namespace depth -- are decided by the text it happens to
write.

**And none of the twelve is a theorem.**  Elaborating the supplied file
against this repository's Mathlib gives **44 errors on 12 lines, one line per
declaration**: `(x1 : α)` used where a type is expected, `∑ i, f i` as a
proposition, `P`, `Q`, `f` and `n` free.  The command is in the study; it is
not run from the test suite because a Mathlib elaboration is minutes, not
milliseconds.

    cd .. && cp source_material/conversation_experiment/lean/glm_generated_theorems.lean /tmp/gen.lean
    sed -i '1i import Mathlib' /tmp/gen.lean && lake env lean /tmp/gen.lean

What would earn a promotion
---------------------------
D8 is the standing rule: where a Lean file and a Python module disagree, the
Lean file is the specification.  A generator of Lean is therefore a generator
of *specifications*, and the checklist below says what that costs: the source
must parse, the reading must round-trip, the declaration must elaborate, and
at least one generated statement must be **proved** -- a `sorry` is a claim
that has not been made.  Every line is computed here except the elaboration
one, which is reported as unmeasured unless a runner is supplied, because
pretending to have measured it would be the same mistake the supplied check
makes.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..reasoning import lean_address as la
from ..reasoning import metric

__all__ = [
    "SUPPLIED_NAMES", "KIND_NAMES", "Generated",
    "reading_of", "generate", "parse_back", "round_trip",
    "supplied_check", "supplied_check_is_vacuous",
    "promotion_checklist", "lean_generation_report",
]

#: The twelve carriers the supplied ``glm_generated_theorems.lean`` was
#: generated from, in the order they appear there.
SUPPLIED_NAMES: Tuple[str, ...] = (
    "energy", "force", "speed_of_light", "mass", "momentum", "curvature",
    "planck_constant", "gravitational_constant", "wavelength", "frequency",
    "boltzmann_constant", "action",
)

#: The inverse of ``lean_address.KIND_CODE``, as the supplied generator has
#: it.  Only 1-5 name a kind; everything else silently becomes a theorem, and
#: that silence is one of the things measured here.
KIND_NAMES: Dict[int, str] = {
    1: "theorem", 2: "def", 3: "structure", 4: "instance", 5: "example",
}


@dataclass(frozen=True)
class Generated:
    """One carrier, written out as a declaration and read back."""

    name: str
    reading: Dict[str, int]      # what the carrier was read as
    source: str                  # the Lean that was written
    parsed: int                  # how many declarations came back
    recovered: Dict[str, int]    # what reading the written text has
    agreeing: int                # coordinates that survived the trip
    exact: bool                  # all 24 of them
    in_range: bool               # the reading names a kind and has no
                                 # negative count


def reading_of(session, name: str) -> Optional[Dict[str, int]]:
    """Read a carrier as a declaration's 24 counts, as the material does."""
    try:
        obj = session.resolve(name)
    except Exception:
        return None
    vector = tuple(int(value) for value in metric.as_exact_vector(obj.carrier))
    point = la.quantise(vector)
    reading = la.describe_address(point)["reading"]
    return {key: int(value) for key, value in reading.items()}


def _in_range(reading: Dict[str, int]) -> bool:
    """Whether a reading is one a declaration could actually have."""
    return (reading["kind"] in KIND_NAMES
            and all(value >= 0 for value in reading.values()))


def generate(name: str, reading: Dict[str, int]) -> str:
    """The supplied generator, restated: a declaration with those counts.

    Kept faithful to the material, absolute values and all, because what is
    being measured is the thing that was supplied rather than an improved
    version of it.
    """
    binders: List[str] = []
    for i in range(abs(reading["forall"])):
        binders.append(f"(x{i + 1} : ℕ)" if reading["nat"] > 0
                       else f"(x{i + 1} : α)")
    for i in range(abs(reading["exists"])):
        binders.append(f"(y{i + 1} : β)")
    parts: List[str] = []
    for i in range(abs(reading["equality"])):
        parts.append(f"x{i + 1} = x{i + 1}")
    for i in range(abs(reading["implication"])):
        left = min(i + 1, max(1, abs(reading["forall"])))
        right = min(i + 1, max(1, abs(reading["exists"])))
        inner = f"x{left} → y{right}"
        parts.append(f"(¬({inner}))" if reading["implication"] < 0
                     else f"({inner})")
    for i in range(abs(reading["iff"])):
        parts.append(f"(x{i + 1} ↔ y{i + 1})")
    parts.extend("(P ∧ Q)" for _ in range(abs(reading["conjunction"])))
    parts.extend("(P ∨ Q)" for _ in range(abs(reading["disjunction"])))
    parts.extend("¬P" for _ in range(abs(reading["negation"])))
    parts.extend("(∑ i, f i)" for _ in range(abs(reading["big_operator"])))
    parts.extend("(n > 0)" for _ in range(abs(reading["numeral"])))
    body = parts[0] if parts else "True"
    for part in parts[1:]:
        body = f"({body} ∧ {part})"
    kind = KIND_NAMES.get(reading["kind"], "theorem")
    namespace = (f"GLM{reading['namespace_depth']}"
                 if reading["namespace_depth"] > 0 else "")
    lines: List[str] = []
    if namespace:
        lines.append(f"namespace {namespace}")
    lines.append(f"{kind} {name}_stmt {' '.join(binders)} : {body} := "
                 f"by sorry")
    if namespace:
        lines.append(f"end {namespace}")
    return "\n".join(lines) + "\n"


def parse_back(source: str) -> Tuple[int, Optional[Dict[str, int]]]:
    """Read generated source with the shipped reader, and re-take its counts.

    Returns how many declarations the reader found and the 24 counts of the
    first, which is the whole of the real round trip: the same reader the
    address book is built on, applied to the text that was written.
    """
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "generated.lean"
        path.write_text(source, encoding="utf-8")
        declarations = la.parse_file(path)
    if not declarations:
        return 0, None
    features = la.features_of(declarations[0])
    return len(declarations), {name: int(value) for name, value
                               in zip(la.FEATURE_NAMES, features)}


def round_trip(session, name: str) -> Optional[Generated]:
    """Generate, write, read back, and compare -- the check that was missing."""
    reading = reading_of(session, name)
    if reading is None:
        return None
    source = generate(name, reading)
    parsed, recovered = parse_back(source)
    recovered = recovered or {}
    agreeing = sum(1 for key in la.FEATURE_NAMES
                   if recovered.get(key) == reading.get(key))
    return Generated(
        name=name, reading=reading, source=source, parsed=parsed,
        recovered=recovered, agreeing=agreeing,
        exact=agreeing == len(la.FEATURE_NAMES),
        in_range=_in_range(reading))


# ===========================================================================
#  THE SUPPLIED CHECK, AND WHY IT PASSES
# ===========================================================================

def supplied_check(session, name: str,
                   generator: Optional[Callable[[str, Dict[str, int]], str]]
                   = None) -> Dict[str, object]:
    """The supplied ``round_trip_check``, restated exactly.

    It generates a source, then re-quantises the **carrier** and compares six
    fields of that reading with the reading it generated from.  The generated
    text is never read, which is why ``generator`` can be anything at all.
    """
    generator = generator or generate
    reading = reading_of(session, name)
    if reading is None:
        return {"name": name, "passes": False, "reason": "unresolved"}
    source = generator(name, reading)
    again = reading_of(session, name)
    matches = all(again is not None and again[key] == reading[key]
                  for key in ("forall", "exists", "implication", "iff",
                              "kind", "namespace_depth"))
    return {"name": name, "passes": matches, "source_length": len(source)}


def supplied_check_is_vacuous(session,
                              names: Sequence[str] = SUPPLIED_NAMES
                              ) -> Dict[str, object]:
    """Run the supplied check against a generator that emits nothing.

    A check that a generator is faithful, which passes for a generator that
    writes the empty string, is measuring something other than the generator.
    """
    honest = tuple(supplied_check(session, name) for name in names)
    empty = tuple(supplied_check(session, name,
                                 generator=lambda _n, _r: "")
                  for name in names)
    return {
        "names": tuple(names),
        "passes_as_supplied": sum(1 for row in honest if row["passes"]),
        "passes_with_empty_generator": sum(1 for row in empty
                                           if row["passes"]),
        "vacuous": (sum(1 for row in honest if row["passes"])
                    == sum(1 for row in empty if row["passes"])),
    }


# ===========================================================================
#  THE PROMOTION CHECKLIST -- computed, not asserted
# ===========================================================================

def promotion_checklist(rows: Optional[Sequence[Generated]] = None,
                        elaborates: Optional[int] = None,
                        proved: Optional[int] = None,
                        session=None) -> Dict[str, object]:
    """What would have to hold for a Lean generator to leave the sandbox.

    ``elaborates`` and ``proved`` are counts a caller supplies from a real
    Lean run; left out, they are reported as unmeasured and their lines are
    false, because the failure this module exists to record is a check that
    reported a result it had not taken.
    """
    rows = list(rows if rows is not None else generated_rows(session))
    total = len(rows)
    checks = {
        "the_reading_is_one_a_declaration_could_have":
            bool(rows) and all(row.in_range for row in rows),
        "the_generated_source_parses_as_one_declaration":
            bool(rows) and all(row.parsed == 1 for row in rows),
        "the_reading_survives_the_round_trip":
            bool(rows) and all(row.exact for row in rows),
        "every_declaration_elaborates":
            elaborates is not None and elaborates == total and total > 0,
        "at_least_one_generated_statement_is_proved":
            proved is not None and proved > 0,
    }
    return {
        "checks": checks,
        "order": tuple(checks),
        "declarations": total,
        "in_range": sum(1 for row in rows if row.in_range),
        "parsed": sum(1 for row in rows if row.parsed == 1),
        "round_tripped": sum(1 for row in rows if row.exact),
        "elaborates": elaborates,
        "proved": proved,
        "ready": all(checks.values()),
        "rule": ("A generator of Lean is a generator of specifications (D8). "
                 "It ships when every line above is true; while any is false "
                 "it stays in the sandbox, and a `sorry` is not a claim that "
                 "has been made."),
    }


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


def generated_rows(session=None,
                   names: Sequence[str] = SUPPLIED_NAMES
                   ) -> Tuple[Generated, ...]:
    """The round trip, taken over the twelve supplied carriers."""
    session = session or _session()
    return tuple(row for row in (round_trip(session, name) for name in names)
                 if row is not None)


def lean_generation_report(session=None) -> Dict[str, object]:
    """What the generator does, what the supplied check does, and the gap."""
    session = session or _session()
    rows = generated_rows(session)
    vacuous = supplied_check_is_vacuous(session)
    checklist = promotion_checklist(rows)
    agreeing = [row.agreeing for row in rows]
    return {
        "names": SUPPLIED_NAMES,
        "declarations": len(rows),
        "coordinates": len(la.FEATURE_NAMES),
        "in_range": sum(1 for row in rows if row.in_range),
        "parsed": sum(1 for row in rows if row.parsed == 1),
        "round_tripped": sum(1 for row in rows if row.exact),
        "least_agreement": min(agreeing, default=0),
        "most_agreement": max(agreeing, default=0),
        "total_agreement": sum(agreeing),
        "supplied_check": vacuous,
        "checklist": checklist,
        "rows": tuple({
            "name": row.name, "parsed": row.parsed,
            "agreeing": row.agreeing, "exact": row.exact,
            "in_range": row.in_range,
            "kind": row.reading["kind"],
            "forall": row.reading["forall"],
            "namespace_depth": row.reading["namespace_depth"],
        } for row in rows),
        "verdict": (
            f"of the {len(rows)} carriers the supplied file was generated "
            f"from, the reading of "
            f"{sum(1 for row in rows if row.in_range)} is one a "
            f"declaration could actually have, and "
            f"{sum(1 for row in rows if row.exact)} survive the round trip: "
            f"written out and read back with the shipped reader, they agree "
            f"with the reading they were generated from on between "
            f"{min(agreeing, default=0)} and {max(agreeing, default=0)} of "
            f"the {len(la.FEATURE_NAMES)} coordinates. The supplied check "
            f"reports {vacuous['passes_as_supplied']} of "
            f"{len(SUPPLIED_NAMES)} faithful, and reports "
            f"{vacuous['passes_with_empty_generator']} of "
            f"{len(SUPPLIED_NAMES)} faithful for a generator that emits the "
            f"empty string, because it never reads what was generated."),
        "caveat": (
            "elaboration is not measured here: run the command in this "
            "module's docstring. Taken by hand at this round against the "
            "repository's Mathlib, the supplied file gives 44 errors on 12 "
            "lines -- one line per declaration -- so none of the twelve is a "
            "statement, let alone a theorem. Nothing in this module is "
            "imported by the shipped package."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = lean_generation_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['name']:<26} agrees on {row['agreeing']:>2} of 24  "
              f"{'in range' if row['in_range'] else 'reading out of range'}")
