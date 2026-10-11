"""``glm_universal.reasoning.operations`` -- the operations round, measured.

The declared battery of ``studies/OPERATIONS_LADDER_STUDY.md`` §3 -- 25
machine runs, 6 programs written in English, 18 questions and the ladder's
relations -- and the marks O2-O9 taken over it.  O1 is the Lean file,
checked by the Lean instruments; the test file checks that the theorems the
mark names are in it.

``python3 -m glm_universal.tools operations`` prints the report.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import batch_machine as bm
from . import batch_speech as bs
from . import ops_ladder as ol

__all__ = ["MACHINE_BATTERY", "ENGLISH_PROGRAMS", "QUESTIONS", "RELATIONS",
           "LEAN_FILE", "LEAN_THEOREMS", "machine_marks", "english_marks",
           "question_marks", "ladder_marks", "operations_report"]

LEAN_FILE = "RequestProject/GLM/OperationsLadder.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "never_halts_of_repeat", "never_halts_of_projected_repeat",
    "andThen_assoc", "orElse_assoc", "reconcile_idempotent",
    "reconcile_no_drift", "reconcile_eq_self_iff", "rollback_restores",
    "layered_wf", "promoted_iff_all_pass", "find_find", "sort_sort")

M5 = ("TYPE data.txt", "IF ERRORLEVEL 1 GOTO FAIL", "ECHO found", "EXIT /B 0",
      ":FAIL", "ECHO not found", "EXIT /B 2")
M7 = ("ECHO pear> fruit.txt", "ECHO apple>> fruit.txt",
      "ECHO fig>> fruit.txt", "TYPE fruit.txt | SORT")
M4 = ("SET /A N=0", ":TOP", "SET /A N=N+1", "IF %N% LSS 5 GOTO TOP",
      "ECHO %N%")
M8 = ("ECHO alpha> a.txt", "ECHO beta>> a.txt",
      'TYPE a.txt | FIND "be" && ECHO yes || ECHO no',
      'TYPE a.txt | FIND "ga" && ECHO yes || ECHO no')
M11 = ("SET /A X=5", "CALL :DOUBLE", "CALL :DOUBLE", "ECHO %X%", "EXIT /B 0",
       ":DOUBLE", "SET /A X=X*2", "EXIT /B 0")
M13 = (":LOOP", "SET X=1", "GOTO LOOP")
M15 = ("SET /A N=0", ":UP", "SET /A N=N+1", "GOTO UP")
M17 = ("ECHO %USERNAME%",)
M19 = ("FORMAT C:",)
M20 = ("IF NOT EXIST out MKDIR out", "ECHO ready> out/flag.txt")
M21 = ("ECHO run>> log.txt",)
M23 = ("GOTO END", "ECHO never", ":END", "ECHO done")

#: ``(id, program, inputs, expected)`` -- §3.1, expected answers as declared.
MACHINE_BATTERY: Tuple[Tuple[str, Tuple[str, ...], Dict[str, object],
                             Dict[str, object]], ...] = (
    ("M1", ("ECHO hello",), {}, {"out": ["hello"], "exit": 0, "steps": 1}),
    ("M2", ("SET NAME=world", "ECHO hello %NAME%"), {},
     {"out": ["hello world"]}),
    ("M3", ("SET /A X=6*7", "ECHO %X%"), {}, {"out": ["42"],
                                             "values": {"X": "42"}}),
    ("M4", M4, {}, {"out": ["5"], "values": {"N": "5"}, "steps": 13}),
    ("M5", M5, {}, {"out": ["not found"], "err": [bm.MSG_NO_FILE],
                    "exit": 2}),
    ("M6", M5, {"files": {"data.txt": ["alpha"]}},
     {"out": ["alpha", "found"], "exit": 0}),
    ("M7", M7, {}, {"out": ["apple", "fig", "pear"],
                    "files": {"fruit.txt": ["pear", "apple", "fig"]}}),
    ("M8", M8, {}, {"out": ["beta", "yes", "no"], "exit": 1}),
    ("M9", ("FOR %%I IN (red green blue) DO ECHO colour %%I",), {},
     {"out": ["colour red", "colour green", "colour blue"]}),
    ("M10", ("SET /A T=0", "FOR %%I IN (3 4 5) DO SET /A T=T+%%I",
             "ECHO %T%"), {}, {"out": ["12"]}),
    ("M11", M11, {}, {"out": ["20"], "exit": 0}),
    ("M12", ("CALL :CHECK", "ECHO %ERRORLEVEL%", "EXIT /B 0", ":CHECK",
             "EXIT /B 3"), {}, {"out": ["3"], "exit": 0}),
    ("M13", M13, {}, {"status": "never", "certificate": (2, 4)}),
    ("M14", (":LOOP", "ECHO tick", "GOTO LOOP"), {},
     {"status": "never", "certificate": (1, 3)}),
    # Phase 126 (studies/INERT_COUNTER_STUDY.md, mark I5): M15 was refused
    # UNDECIDED_WITHIN_BUDGET; its counter N is inert, and forgetting it the
    # control state before step 2 recurs before step 4.
    ("M15", M15, {}, {"status": "never", "certificate": (2, 4)}),
    ("M16", ("SET /A Z=0", "SET /A Y=10/Z", "ECHO done"), {},
     {"out": ["done"], "err": [bm.MSG_DIV_ZERO], "exit": 1}),
    ("M17", M17, {}, {"refusal": "UNDEFINED_VARIABLE"}),
    ("M18", M17, {"env": {"USERNAME": "ada"}}, {"out": ["ada"]}),
    ("M19", M19, {}, {"refusal": "UNKNOWN_COMMAND"}),
    ("M20", M20, {}, {"out": [], "dirs": ["out"],
                      "files": {"out/flag.txt": ["ready"]},
                      "idempotent": True}),
    ("M21", M21, {}, {"idempotent": False, "differing": ["log.txt"]}),
    ("M22", ("MKDIR out",), {}, {"idempotent": True, "second_exit": 1,
                                 "second_err": ["A subdirectory or file out "
                                                "already exists."]}),
    ("M23", M23, {}, {"out": ["done"], "unreachable": [2]}),
)

#: M24 and M25 are not single runs: drift and reconciliation, and a pipeline.
M24 = {"desired": {"config.txt": ["mode=prod"]},
       "actual": {"config.txt": ["mode=dev"], "extra.txt": ["x"]},
       "drift": ["config.txt"], "program": ["ECHO mode=prod> config.txt"]}
M25 = {
    "stages": [("build", ["ECHO built> artifact.bin"]),
               ("test", ['TYPE artifact.bin | FIND "built"']),
               ("deploy", ["COPY artifact.bin prod.bin"])],
    "failing": [("build", ["ECHO built> artifact.bin"]),
                ("test", ['TYPE artifact.bin | FIND "broken"']),
                ("deploy", ["COPY artifact.bin prod.bin"])],
}

#: §3.2 -- ``(id, sentences, declared GLM-BAT, inputs, expected run)``.
ENGLISH_PROGRAMS = (
    ("E1", 'compute N as 0. label TOP. add 1 to N. if %N% is less than 3, '
           'go to TOP. print "%N%".',
     ["SET /A N=0", ":TOP", "SET /A N=N+1", "IF %N% LSS 3 GOTO TOP",
      "ECHO %N%"], {}, {"out": ["3"]}),
    ("E2", 'show file data.txt. if the exit code is at least 1, stop with '
           'code 2. print "ok".',
     ["TYPE data.txt", "IF ERRORLEVEL 1 EXIT 2", "ECHO ok"], {},
     {"exit": 2}),
    ("E3", 'for each I in a, b, c: print "item %%I".',
     ["FOR %%I IN (a b c) DO ECHO item %%I"], {},
     {"out": ["item a", "item b", "item c"]}),
    ("E4", 'print "x", writing to file f.txt. show file f.txt, then count '
           'lines containing "x".',
     ["ECHO x> f.txt", 'TYPE f.txt | FIND /C "x"'], {}, {"out": ["1"]}),
    ("E5", 'make directory out, and if that succeeds, print "made".',
     ["MKDIR out && ECHO made"], {}, {"out": ["made"]}),
    ("E6", 'set GREETING to "hi". print "%GREETING% there".',
     ["SET GREETING=hi", "ECHO %GREETING% there"], {},
     {"out": ["hi there"]}),
)

#: §3.3 -- ``(id, program, question, check)``; ``check`` is the declared
#: answer: a value, or ``("refused", NAME)``.
QUESTIONS = (
    ("Q1", M7, "what does it print?", ["apple", "fig", "pear"]),
    ("Q2", M4, "what is N at the end?", "5"),
    ("Q3", M8, "what is the exit code?", 1),
    ("Q4", M13, "does it halt?", ("never", (2, 4))),
    ("Q5", M4, "does it halt?", ("halts", 13)),
    ("Q6", M15, "does it halt?", ("never", (2, 4))),  # Phase 126; was refused
    ("Q7", M20, "is it idempotent?", True),
    ("Q8", M21, "is it idempotent?", False),
    ("Q9", M23, "which lines are unreachable?", [2]),
    ("Q10", M7, "which files does it write?", ["fruit.txt"]),
    ("Q11", M7, "what is in file fruit.txt?", ["pear", "apple", "fig"]),
    ("Q12", M5, "what does it say?", ("sentences", 7, "show file data.txt.")),
    ("Q13", M8, "what does it use?",
     ("terms", ("command", "pipe", "redirection", "exit_handling", "stream",
                "file", "exit_code"))),
    ("Q14", M17, "what does it print?", ("refused", "UNDEFINED_VARIABLE")),
    ("Q15", M19, "what does it print?", ("refused", "UNKNOWN_COMMAND")),
    ("Q16", M4, "how many steps?", 13),
    ("Q17", M11, "what is X at the end?", "20"),
    ("Q18", ("ECHO hello",), "what is the colour of it?",
     ("refused", "UNREAD_QUESTION")),
)

#: §3.4 -- the declared relations and projections.
RELATIONS = {
    "R1": ("pipe", "feedback_loop", ("part_of",
                                     ("feedback_loop", "pipeline", "pipe"))),
    "R2": ("rollback", "idempotence", ("shares", "state")),
    "R4": {"rollback": "inverse", "idempotence": "fixed point",
           "drift": "error", "feedback_loop": "feedback",
           "pipe": "composition"},
}


def _program(lines: Sequence[str]) -> Tuple[object, ...]:
    return bm.parse_program(list(lines))


def _verify(lines: Sequence[str], claim: Mapping[str, object],
            env=None, files=None, dirs=()) -> Dict[str, int]:
    """Run the column-3 script and every mutation: counts for mark O7."""
    script = bs.column3_script(lines, claim, env, files, dirs)
    ok, _ = bs.run_script(script)
    rejected = 0
    muts = bs.mutations(claim, lines)
    for mut in muts:
        good, _ = bs.run_script(bs.column3_script(lines, mut, env, files, dirs))
        rejected += not good
    return {"scripts": 1, "verified": int(ok), "mutations": len(muts),
            "rejected": rejected}


def _add(total: Dict[str, int], part: Mapping[str, int]) -> None:
    for k, v in part.items():
        total[k] = total.get(k, 0) + v


def machine_marks(scripts: bool = True) -> Dict[str, object]:
    """O4 over the 25 runs, and O7 over every answered run."""
    rows: List[Dict[str, object]] = []
    cert = {"scripts": 0, "verified": 0, "mutations": 0, "rejected": 0}
    for ident, lines, inputs, exp in MACHINE_BATTERY:
        env = inputs.get("env")
        files = inputs.get("files")
        problems: List[str] = []
        try:
            program = _program(lines)
        except bm.BatchError as exc:
            ok = exp.get("refusal") == exc.name
            rows.append({"id": ident, "as_declared": ok, "got": exc.name})
            continue
        run = bm.run_program(program, env, files)
        canon = [bm.render_line(i) for i in program]
        if "refusal" in exp:
            got = ("UNDECIDED_WITHIN_BUDGET" if run.status == "undecided"
                   else "UNDEFINED_VARIABLE" if run.undefined else run.status)
            rows.append({"id": ident, "as_declared": got == exp["refusal"],
                         "got": got})
            continue
        if exp.get("status") == "never":
            ok = (run.status == "never"
                  and run.certificate == tuple(exp["certificate"]))
            if scripts and run.status == "never":
                _add(cert, _verify(canon, bs.never_claim(run), env, files))
            rows.append({"id": ident, "as_declared": ok,
                         "got": (run.status, run.certificate)})
            continue
        if not run.halted:
            problems.append(f"status {run.status}")
        for key, field_ in (("out", "out"), ("err", "err")):
            if key in exp and list(getattr(run, field_)) != exp[key]:
                problems.append(f"{key} {getattr(run, field_)}")
        if "exit" in exp and run.exit_code != exp["exit"]:
            problems.append(f"exit {run.exit_code}")
        if "steps" in exp and run.steps != exp["steps"]:
            problems.append(f"steps {run.steps}")
        for name, value in exp.get("values", {}).items():
            if run.env.get(name) != value:
                problems.append(f"{name}={run.env.get(name)}")
        if "files" in exp and {k: list(v) for k, v in run.files.items()} \
                != exp["files"]:
            problems.append(f"files {run.files}")
        if "dirs" in exp and list(run.dirs) != exp["dirs"]:
            problems.append(f"dirs {run.dirs}")
        if "unreachable" in exp and list(bm.unreachable_lines(program)) \
                != exp["unreachable"]:
            problems.append("unreachable")
        if "idempotent" in exp:
            info = bm.idempotence(program, files, (), env)
            if info["idempotent"] != exp["idempotent"]:
                problems.append("idempotent")
            if "differing" in exp and info["differing_files"] \
                    != exp["differing"]:
                problems.append("differing")
            if "second_exit" in exp and info["second_exit"] \
                    != exp["second_exit"]:
                problems.append("second exit")
            if "second_err" in exp and info["second_err"] != exp["second_err"]:
                problems.append("second err")
            if scripts:
                _add(cert, _verify(canon, {"kind": "idempotent",
                                           "idempotent": info["idempotent"],
                                           "differing":
                                               info["differing_files"]},
                                   env, files))
        if scripts and run.halted:
            values = {k: run.env[k] for k in exp.get("values", {})
                      if k in run.env}
            _add(cert, _verify(canon, bs._run_claim(run, values), env, files))
            if "unreachable" in exp:
                _add(cert, _verify(canon, {"kind": "unreachable", "lines":
                                           list(bm.unreachable_lines(program))},
                                   env, files))
        rows.append({"id": ident, "as_declared": not problems,
                     "problems": problems})
    # ----- M24: drift and reconciliation -----
    d = list(bm.drift(M24["desired"], M24["actual"]))
    prog = bm.reconcile_program(M24["desired"], M24["actual"])
    rec = bm.run_program(_program(prog), None, M24["actual"])
    after = list(bm.drift(M24["desired"], rec.files))
    idem = bm.idempotence(_program(prog), M24["actual"])
    ok24 = (d == M24["drift"] and prog == M24["program"] and not after
            and idem["idempotent"])
    if scripts:
        _add(cert, _verify(prog, {"kind": "idempotent", "idempotent": True,
                                  "differing": []}, None, M24["actual"]))
    rows.append({"id": "M24", "as_declared": ok24,
                 "got": {"drift": d, "program": prog, "after": after}})
    # ----- M25: the pipeline, then the failing one with rollback -----
    st = [(n, _program(p)) for n, p in M25["stages"]]
    fl = [(n, _program(p)) for n, p in M25["failing"]]
    good = bm.run_pipeline(st)
    bad = bm.run_pipeline(fl, rollback=True)
    ok25 = (good["promoted"] and good["passed"] == ["build", "test", "deploy"]
            and good["files"].get("prod.bin") == ("built",)
            and not bad["promoted"] and bad["failed_at"] == "test"
            and bad["files"] == {})
    if scripts:
        for stages, res, rb in ((M25["stages"], good, False),
                                (M25["failing"], bad, True)):
            claim = {"kind": "pipeline", "stages": [[n, list(p)] for n, p in
                                                    stages],
                     "rollback": rb, "promoted": res["promoted"],
                     "failed_at": res["failed_at"],
                     "files": {k: list(v) for k, v in res["files"].items()}}
            _add(cert, _verify([], claim))
    rows.append({"id": "M25", "as_declared": ok25,
                 "got": {"promoted": good["promoted"],
                         "failed_at": bad["failed_at"]}})
    return {"rows": rows, "runs": len(rows),
            "as_declared": sum(1 for r in rows if r["as_declared"]),
            "wrong": sum(1 for r in rows if not r["as_declared"]),
            "certificates": cert}


def english_marks() -> Dict[str, object]:
    """O5: every battery line said and read back; the English programs."""
    said = back = 0
    for _, lines, _, _ in MACHINE_BATTERY:
        try:
            program = _program(lines)
        except bm.BatchError:
            continue
        for ins in program:
            said += 1
            back += bs.read_sentence(bs.say_line(ins)) == ins
    for key in ("stages", "failing"):
        for _, p in M25[key]:
            for ins in _program(p):
                said += 1
                back += bs.read_sentence(bs.say_line(ins)) == ins
    rows = []
    for ident, text, declared, inputs, exp in ENGLISH_PROGRAMS:
        lines = bs.read_english(text)
        run = bm.run_program(_program(lines), inputs.get("env"),
                             inputs.get("files"))
        ok = (lines == declared and run.halted
              and all(list(getattr(run, "out")) == v if k == "out"
                      else run.exit_code == v for k, v in exp.items()))
        rows.append({"id": ident, "lines": lines, "as_declared": ok})
    return {"lines_said": said, "read_back": back, "programs": rows,
            "programs_as_declared": sum(r["as_declared"] for r in rows)}


def question_marks(scripts: bool = True) -> Dict[str, object]:
    """O6 and the questions' share of O7."""
    rows = []
    cert = {"scripts": 0, "verified": 0, "mutations": 0, "rejected": 0}
    for ident, lines, question, check in QUESTIONS:
        a = bs.answer(question, "\n".join(lines), verify=False)
        if isinstance(check, tuple) and check[0] == "refused":
            ok = (not a.answered) and a.refusal == check[1]
        elif not a.answered:
            ok = False
        elif isinstance(check, tuple) and check[0] == "never":
            ok = a.claim.get("certificate") == list(check[1])
        elif isinstance(check, tuple) and check[0] == "halts":
            ok = a.value is True and a.claim.get("steps") == check[1]
        elif isinstance(check, tuple) and check[0] == "sentences":
            ok = len(a.value) == check[1] and a.value[0] == check[2]
        elif isinstance(check, tuple) and check[0] == "terms":
            ok = set(check[1]) <= set(a.value)
        else:
            ok = a.value == check
        if scripts and a.answered and a.claim:
            program = bs.read_program("\n".join(lines))[0]
            _add(cert, _verify([bm.render_line(i) for i in program], a.claim))
        rows.append({"id": ident, "question": question, "as_declared": ok,
                     "answer": a.body()})
    return {"rows": rows, "questions": len(rows),
            "as_declared": sum(r["as_declared"] for r in rows),
            "wrong": sum(1 for r in rows if not r["as_declared"]),
            "certificates": cert}


