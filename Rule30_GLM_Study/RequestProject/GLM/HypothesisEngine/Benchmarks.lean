module

public import Mathlib

/-!
# Round 39: the hypothesis engine away from Rule 30 — Lean checks of its verdicts

The Round 39 study folder runs the puzzle-independent hypothesis core on eight problems whose
answers are known (`rule30_round39/general_benchmarks.py`).  For each one the engine proposes
statements from a development range, tests them on held-out data, refines (cut, narrow, mine a
law, fit a closed form, split a junction) and hands the survivors to the prover.  This file is
the prover's side: every verdict the engine reported is checked here, either for every index
(`FORMAL`) or by a finite computation (`CERT`).

| problem | engine's lift | held-out verdict | engine's refinement | Lean |
|---|---|---|---|---|
| Euler's `n² + n + 41` | always prime | refuted at `n = 40` | law: composite by 41 iff `n mod 41 ∈ {0, 40}` | `euler_*` |
| Fermat numbers | always prime | refuted at `n = 5` | survivor: pairwise coprime | `fermat_*` |
| primes as `a² + b²` | — | — | law: iff `p mod 4 ≠ 3` | `two_squares_law` |
| circle regions (Moser) | `2 ^ (n − 1)` | refuted at `n = 6` | junction split; quartic fits | `moser_*` |
| Josephus (every 2nd) | — | — | closed form `2 (n − 2 ^ ⌊log₂ n⌋)` | `josephus_closed_form` |
| Collatz | stopping time `≤ c` | refuted at every level | "reaches 1" survives; no finite certificate | `collatz_reaches_one_below` |
| `gcd(n¹⁷ + 9, (n+1)¹⁷ + 9)` | always 1 | survives every range tried | flagged "survives ≠ proved" | `gcd_trap_*` |
| 16-bit midpoint | result in `[lo, hi]` | refuted on large inputs | law: fails iff `lo + hi` overflows; fix proved | `midpoint_*` |

Finite checks that use `native_decide`, and the two bit-blasted (`bv_decide`) midpoint laws, are in
the companion file `BenchmarksData.lean`, following the package convention of keeping compiler-
trusting checks out of the proof files.

The `gcd` row is the cautionary one: the statement survives all `n < 10⁵` in the engine (and
every range anyone can search) but is false; the first counterexample has 52 digits.  The
engine's status discipline (`survives on a range`, never `proved` without a proof) is exactly
what keeps it from asserting it.
-/

@[expose] public section

namespace GLM.HypothesisEngine

/-! ## 1. Euler's polynomial `n² + n + 41` -/

/-- The development-range survivor: prime for every `n < 40` (`CERT`). -/
theorem euler_prime_below_40 : ∀ n < 40, (n ^ 2 + n + 41).Prime := by
  intro n hn
  interval_cases n <;> norm_num

/-- The held-out refutation at `n = 40`: `40² + 40 + 41 = 41²`. -/
theorem euler_not_prime_40 : ¬ (40 ^ 2 + 40 + 41).Prime := by norm_num

/-- **The mined law (every `n`)**: `41` divides `n² + n + 41` exactly when `n mod 41` is `0` or
`40`. -/
theorem euler_dvd_iff (n : ℕ) : 41 ∣ n ^ 2 + n + 41 ↔ n % 41 = 0 ∨ n % 41 = 40 := by
  rw [Nat.dvd_iff_mod_eq_zero]
  have h : (n ^ 2 + n + 41) % 41 = ((n % 41) ^ 2 + n % 41) % 41 := by
    simp [Nat.add_mod, Nat.pow_mod]
  rw [h]
  have hr : n % 41 < 41 := Nat.mod_lt _ (by norm_num)
  generalize n % 41 = r at hr ⊢
  interval_cases r <;> simp

/-- Consequence: for `n ≥ 1` with `n mod 41 ∈ {0, 40}` the value is composite. -/
theorem euler_composite_of_mod {n : ℕ} (hn : 0 < n) (h : n % 41 = 0 ∨ n % 41 = 40) :
    ¬ (n ^ 2 + n + 41).Prime := by
  intro hp
  have hd := (euler_dvd_iff n).mpr h
  rcases (Nat.dvd_prime hp).mp hd with h41 | h41
  · norm_num at h41
  · nlinarith

/-! ## 2. Fermat numbers -/

/-- The held-out refutation: `F₅ = 2³² + 1 = 641 · 6700417`. -/
theorem fermat_five_not_prime : ¬ (Nat.fermatNumber 5).Prime := by
  have h : Nat.fermatNumber 5 = 641 * 6700417 := by norm_num [Nat.fermatNumber]
  rw [h]
  exact Nat.not_prime_mul (by norm_num) (by norm_num)

/-- The survivor the engine hands over: Fermat numbers are pairwise coprime (in Mathlib). -/
theorem fermat_pairwise_coprime {m n : ℕ} (h : m ≠ n) :
    (Nat.fermatNumber m).Coprime (Nat.fermatNumber n) :=
  Nat.coprime_fermatNumber_fermatNumber h

/-! ## 3. Which primes are sums of two squares -/

/-- **The mined law (every prime)**: a prime is a sum of two squares iff it is not `3 mod 4`. -/
theorem two_squares_law {p : ℕ} (hp : p.Prime) :
    (∃ a b : ℕ, a ^ 2 + b ^ 2 = p) ↔ p % 4 ≠ 3 := by
  constructor
  · rintro ⟨a, b, rfl⟩
    have ha : a ^ 2 % 4 = 0 ∨ a ^ 2 % 4 = 1 := by
      rcases Nat.even_or_odd a with ⟨k, rfl⟩ | ⟨k, rfl⟩ <;> ring_nf <;> omega
    have hb : b ^ 2 % 4 = 0 ∨ b ^ 2 % 4 = 1 := by
      rcases Nat.even_or_odd b with ⟨k, rfl⟩ | ⟨k, rfl⟩ <;> ring_nf <;> omega
    omega
  · intro h
    haveI := Fact.mk hp
    exact Nat.Prime.sq_add_sq h

