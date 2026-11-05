#!/usr/bin/env python3
"""Verification suite for the exact core (CentCalculus2).

Runs without pytest: ``python3 tests/test_core.py``.  Every check is a claim
made by a module docstring, so a failure here means the documented behaviour is
not the implemented behaviour.

Groups
------
exact      rational arithmetic, structured errors, JSON round-trip
interval   certified enclosures (sqrt/exp/log/pi) and interval algebra
port       conjugate ports, junctions, gyrator, transformer, dissipation
density    unit-density channel policies
geometry   exact stencils, 2-form curl, boundary conditions
state      transactional evaluation context, deterministic streams
program    static checking: arity, parameters, kinds, cycles
evaluator  tick semantics of the primitives
resolution layered fallback and the strict/diverging outcomes
"""
from __future__ import annotations

import pathlib
import sys
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from cent_compiler.exact import (  # noqa: E402
    CentError,
    ErrorCode,
    clamp,
    div,
    format_q,
    from_float_exact,
    q,
    q_from_json,
    q_to_json,
    wrap_periodic,
)
from cent_compiler.interval import (  # noqa: E402
    Interval,
    exp_q,
    log_q,
    pi_interval,
    sqrt_q,
)
from cent_compiler.port import (  # noqa: E402
    Gyrator,
    PhysicalPort,
    Transformer,
    dissipator,
    ideal_transducer,
    junction_0,
    junction_1,
    require_power_balance,
)
from cent_compiler.density import DensityPolicy, UnitDensity  # noqa: E402
from cent_compiler.geometry import (  # noqa: E402
    BoundaryCondition,
    GridDomain,
    GridField,
    ScalarField,
    TwoForm,
    VectorField,
    curl_2form_at,
    curl_3d,
    divergence_of_curl_3d,
    gradient,
    laplacian_at,
)
from cent_compiler.state import EvalContext, MachineState, SplitMix64  # noqa: E402
from cent_compiler.program import (  # noqa: E402
    Instruction,
    Program,
    analyse,
    coerce_input,
)
from cent_compiler.evaluator import Evaluator, run_program  # noqa: E402
from cent_compiler.resolution import Layer, resolve  # noqa: E402

CHECKS: list[tuple[str, str, object]] = []


def check(group: str, name: str):
    def register(fn):
        CHECKS.append((group, name, fn))
        return fn

    return register


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(code: ErrorCode, fn, message: str = "") -> CentError:
    try:
        fn()
    except CentError as exc:
        expect(
            str(exc.code) == str(code),
            f"{message}: expected {code}, raised {exc.code}",
        )
        return exc
    raise AssertionError(f"{message}: expected {code}, nothing was raised")


def scalar_field(fn, ndim: int = 2) -> ScalarField:
    return ScalarField(fn, ndim, "test")


def run_simple(op: str, inputs, *, params=None, in_kind="numeric", out_kind=None):
    program = Program(
        name=op,
        inputs={"x": in_kind},
        instructions=(Instruction(op, ("x",), "y", params or {}),),
        outputs={"y": "y"},
    )
    return [row["y"] for row in Evaluator(program).run([{"x": v} for v in inputs])]


# ---------------------------------------------------------------------------
# exact
# ---------------------------------------------------------------------------

@check("exact", "decimal strings are exact rationals")
def _():
    expect(q("0.1") == Fraction(1, 10), "0.1 must be exactly 1/10")
    expect(q("1e-3") == Fraction(1, 1000), "exponent form must be exact")
    expect(q("-2.5") == Fraction(-5, 2), "negative decimals must be exact")


@check("exact", "binary floats are rejected on purpose")
def _():
    expect_error(ErrorCode.TYPE_ERROR, lambda: q(0.1), "float input")


@check("exact", "float conversion is lossless for the stored value")
def _():
    expect(
        from_float_exact(0.1) == Fraction(3602879701896397, 36028797018963968),
        "0.1 must convert to its exact stored dyadic value",
    )


@check("exact", "division by zero is a structured error")
def _():
    expect_error(ErrorCode.DIVISION_BY_ZERO, lambda: div(1, 0), "div(1, 0)")


@check("exact", "wrap lands in [0, period)")
def _():
    expect(wrap_periodic(-1, 3) == 2, "wrap(-1, 3) must be 2")
    expect(wrap_periodic(Fraction(7, 2), 1) == Fraction(1, 2), "wrap(3.5, 1) must be 1/2")


@check("exact", "exact values round-trip through JSON")
def _():
    value = Fraction(-22, 7)
    expect(q_from_json(q_to_json(value)) == value, "num/den round-trip")


