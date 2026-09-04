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
       note="The standing rules parsed out of PROJECT_DIRECTIVES.md, with "
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
       "answer", contains=("1040", "757", "refinement"),
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
       "answer", contains=("36 verdicts", "0 triples waiting",
                           "12 of the 22 analogies"),
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
       "answer", contains=("7 of 20 answerable query kinds",
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
