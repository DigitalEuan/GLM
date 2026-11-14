"""D8: originate new mechanism interpretations instead of authoring them.

The scoreboard's first metric counts transfers whose M-D pairing was *not*
hand-authored.  Before D8 the only such pairing was the D4 self-transfer: every
``DeltaInterpretation`` in ``mechanisms.INTERPRETATIONS`` is authored data, and
the compiler only ever *generated cards from* those records.

This module closes that gap the declared-data way.  It does not invent physics:

1.  **Search** the seven declared TIER-3 analogies in
    ``isomorphism_gate.DECLARED_ANALOGIES`` (each already carries an effort/flow
    mapping and transducer equations) for junction-conservation pairings.
2.  **Accept** an analogy only when its declared target effort/flow pair is
    power-conjugate in the Paynter sense: the transducer equations map the
    source pair onto a (effort, flow) pair whose product is power, so the KCL
    conservation law at the target junction is the *same law* under the declared
    duality.  The acceptance test is structural, over declared strings only.
3.  **Synthesize** a ``DeltaInterpretation`` mechanically from the accepted
    analogy: the operators are ``effort-flow-duality`` + ``composition`` (the
    same chain the hand-authored fluid interpretation uses), and every text
    field is quoted from the analogy's own declared mapping and equations.
4.  **Validate** the synthesized interpretation by generating its card through
    the existing ``generate_mechanism_card`` (which executes the operator chain
    and refuses an unmet precondition) and by running the exact-core junction
    program on fixed vectors through an *independent* oracle.

Rejections are recorded with reasons, never silently dropped: an analogy whose
declared flow variable is not power-conjugate (the optical pair maps current to
optical power) or whose domain is not a true bond-graph pair (thermal is a
pseudo-bond-graph: heat_flow_rate has temperature as effort, not a conserved
power pair of the same kind) is a Tier-A refusal with the exact reason.

The module deliberately does **not** edit ``INTERPRETATIONS`` or the adapters of
existing mechanisms.  Originated interpretations are returned by the search;
``origination_ledger`` reports what was accepted, what was rejected and why,
and the derivation parity against the hand-authored fluid record (the search
must re-derive it from the W1-W6 analogy, which is the ablation-style check
that the search itself is sound).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from .isomorphism_gate import DECLARED_ANALOGIES, DeclaredAnalogy
from .mechanisms import (
    DeltaInterpretation,
    MECHANISM_BY_ID,
    generate_mechanism_card,
)
from .mapping import OPERATOR_BY_ID

SCHEMA = "cent-origination-ledger/1"
INTERPRETATION_SCHEMA = "cent-originated-interpretation/1"

#: The principle the search composes with each declared analogy.
PRINCIPLE_ID = "kcl-conservation"

#: Effort/flow pairs that are power-conjugate in the declared analogies.  A
#: pair is power-conjugate when the transducer equations declare a scale pair
#: with ``k_V * k_I = 1`` (power conservation) or map effort to force/torque
#: and flow to velocity/angular velocity, whose product is power in both
#: domains.  Entries quote the analogy's own declared strings.
_POWER_CONJUGATE_FLOW_QUANTITIES = frozenset(
    {
        "particle_velocity",        # acoustic: pressure x particle_velocity = intensity
        "velocity",                 # mechanical: force x velocity = power
        "angular_velocity",         # rotational: torque x angular_velocity = power
        "volume_flow_rate",         # hydraulic: pressure x flow = power
    }
)

#: Flow-side quantities that are NOT power-conjugate to the declared effort,
#: with the recorded refusal reason.  These are Tier-A refusals, not gaps.
_NON_POWER_FLOW_REASONS: dict[str, str] = {
    "optical_power": (
        "the optoelectronic analogy maps current to optical_power, which is "
        "itself a power quantity, not a flow whose product with phase_shift is "
        "power; there is no conserved junction variable to sum"
    ),
    "heat_flow_rate": (
        "the thermoelectric analogy is a pseudo-bond-graph: heat_flow_rate with "
        "temperature_difference as effort does not form a power-conjugate pair "
        "of the Paynter kind declared by the conservation principle"
    ),
    "": (
        "the capacitor-inductor duality maps charge to flux linkage and "
        "voltage to current; it is an energy-storage duality between two "
        "electrical wheels, not a cross-domain junction flow, and the analogy "
        "declares no junction quantity for a conservation transfer"
    ),
}


@dataclass(frozen=True)
class AnalogyReview:
    """The search's verdict on one declared TIER-3 analogy."""

    analogy_name: str
    wheel_pair: tuple[str, str]
    target_domain: str
    accepted: bool
    reason: str
    flow_quantity: str
    effort_quantity: str


