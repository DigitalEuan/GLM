module

public import Mathlib

/-!
# The AST index: why one bucket is enough, and what a match is worth

`studies/AST_INDEX_STUDY.md` (Phase 105) indexes the statement-level
expressions of the live code and of the archived GLM tree by a *bucket key*
— the form with every variable erased and the operands of each commutative
operator put in a fixed order — and decides *structural equality* (equal
under a renaming of variables and a choice of operand order at commutative
nodes) inside the bucket
(`glm_universal/reasoning/ast_index.py`).  This file proves, on a
model of integer expressions, the two facts the operation rests on.

## 1.  A match is sound on arithmetic

`structEq_sound`: if renaming the variables of `s` by `σ` gives a term equal
to `t` up to operand order at commutative nodes, then `t` under `ρ` has the
value `s` has under `ρ ∘ σ`.  This is mark A6's claim for every environment,
not only the five the measurement evaluates.  Injectivity of `σ` is not
needed for soundness; the matcher's renaming is one to one so that the
relation is symmetric.

## 2.  The bucket is complete

`bucket_complete`: the same hypothesis puts `s` and `t` under one key.  So
an answer that searches only the query's bucket loses no structurally equal
site, and an empty answer is an answer: no other bucket can hold a match.
`key_sub_ne_add` shows the key is not constant.

## 3.  The edges of the relation

`sub_not_comm`: subtraction is not commutative, so the swap is allowed only
at commutative operators.  `string_append_not_comm`: string concatenation is
not commutative, so treating `+` as commutative is sound only on numbers —
the four index classes that commute `+` across a string constant are counted
and reported rather than claimed.  `assoc_by_renaming`: `(a + b) + c` and
`a + (b + c)` are structurally equal by a renaming and one swap, with no
associativity — the pair the study's cases declared unequal by mistake.
-/

@[expose] public section

namespace GLM.AstIndex

/-- The binary operators of the model. -/
inductive Op
  | add
  | mul
  | sub
  deriving DecidableEq

/-- Whether the two operands of an operator may be swapped. -/
def Op.comm : Op → Bool
  | .add => true
  | .mul => true
  | .sub => false

/-- An operator's value on two integers. -/
def Op.eval : Op → ℤ → ℤ → ℤ
  | .add => fun x y => x + y
  | .mul => fun x y => x * y
  | .sub => fun x y => x - y

theorem Op.eval_comm {o : Op} (h : o.comm = true) (x y : ℤ) :
    o.eval x y = o.eval y x := by
  cases o
  · exact add_comm x y
  · exact mul_comm x y
  · simp [Op.comm] at h

/-- Integer expressions: numbered variables, literals, binary operators. -/
inductive Tm
  | var : ℕ → Tm
  | lit : ℤ → Tm
  | bin : Op → Tm → Tm → Tm
  deriving DecidableEq

/-- The value of a term in an environment. -/
def eval (ρ : ℕ → ℤ) : Tm → ℤ
  | .var i => ρ i
  | .lit z => z
  | .bin o a b => o.eval (eval ρ a) (eval ρ b)

/-- Renaming the variables of a term. -/
def rename (σ : ℕ → ℕ) : Tm → Tm
  | .var i => .var (σ i)
  | .lit z => .lit z
  | .bin o a b => .bin o (rename σ a) (rename σ b)

/-- Equal up to the order of the operands at commutative operators. -/
inductive CommEq : Tm → Tm → Prop
  | refl (t : Tm) : CommEq t t
  | symm {s t : Tm} : CommEq s t → CommEq t s
  | trans {s t u : Tm} : CommEq s t → CommEq t u → CommEq s u
  | cong {o : Op} {a a' b b' : Tm} :
      CommEq a a' → CommEq b b' → CommEq (.bin o a b) (.bin o a' b')
  | swap {o : Op} (a b : Tm) : o.comm = true → CommEq (.bin o a b) (.bin o b a)

/-- Renaming commutes with evaluation. -/
theorem eval_rename (ρ : ℕ → ℤ) (σ : ℕ → ℕ) (t : Tm) :
    eval ρ (rename σ t) = eval (ρ ∘ σ) t := by
  induction t with
  | var i => rfl
  | lit z => rfl
  | bin o a b iha ihb => simp [eval, rename, iha, ihb]

