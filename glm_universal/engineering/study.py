"""``glm_universal.engineering.study`` -- the engineering measurement, whole.

One report, four evidence producers, scores never pooled
--------------------------------------------------------
The session record's architecture is kept: each capability produces its own
evidence and nothing here averages them into one "validity" figure.

* **formula wheels** -- the 41 preregistered cases of the corrected study,
  read at the reference registry and at the GLM register's EXT10 and SI7
  layers; derivability per wheel and across the union of the ten wheels;
  every spoke the axioms generate.
* **Smith chart** -- the 16 transformation and geometry checks, and one exact
  L-section match over a rational band.
* **analogies** -- the structure check of both electro-mechanical
  dictionaries, a scrambled control, and the degeneracy guard.
* **delta-sigma** -- the six checks declared in
  :data:`glm_universal.engineering.delta_sigma.CHECKS`.
* **language** -- the held-out engineering questions of
  :mod:`glm_universal.evaluation.engineering_heldout`, asked through the
  surface; the baseline (both existing paths, measured before this package
  existed) and the stress set's first run are frozen constants there.

:func:`evidence_envelopes` wraps each producer in the envelope the record
recommends (claim, capability, protocol hash, outcome, limitations) so a later
consumer can compare evidence without re-deriving what it means.

Everything is recomputed on each call -- about two seconds -- so there is no
cache to go stale.  Exact and float-free.
"""

from __future__ import annotations

import json
from typing import Dict, List

from . import analogy, delta_sigma, smith, speak, wheels
from .. import integrity
from ..evaluation import engineering_heldout as held

__all__ = ["interference", "language_report", "engineering_report",
           "evidence_envelopes",
           "FACULTY_OF_FRAME"]

#: D15: what a right answer from each frame is worth.
FACULTY_OF_FRAME: Dict[str, str] = {
    "derive": "derive", "wheel": "derive", "check": "derive",
    "smith": "derive", "resonance": "derive", "delta-sigma": "derive",
    "analogy": "derive or address (translation derives; a counterpart "
               "is read off a declared dictionary)",
}


def _tally(questions) -> Dict[str, object]:
    counts = {"correct": 0, "wrong": 0, "refused": 0, "correct-refusal": 0}
    faculties: Dict[str, int] = {}
    wrong: List[str] = []
    for q in questions:
        verdict, got, reason = speak.answer(q.question)
        ok = verdict == "answered"
        score = held.score_engineering(q, ok, got.text if ok else reason)
        counts[score] += 1
        if score == "correct":
            faculties[got.faculty] = faculties.get(got.faculty, 0) + 1
        if score == "wrong":
            wrong.append(q.key)
    return {"counts": counts, "faculties": faculties, "wrong": wrong}


def interference() -> Dict[str, object]:
    """How many questions the machine already answers does an engineering
    frame read?  The surface claims only to *add*; every question of the
    177-case contract set, the frozen probe (both phrasings) and the earlier
    held-out sets is offered to it, and each one it reads is listed."""
    from ..evaluation import cases, heldout
    from ..reasoning import blockers
    texts = [c.question for c in cases.CASES]
    texts += [q.question for qs in heldout.ALL_SETS.values() for q in qs]
    for p in blockers.PROBE:
        texts += [p.question, p.paraphrase]
    read = [t for t in texts if speak.answer(t)[0] != "unread"]
    return {"offered": len(texts), "read": read}


def language_report() -> Dict[str, object]:
    per_set = {name: _tally(qs) for name, qs in held.ALL_SETS.items()}
    total = {k: sum(s["counts"][k] for s in per_set.values())
             for k in ("correct", "wrong", "refused", "correct-refusal")}
    return {"sets": per_set, "total": total,
            "questions": sum(len(qs) for qs in held.ALL_SETS.values()),
            "baseline": dict(held.BASELINE_FIRST_RUN),
            "stress_now": _tally(held.STRESS),
            "stress_first_run": dict(held.STRESS_FIRST_RUN),
            "interference": interference()}


def engineering_report() -> Dict[str, object]:
    ds = delta_sigma.delta_sigma_report()
    sr = smith.smith_report()
    match = sr["match"]
    return {
        "wheels": wheels.wheels_report(),
        "smith": {"checks": sr["checks"], "passed": sr["passed"],
                  "failed": sr["failed"],
                  "match": {k: str(v) for k, v in match.items()}},
        "analogy": analogy.analogy_report(),
        "delta_sigma": {"passed": ds["passed"],
                        "checks": [[c, bool(ok)] for c, ok in ds["checks"]],
                        "periods": ds["periods"],
                        "gains_db_floor": ds["gains_db_floor"],
                        "second_order_peak_state":
                            ds["second_order_peak_state"]},
        "language": language_report(),
    }


def _hash(obj) -> str:
    """The protocol hash of an envelope: an integrity digest of the
    protocol's declaration (D3), so two envelopes can be told to come from
    the same protocol.  It addresses nothing."""
    return integrity.sha256_hex(json.dumps(obj, sort_keys=True,
                                           default=str).encode())


def evidence_envelopes() -> List[Dict[str, object]]:
    """One envelope per producer, in the record's recommended shape."""
    rep = engineering_report()
    w, s, a, d = (rep["wheels"], rep["smith"], rep["analogy"],
                  rep["delta_sigma"])
    return [
        {"claim_id": "ENG-WHEELS", "capability": "formula wheels",
         "protocol_hash": _hash([(x.id, x.axioms, [c.equation for c in
                                                   x.cases])
                                 for x in wheels.WHEELS]),
         "observations": w, "expected_outcome": "41/41 at every layer",
         "outcome_type": "algebraically_derived / dimensionally_consistent",
         "limitations": "monomial laws only; no sums, signs, phase or "
                        "tensor contraction"},
        {"claim_id": "ENG-SMITH", "capability": "Smith chart",
         "protocol_hash": _hash([c for c, _ in smith.smith_checks()]),
         "observations": s, "expected_outcome": "16/16",
         "outcome_type": "exact transformation checks",
         "limitations": "ideal lumped components, lossless, one synthetic "
                        "load"},
        {"claim_id": "ENG-ANALOGY", "capability": "electro-mechanical "
                                                  "analogy",
         "protocol_hash": _hash([analogy.ELECTRICAL_AXIOMS,
                                 analogy.MECHANICAL_AXIOMS]),
         "observations": a,
         "expected_outcome": "force-voltage 9/9 both ways",
         "outcome_type": "structure preservation",
         "limitations": "series lumped topology only"},
        {"claim_id": "ENG-DELTA-SIGMA", "capability": "delta-sigma",
         "protocol_hash": _hash(list(delta_sigma.CHECKS)),
         "observations": d, "expected_outcome": "6/6",
         "outcome_type": "preregistered checks",
         "limitations": "idealised one-bit loops, one window, no analogue "
                        "effects"},
    ]
