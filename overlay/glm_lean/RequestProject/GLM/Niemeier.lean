/-
# The Niemeier census: the 23 root systems, searched for rather than tabulated

`overlay/glm_universal/reasoning/niemeier.py` refuses to store the 23 Niemeier
root systems, because an earlier version of this project *did* store them and
the stored table was wrong — it listed `D_10 E_8^2` (rank 26) and
`A_11 D_7 A_11` (rank 29), and it was missing `D_8^3`, `D_12^2` and
`D_10 E_7^2`.  A table that records its own ranks can only be checked against
itself.  The Python module therefore *searches*: a Niemeier root system is a
union of ADE components in which every component has the same Coxeter number
and the ranks sum to 24, and the rank, Coxeter number and root count of each
component come from the ADE formulas rather than from a row.

This file is the Lean half of that search, and it settles what the Python can
only exhibit: that the search is **complete**.  The enumeration here is a
knapsack over the catalogue of ADE components of rank at most 24, and the two
directions of its correctness are proved, not run —

* `mem_gen` — every multiplicity vector of the right weight is generated;
* `gen_sound` — everything generated has the right weight.

so the filtered list `niemeierVectors` is *exactly* the set of solutions, and
`niemeierVectors_length` says there are 23 of them.  `niemeier_names` reads
them back as the classical names, in the order the search produces them:

    E_8^3, E_6^4, D_24, D_16 E_8, D_12^2, D_10 E_7^2, D_8^3, D_6^4, D_4^6,
    A_24, A_17 E_7, A_15 D_9, A_12^2, A_11 D_7 E_6, A_9^2 D_6, A_8^3,
    A_7^2 D_5^2, A_6^4, A_5^4 D_4, A_4^6, A_3^8, A_2^12, A_1^24

The statement the file is really for is `card_root_systems`: the set of
*abstract* root systems — multisets of ADE components, with no reference to
the catalogue, the enumeration or any ordering — has exactly 23 elements.  The
catalogue is not an assumption of that theorem: `mem_catalogue_of_ok` proves
that a component of a rank-24 system cannot escape it, because its rank is
positive and at most 24.

## What is, and is not, proved

The classification proved here is the **combinatorial** one, and it is stated
exactly as the Python search states it: a Niemeier root system is a multiset of
simply-laced components with one Coxeter number and total rank 24 (Venkov's
condition).  What this file settles is that there are exactly 23 such multisets
and that they carry the names, root counts, node counts and mark sums recorded
below.  It does **not** prove that each of the 23 is realised by an even
unimodular lattice, nor that the Leech lattice is the only rootless one, nor
the Conway-Parker-Sloane bijection with the deep holes; those are taken from
the literature, and `leech_not_root_system` records only the trivial half —
that a rootless system does not satisfy the rank condition, so the search's
answer is 23 rather than 24.

## What this has to do with deep holes

Conway, Parker and Sloane: the deep holes of the Leech lattice fall into 23
classes, in bijection with the 23 Niemeier lattices that have roots, and the
lattice points nearest a hole form the *extended* Dynkin diagram of that root
system.  `overlay/glm_universal/reasoning/deep_holes.py` classifies a hole by
running a modulator at its centre and reading the diagram off the trajectory,
and it certifies the reading with the marks identity `∑ nᵢ vᵢ = h c`.  Three
facts that certificate rests on are proved here componentwise and then over
each of the 23 systems:

* `Comp.roots_eq_rank_mul_coxeter` — a component has `rank × h` roots, so a
  Niemeier root system has exactly `24 h` roots (`niemeier_roots`);
* `Comp.extMarks_sum` — the marks of an extended Dynkin diagram sum to the
  Coxeter number, so a hole's marks sum to `h` per component
  (`niemeier_marks`);
* `Comp.extMarks_length` — the extended diagram of a rank-`n` component has
  `n + 1` nodes, so a hole of type `R` has `24 + (number of components)`
  vertices (`niemeier_nodes`) — the count `deep_holes.py` saturates towards,
  and the reason a vertex set that passes the certificate is the whole vertex
  set.

The 24th even unimodular lattice in this dimension is the Leech lattice, which
has no roots and is the type of no hole; here that is `leech_not_root_system`,
the statement that the empty multiset is not a Niemeier root system, and it is
the reason the search's own answer is 23 rather than 24.
-/
import Mathlib

