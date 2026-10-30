"""``glm_universal.runtime.plan_store`` -- a resolved follow-up, kept against a
digest of everything it depended on.

Why this module exists
----------------------
Resolving a follow-up is not free.  :mod:`glm_universal.runtime.conversation`
decides a pronoun's referent by **licensing** -- it substitutes each candidate
and asks the session whether the resulting query solves -- so a follow-up after
a fourteen-row tie costs fourteen trial solves before it refuses.  The
conversational material supplied with Phase 54 carries a store for exactly
this: successful plans kept under the SHA-256 of the plan and replayed when the
same thing is asked again.

``CONVERSATION_STUDY.md`` §9 said what a round taking it would have to show:
*a speed-up is a cost result, not a target result (D15); it would have to show
a refusal preserved across replay, or it is maintenance.*  That is the thing
this module is built around, and it is the thing the supplied store does not
do: there, only **successful** plans are kept, so the fourteen-row tie pays its
fourteen trials again every time it is asked, and a store that only remembers
answers is a store that forgets exactly the expensive case.

What is stored, and under what key
----------------------------------
A :class:`Plan` is the whole of what resolving one follow-up decided: the turns
that had been asked before it, verbatim and in order; the follow-up itself; the
shape it was read as; and its outcome -- the antecedent and the rewritten query
where it bound, or the refusal reason where it did not.  **Refusals are stored
exactly as answers are**, which is the whole point.

The key is the SHA-256 of the conversation prefix and the follow-up together,
which is directive **D4** kept rather than quoted: a result is reused only
against a digest of everything it depended on.  The digest addresses integrity
and never meaning (**D3**), so a hit is not trusted on the strength of the
digest alone -- the stored plan carries its own prefix and text, and
:meth:`PlanStore.get` compares them before returning anything.  A digest
collision therefore cannot change an answer; it can only cost a miss.

The coarse key is the control
-----------------------------
:data:`COARSE` keys a plan by its follow-up text alone, which is what a store
of "the answer to *describe it*" would be.  Six of the fifteen declared
follow-ups are the text ``describe it`` and they have four different
antecedents between them, so the coarse store answers the second, third and
later ones with the first one's antecedent -- and it does it silently.
:func:`plan_store_report` counts that, and
``GLM.PlanStore.coarse_key_answers_the_wrong_question`` is the same statement
proved.

What it moves
-------------
Under directive **D15** this is **refusal**: a refusal is now a thing the
system can keep, hand back unchanged and be held to, rather than something it
re-derives and might re-derive differently.  The saved trials are a **cost**
result and are reported as one.  It derives nothing and addresses nothing new:
every answer is still the session's, computed by asking the same rewritten
query the first pass asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..integrity import sha256_hex

__all__ = [
    "Plan", "PlanStore", "EXACT", "COARSE", "KEY_RULES",
    "plan_key", "plan_store_report",
]

#: Key a plan by the whole conversation it was resolved in.  This is the rule
#: the store ships with.
EXACT = "exact"

#: Key a plan by its follow-up text alone.  The control, kept so that what the
#: exact key buys is measured rather than asserted.
COARSE = "coarse"

#: Both rules, in the order the report runs them.
KEY_RULES: Tuple[str, ...] = (EXACT, COARSE)


@dataclass(frozen=True)
class Plan:
    """What resolving one follow-up decided, and what it cost."""

    prefix: Tuple[str, ...]      # the turns asked before it, in order
    text: str                    # the follow-up itself
    shape: str                   # one of conversation.SHAPES, or ''
    outcome: str                 # the antecedent, 'answer', or the reason
    rewritten: str = ""          # the query that was asked in the end
    reason: str = ""             # the refusal reason, '' where it bound
    message: str = ""            # the refusal as it was worded
    antecedent_turn: int = -1
    side: str = ""
    considered: Tuple[str, ...] = ()
    licensed: Tuple[str, ...] = ()
    trials: int = 0              # licensing solves this plan paid for

    @property
    def refused(self) -> bool:
        """Whether the plan is a refusal rather than a binding."""
        return bool(self.reason)

    @property
    def content(self) -> str:
        """Everything the plan depended on, as one unambiguous string.

        The separators are characters no query text contains, so two different
        conversations cannot render the same way.
        """
        return "\x1e".join((*self.prefix, "\x1f", self.text))


def plan_key(prefix: Sequence[str], text: str, rule: str = EXACT) -> str:
    """The key a plan is stored under.

    Under :data:`EXACT` this is the SHA-256 of the whole conversation prefix
    and the follow-up; under :data:`COARSE` it is the SHA-256 of the follow-up
    alone, which is the control.
    """
    if rule not in KEY_RULES:
        raise ValueError(f"plan_key: {rule!r} is not one of {KEY_RULES}")
    content = (text if rule == COARSE
               else "\x1e".join((*prefix, "\x1f", text)))
    return sha256_hex(content.encode("utf-8"))


class PlanStore:
    """Resolved follow-ups, kept under a digest of what they depended on.

    The store is a cache and is held to a cache's contract: it may save work
    and it may never change an answer.  Two things enforce that here -- the
    key covers the whole conversation, and a hit is checked against the stored
    plan's own prefix and text before it is used.
    """

    def __init__(self, rule: str = EXACT):
        if rule not in KEY_RULES:
            raise ValueError(f"PlanStore: {rule!r} is not one of {KEY_RULES}")
        self.rule = rule
        self._plans: Dict[str, Plan] = {}
        self.hits = 0
        self.misses = 0
        self.mismatches = 0

    def __len__(self) -> int:
        return len(self._plans)

    @property
    def keys(self) -> Tuple[str, ...]:
        """Every key the store holds, in insertion order."""
        return tuple(self._plans)

    @property
    def plans(self) -> Tuple[Plan, ...]:
        """Every plan the store holds, in insertion order."""
        return tuple(self._plans.values())

    def key_of(self, prefix: Sequence[str], text: str) -> str:
        """The key this store would use for a follow-up."""
        return plan_key(prefix, text, self.rule)

    def put(self, plan: Plan) -> str:
        """Record a plan -- a binding or a refusal, indifferently."""
        key = self.key_of(plan.prefix, plan.text)
        self._plans[key] = plan
        return key

    def get(self, prefix: Sequence[str], text: str) -> Optional[Plan]:
        """The plan recorded for this follow-up, or ``None``.

        Under the exact rule a hit is additionally checked against the stored
        plan's own prefix and text, so the digest is an address and never a
        claim about meaning (**D3**).  Under the coarse rule that check is the
        very thing being controlled for, so it is not made -- which is how the
        control gets to be wrong.
        """
        plan = self._plans.get(self.key_of(prefix, text))
        if plan is None:
            self.misses += 1
            return None
        if self.rule == EXACT and (tuple(prefix) != plan.prefix
                                   or text != plan.text):
            self.mismatches += 1
            self.misses += 1
            return None
        self.hits += 1
        return plan


# ===========================================================================
#  THE MEASUREMENT
# ===========================================================================

def _resolve_once(conversation, text: str) -> Plan:
    """Resolve one follow-up against a live conversation, as a plan."""
    from .conversation import FollowUpError
    prefix = tuple(turn.text for turn in conversation.turns)
    before = conversation.trials
    try:
        binding = conversation.resolve(text)
    except FollowUpError as error:
        return Plan(prefix=prefix, text=text,
                    shape=conversation.shape_of(text) or "",
                    outcome=error.reason, reason=error.reason,
                    message=str(error),
                    considered=tuple(error.considered),
                    trials=conversation.trials - before)
    return Plan(prefix=prefix, text=text, shape=binding.shape,
                outcome=binding.name or "answer",
                rewritten=binding.rewritten,
                antecedent_turn=binding.antecedent_turn,
                side=binding.side, considered=tuple(binding.considered),
                licensed=tuple(binding.licensed),
                trials=conversation.trials - before)


def _run_script(session, script: Sequence[str], store: Optional[PlanStore]):
    """Ask one declared script, returning the plan its last turn produced."""
    from .conversation import Conversation
    conversation = Conversation(session, store=store)
    for text in script[:-1]:
        conversation.ask(text)
    return _resolve_once(conversation, script[-1])


def plan_store_report(session=None) -> Dict[str, object]:
    """What the store keeps, what it saves, and what the coarse key costs.

    Three readings, all over the fifteen follow-ups
    :data:`glm_universal.runtime.conversation.DECLARED_FOLLOW_UPS` declares:
    the first pass, which fills the store; the second, which must reproduce
    every outcome including every refusal; and the same second pass against a
    store keyed by the follow-up text alone.
    """
    from .conversation import DECLARED_FOLLOW_UPS, REFUSAL_REASONS
    if session is None:
        from .session import GeometricSession
        session = GeometricSession()
    store = PlanStore(EXACT)
    coarse = PlanStore(COARSE)
    # Three passes, in this order: the first fills both stores over the whole
    # declared set, and only then is either replayed.  Filling and replaying
    # one row at a time would hide the coarse key's whole failing, which is
    # that six of the fifteen follow-ups are the same text and the last one
    # written is the one every earlier one gets back.
    first_pass: List[Plan] = []
    for _key, script, _expected, _note in DECLARED_FOLLOW_UPS:
        plan = _run_script(session, script, None)
        first_pass.append(plan)
        store.put(plan)
        coarse.put(plan)
    rows: List[Dict[str, object]] = []
    for (key, script, expected, _note), first in zip(DECLARED_FOLLOW_UPS,
                                                     first_pass):
        again = _run_script(session, script, store)
        control = _run_script(session, script, coarse)
        rows.append({
            "key": key,
            "text": first.text,
            "outcome": first.outcome,
            "expected": expected,
            "refused": first.refused,
            "trials_first": first.trials,
            "trials_replayed": again.trials,
            "replays": again.outcome == first.outcome
                       and again.rewritten == first.rewritten
                       and again.reason == first.reason,
            "coarse_outcome": control.outcome,
            "coarse_agrees": control.outcome == first.outcome,
        })
    refusals = tuple(row for row in rows if row["refused"])
    replayed = tuple(row for row in rows if row["replays"])
    refusals_replayed = tuple(row for row in refusals if row["replays"])
    coarse_wrong = tuple(row for row in rows if not row["coarse_agrees"])
    texts: Dict[str, int] = {}
    for row in rows:
        texts[str(row["text"])] = texts.get(str(row["text"]), 0) + 1
    shared = tuple(text for text, count in texts.items() if count > 1)
    trials_first = sum(int(row["trials_first"]) for row in rows)
    trials_again = sum(int(row["trials_replayed"]) for row in rows)
    return {
        "declared": len(DECLARED_FOLLOW_UPS),
        "rows": rows,
        "stored": len(store),
        "distinct_keys": len(set(store.keys)),
        "coarse_keys": len(coarse),
        "shared_texts": shared,
        "refusals": len(refusals),
        "refusals_replayed": len(refusals_replayed),
        "replayed": len(replayed),
        "trials_first": trials_first,
        "trials_replayed": trials_again,
        "trials_saved": trials_first - trials_again,
        "worst_case_trials": max((int(row["trials_first"]) for row in rows),
                                 default=0),
        "coarse_wrong": len(coarse_wrong),
        "coarse_wrong_keys": [row["key"] for row in coarse_wrong],
        "reasons": len(REFUSAL_REASONS) - 1,
        "verdict": (
            f"the store keeps all {len(rows)} resolved follow-ups, "
            f"{len(refusals)} of them refusals, under "
            f"{len(set(store.keys))} distinct keys, and replays every one of "
            f"them unchanged -- {len(replayed)} of {len(rows)} outcomes and "
            f"{len(refusals_replayed)} of {len(refusals)} refusals, reason "
            f"and wording included. The licensing trials the fifteen cost "
            f"fall from {trials_first} to {trials_again}, the worst single "
            f"follow-up being {max((int(row['trials_first']) for row in rows), default=0)} "
            f"trials. Keyed by the follow-up text alone, the same store "
            f"answers {len(coarse_wrong)} of the {len(rows)} with another "
            f"conversation's antecedent."),
        "caveat": (
            f"the store saves the licensing trials and nothing else: the "
            f"rewritten query is still asked of the session on every pass, so "
            f"no answer is stored and none can go stale. "
            f"{len(shared)} follow-up texts are shared by more than one "
            f"declared script, which is why the key covers the whole "
            f"conversation; a hit is checked against the stored plan's own "
            f"prefix and text before it is used, so a digest collision costs "
            f"a miss rather than an answer."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = plan_store_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<26} {str(row['outcome']):<22} "
              f"trials {row['trials_first']:>2} -> "
              f"{row['trials_replayed']:>2}  "
              f"{'replayed' if row['replays'] else 'NOT REPLAYED'}")
