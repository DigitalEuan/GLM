"""Audit a declared move corpus without inventing a lattice or a proof model.

The accepted document is ``cent-move-corpus/1``::

    {
      "schema": "cent-move-corpus/1",
      "provenance": "where the sequences came from",
      "moves": {
        "m1": {"vector": [1, 0], "weight": "1"},
        "m2": {"vector": [0, 1], "weight": "1"}
      },
      "sequences": [
        ["m1", "m2", "m1"],
        ["m2"]
      ]
    }

Only adjacent move IDs are used for the bigram baseline.  The default
evaluation is in-sample: every adjacent transition in the supplied sequences is
predicted by the most frequent next move for its current move, with ties broken
by the lexicographically smallest move ID.  No Laplace smoothing or
cross-validation is invented.  An optional holdout can be requested:
``holdout="study"`` follows the published study protocol (subtract only the
held-out sequence's count of the evaluated pair), while ``holdout="strict"``
removes every transition of the held-out sequence.

If every move used by the corpus has an integer vector, the report also gives
the exact net displacement of each sequence, its squared norm, the median and
mean net squared norms, and the mean squared move norm.  Those are descriptive
statistics from the supplied data, not a Leech-lattice heat kernel.

Nothing here constructs a Leech lattice, Griess algebra, Monster action, Lean
elaborator or Viazovska optimizer.  A corpus may carry integer vectors of any
dimension, but this module only audits them.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "cent-move-corpus/1"
REPORT_SCHEMA = "cent-move-corpus-report/1"


class MoveCorpusError(ValueError):
    """The declared move corpus is malformed or inconsistent."""


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _percent_text(value: Fraction) -> str:
    """Format an exact fraction as a two-decimal percentage, rounded half up."""
    scaled = value * 10000
    rounded = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    return f"{rounded // 100}.{rounded % 100:02d}%"


def _median(values: Sequence[int]) -> Fraction:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("median of an empty sequence")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return Fraction(ordered[middle])
    return Fraction(ordered[middle - 1] + ordered[middle], 2)


def _top_prediction(counts: Mapping[str, int]) -> str | None:
    """Most frequent next move, with the lexical tie-break used throughout."""
    if not counts:
        return None
    highest = max(counts.values())
    return min(move for move, count in counts.items() if count == highest)


def _holdout_report(
    sequences: Sequence[tuple[str, ...]],
    bigrams: Mapping[str, Counter[str]],
    protocol: str,
) -> dict[str, Any]:
    """Evaluate the two explicitly distinct leave-one-sequence protocols."""
    file_bigrams = [Counter(zip(sequence, sequence[1:])) for sequence in sequences]
    correct = 0
    total = 0
    no_prediction = 0

    if protocol == "study":
        for sequence, file_counts in zip(sequences, file_bigrams):
            for current, following in zip(sequence, sequence[1:]):
                counts = Counter(bigrams.get(current, {}))
                removed = file_counts.get((current, following), 0)
                if removed:
                    remaining = counts.get(following, 0) - removed
                    if remaining > 0:
                        counts[following] = remaining
                    else:
                        counts.pop(following, None)
                prediction = _top_prediction(counts)
                total += 1
                if prediction is None:
                    no_prediction += 1
                elif prediction == following:
                    correct += 1
        label = "study-actual-pair"
        note = (
            "subtracts only the held-out sequence's count of the evaluated pair, "
            "matching the study's published leave-one-file-out protocol; this "
            "is not a strict file holdout"
        )
    elif protocol == "strict":
        for sequence, file_counts in zip(sequences, file_bigrams):
            by_current: dict[str, Counter[str]] = defaultdict(Counter)
            for (current, following), count in file_counts.items():
                by_current[current][following] += count
            adjusted: dict[str, Counter[str]] = {}
            for current, following_counts in by_current.items():
                counts = Counter(bigrams.get(current, {}))
                for following, count in following_counts.items():
                    remaining = counts.get(following, 0) - count
                    if remaining > 0:
                        counts[following] = remaining
                    else:
                        counts.pop(following, None)
                adjusted[current] = counts
            for current, following in zip(sequence, sequence[1:]):
                prediction = _top_prediction(adjusted[current])
                total += 1
                if prediction is None:
                    no_prediction += 1
                elif prediction == following:
                    correct += 1
        label = "strict-file"
        note = "removes every transition of the held-out sequence from the counts"
    else:
        raise MoveCorpusError(f"unknown holdout protocol {protocol!r}")

    accuracy = Fraction(correct, total) if total else None
    return {
        "protocol": label,
        "correct": correct,
        "total": total,
        "accuracy": _fraction_text(accuracy) if accuracy is not None else None,
        "percent": _percent_text(accuracy) if accuracy is not None else None,
        "no_prediction": no_prediction,
        "note": note,
    }


def load_corpus(path: str | Path) -> dict[str, Any]:
    """Load a JSON move corpus; syntax and shape errors are explicit."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise MoveCorpusError(f"cannot read move corpus {path}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MoveCorpusError(f"move corpus is not valid JSON: {exc}") from exc
    if not isinstance(data, Mapping):
        raise MoveCorpusError("move corpus must be a JSON object")
    return dict(data)