namespace GLM.Niemeier

/-! ## 1.  ADE components, as formulas -/

/-- The three simply-laced families.  `A` and `D` are formulas in the rank;
`E` exists only at ranks 6, 7 and 8. -/
inductive Letter
  | A
  | D
  | E
deriving DecidableEq, Repr

/-- One irreducible component of a root system: a family and a rank. -/
structure Comp where
  letter : Letter
  rank : ℕ
deriving DecidableEq, Repr

namespace Comp

/-- Which `(letter, rank)` pairs name a distinct simply-laced root system.
`D_3 = A_3` and `D_2 = A_1 + A_1`, so `D` starts at 4; `E` exists only at
6, 7, 8. -/
def ok (c : Comp) : Bool :=
  match c.letter with
  | .A => 1 ≤ c.rank
  | .D => 4 ≤ c.rank
  | .E => c.rank == 6 || c.rank == 7 || c.rank == 8

/-- The Coxeter number: `n + 1` for `A_n`, `2n - 2` for `D_n`, and 12, 18, 30
for `E_6`, `E_7`, `E_8`. -/
def coxeter (c : Comp) : ℕ :=
  match c.letter with
  | .A => c.rank + 1
  | .D => 2 * c.rank - 2
  | .E => if c.rank = 6 then 12 else if c.rank = 7 then 18 else 30

/-- The number of roots: `n(n+1)`, `2n(n-1)`, and 72, 126, 240. -/
def roots (c : Comp) : ℕ :=
  match c.letter with
  | .A => c.rank * (c.rank + 1)
  | .D => 2 * c.rank * (c.rank - 1)
  | .E => if c.rank = 6 then 72 else if c.rank = 7 then 126 else 240

/-- The marks of the extended Dynkin diagram, node by node.  `A_n` is a cycle
of `n + 1` nodes all marked 1; `D_n` is a chain of `n - 3` nodes marked 2 with
four nodes marked 1 hanging off its ends; the three `E` diagrams are their
classical mark vectors. -/
def extMarks (c : Comp) : List ℕ :=
  match c.letter with
  | .A => List.replicate (c.rank + 1) 1
  | .D => [1, 1] ++ List.replicate (c.rank - 3) 2 ++ [1, 1]
  | .E =>
      if c.rank = 6 then [1, 2, 3, 2, 1, 2, 1]
      else if c.rank = 7 then [1, 2, 3, 4, 3, 2, 1, 2]
      else [1, 2, 3, 4, 5, 6, 4, 2, 3]

/-- A simply-laced root system has `rank × h` roots.  This is the componentwise
half of the identity a Niemeier system satisfies with `rank = 24`. -/
theorem roots_eq_rank_mul_coxeter (c : Comp) (h : c.ok) :
    c.roots = c.rank * c.coxeter := by
  obtain ⟨l, n⟩ := c
  cases l
  · simp [roots, coxeter]
  · simp only [ok, decide_eq_true_eq] at h
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 4 := ⟨n - 4, by omega⟩
    have h1 : m + 4 - 1 = m + 3 := by omega
    have h2 : 2 * (m + 4) - 2 = 2 * m + 6 := by omega
    simp only [roots, coxeter, h1, h2]
    ring
  · simp only [ok, Bool.or_eq_true, beq_iff_eq] at h
    rcases h with (h | h) | h <;> subst h <;> simp [roots, coxeter]

/-- The extended Dynkin diagram of a rank-`n` component has `n + 1` nodes: the
`n` simple roots and the affine node. -/
theorem extMarks_length (c : Comp) (h : c.ok) : c.extMarks.length = c.rank + 1 := by
  obtain ⟨l, n⟩ := c
  cases l
  · simp [extMarks]
  · simp only [ok, decide_eq_true_eq] at h
    simp only [extMarks, List.length_append, List.length_replicate]
    simp
    omega
  · simp only [ok, Bool.or_eq_true, beq_iff_eq] at h
    rcases h with (h | h) | h <;> subst h <;> simp [extMarks]

