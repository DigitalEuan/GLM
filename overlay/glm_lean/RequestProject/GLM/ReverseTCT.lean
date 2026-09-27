module

public import Mathlib

/-!
# Reverse Three Column Thinking: the language column generated from the mathematics

The formal half of `studies/REVERSE_TCT_STUDY.md` (mark V7).

`glm_universal/reasoning/reverse_tct.py` realises an exact term over ℚ as
English *prefix first* — `the sum of A and B`, `the negation of A`, … — and
reads the English back. Everything the reverse direction offers rests on that
realisation being uniquely readable, so that the language column carries
exactly the information of the mathematics column.

**The grammar.** A literal's spelling (its number words, `negative …`,
`the fraction … over …`) is modelled as one token `Tok.num q`: that the
spelling of a rational is canonical and injective is checked exhaustively in
the study's battery rather than here.

* `render_prefix_free` — if the realisations of two terms agree up to what
  follows them, the terms and what follows them agree. This is unique
  readability.
* `render_injective`, `renderStmt_prefix_free`, `renderStmt_injective`,
  `renderConj_injective` — distinct terms, statements and conjunctions get
  distinct sentences.
* `infix_not_injective` — the natural infix control (`x plus y plus z`, no
  scope words) gives two different terms one sentence.

**The operations.**

* `negate_exact` — the negated relation holds at exactly the points where the
  relation fails, for every relation.
* `farkas_refutes` — non-negative multipliers that cancel every coefficient and
  leave a contradictory constant refute the system: no point satisfies all its
  rows. This is the certificate behind `ENTAILS`, `CONTRADICTS` and
  `INCONSISTENT_PREMISES`.
* `entails_of_refuted` — premises together with the negated conclusion having
  no solution is entailment.
* `pairing_lt`, `pairing_le`, `pairing_lt_neg`, `pairing_le_neg`,
  `pairing_eq` — two statements whose differences are proportional
  (`d₁ = k · d₂`) are equivalent, with the relation reversed when `k < 0`:
  the certificate behind `solve`, `equivalent` and every paraphrase.
* `solve_eq`, `solve_le_pos`, `solve_le_neg` — the solved form of a linear
  statement in `x` with a nonzero constant coefficient.
* `grid_identity` — two polynomials whose difference has degree at most `d`
  in each variable and which agree on the grid `{0, …, d}ⁿ` are equal: the
  check the column-3 script uses for polynomial identities.
-/

@[expose] public section

namespace GLM.ReverseTCT

/-! ## The terms and their sentences -/

/-- Column 2: exact terms over ℚ. -/
inductive Term where
  | lit : ℚ → Term
  | var : String → Term
  | add : Term → Term → Term
  | sub : Term → Term → Term
  | mul : Term → Term → Term
  | div : Term → Term → Term
  | neg : Term → Term
  | pow : Term → ℕ → Term
  deriving DecidableEq

/-- The words of column 1. -/
inductive Tok where
  | num : ℚ → Tok
  | name : String → Tok
  | the | sum | difference | product | quotient | of | and_
  | negation | square | cube | power | with_ | exponent
  | equals | does | not_ | equal | is | less | than | at_ | most | greater
  | least | comma
  deriving DecidableEq

/-- The head word of a power: `square`, `cube`, or `power … with exponent n`. -/
def powWord (n : ℕ) : Tok :=
  if n = 2 then .square else if n = 3 then .cube else .power

/-- What follows the base of a power: nothing for a square or a cube,
`with exponent n` otherwise. -/
def powTail (n : ℕ) : List Tok :=
  if n = 2 ∨ n = 3 then [] else [.with_, .exponent, .num n]

open Tok in
/-- The realiser: every term is spelled with its head word first. -/
def render : Term → List Tok
  | .lit q => [num q]
  | .var x => [name x]
  | .add a b => [the, sum, of] ++ render a ++ [and_] ++ render b
  | .sub a b => [the, difference, of] ++ render a ++ [and_] ++ render b
  | .mul a b => [the, product, of] ++ render a ++ [and_] ++ render b
  | .div a b => [the, quotient, of] ++ render a ++ [and_] ++ render b
  | .neg a => [the, negation, of] ++ render a
  | .pow a n => [the, powWord n, of] ++ render a ++ powTail n

