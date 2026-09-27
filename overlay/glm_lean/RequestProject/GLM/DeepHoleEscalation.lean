/-
# The deep-hole ladder: when escalating the reading is allowed to help

`studies/DEEP_HOLE_ESCALATION_STUDY.md` asks whether the deep-hole round stopped
because of the geometry or because of the layer the geometry was read at, and it
escalates the reading along a declared ladder until a stated criterion holds.
The measurement is
`overlay/glm_universal/reasoning/deep_hole_escalation.py`.  What is *not* a
measurement is the ladder and its criterion, and that is here.

## 1.  A reading

A `Reading` is what a layer of the ladder is, formally: an exact rational
distance on carriers, symmetric, vanishing on the diagonal, and obeying the
triangle inequality.  Nothing else is assumed — in particular a reading may
conflate distinct carriers, which is the whole subject.

## 2.  The criterion, and why `ρ < 1` is the right thing to measure

`Resolves R refs w` says distinct references are more than `2w` apart under the
reading.  `nearest_correct` is the reason the study measures the ratio
`ρ = 2W / B`: under the criterion, a carrier within `w` of its own reference is
strictly nearer to that reference than to any other, so the nearest-reference
rule names it correctly.  `resolves_of_ratio_lt_one` states the same thing in
the ratio the tables report.

## 3.  Escalation is not guaranteed to help

`cumulative` is the widened reading: carry the layer below alongside the new
one and add the distances.  It **refines** its parts, in the sense that it
separates whatever they separate (`cumulative_ge_left`, `indist_cumulative_iff`)
— and `cumulative_can_break_criterion` exhibits a pair of readings and a table
where the narrow reading satisfies the criterion and the widened one does not.
So a wider view can only see more, and can still be worse for *this* question,
because widening moves the within-class spread as well as the separation.  The
ladder is therefore an experiment and not a theorem, which is exactly what the
pre-registration claims for it.

## 4.  The ladder itself

`firstResolving` walks the rungs in the declared order and returns the least one
whose criterion holds, or `none`.  `firstResolving_holds` (the answer resolves),
`firstResolving_least` (nothing earlier does) and `firstResolving_eq_none_iff`
(a refusal is a statement about *every* rung) are the three facts an escalation
step needs in order to be an inference rather than a retry: a refusal at the top
of the ladder is a proof about the whole ladder, while a refusal at the bottom
is only a lack of resolution.
-/
import Mathlib

namespace GLM.DeepHoleLadder

universe u v

/-! ## 1.  A reading -/

/-- A reading of a carrier space: an exact rational distance.  One rung of the
ladder is one of these. -/
structure Reading (C : Type u) where
  /-- The exact distance the rung compares carriers with. -/
  dist : C → C → ℚ
  dist_self : ∀ c, dist c c = 0
  dist_comm : ∀ a b, dist a b = dist b a
  dist_triangle : ∀ a b c, dist a c ≤ dist a b + dist b c

namespace Reading

variable {C : Type u} (R : Reading C)

theorem dist_nonneg (a b : C) : 0 ≤ R.dist a b := by
  have h := R.dist_triangle a b a
  rw [R.dist_self, R.dist_comm b a] at h
  linarith

/-- Two carriers a rung cannot tell apart. -/
def Indist (a b : C) : Prop := R.dist a b = 0

@[refl] theorem indist_refl (a : C) : R.Indist a a := R.dist_self a

theorem indist_symm {a b : C} (h : R.Indist a b) : R.Indist b a := by
  rw [Indist, R.dist_comm]; exact h

/-- The reading built from a rational coordinate: `|f a - f b|`. -/
def ofMap {C : Type u} (f : C → ℚ) : Reading C where
  dist a b := |f a - f b|
  dist_self := by intro c; simp
  dist_comm := by intro a b; exact abs_sub_comm _ _
  dist_triangle := by
    intro a b c
    calc |f a - f c| = |(f a - f b) + (f b - f c)| := by ring_nf
      _ ≤ |f a - f b| + |f b - f c| := abs_add_le _ _

@[simp] theorem ofMap_dist {C : Type u} (f : C → ℚ) (a b : C) :
    (ofMap f).dist a b = |f a - f b| := rfl

/-- The widened reading: carry the rung below alongside the new one. -/
def cumulative (R S : Reading C) : Reading C where
  dist a b := R.dist a b + S.dist a b
  dist_self := by intro c; simp [R.dist_self, S.dist_self]
  dist_comm := by intro a b; rw [R.dist_comm, S.dist_comm]
  dist_triangle := by
    intro a b c
    have hR := R.dist_triangle a b c
    have hS := S.dist_triangle a b c
    linarith

@[simp] theorem cumulative_dist (R S : Reading C) (a b : C) :
    (cumulative R S).dist a b = R.dist a b + S.dist a b := rfl

/-- Widening never shrinks a distance: the wide reading sees what the narrow
one saw. -/
theorem cumulative_ge_left (R S : Reading C) (a b : C) :
    R.dist a b ≤ (cumulative R S).dist a b := by
  have := S.dist_nonneg a b
  simp only [cumulative_dist]
  linarith

