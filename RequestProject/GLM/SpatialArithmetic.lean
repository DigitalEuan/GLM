/-
# Spatial arithmetic: the polygon codec, and the totient sub-cycle law

Two of the archive's oldest scripts — `GMHGL/spatial_arithmetic.py` and
`GMHGL/spatial_totient_kinetics.py` — encode arithmetic in plane geometry rather
than in symbols:

> Signed integers are represented by regular unit-edge polygons embedded in 3-D.
> The vertex count stores magnitude and sign.  The empty space between adjacent
> polygons stores an operator.  An observer reconstructs the connected cycles,
> measures their geometry, decodes the expression, and evaluates it exactly.

Neither script was ever formalised.  Both claim properties that a codec must
have if it is to be a codec at all, and this file proves them.

## The codec

* `nodeCount v = 2|v| + 4 + [v < 0]` and `decodeNodeCount` — `nodeCount_roundtrip`
  and `nodeCount_injective` say the encoding is lossless, and
  `even_nodeCount_iff_nonneg` says where the sign is kept: in the *parity* of the
  vertex count, which is why the reader never needs a separate sign channel.
* `natural_add_identity` — the script's "node-count identity": for non-negative
  operands the sum is read straight off the combined vertex count,
  `(#A + #B − 2·4)/2 = a + b`.  No arithmetic on the values is performed; the
  count does it.
* `operatorCode_injective`, `one_lt_operatorCode` — the four operators are the
  four integer clearances `4, 5, 6, 7` between bounding spheres, all greater
  than one edge length.
* `dist_ge_clearance` — **why that matters.**  If two operand polygons are placed
  with clearance `k` between their bounding spheres then every cross pair of
  vertices is at distance at least `k`, so a unit-edge component detector can
  never join two operands.  Stated for an arbitrary metric space: it is the
  triangle inequality and nothing else.
* `circumradius`, `circumradius_strictMono` — the unit-edge `n`-gon's radius
  `R(n) = 1/(2 sin(π/n))` grows with `n`, so a larger magnitude really is a
  larger figure.

## The totient sub-cycle law

`spatial_totient_kinetics.py` states, as a "proven theorem", that the number of
closed internal diagonal loops of an `N`-gon under vertex jumping is
`C(N) = ⌊N/2⌋ − φ(N)/2`.  Here it is proved, in two halves:

* `jump_orbit_card` — jumping by `k` visits `N / gcd(N,k)` vertices, so the jump
  traverses the whole polygon exactly when `k` is coprime to `N`
  (`jump_traverses_iff_coprime`).
* `coprime_half_count` — among the step sizes `1 ≤ k ≤ ⌊N/2⌋` exactly `φ(N)/2`
  are coprime to `N`, because `k ↦ N − k` pairs the totatives and never fixes
  one.
* `subCycle_count` — hence exactly `⌊N/2⌋ − φ(N)/2` step sizes short-circuit,
  which is the claimed law.
-/
import Mathlib

namespace GLM.SpatialArithmetic

open Finset

/-! ## 1. The vertex-count codec -/

/-- The smallest polygon the codec uses. -/
def baseNodes : ℕ := 4

/-- Number of vertices representing a signed integer: `2|v| + 4`, plus one more
if `v` is negative. -/
def nodeCount (v : ℤ) : ℕ := 2 * v.natAbs + baseNodes + (if v < 0 then 1 else 0)

/-- The reader's inverse: the magnitude is `(c − 4)/2` and the sign is the parity
of `c`. -/
def decodeNodeCount (c : ℕ) : ℤ :=
  if c % 2 = 0 then (((c - baseNodes) / 2 : ℕ) : ℤ) else -(((c - baseNodes) / 2 : ℕ) : ℤ)

theorem baseNodes_le_nodeCount (v : ℤ) : baseNodes ≤ nodeCount v := by
  unfold nodeCount; omega

