import Mathlib

/-! Machine-checked parts of the Gray/Golay/MOG data object's discrete layer. -/

namespace GolayMOG

/-- Atomic numbers admitted by the experiment. -/
def Element := {z : ℕ // 1 ≤ z ∧ z ≤ 118}

/-- Reflected binary Gray encoding on natural numbers. -/
def grayEncodeNat (n : ℕ) : ℕ := n ^^^ (n >>> 1)

/-- Decode the low twelve bits of a reflected Gray word.
The fixed fold is enough for every 12-bit identity admitted by this schema. -/
def grayDecode12 (g : ℕ) : ℕ :=
  (List.range 12).foldl (fun n k => n ^^^ (g >>> k)) 0

/-- The v2 lossless identity address: Gray-coded atomic number in twelve bits. -/
def identityAddress (e : Element) : BitVec 12 :=
  BitVec.ofNat 12 (grayEncodeNat e.1)

/-- Decode a v2 identity address. -/
def decodeIdentity (v : BitVec 12) : ℕ := grayDecode12 v.toNat

/-- Every v2 Gray identity address decodes to its original atomic number. -/
theorem decodeIdentity_identityAddress (e : Element) :
    decodeIdentity (identityAddress e) = e.1 := by
  rcases e with ⟨z, hz, hz'⟩
  interval_cases z <;> native_decide +revert

/-- The 118 Gray-coded element identity addresses are collision-free. -/
theorem identityAddress_injective : Function.Injective identityAddress := by
  intro a b h
  apply Subtype.ext
  have h' := congrArg decodeIdentity h
  simpa [decodeIdentity_identityAddress] using h'

/-- Two 12-bit words differ by a one-hot mask, hence in exactly one coordinate. -/
def OneBitApart (a b : BitVec 12) : Prop :=
  ∃ i : Fin 12, a ^^^ b = BitVec.ofNat 12 (1 <<< i.1)

/-- Consecutive admitted atomic numbers have spatially local Gray messages. -/
theorem consecutive_identity_oneBitApart
    (z : ℕ) (hz : 1 ≤ z) (hz' : z < 118) :
    OneBitApart
      (identityAddress ⟨z, hz, Nat.le_of_lt hz'⟩)
      (identityAddress ⟨z + 1, by omega, hz'⟩) := by
  interval_cases z <;> simp [identityAddress, OneBitApart, grayEncodeNat] <;> decide

/-- Cyclic-coordinate index occupying each row-major cell of the fixed 4×6 MOG. -/
def mogCoordinate : Fin 24 → Fin 24 :=
  ![0, 4, 6, 19, 16, 11, 1, 17, 15, 5, 9, 13,
    3, 21, 20, 8, 10, 22, 2, 23, 14, 12, 7, 18]

/-- The fixed MOG coordinate assignment is a bijection, so no bit is lost or duplicated. -/
theorem mogCoordinate_bijective : Function.Bijective mogCoordinate := by
  native_decide

/-- Integer-scale coordinates of the 24 fixed Leech minimal-vector addresses.
Coordinates are divided by `sqrt 8` in the Euclidean Leech model.  Addresses
0–22 have `4` in their own coordinate and coordinate 23; address 23 has `4`
and `-4` in coordinates 0 and 23. -/
def leechAddress (i j : Fin 24) : ℤ :=
  if i.1 < 23 then
    if j = i ∨ j.1 = 23 then 4 else 0
  else
    if j.1 = 0 then 4 else if j.1 = 23 then -4 else 0

/-- Each stored address has integer-scale squared norm 32, hence norm 4 after
rescaling squared norms by 1/8 in the standard Euclidean model. -/
theorem leechAddress_sqNorm (i : Fin 24) :
    ∑ j : Fin 24, leechAddress i j * leechAddress i j = 32 := by
  fin_cases i <;> native_decide

/-- No two MOG cells receive the same 24-dimensional address. -/
theorem leechAddress_injective : Function.Injective leechAddress := by
  native_decide

/-- Symmetric XOR interaction used as a control descriptor. -/
def symmetricInteraction (a b : BitVec 24) : BitVec 24 := a ^^^ b

/-- Swapping two element objects does not change their symmetric interaction. -/
theorem symmetricInteraction_comm (a b : BitVec 24) :
    symmetricInteraction a b = symmetricInteraction b a := by
  exact BitVec.xor_comm a b

/-- Placing an object against an identical object gives the zero XOR contrast. -/
theorem symmetricInteraction_self (a : BitVec 24) :
    symmetricInteraction a a = 0 := by
  exact BitVec.xor_self

/-- The symmetric contrast retains enough information to recover either input
when the other input is known. -/
theorem symmetricInteraction_recover (a b : BitVec 24) :
    symmetricInteraction a b ^^^ b = a := by
  simp [symmetricInteraction, BitVec.xor_assoc]

/-- The three classical minimal-vector shape counts have the expected
factorizations: coordinate pairs and signs for A, octads and even signs for B,
and a distinguished coordinate and Golay word for C. -/
theorem leechMinimalClass_counts :
    Nat.choose 24 2 * 4 = 1104 ∧
    759 * 128 = 97152 ∧
    24 * 4096 = 98304 ∧
    1104 + 97152 + 98304 = 196560 := by
  simp [Nat.choose]

/-- A representative Class-A vector has integer-scale squared norm 32. -/
def classARepresentative : Fin 24 → ℤ := fun k =>
  if k.1 = 0 ∨ k.1 = 1 then 4 else 0

/-- A representative Class-B vector has integer-scale squared norm 32. -/
def classBRepresentative : Fin 24 → ℤ := fun k =>
  if k.1 < 8 then 2 else 0

/-- A representative Class-C vector has integer-scale squared norm 32. -/
def classCRepresentative : Fin 24 → ℤ := fun k =>
  if k.1 = 0 then 3 else 1

/-- Every classical shape family has squared norm 32 in integer coordinates,
corresponding to squared norm 4 after division by `sqrt 8`. -/
theorem leechMinimalClass_representative_sqNorms :
    (∑ k : Fin 24, classARepresentative k * classARepresentative k) = 32 ∧
    (∑ k : Fin 24, classBRepresentative k * classBRepresentative k) = 32 ∧
    (∑ k : Fin 24, classCRepresentative k * classCRepresentative k) = 32 := by
  native_decide +revert

/-- Predeclared interaction A at one coordinate: additive co-presence. -/
def interactionA (x y : ℤ) : ℤ := x + y

/-- Predeclared interaction B at one coordinate: unsigned contrast. -/
def interactionB (x y : ℤ) : ℤ := |x - y|

/-- Predeclared interaction C at one coordinate: multiplicative coupling. -/
def interactionC (x y : ℤ) : ℤ := x * y

/-- All three coordinate operators are invariant under exchanging the participants. -/
theorem interactionABC_symmetric (x y : ℤ) :
    interactionA x y = interactionA y x ∧
    interactionB x y = interactionB y x ∧
    interactionC x y = interactionC y x := by
  constructor
  · exact add_comm x y
  constructor
  · simp [interactionB, abs_sub_comm]
  · exact mul_comm x y

/-- The contrast part of an object's self-interaction is zero. -/
theorem interactionB_self (x : ℤ) : interactionB x x = 0 := by
  simp [interactionB]

/-- UBP TAX specialized to a binary vector of Hamming weight `w`: because every
binary coordinate satisfies `x² = x`, norm-squared and weight coincide. -/
def binaryTax (Y : ℚ) (w : ℕ) : ℚ := (w : ℚ) * (Y + 1 / 8)

/-- The supplied NRCI transform, specialized to binary-vector TAX. -/
def binaryNRCI (Y : ℚ) (w : ℕ) : ℚ := 10 / (10 + binaryTax Y w)

/-- For nonnegative wobble parameter, binary TAX is monotone in Hamming weight.
Thus it carries no ordering information beyond the weight itself. -/
theorem binaryTax_mono {Y : ℚ} (hY : 0 ≤ Y) : Monotone (binaryTax Y) := by
  intro a b hab
  simp only [binaryTax]
  exact mul_le_mul_of_nonneg_right (by exact_mod_cast hab) (by positivity)

/-- Below the exact binary-weight boundary, the stated NRCI horizon is automatic:
weights at most 16 have NRCI strictly above one half whenever `Y < 3/16`. -/
theorem binaryNRCI_above_half {Y : ℚ} (hY0 : 0 ≤ Y) (hY : Y < 3 / 16)
    {w : ℕ} (hw : w ≤ 16) : 1 / 2 < binaryNRCI Y w := by
  unfold binaryNRCI binaryTax
  have hfactor : 0 ≤ Y + 1 / 8 := by positivity
  have htax_nonneg : 0 ≤ (w : ℚ) * (Y + 1 / 8) := mul_nonneg (by positivity) hfactor
  have hwq : (w : ℚ) ≤ 16 := by exact_mod_cast hw
  have htax : (w : ℚ) * (Y + 1 / 8) < 10 := by nlinarith
  rw [div_lt_div_iff₀ (by positivity) (by positivity)]
  nlinarith

/-- A subject passes a peer-relative coherence threshold when its score retains
at least the declared fraction of the peer reference score. -/
def relativeCoherent (retention subject peer : ℚ) : Prop :=
  retention * peer ≤ subject

/-- Under the observed element-score bounds, retaining 70% of any peer score is
automatic.  This formalizes why that relative rule is non-selective here. -/
theorem element_relativeCoherent_seventy_percent
    {subject peer : ℚ} (hsubject : 3 / 5 ≤ subject) (hpeer : peer ≤ 4 / 5) :
    relativeCoherent (7 / 10) subject peer := by
  rw [relativeCoherent]
  calc 7 / 10 * peer ≤ 7 / 10 * (4 / 5) := mul_le_mul_of_nonneg_left hpeer (by norm_num : (0:ℚ) ≤ 7/10)
    _ = 14 / 25 := by norm_num
    _ ≤ 3 / 5 := by norm_num
    _ ≤ subject := hsubject

/-- The declared Y virtual-twin map retains the original coordinates and appends
a fixed scalar copy.  It is therefore injective but adds no information. -/
def yTwin (Y : ℚ) (x : Fin n → ℚ) : Fin n → ℚ × ℚ :=
  fun i => (x i, Y * x i)

/-- The Y virtual-twin feature map is injective for every Y because its first
component is the original vector. -/
theorem yTwin_injective (Y : ℚ) : Function.Injective (yTwin (n := n) Y) := by
  intro x x' h
  funext i
  exact congrArg Prod.fst (congrFun h i)

/-- Cyclic-coordinate indices in the three adjacent-column-pair regions of the
fixed MOG.  Each row lists one verified weight-eight region. -/
def octadZoneCoordinate : Fin 3 → Fin 8 → Fin 24 :=
  ![![0, 4, 1, 17, 3, 21, 2, 23],
    ![6, 19, 15, 5, 20, 8, 14, 12],
    ![16, 11, 9, 13, 10, 22, 7, 18]]

/-- The three eight-coordinate MOG regions are disjoint and cover all 24
coordinates. -/
theorem octadZoneCoordinate_bijective :
    Function.Bijective (fun p : Fin 3 × Fin 8 => octadZoneCoordinate p.1 p.2) := by
  native_decide

/-- The unscaled rational form of the published three-row Walsh visualization.
Dividing each output by `sqrt 24` gives the real-valued matrix in the audit;
the rational form has the same kernel. -/
def projection24to3Q (x : Fin 24 → ℚ) : Fin 3 → ℚ := fun r =>
  ∑ c : Fin 24,
    (if r.1 = 0 then (if c.1 < 12 then 1 else -1)
     else if r.1 = 1 then (if c.1 / 6 % 2 = 0 then 1 else -1)
     else (if c.1 / 3 % 2 = 0 then 1 else -1)) * x c

/-- The declared 24-to-3 view is necessarily lossy: two distinct coordinate
basis vectors have the same image. -/
theorem projection24to3Q_not_injective : ¬ Function.Injective projection24to3Q := by
  intro hinjective
  let e0 : Fin 24 → ℚ := fun c => if c.1 = 0 then 1 else 0
  let e1 : Fin 24 → ℚ := fun c => if c.1 = 1 then 1 else 0
  have himage : projection24to3Q e0 = projection24to3Q e1 := by
    funext r
    fin_cases r <;> native_decide
  have heq := hinjective himage
  have hat0 := congrFun heq (0 : Fin 24)
  norm_num [e0, e1] at hat0

end GolayMOG
