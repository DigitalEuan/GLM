"""``glm_universal.reasoning.timed_question`` -- time and the question.

The question
------------
When the GLM meets a tie it cannot separate with what it has -- six
equidistant Golay codewords at coset weight 4, a junction of carriers with
equal coordinates -- it refuses, by design.  The owner's intuition for Phase
145 was that **time** is what such a tie needs: information that a later step
supplies, either because a later step happens to make an observation that
prunes the wrong candidates (*waiting*), or because the GLM works out exactly
what it needs to know and **asks** for it.  At this stage of the system the
answers come from the developer; later a user gives them, through the same
interface.  ``studies/TIMED_QUESTION_STUDY.md`` pre-registered the marks;
:func:`timed_question_report` measures them.

The object
----------
An :class:`OpenTie` is the candidates, the live set and a **ledger** of time
steps (:class:`TimeStep`): whether the information was waited for, asked for
or a confirmation, the question, the answer, who answered, and what it
removed.  ``RequestProject/GLM/TimedQuestion.lean`` proves the rules it keeps:

* information only removes candidates and its arrival order does not matter
  (``after_subset``, ``after_perm``);
* under truthful answers the truth survives, a tie left with one candidate
  holds it, a tie left with none proves an answer false -- it is reported as
  ``contradicted``, never resolved (``truth_mem_after``,
  ``resolved_eq_truth``, ``contradicted_not_truthful``);
* waiting cannot help when every observation that can arrive is constant on
  the tie -- for a junction, every function of the coordinates
  (``no_time_resolves``, ``no_coordinate_question_resolves``);
* a question is worth asking exactly when it splits the live set
  (``splits_iff``), and halving questions resolve ``n`` candidates in
  ``Nat.clog 2 n`` questions, which no strategy of yes/no questions beats
  (``optimal``).

Asking
------
:meth:`OpenTie.best_question` takes, over the vocabulary's questions that
split the live set, the one whose worst answer leaves the fewest candidates,
ties broken by vocabulary order.  When none splits, the GLM says so and puts
the **direct choice** (*which of these do you mean?*), which always resolves.

Exactness
---------
``int`` masks, strings and :class:`fractions.Fraction` only.  No float, no RNG.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Callable, Dict, Iterable, List, Optional, Sequence,
                    Tuple)

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "Question", "TimeStep", "OpenTie",
    "DeclaredInformant", "LyingInformant", "InteractiveInformant",
    "resolve", "wait", "clog2",
    "golay_tie", "golay_coordinate_questions", "golay_set_questions",
    "golay_stream", "probe_forks",
    "register_objects", "register_junctions", "attribute_vocabulary",
    "junction_tie", "coordinate_observations",
    "locate_tie", "DIALOGUES",
    "g1_waiting", "g2_coordinate_questions", "g3_set_questions",
    "g4_false_answer", "r1_coordinates", "r2_r3_asking", "d1_dialogues",
    "timed_question_report",
    "ANSWER_LEAN_FILE", "ANSWER_LEAN_THEOREMS", "GivenError",
    "answer_token", "split_given", "join_given", "question_of",
    "apply_given", "pending_question", "question_record",
    "describe_question", "match_reply",
]

LEAN_FILE = "RequestProject/GLM/TimedQuestion.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "after_eq_filter", "after_subset", "after_perm", "after_append",
    "truth_mem_after", "resolved_eq_truth", "contradicted_not_truthful",
    "resolved_stays", "no_time_resolves", "no_time_resolves_card",
    "no_coordinate_question_resolves", "prune_ssubset_iff", "splits_iff",
    "adversary", "questions_needed", "exists_halving",
    "halveRun_eq_singleton", "optimal", "six_needs_three")

#: The assumption every resolution by an informant rests on.
TRUTHFUL = ("the informant's answers are true of the thing meant "
            "(GLM.TimedQuestion.resolved_eq_truth)")


def clog2(n: int) -> int:
    """``Nat.clog 2 n``: the least ``k`` with ``n <= 2^k``."""
    k = 0
    while (1 << k) < n:
        k += 1
    return k


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE OPEN TIE
# ═════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Question:
    """A declared question: its text and what each candidate would answer."""

    key: str
    text: str
    answer_of: Callable[[object], object]
    kind: str = "ask"          # "ask", "choice", "confirm" or "observe"


@dataclass(frozen=True)
class TimeStep:
    """One piece of information arriving at a later step."""

    t: int
    mode: str                  # "waited", "asked" or "confirmed"
    question: str
    answer: str
    informant: str
    removed: Tuple[str, ...]


@dataclass
class OpenTie:
    """A tie held open until information resolves it.

    ``candidates`` are the things it could be; ``live`` those no step has
    removed; ``ledger`` the steps in the order they arrived.  ``label`` names
    a candidate in questions and answers.
    """

    candidates: Tuple[object, ...]
    label: Callable[[object], str] = str
    live: Tuple[object, ...] = ()
    ledger: List[TimeStep] = field(default_factory=list)
    title: str = "the tie"

    def __post_init__(self) -> None:
        if not self.live:
            self.live = tuple(self.candidates)

    # -- state ---------------------------------------------------------------
    @property
    def status(self) -> str:
        if len(self.live) == 1:
            return "resolved"
        return "open" if self.live else "contradicted"

    @property
    def value(self) -> Optional[object]:
        return self.live[0] if self.status == "resolved" else None

    def partition_holds(self) -> bool:
        """The live candidates and the removed ones partition the
        candidates (``after_subset`` with the ledger)."""
        gone = [r for s in self.ledger for r in s.removed]
        live = [self.label(c) for c in self.live]
        return (len(set(gone)) == len(gone) and not set(gone) & set(live)
                and sorted(gone + live)
                == sorted(self.label(c) for c in self.candidates))

    def counts(self) -> Dict[str, int]:
        out = {"waited": 0, "asked": 0, "confirmed": 0}
        for s in self.ledger:
            out[s.mode] += 1
        return out

    # -- information arriving --------------------------------------------------
    def apply(self, mode: str, question: Question, answer: object,
              informant: str) -> Tuple[object, ...]:
        """Keep the live candidates that give ``answer`` to ``question``."""
        kept, gone = [], []
        for c in self.live:
            (kept if question.answer_of(c) == answer else gone).append(c)
        self.live = tuple(kept)
        self.ledger.append(TimeStep(
            len(self.ledger) + 1, mode, question.text, _show(answer),
            informant, tuple(self.label(c) for c in gone)))
        return tuple(gone)

    # -- asking ------------------------------------------------------------------
    def options(self, question: Question) -> Tuple[object, ...]:
        """The answers the live candidates would give, in first-seen order."""
        seen: List[object] = []
        for c in self.live:
            a = question.answer_of(c)
            if a not in seen:
                seen.append(a)
        return tuple(seen)

    def worst(self, question: Question) -> int:
        """The most candidates any answer to ``question`` leaves."""
        sizes: Dict[object, int] = {}
        for c in self.live:
            a = question.answer_of(c)
            sizes[a] = sizes.get(a, 0) + 1
        return max(sizes.values()) if sizes else 0

    def splits(self, question: Question) -> bool:
        """``splits_iff``: worth asking exactly when it takes two values."""
        return len(self.options(question)) > 1

    def best_question(self, vocabulary: Iterable[Question]
                      ) -> Optional[Question]:
        """The minimax question of the vocabulary, or ``None`` when no
        question in it splits the live set."""
        best, best_worst = None, None
        for q in vocabulary:
            if not self.splits(q):
                continue
            w = self.worst(q)
            if best_worst is None or w < best_worst:
                best, best_worst = q, w
        return best

    def choice_question(self) -> Question:
        """The direct choice: *which of these do you mean?*"""
        names = ", ".join(self.label(c) for c in self.live)
        return Question("choice", f"Which of these do you mean: {names}?",
                        self.label, kind="choice")

    def confirm_question(self, candidate: object) -> Question:
        """*Is it exactly this one?* -- one more step that turns a single
        false answer into a contradiction."""
        name = self.label(candidate)
        return Question(f"confirm:{name}", f"Is it exactly {name}?",
                        lambda c, name=name: self.label(c) == name,
                        kind="confirm")


def _show(answer: object) -> str:
    if answer is True:
        return "yes"
    if answer is False:
        return "no"
    return str(answer)


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE INFORMANTS
# ═════════════════════════════════════════════════════════════════════════

class DeclaredInformant:
    """The developer, at this stage of the system: told the truth, answers
    every question as the truth would."""

    def __init__(self, truth: object, name: str = "developer") -> None:
        self.truth = truth
        self.name = name
        self.asked = 0

    def answer(self, question: Question, options: Sequence[object]) -> object:
        self.asked += 1
        return question.answer_of(self.truth)


class LyingInformant(DeclaredInformant):
    """The control: answers the ``lie_at``-th question (1-based) with an
    option other than the truth's, and every other question truthfully."""

    def __init__(self, truth: object, lie_at: int = 1,
                 name: str = "developer (one false answer)") -> None:
        super().__init__(truth, name)
        self.lie_at = lie_at

    def answer(self, question: Question, options: Sequence[object]) -> object:
        self.asked += 1
        true = question.answer_of(self.truth)
        if self.asked == self.lie_at:
            for o in options:
                if o != true:
                    return o
            if isinstance(true, bool):
                return not true
        return true


