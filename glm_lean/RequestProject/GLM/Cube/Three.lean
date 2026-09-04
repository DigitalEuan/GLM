import Mathlib
import RequestProject.GLM.Cube.Surface

/-!
# Three cubes: what the proposed rules actually give, and what does give the Golay code

`test_8_three_cube.py` proposes splitting the 24 cells into **three parallel
3-cubes** of 8 vertices, with three hierarchical rules:

* **Rule A** — each cube's six face parities are even (the script calls the
  resulting code `RM(2,3)`);
* **Rule B** — corresponding faces across the three cubes align (their parities
  sum to an even number);
* **Rule C** — the total weight is one of `0, 8, 12, 16, 24`.

This file checks that proposal exactly, and then repairs it.

## What the rules give (measured, not asserted)

* `ruleA_card` — the Rule-A cubes are **16** patterns, not `2^7`: Rule A is the
  first-order Reed–Muller code `RM(1,3)`, the affine functions of `(x,y,z)`
  (`ruleA_iff_affine`), **not** `RM(2,3)`, which is the 128-word even-weight
  code (`rm2_card`).  The label in the script is off by one order.
* `ruleB_of_ruleA` — Rule B is **empty as a constraint**: if every cube passes
  Rule A then every face parity is `0`, so the cross-cube sums are automatically
  even.  Rule B rejects nothing that Rule A accepts.
* `ruleA_min_weight`, `ruleA_weight_four_witness` — the three-cube Rule-A code
  is a `[24, 12, 4]` code: the right size (`ruleAB_card`, `2^12` words, the same
  as the Golay code), but minimum distance **4**, so it corrects one cell error,
  not three.
* `ruleC_is_a_real_filter` — Rule C therefore does bite: there are Rule-A/B
  words of weight 4.  But it destroys linearity (`ruleAC_not_linear`), so the
  filtered set is no longer a code one can compose in.
* `ruleA_code_is_not_golay` — and no relabelling of the 24 cells can fix this:
  the transported Rule-A code always contains a weight-4 word, while every
  nonzero MOG codeword has weight ≥ 8.

## What does work: Turyn's glue

Keeping the user's three cubes but changing the *glue* recovers everything.
With `A = RM(1,3)` (Rule A) and a second copy `A ∘ σ` of it obtained by the
explicit vertex relabelling `σ = ![0,1,2,4,3,6,7,5]`, put

    cube₀ = a + x,   cube₁ = b + x,   cube₂ = a + b + x     (`turyn`)

for `a, b ∈ A` and `x ∈ A ∘ σ`.  Then:

* `turyn_add`, `ruleA_add` — the construction is linear;
* `turyn_injective`, `turynCode_card` — `2^12 = 4096` codewords;
* `turyn_min_weight` — minimum weight **8**;
* `turyn_weight_enumerator` — weights `1, 759, 2576, 759, 1`, exactly the MOG
  enumerator of `CubeMOG.mog_weight_enumerator`.

So the three-cube picture *does* carry the Golay code — three 8-cell cubes,
each an affine-function cube, glued by a shared third word — provided the glue
is `(a+x, b+x, a+b+x)` and not a parity rule between corresponding faces.
(That these two `[24,12,8]` codes are the *same* code up to relabelling is the
classical uniqueness theorem for the binary Golay code; it is **not** proved
here.  What is proved here is that they have identical parameters and identical
weight enumerators.)
-/

namespace GLM.ThreeCube

open CubeMOG

set_option maxRecDepth 100000

/-! ## 1. One cube -/

/-- The eight vertices of a 3-cube, indexed by `x*4 + y*2 + z`. -/
abbrev Cube := Fin 8 → Bool

/-- Coordinate `k ∈ {0,1,2}` of vertex `v`. -/
def coord (k : Fin 3) (v : Fin 8) : Bool :=
  decide (((v : Nat) / (4 / 2 ^ (k : Nat))) % 2 = 1)

/-- The six faces: coordinate `k` fixed to `b`. -/
def onFace (k : Fin 3) (b : Bool) (v : Fin 8) : Bool := decide (coord k v = b)

/-- The parity of a face. -/
def faceParity (c : Cube) (k : Fin 3) (b : Bool) : Bool :=
  decide (Odd ((Finset.univ.filter fun v : Fin 8 => onFace k b v ∧ c v = true).card))

/-- **Rule A**: every face of the cube has even parity. -/
def RuleA (c : Cube) : Prop := ∀ (k : Fin 3) (b : Bool), faceParity c k b = false

instance : DecidablePred RuleA := fun _ => inferInstanceAs (Decidable (∀ _ _, _))

