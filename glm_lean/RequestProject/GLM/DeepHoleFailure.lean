/-
# The four failures, and the spread that gates the certificate

`studies/DEEP_HOLE_FAILURE_STUDY.md` opens the four queries the escalated
deep-hole reading does not name correctly, and asks whether the mechanism
behind them is the same one that keeps the separation ratio `ρ = 2W/B` above
the criterion.  The measurement is
`overlay/glm_universal/reasoning/deep_hole_failures.py`.  Three of the things
that round says are not measurements, and they are here.

## 1.  A failure is a statement about the *references*, not only the query

`failure_pair_close`: if a query lies within `w` of its own reference and is
named as another, then those two references are within `2w` of each other.  The
diagnosis the study calls **A** — "the margin was never there, because the pair
is the closest pair" — is therefore not a hypothesis at all: it is forced.  Any
failure at spread `w` exhibits a reference pair inside `2w`, and the measured
round found all four of its failures on the two closest pairs of the table
because there is nowhere else for them to be.

## 2.  Deleting references can only make the criterion easier

`resolves_of_subset`: the criterion on a table implies the criterion on any
sub-table.  That is why the study's deletion sweep is a way of *locating* the
spread and never a certificate: a deletion cannot make the ratio worse, so a
deletion passing the criterion says nothing about the types deleted.

## 3.  A per-type criterion certifies a per-type answer

`per_type_correct`: where one type's own criterion `2w < B_T` holds, every
query of that type within `w` of its reference is named correctly, whatever the
other types do.  This is what lets the round report three certified types out
of ten rather than reporting only the global failure — and
`per_type_absent` is the other half: with faithfulness at radius `w`, a carrier
further than `w` from a reference is *not* of that type, which is an absence
proved rather than guessed.
-/
import RequestProject.GLM.DeepHoleEscalation

namespace GLM.DeepHoleFailure

open GLM.DeepHoleLadder

universe u v

variable {C : Type u} {L : Type v}

/-! ## 1.  Every failure exhibits a close pair of references -/

/-- **A failure is a close pair.**  If `x` sits within `w` of its own reference
`p` and the nearest-reference rule names it `q` instead, then `p` and `q` are
within `2w` of each other.  So a failure at spread `w` always witnesses a
reference pair inside `2w`: there is no such thing as a failure between two
well-separated references. -/
theorem failure_pair_close {R : Reading C} {w : ℚ} {x p q : C}
    (hx : R.dist x p ≤ w) (hwin : R.dist x q ≤ R.dist x p) :
    R.dist p q ≤ 2 * w := by
  have htri : R.dist p q ≤ R.dist p x + R.dist x q := R.dist_triangle p x q
  have hpx : R.dist p x = R.dist x p := R.dist_comm p x
  linarith

/-- The contrapositive, in the form the criterion is stated in: a reference
pair strictly further apart than `2w` cannot produce a failure between those
two references. -/
theorem no_failure_of_separated {R : Reading C} {w : ℚ} {x p q : C}
    (hsep : 2 * w < R.dist p q) (hx : R.dist x p ≤ w) :
    R.dist x p < R.dist x q := by
  by_contra hcon
  push_neg at hcon
  exact absurd (failure_pair_close hx hcon) (not_le.2 hsep)

/-! ## 2.  Deleting references cannot make the criterion harder -/

/-- **A deletion can only help.**  If the criterion holds on a table it holds
on every sub-table, so a deletion that passes it has not earned anything about
the entries it deleted. -/
theorem resolves_of_subset {R : Reading C} {refs kept : List (L × C)} {w : ℚ}
    (hsub : ∀ e ∈ kept, e ∈ refs) (h : Resolves R refs w) :
    Resolves R kept w :=
  fun e he f hf hne => h e (hsub e he) f (hsub f hf) hne

/-- The same fact about the separation itself: the minimum over a sub-table is
at least the minimum over the table, so `B` can only rise under deletion. -/
theorem separation_mono {R : Reading C} {refs kept : List (L × C)} {B : ℚ}
    (hsub : ∀ e ∈ kept, e ∈ refs)
    (hB : ∀ e ∈ refs, ∀ f ∈ refs, e.1 ≠ f.1 → B ≤ R.dist e.2 f.2) :
    ∀ e ∈ kept, ∀ f ∈ kept, e.1 ≠ f.1 → B ≤ R.dist e.2 f.2 :=
  fun e he f hf hne => hB e (hsub e he) f (hsub f hf) hne

/-! ## 3.  One type's criterion certifies one type's answers -/

/-- The criterion for a single type: `p` is the type's reference, and every
*other* reference is more than `2w` away from it. -/
def ResolvesAt (R : Reading C) (refs : List (L × C)) (t : L) (p : C) (w : ℚ) :
    Prop :=
  ∀ f ∈ refs, f.1 ≠ t → 2 * w < R.dist p f.2

/-- **The per-type criterion is sufficient, per type.**  Where it holds, every
carrier within `w` of that type's reference is strictly nearer to it than to
any other reference — whatever the spread of the other types is. -/
theorem per_type_correct {R : Reading C} {refs : List (L × C)} {t : L}
    {p x : C} {w : ℚ} (hres : ResolvesAt R refs t p w) (hx : R.dist x p ≤ w)
    {u : L} {q : C} (hq : (u, q) ∈ refs) (hne : u ≠ t) :
    R.dist x p < R.dist x q :=
  no_failure_of_separated (hres (u, q) hq hne) hx

/-- The global criterion gives the per-type one at every type in the table, so
nothing is lost by reading the criterion type by type. -/
theorem resolvesAt_of_resolves {R : Reading C} {refs : List (L × C)} {w : ℚ}
    (h : Resolves R refs w) {t : L} {p : C} (hmem : (t, p) ∈ refs) :
    ResolvesAt R refs t p w := by
  intro f hf hne
  have := h (t, p) hmem f hf (fun hcon => hne hcon.symm)
  simpa [R.dist_comm] using this

/-- **An absence, proved.**  If the type is faithful at radius `w` — every
carrier of it lies within `w` of its reference — then a carrier further than
`w` from that reference is not of the type.  This is the certificate the
deep-hole rounds have been short of, and it needs faithfulness rather than
separation: the round measures the radius each type needs and reports which
types have one. -/
theorem per_type_absent {R : Reading C} {IsType : C → Prop} {p : C} {w : ℚ}
    (hfaithful : ∀ y, IsType y → R.dist y p ≤ w)
    {x : C} (hfar : w < R.dist x p) : ¬ IsType x :=
  fun hx => absurd (hfaithful x hx) (not_le.2 hfar)

/-- Rank one is correctness: if the query's own reference is strictly nearest,
the nearest-reference rule names it correctly.  Stated so that the study's rank
language and the classifier's verdict language are the same statement. -/
theorem rank_one_correct {R : Reading C} {refs : List (L × C)} {t : L}
    {p x : C} (hlabels : ∀ f ∈ refs, f.1 = t → f.2 = p)
    (hstrict : ∀ f ∈ refs, f.1 ≠ t → R.dist x p < R.dist x f.2) :
    ∀ f ∈ refs, R.dist x p ≤ R.dist x f.2 := by
  intro f hf
  by_cases hft : f.1 = t
  · rw [hlabels f hf hft]
  · exact le_of_lt (hstrict f hf hft)

end GLM.DeepHoleFailure
