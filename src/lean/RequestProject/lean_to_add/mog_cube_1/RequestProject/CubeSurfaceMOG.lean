import Mathlib
import RequestProject.GolayHexTiles

/-!
# The cube's surface *is* the MOG grid

`GolayHexTiles.lean` treats a whole cube as a single MOG *column* (one GF(4)
digit per face).  This file takes the tighter identification:

> 6 faces × 4 cells per face = 24 cells = the 6 columns × 4 rows of the MOG.

A `Grid` is a function `Fin 6 → Fin 4 → Bool`: six faces, four cells on each.
The Golay code is built on it exactly as Curtis's MOG builds it, and exactly as
`glm_clean/glm_clean/hexacode.py` builds it:

* each face gets a **symbol** in GF(4), the sum of the row labels `0, 1, ω, ω̄`
  of its set cells;
* a grid is a codeword iff the six face symbols form a **hexacode** word and
  every face has the same parity as the top row.

What is proved here, all of it exact and finite:

* `colOf_roundtrip`, `mem_mogCode` — the code is parametrised bijectively by a
  hexacode word (`4³` choices) and a free top row (`2⁶` choices): `4³·2⁶ = 2¹²`.
* `mog_card` — 4096 codewords; `mog_weight_enumerator` — `1, 759, 2576, 759, 1`;
  `mog_min_weight` — minimum weight 8.
* **The three-layer factorisation**: `fibre_card` (the 16 cell patterns of a
  face fall onto 4 symbols in fibres of size 4), `hexpass_card` (`2¹⁸` grids
  survive the hexacode layer), `mog_card` (`2¹²` survive the parity layer),
  `parity_layer_factor` (`2¹⁸ = 64·2¹²`).
* **One bad face heals, two do not**: `face_erasure_correctable` — two codewords
  agreeing outside one face are equal; `two_face_ambiguous` — for *every* pair
  of faces the two full faces form an octad, so a two-face erasure is genuinely
  ambiguous.
* The same boundary one layer up: `hexacode_min_dist` (`d = 4`),
  `hexacode_unique_decode` (one symbol error corrects),
  `hexacode_ambiguous_at_two` (two do not).
-/

set_option maxRecDepth 100000
set_option maxHeartbeats 4000000

namespace CubeMOG

open GolayHex

/-! ## 1. Grids -/

/-- The four cells of one face. -/
abbrev Col := Fin 4 → Bool

/-- The 24 cells of the cube's surface: six faces of four cells. -/
abbrev Grid := Fin 6 → Col

instance : Zero Grid := ⟨fun _ _ => false⟩

@[simp] theorem zero_apply (j : Fin 6) (i : Fin 4) : (0 : Grid) j i = false := rfl

/-- Cellwise XOR of two grids. -/
def gxor (g h : Grid) : Grid := fun j i => xor (g j i) (h j i)

/-- Hamming weight: the number of set cells. -/
def wtG (g : Grid) : Nat := ∑ j : Fin 6, ∑ i : Fin 4, if g j i then 1 else 0

/-- The GF(4) labels of the four rows: `0, 1, ω, ω̄`. -/
def rowLabel : Fin 4 → F4 := ![0, 1, 2, 3]

/-- The **symbol of a face**: the GF(4) sum of the labels of its set cells. -/
def symb (b : Col) : F4 :=
  (if b 0 then rowLabel 0 else 0) +₄ ((if b 1 then rowLabel 1 else 0) +₄
    ((if b 2 then rowLabel 2 else 0) +₄ (if b 3 then rowLabel 3 else 0)))

/-- The parity of a face. -/
def par (b : Col) : Bool := xor (b 0) (xor (b 1) (xor (b 2) (b 3)))

/-- The parity of the top row of the grid. -/
def topPar (g : Grid) : Bool :=
  xor (g 0 0) (xor (g 1 0) (xor (g 2 0) (xor (g 3 0) (xor (g 4 0) (g 5 0)))))

/-- The six face symbols. -/
def symbols (g : Grid) : Fin 6 → F4 := fun j => symb (g j)

/-- **The MOG law.**  A grid is a codeword when its six face symbols form a
hexacode word and every face has the parity of the top row. -/
def IsMog (g : Grid) : Prop := IsHex (symbols g) ∧ ∀ j, par (g j) = topPar g

