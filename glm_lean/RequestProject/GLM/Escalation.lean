/-
# Escalation at register scale

`LayerChain.lean` proves the shipped five-layer stack is a refinement chain over
the whole 24-coordinate carrier space.  This file is about what happens when the
audit stops being run on seven hand-picked carriers and is run on the machine's
own data — the thousand-odd named entries of the physics, chemistry, molecule,
mathematics, harmonics and lexicon registers, which
`glm_universal/reasoning/escalation.py` measures.

Three things the measurement turns on are proved here.

* **A register is a *naming*, not a set of carriers.**  Two entries may carry
  the same 24 coordinates, and then no layer of the stack can tell them apart,
  because every layer's view is a function of the carrier alone.  The number of
  distinct carriers is therefore a ceiling on what escalating can ever resolve
  — `entryResolution_le_distinct` — and the rational layer already attains it
  (`entryResolution_rational`), so climbing above the rational layer cannot
  separate one further entry.  That is the shape the measurement found: 1,040
  entries, 757 distinct carriers, and 757 classes at each of the top three
  layers.
* **Resolution can only rise.**  `entryResolution_mono` is `resolution_mono`
  carried to registers: for any naming and any two heights of the chain, the
  higher layer resolves at least as many entries.  The measured column
  415 → 544 → 757 → 757 → 757 is an instance, and no growth of the registers
  can invert it.
* **Addition stops descending below the rational layer, and the witness is a
  half.**  `glmRationalLayer_congruentOn` says every operation descends where
  the view is the carrier itself, which is why the scaled audit reports the top
  three layers as congruent without searching.  Underneath, a single pair of
  carriers — a half unit and the vacuum — is a witness that addition does not
  descend to the substrate (`substrate_addition_not_congruent`) or to the
  integer layer (`glmIntegerLayer_addition_not_congruent`): both readings take
  the integer part first, and ⌊1/2⌋ + ⌊1/2⌋ is not ⌊1/2 + 1/2⌋.

The keyed partition the Python module uses to make the audit linear needs no
separate justification here: a layer in this development *is* its view map, so
`Indist` is key equality by definition, and the module's per-layer keys are the
views listed in `LayerChain.lean`'s table.
-/
import RequestProject.GLM.LayerChain

namespace GLM.Info

open Layer

variable (intOf : ℚ → ℤ) {A : Type} (axis : Carrier24 → A)

/-! ## Registers: entries named, carriers possibly shared -/

/-- A register, as the audit reads one: a finite index of names, each naming a
carrier.  Nothing forces the naming to be injective, and in the shipped
registers it is not — 78 dimensionless physics quantities share one carrier. -/
abbrev Naming (ι : Type) : Type := ι → Carrier24

variable {ι : Type} [Fintype ι]

open scoped Classical in
/-- How many of a register's entries a layer can tell apart. -/
noncomputable def entryResolution (L : Layer Carrier24) (R : Naming ι) : ℕ :=
  (Finset.univ.image fun i => L.perceive (R i)).card

open scoped Classical in
/-- How many distinct carriers the register's entries occupy. -/
noncomputable def distinctCarriers (R : Naming ι) : ℕ :=
  (Finset.univ.image R).card

omit [Fintype ι] in
/-- **Entries that share a carrier are invisible to every layer.**  A layer sees
a carrier and nothing else, so a naming collision cannot be undone by climbing. -/
theorem indist_of_carrier_eq (L : Layer Carrier24) {R : Naming ι} {i j : ι}
    (h : R i = R j) : L.Indist (R i) (R j) := by
  unfold Layer.Indist
  rw [h]

open scoped Classical in
/-- A register's entries, seen by a layer, are the carriers they name seen by
that layer: `entryResolution` is `Layer.resolution` on the carrier set the
naming reaches. -/
theorem entryResolution_eq_resolution (L : Layer Carrier24) (R : Naming ι) :
    entryResolution L R = resolution L (Finset.univ.image R) := by
  classical
  unfold entryResolution resolution
  rw [Finset.image_image]
  rfl