/-- **The sign lives in the parity of the vertex count.** -/
theorem even_nodeCount_iff_nonneg (v : ℤ) : nodeCount v % 2 = 0 ↔ 0 ≤ v := by
  unfold nodeCount baseNodes
  split_ifs with h <;> omega

/-- **The codec is lossless.** -/
theorem nodeCount_roundtrip (v : ℤ) : decodeNodeCount (nodeCount v) = v := by
  unfold decodeNodeCount nodeCount baseNodes
  split_ifs with h1 h2 <;> omega

theorem nodeCount_injective : Function.Injective nodeCount := by
  intro a b hab
  have := nodeCount_roundtrip a
  rw [hab, nodeCount_roundtrip b] at this
  exact this.symm

/-- **The node-count identity.**  For non-negative operands the sum is read off
the combined vertex count; nothing is added but vertices. -/
theorem natural_add_identity (a b : ℤ) (ha : 0 ≤ a) (hb : 0 ≤ b) :
    ((nodeCount a + nodeCount b - 2 * baseNodes) / 2 : ℕ) = (a + b).natAbs := by
  unfold nodeCount baseNodes
  split_ifs <;> omega

/-! ## 2. The operator codes -/

/-- The four operators of the codec. -/
inductive Op | multiply | divide | add | subtract
  deriving DecidableEq, Fintype

/-- The clearance, in edge lengths, that encodes each operator. -/
def operatorCode : Op → ℕ
  | .multiply => 4
  | .divide => 5
  | .add => 6
  | .subtract => 7

theorem operatorCode_injective : Function.Injective operatorCode := by decide

/-- Every operator code exceeds one edge length, which is what keeps the
operands apart. -/
theorem one_lt_operatorCode (o : Op) : 1 < operatorCode o := by
  cases o <;> simp [operatorCode]

/-- **Why the clearance is a separation.**  If the centres of two operand
figures are `rA + rB + k` apart and each vertex lies within its own bounding
radius, then every cross pair of vertices is at least `k` apart — so a
unit-edge component detector with `k > 1` can never join two operands.  Only the
triangle inequality is used. -/
theorem dist_ge_clearance {α : Type*} [MetricSpace α] {cA cB x y : α} {rA rB k : ℝ}
    (hAB : dist cA cB = rA + rB + k) (hx : dist cA x ≤ rA) (hy : dist cB y ≤ rB) :
    k ≤ dist x y := by
  have h1 : dist cA cB ≤ dist cA x + dist x y + dist y cB :=
    le_trans (dist_triangle cA x cB) (by
      have := dist_triangle x y cB
      linarith)
  rw [dist_comm y cB] at h1
  linarith

/-! ## 3. The figure grows with the magnitude -/

/-- Circumradius of a regular `n`-gon of unit edge. -/
noncomputable def circumradius (n : ℕ) : ℝ := 1 / (2 * Real.sin (Real.pi / n))

theorem sin_pi_div_pos {n : ℕ} (hn : 3 ≤ n) : 0 < Real.sin (Real.pi / n) := by
  have hn' : (3:ℝ) ≤ n := by exact_mod_cast hn
  have hn0 : (0:ℝ) < n := by linarith
  refine Real.sin_pos_of_pos_of_lt_pi (by positivity) ?_
  rw [div_lt_iff₀ hn0]
  nlinarith [Real.pi_pos]

theorem circumradius_pos {n : ℕ} (hn : 3 ≤ n) : 0 < circumradius n := by
  unfold circumradius
  have := sin_pi_div_pos hn
  positivity

