/-
# Computing in superposition: what survives bundling a tie, and what does not

The directive "Geometric Ambiguity and Conceptual Superposition" asks the
machine to stop breaking the six-fold Golay tie and instead carry the whole
list forward as a parallel hypothesis space, bundled — in the Vector Symbolic
Architecture sense — either by `F₂` symmetric difference or by exact rational
addition.  It names both bundling rules in the same breath, as if they were
interchangeable implementations of one idea.

They are not, and this file proves the difference exactly.

* `bundleF2_eq_one` — the `F₂` bundle of the six candidates is the **all-ones
  word, whatever the received word was**.  Because the six error patterns
  partition the 24 coordinates (`sextet_partition`) and six copies of the
  received word cancel in characteristic two, XOR-bundling a complete tie
  destroys every bit of information it was supposed to preserve.
  `bundleF2_constant` states the consequence: two different received words
  bundle to the same hypervector.

* `bundleQ_eq` — the **rational** bundle is `(1 + 4·v)/6` coordinatewise: an
  affine, invertible image of the received word.  `bundleQ_injective` and
  `bundleQ_recover` say that nothing is lost: the received word is recovered
  from the bundle by `v = (6·b − 1)/4`, so the superposition really can be
  carried through downstream computation and collapsed later.

* `single_candidate_card` — and the cost of collapsing early: a single chosen
  codeword is consistent with all 10,626 received words at the covering radius,
  while the list determines the received word uniquely.

So of the two rules the directive lists under
`COMPUTING_IN_SUPERPOSITION_METHOD`, exactly one is a faithful carrier of a
complete tie.  The other is a constant.
-/
import RequestProject.GLM.Golay.Sextet

namespace GLM.Golay24

open Finset

/-! ## Indicators, in `F₂` and in `ℚ` -/

/-- The `F₂` indicator vector of a word. -/
def ind (c : Word) : Fin 24 → ZMod 2 := fun i => if i ∈ c then 1 else 0

/-- The rational indicator vector of a word. -/
def indQ (c : Word) : Fin 24 → ℚ := fun i => if i ∈ c then 1 else 0

theorem ind_symmDiff (a b : Word) : ind (symmDiff a b) = ind a + ind b := by
  funext i
  have h11 : (1 : ZMod 2) + 1 = 0 := by decide
  by_cases ha : i ∈ a <;> by_cases hb : i ∈ b <;>
    simp [ind, Finset.mem_symmDiff, ha, hb, h11]

theorem ind_univ : ind (univ : Word) = fun _ => 1 := by
  funext i; simp [ind]

theorem indQ_eq_one_iff {c : Word} {i : Fin 24} : indQ c i = 1 ↔ i ∈ c := by
  by_cases h : i ∈ c <;> simp [indQ, h]

theorem indQ_injective : Function.Injective indQ := by
  intro a b h
  ext i
  rw [← indQ_eq_one_iff, ← indQ_eq_one_iff, h]

/-! ## The tie, as a set of candidate codewords -/

/-- The six error patterns of the coset of `v`: its sextet. -/
def sextetOf (v : Word) : Finset Word := tetrads.filter (fun u => syn u = syn v)

/-- The candidate codewords the list decoder returns for `v`. -/
def candidates (v : Word) : Finset Word := (sextetOf v).image (fun u => symmDiff v u)

theorem mem_candidates {v c : Word} : c ∈ candidates v ↔ IsCodeword c ∧ hdist v c = 4 := by
  constructor
  · intro h
    obtain ⟨u, hu, rfl⟩ := Finset.mem_image.1 h
    simp only [sextetOf, Finset.mem_filter, mem_tetrads] at hu
    refine ⟨?_, ?_⟩
    · show syn (symmDiff v u) = 0
      rw [syn_symmDiff, hu.2]
      funext i
      have hy : ∀ y : ZMod 2, y + y = 0 := by decide
      exact hy _
    · rw [hdist_eq_wt_symmDiff, symmDiff_symmDiff_self]
      exact hu.1
  · rintro ⟨hcw, hd⟩
    refine Finset.mem_image.2 ⟨symmDiff v c, ?_, symmDiff_symmDiff_self v c⟩
    simp only [sextetOf, Finset.mem_filter, mem_tetrads]
    exact ⟨hd, syn_symmDiff_codeword hcw⟩

theorem sextetOf_card {v : Word} (h : CosetHasTetrad v) : (sextetOf v).card = 6 :=
  (sextet_partition h).1

theorem candidates_card {v : Word} (h : CosetHasTetrad v) : (candidates v).card = 6 := by
  rw [candidates, Finset.card_image_of_injective _ (fun a b hab => by
    have := congrArg (fun x => symmDiff v x) hab
    simpa [symmDiff_symmDiff_self] using this), sextetOf_card h]

