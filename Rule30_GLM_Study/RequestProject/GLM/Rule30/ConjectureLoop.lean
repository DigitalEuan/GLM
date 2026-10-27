module

public import RequestProject.GLM.Rule30.TuningByEar

/-!
# Round 26: the conjecture loop — proposing candidate lemmas, testing, narrowing, looping

The question of the round (the user's input): *can the GLM propose possible axioms or lemmas,
test them, and narrow and loop for some iterations, with analogy and junctions helping to propose
original construction steps?*

Round 25 (`TuningByEar.lean`) tuned candidate **laws for the data**.  This file tunes candidate
**statements**.  Almost every open target of this package (`HalfLineDies p`, `TuneExcessLog`,
`HalfLineLinear p a b`, …) has the same shape: it is the conjunction of infinitely many
finitely checkable instances.  So a candidate lemma is presented here by its *level test*
`τ : ℕ → Bool` (instance `n` passes or fails), and it **holds** when every level passes.

## What is proved (for every pool of candidates)

* **Testing.** `refuted_of_fail` — one failing level is a proof of the negation (pruning is
  sound); `SurvivesTo.of_holds` — a true candidate passes every finite test (the truth is never
  pruned); `holds_iff_survivesTo` — holding is surviving every level.
* **Looping.** `loop_prunes_false` — if the test levels of the rounds are unbounded, every false
  candidate that stays in the pool is eventually pruned; `loop_keeps_true` — no true candidate
  ever is.
* **Narrowing** a graded family `fam θ` (larger `θ` = weaker statement, e.g. a larger constant in
  a bound): the frontier `narrow N` (least parameter still standing after level `N`) only moves
  up (`narrow_mono`), never passes a true member (`narrow_le_of_holds`), stays bounded iff some
  member is true (`narrow_bounded_iff`), and then **settles exactly on the least true parameter**
  (`narrow_eventually_eq`).  This is the "tuning closer and closer" of Round 25, now for
  statements: it converges from below to the sharp truth, but (Round 25,
  `no_finite_confirmation`) no finite stage knows it has arrived.
* **Junctions.** Two candidates form a junction at level `N` when no test below `N` separates
  them (`Junction`).  This is the GLM's junction (carriers with the same coordinates, which no read
  separates): `survivesTo_of_junction` — junction members share their fate; `junction_split` — a
  true and a false candidate are separated by some finite read; `junction_forever_iff` — a
  junction persists at every level iff the two tests are identical.
* **Construction from a junction: the meet.** `meet τ τ'` (both tests pass) is a *new* candidate,
  stronger than both, that the data supports exactly as well: `meet_holds_iff`,
  `survivesTo_meet_of_junction`.  A meet of two surviving candidates is how the loop proposes a
  sharper statement without new data.
* **Analogy proposes, testing decides.** `analogy_transport_unsound`: a transport map between
  families can send a true statement to a false one, so an analogy is a source of candidates and
  never a proof.  The Rule 30 instances (period 1 → period 2; Rule 86 → Rule 30) are in
  `ConjectureLoopData.lean`.

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

namespace Conjecture

/-! ## Candidates and testing -/

/-- A candidate statement presented by its level test holds when every level passes. -/
def Holds (τ : ℕ → Bool) : Prop := ∀ n, τ n = true

/-- The candidate passes every test below level `N`. -/
def SurvivesTo (τ : ℕ → Bool) (N : ℕ) : Prop := ∀ n < N, τ n = true

/-- **Pruning is sound**: one failing level refutes the candidate. -/
theorem refuted_of_fail {τ : ℕ → Bool} {n : ℕ} (h : τ n = false) : ¬ Holds τ := fun hh => by
  rw [hh n] at h; exact Bool.noConfusion h

/-- **The truth is never pruned**. -/
theorem SurvivesTo.of_holds {τ : ℕ → Bool} (h : Holds τ) (N : ℕ) : SurvivesTo τ N :=
  fun n _ => h n

