module

public import RequestProject.GLM.Rule30.ElementaryCA

/-!
# Inducing a wheel from demonstrations: exactly when the next row is determined

Round 10.  The GLM solves ARC-style tasks by fitting a rule to demonstration pairs and
answering only when every rule that fits agrees on the query; otherwise it refuses.  For the
wheels this discipline can be proved sound and complete.

A run of wheel `r` from row `x` shows, at row `t` and cell `c`, the neighbourhood
`nbhd r x t c = (L, C, R)` and the output `ecaRule r L C R` one row later.  A demonstration of
rows `0..T` shows the outputs on exactly the neighbourhoods that occur in rows `0..T-1`.

* `rows_agree_iff` : a wheel `s` reproduces rows `0..T` of the run of `r` **iff** `s` and `r`
  agree on every neighbourhood that occurs in rows `0..T-1`.  The demonstrations fix the seen
  part of the truth table and nothing else.
* `ecaRule_flip` : flipping bit `k` of a wheel number changes its rule on exactly one
  neighbourhood.
* `next_row_determined_iff` : **every wheel that reproduces rows `0..T` also produces the same
  row `T+1` iff every neighbourhood of row `T` already occurred in rows `0..T-1`.**  If one has
  not, flipping that one entry of the table gives a wheel that fits all the demonstrations and
  predicts a different row.  So "answer only if all survivors agree" is the same as "answer only
  if the query's neighbourhoods were all seen".

`Observer.lean` applies this to Rule 30 from the impulse: rows `0..3` leave `{30, 62}`, and rows
`0..4` determine 30.
-/

@[expose] public section

namespace GLM.Rule30

/-- The neighbourhood `(L, C, R)` at cell `c` of row `t` of the run of wheel `r` from `x`. -/
def nbhd (r : ℕ) (x : Config) (t : ℕ) (c : ℤ) : Bool × Bool × Bool :=
  (ecaEvolve r x t (c - 1), ecaEvolve r x t c, ecaEvolve r x t (c + 1))

/-- The rule of wheel `r` applied to a neighbourhood triple. -/
def ecaRule3 (r : ℕ) (n : Bool × Bool × Bool) : Bool := ecaRule r n.1 n.2.1 n.2.2

theorem ecaEvolve_succ_nbhd (r : ℕ) (x : Config) (t : ℕ) (c : ℤ) :
    ecaEvolve r x (t + 1) c = ecaRule3 r (nbhd r x t c) := by
  rw [ecaEvolve_succ]; rfl

/-- **The demonstrations fix exactly the seen part of the table.**  A wheel `s` reproduces rows
`0..T` of the run of `r` iff it agrees with `r` on every neighbourhood occurring in rows
`0..T-1`. -/
theorem rows_agree_iff (r s : ℕ) (x : Config) (T : ℕ) :
    (∀ t ≤ T, ecaEvolve s x t = ecaEvolve r x t) ↔
      ∀ t < T, ∀ c, ecaRule3 s (nbhd r x t c) = ecaRule3 r (nbhd r x t c) := by
  constructor
  · intro h t ht c
    have h1 := congrFun (h (t + 1) ht) c
    have h0 := h t ht.le
    rw [ecaEvolve_succ_nbhd, ecaEvolve_succ_nbhd] at h1
    have : nbhd s x t c = nbhd r x t c := by simp [nbhd, h0]
    rwa [this] at h1
  · intro h t ht
    induction t with
    | zero => rfl
    | succ t ih =>
      have h0 := ih (by omega)
      funext c
      rw [ecaEvolve_succ_nbhd, ecaEvolve_succ_nbhd]
      have : nbhd s x t c = nbhd r x t c := by simp [nbhd, h0]
      rw [this]
      exact h t (by omega) c

/-- The table index of a neighbourhood. -/
def nbhdIndex (n : Bool × Bool × Bool) : ℕ := 4 * n.1.toNat + 2 * n.2.1.toNat + n.2.2.toNat

theorem nbhdIndex_inj {n m : Bool × Bool × Bool} (h : nbhdIndex n = nbhdIndex m) : n = m := by
  obtain ⟨a, b, c⟩ := n
  obtain ⟨d, e, f⟩ := m
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;>
    simp_all [nbhdIndex]

/-- **Flipping one table entry.**  Wheel `r ^^^ 2^k` has the rule of `r` with the output on the
neighbourhood of index `k` flipped, and only there. -/
theorem ecaRule_flip (r : ℕ) (n m : Bool × Bool × Bool) :
    ecaRule3 (r ^^^ 2 ^ nbhdIndex n) m = xor (ecaRule3 r m) (decide (m = n)) := by
  simp only [ecaRule3, ecaRule, Nat.testBit_xor, Nat.testBit_two_pow]
  congr 1
  by_cases h : m = n
  · subst h; simp [nbhdIndex]
  · have hne : nbhdIndex n ≠ 4 * m.1.toNat + 2 * m.2.1.toNat + m.2.2.toNat :=
      fun e => h (nbhdIndex_inj e).symm
    simp [hne, h]

/-- **When the next row is determined.**  Every wheel that reproduces rows `0..T` of the run
of `r` also reproduces row `T+1` iff every neighbourhood of row `T` already occurred in rows
`0..T-1`.  (Wheel numbers range over all of `ℕ`; only bits `0..7` matter.) -/
theorem next_row_determined_iff (r : ℕ) (x : Config) (T : ℕ) :
    (∀ s : ℕ, (∀ t ≤ T, ecaEvolve s x t = ecaEvolve r x t) →
        ecaEvolve s x (T + 1) = ecaEvolve r x (T + 1)) ↔
      ∀ c, ∃ t < T, ∃ d, nbhd r x t d = nbhd r x T c := by
  constructor
  · intro h c
    by_contra hne
    push_neg at hne
    obtain ⟨n, hn_def⟩ : ∃ n, nbhd r x T c = n := ⟨_, rfl⟩
    simp only [hn_def] at hne
    have hfit : ∀ t ≤ T, ecaEvolve (r ^^^ 2 ^ nbhdIndex n) x t = ecaEvolve r x t := by
      rw [rows_agree_iff]
      intro t ht d
      rw [ecaRule_flip]
      simp [hne t ht d]
    have := congrFun (h _ hfit) c
    rw [ecaEvolve_succ_nbhd, ecaEvolve_succ_nbhd] at this
    have hn : nbhd (r ^^^ 2 ^ nbhdIndex n) x T c = nbhd r x T c := by
      unfold nbhd; rw [hfit T le_rfl]
    rw [hn, hn_def, ecaRule_flip] at this
    simp at this
  · intro h s hs
    have hseen := (rows_agree_iff r s x T).mp hs
    funext c
    rw [ecaEvolve_succ_nbhd, ecaEvolve_succ_nbhd]
    have : nbhd s x T c = nbhd r x T c := by simp [nbhd, hs T le_rfl]
    rw [this]
    obtain ⟨t, ht, d, hd⟩ := h c
    rw [← hd]
    exact hseen t ht d

end GLM.Rule30
