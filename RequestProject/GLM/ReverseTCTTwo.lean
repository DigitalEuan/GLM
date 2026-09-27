module

public import Mathlib

/-!
# Reverse Three Column Thinking, round two: the widened fragment

The formal half of round two of `studies/REVERSE_TCT_STUDY.md` (§7, Phase 68).

Round two widens `glm_universal/reasoning/reverse_tct.py` with the integer
layer (floor quotient, remainder, minimum, maximum, absolute value), the
bitwise operators, masks (`frozenset` literals and the set operators),
negative exponents, and disjunction, so that a statement is a conjunction of
clauses (conjunctive normal form) and negation is closed under De Morgan.

**The grammar.** As in round one, a literal's spelling is one token
`Tok.num q`, and every head phrase (`the floor quotient of`, `the left shift
of`, …) is one token: that the head phrases are distinct and that the
spellings of numbers are canonical is checked exhaustively in the study's
batteries rather than here.

* `render_prefix_free`, `render_injective` — the widened terms, including the
  count-first mask literal (`the mask of three positions one, two, three`) and
  negative exponents, are uniquely readable.
* `renderStmt_prefix_free`, `renderStmt_injective` — so are the statements
  over the ten relations (the six of round one, `is in`, `is not in`,
  `is contained in`, `is not contained in`).
* `renderClause_prefix_free` — a clause (`either A, or B, or C`) is uniquely
  readable when what follows it is empty or begins `, and`.
* `renderCNF_injective` — distinct conjunctions of non-empty clauses get
  distinct sentences.

**The operations.**

* `negate_product_exact` — negating a conjunction of clauses by distribution
  (one negated atom from each clause, every combination) is exact, for any
  atoms whose negation is exact.
* `simplify_preserves` — the simplification (dropping duplicate atoms and
  clauses, tautologies, and absorbed clauses) keeps the meaning: any clause set
  sandwiched as the theorem states is equivalent to the original.
* `abs_split`, `min_split`, `max_split` — the case splits of the piecewise
  terms are exhaustive and exact.
* `entails_of_cases_refuted` — cases that cover every point, each refuted
  together with the premises and the negated conclusion, give entailment.
* `floor_mod_identity`, `mod_sign_bounds`, `mod_sign_bounds_neg` — Python's
  floor quotient and remainder on rationals: `b * (a // b) + a % b = a`, with
  the remainder taking the sign of the divisor; `py_floor_example`,
  `py_mod_example` check `-17 // 5 = -4` and `-17 % 5 = 3`.
* `chain_floor_misses` — the planner's own twenty-place floored decimal of
  `2/3` lies outside the half-unit interval its rational recognition reads,
  which is why the planner chained to itself does not recover `2/3`, while the
  relay (which hands over the nearest decimal) does.
-/

@[expose] public section

namespace GLM.ReverseTCTTwo

/-! ## The widened terms and their sentences -/

/-- The unary heads: negation, absolute value, complement, size of a mask. -/
inductive Op1 where
  | neg | abs | compl | size
  deriving DecidableEq

/-- The binary heads: the four of round one, the integer layer, the bitwise
operators, the Hamming distance, and the four set operators. -/
inductive Op2 where
  | add | sub | mul | div | floordiv | mod | min | max
  | band | bor | bxor | lshift | rshift | dist
  | inter | union | symdiff | setdiff
  deriving DecidableEq

/-- Column 2: the widened exact terms. -/
inductive Term where
  | lit : ℚ → Term
  | var : String → Term
  | mask : List ℕ → Term
  | un : Op1 → Term → Term
  | bin : Op2 → Term → Term → Term
  | pow : Term → ℤ → Term
  deriving DecidableEq

/-- The words of column 1. -/
inductive Tok where
  | num : ℚ → Tok
  | name : String → Tok
  | h1 : Op1 → Tok
  | h2 : Op2 → Tok
  | the | of | and_ | or_ | either | comma
  | empty | maskW | positions
  | square | cube | power | with_ | exponent
  | equals | does | not_ | equal | is | less | than | at_ | most | greater
  | least | in_ | contained
  deriving DecidableEq

/-- The head word of a power: `square`, `cube`, or `power … with exponent n`
(the exponent may be negative). -/
def powWord (n : ℤ) : Tok :=
  if n = 2 then .square else if n = 3 then .cube else .power