open scoped Classical in
/-- **The ceiling.**  No layer resolves more entries than there are distinct
carriers among them: escalation cannot separate what the data does not. -/
theorem entryResolution_le_distinct (L : Layer Carrier24) (R : Naming ι) :
    entryResolution L R ≤ distinctCarriers R := by
  classical
  rw [entryResolution_eq_resolution]
  exact resolution_le_card L _

open scoped Classical in
/-- The rational layer attains the ceiling: its view *is* the carrier, so it
resolves exactly as many entries as there are distinct carriers. -/
theorem entryResolution_rational (R : Naming ι) :
    entryResolution glmRationalLayer R = distinctCarriers R := by
  classical
  rw [entryResolution_eq_resolution]
  unfold resolution distinctCarriers
  exact Finset.card_image_of_injective _ glmRationalLayer_lossless

open scoped Classical in
/-- Hence every layer above the rational one resolves the same number of
entries: `757` at the rational, Griess and universal layers is not three
measurements but one. -/
theorem entryResolution_eq_of_lossless {L : Layer Carrier24} (h : L.Lossless)
    (R : Naming ι) : entryResolution L R = distinctCarriers R := by
  classical
  rw [entryResolution_eq_resolution]
  unfold resolution distinctCarriers
  exact Finset.card_image_of_injective _ h

open scoped Classical in
/-- **Resolution rises with the layer, on any register.**  This is
`resolution_mono` read through a naming, and it is the guarantee behind the
measured column 415 → 544 → 757: growing the registers changes the numbers and
cannot change their order. -/
theorem entryResolution_mono {L L' : Layer Carrier24} (h : Refines L' L)
    (R : Naming ι) : entryResolution L R ≤ entryResolution L' R := by
  classical
  rw [entryResolution_eq_resolution, entryResolution_eq_resolution]
  exact resolution_mono h _

/-! ## Where addition still descends, and where it stops -/

/-- Coordinatewise addition of carriers: the operation the audit tests for
descent, and the one `information_loss.carrier_sum` computes. -/
def addCarrier (a b : Carrier24) : Carrier24 := fun i => a i + b i

/-- **Every operation descends to a lossless layer.**  The rational, Griess and
universal layers hold the carrier itself, so there is nothing for a witness to
exploit; this is why the scaled audit reports them congruent without a search. -/
theorem congruentOn_of_lossless {L : Layer Carrier24} (h : L.Lossless)
    (S : Set Carrier24) (op : Carrier24 → Carrier24 → Carrier24) :
    CongruentOn L S op := by
  intro a b a' b' _ _ _ _ haa hbb
  have ha : a = a' := h haa
  have hb : b = b' := h hbb
  unfold Layer.Indist
  rw [ha, hb]

theorem glmRationalLayer_congruentOn (S : Set Carrier24)
    (op : Carrier24 → Carrier24 → Carrier24) :
    CongruentOn glmRationalLayer S op :=
  congruentOn_of_lossless glmRationalLayer_lossless S op

theorem glmGriessLayer_congruentOn (S : Set Carrier24)
    (op : Carrier24 → Carrier24 → Carrier24) :
    CongruentOn (glmGriessLayer axis) S op :=
  congruentOn_of_lossless (glmGriessLayer_lossless axis) S op

theorem glmUniversalLayer_congruentOn (S : Set Carrier24)
    (op : Carrier24 → Carrier24 → Carrier24) :
    CongruentOn (glmUniversalLayer intOf axis) S op :=
  congruentOn_of_lossless (glmUniversalLayer_lossless intOf axis) S op

/-- Half a unit on coordinate 0: the carrier whose integer part is zero and
whose double's is not. -/
def halfInside : Carrier24 := unitAt 0 (1 / 2)

/-- One unit on coordinate 0. -/
def oneInside : Carrier24 := unitAt 0 1

/-- The reading that makes the half a witness: its integer part is zero. -/
theorem halfFloor : ⌊(2⁻¹ : ℚ)⌋ = 0 := by
  rw [Int.floor_eq_zero_iff]
  constructor <;> norm_num

