"""``glm_universal.evaluation.meta_question_cases`` -- the declared cases of
Phase 117: track M of ``studies/QUESTION_SET_B_STUDY.md`` §8, the eighteen
outside questions about the GLM's own engineering (class M of the Capability
Failure Matrix).

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.meta_report`.  Every expectation below was worked
out by reading the project's documents and code, not from the machine's
output.

The operation
-------------
A **meta frame** reads a question that names the machine (the GLM, "your
benchmark", "the system", a refusal code, the TCT columns) *and* one declared
topic, and answers it from the project's own material:

* **quoted evidence** -- one or more sentences of a study, each found by a
  declared fragment and quoted as the document has it *at the time of the
  read*, with the section it sits in;
* **cited theorems** -- Lean declarations, each looked up in the development
  when the question is read;
* **code facts** -- a constant or a function of the package, read from its
  source;
* **disputed premises** -- where the question's premise is not what the
  documents say, the reading says so, with the document's words;
* a **column-3 script** that re-checks the quotes against the files, the
  theorems against the Lean sources, and the mathematics of the answer by an
  independent computation.

If a declared fragment is no longer in its document, or a cited declaration
is no longer in the development, the reading is refused ``CITATION_MOVED``
rather than answered from a memory of the document.

Declarations
------------
* :data:`META_QUESTIONS` -- the eighteen class-M questions, by index in
  ``Outside_Question_Set_B_candidate_O1.txt``: the topic that must read each,
  the verdict, a fragment the answer must contain, the documents it must
  quote, the Lean declarations it must cite and the premises it must dispute.
* :data:`PARAPHRASES` -- two rewordings per question, written now, each to be
  read by the same topic.
* :data:`NOT_READ` -- near misses the meta frame must not read: questions
  about the same mathematics that do not name the machine, and questions
  that name the machine but no declared topic.
* :data:`MUTATIONS` -- the controls on the evidence.
* :data:`PRE_EXISTING` / :data:`THIS_ROUND` -- which answers rest only on
  material that existed before the round, and which rest on this round's
  Lean file as well.
* :data:`MARKS` -- the ladder.

Corrections made while reading the documents (before any code): question
101 (bit growth in exact arithmetic) was first expected to be refused
``NOT_IN_CORPUS``; the symbolic-parameters study §1 and §4.1 (first
written here as "§0 and §1", corrected after the run) record exactly
that growth (a 4 x 4 system taking more than five minutes) and its repair
(fraction-free Bareiss determinants, exact division by earlier pivots,
lowest terms by a gcd), so it is declared answered.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["META_QUESTIONS", "PARAPHRASES", "HELD_OUT", "NOT_READ", "MUTATIONS",
           "PRE_EXISTING", "THIS_ROUND", "LEAN_THEOREMS", "MARKS"]

PAPER = "studies/GLM_ACADEMIC_PAPER.md"
QSB = "studies/QUESTION_SET_B_STUDY.md"
OMEGA = "studies/INTEGER_DECISION_STUDY.md"
FORK = "studies/CARRIED_FORK_STUDY.md"
ADDR = "studies/LEAN_ADDRESS_STUDY.md"
SYMB = "studies/SYMBOLIC_PARAMETERS_STUDY.md"

M = "GLM.MetaAnswers."

#: ``(index, topic, verdict, fragment, documents, lean declarations,
#: disputes)``.  ``verdict`` is ``ANSWER`` for all eighteen; ``disputes``
#: names the premises the reading must contest (empty: none).
META_QUESTIONS: Tuple[Tuple[int, str, str, str, Tuple[str, ...],
                            Tuple[str, ...], Tuple[str, ...]], ...] = (
    (91, "orifice_threshold", "ANSWER", "v_crit^2 < 2*g*h",
     (QSB,), (M + "torricelli_crossing",), ()),
    (92, "weight_four_sextet", "ANSWER", "6 nearest codewords",
     (PAPER,), ("GLM.Golay.snap_ambiguous_at_four",), ()),
    (93, "omega_elimination", "ANSWER", "dark shadow",
     (OMEGA,), ("GLM.IntegerDecision.exact_shadow",
                "GLM.IntegerDecision.dark_shadow_gap",
                "GLM.IntegerDecision.splinter_count"),
     ("shadow graphs",)),
    (94, "leech_holes", "ANSWER", "A1^24",
     (FORK, PAPER), ("GLM.Golay.snap_ambiguous_at_four",),
     ("close holes",)),
    (97, "lean_exact_inverse", "ANSWER", "A * B = 1",
     (PAPER,), (M + "inverse_of_certificate", M + "certificate_example"),
     ("Lean per payload",)),
    (98, "rational_automorphism", "ANSWER", "B * M * B^-1",
     (PAPER,), (M + "lattice_map_rational",),
     ("runtime exception scores -1",)),
    (99, "beyond_radius", "ANSWER", "distance 3",
     (PAPER, QSB), ("GLM.Golay24.unique_octad",),
     ("covering radius of the Steiner system", "silent repair")),
    (100, "squared_distance", "ANSWER", "squared distance",
     (ADDR,), (M + "euclid_le_iff", M + "euclid_le_euclid_iff"), ()),
    (101, "exact_growth", "ANSWER", "Bareiss",
     (SYMB,), (), ()),
    (102, "rational_rotation", "ANSWER", "Cayley",
     (SYMB,), (M + "cayley_orthogonal", M + "cayley_det"), ()),
    (104, "steiner_triage", "ANSWER", "exactly one octad",
     (PAPER,), ("GLM.Golay24.unique_octad", "GLM.Golay24.card_octads"), ()),
    (105, "decoding_radius", "ANSWER", "weight <= 3",
     (PAPER,), ("GLM.Golay.snap_boundary_at_three",
                "GLM.Golay.snap_unique_of_le_three"), ()),
    (106, "routing_surfaces", "ANSWER", "reading surfaces",
     (PAPER,), ("GLM.ConnectedMachine.route_prefix_none",
                "GLM.ConnectedMachine.route_append_of_some"),
     ("geometric boundary surfaces",)),
    (107, "transcendental_delay", "ANSWER", "exact process",
     (QSB, SYMB), (), ()),
    (108, "splinter_limit", "ANSWER", "NODE_LIMIT = 5000",
     (OMEGA,), ("GLM.IntegerDecision.splinter_count",
                "GLM.IntegerDecision.pugh_no_integer_point"),
     ("infinite search tree",)),
    (109, "sandbox_gate", "ANSWER", "once per reading",
     (QSB, PAPER), (), ("per token",)),
    (110, "lean_template", "ANSWER", "inverse_of_certificate",
     (PAPER,), (M + "inverse_of_certificate", M + "certificate_example"),
     ("column 2 is Lean",)),
    (111, "scoring_verdicts", "ANSWER", "structured verdict",
     (PAPER,), (), ("parsing messy text",)),
)

#: ``(id, text, topic)`` -- two rewordings per question.
PARAPHRASES: Tuple[Tuple[str, str, str], ...] = (
    ("p91a", "How can the GLM test whether Torricelli's orifice velocity "
     "sqrt(2gh) exceeds a critical velocity without taking a square root?",
     "orifice_threshold"),
    ("p91b", "Your system cannot use square roots: how does it decide v > "
     "v_crit for an orifice flow v = sqrt(2*g*h) using rational inequalities?",
     "orifice_threshold"),
    ("p92a", "In the GLM, why is a received word with coset weight 4 an "
     "AMBIGUOUS refusal, and how many nearest Golay codewords are tied?",
     "weight_four_sextet"),
    ("p92b", "How many equidistant nearest codewords does your machine find "
     "for a coset weight of exactly 4 in the MOG sextet?",
     "weight_four_sextet"),
    ("p93a", "How does the Omega test used by your benchmark differ from "
     "Fourier-Motzkin elimination over the rationals?", "omega_elimination"),
    ("p93b", "In the GLM's integer procedure, what does the Omega test do "
     "differently from Fourier-Motzkin elimination, and where do splinters "
     "come from?", "omega_elimination"),
    ("p94a", "For the GLM, what separates a deep hole of the Leech lattice "
     "from a close hole, and why does only one give the AMBIGUOUS weight-4 "
     "profile?", "leech_holes"),
    ("p94b", "Does an input landing on a close hole of the Leech lattice "
     "trigger your system's AMBIGUOUS weight-4 refusal the way a deep hole "
     "does?", "leech_holes"),
    ("p97a", "How does Lean 4 guarantee that your architecture's proof of a "
     "rational matrix inversion contains no floating-point roundoff?",
     "lean_exact_inverse"),
    ("p97b", "When the GLM checks a matrix inverse over Q^24 in Lean 4, why "
     "can no hidden floating-point roundoff enter the proof?",
     "lean_exact_inverse"),
    ("p98a", "Prove that the automorphisms of the Leech lattice in Conway's "
     "group Co0 have rational matrices, so that the GLM's Q^24 substrate "
     "can apply them exactly.", "rational_automorphism"),
    ("p98b", "Can your machine rotate a carrier by an element of Co0 without "
     "leaving Q^24, and why are the generators of Co0 rational?",
     "rational_automorphism"),
    ("p99a", "Why does your UNCORRECTABLE refusal apply when 5 or more "
     "coordinates of a 24-bit word are flipped?", "beyond_radius"),
    ("p99b", "In the GLM, what happens to a Golay word with an error of "
     "weight 5: why can it not be repaired, and which codeword is nearer?",
     "beyond_radius"),
    ("p100a", "How does the GLM compare Euclidean distances in Q^24 against "
     "a bound without computing square roots?", "squared_distance"),
    ("p100b", "Your system must check that the norm of x - y is at most r "
     "without leaving the rationals: how?", "squared_distance"),
    ("p101a", "In the GLM, how is the growth of numerators and denominators "
     "in exact rational matrix computations kept under control?",
     "exact_growth"),
    ("p101b", "Your exact arithmetic suffers from bit-explosion in rational "
     "linear algebra: what reduction keeps it exact and fast?",
     "exact_growth"),
    ("p102a", "How can the GLM rotate a state vector exactly with a rational "
     "matrix instead of sines and cosines?", "rational_rotation"),
    ("p102b", "Your system needs rotations in SO(24) that stay inside "
     "Q^(24x24): how are such rotation matrices built?", "rational_rotation"),
    ("p104a", "How does the GLM use the Steiner system S(5,8,24) to triage "
     "the weight of an error quickly?", "steiner_triage"),
    ("p104b", "Can your machine use the properties of the S(5,8,24) Steiner "
     "system to localise errors without scanning the whole space?",
     "steiner_triage"),
    ("p105a", "What is the exact condition under which the GLM can still "
     "repair a perturbed 24-bit word, rather than refusing it as "
     "UNCORRECTABLE?", "decoding_radius"),
    ("p105b", "State the proof condition for your system's unique decoding "
     "radius: when does a perturbation stop being repairable?",
     "decoding_radius"),
    ("p106a", "How does the GLM's multi-surface router avoid floating-point "
     "surface skipping and guarantee that a state lands exactly on a "
     "surface?", "routing_surfaces"),
    ("p106b", "When your system routes a variable across intersecting "
     "boundary surfaces, how does it avoid the rounding errors that make "
     "floating-point systems skip a surface?", "routing_surfaces"),
    ("p107a", "How does the GLM emulate a dead-time term e^(-Ls) of a PID "
     "transfer function exactly?", "transcendental_delay"),
    ("p107b", "Your framework is strictly rational: how can it handle "
     "exponential tuning parameters such as e^{-Ls} in a controller?",
     "transcendental_delay"),
    ("p108a", "How does the GLM handle the INTEGER_UNDECIDED refusal when "
     "the Omega test splinters too far?", "splinter_limit"),
    ("p108b", "What does your system do safely when its integer procedure's "
     "splinter search grows without bound, and when is INTEGER_UNDECIDED "
     "returned?", "splinter_limit"),
    ("p109a", "How does the GLM keep the python3 -I subprocess that verifies "
     "column 3 isolated without paying the fork cost on every token?",
     "sandbox_gate"),
    ("p109b", "Your TCT frame runs an isolated python3 -I script within 5 "
     "seconds: how often is it run, and how is the overhead kept low?",
     "sandbox_gate"),
    ("p110a", "How should the GLM's column 2 present a 24 x 24 rational "
     "matrix inverse so that a Lean 4 kernel can check it at once?",
     "lean_template"),
    ("p110b", "What Lean 4 template lets your system verify a rational "
     "matrix inversion in 24 dimensions instantly?", "lean_template"),
    ("p111a", "How does the GLM's scoring tell an unparsed answer, scored 0, "
     "from a confidently wrong answer, scored -1?", "scoring_verdicts"),
    ("p111b", "Your scoring protocol gives -1 for a confidently wrong "
     "answer and +1 for a certified refusal: how does the pipeline tell a "
     "wrong answer from an unparsed one?", "scoring_verdicts"),
)

#: ``(id, text, topic)`` -- one more rewording per question, written after
#: the first run of the meta frames had missed 5 of the 36 PARAPHRASES and
#: *before* any cue was changed in response, so that the sharpened cues are
#: measured on text they were not tuned to.  Reported beside T5; not a
#: mark of its own.
HELD_OUT: Tuple[Tuple[str, str, str], ...] = (
    ("h91", "With no square roots allowed in your substrate, how is the "
     "Torricelli outflow speed compared against a critical speed?",
     "orifice_threshold"),
    ("h92", "In the MOG, how many codewords tie for nearest when the GLM "
     "reads a word whose coset weight is 4?", "weight_four_sextet"),
    ("h93", "Why can the GLM's Omega test not simply reuse Fourier-Motzkin "
     "elimination over Z?", "omega_elimination"),
    ("h94", "Is a close hole of the Leech lattice something your decoder "
     "treats like a deep hole?", "leech_holes"),
    ("h97", "Could a floating-point roundoff hide inside a Lean 4 proof that "
     "the GLM uses for a matrix inverse?", "lean_exact_inverse"),
    ("h98", "Do the generators of Co0 act on your Q^24 carriers with "
     "rational entries?", "rational_automorphism"),
    ("h99", "Why does the GLM refuse UNCORRECTABLE rather than repair a word "
     "with five flipped bits?", "beyond_radius"),
    ("h100", "How does the GLM decide whether two rational points are "
     "within distance r of each other, given that a norm needs a square "
     "root?", "squared_distance"),
    ("h101", "What stops the numerators and denominators in your exact "
     "matrix arithmetic from blowing up?", "exact_growth"),
    ("h102", "Which construction gives the GLM rotation matrices with "
     "rational entries rather than sines and cosines?", "rational_rotation"),
    ("h104", "How does your decoder use S(5,8,24) to triage how many bits "
     "are wrong?", "steiner_triage"),
    ("h105", "Up to what error weight can the GLM repair a word, and when "
     "does it switch to UNCORRECTABLE?", "decoding_radius"),
    ("h106", "Can rounding make your router skip a surface when it routes a "
     "question?", "routing_surfaces"),
    ("h107", "How does the GLM represent a controller's dead time e^{-Ls} "
     "without floats?", "transcendental_delay"),
    ("h108", "When does your integer procedure give up with "
     "INTEGER_UNDECIDED, and is there a limit on the splinters?",
     "splinter_limit"),
    ("h109", "How often does the GLM start a python3 -I subprocess, and what "
     "does that overhead cost?", "sandbox_gate"),
    ("h110", "What format should column 2 use so that Lean 4 can check a "
     "rational matrix inverse quickly?", "lean_template"),
    ("h111", "How does your pipeline separate a confidently wrong answer "
     "(-1) from an answer it could not parse?", "scoring_verdicts"),
)

#: Texts the meta frame must not read: the same mathematics without the
#: machine named, and the machine named with no declared topic.
NOT_READ: Tuple[str, ...] = (
    "What is the Cayley transform of a skew-symmetric matrix?",
    "Prove that the extended Golay code is quasi-perfect.",
    "Explain the Omega test of Pugh.",
    "Compute the distance between (1, 2) and (4, 6).",
    "How does Torricelli's law relate the outflow speed to the height?",
    "How does the GLM handle quantum entanglement?",
    "What is your favourite colour?",
    "Does the GLM dream of electric sheep?",
    "What is the capital of France?",
    "Describe the history of the Leech lattice.",
)

#: The controls on the evidence: each kind is applied to every answered
#: question and must turn the reading into a refusal or a failed script.
MUTATIONS: Tuple[Tuple[str, str], ...] = (
    ("quote-moved", "one declared fragment altered: the reading must be "
                    "refused CITATION_MOVED"),
    ("lean-moved", "one cited declaration renamed: the reading must be "
                   "refused CITATION_MOVED"),
    ("script-quote", "the column-3 script given a quote that is not in the "
                     "document: it must fail"),
    ("script-claim", "the column-3 script given a false value for its "
                     "mathematical check: it must fail"),
)

#: Questions whose every quoted document and cited declaration existed
#: before this round.
PRE_EXISTING: Tuple[int, ...] = (92, 93, 94, 99, 101, 104, 105, 106, 107,
                                 108, 109, 111)
#: Questions that also cite this round's Lean file
#: (``RequestProject/GLM/MetaAnswers.lean``).
THIS_ROUND: Tuple[int, ...] = (91, 97, 98, 100, 102, 110)

#: The theorems mark T7 names, in ``RequestProject/GLM/MetaAnswers.lean``.
LEAN_THEOREMS: Tuple[str, ...] = (
    "euclid_le_iff", "euclid_lt_iff", "euclid_le_euclid_iff",
    "torricelli_crossing", "isUnit_det_one_sub_of_skew", "cayley_orthogonal",
    "cayley_det", "lattice_map_rational", "inverse_of_certificate",
    "certificate_example",
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("T1", "every META_QUESTIONS question is read through the router by the "
           "declared topic, with the declared verdict, and its value holds "
           "the declared fragment"),
    ("T2", "every answer quotes each declared document, every quote is in "
           "its document at read time, and every declared Lean declaration "
           "is cited and found in the development"),
    ("T3", "every declared disputed premise is reported, and no reading "
           "disputes a premise that was not declared"),
    ("T4", "every column-3 script prints VERIFIED True in a fresh python3 "
           "-I, and every MUTATIONS kind is caught on every answered "
           "question"),
    ("T5", "every PARAPHRASES text is read by its declared topic and "
           "answered with the same fragment"),
    ("T6", "non-interference: the meta frame reads none of NOT_READ, none "
           "of the other 94 outside questions, none of the 14 Set B items "
           "and none of the evaluation cases; with the meta frames switched "
           "off and on, no other text changes frame"),
    ("T7", "a Lean file proves what the new answers rest on (LEAN_THEOREMS) "
           "with no sorry"),
)
