"""``glm_universal.reasoning.quadratic_lasso`` -- jumping a pass whose step
grows: accumulators and the first change of a quadratic comparison for GLM-BAT
(Phase 142).

``studies/QUADRATIC_LASSO_STUDY.md`` pre-registered the rule, a twelve-program
battery, twenty questions and eight marks.  The rule lives in the machine
(:func:`batch_machine.jumped_run` with ``quadratic=True``,
:func:`batch_machine.accumulators`, :func:`batch_machine.
first_change_quadratic`); the answers and the column-3 checker live in
:mod:`batch_speech`.  This module holds the battery and takes the marks:

* Q2 -- the battery Q1 ... Q12 as declared;
* Q3 -- the twenty questions;
* Q4 -- every ``run_jump`` and ``never_lasso`` claim's column-3 script passes
  and every mutation fails;
* Q5 -- the Phase 125, 126, 130, 131 and 132 batteries and questions keep the
  answers Phase 132's reading gives (L12 and N6 apart), and every generated
  program keeps its answers;
* Q6 -- every jumped *halts* agrees with a plain run, and no new *never* is
  contradicted by one;
* Q7 -- the first change agrees with a brute-force scan, and the column-3
  route with both, on every small quadratic;
* Q1 and Q8 are pinned by the build and the evaluation.

``RequestProject/GLM/QuadraticLasso.lean`` is why the jump and the *never*
verdict are proofs, and why the first change may be found by bisection on two
monotone stretches.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from . import affine_output as ao
from . import batch_machine as bm
from . import batch_speech as bs
from . import constant_bound as cb
from . import counter_lasso as cl
from . import inert_counter as ic
from . import operations as op

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BATTERY", "QUESTIONS", "battery_marks",
    "question_marks", "certificate_marks", "noninterference_marks",
    "soundness_marks", "first_change_marks", "quadratic_lasso_report",
]

LEAN_FILE = "RequestProject/GLM/QuadraticLasso.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "drift_succ", "seq_accelerate", "halts_of_seq_jump",
    "never_halts_of_seq_lasso", "acc_shift", "quadratic_iterate",
    "quadratic_accelerate", "halts_of_quadratic_jump",
    "never_halts_of_quadratic_lasso", "quad_diff", "quad_closed_form",
    "monotone_on_of_diff_nonneg", "antitone_on_of_diff_nonpos",
    "sign_change_persists", "sign_change_persists_anti", "cmp_of_sign",
    "quad_eventually_pos", "quad_eventually_neg")


def _lines(text: str) -> Tuple[str, ...]:
    return tuple(text.split(" / "))


def _tri(k: int) -> int:
    return k * (k + 1) // 2


_Q11 = ("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / "
        "IF %B% EQU {} GOTO END / GOTO UP / :END / ECHO found")

#: The battery of section 3, with the verdicts declared before the code.
BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object]], ...] = (
    ("Q1", cl._battery_lines("L12"),
     {"status": "never", "certificate": (3, 6), "d": {"A": 1, "B": 1},
      "g": {"B": 1}}),
    ("Q2", _lines("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / "
                  "SET /A B=B+A / IF %B% LSS 50000000 GOTO UP / ECHO %A% %B%"),
     {"status": "halted", "steps": 30004, "out": ("10000 50005000",),
      "exit": 0, "jumps": ((3, 6, 9999),)}),
    ("Q3", _lines("SET /A N=0 / SET /A S=100000000 / :DOWN / SET /A N=N+2 / "
                  "SET /A S=S-N / IF %S% GTR 0 GOTO DOWN / ECHO %N% %S%"),
     {"status": "halted", "steps": 30004, "out": ("20000 -10000",),
      "exit": 0, "values": {"S": "-10000"}, "jumps": ((3, 6, 9999),)}),
    ("Q4", _lines("SET /A K=0 / SET /A T=0 / :UP / SET /A K=K+1 / "
                  "SET /A T=T+K / ECHO %T% / IF %K% LSS 5000 GOTO UP"),
     {"status": "halted", "steps": 20003,
      "out": tuple(str(_tri(k)) for k in range(1, 5001)), "exit": 0,
      "values": {"T": "12502500"}, "jumps": ((3, 7, 4999),)}),
    ("Q5", _lines("SET /A I=0 / SET /A J=0 / SET /A S=0 / :L / "
                  "SET /A I=I+1 / SET /A J=J+4000 / SET /A S=S+I / "
                  "IF %S% LSS %J% GOTO L / ECHO %I% %S% %J%"),
     {"status": "halted", "steps": 32001,
      "out": ("7999 31996000 31996000",), "exit": 0,
      "jumps": ((4, 8, 7998),)}),
    ("Q6", _lines("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / "
                  "SET /A B=B-A / IF %B% LSS 1 GOTO UP"),
     {"status": "never", "certificate": (3, 6), "d": {"A": 1, "B": -1},
      "g": {"B": -1}}),
    ("Q7", _lines("SET /A V=-3000 / SET /A P=0 / :UP / SET /A V=V+1 / "
                  "SET /A P=P+V / IF %P% NEQ 0 GOTO UP / ECHO %V% %P%"),
     {"status": "halted", "steps": 18001, "out": ("2999 0",), "exit": 0,
      "jumps": ((3, 6, 5998),)}),
    ("Q8", next(lines for i, lines, _ in ic.BATTERY if i == "N5"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("Q9", _lines("SET /A A=0 / SET /A B=0 / SET /A C=0 / :UP / "
                  "SET /A A=A+1 / SET /A B=B+A / SET /A C=C+B / "
                  "IF %C% LSS 100000000000 GOTO UP"),
     {"refusal": "UNDECIDED_WITHIN_BUDGET"}),
    ("Q10", _lines("SET /A N=0 / SET /A S=0 / :UP / SET /A N=N+1 / "
                   "ECHO %S% / SET /A S=S+N / IF %N% LSS 4000 GOTO UP"),
     {"status": "halted", "steps": 16003,
      "out": tuple(str(_tri(k)) for k in range(0, 4000)), "exit": 0,
      "values": {"S": "8002000"}, "jumps": ((3, 7, 3999),)}),
    ("Q11", _lines(_Q11.format(50)),
     {"status": "never", "certificate": (3, 7), "d": {"A": 1, "B": 1},
      "g": {"B": 1}}),
    ("Q12", _lines(_Q11.format(50005000)),
     {"status": "halted", "steps": 40003, "out": ("found",), "exit": 0,
      "jumps": ((3, 7, 9999),)}),
)

_BY_ID = {i: lines for i, lines, _ in BATTERY}


def _program_text(ident: str) -> str:
    return "\n".join(_BY_ID[ident])


#: The questions of mark Q3: (program, question, expected).
QUESTIONS: Tuple[Tuple[str, str, Tuple], ...] = tuple(
    (ident, "does it halt?",
     ("halts", exp["steps"], exp["exit"]) if exp.get("status") == "halted"
     else ("never",) if exp.get("status") == "never"
     else ("refused", exp["refusal"]))
    for ident, _l, exp in BATTERY) + (
    ("Q2", "what does it print?", ("value", ["10000 50005000"])),
    ("Q7", "what does it print?", ("value", ["2999 0"])),
    ("Q12", "what does it print?", ("value", ["found"])),
    ("Q3", "what is the value of S?", ("value", "-10000")),
    ("Q10", "what is the value of S?", ("value", "8002000")),
    ("Q4", "what is the value of T?", ("value", "12502500")),
    ("Q5", "how many steps?", ("value", 32001)),
    ("Q1", "why is it undecided?", ("refused", "NOT_UNDECIDED")),
    ("Q9", "why is it undecided?",
     ("why", "found no recurring state with the counters masked")),
)


def battery_marks() -> Dict[str, object]:
    """Q2: each battery program as declared."""
    rows: List[Dict[str, object]] = []
    for ident, lines, exp in BATTERY:
        run = bm.run_program(bm.parse_program(lines))
        jumps = tuple(j[:3] for j in run.jumps)
        if "refusal" in exp:
            ok = run.status == "undecided"
            got: object = run.status
        elif exp["status"] == "never":
            ok = (run.status == "never" and run.certificate == exp["certificate"]
                  and dict(run.lasso) == exp["d"]
                  and dict(run.growth) == exp["g"])
            got = (run.status, run.certificate, run.lasso, run.growth)
        else:
            ok = (run.status == "halted" and run.steps == exp["steps"]
                  and run.out == tuple(exp["out"]) and run.err == ()
                  and run.exit_code == exp["exit"]
                  and all(run.env.get(k) == v
                          for k, v in exp.get("values", {}).items())
                  and jumps == tuple(exp["jumps"]))
            got = (run.status, run.steps, len(run.out), run.exit_code, jumps)
        rows.append({"id": ident, "as_declared": ok, "got": got})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "programs": len(rows), "wrong": wrong,
            "Q2": wrong == 0 and len(rows) == 12}


def question_marks(verify: bool = False) -> Dict[str, object]:
    """Q3: the twenty questions."""
    rows: List[Dict[str, object]] = []
    for ident, question, check in QUESTIONS:
        a = bs.answer(question, _program_text(ident), verify=verify)
        if check[0] == "refused":
            ok = (not a.answered) and a.refusal == check[1]
        elif check[0] == "halts":
            ok = (a.answered and a.value is True
                  and a.claim.get("kind") == "run_jump"
                  and a.claim.get("steps") == check[1]
                  and a.claim.get("exit") == check[2])
        elif check[0] == "never":
            ok = (a.answered and a.value is False
                  and a.claim.get("kind") == "never_lasso"
                  and bool(a.claim.get("g")))
        elif check[0] == "why":
            ok = (a.answered and check[1] in a.text
                  and a.claim.get("kind") == "growth")
        else:
            ok = (a.answered and a.value == check[1]
                  and a.claim.get("kind") == "run_jump")
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "text": a.text[:600], "refusal": a.refusal})
    wrong = sum(not r["as_declared"] for r in rows)
    return {"rows": tuple(rows), "questions": len(rows), "wrong": wrong,
            "missed": tuple(f"{r['id']}: {r['question']}" for r in rows
                            if not r["as_declared"]),
            "Q3": wrong == 0 and len(rows) == 20}


def certificate_marks() -> Dict[str, object]:
    """Q4: the ``run_jump`` and ``never_lasso`` claims of the battery and of
    the questions, their scripts and their mutations."""
    claims: List[Tuple[str, List[str], Dict[str, object]]] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        canon = [bm.render_line(i) for i in program]
        run = bm.run_program(program)
        if run.status == "never" and run.lasso:
            claims.append((ident, canon, bs.never_claim(run)))
        elif run.status == "halted" and run.jumps:
            claims.append((ident, canon, bs._run_claim(run, {})))
    for ident, question, check in QUESTIONS:
        if check[0] in ("refused", "halts", "never"):
            continue
        a = bs.answer(question, _program_text(ident), verify=False)
        canon = [bm.render_line(i) for i in bm.parse_program(_BY_ID[ident])]
        if a.claim:
            claims.append((ident, canon, dict(a.claim)))
    scripts = verified = mutations = rejected = 0
    failed: List[str] = []
    accepted: List[str] = []
    for ident, canon, claim in claims:
        scripts += 1
        ok, _ = bs.run_script(bs.column3_script(canon, claim))
        verified += ok
        if not ok:
            failed.append(ident)
        for mut in bs.mutations(claim, canon):
            mutations += 1
            good, _ = bs.run_script(bs.column3_script(canon, mut))
            rejected += not good
            if good:
                accepted.append(ident)
    return {"scripts": scripts, "verified": verified, "failed": tuple(failed),
            "mutations": mutations, "rejected": rejected,
            "accepted": tuple(accepted),
            "Q4": scripts > 0 and verified == scripts and rejected == mutations}


def _same_run(old: bm.Run, new: bm.Run) -> bool:
    return (old.status, old.certificate, old.lasso, old.forgotten, old.steps,
            old.out, old.err, old.exit_code, old.files,
            tuple(j[:3] for j in old.jumps)) == (
        new.status, new.certificate, new.lasso, new.forgotten, new.steps,
        new.out, new.err, new.exit_code, new.files,
        tuple(j[:3] for j in new.jumps))


#: The earlier programs that hold an accumulator line, named in advance.
MOVED = ("L12", "N6")


def noninterference_marks() -> Dict[str, object]:
    """Q5: Phase 125's battery, questions and English programs as declared;
    the Phase 126, 130, 131 and 132 batteries, questions and diagnosis
    battery as Phase 132's reading gives them, L12 and N6 apart; and every
    generated program keeps its answers."""
    machine = op.machine_marks(scripts=False)
    english = op.english_marks()
    questions = op.question_marks(scripts=False)
    batteries = (("126", ic.BATTERY, ic.QUESTIONS),
                 ("130", cl.BATTERY, cl.QUESTIONS),
                 ("131", cb.BATTERY, cb.QUESTIONS),
                 ("132", ao.BATTERY + ao.DIAGNOSIS, ao.QUESTIONS))
    kept = total = q_kept = q_total = 0
    moved: List[str] = []
    for _name, battery, qs in batteries:
        texts = {i: "\n".join(lines) for i, lines, _ in battery}
        for ident, lines, _exp in battery:
            if ident in MOVED:
                continue
            total += 1
            program = bm.parse_program(lines)
            same = _same_run(bm.run_program(program, quadratic=False),
                             bm.run_program(program))
            kept += same
            if not same:
                moved.append(ident)
        for ident, question, _check in qs:
            if ident in MOVED:
                continue
            q_total += 1
            old = bs.answer(question, texts[ident], verify=False,
                            quadratic=False)
            new = bs.answer(question, texts[ident], verify=False)
            same = (old.answered, old.text, old.refusal, old.claim) == (
                new.answered, new.text, new.refusal, new.claim)
            q_kept += same
            if not same:
                moved.append(f"{ident}: {question}")
    gkept = 0
    gmoved: List[int] = []
    for i in range(op.FUZZ_COUNT):
        program = bm.parse_program(op.generated_program(i))
        same = _same_run(bm.run_program(program, quadratic=False),
                         bm.run_program(program))
        gkept += same
        if not same:
            gmoved.append(i)
    l12 = bm.run_program(bm.parse_program(cl._battery_lines("L12")))
    ok = (machine["wrong"] == 0 and questions["wrong"] == 0
          and english["programs_as_declared"] == 6
          and kept == total and q_kept == q_total and not gmoved
          and l12.status == "never")
    return {"machine_wrong": machine["wrong"], "runs": machine["runs"],
            "questions_wrong": questions["wrong"],
            "english": english["programs_as_declared"],
            "battery_kept": kept, "battery_total": total,
            "questions_kept": q_kept, "questions_total": q_total,
            "moved": tuple(moved), "generated_kept": gkept,
            "generated_total": op.FUZZ_COUNT,
            "generated_moved": tuple(gmoved), "l12_now": l12.status,
            "Q5": ok}


def soundness_marks(budget: int = cl.LONG_BUDGET) -> Dict[str, object]:
    """Q6: every jumped *halts* of the battery equals a plain run of
    ``budget`` steps; no *never* is contradicted by one."""
    agree: List[str] = []
    disagree: List[str] = []
    never_ok: List[str] = []
    never_bad: List[str] = []
    for ident, lines, _exp in BATTERY:
        program = bm.parse_program(lines)
        run = bm.run_program(program)
        if run.status == "undecided":
            continue
        plain = bm.plain_run(program, budget=budget)
        if run.status == "halted":
            same = (plain.status == "halted" and plain.steps == run.steps
                    and plain.out == run.out and plain.err == run.err
                    and plain.files == run.files
                    and plain.exit_code == run.exit_code
                    and plain.env == run.env)
            (agree if same else disagree).append(ident)
        else:
            (never_ok if plain.status != "halted" else never_bad).append(ident)
    return {"halts_agree": tuple(agree), "halts_disagree": tuple(disagree),
            "never_unrefuted": tuple(never_ok), "never_refuted": tuple(never_bad),
            "budget": budget,
            "Q6": bool(agree) and not disagree and bool(never_ok)
            and not never_bad}


def _checker_qflip():
    """The column-3 route to the first change, taken from the checker's own
    source (``flip`` and ``qflip``), so that mark Q7 tests the code that
    runs in the scripts."""
    src = bs.CHECKER
    start = src.index("def flip(")
    stop = src.index("def template(")
    scope: Dict[str, object] = {}
    exec("from math import isqrt\nimport re\n"  # noqa: S102 - our own source
         + src[src.index("CMPS = "):src.index("def counters_of(")]
         + src[start:stop], scope)
    return scope["qflip"]


def first_change_marks(e_range: int = 40, b_range: int = 8, c_range: int = 5,
                       horizon: int = 400) -> Dict[str, object]:
    """Q7: for every ``e0``, ``b``, ``c`` in range and each comparison, the
    machine's first change equals a brute-force scan to ``horizon``, and the
    column-3 route agrees."""
    qflip = _checker_qflip()
    cases = machine_wrong = checker_wrong = 0
    examples: List[Tuple] = []
    for c in range(-c_range, c_range + 1):
        for b in range(-b_range, b_range + 1):
            for e0 in range(-e_range, e_range + 1):
                vals = [e0 + b * t + c * (t * (t - 1) // 2)
                        for t in range(horizon + 1)]
                for opn, truth in bm._CMP_TRUTH.items():
                    t0 = truth(vals[0])
                    brute: Optional[int] = next(
                        (t for t in range(1, horizon + 1)
                         if truth(vals[t]) != t0), None)
                    got = bm.first_change_quadratic(e0, b, c, opn)
                    alt = qflip(e0, b, c, opn)
                    cases += 1
                    if got != brute:
                        machine_wrong += 1
                        if len(examples) < 5:
                            examples.append(("machine", e0, b, c, opn, got,
                                             brute))
                    if alt != brute:
                        checker_wrong += 1
                        if len(examples) < 5:
                            examples.append(("checker", e0, b, c, opn, alt,
                                             brute))
    return {"cases": cases, "machine_wrong": machine_wrong,
            "checker_wrong": checker_wrong, "examples": tuple(examples),
            "Q7": cases > 0 and machine_wrong == 0 and checker_wrong == 0}


def quadratic_lasso_report(soundness: bool = True) -> Dict[str, object]:
    """Every mark the module takes, with its figures."""
    battery = battery_marks()
    questions = question_marks()
    cert = certificate_marks()
    ni = noninterference_marks()
    sound = soundness_marks() if soundness else {"Q6": None}
    first = first_change_marks()
    marks = {"Q2": battery["Q2"], "Q3": questions["Q3"], "Q4": cert["Q4"],
             "Q5": ni["Q5"], "Q6": sound["Q6"], "Q7": first["Q7"]}
    return {"battery": battery, "questions": questions, "certificates": cert,
            "noninterference": ni, "soundness": sound, "first_change": first,
            "marks": marks, "study": "studies/QUADRATIC_LASSO_STUDY.md",
            "lean_file": LEAN_FILE}