def analyze(
    corpus: Mapping[str, Any], holdout: str | None = None
) -> dict[str, Any]:
    """Return the exact bigram and displacement audit for one corpus."""
    if not isinstance(corpus, Mapping):
        raise MoveCorpusError("move corpus must be a mapping")
    if corpus.get("schema") != SCHEMA:
        raise MoveCorpusError(
            f"move corpus schema must be {SCHEMA!r}, got {corpus.get('schema')!r}"
        )
    if holdout not in (None, "study", "strict"):
        raise MoveCorpusError(
            f"holdout must be None, 'study' or 'strict', got {holdout!r}"
        )

    raw_moves = corpus.get("moves") or {}
    if not isinstance(raw_moves, Mapping):
        raise MoveCorpusError("moves must be an object keyed by move id")
    moves: dict[str, dict[str, Any]] = {}
    for raw_id, raw in raw_moves.items():
        move_id = str(raw_id)
        if not move_id:
            raise MoveCorpusError("move ids must be non-empty")
        if not isinstance(raw, Mapping):
            raise MoveCorpusError(f"move {move_id!r} must be an object")
        vector = raw.get("vector")
        if vector is not None:
            if (
                not isinstance(vector, list)
                or not vector
                or not all(
                    isinstance(value, int) and not isinstance(value, bool)
                    for value in vector
                )
            ):
                raise MoveCorpusError(
                    f"move {move_id!r} vector must be a non-empty list of integers"
                )
            vector = tuple(vector)
        try:
            weight = Fraction(raw.get("weight", "1"))
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise MoveCorpusError(
                f"move {move_id!r} weight must be an exact rational"
            ) from exc
        if weight <= 0:
            raise MoveCorpusError(f"move {move_id!r} weight must be positive")
        moves[move_id] = {"vector": vector, "weight": weight}

    raw_sequences = corpus.get("sequences")
    if not isinstance(raw_sequences, list) or not raw_sequences:
        raise MoveCorpusError("sequences must be a non-empty list")
    sequences: list[tuple[str, ...]] = []
    for index, raw_sequence in enumerate(raw_sequences):
        if not isinstance(raw_sequence, list) or not raw_sequence:
            raise MoveCorpusError(f"sequence {index} must be a non-empty list")
        sequence: list[str] = []
        for item in raw_sequence:
            if not isinstance(item, str) or not item:
                raise MoveCorpusError(
                    f"sequence {index} contains a non-string move id"
                )
            if raw_moves and item not in moves:
                raise MoveCorpusError(
                    f"sequence {index} references undeclared move {item!r}"
                )
            if item not in moves:
                moves[item] = {"vector": None, "weight": Fraction(1)}
            sequence.append(item)
        sequences.append(tuple(sequence))

    used_moves = {move for sequence in sequences for move in sequence}
    dimensions = {
        len(moves[move]["vector"])
        for move in used_moves
        if moves[move]["vector"] is not None
    }
    if len(dimensions) > 1:
        raise MoveCorpusError("all move vectors must have the same dimension")
    dimension = next(iter(dimensions), None)

    bigrams: dict[str, Counter[str]] = defaultdict(Counter)
    transition_count = 0
    for sequence in sequences:
        for current, following in zip(sequence, sequence[1:]):
            bigrams[current][following] += 1
            transition_count += 1

    holdout_report = (
        _holdout_report(sequences, bigrams, holdout) if holdout else None
    )

    rows = []
    correct_total = 0
    tied_predictions = 0
    for current in sorted(bigrams):
        counts = bigrams[current]
        top_count = max(counts.values())
        candidates = sorted(
            move for move, count in counts.items() if count == top_count
        )
        prediction = candidates[0]
        if len(candidates) > 1:
            tied_predictions += 1
        correct = counts[prediction]
        total = sum(counts.values())
        correct_total += correct
        rows.append(
            {
                "current": current,
                "prediction": prediction,
                "total": total,
                "correct": correct,
                "accuracy": _fraction_text(Fraction(correct, total)),
                "top_count": top_count,
                "ties": candidates,
                "next_counts": [
                    {"move": move, "count": count}
                    for move, count in sorted(counts.items())
                ],
            }
        )

    gaps: list[str] = []
    top1_accuracy: Fraction | None = None
    top1_percent: str | None = None
    if transition_count:
        top1_accuracy = Fraction(correct_total, transition_count)
        top1_percent = _percent_text(top1_accuracy)
    else:
        gaps.append(
            "no adjacent transitions in the supplied sequences; top-1 is undefined"
        )

    return_stats = None
    all_vectors = bool(used_moves) and all(
        moves[move]["vector"] is not None for move in used_moves
    )
    if all_vectors and dimension is not None:
        displacements = []
        move_squared_norms = 0
        move_occurrences = 0
        for index, sequence in enumerate(sequences):
            net = [0] * dimension
            for move in sequence:
                vector = moves[move]["vector"]
                move_squared_norms += sum(value * value for value in vector)
                move_occurrences += 1
                for axis, value in enumerate(vector):
                    net[axis] += value
            squared_norm = sum(value * value for value in net)
            displacements.append(
                {
                    "index": index,
                    "moves": len(sequence),
                    "net": net,
                    "squared_norm": squared_norm,
                }
            )
        net_squared_norms = [item["squared_norm"] for item in displacements]
        return_stats = {
            "dimension": dimension,
            "median_net_squared_norm": _fraction_text(_median(net_squared_norms)),
            "mean_net_squared_norm": _fraction_text(
                Fraction(sum(net_squared_norms), len(net_squared_norms))
            ),
            "mean_move_squared_norm": _fraction_text(
                Fraction(move_squared_norms, move_occurrences)
            ),
            "sequences": displacements,
        }
    else:
        gaps.append(
            "return statistics unavailable: every used move needs an integer vector"
        )

    status = "ok" if transition_count and return_stats is not None else "partial"
    if not transition_count:
        status = "gap"

    evaluation = (
        "in-sample top-1 over every adjacent transition in the supplied "
        "sequences; deterministic lexical tie-break; no held-out split"
    )
    if holdout == "study":
        evaluation += (
            "; holdout=study-actual-pair (not a strict file holdout)"
        )
    elif holdout == "strict":
        evaluation += "; holdout=strict-file"

    return {
        "schema": REPORT_SCHEMA,
        "status": status,
        "evaluation": evaluation,
        "provenance": str(corpus.get("provenance", "")),
        "counts": {
            "sequences": len(sequences),
            "move_occurrences": sum(len(sequence) for sequence in sequences),
            "transitions": transition_count,
            "declared_moves": len(moves),
            "used_moves": len(used_moves),
            "vector_dimension": dimension,
        },
        "top1": {
            "correct": correct_total,
            "total": transition_count,
            "accuracy": (
                _fraction_text(top1_accuracy) if top1_accuracy is not None else None
            ),
            "percent": top1_percent,
            "tied_current_states": tied_predictions,
            "rows": rows,
        },
        "return_stats": return_stats,
        "holdout": holdout_report,
        "gaps": gaps,
        "claim": (
            "declared-corpus audit only; it is not a Leech heat kernel, a "
            "Griess algebra, a Lean type checker or a codebook optimizer"
        ),
    }


