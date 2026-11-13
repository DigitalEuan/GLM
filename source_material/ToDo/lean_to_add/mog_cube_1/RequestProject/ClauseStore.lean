import Mathlib
import RequestProject.ThreeCube
import RequestProject.SentenceCode
import RequestProject.Causation

/-!
# One cube per role, and a chain of clauses on the code

Report 2 §7.1, the first thing that was *not* achieved:

> **The 24 cells cannot be a dimension record and a clause record at once.**
> `IntegerCube.encG` and `SentenceCode.clauseCode` are two different uses of the
> same surface.  A working system needs one cube per role and a discipline for
> addressing them; nothing here provides that.

And §8: *"Extending to a chain of clauses is where `because` and `if` would
become codeword-level operations rather than sentence-level ones."*

This file provides the discipline.

## The frame

Every record on the surface is one Turyn codeword built from three four-bit
fields, and the discipline is a fixed reading of those twelve bits:

    field 0 :  role (2 bits) ‖ payload (2 bits)
    field 1 :  payload (4 bits)
    field 2 :  payload (4 bits)

so there are four **roles** — `dimension`, `clause`, `link`, `spare` — each with
its own 10-bit address space of 1024 records (`role_capacity`).  A dimension
record holds five exponents; a clause record holds a literal of the language; a
link record holds a connective and the addresses of the two clauses it joins.

## What is proved

* `rec_min_distance` — any two different records differ in at least 8 of the 24
  cells.  This is proved from linearity of the Turyn construction plus one
  finite weight check over the 4096 records, not by comparing 4096² pairs.
* `roles_are_separated` — in particular a dimension record and a clause record
  are never within 7 cells of each other, which is exactly the confusion
  report 2 §7.1 complained about.
* `decodeRec_correct` — any record damaged in up to 3 cells decodes back to
  itself, uniquely, *including its role*.
* `link_is_a_codeword_operation` — `because` between two clauses is itself a
  record on the surface: it has an address, a distance-8 guarantee, and repairs
  like any other.
* `repaired_store_is_still_sound` — the payoff.  If a store is semantically
  sound (every clause true now, every `because` link licensed by the timed
  connective of `Causation.lean`) and every record is damaged in at most 3
  cells, then what is read back is the same store, so the reasoning survives
  the damage.
-/

namespace ClauseStore

open ThreeCube SentenceCode Semantics

set_option maxRecDepth 100000

/-! ## 1. Four-bit fields -/

/-- A four-bit field as an affine cube. -/
def cube16 (k : Fin 16) : Cube := cubeOfNat k.val

/-- Bitwise sum of two fields. -/
def xor16 (k m : Fin 16) : Fin 16 :=
  ⟨k.val ^^^ m.val, by have := Nat.xor_lt_two_pow (n := 4) k.isLt m.isLt; omega⟩

/-- **Adding fields adds cubes.** -/
theorem cube16_xor (k m : Fin 16) :
    (fun v => xor (cube16 k v) (cube16 m v)) = cube16 (xor16 k m) := by
  revert k m; decide

/-! ## 2. Records -/

/-- A record on the surface: a role, and ten bits of payload. -/
structure Rec where
  role : Fin 4
  p0 : Fin 4
  f1 : Fin 16
  f2 : Fin 16
deriving DecidableEq, Repr

/-- The first field: role in the top two bits, payload in the bottom two. -/
def field0 (r : Rec) : Fin 16 := ⟨4 * r.role.val + r.p0.val, by omega⟩

/-- **The record as a codeword.** -/
def encode (r : Rec) : Tri := turyn (cube16 (field0 r)) (cube16 r.f1) (cube16 r.f2)

/-- The triple of fields of a record. -/
def fields (r : Rec) : Fin 16 × Fin 16 × Fin 16 := (field0 r, r.f1, r.f2)

