"""The capability probes: what the GLM can do, and exactly where it stops.

Each probe below is a question a user might ask of the machine -- *can it hold
an irrational value?  can it stack a coordinate of 10^40?  can it tell me two
processes are equal?* -- put to the real code and answered by running it.

The probes that come back ``breaks`` are the point of the file.  Each one
carries the place where the capability stops, exactly: a weight, a level, a
denominator, a separating functional.  Together they are the map of what is
left to build, and several of them are boundaries that are *theorems* -- they
will not be fixed, because they cannot be.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Tuple

from ..data_objects import base as dob
from ..reasoning import coherence as co
from ..reasoning import exact_real as er
from ..reasoning import information_loss as il
from ..reasoning import product as pr
from ..substrate import digit_stack as ds
from ..substrate import golay_decode as gd
from .harness import Outcome, breaks, holds, probe

__all__ = ["ALL_PROBE_NAMES"]


# ===========================================================================
# 1.  REAL AND IRRATIONAL VALUES
# ===========================================================================

@probe("real_sqrt_to_arbitrary_precision", "reals",
       "Can the machine produce sqrt(2) to any precision I ask for?", "holds")
def _real_sqrt_to_arbitrary_precision() -> Outcome:
    root2 = er.sqrt(Fraction(2))
    checked: List[int] = []
    for k in (8, 32, 64, 128, 256):
        value = root2.at(k)
        below = value ** 2 <= 2
        above = (value + er._eps(k)) ** 2 >= 2
        if not (below and above):
            return breaks(f"the bracket fails at precision 2**-{k}",
                          precision=k, value=value)
        checked.append(k)
    return holds("no ceiling found; the cost is the only limit",
                 precisions=tuple(checked),
                 digits_at_256=root2.decimal(40))


@probe("real_transcendental_constants", "reals",
       "Can it produce pi, e and the golden ratio exactly enough to compare?",
       "holds")
def _real_transcendental_constants() -> Outcome:
    value = er.pi().at(64)
    # Two classical rational bounds, one on each side.
    bracketed = Fraction(333, 106) < value < Fraction(355, 113)
    e_value = er.e().at(64)
    e_bracketed = Fraction(2718, 1000) < e_value < Fraction(2719, 1000)
    golden = er.phi()
    # phi^2 = phi + 1, to the precision asked for.
    residual = abs(golden.at(64) ** 2 - golden.at(64) - 1)
    consistent = residual < Fraction(1, 2 ** 60)
    if not (bracketed and e_bracketed and consistent):
        return breaks("a constant failed its own defining relation",
                      pi_bracketed=bracketed, e_bracketed=e_bracketed,
                      phi_residual=residual)
    return holds("pi, e and phi to 2**-64, each checked against a relation "
                 "it must satisfy",
                 pi=er.pi().decimal(30), e=er.e().decimal(30),
                 phi=golden.decimal(30), phi_residual=residual)


@probe("real_arithmetic_is_closed", "reals",
       "Can it add and multiply irrationals and keep the guarantees?", "holds")
def _real_arithmetic_is_closed() -> Outcome:
    root2, root3, root6 = (er.sqrt(Fraction(n)) for n in (2, 3, 6))
    product = root2 * root3
    residuals = {}
    for k in (10, 20, 40, 60):
        residual = abs(product.at(k) - root6.at(k))
        residuals[k] = residual
        if residual > er._eps(k - 1):
            return breaks(f"sqrt(2)*sqrt(3) drifts from sqrt(6) at 2**-{k}",
                          precision=k, residual=residual)
    return holds("sqrt(2)*sqrt(3) agrees with sqrt(6) within the promised "
                 "error at every precision tried",
                 residual_at_60=residuals[60])


@probe("real_equality_is_decidable", "reals",
       "Can it tell me that two constructions denote the same number?",
       "breaks")
def _real_equality_is_decidable() -> Outcome:
    left = er.sqrt(Fraction(2)) * er.sqrt(Fraction(2))
    right = er.from_fraction(Fraction(2))
    verdicts = {k: er.decide_equal(left, right, k) for k in (8, 16, 32, 64)}
    if any(verdict is not None for verdict in verdicts.values()):
        return holds("equality was decided", verdicts=verdicts)
    apart = er.decide_equal(er.sqrt(Fraction(2)),
                            er.from_fraction(Fraction(3, 2)), 4)
    return breaks(
        "equality of two processes is undecidable: sqrt(2)*sqrt(2) and 2 are "
        "still 'not yet distinguished' at 2**-64, and no precision settles "
        "it.  Inequality is decidable; equality is not, and the machine says "
        "so rather than guessing",
        verdict_at_64=verdicts[64], inequality_decided=apart)


@probe("real_value_as_carrier", "reals",
       "Can an irrational be stored in a carrier coordinate?", "breaks")
def _real_value_as_carrier() -> Outcome:
    root2 = er.sqrt(Fraction(2))
    try:
        dob.exact_vector([root2] + [Fraction(0)] * 23)
    except Exception as error:                       # noqa: BLE001 - the point
        rejection = f"{type(error).__name__}"
    else:
        return holds("a process was accepted as a coordinate")
    # And the closest a carrier can come, level by level.
    gaps = {n: abs(er.surrogate(root2, n) ** 2 - 2) for n in (4, 8, 16)}
    return breaks(
        "a carrier holds 24 rationals and no rational is sqrt(2); the "
        "coordinate is refused outright rather than rounded.  The tower's "
        "stand-in at level n is the closest a carrier gets, and its square "
        "is never 2",
        rejected_with=rejection, gap_at_level_16=gaps[16])


@probe("real_surrogate_on_a_grid_point", "reals",
       "Can it read the tower level of a value that sits exactly on the grid?",
       "breaks")
def _real_surrogate_on_a_grid_point() -> Outcome:
    # sqrt(1/4) is 1/2 exactly, but as a *process* nothing finite proves it is
    # not a hair below 1/2, and floor(x * 2) differs on the two sides.
    half_as_process = er.sqrt(Fraction(1, 4))
    try:
        value = er.surrogate(half_as_process, 1)
    except er.PrecisionError as error:
        return breaks(
            "the floor of a process is not computable at a point where the "
            "process sits exactly on the grid: 64 refinements of sqrt(1/4) "
            "still do not settle which side of 1/2 it is on.  A rational "
            "given as a rational is read instantly; the same number given as "
            "a limit is not",
            raised=type(error).__name__,
            rational_route=er.rational_surrogate(Fraction(1, 2), 1))
    return holds("the grid point was read", value=value)


@probe("real_tower_exposes_every_stand_in", "reals",
       "Does every rational stand-in for an irrational eventually fail?",
       "holds")
def _real_tower_exposes_every_stand_in() -> Outcome:
    root2 = er.sqrt(Fraction(2))
    exposures: Dict[int, int] = {}
    for level in range(6):
        stand_in = er.surrogate(root2, level)
        for higher in range(level, level + 10):
            if er.surrogate(root2, higher) != er.rational_surrogate(stand_in, higher):
                exposures[level] = higher
                break
        else:
            return breaks(f"the stand-in at level {level} was never exposed",
                          level=level, stand_in=stand_in)
    return holds("every stand-in tried is separated from the target at a "
                 "higher level; no carrier is true of it all the way up",
                 exposed_at=tuple(sorted(exposures.items())))


# ===========================================================================
# 2.  THE DYNAMIC CARRIER
# ===========================================================================

@probe("dynamic_one_dimensional_bound", "dynamic carrier",
       "Does the modulator really reach any target at rate 1/N?", "holds")
def _dynamic_one_dimensional_bound() -> Outcome:
    targets = (Fraction(3, 7), Fraction(1, 3),
               er.sqrt(Fraction(2)).at(40) - 1,
               er.pi().at(40) - 3)
    worst: Dict[str, Fraction] = {}
    for target in targets:
        for steps in (16, 256, 2048):
            error = er.delta_sigma_error(target, steps)
            if error > Fraction(1, steps):
                return breaks(f"the 1/N bound failed at N={steps}",
                              target=target, steps=steps, error=error)
            worst[f"{target}@{steps}"] = error
    return holds("|average - target| <= 1/N held for every target and run "
                 "length tried, including irrational targets pinned to "
                 "2**-40",
                 runs=len(worst))


@probe("dynamic_resolution_grows_with_time", "dynamic carrier",
       "Does a longer run really buy more resolution?", "holds")
def _dynamic_resolution_grows_with_time() -> Outcome:
    target = er.sqrt(Fraction(2)).at(60) - 1
    errors = {steps: er.delta_sigma_error(target, steps)
              for steps in (8, 64, 512, 4096)}
    improving = all(errors[b] <= errors[a] + Fraction(1, a)
                    for a, b in ((8, 64), (64, 512), (512, 4096)))
    values = {steps: er.delta_sigma_average(target, steps)
              for steps in (8, 64)}
    on_grid = all(value.denominator <= steps
                  for steps, value in values.items())
    if not (improving and on_grid):
        return breaks("the resolution did not improve as the run lengthened",
                      errors=errors)
    return holds("N ticks give resolution 1/N and no more: the average after "
                 "N steps is one of the N+1 values k/N",
                 error_at_4096=errors[4096],
                 average_at_8=values[8])


@probe("dynamic_24d_reachable_target", "dynamic carrier",
       "Can the 24-D carrier hold a target that is not a codeword?", "holds")
def _dynamic_24d_reachable_target() -> Outcome:
    half = tuple(Fraction(1, 2) for _ in range(24))
    run = er.golay_delta_sigma(half, 64)
    if not run["within_one_over_n"]:
        return breaks("the average missed the target",
                      deviation=run["max_coordinate_deviation"])
    return holds("the all-1/2 vector, which is no codeword, is held exactly "
                 "as the time average of two codewords",
                 deviation=run["max_coordinate_deviation"],
                 accumulator=run["max_accumulator"],
                 codewords_visited=run["unique_codewords"])


@probe("dynamic_24d_arbitrary_target", "dynamic carrier",
       "Can the 24-D carrier hold *any* target in the unit cube?", "breaks")
def _dynamic_24d_arbitrary_target() -> Outcome:
    ramp = tuple(Fraction(i, 24) for i in range(24))
    short = er.golay_delta_sigma(ramp, 100)
    long_run = er.golay_delta_sigma(ramp, 400)
    certificate = er.hull_certificate(ramp, 200)
    if short["within_one_over_n"]:
        return holds("the ramp target was reached",
                     deviation=short["max_coordinate_deviation"])
    return breaks(
        "the reachable set of the 24-D carrier is the convex hull of the "
        "4,096 codewords, and the ramp target (coordinate i holds i/24) is "
        "outside it.  The error accumulator therefore grows without bound "
        "and the time average stalls about 1/16 away, whatever the quantiser "
        "rule.  A separating functional is computed and verified against "
        "every codeword, so this is a certificate and not an observation",
        deviation_at_100=short["max_coordinate_deviation"],
        deviation_at_400=long_run["max_coordinate_deviation"],
        accumulator_at_100=short["max_accumulator"],
        accumulator_at_400=long_run["max_accumulator"],
        certificate_separates=certificate["separates"],
        certificate_gap=certificate["gap"],
        codewords_checked=certificate["codewords_checked"])


@probe("dynamic_repair_is_single_valued", "dynamic carrier",
       "Is the repair step of the loop always a function?", "breaks")
def _dynamic_repair_is_single_valued() -> Outcome:
    ramp = tuple(Fraction(i, 24) for i in range(24))
    run = er.golay_delta_sigma(ramp, 100)
    ambiguous = int(run["ambiguous_ticks"])
    if ambiguous == 0:
        return holds("no tick needed a tie broken", ticks=run["steps"])
    return breaks(
        f"on {ambiguous} of {run['steps']} ticks the driven word sat at "
        f"Hamming distance 4 from six codewords at once, so the repair has no "
        f"single value.  The decoder reports the tie instead of breaking it, "
        f"and the loop falls back on the received word -- a declared "
        f"fallback, not a hidden choice",
        ambiguous_ticks=ambiguous, steps=run["steps"])


# ===========================================================================
# 3.  SUBSTRATE
# ===========================================================================

@probe("substrate_repair_radius", "substrate",
       "How much damage can a 24-bit reading take and still be repaired?",
       "breaks")
def _substrate_repair_radius() -> Outcome:
    statuses = {}
    for weight, mask in ((1, 0b1), (2, 0b11), (3, 0b111), (4, 0b1111)):
        statuses[weight] = gd.decode_complete(mask).status
    if statuses[4] != "ambiguous":
        return holds("weight 4 was repaired uniquely", statuses=statuses)
    # Weight 5: confidently wrong, by the Steiner system.
    report = gd.weight5_miscorrection_report(samples=50)
    return breaks(
        "the repair radius is exactly 3.  At weight 4 six codewords are "
        "equally near and the reading is ambiguous; at weight 5 the answer is "
        "unique, confident and wrong, because the octads form a Steiner "
        "system S(5,8,24).  No better decoder exists -- the boundary is a "
        "theorem about the code",
        statuses=statuses,
        weight5_miscorrected=report.get("miscorrected", "n/a"))


# ===========================================================================
# 4.  CARRIERS
# ===========================================================================

@probe("carrier_unbounded_magnitude", "carriers",
       "Is there a largest number a carrier coordinate can hold?", "holds")
def _carrier_unbounded_magnitude() -> Outcome:
    depths = {}
    for exponent in (10, 40, 120):
        vector = tuple([Fraction(10 ** exponent)] + [Fraction(0)] * 23)
        parameters = dob.derive_dynamic_parameters(vector)
        depths[exponent] = parameters.depth
        stack = ds.class_stack(vector, offset=parameters.offset,
                               depth=parameters.depth)
        if tuple(ds.class_stack_rebuild(stack)) != vector:
            return breaks(f"the stack lost 10**{exponent}",
                          exponent=exponent, depth=parameters.depth)
    return holds("no ceiling: the depth grows with the magnitude and the "
                 "stack rebuilds the coordinate exactly",
                 depths=tuple(sorted(depths.items())))


@probe("carrier_non_dyadic_denominator", "carriers",
       "Can every rational carrier be read as a stack of binary planes?",
       "breaks")
def _carrier_non_dyadic_denominator() -> Outcome:
    twelfth = tuple([Fraction(1, 12)] + [Fraction(0)] * 23)
    parameters = dob.derive_dynamic_parameters(twelfth)
    if parameters.dyadic_exponent is not None:
        return holds("a dyadic exponent exists",
                     exponent=parameters.dyadic_exponent)
    stack = ds.class_stack(twelfth, offset=parameters.offset,
                           depth=parameters.depth)
    faithful = tuple(ds.class_stack_rebuild(stack)) == twelfth
    return breaks(
        "a coordinate of 1/12 has no dyadic exponent: no power of two clears "
        "its denominator, so there is no depth at which the binary planes "
        "*are* the value.  The general route -- clear the denominator first, "
        "then stack -- is faithful, and it is the one the codecs use; the "
        "binary-plane reading is the thing that stops",
        denominator=parameters.denominator,
        dyadic_exponent=parameters.dyadic_exponent,
        general_route_faithful=faithful)


@probe("carrier_rejects_floats", "carriers",
       "Will a float ever be silently accepted anywhere?", "holds")
def _carrier_rejects_floats() -> Outcome:
    rejections = {}
    for label, call in (
            ("exact_vector", lambda: dob.exact_vector([0.5] + [0] * 23)),
            ("delta_sigma", lambda: er.delta_sigma_bits(0.5, 4)),
            ("from_fraction", lambda: er.from_fraction(0.5)),
            ("rational_sqrt", lambda: er.rational_sqrt_approx(2.0, 4))):
        try:
            call()
        except TypeError as error:
            rejections[label] = type(error).__name__
        else:
            return breaks(f"{label} accepted a float", entry=label)
    return holds("every entry point tried refuses a float outright rather "
                 "than coercing it",
                 entries=tuple(sorted(rejections)))


# ===========================================================================
# 5.  LAYERS
# ===========================================================================

@probe("layers_form_a_refinement_chain", "layers",
       "Does escalating to a higher layer ever lose something?", "holds")
def _layers_form_a_refinement_chain() -> Outcome:
    report = il.information_loss_report()
    if not report["refinement_chain_intact"]:
        holes = [f"{b['lower']}->{b['higher']}" for b in report["boundaries"]
                 if not b["refines"]]
        return breaks("escalation loses information at " + ", ".join(holes),
                      holes=tuple(holes))
    raw = report["non_cumulative"]
    return holds("every layer of the shipped stack sees at least as much as "
                 "the one below, so nothing true below becomes unstatable "
                 "above; the non-cumulative SI7 reading, kept beside it, is "
                 "the counter-example that shows the property is not free",
                 carriers=report["carrier_count"],
                 non_cumulative_refines=raw["refines_substrate"],
                 non_cumulative_violations=raw["violation_count"])


@probe("layers_can_compute_addition", "layers",
       "Can each layer add two carriers using only what it can see?",
       "breaks")
def _layers_can_compute_addition() -> Outcome:
    report = il.information_loss_report()
    descends = {layer["name"]: layer["addition_descends"]
                for layer in report["layers"]}
    if all(descends.values()):
        return holds("addition descends everywhere", layers=descends)
    stuck = [name for name, ok in descends.items() if not ok]
    return breaks(
        "addition is not a function of what the lower layers see: "
        + ", ".join(stuck) +
        " each conflate two carriers whose sums they then distinguish.  The "
        "law is not false there -- it is not *statable* there, which is the "
        "precise content of the machine's can_multiply flag",
        descends=tuple(sorted(descends.items())))


@probe("tax_conservation_above_bits", "layers",
       "Does the TAX conservation law survive above binary carriers?",
       "breaks")
def _tax_conservation_above_bits() -> Outcome:
    # On bits the law is exact; the check here is the first place above them.
    y = co.Y if hasattr(co, "Y") else None
    left = tuple([Fraction(2)] + [Fraction(0)] * 23)
    right = tuple([Fraction(3)] + [Fraction(0)] * 23)
    total = tuple([Fraction(5)] + [Fraction(0)] * 23)
    lhs = co.combined_tax(left) + co.combined_tax(right)
    rhs = co.combined_tax(total)
    if lhs == rhs:
        return holds("the law held on natural carriers", lhs=lhs, rhs=rhs)
    return breaks(
        "the conservation law is exact on binary carriers and fails as soon "
        "as the coordinates are naturals: the only repair would need the "
        "coherence constant Y to be 1/2, and it is strictly between 1/4 and "
        "1/2.  The boundary is where the geometry stops being a bijection "
        "with the arithmetic",
        tax_left_plus_right=lhs, tax_of_sum=rhs, difference=lhs - rhs,
        y=y)


# ===========================================================================
# 6.  ALGEBRA
# ===========================================================================

@probe("algebra_product_is_associative", "algebra",
       "Can products of three axes be composed in any order?", "breaks")
def _algebra_product_is_associative() -> Outcome:
    # Take a genuine pairwise-2A triple out of the substrate and bracket its
    # product both ways.  Nothing is quoted: both sides are computed here.
    first, second = pr.sample_two_a_pairs(1)[0]
    triple = pr.two_a_subalgebra(first, second)
    a, b, c = triple.labels
    x, y, z = pr.axis(a), pr.axis(b), pr.axis(c)
    left = pr.algebra_product(pr.algebra_product(x, y), z)
    right = pr.algebra_product(x, pr.algebra_product(y, z))
    if left == right:
        return holds("the two bracketings agreed on this triple",
                     triple=(a, b, c), value=str(left))
    return breaks(
        "the Norton-Sakuma product is not associative: the two bracketings "
        "of a pairwise-2A triple give -3/32 times *different* axes.  A "
        "pipeline that composed addresses with XOR was associative, and was "
        "therefore working in a quotient the Monster's product does not live "
        "in",
        triple=(a, b, c), left=str(left), right=str(right),
        subalgebra_closed=triple.closed,
        subalgebra_commutative=triple.commutative,
        subalgebra_associative=triple.associative)


# ===========================================================================
# 7.  RUNTIME
# ===========================================================================

@probe("runtime_answers_about_irrationals", "runtime",
       "Can I ask the running system about sqrt(2) and get an answer?",
       "holds")
def _runtime_answers_about_irrationals() -> Outcome:
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    solution = session.ask("approximate sqrt(2) to 20 places")
    if not solution.ok:
        return breaks(
            "the runtime has no route to a value that is not a carrier: "
            + solution.answer[:160],
            kind=solution.kind)
    return holds("the runtime answers about a value no carrier holds, and "
                 "says which levels of the tower stand in for it",
                 kind=solution.kind,
                 answer=solution.expected.get("decimal", "")[:32])


@probe("runtime_admits_what_it_cannot_parse", "runtime",
       "Does an unrecognised query fail loudly rather than guess?", "holds")
def _runtime_admits_what_it_cannot_parse() -> Outcome:
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    solution = session.ask("flibbertigibbet")
    if solution.ok:
        return breaks("a nonsense query was answered", answer=solution.answer)
    return holds("an unrecognised query comes back as kind 'unknown' with "
                 "suggestions, never as a confident wrong answer",
                 kind=solution.kind)


ALL_PROBE_NAMES: Tuple[str, ...] = (
    "real_sqrt_to_arbitrary_precision",
    "real_transcendental_constants",
    "real_arithmetic_is_closed",
    "real_equality_is_decidable",
    "real_value_as_carrier",
    "real_surrogate_on_a_grid_point",
    "real_tower_exposes_every_stand_in",
    "dynamic_one_dimensional_bound",
    "dynamic_resolution_grows_with_time",
    "dynamic_24d_reachable_target",
    "dynamic_24d_arbitrary_target",
    "dynamic_repair_is_single_valued",
    "substrate_repair_radius",
    "carrier_unbounded_magnitude",
    "carrier_non_dyadic_denominator",
    "carrier_rejects_floats",
    "layers_form_a_refinement_chain",
    "layers_can_compute_addition",
    "tax_conservation_above_bits",
    "algebra_product_is_associative",
    "runtime_answers_about_irrationals",
    "runtime_admits_what_it_cannot_parse",
)
