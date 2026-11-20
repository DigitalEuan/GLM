# 60 — The two-word seam: what the table actually couples, and why `w1 ⋈ w2` cannot break `2k + ½√2`

Run 97, 20 November 2026. Two questions, one instrument, no float.

1. What do the delivered rows that sit *below* the single-word floor `2k + ½√2` actually
   do with their rotations?
2. Can a **field-exact two-word coupled tangency** be built, and does any such sentence
   break that floor or beat the table at the same count?

The answers, in one line each: the below-floor rows at the ridge's own counts are **one
word in a block** (a 17×17 lattice of the 45° word, reused at `k = 13, 14, 15`), the
genuine two-word rows are **mirror pairs** `(θ, 90° − θ)` tangent at the table's `1e-9`
polish, and a two-word seam sentence built exactly over 36 word pairs × `k = 1..8`
**never gets below `2k + 2.019`** — it is not merely unable to break the floor, it pays
0.60–1.12 *more* than the single-word family at the same count.

`submission.csv` and root `WHITEBOARD.md` are untouched; no row moved, no score claimed.

## 1. The delivered rows below the floor

### 1a. At the ridge's own counts, the table uses one word — in a block

`family_spin.py --motifs` walks the 15 rows with `N = 4k² + 1` (`k ≤ 15`). Fourteen of
them sit strictly below `2k + ½√2`; the only exception is `N = 5`, which sits exactly
*on* it. From `k = 4` onward every one of these rows uses exactly **two rotation
classes**: axis squares and the 45° word.

| `n` | `k` | `L` | `L − 2k` | classes |
|---|---|---|---|---|
| 5 | 1 | 2.70711 | **+0.707107** | 0°×4, 45°×1 |
| 17 | 2 | 4.67553 | +0.675530 | 0°×10, 39.805°×6, 53.376°×1 |
| 37 | 3 | 6.59862 | +0.598620 | 42.087°×6, 45°×3, 47.913°×6, 90°×22 |
| 65 … 577 | 4 … 12 | `2k+0.535534` | +0.535534 | 0°×…, 45°×25 (×95, ×145 at `k = 9, 12`) |
| 677, 785, 901 | 13, 14, 15 | `2k+0.520815` | +0.520815 | 0°×388/496/612, 45°×**289** |

The tilted count `289 = 17²` is not a coincidence and not a coupling: projecting the 289
tilted centres of `n = 901` onto the 45° word's own axes gives **17 distinct `u` levels
and 17 distinct `v` levels, every gap exactly `1.000000`** — a 17×17 lattice of one word,
side `17` in its own frame. At `n = 677` (`k = 13`) the same block appears with the
*same* `u` and `v` ranges (`u ∈ [9.6924, 25.6924]`, `v ∈ [−7.6464, 8.3536]`): the table
keeps the tilted block and grows the axis fill around it. That is a **homometric block**,
not a mixed tangency, and it is the thing that carries the row below the floor.

### 1b. The rows that really do carry two tilted words are mirror pairs

443 delivered rows carry two or more tilted classes. 363 of them give every square its
own angle (more than twelve classes) — the relaxed rung, whose classes are not words at
all and are excluded from the pairing. Of the rest, 26 rows have exactly two classes, and 9
of those are **mirror pairs** `(θ, 90° − θ)`; 56 rows have a mixed tangency tight to
`|residual| < 1e-6`, i.e. the coupling is a real tangency at the table's own `1e-9`
polish. 52 of the two-word rows are below the floor.

| `n` | slack | classes | tightest mixed residual |
|---|---|---|---|
| 17 | +0.675530 | 39.805°×6, 53.376°×1 | 4.7e−10 |
| 37 | +0.598620 | 42.087°×6, 45°×3, 47.913°×6 | 3.1e−10 |
| 102 | +0.605829 | −43.090°×12, +43.090°×19 | 1.9e−10 |
| 198 | +0.571429 | 36.870°×16, 53.130°×16 | 1.5e−10 |
| 904 | +0.563626 | 33.876°×96, … | 2.5e−10 |

