# Noise in UBP — Geometric Frustration, Not Probability

The UBP architecture rejects continuous, probabilistic "noise." Everything is discrete, exact geometry.

## 1. "Noise" = Geometric Frustration (High TAX / Ghost States)

In UBP, "visual noise" or "ambiguity" is a 24-bit state that has fallen off the valid topological manifold.

- **Ghost State:** Sensor fuzz, visual artifacts, or misalignment generates an arbitrary 24-bit state v that is NOT a valid Golay codeword.
- **TAX:** The substrate registers "noise" as computational friction (TAX / Syndrome Weight). High TAX = local grid region experiencing spatial ambiguity or multi-color boundary clashes.

## 2. "Noise Clean" = Deterministic Topological Snapping

Standard diffusion models clean noise by guessing. UBP cleans via **The Golay Attractor Engine**.

- **The Attractor:** Complete extended binary Golay [24,12,8] decoder, covering radius 4.
- **The Snap:** Noisy high-TAX state v is forced to collapse ("snap") to nearest valid codeword c ∈ G₂₄ within distance ≤ 4.
- **The Result:** Rigid, deterministic "ghost-state filter." Wandering vectors, pixel jitter, entropic artifacts stripped away instantly.

## 3. "Cross Pattern" Detection = Boolean Face Transforms

No convolutional pixel filters. Uses **Directed Boolean Face Transforms** across X, Y, Z axes (X,Y = Gray-coded spatial, Z = colour/state).

- **XY Transform (AND):** Identifies spatial overlaps and aligned grid structures. Isolates intersecting node of a cross.
- **XZ Transform (XOR):** Detects spatial boundaries and contrast edges. Traces the sharp 4-way boundary of a cross against background.
- **YZ Transform (OR):** Merges contiguous colour domains into connected objects. Recognizes entire "cross" as unified geometrical construct.

## The Active Perception Loop

1. Scan grid → detect TAX spike around fuzzy intersection
2. High TAX → trigger ROI crop (zoom on ambiguous bounding box)
3. Apply XY (AND) and XZ (XOR) face transforms → extract intersection + edges
4. Pass through Golay decoder → snap remaining noise into clean 24-bit object

## Source

User notes (Euan Craig), 7 August 2026.
