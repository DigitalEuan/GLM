import RequestProject.GLM.Rule30.MathieuOrbitsData

/-!
# Round 47: the complete `M₂₄` census of seed patterns (To Do 31)

(Not a `module`: the checks use `native_decide`.)

Round 32 (`MathieuOrbitsData.lean`) certified the orbits of the 24-cell patterns with up to 7
marked cells, and the octads and dodecads.  This file finishes the census: **every** one of the
`2²⁴` patterns is reached from exactly one of 49 representatives (`census_49`), and each orbit
is described by a readable test.

**The tool (FORMAL soundness, then CERT checks).**
* `pmT`, `wt`: byte-table versions of `pmask` and `weight`, proved equal to them
  (`pmT_byteTab`, `wt_eq_weight`).  They only make the checks fast; nothing is assumed.
* `forestOK`: a breadth-first *forest* certificate with several roots; every listed pattern is
  reached from one of the roots (`forestOK_sound`).
* `covers`: every pattern of weight `k` appears in the forest (checked through a position table
  that is computed but never trusted).
* `censusCheck k roots`: both checks for weight `k`; `censusCheck_sound` turns it into
  "every pattern of weight `k` is reached from some root".
* `hasMeet a b y`: some codeword of weight `a` meets `y` in exactly `b` cells.  It is kept by every
  code automorphism (`hasMeet_pmask`), so it separates orbits.
* `orbit_iff_of_census`: a census plus one invariant test that holds at exactly one root gives
  the exact orbit of that root.

**Results (CERT).**
* 8 to 11 marked cells: 3 orbits each; 12 marked cells: 5 orbits (To Do 31), each with its test
  and its size (`orbit8_octad`, …, `orbit12_dodecad`; sizes `orbitSize8`, …).
* Complements: `pmask` commutes with complementing, so the orbits with `k` and `24 − k` cells
  correspond (`reach_compl`).
* `census_49`: the 49 representatives `reps49` reach every pattern, and no pattern is reached from
  two of them — the classical count of 49 orbits, proved here for the GLM code.
-/

namespace GLM.Rule30.Mathieu
namespace Census

/-! ## Byte tables -/

theorem decomp24 (x : ℕ) (hx : x < 2 ^ 24) :
    x = x % 256 ^^^ (x / 256 % 256) <<< 8 ^^^ (x / 65536 % 256) <<< 16 := by
  rw [show (256 : ℕ) = 2 ^ 8 by norm_num, show (65536 : ℕ) = 2 ^ 16 by norm_num]
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [Nat.testBit_xor, Nat.testBit_shiftLeft, Nat.testBit_mod_two_pow,
    Nat.testBit_div_two_pow]
  by_cases h24 : 24 ≤ i
  · have : x.testBit i = false :=
      Nat.testBit_lt_two_pow (lt_of_lt_of_le hx (Nat.pow_le_pow_right (by norm_num) h24))
    rw [this]
    simp [show ¬ i < 8 by omega, show ¬ i - 8 < 8 by omega, show ¬ i - 16 < 8 by omega]
  · push_neg at h24
    interval_cases i <;> simp

theorem getElem!_toArray_map {f : ℕ → ℕ} {N n : ℕ} (hn : n < N) :
    ((List.range N).map f).toArray[n]! = f n := by
  rw [getElem!_pos _ _ (by simpa using hn)]
  simp

/-- The images under `g` of the 256 byte values in each of the three byte positions. -/
def byteTab (g : Equiv.Perm (Fin 24)) : Array ℕ :=
  ((List.range 768).map fun n => pmask g ((n % 256) <<< (8 * (n / 256)))).toArray

/-- `pmask` by three table lookups. -/
def pmT (T : Array ℕ) (x : ℕ) : ℕ :=
  T[x % 256]! ^^^ T[256 + x / 256 % 256]! ^^^ T[512 + x / 65536 % 256]!