theorem powWord_cases (n : ℕ) :
    powWord n = .square ∨ powWord n = .cube ∨ powWord n = .power := by
  unfold powWord; split_ifs <;> simp

theorem pow_parts_inj {n m : ℕ} {r s : List Tok} (hw : powWord n = powWord m)
    (ht : powTail n ++ r = powTail m ++ s) : n = m ∧ r = s := by
  unfold powWord at hw
  unfold powTail at ht
  by_cases h2 : n = 2 <;> by_cases h3 : n = 3 <;> by_cases h2' : m = 2 <;>
    by_cases h3' : m = 3 <;> simp_all

/-- Unique readability: the realisation of a term is never a proper prefix of
another's, and fixes the term. -/
theorem render_prefix_free :
    ∀ (a b : Term) (r s : List Tok), render a ++ r = render b ++ s →
      a = b ∧ r = s := by
  intro a
  induction a with
  | lit q =>
      intro b r s h
      cases b <;> simp_all [render]
  | var x =>
      intro b r s h
      cases b <;> simp_all [render]
  | add a₁ a₂ ih₁ ih₂ =>
      intro b r s h
      cases b with
      | add b₁ b₂ =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, h₁⟩ := ih₁ _ _ _ h
          simp only [List.cons.injEq, true_and] at h₁
          obtain ⟨e₂, e₃⟩ := ih₂ _ _ _ h₁
          exact ⟨by rw [e₁, e₂], e₃⟩
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | sub a₁ a₂ ih₁ ih₂ =>
      intro b r s h
      cases b with
      | sub b₁ b₂ =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, h₁⟩ := ih₁ _ _ _ h
          simp only [List.cons.injEq, true_and] at h₁
          obtain ⟨e₂, e₃⟩ := ih₂ _ _ _ h₁
          exact ⟨by rw [e₁, e₂], e₃⟩
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | mul a₁ a₂ ih₁ ih₂ =>
      intro b r s h
      cases b with
      | mul b₁ b₂ =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, h₁⟩ := ih₁ _ _ _ h
          simp only [List.cons.injEq, true_and] at h₁
          obtain ⟨e₂, e₃⟩ := ih₂ _ _ _ h₁
          exact ⟨by rw [e₁, e₂], e₃⟩
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | div a₁ a₂ ih₁ ih₂ =>
      intro b r s h
      cases b with
      | div b₁ b₂ =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, h₁⟩ := ih₁ _ _ _ h
          simp only [List.cons.injEq, true_and] at h₁
          obtain ⟨e₂, e₃⟩ := ih₂ _ _ _ h₁
          exact ⟨by rw [e₁, e₂], e₃⟩
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | neg a ih =>
      intro b r s h
      cases b with
      | neg b =>
          simp only [render, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, e₂⟩ := ih _ _ _ h
          exact ⟨by rw [e₁], e₂⟩
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | pow a n ih =>
      intro b r s h
      cases b with
      | pow b m =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨hw, h₁⟩ := h
          obtain ⟨e₁, h₂⟩ := ih _ _ _ h₁
          obtain ⟨e₂, e₃⟩ := pow_parts_inj hw h₂
          exact ⟨by rw [e₁, e₂], e₃⟩
      | _ => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h

/-- Distinct terms get distinct sentences. -/
theorem render_injective {a b : Term} (h : render a = render b) : a = b :=
  (render_prefix_free a b [] [] (by simpa using h)).1

/-! ## Statements and conjunctions -/

/-- The six relations. -/
inductive Rel where
  | eq | ne | lt | le | gt | ge
  deriving DecidableEq

open Tok in
/-- The words of a relation. -/
def relWords : Rel → List Tok
  | .eq => [equals]
  | .ne => [does, not_, equal]
  | .lt => [is, less, than]
  | .le => [is, at_, most]
  | .gt => [is, greater, than]
  | .ge => [is, at_, least]

/-- A statement: two terms and a relation. -/
structure Stmt where
  rel : Rel
  lhs : Term
  rhs : Term
  deriving DecidableEq

/-- The sentence of a statement. -/
def renderStmt (s : Stmt) : List Tok :=
  render s.lhs ++ relWords s.rel ++ render s.rhs

theorem relWords_prefix_free (o o' : Rel) (r s : List Tok)
    (h : relWords o ++ r = relWords o' ++ s) : o = o' ∧ r = s := by
  cases o <;> cases o' <;> simp_all [relWords]

/-- Statements are uniquely readable too. -/
theorem renderStmt_prefix_free (s t : Stmt) (r r' : List Tok)
    (h : renderStmt s ++ r = renderStmt t ++ r') : s = t ∧ r = r' := by
  obtain ⟨o, a, b⟩ := s
  obtain ⟨o', a', b'⟩ := t
  simp only [renderStmt, List.append_assoc] at h
  obtain ⟨e₁, h₁⟩ := render_prefix_free _ _ _ _ h
  obtain ⟨e₂, h₂⟩ := relWords_prefix_free _ _ _ _ h₁
  obtain ⟨e₃, e₄⟩ := render_prefix_free _ _ _ _ h₂
  exact ⟨by rw [e₁, e₂, e₃], e₄⟩

theorem renderStmt_injective {s t : Stmt} (h : renderStmt s = renderStmt t) :
    s = t :=
  (renderStmt_prefix_free s t [] [] (by simpa using h)).1

/-- A conjunction: its statements joined by `, and`. -/
def renderConj : List Stmt → List Tok
  | [] => []
  | [s] => renderStmt s
  | s :: t :: rest => renderStmt s ++ [Tok.comma, Tok.and_] ++ renderConj (t :: rest)

/-- Distinct non-empty conjunctions get distinct sentences. -/
theorem renderConj_injective :
    ∀ (l m : List Stmt), l ≠ [] → m ≠ [] → renderConj l = renderConj m →
      l = m := by
  intro l
  induction l with
  | nil => intro m h; exact absurd rfl h
  | cons s l ih =>
      intro m _ hm h
      match l, m, hm with
      | [], [t], _ => simpa [renderConj] using renderStmt_injective h
      | [], t :: u :: rest, _ =>
          simp only [renderConj] at h
          obtain ⟨rfl, h'⟩ := renderStmt_prefix_free s t [] _ (by simpa using h)
          simp at h'
      | l₁ :: l₂, [t], _ =>
          simp only [renderConj] at h
          obtain ⟨rfl, h'⟩ := renderStmt_prefix_free s t _ [] (by simpa using h)
          simp at h'
      | l₁ :: l₂, t :: u :: rest, _ =>
          simp only [renderConj, List.append_assoc] at h
          obtain ⟨rfl, h'⟩ := renderStmt_prefix_free s t _ _ h
          simp only [List.cons_append, List.nil_append, List.cons.injEq,
            true_and] at h'
          have := ih (u :: rest) (by simp) (by simp) h'
          rw [this]

/-! ## The control: infix without scope words is ambiguous -/

/-- The natural infix realiser (`x plus y`), with no scope words. -/
inductive ITok where
  | num : ℚ → ITok
  | name : String → ITok
  | plus | minus | times | divided
  deriving DecidableEq

open ITok in
def infixRender : Term → List ITok
  | .lit q => [num q]
  | .var x => [name x]
  | .add a b => infixRender a ++ [plus] ++ infixRender b
  | .sub a b => infixRender a ++ [minus] ++ infixRender b
  | .mul a b => infixRender a ++ [times] ++ infixRender b
  | .div a b => infixRender a ++ [divided] ++ infixRender b
  | .neg a => [minus] ++ infixRender a
  | .pow a _ => infixRender a

/-- `(x + y) + z` and `x + (y + z)` are different terms with one infix
sentence. -/
theorem infix_not_injective :
    ∃ a b : Term, a ≠ b ∧ infixRender a = infixRender b :=
  ⟨.add (.add (.var "x") (.var "y")) (.var "z"),
   .add (.var "x") (.add (.var "y") (.var "z")),
   by simp, by simp [infixRender]⟩

/-! ## Semantics and negation -/

/-- Evaluation at a point (Lean's `x / 0 = 0`; the Python code refuses a
quotient by zero before it evaluates one). -/
def eval (v : String → ℚ) : Term → ℚ
  | .lit q => q
  | .var x => v x
  | .add a b => eval v a + eval v b
  | .sub a b => eval v a - eval v b
  | .mul a b => eval v a * eval v b
  | .div a b => eval v a / eval v b
  | .neg a => -eval v a
  | .pow a n => eval v a ^ n

def Rel.holds : Rel → ℚ → ℚ → Prop
  | .eq, a, b => a = b
  | .ne, a, b => a ≠ b
  | .lt, a, b => a < b
  | .le, a, b => a ≤ b
  | .gt, a, b => a > b
  | .ge, a, b => a ≥ b

def Stmt.holds (v : String → ℚ) (s : Stmt) : Prop :=
  s.rel.holds (eval v s.lhs) (eval v s.rhs)

/-- The negated relation, as `negate` realises it. -/
def Rel.negate : Rel → Rel
  | .eq => .ne
  | .ne => .eq
  | .lt => .ge
  | .le => .gt
  | .gt => .le
  | .ge => .lt

/-- Negation is exact: the negated statement holds exactly where the
statement fails. -/
theorem negate_exact (v : String → ℚ) (s : Stmt) :
    ({ s with rel := s.rel.negate } : Stmt).holds v ↔ ¬ s.holds v := by
  obtain ⟨o, a, b⟩ := s
  cases o <;> simp [Stmt.holds, Rel.holds, Rel.negate, not_lt, not_le]

/-! ## Entailment and its Farkas certificate -/

/-- One row of a linear system: `∑ a j * x j + k ≤ 0`, or `< 0` when strict. -/
structure Row (n : ℕ) where
  a : Fin n → ℚ
  k : ℚ
  strict : Bool

def Row.value {n : ℕ} (r : Row n) (x : Fin n → ℚ) : ℚ := ∑ j, r.a j * x j + r.k

def Row.sat {n : ℕ} (r : Row n) (x : Fin n → ℚ) : Prop :=
  if r.strict then r.value x < 0 else r.value x ≤ 0

theorem Row.value_nonpos {n : ℕ} {r : Row n} {x : Fin n → ℚ} (h : r.sat x) :
    r.value x ≤ 0 := by
  unfold Row.sat at h; split_ifs at h <;> linarith

/-- A Farkas certificate refutes a system: non-negative multipliers that
cancel every coefficient and leave a positive constant (or a non-negative one
with some strict row weighted) mean no point satisfies every row. -/
theorem farkas_refutes {m n : ℕ} (rows : Fin m → Row n) (lam : Fin m → ℚ)
    (hlam : ∀ i, 0 ≤ lam i) (hcoef : ∀ j, ∑ i, lam i * (rows i).a j = 0)
    (hcontra : 0 < ∑ i, lam i * (rows i).k ∨
      (0 ≤ ∑ i, lam i * (rows i).k ∧ ∃ i, 0 < lam i ∧ (rows i).strict = true)) :
    ¬ ∃ x, ∀ i, (rows i).sat x := by
  rintro ⟨x, hx⟩
  have key : ∑ i, lam i * (rows i).value x = ∑ i, lam i * (rows i).k := by
    simp only [Row.value, mul_add, Finset.sum_add_distrib, Finset.mul_sum]
    have : ∑ i, ∑ j, lam i * ((rows i).a j * x j) = 0 := by
      rw [Finset.sum_comm]
      refine Finset.sum_eq_zero fun j _ => ?_
      have := hcoef j
      calc ∑ i, lam i * ((rows i).a j * x j)
          = (∑ i, lam i * (rows i).a j) * x j := by
            rw [Finset.sum_mul]; exact Finset.sum_congr rfl fun i _ => by ring
        _ = 0 := by rw [this, zero_mul]
    rw [this, zero_add]
  have each : ∀ i, lam i * (rows i).value x ≤ 0 := fun i =>
    mul_nonpos_of_nonneg_of_nonpos (hlam i) (Row.value_nonpos (hx i))
  rcases hcontra with h | ⟨h, i₀, hl, hs⟩
  · have : ∑ i, lam i * (rows i).value x ≤ 0 := Finset.sum_nonpos fun i _ => each i
    linarith
  · have hlt : lam i₀ * (rows i₀).value x < 0 := by
      have := hx i₀
      simp only [Row.sat, hs, if_true] at this
      exact mul_neg_of_pos_of_neg hl this
    have : ∑ i, lam i * (rows i).value x < 0 := by
      calc ∑ i, lam i * (rows i).value x
          < ∑ _i : Fin m, (0 : ℚ) :=
            Finset.sum_lt_sum (fun i _ => each i) ⟨i₀, Finset.mem_univ _, hlt⟩
        _ = 0 := by simp
    linarith

/-- Premises with the negated conclusion having no solution is entailment. -/
theorem entails_of_refuted {α : Type*} (P C : α → Prop)
    (h : ¬ ∃ x, P x ∧ ¬ C x) : ∀ x, P x → C x := by
  intro x hp
  by_contra hc
  exact h ⟨x, hp, hc⟩

/-! ## Pairings: proportional differences are equivalent statements -/

theorem pairing_lt {d₁ d₂ k : ℚ} (hk : 0 < k) (h : d₁ = k * d₂) :
    d₁ < 0 ↔ d₂ < 0 := by
  subst h; constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; nlinarith

theorem pairing_le {d₁ d₂ k : ℚ} (hk : 0 < k) (h : d₁ = k * d₂) :
    d₁ ≤ 0 ↔ d₂ ≤ 0 := by
  subst h; constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; nlinarith

theorem pairing_lt_neg {d₁ d₂ k : ℚ} (hk : k < 0) (h : d₁ = k * d₂) :
    d₁ < 0 ↔ 0 < d₂ := by
  subst h; constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; nlinarith

theorem pairing_le_neg {d₁ d₂ k : ℚ} (hk : k < 0) (h : d₁ = k * d₂) :
    d₁ ≤ 0 ↔ 0 ≤ d₂ := by
  subst h; constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; nlinarith

theorem pairing_eq {d₁ d₂ k : ℚ} (hk : k ≠ 0) (h : d₁ = k * d₂) :
    d₁ = 0 ↔ d₂ = 0 := by
  subst h; simp [hk]

/-! ## The solved form -/

theorem solve_eq {c r x : ℚ} (hc : c ≠ 0) : c * x + r = 0 ↔ x = -r / c := by
  rw [eq_div_iff hc]; constructor <;> intro h <;> linarith

theorem solve_le_pos {c r x : ℚ} (hc : 0 < c) : c * x + r ≤ 0 ↔ x ≤ -r / c := by
  rw [le_div_iff₀ hc]; constructor <;> intro h <;> linarith

theorem solve_le_neg {c r x : ℚ} (hc : c < 0) : c * x + r ≤ 0 ↔ -r / c ≤ x := by
  rw [div_le_iff_of_neg hc]; constructor <;> intro h <;> linarith

/-! ## Polynomial identity on a grid -/

/-- Two polynomials over ℚ whose difference has degree at most `d` in each
variable, and which agree at every point of `{0, …, d}ⁿ`, are equal. -/
theorem grid_identity {σ : Type*} [Finite σ] (P Q : MvPolynomial σ ℚ) (d : ℕ)
    (hdeg : ∀ i, MvPolynomial.degreeOf i (P - Q) ≤ d)
    (hgrid : ∀ x : σ → ℚ, (∀ i, ∃ t : ℕ, t ≤ d ∧ x i = t) →
      MvPolynomial.eval x P = MvPolynomial.eval x Q) : P = Q := by
  have key := MvPolynomial.eq_zero_of_eval_zero_at_prod_finset (P - Q)
    (fun _ => (Finset.range (d + 1)).image (fun t : ℕ => (t : ℚ)))
    (fun i => by
      rw [Finset.card_image_of_injective _ Nat.cast_injective,
        Finset.card_range]
      exact Nat.lt_succ_of_le (hdeg i))
    (fun x hx => by
      rw [map_sub, sub_eq_zero]
      refine hgrid x fun i => ?_
      obtain ⟨t, ht, hxt⟩ := Finset.mem_image.mp (hx i)
      exact ⟨t, Nat.lt_succ_iff.mp (Finset.mem_range.mp ht), hxt.symm⟩)
  exact sub_eq_zero.mp key

end GLM.ReverseTCT
