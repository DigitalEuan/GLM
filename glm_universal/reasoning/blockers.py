"""``glm_universal.reasoning.blockers`` -- what is between this system and
fuller reasoning, measured rather than described.

Why this module exists
----------------------
The escalation work measures one faculty well: geometric addressing, and --
since :mod:`glm_universal.reasoning.operation_escalation` -- a handful of
operations built on it.  None of that is reasoning over natural language,
mathematics, physics, chemistry or program text in the sense a reader would
mean by those words.  This module says exactly what is missing, and it says it
with numbers: every blocker below carries **the measurement that demonstrates
it** and **the smallest experiment that would remove it**.

The pre-registered probe
------------------------
:data:`PROBE` is twenty natural-language questions, four from each of five
domains, declared here *with their scoring rule and their pass mark before
they were run*:

* each question is asked of :class:`glm_universal.runtime.session.GeometricSession`
  in its canonical phrasing and again in a declared paraphrase;
* an asking is **correct** when the session answers and the declared fragment
  appears in the answer or in the solution's ``expected`` mapping; **wrong**
  when it answers and the fragment does not; **refused** when it does not
  answer;
* :data:`PASS_MARK` is the mark declared before the run: at least 10 of the 20
  canonical askings correct, with at most 1 wrong.

The probe is a *coverage* measurement, not a safety one: a refusal costs the
probe a point but is not a failure of the refusal contract, and the report
says which of the two any given miss is.

Three things that are not the same
----------------------------------
:func:`faculty_ledger` insists on the distinction the round asked for, and
assigns every measured result to exactly one of:

``table``
    the answer is a field of a register row, found by name.  No geometry is
    used and none is claimed.
``addressed``
    the answer is found by quantising a *perturbed* carrier and reading the
    cell.  The geometry is doing work -- the query is not the stored key --
    but the answer is still something the register holds.
``derived``
    the system computes the answer itself, by exact arithmetic over values it
    recovered.  Equation checking is the only operation here that reaches this
    class, and it reaches it for one kind of claim.

Exactness
---------
Counts are integers and rates are :class:`~fractions.Fraction`.  No float is
constructed anywhere in this module.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "ProbeQuestion", "PROBE", "PASS_MARK", "run_probe",
    "lexicon_coverage", "VOCABULARY_EXPERIMENT", "vocabulary_experiment", "python_features", "python_addressing",
    "faculty_ledger", "BLOCKERS", "blockers_report",
    "measure", "write_measurements", "measurements", "module_digest",
    "state", "current", "DATA_PATH",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE PRE-REGISTERED PROBE
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProbeQuestion:
    """One declared question, its paraphrase, and what a right answer says."""

    key: str
    domain: str
    question: str
    paraphrase: str
    expect: str
    why: str


#: The twenty questions, declared before the run.  Four from each of the five
#: domains the round names: natural language, mathematics, physics, chemistry
#: and program text.  The ``expect`` string is what a correct answer has to
#: contain; it is a fragment, not a whole answer, so a right answer phrased
#: differently still scores.
PROBE: Tuple[ProbeQuestion, ...] = (
    # ── natural language ────────────────────────────────────────────────
    ProbeQuestion("nl-meaning", "natural language",
                  "what does velocity mean?",
                  "explain the meaning of velocity",
                  "velocity",
                  "a meaning question about a word the lexicon holds"),
    ProbeQuestion("nl-relation", "natural language",
                  "what is velocity the derivative of?",
                  "velocity is the derivative of what?",
                  "position",
                  "a relation the lexicon holds as a triple"),
    ProbeQuestion("nl-compare", "natural language",
                  "is energy more abstract than water?",
                  "which is more abstract, energy or water?",
                  "energy",
                  "a comparison over a semantic primitive both words carry"),
    ProbeQuestion("nl-unknown", "natural language",
                  "why is the sky blue?",
                  "what makes the sky look blue?",
                  "rayleigh",
                  "a question nothing in the system holds -- the right "
                  "outcome is a refusal, and answering it would be wrong"),
    # ── mathematics ─────────────────────────────────────────────────────
    ProbeQuestion("math-add", "mathematics",
                  "what is 2 + 2?",
                  "add two and two",
                  "4",
                  "arithmetic the term layer can ground"),
    ProbeQuestion("math-prime", "mathematics",
                  "is 91 prime?",
                  "is ninety-one a prime number?",
                  "no",
                  "a decidable arithmetic fact needing a computation"),
    ProbeQuestion("math-gcd", "mathematics",
                  "what is the greatest common divisor of 12 and 18?",
                  "gcd of 12 and 18",
                  "6",
                  "a two-argument arithmetic function"),
    ProbeQuestion("math-ratio", "mathematics",
                  "what is the prime limit of the interval 3/2?",
                  "the prime limit of a perfect fifth",
                  "3",
                  "a property the harmonics register holds"),
    # ── physics ─────────────────────────────────────────────────────────
    ProbeQuestion("phys-constant", "physics",
                  "describe speed_of_light",
                  "tell me about speed_of_light",
                  "speed_of_light",
                  "a register lookup by exact name -- the easiest case"),
    ProbeQuestion("phys-dimension", "physics",
                  "what are the dimensions of force?",
                  "give the dimensional formula of force",
                  "M",
                  "a dimensional fact the physics register carries"),
    ProbeQuestion("phys-derive", "physics",
                  "is force equal to mass times acceleration dimensionally?",
                  "check that force has the dimensions of mass times "
                  "acceleration",
                  "true",
                  "a derivation over two register facts, not a lookup"),
    ProbeQuestion("phys-convert", "physics",
                  "convert 3 metres to feet",
                  "how many feet is 3 metres?",
                  "9.84",
                  "a unit conversion needing a factor the register does not "
                  "hold"),
    # ── chemistry ───────────────────────────────────────────────────────
    ProbeQuestion("chem-lookup", "chemistry",
                  "describe C",
                  "tell me about the element C",
                  "carbon",
                  "a register lookup by symbol"),
    ProbeQuestion("chem-weight", "chemistry",
                  "what is the atomic weight of carbon?",
                  "how heavy is a carbon atom?",
                  "12.011",
                  "a field of a register row, asked in English"),
    ProbeQuestion("chem-group", "chemistry",
                  "which block of the periodic table is chlorine in?",
                  "what block does chlorine belong to?",
                  "halogen",
                  "a classification the register holds as an attribute"),
    ProbeQuestion("chem-compose", "chemistry",
                  "what is the molar mass of water?",
                  "how much does a mole of water weigh?",
                  "18",
                  "a quantity derived from the element register"),
    # ── program text ────────────────────────────────────────────────────
    ProbeQuestion("prog-lean", "program text",
                  "which file is GLM.NormFamily.family_tower in?",
                  "where is the declaration GLM.NormFamily.family_tower "
                  "written?",
                  "NormFamily.lean",
                  "a program-text question the Lean address book can answer"),
    ProbeQuestion("prog-python", "program text",
                  "which module defines the function rung_audit?",
                  "where is rung_audit defined?",
                  "norm_escalation",
                  "the same question about this package's own Python"),
    ProbeQuestion("prog-behaviour", "program text",
                  "what does glm_universal.substrate.norm_family.completeness "
                  "return?",
                  "describe what completeness returns",
                  "complete",
                  "a question about what code does, not where it is"),
    ProbeQuestion("prog-count", "program text",
                  "how many rungs does the norm family have?",
                  "count the rungs of the norm family",
                  "25",
                  "a question whose answer is computed by the code itself"),
)

#: The pass mark, declared before the probe was run.
PASS_MARK: Dict[str, int] = {
    "correct_at_least": 10,
    "wrong_at_most": 1,
    "of": len(PROBE),
}


def _score_asking(session, text: str, expect: str) -> Dict[str, object]:
    try:
        solution = session.ask(text)
    except Exception as error:                  # pragma: no cover - defensive
        return {"verdict": "refused", "kind": "error",
                "detail": f"{type(error).__name__}: {error}"[:200]}
    haystack = " ".join(
        [solution.answer] + [f"{key}={value}"
                             for key, value in solution.expected.items()]
    ).lower()
    if not solution.ok:
        return {"verdict": "refused", "kind": solution.kind,
                "detail": (solution.error or "")[:200]}
    return {
        "verdict": "correct" if expect.lower() in haystack else "wrong",
        "kind": solution.kind,
        "detail": solution.answer[:200],
    }


def run_probe() -> Dict[str, object]:
    """Ask every declared question, canonically and in paraphrase, and score.

    Nothing about the questions, the expected fragments, the scoring rule or
    the pass mark is decided here: they are :data:`PROBE` and
    :data:`PASS_MARK`, declared above.
    """
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    rows: List[Dict[str, object]] = []
    for question in PROBE:
        canonical = _score_asking(session, question.question, question.expect)
        paraphrase = _score_asking(session, question.paraphrase,
                                   question.expect)
        rows.append({
            "key": question.key,
            "domain": question.domain,
            "question": question.question,
            "paraphrase": question.paraphrase,
            "expect": question.expect,
            "why": question.why,
            "canonical": canonical,
            "paraphrased": paraphrase,
            "stable": canonical["verdict"] == paraphrase["verdict"],
        })

    def tally(which: str) -> Dict[str, int]:
        return {
            verdict: sum(1 for row in rows
                         if row[which]["verdict"] == verdict)    # type: ignore[index]
            for verdict in ("correct", "wrong", "refused")}

    canonical_tally = tally("canonical")
    paraphrase_tally = tally("paraphrased")
    by_domain: Dict[str, Dict[str, int]] = {}
    for row in rows:
        bucket = by_domain.setdefault(str(row["domain"]),
                                      {"correct": 0, "wrong": 0,
                                       "refused": 0})
        bucket[str(row["canonical"]["verdict"])] += 1          # type: ignore[index]
    passed = (canonical_tally["correct"] >= PASS_MARK["correct_at_least"]
              and canonical_tally["wrong"] <= PASS_MARK["wrong_at_most"])
    return {
        "questions": len(rows),
        "rows": tuple(rows),
        "canonical": canonical_tally,
        "paraphrased": paraphrase_tally,
        "by_domain": by_domain,
        "stable": sum(1 for row in rows if row["stable"]),
        "pass_mark": dict(PASS_MARK),
        "passed": passed,
        "reading": (
            "a refusal costs the probe a point and is not a failure of the "
            "refusal contract; a wrong answer is both. The probe measures "
            "coverage of natural language, and the pass mark was declared "
            "before the run."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE MEASUREMENTS BEHIND THE BLOCKERS
# ═════════════════════════════════════════════════════════════════════════

_STOP_WORDS = frozenset("""
a an the is are was were do does did of in on at to for from by with what
which who whom whose how why when where that this these those it its and or
not no yes be been being have has had can could will would should may might
me you he she they them their there here more most many much some any all
each into out up down over under than then as if so such about
""".split())


def lexicon_coverage() -> Dict[str, object]:
    """How much of the probe's vocabulary the semantic lexicon holds.

    The lexicon is the only register that carries words as words.  Every
    content word of the probe is looked up in it; the ones it does not hold
    are what a natural-language question would have to be parsed without.
    """
    from ..data_objects import semantic_lexicon as SL
    from ..data_objects import semantic_lexicon_objects
    words = {entry.name.lower() for entry in semantic_lexicon_objects()[0]}
    asked: Dict[str, int] = {}
    for question in PROBE:
        for text in (question.question, question.paraphrase):
            for token in text.replace("?", " ").replace(",", " ").split():
                token = token.strip("().").lower()
                if token and token not in _STOP_WORDS and token.isalpha():
                    asked[token] = asked.get(token, 0) + 1
    held = sorted(token for token in asked if token in words)
    missing = sorted(token for token in asked if token not in words)
    # The same count again, after the *declared* morphology of
    # :data:`glm_universal.data_objects.semantic_lexicon.SEMANTIC_WORD_FORMS`
    # -- a finite, hand-written list of surface forms, not a stemmer.  The
    # strict count above is the figure the vocabulary blocker is stated in;
    # this one says how much of the remainder is inflection rather than
    # absence.
    resolved = sorted(token for token in missing
                      if SL.resolve_form(token) is not None)
    unresolved = sorted(token for token in missing
                        if SL.resolve_form(token) is None)
    total = len(asked)
    with_forms = len(held) + len(resolved)
    return {
        "lexicon_size": len(words),
        "declared_forms": len(SL.SEMANTIC_WORD_FORMS),
        "content_words": total,
        "in_lexicon": len(held),
        "out_of_lexicon": len(missing),
        "coverage": Fraction(len(held), total) if total else Fraction(0),
        "in_lexicon_with_forms": with_forms,
        "out_of_lexicon_with_forms": len(unresolved),
        "coverage_with_forms": (Fraction(with_forms, total) if total
                                else Fraction(0)),
        "held": tuple(held),
        "missing": tuple(missing[:40]),
        "missing_resolved_by_a_declared_form": tuple(resolved),
        "missing_after_forms": tuple(unresolved),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2a.  THE VOCABULARY EXPERIMENT, DECLARED BEFORE IT WAS RUN
# ═════════════════════════════════════════════════════════════════════════

#: Blocker ``vocabulary`` named its own smallest experiment: *add the missing
#: content words of the probe to the lexicon with their primitives, and re-run
#: the probe; if the score does not move, the blocker is the parser and not
#: the vocabulary.*  This is that experiment, with the baseline it is read
#: against and the prediction, both recorded before the words were added.
#:
#: ``baseline`` is the measurement of the round that declared the experiment,
#: taken when the register held 95 concepts.  ``prediction`` is what was
#: written down before the 54 words were written.  ``reading`` is the rule for
#: deciding the outcome, and it was fixed in advance too: the vocabulary is
#: ruled out as the binding constraint when coverage rises materially and the
#: probe's canonical score does not.
VOCABULARY_EXPERIMENT: Dict[str, object] = {
    "baseline": {
        "lexicon_size": 95,
        "content_words": 69,
        "in_lexicon": 10,
        "correct": 2,
        "wrong": 1,
        "refused": 17,
    },
    "prediction": (
        "the probe's canonical score does not move by more than one asking: "
        "the refusals are the session failing to recognise a query kind, not "
        "the lexicon failing to hold a word"),
    "reading": (
        "coverage must rise by at least half of the words that were missing "
        "for the experiment to have been carried out at all; if it does and "
        "the canonical score moves by at most one asking, the vocabulary is "
        "not the binding constraint and blocker `parse` is"),
}


def vocabulary_experiment() -> Dict[str, object]:
    """The declared experiment, run: coverage before and after, and the probe.

    Nothing is decided here.  The baseline, the prediction and the rule for
    reading the outcome are :data:`VOCABULARY_EXPERIMENT`, declared before the
    words were added; this function only takes the measurement and applies
    that rule.
    """
    baseline = dict(VOCABULARY_EXPERIMENT["baseline"])           # type: ignore[arg-type]
    lexicon = lexicon_coverage()
    probe = run_probe()
    canonical = probe["canonical"]                               # type: ignore[index]
    was_missing = int(baseline["content_words"]) - int(baseline["in_lexicon"])
    gained = int(lexicon["in_lexicon"]) - int(baseline["in_lexicon"])
    carried_out = gained * 2 >= was_missing
    moved = (abs(int(canonical["correct"]) - int(baseline["correct"]))
             + abs(int(canonical["wrong"]) - int(baseline["wrong"])))
    return {
        "baseline": baseline,
        "prediction": VOCABULARY_EXPERIMENT["prediction"],
        "reading": VOCABULARY_EXPERIMENT["reading"],
        "words_added": int(lexicon["lexicon_size"]) - int(
            baseline["lexicon_size"]),
        "was_missing": was_missing,
        "words_gained": gained,
        "carried_out": carried_out,
        "coverage_before": Fraction(int(baseline["in_lexicon"]),
                                    int(baseline["content_words"])),
        "coverage_after": lexicon["coverage"],
        "coverage_after_with_forms": lexicon["coverage_with_forms"],
        "score_before": {"correct": int(baseline["correct"]),
                         "wrong": int(baseline["wrong"]),
                         "refused": int(baseline["refused"])},
        "score_after": dict(canonical),                          # type: ignore[arg-type]
        "score_moved_by": moved,
        "prediction_held": carried_out and moved <= 1,
        "verdict": (
            "the vocabulary is not the binding constraint: the register now "
            "holds the probe's words and the probe scores the same"
            if carried_out and moved <= 1 else
            "the score moved: the vocabulary was carrying part of the failure"
            if carried_out else
            "the experiment was not carried out -- coverage did not rise"),
    }


#: The 24 structural features a Python function is reduced to.  They are the
#: Python analogue of the Lean features
#: :mod:`glm_universal.reasoning.lean_address` already uses, and they are
#: counts of syntax, never of names: nothing in the vector says which module
#: the function is in, so "the address names the module" is a claim that can
#: fail.
PYTHON_FEATURES: Tuple[str, ...] = (
    "arguments", "defaults", "returns", "ifs", "fors", "whiles", "trys",
    "withs", "calls", "assignments", "comparisons", "boolean_ops",
    "comprehensions", "lambdas", "raises", "asserts", "yields", "decorators",
    "nested_defs", "statements", "max_depth", "constants", "attributes",
    "name_length",
)


def _depth(node: ast.AST, level: int = 0) -> int:
    return max([level] + [_depth(child, level + 1)
                          for child in ast.iter_child_nodes(node)])


def _function_features(node: ast.AST) -> Tuple[int, ...]:
    counts = {name: 0 for name in PYTHON_FEATURES}
    counts["arguments"] = len(getattr(node, "args").args)
    counts["defaults"] = len(getattr(node, "args").defaults)
    counts["decorators"] = len(getattr(node, "decorator_list"))
    counts["name_length"] = min(24, len(getattr(node, "name")))
    counts["statements"] = len(getattr(node, "body"))
    counts["max_depth"] = min(24, _depth(node))
    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            counts["returns"] += 1
        elif isinstance(child, ast.If):
            counts["ifs"] += 1
        elif isinstance(child, ast.For):
            counts["fors"] += 1
        elif isinstance(child, ast.While):
            counts["whiles"] += 1
        elif isinstance(child, ast.Try):
            counts["trys"] += 1
        elif isinstance(child, ast.With):
            counts["withs"] += 1
        elif isinstance(child, ast.Call):
            counts["calls"] += 1
        elif isinstance(child, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            counts["assignments"] += 1
        elif isinstance(child, ast.Compare):
            counts["comparisons"] += 1
        elif isinstance(child, ast.BoolOp):
            counts["boolean_ops"] += 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp,
                                ast.GeneratorExp)):
            counts["comprehensions"] += 1
        elif isinstance(child, ast.Lambda):
            counts["lambdas"] += 1
        elif isinstance(child, ast.Raise):
            counts["raises"] += 1
        elif isinstance(child, ast.Assert):
            counts["asserts"] += 1
        elif isinstance(child, (ast.Yield, ast.YieldFrom)):
            counts["yields"] += 1
        elif isinstance(child, ast.FunctionDef) and child is not node:
            counts["nested_defs"] += 1
        elif isinstance(child, ast.Constant):
            counts["constants"] += 1
        elif isinstance(child, ast.Attribute):
            counts["attributes"] += 1
    return tuple(min(63, counts[name]) for name in PYTHON_FEATURES)


#: How many Python functions the experiment reads, in module and name order.
PYTHON_SAMPLE: int = 240


def python_features(limit: int = PYTHON_SAMPLE
                    ) -> Tuple[Tuple[str, str, Tuple[int, ...]], ...]:
    """``(module, function, features)`` for this package's own functions."""
    root = Path(__file__).resolve().parent.parent
    out: List[Tuple[str, str, Tuple[int, ...]]] = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts or path.name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:                     # pragma: no cover - defensive
            continue
        module = str(path.relative_to(root).with_suffix(""))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                out.append((module, node.name, _function_features(node)))
                if len(out) >= limit:
                    return tuple(out)
    return tuple(out)


