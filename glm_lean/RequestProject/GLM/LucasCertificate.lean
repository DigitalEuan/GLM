module

public import RequestProject.GLM.PocklingtonCertificate

/-!
# N+1 certificates: primality from the factorisation of `p + 1`

The formal half of part B of `studies/POCKLINGTON_CERTIFICATE_STUDY.md`
(Phase 140). Pratt and Pocklington certificates factor `p - 1`; the primes the
first held-out set left refused (`33! - 1`, `94! - 1`, `317# - 1`, …) have a
`p - 1` that will not split but a `p + 1` made of small primes. This file
proves the check that uses `p + 1` instead.

**The ring.** For `p` and `P` the certificate works in
`(ZMod p)[X] / (X² - P·X + 1)`, written on pairs of naturals `(a, b) ↦ a + b·X`
(`qmul`, `qpow`): `X² = P·X - 1`, so `(a + bX)(c + dX) = ac - bd + (ad + bc + Pbd)X`,
with `-bd` computed as `bd·(p - 1)` modulo `p`. The norm of `u + vX` is
`u² + P·u·v + v²` (`qnorm`).

**The entry.** A Lucas entry `(p, P, [(q₁, e₁), …])` is accepted
(`checkLEntry`) when `p ≥ 2`, `∏ qᵢ ^ eᵢ = p + 1`, every `qᵢ` was certified by
an earlier entry, `X ^ (p + 1) = 1`, and for every `i` the norm of
`X ^ ((p + 1) / qᵢ) - 1` is coprime to `p`.

**Why it is sound** (`lucas_prime`). Let `r` be the least prime factor of `p`
and work in `R = (ZMod r)[X] / (X² - P·X + 1)`, a ring with `r²` elements
(`card_quadRing`). The pair arithmetic is the arithmetic of `R` read modulo
`r` (`toQuad_qmul`, `toQuad_qpow`); `X` is a unit of `R`; a coprime norm makes
`X ^ ((p + 1) / q) - 1` a unit, hence nonzero. So `X` has order exactly
`p + 1` in `Rˣ`, and `p + 1 ≤ #Rˣ < r²`. A composite `p` has `r² ≤ p`, which is
impossible. No quadratic non-residue is needed in the proof: a `P` that does
not give order `p + 1` simply fails the check.

**The chain** mixes the two kinds of entry (`Entry.pock`, `Entry.lucas`);
`checkMChain_sound` and `mixed_sound` — **the check the tool runs** — show
every entry of an accepted chain is prime.

A worked instance, checked by the kernel: `prime_33_factorial_sub_one`,
`33! - 1` (OEIS A002982), which the first held-out set left refused.
-/

public section

namespace GLM.PrimalityCertificate

open Polynomial

/-! ## Pair arithmetic in `(ZMod p)[X] / (X² - P·X + 1)` -/

/-- Multiplication of `a + bX` and `c + dX` modulo `p` and `X² - P·X + 1`. -/
@[expose] def qmul (p P : ℕ) (x y : ℕ × ℕ) : ℕ × ℕ :=
  ((x.1 * y.1 + x.2 * y.2 * (p - 1)) % p, (x.1 * y.2 + x.2 * y.1 + P * x.2 * y.2) % p)

/-- Repeated multiplication (the fallback of `qpowF`, never reached). -/
@[expose] def qpowSlow (p P : ℕ) (b : ℕ × ℕ) : ℕ → ℕ × ℕ
  | 0 => (1 % p, 0)
  | k + 1 => qmul p P (qpowSlow p P b k) b

/-- Square-and-multiply with fuel. -/
@[expose] def qpowF (p P : ℕ) : ℕ → ℕ × ℕ → ℕ → ℕ × ℕ
  | 0, b, e => qpowSlow p P b e
  | fuel + 1, b, e =>
    if e = 0 then (1 % p, 0)
    else
      let r := qpowF p P fuel (qmul p P b b) (e / 2)
      if e % 2 = 0 then r else qmul p P r b

/-- `b ^ e` in the ring, by square-and-multiply. -/
@[expose] def qpow (p P : ℕ) (b : ℕ × ℕ) (e : ℕ) : ℕ × ℕ := qpowF p P e b e