`n = 198` is the cleanest: `36.870° = arctan(3/4)` and `53.130° = arctan(4/3)` are the
two 3-4-5 words `(4/5, 3/5)` and `(3/5, 4/5)` — the same rational pair, mirrored. Their
exact mixed tangency is **`28/25`**, not `1`. `n = 37` shows the same idea with three
words (`45° ± 2.913°`), symmetric about the 45° word.

So the table's low-slack rows split cleanly: at the ridge's counts a **one-word block**,
and at small `N` a **mirror pair** whose coupling is exact but whose price is `≥ 1`.

## 2. The two facts that decide the builder's reach

**(i) The floor is a per-square price.** A unit square at word `θ = (c, s)` standing in the
ridge's cross (four `k`-blocks, seam width `w`) is tangent to the blocks at

    φ(θ) = min(x, 1/x),        x = |c| + |s|,

and the single-word ridge attains `w = φ(θ)` at every word — so `φ` is the value, not a
bound. For a unit word `x² = 1 + 2|cs| ∈ [1, 2]`, hence `x ∈ [1, √2]` and

    φ(θ) ≥ ½√2,      equality exactly at |c| = |s| = ½√2 (the 45° word and its turns).

The floor is therefore not a property of one family: **every** square in a mixed bar pays
it, separately. (`glm_wheels.seam_floor`; control 28 asserts the equality and that
`φ·x = 1` for the Seventh and the census word.)

**(ii) A mixed tangency is never cheaper than a same-word one.** Two unit squares of
different words need, along the first one's own axis,

    need(θ₁, θ₂) = (1 + |cos Δ| + |sin Δ|) / 2,        Δ = θ₂ − θ₁,

which is exactly `1` for the same word (a quarter turn included) and *strictly greater*
than `1` otherwise, since `|cos Δ| + |sin Δ| > 1` off the axes. The 3-4-5 mirror pair
pays `28/25`; the mildest pair in the spin pays `1.002088`. (`two_word_need`.)

Consequence, before any code runs: a sentence whose seam is one shared number `w` and
whose squares all stand in the same four blocks pays `w ≥ max(φ₁, φ₂) ≥ ½√2`, and the
coupling itself only *lengthens* the bar. Two words cannot cancel the seam; they can
only add to it. What the builder below does is confirm this exactly, and measure the
addition.

## 3. The builder

`glm_wheels.py` (run 97 section), zero float, `Quad(d)` throughout:

* `seam_floor(cls, c, s)` — fact (i), exact;
* `two_word_need(cls, q1, q2)` — fact (ii), exact;
* `_two_word_slots` — the bar: word 1 at the seam centre (the ridge's own slot), word 2
  at the *mixed* need from it along word 1's `-v`, i.e. a vertex-to-edge tangency across
  the two words, which no single-word sentence can express;
* `two_word_gauge(cls, k, q1, q2)` — the minimal seam width **in closed form**. The four
  blocks ride outward with `w` while the bar rides outward with `w/2`, so every
  block-slot separation is *monotone* in `w`: once separated, always separated. The
  sentence's width is therefore the maximum over pairs of the pair's own threshold, and
  a threshold is the smallest `w` at which any one of its four axes separates — an exact
  linear root. No scan, no tolerance, the same discipline as the single ridge's
  `min(1/(c+s), c+s)`;
* `two_word_pair(d, q1, q2, k)` — the exact gate is the **arbiter**: it certifies the
  sentence and the claim records `L`, `N`, void, contacts, the seam and the two floors.
  Refusals are declared (`two_word_same_word`, `two_word_no_gauge`, `two_word_inside`).

Control 28 asserts that the closed-form gauge equals the gate's own `L − 2k` at `k = 1,
2, 3` — so the reported width really is a contact width, not an interpolation.

## 4. The spin

`glm_wheels.py --two-word-spin`: 36 distinct word pairs inside their own field
(`Q(√2)`: 45°, `t = 1/2, 1/3, 1/5`, `pyth-3/4`, `pyth-5/12` → 15 pairs; `Q(√7)`: the
Seventh, the census word and five rational words → 21 pairs), each at `k = 1..8`:

* **288 sentences, 288 gated** at clearance exactly `0`, `0` refusals, ledger
  `workspace/push/two_word_spin.json`;
* the seam is **constant in `k`** for each pair — the "constant seam" case named in
  advance — and ranges over `2.019084 … 2.533523`;
* the margin over the single-word floor `L − (2k + ½√2)` ranges `1.311977 … 1.826416`
  (closest: `pyth-3/4 × pyth-8/15` in `Q(√7)`; widest: `t = 1/2 × pyth-3/4` in `Q(√2)`);
* every mixed need is `> 1` (`1.002088 … 1.204980`);
* **0 of 288 sit below `2k + ½√2`**, and **0 of 288 beat the delivered row** at the same
  `N = 4k² + 2`.

For scale, at the same count the *single-word* family has the `m = 2` ridge at the 45°
word, `L = 2k + √2 = 2k + 1.414214`. The two-word sentences are **0.605 to 1.119 wider**
than that. Coupling is not a way to reach the floor — it is a way to leave it further
behind.

## 5. Verdict, and the production that would actually move

**Structural refusal, with the mechanism named.** In the seam (cross) topology the floor
`2k + ½√2` is per-square and the mixed tangency is `> 1`, so no choice of two words can
narrow the seam; the builder's exact constant, `2k + 2.019…2.534`, is the measured price
of trying. The cheapest "coupling" is the degenerate one — both squares at 45° — which is
no longer a coupling: that *is* the single-word `m = 2` ridge at `1.414`.

**What the table does instead** is §1a: a **block** of one word. A 17×17 tilted lattice
with unit spacing in its own frame is not a seam at all; its boundary meets the axis fill
along a staircase, so the constant-seam argument does not apply to it. That is the next
production, and it has a falsifier: build a 45° block of `s²` squares with axis fill in
the four corner triangles, and ask whether the exact gate reproduces `L = 2k + 0.520815`
at `N = 4k² + 1` for `k = 13, 14, 15` (and `2k + 0.535534` for `k ≤ 12`). If it does, the
delivered frontier at those counts is grammar, and the block's side law is the thing to
prove; if it does not, the 17×17 block is a pose at the table's `1e-9` polish and the
424-row relaxed rung stays the frontier.

## 6. Honesty about what is proved and what is measured

* **Proved (exact, zero drift):** fact (i) at the words the spin uses (`φ·x = 1`,
  `φ ≥ ½√2`, equality at 45°); fact (ii) for all 36 pairs (`need = 1` only for the same
  word); the 288 sentences (gate clearance `0`, `gate_L == L`); the closed-form gauge
  equals the gate's own width.
* **Measured (12-dp pose, `Decimal` at 70 digits):** every statement about the delivered
  rows — the class counts, the 17×17 lattice projections, the mixed residuals at `~1e-10`
  and the slacks. Those rows are not exact sentences, as run 95 established with the
  `−2.365e-9` overlap.
* **Not claimed:** that no two-word sentence of *any* topology can beat the floor. §1b
  shows the table's own two-word rows are corner wedges at small `N`, where the seam is
  not a cross; this run's refusal is specific to the cross, and it says so.
* The Lean references (`RequestProject/GLM/Escalation.lean`, `EscalationLoop.lean`) stay
  conceptual anchors, never a build dependency.

## 7. Verification

* `glm_wheels.py --selftest` — **28 controls, exit 0** (`1 m 50.7 s`; control 28 is the
  new one, ≈ 2 s), `--audit` — **253 functions, 0 offenders**.
* `glm_wheels.py --two-word-spin` — 288 rows, 288 gated, 0 below the floor, 0 beating the
  table, `1 m 43 s`, ledger `workspace/push/two_word_spin.json`.
* `family_spin.py --motifs` — 15 ridge-count rows, 443 two-word rows, ledger
  `workspace/push/row_motifs.json` (read-only over `submission.csv`).
* `family_spin.py --calibrate` / `--gate-ks` / `--beyond`, `grammar_induction.py`,
  `qsqrt2.py`, `field_triage.py`, `record_guard.py` — unchanged and green.

`submission.csv` untouched; no row changed; no score claimed.