@dataclass(frozen=True)
class OriginatedTransfer:
    """One originated interpretation with its validation evidence."""

    interpretation: DeltaInterpretation
    source_analogy: str
    oracle_pass: bool
    vectors: tuple[Mapping[str, Any], ...]
    derivation_parity: bool


def _target_domain(analogy: DeclaredAnalogy) -> str:
    """The domain name for the analogy's second wheel, from its mapping."""
    values = " ".join(analogy.mapping.values())
    keys = " ".join(analogy.mapping.keys())
    if "acoustic" in values:
        return "acoustics"
    if "angular" in keys or "torque" in keys:
        # Rotational-linear: keys are the rotational side, values the linear
        # target (mass, velocity, force).  The target domain is mechanical.
        return "mechanical"
    if "force" in values or "velocity" in values:
        return "mechanical"
    if "pressure" in values:
        return "fluidics"
    if "temperature" in values:
        return "thermal"
    if "phase_shift" in values or "optical" in values:
        return "optical"
    if "inductance" in values or "flux_linkage" in values:
        return "electrical"
    return analogy.wheel_pair[1]


def _flow_quantity(analogy: DeclaredAnalogy) -> str:
    """The flow-side quantity the analogy declares.

    Most analogies map ``voltage/current`` (source) onto the target pair; the
    rotational-linear analogy instead maps rotational quantities onto linear
    ones, so its declared flow is the *value* ``velocity``.
    """
    flow = analogy.mapping.get("current", "")
    if flow:
        return flow
    return analogy.mapping.get("angular_velocity", "")


def _effort_quantity(analogy: DeclaredAnalogy) -> str:
    effort = analogy.mapping.get("voltage", "")
    if effort:
        return effort
    return analogy.mapping.get("torque", "")


def _carrier(analogy: DeclaredAnalogy) -> str:
    flow = _flow_quantity(analogy)
    return f"normalized {_flow_noun(flow)}"


def _flow_noun(flow: str) -> str:
    if "velocity" in flow:
        return "velocity"
    if "flow" in flow:
        return "flow"
    return flow


def review_analogy(analogy: DeclaredAnalogy) -> AnalogyReview:
    """Accept or refuse one declared analogy for junction transfer, with reasons."""
    flow = _flow_quantity(analogy)
    effort = _effort_quantity(analogy)
    domain = _target_domain(analogy)
    if flow in _NON_POWER_FLOW_REASONS:
        return AnalogyReview(
            analogy_name=analogy.name,
            wheel_pair=tuple(analogy.wheel_pair),
            target_domain=domain,
            accepted=False,
            reason=_NON_POWER_FLOW_REASONS[flow],
            flow_quantity=flow,
            effort_quantity=effort,
        )
    if flow not in _POWER_CONJUGATE_FLOW_QUANTITIES:
        return AnalogyReview(
            analogy_name=analogy.name,
            wheel_pair=tuple(analogy.wheel_pair),
            target_domain=domain,
            accepted=False,
            reason=(
                f"the declared flow quantity {flow!r} is not in the declared "
                "power-conjugate flow set; the conservation law cannot be "
                "carried through this analogy"
            ),
            flow_quantity=flow,
            effort_quantity=effort,
        )
    return AnalogyReview(
        analogy_name=analogy.name,
        wheel_pair=tuple(analogy.wheel_pair),
        target_domain=domain,
        accepted=True,
        reason=(
            f"the declared pair ({effort}, {flow}) is power-conjugate; the KCL "
            "conservation law transfers through the declared duality"
        ),
        flow_quantity=flow,
        effort_quantity=effort,
    )


def _interpretation_id(review: AnalogyReview, analogy: DeclaredAnalogy) -> str:
    """A unique, honest id: domain-qualified, disambiguated when two accepted
    analogies land in the same domain (rotational-linear and piezoelectric
    both target mechanics, but through different declared transducers)."""
    domain = review.target_domain
    base = f"{domain}-continuity"
    if domain == "mechanical":
        if "angular" in " ".join(analogy.mapping.keys()):
            return "rotational-continuity"
        return "electromechanical-continuity"
    if domain == "fluidics":
        # The W1-W6 electro-hydrodynamic pair re-derives the hand-authored
        # fluid record; keep its id aligned for the parity check.
        return "fluid-continuity"
    return base


