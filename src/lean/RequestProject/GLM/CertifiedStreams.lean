module

public import Mathlib

/-!
# Certified continued-fraction streams: what the `continued fraction` and `mobius` tools emit

The formal half of the stream tools of `studies/CONNECTED_MACHINE_TWO_STUDY.md`
(Phase 136). `glm_universal/reasoning/substrate_cognition.py` already computed
certified continued-fraction terms of an exact real (`cf_terms`) and Gosper's
homographic transform of a continued fraction (`mobius_stream`), but only for
its own measurement; Phase 136 puts both behind `tool continued fraction` and
`tool mobius`. This file proves the two rules they emit a term by.

**The interval rule (`cf_terms`).** The tool knows `x` only as a rational
`mid` with `|x - mid| ≤ 2⁻ᵏ`. It expands both ends of that interval and emits
only the prefix the two expansions share.

* `cfPrefix n x` — the first `n` terms of the continued fraction of `x`
  (`⌊x⌋`, then the expansion of `1 / fract x`), with Lean's `1 / 0 = 0`.
* `cfPrefix_between` — if `x` lies strictly between `lo` and `hi` (in either
  order) and `lo`, `hi` share their first `n` terms, so does `x`.
* `cfPrefix_certified` — the same for the closed interval `lo ≤ x ≤ hi`, which
  is what the tool has. So every term the tool emits is a term of `x`.

**The emission rule (`mobius_stream`).** Gosper's algorithm holds
`(a·t + b)/(c·t + d)`, where `t ≥ 1` is the unread tail, and emits `q` when
`⌊a / c⌋ = ⌊(a + b)/(c + d)⌋ = q` and `c`, `c + d` have one sign.

* `mobius_between` — for `t ≥ 1` with `c`, `c + d` of one sign, the value lies
  between `(a + b)/(c + d)` (its value at `t = 1`) and `a / c` (its limit).
* `gosper_emit_sound` — so every tail gives the same floor `q`: the emitted
  term is a term of the transformed value, whatever the tail.
-/

@[expose] public section

namespace GLM.CertifiedStreams

/-- The first `n` continued-fraction terms of `x`. -/
noncomputable def cfPrefix : ℕ → ℝ → List ℤ
  | 0, _ => []
  | n + 1, x => ⌊x⌋ :: cfPrefix n (1 / Int.fract x)

@[simp] theorem cfPrefix_zero (x : ℝ) : cfPrefix 0 x = [] := rfl

@[simp] theorem cfPrefix_succ (n : ℕ) (x : ℝ) :
    cfPrefix (n + 1) x = ⌊x⌋ :: cfPrefix n (1 / Int.fract x) := rfl

/-- One step of the interval rule, for `lo < x < hi`: equal floors put all three
in one unit cell, and the remainders come back in reverse order. -/
theorem step_between {lo x hi : ℝ} (hlo : lo < x) (hhi : x < hi)
    (hfl : ⌊lo⌋ = ⌊hi⌋) (hpos : 0 < Int.fract lo) :
    ⌊x⌋ = ⌊lo⌋ ∧ 1 / Int.fract hi < 1 / Int.fract x ∧
      1 / Int.fract x < 1 / Int.fract lo := by
  have hx : ⌊x⌋ = ⌊lo⌋ := by
    apply le_antisymm
    · rw [hfl]; exact Int.floor_mono hhi.le
    · exact Int.floor_mono hlo.le
  refine ⟨hx, ?_, ?_⟩
  · have h1 : Int.fract x < Int.fract hi := by
      unfold Int.fract; rw [hx, hfl]; linarith
    have h0 : 0 < Int.fract x := by
      have : Int.fract lo < Int.fract x := by
        unfold Int.fract; rw [hx]; linarith
      linarith
    exact one_div_lt_one_div_of_lt h0 h1
  · have h1 : Int.fract lo < Int.fract x := by
      unfold Int.fract; rw [hx]; linarith
    exact one_div_lt_one_div_of_lt hpos h1

/-- If `lo < x < hi` and `lo`, `hi` share `n + 1` continued-fraction terms with
`n ≥ 1`, then `lo` is not an integer: otherwise the second term of `lo` would
be `⌊1 / 0⌋ = 0`, while that of `hi` is at least one. -/
theorem fract_pos_of_prefix {lo hi : ℝ} (hlt : lo < hi) (n : ℕ)
    (h : cfPrefix (n + 2) lo = cfPrefix (n + 2) hi) : 0 < Int.fract lo := by
  rcases (Int.fract_nonneg lo).lt_or_eq with hpos | hzero
  · exact hpos
  exfalso
  simp only [cfPrefix_succ, List.cons.injEq] at h
  obtain ⟨hfl, hfl2, -⟩ := h
  rw [← hzero] at hfl2
  simp only [div_zero, Int.floor_zero] at hfl2
  have hhi_pos : 0 < Int.fract hi := by
    have hlo_int : (⌊lo⌋ : ℝ) = lo := by
      have := Int.floor_add_fract lo; rw [← hzero] at this; linarith
    by_contra hle
    have hz : Int.fract hi = 0 := le_antisymm (not_lt.mp hle) (Int.fract_nonneg _)
    have hhi_int : (⌊hi⌋ : ℝ) = hi := by
      have := Int.floor_add_fract hi; rw [hz] at this; linarith
    rw [← hlo_int, ← hhi_int, hfl] at hlt
    exact lt_irrefl _ hlt
  have hlt1 : Int.fract hi < 1 := Int.fract_lt_one hi
  have : (1 : ℝ) ≤ 1 / Int.fract hi := by
    rw [le_div_iff₀ hhi_pos]; linarith
  have : (1 : ℤ) ≤ ⌊1 / Int.fract hi⌋ := by
    rw [Int.le_floor]; exact_mod_cast this
  omega

