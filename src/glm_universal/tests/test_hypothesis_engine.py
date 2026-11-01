"""Tests for :mod:`glm_universal.reasoning.hypothesis_engine` -- the Rule 30
study's Hypothesis Engine v18, taken into the package (Phase 186).

*Created 1 November 2026 (Phase 186: the intake items absorbed where they
measurably help).*

The intake item's own tests (``glm_engine/test_hypothesis_engine.py``) run
against the supplied file; these run against the package module and pin the
edits its header declares:

* **The engine's self-test passes** in the package (the centre column, the
  linear-complexity profile, the diagonals, the arrow, the gates, typed
  rollback, the recogniser and the ARC solver's refusal rule).
* **Edit 4, no ``eval``**: :func:`safe_predicate` reads integer arithmetic,
  comparisons, the listed functions and generators over ``range``, and
  refuses names, attributes, calls of anything else, non-integer constants
  and an exponent above the bound -- without ever running the text; a
  reading with a work budget is stopped before the work that would exceed it.
* **Edit 3, no floats**: the module constructs no float (the package's
  exactness inventory, :mod:`glm_universal.reasoning.exactness`, holds it to
  that), and the Rule 30 domain's figures are integers and fractions.
* **The ledger decides "proved"**: without it the engine never answers a
  universal claim true; the gcd trap survives every read and is refuted only
  by its Lean theorem.
* **The general domain**: 10 of 10 right with the ledger, 0 wrong without.

Plain test functions (runnable by ``glm_universal.intake.fallback_tests``).
"""
from __future__ import annotations

from fractions import Fraction

from glm_universal.reasoning import hypothesis_engine as E


def test_the_engines_own_selftest():
    assert E.selftest() == 0


def test_the_rule_30_step():
    # new = left XOR (centre OR right) on a row held as an integer (bit i+1
    # is the left neighbour of bit i; the margin keeps the pattern above bit
    # 0): one black cell, then three, then 1 1 0 0 1.
    row = E.rule30_step(1 << 4)
    assert row == 0b111000
    assert E.rule30_step(row) == 0b1001100
    assert E.centre_bits(8) == [1, 1, 0, 1, 1, 1, 0, 0]


def test_safe_predicate_reads_arithmetic():
    f = E.safe_predicate("isprime(n**2 + n + 41)")
    assert f is not None and f(39) and not f(40)
    g = E.safe_predicate("all(n % d != 0 for d in range(2, n)) or n < 2")
    assert g is not None and g(13) and not g(15)
    h = E.safe_predicate("n / 2 == n // 2")             # exact division
    assert h is not None and h(4) and not h(5)


def test_safe_predicate_refuses_without_running():
    for text in ("__import__('os').system('true')", "n.__class__", "open('x')",
                 "eval('1')", "n == 0.5", "n ** 100000", "lambda: n", "[n for n in x]",
                 "n; n", "exec"):
        f = E.safe_predicate(text)
        if f is not None:
            # An exponent above the bound is refused when evaluated.
            try:
                f(2)
            except ValueError:
                continue
            raise AssertionError(f"{text!r} was evaluated")


def test_a_budgeted_reading_stops_before_the_work():
    budget = [10 ** 6]
    f = E.safe_predicate("n ** n > 0", budget=budget)
    assert f(5)                                       # cheap: within the budget
    try:
        f(60000)                                      # charged before it runs
    except E.WorkBound:
        pass
    else:
        raise AssertionError("the reading was not stopped")
    assert budget[0] < 0
    g = E.safe_predicate("n ** n > 0")                # no budget: no bound
    assert g(50)


def test_the_module_constructs_no_float():
    from glm_universal.reasoning import exactness as EX
    inv = EX.exactness_inventory()
    assert "reasoning/hypothesis_engine.py" not in inv["sites"]
    assert "reasoning/hypothesis_engine.py" not in inv["unclassified_modules"]


def test_only_the_ledger_says_proved():
    e = E.Engine(use_ledger=False)
    h = e.add(E.Hypothesis("", "GEN.gcd.trap", "gcd trap", "Pi1",
                           check=lambda N: (True, ""), scales=[1, 2, 3, 4, 5]))
    e.cascade(h)
    assert E.answer_of(h.status) is None
    e2 = E.Engine(use_ledger=True)
    h2 = e2.add(E.Hypothesis("", "GEN.gcd.trap", "gcd trap", "Pi1",
                             check=lambda N: (True, ""), scales=[1, 2, 3, 4, 5]))
    e2.cascade(h2)
    assert E.answer_of(h2.status) is False


def test_the_general_domain():
    _, with_ledger = E.run_general(use_ledger=True)
    _, without = E.run_general(use_ledger=False)
    assert with_ledger["score"]["right"] == with_ledger["score"]["n"] == 10
    assert with_ledger["score"]["wrong"] == 0
    assert without["score"]["wrong"] == 0 and without["score"]["overclaim"] == 0


def test_the_wobble_is_a_fraction():
    ratio, at = E.wobble_max_ratio(E.centre_bits(4000))
    assert isinstance(ratio, Fraction) and isinstance(at, int)
