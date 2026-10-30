"""``glm_universal.runtime.stepwise_five`` -- the measurement of round five
of the stepwise planner: frames generated from a declaration, and the
widenings written as entries in it.

``studies/DECLARED_FRAMES_STUDY.md`` (Phase 91) declares nine marks over the
corpus of :mod:`glm_universal.evaluation.stepwise_five_cases`; this module
takes the eight that are measured (the ninth is the Lean file,
``RequestProject/GLM/DeclaredFrames.lean``).  The declaration and its
generated reader live in :mod:`glm_universal.runtime.frame_declarations`;
the builders the frames name live in :mod:`glm_universal.runtime.stepwise`
and the column-3 script's readers in
:mod:`glm_universal.reasoning.stepwise_script`.

Three controls:

* **The hand-written readers** -- rounds three and four's own frames
  (:data:`glm_universal.runtime.frame_declarations.GENERATED` off): what the
  generated reader, restricted to rounds three and four, must equal on every
  text (mark D1); and **the emptied declaration**, which must read no fold.
* **Round four's reader** -- round five switched off
  (:data:`glm_universal.runtime.frame_declarations.ROUND_FIVE`): what the
  corpus met before this round (marks D2-D5).
* **The declaration without its round-five entries** -- the round left on,
  its entries removed (:data:`~glm_universal.runtime.frame_declarations.
  DECLARE_ROUND_FIVE` off): every widening must hang on an entry, so this
  must give round four's verdict on every case (mark D5).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import frame_declarations as fd
from . import router
from . import stepwise as sw
from . import stepwise_four as s4
from ..reasoning import stepwise_script as ss

__all__ = ["round_four_reader", "without_round_five_entries",
           "handwritten_reader", "corpus_texts", "generated_report",
           "orders_report", "superlatives_report", "bounds_report",
           "classes_report", "prefixes_report", "molecules_report",
           "follow_ups_report", "widenings_report", "completions_report",
           "answered_chains", "scripts_report", "interference_report",
           "stepwise_five_report", "FOLD_TREES"]

#: The tree kinds a fold frame builds.
FOLD_TREES = ("fold", "fold4", "top", "bounds")


class _flags:
    """Set flags of :mod:`frame_declarations` for a ``with`` block."""

    def __init__(self, **flags):
        self._flags = flags

    def __enter__(self):
        self._saved = {k: getattr(fd, k) for k in self._flags}
        for k, v in self._flags.items():
            setattr(fd, k, v)
        return self

    def __exit__(self, *exc) -> bool:
        for k, v in self._saved.items():
            setattr(fd, k, v)
        return False


def round_four_reader():
    """The stepwise planner as round four left it: round five off."""
    return _flags(ROUND_FIVE=False)


def without_round_five_entries():
    """Round five on, its declaration entries removed (D5's control)."""
    return _flags(DECLARE_ROUND_FIVE=False)


def handwritten_reader():
    """Rounds three and four's hand-written readers, round five off."""
    return _flags(GENERATED=False, ROUND_FIVE=False)


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


# ---------------------------------------------------------------------------
# mark D1: the generated reader against the hand-written one
# ---------------------------------------------------------------------------

def corpus_texts() -> List[Tuple[str, str]]:
    """``(source, text)`` of every question of the stepwise corpora of
    rounds one to five and of the router's declared question sets."""
    from ..evaluation import (stepwise_cases, stepwise_five_cases,
                              stepwise_four_cases, stepwise_three_cases,
                              stepwise_two_cases)
    out: List[Tuple[str, str]] = []
    seen = set()
    for mod in (stepwise_cases, stepwise_two_cases, stepwise_three_cases,
                stepwise_four_cases, stepwise_five_cases):
        name = mod.__name__.rsplit(".", 1)[1]
        for attr in sorted(dir(mod)):
            if not attr.endswith("_CASES"):
                continue
            for case in getattr(mod, attr):
                for item in case[1:]:
                    if isinstance(item, str) and " " in item and \
                            item not in seen:
                        seen.add(item)
                        out.append((name, item))
    for name, texts in router._declared_sets().items():
        for t in texts:
            if t not in seen:
                seen.add(t)
                out.append((f"router:{name}", t))
    return out


def _segment_outcome(seg: str):
    try:
        return ("READ", tuple(sw.segment_readings(seg)))
    except sw.Refused as r:
        return ("REFUSED", r.name)
    except Exception as e:                            # pragma: no cover
        return ("ERROR", type(e).__name__)


def _outcomes(text: str):
    try:
        segs = sw.split_then(text)
    except sw.Refused as r:
        return (("SPLIT_REFUSED", r.name),)
    return tuple(_segment_outcome(s) for s in segs)


def _has_fold(outcome) -> bool:
    def walk(t):
        if not isinstance(t, tuple):
            return False
        if t and t[0] in FOLD_TREES:
            return True
        return any(walk(x) for x in t[1:])
    for kind, body in outcome:
        if kind == "READ" and any(walk(t) for t in body):
            return True
    return False


def generated_report() -> Dict[str, object]:
    """Mark D1: on every corpus text, the generated reader restricted to
    rounds three and four gives the hand-written readers' readings; with
    the declaration emptied it reads no fold."""
    from . import declared_frames as df
    texts = corpus_texts()
    rows, differ = [], []
    fold_texts = 0
    for source, text in texts:
        with handwritten_reader():
            hand = _outcomes(text)
        with round_four_reader():
            gen = _outcomes(text)
        same = hand == gen
        folds = _has_fold(hand)
        fold_texts += folds
        if not same:
            differ.append({"source": source, "text": text,
                           "hand": repr(hand)[:300], "generated":
                           repr(gen)[:300]})
        rows.append({"source": source, "text": text, "same": same,
                     "fold": folds})
    emptied_folds = []
    fold_questions = 0
    with fd.emptied():
        for source, text in texts:
            if source not in ("stepwise_three_cases", "stepwise_four_cases",
                              "stepwise_five_cases"):
                continue
            now = _outcomes(text)
            if _has_fold(now):
                emptied_folds.append(text)
    for source, text in texts:
        if source in ("stepwise_three_cases", "stepwise_four_cases",
                      "stepwise_five_cases") and _has_fold(_outcomes(text)):
            fold_questions += 1
    census = fd.declaration_census()
    return {"texts": len(texts), "identical": sum(r["same"] for r in rows),
            "differ": differ, "fold_texts": fold_texts,
            "fold_questions_live": fold_questions,
            "emptied_fold_reads": len(emptied_folds),
            "emptied_examples": emptied_folds[:5],
            "declaration": census,
            "sets_round_three": len(df.DECLARED_SETS),
            "sets_round_five": len(df.UNION_SETS),
            "met": len(differ) == 0 and not emptied_folds
            and fold_questions > 0}


# ---------------------------------------------------------------------------
# marks D2-D5: the corpus, and round four's reader
# ---------------------------------------------------------------------------

def _rows(session, cases) -> Dict[str, object]:
    rows = []
    for cid, q, want in cases:
        a = sw.answer(session, q)
        with round_four_reader():
            before = sw.answer(session, q)
            routed_before = router.route(session, q)
        with without_round_five_entries():
            bare = sw.answer(session, q)
        routed = router.route(session, q)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want),
                     "round_four": list(_verdict(before)),
                     "without_entries": list(_verdict(bare)),
                     "machine_before": routed_before.text if
                     routed_before.answered else None,
                     "machine_now": routed.text if routed.answered else None,
                     "machine_by": getattr(routed.solution, "kind", None)
                     if routed.answered else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "round_four_answers": sum(1 for r in rows
                                      if r["round_four"][0] == "ANSWER"),
            "entries_hold": sum(1 for r in rows
                                if r["without_entries"] == r["round_four"]),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"] is not None),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "rows": rows}


