module

public import Mathlib

/-!
# Round 44: the 23 Niemeier root systems, counted

§5.1 of `GLM_Escalation_Boundaries_Exploration.md` lists the root systems of the Niemeier lattices
(equivalently, by Conway–Parker–Sloane, the types of deep holes of the Leech lattice). It lists 22
and calls them 23; `E₆⁴` is missing, also from the sketch's `DeepHoleType`.

The root system of a Niemeier lattice with roots is a simply-laced (ADE) root system of rank 24
whose components all have the **same Coxeter number** `h` (Niemeier; Venkov). This file checks the
combinatorial half of the classification: the ADE root systems with these two properties are
exactly 23, listed in `niemeier23`, and `E₆⁴` is the one the sketch omits. (That each of the 23
is the root system of exactly one Niemeier lattice is the classical theorem, cited, not proved.)

* `rank_cox_classification` — every non-empty multiset of ADE components of total rank 24, all of
  the same Coxeter number, is one of the 23 in `niemeier23`;
* `niemeier23_valid`, `niemeier23_card`, `niemeier23_nodup` — each of the 23 has these properties,
  and they are pairwise different;
* `sketch22_sub`, `niemeier23_diff_sketch22` — the sketch's 22 are among them, and the only one
  missing is `E₆⁴`.

FORMAL (`decide` on finite enumerations, no `native_decide`).
-/

@[expose] public section

namespace GLM.Escalation.Niemeier

/-- A connected simply-laced Dynkin type: `A n` (`n ≥ 1`), `D n` (`n ≥ 4`), `E₆`, `E₇`, `E₈`. -/
inductive Comp
  | A (n : ℕ)
  | D (n : ℕ)
  | E6
  | E7
  | E8
  deriving DecidableEq, Repr

namespace Comp

/-- The component exists (`A₀`, `D₀ … D₃` are excluded). -/
def Valid : Comp → Prop
  | A n => 1 ≤ n
  | D n => 4 ≤ n
  | _ => True

instance : DecidablePred Valid := fun c => by cases c <;> unfold Valid <;> infer_instance

/-- Rank. -/
def rank : Comp → ℕ
  | A n => n
  | D n => n
  | E6 => 6
  | E7 => 7
  | E8 => 8

/-- Coxeter number. -/
def cox : Comp → ℕ
  | A n => n + 1
  | D n => 2 * n - 2
  | E6 => 12
  | E7 => 18
  | E8 => 30

end Comp

open Comp

/-- The conditions on a Niemeier root system: non-empty, valid components, total rank 24, one
common Coxeter number. -/
def IsNiemeierType (M : Multiset Comp) : Prop :=
  M ≠ 0 ∧ (∀ c ∈ M, c.Valid) ∧ (M.map rank).sum = 24 ∧ ∀ c ∈ M, ∀ c' ∈ M, c.cox = c'.cox

/-- `k` copies of a component. -/
def pow (c : Comp) (k : ℕ) : Multiset Comp := Multiset.replicate k c

/-- The 23 root systems. -/
def niemeier23 : List (Multiset Comp) :=
  [pow (D 24) 1, pow (D 16) 1 + pow E8 1, pow E8 3, pow (A 24) 1, pow (D 12) 2,
   pow (A 17) 1 + pow E7 1, pow (D 10) 1 + pow E7 2, pow (A 15) 1 + pow (D 9) 1, pow (D 8) 3,
   pow (A 12) 2, pow (A 11) 1 + pow (D 7) 1 + pow E6 1, pow E6 4, pow (A 9) 2 + pow (D 6) 1,
   pow (D 6) 4, pow (A 8) 3, pow (A 7) 2 + pow (D 5) 2, pow (A 6) 4, pow (A 5) 4 + pow (D 4) 1,
   pow (D 4) 6, pow (A 4) 6, pow (A 3) 8, pow (A 2) 12, pow (A 1) 24]

