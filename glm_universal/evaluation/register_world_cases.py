"""The declared cases of round 6 of the order of work -- the register against
the world (``studies/REGISTER_WORLD_STUDY.md``, Phase 93).

Written down before any code of the round.  What was seen first, said
plainly: the two outside sources were fetched and frozen
(``data_objects/_data/world_ciaaw_2024.json``, ``world_nist_ie.json``), and a
throw-away comparison was run against the register while the snapshots were
being checked for transcription.  So the *counts* in the list cases below
were seen before this file; what this file fixes before any code is the
reading -- the six verdicts, the interval rule, the configuration rule, the
molecule rule and the completion gate -- and the marks the round is judged by.

The reading, stated before any code
-----------------------------------
A register cell and the world's value for it are compared, never merged, and
the register is never written to.  Each of the 354 cells of the three
world-checked fields (``atomic_weight_u``, ``ionization_energy_eV``,
``electron_configuration``, 118 rows each) receives exactly one verdict:

``agrees``
    the register's point value lies inside the world's interval (for a
    configuration: the two occupations are equal);
``agrees_at_stated_precision``
    the point lies outside, but the register's value read at the precision it
    is held to (half a unit of its last place either side -- the reading of
    ``Interval.as_held``) meets the world's interval: some value both allow
    exists, so the register may be a correct rounding;
``discrepant``
    no value both allow exists: the register's held interval and the world's
    interval are disjoint (a configuration: the occupations differ);
``world_silent``
    the world holds no value (CIAAW gives no standard atomic weight to an
    element without a characteristic terrestrial isotopic composition; NIST
    holds no neutral ionization energy past hassium);
``register_silent``
    the world holds a value and the register holds none -- a cell the world
    could fill, reported, never written;
``both_silent``.

The world's interval: CIAAW ``[a, b]`` is itself; ``v(u)`` is ``v +/- u``
with ``u`` in the last places of ``v``.  NIST ``v`` with uncertainty ``u`` is
``v +/- u``; a NIST value with no stated uncertainty is read at the precision
it is quoted to (the same rule the register's own values get).  A NIST value
the database marks theoretical ``( )`` or semi-empirical ``[ ]`` is compared
the same way and the mark is carried into the verdict.

A configuration is compared as an **occupation**: the map from subshell
(``4s``, ``3d``, ...) to electron count, after expanding a noble-gas core
(``[Ar]``) by the cores the database lists.  The order subshells are written
in is not part of the configuration (``[Ar]4s2 3d6`` is ``[Ar].3d6.4s2``).
A ``(predicted)`` or ``(calculated)`` tag is carried, not compared.

A molecule's molar mass is checked through its elements: the register's
interval is the sum of ``count x`` each element's held interval, the world's
the sum of ``count x`` each element's standard interval.  A molecule is
``world_silent`` if any of its elements is.  A molecule can be discrepant
only if one of its elements is (proved: ``GLM.RegisterWorld.sum_meets``).

The completion gate (H's first item)
------------------------------------
A completion rule is admitted only if it passes the Phase 61 gate **and** its
nested holdout skill (the rule re-chosen without the held-out element, then
scored on it -- ``substrate_cognition.nested_holdout_experiment``) is at most
one half.  A field whose rule fails the second gate over all elements may be
**narrowed** to one declared domain, the main-group elements (groups 1, 2
and 13-18), if the nested skill re-measured inside that domain passes, scored
on at least 20 folds.  The domain was chosen after measuring three (all, the
main group, the d- and f-block placed in groups 3-12) -- which is itself a
selection, and the study reports it as one.  Declared outcome:
``covalent_radius_pm`` is demoted outright (nested skill above one half in
every domain), ``electron_affinity_eV`` is narrowed to the main group, and
the other seven admitted rules are untouched.

Each question case is ``(key, question, expected, note)`` and ``expected`` is

* ``"yes"`` / ``"no"`` -- the answer begins so;
* ``("refuse", CODE)`` -- refused, and the refusal names ``CODE``;
* ``("list", (symbol, ...))`` -- the answer lists exactly these rows.

The marks (judged by ``tools register-world``):

R1  every one of the 354 cells receives exactly one verdict;
R2  the register is not written: its file digest and every loaded value are
    identical before and after the whole report and every question;
R3  every question case comes out as declared, with 0 wrong;
R4  injected errors are caught: for every cell with both values, a register
    value moved wholly outside the world's interval is reported
    ``discrepant``, and the world's own value written at the register's
    precision never is;
R5  every molecule is decided, and no molecule is discrepant while all its
    elements agree;
R6  earlier verdicts hold: of Phase 63's eight interval questions seven are
    unchanged and one moves as declared (``y1-gold-standard``, refused
    before because gold was not in the 30-row table, now ``yes``);
R7  the completion gate: the declared outcome above, the measured layer still
    the register, every empty cell still decided, and the estimated count
    moving by exactly the cells the two fields lose;
R8  proved in ``RequestProject/GLM/RegisterWorld.lean``.
"""

from __future__ import annotations

from typing import Tuple

Case = Tuple[str, str, object, str]

#: The ionization energies the declared reading finds discrepant (seen while
#: the snapshot was checked; see the head of this file).
IE_DISCREPANT = ("As", "Tc", "Sb", "Pr", "Pm", "Ta", "W", "Re", "Os", "Ir",
                 "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pu", "Am",
                 "Cm", "Bk", "Es", "No")

