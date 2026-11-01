"""``glm_universal.wheels.integer_wheel_study`` -- the question set of
``studies/INTEGER_WHEEL_STUDY.md``.

*Created 31 October 2026 (intake of ``glm_wheels_bundle``, directive D22).*
The constants below were written before the query surface, the ports of the
two wheels or the audit existed, and before any question was put to the GLM
or to a wheel (the study's §0 and §4).  Their expected answers come from the
OEIS and the ATLAS as the reviewer knows them, not from the supplied data.

Each question is ``(qid, text, expected)``:

* a forward question's ``expected`` is a ``frozenset`` of acceptable
  identifications (OEIS ids, or a sporadic group's name);
* a reverse question's (``what is the order of ...``) is ``("order", n)``;
* a negative control's is :data:`REFUSE` (code 1 expected);
* an other question's is :data:`NOT_A_QUESTION` (code 2 expected).

*Last altered 31 October 2026 (the measurement of the study's §7 added below
the question set, after the ports, the audit and the query surface existed:
:func:`integer_wheel_report` and one function per mark).*  The constants
above that line were not changed by it.

*Last altered 31 October 2026 (repository check): the command line has since
answered sequence and sporadic-order questions from these wheels (the
``sequence`` lookup kind), so S2 -- the GLM* without *the wheels -- now runs
``src/GLM.py`` with that kind switched off in the subprocess
(:data:`WITHOUT_WHEELS`); :func:`wired_cli` puts the same 102 questions to the
command line as it stands, with the wheels.*
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple, Union

#: A negative control: the surface must answer with code 1.
REFUSE = "refuse"

#: Not a sequence or sporadic-order question: the surface must answer code 2.
NOT_A_QUESTION = "not-a-question"

Expected = Union[FrozenSet[str], Tuple[str, int], str]
Question = Tuple[str, str, Expected]


def _ids(*ids: str) -> FrozenSet[str]:
    return frozenset(ids)


# ---------------------------------------------------------------------------
# 4.1 Sequence questions (70)
# ---------------------------------------------------------------------------

SEQUENCE_QUESTIONS: Tuple[Question, ...] = (
    ("Q01", "what sequence is 1, 1, 2, 3, 5, 8", _ids("A000045")),
    ("Q02", "what sequence is 0, 1, 1, 2, 3, 5, 8, 13", _ids("A000045")),
    ("Q03", "identify the sequence 2 3 5 7 11", _ids("A000040")),
    ("Q04", "which sequence starts 1, 2, 4, 8, 16, 32", _ids("A000079")),
    ("Q05", "what sequence is 1, 1, 2, 5, 14, 42, 132", _ids("A000108")),
    ("Q06", "what sequence is 1, 1, 2, 5, 15, 52, 203", _ids("A000110")),
    ("Q07", "what sequence is 1, 1, 2, 6, 24, 120, 720", _ids("A000142")),
    ("Q08", "what sequence is 0, 1, 4, 9, 16, 25, 36", _ids("A000290")),
    ("Q09", "what sequence is 1, 8, 27, 64, 125, 216", _ids("A000578")),
    ("Q10", "what sequence is 0, 1, 3, 6, 10, 15, 21", _ids("A000217")),
    ("Q11", "what sequence is 2, 1, 3, 4, 7, 11, 18", _ids("A000032")),
    ("Q12", "what sequence is 0, 1, 2, 5, 12, 29, 70", _ids("A000129")),
    ("Q13", "what sequence is 1, 1, 2, 3, 5, 7, 11, 15, 22", _ids("A000041")),
    ("Q14", "what sequence is 0, 1, 3, 6, 2, 7, 13, 20, 12", _ids("A005132")),
    ("Q15", "what sequence is 1, 2, 2, 1, 1, 2, 1, 2, 2, 1", _ids("A000002")),
    ("Q16", "what sequence is 0, 1, 1, 0, 1, 0, 0, 1, 1, 0", _ids("A010060")),
    ("Q17", "what sequence is 3, 1, 4, 1, 5, 9, 2, 6, 5", _ids("A000796")),
    ("Q18", "what sequence is 2, 7, 1, 8, 2, 8, 1, 8, 2", _ids("A001113")),
    ("Q19", "what sequence is 1, 4, 1, 4, 2, 1, 3, 5, 6", _ids("A002193")),
    ("Q20", "what sequence is 1, 7, 3, 2, 0, 5, 0, 8, 0", _ids("A002194")),
    ("Q21", "what sequence is 0, 1, 16, 81, 256, 625", _ids("A000583")),
    ("Q22", "what sequence is 1, 1, 0, 1, 1, 1, 0, 0, 1, 1", _ids("A051023")),
    ("Q23", "what sequence is 1, 3, 13, 63, 321, 1683", _ids("A001850")),
    ("Q24", "what sequence is 1, 0, 1, 2, 9, 44, 265", _ids("A000166")),
    ("Q25", "what sequence is 1, 1, 2, 4, 9, 21, 51", _ids("A001006")),
    ("Q26", "what sequence is 1, 2, 6, 22, 90, 394", _ids("A006318")),
    ("Q27", "what sequence is 1, 1, 3, 11, 45, 197", _ids("A001003")),
    ("Q28", "what sequence is 0, 1, 1, 3, 5, 11, 21, 43", _ids("A001045")),
    ("Q29", "what sequence is 1, 1, 1, 2, 2, 3, 4, 5, 6, 8", _ids("A000009")),
    ("Q30", "what sequence is 4, 6, 8, 9, 10, 12, 14, 15", _ids("A002808")),
    ("Q31", "what sequence is 1, 2, 4, 6, 12, 24, 36, 48, 60", _ids("A002182")),
    ("Q32", "what sequence is 6, 28, 496, 8128", _ids("A000396")),
    ("Q33", "what sequence is 2, 3, 7, 43, 1807", _ids("A000058")),
    ("Q34", "what sequence is 1, 3, 7, 15, 31, 63, 127", _ids("A000225")),
    ("Q35", "what sequence is 2, 3, 5, 7, 13, 17, 19, 31", _ids("A000043")),
    ("Q36", "what sequence is 3, 7, 31, 127, 8191", _ids("A000668")),
    ("Q37", "what sequence is 1, 2, 6, 30, 210, 2310", _ids("A002110")),
    ("Q38", "what sequence is 1, 7, 10, 13, 19, 23, 28", _ids("A007770")),
    ("Q39", "what sequence is 0, 1, 1, 2, 1, 3, 2, 3, 1, 4", _ids("A002487")),
    ("Q40", "what sequence is 1, 1, 2, 4, 9, 20, 48, 115", _ids("A000081")),
    ("Q41", "what sequence is 1, 2, 3, 4, 6, 8, 11, 13, 16, 18", _ids("A002858")),
    ("Q42", "what sequence is 2, 3, 5, 11, 23, 29, 41, 53", _ids("A005384")),
    ("Q43", "what sequence is 1, 2, 3, 5, 6, 7, 10, 11, 13", _ids("A005117")),
    ("Q44", "what sequence is 1, 1, 2, 6, 12, 60, 60, 420", _ids("A003418")),
    ("Q45", "what sequence is 0, 3, 5, 6, 9, 10, 12, 15", _ids("A001969")),
    ("Q46", "what sequence is 1, 2, 4, 7, 8, 11, 13, 14", _ids("A000069")),
    ("Q47", "what sequence is 2, 1, 2, 1, 1, 4, 1, 1, 6", _ids("A003417")),
    ("Q48", "what sequence is 3, 7, 15, 1, 292, 1, 1", _ids("A001203")),
    ("Q49", "what sequence is 1, 6, 1, 8, 0, 3, 3, 9, 8, 8", _ids("A001622")),
    ("Q50", "what sequence is 6, 9, 3, 1, 4, 7, 1, 8, 0", _ids("A002162")),
    ("Q51", "what sequence is 1, 3, 4, 6, 8, 9, 11, 12", _ids("A000201")),
    ("Q52", "what sequence is 2, 5, 7, 10, 13, 15, 18, 20", _ids("A001950")),
    ("Q53", "what sequence is 1, 1, 1, 2, 1, 2, 1, 5, 2, 2", _ids("A000001")),
    ("Q54", "what sequence is 1, 1, 2, 4, 11, 34, 156", _ids("A000088")),
    ("Q55", "what sequence is 1, 1, 3, 13, 75, 541", _ids("A000670")),
    ("Q56", "what sequence is 1, 7, 23, 63, 159, 383", _ids("A003261")),
    ("Q57", "what sequence is 1, 2, 4, 5, 7, 8, 9, 11", _ids("A001951")),
    ("Q58", "what sequence is 1, 9, 35, 91, 189", _ids("A005898")),
    ("Q59", "what sequence is 1, 2, 2, 4, 6, 6, 8, 10, 14, 20", _ids("A005341")),
    ("Q60", "what sequence is 0, 1, 10, 35, 84, 165", _ids("A000447")),
    ("Q61", "what sequence is 7920, 95040, 175560, 443520, 604800",
     _ids("A001228", "CFSG-SPORADIC-ORDERS")),
    ("Q62", "what sequence is 1, 2, 2, 3, 2, 4, 2, 4, 3, 4", _ids("A000005")),
    ("Q63", "what sequence is 1, 1, 2, 2, 4, 2, 6, 4, 6, 4", _ids("A000010")),
    ("Q64", "what sequence is 1, 3, 4, 7, 6, 12, 8, 15, 13", _ids("A000203")),
    ("Q65", "what sequence is 1, 2, 5, 14, 42, 132, 429", _ids("A000108")),
    ("Q66", "what sequence is 1, 1, 3, 15, 105, 945", _ids("A001147")),
    ("Q67", "what sequence is 1, 4, 10, 20, 35, 56", _ids("A000292")),
    ("Q68", "what sequence is 1, 5, 14, 30, 55, 91", _ids("A000330")),
    ("Q69", "what sequence is 1, 1, 1, 2, 3, 4, 6, 9, 13", _ids("A000930")),
    ("Q70", "what sequence is 1, 0, 0, 1, 0, 1, 1, 1, 2, 2, 3", _ids("A000931")),
)

#: The eight sequence questions whose entry the audit was expected, from the
#: listing read before this file was written, to refuse or that the item
#: does not hold under its identifier (study §4.1).
EXPECTED_REFUSALS: Tuple[str, ...] = (
    "Q19", "Q20", "Q22", "Q29", "Q57", "Q58", "Q59", "Q60",
)


# ---------------------------------------------------------------------------
# 4.2 Sporadic-order questions (32)
# ---------------------------------------------------------------------------

ORDER_QUESTIONS: Tuple[Question, ...] = (
    ("G01", "which sporadic group has order 7920", _ids("M11")),
    ("G02", "which sporadic group has order 95040", _ids("M12")),
    ("G03", "what sporadic simple group has order 443520?", _ids("M22")),
    ("G04", "name the sporadic group of order 10200960", _ids("M23")),
    ("G05", "which sporadic group has order 244823040", _ids("M24")),
    ("G06", "which sporadic group has order 175560", _ids("J1")),
    ("G07", "what sporadic simple group has order 604800?", _ids("J2")),
    ("G08", "name the sporadic group of order 50232960", _ids("J3")),
    ("G09", "which sporadic group has order 86775571046077562880", _ids("J4")),
    ("G10", "which sporadic group has order 4157776806543360000", _ids("Co1")),
    ("G11", "what sporadic simple group has order 42305421312000?", _ids("Co2")),
    ("G12", "name the sporadic group of order 495766656000", _ids("Co3")),
    ("G13", "which sporadic group has order 44352000", _ids("HS")),
    ("G14", "which sporadic group has order 898128000", _ids("McL")),
    ("G15", "what sporadic simple group has order 4030387200?", _ids("He")),
    ("G16", "name the sporadic group of order 145926144000", _ids("Ru")),
    ("G17", "which sporadic group has order 448345497600", _ids("Suz")),
    ("G18", "which sporadic group has order 460815505920", _ids("ON")),
    ("G19", "what sporadic simple group has order 64561751654400?", _ids("Fi22")),
    ("G20", "name the sporadic group of order 4089470473293004800", _ids("Fi23")),
    ("G21", "which sporadic group has order 1255205709190661721292800", _ids("Fi24'")),
    ("G22", "which sporadic group has order 273030912000000", _ids("HN")),
    ("G23", "what sporadic simple group has order 90745943887872000?", _ids("Th")),
    ("G24", "name the sporadic group of order 51765179004000000", _ids("Ly")),
    ("G25", "which sporadic group has order 4154781481226426191177580544000000",
     _ids("B")),
    ("G26", "which sporadic group has order "
            "808017424794512875886459904961710757005754368000000000", _ids("M")),
    ("G27", "which sporadic group has order 2^4 * 3^2 * 5 * 11", _ids("M11")),
    ("G28", "which sporadic group has order 2^3 * 3 * 5 * 7 * 11 * 19", _ids("J1")),
    ("G29", "what is the order of the Monster group",
     ("order", 808017424794512875886459904961710757005754368000000000)),
    ("G30", "what is the order of the sporadic group M24", ("order", 244823040)),
    ("G31", "what is the order of the Baby Monster",
     ("order", 4154781481226426191177580544000000)),
    ("G32", "what is the order of the Janko group J1", ("order", 175560)),
)


# ---------------------------------------------------------------------------
# 4.3 Negative controls (28)
# ---------------------------------------------------------------------------

PERTURBED_QUESTIONS: Tuple[Question, ...] = (
    ("P01", "what sequence is 0, 1, 1, 2, 3, 5, 9, 13", REFUSE),
    ("P02", "identify the sequence 2 3 5 7 12", REFUSE),
    ("P03", "what sequence is 1, 2, 4, 8, 16, 33", REFUSE),
    ("P04", "what sequence is 1, 1, 2, 5, 14, 43, 132", REFUSE),
    ("P05", "what sequence is 4, 8, 15, 16, 23, 42", REFUSE),
    ("P06", "what sequence is 0, 3, 8, 29, 400, 87867", REFUSE),
    ("P07", "what sequence is 3, 1, 4, 1, 5, 9, 2, 7", REFUSE),
    ("P08", "what sequence is 100, 99, 99, 98, 96, 92, 84", REFUSE),
    ("P09", "what sequence is 2, 1, 3, 4, 7, 11, 19", REFUSE),
    ("P10", "what sequence is 1, 1, 2, 3, 5, 7, 11, 16", REFUSE),
    ("P11", "what sequence is 0, 1, 3, 6, 10, 15, 22", REFUSE),
    ("P12", "what sequence is 2, 3, 7, 43, 1808", REFUSE),
)

NONSPORADIC_QUESTIONS: Tuple[Question, ...] = (
    ("O01", "which sporadic group has order 60", REFUSE),
    ("O02", "which sporadic group has order 168", REFUSE),
    ("O03", "which sporadic group has order 20160", REFUSE),
    ("O04", "which sporadic group has order 7919", REFUSE),
    ("O05", "which sporadic group has order 7921", REFUSE),
    ("O06", "which sporadic group has order 95041", REFUSE),
    ("O07", "which sporadic group has order 1", REFUSE),
    ("O08", "which sporadic group has order 2^4 * 3^2 * 5 * 13", REFUSE),
    ("O09", "which sporadic group has order "
            "808017424794512875886459904961710757005754368000000001", REFUSE),
    ("O10", "what is the order of the sporadic group M13", REFUSE),
)

OTHER_QUESTIONS: Tuple[Question, ...] = (
    ("X01", "what is the capital of France", NOT_A_QUESTION),
    ("X02", "what is 2 + 3", NOT_A_QUESTION),
    ("X03", "what sequence of events led to the war", NOT_A_QUESTION),
    ("X04", "which group has the most members", NOT_A_QUESTION),
    ("X05", "identify the speaker", NOT_A_QUESTION),
    ("X06", "what is the order of operations", NOT_A_QUESTION),
)

#: The 102 questions of marks S2 and S3.
S3_QUESTIONS: Tuple[Question, ...] = SEQUENCE_QUESTIONS + ORDER_QUESTIONS

#: The 28 questions of mark S4.
S4_QUESTIONS: Tuple[Question, ...] = (PERTURBED_QUESTIONS + NONSPORADIC_QUESTIONS
                                      + OTHER_QUESTIONS)

#: The bars, fixed with the question set (study §3).
S2_BAR_MAX_RIGHT = 10
S3_BAR_MIN_RIGHT = 85


# ===========================================================================
# The measurement (study §7).  Everything below was written after the
# question set above and after the code it measures; nothing below changes a
# question, an expected answer or a bar.
# ===========================================================================

#: How one reply stands against one question's expectation (study §3).
RIGHT = "right"
WRONG = "wrong"
REFUSED = "refused"
LEFT = "left alone"
#: The command line's reply carries an answer that is not the expected
#: identification (S2 only: the baseline is not judged right or wrong on
#: wording it was never asked to use).
OTHER = "answered otherwise"
ERROR = "error"

#: The item's own Rule 30 / ARC battery, copied verbatim (the integer lists
#: only) from ``monster_wheel_rule30_arc_test.py`` of ``glm_wheels_bundle``
#: so that mark R does not import from ``source_material``.
RULE30_SEQUENCES: Tuple[Tuple[str, Tuple[int, ...]], ...] = (
    ("R30-CC-30", (1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1,
                   1, 0, 0, 1, 0, 1, 1, 1, 1, 0)),
    ("R30-CC-18", (1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1)),
    ("R30-PD-DIAG", (0, 3, 8, 29, 400, 87867)),
    ("R30-DYADIC", (1, 2, 4, 8, 16, 32)),
    ("R30-LAG-K", (100, 99, 99, 98, 96, 92, 84)),
    ("R30-DELTA-SIG", (8, 29, 30, 107)),
    ("R30-WOBBLE", (3200, 81, 441, 8)),
    ("R30-WHITE-DIAG", (2, 7, 28)),
    ("R30-UNIF-GAP", (185, 175)),
)
ARC_SEQUENCES: Tuple[Tuple[str, Tuple[int, ...]], ...] = (
    ("ARC-GRID-SIZES", (3, 5, 7, 9, 11, 13, 15, 17)),
    ("ARC-CELL-COUNTS", (1, 4, 9, 16, 25, 36, 49)),
    ("ARC-COLOR-COUNTS", (2, 3, 4, 5, 6, 7, 8, 9, 10)),
    ("ARC-OBJECT-COUNTS", (1, 2, 3, 4, 5, 6, 7, 8)),
    ("ARC-CATALAN", (1, 1, 2, 5, 14, 42, 132)),
    ("ARC-POW2", (1, 2, 4, 8, 16, 32, 64, 128)),
    ("ARC-POW3", (1, 3, 9, 27, 81, 243)),
    ("ARC-TRI", (1, 3, 6, 10, 15, 21, 28, 36)),
    ("ARC-FIB", (0, 1, 1, 2, 3, 5, 8, 13, 21)),
    ("ARC-PRIMES", (2, 3, 5, 7, 11, 13, 17, 19, 23)),
    ("ARC-MERSENNE", (0, 1, 3, 7, 15, 31, 63, 127)),
    ("ARC-HEX-IDS", (2825285897, 1714842634, 3108673890, 3593329684, 148946066,
                     2035896926, 3158565853, 2635863684, 880031113)),
)

#: The held-out battery of S1: from each reference sequence, the runs that
#: start at these positions and have these lengths, and the same runs with
#: the last term increased by one.
HELD_OUT_STARTS: Tuple[int, ...] = (1, 3, 6)
HELD_OUT_LENGTHS: Tuple[int, ...] = (4, 6)

#: The new modules of the round (mark T's exactness scan, the ledger's
#: ``absorbed_into``).
NEW_MODULES: Tuple[str, ...] = (
    "wheels/integer_wheel.py", "wheels/monster_wheel.py", "wheels/oeis_seed.py",
    "wheels/cfsg_seed.py", "wheels/factorint.py", "wheels/oeis_reference.py",
    "wheels/sequence_query.py", "wheels/lean_wheel_data.py",
    "wheels/integer_wheel_study.py",
)

#: The theorems mark L requires the two Lean files to state.
LEAN_THEOREMS: Dict[str, Tuple[str, ...]] = {
    "Wheels/IntegerWheel.lean": (
        "provision_sound", "provision_complete", "speak_sound", "speak_eq_none",
        "speak_isSome", "speak_exact", "speak_least", "merge_keeps", "mem_merge",
        "merge_self", "merge_speak_sound", "termsA000045_eq", "termsA000032_eq",
        "termsA000142_eq", "termsA000108_eq", "termsA000040_eq", "termsA000079_eq",
        "termsA000290_eq", "termsA000217_eq"),
    "Wheels/SporadicOrders.lean": (
        "sporadicOrders_length", "sporadicOrders_nodup", "sporadicNames_nodup",
        "findByOrder_sound", "findByOrder_complete"),
}


def _sequence_text(terms: Sequence[int]) -> str:
    return "what sequence is " + ", ".join(str(t) for t in terms)


def classify(expected: Expected, code: int, ids: Sequence[str],
             order: Optional[int]) -> str:
    """One reply of the query surface against one expectation (study §3): a
    code-0 reply whose first identification is not acceptable is wrong, any
    code-0 reply to a negative control is wrong, a refusal is never wrong."""
    if expected == REFUSE:
        return WRONG if code == 0 else (REFUSED if code == 1 else LEFT)
    if expected == NOT_A_QUESTION:
        return WRONG if code == 0 else (LEFT if code == 2 else REFUSED)
    if code != 0:
        return REFUSED if code == 1 else LEFT
    if isinstance(expected, tuple):
        return RIGHT if order == expected[1] else WRONG
    return RIGHT if ids and ids[0] in expected else WRONG


def surface_rows(questions: Sequence[Question], wheel=None) -> List[Dict[str, object]]:
    """Each question put to :func:`sequence_query.resolve_query` (over
    ``wheel``, default the absorbed Monster Wheel), with its outcome."""
    from .sequence_query import resolve_query
    rows: List[Dict[str, object]] = []
    for qid, text, expected in questions:
        r = resolve_query(text, wheel)
        rows.append({"qid": qid, "code": r.code, "ids": r.ids, "order": r.order,
                     "position": r.position, "reply": r.reply,
                     "outcome": classify(expected, r.code, r.ids, r.order)})
    return rows


def tally(rows: Sequence[Dict[str, object]]) -> Dict[str, int]:
    out = {RIGHT: 0, WRONG: 0, REFUSED: 0, LEFT: 0}
    for row in rows:
        key = str(row["outcome"])
        out[key] = out.get(key, 0) + 1
    return out


def _qids(rows: Sequence[Dict[str, object]], outcome: str) -> Tuple[str, ...]:
    return tuple(str(r["qid"]) for r in rows if r["outcome"] == outcome)


# ---------------------------------------------------------------------------
# Mark A -- the audit
# ---------------------------------------------------------------------------

def mark_a() -> Dict[str, object]:
    """Every supplied sequence entry has a verdict, and the absorbed wheels
    hold exactly the verified ones (plus the groups and the sorted orders)."""
    from . import oeis_reference as ref
    from .integer_wheel import default_wheel
    from .monster_wheel import default_monster_wheel, SORTED_ORDERS_ID
    from .cfsg_seed import CFSG_GROUPS
    from .oeis_seed import CURATED_OEIS
    from .cfsg_seed import GROUP_THEORY_OEIS
    audit = ref.audit_supplied()
    rows = list(audit["integer"]) + list(audit["group_theory"])     # type: ignore[arg-type]
    supplied = len(CURATED_OEIS) + len(GROUP_THEORY_OEIS)
    live_integer = tuple(audit["admitted_integer"])                 # type: ignore[arg-type]
    live_group = tuple(audit["admitted_group_theory"])              # type: ignore[arg-type]
    iw = default_wheel()
    mw = default_monster_wheel()
    group_side = set()
    for g in CFSG_GROUPS:
        group_side.update({g[0], g[0] + "-EXPVEC"})
    group_side.add(SORTED_ORDERS_ID)
    expected_mw = set(live_integer) | set(live_group) | group_side
    frozen_ok = (live_integer == ref.ADMITTED_IDS
                 and live_group == ref.ADMITTED_GROUP_THEORY_IDS)
    disagreements = tuple((str(r["id"]), str(r["reason"])) for r in rows
                          if r["verdict"] == ref.DISAGREES)
    met = (len(rows) == supplied
           and all(r["verdict"] in (ref.VERIFIED, ref.DISAGREES, ref.SHORT,
                                    ref.NOT_RECOMPUTED) for r in rows)
           and frozen_ok
           and set(iw.ids()) == set(live_integer)
           and set(mw.ids()) == expected_mw)
    return {"met": met, "supplied": supplied, "verdicts": len(rows),
            "counts": dict(audit["counts"]),                        # type: ignore[arg-type]
            "admitted_integer": len(live_integer),
            "admitted_group_theory": len(live_group),
            "integer_wheel_entries": len(iw), "monster_wheel_entries": len(mw),
            "frozen_list_matches_live_audit": frozen_ok,
            "disagreements": disagreements}


# ---------------------------------------------------------------------------
# Mark S1 -- soundness against the independent reference
# ---------------------------------------------------------------------------

def group_reference() -> Dict[str, Tuple[int, ...]]:
    """The reference terms of the group-side identifiers, from
    ``Wheels/SporadicOrders.lean``: a group's order is the product of the
    prime powers of its ``order_<name>`` theorem, its exponent vector is read
    over the primes 2 .. 71, and the sorted orders are those products sorted.
    Empty when the Lean file cannot be read."""
    from .lean_wheel_data import sporadic_factorisations
    from .monster_wheel import PRIMES_TO_73, SORTED_ORDERS_ID
    out: Dict[str, Tuple[int, ...]] = {}
    orders: List[int] = []
    for name, (_stated, factors) in sporadic_factorisations().items():
        order = 1
        for p, e in factors:
            order *= p ** e
        exps = dict(factors)
        out[name] = (order,)
        out[name + "-EXPVEC"] = tuple(exps.get(p, 0) for p in PRIMES_TO_73)
        orders.append(order)
    if orders:
        out[SORTED_ORDERS_ID] = tuple(sorted(orders))
    return out


class ReferenceJudge:
    """Judges an identification against the independent reference.

    For every OEIS id on ``wheel`` that has a reference, the audit of the
    entry *as the wheel stores it* fixes where its stored terms start in the
    reference (``start``; ``None`` when the audit does not verify the entry),
    and the reference terms are fetched once, with exactly the length the
    audit itself asked for (so nothing costly is recomputed).  The group-side
    ids are judged against :func:`group_reference`."""

    def __init__(self, wheel):
        from .oeis_reference import (MAX_SHIFT, REFERENCE, VERIFIED, audit_entry,
                                     reference_terms)
        self.groups = group_reference()
        self.refs: Dict[str, Tuple[Optional[int], Tuple[int, ...]]] = {}
        for e in wheel.entries():
            oid = e.oeis_id
            if oid in self.groups or oid not in REFERENCE:
                continue
            a = audit_entry(oid, e.terms)
            n = len(e.terms)
            if a["verdict"] == VERIFIED and a["start"] == 0:
                self.refs[oid] = (0, reference_terms(oid, n))
            else:
                longer = reference_terms(oid, n + MAX_SHIFT)
                shorter = reference_terms(oid, n)
                ref = longer if len(longer) > len(shorter) else shorter
                start = a["start"] if a["verdict"] == VERIFIED else None
                self.refs[oid] = (start, ref)   # type: ignore[assignment]

    def __call__(self, oid: str, position: int, claim: Sequence[int]) -> Optional[bool]:
        return true_identification(oid, position, claim, self)


def true_identification(oid: str, position: int, claim: Sequence[int],
                        judge: ReferenceJudge) -> Optional[bool]:
    """Whether *the claim is the run of sequence ``oid`` at stored position
    ``position``* is true of the independent reference.  A group-side id is
    judged against :func:`group_reference`.  An audited OEIS entry is judged
    at its audited start: the claim must be the reference's terms
    ``start + position ...``.  An entry the audit does not verify (the
    control's) is judged true when the claim is the reference's run at
    ``s + position`` for some shift ``s <= MAX_SHIFT`` (the latitude the
    audit gives), false when it is not and the reference reaches that far.
    ``None`` when the id has no reference or the reference is too short to
    judge."""
    from .oeis_reference import MAX_SHIFT
    claim_t = tuple(claim)
    n = len(claim_t)
    if oid in judge.groups:
        return judge.groups[oid][position:position + n] == claim_t
    if oid not in judge.refs:
        return None
    start, ref = judge.refs[oid]
    if start is not None:
        if start + position + n > len(ref):
            return None
        return ref[start + position:start + position + n] == claim_t
    if any(ref[s + position:s + position + n] == claim_t
           for s in range(0, MAX_SHIFT + 1) if s + position + n <= len(ref)):
        return True
    return False if position + n <= len(ref) else None


def _judge(result, judge: ReferenceJudge) -> Tuple[int, int, int]:
    """``(true, false, unjudged)`` over every identification a code-0 reply
    names (the spoken id and any 'also starting with' ids)."""
    t = f = u = 0
    if result.code != 0:
        return 0, 0, 0
    if result.kind == "sequence":
        for oid in result.ids:
            verdict = judge(oid, result.position or 0, result.claim)
            if verdict is None:
                u += 1
            elif verdict:
                t += 1
            else:
                f += 1
    elif result.kind in ("order", "reverse"):
        for gid in result.ids:
            want = judge.groups.get(gid)
            if want is None:
                u += 1
            elif want == (result.order,):
                t += 1
            else:
                f += 1
    return t, f, u


def held_out_battery() -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    """S1's held-out claims: for every identifier with an independent
    reference, the reference runs at :data:`HELD_OUT_STARTS` of
    :data:`HELD_OUT_LENGTHS` terms (none at the start, so ``speak`` on the
    stored terms is not what answers them), and each again with its last
    term increased by one.  The reference is asked for as many terms as the
    supplied entry stores (the audit's own request), so nothing costly is
    recomputed.  ``(label, claim)`` pairs, deduplicated."""
    from .oeis_reference import REFERENCE, reference_terms
    from .integer_wheel import supplied_entries
    from .cfsg_seed import GROUP_THEORY_OEIS
    stored = {e.oeis_id: len(e.terms) for e in supplied_entries()}
    for row in GROUP_THEORY_OEIS:
        stored.setdefault(row[0], len(row[2]))
    seen = set()
    out: List[Tuple[str, Tuple[int, ...]]] = []
    for oid in sorted(REFERENCE):
        ref = reference_terms(oid, stored.get(oid, 16))
        for start in HELD_OUT_STARTS:
            for length in HELD_OUT_LENGTHS:
                run = tuple(ref[start:start + length])
                if len(run) < length:
                    continue
                for label, claim in ((f"{oid}@{start}+{length}", run),
                                     (f"{oid}@{start}+{length}*", run[:-1] + (run[-1] + 1,))):
                    if claim in seen:
                        continue
                    seen.add(claim)
                    out.append((label, claim))
    return tuple(out)


def soundness_sweep(wheel=None) -> Dict[str, object]:
    """S1 over ``wheel`` (default the absorbed Monster Wheel): every nonempty
    prefix of every entry through ``speak`` (which must not be silent) and,
    from three terms on, through the query surface; every sporadic order
    through the surface; the held-out battery through the surface.  Every
    identification named is judged against the reference."""
    from .monster_wheel import default_monster_wheel
    from .sequence_query import resolve_query, MIN_TERMS
    w = default_monster_wheel() if wheel is None else wheel
    judge = ReferenceJudge(w)
    groups = judge.groups
    prefixes = silent = speak_false = speak_unjudged = 0
    whole_true = whole_false = whole_unjudged = whole_asked = 0
    for e in w.entries():
        for n in range(1, len(e.terms) + 1):
            claim = e.terms[:n]
            prefixes += 1
            spoken = w.speak(claim)
            if spoken is None:
                silent += 1
                continue
            v = judge(spoken, 0, claim)
            if v is None:
                speak_unjudged += 1
            elif not v:
                speak_false += 1
            if n >= MIN_TERMS:
                whole_asked += 1
                t, f, u = _judge(resolve_query(_sequence_text(claim), w), judge)
                whole_true += t
                whole_false += f
                whole_unjudged += u
    for gid, terms in sorted(groups.items()):
        if len(terms) != 1:
            continue
        whole_asked += 1
        t, f, u = _judge(resolve_query(
            f"which sporadic group has order {terms[0]}", w), judge)
        whole_true += t
        whole_false += f
        whole_unjudged += u
    battery = held_out_battery()
    held_answered = held_true = held_false = held_unjudged = 0
    for _label, claim in battery:
        r = resolve_query(_sequence_text(claim), w)
        if r.code == 0:
            held_answered += 1
        t, f, u = _judge(r, judge)
        held_true += t
        held_false += f
        held_unjudged += u
    return {"prefixes": prefixes, "speak_silent": silent, "speak_false": speak_false,
            "speak_unjudged": speak_unjudged, "surface_questions": whole_asked,
            "surface_true": whole_true, "surface_false": whole_false,
            "surface_unjudged": whole_unjudged, "held_out": len(battery),
            "held_out_answered": held_answered, "held_out_true": held_true,
            "held_out_false": held_false, "held_out_unjudged": held_unjudged,
            "groups_referenced": sum(1 for t in groups.values() if len(t) == 1)}


def mark_s1() -> Dict[str, object]:
    """S1 on the absorbed wheels: no silence on a stored prefix, and no
    identification false of (or unjudgeable against) the reference."""
    s = soundness_sweep()
    met = (s["groups_referenced"] == 26 and s["speak_silent"] == 0
           and s["speak_false"] == 0 and s["speak_unjudged"] == 0
           and s["surface_false"] == 0 and s["surface_unjudged"] == 0
           and s["held_out_false"] == 0 and s["held_out_unjudged"] == 0)
    return dict(s, met=met)


# ---------------------------------------------------------------------------
# Mark S2 -- the GLM's command line without the wheels
# ---------------------------------------------------------------------------

def cli_path():
    """``src/GLM.py``, the command line a user runs."""
    from ..constants import PACKAGE_ROOT
    return PACKAGE_ROOT.parent / "GLM.py"


#: ``src/GLM.py`` without the wheels: run in a fresh interpreter with the
#: ``sequence`` lookup kind (:func:`glm_universal.runtime.lookup_kinds.
#: reads_sequence`) switched off, so no question reaches the Integer or Monster
#: Wheel.  Nothing else changes; ``python3 -c WITHOUT_WHEELS src/GLM.py -q ...``.
WITHOUT_WHEELS = (
    "import runpy, sys\n"
    "import glm_universal.runtime.lookup_kinds as lk\n"
    "lk.reads_sequence = lambda text: False\n"
    "sys.argv = sys.argv[1:]\n"
    "runpy.run_path(sys.argv[0], run_name='__main__')\n")


def ask_cli(text: str, timeout: int = 300, with_wheels: bool = False) -> Tuple[int, str]:
    """``python3 src/GLM.py -q <text>`` from the repository root, as a user
    runs it -- without the wheels (:data:`WITHOUT_WHEELS`) unless
    ``with_wheels``: ``(exit status, standard output)``; ``(-1, "")`` on a
    timeout."""
    from ..constants import REPOSITORY_ROOT, PACKAGE_ROOT
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_ROOT.parent)
    command = ([sys.executable, str(cli_path()), "-q", text] if with_wheels else
               [sys.executable, "-c", WITHOUT_WHEELS, str(cli_path()), "-q", text])
    try:
        proc = subprocess.run(command, cwd=str(REPOSITORY_ROOT), env=env,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return -1, ""
    return proc.returncode, proc.stdout


def _acceptable_tokens(expected: Expected) -> Tuple[str, ...]:
    from .cfsg_seed import CFSG_GROUPS
    if isinstance(expected, tuple) or isinstance(expected, str):
        return ()
    names = {g[0]: g[1] for g in CFSG_GROUPS}
    out: List[str] = []
    for item in sorted(expected):
        out.append(item)
        if item in names:
            out.append(names[item])
    return tuple(out)


def classify_cli(expected: Expected, code: int, stdout: str) -> str:
    """One command-line reply: ``right`` when it exits 0 and its reply (the
    echoed query line excluded) names an acceptable identification -- the
    id or, for a group, its name, as a whole word -- or, for a reverse
    question, the expected order (with or without digit grouping); ``refused``
    on exit 1; otherwise ``answered otherwise`` or ``error``.  Deliberately
    lenient to the baseline: a word match anywhere in the reply counts."""
    if code == 1:
        return REFUSED
    if code != 0:
        return ERROR
    body = "\n".join(line for line in stdout.splitlines()
                     if not line.startswith("QUERY"))
    if isinstance(expected, tuple):
        digits = re.sub(r"(?<=\d)[,\s](?=\d{3}\b)", "", body)
        return RIGHT if re.search(rf"(?<!\d){expected[1]}(?!\d)", digits) else OTHER
    for token in _acceptable_tokens(expected):
        if re.search(rf"(?<![\w']){re.escape(token)}(?![\w'])", body):
            return RIGHT
    return OTHER


def cli_rows(questions: Sequence[Question], jobs: int = 4,
             timeout: int = 300, with_wheels: bool = False) -> List[Dict[str, object]]:
    """Each question put to the real command line (``jobs`` at a time),
    without the wheels unless ``with_wheels``."""
    def one(q: Question) -> Dict[str, object]:
        qid, text, expected = q
        code, out = ask_cli(text, timeout, with_wheels=with_wheels)
        answer = ""
        for line in out.splitlines():
            if line.startswith(("ANSWER", "UNSOLVED", "REFUSED")):
                answer = " ".join(line.split()[1:])
        return {"qid": qid, "exit": code, "answer": answer[:200],
                "outcome": classify_cli(expected, code, out)}
    if jobs <= 1:
        return [one(q) for q in questions]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(one, questions))


def wired_cli(jobs: int = 4) -> Dict[str, object]:
    """The 102 questions of S2 through the command line as it stands, *with*
    the wheels (the ``sequence`` lookup kind): not a mark -- the figure that
    shows the surface's answers reaching the command line.  Each reply is
    judged as S3 judges the surface: ``right`` when it names an expected
    identification, ``refused`` on exit 1, ``wrong`` otherwise."""
    rows = cli_rows(S3_QUESTIONS, jobs=jobs, with_wheels=True)
    counts: Dict[str, int] = {}
    for r in rows:
        outcome = {RIGHT: RIGHT, REFUSED: REFUSED}.get(str(r["outcome"]), WRONG)
        counts[outcome] = counts.get(outcome, 0) + 1
    return {"questions": len(rows), "right": counts.get(RIGHT, 0),
            "wrong": counts.get(WRONG, 0), "refused": counts.get(REFUSED, 0),
            "right_qids": _qids(rows, RIGHT)}


def mark_s2(jobs: int = 4) -> Dict[str, object]:
    """S2: the 102 questions through ``python3 src/GLM.py -q`` without the
    wheels (:data:`WITHOUT_WHEELS`); met when at most
    :data:`S2_BAR_MAX_RIGHT` receive the expected identification."""
    rows = cli_rows(S3_QUESTIONS, jobs=jobs)
    counts: Dict[str, int] = {}
    for r in rows:
        counts[str(r["outcome"])] = counts.get(str(r["outcome"]), 0) + 1
    right = counts.get(RIGHT, 0)
    exits: Dict[int, int] = {}
    for r in rows:
        exits[int(r["exit"])] = exits.get(int(r["exit"]), 0) + 1   # type: ignore[arg-type]
    return {"met": right <= S2_BAR_MAX_RIGHT and counts.get(ERROR, 0) == 0,
            "questions": len(rows), "right": right, "counts": counts,
            "exit_statuses": exits,
            "answers": tuple(sorted({str(r["answer"]) for r in rows})),
            "right_qids": _qids(rows, RIGHT), "rows": tuple(rows)}


# ---------------------------------------------------------------------------
# Marks S3, S4 and C -- the query surface with the wheels
# ---------------------------------------------------------------------------

def mark_s3(wheel=None) -> Dict[str, object]:
    """S3: at least :data:`S3_BAR_MIN_RIGHT` of the 102 right, none wrong."""
    rows = surface_rows(S3_QUESTIONS, wheel)
    c = tally(rows)
    return {"met": c[RIGHT] >= S3_BAR_MIN_RIGHT and c[WRONG] == 0,
            "questions": len(rows), "right": c[RIGHT], "wrong": c[WRONG],
            "refused": c[REFUSED], "left_alone": c[LEFT],
            "right_sequence": sum(1 for r in rows if r["outcome"] == RIGHT
                                  and str(r["qid"]).startswith("Q")),
            "right_order": sum(1 for r in rows if r["outcome"] == RIGHT
                               and str(r["qid"]).startswith("G")),
            "refused_qids": _qids(rows, REFUSED), "wrong_qids": _qids(rows, WRONG),
            "left_qids": _qids(rows, LEFT),
            "located": tuple(str(r["qid"]) for r in rows
                             if r["outcome"] == RIGHT and r["position"]),
            "rows": tuple(rows)}


def mark_s4(wheel=None) -> Dict[str, object]:
    """S4: every perturbed sequence and non-sporadic order refused (code 1),
    every other question left alone (code 2)."""
    rows = surface_rows(S4_QUESTIONS, wheel)
    c = tally(rows)
    perturbed = [r for r in rows if str(r["qid"]).startswith("P")]
    nonsporadic = [r for r in rows if str(r["qid"]).startswith("O")]
    other = [r for r in rows if str(r["qid"]).startswith("X")]
    p_ok = sum(1 for r in perturbed if r["outcome"] == REFUSED)
    o_ok = sum(1 for r in nonsporadic if r["outcome"] == REFUSED)
    x_ok = sum(1 for r in other if r["outcome"] == LEFT)
    return {"met": (p_ok == len(perturbed) and o_ok == len(nonsporadic)
                    and x_ok == len(other)),
            "questions": len(rows), "wrong": c[WRONG],
            "perturbed_refused": p_ok, "perturbed": len(perturbed),
            "nonsporadic_refused": o_ok, "nonsporadic": len(nonsporadic),
            "other_left_alone": x_ok, "other": len(other),
            "wrong_qids": _qids(rows, WRONG), "rows": tuple(rows)}


def mark_c() -> Dict[str, object]:
    """C (reported, not passed or failed): the S3 and S4 questions and the
    held-out battery over the *supplied*, unaudited wheels."""
    from .monster_wheel import supplied_monster_wheel
    w = supplied_monster_wheel()
    s3 = mark_s3(w)
    s4 = mark_s4(w)
    sweep = soundness_sweep(w)
    return {"met": True, "reported_only": True, "entries": len(w),
            "s3_right": s3["right"], "s3_wrong": s3["wrong"],
            "s3_wrong_qids": s3["wrong_qids"], "s3_refused": s3["refused"],
            "s4_wrong": s4["wrong"], "s4_wrong_qids": s4["wrong_qids"],
            "speak_false": sweep["speak_false"],
            "speak_unjudged": sweep["speak_unjudged"],
            "surface_false": sweep["surface_false"],
            "surface_unjudged": sweep["surface_unjudged"],
            "held_out_false": sweep["held_out_false"],
            "held_out_unjudged": sweep["held_out_unjudged"]}


# ---------------------------------------------------------------------------
# Mark R -- the item's own Rule 30 / ARC battery
# ---------------------------------------------------------------------------

def mark_r() -> Dict[str, object]:
    """R (reported): the item's battery re-run.  M1: the Monster Wheel's
    identifications beyond the Integer Wheel's on the 21 sequences; M2: the
    battery's integers that are sporadic orders.  Both on the absorbed wheels
    and on the supplied ones (the item's own configuration).  The query
    surface's answers on the 21 are reported too, each judged by S1's
    reference."""
    from .integer_wheel import default_wheel, supplied_wheel
    from .monster_wheel import default_monster_wheel, supplied_monster_wheel
    from .sequence_query import resolve_query
    battery = RULE30_SEQUENCES + ARC_SEQUENCES
    integers = sorted({x for _n, seq in battery for x in seq})

    def run(iw, mw) -> Dict[str, object]:
        iw_spoke = sum(1 for _n, s in battery if iw.speak(s) is not None)
        mw_spoke = sum(1 for _n, s in battery if mw.speak(s) is not None)
        additional = sum(1 for _n, s in battery
                         if mw.speak(s) is not None and mw.speak(s) != iw.speak(s))
        orders = tuple((x, mw.find_by_order(x)) for x in integers
                       if mw.find_by_order(x) is not None)
        return {"integer_wheel_spoke": iw_spoke, "monster_wheel_spoke": mw_spoke,
                "additional": additional, "sporadic_orders": orders}

    absorbed = run(default_wheel(), default_monster_wheel())
    supplied = run(supplied_wheel(), supplied_monster_wheel())
    judge = ReferenceJudge(default_monster_wheel())
    answered: List[Tuple[str, Tuple[str, ...], Optional[int]]] = []
    false = 0
    for name, seq in battery:
        r = resolve_query(_sequence_text(seq))
        if r.code == 0:
            answered.append((name, r.ids, r.position))
            false += _judge(r, judge)[1]
    return {"met": True, "reported_only": True, "sequences": len(battery),
            "integers": len(integers), "absorbed": absorbed, "supplied": supplied,
            "surface_answered": tuple(answered), "surface_false": false,
            "no_help": (absorbed["additional"] == 0
                        and not absorbed["sporadic_orders"])}


# ---------------------------------------------------------------------------
# Mark L -- the Lean half
# ---------------------------------------------------------------------------

def mark_l() -> Dict[str, object]:
    """L: both files in the build tree, imported by ``AxiomAuditAll.lean``,
    the static tree check passing, the required theorems stated, and the
    statements read back equal to the Python data."""
    from ..constants import lean_file
    from .. import lean_check
    from . import lean_wheel_data as L
    from .integer_wheel import default_wheel
    from .cfsg_seed import CFSG_GROUPS, exponent_vector
    from .monster_wheel import PRIMES_TO_73
    present = {name: lean_file(name).is_file() for name in LEAN_THEOREMS}
    audited = {name: lean_check.audited_or_held(name) for name in LEAN_THEOREMS}
    tree_ok = lean_check.check_tree().ok()
    missing: List[str] = []
    for name, theorems in LEAN_THEOREMS.items():
        text = L.lean_text(name)
        for t in theorems:
            if not re.search(rf"^theorem\s+{re.escape(t)}\b", text, re.MULTILINE):
                missing.append(f"{name}: {t}")
    iw = default_wheel()
    lists = L.integer_wheel_terms()
    lists_ok = tuple(sorted(oid for oid, terms in lists.items()
                            if iw.get(oid) is not None
                            and iw.get(oid).terms[:len(terms)] == terms))
    orders = L.sporadic_orders()
    orders_ok = orders == tuple((g[0], g[2]) for g in CFSG_GROUPS)
    facts = L.sporadic_factorisations()
    fact_ok = 0
    for gid, _name, order, *_rest in CFSG_GROUPS:
        if gid not in facts:
            continue
        stated, factors = facts[gid]
        product = 1
        for p, e in factors:
            product *= p ** e
        vector = [dict(factors).get(p, 0) for p in PRIMES_TO_73]
        if (stated == order and product == order
                and list(exponent_vector(order, max_prime=73)) == vector):
            fact_ok += 1
    met = (all(present.values()) and all(audited.values()) and tree_ok
           and not missing and len(lists) == 8 and len(lists_ok) == 8
           and len(orders) == 26 and orders_ok and fact_ok == 26)
    return {"met": met, "present": present, "audited": audited,
            "static_check_ok": tree_ok, "missing_theorems": tuple(missing),
            "terms_lists": len(lists), "terms_lists_agreeing": len(lists_ok),
            "sporadic_orders": len(orders), "orders_agree": orders_ok,
            "factorisations_agreeing": fact_ok,
            "build": "not run here: the owner's scripts/rebuild_lean.sh"}


# ---------------------------------------------------------------------------
# Mark T -- no regression
# ---------------------------------------------------------------------------

#: The test modules mark T runs (with ``python3 -m unittest``).
T_TEST_MODULES: Tuple[str, ...] = (
    "glm_universal.tests.test_integer_wheel",
    "glm_universal.tests.test_monster_wheel",
    "glm_universal.tests.test_wheels",
)


def mark_t(run_tests: bool = True, timeout: int = 1800) -> Dict[str, object]:
    """T: the W01-W15 registry unchanged and the provision family beside it,
    no float site in the new modules, and (``run_tests``) the new modules'
    tests and ``tests/test_wheels.py`` passing under ``python3 -m unittest``.
    Without ``run_tests`` the mark is reported not met: the tests were not
    run."""
    from ..constants import PACKAGE_ROOT
    from ..reasoning.exactness import module_float_sites
    from .. import wheels as W
    registry_ok = (len(W.ALL_WHEELS) == 15
                   and [w.id for w in W.ALL_WHEELS] == [f"W{i}" for i in range(1, 16)])
    provision_ok = tuple(p.id for p in W.PROVISION_WHEELS) == ("IW", "MW")
    floats = {m: module_float_sites(PACKAGE_ROOT / m) for m in NEW_MODULES}
    float_modules = tuple(m for m, sites in floats.items() if sites)
    tests: Dict[str, object] = {"run": False}
    if run_tests:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(PACKAGE_ROOT.parent)
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", *T_TEST_MODULES],
                                  cwd=str(PACKAGE_ROOT.parent), env=env,
                                  capture_output=True, text=True, timeout=timeout)
            ran = re.search(r"Ran (\d+) tests?", proc.stderr)
            tests = {"run": True, "passed": proc.returncode == 0,
                     "tests": int(ran.group(1)) if ran else 0,
                     "tail": proc.stderr.strip().splitlines()[-1:] or [""]}
        except subprocess.TimeoutExpired:
            tests = {"run": True, "passed": False, "tests": 0, "tail": ["timeout"]}
    met = (registry_ok and provision_ok and not float_modules
           and bool(tests.get("run")) and bool(tests.get("passed")))
    return {"met": met, "registry_unchanged": registry_ok,
            "provision_wheels": provision_ok, "float_modules": float_modules,
            "tests": tests}


# ---------------------------------------------------------------------------
# The deciding figure
# ---------------------------------------------------------------------------

def deciding_figure(s1: Dict[str, object], s2: Dict[str, object],
                    s3: Dict[str, object], s4: Dict[str, object]) -> str:
    """The study's deciding figure, as a sentence of integers."""
    controls = (int(s4["perturbed_refused"]) + int(s4["nonsporadic_refused"])  # type: ignore[arg-type]
                + int(s4["other_left_alone"]))                              # type: ignore[arg-type]
    checked = int(s1["prefixes"]) + int(s1["surface_questions"]) + int(s1["held_out"])  # type: ignore[arg-type]
    return (f"{s3['right']} of {s3['questions']} questions answered right and "
            f"{s3['wrong']} wrong with the wheels (bar: at least {S3_BAR_MIN_RIGHT}, "
            f"0 wrong), against {s2['right']} of {s2['questions']} through the "
            f"command line without them; {controls} of {s4['questions']} negative "
            f"controls refused or left alone; {s1['surface_false'] + s1['held_out_false'] + s1['speak_false']} "
            f"false identifications in {checked} soundness checks.")


def integer_wheel_report(cli: bool = True, run_tests: bool = True,
                         jobs: int = 4) -> Dict[str, object]:
    """Every mark of ``studies/INTEGER_WHEEL_STUDY.md``, recomputed: A, S1,
    S2 (``cli``: the real command line, some minutes), S3, S4, C, R, L and T
    (``run_tests``).  A mark that is not taken is reported not met.  The
    verdict holds when A, S1, S2, S3, S4, L and T are met (C and R are
    reported)."""
    a = mark_a()
    s1 = mark_s1()
    s2 = mark_s2(jobs=jobs) if cli else {"met": False, "questions": len(S3_QUESTIONS),
                                         "right": "not taken", "taken": False}
    s3 = mark_s3()
    s4 = mark_s4()
    c = mark_c()
    r = mark_r()
    lean = mark_l()
    t = mark_t(run_tests=run_tests)
    marks = {"A": a, "S1": s1, "S2": s2, "S3": s3, "S4": s4, "C": c, "R": r,
             "L": lean, "T": t}
    decisive = ("A", "S1", "S2", "S3", "S4", "L", "T")
    return {"study": "studies/INTEGER_WHEEL_STUDY.md",
            "marks": marks,
            "met": {k: bool(v["met"]) for k, v in marks.items()},
            "deciding_figure": deciding_figure(s1, s2, s3, s4),
            "holds": all(bool(marks[k]["met"]) for k in decisive)}


def _summary(report: Dict[str, object]) -> str:
    lines = [str(report["deciding_figure"]), ""]
    for key, mark in report["marks"].items():                      # type: ignore[union-attr]
        shown = {k: v for k, v in mark.items() if k != "rows"}
        lines.append(f"{key}: {shown}")
    lines.append(f"holds: {report['holds']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_summary(integer_wheel_report(cli="--no-cli" not in sys.argv,
                                        run_tests="--no-tests" not in sys.argv)))