class InteractiveInformant:
    """The person at the terminal (the developer now, a user later): the
    question and its possible answers are shown, the answer is read."""

    NONE = "none of these"

    def __init__(self, read: Callable[[str], str] = input,
                 write: Callable[[str], None] = print,
                 name: str = "interactive") -> None:
        self.read = read
        self.write = write
        self.name = name

    def answer(self, question: Question, options: Sequence[object]) -> object:
        self.write(f"GLM asks: {question.text}")
        shown = list(options) + [self.NONE]
        for k, o in enumerate(shown, 1):
            self.write(f"  {k}. {_show(o)}")
        while True:
            reply = self.read("answer> ").strip()
            for k, o in enumerate(shown, 1):
                if reply == str(k) or reply.lower() == _show(o).lower():
                    return o
            self.write("  (give the number or the text of one option)")


# ═════════════════════════════════════════════════════════════════════════
# 3.  WAITING AND ASKING
# ═════════════════════════════════════════════════════════════════════════

def wait(tie: OpenTie, stream: Iterable[Tuple[Question, object]],
         until_resolved: bool = True) -> OpenTie:
    """Apply the observations a later step makes, in arrival order."""
    for question, value in stream:
        if until_resolved and tie.status != "open":
            break
        tie.apply("waited", question, value, "a later step")
    return tie