/-- The affine functions of `(x, y, z)`: the first-order Reed–Muller code. -/
def affine (c₀ c₁ c₂ c₃ : Bool) : Cube := fun v =>
  xor c₀ (xor (c₁ && coord 0 v) (xor (c₂ && coord 1 v) (c₃ && coord 2 v)))

/-- **Rule A is `RM(1,3)`.**  A cube has all face parities even exactly when its
cells are an affine function of the coordinates. -/
theorem ruleA_iff_affine (c : Cube) :
    RuleA c ↔ ∃ c₀ c₁ c₂ c₃, affine c₀ c₁ c₂ c₃ = c := by
  revert c; decide

/-- There are 16 Rule-A cubes: `RM(1,3)` is a `[8,4,4]` code. -/
theorem ruleA_card : (Finset.univ.filter RuleA).card = 16 := by decide

/-- For contrast, `RM(2,3)` — the even-weight code named in the script — has
128 words. -/
theorem rm2_card :
    (Finset.univ.filter fun c : Cube =>
      ¬ Odd ((Finset.univ.filter fun v : Fin 8 => c v = true).card)).card = 128 := by decide

/-- Rule A is closed under addition. -/
theorem ruleA_add {c d : Cube} (hc : RuleA c) (hd : RuleA d) :
    RuleA (fun v => xor (c v) (d v)) := by
  revert c d
  decide

/-- The weight of a cube. -/
def wtC (c : Cube) : Nat := (Finset.univ.filter fun v : Fin 8 => c v = true).card

/-- A nonzero Rule-A cube has weight at least 4. -/
theorem ruleA_min_weight (c : Cube) (h : RuleA c) (h0 : c ≠ fun _ => false) : 4 ≤ wtC c := by
  revert c; decide

/-! ## 2. Three cubes -/

/-- Three parallel cubes: 24 cells.  In the script's reading, cube 0 is the
language column, cube 1 the mathematics column, cube 2 the script column. -/
abbrev Tri := Fin 3 → Cube

/-- The weight of a three-cube configuration. -/
def wt3 (t : Tri) : Nat := wtC (t 0) + wtC (t 1) + wtC (t 2)

/-- **Rule A** for the whole configuration. -/
def RuleA3 (t : Tri) : Prop := ∀ n, RuleA (t n)

instance : DecidablePred RuleA3 := fun _ => inferInstanceAs (Decidable (∀ _, _))

/-- **Rule B**: for each face, the three parities sum to an even number. -/
def RuleB (t : Tri) : Prop :=
  ∀ (k : Fin 3) (b : Bool),
    xor (faceParity (t 0) k b) (xor (faceParity (t 1) k b) (faceParity (t 2) k b)) = false

/-- **Rule C**: the total weight is a Golay weight. -/
def RuleC (t : Tri) : Prop := wt3 t ∈ ({0, 8, 12, 16, 24} : Finset Nat)

instance : DecidablePred RuleC := fun _ => inferInstanceAs (Decidable (_ ∈ _))

/-- **Rule B is vacuous.**  If the three cubes satisfy Rule A, all their face
parities are `0`, so Rule B holds automatically: it rejects nothing. -/
theorem ruleB_of_ruleA {t : Tri} (h : RuleA3 t) : RuleB t := by
  intro k b
  rw [h 0 k b, h 1 k b, h 2 k b]
  rfl

/-- The Rule-A three-cube code has `2^12` words — the size of the Golay code. -/
theorem ruleAB_card : (Finset.univ.filter RuleA).card ^ 3 = 2 ^ 12 := by
  rw [ruleA_card]; norm_num

/-- The witness word: one affine cube, two empty ones. -/
def lightWord : Tri := ![affine false true false false, fun _ => false, fun _ => false]

theorem lightWord_ruleA3 : RuleA3 lightWord := by
  intro n
  fin_cases n
  · exact (ruleA_iff_affine _).mpr ⟨false, true, false, false, rfl⟩
  · decide
  · decide

/-- …but a weight-4 word passes Rules A and B, so the minimum distance of the
Rule-A code is 4: it corrects a single cell error, not three. -/
theorem ruleA_weight_four_witness :
    RuleA3 lightWord ∧ RuleB lightWord ∧ wt3 lightWord = 4 ∧ lightWord ≠ (fun _ _ => false) :=
  ⟨lightWord_ruleA3, ruleB_of_ruleA lightWord_ruleA3, by decide, by decide⟩

/-- **So Rule C is a genuine extra filter** — it rejects the weight-4 word that
Rules A and B accept. -/
theorem ruleC_is_a_real_filter :
    RuleA3 lightWord ∧ RuleB lightWord ∧ ¬ RuleC lightWord :=
  ⟨lightWord_ruleA3, ruleB_of_ruleA lightWord_ruleA3, by decide⟩