/-- The marks of an extended Dynkin diagram sum to the Coxeter number.  This is
the identity the deep-hole certificate `∑ nᵢ vᵢ = h c` is balanced against. -/
theorem extMarks_sum (c : Comp) (h : c.ok) : c.extMarks.sum = c.coxeter := by
  obtain ⟨l, n⟩ := c
  cases l
  · simp [extMarks, coxeter]
  · simp only [ok, decide_eq_true_eq] at h
    simp only [extMarks, coxeter, List.sum_append, List.sum_replicate, smul_eq_mul]
    simp
    omega
  · simp only [ok, Bool.or_eq_true, beq_iff_eq] at h
    rcases h with (h | h) | h <;> subst h <;> simp [extMarks, coxeter]

end Comp

/-! ## 2.  The catalogue: every component that can occur at total rank 24 -/

/-- Every distinct simply-laced component of rank at most 24: `A_1 … A_24`,
`D_4 … D_24`, `E_6`, `E_7`, `E_8`.  It is a *bound*, not a table of answers —
`mem_catalogue_of_ok` proves nothing else can occur in a system of rank 24. -/
def catalogue : List Comp :=
  (List.range 24).map (fun i => ⟨.A, i + 1⟩) ++
  (List.range 21).map (fun i => ⟨.D, i + 4⟩) ++
  [⟨.E, 6⟩, ⟨.E, 7⟩, ⟨.E, 8⟩]

theorem catalogue_length : catalogue.length = 48 := by decide

theorem catalogue_nodup : catalogue.Nodup := by decide

theorem catalogue_ok : ∀ c ∈ catalogue, c.ok := by decide

theorem catalogue_rank_pos : ∀ c ∈ catalogue, 0 < c.rank := by decide

theorem catalogue_rank_le : ∀ c ∈ catalogue, c.rank ≤ 24 := by decide

/-- A component that is a genuine simply-laced diagram of rank at most 24 is in
the catalogue.  Since ranks are positive and a Niemeier system has total rank
24, no component of such a system escapes the catalogue — which is what makes
the enumeration below a proof rather than a sample. -/
theorem mem_catalogue_of_ok (c : Comp) (hok : c.ok) (hle : c.rank ≤ 24) :
    c ∈ catalogue := by
  obtain ⟨l, n⟩ := c
  cases l
  · simp only [Comp.ok, decide_eq_true_eq] at hok
    interval_cases n <;> decide
  · simp only [Comp.ok, decide_eq_true_eq] at hok
    interval_cases n <;> decide
  · simp only [Comp.ok, Bool.or_eq_true, beq_iff_eq] at hok
    rcases hok with (h | h) | h <;> subst h <;> decide

/-! ## 3.  The search -/

/-- The total rank of a multiplicity vector read against a list of components. -/
def weight : List Comp → List ℕ → ℕ
  | c :: cs, k :: v => c.rank * k + weight cs v
  | _, _ => 0

/-- Every multiplicity vector over `cs` of total rank `r`: a knapsack, written
so that both halves of its correctness are provable by induction. -/
def gen : List Comp → ℕ → List (List ℕ)
  | [], 0 => [[]]
  | [], _ + 1 => []
  | c :: cs, r =>
      (List.range (r / c.rank + 1)).flatMap (fun k =>
        (gen cs (r - k * c.rank)).map (fun rest => k :: rest))

/-- Nothing spurious is generated. -/
theorem gen_sound : ∀ (cs : List Comp) (r : ℕ) (v : List ℕ),
    v ∈ gen cs r → v.length = cs.length ∧ weight cs v = r := by
  intro cs
  induction cs with
  | nil =>
      intro r v hv
      cases r with
      | zero => simp [gen] at hv; simp [hv, weight]
      | succ n => simp [gen] at hv
  | cons c cs ih =>
      intro r v hv
      simp only [gen, List.mem_flatMap, List.mem_map, List.mem_range] at hv
      obtain ⟨k, hk, rest, hrest, rfl⟩ := hv
      obtain ⟨hlen, hw⟩ := ih _ _ hrest
      have hkle : k * c.rank ≤ r :=
        Nat.le_trans (Nat.mul_le_mul_right _ (by omega)) (Nat.div_mul_le_self r c.rank)
      refine ⟨by simp [hlen], ?_⟩
      simp only [weight, hw, Nat.mul_comm c.rank k]
      omega