@check("exact", "formatting and clamping")
def _():
    expect(format_q(Fraction(3, 4)) == "3/4", "format_q")
    expect(format_q(Fraction(5)) == "5", "integers print without a denominator")
    expect(clamp(5, 0, 1) == 1, "clamp high")
    expect_error(ErrorCode.DOMAIN_ERROR, lambda: clamp(0, 2, 1), "unordered clamp bounds")


# ---------------------------------------------------------------------------
# interval
# ---------------------------------------------------------------------------

@check("interval", "sqrt encloses an irrational and certifies its width")
def _():
    enclosure = sqrt_q(2, 64)
    expect(enclosure.contains(enclosure.midpoint), "an enclosure contains its midpoint")
    expect(
        abs(enclosure.midpoint - Fraction("1.414213562373095")) < Fraction(1, 10**12),
        "sqrt(2) must be 1.414213562373095 to 12 places",
    )
    expect(enclosure.width < Fraction(1, 10**12), "sqrt(2) enclosure is too wide")
    expect(enclosure.lo * enclosure.lo <= 2, "lower endpoint must square below 2")
    expect(enclosure.hi * enclosure.hi >= 2, "upper endpoint must square above 2")


@check("interval", "perfect roots are exact point intervals")
def _():
    expect(sqrt_q(4).is_point and sqrt_q(4).lo == 2, "sqrt(4) = 2")
    expect(sqrt_q(Fraction(9, 4)).lo == Fraction(3, 2), "sqrt(9/4) = 3/2")


@check("interval", "exp enclosures")
def _():
    expect(exp_q(0).is_point and exp_q(0).lo == 1, "exp(0) = 1 exactly")
    enclosure = exp_q(1, 64)
    expect(
        abs(enclosure.midpoint - Fraction("2.718281828459045")) < Fraction(1, 10**12),
        "exp(1) must be e to 12 places",
    )
    expect(enclosure.width < Fraction(1, 10**12), "exp(1) enclosure is too wide")


@check("interval", "log enclosures")
def _():
    expect(log_q(1).is_point and log_q(1).lo == 0, "log(1) = 0 exactly")
    enclosure = log_q(2, 64)
    expect(
        abs(enclosure.midpoint - Fraction("0.6931471805599453")) < Fraction(1, 10**12),
        "log(2) must be 0.6931471805599453 to 12 places",
    )
    expect(enclosure.width < Fraction(1, 10**12), "log(2) enclosure is too wide")


@check("interval", "pi from Machin's formula")
def _():
    enclosure = pi_interval(64)
    expect(
        abs(enclosure.midpoint - Fraction("3.14159265358979")) < Fraction(1, 10**12),
        "pi must be 3.14159265358979 to 12 places",
    )
    expect(enclosure.width < Fraction(1, 10**12), "pi enclosure is too wide")


@check("interval", "interval algebra is outward-rounded")
def _():
    a, b = Interval.of(1, 2), Interval.of(3, 4)
    expect((a + b) == Interval.of(4, 6), "addition")
    expect((a * Interval.of(2, 3)) == Interval.of(2, 6), "multiplication")
    expect((-a) == Interval.of(-2, -1), "negation")
    expect(a.pow_int(3) == Interval.of(1, 8), "integer power")
    expect(a.scale(-2) == Interval.of(-4, -2), "negative scaling")


@check("interval", "a divisor straddling zero is refused")
def _():
    expect_error(
        ErrorCode.DIVISION_BY_ZERO,
        lambda: Interval.of(1, 2) / Interval.of(-1, 1),
        "interval containing zero",
    )


# ---------------------------------------------------------------------------
# port
# ---------------------------------------------------------------------------

@check("port", "the gyrator is anti-reciprocal and power conserving")
def _():
    port = PhysicalPort(3, 5)
    out = Gyrator(2).apply(port)
    expect(out == PhysicalPort(10, Fraction(-3, 2)), "gyrator map (e,f) -> (r f, -e/r)")
    expect(port.power + out.power == 0, "gyrator must conserve power exactly")


@check("port", "the transformer conserves power")
def _():
    port = PhysicalPort(3, 5)
    out = Transformer(2).apply(port)
    expect(out == PhysicalPort(Fraction(3, 2), -10), "transformer map")
    expect(port.power + out.power == 0, "transformer must conserve power exactly")


@check("port", "0-junction resolves effort so power sums to zero")
def _():
    out = junction_0([PhysicalPort(1, 2), PhysicalPort(3, 2)])
    expect(out[1] == PhysicalPort(-1, 2), "resolved effort must be -(1)")
    expect(out[0].power + out[1].power == 0, "junction must balance power")


@check("port", "1-junction resolves flow so power sums to zero")
def _():
    out = junction_1([PhysicalPort(2, 1), PhysicalPort(2, 3)])
    expect(out[1] == PhysicalPort(2, -1), "resolved flow must be -(1)")
    expect(out[0].power + out[1].power == 0, "junction must balance power")


