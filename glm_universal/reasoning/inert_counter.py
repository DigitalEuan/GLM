"""``glm_universal.reasoning.inert_counter`` -- inert variables: a
non-termination certificate for GLM-BAT past the control state (Phase 126).

``studies/INERT_COUNTER_STUDY.md`` pre-registered the rule, a ten-program
battery and seven marks.  The rule itself lives in the machine
(:func:`batch_machine.inert_variables` and the forgetful re-reading in
:func:`batch_machine.run_program`); the answer and the ``never_inert``
column-3 claim live in :mod:`batch_speech`.  This module holds the battery and
takes the marks:

* I2 -- the battery N1 ... N10 as declared;
* I3 -- the questions asked of it;
* I4 -- every ``never_inert`` claim's column-3 script passes, every mutation
  fails;
* I5 -- the Phase 125 battery, questions, English programs and generated
  programs keep their answers, M15 and Q6 apart;
* I6 -- no certified program halts within 200000 steps when run without the
  rule, and N3 halts there;
* I1 and I7 are pinned by the tests and the evaluation.

Exact and deterministic: no randomness, no floating point.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from . import batch_machine as bm
from . import batch_speech as bs
from . import operations as op

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BATTERY", "QUESTIONS", "LONG_BUDGET",
    "battery_marks", "question_marks", "certificate_marks",
    "noninterference_marks", "soundness_marks", "inert_counter_report",
]

LEAN_FILE = "RequestProject/GLM/InertCounter.lean"
LEAN_THEOREMS: Tuple[str, ...] = ("inert_step_commutes", "inert_run_fst",
                                  "never_halts_of_inert_repeat")
#: The budget of the soundness control (I6).
LONG_BUDGET = 200_000


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.split(" / "))


#: The battery of section 3, with the declared verdicts.
BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("N1", op.M15, {"status": "never", "forgotten": ("N",),
                    "certificate": (2, 4)}),
    ("N2", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("N3", _lines("SET /A N=0 / :UP / SET /A N=N+1 / "
                  "IF %N% LSS 20000 GOTO UP / ECHO done"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET", "long_steps": 40003}),
    ("N4", _lines("SET /A N=0 / SET /A M=0 / :UP / SET /A N=N+1 / "
                  "SET /A M=M+N / GOTO UP"),
     {"status": "never", "forgotten": ("M", "N"), "certificate": (3, 6)}),
    ("N5", _lines("SET /A N=1 / :UP / SET /A N=N*2 / SET /A Q=10/N / GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("N6", _lines("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / "
                  "SET /A B=B+A / IF %B% GTR -1 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("N7", _lines("SET /A K=0 / :TOP / CALL :BUMP / GOTO TOP / :BUMP / "
                  "SET /A K=K+1 / GOTO :EOF"),
     {"status": "never", "forgotten": ("K",), "certificate": (2, 6)}),
    ("N8", _lines("SET S=x / :UP / SET S=%S%x / GOTO UP"),
     {"status": "never", "forgotten": ("S",), "certificate": (2, 4)}),
    ("N9", _lines("SET /A N=0 / :UP / SET /A N=N+1 / "
                  "IF %N% LSS 5 GOTO UP / ECHO %N%"),
     {"status": "halted", "steps": 13, "out": ("5",), "exit": 0}),
    ("N10", op.M13, {"status": "never", "forgotten": (),
                     "certificate": (2, 4)}),
)

#: The questions of mark I3: (program, question, expected).
QUESTIONS: Tuple[Tuple[str, str, Tuple], ...] = (
    ("N1", "does it halt?", ("never", ("N",), (2, 4))),
    ("N4", "does it halt?", ("never", ("M", "N"), (3, 6))),
    ("N7", "does it halt?", ("never", ("K",), (2, 6))),
    ("N8", "does it halt?", ("never", ("S",), (2, 4))),
    ("N2", "does it halt?", ("refused", "UNDECIDED_WITHIN_BUDGET")),
    ("N3", "does it halt?", ("refused", "UNDECIDED_WITHIN_BUDGET")),
    ("N5", "does it halt?", ("refused", "UNDECIDED_WITHIN_BUDGET")),
    ("N6", "does it halt?", ("refused", "UNDECIDED_WITHIN_BUDGET")),
    ("N1", "what does it print?", ("refused", "NEVER_HALTS")),
)


def _battery_lines(ident: str) -> Tuple[str, ...]:
    return next(lines for i, lines, _ in BATTERY if i == ident)


def battery_marks() -> Dict[str, object]:
    """I2: each battery program as declared."""
    rows: List[Dict[str, object]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines))
        if "refusal" in exp:
            ok = run.status == "undecided"
            got: object = run.status
        elif exp["status"] == "never":
            ok = (run.status == "never"
                  and run.certificate == tuple(exp["certificate"])
                  and run.forgotten == tuple(exp["forgotten"]))
            got = (run.status, run.forgotten, run.certificate)
        else:
            ok = (run.status == "halted" and run.steps == exp["steps"]
                  and run.out == tuple(exp["out"])
                  and run.exit_code == exp["exit"])
            got = (run.status, run.steps, run.out, run.exit_code)
        rows.append({"id": ident, "as_declared": ok, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "I2": wrong == 0 and len(rows) == 10}


def question_marks() -> Dict[str, object]:
    """I3: the questions asked of the battery."""
    rows: List[Dict[str, object]] = []
    for ident, question, check in QUESTIONS:
        a = bs.answer(question, "\n".join(_battery_lines(ident)), verify=False)
        if check[0] == "refused":
            ok = (not a.answered) and a.refusal == check[1]
        else:
            ok = (a.answered and a.value is False
                  and a.claim.get("kind") == "never_inert"
                  and a.claim.get("forgotten") == list(check[1])
                  and a.claim.get("certificate") == list(check[2]))
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "text": a.text, "refusal": a.refusal})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "questions": len(rows), "wrong": wrong,
            "I3": wrong == 0 and len(rows) == 9}


def certificate_marks() -> Dict[str, object]:
    """I4: the ``never_inert`` claims of I2 and I3, scripts and mutations."""
    claims: List[Tuple[Sequence[str], Dict[str, object]]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines))
        if run.status == "never" and run.forgotten:
            canon = [bm.render_line(i) for i in bm.parse_program(lines)]
            claims.append((canon, bs.never_claim(run)))
    for ident, question, check in QUESTIONS:
        if check[0] != "never":
            continue
        a = bs.answer(question, "\n".join(_battery_lines(ident)), verify=False)
        canon = [bm.render_line(i)
                 for i in bm.parse_program(_battery_lines(ident))]
        claims.append((canon, dict(a.claim)))
    scripts = verified = mutations = rejected = 0
    for canon, claim in claims:
        scripts += 1
        ok, _ = bs.run_script(bs.column3_script(canon, claim))
        verified += ok
        for mut in bs.mutations(claim, canon):
            mutations += 1
            good, _ = bs.run_script(bs.column3_script(canon, mut))
            rejected += not good
    return {"scripts": scripts, "verified": verified, "mutations": mutations,
            "rejected": rejected,
            "I4": scripts > 0 and verified == scripts and rejected == mutations}


def noninterference_marks() -> Dict[str, object]:
    """I5: Phase 125's battery, questions and English programs as declared
    (with M15 and Q6 moved to N1's answer), and every generated program
    Phase 125 decided keeps its verdict."""
    machine = op.machine_marks(scripts=False)
    english = op.english_marks()
    questions = op.question_marks(scripts=False)
    kept = changed = newly = still = 0
    moved: List[int] = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        old = bm.run_program(program, inert=False)
        new = bm.run_program(program)
        if old.status == "undecided":
            if new.status == "never":
                newly += 1
            else:
                still += 1
            continue
        same = (old.status, old.certificate, old.steps, old.out, old.err,
                old.exit_code, old.files) == (new.status, new.certificate,
                                              new.steps, new.out, new.err,
                                              new.exit_code, new.files)
        kept += same
        if not same:
            changed += 1
            moved.append(i)
    ok = (machine["wrong"] == 0 and machine["runs"] == 25
          and questions["wrong"] == 0 and questions["questions"] == 18
          and english["programs_as_declared"] == 6 and changed == 0)
    return {"machine_wrong": machine["wrong"], "runs": machine["runs"],
            "questions_wrong": questions["wrong"],
            "questions": questions["questions"],
            "english": english["programs_as_declared"],
            "generated_kept": kept, "generated_changed": changed,
            "generated_moved": tuple(moved),
            "generated_newly_certified": newly,
            "generated_still_undecided": still, "I5": ok}


def soundness_marks() -> Dict[str, object]:
    """I6: no certified program halts within :data:`LONG_BUDGET` steps when
    run without the rule; N3 halts there and is refused by the rule."""
    certified: List[Tuple[str, Tuple]] = []
    for ident, lines, _ in BATTERY:
        program = bm.parse_program(lines)
        run = bm.run_program(program)
        if run.status == "never" and run.forgotten:
            certified.append((ident, program))
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        run = bm.run_program(program)
        if run.status == "never" and run.forgotten:
            certified.append((f"G{i}", program))
    halted = [ident for ident, program in certified
              if bm.run_program(program, budget=LONG_BUDGET,
                                inert=False).halted]
    n3 = bm.parse_program(_battery_lines("N3"))
    long_run = bm.run_program(n3, budget=LONG_BUDGET, inert=False)
    short = bm.run_program(n3)
    n3_ok = (long_run.halted and long_run.steps == 40003
             and short.status == "undecided")
    return {"certified": tuple(i for i, _ in certified),
            "halted_within_long_budget": tuple(halted),
            "n3_steps": long_run.steps, "n3_refused": short.status
            == "undecided", "I6": not halted and n3_ok}


def inert_counter_report() -> Dict[str, object]:
    """Every mark the module takes, with its figures."""
    battery = battery_marks()
    questions = question_marks()
    cert = certificate_marks()
    ni = noninterference_marks()
    sound = soundness_marks()
    marks = {"I2": battery["I2"], "I3": questions["I3"], "I4": cert["I4"],
             "I5": ni["I5"], "I6": sound["I6"]}
    return {"battery": battery, "questions": questions, "certificates": cert,
            "noninterference": ni, "soundness": sound, "marks": marks,
            "study": "studies/INERT_COUNTER_STUDY.md", "lean_file": LEAN_FILE}
