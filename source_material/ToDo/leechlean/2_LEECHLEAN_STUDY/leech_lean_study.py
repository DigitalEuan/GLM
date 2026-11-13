"""``glm_universal.reasoning.leech_lean_study`` -- the measurement behind
``studies/LEECHLEAN_STUDY.md``: does taking the leechlean item in let the GLM
answer questions about its own Lean development that it currently refuses,
and does the move model reproduce its advantage over the part model?

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22).*

The protocol (pre-registered in the study's §8 before the port existed):

1. the **15 questions**, asked through the real ``tool leechlean`` surface
   (the router and the toolbox, in process), each graded against fragments
   fixed from the item's own data;
2. the **baseline**: the same questions through the same routing with the
   tool taken out (:func:`without_leechlean` -- the Phase-186 pattern), the
   expected outcome 0 of 15, all refused;
3. the **six negative controls** of the study's §4, each graded
   refused / flagged / answered-anyway;
4. the **mechanism, live**: the recorded head-to-head (next-move vs
   next-part prediction, greedy top-1, leave-one-file-out) re-measured on a
   pre-registered sample -- the 442 corpus files decoded through the
   codebook, 30 of them drawn with the fixed seed 20261111, and for each a
   leave-one-file-out model built over the other 441, once predicting the
   next part from the previous part, once the next move from the previous
   move (the bar of the study: the move model at least 3 points above the
   part model; the recorded full-corpus figures are 45.8% against 40.6%).

Nothing here constructs a float: accuracies are exact integer ratios
(hits/total), and the one-decimal renderings in the answer text are integer
per-mille arithmetic.  :func:`leech_lean_report` recomputes the study's
Tier-0 deciding figure; ``call:`` it, or run ``tests/test_leech_lean_study.py``.
"""
from __future__ import annotations

import random
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from .. import constants as C
from . import leech_lean as LL
from . import leech_lean_tools as LT

#: The 30-file leave-one-file-out sample of the mechanism measurement:
#: drawn from the 442 corpus files with this fixed seed (pre-registered).
LOO_SEED = 20261111
LOO_FILES = 30

#: The study this module measures (its Tier 0 is recomputed here).
STUDY = "LEECHLEAN_STUDY"

_SESSION = None


# ── the switch: the GLM without the leechlean tool ─────────────────────────

@contextmanager
def without_leechlean() -> Iterator[None]:
    """The GLM as it answers without the item: the ``leechlean`` tool and
    its English routes out of the toolbox, the module reported not
    installed.  Everything is restored on leaving, whatever happens inside
    (the Phase-186 pattern of ``intake_capability_study.without_phase186``)."""
    from ..runtime import toolbox as tb
    saved = (tb.TOOLS, tb.TOOL_PHRASES, getattr(tb, "_leech_lean_tools", None))
    try:
        tb.TOOLS = tuple(t for t in tb.TOOLS if t.name != "leechlean")
        tb.TOOL_PHRASES = tuple((p, t) for p, t in tb.TOOL_PHRASES
                                if t.split()[1:2] != ["leechlean"])
        tb._leech_lean_tools = lambda: None
        yield
    finally:
        tb.TOOLS, tb.TOOL_PHRASES = saved[:2]
        if saved[2] is None:
            try:
                del tb._leech_lean_tools
            except AttributeError:
                pass
        else:
            tb._leech_lean_tools = saved[2]


def _routed(question: str) -> Tuple[str, str]:
    """One question read as ``-q`` reads it: ``(status, answer text)``."""
    global _SESSION
    import GLM
    from ..runtime.session import GeometricSession
    if _SESSION is None:
        _SESSION = GeometricSession()
    r = GLM.routed_result(_SESSION, question)
    return str(r.status), str(r.answer or "")


# ── the corpus, decoded once through the codebook ──────────────────────────

_DECODED: Optional[List[Tuple[str, List[str], List[Tuple[int, ...]]]]] = None