@check("port", "junctions refuse inconsistent ports")
def _():
    expect_error(
        ErrorCode.DOMAIN_ERROR,
        lambda: junction_0([PhysicalPort(1, 2), PhysicalPort(3, 3)]),
        "0-junction with mismatched flows",
    )


@check("port", "dissipation produces nonnegative entropy")
def _():
    port, entropy_rate = dissipator(resistance=2, effort=4, temperature=2)
    expect(port == PhysicalPort(4, 2), "f = e/R")
    expect(entropy_rate == 4, "entropy rate = P/T")
    expect_error(
        ErrorCode.DOMAIN_ERROR,
        lambda: dissipator(2, 4, 0),
        "zero temperature",
    )


@check("port", "ideal transducer efficiency accounts for the loss")
def _():
    out, loss = ideal_transducer(2, PhysicalPort(3, 5), 1)
    expect(out == PhysicalPort(6, Fraction(-5, 2)), "ideal transducer map")
    expect(loss == 0, "eta = 1 must conserve power exactly")
    out, loss = ideal_transducer(2, PhysicalPort(3, 5), Fraction(1, 2))
    expect(out.power == Fraction(-15, 2), "half efficiency halves delivered power")
    expect(loss == Fraction(15, 2), "the remainder is the dissipated power")
    require_power_balance([PhysicalPort(1, 1), PhysicalPort(1, -1)])


# ---------------------------------------------------------------------------
# density
# ---------------------------------------------------------------------------

@check("density", "the unit channel has an explicit out-of-range policy")
def _():
    expect_error(ErrorCode.DOMAIN_ERROR, lambda: UnitDensity.of(3), "reject policy")
    expect(UnitDensity.of(3, DensityPolicy.CLAMP).value == 1, "clamp policy")
    expect(UnitDensity.of(3, DensityPolicy.WIDEN).value == 3, "widen policy")


@check("density", "complement is separate from negation")
def _():
    expect(UnitDensity.of(Fraction(1, 4)).complement().value == Fraction(3, 4), "complement")
    expect_error(
        ErrorCode.DOMAIN_ERROR,
        lambda: UnitDensity.of(3, DensityPolicy.WIDEN).complement(),
        "complement outside [0,1]",
    )
    expect(UnitDensity.of(Fraction(5, 4), DensityPolicy.WIDEN).wrap().value == Fraction(1, 4), "wrap to unit")


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

def _quadratic(idx):
    return sum((Fraction(v) ** 2 for v in idx), Fraction(0))


@check("geometry", "central gradient is exact on a quadratic")
def _():
    field = scalar_field(_quadratic)
    values = gradient(field, h=1).at((2, 3))
    expect(values[:2] == (4, 6), f"grad = (2x, 2y) = (4, 6), got {values[:2]}")
    expect(all(v == 0 for v in values[2:]), "unused axes must be identically zero")


@check("geometry", "central Laplacian is exact on a quadratic")
def _():
    expect(laplacian_at(scalar_field(_quadratic), (2, 3), h=1) == 4, "lap(x^2+y^2) = 2*ndim")


@check("geometry", "curl of a gradient is exactly zero")
def _():
    field = scalar_field(_quadratic, ndim=3)
    curl = curl_3d(gradient(field, h=1), h=1)
    expect(
        all(component.at((2, 3, 4)) == 0 for component in curl.components),
        "curl(grad f) must vanish identically for these stencils",
    )


@check("geometry", "divergence of a curl is exactly zero")
def _():
    def component(axis):
        return ScalarField(lambda idx: idx[axis] ** 2 * idx[(axis + 1) % 3], 3, f"v{axis}")

    vector = VectorField(tuple(component(axis) for axis in range(3)))
    expect(divergence_of_curl_3d(vector, (1, 2, 3), h=1) == 0, "div(curl v) must vanish")


@check("geometry", "the 2-form has 276 independent components and is antisymmetric")
def _():
    all_pairs = {
        (i, j): Fraction(1) for i in range(24) for j in range(i + 1, 24)
    }
    form = TwoForm(all_pairs)
    expect(len(form) == 276, f"C(24,2) = 276, got {len(form)}")
    expect(form.get(1, 0) == -form.get(0, 1), "antisymmetry")
    expect(form.get(3, 3) == 0, "the diagonal vanishes")

    def v0(idx):
        return Fraction(idx[1])

    vector = VectorField(tuple(
        [ScalarField(v0, 3, "y")] + [ScalarField(lambda idx: Fraction(0), 3, "0")] * 2
    ))
    omega = curl_2form_at(vector, (0, 0, 0), h=1)
    expect(omega.get(0, 1) == -1, "omega_01 = d0 v1 - d1 v0 = -1")


