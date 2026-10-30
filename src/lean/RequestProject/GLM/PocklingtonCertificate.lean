module

public import RequestProject.GLM.PrimalityCertificate

/-!
# Pocklington certificates: primality from a partial factorisation of `p - 1`

The formal half of `studies/POCKLINGTON_CERTIFICATE_STUDY.md` (Phase 140).
Phase 139's Pratt certificates need the *whole* of `p - 1` factored, so a prime
such as `2^521 - 1`, whose `p - 1` does not split within the work budget, was
refused (`NO_CERTIFICATE`). Pocklington's theorem needs only a factored part
`F` of `p - 1` a little larger than `√p`.

**The entry.** An entry `(p, [(q₁, e₁, a₁), …])` claims `p` prime. With
`F = ∏ qᵢ ^ eᵢ` it is accepted (`checkPEntry`) when

* `p ≥ 2`, `F ∣ p - 1` and `p < (F + 1)²`;
* the `qᵢ` are pairwise distinct and each was certified by an earlier entry;
* for every `i`: `aᵢ ^ (p - 1) ≡ 1 (mod p)` and
  `gcd(aᵢ ^ ((p - 1) / qᵢ) - 1, p) = 1` (computed as
  `gcd((aᵢ ^ ((p - 1) / qᵢ) mod p + p - 1) mod p, p)`).

**The theorems.**

* `prime_pow_dvd_of_witness` — for every prime `r ∣ p` and every factor
  `(q, e, a)` that passes, `q ^ e ∣ r - 1` (the order of
  `a ^ ((p - 1) / q ^ e)` modulo `r` is exactly `q ^ e`);
* `prod_dvd_of_pow_dvd` — distinct primes: the prime powers' product divides
  whatever each divides;
* `prime_of_factor_bound` — if every prime factor `r` of `p` has `F ∣ r - 1`
  and `p < (F + 1)²`, then `p` is prime;
* `checkPEntry_sound`, `checkPChain_sound` and `pocklington_sound` — **the
  check the tool runs**: if `certifiesP n c = true` then `n` is prime.

A Pratt entry `(p, a, [(q, e)])` is the special case `F = p - 1` with one base
for every `q`, so the Pocklington chain subsumes the Pratt chain; the run-time
tool still emits Pratt certificates when `p - 1` splits completely and falls
back on Pocklington only when it does not.

A worked instance, checked by the kernel: `prime_2_521_sub_one`, the
Mersenne prime `2^521 - 1` that Phase 139 refused, proved prime by the
certificate the run-time tool produces.
-/

public section

namespace GLM.PrimalityCertificate

/-! ## The entry and the chain -/

/-- The factored part `F = ∏ q ^ e` of an entry. -/
@[expose] def factoredPart (fs : List (ℕ × ℕ × ℕ)) : ℕ := (fs.map fun t => t.1 ^ t.2.1).prod

/-- The Pocklington condition for one factor `(q, e, a)` of an entry about `p`:
`a ^ (p - 1) ≡ 1` and `gcd(a ^ ((p - 1) / q) - 1, p) = 1`. -/
@[expose] def witnessOK (p : ℕ) (t : ℕ × ℕ × ℕ) : Bool :=
  (powMod p t.2.2 (p - 1) == 1) &&
    (Nat.gcd ((powMod p t.2.2 ((p - 1) / t.1) + (p - 1)) % p) p == 1)

/-- One Pocklington entry `(p, [(q, e, a), …])`, checked against the list
`known` of primes certified by earlier entries. -/
@[expose] def checkPEntry (known : List ℕ) (p : ℕ) (fs : List (ℕ × ℕ × ℕ)) : Bool :=
  decide (2 ≤ p) && ((p - 1) % factoredPart fs == 0) &&
    decide (p < (factoredPart fs + 1) * (factoredPart fs + 1)) &&
    decide (fs.map (·.1)).Nodup && fs.all (fun t => decide (t.1 ∈ known)) &&
    fs.all (witnessOK p)

/-- A list of Pocklington entries, each checked against the primes the entries
before it certified. -/
@[expose] def checkPChain : List ℕ → List (ℕ × List (ℕ × ℕ × ℕ)) → Bool
  | _, [] => true
  | known, (p, fs) :: rest => checkPEntry known p fs && checkPChain (p :: known) rest