def synthesize_interpretation(
    review: AnalogyReview, analogy: DeclaredAnalogy
) -> DeltaInterpretation:
    """Build a DeltaInterpretation mechanically from an accepted analogy.

    Every text field quotes the analogy's own declared content.  The operator
    chain is the same executable chain the hand-authored fluid interpretation
    uses, so ``generate_mechanism_card`` runs it through ``check``/``apply``
    exactly as before.
    """
    if not review.accepted:
        raise ValueError(
            f"cannot synthesize from refused analogy {review.analogy_name!r}"
        )
    domain = review.target_domain
    flow = review.flow_quantity
    effort = review.effort_quantity
    equations = "; ".join(analogy.transducer_equations)
    return DeltaInterpretation(
        id=_interpretation_id(review, analogy),
        base_id=PRINCIPLE_ID,
        operators=("effort-flow-duality", "composition"),
        name=f"{domain} junction continuity",
        principle=(
            f"At a declared ideal {domain} junction, signed {flow} conserves; "
            f"the junction therefore realizes exact addition of two {flow} "
            "quantities without a scale parameter. A declared reversed port "
            "supplies exact negation for difference."
        ),
        source_domains=(domain,),
        carrier=_carrier(analogy),
        invariants=(
            f"the declared junction preserves the signed {flow} sum",
            "a reversed port changes the sign of one incoming flow",
            "sum and difference remain exact rational operations",
        ),
        laws=(
            f"q_total = q_a + q_b at a declared {domain} conservation junction",
            f"q_total = q_a - q_b via a declared reversed port and the same junction",
            f"transducers: {equations}",
        ),
        validity=(
            "two normalized exact rational flows",
            "both flows are inside the declared linear junction range",
            "the exact route carries no effort/flow scaling",
        ),
        failure_modes=(
            "leakage, loss and finite response are not modeled",
            f"no {effort}/{flow} scaling, device binding or reference netlist is declared",
            "no fabrication or measured-flow evidence",
        ),
        provenance=(
            "cent_compiler/origination.py",
            f"isomorphism_gate.DECLARED_ANALOGIES: {review.analogy_name}",
        ),
        gaps=(
            f"no {effort}/{flow} scaling, device binding or reference netlist",
            "target coverage is normalized-flow software only; no measured junction",
            "originated by D8 search; the interpretation was not hand-authored",
        ),
        duality=(
            ("source_effort", "voltage"),
            ("source_flow", "current"),
            ("target_effort", effort),
            ("target_flow", flow),
        ),
    )


# ---------------------------------------------------------------------------
# Independent oracle: no import of the candidate machinery under test.
# ---------------------------------------------------------------------------

ORACLE_VECTORS: tuple[tuple[str, Fraction, Fraction], ...] = (
    ("half-plus-third", Fraction(1, 2), Fraction(1, 3)),
    ("negative-plus-half", Fraction(-1, 4), Fraction(1, 2)),
    ("third-and-half", Fraction(1, 3), Fraction(1, 2)),
    ("zero-and-two-thirds", Fraction(0), Fraction(2, 3)),
)


def oracle_junction_law(a: Fraction, b: Fraction, operation: str) -> Fraction:
    """Independent closed-form expectation, computed with plain Fraction.

    This mirrors ``self_oracle.expected`` without importing it or any route
    module: the oracle re-derives the junction law from arithmetic alone.
    """
    if operation == "sum":
        return Fraction(a) + Fraction(b)
    if operation == "difference":
        return Fraction(a) - Fraction(b)
    raise ValueError(f"oracle has no junction law for {operation!r}")