@check("geometry", "boundary conditions extrapolate as declared")
def _():
    expect(BoundaryCondition("dirichlet", value=5).extrapolate(2, 1) == 5, "Dirichlet")
    expect(BoundaryCondition("neumann").extrapolate(2, 1) == 2, "Neumann mirrors")
    expect(
        BoundaryCondition("robin", value=0, alpha=1, beta=1, gamma=0).extrapolate(2, 1) == 1,
        "Robin: a*psi + b*dpsi/dn = gamma",
    )


@check("geometry", "grid fields apply the boundary condition outside the domain")
def _():
    domain = GridDomain((1, 1), spacing=1, boundary=BoundaryCondition("dirichlet", value=0))
    field = GridField({(0, 0): 1}, domain)
    expect(field.at((0, 0)) == 1, "interior sample")
    expect(field.at((1, 0)) == 0, "Dirichlet face")
    expect(field.at((2, 2)) == 0, "corner composition")


# ---------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------

@check("state", "the pseudo-random stream is deterministic")
def _():
    a, b = SplitMix64(42), SplitMix64(42)
    expect([a.next_u64() for _ in range(5)] == [b.next_u64() for _ in range(5)], "same seed")
    expect(SplitMix64(0).next_u64() != SplitMix64(1).next_u64(), "different seeds")


@check("state", "writes are invisible until commit")
def _():
    state = MachineState(seed=0)
    ctx = EvalContext(state=state)
    ctx.write_slot("node", {"value": 5})
    expect(state.slot("node") == {}, "a failed attempt must not mutate the machine")
    committed = ctx.next_clock(state)
    expect(committed.slot("node") == {"value": 5}, "commit applies the writes")
    expect(committed.clock == 1 and state.clock == 0, "the clock advances only on commit")


# ---------------------------------------------------------------------------
# program
# ---------------------------------------------------------------------------

@check("program", "a valid program is ordered and typed")
def _():
    program = Program(
        "scale_then_accum",
        {"x": "numeric"},
        (
            Instruction("scale", ("x",), "s", {"factor": 2}),
            Instruction("accum", ("s",), "a"),
        ),
        {"out": "a"},
    )
    analysis = analyse(program)
    expect(analysis.kinds["s"] == "numeric", "scale yields a numeric wire")
    expect(analysis.order == (0, 1), "schedule follows the data flow")
    expect(not analysis.has_feedback, "no feedback here")


@check("program", "unknown primitives are rejected")
def _():
    program = Program("bad", {}, (Instruction("teleport", (), "y"),), {})
    expect_error(ErrorCode.UNSUPPORTED, lambda: analyse(program), "unknown primitive")


@check("program", "missing and unknown parameters are rejected")
def _():
    missing = Program("p", {"x": "numeric"}, (Instruction("wrap", ("x",), "y"),), {})
    expect_error(ErrorCode.VALIDATION_ERROR, lambda: analyse(missing), "missing period")
    extra = Program(
        "p", {"x": "numeric"},
        (Instruction("wrap", ("x",), "y", {"period": 1, "colour": "red"}),), {},
    )
    expect_error(ErrorCode.VALIDATION_ERROR, lambda: analyse(extra), "unknown parameter")


@check("program", "wires are single-assignment")
def _():
    program = Program(
        "dupe", {"x": "numeric"},
        (Instruction("neg", ("x",), "y"), Instruction("neg", ("x",), "y")), {},
    )
    expect_error(ErrorCode.VALIDATION_ERROR, lambda: analyse(program), "double assignment")


@check("program", "a combinational cycle is rejected")
def _():
    program = Program(
        "loop", {},
        (Instruction("sum", ("b", "a"), "a"), Instruction("neg", ("a",), "b")), {},
    )
    expect_error(ErrorCode.CYCLE_DETECTED, lambda: analyse(program), "combinational loop")


@check("program", "a feedback edge through a stateful primitive is accepted")
def _():
    program = Program(
        "feedback", {"x": "numeric"},
        (
            Instruction("sum", ("a", "x"), "y"),
            Instruction("accum", ("y",), "a"),
        ),
        {"y": "y"},
    )
    analysis = analyse(program)
    expect(analysis.has_feedback, "the accumulator breaks the cycle")
    expect(analysis.back_edges[0] == frozenset({"a"}), "a is read from the previous tick")


@check("program", "wire kinds are enforced")
def _():
    field = scalar_field(_quadratic)
    program = Program(
        "kind", {"f": "field"},
        (Instruction("sum", ("f", "f"), "y"),), {"y": "y"},
    )
    expect_error(ErrorCode.TYPE_ERROR, lambda: analyse(program), "field into an arithmetic op")
    expect_error(
        ErrorCode.TYPE_ERROR, lambda: coerce_input(field, "numeric"), "field on a numeric wire"
    )


