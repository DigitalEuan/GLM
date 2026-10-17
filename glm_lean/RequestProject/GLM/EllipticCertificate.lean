module

public import RequestProject.GLM.LucasCertificate

/-!
# Elliptic-curve certificates: primality when neither `p - 1` nor `p + 1` splits

The formal half of `studies/ELLIPTIC_CERTIFICATE_STUDY.md` (Phase 141).
Pratt and Pocklington certificates need `p - 1` factored, N+1 certificates
`p + 1`; a prime where neither splits within the work budget was refused. This
file proves the check of a third kind of entry, which uses the group of an
elliptic curve instead of the multiplicative group modulo `p` (Goldwasser–Kilian,
Atkin–Morain), in a form whose proof needs only the trivial bound on the number
of points of a curve.

**The arithmetic.** Points of `y² = x³ + a·x + b` are written on naturals
modulo `p`: `none` is the point at infinity, `some (x, y)` an affine point.
`ecAdd` is the chord-and-tangent law; each division is a multiplication by an
inverse found by the extended Euclidean algorithm and **checked**
(`d · i ≡ 1`), and any step
the law cannot take modulo `p` (a check that fails, or `x₁ ≡ x₂` with
`y₁ ≢ ± y₂`) makes the whole computation fail (`none`). `ecMul` is
double-and-add with fuel.

**The entry.** An elliptic entry `(p, a, b, x, y, k, q)` is accepted
(`checkEEntry`) when `p` is odd and at least `3`, `4a³ + 27b²` is coprime to
`p`, `(x, y)` is on the curve modulo `p`, `q` was certified by an earlier
entry, `4p < (q - 1)²`, `Q = k·(x, y)` is computed as an *affine* point, and
`q·Q` is computed as the point at infinity.

**Why it is sound** (`elliptic_prime`). Let `r` be the least prime factor of
`p` and `E` the curve over `ZMod r`, an elliptic curve because `r` is odd and
the discriminant `-16(4a³ + 27b²)` is a unit. Every step the law takes modulo
`p` is a step of the group law of `E(ZMod r)` (`rep_ecAdd`, `rep_ecMulF`): an
inverse checked modulo `p` is an inverse modulo `r`. So `Q` reduces to a
nonzero point of `E(ZMod r)` killed by the prime `q`, whose order is therefore
`q`. But `E(ZMod r)` has at most `2r + 1` points (`card_point_le`: for each `x`
at most `y` and `-y`), so `q ≤ 2r + 1`; a composite `p` has `r² ≤ p`, hence
`(q - 1)² ≤ 4r² ≤ 4p`, which the entry excludes. No point counting, no Hasse
bound and no complex multiplication enters the proof: the run-time search
uses complex multiplication to *find* curves whose order has a large prime
factor, and a curve that does not have one simply fails the check.

**The chain** mixes the new entry with the Pocklington and N+1 entries of
`LucasCertificate.lean` (`EEntry`); `checkEChain_sound` and `elliptic_sound`
— **the check the tool runs** — show every entry of an accepted chain is prime.
-/

public section

namespace GLM.PrimalityCertificate

/-! ## Arithmetic on the curve modulo `p` -/

/-- The extended Euclidean algorithm with fuel, on naturals: the invariant
`rᵢ ≡ sᵢ·d (mod p)` keeps `sᵢ` reduced modulo `p`. -/
@[expose] def invF (p : ℕ) : ℕ → ℕ → ℕ → ℕ → ℕ → ℕ
  | 0, _, _, s₀, _ => s₀
  | fuel + 1, r₀, r₁, s₀, s₁ =>
    if r₁ = 0 then s₀ else invF p fuel r₁ (r₀ % r₁) s₁ ((s₀ + p - r₀ / r₁ * s₁ % p) % p)

/-- An inverse of `d` modulo `p`, by the extended Euclidean algorithm; whether
it *is* an inverse is checked by every caller (`d · i ≡ 1`), so nothing about
the algorithm enters any proof. -/
@[expose] def finv (p d : ℕ) : ℕ := invF p p p (d % p) 0 1

