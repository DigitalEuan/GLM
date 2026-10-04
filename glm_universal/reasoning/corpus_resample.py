"""``glm_universal.reasoning.corpus_resample`` -- the declared resampling.

Phase 100 (``studies/CORPUS_RESAMPLE_STUDY.md``)
------------------------------------------------
Round 9 of the order of work, candidate N1.  The native-parity and
native-words studies each re-read their marks at the close of five later
phases, and several flipped by one query as the corpus grew.  Each re-reading
was one draw.  This module takes all of them at once and says, under a rule
declared before it existed, which readings are effects and which are draws.

The method (the study's §1)
---------------------------
``census``
    every addressed declaration with a relative, asked once as a declaration
    query and once as a goal query, under every ranking of the two studies;
    for each the ranked candidates are kept down to ``depth()`` places (the
    largest file plus the largest cut-off).
``file drops``
    the sub-corpus without one Lean file: its ranking is the census ranking
    with that file filtered out (``GLM.CorpusResample.sorted_perm_filter_eq``;
    ``take_filter_take`` is why ``depth()`` places are enough), its relatives
    the full relatives less that file, its query sample re-drawn over it by
    the system's own stride rule.
``stride offsets``
    on the whole corpus, the query sample at every offset of its stride;
    the offsets partition the census (``stride_offsets_card``).

Every count is an integer and every rate a :class:`~fractions.Fraction` (D7);
no digest enters any ranking (D3).  The Lean half is
``RequestProject/GLM/CorpusResample.lean``.
"""

from __future__ import annotations

import json
import os
from array import array
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from .. import integrity
from . import lean_address as la
from . import native_words as nw
from . import retrieval as rt

__all__ = [
    "SCHEMES", "READINGS", "depth", "census", "file_drop_family",
    "stride_offset_family", "verdicts", "sign_test", "held_fixed_report",
    "filter_check", "faithfulness_report", "corpus_resample_report",
    "module_digest", "corpus_digest", "measure", "write_measurements",
    "measurements", "state", "current", "DATA_PATH",
]

STUDY = "studies/CORPUS_RESAMPLE_STUDY.md"
LEAN_FILE = "RequestProject/GLM/CorpusResample.lean"

#: The native-words rankings resampled (``native_words.RANKINGS``).
NW_SCHEMES: Tuple[str, ...] = ("text", "text_leech", "words_native",
                               "letters", "parts", "text_parts")
#: The native-parity rankings resampled.
NP_SCHEMES: Tuple[str, ...] = ("features", "native", "native2", "features2")
SCHEMES: Tuple[str, ...] = NW_SCHEMES + NP_SCHEMES

MODES: Tuple[str, ...] = ("declarations", "goals")
SAMPLE_SIZE = {"declarations": rt.SAMPLE, "goals": rt.GOAL_SAMPLE}

#: The readings, as declared in the study's §2: ``(id, first, second, ks,
#: mrr, sets, kind)``.  ``kind`` is ``ge`` (first at least second) or ``eq``.
READINGS: Tuple[Tuple[str, str, str, Tuple[int, ...], bool, Tuple[str, ...],
                      str], ...] = (
    ("a", "letters", "text", rt.K_LADDER, False, MODES, "ge"),
    ("b", "letters", "parts", rt.K_LADDER, False, MODES, "ge"),
    ("c", "words_native", "text", rt.K_LADDER, True, MODES, "ge"),
    ("d", "words_native", "text_parts", rt.K_LADDER, False, MODES, "ge"),
    ("e", "words_native", "text_leech", (5,), False, MODES, "ge"),
    ("f", "text_leech", "text", rt.K_LADDER, False, MODES, "ge"),
    ("g", "native", "features", rt.K_LADDER, True, ("declarations",), "ge"),
    ("h", "native", "features", rt.K_LADDER, False, ("goals",), "ge"),
    ("i", "native2", "features", rt.K_LADDER, False, MODES, "ge"),
    ("j", "native2", "features2", rt.K_LADDER, False, MODES, "eq"),
)

#: The declared threshold: a share of at least 95 % in both families.
THRESHOLD = Fraction(95, 100)


# ===========================================================================
#  The census
# ===========================================================================

def _names() -> Tuple[str, ...]:
    """The candidate pool: the corpus, in the address book's order, every name
    holding a profile, a structural address and a lexical address."""
    table = nw.lean_profiles()
    address = rt._point_table("address")
    lexical = rt._point_table("lexical")
    return tuple(n for n in rt.corpus()
                 if n in table and n in address and n in lexical)