theorem pmT_byteTab (g : Equiv.Perm (Fin 24)) {x : ℕ} (hx : x < 2 ^ 24) :
    pmT (byteTab g) x = pmask g x := by
  have h1 : x % 256 < 256 := Nat.mod_lt _ (by norm_num)
  have h2 : x / 256 % 256 < 256 := Nat.mod_lt _ (by norm_num)
  have h3 : x / 65536 % 256 < 256 := Nat.mod_lt _ (by norm_num)
  rw [pmT, byteTab, getElem!_toArray_map (by omega), getElem!_toArray_map (by omega),
    getElem!_toArray_map (by omega)]
  rw [show (256 + x / 256 % 256) % 256 = x / 256 % 256 by omega,
    show (256 + x / 256 % 256) / 256 = 1 by omega,
    show (512 + x / 65536 % 256) % 256 = x / 65536 % 256 by omega,
    show (512 + x / 65536 % 256) / 256 = 2 by omega, Nat.mod_eq_of_lt h1, Nat.div_eq_of_lt h1]
  conv_rhs => rw [decomp24 x hx]
  rw [pmask_xor, pmask_xor]
  norm_num

/-- Number of marked cells among the 8 low cells. -/
def cnt8 (v : ℕ) : ℕ := ∑ j ∈ Finset.range 8, if v.testBit j then 1 else 0

theorem weight_eq_sum (x : ℕ) :
    weight x = ∑ i ∈ Finset.range 24, if x.testBit i then 1 else 0 := by
  rw [weight_eq_card, Finset.card_filter,
    Fin.sum_univ_eq_sum_range (fun i => if x.testBit i then 1 else 0)]

theorem weight_bytes (x : ℕ) :
    weight x = cnt8 (x % 256) + cnt8 (x / 256 % 256) + cnt8 (x / 65536 % 256) := by
  rw [show (256 : ℕ) = 2 ^ 8 by norm_num, show (65536 : ℕ) = 2 ^ 16 by norm_num, weight_eq_sum]
  simp only [cnt8, Finset.sum_range_succ, Finset.sum_range_zero, Nat.testBit_mod_two_pow,
    Nat.testBit_div_two_pow]
  norm_num
  ring

/-- Popcounts of the 256 bytes. -/
def popTab : Array ℕ := ((List.range 256).map cnt8).toArray

/-- `weight` by three table lookups. -/
def wt (x : ℕ) : ℕ := popTab[x % 256]! + popTab[x / 256 % 256]! + popTab[x / 65536 % 256]!

theorem wt_eq_weight (x : ℕ) : wt x = weight x := by
  rw [wt, popTab, getElem!_toArray_map (Nat.mod_lt _ (by norm_num)),
    getElem!_toArray_map (Nat.mod_lt _ (by norm_num)),
    getElem!_toArray_map (Nat.mod_lt _ (by norm_num)), weight_bytes]

/-! ## The two generators as tables -/

def T0 : Array ℕ := byteTab gM0
def T1 : Array ℕ := byteTab gM1

/-- Generator number `b` (0 or 1). -/
def gen (b : ℕ) : Equiv.Perm (Fin 24) := if b = 0 then gM0 else gM1

theorem gen_mem (b : ℕ) : gen b ∈ gensM := by
  unfold gen gensM; split_ifs <;> simp

/-- Fast application of generator `b`. -/
def step (b x : ℕ) : ℕ := if b = 0 then pmT T0 x else pmT T1 x

theorem step_eq (b : ℕ) {x : ℕ} (hx : x < 2 ^ 24) : step b x = pmask (gen b) x := by
  unfold step gen T0 T1; split_ifs <;> exact pmT_byteTab _ hx

/-! ## Loops over a range -/

/-- `p m` for every `m < n`. -/
def allBelow (p : ℕ → Bool) : ℕ → Bool
  | 0 => true
  | n + 1 => p n && allBelow p n

theorem allBelow_iff (p : ℕ → Bool) (n : ℕ) : allBelow p n = true ↔ ∀ m < n, p m = true := by
  induction n with
  | zero => simp [allBelow]
  | succ n ih =>
    simp only [allBelow, Bool.and_eq_true, ih]
    constructor
    · rintro ⟨h1, h2⟩ m hm
      rcases Nat.lt_succ_iff_lt_or_eq.1 hm with h | h
      · exact h2 m h
      · rw [h]; exact h1
    · intro h; exact ⟨h n (Nat.lt_succ_self n), fun m hm => h m (Nat.lt_succ_of_lt hm)⟩

