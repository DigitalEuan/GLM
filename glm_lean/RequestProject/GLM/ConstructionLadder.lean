import RequestProject.GLM.Shortcut.Leech

/-!
# The construction ladder, and escalation that starts in the middle

`source_material/Golay codes and Hadamard matrices.txt` draws the route from
the integer grid to the Leech lattice as a ladder: `ℤ²⁴`, then the
checkerboard lattice `D₂₄`, then Construction `A`, `B`, `C`.  Two things about
that picture are formalised here, and the second is why the escalation in
`overlay/glm_universal/reasoning/ladder_escalation.py` walks the rungs the way
it does.

## §1 The rungs, and the shape they actually make

`IsZ`, `IsD`, `IsA`, `IsB` and `IsC` are the five rungs in the integral
(`×√8`) scaling this development already uses for `Λ₂₄`
(`GLM.LatticeShortcut.IsLeech`).  The containments that hold are proved:

* `isB_isA`, `isB_isC` — `B` sits under both `A` and `C`;
* `isA_isD`, `isC_isD`, `isD_isZ` — and everything sits under the
  checkerboard, which sits inside the grid.

The containment the note assumes — that the rungs are a single file — is
**false**, and `ladder_not_chain` refutes it with two explicit vectors:
`4·e₀` is in `A` and not in `C` (`fourE_isA`, `fourE_not_isC`), and the glue
vector `(-3, 1²³)` is in `C` and not in `A` (`glue_isC`, `glue_not_isA`).  The
five rungs form a diamond, so there are two distinct routes up it, and a
reading that climbs one has not seen the other.

## §2 The middle-out walk

`middleOut k` is the order in which a ladder of `2k+1` rungs is visited when
the walk starts at the middle rung and steps alternately up and down:
`k, k+1, k-1, k+2, k-2, …`.  `middleOut_head` says it starts in the middle,
`middleOut_length` that it is as long as the ladder, `middleOut_nodup` that it
repeats nothing, and `middleOut_perm_range` that it is therefore a permutation
of the rungs: a walk out from the middle misses nothing.

## §3 Escalation, and when the order cannot matter

An escalation is a walk along the rungs that stops at the first one that names
something: `firstNamed`.  `firstNamed_order_independent` is the safety
theorem — if every rung that names something names the *same* thing, then
every order of the walk returns the same answer, so the order can be chosen
for cost alone.  `visitCount_eq_one_of_head_named` is the cost theorem in its
sharpest case: a walk that starts where the answer is pays for one rung.
-/

namespace GLM.ConstructionLadder

open GLM.LatticeShortcut

/-! ## §1 The five rungs -/

/-- Rung `Z`: the raw integer grid.  Every integer vector is on it. -/
def IsZ (_x : Fin 24 → ℤ) : Prop := True

/-- Rung `D`: the checkerboard lattice `D₂₄`, cut out by one parity. -/
def IsD (x : Fin 24 → ℤ) : Prop := (2 : ℤ) ∣ ∑ i, x i

/-- Rung `A`: Construction `A`, the Golay lift — even coordinates whose
mod-4 pattern is a codeword.  The mask is taken on the coordinates divisible
by `4`, which is the convention `GLM.LatticeShortcut.IsLeech` uses at `m = 0`. -/
def IsA (x : Fin 24 → ℤ) : Prop :=
  (∀ i, (2 : ℤ) ∣ x i) ∧ IsGolay (maskOf fun i => decide ((4 : ℤ) ∣ (x i - 0)))

/-- Rung `B`: Construction `B`, which adds the mod-8 coordinate sum. -/
def IsB (x : Fin 24 → ℤ) : Prop := IsA x ∧ (8 : ℤ) ∣ ∑ i, x i

/-- Rung `C`: Construction `C` — the Leech lattice, `B` together with the odd
coset. -/
def IsC (x : Fin 24 → ℤ) : Prop := IsLeech x

theorem isB_isA {x : Fin 24 → ℤ} (h : IsB x) : IsA x := h.1