theorem SurvivesTo.mono {τ : ℕ → Bool} {N M : ℕ} (h : SurvivesTo τ N) (hM : M ≤ N) :
    SurvivesTo τ M := fun n hn => h n (by omega)

theorem holds_iff_survivesTo (τ : ℕ → Bool) : Holds τ ↔ ∀ N, SurvivesTo τ N :=
  ⟨fun h N => SurvivesTo.of_holds h N, fun h n => h (n + 1) n (by omega)⟩

/-- A false candidate fails some level. -/
theorem exists_fail_of_not_holds {τ : ℕ → Bool} (h : ¬ Holds τ) : ∃ n, τ n = false := by
  by_contra hne
  push_neg at hne
  exact h fun n => by simpa using hne n

/-! ## The loop over rounds -/

/-- **A loop with unbounded test levels prunes every false candidate.** If round `r` tests up to
level `lev r` and the levels are unbounded, a false candidate fails at some round. -/
theorem loop_prunes_false {τ : ℕ → Bool} (h : ¬ Holds τ) {lev : ℕ → ℕ}
    (hlev : ∀ B, ∃ r, B ≤ lev r) : ∃ r, ¬ SurvivesTo τ (lev r) := by
  obtain ⟨n, hn⟩ := exists_fail_of_not_holds h
  obtain ⟨r, hr⟩ := hlev (n + 1)
  exact ⟨r, fun hs => by rw [hs n (by omega)] at hn; exact Bool.noConfusion hn⟩

/-- Once pruned, pruned at every later (higher) level. -/
theorem pruned_later {τ : ℕ → Bool} {N M : ℕ} (h : ¬ SurvivesTo τ N) (hNM : N ≤ M) :
    ¬ SurvivesTo τ M := fun hs => h (hs.mono hNM)

/-- **A loop never prunes a true candidate.** -/
theorem loop_keeps_true {τ : ℕ → Bool} (h : Holds τ) (lev : ℕ → ℕ) (r : ℕ) :
    SurvivesTo τ (lev r) :=
  SurvivesTo.of_holds h _

/-! ## Narrowing a graded family -/

section Narrow

open Classical

/-- A graded family: larger parameters are weaker statements, level by level. -/
def Graded (fam : ℕ → ℕ → Bool) : Prop :=
  ∀ θ θ' n, θ ≤ θ' → fam θ n = true → fam θ' n = true

/-- Every single level can be met by some parameter. -/
def LevelwiseMet (fam : ℕ → ℕ → Bool) : Prop := ∀ n, ∃ θ, fam θ n = true

variable {fam : ℕ → ℕ → Bool}

theorem exists_survivor (hg : Graded fam) (hm : LevelwiseMet fam) (N : ℕ) :
    ∃ θ, SurvivesTo (fam θ) N := by
  induction N with
  | zero => exact ⟨0, fun n hn => absurd hn (Nat.not_lt_zero _)⟩
  | succ N ih =>
    obtain ⟨θ, hθ⟩ := ih
    obtain ⟨θ', hθ'⟩ := hm N
    refine ⟨max θ θ', fun n hn => ?_⟩
    rcases Nat.lt_succ_iff_lt_or_eq.1 hn with hn | rfl
    · exact hg θ _ n (le_max_left _ _) (hθ n hn)
    · exact hg θ' _ n (le_max_right _ _) hθ'

/-- **The frontier after level `N`**: the least parameter whose statement survives every test
below `N`. -/
noncomputable def narrow (hg : Graded fam) (hm : LevelwiseMet fam) (N : ℕ) : ℕ :=
  Nat.find (exists_survivor hg hm N)

variable (hg : Graded fam) (hm : LevelwiseMet fam)

theorem narrow_spec (N : ℕ) : SurvivesTo (fam (narrow hg hm N)) N :=
  Nat.find_spec (exists_survivor hg hm N)

