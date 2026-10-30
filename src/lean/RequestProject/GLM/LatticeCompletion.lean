import RequestProject.GLM.ConfigurationReading
import RequestProject.GLM.DeepHoleFailure

/-!
# The lattice round: the configuration reading answers, every Niemeier type is
# apart, and Construction A fills a norm (Phase 123)

`studies/LATTICE_COMPLETION_STUDY.md` takes the three lattice items of the
To-Do list together.  This file is the formal half of all three.

## 1.  The configuration reading is a rung, and its answers are certified

`configReading` packages the L1 distance on configuration profiles as a
`GLM.DeepHoleLadder.Reading`, so every theorem the ladder and the failure
round proved about an abstract rung applies to `L₅` itself.  Two are the ones
the answering path uses:

* `config_answer_sound` — the **answer rule**: if a query profile is strictly
  closer to the reference of type `t` than half the distance from that
  reference to every other reference, then `t`'s reference is strictly the
  nearest.  This is `per_type_correct` with the radius set to the query's own
  distance, and it is the rule the classifier answers by;
* `config_absent` — `GLM.DeepHoleFailure.per_type_absent`, instantiated for
  the first time: under faithfulness of a type at radius `w`, a query profile
  further than `w` from that type's reference is certified not of that type.

## 2.  The 23 Niemeier types are pairwise apart in the uniform limit

`uniform_floor`: with every vertex's share equal, the configuration profiles
of any two distinct Niemeier types are at least `4/9` apart in L1.  The
profiles are computed here from the root-system labels alone (`affineKeys`,
the keys of the affine Dynkin diagrams), and the 253 pairs are checked by the
kernel.  With `separation_floor` this says the reading has a positive floor to
read every one of the 23 types with, not only the ten reference holes.

## 3.  Construction A has minimum norm `min 4 d`

`constructionA_normSq_ge`: a nonzero integer vector whose reduction mod 2 lies
in a binary code of minimum distance `d` has squared norm at least `min 4 d`.
The candidate rungs for the two empty norms of the power-of-two family are
Construction A over sums of short codes: the even-weight codes of length
4, 8 and 12 (`d = 2`, the lattices `D₄⁶`, `D₈³`, `D₁₂²`) and the repetition
and extended Hamming codes (`d = 4`, the lattices `√2 D₄⁶`, `√2 E₈³`), the
latter scaled by eight to norm 256 (`GLM.NormFamily.scaled_min_norm`).
-/

namespace GLM.LatticeCompletion

open GLM.DeepHoleLadder GLM.ConfigurationReading Finset

/-! ## 1.  The configuration reading as a rung -/

/-- The configuration reading `L₅` as a rung of the ladder: profiles on a
finite key set, compared in L1. -/
def configReading (β : Type*) [Fintype β] : Reading (β → ℚ) where
  dist := l1
  dist_self := fun x => by simp [l1]
  dist_comm := l1_comm
  dist_triangle := l1_triangle

/-- **The answer rule is sound.**  If the query profile `x` is closer to the
reference `p` of type `t` than half the distance from `p` to every other
reference, then `p` is strictly the nearest reference to `x`. -/
theorem config_answer_sound {β : Type*} [Fintype β] {L : Type*}
    {refs : List (L × (β → ℚ))} {t : L} {p x : β → ℚ}
    (hrule : ∀ f ∈ refs, f.1 ≠ t → 2 * l1 x p < l1 p f.2) :
    ∀ f ∈ refs, f.1 ≠ t → l1 x p < l1 x f.2 := by
  intro f hf hne
  exact GLM.DeepHoleFailure.per_type_correct (R := configReading β)
    (refs := refs) (t := t) (p := p) (x := x) (w := l1 x p)
    (fun g hg hgt => hrule g hg hgt) le_rfl hf hne