theorem isB_isC {x : Fin 24 → ℤ} (h : IsB x) : IsC x := by
  obtain ⟨⟨heven, hgolay⟩, hsum⟩ := h
  refine ⟨0, Or.inl rfl, ?_, hgolay, ?_⟩
  · intro i; simpa using heven i
  · simpa using hsum

theorem isA_isD {x : Fin 24 → ℤ} (h : IsA x) : IsD x :=
  Finset.dvd_sum fun i _ => h.1 i

theorem isC_isD {x : Fin 24 → ℤ} (h : IsC x) : IsD x := by
  obtain ⟨m, -, -, -, hsum⟩ := h
  obtain ⟨t, ht⟩ := hsum
  exact ⟨2 * m + 4 * t, by linarith⟩

theorem isD_isZ {x : Fin 24 → ℤ} (_h : IsD x) : IsZ x := trivial

theorem isB_isD {x : Fin 24 → ℤ} (h : IsB x) : IsD x := isA_isD (isB_isA h)

/-! ### The two witnesses that break the chain -/

/-- `4·e₀`: four in the first coordinate and nothing anywhere else. -/
def fourE : Fin 24 → ℤ := fun i => if i = 0 then 4 else 0

/-- The glue vector `(-3, 1²³)` of the odd coset. -/
def glue : Fin 24 → ℤ := fun i => if i = 0 then -3 else 1

theorem fourE_isA : IsA fourE := by
  constructor
  · intro i
    by_cases h : i = 0 <;> simp [fourE, h]
  · have hmask : (maskOf fun i => decide ((4 : ℤ) ∣ (fourE i - 0))) = 2 ^ 24 - 1 := by
      have hp : (fun i => decide ((4 : ℤ) ∣ (fourE i - 0))) = fun _ => true := by
        funext i
        by_cases h : i = 0 <;> simp [fourE, h]
      rw [hp, maskOf]
      decide
    rw [hmask]
    exact golay_allOnes

