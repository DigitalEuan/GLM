import Mathlib
import RequestProject.ThreeCube
import RequestProject.Semantics

/-!
# Putting the sentences on the cube

`Semantics.lean` and `Chat.lean` build meaning; `ThreeCube.lean` builds a
`[24, 12, 8]` code out of three 8-vertex cubes.  This file joins them: a clause
of the language is *stored* as a three-cube codeword, so the substrate carries
the sentence and protects it.

## The frame

A clause — "the water is not hotter than the stone" — is three fields:

* **subject** (4 bits): which thing, and whether the clause is asserted or
  denied;
* **predicate** (4 bits): which of the six measured properties or relations;
* **object** (4 bits): the second thing, or "none".

Each 4-bit field is one Rule-A (affine) cube, and the three cubes are glued by
Turyn's rule `cube₀ = a + x`, `cube₁ = b + x`, `cube₂ = a + b + x`.  This is the
"face as function" idea in the attached scripts made exact: the third cube is
*computed*, not stored (`third_cube_is_computed`), and the glue is read straight
back off the record (`glue_recoverable`) — no search, no XOR-as-composition,
just a determined value.

## What is proved

* `clauseCode_injective` — the 60 clauses of the vocabulary get 60 distinct
  records: no two meanings collide (this was the failure mode of the earlier
  word-encoding runs).
* `clause_min_distance` — and any two of them differ in **at least 8 of the 24
  cells**.
* `clause_unique_decoding` — hence a clause damaged in up to **3 cells** is
  still recognised uniquely: the sentence survives damage that the parity-only
  layer could not have survived.
* `clause_repair_bound` — 3 is the guarantee, not the limit of ambition: it
  comes from the distance 8 established in `ThreeCube.turyn_min_weight`.
-/

namespace SentenceCode

open ThreeCube Semantics

set_option maxRecDepth 100000

/-! ## 1. Distance on the three cubes -/

/-- Cellwise difference of two records. -/
def dxor (t u : Tri) : Tri := fun n v => xor (t n v) (u n v)

/-- The number of cells in which two records differ. -/
def dist3 (t u : Tri) : Nat := wt3 (dxor t u)

theorem dist3_comm (t u : Tri) : dist3 t u = dist3 u t := by
  simp only [dist3]
  congr 1
  funext n v
  exact Bool.xor_comm _ _

theorem dist3_self (t : Tri) : dist3 t t = 0 := by
  have h : dxor t t = (fun _ _ => false) := by
    funext n v
    simp [dxor]
  rw [dist3, h]
  decide

theorem wt3_xor_le (t u : Tri) : wt3 (dxor t u) ≤ wt3 t + wt3 u := by
  classical
  rw [wt3_eq_card, wt3_eq_card, wt3_eq_card]
  have hsub : (Finset.univ.filter fun p : Fin 3 × Fin 8 => dxor t u p.1 p.2 = true) ⊆
      (Finset.univ.filter fun p : Fin 3 × Fin 8 => t p.1 p.2 = true) ∪
      (Finset.univ.filter fun p : Fin 3 × Fin 8 => u p.1 p.2 = true) := by
    intro p hp
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, dxor] at hp
    simp only [Finset.mem_union, Finset.mem_filter, Finset.mem_univ, true_and]
    revert hp
    cases t p.1 p.2 <;> cases u p.1 p.2 <;> simp
  exact le_trans (Finset.card_le_card hsub) (Finset.card_union_le _ _)

theorem dist3_triangle (t u r : Tri) : dist3 t u ≤ dist3 t r + dist3 r u := by
  have h : dxor t u = dxor (dxor t r) (dxor r u) := by
    funext n v
    simp only [dxor]
    cases t n v <;> cases u n v <;> cases r n v <;> rfl
  rw [dist3, h]
  exact wt3_xor_le _ _

/-! ## 2. The clause frame -/

/-- The four-bit fields are carried by affine cubes. -/
def cubeOfNat (k : Nat) : Cube :=
  affine (decide (k % 2 = 1)) (decide (k / 2 % 2 = 1)) (decide (k / 4 % 2 = 1))
    (decide (k / 8 % 2 = 1))

/-- Distinct field values give distinct cubes. -/
theorem cubeOfNat_injective :
    ((List.range 16).map cubeOfNat).Nodup := by decide

def entIdx : Ent → Nat
  | .water => 0 | .stone => 1 | .lamp => 2

/-- The subject field: which thing, plus the polarity of the clause. -/
def subjOf (l : Lit) : Nat :=
  (match l.1 with
    | .frozen e => entIdx e
    | .boiling e => entIdx e
    | .warm e => entIdx e
    | .heavy e => entIdx e
    | .hotter e _ => entIdx e
    | .heavier e _ => entIdx e) + (if l.2 then 0 else 8)

