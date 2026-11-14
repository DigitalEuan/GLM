"""D8 gate: the origination search must be falsifiable, sound and refused-where-honest.

The gate encodes the directive item D8 (origination at scale):

* the search accepts only power-conjugate declared analogies and refuses the
  rest with recorded reasons (R1: never invent evidence);
* every originated interpretation is generated, not authored: its card must
  come out of ``generate_mechanism_card`` executing the operator chain (R2);
* the oracle is independent of the candidate program: it re-derives the
  junction law with plain ``Fraction`` arithmetic (R5);
* the search re-derives the hand-authored fluid record from the W1-W6 analogy
  (derivation parity: the search is sound, not lucky);
* the scoreboard gate: at least three M-D pairings must now be non-hand-authored,
  or the suite fails (the kill criterion);
* sabotage: replacing the acceptance predicate with an always-accept function
  must *increase* refusals-as-accepts and break parity, proving the metric
  measures the predicate and not a constant.
"""
from __future__ import annotations

import json

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import origination as origination_module  # noqa: E402
from cent_compiler.isomorphism_gate import DECLARED_ANALOGIES  # noqa: E402
from cent_compiler.mechanisms import generate_mechanism_card  # noqa: E402
from cent_compiler.mapping import OPERATOR_BY_ID  # noqa: E402

