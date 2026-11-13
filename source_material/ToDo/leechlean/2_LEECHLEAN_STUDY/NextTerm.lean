module

public import Mathlib

/-!
# "What comes next?" from a wheel of stored sequences: when the answer is sound

*Created 1 November 2026 (Phase 186: the next-term reading of `glm_universal.wheels.sequence_query`,
directive D22; a standalone check, written for the absorption of `glm_wheels_bundle` ahead of the
owner's build).*

The Integer Wheel stores sequences as lists of terms. Asked for the term after a claimed prefix
`p`, the GLM looks at every stored sequence that *begins* with `p` and answers only when all of them
continue it, and all with the same term; it refuses when one of them ends exactly at `p` (a stored
branch with no continuation), when two continue differently, and when a stored sequence holds `p`
as a run from its second term (the offset-0/1 convention of the OEIS) and does not continue it with
the same term (it continues differently, or stops there).
`nextTerm` is that rule. The theorems say what an answer means:

* `nextTerm_sound` — if `nextTerm w p = some a`, then *every* stored sequence that begins with `p`
  has `a` as its next term: an answer never picks one continuation among several the wheel knows;
* `nextTerm_witness` — and at least one stored sequence begins with `p` and continues with `a`;
* `nextTerm_none_of_split` — two stored sequences that begin with `p` and continue differently
  force a refusal.

The answer is sound *relative to the wheel*: the claim's true continuation is `a` whenever the
sequence the asker means is stored and begins with `p`. Two instances check the terms of stored
sequences against Mathlib's own definitions: `catalan_terms` (A000108) and `fib_terms` (A000045).
Everything is formal (`decide`, `simp`; no `native_decide`).
-/

@[expose] public section

namespace GLM.IntakeChecks.NextTerm

/-- A wheel of stored sequences, each a list of terms. -/
abbrev Wheel := List (List ℕ)

/-- The next terms of the stored sequences that begin with `p` and continue past it. -/
def continuations (w : Wheel) (p : List ℕ) : List ℕ :=
  (w.filter fun s => p.isPrefixOf s).filterMap fun s => s[p.length]?

/-- The common value of a nonempty list whose entries all agree. -/
def agreed : List ℕ → Option ℕ
  | [] => none
  | a :: rest => if rest.all (· == a) then some a else none

/-- The next-term rule: the agreed continuation, refused when a stored sequence ends exactly at
`p`, or holds `p` from its second term on without continuing it with the same term. -/
def nextTerm (w : Wheel) (p : List ℕ) : Option ℕ :=
  match agreed (continuations w p) with
  | none => none
  | some a =>
    if w.any (fun s => p.isPrefixOf s && s.length == p.length) then none
    else if w.any (fun s => p.isPrefixOf s.tail && s.tail[p.length]? != some a) then none
    else some a

theorem mem_of_agreed {l : List ℕ} {a : ℕ} (h : agreed l = some a) : ∀ b ∈ l, b = a := by
  cases l with
  | nil => simp [agreed] at h
  | cons x rest =>
    simp only [agreed] at h
    split_ifs at h with hall
    cases h
    intro b hb
    rcases List.mem_cons.mp hb with rfl | hb
    · rfl
    · simpa using (List.all_eq_true.mp hall) b hb

theorem agreed_mem {l : List ℕ} {a : ℕ} (h : agreed l = some a) : a ∈ l := by
  cases l with
  | nil => simp [agreed] at h
  | cons x rest =>
    simp only [agreed] at h
    split_ifs at h
    cases h
    exact List.mem_cons_self

/-- An answer is the next term of *every* stored sequence that begins with the claim. -/
theorem nextTerm_sound {w : Wheel} {p : List ℕ} {a : ℕ} (h : nextTerm w p = some a) :
    ∀ s ∈ w, p <+: s → s[p.length]? = some a := by
  intro s hs hp
  unfold nextTerm at h
  split at h
  · simp at h
  · rename_i b hb
    split_ifs at h with h1 h2
    cases h
    have hlen : p.length < s.length := by
      rcases Nat.lt_or_ge p.length s.length with hl | hl
      · exact hl
      · exfalso
        have heq : s.length = p.length := le_antisymm hl hp.length_le
        apply h1
        exact List.any_eq_true.mpr ⟨s, hs, by simp [List.isPrefixOf_iff_prefix.mpr hp, heq]⟩
    have hmem : s[p.length] ∈ continuations w p := by
      unfold continuations
      refine List.mem_filterMap.mpr ⟨s, ?_, ?_⟩
      · exact List.mem_filter.mpr ⟨hs, List.isPrefixOf_iff_prefix.mpr hp⟩
      · simp [hlen]
    rw [List.getElem?_eq_getElem hlen, mem_of_agreed hb _ hmem]

/-- An answer has a witness: a stored sequence that begins with the claim and continues with it. -/
theorem nextTerm_witness {w : Wheel} {p : List ℕ} {a : ℕ} (h : nextTerm w p = some a) :
    ∃ s ∈ w, p <+: s ∧ s[p.length]? = some a := by
  unfold nextTerm at h
  split at h
  · simp at h
  · rename_i b hb
    split_ifs at h
    cases h
    have hmem := agreed_mem hb
    unfold continuations at hmem
    obtain ⟨s, hs, hget⟩ := List.mem_filterMap.mp hmem
    obtain ⟨hs, hpre⟩ := List.mem_filter.mp hs
    exact ⟨s, hs, List.isPrefixOf_iff_prefix.mp hpre, hget⟩

/-- Two stored continuations that differ force a refusal. -/
theorem nextTerm_none_of_split {w : Wheel} {p s t : List ℕ} (hs : s ∈ w) (ht : t ∈ w)
    (hps : p <+: s) (hpt : p <+: t) {b c : ℕ} (hb : s[p.length]? = some b)
    (hc : t[p.length]? = some c) (hbc : b ≠ c) : nextTerm w p = none := by
  cases h : nextTerm w p with
  | none => rfl
  | some a =>
    have h1 := nextTerm_sound h s hs hps
    have h2 := nextTerm_sound h t ht hpt
    rw [hb] at h1
    rw [hc] at h2
    exact absurd ((Option.some.inj h1).trans (Option.some.inj h2).symm) hbc

/-- The first ten Catalan numbers (OEIS A000108), from Mathlib's `catalan`. -/
theorem catalan_terms :
    (List.range 10).map catalan = [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862] := by
  simp [List.range_succ, catalan_eq_centralBinom_div, Nat.centralBinom, Nat.choose]

/-- The first fifteen Fibonacci numbers (OEIS A000045, from `F(0) = 0`), from `Nat.fib`. -/
theorem fib_terms :
    (List.range 15).map Nat.fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377] := by
  simp [List.range_succ, Nat.fib_add_two]

/-- Asked for the term after `1, 1, 2, 5, 14, 42` with the Catalan numbers stored, the rule
answers `132`. -/
example : nextTerm [[1, 1, 2, 5, 14, 42, 132, 429]] [1, 1, 2, 5, 14, 42] = some 132 := by decide

/-- With Fibonacci stored from `F(0) = 0`, the claim `1, 1, 2, 3, 5` is a run from its second
term; with a sequence beginning `1, 1, 2, 3, 5, 7` also stored, the rule refuses. -/
example : nextTerm [[0, 1, 1, 2, 3, 5, 8], [1, 1, 2, 3, 5, 7]] [1, 1, 2, 3, 5] = none := by
  decide

/-- A sequence holding the claim from its second term and stopping there also refuses. -/
example : nextTerm [[0, 3, 5, 17], [3, 5, 17, 257]] [3, 5, 17] = none := by decide

end GLM.IntakeChecks.NextTerm
