"""The benchmark harness: evidence tiers, tasks, scores and the registry.

A benchmark in this package is not a number.  It is a *declaration made
before the run* -- what the population is, what counts as a pass, what the
baseline is, and what a null result would look like -- followed by the score
that declaration produced.  The declaration travels with the score, in the
same record, so a headline figure can never be read without the contract it
was measured against.

Three rules are enforced by the types here rather than by convention.

* **The tier is declared first.**  :class:`EvidenceTier` is a required field
  of every :class:`Suite`, and :func:`run_suite` copies it into the result.
  A suite cannot report a score without having said what the score means.
* **Nothing is a float.**  Scores are :class:`fractions.Fraction`, rendered
  as ``"n/d"`` strings when they are serialised.  A benchmark that reported
  ``0.8333333333333334`` would be reporting the arithmetic and not the
  measurement.
* **Negative results ride along.**  :attr:`SuiteScore.findings` is where a
  suite records what it found that was *not* a pass -- a known failure mode,
  a divergence between two semantics, a place the system is confidently
  wrong.  :func:`benchmark_report` surfaces them beside the scores, and the
  test suite checks that the suites which have them still report them.

Determinism: no suite may sample without recording a seed in its tier.  The
run id written into ``results/`` is a hash of the results themselves, so two
runs of the same code produce byte-identical output and a changed number is
visible as a changed id.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

__all__ = [
    "EvidenceTier", "TaskOutcome", "Finding", "SuiteScore", "Suite",
    "register", "suite_names", "get_suite", "run_suite", "run_all",
    "benchmark_report", "write_results", "results_dir", "frac_str",
]


# ===========================================================================
# 1.  SMALL HELPERS
# ===========================================================================

def frac_str(value: Fraction) -> str:
    """A :class:`Fraction` as ``"n/d"`` -- never as a float."""
    return f"{value.numerator}/{value.denominator}"


def _ratio(hits: int, total: int) -> Fraction:
    """``hits/total`` exactly, with an empty population scoring zero."""
    if total <= 0:
        return Fraction(0)
    return Fraction(hits, total)


# ===========================================================================
# 2.  THE CONTRACT, DECLARED BEFORE THE RUN
# ===========================================================================

@dataclass(frozen=True)
class EvidenceTier:
    """What a suite's score is allowed to mean.

    Attributes
    ----------
    tier:
        ``"exhaustive"`` when the population is every case there is,
        ``"curated"`` when it is a hand-written list with external ground
        truth, ``"sampled"`` when it is drawn from a larger population -- in
        which case ``seed`` must be set.
    population:
        What was measured, and how big it is.
    ground_truth:
        Where the right answers come from.  A benchmark whose ground truth is
        the system's own output is measuring its own consistency, and must
        say so here.
    pass_criterion:
        What makes one task a pass.
    baseline:
        What a system that did nothing interesting would score, and why.
    null_result:
        What would be observed if the mechanism under test did not work.
    seed:
        Required for ``"sampled"``; forbidden otherwise.
    """

    tier: str
    population: str
    ground_truth: str
    pass_criterion: str
    baseline: str
    null_result: str
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.tier not in ("exhaustive", "curated", "sampled"):
            raise ValueError(
                f"EvidenceTier: unknown tier {self.tier!r}; known tiers are "
                f"'exhaustive', 'curated' and 'sampled'")
        if self.tier == "sampled" and self.seed is None:
            raise ValueError(
                "EvidenceTier: a sampled benchmark must carry an explicit "
                "seed in its recorded parameters")
        if self.tier != "sampled" and self.seed is not None:
            raise ValueError(
                f"EvidenceTier: a {self.tier!r} benchmark does not sample, "
                f"so it may not carry a seed")

    def as_dict(self) -> Dict[str, object]:
        record: Dict[str, object] = {
            "tier": self.tier,
            "population": self.population,
            "ground_truth": self.ground_truth,
            "pass_criterion": self.pass_criterion,
            "baseline": self.baseline,
            "null_result": self.null_result,
        }
        if self.seed is not None:
            record["seed"] = self.seed
        return record


# ===========================================================================
# 3.  ONE TASK, AND ONE THING A SUITE FOUND
# ===========================================================================

@dataclass(frozen=True)
class TaskOutcome:
    """One scored task: what was asked, what was expected, what came back."""

    task: str
    passed: bool
    expected: str
    observed: str
    note: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {"task": self.task, "passed": self.passed,
                "expected": self.expected, "observed": self.observed,
                "note": self.note}


@dataclass(frozen=True)
class Finding:
    """Something a suite found that is not a pass or a fail.

    A known failure mode, a divergence between two ways of reading the same
    question, or a case where the system is confidently wrong for a reason
    that is understood.  Findings are reported with the score, never instead
    of it.
    """

    key: str
    statement: str
    detail: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {"key": self.key, "statement": self.statement,
                "detail": self.detail}


# ===========================================================================
# 4.  THE SCORE
# ===========================================================================

@dataclass(frozen=True)
class SuiteScore:
    """A suite's result, inseparable from the contract it was run under."""

    name: str
    question: str
    tier: EvidenceTier
    outcomes: Tuple[TaskOutcome, ...]
    baseline_score: Fraction
    findings: Tuple[Finding, ...] = ()
    measurements: Mapping[str, str] = field(default_factory=dict)

    # -- derived ------------------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.outcomes)

    @property
    def passed(self) -> int:
        return sum(1 for o in self.outcomes if o.passed)

    @property
    def score(self) -> Fraction:
        return _ratio(self.passed, self.total)

    @property
    def beats_baseline(self) -> bool:
        return self.score > self.baseline_score

    @property
    def verdict(self) -> str:
        """``"pass"``, ``"null"`` or ``"below baseline"``.

        A score equal to the baseline is a *null* result and is named as one:
        the mechanism under test did not show itself.
        """
        if self.score > self.baseline_score:
            return "pass"
        if self.score == self.baseline_score:
            return "null"
        return "below baseline"

    @property
    def failures(self) -> Tuple[TaskOutcome, ...]:
        return tuple(o for o in self.outcomes if not o.passed)

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "question": self.question,
            "tier": self.tier.as_dict(),
            "total": self.total,
            "passed": self.passed,
            "score": frac_str(self.score),
            "baseline": frac_str(self.baseline_score),
            "verdict": self.verdict,
            "measurements": dict(self.measurements),
            "findings": [f.as_dict() for f in self.findings],
            "outcomes": [o.as_dict() for o in self.outcomes],
        }