def resolve(tie: OpenTie, vocabulary: Callable[[OpenTie], Sequence[Question]],
            informant, confirm: bool = False, limit: int = 64) -> OpenTie:
    """Ask until the tie is resolved or contradicted: the minimax question of
    the vocabulary, else the direct choice; then, if asked, confirm."""
    while tie.status == "open" and len(tie.ledger) < limit:
        q = tie.best_question(vocabulary(tie)) or tie.choice_question()
        tie.apply("asked", q, informant.answer(q, tie.options(q)),
                  informant.name)
    if confirm and tie.status == "resolved":
        q = tie.confirm_question(tie.value)
        tie.apply("confirmed", q, informant.answer(q, (True, False)),
                  informant.name)
    return tie


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE GOLAY FORK
# ═════════════════════════════════════════════════════════════════════════

N = 24


def _support(mask: int) -> Tuple[int, ...]:
    return tuple(j for j in range(N) if (mask >> j) & 1)


def golay_tie(received: int) -> Tuple[OpenTie, Callable[[int], int]]:
    """The six nearest codewords of ``received`` as an open tie, and the
    tetrad (error pattern) each candidate implies."""
    from .carried_fork import carry
    fork = carry(received)
    tie = OpenTie(fork.candidates, label=lambda c: f"{c:#08x}",
                  title=f"the read {received:#08x}")
    return tie, fork.tetrad


def golay_coordinate_questions(tetrad: Callable[[int], int]
                               ) -> Tuple[Question, ...]:
    """"Was coordinate j received correctly?" for the 24 coordinates."""
    return tuple(Question(f"coord:{j}",
                          f"Was coordinate {j} received correctly?",
                          lambda c, j=j: not (tetrad(c) >> j) & 1)
                 for j in range(N))