/-- Number of `m < n` with `p m` (plus `acc`). -/
def countBelow (p : ℕ → Bool) : ℕ → ℕ → ℕ
  | 0, acc => acc
  | n + 1, acc => countBelow p n (if p n then acc + 1 else acc)

theorem countBelow_eq (p : ℕ → Bool) (n acc : ℕ) :
    countBelow p n acc = acc + ((Finset.range n).filter (fun m => p m = true)).card := by
  induction n generalizing acc with
  | zero => simp [countBelow]
  | succ n ih =>
    rw [countBelow, ih, Finset.range_add_one, Finset.filter_insert]
    split_ifs with h
    · simp [h]; omega
    · simp

/-! ## Forest certificates -/

/-- A forest certificate: entry `(v, j, 2)` is the root `roots[j]`; entry `(v, i', b)` with
`b < 2` says `v` is generator `b` applied to the value of the earlier entry `i'`.  `R[i]` is the
root index of entry `i`. -/
def forestOK (roots : List ℕ) (C : Array (ℕ × ℕ × ℕ)) (R : Array ℕ) : Bool :=
  allBelow (fun i =>
    let e := C[i]!
    if e.2.2 = 2 then decide (e.2.1 < roots.length) && e.1 == roots.getD e.2.1 0 &&
      R[i]! == e.2.1
    else decide (e.2.1 < i) && decide (e.2.2 < 2) && e.1 == step e.2.2 C[e.2.1]!.1 &&
      R[i]! == R[e.2.1]!) C.size

/-- **Soundness of forest certificates**: entry `i` is reached from the root `R[i]`. -/
theorem forestOK_sound {roots : List ℕ} {C : Array (ℕ × ℕ × ℕ)} {R : Array ℕ}
    (h : forestOK roots C R = true) (hr : ∀ r ∈ roots, r < 2 ^ 24) :
    ∀ i < C.size, C[i]!.1 < 2 ^ 24 ∧ R[i]! < roots.length ∧
      Reach gensM (roots.getD R[i]! 0) C[i]!.1 := by
  rw [forestOK, allBelow_iff] at h
  intro i
  induction i using Nat.strong_induction_on with
  | _ i ih =>
    intro hi
    have hi' := h i hi
    simp only at hi'
    split_ifs at hi' with h2
    · simp only [Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq] at hi'
      obtain ⟨⟨hj, hv⟩, hR⟩ := hi'
      rw [hv, hR]
      refine ⟨hr _ ?_, hj, Reach.refl⟩
      rw [List.getD_eq_getElem _ _ hj]; exact List.getElem_mem hj
    · simp only [Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq] at hi'
      obtain ⟨⟨⟨hp, _⟩, hv⟩, hR⟩ := hi'
      obtain ⟨hlt, hj, hreach⟩ := ih _ hp (by omega)
      rw [hv, step_eq _ hlt, hR]
      exact ⟨pmask_lt _ _, hj, Reach.step _ (gen_mem _) hreach⟩

/-- Breadth-first construction of a forest certificate (untrusted; checked by `forestOK`). -/
def forestAux : ℕ → ℕ → Array (ℕ × ℕ × ℕ) → ByteArray → Array (ℕ × ℕ × ℕ)
  | 0, _, arr, _ => arr
  | fuel + 1, i, arr, vis =>
    if h : i < arr.size then
      let v := arr[i].1
      let z0 := step 0 v
      let r : Array (ℕ × ℕ × ℕ) × ByteArray :=
        if vis.get! z0 == 0 then (arr.push (z0, i, 0), vis.set! z0 1) else (arr, vis)
      let z1 := step 1 v
      let r := if r.2.get! z1 == 0 then (r.1.push (z1, i, 1), r.2.set! z1 1) else r
      forestAux fuel (i + 1) r.1 r.2
    else arr