instance : DecidablePred IsMog := fun _ => inferInstanceAs (Decidable (_ ∧ _))

/-! ## 2. A face is reconstructed from (symbol, top cell, parity) -/

/-- The low bit of a GF(4) digit (its `1`-component). -/
def bit0 (s : F4) : Bool := s = 1 || s = 3
/-- The high bit of a GF(4) digit (its `ω`-component). -/
def bit1 (s : F4) : Bool := s = 2 || s = 3

/-- The unique face pattern with symbol `s`, top cell `t` and parity `q`. -/
def colOf (s : F4) (t q : Bool) : Col :=
  let u := xor q t
  ![t, xor u (bit1 s), xor u (bit0 s), xor u (xor (bit0 s) (bit1 s))]

theorem colOf_symb : ∀ (s : F4) (t q : Bool), symb (colOf s t q) = s := by decide
theorem colOf_par : ∀ (s : F4) (t q : Bool), par (colOf s t q) = q := by decide
theorem colOf_top : ∀ (s : F4) (t q : Bool), colOf s t q 0 = t := by decide

/-- Every face pattern is recovered from its symbol, top cell and parity: the
16 patterns of a face are exactly `4 × 2 × 2`. -/
theorem colOf_roundtrip : ∀ b : Col, colOf (symb b) (b 0) (par b) = b := by decide

/-! ## 3. The code, parametrised -/

/-- The XOR of the six chosen top cells. -/
def xor6 (t : Fin 6 → Bool) : Bool :=
  xor (t 0) (xor (t 1) (xor (t 2) (xor (t 3) (xor (t 4) (t 5)))))

/-- **The parametrisation of the code**: a hexacode word `combo a b c` for the
face symbols and a free top row `t`; the common face parity is then forced to
be the parity of the top row. -/
def build (a b c : F4) (t : Fin 6 → Bool) : Grid :=
  fun j => colOf (combo a b c j) (t j) (xor6 t)

/-- The parameter space: `4³ · 2⁶ = 4096`. -/
abbrev Params := (F4 × F4 × F4) × (Fin 6 → Bool)

/-- `build` on a packed parameter. -/
def buildP (p : Params) : Grid := build p.1.1 p.1.2.1 p.1.2.2 p.2

theorem build_symbols (a b c : F4) (t : Fin 6 → Bool) :
    symbols (build a b c t) = combo a b c := by
  funext j; simpa [symbols, build] using colOf_symb (combo a b c j) (t j) (xor6 t)

theorem build_top (a b c : F4) (t : Fin 6 → Bool) (j : Fin 6) :
    build a b c t j 0 = t j := colOf_top _ _ _

theorem build_topPar (a b c : F4) (t : Fin 6 → Bool) :
    topPar (build a b c t) = xor6 t := by
  simp [topPar, xor6, build_top]

/-- Everything `build` produces is a codeword. -/
theorem build_isMog (a b c : F4) (t : Fin 6 → Bool) : IsMog (build a b c t) := by
  refine ⟨?_, ?_⟩
  · rw [build_symbols]; exact ⟨a, b, c, rfl⟩
  · intro j
    rw [build_topPar]
    exact colOf_par _ _ _

/-- Every codeword is produced by `build`. -/
theorem isMog_build {g : Grid} (h : IsMog g) : ∃ a b c t, build a b c t = g := by
  obtain ⟨⟨a, b, c, hab⟩, hpar⟩ := h
  refine ⟨a, b, c, fun j => g j 0, ?_⟩
  funext j
  have hsym : combo a b c j = symb (g j) := by rw [hab]; rfl
  have hxor : xor6 (fun j => g j 0) = topPar g := by simp [xor6, topPar]
  rw [build, hsym, hxor, ← hpar j]
  exact colOf_roundtrip (g j)

/-- The code, as a `Finset` of grids. -/
def mogCode : Finset Grid := Finset.univ.image buildP

theorem mem_mogCode {g : Grid} : g ∈ mogCode ↔ IsMog g := by
  constructor
  · rintro hg
    obtain ⟨p, -, rfl⟩ := Finset.mem_image.mp hg
    exact build_isMog _ _ _ _
  · intro hg
    obtain ⟨a, b, c, t, ht⟩ := isMog_build hg
    exact Finset.mem_image.mpr ⟨((a, b, c), t), Finset.mem_univ _, ht⟩

