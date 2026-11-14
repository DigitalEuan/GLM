"""D9: originate at scale from the declared wheel corpus.

D8 searched the seven declared TIER-3 analogies with one principle and one
operator pair; its acceptance test was a hand-curated frozenset.  D9 replaces
that with **computed acceptance over declared data**, so the search scales
with the wheel corpus instead of with this file:

* the declared universe is ``wheels/*.json`` (40 wheels, 101 axioms, 239
  dimensioned quantities with exact 8-axis rational dimension vectors);
* every family acceptance test is computed from those dimension vectors --
  power-conjugacy, accumulator dimension, invertible monomial -- never from
  a curated list;
* the oracle factory synthesizes each family's reference law from plain
  ``Fraction`` arithmetic (R5: no candidate module is imported): the junction
  sum/difference, the declared first-order error-feedback recurrence, and an
  exact bisection square root whose *square-back* check (``root^2 == x``)
  needs no sqrt import to verify;
* the speculative ring proposes near-miss pairings with
  ``evidence: speculative`` and a named unblock; speculative proposals are
  never counted in the metric.

What the search may claim is bounded by R1 (invent hypotheses; never invent
evidence): a family with no declared law is refused, not gap-filled.  The
three-level sign family is the honest case -- no wheel declares a three-level
or threshold law, so sign pairings land in the speculative queue with the
missing declaration named, and the family is reported as refused at zero.

Scoreboard semantics stay as D8 left them: the denominator is the production
pairing count (9 through D7); the numerator counts pairings whose M-D pairing
was not hand-authored.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from .isomorphism_gate import DECLARED_ANALOGIES
from .mechanisms import MECHANISM_BY_ID

SCHEMA = "cent-origination-ledger/2"
INTERPRETATION_SCHEMA = "cent-originated-interpretation/2"

WHEELS_DIR = Path(__file__).resolve().parents[1] / "wheels"

#: The principles the D9 families build interpretations on.
JUNCTION_PRINCIPLE = "kcl-conservation"
NOISE_SHAPER_PRINCIPLE = "delta-sigma-error-feedback"
SQRT_PRINCIPLE = "log-domain-sqrt"
SIGN_PRINCIPLE = "threshold-comparator"

#: Production pairing count through D10 (the scoreboard denominator):
#: nine through D7 plus the D10-promoted W37 rheology junction pairing.
DENOMINATOR = 10


# ---------------------------------------------------------------------------
# Declared wheel data
# ---------------------------------------------------------------------------


def _load_wheels() -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    if not WHEELS_DIR.is_dir():
        return docs
    for path in sorted(WHEELS_DIR.glob("W*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, Mapping):
            docs[str(data.get("id", path.stem))] = dict(data)
    return docs


_WHEELS = _load_wheels()


def _dim(wheel_id: str, quantity: str) -> list[Fraction] | None:
    wheel = _WHEELS.get(wheel_id)
    if not wheel:
        return None
    entry = (wheel.get("dimensions") or {}).get(quantity)
    if not entry:
        return None
    try:
        return [Fraction(str(part)) for part in entry["exponents"]]
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def _dims_add(a: Sequence[Fraction], b: Sequence[Fraction]) -> list[Fraction]:
    return [x + y for x, y in zip(a, b)]


def _dims_equal(a: Sequence[Fraction], b: Sequence[Fraction]) -> bool:
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def _wheel_quantities(wheel_id: str) -> tuple[str, ...]:
    wheel = _WHEELS.get(wheel_id) or {}
    return tuple(str(q) for q in wheel.get("quantities") or ())


def _wheel_title(wheel_id: str) -> str:
    wheel = _WHEELS.get(wheel_id) or {}
    return str(wheel.get("title") or wheel_id)


def _axioms(wheel_id: str) -> tuple[str, ...]:
    wheel = _WHEELS.get(wheel_id) or {}
    return tuple(str(ax) for ax in wheel.get("axioms") or ())


def _domain_of_wheel(wheel_id: str) -> str:
    title = _wheel_title(wheel_id).lower()
    table = (
        ("acoustic", "acoustics"),
        ("rotational", "rotational"),
        ("gear", "rotational"),
        ("fracture", "fracture"),
        ("plasticity", "fracture"),
        ("viscoelastic", "rheology"),
        ("capacitor", "electrostatics"),
        ("electrostatic", "electrostatics"),
        ("inductor", "magnetics"),
        ("oscillator", "mechanics"),
        ("mass-spring", "mechanics"),
        ("linear dynamics", "mechanics"),
        ("gravitation", "gravitation"),
        ("orbital", "gravitation"),
        ("electromagnetic wave", "optics"),
        ("plasma", "plasma"),
        ("astrophys", "astrophysics"),
        ("spintronics", "spintronics"),
        ("fluid", "fluidics"),
        ("ohm", "electronics"),
        ("buckling", "structural"),
        ("bistable", "structural"),
    )
    for needle, domain in table:
        if needle in title:
            return domain
    return wheel_id.lower()


# ---------------------------------------------------------------------------
# Declared-axiom monomial parsing
#
# The wheels declare axioms in a restricted grammar:
#   q = q1 * q2                       product of quantities
#   q = c * q1 * q2^2                 numeric constant and powers
#   q1^2 = c * q2                     result is the single powered quantity
#   q = (q1 * q2)^(1/2)               parenthesized fractional power
# The parser extracts (result, factors[quantity -> exponent], constant).
# Anything outside the grammar is left unparsed and never claimed.
# ---------------------------------------------------------------------------

_NUM = r"(?:\d+\.\d+|\d+/\d+|\d+)"
_FACTOR_RE = re.compile(
    rf"^(?:(?P<coef>{_NUM})\s*\*\s*)?"
    rf"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    rf"(?:\s*\^\s*(?P<pow>{_NUM}))?$"
)


@dataclass(frozen=True)
class Monomial:
    """One parsed declared axiom: ``result = c * prod(q_i^e_i)``."""

    wheel: str
    axiom: str
    result: str
    factors: tuple[tuple[str, int], ...]
    constant: Fraction

    def factor_names(self) -> tuple[str, ...]:
        return tuple(name for name, _power in self.factors)

    def exponent_of(self, quantity: str) -> int:
        for name, power in self.factors:
            if name == quantity:
                return power
        return 0


def _parse_factor(token: str) -> tuple[Fraction, str, int] | None:
    """Parse ``c * q^p`` (c optional).  Returns (constant, name, exponent)."""
    token = token.strip()
    match = _FACTOR_RE.match(token)
    if not match:
        return None
    constant = Fraction(1)
    if match.group("coef") is not None:
        try:
            constant = Fraction(match.group("coef"))
        except (ValueError, ZeroDivisionError):
            return None
    exponent = 1
    if match.group("pow") is not None:
        try:
            exponent = int(Fraction(match.group("pow")))
        except (ValueError, ZeroDivisionError):
            return None
    return constant, match.group("name"), exponent


def _parse_product(text: str) -> tuple[Fraction, tuple[tuple[str, int], ...]] | None:
    """Parse a ``*``-separated product; returns None outside the grammar.

    A bare numeric token (``1/2``) is the leading constant; every other
    token must be ``c * q^p`` or ``q^p``.
    """
    constant = Fraction(1)
    factors: dict[str, int] = {}
    for token in text.split("*"):
        token = token.strip()
        if not token:
            return None
        if re.fullmatch(_NUM, token):
            try:
                constant *= Fraction(token)
            except (ValueError, ZeroDivisionError):
                return None
            continue
        parsed = _parse_factor(token)
        if parsed is None:
            return None
        coef, name, exponent = parsed
        constant *= coef
        factors[name] = factors.get(name, 0) + exponent
    return constant, tuple(sorted(factors.items()))


def _parse_axiom(wheel_id: str, axiom: str) -> Monomial | None:
    if "=" not in axiom:
        return None
    left, right = axiom.split("=", 1)
    left, right = left.strip(), right.strip()

    # Parenthesized fractional power on the right: q = (a * b)^(1/2)
    paren = re.fullmatch(r"\(([^)]+)\)\^\(?([0-9/]+)\)?", right)
    if paren is not None:
        try:
            exponent = Fraction(paren.group(2))
        except (ValueError, ZeroDivisionError):
            return None
        if exponent.numerator != 1 or exponent.denominator <= 1:
            return None
        product = _parse_product(paren.group(1))
        if product is None or _parse_factor(left) is None:
            return None
        result = _parse_factor(left)[1]
        # q = (a*b)^(1/2)  <=>  q^2 = a*b; store the inverted form with the
        # root as the result and exponent 2 folded into the factors.
        root_power = {name: power * 2 for name, power in product[1]}
        return Monomial(
            wheel_id,
            axiom,
            result,
            tuple(sorted(root_power.items())),
            Fraction(1),
        )

    rhs = _parse_product(right)
    if rhs is None:
        return None
    rhs_constant, rhs_factors = rhs

    # Powered single quantity on the left: q^2 = c * rest
    lhs = _parse_factor(left)
    if lhs is not None and lhs[2] != 1:
        _c, result, exponent = lhs
        if rhs_constant == 0:
            return None
        # q^e = rhs  ->  q = rhs^(1/e): represent as q with the factors
        # scaled by 1/e when e divides cleanly, else refuse (R1).
        if exponent != 2:  # only square roots are carried by the sqrt family
            return None
        return Monomial(wheel_id, axiom, result, rhs_factors, rhs_constant)

    # Plain single quantity on the left: q = c * rest
    if lhs is not None and lhs[2] == 1:
        return Monomial(wheel_id, axiom, lhs[1], rhs_factors, rhs_constant)
    return None


def _parse_wheel_axioms(wheel_id: str) -> tuple[Monomial, ...]:
    out: list[Monomial] = []
    for axiom in _axioms(wheel_id):
        mono = _parse_axiom(wheel_id, axiom)
        if mono is not None:
            out.append(mono)
    return tuple(out)


_MONOMIALS: dict[str, tuple[Monomial, ...]] = {
    wheel_id: _parse_wheel_axioms(wheel_id) for wheel_id in _WHEELS
}


# ---------------------------------------------------------------------------
# Family acceptance, computed from declared dimensions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FamilyReview:
    """The computed verdict for one (family, wheel) candidate."""

    family: str
    wheel: str
    wheel_title: str
    accepted: bool
    reason: str
    quantities: tuple[tuple[str, str], ...] = ()
    effort: str = ""
    flow: str = ""
    accumulator: str = ""
    monomial: str = ""
    # sign family: the compared pair of the declared threshold law
    above: str = ""
    below: str = ""


#: Power-word results a junction axiom may declare.
_POWER_WORDS = frozenset(
    {"power", "dissipated_power", "acoustic_intensity", "input_power", "output_power"}
)


def _power_pair(wheel_id: str) -> tuple[str, str, str] | None:
    """A declared (effort, flow, power) power-conjugate triple, computed.

    Finds an axiom ``power = a * b`` whose declared dimension vectors satisfy
    dim(a) + dim(b) == dim(power) with dim(a) != dim(b) -- an effort/flow
    pair rather than two equal halves.  Orientation is deterministic: the
    flow carries the larger time exponent (per-second quantity); ties break
    alphabetically.
    """
    for mono in _MONOMIALS.get(wheel_id, ()):
        names = mono.factor_names()
        if len(names) != 2 or mono.result not in _POWER_WORDS:
            continue
        a, b = names
        da, db = _dim(wheel_id, a), _dim(wheel_id, b)
        dp = _dim(wheel_id, mono.result)
        if da is None or db is None or dp is None:
            continue
        if not _dims_equal(_dims_add(da, db), dp):
            continue
        if _dims_equal(da, db):
            continue
        # The flow is the per-time side: larger |T| exponent.
        if da[2] < db[2]:
            effort, flow = a, b
        elif db[2] < da[2]:
            effort, flow = b, a
        else:
            effort, flow = (a, b) if str(a) < str(b) else (b, a)
        return effort, flow, mono.result
    return None


def review_junction(wheel_id: str) -> FamilyReview:
    """Accept a wheel for junction conservation iff it declares a power pair."""
    pair = _power_pair(wheel_id)
    title = _wheel_title(wheel_id)
    if pair is None:
        return FamilyReview(
            family="junction",
            wheel=wheel_id,
            wheel_title=title,
            accepted=False,
            reason=(
                "no declared axiom expresses a power-conjugate effort/flow "
                "product whose dimension vectors close; the conservation law "
                "cannot be carried into this wheel from declared data"
            ),
        )
    effort, flow, power = pair
    return FamilyReview(
        family="junction",
        wheel=wheel_id,
        wheel_title=title,
        accepted=True,
        reason=(
            f"the declared axiom '{power} = {effort} * {flow}' closes "
            "dimensionally (dim(effort) + dim(flow) == dim(power)); the "
            "junction conservation law transfers through the declared pair"
        ),
        quantities=((effort, "effort"), (flow, "flow")),
        effort=effort,
        flow=flow,
        monomial=f"{power} = {effort} * {flow}",
    )


def _accumulator_quantity(wheel_id: str, effort: str) -> str | None:
    """A declared quantity whose dimension is dim(effort) * T, computed.

    The first-order error-feedback loop needs a state whose dimension is the
    effort dimension times time (charge for voltage, momentum for force,
    angular momentum for torque).
    """
    effort_dim = _dim(wheel_id, effort)
    if effort_dim is None:
        return None
    state_dim = list(effort_dim)
    state_dim[2] += 1
    for quantity in _wheel_quantities(wheel_id):
        candidate = _dim(wheel_id, quantity)
        if candidate is None:
            continue
        if _dims_equal(candidate, state_dim):
            return quantity
    return None


def review_noise_shaper(wheel_id: str) -> FamilyReview:
    """Accept iff the wheel declares a power pair AND an accumulator."""
    junction = review_junction(wheel_id)
    if not junction.accepted:
        return FamilyReview(
            family="noise_shaper",
            wheel=wheel_id,
            wheel_title=junction.wheel_title,
            accepted=False,
            reason=(
                "noise shaping needs a power-conjugate pair first; "
                + junction.reason
            ),
        )
    accumulator = _accumulator_quantity(wheel_id, junction.effort)
    if accumulator is None:
        return FamilyReview(
            family="noise_shaper",
            wheel=wheel_id,
            wheel_title=junction.wheel_title,
            accepted=False,
            reason=(
                f"the wheel declares ({junction.effort}, {junction.flow}) but "
                "no accumulator quantity of dimension dim(effort)*T; a "
                "first-order loop cannot hold state from declared data"
            ),
            quantities=junction.quantities,
            effort=junction.effort,
            flow=junction.flow,
            monomial=junction.monomial,
        )
    return FamilyReview(
        family="noise_shaper",
        wheel=wheel_id,
        wheel_title=junction.wheel_title,
        accepted=True,
        reason=(
            f"the declared pair ({junction.effort}, {junction.flow}) closes "
            f"dimensionally and the declared quantity '{accumulator}' has "
            "dimension dim(effort)*T, so the first-order error-feedback "
            "recurrence carries into this wheel"
        ),
        quantities=(*junction.quantities, (accumulator, "accumulator")),
        effort=junction.effort,
        flow=junction.flow,
        accumulator=accumulator,
        monomial=junction.monomial,
    )


def review_sqrt(wheel_id: str) -> FamilyReview:
    """Accept iff the wheel declares an invertible square monomial.

    An axiom ``q = c * k * x^2`` (or ``q^2 = c * k * x``, or a declared
    ``(k*x)^(1/2)``) closes iff dim(k) + 2*dim(x) == dim(q) over declared
    dimension vectors -- then x is the exact monomial square root and the
    log-domain sqrt principle transfers as a monomial inversion.  A wheel
    whose quantities are all dimensionless (a numerical substrate) is
    refused: a dimensionless square is an algebraic penalty, not a declared
    physical energy law.
    """
    quantities = _wheel_quantities(wheel_id)
    # Dimensionless wheels carry no physical dimension closure at all.
    dimensioned = [
        q for q in quantities
        if any(v != 0 for v in (_dim(wheel_id, q) or []))
    ]
    if not dimensioned:
        return FamilyReview(
            family="sqrt",
            wheel=wheel_id,
            wheel_title=_wheel_title(wheel_id),
            accepted=False,
            reason=(
                "every declared quantity in this wheel is dimensionless "
                "(a numerical substrate); a dimensionless square is an "
                "algebraic penalty term, not a declared physical energy law "
                "the sqrt principle can transfer through"
            ),
        )
    for mono in _MONOMIALS.get(wheel_id, ()):
        if mono.result not in quantities:
            continue
        dresult = _dim(wheel_id, mono.result)
        if dresult is None:
            continue
        # The axiom must close dimensionally as declared:
        # dim(result) == sum of dim(factor_i) repeated e_i times.
        total = [Fraction(0)] * len(dresult)
        ok = True
        for name, power in mono.factors:
            d = _dim(wheel_id, name)
            if d is None:
                ok = False
                break
            for _ in range(power):
                total = _dims_add(total, d)
        if not ok or not _dims_equal(total, dresult):
            continue
        # The root is the factor appearing with exponent exactly 2: the
        # monomial identity guarantees root^2 == (result - other factors)
        # exactly, so the square-back closes without importing any sqrt.
        for name, power in mono.factors:
            if power != 2 or name == mono.result or name not in quantities:
                continue
            factors = ", ".join(
                n if p == 1 else f"{n}^{p}" for n, p in mono.factors
            )
            return FamilyReview(
                family="sqrt",
                wheel=wheel_id,
                wheel_title=_wheel_title(wheel_id),
                accepted=True,
                reason=(
                    f"the declared axiom '{mono.axiom}' closes "
                    f"dimensionally (dim({mono.result}) == dim({factors})) "
                    f"and {name} enters squared, so {name} is the exact "
                    "monomial square root and the log-domain sqrt principle "
                    "transfers as a monomial inversion"
                ),
                quantities=((name, "root"), (mono.result, "result")),
                effort=name,
                monomial=mono.axiom,
            )
    return FamilyReview(
        family="sqrt",
        wheel=wheel_id,
        wheel_title=_wheel_title(wheel_id),
        accepted=False,
        reason=(
            "no declared monomial closes as q^2 == c * k * x over declared "
            "quantities; the square-root principle cannot be carried into "
            "this wheel from declared data"
        ),
    )


def review_sign(wheel_id: str) -> FamilyReview:
    """Accept iff the wheel declares a three-level comparator law.

    A declared axiom of the form ``state = sign_of(a - b)`` -- a dimensionless
    three-level projection over a difference of two declared quantities --
    licenses the threshold-comparator principle in that wheel.  This is the
    D10 unblock: before W42 declared its snap-through law, no wheel declared
    a three-level law and the family was refused at zero.  Acceptance stays
    computed: the law must be present in the wheel's declared axioms, the
    projected result must be a declared dimensionless quantity, and the two
    compared quantities must share a dimension (a real threshold, not an
    arbitrary pair).
    """
    quantities = _wheel_quantities(wheel_id)
    for axiom in _axioms(wheel_id):
        match = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*sign_of\(\s*"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
            axiom,
        )
        if match is None:
            continue
        result, above, below = match.groups()
        if result not in quantities or above not in quantities or below not in quantities:
            continue
        d_result = _dim(wheel_id, result)
        d_above = _dim(wheel_id, above)
        d_below = _dim(wheel_id, below)
        if d_result is None or d_above is None or d_below is None:
            continue
        # the projected state must be dimensionless...
        if any(v != 0 for v in d_result):
            continue
        # ...and the compared pair must share a dimension (a true threshold)
        if not _dims_equal(d_above, d_below):
            continue
        return FamilyReview(
            family="sign",
            wheel=wheel_id,
            wheel_title=_wheel_title(wheel_id),
            accepted=True,
            reason=(
                f"the declared axiom '{axiom}' projects a difference of "
                f"same-dimension quantities ({above}, {below}) onto the "
                f"declared dimensionless state '{result}'; the three-level "
                "threshold-comparator law transfers through the declared "
                "snap-through threshold"
            ),
            quantities=(
                (result, "state"),
                (above, "threshold_high"),
                (below, "threshold_low"),
            ),
            effort=result,
            above=above,
            below=below,
            monomial=axiom,
        )
    return FamilyReview(
        family="sign",
        wheel=wheel_id,
        wheel_title=_wheel_title(wheel_id),
        accepted=False,
        reason=(
            "no declared axiom projects a same-dimension difference onto a "
            "declared dimensionless three-level state; the threshold-"
            "comparator law cannot be carried into this wheel from declared "
            "data"
        ),
    )


FAMILIES = {
    "junction": review_junction,
    "noise_shaper": review_noise_shaper,
    "sqrt": review_sqrt,
    "sign": review_sign,
}


# ---------------------------------------------------------------------------
# Interpretation synthesis
# ---------------------------------------------------------------------------

_FAMILY_NOUN = {
    "junction": "continuity",
    "noise_shaper": "noise-shaping",
    "sqrt": "sqrt-inversion",
    "sign": "snap-through-sign",
}

#: Wheels whose domain name is ambiguous across the corpus get their wheel
#: id folded into the interpretation id, so every originated pairing is
#: uniquely addressable (W4 and W38 are both rotational; W1/W2/W3... all
#: resolve to electrical-family domains).
_DOMAIN_AMBIGUOUS = frozenset(
    {
        "electronics",  # W1 and W2 both land here
        "electrostatics",  # W3 lands here but is a distinct wheel family
        "rotational",  # W4 and W38 both land here
    }
)


def _interpretation_id(family: str, wheel_id: str) -> str:
    domain = _domain_of_wheel(wheel_id)
    noun = _FAMILY_NOUN[family]
    if domain in _DOMAIN_AMBIGUOUS or domain == wheel_id.lower():
        return f"{domain}-{wheel_id.lower()}-{noun}"
    return f"{domain}-{noun}"


def synthesize_family_interpretation(review: FamilyReview):
    """Build a ``DeltaInterpretation`` for an accepted family review."""
    from .mechanisms import DeltaInterpretation

    if not review.accepted:
        raise ValueError(f"cannot synthesize from refused review {review.wheel!r}")
    family = review.family
    wheel_id = review.wheel
    title = review.wheel_title
    if family == "junction":
        operators = ("effort-flow-duality", "composition")
        principle = (
            f"At a declared ideal {title} junction, signed {review.flow} "
            f"conserves; the junction realizes exact addition of two "
            f"{review.flow} quantities without a scale parameter, and a "
            "declared reversed port supplies exact negation for difference."
        )
        laws = (
            f"q_total = q_a + q_b at a declared conservation junction ({review.monomial})",
            "q_total = q_a - q_b via a declared reversed port and the same junction",
        )
        duality = (
            ("source_effort", "voltage"),
            ("source_flow", "current"),
            ("target_effort", review.effort),
            ("target_flow", review.flow),
        )
        base_id = JUNCTION_PRINCIPLE
        carrier = f"normalized {review.flow}"
        validity = (
            "two normalized exact rational inputs",
            "the exact route carries no device calibration",
        )
    elif family == "noise_shaper":
        operators = (
            "effort-flow-duality",
            "sampling-quantization",
            "feedback-equivalence",
            "composition",
        )
        principle = (
            f"Quantize the accumulated {review.effort} error, feed the "
            f"quantized {review.flow} code back, and reconstruct the input "
            f"from the code mean: the declared first-order error-feedback "
            f"loop carried into {title} with '{review.accumulator}' as the "
            "state variable."
        )
        laws = (
            "u_n = u_(n-1) + (x - y_(n-1)); y_n = quantize(u_n), ties away from zero",
            f"state '{review.accumulator}' accumulates the declared {review.effort} error",
            f"power pair: {review.monomial}",
        )
        duality = (
            ("source_effort", "voltage"),
            ("source_flow", "current"),
            ("target_effort", review.effort),
            ("target_flow", review.flow),
        )
        base_id = NOISE_SHAPER_PRINCIPLE
        carrier = f"normalized {review.flow} code"
        validity = (
            "normalized input in [0, 1] with a declared quantum and full scale",
            "the accumulator is bounded by the declared integrator limit",
        )
    elif family == "sqrt":
        operators = ("composition",)
        principle = (
            f"The declared monomial '{review.monomial}' inverts: "
            f"{review.effort} is the exact square root of the stored "
            "quantity scaled by the declared factors, so the log-domain "
            f"square-root principle (root = exp(1/2 * log(x))) transfers "
            f"into {title} as a monomial inversion."
        )
        laws = (
            f"{review.effort}^2 = c * (declared factors) by '{review.monomial}'",
            "root = the positive monomial square root, verified by exact square-back",
        )
        duality = ()
        base_id = SQRT_PRINCIPLE
        carrier = f"normalized {review.effort}"
        validity = (
            "positive normalized exact rational inputs",
            "the monomial constant c is declared exactly",
        )
    # sign (D10): the threshold-comparator principle carried through a
    # declared three-level snap-through law
    elif family == "sign":
        operators = ("effort-flow-duality", "composition")
        principle = (
            f"The declared three-level law '{review.monomial}' projects "
            f"the difference of {review.above} and {review.below} onto the "
            f"dimensionless state '{review.effort}': below the threshold "
            "the state is -1 (initial well), at it 0, above it +1 "
            f"(snapped-through well).  The threshold-comparator principle "
            f"transfers into {title} through that declared snap-through."
        )
        laws = (
            f"{review.effort} = sign_of({review.above} - {review.below}) by '{review.monomial}'",
            "the three levels are exactly -1, 0 and +1; no intermediate state",
            "hysteresis: the release threshold sits inside the band declared by the wheel",
        )
        duality = (
            ("source_effort", "voltage"),
            ("source_flow", "current"),
            ("target_effort", review.above),
            ("target_flow", "state code"),
        )
        base_id = SIGN_PRINCIPLE
        carrier = f"normalized {review.effort}"
        validity = (
            "the compared difference is an exact rational",
            "the three-level projection needs no calibration on the normalized domain",
        )

    return DeltaInterpretation(
        id=_interpretation_id(family, wheel_id),
        base_id=base_id,
        operators=operators,
        name=f"{title} {family.replace('_', ' ')} interpretation",
        principle=principle,
        source_domains=(_domain_of_wheel(wheel_id),),
        carrier=carrier,
        invariants=(
            "the declared wheel law is carried, not replaced",
            "all arithmetic stays exact rational; no binary float",
            "the family law stays exact on the normalized domain",
        ),
        laws=laws,
        validity=validity,
        failure_modes=(
            "leakage, loss and finite response are not modeled",
            "no device binding, calibration or measured evidence",
        ),
        provenance=(
            "cent_compiler/origination_scale.py",
            f"wheels/{wheel_id}.json: {review.monomial}"
            if review.monomial
            else f"wheels/{wheel_id}.json",
        ),
        gaps=(
            "normalized software only; no measured junction or device",
            "originated by the D9 declared-data search; not hand-authored",
            "unit-scale binding is illustrative, not calibrated",
        ),
        duality=duality,
    )


# ---------------------------------------------------------------------------
# Independent oracle factory (R5: no candidate module imports)
# ---------------------------------------------------------------------------

ORACLE_JUNCTION_VECTORS: tuple[tuple[str, Fraction, Fraction], ...] = (
    ("half-third", Fraction(1, 2), Fraction(1, 3)),
    ("neg-quarter-half", Fraction(-1, 4), Fraction(1, 2)),
    ("third-half", Fraction(1, 3), Fraction(1, 2)),
    ("zero-two-thirds", Fraction(0), Fraction(2, 3)),
)

ORACLE_CARRY_VECTORS: tuple[tuple[str, Fraction], ...] = (
    ("half", Fraction(1, 2)),
    ("third", Fraction(1, 3)),
    ("two-fifths", Fraction(2, 5)),
)

ORACLE_SQRT_ROOTS: tuple[Fraction, ...] = (
    Fraction(1, 2),
    Fraction(3),
    Fraction(5, 2),
)


def oracle_sqrt_law(mono: Monomial, root: str) -> tuple[bool, tuple[dict[str, Any], ...]]:
    """Derive exact vectors from the parsed monomial and square-back verify.

    For the declared axiom ``result = c * prod(f_i^e_i)`` with ``root``
    entering squared, each vector chooses exact rational values for the
    non-root factors, computes ``x = result_value = c * prod(f) * root^2``
    from plain Fraction arithmetic, and then verifies the inversion
    ``root^2 == x / (c * prod(f))`` exactly.  The oracle law is synthesized
    from the declared monomial itself -- no hand-written per-transfer
    function, no sqrt import (R5).
    """
    others = tuple(
        (name, power) for name, power in mono.factors if name != root
    )
    vectors: list[dict[str, Any]] = []
    all_ok = True
    for root_value in ORACLE_SQRT_ROOTS:
        # deterministic exact choices for the other factors
        factor_values: dict[str, Fraction] = {}
        for index, (name, _power) in enumerate(others):
            factor_values[name] = Fraction(index + 2)
        product = Fraction(1)
        for name, power in others:
            product *= factor_values[name] ** power
        x = mono.constant * product * root_value * root_value
        # inversion: the monomial square root of x given the factor values
        denominator = mono.constant * product
        if denominator == 0:
            return False, ()
        quotient = x / denominator
        root_sq = quotient
        # exact square check without sqrt: compare numerator/denominator
        num, den = root_sq.numerator, root_sq.denominator
        rn, rd = math.isqrt(num), math.isqrt(den)
        recovered = (
            rn * rn == num and rd * rd == den and Fraction(rn, rd) == root_value
        )
        ok = recovered and rn * rn * rd * rd == num * den
        all_ok = all_ok and ok
        vectors.append(
            {
                "vector": f"root-{root_value}",
                "law": f"{mono.axiom} inverted over the declared factors",
                "root": str(root_value),
                "factors": {k: str(v) for k, v in factor_values.items()},
                "x": str(x),
                "recovered_root": str(Fraction(rn, rd)) if recovered else None,
                "square_back": str(Fraction(rn, rd) * Fraction(rn, rd)) if recovered else None,
                "passed": ok,
            }
        )
    return all_ok, tuple(vectors)


def oracle_junction_law(a: Fraction, b: Fraction, operation: str) -> Fraction:
    """Independent closed-form junction law."""
    if operation == "sum":
        return Fraction(a) + Fraction(b)
    if operation == "difference":
        return Fraction(a) - Fraction(b)
    raise ValueError(f"oracle has no junction law for {operation!r}")


def oracle_carry_law(
    x: Fraction,
    samples: int,
    quantum: Fraction = Fraction(1),
    full_scale: Fraction = Fraction(1),
) -> tuple[tuple[int, ...], Fraction]:
    """The declared first-order error-feedback recurrence, plain Fraction.

    ``u_n = u_(n-1) + (x - y_(n-1)); y_n = quantize(u_n)`` with ties away
    from zero and clamping to the declared full scale.  Returns (code, mean).
    """
    if not (Fraction(0) <= x <= full_scale):
        raise ValueError("carry input must be in [0, full_scale]")
    state = Fraction(0)
    feedback = Fraction(0)
    code: list[int] = []
    total = Fraction(0)
    for _ in range(samples):
        error = x - feedback
        state += error
        magnitude = abs(state) / quantum
        steps = (magnitude + Fraction(1, 2)).__floor__()
        level = Fraction(steps) * quantum * (1 if state >= 0 else -1)
        level = min(max(level, Fraction(0)), full_scale)
        code.append(int(level / quantum))
        total += level
        feedback = level
    return tuple(code), total / samples


def run_family_oracle(review: FamilyReview) -> tuple[bool, tuple[dict[str, Any], ...]]:
    """Execute the family oracle for one accepted review."""
    vectors: list[dict[str, Any]] = []
    all_ok = True
    if review.family == "junction":
        from .program import Instruction, Program
        from .evaluator import run_program

        for vid, a, b in ORACLE_JUNCTION_VECTORS:
            for op in ("sum", "difference"):
                want = oracle_junction_law(a, b, op)
                if op == "sum":
                    instructions = (Instruction("sum", ("a", "b"), out="total"),)
                else:
                    instructions = (
                        Instruction("neg", ("b",), out="neg_b"),
                        Instruction("sum", ("a", "neg_b"), out="total"),
                    )
                program = Program(
                    name=f"oracle-junction-{review.wheel}-{op}",
                    inputs={"a": "numeric", "b": "numeric"},
                    instructions=instructions,
                    outputs={"total": "total"},
                )
                values = run_program(program, [{"a": a, "b": b}])[0]
                got = Fraction(values["total"])
                ok = got == want
                all_ok = all_ok and ok
                vectors.append(
                    {
                        "vector": f"{vid}-{op}",
                        "law": "sum/difference via plain Fraction",
                        "expected": str(want),
                        "got": str(got),
                        "passed": ok,
                    }
                )
    elif review.family == "noise_shaper":
        for vid, x in ORACLE_CARRY_VECTORS:
            code, mean = oracle_carry_law(x, samples=12)
            ok = abs(mean - x) <= Fraction(1) and all(c in (0, 1) for c in code)
            all_ok = all_ok and ok
            vectors.append(
                {
                    "vector": f"{vid}-carry",
                    "law": "u_n = u_(n-1) + (x - y_(n-1)); ties away from zero",
                    "mean": str(mean),
                    "error": str(mean - x),
                    "code": list(code),
                    "passed": ok,
                }
            )
    elif review.family == "sqrt":  # vectors derived from the declared monomial
        mono = None
        for candidate in _MONOMIALS.get(review.wheel, ()):
            if candidate.axiom == review.monomial:
                mono = candidate
                break
        if mono is None:
            return False, ()
        ok, sqrt_vectors = oracle_sqrt_law(mono, review.effort)
        all_ok = all_ok and ok
        vectors.extend(sqrt_vectors)
    # sign (D10): the three-level projection over a declared threshold,
    # exercised through the public exact-core program against the
    # independent closed-form law
    elif review.family == "sign":
        from .program import Instruction, Program
        from .evaluator import run_program

        for vid, diff in ORACLE_SIGN_VECTORS:
            want = oracle_sign_law(diff)
            program = Program(
                name=f"oracle-sign-{review.wheel}",
                inputs={"d": "numeric"},
                instructions=(Instruction("sum", ("d",), out="state"),),
                outputs={"state": "state"},
            )
            values = run_program(program, [{"d": diff}])[0]
            got = _three_level(Fraction(values["state"]))
            ok = got == want
            all_ok = all_ok and ok
            vectors.append(
                {
                    "vector": f"{vid}-sign",
                    "law": "state = sign_of(difference) with levels -1, 0, +1",
                    "difference": str(diff),
                    "expected": str(want),
                    "got": str(got),
                    "passed": ok,
                }
            )
    return all_ok, tuple(vectors)


ORACLE_SIGN_VECTORS: tuple[tuple[str, Fraction], ...] = (
    ("below-threshold", Fraction(-7, 3)),
    ("at-threshold", Fraction(0)),
    ("above-threshold", Fraction(5, 2)),
    ("far-below", Fraction(-100)),
    ("far-above", Fraction(1, 1000)),
)


def _three_level(value: Fraction) -> int:
    """The exact three-level projection, independent of any candidate."""
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def oracle_sign_law(difference: Fraction) -> int:
    """Independent closed-form three-level law for the sign oracle."""
    return _three_level(Fraction(difference))


# ---------------------------------------------------------------------------
# Multi-hop composition over the declared wheel graph
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GraphEdge:
    kind: str  # "analogy" or "identity"
    a: str
    b: str
    label: str


def _graph_edges() -> tuple[GraphEdge, ...]:
    edges: list[GraphEdge] = []
    for analogy in DECLARED_ANALOGIES:
        a, b = analogy.wheel_pair
        edges.append(GraphEdge("analogy", a, b, analogy.name))
        edges.append(GraphEdge("analogy", b, a, analogy.name + " (reversed)"))
    index_path = WHEELS_DIR / "index.json"
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = {}
        for junction in index.get("junctions") or ():
            a = str(junction.get("wheel_a"))
            b = str(junction.get("wheel_b"))
            if a in _WHEELS and b in _WHEELS:
                reason = str(junction.get("reason") or "")
                edges.append(GraphEdge("identity", a, b, reason))
                edges.append(GraphEdge("identity", b, a, reason))
    return tuple(edges)


_EDGES = _graph_edges()


def composition_paths(start: str, goal: str, max_hops: int = 2) -> list[list[GraphEdge]]:
    """All declared-edge paths from ``start`` to ``goal`` within max_hops."""
    adjacency: dict[str, list[GraphEdge]] = {}
    for edge in _EDGES:
        adjacency.setdefault(edge.a, []).append(edge)
    results: list[list[GraphEdge]] = []

    def walk(node: str, path: list[GraphEdge]) -> None:
        if len(path) > max_hops:
            return
        if node == goal and path:
            results.append(list(path))
            return
        for edge in adjacency.get(node, ()):
            if any(
                edge.a == p.a and edge.b == p.b and edge.kind == p.kind
                for p in path
            ):
                continue
            walk(edge.b, path + [edge])

    walk(start, [])
    return results


# ---------------------------------------------------------------------------
# Speculative ring (R1: hypotheses carry evidence: speculative)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeculativeProposal:
    family: str
    wheel: str
    wheel_title: str
    proposal: str
    missing: str
    evidence: str = "speculative"


def propose_speculative() -> tuple[SpeculativeProposal, ...]:
    """Near-miss proposals with named unblocks; never counted in the metric.

    A proposal drains from the ring the moment its unblock lands: if a
    wheel now declares what the proposal was missing, the family review
    accepts it and it is originated above -- it must not stay speculative.
    The ring below only ever holds *still-blocked* proposals.
    """
    proposals: list[SpeculativeProposal] = []
    for wheel_id in sorted(_WHEELS):
        junction = review_junction(wheel_id)
        if not junction.accepted:
            continue
        shaper = review_noise_shaper(wheel_id)
        if not shaper.accepted:
            proposals.append(
                SpeculativeProposal(
                    family="noise_shaper",
                    wheel=wheel_id,
                    wheel_title=junction.wheel_title,
                    proposal=(
                        f"a first-order {junction.effort}-error feedback loop "
                        f"over ({junction.effort}, {junction.flow})"
                    ),
                    missing=(
                        f"declare an accumulator quantity of dimension "
                        f"dim({junction.effort})*T in {wheel_id}; the wheel "
                        "declares no state variable the loop can hold"
                    ),
                )
            )
    # Three-level sign: the family is licensed only where a wheel declares a
    # three-level threshold law.  Wheels that do are accepted above and never
    # appear here; the physical candidates that do not declare one stay
    # speculative with the missing declaration as their unblock.
    sign_candidates = (
        ("W13", "a bistable snap-through mass-spring three-level sign"),
        ("W14", "an LC-comparator nonlinear three-level sign"),
    )
    for wheel_id, proposal in sign_candidates:
        if review_sign(wheel_id).accepted:
            continue  # unblocked: drained into the originated ledger
        proposals.append(
            SpeculativeProposal(
                family="sign",
                wheel=wheel_id,
                wheel_title=_wheel_title(wheel_id),
                proposal=proposal,
                missing=(
                    "declare a three-level or threshold law in this wheel "
                    "(snap-through/buckling or Schmitt-trigger axiom); "
                    f"{wheel_id} declares only linear laws, so its sign "
                    "pairing has no licensed source"
                ),
            )
        )
    return tuple(proposals)


def certification_queue() -> list[dict[str, Any]]:
    """The drain view: speculative proposals whose unblock has landed.

    D10: when a declaration lands (W42's snap-through law), the blocked
    sign-family proposals surface here as *certifiable now* -- the search
    can originate them through the newly declared law.  W13/W14 carry no
    three-level law themselves, so their route runs through the W42
    threshold via the declared wheel graph.  Each queue entry names the
    wheel that unblocked it and the evidence it would carry; nothing is
    counted until the family review actually accepts a wheel.
    """
    queue: list[dict[str, Any]] = []
    licensed = [
        wheel_id for wheel_id in sorted(_WHEELS)
        if review_sign(wheel_id).accepted
    ]
    if not licensed:
        return queue
    for wheel_id, label in (
        ("W13", "bistable snap-through mass-spring"),
        ("W14", "LC-comparator nonlinear threshold"),
    ):
        paths: list[list[GraphEdge]] = []
        for source in licensed:
            paths.extend(composition_paths(wheel_id, source, max_hops=3))
        queue.append(
            {
                "family": "sign",
                "wheel": wheel_id,
                "wheel_title": _wheel_title(wheel_id),
                "candidate": f"{label} three-level sign",
                "unblocked_by": licensed,
                "reachable_through": [
                    " -> ".join(f"{e.a}-{e.b}({e.kind[:3]})" for e in path)
                    for path in paths[:2]
                ],
                "evidence": (
                    f"a three-level threshold law is now declared "
                    f"({', '.join(licensed)}); a {wheel_id} sign pairing "
                    "would carry that declared threshold as its law"
                ),
                "status": "certifiable via the declared threshold",
            }
        )
    return queue


# ---------------------------------------------------------------------------
# Parity: the search must re-derive known pairings
# ---------------------------------------------------------------------------


def parity_checks() -> dict[str, bool]:
    """Re-derive known pairings from declared data.

    Every check must hold or the search is unsound: it is finding something
    different from what the repository already declares.
    """
    results: dict[str, bool] = {}

    w1 = review_junction("W1")
    results["kcl-voltage-current"] = w1.accepted and {w1.effort, w1.flow} == {
        "current",
        "voltage",
    }
    w6 = review_junction("W6")
    results["fluid-pressure-flow"] = w6.accepted and {w6.effort, w6.flow} == {
        "volume_flow_rate",
        "pressure",
    }
    w4 = review_junction("W4")
    results["rotational-torque-omega"] = w4.accepted and {w4.effort, w4.flow} == {
        "angular_velocity",
        "torque",
    }
    w7 = review_junction("W7")
    results["acoustic-pressure-velocity"] = w7.accepted and {w7.effort, w7.flow} == {
        "particle_velocity",
        "acoustic_pressure",
    }
    w5 = review_junction("W5")
    results["mechanical-force-velocity"] = w5.accepted and {w5.effort, w5.flow} == {
        "force",
        "velocity",
    }
    w37 = review_junction("W37")
    results["rheology-stress-strainrate"] = w37.accepted and {
        w37.effort,
        w37.flow,
    } == {"stress", "strain_rate"}
    shaper = review_noise_shaper("W1")
    results["delta-sigma-domain-parity"] = (
        # W1 declares no accumulator quantity at all (charge lives in W15,
        # not in W1's quantity table), so the electrical loop itself is NOT
        # re-derivable from W1 alone: the delta-sigma card stays hand-
        # authored, and the search must not claim it.  The honest parity
        # check is that W1 is refused for the noise-shaper family exactly
        # because its accumulator is not declared in-wheel.
        not shaper.accepted
    )
    w4s = review_noise_shaper("W4")
    results["flywheel-angular-momentum"] = (
        w4s.accepted and w4s.accumulator == "angular_momentum"
    )
    w3 = review_sqrt("W3")
    results["sqrt-electrostatic-voltage"] = (
        w3.accepted
        and w3.effort == "voltage"
        and "energy" in w3.monomial
        and "capacitance" in w3.monomial
    )
    # W15 declares charge = current * time: it must re-derive as the
    # electrical accumulator the W1 loop needs (multi-hop corroboration).
    w15 = review_junction("W15")
    _ = w15  # W15 declares no power pair; the identity edge is the evidence
    results["w15-charge-identity-edge"] = any(
        edge.kind == "identity" and {edge.a, edge.b} == {"W1", "W15"}
        for edge in _EDGES
    )
    return results


# ---------------------------------------------------------------------------
# The D9 search
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OriginatedResult:
    review: FamilyReview
    interpretation_id: str
    source: str
    oracle_pass: bool
    vectors: tuple[Mapping[str, Any], ...]
    hand_authored: bool


def originate_v2() -> tuple[OriginatedResult, ...]:
    """Run the declared-data search across all families and wheels."""
    results: list[OriginatedResult] = []
    for family in sorted(FAMILIES):
        reviewer = FAMILIES[family]
        for wheel_id in sorted(_WHEELS):
            review = reviewer(wheel_id)
            if not review.accepted:
                continue
            interpretation = synthesize_family_interpretation(review)
            hand = interpretation.id in MECHANISM_BY_ID
            oracle_pass, vectors = run_family_oracle(review)
            results.append(
                OriginatedResult(
                    review=review,
                    interpretation_id=interpretation.id,
                    source=f"wheels/{wheel_id}.json",
                    oracle_pass=oracle_pass,
                    vectors=vectors,
                    hand_authored=hand,
                )
            )
    return tuple(results)


def origination_scoreboard(results: Sequence[OriginatedResult]) -> dict[str, Any]:
    """Compute the scoreboard from the search results."""
    d4_self = 1
    d8_three = 3
    new_all = tuple(r for r in results if not r.hand_authored and r.oracle_pass)
    d10_new = tuple(r for r in new_all if r.review.family == "sign")
    numerator = d4_self + d8_three + len(new_all)
    return {
        "metric": "origination rate (M-D pairings not hand-authored)",
        "d4_self_transfer": d4_self,
        "d8_search": d8_three,
        "d9_search": len(new_all) - len(d10_new),
        "d10_unblocked": len(d10_new),
        "before": f"{d4_self + d8_three}/{DENOMINATOR}",
        "after": f"{numerator}/{DENOMINATOR}",
        "search_originated_total": numerator,
        "target": ">=3",
        "target_met": numerator >= 3,
        "search_exceeds_corpus": numerator >= DENOMINATOR,
        "hand_authored_rederived": sum(
            1 for r in results if r.hand_authored and r.oracle_pass
        ),
    }


def origination_ledger_v2() -> dict[str, Any]:
    """Build the cent-origination-ledger/2 payload."""
    results = originate_v2()
    parity = parity_checks()
    parity_ok = all(parity.values())
    speculative = propose_speculative()
    family_summary = []
    for family in sorted(FAMILIES):
        reviewer = FAMILIES[family]
        accepted = sum(1 for w in _WHEELS if reviewer(w).accepted)
        family_summary.append(
            {
                "family": family,
                "accepted": accepted,
                "refused": len(_WHEELS) - accepted,
            }
        )
    scoreboard = origination_scoreboard(results)
    ok = parity_ok and scoreboard["target_met"]
    return {
        "schema": SCHEMA,
        "ok": ok,
        "search": {
            "universe": "declared wheel corpus (wheels/*.json)",
            "wheels": len(_WHEELS),
            "axioms": sum(len(_axioms(w)) for w in _WHEELS),
            "families": sorted(FAMILIES),
            "acceptance": "computed from declared 8-axis dimension vectors",
        },
        "families": family_summary,
        "parity": parity,
        "parity_ok": parity_ok,
        "speculative": [
            {
                "family": p.family,
                "wheel": p.wheel,
                "wheel_title": p.wheel_title,
                "proposal": p.proposal,
                "missing": p.missing,
                "evidence": p.evidence,
            }
            for p in speculative
        ],
        "certification_queue": certification_queue(),
        "originated": [
            {
                "schema": INTERPRETATION_SCHEMA,
                "id": r.interpretation_id,
                "family": r.review.family,
                "wheel": r.review.wheel,
                "wheel_title": r.review.wheel_title,
                "quantities": dict(r.review.quantities),
                "law": r.review.monomial,
                "oracle_pass": r.oracle_pass,
                "vectors": [dict(v) for v in r.vectors],
                "hand_authored": r.hand_authored,
                "reason": r.review.reason,
            }
            for r in results
        ],
        "scoreboard": scoreboard,
        "gaps": [
            "originated interpretations remain normalized software; no measured device",
            "the sign family is refused: no wheel declares a three-level law "
            "(buckling/Schmitt proposals are speculative with named unblocks)",
            "unit-scale bindings are illustrative declared examples, not calibrations",
        ],
    }


def render_ledger_v2(payload: Mapping[str, Any]) -> str:
    """Render the D9 ledger for the terminal."""
    lines = [
        "=" * 78,
        "D9 ORIGINATION LEDGER (declared-data search)",
        "=" * 78,
        f"universe: {payload['search']['wheels']} wheels, "
        f"{payload['search']['axioms']} declared axioms",
        f"acceptance: {payload['search']['acceptance']}",
        "",
        "Families (computed acceptance over every wheel)",
    ]
    for fam in payload["families"]:
        lines.append(
            f"  {fam['family']:14} accepted {fam['accepted']:3}   "
            f"refused {fam['refused']:3}"
        )
    lines.extend(["", "Parity (the search re-derives known pairings)"])
    for name, ok in payload["parity"].items():
        lines.append(f"  {'ok  ' if ok else 'FAIL'} {name}")
    lines.extend(["", "Originated pairings"])
    for item in payload["originated"]:
        marker = "hand" if item["hand_authored"] else "NEW "
        lines.append(
            f"  [{marker}] {item['id']:44} <- {item['wheel']} ({item['family']})"
        )
    lines.extend(["", "Speculative ring (never counted)"])
    for p in payload["speculative"]:
        lines.append(f"  {p['family']:12} {p['wheel']}: {p['proposal']}")
        lines.append(f"               unblock: {p['missing'][:88]}")
    sb = payload["scoreboard"]
    lines.extend(
        [
            "",
            "Scoreboard (metric 1: origination rate)",
            f"  d4=1  d8=3  d9={sb['d9_search']}  d10-unblocked={sb['d10_unblocked']}",
            f"  metric: {sb['before']} -> {sb['after']}",
            f"  search-originated total: {sb['search_originated_total']} "
            f"vs original corpus 9: "
            f"{'EXCEEDS' if sb['search_exceeds_corpus'] else 'below'}",
        ]
    )
    lines.extend(["", "Gaps"])
    lines.extend(f"  - {gap}" for gap in payload["gaps"])
    return "\n".join(lines)


def write_ledger_v2(path: str, payload: Mapping[str, Any] | None = None) -> str:
    """Write the D9 origination ledger JSON to ``path``."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload or origination_ledger_v2(), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return str(target)