/-- `c` certifies that `n` is prime: the chain is accepted and one of its
entries is about `n`. -/
@[expose] def certifiesP (n : ℕ) (c : List (ℕ × List (ℕ × ℕ × ℕ))) : Bool :=
  checkPChain [] c && c.any (fun e => e.1 == n)

/-! ## One factor: `q ^ e` divides `r - 1` -/

/-- **One factor.** If `(q, e, a)` passes for `p`, `q` is prime and
`q ^ e ∣ p - 1`, then `q ^ e ∣ r - 1` for every prime `r` dividing `p`. -/
theorem prime_pow_dvd_of_witness {p r q e a : ℕ} (hp : 2 ≤ p) (hr : r.Prime) (hrp : r ∣ p)
    (hq : q.Prime) (hqe : q ^ e ∣ p - 1) (hw : witnessOK p (q, e, a) = true) :
    q ^ e ∣ r - 1 := by
  haveI := Fact.mk hr
  haveI := Fact.mk hq
  simp only [witnessOK, Bool.and_eq_true, beq_iff_eq] at hw
  obtain ⟨hf, hg⟩ := hw
  rw [powMod_eq] at hf hg
  have hp1 : 1 < p := hp
  -- Fermat's condition, read modulo `r`.
  have hx : (a : ZMod r) ^ (p - 1) = 1 := by
    have : ((a ^ (p - 1) : ℕ) : ZMod r) = ((1 : ℕ) : ZMod r) := by
      rw [ZMod.natCast_eq_natCast_iff', ← Nat.mod_mod_of_dvd _ hrp, hf]
    push_cast at this; exact this
  -- The gcd condition, read modulo `r`.
  have hy : (a : ZMod r) ^ ((p - 1) / q) ≠ 1 := by
    intro heq
    have h1 : ((a ^ ((p - 1) / q) % p : ℕ) : ZMod r) = 1 := by
      rw [(ZMod.natCast_eq_natCast_iff' _ _ _).mpr (Nat.mod_mod_of_dvd _ hrp)]
      push_cast; exact heq
    have hp0 : (p : ZMod r) = 0 := (ZMod.natCast_eq_zero_iff _ _).2 hrp
    have h2 : (((a ^ ((p - 1) / q) % p + (p - 1)) % p : ℕ) : ZMod r) = 0 := by
      rw [(ZMod.natCast_eq_natCast_iff' _ _ _).mpr (Nat.mod_mod_of_dvd _ hrp)]
      push_cast [Nat.cast_sub hp1.le]
      rw [h1, hp0]; ring
    rw [ZMod.natCast_eq_zero_iff] at h2
    have := Nat.dvd_gcd h2 hrp
    rw [hg] at this
    exact hr.one_lt.ne' (Nat.dvd_one.1 this)
  rcases Nat.eq_zero_or_pos e with rfl | he
  · simp
  obtain ⟨k, rfl⟩ : ∃ k, e = k + 1 := ⟨e - 1, by omega⟩
  obtain ⟨m, hm⟩ := hqe
  set b : ZMod r := (a : ZMod r) ^ m with hb
  have hfin : b ^ q ^ (k + 1) = 1 := by
    rw [hb, ← pow_mul, mul_comm, ← hm]; exact hx
  have hnot : ¬ b ^ q ^ k = 1 := by
    rw [hb, ← pow_mul]
    have : m * q ^ k = (p - 1) / q := by
      rw [hm, pow_succ, show q ^ k * q * m = q * (m * q ^ k) by ring,
        Nat.mul_div_cancel_left _ hq.pos]
    rw [this]; exact hy
  have hord := orderOf_eq_prime_pow hnot hfin
  have hb0 : b ≠ 0 := by
    intro h0
    rw [h0, zero_pow (pow_pos hq.pos _).ne'] at hfin
    exact zero_ne_one hfin
  rw [← hord]
  exact ZMod.orderOf_dvd_card_sub_one hb0

/-- **Distinct primes.** If the `q` of the factors are distinct primes and
every `q ^ e` divides `m`, then so does their product. -/
theorem prod_dvd_of_pow_dvd {m : ℕ} :
    ∀ fs : List (ℕ × ℕ × ℕ), (fs.map (·.1)).Nodup → (∀ t ∈ fs, t.1.Prime) →
      (∀ t ∈ fs, t.1 ^ t.2.1 ∣ m) → factoredPart fs ∣ m := by
  intro fs
  induction fs with
  | nil => intros; simp [factoredPart]
  | cons t rest ih =>
    intro hnd hpr hdv
    simp only [List.map_cons, List.nodup_cons] at hnd
    have hrest : factoredPart rest ∣ m :=
      ih hnd.2 (fun x hx => hpr x (by simp [hx])) (fun x hx => hdv x (by simp [hx]))
    have ht : t.1 ^ t.2.1 ∣ m := hdv t (by simp)
    have hcop : Nat.Coprime (t.1 ^ t.2.1) (factoredPart rest) := by
      unfold factoredPart
      rw [Nat.coprime_list_prod_right_iff]
      intro n hn
      obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hn
      apply Nat.Coprime.pow
      rw [Nat.coprime_primes (hpr t (by simp)) (hpr x (by simp [hx]))]
      intro heq
      exact hnd.1 (heq ▸ List.mem_map_of_mem hx)
    simp only [factoredPart, List.map_cons, List.prod_cons]
    exact hcop.mul_dvd_of_dvd_of_dvd ht hrest

/-- **The size bound.** If every prime factor `r` of `p ≥ 2` satisfies
`F ∣ r - 1` and `p < (F + 1)²`, then `p` is prime. -/
theorem prime_of_factor_bound {p F : ℕ} (hp : 2 ≤ p)
    (hF : ∀ r, r.Prime → r ∣ p → F ∣ r - 1) (hb : p < (F + 1) * (F + 1)) :
    p.Prime := by
  by_contra hnp
  have hr := Nat.minFac_prime (show p ≠ 1 by omega)
  have hsq := Nat.minFac_sq_le_self (by omega) hnp
  have hr2 := hr.two_le
  have hle : F ≤ p.minFac - 1 := Nat.le_of_dvd (by omega) (hF _ hr (Nat.minFac_dvd p))
  have : (F + 1) * (F + 1) ≤ p.minFac ^ 2 := by
    rw [sq]; exact Nat.mul_le_mul (by omega) (by omega)
  omega

/-! ## Soundness of the chain -/

/-- An accepted Pocklington entry is about a prime. -/
theorem checkPEntry_sound {known : List ℕ} {p : ℕ} {fs : List (ℕ × ℕ × ℕ)}
    (hk : ∀ q ∈ known, q.Prime) (h : checkPEntry known p fs = true) : p.Prime := by
  simp only [checkPEntry, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq,
    List.all_eq_true] at h
  obtain ⟨⟨⟨⟨⟨hp2, hF⟩, hb⟩, hnd⟩, hknown⟩, hw⟩ := h
  have hpr : ∀ t ∈ fs, t.1.Prime := fun t ht => hk _ (hknown t ht)
  have hFd : factoredPart fs ∣ p - 1 := Nat.dvd_of_mod_eq_zero hF
  refine prime_of_factor_bound hp2 (fun r hr hrp => ?_) hb
  refine prod_dvd_of_pow_dvd fs hnd hpr (fun t ht => ?_)
  obtain ⟨q, e, a⟩ := t
  exact prime_pow_dvd_of_witness hp2 hr hrp (hpr _ ht)
    (dvd_trans (List.dvd_prod (List.mem_map_of_mem (f := fun t : ℕ × ℕ × ℕ => t.1 ^ t.2.1) ht))
      hFd) (hw _ ht)

/-- Every entry of an accepted Pocklington chain is about a prime. -/
theorem checkPChain_sound :
    ∀ (c : List (ℕ × List (ℕ × ℕ × ℕ))) (known : List ℕ), (∀ q ∈ known, q.Prime) →
      checkPChain known c = true → ∀ e ∈ c, e.1.Prime := by
  intro c
  induction c with
  | nil => intro _ _ _ e he; simp at he
  | cons hd rest ih =>
    obtain ⟨p, fs⟩ := hd
    intro known hk h
    simp only [checkPChain, Bool.and_eq_true] at h
    have hp := checkPEntry_sound hk h.1
    have hrest := ih (p :: known) (by
      intro q hq
      rcases List.mem_cons.1 hq with rfl | hq
      · exact hp
      · exact hk q hq) h.2
    intro e he
    rcases List.mem_cons.1 he with rfl | he
    · exact hp
    · exact hrest e he

/-- **The check the tool runs**: an accepted Pocklington certificate for `n`
shows that `n` is prime. -/
theorem pocklington_sound {n : ℕ} {c : List (ℕ × List (ℕ × ℕ × ℕ))}
    (h : certifiesP n c = true) : n.Prime := by
  simp only [certifiesP, Bool.and_eq_true, List.any_eq_true, beq_iff_eq] at h
  obtain ⟨hc, e, he, rfl⟩ := h
  exact checkPChain_sound c [] (by simp) hc e he

/-! ## An instance the Pratt search could not reach -/

/-- The Pocklington certificate `glm_universal.reasoning.primality_certificate
.certify` produces for `2^521 - 1`, copied verbatim. Its last entry uses only
the part of `2^520 - 1` the work budget split. -/
def cert_2_521 : List (ℕ × List (ℕ × ℕ × ℕ)) :=
  [(2, []),
    (3, []),
    (5, [(2, 2, 2)]),
    (11, [(2, 1, 2), (5, 1, 2)]),
    (17, [(2, 4, 3)]),
    (31, [(2, 1, 3), (3, 1, 3)]),
    (41, [(2, 3, 3)]),
    (13, [(2, 2, 2)]),
    (53, [(2, 2, 2), (13, 1, 2)]),
    (131, [(2, 1, 2), (5, 1, 2), (13, 1, 2)]),
    (157, [(2, 2, 2), (3, 1, 3)]),
    (521, [(2, 3, 3), (5, 1, 2)]),
    (1613, [(2, 2, 2), (13, 1, 2)]),
    (7, [(2, 1, 3)]),
    (2731, [(2, 1, 2), (3, 1, 3), (5, 1, 3), (7, 1, 3)]),
    (8191, [(2, 1, 3), (3, 2, 7), (5, 1, 3)]),
    (42641, [(2, 4, 3), (5, 1, 2), (13, 1, 2)]),
    (51481, [(2, 3, 7), (3, 2, 3), (5, 1, 2)]),
    (257, [(2, 8, 3)]),
    (61681, [(2, 4, 17), (3, 1, 3), (5, 1, 2), (257, 1, 3)]),
    (1051, [(2, 1, 2), (3, 1, 3), (5, 2, 2)]),
    (409891, [(2, 1, 2), (3, 1, 7), (5, 1, 2), (13, 1, 2), (1051, 1, 3)]),
    (858001, [(2, 4, 17), (3, 1, 5), (5, 3, 3)]),
    (5746001, [(2, 4, 3), (5, 3, 5), (13, 2, 3)]),
    (37, [(2, 2, 2), (3, 2, 2)]),
    (7623851, [(2, 1, 2), (5, 2, 3), (13, 1, 2), (37, 1, 3)]),
    (19, [(2, 1, 2), (3, 2, 2)]),
    (34110701, [(2, 2, 2), (5, 2, 5), (13, 1, 2), (19, 1, 3)]),
    (103, [(2, 1, 3), (3, 1, 2), (17, 1, 2)]),
    (1237, [(2, 2, 2), (3, 1, 2), (103, 1, 2)]),
    (49481, [(2, 3, 3), (5, 1, 2), (1237, 1, 2)]),
    (308761441, [(2, 5, 11), (3, 1, 3), (5, 1, 3), (13, 1, 2), (49481, 1, 3)]),
    (6864797660130609714981900799081393217269435300143305409394463459185543183397656052122559640661454554977296311391480858037121987999716643812574028291115057151, [(2, 1, 3), (3, 1, 3), (5, 2, 3), (11, 1, 3), (17, 1, 3), (31, 1, 3), (41, 1, 3), (53, 1, 3), (131, 1, 3), (157, 1, 3), (521, 1, 2), (1613, 1, 3), (2731, 1, 3), (8191, 1, 3), (42641, 1, 3), (51481, 1, 3), (61681, 1, 3), (409891, 1, 3), (858001, 1, 3), (5746001, 1, 3), (7623851, 1, 3), (34110701, 1, 3), (308761441, 1, 3)])]

/-- `2^521 - 1` is prime: the Pocklington certificate the run-time tool
produced, checked by the kernel. Phase 139's Pratt search refused it. -/
theorem prime_2_521_sub_one : Nat.Prime (2 ^ 521 - 1) :=
  pocklington_sound (c := cert_2_521) (by decide +kernel)

end GLM.PrimalityCertificate
