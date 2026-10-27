module

public import Mathlib

/-!
# Round 28: local-rule induction on any grid, with any reader

`WheelInduction.lean` (Round 10) proved, for the 256 one-dimensional wheels, that the GLM's
induction discipline — *keep every rule that fits, answer only if all of them agree* — is the same
as *answer only if every neighbourhood the query needs has been seen*.  This file proves the same
facts in the generality an ARC solver needs:

* a **grid** type `G` with a set of cells `cells g` (any shape, any number of positions);
* a **reader** `read g p : K` — what the observer `Y` sees at cell `p` (the cell itself, its
  `3 × 3` block, the first colour seen looking north, …);
* optionally **slots** `slot g p : S` and a **decoder** `dec : E → S → C`, so that an output can be
  read *relative* to the reader ("copy the colour seen to the west") rather than as an absolute
  colour.  A rule is `f : K → E`, and its prediction at `p` is `dec (f (read g p)) (slot g p)`.

The plain table (`E = C`, `dec e _ = e`) is the special case used for wheels.

## Results (all `FORMAL`, standard axioms only)

* `reproduces_iff_keyOK` — a rule reproduces the demonstrations iff, key by key, its entry is
  consistent with every demonstration cell carrying that key.  Rules are chosen **independently
  per key** (the survivors form a product).
* `consistent_iff` — some rule reproduces the demonstrations iff every key has a consistent entry.
* `determined_iff_keyDetermined` — for a consistent set of demonstrations, all surviving rules
  agree at a query cell iff all consistent entries for its key decode to the same colour there.
* `determined_iff_seen` (plain tables, at least two colours) — **all survivors agree at a query
  cell iff its key has been seen.**  The refusal rule is exact: refuse iff an unseen key is needed.
* `answer_determined_iff_covered` — the grid-level form: all survivors produce the same answer on
  the query grid iff every key it needs has been seen.
* `survivor_correct` — *lock-in*: if the true transformation is a rule over the reader and every
  query key has been seen, every surviving rule gives the true answer.
* `clash_refutes` — two demonstration cells with the same key and different outputs refute the
  reader for good: no plain rule over it reproduces any larger set of demonstrations.
* `keyOK_antitone`, `not_consistent_mono` — more demonstrations only remove survivors (pruning is
  permanent: the "tuning by ear" property of `TuningByEar.lean`).

The GLM implementation is `rule30_round28/glm_overlay/glm_universal/reasoning/local_rule_induction.py`
in the study folder; its measured effect on the stored ARC tasks is reported in the package README
(Round 28).
-/

@[expose] public section

namespace GLM.LocalRule

variable {G P K S E C : Type*}

/-- One demonstration: an input grid and its output colouring. -/
abbrev Demo (G P C : Type*) := G × (P → C)

/-- The setting: which cells a grid has, what the reader sees, the slots and the decoder. -/
structure Reading (G P K S E C : Type*) where
  cells : G → Set P
  read : G → P → K
  slot : G → P → S
  dec : E → S → C

variable (R : Reading G P K S E C)

/-- The prediction of rule `f` at cell `p` of grid `g`. -/
def Reading.predict (f : K → E) (g : G) (p : P) : C := R.dec (f (R.read g p)) (R.slot g p)

/-- Rule `f` reproduces every demonstration on every cell. -/
def Reading.Reproduces (demos : List (Demo G P C)) (f : K → E) : Prop :=
  ∀ d ∈ demos, ∀ p ∈ R.cells d.1, R.predict f d.1 p = d.2 p

/-- Entry `e` for key `k` is consistent with every demonstration cell that carries key `k`. -/
def Reading.KeyOK (demos : List (Demo G P C)) (k : K) (e : E) : Prop :=
  ∀ d ∈ demos, ∀ p ∈ R.cells d.1, R.read d.1 p = k → R.dec e (R.slot d.1 p) = d.2 p

/-- Key `k` occurs in some demonstration. -/
def Reading.Seen (demos : List (Demo G P C)) (k : K) : Prop :=
  ∃ d ∈ demos, ∃ p ∈ R.cells d.1, R.read d.1 p = k

variable {R}

/-- **Rules are chosen key by key.** A rule reproduces the demonstrations iff each of its
entries is consistent with the cells carrying that key. -/
theorem reproduces_iff_keyOK (demos : List (Demo G P C)) (f : K → E) :
    R.Reproduces demos f ↔ ∀ k, R.KeyOK demos k (f k) := by
  constructor
  · rintro h k d hd p hp rfl
    exact h d hd p hp
  · intro h d hd p hp
    exact h _ d hd p hp rfl