/-- Distinct records have distinct field triples. -/
theorem fields_injective {r q : Rec} (h : fields r = fields q) : r = q := by
  obtain ⟨hr, hp, hf1, hf2⟩ := r
  obtain ⟨hr', hp', hf1', hf2'⟩ := q
  simp only [fields, field0, Prod.mk.injEq, Fin.mk.injEq] at h
  obtain ⟨h0, h1, h2⟩ := h
  have : hr = hr' ∧ hp = hp' := by
    constructor <;> (apply Fin.ext; omega)
  simp [this.1, this.2, h1, h2]

/-- Every record. -/
def allRecs : List Rec :=
  (List.finRange 4).flatMap fun r => (List.finRange 4).flatMap fun p =>
    (List.finRange 16).flatMap fun f1 => (List.finRange 16).map fun f2 => ⟨r, p, f1, f2⟩

theorem mem_allRecs (r : Rec) : r ∈ allRecs := by
  obtain ⟨a, b, c, d⟩ := r
  exact List.mem_flatMap.mpr ⟨a, List.mem_finRange _,
    List.mem_flatMap.mpr ⟨b, List.mem_finRange _,
      List.mem_flatMap.mpr ⟨c, List.mem_finRange _,
        List.mem_map.mpr ⟨d, List.mem_finRange _, rfl⟩⟩⟩⟩

/-- **Each role addresses 1024 records**, and the surface holds 4096 in all —
the `2^12` words of the code, partitioned four ways. -/
theorem role_capacity :
    allRecs.length = 4096 ∧
    ∀ k : Fin 4, (allRecs.filter fun r => decide (r.role = k)).length = 1024 := by
  refine ⟨by decide, ?_⟩
  intro k
  fin_cases k <;> decide

/-! ## 3. Distance -/

/-- The record built from a field triple. -/
def recOf (f : Fin 16 × Fin 16 × Fin 16) : Tri :=
  turyn (cube16 f.1) (cube16 f.2.1) (cube16 f.2.2)

theorem encode_eq_recOf (r : Rec) : encode r = recOf (fields r) := rfl

/-- **Every nonzero record word weighs at least 8** — one check over the 4096
field triples. -/
theorem recOf_weight (f : Fin 16 × Fin 16 × Fin 16) :
    wt3 (recOf f) = 0 ∨ 8 ≤ wt3 (recOf f) := by
  revert f; native_decide

/-- …and only the all-zero triple gives weight 0. -/
theorem recOf_zero_iff (f : Fin 16 × Fin 16 × Fin 16) :
    wt3 (recOf f) = 0 ↔ f = (0, 0, 0) := by
  revert f; native_decide

/-- The difference of two record words is the record word of the difference:
the frame is linear. -/
theorem dxor_recOf (f g : Fin 16 × Fin 16 × Fin 16) :
    dxor (recOf f) (recOf g) = recOf (xor16 f.1 g.1, xor16 f.2.1 g.2.1, xor16 f.2.2 g.2.2) := by
  have h := turyn_add (cube16 f.1) (cube16 f.2.1) (cube16 f.2.2)
    (cube16 g.1) (cube16 g.2.1) (cube16 g.2.2)
  funext n v
  have := congrFun (congrFun h n) v
  simp only [dxor, recOf]
  rw [this, cube16_xor, cube16_xor, cube16_xor]

theorem xor16_eq_zero_iff (k m : Fin 16) : xor16 k m = 0 ↔ k = m := by
  revert k m; decide

/-- **Any two different records differ in at least 8 of the 24 cells.** -/
theorem rec_min_distance {r q : Rec} (h : r ≠ q) : 8 ≤ dist3 (encode r) (encode q) := by
  have hne : fields r ≠ fields q := fun hc => h (fields_injective hc)
  rw [encode_eq_recOf, encode_eq_recOf, dist3, dxor_recOf]
  rcases recOf_weight (xor16 (fields r).1 (fields q).1, xor16 (fields r).2.1 (fields q).2.1,
      xor16 (fields r).2.2 (fields q).2.2) with hz | h8
  · exfalso
    have := (recOf_zero_iff _).mp hz
    simp only [Prod.mk.injEq] at this
    obtain ⟨h1, h2, h3⟩ := this
    exact hne (Prod.ext ((xor16_eq_zero_iff _ _).mp h1)
      (Prod.ext ((xor16_eq_zero_iff _ _).mp h2) ((xor16_eq_zero_iff _ _).mp h3)))
  · exact h8

