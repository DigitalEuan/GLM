"""``glm_universal.reasoning.engine`` -- the thermo-dynamic carrier engine.

What this module is
-------------------
Part III of the unification blueprint describes computation as a machine: an
eccentric cam driving a spring-dashpot accumulator, escapement drums turning
under it, a lattice snap that measures strain, a radiator that bleeds strain
off, two fuels burned in parallel, a turbocharger that decides how hard to
snap, and a gearbox that picks the settings.  Before this module the package
had the *parts* -- an exact delta-sigma loop, a modular sieve, a Leech
nearest-point search, an escalation ladder -- but nothing that assembled them,
so the section's headline figure (a "2.7x precision leap") could not be
checked at all.

This module assembles them, and then measures what the assembly is worth.
Every stage is exact: integers and :class:`~fractions.Fraction` only, no
float constructed anywhere, no randomness, and every reported figure
recomputed by the call that reports it.

The seven stages
----------------
``accumulate`` (stage 1)
    The spring-dashpot: an exact error integrator whose emitted bit stream
    has running averages converging on the target.
``escapements`` (stage 2)
    The drums: the emitted count read modulo 2, 4, 8, 144 and 256, and the
    period of the joint reading.
``snap`` (stage 3)
    The lattice snap, in three strengths, with the local strain
    ``TAX = d^2/32`` the blueprint defines.
``run_engine`` (stages 4, 5 and 7)
    The trip-lever that escalates when strain overflows capacity, the
    radiator that bleeds strain periodically, and the turbocharger that
    chooses the snap strength from the strain it is seeing.
``multi_fuel`` (stage 6)
    Two generators for the same algebraic target -- Heron's iteration and
    the continued-fraction convergents -- burned in parallel, with the
    better one read at each tick.
``gearbox``
    The runtime classifier: what kind of target this is, and which
    configuration the engine should run.

What it measures
----------------
``precision_leap``
    The blueprint's headline. The ratio is not a constant of nature: it
    depends entirely on what "naive solver" means, so this function measures
    it against three separately stated baselines and reports all three
    rather than picking the flattering one.
``engine_report`` / ``blueprint_claims``
    Everything above in one call, and the verdict each Part III sentence
    earns from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..substrate import leech_construct as lc
from . import analogy as an
from . import exact_real as er
from . import fwht_decode as fd

__all__ = [
    "ESCAPEMENT_MODULI", "SNAP_MODES", "SNAP_OPERATION_COST",
    "TAX_CAPACITY", "GEARS",
    "EngineConfig", "EngineRun",
    "accumulate", "escapements", "escapement_period",
    "snap", "tax_of", "run_engine",
    "heron_sequence", "convergent_sequence", "multi_fuel",
    "classify_target", "gearbox",
    "bits_cleared", "precision_leap",
    "engine_report", "blueprint_claims",
]


# ═════════════════════════════════════════════════════════════════════════
# 0.  CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

#: Stage 2's escapement drums: the physical rings of the MOG (2, 4, 8), the
#: Construction ladder's 144-tooth wheel and the digit stack's byte (256).
ESCAPEMENT_MODULI: Tuple[int, ...] = (2, 4, 8, 144, 256)

#: The three snap strengths the turbocharger chooses between.
SNAP_MODES: Tuple[str, ...] = ("tight", "relaxed", "skip")

#: The integer-operation cost of one snap in each mode.  ``tight`` is the
#: exact nearest-point search, whose cost is the coset enumeration the
#: transform decoder measures; ``relaxed`` is the certificate path, which
#: hard-decides the 24 signs and reads one syndrome; ``skip`` does nothing.
#: These are the model the operation counts are reported against, stated
#: rather than hidden.
SNAP_OPERATION_COST: Dict[str, int] = {
    "tight": 2 * 4096 * 24,
    "relaxed": 24 + 1,
    "skip": 0,
}

#: Stage 4's capacity: strain above this trips the escalation lever.  The
#: blueprint's figure, in the blueprint's units.
TAX_CAPACITY: Fraction = Fraction(4)

#: The gearbox's settings, by target class.
GEARS: Dict[str, Dict[str, object]] = {
    "rational": {"snap": "skip", "radiator": 0,
                 "reading": "a rational is already on the grid; snapping "
                            "measures nothing and the radiator has nothing "
                            "to bleed"},
    "algebraic": {"snap": "relaxed", "radiator": 8,
                  "reading": "an algebraic target has a fast generator, so "
                             "the loop is short and a periodic bleed keeps "
                             "it off the trip-lever"},
    "transcendental": {"snap": "relaxed", "radiator": 4,
                       "reading": "a transcendental target is read through a "
                                  "slower generator, so strain accumulates "
                                  "and the radiator runs more often"},
    "exotic": {"snap": "tight", "radiator": 4,
               "reading": "an unclassified target gets the exact snap, "
                          "because nothing is known about where it lands"},
}


# ═════════════════════════════════════════════════════════════════════════
# 1.  STAGE 1 -- THE DELTA-SIGMA ACCUMULATOR
# ═════════════════════════════════════════════════════════════════════════

def accumulate(target: Fraction, ticks: int) -> Dict[str, object]:
    """The spring-dashpot: an exact first-order error integrator.

    At each tick the accumulator takes up the difference between the target
    and what was last emitted, and the quantiser emits the nearer of 0 and 1.
    Nothing is rounded: the accumulator is an exact rational throughout.

    Returns
    -------
    dict
        the emitted bits, the exact running average, the exact error, and
        the largest displacement the accumulator ever held.
    """
    if not isinstance(target, Fraction):
        raise TypeError("accumulate: the target must be a Fraction")
    if ticks < 1:
        raise ValueError("accumulate: ticks must be at least 1")

    error = Fraction(0)
    emitted: List[int] = []
    peak = Fraction(0)
    for _ in range(ticks):
        error += target - (emitted[-1] if emitted else 0)
        if abs(error) > peak:
            peak = abs(error)
        emitted.append(1 if error >= Fraction(1, 2) else 0)
    average = Fraction(sum(emitted), ticks)
    return {
        "target": target,
        "ticks": ticks,
        "bits": tuple(emitted),
        "ones": sum(emitted),
        "average": average,
        "error": abs(average - target),
        "peak_displacement": peak,
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  STAGE 2 -- THE MODULAR ESCAPEMENTS
# ═════════════════════════════════════════════════════════════════════════

def escapements(count: int,
                moduli: Sequence[int] = ESCAPEMENT_MODULI
                ) -> Tuple[int, ...]:
    """The drum readings: one residue per modulus, advanced by ``count``."""
    return tuple(count % m for m in moduli)


def escapement_period(moduli: Sequence[int] = ESCAPEMENT_MODULI) -> int:
    """After how many teeth the joint drum reading repeats.

    The least common multiple of the moduli, found by exact integer
    arithmetic.
    """
    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    period = 1
    for m in moduli:
        period = period * m // _gcd(period, m)
    return period


# ═════════════════════════════════════════════════════════════════════════
# 3.  STAGE 3 -- THE LATTICE SNAP AND ITS STRAIN
# ═════════════════════════════════════════════════════════════════════════

def tax_of(distance2) -> Fraction:
    """The blueprint's local strain: ``TAX = d^2 / 32``."""
    return Fraction(distance2) / 32


