"""``glm_universal.reasoning.affine_output`` -- passes that print a counter,
long output, and the diagnosis of a refusal for GLM-BAT (Phase 132).

``studies/AFFINE_OUTPUT_STUDY.md`` pre-registered the rule, a ten-program
battery, an eight-program diagnosis battery and nine marks.  The rule lives in
the machine (:func:`batch_machine.jumped_run` with ``affine=True``: an
``ECHO`` naming a counter read as a template, and the output bound of
:data:`batch_machine.AFFINE_OUTPUT_CAP`; :func:`batch_machine.
growth_diagnosis`); the answers, the run form of a long claim and the column-3
checker live in :mod:`batch_speech`.  This module holds the batteries and
takes the marks:

* A2 -- the battery P1 ... P10 as declared;
* A3 -- the twenty questions asked of it and of the diagnosis battery;
* A4 -- every ``run_jump``, ``never_lasso`` and ``growth`` claim's column-3
  script passes and every mutation fails;
* A5 -- the diagnosis battery as declared, with the NRCI of a straight line
  through L12's ``B`` above 0.99 (reported, never used to decide);
* A6 -- the closed forms read from the window predict the next 32 visits;
* A7 -- the Phase 125, 126, 130 and 131 batteries and questions keep the
  answers Phase 131's reading gives (N2, N3, L10, L11, K4 and K5 apart), K4
  and K5 move to P2 and P1, and every generated program keeps its answers;
* A8 -- every *halts* the affine reading gives agrees with a plain run, and
  the refused controls are reported with their plain outcome;
* A1 and A9 are pinned by the build, the tests and the evaluation.

``RequestProject/GLM/AffineOutput.lean`` is why a jump over a pass that
writes a counter is a proof, and why the shapes the diagnosis names have the
closed forms it predicts with.

Exact and deterministic, with no float anywhere: the NRCI is held in
millionths from an integer square root of its exact rational squared form.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from . import batch_machine as bm
from . import batch_speech as bs
from . import constant_bound as cb
from . import counter_lasso as cl
from . import inert_counter as ic
from . import operations as op

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BATTERY", "DIAGNOSIS", "QUESTIONS",
    "battery_marks", "question_marks", "diagnosis_marks", "prediction_marks",
    "certificate_marks", "noninterference_marks", "soundness_marks",
    "affine_output_report",
]

LEAN_FILE = "RequestProject/GLM/AffineOutput.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "wrun_pass_shifted", "passOutput_succ", "lasso_output_affine",
    "halts_of_jump_affine", "render_hole", "render_append", "render_const",
    "templated_block", "const_diff_closed_form",
    "const_second_diff_closed_form", "const_ratio_closed_form",
    "quadratic_not_translation")

_MISSING = "The system cannot find the file specified."

#: The budget of the plain run P6 is reported under (mark A8).
P6_BUDGET = 4_000_000


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.split(" / "))


def _count(a: int, b: int) -> Tuple[str, ...]:
    step = 1 if b >= a else -1
    return tuple(str(n) for n in range(a, b + step, step))


#: The battery of section 3, with the verdicts declared before the code.
BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("P1", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / "
                  "IF %N% LSS 20000 GOTO UP"),
     {"status": "halted", "steps": 60002, "out": _count(1, 20000), "exit": 0,
      "values": {"N": "20000"}, "jumps": ((2, 5, 19999),)}),
    ("P2", _lines("SET /A N=0 / SET LIM=500000 / :UP / ECHO tick / "
                  "SET /A N=N+1 / IF %N% LSS %LIM% GOTO UP / ECHO %N%"),
     {"status": "halted", "steps": 1500004,
      "out": ("tick",) * 500000 + ("500000",), "exit": 0,
      "jumps": ((3, 6, 499999),), "runs": True}),
    ("P3", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / "
                  "ECHO N=%N% / IF %N% LSS 30000 GOTO UP"),
     {"status": "halted", "steps": 120002,
      "out": tuple(x for n in range(1, 30001) for x in ("tick", f"N={n}")),
      "exit": 0, "jumps": ((2, 6, 29999),)}),
    ("P4", _lines("SET /A N=10 / :DOWN / ECHO %N% / SET /A N=N-1 / "
                  "IF %N% GEQ -20000 GOTO DOWN"),
     {"status": "halted", "steps": 60035, "out": _count(10, -20000),
      "exit": 0, "values": {"N": "-20001"}, "jumps": ((2, 5, 20010),)}),
    ("P5", _lines("SET /A I=0 / SET /A J=100 / :L / SET /A I=I+1 / "
                  "SET /A J=J+3 / ECHO %I%:%J% / IF %I% LSS 10000 GOTO L"),
     {"status": "halted", "steps": 40003,
      "out": tuple(f"{i}:{100 + 3 * i}" for i in range(1, 10001)), "exit": 0,
      "jumps": ((3, 7, 9999),)}),
    ("P6", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / "
                  "IF %N% LSS 1200000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("P7", _lines("SET P=item / SET /A N=0 / :UP / SET /A N=N+1 / "
                  "ECHO %P% %N% / IF %N% LSS 25000 GOTO UP"),
     {"status": "halted", "steps": 75003,
      "out": tuple(f"item {n}" for n in range(1, 25001)), "exit": 0,
      "jumps": ((3, 6, 24999),)}),
    ("P8", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N%%N% / "
                  "IF %N% LSS 5000 GOTO UP"),
     {"status": "halted", "steps": 15002,
      "out": tuple(f"{n}{n}" for n in range(1, 5001)), "exit": 0,
      "jumps": ((2, 5, 4999),)}),
    ("P9", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / "
                  "TYPE missing.txt / IF %N% LSS 15000 GOTO UP"),
     {"status": "halted", "steps": 60002, "out": _count(1, 15000),
      "err": (_MISSING,) * 15000, "exit": 1, "jumps": ((5, 9, 14999),)}),
    ("P10", _lines("SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% > last.txt / "
                   "IF %N% LSS 20000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
)


def _battery_lines(ident: str) -> Tuple[str, ...]:
    for i, lines, _ in BATTERY:
        if i == ident:
            return lines
    for i, lines, _ in DIAGNOSIS:
        if i == ident:
            return lines
    raise KeyError(ident)


def _program_text(ident: str) -> str:
    return "\n".join(_battery_lines(ident))


#: The diagnosis battery of section 3: (program, lines, expected).
DIAGNOSIS: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("L12", cl._battery_lines("L12"),
     {"head": 4, "visits": 3333,
      "shapes": {"A": ("translation", 1), "B": ("quadratic", 1)},
      "files": (), "blocked": ("no_recurrence",)}),
    ("N5", next(lines for i, lines, _ in ic.BATTERY if i == "N5"),
     {"head": 3, "visits": 3333, "shapes": {"N": ("geometric", 2)},
      "files": (), "blocked": ("no_recurrence",)}),
    ("K8", cb._battery_lines("K8"),
     {"head": 4, "visits": 4999, "shapes": {"N": ("translation", 1)},
      "files": (), "blocked": ("line", 5)}),
    ("P6", BATTERY[5][1],
     {"head": 3, "visits": 3333, "shapes": {"N": ("translation", 1)},
      "files": (), "blocked": ("cap", bm.AFFINE_OUTPUT_CAP)}),
    ("P10", BATTERY[9][1],
     {"head": 3, "visits": 3333, "shapes": {"N": ("translation", 1)},
      "files": ("last.txt",), "blocked": ("no_recurrence",)}),
    ("G1", _lines("SET /A A=0 / SET /A B=1 / :UP / SET /A C=A+B / "
                  "SET /A A=B / SET /A B=C / IF %B% GTR -1 GOTO UP"),
     {"head": 4, "visits": 2500,
      "shapes": {"A": ("irregular", None), "B": ("irregular", None),
                 "C": ("irregular", None)},
      "files": (), "blocked": ("no_recurrence",)}),
    ("G2", _lines("SET /A N=1 / :UP / SET /A N=N*3 / IF %N% GTR 0 GOTO UP"),
     {"head": 3, "visits": 4999, "shapes": {"N": ("geometric", 3)},
      "files": (), "blocked": ("no_recurrence",)}),
    ("G3", _lines("SET /A N=0 / SET S=x / :UP / SET /A N=N+1 / "
                  "SET S=%S%x / IF %N% GTR 0 GOTO UP"),
     {"head": 4, "visits": 3333,
      "shapes": {"N": ("translation", 1), "S": ("text", None)},
      "files": (), "blocked": ("no_recurrence",)}),
)

_P8_TEXT = ('"11" … "99" (9 lines; the number steps by 11), "1010" … "9999" '
            '(90 lines; the number steps by 101), "100100" … "999999" (900 '
            'lines; the number steps by 1001), "10001000" … "50005000" (4001 '
            'lines; the number steps by 10001)')

#: The questions of mark A3: (program, question, expected).  ``("halts",
#: steps, exit)``, ``("refused", name)``, ``("value", v)``, ``("print",
#: value or None, phrase)``, ``("why", phrase)``.
QUESTIONS: Tuple[Tuple[str, str, Tuple], ...] = tuple(
    (ident, "does it halt?",
     ("halts", exp["steps"], exp["exit"]) if exp.get("status") == "halted"
     else ("refused", exp["refusal"]))
    for ident, _lines_, exp in BATTERY) + (
    ("P1", "what does it print?",
     ("print", list(_count(1, 20000)),
      '"1" … "20000" (20000 lines; the number steps by 1)')),
    ("P2", "what does it print?",
     ("print", None, '"tick" (500000 times), "500000"')),
    ("P8", "what does it print?", ("print", None, _P8_TEXT)),
    ("P4", "what is the value of N?", ("value", "-20001")),
    ("P5", "how many steps?", ("value", 40003)),
    ("P9", "what is the exit code?", ("value", 1)),
    ("L12", "why is it undecided?",
     ("why", "B grows quadratically (second difference 1)")),
    ("P6", "why is it undecided?", ("why", "would pass 1000000 lines")),
    ("G1", "why is it undecided?", ("why", "C changes irregularly")),
    ("P1", "why is it undecided?", ("refused", "NOT_UNDECIDED")),
)


def battery_marks() -> Dict[str, object]:
    """A2: each battery program as declared."""
    rows: List[Dict[str, object]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines))
        jumps = tuple(j[:3] for j in run.jumps)
        if "refusal" in exp:
            ok = run.status == "undecided"
            got: object = run.status
        else:
            ok = (run.status == "halted" and run.steps == exp["steps"]
                  and run.out == tuple(exp["out"])
                  and run.err == tuple(exp.get("err", ()))
                  and run.exit_code == exp["exit"]
                  and all(run.env.get(k) == v
                          for k, v in exp.get("values", {}).items())
                  and jumps == tuple(exp["jumps"]))
            got = (run.status, run.steps, len(run.out), len(run.err),
                   run.exit_code, jumps)
        rows.append({"id": ident, "as_declared": ok, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "A2": wrong == 0 and len(rows) == 10}


def question_marks() -> Dict[str, object]:
    """A3: the twenty questions."""
    rows: List[Dict[str, object]] = []
    for ident, question, check in QUESTIONS:
        a = bs.answer(question, _program_text(ident), verify=False)
        if check[0] == "refused":
            ok = (not a.answered) and a.refusal == check[1]
        elif check[0] == "halts":
            ok = (a.answered and a.value is True
                  and a.claim.get("kind") == "run_jump"
                  and a.claim.get("steps") == check[1]
                  and a.claim.get("exit") == check[2])
        elif check[0] == "print":
            ok = (a.answered and check[2] in a.text
                  and (check[1] is None or a.value == check[1])
                  and a.claim.get("kind") == "run_jump")
        elif check[0] == "why":
            ok = (a.answered and check[1] in a.text
                  and a.claim.get("kind") == "growth")
        else:
            ok = a.answered and a.value == check[1] \
                and a.claim.get("kind") == "run_jump"
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "text": a.text[:600], "refusal": a.refusal})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "questions": len(rows), "wrong": wrong,
            "missed": tuple(f"{r['id']}: {r['question']}" for r in rows
                            if not r["as_declared"]),
            "A3": wrong == 0 and len(rows) == 20}


def _diagnose(lines: Sequence[str]) -> Dict[str, object]:
    return bm.growth_diagnosis(bm.parse_program(lines))


def diagnosis_marks() -> Dict[str, object]:
    """A5: the diagnosis battery as declared, and the NRCI of every variable
    that is not a translation (reported; L12's ``B`` is declared above
    0.99)."""
    rows: List[Dict[str, object]] = []
    nrci: Dict[str, str] = {}
    micro: Dict[str, int] = {}
    for ident, lines, exp in DIAGNOSIS:
        diag = _diagnose(lines)
        got = {"head": diag["head"], "visits": diag["visits"],
               "shapes": dict(diag["shapes"]), "files": tuple(diag["files"]),
               "blocked": tuple(diag["blocked"])}
        ok = got == {k: (dict(v) if k == "shapes" else v)
                     for k, v in exp.items()}
        for name, value in sorted(diag["nrci"].items()):
            if value is not None:
                nrci[f"{ident}.{name}"] = bm.nrci_decimal(value[1])
                micro[f"{ident}.{name}"] = value[1]
        rows.append({"id": ident, "as_declared": ok, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    l12_b = micro.get("L12.B")
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "nrci": nrci, "nrci_micro": micro, "l12_b_nrci": nrci.get("L12.B"),
            "A5": wrong == 0 and len(rows) == 8 and l12_b is not None
            and l12_b > 990_000}


def _head_values(program: Sequence[object], head: int, name: str,
                 visits: int) -> List[int]:
    """``name`` at the first ``visits`` visits of line ``head`` in a plain
    run."""
    ctx = bm._Ctx({}, {}, ())
    labels = bm._labels(program)
    pc, stack = 0, ()
    out: List[int] = []
    while len(out) < visits and pc < len(program):
        if pc == head - 1:
            out.append(int(ctx.env[name]))
        pc, stack, code = bm._exec_step(program, labels, ctx, pc, stack)
        if code is not None:
            break
    return out


def prediction_marks(ahead: int = bm.GROWTH_WINDOW) -> Dict[str, object]:
    """A6: for every ``translation``, ``quadratic`` and ``geometric``
    variable of the diagnosis battery, the closed form read from the window
    gives its value at each of the next ``ahead`` visits."""
    rows: List[Dict[str, object]] = []
    for ident, lines, _exp in DIAGNOSIS:
        program = bm.parse_program(lines)
        diag = bm.growth_diagnosis(program)
        for name, shape in sorted(diag["shapes"].items()):
            if shape[0] not in ("translation", "quadratic", "geometric"):
                continue
            n = diag["visits"]
            series = _head_values(program, diag["head"], name, n + ahead)
            window = series[n - diag["window"]:n]
            ok = (tuple(window) == diag["series"][name]
                  and bm.predict(shape, window, ahead) == series[n:n + ahead])
            rows.append({"id": f"{ident}.{name}", "shape": shape,
                         "holds": ok})
    held = sum(r["holds"] for r in rows)
    return {"rows": tuple(rows), "variables": len(rows), "held": held,
            "A6": bool(rows) and held == len(rows)}


def _undecided_generated() -> List[Tuple[int, Sequence[object]]]:
    out = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        if bm.run_program(program).status == "undecided":
            out.append((i, program))
    return out


def certificate_marks() -> Dict[str, object]:
    """A4: the claims of A2, A3 and A5 -- and the ``growth`` claim of every
    undecided generated program -- their scripts and their mutations."""
    claims: List[Tuple[str, Sequence[str], Dict[str, object]]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        canon = [bm.render_line(i) for i in program]
        run = bm.run_program(program)
        if run.status == "never" and run.lasso:
            claims.append((ident, canon, bs.never_claim(run)))
        elif run.status == "halted" and run.jumps:
            claims.append((ident, canon, bs._run_claim(run, {})))
    for ident, question, check in QUESTIONS:
        if check[0] == "refused":
            continue
        a = bs.answer(question, _program_text(ident), verify=False)
        canon = [bm.render_line(i)
                 for i in bm.parse_program(_battery_lines(ident))]
        if a.claim:
            claims.append((ident, canon, dict(a.claim)))
    for ident, lines, _exp in DIAGNOSIS:
        program = bm.parse_program(lines)
        diag = bm.growth_diagnosis(program)
        claims.append((ident, [bm.render_line(i) for i in program],
                       bs.growth_claim(diag)))
    generated = _undecided_generated()
    for i, program in generated:
        diag = bm.growth_diagnosis(program)
        if diag["head"] is not None:
            claims.append((f"G{i}", [bm.render_line(x) for x in program],
                           bs.growth_claim(diag)))
    scripts = verified = mutations = rejected = 0
    failed: List[str] = []
    p2_bytes = p2_claim = None
    for ident, canon, claim in claims:
        scripts += 1
        script = bs.column3_script(canon, claim)
        if ident == "P2" and claim.get("kind") == "run_jump":
            p2_bytes = len(script.encode("utf-8"))
            p2_claim = len(repr(bs._plain(claim)).encode("utf-8"))
        ok, _ = bs.run_script(script)
        verified += ok
        if not ok:
            failed.append(ident)
        for mut in bs.mutations(claim, canon):
            mutations += 1
            good, _ = bs.run_script(bs.column3_script(canon, mut))
            rejected += not good
    return {"scripts": scripts, "verified": verified, "failed": tuple(failed),
            "mutations": mutations, "rejected": rejected,
            "undecided_generated": len(generated), "p2_script_bytes": p2_bytes,
            "p2_claim_bytes": p2_claim,
            "checker_bytes": len(bs.CHECKER.encode("utf-8")),
            "A4": (scripts > 0 and verified == scripts
                   and rejected == mutations and p2_bytes is not None
                   and p2_bytes < 10_000)}


def _same_run(old: bm.Run, new: bm.Run) -> bool:
    return (old.status, old.certificate, old.lasso, old.forgotten, old.steps,
            old.out, old.err, old.exit_code,
            tuple(j[:3] for j in old.jumps)) == (
        new.status, new.certificate, new.lasso, new.forgotten, new.steps,
        new.out, new.err, new.exit_code, tuple(j[:3] for j in new.jumps))


def noninterference_marks() -> Dict[str, object]:
    """A7: Phase 125's battery, questions and English programs as declared;
    the Phase 126, 130 and 131 batteries and questions as Phase 131's reading
    gives them, N2, N3, L10, L11, K4 and K5 apart; K4 and K5 as P2 and P1;
    and every generated program keeps its answers."""
    machine = op.machine_marks(scripts=False)
    english = op.english_marks()
    questions = op.question_marks(scripts=False)
    batteries = (("126", ic.BATTERY, ic.QUESTIONS, ("N2", "N3")),
                 ("130", cl.BATTERY, cl.QUESTIONS, ("L10", "L11")),
                 ("131", cb.BATTERY, cb.QUESTIONS, ("K4", "K5")))
    kept = total = q_kept = q_total = 0
    moved_rows: List[str] = []
    for _name, battery, qs, skip in batteries:
        texts = {i: "\n".join(lines) for i, lines, _ in battery}
        for ident, lines, _exp in battery:
            if ident in skip:
                continue
            total += 1
            old = bm.run_program(bm.parse_program(lines), affine=False)
            new = bm.run_program(bm.parse_program(lines))
            same = _same_run(old, new)
            kept += same
            if not same:
                moved_rows.append(ident)
        for ident, question, _check in qs:
            if ident in skip:
                continue
            q_total += 1
            old = bs.answer(question, texts[ident], verify=False,
                            affine=False)
            new = bs.answer(question, texts[ident], verify=False)
            same = (old.answered, old.text, old.refusal, old.claim) == (
                new.answered, new.text, new.refusal, new.claim)
            q_kept += same
            if not same:
                moved_rows.append(f"{ident}: {question}")
    as_p = all(
        _same_run(bm.run_program(bm.parse_program(cb._battery_lines(kid))),
                  bm.run_program(bm.parse_program(_battery_lines(pid))))
        for kid, pid in (("K4", "P2"), ("K5", "P1")))
    gkept = gjumps = 0
    gmoved: List[int] = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        old = bm.run_program(program, affine=False)
        new = bm.run_program(program)
        same = (old.status, old.certificate, old.lasso, old.forgotten,
                old.steps, old.out, old.err, old.exit_code, old.files) == (
            new.status, new.certificate, new.lasso, new.forgotten, new.steps,
            new.out, new.err, new.exit_code, new.files)
        gkept += same
        if not same:
            gmoved.append(i)
        elif tuple(j[:3] for j in old.jumps) != tuple(j[:3] for j in new.jumps):
            gjumps += 1
    ok = (machine["wrong"] == 0 and machine["runs"] == 25
          and questions["wrong"] == 0 and questions["questions"] == 18
          and english["programs_as_declared"] == 6
          and kept == total and q_kept == q_total and as_p
          and not gmoved)
    return {"machine_wrong": machine["wrong"], "runs": machine["runs"],
            "questions_wrong": questions["wrong"],
            "questions": questions["questions"],
            "english": english["programs_as_declared"],
            "battery_kept": kept, "battery_total": total,
            "questions_kept": q_kept, "questions_total": q_total,
            "moved": tuple(moved_rows), "k4_k5_as_p2_p1": as_p,
            "generated_kept": gkept, "generated_moved": tuple(gmoved),
            "generated_new_jumps": gjumps, "A7": ok}


def soundness_marks() -> Dict[str, object]:
    """A8: every *halts* by the affine reading agrees with a plain run under
    ``counter_lasso.LONG_BUDGET``; the refused controls are reported with
    their plain outcome."""
    decided: List[Tuple[str, Sequence[object], bm.Run]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        decided.append((ident, program, bm.run_program(program)))
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        run = bm.run_program(program)
        if run.jumps:
            decided.append((f"G{i}", program, run))
    halts_ok: List[str] = []
    halts_bad: List[str] = []
    for ident, program, run in decided:
        if run.status == "halted" and run.jumps:
            plain = bm.plain_run(program, budget=cl.LONG_BUDGET)
            same = (plain.status == "halted" and plain.steps == run.steps
                    and plain.out == run.out and plain.err == run.err
                    and plain.files == run.files
                    and plain.exit_code == run.exit_code
                    and plain.env == run.env)
            (halts_ok if same else halts_bad).append(ident)
    p6 = bm.plain_run(bm.parse_program(_battery_lines("P6")),
                      budget=P6_BUDGET)
    p10 = bm.plain_run(bm.parse_program(_battery_lines("P10")),
                       budget=cl.LONG_BUDGET)
    controls = {"P6": (p6.status, p6.steps),
                "P10": (p10.status, p10.steps,
                        p10.files.get("last.txt"))}
    expected = {"P6": ("halted", 3600002),
                "P10": ("halted", 60002, ("20000",))}
    ok = not halts_bad and bool(halts_ok) and controls == expected
    return {"halts_agree": tuple(halts_ok), "halts_disagree": tuple(halts_bad),
            "controls": controls, "A8": ok}


def affine_output_report() -> Dict[str, object]:
    """Every mark the module takes, with its figures."""
    battery = battery_marks()
    questions = question_marks()
    diagnosis = diagnosis_marks()
    prediction = prediction_marks()
    cert = certificate_marks()
    ni = noninterference_marks()
    sound = soundness_marks()
    marks = {"A2": battery["A2"], "A3": questions["A3"], "A4": cert["A4"],
             "A5": diagnosis["A5"], "A6": prediction["A6"], "A7": ni["A7"],
             "A8": sound["A8"]}
    return {"battery": battery, "questions": questions,
            "diagnosis": diagnosis, "prediction": prediction,
            "certificates": cert, "noninterference": ni, "soundness": sound,
            "marks": marks, "study": "studies/AFFINE_OUTPUT_STUDY.md",
            "lean_file": LEAN_FILE}
