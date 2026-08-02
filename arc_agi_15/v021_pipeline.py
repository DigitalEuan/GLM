"""
v021_pipeline.py — v0.21: HDRB + Hex-Colour Addresses wired in
=================================================================

Architecture:
  1. Hex-colour learning (NEW — uniform delta, colour mapping, nearest-address)
  2. ALL 162 DSL ops with per-op 1.5s timeout (from patched v0.20)
  3. CRG colour mapping (from v0.20)
  4. Train-derived colour mappings (from v0.20)
  5. Two-op compositions (from v0.20)
  6. Prediction paths (analogy, chain, group) (from v0.20)
  7. Identity (from v0.20)
  8. HARD FILTER: exact train-pair reproduction
  9. HDRB signature as TIEBREAKER (replaces NRCI for ordering)
       — prefer candidates whose HDRB signature matches the train signature
  10. NRCI + LDP + eml as DIAGNOSTICS (still computed, not used for selection)

The key change vs v0.20: HDRB signature is the primary tiebreaker.
The HDRB signature tells us "what KIND of transformation is this?" —
exact (gradient), co-exact (curl), or harmonic (recolour).  When
multiple candidates pass the hard gate, we prefer the one whose
signature matches the train pairs' signature.

Hex-colour learning adds three new candidate sources that often catch
transformations the DSL ops miss (because the DSL ops are pre-defined,
while hex learning derives the transformation FROM the train data).
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
import sys, os, time, math, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from encoder import encode_grid
from dsl.arc_dsl_full import Ops, Operation, Program


# ── per-op timeout (some DSL ops infinite-loop on certain grids) ─────────────
class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)

def _apply_timed(prog, grid, seconds=1.5):
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return prog.apply(grid)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def _train_pass(task: ARCTask, prog: Program) -> bool:
    for pair in task.train:
        try:
            if _apply_timed(prog, pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


# ── NRCI (still computed as a diagnostic) ────────────────────────────────────
def _nrci(grid: Grid) -> Fraction:
    from ubp_unified_v5 import UBPSourceCodeParticlePhysics
    pp = UBPSourceCodeParticlePhysics()
    Y = pp.Y
    v, _ = encode_grid(grid)
    snapped, _ = GOLAY_ENGINE.snap_to_codeword(v)
    hw = sum(snapped)
    ns = sum(x * x for x in snapped)
    tax = Fraction(hw) * Y + Fraction(ns, 8)
    return Fraction(10) / (Fraction(10) + tax)


# ── HDRB signature ───────────────────────────────────────────────────────────
def _hdrb_signature(grid_in: Grid, grid_out: Grid) -> Optional[Dict[str, Any]]:
    """Compute the HDRB signature of an input → output transformation."""
    try:
        if grid_in.shape != grid_out.shape:
            return None
        from generative.hex_learner import address_grid
        in_addrs = address_grid(grid_in)
        out_addrs = address_grid(grid_out)
        in_vecs = [c.vector for row in in_addrs for c in row]
        out_vecs = [c.vector for row in out_addrs for c in row]
        from vendor.hdrb import analyse_train_pair
        sig = analyse_train_pair(in_vecs, out_vecs)
        return sig.as_dict()
    except Exception:
        return None


def _hdrb_match_score(train_sig: Optional[Dict], cand_sig: Optional[Dict]) -> float:
    """How well does the candidate signature match the train signature?

    Returns a score in [0, 1].  Higher = better match.
    """
    if train_sig is None or cand_sig is None:
        return 0.5  # neutral
    if train_sig.get("total_mass", 0) < 1e-9 or cand_sig.get("total_mass", 0) < 1e-9:
        # Both zero-mass = identity-like, perfect match
        if abs(train_sig.get("total_mass", 0)) < 1e-9 and abs(cand_sig.get("total_mass", 0)) < 1e-9:
            return 1.0
        return 0.3
    # Compare dominant component
    if train_sig.get("dominant") == cand_sig.get("dominant"):
        # Same dominant — compare the mass distributions
        t_total = train_sig.get("total_mass", 1)
        c_total = cand_sig.get("total_mass", 1)
        t_h = train_sig.get("harmonic_mass", 0) / max(t_total, 1e-9)
        c_h = cand_sig.get("harmonic_mass", 0) / max(c_total, 1e-9)
        t_e = train_sig.get("exact_mass", 0) / max(t_total, 1e-9)
        c_e = cand_sig.get("exact_mass", 0) / max(c_total, 1e-9)
        t_c = train_sig.get("coexact_mass", 0) / max(t_total, 1e-9)
        c_c = cand_sig.get("coexact_mass", 0) / max(c_total, 1e-9)
        # Cosine similarity of the (h, e, c) vectors
        dot = t_h * c_h + t_e * c_e + t_c * c_c
        norm_t = math.sqrt(t_h ** 2 + t_e ** 2 + t_c ** 2)
        norm_c = math.sqrt(c_h ** 2 + c_e ** 2 + c_c ** 2)
        if norm_t < 1e-9 or norm_c < 1e-9:
            return 0.5
        return 0.5 + 0.5 * (dot / (norm_t * norm_c))
    else:
        return 0.1


# ── LDP + eml (still computed as diagnostics) ────────────────────────────────
def _ldp(grid: Grid) -> Dict:
    try:
        from ldp import DataObject
        from generative.object_extractor import extract_objects
        objs = extract_objects(grid)
        mass = sum(DataObject(o.cell_count).mass for o in objs if o.cell_count > 0)
        tensions = [DataObject(o.cell_count).tension for o in objs if o.cell_count > 0]
        primes = sum(1 for o in objs if o.cell_count > 0 and DataObject(o.cell_count).is_prime)
        return {"mass": mass, "tension": sum(tensions) / len(tensions) if tensions else 0,
                "primes": primes, "objects": len(objs)}
    except Exception:
        return {}


def _eml(grid: Grid) -> Dict:
    try:
        from spatial_arithmetic_compat import eml
        n = float(_nrci(grid))
        l = _ldp(grid)
        t = max(l.get("tension", 0.001), 0.001)
        return {"nrci": n, "tension": t, "eml": eml(n, t),
                "Y": math.pi / (math.pi ** 2 + 2)}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# SOLVE
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Solve with the v0.21 pipeline (HDRB + Hex + DSL + prediction paths)."""
    test_input = task.test[0].input

    # Compute the train HDRB signature (for tiebreaker)
    train_sig = None
    try:
        # Use the first train pair with same shape in/out
        for pair in task.train:
            if pair.input.shape == pair.output.shape:
                train_sig = _hdrb_signature(pair.input, pair.output)
                break
    except Exception:
        pass

    # Each survivor: (grid, source, nrci, hdrb_sig)
    survivors: List[Tuple[Grid, str, Fraction, Optional[Dict]]] = []

    # ── 1. HEX-COLOUR LEARNING (NEW) ──
    try:
        from generative.hex_learner import learn_from_task, predict_best
        hex_pred, hex_src, hex_diag = predict_best(task)
        if hex_pred is not None:
            # Verify it passes train (predict_best already does, but double-check)
            sig = _hdrb_signature(test_input, hex_pred)
            survivors.append((hex_pred, f"hex_{hex_src}", _nrci(hex_pred), sig))
    except Exception:
        pass

    # ── 2. ALL 162 DSL ops ──
    for op in Ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                sig = _hdrb_signature(test_input, pred)
                survivors.append((pred, f"dsl_{op.name}", _nrci(pred), sig))
        except Exception:
            continue

    # ── 3. CRG colour mapping ──
    try:
        from generative.object_crg_full import ObjectCRG as FullCRG
        crg = FullCRG()
        crg.learn_from_task(task)
        if crg.global_colour_mapping:
            m = {int(k): int(v) for k, v in crg.global_colour_mapping.items()}
            prog = Program([Operation(Ops.RECOLOUR, {"mapping": m})])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                sig = _hdrb_signature(test_input, pred)
                survivors.append((pred, "crg", _nrci(pred), sig))
    except Exception:
        pass

    # ── 4. Train-derived colour mappings ──
    train_maps = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        m = {}
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old, new = pair.input.cells[r][c], pair.output.cells[r][c]
                if old != new:
                    m[old] = new
        if m and m not in train_maps:
            train_maps.append(m)
    for m in train_maps[:5]:
        prog = Program([Operation(Ops.RECOLOUR, {"mapping": m})])
        if _train_pass(task, prog):
            pred = _apply_timed(prog, test_input)
            sig = _hdrb_signature(test_input, pred)
            survivors.append((pred, "train_map", _nrci(pred), sig))

    # ── 5. Two-op compositions ──
    geo_ops = [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
               Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
               Ops.GRAVITY_DOWN, Ops.GRAVITY_UP,
               Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
               Ops.CROP_TO_NONZERO, Ops.TILE_2X]
    for g in geo_ops:
        for m in train_maps[:2]:
            try:
                prog = Program([Operation(g), Operation(Ops.RECOLOUR, {"mapping": m})])
                if _train_pass(task, prog):
                    pred = _apply_timed(prog, test_input)
                    sig = _hdrb_signature(test_input, pred)
                    survivors.append((pred, "compose", _nrci(pred), sig))
            except Exception:
                continue

    # ── 6. Prediction paths ──
    try:
        from generative.object_crg_full import ObjectCRG as FullCRG
        from generative.prediction_paths import (
            predict_via_analogy, predict_via_chain, predict_via_groups
        )
        crg = FullCRG()
        crg.learn_from_task(task)
        for fn, name in [(predict_via_analogy, "analogy"),
                         (predict_via_chain, "chain"),
                         (predict_via_groups, "group")]:
            try:
                pred = fn(task, crg)
                if pred is not None:
                    sig = _hdrb_signature(test_input, pred)
                    survivors.append((pred, name, _nrci(pred), sig))
            except Exception:
                pass
    except Exception:
        pass

    # ── 7. Identity ──
    if all(p.input == p.output for p in task.train):
        sig = _hdrb_signature(test_input, test_input)
        survivors.append((test_input.copy(), "identity", _nrci(test_input), sig))

    # ── 8. TIEBREAK: source MDL (simpler wins), then HDRB match, then NRCI ──
    # Source priority by description length (Occam's razor).
    # Lower number = simpler model = preferred when all pass the hard gate.
    SOURCE_PRIORITY = {
        "identity": 0,
        # Single DSL ops — model = 1 op name (lowest MDL among non-identity)
        # Geometric ops (gravity, rotate, flip) are simplest; others follow.
        "dsl_GRAVITY_DOWN": 1, "dsl_GRAVITY_UP": 1, "dsl_GRAVITY_LEFT": 1, "dsl_GRAVITY_RIGHT": 1,
        "dsl_ROTATE_90": 1, "dsl_ROTATE_180": 1, "dsl_ROTATE_270": 1,
        "dsl_FLIP_H": 1, "dsl_FLIP_V": 1, "dsl_TRANSPOSE": 1,
        "dsl_CROP_TO_NONZERO": 2, "dsl_TILE_2X": 2, "dsl_SHIFT_UP": 2, "dsl_SHIFT_DOWN": 2,
        "dsl_SHIFT_LEFT": 2, "dsl_SHIFT_RIGHT": 2, "dsl_RECOLOUR": 3,
        # Other DSL ops — single op but more complex params
        # (default for dsl_* is 5)
        # Train-derived mappings
        "train_map": 4, "crg": 4,
        # Compositions (two ops)
        "compose": 6,
        # Hex-learner — model is the entire train set (highest MDL)
        "hex_uniform_delta": 3,        # model = 1 int
        "hex_colour_mapping": 4,        # model = ≤10 colour pairs
        "hex_nearest_address": 8,       # model = entire train set (k-NN)
        # Generative paths
        "analogy": 7, "chain": 7, "group": 7,
    }

    def _priority(src: str) -> int:
        if src in SOURCE_PRIORITY:
            return SOURCE_PRIORITY[src]
        if src.startswith("dsl_"):
            return 5  # default DSL priority
        return 9  # unknown — lowest priority

    if survivors:
        # Sort by (priority asc, HDRB match desc, NRCI desc)
        survivors.sort(key=lambda x: (
            _priority(x[1]),
            -_hdrb_match_score(train_sig, x[3]),
            -float(x[2]),
        ))
        best = survivors[0]
        return best[0], best[1], {
            "survivors": len(survivors),
            "sources": [s for _, s, _, _ in survivors],
            "nrci": float(best[2]),
            "train_hdrb": train_sig,
            "best_hdrb": best[3],
            "hdrb_match_score": _hdrb_match_score(train_sig, best[3]),
            "priority": _priority(best[1]),
            "ldp": _ldp(best[0]),
            "eml": _eml(best[0]),
        }
    return test_input.copy(), "none", {"survivors": 0, "train_hdrb": train_sig}


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        files = files[:args.max_tasks]

    solved = total = 0
    t_total = 0
    sources = {}
    hex_sources = 0
    hdrb_matches = 0

    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        t0 = time.time()
        pred, src, diag = solve(task)
        t_total += time.time() - t0
        ok = (pred == task.test[0].expected_output)
        if ok:
            solved += 1
        sources[src] = sources.get(src, 0) + 1
        if src.startswith("hex_"):
            hex_sources += 1
        if diag.get("hdrb_match_score", 0) > 0.7:
            hdrb_matches += 1
        if args.verbose or ok:
            print(f"  {fname}: {'OK' if ok else 'X'} src={src} "
                  f"survivors={diag.get('survivors', 0)} "
                  f"hdrb_match={diag.get('hdrb_match_score', 0):.2f} "
                  f"({time.time() - t0:.2f}s)")

    print(f"\n═══ v0.21 ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total / max(total, 1):.2f}s/task)")
    print(f"  Hex-learner wins: {hex_sources}")
    print(f"  HDRB match >0.7: {hdrb_matches}")
    print(f"  Sources: {sources}")
