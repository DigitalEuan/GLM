"""The declared cases of round 5 of the order of work -- discourse state
(``studies/DISCOURSE_STATE_STUDY.md``, Phase 92).

Written down before any code of the round.  Each case is
``(key, script, expected, note)``: ``script`` is the whole conversation with
the follow-up last, and ``expected`` is one of

* a register name -- the follow-up binds that single row;
* ``("column", (name, ...))`` -- the follow-up is asked of every row of a
  set-valued referent, in the order given, and answered as a column;
* ``("why", subject)`` -- *why?* explains the turn before it, and the
  explanation names ``subject`` (the bound name, the refusal reason, or the
  query a whole turn asked);
* a refusal reason -- ``no-antecedent``, ``ambiguous-antecedent``,
  ``unlicensed``, and the two this round adds: ``column-incomplete`` (a
  set-valued referent some of whose rows do not answer the question) and
  ``number-mismatch`` (a plural pronoun with one referent, or *both* with a
  number of referents other than two).

What *the answer for several rows at once* is, stated before any code
(candidate 0b): a fold whose end is attained by several rows **produced a
set**, and a later *it* or *them* names that set.  The question is asked of
every row of it, each by the same session that would answer it written out
in full, and the answer is the column of those answers in the fold's order.
The column is answered only when every row answers; a row that does not is a
hole, and a hole refuses the column (``column-incomplete``) exactly as a hole
refuses a fold over a column (Phase 85), unless no row at all answers, when
the set does not decide and older turns are read, as for any unlicensed side.
A comparison's two rows are *not* a set the turn produced: *it* after one is
still ``ambiguous-antecedent``; *both of them* names the pair.

The three groups:

``COLUMN_CASES``  0b -- a tie carried as a column (marks D1, D6);
``FOURTH_CASES``  D = 0a -- *the one before that*, *both of them* / *them*,
                  and *why?* (mark D2);
``SURFACE_CASES`` K3 -- follow-ups bound on every surface: the licensing test
                  is the multi-surface router, not the session alone (D3).
"""

from __future__ import annotations

from typing import Tuple

LEXICON_TIE = ("atom", "bond", "C", "Cl", "computer", "instrument", "ion",
               "liquid", "molecule", "neutron", "proton", "sky", "solid",
               "water")
ION_TIE = ("carbonate ion", "sulfate ion")

Case = Tuple[str, Tuple[str, ...], object, str]

COLUMN_CASES: Tuple[Case, ...] = (
    ("tie-describe",
     ("largest abstract_concrete in carrier:lexicon", "describe it"),
     ("column", LEXICON_TIE),
     "the fourteen-row tie Phase 55 refused, carried as a column"),
    ("tie-field",
     ("smallest charge in molecule", "field molar_mass_u of it"),
     ("column", ION_TIE),
     "a two-row tie, and a field every row of it holds"),
    ("tie-incomplete",
     ("largest abstract_concrete in carrier:lexicon",
      "field electronegativity_pauling of it"),
     "column-incomplete",
     "two of the fourteen rows hold an electronegativity; twelve are holes"),
    ("column-carried",
     ("smallest charge in molecule", "describe it",
      "field molar_mass_u of it"),
     ("column", ION_TIE),
     "a column turn produced the same set, and the next turn names it again"),
    ("dead-set-walked-past",
     ("describe carbon", "smallest charge in molecule",
      "field electronegativity_pauling of it"),
     "C",
     "no row of the set answers, so the set does not decide and the older "
     "turn does"),
    ("no-tie-unchanged",
     ("largest atomic_weight_u in element", "describe it"),
     "Og",
     "one row attains the end: the binding is Phase 55's"),
    ("comparison-still-ambiguous",
     ("order atomic_weight_u of carbon and oxygen", "describe it"),
     "ambiguous-antecedent",
     "a comparison's two rows are not a set the turn produced"),
)

