/-
# The search loop, taken from the archive's ARC generations

`source_material/GLM-main.zip/arc_agi_15` is the generation of the ARC work that
kept an honest ledger of its own methods (`METHODS_TRIED.md`), and the ledger's
three surviving rules are not numbers but a *procedure*:

* **D1, the hard gate.** A candidate program is admitted only if it reproduces
  every observed example exactly. The ledger calls it "the ONLY reliable
  filter" and "non-negotiable".
* **D2, the soft gate, never.** Accepting a candidate because a coherence score
  (there, `NRCI`) is high enough is recorded as "catastrophic — accepts wrong
  candidates".
* **C5, Occam.** Among the candidates the hard gate leaves, the one of least
  description cost is taken, because nothing in the data separates them.

This file is that procedure, stated once and proved, for an arbitrary finite
candidate set and an arbitrary stream of observations, and then *measured* on
the smallest concrete instance the archive's own solvers used: the eight
symmetries of the square acting on a `3 × 3` grid.

## What is proved

§1 is the loop. `survivors` is the hard gate; `gate_sound` is the statement
that it never discards the truth, `survivors_append` that filtering twice is
filtering once (so a loop and a batch agree), `survivors_antitone` and
`card_survivors_le` that it only ever shrinks, and `loop_stabilises` that a
descending loop reaches a fixed point in at most `#H` productive rounds.
`gate_blind` is why the ledger's C5 is forced: any two survivors agree on every
observation, so *no* function of the observed behaviour can separate them, and
a tie-break must come from outside the data. `occam_unique` says an injective
cost makes that choice well defined, and `score_gate_unsound` exhibits, in four
lines, the failure D2 records: a score whose maximiser is a candidate the gate
has already refuted.

§2 is what the gate leaves when the candidates are the elements of a group
acting on the data — the case of the archive's geometric operators.
`symSurvivors_eq_coset` and `card_symSurvivors` say the survivors of one
example `(g, s₀ • g)` are exactly the coset `s₀ · Stab g`, so the residual
ambiguity is the *stabiliser of the observed input* and nothing else.
`card_predictions_eq_orbit` turns that into the quantity a solver actually
cares about — how many different answers the survivors give on a fresh input —
and it is the orbit of that input under `Stab g`; `card_predictions_dvd_card_stab`
bounds it, and `predictions_card_eq_one_iff` says the answer is unique exactly
when every symmetry of the example is also a symmetry of the question.

§3 is the census, for the dihedral group of order 8 on `3 × 3` binary grids.
`d4_closed` checks the eight maps really are a group of permutations of the
512 grids; `stab_census` counts, over all 512 grids, how many candidates one
example leaves — `288` grids leave one, `200` leave two, `16` leave four and
`8` leave all eight — `stab_total` sums that to `816`, which is `8 · 102` and
so recovers the 102 orbits by Burnside; and `ambiguity_census` walks all
`512 · 512 = 262,144` (example, question) pairs and finds the answer determined
in `160,320` of them, two-valued in `91,776`, four-valued in `7,744` and
eight-valued in `2,304`, with `ambiguity_dvd_eight` confirming §2's divisibility
on every pair and `ambiguity_total` giving the exact mean `393280/262144 =
6145/4096`.

`glm_universal.reasoning.search_loop` recomputes every census here, and
`studies/SEARCH_LOOP_STUDY.md` is the write-up.
-/
import Mathlib

namespace GLM.SearchLoop

open Finset

/-! ## 1. The loop

A candidate is an index `h : ι`; what it *does* is `sem h : α → β`. An
observation is an input paired with the output that was seen. -/

section Generic

variable {ι α β : Type*} [DecidableEq β]

/-- A candidate is *consistent* with a list of observations when it reproduces
every one of them exactly. This is the archive's hard gate. -/
def Consistent (sem : ι → α → β) (obs : List (α × β)) (h : ι) : Prop :=
  ∀ p ∈ obs, sem h p.1 = p.2

instance (sem : ι → α → β) (obs : List (α × β)) (h : ι) :
    Decidable (Consistent sem obs h) := by
  unfold Consistent; infer_instance

/-- The survivors of the hard gate. -/
def survivors (sem : ι → α → β) (H : Finset ι) (obs : List (α × β)) : Finset ι :=
  H.filter (Consistent sem obs)

variable {sem : ι → α → β} {H : Finset ι} {obs o₁ o₂ : List (α × β)} {h truth : ι}