@check("program", "interval wires feed interval-closed numeric primitives")
def _():
    program = Program(
        "mixed", {"x": "numeric"},
        (
            Instruction("exp", ("x",), "e", {"precision": 32}),
            Instruction("sum", ("e", "x"), "y"),
        ),
        {"y": "y"},
    )
    analysis = analyse(program)
    expect(analysis.kinds["e"] == "interval", "exp yields a certified interval")
    result = Evaluator(program).run([{"x": 0}])[0]["y"]
    expect(result == Interval.point(1), "exp(0) + 0 = 1 exactly")


# ---------------------------------------------------------------------------
# evaluator
# ---------------------------------------------------------------------------

@check("evaluator", "accumulate is a running exact sum")
def _():
    expect(run_simple("accum", [1, 2, 3]) == [1, 3, 6], "accum")


@check("evaluator", "rate starts at zero and then differentiates")
def _():
    expect(run_simple("rate", [5, 7, 7], params={"dt": 1}) == [0, 2, 0], "rate")


@check("evaluator", "delay is a per-node ring buffer")
def _():
    expect(
        run_simple("delay", [1, 2, 3, 4], params={"ticks": 2, "initial": 0}) == [0, 0, 1, 2],
        "delay by two ticks",
    )


@check("evaluator", "hysteresis retains state inside the deadband")
def _():
    got = run_simple(
        "hysteresis",
        [Fraction(1, 2), Fraction(3, 2), Fraction(1, 2), Fraction(-1, 2)],
        params={"lower": 0, "upper": 1, "initial": False},
    )
    expect(got == [0, 1, 1, 0], f"latch sequence, got {got}")


@check("evaluator", "noise follows its exact two-point law")
def _():
    program = Program(
        "noise", {},
        (Instruction("noise", (), "n", {"amplitude": Fraction(1, 2), "seed": 7}),),
        {"n": "n"},
    )
    values = [row["n"] for row in Evaluator(program).run([{}] * 512)]
    expect(all(v in {Fraction(1, 2), Fraction(-1, 2)} for v in values), "values are +-a only")
    mean = sum(values, Fraction(0)) / len(values)
    expect(abs(mean) <= Fraction(1, 8), f"mean must be small, got {mean}")
    second = sum((v * v for v in values), Fraction(0)) / len(values)
    expect(second == Fraction(1, 4), "the second moment is exactly a^2")


@check("evaluator", "quantize rounds to the nearest multiple, ties away from zero")
def _():
    got = run_simple(
        "quantize",
        [Fraction(3, 10), Fraction(1, 8), Fraction(-1, 8)],
        params={"quantum": Fraction(1, 4)},
    )
    expect(got == [Fraction(1, 4), Fraction(1, 4), Fraction(-1, 4)], f"quantize, got {got}")


@check("evaluator", "pid includes the current sample in the integral")
def _():
    got = run_simple(
        "pid", [1, 1, 1], params={"kp": 1, "ki": 1, "kd": 0, "dt": 1}
    )
    expect(got == [2, 3, 4], f"pid, got {got}")


@check("evaluator", "state_space advances x' = A x + B u")
def _():
    program = Program(
        "integrator", {"u": "vector"},
        (
            Instruction(
                "state_space", ("u",), "y",
                {
                    "A": [[0, 1], [0, 0]],
                    "B": [[0], [1]],
                    "C": [[1, 0]],
                    "D": [[0]],
                },
            ),
        ),
        {"y": "y"},
    )
    got = [row["y"] for row in Evaluator(program).run([{"u": (Fraction(1),)}] * 5)]
    expect(got == [(0,), (0,), (1,), (1,), (1,)], f"double integrator, got {got}")


@check("evaluator", "translinear is exact when the roots are rational")
def _():
    program = Program(
        "geometric_mean", {"a": "numeric", "b": "numeric"},
        (Instruction("translinear", ("a", "b"), "y", {"exponents": [Fraction(1, 2), Fraction(1, 2)]}),),
        {"y": "y"},
    )
    result = Evaluator(program).run([{"a": 4, "b": 9}])[0]["y"]
    expect(result == 6, f"sqrt(4)*sqrt(9) = 6, got {result}")


@check("evaluator", "delta-sigma tracks a constant input in its bit average")
def _():
    got = run_simple(
        "delta_sigma_modulator",
        [Fraction(3, 10)] * 500,
        params={"order": 1, "threshold": Fraction(1, 2)},
    )
    mean = Fraction(sum(got), len(got))
    expect(abs(mean - Fraction(3, 10)) <= Fraction(1, 25), f"bit average {mean}")