/-- The forest for a list of roots (untrusted). -/
def forestBFS (roots : List ℕ) : Array (ℕ × ℕ × ℕ) :=
  let init := (roots.zipIdx.map fun p => (p.1, p.2, 2)).toArray
  let vis := roots.foldl (fun (v : ByteArray) r => v.set! r 1)
    (ByteArray.mk (Array.replicate (2 ^ 24) 0))
  forestAux (2 ^ 24 + 1) 0 init vis

/-- Root indices of the entries (untrusted; checked by `forestOK`). -/
def mkRoots (C : Array (ℕ × ℕ × ℕ)) : Array ℕ :=
  C.foldl (fun (R : Array ℕ) e => R.push (if e.2.2 = 2 then e.2.1 else R[e.2.1]!)) #[]

/-- Position table (untrusted): `pos[v]` is the index of an entry with value `v`. -/
def mkPos (C : Array (ℕ × ℕ × ℕ)) : Array ℕ :=
  (C.foldl (fun (acc : Array ℕ × ℕ) e => (acc.1.set! e.1 acc.2, acc.2 + 1))
    (Array.replicate (2 ^ 24) 0, 0)).1

/-- Every pattern of weight `k` appears in `C` (found through the table `pos`). -/
def covers (k : ℕ) (C : Array (ℕ × ℕ × ℕ)) (pos : Array ℕ) : Bool :=
  allBelow (fun y => wt y != k || (decide (pos[y]! < C.size) && C[pos[y]!]!.1 == y)) (2 ^ 24)

theorem covers_sound {k : ℕ} {C : Array (ℕ × ℕ × ℕ)} {pos : Array ℕ} (h : covers k C pos = true)
    {y : ℕ} (hy : y < 2 ^ 24) (hw : weight y = k) : ∃ i < C.size, C[i]!.1 = y := by
  rw [covers, allBelow_iff] at h
  have := h y hy
  simp only [Bool.or_eq_true, bne_iff_ne, ne_eq, wt_eq_weight, hw, not_true_eq_false,
    false_or, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq] at this
  exact ⟨_, this.1, this.2⟩

/-- The values of `C` are pairwise distinct (each one's position is its own index). -/
def distinct (C : Array (ℕ × ℕ × ℕ)) (pos : Array ℕ) : Bool :=
  allBelow (fun i => pos[C[i]!.1]! == i) C.size

theorem distinct_sound {C : Array (ℕ × ℕ × ℕ)} {pos : Array ℕ} (h : distinct C pos = true)
    {i i' : ℕ} (hi : i < C.size) (hi' : i' < C.size) (he : C[i]!.1 = C[i']!.1) : i = i' := by
  rw [distinct, allBelow_iff] at h
  have h1 := h i hi
  have h2 := h i' hi'
  simp only [beq_iff_eq] at h1 h2
  rw [← h1, ← h2, he]

/-- Entries with root `j`. -/
def rootCount (R : Array ℕ) (n j : ℕ) : ℕ := countBelow (fun i => R[i]! == j) n 0

/-- The census check for weight `k`: forest, coverage, distinctness, and the orbit sizes. -/
def censusCheck (k : ℕ) (roots sizes : List ℕ) : Bool :=
  let C := forestBFS roots
  let R := mkRoots C
  let pos := mkPos C
  roots.all (fun r => decide (r < 2 ^ 24)) && forestOK roots C R && covers k C pos &&
    distinct C pos && sizes == (List.range roots.length).map (rootCount R C.size)

/-- What a passed census check provides. -/
structure CensusFacts (k : ℕ) (roots sizes : List ℕ) (C : Array (ℕ × ℕ × ℕ)) (R : Array ℕ) :
    Prop where
  roots_lt : ∀ r ∈ roots, r < 2 ^ 24
  sound : ∀ i < C.size, C[i]!.1 < 2 ^ 24 ∧ R[i]! < roots.length ∧
      Reach gensM (roots.getD R[i]! 0) C[i]!.1
  cover : ∀ y < 2 ^ 24, weight y = k → ∃ i < C.size, C[i]!.1 = y
  inj : ∀ i < C.size, ∀ i' < C.size, C[i]!.1 = C[i']!.1 → i = i'
  sizes : ∀ j < roots.length, sizes.getD j 0 = rootCount R C.size j