def decoded_corpus() -> List[Tuple[str, List[str], List[Tuple[int, ...]]]]:
    """The 442 corpus files as (rel path, part keys, addresses), decoded
    through the injective codebook (every file of ``src/lean`` is covered --
    the item battery re-measures that on the tree as it stands)."""
    global _DECODED
    if _DECODED is not None:
        return _DECODED
    root = C.REPOSITORY_ROOT / "src" / "lean"
    out: List[Tuple[str, List[str], List[Tuple[int, ...]]]] = []
    for path in sorted(root.rglob("*.lean")):
        try:
            keys, addrs = LL.encode_text(
                path.read_text(encoding="utf-8", errors="replace"))
        except KeyError:
            continue            # a part outside the 442-file codebook
        out.append((str(path.relative_to(root)), keys, addrs))
    _DECODED = out
    return _DECODED


# ── the mechanism: leave-one-file-out, next part vs next move ──────────────

def loo_head_to_head() -> Dict[str, int]:
    """The move model against the part model, greedy top-1, leave-one-file-out
    over the pre-registered sample.  Every figure is an integer: hits and
    totals, never a divided float."""
    files = decoded_corpus()
    part_trans: List[Counter] = []
    move_trans: List[Counter] = []
    keys_by_file: List[List[str]] = []
    for _rel, keys, addrs in files:
        keys_by_file.append(keys)
        cp = Counter()
        cm = Counter()
        for i in range(1, len(keys)):
            cp[(keys[i - 1], keys[i])] += 1
            d1 = tuple(addrs[i - 1][j] - addrs[i - 2][j] for j in range(24)) \
                if i >= 2 else None
            if d1 is not None:
                d2 = tuple(addrs[i][j] - addrs[i - 1][j] for j in range(24))
                cm[(d1, d2)] += 1
        part_trans.append(cp)
        move_trans.append(cm)
    full_p: Dict[str, Counter] = {}
    full_m: Dict[Tuple[int, ...], Counter] = {}
    for cp, cm in zip(part_trans, move_trans):
        for (u, v), n in cp.items():
            full_p.setdefault(u, Counter())[v] += n
        for (d1, d2), n in cm.items():
            full_m.setdefault(d1, Counter())[d2] += n
    rng = random.Random(LOO_SEED)
    sample = rng.sample(range(len(files)), min(LOO_FILES, len(files)))
    part_hits = part_total = move_hits = move_total = 0
    for fi in sample:
        cp, cm = part_trans[fi], move_trans[fi]
        fp: Dict[str, Counter] = {}
        for (u, v), n in cp.items():
            fp.setdefault(u, Counter())[v] -= n
        fm: Dict[Tuple[int, ...], Counter] = {}
        for (d1, d2), n in cm.items():
            fm.setdefault(d1, Counter())[d2] -= n
        keys, addrs = files[fi][1], files[fi][2]
        for i in range(1, len(keys)):
            u, v = keys[i - 1], keys[i]
            cand = full_p.get(u)
            if cand:
                best = None
                for k, n in cand.items():
                    eff = n + fp.get(u, Counter()).get(k, 0)
                    if eff > 0 and (best is None or eff > best[0]
                                    or (eff == best[0] and k < best[1])):
                        best = (eff, k)
                if best is not None:
                    part_total += 1
                    part_hits += best[1] == v
            if i >= 2:
                d1 = tuple(addrs[i - 1][j] - addrs[i - 2][j] for j in range(24))
                d2 = tuple(addrs[i][j] - addrs[i - 1][j] for j in range(24))
                cand = full_m.get(d1)
                if cand:
                    best = None
                    for k, n in cand.items():
                        eff = n + fm.get(d1, Counter()).get(k, 0)
                        if eff > 0 and (best is None or eff > best[0]
                                        or (eff == best[0] and k < best[1])):
                            best = (eff, k)
                    if best is not None:
                        move_total += 1
                        move_hits += best[1] == d2
    return {"part_hits": part_hits, "part_total": part_total,
            "move_hits": move_hits, "move_total": move_total,
            "files": len(sample)}


