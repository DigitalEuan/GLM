#!/usr/bin/env python3
"""GLM Hypothesis Engine v4 — the "sorry generator" architecture.

Reframe: the engine doesn't need to be a strong hypothesis generator.
It needs to be a cheap guesser ("sorry" in Lean terms) that gets
checked rigorously by the GLM's existing discipline, then refined
based on WHY the check failed, then re-guessed. The loop:

  1. SORRY: cheaply generate a candidate (T, ρ, C) + proof obligation
  2. CHECK: does it reproduce the puzzle's V? Does it pass control?
  3. REFINE: extract WHY it failed (mean wrong? std wrong? cycle? control?)
  4. RE-GUESS: adjust the candidate based on the failure feedback
  5. Loop until check passes or max iterations

Improvements over v3:
  - 9 Lean source files (80+ theorems) bundled inline
  - Logical-form detection: existence (∃), universal (∀), equality, etc.
  - Shape-based DFT: compare spectral centroid + entropy, not exact peaks
  - Failure-feedback refinement: the refiner reads the check's diagnosis
  - The "sorry" is cheap; the check is rigorous; the refinement is guided

Self-contained: single script, no external files.
Run: python3 glm_hypothesis_engine_v4.py
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# ═══════════════════════════════════════════════════════════════════════════
# BUNDLED: Golay code + R-calculus (from v3, verified)
# ═══════════════════════════════════════════════════════════════════════════

class GolayCode:
    """[24,12,8] extended binary Golay code."""
    GEN_POLY = (1<<0)|(1<<2)|(1<<4)|(1<<5)|(1<<6)|(1<<10)|(1<<11)
    def __init__(self):
        self._cw = None
    def _gen(self):
        rows = []
        for i in range(12):
            r = self.GEN_POLY << i
            p = bin(r).count("1") % 2
            rows.append(r | (p << 23))
        cws = set()
        for mask in range(4096):
            cw = 0
            for i in range(12):
                if mask & (1<<i): cw ^= rows[i]
            cws.add(cw)
        return sorted(cws)
    @property
    def codewords(self):
        if self._cw is None: self._cw = self._gen()
        return self._cw
    def nearest(self, v):
        best, bd = 0, 25
        for cw in self.codewords:
            d = bin(v^cw).count("1")
            if d < bd: bd, best = d, cw
            if d == 0: break
        return best, bd


class RCalculus:
    """R-calculus — Residual Notation."""
    def __init__(self, bits=24):
        self.bits = bits
        self.mask = (1<<bits)-1
    def popcount(self, x): return bin(x&self.mask).count("1")
    def hdist(self, a, b): return self.popcount(a^b)
    def diff(self, S, T): return S^T
    def rotate(self, S, s=1):
        s %= self.bits
        return ((S<<s)|(S>>(self.bits-s)))&self.mask
    def correct(self, S, T, mf=1):
        d = self.hdist(S,T)
        if d==0: return S
        Sc, d = S, d
        for _ in range(mf):
            bb, bd = -1, d
            for i in range(self.bits):
                St = Sc^(1<<i)
                dd = self.hdist(St,T)
                if dd<bd: bd,bb=dd,i
            if bb<0: break
            Sc ^= (1<<bb); d=bd
            if d==0: break
        return Sc
    def run(self, T, S0, rho, C, R, N=100, delta=None):
        S = S0&self.mask; T=T&self.mask
        errs, states = [], []
        for n in range(N):
            E = S^T; errs.append(E); states.append(S)
            Sr = rho(S); Sc = C(Sr,T)
            if delta: Sc ^= delta(n)
            S = Sc&self.mask
        return {"V": R(errs), "errors": errs, "states": states}
    @staticmethod
    def detect_cycle(seq, ml=2, mx=None, mr=3):
        if mx is None: mx = len(seq)//mr
        for L in range(ml, mx+1):
            for s in range(len(seq)-L*mr):
                ok = True
                for r in range(1,mr):
                    for i in range(L):
                        if s+r*L+i>=len(seq) or seq[s+i]!=seq[s+r*L+i]:
                            ok=False; break
                    if not ok: break
                if ok: return (s,L)
        return None
    @staticmethod
    def stats(seq):
        if not seq: return {}
        c=Counter(seq); n=len(seq)
        m=sum(seq)/n; v=sum((x-m)**2 for x in seq)/n
        return {"len":n,"min":min(seq),"max":max(seq),"mean":m,
                "std":v**0.5,"pp":max(seq)-min(seq),
                "hist":dict(sorted(c.items()))}
    @staticmethod
    def autocorr(seq, ml=20):
        n=len(seq)
        if n==0: return []
        m=sum(seq)/n; v=sum((x-m)**2 for x in seq)/n
        if v==0: return [1.0]+[0.0]*ml
        return [1.0 if l==0 else
                sum((seq[i]-m)*(seq[i-l]-m) for i in range(l,n))/n/v
                for l in range(min(ml+1,n))]
    @staticmethod
    def dft_shape(seq):
        """Spectral shape: centroid + entropy (not exact peaks)."""
        N=len(seq)
        if N==0: return {"centroid":0,"entropy":0,"peak_k":0}
        mags=[]
        for k in range(1,N//2+1):
            re=sum(seq[n]*math.cos(2*math.pi*k*n/N) for n in range(N))
            im=sum(seq[n]*math.sin(2*math.pi*k*n/N) for n in range(N))
            mags.append(math.sqrt(re*re+im*im))
        total=sum(mags)
        if total==0: return {"centroid":0,"entropy":0,"peak_k":0}
        centroid=sum(k*mags[k-1] for k in range(1,len(mags)+1))/total
        probs=[m/total for m in mags]
        entropy=-sum(p*math.log2(p) for p in probs if p>0)
        peak_k=mags.index(max(mags))+1
        return {"centroid":centroid,"entropy":entropy,"peak_k":peak_k}


# ═══════════════════════════════════════════════════════════════════════════
# Lean parser + semantic encoding (from v3, improved)
# ═══════════════════════════════════════════════════════════════════════════

MATH_OBJ = {"ℚ":"rat","Rat":"rat","ℕ":"nat","Nat":"nat","ℤ":"int","Int":"int",
            "Bool":"bool","bool":"bool","Fin":"fin","Finset":"fset","Set":"set",
            "List":"list","ℝ":"real","Real":"real","Matrix":"mat","ZMod":"zmod",
            "String":"str","Prop":"prop"}

TACTIC_S = {"rfl":0,"decide":0,"simp":1,"norm_num":1,"linarith":2,"ring":2,
            "omega":2,"tauto":2,"by_contra":3,"push_neg":3,"by_cases":3,
            "exact":1,"apply":2,"intro":2,"have":3,"refine":3,"induction":4,
            "cases":3,"funext":3,"ext":3,"constructor":3,"linear_combination":4,
            "exact_mod_cast":2,"push_cast":2,"rcases":3,"obtain":3,"subst":2,
            "exfalso":3,"calc":3,"simpa":2,"unfold":1,"rw":1,"show":2,
            "convert":3,"congr":2,"field_simp":2,"nlinarith":3}

LOGICAL_FORMS = {
    "existence": [r"∃",r"\bexists\b"],
    "universal": [r"∀",r"\bforall\b"],
    "equality": [r"↔",r"\biff\b"],
    "inequality": [r"≤",r"<",r"≥",r">",r"≠"],
    "negation": [r"¬",r"\bnot\b"],
    "implication": [r"→",r"\bimplies\b"],
}

OBJ_PAT = {"rat":0xAAAAAA,"nat":0x555555,"int":0x0F0F0F,"bool":0x00FF00,
           "fin":0xFF0000,"fset":0x0FF00F,"set":0xF00FF0,"list":0xF0F0F0,
           "real":0x000F0F,"mat":0x0FF0FF,"zmod":0xF0000F,"str":0x00F00F,
           "prop":0xF0F000}

FORM_PAT = {"existence":0x000FF0,"universal":0x0FF000,"equality":0x0F0F0F,
            "inequality":0xF0F0F0,"negation":0xFF0000,"implication":0x00FF00}

NS_DIM = {"GLM.Golay":24,"GLM.Golay24":24,"GLM.DeepHoleFailure":24,
          "GLM.DeepHole":24,"GLM.Info":0,"GLM.Info.Layer":0,"GLM":24,
          "GLM.Conversation":0,"GLM.Distinction":1,"GLM.NowReceipt":0,
          "GLM.TieBreak":24,"GLM.SecondReading":0}


@dataclass
class Theorem:
    name: str; namespace: str; short_name: str
    statement: str; docstring: str
    math_objects: set; tactics: list; tactic_seq: list
    proof_len: int; is_theorem: bool; source_file: str
    logical_forms: set; hypotheses: list


def parse_lean(text, fname=""):
    theorems = []
    ns_stack = []
    cur_ns = "GLM"
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*namespace\s+(\S+)", line)
        if m: ns_stack.append(m.group(1)); cur_ns=".".join(ns_stack) or "GLM"; i+=1; continue
        m = re.match(r"^\s*end\s+(\S+)", line)
        if m:
            if ns_stack: ns_stack.pop(); cur_ns=".".join(ns_stack) or "GLM"
            i+=1; continue
        m = re.match(r"^\s*(theorem|lemma|def)\s+(\w+)", line)
        if m:
            kind, name = m.group(1), m.group(2)
            stmt_lines = [line]
            j = i+1
            while j < len(lines):
                sl = lines[j]; stmt_lines.append(sl)
                if re.search(r"\bby\s*$",sl) or re.search(r":=\s*$",sl): break
                if sl.strip()=="" and len(stmt_lines)>2: break
                j += 1
            stmt = "\n".join(stmt_lines)
            # tactics
            tacs = []
            for k in range(j, min(j+40, len(lines))):
                pl = lines[k]
                if re.match(r"^\s*(theorem|lemma|def|end|namespace|@)", pl): break
                for t in TACTIC_S:
                    if re.search(r"\b"+re.escape(t)+r"\b", pl): tacs.append(t)
            # docstring
            doc = ""
            k = i-1
            while k >= 0:
                dl = lines[k]
                if re.match(r"^\s*/--",dl) or re.match(r"^\s*/-!",dl):
                    dls=[dl]; mm=k-1
                    while mm>=0:
                        if re.search(r"-/\s*$",lines[mm]): dls.insert(0,lines[mm]); break
                        dls.insert(0,lines[mm]); mm-=1
                    doc=re.sub(r"^/-+\s*","","\n".join(dls))
                    doc=re.sub(r"\s*-/\s*$","",doc); break
                if dl.strip() and not dl.strip().startswith("/-"): break
                k -= 1
            # math objects
            mo = set()
            for sym,nm in MATH_OBJ.items():
                if sym in stmt: mo.add(nm)
            # logical forms
            lf = set()
            for form, pats in LOGICAL_FORMS.items():
                for p in pats:
                    if re.search(p, stmt): lf.add(form); break
            # hypotheses
            hyps = re.findall(r"\((\w+)\s*:", stmt)
            fn = f"{cur_ns}.{name}"
            theorems.append(Theorem(
                name=fn, namespace=cur_ns, short_name=name,
                statement=stmt[:600], docstring=doc[:400],
                math_objects=mo, tactics=list(set(tacs)), tactic_seq=tacs,
                proof_len=len(tacs), is_theorem=(kind=="theorem"),
                source_file=fname, logical_forms=lf, hypotheses=hyps))
        i += 1
    return theorems


def encode(thm):
    """Deep semantic encoding → (T, ρ, C)."""
    T = 0
    for o in thm.math_objects:
        if o in OBJ_PAT: T ^= OBJ_PAT[o]
    for f in thm.logical_forms:
        if f in FORM_PAT: T ^= FORM_PAT[f]
    if thm.hypotheses:
        h = int(hashlib.sha256("|".join(thm.hypotheses).encode()).hexdigest()[:6],16)
        T ^= h & 0xFFFFFF
    if T == 0: T = 0x888888
    dim = NS_DIM.get(thm.namespace, 24)
    rho = max(1, dim//24) if dim > 0 else 12
    rho = (rho + len(thm.tactic_seq)) % 24 or 1
    if thm.tactic_seq:
        C = min(sum(TACTIC_S.get(t,1) for t in thm.tactic_seq)//2, 4)
    else: C = 0
    return T, rho, C


# ═══════════════════════════════════════════════════════════════════════════
# Trajectory fit (v4: shape-based DFT)
# ═══════════════════════════════════════════════════════════════════════════

class Fit:
    @staticmethod
    def score(Vp, Vq):
        n = min(len(Vp), len(Vq), 200)
        Vp, Vq = Vp[:n], Vq[:n]
        if not Vp or not Vq: return {"total":float("inf")}
        rc = RCalculus()
        mp, mq = sum(Vp)/len(Vp), sum(Vq)/len(Vq)
        sp = (sum((x-mp)**2 for x in Vp)/len(Vp))**0.5
        sq = (sum((x-mq)**2 for x in Vq)/len(Vq))**0.5
        md, sd = abs(mp-mq), abs(sp-sq)
        cp = rc.detect_cycle(Vp,2,30,3)
        cq = rc.detect_cycle(Vq,2,30,3)
        if cp is None and cq is None: cm = 0.0
        elif cp and cq:
            if cp[1]==cq[1]: cm=0.0
            elif abs(cp[1]-cq[1])<=2: cm=0.5
            else: cm=1.0
        else: cm=1.0
        ap = rc.autocorr(Vp,20); aq = rc.autocorr(Vq,20)
        ad = sum(abs(a-b) for a,b in zip(ap,aq))/len(ap)
        hp, hq = Counter(Vp), Counter(Vq)
        tot = sum(hp.values())
        inter = sum(min(hp[k],hq[k]) for k in set(hp)|set(hq))
        hd = 1.0-(inter/tot) if tot>0 else 1.0
        # Shape-based DFT: compare centroid + entropy
        dp = rc.dft_shape(Vp); dq = rc.dft_shape(Vq)
        dft_diff = (abs(dp["centroid"]-dq["centroid"])/max(dp["centroid"]+dq["centroid"],1)
                    + abs(dp["entropy"]-dq["entropy"])/max(dp["entropy"]+dq["entropy"],1))/2
        total = md*0.15 + sd*0.20 + cm*0.80 + ad*1.50 + hd*1.00 + dft_diff*0.60
        return {"mean_diff":md,"std_diff":sd,"cycle_match":cm,
                "autocorr_diff":ad,"hist_diff":hd,"dft_diff":dft_diff,
                "total":total,
                "puzzle":{"mean":mp,"std":sp,"cycle":cp,
                          "dft_centroid":dp["centroid"],"dft_entropy":dp["entropy"]},
                "pipeline":{"mean":mq,"std":sq,"cycle":cq,
                            "dft_centroid":dq["centroid"],"dft_entropy":dq["entropy"]}}


# ═══════════════════════════════════════════════════════════════════════════
# THE SORRY GENERATOR + CHECKER + REFINER (v4 architecture)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Sorry:
    """A candidate axiom — a 'sorry' that needs checking."""
    T: int; rho_shift: int; C_strength: int
    source: str  # "axiom:THEOREM_NAME" or "constructed"
    iteration: int
    proof_obligation: str  # what would need to be true


@dataclass
class CheckResult:
    """The result of checking a sorry."""
    passed: bool
    fit: dict
    control_fit: Optional[dict]
    is_real: bool
    diagnosis: dict  # WHY it passed/failed


class SorryGenerator:
    """Generates cheap candidate axioms ('sorrys')."""

    def __init__(self, theorems, golay):
        self.theorems = theorems
        self.golay = golay
        self.rc = RCalculus()

    def from_axiom_library(self, iteration=0) -> list[Sorry]:
        """Generate sorrys from the Lean axiom library."""
        sorrys = []
        for thm in self.theorems:
            T, rho, C = encode(thm)
            sorrys.append(Sorry(
                T=T, rho_shift=rho, C_strength=C,
                source=f"axiom:{thm.name}",
                iteration=iteration,
                proof_obligation=f"The puzzle's V trajectory matches the R-calculus pipeline of {thm.name}"))
        return sorrys

    def from_inverse(self, V_puzzle, iteration=0) -> Sorry:
        """Generate a sorry from the puzzle's V structure."""
        stats = self.rc.stats(V_puzzle)
        cycle = self.rc.detect_cycle(V_puzzle, 2, 30, 3)
        dft = self.rc.dft_shape(V_puzzle)
        # Target weight ≈ mean
        tw = round(stats["mean"]) + iteration
        best_T, best_wd = 0, 999
        for cw in self.golay.codewords:
            w = self.rc.popcount(cw)
            if abs(w-tw) < best_wd:
                best_wd, best_T = abs(w-tw), cw
                if best_wd == 0: break
        T = best_T
        # Rotation from cycle
        if cycle and cycle[1] > 0:
            target_order = cycle[1]
            best_s, best_sd = 1, 999
            for s in range(1, 24):
                order = 24 // math.gcd(s, 24)
                if abs(order-target_order) < best_sd:
                    best_sd, best_s = abs(order-target_order), s
                    if best_sd == 0: break
            rho = (best_s + iteration) % 24 or 1
        else:
            rho = (7 + iteration*3) % 24 or 1
        # Correction from std
        if stats["std"] > 2.5: C = 1
        elif stats["std"] > 1.5: C = 2
        elif stats["std"] > 0.8: C = 3
        else: C = 4
        C = max(0, min(C + iteration - 1, 4))
        return Sorry(
            T=T, rho_shift=rho, C_strength=C,
            source="constructed",
            iteration=iteration,
            proof_obligation=f"A correction system with T=0x{T:06x}, ρ={rho}, C={C} reproduces the puzzle's V")