theorem mogCode_eq_filter : mogCode = Finset.univ.filter IsMog := by
  ext g; simp [mem_mogCode]

/-! ## 3b. A fast membership test

Coordinates `0, 1, 2` are an information set of the hexacode: the generator is
systematic there.  So `IsHex h` can be tested by re-encoding, without searching
the 64 words, and `IsMog` becomes a constant-cost check. -/

theorem isHex_iff_info : ∀ h : Fin 6 → F4, IsHex h ↔ combo (h 0) (h 1) (h 2) = h := by
  native_decide

/-- The decidable membership test for the code. -/
def IsMogB (g : Grid) : Bool :=
  (combo (symbols g 0) (symbols g 1) (symbols g 2) == symbols g) &&
    ((par (g 0) == topPar g) && ((par (g 1) == topPar g) && ((par (g 2) == topPar g) &&
      ((par (g 3) == topPar g) && ((par (g 4) == topPar g) && (par (g 5) == topPar g))))))

theorem isMogB_iff (g : Grid) : IsMogB g = true ↔ IsMog g := by
  simp only [IsMogB, Bool.and_eq_true, beq_iff_eq, IsMog, isHex_iff_info]
  constructor
  · rintro ⟨h1, h2, h3, h4, h5, h6, h7⟩
    refine ⟨h1, ?_⟩
    intro j
    fin_cases j <;> assumption
  · rintro ⟨h1, h2⟩
    exact ⟨h1, h2 0, h2 1, h2 2, h2 3, h2 4, h2 5⟩

/-! ## 4. Counting: the three layers -/

/-- Layer 1: the 16 cell patterns of one face map onto the 4 GF(4) symbols with
fibres of size 4. -/
theorem fibre_card : ∀ s : F4, (Finset.univ.filter fun b : Col => symb b = s).card = 4 := by
  decide

theorem symbols_fibre_card (h : Fin 6 → F4) :
    (Finset.univ.filter fun g : Grid => symbols g = h).card = 4096 := by
  have hset : (Finset.univ.filter fun g : Grid => symbols g = h)
      = Fintype.piFinset (fun j => Finset.univ.filter fun b : Col => symb b = h j) := by
    ext g
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Fintype.mem_piFinset]
    constructor
    · intro hg j; exact congrFun hg j
    · intro hg; funext j; exact hg j
  rw [hset, Fintype.card_piFinset]
  simp [fibre_card]

/-- Layer 2: exactly `2¹⁸` of the `2²⁴` grids have face symbols forming a
hexacode word. -/
theorem hexpass_card :
    (Finset.univ.filter fun g : Grid => IsHex (symbols g)).card = 2 ^ 18 := by
  classical
  have hmap : ((Finset.univ.filter fun g : Grid => IsHex (symbols g) : Finset Grid) : Set Grid).MapsTo
      symbols (Finset.univ.filter fun h : Fin 6 → F4 => IsHex h) := by
    intro g hg
    simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_univ, true_and] at hg
    simpa using hg
  rw [Finset.card_eq_sum_card_fiberwise hmap]
  have hfib : ∀ h ∈ Finset.univ.filter fun h : Fin 6 → F4 => IsHex h,
      ((Finset.univ.filter fun g : Grid => IsHex (symbols g)).filter
        fun g => symbols g = h).card = 4096 := by
    intro h hh
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hh
    have heq : ((Finset.univ.filter fun g : Grid => IsHex (symbols g)).filter
        fun g => symbols g = h) = Finset.univ.filter fun g : Grid => symbols g = h := by
      ext g
      simp only [Finset.mem_filter, Finset.mem_univ, true_and]
      constructor
      · rintro ⟨-, h2⟩; exact h2
      · intro h2; exact ⟨h2 ▸ hh, h2⟩
    rw [heq, symbols_fibre_card]
  rw [Finset.sum_congr rfl hfib, Finset.sum_const, hexacode_card]
  norm_num

theorem combo_injective : ∀ a b c a' b' c' : F4,
    combo a b c = combo a' b' c' → a = a' ∧ b = b' ∧ c = c' := by decide