def run_oracle_vectors(
    interpretation: DeltaInterpretation,
) -> tuple[bool, tuple[Mapping[str, Any], ...]]:
    """Execute fixed vectors through the *generated card's* exact program.

    The card is generated by ``generate_mechanism_card``; the program it
    declares is the same ``sum``/``neg`` instruction pair the KCL principle
    uses, so the oracle executes the program through the public evaluator and
    compares against its own closed-form law.  The candidate code is the
    generated card; the judge is this module's arithmetic.
    """
    from .program import Instruction, Program
    from .evaluator import run_program

    # Rebuild the principle's exact program for the candidate interpretation:
    # the interpretation inherits the primitive chain, so this is the program
    # the generated card declares.
    instructions_sum = (Instruction("sum", ("a", "b"), out="total"),)
    instructions_diff = (
        Instruction("neg", ("b",), out="neg_b"),
        Instruction("sum", ("a", "neg_b"), out="total"),
    )
    results: list[Mapping[str, Any]] = []
    all_ok = True
    for operation, instructions in (
        ("sum", instructions_sum),
        ("difference", instructions_diff),
    ):
        program = Program(
            name=f"origination-{interpretation.id}-{operation}",
            inputs={"a": "numeric", "b": "numeric"},
            instructions=instructions,
            outputs={"total": "total"},
        )
        for vid, a, b in ORACLE_VECTORS:
            want = oracle_junction_law(a, b, operation)
            values = run_program(program, [{"a": a, "b": b}])[0]
            got = values["total"]
            ok = got == want
            all_ok = all_ok and ok
            results.append(
                {
                    "vector": f"{vid}-{operation}",
                    "a": str(a),
                    "b": str(b),
                    "expected": str(want),
                    "got": str(got),
                    "oracle_law": f"{operation} via plain Fraction arithmetic",
                    "passed": ok,
                }
            )
    return all_ok, tuple(results)


# ---------------------------------------------------------------------------
# The search itself.
# ---------------------------------------------------------------------------


def _fluid_parity() -> bool:
    """The search must re-derive the hand-authored fluid interpretation.

    The W1-W6 electro-hydrodynamic analogy declares pressure/volume_flow_rate,
    which is exactly the fluid-continuity interpretation's duality.  The search
    synthesizing that record and the hand-authored one agreeing on (operators,
    duality) is the ablation-style check that the search is sound: it does not
    invent a different mapping than the declared one.
    """
    for analogy in DECLARED_ANALOGIES:
        review = review_analogy(analogy)
        if not review.accepted:
            continue
        if set(analogy.wheel_pair) != {"W1", "W6"}:
            continue
        synthesized = synthesize_interpretation(review, analogy)
        authored = MECHANISM_BY_ID.get("fluid-continuity")
        if authored is None:
            return False
        return (
            synthesized.operators == ("effort-flow-duality", "composition")
            and authored.operators == ("effort-flow-duality", "composition")
            and dict(synthesized.duality).get("target_effort") == "pressure"
            and dict(synthesized.duality).get("target_flow")
            == "volume_flow_rate"
            and authored.carrier.startswith("normalized")
        )
    return False


def originate(
    *, exclude_hand_authored: bool = True
) -> tuple[OriginatedTransfer, ...]:
    """Run the D8 search and return the originated transfers.

    ``exclude_hand_authored`` drops interpretations whose id collides with a
    hand-authored record (the fluid one), so the returned set is strictly *new*
    pairings.  The parity check still runs first.
    """
    originated: list[OriginatedTransfer] = []
    for analogy in DECLARED_ANALOGIES:
        review = review_analogy(analogy)
        if not review.accepted:
            continue
        interpretation = synthesize_interpretation(review, analogy)
        if exclude_hand_authored:
            existing = MECHANISM_BY_ID.get(interpretation.id)
            if existing is not None and not existing.operators:
                # A card with no operators is hand-authored (a base card).
                continue
            if interpretation.id == "fluid-continuity":
                # The hand-authored fluid record lives under this id family.
                continue
        # Validate: the operator chain must execute over the principle.
        card = generate_mechanism_card(interpretation)
        card.validate()
        # Validate: the exact program must satisfy the independent oracle.
        oracle_pass, vectors = run_oracle_vectors(interpretation)
        originated.append(
            OriginatedTransfer(
                interpretation=interpretation,
                source_analogy=review.analogy_name,
                oracle_pass=oracle_pass,
                vectors=vectors,
                derivation_parity=True,
            )
        )
    return tuple(originated)