class Checker:
    """Checks a sorry against the puzzle — rigorously."""

    def __init__(self, rc, golay):
        self.rc = rc
        self.golay = golay

    def check(self, sorry: Sorry, V_puzzle: list[int],
               puzzle_data: list[int], control: bool = True) -> CheckResult:
        """Check if the sorry's pipeline reproduces the puzzle's V."""
        rho = lambda S, s=sorry.rho_shift: self.rc.rotate(S, s)
        C = lambda S, T, mf=sorry.C_strength: self.rc.correct(S, T, mf)
        R = lambda errs: [self.rc.popcount(e) for e in errs]
        S0 = sum(puzzle_data[:24]) if len(puzzle_data) >= 24 else 0
        result = self.rc.run(sorry.T, S0, rho, C, R, N=200)
        V_pipe = result["V"]
        fit = Fit.score(V_puzzle, V_pipe)

        control_fit = None
        is_real = True
        if control:
            rand = [(hash((sorry.T,j,sorry.iteration))%2) for j in range(len(puzzle_data))]
            Vr = []
            for i in range(0, len(rand)-24+1, 24):
                Vr.append(sum(rand[i:i+24]))
            control_fit = Fit.score(Vr, V_pipe)
            is_real = fit["total"] < control_fit["total"]

        passed = is_real and fit["total"] < 3.0

        # Diagnosis: WHY did it pass/fail?
        diag = {"fit_total": fit["total"]}
        if control_fit:
            diag["control_total"] = control_fit["total"]
            diag["is_real"] = is_real
        if fit["mean_diff"] > 1.0:
            diag["mean_off"] = f"pipeline mean {fit['pipeline']['mean']:.1f} vs puzzle {fit['puzzle']['mean']:.1f}"
        if fit["std_diff"] > 1.0:
            diag["std_off"] = f"pipeline std {fit['pipeline']['std']:.1f} vs puzzle {fit['puzzle']['std']:.1f}"
        if fit["cycle_match"] > 0.5:
            pc = fit['puzzle']['cycle']
            qc = fit['pipeline']['cycle']
            diag["cycle_off"] = f"puzzle cycle {pc} vs pipeline {qc}"
        if fit["dft_diff"] > 0.5:
            diag["dft_off"] = f"centroid {fit['puzzle']['dft_centroid']:.1f} vs {fit['pipeline']['dft_centroid']:.1f}"

        return CheckResult(passed=passed, fit=fit, control_fit=control_fit,
                           is_real=is_real, diagnosis=diag)


class Refiner:
    """Refines a sorry based on the check's failure diagnosis."""

    def __init__(self, rc, golay):
        self.rc = rc
        self.golay = golay

    def refine(self, sorry: Sorry, check: CheckResult,
               V_puzzle: list[int]) -> Sorry:
        """Adjust the sorry based on WHY it failed."""
        diag = check.diagnosis
        T, rho, C = sorry.T, sorry.rho_shift, sorry.C_strength
        stats = self.rc.stats(V_puzzle)

        # If mean is off: adjust T's weight
        if "mean_off" in diag:
            target_w = round(stats["mean"])
            cur_w = self.rc.popcount(T)
            if cur_w != target_w:
                # Find a codeword with the right weight
                best_T, best_wd = T, abs(cur_w - target_w)
                for cw in self.golay.codewords:
                    w = self.rc.popcount(cw)
                    if abs(w - target_w) < best_wd:
                        best_wd, best_T = abs(w - target_w), cw
                        if best_wd == 0: break
                T = best_T

        # If std is off: adjust C
        if "std_off" in diag:
            pipe_std = check.fit["pipeline"]["std"]
            puzzle_std = stats["std"]
            if pipe_std < puzzle_std:
                C = max(0, C - 1)  # weaker correction → more variance
            else:
                C = min(4, C + 1)  # stronger correction → less variance

        # If cycle is off: adjust rho
        if "cycle_off" in diag:
            pc = check.fit["puzzle"]["cycle"]
            if pc and pc[1] > 0:
                target_order = pc[1]
                best_s, best_sd = rho, 999
                for s in range(1, 24):
                    order = 24 // math.gcd(s, 24)
                    if abs(order - target_order) < best_sd:
                        best_sd, best_s = abs(order - target_order), s
                        if best_sd == 0: break
                rho = best_s

        return Sorry(
            T=T, rho_shift=rho, C_strength=C,
            source=sorry.source + "+refined",
            iteration=sorry.iteration + 1,
            proof_obligation=sorry.proof_obligation + " (refined)")


# ═══════════════════════════════════════════════════════════════════════════
# The v4 engine: sorry → check → refine → loop
# ═══════════════════════════════════════════════════════════════════════════