/-- Operand order at commutative operators does not change a value. -/
theorem commEq_eval {s t : Tm} (h : CommEq s t) (ρ : ℕ → ℤ) :
    eval ρ s = eval ρ t := by
  induction h with
  | refl => rfl
  | symm _ ih => exact ih.symm
  | trans _ _ ih1 ih2 => exact ih1.trans ih2
  | cong _ _ iha ihb => simp [eval, iha, ihb]
  | swap a b hc => exact Op.eval_comm hc _ _

/-- **A match is sound.**  If `rename σ s` equals `t` up to operand order,
`t` under `ρ` has the value `s` has under `ρ ∘ σ`. -/
theorem structEq_sound {s t : Tm} {σ : ℕ → ℕ} (h : CommEq (rename σ s) t)
    (ρ : ℕ → ℤ) : eval ρ t = eval (ρ ∘ σ) s := by
  rw [← commEq_eval h ρ, eval_rename]

/-- The code of an operator in the key. -/
def Op.code : Op → ℕ
  | .add => 0
  | .mul => 1
  | .sub => 2

/-- The bucket key: variables erased, a commutative operator's two operand
keys taken in increasing order. -/
def key : Tm → ℕ
  | .var _ => 0
  | .lit z => Nat.pair 1 (Encodable.encode z)
  | .bin o a b =>
      if o.comm then Nat.pair (2 + o.code) (Nat.pair (min (key a) (key b))
        (max (key a) (key b)))
      else Nat.pair (2 + o.code) (Nat.pair (key a) (key b))

/-- No renaming moves the key. -/
theorem key_rename (σ : ℕ → ℕ) (t : Tm) : key (rename σ t) = key t := by
  induction t with
  | var i => rfl
  | lit z => rfl
  | bin o a b iha ihb => simp [key, rename, iha, ihb]

/-- No change of operand order at a commutative operator moves the key. -/
theorem key_commEq {s t : Tm} (h : CommEq s t) : key s = key t := by
  induction h with
  | refl => rfl
  | symm _ ih => exact ih.symm
  | trans _ _ ih1 ih2 => exact ih1.trans ih2
  | cong _ _ iha ihb => simp [key, iha, ihb]
  | swap a b hc => simp [key, hc, min_comm, max_comm]

/-- **The bucket is complete.**  Structurally equal terms share a key, so
searching the query's bucket loses no match. -/
theorem bucket_complete {s t : Tm} {σ : ℕ → ℕ} (h : CommEq (rename σ s) t) :
    key s = key t := by
  rw [← key_rename σ s]
  exact key_commEq h

/-- The key is not constant: `x - y` and `x + y` fall in different buckets. -/
theorem key_sub_ne_add :
    key (.bin .sub (.var 0) (.var 1)) ≠ key (.bin .add (.var 0) (.var 1)) := by
  simp only [key, Op.comm, Op.code, if_false, if_true, Bool.false_eq_true]
  intro h
  have := congrArg (fun n => (Nat.unpair n).1) h
  simp at this

/-- Subtraction is not commutative: the swap must be restricted. -/
theorem sub_not_comm :
    ∃ ρ : ℕ → ℤ, eval ρ (.bin .sub (.var 0) (.var 1)) ≠
      eval ρ (.bin .sub (.var 1) (.var 0)) :=
  ⟨fun i => (i : ℤ), by simp [eval, Op.eval]⟩

/-- String concatenation is not commutative: commuting `+` is sound only on
numbers. -/
theorem string_append_not_comm : ("a" ++ "b" : String) ≠ "b" ++ "a" := by
  decide

/-- `(a + b) + c` and `a + (b + c)` are structurally equal by a renaming and
one swap: no associativity is used. -/
theorem assoc_by_renaming :
    CommEq (rename (fun i => if i = 0 then 1 else if i = 1 then 2 else 0)
        (.bin .add (.bin .add (.var 0) (.var 1)) (.var 2)))
      (.bin .add (.var 0) (.bin .add (.var 1) (.var 2))) := by
  simp only [rename, if_true, show (1 : ℕ) ≠ 0 from by decide,
    show (2 : ℕ) ≠ 0 from by decide, show (2 : ℕ) ≠ 1 from by decide, if_false]
  exact CommEq.swap _ _ rfl

end GLM.AstIndex