/-- The chord-and-tangent law on `y² = x³ + a·x + b` modulo `p`; `none` when a
step cannot be taken modulo `p`. -/
@[expose] def ecAdd (p a : ℕ) : Option (ℕ × ℕ) → Option (ℕ × ℕ) → Option (Option (ℕ × ℕ))
  | none, Q => some Q
  | some P, none => some (some P)
  | some (x₁, y₁), some (x₂, y₂) =>
    if x₁ % p = x₂ % p then
      if (y₁ + y₂) % p = 0 then some none
      else if y₁ % p = y₂ % p then
        let d := 2 * y₁ % p
        let i := finv p d
        if d * i % p = 1 then
          let l := (3 * x₁ * x₁ + a) * i % p
          let x₃ := (l * l + 2 * (p - x₁ % p)) % p
          some (some (x₃, (l * (x₁ % p + p - x₃) + (p - y₁ % p)) % p))
        else none
      else none
    else
      let d := (x₂ % p + p - x₁ % p) % p
      let i := finv p d
      if d * i % p = 1 then
        let l := (y₂ % p + p - y₁ % p) * i % p
        let x₃ := (l * l + (p - x₁ % p) + (p - x₂ % p)) % p
        some (some (x₃, (l * (x₁ % p + p - x₃) + (p - y₁ % p)) % p))
      else none

/-- Double-and-add with fuel; `none` when a step fails or the fuel runs out. -/
@[expose] def ecMulF (p a : ℕ) : ℕ → ℕ → Option (ℕ × ℕ) → Option (Option (ℕ × ℕ))
  | 0, k, _ => if k = 0 then some none else none
  | fuel + 1, k, P =>
    if k = 0 then some none
    else
      match ecMulF p a fuel (k / 2) P with
      | none => none
      | some H =>
        match ecAdd p a H H with
        | none => none
        | some D => if k % 2 = 0 then some D else ecAdd p a D P

/-- `k · P` on the curve modulo `p`. -/
@[expose] def ecMul (p a k : ℕ) (P : Option (ℕ × ℕ)) : Option (Option (ℕ × ℕ)) :=
  ecMulF p a k k P

/-! ## The curve modulo a prime factor -/

/-- `y² = x³ + a·x + b` over `ZMod r`. -/
@[expose] def curve (r a b : ℕ) : WeierstrassCurve (ZMod r) :=
  { a₁ := 0, a₂ := 0, a₃ := 0, a₄ := (a : ZMod r), a₆ := (b : ZMod r) }

/-- A point modulo `p` read as a point of the curve over `ZMod r`. -/
def Rep {r : ℕ} (W : WeierstrassCurve (ZMod r)) : Option (ℕ × ℕ) → W.toAffine.Point → Prop
  | none, P => P = 0
  | some (x, y), P => ∃ h : W.toAffine.Nonsingular (x : ZMod r) (y : ZMod r), P = .some h

theorem natCast_mod_of_dvd {r p : ℕ} (hrp : r ∣ p) (n : ℕ) :
    ((n % p : ℕ) : ZMod r) = n := by
  have hp : (p : ZMod r) = 0 := (ZMod.natCast_eq_zero_iff _ _).2 hrp
  conv_rhs => rw [← Nat.mod_add_div n p]
  push_cast
  rw [hp]; ring

theorem natCast_neg_mod {r p : ℕ} (hrp : r ∣ p) (hp : 0 < p) (n : ℕ) :
    ((p - n % p : ℕ) : ZMod r) = -(n : ZMod r) := by
  have hp0 : (p : ZMod r) = 0 := (ZMod.natCast_eq_zero_iff _ _).2 hrp
  rw [Nat.cast_sub (Nat.mod_lt n hp).le, natCast_mod_of_dvd hrp, hp0, zero_sub]

theorem natCast_sub_mod {r p : ℕ} (hrp : r ∣ p) (hp : 0 < p) (m n : ℕ) :
    ((m % p + p - n % p : ℕ) : ZMod r) = (m : ZMod r) - n := by
  have hp0 : (p : ZMod r) = 0 := (ZMod.natCast_eq_zero_iff _ _).2 hrp
  rw [Nat.cast_sub (by have := Nat.mod_lt n hp; omega), Nat.cast_add,
    natCast_mod_of_dvd hrp, natCast_mod_of_dvd hrp, hp0, add_zero]

theorem rep_some_of_eq {r : ℕ} {W : WeierstrassCurve (ZMod r)} {x y : ℕ} :
    ∀ {X Y : ZMod r} (h : W.toAffine.Nonsingular X Y), (x : ZMod r) = X → (y : ZMod r) = Y →
      Rep W (some (x, y)) (.some h) := by
  intro X Y h hx hy
  subst hx hy
  exact ⟨h, rfl⟩