/-- Nothing is missed. -/
theorem mem_gen : ∀ (cs : List Comp), (∀ c ∈ cs, 0 < c.rank) → ∀ v : List ℕ,
    v.length = cs.length → v ∈ gen cs (weight cs v) := by
  intro cs
  induction cs with
  | nil => intro _ v hv; cases v <;> simp_all [gen, weight]
  | cons c cs ih =>
      intro hpos v hv
      cases v with
      | nil => simp at hv
      | cons k rest =>
        have hlen : rest.length = cs.length := by simpa using hv
        have hrec := ih (fun d hd => hpos d (List.mem_cons_of_mem _ hd)) rest hlen
        have hc : 0 < c.rank := hpos c (List.mem_cons_self ..)
        have hcomm : k * c.rank = c.rank * k := Nat.mul_comm _ _
        simp only [weight, gen, List.mem_flatMap, List.mem_map, List.mem_range]
        refine ⟨k, ?_, rest, ?_, rfl⟩
        · have : k ≤ (c.rank * k + weight cs rest) / c.rank :=
            (Nat.le_div_iff_mul_le hc).2 (by omega)
          omega
        · have h2 : c.rank * k + weight cs rest - k * c.rank = weight cs rest := by omega
          rw [h2]; exact hrec

/-- The components a multiplicity vector actually uses, with their
multiplicities. -/
def used (v : List ℕ) : List (Comp × ℕ) :=
  (catalogue.zip v).filter (fun p => p.2 != 0)

/-- The Coxeter number of the first component used, or 0 for the empty vector. -/
def coxOf (v : List ℕ) : ℕ := ((used v).headD (⟨.A, 1⟩, 0)).1.coxeter

/-- The second Niemeier condition: one Coxeter number across all components. -/
def sameCox (v : List ℕ) : Bool := (used v).all (fun p => p.1.coxeter == coxOf v)

/-- The search: all multiplicity vectors of total rank 24 whose components share
a Coxeter number. -/
def niemeierVectors : List (List ℕ) := (gen catalogue 24).filter sameCox

/-! ## 4.  What the search finds -/

/-- There are exactly 23 Niemeier root systems. -/
theorem niemeierVectors_length : niemeierVectors.length = 23 := by native_decide

theorem niemeierVectors_nodup : niemeierVectors.Nodup := by native_decide

theorem niemeierVectors_weight : ∀ v ∈ niemeierVectors, weight catalogue v = 24 :=
  fun _ hv => (gen_sound _ _ _ (List.mem_filter.1 hv).1).2

theorem niemeierVectors_length_eq : ∀ v ∈ niemeierVectors, v.length = catalogue.length :=
  fun _ hv => (gen_sound _ _ _ (List.mem_filter.1 hv).1).1

theorem niemeierVectors_sameCox : ∀ v ∈ niemeierVectors, sameCox v :=
  fun _ hv => (List.mem_filter.1 hv).2

/-- The name of a component with a multiplicity, as the literature writes it. -/
def Letter.str : Letter → String
  | .A => "A"
  | .D => "D"
  | .E => "E"

/-- The classical name of a root system, `A_5^4 D_4` and so on. -/
def systemName (v : List ℕ) : String :=
  String.intercalate " " ((used v).map (fun p =>
    p.1.letter.str ++ "_" ++ toString p.1.rank ++
      (if p.2 = 1 then "" else "^" ++ toString p.2)))

/-- The search reproduces the classical list of 23 names. -/
theorem niemeier_names :
    niemeierVectors.map systemName =
      ["E_8^3", "E_6^4", "D_24", "D_16 E_8", "D_12^2", "D_10 E_7^2", "D_8^3",
       "D_6^4", "D_4^6", "A_24", "A_17 E_7", "A_15 D_9", "A_12^2",
       "A_11 D_7 E_6", "A_9^2 D_6", "A_8^3", "A_7^2 D_5^2", "A_6^4",
       "A_5^4 D_4", "A_4^6", "A_3^8", "A_2^12", "A_1^24"] := by
  native_decide

/-- The Coxeter numbers of the 23, in the order the search produces them. -/
theorem niemeier_coxeter_numbers :
    niemeierVectors.map coxOf =
      [30, 12, 46, 30, 22, 18, 14, 10, 6, 25, 18, 16, 13, 12, 10, 9, 8, 7, 6,
       5, 4, 3, 2] := by
  native_decide