def _permille(hits: int, total: int) -> str:
    """A percentage rendered without a float (integer per-mille)."""
    if not total:
        return "0.0%"
    pm = (hits * 1000) // total
    return f"{pm // 10}.{pm % 10}%"


# ── the 15 questions and the 6 controls (pre-registered in the study) ──────

def _fragments() -> Dict[str, List[str]]:
    """The grade fragments of the 15 questions, fixed from the item's own
    data (the codebook, the library graph, the file tree)."""
    cb = LL.codebook_state()
    thm = cb.parts["kw:theorem"]
    colons = cb.parts["sym::="]
    mllib = cb.parts["ident:Mathlib"]
    ws = cb.parts["ws: "]
    path = "RequestProject/GLM/Golay/Code.lean"
    rep = LL.file_report(LL.resolve_lean_path(path))
    att = LL.attestations_of("kw:theorem")
    return {
        "q1": [str(list(thm.address)), f"= {thm.energy}", f"{thm.count:,} uses"],
        "q2": [str(list(colons.address)), f"= {colons.energy}"],
        "q3": [str(list(mllib.address)), f"= {mllib.energy}", f"{mllib.count} uses"],
        "q4": ["type 2 (one of the 98,280", "minimal-vector classes"],
        "q5": [f"{rep.ticks:,} ticks", "byte-exact", f"{rep.on_lattice}/{rep.ticks}"],
        "q6": ["kappa(d1)(*)kappa(d2) = kappa(d1+d2) holds live on the two "
               "most common moves: True"],
        "q7": ["'ws: '", "6,725 joinings", "unverified graph proposals"],
        "q8": [f"{len(LL.universal_core(400))} parts"],
        "q9": ["29,422 token", "10,421 bigram", "63 frame", "86 tactic"],
        "q10": ["flags 40 of 40", "mod2", "40/40 back to the true parts"],
        "q11": ["clean: the congruence sieve raises 0 false alarms"],
        "q12": [f"{len(att)} declaration frame(s)",
                f"{LL.library_state().part_files.get('kw:theorem', 0)} of the "
                "442 library files"],
        "q13": ["1 new", "fresh addresses on the fly", "byte-exact"],
        "q14": ["class syndrome flags 40 of 40",
                "the congruence sieve sees 40 clean ticks"],
        "q15": [f"energy {ws.energy} (the one-bit sphere)",
                f"'ident:Mathlib' ({mllib.count} uses) at {mllib.energy}",
                "one bit of surprisal is four units of Leech energy"],
    }


_QUESTIONS: List[Tuple[str, str]] = [
    ("q1", "tool leechlean address theorem"),
    ("q2", "tool leechlean address :="),
    ("q3", "tool leechlean address Mathlib"),
    ("q4", "tool leechlean address theorem"),
    ("q5", "tool leechlean file RequestProject/GLM/Golay/Code.lean"),
    ("q6", "tool leechlean moves RequestProject/GLM/Golay/Code.lean"),
    ("q7", "tool leechlean continue theorem"),
    ("q8", "tool leechlean state"),
    ("q9", "tool leechlean state"),
    ("q10", "tool leechlean verify RequestProject/GLM/Golay/Code.lean flip 1"),
    ("q11", "tool leechlean verify RequestProject/GLM/Golay/Code.lean"),
    ("q12", "tool leechlean attest theorem"),
    ("q13", "tool leechlean stitch theorem glm_fresh_9c4d : True := by decide"),
    ("q14", "tool leechlean verify RequestProject/GLM/Golay/Code.lean slip"),
    ("q15", "tool leechlean state"),
]

