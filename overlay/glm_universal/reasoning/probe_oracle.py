"""``glm_universal.reasoning.probe_oracle`` -- the smallest experiment against
blocker 1: hand-write the query each probe question *should* become, and see
how many the existing solvers then answer.

Why this module exists
----------------------
:mod:`glm_universal.reasoning.blockers` measures how much open natural
language the system takes at all, and the answer is: almost none.  Its
verdict is a single number -- 2 correct, 1 wrong, 17 refused of 20 -- and that
number cannot tell two very different failures apart:

* the question was *not understood*, and a solver that could answer it exists;
* the question was understood perfectly well and **nothing here can answer
  it**.

The experiment blocker 1 declares is the one run here.  For each of the twenty
pre-registered questions of :data:`glm_universal.reasoning.blockers.PROBE` a
**translation** is written by hand into the system's own query grammar, and
the translation is asked instead of the English.  Nothing is built, no parser
is written, and no solver is changed: the only thing added is a person who
knows the grammar.

What the experiment separates
-----------------------------
Every question lands in exactly one of three classes, and the class is
*computed* rather than asserted:

``parsed``
    a query in the existing grammar answers it, with the declared fragment in
    the declared field.  The whole of the gap between the English and the
    answer was the parser.
``surface``
    no query in the grammar answers it, but a **witness** -- a shipped
    register row, or a shipped function -- holds the answer.  The fact is
    here; no query kind returns it.  The gap is a missing surface, not a
    missing capability, and it is the cheaper of the two to close.
``absent``
    no query answers it and no witness holds it.  The refusal is the right
    behaviour, and a parser would not change it.

The reading that matters is the *split*: it says whether the next round should
buy a parser or a query kind, and it says so in integers.

What is declared, and what is measured
--------------------------------------
Declared here, before the run: the translation for each question, the **locus**
-- which field of the solution must carry the declared fragment, so that a
fragment matching somewhere irrelevant does not score -- and the witness with
the kind of thing it is.  Measured: whether the session answers, whether the
fragment is at the locus, and what the witness holds.

The locus rule is the reason this measurement is worth more than the probe's.
The probe scores a fragment anywhere in the answer or in any value of the
solution's ``expected`` mapping, so ``6`` scores against ``0.6667`` and
``energy`` scores against an echo of the question.  Here the fragment must
appear in the one field that would be *answering the question asked*.

Exactness
---------
Every quantity is an integer or a :class:`~fractions.Fraction`, and the
decimal renderings are exact.  No float is constructed anywhere in this
module.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .blockers import PROBE, ProbeQuestion

__all__ = [
    "Translation", "TRANSLATIONS", "WITNESS_KINDS",
    "witness_value", "translate", "oracle_report",
    "CLASSES", "class_of",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE DECLARED TRANSLATIONS
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Translation:
    """One probe question, written into the system's own query grammar.

    ``query``
        the query a person who knew the grammar would write, or ``None`` when
        the grammar has no way to ask it.  A translation may not smuggle the
        answer into the question: ``relate velocity position`` is not a
        translation of *what is velocity the derivative of?*, because it
        supplies the word the question asks for.
    ``locus``
        ``"answer"``, or the key of the solution's ``expected`` mapping that
        must carry the declared fragment.  Declared before the run.
    ``witness``
        the name of the entry in :data:`WITNESSES` that holds the answer
        independently of any query, or ``None`` when nothing holds it.
    ``witness_kind``
        ``register`` (a shipped register row and field), ``module`` (a shipped
        function's return value), ``source`` (the package's own text, read
        with the machinery the package already ships) or ``none``.
    """

    key: str
    query: Optional[str]
    locus: Optional[str]
    witness: Optional[str]
    witness_kind: str
    note: str


#: What a witness may be.  The order is from strongest to weakest: a register
#: row is data the system is built on, a module return value is something it
#: computes on demand, and a source scan is text it ships but holds in no
#: structure.
WITNESS_KINDS: Tuple[str, ...] = ("register", "module", "source", "none")


#: The twenty translations, one per question of
#: :data:`glm_universal.reasoning.blockers.PROBE`, in the same order.
TRANSLATIONS: Tuple[Translation, ...] = (
    # ── natural language ────────────────────────────────────────────────
    Translation("nl-meaning", "meaning of velocity", "answer", None, "none",
                "the `meaning` kind is exactly this question; only the "
                "English phrasing was in the way"),
    Translation("nl-relation", None, None, "velocity-derivative-of",
                "register",
                "the lexicon holds the triple ('velocity', 'derivative_of', "
                "'position') as an attribute of the entry.  No query kind "
                "takes a relation name and one end of it and returns the "
                "other: `relate a b` needs both ends, which is the question "
                "already answered"),
    Translation("nl-compare", None, None, "abstractness-energy-water",
                "register",
                "coordinate 0 of the lexicon carrier is `abstract_concrete`, "
                "0 = abstract and 1 = concrete, and it is 1/4 for energy "
                "against 1 for water.  The comparison is a subtraction the "
                "register supports and no query kind performs: `comparative` "
                "reads degree words against measure scales, not lexicon "
                "primitives"),
    Translation("nl-unknown", None, None, None, "none",
                "nothing here holds why the sky is blue, and the declared "
                "right outcome is the refusal the system gives"),
    # ── mathematics ─────────────────────────────────────────────────────
    Translation("math-add", "approximate 2+2 to 2 places", "answer", None,
                "none",
                "the `real` kind reads the sum as a process and settles it "
                "exactly"),
    Translation("math-prime", None, None, None, "none",
                "no register holds primality and no solver decides it; the "
                "arithmetic is trivial and the system has no operation that "
                "performs it, which is blocker 3 rather than blocker 1"),
    Translation("math-gcd", None, None, None, "none",
                "the same again for a two-argument function.  `approximate "
                "12/18 to 4 places` is not a translation: it answers a "
                "different question, and it is the kind of near-miss the "
                "locus rule is here to refuse"),
    Translation("math-ratio",
                "derive prime_limit of perfect_fifth in harmonics", "value",
                None, "none",
                "the `derive` kind answers it off the harmonics description, "
                "with the rule that computed it reported beside the value"),
    # ── physics ─────────────────────────────────────────────────────────
    Translation("phys-constant", "describe speed_of_light", "name", None,
                "none",
                "the easiest case: a register lookup by exact name, and the "
                "one question the English probe also gets right"),
    Translation("phys-dimension", "meaning of force", "answer", None, "none",
                "the `meaning` kind returns the dimensional formula; the "
                "English asking was refused for its phrasing alone"),
    Translation("phys-derive", "force = mass * acceleration", "holds", None,
                "none",
                "the `verify` kind audits the claim across planes.  This is "
                "the one measured result of the round that derives rather "
                "than looks up"),
    Translation("phys-convert", None, None, None, "none",
                "the lexicon holds `foot` as a word and the physics register "
                "holds the metre, but no metre-to-foot factor is held "
                "anywhere and no solver converts between units"),
    # ── chemistry ───────────────────────────────────────────────────────
    Translation("chem-lookup", None, None, "carbon-name", "register",
                "the element register holds `name = 'Carbon'` beside the "
                "symbol; `describe C` returns the carrier's geometry and "
                "never the row's own fields"),
    Translation("chem-weight", None, None, "carbon-atomic-weight",
                "register",
                "`atomic_weight_u = 12011/1000` is in the same row, exactly.  "
                "`derive` would be the natural surface for it and the "
                "described domains are comparison, harmonics and economics "
                "only"),
    Translation("chem-group", None, None, "chlorine-block", "register",
                "`group_block = 'Halogen'` is in the row for chlorine"),
    Translation("chem-compose", None, None, "water-molar-mass", "module",
                "not held as a field but computed from two that are: the "
                "molecule register holds the formula H2O and the element "
                "register the atomic weights, and the composition is one "
                "exact sum"),
    # ── program text ────────────────────────────────────────────────────
    Translation("prog-lean", None, None, "family-tower-file", "module",
                "the Lean address book holds the file of every declaration "
                "and is what `report lean` measures in aggregate; no query "
                "kind asks it about one declaration"),
    Translation("prog-python", None, None, "rung-audit-module", "source",
                "the package's own Python is not a register and is not "
                "addressed; the answer is in the source and is found by the "
                "same AST walk `blockers.python_features` already does"),
    Translation("prog-behaviour", None, None, "completeness-returns",
                "module",
                "the function returns a mapping with a `complete` key, so "
                "the answer is obtainable by calling it; nothing in the "
                "system reads what a function returns"),
    Translation("prog-count", None, None, "norm-family-rungs", "module",
                "`substrate.norm_family.family_rungs()` has 25 entries; "
                "`report lattices` reports the ladder past the Leech lattice "
                "and not this count"),
)


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE WITNESSES
# ═════════════════════════════════════════════════════════════════════════

def _decimal(value: Fraction, places: int) -> str:
    """``value`` rendered to ``places`` decimals, exactly and by truncation."""
    scaled = value.numerator * 10 ** places // value.denominator
    digits = str(abs(scaled)).rjust(places + 1, "0")
    sign = "-" if scaled < 0 else ""
    if places == 0:
        return f"{sign}{digits}"
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def _velocity_derivative_of() -> str:
    from ..data_objects import semantic_lexicon_objects
    entries = {entry.name.lower(): entry
               for entry in semantic_lexicon_objects()[0]}
    triples = entries["velocity"].attributes.get("triples", ())
    for subject, relation, target in triples:
        if relation == "derivative_of":
            return f"{subject} derivative_of {target}"
    return ""


def _abstractness_energy_water() -> str:
    from ..data_objects import semantic_lexicon_objects
    entries = {entry.name.lower(): entry
               for entry in semantic_lexicon_objects()[0]}
    energy = Fraction(entries["energy"].carrier[0])
    water = Fraction(entries["water"].carrier[0])
    # 0 = abstract, 1 = concrete, so the smaller coordinate is the more
    # abstract word.
    more = "energy" if energy < water else "water"
    return (f"abstract_concrete energy={energy} water={water}; "
            f"more abstract: {more}")


def _carbon_name() -> str:
    from ..data_objects import element_by_symbol
    return str(element_by_symbol("C").name)


def _carbon_atomic_weight() -> str:
    from ..data_objects import element_by_symbol
    return _decimal(Fraction(element_by_symbol("C").atomic_weight_u), 3)


def _chlorine_block() -> str:
    from ..data_objects import element_by_symbol
    return str(element_by_symbol("Cl").group_block)


def _water_molar_mass() -> str:
    from ..data_objects import element_by_symbol, molecule_by_name
    water = molecule_by_name("water")
    total = Fraction(0)
    for symbol, count in water.counts.items():
        total += count * Fraction(element_by_symbol(symbol).atomic_weight_u)
    return _decimal(total, 3)


def _family_tower_file() -> str:
    """Which file the declaration is in, read off the **stored** Lean book.

    Reading it off the development instead would put the whole Lean tree
    into this module's closure, and through this module into the closure of
    everything that reaches the probe -- the leak
    ``studies/ITERATION_COST_STUDY.md`` §5e is about.  The book is generated
    from the development and is data, so a unit that reads it is still stale
    when the book moves.
    """
    from . import lean_book
    row = lean_book.declaration_rows().get("GLM.NormFamily.family_tower")
    return str(row["file"]) if row else ""


def _rung_audit_module() -> str:
    root = Path(__file__).resolve().parent.parent
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):           # pragma: no cover - defensive
            continue
        for node in ast.walk(tree):
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "rung_audit"):
                return path.stem
    return ""


def _completeness_returns() -> str:
    from ..substrate import norm_family
    return " ".join(sorted(norm_family.completeness()))


def _norm_family_rungs() -> str:
    from ..substrate import norm_family
    return str(len(norm_family.family_rungs()))


#: Every witness, by the name a translation cites.  A witness returns the
#: string the register or the function holds; the declared fragment has to
#: appear in it for the fact to count as held.
WITNESSES: Dict[str, Callable[[], str]] = {
    "velocity-derivative-of": _velocity_derivative_of,
    "abstractness-energy-water": _abstractness_energy_water,
    "carbon-name": _carbon_name,
    "carbon-atomic-weight": _carbon_atomic_weight,
    "chlorine-block": _chlorine_block,
    "water-molar-mass": _water_molar_mass,
    "family-tower-file": _family_tower_file,
    "rung-audit-module": _rung_audit_module,
    "completeness-returns": _completeness_returns,
    "norm-family-rungs": _norm_family_rungs,
}


def witness_value(name: str) -> str:
    """What the named witness holds, as a string."""
    return WITNESSES[name]()


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE EXPERIMENT
# ═════════════════════════════════════════════════════════════════════════

#: The three classes, in the order they are reported.
CLASSES: Tuple[str, ...] = ("parsed", "surface", "absent")


def class_of(answered: bool, held: bool) -> str:
    """The class of one question, from the two facts that decide it."""
    if answered:
        return "parsed"
    return "surface" if held else "absent"


def _ask(session, query: str, locus: str, expect: str) -> Dict[str, object]:
    """Ask one translation and score it at its declared locus."""
    try:
        solution = session.ask(query)
    except Exception as error:                  # pragma: no cover - defensive
        return {"ok": False, "kind": "error", "at_locus": False,
                "field": "", "detail": f"{type(error).__name__}: {error}"[:200]}
    if not solution.ok:
        return {"ok": False, "kind": solution.kind, "at_locus": False,
                "field": "", "detail": (solution.error or "")[:200]}
    if locus == "answer":
        field = solution.answer
    else:
        field = str(solution.expected.get(locus, ""))
    return {"ok": True, "kind": solution.kind,
            "at_locus": expect.lower() in field.lower(),
            "field": field[:200], "detail": solution.answer[:200]}


def translate(session=None,
              translations: Optional[Sequence["Translation"]] = None
              ) -> Tuple[Dict[str, object], ...]:
    """Run every declared translation and classify every question.

    One row per probe question: what the translation was, what the session
    did with it, what the witness holds, and which of the three classes the
    two answers put the question in.

    ``translations`` defaults to :data:`TRANSLATIONS`, which is frozen: it is
    what the round that declared it measured, and it stays measurable.  A
    later round that *builds* one of the missing surfaces passes its own
    table here rather than editing this one, so the two readings can be
    compared instead of one replacing the other.
    """
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    questions: Dict[str, ProbeQuestion] = {q.key: q for q in PROBE}
    rows: List[Dict[str, object]] = []
    for translation in (TRANSLATIONS if translations is None
                        else tuple(translations)):
        question = questions[translation.key]
        expect = question.expect
        if translation.query is None:
            asked: Dict[str, object] = {"ok": False, "kind": "not-expressible",
                                        "at_locus": False, "field": "",
                                        "detail": ""}
        else:
            asked = _ask(session, translation.query,
                         str(translation.locus), expect)
        answered = bool(asked["ok"]) and bool(asked["at_locus"])
        if translation.witness is None:
            witness_holds, witness_text = False, ""
        else:
            witness_text = witness_value(translation.witness)
            witness_holds = expect.lower() in witness_text.lower()
        rows.append({
            "key": translation.key,
            "domain": question.domain,
            "question": question.question,
            "expect": expect,
            "query": translation.query,
            "locus": translation.locus,
            "asked": asked,
            "answered": answered,
            "witness": translation.witness,
            "witness_kind": translation.witness_kind,
            "witness_text": witness_text[:200],
            "witness_holds": witness_holds,
            "class": class_of(answered, witness_holds),
            "note": translation.note,
        })
    return tuple(rows)


def oracle_report(session=None,
                  translations: Optional[Sequence["Translation"]] = None
                  ) -> Dict[str, object]:
    """The whole experiment: the rows, the split, and what it decides.

    The English verdicts it is set against are the canonical askings of the
    probe itself, re-run here so that the two readings are taken in the same
    process and against the same registers.
    """
    from .blockers import run_probe
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    rows = translate(session, translations)
    probe = run_probe()
    english = {str(row["key"]): str(row["canonical"]["verdict"])   # type: ignore[index]
               for row in probe["rows"]}                          # type: ignore[union-attr]
    counts = {name: sum(1 for row in rows if row["class"] == name)
              for name in CLASSES}
    by_domain: Dict[str, Dict[str, int]] = {}
    for row in rows:
        bucket = by_domain.setdefault(str(row["domain"]),
                                      {name: 0 for name in CLASSES})
        bucket[str(row["class"])] += 1
    english_correct = sum(1 for key in english if english[key] == "correct")
    moved = tuple(sorted(str(row["key"]) for row in rows
                         if row["class"] == "parsed"
                         and english[str(row["key"])] != "correct"))
    witness_kinds = {kind: sum(1 for row in rows
                               if row["class"] == "surface"
                               and row["witness_kind"] == kind)
                     for kind in WITNESS_KINDS}
    total = len(rows)
    return {
        "questions": total,
        "rows": rows,
        "counts": counts,
        "by_domain": by_domain,
        "english_correct": english_correct,
        "english": english,
        "moved_by_translation": moved,
        "witness_kinds": witness_kinds,
        "parser_worth": len(moved),
        "surface_worth": counts["surface"],
        "verdict": (
            f"{counts['parsed']} of {total} are answered by a query written "
            f"in the existing grammar, against {english_correct} asked in "
            f"English, so hand-translation is worth {len(moved)} questions; "
            f"{counts['surface']} more are held by a register or a shipped "
            f"function with no query kind that returns them, and "
            f"{counts['absent']} are held nowhere, where the refusal is the "
            f"right answer."),
        "reading": (
            "the split is the result, not the score: the parser is worth "
            f"{len(moved)} questions and a surface onto what the registers "
            f"already hold is worth {counts['surface']}, so the cheaper "
            "instrument is the one this repository does not have.  A "
            "question is only counted answered when the declared fragment "
            "appears in the declared field of the solution, which is "
            "stricter than the probe's own scoring rule."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = oracle_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<15} {row['class']:<8} "
              f"{row['query'] or '(not expressible)'}")
