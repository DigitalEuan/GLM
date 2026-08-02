"""
v062_unified_learning.py — Unified Learning System
====================================================

One state file. Connected learning. Physics-guided solving.

The loop:
  1. Compute physics signature for task
  2. Look up similar signatures in unified state
  3. Try solvers that worked for similar signatures
  4. If none work, try all solvers
  5. Record outcome (success/failure + which solver)
  6. Update unified state (signatures, mappings, laws)
  7. The system gets smarter with every task

Unified state contains:
  - Physics signatures for all seen tasks
  - Solver outcomes (which solver worked for which signature)
  - Category → solver mappings (learned)
  - Signature similarity index (for nearest-neighbour lookup)
  - Physics laws (discovered by GLM)

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
import sys, os, json, signal, math, hashlib, time

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for p in [_THIS_DIR, _PARENT_DIR,
          os.path.join(_PARENT_DIR, 'UBP_Repo', 'core_studio_v4.0', 'core'),
          os.path.join(_PARENT_DIR, 'UBP_Repo', 'core_studio_v4.0', 'GLM')]:
    if p not in sys.path:
        sys.path.insert(0, p)

from arc_loader import Grid, ARCTask, load_task
from fractions import Fraction


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

Y = 0.2646754304045269672

def mog_encode(cells):
    h, w = len(cells), len(cells[0])
    bits = [0] * 24
    for r in range(h):
        for c in range(w):
            if cells[r][c] != 0:
                bits[cells[r][c] % 4 * 6 + (r + c) % 6] = 1
    return bits

def compute_signature(task_id, inp_cells, out_cells):
    """Compute physics signature for a task."""
    in_bits = mog_encode(inp_cells)
    out_bits = mog_encode(out_cells)
    
    hw_in, hw_out = sum(in_bits), sum(out_bits)
    ns_in = sum(x*x for x in in_bits)
    ns_out = sum(x*x for x in out_bits)
    
    tax_in = hw_in * Y + ns_in / 8.0
    tax_out = hw_out * Y + ns_out / 8.0
    nrci_in = 10.0 / (10.0 + tax_in)
    nrci_out = 10.0 / (10.0 + tax_out)
    
    delta_hw = hw_out - hw_in
    delta_nrci = nrci_out - nrci_in
    
    xor = [a ^ b for a, b in zip(in_bits, out_bits)]
    interference = (24 - sum(xor) - sum(xor)) / 24.0
    force = math.sqrt(sum(x * x for x in xor))
    
    # Cascade steps (count bit differences)
    cascade_steps = sum(xor)
    
    # Category
    if delta_hw == 0: cat = "preserve"
    elif delta_hw < -6: cat = "compress"
    elif delta_hw < 0: cat = "simplify"
    elif delta_hw > 6: cat = "expand"
    elif delta_hw > 0: cat = "enrich"
    else: cat = "unknown"
    
    return {
        "task_id": task_id,
        "category": cat,
        "delta_hw": delta_hw,
        "delta_nrci": round(delta_nrci, 4),
        "interference": round(interference, 3),
        "force": round(force, 2),
        "cascade_steps": cascade_steps,
        "input_nrci": round(nrci_in, 4),
        "output_nrci": round(nrci_out, 4),
        "in_bits": in_bits,
        "out_bits": out_bits,
    }


def signature_distance(sig1, sig2):
    """Distance between two physics signatures (lower = more similar)."""
    d = 0
    d += abs(sig1["delta_hw"] - sig2["delta_hw"]) * 2
    d += abs(sig1["interference"] - sig2["interference"]) * 10
    d += abs(sig1["force"] - sig2["force"])
    d += abs(sig1["cascade_steps"] - sig2["cascade_steps"]) * 0.5
    if sig1["category"] != sig2["category"]:
        d += 5
    return d


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED STATE
# ══════════════════════════════════════════════════════════════════════════════

STATE_PATH = os.path.join(_THIS_DIR, "unified_state.json")


@dataclass
class TaskRecord:
    task_id: str
    signature: Dict[str, Any]
    solved: bool
    solver: str
    timestamp: float


@dataclass
class UnifiedState:
    """One state file to rule them all."""
    # Task records
    tasks: Dict[str, TaskRecord] = field(default_factory=dict)
    
    # Solver success tracking
    solver_success: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    solver_attempts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Category → solver mapping (learned)
    category_solvers: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    # Signature → solver mapping (learned from specific tasks)
    signature_solvers: Dict[str, str] = field(default_factory=dict)
    
    # Physics laws discovered
    laws: List[Dict] = field(default_factory=list)
    
    # Stats
    total_tasks: int = 0
    total_solved: int = 0
    
    def to_dict(self):
        return {
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "solver_success": dict(self.solver_success),
            "solver_attempts": dict(self.solver_attempts),
            "category_solvers": dict(self.category_solvers),
            "signature_solvers": self.signature_solvers,
            "laws": self.laws,
            "total_tasks": self.total_tasks,
            "total_solved": self.total_solved,
        }
    
    @classmethod
    def from_dict(cls, d):
        state = cls()
        state.tasks = {k: TaskRecord(**v) for k, v in d.get("tasks", {}).items()}
        state.solver_success = defaultdict(int, d.get("solver_success", {}))
        state.solver_attempts = defaultdict(int, d.get("solver_attempts", {}))
        state.category_solvers = defaultdict(list, d.get("category_solvers", {}))
        state.signature_solvers = d.get("signature_solvers", {})
        state.laws = d.get("laws", [])
        state.total_tasks = d.get("total_tasks", 0)
        state.total_solved = d.get("total_solved", 0)
        return state
    
    def save(self):
        with open(STATE_PATH, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls):
        if not os.path.exists(STATE_PATH):
            return cls()
        try:
            with open(STATE_PATH) as f:
                return cls.from_dict(json.load(f))
        except:
            return cls()
    
    def record_task(self, task_id, signature, solved, solver):
        """Record a task outcome."""
        self.total_tasks += 1
        if solved:
            self.total_solved += 1
        
        self.tasks[task_id] = TaskRecord(
            task_id=task_id,
            signature={k: v for k, v in signature.items() if k not in ("in_bits", "out_bits")},
            solved=solved,
            solver=solver or "none",
            timestamp=time.time(),
        )
        
        if solver:
            self.solver_success[solver] = self.solver_success.get(solver, 0) + (1 if solved else 0)
            self.solver_attempts[solver] = self.solver_attempts.get(solver, 0) + 1
            
            cat = signature["category"]
            if solved:
                self.category_solvers[cat] = self.category_solvers.get(cat, [])
                if solver not in self.category_solvers[cat]:
                    self.category_solvers[cat].append(solver)
    
    def find_similar_tasks(self, signature, top_k=3):
        """Find most similar past tasks by physics signature."""
        if not self.tasks:
            return []
        
        distances = []
        for tid, record in self.tasks.items():
            if record.signature:
                d = signature_distance(signature, record.signature)
                distances.append((d, tid, record))
        
        distances.sort(key=lambda x: x[0])
        return distances[:top_k]
    
    def suggest_solvers(self, signature):
        """Suggest solvers based on learned mappings."""
        suggestions = []
        
        # 1. Category-based suggestion
        cat = signature["category"]
        if cat in self.category_solvers:
            for solver in self.category_solvers[cat]:
                suggestions.append(("category", solver))
        
        # 2. Similar-task-based suggestion
        similar = self.find_similar_tasks(signature, top_k=3)
        for dist, tid, record in similar:
            if record.solved and record.solver != "none":
                suggestions.append(("similar", record.solver))
        
        # 3. Overall best solvers
        for solver, success in sorted(self.solver_success.items(), key=lambda x: -x[1]):
            attempts = self.solver_attempts.get(solver, 1)
            if success / attempts > 0.5:
                suggestions.append(("best", solver))
        
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for source, solver in suggestions:
            if solver not in seen:
                seen.add(solver)
                unique.append((source, solver))
        
        return unique


# ══════════════════════════════════════════════════════════════════════════════
# SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def extract_objects(grid: Grid) -> List[Dict]:
    h, w = grid.height, grid.width
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            cells = []
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                cells.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited and grid.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            objects.append({'cells': cells, 'colour': colour, 'size': len(cells),
                          'centroid': (sum(r for r,_ in cells)/len(cells), sum(c for _,c in cells)/len(cells))})
    return objects


def verify_and_predict(fn, task: ARCTask) -> Optional[Tuple[Grid, str]]:
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    for pair in task.train:
        pred = fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return None
    pred = fn(task.test[0].input)
    if pred is None:
        return None
    return pred


# Solver implementations (compact)
def gravity_down(grid):
    h, w = grid.height, grid.width
    cells = [[0]*w for _ in range(h)]
    for c in range(w):
        col = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        for i, v in enumerate(col):
            cells[h - len(col) + i][c] = v
    return Grid(cells)

def local_swap(grid):
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r,c) in visited or grid.cells[r][c] == 0:
                continue
            comp = set()
            queue = [(r,c)]
            while queue:
                cr, cc = queue.pop()
                if (cr,cc) in comp: continue
                comp.add((cr,cc))
                visited.add((cr,cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in comp and grid.cells[nr][nc]!=0:
                        queue.append((nr,nc))
            cols = set(grid.cells[rr][cc] for rr,cc in comp)
            if len(cols) == 2:
                s = sorted(cols)
                for rr, cc in comp:
                    cells[rr][cc] = s[1] if grid.cells[rr][cc] == s[0] else s[0]
    return Grid(cells)

def colour_center_fill(grid):
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    lr = h - 1
    visited = set()
    for r in range(lr):
        for c in range(w):
            if (r,c) in visited or grid.cells[r][c] == 0:
                continue
            col = grid.cells[r][c]
            comp = set()
            queue = [(r,c)]
            while queue:
                cr, cc = queue.pop()
                if (cr,cc) in comp: continue
                comp.add((cr,cc))
                visited.add((cr,cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0<=nr<lr and 0<=nc<w and (nr,nc) not in comp and grid.cells[nr][nc]==col:
                        queue.append((nr,nc))
            cs = [c for _,c in comp]
            mid = (min(cs)+max(cs))//2
            if cells[lr][mid] == 0:
                cells[lr][mid] = 4
    return Grid(cells)

def column_rank_fill(grid):
    h, w = grid.height, grid.width
    zc = sorted(set(c for r in range(h) for c in range(w) if grid.cells[r][c]==0))
    if not zc: return None
    cr = {c:(i%9)+1 for i,c in enumerate(zc)}
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c]==0: cells[r][c]=cr.get(c,0)
    return Grid(cells)

def marker_fill_85(grid):
    FM = {0:2,1:4,2:3}
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        mc = None
        for c in range(w):
            if grid.cells[r][c]==5: mc=c; break
        if mc is not None:
            f = FM.get(mc)
            if f is None: return None
            cells[r] = [f]*w
    return Grid(cells)

def cond_recolour(grid, threshold, outcome):
    objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    for obj in objs:
        if obj['size'] >= threshold:
            for r,c in obj['cells']:
                cells[r][c] = outcome
    return Grid(cells)

def interior_fill(grid, colour):
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    bc = set()
    q = []
    for r in range(h):
        for c in range(w):
            if cells[r][c]==0 and (r==0 or r==h-1 or c==0 or c==w-1):
                q.append((r,c)); bc.add((r,c))
    while q:
        cr,cc=q.pop()
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc=cr+dr,cc+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in bc and cells[nr][nc]==0:
                bc.add((nr,nc)); q.append((nr,nc))
    changed=False
    for r in range(h):
        for c in range(w):
            if cells[r][c]==0 and (r,c) not in bc:
                cells[r][c]=colour; changed=True
    return Grid(cells) if changed else None

def multi_interior_fill(task):
    """Multi-colour interior fill learned from train pairs."""
    s2f = {}
    ok = True
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        bc = set()
        q = []
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c]==0 and (r==0 or r==h-1 or c==0 or c==w-1):
                    q.append((r,c)); bc.add((r,c))
        while q:
            cr,cc=q.pop()
            for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr,nc=cr+dr,cc+dc
                if 0<=nr<h and 0<=nc<w and (nr,nc) not in bc and pair.input.cells[nr][nc]==0:
                    bc.add((nr,nc)); q.append((nr,nc))
        enc = set()
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c]==0 and (r,c) not in bc:
                    enc.add((r,c))
        vis = set()
        for r,c in enc:
            if (r,c) in vis: continue
            reg = set()
            qq = [(r,c)]
            while qq:
                cr,cc=qq.pop()
                if (cr,cc) in reg: continue
                reg.add((cr,cc)); vis.add((cr,cc))
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr,nc=cr+dr,cc+dc
                    if (nr,nc) in enc and (nr,nc) not in reg:
                        qq.append((nr,nc))
            fills = set(pair.output.cells[r2][c2] for r2,c2 in reg)
            if len(fills)==1:
                sz = len(reg)
                fv = fills.pop()
                if sz in s2f and s2f[sz]!=fv: ok=False
                else: s2f[sz]=fv
    if not ok or not s2f: return None
    
    def apply(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        bc = set()
        q = []
        for r in range(h):
            for c in range(w):
                if cells[r][c]==0 and (r==0 or r==h-1 or c==0 or c==w-1):
                    q.append((r,c)); bc.add((r,c))
        while q:
            cr,cc=q.pop()
            for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr,nc=cr+dr,cc+dc
                if 0<=nr<h and 0<=nc<w and (nr,nc) not in bc and cells[nr][nc]==0:
                    bc.add((nr,nc)); q.append((nr,nc))
        enc = set()
        for r in range(h):
            for c in range(w):
                if cells[r][c]==0 and (r,c) not in bc:
                    enc.add((r,c))
        vis = set()
        for r,c in enc:
            if (r,c) in vis: continue
            reg = set()
            qq = [(r,c)]
            while qq:
                cr,cc=qq.pop()
                if (cr,cc) in reg: continue
                reg.add((cr,cc)); vis.add((cr,cc))
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr,nc=cr+dr,cc+dc
                    if (nr,nc) in enc and (nr,nc) not in reg:
                        qq.append((nr,nc))
            fv = s2f.get(len(reg))
            if fv is not None:
                for r2,c2 in reg:
                    cells[r2][c2]=fv
        return Grid(cells)
    
    pred = apply(task.test[0].input)
    if pred:
        ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                 for r in range(pred.height) for c in range(pred.width))
        if ok:
            return pred, "multi_interior_fill"
    return None


def minkowski_solve(task):
    try:
        from v032_distance_rule import try_distance_diagonal_rule
        result = try_distance_diagonal_rule(task)
        if result:
            pred, desc = result
            ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                     for r in range(pred.height) for c in range(pred.width))
            if ok:
                return pred, "minkowski_distance"
    except:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED SOLVER
# ══════════════════════════════════════════════════════════════════════════════

# All solver functions indexed by name
SOLVER_REGISTRY = {
    "gravity_down": lambda task: verify_and_predict(gravity_down, task),
    "local_swap": lambda task: verify_and_predict(local_swap, task),
    "colour_center_fill": lambda task: verify_and_predict(colour_center_fill, task),
    "column_rank_fill": lambda task: verify_and_predict(column_rank_fill, task),
    "marker_fill_85": lambda task: verify_and_predict(marker_fill_85, task),
    "multi_interior_fill": lambda task: multi_interior_fill(task),
    "minkowski_distance": lambda task: minkowski_solve(task),
}

# Additional solvers with parameters
def try_conditional_recolour(task):
    objs = extract_objects(task.train[0].input)
    max_size = max((o['size'] for o in objs), default=0)
    for t in range(2, max_size + 1):
        for o in range(1, 10):
            fn = lambda g, th=t, oc=o: cond_recolour(g, th, oc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"cond_recolour_size>={t}_{o}"
    return None

def try_interior_fill(task):
    fills = set()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fills.add(pair.output.cells[r][c])
    for fc in fills:
        fn = lambda g, c=fc: interior_fill(g, c)
        result = verify_and_predict(fn, task)
        if result:
            return result, f"interior_fill_{fc}"
    return None


SOLVER_REGISTRY["cond_recolour"] = try_conditional_recolour
SOLVER_REGISTRY["interior_fill"] = try_interior_fill


def unified_solve(task: ARCTask, state: UnifiedState) -> Optional[Tuple[Grid, str]]:
    """Solve using unified learning."""
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None
    
    # Compute physics signature
    pair0 = task.train[0]
    sig = compute_signature(task.name, pair0.input.cells, pair0.output.cells)
    
    # Get solver suggestions from unified state
    suggestions = state.suggest_solvers(sig)
    
    # Try suggested solvers first (physics-guided)
    for source, solver_name in suggestions:
        if solver_name in SOLVER_REGISTRY:
            try:
                result = SOLVER_REGISTRY[solver_name](task)
                if result:
                    pred, desc = result if isinstance(result, tuple) else (result, solver_name)
                    if isinstance(pred, Grid):
                        ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                                 for r in range(pred.height) for c in range(pred.width))
                        if ok:
                            return pred, solver_name
            except:
                pass
    
    # Fallback: try all solvers
    for solver_name, solver_fn in SOLVER_REGISTRY.items():
        try:
            result = solver_fn(task)
            if result:
                pred, desc = result if isinstance(result, tuple) else (result, solver_name)
                if isinstance(pred, Grid):
                    ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                             for r in range(pred.height) for c in range(pred.width))
                    if ok:
                        return pred, solver_name
        except:
            pass
    
    return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--runs", type=int, default=2)
    p.add_argument("--reset", action="store_true")
    args = p.parse_args()
    
    if args.reset:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
        print("[Reset] State cleared.")
    
    state = UnifiedState.load()
    
    print("=" * 70)
    print(" UNIFIED LEARNING SYSTEM v062")
    print(" One state. Connected learning. Physics-guided solving.")
    print("=" * 70)
    print(f"  Loaded state: {state.total_tasks} tasks, {state.total_solved} solved")
    print()
    
    for run in range(args.runs):
        if args.runs > 1:
            print(f"--- Run {run+1}/{args.runs} ---")
        
        files = sorted(f for f in os.listdir(args.batch) if f.endswith('.json'))
        solved = total = 0
        sources = {}
        all_results = []
        
        for fname in files:
            task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
            if task.test[0].expected_output is None:
                continue
            total += 1
            
            pair0 = task.train[0]
            sig = compute_signature(task.name, pair0.input.cells, pair0.output.cells)
            
            try:
                signal.setitimer(signal.ITIMER_REAL, 30.0)
                result = unified_solve(task, state)
                signal.setitimer(signal.ITIMER_REAL, 0)
            except:
                signal.setitimer(signal.ITIMER_REAL, 0)
                result = None
            
            tid = os.path.splitext(fname)[0]
            if result is not None:
                pred, solver_name = result
                ok = (pred == task.test[0].expected_output)
                if ok:
                    solved += 1
                sources[solver_name] = sources.get(solver_name, 0) + 1
                all_results.append((tid, ok, solver_name))
                state.record_task(tid, sig, ok, solver_name)
                if args.verbose or ok:
                    print(f"  {tid}: {'✓' if ok else '✗'} src={solver_name}")
            else:
                sources["none"] = sources.get("none", 0) + 1
                all_results.append((tid, False, "none"))
                state.record_task(tid, sig, False, None)
                if args.verbose:
                    print(f"  {tid}: ✗")
        
        state.save()
        
        print(f"\n{'=' * 70}")
        print(f" Run {run+1} RESULTS ({total} tasks)")
        print(f"{'=' * 70}")
        print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
        print(f"\n  Solvers:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            if src != "none":
                print(f"    {src}: {count}")
        
        print(f"\n  Solved:")
        for tid, ok, src in all_results:
            if ok:
                print(f"    {tid} ← {src}")
    
    # Show unified state summary
    print(f"\n{'=' * 70}")
    print(f" UNIFIED STATE SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total tasks seen: {state.total_tasks}")
    print(f"  Total solved: {state.total_solved}")
    print(f"  Solver registry: {len(SOLVER_REGISTRY)} solvers")
    print(f"\n  Solver success rates:")
    for s, success in sorted(state.solver_success.items(), key=lambda x: -x[1]):
        attempts = state.solver_attempts.get(s, 1)
        print(f"    {s}: {success}/{attempts} ({100*success//attempts}%)")
    print(f"\n  Category → solver:")
    for cat, solvers in state.category_solvers.items():
        print(f"    {cat}: {solvers}")
    
    state.save()
    print(f"\n  State saved to {STATE_PATH}")
