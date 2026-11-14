#!/usr/bin/env python3
"""Phase 0/1/3 tests for Cent transfer contracts and the seeded target.

Run without pytest: ``python3 tests/test_transfer_contracts.py``.

The schema/card tests do not claim a target transfer.  The target section below
executes the declared exact-rational ``glm-reference`` adapter and checks its
certificate.  It does not run a GLM model or claim GLM integration.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
from dataclasses import replace
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler.mechanisms import (  # noqa: E402
    MECHANISM_BY_ID,
    MECHANISM_CARDS,
    MechanismCard,
    get_mechanism,
    validate_mechanism_registry,
)
from cent_compiler.operation_contract import (  # noqa: E402
    OperationContract,
    OperationTest,
)
from cent_compiler.transfer import (  # noqa: E402
    MappingStep,
    RelaxationRecord,
    TargetProfile,
    TransferCandidate,
)
from cent_compiler.exact import (  # noqa: E402
    div as exact_div,
    mul as exact_mul,
    reciprocal as exact_reciprocal,
    sign as exact_sign,
)
from cent_compiler.interval import exp_q, log_q  # noqa: E402
from cent_compiler import assembly  # noqa: E402
from cent_compiler import transfer_engine  # noqa: E402
from cent_compiler import transfer_validation  # noqa: E402
from cent_compiler import proposals as proposal_module  # noqa: E402
from cent_compiler import proposal_trial as trial_module  # noqa: E402
from cent_compiler.targets import glm as glm_target  # noqa: E402

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


def _raises(call, needle: str) -> bool:
    try:
        call()
    except ValueError as exc:
        return needle in str(exc)
    return False


def _roundtrip(record):
    payload = json.loads(json.dumps(record.as_dict(), sort_keys=True))
    loaded = type(record).from_dict(payload)
    loaded.validate()
    return loaded, payload


SQRT = OperationContract(
    id="sqrt",
    name="square root",
    signature={
        "inputs": {"x": "nonnegative rational"},
        "outputs": {"y": "nonnegative rational or certified enclosure"},
    },
    semantics="y is the nonnegative value with y^2 = x.",
    reference={
        "kind": "exact-interval",
        "expression": "y = sqrt(x)",
        "path": "cent_compiler.interval",
    },
    tolerance="1/1000000000",
    tests=(
        OperationTest(
            id="sqrt-four",
            kind="exact",
            inputs={"x": "4"},
            expected="2",
            tolerance="0",
            provenance=("tests/test_core.py",),
            note="exact perfect square",
        ),
    ),
    target_constraints={"targets": ["physical", "glm"], "input": "nonnegative"},
    provenance=("cent_compiler/interval.py", "tests/test_core.py"),
    gaps=("no GLM target adapter yet",),
)

QUANTIZED_CARRY = OperationContract(
    id="quantized_carry",
    name="quantized carry",
    signature={
        "inputs": {"x": "scalar in the declared range"},
        "outputs": {"code": "bounded bitstream or code"},
    },
    semantics="Carry a scalar as a bounded code with a declared reconstruction.",
    reference={
        "kind": "declared-loop",
        "description": "first-order error-feedback loop declared in assembly.py",
        "path": "cent_compiler/assembly.py",
    },
    tolerance="1/100",
    tests=(
        OperationTest(
            id="reconstruct-one-third",
            kind="numerical",
            inputs={"x": "1/3"},
            expected="1/3",
            tolerance="1/100",
            provenance=("cent_compiler/assembly.py",),
        ),
    ),
    target_constraints={"targets": ["glm"], "precision": "declared"},
    provenance=("cent_compiler/assembly.py", "docs/DELTA_SIGMA_DEMO.md"),
    gaps=("no GLM target API or target test yet",),
)

SUM = OperationContract(
    id="sum",
    name="sum",
    signature={
        "inputs": {"x": "rational", "z": "rational"},
        "outputs": {"y": "rational"},
    },
    semantics="y = x + z under the exact KCL route.",
    reference={
        "kind": "exact-route",
        "expression": "y = x + z",
        "path": "cent_compiler/assembly.py",
    },
    tolerance="0",
    tests=(
        OperationTest(
            id="sum-five-sixths",
            kind="exact",
            inputs={"x": "1/2", "z": "1/3"},
            expected="5/6",
            tolerance="0",
            provenance=("tests/test_assembly.py",),
        ),
    ),
    target_constraints={"targets": ["physical", "glm"]},
    provenance=("cent_compiler/assembly.py", "tests/test_assembly.py"),
    gaps=("physical KCL units and fabrication evidence are not declared",),
)

DELTA = MechanismCard(
    id="delta-sigma-error-feedback",
    name="delta-sigma error feedback",
    principle="quantize the accumulated error and feed the code back",
    source_domains=("audio", "electronics"),
    supported_operations=("quantized_carry",),
    primitive_chain=("accum", "quantize", "sum"),
    carrier="bitstream",
    stateful=True,
    invariants=("bounded loop state", "first-moment reconstruction"),
    laws=("declared first-order loop in cent_compiler/assembly.py",),
    validity=("declared input range", "stable loop"),
    failure_modes=("overload", "limit cycle"),
    evidence_level="source-simulated",
    provenance=("cent_compiler/assembly.py", "docs/DELTA_SIGMA_DEMO.md"),
    gaps=("no GLM target adapter or target test yet",),
)

KCL = MechanismCard(
    id="kcl-conservation",
    name="KCL conservation",
    principle="sum currents at a node and preserve the declared effort",
    source_domains=("electronics",),
    supported_operations=("sum", "difference"),
    primitive_chain=("sum", "neg"),
    carrier="voltage",
    stateful=False,
    invariants=("signed current sum", "declared exact result"),
    laws=("KCL junction law with declared exact negate glue",),
    validity=("two declared rational inputs", "normalized KCL route"),
    failure_modes=("physical source/load impedance not declared",),
    evidence_level="source-simulated",
    provenance=("cent_compiler/assembly.py", "docs/PHYSICAL_NETLIST.md"),
    gaps=("physical voltage/current mapping is not declared",),
)

CAM = MechanismCard(
    id="cam-profile",
    name="mechanical cam profile",
    principle="shape a spatial profile so displacement realizes a declared law",
    source_domains=("mechanical",),
    supported_operations=("sqrt",),
    primitive_chain=("spatial", "scale"),
    carrier="position",
    stateful=False,
    invariants=("declared input range", "profile displacement law"),
    laws=("declared shaped-profile cam law in the substrate library",),
    validity=("fixed profile", "declared operating range"),
    failure_modes=("wear", "manufacturing profile error"),
    evidence_level="structural",
    provenance=("cent_compiler/substrate_library.py",),
    gaps=("no exact cam solver or fabricated profile",),
)

GENERIC_MULT = MechanismCard(
    id="generic-scalar-multiplier",
    name="generic scalar multiplier",
    principle="apply a scalar product",
    source_domains=("electrical", "mechanical"),
    supported_operations=("mult",),
    primitive_chain=("mult",),
    carrier="scalar",
    stateful=False,
    invariants=("scalar bilinearity",),
    laws=("declared scalar product only",),
    validity=("scalar inputs",),
    failure_modes=("no vector or tensor shape contract",),
    evidence_level="structural",
    provenance=("cent_compiler/substrate_library.py",),
    gaps=("no vector, matrix or tensor contract",),
)

TRANSFER_DELTA = TransferCandidate(
    id="quantized-carry-delta-sigma",
    operation="quantized_carry",
    mechanism="delta-sigma-error-feedback",
    source_domain="audio/electronics",
    target="glm-reference",
    mapping=(
        MappingStep(
            "normalized scalar input",
            "normalized numerical input",
            "the declared input range maps to the target range",
            "variable",
            ("cent_compiler/assembly.py",),
        ),
        MappingStep(
            "comparator code",
            "±1 code",
            "the declared quantizer levels map to the target code",
            "quantization",
            ("cent_compiler/assembly.py",),
        ),
        MappingStep(
            "loop state",
            "numerical accumulator",
            "state carries the accumulated error",
            "state",
            ("cent_compiler/assembly.py",),
        ),
        MappingStep(
            "mean code",
            "scalar estimate",
            "declared reconstruction maps the code sequence to a scalar",
            "variable",
            ("cent_compiler/assembly.py",),
        ),
    ),
    preserved=("bounded state", "error feedback", "first-moment reconstruction"),
    relaxed=("analog voltage range", "clock jitter", "thermal noise"),
    validity=("declared input range", "stable loop"),
    evidence_level="structural",
    gaps=("no GLM target adapter or target test yet",),
    provenance=("cent_compiler/assembly.py", "docs/DELTA_SIGMA_DEMO.md"),
)

TRANSFER_KCL = TransferCandidate(
    id="sum-kcl-to-glm",
    operation="sum",
    mechanism="kcl-conservation",
    source_domain="electronics",
    target="glm-reference",
    mapping=(
        MappingStep(
            "input current",
            "numeric input",
            "declared rational input maps to a normalized target input",
            "variable",
            ("cent_compiler/assembly.py",),
        ),
    ),
    preserved=("exact sum", "declared input count"),
    relaxed=("physical current/voltage units",),
    validity=("declared normalized inputs",),
    evidence_level="source-simulated",
    gaps=("no target adapter test yet",),
    provenance=("cent_compiler/assembly.py",),
)

NEGATIVE_GRIESS = TransferCandidate(
    id="negative-griess-scalar-multiplier",
    operation="griess_product",
    mechanism="generic-scalar-multiplier",
    source_domain="electrical",
    target="glm-reference",
    mapping=(
        MappingStep(
            "scalar input",
            "scalar input",
            "scalar multiplication only",
            "variable",
            ("docs/GLM_CENT_APPLICATION_AUDIT.md",),
        ),
    ),
    preserved=("scalar product",),
    relaxed=(),
    validity=("scalar inputs only",),
    evidence_level="proposed",
    gaps=("no Griess multiplication tensor is declared",),
    provenance=("docs/GLM_CENT_APPLICATION_AUDIT.md",),
)

GLM_TARGET = TargetProfile(
    id="glm-reference",
    kind="software",
    description="reference adapter contract for GLM-style scalar operations",
    interface={"input": "json", "output": "json", "precision": "declared"},
    constraints={"no GLM performance claim": True},
    evidence_required=("reference-test", "adapter-artifact"),
    provenance=("docs/TRANSFER_COMPILER_OBJECTIVE.md",),
    gaps=("no real GLM interface is connected",),
)


def main() -> int:
    print("=" * 78)
    print("TRANSFER CONTRACTS AND MECHANISM REGISTRY")
    print("=" * 78)

    operation, operation_payload = _roundtrip(SQRT)
    expect(
        operation.as_dict() == operation_payload
        and operation_payload["schema"] == "cent-operation/1",
        "a sqrt operation contract round-trips through JSON",
    )
    expect(
        _raises(lambda: replace(SQRT, tests=()).validate(), "tests"),
        "an operation without a reference test is rejected",
    )
    expect(
        _raises(lambda: replace(SQRT, provenance=()).validate(), "provenance"),
        "an operation without provenance is rejected",
    )

    card, card_payload = _roundtrip(DELTA)
    expect(
        card.as_dict() == card_payload
        and card_payload["schema"] == "cent-mechanism/1",
        "a delta-sigma mechanism card round-trips through JSON",
    )
    expect(
        _raises(
            lambda: replace(DELTA, primitive_chain=("not_a_primitive",)).validate(),
            "unknown primitive",
        ),
        "a mechanism with an unknown primitive is rejected",
    )
    expect(
        _raises(lambda: replace(DELTA, provenance=()).validate(), "provenance"),
        "a mechanism without provenance is rejected",
    )

    transfer, transfer_payload = _roundtrip(TRANSFER_DELTA)
    valid_transfer = True
    try:
        transfer.validate(mechanism=DELTA)
    except ValueError:
        valid_transfer = False
    expect(
        valid_transfer
        and transfer.as_dict() == transfer_payload
        and transfer_payload["schema"] == "cent-transfer/1"
        and transfer_payload["status"] == "candidate",
        "a delta-sigma → GLM candidate round-trips and remains a candidate",
    )
    expect(
        transfer_payload["relaxation"]["schema"] == "cent-relaxation/1"
        and transfer_payload["relaxation"]["classification"] == "unclassified"
        and transfer_payload["relaxation"]["evidence_level"] == "none"
        and transfer_payload["relaxation"]["target"] == ""
        and transfer_payload["relaxation"]["basis"],
        "candidate-only transfers default to unclassified relaxation with a basis",
    )
    expect(
        _raises(
            lambda: replace(
                TRANSFER_DELTA, evidence_level="target-simulated"
            ).validate(),
            "target evidence",
        ),
        "target-simulated evidence without an artifact and tests is rejected",
    )
    expect(
        _raises(
            lambda: replace(TRANSFER_DELTA, status="validated").validate(),
            "target evidence",
        ),
        "a validated transfer without an artifact and tests is rejected",
    )
    expect(
        _raises(
            lambda: replace(
                TRANSFER_DELTA,
                relaxation=replace(
                    transfer.relaxation,
                    classification="exact",
                    basis="declared exact mapping",
                    evidence_level="target-simulated",
                    target="",
                ),
            ).validate(mechanism=DELTA),
            "relaxation.target",
        )
        and _raises(
            lambda: replace(
                TRANSFER_DELTA,
                relaxation=replace(
                    transfer.relaxation,
                    classification="exact",
                    basis="",
                    evidence_level="target-simulated",
                    target="glm-reference",
                ),
            ).validate(mechanism=DELTA),
            "relaxation.basis",
        )
        and _raises(
            lambda: replace(
                TRANSFER_DELTA,
                relaxation=replace(
                    transfer.relaxation,
                    classification="near-exact",
                    basis="declared exact mapping",
                    evidence_level="target-simulated",
                    target="glm-reference",
                ),
            ).validate(mechanism=DELTA),
            "relaxation.classification",
        )
        and _raises(
            lambda: replace(
                TRANSFER_DELTA,
                relaxation=replace(
                    transfer.relaxation,
                    classification="exact",
                    basis="declared exact mapping",
                    evidence_level="source-simulated",
                    target="glm-reference",
                ),
            ).validate(mechanism=DELTA),
            "target-simulated or target-integrated",
        )
        and _raises(
            lambda: replace(
                TRANSFER_DELTA,
                relaxation=replace(
                    transfer.relaxation,
                    classification="exact",
                    basis="declared exact mapping",
                    evidence_level="target-simulated",
                    target="glm-reference",
                ),
            ).validate(mechanism=DELTA),
            "target artifact and at least one target test",
        ),
        "classified relaxation rejects missing target, basis, target evidence, artifact or unknown class",
    )

    kcl_operation, _ = _roundtrip(SUM)
    cam_card, _ = _roundtrip(CAM)
    target_profile, target_payload = _roundtrip(GLM_TARGET)
    expect(
        kcl_operation.id == "sum"
        and cam_card.id == "cam-profile"
        and target_profile.id == "glm-reference"
        and target_payload["schema"] == "cent-target/1",
        "the KCL, cam and target-profile fixtures round-trip",
    )

    negative_griess = replace(NEGATIVE_GRIESS, operation="griess_product")
    negative_matrix = replace(NEGATIVE_GRIESS, operation="matrix_vector_product")
    expect(
        _raises(
            lambda: negative_griess.validate(mechanism=GENERIC_MULT),
            "does not support",
        )
        and _raises(
            lambda: negative_matrix.validate(mechanism=GENERIC_MULT),
            "does not support",
        ),
        "a generic scalar multiplier is rejected for Griess and matrix-vector operations",
    )

    json.dumps(
        [record.as_dict() for record in (SQRT, SUM, DELTA, KCL, CAM, TRANSFER_DELTA, GLM_TARGET)],
        sort_keys=True,
    )
    expect(
        all(
            isinstance(record.as_dict(), dict)
            for record in (SQRT, SUM, DELTA, KCL, CAM, TRANSFER_DELTA, GLM_TARGET)
        ),
        "all Phase 0 records are JSON-serialisable mappings",
    )

    registry_ids = [card.id for card in MECHANISM_CARDS]
    expect(
        len(MECHANISM_CARDS) == 13
        and len(MECHANISM_BY_ID) == 13
        and len(set(registry_ids)) == 13
        and get_mechanism("fluid-continuity").source_domains == ("fluidics",)
        and get_mechanism("fluid-continuity").supported_operations
        == ("sum", "difference")
        and get_mechanism("opamp-summing").source_domains == ("electronics",)
        and get_mechanism("opamp-summing").supported_operations
        == ("sum", "difference")
        and get_mechanism("log-domain-arithmetic").principle_id
        == "transcendental-identity"
        and get_mechanism("log-domain-arithmetic").supported_operations
        == ("exp", "log", "mult", "div", "reciprocal")
        and get_mechanism("threshold-comparator").supported_operations
        == ("sign",),
        "the registry seeds thirteen unique mechanism cards (ten authored plus three originated: two D9 noise shapers, one D10 rheology junction)",
    )
    registry_valid = True
    try:
        validate_mechanism_registry()
    except ValueError:
        registry_valid = False
    expect(registry_valid, "every seeded mechanism card validates")
    expect(
        all(card.provenance for card in MECHANISM_CARDS),
        "every seeded mechanism card carries provenance",
    )
    expect(
        all(card.gaps for card in MECHANISM_CARDS),
        "every seeded mechanism card names at least one first gap",
    )
    expect(
        all(
            card.evidence_level
            in {"proposed", "structural", "admissible", "source-simulated"}
            for card in MECHANISM_CARDS
        ),
        "no seeded mechanism card claims target evidence",
    )

    delta_card = get_mechanism("delta-sigma-error-feedback")
    expect(
        delta_card.primitive_chain
        == ("neg", "sum", "accum", "quantize", "sat", "delay")
        and delta_card.supported_operations == ("quantized_carry",)
        and "feedback = delayed level" in delta_card.laws[0],
        "the delta-sigma card copies the exact route chain and feedback law",
    )

    log_card = get_mechanism("log-domain-sqrt")
    expect(
        log_card.primitive_chain == ("log", "scale", "exp")
        and log_card.supported_operations == ("sqrt",)
        and "exp((1/2)" in log_card.laws[0],
        "the log-domain card copies the log/scale/exp route",
    )

    kcl_card = get_mechanism("kcl-conservation")
    expect(
        kcl_card.primitive_chain == ("sum", "neg")
        and set(kcl_card.supported_operations) == {"sum", "difference"}
        and "total = a + b" in kcl_card.laws[0],
        "the KCL card copies the exact sum/difference junction law",
    )

    cam_card = get_mechanism("cam-profile")
    orifice_card = get_mechanism("orifice-pressure-flow")
    expect(
        cam_card.evidence_level == "structural"
        and orifice_card.evidence_level == "structural"
        and cam_card.primitive_chain == ("spatial",)
        and orifice_card.primitive_chain == ("mult", "eq")
        and any("no exact" in gap for gap in cam_card.gaps)
        and any("no exact" in gap for gap in orifice_card.gaps),
        "the cam and orifice cards stay structural and expose their missing solvers",
    )

    pll_card = get_mechanism("pll-phase-tracking")
    expect(
        pll_card.stateful
        and pll_card.carrier == "phase"
        and "sin(phi_ref - phi_vco)" in pll_card.laws[0]
        and "cycle slip" in " ".join(pll_card.failure_modes),
        "the PLL card copies the declared phase detector and lock limits",
    )

    registry_roundtrip = True
    for card in MECHANISM_CARDS:
        payload = json.loads(json.dumps(card.as_dict(), sort_keys=True))
        reloaded = MechanismCard.from_dict(payload)
        reloaded.validate()
        registry_roundtrip = registry_roundtrip and reloaded.as_dict() == payload
    expect(
        registry_roundtrip,
        "all ten seeded mechanism cards round-trip through JSON",
    )

    operations = transfer_engine.OPERATION_CONTRACTS
    expect(
        len(operations) == 10
        and set(transfer_engine.OPERATION_BY_ID)
        == {
            "sqrt", "sum", "difference", "quantized_carry",
            "mult", "div", "exp", "log", "reciprocal", "sign",
        }
        and all(operation.tests for operation in operations),
        "the G5a registry exposes ten tested operation contracts",
    )
    new_operation_ids = {"mult", "div", "exp", "log", "reciprocal", "sign"}
    new_operations = [transfer_engine.get_operation(item) for item in new_operation_ids]
    expect(
        all(
            operation.reference.get("path")
            in {"cent_compiler/exact.py", "cent_compiler/interval.py"}
            and operation.gaps
            for operation in new_operations
        )
        and exact_mul(Fraction(3, 4), Fraction(2, 3)) == Fraction(1, 2)
        and exact_div(Fraction(1, 2), Fraction(3, 4)) == Fraction(2, 3)
        and exact_reciprocal(Fraction(3, 4)) == Fraction(4, 3)
        and exact_sign(Fraction(-5, 2)) == -1
        and exp_q(0).lo == 1
        and log_q(1).lo == 0,
        "the six new contracts name exact/certified references, fixed tests and explicit evidence gaps",
    )
    sign_payload = transfer_engine.transfer_payload("sign")
    expect(
        sign_payload["summary"]["candidates"] == 3
        and sign_payload["summary"]["candidate_only"] is True
        and sign_payload["checks"][0]["status"] == "pass"
        and sign_payload["summary"]["mechanisms"][0] == "threshold-comparator"
        and sign_payload["operation"]["target_constraints"]["targets"]
        == ["glm-reference"]
        and "reference-adapter-implemented"
        in sign_payload["operation"]["target_constraints"]["target_validation"]
        and not any(
            "no declared target adapter" in gap
            for gap in sign_payload["operation"]["gaps"]
        ),
        "sign exposes a top-ranked comparator candidate and a declared reference adapter",
    )
    sign_validation = transfer_validation.validate_transfer("sign")
    expect(
        sign_validation["ok"] is True
        and sign_validation["validated_candidate"]["mechanism"]
        == "threshold-comparator"
        and sign_validation["metrics"]
        == {"vectors": 3, "passed": 3}
        and all(row["passed"] for row in sign_validation["vectors"]),
        "the sign reference adapter passes the negative, zero and positive fixed vectors",
    )

    sqrt_operation, sqrt_target, sqrt_candidates, sqrt_matches = transfer_engine.retrieve("sqrt")
    expect(
        sqrt_operation.id == "sqrt"
        and sqrt_target.id == "glm-reference"
        and len(sqrt_candidates) == 3
        and [candidate.mechanism for candidate in sqrt_candidates]
        == ["log-domain-sqrt", "cam-profile", "fluid-continuity"]
        and {candidate.source_domain for candidate in sqrt_candidates}
        == {"electronics", "mechanical", "fluidics"}
        and [candidate.rank for candidate in sqrt_candidates] == [1, 2, 3],
        "sqrt retrieves the top three structural candidates, including unlabelled ones",
    )

    quantized_operation, _quantized_target, quantized_candidates, quantized_matches = transfer_engine.retrieve("quantized_carry")
    quantized_match = quantized_matches[quantized_candidates[0].id]
    expect(
        quantized_operation.id == "quantized_carry"
        and len(quantized_candidates) == 3
        and quantized_candidates[0].mechanism == "delta-sigma-error-feedback"
        and any("primitive overlap" in reason for reason in quantized_match["reasons"])
        and any("stateful true match" in reason for reason in quantized_match["reasons"])
        and any("feedback true match" in reason for reason in quantized_match["reasons"])
        and quantized_candidates[0].rank == 1,
        "delta-sigma ranks first by primitive/state/feedback features, not a name branch",
    )

    sum_candidates = transfer_engine.retrieve("sum")[2]
    difference_candidates = transfer_engine.retrieve("difference")[2]
    expect(
        len(sum_candidates) == 3
        and len(difference_candidates) == 3
        and {candidate.mechanism for candidate in sum_candidates}
        == {"kcl-conservation", "fluid-continuity", "opamp-summing"}
        and {candidate.mechanism for candidate in difference_candidates}
        == {"kcl-conservation", "fluid-continuity", "opamp-summing"}
        and any(
            "signed current sum" in item
            for candidate in sum_candidates
            if candidate.mechanism == "kcl-conservation"
            for item in candidate.preserved
        )
        and any(
            "signed flow sum" in item
            for candidate in sum_candidates
            if candidate.mechanism == "fluid-continuity"
            for item in candidate.preserved
        ),
        "sum and difference each retrieve all three declared exact source domains",
    )

    all_candidates = (*sqrt_candidates, *quantized_candidates, *sum_candidates, *difference_candidates)
    expect(
        all(
            candidate.status == "candidate"
            and candidate.artifact is None
            and candidate.tests == ()
            and candidate.mapping
            and candidate.gaps
            and candidate.evidence_level in {"structural", "source-simulated"}
            and candidate.relaxation.classification == "unclassified"
            for candidate in all_candidates
        ),
        "every retrieval result remains an unvalidated candidate with a first gap",
    )

    unknown_operations = 0
    for operation_id in ("griess_product", "matrix_vector_product"):
        try:
            transfer_engine.transfer_payload(operation_id)
        except KeyError:
            unknown_operations += 1
    expect(
        unknown_operations == 2,
        "unknown Griess and matrix-vector operations are refused, not overmatched",
    )

    expect(
        transfer_engine.get_target_profile("glm-reference").id == "glm-reference"
        and len(transfer_engine.MAPPING_OPERATORS) == 7
        and set(transfer_engine.OPERATION_BEHAVIORS) == set(transfer_engine.OPERATION_BY_ID)
        and set(transfer_engine.MECHANISM_BEHAVIORS) == set(transfer_engine.MECHANISM_BY_ID),
        "the target, behavior tables and mapping operators are declared and aligned",
    )

    payload = transfer_engine.transfer_payload("sqrt")
    rendered = transfer_engine.render_transfer(payload)
    expect(
        payload["schema"] == transfer_engine.RESULT_SCHEMA
        and payload["summary"]["candidate_only"] is True
        and payload["summary"]["candidates"] == 3
        and payload["gaps"]
        and "TRANSFER RETRIEVAL" in rendered
        and "relaxation: unclassified" in rendered
        and "No target artifact" in rendered
        and json.dumps(payload, ensure_ascii=False),
        "the transfer payload and renderer preserve the no-target-claim boundary",
    )

    cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sqrt",
            "--target", "glm-reference", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == transfer_engine.RESULT_SCHEMA
        and len(cli_payload.get("candidates") or ()) == 3
        and (cli_payload.get("output_certificate") or {}).get("subject_schema")
        == transfer_engine.RESULT_SCHEMA,
        "cent transfer --json emits the candidate payload and certificate envelope",
    )

    human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "transfer", "quantized_carry"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    unknown = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "transfer", "griess_product"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        human.returncode == 0
        and "TRANSFER RETRIEVAL" in human.stdout
        and "delta-sigma-error-feedback" in human.stdout
        and unknown.returncode == 2
        and "unknown operation contract" in unknown.stderr,
        "the transfer CLI renders candidates and refuses an undeclared operation",
    )

    target_profile = glm_target.GLM_REFERENCE_TARGET
    expect(
        target_profile.id == "glm-reference"
        and set(target_profile.interface.get("operations") or ())
        == {"quantized_carry", "sum", "difference", "sqrt", "exp", "log", "mult", "div", "reciprocal", "sign"}
        and "quantized_carry" in (target_profile.interface.get("interfaces") or {})
        and target_profile.constraints.get("no_real_glm_interface") is True
        and target_profile.constraints.get("no_binary_float") is True
        and any("no real GLM" in gap for gap in target_profile.gaps),
        "the glm-reference target declares exact inputs, state and its no-integration boundary",
    )

    adapter = glm_target.get_adapter(
        "quantized_carry", "delta-sigma-error-feedback"
    )
    expect(
        adapter.entrypoint == "delta_sigma_quantized_carry"
        and adapter.path == "cent_compiler/targets/glm.py"
        and callable(adapter.function)
        and len(adapter.vectors) == 3,
        "the declared target adapter exposes an executable entrypoint and three fixed vectors",
    )

    half = glm_target.delta_sigma_quantized_carry(Fraction(1, 2), samples=12)
    expect(
        half.code == (1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0)
        and half.mean == Fraction(1, 2)
        and half.error == 0
        and half.peak_state == 1
        and half.bounded
        and half.passed,
        "the target reproduces the exact half-scale code, mean and bounded state",
    )

    parity = True
    for vector in glm_target.FIXED_VECTORS:
        route = assembly.delta_sigma_route(
            quantum=vector.quantum,
            full_scale=vector.full_scale,
            integrator_limit=vector.integrator_limit,
        )
        source = route.simulate(vector.x, samples=vector.samples)
        target = glm_target.delta_sigma_quantized_carry(
            vector.x,
            samples=vector.samples,
            quantum=vector.quantum,
            full_scale=vector.full_scale,
            integrator_limit=vector.integrator_limit,
        )
        source_code = tuple(
            int(item["level"] / vector.quantum) for item in source.trace
        )
        parity = parity and (
            source_code == target.code == vector.expected_code
            and source.mean == target.mean == vector.expected_mean
            and source.passed
        )
    expect(
        parity,
        "all three fixed vectors match the exact source route code and mean",
    )

    baseline = glm_target.uniform_quantizer_carry(
        Fraction(1, 2), samples=4
    )
    four_tick = glm_target.delta_sigma_quantized_carry(
        Fraction(1, 2), samples=4
    )
    expect(
        baseline.mean == 1
        and four_tick.mean == Fraction(3, 4)
        and abs(four_tick.error) < abs(baseline.error),
        "the delta-sigma target beats the stateless uniform-quantizer baseline",
    )

    too_small = glm_target.delta_sigma_quantized_carry(
        Fraction(1, 2), samples=12, integrator_limit=Fraction(1, 2)
    )
    expect(
        too_small.peak_state == 1
        and too_small.bounded is False
        and too_small.passed is False,
        "a too-small state limit fails explicitly instead of being widened",
    )

    rejected = 0
    for call in (
        lambda: glm_target.delta_sigma_quantized_carry(Fraction(-1, 10)),
        lambda: glm_target.delta_sigma_quantized_carry(
            Fraction(1, 2), samples=0
        ),
        lambda: glm_target.delta_sigma_quantized_carry(
            Fraction(2), full_scale=Fraction(1)
        ),
        lambda: glm_target.delta_sigma_quantized_carry(
            Fraction(1, 2), quantum=Fraction(2), full_scale=Fraction(1)
        ),
    ):
        try:
            call()
        except ValueError:
            rejected += 1
    expect(
        rejected == 4,
        "the target rejects out-of-range, zero-sample and invalid quantizer settings",
    )

    validation = transfer_validation.validate_transfer("quantized_carry")
    certificate = validation.get("certificate") or {}
    expect(
        validation.get("schema") == transfer_validation.VALIDATION_SCHEMA
        and certificate.get("schema") == transfer_validation.CERTIFICATE_SCHEMA
        and certificate.get("status") == "pass"
        and certificate.get("evidence_level") == "target-simulated"
        and len(validation.get("checks") or ()) == 10
        and all(
            check.get("status") == "pass"
            for check in validation.get("checks") or ()
        )
        and validation.get("metrics", {}).get("vectors") == 3,
        "the executable validator emits a passing target-simulated certificate",
    )

    reviewed = validation.get("validated_candidate") or {}
    expect(
        reviewed.get("status") == "validated"
        and reviewed.get("evidence_level") == "target-simulated"
        and (reviewed.get("artifact") or {}).get("entrypoint")
        == "delta_sigma_quantized_carry"
        and reviewed.get("tests") == ["half-12", "third-8", "two-fifths-12"]
        and any("no real GLM" in gap for gap in reviewed.get("gaps") or ())
        and not any(
            "not implemented" in gap for gap in reviewed.get("gaps") or ()
        )
        and (reviewed.get("relaxation") or {}).get("classification")
        == "unclassified"
        and (reviewed.get("relaxation") or {}).get("basis"),
        "the validated candidate carries the artifact, tests and remaining target gaps",
    )

    sum_validation = transfer_validation.validate_transfer(
        "sum", mechanism_id="kcl-conservation"
    )
    sum_reviewed = sum_validation.get("validated_candidate") or {}
    sum_relaxation = sum_reviewed.get("relaxation") or {}
    expect(
        sum_validation.get("status") == "pass"
        and sum_relaxation.get("classification") == "exact"
        and sum_relaxation.get("evidence_level") == "target-simulated"
        and sum_relaxation.get("target") == "glm-reference"
        and sum_relaxation.get("basis"),
        "validated exact KCL carries a target-backed exact relaxation record",
    )

    retrieval = transfer_engine.transfer_payload("quantized_carry")
    expect(
        retrieval.get("candidates")
        and retrieval["candidates"][0].get("status") == "candidate"
        and retrieval["candidates"][0].get("artifact") is None
        and retrieval["candidates"][0].get("tests") == []
        and (retrieval["candidates"][0].get("relaxation") or {}).get(
            "classification"
        ) == "unclassified",
        "target validation does not mutate the candidate-only retrieval view",
    )

    refused = 0
    for operation, mechanism in (("sqrt", "cam-profile"), ("griess_product", None)):
        try:
            transfer_validation.validate_transfer(
                operation, mechanism_id=mechanism
            )
        except (ValueError, KeyError):
            refused += 1
    expect(
        refused == 2,
        "target validation refuses an undeclared mechanism and an unknown operation",
    )

    validation_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "quantized_carry",
            "--validate", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    validation_payload = (
        json.loads(validation_cli.stdout) if validation_cli.returncode == 0 else {}
    )
    validation_human = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "quantized_carry",
            "--validate",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    validation_refusal = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sqrt",
            "--target", "glm-live", "--validate",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        validation_cli.returncode == 0
        and validation_payload.get("schema") == transfer_validation.VALIDATION_SCHEMA
        and (validation_payload.get("certificate") or {}).get("status") == "pass"
        and (validation_payload.get("output_certificate") or {}).get("subject_schema")
        == transfer_validation.VALIDATION_SCHEMA
        and validation_human.returncode == 0
        and "TRANSFER TARGET VALIDATION" in validation_human.stdout
        and "uniform quantizer baseline" in validation_human.stdout
        and validation_refusal.returncode == 2
        and "no executable target adapter" in validation_refusal.stderr,
        "the validation CLI emits the certificate and refuses an unsupported target",
    )

    kcl_adapter = glm_target.get_adapter("sum", "kcl-conservation")
    expect(
        kcl_adapter.entrypoint == "exact_kcl_sum"
        and kcl_adapter.kind == "exact_sum"
        and kcl_adapter.invocation == "exact_kcl_sum(a, b)"
        and len(kcl_adapter.vectors) == 3
        and "sum" in (target_profile.interface.get("interfaces") or {}),
        "the reference target declares an executable exact-sum adapter and interface",
    )

    sum_interface = (target_profile.interface.get("interfaces") or {}).get("sum") or {}
    expect(
        sum_interface.get("state") == "none"
        and sum_interface.get("feedback") == "none"
        and "total" in (sum_interface.get("outputs") or {})
        and kcl_adapter.vectors[0].expected == Fraction(5, 6),
        "the target contract declares a stateless exact-sum interface and fixed expectation",
    )

    sum_run = glm_target.exact_kcl_sum(Fraction(1, 2), Fraction(1, 3))
    expect(
        sum_run.result == Fraction(5, 6)
        and sum_run.passed
        and glm_target.exact_kcl_sum(Fraction(1, 3), Fraction(1, 2)).result
        == sum_run.result,
        "the KCL target computes an exact commutative sum",
    )

    kcl_parity = True
    for vector in glm_target.KCL_VECTORS:
        source = assembly.kcl_sum_route(operation="sum").simulate(
            vector.a, vector.b
        )
        target = glm_target.exact_kcl_sum(vector.a, vector.b)
        kcl_parity = kcl_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    expect(
        kcl_parity,
        "all three KCL vectors match the exact source junction route",
    )

    sum_validation = transfer_validation.validate_transfer(
        "sum", mechanism_id="kcl-conservation"
    )
    sum_certificate = sum_validation.get("certificate") or {}
    expect(
        sum_validation.get("schema") == transfer_validation.VALIDATION_SCHEMA
        and sum_certificate.get("status") == "pass"
        and sum_certificate.get("evidence_level") == "target-simulated"
        and len(sum_validation.get("checks") or ()) == 8
        and all(
            check.get("status") == "pass"
            for check in sum_validation.get("checks") or ()
        )
        and sum_validation.get("metrics", {}).get("vectors") == 3
        and sum_validation.get("metrics", {}).get("max_abs_residual")
        == {"num": "0", "den": "1"},
        "the exact-sum adapter emits a second passing target-simulated certificate",
    )

    sum_reviewed = sum_validation.get("validated_candidate") or {}
    expect(
        sum_reviewed.get("status") == "validated"
        and sum_reviewed.get("evidence_level") == "target-simulated"
        and (sum_reviewed.get("artifact") or {}).get("entrypoint")
        == "exact_kcl_sum"
        and sum_reviewed.get("tests")
        == ["half-plus-third", "negative-plus-half", "zero-plus-third"]
        and any("no real GLM" in gap for gap in sum_reviewed.get("gaps") or ())
        and not any(
            "not implemented" in gap for gap in sum_reviewed.get("gaps") or ()
        ),
        "the validated KCL candidate carries its artifact, tests and target gaps",
    )

    sum_retrieval = transfer_engine.transfer_payload("sum")
    expect(
        sum_retrieval.get("candidates")
        and sum_retrieval["candidates"][0].get("status") == "candidate"
        and sum_retrieval["candidates"][0].get("artifact") is None
        and sum_retrieval["candidates"][0].get("tests") == [],
        "KCL validation leaves the sum retrieval view candidate-only",
    )

    sum_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sum",
            "--mechanism", "kcl-conservation", "--validate", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    sum_cli_payload = json.loads(sum_cli.stdout) if sum_cli.returncode == 0 else {}
    sum_human = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sum",
            "--mechanism", "kcl-conservation", "--validate",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        sum_cli.returncode == 0
        and (sum_cli_payload.get("certificate") or {}).get("status") == "pass"
        and (sum_cli_payload.get("artifact") or {}).get("entrypoint")
        == "exact_kcl_sum"
        and sum_human.returncode == 0
        and "exact_kcl_sum" in sum_human.stdout
        and "sum commutative" in sum_human.stdout,
        "the KCL sum validation CLI emits its certificate",
    )

    fluid_adapter = glm_target.get_adapter("sum", "fluid-continuity")
    fluid_parity = True
    for vector in glm_target.FLUID_VECTORS:
        source = assembly.fluid_sum_route().simulate(vector.a, vector.b)
        target = glm_target.exact_fluid_sum(vector.a, vector.b)
        fluid_parity = fluid_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    expect(
        fluid_adapter.entrypoint == "exact_fluid_sum"
        and fluid_adapter.kind == "fluid_sum"
        and fluid_adapter.invocation == "exact_fluid_sum(a, b)"
        and len(fluid_adapter.vectors) == 3
        and fluid_parity,
        "the reference target declares an independent normalized-fluid sum adapter",
    )

    fluid_validation = transfer_validation.validate_transfer(
        "sum", mechanism_id="fluid-continuity"
    )
    fluid_reviewed = fluid_validation.get("validated_candidate") or {}
    expect(
        fluid_validation.get("status") == "pass"
        and (fluid_validation.get("certificate") or {}).get("status") == "pass"
        and len(fluid_validation.get("checks") or ()) == 8
        and fluid_validation.get("metrics", {}).get("vectors") == 3
        and (fluid_reviewed.get("artifact") or {}).get("entrypoint")
        == "exact_fluid_sum"
        and fluid_reviewed.get("tests")
        == ["flow-half-plus-third", "flow-negative-plus-half", "flow-zero-plus-third"]
        and (fluid_reviewed.get("relaxation") or {}).get("classification")
        == "exact"
        and any("no real GLM" in gap for gap in fluid_reviewed.get("gaps") or ())
        and any("measured junction" in gap for gap in fluid_reviewed.get("gaps") or ()),
        "the fluid-continuity adapter passes all fixed vectors and keeps its physical gaps",
    )

    fluid_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sum",
            "--mechanism", "fluid-continuity", "--validate", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    fluid_cli_payload = json.loads(fluid_cli.stdout) if fluid_cli.returncode == 0 else {}
    expect(
        fluid_cli.returncode == 0
        and (fluid_cli_payload.get("artifact") or {}).get("entrypoint")
        == "exact_fluid_sum"
        and (fluid_cli_payload.get("certificate") or {}).get("status") == "pass",
        "the CLI validates the selected fluid-continuity mechanism",
    )

    reference_latency = target_profile.interface.get("latency") or {}
    reference_bits = target_profile.interface.get("bit_budget") or {}
    expect(
        reference_latency.get("quantized_carry") == "samples"
        and reference_latency.get("sum") == 1
        and reference_latency.get("difference") == 1
        and "exact rational result" in (reference_bits.get("sum") or "")
        and target_profile.constraints.get("reference_budgets_declared") is True,
        "the target declares reference-operation latency and bit budgets without an external claim",
    )

    difference_adapter = glm_target.get_adapter("difference", "kcl-conservation")
    expect(
        difference_adapter.entrypoint == "exact_kcl_difference"
        and difference_adapter.kind == "exact_difference"
        and difference_adapter.invocation == "exact_kcl_difference(a, b)"
        and len(difference_adapter.vectors) == 3,
        "the reference target declares the third executable KCL difference adapter",
    )

    difference_interface = (
        target_profile.interface.get("interfaces") or {}
    ).get("difference") or {}
    expect(
        difference_interface.get("state") == "none"
        and difference_interface.get("feedback") == "none"
        and "total" in (difference_interface.get("outputs") or {})
        and difference_adapter.vectors[0].expected == Fraction(1, 6),
        "the target contract declares a stateless exact-difference interface and fixed expectation",
    )

    difference_run = glm_target.exact_kcl_difference(
        Fraction(1, 2), Fraction(1, 3)
    )
    swapped_difference = glm_target.exact_kcl_difference(
        Fraction(1, 3), Fraction(1, 2)
    )
    expect(
        difference_run.result == Fraction(1, 6)
        and difference_run.passed
        and swapped_difference.result == -difference_run.result,
        "the KCL target computes an exact antisymmetric difference",
    )

    difference_parity = True
    for vector in glm_target.KCL_DIFFERENCE_VECTORS:
        source = assembly.kcl_sum_route(operation="difference").simulate(
            vector.a, vector.b
        )
        target = glm_target.exact_kcl_difference(vector.a, vector.b)
        difference_parity = difference_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    expect(
        difference_parity,
        "all three KCL difference vectors match the exact source junction route",
    )

    difference_validation = transfer_validation.validate_transfer(
        "difference", mechanism_id="kcl-conservation"
    )
    difference_certificate = difference_validation.get("certificate") or {}
    expect(
        difference_certificate.get("status") == "pass"
        and difference_certificate.get("evidence_level") == "target-simulated"
        and len(difference_validation.get("checks") or ()) == 9
        and all(
            check.get("status") == "pass"
            for check in difference_validation.get("checks") or ()
        )
        and difference_validation.get("metrics", {}).get("vectors") == 3
        and difference_validation.get("metrics", {}).get("max_abs_residual")
        == {"num": "0", "den": "1"},
        "the exact-difference adapter emits a third passing target-simulated certificate",
    )

    difference_reviewed = difference_validation.get("validated_candidate") or {}
    difference_retrieval = transfer_engine.transfer_payload("difference")
    expect(
        difference_reviewed.get("status") == "validated"
        and difference_reviewed.get("evidence_level") == "target-simulated"
        and (difference_reviewed.get("artifact") or {}).get("entrypoint")
        == "exact_kcl_difference"
        and difference_reviewed.get("tests")
        == ["half-minus-third", "negative-minus-half", "zero-minus-third"]
        and difference_retrieval.get("candidates")
        and difference_retrieval["candidates"][0].get("status") == "candidate"
        and difference_retrieval["candidates"][0].get("artifact") is None,
        "the validated difference candidate is separate from the candidate-only retrieval view",
    )

    difference_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "difference",
            "--mechanism", "kcl-conservation", "--validate", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    difference_payload = (
        json.loads(difference_cli.stdout) if difference_cli.returncode == 0 else {}
    )
    difference_human = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "difference",
            "--mechanism", "kcl-conservation", "--validate",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        difference_cli.returncode == 0
        and (difference_payload.get("certificate") or {}).get("status") == "pass"
        and (difference_payload.get("artifact") or {}).get("entrypoint")
        == "exact_kcl_difference"
        and difference_human.returncode == 0
        and "exact_kcl_difference" in difference_human.stdout
        and "difference noncommutative" in difference_human.stdout,
        "the KCL difference validation CLI emits its third certificate",
    )

    fluid_difference_adapter = glm_target.get_adapter(
        "difference", "fluid-continuity"
    )
    fluid_difference_parity = True
    for vector in glm_target.FLUID_DIFFERENCE_VECTORS:
        source = assembly.fluid_sum_route(operation="difference").simulate(
            vector.a, vector.b
        )
        target = glm_target.exact_fluid_difference(vector.a, vector.b)
        fluid_difference_parity = fluid_difference_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    expect(
        fluid_difference_adapter.entrypoint == "exact_fluid_difference"
        and fluid_difference_adapter.kind == "fluid_difference"
        and fluid_difference_adapter.invocation
        == "exact_fluid_difference(a, b)"
        and len(fluid_difference_adapter.vectors) == 3
        and fluid_difference_parity,
        "the reference target declares an independent normalized-fluid difference adapter",
    )

    fluid_difference_validation = transfer_validation.validate_transfer(
        "difference", mechanism_id="fluid-continuity"
    )
    fluid_difference_reviewed = (
        fluid_difference_validation.get("validated_candidate") or {}
    )
    expect(
        fluid_difference_validation.get("status") == "pass"
        and (fluid_difference_validation.get("certificate") or {}).get("status")
        == "pass"
        and len(fluid_difference_validation.get("checks") or ()) == 9
        and fluid_difference_validation.get("metrics", {}).get("vectors") == 3
        and (fluid_difference_reviewed.get("artifact") or {}).get("entrypoint")
        == "exact_fluid_difference"
        and fluid_difference_reviewed.get("tests")
        == [
            "flow-half-minus-third",
            "flow-negative-minus-half",
            "flow-zero-minus-third",
        ]
        and any(
            "measured junction" in gap
            for gap in fluid_difference_reviewed.get("gaps") or ()
        ),
        "the fluid reversed-port difference adapter passes with physical gaps intact",
    )

    opamp_adapter = glm_target.get_adapter("sum", "opamp-summing")
    opamp_difference_adapter = glm_target.get_adapter(
        "difference", "opamp-summing"
    )
    opamp_parity = True
    for vector in glm_target.OPAMP_VECTORS:
        source = assembly.opamp_sum_route(operation="sum").simulate(
            vector.a, vector.b
        )
        target = glm_target.exact_opamp_sum(vector.a, vector.b)
        opamp_parity = opamp_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    for vector in glm_target.OPAMP_DIFFERENCE_VECTORS:
        source = assembly.opamp_sum_route(operation="difference").simulate(
            vector.a, vector.b
        )
        target = glm_target.exact_opamp_difference(vector.a, vector.b)
        opamp_parity = opamp_parity and (
            source.result == target.result == vector.expected
            and source.passed
        )
    expect(
        opamp_adapter.entrypoint == "exact_opamp_sum"
        and opamp_adapter.kind == "opamp_sum"
        and opamp_difference_adapter.entrypoint == "exact_opamp_difference"
        and opamp_difference_adapter.kind == "opamp_difference"
        and len(opamp_adapter.vectors) == 3
        and len(opamp_difference_adapter.vectors) == 3
        and opamp_parity,
        "the reference target declares independent op-amp sum and difference adapters",
    )

    opamp_difference_validation = transfer_validation.validate_transfer(
        "difference", mechanism_id="opamp-summing"
    )
    opamp_difference_reviewed = (
        opamp_difference_validation.get("validated_candidate") or {}
    )
    expect(
        opamp_difference_validation.get("status") == "pass"
        and (opamp_difference_validation.get("certificate") or {}).get("status")
        == "pass"
        and len(opamp_difference_validation.get("checks") or ()) == 9
        and opamp_difference_validation.get("metrics", {}).get("vectors") == 3
        and (opamp_difference_reviewed.get("artifact") or {}).get("entrypoint")
        == "exact_opamp_difference"
        and opamp_difference_reviewed.get("tests")
        == [
            "opamp-half-minus-third",
            "opamp-negative-minus-half",
            "opamp-zero-minus-third",
        ]
        and any(
            "measured amplifier" in gap
            for gap in opamp_difference_reviewed.get("gaps") or ()
        ),
        "the op-amp difference adapter passes with its physical gaps intact",
    )

    sqrt_interface = (
        target_profile.interface.get("interfaces") or {}
    ).get("sqrt") or {}
    expect(
        (target_profile.interface.get("latency") or {}).get("sqrt")
        == "1 route evaluation"
        and (target_profile.interface.get("bit_budget") or {}).get("sqrt")
        == "precision bits per enclosure"
        and sqrt_interface.get("state") == "none"
        and sqrt_interface.get("feedback") == "none"
        and sqrt_interface.get("law") == "root = exp((1/2) * log(x))"
        and "certified rational enclosure"
        in (sqrt_interface.get("outputs") or {}).get("root", ""),
        "the target profile declares a stateless sqrt interface and operation-local budgets",
    )

    sqrt_adapter = glm_target.get_adapter("sqrt", "log-domain-sqrt")
    expect(
        sqrt_adapter.entrypoint == "log_domain_sqrt"
        and sqrt_adapter.operation == "sqrt"
        and sqrt_adapter.mechanism == "log-domain-sqrt"
        and sqrt_adapter.kind == "certified_enclosure"
        and sqrt_adapter.invocation
        == "log_domain_sqrt(x, precision=..., tolerance=...)"
        and [vector.id for vector in sqrt_adapter.vectors]
        == ["sqrt-two", "sqrt-half", "sqrt-nine"],
        "the reference target declares the fourth executable log-domain sqrt adapter",
    )

    sqrt_run = glm_target.log_domain_sqrt(Fraction(2))
    sqrt_checker_overlap = (
        max(sqrt_run.root.lo, sqrt_run.checker.lo)
        <= min(sqrt_run.root.hi, sqrt_run.checker.hi)
    )
    expect(
        sqrt_run.passed
        and sqrt_checker_overlap
        and sqrt_run.root.width <= Fraction(1, 10000)
        and sqrt_run.precision == 20,
        "the target sqrt route returns a passing certified enclosure",
    )

    sqrt_parity = True
    for vector in glm_target.SQRT_VECTORS:
        source = assembly.log_domain_sqrt_route(
            precision=vector.precision, tolerance=vector.tolerance
        ).simulate(vector.x)
        target = glm_target.log_domain_sqrt(
            vector.x, precision=vector.precision, tolerance=vector.tolerance
        )
        source_target_overlap = (
            max(source.root.lo, target.root.lo)
            <= min(source.root.hi, target.root.hi)
        )
        source_checker_overlap = (
            max(source.root.lo, target.checker.lo)
            <= min(source.root.hi, target.checker.hi)
        )
        target_checker_overlap = (
            max(target.root.lo, target.checker.lo)
            <= min(target.root.hi, target.checker.hi)
        )
        sqrt_parity = sqrt_parity and (
            source.passed
            and target.passed
            and source_target_overlap
            and source_checker_overlap
            and target_checker_overlap
        )
    expect(
        sqrt_parity,
        "all three log-domain sqrt vectors agree with the source route and sqrt_q",
    )

    sqrt_validation = transfer_validation.validate_transfer("sqrt")
    sqrt_certificate = sqrt_validation.get("certificate") or {}
    expect(
        sqrt_certificate.get("status") == "pass"
        and sqrt_certificate.get("evidence_level") == "target-simulated"
        and len(sqrt_validation.get("checks") or ()) == 9
        and all(
            check.get("status") == "pass"
            for check in sqrt_validation.get("checks") or ()
        )
        and sqrt_validation.get("metrics", {}).get("vectors") == 3
        and "max_root_width" in (sqrt_validation.get("metrics") or {}),
        "the log-domain sqrt adapter emits a fourth passing target-simulated certificate",
    )

    sqrt_reviewed = sqrt_validation.get("validated_candidate") or {}
    expect(
        sqrt_reviewed.get("status") == "validated"
        and sqrt_reviewed.get("evidence_level") == "target-simulated"
        and (sqrt_reviewed.get("artifact") or {}).get("entrypoint")
        == "log_domain_sqrt"
        and sqrt_reviewed.get("tests")
        == ["sqrt-two", "sqrt-half", "sqrt-nine"],
        "the validated sqrt candidate carries its adapter and fixed-vector evidence",
    )

    sqrt_cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sqrt",
            "--validate", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    sqrt_payload = json.loads(sqrt_cli.stdout) if sqrt_cli.returncode == 0 else {}
    sqrt_human = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "transfer", "sqrt",
            "--validate",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        sqrt_cli.returncode == 0
        and (sqrt_payload.get("certificate") or {}).get("status") == "pass"
        and (sqrt_payload.get("artifact") or {}).get("entrypoint")
        == "log_domain_sqrt"
        and sqrt_human.returncode == 0
        and "log_domain_sqrt" in sqrt_human.stdout
        and "source target enclosures overlap" in sqrt_human.stdout,
        "the log-domain sqrt validation CLI emits its fourth certificate",
    )

    sqrt_bundle = proposal_module.build_bundle("sqrt")
    expect(
        sqrt_bundle.get("schema") == proposal_module.BUNDLE_SCHEMA
        and len(sqrt_bundle.get("proposals") or ()) == 3
        and sqrt_bundle.get("summary", {}).get("proposals") == 3
        and sqrt_bundle.get("summary", {}).get("ready_for_execution") == 1
        and sqrt_bundle.get("summary", {}).get("needs_target_adapter") == 2
        and sqrt_bundle.get("ok") is True,
        "the proposal layer emits a cross-domain bundle for sqrt",
    )

    sqrt_proposals = sqrt_bundle.get("proposals") or []
    sqrt_ready = [
        proposal for proposal in sqrt_proposals
        if proposal.get("handoff", {}).get("readiness") == "ready-for-execution"
    ]
    sqrt_needs = [
        proposal for proposal in sqrt_proposals
        if proposal.get("handoff", {}).get("readiness") == "needs-target-adapter"
    ]
    expect(
        len(sqrt_ready) == 1
        and len(sqrt_needs) == 2
        and sqrt_ready[0].get("mechanism", {}).get("id") == "log-domain-sqrt"
        and (sqrt_ready[0].get("target", {}).get("adapter") or {}).get("entrypoint")
        == "log_domain_sqrt"
        and sqrt_ready[0].get("handoff", {}).get("fixed_vectors")
        == ["sqrt-two", "sqrt-half", "sqrt-nine"]
        and all(
            proposal.get("handoff", {}).get("fixed_vectors") == []
            and proposal.get("target", {}).get("adapter") is None
            for proposal in sqrt_needs
        ),
        "sqrt exposes one executable log-domain handoff and two honest adapter gaps",
    )

    sqrt_trial = trial_module.run_trial(sqrt_ready[0])
    blocked_trial = trial_module.run_trial(sqrt_needs[0])
    attached = trial_module.attach_trials(sqrt_bundle)
    expect(
        sqrt_trial.get("schema") == trial_module.TRIAL_SCHEMA
        and sqrt_trial.get("status") == "pass"
        and sqrt_trial.get("metrics", {}).get("vectors") == 3
        and sqrt_trial.get("metrics", {}).get("passed") == 3
        and len(sqrt_trial.get("vectors") or ()) == 3
        and all(row.get("passed") for row in sqrt_trial.get("vectors") or ())
        and (sqrt_trial.get("certificate") or {}).get("status") == "pass"
        and sqrt_trial.get("evidence_level") == "target-simulated"
        and (sqrt_trial.get("proposal_summary") or {}).get("operation")
        == "square root"
        and (sqrt_trial.get("proposal_summary") or {}).get("mechanism")
        and (sqrt_trial.get("proposal_summary") or {}).get("target") == "glm-reference"
        and "execute 3 declared fixed vector" in (sqrt_trial.get("what") or "")
        and blocked_trial.get("status") == "not-run"
        and "needs-target-adapter" in (blocked_trial.get("reason") or "")
        and blocked_trial.get("adjustment")
        and attached.get("trial_summary")
        == {"attempted": 3, "passed": 1, "failed": 0, "not_run": 2, "errors": 0}
        and any(
            check.get("name") == "computational proposal trial"
            and check.get("status") == "pass"
            for check in attached.get("checks") or ()
        ),
        "the sqrt proposal trial executes one ready adapter and marks adapter gaps unrun",
    )

    with tempfile.TemporaryDirectory() as tmp:
        proposal_module.write_bundle(sqrt_bundle, tmp)
        trial_cli = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "trial", tmp, "--json"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        trial_payload = (
            json.loads(trial_cli.stdout) if trial_cli.returncode == 0 else {}
        )
        trial_human = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "trial", tmp,
                sqrt_ready[0]["id"],
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        unknown_trial = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "trial", tmp,
                "proposal-does-not-exist", "--json",
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        expect(
            trial_cli.returncode == 0
            and trial_payload.get("schema") == trial_module.BUNDLE_SCHEMA
            and trial_payload.get("summary") == {
                "attempted": 3,
                "passed": 1,
                "failed": 0,
                "not_run": 2,
                "errors": 0,
            }
            and trial_payload.get("ok") is True
            and trial_human.returncode == 0
            and "COMPUTATIONAL PROPOSAL TRIAL" in trial_human.stdout
            and "sqrt-two" in trial_human.stdout
            and "works on the declared fixed vectors" in trial_human.stdout
            and unknown_trial.returncode == 2
            and "unknown proposal" in unknown_trial.stderr,
            "cent trial runs saved bundles, selects one proposal, and refuses unknown ids",
        )

    propose_trial = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "propose", "sqrt",
            "--trial", "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    propose_trial_payload = (
        json.loads(propose_trial.stdout) if propose_trial.returncode == 0 else {}
    )
    expect(
        propose_trial.returncode == 0
        and propose_trial_payload.get("trial_summary")
        == {"attempted": 3, "passed": 1, "failed": 0, "not_run": 2, "errors": 0}
        and len(
            [
                proposal for proposal in propose_trial_payload.get("proposals") or ()
                if (proposal.get("trial") or {}).get("status") == "pass"
            ]
        ) == 1,
        "cent propose --trial attaches executable results to the bundle",
    )

    wheel = trial_module.run_wheel(limit=1)
    wheel_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "trial", "--wheel", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    wheel_human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "trial", "--wheel"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    wheel_bad = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "trial", "--wheel", "/tmp/x"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    expect(
        wheel.get("schema") == trial_module.WHEEL_SCHEMA
        and wheel.get("summary", {}).get("operations") == 10
        and wheel.get("summary", {}).get("testable_operations") == 10
        and wheel.get("summary", {}).get("untestable_operations") == 0
        and wheel.get("summary", {}).get("passed") == 10
        and wheel.get("summary", {}).get("errors") == 0
        and any(
            row.get("operation") == "sign" and row.get("testable") is True
            for row in wheel.get("operations") or ()
        )
        and any(
            row.get("operation") == "sqrt" and row.get("testable") is True
            for row in wheel.get("operations") or ()
        )
        and wheel_cli.returncode == 0
        and json.loads(wheel_cli.stdout).get("schema") == trial_module.WHEEL_SCHEMA
        and wheel_human.returncode == 0
        and "OPERATION TRIAL WHEEL" in wheel_human.stdout
        and "10/10 declared operation" in wheel_human.stdout
        and "sign" in wheel_human.stdout
        and wheel_bad.returncode == 2
        and "--wheel does not take" in wheel_bad.stderr,
        "the operation wheel trials every declared operation and reports executable gaps",
    )

    sum_bundle = proposal_module.build_bundle("sum")
    sum_proposal = next(
        (
            proposal for proposal in sum_bundle.get("proposals") or ()
            if proposal.get("mechanism", {}).get("id") == "kcl-conservation"
        ),
        {},
    )
    expect(
        sum_proposal.get("handoff", {}).get("readiness") == "ready-for-execution"
        and (sum_proposal.get("target", {}).get("adapter") or {}).get("entrypoint")
        == "exact_kcl_sum"
        and sum_proposal.get("handoff", {}).get("fixed_vectors")
        == ["half-plus-third", "negative-plus-half", "zero-plus-third"]
        and (sum_proposal.get("relaxation") or {}).get("classification")
        == "unclassified"
        and 'transfer "sum"' in (sum_proposal.get("handoff", {}).get("command") or "")
        and '--mechanism "kcl-conservation"'
        in (sum_proposal.get("handoff", {}).get("command") or ""),
        "the KCL sum proposal is ready with an exact validation handoff",
    )

    fluid_proposal = next(
        (
            proposal for proposal in sum_bundle.get("proposals") or ()
            if proposal.get("mechanism", {}).get("id") == "fluid-continuity"
        ),
        {},
    )
    opamp_proposal = next(
        (
            proposal for proposal in sum_bundle.get("proposals") or ()
            if proposal.get("mechanism", {}).get("id") == "opamp-summing"
        ),
        {},
    )
    expect(
        sum_bundle.get("summary", {}).get("ready_for_execution") == 3
        and fluid_proposal.get("handoff", {}).get("readiness")
        == "ready-for-execution"
        and (fluid_proposal.get("target", {}).get("adapter") or {}).get("entrypoint")
        == "exact_fluid_sum"
        and fluid_proposal.get("handoff", {}).get("fixed_vectors")
        == ["flow-half-plus-third", "flow-negative-plus-half", "flow-zero-plus-third"]
        and '--mechanism "fluid-continuity"'
        in (fluid_proposal.get("handoff", {}).get("command") or ""),
        "the fluid sum proposal hands off to its selected mechanism adapter",
    )
    expect(
        opamp_proposal.get("handoff", {}).get("readiness")
        == "ready-for-execution"
        and (opamp_proposal.get("target", {}).get("adapter") or {}).get(
            "entrypoint"
        ) == "exact_opamp_sum"
        and opamp_proposal.get("handoff", {}).get("fixed_vectors")
        == [
            "opamp-half-plus-third",
            "opamp-negative-plus-half",
            "opamp-zero-plus-third",
        ]
        and '--mechanism "opamp-summing"'
        in (opamp_proposal.get("handoff", {}).get("command") or ""),
        "the op-amp sum proposal hands off to its selected mechanism adapter",
    )

    carry_bundle = proposal_module.build_bundle("quantized_carry")
    carry_proposal = (carry_bundle.get("proposals") or [{}])[0]
    expect(
        carry_proposal.get("handoff", {}).get("readiness") == "ready-for-execution"
        and (carry_proposal.get("target", {}).get("adapter") or {}).get("entrypoint")
        == "delta_sigma_quantized_carry",
        "the quantized-carry proposal hands off to its reference adapter",
    )

    live_bundle = proposal_module.build_bundle("sum", target_id="glm-live")
    live_proposal = next(
        (
            proposal for proposal in live_bundle.get("proposals") or ()
            if proposal.get("mechanism", {}).get("id") == "kcl-conservation"
        ),
        {},
    )
    expect(
        live_proposal.get("handoff", {}).get("readiness") == "ready-for-execution"
        and (live_proposal.get("handoff", {}).get("environment") or {}).get("available")
        is True
        and live_proposal.get("target", {}).get("id") == "glm-live",
        "the live sum proposal exposes its external environment and handoff",
    )

    analogy = sum_proposal.get("analogy") or {}
    expect(
        analogy.get("kind") == "behavioral-analogy"
        and analogy.get("isomorphism_claimed") is False
        and analogy.get("basis")
        and any(
            check.get("name") == "isomorphism"
            and check.get("status") == "gap"
            for check in sum_proposal.get("checks") or ()
        ),
        "proposals label behavioral analogy and do not claim an isomorphism",
    )

    ids = [proposal.get("id") for proposal in sqrt_bundle.get("proposals") or ()]
    expect(
        len(ids) == len(set(ids))
        and all(
            proposal.get("status") == "unvalidated"
            for proposal in sqrt_bundle["proposals"]
        )
        and all(
            any(
                "not a target validation" in gap
                for gap in proposal.get("gaps") or ()
            )
            for proposal in sqrt_bundle["proposals"]
        ),
        "proposal identifiers are unique and every proposal stays unvalidated",
    )

    with tempfile.TemporaryDirectory() as tmp:
        written = proposal_module.write_bundle(sum_bundle, tmp)
        index = json.loads((pathlib.Path(tmp) / "index.json").read_text())
        expect(
            len(written) == len(sum_bundle.get("proposals") or ()) + 2
            and (pathlib.Path(tmp) / "index.md").exists()
            and index.get("schema") == proposal_module.INDEX_SCHEMA
            and index.get("proposals")
            and any(
                proposal.get("readiness") == "ready-for-execution"
                for proposal in index["proposals"]
            ),
            "the proposal writer emits JSON proposals, index.json and index.md",
        )

    proposal_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "propose", "sqrt", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    proposal_payload = (
        json.loads(proposal_cli.stdout) if proposal_cli.returncode == 0 else {}
    )
    expect(
        proposal_cli.returncode == 0
        and proposal_payload.get("schema") == proposal_module.BUNDLE_SCHEMA
        and len(proposal_payload.get("proposals") or ()) == 3,
        "cent propose --json emits the proposal bundle",
    )

    with tempfile.TemporaryDirectory() as tmp:
        export_cli = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "propose", "sqrt",
                "--json", "--out", tmp,
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        exported = sorted(path.name for path in pathlib.Path(tmp).iterdir())
        human_cli = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "propose", "sum"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        expect(
            export_cli.returncode == 0
            and "index.json" in exported
            and "index.md" in exported
            and len(exported) == 5
            and human_cli.returncode == 0
            and "ready-for-execution" in human_cli.stdout
            and "A proposal is a reviewable analogy" in human_cli.stdout,
            "proposal export writes five sqrt files and the human view shows the handoff",
        )
        exported_index = json.loads(
            (pathlib.Path(tmp) / "index.json").read_text()
        )
        indexed_ready = [
            entry for entry in exported_index.get("proposals") or ()
            if entry.get("readiness") == "ready-for-execution"
        ]
        indexed_needs = [
            entry for entry in exported_index.get("proposals") or ()
            if entry.get("readiness") == "needs-target-adapter"
        ]
        expect(
            len(indexed_ready) == 1
            and len(indexed_needs) == 2
            and indexed_ready[0].get("id", "").endswith("log-domain-sqrt"),
            "the exported sqrt index carries the executable handoff and adapter gaps",
        )

    expect(
        all(
            (proposal.get("review") or {}).get("schema")
            == proposal_module.REVIEW_STATE_SCHEMA
            and (proposal.get("review") or {}).get("state") == "unreviewed"
            and (proposal.get("review") or {}).get("history") == []
            for proposal in sqrt_proposals
        ),
        "proposal bundles start unreviewed with an empty review history",
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        proposal_module.write_bundle(sqrt_bundle, root)
        review_id = sqrt_ready[0]["id"]
        review_row = next(
            row for row in json.loads((root / "index.json").read_text())["proposals"]
            if row.get("id") == review_id
        )
        proposal_path = root / review_row["file"]
        accepted = proposal_module.record_review(
            root,
            review_id,
            state="accepted",
            reviewer="reviewer-a",
            note="Handoff accepted for execution.",
        )
        ledger = proposal_module.load_review_ledger(root)
        accepted_proposal = json.loads(proposal_path.read_text())
        expect(
            accepted.get("schema") == proposal_module.REVIEW_EVENT_SCHEMA
            and accepted.get("prior_state") == "unreviewed"
            and accepted.get("state") == "accepted"
            and (accepted.get("event") or {}).get("sequence") == 1
            and (accepted.get("event") or {}).get("reviewer") == "reviewer-a"
            and (accepted.get("event") or {}).get("recorded_at", "").endswith("Z")
            and ledger.get("schema") == proposal_module.REVIEW_LEDGER_SCHEMA
            and len(ledger.get("events") or ()) == 1
            and accepted_proposal.get("review", {}).get("state") == "accepted"
            and accepted_proposal.get("status") == "unvalidated",
            "accepted proposals receive a durable review event without becoming validated",
        )

        rejected = proposal_module.record_review(
            root,
            review_id,
            state="rejected",
            reviewer="reviewer-b",
            note="Independent evidence is still missing.",
        )
        expect(
            rejected.get("prior_state") == "accepted"
            and rejected.get("state") == "rejected"
            and (rejected.get("event") or {}).get("sequence") == 2
            and (rejected.get("event") or {}).get("note")
            == "Independent evidence is still missing."
            and len(ledger.get("events") or ()) == 1
            and len(proposal_module.load_review_ledger(root).get("events") or ()) == 2,
            "rejected handoffs preserve their reason and prior review state",
        )

        no_reason = _raises(
            lambda: proposal_module.record_review(
                root,
                review_id,
                state="rejected",
                reviewer="reviewer-b",
                note="",
            ),
            "review note is required",
        )
        unknown_proposal = _raises(
            lambda: proposal_module.record_review(
                root,
                "proposal-does-not-exist",
                state="accepted",
                reviewer="reviewer-b",
                note="Unknown proposal.",
            ),
            "unknown proposal",
        )
        expect(
            no_reason and unknown_proposal,
            "reviews refuse a missing reason and an unknown proposal id",
        )

        certificate = transfer_validation.validate_transfer("sqrt")
        certificate_path = root / "sqrt-certificate.json"
        certificate_path.write_text(json.dumps(certificate), encoding="utf-8")
        missing_certificate = _raises(
            lambda: proposal_module.record_review(
                root,
                review_id,
                state="tested",
                reviewer="reviewer-c",
                note="Tested without evidence.",
            ),
            "requires --certificate",
        )
        tested = proposal_module.record_review(
            root,
            review_id,
            state="tested",
            reviewer="reviewer-c",
            note="Passing target certificate attached.",
            certificate_path=certificate_path,
        )
        evidence = (tested.get("event") or {}).get("evidence") or {}
        evidence_path = root / str(evidence.get("path", ""))
        digest = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
        expect(
            missing_certificate
            and evidence.get("sha256") == digest
            and evidence.get("status") == "pass"
            and evidence_path.is_file()
            and evidence_path.read_bytes() == certificate_path.read_bytes()
            and tested.get("state") == "tested",
            "tested reviews require and copy a passing certificate with its hash",
        )

        bad_certificate = root / "bad-certificate.json"
        bad_certificate.write_text(
            json.dumps({"schema": "not-a-certificate", "status": "pass"}),
            encoding="utf-8",
        )
        bad_refused = _raises(
            lambda: proposal_module.record_review(
                root,
                review_id,
                state="tested",
                reviewer="reviewer-d",
                note="Bad certificate.",
                certificate_path=bad_certificate,
            ),
            "cent-transfer-certificate/1",
        )
        expect(
            bad_refused
            and len(proposal_module.load_review_ledger(root).get("events") or ()) == 3,
            "invalid certificates are refused without appending a review event",
        )

        proposal_module.write_bundle(sqrt_bundle, root)
        reexported = json.loads(proposal_path.read_text())
        reexported_index = json.loads((root / "index.json").read_text())
        reexported_row = next(
            row for row in reexported_index["proposals"]
            if row.get("id") == review_id
        )
        expect(
            reexported.get("review", {}).get("state") == "tested"
            and len(reexported.get("review", {}).get("history") or ()) == 3
            and reexported_row.get("review_state") == "tested"
            and reexported_index.get("review_ledger")
            == proposal_module.REVIEW_LEDGER_FILENAME,
            "re-exporting a bundle preserves its durable review history",
        )

        review_cli = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "review", tmp, review_id,
                "--state", "accepted", "--reviewer", "reviewer-cli",
                "--note", "CLI acceptance.", "--json",
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        review_list = subprocess.run(
            [
                sys.executable, str(ROOT / "cent"), "review", tmp,
                "--list", "--json",
            ],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        review_cli_payload = (
            json.loads(review_cli.stdout) if review_cli.returncode == 0 else {}
        )
        review_list_payload = (
            json.loads(review_list.stdout) if review_list.returncode == 0 else {}
        )
        events = review_list_payload.get("events") or ()
        expect(
            review_cli.returncode == 0
            and review_cli_payload.get("prior_state") == "tested"
            and review_cli_payload.get("state") == "accepted"
            and review_list.returncode == 0
            and len(events) == 4
            and review_list_payload.get("schema")
            == proposal_module.REVIEW_LEDGER_SCHEMA
            and (review_list_payload.get("events") or [{}])[-1].get("reviewer")
            == "reviewer-cli",
            "the review CLI records decisions and lists the durable ledger",
        )

    unknown_proposal = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "propose", "not_an_operation"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    expect(
        unknown_proposal.returncode == 2
        and "unknown operation contract" in unknown_proposal.stderr,
        "the proposal CLI refuses an unknown operation",
    )

    print("\n" + "=" * 78)
    print(f"TRANSFER CONTRACTS, REGISTRY, ENGINE AND TARGET: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