theorem fourE_not_isC : ¬ IsC fourE := by
  rintro ⟨m, hm, hpar, -, hsum⟩
  have h1 : (2 : ℤ) ∣ (fourE ⟨1, by norm_num⟩ - m) := hpar _
  have hfe : fourE ⟨1, by norm_num⟩ = 0 := by simp [fourE]
  rw [hfe] at h1
  have hm0 : m = 0 := by
    rcases hm with h | h
    · exact h
    · exfalso; rw [h] at h1; omega
  have hsum0 : ∑ i : Fin 24, fourE i = 4 := by
    simp [fourE, Finset.sum_ite_eq' Finset.univ (0 : Fin 24) (fun _ => (4 : ℤ))]
  rw [hm0, hsum0] at hsum
  omega

theorem glue_isC : IsC glue := by
  refine ⟨1, Or.inr rfl, ?_, ?_, ?_⟩
  · intro i
    by_cases h : i = 0 <;> simp [glue, h]
  · have hp : (fun i => decide ((4 : ℤ) ∣ (glue i - 1))) = fun _ => true := by
      funext i
      by_cases h : i = 0 <;> simp [glue, h]
    have hmask : (maskOf fun i => decide ((4 : ℤ) ∣ (glue i - 1))) = 2 ^ 24 - 1 := by
      rw [hp, maskOf]; decide
    rw [hmask]
    exact golay_allOnes
  · have hsum : ∑ i : Fin 24, glue i = 20 := by
      simp [glue]
      decide
    rw [hsum]
    norm_num

theorem glue_not_isA : ¬ IsA glue := by
  rintro ⟨heven, -⟩
  have := heven ⟨1, by norm_num⟩
  simp [glue] at this

/-- **The ladder is not a chain.**  `A` and `C` are incomparable: each holds a
vector the other does not. -/
theorem ladder_not_chain :
    (∃ x : Fin 24 → ℤ, IsA x ∧ ¬ IsC x) ∧ (∃ y : Fin 24 → ℤ, IsC y ∧ ¬ IsA y) :=
  ⟨⟨fourE, fourE_isA, fourE_not_isC⟩, ⟨glue, glue_isC, glue_not_isA⟩⟩

/-! ## §2 The middle-out walk -/

/-- The indices visited, after the middle, by a walk that steps alternately up
and down: `k+1, k-1, k+2, k-2, …`, `j` steps of it. -/
def middleOutTail (k : ℕ) : ℕ → List ℕ
  | 0 => []
  | j + 1 => middleOutTail k j ++ [k + (j + 1), k - (j + 1)]

/-- The middle-out visiting order of a ladder of `2k+1` rungs: start in the
middle, then out one step each way at a time. -/
def middleOut (k : ℕ) : List ℕ := k :: middleOutTail k k

theorem middleOut_head (k : ℕ) : (middleOut k).head? = some k := rfl

theorem middleOutTail_length (k j : ℕ) : (middleOutTail k j).length = 2 * j := by
  induction j with
  | zero => simp [middleOutTail]
  | succ j ih => simp [middleOutTail, ih]; ring

theorem middleOut_length (k : ℕ) : (middleOut k).length = 2 * k + 1 := by
  simp [middleOut, middleOutTail_length]

theorem mem_middleOutTail {k j x : ℕ} (h : x ∈ middleOutTail k j) :
    ∃ d, 1 ≤ d ∧ d ≤ j ∧ (x = k + d ∨ x = k - d) := by
  induction j with
  | zero => simp [middleOutTail] at h
  | succ j ih =>
      rw [middleOutTail, List.mem_append] at h
      rcases h with h | h
      · obtain ⟨d, hd1, hd2, hd3⟩ := ih h
        exact ⟨d, hd1, by omega, hd3⟩
      · simp at h
        rcases h with h | h
        · exact ⟨j + 1, by omega, le_rfl, Or.inl h⟩
        · exact ⟨j + 1, by omega, le_rfl, Or.inr h⟩

theorem middleOutTail_nodup (k j : ℕ) (hj : j ≤ k) : (middleOutTail k j).Nodup := by
  induction j with
  | zero => simp [middleOutTail]
  | succ j ih =>
      have hj' : j ≤ k := by omega
      rw [middleOutTail]
      refine List.Nodup.append (ih hj') ?_ ?_
      · simp
        omega
      · intro a ha hb
        obtain ⟨d, hd1, hd2, hd3⟩ := mem_middleOutTail ha
        simp at hb
        rcases hd3 with rfl | rfl <;> rcases hb with hb | hb <;> omega

theorem middleOut_nodup (k : ℕ) : (middleOut k).Nodup := by
  rw [middleOut, List.nodup_cons]
  refine ⟨?_, middleOutTail_nodup k k le_rfl⟩
  intro h
  obtain ⟨d, hd1, hd2, hd3⟩ := mem_middleOutTail h
  omega

theorem middleOut_lt (k : ℕ) : ∀ x ∈ middleOut k, x < 2 * k + 1 := by
  intro x hx
  rw [middleOut, List.mem_cons] at hx
  rcases hx with rfl | hx
  · omega
  · obtain ⟨d, hd1, hd2, hd3⟩ := mem_middleOutTail hx
    rcases hd3 with rfl | rfl <;> omega

/-- **The walk out from the middle misses nothing**: it is a permutation of the
rungs of the ladder. -/
theorem middleOut_perm_range (k : ℕ) : (middleOut k).Perm (List.range (2 * k + 1)) := by
  have hsub : middleOut k ⊆ List.range (2 * k + 1) := by
    intro x hx
    exact List.mem_range.2 (middleOut_lt k x hx)
  have hsubperm : (middleOut k).Subperm (List.range (2 * k + 1)) :=
    (middleOut_nodup k).subperm hsub
  refine (List.Subperm.perm_of_length_le hsubperm ?_)
  simp [middleOut_length]

/-! ## §3 Escalation along a walk -/

variable {R C : Type*}

/-- The answer an escalation returns: the first rung of the walk that names
something. -/
def firstNamed (name : R → Option C) (rungs : List R) : Option C :=
  rungs.findSome? name

theorem firstNamed_nil (name : R → Option C) : firstNamed name [] = none := rfl

theorem firstNamed_eq_none_iff (name : R → Option C) (rungs : List R) :
    firstNamed name rungs = none ↔ ∀ r ∈ rungs, name r = none := by
  simp [firstNamed]

theorem exists_of_firstNamed {name : R → Option C} :
    ∀ {rungs : List R} {c : C}, firstNamed name rungs = some c →
      ∃ r ∈ rungs, name r = some c := by
  intro rungs
  induction rungs with
  | nil => intro c h; simp [firstNamed] at h
  | cons r rs ih =>
      intro c h
      cases hn : name r with
      | none =>
          rw [firstNamed, List.findSome?_cons, hn] at h
          obtain ⟨r', hr', hname⟩ := ih h
          exact ⟨r', by simp [hr'], hname⟩
      | some c' =>
          rw [firstNamed, List.findSome?_cons, hn] at h
          exact ⟨r, by simp, by simpa using h ▸ hn⟩

theorem firstNamed_eq_some_iff {name : R → Option C} {rungs : List R} {c : C}
    (hagree : ∀ r ∈ rungs, ∀ c', name r = some c' → c' = c) :
    firstNamed name rungs = some c ↔ ∃ r ∈ rungs, (name r).isSome := by
  induction rungs with
  | nil => simp [firstNamed]
  | cons r rs ih =>
      have hr : ∀ c', name r = some c' → c' = c := hagree r (by simp)
      have hrest : ∀ r' ∈ rs, ∀ c', name r' = some c' → c' = c :=
        fun r' hr' => hagree r' (by simp [hr'])
      cases hn : name r with
      | none => simpa [firstNamed, List.findSome?_cons, hn] using ih hrest
      | some c' =>
          have : c' = c := hr c' hn
          subst this
          simp [firstNamed, hn]

