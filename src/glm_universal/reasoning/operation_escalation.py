"""``glm_universal.reasoning.operation_escalation`` -- escalating operations
that are not retrieval.

The question
------------
The construction ladder improves one thing that has been measured carefully:
**geometric addressing**.  A perturbed carrier is quantised at rung after rung
until a rung's cell holds exactly one carrier, and the carrier is named.  That
is retrieval, and
``studies/CONSTRUCTION_LADDER_STUDY.md`` and ``studies/NORM_FAMILY_STUDY.md``
measure it.

This module asks the next question honestly: **does escalation help anything
else?**  Six operations are declared, each with the same shape --

* an operation: a question asked of a *perturbed* carrier that is not "which
  carrier is this";
* a refusal contract: exactly when the operation is allowed to answer;
* an escalation: the same declared ladder, the same stopping rule;
* controls: the operation with the substrate removed, and the operation
  answered by the label prior, which needs no reading at all;
* a verdict, recorded whether it is positive or negative.

The six operations
------------------
``register``
    *Meaning.*  Which of the six registers does this carrier belong to --
    physics, chemistry, molecules, mathematics, harmonics or lexicon?  A
    meaning-level question: the answer is a class, not an identity.
``dimension``
    *Dimensional and unit reasoning.*  Recover the seven SI exponents of a
    physics quantity from the perturbed carrier.  The answer space is large,
    so the prior control is weak and the reading has to do real work.
``chemistry``
    *The chemistry register.*  Which block of the periodic table does this
    element belong to?
``physics``
    *The physics register.*  Which sub-domain of physics is this quantity
    from -- kinematics, thermodynamics, and so on?
``harmony``
    *Small-integer structure.*  What is the prime limit of this interval?
``program``
    *Program text.*  Which file of the Lean development does this declaration
    come from, read from its 24 structural features rather than its name?

and, measured separately because it is not a classification,

``equation``
    *Equation checking.*  Given three physics quantities and the claim
    ``dim(a) = dim(b) + dim(c)``, decide whether the claim holds -- from the
    perturbed carriers, not from the register.  The system recovers the
    exponent vectors by reading each operand at a rung and then does the
    arithmetic itself, so a correct answer is a **derivation over recovered
    values**, not a lookup.

The refusal contract
--------------------
One contract, shared by every classification operation: *answer only when the
rung's cell is non-empty and every carrier in it carries the same label;
otherwise refuse and go on to the next rung.*  This is weaker than retrieval's
contract -- which needs the cell to hold exactly **one** carrier -- and that is
the point: a rung that cannot say *which* carrier a query is may still say what
*kind* it is.  The equation operation's contract is the same applied to each
operand: every operand must be read unambiguously or the whole check is
refused.

What counts as a finding
------------------------
An operation whose escalation beats its best single rung has gained something
from the ladder.  An operation that does not is a **real finding** and is
written up as one: :func:`operation_report` records ``gain_over_best_rung``
and ``verdict`` for every operation, negative ones included.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; the perturbations are the
declared deterministic ones of
:mod:`glm_universal.reasoning.ladder_escalation`.  No float is constructed
anywhere in this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import (Callable, Dict, Hashable, List, Optional, Sequence, Tuple)

from .. import integrity
from ..substrate import construction_ladder as CL
from . import ladder_escalation as LE
from . import norm_escalation as NE

__all__ = [
    "Operation", "OPERATIONS", "REFUSAL_CONTRACT", "LADDER",
    "operation_queries", "run_operation", "operation_report",
    "equation_cases", "run_equations", "measure", "write_measurements",
    "measurements", "module_digest", "state", "current", "DATA_PATH",
]

DIM = 24

#: The ladder every operation is escalated over: the norm-indexed family,
#: coarsest first.  One ladder for all of them, so that a difference between
#: two operations is a difference in the operation.
LADDER: Tuple[str, ...] = NE.NORM_LADDER

#: The refusal contract, stated once and quoted by every report.
REFUSAL_CONTRACT: str = (
    "answer only when the rung's cell is non-empty and every carrier in it "
    "carries the same label; otherwise refuse and try the next rung. A query "
    "the whole ladder refuses is refused, never guessed.")


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE OPERATIONS
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Operation:
    """One faculty, with what a rung is supposed to give it."""

    key: str
    title: str
    question: str
    what_a_rung_adds: str
    source: Callable[[], Tuple[Tuple[str, Hashable, Tuple[Fraction, ...]], ...]]

    def carriers(self) -> Tuple[Tuple[str, Hashable, Tuple[Fraction, ...]], ...]:
        return self.source()


def _register_source(registers: Sequence[str],
                     label: Callable[[object], Hashable]
                     ) -> Callable[[], Tuple[Tuple[str, Hashable,
                                                   Tuple[Fraction, ...]], ...]]:
    def build() -> Tuple[Tuple[str, Hashable, Tuple[Fraction, ...]], ...]:
        from ..data_objects import (element_objects, harmonic_objects,
                                    mathematics_objects, molecule_objects,
                                    physics_objects, semantic_lexicon_objects)
        loaders = {
            "physics": physics_objects,
            "chemistry": element_objects,
            "molecules": molecule_objects,
            "mathematics": mathematics_objects,
            "harmonics": harmonic_objects,
            "lexicon": lambda: semantic_lexicon_objects()[0],
        }
        out: List[Tuple[str, Hashable, Tuple[Fraction, ...]]] = []
        for register in registers:
            for obj in loaders[register]()[:LE.SAMPLE_PER_REGISTER]:
                out.append((obj.name, label(obj),
                            tuple(Fraction(x) for x in obj.carrier)))
        return tuple(out)
    return build


def _si7_of(obj: object) -> Tuple[int, ...]:
    """The seven SI exponents a physics carrier holds in coordinates 10-16."""
    carrier = getattr(obj, "carrier")
    return tuple(int(carrier[i]) for i in range(10, 17))


def _lean_source() -> Tuple[Tuple[str, Hashable, Tuple[Fraction, ...]], ...]:
    """The first declarations of the Lean development, as feature carriers.

    The 24 structural features are exactly the ones
    :mod:`glm_universal.reasoning.lean_address` addresses a declaration by --
    quantifier counts, statement length, citations, namespace depth and the
    rest -- and the label is the file the declaration is written in, which is
    *not* one of the features.  So "the reading names the file" is a claim the
    scheme can fail.
    """
    from . import lean_address as LA
    table = LA.feature_table()
    by_name = {decl.name: decl for decl in LA.declarations()}
    out: List[Tuple[str, Hashable, Tuple[Fraction, ...]]] = []
    for name in sorted(table)[:LEAN_SAMPLE]:
        decl = by_name.get(name)
        if decl is None:                        # pragma: no cover - defensive
            continue
        out.append((name, decl.file,
                    tuple(Fraction(x) for x in table[name])))
    return tuple(out)


#: How many Lean declarations the program-text operation reads.
LEAN_SAMPLE: int = 144


OPERATIONS: Tuple[Operation, ...] = (
    Operation(
        key="register",
        title="meaning: which register is this?",
        question=("given a perturbed carrier, name the register it belongs "
                  "to -- physics, chemistry, molecules, mathematics, "
                  "harmonics or lexicon"),
        what_a_rung_adds=("a coarser rung tolerates a larger perturbation, and "
                          "a register is a coarse property, so a coarse rung "
                          "should answer it where a fine rung has already lost "
                          "the address"),
        source=_register_source(
            ("physics", "chemistry", "molecules", "mathematics", "harmonics",
             "lexicon"),
            lambda obj: getattr(obj, "domain")),
    ),
    Operation(
        key="dimension",
        title="dimensional reasoning: what are the SI exponents?",
        question=("given a perturbed physics carrier, recover its seven SI "
                  "dimension exponents exactly"),
        what_a_rung_adds=("the answer is a seven-integer vector, so the label "
                          "prior is nearly useless and a rung has to separate "
                          "the query from everything of another dimension"),
        source=_register_source(("physics",), _si7_of),
    ),
    Operation(
        key="chemistry",
        title="the chemistry register: which block of the table?",
        question=("given a perturbed element carrier, name its block -- "
                  "nonmetal, alkali metal, halogen and so on"),
        what_a_rung_adds=("elements of one block are near each other in the "
                          "coordinates the register uses, so a rung coarse "
                          "enough to conflate two elements of one block can "
                          "still answer the block"),
        source=_register_source(
            ("chemistry",),
            lambda obj: getattr(obj, "attributes").get("group_block")),
    ),
    Operation(
        key="physics",
        title="the physics register: which sub-domain?",
        question=("given a perturbed physics carrier, name the sub-domain it "
                  "comes from -- kinematics, thermodynamics, and so on"),
        what_a_rung_adds=("a sub-domain is a coarser property than an "
                          "identity, so it should survive a perturbation that "
                          "destroys the address"),
        source=_register_source(
            ("physics",),
            lambda obj: getattr(obj, "attributes").get("domain_name")),
    ),
    Operation(
        key="harmony",
        title="small-integer structure: what is the prime limit?",
        question=("given a perturbed interval carrier, name its prime limit"),
        what_a_rung_adds=("the prime limit is carried by a single coordinate, "
                          "so this operation tests whether escalation helps an "
                          "operation whose answer is nearly a projection"),
        source=_register_source(
            ("harmonics",),
            lambda obj: getattr(obj, "attributes").get("prime_limit")),
    ),
    Operation(
        key="program",
        title="program text: which file is this declaration from?",
        question=("given a perturbed feature vector of a Lean declaration, "
                  "name the file it is written in"),
        what_a_rung_adds=("declarations of one file share structure but not "
                          "coordinates, so this asks whether the ladder helps "
                          "where the label is only loosely carried by the "
                          "geometry"),
        source=_lean_source,
    ),
)


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE RUN
# ═════════════════════════════════════════════════════════════════════════

def operation_queries(operation: Operation
                      ) -> Tuple[Tuple[int, Tuple[Fraction, ...], Hashable], ...]:
    """``(index, query, truth)`` for every declared perturbation of every carrier."""
    entries = operation.carriers()
    out: List[Tuple[int, Tuple[Fraction, ...], Hashable]] = []
    for _, support, magnitude in LE.PERTURBATIONS:
        for i, (_, label, carrier) in enumerate(entries):
            out.append((i, LE.perturb(carrier, i, support, magnitude), label))
    return tuple(out)


def _label_index(rung: str,
                 entries: Sequence[Tuple[str, Hashable, Tuple[Fraction, ...]]]
                 ) -> Dict[Tuple[int, ...], Tuple[Hashable, ...]]:
    """``lattice point -> the labels of the carriers that quantise to it``."""
    table: Dict[Tuple[int, ...], List[Hashable]] = {}
    for _, label, carrier in entries:
        point = LE.quantise(carrier, rung).point
        table.setdefault(point, []).append(label)
    return {point: tuple(labels) for point, labels in table.items()}


def _digest_cell(vector: Sequence[Fraction], cells: int) -> Tuple[int, ...]:
    """The control's cell: a digest of the exact vector, with the substrate gone.

    The number of cells is matched to the rung being controlled, so the control
    differs from the reading in one thing only -- that its cells are decided by
    a hash rather than by a lattice.
    """
    material = ";".join(f"{value.numerator}/{value.denominator}"
                        for value in vector).encode("utf-8")
    digest = integrity.sha256_bytes(material)
    return (int.from_bytes(digest[:8], "big") % max(1, cells),)


def _digest_index(entries: Sequence[Tuple[str, Hashable, Tuple[Fraction, ...]]],
                  cells: int) -> Dict[Tuple[int, ...], Tuple[Hashable, ...]]:
    table: Dict[Tuple[int, ...], List[Hashable]] = {}
    for _, label, carrier in entries:
        table.setdefault(_digest_cell(carrier, cells), []).append(label)
    return {cell: tuple(labels) for cell, labels in table.items()}


def _answer(cell_labels: Sequence[Hashable]) -> Optional[Hashable]:
    """The refusal contract: unanimous or nothing."""
    distinct = set(cell_labels)
    return next(iter(distinct)) if len(distinct) == 1 else None


def _verdict(answer: Optional[Hashable], truth: Hashable) -> str:
    if answer is None:
        return "refused"
    return "correct" if answer == truth else "wrong"


def _score(rows: Sequence[str]) -> Dict[str, int]:
    return {
        "queries": len(rows),
        "correct": sum(1 for row in rows if row == "correct"),
        "wrong": sum(1 for row in rows if row == "wrong"),
        "refused": sum(1 for row in rows if row == "refused"),
    }


def run_operation(operation: Operation,
                  rungs: Sequence[str] = LADDER) -> Dict[str, object]:
    """One operation, escalated, against its fixed rungs and its controls."""
    entries = operation.carriers()
    ladder = tuple(rungs)
    queries = operation_queries(operation)
    indices = {rung: _label_index(rung, entries) for rung in ladder}
    cells = max((len(indices[rung]) for rung in ladder), default=1)
    digest = _digest_index(entries, cells)

    counts: Dict[Hashable, int] = {}
    for _, label, _ in entries:
        counts[label] = counts.get(label, 0) + 1
    prior_label = max(sorted(counts, key=repr), key=lambda key: counts[key])

    escalated: List[str] = []
    per_rung: Dict[str, List[str]] = {rung: [] for rung in ladder}
    control_digest: List[str] = []
    control_prior: List[str] = []
    oracle = 0
    resolving: Dict[str, int] = {}
    for _, query, truth in queries:
        answered: Optional[Hashable] = None
        stopped_at: Optional[str] = None
        for rung in ladder:
            point = LE.quantise(query, rung).point
            answer = _answer(indices[rung].get(point, ()))
            per_rung[rung].append(_verdict(answer, truth))
            if answered is None and answer is not None:
                answered, stopped_at = answer, rung
        escalated.append(_verdict(answered, truth))
        resolving[str(stopped_at)] = resolving.get(str(stopped_at), 0) + 1
        if any(per_rung[rung][-1] == "correct" for rung in ladder):
            oracle += 1
        control_digest.append(_verdict(
            _answer(digest.get(_digest_cell(query, cells), ())), truth))
        control_prior.append(_verdict(prior_label, truth))

    rung_scores = {rung: _score(rows) for rung, rows in per_rung.items()}
    best_rung, best = max(rung_scores.items(),
                          key=lambda item: (item[1]["correct"],
                                            -item[1]["wrong"]))
    ladder_score = _score(escalated)
    disagreements = 0
    for position in range(len(queries)):
        spoken = {per_rung[rung][position] for rung in ladder}
        if "correct" in spoken and "wrong" in spoken:
            disagreements += 1
    gain = ladder_score["correct"] - best["correct"]
    return {
        "operation": operation.key,
        "title": operation.title,
        "question": operation.question,
        "what_a_rung_adds": operation.what_a_rung_adds,
        "contract": REFUSAL_CONTRACT,
        "carriers": len(entries),
        "labels": len(counts),
        "queries": len(queries),
        "ladder": ladder,
        "escalation": ladder_score,
        "per_rung": rung_scores,
        "norms": tuple(CL.rung_spec(rung).minimum_norm for rung in ladder),
        "best_rung": best_rung,
        "best_rung_score": best,
        "oracle": oracle,
        "matches_oracle": ladder_score["correct"] == oracle,
        "rungs_disagree": disagreements,
        "resolving_rung": dict(sorted(resolving.items())),
        "control_substrate_removed": _score(control_digest),
        "control_label_prior": _score(control_prior),
        "prior_label": repr(prior_label),
        "gain_over_best_rung": gain,
        "gain_over_prior": (ladder_score["correct"]
                            - _score(control_prior)["correct"]),
        "gain_over_control": (ladder_score["correct"]
                              - _score(control_digest)["correct"]),
        "safe": ladder_score["wrong"] == 0,
        "verdict": ("escalation helps" if gain > 0 else
                    ("escalation buys nothing over the best single rung"
                     if gain == 0 else
                     "escalation is worse than the best single rung")),
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  EQUATION CHECKING -- A DERIVATION, NOT A LOOKUP
# ═════════════════════════════════════════════════════════════════════════

#: How many true and how many false equations the declared case set holds.
EQUATIONS_PER_CLASS: int = 24


def equation_cases() -> Dict[str, object]:
    """The declared equations, generated from the physics register.

    A case is a triple ``(a, b, c)`` and the claim ``dim(a) = dim(b) + dim(c)``
    -- the dimensional content of ``a = b · c``.  True cases are triples of the
    sample that satisfy it; false cases are triples that do not, taken in the
    same index order, so neither class is chosen.  Both classes are capped at
    :data:`EQUATIONS_PER_CLASS`, and the cap is reported with the count that
    was available.
    """
    entries = _register_source(("physics",), _si7_of)()
    vectors = [label for _, label, _ in entries]
    true_cases: List[Tuple[int, int, int]] = []
    false_cases: List[Tuple[int, int, int]] = []
    size = len(entries)
    for a in range(size):
        for b in range(size):
            for c in range(b + 1, size):
                if a in (b, c):
                    continue
                holds = all(vectors[a][k] == vectors[b][k] + vectors[c][k]
                            for k in range(7))
                if holds and len(true_cases) < EQUATIONS_PER_CLASS:
                    true_cases.append((a, b, c))
                elif (not holds and len(false_cases) < EQUATIONS_PER_CLASS
                      and len(false_cases) <= len(true_cases)):
                    false_cases.append((a, b, c))
            if (len(true_cases) >= EQUATIONS_PER_CLASS
                    and len(false_cases) >= EQUATIONS_PER_CLASS):
                break
    return {
        "entries": entries,
        "true_cases": tuple(true_cases),
        "false_cases": tuple(false_cases),
        "cap": EQUATIONS_PER_CLASS,
        "claim": "dim(a) = dim(b) + dim(c), the dimensional content of a = b·c",
    }


def run_equations(rungs: Sequence[str] = LADDER) -> Dict[str, object]:
    """Equation checking at every rung, escalated, against its controls.

    At a rung each operand is read separately: the cell it lands in must carry
    a single SI exponent vector, or the check is refused.  When all three are
    read the *system* does the arithmetic -- seven integer additions and a
    comparison -- so a correct answer here is a derivation over recovered
    values rather than a table lookup.
    """
    cases = equation_cases()
    entries = cases["entries"]                                  # type: ignore[index]
    ladder = tuple(rungs)
    indices = {rung: _label_index(rung, entries) for rung in ladder}
    cells = max((len(indices[rung]) for rung in ladder), default=1)
    digest = _digest_index(entries, cells)

    triples = [(triple, True) for triple in cases["true_cases"]] + \
              [(triple, False) for triple in cases["false_cases"]]    # type: ignore[operator]
    prior = sum(1 for _, truth in triples if truth) > len(triples) // 2

    def read_at(rung: str, query: Sequence[Fraction]
                ) -> Optional[Tuple[int, ...]]:
        point = LE.quantise(query, rung).point
        return _answer(indices[rung].get(point, ()))            # type: ignore[return-value]

    def read_control(query: Sequence[Fraction]) -> Optional[Tuple[int, ...]]:
        return _answer(digest.get(_digest_cell(query, cells), ()))  # type: ignore[return-value]

    per_rung: Dict[str, List[str]] = {rung: [] for rung in ladder}
    escalated: List[str] = []
    control_digest: List[str] = []
    control_prior: List[str] = []
    oracle = 0
    for label, support, magnitude in LE.PERTURBATIONS:
        for triple, truth in triples:
            queries = [LE.perturb(entries[i][2], i, support, magnitude)   # type: ignore[index]
                       for i in triple]
            decided: Optional[bool] = None
            for rung in ladder:
                reads = [read_at(rung, query) for query in queries]
                if any(value is None for value in reads):
                    per_rung[rung].append("refused")
                    continue
                holds = all(reads[0][k] == reads[1][k] + reads[2][k]      # type: ignore[index]
                            for k in range(7))
                per_rung[rung].append("correct" if holds == truth
                                      else "wrong")
                if decided is None:
                    decided = holds
            escalated.append("refused" if decided is None else
                             ("correct" if decided == truth else "wrong"))
            if any(per_rung[rung][-1] == "correct" for rung in ladder):
                oracle += 1
            reads = [read_control(query) for query in queries]
            if any(value is None for value in reads):
                control_digest.append("refused")
            else:
                holds = all(reads[0][k] == reads[1][k] + reads[2][k]      # type: ignore[index]
                            for k in range(7))
                control_digest.append("correct" if holds == truth
                                      else "wrong")
            control_prior.append("correct" if truth == prior else "wrong")

    rung_scores = {rung: _score(rows) for rung, rows in per_rung.items()}
    best_rung, best = max(rung_scores.items(),
                          key=lambda item: (item[1]["correct"],
                                            -item[1]["wrong"]))
    ladder_score = _score(escalated)
    return {
        "operation": "equation",
        "title": "equation checking: does dim(a) = dim(b) + dim(c)?",
        "question": ("given three perturbed physics carriers and the claim "
                     "dim(a) = dim(b) + dim(c), decide whether it holds"),
        "what_a_rung_adds": ("every operand has to be read unambiguously "
                             "before the arithmetic can be done, so the check "
                             "refuses three times as often as a single "
                             "reading and gains three times as much from a "
                             "rung that reads a query the one below cannot"),
        "contract": ("every operand must land in a cell carrying a single "
                     "exponent vector; if any one does not, the whole check "
                     "is refused"),
        "cases": len(triples),
        "true_cases": len(cases["true_cases"]),                  # type: ignore[arg-type]
        "false_cases": len(cases["false_cases"]),                # type: ignore[arg-type]
        "queries": len(escalated),
        "ladder": ladder,
        "escalation": ladder_score,
        "per_rung": rung_scores,
        "best_rung": best_rung,
        "best_rung_score": best,
        "oracle": oracle,
        "matches_oracle": ladder_score["correct"] == oracle,
        "control_substrate_removed": _score(control_digest),
        "control_label_prior": _score(control_prior),
        "prior_label": repr(prior),
        "gain_over_best_rung": ladder_score["correct"] - best["correct"],
        "gain_over_prior": (ladder_score["correct"]
                            - _score(control_prior)["correct"]),
        "gain_over_control": (ladder_score["correct"]
                              - _score(control_digest)["correct"]),
        "safe": ladder_score["wrong"] == 0,
        "derivation": ("the seven integer additions and the comparison are "
                       "done by this module over the vectors the reading "
                       "recovered; the register is consulted only to score "
                       "the answer"),
        "verdict": ("escalation helps"
                    if ladder_score["correct"] > best["correct"] else
                    ("escalation buys nothing over the best single rung"
                     if ladder_score["correct"] == best["correct"] else
                     "escalation is worse than the best single rung")),
    }


def operation_report(rungs: Sequence[str] = LADDER) -> Dict[str, object]:
    """Every operation, escalated, with its controls and its verdict."""
    rows = [run_operation(operation, rungs) for operation in OPERATIONS]
    equations = run_equations(rungs)
    everything = rows + [equations]
    helped = [row["operation"] for row in everything
              if int(row["gain_over_best_rung"]) > 0]              # type: ignore[arg-type]
    flat = [row["operation"] for row in everything
            if int(row["gain_over_best_rung"]) == 0]               # type: ignore[arg-type]
    unsafe = [row["operation"] for row in everything if not row["safe"]]
    return {
        "ladder": tuple(rungs),
        "contract": REFUSAL_CONTRACT,
        "operations": tuple(rows),
        "equation": equations,
        "helped": tuple(helped),
        "no_gain": tuple(flat),
        "unsafe": tuple(unsafe),
        "operations_measured": len(everything),
        "limits": (
            "Each operation is measured on its own register's sample and on "
            "the four declared perturbations, so the figures are about this "
            "sample and this sweep. A wrong answer is reported separately "
            "from a refusal and is never folded into an accuracy."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "operation_escalation.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/operation_escalation.py",
    "reasoning/norm_escalation.py",
    "reasoning/ladder_escalation.py",
    "substrate/norm_family.py",
    "substrate/construction_ladder.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The whole round, recomputed."""
    payload = dict(operation_report())
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
