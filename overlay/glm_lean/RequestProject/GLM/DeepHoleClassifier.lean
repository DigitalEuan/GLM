/-
# The deep-hole classifier: invariance, refusal, and certified absence

`studies/DEEP_HOLE_STUDY.md` asks whether the distribution of trajectories that
arrive at a deep hole of the Leech lattice is enough to name the hole's
Coxeter–Dynkin type.  Most of that study is a measurement and lives in
`overlay/glm_universal/reasoning/deep_hole_classifier.py`.  What is *not* a
measurement is the classifier itself, and it is here.

The census is not formalised here and is not meant to be: `Golay/Census.lean`
is the census for one lattice, and the 23 root systems are the Python side's
derived catalogue.  The theorems worth having are about the classifier, in the
register the retrieval round's completeness bound established.

## 1.  The metric

`l1` is the L1 distance on `Fin n → ℚ`.  Exact rationals, no reals: the whole
point of the substrate is that it is exact, so the distance a proof reasons
about is the distance the module computes.  `l1_triangle` is the only property
the classification theorems need, and `l1_reindex` says the metric does not
care how the coordinates were numbered.

## 2.  Invariance — the label is a function of the hole

The statistic is an *arrival multiset*: how often the trajectory arrived at each
vertex, with the vertices unnamed.  `arrivalMultiset_reindex` says that
relabelling the vertices — the only arbitrary choice the walk makes when it
writes down what it reached — leaves the multiset alone, and
`sortedProfile_reindex` carries that to the sorted profile the classifier
actually compares.  So the label is a function of the hole and not of the
walk's bookkeeping.

## 3.  Totality, single-valuedness, and a refusal that is a value

`classify` returns a `Verdict`: `named t`, `ambiguous`, or `absent`.  It is a
total function, so it is single-valued by construction; `classify_named_mem`
says a name is never invented (the named reference really is in the table and
really is within the radius), and `classify_absent_iff` says a refusal of the
`absent` kind is exactly the statement that nothing is within the radius.  A
refusal is a value and not a failure, which is what the study asked for in place
of a guess.

## 4.  The one with teeth — certified absence

Under a separation hypothesis on the reference table — distinct labels more than
`2r` apart, which the measurement supplies as `r*` — two things follow:

* `classify_named_of_separated`: anything within `r` of a reference is *named*
  by it, and `ambiguous` cannot occur;
* `absent_certifies`: if the verdict is `absent`, then **no** profile that is
  within `r` of any tabulated reference is equal to the query.  Given
  faithfulness — every hole of type `t` has a profile within `r` of `t`'s
  reference — that is a proof that no hole of any tabulated type has this
  statistic.  A negative answer is a proof, which is the property that made the
  retrieval shortlist worth having.

Faithfulness is an empirical hypothesis and appears as a hypothesis, never as an
assumption made silently.
-/
import Mathlib

namespace GLM.DeepHole

variable {n : ℕ} {L : Type*}

/-- A profile: `n` exact rational shares, sorted and padded by the caller. -/
abbrev Profile (n : ℕ) := Fin n → ℚ

/-- The L1 distance between two profiles, exactly. -/
def l1 (p q : Profile n) : ℚ := ∑ i, |p i - q i|

@[simp] theorem l1_self (p : Profile n) : l1 p p = 0 := by
  simp [l1]

theorem l1_nonneg (p q : Profile n) : 0 ≤ l1 p q :=
  Finset.sum_nonneg fun _ _ => abs_nonneg _

theorem l1_comm (p q : Profile n) : l1 p q = l1 q p := by
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [abs_sub_comm]

theorem l1_triangle (p q r : Profile n) : l1 p r ≤ l1 p q + l1 q r := by
  rw [l1, l1, l1, ← Finset.sum_add_distrib]
  refine Finset.sum_le_sum fun i _ => ?_
  calc |p i - r i| = |(p i - q i) + (q i - r i)| := by ring_nf
    _ ≤ |p i - q i| + |q i - r i| := abs_add_le _ _

/-- Renumbering the coordinates moves neither profile relative to the other. -/
theorem l1_reindex (σ : Equiv.Perm (Fin n)) (p q : Profile n) :
    l1 (p ∘ σ) (q ∘ σ) = l1 p q :=
  Fintype.sum_equiv σ _ _ fun _ => rfl

/-! ## The statistic, and why the label is a function of the hole -/

section Statistic

variable {V W : Type*} [Fintype V] [Fintype W]