def ladder_marks() -> Dict[str, object]:
    """O2, O3, O8 and hypothesis H."""
    note = ol.note_check()
    o2 = (note["terms_in_note"] == note["terms"] == 97
          and not note["mismatched_tiers"] and not note["layering_violations"]
          and not note["ungrounded"] and not note["idle_primitives"])
    car = ol.carrier_census()
    o3 = car["round_trips"] == car["distinct"] == 97
    r1 = ol.relation("pipe", "feedback_loop")
    r2 = ol.relation("rollback", "idempotence")
    rels = {
        "R1": r1["kind"] == "part_of" and tuple(r1["chain"]) ==
        RELATIONS["R1"][2][1],
        "R2": r2["kind"] == "related" and "state" in r2["shared_parts"],
        "R4": all(ol.PROJECTION[t] == g for t, g in RELATIONS["R4"].items()),
    }
    without_process = [t for t in ol.term_ids() if ol.tier_of(t) > 0
                       and "process" not in ol.ground(t)]
    cross = ol.crossover_census()
    rels["R5"] = all(r["resolves"] for r in cross)
    return {"note": note, "O2": o2, "carrier": car, "O3": o3,
            "relations": rels, "O8": all(rels.values()),
            "r1_sentence": ol.relation_sentence("pipe", "feedback_loop"),
            "r2_sentence": ol.relation_sentence("rollback", "idempotence"),
            "r2_overlap": r2["ground_overlap"],
            "r3_without_process": without_process,
            "crossovers": cross, "projection": ol.projection_census()}


