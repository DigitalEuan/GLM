"""Capability probes for the parts a user actually touches.

:mod:`~glm_universal.capabilities.probes` asks what the geometry can do.  This
file asks what the *machine* can do when it is spoken to: can it read an
expression, order two values, say what a word means, refuse a word it has no
referent for, hold more data than the substrate has room for, and hand back an
answer that re-derives itself in a fresh interpreter.

As there, a probe that comes back ``breaks`` is the useful one.  Each carries
the exact place the capability stops, and those places are the work list:
there is no inverse or hyperbolic function in the value grammar, no arithmetic
in the *describe* route, no vocabulary outside the registers, and no
twenty-fifth coordinate.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Tuple

from ..reasoning import exact_real as er
from ..reasoning import real_expr as rx
from ..semantics import reference as rf
from .harness import Outcome, breaks, holds, probe

__all__ = ["LANGUAGE_PROBE_NAMES"]


# ===========================================================================
# 1.  WRITTEN ARITHMETIC OVER THE REALS
# ===========================================================================

@probe("real_written_arithmetic", "reals",
       "Can I write an expression like (1+sqrt(5))/2 and get its digits?",
       "holds")
def _real_written_arithmetic() -> Outcome:
    built = rx.parse_expression("(1+sqrt(5))/2")
    golden = er.phi()
    agree = abs(built.at(80) - golden.at(80)) <= Fraction(1, 2 ** 78)
    sum_of_roots = rx.parse_expression("sqrt(2)+sqrt(3)")
    # (sqrt2+sqrt3)^2 = 5 + 2*sqrt(6), checked against an independent build.
    squared = sum_of_roots * sum_of_roots
    reference = rx.parse_expression("5+2*sqrt(6)")
    consistent = abs(squared.at(70) - reference.at(70)) <= Fraction(1, 2 ** 66)
    if not (agree and consistent):
        return breaks("an expression disagreed with an independent build of "
                      "the same value",
                      phi_agrees=agree, square_agrees=consistent)
    return holds("the grammar composes +, -, *, /, integer powers and roots "
                 "over processes, and the results agree with independent "
                 "constructions of the same numbers",
                 phi=built.decimal(24),
                 sum_of_roots=sum_of_roots.decimal(24),
                 cube_root_of_2=rx.parse_expression("root(3, 2)").decimal(24))


@probe("real_division_by_an_undecided_value", "reals",
       "Can it divide by a quantity that might be zero?", "breaks")
def _real_division_by_an_undecided_value() -> Outcome:
    try:
        value = rx.parse_expression("1/(sqrt(2)-sqrt(2))", depth=64)
        return holds("the division went through", value=value.decimal(10))
    except er.PrecisionError:
        pass
    except ZeroDivisionError as error:                # noqa: BLE001 reported
        return breaks("division by an exact zero was caught by type",
                      error=str(error))
    # The same shape with a divisor that *is* apart from zero goes through, so
    # the refusal is about the undecidable case and nothing else.
    ok = rx.parse_expression("1/(sqrt(3)-sqrt(2))", depth=64)
    return breaks(
        "a divisor that has not moved away from zero by 2**-64 is refused: "
        "producing 1/x needs a bound |x| >= 2**-m, and no algorithm produces "
        "that bound for an arbitrary process, because doing so would decide "
        "whether the process is zero.  The refusal is the theorem, not a "
        "missing feature",
        witness_depth=64,
        witness_for_sqrt3_minus_sqrt2=er.nonzero_witness(
            rx.parse_expression("sqrt(3)-sqrt(2)"), 64),
        divisible_case=ok.decimal(12))


@probe("real_transcendental_functions", "reals",
       "Can it compute sin(1), log(2) or 2^pi?", "holds")
def _real_transcendental_functions() -> Outcome:
    """Built in v1.2.0.  The probe now checks the identities, not the refusal."""
    values = {}
    for text in ("sin(1)", "log(2)", "exp(1)", "2^pi", "2^(1/3)", "tan(1)"):
        values[text] = rx.parse_expression(text).decimal(20)

    # Each value is checked against an identity it must satisfy, so a wrong
    # series or a wrong error budget shows up here rather than in a decimal
    # nobody reads.
    checks = {
        "exp(1) is e":
            abs(rx.parse_expression("exp(1)").at(80) - er.e().at(80))
            <= Fraction(1, 2 ** 78),
        "exp inverts log":
            abs(rx.parse_expression("exp(log(7/2))").at(60) - Fraction(7, 2))
            <= Fraction(1, 2 ** 55),
        "sin^2 + cos^2 = 1":
            abs(rx.parse_expression("sin(1)^2+cos(1)^2").at(60) - 1)
            <= Fraction(1, 2 ** 55),
        "2^(1/3) is the cube root of 2":
            abs(rx.parse_expression("2^(1/3)").at(60)
                - rx.parse_expression("root(3, 2)").at(60))
            <= Fraction(1, 2 ** 55),
        "log(2, 8) = 3":
            abs(rx.parse_expression("log(2, 8)").at(60) - 3)
            <= Fraction(1, 2 ** 55),
    }
    failed = tuple(name for name, ok in checks.items() if not ok)
    if failed:
        return breaks("a transcendental value failed an identity it must "
                      "satisfy", failed=failed, values=values)

    # Where the layer stops now: the inverse functions are refused by name,
    # and a logarithm still needs a positivity witness.
    refused = {}
    for text in ("asin(1)", "atan(1)", "sinh(1)", "log(0)",
                 "log(sqrt(2)-sqrt(2))"):
        try:
            rx.parse_expression(text, depth=32).at(16)
            refused[text] = "accepted"
        except (rx.ExpressionError, er.PrecisionError, ValueError) as error:
            refused[text] = type(error).__name__
    if any(verdict == "accepted" for verdict in refused.values()):
        return breaks("a function that is not built was accepted anyway",
                      refusals=refused)

    return holds(
        "exp, the natural logarithm, sin, cos, tan and a non-integer exponent "
        "are computed as processes with stated error bounds, and each agrees "
        "with an identity it must satisfy.  What is still refused by name is "
        "the inverse family -- asin, atan, sinh and the rest -- and a "
        "logarithm whose argument has not moved above zero, which needs a "
        "positivity witness for the same reason a division needs a nonzero "
        "one",
        values=values,
        refusals=refused,
        unbuilt=rx.UNBUILT_FUNCTIONS)


# ===========================================================================
# 2.  THE DYNAMIC CARRIER ON AN IRRATIONAL TARGET
# ===========================================================================

@probe("dynamic_24d_irrational_target", "dynamic carrier",
       "Can the 24-D carrier hold an irrational value in every coordinate?",
       "holds")
def _dynamic_24d_irrational_target() -> Outcome:
    # sqrt(2) - 1 in all 24 coordinates: irrational, and inside the hull of
    # the code because the all-ones word is a codeword.
    fractional = er.surrogate(er.sqrt(Fraction(2)), 40) - 1
    target = tuple(fractional for _ in range(24))
    steps = 200
    run = er.golay_delta_sigma(target, steps, rule="minnorm")
    if not run["within_one_over_n"]:
        return breaks(
            "the time average missed the target by more than 1/N",
            deviation=run["max_coordinate_deviation"], steps=steps)
    return holds(
        "a constant irrational target is tracked to within 1/N, with the "
        "accumulator bounded -- the carrier holds what no single carrier can "
        "hold, by moving",
        steps=steps,
        deviation=run["max_coordinate_deviation"],
        bound=Fraction(1, steps),
        max_accumulator=run["max_accumulator"],
        codewords_used=run["unique_codewords"])


# ===========================================================================
# 3.  MEANING
# ===========================================================================

@probe("semantics_refuses_an_ambiguous_term", "semantics",
       "If a word has two referents, will it say so instead of picking one?",
       "holds")
def _semantics_refuses_an_ambiguous_term() -> Outcome:
    report = rf.ambiguity_report()
    ambiguous = report["ambiguous"]
    if not ambiguous:
        return breaks("no term in the registers is ambiguous, so the refusal "
                      "has never been exercised",
                      named_terms=report["named_terms"])
    sample = str(ambiguous[0]["term"])
    resolution = rf.resolve(sample)
    if resolution.meaning is not None:
        return breaks(
            f"the ambiguous term {sample!r} was resolved anyway, by resolver "
            f"order rather than by evidence",
            sense=resolution.sense, witness=resolution.witness)
    return holds(
        "an ambiguous term comes back refused, with every sense that claimed "
        "it listed; the resolution order is never used as a tie-break",
        named_terms=report["named_terms"],
        ambiguous_terms=report["ambiguous_terms"],
        example=sample, reason=resolution.reason[:120])


@probe("semantics_open_vocabulary", "semantics",
       "Can it tell me what an ordinary English word means?", "breaks")
def _semantics_open_vocabulary() -> Outcome:
    words = ("justice", "friendship", "banana", "yesterday")
    refused = {}
    for word in words:
        resolution = rf.resolve(word)
        refused[word] = resolution.sense
    resolved = [word for word, sense in refused.items() if sense != "none"]
    if resolved:
        return holds("some open-vocabulary word resolved",
                     resolved=tuple(resolved))
    report = rf.ambiguity_report()
    return breaks(
        "the vocabulary is exactly the registers -- numerals, SI constants, "
        "the 118 elements and their formulae, the physics quantities and the "
        "operators.  A word outside them has no determinate referent and is "
        "refused, which is the right answer for a machine whose meanings are "
        "geometric: it has nowhere to put 'justice'.  Widening the "
        "vocabulary means widening the registers, not the parser",
        named_terms=report["named_terms"],
        tried=words, senses=refused)


# ===========================================================================
# 4.  SCALE
# ===========================================================================

@probe("scale_more_than_24_coordinates", "scale",
       "Can it hold a value with more than 24 coordinates?", "breaks")
def _scale_more_than_24_coordinates() -> Outcome:
    root2 = er.sqrt(Fraction(2))
    try:
        er.real_carrier([root2] * 25, 8)
        return holds("a 25-coordinate carrier was accepted")
    except ValueError as error:
        message = str(error)
    fits = len(er.real_carrier([root2] * 24, 8))
    return breaks(
        "twenty-four is the substrate, not a parameter: the Leech lattice, "
        "the Golay code and the MOG all live in 24 coordinates, so a "
        "25th has nowhere to go and is refused rather than silently dropped. "
        "Wider data must be projected first, and a projection conflates",
        limit=24, accepted_width=fits, refusal=message)


@probe("scale_precision_has_no_ceiling", "scale",
       "Is there a precision beyond which the machine gives up?", "holds")
def _scale_precision_has_no_ceiling() -> Outcome:
    root2 = er.sqrt(Fraction(2))
    checked = []
    for k in (64, 256, 1024, 4096):
        value = root2.at(k)
        if not (value ** 2 <= 2 <= (value + er._eps(k)) ** 2):
            return breaks(f"the bracket failed at 2**-{k}", precision=k)
        checked.append(k)
    digits = root2.decimal(200)
    return holds(
        "no ceiling: the representation is a rule, so the only cost of more "
        "precision is time.  The 200th decimal digit is produced by the same "
        "code as the first",
        precisions=tuple(checked),
        digits_200_tail=digits[-20:],
        digit_count=len(digits) - 2)


# ===========================================================================
# 5.  THE RUNNING MACHINE
# ===========================================================================

@probe("runtime_orders_two_reals", "runtime",
       "Can I ask which of two values is bigger and be told?", "holds")
def _runtime_orders_two_reals() -> Outcome:
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    decided = session.ask("is pi less than 355/113")
    undecided = session.ask("is sqrt(2)*sqrt(2) equal to 2")
    if not (decided.ok and undecided.ok):
        return breaks("a comparison query was not answered",
                      decided=decided.ok, undecided=undecided.ok)
    if decided.expected.get("verdict") != "True":
        return breaks("the machine got a decidable comparison wrong",
                      verdict=decided.expected.get("verdict"))
    if undecided.expected.get("verdict") != "undecided":
        return breaks("the machine claimed to settle an equality between two "
                      "processes",
                      verdict=undecided.expected.get("verdict"))
    return holds(
        "inequality is decided, and the precision it took is reported; "
        "equality comes back 'undecided' rather than guessed",
        decided_at=decided.expected.get("settled_at"),
        decided_verdict=decided.expected.get("verdict"),
        equality_verdict=undecided.expected.get("verdict"))


@probe("runtime_answer_reruns_itself", "runtime",
       "Does an answer come with a script that re-derives it from scratch?",
       "holds")
def _runtime_answer_reruns_itself() -> Outcome:
    from ..runtime import tct_engine as tct
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    solution = session.ask("approximate (1+sqrt(5))/2 to 20 places")
    trace = tct.verify_trace(tct.build_trace(solution))
    verdict = trace.verdict
    if verdict is None or not verdict.matches_column2:
        return breaks(
            "the generated script did not reproduce the answer",
            returncode=None if verdict is None else verdict.returncode,
            mismatches=None if verdict is None else verdict.mismatches)
    return holds(
        "the third column is a script, run in a fresh interpreter, whose "
        "output is asserted key by key against the answer that was given",
        keys_checked=len(solution.expected),
        returncode=verdict.returncode)


@probe("runtime_arithmetic_inside_a_describe", "runtime",
       "Can I ask about 'energy divided by time' as one question?", "holds")
def _runtime_arithmetic_inside_a_describe() -> Outcome:
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    composed = session.ask("what is energy divided by time")
    plain = session.ask("what is energy")
    if not composed.ok:
        return breaks(
            "the describe route resolves a *name*, and 'energy divided by "
            "time' is an expression over names, so it resolves to nothing",
            composed_error=(composed.error or "")[:140],
            plain_query_works=plain.ok)
    # The capability is won only if the arithmetic is actually done: the
    # quotient has dimension L^2 M T^-3, which the register names `power`.
    answer = composed.answer
    if "L^2 M T^-3" not in answer or "power" not in answer:
        return breaks(
            "the describe route answered, but not with the dimension of the "
            "quotient",
            answer=answer[:140])
    return holds(
        "the describe route rewrites the operator words into the dimensional "
        "grammar, evaluates the expression exactly, and names every register "
        "quantity of the resulting dimension, so an expression over names is "
        "askable as one question",
        answer=answer[:140],
        plain_query_works=plain.ok)


LANGUAGE_PROBE_NAMES: Tuple[str, ...] = (
    "real_written_arithmetic",
    "real_division_by_an_undecided_value",
    "real_transcendental_functions",
    "dynamic_24d_irrational_target",
    "semantics_refuses_an_ambiguous_term",
    "semantics_open_vocabulary",
    "scale_more_than_24_coordinates",
    "scale_precision_has_no_ceiling",
    "runtime_orders_two_reals",
    "runtime_answer_reruns_itself",
    "runtime_arithmetic_inside_a_describe",
)