/-- **A larger magnitude is a larger figure**: the unit-edge circumradius is
strictly increasing in the number of vertices. -/
theorem circumradius_strictMono {m n : ℕ} (hm : 3 ≤ m) (hmn : m < n) :
    circumradius m < circumradius n := by
  have hn : 3 ≤ n := le_trans hm (le_of_lt hmn)
  have hm' : (3:ℝ) ≤ m := by exact_mod_cast hm
  have hm0 : (0:ℝ) < m := by linarith
  have hn0 : (0:ℝ) < n := by positivity
  have hmn' : (m : ℝ) < n := by exact_mod_cast hmn
  have hlt : Real.pi / n < Real.pi / m := div_lt_div_of_pos_left Real.pi_pos hm0 hmn'
  have hle : Real.pi / m ≤ Real.pi / 2 := by
    rw [div_le_div_iff₀ hm0 (by norm_num)]
    nlinarith [Real.pi_pos]
  have hsin : Real.sin (Real.pi / n) < Real.sin (Real.pi / m) := by
    refine Real.sin_lt_sin_of_lt_of_le_pi_div_two ?_ hle hlt
    have h1 : (0:ℝ) < Real.pi / n := by positivity
    linarith [Real.pi_pos]
  have h1 := sin_pi_div_pos hn
  have h2 := sin_pi_div_pos hm
  unfold circumradius
  rw [div_lt_div_iff₀ (by linarith) (by linarith)]
  linarith

/-! ## 4. The totient sub-cycle law -/

/-- **Jumping by `k` visits `N / gcd(N,k)` of the `N` vertices.** -/
theorem jump_orbit_card {N : ℕ} (hN : N ≠ 0) (k : ℕ) :
    addOrderOf ((k : ZMod N)) = N / Nat.gcd N k :=
  ZMod.addOrderOf_coe k hN

/-- **The jump traverses the whole polygon exactly when the step is coprime to
the vertex count.** -/
theorem jump_traverses_iff_coprime {N : ℕ} (hN : N ≠ 0) (k : ℕ) :
    addOrderOf ((k : ZMod N)) = N ↔ Nat.gcd N k = 1 := by
  rw [jump_orbit_card hN k]
  have hdvd : Nat.gcd N k ∣ N := Nat.gcd_dvd_left N k
  have hpos : 0 < N := Nat.pos_of_ne_zero hN
  have hgpos : 0 < Nat.gcd N k := Nat.gcd_pos_of_pos_left k hpos
  constructor
  · intro h
    have h1 : Nat.gcd N k * N = N := by
      calc Nat.gcd N k * N = Nat.gcd N k * (N / Nat.gcd N k) := by rw [h]
        _ = N := Nat.mul_div_cancel' hdvd
    nlinarith [h1, hgpos, hpos]
  · intro h; rw [h, Nat.div_one]

/-- A totative of `N ≥ 3` in the lower half is strictly below the midpoint. -/
theorem two_mul_lt_of_coprime {N k : ℕ} (hN : 3 ≤ N) (hle : k ≤ N / 2)
    (hcop : Nat.gcd N k = 1) : 2 * k < N := by
  have h2 : 2 * k ≤ N := by omega
  rcases lt_or_eq_of_le h2 with h | h
  · exact h
  · exfalso
    have hdvd : k ∣ N := ⟨2, by omega⟩
    have : k ∣ Nat.gcd N k := Nat.dvd_gcd hdvd dvd_rfl
    rw [hcop] at this
    have : k = 1 := Nat.dvd_one.1 this
    omega