/-- **An absence, certified by the configuration reading.**  If every
profile of a type lies within `w` of the type's reference, a profile further
than `w` from that reference is not of the type.  This is
`GLM.DeepHoleFailure.per_type_absent` at the rung `L₅`. -/
theorem config_absent {β : Type*} [Fintype β] {IsType : (β → ℚ) → Prop}
    {p : β → ℚ} {w : ℚ} (hfaithful : ∀ y, IsType y → l1 y p ≤ w)
    {x : β → ℚ} (hfar : w < l1 x p) : ¬ IsType x :=
  GLM.DeepHoleFailure.per_type_absent (R := configReading β) hfaithful hfar

/-- The certified radius of a type is half its distance to the nearest other
reference: inside it the answer rule fires, and every type's radius is
positive exactly when its reference differs from every other. -/
theorem config_radius_pos {β : Type*} [Fintype β] {p q : β → ℚ}
    (hne : p ≠ q) : 0 < l1 p q / 2 := by
  have hpos : 0 < l1 p q := by
    by_contra h
    push_neg at h
    apply hne
    funext b
    have hb : |p b - q b| ≤ l1 p q :=
      Finset.single_le_sum (f := fun b => |p b - q b|)
        (fun b _ => abs_nonneg _) (Finset.mem_univ b)
    have : |p b - q b| = 0 := le_antisymm (le_trans hb h) (abs_nonneg _)
    linarith [abs_eq_zero.mp this]
  linarith

/-! ## 2.  The 23 Niemeier types in the uniform limit -/

/-- The three simply-laced families. -/
inductive Fam
  | A
  | D
  | E
  deriving DecidableEq

/-- The keys `(component size, degree with multiplicity)` of the affine
Dynkin diagram of one irreducible root system, with their counts.  `Ã_n` is
an `(n+1)`-cycle (`Ã_1` a double edge), `D̃_4` a star, `D̃_n` two forks joined
by a path, `Ẽ_n` a tree with three legs. -/
def affineKeys : Fam → ℕ → List ((ℕ × ℕ) × ℕ)
  | .A, r => [((r + 1, 2), r + 1)]
  | .D, r => if r = 4 then [((5, 1), 4), ((5, 4), 1)]
             else [((r + 1, 1), 4), ((r + 1, 2), r - 5), ((r + 1, 3), 2)]
  | .E, r => [((r + 1, 1), 3), ((r + 1, 2), r - 3), ((r + 1, 3), 1)]

/-- A root system: its components as `(family, rank, power)`. -/
abbrev Label := List (Fam × ℕ × ℕ)

/-- How many vertices of a deep hole of type `L` carry the key `k`. -/
def keyCount (L : Label) (k : ℕ × ℕ) : ℕ :=
  (L.map fun c => c.2.2 *
    ((affineKeys c.1 c.2.1).map fun e => if e.1 = k then e.2 else 0).sum).sum

/-- The number of vertices of a deep hole of type `L`: `24 + #components`. -/
def vertexCount (L : Label) : ℕ :=
  (L.map fun c => c.2.2 * (c.2.1 + 1)).sum

/-- Every key a vertex of type `L` can carry. -/
def keysOf (L : Label) : List (ℕ × ℕ) :=
  L.flatMap fun c => (affineKeys c.1 c.2.1).map Prod.fst

/-- The keys of either of two types, each once. -/
def keyUnion (a b : Label) : List (ℕ × ℕ) := (keysOf a ++ keysOf b).dedup

/-- The uniform-limit L1 distance, cleared of denominators:
`Σ_k |c_a(k) n_b - c_b(k) n_a|`, which is `n_a n_b` times the distance. -/
def crossNum (a b : Label) : ℤ :=
  ((keyUnion a b).map fun k =>
    |(keyCount a k : ℤ) * vertexCount b - (keyCount b k : ℤ) * vertexCount a|).sum

/-- The uniform-limit configuration profile of type `L` at key `k`. -/
def uniformShare (L : Label) (k : ℕ × ℕ) : ℚ := (keyCount L k : ℚ) / vertexCount L