/-- `x - 1` in the ring. -/
@[expose] def qsubOne (p : ℕ) (x : ℕ × ℕ) : ℕ × ℕ := ((x.1 + (p - 1)) % p, x.2)

/-- The norm `u² + P·u·v + v²` of `u + vX`, modulo `p`. -/
@[expose] def qnorm (p P : ℕ) (x : ℕ × ℕ) : ℕ :=
  (x.1 * x.1 + P * x.1 * x.2 + x.2 * x.2) % p

/-! ## The ring modulo a prime factor -/

/-- The quadratic `X² - P·X + 1` over `ZMod r`. -/
noncomputable def quadPoly (r P : ℕ) : (ZMod r)[X] := X ^ 2 - C (P : ZMod r) * X + 1

/-- The ring `(ZMod r)[X] / (X² - P·X + 1)`. -/
abbrev QuadRing (r P : ℕ) := AdjoinRoot (quadPoly r P)

/-- A pair, read in the ring. -/
noncomputable def toQuad (r P : ℕ) (x : ℕ × ℕ) : QuadRing r P :=
  (x.1 : QuadRing r P) + (x.2 : QuadRing r P) * AdjoinRoot.root (quadPoly r P)

theorem quadPoly_monic (r P : ℕ) [Fact r.Prime] : (quadPoly r P).Monic := by
  unfold quadPoly; monicity!

theorem quadPoly_natDegree (r P : ℕ) [Fact r.Prime] : (quadPoly r P).natDegree = 2 := by
  unfold quadPoly; compute_degree!

instance (r P : ℕ) [Fact r.Prime] : Nontrivial (QuadRing r P) :=
  AdjoinRoot.nontrivial _ (by
    rw [Polynomial.degree_eq_natDegree (quadPoly_monic r P).ne_zero, quadPoly_natDegree]
    decide)

/-- The root satisfies `X² = P·X - 1`. -/
theorem root_sq (r P : ℕ) :
    AdjoinRoot.root (quadPoly r P) ^ 2 =
      (P : QuadRing r P) * AdjoinRoot.root (quadPoly r P) - 1 := by
  have h : eval₂ (AdjoinRoot.of (quadPoly r P)) (AdjoinRoot.root (quadPoly r P))
      (X ^ 2 - C (P : ZMod r) * X + 1) = 0 := AdjoinRoot.eval₂_root (quadPoly r P)
  simp only [eval₂_add, eval₂_sub, eval₂_mul, eval₂_pow, eval₂_X, eval₂_C, eval₂_one] at h
  rw [map_natCast] at h
  linear_combination h

/-- A multiple of `p` vanishes in the ring when `r ∣ p`. -/
theorem natCast_mod (r P : ℕ) {p : ℕ} (hrp : r ∣ p) (a : ℕ) :
    ((a % p : ℕ) : QuadRing r P) = (a : QuadRing r P) := by
  have hp : (p : QuadRing r P) = 0 := by
    have : (p : ZMod r) = 0 := (ZMod.natCast_eq_zero_iff _ _).2 hrp
    rw [← map_natCast (AdjoinRoot.of (quadPoly r P)), this, map_zero]
  conv_rhs => rw [← Nat.mod_add_div a p]
  push_cast
  rw [hp]; ring

theorem toQuad_qmul (r P : ℕ) {p : ℕ} (hp : 1 ≤ p) (hrp : r ∣ p) (x y : ℕ × ℕ) :
    toQuad r P (qmul p P x y) = toQuad r P x * toQuad r P y := by
  have hp0 : (p : QuadRing r P) = 0 := by
    rw [← natCast_mod r P hrp p, Nat.mod_self, Nat.cast_zero]
  have h := root_sq r P
  simp only [toQuad, qmul, natCast_mod r P hrp]
  push_cast [Nat.cast_sub hp]
  rw [hp0]
  linear_combination (-(↑x.2 * ↑y.2) : QuadRing r P) * h

theorem toQuad_one (r P : ℕ) {p : ℕ} (hrp : r ∣ p) : toQuad r P (1 % p, 0) = 1 := by
  simp [toQuad, natCast_mod r P hrp]

