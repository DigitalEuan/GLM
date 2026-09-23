"""``glm_universal.sandbox.memory_split`` -- four memory registers, measured
against the one test the conversation layer actually applies.

What it is
----------
The conversational material supplied with Phase 54 splits a session's memory
four ways -- **episodic** (what happened, decaying at 9/10 a turn),
**semantic** (stable facts, no decay), **procedural** (reusable plans) and
**preferences** (what this user wants) -- and retrieves from each with its own
weighting of four exact-rational components: concept overlap, recency, intent
match and a constant.  The weights and the decay rates here are the supplied
ones, unchanged.

``CONVERSATION_STUDY.md`` §9 said what a round taking it would have to
measure: *which questions are answered because of the split that are not
answered without it.*  This module answers that question, and the answer is
the reason it is in the sandbox rather than in the package.

What it is measured against
---------------------------
:mod:`glm_universal.runtime.conversation` resolves a follow-up by
**licensing**: a candidate antecedent is the antecedent when the query it
produces *solves*.  That is a reading of the registers rather than a rule
about word order, and it is what makes *field electronegativity_pauling of it*
after *describe carbon; describe water* bind **carbon** -- the molecule table
holds no electronegativity.  The split cannot see that: a pronoun names no
concept, so the concept-overlap component of every score is zero on every
pronoun follow-up and what is left is recency and intent.

So the split is not a fifth reading of the conversation.  On the pronoun
follow-ups it is the **recency control the conversation round already ran**,
with a decay rate attached, and :func:`memory_split_report` measures exactly
that: how often it names the antecedent licensing named, and what it does on
the follow-ups licensing refuses.  Where it answers one of those it has not
resolved an ambiguity -- it has chosen a member of it, which is the thing the
refusal exists to avoid.

Why it is in the sandbox
------------------------
Because a memory that scores candidates would quietly start answering the
questions the conversation layer is right to refuse, and because on the
evidence below it buys nothing that licensing does not already give.  The
promotion checklist is computed rather than asserted, and its utility line is
the one that fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "KINDS", "DECAY", "Memory", "MemoryRegister", "SplitMemory",
    "split_rows", "promotion_checklist", "memory_split_report",
]

#: The four registers, in the order the supplied material names them.
KINDS: Tuple[str, ...] = ("episodic", "semantic", "procedural", "preference")

#: Each register's decay rate, exactly as supplied: episodic forgets at 9/10 a
#: turn and the other three do not forget at all.
DECAY: Dict[str, Optional[Fraction]] = {
    "episodic": Fraction(9, 10),
    "semantic": None,
    "procedural": None,
    "preference": None,
}


@dataclass(frozen=True)
class Memory:
    """One turn, as a memory register holds it."""

    turn: int
    text: str
    concepts: Tuple[str, ...]
    intent: str


@dataclass
class MemoryRegister:
    """One register, with its own decay rate and its own weighting."""

    kind: str
    memories: List[Memory] = field(default_factory=list)

    @property
    def decay(self) -> Optional[Fraction]:
        return DECAY[self.kind]

    def add(self, memory: Memory) -> None:
        self.memories.append(memory)

    def score(self, memory: Memory, index: int, concepts: Sequence[str],
              intent: str) -> Fraction:
        """The supplied combined score, exactly: four rational components."""
        total = len(self.memories)
        common = set(concepts) & set(memory.concepts)
        geometry = Fraction(len(common), max(1, len(concepts)))
        recency = (self.decay ** (total - 1 - index) if self.decay is not None
                   else Fraction(1, 2))
        matching = Fraction(1) if memory.intent == intent else Fraction(1, 4)
        if self.kind == "procedural":
            return (Fraction(1, 4) * geometry + Fraction(1, 4) * recency
                    + Fraction(1, 2) * matching)
        if self.kind == "semantic":
            return (Fraction(3, 4) * geometry + Fraction(1, 8) * recency
                    + Fraction(1, 8) * matching)
        if self.kind == "preference":
            return geometry
        return (Fraction(1, 2) * geometry + Fraction(1, 16)
                + Fraction(1, 8) * recency + Fraction(1, 8) * matching)

    def recall(self, concepts: Sequence[str], intent: str,
               top_k: int = 5) -> Tuple[Tuple[Memory, Fraction], ...]:
        """The register's own ranking of what it holds."""
        scored = [(memory, self.score(memory, index, concepts, intent))
                  for index, memory in enumerate(self.memories)]
        scored.sort(key=lambda row: (-row[1], -row[0].turn))
        return tuple(scored[:top_k])


class SplitMemory:
    """The four registers together, and the one name they end up naming."""

    def __init__(self) -> None:
        self.registers = {kind: MemoryRegister(kind) for kind in KINDS}

    def remember(self, memory: Memory, kinds: Sequence[str] = KINDS) -> None:
        for kind in kinds:
            self.registers[kind].add(memory)

    def best(self, concepts: Sequence[str], intent: str
             ) -> Optional[Tuple[str, str, Fraction]]:
        """The highest-scoring memory over all four registers, and its name.

        Returns ``(register, name, score)`` or ``None`` when nothing is held.
        The name is the first concept of the memory, which is what a retrieval
        that returns *a memory* rather than *a referent* leaves the caller to
        do.
        """
        best: Optional[Tuple[str, str, Fraction]] = None
        for kind, register in self.registers.items():
            for memory, score in register.recall(concepts, intent, top_k=1):
                if not memory.concepts:
                    continue
                if best is None or score > best[2]:
                    best = (kind, memory.concepts[0], score)
        return best