/-- The 22 root systems listed in the sketch (§5.1 and its `DeepHoleType`). -/
def sketch22 : List (Multiset Comp) :=
  [pow (A 1) 24, pow (A 2) 12, pow (A 3) 8, pow (A 4) 6, pow (A 5) 4 + pow (D 4) 1, pow (A 6) 4,
   pow (A 7) 2 + pow (D 5) 2, pow (A 8) 3, pow (A 9) 2 + pow (D 6) 1,
   pow (A 11) 1 + pow (D 7) 1 + pow E6 1, pow (A 12) 2, pow (A 15) 1 + pow (D 9) 1,
   pow (A 17) 1 + pow E7 1, pow (A 24) 1, pow (D 4) 6, pow (D 6) 4, pow (D 8) 3,
   pow (D 10) 1 + pow E7 2, pow (D 12) 2, pow (D 16) 1 + pow E8 1, pow (D 24) 1, pow E8 3]

/-- The components of Coxeter number `h` (at most three). -/
def compsOf (h : ℕ) : List Comp :=
  [A (h - 1)] ++ (if h % 2 = 0 then [D (h / 2 + 1)] else []) ++
    (if h = 12 then [E6] else []) ++ (if h = 18 then [E7] else []) ++ (if h = 30 then [E8] else [])

theorem mem_compsOf {c : Comp} (hc : c.Valid) : c ∈ compsOf c.cox := by
  cases c with
  | A n => simp [compsOf, cox]
  | D n =>
    simp only [Valid] at hc
    simp only [compsOf, cox, List.mem_append, List.mem_cons]
    left; left; left; right
    rw [if_pos (by omega)]
    simp only [List.mem_singleton, D.injEq]
    omega
  | E6 => simp [compsOf, cox]
  | E7 => simp [compsOf, cox]
  | E8 => simp [compsOf, cox]

theorem cox_le_of_rank {c : Comp} (hc : c.Valid) (h : c.rank ≤ 24) : c.cox ≤ 46 := by
  cases c <;> simp_all [Valid, rank, cox] <;> omega

/-- Build the multiset with counts `k₀, k₁, k₂, …` of the listed components. -/
def build : List Comp → List ℕ → Multiset Comp
  | c :: cs, k :: ks => pow c k + build cs ks
  | _, _ => 0

/-- Total rank, validity and non-emptiness of `build cs ks`, computed on the count vector. -/
def rankOf : List Comp → List ℕ → ℕ
  | c :: cs, k :: ks => k * c.rank + rankOf cs ks
  | _, _ => 0

def validOf : List Comp → List ℕ → Bool
  | c :: cs, k :: ks => (k == 0 || decide c.Valid) && validOf cs ks
  | _, _ => true

/-- The table of the 23 root systems as (Coxeter number, counts of `compsOf h`). -/
def table : List (ℕ × List ℕ) :=
  [(46, [0, 1]), (30, [0, 1, 1]), (30, [0, 0, 3]), (25, [1]), (22, [0, 2]), (18, [1, 0, 1]),
   (18, [0, 1, 2]), (16, [1, 1]), (14, [0, 3]), (13, [2]), (12, [1, 1, 1]), (12, [0, 0, 4]),
   (10, [2, 1]), (10, [0, 4]), (9, [3]), (8, [2, 2]), (7, [4]), (6, [4, 1]), (6, [0, 6]),
   (5, [6]), (4, [8, 0]), (3, [12]), (2, [24, 0])]

/-- The finite check, on count vectors only: for every `h ≤ 46` and every count vector with
entries `≤ 24`, total rank 24, valid and non-zero means listed in `table`. -/
def checkH (h : ℕ) : Bool :=
  let cs := compsOf h
  let r : ℕ → List ℕ := fun i => if i < cs.length then List.range 25 else [0]
  (r 0).all fun a => (r 1).all fun d => (r 2).all fun e =>
    let ks := [a, d, e].take cs.length
    if rankOf cs ks = 24 ∧ ks.sum ≠ 0 ∧ validOf cs ks = true then decide ((h, ks) ∈ table)
    else true

set_option maxRecDepth 100000 in
theorem checkH_all : ∀ h < 47, checkH h = true := by decide +kernel

set_option maxRecDepth 100000 in
theorem table_build : ∀ e ∈ table, build (compsOf e.1) e.2 ∈ niemeier23 := by decide +kernel

theorem rank_build (cs : List Comp) (ks : List ℕ) :
    ((build cs ks).map rank).sum = rankOf cs ks := by
  induction cs generalizing ks with
  | nil => cases ks <;> rfl
  | cons c cs ih => cases ks with
    | nil => rfl
    | cons k ks => simp [build, rankOf, pow, ih]