def render_text(report: Mapping[str, Any]) -> str:
    counts = report.get("counts") or {}
    top1 = report.get("top1") or {}
    lines = [
        "MOVE CORPUS AUDIT",
        "=" * 72,
        f"schema: {report.get('schema')}",
        f"status: {report.get('status')}",
        (
            f"sequences: {counts.get('sequences')}  "
            f"moves: {counts.get('move_occurrences')}  "
            f"transitions: {counts.get('transitions')}  "
            f"unique moves: {counts.get('used_moves')}"
        ),
        f"evaluation: {report.get('evaluation')}",
        (
            "top-1: {}/{} = {} ({})".format(
                top1.get("correct"),
                top1.get("total"),
                top1.get("accuracy"),
                top1.get("percent"),
            )
            if top1.get("accuracy") is not None
            else "top-1: undefined"
        ),
        f"tied current states: {top1.get('tied_current_states', 0)}",
    ]
    stats = report.get("return_stats")
    if stats:
        lines.extend(
            [
                (
                    "net squared displacement: median={} mean={}".format(
                        stats["median_net_squared_norm"],
                        stats["mean_net_squared_norm"],
                    )
                ),
                f"mean move squared norm: {stats['mean_move_squared_norm']}",
                f"vector dimension: {stats['dimension']}",
            ]
        )
    else:
        lines.append("net displacement: unavailable")
    holdout = report.get("holdout")
    if holdout:
        lines.append(
            "holdout ({}): {}/{} = {} ({})".format(
                holdout["protocol"],
                holdout["correct"],
                holdout["total"],
                holdout["accuracy"],
                holdout["percent"],
            )
        )
        lines.append(f"holdout no prediction: {holdout['no_prediction']}")
        lines.append(f"holdout note: {holdout['note']}")
    for gap in report.get("gaps") or []:
        lines.append(f"gap: {gap}")
    if report.get("provenance"):
        lines.append(f"provenance: {report['provenance']}")
    return "\n".join(lines)


__all__ = [
    "MoveCorpusError",
    "REPORT_SCHEMA",
    "SCHEMA",
    "analyze",
    "load_corpus",
    "render_text",
]
