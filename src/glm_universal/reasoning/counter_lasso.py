"""``glm_universal.reasoning.counter_lasso`` -- counter lassos: halting and
non-termination for GLM-BAT past the budget (Phase 130).

``studies/COUNTER_LASSO_STUDY.md`` pre-registered the rule, a twelve-program
battery and seven marks.  The rule itself lives in the machine
(:func:`batch_machine.counters`, :func:`batch_machine.jumped_run`, the third
reading in :func:`batch_machine.run_program`); the answers and the
``run_jump`` and ``never_lasso`` column-3 claims live in :mod:`batch_speech`.
This module holds the battery and takes the marks:

* C2 -- the battery L1 ... L12 as declared;
* C3 -- the questions asked of it;
* C4 -- every ``run_jump`` and ``never_lasso`` claim's column-3 script
  passes, every mutation fails;
* C5 -- the Phase 125 and Phase 126 batteries and questions keep their
  answers, N2 and N3 apart, and every generated program Phase 125 or 126
  decided keeps its verdict;
* C6 -- every *halts* the rule gives agrees with a plain run of up to
  2,500,000 steps, and no *never* it gives halts within 200,000 plain steps;
* C1 and C7 are pinned by the build, the tests and the evaluation.

``RequestProject/GLM/CounterLasso.lean`` is why a jump and a lasso are proofs.

Every run here is read with ``extended=False``: the module measures the Phase
130 rule as it was declared.  Phase 131's constant operands and writing
passes (which decide L10 and L11) are measured by :mod:`constant_bound`.

Exact and deterministic: no randomness, no floating point.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from . import batch_machine as bm
from . import batch_speech as bs
from . import inert_counter as ic
from . import operations as op

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BATTERY", "QUESTIONS", "LONG_BUDGET",
    "NEVER_BUDGET", "battery_marks", "question_marks", "certificate_marks",
    "noninterference_marks", "soundness_marks", "counter_lasso_report",
]

LEAN_FILE = "RequestProject/GLM/CounterLasso.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "lasso_iterate", "lasso_accelerate", "never_halts_of_lasso",
    "halts_of_jump", "indep_equivariant", "add_equivariant",
    "test_equivariant", "linear_neg_stable", "linear_nonneg_stable",
    "linear_zero_unique")
#: The plain budget every *halts* is re-run under (C6).
LONG_BUDGET = 2_500_000
#: The plain budget every *never* is run a further time under (C6).
NEVER_BUDGET = 200_000


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.split(" / "))


#: The battery of section 3, with the declared verdicts.
BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("L1", _lines("SET /A N=0 / :UP / SET /A N=N+1 / "
                  "IF %N% LSS 20000 GOTO UP / ECHO done"),
     {"status": "halted", "steps": 40003, "out": ("done",), "exit": 0,
      "values": {"N": "20000"}, "jumps": ((2, 4, 19999),)}),
    ("L2", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / GOTO UP"),
     {"status": "never", "certificate": (2, 5), "d": (("N", 1),)}),
    ("L3", _lines("SET /A N=1000000 / :LOOP / SET /A N=N-1 / "
                  "IF %N% GTR 0 GOTO LOOP / ECHO %N%"),
     {"status": "halted", "steps": 2000003, "out": ("0",), "exit": 0,
      "jumps": ((2, 4, 999999),)}),
    ("L4", _lines("SET /A I=0 / SET /A J=1000000 / :L / SET /A I=I+3 / "
                  "SET /A J=J+1 / IF %I% LSS %J% GOTO L / ECHO %I% %J%"),
     {"status": "halted", "steps": 1500004, "out": ("1500000 1500000",),
      "exit": 0, "jumps": ((3, 6, 499999),)}),
    ("L5", _lines("SET /A N=0 / :TOP / CALL :INC / IF %N% LSS 50000 GOTO TOP"
                  " / ECHO %N% / EXIT /B 0 / :INC / SET /A N=N+1 / "
                  "GOTO :EOF"),
     {"status": "halted", "steps": 200004, "out": ("50000",), "exit": 0,
      "jumps": ((2, 6, 49999),)}),
    ("L6", _lines("SET /A N=-7 / :UP / SET /A N=N+2 / IF %N% NEQ 0 GOTO UP"
                  " / ECHO never"),
     {"status": "never", "certificate": (2, 4), "d": (("N", 2),)}),
    ("L7", _lines("SET /A N=-200000 / :UP / SET /A N=N+2 / "
                  "IF %N% NEQ 0 GOTO UP / ECHO reached"),
     {"status": "halted", "steps": 200003, "out": ("reached",), "exit": 0,
      "jumps": ((2, 4, 99999),)}),
    ("L8", _lines("SET /A N=0 / :UP / SET /A N=N+1 / "
                  "IF %N% EQU 30000 EXIT 7 / GOTO UP"),
     {"status": "halted", "steps": 90001, "out": (), "exit": 7,
      "jumps": ((2, 5, 29999),)}),
    ("L9", _lines("SET /A N=0 / :UP / SET /A N=N+1 / SET /A N=N*1 / "
                  "IF %N% LSS 20000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("L10", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / "
                   "IF %N% LSS 20000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("L11", _lines("SET /A N=0 / SET L=20000 / :UP / SET /A N=N+1 / "
                   "IF %N% LSS %L% GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("L12", _lines("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / "
                   "SET /A B=B+A / IF %B% GTR -1 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
)

#: The questions of mark C3: (program, question, expected).  ``("halts",
#: steps, exit)``, ``("never",)``, ``("refused", name)``, ``("value", v)``.
QUESTIONS: Tuple[Tuple[str, str, Tuple], ...] = tuple(
    (ident, "does it halt?",
     ("halts", exp["steps"], exp["exit"]) if exp.get("status") == "halted"
     else ("never",) if exp.get("status") == "never"
     else ("refused", exp["refusal"]))
    for ident, _lines_, exp in BATTERY) + (
    ("L3", "how many steps?", ("value", 2000003)),
    ("L4", "what does it print?", ("value", ["1500000 1500000"])),
    ("L8", "what is the exit code?", ("value", 7)),
    ("L1", "what is the value of N?", ("value", "20000")),
    ("L2", "what does it print?", ("refused", "NEVER_HALTS")),
)


def _battery_lines(ident: str) -> Tuple[str, ...]:
    return next(lines for i, lines, _ in BATTERY if i == ident)


def _program_text(ident: str) -> str:
    return "\n".join(_battery_lines(ident))


def battery_marks() -> Dict[str, object]:
    """C2: each battery program as declared."""
    rows: List[Dict[str, object]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines), extended=False)
        jumps = tuple(j[:3] for j in run.jumps)
        if "refusal" in exp:
            ok = run.status == "undecided"
            got: object = run.status
        elif exp["status"] == "never":
            ok = (run.status == "never"
                  and run.certificate == tuple(exp["certificate"])
                  and run.lasso == tuple(exp["d"]))
            got = (run.status, run.certificate, run.lasso)
        else:
            ok = (run.status == "halted" and run.steps == exp["steps"]
                  and run.out == tuple(exp["out"])
                  and run.exit_code == exp["exit"]
                  and jumps == tuple(exp["jumps"])
                  and all(run.env.get(k) == v
                          for k, v in exp.get("values", {}).items()))
            got = (run.status, run.steps, run.out, run.exit_code, jumps)
        rows.append({"id": ident, "as_declared": ok, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "C2": wrong == 0 and len(rows) == 12}


def question_marks() -> Dict[str, object]:
    """C3: the questions asked of the battery."""
    rows: List[Dict[str, object]] = []
    for ident, question, check in QUESTIONS:
        a = bs.answer(question, _program_text(ident), verify=False,
                      extended=False)
        if check[0] == "refused":
            ok = (not a.answered) and a.refusal == check[1]
        elif check[0] == "never":
            ok = (a.answered and a.value is False
                  and a.claim.get("kind") == "never_lasso")
        elif check[0] == "halts":
            ok = (a.answered and a.value is True
                  and a.claim.get("kind") == "run_jump"
                  and a.claim.get("steps") == check[1]
                  and a.claim.get("exit") == check[2])
        else:
            ok = a.answered and a.value == check[1] \
                and a.claim.get("kind") == "run_jump"
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "text": a.text, "refusal": a.refusal})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "questions": len(rows), "wrong": wrong,
            "C3": wrong == 0 and len(rows) == 17}


def certificate_marks() -> Dict[str, object]:
    """C4: the ``run_jump`` and ``never_lasso`` claims of C2 and C3, their
    scripts and their mutations."""
    claims: List[Tuple[Sequence[str], Dict[str, object]]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        canon = [bm.render_line(i) for i in program]
        run = bm.run_program(program, extended=False)
        if run.status == "never" and run.lasso:
            claims.append((canon, bs.never_claim(run)))
        elif run.status == "halted" and run.jumps:
            claims.append((canon, bs._run_claim(run, {})))
    for ident, question, check in QUESTIONS:
        if check[0] == "refused":
            continue
        a = bs.answer(question, _program_text(ident), verify=False,
                      extended=False)
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
            "C4": scripts > 0 and verified == scripts and rejected == mutations}


def noninterference_marks() -> Dict[str, object]:
    """C5: Phase 125's battery, questions and English programs as declared;
    Phase 126's battery and questions as declared except N2 and N3; and every
    generated program Phase 125 or 126 decided keeps its verdict."""
    machine = op.machine_marks(scripts=False)
    english = op.english_marks()
    questions = op.question_marks(scripts=False)
    moved_ids = ("N2", "N3")
    inert_kept = inert_total = 0
    for ident, lines, exp in ic.BATTERY:
        if ident in moved_ids:
            continue
        inert_total += 1
        old = bm.run_program(bm.parse_program(lines), jump=False)
        new = bm.run_program(bm.parse_program(lines), extended=False)
        inert_kept += (old.status, old.certificate, old.forgotten, old.steps,
                       old.out, old.exit_code) == (
            new.status, new.certificate, new.forgotten, new.steps, new.out,
            new.exit_code)
    q_kept = q_total = 0
    for ident, question, _check in ic.QUESTIONS:
        if ident in moved_ids:
            continue
        q_total += 1
        text = "\n".join(next(l for i, l, _ in ic.BATTERY if i == ident))
        old = bs.answer(question, text, verify=False, jump=False)
        new = bs.answer(question, text, verify=False, extended=False)
        q_kept += (old.answered, old.text, old.refusal, old.claim) == (
            new.answered, new.text, new.refusal, new.claim)
    kept = changed = newly = still = 0
    moved: List[int] = []
    newly_ids: List[int] = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        old = bm.run_program(program, jump=False)
        new = bm.run_program(program, extended=False)
        if old.status == "undecided":
            if new.status != "undecided":
                newly += 1
                newly_ids.append(i)
            else:
                still += 1
            continue
        same = (old.status, old.certificate, old.forgotten, old.steps,
                old.out, old.err, old.exit_code, old.files) == (
            new.status, new.certificate, new.forgotten, new.steps, new.out,
            new.err, new.exit_code, new.files)
        kept += same
        if not same:
            changed += 1
            moved.append(i)
    ok = (machine["wrong"] == 0 and machine["runs"] == 25
          and questions["wrong"] == 0 and questions["questions"] == 18
          and english["programs_as_declared"] == 6
          and inert_kept == inert_total == 8 and q_kept == q_total == 7
          and changed == 0)
    return {"machine_wrong": machine["wrong"], "runs": machine["runs"],
            "questions_wrong": questions["wrong"],
            "questions": questions["questions"],
            "english": english["programs_as_declared"],
            "inert_kept": inert_kept, "inert_total": inert_total,
            "inert_questions_kept": q_kept, "inert_questions": q_total,
            "generated_kept": kept, "generated_changed": changed,
            "generated_moved": tuple(moved),
            "generated_newly_decided": newly,
            "generated_newly_decided_ids": tuple(newly_ids),
            "generated_still_undecided": still, "C5": ok}


def soundness_marks() -> Dict[str, object]:
    """C6: every *halts* by a jump agrees with a plain run under
    :data:`LONG_BUDGET`; no *never* by a lasso halts within
    :data:`NEVER_BUDGET` plain steps; the refused controls are reported with
    their plain outcome."""
    decided: List[Tuple[str, Sequence[object], bm.Run]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        decided.append((ident, program,
                        bm.run_program(program, extended=False)))
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        run = bm.run_program(program, extended=False)
        if run.jumps or run.lasso:
            decided.append((f"G{i}", program, run))
    halts_ok: List[str] = []
    halts_bad: List[str] = []
    never_ok: List[str] = []
    never_bad: List[str] = []
    for ident, program, run in decided:
        if run.status == "halted" and run.jumps:
            plain = bm.plain_run(program, budget=LONG_BUDGET)
            same = (plain.status == "halted" and plain.steps == run.steps
                    and plain.out == run.out and plain.err == run.err
                    and plain.files == run.files
                    and plain.exit_code == run.exit_code
                    and plain.env == run.env)
            (halts_ok if same else halts_bad).append(ident)
        elif run.status == "never" and run.lasso:
            plain = bm.plain_run(program, budget=NEVER_BUDGET)
            (never_ok if not plain.halted else never_bad).append(ident)
    controls = {}
    for ident in ("L9", "L10", "L11"):
        plain = bm.plain_run(bm.parse_program(_battery_lines(ident)),
                             budget=LONG_BUDGET)
        controls[ident] = (plain.status, plain.steps)
    ok = not halts_bad and not never_bad and bool(halts_ok) and bool(never_ok)
    return {"halts_agree": tuple(halts_ok), "halts_disagree": tuple(halts_bad),
            "never_hold": tuple(never_ok), "never_halt": tuple(never_bad),
            "controls": controls, "C6": ok}


def counter_lasso_report() -> Dict[str, object]:
    """Every mark the module takes, with its figures."""
    battery = battery_marks()
    questions = question_marks()
    cert = certificate_marks()
    ni = noninterference_marks()
    sound = soundness_marks()
    marks = {"C2": battery["C2"], "C3": questions["C3"], "C4": cert["C4"],
             "C5": ni["C5"], "C6": sound["C6"]}
    return {"battery": battery, "questions": questions, "certificates": cert,
            "noninterference": ni, "soundness": sound, "marks": marks,
            "study": "studies/COUNTER_LASSO_STUDY.md", "lean_file": LEAN_FILE}
