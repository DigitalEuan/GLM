module

public import RequestProject.GLM.Rule30.ConeSeparation
public import RequestProject.GLM.Rule30.Prizes

/-!
# Machine models for Problem 3

Problem 3 asks whether computing `a(n)` needs `Ω(n)` computational effort. Whether that question
is meaningful depends on the machine model, so this file separates three models.

## 1. Boolean circuits (straight-line programs)

`Circuit n` is a list of fan-in ≤ 2 gates over `n` input wires. Proved:

* `essential_mem_reads` : a circuit's output can only depend on an input that the output wire is,
  or that some gate reads.
* `card_essential_le` : **if `f` depends essentially on `k` inputs, every circuit computing `f` has
  at least `(k − 1)/2` gates** (`k ≤ 2·size + 1`).

## 2. Circuits on the row: the light-cone map (not Problem 3)

`centreWindow t : (Fin (2t+1) → Bool) → Bool` is the map `(x_{-t}, …, x_t) ↦ a(t)(0)`.

* `centreWindow_essential_left` : it always depends on `x_{-t}` (cone separation).
* `centreWindow_essential_right` : it always depends on `x_t` (right-edge derivative formula).
* `WholeConeDependence` (open, stated): it depends on **all** `2t+1` cells. `wholeCone_le_6`
  (in `MachineModelData.lean`) checks this for `t ≤ 6` by exhaustive computation.
* `circuit_size_ge_of_wholeCone` : under `WholeConeDependence`, every circuit computing the
  light-cone map has at least `t` gates.

This is a lower bound for the *generic map* (input: a whole row, `2t+1` bits). It is **not**
Problem 3, whose input is only the number `n`.

## 3. Problem 3 needs a uniform model

* `nonuniform_trivial` : for each fixed `n`, the bit `a(n)` is computed by a circuit with **zero**
  gates (a constant). So non-uniform circuit size says nothing about Problem 3: a model with one
  machine for all `n` is needed.
* `fuel_model_trivial` : in the step-counted evaluation `Nat.Partrec.Code.evaln` of Mathlib, the
  fuel needed on input `n` is always more than `n`, for **every** program. So "Ω(n)" holds there
  for trivial reasons (the input is effectively read in unary) and that model does not capture
  Problem 3 either.
* `Problem3` : the faithful statement, in Mathlib's multi-tape Turing machine model
  (`Turing.TM2ComputableInTime`) with `n` written in **binary** and the output bit as result: no
  machine computing the centre column has a running-time bound that is `o(n)`. This is **open**.
  Note that the time bound is a function of the input *length* `≈ log₂ n`, so `o(n)` means
  `o(2^length)`; proving such a lower bound for a specific natural function is far beyond known
  lower-bound techniques. The proposed "diagonal-predictor coupling" argument does not supply one:
  see `DiagonalCoupling.lean`, where the same coupling holds for rows with constant-time centre
  columns.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## 1. Boolean circuits -/

/-- A gate. Wires are numbered: `0, …, n−1` are the inputs, wire `n + j` is the output of
gate `j`. A read of a wire that does not exist yet returns `false`. -/
inductive Gate where
  | const (b : Bool)
  | not (a : ℕ)
  | and (a b : ℕ)
  | or (a b : ℕ)
  | xor (a b : ℕ)
  deriving DecidableEq

namespace Gate

/-- The wires read by a gate (at most two). -/
def reads : Gate → List ℕ
  | const _ => []
  | not a => [a]
  | and a b => [a, b]
  | or a b => [a, b]
  | xor a b => [a, b]

theorem reads_length_le (g : Gate) : g.reads.length ≤ 2 := by
  cases g <;> simp [reads]

/-- Evaluate a gate on the current list of wire values. -/
def eval (vs : List Bool) : Gate → Bool
  | const b => b
  | not a => !vs.getD a false
  | and a b => vs.getD a false && vs.getD b false
  | or a b => vs.getD a false || vs.getD b false
  | xor a b => Bool.xor (vs.getD a false) (vs.getD b false)