theorem rep_ecAdd {r p a b : ℕ} [Fact r.Prime] (hrp : r ∣ p) (hp : 0 < p)
    {P Q : Option (ℕ × ℕ)} {Pt Qt : (curve r a b).toAffine.Point}
    (hP : Rep (curve r a b) P Pt) (hQ : Rep (curve r a b) Q Qt)
    {R : Option (ℕ × ℕ)} (h : ecAdd p a P Q = some R) :
    Rep (curve r a b) R (Pt + Qt) := by
  rcases P with _ | ⟨x₁, y₁⟩
  · simp only [ecAdd, Option.some.injEq] at h
    subst h
    simp only [Rep] at hP
    rw [hP, zero_add]; exact hQ
  rcases Q with _ | ⟨x₂, y₂⟩
  · simp only [ecAdd, Option.some.injEq] at h
    subst h
    simp only [Rep] at hQ
    rw [hQ, add_zero]; exact hP
  obtain ⟨h₁, rfl⟩ := hP
  obtain ⟨h₂, rfl⟩ := hQ
  have cast_eq : ∀ m n : ℕ, m % p = n % p → (m : ZMod r) = n := by
    intro m n hmn
    rw [← natCast_mod_of_dvd hrp m, hmn, natCast_mod_of_dvd hrp]
  have cast_one : ∀ m : ℕ, m % p = 1 → (m : ZMod r) = 1 := by
    intro m hm
    rw [← natCast_mod_of_dvd hrp m, hm, Nat.cast_one]
  simp only [ecAdd] at h
  split_ifs at h with hx hy hyy hd hd'
  · cases h
    have hx' := cast_eq _ _ hx
    have hy' : (y₁ : ZMod r) = (curve r a b).toAffine.negY x₂ y₂ := by
      have : ((y₁ + y₂ : ℕ) : ZMod r) = 0 := by
        rw [← natCast_mod_of_dvd hrp, hy, Nat.cast_zero]
      simp only [WeierstrassCurve.Affine.negY, curve]
      push_cast at this
      linear_combination this
    exact WeierstrassCurve.Affine.Point.add_of_Y_eq hx' hy'
  · cases h
    have hx' := cast_eq _ _ hx
    have hyy' := cast_eq _ _ hyy
    have hdi := cast_one _ hd
    simp only [Nat.cast_mul, natCast_mod_of_dvd hrp] at hdi
    push_cast at hdi
    have hne : (y₁ : ZMod r) ≠ (curve r a b).toAffine.negY x₂ y₂ := by
      intro he
      simp only [WeierstrassCurve.Affine.negY, curve] at he
      have h2 : 2 * (y₁ : ZMod r) = 0 := by rw [hyy'] at he ⊢; linear_combination he
      rw [h2, zero_mul] at hdi
      exact zero_ne_one hdi
    rw [WeierstrassCurve.Affine.Point.add_of_Y_ne hne]
    have h2y : 2 * (y₁ : ZMod r) ≠ 0 := by
      intro h0; rw [h0, zero_mul] at hdi; exact zero_ne_one hdi
    have hi := eq_inv_of_mul_eq_one_right hdi
    have hsl : (curve r a b).toAffine.slope x₁ x₂ y₁ y₂ =
        (3 * (x₁ : ZMod r) * x₁ + a) * (finv p (2 * y₁ % p) : ZMod r) := by
      rw [WeierstrassCurve.Affine.slope_of_Y_ne hx' hne, hi]
      simp only [WeierstrassCurve.Affine.negY, curve]
      field_simp
      ring
    apply rep_some_of_eq
    · simp only [WeierstrassCurve.Affine.addX]
      rw [hsl]
      simp only [curve, natCast_mod_of_dvd hrp,
        natCast_neg_mod hrp hp, Nat.cast_add, Nat.cast_mul, Nat.cast_ofNat]
      rw [← hx']
      ring
    · simp only [WeierstrassCurve.Affine.addY, WeierstrassCurve.Affine.negAddY,
        WeierstrassCurve.Affine.addX]
      rw [hsl]
      simp only [WeierstrassCurve.Affine.negY, curve,
        natCast_mod_of_dvd hrp, natCast_neg_mod hrp hp, natCast_sub_mod hrp hp, Nat.cast_add,
        Nat.cast_mul, Nat.cast_ofNat]
      rw [← hx']
      ring
  · cases h
    have hdi := cast_one _ hd'
    simp only [Nat.cast_mul, natCast_mod_of_dvd hrp, natCast_sub_mod hrp hp] at hdi
    have hx' : (x₁ : ZMod r) ≠ x₂ := by
      intro he; rw [he, sub_self, zero_mul] at hdi; exact zero_ne_one hdi
    rw [WeierstrassCurve.Affine.Point.add_of_X_ne hx']
    have hi := eq_inv_of_mul_eq_one_right hdi
    have hsl : (curve r a b).toAffine.slope x₁ x₂ y₁ y₂ =
        ((y₂ : ZMod r) - y₁) * (finv p ((x₂ % p + p - x₁ % p) % p) : ZMod r) := by
      rw [WeierstrassCurve.Affine.slope_of_X_ne hx', hi]
      have : (x₂ : ZMod r) - x₁ ≠ 0 := sub_ne_zero.2 (Ne.symm hx')
      have : (x₁ : ZMod r) - x₂ ≠ 0 := sub_ne_zero.2 hx'
      field_simp
      ring
    apply rep_some_of_eq
    · simp only [WeierstrassCurve.Affine.addX]
      rw [hsl]
      simp only [curve, natCast_mod_of_dvd hrp,
        natCast_neg_mod hrp hp, natCast_sub_mod hrp hp, Nat.cast_add, Nat.cast_mul]
      ring
    · simp only [WeierstrassCurve.Affine.addY, WeierstrassCurve.Affine.negAddY,
        WeierstrassCurve.Affine.addX]
      rw [hsl]
      simp only [WeierstrassCurve.Affine.negY, curve,
        natCast_mod_of_dvd hrp, natCast_neg_mod hrp hp, natCast_sub_mod hrp hp, Nat.cast_add,
        Nat.cast_mul]
      ring

theorem rep_ecMulF {r p a b : ℕ} [Fact r.Prime] (hrp : r ∣ p) (hp : 0 < p)
    {P : Option (ℕ × ℕ)} {Pt : (curve r a b).toAffine.Point}
    (hP : Rep (curve r a b) P Pt) :
    ∀ fuel k {R : Option (ℕ × ℕ)}, ecMulF p a fuel k P = some R →
      Rep (curve r a b) R (k • Pt) := by
  intro fuel
  induction fuel with
  | zero =>
    intro k R h
    simp only [ecMulF] at h
    split_ifs at h with hk
    cases h; subst hk
    exact zero_nsmul Pt
  | succ n ih =>
    intro k R h
    by_cases hk : k = 0
    · subst hk
      simp only [ecMulF, if_true] at h
      cases h
      exact zero_nsmul Pt
    simp only [ecMulF, if_neg hk] at h
    cases hH : ecMulF p a n (k / 2) P with
    | none => rw [hH] at h; simp at h
    | some H =>
      rw [hH] at h
      have hH' := ih (k / 2) hH
      cases hD : ecAdd p a H H with
      | none => simp [hD] at h
      | some D =>
        simp only [hD] at h
        have hD' := rep_ecAdd hrp hp hH' hH' hD
        by_cases h2 : k % 2 = 0
        · rw [if_pos h2] at h
          cases h
          have : k = k / 2 + k / 2 := by omega
          rw [this, add_smul]; exact hD'
        · rw [if_neg h2] at h
          have : k = k / 2 + k / 2 + 1 := by omega
          rw [this, add_smul, add_smul, one_smul]
          exact rep_ecAdd hrp hp hD' hP h

/-- The trivial bound: a Weierstrass curve `y² = x³ + a·x + b` over `ZMod r`
has at most `2r + 1` points, since each `x` carries at most `y` and `-y`. -/
theorem card_point_le (r a b : ℕ) [Fact r.Prime] :
    Finite (curve r a b).toAffine.Point ∧ Nat.card (curve r a b).toAffine.Point ≤ 2 * r + 1 := by
  let f : (curve r a b).toAffine.Point → Option (ZMod r × Bool)
    | .zero => none
    | @WeierstrassCurve.Affine.Point.some _ _ _ x y _ => some (x, decide (y.val < (-y).val))
  have hf : Function.Injective f := by
    rintro (_ | @⟨x, y, h⟩) (_ | @⟨x', y', h'⟩) hxy
    · rfl
    · simp [f] at hxy
    · simp [f] at hxy
    · simp only [f, Option.some.injEq, Prod.mk.injEq] at hxy
      obtain ⟨rfl, hb⟩ := hxy
      have e := h.1
      have e' := h'.1
      rw [WeierstrassCurve.Affine.equation_iff] at e e'
      simp only [curve] at e e'
      have hsq : (y' - y) * (y' + y) = 0 := by linear_combination e' - e
      rcases mul_eq_zero.1 hsq with h0 | h0
      · have : y' = y := by linear_combination h0
        subst this; rfl
      · have hy' : y' = -y := by linear_combination h0
        subst hy'
        rw [neg_neg] at hb
        have : y = -y := by
          by_contra hne
          have hv : y.val ≠ (-y).val := fun hv => hne (ZMod.val_injective _ hv)
          rcases lt_or_gt_of_ne hv with hl | hl
          · have := hb; simp [hl, not_lt.2 hl.le] at this
          · have := hb; simp [hl, not_lt.2 hl.le] at this
        have hyy : -y = y := this.symm
        simp only [hyy]
  haveI : Finite (curve r a b).toAffine.Point := Finite.of_injective f hf
  refine ⟨this, ?_⟩
  have := Nat.card_le_card_of_injective f hf
  rw [Nat.card_eq_fintype_card (α := Option (ZMod r × Bool)), Fintype.card_option, Fintype.card_prod, ZMod.card,
    Fintype.card_bool] at this
  omega

/-! ## The elliptic entry -/

/-- One elliptic entry `(p, a, b, x, y, k, q)`, checked against the primes
`known` certified by earlier entries. -/
@[expose] def checkEEntry (known : List ℕ) (p a b x y k q : ℕ) : Bool :=
  decide (3 ≤ p) && (p % 2 == 1) && (Nat.gcd ((4 * a * a * a + 27 * b * b) % p) p == 1) &&
    ((y * y) % p == (x * x * x + a * x + b) % p) && decide (q ∈ known) &&
    decide (4 * p < (q - 1) * (q - 1)) &&
    (match ecMul p a k (some (x, y)) with
      | some (some Q) => ecMul p a q (some Q) == some none
      | _ => false)

/-- **The elliptic test.** An accepted elliptic entry is about a prime. -/
theorem elliptic_prime {known : List ℕ} {p a b x y k q : ℕ}
    (hk : ∀ q ∈ known, q.Prime) (h : checkEEntry known p a b x y k q = true) : p.Prime := by
  simp only [checkEEntry, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨hp3, hodd⟩, hgcd⟩, heq⟩, hq⟩, hbound⟩, hm⟩ := h
  have hqp : q.Prime := hk q hq
  haveI := Fact.mk hqp
  by_contra hnp
  have hr : p.minFac.Prime := Nat.minFac_prime (by omega)
  haveI := Fact.mk hr
  have hrp : p.minFac ∣ p := Nat.minFac_dvd p
  have hsq : p.minFac ^ 2 ≤ p := Nat.minFac_sq_le_self (by omega) hnp
  have hp0 : 0 < p := by omega
  set r := p.minFac with hr_def
  -- `r` is odd, so `2` is a unit modulo `r`
  have hr2 : (2 : ZMod r) ≠ 0 := by
    intro h2
    have : (r : ℕ) ∣ 2 := by
      have := (ZMod.natCast_eq_zero_iff 2 r).1 (by exact_mod_cast h2)
      exact this
    have hr2' : r = 2 := (Nat.prime_dvd_prime_iff_eq hr Nat.prime_two).1 this
    have : 2 ∣ p := hr2' ▸ hrp
    omega
  -- the discriminant is a unit modulo `r`
  have hdisc : ((4 * a * a * a + 27 * b * b : ℕ) : ZMod r) ≠ 0 := by
    rw [← natCast_mod_of_dvd hrp, Ne, ZMod.natCast_eq_zero_iff]
    intro hd
    have := Nat.dvd_gcd hd hrp
    rw [hgcd] at this
    exact hr.one_lt.ne' (Nat.dvd_one.1 this)
  have hΔ : (curve r a b).Δ ≠ 0 := by
    have : (curve r a b).Δ = -16 * ((4 * a * a * a + 27 * b * b : ℕ) : ZMod r) := by
      simp only [WeierstrassCurve.Δ, WeierstrassCurve.b₂, WeierstrassCurve.b₄,
        WeierstrassCurve.b₆, WeierstrassCurve.b₈, curve]
      push_cast; ring
    rw [this]
    refine mul_ne_zero ?_ hdisc
    have : (-16 : ZMod r) = -(2 ^ 4) := by norm_num
    rw [this, neg_ne_zero]
    exact pow_ne_zero _ hr2
  -- the base point is on the curve modulo `r`, hence nonsingular
  have hE : (curve r a b).toAffine.Equation (x : ZMod r) (y : ZMod r) := by
    rw [WeierstrassCurve.Affine.equation_iff]
    have := congrArg (fun n : ℕ => (n : ZMod r)) heq
    simp only [natCast_mod_of_dvd hrp] at this
    simp only [curve]
    push_cast at this
    linear_combination this
  have hN := (WeierstrassCurve.Affine.equation_iff_nonsingular_of_Δ_ne_zero hΔ).1 hE
  have hP : Rep (curve r a b) (some (x, y)) (.some hN) := ⟨hN, rfl⟩
  split at hm
  · rename_i Q hQ
    have hkP := rep_ecMulF hrp hp0 hP k k hQ
    have hm' : ecMulF p a q q (some Q) = some none := by
      simpa only [ecMul, beq_iff_eq] using hm
    have hqQ := rep_ecMulF hrp hp0 hkP q q hm'
    obtain ⟨Q₁, Q₂⟩ := Q
    obtain ⟨hQN, hkP'⟩ := hkP
    have hq0 : q • (k • WeierstrassCurve.Affine.Point.some hN) = 0 := hqQ
    have hne : k • WeierstrassCurve.Affine.Point.some hN ≠ 0 := by
      rw [hkP']; exact WeierstrassCurve.Affine.Point.some_ne_zero _
    have hord := addOrderOf_eq_prime hq0 hne
    obtain ⟨hfin, hcard⟩ := card_point_le r a b
    have hle : q ≤ Nat.card (curve r a b).toAffine.Point := hord ▸ addOrderOf_le_card
    have h1 : q - 1 ≤ 2 * r := by omega
    have h2 : (q - 1) * (q - 1) ≤ 2 * r * (2 * r) := Nat.mul_le_mul h1 h1
    have h3 : 2 * r * (2 * r) = 4 * r ^ 2 := by ring
    omega
  · simp at hm

/-! ## Chains with elliptic entries -/

/-- An entry of a chain: a Pocklington or N+1 entry, or an elliptic entry. -/
inductive EEntry where
  | base (e : Entry)
  | ec (p a b x y k q : ℕ)

/-- The number an entry is about. -/
@[expose] def EEntry.num : EEntry → ℕ
  | .base e => e.num
  | .ec p _ _ _ _ _ _ => p

/-- One entry, of any kind. -/
@[expose] def checkEAnyEntry (known : List ℕ) : EEntry → Bool
  | .base e => checkAnyEntry known e
  | .ec p a b x y k q => checkEEntry known p a b x y k q

/-- A chain, each entry checked against the primes before it. -/
@[expose] def checkEChain : List ℕ → List EEntry → Bool
  | _, [] => true
  | known, e :: rest => checkEAnyEntry known e && checkEChain (e.num :: known) rest

/-- `c` certifies that `n` is prime. -/
@[expose] def certifiesE (n : ℕ) (c : List EEntry) : Bool :=
  checkEChain [] c && c.any (fun e => e.num == n)

theorem checkEAnyEntry_sound {known : List ℕ} {e : EEntry}
    (hk : ∀ q ∈ known, q.Prime) (h : checkEAnyEntry known e = true) : e.num.Prime := by
  cases e with
  | base e => exact checkAnyEntry_sound hk h
  | ec p a b x y k q => exact elliptic_prime hk h

/-- Every entry of an accepted chain is about a prime. -/
theorem checkEChain_sound :
    ∀ (c : List EEntry) (known : List ℕ), (∀ q ∈ known, q.Prime) →
      checkEChain known c = true → ∀ e ∈ c, e.num.Prime := by
  intro c
  induction c with
  | nil => intro _ _ _ e he; simp at he
  | cons hd rest ih =>
    intro known hk h
    simp only [checkEChain, Bool.and_eq_true] at h
    have hp := checkEAnyEntry_sound hk h.1
    have hrest := ih (hd.num :: known) (by
      intro q hq
      rcases List.mem_cons.1 hq with rfl | hq
      · exact hp
      · exact hk q hq) h.2
    intro e he
    rcases List.mem_cons.1 he with rfl | he
    · exact hp
    · exact hrest e he

/-- **The check the tool runs**: an accepted certificate with elliptic entries
for `n` shows that `n` is prime. -/
theorem elliptic_sound {n : ℕ} {c : List EEntry} (h : certifiesE n c = true) : n.Prime := by
  simp only [certifiesE, Bool.and_eq_true, List.any_eq_true, beq_iff_eq] at h
  obtain ⟨hc, e, he, rfl⟩ := h
  exact checkEChain_sound c [] (by simp) hc e he

/-! ## An instance neither `p - 1` nor `p + 1` reached -/

/-- The certificate `glm_universal.reasoning.primality_certificate.certify`
produces for `2^255 - 19` (the Curve25519 field prime, RFC 7748), copied
verbatim: Pocklington and N+1 entries for the small primes and five elliptic
entries descending from `2^255 - 19`. The Phase 140 certifier refused this
number: neither `p - 1` nor `p + 1` split within the work budget. -/
def cert_2_255_sub_19 : List EEntry :=
  [.base (.pock 2 []),
    .base (.pock 5 [(2, 2, 2)]),
    .base (.pock 3 []),
    .base (.pock 61 [(2, 2, 2), (3, 1, 2)]),
    .base (.pock 101 [(2, 2, 2), (5, 2, 2)]),
    .base (.pock 607 [(2, 1, 3), (3, 1, 2), (101, 1, 2)]),
    .base (.pock 43 [(2, 1, 2), (3, 1, 3)]),
    .base (.pock 173 [(2, 2, 2), (43, 1, 2)]),
    .base (.pock 1039 [(2, 1, 3), (3, 1, 2), (173, 1, 2)]),
    .base (.pock 17 [(2, 4, 3)]),
    .base (.pock 137 [(2, 3, 3), (17, 1, 2)]),
    .base (.lucas 4657 3 [(2, 1), (17, 1), (137, 1)]),
    .base (.pock 73 [(2, 3, 5)]),
    .base (.pock 293 [(2, 2, 2), (73, 1, 2)]),
    .base (.lucas 59771 17 [(2, 2), (3, 1), (17, 1), (293, 1)]),
    .base (.pock 19 [(2, 1, 2), (3, 2, 2)]),
    .base (.pock 7 [(2, 1, 3)]),
    .base (.pock 13 [(2, 2, 2)]),
    .base (.pock 53 [(2, 2, 2), (13, 1, 2)]),
    .base (.pock 107 [(2, 1, 2), (53, 1, 2)]),
    .base (.pock 1499 [(2, 1, 2), (7, 1, 2), (107, 1, 2)]),
    .base (.lucas 89939 22 [(2, 2), (3, 1), (5, 1), (1499, 1)]),
    .base (.lucas 6835363 6 [(2, 2), (19, 1), (89939, 1)]),
    .base (.lucas 731968542009516166067329 17 [(2, 1), (5, 1), (61, 1), (607, 1), (1039, 1), (4657, 1), (59771, 1), (6835363, 1)]),
    .ec 6882305636640103496420799884323364902037 1 0 2 657684062143154659737303346196919155816 9402460955146660 731968542009516166067329,
    .ec 122150202418179951780222441427702513729864363609 7 0 1 82098135494331596873942291554823063555119927655 17748442 6882305636640103496420799884323364902037,
    .ec 99891730601060994184623016610231755004557778507865192738311046749 1 0 3 14147900581418058180752735573168274541366158004354621028849166601 817777855652524340 122150202418179951780222441427702513729864363609,
    .ec 1231665038311082058296401794804157600809929321178200288861124643260049 29 0 1 972399650946008284536188552390504236294986164963302181080128256683349 12330 99891730601060994184623016610231755004557778507865192738311046749,
    .ec 57896044618658097711785492504343953926634992332820282019728792003956564819949 0 2 1 42866205148224706689520316867404180639008696231783436520640712727970230077114 47006323 1231665038311082058296401794804157600809929321178200288861124643260049]

/-- `2^255 - 19` is prime: the elliptic certificate the run-time tool
produced, checked by the kernel. -/
theorem prime_2_255_sub_19 : Nat.Prime (2 ^ 255 - 19) :=
  elliptic_sound (c := cert_2_255_sub_19) (by decide +kernel)

end GLM.PrimalityCertificate