def orders_report(session) -> Dict[str, object]:
    """Mark D2: the further order statistics."""
    from ..evaluation.stepwise_five_cases import ORDER_CASES
    return _rows(session, ORDER_CASES)


def superlatives_report(session) -> Dict[str, object]:
    """Mark D3: superlatives and the top k."""
    from ..evaluation.stepwise_five_cases import SUPERLATIVE_CASES
    return _rows(session, SUPERLATIVE_CASES)


def bounds_report(session) -> Dict[str, object]:
    """Mark D4: bounds and the present-rows parity count."""
    from ..evaluation.stepwise_five_cases import BOUND_CASES
    return _rows(session, BOUND_CASES)


def classes_report(session) -> Dict[str, object]:
    """Mark D5: the declared unions."""
    from ..evaluation.stepwise_five_cases import CLASS_CASES
    return _rows(session, CLASS_CASES)


def prefixes_report(session) -> Dict[str, object]:
    """Mark D5: the remaining SI prefixes."""
    from ..evaluation.stepwise_five_cases import PREFIX_CASES
    return _rows(session, PREFIX_CASES)


def molecules_report(session) -> Dict[str, object]:
    """Mark D5: the comparatives over the molecule table."""
    from ..evaluation.stepwise_five_cases import MOLECULE_CASES
    return _rows(session, MOLECULE_CASES)


