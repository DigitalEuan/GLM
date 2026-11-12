module

public import Mathlib
public import RequestProject.GLM.Escalation.LayerStack

/-!
# Round 43: the unified master step, graded escalation and complete decoding

This file checks the structural claims of §§2, 4, 5.2 and 6 of
`GLM_Escalation_Boundaries_Exploration.md`.

**The master step (§2.1, §6).** The state is a pair (carrier, layer). One tick modulates the
carrier, snaps it (the snap returns a carrier *and* a layer), and commits the gated result only
if the three-column check (TCT) accepts; otherwise the state is returned unchanged.

* `step_of_reject`, `iterate_of_reject` : with a fixed modulation target, **a rejected state is
  rejected forever** — "TCT failure rolls back" means the run is stuck at that state for good.
  The roll-back semantics is a deadlock unless something outside the step (a new target, a
  perturbation, an escalation) changes the input. This settles the open "TCT semantics"
  question of §8.2 in one direction: roll-back alone cannot be the whole semantics.
* `layer_preserved_of_snap` : if the snap never changes the layer, no tick does. The snap is
  the only place a layer can change (§2.3), as claimed.
* `layer_of_input` : if the snap ignores the incoming layer (§6, "the layer is a property of
  the input"), then two accepted ticks from the same carrier land on the same layer.
* `layer_monotone`, `layer_eventually_const` : **the arrow.** If the snap only ever escalates
  (never lowers the layer), the layer index along any run is non-decreasing and, in a finite
  stack, eventually constant. This is the precise sense in which the layer can serve as the
  "direction" of a run (the Observer's read position): it orders the run and says where it
  settles. If the snap may also de-escalate, neither conclusion holds in general.

**Graded escalation (§4).** `escalate` returns the least layer at or above the current one at
which the operation is congruent.

* `escalate_spec`, `escalate_eq_none_iff` : it is correct and minimal, and it fails exactly when
  no layer at or above the start resolves.
* `escalate_isSome_of_top` : if the top layer resolves (for instance because it is lossless,
  `View.congruent_of_injective`), graded escalation always succeeds.
* `five_floor_filters_fail` : on the exploration's own half-unit example, none of the five
  floor-residue filters (mod 2, 4, 8, 144, 256) resolves; so its theorem
  `graded_escalation_correct` (every failure escalates to a resolving layer above) is false on
  its own stack. In the GLM's shipped stack the top three layers see the exact carrier, which is
  what makes escalation terminate (`escalate_isSome_of_top`).

**Complete decoding (§5.2).** A complete (syndrome) decoder picks, in each coset of the lattice,
a fixed leader. The exploration says a fixed table gives "no instability".

* `no_continuous_leader` : **no choice of leaders is continuous.** Along any lattice direction
  `v` that some integer-valued linear functional `φ` reads as `1`, the leader must jump. (For the
  Leech lattice, which is unimodular, take `φ = ⟪·, w⟫` with `w` a lattice vector and
  `⟪v, w⟫ = 1`.) A fixed table makes the decoder *deterministic*, not *stable*: points on
  either side of a cell wall still decode to different lattice points, at every wall, not only
  at the deep holes (which are cell vertices).
-/

@[expose] public section

namespace GLM.Escalation

/-! ## The master step -/

/-- The ingredients of one tick: a modulator (with its target fixed), a snap that returns a
carrier and a layer, a gate, and a Boolean three-column check. -/
structure Machine (C K : Type*) where
  modulate : C → C
  snap : C → K → C × K
  gate : C → C
  tct : C → C → C → Bool

namespace Machine

variable {C K : Type*} (M : Machine C K)

/-- One tick of the unified master equation (§6). -/
def step (s : C × K) : C × K :=
  let ψh := M.modulate s.1
  let p := M.snap ψh s.2
  if M.tct s.1 ψh p.1 then (M.gate p.1, p.2) else s

/-- The tick is accepted at `s`. -/
def accepts (s : C × K) : Bool := M.tct s.1 (M.modulate s.1) (M.snap (M.modulate s.1) s.2).1

theorem step_of_reject {s : C × K} (h : M.accepts s = false) : M.step s = s := by
  simp only [accepts] at h
  simp [step, h]

/-- **A rejected state is a fixed point forever.** -/
theorem iterate_of_reject {s : C × K} (h : M.accepts s = false) (n : ℕ) :
    M.step^[n] s = s :=
  Function.iterate_fixed (M.step_of_reject h) n

theorem step_of_accept {s : C × K} (h : M.accepts s = true) :
    M.step s = (M.gate (M.snap (M.modulate s.1) s.2).1, (M.snap (M.modulate s.1) s.2).2) := by
  simp only [accepts] at h
  simp [step, h]

/-- **The snap is the only place the layer can change.** -/
theorem layer_preserved_of_snap (h : ∀ c k, (M.snap c k).2 = k) (s : C × K) :
    (M.step s).2 = s.2 := by
  simp only [step]
  split_ifs <;> simp [h]

theorem layer_preserved_iterate (h : ∀ c k, (M.snap c k).2 = k) (s : C × K) (n : ℕ) :
    (M.step^[n] s).2 = s.2 := by
  induction n generalizing s with
  | zero => rfl
  | succ n ih => rw [Function.iterate_succ_apply, ih, M.layer_preserved_of_snap h]

/-- **When the snap ignores the incoming layer, the layer is a property of the input.** -/
theorem layer_of_input (h : ∀ c k k', M.snap c k = M.snap c k') (c : C) (k k' : K)
    (hk : M.accepts (c, k) = true) (hk' : M.accepts (c, k') = true) :
    (M.step (c, k)).2 = (M.step (c, k')).2 := by
  rw [M.step_of_accept hk, M.step_of_accept hk', h (M.modulate c) k k']

/-- **The arrow of escalation.** If the snap never lowers the layer (escalation only), then along
any run the layer never decreases, and in a finite stack it is eventually constant: the run has
a direction, and it settles on a layer. -/
theorem layer_monotone {n : ℕ} (M : Machine C (Fin (n + 1)))
    (h : ∀ c k, k ≤ (M.snap c k).2) (s : C × Fin (n + 1)) :
    Monotone (fun t => (M.step^[t] s).2) := by
  apply monotone_nat_of_le_succ
  intro t
  simp only [Function.iterate_succ_apply']
  set u := M.step^[t] s
  simp only [step]
  split_ifs
  · exact h _ _
  · exact le_rfl

theorem layer_eventually_const {n : ℕ} (M : Machine C (Fin (n + 1)))
    (h : ∀ c k, k ≤ (M.snap c k).2) (s : C × Fin (n + 1)) :
    ∃ T, ∀ t ≥ T, (M.step^[t] s).2 = (M.step^[T] s).2 := by
  have hm := M.layer_monotone h s
  set f : ℕ → ℕ := fun t => ((M.step^[t] s).2 : ℕ) with hf
  have hfm : Monotone f := fun a b hab => hm hab
  have hbd : ∀ t, f t ≤ n := fun t => Nat.lt_succ_iff.1 (M.step^[t] s).2.isLt
  obtain ⟨T, hT⟩ : ∃ T, ∀ t, f t ≤ f T := by
    by_contra hne
    push_neg at hne
    have : ∀ k, ∃ t, k ≤ f t := by
      intro k
      induction k with
      | zero => exact ⟨0, Nat.zero_le _⟩
      | succ k ih =>
        obtain ⟨t, ht⟩ := ih
        obtain ⟨t', ht'⟩ := hne t
        exact ⟨t', by omega⟩
    obtain ⟨t, ht⟩ := this (n + 1)
    have := hbd t
    omega
  refine ⟨T, fun t ht => ?_⟩
  apply Fin.ext
  exact le_antisymm (hT t) (hfm ht)

end Machine

/-! ## Graded escalation on a finite chain -/

/-- The least layer `j ≥ k` of a chain of `n + 1` layers at which `cong` holds. -/
def escalate {n : ℕ} (cong : Fin (n + 1) → Prop) [DecidablePred cong] (k : Fin (n + 1)) :
    Option (Fin (n + 1)) :=
  (List.finRange (n + 1)).find? (fun j => decide (k ≤ j ∧ cong j))

variable {n : ℕ} {cong : Fin (n + 1) → Prop} [DecidablePred cong]

theorem escalate_eq_none_iff (k : Fin (n + 1)) :
    escalate cong k = none ↔ ∀ j, k ≤ j → ¬ cong j := by
  simp [escalate, List.find?_eq_none]

/-- **Graded escalation is correct and minimal.** -/
theorem escalate_spec {k j : Fin (n + 1)} (h : escalate cong k = some j) :
    k ≤ j ∧ cong j ∧ ∀ i, k ≤ i → i < j → ¬ cong i := by
  unfold escalate at h
  rw [List.find?_eq_some_iff_append] at h
  obtain ⟨hj, as, bs, hsplit, hbefore⟩ := h
  simp only [decide_eq_true_eq] at hj
  refine ⟨hj.1, hj.2, fun i hki hij hci => ?_⟩
  have hi : i ∈ as := by
    have hmem : i ∈ List.finRange (n + 1) := List.mem_finRange i
    rw [hsplit] at hmem
    rcases List.mem_append.1 hmem with h | h
    · exact h
    · exfalso
      rcases List.mem_cons.1 h with h | h
      · exact absurd hij (by rw [h]; exact lt_irrefl _)
      · -- elements after `j` in `finRange` are larger than `j`
        have hsorted : (List.finRange (n + 1)).Pairwise (· < ·) := List.pairwise_lt_finRange _
        rw [hsplit, List.pairwise_append] at hsorted
        have := (List.pairwise_cons.1 hsorted.2.1).1 i h
        exact absurd hij (not_lt.2 this.le)
  have := hbefore i hi
  simp only [Bool.not_eq_true', decide_eq_false_iff_not] at this
  exact this ⟨hki, hci⟩

/-- **If the top layer resolves, graded escalation always succeeds.** -/
theorem escalate_isSome_of_top (htop : cong (Fin.last n)) (k : Fin (n + 1)) :
    (escalate cong k).isSome := by
  rcases h : escalate cong k with _ | j
  · exact absurd htop ((escalate_eq_none_iff k).1 h _ (Fin.le_last k))
  · rfl

/-- **On the exploration's own example, none of its five filters resolves.** For each modulus
`m ∈ {2, 4, 8, 144, 256}`, addition is not congruent for `⌊q⌋ mod m` on `{0, 1/2}`. -/
theorem five_floor_filters_fail :
    ∀ m ∈ ([2, 4, 8, 144, 256] : List ℕ),
      ¬ (floorResidue m).Congruent {0, 1/2} (· + ·) := by
  intro m hm
  apply floorResidue_add_not_congruent
  simp only [List.mem_cons, List.not_mem_nil, or_false] at hm
  rcases hm with rfl | rfl | rfl | rfl | rfl <;> norm_num

/-- So the exploration's `graded_escalation_correct` fails on its own five-filter stack:
starting at the substrate, the half-unit sum has no resolving layer. -/
theorem graded_escalation_claim_false :
    let filters : Fin 5 → ℕ := ![2, 4, 8, 144, 256]
    ¬ ∃ k', (floorResidue (filters k')).Congruent {0, 1/2} (· + ·) := by
  intro filters ⟨k', hk'⟩
  refine five_floor_filters_fail (filters k') ?_ hk'
  fin_cases k' <;> simp [filters]

/-! ## Complete decoding: no continuous choice of coset leaders -/

/-- **Every complete decoder jumps.** Let `ℓ` choose a leader in each coset of an additive
subgroup `Λ` (so `ℓ x - x ∈ Λ`), periodic along a lattice vector `v`, and suppose a continuous
linear functional `φ` is integer-valued on `Λ` with `φ v = 1`. Then `ℓ` is not continuous. -/
theorem no_continuous_leader {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (Λ : AddSubgroup E) (φ : E →L[ℝ] ℝ) (hφΛ : ∀ x ∈ Λ, ∃ z : ℤ, φ x = z)
    (v : E) (hv : φ v = 1) (ℓ : E → E) (hper : ∀ x, ℓ (x + v) = ℓ x)
    (hcoset : ∀ x, ℓ x - x ∈ Λ) : ¬ Continuous ℓ := by
  intro hℓ
  set g : ℝ → ℝ := fun t => φ (ℓ (t • v) - t • v) with hg
  have hgc : Continuous g := by
    apply φ.continuous.comp
    exact (hℓ.comp (continuous_id.smul continuous_const)).sub (continuous_id.smul continuous_const)
  have hint : ∀ t, ∃ z : ℤ, g t = z := fun t => hφΛ _ (hcoset _)
  have hg1 : g 1 = g 0 - 1 := by
    simp only [hg, one_smul, zero_smul, map_sub, hv]
    have : ℓ v = ℓ 0 := by simpa using hper 0
    rw [this]; simp
  obtain ⟨t, -, ht⟩ : g 0 - 1/2 ∈ g '' Set.Icc 0 1 := by
    apply intermediate_value_Icc' zero_le_one hgc.continuousOn
    constructor <;> linarith
  obtain ⟨a, ha⟩ := hint t
  obtain ⟨b, hb⟩ := hint 0
  rw [ha, hb] at ht
  have : (2 : ℝ) * (a - b) = -1 := by linarith
  have h2 : (2 : ℤ) * (a - b) = -1 := by exact_mod_cast this
  omega

end GLM.Escalation