/-- **The confusion of report 2 §7.1 cannot happen.**  A record in one role is
never within 7 cells of a record in another: a dimension record can never be
mistaken for a clause. -/
theorem roles_are_separated {r q : Rec} (h : r.role ≠ q.role) :
    8 ≤ dist3 (encode r) (encode q) :=
  rec_min_distance fun hc => h (by rw [hc])

/-! ## 4. Repair -/

/-- Nearest-record decoding within the guaranteed radius. -/
def decodeRec (t : Tri) : Option Rec := allRecs.find? fun r => decide (dist3 t (encode r) ≤ 3)

/-- **A record damaged in up to three cells reads back, uniquely and with its
role intact.** -/
theorem decodeRec_correct {t : Tri} {r : Rec} (h : dist3 t (encode r) ≤ 3) :
    decodeRec t = some r := by
  have huniq : ∀ q : Rec, dist3 t (encode q) ≤ 3 → q = r := by
    intro q hq
    by_contra hne
    have hd : dist3 (encode q) (encode r) ≤ 6 := by
      have := dist3_triangle (encode q) (encode r) t
      rw [dist3_comm (encode q) t] at this
      omega
    have := rec_min_distance hne
    omega
  rcases hfind : decodeRec t with _ | q
  · exfalso
    have : ∀ s ∈ allRecs, ¬ (decide (dist3 t (encode s) ≤ 3) = true) := by
      intro s hs
      have := List.find?_eq_none.mp hfind s hs
      simpa using this
    exact (this r (mem_allRecs r)) (by simpa using h)
  · have hq : dist3 t (encode q) ≤ 3 := by
      have := List.find?_some (p := fun s => decide (dist3 t (encode s) ≤ 3)) hfind
      simpa using this
    rw [huniq q hq]

/-! ## 5. The three roles -/

/-- The five exponents of a dimension record, two bits each. -/
def dimRec (eL eM eT eI eΘ : Fin 4) : Rec :=
  ⟨0, eL, ⟨4 * eM.val + eT.val, by omega⟩, ⟨4 * eI.val + eΘ.val, by omega⟩⟩

/-- A clause record: polarity, predicate, and the two things. -/
def clauseRec (l : Lit) : Rec :=
  ⟨1, if l.2 then 0 else 1, ⟨predOf l % 16, Nat.mod_lt _ (by norm_num)⟩,
   ⟨(4 * (subjOf l % 4) + objOf l % 4) % 16, Nat.mod_lt _ (by norm_num)⟩⟩

/-- The connectives that can join two clauses. -/
inductive Link | becauseL | ifL | andL | afterL
deriving DecidableEq, Repr

def linkIdx : Link → Fin 4
  | .becauseL => 0 | .ifL => 1 | .andL => 2 | .afterL => 3

/-- A link record: which connective, and the addresses of the two clauses. -/
def linkRec (k : Link) (i j : Fin 16) : Rec := ⟨2, linkIdx k, i, j⟩

/-- **Distinct clauses get distinct records** — the vocabulary of 60 literals
lands injectively in the clause role. -/
theorem clauseRec_injective : (allLits.map clauseRec).Nodup := by native_decide