/-- **The interval rule, strict form.** A value strictly between two reals that
share their first `n` continued-fraction terms shares them too. -/
theorem cfPrefix_between (n : ℕ) :
    ∀ {lo x hi : ℝ}, ((lo < x ∧ x < hi) ∨ (hi < x ∧ x < lo)) →
      cfPrefix n lo = cfPrefix n hi → cfPrefix n x = cfPrefix n lo := by
  induction n with
  | zero => intros; rfl
  | succ n ih =>
    intro lo x hi hbt heq
    -- reduce to the ordered case `a < x < b`
    have key : ∀ {a b : ℝ}, a < x → x < b → cfPrefix (n + 1) a = cfPrefix (n + 1) b →
        cfPrefix (n + 1) x = cfPrefix (n + 1) a := by
      intro a b ha hb hab
      cases n with
      | zero =>
        simp only [cfPrefix_succ, cfPrefix_zero, List.cons.injEq, and_true] at hab ⊢
        apply le_antisymm
        · rw [hab]; exact Int.floor_mono hb.le
        · exact Int.floor_mono ha.le
      | succ m =>
        have hpos := fract_pos_of_prefix (ha.trans hb) m hab
        have hab' := hab
        simp only [cfPrefix_succ, List.cons.injEq] at hab'
        obtain ⟨hfl, htail⟩ := hab'
        obtain ⟨hx, h1, h2⟩ := step_between ha hb hfl hpos
        rw [cfPrefix_succ, cfPrefix_succ, hx]
        congr 1
        have htail' : cfPrefix (m + 1) (1 / Int.fract a) =
            cfPrefix (m + 1) (1 / Int.fract b) := by
          simpa [cfPrefix_succ] using htail
        exact ih (Or.inr ⟨h1, h2⟩) htail'
    rcases hbt with ⟨h1, h2⟩ | ⟨h1, h2⟩
    · exact key h1 h2 heq
    · rw [key h1 h2 heq.symm, heq]

/-- **The interval rule, as the tool uses it.** Every value of the closed
interval `[lo, hi]` shares the continued-fraction terms its two ends share. -/
theorem cfPrefix_certified (n : ℕ) {lo x hi : ℝ} (hlo : lo ≤ x) (hhi : x ≤ hi)
    (heq : cfPrefix n lo = cfPrefix n hi) : cfPrefix n x = cfPrefix n lo := by
  rcases hlo.lt_or_eq with hlo | rfl
  · rcases hhi.lt_or_eq with hhi | rfl
    · exact cfPrefix_between n (Or.inl ⟨hlo, hhi⟩) heq
    · exact heq.symm
  · rfl

/-- **The homographic value lies between its two ends.** For a tail `t ≥ 1` and
`c`, `c + d` positive, `(a t + b)/(c t + d)` lies between `(a + b)/(c + d)` and
`a / c`. -/
theorem mobius_between_pos (a b c d t : ℝ) (hc : 0 < c) (hcd : 0 < c + d)
    (ht : 1 ≤ t) :
    min (a / c) ((a + b) / (c + d)) ≤ (a * t + b) / (c * t + d) ∧
      (a * t + b) / (c * t + d) ≤ max (a / c) ((a + b) / (c + d)) := by
  have hden : 0 < c * t + d := by nlinarith
  -- the value is a weighted average of the two ends, with weights
  -- `c (t - 1) ≥ 0` and `c + d > 0`
  have hw : (a * t + b) / (c * t + d) =
      (c * (t - 1) * (a / c) + (c + d) * ((a + b) / (c + d))) /
        (c * (t - 1) + (c + d)) := by
    field_simp
    ring
  set p := a / c
  set q := (a + b) / (c + d)
  have hw1 : 0 ≤ c * (t - 1) := mul_nonneg hc.le (by linarith)
  have hsum : 0 < c * (t - 1) + (c + d) := by linarith
  rw [hw]
  constructor
  · rw [le_div_iff₀ hsum]
    have h1 : min p q ≤ p := min_le_left _ _
    have h2 : min p q ≤ q := min_le_right _ _
    nlinarith
  · rw [div_le_iff₀ hsum]
    have h1 : p ≤ max p q := le_max_left _ _
    have h2 : q ≤ max p q := le_max_right _ _
    nlinarith