theorem narrow_le {N θ : ℕ} (h : SurvivesTo (fam θ) N) : narrow hg hm N ≤ θ :=
  Nat.find_min' _ h

theorem survivesTo_of_narrow_le {N θ : ℕ} (h : narrow hg hm N ≤ θ) : SurvivesTo (fam θ) N :=
  fun n hn => hg _ _ n h (narrow_spec hg hm N n hn)

/-- **The frontier only moves up** as the loop tests more levels. -/
theorem narrow_mono : Monotone (narrow hg hm) := by
  intro N M hNM
  exact narrow_le hg hm ((narrow_spec hg hm M).mono hNM)

/-- **The frontier never passes a true member** of the family. -/
theorem narrow_le_of_holds {θ : ℕ} (h : Holds (fam θ)) (N : ℕ) : narrow hg hm N ≤ θ :=
  narrow_le hg hm (SurvivesTo.of_holds h N)

/-- **The frontier stays bounded iff some member of the family is true.** -/
theorem narrow_bounded_iff : (∃ B, ∀ N, narrow hg hm N ≤ B) ↔ ∃ θ, Holds (fam θ) := by
  constructor
  · rintro ⟨B, hB⟩
    exact ⟨B, (holds_iff_survivesTo _).2 fun N => survivesTo_of_narrow_le hg hm (hB N)⟩
  · rintro ⟨θ, hθ⟩
    exact ⟨θ, narrow_le_of_holds hg hm hθ⟩

/-- **The frontier settles exactly on the least true parameter.** If some member of the family
is true, then after finitely many levels the frontier equals the least `θ` with `Holds (fam θ)`,
and stays there. -/
theorem narrow_eventually_eq (hex : ∃ θ, Holds (fam θ)) :
    ∃ N₀, ∀ N, N₀ ≤ N → narrow hg hm N = Nat.find hex := by
  set θ₀ := Nat.find hex
  -- every smaller parameter is false, hence fails some level
  have hfail : ∀ θ < θ₀, ∃ n, fam θ n = false := fun θ hθ =>
    exists_fail_of_not_holds (Nat.find_min hex hθ)
  choose! f hf using hfail
  refine ⟨(Finset.range θ₀).sup (fun θ => f θ + 1), fun N hN => ?_⟩
  apply le_antisymm (narrow_le_of_holds hg hm (Nat.find_spec hex) N)
  by_contra hlt
  push_neg at hlt
  set θ := narrow hg hm N
  have hle : f θ + 1 ≤ N :=
    le_trans (Finset.le_sup (f := fun θ => f θ + 1) (Finset.mem_range.2 hlt)) hN
  have := narrow_spec hg hm N (f θ) (by omega)
  rw [hf θ hlt] at this
  exact Bool.noConfusion this

end Narrow

/-! ## Junctions -/