@memo
def file_members() -> Dict[str, Tuple[str, ...]]:
    files = rt.file_of()
    out: Dict[str, List[str]] = {}
    for name in _names():
        out.setdefault(files[name], []).append(name)
    return {f: tuple(v) for f, v in sorted(out.items())}


def depth() -> int:
    """How far down the census keeps each ranking: the largest file plus the
    largest cut-off, which ``take_filter_take`` shows is enough."""
    members = file_members()
    largest = max((len(v) for v in members.values()), default=0)
    return largest + max(rt.K_LADDER)


def _warm() -> None:
    """Build every memoised table before the workers fork."""
    nw.lean_profiles()
    nw.lean_book()
    for scheme in ("address", "lexical", "features"):
        rt._point_table(scheme)
    rt.readback_table("address")
    rt.readback_table("lexical")
    rt.lexical_table()
    rt.relative_table()
    la.citation_index()
    la.declarations()
    file_members()


def _query_row(task: Tuple[str, str, Optional[Tuple[str, ...]]]
               ) -> Dict[str, Tuple[str, ...]]:
    """Every ranking of one query, ``depth()`` places down.

    ``task`` is ``(name, mode, candidates)``; ``candidates`` ``None`` means
    the whole pool (the census), a tuple a direct re-ranking over a
    sub-corpus (mark M2).
    """
    name, mode, candidates = task
    top = depth()
    decls = _declarations()
    table = nw.lean_profiles()
    book = nw.lean_book()
    address = rt._point_table("address")
    lexical = rt._point_table("lexical")
    features = rt._point_table("features")
    lexical_raw = rt.lexical_table()
    pool = candidates if candidates is not None else _names()
    text = rt.strip_declaration_head(decls[name].statement)
    query = nw.Profile(rt.identifier_tokens(text), book)
    if mode == "goals":
        vector = tuple(rt.goal_features(text, exclude=name))
        point = la.quantise(vector)
        lexical_vec = tuple(rt.lexical_vector(text))
        lexical_point = la.quantise(lexical_vec)
    else:
        vector = tuple(features[name])
        point = address[name]
        lexical_vec = tuple(lexical_raw[name])
        lexical_point = lexical[name]

    def leech(other: str) -> int:
        there = address.get(other)
        if there is None:
            return 0
        return la.squared_distance(point, there)

    out: Dict[str, Tuple[str, ...]] = {}
    for scheme in NW_SCHEMES:
        found = nw.rank_profiles(scheme, query, table, pool, top, name, leech)
        out[scheme] = tuple(n for n, _ in found)
    out["native"] = tuple(c.name for c in rt.rank_by_native(
        point, top, name, candidates=pool))
    out["native2"] = tuple(c.name for c in rt.rank_by_native2(
        point, lexical_point, top, name, candidates=pool))
    out["features2"] = tuple(c.name for c in rt.rank_by_features2(
        vector, lexical_vec, top, name, candidates=pool))
    out["features"] = tuple(c.name for c in rt.rank_by_point(
        features, vector, top, name, candidates=pool))
    return out


@memo
def _declarations() -> Dict[str, la.Declaration]:
    return {d.name: d for d in la.declarations()}


def jobs() -> int:
    """Every core up to eight, one when ``GLM_RESAMPLE_JOBS=1``.  The census
    does not depend on it: the rows are returned in the declared order."""
    raw = os.environ.get("GLM_RESAMPLE_JOBS")
    if raw is not None:
        try:
            return max(1, int(raw))
        except ValueError:
            return 1
    return max(1, min(8, os.cpu_count() or 1))


def _run(tasks: Sequence[Tuple[str, str, Optional[Tuple[str, ...]]]]
         ) -> List[Dict[str, Tuple[str, ...]]]:
    _warm()
    workers = jobs()
    if workers <= 1 or len(tasks) < 2:
        return [_query_row(task) for task in tasks]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_query_row, tasks, chunksize=16))