theorem mem_survivors :
    h ∈ survivors sem H obs ↔ h ∈ H ∧ Consistent sem obs h := mem_filter

theorem survivors_subset : survivors sem H obs ⊆ H := filter_subset _ _

/-- **The gate is sound.** Whatever produced the observations is never
discarded by the rule that keeps what reproduces them. -/
theorem gate_sound (ht : truth ∈ H) (hc : Consistent sem obs truth) :
    truth ∈ survivors sem H obs :=
  mem_survivors.2 ⟨ht, hc⟩

/-- In particular the truth survives its own observations: any list of
observations read off `sem truth` keeps `truth`. -/
theorem gate_sound_of_generated (ht : truth ∈ H) (inputs : List α) :
    truth ∈ survivors sem H (inputs.map fun a => (a, sem truth a)) := by
  refine gate_sound ht ?_
  intro p hp
  simp only [List.mem_map] at hp
  obtain ⟨a, _, rfl⟩ := hp
  rfl

/-- **Looping is batching.** Filtering by `o₁` and then by `o₂` is filtering by
both at once, so an incremental loop and a single pass agree exactly. -/
theorem survivors_append :
    survivors sem (survivors sem H o₁) o₂ = survivors sem H (o₁ ++ o₂) := by
  ext h
  simp only [survivors, mem_filter, Consistent, List.mem_append]
  constructor
  · rintro ⟨⟨hH, h₁⟩, h₂⟩
    exact ⟨hH, fun p hp => hp.elim (h₁ p) (h₂ p)⟩
  · rintro ⟨hH, hb⟩
    exact ⟨⟨hH, fun p hp => hb p (Or.inl hp)⟩, fun p hp => hb p (Or.inr hp)⟩

/-- More observations can only remove candidates. -/
theorem survivors_antitone (hsub : ∀ p ∈ o₁, p ∈ o₂) :
    survivors sem H o₂ ⊆ survivors sem H o₁ := by
  intro h hh
  rw [mem_survivors] at hh ⊢
  exact ⟨hh.1, fun p hp => hh.2 p (hsub p hp)⟩

theorem card_survivors_le : #(survivors sem H obs) ≤ #H :=
  card_le_card survivors_subset

/-- Filtering by the same observations twice changes nothing. -/
theorem survivors_idem :
    survivors sem (survivors sem H obs) obs = survivors sem H obs := by
  ext h; simp [survivors, mem_filter]

/-- **The gate is blind to its own residue.** Any two survivors agree on every
observed input, so no quantity computed from the observed behaviour can
separate them: a tie-break has to come from outside the data. This is why the
archive's coherence rankers never improved on the gate, and why its Occam rule
is the honest default. -/
theorem gate_blind (h₁ h₂ : ι) (hh₁ : h₁ ∈ survivors sem H obs)
    (hh₂ : h₂ ∈ survivors sem H obs) (p : α × β) (hp : p ∈ obs) :
    sem h₁ p.1 = sem h₂ p.1 := by
  rw [mem_survivors] at hh₁ hh₂
  rw [hh₁.2 p hp, hh₂.2 p hp]

/-- **A wrong survivor can always be removed by an observation.** If a
candidate does not compute the same function as the truth, there is an input on
which they differ, and observing the truth there refutes the candidate while
keeping the truth. -/
theorem separating_observation (hne : sem h ≠ sem truth) :
    ∃ a : α, h ∉ survivors sem H (obs ++ [(a, sem truth a)]) ∧
      (truth ∈ survivors sem H obs → truth ∈ survivors sem H (obs ++ [(a, sem truth a)])) := by
  obtain ⟨a, ha⟩ := Function.ne_iff.1 hne
  refine ⟨a, ?_, ?_⟩
  · intro hmem
    exact ha (mem_survivors.1 hmem |>.2 (a, sem truth a) (by simp))
  · intro hmem
    rw [mem_survivors] at hmem ⊢
    refine ⟨hmem.1, fun p hp => ?_⟩
    rcases List.mem_append.1 hp with hp | hp
    · exact hmem.2 p hp
    · simp only [List.mem_singleton] at hp; subst hp; rfl

