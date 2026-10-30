module

public import RequestProject.GLM.ConstantBound
import all RequestProject.GLM.ConstantBound

/-!
# Passes that print a counter, and the shape of growth (Phase 132)

The formal half of `studies/AFFINE_OUTPUT_STUDY.md`
(`glm_universal.reasoning.batch_machine.jumped_run`, the affine reading, and
`glm_universal.reasoning.batch_machine.growth_diagnosis`).

Phase 131 (`GLM.ConstantBound`) jumps a pass that writes output only when what
it writes does not read the counters, so that every pass writes the same
block. A loop such as

    SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / IF %N% LSS 20000 GOTO UP

writes a different line on every pass, and was refused. Its output is still
determined: the line written at step `r` of pass `m` is the line of a fixed
*template* with each hole naming a counter filled by that counter's value at
step `r` of the first pass plus `m` times its step.

* `wrun_pass_shifted`, `lasso_output_affine`, `halts_of_jump_affine` — with no
  assumption on what the steps write, `K` passes write, pass by pass, what the
  first pass writes when it is started from the translated state; this is
  `GLM.ConstantBound.lasso_output` without its hypothesis on `emit`.
* `render`, `render_shift`, `render_hole` — a line written from a template
  reads each hole at the translated counters: an arithmetic progression in
  every hole (`render_hole`), and the same line on every pass when the template
  has no hole (`render_const`, which gives back Phase 131's repeated block).
* `templated_block` — so the block written on pass `m` is the first pass's
  templates rendered at `x + m • d`: the output of a jump is stated in closed
  form, as `K` blocks whose numbers step by `d`.

The second half is the diagnosis a refused run is given (it never answers a
question and never admits a candidate):

* `diff`, `const_diff_closed_form` — a sequence whose first differences are
  constant is a translation `x₀ + t·Δ`;
* `const_second_diff_closed_form` — one whose *second* differences are
  constant is the quadratic `x₀ + t·Δ₀ + c·t(t−1)/2` (stated without division,
  with `t(t−1)` even);
* `const_ratio_closed_form` — one with `x_{t+1} = r·x_t` is `x₀·rᵗ`;
* `quadratic_not_translation` — a non-zero constant second difference is never
  a translation, however well a straight line happens to fit a window of it.
-/

@[expose] public section

namespace GLM.AffineOutput

open GLM.OperationsLadder GLM.CounterLasso GLM.ConstantBound

/-! ## A pass that writes, from any translate -/

section Pass

variable {C ι O : Type*}

/-- **One pass, with what it writes, from a translate.** No hypothesis on
`emit`: from the start translated by `m • d`, the pass ends at the start
translated by `(m + 1) • d`, having written the first pass's lines as they read
from the translated states. -/
theorem wrun_pass_shifted (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p : ℕ) (d : ι → ℤ) (m : ℤ)
    (hclose : path p = shift d (path 0))
    (hequi : ∀ r < p, step (shift (m • d) (path r)) = some (shift (m • d) (path (r + 1)))) :
    wrun step emit p (shift (m • d) (path 0)) =
      some (shift ((m + 1) • d) (path 0), block (fun s => emit (shift (m • d) s)) path p) := by
  have hr : ∀ r ≤ p, wrun step emit r (shift (m • d) (path 0)) =
      some (shift (m • d) (path r), block (fun s => emit (shift (m • d) s)) path r) := by
    intro r hrp
    induction r with
    | zero => rfl
    | succ r ih =>
      rw [wrun_add, ih (by omega), Option.bind_some]
      simp only [wrun, hequi r (by omega), Option.bind_some, Option.map_some,
        List.append_nil, block_succ]
  rw [hr p le_rfl, hclose, shift_shift, add_smul, one_smul, add_comm d]

/-- The lines written by `K` passes, pass `m` read from the start translated by
`m • d`. -/
def passOutput (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p K : ℕ)
    (d : ι → ℤ) : List O :=
  ((List.range K).map fun m => block (fun s => emit (shift ((m : ℤ) • d) s)) path p).flatten

theorem passOutput_succ (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p K : ℕ)
    (d : ι → ℤ) :
    passOutput emit path p (K + 1) d =
      passOutput emit path p K d ++ block (fun s => emit (shift ((K : ℤ) • d) s)) path p := by
  simp [passOutput, List.range_succ]

/-- **The jump, with what every pass writes.** `K` passes end at the start
translated by `K • d` in `K * p` steps, having written pass `m`'s block as read
from the translate `m • d`, for `m = 0, …, K − 1` in order. -/
theorem lasso_output_affine (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p K : ℕ) (d : ι → ℤ)
    (hclose : path p = shift d (path 0))
    (hequi : ∀ m < K, ∀ r < p,
      step (shift ((m : ℤ) • d) (path r)) = some (shift ((m : ℤ) • d) (path (r + 1)))) :
    wrun step emit (K * p) (path 0) =
      some (shift ((K : ℤ) • d) (path 0), passOutput emit path p K d) := by
  induction K with
  | zero => simp [wrun, passOutput]
  | succ K ih =>
    rw [Nat.succ_mul, wrun_add, ih (fun m hm => hequi m (by omega)), Option.bind_some,
      wrun_pass_shifted step emit path p d K hclose (hequi K (by omega)), Option.map_some,
      passOutput_succ]
    push_cast
    rfl

/-- **The halting certificate, with a counter in the output.** Run `i` steps
to the start of the pass writing `w₀`, jump `K` passes, and run `n` more steps
writing `w₁` to a state with no successor: the machine halts after exactly
`i + K * p + n` steps, having written `w₀`, the `K` blocks, and `w₁`. -/
theorem halts_of_jump_affine (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (s₀ : C × (ι → ℤ)) (path : ℕ → C × (ι → ℤ))
    (i p K n : ℕ) (d : ι → ℤ) (t : C × (ι → ℤ)) (w₀ w₁ : List O)
    (hi : wrun step emit i s₀ = some (path 0, w₀))
    (hclose : path p = shift d (path 0))
    (hequi : ∀ m < K, ∀ r < p,
      step (shift ((m : ℤ) • d) (path r)) = some (shift ((m : ℤ) • d) (path (r + 1))))
    (hn : wrun step emit n (shift ((K : ℤ) • d) (path 0)) = some (t, w₁))
    (ht : step t = none) :
    wrun step emit (i + K * p + n) s₀ = some (t, w₀ ++ passOutput emit path p K d ++ w₁) ∧
      Halts step s₀ := by
  have h : wrun step emit (i + K * p + n) s₀ =
      some (t, w₀ ++ passOutput emit path p K d ++ w₁) := by
    rw [wrun_add, wrun_add, hi, Option.bind_some, lasso_output_affine step emit path p K d hclose hequi,
      Option.map_some, Option.bind_some, hn, Option.map_some]
  refine ⟨h, i + K * p + n, t, ?_, ht⟩
  have := congrArg (Option.map Prod.fst) h
  rwa [wrun_fst] at this

end Pass

/-! ## Lines written from a template -/

section Template

variable {ι A : Type*}

/-- One line written from a template: a literal piece is written as it is,
and a hole naming counter `i` is written as `fmt (x i)` (the decimal digits). -/
def render (fmt : ℤ → List A) (tmpl : List (List A ⊕ ι)) (x : ι → ℤ) : List A :=
  (tmpl.map fun | .inl a => a | .inr i => fmt (x i)).flatten

/-- The hole of a template reads the translated counter: `x_i + m · d_i`. -/
@[simp] theorem render_hole (fmt : ℤ → List A) (i : ι) (x d : ι → ℤ) (m : ℤ) :
    render fmt [.inr i] (x + m • d) = fmt (x i + m * d i) := by
  simp [render]

/-- Rendering distributes over the pieces of a template. -/
theorem render_append (fmt : ℤ → List A) (t₁ t₂ : List (List A ⊕ ι)) (x : ι → ℤ) :
    render fmt (t₁ ++ t₂) x = render fmt t₁ x ++ render fmt t₂ x := by
  simp [render]

/-- A template with no hole writes the same line from every translate — Phase
131's repeated block. -/
theorem render_const (fmt : ℤ → List A) (tmpl : List (List A ⊕ ι))
    (h : ∀ e ∈ tmpl, e.isLeft) (x y : ι → ℤ) : render fmt tmpl x = render fmt tmpl y := by
  induction tmpl with
  | nil => rfl
  | cons e tl ih =>
    have hl := h e (by simp)
    have ht := ih (fun e' he' => h e' (by simp [he']))
    cases e with
    | inl a => simpa [render] using ht
    | inr i => simp at hl