def noninterference() -> Dict[str, object]:
    """O9's routing half: the toolbox (where the new tools live) reads none
    of the router's declared question sets."""
    from ..runtime import router
    sets = router._declared_sets()
    read = {name: sum(1 for t in texts if router.reader_of(t) == "toolbox")
            for name, texts in sets.items()}
    return {"toolbox_reads": read, "O9_routing": not any(read.values())}


# ===========================================================================
# POST HOC, NOT A MARK -- the two interpreters on generated programs
# ===========================================================================

#: The generator's declared seed and size (chosen after the marks were
#: taken; the study reports this as post-hoc evidence, not as a mark).
FUZZ_SEED = 20261010
FUZZ_COUNT = 300


def _lcg(seed: int):
    state = seed
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        yield state >> 33


def generated_program(index: int) -> List[str]:
    """A deterministic random GLM-BAT program over a small vocabulary:
    variables, arithmetic, files, pipes, chains, loops, labels, jumps and
    subroutines, so that halting, cycles and the budget all occur."""
    g = _lcg(FUZZ_SEED + 7919 * index)

    def pick(seq):
        return seq[next(g) % len(seq)]

    labels = ["L1", "L2", "L3"]
    words = ["red", "fig", "pear", "apple", "x1"]
    files = ["a.txt", "b.txt"]
    lines = ["SET /A N=0", "SET W=fig"]
    body = []
    for _ in range(3 + next(g) % 8):
        v = pick(["N", "M"])
        k = 1 + next(g) % 4
        body.append(pick([
            f"ECHO {pick(words)}",
            f"ECHO %{v}%",
            f"SET W={pick(words)}",
            f"SET /A {v}={v}+{k}",
            f"SET /A {v}={v}*{k}-{next(g) % 3}",
            f"SET /A M=N%{k}",
            f"IF %N% LSS {k + next(g) % 6} GOTO {pick(labels)}",
            f"IF ERRORLEVEL 1 ECHO failed",
            f"IF NOT EXIST {pick(files)} ECHO {pick(words)}> {pick(files)}",
            f"ECHO {pick(words)}>> {pick(files)}",
            f"TYPE {pick(files)}",
            f"TYPE {pick(files)} | SORT",
            f'TYPE {pick(files)} | FIND "{pick(words)[:2]}" && ECHO yes || '
            f"ECHO no",
            f'TYPE {pick(files)} | FIND /C "{pick(words)[:1]}"',
            f"FOR %%I IN ({pick(words)} {pick(words)}) DO ECHO %%I %W%",
            f'IF "%W%"=="{pick(words)}" SET /A N=N+1',
            f"GOTO {pick(labels)}",
            f":{pick(labels)}",
            f"DEL {pick(files)}",
            f"COPY {pick(files)} {pick(files)}",
            "CALL :SUB",
            f"EXIT /B {next(g) % 3}",
        ]))
    seen = set()
    for line in body:
        if line.startswith(":"):
            if line in seen:
                continue
            seen.add(line)
        lines.append(line)
    for lab in labels:
        if f":{lab}" not in seen:
            lines.append(f":{lab}")
    lines += ["EXIT /B 0", ":SUB", "SET /A N=N+1", "EXIT /B 0"]
    return lines