/-- The total number of roots of a system. -/
def totalRoots (v : List ℕ) : ℕ := ((used v).map (fun p => p.1.roots * p.2)).sum

/-- The number of nodes of the extended diagram: one per simple root, plus one
affine node per component. -/
def totalNodes (v : List ℕ) : ℕ := ((used v).map (fun p => (p.1.rank + 1) * p.2)).sum

/-- The number of irreducible components, counted with multiplicity. -/
def numComponents (v : List ℕ) : ℕ := ((used v).map (fun p => p.2)).sum

/-- The sum of all the marks of the extended diagram. -/
def totalMarks (v : List ℕ) : ℕ := ((used v).map (fun p => p.1.extMarks.sum * p.2)).sum

/-- Every Niemeier root system has `24 h` roots — the identity
`roots = rank × h` at `rank = 24`. -/
theorem niemeier_roots : ∀ v ∈ niemeierVectors, totalRoots v = 24 * coxOf v := by
  native_decide

/-- A deep hole of type `R` has `24 + (number of components of R)` nearest
lattice points: the extended diagram's nodes. -/
theorem niemeier_nodes :
    ∀ v ∈ niemeierVectors, totalNodes v = 24 + numComponents v := by
  native_decide

/-- The marks of the whole diagram sum to `h` per component. -/
theorem niemeier_marks :
    ∀ v ∈ niemeierVectors, totalMarks v = coxOf v * numComponents v := by
  native_decide

/-! ## 5.  The abstract statement: a root system, with no catalogue in sight -/

/-- A **Niemeier root system**: a multiset of simply-laced components, all with
the same Coxeter number, of total rank 24.  Nothing here mentions the
catalogue, the enumeration or any ordering. -/
structure IsRootSystem (s : Multiset Comp) : Prop where
  ok : ∀ c ∈ s, c.ok
  rank : (s.map Comp.rank).sum = 24
  coxeter : ∀ c ∈ s, ∀ d ∈ s, c.coxeter = d.coxeter

/-- The Leech lattice is the 24th even unimodular lattice in this dimension and
has no roots at all, so the empty system is not one of the 23. -/
theorem leech_not_root_system : ¬ IsRootSystem 0 := by
  intro h
  have := h.rank
  simp at this

/-- The multiplicity vector of an abstract system, read against the catalogue. -/
def multVector (s : Multiset Comp) : List ℕ := catalogue.map (fun c => Multiset.count c s)

/-- The multiset a multiplicity vector describes. -/
def bag : List Comp → List ℕ → Multiset Comp
  | c :: cs, k :: v => Multiset.replicate k c + bag cs v
  | _, _ => 0

/-- The multiset a Niemeier vector describes. -/
def toMultiset (v : List ℕ) : Multiset Comp := bag catalogue v

theorem weight_map (f : Comp → ℕ) : ∀ L : List Comp,
    weight L (L.map f) = (L.map (fun c => c.rank * f c)).sum := by
  intro L; induction L with
  | nil => simp [weight]
  | cons c cs ih => simp [weight, ih]