/-- `build` is injective, so the code has exactly `4³ · 2⁶` words. -/
theorem buildP_injective : Function.Injective buildP := by
  rintro ⟨⟨a, b, c⟩, t⟩ ⟨⟨a', b', c'⟩, t'⟩ h
  have ht : t = t' := by
    funext j
    have := congrFun (congrFun h j) 0
    simpa [buildP, build, colOf_top] using this
  have hs : combo a b c = combo a' b' c' := by
    have := congrArg symbols h
    simpa [buildP, build_symbols] using this
  obtain ⟨rfl, rfl, rfl⟩ := combo_injective a b c a' b' c' hs
  simp [ht]

/-- Layer 3: the parity rules cut `2¹⁸` down to `2¹² = 4096`. -/
theorem mog_card : (Finset.univ.filter IsMog).card = 2 ^ 12 := by
  rw [← mogCode_eq_filter, mogCode, Finset.card_image_of_injective _ buildP_injective,
    Finset.card_univ]
  simp [Params]

/-- The parity layer costs exactly a factor of 64. -/
theorem parity_layer_factor :
    (Finset.univ.filter fun g : Grid => IsHex (symbols g)).card
      = 64 * (Finset.univ.filter IsMog).card := by
  rw [hexpass_card, mog_card]
  norm_num

/-- Every codeword passes the hexacode layer. -/
theorem mog_subset_hexpass :
    (Finset.univ.filter IsMog) ⊆ Finset.univ.filter fun g : Grid => IsHex (symbols g) := by
  intro g hg
  simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hg ⊢
  exact hg.1

/-! ## 5. Weights -/

/-- The Golay weight enumerator, read on the cube's surface. -/
theorem mog_weight_enumerator :
    (Finset.univ.filter fun p : Params => wtG (buildP p) = 0).card = 1 ∧
    (Finset.univ.filter fun p : Params => wtG (buildP p) = 8).card = 759 ∧
    (Finset.univ.filter fun p : Params => wtG (buildP p) = 12).card = 2576 ∧
    (Finset.univ.filter fun p : Params => wtG (buildP p) = 16).card = 759 ∧
    (Finset.univ.filter fun p : Params => wtG (buildP p) = 24).card = 1 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

private theorem min_weight_params : ∀ p : Params, buildP p ≠ 0 → 8 ≤ wtG (buildP p) := by
  native_decide

theorem wtG_eq_zero_iff (g : Grid) : wtG g = 0 ↔ g = 0 := by
  constructor
  · intro h
    funext j i
    by_contra hji
    have hg : g j i = true := by
      cases hgv : g j i with
      | false => exact absurd hgv hji
      | true => rfl
    have hpos : 0 < ∑ i : Fin 4, (if g j i then 1 else 0) := by
      refine Finset.sum_pos' (fun k _ => by positivity) ⟨i, Finset.mem_univ i, ?_⟩
      simp [hg]
    have hlt : 0 < wtG g := lt_of_lt_of_le hpos (Finset.single_le_sum
      (f := fun j : Fin 6 => ∑ i : Fin 4, if g j i then 1 else 0)
      (fun k _ => by positivity) (Finset.mem_univ j))
    omega
  · intro h; subst h; decide

/-- **Minimum weight 8** on the cube's surface. -/
theorem mog_min_weight (g : Grid) (hg : IsMog g) (h0 : g ≠ 0) : 8 ≤ wtG g := by
  obtain ⟨a, b, c, t, ht⟩ := isMog_build hg
  have hb : buildP ((a, b, c), t) = g := ht
  rw [← hb] at h0 ⊢
  exact min_weight_params _ h0

/-! ## 6. The code is linear -/

theorem symb_xor : ∀ b b' : Col, symb (fun i => xor (b i) (b' i)) = symb b +₄ symb b' := by
  decide

theorem combo_add : ∀ a b c a' b' c' : F4,
    (fun j => combo a b c j +₄ combo a' b' c' j) = combo (a +₄ a') (b +₄ b') (c +₄ c') := by
  decide