theorem toQuad_qpowSlow (r P : ℕ) {p : ℕ} (hp : 1 ≤ p) (hrp : r ∣ p) (b : ℕ × ℕ) :
    ∀ e, toQuad r P (qpowSlow p P b e) = toQuad r P b ^ e := by
  intro e
  induction e with
  | zero => exact toQuad_one r P hrp
  | succ k ih => rw [qpowSlow, toQuad_qmul r P hp hrp, ih, pow_succ]

theorem toQuad_qpowF (r P : ℕ) {p : ℕ} (hp : 1 ≤ p) (hrp : r ∣ p) :
    ∀ fuel b e, toQuad r P (qpowF p P fuel b e) = toQuad r P b ^ e := by
  intro fuel
  induction fuel with
  | zero => intro b e; exact toQuad_qpowSlow r P hp hrp b e
  | succ k ih =>
    intro b e
    simp only [qpowF]
    split_ifs with h0 h2
    · subst h0; rw [pow_zero]; exact toQuad_one r P hrp
    · rw [ih, toQuad_qmul r P hp hrp, ← sq, ← pow_mul]
      congr 1; omega
    · rw [toQuad_qmul r P hp hrp, ih, toQuad_qmul r P hp hrp, ← sq, ← pow_mul, ← pow_succ]
      congr 1; omega

/-- The pair power is the power in the ring. -/
theorem toQuad_qpow (r P : ℕ) {p : ℕ} (hp : 1 ≤ p) (hrp : r ∣ p) (b : ℕ × ℕ) (e : ℕ) :
    toQuad r P (qpow p P b e) = toQuad r P b ^ e := toQuad_qpowF r P hp hrp e b e

theorem toQuad_qsubOne (r P : ℕ) {p : ℕ} (hp : 1 ≤ p) (hrp : r ∣ p) (x : ℕ × ℕ) :
    toQuad r P (qsubOne p x) = toQuad r P x - 1 := by
  have hp0 : (p : QuadRing r P) = 0 := by
    rw [← natCast_mod r P hrp p, Nat.mod_self, Nat.cast_zero]
  simp only [toQuad, qsubOne, natCast_mod r P hrp]
  push_cast [Nat.cast_sub hp]
  rw [hp0]; ring

/-- A pair whose norm is nonzero modulo `r` is a unit of the ring. -/
theorem isUnit_of_qnorm (r P : ℕ) [Fact r.Prime] {p : ℕ} (hrp : r ∣ p) (x : ℕ × ℕ)
    (hn : ((qnorm p P x : ℕ) : ZMod r) ≠ 0) : IsUnit (toQuad r P x) := by
  set ρ := AdjoinRoot.root (quadPoly r P)
  set N : ZMod r := ((qnorm p P x : ℕ) : ZMod r)
  have hN : (AdjoinRoot.of (quadPoly r P) N) = toQuad r P x *
      ((x.1 : QuadRing r P) + (P : QuadRing r P) * x.2 - x.2 * ρ) := by
    have h := root_sq r P
    simp only [N, map_natCast, qnorm, natCast_mod r P hrp, toQuad]
    push_cast
    linear_combination ((x.2 : QuadRing r P) * x.2) * h
  refine IsUnit.of_mul_eq_one (((x.1 : QuadRing r P) + (P : QuadRing r P) * (x.2 : QuadRing r P)
    - (x.2 : QuadRing r P) * ρ) *
    AdjoinRoot.of (quadPoly r P) N⁻¹) ?_
  rw [← mul_assoc, ← hN, ← map_mul, mul_inv_cancel₀ hn, map_one]