WEIGHT_CASES: Tuple[Case, ...] = (
    ("w-iron", "is the atomic weight of iron consistent with the standard "
     "value", "yes",
     "held 55.84 -> [55.835, 55.845] meets 55.845(2) at the stated precision "
     "only: the planner's one wrong answer, now located rather than hidden"),
    ("w-gold", "is the atomic weight of gold consistent with the standard "
     "value", "yes",
     "the declared move: gold was outside the 30-row table; 196.96657 lies "
     "inside 196.966570(4)"),
    ("w-lead", "is the atomic weight of lead consistent with the standard "
     "value", "yes", "held as 207, inside the interval [206.14, 207.94]"),
    ("w-carbon", "is the atomic weight of carbon consistent with the "
     "standard value", "yes", "12.011 lies inside [12.0096, 12.0116]"),
    ("w-technetium", "is the atomic weight of technetium consistent with the "
     "standard value", ("refuse", "WORLD_SILENT"),
     "CIAAW gives technetium no standard atomic weight"),
    ("w-oganesson", "is the atomic weight of oganesson consistent with the "
     "standard value", ("refuse", "WORLD_SILENT"),
     "nor any element past uranium"),
    ("w-list", "which elements have an atomic weight inconsistent with the "
     "standard value", ("list", ()),
     "none: every checked weight agrees, eleven only at stated precision"),
)

ENERGY_CASES: Tuple[Case, ...] = (
    ("e-iron", "is the ionization energy of iron consistent with the "
     "standard value", "yes", "7.902 at three places meets 7.9024681(12)"),
    ("e-tantalum", "is the ionization energy of tantalum consistent with the "
     "standard value", "no",
     "the register holds 7.89; NIST holds 7.549571(25)"),
    ("e-arsenic", "is the ionization energy of arsenic consistent with the "
     "standard value", "no", "9.815 against 9.78855(25)"),
    ("e-actinium", "is the ionization energy of actinium consistent with the "
     "standard value", "no", "5.17 against 5.380235(12)"),
    ("e-krypton", "is the ionization energy of krypton consistent with the "
     "standard value", "yes",
     "held as 14, read at zero places as [13.5, 14.5]: consistent, and the "
     "answer says how coarsely"),
    ("e-lawrencium", "is the ionization energy of lawrencium consistent with "
     "the standard value", ("refuse", "REGISTER_SILENT"),
     "NIST holds 4.96(5); the register holds nothing to compare"),
    ("e-oganesson", "is the ionization energy of oganesson consistent with "
     "the standard value", ("refuse", "WORLD_SILENT"),
     "neither holds a value; the world's silence is named first"),
    ("e-electronegativity", "is the electronegativity of carbon consistent "
     "with the standard value", ("refuse", "STANDARD_UNDECLARED"),
     "no outside source is declared for electronegativity"),
    ("e-list", "which elements have an ionization energy inconsistent with "
     "the standard value", ("list", IE_DISCREPANT),
     "the whole report's discrepant ionization energies, in atomic-number "
     "order"),
)

CONFIGURATION_CASES: Tuple[Case, ...] = (
    ("c-chromium", "is the electron configuration of chromium consistent "
     "with the standard value", "yes", "[Ar]4s1 3d5, the familiar exception"),
    ("c-iron", "is the electron configuration of iron consistent with the "
     "standard value", "yes",
     "[Ar]4s2 3d6 against [Ar].3d6.4s2: the order written is not compared"),
    ("c-lawrencium", "is the electron configuration of lawrencium consistent "
     "with the standard value", "no",
     "the register holds 6d1; NIST holds 7p1"),
    ("c-oganesson", "is the electron configuration of oganesson consistent "
     "with the standard value", ("refuse", "WORLD_SILENT"),
     "the snapshot holds no configuration past hassium"),
    ("c-list", "which elements have an electron configuration inconsistent "
     "with the standard value", ("list", ("Lr",)), "one row"),
)

MOLECULE_CASES: Tuple[Case, ...] = (
    ("m-water", "is the molar mass of water consistent with the standard "
     "value", "yes", "2 x H + O against 2 x [1.00784, 1.00811] + O's interval"),
    ("m-glucose", "is the molar mass of glucose consistent with the standard "
     "value", "yes", "C6H12O6"),
    ("m-sulfate", "is the molar mass of sulfate ion consistent with the "
     "standard value", "yes", "an ion: the electrons' mass is not counted, as "
     "the register does not count it"),
)

ALL_CASES: Tuple[Case, ...] = (WEIGHT_CASES + ENERGY_CASES
                               + CONFIGURATION_CASES + MOLECULE_CASES)

#: R6: Phase 63's interval questions and the one declared move.
DECLARED_MOVES = {"y1-gold-standard": "yes"}

#: R7: the completion gate's declared outcome.
COMPLETION_DEMOTED = ("covalent_radius_pm",)
COMPLETION_NARROWED = {"electron_affinity_eV": "main group"}
COMPLETION_KEPT = ("atomic_radius_pm", "boiling_point_K", "density_g_per_cm3",
                   "electronegativity_pauling", "ionization_energy_eV",
                   "melting_point_K", "valence_electrons")
