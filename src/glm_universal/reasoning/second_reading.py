"""``glm_universal.reasoning.second_reading`` -- a second reading before answering.

The question
------------
:mod:`glm_universal.reasoning.operation_escalation` measures seven operations
under one refusal contract -- *answer only when the rung's cell is non-empty
and every carrier in it carries the same label* -- and reports one failure:
the program-text operation answers 13 of 576 queries **wrongly** rather than
refusing.  Its label, the file a declaration is written in, is not a property
of the 24 structural coordinates, so a cell can be unanimous and unanimously
wrong, and unanimity across the rungs of one reading cannot catch it.

This module asks what ``studies/SECOND_READING_STUDY.md`` pre-registers:
**does requiring a second, independent reading to agree before answering
remove the wrong answers, and what does it cost in refusals?**

What is declared
----------------
The study fixes all of it before the measurement is taken; this module
implements exactly that and nothing else.

*The primary reading* is frozen -- the escalated norm-ladder reading of
:mod:`operation_escalation`, re-derived here rather than re-tuned.

*Two second readings*, both taken at a different layer from the ladder's
quantisation and neither using the label:

``code``
    The carrier set fixes, per coordinate, the exact **lower median** over the
    carriers.  A vector becomes a 24-bit word by setting bit *j* when its
    *j*-th coordinate exceeds the *j*-th median.  The word is decoded by
    complete Golay syndrome decoding, which returns a codeword only when one
    is forced; the reading refuses when the decoding is ambiguous, and
    otherwise answers the unanimous label of the carriers decoding to the same
    codeword.
``margin``
    The exact ``l1`` distance to every carrier.  With ``d1`` the smallest, the
    answer set is every carrier at distance ``<= 2*d1``, and the reading
    answers when their labels are unanimous.

*Two guards*, both proved in ``RequestProject/GLM/SecondReading.lean``:

``strict``
    Answer the primary's answer only when the second reading answers and
    agrees.
``veto``
    Answer the primary's answer unless the second reading contradicts it.

and both readings together, so six guarded configurations.

*Two controls.*  **Matched refusal** gives up exactly as many primary answers
as the guard does, choosing them by a digest of the query rather than by a
reading, which prices a guard against refusing at random.  **Reshuffled
labels** keeps the second reading's index and permutes its labels by a
declared seeded permutation, so it answers as often and its agreements are
accidents.

*Four marks*, declared in the study: ``M1`` the program operation's wrong
count falls to 0; ``M2`` its correct count stays at or above 252; ``M3`` the
guard removes strictly more wrong answers than matched refusal does for the
same number of answers given up; ``M4`` no other operation loses more than
half its correct answers and none gains a wrong one.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout, the same deterministic
perturbations as every other escalation measurement here, and no random
source: the reshuffle is a declared permutation driven by a digest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import (Callable, Dict, Hashable, List, Optional, Sequence, Tuple)

from .. import integrity
from . import ladder_escalation as LE
from . import operation_escalation as OE

__all__ = [
    "READINGS", "GUARDS", "MARKS", "MARGIN_FACTOR",
    "medians", "binary_word", "code_reading_index", "read_code",
    "read_margin", "strict_guard", "veto_guard",
    "run_operation_guards", "guard_report", "marks_report",
    "measure", "write_measurements", "measurements", "module_digest",
    "state", "current", "DATA_PATH",
]

DIM = 24

#: The margin of the metric reading: the answer set is every carrier within
#: this multiple of the nearest distance.
MARGIN_FACTOR: int = 2

#: The declared second readings.
READINGS: Tuple[str, ...] = ("code", "margin", "both")

#: The declared guard strengths.
GUARDS: Tuple[str, ...] = ("strict", "veto")

#: The declared marks, quoted by the report rather than restated in it.
MARKS: Dict[str, str] = {
    "M1": ("safety: on the program-text operation the guarded reading answers "
           "nothing wrongly"),
    "M2": ("cost: on the program-text operation the guarded reading keeps at "
           "least 252 correct answers, half of the 503 the unguarded "
           "escalation gets"),
    "M3": ("better than refusing more: the guard removes strictly more wrong "
           "answers than the matched-refusal control removes for the same "
           "number of answers given up"),
    "M4": ("no damage elsewhere: on each other operation the guard introduces "
           "no wrong answer and loses at most half the correct answers"),
}

#: The mark thresholds, as the study states them.
M2_FLOOR: int = 252
M4_SHARE: Fraction = Fraction(1, 2)


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE TWO SECOND READINGS
# ═════════════════════════════════════════════════════════════════════════

Carriers = Sequence[Tuple[str, Hashable, Tuple[Fraction, ...]]]


def medians(entries: Carriers) -> Tuple[Fraction, ...]:
    """The exact lower median of every coordinate over the carriers."""
    size = len(entries)
    out: List[Fraction] = []
    for j in range(DIM):
        column = sorted(carrier[j] for _, _, carrier in entries)
        out.append(column[(size - 1) // 2])
    return tuple(out)


def binary_word(vector: Sequence[Fraction],
                thresholds: Sequence[Fraction]) -> int:
    """The 24-bit word: bit ``j`` is set when coordinate ``j`` exceeds its median."""
    word = 0
    for j in range(DIM):
        if vector[j] > thresholds[j]:
            word |= 1 << j
    return word


def _unanimous(labels: Sequence[Hashable]) -> Optional[Hashable]:
    distinct = set(labels)
    return next(iter(distinct)) if len(distinct) == 1 else None


def code_reading_index(entries: Carriers, thresholds: Sequence[Fraction]
                       ) -> Dict[int, Tuple[Hashable, ...]]:
    """``forced codeword -> the labels of the carriers that decode to it``."""
    from ..substrate import golay_decode as GD
    table: Dict[int, List[Hashable]] = {}
    for _, label, carrier in entries:
        codeword, _status = GD.decode_or_detect(binary_word(carrier, thresholds))
        if codeword is None:                    # ambiguous: the carrier is not read
            continue
        table.setdefault(codeword, []).append(label)
    return {word: tuple(labels) for word, labels in table.items()}


def read_code(query: Sequence[Fraction], thresholds: Sequence[Fraction],
              index: Dict[int, Tuple[Hashable, ...]]) -> Optional[Hashable]:
    """The code-layer reading of one query, or ``None`` for a refusal."""
    from ..substrate import golay_decode as GD
    codeword, _status = GD.decode_or_detect(binary_word(query, thresholds))
    if codeword is None:
        return None
    return _unanimous(index.get(codeword, ()))


def read_margin(query: Sequence[Fraction], entries: Carriers,
                labels: Optional[Sequence[Hashable]] = None
                ) -> Optional[Hashable]:
    """The metric reading of one query, or ``None`` for a refusal.

    ``labels`` overrides the carriers' own labels, which is how the reshuffled
    control is measured without touching the geometry.
    """
    distances = [sum(abs(query[j] - carrier[j]) for j in range(DIM))
                 for _, _, carrier in entries]
    nearest = min(distances)
    bound = MARGIN_FACTOR * nearest
    if labels is None:
        near = [entry[1] for entry, distance in zip(entries, distances)
                if distance <= bound]
    else:
        near = [labels[i] for i, distance in enumerate(distances)
                if distance <= bound]
    return _unanimous(near)


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE TWO GUARDS
# ═════════════════════════════════════════════════════════════════════════

def strict_guard(primary: Optional[Hashable],
                 second: Optional[Hashable]) -> Optional[Hashable]:
    """Answer only when both readings answer and they agree."""
    if primary is None or second is None:
        return None
    return primary if primary == second else None


def veto_guard(primary: Optional[Hashable],
               second: Optional[Hashable]) -> Optional[Hashable]:
    """Answer unless the second reading contradicts the primary."""
    if primary is None:
        return None
    if second is not None and second != primary:
        return None
    return primary


def _apply(guard: str, primary: Optional[Hashable],
           seconds: Sequence[Optional[Hashable]]) -> Optional[Hashable]:
    if guard == "strict":
        answer = primary
        for second in seconds:
            answer = strict_guard(answer, second)
        return answer
    answer = primary
    for second in seconds:
        answer = veto_guard(answer, second)
    return answer


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE RUN
# ═════════════════════════════════════════════════════════════════════════

def _verdict(answer: Optional[Hashable], truth: Hashable) -> str:
    if answer is None:
        return "refused"
    return "correct" if answer == truth else "wrong"


def _score(rows: Sequence[str]) -> Dict[str, int]:
    return {
        "queries": len(rows),
        "correct": sum(1 for row in rows if row == "correct"),
        "wrong": sum(1 for row in rows if row == "wrong"),
        "refused": sum(1 for row in rows if row == "refused"),
    }


def _reshuffled_labels(entries: Carriers) -> Tuple[Hashable, ...]:
    """A declared seeded permutation of the carriers' labels.

    The permutation is a Fisher-Yates shuffle whose swaps are read off a
    digest of the carrier names, so it is deterministic and carries no random
    source: the *index* is untouched and only the labels move.
    """
    labels = [label for _, label, _ in entries]
    material = ";".join(name for name, _, _ in entries).encode("utf-8")
    stream = integrity.sha256_bytes(material)
    while len(stream) < 4 * len(labels):
        stream = stream + integrity.sha256_bytes(stream)
    for i in range(len(labels) - 1, 0, -1):
        draw = int.from_bytes(stream[4 * i:4 * i + 4], "big")
        j = draw % (i + 1)
        labels[i], labels[j] = labels[j], labels[i]
    return tuple(labels)


def _matched_refusal(primary: Sequence[Optional[Hashable]],
                     truths: Sequence[Hashable],
                     queries: Sequence[Sequence[Fraction]],
                     given_up: int) -> Dict[str, int]:
    """Control A: give up the same number of answers, chosen by a digest.

    The answers are ranked by a digest of the exact query, and the first
    ``given_up`` of the ones the primary answered are refused.  So the control
    refuses exactly as often as the guard and differs from it in one thing:
    which queries it refuses.
    """
    answered = [i for i, answer in enumerate(primary) if answer is not None]
    ranked = sorted(answered, key=lambda i: integrity.sha256_hex(
        ";".join(f"{value.numerator}/{value.denominator}"
                 for value in queries[i]).encode("utf-8")))
    dropped = set(ranked[:max(0, given_up)])
    rows = [_verdict(None if i in dropped else answer, truth)
            for i, (answer, truth) in enumerate(zip(primary, truths))]
    return _score(rows)


@dataclass(frozen=True)
class _Readings:
    primary: Tuple[Optional[Hashable], ...]
    code: Tuple[Optional[Hashable], ...]
    margin: Tuple[Optional[Hashable], ...]
    code_control: Tuple[Optional[Hashable], ...]
    margin_control: Tuple[Optional[Hashable], ...]
    truths: Tuple[Hashable, ...]
    queries: Tuple[Tuple[Fraction, ...], ...]


def _readings(operation: OE.Operation,
              rungs: Sequence[str] = OE.LADDER) -> _Readings:
    """Every reading of every query, taken once and scored many ways."""
    entries = operation.carriers()
    ladder = tuple(rungs)
    indices = {rung: OE._label_index(rung, entries) for rung in ladder}
    thresholds = medians(entries)
    code_index = code_reading_index(entries, thresholds)
    shuffled = _reshuffled_labels(entries)
    control_entries = tuple((name, shuffled[i], carrier)
                            for i, (name, _, carrier) in enumerate(entries))
    control_index = code_reading_index(control_entries, thresholds)

    primary: List[Optional[Hashable]] = []
    code: List[Optional[Hashable]] = []
    margin: List[Optional[Hashable]] = []
    code_control: List[Optional[Hashable]] = []
    margin_control: List[Optional[Hashable]] = []
    truths: List[Hashable] = []
    queries: List[Tuple[Fraction, ...]] = []
    for _, query, truth in OE.operation_queries(operation):
        answered: Optional[Hashable] = None
        for rung in ladder:
            point = LE.quantise(query, rung).point
            answer = _unanimous(indices[rung].get(point, ()))
            if answer is not None:
                answered = answer
                break
        primary.append(answered)
        code.append(read_code(query, thresholds, code_index))
        margin.append(read_margin(query, entries))
        code_control.append(read_code(query, thresholds, control_index))
        margin_control.append(read_margin(query, entries, shuffled))
        truths.append(truth)
        queries.append(tuple(query))
    return _Readings(tuple(primary), tuple(code), tuple(margin),
                     tuple(code_control), tuple(margin_control),
                     tuple(truths), tuple(queries))


def run_operation_guards(operation: OE.Operation,
                         rungs: Sequence[str] = OE.LADDER) -> Dict[str, object]:
    """One operation: the readings, the six guarded configurations, the controls."""
    read = _readings(operation, rungs)
    truths = read.truths

    def score_of(answers: Sequence[Optional[Hashable]]) -> Dict[str, int]:
        return _score([_verdict(answer, truth)
                       for answer, truth in zip(answers, truths)])

    bare = score_of(read.primary)
    readings = {
        "primary": bare,
        "code": score_of(read.code),
        "margin": score_of(read.margin),
        "code_reshuffled": score_of(read.code_control),
        "margin_reshuffled": score_of(read.margin_control),
    }

    seconds = {
        "code": (read.code,),
        "margin": (read.margin,),
        "both": (read.code, read.margin),
    }
    controls = {
        "code": (read.code_control,),
        "margin": (read.margin_control,),
        "both": (read.code_control, read.margin_control),
    }

    configurations: Dict[str, Dict[str, object]] = {}
    for reading in READINGS:
        for guard in GUARDS:
            answers = [_apply(guard, primary,
                              [column[i] for column in seconds[reading]])
                       for i, primary in enumerate(read.primary)]
            score = score_of(answers)
            given_up = bare["correct"] + bare["wrong"] - (score["correct"]
                                                          + score["wrong"])
            matched = _matched_refusal(read.primary, truths, read.queries,
                                       given_up)
            shuffled_answers = [
                _apply(guard, primary,
                       [column[i] for column in controls[reading]])
                for i, primary in enumerate(read.primary)]
            configurations[f"{guard}+{reading}"] = {
                "guard": guard,
                "reading": reading,
                "score": score,
                "answers_given_up": given_up,
                "wrongs_removed": bare["wrong"] - score["wrong"],
                "control_matched_refusal": matched,
                "control_matched_wrongs_removed": (bare["wrong"]
                                                   - matched["wrong"]),
                "control_reshuffled": score_of(shuffled_answers),
            }
    return {
        "operation": operation.key,
        "title": operation.title,
        "queries": len(truths),
        "readings": readings,
        "configurations": configurations,
    }


def guard_report(rungs: Sequence[str] = OE.LADDER) -> Dict[str, object]:
    """Every operation, every declared configuration, every control."""
    rows = [run_operation_guards(operation, rungs)
            for operation in OE.OPERATIONS]
    return {
        "ladder": tuple(rungs),
        "readings": READINGS,
        "guards": GUARDS,
        "margin_factor": MARGIN_FACTOR,
        "operations": tuple(rows),
        "marks": dict(MARKS),
        "limits": (
            "The samples and the four perturbations are those of "
            "operation_escalation, and the figures inherit its limits. The "
            "margin reading computes an exact distance to every carrier, so "
            "it is a second reading and not a second index."),
    }


def marks_report(report: Dict[str, object]) -> Dict[str, object]:
    """The four declared marks, applied to every configuration."""
    rows = {row["operation"]: row                       # type: ignore[index]
            for row in report["operations"]}            # type: ignore[union-attr]
    program = rows["program"]
    verdicts: Dict[str, Dict[str, object]] = {}
    for key, configuration in program["configurations"].items():  # type: ignore[index]
        score = configuration["score"]
        m1 = score["wrong"] == 0
        m2 = score["correct"] >= M2_FLOOR
        m3 = (configuration["wrongs_removed"]
              > configuration["control_matched_wrongs_removed"])
        damage: List[str] = []
        for name, row in rows.items():
            if name == "program":
                continue
            other = row["configurations"][key]           # type: ignore[index]
            bare = row["readings"]["primary"]            # type: ignore[index]
            if other["score"]["wrong"] > bare["wrong"]:
                damage.append(f"{name}: a wrong answer appears")
            elif (Fraction(other["score"]["correct"])
                  < M4_SHARE * Fraction(bare["correct"])):
                damage.append(f"{name}: {bare['correct']} -> "
                              f"{other['score']['correct']} correct")
        m4 = not damage
        verdicts[key] = {
            "M1": m1, "M2": m2, "M3": m3, "M4": m4,
            "damage": tuple(damage),
            "adopted": bool(m1 and m2 and m3 and m4),
            "program": score,
            "wrongs_removed": configuration["wrongs_removed"],
            "matched_control_wrongs_removed":
                configuration["control_matched_wrongs_removed"],
            "answers_given_up": configuration["answers_given_up"],
        }
    adopted = [key for key, row in verdicts.items() if row["adopted"]]
    cheapest = min(adopted,
                   key=lambda key: (verdicts[key]["answers_given_up"], key)) \
        if adopted else None
    return {
        "marks": dict(MARKS),
        "floor_M2": M2_FLOOR,
        "share_M4": f"{M4_SHARE.numerator}/{M4_SHARE.denominator}",
        "verdicts": verdicts,
        "adopted": tuple(sorted(adopted)),
        "shipped": cheapest,
        "verdict": ("no declared configuration meets all four marks"
                    if not adopted else
                    f"{len(adopted)} of {len(verdicts)} configurations are "
                    f"adopted; the cheapest by answers given up is "
                    f"{cheapest}"),
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "second_reading.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/second_reading.py",
    "reasoning/operation_escalation.py",
    "reasoning/norm_escalation.py",
    "reasoning/ladder_escalation.py",
    "substrate/golay_decode.py",
    "substrate/norm_family.py",
    "substrate/construction_ladder.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The whole round, recomputed."""
    report = guard_report()
    payload = dict(report)
    payload["marks_report"] = marks_report(report)
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")
