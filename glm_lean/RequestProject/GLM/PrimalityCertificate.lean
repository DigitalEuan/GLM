module

public import Mathlib

/-!
# Primality certificates: the primality step without a ceiling

The formal half of `studies/PRIMALITY_CERTIFICATE_STUDY.md` (Phase 139). Until
Phase 138 the stepwise planner's `prime` step decided primality by trial
division and refused every number above `10^12`, because trial division there
costs a million divisions per check and the step is re-checked twice (the step
gate and the chain's column-3 script). This file proves the checks that replace
trial division above that line, so the ceiling goes. Each check costs a few
modular exponentiations, whatever the size of the number.

**Modular exponentiation.** `powMod m b e` is square-and-multiply with fuel;
`powMod_eq` proves it equals `b ^ e % m` for every input (when the fuel runs
out the fallback is the definition itself, so no precondition is needed).

**Not prime.**

* `factor_witness` — a divisor `f` with `1 < f < n` shows `n` is not prime;
* `fermat_witness` — a base `a` with `1 ≤ a < n` and `a ^ (n - 1) % n ≠ 1`
  shows `n` is not prime (Fermat's little theorem), with no factor named.

**Prime (Pratt certificates).** A certificate is a list of entries
`(p, a, [(q₁, e₁), …])`, each claiming `p` prime with witness `a`. An entry is
accepted (`checkEntry`) when `p ≥ 2`, `∏ qᵢ ^ eᵢ = p - 1`, every `qᵢ` was
certified by an *earlier* entry, `a ^ (p - 1) % p = 1`, and
`a ^ ((p - 1) / qᵢ) % p ≠ 1` for every `i`.

* `checkEntry_sound` — an accepted entry's `p` is prime (Lucas's converse of
  Fermat, Mathlib's `lucas_primality`);
* `checkChain_sound` — every entry of an accepted list is prime;
* `pratt_sound` — **the check the tool runs**: if `certifies n c = true`, then
  `n` is prime.

The certificate is flat (no nested inductive), so the run-time checker in
`glm_universal/reasoning/primality_certificate.py` and the column-3 script
mirror `checkEntry` and `checkChain` line for line.

Two worked instances above the old ceiling are checked by the kernel:
`prime_10_12_39` (`10^12 + 39` is prime) and `not_prime_10_12_1`
(`10^12 + 1` is not, by a Fermat witness with no factor named).
-/

public section

namespace GLM.PrimalityCertificate

/-! ## Modular exponentiation -/

/-- Square-and-multiply modular exponentiation with fuel. When the fuel is
exhausted it falls back on the definition, so it is exact for every fuel. -/
@[expose] def powModF (m : ℕ) : ℕ → ℕ → ℕ → ℕ
  | 0, b, e => b ^ e % m
  | fuel + 1, b, e =>
    if e = 0 then 1 % m
    else
      let r := powModF m fuel (b * b % m) (e / 2)
      if e % 2 = 0 then r else r * b % m

/-- `b ^ e % m`, computed by square-and-multiply. -/
@[expose] def powMod (m b e : ℕ) : ℕ := powModF m e b e

theorem powModF_eq (m : ℕ) : ∀ fuel b e, powModF m fuel b e = b ^ e % m := by
  intro fuel
  induction fuel with
  | zero => intro b e; rfl
  | succ k ih =>
    intro b e
    simp only [powModF]
    split_ifs with h0 h2
    · subst h0; simp
    · rw [ih, ← Nat.pow_mod, ← sq, ← pow_mul]
      congr 2
      omega
    · rw [ih, ← Nat.pow_mod, Nat.mod_mul_mod, ← sq, ← pow_mul, ← pow_succ]
      congr 2
      omega

/-- `powMod` is modular exponentiation. -/
theorem powMod_eq (m b e : ℕ) : powMod m b e = b ^ e % m := powModF_eq m e b e

/-! ## Not prime -/

/-- A proper divisor shows a number is not prime. -/
theorem factor_witness {n f : ℕ} (h1 : 1 < f) (h2 : f < n) (hd : n % f = 0) :
    ¬ n.Prime := by
  intro hp
  rcases hp.eq_one_or_self_of_dvd f (Nat.dvd_of_mod_eq_zero hd) with h | h <;> omega

/-- A Fermat witness shows a number is not prime, without naming a factor. -/
theorem fermat_witness {n a : ℕ} (h1 : 1 ≤ a) (h2 : a < n)
    (hw : powMod n a (n - 1) ≠ 1) : ¬ n.Prime := by
  intro hp
  haveI := Fact.mk hp
  apply hw
  rw [powMod_eq]
  have ha : (a : ZMod n) ≠ 0 := by
    rw [Ne, ZMod.natCast_eq_zero_iff]
    intro hd
    exact absurd (Nat.le_of_dvd (by omega) hd) (by omega)
  have key := ZMod.pow_card_sub_one_eq_one ha
  have : ((a ^ (n - 1) : ℕ) : ZMod n) = ((1 : ℕ) : ZMod n) := by
    push_cast; exact key
  rw [ZMod.natCast_eq_natCast_iff'] at this
  rw [this, Nat.mod_eq_of_lt hp.one_lt]

/-! ## Prime: Pratt certificates -/

/-- One entry `(p, a, [(q, e), …])` of a Pratt certificate, checked against the
list `known` of primes certified by earlier entries. -/
def checkEntry (known : List ℕ) (p a : ℕ) (fs : List (ℕ × ℕ)) : Bool :=
  decide (2 ≤ p) && ((fs.map fun qe => qe.1 ^ qe.2).prod == p - 1) &&
    fs.all (fun qe => decide (qe.1 ∈ known)) && (powMod p a (p - 1) == 1) &&
    fs.all (fun qe => powMod p a ((p - 1) / qe.1) != 1)

/-- A list of entries, each checked against the primes the entries before it
certified. -/
def checkChain : List ℕ → List (ℕ × ℕ × List (ℕ × ℕ)) → Bool
  | _, [] => true
  | known, (p, a, fs) :: rest => checkEntry known p a fs && checkChain (p :: known) rest

/-- `c` certifies that `n` is prime: the chain is accepted and one of its
entries is about `n`. -/
def certifies (n : ℕ) (c : List (ℕ × ℕ × List (ℕ × ℕ))) : Bool :=
  checkChain [] c && c.any (fun e => e.1 == n)

/-- A prime dividing a product of prime powers is one of the primes. -/
theorem prime_dvd_prod_pow {r : ℕ} (hr : r.Prime) :
    ∀ fs : List (ℕ × ℕ), (∀ qe ∈ fs, qe.1.Prime) →
      r ∣ (fs.map fun qe => qe.1 ^ qe.2).prod → ∃ qe ∈ fs, qe.1 = r := by
  intro fs
  induction fs with
  | nil => intro _ h; simp at h; exact absurd h hr.one_lt.ne'
  | cons qe rest ih =>
    intro hfs h
    simp only [List.map_cons, List.prod_cons] at h
    rcases (Nat.Prime.dvd_mul hr).1 h with h | h
    · have hq := hfs qe (by simp)
      have := (Nat.prime_dvd_prime_iff_eq hr hq).1 (hr.dvd_of_dvd_pow h)
      exact ⟨qe, by simp, this.symm⟩
    · obtain ⟨x, hx, hx'⟩ := ih (fun x hx => hfs x (by simp [hx])) h
      exact ⟨x, by simp [hx], hx'⟩

/-- An accepted entry is about a prime (Lucas's theorem). -/
theorem checkEntry_sound {known : List ℕ} {p a : ℕ} {fs : List (ℕ × ℕ)}
    (hk : ∀ q ∈ known, q.Prime) (h : checkEntry known p a fs = true) : p.Prime := by
  simp only [checkEntry, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq,
    List.all_eq_true, bne_iff_ne, ne_eq] at h
  obtain ⟨⟨⟨⟨hp2, hprod⟩, hknown⟩, hfermat⟩, hlucas⟩ := h
  have hfs : ∀ qe ∈ fs, qe.1.Prime := fun qe hqe => hk _ (hknown qe hqe)
  apply lucas_primality p (a : ZMod p)
  · rw [powMod_eq] at hfermat
    have : ((a ^ (p - 1) : ℕ) : ZMod p) = ((1 : ℕ) : ZMod p) := by
      rw [ZMod.natCast_eq_natCast_iff', hfermat, Nat.mod_eq_of_lt (by omega)]
    push_cast at this; exact this
  · intro q hq hqd
    obtain ⟨qe, hqe, rfl⟩ := prime_dvd_prod_pow hq fs hfs (hprod ▸ hqd)
    have hne := hlucas qe hqe
    rw [powMod_eq] at hne
    intro heq
    apply hne
    have : ((a ^ ((p - 1) / qe.1) : ℕ) : ZMod p) = ((1 : ℕ) : ZMod p) := by
      push_cast; exact heq
    rw [ZMod.natCast_eq_natCast_iff', Nat.mod_eq_of_lt (by omega : 1 < p)] at this
    exact this

/-- Every entry of an accepted chain is about a prime. -/
theorem checkChain_sound :
    ∀ (c : List (ℕ × ℕ × List (ℕ × ℕ))) (known : List ℕ), (∀ q ∈ known, q.Prime) →
      checkChain known c = true → ∀ e ∈ c, e.1.Prime := by
  intro c
  induction c with
  | nil => intro _ _ _ e he; simp at he
  | cons hd rest ih =>
    obtain ⟨p, a, fs⟩ := hd
    intro known hk h
    simp only [checkChain, Bool.and_eq_true] at h
    have hp := checkEntry_sound hk h.1
    have hrest := ih (p :: known) (by
      intro q hq
      rcases List.mem_cons.1 hq with rfl | hq
      · exact hp
      · exact hk q hq) h.2
    intro e he
    rcases List.mem_cons.1 he with rfl | he
    · exact hp
    · exact hrest e he

/-- **The check the tool runs**: an accepted Pratt certificate for `n` shows
that `n` is prime. -/
theorem pratt_sound {n : ℕ} {c : List (ℕ × ℕ × List (ℕ × ℕ))}
    (h : certifies n c = true) : n.Prime := by
  simp only [certifies, Bool.and_eq_true, List.any_eq_true, beq_iff_eq] at h
  obtain ⟨hc, e, he, rfl⟩ := h
  exact checkChain_sound c [] (by simp) hc e he

/-! ## Two instances above the old ceiling -/

/-- The Pratt certificate `glm_universal.reasoning.primality_certificate.certify`
produces for `10^12 + 39`, copied verbatim. -/
def cert_10_12_39 : List (ℕ × ℕ × List (ℕ × ℕ)) :=
  [(2, 1, []),
    (3, 2, [(2, 1)]),
    (13, 2, [(2, 2), (3, 1)]),
    (17, 3, [(2, 4)]),
    (7, 3, [(2, 1), (3, 1)]),
    (29, 2, [(2, 2), (7, 1)]),
    (5, 2, [(2, 2)]),
    (31, 3, [(2, 1), (3, 1), (5, 1)]),
    (3907, 2, [(2, 1), (3, 2), (7, 1), (31, 1)]),
    (250049, 3, [(2, 6), (3907, 1)]),
    (26005097, 5, [(2, 3), (13, 1), (250049, 1)]),
    (1000000000039, 3, [(2, 1), (3, 1), (13, 1), (17, 1), (29, 1), (26005097, 1)])]

/-- `10^12 + 39 = 1000000000039` is prime: a Pratt certificate the run-time
tool produced, checked by the kernel. -/
theorem prime_10_12_39 : Nat.Prime 1000000000039 :=
  pratt_sound (c := cert_10_12_39) (by decide +kernel)

/-- `10^12 + 1` is not prime: the base `2` is a Fermat witness. -/
theorem not_prime_10_12_1 : ¬ Nat.Prime 1000000000001 :=
  fermat_witness (a := 2) (by norm_num) (by norm_num) (by decide +kernel)

end GLM.PrimalityCertificate