/-- What follows the base of a power. -/
def powTail (n : ℤ) : List Tok :=
  if n = 2 ∨ n = 3 then [] else [.with_, .exponent, .num n]

/-- The positions after the first of a mask literal, each after a comma. -/
def commaNums : List ℕ → List Tok
  | [] => []
  | p :: ps => .comma :: .num (p : ℚ) :: commaNums ps

open Tok in
/-- The realiser: every term is spelled with its head first; a mask literal
says how many positions it has before it lists them. -/
def render : Term → List Tok
  | .lit q => [num q]
  | .var x => [name x]
  | .mask [] => [the, empty, maskW]
  | .mask (p :: ps) =>
      [the, maskW, of, num ((ps.length + 1 : ℕ) : ℚ), positions, num (p : ℚ)] ++
        commaNums ps
  | .un o a => [the, h1 o, of] ++ render a
  | .bin o a b => [the, h2 o, of] ++ render a ++ [and_] ++ render b
  | .pow a n => [the, powWord n, of] ++ render a ++ powTail n

theorem powWord_cases (n : ℤ) :
    powWord n = .square ∨ powWord n = .cube ∨ powWord n = .power := by
  unfold powWord; split_ifs <;> simp

theorem pow_parts_inj {n m : ℤ} {r s : List Tok} (hw : powWord n = powWord m)
    (ht : powTail n ++ r = powTail m ++ s) : n = m ∧ r = s := by
  unfold powWord at hw
  unfold powTail at ht
  by_cases h2 : n = 2 <;> by_cases h3 : n = 3 <;> by_cases h2' : m = 2 <;>
    by_cases h3' : m = 3 <;> simp_all

theorem commaNums_prefix_free :
    ∀ (ps qs : List ℕ) (r s : List Tok), ps.length = qs.length →
      commaNums ps ++ r = commaNums qs ++ s → ps = qs ∧ r = s := by
  intro ps
  induction ps with
  | nil => intro qs r s hl h; cases qs <;> simp_all [commaNums]
  | cons p ps ih =>
      intro qs r s hl h
      cases qs with
      | nil => simp at hl
      | cons q qs =>
          simp only [commaNums, List.cons_append, List.cons.injEq, true_and,
            Tok.num.injEq, Nat.cast_inj] at h
          obtain ⟨rfl, h⟩ := h
          obtain ⟨e, e'⟩ := ih qs r s (by simpa using hl) h
          exact ⟨by rw [e], e'⟩

/-- Unique readability of the widened terms. -/
theorem render_prefix_free :
    ∀ (a b : Term) (r s : List Tok), render a ++ r = render b ++ s →
      a = b ∧ r = s := by
  intro a
  induction a with
  | lit q =>
      intro b r s h
      cases b with
      | mask l => cases l <;> simp_all [render]
      | _ => simp_all [render]
  | var x =>
      intro b r s h
      cases b with
      | mask l => cases l <;> simp_all [render]
      | _ => simp_all [render]
  | mask l =>
      intro b r s h
      cases b with
      | mask l' =>
          cases l with
          | nil => cases l' <;> simp_all [render]
          | cons p ps =>
              cases l' with
              | nil => simp [render] at h
              | cons q qs =>
                  simp only [render, List.cons_append, List.cons.injEq,
                    true_and, Tok.num.injEq, Nat.cast_inj, List.nil_append,
                    Nat.add_right_cancel_iff] at h
                  obtain ⟨hl, rfl, h⟩ := h
                  obtain ⟨e, e'⟩ := commaNums_prefix_free ps qs r s hl h
                  exact ⟨by rw [e], e'⟩
      | pow b n =>
          cases l <;> rcases powWord_cases n with h' | h' | h' <;>
            simp [render, h'] at h
      | _ => cases l <;> simp [render] at h
  | un o a ih =>
      intro b r s h
      cases b with
      | un o' b =>
          simp only [render, List.cons_append, List.nil_append,
            List.cons.injEq, true_and, Tok.h1.injEq] at h
          obtain ⟨rfl, h⟩ := h
          obtain ⟨e₁, e₂⟩ := ih _ _ _ h
          exact ⟨by rw [e₁], e₂⟩
      | mask l => cases l <;> simp [render] at h
      | pow b n => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h
      | _ => simp [render] at h
  | bin o a₁ a₂ ih₁ ih₂ =>
      intro b r s h
      cases b with
      | bin o' b₁ b₂ =>
          simp only [render, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and, Tok.h2.injEq] at h
          obtain ⟨rfl, h⟩ := h
          obtain ⟨e₁, h₁⟩ := ih₁ _ _ _ h
          simp only [List.cons.injEq, true_and] at h₁
          obtain ⟨e₂, e₃⟩ := ih₂ _ _ _ h₁
          exact ⟨by rw [e₁, e₂], e₃⟩
      | mask l => cases l <;> simp [render] at h
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
      | mask l =>
          cases l <;> rcases powWord_cases n with h' | h' | h' <;>
            simp [render, h'] at h
      | _ => rcases powWord_cases n with h' | h' | h' <;> simp [render, h'] at h

/-- Distinct widened terms get distinct sentences. -/
theorem render_injective {a b : Term} (h : render a = render b) : a = b :=
  (render_prefix_free a b [] [] (by simpa using h)).1

/-- No term's sentence begins with `either` (so a clause of two or more
statements is told apart from a single statement by its first word). -/
theorem render_head_ne_either (a : Term) (r s : List Tok) :
    render a ++ r ≠ Tok.either :: s := by
  cases a with
  | mask l => cases l <;> simp [render]
  | _ => simp [render]

