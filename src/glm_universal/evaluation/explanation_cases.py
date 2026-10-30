"""``glm_universal.evaluation.explanation_cases`` -- the declared cases of
Phase 120: track E of ``studies/QUESTION_SET_B_STUDY.md`` §8, the outside
questions that ask *why* (class E of the Capability Failure Matrix), and the
three class-P questions Phase 107 left refused as accounts (29, 39 and 96).

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.explanation_report`.  Every expectation below was
worked out by reading the questions, the element register
(``data_objects/_data/elements_118.json``) and the two outside tables the
round reads in (AME2020 and NUBASE2020, below), not from the machine's
output.

The count
---------
``STATUS.md`` §2.1 named the line "32 outside questions, including outside
questions 29, 39 and 96".  Read against ``question_set_b_cases.BOUNDARY``,
class E holds 32 questions (0, 4, 23, 32, 43, 60-80 without 81, 82, 83, 84,
87, 88, 89) and 29, 39 and 96 are class P, so the line covers **35**
questions: the 32 and the three.  All 35 are declared here.

The operation
-------------
An **explanation frame** reads one declared question (or a rewording of it)
and answers the part of it that a register or an exact derivation decides:

* **register anchors** -- values read from the element register or the
  nuclide register when the question is read, each with the row it came
  from, and any quantity computed from them exactly (a Q-value from two mass
  excesses, a molar volume from a weight and a density, a Slater effective
  charge from a configuration);
* **derivations** -- a closed statement the machine computes and gates (the
  reactance above resonance, the gain of a filtered derivative, a Kripke
  countermodel, an exact optimum of a small constrained problem);
* **the account refused** -- whatever the question asks that is a causal or
  philosophical account rather than a value is stated, in the answer, as
  ``refused EXPLANATION`` with what it would need.  A question whose every
  part is decided is declared ``FULL`` and carries no such line;
* **disputed premises** -- where a register contradicts the question's
  premise, the answer says so, with the register's figures;
* a **column-3 script** that re-derives every anchor from the register rows
  it embeds and every derivation by an independent computation.

The nuclide register
--------------------
The round reads in the Atomic Mass Evaluation 2020 (``mass_1.mas20.txt``,
Wang, Huang, Kondev, Audi and Naimi, Chinese Physics C45, 030003, 2021) and
NUBASE2020 (``nubase_4.mas20.txt``, Kondev et al., Chinese Physics C45,
030001, 2021), as published by the IAEA Nuclear Data Section, frozen with
the SHA-256 of each raw file.  Ground states only.  A mass excess marked
``#`` in the table (from systematics, not measured) is kept with the mark.

Declarations
------------
* :data:`EXPLANATION_QUESTIONS` -- the 35 questions: index, topic, scope
  (``FULL`` or ``ANCHORED``), a fragment the answer must contain, the
  registers it must read, the premises it must dispute.
* :data:`PARAPHRASES` -- one rewording per question, written now.
* :data:`HELD_OUT` -- one more rewording per question, written after the
  first run and before any cue change (added to this file then; reported,
  not a mark).
* :data:`NOT_READ` -- near misses the explanation frames must not read.
* :data:`REGISTER_CHECKS` -- read-back checks of the nuclide register.
* :data:`MUTATIONS` -- the controls.
* :data:`LEAN_THEOREMS` -- what ``RequestProject/GLM/ExplanationAnchors.lean``
  must prove.
* :data:`MARKS` -- the ladder.

Hand-worked values the fragments rest on
----------------------------------------
* 4He 2424.91587 keV, 8Be 4941.67 keV (AME2020 mass excesses):
  Q(8Be -> 2 alpha) = 4941.672 - 2 x 2424.916 = 91.84 keV.
* 3 x 2424.91587 - 0 (12C) = 7274.75 keV, the triple-alpha threshold.
* 7Be 15769.0 and 7Li 14907.1 keV: Q_EC(7Be) = 861.89 keV.
* n 8071.318, 1H 7288.971, 2H 13135.723 keV: B(d) = 2224.566 keV.
* 11B 8667.708 and 11C 10649.397 keV: B(11B) - B(11C) =
  (ME(11C) - ME(11B)) + (ME(n) - ME(1H)) = 1981.689 + 782.347 = 2764.04 keV.
* 208Pb: B/A = 7867.45 keV, below 206Pb (7875.36) and 207Pb (7869.87);
  S_n(208Pb) = 7367.87 keV, S_n(209Pb) = 3937.37 keV.
* 76Ge -> 76Se: Q_bb = 2039.06 keV.
* every Tc isotope in AME2020 is heavier than its Mo or its Ru isobar; the
  smallest such margin is 99Tc -> 99Ru, 297.5 keV.
* element register: He's first ionisation energy 24.587 eV is the largest of
  the 102 measured; F's Pauling electronegativity 3.98 is the largest of the
  95; Os has the largest density (22.57) and, in period 6, the smallest
  molar volume (190.2 / 22.57 = 8.43 cm^3/mol against Ir's 8.57).
* Slater: Z_eff of the outer electron is 3.15 for both Zr (5s) and Hf (6s);
  3.5 for Al (3p) and 5.0 for Ga (4p).
* the register's configurations differ from the Madelung filling for 6 of
  the 15 actinides (Ac, Th, Pa, U, Np, Cm) and 3 of the 15 lanthanides
  (La, Ce, Gd).
* sqrt(1 - (79 alpha)^2) = 0.8171 (gold, 1s); sqrt(1 - (118 alpha)^2) =
  0.5084 (oganesson, s1/2 and p1/2).
* Gibbs: Si(pi)/pi - 1/2 = 0.08949 of the jump, whatever the length.
* WF6: 183.84 + 6 x 18.998 = 297.83 g/mol; TaF5: 275.94 g/mol.
* Stork sequence: C6H10O + C4H9N - H2O + C3H5Br + H2O -> C9H14O + C4H10NBr.
* fuzzy against probability with both marginals 7/10: min gives 7/10, a
  probability of the conjunction can be anything in [2/5, 7/10].
* NUBASE2020: the most neutron-rich Z = 114 nuclide with a measured
  half-life is 290Fl, N = 176.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["EXPLANATION_QUESTIONS", "PARAPHRASES", "HELD_OUT", "NOT_READ",
           "REGISTER_CHECKS", "MUTATIONS", "PREVIOUSLY_REFUSED",
           "LEAN_THEOREMS", "MARKS", "SCOPES", "REGISTERS"]

#: The registers an answer may read.
REGISTERS: Tuple[str, ...] = ("elements", "nuclides", "proof_search",
                              "integer_decision", "none")

#: ``FULL``: every part of the question is decided; ``ANCHORED``: the
#: decided part is answered and the account is refused EXPLANATION.
SCOPES: Tuple[str, ...] = ("FULL", "ANCHORED")

#: ``(index, topic, scope, fragment, registers, disputes)``.  ``disputes``
#: holds a fragment of each premise the answer must contest.
EXPLANATION_QUESTIONS: Tuple[Tuple[int, str, str, str, Tuple[str, ...],
                                   Tuple[str, ...]], ...] = (
    (0, "rlc_resonance", "FULL", "inductive", ("none",), ()),
    (4, "quasi_fermi", "ANCHORED", "E_Fn - E_Fp = qV", ("none",), ()),
    (23, "stork_enamine", "ANCHORED", "C9H14O", ("elements",), ()),
    (32, "derivative_kick", "FULL", "Kd/tau_f", ("none",), ()),
    (43, "window_tradeoff", "ANCHORED", "0.0894", ("none",), ()),
    (60, "helium_beryllium", "ANCHORED", "24.587 eV", ("elements",), ()),
    (61, "osmium_density", "ANCHORED", "smallest molar volume",
     ("elements",), ()),
    (62, "fluorine_oxidation", "ANCHORED", "3.98", ("elements",), ()),
    (63, "group14_conductivity", "ANCHORED", "4 valence electrons",
     ("elements",), ()),
    (64, "gold_mercury", "ANCHORED", "0.817", ("elements",), ()),
    (65, "technetium", "ANCHORED", "297.5", ("nuclides",), ()),
    (66, "fluoride_volatility", "ANCHORED", "297.8", ("elements",), ()),
    (67, "lanthanide_contraction", "ANCHORED", "3.15", ("elements",), ()),
    (68, "actinide_counting", "ANCHORED", "6 of the 15 actinides",
     ("elements",), ()),
    (69, "oganesson", "ANCHORED", "0.508", ("elements",),
     ("Expected to be a Gas",)),
    (70, "deuteron", "ANCHORED", "2224.566", ("nuclides",), ()),
    (71, "mirror_nuclei", "ANCHORED", "2764.0", ("nuclides",), ()),
    (72, "lead208", "ANCHORED", "3937.4", ("nuclides",),
     ("binding energy per nucleon",)),
    (73, "beryllium8", "ANCHORED", "91.84", ("nuclides",), ()),
    (74, "double_beta", "FULL", "2039.06", ("nuclides",), ()),
    (75, "giant_dipole", "ANCHORED", "A^(-1/3)", ("none",), ()),
    (76, "island_stability", "ANCHORED", "N = 176", ("nuclides",), ()),
    (77, "s_r_process", "ANCHORED", "r-only", ("nuclides",), ()),
    (78, "lithium_problem", "ANCHORED", "861.89", ("nuclides",), ()),
    (79, "hoyle_state", "ANCHORED", "7274.75", ("nuclides",), ()),
    (80, "material_implication", "ANCHORED", "strict implication fails",
     ("proof_search",), ()),
    (82, "soundness_completeness", "ANCHORED", "sound but not complete",
     ("proof_search",), ()),
    (83, "intuitionistic_lem", "ANCHORED", "~~(p | ~p)",
     ("proof_search",), ()),
    (84, "skolem_paradox", "ANCHORED", "countable elementary substructure",
     ("none",), ()),
    (87, "fuzzy_probability", "ANCHORED", "[2/5, 7/10]", ("none",), ()),
    (88, "godel_second", "ANCHORED", "proves every sentence",
     ("proof_search",), ()),
    (89, "lindstrom", "ANCHORED", "compactness", ("none",), ()),
    (29, "cstr_multiplicity", "ANCHORED", "three steady states",
     ("none",), ()),
    (39, "mpc_constraints", "ANCHORED", "u1 = 1", ("none",), ()),
    (96, "tarski_diophantine", "ANCHORED", "x^2 = 2",
     ("integer_decision",), ("node budget",)),
)

#: The three questions Phase 107 declared to stay refused.
PREVIOUSLY_REFUSED: Tuple[int, ...] = (29, 39, 96)

#: ``(id, text, topic)`` -- one rewording per question.
PARAPHRASES: Tuple[Tuple[str, str, str], ...] = (
    ("p0", "Above resonance, what happens to the impedance of a series RLC "
     "circuit, and is it inductive or capacitive?", "rlc_resonance"),
    ("p4", "Under forward bias, how far apart are the electron and hole "
     "quasi-Fermi levels in the depletion region of a p-n junction, as a "
     "function of the applied voltage?", "quasi_fermi"),
    ("p23", "What product forms when cyclohexanone is treated with "
     "pyrrolidine and acid, then allyl bromide, then aqueous hydrolysis?",
     "stork_enamine"),
    ("p32", "Why is pure derivative action impractical in a PID controller, "
     "what does a derivative filter do, and what is derivative kick?",
     "derivative_kick"),
    ("p43", "Compare the rectangular window and the Kaiser window for FIR "
     "low-pass design by the window method: ripple and transition width.",
     "window_tradeoff"),
    ("p60", "Why does beryllium form compounds such as BeCl2 while helium "
     "is inert, although both have filled s shells?", "helium_beryllium"),
    ("p61", "Why does density peak at osmium in the transition metal row and "
     "fall after it, even though atomic mass keeps rising?",
     "osmium_density"),
    ("p62", "Why is fluorine always in oxidation state -1 in its compounds, "
     "unlike oxygen, chlorine and nitrogen?", "fluorine_oxidation"),
    ("p63", "Down group 14, why do carbon, silicon, germanium, tin and lead "
     "go from insulator to semiconductor to metal with the same valence "
     "electrons?", "group14_conductivity"),
    ("p64", "How do relativistic effects on the 6s shell make gold yellow "
     "and mercury liquid?", "gold_mercury"),
    ("p65", "Why has technetium no stable isotope although its neighbours "
     "molybdenum and ruthenium are stable?", "technetium"),
    ("p66", "Why is WF6 a gas at room temperature while TaF5 is a solid, "
     "although tungsten hexafluoride is heavier?", "fluoride_volatility"),
    ("p67", "Why do hafnium and zirconium have nearly the same radius "
     "(the lanthanide contraction), and what does the 3d block do to "
     "gallium against aluminium?", "lanthanide_contraction"),
    ("p68", "Why do electron-counting rules fail for the actinides, given "
     "the 5f, 6d and 7s orbital energies?", "actinide_counting"),
    ("p69", "How do relativity and spin-orbit coupling stop oganesson "
     "behaving like a noble gas?", "oganesson"),
    ("p70", "Why is the deuteron bound when the diproton and the dineutron "
     "are not?", "deuteron"),
    ("p71", "Why do the mirror nuclei boron-11 and carbon-11 differ in "
     "binding energy by about 2.76 MeV?", "mirror_nuclei"),
    ("p72", "How does the shell model explain the stability of lead-208, "
     "and what is its neutron skin?", "lead208"),
    ("p73", "Why is beryllium-8 unbound and decays into two alpha "
     "particles?", "beryllium8"),
    ("p74", "How does the electron energy spectrum tell neutrinoless double "
     "beta decay from two-neutrino double beta decay, and why does it "
     "violate lepton number?", "double_beta"),
    ("p75", "How does the giant dipole resonance frequency scale with mass "
     "number A in the liquid drop picture?", "giant_dipole"),
    ("p76", "How do shell corrections create the island of stability near "
     "Z = 114 and N = 184?", "island_stability"),
    ("p77", "Why can tin-124 be made only by the r-process, and why is "
     "tin-112 bypassed by neutron capture?", "s_r_process"),
    ("p78", "Explain the primordial lithium problem: how is lithium-7 made "
     "in Big Bang nucleosynthesis through beryllium-7 electron capture?",
     "lithium_problem"),
    ("p79", "Why does the Hoyle state of carbon-12 act as a resonance for "
     "the triple-alpha process?", "hoyle_state"),
    ("p80", "What are the paradoxes of material implication, and how does "
     "strict implication or relevant logic avoid them?",
     "material_implication"),
    ("p82", "What is the difference between soundness and completeness of a "
     "deductive system, and which logics lack completeness?",
     "soundness_completeness"),
    ("p83", "Why does intuitionistic logic reject the law of excluded middle "
     "and double negation elimination?", "intuitionistic_lem"),
    ("p84", "Resolve the Skolem paradox: how can ZFC prove an uncountable "
     "set exists yet have a countable model?", "skolem_paradox"),
    ("p87", "What is the difference between a fuzzy membership degree of "
     "0.7 and a probability of 0.7, for conjunction and disjunction?",
     "fuzzy_probability"),
    ("p88", "Why is a formal system that proves its own consistency, "
     "Con(PA), a red flag, given Goedel's second incompleteness theorem?",
     "godel_second"),
    ("p89", "What does Lindstrom's theorem say we lose if we extend "
     "first-order logic beyond compactness and Loewenheim-Skolem?",
     "lindstrom"),
    ("p29", "For an exothermic second-order reaction 2A -> B in a "
     "non-isothermal CSTR, write the steady-state material and energy "
     "balances and show how multiple steady states arise.",
     "cstr_multiplicity"),
    ("p39", "How does model predictive control treat input constraints "
     "differently from PID, and what is the MPC cost function over the "
     "prediction and control horizons?", "mpc_constraints"),
    ("p96", "Why can't Tarski-Seidenberg quantifier elimination decide a "
     "Diophantine verification query over Q and Z, and what does "
     "Matiyasevich's theorem imply?", "tarski_diophantine"),
)

#: ``(id, text, topic)`` -- one more rewording per question, written after
#: the first run of the explanation frames (which read all 35 PARAPHRASES)
#: and before any cue was changed, by a deliberate change of vocabulary, so
#: that the cues are measured on text they were not written beside.
#: Reported beside E6; not a mark of its own.
HELD_OUT: Tuple[Tuple[str, str, str], ...] = (
    ("h0", "Drive a series resistor-inductor-capacitor loop a little faster "
     "than its natural frequency: does the impedance grow, and does it look "
     "inductive?", "rlc_resonance"),
    ("h4", "Explain the splitting of the electron and hole imrefs in a "
     "forward-biased pn diode.", "quasi_fermi"),
    ("h23", "Outline the Stork enamine alkylation of cyclohexanone using "
     "pyrrolidine and allyl bromide.", "stork_enamine"),
    ("h32", "What goes wrong with an unfiltered D term in a three-term "
     "controller, and what is the kick on a setpoint step?",
     "derivative_kick"),
    ("h43", "Kaiser versus rectangular windows for an FIR lowpass: what "
     "happens to the ripple and the transition band?", "window_tradeoff"),
    ("h60", "If He and Be both have closed s subshells, why is Be reactive "
     "and He a noble gas?", "helium_beryllium"),
    ("h61", "Why is Os denser than Ir and Pt even though they are heavier "
     "atoms?", "osmium_density"),
    ("h62", "Why can F never take a positive oxidation number?",
     "fluorine_oxidation"),
    ("h63", "Diamond insulates, silicon is a semiconductor and lead "
     "conducts: what changes down the carbon group?",
     "group14_conductivity"),
    ("h64", "Why is Au yellow and Hg a liquid at room temperature, in terms "
     "of relativistic quantum chemistry?", "gold_mercury"),
    ("h65", "Element 43 has no stable isotopes: why?", "technetium"),
    ("h66", "Tungsten hexafluoride boils at 17 C while tantalum "
     "pentafluoride is a solid: why is the heavier fluoride more "
     "volatile?", "fluoride_volatility"),
    ("h67", "Explain why Zr and Hf are so hard to separate chemically.",
     "lanthanide_contraction"),
    ("h68", "Why is valence electron counting unreliable for uranium, "
     "neptunium and plutonium compounds?", "actinide_counting"),
    ("h69", "Is element 118 really a noble gas once relativistic effects "
     "are included?", "oganesson"),
    ("h70", "Why is there no bound state of two protons, while a proton and "
     "a neutron bind?", "deuteron"),
    ("h71", "What causes the binding energy difference between 11C and "
     "11B?", "mirror_nuclei"),
    ("h72", "Why is Pb-208 doubly magic and so stable?", "lead208"),
    ("h73", "Why does 8Be fall apart into two helium-4 nuclei almost "
     "instantly?", "beryllium8"),
    ("h74", "How would we know from the electron spectrum that a double "
     "beta decay emitted no neutrinos?", "double_beta"),
    ("h75", "How does the energy of the GDR in nuclei depend on the mass "
     "number?", "giant_dipole"),
    ("h76", "Why might superheavy nuclei near N = 184 live longer than "
     "their neighbours?", "island_stability"),
    ("h77", "Which tin isotopes are made by slow neutron capture and which "
     "only by rapid capture?", "s_r_process"),
    ("h78", "Why do Big Bang models predict about three times more 7Li "
     "than is observed?", "lithium_problem"),
    ("h79", "Why does carbon production in stars depend on a resonance in "
     "12C near 7.65 MeV?", "hoyle_state"),
    ("h80", "Why is 'if P then Q' read as 'not P or Q' in classical logic "
     "problematic for everyday conditionals?", "material_implication"),
    ("h82", "Can a proof system prove only true things yet fail to prove "
     "some truths?", "soundness_completeness"),
    ("h83", "Why don't constructivists accept P or not P?",
     "intuitionistic_lem"),
    ("h84", "How can a countable model of set theory contain the real "
     "numbers?", "skolem_paradox"),
    ("h87", "Is a membership degree of 0.7 the same thing as a probability "
     "of 0.7?", "fuzzy_probability"),
    ("h88", "If PA proved its own consistency, what would that tell us?",
     "godel_second"),
    ("h89", "What does Lindstrom's characterisation of first-order logic "
     "imply for stronger logics?", "lindstrom"),
    ("h29", "How can an exothermic continuous stirred tank reactor have "
     "several steady states?", "cstr_multiplicity"),
    ("h39", "How does a model predictive controller enforce valve limits, "
     "and what objective does it minimise?", "mpc_constraints"),
    ("h96", "Why does real quantifier elimination not settle integer "
     "polynomial equations?", "tarski_diophantine"),
)

#: Texts no explanation frame may read: the same subjects asked for a single
#: value or a definition, and questions with no declared topic.
NOT_READ: Tuple[str, ...] = (
    "What is the atomic number of osmium?",
    "address of golay",
    "What is the capital of France?",
    "Explain photosynthesis.",
    "Why is the sky blue?",
    "Explain the Omega test of Pugh.",
    "How does the GLM handle quantum entanglement?",
    "What is the half-life of carbon-14?",
    "Explain how a transistor amplifies a signal.",
    "Why do cats purr?",
)

#: Read-back checks of the nuclide register: ``(id, what)``.
REGISTER_CHECKS: Tuple[Tuple[str, str], ...] = (
    ("raw-digest", "the SHA-256 of both raw files is stored and the frozen "
                   "register names it"),
    ("round-trip", "every stored mass excess is an exact rational and reads "
                   "back to its table string"),
    ("deuteron", "B(2H) = 2224.566 keV to the table's precision"),
    ("peak", "the largest binding energy per nucleon among measured masses "
             "is 62Ni's"),
    ("stable-count", "NUBASE2020 marks between 250 and 260 ground states "
                     "'stbl'"),
)

#: The controls: each kind is applied to every answered question.
MUTATIONS: Tuple[Tuple[str, str], ...] = (
    ("script-claim", "the column-3 script given an altered value for its "
                     "headline anchor: it must fail"),
    ("register-row", "for an answer that reads a register, one register row "
                     "the script embeds is altered: the script must fail"),
)

#: The theorems mark E9 names, in
#: ``RequestProject/GLM/ExplanationAnchors.lean``.
LEAN_THEOREMS: Tuple[str, ...] = (
    "reactance_pos_above_resonance", "impedance_sq_strictMonoOn",
    "filtered_derivative_gain_lt", "nucleon_pair_channels",
    "chain_em_fails", "chain_dne_fails", "strict_implication_fails",
    "frechet_lower", "not_truth_functional", "inconsistent_proves_all",
    "countable_elementary_substructure", "real_root_no_rational_root",
    "mpc_instance_optimal", "be8_unbound", "technetium_unstable",
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("E1", "every EXPLANATION_QUESTIONS question is read through the router "
           "by the declared topic, answered, and its value holds the "
           "declared fragment"),
    ("E2", "every ANCHORED answer states its account part as refused "
           "EXPLANATION and no FULL answer does"),
    ("E3", "every answer that reads a register names the rows it read, and "
           "the values it quotes are the register's at read time"),
    ("E4", "every column-3 script prints VERIFIED True in a fresh python3 "
           "-I, and every MUTATIONS kind that applies is caught on every "
           "answered question"),
    ("E5", "every declared disputed premise is reported, and no answer "
           "disputes a premise that was not declared"),
    ("E6", "at least 32 of the 35 PARAPHRASES are read by their declared "
           "topic and answered with the same fragment"),
    ("E7", "non-interference: the explanation frames read none of NOT_READ, "
           "none of the other 77 outside questions, none of the 14 Set B "
           "items and none of the evaluation cases; with the frames off and "
           "on no other text changes frame"),
    ("E8", "the nuclide register passes every REGISTER_CHECKS check"),
    ("E9", "a Lean file proves LEAN_THEOREMS with no sorry"),
    ("E10", "questions 29, 39 and 96, refused since Phase 107, are "
            "answered, and every outside question answered before the "
            "round keeps its frame"),
)