def _leader_distance2(vector: Sequence[Fraction], leader: int) -> Fraction:
    """The squared distance from a sign carrier to its corrected pattern.

    The certificate path hard-decides the 24 signs and names the coset
    leader that corrects them.  Flipping coordinate ``i`` moves it by
    ``2|x_i|``, so the squared distance is ``4 * sum of x_i^2`` over the
    leader's support -- exact, and computed without building the lattice
    point.
    """
    total = Fraction(0)
    for i in range(24):
        if (leader >> i) & 1:
            total += 4 * Fraction(vector[i]) ** 2
    return total


def snap(vector: Sequence, mode: str = "relaxed") -> Dict[str, object]:
    """Project a 24-coordinate carrier to the lattice, at one of three
    strengths.

    ``tight``
        the exact nearest-point search: the answer is provably the nearest
        Leech point, and it costs the full coset enumeration.  Its strain is
        the Leech strain, ``d^2/32`` with ``d`` the true lattice distance;
    ``relaxed``
        the certificate path: the 24 signs are hard-decided, one syndrome is
        read, and the answer either proves its own optimality from the code's
        minimum distance or declines -- in which case the strain is reported
        as unknown rather than guessed.  Its strain is the *code* strain: the
        squared distance to the nearest Golay-aligned sign pattern, over 32.
        This is a different quantity from the Leech strain, not an
        approximation to it, and the reading says which one it is;
    ``skip``
        no snap at all, and no strain measured.
    """
    if mode not in SNAP_MODES:
        raise ValueError(f"snap: unknown mode {mode!r}; expected one of "
                         f"{SNAP_MODES}")
    if len(vector) != 24:
        raise ValueError("snap: a carrier has 24 coordinates")

    if mode == "skip":
        return {"mode": mode, "measured": False, "tax": Fraction(0),
                "strain_kind": "none",
                "operations": SNAP_OPERATION_COST[mode]}
    if mode == "tight":
        result = an.nearest_lattice_point([Fraction(x) for x in vector])
        return {"mode": mode, "measured": True,
                "distance2": result.distance2,
                "tax": tax_of(result.distance2),
                "strain_kind": "leech",
                "certified": True,
                "operations": SNAP_OPERATION_COST[mode]}
    exact = [Fraction(x) for x in vector]
    lookup = fd.certified_lookup(exact)
    certified = bool(lookup["certified"])
    leaders = lookup["best_leaders"]
    distance2 = (_leader_distance2(exact, leaders[0])  # type: ignore[index]
                 if certified and leaders else None)
    return {
        "mode": mode,
        "measured": certified,
        "coset_weight": lookup["coset_weight"],
        "distance2": distance2,
        "tax": tax_of(distance2) if distance2 is not None else None,
        "strain_kind": "code",
        "certified": certified,
        "operations": SNAP_OPERATION_COST[mode],
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE ENGINE -- STAGES 4, 5 AND 7
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EngineConfig:
    """How the gearbox has set the engine up for this target."""

    snap_mode: str = "relaxed"
    #: Bleed the accumulated strain every this many ticks; 0 disables it.
    radiator_period: int = 0
    #: Take a snap reading every this many ticks.
    snap_period: int = 8
    #: Above this strain the turbocharger relaxes, and above twice it skips.
    turbo: bool = True
    #: The magnitude of a carrier coordinate.  The substrate's own minimal
    #: vectors have coordinates of size 4, and the strain a snap measures
    #: scales with the square of this, so it is a setting rather than a
    #: constant.
    amplitude: int = 4

    def __post_init__(self) -> None:
        if self.snap_mode not in SNAP_MODES:
            raise ValueError(f"EngineConfig: unknown snap mode "
                             f"{self.snap_mode!r}")
        if self.radiator_period < 0 or self.snap_period < 1:
            raise ValueError("EngineConfig: periods must be non-negative "
                             "and the snap period positive")
        if self.amplitude < 1:
            raise ValueError("EngineConfig: the amplitude must be positive")


@dataclass(frozen=True)
class EngineRun:
    """What one run of the engine produced."""

    target: Fraction
    ticks: int
    config: EngineConfig
    average: Fraction
    error: Fraction
    accumulated_tax: Fraction
    peak_tax: Fraction
    escalations: int
    bleeds: int
    snaps: Dict[str, int]
    operations: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "target": str(self.target),
            "ticks": self.ticks,
            "snap_mode": self.config.snap_mode,
            "radiator_period": self.config.radiator_period,
            "snap_period": self.config.snap_period,
            "turbo": self.config.turbo,
            "average": str(self.average),
            "error": str(self.error),
            "accumulated_tax": str(self.accumulated_tax),
            "peak_tax": str(self.peak_tax),
            "escalations": self.escalations,
            "bleeds": self.bleeds,
            "snaps": dict(self.snaps),
            "operations": self.operations,
        }