theorem eval_congr (g : Gate) (vs ws : List Bool)
    (h : ∀ j ∈ g.reads, vs.getD j false = ws.getD j false) : g.eval vs = g.eval ws := by
  cases g <;> simp_all [reads, eval]

end Gate

/-- Run a list of gates, appending each gate's value to the wire list. -/
def runGates : List Gate → List Bool → List Bool
  | [], vs => vs
  | g :: gs, vs => runGates gs (vs ++ [g.eval vs])

/-- A circuit with `n` inputs: a list of gates and an output wire. -/
structure Circuit (n : ℕ) where
  gates : List Gate
  output : ℕ

namespace Circuit

variable {n : ℕ}

/-- Number of gates. -/
def size (C : Circuit n) : ℕ := C.gates.length

/-- Evaluate the circuit. -/
def eval (C : Circuit n) (v : Fin n → Bool) : Bool :=
  (runGates C.gates (List.ofFn v)).getD C.output false

/-- `C` computes `f`. -/
def Computes (C : Circuit n) (f : (Fin n → Bool) → Bool) : Prop := ∀ v, C.eval v = f v

end Circuit

/-- `f` depends essentially on input `i`: flipping `x_i` changes `f` for some input. -/
def Essential {n : ℕ} (f : (Fin n → Bool) → Bool) (i : Fin n) : Prop :=
  ∃ v, f (Function.update v i (!v i)) ≠ f v

theorem runGates_length (gs : List Gate) (vs : List Bool) :
    (runGates gs vs).length = vs.length + gs.length := by
  induction gs generalizing vs with
  | nil => simp [runGates]
  | cons g gs ih => simp [runGates, ih]; ring

theorem getD_append_singleton (vs : List Bool) (b : Bool) (j : ℕ) :
    (vs ++ [b]).getD j false = if j < vs.length then vs.getD j false
      else if j = vs.length then b else false := by
  simp only [List.getD_eq_getElem?_getD]
  split_ifs with h1 h2
  · rw [List.getElem?_append_left h1]
  · subst h2; simp
  · rw [List.getElem?_append_right (by omega)]
    simp [show j - vs.length ≠ 0 by omega]

/-- If no gate reads wire `i`, wire lists that agree off `i` keep agreeing off `i`. -/
theorem runGates_agree (i : ℕ) (gs : List Gate) (hgs : ∀ g ∈ gs, i ∉ g.reads) (vs ws : List Bool)
    (hlen : vs.length = ws.length) (hag : ∀ j, j ≠ i → vs.getD j false = ws.getD j false) :
    ∀ j, j ≠ i → (runGates gs vs).getD j false = (runGates gs ws).getD j false := by
  induction gs generalizing vs ws with
  | nil => exact hag
  | cons g gs ih =>
    simp only [runGates]
    have hg : g.eval vs = g.eval ws :=
      g.eval_congr vs ws (fun j hj => hag j (fun h => hgs g (by simp) (h ▸ hj)))
    apply ih (fun g' hg' => hgs g' (by simp [hg'])) _ _ (by simp [hlen])
    intro j hj
    rw [getD_append_singleton, getD_append_singleton, hg, hlen, hag j hj]

/-- **An input that no gate reads (and that is not the output) is inessential.** -/
theorem essential_mem_reads {n : ℕ} (C : Circuit n) (i : Fin n) (h : Essential C.eval i) :
    C.output = i ∨ ∃ g ∈ C.gates, (i : ℕ) ∈ g.reads := by
  by_contra hcon
  push_neg at hcon
  obtain ⟨hout, hreads⟩ := hcon
  obtain ⟨v, hv⟩ := h
  apply hv
  unfold Circuit.eval
  refine runGates_agree i C.gates hreads _ _ (by simp) (fun j hj => ?_) C.output hout
  simp only [List.getD_eq_getElem?_getD, List.getElem?_ofFn]
  by_cases hjn : j < n
  · simp only [hjn, dite_true, Option.getD_some]
    rw [Function.update_of_ne (fun h => hj (by rw [← h]))]
  · simp [hjn]