theorem par_xor : ∀ b b' : Col, par (fun i => xor (b i) (b' i)) = xor (par b) (par b') := by
  decide

theorem topPar_gxor (g h : Grid) : topPar (gxor g h) = xor (topPar g) (topPar h) := by
  simp only [topPar, gxor]
  cases g 0 0 <;> cases g 1 0 <;> cases g 2 0 <;> cases g 3 0 <;> cases g 4 0 <;> cases g 5 0 <;>
    cases h 0 0 <;> cases h 1 0 <;> cases h 2 0 <;> cases h 3 0 <;> cases h 4 0 <;> cases h 5 0 <;>
    rfl

theorem IsMog_gxor {g h : Grid} (hg : IsMog g) (hh : IsMog h) : IsMog (gxor g h) := by
  obtain ⟨⟨a, b, c, hab⟩, hpg⟩ := hg
  obtain ⟨⟨a', b', c', hab'⟩, hph⟩ := hh
  constructor
  · refine ⟨a +₄ a', b +₄ b', c +₄ c', ?_⟩
    funext j
    have hj : symbols (gxor g h) j = symbols g j +₄ symbols h j := symb_xor (g j) (h j)
    rw [hj, ← hab, ← hab']
    exact (congrFun (combo_add a b c a' b' c') j).symm
  · intro j
    have hp : par (gxor g h j) = xor (par (g j)) (par (h j)) := par_xor (g j) (h j)
    rw [hp, topPar_gxor, hpg j, hph j]


/-! ## 6b. A generating set

The code is `F₂`-linear and 12-dimensional, so it is the span of twelve
generators: six that move the hexacode word (the GF(4) coefficients `a, b, c`,
two bits each) and six that move the top row.  Everything that has to be
checked on the whole code can therefore be checked on these twelve. -/

theorem colOf_xor : ∀ (s s' : F4) (t t' q q' : Bool),
    (fun i => xor (colOf s t q i) (colOf s' t' q' i)) = colOf (s +₄ s') (xor t t') (xor q q') := by
  decide

theorem xor6_xor : ∀ t t' : Fin 6 → Bool,
    xor6 (fun j => xor (t j) (t' j)) = xor (xor6 t) (xor6 t') := by native_decide

theorem build_add (a b c a' b' c' : F4) (t t' : Fin 6 → Bool) :
    gxor (build a b c t) (build a' b' c' t')
      = build (a +₄ a') (b +₄ b') (c +₄ c') (fun j => xor (t j) (t' j)) := by
  funext j i
  have h := congrFun (colOf_xor (combo a b c j) (combo a' b' c' j) (t j) (t' j)
    (xor6 t) (xor6 t')) i
  simp only [gxor, build]
  rw [h, xor6_xor, congrFun (combo_add a b c a' b' c') j]

theorem IsMog_zero : IsMog (0 : Grid) := by
  refine ⟨⟨0, 0, 0, ?_⟩, ?_⟩ <;> decide

/-- The `k`-th generator of a family, switched on by `m k`, XORed together
along a list. -/
def selL (B : Fin 12 → Grid) (m : Fin 12 → Bool) : List (Fin 12) → Grid
  | [] => fun _ _ => false
  | k :: l => fun j i => xor (m k && B k j i) (selL B m l j i)

/-- The span of a twelve-element family. -/
def selG (B : Fin 12 → Grid) (m : Fin 12 → Bool) : Grid := selL B m (List.finRange 12)

/-- Any property that holds of the zero grid and survives XOR holds of every
span of grids that have it. -/
theorem selL_closed {P : Grid → Prop} (hz : P 0) (hx : ∀ A B : Grid, P A → P B → P (gxor A B))
    (B : Fin 12 → Grid) (hB : ∀ k, P (B k)) (m : Fin 12 → Bool) :
    ∀ l : List (Fin 12), P (selL B m l)
  | [] => hz
  | k :: l => by
      have h1 : P (fun j i => m k && B k j i : Grid) := by
        cases hm : m k with
        | false => exact hz
        | true => exact hB k
      exact hx _ _ h1 (selL_closed hz hx B hB m l)

theorem selG_closed {P : Grid → Prop} (hz : P 0) (hx : ∀ A B : Grid, P A → P B → P (gxor A B))
    (B : Fin 12 → Grid) (hB : ∀ k, P (B k)) (m : Fin 12 → Bool) : P (selG B m) :=
  selL_closed hz hx B hB m _

theorem selG_isMog (B : Fin 12 → Grid) (hB : ∀ k, IsMog (B k)) (m : Fin 12 → Bool) :
    IsMog (selG B m) :=
  selG_closed IsMog_zero (fun _ _ h h' => IsMog_gxor h h') B hB m

theorem selL_xor (B : Fin 12 → Grid) (m m' : Fin 12 → Bool) : ∀ l : List (Fin 12),
    gxor (selL B m l) (selL B m' l) = selL B (fun k => xor (m k) (m' k)) l
  | [] => by funext j i; simp [selL, gxor]
  | k :: l => by
      have ih := selL_xor B m m' l
      funext j i
      have hih := congrFun (congrFun ih j) i
      simp only [selL, gxor] at hih ⊢
      cases hm : m k <;> cases hm' : m' k <;> cases hb : B k j i <;>
        simp_all [Bool.xor_comm]

theorem selG_xor (B : Fin 12 → Grid) (m m' : Fin 12 → Bool) :
    gxor (selG B m) (selG B m') = selG B (fun k => xor (m k) (m' k)) :=
  selL_xor B m m' _

/-- Six generators for the hexacode word, six for the top row. -/
def mogBasis : Fin 12 → Grid :=
  ![build 1 0 0 (fun _ => false), build w 0 0 (fun _ => false),
    build 0 1 0 (fun _ => false), build 0 w 0 (fun _ => false),
    build 0 0 1 (fun _ => false), build 0 0 w (fun _ => false),
    build 0 0 0 (fun j => j = 0), build 0 0 0 (fun j => j = 1),
    build 0 0 0 (fun j => j = 2), build 0 0 0 (fun j => j = 3),
    build 0 0 0 (fun j => j = 4), build 0 0 0 (fun j => j = 5)]

theorem mogBasis_isMog (k : Fin 12) : IsMog (mogBasis k) := by
  fin_cases k <;> exact build_isMog _ _ _ _

/-- The coefficients of a parametrised codeword over the twelve generators. -/
def mogCoeff (p : Params) : Fin 12 → Bool :=
  ![bit0 p.1.1, bit1 p.1.1, bit0 p.1.2.1, bit1 p.1.2.1, bit0 p.1.2.2, bit1 p.1.2.2,
    p.2 0, p.2 1, p.2 2, p.2 3, p.2 4, p.2 5]

theorem selG_mogCoeff : ∀ p : Params, selG mogBasis (mogCoeff p) = buildP p := by native_decide

/-- **The twelve generators span the code.** -/
theorem mog_spanned {G : Grid} (h : IsMog G) : ∃ m, selG mogBasis m = G := by
  obtain ⟨a, b, c, t, ht⟩ := isMog_build h
  exact ⟨mogCoeff ((a, b, c), t), by rw [selG_mogCoeff ((a, b, c), t)]; exact ht⟩

/-! ## 7. One bad face heals, two do not -/

theorem wtG_le_four_of_face {g : Grid} {f : Fin 6} (h : ∀ j, j ≠ f → g j = fun _ => false) :
    wtG g ≤ 4 := by
  have hsum : wtG g = ∑ i : Fin 4, if g f i then 1 else 0 := by
    unfold wtG
    rw [Finset.sum_eq_single f]
    · intro j _ hj; rw [h j hj]; simp
    · intro hf; exact absurd (Finset.mem_univ f) hf
  rw [hsum]
  calc ∑ i : Fin 4, (if g f i then 1 else 0) ≤ ∑ _i : Fin 4, 1 := by
        refine Finset.sum_le_sum (fun i _ => ?_); split <;> omega
    _ = 4 := by simp

/-- **One bad face is healable.**  Two codewords that agree outside a single
face are equal: a whole face can be erased and reconstructed. -/
theorem face_erasure_correctable {g h : Grid} (hg : IsMog g) (hh : IsMog h) (f : Fin 6)
    (hagree : ∀ j, j ≠ f → g j = h j) : g = h := by
  have hd : IsMog (gxor g h) := IsMog_gxor hg hh
  have hsupp : ∀ j, j ≠ f → gxor g h j = fun _ => false := by
    intro j hj
    funext i
    simp [gxor, hagree j hj]
  have hle : wtG (gxor g h) ≤ 4 := wtG_le_four_of_face hsupp
  have hzero : gxor g h = 0 := by
    by_contra hne
    have := mog_min_weight _ hd hne
    omega
  funext j i
  have hji := congrFun (congrFun hzero j) i
  simp only [gxor, zero_apply] at hji
  revert hji
  cases g j i <;> cases h j i <;> simp

/-- The grid that fills two whole faces. -/
def twoFaces (f₁ f₂ : Fin 6) : Grid := fun j _ => j = f₁ || j = f₂

theorem twoFaces_isMog : ∀ f₁ f₂ : Fin 6, f₁ ≠ f₂ → IsMog (twoFaces f₁ f₂) := by decide

theorem twoFaces_ne_zero : ∀ f₁ f₂ : Fin 6, twoFaces f₁ f₂ ≠ 0 := by decide

theorem twoFaces_weight : ∀ f₁ f₂ : Fin 6, f₁ ≠ f₂ → wtG (twoFaces f₁ f₂) = 8 := by decide

/-- **Two bad faces are ambiguous.**  For every pair of faces there is a nonzero
codeword living inside those two faces — the octad made of the two full faces —
so two codewords can agree outside two faces without being equal. -/
theorem two_face_ambiguous (f₁ f₂ : Fin 6) (h : f₁ ≠ f₂) :
    ∃ g : Grid, IsMog g ∧ g ≠ 0 ∧ wtG g = 8 ∧ ∀ j, j ≠ f₁ → j ≠ f₂ → g j = fun _ => false := by
  refine ⟨twoFaces f₁ f₂, twoFaces_isMog f₁ f₂ h, twoFaces_ne_zero f₁ f₂,
    twoFaces_weight f₁ f₂ h, ?_⟩
  intro j h1 h2
  funext i
  simp [twoFaces, h1, h2]

/-! ## 8. The same boundary at the hexacode layer -/

/-- Number of faces on which two symbol vectors differ. -/
def hexDist (x y : Fin 6 → F4) : Nat := (Finset.univ.filter fun j => x j ≠ y j).card

theorem hexDist_comm (x y : Fin 6 → F4) : hexDist x y = hexDist y x := by
  unfold hexDist; congr 1; ext j; simp [ne_comm]

theorem hexDist_triangle (x y z : Fin 6 → F4) : hexDist x z ≤ hexDist x y + hexDist y z := by
  classical
  have hsub : (Finset.univ.filter fun j => x j ≠ z j) ⊆
      (Finset.univ.filter fun j => x j ≠ y j) ∪ (Finset.univ.filter fun j => y j ≠ z j) := by
    intro j hj
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hj
    simp only [Finset.mem_union, Finset.mem_filter, Finset.mem_univ, true_and]
    by_contra hc
    push_neg at hc
    exact hj (hc.1.trans hc.2)
  calc hexDist x z ≤ _ := Finset.card_le_card hsub
    _ ≤ _ := Finset.card_union_le _ _

private theorem combo_min_dist : ∀ a b c a' b' c' : F4,
    combo a b c ≠ combo a' b' c' → 4 ≤ hexDist (combo a b c) (combo a' b' c') := by
  native_decide

/-- The hexacode has minimum distance 4. -/
theorem hexacode_min_dist (x y : Fin 6 → F4) (hx : IsHex x) (hy : IsHex y) (hne : x ≠ y) :
    4 ≤ hexDist x y := by
  obtain ⟨a, b, c, rfl⟩ := hx
  obtain ⟨a', b', c', rfl⟩ := hy
  exact combo_min_dist a b c a' b' c' hne

/-- **One corrupted face symbol is correctable**: at most one hexacode word lies
within distance 1 of any symbol vector. -/
theorem hexacode_unique_decode (v x y : Fin 6 → F4) (hx : IsHex x) (hy : IsHex y)
    (h1 : hexDist x v ≤ 1) (h2 : hexDist y v ≤ 1) : x = y := by
  by_contra hne
  have hmin := hexacode_min_dist x y hx hy hne
  have htri : hexDist x y ≤ hexDist x v + hexDist v y := hexDist_triangle x v y
  rw [hexDist_comm v y] at htri
  omega

/-- **Two corrupted face symbols are not correctable**: an explicit symbol vector
sits at distance 2 from two different hexacode words. -/
theorem hexacode_ambiguous_at_two :
    ∃ v x y : Fin 6 → F4, IsHex x ∧ IsHex y ∧ x ≠ y ∧ hexDist x v = 2 ∧ hexDist y v = 2 := by
  refine ⟨![0, 0, 0, 0, 1, 1], ![0, 0, 0, 0, 0, 0], ![0, 0, 1, 1, 1, 1], ⟨0, 0, 0, by decide⟩,
    ⟨0, 0, 1, by decide⟩, by decide, by decide, by decide⟩

end CubeMOG
