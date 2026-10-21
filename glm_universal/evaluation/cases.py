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

Last altered 20 October 2026 (Phase 172: `report anonymous` pinned on its claim, read off the measurement, not on counts; Phase 171: two report cases re-pinned for the corpus refreshed with AdversarialDialogue.lean, ContextFrames.lean and EvidenceInUse.lean; Phase 166: two re-pinned for PiMachine.lean).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
#:
#: A case that quotes the size of the set writes ``{CASES}`` where the number
#: goes; the count is filled in below, from the set itself, so that adding a
#: case cannot leave a stale figure behind in the ground truth.
_CASES: Tuple[EvalCase, ...] = (

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
       "answer", contains=("work",),
       note="Refused as a boundary until the energy-conjugate register was "
            "built, and the refusal had two halves: the lexicon's own "
            "relation -- `temperature drives heat` -- reaches nothing from "
            "force, and the three terms share no register that dimensions "
            "them.  Both are closed by a register whose rows run across the "
            "domains: `heat = temperature x entropy` and `work = force x "
            "length` are two rows of it, `temperature effort_of heat` is "
            "the relation, and force occupies the effort column, so the "
            "relation is applied in reverse to the unique transfer whose "
            "effort is force.  The answer is derived rather than chosen "
            "because the relation is a bijection between its two columns."),
    _c("analogy-conjugate-unplaced", "analogy",
       "heat : temperature :: acceleration : ?",
       "refusal", classification="boundary",
       note="The complement of the case above, and the reason answering it "
            "is not a licence to answer anything: acceleration occupies no "
            "column of the conjugate register, so `effort_of` has no side "
            "for it to enter on.  The refusal names the criterion that "
            "failed -- role_typed -- and still reports the register split."),

    # --------------------------------------------------------------- nearest
    _c("nearest-molecule", "nearest", "nearest to H2O",
       "answer", contains=("water",),
       note="Was a gap until v1.4.0: the nearest search ranges over the "
            "names a register enumerates, and until the molecules register "
            "existed no register enumerated molecules.  It now does, and "
            "the formula is one of the carrier's indexed aliases, so the "
            "query resolves to water and ranks the register around it."),
    _c("nearest-unregistered-molecule", "nearest", "nearest to PbCl2",
       "answer", contains=("Cl2Pb", "sodium chloride"),
       note="Was the evaluation set's last gap.  `PbCl2` names no carrier "
            "the register enumerates, so the operand is handed to the "
            "formula parser: the composition is read exactly and encoded "
            "into the same 24 coordinates a registered molecule uses, every "
            "coordinate derived from the element register, and the built "
            "carrier is then ranked against the register.  Nothing is "
            "guessed -- an unparseable formula still refuses."),

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

    # ------------------------------------------------------------------ tool
    _c("tool-leech-norm-12", "tool",
       "the number of vectors of norm 12 in the leech lattice",
       "answer", contains=("is 34417656000", "counted from the Golay census"),
       note="Phase 164: the llvq tool's shell table was stored, and its "
            "norm-12 entry was wrong (34408430950); it is now counted from "
            "the Golay census by the lattice's definition and checked "
            "against the theta series."),

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

    _c("coherence-unregistered-molecule", "coherence", "coherence PbCl2",
       "answer", contains=("Cl2Pb", "NRCI"),
       note="Closed in v1.4.0.  Every solver that takes a carrier and "
            "nothing else now hands an operand no register enumerates to "
            "the molecule formula parser before refusing, so a species the "
            "element register can encode is scored rather than declined.  "
            "Nothing is guessed: the fall-through refuses in turn unless "
            "the formula parses and every coordinate is derived."),
    _c("spatial-unregistered-molecule", "spatial", "spatial PbCl2",
       "answer", contains=("Cl2Pb", "Golay distance"),
       note="The same fall-through, in the MOG presentation."),
    _c("angle-unregistered-molecule", "angle", "angle PbCl2 water",
       "answer", contains=("Cl2Pb", "cos^2"),
       note="Two operands, one registered and one built from its formula."),
    _c("cluster-unregistered-molecule", "cluster",
       "cluster PbCl2, water, ammonia",
       "answer", contains=("Cl2Pb",),
       note="A list of operands, one of which no register enumerates.  The "
            "cluster path also had to stop lower-casing its operands, since "
            "a formula's capitalisation is what names its elements."),

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
    _c("report-completion", "report", "report completion",
       "answer", contains=("1257 of 1652", "empty cells are decided",
                           "register itself unchanged"),
       note="Every empty cell of the element register is decided: filled by "
            "a rule that beat the field's own mean out of sample, or named "
            "as lacking the rule's inputs, or belonging to a field where "
            "every rule failed the gate, or to a field no rule over this "
            "register could reach."),
    _c("report-vagueness", "report", "report vagueness",
       "answer", contains=("35 of 110", "referred to a person"),
       note="The standing rule for a vague related_to triple: four routes "
            "tried in order, of which only the last asks a person, and a "
            "proposer whose rules are admitted only for agreeing with every "
            "hand decision they fire on."),
    _c("report-admission", "report", "report admission",
       "answer", contains=("a name is admissible exactly when",
                           "20 of 27 probes", "7 are refused"),
       note="The door a new word comes in by: three routes admit -- already "
            "held by a register, parses as a unit expression, is arithmetic "
            "over register names -- and the fourth refuses, conditionally "
            "and with the condition named."),
    _c("report-conjugates", "report", "report conjugates",
       "answer", contains=("7 energy domains",
                           "heat : temperature :: force : work"),
       note="The register that carries an analogy across the domains: seven "
            "rows, each checked against the physics register's own "
            "exponents, and the four criteria under which a relation may be "
            "transported at all."),
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
    _c("report-noise", "report", "report noise",
       "answer", contains=("second difference", "triangular window"),
       note="Noise used as the computation rather than as a representation: "
            "a loop chasing a two-tone signal, the condition under which its "
            "orbit closes, the cascade whose error is a second difference, "
            "and what dither costs -- each measured against a theorem of "
            "RequestProject/GLM/Cascade.lean."),
    _c("report-lattices", "report", "report lattices",
       "answer", contains=("three-resolution address", "even number of 2s"),
       note="The two rungs above the Leech lattice: the 32-dimensional "
            "Barnes-Wall lattice built by Construction D over a dual pair "
            "of Reed-Muller codes, whose payoff is an address at three "
            "resolutions, and the 48-dimensional extremal lattice, which "
            "needs a ternary code and a neighbour step decided by a parity "
            "census of the full-weight codewords."),
    _c("report-shells", "report", "report shells",
       "answer", contains=("support function", "unreachable"),
       note="Delta-sigma with the alphabet widened to a Leech shell and "
            "then to the whole lattice: the shell's support function in "
            "closed form, a target tracked inside the hull and a target "
            "certified unreachable outside it, and the Gibbs-style rule "
            "realised deterministically by greedy error feedback."),
    _c("report-llvq", "report", "report llvq",
       "answer", contains=("128 classes of 32", "0 mismatches"),
       note="The quantiser's search replaced by a table: the 4,096 Golay "
            "codewords read as 128 classes of 32 out of a 16-entry column "
            "table, the bounded class search proved least-cost in "
            "RequestProject/GLM/LLVQTable.lean, and the frozen scan kept "
            "beside it as the thing to agree with -- 0 mismatches."),
    _c("report-signature", "report", "report signature",
       "answer", contains=("floor(N t)", "binary entropy"),
       note="The spectral signature the external studies tabulate for a "
            "constant, recomputed with the law beside every measured "
            "column: the ones are exactly floor(N t), the entropy is the "
            "binary entropy of the density, and the longest run sits on "
            "its proved bound."),
    _c("report-drift", "report", "report drift",
       "answer", contains=("contractive", "truncation never helps"),
       note="One recurrence over the odd primes run three ways -- exactly, "
            "in binary64, and truncated to a display precision -- with the "
            "drift between them measured in exact arithmetic rather than "
            "in the host's floats."),
    _c("report-catalog", "report", "report catalog",
       "answer", contains=("confirmed", "refuted"),
       note="The external study findings read as a live claim ledger: every "
            "figure recomputed here and given a verdict, so a finding the "
            "package cannot reproduce is a recorded disagreement rather "
            "than an unexamined claim."),
    _c("report-containers", "report", "report containers",
       "answer", contains=("three containers", "certificate"),
       note="Eight constants through three containers -- the exact "
            "generator, the delta-sigma stream and the 24-dimensional "
            "projection -- with both hull verdicts checked against all "
            "196,560 minimal vectors, since a sample of witnesses can only "
            "ever prove that a point is inside."),
    _c("report-companion", "report", "report companion",
       "answer", contains=("confirmed", "refuted"),
       note="The two companion preprints read as a live claim ledger, "
            "finer than the catalogue's because the preprints state the "
            "projection, the indexing and the alphabet their summary "
            "omits."),
    _c("report-blueprint", "report", "report blueprint",
       "answer", contains=("testable claims",),
       note="The blueprint read as a live claim ledger: every testable "
            "sentence recomputed, and the ones that are false as written "
            "recorded as refuted with what holds instead."),
    _c("report-engine", "report", "report engine",
       "answer", contains=("radiator", "turbocharger")),
    _c("report-mantissa", "report", "report mantissa",
       "answer", contains=("binary64",),
       note="What a stored mantissa keeps and what it destroys, computed in "
            "exact integer arithmetic rather than by asking the hardware."),
    _c("report-reversible", "report", "report reversible",
       "answer", contains=("Gray",),
       note="The reversible-gate claims, each answered True or False by "
            "measurement -- several of them False, which is the point."),
    _c("report-lean", "report", "report lean",
       "answer", contains=("deterministic Leech address", "SHA-256 control"),
       note="Every declaration of the Lean development given a Leech "
            "address by its structure alone, scored on read-back fidelity "
            "and on whether address distance tracks anything -- against a "
            "digest control that knows nothing and a reshuffle that keeps "
            "the geometry."),
    _c("report-directives", "report", "report directives",
       "answer", contains=("standing rules", "instrument"),
       note="The standing rules parsed out of the project directives, with "
            "the instrument each one names checked to exist in the tree "
            "rather than assumed."),
    _c("report-searchloop", "report", "report searchloop",
       "answer", contains=("51/32", "filter"),
       note="The archive's reasoning loop -- filter on every example, then "
            "rank -- measured on the eight symmetries of the square over "
            "the 512 binary 3 x 3 grids: what one example leaves, what a "
            "second buys, and the witness that refutes ranking first."),
    _c("report-controller", "report", "report controller",
       "answer", contains=("propose-check-refuse", "re-verified",
                           "refused outright"),
       note="The multi-step loop: derive a physical quantity from the ten "
            "EXT10 generators one factor at a time, with the digit-stack "
            "verifier checking every finished plan and an invariant refusing "
            "the unreachable targets outright.  Six scorers on the same "
            "tasks, one of them the Leech address."),
    _c("report-landscape", "report", "report landscape",
       "answer", contains=("77/1066", "not a derivation of alpha",
                           "magnitude-matched"),
       note="The pre-registered wobble landscape: one statistic fixed "
            "before the measurement -- the stage-0 long-gap frequency of "
            "the Sturmian word -- against a magnitude-matched null "
            "enumerated exhaustively, scored in bits and corrected for the "
            "statistics tried.  The answer is a weak result, reported as "
            "one, and it is not a derivation of alpha."),
    _c("report-hole-classifier", "report", "report hole classifier",
       "answer", contains=("arrival-share profile", "vertex count",
                           "sanity query fails"),
       note="The pre-registered deep-hole round: can the distribution of "
            "trajectories that arrive at a hole name the hole's "
            "Coxeter-Dynkin type?  One statistic fixed before the module "
            "existed, against a digest control, a seeded reshuffle, a "
            "uniform-profile ablation and the competitor that mattered, "
            "the plain vertex count.  It beats all four and the round "
            "still stops, because the sanity query -- the same hole under "
            "a different declared ensemble -- fails."),
    _c("report-hole-ladder", "report", "report hole ladder",
       "answer", contains=("cells", "recognise", "the law descends"),
       note="The second deep-hole round: was the first round's failure the "
            "geometry or the layer it was read at?  Four readings at four "
            "ensemble sizes -- twelve cells fixed before the module existed "
            "and one extension rung added afterwards and labelled as one -- "
            "with one gate: every reference hole recognises itself under a "
            "bare seed change.  The bottom rung reproduces the first round "
            "at 3 of 10, the best pre-registered cell reaches 9 of 10, and "
            "the extension rung reaches the gate at 10 of 10, where the full "
            "query set comes out 40 of 44 against 12 for the vertex count.  "
            "So the obstruction was the reading, and the round says which "
            "reading and at what cost."),
    _c("report-retrieval", "report", "report retrieval",
       "answer", contains=("used as an index", "times the closed-form",
                           "beaten decisively"),
       note="The address book used as an index: does address-nearest "
            "retrieval find the relatives of a query, and how does it "
            "compare against a digest, a reshuffle, a random ranking, "
            "chance, a name search and a plain lexical search?  It beats "
            "every control except the last, which beats it decisively, and "
            "what the lattice earns is the completeness bound rather than "
            "the ranking."),
    _c("report-generated", "report", "report generated",
       "answer", contains=("sound and badly incomplete",
                           "1152 of the 196560",
                           "every regenerated object checked identical"),
       note="Generate rather than store, measured: what a generator saves "
            "against the table it replaces, with every regenerated object "
            "compared with the stored one, and whether the proposed "
            "on-the-fly Leech sieve is the lattice -- it is sound and keeps "
            "1,152 of the 196,560 minimal vectors."),
    _c("report-pipeline", "report", "report pipeline",
       "answer", contains=("six stages",),
       note="Study to test to implemented to measured: the stage each "
            "piece of work has reached, read off the tree rather than "
            "claimed in prose."),
    _c("report-harmony", "report", "report harmony",
       "answer", contains=("531441/524288", "not reproduced"),
       note="The harmonic register measured rather than described: equal "
            "temperament's exact error, the fifth that never closes, and "
            "the catalogue's universality claim tested against a control "
            "that it does not beat."),
    _c("report-economics", "report", "report economics",
       "answer", contains=("21 quoted prices", "scale 1024",
                           "not reproduced"),
       note="The economic register measured rather than described: the "
            "scale at which the lattice first separates all 21 records, the "
            "co-movement rate against its chance rate, and the undecoded "
            "control that scores just as well -- which is what makes the "
            "catalogue's economic claim not reproduced."),
    _c("report-escalation", "report", "report escalation",
       "answer", contains=("1094", "811", "refinement"),
       note="The layer audit run on every register carrier rather than on "
            "seven fixtures: resolution rises and stops, every boundary is "
            "still a refinement, and 283 named entries share a carrier with "
            "another and are beyond every layer."),
    _c("report-names", "report", "report names",
       "answer", contains=("283", "16 bits", "register label recovers 0"),
       note="The ceiling attacked where it lives.  An exact coordinate read "
            "off the entry's own name recovers all 283 entries no layer "
            "could separate; that much is forced, so the measurement is the "
            "sweep and the control -- 16 bits suffice, and the register "
            "label, a coordinate of the same exactness, recovers none."),
    _c("report-unknown-subject", "report", "report nonsense subject",
       "refusal", classification="boundary",
       note="An unknown subject must be refused with the list of subjects, "
            "not silently mapped to the nearest one."),
    _c("report-measure", "report", "report measure",
       "answer", contains=("45 comparison classes", "108", "0 violations"),
       note="The relative-measure study recomputed: the register's size, "
            "what the widening gains, and that it gives nothing up."),
    _c("report-denotations", "report", "report denotations",
       "answer", contains=("83 verdicts", "0 triples waiting",
                           "18 of the 26 analogies"),
       note="The denotation half of the same subject, reached by the name "
            "the question asks for: what the undimensioned endpoints of the "
            "residue denote is decided one name at a time, so nothing is "
            "left waiting on a lookup, and the conversions the decision "
            "licenses are transported rather than merely counted."),
    _c("report-recipe", "report", "report recipe",
       "answer", contains=("3 domains described", "72 coordinates",
                           "94 of 94 carriers", "regenerated"),
       note="The domain description made the object: three registers built "
            "by hand in earlier rounds are deleted and rebuilt from their "
            "descriptions alone by one generic path, and every carrier and "
            "every measured figure comes back unchanged."),

    _c("report-language", "report", "report language",
       # Re-pinned at the Phase 150-152 close: the answerable kinds are 26
       # (the shared baseline of Phases 150-151 already read 26); claim
       # unchanged, the same seven kinds described.
       # Re-pinned at Phase 154: the `corpus` kind makes the answerable
       # kinds 27; claim unchanged, the same seven kinds described.
       "answer", contains=("7 of 27 answerable query kinds",
                           "derive, measure, task, compare by slot shape",
                           "verify, analogy, compare by infix shape",
                           "comparative by nested shape",
                           "deleted and frozen",
                           "0 disagreements", "one declared widening",
                           "described"),
       note="The question shape made the object.  Seven query kinds are now "
            "read off their descriptions by the parser itself -- every "
            "branch that used to recognise them is deleted, kept frozen "
            "only so the comparison has something to measure against -- and "
            "over corpora generated from the registers the reading is the "
            "one the branches gave.  Three shape families: an opening with "
            "slots, one of which may hold a list; an operator cutting the "
            "question in two, with described modifiers and trailing "
            "options; and a nested shape whose operands are not text but "
            "matches of another shape.  The one place the descriptions read "
            "more than the branches did is declared and every widened "
            "question is accounted for by it."),

    _c("report-cumulativity", "report", "report cumulativity",
       "answer", contains=("3 declared layer families",
                           "7 refinement edges verified",
                           "conflated pairs reported as resolutions"),
       note="Cumulativity as a shipping condition: every declared "
            "refinement edge is verified on its probe set, every declared "
            "non-edge is witnessed, and the conflations each rung inflicts "
            "are reported beside them as resolutions rather than as "
            "defects."),
    _c("report-hole-failures", "report", "report hole failures",
       "answer", contains=("40 of 44", "rank-2 near misses",
                           "3 of 10 types"),
       note="The four failures of the escalated deep-hole reading, scored "
            "against four mechanisms fixed in advance: all four are rank-2 "
            "near misses on a closest reference pair, and the type whose "
            "spread stalls the separation ratio is the type they belong "
            "to, so the failures and the unmet criterion are one "
            "mechanism."),
    _c("report-hole-configuration", "report", "report hole configuration",
       "answer", contains=("44 correctly, 0 wrongly and 0 refused",
                           "0 false", "the joint reading named 40"),
       note="The configuration reading in the deep-hole answering path: "
            "the escalation round's 44 queries answered under a declared "
            "rule that answers only inside half the distance to the nearest "
            "other reference (a certificate, by "
            "GLM.LatticeCompletion.config_answer_sound) and issues every "
            "other type outside its certified radius as an absence."),
    _c("report-query-escalation", "report", "report query escalation",
       "answer", contains=("{CASES} evaluation cases", "no answer moves",
                           "4 of 18 declared probes"),
       note="Escalation as a step of the ordinary query loop: over the "
            "whole evaluation set no answer moves and no principled "
            "refusal is converted, while four declared probes are "
            "resolved above the first rung and two refusals come back as "
            "certified absences."),
    _c("report-relay", "report", "report relay",
       # Re-pinned at Phase 77: DecoderConfidence.lean grew the goal-query
       # set from 820 to 822 and re-dealt the two strides; the stack is still
       # ahead on every set, and now loses one query (was 0) while carrying 13.
       # Re-pinned at Phase 85: the goal-query set grew to 835 (HoleBounds.lean)
       # and the gate now fires on 64 of 1670; still ahead, carrying 12, losing 1.
       # Re-pinned at Phase 88: the goal-query set grew to 841 (PlannerLoop.lean)
       # and the gate now fires on 56 of 1682; still ahead on every set,
       # carrying 11, losing 1.
       # Re-pinned at Phase 89: the goal-query set grew to 844 (QuestionSetB.lean)
       # and the gate now fires on 52 of 1688; still ahead on every set,
       # carrying 14, losing 1.
       # Re-pinned at Phase 92: with TypedOperators, DeclaredFrames and
       # DiscourseState the corpus is 4416 declarations, the stride 4416 // 400
       # = 11 (was 10), so the goal-query set is 803 and the gate fires on 42
       # of 1606; still ahead on every set, carrying 13, losing 1.
       # Re-pinned in the sharpening pass after Phase 108: the Lean corpus
       # at 4676 declarations (Phase 108) makes the goal-query set 851 and
       # the gate fires on 60 of 1702; still ahead on every set, carrying
       # 15, losing 0.
       # Re-pinned in the Phase 109 close: QuarticResolvent.lean and
       # SignFactor.lean (4691 declarations) make the goal-query set 853 and
       # the gate fires on 58 of 1706; still ahead on every set, carrying
       # 18, losing 0.
       # Re-pinned at Phase 110: StrayBlind.lean (4706 declarations) makes
       # the goal-query set 856 and the gate fires on 64 of 1712; still
       # ahead on every set, carrying 20, losing 0.
       # Re-pinned at Phase 123: the corpus at 4903 declarations (Phases
       # 111-123) makes the goal-query set 818 and the gate fires on 46 of
       # 1636; still ahead on every set, carrying 8, losing 0.
       # Re-pinned at Phase 125: OperationsLadder.lean (the corpus refreshed
       # with it) makes the goal-query set 822 and the gate fires on 54 of
       # 1644; still ahead on every set, carrying 10, losing 0.
       # Re-pinned at Phase 126: InertCounter.lean (the corpus refreshed
       # with it) makes the goal-query set 823 and the gate fires on 44 of
       # 1646; still ahead on every set, carrying 7, losing 0.
       # Re-pinned at Phase 130: CounterLasso.lean (the corpus refreshed
       # with it) makes the goal-query set 835 and the gate fires on 56 of
       # 1670; still ahead on every set, carrying 14, losing 0.
       # Re-pinned at Phase 132: AffineOutput.lean (the corpus refreshed
       # with it) makes the goal-query set 840 and the gate fires on 44 of
       # 1680; still ahead on every set, carrying 8, losing 0.
       # Re-pinned at Phase 134 (ProtectedTag.lean; the corpus refreshed
       # with Phases 133-134) makes the goal-query set 848 and the gate fires
       # on 62 of 1696; still ahead on every set, carrying 15, losing 0.
       # Re-pinned at Phase 135 (ShortestTag.lean) makes the goal-query set
       # 854 and the gate fires on 62 of 1708; still ahead on every set,
       # carrying 15, losing 0.
       # Re-pinned at Phase 136 (CertifiedStreams.lean) makes the goal-query
       # set 856 and the gate fires on 54 of 1712; still ahead on every set,
       # carrying 18, losing 0.
       # Re-pinned at Phase 138 (NearestFraction.lean) makes the goal-query
       # set 860 and the gate fires on 54 of 1720; still ahead on every set,
       # carrying 18, losing 0.
       # Re-pinned again at Phase 138 (the last NearestFraction.lean
       # declarations, le_fib_succ and search_terminates) makes the set 862
       # and the gate fires on 54 of 1724; still ahead, carrying 18, losing 0.
       # Re-pinned at Phase 139 (PrimalityCertificate.lean) makes the set
       # 864 and the gate fires on 56 of 1728; still ahead on every set,
       # carrying 16, losing 0.
       # Re-pinned at Phase 140 (PocklingtonCertificate.lean and
       # LucasCertificate.lean; the declaration count moves the stride, so
       # the set is 805) and the gate fires on 36 of 1610; still ahead on
       # every set, carrying 14, losing 0.
       # Re-pinned at Phase 141 (EllipticCertificate.lean) makes the set
       # 809 and the gate fires on 36 of 1618; still ahead on every set,
       # carrying 14, losing 0.
       # Re-pinned at Phase 142 (QuadraticLasso.lean) makes the set 813 and
       # the gate fires on 46 of 1626; still ahead on every set, carrying
       # 12, losing 0.
       # Re-pinned at Phase 144 (CoordinateJunction.lean) makes the set 817
       # and the gate fires on 38 of 1634; still ahead on every set,
       # carrying 9, losing 0.
       # Re-pinned at Phase 145 (TimedQuestion.lean) makes the set 822 and
       # the gate fires on 38 of 1644; still ahead on every set, carrying
       # 9, losing 0.
       # Re-pinned at the Phase 150-152 close (the Lean files of Phases
       # 146-151, the corpus refreshed with them) makes the set 830 and the
       # gate fires on 32 of 1660; still ahead on every set, carrying 6,
       # losing 0.
       # Re-pinned at Phase 154 (CorpusKnowledge.lean and the knowledge
       # package) makes the set 835 and the gate fires on 40 of 1670; still
       # ahead on every set, carrying 5, losing 0.
       # Re-pinned at Phase 155 (CorpusDefinitions.lean and the knowledge
       # modules) makes the set 837 and the gate fires on 56 of 1674; still
       # ahead on every set, carrying 12, losing 0.
       # Re-pinned at Phase 157 (FrictionTwo.lean, DomainWheels.lean and the
       # Phase 156 file, the corpus refreshed with them) makes the set 843 and
       # the gate fires on 50 of 1686; still ahead on every set, carrying 17,
       # losing 0.
       # Re-pinned at Phase 158 (OscillatorJunction.lean, the corpus refreshed
       # with it) makes the set 845 and the gate fires on 50 of 1690; still
       # ahead on every set, carrying 17, losing 0.
       # Re-pinned at Phase 159 (ThermoFriction.lean, the corpus refreshed
       # with it) makes the set 847 and the gate fires on 44 of 1694; still
       # ahead on every set, carrying 15, losing 0.
       # Re-pinned at Phase 160 (FoldMachine.lean, the corpus refreshed with
       # it) makes the set 850 and the gate fires on 60 of 1700; still ahead
       # on every set, carrying 13, losing 0.
       # Re-pinned at Phase 161 (StudyLedger.lean, the corpus refreshed with
       # it) makes the set 851 and the gate fires on 58 of 1702; still ahead
       # on every set, carrying 13, losing 0.
       # Re-pinned at Phase 162, 18 October 2026 (SourceTiers.lean, the
       # corpus refreshed with it) makes the set 853 and the gate fires on 58
       # of 1706; still ahead on every set, carrying 13, losing 0.
       # Re-pinned at Phase 164, 19 October 2026 (ToolMachine.lean,
       # LeechMachine.lean and LeechShells.lean, the corpus refreshed with
       # them): the stride grows by one, so the set is 803 and the gate fires
       # on 46 of 1606; still ahead on every set, carrying 10, losing 0.
       # Re-pinned at Phase 165, 19 October 2026 (LeechKissing.lean, the
       # corpus refreshed with it): the set is 811 and the gate fires on 30
       # of 1622; still ahead on every set, carrying 7, losing 0.
       # Re-pinned at Phase 166, 19 October 2026 (PiMachine.lean, the corpus
       # refreshed with it): the set is 812 and the gate fires on 44 of
       # 1624; still ahead on every set, carrying 9, losing 0.
       # Phase 171, 20 October 2026: pinned on the claim, not the counts.
       # Every Lean file added since Phase 161 moved the counts and forced a
       # re-pin (the corpus refreshed with AdversarialDialogue.lean and
       # ContextFrames.lean gave a set of 816, with EvidenceInUse.lean 817),
       # and every re-pin staled the stored measurements that digest this
       # file.  The report's standing words are read off the measurement
       # (`standing`: ahead, level or behind), so the pin now asks for what
       # the case claims -- ahead on all three sets, losing nothing.
       "answer", contains=("(ahead), a disjoint held-out stride",
                           "(ahead) and bare goal queries",
                           "(ahead), carrying",
                           "queries it misses and losing 0."),
       note="The faculties arranged as a stack rather than scored one at a "
            "time: below a gate of 1/10 the leading lexical search is "
            "judged to have abstained and the two geometric address books "
            "answer in its place, by a stated quota.  The stack is ahead "
            "of the text-only control at k = 5 on the tuning stride, on a "
            "disjoint held-out stride and on bare goal queries, and the "
            "matched digest-and-reshuffle control carries far fewer, so "
            "the gain is the substrate's rather than the padding's."),
    _c("report-anonymous", "report", "report anonymous",
       # Re-pinned at Phase 85 (queries 822 -> 835 as the Lean corpus grew
       # to 4171 declarations); claim unchanged.
       # Re-pinned at Phase 88 (queries 835 -> 841 with PlannerLoop.lean);
       # claim unchanged: text and identifier book to chance, structure holds.
       # Re-pinned at Phase 89 (queries 841 -> 844 with QuestionSetB.lean);
       # claim unchanged.
       # Re-pinned at Phase 92 (queries 844 -> 803: 4416 declarations, the
       # stride 11 where it was 10); claim unchanged.
       # Re-pinned in the sharpening pass after Phase 108 (queries 803 ->
       # 851 as the Lean corpus grew to 4676 declarations by Phase 108,
       # which left this pin unmoved): text 699 -> 68, structure 192 -> 188;
       # claim unchanged.
       # Re-pinned at Phase 109 (queries 851 -> 853 with QuarticResolvent.lean
       # and SignFactor.lean, 4691 declarations): text 711 -> 65, structure
       # 180 -> 175; claim unchanged.
       # Re-pinned at Phase 110 (queries 853 -> 856 with StrayBlind.lean,
       # 4706 declarations): text 708 -> 67, structure 184 -> 181; claim
       # unchanged.
       # Re-pinned at Phase 123 (queries 856 -> 818, 4903 declarations):
       # text 693 -> 51, structure 149 -> 145; claim unchanged.
       # Re-pinned at Phase 125 (queries 818 -> 822 with
       # OperationsLadder.lean): text 691 -> 48, structure 149 -> 146;
       # claim unchanged.
       # Re-pinned at Phase 126 (queries 822 -> 823 with InertCounter.lean):
       # text 710 -> 52, structure 163 -> 161; claim unchanged.
       # Re-pinned at Phase 130 (queries 823 -> 835 with CounterLasso.lean):
       # text 686 -> 53, structure 165 -> 163; claim unchanged.
       # Re-pinned at Phase 132 (queries 837 -> 840 with AffineOutput.lean):
       # text 699 -> 53, structure 153 -> 150; claim unchanged.
       # Re-pinned at Phase 134 (queries 840 -> 848 with ProtectedTag.lean
       # and the Phase 133 files): text 692 -> 47, structure 165 -> 164;
       # claim unchanged.
       # Re-pinned at Phase 135 (queries 848 -> 854 with ShortestTag.lean):
       # text 697 -> 47, structure 167 -> 166; claim unchanged.
       # Re-pinned at Phase 136 (queries 854 -> 856 with
       # CertifiedStreams.lean): text 711 -> 50, structure 169 -> 168; claim
       # unchanged.
       # Re-pinned at Phase 138 (queries 856 -> 860 with
       # NearestFraction.lean): text 714 -> 49, structure 173 -> 172; claim
       # unchanged.
       # Re-pinned again at Phase 138 (queries 860 -> 862 with the last
       # NearestFraction.lean declarations): text 714 -> 49, structure
       # 174 -> 173; claim unchanged.
       # Re-pinned at Phase 139 (queries 862 -> 864 with
       # PrimalityCertificate.lean): text 713 -> 52, structure 167 -> 165;
       # claim unchanged.
       # Re-pinned at Phase 140 (queries 864 -> 805 with
       # PocklingtonCertificate.lean and LucasCertificate.lean, the stride
       # moving with the declaration count): text 676 -> 50, structure
       # 165 -> 161; claim unchanged.
       # Re-pinned at Phase 141 (queries 805 -> 809 with
       # EllipticCertificate.lean): text 679 -> 50, structure 167 -> 163;
       # claim unchanged.
       # Re-pinned at Phase 142 (queries 809 -> 813 with
       # QuadraticLasso.lean): text 661 -> 45, structure 161 -> 157; claim
       # unchanged.
       # Re-pinned at Phase 144 (queries 813 -> 817 with
       # CoordinateJunction.lean): text 691 -> 51, structure 143 -> 141;
       # claim unchanged.
       # Re-pinned at Phase 145 (queries 817 -> 822 with
       # TimedQuestion.lean): text 687 -> 51, structure 139 -> 137; claim
       # unchanged.
       # Re-pinned at the Phase 150-152 close (queries 822 -> 830 with the
       # Lean files of Phases 146-151): text 701 -> 41, structure 157 -> 156;
       # claim unchanged.
       # Re-pinned at Phase 154 (queries 830 -> 835 with
       # CorpusKnowledge.lean): text 703 -> 47, structure 147 -> 145; claim
       # unchanged.
       # Re-pinned at Phase 155 (queries 835 -> 837 with
       # CorpusDefinitions.lean): text 677 -> 56, structure 151 -> 149; claim
       # unchanged.
       # Re-pinned at Phase 157 (queries 837 -> 843 with FrictionTwo.lean,
       # DomainWheels.lean and Friction.lean): text 702 -> 47, structure
       # 164 -> 162; claim unchanged.
       # Re-pinned at Phase 158 (queries 843 -> 845 with
       # OscillatorJunction.lean): text 703 -> 47, structure 165 -> 163; claim
       # unchanged.
       # Re-pinned at Phase 159 (queries 845 -> 847 with
       # ThermoFriction.lean): text 710 -> 51, structure 168 -> 166; claim
       # unchanged.
       # Re-pinned at Phase 160 (queries 847 -> 850 with FoldMachine.lean):
       # text 682 -> 54, structure 157 -> 155; claim unchanged.
       # Re-pinned at Phase 161 (queries 850 -> 851 with StudyLedger.lean):
       # text 683 -> 54, structure 153 -> 152; claim unchanged.
       # Re-pinned at Phase 162, 18 October 2026 (queries 851 -> 853 with
       # SourceTiers.lean): text 685 -> 54, structure 154 -> 153; claim
       # unchanged.
       # Re-pinned at Phase 164, 19 October 2026 (queries 853 -> 803: the
       # three new Lean files grow the sampling stride by one): text
       # 655 -> 53, structure 156 -> 157; claim unchanged.
       # Re-pinned at Phase 165, 19 October 2026 (queries 803 -> 811 with
       # LeechKissing.lean): text 687 -> 63, structure 166 -> 167; claim
       # unchanged.
       # Re-pinned at Phase 166, 19 October 2026 (queries 811 -> 812 with
       # PiMachine.lean): text 671 -> 60, structure 170 -> 171; claim
       # unchanged.
       # Re-pinned at Phase 171, 20 October 2026 (queries 812 -> 816 with
       # AdversarialDialogue.lean, ContextFrames.lean and EvidenceInUse.lean):
       # text 669 -> 49, structure 153 -> 154; claim unchanged.  With
       # EvidenceInUse.lean too (queries 816 -> 817): text 674 -> 57,
       # structure 154 -> 153; claim unchanged.
       # Phase 172, 20 October 2026: pinned on the claim, not the counts,
       # as `report relay` has been since Phase 171.  The report now reads
       # its standing off the measurement's verdict and names any check that
       # fails; the pin forbids a failure of the four checks the claim rests
       # on.  Reading it showed that one check the sentence used to assert
       # does not hold (`text_is_within_twice_chance`: text 57 against 23 by
       # chance, more than twice), so the words "both to chance" became
       # "against chance".
       "answer", contains=("class, not a residue",
                           "Standing, read off the measurement:"),
       forbids=("text_collapses_without_the_names", "address_holds",
                "address_is_the_clear_leader", "gate_hands_over"),
       note="The register where the geometric address is the only faculty "
            "still reading: rename every identifier of a query outside a "
            "declared vocabulary and the text search and the identifier "
            "address book both fall to chance, while the structural address "
            "keeps most of what it had, because a renaming cannot move a "
            "count of the syntax."),
    _c("report-review-sweep", "report", "report review sweep",
       "answer", contains=("8 stalled results", "retrieval-hit-at-5",
                           "0 entry defects"),
       note="The review-sweep register of directive D13: the standing set "
            "of stalled results ranked by whether the coarse reading "
            "discarded an identifiable quantity, written before the next "
            "re-reading rather than after it."),
    _c("report-routes", "report", "report routes",
       "answer", contains=("3 decision points with 8 routes",
                           "9 of 9 reference problems",
                           "every route reached"),
       note="Phase 109: the route choices that showed only in column 2 of "
            "the answer making them, listed in one place -- every decision "
            "point, its routes and deciders, and one reference problem per "
            "route run live, so a route that stops being reached is a "
            "changed row rather than silence."),

    # --------------------------------------------------------------- measure
    _c("measure-hot-tea", "measure", "measure hot in tea",
       "answer", contains=("363/1", "K"), forbids=("44000",),
       note="293 + 7/8 * (373 - 293) = 363 K, exactly.  A measure word is "
            "relative: the answer is the class's bracket read at the word's "
            "position, not a property of the word alone."),
    _c("measure-hot-star", "measure", "measure hot in stellar_surface",
       "answer", contains=("44000/1", "K"), forbids=("363/1 K --",),
       note="The same word against a different class is a different "
            "magnitude, which is the whole content of the claim that the "
            "reading is relative."),
    _c("measure-hot-across-classes", "measure", "measure hot",
       "answer", contains=("363/1", "44000/1", "6 classes"),
       note="One word, six brackets, six magnitudes -- the static concept "
            "carrier is the same in all six."),
    _c("measure-magnitude-in-tea", "measure", "measure 300 in tea",
       "answer", contains=("cold", "7/80"),
       note="The other direction: a magnitude earns the word whose scale "
            "position is nearest, and 300 K is cold for tea."),
    _c("measure-large-room-volume", "measure",
       "measure large in room_volume",
       "answer", contains=("1755/4", "m^3"),
       note="10 + 7/8 * (500 - 10) = 1755/4 cubic metres, exactly.  `large` "
            "is `property_of size` and the register calls that quantity "
            "volume; the alias resolves the two names and every coordinate "
            "of the reading still comes out of the physics register."),
    _c("measure-dark-indoor", "measure", "measure dark in indoor_lighting",
       "answer", contains=("675/4", "lx"),
       note="The light half of the same step: `dark` is `property_of light`, "
            "which the register holds as illuminance, so the word that used "
            "to be refused is now an exact number of lux."),
    _c("measure-large-room", "measure", "measure large in room",
       "refusal", classification="boundary",
       note="`large` measures a volume and *room* brackets a length, so the "
            "two are about different quantities and no measurement is "
            "defined.  This used to refuse because the registers held no "
            "size at all; what refuses now is the mismatch, which is a "
            "stricter boundary rather than a missing one."),
    _c("measure-expensive-market", "measure", "measure expensive in market",
       "refusal", classification="boundary",
       note="`expensive` is on no measure scale at all.  The refusal names "
            "which register is missing the word rather than guessing a "
            "nearest one."),
    _c("measure-hot-walking", "measure", "measure hot in walking",
       "refusal", classification="boundary",
       note="A temperature word against a velocity class: the two registers "
            "disagree about the quantity, and no measurement is defined."),

    # ----------------------------------------------------------- comparative
    _c("comparative-cold-star-hotter-than-hot-tea", "comparative",
       "is cold in stellar_surface hotter than hot in tea",
       "answer", contains=("Yes", "8000/1", "363/1"), forbids=("No:",),
       note="The reversal the comparative exists for: *cold*, for a star, is "
            "8000 K and *hot*, for a cup of tea, is 363 K, although `cold` "
            "sits below `hot` on the scale.  A machine that compared the two "
            "concepts would answer this backwards; "
            "`GLM.Info.comparative_not_determined_by_word_order` is the "
            "theorem that it must."),
    _c("comparative-hot-tea-hotter-than-cold-tea", "comparative",
       "is hot in tea hotter than cold in tea",
       "answer", contains=("Yes", "363/1", "303/1"),
       note="Within one class the word order does decide it, and exactly: "
            "`GLM.Info.hotterThan_iff_position_lt`."),
    _c("comparative-false-claim", "comparative",
       "is cold in tea hotter than hot in tea",
       "answer", contains=("No",), forbids=("Yes:",),
       note="A false comparative is answered false rather than refused: the "
            "registers reach it, so there is a fact of the matter."),
    _c("comparative-equative", "comparative",
       "is warm in tea as hot as cold in stellar_surface",
       "answer", contains=("No", "343/1", "8000/1"),
       note="The equative asks for equality of magnitudes, which 343 K and "
            "8000 K are not."),
    _c("comparative-cross-quantity", "comparative",
       "is hot in tea hotter than fast in walking",
       "refusal", classification="boundary",
       note="Both sides are perfectly well measured and still incomparable: "
            "a temperature and a velocity are on no common scale.  "
            "`GLM.Info.hotTea_not_comparable_fastWalking`."),
    _c("comparative-wrong-scale-marker", "comparative",
       "is fast in walking hotter than slow in airliner",
       "refusal", classification="boundary",
       note="*hotter* is a temperature comparative and the pair measures "
            "velocity; the marker cannot order magnitudes of another "
            "quantity."),
    _c("comparative-midpoint-word", "comparative",
       "is tepid in tea tepider than cold in tea",
       "refusal", classification="boundary",
       note="`tepid` sits exactly at the middle of the temperature scale, so "
            "its comparative names no direction.  The direction a marker "
            "asserts is read off the register rather than listed, and at the "
            "midpoint the register does not decide it."),

    # ---------------------------------------------------------------- derive
    _c("derive-span-ratio-tea", "derive", "derive span_ratio of tea",
       "answer", contains=("373/293", "quotient", "comparison"),
       forbids=("1.27",),
       note="The coordinate is answered off the domain description rather "
            "than off a hand-written phrase: 373/293 is the tea bracket's "
            "span as an exact rational, computed by the shared `quotient` "
            "primitive that also serves a frequency ratio and a price."),
    _c("derive-numerator-perfect-fifth", "derive",
       "derive numerator of perfect_fifth",
       "answer", contains=("= 3", "harmonics"),
       note="The same query surface reaches a second described domain with "
            "no new parsing rule, which is what makes the path generic."),
    _c("derive-euler-gradus", "derive",
       "derive euler_gradus of perfect_fifth",
       "answer", contains=("= 4", "judgement"),
       note="A coordinate the description cannot build from shared "
            "primitives is marked a judgement rather than hidden: Euler's "
            "gradus of 3/2 is 1 + (2 - 1) + (3 - 1) = 4."),
    _c("derive-undescribed-coordinate", "derive",
       "derive cents of perfect_fifth",
       "refusal", classification="boundary",
       note="A cent is a logarithm, so no description derives it, and the "
            "refusal is exactly the boundary "
            "`GLM.Recipe.Spec.answer_eq_none_iff` describes: the answered "
            "coordinates are the described ones and no others."),

    # ----------------------------------------------------------------- field
    _c("field-atomic-weight-carbon", "field",
       "field atomic_weight_u of carbon",
       "answer", contains=("12011/1000", "12.011", "element"),
       note="The fact the probe oracle found held and unreachable: the row "
            "has always carried it and no query kind returned it.  Exact, "
            "with the terminating decimal beside the rational because one "
            "exists."),
    _c("field-group-block-chlorine", "field",
       "field group_block of chlorine",
       "answer", contains=("Halogen", "Cl"),
       note="A row is resolved by a name it holds itself -- here the "
            "element's `name` field rather than its symbol."),
    _c("field-molar-mass-water", "field", "field molar_mass_u of water",
       "answer", contains=("3603/200", "18.015", "recomputed"),
       note="The molecule register declares this derived rather than "
            "stored, so the answer says it was recomputed and names the "
            "rule: a surface that let a derived value pass as a held one "
            "would be claiming more than it does."),
    _c("field-lean-declaration-file", "field",
       "field file of GLM.NormFamily.family_tower",
       "answer", contains=("NormFamily.lean", "address"),
       note="The Lean address book read as a table: one declaration, one "
            "field, rather than the aggregate `report lean` gives."),
    _c("field-listing-shape", "field",
       "fields of glm_universal.substrate.norm_family.completeness",
       "answer", contains=("complete", "rungs", "function"),
       note="How *what does this return?* is asked without naming the "
            "answer in the question: the keys of a declared function's "
            "returned mapping are its fields."),
    _c("field-unknown-field", "field", "field boiling_point of carbon",
       "refusal", classification="boundary",
       note="The field is refused with the list of the fields the row does "
            "answer to -- `boiling_point_K` is the name it holds -- rather "
            "than answered with a blank or guessed at."),
    _c("field-missing-value", "field", "field electronegativity_pauling of He",
       "refusal", classification="boundary",
       note="Helium's row records this field as missing, and the "
            "missingness mask is a fact about the register: answering "
            "`none` as though it were a value would hide it."),
    _c("field-unknown-row", "field", "field name of unobtainium",
       "refusal", classification="boundary",
       note="No declared table holds the row, and the refusal carries the "
            "nearest row names rather than a bare failure."),

    # -------------------------------------------------------------- ordering
    _c("ordering-abstractness", "ordering",
       "order abstract_concrete of energy and water",
       "answer", contains=("1/4", "3/4", "abstract", "energy"),
       note="The one question the field surface declared unreachable, "
            "closed: one coordinate read off two rows, checked to be on one "
            "scale, and ordered exactly.  The pole is the lexicon "
            "register's own declaration, and the answer says so."),
    _c("ordering-atomic-weight", "ordering",
       "order atomic_weight_u of carbon and oxygen",
       "answer", contains=("997/250", "element:atomic_weight_u"),
       note="The same operation over a stored coordinate of a second "
            "table: the gap is the exact difference of two rationals."),
    _c("ordering-derived-coordinate", "ordering",
       "order molar_mass_u of water and ethanol",
       "answer", contains=("14027/500", "molecule:molar_mass_u"),
       note="Both readings are recomputed rather than stored, and a "
            "derived coordinate is orderable on the same terms as a held "
            "one so long as both rows are read on one scale."),
    _c("ordering-level", "ordering",
       "order animate_inanimate of energy and water",
       "answer", contains=("level with",),
       forbids=("is below", "is above"),
       note="Two readings that are equal are reported as level and no pole "
            "is named: the register declares an end, not a winner."),
    _c("ordering-nominal", "ordering", "order kind of energy and water",
       "refusal", classification="boundary",
       note="`kind` is a label rather than a quantity, and a nominal "
            "coordinate has no order to read; the refusal says which "
            "reading was not a number."),
    _c("ordering-across-scales", "ordering",
       "order line of GLM.NormFamily.family_tower and rung_audit",
       "refusal", classification="boundary",
       note="The boundary the whole operation is built around: `line` is "
            "held by the Lean address book and by the package's own source "
            "walk, and two readings on different scales have no common "
            "order.  `GLM.CoordinateOrder.naive_order_is_not_scale_free` "
            "exhibits a rescaling that flips the comparison of the bare "
            "numbers."),
    _c("ordering-unreadable", "ordering",
       "order atomic_weight_u of carbon and water",
       "refusal", classification="boundary",
       note="The second row is held and does not carry the coordinate, so "
            "the surface's own refusal is restated with the fields that row "
            "does answer to rather than reclassified."),

    # ------------------------------------------------------------- extremum
    _c("extremum-heaviest", "extremum",
       "largest atomic_weight_u in element",
       "answer", contains=("Og", "36902/125", "118 rows"),
       note="The column rather than the pair: one coordinate read off every "
            "row of one declared table, folded exactly, with the gap to the "
            "next distinct value stated as a rational."),
    _c("extremum-lightest", "extremum",
       "smallest atomic_weight_u in element",
       "answer", contains=("H", "126/125"),
       note="The other end of the same column. The two ends are one "
            "operation -- the smallest is the largest of the negated "
            "column, which is `GLM.ColumnExtremum.trough_eq_none_iff` -- "
            "and they name different rows."),
    _c("extremum-derived-column", "extremum",
       "largest molar_mass_u in molecule",
       "answer", contains=("iron(III) sulfate", "199939/500"),
       note="Every reading of the column is recomputed from the element "
            "register rather than stored, and a derived column folds on the "
            "same terms as a held one so long as it is one scale."),
    _c("extremum-tie", "extremum",
       "largest abstract_concrete in carrier:lexicon",
       "answer", contains=("14 rows", "water"),
       note="Fourteen rows sit at the concrete end of the lexicon "
            "register's coordinate. Every one of them is named: a tie is a "
            "fact about the register, and picking one would be a choice the "
            "register does not make."),
    _c("extremum-holes", "extremum",
       "largest electronegativity_pauling in element",
       "refusal", classification="boundary",
       note="The refusal the operation exists for: 23 of the 118 rows "
            "record the coordinate as missing, and the largest of the 95 "
            "present values is the largest of the rows that happen to be "
            "filled in rather than of the column. "
            "`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` "
            "exhibits a column where the two differ, so an answer over the "
            "present rows is wrong rather than partial."),
    _c("extremum-two-tables", "extremum", "largest line",
       "refusal", classification="boundary",
       note="The ordering operation's `different-scale`, one level up: with "
            "no table named, `line` is gathered from the Lean address book "
            "and from the package's own source walk, and the largest of "
            "those numbers jointly is a fact about neither table."),
    _c("extremum-nominal", "extremum", "largest name in element",
       "refusal", classification="boundary",
       note="A column of labels has no extremum, and the refusal says which "
            "reading was not a quantity rather than ordering the spelling."),
    _c("extremum-absent", "extremum", "largest boiling_point in element",
       "refusal", classification="boundary",
       note="No row of the named table answers for the coordinate -- "
            "`boiling_point_K` is the name it holds -- so there is no "
            "column to fold."),

    # -------------------------------------------------------------- carrier
    #  Phase 134 (studies/PROTECTED_TAG_STUDY.md, section 3.1): one carrier,
    #  message 0x5a3, codeword 0x8ad5a3, tag 0x54, fifteen-bit tag 0x1a54.
    _c("carrier-clean", "carrier", "carrier 0x8ad5a3",
       "answer", contains=("0x8ad5a3", "0x5a3", "0 flips"),
       note="A codeword read as itself: the decoder alone, no flips."),
    _c("carrier-two-flips", "carrier", "carrier 0x88d5ab",
       "answer", contains=("0x8ad5a3", "0x5a3", "2 flips"),
       note="Two flips are inside the decoder's radius, so the fork has one "
            "candidate and no stage is needed."),
    _c("carrier-tie", "carrier", "carrier 0xca97a1",
       "refusal", classification="boundary",
       note="Four flips leave six equidistant codewords, and no function of "
            "the received word resolves them -- "
            "`GLM.Golay24.weight4_resolved_le_4096` -- so the read refuses "
            "and names all six rather than picking one."),
    _c("carrier-tag", "carrier", "carrier 0xca97a1 tag 0x54",
       "answer", contains=("0x8ad5a3", "0x5a3", "sender tag"),
       note="The same tie with the sender's seven-bit tag: the tag stage "
            "removes five candidates, which is `GLM.Golay24.tag_resolves`."),
    _c("carrier-protected-tag", "carrier",
       "carrier 0xca97a1 protected tag 0x1256",
       "answer", contains=("0x8ad5a3", "protected tag"),
       note="The fifteen-bit tag with two of its bits flipped still resolves "
            "the tie to the sent carrier, which is "
            "`GLM.Golay24.tag15_corrects_two`; the seven-bit tag absorbs no "
            "flip (`tag7_one_flip_misleads`)."),
    _c("carrier-flagged", "carrier", "carrier 0xca9781 tag 0x54",
       "refusal", classification="boundary",
       note="Five flips: the decoder alone answers the wrong codeword "
            "0x428781 at distance 3, and the intact tag disagrees with it, "
            "so the read refuses -- `GLM.Golay24.tag_flags_miscorrection`: "
            "a decoder's silent wrong answer turned into a refusal."),
    _c("carrier-soft", "carrier",
       "carrier soft 13/16, 7/16, 1/16, 0, 3/16, 7/8, 1/16, 1, 13/16, 9/16, 15/16, 0, 13/16, 1/8, 13/32, 1, 3/16, 7/8, 1/16, 1, 3/16, 1/8, 19/32, 1",
       "answer", contains=("0x8ad5a3", "soft certificate"),
       note="Read 0 of Phase 133's gentle ensemble: the hard word is the "
            "tie 0xca97a1, and the soft certificate keeps one candidate, "
            "which is `GLM.Golay24.soft_certificate`."),
    _c("carrier-not-a-word", "carrier", "carrier 0x1000000",
       "refusal", classification="boundary",
       note="Twenty-five bits are not a carrier."),
    _c("carrier-tag-width", "carrier", "carrier 0xca97a1 tag 0x154",
       "refusal", classification="boundary",
       note="A nine-bit value is not a seven-bit tag, and the read says so "
            "rather than truncating it."),

    # --------------------------------------------------------------- locate
    #  Phase 143 (studies/ADDRESS_READ_STUDY.md, section 3.2): a point read
    #  off the construction ladder by its address, under the placement guard.
    _c("locate-clean", "locate", "locate C",
       "answer", contains=("chemistry:C", "strictly nearest", "rung C"),
       note="A carrier read as itself: its own cell at the middle rung holds "
            "only it and the placement guard holds, so the answer is "
            "certified the strictly nearest carrier "
            "(`GLM.AddressRead.read_strict_nearest`)."),
    _c("locate-moved", "locate", "locate C moved 8 by 1/2",
       "answer", contains=("chemistry:C", "rung 2A", "read_origin"),
       note="Carbon moved on eight coordinates by 1/2: the cells of the "
            "first two rungs visited (C, A) are empty, the third (2A) "
            "certifies, and the move of length "
            "sqrt 2 is inside the margin, so the answer is certified to be "
            "the carrier the point came from (`GLM.AddressRead.read_origin`)."),
    _c("locate-point", "locate",
       "locate 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, "
       "0, 0, 0, 0 within 1/2",
       "answer", contains=("golay_codeword_1", "rung A/2", "read_origin"),
       note="Twenty-four coordinates and a bound on the move: five rungs "
            "find the cell shared, the sixth certifies, and no other carrier "
            "lies within the margin of 2.581."),
    _c("locate-uncertified", "locate", "locate perfect_fifth moved 2 by 2",
       "refusal", classification="boundary",
       note="No rung's cell holds one carrier with its guard holding, so the "
            "read refuses rung by rung rather than name an uncertified "
            "carrier (`GLM.AddressRead.read_none_iff`)."),
    _c("locate-ambiguous", "locate", "locate water",
       "refusal", classification="boundary",
       note="Two registers hold a carrier named water; the read names both "
            "and asks which, rather than picking one."),
    _c("locate-unknown", "locate", "locate Fe",
       "refusal", classification="boundary",
       note="Iron is not among the 142 carriers the address table holds."),
    #  Phase 144 (studies/COORDINATE_JUNCTION_STUDY.md): carriers that share
    #  exact coordinates are read as a junction, Phase 66's rule for names.
    _c("locate-junction", "locate", "locate albedo",
       "answer", contains=("junction", "physics:absorptance",
                           "physics:albedo", "no_read_separates",
                           "declared distinct"),
       note="Absorptance and albedo have the same 24 coordinates, so no read "
            "can name one of them; the read answers their junction, certified "
            "strictly nearer than every other carrier "
            "(`GLM.CoordinateJunction.jread_junction_nearest`), and reports "
            "the declaration that they are two measurands, not one."),
    _c("locate-junction-moved", "locate", "locate filled_2x12 moved 4 by 1/2",
       "answer", contains=("junction", "mathematics:filled_4x6",
                           "jread_origin"),
       note="A moved matrix of the eight `filled_*` (same entries, different "
            "shapes): the move is inside the junction's margin, so the "
            "carrier it came from is certified to be in the junction "
            "(`GLM.CoordinateJunction.jread_origin`)."),
    _c("locate-junction-crowded", "locate", "locate golay_codeword_0",
       "refusal", classification="boundary",
       note="The zero word's junction (Golay and hexacode) shares every cell "
            "with two nearby carriers that are not in it, so no rung "
            "certifies it and the read refuses rather than name it."),
    _c("locate-dimension", "locate", "locate 1, 2, 3",
       "refusal", classification="boundary",
       note="Three coordinates are not a point of the 24-dimensional "
            "substrate."),
    #  Phase 146 (studies/ANSWERING_QUESTION_STUDY.md): the junction answer
    #  ends with the question that would split it, and replies are given.
    _c("locate-reply", "locate", "locate acoustic_power_level given "
       "attr:unit is dB",
       "answer", contains=("leave 2 of the 3 members",
                           "physics:acoustic_intensity_level",
                           "the GLM asks: Does its description mention "
                           "'intensity'?", "after_reply"),
       note="One reply (the unit is dB) leaves two of the three acoustic "
            "members, and the answer ends with the next question, which "
            "splits them (`GLM.AnsweringQuestion.after_reply`)."),
    _c("locate-reply-confirmed", "locate", "locate albedo given "
       "word:absorbed is no; confirm:physics:albedo is yes",
       "answer", contains=("it is physics:albedo", "resolved_eq_truth",
                           "the confirming reply agrees"),
       forbids=("the GLM asks",),
       note="A reply resolves the junction to albedo and the confirming "
            "reply agrees, so the answer puts no further question."),
    _c("locate-reply-contradicted", "locate", "locate albedo given "
       "word:absorbed is no; confirm:physics:albedo is no",
       "refusal", classification="boundary",
       note="The confirming reply contradicts the first, so no member is "
            "left; the GLM reports the contradiction and does not choose "
            "(`GLM.AnsweringQuestion.confirm_catches`)."),
    _c("locate-reply-no-tie", "locate", "locate C given attr:unit is dB",
       "refusal", classification="boundary",
       note="Carbon reads as a single carrier, so there is no tie for a "
            "reply to resolve."),

    # ------------------------------------------- the budget rule (Phase 147)
    _c("hole-walk", "hole", "hole walk 1",
       "answer", contains=("D_24", "certified complete", "budget rule"),
       note="A declared walk reaches a deep hole and the reading, with no "
            "barren stop and the proved budget of 1056 starts, certifies "
            "its type (`GLM.BudgetReading.budget_agrees`)."),
    _c("hole-octad-pair", "hole", "hole octad pair",
       "answer", contains=("A_1^24", "48 vertices"),
       note="The octad-pair midpoint, built from the substrate's own "
            "codewords, read under the budget rule."),
    _c("hole-patience-refused", "hole", "hole walk 3006",
       "answer", contains=("D_16 E_8", "certified complete"),
       note="The walk's own reading (200 starts, patience 40) left this "
            "deep hole uncertified; under the budget rule the reading runs "
            "on to its certificate (`GLM.BudgetReading.patience_may_refuse`)."),
    _c("hole-lattice-point", "hole",
       "hole 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0",
       "refusal", classification="boundary",
       note="A lattice point sits in no deep hole, decided by start 0."),
    _c("hole-malformed", "hole", "hole walk x",
       "refusal", classification="boundary",
       note="A walk is named by its index."),

    # --------------------------- the corpus as what the GLM knows (Phase 154)
    _c("corpus-define", "corpus", "corpus define golay code",
       "answer", contains=("The corpus says", "Golay code"),
       note="What the project's own corpus says the Golay code is, with the "
            "sentence's address; ranked by where the sentence stands."),
    _c("corpus-continue", "corpus", "corpus continue a digest addresses",
       "answer", contains=("integrity never meaning",),
       note="The corpus's own most frequent continuation, each token with a "
            "witness sentence; a tie would stop it (GLM.CorpusKnowledge."
            "predict_eq_none_of_tie)."),
    _c("corpus-unmentioned", "corpus", "corpus define zyxwv",
       "refusal", classification="boundary",
       note="A term no sentence of the corpus mentions is refused, never "
            "guessed."),

    # ------------- a word's place on the lattice, from its corpus counts (Phase 155)
    _c("corpus-address", "corpus", "corpus address of seven",
       "answer", contains=("sits at the Leech point", "read back exactly: True",
                           "six"),
       note="A word's 24 positional coordinates, quantised onto the Leech "
            "lattice and read back exactly; its nearest words on the lattice "
            "are the other number words (CORPUS_DEFINITIONS_STUDY.md, W2')."),
    _c("corpus-address-phrase", "corpus", "corpus address of golay code",
       "refusal", classification="boundary",
       note="A lattice address is for one word; a phrase is refused with the "
            "reason."),

    # ------------------------------ the guarded read in nearest (Phase 148)
    _c("nearest-address-moved", "nearest", "nearest to C moved 8 by 1/2",
       "answer", contains=("chemistry:C", "certifies the head",
                           "ranking_head_origin"),
       note="A moved carrier no register holds, ranked against the 142 "
            "carriers of the address table; the guarded read certifies the "
            "head and the gap after it (`GLM.NearestAddress`)."),
    _c("nearest-address-point", "nearest",
       "nearest to 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, "
       "0, 0, 0, 0, 0",
       "answer", contains=("mathematics:golay_codeword_1",
                           "certifies the head"),
       note="24 exact coordinates ranked by full scan, the head certified."),
    _c("nearest-address-uncertified", "nearest",
       "nearest 3 to harmonics:perfect_fifth moved 2 by 2",
       "answer", contains=("harmonics:perfect_fifth",
                           "no margin is certified"),
       note="No rung certifies the point: the ranking stands, its head the "
            "strict nearest by scan (`ranking_head_of_strict`), and the "
            "answer says no margin is certified."),
    _c("nearest-address-junction", "nearest",
       "nearest to albedo moved 4 by 1/4",
       "answer", contains=("physics:absorptance", "physics:albedo",
                           "member of the junction"),
       note="The head of the ranking is a junction, two carriers at one "
            "exact coordinate vector."),
    _c("nearest-address-ambiguous", "nearest",
       "nearest to water moved 8 by 1/2",
       "refusal", classification="boundary",
       note="'water' names two carriers of the address table."),

    # ------------------------------- the question at the ties (Phase 150)
    _c("nearest-tie-question", "nearest",
       "nearest to 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
       "0, 0, 0, 0, 0",
       "answer", contains=("no margin is certified",
                           "the GLM asks: What is its field order?"),
       note="The scan finds two carriers at distance 0 where the guarded "
            "read refuses; the answer ends with the question that splits "
            "them (studies/NEAREST_QUESTION_STUDY.md)."),
    _c("nearest-tie-reply", "nearest",
       "nearest to albedo moved 4 by 1/4 given word:absorbed is no",
       "answer", contains=("leave 1 of the 2 carriers of the head",
                           "physics:albedo", "after_least",
                           "Is it exactly physics:albedo?"),
       note="A reply leaves one member of the certified junction and never "
            "moves the answer off the head "
            "(`GLM.NearestQuestion.after_least`); the confirming question "
            "follows."),
    _c("nearest-tie-confirmed", "nearest",
       "nearest to albedo moved 4 by 1/4 given word:absorbed is no; "
       "confirm:physics:albedo is yes",
       "answer", contains=("resolved_is_meant", "the confirming reply agrees"),
       forbids=("the GLM asks",),
       note="The confirming reply agrees, so no further question is put."),
    _c("nearest-tie-contradicted", "nearest",
       "nearest to albedo moved 4 by 1/4 given word:absorbed is no; "
       "confirm:physics:albedo is no",
       "refusal", classification="boundary",
       note="The replies leave no member of the head; the GLM reports the "
            "contradiction rather than choose "
            "(`GLM.NearestQuestion.outside_never_confirmed`)."),
    _c("nearest-tie-no-tie", "nearest",
       "nearest to C moved 8 by 1/2 given word:absorbed is no",
       "refusal", classification="boundary",
       note="The head is the single carrier chemistry:C, so there is no "
            "tie for a reply to resolve "
            "(`GLM.NearestQuestion.head_card_le_one_iff`)."),

    # ----------------------------------------------------- scale conversion
    _c("scales-mass-across-tables", "ordering",
       "order atomic_weight_u of carbon and molar_mass_u of water",
       "answer", contains=("1501/250", "declared conversions", "in u"),
       note="One quantity held under two field names in two tables. The "
            "declared conversion table relates the two scales, both "
            "readings are carried into unified atomic mass units and the "
            "comparison is taken there; a positive conversion cannot move "
            "a verdict, which is `GLM.ScaleConversion.cmpQ_apply`."),
    _c("scales-energy-across-units", "ordering",
       "order ionization_energy_eV of hydrogen and "
       "homonuclear_bde_kJ_per_mol of hydrogen",
       "answer", contains=("kJ/mol", "is above"),
       note="The one declared conversion with a factor other than 1: an "
            "electronvolt per atom is `N_A e` joules per mole, exact by "
            "the 2019 SI definitions, so the comparison is exact too."),
    _c("scales-column-by-quantity", "extremum", "largest mass",
       "answer", contains=("iron(III) sulfate", "169 rows", " u "),
       note="A column no table holds: the 118 element rows and the 51 "
            "molecule rows, gathered into one unit by the declared table "
            "and folded exactly."),
    _c("scales-different-quantity", "ordering",
       "order atomic_weight_u of carbon and melting_point_K of iron",
       "refusal", classification="boundary",
       note="The table relates scales of one quantity and declares no "
            "conversion between two: a mass and a temperature have no "
            "common order, and the refusal names both quantities."),
    _c("scales-quantity-with-holes", "extremum", "largest temperature",
       "refusal", classification="boundary",
       note="Gathering by quantity does not weaken the hole refusal: 40 of "
            "the 236 melting and boiling points are recorded as missing, "
            "and the extremum of the rows that are filled in is a wrong "
            "answer rather than a partial one."),
)


def _fill_case_count(cases: Tuple[EvalCase, ...]) -> Tuple[EvalCase, ...]:
    """Substitute the size of the set for ``{CASES}`` in every ground truth.

    The evaluation set is its own subject in one case -- the escalation
    report states how many cases it ran over -- and hand-typing that number
    has twice gone stale as the set grew.  The token is replaced here, after
    the set is complete, so the figure is read off the set rather than
    remembered.
    """
    count = str(len(cases))

    def fill(strings: Tuple[str, ...]) -> Tuple[str, ...]:
        return tuple(s.replace("{CASES}", count) for s in strings)

    return tuple(
        replace(case, contains=fill(case.contains), forbids=fill(case.forbids))
        for case in cases)


#: The question set with every ``{CASES}`` token resolved.
CASES: Tuple[EvalCase, ...] = _fill_case_count(_CASES)


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