/-! ## Statements, clauses and conjunctions -/

/-- The ten relations. -/
inductive Rel where
  | eq | ne | lt | le | gt | ge | mem | notmem | sub | notsub
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
  | .mem => [is, in_]
  | .notmem => [is, not_, in_]
  | .sub => [is, contained, in_]
  | .notsub => [is, not_, contained, in_]

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

theorem renderStmt_ne_either (s : Stmt) (r l : List Tok) :
    renderStmt s ++ r ≠ Tok.either :: l := by
  obtain ⟨o, a, b⟩ := s
  simp only [renderStmt, List.append_assoc]
  exact render_head_ne_either a _ l

/-- The later statements of a clause, each after `, or`. -/
def disjTail : List Stmt → List Tok
  | [] => []
  | s :: rest => [Tok.comma, Tok.or_] ++ renderStmt s ++ disjTail rest

/-- A clause: one statement, or `either A, or B, …`. -/
def renderClause : List Stmt → List Tok
  | [] => []
  | [s] => renderStmt s
  | s :: t :: rest => Tok.either :: (renderStmt s ++ disjTail (t :: rest))

/-- What may follow a clause: nothing, or `, and …`. -/
def Guard (r : List Tok) : Prop := r = [] ∨ ∃ l, r = Tok.comma :: Tok.and_ :: l

theorem disjTail_prefix_free :
    ∀ (l l' : List Stmt) (r r' : List Tok), Guard r → Guard r' →
      disjTail l ++ r = disjTail l' ++ r' → l = l' ∧ r = r' := by
  intro l
  induction l with
  | nil =>
      intro l' r r' hr hr' h
      cases l' with
      | nil => simpa [disjTail] using h
      | cons t rest =>
          exfalso
          rcases hr with rfl | ⟨k, rfl⟩ <;> simp [disjTail] at h
  | cons s rest ih =>
      intro l' r r' hr hr' h
      cases l' with
      | nil =>
          exfalso
          rcases hr' with rfl | ⟨k, rfl⟩ <;> simp [disjTail] at h
      | cons t rest' =>
          simp only [disjTail, List.append_assoc, List.cons_append,
            List.nil_append, List.cons.injEq, true_and] at h
          obtain ⟨e₁, h₁⟩ := renderStmt_prefix_free s t _ _ h
          obtain ⟨e₂, e₃⟩ := ih rest' r r' hr hr' h₁
          exact ⟨by rw [e₁, e₂], e₃⟩

