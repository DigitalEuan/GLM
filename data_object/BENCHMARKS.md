# GLM Training Benchmarks

**Purpose:** Track the mind's progress across training iterations.  
**How to run:** `python3 training_benchmark.py`  
**Results:** Saved to `data/benchmark_YYYYMMDD_HHMMSS.json`

---

## Current Benchmarks (Iteration 11, 2 Aug 2026)

| Benchmark | Pass Rate | Metric | What It Tests |
|-----------|-----------|--------|---------------|
| triplet_nrci | **100%** | r = +0.79 | 3-body coherence computation |
| shape_intersection | 67% | +0.28 | Geometric intersection via AND |
| golay_error_correction | 60% | 0.40 | Substrate error correction |
| pair_geometry_r | 47% | r = +0.05 | Element pair coherence delta |
| mol_geometry_r | 0% | r = +0.00 | Molecule geometry (needs different spec) |

## What Each Benchmark Measures

### triplet_nrci (100%)
Can the mind compute NRCI for 3-element combinations (molecular fragments)?  
**Status:** Fully working. The AND encoding captures 3-body coherence reliably.

### shape_intersection (67%)
Can the mind identify geometric intersection between shapes?  
**Status:** Partially working. Non-overlapping shapes correctly give AND=0.

### golay_error_correction (60%)
Can the substrate correct bit errors?  
**Status:** Working for 1-3 errors. Some 4-error patterns also correct (60% vs theoretical 0% for 4 errors — the Golay code is sometimes lucky).

### pair_geometry_r (47%)
Can the mind compute meaningful coherence deltas for element pairs?  
**Status:** Weak. Same-element pairs give zero signal (distance=0, ΔNRCI=0).

### mol_geometry_r (0%)
Can the mind compute molecule geometry?  
**Status:** Broken. The v0_baseline spec doesn't encode molecules. Need molecule-specific spec (M, BP, MP).

---

## Training Iterations

| Iter | Focus | Key Result |
|------|-------|-----------|
| 0-4 | Element encoding | r(ΔH) = −0.91 |
| 5 | Molecules | r(ΔH) = +0.96 |
| 6 | Bond order | r(BO, BE) = +0.84 |
| 7 | Full periodic table | 106 unique vectors |
| 8 | Bond geometry | r(BE) = +0.90 (AND encoding) |
| 9 | Bond-order inference | r(BO) = +0.52 from geometry |
| 10 | Substrate training | Shapes, numbers, Golay self-knowledge |
| 11 | Full benchmarks | Triplet NRCI: 100% |

---

## How to Improve

1. **mol_geometry_r:** Use molecule-specific encoding (M, BP, MP) instead of element encoding
2. **pair_geometry_r:** Focus on heteronuclear pairs (same-element pairs have zero signal)
3. **shape_intersection:** Test more shape pairs with known intersection properties
4. **golay_error_correction:** Test with systematic error patterns (not random)