/-- **Full information isolates the truth up to behaviour.** Observing every
input leaves exactly the candidates that compute the same function — never
fewer (soundness) and never more (separation). -/
theorem full_information [Fintype α] [DecidableEq α] (truth : ι) :
    survivors sem H ((univ : Finset α).toList.map fun a => (a, sem truth a))
      = H.filter fun h => ∀ a, sem h a = sem truth a := by
  ext h
  simp only [survivors, mem_filter, Consistent, List.mem_map, mem_toList,
    mem_univ, true_and]
  constructor
  · rintro ⟨hH, hc⟩
    exact ⟨hH, fun a => hc (a, sem truth a) ⟨a, rfl⟩⟩
  · rintro ⟨hH, hc⟩
    refine ⟨hH, ?_⟩
    rintro p ⟨a, rfl⟩
    exact hc a

/-- **The loop terminates.** A descending chain of candidate sets reaches a
fixed point after at most `#(S 0)` steps: each productive round removes at
least one candidate, and there are only finitely many to remove. -/
theorem loop_stabilises (S : ℕ → Finset ι) (hmono : ∀ n, S (n + 1) ⊆ S n) :
    ∃ n ≤ #(S 0), S (n + 1) = S n := by
  by_contra hcon
  push_neg at hcon
  have hle : ∀ n, #(S n) ≤ #(S 0) := by
    intro n
    induction n with
    | zero => exact le_rfl
    | succ j ihj => exact le_trans (card_le_card (hmono j)) ihj
  have key : ∀ n ≤ #(S 0) + 1, n ≤ #(S 0) - #(S n) := by
    intro n
    induction n with
    | zero => intro _; simp
    | succ k ih =>
      intro hk
      have hik := ih (Nat.le_of_succ_le hk)
      have hne : S (k + 1) ≠ S k := hcon k (by omega)
      have hss : S (k + 1) ⊂ S k := Finset.ssubset_iff_subset_ne.2 ⟨hmono k, hne⟩
      have hlt : #(S (k + 1)) < #(S k) := card_lt_card hss
      have := hle k
      omega
  have := key (#(S 0) + 1) le_rfl
  omega

/-- **Occam is well defined.** If the description cost is injective on the
survivors, there is exactly one cheapest survivor, so the loop's answer is
determined rather than chosen. -/
theorem occam_unique (S : Finset ι) (hS : S.Nonempty) (rank : ι → ℕ)
    (hinj : ∀ a ∈ S, ∀ b ∈ S, rank a = rank b → a = b) :
    ∃! h, h ∈ S ∧ ∀ k ∈ S, rank h ≤ rank k := by
  obtain ⟨m, hm, hmin⟩ := S.exists_min_image rank hS
  refine ⟨m, ⟨hm, hmin⟩, ?_⟩
  rintro y ⟨hy, hymin⟩
  exact hinj y hy m hm (le_antisymm (hymin m hm) (hmin y hy))

end Generic

/-! ### The soft gate, refuted by an example

Two candidates over one bit: `false` computes the identity, `true` computes
negation. One observation `(true, true)` is seen. The score prefers `true`,
which the observation has already refuted. -/

/-- The demonstration's two candidates, as functions `Bool → Bool`. -/
def demoSem : Bool → Bool → Bool := fun h a => xor h a

/-- Both candidates are available. -/
def demoH : Finset Bool := Finset.univ

/-- The one observation: on input `true` the true program returned `true`. -/
def demoObs : List (Bool × Bool) := [(true, true)]

/-- A score that happens to prefer the wrong candidate. -/
def demoScore : Bool → ℕ := fun h => if h then 1 else 0

/-- **The hard gate keeps the truth and refutes the other candidate**, while
**the score prefers the refuted one**. Ranking without gating is therefore
unsound, which is exactly what the archive's ledger records under D2. -/
theorem score_gate_unsound :
    false ∈ survivors demoSem demoH demoObs ∧
      true ∉ survivors demoSem demoH demoObs ∧
      demoScore false < demoScore true := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

/-! ## 2. What one example leaves, when the candidates are symmetries

The archive's geometric operators are a group acting on grids: rotate, flip,
and their composites. In that case the survivors of a single example are a
coset of the stabiliser of the input, and the ambiguity of the *answer* is an
orbit under that stabiliser. -/

section Symmetry

variable {G X : Type*} [Group G] [Fintype G] [DecidableEq G] [DecidableEq X]
  [MulAction G X]

/-- The stabiliser of a datum, as a `Finset` of candidates. -/
def stabF (G : Type*) [Group G] [Fintype G] [DecidableEq G] [MulAction G X]
    (g : X) : Finset G := univ.filter fun s => s • g = g

/-- The candidates consistent with the single example `(g, out)`. -/
def symSurvivors (G : Type*) [Group G] [Fintype G] [DecidableEq G] [MulAction G X]
    (g out : X) : Finset G := univ.filter fun s => s • g = out

theorem mem_symSurvivors {g out : X} {s : G} :
    s ∈ symSurvivors G g out ↔ s • g = out := by
  simp [symSurvivors]

/-- **The survivors of one example are a coset of the stabiliser.** -/
theorem symSurvivors_eq_coset (s₀ : G) (g : X) :
    symSurvivors G g (s₀ • g) = (stabF G g).image fun s => s₀ * s := by
  ext s
  simp only [mem_symSurvivors, mem_image, stabF, mem_filter, mem_univ, true_and]
  constructor
  · intro hs
    refine ⟨s₀⁻¹ * s, ?_, by group⟩
    rw [mul_smul, hs, inv_smul_smul]
  · rintro ⟨t, ht, rfl⟩
    rw [mul_smul, ht]

/-- **So exactly `|Stab g|` candidates survive**, whatever the example's
output was. -/
theorem card_symSurvivors (s₀ : G) (g : X) :
    #(symSurvivors G g (s₀ • g)) = #(stabF G g) := by
  rw [symSurvivors_eq_coset]
  exact card_image_of_injective _ (mul_right_injective s₀)

/-- The stabiliser finset counts the stabiliser subgroup. -/
theorem card_stabF (g : X) : #(stabF G g) = Nat.card (MulAction.stabilizer G g) := by
  classical
  rw [Nat.card_eq_fintype_card, Fintype.card_subtype]
  congr 1

/-- And its size divides the number of candidates (Lagrange). -/
theorem card_stabF_dvd (g : X) : #(stabF G g) ∣ Fintype.card G := by
  rw [card_stabF, ← Nat.card_eq_fintype_card]
  exact Subgroup.card_subgroup_dvd_card (MulAction.stabilizer G g)

/-- The distinct answers the survivors give on a fresh input `t`. -/
def predictions (G : Type*) [Group G] [Fintype G] [DecidableEq G] [MulAction G X]
    (g out t : X) : Finset X := (symSurvivors G g out).image fun s => s • t

/-- **The ambiguity of the answer is an orbit of the stabiliser.** Up to the
overall relabelling by `s₀`, the survivors predict exactly the orbit of the
question under the symmetries of the example. -/
theorem card_predictions_eq_orbit (s₀ : G) (g t : X) :
    #(predictions G g (s₀ • g) t) = #((stabF G g).image fun s => s • t) := by
  rw [predictions, symSurvivors_eq_coset, image_image]
  refine card_nbij (fun x => s₀⁻¹ • x) ?_ ?_ ?_
  · intro x hx
    simp only [coe_image, Set.mem_image, mem_coe, stabF, mem_filter, mem_univ,
      true_and, Function.comp_apply] at hx ⊢
    obtain ⟨s, hs, rfl⟩ := hx
    exact ⟨s, hs, by rw [mul_smul, inv_smul_smul]⟩
  · intro x _ y _ hxy
    simpa using congrArg (fun z => s₀ • z) hxy
  · intro y hy
    simp only [coe_image, Set.mem_image, mem_coe, stabF, mem_filter, mem_univ,
      true_and, Function.comp_apply] at hy ⊢
    obtain ⟨s, hs, rfl⟩ := hy
    exact ⟨s₀ • s • t, ⟨s, hs, by rw [mul_smul]⟩, by rw [inv_smul_smul]⟩

/-- **The answer is unique exactly when every symmetry of the example is a
symmetry of the question.** -/
theorem predictions_card_eq_one_iff (s₀ : G) (g t : X) :
    #(predictions G g (s₀ • g) t) = 1 ↔ ∀ s ∈ stabF G g, s • t = t := by
  rw [card_predictions_eq_orbit]
  constructor
  · intro hcard s hs
    have h1 : (1 : G) ∈ stabF G g := by simp [stabF]
    have hmem : s • t ∈ (stabF G g).image fun s => s • t := mem_image_of_mem _ hs
    have hmem1 : (1 : G) • t ∈ (stabF G g).image fun s => s • t := mem_image_of_mem _ h1
    have := card_eq_one.1 hcard
    obtain ⟨a, ha⟩ := this
    rw [ha, mem_singleton] at hmem hmem1
    rw [hmem, ← hmem1, one_smul]
  · intro hfix
    rw [card_eq_one]
    refine ⟨t, ?_⟩
    ext x
    simp only [mem_image, mem_singleton]
    constructor
    · rintro ⟨s, hs, rfl⟩; exact hfix s hs
    · rintro rfl
      exact ⟨1, by simp [stabF], one_smul _ _⟩

/-- **The number of distinct answers divides the number of survivors**, hence
divides the number of candidates: the ambiguity of a symmetry search is always
a divisor of the group's order. -/
theorem card_predictions_dvd_card_stab (s₀ : G) (g t : X) :
    #(predictions G g (s₀ • g) t) ∣ #(stabF G g) := by
  classical
  rw [card_predictions_eq_orbit]
  -- the fibres of `s ↦ s • t` on `stabF G g` are the cosets of `stabF G g ∩ stabF G t`
  have hfib : ∀ x ∈ (stabF G g).image (fun s => s • t),
      #((stabF G g).filter fun s => s • t = x) = #(stabF G g ∩ stabF G t) := by
    intro x hx
    simp only [mem_image, stabF, mem_filter, mem_univ, true_and] at hx
    obtain ⟨s₁, hs₁, rfl⟩ := hx
    refine card_nbij (fun s => s₁⁻¹ * s) ?_ ?_ ?_
    · intro s hs
      simp only [mem_coe, mem_filter, stabF, mem_univ, true_and, mem_inter] at hs ⊢
      refine ⟨?_, ?_⟩
      · rw [mul_smul, hs.1, ← hs₁, inv_smul_smul]
        exact hs₁.symm
      · rw [mul_smul, hs.2, inv_smul_smul]
    · intro a _ b _ hab
      simpa using congrArg (fun z => s₁ * z) hab
    · intro y hy
      simp only [mem_coe, mem_inter, stabF, mem_filter, mem_univ, true_and] at hy
      refine ⟨s₁ * y, ?_, by group⟩
      simp only [mem_coe, mem_filter, stabF, mem_univ, true_and]
      exact ⟨by rw [mul_smul, hy.1, hs₁], by rw [mul_smul, hy.2]⟩
  have hsum := card_eq_sum_card_fiberwise
    (f := fun s : G => s • t) (s := stabF G g)
    (t := (stabF G g).image fun s => s • t)
    (fun x hx => mem_coe.2 (mem_image_of_mem _ (mem_coe.1 hx)))
  rw [hsum, Finset.sum_congr rfl hfib, sum_const, smul_eq_mul]
  exact Dvd.intro _ rfl

end Symmetry

/-! ## 3. The census

The smallest instance the archive's own solvers ran on: the eight symmetries of
the square — the identity, three rotations, two mirrors and the two diagonal
reflections — acting on `3 × 3` binary grids. A grid is a number below `512`
whose bit `3i + j` is the cell `(i, j)`, and a symmetry is a table saying which
old cell each new cell reads. Everything below is a walk over all 512 grids, or
over all `512 · 512 = 262,144` pairs of (example, question). -/

section D4

/-- The `3 × 3` binary grids, as bitmasks. -/
def gridsN : List ℕ := List.range 512

/-- The eight symmetries of the square, as tables of source cells: entry `p` of
table `k` is the old cell that new cell `p` reads. -/
def d4Table : List (List ℕ) :=
  [[0, 1, 2, 3, 4, 5, 6, 7, 8],   -- identity
   [6, 3, 0, 7, 4, 1, 8, 5, 2],   -- rotate 90°
   [8, 7, 6, 5, 4, 3, 2, 1, 0],   -- rotate 180°
   [2, 5, 8, 1, 4, 7, 0, 3, 6],   -- rotate 270°
   [2, 1, 0, 5, 4, 3, 8, 7, 6],   -- mirror in the vertical axis
   [6, 7, 8, 3, 4, 5, 0, 1, 2],   -- mirror in the horizontal axis
   [0, 3, 6, 1, 4, 7, 2, 5, 8],   -- transpose
   [8, 5, 2, 7, 4, 1, 6, 3, 0]]   -- anti-transpose

/-- Symmetry `k` applied to grid `g`. -/
def act (k g : ℕ) : ℕ :=
  (((List.range 9).map fun p =>
    if g.testBit ((d4Table.getD k []).getD p 0) then 2 ^ p else 0).sum)

/-- The symmetries that fix a grid. -/
def stabList (g : ℕ) : List ℕ := (List.range 8).filter fun k => act k g == g

/-- How many of the eight candidates one example leaves. -/
def stabCard (g : ℕ) : ℕ := (stabList g).length

/-- The candidates consistent with the single example `(g, out)`. -/
def survivorsN (g out : ℕ) : List ℕ := (List.range 8).filter fun k => act k g == out

/-- How many different answers those candidates give on a fresh grid `t`. -/
def ambiguity (g t : ℕ) : ℕ := (((stabList g).map fun k => act k t)).dedup.length

/-- The eight tables really are a group of permutations of the grids: every
composite of two of them is a third. -/
theorem d4_closed :
    ((List.range 8).all fun a => (List.range 8).all fun b =>
      (List.range 8).any fun c => gridsN.all fun g => act a (act b g) == act c g) = true := by
  native_decide

/-- And they are eight *different* permutations, so the candidate set really has
eight members. -/
theorem d4_faithful :
    ((List.range 8).all fun a => (List.range 8).all fun b =>
      (a == b) || !(gridsN.all fun g => act a g == act b g)) = true := by
  native_decide

/-- The action stays inside the grids. -/
theorem act_lt : (gridsN.all fun g => (List.range 8).all fun k => act k g < 512) = true := by
  native_decide

/-- §2 on this instance: whatever the observed output, exactly `|Stab g|`
candidates survive one example. -/
theorem survivorsN_card_eq_stabCard :
    (gridsN.all fun g => (List.range 8).all fun k =>
      (survivorsN g (act k g)).length == stabCard g) = true := by
  native_decide

/-- **What one example leaves.** Over all 512 grids, `288` are fixed by the
identity alone, `200` by two symmetries, `16` by four and `8` by all eight. -/
theorem stab_census :
    [1, 2, 4, 8].map (fun m => gridsN.countP fun g => stabCard g == m)
      = [288, 200, 16, 8] := by
  native_decide

/-- The census accounts for every grid, and no grid has a stabiliser of any
other size. -/
theorem stab_census_total :
    ([1, 2, 4, 8].map (fun m => gridsN.countP fun g => stabCard g == m)).sum = 512 := by
  rw [stab_census]
  norm_num

/-- The total is `816`. -/
theorem stab_total : (gridsN.map stabCard).sum = 816 := by
  native_decide

/-- Which is `8 · 102`: by Burnside the 512 grids fall into **102** orbits, so
the mean number of survivors of one example is `816/512 = 51/32`. -/
theorem burnside_orbits : (gridsN.map stabCard).sum = 8 * 102 := by
  rw [stab_total]

/-- **How ambiguous the answer is.** Over all 262,144 (example, question)
pairs the survivors agree on the answer in `160,320` of them, split two ways in
`91,776`, four ways in `7,744` and eight ways in `2,304`. -/
theorem ambiguity_census :
    [1, 2, 4, 8].map
        (fun m => ((gridsN.map fun g => gridsN.countP fun t => ambiguity g t == m)).sum)
      = [160320, 91776, 7744, 2304] := by
  native_decide

/-- The census accounts for every pair. -/
theorem ambiguity_census_total :
    ([1, 2, 4, 8].map
      (fun m => ((gridsN.map fun g => gridsN.countP fun t => ambiguity g t == m)).sum)).sum
        = 262144 := by
  rw [ambiguity_census]
  norm_num

/-- The total ambiguity is `393,280`, so the mean number of distinct answers
after one example is `393280/262144 = 6145/4096`, just over one and a half. -/
theorem ambiguity_total :
    (gridsN.map fun g => (gridsN.map fun t => ambiguity g t).sum).sum = 393280 := by
  native_decide

/-- §2's divisibility, checked on every pair: the number of distinct answers
divides the number of survivors. -/
theorem ambiguity_dvd_stab :
    (gridsN.all fun g => gridsN.all fun t => stabCard g % ambiguity g t == 0) = true := by
  native_decide

/-- And §2's criterion for a determined answer, checked on every pair: the
answer is unique exactly when every symmetry of the example fixes the
question. -/
theorem ambiguity_eq_one_iff :
    (gridsN.all fun g => gridsN.all fun t =>
      (ambiguity g t == 1) == ((stabList g).all fun k => act k t == t)) = true := by
  native_decide

end D4

end GLM.SearchLoop
