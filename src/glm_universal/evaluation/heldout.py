"""``glm_universal.evaluation.heldout`` -- the held-out language sets.

Why this exists
---------------
The 177-case contract set (:mod:`glm_universal.evaluation.cases`) is generated
from the runtime's own query kinds and report subjects, so it can detect a
regression and cannot measure whether a new *phrasing* reaches the machine.
The twenty-question probe (:data:`glm_universal.reasoning.blockers.PROBE`)
measures that, but it is twenty questions, each with one paraphrase, and any
instrument built to raise its score is built while looking at it.

These sets are the control for that.  They were written **before** the typed
planner (:mod:`glm_universal.runtime.semantic_plan`) existed, and committed on
their own so that the commit is the pre-registration: nothing below was edited
after the planner was first run against it.  The labels are written from world
knowledge -- a standard atomic weight, a definition of the international foot,
a gcd -- and not read off the registers, so a register error scores as an
error rather than as agreement with itself.

Three sets
----------
* :data:`PARAPHRASES` -- three new phrasings of each of the twenty probe
  questions, sixty in all.  None repeats the probe's own two phrasings.
* :data:`COMPOSITIONS` -- thirty questions that ask the *same operations* of
  rows the probe never names: another element's weight, another molecule's
  molar mass, another pair of integers.
* :data:`ADVERSARIAL` -- twenty questions whose right outcome is a refusal, or
  one narrow answer: absent facts, impossible conversions, category errors,
  division by zero, a declaration that does not exist.

The scoring rule
----------------
A question carries ``expect``, a tuple of lowercase fragments of which a right
answer must contain at least one, or ``None`` when the right outcome is a
refusal.  ``refusal_ok`` says whether declining is acceptable for a question
that has an answer (it is, for every answerable question: a refusal costs
coverage, never safety).

* answered, and a fragment is present -- **correct**;
* answered, and no fragment is present -- **wrong**;
* answered where ``expect`` is ``None`` -- **wrong** (a confident answer to a
  question that should have been declined);
* declined where ``expect`` is ``None`` -- **correct refusal**;
* declined where ``expect`` is not ``None`` -- **refused**.

*Safe coverage* is ``(correct + correct refusals) / total`` and the count that
matters most is ``wrong``, reported beside it and never folded into it.

Exact and float-free: the module holds strings and integers only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

__all__ = [
    "HeldOut", "PARAPHRASES", "COMPOSITIONS", "ADVERSARIAL", "STRESS",
    "ALL_SETS",
    "score_answer",
]


@dataclass(frozen=True)
class HeldOut:
    """One held-out question and what a right answer says."""

    key: str
    question: str
    expect: Optional[Tuple[str, ...]]
    probe_key: str = ""
    note: str = ""


def _q(key: str, question: str, *expect: str, probe: str = "",
       note: str = "") -> HeldOut:
    return HeldOut(key, question, tuple(e.lower() for e in expect) or None,
                   probe, note)


def _refuse(key: str, question: str, note: str, probe: str = "") -> HeldOut:
    return HeldOut(key, question, None, probe, note)


#: Three new phrasings of each probe question.  ``probe_key`` names the probe
#: row; the fragments are the probe's own where they are specific enough, and
#: narrowed where the probe's fragment would match by accident.
PARAPHRASES: Tuple[HeldOut, ...] = (
    # nl-meaning
    _q("p-nl-meaning-1", "what is the meaning of velocity?", "velocity",
       probe="nl-meaning"),
    _q("p-nl-meaning-2", "define velocity", "velocity", probe="nl-meaning"),
    _q("p-nl-meaning-3", "what does the word velocity mean?", "velocity",
       probe="nl-meaning"),
    # nl-relation
    _q("p-nl-relation-1", "velocity is the derivative of which quantity?",
       "position", probe="nl-relation"),
    _q("p-nl-relation-2", "of what is velocity the derivative?", "position",
       probe="nl-relation"),
    _q("p-nl-relation-3", "which quantity has velocity as its derivative?",
       "position", probe="nl-relation"),
    # nl-compare
    _q("p-nl-compare-1", "is water more concrete than energy?", "water",
       probe="nl-compare",
       note="the same coordinate asked from the other pole"),
    _q("p-nl-compare-2", "which of energy and water is more abstract?",
       "energy", probe="nl-compare"),
    _q("p-nl-compare-3", "between water and energy, which is the more "
                         "abstract?", "energy", probe="nl-compare"),
    # nl-unknown -- the right outcome is a refusal
    _refuse("p-nl-unknown-1", "what causes the blue colour of the sky?",
            "nothing held explains it", probe="nl-unknown"),
    _refuse("p-nl-unknown-2", "explain why the sky is blue",
            "nothing held explains it", probe="nl-unknown"),
    _refuse("p-nl-unknown-3", "why does the sky appear blue during the day?",
            "nothing held explains it", probe="nl-unknown"),
    # math-add
    _q("p-math-add-1", "what is two plus two?", "4", probe="math-add"),
    _q("p-math-add-2", "what do you get if you add 2 and 2?", "4",
       probe="math-add"),
    _q("p-math-add-3", "compute 2 + 2", "4", probe="math-add"),
    # math-prime
    _q("p-math-prime-1", "is 91 a prime number?", "not prime",
       probe="math-prime"),
    _q("p-math-prime-2", "is the number 91 prime?", "not prime",
       probe="math-prime"),
    _q("p-math-prime-3", "tell me whether 91 is prime", "not prime",
       probe="math-prime"),
    # math-gcd
    _q("p-math-gcd-1", "what is the gcd of 12 and 18?", "6",
       probe="math-gcd"),
    _q("p-math-gcd-2", "find the highest common factor of 12 and 18", "6",
       probe="math-gcd"),
    _q("p-math-gcd-3", "greatest common divisor of 18 and 12", "6",
       probe="math-gcd"),
    # math-ratio
    _q("p-math-ratio-1", "what is the prime limit of 3/2?", "3",
       probe="math-ratio"),
    _q("p-math-ratio-2", "what prime limit does the ratio 3/2 have?", "3",
       probe="math-ratio"),
    _q("p-math-ratio-3", "give the prime limit of the perfect fifth", "3",
       probe="math-ratio"),
    # phys-constant
    _q("p-phys-constant-1", "what is speed_of_light?", "speed_of_light",
       probe="phys-constant"),
    _q("p-phys-constant-2", "describe the speed_of_light", "speed_of_light",
       probe="phys-constant"),
    _q("p-phys-constant-3", "tell me about the speed of light",
       "speed_of_light", "speed of light", probe="phys-constant"),
    # phys-dimension
    _q("p-phys-dimension-1", "what is the dimension of force?", "l m t^-2",
       probe="phys-dimension"),
    _q("p-phys-dimension-2", "what dimensions does force have?", "l m t^-2",
       probe="phys-dimension"),
    _q("p-phys-dimension-3", "give me the dimensions of force", "l m t^-2",
       probe="phys-dimension"),
    # phys-derive
    _q("p-phys-derive-1", "does force have the same dimensions as mass "
                          "times acceleration?", "true", "holds",
       probe="phys-derive"),
    _q("p-phys-derive-2", "is force dimensionally equal to mass times "
                          "acceleration?", "true", "holds",
       probe="phys-derive"),
    _q("p-phys-derive-3", "check whether force equals mass times "
                          "acceleration dimensionally", "true", "holds",
       probe="phys-derive"),
    # phys-convert
    _q("p-phys-convert-1", "how many feet are in 3 metres?", "9.84",
       probe="phys-convert"),
    _q("p-phys-convert-2", "convert 3 meters into feet", "9.84",
       probe="phys-convert"),
    _q("p-phys-convert-3", "what is 3 metres in feet?", "9.84",
       probe="phys-convert"),
    # chem-lookup
    _q("p-chem-lookup-1", "which element has the symbol C?", "carbon",
       probe="chem-lookup"),
    _q("p-chem-lookup-2", "what element is C?", "carbon",
       probe="chem-lookup"),
    _q("p-chem-lookup-3", "what is the name of the element C?", "carbon",
       probe="chem-lookup"),
    # chem-weight
    _q("p-chem-weight-1", "what is the atomic mass of carbon?", "12.011",
       probe="chem-weight"),
    _q("p-chem-weight-2", "give the atomic weight of carbon", "12.011",
       probe="chem-weight"),
    _q("p-chem-weight-3", "carbon's atomic weight?", "12.011",
       probe="chem-weight"),
    # chem-group
    _q("p-chem-group-1", "what block is chlorine in?", "halogen",
       probe="chem-group"),
    _q("p-chem-group-2", "which group does chlorine belong to?", "halogen",
       probe="chem-group"),
    _q("p-chem-group-3", "what kind of element is chlorine?", "halogen",
       probe="chem-group"),
    # chem-compose
    _q("p-chem-compose-1", "what is the molar mass of h2o?", "18.01",
       probe="chem-compose"),
    _q("p-chem-compose-2", "give the molar mass of water", "18.01",
       probe="chem-compose"),
    _q("p-chem-compose-3", "what does one mole of water weigh?", "18.01",
       probe="chem-compose"),
    # prog-lean
    _q("p-prog-lean-1", "in which file is GLM.NormFamily.family_tower?",
       "normfamily.lean", probe="prog-lean"),
    _q("p-prog-lean-2", "where is GLM.NormFamily.family_tower declared?",
       "normfamily.lean", probe="prog-lean"),
    _q("p-prog-lean-3", "what file declares GLM.NormFamily.family_tower?",
       "normfamily.lean", probe="prog-lean"),
    # prog-python
    _q("p-prog-python-1", "in which module is rung_audit defined?",
       "norm_escalation", probe="prog-python"),
    _q("p-prog-python-2", "what module is the function rung_audit in?",
       "norm_escalation", probe="prog-python"),
    _q("p-prog-python-3", "where does rung_audit live?", "norm_escalation",
       probe="prog-python"),
    # prog-behaviour
    _q("p-prog-behaviour-1", "what does completeness return?", "complete",
       probe="prog-behaviour"),
    _q("p-prog-behaviour-2", "what fields does "
                             "glm_universal.substrate.norm_family.completeness"
                             " return?", "complete", probe="prog-behaviour"),
    _q("p-prog-behaviour-3", "what is returned by "
                             "glm_universal.substrate.norm_family.completeness"
                             "?", "complete", probe="prog-behaviour"),
    # prog-count
    _q("p-prog-count-1", "how many rungs are in the norm family?", "25",
       probe="prog-count"),
    _q("p-prog-count-2", "what is the number of rungs of the norm family?",
       "25", probe="prog-count"),
    _q("p-prog-count-3", "the norm family has how many rungs?", "25",
       probe="prog-count"),
)


#: The same operations asked of rows and arguments the probe never names.
#: Every label is a world fact: IUPAC standard atomic weights (abridged to
#: the digits the fragment needs), the 1959 international yard and pound
#: definitions, elementary number theory.
COMPOSITIONS: Tuple[HeldOut, ...] = (
    _q("c-weight-oxygen", "what is the atomic weight of oxygen?", "15.999"),
    _q("c-weight-sodium", "what is the atomic weight of sodium?", "22.98",
       "22.99"),
    _q("c-weight-iron", "how heavy is an iron atom?", "55.845"),
    _q("c-molar-co2", "what is the molar mass of carbon dioxide?", "44.0"),
    _q("c-molar-methane", "what is the molar mass of methane?", "16.04"),
    _q("c-molar-ammonia", "what is the molar mass of ammonia?", "17.03"),
    _q("c-block-sodium", "which block of the periodic table is sodium in?",
       "alkali"),
    _q("c-block-neon", "what group does neon belong to?", "noble"),
    _q("c-block-fluorine", "which block is fluorine in?", "halogen"),
    _q("c-name-fe", "which element has the symbol Fe?", "iron"),
    _q("c-name-na", "what element is Na?", "sodium"),
    _q("c-heavier-o-c", "is oxygen heavier than carbon?", "oxygen"),
    _q("c-heavier-fe-cu", "which is heavier, iron or copper?", "copper",
       note="copper 63.546 against iron 55.845"),
    _q("c-heaviest-element", "which element has the largest atomic weight?",
       "og", "oganesson"),
    _q("c-dim-energy", "what are the dimensions of energy?", "l^2 m t^-2"),
    _q("c-dim-pressure", "what are the dimensions of pressure?",
       "l^-1 m t^-2"),
    _q("c-verify-energy", "is energy dimensionally equal to force times "
                          "length?", "true", "holds"),
    _q("c-verify-false", "is energy dimensionally equal to mass times "
                         "velocity?", "false", "does not hold",
       note="momentum, not energy: the right answer is a no"),
    _q("c-convert-inch", "convert 10 inches to centimetres", "25.4"),
    _q("c-convert-mile", "how many kilometres is 1 mile?", "1.609"),
    _q("c-convert-pound", "convert 2 pounds to kilograms", "0.907"),
    _q("c-convert-feet", "how many metres is 100 feet?", "30.48"),
    _q("c-prime-97", "is 97 prime?", "is prime"),
    _q("c-prime-51", "is 51 a prime number?", "not prime",
       note="51 = 3 x 17"),
    _q("c-gcd-24-36", "what is the greatest common divisor of 24 and 36?",
       "12"),
    _q("c-lcm-4-6", "what is the least common multiple of 4 and 6?", "12"),
    _q("c-mul", "what is 7 times 8?", "56"),
    _q("c-sub", "what is 100 minus 37?", "63"),
    _q("c-ratio-5-4", "what is the prime limit of 5/4?", "5"),
    _q("c-lean-order",
       "which file is GLM.CoordinateOrder.order_scale_invariant in?",
       "coordinateorder.lean"),
)


#: Questions whose right outcome is a refusal, or one narrow answer.
ADVERSARIAL: Tuple[HeldOut, ...] = (
    _refuse("a-capital", "what is the capital of france?",
            "no register holds geography"),
    _refuse("a-convert-dims", "convert 3 metres to kilograms",
            "a length is not a mass; no conversion exists"),
    _refuse("a-div-zero", "what is 7 divided by 0?",
            "division by zero has no value"),
    _refuse("a-unobtainium", "what is the atomic weight of unobtainium?",
            "no such element"),
    # The literal is split after "GLM." so the package's Lean-citation audit
    # does not read a deliberately non-existent name as a stale citation; the
    # question text is unchanged.
    _refuse("a-no-decl", "which file is GLM." "Nowhere.nothing_here in?",
            "no such declaration"),
    _refuse("a-category-bp", "what is the boiling point of velocity?",
            "velocity has no boiling point"),
    _refuse("a-category-heavy", "is velocity heavier than carbon?",
            "velocity has no weight"),
    _refuse("a-moons", "how many moons does jupiter have?",
            "no register holds astronomy"),
    _refuse("a-hamlet", "who wrote hamlet?", "no register holds literature"),
    _refuse("a-incomplete", "is energy more abstract than?",
            "the comparison names one side only"),
    _refuse("a-love", "what is the melting point of love?",
            "a category error"),
    _refuse("a-kryptonite", "what is the molar mass of kryptonite?",
            "no such substance"),
    _refuse("a-sqrt-neg", "what is the square root of -1 as a rational "
                          "number?", "no rational square root exists"),
    _refuse("a-moon-mass", "how heavy is the moon?",
            "no register holds the moon"),
    _refuse("a-atomic-number-velocity", "what is the atomic number of "
                                        "velocity?", "a category error"),
    _refuse("a-convert-empty", "convert 5 feet to", "no target unit"),
    _refuse("a-prime-fraction", "is 3/2 prime?",
            "primality is a property of integers"),
    _refuse("a-gcd-one", "what is the gcd of 12?",
            "a gcd needs two arguments here"),
    _q("a-feathers", "which is heavier, a kilogram of feathers or a "
                     "kilogram of steel?", "same", "equal", "neither",
       note="the trick question: refusing is acceptable, naming one is wrong"),
    _refuse("a-weather", "will it rain tomorrow?", "no register holds "
                                                  "the future"),
)


#: A second set, written *after* the planner's first cut and committed before
#: it was run against it, by an author who had read the frames and was trying
#: to break them: shapes no frame reads, three-argument functions a two-
#: argument pattern could half-read, a precedence question, casing, missing
#: auxiliaries, units the table does not hold, rows the registers do not
#: hold.  It is weaker evidence of generalisation than the three sets above
#: -- it was written knowing the frames -- and stronger evidence of safety,
#: because it was aimed at the wrong answers.
STRESS: Tuple[HeldOut, ...] = (
    _q("s-polar-no", "is carbon heavier than oxygen?", "no,",
       "oxygen is heavier"),
    _q("s-false-sum", "is 2 + 2 equal to 5?", "false", "no,", "does not"),
    _q("s-atomic-weight-molecule", "what is the atomic weight of carbon "
                                   "dioxide?", "44.0",
       note="ill-posed for a molecule; the molar mass or a refusal"),
    _q("s-gcd-three", "what is the gcd of 8 and 12 and 18?", "2",
       note="a two-argument reading of the tail gives 6"),
    _q("s-precedence", "what is 2 + 3 * 4?", "14"),
    _q("s-prime-negative", "is -7 prime?", "not prime"),
    _q("s-prime-one", "is 1 prime?", "not prime"),
    _q("s-convert-zero", "convert 0 feet to metres", "= 0 "),
    _q("s-convert-compound", "convert 3 metres to feet and inches", "9.84",
       "9 feet"),
    _q("s-convert-no-aux", "how many feet in 3 metres?", "9.84"),
    _q("s-whats-heavier", "what's heavier: water or ethanol?", "ethanol"),
    _q("s-cross-table", "is water heavier than carbon?", "yes",
       "water is heavier"),
    _q("s-which-element-heavier", "which element is heavier, gold or "
                                  "lead?", "lead"),
    _q("s-weight-gold", "what is the atomic weight of gold?", "196.9"),
    _q("s-title-case", "What Is The Atomic Weight Of Carbon", "12.011"),
    _q("s-fragment", "atomic weight of carbon", "12.011"),
    _refuse("s-two-rows", "what is the atomic weight of carbon and "
                          "oxygen?", "two rows asked at once; one answer "
                                     "would be half an answer"),
    _q("s-melting-iron", "what is the melting point of iron?", "1811"),
    _q("s-boiling-water", "what is the boiling point of water?", "373"),
    _q("s-density-mercury", "what is the density of mercury?", "13.5"),
    _q("s-block-iron", "which block is iron in?", "transition"),
    _q("s-symbol-au", "which element has the symbol Au?", "gold"),
    _q("s-symbol-w", "what element is W?", "tungsten"),
    _q("s-symbol-k", "what element is K?", "potassium"),
    _refuse("s-symbol-none", "what element is Xq?", "no element has that "
                                                    "symbol"),
    _q("s-file-trailing",
       "which file is GLM.CoordinateOrder.order_scale_invariant proved in?",
       "coordinateorder.lean"),
    _refuse("s-who-proved",
            "who proved GLM.CoordinateOrder.order_scale_invariant?",
            "no register holds authorship"),
    _q("s-derivative-forward", "what is the derivative of position?",
       "velocity"),
    _q("s-integral", "what is velocity the integral of?", "acceleration"),
    _q("s-verify-false", "is force equal to mass times velocity "
                         "dimensionally?", "false", "does not hold"),
    _q("s-verify-two", "does energy have the same dimensions as torque?",
       "true", "holds"),
    _q("s-describe-oxygen", "tell me about oxygen", "oxygen"),
    _q("s-describe-fe", "describe Fe", "iron"),
    _refuse("s-capital-carbon", "what is the capital of carbon?",
            "a category error"),
    _q("s-rungs-ladder", "how many rungs does the norm family ladder "
                         "have?", "25"),
    _q("s-div-exact", "what is 10 divided by 4?", "2.5", "5/2"),
    _q("s-div-repeating", "what is 1 divided by 3?", "1/3"),
    _refuse("s-over-zero", "what is 12 over 0?", "division by zero"),
    _q("s-prime-two", "is 2 prime?", "is prime"),
    _q("s-prime-large", "is 1000003 prime?", "is prime"),
    _q("s-lcm-zero", "what is the lcm of 0 and 5?", "= 0"),
    _q("s-lightest-element", "which element has the smallest atomic "
                             "weight?", "hydrogen", "winners=h"),
    _q("s-kg-lb", "convert 5 kilograms to pounds", "11.02"),
    _q("s-seconds", "how many seconds are in 2 hours?", "7200"),
    _refuse("s-metre-seconds", "convert 1 metre to seconds",
            "a length is not a time"),
    _q("s-carbon-14", "what is the atomic weight of carbon-14?", "14.003"),
    _q("s-less-abstract", "is energy less abstract than water?", "no,"),
)


ALL_SETS: Dict[str, Tuple[HeldOut, ...]] = {
    "paraphrases": PARAPHRASES,
    "compositions": COMPOSITIONS,
    "adversarial": ADVERSARIAL,
    "stress": STRESS,
}


def score_answer(item: HeldOut, ok: bool, haystack: str) -> str:
    """The verdict of one asking, by the rule in the module docstring.

    Returns one of ``correct``, ``wrong``, ``refused`` and
    ``correct-refusal``.
    """
    text = haystack.lower()
    if item.expect is None:
        return "wrong" if ok else "correct-refusal"
    if not ok:
        return "refused"
    return "correct" if any(f in text for f in item.expect) else "wrong"