variable {C : Type*}

/-- **The block of pass `m`, in closed form.** If the line a step writes is read
from a template with the counters of its state, then the block written on pass
`m` is the first pass's templates rendered at the counters translated by
`m • d`. -/
theorem templated_block (fmt : ℤ → List A) (tmpl : C → List (List (List A ⊕ ι)))
    (emit : C × (ι → ℤ) → List (List A))
    (hemit : ∀ s, emit s = (tmpl s.1).map fun t => render fmt t s.2)
    (path : ℕ → C × (ι → ℤ)) (p : ℕ) (d : ι → ℤ) (m : ℤ) :
    block (fun s => emit (shift (m • d) s)) path p =
      ((List.range p).map fun r =>
        (tmpl (path r).1).map fun t => render fmt t ((path r).2 + m • d)).flatten := by
  simp [block, hemit, shift]

end Template

/-! ## The shape of growth, for the diagnosis of a refusal -/

section Growth

/-- First differences of a sequence. -/
def diff (x : ℕ → ℤ) (t : ℕ) : ℤ := x (t + 1) - x t

/-- Constant first differences: a translation `x₀ + t·Δ`. -/
theorem const_diff_closed_form (x : ℕ → ℤ) (Δ : ℤ) (h : ∀ t, diff x t = Δ) (t : ℕ) :
    x t = x 0 + t * Δ := by
  induction t with
  | zero => simp
  | succ t ih =>
    have := h t
    unfold diff at this
    push_cast
    linarith

