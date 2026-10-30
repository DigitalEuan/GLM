module

public import RequestProject.GLM.PlannerLadder

/-!
# The machine reads what it carries (Phase 153)

The formal half of `studies/CARRIED_READ_STUDY.md`. Phase 151 said every chain
of the stepwise planner as a GLM-BAT program, but the machine took every
*carried* step — a register value, a given — as data: a lie there was seen only
downstream, if at all. This round gives the machine its own copy of the
registers, written as files (`reg/<table>.txt`, one line `@key=value;` per
entry), and the question's numbers (`q.txt`), and a carried step becomes a
**read**: the step's file is written only when `FIND` finds the claimed entry.

* `sep_cancel` — a separator that occurs in neither left part splits two
  lists at the same place.
* `line_infix_iff` — **the read is exact.** With keys and values free of the
  three delimiters `@`, `=`, `;`, the needle `@k=v;` occurs in the line
  `@k'=v';` exactly when `k = k'` and `v = v'`: `FIND`'s substring test is an
  equality test on these lines.
* `find_iff_mem` — so `FIND` finds `@k=v;` in a register file exactly when the
  register holds the entry `(k, v)`; `find_iff_eq` — and, keys being unique,
  exactly when `v` is the register's value at `k`.
* `honest_no_drift`, `first_lie_drifts` — over a chain with computed steps,
  checked reads and unchecked carried steps: an honest chain never drifts, and
  the **first** lie drifts at its own step, whether it is computed or read,
  with no drift before it.
* `no_drift_iff` — when every step the machine does not compute is an exact
  read, no drift holds exactly when the chain is honest.
-/

@[expose] public section

namespace GLM.CarriedRead

/-! ## The register line and `FIND` -/