theorem compsOf_length_le (h : ℕ) : (compsOf h).length ≤ 3 := by
  unfold compsOf
  by_cases h1 : h % 2 = 0 <;> by_cases h2 : h = 12 <;> by_cases h3 : h = 18 <;>
    by_cases h4 : h = 30 <;> simp_all

theorem compsOf_nodup (h : ℕ) : (compsOf h).Nodup := by
  unfold compsOf
  by_cases h1 : h % 2 = 0 <;> by_cases h2 : h = 12 <;> by_cases h3 : h = 18 <;>
    by_cases h4 : h = 30 <;> simp_all

theorem split_count (M : Multiset Comp) (c : Comp) :
    M = Multiset.replicate (M.count c) c + M.filter (· ≠ c) := by
  rw [← Multiset.filter_eq' M c]
  exact (Multiset.filter_add_not (· = c) M).symm

/-- A multiset supported on a duplicate-free list is the sum of its counts. -/
theorem eq_build_counts {M : Multiset Comp} {cs : List Comp} (hnd : cs.Nodup)
    (hsupp : ∀ c ∈ M, c ∈ cs) : M = build cs (cs.map M.count) := by
  induction cs generalizing M with
  | nil =>
    simp only [build]
    exact Multiset.eq_zero_of_forall_notMem fun c hc => by simpa using hsupp c hc
  | cons c cs ih =>
    simp only [List.map_cons, build, pow]
    have hnd' := (List.nodup_cons.1 hnd)
    set M' := M.filter (· ≠ c) with hM'
    have hsupp' : ∀ x ∈ M', x ∈ cs := by
      intro x hx
      rw [Multiset.mem_filter] at hx
      rcases List.mem_cons.1 (hsupp x hx.1) with h | h
      · exact absurd h hx.2
      · exact h
    have hcounts : cs.map M.count = cs.map M'.count := by
      refine List.map_congr_left fun x hx => ?_
      have : x ≠ c := fun h => hnd'.1 (h ▸ hx)
      simp [M', this]
    rw [hcounts, ← ih hnd'.2 hsupp']
    exact split_count M c

theorem count_le_24 {M : Multiset Comp} (hv : ∀ c ∈ M, c.Valid) (hr : (M.map rank).sum = 24)
    (c : Comp) : M.count c ≤ 24 := by
  by_cases hc : c ∈ M
  · have h1 : 1 ≤ c.rank := by
      have := hv c hc; cases c <;> simp only [Valid, rank] at this ⊢ <;> omega
    have h2 : M.count c * c.rank ≤ (M.map rank).sum := by
      conv_rhs => rw [split_count M c]
      simp
    nlinarith
  · simp [Multiset.count_eq_zero.2 hc]

theorem validOf_of {cs : List Comp} {ks : List ℕ} (h : ∀ c ∈ build cs ks, c.Valid) :
    validOf cs ks = true := by
  induction cs generalizing ks with
  | nil => cases ks <;> rfl
  | cons c cs ih => cases ks with
    | nil => rfl
    | cons k ks =>
      simp only [build, pow, Multiset.mem_add, Multiset.mem_replicate] at h
      simp only [validOf, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq, decide_eq_true_eq]
      refine ⟨?_, ih fun x hx => h x (Or.inr hx)⟩
      by_cases hk : k = 0
      · exact Or.inl hk
      · exact Or.inr (h c (Or.inl ⟨hk, rfl⟩))

theorem build_eq_zero_of {cs : List Comp} {ks : List ℕ} (h : ks.sum = 0) : build cs ks = 0 := by
  induction cs generalizing ks with
  | nil => cases ks <;> rfl
  | cons c cs ih => cases ks with
    | nil => rfl
    | cons k ks =>
      simp only [List.sum_cons] at h
      simp only [build, pow, show k = 0 by omega, Multiset.replicate_zero, zero_add]
      exact ih (by omega)

theorem sum_ne_zero_of {cs : List Comp} {ks : List ℕ} (h : build cs ks ≠ 0) : ks.sum ≠ 0 :=
  fun h' => h (build_eq_zero_of h')

/-- **Classification (combinatorial half).** Every ADE root system of rank 24 whose components
share one Coxeter number is one of the 23. -/
theorem rank_cox_classification (M : Multiset Comp) (hM : IsNiemeierType M) : M ∈ niemeier23 := by
  obtain ⟨hne, hv, hr, hcox⟩ := hM
  obtain ⟨c₀, hc₀⟩ := Multiset.exists_mem_of_ne_zero hne
  set h := c₀.cox
  have hsupp : ∀ c ∈ M, c ∈ compsOf h := fun c hc => by
    rw [show h = c.cox from hcox c₀ hc₀ c hc]; exact mem_compsOf (hv c hc)
  have hrank : c₀.rank ≤ 24 := by
    rw [← hr]; exact Multiset.le_sum_of_mem (Multiset.mem_map_of_mem rank hc₀)
  have hh : h < 47 := by have := cox_le_of_rank (hv c₀ hc₀) hrank; omega
  have hM := eq_build_counts (compsOf_nodup h) hsupp
  have hck := checkH_all h hh
  have hcnt := count_le_24 hv hr
  have hlen := compsOf_length_le h
  have key : ∀ (a d e : ℕ), a < 25 → d < 25 → e < 25 → ((compsOf h).length ≤ 0 → a = 0) →
      ((compsOf h).length ≤ 1 → d = 0) → ((compsOf h).length ≤ 2 → e = 0) →
      (compsOf h).map M.count = [a, d, e].take (compsOf h).length → M ∈ niemeier23 := by
    intro a d e ha hd he ha' hd' he' hks
    simp only [checkH, List.all_eq_true] at hck
    have hmem : ∀ i x, (i < (compsOf h).length → x < 25) → (¬ i < (compsOf h).length → x = 0) →
        x ∈ (if i < (compsOf h).length then List.range 25 else [0]) := by
      intro i x h1 h2
      split_ifs with hi
      · exact List.mem_range.2 (h1 hi)
      · simp [h2 hi]
    have := hck a (hmem 0 a (fun _ => ha) (fun hi => ha' (by omega)))
      d (hmem 1 d (fun _ => hd) (fun hi => hd' (by omega)))
      e (hmem 2 e (fun _ => he) (fun hi => he' (by omega)))
    rw [← hks] at this
    rw [if_pos ⟨by rw [← rank_build, ← hM, hr], sum_ne_zero_of (hM ▸ hne),
      validOf_of (hM ▸ hv)⟩] at this
    have hmem' := table_build _ (of_decide_eq_true this)
    simpa [← hM] using hmem'
  have c25 := fun c => Nat.lt_succ_of_le (hcnt c)
  rcases hcs : compsOf h with _ | ⟨x, _ | ⟨y, _ | ⟨z, _ | ⟨w, t⟩⟩⟩⟩
  · exact absurd (by rw [hM, hcs]; rfl) hne
  · exact key (M.count x) 0 0 (c25 x) (by omega) (by omega) (by simp [hcs]) (fun _ => rfl)
      (fun _ => rfl) (by rw [hcs]; simp)
  · exact key (M.count x) (M.count y) 0 (c25 x) (c25 y) (by omega) (by simp [hcs])
      (by simp [hcs]) (fun _ => rfl) (by rw [hcs]; simp)
  · exact key (M.count x) (M.count y) (M.count z) (c25 x) (c25 y) (c25 z) (by simp [hcs])
      (by simp [hcs]) (by simp [hcs]) (by rw [hcs]; simp)
  · rw [hcs] at hlen; simp at hlen; omega

/-- Each of the 23 satisfies the conditions. -/
theorem niemeier23_valid : ∀ M ∈ niemeier23, IsNiemeierType M := by
  unfold IsNiemeierType; decide +kernel

theorem niemeier23_card : niemeier23.length = 23 := rfl

theorem niemeier23_nodup : niemeier23.Nodup := by decide +kernel

/-- The sketch's 22 are among the 23. -/
theorem sketch22_sub : ∀ M ∈ sketch22, M ∈ niemeier23 := by decide +kernel

theorem sketch22_card : sketch22.length = 22 := rfl

/-- **The one the sketch misses is `E₆⁴`.** -/
theorem niemeier23_diff_sketch22 : niemeier23.filter (fun M => M ∉ sketch22) = [pow E6 4] := by
  decide +kernel

end GLM.Escalation.Niemeier