theorem censusCheck_facts {k : ℕ} {roots sizes : List ℕ} (h : censusCheck k roots sizes = true) :
    ∃ C R, CensusFacts k roots sizes C R := by
  simp only [censusCheck, Bool.and_eq_true, List.all_eq_true, decide_eq_true_eq,
    beq_iff_eq] at h
  obtain ⟨⟨⟨⟨hr, hf⟩, hc⟩, hd⟩, hs⟩ := h
  refine ⟨_, _, hr, forestOK_sound hf hr, fun y hy hw => covers_sound hc hy hw,
    fun i hi i' hi' he => distinct_sound hd hi hi' he, fun j hj => ?_⟩
  rw [hs, List.getD_eq_getElem _ _ (by simpa using hj)]
  simp

/-- **Census soundness**: every pattern of weight `k` is reached from one of the roots. -/
theorem censusCheck_sound {k : ℕ} {roots sizes : List ℕ} (h : censusCheck k roots sizes = true)
    {y : ℕ} (hy : y < 2 ^ 24) (hw : weight y = k) :
    ∃ j < roots.length, Reach gensM (roots.getD j 0) y := by
  obtain ⟨C, R, hF⟩ := censusCheck_facts h
  obtain ⟨i, hi, rfl⟩ := hF.cover y hy hw
  exact ⟨_, (hF.sound i hi).2.1, (hF.sound i hi).2.2⟩

theorem censusCheck_roots_lt {k : ℕ} {roots sizes : List ℕ}
    (h : censusCheck k roots sizes = true) : ∀ r ∈ roots, r < 2 ^ 24 := by
  obtain ⟨C, R, hF⟩ := censusCheck_facts h
  exact hF.roots_lt

/-! ## Invariant tests -/

/-- The 4096 codewords. -/
def codeList : List ℕ := (List.range 4096).map golayWord

theorem mem_codeList {c : ℕ} : c ∈ codeList ↔ c ∈ code := by
  simp [codeList, code]

/-- Some codeword of weight `a` meets `y` in exactly `b` cells. -/
def hasMeet (a b y : ℕ) : Bool := codeList.any (fun c => weight c == a && weight (c &&& y) == b)

theorem hasMeet_iff (a b y : ℕ) :
    hasMeet a b y = true ↔ ∃ c ∈ code, weight c = a ∧ weight (c &&& y) = b := by
  simp [hasMeet, List.any_eq_true, mem_codeList]

theorem hasMeet_pmask_of {g : Equiv.Perm (Fin 24)} (hg : PreservesCode g) {a b y : ℕ}
    (h : hasMeet a b y = true) : hasMeet a b (pmask g y) = true := by
  rw [hasMeet_iff] at h ⊢
  obtain ⟨c, hc, hw, hm⟩ := h
  exact ⟨pmask g c, hg c hc, by rw [weight_pmask, hw], by rw [← pmask_and, weight_pmask, hm]⟩

/-- `hasMeet` is kept by every code automorphism. -/
theorem hasMeet_pmask {g : Equiv.Perm (Fin 24)} (hg : PreservesCode g) (a b : ℕ) {y : ℕ}
    (hy : y < 2 ^ 24) : hasMeet a b (pmask g y) = hasMeet a b y := by
  apply Bool.eq_iff_iff.2
  refine ⟨fun h => ?_, hasMeet_pmask_of hg⟩
  have := hasMeet_pmask_of hg.symm h
  rwa [pmask_symm_pmask g hy] at this

/-- A test on patterns kept by the generators. -/
def Invariant (Q : ℕ → Bool) : Prop := ∀ g ∈ gensM, ∀ y < 2 ^ 24, Q (pmask g y) = Q y

theorem invariant_hasMeet (a b : ℕ) : Invariant (hasMeet a b) :=
  fun g hg _ hy => hasMeet_pmask (gens_preserve g hg) a b hy