# ===========================================================================
#  THE MEASUREMENT -- the split against licensing, on the declared set
# ===========================================================================

def _intent_of(text: str) -> str:
    """The intent a scoring memory can see: the leading word, lowercased."""
    tokens = text.strip().lower().split()
    return tokens[0] if tokens else ""


def split_rows(session=None) -> Tuple[Dict[str, object], ...]:
    """Run the split and the shipped layer over the same declared set."""
    from ..runtime.conversation import (Conversation, DECLARED_FOLLOW_UPS,
                                        FollowUpError)
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    rows: List[Dict[str, object]] = []
    for key, script, _expected, _note in DECLARED_FOLLOW_UPS:
        conversation = Conversation(session)
        memory = SplitMemory()
        for text in script[:-1]:
            solution = conversation.ask(text)
            turn = conversation.turns[-1]
            memory.remember(Memory(
                turn=turn.index, text=text,
                concepts=tuple(m.name for m in turn.mentions),
                intent=_intent_of(text)))
        text = script[-1]
        chosen = memory.best((), _intent_of(text))
        try:
            binding = conversation.resolve(text)
        except FollowUpError as error:
            licensed, reason = "", error.reason
        else:
            licensed, reason = binding.name or "answer", ""
        name = chosen[1] if chosen else ""
        rewritten = (text.replace(" it", f" {name}").replace(" that",
                                                             f" {name}")
                     if name else "")
        solves = bool(name) and bool(session.ask(rewritten).ok)
        rows.append({
            "key": key,
            "refused": bool(reason),
            "licensing": licensed or reason,
            "reason": reason,
            "split": name or "no-memory",
            "register": chosen[0] if chosen else "",
            "agrees": bool(licensed) and name == licensed,
            "answers_a_refusal": bool(reason) and bool(name),
            "answer_solves": solves,
            "moves_an_answer": bool(licensed) and bool(name)
                               and name != licensed,
        })
    return tuple(rows)


def promotion_checklist(rows: Optional[Sequence[Dict[str, object]]] = None,
                        session=None) -> Dict[str, object]:
    """What would have to hold for the split to leave the sandbox.

    The safety line is that it moves no answer the shipped layer gives; the
    utility line is that it answers something the shipped layer does not.  A
    split that only answers where the layer refuses *by choosing a member of
    the ambiguity* fails the second line, because the refusal is the answer
    there.
    """
    rows = list(rows if rows is not None else split_rows(session))
    bound = [row for row in rows if not row["refused"]]
    refused = [row for row in rows if row["refused"]]
    moved = [row["key"] for row in rows if row["moves_an_answer"]]
    gained = [row["key"] for row in refused
              if row["answers_a_refusal"] and row["answer_solves"]]
    ambiguous = [row["key"] for row in refused
                 if row["answers_a_refusal"] and row["answer_solves"]
                 and row["reason"] == "ambiguous-antecedent"]
    checks = {
        "agrees_with_licensing_wherever_licensing_binds":
            bool(bound) and all(row["agrees"] for row in bound),
        "moves_no_answer_the_shipped_layer_gives": not moved,
        "answers_a_refusal_without_choosing_a_member_of_it":
            bool(gained) and not ambiguous,
    }
    return {
        "checks": checks,
        "order": tuple(checks),
        "bound": len(bound),
        "agreed": sum(1 for row in bound if row["agrees"]),
        "refused": len(refused),
        "moved": tuple(moved),
        "gained": tuple(gained),
        "gained_by_choosing": tuple(ambiguous),
        "ready": all(checks.values()),
        "rule": ("The split ships when every line above is true. While any is "
                 "false it stays in the sandbox, and the false line is the "
                 "work that remains."),
    }


def memory_split_report(session=None) -> Dict[str, object]:
    """What the split names, what licensing names, and where they part."""
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    rows = split_rows(session)
    checklist = promotion_checklist(rows)
    bound = tuple(row for row in rows if not row["refused"])
    refused = tuple(row for row in rows if row["refused"])
    agreed = tuple(row for row in bound if row["agrees"])
    answered = tuple(row for row in refused if row["answers_a_refusal"])
    return {
        "registers": len(KINDS),
        "declared": len(rows),
        "rows": rows,
        "bound": len(bound),
        "agreed": len(agreed),
        "disagreed": len(bound) - len(agreed),
        "refused": len(refused),
        "answered_a_refusal": len(answered),
        "checklist": checklist,
        "verdict": (
            f"over the {len(rows)} declared follow-ups the four-register "
            f"split names the same antecedent as licensing on "
            f"{len(agreed)} of the {len(bound)} the shipped layer binds, and "
            f"on the {len(refused)} it refuses the split answers "
            f"{len(answered)}, of which "
            f"{len(checklist['gained'])} produce a query the session really "
            f"answers -- and "
            f"{len(checklist['gained_by_choosing'])} of those do it by "
            f"choosing a member of an ambiguity the refusal exists to keep "
            f"open. It "
            f"moves {len(checklist['moved'])} of the answers the shipped "
            f"layer gives. The promotion checklist reports ready="
            f"{str(checklist['ready']).lower()}."),
        "caveat": (
            "a pronoun names no concept, so the concept-overlap component of "
            "every score is zero on every pronoun follow-up and the split "
            "reduces to recency and intent -- the control the conversation "
            "round already ran. The registers and their weights are the "
            "supplied ones; what is measured here is what they decide, not "
            "whether some other weighting would decide better."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = memory_split_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<26} licensing {str(row['licensing']):<22} "
              f"split {str(row['split']):<16} "
              f"{'agrees' if row['agrees'] else ''}")