/-- **Half the totatives lie below the midpoint.**  `k ↦ N − k` pairs the
totatives of `N ≥ 3` and never fixes one. -/
theorem coprime_half_count (N : ℕ) (hN : 3 ≤ N) :
    2 * #((Ioc 0 (N / 2)).filter (fun k => Nat.gcd N k = 1)) = N.totient := by
  classical
  set L := (Ioc 0 (N / 2)).filter (fun k => Nat.gcd N k = 1) with hLdef
  set U := (Ioo (N / 2) N).filter (fun k => Nat.gcd N k = 1) with hUdef
  have hmemL : ∀ k, k ∈ L ↔ (0 < k ∧ k ≤ N / 2 ∧ Nat.gcd N k = 1) := by
    intro k; simp [hLdef, and_assoc]
  have hmemU : ∀ k, k ∈ U ↔ (N / 2 < k ∧ k < N ∧ Nat.gcd N k = 1) := by
    intro k; simp [hUdef, and_assoc]
  have hcard : #L = #U := by
    refine Finset.card_nbij' (i := fun k => N - k) (j := fun k => N - k) ?_ ?_ ?_ ?_
    · intro k hk
      rw [Finset.mem_coe, hmemL] at hk
      obtain ⟨hk0, hkle, hcop⟩ := hk
      have h2k := two_mul_lt_of_coprime hN hkle hcop
      have hA : N / 2 < N - k := by omega
      have hB : N - k < N := by omega
      have hC : Nat.gcd N (N - k) = 1 := by
        rw [Nat.gcd_self_sub_right (by omega : k ≤ N)]; exact hcop
      rw [Finset.mem_coe, hmemU]
      exact ⟨hA, hB, hC⟩
    · intro k hk
      rw [Finset.mem_coe, hmemU] at hk
      obtain ⟨hk0, hklt, hcop⟩ := hk
      have hA : 0 < N - k := by omega
      have hB : N - k ≤ N / 2 := by omega
      have hC : Nat.gcd N (N - k) = 1 := by
        rw [Nat.gcd_self_sub_right (by omega : k ≤ N)]; exact hcop
      rw [Finset.mem_coe, hmemL]
      exact ⟨hA, hB, hC⟩
    · intro k hk
      rw [Finset.mem_coe, hmemL] at hk
      show N - (N - k) = k
      omega
    · intro k hk
      rw [Finset.mem_coe, hmemU] at hk
      show N - (N - k) = k
      omega
  have hunion : (range N).filter (fun k => Nat.gcd N k = 1) = L ∪ U := by
    ext k
    simp only [Finset.mem_filter, Finset.mem_range, Finset.mem_union, hmemL, hmemU]
    constructor
    · rintro ⟨hklt, hcop⟩
      have hk0 : 0 < k := by
        rcases Nat.eq_zero_or_pos k with rfl | h
        · rw [Nat.gcd_zero_right] at hcop; omega
        · exact h
      rcases Nat.lt_or_ge (N / 2) k with h | h
      · exact Or.inr ⟨h, hklt, hcop⟩
      · exact Or.inl ⟨hk0, h, hcop⟩
    · rintro (⟨hk0, hle, hcop⟩ | ⟨hgt, hlt, hcop⟩)
      · exact ⟨by omega, hcop⟩
      · exact ⟨hlt, hcop⟩
  have hdisj : Disjoint L U := by
    rw [Finset.disjoint_left]
    intro a haL haU
    rw [hmemL] at haL
    rw [hmemU] at haU
    omega
  have htot : N.totient = #L + #U := by
    rw [Nat.totient]
    rw [show (Finset.filter N.Coprime (range N)) = (range N).filter (fun k => Nat.gcd N k = 1) from rfl]
    rw [hunion, Finset.card_union_of_disjoint hdisj]
  rw [htot, ← hcard]
  ring

/-- The number of step sizes that short-circuit: `C(N) = ⌊N/2⌋ − φ(N)/2`. -/
theorem subCycle_count (N : ℕ) (hN : 3 ≤ N) :
    #((Ioc 0 (N / 2)).filter (fun k => Nat.gcd N k ≠ 1)) = N / 2 - N.totient / 2 := by
  classical
  have hsplit :
      #((Ioc 0 (N / 2)).filter (fun k => Nat.gcd N k = 1))
        + #((Ioc 0 (N / 2)).filter (fun k => Nat.gcd N k ≠ 1)) = N / 2 := by
    rw [Finset.card_filter_add_card_filter_not]
    simp
  have hhalf := coprime_half_count N hN
  omega

end GLM.SpatialArithmetic