/-- **Order independence.**  If every rung that names something names the same
thing, the escalation's answer does not depend on the order the rungs are
visited in — so the order may be chosen for cost alone. -/
theorem firstNamed_order_independent {name : R → Option C} {rs rs' : List R}
    (hperm : rs.Perm rs')
    (hagree : ∀ r ∈ rs, ∀ r' ∈ rs, ∀ c c', name r = some c → name r' = some c' → c = c') :
    firstNamed name rs = firstNamed name rs' := by
  cases h : firstNamed name rs with
  | none =>
      have hnone : ∀ r ∈ rs, name r = none :=
        (firstNamed_eq_none_iff name rs).1 h
      exact ((firstNamed_eq_none_iff name rs').2
        fun r hr => hnone r (hperm.mem_iff.2 hr)).symm
  | some c =>
      obtain ⟨r₀, hr₀, hname₀⟩ := exists_of_firstNamed h
      have hagree' : ∀ r ∈ rs', ∀ c', name r = some c' → c' = c := by
        intro r hr c' hc'
        exact (hagree r₀ hr₀ r (hperm.mem_iff.2 hr) c c' hname₀ hc').symm
      exact ((firstNamed_eq_some_iff hagree').2
        ⟨r₀, hperm.mem_iff.1 hr₀, by simp [hname₀]⟩).symm

/-- How many rungs a walk pays for: those it passes over, and the one it stops
at.  A walk that names nothing pays for all of them. -/
def visitCount (name : R → Option C) (rungs : List R) : ℕ :=
  match rungs.findIdx? (fun r => (name r).isSome) with
  | some i => i + 1
  | none => rungs.length

/-- **The cost of starting in the right place.**  A walk whose first rung names
something pays for exactly one rung. -/
theorem visitCount_eq_one_of_head_named {name : R → Option C} {r : R} {rs : List R}
    (h : (name r).isSome) : visitCount name (r :: rs) = 1 := by
  simp [visitCount, List.findIdx?_cons, h]

theorem visitCount_le_length {name : R → Option C} {rungs : List R} :
    visitCount name rungs ≤ rungs.length := by
  unfold visitCount
  cases h : rungs.findIdx? (fun r => (name r).isSome) with
  | none => simp
  | some i =>
      simp only
      have := List.findIdx?_eq_some_iff_findIdx_eq.mp h
      omega

end GLM.ConstructionLadder