/-- Each coordinate lies in exactly one tetrad of the sextet. -/
theorem exists_unique_mem_sextet {v : Word} (h : CosetHasTetrad v) (i : Fin 24) :
    ∃! u, u ∈ sextetOf v ∧ i ∈ u := by
  obtain ⟨_, hdisj, hcover⟩ := sextet_partition h
  have hi : i ∈ (sextetOf v).biUnion (fun u => u) := by
    rw [show (sextetOf v).biUnion (fun u => u)
        = (tetrads.filter fun u => syn u = syn v).biUnion (fun u => u) from rfl, hcover]
    exact Finset.mem_univ i
  obtain ⟨u, hu, hiu⟩ := Finset.mem_biUnion.1 hi
  refine ⟨u, ⟨hu, hiu⟩, ?_⟩
  rintro u' ⟨hu', hiu'⟩
  by_contra hne
  exact (Finset.disjoint_left.1 (hdisj u' hu' u hu hne) hiu') hiu

/-! ## `F₂` bundling destroys the tie -/

/-- The `F₂` (XOR) bundle of the candidate list. -/
def bundleF2 (v : Word) : Fin 24 → ZMod 2 := ∑ c ∈ candidates v, ind c

/-- **The XOR bundle is a constant.**  Bundling a complete six-fold tie by
symmetric difference always yields the all-ones word, whatever was received:
the six copies of `v` cancel in characteristic two and the six error patterns
sum to the whole coordinate set. -/
theorem bundleF2_eq_one {v : Word} (h : CosetHasTetrad v) :
    bundleF2 v = fun _ => 1 := by
  have hinj : Set.InjOn (fun u => symmDiff v u) (sextetOf v) := by
    intro a _ b _ hab
    have := congrArg (fun x => symmDiff v x) hab
    simpa [symmDiff_symmDiff_self] using this
  have hsum : bundleF2 v = ∑ u ∈ sextetOf v, ind (symmDiff v u) := by
    rw [bundleF2, candidates, Finset.sum_image (fun a ha b hb hab => hinj ha hb hab)]
  rw [hsum]
  have hsplit : ∑ u ∈ sextetOf v, ind (symmDiff v u)
      = (∑ _u ∈ sextetOf v, ind v) + ∑ u ∈ sextetOf v, ind u := by
    rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun u _ => ind_symmDiff v u
  rw [hsplit]
  have hcard : (sextetOf v).card = 6 := sextetOf_card h
  have hzero : (∑ _u ∈ sextetOf v, ind v) = 0 := by
    rw [Finset.sum_const, hcard]
    funext i
    simp only [Pi.smul_apply, Pi.zero_apply, nsmul_eq_mul]
    have h6 : ((6 : ℕ) : ZMod 2) = 0 := by decide
    rw [h6, zero_mul]
  rw [hzero, zero_add]
  -- the sextet is a partition, so its indicators sum to the all-ones word
  funext i
  obtain ⟨u0, ⟨hu0, hiu0⟩, huniq⟩ := exists_unique_mem_sextet h i
  rw [Finset.sum_apply, ← Finset.sum_erase_add _ _ hu0]
  have hrest : ∀ u ∈ (sextetOf v).erase u0, ind u i = 0 := by
    intro u hu
    have hne : u ≠ u0 := Finset.ne_of_mem_erase hu
    have hmem : u ∈ sextetOf v := Finset.mem_of_mem_erase hu
    have : i ∉ u := fun hi => hne (huniq u ⟨hmem, hi⟩)
    simp [ind, this]
  rw [Finset.sum_congr rfl hrest]
  simp [ind, hiu0]

/-- **The XOR bundle carries no information.**  Any two words at the covering
radius bundle to the same hypervector. -/
theorem bundleF2_constant {v v' : Word} (h : CosetHasTetrad v) (h' : CosetHasTetrad v') :
    bundleF2 v = bundleF2 v' := by
  rw [bundleF2_eq_one h, bundleF2_eq_one h']

/-! ## Rational bundling is faithful -/

/-- The exact rational bundle of the candidate list: the mean of the six
candidates, coordinate by coordinate. -/
def bundleQ (v : Word) : Fin 24 → ℚ := fun i => (∑ c ∈ candidates v, indQ c i) / 6

theorem indQ_symmDiff_of_mem {v u : Word} {i : Fin 24} (hi : i ∈ u) :
    indQ (symmDiff v u) i = 1 - indQ v i := by
  by_cases hv : i ∈ v <;> simp [indQ, Finset.mem_symmDiff, hi, hv]

theorem indQ_symmDiff_of_not_mem {v u : Word} {i : Fin 24} (hi : i ∉ u) :
    indQ (symmDiff v u) i = indQ v i := by
  by_cases hv : i ∈ v <;> simp [indQ, Finset.mem_symmDiff, hi, hv]

/-- **The rational bundle is an invertible image of the received word.**
Coordinatewise the bundle is `(1 + 4·vᵢ)/6`: five of the six candidates agree
with `v` at any coordinate, and exactly one — the candidate whose error tetrad
covers that coordinate — disagrees. -/
theorem bundleQ_eq {v : Word} (h : CosetHasTetrad v) (i : Fin 24) :
    bundleQ v i = (1 + 4 * indQ v i) / 6 := by
  have hinj : Set.InjOn (fun u => symmDiff v u) (sextetOf v) := by
    intro a _ b _ hab
    have := congrArg (fun x => symmDiff v x) hab
    simpa [symmDiff_symmDiff_self] using this
  have hsum : (∑ c ∈ candidates v, indQ c i) = ∑ u ∈ sextetOf v, indQ (symmDiff v u) i := by
    rw [candidates, Finset.sum_image (fun a ha b hb hab => hinj ha hb hab)]
  obtain ⟨u0, ⟨hu0, hiu0⟩, huniq⟩ := exists_unique_mem_sextet h i
  have hcard : (sextetOf v).card = 6 := sextetOf_card h
  have hrest : ∀ u ∈ (sextetOf v).erase u0, indQ (symmDiff v u) i = indQ v i := by
    intro u hu
    have hne : u ≠ u0 := Finset.ne_of_mem_erase hu
    have hmem : u ∈ sextetOf v := Finset.mem_of_mem_erase hu
    exact indQ_symmDiff_of_not_mem (fun hi => hne (huniq u ⟨hmem, hi⟩))
  have hercard : ((sextetOf v).erase u0).card = 5 := by
    rw [Finset.card_erase_of_mem hu0, hcard]
  have htotal : (∑ u ∈ sextetOf v, indQ (symmDiff v u) i) = 1 + 4 * indQ v i := by
    rw [← Finset.sum_erase_add _ _ hu0, Finset.sum_congr rfl hrest, Finset.sum_const,
      hercard, indQ_symmDiff_of_mem hiu0]
    ring
  rw [bundleQ, hsum, htotal]

/-- The bundle takes only two values per coordinate: `1/6` and `5/6`. -/
theorem bundleQ_values {v : Word} (h : CosetHasTetrad v) (i : Fin 24) :
    bundleQ v i = 1 / 6 ∨ bundleQ v i = 5 / 6 := by
  rw [bundleQ_eq h]
  by_cases hv : i ∈ v
  · right; simp [indQ, hv]; norm_num
  · left; simp [indQ, hv]

/-- **The received word is recovered from the bundle**: `v = (6·b − 1)/4`. -/
theorem bundleQ_recover {v : Word} (h : CosetHasTetrad v) (i : Fin 24) :
    indQ v i = (6 * bundleQ v i - 1) / 4 := by
  rw [bundleQ_eq h]
  field_simp
  ring

/-- **Rational bundling loses nothing.**  Two words at the covering radius with
the same bundle are equal, so the whole hypothesis space can be carried in one
hypervector and collapsed later. -/
theorem bundleQ_injective {v v' : Word} (h : CosetHasTetrad v) (h' : CosetHasTetrad v')
    (heq : bundleQ v = bundleQ v') : v = v' := by
  apply indQ_injective
  funext i
  rw [bundleQ_recover h i, bundleQ_recover h' i, heq]

/-! ## The cost of collapsing early -/

/-- **A single candidate is 10,626-fold ambiguous.**  Every codeword `c` is the
nearest codeword of exactly `C(24,4) = 10 626` words at the covering radius, so
a decoder that returns one codeword and discards the rest has thrown away the
identity of what it read — while the list, by `bundleQ_injective`, has not. -/
theorem single_candidate_card (c : Word) :
    #(univ.filter fun v => hdist v c = 4) = 10626 := by
  have hbij : #(univ.filter fun v => hdist v c = 4) = #tetrads := by
    refine Finset.card_nbij' (fun v => symmDiff v c) (fun u => symmDiff c u) ?_ ?_ ?_ ?_
    · intro v hv
      simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ, true_and] at hv
      simpa [mem_tetrads, wt] using hv
    · intro u hu
      simp only [Finset.mem_coe, mem_tetrads] at hu
      simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ, true_and]
      show (symmDiff (symmDiff c u) c).card = 4
      rw [show symmDiff (symmDiff c u) c = u by
        rw [symmDiff_comm (symmDiff c u) c, symmDiff_symmDiff_cancel_left]]
      exact hu
    · intro v _
      show symmDiff c (symmDiff v c) = v
      rw [symmDiff_comm v c, symmDiff_symmDiff_cancel_left]
    · intro u _
      show symmDiff (symmDiff c u) c = u
      rw [symmDiff_comm (symmDiff c u) c, symmDiff_symmDiff_cancel_left]
  rw [hbij, tetrads, Finset.card_powersetCard]
  simp only [Finset.card_univ, Fintype.card_fin]
  rfl

end GLM.Golay24