/-- The uniform-limit L1 distance between two types, over their keys. -/
def uniformDist (a b : Label) : ℚ :=
  ((keyUnion a b).map fun k => |uniformShare a k - uniformShare b k|).sum

/-- The 23 Niemeier root systems, in the order of the package's
`configuration_reading.NIEMEIER_TYPES`. -/
def niemeier : List Label :=
  [ [(.D, 24, 1)], [(.D, 16, 1), (.E, 8, 1)], [(.E, 8, 3)], [(.A, 24, 1)],
    [(.D, 12, 2)], [(.A, 17, 1), (.E, 7, 1)], [(.D, 10, 1), (.E, 7, 2)],
    [(.A, 15, 1), (.D, 9, 1)], [(.D, 8, 3)], [(.A, 12, 2)],
    [(.A, 11, 1), (.D, 7, 1), (.E, 6, 1)], [(.E, 6, 4)],
    [(.A, 9, 2), (.D, 6, 1)], [(.D, 6, 4)], [(.A, 8, 3)],
    [(.A, 7, 2), (.D, 5, 2)], [(.A, 6, 4)], [(.A, 5, 4), (.D, 4, 1)],
    [(.D, 4, 6)], [(.A, 4, 6)], [(.A, 3, 8)], [(.A, 2, 12)], [(.A, 1, 24)] ]

theorem niemeier_length : niemeier.length = 23 := by decide

/-- Every Niemeier type has rank 24, so `24 + k` vertices. -/
theorem niemeier_rank :
    ∀ L ∈ niemeier, (L.map fun c => c.2.2 * c.2.1).sum = 24 := by decide

/-- The vertex counts are positive, so the uniform shares are defined. -/
theorem niemeier_vertexCount_pos : ∀ L ∈ niemeier, 0 < vertexCount L := by
  decide

/-- The 253 pairs (each in both orders), cleared of denominators:
`9 Σ|…| ≥ 4 n_a n_b`. -/
theorem uniform_floor_cross :
    ∀ a ∈ niemeier, ∀ b ∈ niemeier, a ≠ b →
      4 * ((vertexCount a : ℤ) * vertexCount b) ≤ 9 * crossNum a b := by
  decide +kernel