theorem addCarrier_half_half : addCarrier halfInside halfInside = oneInside := by
  funext i
  by_cases hi : i = (0 : Fin 24)
  · subst hi
    simp [addCarrier, halfInside, oneInside, unitAt]
    norm_num
  · simp [addCarrier, halfInside, oneInside, unitAt, hi]

theorem addCarrier_vacuum_half : addCarrier vacuum24 halfInside = halfInside := by
  funext i
  simp [addCarrier, vacuum24]

/-- The substrate cannot tell half a unit from the vacuum: the parity reading
takes the integer part first, and ⌊1/2⌋ = 0. -/
theorem substrate_indist_half_vacuum :
    (glmSubstrateLayer intFloor).Indist halfInside vacuum24 := by
  funext i
  by_cases hi : i = (0 : Fin 24)
  · subst hi
    have h : halfInside (0 : Fin 24) = 1 / 2 := by simp [halfInside, unitAt]
    simp [parityView, intFloor, vacuum24, h]
    norm_num
  · simp [parityView, intFloor, vacuum24, halfInside, unitAt, hi]

/-- But it can tell their doubles apart: ⌊1⌋ is odd. -/
theorem substrate_separates_one_half :
    ¬ (glmSubstrateLayer intFloor).Indist oneInside halfInside := by
  intro h
  have hc := congrFun h (0 : Fin 24)
  have h1 : oneInside (0 : Fin 24) = 1 := by simp [oneInside, unitAt]
  have h2 : halfInside (0 : Fin 24) = 1 / 2 := by simp [halfInside, unitAt]
  simp [glmSubstrateLayer, parityView, intFloor, h1, h2] at hc
  rw [halfFloor] at hc
  exact absurd hc (by decide)

/-- The integer layer cannot tell them apart either: it adds the seven SI7
exponents to the parity reading, and ⌊1/2⌋ is zero for those too. -/
theorem integer_indist_half_vacuum :
    (glmIntegerLayer intFloor).Indist halfInside vacuum24 := by
  refine Layer.cumulative_indist_iff.2 ⟨substrate_indist_half_vacuum, ?_⟩
  funext i
  by_cases hi : (i : ℕ) = 0
  · have h0 : si7Index i = (0 : Fin 24) := by
      apply Fin.ext
      simpa [si7Index] using hi
    have h : halfInside (si7Index i) = 1 / 2 := by
      rw [h0]; simp [halfInside, unitAt]
    simp [si7View, intFloor, vacuum24, h]
    norm_num
  · have h0 : si7Index i ≠ (0 : Fin 24) := by
      intro hEq
      exact hi (congrArg Fin.val hEq)
    simp [si7View, intFloor, vacuum24, halfInside, unitAt, h0]

/-- **Addition does not descend to the substrate**, and the witness is a half.
Replacing a half unit by the vacuum — a substitution the substrate cannot see —
changes what it sees of the sum, so no function of parity bits computes the
parity bits of a sum. -/
theorem substrate_addition_not_congruent :
    ¬ CongruentOn (glmSubstrateLayer intFloor) Set.univ addCarrier := by
  intro h
  have hstep := h halfInside halfInside vacuum24 halfInside trivial trivial
    trivial trivial substrate_indist_half_vacuum (Layer.indist_refl _ _)
  rw [addCarrier_half_half, addCarrier_vacuum_half] at hstep
  exact substrate_separates_one_half hstep

/-- The same pair defeats the integer layer, which carries the substrate's
reading and so inherits its witness. -/
theorem glmIntegerLayer_addition_not_congruent :
    ¬ CongruentOn (glmIntegerLayer intFloor) Set.univ addCarrier := by
  intro h
  have hstep := h halfInside halfInside vacuum24 halfInside trivial trivial
    trivial trivial integer_indist_half_vacuum (Layer.indist_refl _ _)
  rw [addCarrier_half_half, addCarrier_vacuum_half] at hstep
  exact substrate_separates_one_half
    (Layer.cumulative_indist_iff.1 hstep).1

end GLM.Info
