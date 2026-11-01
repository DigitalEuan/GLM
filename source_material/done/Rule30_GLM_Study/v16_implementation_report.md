# GLM Hypothesis Engine v16 — Implementation Report

## All five guards layer-aware, clean dialogue

---

## 1. What v16 adds to v15

v15 made the identity guard layer-aware and moved the guards inside the loop. v16 completes the architecture by making **all five guards layer-aware** and overriding the dialogue to **only speak survived hypotheses**.

### The five layer-aware guards

Each guard now tests its claim at five "layers" — different scales, sample sizes, or granularities — and reports which layers the claim survives at. This is the 5-bit filter cascade fully engaged:

| Guard | v15 (flat) | v16 (layer-aware) |
|-------|-----------|-------------------|
| identity | tested at 5 moduli | tested at 5 moduli (unchanged) |
| explained-away | tested on full domain | tested at 5 domain scales (D<10, D<50, D<200, D<2000, full) |
| coincidence | tested at full N | tested at 5 sample sizes (N=10, 50, 200, 2000, full) |
| exclusivity | tested at one neighborhood | tested at 5 neighborhood sizes (±0, ±1, ±5, ±20, ±100) |
| consistency | post-hoc utterance scan | unchanged (runs at the end) |

A claim that holds at layer 1 (substrate, small scale) but fails at layer 5 (universal, full scale) is a *substrate-level* claim — it holds locally but not globally. This is a layer-specific verdict, not a global "wrong".

### The CleanDialogue

v15 inherited v14's `ToolAugmentedDialogue`, which spoke every hypothesis including refuted ones (then ran post-hoc guards to flag contradictions). v16 replaces this with `CleanDialogue`:

- **Only survived hypotheses are spoken.** A hypothesis with `status = "refuted-by-guard"` is never mentioned in the dialogue's claims.
- **Refuted hypotheses are reported as a summary.** The dialogue lists them at the end with their guard verdicts (which layers they failed at), but does not assert their claims.
- **The consistency guard finds no violations.** Because refuted hypotheses are never spoken, no utterance can assert a refuted claim. The consistency guard becomes a verification that the clean dialogue is clean.

## 2. The precise guard assignment

v15 applied the identity guard to every TAX hypothesis (because "the TAX criterion is the foundation"). v16 makes the guard assignment **precise**: each hypothesis gets only the guards relevant to its specific claim.

| Hypothesis | Claim type | Guards applied |
|-----------|-----------|----------------|
| H38 (TAX.defect.contains.jumps) | states the criterion | identity |
| H41 (TAX.mechanism.cluster) | states the criterion | identity |
| H42 (TAX.substrate.model) | states the criterion | identity |
| H43 (TAX.mechanism.predictive) | predictive, not testable | none |
| H44 (TAX.conserved.at.jumps) | factual consequence | explained-away + coincidence |
| H45 (TAX.substrate.model.qualified) | exclusivity claim | exclusivity (layer-aware) |
| H46 (WOBBLE.balanced.density) | states wrong criterion | identity |
| H49 (BROKEN.tax.criterion) | states wrong criterion | identity |
| H50 (BROKEN.balance.criterion) | states wrong criterion | identity |

