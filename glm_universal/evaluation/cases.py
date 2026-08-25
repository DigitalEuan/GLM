"""The fixed question set the end-to-end evaluation scores.

Every case is a question a user could type at the CLI, together with what the
*right* answer is -- decided by mathematics or by the design of the register,
never by what the machine happens to print.  A case declares one of two
expectations:

``expect="answer"``
    the question has an answer and the machine should give it.  ``contains``
    lists substrings that a right answer must have (matched case-insensitively
    against the answer line), and ``forbids`` substrings it must not have.

``expect="refusal"``
    the honest answer is to refuse.  ``classification`` says *why*:

    ``"boundary"``
        refusing is correct and cannot be improved on -- the obstruction is a
        theorem or a deliberate limit of the register (equality of two
        processes is undecidable; a word outside the registers denotes
        nothing).  A machine that answered here would be guessing.
    ``"gap"``
        the refusal is a missing implementation.  The question is answerable
        in principle and the parts are already in the package; nothing joins
        them.  These are the work items.

A refusal counts as a pass when it was expected and as a *mild* failure when
it was not.  A confident answer where the honest answer is a refusal, or an
answer that contradicts the ground truth, counts as a *severe* failure -- the
scoring in :mod:`glm_universal.evaluation.harness` is deliberately harsher on
being confidently wrong than on declining to answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

__all__ = ["EvalCase", "CASES", "cases_by_kind", "KINDS_COVERED",
           "SUBJECTS_COVERED"]


@dataclass(frozen=True)
class EvalCase:
    """One question, and what the right answer is."""

    id: str
    kind: str
    question: str
    expect: str                       # "answer" | "refusal"
    contains: Tuple[str, ...] = ()
    forbids: Tuple[str, ...] = ()
    classification: str = ""          # "" | "boundary" | "gap"
    note: str = ""

    def __post_init__(self) -> None:
        if self.expect not in ("answer", "refusal"):
            raise ValueError(f"{self.id}: expect must be answer or refusal")
        if self.expect == "refusal" and self.classification not in (
                "boundary", "gap"):
            raise ValueError(
                f"{self.id}: an expected refusal must be classified")
        if self.expect == "answer" and not self.contains:
            raise ValueError(f"{self.id}: an expected answer needs a ground "
                             f"truth to check")


def _c(*args, **kwargs) -> EvalCase:
    return EvalCase(*args, **kwargs)


#: The whole question set, in reading order.
CASES: Tuple[EvalCase, ...] = (

    # ---------------------------------------------------------------- verify
    _c("verify-newton", "verify", "verify force = mass * acceleration",
       "answer", contains=("holds",), forbids=("does not hold",),
       note="Newton's second law is dimensionally exact."),
    _c("verify-power", "verify", "verify power = energy / time",
       "answer", contains=("holds",), forbids=("does not hold",)),
    _c("verify-pressure", "verify", "verify pressure = force / area",
       "answer", contains=("holds",), forbids=("does not hold",)),
    _c("verify-false", "verify", "verify energy = mass * velocity",
       "answer", contains=("does not hold",),
       note="L^2 M T^-2 against L M T^-1: the machine must refuse a false "
            "identity rather than accept it."),
    _c("verify-scaled-false", "verify",
       "verify force = mass * acceleration * 10",
       "answer", contains=("does not hold",),
       note="A decimal factor changes the scale, so the equation is false as "
            "written."),
    _c("verify-angular-momentum", "verify",
       "verify angular_momentum = momentum * length",
       "answer", contains=("does not hold",),
       note="True in SI7 and false in the active EXT10 basis, where angular "
            "momentum carries an angle exponent.  The verdict is correct for "
            "the basis in force; the benchmark records the discrepancy."),

    # --------------------------------------------------------------- analogy
    _c("analogy-alkali", "analogy", "Li : Na :: Be : ?",
       "answer", contains=("Mg",),
       note="Down one period in the next group: Be -> Mg."),
    _c("analogy-antonym", "analogy", "hot : cold :: fast : ?",
       "answer", contains=("slow",)),
    _c("analogy-halogen", "analogy", "F : Cl :: O : ?",
       "answer", contains=("S",)),
    _c("analogy-reciprocal", "analogy", "length : wavenumber :: time : ?",
       "answer", contains=("frequency",),
       note="Wavenumber is reciprocal length and frequency is reciprocal "
            "time.  Answered by the `reciprocal_dimension` model: a "
            "reflection of the exponent vector, not a displacement of it."),
    _c("analogy-noble-gas", "analogy", "He : Ne :: Ar : ?",
       "answer", contains=("Kr",),
       note="The next noble gas after argon is krypton.  Answered by the "
            "`periodic_step` model in derived table coordinates."),
    _c("analogy-boron-carbon", "analogy", "B : Al :: C : ?",
       "answer", contains=("Si",),
       note="Down one period in the carbon group: C -> Si."),
    _c("analogy-states-of-matter", "analogy",
       "solid : liquid :: liquid : ?",
       "answer", contains=("gas",),
       note="The next state along the same ladder.  Answered from the "
            "register's own triples -- `gas opposite_of liquid` -- with the "
            "operands excluded, rather than from the primitive metric, "
            "which puts the hypernym `fluid` nearer."),
    _c("analogy-scale", "analogy", "gram : mass :: millisecond : ?",
       "answer", contains=("time",),
       note="A change of decimal scale by 10^3, transported to another "
            "dimension: the `scale_shift` model."),
    _c("analogy-empty-table-position", "analogy", "Ca : Sc :: Ba : ?",
       "refusal", classification="boundary",
       note="The step is one group to the right, and period 6 group 3 holds "
            "fifteen elements -- the f-block sits there -- so the position "
            "names no single element.  Naming one would be a choice the "
            "table does not make."),
    _c("analogy-cross-register", "analogy",
       "heat : temperature :: force : ?",
       "refusal", classification="boundary",
       note="Both halves of the refusal are stated.  The relation the "
            "lexicon does carry -- `temperature drives heat` -- reaches "
            "nothing when looked up from force in either direction; and the "
            "three terms do not share a register, since physics holds "
            "temperature and force but not heat, so the query is answerable "
            "only in the lexicon, which is not where the question lives.  "
            "Answering with an unrelated energy-like quantity is a "
            "confident wrong answer."),

    # --------------------------------------------------------------- nearest
    _c("nearest-molecule", "nearest", "nearest to H2O",
       "answer", contains=("water",),
       note="Was a gap until v1.4.0: the nearest search ranges over the "
            "names a register enumerates, and until the molecules register "
            "existed no register enumerated molecules.  It now does, and "
            "the formula is one of the carrier's indexed aliases, so the "
            "query resolves to water and ranks the register around it."),
    _c("nearest-unregistered-molecule", "nearest", "nearest to PbCl2",
       "refusal", classification="gap",
       note="The gap the molecules register moved rather than closed.  The "
            "formula parser reads `PbCl2` and the molecule codec would "
            "encode it -- every coordinate is derived from the element "
            "register, so no new datum is needed -- but the nearest search "
            "resolves its operand against the names a register enumerates "
            "and stops there.  Joining the two, so that an unregistered "
            "formula can be ranked against the register, is the work "
            "item."),

    # -------------------------------------------------------------- describe
    _c("describe-carbon", "describe", "describe carbon",
       "answer", contains=("chemistry",)),
    _c("describe-energy", "describe", "what is energy",
       "answer", contains=("physics",)),
    _c("describe-water", "describe", "describe water",
       "answer", contains=("water",)),
    _c("describe-unknown-word", "describe", "describe unobtainium",
       "refusal", classification="boundary",
       note="No such carrier exists in any register; guessing a near "
            "spelling would be worse than refusing."),
    _c("describe-formula", "describe", "describe PbCl2",
       "answer", contains=("compound", "PbCl2"),
       note="A formula no register spells still denotes something the "
            "element register pins down, so the describe route asks the "
            "reference resolver before refusing.  Was a gap until v1.3.0.  "
            "The case moved from H2O to PbCl2 in v1.4.0, because H2O is now "
            "a register entry and takes the carrier route instead."),
    _c("describe-registered-formula", "describe", "describe C6H12O6",
       "answer", contains=("glucose", "molecules"),
       note="A formula the molecules register does carry resolves to its "
            "carrier, not merely to its denotation: the formula is an "
            "indexed alias of the molecule."),
    _c("describe-arithmetic", "describe", "what is energy divided by time",
       "answer", contains=("power", "L^2 M T^-3"),
       note="Arithmetic over register names: the dimension is exact, and the "
            "answer names every register quantity that carries it rather "
            "than picking one.  Was a gap until v1.3.0."),
    _c("describe-numeral-arithmetic", "describe", "what is 2 + 2",
       "answer", contains=("4",),
       note="Arithmetic inside a description, in numerals: the reference "
            "resolver reads the expression and the answer is the number it "
            "denotes.  Was a gap until v1.3.0."),

    # --------------------------------------------------------------- nearest
    _c("nearest-pressure", "nearest", "nearest 5 to pressure",
       "answer", contains=("nearest to pressure",)),
    _c("nearest-carbon", "nearest", "nearest 3 to carbon",
       "answer", contains=("N", "O"),
       note="Carbon's neighbours in the periodic table are its nearest "
            "carriers under the Griess metric."),

    # --------------------------------------------------------------- product
    _c("product-sakuma", "product", "sakuma product",
       "answer", contains=("1/8",),
       note="The 2A Norton-Sakuma product a.b = (1/8)(a + b - c)."),

    # --------------------------------------------------------------- cluster
    _c("cluster-cno", "cluster", "cluster C, N, O into 2",
       "answer", contains=("2 clusters",)),

    # --------------------------------------------------------------- spatial
    _c("spatial-oxygen", "spatial", "mog grid of oxygen",
       "answer", contains=("brick weights",)),

    # --------------------------------------------------------------- project
    _c("project-carbon-oxygen", "project", "project carbon oxygen",
       "answer", contains=("layers",)),

    # ------------------------------------------------------------- trilinear
    _c("trilinear-triple", "trilinear", "trilinear 127 432 463",
       "answer", contains=("-3/32",),
       note="The invariant of a pairwise-2A triple."),
    _c("trilinear-nonaxes", "trilinear", "trilinear 1 2 3",
       "refusal", classification="boundary",
       note="1, 2 and 3 are not 2A axes, so the form is not defined on them."),

    # ------------------------------------------------------------- coherence
    _c("coherence-carbon", "coherence", "coherence carbon",
       "answer", contains=("NRCI",)),

    # ----------------------------------------------------------------- angle
    _c("angle-carbon-oxygen", "angle", "angle carbon oxygen",
       "answer", contains=("cos^2",)),

    # ------------------------------------------------------------------ task
    _c("task-grid", "task", "task grid",
       "answer", contains=("rotate180",),
       note="The ARC-style task: the rule is a 180-degree rotation."),
    _c("task-physics", "task", "task physics",
       "answer", contains=("torque",)),
    _c("task-concepts", "task", "task concepts",
       "answer", contains=("entropy",)),

    # ------------------------------------------------------------- pi_groups
    _c("pi-groups-force", "pi_groups",
       "pi groups force, mass, acceleration, length, time",
       "answer", contains=("2 Pi group", "rank 3"),
       note="Five quantities of rank 3 leave 5 - 3 = 2 dimensionless groups."),
    _c("pi-groups-energy", "pi_groups", "pi groups energy, mass, velocity",
       "answer", contains=("1 Pi group",),
       note="Three quantities of rank 2 leave one group, E/(m v^2)."),

    # --------------------------------------------------------------- meaning
    _c("meaning-water", "meaning", "meaning of water",
       "answer", contains=("compound",)),
    _c("meaning-numeral", "meaning", "meaning of 42",
       "answer", contains=("42",)),
    _c("meaning-roman", "meaning", "meaning of XIV",
       "answer", contains=("14",)),
    _c("meaning-relate-synonyms", "meaning", "relate energy work",
       "answer", contains=("same",),
       note="Energy and work are the same dimension, L^2 M T^-2."),
    _c("meaning-relate-conflated", "meaning", "relate energy torque",
       "answer", contains=("si7_conflates",),
       note="SI7 conflates them; EXT10 does not."),
    _c("meaning-open-vocabulary", "meaning", "meaning of justice",
       "refusal", classification="boundary",
       note="The vocabulary is exactly the registers.  A word with no "
            "determinate referent must be refused, not approximated."),

    # ------------------------------------------------------------------ real
    _c("real-sqrt2", "real", "approximate sqrt(2) to 20 places",
       "answer", contains=("1.41421356237309504880",)),
    _c("real-pi", "real", "approximate pi to 20 places",
       "answer", contains=("3.14159265358979323846",)),
    _c("real-e", "real", "approximate exp(1) to 20 places",
       "answer", contains=("2.71828182845904523536",)),
    _c("real-phi", "real", "approximate (1+sqrt(5))/2 to 12 places",
       "answer", contains=("1.618033988749",)),
    _c("real-divide-by-zero", "real", "approximate 1/0 to 5 places",
       "refusal", classification="boundary",
       note="A quotient by an exact zero names no value.  Before this run "
            "the CLI raised an uncaught ZeroDivisionError here."),

    # --------------------------------------------------------------- compare
    _c("compare-pi-355", "compare", "is pi less than 355/113",
       "answer", contains=("true",),
       note="pi = 3.14159265... < 3.14159292... = 355/113."),
    _c("compare-sqrt2-1_5", "compare", "compare sqrt(2) and 1.5",
       "answer", contains=("sqrt(2) < 1.5",)),
    _c("compare-2pi-9", "compare", "is 2^pi less than 9",
       "answer", contains=("true",),
       note="2^pi = 8.8249... < 9."),
    _c("compare-equality", "compare", "is 0.1 + 0.2 equal to 0.3",
       "refusal", classification="boundary",
       note="Equality of two processes is not decidable; the machine must "
            "say it cannot distinguish them rather than assert equality."),

    # --------------------------------------------------------------- unknown
    _c("unknown-nonsense", "unknown",
       "please compute the square root of a banana",
       "refusal", classification="boundary",
       note="Not any query kind; the machine should say so and list what it "
            "does understand."),

    # ---------------------------------------------------------------- report
    _c("report-relations", "report", "report relations",
       "answer", contains=("222",)),
    _c("report-leech-distribution", "report", "report leech distribution",
       "answer", contains=("93150",),
       note="The Lambda/2Lambda class census: 93,150 classes of type 0."),
    _c("report-theta", "report", "report theta",
       "answer", contains=("196560", "16773120"),
       note="The theta series of the Leech lattice."),
    _c("report-subalgebra", "report", "report subalgebra",
       "answer", contains=("none_associative': True",)),
    _c("report-information-loss", "report", "report information loss",
       "answer", contains=("substrate",)),
    _c("report-golay-decoding", "report", "report golay decoding",
       "answer", contains=("4096 cosets", "S(5,8,24)")),
    _c("report-superposition", "report", "report superposition",
       "answer", contains=("3433/1024", "1771"),
       note="The coset census and the exact mean coset weight."),
    _c("report-leech-construction", "report", "report leech construction",
       "answer", contains=("196560",)),
    _c("report-facets", "report", "report facets",
       "answer", contains=("6 facets",)),
    _c("report-monster-stack", "report", "report monster stack",
       "answer", contains=("depth 10",)),
    _c("report-multiresolution", "report", "report multiresolution",
       "answer", contains=("GF(4)",)),
    _c("report-migration", "report", "report migration",
       "answer", contains=("8 of 4096",)),
    _c("report-state-migration", "report", "report state migration",
       "answer", contains=("4282 concepts",)),
    _c("report-concept-store", "report", "report concept store",
       "answer", contains=("4680 concepts",)),
    _c("report-fusion", "report", "report fusion",
       "answer", contains=("9 axes",)),
    _c("report-benchmarks", "report", "report benchmarks",
       "answer", contains=("5 suites",)),
    _c("report-semantics", "report", "report semantics",
       "answer", contains=("83 of 4282",)),
    _c("report-infinite-values", "report", "report infinite values",
       "answer", contains=("1.41421356237309504880",)),
    _c("report-analogies", "report", "report analogies",
       "answer", contains=("relation models",),
       note="Re-solves every analogy case through the relation-model layer "
            "and says which model recognised each relation."),
    _c("report-transform-decoder", "report", "report transform decoder",
       "answer", contains=("49152", "n = 2k"),
       note="The Walsh-Hadamard route to the 4,096 coset costs, its "
            "measured operation count against the direct summation, and "
            "the certified constant-time tier."),
    _c("report-units", "report", "report units",
       "answer", contains=("steradian", "lumen"),
       note="Every unit string in the physics register is parsed and "
            "checked against the exponents declared beside it, and the "
            "cost of reading the steradian as dimensionless is measured."),
    _c("report-deep-holes", "report", "report deep holes",
       "answer", contains=("196,560", "shortfall"),
       note="The Niemeier classification obtained by walking to a hole and "
            "certifying the reading, with the coverage shortfall reported "
            "rather than hidden."),
    _c("report-capabilities", "report", "report capabilities",
       "answer", contains=("33 probes",)),
    _c("report-molecules", "report", "report molecules",
       "answer", contains=("51 molecules", "bundle"),
       note="The multi-carrier register: the bundle is checked to be "
            "faithful and the composite is checked for collisions rather "
            "than assumed injective."),
    _c("report-chemistry-coverage", "report", "report chemistry coverage",
       "answer", contains=("covalent", "residual"),
       note="The three honest widenings of a sparse register -- derive, "
            "estimate with the error measured, cross-check without "
            "merging -- each keeping its label."),
    _c("report-unknown-subject", "report", "report nonsense subject",
       "refusal", classification="boundary",
       note="An unknown subject must be refused with the list of subjects, "
            "not silently mapped to the nearest one."),
)


def cases_by_kind() -> Dict[str, Tuple[EvalCase, ...]]:
    """The cases grouped by query kind, in reading order."""
    out: Dict[str, list] = {}
    for case in CASES:
        out.setdefault(case.kind, []).append(case)
    return {k: tuple(v) for k, v in out.items()}


#: Every query kind the set exercises.
KINDS_COVERED: Tuple[str, ...] = tuple(cases_by_kind())

#: Every report subject the set exercises, as written in the question.
SUBJECTS_COVERED: Tuple[str, ...] = tuple(
    case.question[len("report "):] for case in CASES
    if case.kind == "report" and case.expect == "answer")