/-- Two candidates form a **junction at level `N`** when no test below `N` separates them. -/
def Junction (τ τ' : ℕ → Bool) (N : ℕ) : Prop := ∀ n < N, τ n = τ' n

theorem Junction.refl (τ : ℕ → Bool) (N : ℕ) : Junction τ τ N := fun _ _ => rfl

theorem Junction.symm {τ τ' : ℕ → Bool} {N : ℕ} (h : Junction τ τ' N) : Junction τ' τ N :=
  fun n hn => (h n hn).symm

theorem Junction.trans {τ τ' τ'' : ℕ → Bool} {N : ℕ} (h : Junction τ τ' N)
    (h' : Junction τ' τ'' N) : Junction τ τ'' N := fun n hn => (h n hn).trans (h' n hn)

theorem Junction.mono {τ τ' : ℕ → Bool} {N M : ℕ} (h : Junction τ τ' N) (hM : M ≤ N) :
    Junction τ τ' M := fun n hn => h n (by omega)

/-- **Junction members share their fate**: at the junction's level, no read separates them. -/
theorem survivesTo_of_junction {τ τ' : ℕ → Bool} {N : ℕ} (hj : Junction τ τ' N)
    (h : SurvivesTo τ N) : SurvivesTo τ' N := fun n hn => (hj n hn) ▸ h n hn

/-- **A finer read splits a junction of a true and a false candidate.** -/
theorem junction_split {τ τ' : ℕ → Bool} (h : Holds τ) (h' : ¬ Holds τ') :
    ∃ N, ¬ Junction τ τ' N := by
  obtain ⟨n, hn⟩ := exists_fail_of_not_holds h'
  refine ⟨n + 1, fun hj => ?_⟩
  have := hj n (by omega)
  rw [h n, hn] at this
  exact Bool.noConfusion this

/-- A junction persists at every level exactly when the two tests are identical. -/
theorem junction_forever_iff (τ τ' : ℕ → Bool) : (∀ N, Junction τ τ' N) ↔ τ = τ' :=
  ⟨fun h => funext fun n => h (n + 1) n (by omega), fun h N => h ▸ Junction.refl τ N⟩

/-! ## Construction from a junction: the meet -/

/-- **The meet** of two candidates: both pass. -/
def meet (τ τ' : ℕ → Bool) : ℕ → Bool := fun n => τ n && τ' n

theorem meet_holds_iff (τ τ' : ℕ → Bool) : Holds (meet τ τ') ↔ Holds τ ∧ Holds τ' := by
  simp only [Holds, meet, Bool.and_eq_true]
  exact ⟨fun h => ⟨fun n => (h n).1, fun n => (h n).2⟩, fun h n => ⟨h.1 n, h.2 n⟩⟩

theorem survivesTo_meet_iff (τ τ' : ℕ → Bool) (N : ℕ) :
    SurvivesTo (meet τ τ') N ↔ SurvivesTo τ N ∧ SurvivesTo τ' N := by
  simp only [SurvivesTo, meet, Bool.and_eq_true]
  exact ⟨fun h => ⟨fun n hn => (h n hn).1, fun n hn => (h n hn).2⟩,
    fun h n hn => ⟨h.1 n hn, h.2 n hn⟩⟩

/-- **The meet of a surviving junction survives**: a stronger statement with the same support. -/
theorem survivesTo_meet_of_junction {τ τ' : ℕ → Bool} {N : ℕ} (hj : Junction τ τ' N)
    (h : SurvivesTo τ N) : SurvivesTo (meet τ τ') N :=
  (survivesTo_meet_iff _ _ _).2 ⟨h, survivesTo_of_junction hj h⟩

/-- The meet implies each of its parts. -/
theorem holds_of_meet_left {τ τ' : ℕ → Bool} (h : Holds (meet τ τ')) : Holds τ :=
  ((meet_holds_iff _ _).1 h).1

theorem holds_of_meet_right {τ τ' : ℕ → Bool} (h : Holds (meet τ τ')) : Holds τ' :=
  ((meet_holds_iff _ _).1 h).2

/-! ## Analogy proposes, testing decides -/

/-- **Analogy is not a proof.** There is a transport map between candidate families (here the
shift of tests by one level, the simplest "same shape, other object" map) sending a true
statement to a false one.  The Rule 30 instances are in `ConjectureLoopData.lean`. -/
theorem analogy_transport_unsound :
    ∃ (A : (ℕ → Bool) → (ℕ → Bool)) (τ : ℕ → Bool), Holds τ ∧ ¬ Holds (A τ) :=
  ⟨fun τ n => τ n && decide (n ≠ 0), fun _ => true, fun _ => rfl,
    refuted_of_fail (n := 0) rfl⟩

/-- **What an analogy is good for**: if a transported candidate survives the loop and a proved
implication carries it to a target, the target is reduced to the candidate.  (Logically trivial;
recorded because it is the loop's success criterion: a *useful* survivor.) -/
theorem useful_survivor {τ : ℕ → Bool} {P : Prop} (himp : Holds τ → P) (h : Holds τ) : P :=
  himp h

end Conjecture

end GLM.Rule30