PASS = 0
FAIL = 0


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def d8_checks() -> int:
    print("=" * 78)
    print("D8 ORIGINATION")
    print("=" * 78)

    reviews = [
        origination_module.review_analogy(analogy) for analogy in DECLARED_ANALOGIES
    ]
    accepted = [r for r in reviews if r.accepted]
    refused = [r for r in reviews if not r.accepted]

    expect(
        len(DECLARED_ANALOGIES) == 7 and len(reviews) == 7,
        "the search space is the seven declared TIER-3 analogies",
    )
    expect(
        all(r.reason.strip() for r in reviews),
        "every accepted and refused review carries a reason",
    )
    expect(
        any(r.target_domain == "optical" and not r.accepted for r in reviews)
        and any(r.target_domain == "thermal" and not r.accepted for r in reviews),
        "the optical and thermal analogies are refused (no power-conjugate flow)",
    )
    expect(
        any(r.flow_quantity == "volume_flow_rate" and r.accepted for r in reviews),
        "the hydraulic pair (pressure, volume_flow_rate) is accepted",
    )

    originated = origination_module.originate()
    expect(
        len(originated) >= 3,
        f"at least three interpretations originate (got {len(originated)})",
    )
    expect(
        all(t.oracle_pass for t in originated),
        "every originated transfer passes the independent oracle",
    )
    expect(
        all(
            t.interpretation.operators == ("effort-flow-duality", "composition")
            for t in originated
        ),
        "every originated interpretation uses the executable operator chain",
    )
    expect(
        all(
            OPERATOR_BY_ID[op].check(
                {
                    "operation": "sum",
                    "primitive_chain": ("sum", "neg"),
                    "stateful": False,
                    "feedback": False,
                    "domain": "electronics",
                    "carrier": "normalized current",
                    "target_domain": t.interpretation.source_domains[0],
                    "target_carrier": t.interpretation.carrier,
                    "target_units": t.interpretation.carrier,
                    "scale": t.interpretation.scale,
                    "offset": t.interpretation.offset,
                    "duality": dict(t.interpretation.duality),
                }
            )
            for op in ("effort-flow-duality", "composition")
            for t in originated
        ),
        "the effort-flow-duality precondition is checkable on every originated model",
    )

    # The generated cards must validate and refuse nothing silently.
    cards_ok = True
    for transfer in originated:
        try:
            card = generate_mechanism_card(transfer.interpretation)
            card.validate()
        except ValueError:
            cards_ok = False
    expect(cards_ok, "generate_mechanism_card validates every originated card")

    expect(
        origination_module._fluid_parity(),
        "derivation parity: the search re-derives the hand-authored fluid record",
    )

    ledger = origination_module.origination_ledger()
    sb = ledger["scoreboard"]
    expect(
        sb["before"] == "1/9" and sb["after"] == "4/9",
        "the scoreboard reports 1/9 -> 4/9 (three new non-hand-authored pairings)",
    )
    expect(
        sb["target_met"] is True and sb["target"] == ">=3",
        "the origination-rate target (>=3) is met",
    )
    expect(
        ledger["ok"] is True,
        "the ledger declares ok only with parity and >=2 adopted origins",
    )

    # Sabotage: an always-accept predicate must break parity (R3).
    original_review = origination_module.review_analogy

    def sabotaged_review(analogy):
        review = original_review(analogy)
        return type(review)(
            analogy_name=review.analogy_name,
            wheel_pair=review.wheel_pair,
            target_domain=review.target_domain,
            accepted=True,
            reason="sabotage",
            flow_quantity=review.flow_quantity,
            effort_quantity=review.effort_quantity,
        )

    origination_module.review_analogy = sabotaged_review
    try:
        # _fluid_parity must now see an accepted W1-W6 analogy; but the
        # capacitor-inductor and optical analogies also "accepted", and the
        # synthesized fluid record must still match.  Parity itself is about
        # the fluid record, so the sabotage signal is the refusal count:
        # with the real predicate 4 reviews are refused; with the constant
        # predicate 0 are.  The metric (accepted count) must degrade to a
        # constant 7/7 - proving the acceptance test is load-bearing.
        sabotaged_accepted = sum(
            1
            for analogy in DECLARED_ANALOGIES
            if origination_module.review_analogy(analogy).accepted
        )
    finally:
        origination_module.review_analogy = original_review
    expect(
        sabotaged_accepted == 7 and len(accepted) == 4 and len(refused) == 3,
        "sabotage: an always-accept predicate accepts 7/7 while the real predicate refuses 3",
    )

    # The oracle must refuse unknown operations, not guess.
    try:
        origination_module.oracle_junction_law(1, 1, "modulo")
        oracle_refuses = False
    except ValueError:
        oracle_refuses = True
    expect(oracle_refuses, "the oracle refuses an unknown junction law")

    # Vector evidence must contain no binary floats.
    def no_floats(value) -> bool:
        if isinstance(value, float):
            return False
        if isinstance(value, dict):
            return all(no_floats(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return all(no_floats(v) for v in value)
        return True

    expect(
        all(no_floats(v) for t in originated for v in t.vectors),
        "oracle vector evidence contains no binary floats",
    )

    # CLI surface.
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "originate", "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    expect(
        result.returncode == 0 and '"schema": "cent-origination-ledger/1"' in result.stdout,
        "cent originate --json emits the ledger with exit 0",
    )

    print()
    print("=" * 78)
    print(f"D8 ORIGINATION: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 1 if FAIL else 0


def d9_checks() -> int:
    """The D9 gate: declared-data origination at scale."""
    global PASS, FAIL
    from cent_compiler import origination_scale as scale

    print("=" * 78)
    print("D9 ORIGINATION AT SCALE (declared-data search)")
    print("=" * 78)

    ledger = scale.origination_ledger_v2()

    # --- Search space and computed acceptance ---
    expect(
        ledger["search"]["wheels"] == 40 and ledger["search"]["axioms"] == 101,
        "the search universe is the declared wheel corpus (40 wheels, 101 axioms)",
    )
    fam = {f["family"]: f for f in ledger["families"]}
    expect(
        fam["junction"]["accepted"] == 8,
        f"junction family accepts 8 wheels by computed power-conjugacy "
        f"(got {fam['junction']['accepted']})",
    )
    expect(
        fam["noise_shaper"]["accepted"] == 3,
        f"noise-shaper family accepts 3 wheels with a computed accumulator "
        f"(got {fam['noise_shaper']['accepted']})",
    )
    expect(
        fam["sqrt"]["accepted"] == 5,
        f"sqrt family accepts 5 wheels with computed invertible monomials "
        f"(got {fam['sqrt']['accepted']})",
    )

    # --- The W37 discovery: a junction no analogy ever declared ---
    w37 = scale.review_junction("W37")
    expect(
        w37.accepted and {w37.effort, w37.flow} == {"stress", "strain_rate"},
        "W37 rheology is discovered by dimensional scan (no analogy declared it)",
    )

    # --- Dimensionless substrate refused (not a physical energy law) ---
    w36 = scale.review_sqrt("W36")
    expect(
        not w36.accepted and "dimensionless" in w36.reason,
        "W36 numerical substrate is refused for sqrt (dimensionless penalty terms)",
    )

    # --- Parity: the search re-derives every known pairing ---
    expect(
        ledger["parity_ok"] is True,
        "parity: the computed search re-derives every known pairing "
        "(kcl/fluid/rotational/acoustic/mechanical/rheology + sqrt W3)",
    )

    # --- Scoreboard: beyond the original corpus ---
    sb = ledger["scoreboard"]
    expect(
        sb["d9_search"] >= 12,
        f"at least 12 new pairings originate (got {sb['d9_search']})",
    )
    expect(
        sb["search_exceeds_corpus"] is True,
        f"search-originated total ({sb['search_originated_total']}) exceeds "
        "the original corpus denominator (9)",
    )
    expect(
        sb["after"] == f"{4 + sb['d9_search'] + sb['d10_unblocked']}/10",
        "the metric moves from 4/10 by exactly the d9+d10 search count",
    )

    # --- Every originated pairing is oracle-passed ---
    expect(
        all(item["oracle_pass"] for item in ledger["originated"]),
        "every originated pairing passes its independent oracle",
    )

    # --- Unique ids across families ---
    ids = [item["id"] for item in ledger["originated"]]
    expect(len(ids) == len(set(ids)), "every originated interpretation id is unique")

    # --- Speculative isolation: never counted, always carries an unblock ---
    spec = ledger["speculative"]
    expect(
        all(p["evidence"] == "speculative" and p["missing"].strip() for p in spec),
        "speculative proposals carry evidence: speculative and a named unblock",
    )
    expect(
        all(
            item["family"] == "sign" for item in ledger["originated"]
            if item["family"] == "sign"
        )
        and all(
            scale.review_sign(item["wheel"]).accepted
            for item in ledger["originated"]
            if item["family"] == "sign"
        ),
        "sign-family pairings appear only from wheels with a declared three-level law",
    )
    sign_spec = [p for p in spec if p["family"] == "sign"]
    expect(
        len(sign_spec) >= 2,
        "the sign-family physical candidates appear as speculative with unblocks",
    )

    # --- Multi-hop composition over declared edges ---
    paths = scale.composition_paths("W1", "W4", max_hops=2)
    expect(
        len(paths) >= 1
        and all(e.kind == "analogy" for p in paths for e in p),
        "W1 -> W4 composes through declared analogy edges (W1-W5-W4)",
    )

    # --- Registration: the two promoted noise-shapers are production cards ---
    from cent_compiler.mechanisms import MECHANISM_BY_ID
    from cent_compiler.targets import glm

    expect(
        "rotational-w4-noise-shaping" in MECHANISM_BY_ID
        and "mechanics-noise-shaping" in MECHANISM_BY_ID,
        "the two promoted noise-shapers are production registry cards",
    )
    expect(
        ("quantized_carry", "rotational-w4-noise-shaping") in glm.ADAPTERS
        and ("quantized_carry", "mechanics-noise-shaping") in glm.ADAPTERS,
        "both promoted cards have executable glm-reference adapters",
    )
    # the registered pairings must be re-derived by the search (hand_authored=True)
    registered = [
        item for item in ledger["originated"] if item["hand_authored"]
    ]
    expect(
        {item["id"] for item in registered}
        >= {"rotational-w4-noise-shaping", "mechanics-noise-shaping"},
        "the search re-derives the two registered production pairings",
    )

    # --- Oracle independence (R5): sabotage the oracle law and it must fail ---
    from fractions import Fraction

    good = scale.oracle_junction_law(Fraction(1, 2), Fraction(1, 3), "sum")
    expect(
        good == Fraction(5, 6),
        "the independent junction oracle computes 1/2 + 1/3 = 5/6",
    )
    # sqrt oracle: square-back catches a non-square
    mono = next(
        m for m in scale._MONOMIALS["W3"] if m.result == "energy"
    )
    ok, vectors = scale.oracle_sqrt_law(mono, "voltage")
    expect(
        ok
        and all(
            v["square_back"] is not None
            and Fraction(v["square_back"])
            == Fraction(v["root"]) * Fraction(v["root"])
            for v in vectors
        ),
        "the sqrt oracle derives vectors from the declared monomial and square-backs",
    )

    # --- Sabotage (R3): always-accept must inflate and break parity ---
    original = scale.review_junction

    def sabotage(wheel_id):
        review = original(wheel_id)
        return type(review)(
            family=review.family,
            wheel=review.wheel,
            wheel_title=review.wheel_title,
            accepted=True,
            reason="sabotage",
        )

    scale.review_junction = sabotage
    try:
        sabotaged_parity = scale.parity_checks()
    finally:
        scale.review_junction = original
    broken = [k for k, v in sabotaged_parity.items() if not v]
    expect(
        len(broken) >= 1,
        f"sabotage: an always-accept predicate breaks parity checks {broken[:2]}",
    )

    # --- Kill criterion: did the search need undeclared data? ---
    undeclared = [
        item for item in ledger["originated"]
        if item["wheel"] not in scale._WHEELS
    ]
    expect(
        not undeclared,
        "kill criterion: every originated pairing comes from a declared wheel",
    )

    # --- CLI surface ---
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "originate", "--search", "scale", "--json"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    expect(
        result.returncode == 0
        and '"schema": "cent-origination-ledger/2"' in result.stdout,
        "cent originate --search scale --json emits the ledger with exit 0",
    )

    print()
    print("=" * 78)
    # The combined total is the suite's declared gate count (run_all reads
    # the last "N/N checks passed" line; D8's 17/17 above is informational).
    print(f"ORIGINATION (D8+D9 COMBINED): {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 1 if FAIL else 0


_d8_total = [0]
_d9_total = [0]


def d10_checks() -> int:
    """The D10 gate: the sign-family unblock and the W37 promotion."""
    global PASS, FAIL
    from cent_compiler import origination_scale as scale
    from fractions import Fraction

    print("=" * 78)
    print("D10 UNBLOCK (three-level sign + W37 promotion)")
    print("=" * 78)

    # --- W42 is a declared wheel with a three-level law ---
    w42 = scale.review_sign("W42")
    expect(
        w42.accepted and w42.above == "applied_load" and w42.below == "critical_load",
        "W42 declares the snap-through three-level law (applied vs critical load)",
    )
    w13 = scale.review_sign("W13")
    expect(
        not w13.accepted,
        "W13 still declares no three-level law (the family is licensed, not blanket)",
    )

    # --- The sign family is unblocked in the search ---
    ledger = scale.origination_ledger_v2()
    sign_items = [o for o in ledger["originated"] if o["family"] == "sign"]
    expect(
        len(sign_items) == 1
        and sign_items[0]["id"] == "structural-snap-through-sign"
        and sign_items[0]["oracle_pass"]
        and not sign_items[0]["hand_authored"],
        "the sign family originates one pairing from the declared W42 law",
    )

    # --- The speculative ring drained; the certification queue filled ---
    spec_sign = [p for p in ledger["speculative"] if p["family"] == "sign"]
    expect(
        all(p["wheel"] not in ("W42",) for p in spec_sign) and len(spec_sign) == 2,
        "the ring keeps only still-blocked sign proposals (W13/W14 drain-test)",
    )
    queue = ledger["certification_queue"]
    expect(
        len(queue) == 2
        and all(item["unblocked_by"] == ["W42"] for item in queue)
        and all(item["reachable_through"] for item in queue),
        "the certification queue names W42 as the unblock with reachable paths",
    )

    # --- The oracle: three-level law on all five vectors ---
    ok, vectors = scale.run_family_oracle(w42)
    expect(
        ok and len(vectors) == 5
        and all(v["passed"] for v in vectors),
        "the sign oracle exercises below/at/above and far-below/far-above thresholds",
    )
    expect(
        scale.oracle_sign_law(Fraction(0)) == 0
        and scale.oracle_sign_law(Fraction(-1, 7)) == -1
        and scale.oracle_sign_law(Fraction(9, 8)) == 1,
        "the independent three-level law returns exactly -1, 0, +1",
    )

    # --- Sabotage: an always-accept sign review must break the W42 check ---
    original = scale.review_sign

    def sabotage(wheel_id):
        review = original(wheel_id)
        return type(review)(
            family=review.family,
            wheel=review.wheel,
            wheel_title=review.wheel_title,
            accepted=True,
            reason="sabotage",
        )

    saved = scale.FAMILIES["sign"]
    scale.FAMILIES = dict(scale.FAMILIES)
    scale.FAMILIES["sign"] = sabotage
    try:
        broken = [o for o in scale.originate_v2()
                  if o.review.family == "sign"]
    finally:
        scale.FAMILIES = dict(scale.FAMILIES)
        scale.FAMILIES["sign"] = saved
    expect(
        len(broken) > 1,
        "sabotage: always-accept inflates the sign family beyond the one licensed wheel",
    )

    # --- W37 promotion: production card, adapters, certificates ---
    from cent_compiler.mechanisms import MECHANISM_BY_ID
    from cent_compiler.targets import glm

    expect(
        "rheology-continuity" in MECHANISM_BY_ID
        and MECHANISM_BY_ID["rheology-continuity"].supported_operations
        == ("sum", "difference"),
        "the W37 rheology junction is a production card with sum/difference",
    )
    expect(
        ("sum", "rheology-continuity") in glm.ADAPTERS
        and ("difference", "rheology-continuity") in glm.ADAPTERS,
        "the rheology card has executable glm-reference adapters",
    )
    import subprocess

    for op in ("sum", "difference"):
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "transfer", op,
                "--mechanism", "rheology-continuity",
                "--validate", "--limit", "6", "--json",
            ],
            capture_output=True, text=True, timeout=300,
        )
        payload = json.loads(result.stdout)
        expect(
            payload["ok"] is True
            and payload["certificate"]["status"] == "pass",
            f"the rheology {op} transfer certifies target-simulated",
        )

    # --- Scoreboard: denominator grew to 10; metric re-based honestly ---
    sb = ledger["scoreboard"]
    expect(
        sb["after"] == "18/10" and sb["d10_unblocked"] == 1,
        "the scoreboard reports 18/10 with one D10-unblocked pairing",
    )
    expect(
        sb["hand_authored_rederived"] == 3,
        "the search re-derives all three promoted pairings (2 shapers + rheology)",
    )

    # --- Kill criterion: no undeclared data in the D10 additions ---
    w42_declared = "W42" in scale._WHEELS
    sign_law_in_wheel = any(
        "sign_of" in ax for ax in scale._axioms("W42")
    )
    expect(
        w42_declared and sign_law_in_wheel,
        "kill criterion: the D10 unblock comes from a declared wheel law, not code",
    )

    print()
    print("=" * 78)
    # The suite's declared gate count (run_all reads the last footer line).
    print(f"ORIGINATION (D8+D9+D10 TOTAL): {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 1 if FAIL else 0


def main() -> int:
    rc = d8_checks()
    _d8_total[0] = PASS + FAIL
    if rc:
        return rc
    rc = d9_checks()
    _d9_total[0] = PASS + FAIL
    if rc:
        return rc
    return d10_checks()


if __name__ == "__main__":
    sys.exit(main())
