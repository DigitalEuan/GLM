/-
# How far a word can fall in one step, and how many steps it really needs

`LDP.lean` settles the archive's energy landscape: the ground states are the
codewords, every excited word has a neighbour of energy exactly one lower, and
relaxation therefore reaches the code in at most `energy v` flips.  What it
does not say is *how deep* a single flip can go, or whether the bound of
`energy v` steps is anywhere near what a good descent needs.  Both were left
open by `studies/SOURCE_SALVAGE_AUDIT.md` §5, and this file answers them.

**One step.**  `drop_identity` is the whole arithmetic: flipping coordinate `k`
changes the syndrome weight by `2·|f ∩ col k| − wt(col k)`, so a flip can lower
the energy by at most the weight of its own column (`drop_le_colWt`), does so
exactly when the column sits inside the syndrome (`drop_eq_colWt_iff`), and
always changes the energy by a number of the same parity as that column weight
(`drop_parity`).  Every one of the substrate's 24 columns has *odd* weight —
eleven, seven or one (`colWt_odd`) — so **every energy change is odd**
(`energy_flip_parity`), and the deepest single step available is eleven.

`drop_census` is the exact distribution of the best available drop over the
4,096 cosets: `1, 3, 5, 7, 9, 11` occur `1486, 1342, 957, 286, 22, 2` times,
and no even value ever occurs.  The archive's reading — "descend one bit at a
time" — is right for 1,486 cosets and understates the other 2,609.

**The whole descent.**  A descent path is a sequence of flips each of which
lowers the energy.  `descent_path_length_le_energy` bounds any such path by
`energy v`, and `exists_slow_path` shows the bound is attained: the unit
columns of the systematic half always drop exactly one, so the slowest
improving descent takes exactly `energy v` steps.  `Descent.lean`'s companion
question — how *short* the fastest improving descent can be — is the census in
`glm_universal.reasoning.relaxation`, which measures 5 or 6 flips for 792 of the
4,096 cosets even though every coset is within distance 4 of the code: energy
descent is a relaxation, and it is not a decoder.
-/
import Mathlib
import RequestProject.GLM.LDP

namespace GLM.Golay24

open Finset

/-! ## 1. The support of a syndrome -/

/-- The set of parity bits a syndrome has set. -/
def supp (f : Syn) : Finset (Fin 12) := univ.filter (fun i => f i = 1)

theorem synWt_eq_card_supp (f : Syn) : synWt f = #(supp f) := rfl

theorem supp_add (f g : Syn) : supp (f + g) = symmDiff (supp f) (supp g) := by
  ext i
  have hx : ∀ x y : ZMod 2,
      ((x + y = 1) ↔ ((x = 1 ∧ ¬ y = 1) ∨ (y = 1 ∧ ¬ x = 1))) := by decide
  simpa [supp, Finset.mem_symmDiff, and_comm] using hx (f i) (g i)

/-! ## 2. One step: how far a single flip can go -/

/-- **The step identity.**  Adding a column to a syndrome changes its weight by
twice the overlap minus the column's own weight. -/
theorem drop_identity (f c : Syn) :
    synWt (f + c) + 2 * #(supp f ∩ supp c) = synWt f + synWt c := by
  rw [synWt_eq_card_supp f, synWt_eq_card_supp c, synWt_eq_card_supp (f + c), supp_add]
  exact card_symmDiff_add_two_inter _ _

/-- A flip lowers the energy by at most the weight of its column. -/
theorem drop_le_colWt (f c : Syn) : synWt f ≤ synWt (f + c) + synWt c := by
  have h := drop_identity f c
  have hle : #(supp f ∩ supp c) ≤ #(supp c) :=
    Finset.card_le_card Finset.inter_subset_right
  have hsc : synWt c = #(supp c) := rfl
  omega