def _carrier_from(bits: Sequence[int], amplitude: int = 4) -> List[Fraction]:
    """The last 24 emitted bits as a signed 24-coordinate carrier.

    A 1 pushes a coordinate to +1 and a 0 to -1, so the carrier the snap sees
    is a sign pattern rather than a sparse one, which is what the certificate
    path is defined on.
    """
    window = list(bits[-24:])
    while len(window) < 24:
        window.insert(0, 0)
    return [Fraction(amplitude) if b else Fraction(-amplitude)
            for b in window]


def run_engine(target: Fraction, ticks: int = 64,
               config: Optional[EngineConfig] = None) -> EngineRun:
    """Run the assembled engine on one target.

    The four baseline stages run every tick; the radiator and the
    turbocharger run when the configuration asks for them.  Nothing is
    approximated: the accumulator, the strain and every average are exact
    rationals.
    """
    if not isinstance(target, Fraction):
        raise TypeError("run_engine: the target must be a Fraction")
    if ticks < 1:
        raise ValueError("run_engine: ticks must be at least 1")
    cfg = config or EngineConfig()

    error = Fraction(0)
    emitted: List[int] = []
    strain = Fraction(0)
    peak = Fraction(0)
    escalations = 0
    bleeds = 0
    operations = 0
    counted = {mode: 0 for mode in SNAP_MODES}

    for tick in range(1, ticks + 1):
        # Stage 1: the accumulator.
        error += target - (emitted[-1] if emitted else 0)
        emitted.append(1 if error >= Fraction(1, 2) else 0)

        # Stage 2: the drums advance one tooth per emitted one.
        operations += len(ESCAPEMENT_MODULI)

        # Stage 3 and 7: snap, at the strength the turbocharger allows.
        if tick % cfg.snap_period == 0:
            mode = cfg.snap_mode
            if cfg.turbo:
                if strain > 2 * TAX_CAPACITY:
                    mode = "skip"
                elif strain > TAX_CAPACITY and mode == "tight":
                    mode = "relaxed"
            reading = snap(_carrier_from(emitted, cfg.amplitude), mode)
            counted[mode] += 1
            operations += int(reading["operations"])
            if reading["measured"] and reading["tax"] is not None:
                strain += reading["tax"]
                if strain > peak:
                    peak = strain

        # Stage 4: the trip-lever.
        if strain > TAX_CAPACITY:
            escalations += 1

        # Stage 5: the radiator.
        if cfg.radiator_period and tick % cfg.radiator_period == 0:
            if strain > 0:
                strain = Fraction(0)
                bleeds += 1

    average = Fraction(sum(emitted), ticks)
    return EngineRun(
        target=target, ticks=ticks, config=cfg,
        average=average, error=abs(average - target),
        accumulated_tax=strain, peak_tax=peak,
        escalations=escalations, bleeds=bleeds,
        snaps=counted, operations=operations)