theorem cumulative_ge_right (R S : Reading C) (a b : C) :
    S.dist a b ≤ (cumulative R S).dist a b := by
  have := R.dist_nonneg a b
  simp only [cumulative_dist]
  linarith

/-- The widened reading conflates exactly what *both* of its parts conflate. -/
theorem indist_cumulative_iff (R S : Reading C) {a b : C} :
    (cumulative R S).Indist a b ↔ R.Indist a b ∧ S.Indist a b := by
  have hR := R.dist_nonneg a b
  have hS := S.dist_nonneg a b
  constructor
  · intro h
    simp only [Indist, cumulative_dist] at h
    constructor <;> simp only [Indist] <;> linarith
  · rintro ⟨h1, h2⟩
    simp only [Indist, cumulative_dist]
    simp only [Indist] at h1 h2
    rw [h1, h2, add_zero]

end Reading

/-! ## 2.  The criterion -/

variable {C : Type u} {L : Type v}

/-- The separation criterion at spread `w`: distinct references are more than
`2w` apart.  This is `ρ = 2W/B < 1` in the study's notation. -/
def Resolves (R : Reading C) (refs : List (L × C)) (w : ℚ) : Prop :=
  ∀ e ∈ refs, ∀ f ∈ refs, e.1 ≠ f.1 → 2 * w < R.dist e.2 f.2

/-- **The criterion is sufficient.**  A carrier within `w` of its own
reference is strictly nearer to that reference than to any other, so the
nearest-reference rule names it correctly. -/
theorem nearest_correct {R : Reading C} {refs : List (L × C)} {w : ℚ}
    (hres : Resolves R refs w) {t : L} {p x : C}
    (hmem : (t, p) ∈ refs) (hx : R.dist x p ≤ w)
    {u : L} {q : C} (hq : (u, q) ∈ refs) (hne : u ≠ t) :
    R.dist x p < R.dist x q := by
  have hsep : 2 * w < R.dist q p := hres (u, q) hq (t, p) hmem hne
  have htri : R.dist q p ≤ R.dist q x + R.dist x p := R.dist_triangle q x p
  have hqx : R.dist q x = R.dist x q := R.dist_comm q x
  have hxq : 0 ≤ R.dist x q := R.dist_nonneg x q
  linarith [hsep, htri, hqx, hx, hxq]

/-- The same statement in the ratio the study's tables report: if the worst
within-class spread is `W`, the reference separation is at least `B`, and
`2W < B`, the criterion holds. -/
theorem resolves_of_ratio_lt_one {R : Reading C} {refs : List (L × C)}
    {W B : ℚ} (hB : ∀ e ∈ refs, ∀ f ∈ refs, e.1 ≠ f.1 → B ≤ R.dist e.2 f.2)
    (hlt : 2 * W < B) : Resolves R refs W := by
  intro e he f hf hne
  exact lt_of_lt_of_le hlt (hB e he f hf hne)

/-- **The criterion is a congruence statement.**  If a reading cannot tell two
carriers apart at all — the same distance to everything — the nearest-reference
verdict is the same for both, so the label descends to the layer. -/
theorem label_descends {R : Reading C} {refs : List (L × C)} {x y : C}
    (hxy : ∀ e ∈ refs, R.dist x e.2 = R.dist y e.2)
    {t : L} {p : C} (hmem : (t, p) ∈ refs)
    (hnear : ∀ e ∈ refs, R.dist x p ≤ R.dist x e.2) :
    ∀ e ∈ refs, R.dist y p ≤ R.dist y e.2 := by
  intro e he
  rw [← hxy (t, p) hmem, ← hxy e he]
  exact hnear e he

/-! ## 3.  Escalation refines, and may still make this question harder -/

/-- The three carriers of the witness: a query, and two references. -/
inductive Witness
  | query
  | left
  | right
  deriving DecidableEq, Repr

/-- The narrow rung: it separates the two references and puts the query close
to the left one. -/
def narrowMap : Witness → ℚ
  | .query => 1 / 4
  | .left => 0
  | .right => 1

/-- The rung that is added on escalation: it says nothing about the references
and a great deal about the query.  This is what "the strays" are in the
study — real information about the carrier that the narrow rung discarded. -/
def wideMap : Witness → ℚ
  | .query => 1
  | .left => 0
  | .right => 0

/-- The narrow reading. -/
def narrow : Reading Witness := Reading.ofMap narrowMap

/-- The widened reading: the narrow one carried alongside the new rung. -/
def widened : Reading Witness := Reading.cumulative narrow (Reading.ofMap wideMap)

/-- The two-reference table of the witness. -/
def witnessRefs : List (Bool × Witness) := [(false, .left), (true, .right)]