/-- The ring has `r²` elements. -/
theorem card_quadRing (r P : ℕ) [Fact r.Prime] : Nat.card (QuadRing r P) = r ^ 2 := by
  haveI : Module.Finite (ZMod r) (QuadRing r P) :=
    (AdjoinRoot.powerBasis' (quadPoly_monic r P)).finite
  rw [Module.natCard_eq_pow_finrank (K := ZMod r), Nat.card_zmod,
    (AdjoinRoot.powerBasis' (quadPoly_monic r P)).finrank, AdjoinRoot.powerBasis'_dim,
    quadPoly_natDegree]

instance (r P : ℕ) [Fact r.Prime] : Finite (QuadRing r P) :=
  Nat.finite_of_card_ne_zero (by rw [card_quadRing]; exact pow_ne_zero _ (Fact.out : r.Prime).ne_zero)

/-! ## The Lucas entry -/

/-- One Lucas (N+1) entry `(p, P, [(q, e), …])`, checked against the primes
`known` certified by earlier entries. -/
@[expose] def checkLEntry (known : List ℕ) (p P : ℕ) (fs : List (ℕ × ℕ)) : Bool :=
  decide (2 ≤ p) && ((fs.map fun qe => qe.1 ^ qe.2).prod == p + 1) &&
    fs.all (fun qe => decide (qe.1 ∈ known)) && (qpow p P (0, 1) (p + 1) == (1, 0)) &&
    fs.all (fun qe => Nat.gcd (qnorm p P (qsubOne p (qpow p P (0, 1) ((p + 1) / qe.1)))) p == 1)

/-- **The N+1 test.** An accepted Lucas entry is about a prime. -/
theorem lucas_prime {known : List ℕ} {p P : ℕ} {fs : List (ℕ × ℕ)}
    (hk : ∀ q ∈ known, q.Prime) (h : checkLEntry known p P fs = true) : p.Prime := by
  simp only [checkLEntry, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq,
    List.all_eq_true] at h
  obtain ⟨⟨⟨⟨hp2, hprod⟩, hknown⟩, hX⟩, hw⟩ := h
  have hfs : ∀ qe ∈ fs, qe.1.Prime := fun qe hqe => hk _ (hknown qe hqe)
  by_contra hnp
  have hr : p.minFac.Prime := Nat.minFac_prime (by omega)
  haveI := Fact.mk hr
  have hrp : p.minFac ∣ p := Nat.minFac_dvd p
  have hsq : p.minFac ^ 2 ≤ p := Nat.minFac_sq_le_self (by omega) hnp
  have hp1 : 1 ≤ p := by omega
  have hρ : toQuad p.minFac P (0, 1) = AdjoinRoot.root (quadPoly p.minFac P) := by
    simp [toQuad]
  have hpow : AdjoinRoot.root (quadPoly p.minFac P) ^ (p + 1) = 1 := by
    rw [← hρ, ← toQuad_qpow _ P hp1 hrp, hX]; simp [toQuad]
  have hunit : IsUnit (AdjoinRoot.root (quadPoly p.minFac P)) :=
    IsUnit.of_mul_eq_one ((P : QuadRing p.minFac P) - AdjoinRoot.root (quadPoly p.minFac P))
      (by linear_combination -(root_sq p.minFac P))
  have hne : ∀ q, q.Prime → q ∣ p + 1 →
      AdjoinRoot.root (quadPoly p.minFac P) ^ ((p + 1) / q) ≠ 1 := by
    intro q hq hqd
    obtain ⟨qe, hqe, rfl⟩ := prime_dvd_prod_pow hq fs hfs (by rw [hprod]; exact hqd)
    have hg := hw qe hqe
    have hn : ((qnorm p P (qsubOne p (qpow p P (0, 1) ((p + 1) / qe.1))) : ℕ) :
        ZMod p.minFac) ≠ 0 := by
      rw [Ne, ZMod.natCast_eq_zero_iff]
      intro hd
      have := Nat.dvd_gcd hd hrp
      rw [hg] at this
      exact hr.one_lt.ne' (Nat.dvd_one.1 this)
    have hu := isUnit_of_qnorm _ P hrp _ hn
    rw [toQuad_qsubOne _ P hp1 hrp, toQuad_qpow _ P hp1 hrp, hρ] at hu
    intro heq
    rw [heq, sub_self] at hu
    exact not_isUnit_zero hu
  have hord : orderOf hunit.unit = p + 1 := by
    apply orderOf_eq_of_pow_and_pow_div_prime (by omega)
    · ext; simp [hpow]
    · intro q hq hqd h1
      apply hne q hq hqd
      have := congrArg Units.val h1
      simpa using this
  have h1 : p + 1 ≤ Nat.card (QuadRing p.minFac P)ˣ := hord ▸ orderOf_le_card
  have h2 := natCard_units_lt (QuadRing p.minFac P)
  rw [card_quadRing] at h2
  omega

/-! ## Mixed chains -/

/-- An entry of a mixed chain: a Pocklington entry or a Lucas entry. -/
inductive Entry where
  | pock (p : ℕ) (fs : List (ℕ × ℕ × ℕ))
  | lucas (p P : ℕ) (fs : List (ℕ × ℕ))

/-- The number an entry is about. -/
@[expose] def Entry.num : Entry → ℕ
  | .pock p _ => p
  | .lucas p _ _ => p

/-- One entry, of either kind. -/
@[expose] def checkAnyEntry (known : List ℕ) : Entry → Bool
  | .pock p fs => checkPEntry known p fs
  | .lucas p P fs => checkLEntry known p P fs

/-- A mixed chain, each entry checked against the primes before it. -/
@[expose] def checkMChain : List ℕ → List Entry → Bool
  | _, [] => true
  | known, e :: rest => checkAnyEntry known e && checkMChain (e.num :: known) rest

/-- `c` certifies that `n` is prime. -/
@[expose] def certifiesM (n : ℕ) (c : List Entry) : Bool :=
  checkMChain [] c && c.any (fun e => e.num == n)

theorem checkAnyEntry_sound {known : List ℕ} {e : Entry}
    (hk : ∀ q ∈ known, q.Prime) (h : checkAnyEntry known e = true) : e.num.Prime := by
  cases e with
  | pock p fs => exact checkPEntry_sound hk h
  | lucas p P fs => exact lucas_prime hk h

/-- Every entry of an accepted mixed chain is about a prime. -/
theorem checkMChain_sound :
    ∀ (c : List Entry) (known : List ℕ), (∀ q ∈ known, q.Prime) →
      checkMChain known c = true → ∀ e ∈ c, e.num.Prime := by
  intro c
  induction c with
  | nil => intro _ _ _ e he; simp at he
  | cons hd rest ih =>
    intro known hk h
    simp only [checkMChain, Bool.and_eq_true] at h
    have hp := checkAnyEntry_sound hk h.1
    have hrest := ih (hd.num :: known) (by
      intro q hq
      rcases List.mem_cons.1 hq with rfl | hq
      · exact hp
      · exact hk q hq) h.2
    intro e he
    rcases List.mem_cons.1 he with rfl | he
    · exact hp
    · exact hrest e he

/-- **The check the tool runs**: an accepted mixed certificate for `n` shows
that `n` is prime. -/
theorem mixed_sound {n : ℕ} {c : List Entry} (h : certifiesM n c = true) : n.Prime := by
  simp only [certifiesM, Bool.and_eq_true, List.any_eq_true, beq_iff_eq] at h
  obtain ⟨hc, e, he, rfl⟩ := h
  exact checkMChain_sound c [] (by simp) hc e he

/-! ## An instance the first held-out set left refused -/

/-- The mixed certificate `glm_universal.reasoning.primality_certificate
.certify` produces for `33! - 1`, copied verbatim: eleven Pocklington entries
for the primes up to 31 and one N+1 entry, since `33!` splits into them. -/
def cert_33_factorial : List Entry :=
  [.pock 2 [],
    .pock 3 [],
    .pock 5 [(2, 2, 2)],
    .pock 7 [(2, 1, 3)],
    .pock 11 [(2, 1, 2), (5, 1, 2)],
    .pock 13 [(2, 2, 2)],
    .pock 17 [(2, 4, 3)],
    .pock 19 [(2, 1, 2), (3, 2, 2)],
    .pock 23 [(2, 1, 5), (11, 1, 2)],
    .pock 29 [(2, 2, 2), (7, 1, 2)],
    .pock 31 [(2, 1, 3), (3, 1, 3)],
    .lucas 8683317618811886495518194401279999999 71 [(2, 31), (3, 15), (5, 7), (7, 4), (11, 3), (13, 2), (17, 1), (19, 1), (23, 1), (29, 1), (31, 1)]]

/-- `33! - 1` is prime (OEIS A002982): the mixed certificate the run-time
tool produced, checked by the kernel. Neither the Pratt nor the Pocklington
search reached it within the work budget. -/
theorem prime_33_factorial_sub_one : Nat.Prime (Nat.factorial 33 - 1) :=
  mixed_sound (c := cert_33_factorial) (by decide +kernel)

end GLM.PrimalityCertificate
