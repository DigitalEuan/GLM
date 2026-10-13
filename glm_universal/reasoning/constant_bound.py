"""``glm_universal.reasoning.constant_bound`` -- constant bounds and repeated
output: two more counter lassos for GLM-BAT (Phase 131).

``studies/CONSTANT_BOUND_STUDY.md`` pre-registered the rule, a ten-program
battery and seven marks.  The rule itself lives in the machine
(:func:`batch_machine.jumped_run` with ``extended=True``: a comparison with a
non-counter bound read as a literal at its step, and a writing pass jumped
with its blocks repeated); the answers and the column-3 checker live in
:mod:`batch_speech`.  This module holds the battery and takes the marks:

* B2 -- the battery K1 ... K10 as declared;
* B3 -- the questions asked of it;
* B4 -- every ``run_jump`` and ``never_lasso`` claim's column-3 script
  passes, every mutation fails;
* B5 -- the Phase 125, 126 and 130 batteries and questions keep the answers
  Phase 130's reading gives (N2, N3, L10 and L11 apart), and every generated
  program keeps its verdict and its outputs;
* B6 -- every *halts* the extended reading gives agrees with a plain run of up
  to 2,500,000 steps, and no *never* it gives halts within 200,000 plain
  steps;
* B1 and B7 are pinned by the build, the tests and the evaluation.

Every run here is read with ``affine=False``: the module measures the Phase
131 rule it declared, without Phase 132's passes that write a counter
(``studies/AFFINE_OUTPUT_STUDY.md``).

``RequestProject/GLM/ConstantBound.lean`` is why a jump over a writing pass,
and a comparison with a constant bound, are proofs.

Exact and deterministic: no randomness, no floating point.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from . import batch_machine as bm
from . import batch_speech as bs
from . import counter_lasso as cl
from . import inert_counter as ic
from . import operations as op

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BATTERY", "QUESTIONS", "battery_marks",
    "question_marks", "certificate_marks", "noninterference_marks",
    "soundness_marks", "constant_bound_report",
]

LEAN_FILE = "RequestProject/GLM/ConstantBound.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "wrun_fst", "wrun_add", "wrun_pass", "lasso_output",
    "halts_of_jump_output", "shift_fst", "testC_equivariant",
    "const_bound_linear", "const_bound_linear'")

_MISSING = "The system cannot find the file specified."


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.split(" / "))


#: The battery of section 3, with the verdicts declared before the code.
BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("K1", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / "
                  "IF %N% LSS 20000 GOTO UP"),
     {"status": "halted", "steps": 60002, "out": ("tick",) * 20000,
      "exit": 0, "values": {"N": "20000"}, "jumps": ((2, 5, 19999),)}),
    ("K2", _lines("SET /A N=0 / SET L=20000 / :UP / SET /A N=N+1 / "
                  "IF %N% LSS %L% GOTO UP"),
     {"status": "halted", "steps": 40003, "out": (), "exit": 0,
      "values": {"N": "20000"}, "jumps": ((3, 5, 19999),)}),
    ("K3", _lines("SET /A N=0 / SET LIM=50000 / :UP / ECHO tick / "
                  "SET /A N=N+1 / IF %N% LSS %LIM% GOTO UP / ECHO %N%"),
     {"status": "halted", "steps": 150004,
      "out": ("tick",) * 50000 + ("50000",), "exit": 0,
      "jumps": ((3, 6, 49999),)}),
    ("K4", _lines("SET /A N=0 / SET LIM=500000 / :UP / ECHO tick / "
                  "SET /A N=N+1 / IF %N% LSS %LIM% GOTO UP / ECHO %N%"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("K5", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / "
                  "IF %N% LSS 20000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("K6", _lines("SET /A N=0 / SET L=7 / :UP / SET L=30000 / "
                  "SET /A N=N+1 / IF %N% LSS %L% GOTO UP / ECHO %N%"),
     {"status": "halted", "steps": 90004, "out": ("30000",), "exit": 0,
      "values": {"N": "30000"}, "jumps": ((6, 9, 29998),)}),
    ("K7", _lines("SET /A N=0 / SET L=-5 / :UP / SET /A N=N+1 / "
                  "IF %N% GTR %L% GOTO UP / ECHO unreachable"),
     {"status": "never", "certificate": (3, 5), "d": (("N", 1),)}),
    ("K8", _lines("SET /A N=0 / SET L=abc / :UP / SET /A N=N+1 / "
                  "IF %N% LSS %L% GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("K9", _lines("SET /A N=40000 / SET L=0 / :DOWN / ECHO %L% / "
                  "SET /A N=N-1 / IF %L% LSS %N% GOTO DOWN / ECHO lift-off"),
     {"status": "halted", "steps": 120004,
      "out": ("0",) * 40000 + ("lift-off",), "exit": 0,
      "jumps": ((3, 6, 39999),)}),
    ("K10", _lines("SET /A N=0 / :UP / SET /A N=N+1 / TYPE missing.txt / "
                   "IF %N% LSS 30000 GOTO UP"),
     {"status": "halted", "steps": 90002, "out": (),
      "err": (_MISSING,) * 30000, "exit": 1, "jumps": ((5, 8, 29998),)}),
)

#: The questions of mark B3: (program, question, expected).  ``("halts",
#: steps, exit)``, ``("never",)``, ``("refused", name)``, ``("value", v)``,
#: ``("print", value, phrase)``.
QUESTIONS: Tuple[Tuple[str, str, Tuple], ...] = tuple(
    (ident, "does it halt?",
     ("halts", exp["steps"], exp["exit"]) if exp.get("status") == "halted"
     else ("never",) if exp.get("status") == "never"
     else ("refused", exp["refusal"]))
    for ident, _lines_, exp in BATTERY) + (
    ("K3", "what does it print?",
     ("print", ["tick"] * 50000 + ["50000"], '"tick" (50000 times)')),
    ("K9", "how many steps?", ("value", 120004)),
    ("K10", "what is the exit code?", ("value", 1)),
    ("K6", "what is the value of N?", ("value", "30000")),
    ("K7", "what does it print?", ("refused", "NEVER_HALTS")),
)

#: The refused controls B6 reports with their plain outcome.
CONTROLS: Tuple[str, ...] = ("K4", "K5", "K8")


def _battery_lines(ident: str) -> Tuple[str, ...]:
    return next(lines for i, lines, _ in BATTERY if i == ident)


def _program_text(ident: str) -> str:
    return "\n".join(_battery_lines(ident))


def battery_marks() -> Dict[str, object]:
    """B2: each battery program as declared.  A row also says whether the
    program is as declared apart from its jumps (``as_declared_but_jumps``):
    which pass is jumped is the one figure of a halting run that the end of
    the run does not fix."""
    rows: List[Dict[str, object]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines), affine=False)
        jumps = tuple(j[:3] for j in run.jumps)
        if "refusal" in exp:
            ok = end = run.status == "undecided"
            got: object = run.status
        elif exp["status"] == "never":
            ok = end = (run.status == "never"
                        and run.certificate == tuple(exp["certificate"])
                        and run.lasso == tuple(exp["d"]))
            got = (run.status, run.certificate, run.lasso)
        else:
            end = (run.status == "halted" and run.steps == exp["steps"]
                   and run.out == tuple(exp["out"])
                   and ("err" not in exp or run.err == tuple(exp["err"]))
                   and run.exit_code == exp["exit"]
                   and all(run.env.get(k) == v
                           for k, v in exp.get("values", {}).items()))
            ok = end and jumps == tuple(exp["jumps"])
            got = (run.status, run.steps, len(run.out), len(run.err),
                   run.exit_code, jumps)
        rows.append({"id": ident, "as_declared": ok,
                     "as_declared_but_jumps": end, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    wrong_end = sum(not r["as_declared_but_jumps"] for r in rows)
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "wrong_apart_from_jumps": wrong_end,
            "jumps_differ": tuple(r["id"] for r in rows
                                  if r["as_declared_but_jumps"]
                                  and not r["as_declared"]),
            "B2": wrong == 0 and len(rows) == 10}


def question_marks() -> Dict[str, object]:
    """B3: the questions asked of the battery."""
    rows: List[Dict[str, object]] = []
    for ident, question, check in QUESTIONS:
        a = bs.answer(question, _program_text(ident), verify=False,
                      affine=False)
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
        elif check[0] == "print":
            ok = (a.answered and a.value == check[1] and check[2] in a.text
                  and a.claim.get("kind") == "run_jump")
        else:
            ok = a.answered and a.value == check[1] \
                and a.claim.get("kind") == "run_jump"
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "text": a.text[:300], "refusal": a.refusal})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "questions": len(rows), "wrong": wrong,
            "B3": wrong == 0 and len(rows) == 15}


def certificate_marks() -> Dict[str, object]:
    """B4: the ``run_jump`` and ``never_lasso`` claims of B2 and B3, their
    scripts and their mutations."""
    claims: List[Tuple[Sequence[str], Dict[str, object]]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        canon = [bm.render_line(i) for i in program]
        run = bm.run_program(program, affine=False)
        if run.status == "never" and run.lasso:
            claims.append((canon, bs.never_claim(run)))
        elif run.status == "halted" and run.jumps:
            claims.append((canon, bs._run_claim(run, {})))
    for ident, question, check in QUESTIONS:
        if check[0] == "refused":
            continue
        a = bs.answer(question, _program_text(ident), verify=False,
                      affine=False)
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
            "B4": scripts > 0 and verified == scripts and rejected == mutations}


def _same_run(old: bm.Run, new: bm.Run) -> bool:
    return (old.status, old.certificate, old.lasso, old.forgotten, old.steps,
            old.out, old.err, old.exit_code,
            tuple(j[:3] for j in old.jumps)) == (
        new.status, new.certificate, new.lasso, new.forgotten, new.steps,
        new.out, new.err, new.exit_code, tuple(j[:3] for j in new.jumps))


def noninterference_marks() -> Dict[str, object]:
    """B5: Phase 125's battery, questions and English programs as declared;
    Phases 126 and 130's batteries and questions as Phase 130's reading gives
    them, N2, N3, L10 and L11 apart; L10 and L11 as K1 and K2; and every
    generated program keeps its verdict and outputs."""
    machine = op.machine_marks(scripts=False)
    english = op.english_marks()
    questions = op.question_marks(scripts=False)
    batteries = (("126", ic.BATTERY, ic.QUESTIONS, ("N2", "N3")),
                 ("130", cl.BATTERY, cl.QUESTIONS, ("L10", "L11")))
    kept = total = q_kept = q_total = 0
    moved_rows: List[str] = []
    for _name, battery, qs, skip in batteries:
        texts = {i: "\n".join(lines) for i, lines, _ in battery}
        for ident, lines, _exp in battery:
            if ident in skip:
                continue
            total += 1
            old = bm.run_program(bm.parse_program(lines), extended=False)
            new = bm.run_program(bm.parse_program(lines), affine=False)
            same = _same_run(old, new)
            kept += same
            if not same:
                moved_rows.append(ident)
        for ident, question, _check in qs:
            if ident in skip:
                continue
            q_total += 1
            old = bs.answer(question, texts[ident], verify=False,
                            extended=False)
            new = bs.answer(question, texts[ident], verify=False,
                      affine=False)
            same = (old.answered, old.text, old.refusal, old.claim) == (
                new.answered, new.text, new.refusal, new.claim)
            q_kept += same
            if not same:
                moved_rows.append(f"{ident}: {question}")
    # L10 and L11 are K1 and K2.
    as_k = all(
        _same_run(bm.run_program(bm.parse_program(cl._battery_lines(lid)),
                                 affine=False),
                  bm.run_program(bm.parse_program(_battery_lines(kid)),
                                 affine=False))
        for lid, kid in (("L10", "K1"), ("L11", "K2")))
    gkept = gchanged = gjumps = 0
    gmoved: List[int] = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        old = bm.run_program(program, extended=False)
        new = bm.run_program(program, affine=False)
        same = (old.status, old.certificate, old.lasso, old.forgotten,
                old.steps, old.out, old.err, old.exit_code, old.files) == (
            new.status, new.certificate, new.lasso, new.forgotten, new.steps,
            new.out, new.err, new.exit_code, new.files)
        gkept += same
        if not same:
            gchanged += 1
            gmoved.append(i)
        elif tuple(j[:3] for j in old.jumps) != tuple(j[:3] for j in new.jumps):
            gjumps += 1
    ok = (machine["wrong"] == 0 and machine["runs"] == 25
          and questions["wrong"] == 0 and questions["questions"] == 18
          and english["programs_as_declared"] == 6
          and kept == total and q_kept == q_total and as_k
          and gchanged == 0)
    return {"machine_wrong": machine["wrong"], "runs": machine["runs"],
            "questions_wrong": questions["wrong"],
            "questions": questions["questions"],
            "english": english["programs_as_declared"],
            "battery_kept": kept, "battery_total": total,
            "questions_kept": q_kept, "questions_total": q_total,
            "moved": tuple(moved_rows), "l10_l11_as_k1_k2": as_k,
            "generated_kept": gkept, "generated_changed": gchanged,
            "generated_moved": tuple(gmoved),
            "generated_new_jumps": gjumps, "B5": ok}


def soundness_marks() -> Dict[str, object]:
    """B6: every *halts* by a jump agrees with a plain run under
    ``counter_lasso.LONG_BUDGET``; no *never* by a lasso halts within
    ``counter_lasso.NEVER_BUDGET`` plain steps; the refused controls are
    reported with their plain outcome."""
    decided: List[Tuple[str, Sequence[object], bm.Run]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        decided.append((ident, program,
                        bm.run_program(program, affine=False)))
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        run = bm.run_program(program, affine=False)
        if run.jumps or run.lasso:
            decided.append((f"G{i}", program, run))
    halts_ok: List[str] = []
    halts_bad: List[str] = []
    never_ok: List[str] = []
    never_bad: List[str] = []
    for ident, program, run in decided:
        if run.status == "halted" and run.jumps:
            plain = bm.plain_run(program, budget=cl.LONG_BUDGET)
            same = (plain.status == "halted" and plain.steps == run.steps
                    and plain.out == run.out and plain.err == run.err
                    and plain.files == run.files
                    and plain.exit_code == run.exit_code
                    and plain.env == run.env)
            (halts_ok if same else halts_bad).append(ident)
        elif run.status == "never" and run.lasso:
            plain = bm.plain_run(program, budget=cl.NEVER_BUDGET)
            (never_ok if not plain.halted else never_bad).append(ident)
    controls = {}
    for ident in CONTROLS:
        plain = bm.plain_run(bm.parse_program(_battery_lines(ident)),
                             budget=cl.LONG_BUDGET)
        controls[ident] = (plain.status, plain.steps)
    expected = {"K4": ("halted", 1500004), "K5": ("halted", 60002),
                "K8": ("undecided", cl.LONG_BUDGET)}
    ok = (not halts_bad and not never_bad and bool(halts_ok)
          and bool(never_ok) and controls == expected)
    return {"halts_agree": tuple(halts_ok), "halts_disagree": tuple(halts_bad),
            "never_hold": tuple(never_ok), "never_halt": tuple(never_bad),
            "controls": controls, "B6": ok}


def constant_bound_report() -> Dict[str, object]:
    """Every mark the module takes, with its figures."""
    battery = battery_marks()
    questions = question_marks()
    cert = certificate_marks()
    ni = noninterference_marks()
    sound = soundness_marks()
    marks = {"B2": battery["B2"], "B3": questions["B3"], "B4": cert["B4"],
             "B5": ni["B5"], "B6": sound["B6"]}
    return {"battery": battery, "questions": questions, "certificates": cert,
            "noninterference": ni, "soundness": sound, "marks": marks,
            "study": "studies/CONSTANT_BOUND_STUDY.md", "lean_file": LEAN_FILE}
