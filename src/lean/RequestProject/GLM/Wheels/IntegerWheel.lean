module

public import Mathlib

/-!
# The Integer Wheel: the contract of a provisions wheel over integer sequences

*Created 31 October 2026 (repository check; the intake of `source_material/ToDo/glm_wheels_bundle`,
directive D22).* The supplied Integer Wheel (`integer_wheel.py`, data `oeis_seed.py`) holds entries
`(id, terms)` — an OEIS identifier and the first terms of its b-file — and answers a claim (a list
of integers) with an identifier or stays silent. This file states and proves what that mechanism
guarantees, independently of the data, and checks the stored terms of the closed-form entries.
Everything here is formal (`decide`, no `native_decide`).

## 1. One provision
* `provision_sound` — an entry speaks only its own identifier, only on a nonempty claim, and only
  when the claim is a prefix of its stored terms;
* `provision_complete` — and it does speak whenever that holds.

## 2. Speaking from the whole wheel
`speak w c` is silent on the empty claim; otherwise it answers from the *exact* matches (stored
terms equal to the claim) if there are any, else from the *prefix* matches, and returns the least
identifier of that tier (the Python's alphabetical tie-break).
* `speak_sound` — whatever `speak` says is the identifier of an entry whose stored terms start with
  the claim: the wheel never utters a false identification;
* `speak_eq_none` — it is silent exactly when the claim is empty or no entry starts with it;
* `speak_isSome` — so it answers whenever some entry starts with a nonempty claim;
* `speak_exact` — when some entry's terms are exactly the claim, the answer is such an entry;
* `speak_least` — the answer is the least identifier of the tier it was chosen from.

## 3. Turning the wheel
`merge old new` keeps every entry of the old wheel and adds the new entries whose identifiers are
not already present (`IntegerWheel.merge` in the Python).
* `merge_keeps`, `mem_merge` — nothing old is lost and nothing foreign is added;
* `merge_speak_sound` — speaking from a merged wheel is sound for the union;
* `merge_self` — turning a wheel against itself changes nothing.

## 4. The stored terms of the closed-form entries
For the eight entries of `oeis_seed.py` with a closed form, the stored terms equal the closed form's
first values: Fibonacci (A000045), Lucas (A000032), factorials (A000142), Catalan (A000108), the
primes (A000040), powers of two (A000079), squares (A000290) and triangular numbers (A000217).
`tests/test_integer_wheel.py` reads the `terms…` lists below and compares them with the Python
data, so a drift between the two fails a test.
-/

@[expose] public section

namespace GLM.IntegerWheel

variable {ι : Type*}

/-- One entry of a provisions wheel: an identifier and the stored first terms. -/
structure Entry (ι : Type*) where
  id : ι
  terms : List ℤ

/-! ## 1. One provision -/

/-- The provision of one entry: it speaks its identifier exactly when the claim is a nonempty
prefix of the stored terms, and stays silent otherwise. -/
def provision (e : Entry ι) (claim : List ℤ) : Option ι :=
  if claim ≠ [] ∧ claim <+: e.terms then some e.id else none

theorem provision_sound {e : Entry ι} {c : List ℤ} {i : ι} (h : provision e c = some i) :
    i = e.id ∧ c ≠ [] ∧ c <+: e.terms := by
  unfold provision at h
  split_ifs at h with hc
  cases h
  exact ⟨rfl, hc⟩

theorem provision_complete {e : Entry ι} {c : List ℤ} (hc : c ≠ []) (hp : c <+: e.terms) :
    provision e c = some e.id := by
  simp [provision, hc, hp]

/-! ## The least identifier of a list -/

/-- The least element of a list, if any. -/
def least [LinearOrder ι] : List ι → Option ι
  | [] => none
  | a :: l => match least l with
    | none => some a
    | some b => some (min a b)

theorem least_eq_none [LinearOrder ι] : ∀ {l : List ι}, least l = none ↔ l = []
  | [] => by simp [least]
  | a :: l => by
    unfold least
    cases least l <;> simp

theorem least_mem [LinearOrder ι] : ∀ {l : List ι} {i : ι}, least l = some i → i ∈ l
  | [], _, h => by simp [least] at h
  | a :: l, i, h => by
    unfold least at h
    cases hl : least l with
    | none => rw [hl] at h; cases h; simp
    | some b =>
      rw [hl] at h; cases h
      rcases min_choice a b with hm | hm
      · rw [hm]; simp
      · rw [hm]; exact List.mem_cons_of_mem _ (least_mem hl)

theorem least_le [LinearOrder ι] : ∀ {l : List ι} {i : ι}, least l = some i → ∀ j ∈ l, i ≤ j
  | [], _, h => by simp [least] at h
  | a :: l, i, h => by
    unfold least at h
    cases hl : least l with
    | none =>
      rw [hl] at h; cases h
      have := least_eq_none.1 hl
      subst this
      intro j hj
      simp at hj; subst hj; exact le_rfl
    | some b =>
      rw [hl] at h; cases h
      intro j hj
      rcases List.mem_cons.1 hj with rfl | hj
      · exact min_le_left _ _
      · exact le_trans (min_le_right _ _) (least_le hl j hj)

/-! ## 2. Speaking from the whole wheel -/

/-- The entries whose stored terms are exactly the claim. -/
def exactMatches (w : List (Entry ι)) (c : List ℤ) : List (Entry ι) :=
  w.filter (fun e => decide (e.terms = c))

/-- The entries whose stored terms start with the claim. -/
def prefixMatches (w : List (Entry ι)) (c : List ℤ) : List (Entry ι) :=
  w.filter (fun e => decide (c <+: e.terms))

/-- The tier a claim is answered from: the exact matches if there are any, else the prefix
matches. -/
def chosen (w : List (Entry ι)) (c : List ℤ) : List (Entry ι) :=
  if exactMatches w c = [] then prefixMatches w c else exactMatches w c

theorem mem_chosen {w : List (Entry ι)} {c : List ℤ} {e : Entry ι} (h : e ∈ chosen w c) :
    e ∈ w ∧ c <+: e.terms := by
  unfold chosen at h
  split_ifs at h with hx
  · simp [prefixMatches] at h; exact h
  · simp [exactMatches] at h; exact ⟨h.1, h.2 ▸ List.prefix_refl _⟩

theorem chosen_eq_nil {w : List (Entry ι)} {c : List ℤ} :
    chosen w c = [] ↔ ∀ e ∈ w, ¬ c <+: e.terms := by
  unfold chosen
  split_ifs with hx
  · simp [prefixMatches, List.filter_eq_nil_iff]
  · constructor
    · intro h; exact absurd h hx
    · intro h
      exfalso; apply hx
      simp only [exactMatches, List.filter_eq_nil_iff, decide_eq_true_eq]
      intro e he hte
      exact h e he (hte ▸ List.prefix_refl _)

variable [LinearOrder ι]

/-- `speak`: silent on the empty claim; otherwise the least identifier of the chosen tier. -/
def speak (w : List (Entry ι)) (c : List ℤ) : Option ι :=
  if c = [] then none else least ((chosen w c).map Entry.id)

/-- **Soundness**: whatever `speak` says is the identifier of an entry of the wheel whose stored
terms start with the (nonempty) claim. -/
theorem speak_sound {w : List (Entry ι)} {c : List ℤ} {i : ι} (h : speak w c = some i) :
    c ≠ [] ∧ ∃ e ∈ w, e.id = i ∧ c <+: e.terms := by
  unfold speak at h
  split_ifs at h with hc
  refine ⟨hc, ?_⟩
  obtain ⟨e, he, rfl⟩ := List.mem_map.1 (least_mem h)
  exact ⟨e, (mem_chosen he).1, rfl, (mem_chosen he).2⟩

theorem speak_eq_none {w : List (Entry ι)} {c : List ℤ} :
    speak w c = none ↔ c = [] ∨ ∀ e ∈ w, ¬ c <+: e.terms := by
  unfold speak
  split_ifs with hc
  · simp [hc]
  · rw [least_eq_none, List.map_eq_nil_iff, chosen_eq_nil]
    simp [hc]

theorem speak_isSome {w : List (Entry ι)} {c : List ℤ} (hc : c ≠ []) {e : Entry ι} (he : e ∈ w)
    (hp : c <+: e.terms) : ∃ i, speak w c = some i := by
  cases hs : speak w c with
  | some i => exact ⟨i, rfl⟩
  | none =>
    rcases speak_eq_none.1 hs with h | h
    · exact absurd h hc
    · exact absurd hp (h e he)

/-- **Exact matches first**: when some entry's terms are exactly the claim, the answer is such an
entry (a single order is not identified with a longer list that merely starts with it). -/
theorem speak_exact {w : List (Entry ι)} {c : List ℤ} {i : ι} (h : speak w c = some i)
    (hx : ∃ e ∈ w, e.terms = c) : ∃ e ∈ w, e.id = i ∧ e.terms = c := by
  unfold speak at h
  split_ifs at h with hc
  obtain ⟨e, he, rfl⟩ := List.mem_map.1 (least_mem h)
  have hne : exactMatches w c ≠ [] := by
    obtain ⟨e', he', ht'⟩ := hx
    intro hnil
    have := List.filter_eq_nil_iff.1 hnil e' he'
    simp [ht'] at this
  unfold chosen at he
  split_ifs at he with hx'
  · exact absurd hx' hne
  · simp [exactMatches] at he
    exact ⟨e, he.1, rfl, he.2⟩

/-- **Determinism**: the answer is the least identifier of the tier it was chosen from. -/
theorem speak_least {w : List (Entry ι)} {c : List ℤ} {i : ι} (h : speak w c = some i) :
    ∀ e ∈ chosen w c, i ≤ e.id := by
  unfold speak at h
  split_ifs at h with hc
  intro e he
  exact least_le h e.id (List.mem_map.2 ⟨e, he, rfl⟩)

/-! ## 3. Turning the wheel -/

/-- `merge old new`: every old entry, then the new entries whose identifiers are not yet present. -/
def merge (old new : List (Entry ι)) : List (Entry ι) :=
  old ++ new.filter (fun e => decide (e.id ∉ old.map Entry.id))

theorem merge_keeps {old new : List (Entry ι)} {e : Entry ι} (h : e ∈ old) :
    e ∈ merge old new :=
  List.mem_append_left _ h

theorem mem_merge {old new : List (Entry ι)} {e : Entry ι} (h : e ∈ merge old new) :
    e ∈ old ∨ e ∈ new := by
  rcases List.mem_append.1 h with h | h
  · exact Or.inl h
  · exact Or.inr (List.mem_filter.1 h).1

theorem merge_self (w : List (Entry ι)) : merge w w = w := by
  unfold merge
  have : w.filter (fun e => decide (e.id ∉ w.map Entry.id)) = [] := by
    rw [List.filter_eq_nil_iff]
    intro e he
    simp only [decide_eq_true_eq, not_not]
    exact List.mem_map.2 ⟨e, he, rfl⟩
  rw [this, List.append_nil]

theorem merge_speak_sound {old new : List (Entry ι)} {c : List ℤ} {i : ι}
    (h : speak (merge old new) c = some i) :
    ∃ e, (e ∈ old ∨ e ∈ new) ∧ e.id = i ∧ c <+: e.terms := by
  obtain ⟨_, e, he, hi, hp⟩ := speak_sound h
  exact ⟨e, mem_merge he, hi, hp⟩

/-! ## 4. The stored terms of the closed-form entries -/

/-- The Lucas numbers `2, 1, 3, 4, 7, …`. -/
def lucas : ℕ → ℕ
  | 0 => 2
  | 1 => 1
  | (n + 2) => lucas n + lucas (n + 1)

def termsA000045 : List ℕ := [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368]
def termsA000032 : List ℕ := [2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322, 521, 843, 1364, 2207, 3571, 5778, 9349, 15127, 24476, 39603, 64079, 103682]
def termsA000142 : List ℕ := [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800, 39916800, 479001600, 6227020800, 87178291200, 1307674368000, 20922789888000, 355687428096000, 6402373705728000, 121645100408832000]
def termsA000108 : List ℕ := [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796, 58786, 208012, 742900, 2674440, 9694845, 35357670, 129644790, 477638700, 1767263190]
def termsA000040 : List ℕ := [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
def termsA000079 : List ℕ := [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216]
def termsA000290 : List ℕ := [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 289, 324, 361, 400, 441, 484, 529, 576]
def termsA000217 : List ℕ := [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120, 136, 153, 171, 190, 210, 231, 253, 276, 300]

theorem termsA000045_eq : termsA000045 = (List.range 25).map Nat.fib := by decide
theorem termsA000032_eq : termsA000032 = (List.range 25).map lucas := by decide
theorem termsA000142_eq : termsA000142 = (List.range 20).map Nat.factorial := by decide
theorem termsA000108_eq : termsA000108 = (List.range 20).map (fun n => Nat.choose (2 * n) n / (n + 1)) := by
  decide
/-- The first 25 primes are the primes below 100, in order. -/
theorem termsA000040_eq : termsA000040 = (List.range 100).filter Nat.Prime := by decide
theorem termsA000079_eq : termsA000079 = (List.range 25).map (2 ^ ·) := by decide
theorem termsA000290_eq : termsA000290 = (List.range 25).map (· ^ 2) := by decide
theorem termsA000217_eq : termsA000217 = (List.range 25).map (fun n => n * (n + 1) / 2) := by decide

end GLM.IntegerWheel