/-- A separator absent from both left parts splits two lists at the same
place. -/
theorem sep_cancel {α : Type*} {c : α} :
    ∀ {k k' a b : List α}, c ∉ k → c ∉ k' → k ++ c :: a = k' ++ c :: b →
      k = k' ∧ a = b
  | [], [], _, _, _, _, h => by simpa using h
  | [], x :: k', _, _, _, hk', h => by
      simp only [List.nil_append, List.cons_append, List.cons.injEq] at h
      exact absurd (h.1 ▸ List.mem_cons_self) hk'
  | x :: k, [], _, _, hk, _, h => by
      simp only [List.nil_append, List.cons_append, List.cons.injEq] at h
      exact absurd (h.1 ▸ List.mem_cons_self) hk
  | x :: k, y :: k', a, b, hk, hk', h => by
      simp only [List.cons_append, List.cons.injEq] at h
      obtain ⟨rfl, h⟩ := h
      have := sep_cancel (fun m => hk (List.mem_cons_of_mem _ m))
        (fun m => hk' (List.mem_cons_of_mem _ m)) h
      exact ⟨by rw [this.1], this.2⟩

/-- The register line `@k=v;`. -/
def line (k v : List Char) : List Char := '@' :: (k ++ '=' :: (v ++ [';']))

/-- A key or value free of the three delimiters. -/
def Clean (s : List Char) : Prop := '@' ∉ s ∧ '=' ∉ s ∧ ';' ∉ s

/-- **The read is exact.** The needle `@k=v;` occurs in the line `@k'=v';`
exactly when the keys and the values agree. -/
theorem line_infix_iff {k v k' v' : List Char} (hk : Clean k) (hv : Clean v)
    (hk' : Clean k') (hv' : Clean v') :
    line k v <:+: line k' v' ↔ k = k' ∧ v = v' := by
  constructor
  · rintro ⟨s, t, h⟩
    -- the needle starts at the line's only `@`
    have hs : s = [] := by
      rcases s with _ | ⟨x, s⟩
      · rfl
      · exfalso
        simp only [line, List.cons_append, List.append_assoc, List.cons.injEq]
          at h
        have hmem : '@' ∈ k' ++ '=' :: (v' ++ [';']) := by
          rw [← h.2]; simp
        simp only [List.mem_append, List.mem_cons] at hmem
        rcases hmem with h1 | h1 | h1 | h1
        · exact hk'.1 h1
        · exact absurd h1 (by decide)
        · exact hv'.1 h1
        · exact absurd h1 (by decide)
    subst hs
    simp only [line, List.nil_append, List.cons_append, List.append_assoc,
      List.cons.injEq, true_and] at h
    obtain ⟨rfl, h2⟩ := sep_cancel hk.2.1 hk'.2.1 h
    have h3 : v ++ ';' :: t = v' ++ ';' :: [] := by simpa using h2
    exact ⟨rfl, (sep_cancel hv.2.2 hv'.2.2 h3).1⟩
  · rintro ⟨rfl, rfl⟩
    exact List.infix_refl _

/-- The register file: one line per entry. -/
def regFile (R : List (List Char × List Char)) : List (List Char) :=
  R.map fun e => line e.1 e.2

/-- `FIND "needle"` succeeds when some line contains the needle. -/
def found (needle : List Char) (file : List (List Char)) : Prop :=
  ∃ l ∈ file, needle <:+: l

/-- **`FIND` finds an entry exactly when the register holds it.** -/
theorem find_iff_mem {R : List (List Char × List Char)}
    (hR : ∀ e ∈ R, Clean e.1 ∧ Clean e.2) {k v : List Char} (hk : Clean k)
    (hv : Clean v) : found (line k v) (regFile R) ↔ (k, v) ∈ R := by
  constructor
  · rintro ⟨l, hl, hin⟩
    obtain ⟨e, he, rfl⟩ := List.mem_map.1 hl
    obtain ⟨h1, h2⟩ := (line_infix_iff hk hv (hR e he).1 (hR e he).2).1 hin
    subst h1; subst h2
    exact he
  · intro h
    exact ⟨line k v, List.mem_map.2 ⟨(k, v), h, rfl⟩, List.infix_refl _⟩

/-- **With unique keys, `FIND` finds `@k=v;` exactly when `v` is the
register's value at `k`.** -/
theorem find_iff_eq {R : List (List Char × List Char)}
    (hR : ∀ e ∈ R, Clean e.1 ∧ Clean e.2) (hkeys : (R.map Prod.fst).Nodup)
    {k v w : List Char} (hk : Clean k) (hv : Clean v) (hw : (k, w) ∈ R) :
    found (line k v) (regFile R) ↔ v = w := by
  rw [find_iff_mem hR hk hv]
  constructor
  · intro hkv
    have key := List.inj_on_of_nodup_map hkeys hkv hw rfl
    exact (Prod.mk.inj key).2
  · rintro rfl
    exact hw

/-! ## The chain with reads -/

section Chain

variable {V : Type*}

open GLM.PlannerLadder

/-- The machine's values: a computed step from its own earlier values,
anything else as the planner claims it. -/
def MachineVal (comp : ℕ → Prop) [DecidablePred comp] (f : ℕ → (ℕ → V) → V)
    (claimed m : ℕ → V) : Prop :=
  ∀ k, m k = if comp k then f k m else claimed k

/-- The file a step leaves: a computed step writes the machine's value; a step
the machine reads writes the claimed value only when its check passes (an
unchecked carried step has the check that always passes). -/
def out (comp : ℕ → Prop) [DecidablePred comp] (chk : ℕ → V → Prop)
    [∀ k v, Decidable (chk k v)] (claimed m : ℕ → V) (k : ℕ) : Option V :=
  if comp k then some (m k) else if chk k (claimed k) then some (claimed k)
  else none

/-- Up to a step before which every claim is honest, the machine's values are
the honest ones. -/
theorem machine_honest_below {comp : ℕ → Prop} [DecidablePred comp]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineVal comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    {n : ℕ} (hbelow : ∀ i < n, claimed i = h i) : ∀ i < n, m i = h i := by
  intro i
  induction i using Nat.strong_induction_on with
  | _ i ih =>
    intro hi
    rw [hm i]
    split_ifs with hc
    · rw [hh i hc]
      exact hf i m h fun j hj => ih j hj (lt_trans hj hi)
    · exact hbelow i hi

/-- **An honest chain never drifts.** -/
theorem honest_no_drift {comp : ℕ → Prop} [DecidablePred comp]
    {chk : ℕ → V → Prop} [∀ k v, Decidable (chk k v)]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineVal comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hpass : ∀ k, ¬ comp k → chk k (h k)) (honest : claimed = h) :
    ∀ k, out comp chk claimed m k = some (claimed k) := by
  subst honest
  intro k
  have hmk := machine_honest_below hf hm hh (n := k + 1)
    (fun _ _ => rfl) k (Nat.lt_succ_self k)
  unfold out
  split_ifs with hc hp
  · rw [hmk]
  · rfl
  · exact absurd (hpass k hc) hp

/-- **The first lie drifts at its own step**, computed or read, and nothing
before it drifts. A lie at an unchecked carried step is outside the
hypothesis: the machine cannot see it there. -/
theorem first_lie_drifts {comp : ℕ → Prop} [DecidablePred comp]
    {chk : ℕ → V → Prop} [∀ k v, Decidable (chk k v)]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineVal comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hpass : ∀ k, ¬ comp k → chk k (h k)) {n : ℕ}
    (hbelow : ∀ i < n, claimed i = h i) (hlie : claimed n ≠ h n)
    (hseen : comp n ∨ ¬ chk n (claimed n)) :
    out comp chk claimed m n ≠ some (claimed n) ∧
      ∀ i < n, out comp chk claimed m i = some (claimed i) := by
  have hmb := machine_honest_below hf hm hh hbelow
  refine ⟨?_, ?_⟩
  · unfold out
    split_ifs with hc hp
    · intro e
      have e' := Option.some.inj e
      rw [hm n, if_pos hc, hf n m h hmb, ← hh n hc] at e'
      exact hlie e'.symm
    · rcases hseen with hs | hs
      · exact absurd hs hc
      · exact absurd hp hs
    · simp
  · intro i hi
    unfold out
    split_ifs with hc hp
    · rw [hmb i hi, hbelow i hi]
    · rfl
    · exact absurd (hbelow i hi ▸ hpass i hc) hp

