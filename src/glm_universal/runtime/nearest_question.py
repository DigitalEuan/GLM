"""``glm_universal.runtime.nearest_question`` -- the question at the
``nearest`` ties: a reply turn for the ranking's head (Phase 150).

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/NEAREST_QUESTION_STUDY.md
(§§0-2, 7), MASTER_PLAN.md (Phase 150), the evaluation cases
``nearest-tie-*`` in ``evaluation/cases.py``, and the Phase 146 ``locate``
question that survived in ``runtime/session.py``
(``GeometricSession._locate_question``), whose rule this one mirrors.  The
original kept this code inside ``runtime/session.py``; it lives in its own
module now because the session is held under its line limit.  The wording of
the answer's added clauses is this reconstruction's own, apart from the
phrases the evaluation cases quote.*

What it does
------------
A ``nearest`` answer on the address path (Phase 148) has a **head**: the
guarded read's certified junction when the read certifies, and the scan's
least-distance set when it refuses.  When the head has two or more carriers
it is held open as a tie over its members
(:class:`glm_universal.reasoning.timed_question.OpenTie`); the replies given
(``nearest to X given key is reply; ...``) are applied in order, and the
answer ends with the question that comes next -- the minimax question of the
declared attribute and gloss vocabulary while the tie is open, the confirming
question once one member is left.

What an answer is worth is ``GLM.NearestQuestion``:

* ``after_least`` -- every member a history of replies leaves live is at the
  least distance: a reply never moves the answer off the scan's head;
* ``resolved_is_meant`` -- if the carrier meant is in the head and the replies
  are true of it, the tie resolves to that carrier;
* ``outside_never_confirmed`` -- if the carrier meant is not in the head,
  true replies never confirm a member;
* ``head_card_le_one_iff`` -- a head of one carrier puts no question, and a
  ``given`` reply to it is refused as ``no-tie``.

The refusals are named: ``no-tie``, ``unknown-question``, ``not-an-option``,
``malformed-reply`` and ``contradicted`` (the GLM reports the contradiction
rather than choose).  Column 3 (``runtime/tct_engine.py``,
``_body_nearest_address``) re-derives the live set and the split from the
register attributes, apart from the question module; the ``asks`` claim is a
partition, its groups and their members sorted, on both sides.

Exactness
---------
Strings and integers only; the distances stay with the Phase 148 read.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .solution import SolverError, Step

__all__ = ["LEAN_FILE", "LEAN_THEOREMS", "split", "head_labels",
           "question_turn", "asks_claim"]

LEAN_FILE: str = "RequestProject/GLM/NearestQuestion.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "head_mem_least", "after_least", "resolved_least", "resolved_is_meant",
    "outside_never_confirmed", "head_card_le_one_iff")


def split(request: str) -> Tuple[str, List[Tuple[str, str]]]:
    """``"albedo moved 4 by 1/4 given word:absorbed is no"`` ->
    ``("albedo moved 4 by 1/4", [("word:absorbed", "no")])``; a malformed
    reply is refused by name."""
    from ..reasoning import timed_question as tq
    try:
        return tq.split_given(request)
    except tq.GivenError as error:
        raise SolverError(f"nearest ({error.reason}): {error}") from None


def head_labels(out: Dict[str, object], rows) -> List[str]:
    """The head of the ranking: the certified junction's members when the
    guarded read certifies, else every carrier at the least distance."""
    from ..reasoning import address_read as adr
    if out.get("certified"):
        return [adr.carrier_label(rows, i) for i in out["members"]]
    return [adr.carrier_label(rows, i) for i in out["head_tied"]]


def asks_claim(record: Dict[str, object]) -> str:
    """The ``asks`` claim of column 2: the question's key and the partition
    of the live members it makes, groups and members sorted."""
    groups = sorted(sorted(o["keeps"]) for o in record["options"]
                    if o["keeps"])
    return (str(record["key"]) + " -> "
            + " / ".join("|".join(g) for g in groups))


def question_turn(head: Sequence[str], place: str,
                  given: Sequence[Tuple[str, str]], answer: str,
                  expected: Dict[str, str], steps: List[Step]
                  ) -> Tuple[str, Optional[Dict[str, object]]]:
    """The answer with the question that comes next, and the tie payload the
    conversation reads a reply against (``None`` when the head is one
    carrier and nothing was replied)."""
    from ..reasoning import timed_question as tq
    head = list(head)
    if len(head) <= 1:
        if given:
            only = head[0] if head else "no carrier"
            raise SolverError(
                f"nearest (no-tie): the head of the ranking is the single "
                f"carrier {only}, so there is no tie for a reply to resolve "
                f"(GLM.NearestQuestion.head_card_le_one_iff)")
        return answer, None
    tie = tq.OpenTie(tuple(head), label=str,
                     title=f"the head {{{', '.join(head)}}}")
    try:
        tq.apply_given(tie, list(given))
    except tq.GivenError as error:
        raise SolverError(f"nearest ({error.reason}): {error}") from None
    replies = "; ".join(f"{s.question} {s.answer}" for s in tie.ledger)
    live = [tie.label(c) for c in tie.live]
    if tie.status == "contradicted":
        raise SolverError(
            f"nearest (contradicted): the head of the ranking is "
            f"{{{', '.join(head)}}}, and the replies given ({replies}) leave "
            f"no member: some reply is false of the carrier meant, or the "
            f"carrier meant is not in the head "
            f"(GLM.NearestQuestion.outside_never_confirmed); the GLM reports "
            f"the contradiction rather than choose")
    q = tq.pending_question(tie)
    record = None if q is None else tq.question_record(tie, q)
    if given:
        answer += (f"; the replies given ({replies}) leave {len(live)} of "
                   f"the {len(head)} carriers of the head: "
                   f"{', '.join(live)} -- a reply never moves the answer off "
                   f"the scan's head (GLM.NearestQuestion.after_least)")
        expected["live"] = "|".join(sorted(live))
    if tie.status == "resolved":
        confirmed = any(s.mode == "confirmed" for s in tie.ledger)
        answer += (f"; if the replies are true of the carrier meant, it is "
                   f"{live[0]} (GLM.NearestQuestion.resolved_is_meant)")
        if confirmed:
            answer += ", and the confirming reply agrees"
    if record is not None:
        how = ("`nearest to " + tq.join_given(
            place, list(given) + [(str(record["key"]), "<reply>")]) + "`")
        if record["kind"] == "confirm":
            answer += (f"; to confirm, the GLM asks: "
                       f"{tq.describe_question(record)} -- a carrier meant "
                       f"outside the head is never confirmed "
                       f"(GLM.NearestQuestion.outside_never_confirmed); "
                       f"reply as the next turn, or ask {how}")
        else:
            answer += (f"; to separate them, the GLM asks: "
                       f"{tq.describe_question(record)} -- reply as the "
                       f"next turn, or ask {how}")
            expected["asks"] = asks_claim(record)
    steps.append(Step(
        "the question that comes next",
        "The head of the ranking is held open as a tie over its members. "
        "The replies given are applied in order, each keeping the members "
        "that give it; every member left is still at the least distance "
        "(GLM.NearestQuestion.after_least). While more than one member is "
        "live, the answer ends with the declared question whose worst reply "
        "leaves the fewest members; with one member left it ends with the "
        "confirming question.",
        f"replies {len(given)}; live {len(live)} of {len(head)} "
        f"({', '.join(live)}); status {tie.status}; next "
        f"{'none' if record is None else record['key']}"))
    payload = {"status": tie.status, "live": tuple(live),
               "given": tuple(f"{k} is {v}" for k, v in given),
               "place": place, "question": record,
               "steps": tuple(dict(s.__dict__) for s in tie.ledger)}
    return answer, payload