theorem invariant_const (c : Bool) : Invariant (fun _ => c) := fun _ _ _ _ => rfl

theorem Invariant.and {Q Q' : ℕ → Bool} (h : Invariant Q) (h' : Invariant Q') :
    Invariant (fun y => Q y && Q' y) := fun g hg y hy => by
  simp only [h g hg y hy, h' g hg y hy]

theorem Invariant.not {Q : ℕ → Bool} (h : Invariant Q) : Invariant (fun y => !Q y) :=
  fun g hg y hy => by simp only [h g hg y hy]

theorem reach_lt {x y : ℕ} (hx : x < 2 ^ 24) (h : Reach gensM x y) : y < 2 ^ 24 := by
  induction h with
  | refl => exact hx
  | step g _ _ _ => exact pmask_lt _ _

theorem reach_eq_of_invariant {Q : ℕ → Bool} (hQ : Invariant Q) {x y : ℕ} (hx : x < 2 ^ 24)
    (h : Reach gensM x y) : Q y = Q x := by
  induction h with
  | refl => rfl
  | step g hg hr ih => rw [hQ g hg _ (reach_lt hx hr), ih]

theorem reach_weight' {x y : ℕ} (h : Reach gensM x y) : weight y = weight x := by
  induction h with
  | refl => rfl
  | step g _ _ ih => rw [weight_pmask, ih]

/-- **Exact orbit from a census.**  If the census for weight `k` passes and the invariant test
`Q` holds at root `i` and at no other root, then the orbit of root `i` is exactly the set of
patterns of weight `k` passing `Q`. -/
theorem orbit_iff_of_census {k : ℕ} {roots sizes : List ℕ}
    (hc : censusCheck k roots sizes = true)
    {Q : ℕ → Bool} (hQ : Invariant Q) {i : ℕ} (hi : i < roots.length)
    (hwi : weight (roots.getD i 0) = k)
    (hsep : ∀ j < roots.length, Q (roots.getD j 0) = true ↔ j = i) (y : ℕ) :
    Reach gensM (roots.getD i 0) y ↔ y < 2 ^ 24 ∧ weight y = k ∧ Q y = true := by
  have hr := censusCheck_roots_lt hc
  have hlt : ∀ j < roots.length, roots.getD j 0 < 2 ^ 24 := fun j hj => by
    rw [List.getD_eq_getElem _ _ hj]; exact hr _ (List.getElem_mem hj)
  constructor
  · intro h
    refine ⟨reach_lt (hlt i hi) h, by rw [reach_weight' h, hwi], ?_⟩
    rw [reach_eq_of_invariant hQ (hlt i hi) h]
    exact (hsep i hi).2 rfl
  · rintro ⟨hy, hw, hq⟩
    obtain ⟨j, hj, hreach⟩ := censusCheck_sound hc hy hw
    rw [reach_eq_of_invariant hQ (hlt j hj) hreach] at hq
    rw [← (hsep j hj).1 hq]
    exact hreach

/-- **Orbit size from a census**, under the same separation hypothesis. -/
theorem orbit_ncard_of_census {k : ℕ} {roots sizes : List ℕ}
    (hc : censusCheck k roots sizes = true)
    {Q : ℕ → Bool} (hQ : Invariant Q) {i : ℕ} (hi : i < roots.length)
    (hwi : weight (roots.getD i 0) = k)
    (hsep : ∀ j < roots.length, Q (roots.getD j 0) = true ↔ j = i) :
    {y | Reach gensM (roots.getD i 0) y}.ncard = sizes.getD i 0 := by
  obtain ⟨C, R, hF⟩ := censusCheck_facts hc
  have hr := hF.roots_lt
  have hlt : ∀ j < roots.length, roots.getD j 0 < 2 ^ 24 := fun j hj => by
    rw [List.getD_eq_getElem _ _ hj]; exact hr _ (List.getElem_mem hj)
  set F := (Finset.range C.size).filter (fun t => (R[t]! == i) = true) with hFdef
  have hset : {y | Reach gensM (roots.getD i 0) y} = ↑(F.image (fun t => C[t]!.1)) := by
    ext y
    simp only [Set.mem_setOf_eq, Finset.coe_image, Set.mem_image, Finset.mem_coe, hFdef,
      Finset.mem_filter, Finset.mem_range, beq_iff_eq]
    constructor
    · intro h
      have hy := reach_lt (hlt i hi) h
      obtain ⟨t, ht, rfl⟩ := hF.cover y hy (by rw [reach_weight' h, hwi])
      obtain ⟨_, hRt, hreach⟩ := hF.sound t ht
      refine ⟨t, ⟨ht, ?_⟩, rfl⟩
      have h1 := reach_eq_of_invariant hQ (hlt i hi) h
      have h2 := reach_eq_of_invariant hQ (hlt _ hRt) hreach
      exact (hsep _ hRt).1 (by rw [← h2, h1]; exact (hsep i hi).2 rfl)
    · rintro ⟨t, ⟨ht, hRt⟩, rfl⟩
      have := (hF.sound t ht).2.2
      rwa [hRt] at this
  rw [hset, Set.ncard_coe_finset, Finset.card_image_of_injOn, hF.sizes i hi, rootCount,
    countBelow_eq, zero_add]
  intro t ht t' ht' he
  simp only [hFdef, Finset.coe_filter, Finset.mem_range, Set.mem_setOf_eq] at ht ht'
  exact hF.inj t ht.1 t' ht'.1 he

/-! ## The census, weight by weight -/

/-- Representatives: `roots k` lists one pattern per orbit of `k`-cell patterns, `k ≤ 12`. -/
def censusRoots : ℕ → List ℕ
  | 6 => [119, 63]
  | 7 => [475, 127]
  | 8 => [10616863, 1151, 255]
  | 9 => [9343, 511, 767]
  | 10 => [4194815, 1023, 131839]
  | 11 => [2098175, 2047, 656127]
  | 12 => [1704703, 4095, 18431, 10239, 6292479]
  | k => [2 ^ k - 1]

/-- The orbit sizes, in the same order. -/
def censusSizes : ℕ → List ℕ
  | 0 => [1]
  | 1 => [24]
  | 2 => [276]
  | 3 => [2024]
  | 4 => [10626]
  | 5 => [42504]
  | 6 => [21252, 113344]
  | 7 => [6072, 340032]
  | 8 => [759, 97152, 637560]
  | 9 => [12144, 728640, 566720]
  | 10 => [91080, 1700160, 170016]
  | 11 => [425040, 2040192, 30912]
  | 12 => [2576, 370944, 1020096, 1275120, 35420]
  | _ => []

theorem census0 : censusCheck 0 (censusRoots 0) (censusSizes 0) = true := by native_decide
theorem census1 : censusCheck 1 (censusRoots 1) (censusSizes 1) = true := by native_decide
theorem census2 : censusCheck 2 (censusRoots 2) (censusSizes 2) = true := by native_decide
theorem census3 : censusCheck 3 (censusRoots 3) (censusSizes 3) = true := by native_decide
theorem census4 : censusCheck 4 (censusRoots 4) (censusSizes 4) = true := by native_decide
theorem census5 : censusCheck 5 (censusRoots 5) (censusSizes 5) = true := by native_decide
theorem census6 : censusCheck 6 (censusRoots 6) (censusSizes 6) = true := by native_decide
theorem census7 : censusCheck 7 (censusRoots 7) (censusSizes 7) = true := by native_decide
theorem census8 : censusCheck 8 (censusRoots 8) (censusSizes 8) = true := by native_decide
theorem census9 : censusCheck 9 (censusRoots 9) (censusSizes 9) = true := by native_decide
theorem census10 : censusCheck 10 (censusRoots 10) (censusSizes 10) = true := by native_decide
theorem census11 : censusCheck 11 (censusRoots 11) (censusSizes 11) = true := by native_decide
theorem census12 : censusCheck 12 (censusRoots 12) (censusSizes 12) = true := by native_decide

end Census
end GLM.Rule30.Mathieu