/-- `mobius_between_pos` for `c`, `c + d` of either common sign. -/
theorem mobius_between (a b c d t : ℝ)
    (hsign : (0 < c ∧ 0 < c + d) ∨ (c < 0 ∧ c + d < 0)) (ht : 1 ≤ t) :
    min (a / c) ((a + b) / (c + d)) ≤ (a * t + b) / (c * t + d) ∧
      (a * t + b) / (c * t + d) ≤ max (a / c) ((a + b) / (c + d)) := by
  rcases hsign with ⟨hc, hcd⟩ | ⟨hc, hcd⟩
  · exact mobius_between_pos a b c d t hc hcd ht
  · have h := mobius_between_pos (-a) (-b) (-c) (-d) t (by linarith) (by linarith) ht
    have e1 : -a / -c = a / c := neg_div_neg_eq a c
    have e2 : (-a + -b) / (-c + -d) = (a + b) / (c + d) := by
      rw [← neg_add, ← neg_add, neg_div_neg_eq]
    have e3 : (-a * t + -b) / (-c * t + -d) = (a * t + b) / (c * t + d) := by
      rw [show -a * t + -b = -(a * t + b) by ring,
        show -c * t + -d = -(c * t + d) by ring, neg_div_neg_eq]
    rw [e1, e2, e3] at h
    exact h

/-- **Gosper's emission rule is sound.** If `c`, `c + d` have one sign and
`⌊a / c⌋ = ⌊(a + b)/(c + d)⌋ = q`, then every tail `t ≥ 1` gives
`⌊(a t + b)/(c t + d)⌋ = q`: the emitted term does not depend on the part of
the input not yet read. -/
theorem gosper_emit_sound (a b c d : ℤ) (q : ℤ) (t : ℝ)
    (hsign : (0 < c ∧ 0 < c + d) ∨ (c < 0 ∧ c + d < 0)) (ht : 1 ≤ t)
    (h1 : ⌊(a : ℝ) / c⌋ = q) (h2 : ⌊((a : ℝ) + b) / ((c : ℝ) + d)⌋ = q) :
    ⌊((a : ℝ) * t + b) / ((c : ℝ) * t + d)⌋ = q := by
  have hs : (0 < (c : ℝ) ∧ 0 < (c : ℝ) + d) ∨ ((c : ℝ) < 0 ∧ (c : ℝ) + d < 0) := by
    rcases hsign with ⟨h, h'⟩ | ⟨h, h'⟩
    · left; exact ⟨by exact_mod_cast h, by exact_mod_cast h'⟩
    · right; exact ⟨by exact_mod_cast h, by exact_mod_cast h'⟩
  obtain ⟨hmin, hmax⟩ := mobius_between (a : ℝ) b c d t hs ht
  rw [Int.floor_eq_iff] at h1 h2 ⊢
  constructor
  · exact le_trans (le_min h1.1 h2.1) hmin
  · exact lt_of_le_of_lt hmax (max_lt h1.2 h2.2)

/-- A worked instance: the continued fraction of `√2` begins `1, 2, 2`, and the
certified interval `[1.4142, 1.4143]` already decides those three terms. -/
theorem sqrt2_interval_prefix :
    cfPrefix 3 (14142 / 10000 : ℝ) = cfPrefix 3 (14143 / 10000 : ℝ) := by
  have e1 : ⌊(14142 / 10000 : ℝ)⌋ = 1 := by
    rw [Int.floor_eq_iff]; norm_num
  have e2 : ⌊(14143 / 10000 : ℝ)⌋ = 1 := by
    rw [Int.floor_eq_iff]; norm_num
  have f1 : Int.fract (14142 / 10000 : ℝ) = 4142 / 10000 := by
    unfold Int.fract; rw [e1]; norm_num
  have f2 : Int.fract (14143 / 10000 : ℝ) = 4143 / 10000 := by
    unfold Int.fract; rw [e2]; norm_num
  have g1 : ⌊(1 / (4142 / 10000) : ℝ)⌋ = 2 := by
    rw [Int.floor_eq_iff]; norm_num
  have g2 : ⌊(1 / (4143 / 10000) : ℝ)⌋ = 2 := by
    rw [Int.floor_eq_iff]; norm_num
  have k1 : Int.fract (1 / (4142 / 10000) : ℝ) = 1716 / 4142 := by
    unfold Int.fract; rw [g1]; norm_num
  have k2 : Int.fract (1 / (4143 / 10000) : ℝ) = 1714 / 4143 := by
    unfold Int.fract; rw [g2]; norm_num
  have m1 : ⌊(1 / (1716 / 4142) : ℝ)⌋ = 2 := by
    rw [Int.floor_eq_iff]; norm_num
  have m2 : ⌊(1 / (1714 / 4143) : ℝ)⌋ = 2 := by
    rw [Int.floor_eq_iff]; norm_num
  simp only [cfPrefix_succ, cfPrefix_zero, e1, e2, f1, f2, g1, g2, k1, k2, m1, m2]

end GLM.CertifiedStreams