FOURTH_CASES: Tuple[Case, ...] = (
    ("prior",
     ("describe carbon", "describe water", "describe the one before that"),
     "C",
     "that is water; the one before it is carbon"),
    ("prior-licensing",
     ("describe carbon", "describe oxygen", "describe water",
      "field electronegativity_pauling of the one before that"),
     "C",
     "water answers nothing here, so that is oxygen, and the one before it "
     "carbon"),
    ("prior-none",
     ("describe carbon", "describe the one before that"),
     "no-antecedent",
     "nothing was named before that"),
    ("prior-set",
     ("smallest charge in molecule", "describe water",
      "describe the one before that"),
     ("column", ION_TIE),
     "the one before that may itself be a set"),
    ("both",
     ("order atomic_weight_u of carbon and oxygen", "describe both of them"),
     ("column", ("C", "O")),
     "the pair a comparison was about"),
    ("both-field",
     ("order atomic_weight_u of carbon and oxygen",
      "field electronegativity_pauling of both of them"),
     ("column", ("C", "O")),
     "the same pair, a field both rows hold"),
    ("both-across-turns",
     ("describe carbon", "describe oxygen", "describe both of them"),
     ("column", ("C", "O")),
     "two turns of one row each, in the order they were named"),
    ("both-wrong-number",
     ("largest abstract_concrete in carrier:lexicon",
      "describe both of them"),
     "number-mismatch",
     "both says two, and the set holds fourteen"),
    ("them-set",
     ("smallest charge in molecule", "field molar_mass_u of them"),
     ("column", ION_TIE),
     "them names the set the fold produced"),
    ("them-one-row",
     ("describe carbon", "describe them"),
     "number-mismatch",
     "a plural pronoun with one referent"),
    ("them-incomplete",
     ("largest abstract_concrete in carrier:lexicon",
      "field electronegativity_pauling of them"),
     "column-incomplete",
     "the set has holes for this field"),
    ("plural-first-turn",
     ("describe both of them",),
     "no-antecedent",
     "a follow-up with nothing to follow"),
    ("why-after-binding",
     ("describe carbon", "describe it", "why?"),
     ("why", "C"),
     "the explanation names what the pronoun was bound to"),
    ("why-after-refusal",
     ("largest abstract_concrete in carrier:lexicon",
      "field electronegativity_pauling of it", "why?"),
     ("why", "column-incomplete"),
     "a refusal is a turn, and why? restates its reason"),
    ("why-after-whole",
     ("describe carbon", "why?"),
     ("why", "describe carbon"),
     "a whole query: the explanation is its own derivation"),
    ("why-first-turn",
     ("why?",),
     "no-antecedent",
     "nothing to explain"),
)

SURFACE_CASES: Tuple[Case, ...] = (
    ("surface-stepwise-pronoun",
     ("describe iron", "is the atomic number of it prime"),
     "Fe",
     "the stepwise planner answers the rewritten question; the session "
     "alone does not"),
    ("surface-planner-subject",
     ("what is the electronegativity of carbon", "and oxygen?"),
     "oxygen",
     "a turn the typed planner answered, its row read from the question"),
    ("surface-both-ordering",
     ("which is heavier, carbon or oxygen", "describe both of them"),
     ("column", ("C", "O")),
     "a comparison the planner answered, its two rows named"),
    ("surface-column",
     ("smallest charge in molecule", "what is the molar mass of it"),
     ("column", ION_TIE),
     "a set carried into a question only the typed planner reads"),
    ("surface-stepwise-given",
     ("describe hydrogen",
      "given the ionization energy of it and wave speed = 299792458, what "
      "is the wavelength"),
     "H",
     "a register value fed to a wheel derivation through the pronoun"),
    ("surface-unlicensed",
     ("describe water", "is the atomic number of it prime"),
     "unlicensed",
     "no surface answers it of water"),
)

ALL_CASES: Tuple[Case, ...] = COLUMN_CASES + FOURTH_CASES + SURFACE_CASES

#: The one earlier declared outcome this round is declared to move: Phase
#: 55's ``pronoun-tie-refused`` (``describe it`` after the fourteen-row tie)
#: goes from ``ambiguous-antecedent`` to the column.  Every other row of
#: ``conversation.DECLARED_FOLLOW_UPS`` keeps its outcome.
DECLARED_MOVES = {"pronoun-tie-refused": ("column", LEXICON_TIE)}
