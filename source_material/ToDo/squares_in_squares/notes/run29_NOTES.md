# Run 29 notes (2026-11-06)

Run documentation under the distinct name.  The same content is in README.md (Run 29 section), RUN_NOTES.md, and download/run29/README.md.
# Run 29 (2026-11-06): the SAT measure — TAX/NRCI on the SAT data

User input: is there a measure on the SAT data — like the TAX
measurement the GLM uses, with NRCI as a metric?

## Where TAX and NRCI are defined

The repo the user linked (github.com/DigitalEuan/GLM) is the parent
system; the definitions live in the uploaded GLM papers
(upload/GLM_Complete_Number_Theory_Evidence.md §1.1–1.3):
Y = 1/(π+2/π) ∈ (0.264675, 0.264676), Q = Y+1/8, B = 10;
TAX(v) = HW(v)·Y + ‖v‖²/8 = HW·Q on binary carriers; NRCI(v) =
B/(B+TAX(v)) ∈ (0,1] with the Lean theorem NRCI = 1 ⟺ v = 0;
regimes at TAX ≤ 5/2 / ≤ 10 / ≤ 70/3 (onBit / coherent /
transitional, subcoherent above).

## The SAT data's binary layer: the symmetry tie

A contact pair is **tied** when the two axis families see the same
two directions — multiset{pen_u0, pen_v0} = multiset{pen_u1,
pen_v1} — the case where the tight axes come in symmetry-tied pairs
(even weight; run 28's parity law).  Measured: the tie residual is
bimodal with a 3.3-decade empty gap — tied population ≤ 5e-12 (float
noise of exact constructions), generic continuum ≥ 1.1e-8.  The
carrier of the measure is the packing's contact word; its 1-bits are
the **generic** (non-tied) contacts, g of them.  SAT-TAX = g·Q;
SAT-NRCI = 10/(10+SAT-TAX); the GLM regime map at integer cutoffs
g ≤ 6/25/59 (exact under the proved Y bounds).  Instrument:
scripts/sat_measure.py; ledger workspace/push/sat_measure29.json.
Validated on the n=50 decode row (C=105, g=10, the ten weight-1
contacts of runs 26/28).

## What the measure says (§2b)

1. **The vacuum is exactly the grid.**  NRCI = 1 precisely on the 546
   grid rows — no generic contacts ⟺ grid.
2. **The provable frontier off the vacuum is the four hand-proved
   packings.**  Göbel 5 (φ = 1.00: all four contacts generic), Ahmed
   11, Overbeck 17, Fitzharding 19 (NRCI 0.70–0.87).  Everything
   else below grid is unproven territory (450 rows, NRCI median
   0.39, 55 subcoherent).
3. **Depth is not bought with genericity.**  Within run18-frontier,
   φ-vs-depth = −0.61 (shallow third φ 0.138, deep third 0.048); the
   deepest class, chain3 (d/√n median 0.0123), sits nearly at the
   vacuum (φ 0.015).  The landscape is two-phase: a vacuum phase
   (lattice-tied, depth by chain arithmetic at large n) and a generic
   phase (small n, hand-proved).  This corrects run 28's P1'
   prescription — genericity is the signature of the small-n
   provable regime, not a depth strategy.
4. **A falsifiable prediction for P2.**  T-263 (n=299) is the most
   generic row per contact in the table (φ 0.101).  If settling its
   41 floaters improves L, the improved packing should come with φ
   down / NRCI up.  φ up falsifies the two-phase picture and re-aims
   P1' at the generic language.

## NEXT_STEPS.md updated to the Run-29 state

New §2b (the SAT measure); §2a.1 reading corrected; P1' and P2
guidance updated (NRCI logged before/after on P2); §0 row; §6
run-29 entry.  Copies: NEXT_STEPS.md and download/NEXT_STEPS.md.

Score 22.819977568 (unchanged — measurement run); download
table/csv copies in sync (no table change).