# ===========================================================================
# 5.  THE REGISTRY
# ===========================================================================

@dataclass(frozen=True)
class Suite:
    """A named benchmark: a question, a declared tier, and a way to run it."""

    name: str
    question: str
    tier: EvidenceTier
    runner: Callable[[], SuiteScore]


_REGISTRY: Dict[str, Suite] = {}


def register(suite: Suite) -> Suite:
    """Add a suite to the registry, refusing a duplicate name."""
    if suite.name in _REGISTRY:
        raise ValueError(f"register: suite {suite.name!r} already exists")
    _REGISTRY[suite.name] = suite
    return suite


def suite_names() -> Tuple[str, ...]:
    """Every registered suite, in a fixed order."""
    return tuple(sorted(_REGISTRY))


def get_suite(name: str) -> Suite:
    """The suite of that name, or a :class:`KeyError` naming the known ones."""
    if name not in _REGISTRY:
        raise KeyError(f"get_suite: unknown suite {name!r}; known suites are "
                       f"{list(suite_names())}")
    return _REGISTRY[name]


# ===========================================================================
# 6.  RUNNING
# ===========================================================================

def run_suite(name: str) -> SuiteScore:
    """Run one suite and check that it honoured its own declaration."""
    suite = get_suite(name)
    score = suite.runner()
    if score.name != suite.name:
        raise ValueError(
            f"run_suite: {suite.name!r} returned a score named "
            f"{score.name!r}")
    if score.tier != suite.tier:
        raise ValueError(
            f"run_suite: {suite.name!r} reported a tier it did not declare")
    if score.total == 0:
        raise ValueError(
            f"run_suite: {suite.name!r} scored no tasks; an empty suite is a "
            f"broken suite, not a perfect one")
    return score