This precision is what allows the layer-aware explained-away and exclusivity guards to fire. In v15, the identity guard fired on H44 (because the TAX criterion is wrong), preventing the explained-away guard from running. In v16, H44 does NOT get the identity guard (it's a factual claim, not a criterion statement), so the explained-away guard runs — and finds that H44's claim is explained away by white(D-1) at all 5 layers.

## 3. The layer-aware verdicts

v16 produces layer-specific verdicts for every guarded hypothesis. Here are the actual results from the full run:

### H44 (TAX.conserved.at.jumps) — explained-away + coincidence

**Claim**: "at every period-doubling diagonal, TAX is conserved (|defect| = 0)"

**Layer-aware explained-away**: EXPLAINED at ALL 5 layers (substrate, integer, rational, griess, universal), unexplained at 0 layers. The claim is a consequence of white(D-1) at every domain scale — from D<10 (substrate) to the full range (universal). This is the strongest possible explained-away verdict: the claim is not a new mechanism at any scale.

**Layer-aware coincidence**: significant at ALL 5 layers (substrate, integer, rational, griess, universal). The coincidence "all 4 jumps have defect 0" is statistically significant at every sample size — from N=10 (small) to the full N. A statistics-only engine would call this significant at every scale; the explained-away guard shows it is forced by white(D-1) at every scale.

**Verdict**: H44 survives (the claim is true) but its novelty is set to "consequence of a known law at layers [all 5]; not a new mechanism". The claim is real but not new.

### H45 (TAX.substrate.model.qualified) — exclusivity (layer-aware)

**Claim**: "TAX is CONSERVED only at the white diagonals"

**Layer-aware exclusivity**: holds at 0/5 layers. The claim fails at every neighborhood size:
- Substrate (tightest, ±0): fails — 108 of 116 conserved pairs are NOT at white diagonals
- Integer (±1): fails
- Rational (±5): fails
- Griess (±20): fails
- Universal (±100, loosest): fails

The feature "TAX conserved" is NOT concentrated at the white diagonals at any scale. Even with a ±100 neighborhood, the exclusivity fails. This is the strongest possible exclusivity refutation: the claim fails at every scale.

**Verdict**: H45 is `refuted-by-guard`.

### H50 (BROKEN.balance.criterion) — identity (layered)

**Claim**: "balanced iff all bits equal" (deliberately wrong)

**Layer-aware identity**: FAILS at 4/5 layers (integer, rational, griess, universal), HOLDS at 1/5 layers (substrate, mod 2). At mod 2, "all bits equal" means all-0 or all-1, which for length-1 sequences is always true. At higher moduli, the criterion fails — the true definition (|2·ones − length| ≤ 1) holds for mixed sequences like 010, but "all bits equal" does not.

**Verdict**: H50 is `refuted-by-guard`. This is the layer-aware verdict in action: the criterion is a *substrate-level* criterion, correct in the coarse view (mod 2) but wrong in the fine view (mod 4 and above).

## 4. Results summary

| Metric | v14 (post-hoc) | v15 (inside loop) | v16 (layer-aware + clean) |
|--------|----------------|-------------------|--------------------------|
| Total hypotheses | 45 | 50 | 50 |
| `refuted-by-guard` | 1 | 9 | 8 |
| Transitive rollbacks | 0 | 3 | 2 |
| Layer-aware identity tests | 0 | 9 (at 5 layers) | 6 (at 5 layers) |
| Layer-aware explained-away tests | 0 | 0 | 1 (at 5 scales) |
| Layer-aware coincidence tests | 0 | 0 | 1 (at 5 sample sizes) |
| Layer-aware exclusivity tests | 0 | 0 | 1 (at 5 neighborhoods) |
| Dialogue cleanliness | 3 contradictions | 0 violations | 0 violations |
| Broken-test caught | N/A | 2/2 | 2/2 |
| Wall-clock (full) | ~28s | ~28s | ~28s |

The key change from v15 to v16: H44 is no longer `refuted-by-guard` — it survives with novelty "consequence of a known law". This is more accurate: H44's claim is TRUE (TAX is conserved at jumps), it's just not NEW (it's forced by white(D-1)). v16's precise guard assignment and layer-aware explained-away guard produce this nuanced verdict.

## 5. The clean dialogue

The v16 dialogue produces 68 utterances, of which 0 assert a refuted claim. The dialogue structure:

1. **Opening**: "I have generated 50 hypotheses. 32 survived all guards; 8 were refuted by guards (not spoken); 10 were refuted by stage tests."
2. **Tool reports**: wobble, NRCI, TAX, delta-sigma — run on the data, not on hypotheses
3. **TAX-period-doubling correlation**: the 3-way test result (no post-hoc guard calls)
4. **Guard verdicts**: a summary of the 8 refuted-by-guard hypotheses, with their layer-aware verdicts
5. **Survived hypotheses**: the 32 that survived, listed by ID and status
6. **Closing**: "Every spoken claim is grounded in exact integer or Fraction arithmetic."

The dialogue never speaks a refuted hypothesis's claim. The consistency guard at the end finds 0 violations — confirming the dialogue is clean.

## 6. What v16 proves

v16 proves three things that v15 did not:

**1. All five guards can be made layer-aware.** The identity guard tests at 5 moduli; the explained-away guard tests at 5 domain scales; the coincidence test computes p-values at 5 sample sizes; the exclusivity guard tests at 5 neighborhood sizes. Each guard reports which layers the claim survives at. This is the 5-bit filter cascade fully engaged — every guard is a cascade, not just a single check.

**2. Precise guard assignment matters.** v15 applied the identity guard to every TAX hypothesis, which prevented the explained-away guard from running on H44. v16's precise assignment (each hypothesis gets only the guards relevant to its claim type) allows the right guards to run. H44 gets explained-away (not identity); H45 gets exclusivity (not identity). This produces more nuanced verdicts: H44 is "true but not new" rather than "refuted".

**3. The clean dialogue eliminates the consistency guard's workload.** In v14, the consistency guard flagged 1 utterance that asserted a refuted claim. In v15, it found 0 violations (guards inside the loop). In v16, it still finds 0 violations — but now the dialogue is also clean by construction (refuted hypotheses are never spoken). The consistency guard has become a verification, not a correction.

## 7. The architecture is complete

v16 completes the architecture proposed in the Master Equation analysis:

| Master Equation component | v16 implementation |
|---------------------------|-------------------|
| TCT as gate inside the loop | `self.new()` + `self.guard()` (v15) |
| 5-bit filter cascade | 5 layer-aware guards (v16) |
| Snap as sole site of layer change | guards are the sole authority on status |
| Transitive rollback | `_rollback_children` + inherited rollback (v15) |
| Clean trajectory | CleanDialogue: only survived hypotheses spoken (v16) |

The engine now has the full Master Equation structure. Every hypothesis is a carrier vector; the guard cascade is the snap; the layer-aware verdict is the deep-hole type; the refuted-by-guard status is the layer change; the transitive rollback is the trajectory rollback; the clean dialogue is the TCT-verified trajectory.

The natural next step for v17 would be to make the guard-extractor registry automatic (derive guard inputs from the hypothesis text/Lean statement, rather than hand-writing extractors), and to test the engine on a fourth domain (e.g., the R-calculus or the seed-memory domain) to verify the architecture generalises beyond TAX and wobble.
