# 84 — Run 116's band test, re-run on the corrected driver (run 125)

Run 116's re-squeeze null came from an instrument that doc 83 §2 found guilty of two defects: `patches` /
`solve_patch` penalised only patch-vs-**outside** pairs, so a patch could overlap itself at zero cost, and
`patches` returned an **empty list** for a flat pose. A null from that instrument is not evidence. This re-runs
the same three bands on the corrected driver. **The null is confirmed; the old violation counts are retracted;
the k = 32 notch is measured deeper than run 116 could see it; and the re-run is itself budget-limited.**

## 1. The protocol, held fixed

Run 116's bands: insert one cell at the best free-space point of the band's frontier pose, hinge the container at
`k`, and ask whether the result is legal at 40 digits with a side strictly below `k`. Bands k = 26 (with a
no-insert control) and k = 32, whose frontier poses are n = 655 and n = 998.

The re-run changes only the instrument, and only in the three ways doc 83 records:

| | run 116 | this run |
|---|---|---|
| patch list | `resqueeze.patches` — exclusive bounds, can be empty, skips last row/col | `structure.patches` — inclusive, never empty |
| patch penalty | patch-vs-outside only | intra-patch pairs included (`solve_patch_w`) |
| legalisation | none — a pose left illegal by the relaxer's 1e-9 tolerance was reported as a jam | `structure.legalise`, 40-digit ladder with an exact monotone stop at `k` |

`--corrected` keeps the old path intact for the record; the corrected run writes
`workspace/push/resqueeze116_corrected.json`.

## 2. Results

| band | run 116 | corrected driver | beat |
|---|---|---|---|
| k = 26, control (no insert, n = 655) | `26.00000000132585821722780372142460596278`, **76 violations** | `26.00000000157039249645036947510335896172`, pen 8.088e-15 (max 1.49e-8), side ≥ k | no |
| k = 26, insert one cell (n = 656) | `26.00000000132585758710197519778940807573`, **79 violations** | `26.00000000366561618870813889061627995114`, pen 1.89e-9 (max 1.71e-5), side ≥ k | no |
| k = 32, insert one cell (n = 999) | `31.99687596003605622186409680131440612314`, **17 violations** | pose reaches `31.90666480806531849` with 4.13e-3 penetration (max 2.40e-2); first near-legal rung is `f = 0.1`, giving `35.09733128887185034232018692623109691890` | no |

Inserted-cell sizes are the same as run 116's (0.99979740 at k = 26, 0.83900259 at k = 32), so the comparison is
like for like on the band geometry.

**What changes, band by band:**

* **k = 26, control.** Both instruments land the untouched pose just above `k` (26.0000000013 vs 26.0000000016,
  a 2.4e-10 difference from a different relaxation path). Run 116's 76 violations were the relaxer's own 1e-9
  residue counted as overlap; the corrected driver reports the same pose without pretending to certify it, and
  legalisation would only push it further above `k`. The control still does its job: the instrument does not
  destroy a legal pose.
* **k = 26, insert.** Run 116's `26.0000000013` with 79 violations and this run's `26.0000000037` agree: the
  inserted cell is absorbed and the frontier's own `delta` is spent. No pose at or below `k` is produced.
* **k = 32, insert.** This is the band that mattered. Run 116 saw `31.996876` (3.1e-3 inside `k`, worth 9.9e-5)
  jammed 17 pairs deep. The corrected driver drives the pose **deeper — to 31.9067, 9.3e-2 inside `k`** — and
  measures the jam as 4.13e-3 of penalty with a 2.40e-2 deepest bite. Legalisation then asks the only question
  left: at `f = 0.1` (the first rung whose penetration is under the 1e-6 screen) the side is **35.0973**, i.e.
  **3.1 above the grid side**. The notch is real room; the price of legality is thirty times the gain.

## 3. Verdict

**Run 116's null is confirmed on all three bands, and its violation counts are retracted.**

* Confirmed: none of the three bands produces a legal pose below `k` on the corrected driver. For k = 26 the
  pose settles just above `k`; for k = 32 the only pose below `k` is illegal and legalising it costs a 10 %
  expansion, landing 3.1 above the bar.
* Retracted: the numbers 76, 79 and 17 were produced by a penalty that could not see overlaps inside a patch and
  a patch list that could be empty. They are instrument artifacts, not measurements of a jam. The corrected run
  does not replace them with a count, because the pose's exact side already bars a gain and the 40-digit pair
  pass is only paid where it can change a verdict.
* Corrected depth: the k = 32 notch is **9.3e-2** inside `k`, not 3.1e-3 — run 116's shallower reading was the
  instrument, and run 117's hand repair (stuck at 9.39e-2 of bite, no single slide helping) sits between the two.

## 4. What this does not settle

Both runs are **sweep-limited**, and the re-run says so in its own records (`budget_limited: true` for all three
bands). One relaxation sweep costs 72.6 s at n = 439 and 163.3 s at n = 942 (doc 83 §3), so at n = 655 and 999 a
60 s band budget covers well under one sweep: the corrected bands ran one squeeze/project cycle and stopped. The
null therefore says "no beat inside this budget on this instrument", which is the same sentence run 116 was
entitled to say — it is *not* a statement that the re-squeeze family cannot beat these bands. The route stays
open exactly where doc 83 leaves it: behind the throughput of the patch solve.

## 5. Checks

| check | result |
|---|---|
| `resqueeze.py --corrected --seconds 60` | 3 bands, 0 beats, 0 certified legal poses below `k` |
| `structure.py --control` | A: 100 % recovery of 3.75e-3, legal; B: displaced cell absorbed, legal |
| `resqueeze.py` (legacy path, `resqueeze116.json`) | unchanged, kept for the record |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