/-- **Essential inputs bound circuit size from below:** if `f` depends on every input in `S`,
any circuit computing `f` has `|S| ≤ 2·size + 1`. -/
theorem card_essential_le {n : ℕ} (C : Circuit n) (f : (Fin n → Bool) → Bool) (hC : C.Computes f)
    (S : Finset (Fin n)) (hS : ∀ i ∈ S, Essential f i) : S.card ≤ 2 * C.size + 1 := by
  have hf : C.eval = f := funext hC
  have hsub : S.image (fun i : Fin n => (i : ℕ)) ⊆ (C.output :: C.gates.flatMap Gate.reads).toFinset := by
    intro j hj
    obtain ⟨i, hi, rfl⟩ := Finset.mem_image.mp hj
    have := essential_mem_reads C i (hf ▸ hS i hi)
    rcases this with h | ⟨g, hg, hr⟩
    · simp [h]
    · simp only [List.toFinset_cons, Finset.mem_insert, List.mem_toFinset, List.mem_flatMap]
      exact Or.inr ⟨g, hg, hr⟩
  have h1 := Finset.card_le_card hsub
  rw [Finset.card_image_of_injective _ Fin.val_injective] at h1
  have h2 := List.toFinset_card_le (C.output :: C.gates.flatMap Gate.reads)
  have h3 : (C.gates.flatMap Gate.reads).length ≤ 2 * C.gates.length := by
    rw [List.length_flatMap]
    have : ∀ l : List Gate, (l.map (fun g => g.reads.length)).sum ≤ 2 * l.length := by
      intro l
      induction l with
      | nil => simp
      | cons g l ih => simp only [List.map_cons, List.sum_cons, List.length_cons]
                       have := g.reads_length_le; omega
    exact this _
  simp only [List.length_cons] at h2
  unfold Circuit.size
  omega

/-! ## 2. The light-cone map `(x_{-t}, …, x_t) ↦ a(t)(0)` -/

/-- The row with window `v` on `[-t, t]` and white elsewhere. -/
def windowRow (t : ℕ) (v : Fin (2 * t + 1) → Bool) : Config := fun j =>
  if h : -(t : ℤ) ≤ j ∧ j ≤ t then v ⟨(j + t).toNat, by omega⟩ else false

/-- The light-cone map: the centre cell after `t` steps as a function of the `2t+1` cells of its
light cone. -/
def centreWindow (t : ℕ) (v : Fin (2 * t + 1) → Bool) : Bool := evolve (windowRow t v) t 0

/-- The window index of position `j ∈ [-t, t]`. -/
def windowIdx (t : ℕ) (j : ℤ) (h : -(t : ℤ) ≤ j ∧ j ≤ t) : Fin (2 * t + 1) :=
  ⟨(j + t).toNat, by omega⟩

theorem windowRow_flip (t : ℕ) (v : Fin (2 * t + 1) → Bool) (j : ℤ) (h : -(t : ℤ) ≤ j ∧ j ≤ t) :
    windowRow t (Function.update v (windowIdx t j h) (!v (windowIdx t j h))) =
      flipAt (windowRow t v) j := by
  funext k
  simp only [flipAt]
  by_cases hk : k = j
  · subst hk; simp [h, windowIdx, windowRow]
  · rw [Function.update_of_ne hk]
    simp only [windowRow]
    split_ifs with hk'
    · rw [Function.update_of_ne]
      simp only [windowIdx, ne_eq, Fin.mk.injEq]
      omega
    · rfl

/-- **The light-cone map always depends on `x_{-t}`** (cone separation). -/
theorem centreWindow_essential_left (t : ℕ) :
    Essential (centreWindow t) (windowIdx t (-t) (by omega)) := by
  refine ⟨fun _ => false, ?_⟩
  unfold centreWindow
  rw [windowRow_flip, show (-(t : ℤ)) = 0 - t by ring, evolve_flip_left_edge]
  simp