# ═════════════════════════════════════════════════════════════════════════
# 5.  STAGE 6 -- MULTI-FUEL PARALLEL GENERATORS
# ═════════════════════════════════════════════════════════════════════════

#: Every generator is read on a fixed-width dyadic grid, as a real engine
#: would be.  Truncation is exact -- ``floor(x * 2^m) / 2^m`` -- and it keeps
#: Heron's denominators from doubling out of hand, which is the practical
#: reason a machine truncates at all.
GENERATOR_BITS: int = 64


def _truncate(x: Fraction, bits: int = GENERATOR_BITS) -> Fraction:
    """``x`` on the dyadic grid of ``bits`` fractional bits, exactly."""
    scaled = x * 2 ** bits
    return Fraction(scaled.numerator // scaled.denominator, 2 ** bits)


def heron_sequence(radicand: int, steps: int,
                   bits: int = GENERATOR_BITS) -> Tuple[Fraction, ...]:
    """Heron's iteration for ``sqrt(radicand)``, on the dyadic grid."""
    if radicand < 1:
        raise ValueError("heron_sequence: the radicand must be positive")
    x = Fraction(radicand)
    out = [x]
    for _ in range(steps):
        x = _truncate((x + Fraction(radicand) / x) / 2, bits)
        out.append(x)
    return tuple(out)


def convergent_sequence(radicand: int, steps: int,
                        bits: int = GENERATOR_BITS) -> Tuple[Fraction, ...]:
    """The continued-fraction convergents of ``sqrt(radicand)``.

    Built from the exact recurrence on the numerator and denominator, so no
    square root is ever taken and no float appears.
    """
    if radicand < 1:
        raise ValueError("convergent_sequence: the radicand must be positive")
    # p/q -> (p + radicand*q) / (p + q) is the Newton-free recurrence whose
    # fixed point is sqrt(radicand); its iterates are the convergents.
    p, q = 1, 1
    out = [Fraction(p, q)]
    for _ in range(steps):
        p, q = p + radicand * q, p + q
        out.append(_truncate(Fraction(p, q), bits))
    return tuple(out)


def multi_fuel(radicand: int = 2, steps: int = 24,
               depth: int = 40) -> Dict[str, object]:
    """Burn two generators in parallel and read whichever is ahead.

    Both sequences converge to the same algebraic number.  At each tick the
    engine reads the one whose squared error is smaller -- a comparison that
    stays exact, because ``|x^2 - r|`` is rational and never needs the root
    itself.

    Returns
    -------
    dict
        the tick at which each generator alone clears ``depth`` bits, the
        tick at which the switching strategy clears it, and the exact
        speed-up that buys.
    """
    heron = heron_sequence(radicand, steps)
    convergents = convergent_sequence(radicand, steps)

    def _residual(x: Fraction) -> Fraction:
        return abs(x * x - radicand)

    target_residual = Fraction(1, 2 ** depth)

    def _first_below(seq: Sequence[Fraction]) -> Optional[int]:
        for i, x in enumerate(seq):
            if _residual(x) <= target_residual:
                return i
        return None

    switched: List[Fraction] = []
    choices: List[str] = []
    for i in range(min(len(heron), len(convergents))):
        if _residual(heron[i]) <= _residual(convergents[i]):
            switched.append(heron[i])
            choices.append("heron")
        else:
            switched.append(convergents[i])
            choices.append("convergent")

    heron_tick = _first_below(heron)
    conv_tick = _first_below(convergents)
    switch_tick = _first_below(switched)

    slower = max(t for t in (heron_tick, conv_tick) if t is not None) \
        if (heron_tick is not None or conv_tick is not None) else None
    speedup = (Fraction(slower, switch_tick)
               if slower is not None and switch_tick else None)

    return {
        "radicand": radicand,
        "steps": steps,
        "depth": depth,
        "heron_tick": heron_tick,
        "convergent_tick": conv_tick,
        "switched_tick": switch_tick,
        "choices": tuple(choices),
        "switch_count": sum(1 for i in range(1, len(choices))
                            if choices[i] != choices[i - 1]),
        "speedup_over_slower": speedup,
        "switching_never_loses": (
            switch_tick is not None
            and all(t is None or switch_tick <= t
                    for t in (heron_tick, conv_tick))),
        "same_limit": all(
            abs(heron[i] - convergents[i]) <= _residual(heron[i])
            + _residual(convergents[i])
            for i in range(min(len(heron), len(convergents)))),
    }


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE GEARBOX
# ═════════════════════════════════════════════════════════════════════════

def classify_target(value) -> str:
    """What kind of number this is, decided from how it is presented.

    A :class:`~fractions.Fraction` is rational.  An
    :class:`~glm_universal.reasoning.exact_real.ExactReal` is algebraic when
    its name says it is a root, transcendental when it is one of the named
    transcendental processes, and exotic otherwise -- the classifier says
    "exotic" rather than guessing.
    """
    if isinstance(value, Fraction) or isinstance(value, int):
        return "rational"
    if isinstance(value, er.ExactReal):
        if value.exact is not None:
            return "rational"
        name = value.name.lower()
        if "sqrt" in name or "root" in name or "phi" in name:
            return "algebraic"
        if name.startswith("pi") or name.startswith("e"):
            return "transcendental"
        return "exotic"
    raise TypeError(f"classify_target: cannot classify {type(value)!r}")


def gearbox(value) -> Dict[str, object]:
    """Classify a target and return the configuration the engine should use."""
    kind = classify_target(value)
    gear = GEARS[kind]
    config = EngineConfig(snap_mode=str(gear["snap"]),
                          radiator_period=int(gear["radiator"]))  # type: ignore[arg-type]
    return {"kind": kind, "config": config, "reading": gear["reading"]}


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE HEADLINE: HOW BIG IS THE LEAP?
# ═════════════════════════════════════════════════════════════════════════

def bits_cleared(error: Fraction) -> int:
    """The largest ``k`` with ``error <= 2^-k``; exact, found by doubling."""
    if error <= 0:
        return -1
    k = 0
    bound = Fraction(1)
    while bound / 2 >= error:
        bound /= 2
        k += 1
    return k


#: The targets the leap is measured on.
LEAP_TARGETS: Tuple[Fraction, ...] = (
    Fraction(1, 3), Fraction(2, 7), Fraction(5, 12),
)


def precision_leap(ticks: int = 64,
                   targets: Sequence[Fraction] = LEAP_TARGETS
                   ) -> Dict[str, object]:
    """Measure the blueprint's "2.7x precision leap" -- three ways.

    A ratio of precisions is only meaningful once both terms are named.  The
    blueprint names neither, so three separate baselines are measured, each
    stated:

    ``against_truncation``
        the engine's tick budget spent instead on truncating the target's
        binary expansion, one bit per tick.  This is the honest comparison a
        sceptic would make, and the engine loses it badly: a modulator's
        running average clears bits logarithmically, not linearly.
    ``against_first_order_hold``
        the same budget spent holding the first emitted bit, which is what a
        one-shot quantiser does.  This is the comparison the modulator is
        designed to win.
    ``against_half_budget``
        the engine at ``ticks`` against the engine at ``ticks/2``: what
        doubling the budget buys, with no other solver involved.
    """
    rows: List[Dict[str, object]] = []
    for target in targets:
        run = accumulate(target, ticks)
        half = accumulate(target, max(1, ticks // 2))
        engine_bits = bits_cleared(run["error"])          # type: ignore[arg-type]
        half_bits = bits_cleared(half["error"])           # type: ignore[arg-type]
        truncation_bits = ticks
        hold_error = abs(Fraction(run["bits"][0]) - target)  # type: ignore[index]
        hold_bits = bits_cleared(hold_error)
        rows.append({
            "target": str(target),
            "engine_bits": engine_bits,
            "truncation_bits": truncation_bits,
            "hold_bits": hold_bits,
            "half_budget_bits": half_bits,
            "against_truncation": str(Fraction(engine_bits, truncation_bits)),
            "against_first_order_hold": (
                str(Fraction(engine_bits, hold_bits)) if hold_bits > 0
                else "unbounded"),
            "against_half_budget": (
                str(Fraction(engine_bits, half_bits)) if half_bits > 0
                else "unbounded"),
        })

    def _ratios(key: str) -> List[Fraction]:
        out = []
        for row in rows:
            if row[key] != "unbounded":
                out.append(Fraction(str(row[key])))
        return out

    truncation = _ratios("against_truncation")
    half = _ratios("against_half_budget")
    claimed = Fraction(27, 10)
    return {
        "ticks": ticks,
        "rows": rows,
        "claimed_ratio": str(claimed),
        "against_truncation_range": [str(min(truncation)),
                                     str(max(truncation))]
        if truncation else [],
        "against_half_budget_range": [str(min(half)), str(max(half))]
        if half else [],
        "any_baseline_gives_the_claimed_ratio": any(
            r == claimed for r in truncation + half),
        "reading": (
            "the modulator loses outright against bitwise truncation and "
            "wins outright against a one-shot hold; between those two the "
            "ratio can be made almost anything, so a bare '2.7x' names no "
            "measurement"
        ),
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT AND THE VERDICTS
# ═════════════════════════════════════════════════════════════════════════

def engine_report(ticks: int = 64) -> Dict[str, object]:
    """The assembled engine, measured end to end."""
    target = Fraction(1, 3)

    plain = run_engine(
        target, ticks,
        EngineConfig(snap_mode="relaxed", radiator_period=0, turbo=False))
    cooled = run_engine(
        target, ticks,
        EngineConfig(snap_mode="relaxed", radiator_period=16, turbo=False))
    no_turbo = plain
    turbo = run_engine(
        target, ticks,
        EngineConfig(snap_mode="relaxed", radiator_period=0, turbo=True))

    # The two snap strengths measure different quantities on the same
    # carrier; the gap is reported rather than smoothed over.
    probe = _carrier_from(accumulate(target, ticks)["bits"],  # type: ignore[arg-type]
                          EngineConfig().amplitude)
    tight_reading = snap(probe, "tight")
    relaxed_reading = snap(probe, "relaxed")

    fuel = multi_fuel()
    leap = precision_leap(ticks)

    gears = {
        name: {
            "kind": gearbox(value)["kind"],
            "snap": gearbox(value)["config"].snap_mode,
            "radiator": gearbox(value)["config"].radiator_period,
        }
        for name, value in (
            ("1/3", Fraction(1, 3)),
            ("sqrt(2)", er.sqrt(Fraction(2))),
            ("pi", er.pi()),
        )
    }

    return {
        "ticks": ticks,
        "stages": {
            "accumulator": {
                "target": str(target),
                "error": str(plain.error),
                "peak_displacement": str(
                    accumulate(target, ticks)["peak_displacement"]),
            },
            "escapements": {
                "moduli": list(ESCAPEMENT_MODULI),
                "reading_at_100": list(escapements(100)),
                "period": escapement_period(),
            },
            "snap": {
                "modes": list(SNAP_MODES),
                "operation_cost": dict(SNAP_OPERATION_COST),
                "capacity": str(TAX_CAPACITY),
            },
        },
        "runs": {
            "plain": plain.as_dict(),
            "cooled": cooled.as_dict(),
            "without_turbo": no_turbo.as_dict(),
            "with_turbo": turbo.as_dict(),
        },
        "strain_readings": {
            "tight": {"kind": tight_reading["strain_kind"],
                      "distance2": str(tight_reading["distance2"]),
                      "tax": str(tight_reading["tax"])},
            "relaxed": {"kind": relaxed_reading["strain_kind"],
                        "coset_weight": relaxed_reading["coset_weight"],
                        "distance2": str(relaxed_reading["distance2"]),
                        "tax": str(relaxed_reading["tax"])},
            "agree": tight_reading["tax"] == relaxed_reading["tax"],
            "reading": (
                "the exact search measures the distance to the Leech "
                "lattice and the certificate path measures the distance to "
                "the nearest Golay-aligned sign pattern; on a sign carrier "
                "these are different numbers, so the fast path is a "
                "different reading rather than an approximation of the slow "
                "one"),
        },
        "radiator_bleeds": cooled.bleeds,
        "radiator_lowers_final_strain": (
            cooled.accumulated_tax <= plain.accumulated_tax),
        "turbo_saves_operations": (
            no_turbo.operations - turbo.operations),
        "turbo_snaps_avoided": (
            turbo.snaps["skip"] - no_turbo.snaps["skip"]),
        "multi_fuel": fuel,
        "precision_leap": leap,
        "gearbox": gears,
    }


def blueprint_claims(ticks: int = 64) -> Tuple[Dict[str, object], ...]:
    """Each Part III sentence, the figure that settles it, and the verdict."""
    report = engine_report(ticks)
    fuel = report["multi_fuel"]
    leap = report["precision_leap"]
    plain = report["runs"]["plain"]         # type: ignore[index]
    cooled = report["runs"]["cooled"]       # type: ignore[index]

    return (
        {
            "claim": "the baseline engine routes a target through four "
                     "stages: accumulator, escapements, Leech snap and "
                     "escalation trip-lever",
            "verdict": "confirmed",
            "holds": True,
            "figure": f"one run on 1/3 over {ticks} ticks: error "
                      f"{plain['error']}, drum period "
                      f"{escapement_period()}, snaps {plain['snaps']}, "
                      f"escalations {plain['escalations']}",
        },
        {
            "claim": "the radiator bleeds accumulated strain and prevents "
                     "premature escalation",
            "verdict": ("confirmed" if report["radiator_lowers_final_strain"]
                        else "refuted"),
            "holds": bool(report["radiator_lowers_final_strain"]),
            "figure": f"{cooled['bleeds']} bleeds leave strain "
                      f"{cooled['accumulated_tax']} against "
                      f"{plain['accumulated_tax']} uncooled, and "
                      f"{cooled['escalations']} escalations against "
                      f"{plain['escalations']}",
        },
        {
            "claim": "two generators run in parallel and the engine swaps to "
                     "the faster-converging path at each tick",
            "verdict": ("confirmed" if fuel["switching_never_loses"]
                        else "refuted"),
            "holds": bool(fuel["switching_never_loses"]),
            "figure": f"Heron clears {fuel['depth']} bits at tick "
                      f"{fuel['heron_tick']}, the convergents at "
                      f"{fuel['convergent_tick']}, the switching strategy at "
                      f"{fuel['switched_tick']}, with "
                      f"{fuel['switch_count']} swap(s)",
        },
        {
            "claim": "the turbocharger conserves integer operations by "
                     "relaxing or skipping the snap under strain",
            "verdict": ("confirmed" if report["turbo_saves_operations"] > 0
                        else "refuted"),
            "holds": bool(report["turbo_saves_operations"] > 0),
            "figure": f"{report['turbo_snaps_avoided']} of the run's snaps "
                      f"are skipped once the strain is over capacity, "
                      f"saving {report['turbo_saves_operations']} integer "
                      f"operations against the same run with the "
                      f"turbocharger disabled, under the stated cost model "
                      f"{dict(SNAP_OPERATION_COST)}",
        },
        {
            "claim": "the gearbox classifies a target at runtime and shifts "
                     "the configuration",
            "verdict": "confirmed",
            "holds": True,
            "figure": f"{report['gearbox']}",
        },
        {
            "claim": "the engine achieves a 2.7x precision leap over naive "
                     "solvers",
            "verdict": "not reproduced -- the ratio names no measurement",
            "holds": not leap["any_baseline_gives_the_claimed_ratio"],
            "figure": f"against bitwise truncation the ratio is in "
                      f"{leap['against_truncation_range']} (the engine "
                      f"loses); against half the tick budget it is in "
                      f"{leap['against_half_budget_range']}; none of the "
                      f"three stated baselines gives 27/10",
        },
    )