/-- **No drift exactly when honest**, when every step the machine does not
compute is an exact read. -/
theorem no_drift_iff {comp : ℕ → Prop} [DecidablePred comp]
    {chk : ℕ → V → Prop} [∀ k v, Decidable (chk k v)]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineVal comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hexact : ∀ k, ¬ comp k → ∀ x, chk k x ↔ x = h k) :
    (∀ k, out comp chk claimed m k = some (claimed k)) ↔ claimed = h := by
  have hpass : ∀ k, ¬ comp k → chk k (h k) := fun k hc => (hexact k hc _).2 rfl
  refine ⟨fun hall => ?_, honest_no_drift hf hm hh hpass⟩
  by_contra hne
  have hex : ∃ n, claimed n ≠ h n := by
    by_contra hno
    push_neg at hno
    exact hne (funext hno)
  classical
  let n := Nat.find hex
  have hlie : claimed n ≠ h n := Nat.find_spec hex
  have hbelow : ∀ i < n, claimed i = h i := fun i hi => by
    have := Nat.find_min hex hi
    simpa using this
  have hseen : comp n ∨ ¬ chk n (claimed n) := by
    by_cases hc : comp n
    · exact Or.inl hc
    · exact Or.inr fun hp => hlie ((hexact n hc _).1 hp)
  exact (first_lie_drifts hf hm hh hpass hbelow hlie hseen).1 (hall n)

end Chain

end GLM.CarriedRead