/-- And it changes the energy by a number of the same parity as that weight. -/
theorem drop_parity (f c : Syn) : (synWt (f + c) + synWt f) % 2 = synWt c % 2 := by
  have := drop_identity f c; omega

/-- The full drop is achieved exactly when the column sits inside the
syndrome. -/
theorem drop_eq_colWt_iff (f c : Syn) :
    synWt (f + c) + synWt c = synWt f ↔ supp c ⊆ supp f := by
  have h := drop_identity f c
  have hsc : synWt c = #(supp c) := rfl
  constructor
  · intro hh
    have hcard : #(supp c) ≤ #(supp f ∩ supp c) := by omega
    have heq : supp f ∩ supp c = supp c :=
      Finset.eq_of_subset_of_card_le Finset.inter_subset_right hcard
    calc supp c = supp f ∩ supp c := heq.symm
      _ ⊆ supp f := Finset.inter_subset_left
  · intro hsub
    rw [Finset.inter_eq_right.mpr hsub] at h
    omega


/-! ## 3. The substrate's columns are all of odd weight -/

/-- The weight of the parity-check column at coordinate `k`. -/
def colWt (k : Fin 24) : ℕ := synWt (col k)

/-- **Every column has odd weight** — eleven, seven or one.  This is what makes
every energy change odd. -/
theorem colWt_odd (k : Fin 24) : colWt k % 2 = 1 := by
  unfold colWt synWt col; revert k; decide

theorem colWt_le_eleven (k : Fin 24) : colWt k ≤ 11 := by
  unfold colWt synWt col; revert k; decide

/-- **Every flip changes the energy by an odd number.**  The archive's
"descend by one" is right only about the parity. -/
theorem energy_flip_parity (v : Word) (k : Fin 24) :
    (energy (flip v k) + energy v) % 2 = 1 := by
  rw [energy, energy, syn_flip]
  have h := drop_parity (syn v) (col k)
  rw [show synWt (col k) = colWt k from rfl, colWt_odd k] at h
  exact h

/-! ## 4. The best drop available from a coset -/

/-- The lowest energy reachable from a syndrome by a single flip. -/
def bestNext (f : Syn) : ℕ :=
  (List.finRange 24).foldl (fun acc k => min acc (synWt (f + col k))) 12

/-- How far the best single flip drops the energy. -/
def bestDrop (f : Syn) : ℕ := synWt f - bestNext f

/-- There are twelve parity bits, so no syndrome weighs more than twelve. -/
theorem synWt_le_twelve (f : Syn) : synWt f ≤ 12 := by
  unfold synWt
  simpa using Finset.card_filter_le (univ : Finset (Fin 12)) _

/-- No single flip drops the energy by more than eleven, the largest column
weight. -/
theorem bestDrop_le_eleven (f : Syn) : bestDrop f ≤ 11 := by
  have hle : ∀ k ∈ List.finRange 24, synWt f ≤ synWt (f + col k) + 11 := by
    intro k _
    have h1 := drop_le_colWt f (col k)
    have h2 := colWt_le_eleven k
    unfold colWt at h2
    omega
  have hfold : ∀ (l : List (Fin 24)) (acc : ℕ),
      (∀ k ∈ l, synWt f ≤ synWt (f + col k) + 11) → synWt f ≤ acc + 11 →
      synWt f ≤ l.foldl (fun a k => min a (synWt (f + col k))) acc + 11 := by
    intro l
    induction l with
    | nil => intro acc _ hacc; simpa using hacc
    | cons k ks ih =>
        intro acc hmem hacc
        refine ih _ (fun j hj => hmem j (List.mem_cons_of_mem _ hj)) ?_
        have hk := hmem k (List.mem_cons_self ..)
        show synWt f ≤ min acc (synWt (f + col k)) + 11
        omega
  have hbound := hfold (List.finRange 24) 12 hle (by
    have := synWt_le_twelve f
    omega)
  unfold bestDrop bestNext
  omega