/-- The arrival multiset: the shares, with the vertices unnamed. -/
def arrivalMultiset (a : V → ℚ) : Multiset ℚ :=
  (Finset.univ : Finset V).val.map a

/-- Relabelling the vertices leaves the arrival multiset alone. -/
theorem arrivalMultiset_reindex (e : V ≃ W) (a : W → ℚ) :
    arrivalMultiset (a ∘ e) = arrivalMultiset a := by
  classical
  have h : Multiset.map (⇑e) (Finset.univ : Finset V).val
      = (Finset.univ : Finset W).val := by
    simp
  simp only [arrivalMultiset, ← h, Multiset.map_map, Function.comp_def]

/-- The sorted profile: descending, and a function of the multiset alone. -/
def sortedProfile (m : Multiset ℚ) : List ℚ := m.sort (· ≥ ·)

/-- Hence the sorted profile cannot see how the vertices were named. -/
theorem sortedProfile_reindex (e : V ≃ W) (a : W → ℚ) :
    sortedProfile (arrivalMultiset (a ∘ e)) = sortedProfile (arrivalMultiset a) := by
  rw [arrivalMultiset_reindex]

end Statistic

/-! ## The classifier -/

/-- What the classifier may answer.  A refusal is a value, not a failure. -/
inductive Verdict (L : Type*)
  | named (label : L)
  | ambiguous
  | absent
  deriving Repr

/-- The references within the radius of a query. -/
def near (r : ℚ) (q : Profile n) (refs : List (L × Profile n)) :
    List (L × Profile n) :=
  refs.filter (fun e => decide (l1 q e.2 ≤ r))

/-- Name the unique reference within the radius, or refuse and say which way. -/
def classify (r : ℚ) (q : Profile n) (refs : List (L × Profile n)) : Verdict L :=
  match near r q refs with
  | [e] => .named e.1
  | [] => .absent
  | _ => .ambiguous

theorem mem_near {r : ℚ} {q : Profile n} {refs : List (L × Profile n)}
    {e : L × Profile n} : e ∈ near r q refs ↔ e ∈ refs ∧ l1 q e.2 ≤ r := by
  simp [near, List.mem_filter]

/-- A name is never invented: it comes from the table and it is within `r`. -/
theorem classify_named_mem {r : ℚ} {q : Profile n} {refs : List (L × Profile n)}
    {t : L} (h : classify r q refs = .named t) :
    ∃ p : Profile n, (t, p) ∈ refs ∧ l1 q p ≤ r := by
  unfold classify at h
  cases hn : near r q refs with
  | nil => rw [hn] at h; exact absurd h (by simp)
  | cons a as =>
      cases as with
      | nil =>
          rw [hn] at h
          simp only [Verdict.named.injEq] at h
          have hmem : a ∈ near r q refs := by rw [hn]; simp
          rw [mem_near] at hmem
          exact ⟨a.2, by rw [← h]; exact hmem.1, hmem.2⟩
      | cons b bs => rw [hn] at h; exact absurd h (by simp)

/-- `absent` says exactly that nothing in the table is within the radius. -/
theorem classify_absent_iff {r : ℚ} {q : Profile n}
    {refs : List (L × Profile n)} :
    classify r q refs = .absent ↔ ∀ e ∈ refs, r < l1 q e.2 := by
  constructor
  · intro h e he
    by_contra hle
    push_neg at hle
    have hmem : e ∈ near r q refs := mem_near.2 ⟨he, hle⟩
    unfold classify at h
    cases hn : near r q refs with
    | nil => rw [hn] at hmem; simp at hmem
    | cons a as =>
        cases as with
        | nil => rw [hn] at h; exact absurd h (by simp)
        | cons b bs => rw [hn] at h; exact absurd h (by simp)
  · intro h
    have hnil : near r q refs = [] := by
      rw [List.eq_nil_iff_forall_not_mem]
      intro e he
      rw [mem_near] at he
      exact absurd he.2 (not_le.2 (h e he.1))
    unfold classify
    rw [hnil]