_CONTROLS: List[Tuple[str, str, str]] = [
    ("n1_unknown_part", "tool leechlean address zzz_not_a_part_qq", "refused"),
    ("n2_unknown_file", "tool leechlean file No/Such/File.lean", "refused"),
    ("n3_unseen_continuation", "tool leechlean continue zzz_not_a_part_qq",
     "refused"),
    ("n4_prove_overclaim", "tool leechlean prove that one equals one",
     "refused"),
    ("n5_corrupted_as_clean",
     "tool leechlean verify RequestProject/GLM/Golay/Code.lean flip 3",
     "flagged"),
    ("n6_prove_riemann", "tool leechlean prove the Riemann hypothesis",
     "refused"),
]


def _grade_tool(question: str, fragments: List[str]) -> Tuple[str, str]:
    """One question through the real tool surface: ``(grade, answer)``."""
    arg = question[len("tool leechlean"):].strip()
    ok, text, _fig = LT.leechlean_text(arg)
    if not ok:
        return "refused", text
    missing = [f for f in fragments if f not in text]
    return ("right" if not missing else "wrong"), text


# ── the report ─────────────────────────────────────────────────────────────

def leech_lean_report() -> Dict[str, object]:
    """The study's measurement, recomputed: every check, the 15 grades, the
    baseline, the controls and the mechanism figures, all exact."""
    frags = _fragments()
    grades: Dict[str, str] = {}
    answers: Dict[str, str] = {}
    for qid, question in _QUESTIONS:
        grade, text = _grade_tool(question, frags[qid])
        grades[qid] = grade
        answers[qid] = text
    # the baseline: the same questions with the tool taken out
    with without_leechlean():
        baseline: Dict[str, str] = {}
        for qid, question in _QUESTIONS:
            status, _text = _routed(question)
            baseline[qid] = "answered" if status == "answered" else "refused"
    # the negative controls
    controls: Dict[str, str] = {}
    for cid, question, expected in _CONTROLS:
        grade, text = _grade_tool(question, [])
        if expected == "refused":
            controls[cid] = "refused" if grade == "refused" else "answered-anyway"
        elif expected == "flagged":
            controls[cid] = ("flagged" if "flags 40 of 40" in text
                             and "false alarms" not in text
                             else ("refused" if grade == "refused"
                                   else "passed-as-clean"))
    # the mechanism
    loo = loo_head_to_head()
    part_pm = _permille(loo["part_hits"], loo["part_total"])
    move_pm = _permille(loo["move_hits"], loo["move_total"])
    margin_pm = ((loo["move_hits"] * 1000) // max(loo["move_total"], 1)
                 - (loo["part_hits"] * 1000) // max(loo["part_total"], 1))
    right = sum(1 for g in grades.values() if g == "right")
    wrong = sum(1 for g in grades.values() if g == "wrong")
    base_right = sum(1 for g in baseline.values() if g == "answered")
    controls_held = all(v in ("refused", "flagged") for v in controls.values())
    checks = {
        "twelve_of_fifteen": right >= 12,
        "zero_wrong": wrong == 0,
        "baseline_zero": base_right == 0,
        "controls_held": controls_held,
        "move_beats_part": margin_pm >= 30,
    }
    deciding = (f"{right} of 15 questions answered right and {wrong} wrong "
                f"through the tool leechlean surface, against {base_right} of "
                f"15 through the GLM without it; "
                f"{sum(1 for v in controls.values() if v in ('refused', 'flagged'))}"
                f" of {len(_CONTROLS)} negative controls refused or left alone; "
                f"and on the {loo['files']}-file leave-one-file-out sample the "
                f"move model {move_pm} against the part model {part_pm} greedy "
                f"top-1 (+{margin_pm // 10}.{margin_pm % 10} points)")
    return {
        "study": STUDY,
        "checks": checks,
        "grades": grades,
        "baseline": baseline,
        "controls": controls,
        "right": right, "wrong": wrong, "baseline_right": base_right,
        "loo": loo, "part_top1": part_pm, "move_top1": move_pm,
        "margin_points_pm": margin_pm,
        "deciding_figure": deciding,
        "all_checks_hold": all(checks.values()),
    }
