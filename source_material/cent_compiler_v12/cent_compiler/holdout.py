"""D6 retrodictive holdout: freeze the library before a dated cutoff.

The library is a hand-declared set of source mechanisms with publication dates
before ``CUTOFF_YEAR``.  The cases are transfers whose target publications are
after the cutoff.  Retrieval uses only structural signatures; target labels come
from the cited historical publications, never from a mechanism card's
``supported_operations`` field.

This is deliberately a small, curated corpus.  It is a regression and
false-positive test, not independent proof of general retrodictive power.  The
Bresenham/delta-sigma candidate from the directive is recorded as excluded: the
source algorithm was published after 1940, so it cannot belong to the frozen
library.

Direction policy: the directive's arrow is conceptual shorthand, not a temporal
order.  A case always names the post-cutoff publication as the target and the
pre-cutoff principle as the source.  Where the shorthand's order conflicts with
publication history, the dated direction is used and recorded in the case id.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .transfer_engine import BehaviorSignature

SCHEMA = "cent-retrodictive-holdout/1"
MECHANISM_SCHEMA = "cent-holdout-mechanism/1"
CASE_SCHEMA = "cent-holdout-case/1"
CUTOFF_YEAR = 1940
DEFAULT_LIMIT = 3


def _tokens(value: str) -> set[str]:
    return set(str(value).lower().replace("/", " ").replace("_", " ").split())


def _overlap(left: str, right: str) -> bool:
    return bool(_tokens(left) & _tokens(right))


def score_signature(operation: BehaviorSignature, candidate: BehaviorSignature) -> tuple[int, list[str]]:
    """Apply the transfer engine's structural score terms to the frozen library.

    The live registry's constant base and card-support bonus are omitted because
    holdout sources are not live mechanism cards. Only the ordering is used.
    """
    score = 0
    reasons: list[str] = []
    overlap = set(operation.primitive_chain) & set(candidate.primitive_chain)
    if overlap:
        score += 2 * len(overlap)
        reasons.append("primitive overlap: " + ", ".join(sorted(overlap)))
    if operation.stateful == candidate.stateful:
        score += 3
        reasons.append(f"stateful {str(operation.stateful).lower()} match")
    if operation.feedback == candidate.feedback:
        score += 3
        reasons.append(f"feedback {str(operation.feedback).lower()} match")
    if _overlap(operation.encoding, candidate.encoding):
        score += 1
        reasons.append("encoding overlap")
    if _overlap(operation.nonlinearity, candidate.nonlinearity):
        score += 1
        reasons.append("nonlinearity overlap")
    if _overlap(operation.precision, candidate.precision):
        score += 1
        reasons.append("precision overlap")
    if set(operation.conserved_quantities) & set(candidate.conserved_quantities):
        score += 2
        reasons.append("conserved-quantity overlap")
    return score, reasons


@dataclass(frozen=True)
class FrozenMechanism:
    """A source principle declared available before the cutoff."""

    id: str
    name: str
    source_domain: str
    source_year: int | None
    source_date: str
    signature: BehaviorSignature
    citation: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip() or not self.source_domain.strip():
            raise ValueError("holdout mechanism needs an id, name and source domain")
        if self.source_year is not None and self.source_year >= CUTOFF_YEAR:
            raise ValueError(
                f"{self.id}: source year {self.source_year} is not before the "
                f"cutoff {CUTOFF_YEAR}"
            )
        if not self.source_date.strip() or not self.citation.strip():
            raise ValueError(f"{self.id}: source date and citation are required")
        self.signature.validate()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": MECHANISM_SCHEMA,
            "id": self.id,
            "name": self.name,
            "source_domain": self.source_domain,
            "source_year": self.source_year,
            "source_date": self.source_date,
            "signature": self.signature.as_dict(),
            "citation": self.citation,
            "frozen_before": CUTOFF_YEAR,
        }


@dataclass(frozen=True)
class HoldoutCase:
    """A transfer whose target publication is after the cutoff."""

    id: str
    target_domain: str
    target_operation: str
    target_year: int
    expected_mechanism: str
    target_signature: BehaviorSignature
    required_observable: str
    forbidden_traits: Mapping[str, str]
    citation: str
    provenance: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.target_domain.strip() or not self.target_operation.strip():
            raise ValueError("holdout case needs an id, target domain and operation")
        if self.target_year <= CUTOFF_YEAR:
            raise ValueError(
                f"{self.id}: target year {self.target_year} is not after the "
                f"cutoff {CUTOFF_YEAR}"
            )
        if not self.required_observable.strip() or not self.citation.strip():
            raise ValueError(f"{self.id}: required observable and citation are required")
        self.target_signature.validate()
        object.__setattr__(self, "forbidden_traits", dict(self.forbidden_traits))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CASE_SCHEMA,
            "id": self.id,
            "target_domain": self.target_domain,
            "target_operation": self.target_operation,
            "target_year": self.target_year,
            "expected_mechanism": self.expected_mechanism,
            "target_signature": self.target_signature.as_dict(),
            "required_observable": self.required_observable,
            "forbidden_traits": dict(self.forbidden_traits),
            "citation": self.citation,
            "provenance": self.provenance,
            "status": "post-cutoff",
        }


@dataclass(frozen=True)
class ExcludedCase:
    id: str
    reason: str
    citation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CASE_SCHEMA,
            "id": self.id,
            "status": "excluded",
            "reason": self.reason,
            "citation": self.citation,
        }


@dataclass(frozen=True)
class NegativeControl:
    """A pre-registered target with no licensed source in the frozen library.

    This is a strict operator control, not a historical recall case.  The target
    requires a primitive that no frozen source contains, so a retrieved source
    is a false positive for the exact target even when it has structural overlap.
    """

    id: str
    target_domain: str
    target_operation: str
    target_year: int
    target_signature: BehaviorSignature
    required_primitive: str
    forbidden_traits: Mapping[str, str]
    citation: str
    provenance: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.target_domain.strip() or not self.target_operation.strip():
            raise ValueError("negative control needs an id, target domain and operation")
        if self.target_year <= CUTOFF_YEAR:
            raise ValueError(
                f"{self.id}: target year {self.target_year} is not after the cutoff {CUTOFF_YEAR}"
            )
        if not self.required_primitive.strip() or not self.citation.strip():
            raise ValueError(f"{self.id}: required primitive and citation are required")
        self.target_signature.validate()
        object.__setattr__(self, "forbidden_traits", dict(self.forbidden_traits))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CASE_SCHEMA,
            "id": self.id,
            "status": "negative-control",
            "target_domain": self.target_domain,
            "target_operation": self.target_operation,
            "target_year": self.target_year,
            "expected_mechanism": None,
            "target_signature": self.target_signature.as_dict(),
            "required_primitive": self.required_primitive,
            "forbidden_traits": dict(self.forbidden_traits),
            "citation": self.citation,
            "provenance": self.provenance,
            "rationale": self.rationale,
        }


def _frozen_mechanisms() -> tuple[FrozenMechanism, ...]:
    return (
        FrozenMechanism(
            id="metallurgical-annealing",
            name="metallurgical annealing",
            source_domain="metallurgy",
            source_year=None,
            source_date="antiquity; no single publication date claimed",
            signature=BehaviorSignature(
                primitive_chain=("sat", "hysteresis", "noise"),
                stateful=True,
                feedback=False,
                conserved_quantities=("thermal equilibrium",),
                nonlinearity="stochastic thermal relaxation",
                encoding="state",
                precision="statistical",
            ),
            citation="traditional metallurgical annealing; no dated publication claimed",
        ),
        FrozenMechanism(
            id="random-walk",
            name="random walk",
            source_domain="probability",
            source_year=1905,
            source_date="Pearson, Nature 72 (1905)",
            signature=BehaviorSignature(
                primitive_chain=("accum", "spatial"),
                stateful=False,
                feedback=False,
                conserved_quantities=("probability",),
                nonlinearity="linear",
                encoding="graph",
                precision="exact rational",
            ),
            citation="Pearson, 'The problem of the random walk', Nature 72 (1905)",
        ),
        FrozenMechanism(
            id="ising-spin",
            name="Ising spin model",
            source_domain="statistical mechanics",
            source_year=1925,
            source_date="Ising, Zeitschrift für Physik 31 (1925)",
            signature=BehaviorSignature(
                primitive_chain=("sum", "sat", "mult"),
                stateful=True,
                feedback=True,
                conserved_quantities=("energy",),
                nonlinearity="bistable",
                encoding="spin lattice",
                precision="statistical",
            ),
            citation="Ising, 'Beitrag zur Theorie des Ferromagnetismus', Z. Phys. 31 (1925)",
        ),
        FrozenMechanism(
            id="kinetic-theory",
            name="Boltzmann kinetic theory",
            source_domain="kinetic theory",
            source_year=1872,
            source_date="Boltzmann, further studies on thermal equilibrium (1872)",
            signature=BehaviorSignature(
                primitive_chain=("sum", "mult", "grad"),
                stateful=True,
                feedback=False,
                conserved_quantities=("mass", "momentum"),
                nonlinearity="collision",
                encoding="distribution",
                precision="statistical",
            ),
            citation="Boltzmann, 'Weitere Studien über das Wärmegleichgewicht' (1872)",
        ),
        FrozenMechanism(
            id="soap-film",
            name="soap-film minimal surface",
            source_domain="surface physics",
            source_year=1873,
            source_date="Plateau, Statique expérimentale et théorique... (1873)",
            signature=BehaviorSignature(
                primitive_chain=("spatial", "boundary"),
                stateful=False,
                feedback=False,
                conserved_quantities=("area",),
                nonlinearity="minimal surface",
                encoding="geometry",
                precision="exact rational",
            ),
            citation="Plateau, Statique expérimentale et théorique des liquides (1873)",
        ),
    )


def _cases() -> tuple[HoldoutCase, ...]:
    return (
        HoldoutCase(
            id="simulated-annealing",
            target_domain="combinatorial optimization",
            target_operation="simulated_annealing",
            target_year=1983,
            expected_mechanism="metallurgical-annealing",
            target_signature=BehaviorSignature(
                primitive_chain=("sat", "hysteresis", "noise"),
                stateful=True,
                feedback=False,
                conserved_quantities=("thermal equilibrium",),
                nonlinearity="stochastic thermal relaxation",
                encoding="state",
                precision="statistical",
            ),
            required_observable="a temperature schedule that accepts uphill moves and converges to a low-cost state",
            forbidden_traits={"precision": "exact rational"},
            citation="Kirkpatrick, Gelatt & Vecchi, Science 220, 671–680 (1983), doi:10.1126/science.220.4598.671",
            provenance="https://www.science.org/doi/10.1126/science.220.4598.671",
        ),
        HoldoutCase(
            id="resistor-network-random-walk",
            target_domain="electrical networks",
            target_operation="effective_resistance",
            target_year=1984,
            expected_mechanism="random-walk",
            target_signature=BehaviorSignature(
                primitive_chain=("sum", "neg"),
                stateful=False,
                feedback=False,
                conserved_quantities=("potential",),
                nonlinearity="linear",
                encoding="graph",
                precision="exact rational",
            ),
            required_observable="effective resistance as an exact graph potential with a random-walk interpretation",
            forbidden_traits={"precision": "statistical"},
            citation=(
                "Doyle & Snell, Random Walks and Electric Networks, "
                "MAA Carus Monograph 22 (1984); Kakutani's 1945 connection is "
                "acknowledged as earlier"
            ),
            provenance="https://math.dartmouth.edu/~doyle/docs/walks/walks.pdf",
        ),
        HoldoutCase(
            id="hopfield-associative-memory",
            target_domain="neural computation",
            target_operation="associative_memory",
            target_year=1982,
            expected_mechanism="ising-spin",
            target_signature=BehaviorSignature(
                primitive_chain=("sum", "mult", "sat"),
                stateful=True,
                feedback=True,
                conserved_quantities=("energy",),
                nonlinearity="bistable",
                encoding="spin lattice",
                precision="statistical",
            ),
            required_observable="content-addressable recall as a collective energy minimum of binary spins",
            forbidden_traits={"encoding": "geometry"},
            citation="Hopfield, PNAS 79(8), 2554–2558 (1982), doi:10.1073/pnas.79.8.2554",
            provenance="https://www.pnas.org/doi/10.1073/pnas.79.8.2554",
        ),
        HoldoutCase(
            id="lattice-boltzmann-kinetic",
            target_domain="computational fluid dynamics",
            target_operation="lattice_boltzmann",
            target_year=1988,
            expected_mechanism="kinetic-theory",
            target_signature=BehaviorSignature(
                primitive_chain=("sum", "grad", "spatial"),
                stateful=True,
                feedback=False,
                conserved_quantities=("mass", "momentum"),
                nonlinearity="collision",
                encoding="distribution",
                precision="statistical",
            ),
            required_observable="a discrete distribution function whose collision and streaming recover hydrodynamic moments",
            forbidden_traits={"nonlinearity": "minimal surface"},
            citation="McNamara & Zanetti, Phys. Rev. Lett. 61, 2332 (1988), doi:10.1103/PhysRevLett.61.2332",
            provenance="https://link.aps.org/doi/10.1103/PhysRevLett.61.2332",
        ),
        HoldoutCase(
            id="steiner-tree-soap-film",
            target_domain="computational geometry",
            target_operation="steiner_tree",
            target_year=1941,
            expected_mechanism="soap-film",
            target_signature=BehaviorSignature(
                primitive_chain=("spatial", "grad"),
                stateful=False,
                feedback=False,
                conserved_quantities=("length",),
                nonlinearity="minimal network",
                encoding="geometry",
                precision="exact rational",
            ),
            required_observable="a minimum-length network with 120-degree Steiner junctions",
            forbidden_traits={"encoding": "spin lattice"},
            citation="Courant & Robbins, What Is Mathematics?, Oxford University Press (1941), ch. VII",
            provenance="https://mathweb.ucsd.edu/~ronspubs/14_02_Steiner.pdf",
        ),
    )


def _negative_controls() -> tuple[NegativeControl, ...]:
    return (
        NegativeControl(
            id="rsa-modular-exponentiation",
            target_domain="public-key cryptography",
            target_operation="modular_exponentiation",
            target_year=1978,
            target_signature=BehaviorSignature(
                primitive_chain=("exp", "mod", "mult"),
                stateful=False,
                feedback=False,
                conserved_quantities=("modulus",),
                nonlinearity="modular",
                encoding="integer",
                precision="exact",
            ),
            required_primitive="mod",
            forbidden_traits={"precision": "statistical"},
            citation="Rivest, Shamir & Adleman, Communications of the ACM 21(2), 120–126 (1978)",
            provenance="https://dl.acm.org/doi/10.1145/359340.359342",
            rationale=(
                "Strict operator control: RSA's public-key operation needs modular "
                "exponentiation. No frozen source contains mod, so the machine must "
                "report no licensed source rather than rank structural analogues; "
                "the known number-theory source is outside this curated library."
            ),
        ),
    )


def _excluded() -> tuple[ExcludedCase, ...]:
    return (
        ExcludedCase(
            id="bresenham-delta-sigma",
            reason=(
                "Bresenham's algorithm was published in 1965, after the 1940 "
                "cutoff, so it cannot be in the frozen library; the D4 one-tick "
                "correspondence is internal evidence, not a dated external transfer."
            ),
            citation="Bresenham, IBM Systems Journal 4(1), 25–30 (1965)",
        ),
    )


def _finite_map(value: Mapping[str, str]) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}


def _matches_trait(signature: BehaviorSignature, field: str, value: str) -> bool:
    actual = getattr(signature, field, None)
    return actual == value


def _rank(case: HoldoutCase | NegativeControl, mechanisms: Iterable[FrozenMechanism]) -> list[dict[str, Any]]:
    rows = []
    for mechanism in mechanisms:
        score, reasons = score_signature(case.target_signature, mechanism.signature)
        rows.append(
            {
                "mechanism": mechanism.id,
                "score": score,
                "reasons": reasons,
                "false_positive": any(
                    _matches_trait(mechanism.signature, field, value)
                    for field, value in _finite_map(case.forbidden_traits).items()
                ),
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["mechanism"]))
    return rows


def build_ledger(limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """Run the frozen holdout and report recall, misses and false positives."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("holdout limit must be a positive integer")
    frozen = _frozen_mechanisms()
    cases = _cases()
    results: list[dict[str, Any]] = []
    false_positive_candidates: list[str] = []
    misses: list[str] = []
    for case in cases:
        ranked = _rank(case, frozen)
        retrieved = ranked[:limit]
        expected_rank = next(
            (index + 1 for index, row in enumerate(ranked) if row["mechanism"] == case.expected_mechanism),
            None,
        )
        expected = next(
            (row for row in ranked if row["mechanism"] == case.expected_mechanism),
            None,
        )
        passed = expected_rank is not None and expected_rank <= limit
        if not passed:
            misses.append(f"{case.id}/{case.expected_mechanism}")
        false_positives = [row["mechanism"] for row in retrieved if row["false_positive"]]
        false_positive_candidates.extend(
            f"{case.id}/{mechanism}" for mechanism in false_positives
        )
        results.append(
            {
                **case.as_dict(),
                "expected_rank": expected_rank,
                "expected_score": expected["score"] if expected else None,
                "retrieved": [
                    {
                        "mechanism": row["mechanism"],
                        "score": row["score"],
                        "false_positive": row["false_positive"],
                        "reasons": row["reasons"],
                    }
                    for row in retrieved
                ],
                "false_positives": false_positives,
                "unlabelled": [
                    row["mechanism"]
                    for row in retrieved
                    if row["mechanism"] != case.expected_mechanism
                    and not row["false_positive"]
                ],
                "passed": passed,
                "originated": bool(passed and expected and expected["score"] > 0),
            }
        )
    recall = sum(1 for result in results if result["passed"])
    total = len(results)
    controls = _negative_controls()
    negative_results: list[dict[str, Any]] = []
    negative_false_positives: list[str] = []
    negative_misses: list[str] = []
    for control in controls:
        ranked = _rank(control, frozen)
        retrieved = ranked[:limit]
        false_positives = []
        for row in retrieved:
            mechanism = next(
                item for item in frozen if item.id == row["mechanism"]
            )
            if (
                control.required_primitive not in mechanism.signature.primitive_chain
                or row["false_positive"]
            ):
                false_positives.append(row["mechanism"])
        missing = [
            mechanism.id
            for mechanism in frozen
            if control.required_primitive not in mechanism.signature.primitive_chain
        ]
        no_licensed_source = len(missing) == len(frozen)
        if not no_licensed_source:
            negative_false_positives.extend(
                f"{control.id}/{mechanism}" for mechanism in false_positives
            )
        if no_licensed_source:
            negative_misses.append(
                f"{control.id}: required primitive {control.required_primitive!r} "
                "is absent from every frozen source"
            )
            retrieved = []
            false_positives = []
        negative_results.append(
            {
                **control.as_dict(),
                "retrieved": [
                    {
                        "mechanism": row["mechanism"],
                        "score": row["score"],
                        "false_positive": row["mechanism"] in false_positives,
                        "reasons": row["reasons"],
                    }
                    for row in retrieved
                ],
                "false_positives": false_positives,
                "coverage_miss": no_licensed_source,
                "outcome": (
                    "no_licensed_source"
                    if no_licensed_source
                    else ("fail" if false_positives else "pass")
                ),
            }
        )
    generated = _excluded()
    return {
        "schema": SCHEMA,
        "cutoff_year": CUTOFF_YEAR,
        "direction_policy": (
            "target <- source; the target is the post-cutoff publication. "
            "The directive's arrow is conceptual shorthand, not temporal order."
        ),
        "frozen_library": [mechanism.as_dict() for mechanism in frozen],
        "cases": [case.as_dict() for case in cases],
        "excluded": [case.as_dict() for case in generated],
        "results": results,
        "negative_controls": negative_results,
        "metrics": {
            "cases": total,
            "recalled": recall,
            "recall": f"{recall}/{total}",
            "candidate_recall": recall / total if total else 0.0,
            "misses": misses,
            "false_positive_candidates": false_positive_candidates,
            "false_positive_cases": sorted(
                {
                    item.split("/", 1)[0]
                    for item in false_positive_candidates
                }
            ),
            "false_positive_rate": (
                f"{len(false_positive_candidates)}/"
                f"{sum(len(result['retrieved']) for result in results)}"
            ),
            "excluded_cases": len(generated),
            "negative_controls": len(negative_results),
            "negative_control_false_positive_candidates": negative_false_positives,
            "negative_control_false_positive_rate": (
                f"{len(negative_false_positives)}/"
                f"{sum(len(result['retrieved']) for result in negative_results)}"
            ),
            "negative_control_no_licensed_source": any(
                result["outcome"] == "no_licensed_source"
                for result in negative_results
            ),
            "negative_control_misses": negative_misses,
            "negative_control_outcome": (
                "no_licensed_source"
                if negative_results
                and all(result["outcome"] == "no_licensed_source" for result in negative_results)
                else (
                    "fail"
                    if any(result["outcome"] == "fail" for result in negative_results)
                    else "pass"
                )
            ),
        },
        "gaps": [
            "the frozen library is a separate hand-declared holdout library, not a snapshot of the live mechanism registry",
            "the frozen library is hand-declared; no external historical corpus is used",
            "the corpus has five evaluated cases and one excluded candidate; it is a regression test, not general evidence",
            "the random-walk/electric-network case cites Doyle & Snell 1984; Kakutani's 1945 connection is earlier and is not claimed as first-ever",
            "two targets (simulated annealing and Hopfield associative memory) share a signature with their source, so those cases test provenance recall more than structural re-description",
            "false-positive constraints are author-declared from the target observable and were not independently pre-registered",
            "the negative control is a strict operator control, not a historical recall case; its failure is reported, not counted as positive recall",
            "target retrieval is structural signature matching, not a proof of the historical analogy",
        ],
        "ok": bool(frozen and cases and all(
            isinstance(mechanism.source_year, int) and mechanism.source_year < CUTOFF_YEAR
            or mechanism.source_year is None
            for mechanism in frozen
        )),
    }