/-- **The light-cone map always depends on `x_t`** (right-edge derivative formula, at the white
row). -/
theorem centreWindow_essential_right (t : ℕ) :
    Essential (centreWindow t) (windowIdx t t (by omega)) := by
  refine ⟨fun _ => false, ?_⟩
  unfold centreWindow
  rw [windowRow_flip]
  have hw : windowRow t (fun _ => false) = fun _ => false := by
    funext j; simp [windowRow]
  rw [hw]
  have hd := booleanDerivative_right_edge t 0 (fun _ => false)
  simp only [booleanDerivative, zero_add, evolve_false] at hd
  simp only [flipAt, Bool.not_false]
  have h0 : Function.update (fun _ : ℤ => false) (t : ℤ) false = fun _ => false := by
    funext j; by_cases hj : j = t <;> simp [Function.update, hj]
  rw [h0, evolve_false] at hd
  rw [evolve_false]
  simpa using hd

/-- **Whole-cone dependence** (open in general): the centre cell after `t` steps depends on every
one of the `2t+1` cells of its light cone. -/
def WholeConeDependence : Prop := ∀ t (i : Fin (2 * t + 1)), Essential (centreWindow t) i

/-- A decidable form of essentiality, for small exhaustive checks. -/
def essentialB {n : ℕ} (f : (Fin n → Bool) → Bool) (i : Fin n) : Bool :=
  decide (∃ v : Fin n → Bool, f (Function.update v i (!v i)) ≠ f v)

/-- **Conditional circuit lower bound for the light-cone map.** If the centre cell depends on its
whole light cone, every circuit computing it from the row has at least `t` gates. -/
theorem circuit_size_ge_of_wholeCone (hW : WholeConeDependence) (t : ℕ)
    (C : Circuit (2 * t + 1)) (hC : C.Computes (centreWindow t)) : t ≤ C.size := by
  have := card_essential_le C _ hC Finset.univ (fun i _ => hW t i)
  simp at this
  omega

/-! ## 3. Problem 3 needs a uniform machine model -/

/-- **Non-uniform circuit size is trivial for a single sequence.** For each `n`, the bit `a(n)` is
computed by a circuit with no inputs and no gates beyond one constant. (Here the circuit has a
single constant gate; its size is `1`.) -/
theorem nonuniform_trivial (a : ℕ → Bool) (n : ℕ) :
    ∃ C : Circuit 0, C.size = 1 ∧ C.Computes (fun _ => a n) :=
  ⟨⟨[Gate.const (a n)], 0⟩, rfl, fun v => by
    simp [Circuit.eval, runGates, List.ofFn_zero, Gate.eval]⟩

/-- **The fuel of `Nat.Partrec.Code.evaln` is always more than the input.** For every program and
every input `n`, a successful run with fuel `k` has `n < k`. So an `Ω(n)` "lower bound" in this
model holds for every function, Rule 30 or not, and the model does not capture Problem 3. -/
theorem fuel_model_trivial (c : Nat.Partrec.Code) (k n m : ℕ)
    (h : m ∈ Nat.Partrec.Code.evaln k c n) : n < k :=
  Nat.Partrec.Code.evaln_bound h

open Asymptotics Filter in
/-- **Problem 3** (open), in Mathlib's multi-tape Turing machine model with `n` written in binary:
no Turing machine computing the centre column has a running-time bound that is `o(n)`.
(`M.time` is a bound in terms of the input length; `(Computability.finEncodingNatBool.encode n).length`
is the length of the binary representation of `n`.) -/
def Problem3 : Prop :=
  ∀ M : Turing.TM2ComputableInTime Computability.finEncodingNatBool
      Computability.finEncodingBoolBool centerCol,
    ¬ (fun n : ℕ => (M.time (Computability.finEncodingNatBool.encode n).length : ℝ)) =o[atTop]
      (fun n : ℕ => (n : ℝ))

end GLM.Rule30