def golay_set_questions(tie: OpenTie, tetrad: Callable[[int], int]
                        ) -> Tuple[Question, ...]:
    """The halving question the GLM constructs from the live tetrads: "did
    the error fall among coordinates S?", S the union of the first half."""
    live = tie.live
    if len(live) < 2:
        return ()
    mask = 0
    for c in live[:len(live) // 2]:
        mask |= tetrad(c)
    return (Question(f"set:{mask:#08x}",
                     f"Did the error fall among coordinates "
                     f"{list(_support(mask))}?",
                     lambda c, mask=mask: bool(tetrad(c) & mask)),)


def golay_stream(i: int, truth: int, tetrad: Callable[[int], int]
                 ) -> List[Tuple[Question, object]]:
    """What later steps report for fork ``i``: "coordinate j was received
    correctly" for each coordinate that was, in the order
    ``(13 j + 7 i) mod 24``."""
    err = tetrad(truth)
    order = sorted((j for j in range(N) if not (err >> j) & 1),
                   key=lambda j: ((13 * j + 7 * i) % N, j))
    return [(Question(f"coord:{j}",
                      f"A later step reports coordinate {j} was received "
                      f"correctly",
                      lambda c, j=j: not (tetrad(c) >> j) & 1,
                      kind="observe"), True) for j in order]


def probe_forks() -> List[Tuple[int, int, int]]:
    """The 768 forks of Phase 65's probe: ``(i, received, transmitted)``."""
    from .carried_fork import x1_probe
    words, errs = x1_probe()
    out = []
    for c in words:
        for e in errs:
            out.append((len(out), c ^ e, c))
    return out


def _stats(values: Sequence[int]) -> Dict[str, object]:
    return {"runs": len(values), "max": max(values), "min": min(values),
            "mean": Fraction(sum(values), len(values)) if values else None,
            "histogram": {str(k): values.count(k)
                          for k in sorted(set(values))}}


def g1_waiting(forks=None) -> Dict[str, object]:
    """G1: waiting on the stream of later reports."""
    forks = forks if forks is not None else probe_forks()
    steps, resolved, wrong, other = [], 0, 0, 0
    for i, received, truth in forks:
        tie, tetrad = golay_tie(received)
        wait(tie, golay_stream(i, truth, tetrad))
        if tie.status == "resolved":
            resolved += 1
            wrong += tie.value != truth
        else:
            other += 1
        steps.append(tie.counts()["waited"])
    return {"forks": len(forks), "resolved": resolved, "wrong": wrong,
            "unresolved": other, "reports": _stats(steps)}


def _ask_golay(forks, use_sets: bool) -> Dict[str, object]:
    steps, resolved, wrong, choices = [], 0, 0, 0
    for _i, received, truth in forks:
        tie, tetrad = golay_tie(received)
        coords = golay_coordinate_questions(tetrad)
        vocab = ((lambda t: golay_set_questions(t, tetrad)) if use_sets
                 else (lambda t: coords))
        resolve(tie, vocab, DeclaredInformant(truth))
        if tie.status == "resolved":
            resolved += 1
            wrong += tie.value != truth
        choices += sum(1 for s in tie.ledger
                       if s.question.startswith("Which of these"))
        steps.append(tie.counts()["asked"])
    return {"forks": len(forks), "resolved": resolved, "wrong": wrong,
            "direct_choices": choices, "questions": _stats(steps)}


def g2_coordinate_questions(forks=None) -> Dict[str, object]:
    """G2: asking "was coordinate j received correctly?"."""
    return _ask_golay(forks if forks is not None else probe_forks(), False)


def g3_set_questions(forks=None) -> Dict[str, object]:
    """G3: asking the halving set questions the GLM constructs."""
    return _ask_golay(forks if forks is not None else probe_forks(), True)


def g4_false_answer(forks=None) -> Dict[str, object]:
    """G4: one set question answered falsely, without and with the
    confirming question."""
    forks = forks if forks is not None else probe_forks()
    out = {}
    for confirm in (False, True):
        runs = wrong = contradicted = right = 0
        for _i, received, truth in forks:
            for lie_at in (1, 2):
                tie, tetrad = golay_tie(received)
                vocab = lambda t, tetrad=tetrad: golay_set_questions(t, tetrad)
                resolve(tie, vocab, LyingInformant(truth, lie_at),
                        confirm=confirm)
                if tie.counts()["asked"] < lie_at:
                    continue      # resolved before the false answer came
                runs += 1
                if tie.status == "contradicted":
                    contradicted += 1
                elif tie.value == truth:
                    right += 1
                else:
                    wrong += 1
        out["with_confirmation" if confirm else "without_confirmation"] = {
            "runs": runs, "resolved_wrong": wrong,
            "contradicted": contradicted, "resolved_right": right}
    return out


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE REGISTER JUNCTIONS
# ═════════════════════════════════════════════════════════════════════════

_registry: Optional[Dict[str, object]] = None

#: Attributes the vocabulary never asks for: asking them is asking the answer
#: (``symbol``), and the gloss is asked word by word.
_NOT_ASKED = ("symbol", "gloss")
_WORD = re.compile(r"[a-z]{4,}")


def register_objects() -> Dict[str, object]:
    """Every register object of the six registers, by ``register:name``."""
    global _registry
    if _registry is None:
        from . import escalation as ESC
        reg: Dict[str, object] = {}
        for register in ESC.REGISTERS:
            for obj in ESC._register_loader(register)():
                reg[f"{register}:{obj.name}"] = obj
        _registry = reg
    return _registry


def register_junctions() -> List[Tuple[str, ...]]:
    """The junctions of the full registers (Phase 144's census), each in
    register order, ordered by their first member."""
    from . import escalation as ESC
    groups: Dict[Tuple[Fraction, ...], List[str]] = {}
    for register in ESC.REGISTERS:
        for obj in ESC._register_loader(register)():
            key = tuple(Fraction(x) for x in obj.carrier)
            groups.setdefault(key, []).append(f"{register}:{obj.name}")
    return sorted(tuple(g) for g in groups.values() if len(g) > 1)


def _attrs(label: str) -> Dict[str, object]:
    return dict(getattr(register_objects()[label], "attributes", {}) or {})


def _words(label: str) -> frozenset:
    return frozenset(_WORD.findall(str(_attrs(label).get("gloss", "")).lower()))


def attribute_vocabulary(tie: OpenTie) -> Tuple[Question, ...]:
    """The declared vocabulary for a junction: "what is its attribute?" for
    each attribute but the symbol and the gloss, then "does its description
    mention 'word'?" for each gloss word of four or more letters."""
    members = tie.live
    keys = sorted(set().union(*(_attrs(m) for m in members)) - set(_NOT_ASKED))
    out = [Question(f"attr:{k}", f"What is its {k.replace('_', ' ')}?",
                    lambda c, k=k: repr(_attrs(c).get(k)))
           for k in keys]
    words = sorted(set().union(*(_words(m) for m in members)))
    out += [Question(f"word:{w}", f"Does its description mention '{w}'?",
                     lambda c, w=w: w in _words(c)) for w in words]
    return tuple(out)


def junction_tie(members: Sequence[str]) -> OpenTie:
    return OpenTie(tuple(members), label=str,
                   title=f"the junction {{{', '.join(members)}}}")


def coordinate_observations(members: Sequence[str]
                            ) -> List[Tuple[Question, object]]:
    """Everything a later step could observe of a junction's coordinates:
    each of the 24 coordinates, and the junction read itself."""
    reg = register_objects()
    truth = members[0]
    coord = lambda c: tuple(Fraction(x) for x in reg[c].carrier)
    out = [(Question(f"coord:{j}", f"coordinate {j}",
                     lambda c, j=j: coord(c)[j], kind="observe"),
            coord(truth)[j]) for j in range(N)]
    out.append((Question("read", "the junction read of the point",
                         lambda c: coord(c), kind="observe"), coord(truth)))
    return out


def r1_coordinates(junctions=None) -> Dict[str, object]:
    """R1: waiting on every coordinate observation removes nothing."""
    junctions = junctions if junctions is not None else register_junctions()
    unchanged = 0
    for members in junctions:
        for truth in members:
            tie = junction_tie(members)
            obs = coordinate_observations((truth,) + tuple(
                m for m in members if m != truth))
            wait(tie, obs, until_resolved=False)
            if len(tie.live) != len(members):
                break
        else:
            unchanged += 1
    return {"junctions": len(junctions), "unchanged": unchanged,
            "carriers": sum(len(m) for m in junctions)}


def r2_r3_asking(junctions=None) -> Dict[str, object]:
    """R2 and R3: asking the vocabulary, against the clog2 bound and the
    one-by-one baseline."""
    junctions = junctions if junctions is not None else register_junctions()
    asked, bound, baseline = [], [], []
    resolved = wrong = with_choice = 0
    first_questions: Dict[str, int] = {}
    for members in junctions:
        for pos, truth in enumerate(members, 1):
            tie = junction_tie(members)
            resolve(tie, attribute_vocabulary, DeclaredInformant(truth))
            if tie.status == "resolved":
                resolved += 1
                wrong += tie.value != truth
            if any(s.question.startswith("Which of these")
                   for s in tie.ledger):
                with_choice += 1
            asked.append(tie.counts()["asked"])
            bound.append(clog2(len(members)))
            baseline.append(min(pos, len(members) - 1))
            if tie.ledger:
                q = tie.ledger[0].question
                key = ("word" if q.startswith("Does its description")
                       else "choice" if q.startswith("Which of these")
                       else q)
                first_questions[key] = first_questions.get(key, 0) + 1
    runs = len(asked)
    return {"junctions": len(junctions), "runs": runs,
            "resolved": resolved, "wrong": wrong,
            "with_direct_choice": with_choice,
            "without_direct_choice": runs - with_choice,
            "questions": _stats(asked),
            "clog2_mean": Fraction(sum(bound), runs),
            "baseline_mean": Fraction(sum(baseline), runs),
            "first_questions": dict(sorted(first_questions.items(),
                                           key=lambda kv: (-kv[1], kv[0])))}


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE LOCATE TIE AND THE DIALOGUES
# ═════════════════════════════════════════════════════════════════════════

def locate_tie(text: str) -> Tuple[Optional[OpenTie], str]:
    """Run ``text`` (a ``locate`` question) through the session.  A junction
    answer opens a tie over its members; a single carrier opens none."""
    from ..runtime.parser import parse_query
    from ..runtime.session import GeometricSession
    session = GeometricSession(domains=())
    sol = session.solve(parse_query(text))
    if not sol.ok:
        return None, f"refused: {sol.error}"
    payload = dict(sol.payload)
    members = tuple(payload.get("junction") or ())
    if len(members) < 2:
        return None, f"no tie: {payload.get('carrier')}"
    return junction_tie(members), sol.answer


#: ``(id, tie, truth, declared)``: ``("resolved", truth, max questions)`` or
#: ``("no tie", carrier)``.  The study's section 3.
DIALOGUES: Tuple[Tuple[str, str, Optional[str], tuple], ...] = (
    ("T-D1", "locate albedo", "physics:albedo",
     ("resolved", "physics:albedo", 1)),
    ("T-D2", "locate absorptance", "physics:absorptance",
     ("resolved", "physics:absorptance", 1)),
    ("T-D3", "locate acoustic_power_level", "physics:acoustic_power_level",
     ("resolved", "physics:acoustic_power_level", 2)),
    ("T-D4", "locate filled_4x6", "mathematics:filled_4x6",
     ("resolved", "mathematics:filled_4x6", 3)),
    ("T-D5", "locate C", None, ("no tie", "chemistry:C")),
    ("T-D6", "fork 0", None, ("resolved", "transmitted", 3)),
)


def run_dialogue(tie_text: str, truth: Optional[str], informant=None,
                 confirm: bool = False,
                 announce: Optional[Callable[[str, OpenTie], None]] = None
                 ) -> Dict[str, object]:
    """One tie, opened from ``tie_text`` (``locate ...`` or ``fork i``), and
    resolved by asking ``informant`` (by default the developer, told
    ``truth``).  ``announce`` is called with the read and the tie once the
    tie is open, before the first question."""
    if tie_text.startswith("fork"):
        i = int(tie_text.split()[1], 0)
        forks = probe_forks()
        if i < len(forks):
            _i, received, transmitted = forks[i]
        else:
            received, transmitted = i, None
        tie, tetrad = golay_tie(received)
        target = transmitted if truth is None else int(truth, 0)
        informant = informant or DeclaredInformant(target)
        opened = (f"the read {received:#08x} is at coset weight 4: six "
                  f"codewords are equally near, and the decoder refuses to "
                  f"choose")
        vocab = lambda t: golay_set_questions(t, tetrad)
        label = None if transmitted is None else f"{transmitted:#08x}"
    else:
        tie, opened = locate_tie(tie_text)
        if tie is None:
            return {"tie": tie_text, "opened": False, "read": opened,
                    "status": "no tie", "asked": 0, "steps": []}
        informant = informant or DeclaredInformant(truth)
        vocab = attribute_vocabulary
        label = truth
    if announce is not None:
        announce(opened, tie)
    resolve(tie, vocab, informant, confirm=confirm)
    return {"tie": tie_text, "opened": True, "read": opened,
            "candidates": [tie.label(c) for c in tie.candidates],
            "status": tie.status,
            "value": None if tie.value is None else tie.label(tie.value),
            "truth": label, "asked": tie.counts()["asked"],
            "steps": [s.__dict__ for s in tie.ledger],
            "partition": tie.partition_holds()}


def d1_dialogues() -> Dict[str, object]:
    rows = []
    for did, text, truth, declared in DIALOGUES:
        r = run_dialogue(text, truth)
        if declared[0] == "no tie":
            ok = r["status"] == "no tie" and declared[1] in r["read"]
        else:
            want = r["truth"] if declared[1] == "transmitted" else declared[1]
            ok = (r["status"] == "resolved" and r["value"] == want
                  and r["asked"] <= declared[2])
        rows.append({"id": did, "tie": text, "status": r["status"],
                     "value": r.get("value"), "asked": r["asked"],
                     "as_declared": ok,
                     "questions": [s["question"] for s in r["steps"]]})
    return {"rows": rows, "declared": len(rows),
            "as_declared": sum(r["as_declared"] for r in rows),
            "missed": [r["id"] for r in rows if not r["as_declared"]]}


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def timed_question_report() -> Dict[str, object]:
    """Every measured mark of ``studies/TIMED_QUESTION_STUDY.md`` (L1 is
    pinned by the build)."""
    forks = probe_forks()
    g1 = g1_waiting(forks)
    g2 = g2_coordinate_questions(forks)
    g3 = g3_set_questions(forks)
    g4 = g4_false_answer(forks)
    junctions = register_junctions()
    r1 = r1_coordinates(junctions)
    rr = r2_r3_asking(junctions)
    d1 = d1_dialogues()
    n = len(forks)
    w, c = g4["without_confirmation"], g4["with_confirmation"]
    marks = {
        "G1": (g1["resolved"] == n and g1["wrong"] == 0
               and g1["reports"]["max"] <= 17
               and Fraction(7) <= g1["reports"]["mean"] <= Fraction(21, 2)),
        "G2": (g2["resolved"] == n and g2["wrong"] == 0
               and g2["questions"]["max"] == 5),
        "G3": (g3["resolved"] == n and g3["wrong"] == 0
               and g3["questions"]["max"] == 3 == clog2(6)
               and 2 * g3["questions"]["mean"] <= g1["reports"]["mean"]),
        "G4": (w["runs"] > 0 and w["resolved_wrong"] == w["runs"]
               and c["runs"] > 0 and c["contradicted"] == c["runs"]
               and c["resolved_wrong"] == 0),
        "R1": r1["unchanged"] == r1["junctions"] == len(junctions),
        "R2": (rr["resolved"] == rr["runs"] and rr["wrong"] == 0
               and 10 * rr["without_direct_choice"] >= 9 * rr["runs"]),
        "R3": (rr["questions"]["mean"] <= rr["clog2_mean"] + 1
               and rr["questions"]["mean"] < rr["baseline_mean"]),
        "D1": d1["as_declared"] == d1["declared"],
    }
    return {"lean_file": LEAN_FILE, "lean_theorems": list(LEAN_THEOREMS),
            "g1": g1, "g2": g2, "g3": g3, "g4": g4,
            "r1": r1, "r2_r3": rr, "d1": d1, "marks": marks,
            "met": sum(marks.values()), "taken": len(marks)}


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE QUESTION IN THE ANSWERING PATH  (Phase 146)
# ═════════════════════════════════════════════════════════════════════════
#
# ``studies/ANSWERING_QUESTION_STUDY.md``.  A ``locate`` answer that is a
# junction ends with the one question that would split it; the reply is the
# conversation's next turn, rewritten to a whole query
#
#     locate albedo given word:absorbed is no
#
# that the session answers.  ``RequestProject/GLM/AnsweringQuestion.lean``
# proves the turn-by-turn reading: a reply prunes the live set the previous
# turn left (``after_reply``), every reply to a question the GLM puts removes
# a candidate, so a dialogue over ``n`` candidates ends within ``n - 1``
# replies (``dialogue_bound``, ``dialogue_length_lt``), and the confirming
# question turns a false resolution into a contradiction
# (``confirm_catches``).

ANSWER_LEAN_FILE = "RequestProject/GLM/AnsweringQuestion.lean"
ANSWER_LEAN_THEOREMS: Tuple[str, ...] = (
    "after_reply", "reply_removes", "dialogue_bound", "dialogue_length_lt",
    "confirm_yes", "confirm_no", "confirm_catches")

#: The words that separate the place from the replies in a ``locate``
#: request, and one reply from the next.
GIVEN = re.compile(r"\s+given\s+", re.IGNORECASE)
_REPLY = re.compile(r"^(\S+)\s+is\s+(\S.*)$")


class GivenError(ValueError):
    """A reply the answering path cannot read, with a stated reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def answer_token(answer: object) -> str:
    """The text a reply carries for ``answer``: ``yes``/``no`` for a truth
    value, the bare text of a quoted attribute, else its own text."""
    shown = _show(answer)
    if (len(shown) >= 2 and shown[0] == shown[-1] and shown[0] in "'\""):
        return shown[1:-1]
    return shown


def split_given(request: str) -> Tuple[str, List[Tuple[str, str]]]:
    """``"albedo given word:absorbed is no; attr:unit is dB"`` ->
    ``("albedo", [("word:absorbed", "no"), ("attr:unit", "dB")])``.

    The place is everything before the first ``given``; each reply is
    ``key is answer``, replies separated by ``;``.  A reply of any other
    form is refused (``malformed-reply``).  The word ``is`` and not ``=``
    separates them: an ``=`` would make the request read as an identity to
    the description layer's infix ``verify`` shape (found by this round's
    frozen-path comparison)."""
    parts = GIVEN.split(request.strip(), maxsplit=1)
    if len(parts) == 1:
        return parts[0].strip(), []
    place, tail = parts[0].strip(), parts[1]
    given: List[Tuple[str, str]] = []
    for chunk in tail.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = _REPLY.match(chunk)
        if m is None:
            raise GivenError("malformed-reply",
                             f"the reply {chunk!r} is not of the form "
                             f"'question is answer'")
        given.append((m.group(1), m.group(2).strip()))
    if not given:
        raise GivenError("malformed-reply",
                         "'given' is followed by no reply")
    return place, given


def join_given(place: str, given: Sequence[Tuple[str, str]]) -> str:
    """The inverse of :func:`split_given`."""
    if not given:
        return place
    return place + " given " + "; ".join(f"{k} is {v}" for k, v in given)


def question_of(tie: OpenTie, key: str) -> Optional[Question]:
    """The declared question ``key`` over the tie's *candidates*: an
    attribute or a gloss word of :func:`attribute_vocabulary`, the direct
    choice (``choice``), or a confirmation (``confirm:<member>``)."""
    if key == "choice":
        return Question("choice", "Which of these do you mean?", tie.label,
                        kind="choice")
    if key.startswith("confirm:"):
        name = key[len("confirm:"):]
        if name not in {tie.label(c) for c in tie.candidates}:
            return None
        return tie.confirm_question(
            next(c for c in tie.candidates if tie.label(c) == name))
    full = OpenTie(tie.candidates, label=tie.label)
    for q in attribute_vocabulary(full):
        if q.key == key:
            return q
    return None


def _matching_answer(tie: OpenTie, q: Question, token: str) -> object:
    """The answer among the *candidates'* answers to ``q`` whose token is
    ``token``; refused when none or more than one is."""
    found: List[object] = []
    for c in tie.candidates:
        a = q.answer_of(c)
        if answer_token(a) == token and a not in found:
            found.append(a)
    if not found:
        raise GivenError("not-an-option",
                         f"{token!r} is no candidate's answer to "
                         f"{q.text!r}")
    if len(found) > 1:                     # pragma: no cover -- guarded
        raise GivenError("ambiguous-answer",
                         f"{token!r} stands for {len(found)} answers to "
                         f"{q.text!r}")
    return found[0]


def apply_given(tie: OpenTie, given: Sequence[Tuple[str, str]],
                informant: str = "the conversation") -> OpenTie:
    """Apply replies, in the order given (``after_perm``: the order does not
    change the live set).  A ``confirm:`` reply is recorded as a
    confirmation, every other reply as asked."""
    for key, token in given:
        q = question_of(tie, key)
        if q is None:
            raise GivenError("unknown-question",
                             f"{key!r} is not a question declared for "
                             f"{tie.title}")
        mode = "confirmed" if q.kind == "confirm" else "asked"
        tie.apply(mode, q, _matching_answer(tie, q, token), informant)
    return tie


def pending_question(tie: OpenTie) -> Optional[Question]:
    """The question the answer ends with: while open, the minimax question
    of the vocabulary (else the direct choice); once resolved and not yet
    confirmed, the confirming question; otherwise none."""
    if tie.status == "open":
        live = OpenTie(tie.live, label=tie.label)
        q = live.best_question(attribute_vocabulary(live))
        return q or live.choice_question()
    if tie.status == "resolved" and not any(
            s.mode == "confirmed" for s in tie.ledger):
        return tie.confirm_question(tie.value)
    return None


def question_record(tie: OpenTie, q: Question) -> Dict[str, object]:
    """The question as the answer and the conversation carry it: its key,
    its text and, for each answer the live candidates give, the reply token
    and the members that answer keeps."""
    options = []
    if q.kind == "confirm":
        keeps = {True: [tie.label(c) for c in tie.live], False: []}
        for a in (True, False):
            options.append({"reply": answer_token(a), "keeps": keeps[a]})
    else:
        for a in tie.options(q):
            options.append({"reply": answer_token(a),
                            "keeps": [tie.label(c) for c in tie.live
                                      if q.answer_of(c) == a]})
    # the answers only removed members give: not offered, but read when
    # replied, and they leave no member (a contradiction is reported)
    shown = {o["reply"] for o in options}
    others: List[str] = []
    if q.kind != "confirm":
        for c in tie.candidates:
            token = answer_token(q.answer_of(c))
            if token not in shown and token not in others:
                others.append(token)
    return {"key": q.key, "text": q.text, "kind": q.kind,
            "options": options, "others": others}


def describe_question(record: Dict[str, object]) -> str:
    """One sentence: the question and what each reply keeps."""
    parts = []
    for o in record["options"]:
        keeps = o["keeps"]
        what = (", ".join(keeps) if keeps else "no member (a contradiction)")
        parts.append(f"{o['reply']}: {what}")
    return f"{record['text']} ({'; '.join(parts)})"


def match_reply(record: Dict[str, object], text: str) -> Optional[str]:
    """The reply token ``text`` gives to the question ``record``, or
    ``None`` when it is not a reply to it.  Accepted: the option's number
    (1-based), its token, the token in quotes, or -- for the direct choice --
    a member's name without its register prefix; case is ignored."""
    said = text.strip().rstrip("?.!").strip()
    if len(said) >= 2 and said[0] == said[-1] and said[0] in "'\"":
        said = said[1:-1]
    low = said.lower()
    offered = [str(o["reply"]) for o in record["options"]]
    tokens = offered + [str(t) for t in record.get("others", ())]
    # the text of an option first, then its number: a reply "1" to "what is
    # its cols?" is the option whose text is 1, not the first option
    hits = [t for t in tokens if t.lower() == low]
    if not hits and record.get("kind") == "choice":
        hits = [t for t in tokens if ":" in t
                and t.split(":", 1)[1].lower() == low]
    if not hits and low.isdigit() and 1 <= int(low) <= len(offered):
        hits = [offered[int(low) - 1]]
    return hits[0] if len(hits) == 1 else None