/-! ## 4. Regions of a circle cut by chords (Moser) — a junction -/

/-- The quartic the engine fits to the region counts. -/
def moserQuartic (n : ℕ) : ℕ := n.choose 4 + n.choose 2 + 1

/-- The junction: the quartic and `2 ^ (n − 1)` agree for `n = 1, …, 5`. -/
theorem moser_junction : ∀ n ∈ Finset.Icc 1 5, moserQuartic n = 2 ^ (n - 1) := by decide

/-- The separating observation the engine names: at `n = 6` the two laws differ (`31 ≠ 32`). -/
theorem moser_split : moserQuartic 6 = 31 ∧ 2 ^ (6 - 1) = 32 := by decide

/-! ## 5. Josephus (every second person eliminated) -/

/-- Survivor position (0-indexed) of the Josephus game with `n` people, eliminating every second
one: the standard recursion of the elimination process. -/
def josephus : ℕ → ℕ
  | 0 => 0
  | n + 1 => (josephus n + 2) % (n + 1)

/-- Direct simulation of the circle, used to check the recursion against the game itself.
`go circle pos fuel`: the person after `pos` is eliminated, play continues after them. -/
def josephusSim (n : ℕ) : ℕ :=
  go (List.range n) 0 n
where
  go : List ℕ → ℕ → ℕ → ℕ
  | l, _, 0 => l.headD 0
  | l, pos, fuel + 1 =>
    if l.length ≤ 1 then l.headD 0
    else
      let k := (pos + 1) % l.length
      let l' := l.eraseIdx k
      go l' (k % l'.length) fuel

/-- The recursion agrees with the simulated game for `1 ≤ n ≤ 64` (`CERT`). -/
theorem josephus_eq_sim : ∀ n ∈ Finset.Icc 1 64, josephus n = josephusSim n := by
  decide +kernel

/-- **The engine's closed form (every `n ≥ 1`)**: `J(n) = 2 (n − 2 ^ ⌊log₂ n⌋)`. -/
theorem josephus_closed_form (n : ℕ) (hn : 1 ≤ n) :
    josephus n = 2 * (n - 2 ^ Nat.log 2 n) := by
  induction n, hn using Nat.le_induction with
  | base => decide
  | succ n hn ih =>
    simp only [josephus]
    rw [ih]
    have hlo : 2 ^ Nat.log 2 n ≤ n := Nat.pow_log_le_self 2 (by omega)
    have hhi : n < 2 ^ (Nat.log 2 n + 1) := Nat.lt_pow_succ_log_self (by norm_num) n
    by_cases hp : n + 1 = 2 ^ (Nat.log 2 n + 1)
    · -- `n + 1` is a power of two: the survivor wraps to position 0
      have hl : Nat.log 2 (n + 1) = Nat.log 2 n + 1 := by
        rw [hp, Nat.log_pow (by norm_num)]
      rw [hl, ← hp, Nat.sub_self, mul_zero]
      have : 2 * (n - 2 ^ Nat.log 2 n) + 2 = n + 1 := by
        rw [pow_succ] at hp; omega
      rw [this, Nat.mod_self]
    · have hl : Nat.log 2 (n + 1) = Nat.log 2 n := by
        apply Nat.log_eq_of_pow_le_of_lt_pow (by omega)
        omega
      rw [hl]
      have hlt : 2 * (n - 2 ^ Nat.log 2 n) + 2 < n + 1 := by
        rw [pow_succ] at hhi hp; omega
      rw [Nat.mod_eq_of_lt hlt]
      omega

/-! ## 6. Collatz — a statement with no finite certificate -/

/-- One Collatz step. -/
def collatzStep (n : ℕ) : ℕ := if n % 2 = 0 then n / 2 else 3 * n + 1

/-- `n` reaches `1` within `fuel` steps. -/
def reachesOne : ℕ → ℕ → Bool
  | _, 0 => false
  | n, fuel + 1 => n == 1 || reachesOne (collatzStep n) fuel

/-- The engine's bound lifts fail: e.g. `27` needs more than `100` steps, refuting "stopping
time `≤ 100`" (the narrowed bounds keep failing on every larger range). -/
theorem collatz_27_slow : reachesOne 27 100 = false := by decide

/-! ## 7. The `gcd` trap: survival on every searchable range is not truth -/

/-- …but it is false: the first counterexample has 52 digits (kernel-checked with `decide`). -/
theorem gcd_trap_refuted :
    Nat.gcd (8424432925592889329288197322308900672459420460792433 ^ 17 + 9)
      ((8424432925592889329288197322308900672459420460792433 + 1) ^ 17 + 9) ≠ 1 := by
  decide

/-! ## 8. Debugging: the 16-bit midpoint -/

/-- The buggy midpoint `(lo + hi) / 2` in 16-bit arithmetic. -/
def midBuggy (lo hi : BitVec 16) : BitVec 16 := (lo + hi) / 2

/-- The repaired midpoint `lo + (hi − lo) / 2`. -/
def midFixed (lo hi : BitVec 16) : BitVec 16 := lo + (hi - lo) / 2

/-- The held-out refutation: a concrete failing input. -/
theorem midpoint_bug : midBuggy 40000#16 50000#16 < 40000#16 := by decide

end GLM.HypothesisEngine
