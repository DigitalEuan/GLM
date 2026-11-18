# 27 — Bui's staircase, implemented and refused (run 62)

**Track A of the next push.** Source found, construction implemented exactly,
certified against the canonical scorer — and refused, with the reason measured
rather than argued. No row changed.

## 1. The nomination, and where it comes from

`19` §10.8 listed "Bui's construction, still unimplemented" without a source.
It is:

> **Hong Duc Bui, "Square packing with O(x^0.6) wasted area", arXiv:2508.04603v2**
> (v1 Aug 2025, v2 Mar 2026). §3.1.1 *Initial Configuration*, §3.1.2
> *Modification of the Packing*.

`21` §8 had already analysed it from the text and reached an arithmetic judgement
(waste `O((m+i_m)θ) + O(x^{3/4}+x^{1/2})` at `x ≈ 25` is the same order as the
delivered atom's `L² − n = 25.3`). `22` §7 then withdrew the one *structural*
objection that had made it untestable — with rational `t = tan(θ/2)` every such
orientation is exactly representable in ℚ. So the remaining question was purely
"does it save space at our sizes", which is a build, not an argument.

## 2. What was implemented, exactly

All of §3.1.1 is exact over ℚ once θ and σ₁ are given by rational half-tangents:

    D₁ = cos θ,        D₂ = sec(θ+σ₁) sin σ₁,      D₃ = sec(θ+σ₁) cos σ₁
    S(i, j+1) − S(i, j) = u = (cos θ, −sin θ)                  (|u| = 1: they touch)
    S(i+1, j) − S(i, j) = (D₂, −D₃)
    i_j = ⌈(j−1)(1 − D₁)/D₂⌉ + 1,    n₀ = m·i_m tilted squares

The construction's own soundness check is a one-line identity, asserted in
`Fraction` by the selftest: the inter-row offset has **row-normal component
exactly −1**,

    (D₂, −D₃)·(sin θ, cos θ) = −sec(θ+σ₁)·cos(θ+σ₁) = −1,

which is why consecutive rows are one unit apart and never overlap. The
instrument is `scripts/bui_wheel.py` (`--selftest` 8/8), ledger
`workspace/push/bui_wheel.json`.

**One modelling bug, recorded.** The first build put every row in collision
(`worst_pen +7.8e-2`). The squares must be rotated by **−θ**, not +θ: the row
axis `(cos θ, −sin θ)` is an *edge* direction of the square, so the state angle
is `−θ`. With that fixed every cell verifies.

## 3. What was deliberately not reproduced

§3.1.2 closes the staircase with a quadrilateral `ABCD` and replaces everything
above each ceiling with vertical stacks `T`. The vertical placement of `CD` is
given relative to Figures 6–9, and this wheel does **not** claim to reproduce it.
Instead it does the weaker, checkable thing:

* seal the staircase in its bounding **square** of side `max(w, h)` — valid by
  construction, since any `w × h` rectangle fits in a square of side `max(w,h)`;
* fill the free region with upright unit squares, greedily, in whole cells
  (below and above each column's band).

The result is a valid packing of `n = n₀ + n_fill` squares. Its side is an
**upper bound** on what this primitive can do at that cell, so a refusal here is
conservative — it cannot hide a gain that a faithful `ABCD` would have found.

## 4. The result: 132 cells, 132 verified, 0 gains

Grid: m ∈ {5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30}, θ from half-tangents
{1/12, 1/10, 1/8, 1/6}, σ₁ from {1/20, 1/14, 1/10}.

| | |
|---|---|
| cells built | **132** |
| cells accepted by `packlib.verify` | **132 / 132** |
| cells in range n ≤ 1000 | 132 |
| **cells with a positive canonical gain** | **0** |
| best gain over the grid | **−0.078** (and every other cell is worse) |
| worst gain | −1.051 |
| achieved density n/L² | 0.227 – 0.823 |
| delivered density at those rows | ≈ 0.95 |

No cell gains. The closest is n = 294, where the wheel reaches `L = 19` against
the delivered 17.656854; a representative mid-range cell (m = 20, θ ≈ 0.166) gives
`n = 192` at `L = 21` against the delivered 14.0 — a deficit of seven units of
side. The refusal is not marginal, and the reason is structural
rather than numerical. (The 0.823 maximum density is reached only at small m,
where the band nearly fills its square; it is still below the table's ≈ 0.95.)

## 5. Why: the primitive is a slanted tile, not a square

The staircase occupies a **parallelogram-like band**: about `m` wide, about
`i_m·cos θ` tall, with the top and bottom edges sloped by θ. Sealing one band in
a square therefore pays the two triangular corners. At m = 20, θ ≈ 0.166 the seal
is `L = 21` holding `n = 192`, density **0.435** — against 0.96 for any delivered
row at that size. The construction only becomes competitive when many tiles are butted
together, which is exactly what the paper does next:

* §4 packs a **right trapezoid** with these quadrilaterals;
* §5 reduces **square packing to trapezoid packing**, tiling the square.

That two-level tiling — not the primitive — is where `O(x^{0.6})` comes from, and
it is a substantially larger build than a wheel. The arithmetic in `21` §8 is
consistent with what we measured: at `x ≈ 25` the accounted waste is the same
order as the delivered atom's, so no win is indicated at our sizes.

## 6. Refusal, stated as a scope

* **What was excluded:** the `ABCD` closure of §3.1.2 (figure-dependent), the §4
  trapezoid packing, the §5 square reduction, and the dual method (§6.2).
* **What was tested:** the primitive sealed in its bounding square with a greedy
  cell fill, 132 parameter cells, all exactly rational, all accepted by the
  canonical verifier.
* **What is refused:** "a Bui staircase can improve a row of this table" — on the
  evidence of §4, it cannot, by a wide margin, in primitive form.
* **What would reopen it:** implementing §4 + §5 so that tiles fill a square
  rather than sitting in one. That is a different piece of work and needs its own
  wheel; the ledger here (`bui/1`) is the price of the primitive, which any such
  build inherits.

## 7. Files

* `scripts/bui_wheel.py` — exact builder, ceiling, seal, greedy fill, `--selftest`
  8/8; `cell_report` scores every cell against the delivered row.
* `workspace/push/bui_wheel.json` — 132 cells with `n`, `L`, `theta`, `i_m`,
  `n_tilted`, `n_fill`, `gain`, `verifies`, `worst_pen`.
* `workspace/raw/bui.html` — the fetched paper, kept for audit.
* follows `19` §10.8; corrects `21` §8's premise (the field objection is dead,
  `22` §7) while confirming its arithmetic conclusion.
