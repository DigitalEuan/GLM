"""Tests for the evidence model in use (Phase 171).

*Created 20 October 2026.*

``studies/EVIDENCE_IN_USE_STUDY.md`` pre-registered the marks L1 and U1-U6.
These tests pin:

* **``GLM.py --result``**: an answer prints as one result row with the ten
  fields, replayed under ``--verify-tct``; a refusal prints with its reason
  and exit code 1; without the flag the command line prints as before;
* **the gate's rule** (U5): one failed replay, one unanswered row or one
  process error fails it; a row without a column 3 does not;
* **the gate on one case**: ``verify-newton`` replays and passes;
* **the Lean half**: the five theorems are declared with no ``sorry``;
* **the stored measurement**, when current: every mark met.
"""

from __future__ import annotations

import io
import json

import GLM
from glm_universal.evaluation import replay as rp
from glm_universal.evaluation.cases import CASES
from glm_universal.reasoning import evidence_in_use_study as eus
from glm_universal.runtime import evidence as evm


def _run(argv):
    out = io.StringIO()
    code = GLM.main(argv, out=out)
    return code, out.getvalue()


def test_result_flag_prints_the_model():
    code, text = _run(["-q", "verify force = mass * acceleration",
                       "--result", "--verify-tct"])
    rows = json.loads(text)
    assert code == 0 and len(rows) == 1
    row = rows[0]
    assert all(f in row for f in evm.FIELDS)
    assert row["status"] == "answered" and row["replayed"] is True
    assert row["boundary"] == "certified"


def test_result_flag_refusal_has_a_reason():
    code, text = _run(["-q", "meaning of justice", "--result"])
    row = json.loads(text)[0]
    assert code == 1
    assert row["status"] == "refused" and row["refusal"]


def test_without_the_flag_nothing_changes():
    code, text = _run(["-q", "verify force = mass * acceleration",
                       "-c", "1"])
    assert code == 0
    assert "holds under scalar semantics" in text
    assert not text.lstrip().startswith("[")


def test_gate_rule_on_hand_rows():
    verdicts = {name: rp.gate_passes(rp.summarise(rows))
                for name, rows in eus.hand_rows().items()}
    assert verdicts == {"clean": True, "failed_replay": False,
                        "unanswered": False, "error": False, "absent": True}


def test_gate_on_one_case():
    case = [c for c in CASES if c.id == "verify-newton"]
    report = rp.replay_gate(case, jobs=1)
    assert rp.gate_passes(report)
    assert report["verified"] == report["replayable"] == 1


def test_lean_half_declared():
    lean = eus._lean()
    assert lean["theorems"] == list(eus.LEAN_THEOREMS)
    assert lean["sorry"] == 0


def test_stored_measurement_when_current():
    report = eus.evidence_in_use_report()
    if not report.get("available"):
        return
    assert report["met"] == report["taken"]