def python_addressing(limit: int = PYTHON_SAMPLE) -> Dict[str, object]:
    """Does a geometric address of Python code carry which module it is in?

    The smallest experiment that would tell whether the substrate reaches
    program text at all: address each function by its 24 syntax counts, take
    each one's nearest neighbour by squared distance, and ask how often the
    neighbour is from the same module.  Two controls are measured beside it --
    a digest address, which knows nothing about the function, and chance,
    which is the probability two functions drawn at random share a module.
    """
    from . import ladder_escalation as LE
    sample = python_features(limit)
    if len(sample) < 2:                         # pragma: no cover - defensive
        return {"functions": len(sample), "usable": False}
    points = [LE.quantise([Fraction(value) for value in features], "A").point
              for _, _, features in sample]
    digests = []
    for module, name, _ in sample:
        coordinates = [Fraction(value) for value
                       in integrity.byte_vector(f"{module}.{name}", 24, 64)]
        digests.append(LE.quantise(coordinates, "A").point)

    def nearest_share(vectors: Sequence[Sequence[int]]) -> int:
        shared = 0
        for i, point in enumerate(vectors):
            best, best_index = None, None
            for j, other in enumerate(vectors):
                if i == j:
                    continue
                distance = sum((int(a) - int(b)) ** 2
                               for a, b in zip(point, other))
                if best is None or distance < best or (
                        distance == best and j < (best_index or 0)):
                    best, best_index = distance, j
            if best_index is not None and sample[best_index][0] == sample[i][0]:
                shared += 1
        return shared

    modules: Dict[str, int] = {}
    for module, _, _ in sample:
        modules[module] = modules.get(module, 0) + 1
    total = len(sample)
    chance_numerator = sum(count * (count - 1) for count in modules.values())
    chance = Fraction(chance_numerator, total * (total - 1))
    lattice = nearest_share(points)
    control = nearest_share(digests)
    return {
        "functions": total,
        "modules": len(modules),
        "usable": True,
        "nearest_shares_module": lattice,
        "digest_control": control,
        "chance": chance,
        "expected_by_chance": chance * total,
        "rate": Fraction(lattice, total),
        "beats_control": lattice > control,
        "beats_chance": Fraction(lattice, total) > chance,
        "features": PYTHON_FEATURES,
        "reading": ("the vector holds syntax counts only -- no name, no "
                    "module, no path -- so a rate above chance is the "
                    "geometry carrying something about the code"),
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE LEDGER AND THE BLOCKERS
# ═════════════════════════════════════════════════════════════════════════

def faculty_ledger() -> Tuple[Dict[str, object], ...]:
    """Every measured result of the round, assigned to one of three classes.

    ``table``, ``addressed`` and ``derived`` -- the distinction the round
    insists on.  A result is in the class its *mechanism* puts it in, not the
    class its headline sounds like.
    """
    return (
        {"result": "register lookup by exact name (the describe solver)",
         "class": "table",
         "why": ("the name is matched against the register index; no "
                 "quantisation happens and no geometry is consulted"),
         "measured_in": "glm_universal.runtime.session"},
        {"result": "retrieval of a perturbed carrier over the norm ladder",
         "class": "addressed",
         "why": ("the query is not the stored key -- it is the key plus a "
                 "declared offset -- and the lattice cell is what recovers "
                 "the identity"),
         "measured_in": "glm_universal.reasoning.norm_escalation"},
        {"result": "register, chemistry, physics, harmony and program-text "
                   "classification of a perturbed carrier",
         "class": "addressed",
         "why": ("the same mechanism answering a coarser question; the "
                 "answer is still a label the register holds"),
         "measured_in": "glm_universal.reasoning.operation_escalation"},
        {"result": "dimensional exponent recovery",
         "class": "addressed",
         "why": ("the exponents are read out of the cell, not computed; what "
                 "the geometry supplies is the reading"),
         "measured_in": "glm_universal.reasoning.operation_escalation"},
        {"result": "equation checking over recovered exponent vectors",
         "class": "derived",
         "why": ("the seven integer additions and the comparison are done by "
                 "the system over values it recovered; no register holds the "
                 "answer to the claim being checked"),
         "measured_in": "glm_universal.reasoning.operation_escalation"},
        {"result": "the containment order of the norm family",
         "class": "derived",
         "why": ("every containment is composed from a handful of relative "
                 "rules and then checked on generated points; none is stored"),
         "measured_in": "glm_universal.substrate.norm_family"},
    )


#: The blockers, each with the measurement that demonstrates it and the
#: smallest experiment that would remove it.  The measurement is a *key* into
#: the report computed by :func:`blockers_report`, never a typed-in number.
BLOCKERS: Tuple[Dict[str, str], ...] = (
    {"key": "parse",
     "title": "there is no parser from open natural language to a query",
     "statement": ("the session recognises a fixed grammar of query kinds; a "
                   "question outside it is not misunderstood, it is not "
                   "understood at all"),
     "measurement": "probe.canonical.refused and probe.unrecognised",
     "experiment": ("take the twenty probe questions and hand-write the "
                    "query each one should become; measure how many of the "
                    "twenty the existing solvers then answer. That separates "
                    "'cannot parse' from 'cannot answer' without building a "
                    "parser -- run in reasoning/probe_oracle.py, which finds "
                    "the parser worth 4 of the 20 and a surface onto what "
                    "the registers already hold worth 10")},
    {"key": "vocabulary",
     "title": "the lexicon is small and closed",
     "statement": ("words the lexicon does not hold cannot be grounded, and "
                   "most words of an ordinary question are not in it"),
     "measurement": "lexicon.coverage",
     "experiment": ("add the missing content words of the probe to the "
                    "lexicon with their primitives, and re-run the probe; if "
                    "the score does not move, the blocker is the parser and "
                    "not the vocabulary")},
    {"key": "composition",
     "title": "answers are fields, not compositions",
     "statement": ("the registers hold values; the system has one measured "
                   "operation that composes two of them into a third, and it "
                   "composes exponents only"),
     "measurement": "faculty.derived_count",
     "experiment": ("extend the equation operation from checking a claim to "
                    "solving one -- given two operands and the claim, emit "
                    "the third exponent vector -- and measure exactness "
                    "against the register")},
    {"key": "paraphrase",
     "title": "surface form decides whether a question is answered",
     "statement": ("the same question in two phrasings is not the same query "
                   "to the system"),
     "measurement": "probe.stable",
     "experiment": ("paraphrase each probe question three ways rather than "
                    "one and report the spread; a faculty that is stable "
                    "under paraphrase would show equal scores")},
    {"key": "python",
     "title": "program text is a register the system does not have",
     "statement": ("the Lean development is addressed; this package's own "
                   "Python is not addressed by anything, and nothing reads "
                   "a script as a carrier"),
     "measurement": "python.nearest_shares_module",
     "experiment": ("the experiment in python_addressing is that smallest "
                    "experiment, run here: address 240 functions by 24 "
                    "syntax counts and measure nearest-neighbour module "
                    "agreement against a digest control and chance")},
    {"key": "safety-vs-coverage",
     "title": "the refusal contract buys safety at the cost of coverage",
     "statement": ("the ladder refuses rather than answering wrongly, and "
                   "the price is the refused queries; nothing in the system "
                   "reduces that price except a better reading"),
     "measurement": "escalation.refused",
     "experiment": ("measure whether a second, independent reading -- the "
                    "lexical address book -- answers any of the queries the "
                    "ladder refuses, which would show refusals are a "
                    "single-channel limit rather than an information limit")},
)


def blockers_report() -> Dict[str, object]:
    """Every blocker with its measurement taken, and the probe's outcome."""
    probe = run_probe()
    lexicon = lexicon_coverage()
    vocabulary = vocabulary_experiment()
    python = python_addressing()
    ledger = faculty_ledger()
    unrecognised = sum(
        1 for row in probe["rows"]                               # type: ignore[union-attr]
        if row["canonical"]["kind"] in ("unknown", "error"))     # type: ignore[index]
    from . import norm_escalation as NE
    escalation = NE.current()
    refused = (int(escalation["repaired"]["orders"]["totals"]    # type: ignore[index]
                   ["middle_out"]["refused"])
               if escalation is not None else None)
    figures: Dict[str, object] = {
        "escalation.refused": refused,
        "probe.canonical.correct": probe["canonical"]["correct"],  # type: ignore[index]
        "probe.canonical.wrong": probe["canonical"]["wrong"],      # type: ignore[index]
        "probe.canonical.refused": probe["canonical"]["refused"],  # type: ignore[index]
        "probe.unrecognised": unrecognised,
        "probe.stable": probe["stable"],
        "lexicon.coverage": str(lexicon["coverage"]),
        "lexicon.out_of_lexicon": lexicon["out_of_lexicon"],
        "lexicon.coverage_with_forms": str(lexicon["coverage_with_forms"]),
        "vocabulary.words_added": vocabulary["words_added"],
        "vocabulary.score_moved_by": vocabulary["score_moved_by"],
        "vocabulary.prediction_held": vocabulary["prediction_held"],
        "faculty.derived_count": sum(1 for row in ledger
                                     if row["class"] == "derived"),
        "python.nearest_shares_module": python.get("nearest_shares_module"),
        "python.digest_control": python.get("digest_control"),
        "python.chance": str(python.get("chance")),
    }
    return {
        "probe": probe,
        "lexicon": lexicon,
        "vocabulary": vocabulary,
        "python": python,
        "ledger": ledger,
        "blockers": BLOCKERS,
        "figures": figures,
        "unrecognised": unrecognised,
        "claim": (
            "what is demonstrated here is coverage and mechanism, not "
            "reasoning: the probe measures how much open natural language "
            "the system takes at all, the ledger says which of table lookup, "
            "geometric addressing and derivation each measured result "
            "actually is, and the blockers name what stands between the two."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = Path(__file__).resolve().parent / "_data" / "blockers.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/blockers.py",
    "data_objects/semantic_lexicon.py",
    "reasoning/operation_escalation.py",
    "reasoning/norm_escalation.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, ProbeQuestion):
        return {"key": value.key, "domain": value.domain,
                "question": value.question, "paraphrase": value.paraphrase,
                "expect": value.expect, "why": value.why}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The whole study, recomputed."""
    payload = dict(blockers_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")
