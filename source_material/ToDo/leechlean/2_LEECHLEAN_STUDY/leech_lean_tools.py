"""``glm_universal.reasoning.leech_lean_tools`` -- the leechlean addressing of
this repository's Lean development on the GLM's answering path: ``tool
leechlean``.

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22; absorbed ahead of the owner's Lean build -- every answer says
so while the register of provisional families lists the item).*

What it answers
---------------
``tool leechlean address PART``
    the Leech address of a recurring part of this repository's Lean
    development (a token, bigram, frame or tactic head of the 39,992-part
    codebook): the 24 coordinates, the lattice energy |A|²/8, the corpus
    count, and the Λ/2Λ class with its type (2 = one of the 98,280
    minimal-vector classes the Griess algebra's 98,280-piece is indexed by,
    3 = q = 1, 4 = a frame class) -- all through the substrate's exact
    machinery.
``tool leechlean file PATH``
    a Lean file of this repository encoded as its address stream: the tick
    count, the byte-exact round trip, the on-lattice count, the journey's
    energy, path² and net displacement², and the verification frontier (how
    many of its ticks the library attests).
``tool leechlean moves PATH``
    the moves d = B − A of the file's stream: counts, the mean |d|², the
    class types met, the class law checked live on the file's two most
    common moves, and whether their composed move is back in the corpus
    repertoire.
``tool leechlean continue PART``
    the library's continuations of a part (heaviest joinings first) --
    **unverified graph proposals**, labelled as such, never library
    material.
``tool leechlean verify PATH [flip K | slip]``
    the congruence sieve and the class-assisted repair over the file's
    first ticks: clean (0 false alarms), corrupted by a ±K flip on one
    coordinate of every tick (caught by the parity congruence, repaired),
    or slipped by a minimal vector (on the lattice -- invisible to the
    sieve, caught by the Λ/2Λ class syndrome, repaired).
``tool leechlean attest PART``
    the declaration frames a part is attested under in the library, with
    file counts -- syntactic attestation, never a proof.
``tool leechlean stitch SNIPPET``
    authoring against the library: every tick classified (context-verified /
    part-known / new), genuinely new parts addressed on the fly on the
    lattice (the extended codebook stays injective), and the projection
    checked byte-exact.
``tool leechlean state``
    the addressing itself: the codebook and library sizes, the parts per
    granularity, the universal core (the parts in at least 400 of the 442
    corpus files), and the energy law on the two anchor parts (the one-bit
    sphere and a rare import word).

Nothing here claims a proof: the library's notion of verified is syntactic
attestation under a frame, stated as such.  Nothing constructs a float; the
figures are integers, strings and booleans.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import leech_lean as LL

#: ``(ok, text, figures)``, the shape every tool of the toolbox returns.
Answer = Tuple[bool, str, Dict[str, object]]

#: The Lean checks this surface rests on (compiled standalone under the
#: pinned toolchain; the owner's build has to confirm them).
LEAN_GOLAY = "RequestProject/GLM/IntakeChecks/LeechLeanGolay.lean"
LEAN_CODEC = "RequestProject/GLM/IntakeChecks/LeechLeanCodec.lean"

USAGE = ("leechlean: the leechlean addressing of this repository's Lean "
         "development. Reads: address PART | file PATH | moves PATH | "
         "continue PART | verify PATH [flip K | slip] | attest PART | "
         "stitch SNIPPET | state")

_KINDS = ("kw", "ident", "sym", "num", "str", "ws", "comment", "b", "f", "t")


def build_note() -> Optional[str]:
    """The note every answer carries while the register of provisional
    families lists the item (absorbed ahead of the owner's build)."""
    from ..wheels import provisional_status
    return provisional_status(MODULE := LL.MODULE)


def _finish(ok: bool, text: str, figures: Dict[str, object]) -> Answer:
    note = build_note()
    if note:
        figures = dict(figures, provisional=str(note))
        text = f"{text} [{note}]"
    return ok, text, figures


def _find_part(arg: str) -> Optional[str]:
    """A part key from a name: the key itself, or the first kind-prefixed
    hit (``theorem`` -> ``kw:theorem``)."""
    cb = LL.codebook_state()
    a = " ".join(arg.split())
    if a in cb.parts:
        return a
    for kind in _KINDS:
        key = f"{kind}:{a}"
        if key in cb.parts:
            return key
    return None


def _part_text(key: str) -> str:
    return key.split(":", 1)[1]


# ---------------------------------------------------------------------------
# tool leechlean address PART
# ---------------------------------------------------------------------------

def _address(arg: str) -> Answer:
    key = _find_part(arg)
    if key is None:
        return _finish(False, f"leechlean: refused -- {arg!r} is not a part "
                       f"of the corpus codebook (the 39,992 recurring parts "
                       f"of this repository's Lean development); " + USAGE,
                       {"status": "refused"})
    p = LL.part_info(key)
    assert p is not None
    try:
        cls = LL.class_of(p.address)
        ctype = LL.class_type_of(p.address)
    except ValueError:
        cls, ctype = -1, -1     # a non-lattice address cannot occur (checked)
    on = LL.is_lattice_point(p.address)
    names = {0: "the zero class", 2: "type 2 (one of the 98,280 minimal-"
             "vector classes, the Griess algebra's 98,280-piece index)",
             3: "type 3 (q = 1)", 4: "type 4 (a frame class)"}
    text = (f"the Leech address of the part {key!r} (granularity {p.grade}, "
            f"{p.count:,} uses in the 442-file corpus): "
            f"A = {list(p.address)} -- on the lattice: {on}; lattice energy "
            f"|A|^2/8 = {p.energy} (surprisal law: one bit = 4 units); the "
            f"Lambda/2Lambda class {cls} is {names.get(ctype, ctype)}"
            + (" (displaced outward from its target by the codebook's "
               "collision rule)" if p.displaced else ""))
    return _finish(True, text, {"status": "ok", "part": key,
                                "address": list(p.address),
                                "energy": p.energy, "count": p.count,
                                "grade": p.grade, "class": cls,
                                "class_type": ctype, "on_lattice": on})


# ---------------------------------------------------------------------------
# tool leechlean file PATH | moves PATH
# ---------------------------------------------------------------------------

def _file(arg: str) -> Answer:
    try:
        path = LL.resolve_lean_path(arg)
    except FileNotFoundError as exc:
        return _finish(False, f"leechlean: refused -- {exc}; " + USAGE,
                       {"status": "refused"})
    try:
        rep = LL.file_report(path)
    except KeyError as exc:
        return _finish(False, f"leechlean: refused -- {path.name} has a part "
                       f"outside the corpus codebook ({exc.args[0]!r}); the "
                       f"codebook addresses the 442-file corpus it was built "
                       f"from", {"status": "refused"})
    rel = path.relative_to(LL.C.REPOSITORY_ROOT) if str(path).startswith(
        str(LL.C.REPOSITORY_ROOT)) else path
    text = (f"the file {rel} as a leechlean address stream: {rep.ticks:,} "
            f"ticks, every address a true Leech lattice point "
            f"({rep.on_lattice}/{rep.ticks}), and the stream decodes back "
            f"through the injective codebook to the exact file bytes "
            f"({'byte-exact' if rep.round_trip else 'MISMATCH'}); journey: "
            f"total energy {rep.energy:,} lattice units, path^2 "
            f"{rep.path2:,} over net displacement^2 {rep.net2:,} "
            f"(tortuosity {rep.path2}/{rep.net2} exactly); the library "
            f"attests {rep.ctx:,} of its ticks context-verified, "
            f"{rep.part_known:,} part-known, {rep.new_ticks} new "
            f"(the verification frontier)")
    return _finish(True, text, {"status": "ok", "file": str(rel),
                                "ticks": rep.ticks, "round_trip": rep.round_trip,
                                "on_lattice": rep.on_lattice,
                                "energy": rep.energy, "path2": rep.path2,
                                "net2": rep.net2, "ctx": rep.ctx,
                                "part_known": rep.part_known,
                                "new_ticks": rep.new_ticks})


def _moves(arg: str) -> Answer:
    try:
        path = LL.resolve_lean_path(arg)
        text = path.read_text(encoding="utf-8", errors="replace")
        _, addrs = LL.encode_text(text)
    except FileNotFoundError as exc:
        return _finish(False, f"leechlean: refused -- {exc}; " + USAGE,
                       {"status": "refused"})
    except KeyError as exc:
        return _finish(False, f"leechlean: refused -- {path.name} has a part "
                       f"outside the corpus codebook ({exc.args[0]!r})",
                       {"status": "refused"})
    rep = LL.move_report(addrs)
    top_text = ""
    if rep.top:
        join = _top_joining(rep.top[0][0])
        if join is not None:
            top_text = (f"; the most common move is {_part_text(join[0])} -> "
                        f"{_part_text(join[1])} (|d|^2 {rep.top[0][2]}, "
                        f"{rep.top[0][1]} times)")
    names = {2: "type 2 (minimal-vector)", 3: "type 3 (q = 1)",
             4: "type 4 (frame)"}
    types = ", ".join(f"{names.get(t, t)}: {n}" for t, n in rep.types.items())
    text = (f"the happening between the addresses of {path.name}: "
            f"{rep.moves:,} moves, {rep.distinct:,} distinct, of which "
            f"{rep.known_moves:,} carry the stream back into the corpus "
            f"repertoire; mean |d|^2 = {rep.mean_norm2_num}/"
            f"{rep.mean_norm2_den} exactly over the distinct moves; class "
            f"types met: {types}; the class law kappa(d1)(*)kappa(d2) = "
            f"kappa(d1+d2) holds live on the two most common moves: "
            f"{rep.class_law}, and their composed move is "
            f"{'back in the repertoire' if rep.composed_known else 'outside the repertoire'}"
            + top_text)
    return _finish(True, text, {"status": "ok", "moves": rep.moves,
                                "distinct": rep.distinct,
                                "known_moves": rep.known_moves,
                                "class_law": rep.class_law,
                                "composed_known": rep.composed_known,
                                "types": {str(k): v for k, v in rep.types.items()}})


def _top_joining(move: Tuple[int, ...]) -> Optional[Tuple[str, str]]:
    """An example (u, v) joining of a move, from the library graph."""
    core = LL.library_state()
    cb = LL.codebook_state()
    for (u, v) in core.edge_count:
        a, b = cb.parts[u].address, cb.parts[v].address
        if tuple(b[i] - a[i] for i in range(24)) == move:
            return u, v
    return None


# ---------------------------------------------------------------------------
# tool leechlean continue PART
# ---------------------------------------------------------------------------

def _continue(arg: str) -> Answer:
    key = _find_part(arg)
    if key is None:
        return _finish(False, f"leechlean: refused -- {arg!r} is not a part "
                       f"of the corpus codebook; " + USAGE,
                       {"status": "refused"})
    cont = LL.continuations(key)
    if not cont:
        return _finish(False, f"leechlean: refused -- the library has no "
                       f"joining out of {key!r}; " + USAGE,
                       {"status": "refused"})
    shown = ", ".join(f"{v!r} ({c:,} joinings)" for v, c in cont[:5])
    text = (f"the library's continuations of {key!r}, heaviest joining "
            f"first: {shown}, then {max(len(cont) - 5, 0)} more -- "
            f"[unverified graph proposals: the library attests the joining, "
            f"it does not prove anything]")
    return _finish(True, text, {"status": "ok", "part": key,
                                "continuations": [v for v, _ in cont[:5]],
                                "top_count": cont[0][1]})


# ---------------------------------------------------------------------------
# tool leechlean verify PATH [flip K | slip]
# ---------------------------------------------------------------------------

_VERIFY_TICKS = 40


def _verify(arg: str) -> Answer:
    words = arg.split()
    if not words:
        return _finish(False, "leechlean: refused -- " + USAGE,
                       {"status": "refused"})
    model, k = "clean", 1
    if len(words) >= 2 and words[1] == "flip":
        model = "flip"
        k = int(words[2]) if len(words) > 2 and words[2].isdigit() else 1
    elif len(words) >= 2 and words[1] == "slip":
        model = "slip"
    try:
        path = LL.resolve_lean_path(words[0])
        text = path.read_text(encoding="utf-8", errors="replace")
        _, addrs = LL.encode_text(text)
    except FileNotFoundError as exc:
        return _finish(False, f"leechlean: refused -- {exc}; " + USAGE,
                       {"status": "refused"})
    except KeyError as exc:
        return _finish(False, f"leechlean: refused -- {path.name} has a part "
                       f"outside the corpus codebook ({exc.args[0]!r})",
                       {"status": "refused"})
    addrs = addrs[:_VERIFY_TICKS]
    true = [LL.codebook_state().cells[a] for a in addrs]
    if model == "clean":
        report = LL.sieve_report(addrs)
        false_alarms = sum(v for kk, v in report.items() if kk != "clean")
        text_out = (f"the address stream of {path.name} (first "
                    f"{len(addrs)} ticks) is clean: the congruence sieve "
                    f"raises {false_alarms} false alarms (one parity, Golay "
                    f"supports mod 4, sum = 4m mod 8 all hold on every tick)")
        return _finish(false_alarms == 0, text_out,
                       {"status": "ok", "model": "clean", "ticks": len(addrs),
                        "false_alarms": false_alarms})
    corrupted = LL.corrupt_stream(addrs, model, 20261111, k=k)
    report = LL.sieve_report(corrupted)
    detected = sum(v for kk, v in report.items() if kk != "clean")
    if model == "slip":
        # on-lattice: the sieve sees clean ticks; the class syndrome speaks
        cb = LL.codebook_state()
        changed = sum(1 for a, x in zip(addrs, corrupted)
                      if LL.class_of(x) != LL.class_of(a))
        repaired, stats = LL.repair_stream(corrupted)
        got = sum(1 for g, t in zip(repaired, true) if g == t)
        text_out = (f"the address stream of {path.name} corrupted by "
                    f"minimal-vector slips (on the lattice): the congruence "
                    f"sieve sees {report['clean']} clean ticks (it cannot "
                    f"see an on-lattice slip), but the Lambda/2Lambda class "
                    f"syndrome flags {changed} of {len(addrs)} ticks, and "
                    f"the class-assisted repair decodes {got}/{len(addrs)} "
                    f"back to the true parts")
        return _finish(changed == len(addrs), text_out,
                       {"status": "ok", "model": "slip", "ticks": len(addrs),
                        "class_changed": changed, "repaired": got,
                        "sieve_clean": report["clean"]})
    repaired, stats = LL.repair_stream(corrupted)
    got = sum(1 for g, t in zip(repaired, true) if g == t)
    text_out = (f"the address stream of {path.name} corrupted by a single "
                f"+-{k} flip on one coordinate of every tick: the sieve "
                f"flags {detected} of {len(addrs)} ticks (first broken "
                f"congruence: "
                f"{max(((v, kk) for kk, v in report.items() if kk != 'clean'), default=(0, 'none'))[1]}"
                f"), and the class-assisted repair decodes "
                f"{got}/{len(addrs)} back to the true parts")
    return _finish(detected == len(addrs), text_out,
                   {"status": "ok", "model": "flip", "k": k,
                    "ticks": len(addrs), "detected": detected,
                    "repaired": got})


# ---------------------------------------------------------------------------
# tool leechlean attest PART | stitch SNIPPET | state
# ---------------------------------------------------------------------------

def _attest(arg: str) -> Answer:
    key = _find_part(arg)
    if key is None:
        return _finish(False, f"leechlean: refused -- {arg!r} is not a part "
                       f"of the corpus codebook; " + USAGE,
                       {"status": "refused"})
    att = LL.attestations_of(key)
    core = LL.library_state()
    files = core.part_files.get(key, 0)
    shown = ", ".join(f"{f} ({n} files)" for f, n in att[:4])
    text = (f"the part {key!r} is attested under {len(att)} declaration "
            f"frame(s) in {files} of the {core.n_files} library files -- "
            f"most attested: {shown} -- [syntactic attestation: the library "
            f"has seen the part used this way; it is not a proof]")
    return _finish(True, text, {"status": "ok", "part": key,
                                "frames": len(att), "files": files,
                                "top_frames": [f for f, _ in att[:4]]})


def _stitch(arg: str) -> Answer:
    if not arg.strip():
        return _finish(False, "leechlean: refused -- stitch needs a Lean "
                       "snippet to author; " + USAGE, {"status": "refused"})
    res = LL.stitch_text(arg)
    new = ", ".join(f"{k!r} -> {list(a)} (energy {LL.energy_of(a)})"
                    for k, a, _e, _j in res["new_parts"])
    text = (f"authoring the snippet against the library: {res['ticks']} "
            f"ticks, {res['n_ctx']} context-verified, {res['n_part']} "
            f"part-known, {res['n_new']} new"
            + (f"; fresh addresses on the fly: {new}" if new else "")
            + f"; the projection through the extended codebook is "
            f"{'byte-exact' if res['byte_exact'] else 'NOT exact'} "
            f"[attestation is syntactic, never a proof]")
    return _finish(bool(res["byte_exact"]), text,
                   {"status": "ok", "ticks": res["ticks"],
                    "n_ctx": res["n_ctx"], "n_part": res["n_part"],
                    "n_new": res["n_new"], "byte_exact": res["byte_exact"],
                    "new_parts": [k for k, *_ in res["new_parts"]]})


def _state(arg: str) -> Answer:
    cb = LL.codebook_state()
    core = LL.library_state()
    grades = LL.granularity_counts()
    uni = LL.universal_core(400)
    ws = cb.parts["ws: "]
    mllib = cb.parts["ident:Mathlib"]
    text = (f"the leechlean addressing of this repository's Lean "
            f"development: {len(cb):,} parts at {len(cb):,} distinct Leech "
            f"addresses (0 collisions), {grades['token']:,} token, "
            f"{grades['bigram']:,} bigram, {grades['frame']} frame and "
            f"{grades['tactic']} tactic parts; the library graph joins "
            f"{len(core.part_files):,} parts by {len(core.edge_count):,} "
            f"directed joinings under {len(core.ctx_files):,} (part, frame) "
            f"attestations over {core.n_files} files and "
            f"{core.n_tokens:,} tokens; the universal core (parts in at "
            f"least 400 files) is {len(uni)} parts: "
            f"{', '.join(repr(k) for k in uni[:8])} ...; the energy law: the "
            f"most common part 'ws: ' ({ws.count:,} uses) sits at lattice "
            f"energy {ws.energy} (the one-bit sphere), the rare "
            f"'ident:Mathlib' ({mllib.count} uses) at {mllib.energy} -- one "
            f"bit of surprisal is four units of Leech energy")
    return _finish(True, text,
                   {"status": "ok", "parts": len(cb),
                    "grades": {k: v for k, v in grades.items()},
                    "joinings": len(core.edge_count),
                    "contexts": len(core.ctx_files),
                    "files": core.n_files, "tokens": core.n_tokens,
                    "core_400": len(uni)})


# ---------------------------------------------------------------------------
# the dispatch
# ---------------------------------------------------------------------------

_OPS = {"address": _address, "file": _file, "moves": _moves,
        "continue": _continue, "verify": _verify, "attest": _attest,
        "stitch": _stitch, "state": _state}


def leechlean_text(arg: str) -> Answer:
    """``tool leechlean ...`` (see the module docstring)."""
    a = " ".join(arg.split())
    if not a:
        return _finish(True, "leechlean: the leechlean addressing of this "
                       "repository's Lean development; reads: " + USAGE,
                       {"status": "usage"})
    op, _, rest = a.partition(" ")
    if op == "prove" or op.startswith("prove "):
        return _finish(False, "leechlean: refused -- it addresses, proposes "
                       "and checks; it never proves. Its attestation is "
                       "syntactic (a part under a frame in the library), "
                       "stated as such in every answer", {"status": "refused"})
    fn = _OPS.get(op)
    if fn is None:
        return _finish(False, f"leechlean: refused -- {op!r} is not a "
                       f"request it reads; " + USAGE, {"status": "refused"})
    return fn(rest.strip())