@memo
def census() -> Dict[str, object]:
    """Every census query's rankings, as indices into the pool."""
    names = _names()
    index = {n: i for i, n in enumerate(names)}
    queries = tuple(n for n in names if rt.relatives(n))
    out: Dict[str, Dict[str, Dict[str, array]]] = {}
    for mode in MODES:
        rows = _run([(n, mode, None) for n in queries])
        out[mode] = {n: {s: array("H", (index[c] for c in row[s]))
                         for s in SCHEMES}
                     for n, row in zip(queries, rows)}
    return {"names": names, "index": index, "queries": queries,
            "rankings": out, "depth": depth()}


# ===========================================================================
#  Scoring a resample
# ===========================================================================

def _sample(names: Sequence[str], size: int, offset: int,
            relatives: Mapping[str, frozenset]) -> Tuple[str, ...]:
    """The system's stride rule (``retrieval.query_sample``) at an offset."""
    if not names:
        return ()
    stride = max(1, len(names) // size)
    return tuple(n for n in names[offset::stride] if relatives.get(n))


def _tally(mode: str, queries: Sequence[str], dropped: frozenset,
           relatives: Mapping[str, frozenset]) -> Dict[str, Dict[str, object]]:
    """Hits at every cut-off and MRR@10 of every ranking on one sample."""
    data = census()
    names = data["names"]
    index = data["index"]
    dropped_ix = frozenset(index[n] for n in dropped)
    ladder = rt.K_LADDER
    top = max(ladder)
    out: Dict[str, Dict[str, object]] = {}
    for scheme in SCHEMES:
        hits = {k: 0 for k in ladder}
        rr = Fraction(0)
        for q in queries:
            rel = frozenset(index[n] for n in relatives[q])
            ranked = data["rankings"][mode][q][scheme]
            found = [c for c in ranked if c not in dropped_ix][:top]
            for k in ladder:
                if any(c in rel for c in found[:k]):
                    hits[k] += 1
            for rank, c in enumerate(found, start=1):
                if c in rel:
                    rr += Fraction(1, rank)
                    break
        count = len(queries)
        out[scheme] = {"hits": hits,
                       "mrr_at_10": rr / count if count else Fraction(0)}
    del names
    return out


def _holds(reading: Tuple, tally: Mapping[str, Mapping[str, object]],
           opposite: bool = False) -> bool:
    _id, first, second, ks, mrr, _sets, kind = reading
    a, b = tally[first], tally[second]
    if kind == "eq":
        return all(a["hits"][k] == b["hits"][k] for k in ks)
    if opposite:
        a, b = b, a
        return all(a["hits"][k] >= b["hits"][k] for k in ks)
    ok = all(a["hits"][k] >= b["hits"][k] for k in ks)
    if mrr:
        ok = ok and a["mrr_at_10"] >= b["mrr_at_10"]
    return ok


def _readings_of(tally: Mapping[str, Mapping[str, object]], mode: str
                 ) -> Dict[str, Dict[str, bool]]:
    return {r[0]: {"holds": _holds(r, tally),
                   "opposite": _holds(r, tally, opposite=True)}
            for r in READINGS if mode in r[5]}


def _relatives_without(dropped: frozenset) -> Dict[str, frozenset]:
    table = rt.relative_table()
    if not dropped:
        return dict(table)
    return {n: rel - dropped for n, rel in table.items() if n not in dropped}


@memo
def file_drop_family() -> Dict[str, object]:
    """The 170 sub-corpora, one per Lean file, each with its sample re-drawn."""
    names = census()["names"]
    rows = []
    for f, members in file_members().items():
        dropped = frozenset(members)
        relatives = _relatives_without(dropped)
        sub = tuple(n for n in names if n not in dropped)
        row = {"file": f, "dropped": len(members), "modes": {}}
        for mode in MODES:
            queries = _sample(sub, SAMPLE_SIZE[mode], 0, relatives)
            tally = _tally(mode, queries, dropped, relatives)
            row["modes"][mode] = {"queries": len(queries),
                                  "hits": {s: tally[s]["hits"] for s in SCHEMES},
                                  "readings": _readings_of(tally, mode)}
        rows.append(row)
    return {"resamples": len(rows), "rows": rows}


@memo
def stride_offset_family() -> Dict[str, object]:
    """Every offset of each query set's stride, on the whole corpus."""
    names = census()["names"]
    relatives = _relatives_without(frozenset())
    out: Dict[str, object] = {}
    for mode in MODES:
        stride = max(1, len(names) // SAMPLE_SIZE[mode])
        rows = []
        for offset in range(stride):
            queries = _sample(names, SAMPLE_SIZE[mode], offset, relatives)
            tally = _tally(mode, queries, frozenset(), relatives)
            rows.append({"offset": offset, "queries": len(queries),
                         "hits": {s: tally[s]["hits"] for s in SCHEMES},
                         "mrr": {s: tally[s]["mrr_at_10"] for s in SCHEMES},
                         "readings": _readings_of(tally, mode)})
        out[mode] = {"stride": stride, "rows": rows,
                     "covered": sum(r["queries"] for r in rows)}
    return out


# ===========================================================================
#  The sign test and the verdicts
# ===========================================================================

def sign_test(b: int, c: int) -> Fraction:
    """``min(1, 2 · Σ_{i ≤ min(b, c)} C(b + c, i) / 2^(b + c))``, exactly
    (``GLM.CorpusResample.signTest``)."""
    n = b + c
    tail = sum(comb(n, i) for i in range(min(b, c) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** n))


@memo
def discordance() -> Dict[str, Dict[str, Dict[str, object]]]:
    """For every reading on every set, the census discordance at ``k = 5``."""
    data = census()
    index = data["index"]
    relatives = rt.relative_table()
    out: Dict[str, Dict[str, Dict[str, object]]] = {}
    for reading in READINGS:
        rid, first, second = reading[0], reading[1], reading[2]
        out[rid] = {}
        for mode in reading[5]:
            b = c = 0
            for q in data["queries"]:
                rel = frozenset(index[n] for n in relatives[q])
                ranked = data["rankings"][mode][q]
                hit_a = any(x in rel for x in ranked[first][:5])
                hit_b = any(x in rel for x in ranked[second][:5])
                if hit_a and not hit_b:
                    b += 1
                elif hit_b and not hit_a:
                    c += 1
            out[rid][mode] = {"first_only": b, "second_only": c,
                              "sign_test": sign_test(b, c)}
    return out


def _share(rows: Sequence[Mapping[str, object]], rid: str, key: str) -> Fraction:
    total = len(rows)
    if not total:
        return Fraction(0)
    return Fraction(sum(1 for r in rows if r["readings"][rid][key]), total)


def _share_k(rows: Sequence[Mapping[str, object]], reading: Tuple, k: int,
             relation: str) -> Fraction:
    """Post hoc, not part of the declared rule: the share of resamples in
    which the first ranking's hits at one cut-off stand in ``relation``
    (``ge``, ``gt`` or ``lt``) to the second's."""
    first, second = reading[1], reading[2]
    total = len(rows)
    if not total:
        return Fraction(0)
    count = 0
    for r in rows:
        a, b = r["hits"][first][k], r["hits"][second][k]
        if ((relation == "ge" and a >= b) or (relation == "gt" and a > b)
                or (relation == "lt" and a < b)):
            count += 1
    return Fraction(count, total)


@memo
def verdicts() -> Dict[str, Dict[str, Dict[str, object]]]:
    """The declared rule, applied to every reading on every query set."""
    drops = file_drop_family()["rows"]
    offsets = stride_offset_family()
    disc = discordance()
    out: Dict[str, Dict[str, Dict[str, object]]] = {}
    for reading in READINGS:
        rid, kind = reading[0], reading[6]
        out[rid] = {}
        for mode in reading[5]:
            f_rows = [r["modes"][mode] for r in drops]
            s_rows = offsets[mode]["rows"]
            share_f = _share(f_rows, rid, "holds")
            share_s = _share(s_rows, rid, "holds")
            opp_f = _share(f_rows, rid, "opposite")
            opp_s = _share(s_rows, rid, "opposite")
            if kind == "eq":
                verdict = ("holds everywhere" if share_f == 1 and share_s == 1
                           else "fails")
            elif share_f >= THRESHOLD and share_s >= THRESHOLD:
                verdict = "effect"
            elif opp_f >= THRESHOLD and opp_s >= THRESHOLD:
                verdict = "effect against"
            else:
                verdict = "draw"
            per_k = {}
            for k in rt.K_LADDER:
                per_k[k] = {
                    "ge_file_drops": _share_k(f_rows, reading, k, "ge"),
                    "ge_offsets": _share_k(s_rows, reading, k, "ge"),
                    "gt_file_drops": _share_k(f_rows, reading, k, "gt"),
                    "gt_offsets": _share_k(s_rows, reading, k, "gt"),
                    "lt_file_drops": _share_k(f_rows, reading, k, "lt"),
                    "lt_offsets": _share_k(s_rows, reading, k, "lt"),
                }
            out[rid][mode] = {"per_k": per_k,
                              "share_file_drops": share_f,
                              "share_offsets": share_s,
                              "opposite_file_drops": opp_f,
                              "opposite_offsets": opp_s,
                              "verdict": verdict,
                              "discordance": disc[rid][mode]}
    return out


# ===========================================================================
#  The marks' own checks
# ===========================================================================

@memo
def faithfulness_report() -> Dict[str, object]:
    """M1: offset 0 on the whole corpus reproduces both studies' figures."""
    from . import native_parity as npy
    offsets = stride_offset_family()
    words = nw.lean_report()
    decl_np = npy.declaration_report()
    goal_np = npy.goal_report()
    mismatches: List[str] = []
    for mode, np_block in (("declarations", decl_np), ("goals", goal_np)):
        row = offsets[mode]["rows"][0]
        for scheme in NW_SCHEMES:
            want = words[mode]["schemes"][scheme]
            if (row["hits"][scheme] != want["hits"]
                    or row["mrr"][scheme] != want["mrr_at_10"]):
                mismatches.append(f"{mode}:{scheme}")
        for scheme in NP_SCHEMES:
            want = np_block["schemes"][scheme]
            if (row["hits"][scheme] != want["hits"]
                    or row["mrr"][scheme] != want["mrr_at_10"]):
                mismatches.append(f"{mode}:{scheme}")
    return {"met": not mismatches, "mismatches": mismatches,
            "pool": len(census()["names"]),
            "corpus": len(rt.corpus())}


def _check_files() -> Tuple[str, ...]:
    """M2's five declared files: the largest, the smallest, and the first,
    middle and last of the sorted list (ties by name; no file twice)."""
    members = file_members()
    ordered = sorted(members)
    by_size = sorted(members, key=lambda f: (len(members[f]), f))
    picks = [by_size[-1], by_size[0], ordered[0], ordered[len(ordered) // 2],
             ordered[-1]]
    out: List[str] = []
    for f in picks:
        if f not in out:
            out.append(f)
    return tuple(out)


@memo
def filter_check() -> Dict[str, object]:
    """M2: a direct re-ranking over the sub-corpus equals the filtered census."""
    data = census()
    names = data["names"]
    index = data["index"]
    top = max(rt.K_LADDER)
    rows = []
    for f in _check_files():
        dropped = frozenset(file_members()[f])
        relatives = _relatives_without(dropped)
        sub = tuple(n for n in names if n not in dropped)
        queries = _sample(sub, SAMPLE_SIZE["declarations"], 0, relatives)
        direct = _run([(q, "declarations", sub) for q in queries])
        dropped_ix = frozenset(index[n] for n in dropped)
        differ = 0
        for q, row in zip(queries, direct):
            for scheme in SCHEMES:
                ranked = data["rankings"]["declarations"][q][scheme]
                filtered = [names[c] for c in ranked if c not in dropped_ix][:top]
                if list(row[scheme][:top]) != filtered:
                    differ += 1
        rows.append({"file": f, "queries": len(queries), "differ": differ})
    return {"files": rows, "met": all(r["differ"] == 0 for r in rows)}


@memo
def held_fixed_report() -> Dict[str, object]:
    """M5: how many structural feature vectors a rebuilt sub-corpus changes.

    For each file, the citation index, the citation graph and the fan-in are
    rebuilt over the declarations outside it, exactly as
    ``lean_address.feature_table`` builds them, and every declaration of the
    pool outside the file whose clamped feature vector differs is counted.
    """
    decls = la.declarations()
    pool = set(_names())
    stored = rt._point_table("features")
    tokens = {d.name: frozenset(la._TOKEN.findall(d.statement + "\n" + d.body))
              for d in decls}
    def changed_without(f: Optional[str]) -> int:
        kept = [d for d in decls if d.file != f]
        full = {d.name for d in kept}
        short_counts: Dict[str, int] = {}
        for d in kept:
            short_counts[d.short] = short_counts.get(d.short, 0) + 1
        index: Dict[str, str] = {name: name for name in full}
        for d in kept:
            if short_counts[d.short] == 1:
                index.setdefault(d.short, d.name)
            tail = d.name.split(".")
            if len(tail) >= 2:
                index.setdefault(".".join(tail[-2:]), d.name)
        graph: Dict[str, set] = {}
        for d in kept:
            found = set()
            for token in tokens[d.name]:
                target = index.get(token)
                if target is None and "." in token:
                    target = index.get(token.rsplit(".", 1)[-1])
                if target is not None and target != d.name:
                    found.add(target)
            graph[d.name] = found
        fan_in: Dict[str, int] = {name: 0 for name in graph}
        for targets in graph.values():
            for target in targets:
                fan_in[target] = fan_in.get(target, 0) + 1
        changed = 0
        for d in kept:
            if d.name not in pool:
                continue
            vector = la.features_of(d, len(graph[d.name]), fan_in[d.name])
            if tuple(vector) != tuple(stored[d.name]):
                changed += 1
        return changed

    baseline = changed_without(None)
    per_file = [{"file": f, "changed": changed_without(f)}
                for f in file_members()]
    counts = [r["changed"] for r in per_file]
    return {"files": per_file, "baseline_changed": baseline,
            "largest": max(counts, default=0),
            "total": sum(counts),
            "files_with_change": sum(1 for c in counts if c)}


# ===========================================================================
#  The report
# ===========================================================================

@memo
def corpus_resample_report() -> Dict[str, object]:
    """Every declared mark of the study, measured."""
    data = census()
    drops = file_drop_family()
    offsets = stride_offset_family()
    verdict = verdicts()
    faithful = faithfulness_report()
    exact = filter_check()
    held = held_fixed_report()
    every_with_relative = sum(1 for n in data["names"] if rt.relatives(n))
    covered = all(offsets[m]["covered"] == len(data["queries"]) for m in MODES)
    marks = {
        "M1": bool(faithful["met"]),
        "M2": bool(exact["met"]),
        "M3": (drops["resamples"] == len(file_members())
               and covered and len(data["queries"]) == every_with_relative
               and all(r["modes"][m]["queries"] > 0 for r in drops["rows"]
                       for m in MODES)),
        "M4": (all(v["verdict"] in ("effect", "effect against", "draw",
                                    "holds everywhere")
                   for block in verdict.values() for v in block.values())
               and all(v["verdict"] == "holds everywhere"
                       for v in verdict["j"].values())),
        "M5": (len(held["files"]) == len(file_members())
               and held["baseline_changed"] == 0),
    }
    return {
        "pool": len(data["names"]), "census": len(data["queries"]),
        "depth": data["depth"], "files": len(file_members()),
        "strides": {m: offsets[m]["stride"] for m in MODES},
        "offset_queries": {m: [r["queries"] for r in offsets[m]["rows"]]
                           for m in MODES},
        "drop_queries": {m: [r["modes"][m]["queries"] for r in drops["rows"]]
                         for m in MODES},
        "verdicts": verdict, "faithfulness": faithful, "filter_check": exact,
        "held_fixed": held, "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "study": STUDY, "lean_file": LEAN_FILE,
    }


# ===========================================================================
#  The cache, guarded by a digest of the measuring code
# ===========================================================================

DATA_PATH = Path(__file__).resolve().parent / "_data" / "corpus_resample.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/corpus_resample.py",
    "reasoning/native_words.py",
    "reasoning/native_parity.py",
    "reasoning/retrieval.py",
    "reasoning/lean_address.py",
    "substrate/golay_decode.py",
    "reasoning/_data/lean_addresses.json",
    "reasoning/_data/lean_lexical_addresses.json",
)


def module_digest() -> str:
    """The measuring code only; the corpus is a dated observation, as in
    ``native_words.module_digest``."""
    root = Path(__file__).resolve().parent.parent
    code = [root / name for name in _SOURCES
            if name.endswith(".py") and (root / name).exists()]
    return integrity.tree_digest(code, root)


def corpus_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    books = integrity.tree_digest([root / name for name in _SOURCES
                                   if not name.endswith(".py")
                                   and (root / name).exists()], root)
    return integrity.sha256_hex("|".join((books, la.tree_digest()))
                                .encode("utf-8"))


def _summary() -> Dict[str, object]:
    """What is stored: the report without the per-query census."""
    report = corpus_resample_report()
    return dict(report)


def measure() -> Dict[str, object]:
    payload = _summary()
    payload["source_digest"] = module_digest()
    payload["corpus_digest"] = corpus_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    global _cache
    taken = measure()
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(nw._freeze(taken), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = nw._thaw(loaded) if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