def write_ledger(path: str, payload: Mapping[str, Any] | None = None) -> str:
    import json
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload or build_ledger(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(target)


def render_ledger(payload: Mapping[str, Any] | None = None) -> str:
    ledger = payload or build_ledger()
    metrics = ledger.get("metrics") or {}
    lines = ["=" * 78, "D6 RETRODICTIVE HOLDOUT", "=" * 78]
    lines.append(
        f"cutoff: {ledger.get('cutoff_year')} · frozen mechanisms: "
        f"{len(ledger.get('frozen_library') or ())} · cases: {metrics.get('cases')}"
    )
    lines.append(
        f"recall: {metrics.get('recall')} · misses: {len(metrics.get('misses') or ())} · "
        f"false-positive candidates: {len(metrics.get('false_positive_candidates') or ())}"
    )
    lines.append("")
    for result in ledger.get("results") or ():
        lines.append(
            f"{result.get('id')} → {result.get('expected_mechanism')} "
            f"(rank {result.get('expected_rank')}, {'pass' if result.get('passed') else 'MISS'})"
        )
        lines.append(
            f"  target {result.get('target_year')} · {result.get('target_domain')}"
        )
        lines.append("  retrieved: " + ", ".join(
            f"{row.get('mechanism')}:{row.get('score')}"
            for row in result.get("retrieved") or ()
        ))
        if result.get("false_positives"):
            lines.append("  false positives: " + ", ".join(result["false_positives"]))
        if not result.get("passed"):
            lines.append("  miss: expected mechanism is outside the declared top three")
    for control in ledger.get("negative_controls") or ():
        retrieved = [
            row.get("mechanism", "") for row in control.get("retrieved") or []
        ]
        lines.append(
            f"NEGATIVE CONTROL {control.get('id')}: {control.get('outcome')} "
            f"(required {control.get('required_primitive')!r}, "
            f"retrieved {', '.join(retrieved)})"
        )
        if control.get("outcome") == "no_licensed_source":
            lines.append(
                "  no licensed source: no frozen source contains the required primitive"
            )
        if control.get("false_positives"):
            lines.append("  false positives: " + ", ".join(control["false_positives"]))
    for case in ledger.get("excluded") or ():
        lines.append(f"EXCLUDED {case.get('id')}: {case.get('reason')}")
    return "\n".join(lines)


__all__ = [
    "CASE_SCHEMA",
    "CUTOFF_YEAR",
    "DEFAULT_LIMIT",
    "ExcludedCase",
    "FrozenMechanism",
    "HoldoutCase",
    "MECHANISM_SCHEMA",
    "NegativeControl",
    "SCHEMA",
    "build_ledger",
    "render_ledger",
    "score_signature",
    "write_ledger",
]