def interpreter_agreement(count: int = FUZZ_COUNT) -> Dict[str, object]:
    """Run each generated program on the machine, give the verdict to the
    second interpreter as a column-3 claim, and count agreements."""
    tally = {"programs": count, "halted": 0, "never": 0, "undecided": 0,
             "agree": 0, "disagree": [], "lines": 0, "lines_read_back": 0}
    for i in range(count):
        lines = generated_program(i)
        program = _program(lines)
        for ins in program:
            tally["lines"] += 1
            tally["lines_read_back"] += bs.read_sentence(bs.say_line(ins)) == ins
        run = bm.run_program(program)
        tally[run.status] += 1
        if run.status == "undecided":
            continue
        claim = bs._run_claim(run, {}) if run.halted else bs.never_claim(run)
        ok, last = bs.run_script(bs.column3_script(
            [bm.render_line(x) for x in program], claim))
        if ok:
            tally["agree"] += 1
        else:
            tally["disagree"].append((i, last))
    return tally


def operations_report(scripts: bool = True,
                      routing: bool = True) -> Dict[str, object]:
    machine = machine_marks(scripts)
    english = english_marks()
    questions = question_marks(scripts)
    ladder = ladder_marks()
    cert = dict(machine["certificates"])
    _add(cert, questions["certificates"])
    marks = {
        "O2": ladder["O2"], "O3": ladder["O3"],
        "O4": machine["wrong"] == 0 and machine["runs"] == 25,
        "O5": (english["read_back"] == english["lines_said"]
               and english["programs_as_declared"] == 6),
        "O6": questions["wrong"] == 0 and questions["questions"] == 18,
        "O7": (not scripts) or (cert["verified"] == cert["scripts"]
                                and cert["rejected"] == cert["mutations"]),
        "O8": ladder["O8"],
    }
    report: Dict[str, object] = {
        "machine": machine, "english": english, "questions": questions,
        "ladder": ladder, "certificates": cert, "marks": marks,
        "hypothesis_H": ladder["projection"]["holds"],
        "study": "studies/OPERATIONS_LADDER_STUDY.md", "lean_file": LEAN_FILE,
    }
    if routing:
        ni = noninterference()
        report["noninterference"] = ni
        marks["O9_routing"] = ni["O9_routing"]
    return report