private theorem sum_if_eq : ∀ {L : List Comp}, L.Nodup → ∀ {a : Comp}, a ∈ L →
    (L.map (fun c => if c = a then c.rank else 0)).sum = a.rank := by
  intro L
  induction L with
  | nil => intro _ a ha; simp at ha
  | cons b L ih =>
      intro hnd a ha
      rw [List.nodup_cons] at hnd
      rcases List.mem_cons.1 ha with rfl | ha'
      · have hzero : (L.map (fun c => if c = a then c.rank else 0)).sum = 0 := by
          apply List.sum_eq_zero
          intro x hx
          simp only [List.mem_map] at hx
          obtain ⟨c, hc, rfl⟩ := hx
          have : c ≠ a := by rintro rfl; exact hnd.1 hc
          simp [this]
        simp [hzero]
      · have hba : b ≠ a := by rintro rfl; exact hnd.1 ha'
        simp [hba, ih hnd.2 ha']

private theorem sum_map_add (f g : Comp → ℕ) : ∀ L : List Comp,
    (L.map (fun c => f c + g c)).sum = (L.map f).sum + (L.map g).sum := by
  intro L; induction L with
  | nil => simp
  | cons b L ih => simp [ih]; omega

/-- The total rank an abstract system claims and the weight its multiplicity
vector carries are the same number. -/
theorem weight_multVector (L : List Comp) (hL : L.Nodup) :
    ∀ s : Multiset Comp, (∀ c ∈ s, c ∈ L) →
      weight L (L.map (fun c => Multiset.count c s)) = (s.map Comp.rank).sum := by
  intro s
  induction s using Multiset.induction_on with
  | empty => intro _; rw [weight_map]; simp
  | cons a s ih =>
      intro hs
      have ha : a ∈ L := hs a (Multiset.mem_cons_self _ _)
      have hs' : ∀ c ∈ s, c ∈ L := fun c hc => hs c (Multiset.mem_cons_of_mem hc)
      rw [weight_map] at *
      have hsplit : ∀ c : Comp, c.rank * Multiset.count c (a ::ₘ s)
          = c.rank * Multiset.count c s + (if c = a then c.rank else 0) := by
        intro c
        by_cases h : c = a
        · subst h; simp [Multiset.count_cons_self, Nat.mul_add]
        · simp [Multiset.count_cons_of_ne h, h]
      simp only [hsplit]
      rw [sum_map_add (fun c => c.rank * Multiset.count c s)
            (fun c => if c = a then c.rank else 0) L, sum_if_eq hL ha, ih hs']
      simp
      omega

/-- Reading a multiplicity vector off a list of components and back. -/
private theorem mem_zip_map (f : Comp → ℕ) : ∀ (L : List Comp) (p : Comp × ℕ),
    p ∈ L.zip (L.map f) → p.2 = f p.1 := by
  intro L
  induction L with
  | nil => intro p hp; simp at hp
  | cons c cs ih =>
      intro p hp
      simp only [List.map_cons, List.zip_cons_cons, List.mem_cons] at hp
      rcases hp with rfl | hp
      · rfl
      · exact ih p hp

private theorem headD_mem {α : Type*} (l : List α) (d : α) (h : l ≠ []) :
    l.headD d ∈ l := by
  cases l with
  | nil => exact absurd rfl h
  | cons x xs => simp

/-- If all the components a vector uses share a Coxeter number, the Boolean
check says so. -/
theorem sameCox_of_pairwise (v : List ℕ)
    (h : ∀ p ∈ used v, ∀ q ∈ used v, p.1.coxeter = q.1.coxeter) : sameCox v := by
  simp only [sameCox, List.all_eq_true, beq_iff_eq, coxOf]
  intro p hp
  exact h p hp _ (headD_mem _ _ (by rintro he; rw [he] at hp; simp at hp))

/-- Conversely, the Boolean check gives the pairwise statement back. -/
theorem pairwise_of_sameCox (v : List ℕ) (h : sameCox v) :
    ∀ p ∈ used v, ∀ q ∈ used v, p.1.coxeter = q.1.coxeter := by
  simp only [sameCox, List.all_eq_true, beq_iff_eq] at h
  intro p hp q hq
  rw [h p hp, h q hq]

/-- **Completeness of the search.**  Every abstract Niemeier root system is one
of the vectors the enumeration finds. -/
theorem multVector_mem_niemeierVectors (s : Multiset Comp) (h : IsRootSystem s) :
    multVector s ∈ niemeierVectors := by
  have hsub : ∀ c ∈ s, c ∈ catalogue := by
    intro c hc
    refine mem_catalogue_of_ok c (h.ok c hc) ?_
    have hle : c.rank ≤ (s.map Comp.rank).sum :=
      Multiset.single_le_sum (fun _ _ => Nat.zero_le _) _ (Multiset.mem_map_of_mem _ hc)
    have hr := h.rank
    omega
  have hw : weight catalogue (multVector s) = 24 := by
    rw [multVector, weight_multVector catalogue catalogue_nodup s hsub, h.rank]
  have hmem : multVector s ∈ gen catalogue 24 := by
    rw [← hw]
    exact mem_gen catalogue catalogue_rank_pos _ (by simp [multVector])
  refine List.mem_filter.2 ⟨hmem, ?_⟩
  refine sameCox_of_pairwise _ ?_
  have hused : ∀ p ∈ used (multVector s), p.1 ∈ s := by
    intro p hp
    have hp' := List.mem_filter.1 hp
    have hcount : p.2 = Multiset.count p.1 s :=
      mem_zip_map (fun c => Multiset.count c s) catalogue p hp'.1
    have : p.2 ≠ 0 := by simpa using hp'.2
    rw [hcount] at this
    exact Multiset.count_ne_zero.1 this
  intro p hp q hq
  exact h.coxeter p.1 (hused p hp) q.1 (hused q hq)

/-! ## 6.  The count -/

theorem bag_rank_sum : ∀ (cs : List Comp) (v : List ℕ),
    ((bag cs v).map Comp.rank).sum = weight cs v := by
  intro cs
  induction cs with
  | nil => intro v; cases v <;> simp [bag, weight]
  | cons c cs ih =>
      intro v
      cases v with
      | nil => simp [bag, weight]
      | cons k rest =>
          simp [bag, weight, ih rest, Multiset.map_replicate, Multiset.sum_replicate,
            Nat.mul_comm]

theorem mem_bag : ∀ (cs : List Comp) (v : List ℕ) (x : Comp),
    x ∈ bag cs v → x ∈ cs := by
  intro cs
  induction cs with
  | nil => intro v x hx; cases v <;> simp [bag] at hx
  | cons c cs ih =>
      intro v x hx
      cases v with
      | nil => simp [bag] at hx
      | cons k rest =>
          simp only [bag, Multiset.mem_add, Multiset.mem_replicate] at hx
          rcases hx with ⟨_, rfl⟩ | hx
          · exact List.mem_cons_self ..
          · exact List.mem_cons_of_mem _ (ih rest x hx)

/-- An element of the multiset a vector describes is one of the components the
vector uses. -/
theorem mem_used_of_mem_bag : ∀ (cs : List Comp) (v : List ℕ) (x : Comp),
    x ∈ bag cs v → ∃ k, (x, k) ∈ (cs.zip v).filter (fun p => p.2 != 0) := by
  intro cs
  induction cs with
  | nil => intro v x hx; cases v <;> simp [bag] at hx
  | cons c cs ih =>
      intro v x hx
      cases v with
      | nil => simp [bag] at hx
      | cons k rest =>
          simp only [bag, Multiset.mem_add, Multiset.mem_replicate] at hx
          rcases hx with ⟨hk, rfl⟩ | hx
          · exact ⟨k, List.mem_filter.2 ⟨by simp, by simpa using hk⟩⟩
          · obtain ⟨j, hj⟩ := ih rest x hx
            refine ⟨j, ?_⟩
            simp only [List.zip_cons_cons, List.filter]
            by_cases hk0 : k = 0
            · simpa [hk0] using hj
            · have hkb : (k != 0) = true := by simpa using hk0
              rw [hkb]
              exact List.mem_cons_of_mem _ hj

theorem count_bag : ∀ (cs : List Comp), cs.Nodup → ∀ v : List ℕ, v.length = cs.length →
    cs.map (fun c => Multiset.count c (bag cs v)) = v := by
  intro cs
  induction cs with
  | nil => intro _ v hv; cases v <;> simp_all
  | cons c cs ih =>
      intro hnd v hv
      cases v with
      | nil => simp at hv
      | cons k rest =>
          rw [List.nodup_cons] at hnd
          have hlen : rest.length = cs.length := by simpa using hv
          have hzero : Multiset.count c (bag cs rest) = 0 := by
            by_contra hne
            exact hnd.1 (mem_bag cs rest c (Multiset.count_ne_zero.1 hne))
          have hhead : Multiset.count c (bag (c :: cs) (k :: rest)) = k := by
            simp [bag, hzero]
          have htail : cs.map (fun d => Multiset.count d (bag (c :: cs) (k :: rest)))
              = cs.map (fun d => Multiset.count d (bag cs rest)) := by
            refine List.map_congr_left ?_
            intro d hd
            have hdc : ¬ (c = d) := by rintro rfl; exact hnd.1 hd
            simp [bag, Multiset.count_replicate, hdc]
          simp only [List.map_cons, hhead, htail, ih hnd.2 rest hlen]

/-- The two readings are inverse to each other on vectors of the right length. -/
theorem multVector_toMultiset (v : List ℕ) (hv : v.length = catalogue.length) :
    multVector (toMultiset v) = v :=
  count_bag catalogue catalogue_nodup v hv

/-- And inverse the other way on abstract systems. -/
theorem toMultiset_multVector (s : Multiset Comp) (h : IsRootSystem s) :
    toMultiset (multVector s) = s := by
  have hsub : ∀ c ∈ s, c ∈ catalogue := by
    intro c hc
    refine mem_catalogue_of_ok c (h.ok c hc) ?_
    have hle : c.rank ≤ (s.map Comp.rank).sum :=
      Multiset.single_le_sum (fun _ _ => Nat.zero_le _) _ (Multiset.mem_map_of_mem _ hc)
    have hr := h.rank
    omega
  refine Multiset.ext.2 ?_
  intro c
  by_cases hc : c ∈ catalogue
  · have hread := count_bag catalogue catalogue_nodup (multVector s) (by simp [multVector])
    have := List.get_of_mem hc
    -- read both sides off the catalogue position of `c`
    obtain ⟨i, hi⟩ := List.mem_iff_getElem.1 hc
    obtain ⟨hlt, hval⟩ := hi
    have h1 : (catalogue.map (fun d => Multiset.count d (toMultiset (multVector s))))[i]!
        = Multiset.count c (toMultiset (multVector s)) := by
      simp [List.getElem!_eq_getElem?_getD, List.getElem?_map,
        List.getElem?_eq_getElem hlt, hval]
    have h2 : (multVector s)[i]! = Multiset.count c s := by
      simp [multVector, List.getElem!_eq_getElem?_getD, List.getElem?_map,
        List.getElem?_eq_getElem hlt, hval]
    rw [← h1, ← h2, toMultiset, hread]
  · have hcs : c ∉ s := fun h' => hc (hsub c h')
    have hcb : c ∉ toMultiset (multVector s) := fun h' =>
      hc (mem_bag catalogue (multVector s) c h')
    rw [Multiset.count_eq_zero_of_notMem hcs, Multiset.count_eq_zero_of_notMem hcb]

/-- Everything the search finds really is a Niemeier root system. -/
theorem isRootSystem_toMultiset (v : List ℕ) (hv : v ∈ niemeierVectors) :
    IsRootSystem (toMultiset v) := by
  refine ⟨?_, ?_, ?_⟩
  · intro c hc
    exact catalogue_ok c (mem_bag catalogue v c hc)
  · rw [toMultiset, bag_rank_sum, niemeierVectors_weight v hv]
  · intro c hc d hd
    obtain ⟨k, hk⟩ := mem_used_of_mem_bag catalogue v c hc
    obtain ⟨j, hj⟩ := mem_used_of_mem_bag catalogue v d hd
    exact pairwise_of_sameCox v (niemeierVectors_sameCox v hv) (c, k) hk (d, j) hj

/-- **There are exactly 23 Niemeier root systems.**  The statement is about
multisets of ADE components — no catalogue, no enumeration, no ordering — and
the number is the one the search finds.  `IsRootSystem` is Venkov's
combinatorial condition, so this is the classification of the *root systems*;
their realisation as lattices is not part of the statement. -/
theorem card_root_systems : {s : Multiset Comp | IsRootSystem s}.ncard = 23 := by
  have himg : {s : Multiset Comp | IsRootSystem s} = toMultiset '' {v | v ∈ niemeierVectors} := by
    ext s
    constructor
    · intro hs
      exact ⟨multVector s, multVector_mem_niemeierVectors s hs, toMultiset_multVector s hs⟩
    · rintro ⟨v, hv, rfl⟩
      exact isRootSystem_toMultiset v hv
  have hfin : {v : List ℕ | v ∈ niemeierVectors} = ↑niemeierVectors.toFinset := by
    ext v; simp
  have hinj : Set.InjOn toMultiset {v | v ∈ niemeierVectors} := by
    intro a ha b hb hab
    have ha' := multVector_toMultiset a (niemeierVectors_length_eq a ha)
    have hb' := multVector_toMultiset b (niemeierVectors_length_eq b hb)
    rw [← ha', ← hb', hab]
  rw [himg, Set.InjOn.ncard_image hinj, hfin, Set.ncard_coe_finset,
    List.toFinset_card_of_nodup niemeierVectors_nodup, niemeierVectors_length]

end GLM.Niemeier