/-- The rational distance is the cleared one divided by `n_a n_b`. -/
theorem uniformDist_eq (a b : Label) (ha : 0 < vertexCount a)
    (hb : 0 < vertexCount b) :
    uniformDist a b = (crossNum a b : ℚ) / ((vertexCount a : ℚ) * vertexCount b) := by
  have ha' : (0 : ℚ) < vertexCount a := by exact_mod_cast ha
  have hb' : (0 : ℚ) < vertexCount b := by exact_mod_cast hb
  have hab : (0 : ℚ) < (vertexCount a : ℚ) * vertexCount b := mul_pos ha' hb'
  unfold uniformDist crossNum uniformShare
  rw [eq_div_iff hab.ne']
  generalize keyUnion a b = ks
  induction ks with
  | nil => simp
  | cons k ks ih =>
    simp only [List.map_cons, List.sum_cons, add_mul, ih]
    push_cast
    congr 1
    rw [← abs_of_pos hab, ← abs_mul]
    have hna : (vertexCount a : ℚ) ≠ 0 := ha'.ne'
    have hnb : (vertexCount b : ℚ) ≠ 0 := hb'.ne'
    exact congrArg _ (by field_simp)

/-- **Every pair of Niemeier types is at least `4/9` apart** under the
configuration reading with uniform shares.  The closest pair is
`E_8^3`/`D_8^3`; `D_24`/`A_24` is at `12/25` and `E_6^4`/`D_6^4` at `4/7`. -/
theorem uniform_floor :
    ∀ a ∈ niemeier, ∀ b ∈ niemeier, a ≠ b → (4 : ℚ) / 9 ≤ uniformDist a b := by
  intro a ha b hb hab
  have hx := niemeier_vertexCount_pos a ha
  have hy := niemeier_vertexCount_pos b hb
  have h := uniform_floor_cross a ha b hb hab
  rw [uniformDist_eq a b hx hy]
  have hx' : (0 : ℚ) < vertexCount a := by exact_mod_cast hx
  have hy' : (0 : ℚ) < vertexCount b := by exact_mod_cast hy
  rw [div_le_div_iff₀ (by norm_num) (mul_pos hx' hy')]
  have : ((4 * ((vertexCount a : ℤ) * vertexCount b) : ℤ) : ℚ) ≤
      ((9 * crossNum a b : ℤ) : ℚ) := by exact_mod_cast h
  push_cast at this
  linarith

/-! ## 3.  Construction A -/

/-- **Construction A has minimum norm `min 4 d`.**  A nonzero integer vector
whose reduction mod 2 is a codeword of a code of minimum distance `d` has
squared norm at least `min 4 d`: either the reduction is zero, so some
coordinate is a nonzero even integer, or the reduction has at least `d` odd
coordinates, each contributing at least one. -/
theorem constructionA_normSq_ge {n : ℕ} (C : Set (Fin n → ZMod 2)) (d : ℕ)
    (hC : ∀ c ∈ C, c ≠ 0 → d ≤ (univ.filter fun i => c i ≠ 0).card)
    (x : Fin n → ℤ) (hx : (fun i => (x i : ZMod 2)) ∈ C) (h0 : x ≠ 0) :
    (min 4 d : ℤ) ≤ ∑ i, x i ^ 2 := by
  have hsq : ∀ i, 0 ≤ x i ^ 2 := fun i => sq_nonneg _
  by_cases hz : (fun i => (x i : ZMod 2)) = 0
  · -- every coordinate is even, and some coordinate is a nonzero even integer
    obtain ⟨i, hi⟩ : ∃ i, x i ≠ 0 := by
      by_contra h
      push_neg at h
      exact h0 (funext h)
    have heven : (x i : ZMod 2) = 0 := congrFun hz i
    rw [ZMod.intCast_zmod_eq_zero_iff_dvd] at heven
    obtain ⟨m, hm⟩ := heven
    push_cast at hm
    have hm0 : m ≠ 0 := by rintro rfl; simp at hm; exact hi hm
    have h4 : 4 ≤ x i ^ 2 := by
      rw [hm]
      have : 1 ≤ m ^ 2 := by
        have := sq_pos_of_ne_zero hm0
        omega
      nlinarith
    calc (min 4 d : ℤ) ≤ 4 := min_le_left _ _
      _ ≤ x i ^ 2 := h4
      _ ≤ ∑ j, x j ^ 2 :=
        Finset.single_le_sum (f := fun j => x j ^ 2) (fun j _ => hsq j)
          (Finset.mem_univ i)
  · -- at least `d` coordinates are odd, each contributing at least one
    have hd := hC _ hx hz
    set S := univ.filter fun i => ((x i : ℤ) : ZMod 2) ≠ 0
    have hodd : ∀ i ∈ S, 1 ≤ x i ^ 2 := by
      intro i hi
      have hi' : ((x i : ℤ) : ZMod 2) ≠ 0 := (Finset.mem_filter.mp hi).2
      have hne : x i ≠ 0 := by rintro h; rw [h] at hi'; simp at hi'
      have := sq_pos_of_ne_zero hne
      omega
    calc (min 4 d : ℤ) ≤ (d : ℤ) := min_le_right _ _
      _ ≤ (S.card : ℤ) := by exact_mod_cast hd
      _ = ∑ i ∈ S, (1 : ℤ) := by simp
      _ ≤ ∑ i ∈ S, x i ^ 2 := Finset.sum_le_sum hodd
      _ ≤ ∑ i, x i ^ 2 :=
        Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ S)
          (fun i _ _ => hsq i)

end GLM.LatticeCompletion