/-- **`because` is a codeword operation.**  A link between two clauses is itself
a record: it has an address, it is at distance 8 from every other record, and it
repairs like any other. -/
theorem link_is_a_codeword_operation (k k' : Link) (i j i' j' : Fin 16)
    (h : (k, i, j) ≠ (k', i', j')) :
    8 ≤ dist3 (encode (linkRec k i j)) (encode (linkRec k' i' j')) := by
  refine rec_min_distance ?_
  intro hc
  apply h
  simp only [linkRec, Rec.mk.injEq] at hc
  obtain ⟨_, hk, hi, hj⟩ := hc
  have : k = k' := by
    cases k <;> cases k' <;> simp_all [linkIdx]
  simp [this, hi, hj]

/-- Clause records and link records never collide. -/
theorem clause_link_separated (l : Lit) (k : Link) (i j : Fin 16) :
    8 ≤ dist3 (encode (clauseRec l)) (encode (linkRec k i j)) :=
  roles_are_separated (by simp [clauseRec, linkRec])

/-- A dimension record is never mistaken for a clause: the failure named in
report 2 §7.1, ruled out. -/
theorem dimension_clause_separated (eL eM eT eI eΘ : Fin 4) (l : Lit) :
    8 ≤ dist3 (encode (dimRec eL eM eT eI eΘ)) (encode (clauseRec l)) :=
  roles_are_separated (by simp [dimRec, clauseRec])

/-! ## 6. A chain of clauses, stored and repaired -/

/-- A store: clauses at addresses `0, 1, …`, and links between those
addresses. -/
structure Store where
  clauses : List Lit
  links : List (Link × Fin 16 × Fin 16)

/-- The records a store occupies. -/
def storeRecs (s : Store) : List Rec :=
  s.clauses.map clauseRec ++ s.links.map fun t => linkRec t.1 t.2.1 t.2.2

/-- The store is semantically sound in a history: every clause is true now, and
every `because` link really is licensed by the timed connective. -/
def storeSound (h : Causation.Hist) (s : Store) : Prop :=
  (∀ l ∈ s.clauses, evalLit l (Causation.nowW h) = true) ∧
  (∀ t ∈ s.links, t.1 = Link.becauseL →
    ∀ l m : Lit, s.clauses[t.2.1.val]? = some l → s.clauses[t.2.2.val]? = some m →
      Causation.causalBecause h l m = true)

/-- **The payoff.**  If every record of a sound store is damaged in at most
three cells, the store read back is the store that was written — so every
clause is still true and every `because` link is still licensed.  The reasoning
survives the damage, not just the letters. -/
theorem repaired_store_is_still_sound {h : Causation.Hist} {s : Store}
    (hsound : storeSound h s) (received : List Tri)
    (hlen : received.length = (storeRecs s).length)
    (hclose : ∀ i (hi : i < received.length),
      dist3 (received[i]) (encode ((storeRecs s)[i]'(by omega))) ≤ 3) :
    (∀ i (hi : i < received.length), decodeRec (received[i]) =
      some ((storeRecs s)[i]'(by omega))) ∧ storeSound h s :=
  ⟨fun i hi => decodeRec_correct (hclose i hi), hsound⟩

/-- A store of two clauses and the `because` between them. -/
def demoStore : Store :=
  ⟨[(.warm .water, false), (.frozen .water, true)], [(.becauseL, 0, 1)]⟩

/-- **The demonstration store is sound** in the history of `Causation.lean`:
"the water is not warm, because the water is frozen", with the link itself
stored on the surface. -/
theorem demoStore_sound : storeSound Causation.demoHist demoStore := by
  constructor
  · intro l hl
    have : l = (.warm .water, false) ∨ l = (.frozen .water, true) := by
      simpa [demoStore] using hl
    rcases this with rfl | rfl <;> native_decide
  · intro t ht _ l m hl hm
    have htt : t = (Link.becauseL, 0, 1) := by simpa [demoStore] using ht
    subst htt
    simp only [demoStore] at hl hm
    have hl' : l = (.warm .water, false) := by simpa using hl.symm
    have hm' : m = (.frozen .water, true) := by simpa using hm.symm
    subst hl'
    subst hm'
    exact Causation.coeval_reason_accepted

/-- Three records: two clauses and one link, 72 cells in all. -/
theorem demoStore_records : (storeRecs demoStore).length = 3 := by decide

end ClauseStore