@check("evaluator", "field stencils compose through a program")
def _():
    field = scalar_field(_quadratic)
    program = Program(
        "laplace", {"f": "field"},
        (
            Instruction("grad", ("f",), "g", {"h": 1}),
            Instruction("div_spatial", ("g",), "d", {"h": 1, "index": [2, 3]}),
        ),
        {"d": "d"},
    )
    expect(Evaluator(program).run([{"f": field}])[0]["d"] == 4, "div(grad f) = 4")


@check("evaluator", "conservative ports compose")
def _():
    program = Program(
        "tee", {"p1": "port", "p2": "port"},
        (Instruction("junction_1", ("p1", "p2"), "out"),),
        {"out": "out"},
    )
    result = Evaluator(program).run(
        [{"p1": PhysicalPort(2, 1), "p2": PhysicalPort(2, 3)}]
    )[0]["out"]
    expect(result == PhysicalPort(2, -1), "resolved flow closes the junction")
    expect(PhysicalPort(2, 1).power + result.power == 0, "power balances exactly")


@check("evaluator", "entropy rejects an active port")
def _():
    program = Program(
        "entropy", {"p": "port"},
        (Instruction("entropy", ("p",), "s", {"temperature": 2}),), {"s": "s"},
    )
    expect(
        Evaluator(program).run([{"p": PhysicalPort(4, 2)}])[0]["s"] == 4,
        "P/T = 8/2 = 4",
    )
    expect_error(
        ErrorCode.DOMAIN_ERROR,
        lambda: Evaluator(program).run([{"p": PhysicalPort(4, -2)}]),
        "negative power",
    )


@check("evaluator", "thermoelectric conversion is exact")
def _():
    program = Program(
        "tec", {"e": "port"},
        (
            Instruction(
                "thermo_electric", ("e",), "t",
                {"seebeck": Fraction(1, 1000), "resistance": Fraction(1, 10), "temperature": 300},
            ),
        ),
        {"t": "t"},
    )
    port = Evaluator(program).run([{"e": PhysicalPort(0, 3)}])[0]["t"]
    expect(port.power == Fraction(18, 10), "Peltier + Joule heat = 1.8 W")
    expect(port.effort == 300, "thermal effort is the absolute temperature")


@check("evaluator", "boundary conditions apply through a program")
def _():
    field = ScalarField(lambda idx: Fraction(idx[0]), 1, "x")
    program = Program(
        "bc", {"f": "field"},
        (
            Instruction("boundary", ("f",), "g", {"shape": [1], "kind": "dirichlet", "value": 0}),
            Instruction("spatial", ("g",), "v", {"index": [2]}),
        ),
        {"v": "v"},
    )
    expect(Evaluator(program).run([{"f": field}])[0]["v"] == 0, "Dirichlet face value")


@check("evaluator", "a failed tick leaves the machine untouched")
def _():
    program = Program(
        "fragile", {"x": "numeric"},
        (Instruction("accum", ("x",), "a"), Instruction("wrap", ("a",), "w", {"period": 0})),
        {"w": "w"},
    )
    evaluator = Evaluator(program)
    expect_error(ErrorCode.DOMAIN_ERROR, lambda: evaluator.tick({"x": 1}), "zero period")
    expect(evaluator.state.clock == 0, "the clock must not advance on failure")
    expect(evaluator.state.slot("a") == {}, "no slot may be committed on failure")


@check("evaluator", "run_program is the convenience entry point")
def _():
    program = Program(
        "double", {"x": "numeric"},
        (Instruction("scale", ("x",), "y", {"factor": 2}),), {"y": "y"},
    )
    expect(run_program(program, [{"x": 3}])[0]["y"] == 6, "2 * 3")


# ---------------------------------------------------------------------------
# coverage: every remaining primitive executes as documented
# ---------------------------------------------------------------------------

def _single(op, params, inputs, in_kind="numeric", out="y"):
    program = Program(
        "one", {"x": in_kind},
        (Instruction(op, ("x",), out, params),), {out: out},
    )
    return [row[out] for row in Evaluator(program).run([{"x": v} for v in inputs])]


@check("coverage", "sum, neg, mult and scale compose exactly")
def _():
    program = Program(
        "arith", {"a": "numeric", "b": "numeric"},
        (
            Instruction("mult", ("a", "b"), "p"),
            Instruction("neg", ("p",), "n"),
            Instruction("sum", ("n", "a", "b"), "s"),
            Instruction("scale", ("s",), "y", {"factor": 2}),
        ),
        {"y": "y"},
    )
    got = Evaluator(program).run([{"a": 2, "b": 3}])[0]["y"]
    expect(got == -2, f"(-(2*3) + 2 + 3) * 2 = -2, got {got}")