def run_all(names: Optional[Sequence[str]] = None) -> Tuple[SuiteScore, ...]:
    """Run every suite (or the named ones), in registry order."""
    chosen = suite_names() if names is None else tuple(names)
    return tuple(run_suite(n) for n in chosen)


def _run_id(payload: object) -> str:
    """A content hash of the results: same code, same id, every time."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def benchmark_report(names: Optional[Sequence[str]] = None
                     ) -> Dict[str, object]:
    """Every suite's score, its declaration, and the claims they license.

    The ``claims`` list is the only place a headline number is allowed to be
    stated, and each claim carries the suite it came from and the verdict
    against the baseline, so no figure can be quoted without its contract.
    """
    scores = run_all(names)
    suites = [s.as_dict() for s in scores]
    claims = [
        {
            "suite": s.name,
            "claim": f"{s.passed}/{s.total} ({frac_str(s.score)}) "
                     f"against a baseline of {frac_str(s.baseline_score)}",
            "verdict": s.verdict,
            "tier": s.tier.tier,
        }
        for s in scores
    ]
    findings = [
        dict(f.as_dict(), suite=s.name) for s in scores for f in s.findings
    ]
    total = sum(s.total for s in scores)
    passed = sum(s.passed for s in scores)
    payload: Dict[str, object] = {
        "suites": suites,
        "claims": claims,
        "findings": findings,
        "suite_count": len(scores),
        "task_count": total,
        "passed_count": passed,
        "overall_score": frac_str(_ratio(passed, total)),
        "null_results": [s.name for s in scores if s.verdict != "pass"],
    }
    payload["run_id"] = _run_id(payload)
    return payload


# ===========================================================================
# 7.  WRITING THE RESULTS DOWN
# ===========================================================================

#: How many passing outcomes a written result file keeps.  Every *failing*
#: outcome is written whatever this is: a results file must never be shorter
#: because something went wrong.
WRITTEN_PASS_SAMPLE = 25


def _trimmed(suite: Dict[str, object]) -> Dict[str, object]:
    """A suite record with its passing outcomes sampled, failures intact."""
    outcomes = list(suite["outcomes"])          # type: ignore[arg-type]
    if len(outcomes) <= WRITTEN_PASS_SAMPLE:
        return suite
    failed = [o for o in outcomes if not o["passed"]]
    passed = [o for o in outcomes if o["passed"]][:WRITTEN_PASS_SAMPLE]
    record = dict(suite)
    record["outcomes"] = failed + passed
    record["outcomes_written"] = len(failed) + len(passed)
    record["outcomes_total"] = len(outcomes)
    record["outcomes_note"] = (
        f"every failing outcome is written; passing outcomes are sampled to "
        f"the first {WRITTEN_PASS_SAMPLE}.  The score, the run id and the "
        f"claims are computed from all {len(outcomes)}.")
    return record


def results_dir() -> str:
    """Where scores are written: ``glm_universal/benchmarks/results``."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def write_results(directory: Optional[str] = None,
                  names: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """Run the suites and write the results as data, not as prose.

    One JSON file per suite, plus ``claims.json`` holding the run id, the
    claims and the findings.  Returns the report it wrote.
    """
    target = results_dir() if directory is None else directory
    os.makedirs(target, exist_ok=True)
    report = benchmark_report(names)

    for suite in report["suites"]:              # type: ignore[union-attr]
        path = os.path.join(target, f"{suite['name']}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(_trimmed(suite), handle, indent=2, sort_keys=True)
            handle.write("\n")

    claims_path = os.path.join(target, "claims.json")
    with open(claims_path, "w", encoding="utf-8") as handle:
        json.dump({k: report[k] for k in
                   ("run_id", "suite_count", "task_count", "passed_count",
                    "overall_score", "null_results", "claims", "findings")},
                  handle, indent=2, sort_keys=True)
        handle.write("\n")
    return report