/-- **Refinement is not improvement.**  The widened reading separates
everything the narrow one separated, and yet the criterion that holds at the
spread the narrow reading needs fails at the spread the widened reading needs.
So escalating the view is an experiment, never a guarantee. -/
theorem cumulative_can_break_criterion :
    (∀ a b : Witness, narrow.dist a b ≤ widened.dist a b)
      ∧ Resolves narrow witnessRefs (1 / 4)
      ∧ narrow.dist .query .left ≤ 1 / 4
      ∧ widened.dist .query .left = 5 / 4
      ∧ ¬ Resolves widened witnessRefs (5 / 4) := by
  refine ⟨fun a b => Reading.cumulative_ge_left _ _ a b, ?_, ?_, ?_, ?_⟩
  · intro e he f hf hne
    fin_cases he <;> fin_cases hf <;> simp_all [narrow, narrowMap] <;> norm_num
  · norm_num [narrow, narrowMap]
  · norm_num [widened, narrow, narrowMap, wideMap]
  · intro h
    have := h (false, .left) (by simp [witnessRefs]) (true, .right)
      (by simp [witnessRefs]) (by simp)
    norm_num [widened, narrow, narrowMap, wideMap] at this

/-! ## 4.  The ladder -/

/-- Walk the rungs in the declared order and return the least one whose
criterion holds.  `none` is a refusal, and it is a statement about every rung. -/
def firstResolving : ℕ → (ℕ → Bool) → Option ℕ
  | 0, _ => none
  | n + 1, P =>
      match firstResolving n P with
      | some i => some i
      | none => if P n then some n else none

@[simp] theorem firstResolving_zero (P : ℕ → Bool) : firstResolving 0 P = none := rfl

/-- The rung the ladder returns really does resolve. -/
theorem firstResolving_holds : ∀ (n : ℕ) (P : ℕ → Bool) (i : ℕ),
    firstResolving n P = some i → P i = true := by
  intro n
  induction n with
  | zero => intro P i h; simp [firstResolving] at h
  | succ n ih =>
      intro P i h
      simp only [firstResolving] at h
      cases hn : firstResolving n P with
      | some j =>
          rw [hn] at h
          simp only [Option.some.injEq] at h
          subst h
          exact ih P j hn
      | none =>
          rw [hn] at h
          by_cases hP : P n
          · simp only [hP, if_true, Option.some.injEq] at h
            subst h; exact hP
          · simp [hP] at h

/-- The rung the ladder returns is inside the ladder. -/
theorem firstResolving_lt : ∀ (n : ℕ) (P : ℕ → Bool) (i : ℕ),
    firstResolving n P = some i → i < n := by
  intro n
  induction n with
  | zero => intro P i h; simp [firstResolving] at h
  | succ n ih =>
      intro P i h
      simp only [firstResolving] at h
      cases hn : firstResolving n P with
      | some j =>
          rw [hn] at h
          simp only [Option.some.injEq] at h
          subst h
          exact Nat.lt_succ_of_lt (ih P j (by simpa using hn))
      | none =>
          rw [hn] at h
          by_cases hP : P n
          · simp only [hP, if_true, Option.some.injEq] at h
            subst h; exact Nat.lt_succ_self n
          · simp [hP] at h

/-- A refusal is a statement about every rung of the ladder. -/
theorem firstResolving_eq_none_iff : ∀ (n : ℕ) (P : ℕ → Bool),
    firstResolving n P = none ↔ ∀ i < n, P i = false := by
  intro n
  induction n with
  | zero => intro P; simp [firstResolving]
  | succ n ih =>
      intro P
      simp only [firstResolving]
      cases hn : firstResolving n P with
      | some j =>
          have hj : P j = true := firstResolving_holds n P j hn
          have hlt : j < n := firstResolving_lt n P j hn
          constructor
          · intro h; simp at h
          · intro h
            have := h j (Nat.lt_succ_of_lt hlt)
            rw [hj] at this
            exact absurd this (by simp)
      | none =>
          have hprev := (ih P).1 hn
          by_cases hP : P n
          · simp only [hP, if_true]
            constructor
            · intro h; simp at h
            · intro h
              have := h n (Nat.lt_succ_self n)
              rw [hP] at this
              exact absurd this (by simp)
          · simp only [hP, Bool.false_eq_true, if_false]
            constructor
            · intro _ i hi
              rcases Nat.lt_succ_iff_lt_or_eq.1 hi with hlt | rfl
              · exact hprev i hlt
              · simpa using hP
            · intro _; trivial

/-- Nothing earlier than the returned rung resolves: the ladder is minimal, so
the answer names the cheapest resolution and not merely a resolution. -/
theorem firstResolving_least : ∀ (n : ℕ) (P : ℕ → Bool) (i : ℕ),
    firstResolving n P = some i → ∀ j < i, P j = false := by
  intro n
  induction n with
  | zero => intro P i h; simp [firstResolving] at h
  | succ n ih =>
      intro P i h
      simp only [firstResolving] at h
      cases hn : firstResolving n P with
      | some k =>
          rw [hn] at h
          simp only [Option.some.injEq] at h
          subst h
          exact ih P k (by simpa using hn)
      | none =>
          rw [hn] at h
          by_cases hP : P n
          · simp only [hP, if_true, Option.some.injEq] at h
            subst h
            exact (firstResolving_eq_none_iff n P).1 hn
          · simp [hP] at h

end GLM.DeepHoleLadder
