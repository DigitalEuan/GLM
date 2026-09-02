"""What the undimensioned names denote -- a vocabulary decision, written down.

Why this register exists
------------------------
``reasoning.measure_view.relation_repair`` converts the lexicon's
``related_to`` triples wherever the physics register can decide them: 27 of
the 66 convert, and 39 remain.  Thirty-eight of those 39 are declined for one
reason -- an endpoint *reaches no dimension the physics register holds* -- and
that reason is a statement about a **lookup**, not about the world.  Left as
it stands it says only that the machine did not find something; it does not
say whether there was anything to find.

This module closes that gap by *deciding*, one name at a time, what each of
those endpoints denotes.  Each entry is a judgement made on purpose and
written down with its justification, in exactly the way every other register
entry is justified.  Nothing here is inferred from the shape of the relation
graph: the graph asks the question, and a person answers it.

The six verdicts
----------------
``quantity``
    the name denotes a quantity the physics register already holds, under a
    different spelling.  The entry names that quantity and supplies **no**
    coordinate: the dimension continues to be read out of the physics
    register, so a denotation can no more invent a quantity than
    :data:`~.comparison_classes.QUANTITY_ALIASES` can.
``ambiguous``
    the name ranges over several quantities the register holds and nothing in
    the word chooses between them.  The candidates are listed, and the
    decision *is* the refusal: a machine that picked one would be guessing.
``polymorphic``
    the name takes whatever dimension the thing it is applied to has --
    *magnitude*, *measurement*, *quantity*, *function*.  Every quantity is a
    candidate, so listing candidates would say nothing.
``carrier``
    the name denotes a thing that *bears* quantities rather than a quantity:
    an electron has a mass and a charge and is neither.
``process``
    the name denotes something that happens.  A process is quantified by
    quantities -- a rotation by an angle -- and is not one.
``abstraction``
    the name denotes no magnitude at all: a domain (*electricity*), a
    relation between events (*cause*), a state (*equilibrium*), an
    orientation label (*north*).

Only the first verdict makes a name dimensional.  The other five are
**decisions that it is not**, which is the point: after this register the
residue is not a list of failed lookups but a list of decided cases, and
:mod:`glm_universal.reasoning.denotation_view` measures exactly what changes.

What is checked
---------------
:func:`denotation_audit` requires that

* every verdict is one of the six;
* a ``quantity`` verdict names a quantity the physics register holds (through
  :func:`~.comparison_classes.resolve_quantity`), and no other verdict names
  one;
* an ``ambiguous`` verdict lists at least two candidates and every candidate
  is a quantity the register holds -- an ambiguity between things the machine
  does not have would be a different complaint;
* no decided name is itself a registered quantity or an existing alias, so a
  denotation reaches the register and never shadows it;
* every entry carries a justification, and no two entries name the same word.

Coverage -- that the decided names are exactly the undimensioned endpoints of
the residue, with none missing and none idle -- is checked in
:mod:`glm_universal.reasoning.denotation_view`, which is where the residue
lives.

Exactness
---------
This module holds no magnitudes at all.  It is a table of decisions about
words; every number it can be asked for is a count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import comparison_classes as cc
from . import physics as ph

__all__ = [
    "VERDICTS", "DIMENSIONAL_VERDICT",
    "Denotation", "DENOTATIONS",
    "denotation", "decided_names", "denotes_quantity",
    "verdict_of", "denotations_with_verdict",
    "denotation_audit", "register_summary",
]


#: The six answers the register may give.  ``quantity`` is the only one that
#: makes a name dimensional; the other five each say *why not*, and they are
#: kept apart because they are different reasons and a reader is owed the
#: difference.
VERDICTS: Tuple[str, ...] = (
    "quantity", "ambiguous", "polymorphic", "carrier", "process",
    "abstraction",
)

#: The one verdict under which a name reaches a dimension.
DIMENSIONAL_VERDICT: str = "quantity"


@dataclass(frozen=True)
class Denotation:
    """One decided name.

    ``quantity`` is set only under the ``quantity`` verdict and names an entry
    of the physics register; ``candidates`` only under ``ambiguous``.
    ``justification`` is the reason the decision was made, and is required:
    an entry without one would be an assertion.
    """

    name: str
    verdict: str
    justification: str
    quantity: Optional[str] = None
    candidates: Tuple[str, ...] = ()

    @property
    def dimensional(self) -> bool:
        """Whether this name reaches a dimension the register holds."""
        return self.verdict == DIMENSIONAL_VERDICT


#: The decided vocabulary.  Every name here is an endpoint of a ``related_to``
#: triple that ``relation_repair`` declined because the name reached no
#: dimension, and every entry says what the name denotes instead.  Ordered by
#: verdict so that the one dimensional decision is not lost among the
#: refusals.
DENOTATIONS: Tuple[Denotation, ...] = (

    # -- quantity ----------------------------------------------------------
    Denotation(
        name="gravity", verdict="quantity", quantity="gravitational_field",
        justification=(
            "In ordinary use *gravity* names the field a mass falls in -- "
            "'the gravity at the Earth's surface is 9.80665 m/s^2', which is "
            "standard gravity, an exactly defined value.  That is the "
            "register's `gravitational_field`, in newtons per kilogram, "
            "which is metres per second squared.  The entry supplies no "
            "coordinate: the ten EXT10 exponents continue to be read from "
            "the register's own entry, exactly as an alias does.  The word "
            "also has a second use -- the interaction, as in 'gravity is one "
            "of the four forces' -- and that use denotes no magnitude; the "
            "decision recorded here is that the measurable use is the one a "
            "quantity register should follow."),
    ),

    # -- ambiguous ---------------------------------------------------------
    Denotation(
        name="motion", verdict="ambiguous",
        candidates=("velocity", "momentum", "kinetic_energy"),
        justification=(
            "*Motion* names the state of a body that is moving, and three "
            "quantities the register holds are each called 'the amount of "
            "motion' by some standard usage: velocity, momentum -- Newton's "
            "own 'quantity of motion' -- and kinetic energy.  They have "
            "three different dimensions, and nothing in the word chooses.  "
            "The lexicon's own two triples show the same spread: *motion* is "
            "related to velocity in one and to acceleration in the other."),
    ),
    Denotation(
        name="space", verdict="ambiguous",
        candidates=("length", "area", "volume"),
        justification=(
            "*Space* is an extent, and the register holds three extents.  "
            "'The space between two towns' is a length, 'the floor space' an "
            "area, 'the space in the tank' a volume.  A single denotation "
            "would have to prefer one reading of a word whose whole use is "
            "that it does not commit to one."),
    ),
    Denotation(
        name="amplitude", verdict="ambiguous",
        candidates=("length", "pressure", "electric_field"),
        justification=(
            "An amplitude is the peak excursion of *whatever is waving*, so "
            "its dimension is the dimension of that thing: metres for a "
            "string, pascals for a sound wave, volts per metre for a light "
            "wave.  The lexicon's triple relates it to energy, which is the "
            "square-law relation between them rather than a dimension for "
            "the word."),
    ),

    # -- polymorphic -------------------------------------------------------
    Denotation(
        name="magnitude", verdict="polymorphic",
        justification=(
            "A magnitude is a magnitude *of* something, and takes that "
            "thing's dimension.  This is precisely why the lexicon's four "
            "degree words -- large, small, strong, weak -- are related to it: "
            "it is the general term under which they sit, not a quantity "
            "beside them."),
    ),
    Denotation(
        name="measurement", verdict="polymorphic",
        justification=(
            "A measurement has the dimension of the quantity measured and no "
            "dimension of its own.  The register already treats it that way: "
            "a reading is a pair of a quantity and a magnitude, so nothing "
            "would be gained by dimensioning the word for the pair."),
    ),
    Denotation(
        name="quantity", verdict="polymorphic",
        justification=(
            "The general term for what the register holds 726 of.  It ranges "
            "over all of them; that is what makes it the general term."),
    ),
    Denotation(
        name="function", verdict="polymorphic",
        justification=(
            "A function's values have whatever dimension its values have, "
            "and integrating or differentiating it changes that dimension by "
            "the dimension of the variable.  The word names a mapping, not a "
            "magnitude."),
    ),

    # -- carrier -----------------------------------------------------------
    Denotation(
        name="electron", verdict="carrier",
        justification=(
            "A particle, not a quantity.  It bears a mass and a charge, both "
            "of which the register holds; the word for the bearer is not the "
            "word for either."),
    ),
    Denotation(
        name="photon", verdict="carrier",
        justification=(
            "A quantum of the electromagnetic field.  It bears an energy and "
            "a momentum that depend on its frequency, so it has no magnitude "
            "of its own even in the quantities it does bear."),
    ),
    Denotation(
        name="ion", verdict="carrier",
        justification=(
            "An atom or molecule bearing a net charge.  The charge is a "
            "quantity the register holds; the charged thing is not."),
    ),
    Denotation(
        name="plasma", verdict="carrier",
        justification=(
            "A state of matter -- an ionised gas.  Like any body of matter "
            "it bears a temperature, a density and a degree of ionisation, "
            "and is none of them."),
    ),
    Denotation(
        name="magnet", verdict="carrier",
        justification=(
            "A body with a magnetic moment.  The register holds "
            "`magnetic_dipole_moment` and `magnetic_flux_density`; the body "
            "that has them is a thing, not a magnitude."),
    ),
    Denotation(
        name="bond", verdict="carrier",
        justification=(
            "A chemical bond bears a dissociation energy and a bond length "
            "-- the diatomic register holds both for 52 species -- and the "
            "bond itself is the thing that bears them."),
    ),
    Denotation(
        name="boundary", verdict="carrier",
        justification=(
            "A boundary is a locus: the surface at which a system stops.  It "
            "bears an area and, in a thermodynamic argument, a flux through "
            "it; the word names the place, not the amount."),
    ),
    Denotation(
        name="observer", verdict="carrier",
        justification=(
            "An agent, or a frame.  What an observer contributes to a "
            "physical statement is a frame of reference, which selects the "
            "values of quantities and is not one."),
    ),
    Denotation(
        name="environment", verdict="carrier",
        justification=(
            "The surroundings of a system: another system, bearing whatever "
            "quantities a system bears.  The word marks a division of the "
            "world into two parts, and neither part is a magnitude."),
    ),

    # -- process -----------------------------------------------------------
    Denotation(
        name="move", verdict="process",
        justification=(
            "A verb.  Moving is quantified by a velocity -- which is the "
            "lexicon's own triple -- and is not one; the process and the "
            "quantity that measures its rate are different things."),
    ),
    Denotation(
        name="rotate", verdict="process",
        justification=(
            "A verb.  A rotation is quantified by an angle, and by an "
            "angular velocity if it is going on; neither is the rotating."),
    ),
    Denotation(
        name="attract", verdict="process",
        justification=(
            "A verb.  Attracting is quantified by the force between the two "
            "bodies; the force is a quantity, the attracting is what the "
            "bodies do."),
    ),
    Denotation(
        name="react", verdict="process",
        justification=(
            "A verb.  A reaction is quantified by an enthalpy, a rate and an "
            "activation energy, all of which are quantities and none of "
            "which is the reacting."),
    ),
    Denotation(
        name="reaction", verdict="process",
        justification=(
            "The noun for what *react* names, and a process for the same "
            "reason: it happens, it takes time, and it is quantified by "
            "quantities it is not."),
    ),
    Denotation(
        name="change", verdict="process",
        justification=(
            "A verb, and the general one: any quantity may change.  A "
            "particular change has the dimension of what changed, so the "
            "word names the happening rather than a magnitude -- which is "
            "why the lexicon relates *time* to it."),
    ),
    Denotation(
        name="measure", verdict="process",
        justification=(
            "A verb.  Measuring is an act performed on a quantity; its "
            "result is a measurement, which is polymorphic for the same "
            "reason."),
    ),
    Denotation(
        name="observe", verdict="process",
        justification=(
            "A verb.  Observing is an act, related in the lexicon to the "
            "observer who performs it; neither the act nor the agent is a "
            "quantity."),
    ),
    Denotation(
        name="predict", verdict="process",
        justification=(
            "A verb.  Predicting is an act about a time later than the one "
            "it is performed at -- which is the lexicon's triple -- and time "
            "is the quantity, not the predicting."),
    ),
    Denotation(
        name="integrate", verdict="process",
        justification=(
            "A verb, and an operation on a function: it multiplies the "
            "dimension of the integrand by the dimension of the variable of "
            "integration.  An operation that *changes* dimension cannot "
            "itself have one."),
    ),
    Denotation(
        name="differentiate", verdict="process",
        justification=(
            "A verb, and the inverse operation: it divides by the dimension "
            "of the variable.  Same reason."),
    ),

    # -- abstraction -------------------------------------------------------
    Denotation(
        name="electricity", verdict="abstraction",
        justification=(
            "The name of a domain of phenomena, in the way *optics* is.  The "
            "register holds its quantities -- charge, current, potential, "
            "resistance -- and there is no quantity of electricity beside "
            "them."),
    ),
    Denotation(
        name="cause", verdict="abstraction",
        justification=(
            "A relation between events, not a magnitude.  The lexicon "
            "relates it to force, which is the quantity a physical cause is "
            "usually delivered as, and no amount of force is a cause."),
    ),
    Denotation(
        name="effect", verdict="abstraction",
        justification=(
            "The other end of that relation.  An effect is whatever "
            "happened; the lexicon relates it to change for that reason."),
    ),
    Denotation(
        name="equilibrium", verdict="abstraction",
        justification=(
            "A condition on a system -- that the net force, or the net flux, "
            "or the net rate of reaction, is zero.  It is a predicate over "
            "quantities and takes no value itself."),
    ),
    Denotation(
        name="balance", verdict="abstraction",
        justification=(
            "The same condition under an ordinary-language name, which is "
            "why the lexicon relates the two.  (The instrument called a "
            "balance is a carrier, and a different word.)"),
    ),
    Denotation(
        name="direction", verdict="abstraction",
        justification=(
            "An orientation.  A direction is a unit vector: it is exactly "
            "the part of a vector quantity that is left when the magnitude "
            "is divided out, so it carries no magnitude by construction."),
    ),
    Denotation(
        name="north", verdict="abstraction",
        justification=(
            "A label for one pole, and one end of an orientation.  The "
            "magnetic field it labels is a quantity the register holds; the "
            "label is not."),
    ),
    Denotation(
        name="south", verdict="abstraction",
        justification=(
            "The opposite label, for the same reason."),
    ),
)


_BY_NAME: Dict[str, Denotation] = {d.name: d for d in DENOTATIONS}


def denotation(name: str) -> Optional[Denotation]:
    """The decision recorded for ``name``, or ``None`` if there is none."""
    return _BY_NAME.get(name)


def decided_names() -> Tuple[str, ...]:
    """Every name this register decides, in register order."""
    return tuple(d.name for d in DENOTATIONS)


def verdict_of(name: str) -> Optional[str]:
    """The verdict recorded for ``name``, or ``None`` if it is undecided."""
    found = _BY_NAME.get(name)
    return None if found is None else found.verdict


def denotations_with_verdict(verdict: str) -> Tuple[Denotation, ...]:
    """Every entry with the given verdict, in register order."""
    return tuple(d for d in DENOTATIONS if d.verdict == verdict)


def denotes_quantity(name: str) -> Optional[str]:
    """The physics register's quantity this name denotes, if it denotes one.

    ``None`` for every verdict but ``quantity`` -- including the ambiguous
    ones, where the point of the entry is that the machine must not choose.
    """
    found = _BY_NAME.get(name)
    if found is None or not found.dimensional:
        return None
    return found.quantity


def _registered(name: str) -> bool:
    try:
        ph.quantity_by_name(cc.resolve_quantity(name))
    except KeyError:
        return False
    return True


def denotation_audit() -> Dict[str, object]:
    """Check the register against the five rules in the module docstring."""
    bad_verdict: List[str] = []
    unregistered_target: List[str] = []
    quantity_without_verdict: List[str] = []
    thin_candidates: List[str] = []
    unregistered_candidate: List[str] = []
    shadowing: List[str] = []
    unjustified: List[str] = []
    duplicates: List[str] = []

    seen: Dict[str, int] = {}
    for entry in DENOTATIONS:
        seen[entry.name] = seen.get(entry.name, 0) + 1
        if entry.verdict not in VERDICTS:
            bad_verdict.append(entry.name)
        if entry.dimensional:
            if entry.quantity is None or not _registered(entry.quantity):
                unregistered_target.append(entry.name)
        elif entry.quantity is not None:
            quantity_without_verdict.append(entry.name)
        if entry.verdict == "ambiguous":
            if len(entry.candidates) < 2:
                thin_candidates.append(entry.name)
            for candidate in entry.candidates:
                if not _registered(candidate):
                    unregistered_candidate.append(
                        f"{entry.name} -> {candidate}")
        elif entry.candidates:
            thin_candidates.append(entry.name)
        if _registered(entry.name):
            shadowing.append(entry.name)
        if len(entry.justification) < 40:
            unjustified.append(entry.name)
    duplicates = sorted(n for n, count in seen.items() if count > 1)

    sound = not (bad_verdict or unregistered_target
                 or quantity_without_verdict or thin_candidates
                 or unregistered_candidate or shadowing or unjustified
                 or duplicates)
    return {
        "entries": len(DENOTATIONS),
        "bad_verdict": tuple(bad_verdict),
        "unregistered_target": tuple(unregistered_target),
        "quantity_without_verdict": tuple(quantity_without_verdict),
        "thin_candidates": tuple(thin_candidates),
        "unregistered_candidate": tuple(unregistered_candidate),
        "shadowing": tuple(shadowing),
        "unjustified": tuple(unjustified),
        "duplicates": tuple(duplicates),
        "sound": sound,
    }


def register_summary() -> Dict[str, object]:
    """Counts by verdict, and the one dimensional decision spelled out."""
    by_verdict = {v: len(denotations_with_verdict(v)) for v in VERDICTS}
    dimensional = {d.name: d.quantity
                   for d in denotations_with_verdict(DIMENSIONAL_VERDICT)}
    ambiguous = {d.name: d.candidates
                 for d in denotations_with_verdict("ambiguous")}
    return {
        "entries": len(DENOTATIONS),
        "by_verdict": by_verdict,
        "dimensional": dimensional,
        "dimensional_count": len(dimensional),
        "ambiguous": ambiguous,
        "audit": denotation_audit(),
    }