def follow_ups_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_five_cases import FOLLOW_UP_CASES
    rows = []
    for cid, first, second, want in FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def widenings_report(reports: Dict[str, Dict[str, object]]
                     ) -> Dict[str, object]:
    """Mark D5's second half over D2-D5's rows: with the round-five
    entries removed, every case gets round four's verdict."""
    rows = [r for rep in reports.values() for r in rep["rows"]]
    off = [r["id"] for r in rows if r["without_entries"] != r["round_four"]]
    return {"cases": len(rows), "hold": len(rows) - len(off),
            "not_holding": off,
            "round_four_answers": sum(1 for r in rows
                                      if r["round_four"][0] == "ANSWER"),
            "met": not off}


# ---------------------------------------------------------------------------
# mark D6: the completions
# ---------------------------------------------------------------------------

def _fills(seed: int):
    """A fixed linear congruential sequence (Numerical Recipes constants)."""
    state = seed & 0xFFFFFFFF
    while True:
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        yield state


def completed(fn: str, column: Sequence[Fraction]) -> Fraction:
    """A fold of a complete column, computed directly and independently
    of the planner: sums, means and parity counts, and the order statistics
    by sorting (the quartile as the median of the lower or upper half, the
    middle left out of both when the count is odd)."""
    p = sorted(column)
    n = len(p)
    if fn == "sum":
        return sum(p, Fraction(0))
    if fn == "mean":
        return sum(p, Fraction(0)) / n
    if fn in ("odd", "even"):
        want = 1 if fn == "odd" else 0
        return Fraction(sum(1 for v in p if int(v) % 2 == want))

    def median(xs):
        m = len(xs)
        return xs[m // 2] if m % 2 else (xs[m // 2 - 1] + xs[m // 2]) / 2
    if fn == "median":
        return median(p)
    if fn == "q1":
        return median(p[:n // 2])
    if fn == "q3":
        return median(p[n - n // 2:])
    side, _, k = fn.partition(":")
    k = int(k) if k else 1
    return p[n - k] if side == "max" else p[k - 1]


def _interval(value) -> Tuple[Fraction, Fraction]:
    if isinstance(value, Fraction):
        return value, value
    lo, hi = str(value)[len("between "):].split(" and ")
    return ss.parse_value(lo), ss.parse_value(hi)


def _inputs(session, d) -> Tuple[List[Fraction], int]:
    from . import declared_frames as df
    fs = session.field_surface
    table = fs.table_by_name(df.ELEMENT_TABLE).rows()
    vals, holes = [], 0
    for k, _n in df.members(fs, d["set"]):
        v = table[k].get(d["field"])
        if v is None:
            holes += 1
        else:
            vals.append(Fraction(v))
    return vals, holes


def completions_report(session, per_answer: Optional[int] = None
                       ) -> Dict[str, object]:
    """Mark D6: every bounded answer of the corpus against completions of
    its holes, both extreme completions among them."""
    from ..evaluation import stepwise_five_cases as C
    per_answer = per_answer or C.COMPLETIONS_PER_ANSWER
    out = []
    for cid, q, _want in C.all_cases():
        a = sw.answer(session, q)
        if not a.answered:
            continue
        step = next((s for s in reversed(a.chain.steps) if s.op == "fold"),
                    None)
        if step is None or not step.detail.get("bounded"):
            continue
        d = step.detail
        fn = d["fn"]
        vals, holes = _inputs(session, d)
        lo, hi = _interval(step.value)
        gen = _fills(sum(map(ord, cid)))
        if d.get("range"):
            L, U = (ss.parse_value(x) for x in d["range"])
            low_col, high_col = vals + [L] * holes, vals + [U] * holes

            def fill():
                return L + (U - L) * Fraction(next(gen) % 10 ** 6, 10 ** 6)
        elif fn in ("odd", "even"):
            par = 1 if fn == "odd" else 0
            low_col = vals + [Fraction(1 - par)] * holes
            high_col = vals + [Fraction(par)] * holes

            def fill():
                return Fraction(next(gen) % 1000)
        else:
            least, most = min(vals), max(vals)
            span = most - least + 1
            low_col = vals + [least - span] * holes
            high_col = vals + [most + span] * holes

            def fill():
                return least - span + Fraction(next(gen) % 10 ** 6,
                                               10 ** 6) * 3 * span
        columns = [low_col, high_col]
        while len(columns) < per_answer:
            columns.append(vals + [fill() for _ in range(holes)])
        inside, seen = 0, set()
        for col in columns:
            got = completed(fn, col)
            seen.add(got)
            inside += lo <= got <= hi
        low, high = completed(fn, low_col), completed(fn, high_col)
        out.append({"id": cid, "fn": fn, "holes": holes,
                    "interval": [ss.render_value(lo), ss.render_value(hi)],
                    "completions": len(columns), "inside": inside,
                    "low_attained": low == lo, "high_attained": high == hi,
                    "distinct_values": len(seen),
                    "ok": inside == len(columns) and low == lo and high == hi})
    return {"bounded": out, "per_answer": per_answer,
            "met": bool(out) and all(r["ok"] for r in out)}


# ---------------------------------------------------------------------------
# mark D7: the scripts
# ---------------------------------------------------------------------------

def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the round-five corpus, with its case id."""
    from ..evaluation import stepwise_five_cases as C
    out = []
    for cid, q, _want in C.all_cases():
        a = sw.answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    for cid, first, second, _ in C.FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Every answered chain's column-3 script in a fresh ``python3 -I``, and
    every mutation of each."""
    import re
    from .python_tct import run_column3
    from .tct_engine import package_root
    root = str(package_root())
    chains = answered_chains(session)
    if limit is not None:
        chains = chains[:limit]
    verified, failed, aligned, steps = 0, [], 0, 0
    caught = {k: 0 for k in ss.MUTATION_KINDS}
    built = {k: 0 for k in ss.MUTATION_KINDS}
    escaped: List[str] = []
    for cid, chain in chains:
        got = run_column3(ss.render_script(chain, root))
        steps += len(chain.steps)
        m = re.search(r"ALIGNED (\d+) of (\d+)", got["stdout"])
        aligned += int(m.group(1)) if m else 0
        if got["verified"]:
            verified += 1
        else:
            failed.append(cid)
        for kind, data in ss.mutants(chain).items():
            built[kind] += 1
            bad = run_column3(ss.render_script(chain, root, data))
            if bad["verified"]:
                escaped.append(f"{cid}:{kind}")
            else:
                caught[kind] += 1
    return {"chains": len(chains), "verified": verified, "failed": failed,
            "steps": steps, "aligned": aligned, "mutants": built,
            "caught": caught, "escaped": escaped}


# ---------------------------------------------------------------------------
# mark D8: non-interference
# ---------------------------------------------------------------------------

def moved_report(session) -> Dict[str, object]:
    """The three declared moves: each gets its new verdict, and its earlier
    one with round five switched off."""
    from ..evaluation.stepwise_five_cases import MOVED
    rows = []
    for (corpus, cid), (q, before, now) in MOVED.items():
        got = _verdict(sw.answer(session, q))
        with round_four_reader():
            old = _verdict(sw.answer(session, q))
        rows.append({"corpus": corpus, "id": cid, "now": list(got),
                     "declared_now": list(now), "with_round_five_off":
                     list(old), "declared_before": list(before),
                     "ok": _ok(got, now) and _ok(old, before)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def interference_report(session) -> Dict[str, object]:
    """Round four's corpus through the round-five module (its marks H1-H4
    re-taken without scripts, the declared moves counted as declared), and
    through it rounds one to three and the router's declared sets; the
    router's stepwise rows compared with round four's reader."""
    four = {
        "orders": s4.orders_report(session),
        "bounded": s4.bounded_report(session),
        "ranks": s4.ranks_report(session),
        "present": s4.present_report(session),
        "follow_ups": s4.follow_ups_report(session),
    }
    below = s4.interference_report(session)
    with round_four_reader():
        router_before = sw.interference_report(session)
    router_now = sw.interference_report(session)
    key = lambda r: (r["question"], tuple(r["stepwise"]))  # noqa: E731
    before_rows = {r["question"]: r for r in router_before["rows"]}
    changed = [r["question"] for r in router_now["rows"]
               if r["question"] not in before_rows
               or tuple(before_rows[r["question"]]["stepwise"])
               != tuple(r["stepwise"])]
    held_four = all(v["met"] == v["cases"] for v in four.values())
    moved = moved_report(session)
    return {"round_four": {k: {"cases": v["cases"], "met": v["met"]}
                           for k, v in four.items()},
            "round_four_held": held_four,
            "round_three_held": below["round_three_held"],
            "round_two_held": below["round_two_held"],
            "round_one_held": below["round_one_held"],
            "router_read": router_now["read"],
            "router_read_before": router_before["read"],
            "router_questions": router_now["questions"],
            "router_rows_changed": changed,
            "turned_into_answers": router_now["turned_into_answers"],
            "turned_into_answers_before":
                router_before["turned_into_answers"],
            "declared_refusals_answered":
                router_now["declared_refusals_answered"],
            "moved": moved,
            "met": held_four and below["round_three_held"]
            and below["round_two_held"] and below["round_one_held"]
            and moved["met"] == moved["cases"]
            and not router_now["declared_refusals_answered"]
            and sorted(router_now["turned_into_answers"])
            == sorted(router_before["turned_into_answers"])}


def stepwise_five_report(scripts: bool = True,
                         interference: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/DECLARED_FRAMES_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    report: Dict[str, object] = {"generated": generated_report()}
    parts = {
        "orders": orders_report(session),
        "superlatives": superlatives_report(session),
        "bounds": bounds_report(session),
        "classes": classes_report(session),
        "prefixes": prefixes_report(session),
        "molecules": molecules_report(session),
    }
    report.update(parts)
    report["follow_ups"] = follow_ups_report(session)
    report["widenings"] = widenings_report(parts)
    report["completions"] = completions_report(session)
    if interference:
        report["interference"] = interference_report(session)
    if scripts:
        report["scripts"] = scripts_report(session)
    report["study"] = "studies/DECLARED_FRAMES_STUDY.md"
    report["lean_file"] = "RequestProject/GLM/DeclaredFrames.lean"
    return report