/-- Constant second differences: the quadratic `x₀ + t·Δ₀ + c·t(t−1)/2`,
stated as `2·x_t = 2·x₀ + 2·t·Δ₀ + c·t·(t−1)`. -/
theorem const_second_diff_closed_form (x : ℕ → ℤ) (c : ℤ) (h : ∀ t, diff (diff x) t = c)
    (t : ℕ) : 2 * x t = 2 * x 0 + 2 * t * diff x 0 + c * t * (t - 1) := by
  have hd : ∀ t, diff x t = diff x 0 + t * c := const_diff_closed_form (diff x) c h
  induction t with
  | zero => simp
  | succ t ih =>
    have h1 := hd t
    have h2 : diff x t = x (t + 1) - x t := rfl
    push_cast
    linear_combination ih + 2 * h1 - 2 * h2

/-- Constant ratio: `x_{t+1} = r·x_t` gives `x_t = x₀·rᵗ`. -/
theorem const_ratio_closed_form (x : ℕ → ℤ) (r : ℤ) (h : ∀ t, x (t + 1) = r * x t) (t : ℕ) :
    x t = x 0 * r ^ t := by
  induction t with
  | zero => simp
  | succ t ih => rw [h t, ih, pow_succ]; ring

/-- A non-zero constant second difference is never a translation: no `Δ` makes
every first difference equal to it. -/
theorem quadratic_not_translation (x : ℕ → ℤ) (c : ℤ) (hc : c ≠ 0)
    (h : ∀ t, diff (diff x) t = c) : ¬ ∃ Δ, ∀ t, diff x t = Δ := by
  rintro ⟨Δ, hΔ⟩
  have := h 0
  simp only [diff] at this hΔ
  have h1 := hΔ 1
  have h0 := hΔ 0
  exact hc (by linarith)

end Growth

end GLM.AffineOutput