/-- A Rule-A word of total weight 8: one full cube. -/
def heavyWord : Tri := ![affine true false false false, fun _ => false, fun _ => false]

/-- A Rule-A word of total weight 12: a full cube and a half cube. -/
def heavyWord' : Tri :=
  ![affine true false false false, affine false true false false, fun _ => false]

theorem heavyWord_ruleA3 : RuleA3 heavyWord := by
  intro n
  fin_cases n
  · exact (ruleA_iff_affine _).mpr ⟨true, false, false, false, rfl⟩
  · decide
  · decide

theorem heavyWord'_ruleA3 : RuleA3 heavyWord' := by
  intro n
  fin_cases n
  · exact (ruleA_iff_affine _).mpr ⟨true, false, false, false, rfl⟩
  · exact (ruleA_iff_affine _).mpr ⟨false, true, false, false, rfl⟩
  · decide

/-- **…but Rule C is not linear.**  Two configurations pass Rules A, B and C
(total weights 8 and 12) whose sum has weight 4 and does not: the filtered set
is not a code one can compose inside. -/
theorem ruleAC_not_linear :
    (RuleA3 heavyWord ∧ RuleC heavyWord) ∧ (RuleA3 heavyWord' ∧ RuleC heavyWord') ∧
      ¬ RuleC (fun n v => xor (heavyWord n v) (heavyWord' n v)) :=
  ⟨⟨heavyWord_ruleA3, by decide⟩, ⟨heavyWord'_ruleA3, by decide⟩, by decide⟩

/-! ## 3. No relabelling turns Rule A into the Golay code -/

theorem wtG_eq_card (g : Grid) :
    wtG g = (Finset.univ.filter fun q : Fin 6 × Fin 4 => g q.1 q.2 = true).card := by
  rw [Finset.card_filter, Fintype.sum_prod_type]
  simp [wtG]

theorem wt3_eq_card (t : Tri) :
    wt3 t = (Finset.univ.filter fun p : Fin 3 × Fin 8 => t p.1 p.2 = true).card := by
  rw [Finset.card_filter, Fintype.sum_prod_type, Fin.sum_univ_three, wt3, wtC, wtC, wtC,
    Finset.card_filter, Finset.card_filter, Finset.card_filter]

/-- Weight is preserved by any relabelling of the 24 cells. -/
theorem wt_transport (e : (Fin 3 × Fin 8) ≃ (Fin 6 × Fin 4)) (t : Tri) :
    wtG (fun j i => t (e.symm (j, i)).1 (e.symm (j, i)).2) = wt3 t := by
  rw [wtG_eq_card, wt3_eq_card]
  refine (Finset.card_equiv e ?_).symm
  intro p
  simp

/-- **The three-cube Rule-A code is not the Golay code, under any relabelling of
the cells.**  It always carries a word of weight 4, and every nonzero MOG
codeword has weight at least 8. -/
theorem ruleA_code_is_not_golay (e : (Fin 3 × Fin 8) ≃ (Fin 6 × Fin 4)) :
    RuleA3 lightWord ∧ lightWord ≠ (fun _ _ => false) ∧
      ¬ IsMog (fun j i => lightWord (e.symm (j, i)).1 (e.symm (j, i)).2) := by
  refine ⟨lightWord_ruleA3, by decide, ?_⟩
  intro hmog
  set g : Grid := fun j i => lightWord (e.symm (j, i)).1 (e.symm (j, i)).2 with hg
  have hcard : wtG g = 4 := by
    rw [hg, wt_transport e lightWord]
    decide
  have hgz : g ≠ 0 := by
    intro h0
    rw [h0] at hcard
    simp [wtG] at hcard
  have h8 := mog_min_weight g hmog hgz
  rw [hcard] at h8
  omega

/-! ## 4. Turyn's glue: three cubes that *do* give a Golay code -/

/-- The vertex relabelling that produces the second copy of `RM(1,3)`. -/
def sigma : Fin 8 → Fin 8 := ![0, 1, 2, 4, 3, 6, 7, 5]

/-- **The three-cube Turyn construction**: `cube₀ = a + x`, `cube₁ = b + x`,
`cube₂ = a + b + x`, where `x` is read through the relabelling `sigma`. -/
def turyn (a b x : Cube) : Tri :=
  ![fun v => xor (a v) (x (sigma v)),
    fun v => xor (b v) (x (sigma v)),
    fun v => xor (xor (a v) (b v)) (x (sigma v))]

/-- The construction is linear in its three parameters. -/
theorem turyn_add (a b x a' b' x' : Cube) :
    (fun n v => xor (turyn a b x n v) (turyn a' b' x' n v)) =
      turyn (fun v => xor (a v) (a' v)) (fun v => xor (b v) (b' v))
            (fun v => xor (x v) (x' v)) := by
  funext n v
  fin_cases n <;> simp [turyn] <;> cases a v <;> cases b v <;> cases a' v <;> cases b' v <;>
    cases x (sigma v) <;> cases x' (sigma v) <;> rfl

/-- The parametrisation is injective, so the code has `16³ = 2^12` words. -/
theorem turyn_injective {a b x a' b' x' : Cube}
    (h : turyn a b x = turyn a' b' x') : a = a' ∧ b = b' ∧ x = x' := by
  have h0 : ∀ v, xor (a v) (x (sigma v)) = xor (a' v) (x' (sigma v)) := fun v =>
    congrFun (congrFun h 0) v
  have h1 : ∀ v, xor (b v) (x (sigma v)) = xor (b' v) (x' (sigma v)) := fun v =>
    congrFun (congrFun h 1) v
  have h2 : ∀ v, xor (xor (a v) (b v)) (x (sigma v)) =
      xor (xor (a' v) (b' v)) (x' (sigma v)) := fun v => congrFun (congrFun h 2) v
  have hx : ∀ v, x (sigma v) = x' (sigma v) := by
    intro v
    have e0 := h0 v
    have e1 := h1 v
    have e2 := h2 v
    revert e0 e1 e2
    cases a v <;> cases b v <;> cases a' v <;> cases b' v <;>
      cases x (sigma v) <;> cases x' (sigma v) <;> simp
  refine ⟨?_, ?_, ?_⟩
  · funext v
    have e0 := h0 v
    rw [hx v] at e0
    revert e0
    cases a v <;> cases a' v <;> cases x' (sigma v) <;> simp
  · funext v
    have e1 := h1 v
    rw [hx v] at e1
    revert e1
    cases b v <;> cases b' v <;> cases x' (sigma v) <;> simp
  · have hsurj : Function.Surjective sigma := by decide
    funext w
    obtain ⟨v, rfl⟩ := hsurj w
    exact hx v

/-- The Rule-A cubes, listed. -/
def ruleAList : List Cube :=
  (List.finRange 16).map fun k =>
    affine (decide ((k : Nat) % 2 = 1)) (decide ((k : Nat) / 2 % 2 = 1))
           (decide ((k : Nat) / 4 % 2 = 1)) (decide ((k : Nat) / 8 % 2 = 1))

theorem ruleAList_mem (c : Cube) : c ∈ ruleAList ↔ RuleA c := by
  revert c; decide

theorem ruleAList_length : ruleAList.length = 16 := by decide

/-- The Turyn three-cube code, listed. -/
def turynCode : List Tri :=
  ruleAList.flatMap fun a => ruleAList.flatMap fun b => ruleAList.map fun x => turyn a b x

theorem turynCode_length : turynCode.length = 4096 := by native_decide

/-- **`2^12` distinct codewords.** -/
theorem turynCode_card : turynCode.dedup.length = 2 ^ 12 := by native_decide

/-- **Minimum weight 8** — three times the error correction of the Rule-A code. -/
theorem turyn_min_weight :
    turynCode.all (fun t => decide (wt3 t = 0 ∨ 8 ≤ wt3 t)) = true := by native_decide

/-- **The Golay weight enumerator**, `1, 759, 2576, 759, 1`, cell for cell the
same as `CubeMOG.mog_weight_enumerator`. -/
theorem turyn_weight_enumerator :
    (turynCode.filter fun t => decide (wt3 t = 0)).length = 1 ∧
    (turynCode.filter fun t => decide (wt3 t = 8)).length = 759 ∧
    (turynCode.filter fun t => decide (wt3 t = 12)).length = 2576 ∧
    (turynCode.filter fun t => decide (wt3 t = 16)).length = 759 ∧
    (turynCode.filter fun t => decide (wt3 t = 24)).length = 1 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

/-- Each cube of a Turyn word still satisfies Rule A only when the glue `x`
vanishes on it; the glue is what makes the distance jump from 4 to 8. -/
theorem turyn_glue_needed :
    ∃ a b x : Cube, RuleA a ∧ RuleA b ∧ RuleA x ∧ ¬ RuleA3 (turyn a b x) := by
  refine ⟨fun _ => false, fun _ => false, affine false true false false, ?_, ?_, ?_, ?_⟩
  · decide
  · decide
  · exact (ruleA_iff_affine _).mpr ⟨false, true, false, false, rfl⟩
  · intro h
    exact absurd (h 0) (by decide)

end GLM.ThreeCube