@check("coverage", "recip, div, sqrt and eq")
def _():
    program = Program(
        "algebra", {"a": "numeric", "b": "numeric"},
        (
            Instruction("div", ("a", "b"), "d"),
            Instruction("recip", ("b",), "r"),
            Instruction("sqrt", ("a",), "q"),
            Instruction("eq", ("d", "r"), "e"),
        ),
        {"d": "d", "r": "r", "q": "q", "e": "e"},
    )
    row = Evaluator(program).run([{"a": 4, "b": 2}])[0]
    expect(row["d"] == 2 and row["r"] == Fraction(1, 2), "4/2 = 2 and 1/2")
    expect(row["q"].is_point and row["q"].lo == 2, "sqrt(4) = 2 exactly")
    expect(row["e"] == 0, "2 is not 1/2")


@check("coverage", "sat and wrap")
def _():
    program = Program(
        "limits", {"x": "numeric"},
        (
            Instruction("sat", ("x",), "c", {"lo": -1, "hi": 1}),
            Instruction("wrap", ("x",), "w", {"period": 1}),
            Instruction("sum", ("c", "w"), "y"),
        ),
        {"y": "y"},
    )
    got = Evaluator(program).run([{"x": 3}])[0]["y"]
    expect(got == 1, f"clamp(3) + wrap(3, 1) = 1 + 0, got {got}")


@check("coverage", "log then exp stays inside a certified enclosure")
def _():
    log_program = Program(
        "log9", {"x": "numeric"},
        (Instruction("log", ("x",), "l"),),
        {"l": "l"},
    )
    value = Evaluator(log_program).run([{"x": 9}])[0]["l"]
    expect(
        abs(value.midpoint - Fraction("2.1972245773362196")) < Fraction(1, 10**6),
        "log(9) enclosure midpoint",
    )

    # Composing enclosures multiplies denominators, so keep the precision low:
    # the point is that the composition stays certified, not that it is tight.
    exp_program = Program(
        "exp_log", {"x": "numeric"},
        (
            Instruction("log", ("x",), "l"),
            Instruction("exp", ("l",), "y", {"precision": 16}),
        ),
        {"y": "y"},
    )
    composed = Evaluator(exp_program).run([{"x": 9}])[0]["y"]
    expect(composed.contains(Fraction(9)), "exp(log 9) must enclose 9")


@check("coverage", "potential store accumulates charge")
def _():
    program = Program(
        "cap", {"f": "numeric"},
        (Instruction("store_pot", ("f",), "p", {"capacitance": 2, "dt": 1}),),
        {"p": "p"},
    )
    rows = Evaluator(program).run([{"f": 1}, {"f": 1}])
    expect(rows[0]["p"] == PhysicalPort(Fraction(1, 2), 1), "q = 1, e = q/C = 1/2")
    expect(rows[1]["p"] == PhysicalPort(1, 1), "q = 2, e = 1")


@check("coverage", "kinetic store accumulates flux")
def _():
    program = Program(
        "ind", {"e": "numeric"},
        (Instruction("store_kin", ("e",), "p", {"inductance": 2, "dt": 1}),),
        {"p": "p"},
    )
    rows = Evaluator(program).run([{"e": 1}, {"e": 1}])
    expect(rows[0]["p"] == PhysicalPort(1, Fraction(1, 2)), "phi = 1, f = phi/L = 1/2")
    expect(rows[1]["p"] == PhysicalPort(1, 1), "phi = 2, f = 1")


@check("coverage", "transducer maps a port")
def _():
    program = Program(
        "tx", {"p": "port"},
        (Instruction("transduce", ("p",), "q", {"ratio": 2, "efficiency": 1}),),
        {"q": "q"},
    )
    out = Evaluator(program).run([{"p": PhysicalPort(3, 5)}])[0]["q"]
    expect(out == PhysicalPort(6, Fraction(-5, 2)), "ratio 2, eta 1")


@check("coverage", "gyrator then transformer")
def _():
    program = Program(
        "two_port", {"p": "port"},
        (
            Instruction("gyrator", ("p",), "g", {"resistance": 2}),
            Instruction("transformer", ("g",), "t", {"ratio": 2}),
        ),
        {"t": "t"},
    )
    out = Evaluator(program).run([{"p": PhysicalPort(3, 5)}])[0]["t"]
    expect(out == PhysicalPort(5, 3), "gyrator (10, -3/2) then /2, *-2")
    expect(out.power == 15, "two documented sign conventions compose")


@check("coverage", "0-junction closes a dissipative branch")
def _():
    program = Program(
        "diss", {"e": "numeric", "p": "port"},
        (
            Instruction("dissipate", ("e",), "d", {"resistance": 2, "temperature": 2}),
            Instruction("junction_0", ("d", "p"), "out"),
        ),
        {"out": "out"},
    )
    out = Evaluator(program).run([{"e": 4, "p": PhysicalPort(3, 2)}])[0]["out"]
    expect(out == PhysicalPort(-4, 2), "resolved effort = -(4)")
    expect(PhysicalPort(4, 2).power + out.power == 0, "the junction balances power")