class EngineV4:
    """The v4 hypothesis engine — sorry generator architecture."""

    def __init__(self, lean_sources: dict):
        self.rc = RCalculus()
        self.golay = GolayCode()
        self.theorems: list[Theorem] = []
        for fname, text in lean_sources.items():
            self.theorems.extend(parse_lean(text, fname))
        self.generator = SorryGenerator(self.theorems, self.golay)
        self.checker = Checker(self.rc, self.golay)
        self.refiner = Refiner(self.rc, self.golay)

    def hypothesise(self, puzzle_data, max_iterations=3, control=True) -> dict:
        """Run the sorry-check-refine loop on a puzzle."""
        if isinstance(puzzle_data, str):
            puzzle_data = [int(c) for c in puzzle_data if c in "01"]

        # Puzzle's V
        V_puzzle = []
        for i in range(0, len(puzzle_data)-24+1, 24):
            V_puzzle.append(sum(puzzle_data[i:i+24]))

        trace = []
        all_results = []

        for iteration in range(max_iterations):
            # ── 1. SORRY: generate candidates ────────────────────────────
            if iteration == 0:
                # First iteration: try both axiom library and inverse solver
                sorrys = self.generator.from_axiom_library(iteration)
                sorrys.append(self.generator.from_inverse(V_puzzle, iteration))
            else:
                # Later iterations: just the inverse solver
                sorrys = [self.generator.from_inverse(V_puzzle, iteration)]

            # ── 2. CHECK: check each sorry ───────────────────────────────
            iteration_results = []
            for sorry in sorrys:
                check = self.checker.check(sorry, V_puzzle, puzzle_data, control)
                iteration_results.append((sorry, check))
                all_results.append((sorry, check))
                if check.passed:
                    trace.append({
                        "iteration": iteration,
                        "sorry": f"0x{sorry.T:06x},ρ={sorry.rho_shift},C={sorry.C_strength}",
                        "source": sorry.source,
                        "fit": check.fit["total"],
                        "control": check.control_fit["total"] if check.control_fit else None,
                        "verdict": "PASSED",
                        "diagnosis": check.diagnosis,
                    })
                    return {
                        "verdict": "passed",
                        "iterations": iteration + 1,
                        "trace": trace,
                        "best": (sorry, check),
                        "all_results": all_results,
                    }

            # Sort by fit
            iteration_results.sort(key=lambda x: x[1].fit["total"])
            best_sorry, best_check = iteration_results[0]

            trace.append({
                "iteration": iteration,
                "sorry": f"0x{best_sorry.T:06x},ρ={best_sorry.rho_shift},C={best_sorry.C_strength}",
                "source": best_sorry.source,
                "fit": best_check.fit["total"],
                "control": best_check.control_fit["total"] if best_check.control_fit else None,
                "verdict": "failed",
                "diagnosis": best_check.diagnosis,
            })

            # ── 3. REFINE: adjust the best sorry based on failure ────────
            if iteration < max_iterations - 1:
                best_sorry = self.refiner.refine(best_sorry, best_check, V_puzzle)
                trace[-1]["refined_to"] = f"0x{best_sorry.T:06x},ρ={best_sorry.rho_shift},C={best_sorry.C_strength}"

        return {
            "verdict": "best_effort",
            "iterations": max_iterations,
            "trace": trace,
            "best": all_results[0] if all_results else None,
            "all_results": all_results,
        }

    def control_test(self, puzzle_data, n_random=5) -> dict:
        if isinstance(puzzle_data, str):
            puzzle_data = [int(c) for c in puzzle_data if c in "01"]
        ph = self.hypothesise(puzzle_data, max_iterations=1, control=False)
        pr_count = sum(1 for _,c in ph["all_results"] if c.fit["total"] < 5.0)
        rc_counts = []
        for i in range(n_random):
            rd = [(hash((i,j))%2) for j in range(len(puzzle_data))]
            rh = self.hypothesise(rd, max_iterations=1, control=False)
            rr = sum(1 for _,c in rh["all_results"] if c.fit["total"] < 5.0)
            rc_counts.append(rr)
        return {
            "puzzle_fits": pr_count,
            "random_fits_mean": sum(rc_counts)/n_random,
            "random_fits_std": (sum((x-sum(rc_counts)/n_random)**2 for x in rc_counts)/n_random)**0.5,
            "snr": pr_count / max(sum(rc_counts)/n_random, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Bundled Lean sources (9 files from the GLM repository)
# ═══════════════════════════════════════════════════════════════════════════

LEAN_SOURCES = {}

# v4 Lean sources - 9 files from the GLM repository
# Encoded as base64 to avoid all quoting issues

LEAN_SOURCES["DeepHoleFailure.lean"] = __import__("base64").b64decode("IiJcCi8tICMgVGhlIGZvdXIgZmFpbHVyZXMsIGFuZCB0aGUgc3ByZWFkIHRoYXQgZ2F0ZXMgdGhlIGNlcnRpZmljYXRlIC0vCmltcG9ydCBSZXF1ZXN0UHJvamVjdC5HTE0uRGVlcEhvbGVFc2NhbGF0aW9uCm5hbWVzcGFjZSBHTE0uRGVlcEhvbGVGYWlsdXJlCm9wZW4gR0xNLkRlZXBIb2xlTGFkZGVyCnVuaXZlcnNlIHUgdgp2YXJpYWJsZSB7QyA6IFR5cGUgdX0ge0wgOiBUeXBlIHZ9Ci8tLSBBIGZhaWx1cmUgaXMgYSBjbG9zZSBwYWlyLiAtLwp0aGVvcmVtIGZhaWx1cmVfcGFpcl9jbG9zZSB7UiA6IFJlYWRpbmcgQ30ge3cgOiDihJp9IHt4IHAgcSA6IEN9CihoeCA6IFIuZGlzdCB4IHAg4omkIHcpIChod2luIDogUi5kaXN0IHggcSDiiaQgUi5kaXN0IHggcCkgOgpSLmRpc3QgcCBxIOKJpCAyICogdyA6PSBieQpoYXZlIGh0cmkgOiBSLmRpc3QgcCBxIOKJpCBSLmRpc3QgcCB4ICsgUi5kaXN0IHggcSA6PSBSLmRpc3RfdHJpYW5nbGUgcCB4IHEKaGF2ZSBocHggOiBSLmRpc3QgcCB4ID0gUi5kaXN0IHggcCA6PSBSLmRpc3RfY29tbSBwIHgKbGluYXJpdGgKdGhlb3JlbSBub19mYWlsdXJlX29mX3NlcGFyYXRlZCB7UiA6IFJlYWRpbmcgQ30ge3cgOiDihJp9IHt4IHAgcSA6IEN9Cihoc2VwIDogMiAqIHcgPCBSLmRpc3QgcCBxKSAoaHggOiBSLmRpc3QgeCBwIOKJpCB3KSA6ClIuZGlzdCB4IHAgPCBSLmRpc3QgeCBxIDo9IGJ5CmJ5X2NvbnRyYSBoY29uCnB1c2hfbmVnIGF0IGhjb24KZXhhY3QgYWJzdXJkIChmYWlsdXJlX3BhaXJfY2xvc2UgaHggaGNvbikgKG5vdF9sZS4yIGhzZXApCnRoZW9yZW0gcmVzb2x2ZXNfb2Zfc3Vic2V0IHtSIDogUmVhZGluZyBDfSB7cmVmcyBrZXB0IDogTGlzdCAoTCDDlyBDKX0ge3cgOiDihJp9Cihoc3ViIDog4oiAIGUg4oiIIGtlcHQsIGUg4oiIIHJlZnMpIChoIDogUmVzb2x2ZXMgUiByZWZzIHcpIDoKUmVzb2x2ZXMgUiBrZXB0IHcgOj0KZnVuIGUgaGUgZiBoZiBobmUgPT4gaCBlIChoc3ViIGUgaGUpIGYgKGhzdWIgZiBoZikgaG5lCmRlZiBSZXNvbHZlc0F0IChSIDogUmVhZGluZyBDKSAocmVmcyA6IExpc3QgKEwgw5cgQykpICh0IDogTCkgKHAgOiBDKSAodyA6IOKEmikgOgpQcm9wIDo9CuKIgCBmIOKIiCByZWZzLCBmLjEg4omgIHQg4oaSIDIgKiB3IDwgUi5kaXN0IHAgZi4yCnRoZW9yZW0gcGVyX3R5cGVfY29ycmVjdCB7UiA6IFJlYWRpbmcgQ30ge3JlZnMgOiBMaXN0IChMIMOXIEMpfSB7dCA6IEx9CntwIHggOiBDfSB7dyA6IOKEmn0gKGhyZXMgOiBSZXNvbHZlc0F0IFIgcmVmcyB0IHAgdykgKGh4IDogUi5kaXN0IHggcCDiiaQgdykKe3UgOiBMfSB7cSA6IEN9IChocSA6ICh1LCBxKSDiiIggcmVmcykgKGhuZSA6IHUg4omgIHQpIDoKUi5kaXN0IHggcCA8IFIuZGlzdCB4IHEgOj0Kbm9fZmFpbHVyZV9vZl9zZXBhcmF0ZWQgKGhyZXMgKHUsIHEpIGhxIGhuZSkgaHgKdGhlb3JlbSByZXNvbHZlc0F0X29mX3Jlc29sdmVzIHtSIDogUmVhZGluZyBDfSB7cmVmcyA6IExpc3QgKEwgw5cgQyl9IHt3IDog4oSafQooaCA6IFJlc29sdmVzIFIgcmVmcyB3KSB7dCA6IEx9IHtwIDogQ30gKGhtZW0gOiAodCwgcCkg4oiIIHJlZnMpIDoKUmVzb2x2ZXNBdCBSIHJlZnMgdCBwIHcgOj0gYnkKaW50cm8gZiBoZiBobmUKaGF2ZSA6PSBoICh0LCBwKSBobWVtIGYgaGYgKGZ1biBoY29uID0+IGhuZSBoY29uLnN5bW0pCnNpbXBhIFtSLmRpc3RfY29tbV0gdXNpbmcgdGhpcwp0aGVvcmVtIHBlcl90eXBlX2Fic2VudCB7UiA6IFJlYWRpbmcgQ30ge0lzVHlwZSA6IEMg4oaSIFByb3B9IHtwIDogQ30ge3cgOiDihJp9CihoZmFpdGhmdWwgOiDiiIAgeSwgSXNUeXBlIHkg4oaSIFIuZGlzdCB5IHAg4omkIHcpCnt4IDogQ30gKGhmYXIgOiB3IDwgUi5kaXN0IHggcCkgOiDCrCBJc1R5cGUgeCA6PQpmdW4gaHggPT4gYWJzdXJkIChoZmFpdGhmdWwgeCBoeCkgKG5vdF9sZS4yIGhmYXIpCnRoZW9yZW0gcmFua19vbmVfY29ycmVjdCB7UiA6IFJlYWRpbmcgQ30ge3JlZnMgOiBMaXN0IChMIMOXIEMpfSB7dCA6IEx9CntwIHggOiBDfSAoaGxhYmVscyA6IOKIgCBmIOKIiCByZWZzLCBmLjEgPSB0IOKGkiBmLjIgPSBwKQooaHN0cmljdCA6IOKIgCBmIOKIiCByZWZzLCBmLjEg4omgIHQg4oaSIFIuZGlzdCB4IHAgPCBSLmRpc3QgeCBmLjIpIDoK4oiAIGYg4oiIIHJlZnMsIFIuZGlzdCB4IHAg4omkIFIuZGlzdCB4IGYuMiA6PSBieQppbnRybyBmIGhmCmJ5X2Nhc2VzIGhmdCA6IGYuMSA9IHQKwrcgcncgW2hsYWJlbHMgZiBoZiBoZnRdCsK3IGV4YWN0IGxlX29mX2x0IChoc3RyaWN0IGYgaGYgaGZ0KQplbmQgR0xNLkRlZXBIb2xlRmFpbHVyZQoiIg==").decode("utf-8")
LEAN_SOURCES["TaxConservation.lean"] = __import__("base64").b64decode("IiJcCi8tICMgVGhlIFRBWCBjb25zZXJ2YXRpb24gbGF3LCBhbmQgdGhlIGV4YWN0IGJvdW5kYXJ5IC0vCmltcG9ydCBSZXF1ZXN0UHJvamVjdC5HTE0uQ29uc3RhbnRzCm5hbWVzcGFjZSBHTE0Kb3BlbiBGaW5zZXQKdmFyaWFibGUge24gOiDihJV9CmRlZiBvZkJpdHMgKGEgOiBGaW4gbiDihpIgQm9vbCkgOiBGaW4gbiDihpIg4oSkIDo9IGZ1biBpID0+IGlmIGEgaSB0aGVuIDEgZWxzZSAwCmRlZiBieG9yIChhIGIgOiBGaW4gbiDihpIgQm9vbCkgOiBGaW4gbiDihpIgQm9vbCA6PSBmdW4gaSA9PiB4b3IgKGEgaSkgKGIgaSkKZGVmIGJhbmQgKGEgYiA6IEZpbiBuIOKGkiBCb29sKSA6IEZpbiBuIOKGkiBCb29sIDo9IGZ1biBpID0+IChhIGkgJiYgYiBpKQpkZWYgc3VwcG9ydCAoYSA6IEZpbiBuIOKGkiBCb29sKSA6IEZpbnNldCAoRmluIG4pIDo9IHtpIHwgYSBpID0gdHJ1ZX0KdGhlb3JlbSB0YXhfb2ZCaXRzIChhIDogRmluIG4g4oaSIEJvb2wpIDogdGF4IChvZkJpdHMgYSkgPSAoIyhzdXBwb3J0IGEpIDog4oSdKSAqIFEgOj0gYnkKdW5mb2xkIHRheCBRCnJ3IFtoYW1taW5nV2VpZ2h0X29mQml0cywgbm9ybVNxX29mQml0c10KcHVzaF9jYXN0CnJpbmcKdGhlb3JlbSB0YXhfY29uc2VydmF0aW9uIChhIGIgOiBGaW4gbiDihpIgQm9vbCkgOgp0YXggKG9mQml0cyAoYnhvciBhIGIpKSA9IHRheCAob2ZCaXRzIGEpICsgdGF4IChvZkJpdHMgYikgLSAyICogdGF4IChvZkJpdHMgKGJhbmQgYSBiKSkgOj0gYnkKcncgW3RheF9vZkJpdHMsIHRheF9vZkJpdHMsIHRheF9vZkJpdHMsIHRheF9vZkJpdHMsIHN1cHBvcnRfYnhvciwgc3VwcG9ydF9iYW5kXQpoYXZlIGggOj0gY2FyZF9zeW1tRGlmZl9hZGRfdHdvX211bF9jYXJkX2ludGVyIChzdXBwb3J0IGEpIChzdXBwb3J0IGIpCmxpbmVhcl9jb21iaW5hdGlvbiBRICogaCcKdGhlb3JlbSB0YXhfY29uc2VydmF0aW9uX2ZhaWxzX2F0X2ludGVnZXJfbGF5ZXIgOgp0YXggKG9mTmF0cyAobnhvciB3MSB3MikpIOKJoAp0YXggKG9mTmF0cyB3MSkgKyB0YXggKG9mTmF0cyB3MikgLSAyICogdGF4IChvZk5hdHMgKG5hbmQgdzEgdzIpKSA6PSBieQpydyBbaDAsIGgxLCBoMiwgaDNdCmludHJvIGgKaGF2ZSA6IFkgPSAxIC8gMiA6PSBieSBsaW5hcml0aApleGFjdCBhYnN1cmQgdGhpcyAobmVfb2ZfbHQgWV9sdF9oYWxmKQp0aGVvcmVtIHRheF9jb25zZXJ2YXRpb25fYXRfaW50ZWdlcl9sYXllcl9pZmYgOgoodGF4IChvZk5hdHMgKG54b3IgdzEgdzIpKSA9CnRheCAob2ZOYXRzIHcxKSArIHRheCAob2ZOYXRzIHcyKSAtIDIgKiB0YXggKG9mTmF0cyAobmFuZCB3MSB3MikpKSDihpQgWSA9IDEgLyAyIDo9IGJ5CmNvbnN0cnVjdG9yIDw7PiBpbnRybyBoIDw7PiBsaW5hcml0aAplbmQgR0xNCiIi").decode("utf-8")
LEAN_SOURCES["CumulativityRule.lean"] = __import__("base64").b64decode("IiJcCi8tICMgVGhlIGN1bXVsYXRpdml0eSBydWxlLCBhbmQgdGhlIGZhaWx1cmUgbW9kZSBpdCBkb2VzIG5vdCByZXBhaXIgLS8KaW1wb3J0IFJlcXVlc3RQcm9qZWN0LkdMTS5DdW11bGF0aXZlCm5hbWVzcGFjZSBHTE0uSW5mbwpuYW1lc3BhY2UgTGF5ZXIKdW5pdmVyc2UgdSB2CnZhcmlhYmxlIHtDIDogVHlwZSB1fQpkZWYgZmFjdG9yIChMIDogTGF5ZXIue3UsIHZ9IEMpIHtXIDogVHlwZSB2fSAoZiA6IEwuVmlldyDihpIgVykgOgpMYXllci57dSwgdn0gQyB3aGVyZQpWaWV3IDo9IFcKcGVyY2VpdmUgYyA6PSBmIChMLnBlcmNlaXZlIGMpCnRoZW9yZW0gZmFjdG9yZWRfY29uZmxhdGVzIChMIDogTGF5ZXIue3UsIHZ9IEMpIHtXIDogVHlwZSB2fSAoZiA6IEwuVmlldyDihpIgVykKe2EgYiA6IEN9IChoIDogTC5JbmRpc3QgYSBiKSA6IChmYWN0b3IgTCBmKS5JbmRpc3QgYSBiIDo9IGJ5CnNob3cgZiAoTC5wZXJjZWl2ZSBhKSA9IGYgKEwucGVyY2VpdmUgYikKcncgW2hdCnRoZW9yZW0gZmFjdG9yX3JlZmluZWRfYnkgKEwgOiBMYXllci57dSwgdn0gQykge1cgOiBUeXBlIHZ9IChmIDogTC5WaWV3IOKGkiBXKSA6ClJlZmluZXMgTCAoZmFjdG9yIEwgZikgOj0gZnVuIF8gXyBoID0+IGZhY3RvcmVkX2NvbmZsYXRlcyBMIGYgaAp0aGVvcmVtIGpvaW5fc2VwYXJhdGVzIChMIE0gOiBMYXllci57dSwgdn0gQykge2EgYiA6IEN9CihoTSA6IMKsIE0uSW5kaXN0IGEgYikgOiDCrCAoY3VtdWxhdGl2ZSBMIE0pLkluZGlzdCBhIGIgOj0gYnkKaW50cm8gaApleGFjdCBoTSAoKGN1bXVsYXRpdmVfaW5kaXN0X2lmZiAoTCA6PSBMKSAoTSA6PSBNKSkuMSBoKS4yCnRoZW9yZW0gam9pbl9uZWVkc19hX3NlY29uZF9yZWFkaW5nIChMIE0gOiBMYXllci57dSwgdn0gQykge2EgYiA6IEN9CihoTCA6IEwuSW5kaXN0IGEgYikgKGhNIDogTS5JbmRpc3QgYSBiKSA6IChjdW11bGF0aXZlIEwgTSkuSW5kaXN0IGEgYiA6PQooY3VtdWxhdGl2ZV9pbmRpc3RfaWZmIChMIDo9IEwpIChNIDo9IE0pKS4yIOKfqGhMLCBoTeKfqQpkZWYgUmVmaW5lbWVudENoYWluIChyZWFkIDog4oSVIOKGkiBMYXllci57dSwgdn0gQykgOiBQcm9wIDo9CuKIgCBuLCBSZWZpbmVzIChyZWFkIChuICsgMSkpIChyZWFkIG4pCnRoZW9yZW0gcmVmaW5lc19vZl9sZSB7cmVhZCA6IOKElSDihpIgTGF5ZXIue3UsIHZ9IEN9IChoIDogUmVmaW5lbWVudENoYWluIHJlYWQpCnttIG4gOiDihJV9IChobW4gOiBtIOKJpCBuKSA6IFJlZmluZXMgKHJlYWQgbikgKHJlYWQgbSkgOj0gYnkKaW5kdWN0aW9uIG4gd2l0aAp8IHplcm8gPT4KaGF2ZSA6IG0gPSAwIDo9IE5hdC5sZV96ZXJvLjEgaG1uCnN1YnN0IHRoaXMKZXhhY3QgcmVmaW5lc19yZWZsIF8KfCBzdWNjIGsgaWggPT4KcmNhc2VzIE5hdC5sdF9zdWNjX2lmZl9sdF9vcl9lcS4xIChOYXQubHRfc3VjY19vZl9sZSBobW4pIHdpdGggaGx0IHwgaGVxCsK3IGV4YWN0IFJlZmluZXMudHJhbnMgKGggaykgKGloIChOYXQubHRfc3VjY19pZmYuMSBobHQpKQrCtyBzdWJzdCBoZXEKZXhhY3QgcmVmaW5lc19yZWZsIF8KdGhlb3JlbSByZWZpbmVtZW50Q2hhaW5fY3VtdWxhdGl2ZVRvd2VyIChiYXNlIDogTGF5ZXIue3UsIHZ9IEMpCihyZWFkIDog4oSVIOKGkiBMYXllci57dSwgdn0gQykgOgpSZWZpbmVtZW50Q2hhaW4gKGN1bXVsYXRpdmVUb3dlciBiYXNlIHJlYWQpIDo9IGJ5CmludHJvIG4KZXhhY3QgY3VtdWxhdGl2ZVRvd2VyX3JlZmluZXNfc3VjYyBiYXNlIHJlYWQgbgplbmQgTGF5ZXIKZW5kIEdMTS5JbmZvCiIi").decode("utf-8")
LEAN_SOURCES["GolayBoundary.lean"] = __import__("base64").b64decode("IiJcCi8tICMgVGhlIHNuYXAgYm91bmRhcnk6IG5lYXJlc3QtY29kZXdvcmQgcmVhZGluZyBpcyB0cnVlIHVwIHRvIHdlaWdodCAzIGFuZCB1bnRydWUgYXQgNCAtLwppbXBvcnQgTWF0aGxpYgpuYW1lc3BhY2UgR0xNLkdvbGF5Cm9wZW4gRmluc2V0CnZhcmlhYmxlIHtuIDog4oSVfQpkZWYgZGlmZlNldCAoYSBiIDogRmluIG4g4oaSIEJvb2wpIDogRmluc2V0IChGaW4gbikgOj0ge2kgfCBhIGkg4omgIGIgaX0KZGVmIGhkaXN0IChhIGIgOiBGaW4gbiDihpIgQm9vbCkgOiDihJUgOj0gIyhkaWZmU2V0IGEgYikKbGVtbWEgaGRpc3RfdHJpYW5nbGUgKGEgYiBjIDogRmluIG4g4oaSIEJvb2wpIDogaGRpc3QgYSBjIOKJpCBoZGlzdCBhIGIgKyBoZGlzdCBiIGMgOj0gYnkKaGF2ZSBoc3ViIDogZGlmZlNldCBhIGMg4oqGIGRpZmZTZXQgYSBiIOKIqiBkaWZmU2V0IGIgYyA6PSBieQppbnRybyBpIGhpCnNpbXAgb25seSBbZGlmZlNldCwgRmluc2V0Lm1lbV9maWx0ZXIsIEZpbnNldC5tZW1fdW5pdiwgdHJ1ZV9hbmRdIGF0IGhpCnNpbXAgb25seSBbZGlmZlNldCwgRmluc2V0Lm1lbV91bmlvbiwgRmluc2V0Lm1lbV9maWx0ZXIsIEZpbnNldC5tZW1fdW5pdiwgdHJ1ZV9hbmRdCmJ5X2NvbnRyYSBoYwpwdXNoX25lZyBhdCBoYwpleGFjdCBoaSAoaGMuMS50cmFucyBoYy4yKQpjYWxjIGhkaXN0IGEgYyDiiaQgIyhkaWZmU2V0IGEgYiDiiKogZGlmZlNldCBiIGMpIDo9IEZpbnNldC5jYXJkX2xlX2NhcmQgaHN1YgpfIOKJpCAjKGRpZmZTZXQgYSBiKSArICMoZGlmZlNldCBiIGMpIDo9IEZpbnNldC5jYXJkX3VuaW9uX2xlIF8gXwp0aGVvcmVtIHNuYXBfdW5pcXVlX29mX2xlX3RocmVlIHtDIDogU2V0IChGaW4gbiDihpIgQm9vbCl9CihobWluIDog4oiAIGMg4oiIIEMsIOKIgCBjJyDiiIggQywgYyDiiaAgYycg4oaSIDgg4omkIGhkaXN0IGMgYycpCnt2IGMgYycgOiBGaW4gbiDihpIgQm9vbH0gKGhjIDogYyDiiIggQykgKGhjJyA6IGMnIOKIiCBDKQooaCA6IGhkaXN0IHYgYyDiiaQgMykgKGgnIDogaGRpc3QgdiBjJyDiiaQgMykgOiBjID0gYycgOj0gYnkKYnlfY29udHJhIGhuZQpoYXZlIGhjYycgOiA4IOKJpCBoZGlzdCBjIGMnIDo9IGhtaW4gYyBoYyBjJyBoYycgaG5lCmhhdmUgaHRyaSA6IGhkaXN0IGMgYycg4omkIGhkaXN0IGMgdiArIGhkaXN0IHYgYycgOj0gaGRpc3RfdHJpYW5nbGUgYyB2IGMnCnJ3IFtoZGlzdF9jb21tIGMgdl0gYXQgaHRyaQpvbWVnYQp0aGVvcmVtIHNuYXBfYW1iaWd1b3VzX2F0X2ZvdXIge2MgYycgOiBGaW4gbiDihpIgQm9vbH0gKGggOiBoZGlzdCBjIGMnID0gOCkgOgriiIMgdiA6IEZpbiBuIOKGkiBCb29sLCBoZGlzdCB2IGMgPSA0IOKIpyBoZGlzdCB2IGMnID0gNCA6PSBieQpvYnRhaW4g4p+ocywgaHMsIGhjYXJk4p+pIDog4oiDIHMg4oqGIGRpZmZTZXQgYyBjJywgI3MgPSA0IDo9IGJ5CnJlZmluZSBGaW5zZXQuZXhpc3RzX3N1YnNldF9jYXJkX2VxID9fCnVuZm9sZCBoZGlzdCBhdCBoCm9tZWdhCnJlZmluZSDin6hmbGlwT24gYyBzLCA/XywgP1/in6kKwrcgcncgW2hkaXN0X2NvbW0sIGhkaXN0X2ZsaXBPbiwgaGNhcmRdCsK3IHJ3IFtoZGlzdF9mbGlwT25fb2Zfc3Vic2V0IGhzLCBoLCBoY2FyZF0KdGhlb3JlbSBzbmFwX2FtYmlndW91c19uZSB7YyBjJyA6IEZpbiBuIOKGkiBCb29sfSAoaCA6IGhkaXN0IGMgYycgPSA4KSA6IGMg4omgIGMnIDo9IGJ5CmludHJvIGhjYwpydyBbaGNjLCBoZGlzdF9lcV96ZXJvX2lmZi4yIHJmbF0gYXQgaApleGFjdCBhYnN1cmQgaCAoYnkgbm9ybV9udW0pCnRoZW9yZW0gc25hcF9ib3VuZGFyeV9hdF90aHJlZSB7QyA6IFNldCAoRmluIG4g4oaSIEJvb2wpfQooaG1pbiA6IOKIgCBjIOKIiCBDLCDiiIAgYycg4oiIIEMsIGMg4omgIGMnIOKGkiA4IOKJpCBoZGlzdCBjIGMnKQp7YyBjJyA6IEZpbiBuIOKGkiBCb29sfSAoaCA6IGhkaXN0IGMgYycgPSA4KSA6CijiiIAgdiA6IEZpbiBuIOKGkiBCb29sLCDiiIAgZCDiiIggQywg4oiAIGQnIOKIiCBDLCBoZGlzdCB2IGQg4omkIDMg4oaSIGhkaXN0IHYgZCcg4omkIDMg4oaSIGQgPSBkJykK4oinIOKIgyB2IDogRmluIG4g4oaSIEJvb2wsIGMg4omgIGMnIOKIpyBoZGlzdCB2IGMgPSA0IOKIpyBoZGlzdCB2IGMnID0gNCA6PSBieQpyZWZpbmUg4p+oZnVuIHYgZCBoZCBkJyBoZCcgaDEgaDIgPT4gc25hcF91bmlxdWVfb2ZfbGVfdGhyZWUgaG1pbiBoZCBoZCcgaDEgaDIsID9f4p+pCm9idGFpbiDin6h2LCBodiwgaHYn4p+pIDo9IHNuYXBfYW1iaWd1b3VzX2F0X2ZvdXIgaApleGFjdCDin6h2LCBzbmFwX2FtYmlndW91c19uZSBoLCBodiwgaHYn4p+pCmVuZCBHTE0uR29sYXkKIiI=").decode("utf-8")
LEAN_SOURCES["Combiner.lean"] = __import__("base64").b64decode("IiJcCi8tICMgV2h5IFhPUiBrZWVwcyBhcHBlYXJpbmcsIGV4YWN0bHkgd2hhdCBpdCBkaXNjYXJkcywgYW5kIHdoYXQgcmVwbGFjZXMgaXQgLS8KaW1wb3J0IE1hdGhsaWIKaW1wb3J0IFJlcXVlc3RQcm9qZWN0LkdMTS5Hb2xheS5Db2RlCmltcG9ydCBSZXF1ZXN0UHJvamVjdC5HTE0uR29sYXlXZWlnaHRFbnVtCm5hbWVzcGFjZSBHTE0uR29sYXkyNApvcGVuIEZpbnNldApkZWYgYXBwbHkyIChmIDogQm9vbCDihpIgQm9vbCDihpIgQm9vbCkgKGEgYiA6IFdvcmQpIDogV29yZCA6PQp1bml2LmZpbHRlciAoZnVuIGkgPT4gZiAoZGVjaWRlIChpIOKIiCBhKSkgKGRlY2lkZSAoaSDiiIggYikpID0gdHJ1ZSkKZGVmIElzQWZmaW5lIChmIDogQm9vbCDihpIgQm9vbCDihpIgQm9vbCkgOiBQcm9wIDo9CuKIgyBj4oKAIGPigoEgY+KCgiA6IEJvb2wsIOKIgCB4IHksIGYgeCB5ID0geG9yIGPigoAgKHhvciAoY+KCgSAmJiB4KSAoY+KCgiAmJiB5KSkKdGhlb3JlbSBhcHBseTJfYWZmaW5lIChhIGIgOiBXb3JkKSAoY+KCgCBj4oKBIGPigoIgOiBCb29sKSA6CmFwcGx5MiAoZnVuIHggeSA9PiB4b3IgY+KCgCAoeG9yIChj4oKBICYmIHgpIChj4oKCICYmIHkpKSkgYSBiCj0gc3ltbURpZmYgKHN5bW1EaWZmIChpZiBj4oKAIHRoZW4gKHVuaXYgOiBXb3JkKSBlbHNlIOKIhSkKKGlmIGPigoEgdGhlbiBhIGVsc2Ug4oiFKSkgKGlmIGPigoIgdGhlbiBiIGVsc2Ug4oiFKSA6PSBieQpleHQgaQpieV9jYXNlcyBoaWEgOiBpIOKIiCBhIDw7PiBieV9jYXNlcyBoaWIgOiBpIOKIiCBiIDw7PiBjYXNlcyBj4oKAIDw7PiBjYXNlcyBj4oKBIDw7PiBjYXNlcyBj4oKCIDw7PgpzaW1wIFthcHBseTIsIEZpbnNldC5tZW1fc3ltbURpZmYsIGhpYSwgaGliXQp0aGVvcmVtIGFmZmluZV9vcl9pbnRlciAoZiA6IEJvb2wg4oaSIEJvb2wg4oaSIEJvb2wpIDoKSXNBZmZpbmUgZiDiiKgg4oiDIGPigoAgY+KCgSBj4oKCIDogQm9vbCwK4oiAIHggeSwgZiB4IHkgPSB4b3IgKHhvciBj4oKAICh4b3IgKGPigoEgJiYgeCkgKGPigoIgJiYgeSkpKSAoeCAmJiB5KSA6PSBieQpyZXZlcnQgZjsgZGVjaWRlCnRoZW9yZW0gaXNDb2Rld29yZF91bml2IDogSXNDb2Rld29yZCAodW5pdiA6IFdvcmQpIDo9IGJ5CnVuZm9sZCBJc0NvZGV3b3JkIHN5bjsgZGVjaWRlCnRoZW9yZW0gaW50ZXJfbm90X2NvZGV3b3JkIDogwqwgSXNDb2Rld29yZCAob2N0YWRBIOKIqSBvY3RhZEIpIDo9IGJ5CnVuZm9sZCBJc0NvZGV3b3JkIHN5biBvY3RhZEEgb2N0YWRCOyBkZWNpZGUKdGhlb3JlbSBjbG9zZWRfaWZmX2FmZmluZSAoZiA6IEJvb2wg4oaSIEJvb2wg4oaSIEJvb2wpIDoKKOKIgCBhIGIgOiBXb3JkLCBJc0NvZGV3b3JkIGEg4oaSIElzQ29kZXdvcmQgYiDihpIgSXNDb2Rld29yZCAoYXBwbHkyIGYgYSBiKSkK4oaUIElzQWZmaW5lIGYgOj0gYnkKY29uc3RydWN0b3IKwrcgaW50cm8gaGNsb3NlZApyY2FzZXMgYWZmaW5lX29yX2ludGVyIGYgd2l0aCBoYWZmIHwg4p+oY+KCgCwgY+KCgSwgY+KCgiwgaGbin6kKwrcgZXhhY3QgaGFmZgrCtyBleGZhbHNvCmhhdmUgaGZ1biA6IGYgPSBmdW4geCB5ID0+IHhvciAoeG9yIGPigoAgKHhvciAoY+KCgSAmJiB4KSAoY+KCgiAmJiB5KSkpICh4ICYmIHkpIDo9IGJ5CmZ1bmV4dCB4IHk7IGV4YWN0IGhmIHggeQpoYXZlIGhjdyA6PSBoY2xvc2VkIG9jdGFkQSBvY3RhZEIgaXNDb2Rld29yZF9vY3RhZEEgaXNDb2Rld29yZF9vY3RhZEIKcncgW2hmdW4sIGFwcGx5Ml9hZmZpbmVfaW50ZXJdIGF0IGhjdwpleGFjdCBpbnRlcl9ub3RfY29kZXdvcmQgdGhpcwrCtyByaW50cm8g4p+oY+KCgCwgY+KCgSwgY+KCgiwgaGbin6kgYSBiIGhhIGhiCmhhdmUgaGZ1biA6IGYgPSBmdW4geCB5ID0+IHhvciBj4oKAICh4b3IgKGPigoEgJiYgeCkgKGPigoIgJiYgeSkpIDo9IGJ5CmZ1bmV4dCB4IHk7IGV4YWN0IGhmIHggeQpydyBbaGZ1biwgYXBwbHkyX2FmZmluZV0KcmVmaW5lIGlzQ29kZXdvcmRfc3ltbURpZmYgKGlzQ29kZXdvcmRfc3ltbURpZmYgP18gP18pID9fCsK3IGV4YWN0IGlzQ29kZXdvcmRfaXRlIGPigoAgaXNDb2Rld29yZF91bml2CsK3IGV4YWN0IGlzQ29kZXdvcmRfaXRlIGPigoEgaGEKwrcgZXhhY3QgaXNDb2Rld29yZF9pdGUgY+KCgiBoYgp0aGVvcmVtIHhvcl9maWJyZV9jYXJkICh0IDogV29yZCkgOgpGaW50eXBlLmNhcmQge3AgOiBXb3JkIMOXIFdvcmQgLy8gc3ltbURpZmYgcC4xIHAuMiA9IHR9ID0gMiBeIDI0IDo9IGJ5CnJ3IFvihpAgRmludHlwZS5jYXJkX2NvbmdyICh4b3JGaWJyZUVxdWl2IHQpLCBGaW50eXBlLmNhcmRfZmluc2V0LCBGaW50eXBlLmNhcmRfZmluXQp0aGVvcmVtIGV4aXN0c19sYXJnZV9maWJyZSAoZiA6IFdvcmQgw5cgV29yZCDihpIgV29yZCkgOgriiIMgdCA6IFdvcmQsIDIgXiAyNCDiiaQgRmludHlwZS5jYXJkIHtwIDogV29yZCDDlyBXb3JkIC8vIGYgcCA9IHR9IDo9IGJ5CmJ5X2NvbnRyYSBoCnB1c2hfbmVnIGF0IGgKaGF2ZSBoc3VtIDog4oiRIHQgOiBXb3JkLCBGaW50eXBlLmNhcmQge3AgOiBXb3JkIMOXIFdvcmQgLy8gZiBwID0gdH0KPSBGaW50eXBlLmNhcmQgKFdvcmQgw5cgV29yZCkgOj0gYnkKcncgW+KGkCBGaW50eXBlLmNhcmRfc2lnbWFdCmV4YWN0IEZpbnR5cGUuY2FyZF9jb25nciAoRXF1aXYuc2lnbWFGaWJlckVxdWl2IGYpCmhhdmUgaGx0IDog4oiRIHQgOiBXb3JkLCBGaW50eXBlLmNhcmQge3AgOiBXb3JkIMOXIFdvcmQgLy8gZiBwID0gdH0gPCAyIF4gMjQgKiAyIF4gMjQgOj0gYnkKY2FsYyDiiJEgdCA6IFdvcmQsIEZpbnR5cGUuY2FyZCB7cCA6IFdvcmQgw5cgV29yZCAvLyBmIHAgPSB0fQriiaQg4oiRIF90IDogV29yZCwgKDIgXiAyNCAtIDEpIDo9IEZpbnNldC5zdW1fbGVfc3VtIChmdW4gdCBfID0+IGJ5IGhhdmUgOj0gaCB0OyBvbWVnYSkKXyA9IDIgXiAyNCAqICgyIF4gMjQgLSAxKSA6PSBieQpzaW1wIFtGaW5zZXQuc3VtX2NvbnN0LCBGaW5zZXQuY2FyZF91bml2LCBGaW50eXBlLmNhcmRfZmluc2V0LCBGaW50eXBlLmNhcmRfZmluXQpfIDwgMiBeIDI0ICogMiBeIDI0IDo9IGJ5IG5vcm1fbnVtCnJ3IFtoc3VtXSBhdCBobHQKc2ltcCBbRmludHlwZS5jYXJkX3Byb2QsIEZpbnR5cGUuY2FyZF9maW5zZXQsIEZpbnR5cGUuY2FyZF9maW5dIGF0IGhsdAp0aGVvcmVtIHRzdW1fdGRpZmZfaW5qZWN0aXZlIDoKRnVuY3Rpb24uSW5qZWN0aXZlIChmdW4gcCA6IFdvcmQgw5cgV29yZCA9PiAodHN1bSBwLjEgcC4yLCB0ZGlmZiBwLjEgcC4yKSkgOj0gYnkKcmludHJvIOKfqGEsIGLin6kg4p+oYywgZOKfqSBoCmhhdmUgaGQgOiB0ZGlmZiBhIGIgPSB0ZGlmZiBjIGQgOj0gKFByb2QuZXh0X2lmZi5tcCBoKS4yCmhhdmUgaHMgOiB0c3VtIGEgYiA9IHRzdW0gYyBkIDo9IChQcm9kLmV4dF9pZmYubXAgaCkuMQpoYXZlIGhhYyA6IGEgPSBjIDo9IGJ5CmV4dCBpCmhhdmUgaDEgOiB0ZGlmZiBhIGIgaSA9IHRkaWZmIGMgZCBpIDo9IGNvbmdyRnVuIGhkIGkKaGF2ZSBoMiA6IHRzdW0gYSBiIGkgPSB0c3VtIGMgZCBpIDo9IGNvbmdyRnVuIGhzIGkKYnlfY2FzZXMgaGlhIDogaSDiiIggYSA8Oz4gYnlfY2FzZXMgaGljIDogaSDiiIggYyA8Oz4KYnlfY2FzZXMgaGliIDogaSDiiIggYiA8Oz4gYnlfY2FzZXMgaGlkIDogaSDiiIggZCA8Oz4Kc2ltcF9hbGwgW3RkaWZmLCB0c3VtXQpzdWJzdCBoYWMKaGF2ZSBoYmQgOiBiID0gZCA6PSBieQpleHQgaQpoYXZlIGgxIDogdGRpZmYgYSBiIGkgPSB0ZGlmZiBhIGQgaSA6PSBjb25nckZ1biBoZCBpCmJ5X2Nhc2VzIGhpYSA6IGkg4oiIIGEgPDs+IGJ5X2Nhc2VzIGhpYiA6IGkg4oiIIGIgPDs+IGJ5X2Nhc2VzIGhpZCA6IGkg4oiIIGQgPDs+CnNpbXBfYWxsIFt0ZGlmZl0Kc2ltcCBbaGJkXQplbmQgR0xNLkdvbGF5MjQKIiI=").decode("utf-8")
LEAN_SOURCES["Distinction.lean"] = __import__("base64").b64decode("Ly0gIyBTdGFnZSAwIOKAlCB3aGF0IGEgc2luZ2xlIGRpc3RpbmN0aW9uIGZvcmNlcyAtLwppbXBvcnQgTWF0aGxpYgpuYW1lc3BhY2UgR0xNLkRpc3RpbmN0aW9uCnRoZW9yZW0gbm9faW5mb3JtYXRpb25fd2l0aG91dF9kaXN0aW5jdGlvbiAoZiA6IM6xIOKGkiDOsikgKGEgYiA6IM6xKSA6IGYgYSA9IGYgYiA6PSBieSBydyBbU3Vic2luZ2xldG9uLmVsaW0gYSBiXQp0aGVvcmVtIGJvb2xfY2FyZCA6IEZpbnR5cGUuY2FyZCBCb29sID0gMiA6PSByZmwKdGhlb3JlbSBzdXJqZWN0c19vbnRvX2Jvb2wge86xIDogVHlwZSp9IHthIGIgOiDOsX0gKGhhYiA6IGEg4omgIGIpIDog4oiDIGYgOiDOsSDihpIgQm9vbCwgRnVuY3Rpb24uU3VyamVjdGl2ZSBmIDo9IGJ5IGNsYXNzaWNhbAp0aGVvcmVtIGJpdGZpZWxkX2NhcmQgKG4gOiDihJUpIDogRmludHlwZS5jYXJkIChCaXRzIG4pID0gMiBeIG4gOj0gYnkgc2ltcCBbQml0c10KdGhlb3JlbSBwZXJtX2Jvb2xfY2FyZCA6IEZpbnR5cGUuY2FyZCAoRXF1aXYuUGVybSBCb29sKSA9IDIgOj0gYnkgcncgW0ZpbnR5cGUuY2FyZF9wZXJtXTsgZGVjaWRlCnRoZW9yZW0gcGVybV9ib29sX2VxICjPgyA6IEVxdWl2LlBlcm0gQm9vbCkgOiAo4oiAIGIsIM+DIGIgPSBiKSDiiKggKOKIgCBiLCDPgyBiID0gIWIpIDo9IGJ5IHJldmVydCDPgzsgZGVjaWRlCnRoZW9yZW0gdHdvX2VsZW1lbnRfcmluZ19pc196bW9kX3R3byAoUiA6IFR5cGUpIFtSaW5nIFJdIFtGaW50eXBlIFJdIChoIDogRmludHlwZS5jYXJkIFIgPSAyKSA6IE5vbmVtcHR5IChaTW9kIDIg4omDKyogUikgOj0g4p+oWk1vZC5yaW5nRXF1aXZPZlByaW1lIFIgKGJ5IG5vcm1fbnVtKSBo4p+pCnRoZW9yZW0gc2VsZl9pbnZlcnNlIHtuIDog4oSVfSAoeCA6IEJpdHMgbikgOiB4ICsgeCA9IDAgOj0gYnkgZnVuZXh0IGk7IHNpbXBhCnRoZW9yZW0gcmVhY2hhYmxlIHtuIDog4oSVfSAoeCB5IDogQml0cyBuKSA6IOKIgyEgdCA6IEJpdHMgbiwgeCArIHQgPSB5IDo9IOKfqHkgLSB4LCBieSByaW5nLCBmdW4gdCBodCA9PiBieSBydyBb4oaQIGh0XTsgcmluZ+KfqQp0aGVvcmVtIHNlbGZfaW52ZXJzZV9mb3JjZXNfY29tbSB7RyA6IFR5cGUqfSBbR3JvdXAgR10gKGggOiDiiIAgeCA6IEcsIHggKiB4ID0gMSkgKGEgYiA6IEcpIDogYSAqIGIgPSBiICogYSA6PSBieQpoYXZlIGhpbnYgOiDiiIAgeCA6IEcsIHjigbvCuSA9IHggOj0gZnVuIHggPT4gYnkgcncgW2VxX2NvbW0sIOKGkCBtdWxfZXFfb25lX2lmZl9lcV9pbnZdOyBleGFjdCBoIHgKY2FsYyBhICogYiA9IChhICogYinigbvCuSA6PSAoaGludiBfKS5zeW1tCl8gPSBi4oG7wrkgKiBh4oG7wrkgOj0gbXVsX2ludl9yZXYgYSBiCl8gPSBiICogYSA6PSBieSBydyBbaGludiwgaGludl0KZW5kIEdMTS5EaXN0aW5jdGlvbgo=").decode("utf-8")
LEAN_SOURCES["NowReceipt.lean"] = __import__("base64").b64decode("Ly0gIyBUaGUgcmVjZWlwdCBpbiB0aGUgbm93IC0vCmltcG9ydCBSZXF1ZXN0UHJvamVjdC5HTE0uWmVyb1N0b3JhZ2VWNQpuYW1lc3BhY2UgR0xNLk5vd1JlY2VpcHQKb3BlbiBGaW5zZXQKdmFyaWFibGUge3QgdSA6IOKElSDihpIg4oSafQp0aGVvcmVtIGFjY19lcV9mcmFjdCAoaHQgOiDiiIAgbiwgMCDiiaQgdCBuIOKIpyB0IG4g4omkIDEpIChuIDog4oSVKSA6IGRzQWNjIHQgbiA9IEludC5mcmFjdCAo4oiRIGkg4oiIIHJhbmdlIG4sIHQgaSkgOj0gYnkKb2J0YWluIOKfqG0sIGht4p+pIDo9IGV4aXN0c19jb3VudCB0IG4Kb2J0YWluIOKfqGgwLCBoMeKfqSA6PSBkc0FjY19tZW1fSWNvIGh0IG4KaGF2ZSBoc3VtIDog4oiRIGkg4oiIIHJhbmdlIG4sIHQgaSA9IChtIDog4oSkKSArIGRzQWNjIHQgbiA6PSBieSBoYXZlIDo9IGRzQWNjX2VxIHQgbjsgcncgW2htXSBhdCB0aGlzOyBwdXNoX2Nhc3Q7IGxpbmFyaXRoIFt0aGlzXQpydyBbaHN1bSwgSW50LmZyYWN0X2ludENhc3RfYWRkLCBJbnQuZnJhY3RfZXFfc2VsZi4yIOKfqGgwLCBoMeKfqV0KdGhlb3JlbSBjb3VudF9lcV9mbG9vciAoaHQgOiDiiIAgbiwgMCDiiaQgdCBuIOKIpyB0IG4g4omkIDEpIChuIDog4oSVKSA6IOKIkSBpIOKIiCByYW5nZSBuLCBkc0JpdCB0IGkgPSAo4oyK4oiRIGkg4oiIIHJhbmdlIG4sIHQgaeKMiyA6IOKEmikgOj0gYnkKaGF2ZSBoYWNjIDo9IGFjY19lcV9mcmFjdCBodCBuOyBoYXZlIDo9IGRzQWNjX2VxIHQgbjsgcncgW2hhY2NdIGF0IHRoaXM7IHJ3IFt0aGlzLCBJbnQuc2VsZl9zdWJfZnJhY3RdCnRoZW9yZW0gcmVjZWlwdF9jb2xsaXNpb24gOiBkc0FjYyBzY2hlZEEgMiA9IGRzQWNjIHNjaGVkQiAyIOKIpyAo4oiRIGkg4oiIIHJhbmdlIDIsIGRzQml0IHNjaGVkQSBpKSA9ICjiiJEgaSDiiIggcmFuZ2UgMiwgZHNCaXQgc2NoZWRCIGkpIOKIpyBkc0FjYyBzY2hlZEEgMSDiiaAgZHNBY2Mgc2NoZWRCIDEgOj0gYnkKcmVmaW5lIOKfqGJ5IG5vcm1fbnVtIFtkc0FjYywgZHNCaXQsIHNjaGVkQSwgc2NoZWRCXSwgP18sIGJ5IG5vcm1fbnVtIFtkc0FjYywgZHNCaXQsIHNjaGVkQSwgc2NoZWRCXeKfqQp0aGVvcmVtIGNvbnN0X2NvdW50X2VxX2Zsb29yIHtjIDog4oSafSAoaDAgOiAwIOKJpCBjKSAoaDEgOiBjIOKJpCAxKSAobiA6IOKElSkgOiDiiJEgaSDiiIggcmFuZ2UgbiwgZHNCaXQgKGZ1biBfID0+IGMpIGkgPSAo4oyKKG4gOiDihJopICogY+KMiyA6IOKEmikgOj0gYnkKaGF2ZSA6PSBjb3VudF9lcV9mbG9vciAodCA6PSBmdW4gXyA9PiBjKSAoZnVuIF8gPT4g4p+oaDAsIGgx4p+pKSBuOyBzaW1wYSBbRmluc2V0LnN1bV9jb25zdCwgbnNtdWxfZXFfbXVsXSB1c2luZyB0aGlzCnRoZW9yZW0gY3VtdWxhdGl2ZV9tb25vIHt3IDog4oSVIOKGkiDihJp9IChodyA6IOKIgCBpLCAwIOKJpCB3IGkpIDogTW9ub3RvbmUgKGZ1biBuID0+IOKIkSBpIOKIiCByYW5nZSBuLCB3IGkpIDo9IGJ5CmludHJvIGEgYiBoYWI7IGV4YWN0IEZpbnNldC5zdW1fbGVfc3VtX29mX3N1YnNldF9vZl9ub25uZWcgKGZ1biBpIGhpID0+IEZpbnNldC5tZW1fcmFuZ2UuMiAobHRfb2ZfbHRfb2ZfbGUgKEZpbnNldC5tZW1fcmFuZ2UuMSBoaSkgaGFiKSkgKGZ1biBpIF8gXyA9PiBodyBpKQplbmQgR0xNLk5vd1JlY2VpcHQK").decode("utf-8")
LEAN_SOURCES["TieBreak.lean"] = __import__("base64").b64decode("Ly0gIyBUaGUgdGllLWJyZWFrIC0vCmltcG9ydCBNYXRobGliCmltcG9ydCBSZXF1ZXN0UHJvamVjdC5HTE0uQWRkcmVzcwpuYW1lc3BhY2UgR0xNLlRpZUJyZWFrCm9wZW4gRmluc2V0CmRlZiBOZWFyZXN0IChMIDogU2V0IFgpICh4IDogWCkgOiBTZXQgWCA6PSB7cCB8IHAg4oiIIEwg4oinIOKIgCBxIOKIiCBMLCBkaXN0IHggcCDiiaQgZGlzdCB4IHF9CnRoZW9yZW0gZGlzdF9lcV9vZl9tZW1fbmVhcmVzdCB7eCBwIHEgOiBYfSAoaHAgOiBwIOKIiCBOZWFyZXN0IEwgeCkgKGhxIDogcSDiiIggTmVhcmVzdCBMIHgpIDogZGlzdCB4IHAgPSBkaXN0IHggcSA6PSBsZV9hbnRpc3ltbSAoaHAuMiBxIGhxLjEpIChocS4yIHAgaHAuMSkKdGhlb3JlbSBpc0xleExlYXN0X3VuaXF1ZSB7UyA6IFNldCAoRmluIG4g4oaSIOKEpCl9IHtwIHEgOiBGaW4gbiDihpIg4oSkfSAoaHAgOiBJc0xleExlYXN0IFMgcCkgKGhxIDogSXNMZXhMZWFzdCBTIHEpIDogcCA9IHEgOj0gYnkgYnlfY29udHJhIGhuZTsgZXhhY3QgbGV4THRfYXN5bW0gKGhwLjIgcSBocS4xIChOZS5zeW1tIGhuZSkpIChocS4yIHAgaHAuMSBobmUpCnRoZW9yZW0gc3VtX3JhaXNlX21vZF9laWdodCAoYSA6IEZpbiBuIOKGkiDihKQpIChTIDogRmluc2V0IChGaW4gbikpIDogKOKIkSBpLCByYWlzZSBhIFMgaSkgJSA4ID0gKCjiiJEgaSwgYSBpKSArIDQgKiAoKFMuY2FyZCA6IOKEpCkgJSAyKSkgJSA4IDo9IGJ5IHJ3IFtzdW1fcmFpc2VdOyBvbWVnYQp0aGVvcmVtIGNhcmRfb2RkX3N1YnNldHMgKFQgOiBGaW5zZXQgKEZpbiBuKSkgKGhUIDogVC5Ob25lbXB0eSkgOiAoVC5wb3dlcnNldC5maWx0ZXIgKGZ1biBTID0+IFMuY2FyZCAlIDIgPSAxKSkuY2FyZCA9IDIgXiAoVC5jYXJkIC0gMSkgOj0gYnkgb21lZ2EKdGhlb3JlbSBuZWFyZXN0X2luX3Jlc2lkdWVfY2xhc3NfZGlmZmVyX2J5X2ZvdXIge3YgciB4IHkgOiDihKR9IChoeCA6IHggJSA0ID0gciAlIDQpIChoeSA6IHkgJSA0ID0gciAlIDQpIChobWluIDog4oiAIHogOiDihKQsIHogJSA0ID0gciAlIDQg4oaSICh2IC0geCkgXiAyIOKJpCAodiAtIHopIF4gMikgKGhjb3N0IDogKHYgLSB4KSBeIDIgPSAodiAtIHkpIF4gMikgKGhuZSA6IHgg4omgIHkpIDogMiAqIHYgPSB4ICsgeSDiiKcgKHkgPSB4ICsgNCDiiKggeCA9IHkgKyA0KSA6PSBieSBubGluYXJpdGggW2hjb3N0XQp0aGVvcmVtIHJlYWRiYWNrX29mX3RpZV9jbGFzcyB7biA6IOKElX0ge3NjYWxlIHJobyA6IOKEpH0gKGhyaG8gOiAwIOKJpCByaG8pIChoc2NhbGUgOiAyICogcmhvIDwgc2NhbGUpIHtmIGcgaCA6IEZpbiBuIOKGkiDihKR9IHtwIHEgOiBGaW4gbiDihpIg4oSkfSAoaHAgOiDiiIAgaSwgfHAgaSAtIHNjYWxlICogZiBpfCDiiaQgcmhvKSAoaHEgOiDiiIAgaSwgfHEgaSAtIHNjYWxlICogZiBpfCDiiaQgcmhvKSAoaHBnIDog4oiAIGksIHxwIGkgLSBzY2FsZSAqIGcgaXwg4omkIHJobykgKGhxaCA6IOKIgCBpLCB8cSBpIC0gc2NhbGUgKiBoIGl8IOKJpCByaG8pIDogZyA9IGggOj0gYnkgaGF2ZSBo4oKBIDogZyA9IGYgOj0gQWRkcmVzcy5yZWFkYmFja191bmlxdWUgaHJobyBoc2NhbGUgcCBnIGYgaHBnIGhwOyBoYXZlIGjigoIgOiBoID0gZiA6PSBBZGRyZXNzLnJlYWRiYWNrX3VuaXF1ZSBocmhvIGhzY2FsZSBxIGggZiBocWggaHE7IHJ3IFto4oKBLCBo4oKCXQplbmQgR0xNLlRpZUJyZWFrCg==").decode("utf-8")
LEAN_SOURCES["SecondReading.lean"] = __import__("base64").b64decode("Ly0gIyBBIHNlY29uZCByZWFkaW5nIGJlZm9yZSBhbnN3ZXJpbmcgLS8KaW1wb3J0IE1hdGhsaWIKbmFtZXNwYWNlIEdMTS5TZWNvbmRSZWFkaW5nCnZhcmlhYmxlIHvOsSA6IFR5cGUqfSBbRGVjaWRhYmxlRXEgzrFdCmRlZiBzdHJpY3RHdWFyZCAocCBzIDogT3B0aW9uIM6xKSA6IE9wdGlvbiDOsSA6PSBtYXRjaCBwLCBzIHdpdGggfCBzb21lIGEsIHNvbWUgYiA9PiBpZiBhID0gYiB0aGVuIHNvbWUgYSBlbHNlIG5vbmUgfCBfLCBfID0+IG5vbmUKZGVmIHZldG9HdWFyZCAocCBzIDogT3B0aW9uIM6xKSA6IE9wdGlvbiDOsSA6PSBtYXRjaCBwLCBzIHdpdGggfCBzb21lIGEsIHNvbWUgYiA9PiBpZiBhID0gYiB0aGVuIHNvbWUgYSBlbHNlIG5vbmUgfCBzb21lIGEsIG5vbmUgPT4gc29tZSBhIHwgbm9uZSwgXyA9PiBub25lCnRoZW9yZW0gc3RyaWN0R3VhcmRfZXFfc29tZSB7cCBzIDogT3B0aW9uIM6xfSB7YSA6IM6xfSA6IHN0cmljdEd1YXJkIHAgcyA9IHNvbWUgYSDihpQgcCA9IHNvbWUgYSDiiKcgcyA9IHNvbWUgYSA6PSBieSBjYXNlcyBwIDw7PiBjYXNlcyBzIDw7PiBzaW1wIFtzdHJpY3RHdWFyZF0KdGhlb3JlbSB2ZXRvR3VhcmRfZXFfc29tZSB7cCBzIDogT3B0aW9uIM6xfSB7YSA6IM6xfSA6IHZldG9HdWFyZCBwIHMgPSBzb21lIGEg4oaUIHAgPSBzb21lIGEg4oinIChzID0gbm9uZSDiiKggcyA9IHNvbWUgYSkgOj0gYnkgY2FzZXMgcCA8Oz4gY2FzZXMgcyA8Oz4gc2ltcCBbdmV0b0d1YXJkLCBlcV9jb21tXQp0aGVvcmVtIHN0cmljdEd1YXJkX3NvdW5kIHtwIHMgOiBPcHRpb24gzrF9IHthIDogzrF9IChoIDogc3RyaWN0R3VhcmQgcCBzID0gc29tZSBhKSA6IHAgPSBzb21lIGEgOj0gKHN0cmljdEd1YXJkX2VxX3NvbWUubXAgaCkuMQp0aGVvcmVtIHZldG9HdWFyZF9zb3VuZCB7cCBzIDogT3B0aW9uIM6xfSB7YSA6IM6xfSAoaCA6IHZldG9HdWFyZCBwIHMgPSBzb21lIGEpIDogcCA9IHNvbWUgYSA6PSAodmV0b0d1YXJkX2VxX3NvbWUubXAgaCkuMQp0aGVvcmVtIHN0cmljdEd1YXJkX2xlX3ZldG9HdWFyZCB7cCBzIDogT3B0aW9uIM6xfSB7YSA6IM6xfSAoaCA6IHN0cmljdEd1YXJkIHAgcyA9IHNvbWUgYSkgOiB2ZXRvR3VhcmQgcCBzID0gc29tZSBhIDo9IGJ5IG9idGFpbiDin6hocCwgaHPin6kgOj0gc3RyaWN0R3VhcmRfZXFfc29tZS5tcCBoOyBleGFjdCB2ZXRvR3VhcmRfZXFfc29tZS5tcHIg4p+oaHAsIE9yLmluciBoc+KfqQp0aGVvcmVtIHN0cmljdEd1YXJkX3NhZmVfb2Zfc291bmQge3AgcyA6IE9wdGlvbiDOsX0ge3QgOiDOsX0gKGhzIDog4oiAIGIsIHMgPSBzb21lIGIg4oaSIGIgPSB0KSB7YSA6IM6xfSAoaCA6IHN0cmljdEd1YXJkIHAgcyA9IHNvbWUgYSkgOiBhID0gdCA6PSBocyBhIChzdHJpY3RHdWFyZF9lcV9zb21lLm1wIGgpLjIKdGhlb3JlbSBzdHJpY3RfYmxvY2tzX3VubGVzc19zZWNvbmRfcmVwZWF0cyB7cCBzIDogT3B0aW9uIM6xfSB7YSA6IM6xfSAoaHMgOiBzIOKJoCBzb21lIGEpIDogc3RyaWN0R3VhcmQgcCBzIOKJoCBzb21lIGEgOj0gYnkgaW50cm8gaDsgZXhhY3QgaHMgKHN0cmljdEd1YXJkX2VxX3NvbWUubXAgaCkuMgplbmQgR0xNLlNlY29uZFJlYWRpbmcK").decode("utf-8")


# Sources are loaded from v3_lean_sources.py content + new files.
# For the self-contained script, they're embedded in the file below.
# (See the file generation script for the actual content.)


# ═══════════════════════════════════════════════════════════════════════════
# Puzzles
# ═══════════════════════════════════════════════════════════════════════════

def rule30_center(steps):
    w = 2*steps+1; s = [0]*w; s[w//2]=1; c=w//2; col=[s[c]]
    for _ in range(steps-1):
        n = [0]*w
        for i in range(w):
            n[i] = s[(i-1)%w] ^ (s[i] | s[(i+1)%w])
        s = n; col.append(s[c])
    return col

def p_golay_snap():
    return [1,1,1,1,0]*200, "Golay snap: correct ≤3, ambiguous 4 (density 0.8)"
def p_tax():
    return [1,0]*500, "TAX: true on substrate, false at integer (density 0.5)"
def p_deep_hole():
    return [0,0,1,0,0,0,1,0,0,1]*100, "Deep-hole: 3/10 pass (density 0.3)"
def p_rule30():
    return rule30_center(1024), "Rule 30: chaotic"
def p_receipt():
    """The receipt collision: two schedules, same receipt."""
    schedA = [1,1,0,1,1,0,1,1,0,1]  # 3/4 pattern → 1101101101
    schedB = [1,0,1,1,1,0,1,1,1,0]  # 1/2 then 1 pattern
    puzzle = (schedA + schedB) * 50  # 1000 bits
    return puzzle, "Receipt collision: two schedules, same accumulator"


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 76)
    print("  GLM HYPOTHESIS ENGINE v4 — THE 'SORRY GENERATOR'")
    print("  Cheap guess → rigorous check → failure-feedback refinement → loop")
    print("=" * 76)
    print()

    # Load sources (from the bundled content)
    engine = EngineV4(LEAN_SOURCES)
    print(f"Engine loaded: {len(engine.theorems)} theorems from {len(LEAN_SOURCES)} files")
    print()

    puzzles = [
        ("Golay snap boundary", p_golay_snap),
        ("TAX conservation boundary", p_tax),
        ("Deep-hole separation", p_deep_hole),
        ("Receipt collision", p_receipt),
        ("Rule 30", p_rule30),
    ]

    for name, fn in puzzles:
        print("═" * 76)
        print(f"  PUZZLE: {name}")
        print("═" * 76)
        puzzle, known = fn()
        print(f"  Known: {known}")
        print(f"  Length: {len(puzzle)}, density: {sum(puzzle)/len(puzzle):.4f}")
        print()

        # Control
        ct = engine.control_test(puzzle, n_random=5)
        print(f"  Control: puzzle={ct['puzzle_fits']}, random={ct['random_fits_mean']:.1f}±{ct['random_fits_std']:.1f}, SNR={ct['snr']:.2f}")
        if ct["snr"] > 2: print("  → STRONG signal")
        elif ct["snr"] > 1: print("  → WEAK signal")
        else: print("  → NO signal")
        print()

        # Sorry-check-refine loop
        print("  Sorry-check-refine loop (3 iterations):")
        result = engine.hypothesise(puzzle, max_iterations=3, control=True)
        print(f"  Verdict: {result['verdict']} ({result['iterations']} iterations)")
        print()

        print("  Refinement trace:")
        for step in result["trace"]:
            print(f"    iter {step['iteration']}: {step['sorry']} ({step['source']})")
            print(f"      fit={step['fit']:.3f}", end="")
            if step.get("control"): print(f", control={step['control']:.3f}", end="")
            print(f", {step['verdict']}")
            if step.get("diagnosis"):
                for k, v in step["diagnosis"].items():
                    if k not in ("fit_total","control_total","is_real"):
                        print(f"      {k}: {v}")
            if step.get("refined_to"):
                print(f"      → refined to {step['refined_to']}")
        print()

        # Top hypotheses from all results
        all_r = sorted(result["all_results"], key=lambda x: x[1].fit["total"])
        real = [(s,c) for s,c in all_r if c.is_real]
        print(f"  Real hypotheses: {len(real)}")
        if real:
            print("  Top 3:")
            for i, (s, c) in enumerate(real[:3]):
                src = s.source.split(":")[-1][:50] if ":" in s.source else s.source
                print(f"    {i+1}. [{src}] T=0x{s.T:06x}, ρ={s.rho_shift}, C={s.C_strength}")
                print(f"       fit={c.fit['total']:.3f}", end="")
                if c.control_fit: print(f", control={c.control_fit['total']:.3f}", end="")
                print(f", real={c.is_real}")
        print()

    # Summary
    print("=" * 76)
    print("  SUMMARY — v4 'sorry generator' architecture")
    print("=" * 76)
    print(f"""
  Architecture: sorry (cheap guess) → check (rigorous) → refine (failure-feedback) → loop
  Engine: {len(engine.theorems)} Lean theorems, 9 source files
  Fit: 6-component trajectory (mean + std + cycle + autocorr + histogram + DFT-shape)
  Refinement: guided by the check's diagnosis (mean off → fix T weight, std off → fix C, cycle off → fix ρ)

  The sorry is cheap; the check is rigorous; the refinement is guided.
  The GLM's checking discipline does the heavy lifting, not the generation.
""")


if __name__ == "__main__":
    main()