/-- The predicate field: which of the six measured properties or relations. -/
def predOf (l : Lit) : Nat :=
  match l.1 with
  | .frozen _ => 0 | .boiling _ => 1 | .warm _ => 2
  | .heavy _ => 3 | .hotter _ _ => 4 | .heavier _ _ => 5

/-- The object field: the second thing, or `0` for "none". -/
def objOf (l : Lit) : Nat :=
  match l.1 with
  | .hotter _ f => entIdx f + 1
  | .heavier _ f => entIdx f + 1
  | _ => 0

/-- **A clause as a three-cube codeword.** -/
def clauseCode (l : Lit) : Tri :=
  turyn (cubeOfNat (subjOf l)) (cubeOfNat (predOf l)) (cubeOfNat (objOf l))

/-! ## 3. The third cube is computed, and the glue is recoverable -/

/-- **Face as function.**  The third cube is not an independent store: it is the
sum of the first two and the glue. -/
theorem third_cube_is_computed (a b x : Cube) :
    (turyn a b x) 2 = fun v => xor (xor ((turyn a b x) 0 v) ((turyn a b x) 1 v)) (x (sigma v)) := by
  funext v
  have h0 : (turyn a b x) 0 v = xor (a v) (x (sigma v)) := rfl
  have h1 : (turyn a b x) 1 v = xor (b v) (x (sigma v)) := rfl
  have h2 : (turyn a b x) 2 v = xor (xor (a v) (b v)) (x (sigma v)) := rfl
  rw [h0, h1, h2]
  cases a v <;> cases b v <;> cases x (sigma v) <;> rfl

/-- **…and the glue is read straight back off the record**: the cellwise sum of
the three cubes is the glue word. -/
theorem glue_recoverable (a b x : Cube) (v : Fin 8) :
    xor (xor ((turyn a b x) 0 v) ((turyn a b x) 1 v)) ((turyn a b x) 2 v) = x (sigma v) := by
  have h0 : (turyn a b x) 0 v = xor (a v) (x (sigma v)) := rfl
  have h1 : (turyn a b x) 1 v = xor (b v) (x (sigma v)) := rfl
  have h2 : (turyn a b x) 2 v = xor (xor (a v) (b v)) (x (sigma v)) := rfl
  rw [h0, h1, h2]
  cases a v <;> cases b v <;> cases x (sigma v) <;> rfl

/-! ## 4. No two meanings collide, and damage is survivable -/

/-- **Distinct clauses get distinct records.** -/
theorem clauseCode_injective : (allLits.map clauseCode).Nodup := by native_decide

/-- **Any two clauses differ in at least 8 of the 24 cells.** -/
theorem clause_min_distance :
    allLits.all (fun l => allLits.all fun l' =>
      decide (l = l') || decide (8 ≤ dist3 (clauseCode l) (clauseCode l'))) = true := by
  native_decide

theorem clause_min_distance' {l l' : Lit} (h : l ≠ l') :
    8 ≤ dist3 (clauseCode l) (clauseCode l') := by
  have h1 := (List.all_eq_true.mp clause_min_distance) l (mem_allLits l)
  have h2 := (List.all_eq_true.mp h1) l' (mem_allLits l')
  simp only [Bool.or_eq_true, decide_eq_true_eq] at h2
  rcases h2 with h2 | h2
  · exact absurd h2 h
  · exact h2

/-- **A clause damaged in up to three cells is still recognised uniquely.**  If a
received record is within 3 cells of two clauses of the vocabulary, those
clauses are the same one. -/
theorem clause_unique_decoding {l l' : Lit} {r : Tri}
    (h1 : dist3 r (clauseCode l) ≤ 3) (h2 : dist3 r (clauseCode l') ≤ 3) : l = l' := by
  by_contra hne
  have hd : dist3 (clauseCode l) (clauseCode l') ≤ 6 := by
    have := dist3_triangle (clauseCode l) (clauseCode l') r
    rw [dist3_comm (clauseCode l) r] at this
    omega
  have := clause_min_distance' hne
  omega

/-- The guarantee in one line: three cells of damage anywhere on the surface,
and the clause still reads back. -/
theorem clause_repair_bound (l : Lit) (r : Tri) (h : dist3 r (clauseCode l) ≤ 3) :
    ∀ l' : Lit, dist3 r (clauseCode l') ≤ 3 → clauseCode l' = clauseCode l := by
  intro l' h'
  rw [clause_unique_decoding h' h]

end SentenceCode