@check("coverage", "kalman observer converges on a constant measurement")
def _():
    program = Program(
        "kalman", {"z": "numeric"},
        (
            Instruction(
                "kalman_observer", ("z",), "x",
                {
                    "process_variance": Fraction(1, 100),
                    "measurement_variance": 1,
                    "initial_x": 0,
                    "initial_p": 1,
                },
            ),
        ),
        {"x": "x"},
    )
    rows = Evaluator(program).run([{"z": 4}] * 60)
    expect(abs(rows[-1]["x"] - 4) <= Fraction(1, 10), f"estimate {rows[-1]['x']}")


@check("coverage", "PLL integrates the VCO phase")
def _():
    got = _single(
        "phase_locked_loop",
        {"center_frequency": 0, "gain": 1, "dt": 1, "initial_phase": 0},
        [1, 1, 1],
    )
    expect(got == [1, 2, 3], f"phase, got {got}")


@check("coverage", "transmission line delays without reflection")
def _():
    got = _single(
        "transmission_line", {"segments": 2, "reflection": 0, "initial": 0}, [1, 2, 3, 4]
    )
    expect(got == [0, 0, 1, 2], f"line, got {got}")


@check("coverage", "laplacian and curl in a program")
def _():
    field = scalar_field(_quadratic)
    lap = Program(
        "lap", {"f": "field"},
        (Instruction("laplacian", ("f",), "d", {"index": [2, 3], "h": 1}),),
        {"d": "d"},
    )
    expect(Evaluator(lap).run([{"f": field}])[0]["d"] == 4, "lap(x^2 + y^2) = 4")

    zero = ScalarField(lambda idx: Fraction(0), 3, "0")
    vector = VectorField((ScalarField(lambda idx: Fraction(idx[1]), 3, "y"), zero, zero))
    curl_program = Program(
        "curl", {"v": "vector_field"},
        (Instruction("curl", ("v",), "w", {"index": [0, 0, 0], "h": 1}),),
        {"w": "w"},
    )
    form = Evaluator(curl_program).run([{"v": vector}])[0]["w"]
    expect(form.get(0, 1) == -1, "omega_01 = d0 v1 - d1 v0 = -1")


# ---------------------------------------------------------------------------
# resolution
# ---------------------------------------------------------------------------

@check("resolution", "a failing candidate is replaced and the trace is kept")
def _():
    def run(candidate, layer):
        if candidate == "fragile" and layer.name == "parasitic":
            raise CentError(ErrorCode.DOMAIN_ERROR, "finite gain breaks this topology")
        return f"{candidate}@{layer.name}"

    result = resolve(
        ["fragile", "robust"], run, [Layer("ideal"), Layer("parasitic")]
    )
    expect(result.converged, "resolution must converge")
    expect(result.candidate == "robust", "the fallback candidate is selected")
    expect(len(result.failures) == 1, "the failure stays in the trace")
    expect(result.failures[0].error["code"] == "domain_error", "structured error code")


@check("resolution", "strict mode refuses on the first failure")
def _():
    def run(candidate, layer):
        raise CentError(ErrorCode.DOMAIN_ERROR, "no")

    result = resolve(["only"], run, [Layer("ideal")], strict=True)
    expect(result.status == "refused", f"expected refused, got {result.status}")


@check("resolution", "no surviving candidate ends in diverging")
def _():
    def run(candidate, layer):
        raise CentError(ErrorCode.DOMAIN_ERROR, "no")

    result = resolve(["a", "b"], run, [Layer("ideal"), Layer("parasitic")])
    expect(result.status == "diverging", f"expected diverging, got {result.status}")
    expect(len(result.attempts) == 2, "both candidates were tried and recorded")


# ---------------------------------------------------------------------------

def main() -> int:
    failures: list[tuple[str, str, BaseException]] = []
    group = None
    for current_group, name, fn in CHECKS:
        if current_group != group:
            print(f"\n[{current_group}]")
            group = current_group
        try:
            fn()
        except BaseException as exc:  # noqa: BLE001 - the harness reports everything
            failures.append((current_group, name, exc))
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"  PASS  {name}")

    total = len(CHECKS)
    print("\n" + "=" * 78)
    if failures:
        print(f"EXACT CORE: {total - len(failures)}/{total} checks passed, {len(failures)} failed")
        for current_group, name, exc in failures:
            print(f"  - {current_group}: {name}: {exc}")
        return 1
    print(f"EXACT CORE: {total}/{total} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