/-- A one-element filter, when exactly one member of a nodup list qualifies. -/
theorem filter_eq_singleton {α : Type*} {P : α → Bool} {l : List α} {a : α}
    (hnd : l.Nodup) (ha : a ∈ l) (hPa : P a)
    (huniq : ∀ x ∈ l, P x → x = a) : l.filter P = [a] := by
  induction l with
  | nil => simp at ha
  | cons b bs ih =>
      rw [List.nodup_cons] at hnd
      rcases List.mem_cons.1 ha with rfl | hmem
      · have hbs : bs.filter P = [] := by
          rw [List.eq_nil_iff_forall_not_mem]
          intro x hx
          rw [List.mem_filter] at hx
          have := huniq x (List.mem_cons_of_mem _ hx.1) hx.2
          exact hnd.1 (this ▸ hx.1)
        rw [List.filter_cons_of_pos hPa, hbs]
      · have hb : P b = false := by
          by_contra hb
          simp only [Bool.not_eq_false] at hb
          have : b = a := huniq b (List.mem_cons_self ..) hb
          exact hnd.1 (this ▸ hmem)
        rw [List.filter_cons_of_neg (by simp [hb])]
        exact ih hnd.2 hmem (fun x hx hPx => huniq x (List.mem_cons_of_mem _ hx) hPx)

/-- With the table separated by more than `2r`, anything within `r` is named —
and `ambiguous` cannot occur. -/
theorem classify_named_of_separated {r : ℚ} {q : Profile n}
    {refs : List (L × Profile n)} {t : L} {p : Profile n}
    (hnd : refs.Nodup)
    (hsep : ∀ e ∈ refs, ∀ f ∈ refs, e ≠ f → 2 * r < l1 e.2 f.2)
    (hmem : (t, p) ∈ refs) (hq : l1 q p ≤ r) :
    classify r q refs = .named t := by
  have huniq : ∀ x ∈ refs, decide (l1 q x.2 ≤ r) = true → x = (t, p) := by
    intro x hx hxr
    by_contra hne
    have hxle : l1 q x.2 ≤ r := of_decide_eq_true hxr
    have hlt : 2 * r < l1 x.2 p := hsep x hx (t, p) hmem hne
    have : l1 x.2 p ≤ l1 x.2 q + l1 q p := l1_triangle _ _ _
    rw [l1_comm x.2 q] at this
    have : l1 x.2 p ≤ 2 * r := by linarith
    linarith
  have : near r q refs = [(t, p)] :=
    filter_eq_singleton hnd hmem (by simpa using hq) huniq
  unfold classify
  rw [this]

/-- **Certified absence.**  If the verdict is `absent`, no profile faithful to a
tabulated reference is the query — so, given faithfulness, no hole of any
tabulated type has this statistic. -/
theorem absent_certifies {r : ℚ} {q : Profile n} {refs : List (L × Profile n)}
    (h : classify r q refs = .absent) {t : L} {p s : Profile n}
    (hmem : (t, p) ∈ refs) (hfaith : l1 s p ≤ r) : s ≠ q := by
  intro hsq
  have := (classify_absent_iff.1 h) (t, p) hmem
  rw [← hsq] at this
  exact absurd hfaith (not_le.2 this)

/-- The verdict does not depend on how the coordinates were numbered. -/
theorem classify_reindex (r : ℚ) (σ : Equiv.Perm (Fin n)) (q : Profile n)
    (refs : List (L × Profile n)) :
    classify r (q ∘ σ) (refs.map (fun e => (e.1, e.2 ∘ σ))) = classify r q refs := by
  have hnear : near r (q ∘ σ) (refs.map (fun e => (e.1, e.2 ∘ σ)))
      = (near r q refs).map (fun e => (e.1, e.2 ∘ σ)) := by
    rw [near, near, List.filter_map]
    congr 1
    refine List.filter_congr fun x _ => ?_
    have h : l1 (fun i => q (σ i)) (fun i => x.2 (σ i)) = l1 q x.2 :=
      l1_reindex σ q x.2
    exact congrArg (fun z : ℚ => decide (z ≤ r)) h
  unfold classify
  rw [hnear]
  cases near r q refs with
  | nil => rfl
  | cons a as => cases as with
    | nil => rfl
    | cons b bs => rfl

/-- The classifier is total: it always returns one of the three verdicts. -/
theorem classify_total (r : ℚ) (q : Profile n) (refs : List (L × Profile n)) :
    (∃ t, classify r q refs = .named t) ∨ classify r q refs = .ambiguous
      ∨ classify r q refs = .absent := by
  cases h : classify r q refs with
  | named t => exact Or.inl ⟨t, rfl⟩
  | ambiguous => exact Or.inr (Or.inl rfl)
  | absent => exact Or.inr (Or.inr rfl)

end GLM.DeepHole