/-- **The census of best drops.**  Over the 4,096 cosets the best available
drop is `1, 3, 5, 7, 9, 11` in `1486, 1342, 957, 286, 22, 2` cases, and the
ground state accounts for the remaining one.  No even drop ever occurs, as
`energy_flip_parity` requires. -/
theorem drop_census :
    (List.range 12).map (fun d => #((univ : Finset Syn).filter (fun f => bestDrop f == d)))
      = [1, 1486, 0, 1342, 0, 957, 0, 286, 0, 22, 0, 2] := by
  unfold bestDrop bestNext synWt col; native_decide

theorem drop_census_total :
    ((List.range 12).map
      (fun d => #((univ : Finset Syn).filter (fun f => bestDrop f == d)))).sum = 4096 := by
  rw [drop_census]; norm_num

/-! ## 5. The whole descent: paths of improving flips -/

/-- A descent path: each listed flip lowers the energy, and the last word is a
codeword. -/
def IsDescentPath : Word → List (Fin 24) → Prop
  | v, [] => IsCodeword v
  | v, k :: ks => energy (flip v k) < energy v ∧ IsDescentPath (flip v k) ks

/-- **No descent is longer than the energy.**  Each step drops at least one, so
`energy v` bounds every improving path. -/
theorem descent_path_length_le_energy :
    ∀ (ks : List (Fin 24)) (v : Word), IsDescentPath v ks → ks.length ≤ energy v := by
  intro ks
  induction ks with
  | nil => intro v _; simp
  | cons k ks ih =>
      intro v h
      obtain ⟨hstep, hrest⟩ := h
      have := ih _ hrest
      simp only [List.length_cons]
      omega

/-- **And the bound is attained.**  The systematic columns drop exactly one, so
there is always an improving descent of exactly `energy v` steps: the archive's
"about four steps" is the slowest such path, not the shortest. -/
theorem exists_slow_path :
    ∀ (n : ℕ) (v : Word), energy v = n →
      ∃ ks : List (Fin 24), IsDescentPath v ks ∧ ks.length = n := by
  intro n
  induction n with
  | zero => intro v hv; exact ⟨[], energy_eq_zero_iff.mp hv, rfl⟩
  | succ n ih =>
      intro v hv
      have hnc : ¬ IsCodeword v := by
        intro hc
        rw [energy_eq_zero_iff.mpr hc] at hv
        omega
      obtain ⟨k, hk⟩ := energy_descent hnc
      obtain ⟨ks, hks, hlen⟩ := ih (flip v k) (by omega)
      exact ⟨k :: ks, ⟨by omega, hks⟩, by simp [hlen]⟩

/-! ## 6. The fastest descent, and why relaxation is not decoding

The bound of §5 is on the *longest* improving descent.  The question the
salvage audit left open is the other one: how few improving flips can reach the
code, and how that compares with the two, three or four flips that would decode
the word outright.  The answer is that energy descent is genuinely slower —
`relaxation_is_not_decoding` exhibits a word two flips from the code from which
no improving descent arrives in five — and the census in
`glm_universal.reasoning.relaxation` counts 792 such cosets out of 4,096. -/

/-- Reaching the code in at most `n` improving flips, stated on syndromes:
energy depends on a word only through its syndrome, so the whole question lives
on the 4,096 cosets. -/
def CanDescend : ℕ → Syn → Prop
  | 0, f => f = 0
  | (n + 1), f => CanDescend n f ∨
      ∃ k : Fin 24, synWt (f + col k) < synWt f ∧ CanDescend n (f + col k)

instance decCanDescend : ∀ (n : ℕ) (f : Syn), Decidable (CanDescend n f)
  | 0, f => inferInstanceAs (Decidable (f = 0))
  | (n + 1), f =>
      letI : ∀ g : Syn, Decidable (CanDescend n g) := decCanDescend n
      inferInstanceAs (Decidable (CanDescend n f ∨
        ∃ k : Fin 24, synWt (f + col k) < synWt f ∧ CanDescend n (f + col k)))

/-- `CanDescend` is the descent path of §5, read on syndromes. -/
theorem canDescend_iff_path : ∀ (n : ℕ) (v : Word),
    CanDescend n (syn v) ↔ ∃ ks : List (Fin 24), IsDescentPath v ks ∧ ks.length ≤ n := by
  intro n
  induction n with
  | zero =>
      intro v
      constructor
      · intro h; exact ⟨[], h, le_refl 0⟩
      · rintro ⟨ks, hks, hlen⟩
        have hnil : ks = [] := List.eq_nil_of_length_eq_zero (Nat.le_zero.mp hlen)
        subst hnil
        exact hks
  | succ n ih =>
      intro v
      constructor
      · rintro (h | ⟨k, hlt, hrest⟩)
        · obtain ⟨ks, hks, hlen⟩ := (ih v).mp h
          exact ⟨ks, hks, by omega⟩
        · rw [← syn_flip v k] at hlt hrest
          obtain ⟨ks, hks, hlen⟩ := (ih (flip v k)).mp hrest
          refine ⟨k :: ks, ⟨hlt, hks⟩, ?_⟩
          simp only [List.length_cons]
          omega
      · rintro ⟨ks, hks, hlen⟩
        cases ks with
        | nil => exact Or.inl ((ih v).mpr ⟨[], hks, Nat.zero_le _⟩)
        | cons k ks =>
            obtain ⟨hstep, hrest⟩ := hks
            simp only [List.length_cons] at hlen
            refine Or.inr ⟨k, ?_, ?_⟩
            · rw [← syn_flip v k]; exact hstep
            · rw [← syn_flip v k]
              exact (ih (flip v k)).mpr ⟨ks, hrest, by omega⟩

/-! ### The census, computed once over the 4,096 cosets

The descent question is a reachability problem on 4,096 nodes, so it is
answered by four sweeps of an array rather than by a search: `dpLevel n` marks
the syndromes that reach the code in at most `n` improving flips, and
`dpLevel_get` proves that is what it marks. -/

/-- A syndrome as a twelve-bit index. -/
def synIdx (f : Syn) : ℕ := ∑ i : Fin 12, if f i = 1 then 2 ^ (i : ℕ) else 0

/-- And back again. -/
def synOf (n : ℕ) : Syn := fun i => if (n / 2 ^ (i : ℕ)) % 2 = 1 then 1 else 0

theorem synIdx_lt (f : Syn) : synIdx f < 4096 := by revert f; native_decide

theorem synOf_synIdx (f : Syn) : synOf (synIdx f) = f := by revert f; native_decide

theorem synIdx_eq_zero_iff (f : Syn) : synIdx f = 0 ↔ f = 0 := by
  constructor
  · intro h
    have hf := synOf_synIdx f
    rw [h] at hf
    rw [← hf]
    funext i
    simp [synOf]
  · rintro rfl
    simp [synIdx]

private theorem getD_range_map (g : ℕ → Bool) {N i : ℕ} (hi : i < N) :
    ((Array.range N).map g).getD i false = g i := by
  simp [Array.getD, hi]

/-- One sweep: a syndrome is marked if it was already marked, or if some
improving flip lands on a marked one. -/
def dpStepFn (a : Array Bool) (n : ℕ) : Bool :=
  a.getD n false ||
    (List.finRange 24).any (fun k =>
      decide (synWt (synOf n + col k) < synWt (synOf n))
        && a.getD (synIdx (synOf n + col k)) false)

/-- The syndromes that reach the code in at most `m` improving flips. -/
def dpLevel : ℕ → Array Bool
  | 0 => (Array.range 4096).map (fun n => decide (n = 0))
  | (m + 1) => (Array.range 4096).map (dpStepFn (dpLevel m))

/-- **The sweep computes what it claims to.** -/
theorem dpLevel_get (m : ℕ) (f : Syn) :
    (dpLevel m).getD (synIdx f) false = true ↔ CanDescend m f := by
  induction m generalizing f with
  | zero =>
      rw [dpLevel, getD_range_map _ (synIdx_lt f)]
      simpa using synIdx_eq_zero_iff f
  | succ m ih =>
      rw [dpLevel, getD_range_map _ (synIdx_lt f), dpStepFn, synOf_synIdx f]
      simp only [Bool.or_eq_true, List.any_eq_true, Bool.and_eq_true, decide_eq_true_iff]
      rw [CanDescend]
      constructor
      · rintro (h | ⟨k, -, hlt, ha⟩)
        · exact Or.inl ((ih f).mp h)
        · exact Or.inr ⟨k, hlt, (ih _).mp ha⟩
      · rintro (h | ⟨k, hlt, hc⟩)
        · exact Or.inl ((ih f).mpr h)
        · exact Or.inr ⟨k, List.mem_finRange k, hlt, (ih _).mpr hc⟩

/-- How many of the 4,096 cosets relax in at most `m` improving flips.  The
array is built once and then read, which is what keeps the count cheap. -/
def descendCount (m : ℕ) : ℕ :=
  let a := dpLevel m
  Finset.card ((univ : Finset Syn).filter (fun f => a.getD (synIdx f) false = true))

theorem descendCount_eq (m : ℕ) :
    descendCount m = #((univ : Finset Syn).filter (fun f => CanDescend m f)) := by
  show Finset.card ((univ : Finset Syn).filter
      (fun f => (dpLevel m).getD (synIdx f) false = true)) = _
  congr 1
  exact Finset.filter_congr (fun f _ => by simpa using dpLevel_get m f)

/-- **Six improving flips always suffice.** -/
theorem descend_within_six : descendCount 6 = 4096 := by native_decide

/-- **And four do not.**  3,304 of the 4,096 cosets relax in four improving
flips; the other 792 need five or six, even though every coset is within
distance 4 of the code. -/
theorem descend_within_four : descendCount 4 = 3304 := by native_decide

theorem descend_within_five : descendCount 5 = 4030 := by native_decide

theorem every_coset_descends_in_six (f : Syn) : CanDescend 6 f := by
  have h := descend_within_six
  rw [descendCount_eq] at h
  have hcard : #(univ : Finset Syn) ≤ #((univ : Finset Syn).filter (fun f => CanDescend 6 f)) := by
    rw [h]; simp
  have heq := Finset.eq_of_subset_of_card_le (Finset.filter_subset _ _) hcard
  have : f ∈ (univ : Finset Syn).filter (fun f => CanDescend 6 f) := by
    rw [heq]; exact Finset.mem_univ f
  exact (Finset.mem_filter.mp this).2

/-- The witness behind the 792: two errors in the message half of the word.
No improving descent from it reaches the code in five flips. -/
theorem not_descend_five_pair : ¬ CanDescend 5 (syn ({0, 1} : Word)) := by
  rw [← dpLevel_get]
  native_decide

/-- **Relaxation is not decoding.**  There is a word two flips from a codeword
from which no descent that lowers the energy at every step arrives in five — it
takes six.  Falling downhill and taking the short way are different journeys,
and the archive's "relaxation reaches the ground state" is the first. -/
theorem relaxation_is_not_decoding :
    ∃ v c : Word, IsCodeword c ∧ hdist v c = 2 ∧
      ¬ ∃ ks : List (Fin 24), IsDescentPath v ks ∧ ks.length ≤ 5 := by
  refine ⟨{0, 1}, ∅, isCodeword_empty, ?_, ?_⟩
  · unfold hdist; decide
  · rw [← canDescend_iff_path]
    exact not_descend_five_pair

end GLM.Golay24