/-- **Consistency is per key.** Some rule reproduces the demonstrations iff every key has a
consistent entry. -/
theorem consistent_iff (demos : List (Demo G P C)) :
    (∃ f, R.Reproduces demos f) ↔ ∀ k, ∃ e, R.KeyOK demos k e := by
  constructor
  · rintro ⟨f, hf⟩ k
    exact ⟨f k, (reproduces_iff_keyOK demos f).1 hf k⟩
  · intro h
    choose f hf using h
    exact ⟨f, (reproduces_iff_keyOK demos f).2 hf⟩

/-- Changing a surviving rule at one key, to another consistent entry, keeps it a survivor. -/
theorem reproduces_update [DecidableEq K] {demos : List (Demo G P C)} {f : K → E}
    (hf : R.Reproduces demos f) {k : K} {e : E} (he : R.KeyOK demos k e) :
    R.Reproduces demos (Function.update f k e) := by
  rw [reproduces_iff_keyOK] at hf ⊢
  intro k'
  by_cases hk : k' = k
  · subst hk; simpa using he
  · simpa [Function.update_of_ne hk] using hf k'

/-- **Determinacy, general form.** For consistent demonstrations, every pair of surviving rules
agrees at a query cell with key `k` and slots `s` iff every pair of consistent entries for `k`
decodes to the same colour at `s`. -/
theorem determined_iff_keyDetermined {demos : List (Demo G P C)}
    (hcons : ∃ f, R.Reproduces demos f) (k : K) (s : S) :
    (∀ f f', R.Reproduces demos f → R.Reproduces demos f' → R.dec (f k) s = R.dec (f' k) s) ↔
      (∀ e e', R.KeyOK demos k e → R.KeyOK demos k e' → R.dec e s = R.dec e' s) := by
  classical
  constructor
  · intro h e e' he he'
    obtain ⟨f, hf⟩ := hcons
    have := h _ _ (reproduces_update hf he) (reproduces_update hf he')
    simpa using this
  · intro h f f' hf hf'
    exact h _ _ ((reproduces_iff_keyOK demos f).1 hf k) ((reproduces_iff_keyOK demos f').1 hf' k)

/-- More demonstrations only remove consistent entries. -/
theorem keyOK_antitone {demos demos' : List (Demo G P C)} (hsub : demos ⊆ demos') {k : K} {e : E}
    (h : R.KeyOK demos' k e) : R.KeyOK demos k e :=
  fun d hd => h d (hsub hd)

/-- **Pruning is permanent.** If no rule reproduces some demonstrations, no rule reproduces any
larger set of demonstrations. -/
theorem not_consistent_mono {demos demos' : List (Demo G P C)} (hsub : demos ⊆ demos')
    (h : ¬ ∃ f, R.Reproduces demos f) : ¬ ∃ f, R.Reproduces demos' f := by
  rintro ⟨f, hf⟩
  exact h ⟨f, fun d hd => hf d (hsub hd)⟩

/-! ## Plain tables: the output is the entry itself -/

/-- A plain reading: the rule's entry is the output colour (no slots). -/
def plain (cells : G → Set P) (read : G → P → K) : Reading G P K Unit C C :=
  ⟨cells, read, fun _ _ => (), fun e _ => e⟩

variable {cells : G → Set P} {read : G → P → K}

theorem plain_keyOK_iff (demos : List (Demo G P C)) (k : K) (e : C) :
    (plain cells read).KeyOK demos k e ↔
      ∀ d ∈ demos, ∀ p ∈ cells d.1, read d.1 p = k → e = d.2 p := Iff.rfl

/-- **The refusal rule is exact.** For plain tables over at least two colours and consistent
demonstrations, all surviving rules agree on key `k` iff `k` has been seen. -/
theorem determined_iff_seen [Nontrivial C] {demos : List (Demo G P C)}
    (hcons : ∃ f, (plain cells read).Reproduces demos f) (k : K) :
    (∀ f f', (plain cells read).Reproduces demos f → (plain cells read).Reproduces demos f' →
        f k = f' k) ↔ (plain cells read).Seen demos k := by
  refine (determined_iff_keyDetermined hcons k ()).trans ?_
  change (∀ e e' : C, (plain cells read).KeyOK demos k e → (plain cells read).KeyOK demos k e' →
    e = e') ↔ _
  constructor
  · intro h
    by_contra hns
    obtain ⟨a, b, hab⟩ := exists_pair_ne C
    refine hab (h a b ?_ ?_) <;>
    · intro d hd p hp hk
      exact absurd ⟨d, hd, p, hp, hk⟩ hns
  · rintro ⟨d, hd, p, hp, rfl⟩ e e' he he'
    exact (he d hd p hp rfl).trans (he' d hd p hp rfl).symm

/-- **Grid-level determinacy.** For plain tables over at least two colours and consistent
demonstrations, all surviving rules give the same answer on every cell of the query grid `q` iff
every key that `q` needs has been seen. -/
theorem answer_determined_iff_covered [Nontrivial C] {demos : List (Demo G P C)}
    (hcons : ∃ f, (plain cells read).Reproduces demos f) (q : G) :
    (∀ f f', (plain cells read).Reproduces demos f → (plain cells read).Reproduces demos f' →
        ∀ p ∈ cells q, f (read q p) = f' (read q p)) ↔
      ∀ p ∈ cells q, (plain cells read).Seen demos (read q p) := by
  constructor
  · intro h p hp
    exact (determined_iff_seen hcons _).1 fun f f' hf hf' => h f f' hf hf' p hp
  · intro h f f' hf hf' p hp
    exact (determined_iff_seen hcons _).2 (h p hp) f f' hf hf'

/-- **Lock-in.** If the true transformation is a plain rule `f₀` over the reader (it reproduces
the demonstrations and gives the true answer `o` on the query `q`), and every key `q` needs has
been seen, then every surviving rule gives exactly the true answer. -/
theorem survivor_correct {demos : List (Demo G P C)} {f₀ : K → C}
    (h₀ : (plain cells read).Reproduces demos f₀) {q : G} {o : P → C}
    (ho : ∀ p ∈ cells q, f₀ (read q p) = o p)
    (hcov : ∀ p ∈ cells q, (plain cells read).Seen demos (read q p))
    {f : K → C} (hf : (plain cells read).Reproduces demos f) :
    ∀ p ∈ cells q, f (read q p) = o p := by
  intro p hp
  obtain ⟨d, hd, p', hp', hk⟩ := hcov p hp
  rw [← ho p hp, ← hk]
  exact (hf d hd p' hp').trans (h₀ d hd p' hp').symm

/-- **A clash refutes the reader for good.** Two demonstration cells with the same key and
different outputs: no plain rule over this reader reproduces any set of demonstrations that
contains both. -/
theorem clash_refutes {demos demos' : List (Demo G P C)} (hsub : demos ⊆ demos')
    {d₁ d₂ : Demo G P C} (h₁ : d₁ ∈ demos) (h₂ : d₂ ∈ demos) {p₁ p₂ : P}
    (hp₁ : p₁ ∈ cells d₁.1) (hp₂ : p₂ ∈ cells d₂.1) (hk : read d₁.1 p₁ = read d₂.1 p₂)
    (hc : d₁.2 p₁ ≠ d₂.2 p₂) : ¬ ∃ f, (plain cells read).Reproduces demos' f := by
  rintro ⟨f, hf⟩
  have e₁ := hf d₁ (hsub h₁) p₁ hp₁
  have e₂ := hf d₂ (hsub h₂) p₂ hp₂
  simp only [Reading.predict, plain] at e₁ e₂
  exact hc (by rw [← e₁, ← e₂, hk])

/-- **Consistency of plain tables is exactly the absence of clashes** (for a non-empty colour
set). -/
theorem plain_consistent_iff [Nonempty C] (demos : List (Demo G P C)) :
    (∃ f, (plain cells read).Reproduces demos f) ↔
      ∀ d₁ ∈ demos, ∀ d₂ ∈ demos, ∀ p₁ ∈ cells d₁.1, ∀ p₂ ∈ cells d₂.1,
        read d₁.1 p₁ = read d₂.1 p₂ → d₁.2 p₁ = d₂.2 p₂ := by
  classical
  constructor
  · rintro hcons d₁ h₁ d₂ h₂ p₁ hp₁ p₂ hp₂ hk
    by_contra hc
    exact clash_refutes (List.Subset.refl _) h₁ h₂ hp₁ hp₂ hk hc hcons
  · intro h
    rw [consistent_iff]
    intro k
    by_cases hs : (plain cells read).Seen demos k
    · obtain ⟨d, hd, p, hp, hk⟩ := hs
      refine ⟨d.2 p, fun d' hd' p' hp' hk' => ?_⟩
      exact h d hd d' hd' p hp p' hp' (hk.trans hk'.symm)
    · exact ⟨Classical.arbitrary C, fun d hd p hp hk => absurd ⟨d, hd, p, hp, hk⟩ hs⟩

end GLM.LocalRule