/-- A clause is uniquely readable when what follows it is empty or begins
`, and`. -/
theorem renderClause_prefix_free (c c' : List Stmt) (r r' : List Tok)
    (hc : c ≠ []) (hc' : c' ≠ []) (hr : Guard r) (hr' : Guard r')
    (h : renderClause c ++ r = renderClause c' ++ r') : c = c' ∧ r = r' := by
  match c, c', hc, hc' with
  | [s], [t], _, _ =>
      obtain ⟨e₁, e₂⟩ := renderStmt_prefix_free s t r r' (by simpa [renderClause] using h)
      exact ⟨by rw [e₁], e₂⟩
  | [s], t :: u :: rest, _, _ =>
      exact absurd (by simpa [renderClause] using h) (renderStmt_ne_either s r _)
  | s :: u :: rest, [t], _, _ =>
      exact absurd (by simpa [renderClause] using h.symm) (renderStmt_ne_either t r' _)
  | s :: u :: rest, t :: v :: rest', _, _ =>
      simp only [renderClause, List.cons_append, List.append_assoc,
        List.cons.injEq, true_and] at h
      obtain ⟨e₁, h₁⟩ := renderStmt_prefix_free s t _ _ h
      obtain ⟨e₂, e₃⟩ := disjTail_prefix_free (u :: rest) (v :: rest') r r' hr hr' h₁
      exact ⟨by rw [e₁, e₂], e₃⟩

/-- A conjunction of clauses, joined by `, and`. -/
def renderCNF : List (List Stmt) → List Tok
  | [] => []
  | [c] => renderClause c
  | c :: d :: rest => renderClause c ++ [Tok.comma, Tok.and_] ++ renderCNF (d :: rest)

/-- Distinct non-empty conjunctions of non-empty clauses get distinct
sentences. -/
theorem renderCNF_injective :
    ∀ (l m : List (List Stmt)), l ≠ [] → m ≠ [] → (∀ c ∈ l, c ≠ []) →
      (∀ c ∈ m, c ≠ []) → renderCNF l = renderCNF m → l = m := by
  intro l
  induction l with
  | nil => intro m h; exact absurd rfl h
  | cons c l ih =>
      intro m _ hm hl hm' h
      match l, m, hm with
      | [], [d], _ =>
          obtain ⟨e, -⟩ := renderClause_prefix_free c d [] []
            (hl c (by simp)) (hm' d (by simp)) (Or.inl rfl) (Or.inl rfl)
            (by simpa [renderCNF] using h)
          rw [e]
      | [], d :: e :: rest, _ =>
          simp only [renderCNF] at h
          obtain ⟨-, h'⟩ := renderClause_prefix_free c d []
            ([Tok.comma, Tok.and_] ++ renderCNF (e :: rest))
            (hl c (by simp)) (hm' d (by simp)) (Or.inl rfl)
            (Or.inr ⟨_, rfl⟩) (by simpa using h)
          simp at h'
      | l₁ :: l₂, [d], _ =>
          simp only [renderCNF] at h
          obtain ⟨-, h'⟩ := renderClause_prefix_free c d
            ([Tok.comma, Tok.and_] ++ renderCNF (l₁ :: l₂)) []
            (hl c (by simp)) (hm' d (by simp)) (Or.inr ⟨_, rfl⟩)
            (Or.inl rfl) (by simpa using h)
          simp at h'
      | l₁ :: l₂, d :: e :: rest, _ =>
          simp only [renderCNF, List.append_assoc] at h
          obtain ⟨rfl, h'⟩ := renderClause_prefix_free c d
            ([Tok.comma, Tok.and_] ++ renderCNF (l₁ :: l₂))
            ([Tok.comma, Tok.and_] ++ renderCNF (e :: rest))
            (hl c (by simp)) (hm' d (by simp)) (Or.inr ⟨_, rfl⟩)
            (Or.inr ⟨_, rfl⟩) h
          simp only [List.cons_append, List.nil_append, List.cons.injEq,
            true_and] at h'
          have := ih (e :: rest) (by simp) (by simp)
            (fun c hc => hl c (List.mem_cons_of_mem _ hc))
            (fun c hc => hm' c (List.mem_cons_of_mem _ hc)) h'
          rw [this]

/-! ## Negation by distribution -/

section Negation

variable {α : Type*} (h : α → Prop)

/-- A conjunction of clauses holds when every clause has an atom that holds. -/
def CNFHolds (cs : List (List α)) : Prop := ∀ c ∈ cs, ∃ a ∈ c, h a

theorem sections_exists_iff (P : α → Prop) :
    ∀ L : List (List α),
      (∀ s ∈ L.sections, ∃ a ∈ s, P a) ↔ ∃ l ∈ L, ∀ a ∈ l, P a := by
  intro L
  induction L with
  | nil => simp
  | cons l L ih =>
      simp only [List.sections, List.mem_flatMap, List.mem_map,
        forall_exists_index, and_imp, List.mem_cons, exists_eq_or_imp]
      constructor
      · intro H
        by_contra hne
        push_neg at hne
        obtain ⟨hl, hL⟩ := hne
        obtain ⟨a, ha, hPa⟩ := hl
        have : ¬ ∀ s ∈ L.sections, ∃ a ∈ s, P a := by
          rw [ih]; push_neg; exact hL
        push_neg at this
        obtain ⟨s, hs, hsP⟩ := this
        obtain ⟨b, hb, hPb⟩ := H _ s hs _ ha rfl
        simp only [List.mem_cons] at hb
        rcases hb with rfl | hb
        · exact hPa hPb
        · exact hsP b hb hPb
      · rintro (hl | hL) t s hs a ha rfl
        · exact ⟨a, by simp, hl a ha⟩
        · obtain ⟨b, hb, hPb⟩ := ih.2 hL s hs
          exact ⟨b, by simp [hb], hPb⟩

/-- Negation by distribution is exact: when each atom's negation `n a` holds
exactly where `a` fails, the clauses formed by choosing one negated atom from
each clause, in every combination, hold exactly where the conjunction
fails. -/
theorem negate_product_exact (n : α → α) (hn : ∀ a, h (n a) ↔ ¬ h a)
    (cs : List (List α)) :
    CNFHolds h (cs.map (List.map n)).sections ↔ ¬ CNFHolds h cs := by
  unfold CNFHolds
  rw [sections_exists_iff h (cs.map (List.map n))]
  constructor
  · rintro ⟨l, hl, hall⟩ H
    obtain ⟨c, hc, rfl⟩ := List.mem_map.1 hl
    obtain ⟨a, ha, hha⟩ := H c hc
    exact (hn a).1 (hall (n a) (List.mem_map_of_mem ha)) hha
  · intro H
    push_neg at H
    obtain ⟨c, hc, hall⟩ := H
    refine ⟨c.map n, List.mem_map_of_mem hc, ?_⟩
    intro b hb
    obtain ⟨a, ha, rfl⟩ := List.mem_map.1 hb
    exact (hn a).2 (hall a ha)

/-- The simplification keeps the meaning. `cs'` is the simplified clause set:
every clause kept contains (as a set) some original clause, and every original
clause is a tautology (an atom and its negation) or contains some kept clause.
Dropping duplicate atoms, duplicate clauses, tautologies and absorbed clauses
all produce such a `cs'`. -/
theorem simplify_preserves (n : α → α) (hn : ∀ a, h (n a) ↔ ¬ h a)
    (cs cs' : List (List α))
    (hkept : ∀ c' ∈ cs', ∃ c ∈ cs, ∀ a ∈ c, a ∈ c')
    (hcover : ∀ c ∈ cs, (∃ a ∈ c, n a ∈ c) ∨ ∃ c' ∈ cs', ∀ a ∈ c', a ∈ c) :
    CNFHolds h cs' ↔ CNFHolds h cs := by
  unfold CNFHolds
  constructor
  · intro H c hc
    rcases hcover c hc with ⟨a, ha, hna⟩ | ⟨c', hc', hsub⟩
    · by_cases hA : h a
      · exact ⟨a, ha, hA⟩
      · exact ⟨n a, hna, (hn a).2 hA⟩
    · obtain ⟨a, ha, hha⟩ := H c' hc'
      exact ⟨a, hsub a ha, hha⟩
  · intro H c' hc'
    obtain ⟨c, hc, hsub⟩ := hkept c' hc'
    obtain ⟨a, ha, hha⟩ := H c hc
    exact ⟨a, hsub a ha, hha⟩

end Negation

/-! ## Piecewise terms: the case splits -/

/-- The absolute value splits on the sign of its argument. -/
theorem abs_split (P : ℚ → Prop) (t : ℚ) :
    P |t| ↔ (0 ≤ t ∧ P t) ∨ (t < 0 ∧ P (-t)) := by
  rcases le_or_gt 0 t with h | h
  · simp [abs_of_nonneg h, h, not_lt.mpr h]
  · simp [abs_of_neg h, h, not_le.mpr h]

/-- The minimum splits on which argument is smaller. -/
theorem min_split (P : ℚ → Prop) (a b : ℚ) :
    P (min a b) ↔ (a ≤ b ∧ P a) ∨ (b < a ∧ P b) := by
  rcases le_or_gt a b with h | h
  · simp [h, not_lt.mpr h]
  · simp [min_eq_right h.le, h, not_le.mpr h]

/-- The maximum splits on which argument is larger. -/
theorem max_split (P : ℚ → Prop) (a b : ℚ) :
    P (max a b) ↔ (b ≤ a ∧ P a) ∨ (a < b ∧ P b) := by
  rcases le_or_gt b a with h | h
  · simp [h, not_lt.mpr h]
  · simp [max_eq_right h.le, h, not_le.mpr h]

/-- Cases that cover every point, each refuted together with the premises and
the negated conclusion, give entailment. -/
theorem entails_of_cases_refuted {β : Type*} (P C : β → Prop) (G : List (β → Prop))
    (hcover : ∀ x, ∃ g ∈ G, g x)
    (hrefuted : ∀ g ∈ G, ¬ ∃ x, g x ∧ P x ∧ ¬ C x) : ∀ x, P x → C x := by
  intro x hp
  by_contra hc
  obtain ⟨g, hg, hgx⟩ := hcover x
  exact hrefuted g hg ⟨x, hgx, hp, hc⟩

/-! ## Python's floor quotient and remainder -/

/-- Python's `a // b` on rationals. -/
def pyFloorDiv (a b : ℚ) : ℤ := ⌊a / b⌋

/-- Python's `a % b` on rationals. -/
def pyMod (a b : ℚ) : ℚ := a - b * pyFloorDiv a b

/-- `b * (a // b) + a % b = a`. -/
theorem floor_mod_identity (a b : ℚ) : b * pyFloorDiv a b + pyMod a b = a := by
  unfold pyMod; ring

/-- With a positive divisor the remainder lies in `[0, b)`. -/
theorem mod_sign_bounds (a b : ℚ) (hb : 0 < b) : 0 ≤ pyMod a b ∧ pyMod a b < b := by
  unfold pyMod pyFloorDiv
  have h1 := Int.floor_le (a / b)
  have h2 := Int.lt_floor_add_one (a / b)
  have e : b * (a / b) = a := by rw [mul_comm]; exact div_mul_cancel₀ a hb.ne'
  constructor <;> nlinarith

/-- With a negative divisor the remainder lies in `(b, 0]`. -/
theorem mod_sign_bounds_neg (a b : ℚ) (hb : b < 0) : b < pyMod a b ∧ pyMod a b ≤ 0 := by
  unfold pyMod pyFloorDiv
  have h1 := Int.floor_le (a / b)
  have h2 := Int.lt_floor_add_one (a / b)
  have e : b * (a / b) = a := by rw [mul_comm]; exact div_mul_cancel₀ a hb.ne
  constructor <;> nlinarith

theorem py_floor_example : pyFloorDiv (-17) 5 = -4 := by
  unfold pyFloorDiv
  rw [Int.floor_eq_iff]; norm_num

theorem py_mod_example : pyMod (-17) 5 = 3 := by
  unfold pyMod; rw [py_floor_example]; norm_num

/-! ## Why the planner chained to itself misses `2/3` -/

/-- The planner's twenty-place decimal of `2/3` is floored
(`0.66666666666666666666`), and its rational recognition reads a decimal of
twenty places as the interval of half a unit in the last place around it:
`2/3` is not in that interval. -/
theorem chain_floor_misses :
    ¬ |(2 / 3 : ℚ) - 66666666666666666666 / 10 ^ 20| ≤ 1 / (2 * 10 ^ 20) := by
  norm_num [abs_of_pos]

/-- The relay hands over the nearest decimal (`0.66666666666666666667`),
whose half-unit interval does contain `2/3`. -/
theorem relay_nearest_hits :
    |(2 / 3 : ℚ) - 66666666666666666667 / 10 ^ 20| ≤ 1 / (2 * 10 ^ 20) := by
  norm_num [abs_le]

end GLM.ReverseTCTTwo