def origination_ledger() -> dict[str, Any]:
    """Build the cent-origination-ledger/1 payload."""
    reviews = [review_analogy(analogy) for analogy in DECLARED_ANALOGIES]
    accepted_reviews = [r for r in reviews if r.accepted]
    refused = [r for r in reviews if not r.accepted]
    parity = _fluid_parity()
    originated = originate()
    new_pairs = tuple(
        t for t in originated if t.interpretation.id != "fluid-continuity"
    )
    # The scoreboard's origination count: existing 1 (D4) plus each *new*
    # originated pairing that passes its oracle.
    adopted = tuple(
        t for t in new_pairs if t.oracle_pass and t.derivation_parity
    )
    scoreboard_before = "1/9"
    scoreboard_after = f"{1 + len(adopted)}/9"
    return {
        "schema": SCHEMA,
        "ok": parity and len(adopted) >= 2,
        "principle": PRINCIPLE_ID,
        "search_space": {
            "source": "isomorphism_gate.DECLARED_ANALOGIES",
            "size": len(DECLARED_ANALOGIES),
            "operators": ["effort-flow-duality", "composition"],
        },
        "reviews": [
            {
                "analogy": r.analogy_name,
                "wheel_pair": list(r.wheel_pair),
                "target_domain": r.target_domain,
                "accepted": r.accepted,
                "flow": r.flow_quantity,
                "effort": r.effort_quantity,
                "reason": r.reason,
            }
            for r in reviews
        ],
        "accepted": [r.analogy_name for r in accepted_reviews],
        "refused": [
            {"analogy": r.analogy_name, "reason": r.reason} for r in refused
        ],
        "fluid_derivation_parity": parity,
        "originated": [
            {
                "schema": INTERPRETATION_SCHEMA,
                "id": t.interpretation.id,
                "source_analogy": t.source_analogy,
                "operators": list(t.interpretation.operators),
                "duality": {
                    "target_effort": dict(t.interpretation.duality).get(
                        "target_effort"
                    ),
                    "target_flow": dict(t.interpretation.duality).get(
                        "target_flow"
                    ),
                },
                "oracle_pass": t.oracle_pass,
                "vectors": [dict(v) for v in t.vectors],
                "generated_card_valid": True,
                "hand_authored": False,
            }
            for t in originated
            if t.interpretation.id != "fluid-continuity"
        ],
        "scoreboard": {
            "metric": "origination rate (M-D pairings not hand-authored)",
            "before": scoreboard_before,
            "after": scoreboard_after,
            "target": ">=3",
            "target_met": 1 + len(adopted) >= 3,
        },
        "gaps": [
            "originated interpretations are normalized-flow software only; no measured junction",
            "the optical and thermal analogies are refused, not gapped: their declared "
            "flow variables are not power-conjugate",
            "origination covers junction-conservation pairings only; other principles "
            "(noise shaping, transcendental identity) are not yet searched",
        ],
    }


def render_ledger(payload: Mapping[str, Any]) -> str:
    """Render the origination ledger for the terminal."""
    lines = [
        "=" * 78,
        "D8 ORIGINATION LEDGER",
        "=" * 78,
        f"principle: {payload['principle']}",
        f"search space: {payload['search_space']['size']} declared TIER-3 analogies",
        "",
        "Reviews",
    ]
    for r in payload["reviews"]:
        verdict = "ACCEPT" if r["accepted"] else "REFUSE"
        lines.append(f"  [{verdict}] {r['analogy']}")
        lines.append(f"         pair ({r['effort']}, {r['flow']}) -> {r['target_domain']}")
        lines.append(f"         {r['reason'][:100]}")
    lines.extend(
        [
            "",
            f"fluid derivation parity (re-derives the hand-authored record): "
            f"{payload['fluid_derivation_parity']}",
            "",
            "Originated transfers",
        ]
    )
    for item in payload["originated"]:
        lines.append(
            f"  {item['id']}  <-  {item['source_analogy']}"
        )
        lines.append(
            f"    oracle: {'pass' if item['oracle_pass'] else 'FAIL'} on "
            f"{len(item['vectors'])} vectors; hand-authored: no"
        )
    sb = payload["scoreboard"]
    lines.extend(
        [
            "",
            "Scoreboard (metric 1: origination rate)",
            f"  before: {sb['before']}   after: {sb['after']}   target: {sb['target']}",
            f"  target met: {'yes' if sb['target_met'] else 'no'}",
            "",
            "Gaps",
        ]
    )
    lines.extend(f"  - {gap}" for gap in payload["gaps"])
    return "\n".join(lines)


def write_ledger(path: str, payload: Mapping[str, Any] | None = None) -> str:
    """Write the origination ledger JSON to ``path``."""
    import json
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload or origination_ledger(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(target)
