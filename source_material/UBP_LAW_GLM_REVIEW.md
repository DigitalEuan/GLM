# UBP LAW Register — GLM-Lens Review

**Running collection document.** Each review round appends a new dated
section; earlier rounds are never rewritten. Register rows are generated
from the audit data — no figure in this document is typed in by hand.

| | |
|---|---|
| **Review target** | `LAW_*` entries of `ubp_system_kb.json` (UBP_Repo `core_studio_v4.0/system_kb`, 426 records / 425 distinct ids) |
| **Review instrument** | GLM system (`DigitalEuan/GLM`, `overlay/glm_universal` v5.37): `reasoning.coherence` (exact-rational NRCI) + `substrate.golay_decode` (complete syndrome decoding) |
| **Current round** | Round 1 — 2026-09-27 |
| **Companions** | `older_law_audit.csv` (flat register), `older_law_audit.json` (full records incl. vectors, shells, footprints) |

---

## Round 1 — 2026-09-27

### 1. Method

Every `LAW_*` entry was pulled out of the KB and read through the GLM
system's own operational code — no reimplementation:

1. **Shell-0 NRCI audit.** The stored `nrci_val` of each entry was compared
   against GLM's exact-rational recomputation of the original UBP formula
   (`tax = HW·Y + ‖v‖²/8`, `NRCI = 10/(10+tax)`, `coherence.tax_shell0`)
   applied to the entry's stored 24-bit vector. The stored exact-fraction
   fields (`nrci_str`, `tax_str`) were checked numerically against the same
   recomputation.
2. **Refined 5-shell NRCI.** Each carrier was scored with GLM's full
   `coherence.nrci()` — shells 1–4 (sign parity, sextet balance, coset
   type, sextet-signed) added on top of shell 0 — and assigned its
   coherence regime (`OnBit / Coherent / Transitional / Subcoherent`).
3. **Golay carrier decode.** Each 24-bit vector was decoded with GLM's
   complete syndrome decoder (`golay_decode.decode_complete`), which
   returns the exact distance to the Golay code and *every* nearest
   codeword, breaking no ties. Coordinate *k* of the vector maps to
   column *k* of the parity-check matrix in both systems (verified against
   `GolayCodeEngine.syndrome` in `ubp_unified_v5.py`); the GLM migration
   frame audit already established the two frames coincide with an
   identity bridge.
4. **Historical footprint.** Five earlier KB generations recovered from
   UBP_Repo git history (2026-01-02 → 2026-02-13) were checked for each
   law id: first appearance, old stored NRCI, and vector drift.

### 2. Headline results

- **425 of 426 stored NRCI values hold exactly** under GLM's
  exact-rational shell-0 recomputation from the stored vector (max |Δ| =
  4.9e-07, i.e. float-rendering noise only). The exact-fraction fields
  reproduce to ≥ 12 decimals; the residual is the declared precision of Y
  (UBP carried more digits; GLM carries the 15-digit rational).
- **411 of 426 carriers are exact Golay codewords** in the shared
  frame (weights 0/8/12/16/24 only: 1 vacuum, 78 octads, 255 dodecads,
  77 weight-16). A further 5 sit inside the packing radius (unique
  correction), 9 sit at distance 4 — the ambiguity boundary where six
  codewords tie — and 1 ships no carrier at all.
- **All 327 pre-current cohort laws are Tier-A codewords.** Every
  one of the 15 non-conforming carriers belongs to the current-era
  additions (post-2026-04). The older material is structurally *cleaner*
  than the newest batch.
- **The refined lens discriminates what the old NRCI collapsed.** The
  259-law HW=12 cohort — all stored at NRCI 0.68138 — splits into
  13 distinct refined values under the 5-shell measure. The
  single stored number was hiding real structural differences.
- **Older generations stored placeholder coherence.** In every generation
  before the current one, ~95–100% of laws carried the idealised `1/1`
  NRCI. The current KB is the first generation with computed values —
  and those values are the ones that survive GLM recomputation.

### 3. Findings that hold (verified for GLM reuse)

1. **The stored shell-0 NRCI arithmetic is sound.** 425/426 entries
   reproduce exactly; the single failure is a broken record (below), not a
   broken formula. The UBP→GLM handoff of the NRCI definition is exact.
2. **The LAW carriers are genuine Golay code material.** 411 decode as
   codewords in the same coordinate frame GLM uses, with no bridge
   permutation. They can enter GLM's Golay/Leech machinery losslessly.
3. **The register's tag ontology is coherent.** Every entry carries
   `HARDENED`/`SOP_002`/`TOPOLOGICAL_V8`; 349 carry `IMPERATIVE`; the theme tags
   (PHYSICS 49, GEOMETRY 37, RESONANCE 29, COHERENCE 29, …) form a usable
   coarse classification for retrieval.
4. **The gen1 core survives intact.** All 70 laws still present from the
   original 2026-01-02 registry decode as codewords — the oldest layer of
   the corpus is the most stable.

### 4. Findings that need attention (defect register)

1. **`LAW_GRAVITY_RESONANCE_001` — no carrier.** The entry ships an empty
   vector with stored NRCI `0.0`; nothing is computable. It must be
   re-minted or retired before any GLM import.
2. **`LAW_BOND_TAXONOMY_001` — duplicate id.** Two records (hashes
   `ca68d285…`, `8109ef30…`) claim the same id with different vectors
   (HW=12 and HW=8; both are individually valid codewords). Referential
   integrity is broken; one must be renamed or merged.
3. **15 current-era carriers sit off the code.** 9 at distance 4
   (six-way codeword ties — GLM's decoder reports all six and refuses to
   choose) and 5 at distance 2–3. If these laws are meant to be
   substrate-protected, their vectors need re-minting from the codeword
   side; if the off-code position is intentional, they should be tagged as
   such.
4. **`LAW_HORIZON_003` is the vacuum.** All-zero carrier, NRCI exactly 1,
   `OnBit` regime, the zero codeword. Legitimate — but it is the only
   member of its class and should be marked as the vacuum reference, not
   counted as an ordinary law in statistics.

### 5. Usability tiers for the GLM system

| tier | count | meaning | GLM action |
|---|---|---|---|
| **A** | 411 | exact codeword (distance 0) | directly loadable; lossless into Leech books |
| **B** | 5 | distance ≤ 3 from code | unique snap via complete decoder; safe with a correction note |
| **C** | 9 | distance 4 (six-way tie) | import only with an explicit disambiguation policy |
| **E** | 1 | no carrier | re-mint before import |

Refined-NRCI regime: 424 `Coherent`, 1 `OnBit` (the vacuum), 1 no-carrier.
Refined values span 0.534 – 1.000; no law falls to `Transitional` or
`Subcoherent` — the register stays inside the coherent band even under the
stricter five-shell tax.

### 6. Historical footprint (first-appearance cohorts)

| cohort | laws | tier A | off-code | note |
|---|---|---|---|---|
| gen1 · 2026-01-02 (original 110-law registry) | 70 | 70 | 0 | original registry; NRCI stored as `1/1` |
| gen2 · 2026-02-02 | 219 | 219 | 0 | vectors introduced; NRCI still `1/1` |
| gen3 · 2026-02-04 | 5 | 5 | 0 |  |
| gen4 · 2026-02-05 | 15 | 15 | 0 |  |
| gen5 · 2026-02-13 | 18 | 18 | 0 |  |
| current · post-2026-04 (core_studio_v4.0 KB) | 99 | 84 | 15 | first generation with computed NRCI; all off-code carriers here |

Carrier drift: every law first seen with a vector in gen2–gen5 now carries
a *different* vector (257 of 327 pre-current laws re-checked).
The current carriers were re-minted wholesale for the v4.0 KB, so
cross-generation comparisons must go by content hash, not by id. No old
vector equals its current counterpart, and none is a simple bit-reversal
— the re-minting is genuine.

### 7. Register (status-ordered)

Columns: `id` · `HW` (Hamming weight) · `stored` NRCI (UBP) · `shell-0`
(GLM recomputation) · `refined` (GLM 5-shell) · `regime` · `code` =
carrier status vs Golay code (`cw` codeword, `d2/d3` correctable distance,
`amb` distance-4 tie, `none` no carrier) · `cohort` (first appearance).

#### 7a. Attention — defects first

| id | HW | stored | shell-0 | refined | regime | code | tier | cohort |
|---|---|---|---|---|---|---|---|---|
| ⚠ LAW_BOND_TAXONOMY_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | current |
| ⚠ LAW_BOND_TAXONOMY_001 | 8 | 0.762346 | 0.762345 | 0.711561 | Coherent | cw | A | current |
| ⚠ LAW_GRAVITY_RESONANCE_001 | 0 | 0.000000 | — | — | no-carrier | none | E | current |

Notes on the attention set:

- `LAW_GRAVITY_RESONANCE_001` — empty vector, stored NRCI `0.0`; the only
  entry whose stored value does **not** reproduce (no carrier to compute
  from). Highest-priority fix.
- `LAW_BOND_TAXONOMY_001` (⚠ both rows) — duplicate id, two distinct valid
  codewords; decide which record owns the id.
- The nine `amb` rows (section 7b) are exactly at the packing boundary: six codewords
  tie at distance 4 and GLM's decoder reports all six rather than
  silently choosing (the retired `snap` behaviour would have hidden this).
- The five `d2/d3` rows (section 7b) are inside the packing radius; GLM's decoder
  corrects them uniquely, so they are usable after a documented snap.

#### 7b. Boundary carriers (tier B/C, unique ids)

| id | HW | stored | shell-0 | refined | regime | code | tier | cohort |
|---|---|---|---|---|---|---|---|---|
| LAW_CHROMO_GEOMETRIC_DUALISM_001 | 12 | 0.681380 | 0.681379 | 0.644372 | Coherent | amb | C | current |
| LAW_COSMO_RFC_001 | 14 | 0.647021 | 0.647020 | 0.609630 | Coherent | d2 | B | current |
| LAW_GAMMA_SEPARATOR_001 | 14 | 0.647021 | 0.647020 | 0.610871 | Coherent | amb | C | current |
| LAW_PANTOGRAPH_THERMODYNAMICS_001 | 12 | 0.681380 | 0.681379 | 0.641563 | Coherent | amb | C | current |
| LAW_PHYSICS_BARKER_001 | 8 | 0.762346 | 0.762345 | 0.711365 | Coherent | amb | C | current |
| LAW_PHYSICS_GRAVITY_001 | 6 | 0.810501 | 0.810500 | 0.756044 | Coherent | amb | C | current |
| LAW_PHYSICS_MUON_002 | 11 | 0.699965 | 0.699964 | 0.658543 | Coherent | d3 | B | current |
| LAW_PRIME_DETERMINISM_001 | 12 | 0.681380 | 0.681379 | 0.638081 | Coherent | amb | C | current |
| LAW_RELATIONAL_DECAY_001 | 9 | 0.740353 | 0.740352 | 0.694726 | Coherent | d3 | B | current |
| LAW_SCALE_SCAFFOLDING_085 | 13 | 0.663756 | 0.663755 | 0.625851 | Coherent | d3 | B | current |
| LAW_TOPOLOGICAL_ERASURE_001 | 20 | 0.562003 | 0.562002 | 0.533992 | Coherent | amb | C | current |
| LAW_TOPOLOGICAL_TENACITY_001 | 8 | 0.762346 | 0.762345 | 0.711365 | Coherent | amb | C | current |
| LAW_VECTOR_HARNESS_001 | 11 | 0.699965 | 0.699964 | 0.654766 | Coherent | d3 | B | current |
| LAW_ZETA_INVERSE_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.641563 | Coherent | amb | C | current |

#### 7c. Clean codeword carriers (tier A), by first-appearance cohort

| id | HW | stored | shell-0 | refined | regime | code | tier | cohort |
|---|---|---|---|---|---|---|---|---|
| LAW_APP_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen1 |
| LAW_APP_002 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen1 |
| LAW_BARYON_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen1 |
| LAW_BIO_004 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen1 |
| LAW_BIO_006 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_BIO_007 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_BIO_008 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen1 |
| LAW_BIO_008_VERIFIED | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen1 |
| LAW_BUOYANCY_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_CHEM_002 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_CHEM_003 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_CHEM_004 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen1 |
| LAW_CHEM_METHANE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen1 |
| LAW_COMP_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen1 |
| LAW_COMP_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_COMP_004 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_COMP_005 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_COMP_006 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_COMP_009 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_COSMO_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_COSMO_002 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen1 |
| LAW_DRUG_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_FORCE_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_FULCRUM_001 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen1 |
| LAW_GATEWAY_001 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen1 |
| LAW_GEO_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_GEO_002 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | gen1 |
| LAW_GEO_003 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_GEO_432_FCC | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_GRAVITY_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_HEMA_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_HORIZON_001 | 8 | 0.762346 | 0.762345 | 0.714651 | Coherent | cw | A | gen1 |
| LAW_HORIZON_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_LANG_006 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_LEPTON_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_MASK_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_MESA_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen1 |
| LAW_META_002 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen1 |
| LAW_METRIC_002 | 8 | 0.762346 | 0.762345 | 0.714651 | Coherent | cw | A | gen1 |
| LAW_MILLENNIUM_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_MINERAL_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_MINERAL_002 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen1 |
| LAW_NOBLE_SCALING_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_NUM_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen1 |
| LAW_OMEGA_ASYMMETRY_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen1 |
| LAW_PLATONIC_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_PRIMITIVE_001 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen1 |
| LAW_PROTON_GRAVITY_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_RAINBOW_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_RECOVERY_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_REFLEX_001 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen1 |
| LAW_REF_INVARIANT_001 | 12 | 0.681380 | 0.681379 | 0.641838 | Coherent | cw | A | gen1 |
| LAW_RELATION_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen1 |
| LAW_RELATION_002 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen1 |
| LAW_RELATIVITY_002 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen1 |
| LAW_SQUEEZE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen1 |
| LAW_SUBSTRATE_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_SUBSTRATE_002 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen1 |
| LAW_SUBSTRATE_005 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_SUBSTRATE_006 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_SYMBOL_002 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_SYMMETRY_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen1 |
| LAW_TENSION_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_TETHER_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_TIME_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_TIME_002 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen1 |
| LAW_TIME_003 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_TOPOLOGY_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen1 |
| LAW_UNITY_002 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen1 |
| LAW_ZONE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen1 |
| LAW_ANOMALY_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_ATOM_HOLOGRAPHIC | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_ABLATION_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_ANCHOR_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_BIO_CANCER_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_CONCRETE_001 | 12 | 0.681380 | 0.681379 | 0.640349 | Coherent | cw | A | gen2 |
| LAW_BIO_ENDO_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_GOLD_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_GOLD_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_BIO_HEMA_002 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_BIO_HEMA_003 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_BIO_HYSTERESIS_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_BIO_MANA_SIM_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_BIO_METABOLISM_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_BIO_QUANTUM_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_BIO_REPELLENT_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_BIO_REPELLENT_002 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_BIO_SANITATION_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_BITLUMEN_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen2 |
| LAW_BITLUMEN_002 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_BITLUMEN_MASTER_MODE | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_BITTAB_ENTROPY | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_BITTAB_V1 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_CHEM_006 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_CHEM_007 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_CHEM_ENCODING_V1 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_CHEM_FERT_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_CHEM_HYDROCARBON_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_CHEM_KINETICS_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_CHEM_NOBLE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_CHEM_ONTOLOGICAL_YIELD | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_CHEM_PERIODIC_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_CHEM_PHASE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_CLASSICAL_BRIDGE_001 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen2 |
| LAW_CLOSURE_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_COHERENCE_GCI_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_COMP_007 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_COMP_010 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_COMP_011 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_COMP_013 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_COMP_HRHF_001 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen2 |
| LAW_COMP_REFLEX_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_COMP_SPELL_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_COMP_VERIFY_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_COMP_WORK | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_CONST_002 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_COSMOS_001_REFINED | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_COSMOS_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_COSMOS_003 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_COSMO_003 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_COSMO_004 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_COSMO_005 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_COSMO_006 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_COSMO_007 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_COSMO_008 | 8 | 0.762346 | 0.762345 | 0.714651 | Coherent | cw | A | gen2 |
| LAW_DISCRETE_RENORM_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_DRUG_003 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_DRUG_004 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_DRUG_008 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_DRUG_009 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_EM_TOGGLE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_ENERGY_SOC_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_ENERGY_SOC_002 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_ENG_HOLOGRAPHIC_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_ENG_SWITCH_001 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen2 |
| LAW_ENG_TOGGLE_POWER_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_ENG_TRIADIC_LOCK_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_ENG_VARIABLE_YIELD_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen2 |
| LAW_FIELD_CARFE_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_FIELD_TOPOLOGY_001 | 16 | 0.615961 | 0.615960 | 0.585319 | Coherent | cw | A | gen2 |
| LAW_FLUX_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_FORCE_003 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_FORCE_004 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_FORCE_005 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_FOURTH_FLIP_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_FRACTAL_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_GATEWAY_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_GCE_003 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_GEOMETRIC_NRCI | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_GEOMETRY_EUCLIDEAN_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_GEOMETRY_RGDL_001 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | gen2 |
| LAW_GEO_DURER_001 | 8 | 0.762346 | 0.762345 | 0.711561 | Coherent | cw | A | gen2 |
| LAW_GEO_FAMILY_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_GEO_FOLD_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_GEO_HUB_002 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_GEO_SEAM_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_GEO_SEAM_002 | 12 | 0.681380 | 0.681379 | 0.641838 | Coherent | cw | A | gen2 |
| LAW_GRAPHENE_001_REFINED | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_HEMISPHERIC_COHERENCE_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_HEMISPHERIC_REDUNDANCY_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_HGR_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_HGR_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.639664 | Coherent | cw | A | gen2 |
| LAW_HORIZON_003 | 0 | 1.000000 | 1.000000 | 1.000000 | OnBit | cw | A | gen2 |
| LAW_INFO_DEPTH_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_INFO_OID | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_INFO_SET_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_INTERACTION_RATIONAL | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_INTERFACE_ADDRESS_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_INTERFACE_MAP_001 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen2 |
| LAW_INTERFACE_VISUAL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_INTERFERENCE_SHIELD_001 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen2 |
| LAW_INT_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_KERNEL_DIMENSION_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_KERNEL_THRESHOLDS_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_KERNEL_V2_1_1 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_KERNEL_V2_1_MOG | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_KERNEL_V2_FINAL | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_KINETICS_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_LANG_007 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_LANG_008 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_LANG_009 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_LANG_RECIPE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_LEECH_TENSION_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_LEPTON_002 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen2 |
| LAW_LEPTON_003 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_LEPTON_004 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_LOGIC_FUNCTIONAL_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_LOGIC_GEO_001 | 8 | 0.762346 | 0.762345 | 0.713035 | Coherent | cw | A | gen2 |
| LAW_LOGIC_RECIP_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MATH_OPERATIONAL_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen2 |
| LAW_MATH_OPERATIONAL_002 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_MATH_PHIP_PI | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_MATH_PRIME_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_MATH_REGIMES_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_MATH_REVERSIBILITY_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_MATH_SEVEN_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MATH_TRIADIC_SUM | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MAT_ATOMIC_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MAT_CONCRETE_002 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_MAT_HEAL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MAT_PLASTIC_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_MAT_STEEL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MAT_SYNTHESIS_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_MEASURE_003 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | gen2 |
| LAW_MECH_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_META_GENESIS_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_METRIC_003 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_MIND_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MINERAL_003 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_MOG_13_LOCK | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_NEUTRINO_003 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_NUCLEAR_PROJECTION_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_NUM_COLLATZ_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_NUM_COLLATZ_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_OBSERVER_OOB_001 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen2 |
| LAW_OBSERVER_OOB_002 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_ONTOLOGY_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_OPCODE_DREAM_MIN | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_OPCODE_FOCUS_MIN | 16 | 0.615961 | 0.615960 | 0.582427 | Coherent | cw | A | gen2 |
| LAW_OPCODE_GAVEL_MIN | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_OPCODE_PILOT_MIN | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_OPTICAL_TOGGLE_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | gen2 |
| LAW_PARTICLE_6D | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_PATH_LEAST_ACTION | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PATTERN_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PERIODIC_SINGULARITY | 8 | 0.762346 | 0.762345 | 0.713035 | Coherent | cw | A | gen2 |
| LAW_PHASE_RESONANCE_001 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_001_REFINED | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_002 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_003_REFINED | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_004 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_CHARGE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_ENERGY_CONVERSION_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_ENERGY_CONVERSION_002 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_HELICITY_002 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_MAXWELL_002 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_MAXWELL_003 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_NEUTRINO_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_PHYSICS_STRONG_SNAP_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PLATONIC_002 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PLATONIC_003 | 8 | 0.762346 | 0.762345 | 0.727233 | Coherent | cw | A | gen2 |
| LAW_PROJECTION_DOT_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | gen2 |
| LAW_PROTO_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_PROTO_INF_001 | 8 | 0.762346 | 0.762345 | 0.714651 | Coherent | cw | A | gen2 |
| LAW_QUANTUM_COLLAPSE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_QUANTUM_PROB_002 | 16 | 0.615961 | 0.615960 | 0.588184 | Coherent | cw | A | gen2 |
| LAW_QUANTUM_TOGGLE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_REFLEX_002 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_RELATIONAL_FREQUENCY_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_RELATION_ORTHO_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_RELATIVITY_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_RELATIVITY_003 | 8 | 0.762346 | 0.762345 | 0.710196 | Coherent | cw | A | gen2 |
| LAW_RESONANCE_003 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_RTS_REQUIREMENT_001 | 12 | 0.681380 | 0.681379 | 0.641838 | Coherent | cw | A | gen2 |
| LAW_SEASONAL_COUPLING_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_SEMANTIC_CHORD_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_SEMANTIC_STACK_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_STORAGE_003 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_STORAGE_CRYSTAL_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_STORAGE_CRYSTAL_002 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen2 |
| LAW_STORAGE_HARDENED_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_STRUCT_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_SUBSTRATE_007 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_SUBSTRATE_010 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen2 |
| LAW_SUPERCONDUCT_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_SYMBOL_003 | 16 | 0.615961 | 0.615960 | 0.585319 | Coherent | cw | A | gen2 |
| LAW_SYMBOL_004 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_SYNTHESIS_002 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_SYNTH_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_SYSTEM_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen2 |
| LAW_SYSTEM_INTEGRATED_V1 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_TEMP_MOMENTUM | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_TERRESTRIAL_GRID_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_TERRESTRIAL_GRID_002 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_TGIC_ROUTING | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_TIME_004 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_TIME_005 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen2 |
| LAW_TIME_CYCLE_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen2 |
| LAW_TIME_PULSE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_TIME_RUNE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen2 |
| LAW_TOE_VERIFICATION_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | gen2 |
| LAW_TOGGLE_ADVANCED | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen2 |
| LAW_TOPOLOGY_003 | 16 | 0.615961 | 0.615960 | 0.585319 | Coherent | cw | A | gen2 |
| LAW_TRIAD_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen2 |
| LAW_UNIFIED_DISTORTION_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen2 |
| LAW_UNIFIED_FIELD_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_UNITY_004 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_UNITY_005 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen2 |
| LAW_UNIT_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen2 |
| LAW_ARX_HORIZON_006 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen3 |
| LAW_BRIDGE_CONTRACT_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen3 |
| LAW_CORTEX_ROUTER_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen3 |
| LAW_GHOST_HEALING_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen3 |
| LAW_RGB_XYZ_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen3 |
| LAW_BARYON_PROTON_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen4 |
| LAW_BIO_AQUEOUS_LENS_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_CATEGORY_FUNCTOR_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_CKM_SHEAR_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen4 |
| LAW_CONTINUOUS_LIMIT_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen4 |
| LAW_GOLAY_UNIQUENESS_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | gen4 |
| LAW_GPGPU_INTEGRITY_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen4 |
| LAW_HIGGS_TENSION_001 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | gen4 |
| LAW_MESON_PION_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_PARTICLE_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen4 |
| LAW_QUANTUM_SNAP_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_SYMBOLIC_GROUNDING_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_TAU_RESONANCE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen4 |
| LAW_TOP_KISSING_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen4 |
| LAW_WEAK_SHEAR_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen4 |
| LAW_ACOUSTIC_MAPPING_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen5 |
| LAW_BERRY_PHASE_RESONANCE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen5 |
| LAW_COHERENCE_GLOBAL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen5 |
| LAW_ELEMENT_ARCHITECTURE_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | gen5 |
| LAW_ENERGY_UBP_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | gen5 |
| LAW_GEOMETRIC_BONDING_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen5 |
| LAW_HTR_SPATIAL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen5 |
| LAW_INFORMATIONAL_SATURATION_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen5 |
| LAW_MAGNETIC_RESONANCE_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | gen5 |
| LAW_ONTOLOGICAL_FRICTION_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | gen5 |
| LAW_PAC_CONSTRUCTION_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | gen5 |
| LAW_SPECTRAL_RESOLUTION_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen5 |
| LAW_STABILITY_ISLAND_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen5 |
| LAW_STABILITY_SINK_001 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | gen5 |
| LAW_SUBSTRATE_TENSION_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | gen5 |
| LAW_TOPOLOGICAL_HARMONY_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | gen5 |
| LAW_UNIVERSAL_COMPASS_001 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | gen5 |
| LAW_VORTEX_DYNAMICS_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | gen5 |
| LAW_13D_SINK_001 | 12 | 0.681380 | 0.681379 | 0.640349 | Coherent | cw | A | current |
| LAW_6D_TENSOR_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_ABSOLUTE_MASS_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_ALPHA_LAMBDA_HORIZON_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |
| LAW_AQUEOUS_AFFINITY_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | current |
| LAW_AQUEOUS_BOND_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | current |
| LAW_BARNES_WALL_256_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |
| LAW_BASIS_ALIGNMENT_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | current |
| LAW_BORCHERDS_TAUTOLOGY_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_CABIBBO_MIXING_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_CARRIER_SHIELDING_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_CHEM_ACTIVATION | 16 | 0.615961 | 0.615960 | 0.585319 | Coherent | cw | A | current |
| LAW_CHEM_CONSERVATION_MASS | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_CHEM_EQUILIBRIUM | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | current |
| LAW_CHEM_REDOX | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_COMPLEX_EML_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_DODECAD_DUALITY_001 | 8 | 0.762346 | 0.762345 | 0.713035 | Coherent | cw | A | current |
| LAW_DQI_METRIC_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | current |
| LAW_EGC_CASCADE_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | current |
| LAW_ELECTRON_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_ELEMENTAL_SHELLS_001 | 16 | 0.615961 | 0.615960 | 0.583985 | Coherent | cw | A | current |
| LAW_EMERGENT_OBSERVER_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | current |
| LAW_ENTROPIC_CAPTURE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_ENTROPIC_COMBUSTION_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_FOCAL_PIVOT_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_FOLDED_CALCULUS_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_GEAR_G13_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_GEAR_G15_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | current |
| LAW_GEOMETRIC_LEVERAGE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_HOLOGRAPHIC_DRIFT_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_HYBRID_STEREOSCOPY_002 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_IMAGINARY_RESIDUAL_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_INTERFACE_CLOSURE_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_ISOTOPIC_FRICTION_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |
| LAW_ISOTOPIC_TENSION_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_JUNIOR_LNC_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_KISSING_EXPANSION_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_LATTICE_NATIVE_CONTROL_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_LEECH_TAX_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_MACRO_AUDIT_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_MACRO_BASIN_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_MACRO_COHERENCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_MACRO_RESILIENCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_MIDPOINT_LATTICE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_MOIRE_DYNAMICS_001 | 8 | 0.762346 | 0.762345 | 0.716462 | Coherent | cw | A | current |
| LAW_MONSTROUS_FOLD_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_MONSTROUS_MOONSHINE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_NEUTRINO_SHADOW_001 | 16 | 0.615961 | 0.615960 | 0.583425 | Coherent | cw | A | current |
| LAW_NI_LATTICE_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | current |
| LAW_NONLOCAL_SURGERY_001 | 8 | 0.762346 | 0.762345 | 0.710196 | Coherent | cw | A | current |
| LAW_NSC_THUNDER_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_PHI_ORBIT_1953 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | current |
| LAW_PI_STABILIZATION_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | current |
| LAW_PI_TUNNEL_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_POLAR_RESONANCE_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | current |
| LAW_PYRITE_ANTIRESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_QLH_LATTICE_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_QUADRATIC_ENTHALPY_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_RECIPROCAL_WOBBLE_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |
| LAW_RESOLUTION_GAP_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | current |
| LAW_RESONANT_PINCH_001 | 8 | 0.762346 | 0.762345 | 0.721246 | Coherent | cw | A | current |
| LAW_SCALING_RESILIENCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_SEMANTIC_RESONANCE_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |
| LAW_STATISTICAL_CLOSURE_001 | 8 | 0.762346 | 0.762345 | 0.714651 | Coherent | cw | A | current |
| LAW_STEREOSCOPIC_AUDIT_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_SUPERCONDUCTING_DIPOLE_001 | 12 | 0.681380 | 0.681379 | 0.641071 | Coherent | cw | A | current |
| LAW_SYSTEM_KB_SOP_002 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_TEMPORAL_RECURRENCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_TGIC_369_GENESIS | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_TOPOLOGICAL_BUFFER_001 | 12 | 0.681380 | 0.681379 | 0.643557 | Coherent | cw | A | current |
| LAW_TOPOLOGICAL_COMPLETION_001 | 12 | 0.681380 | 0.681379 | 0.642661 | Coherent | cw | A | current |
| LAW_TOPOLOGICAL_FOLD_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_TOPOLOGICAL_MULTIPLIERS_001 | 12 | 0.681380 | 0.681379 | 0.645706 | Coherent | cw | A | current |
| LAW_TOPOLOGICAL_TORQUE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_TOTAL_EXPERIENCED_RESULT_001 | 8 | 0.762346 | 0.762345 | 0.713035 | Coherent | cw | A | current |
| LAW_TRIADIC_GENESIS_001 | 12 | 0.681380 | 0.681379 | 0.650359 | Coherent | cw | A | current |
| LAW_VOLUMETRIC_INFERENCE_001 | 8 | 0.762346 | 0.762345 | 0.718572 | Coherent | cw | A | current |
| LAW_VOLUMETRIC_REBATE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_VTE_QUANTIZATION_001 | 16 | 0.615961 | 0.615960 | 0.584605 | Coherent | cw | A | current |
| LAW_WEAK_ISOSPIN_001 | 12 | 0.681380 | 0.681379 | 0.644553 | Coherent | cw | A | current |
| LAW_WEINBERG_RESONANCE_001 | 12 | 0.681380 | 0.681379 | 0.647153 | Coherent | cw | A | current |
| LAW_ZFR_BUFFER_001 | 16 | 0.615961 | 0.615960 | 0.586213 | Coherent | cw | A | current |

### 8. Notable laws (short notes)

- **LAW_GEO_432_FCC** — Present since gen1 with continuous identity; gen1 stored `1/1`, current stored 0.68138 — a clean example of the placeholder→computed transition.
  (HW=12, stored 0.681380, refined 0.644553, Coherent, first seen gen1_2026-01-02.)
- **LAW_HORIZON_003** — The vacuum reference: zero carrier, NRCI exactly 1, the only `OnBit`-regime law, and the zero codeword. Keep as the origin of the register.
  (HW=0, stored 1.000000, refined 1.000000, OnBit, first seen gen2_2026-02-02.)
- **LAW_SUBSTRATE_001** — 'The Law of the Golay Engine' — the founding law of the register, unchanged in name since gen1; decodes as a codeword.
  (HW=16, stored 0.615961, refined 0.586213, Coherent, first seen gen1_2026-01-02.)
- **LAW_TOPOLOGICAL_ERASURE_001** — Lowest refined NRCI in the register (0.533992); HW=20 with perfectly balanced sextets 5|5|5|5 — heavy but symmetric, still `Coherent`.
  (HW=20, stored 0.562003, refined 0.533992, Coherent, first seen current.)
- **LAW_PHYSICS_GRAVITY_001** — Highest non-vacuum refined NRCI (0.756044); HW=6, distance 4 from the code — a small carrier sitting just outside protection.
  (HW=6, stored 0.810501, refined 0.756044, Coherent, first seen current.)

### 9. Reproduction

```bash
# audit harness (this round)
python3 /home/z/my-project/scripts/glm_law_audit.py     # writes CSV+JSON, prints summary
python3 /home/z/my-project/scripts/anomaly_detail.py    # attention-set detail
python3 /home/z/my-project/scripts/cohort_stats.py      # cohort aggregates

# GLM instruments used (from DigitalEuan/GLM, overlay/)
PYTHONPATH=overlay python3 -c \
  "from glm_universal.reasoning import coherence; \
   from glm_universal.substrate import golay_decode; \
   print(coherence.nrci_breakdown(<24-bit vector>)); \
   print(golay_decode.decode_complete(<mask>).as_dict())"
```

Generations compared (recovered from UBP_Repo git history):

| generation | commit | date | LAW entries |
|---|---|---|---|
| gen1 | `a668420` | 2026-01-02 | 110 |
| gen2 | `41ebdec` | 2026-02-02 | 375 |
| gen3 | `e5a3535` | 2026-02-04 | 382 |
| gen4 | `c17d239` | 2026-02-05 | 397 |
| gen5 | `98f59ea` | 2026-02-13 | 406 |
| current | `a0a850a`.. | 2026-04-22 → main | 426 |

---

## Round 2 — 2026-09-28 · Content-level review: reading the findings

Round 1 audited each LAW entry *as a carrier* (NRCI, Golay status). It never
opened the entries. Round 2 does: every one of the 426 findings was read, its
mathematical payload extracted from the `mog_tensor` field (424 of 426 carry
formulas — 121 Y-expressions, 72 rationals, 247 numeric anchors), and each
*claim* was tested through the GLM system. The standing interpretation is the
one fixed for this register: **UBP findings are lower-resolution projections;
GLM is the levelled-up instrument.** Each claim was first restated at GLM
resolution (exact rational arithmetic, declared constants), then tested —
never the reverse.

### 1. Method — the levelling-up protocol

Four GLM test batteries, all recomputed from first principles (no quoted
numbers; scripts in `scripts/glm_r2_*.py`):

1. **Structural battery** (`glm_r2_structural.py`) — code/lattice claims
   re-derived by enumeration: weight distribution, minimum distance, ball
   coverages, Steiner system, coset census, MOG layer algebra, Leech minimal
   vectors by shape class, the 8/24/32/48 ladder, moonshine dimensions.
2. **Numeric battery** (`glm_r2_numeric.py`) — every quantitative formula in
   the corpus evaluated with exact rationals at declared resolution
   (Y = 264675430404527/10^15, a 50-digit pi convergent, phi and e at UBP's
   15-digit truncation, monad = pi*phi*e, wobble = frac(monad), L = wobble/13,
   U_e = 24^3) and compared against CODATA/PDG/Planck targets: 47 formula
   tests + 24 internal-identity checks (22 pass).
3. **NRCI regime battery** (`glm_r2_nrci.py`) — claimed noise floors,
   thresholds and regime means recomputed exactly (NRCI is
   weight-deterministic on 0/1 carriers) plus a 400-sample refined-lens
   Monte Carlo.
4. **Dynamics + cross-entry battery** — snap dynamics by greedy syndrome
   descent; deep-hole ambiguity by complete decoding; and the KB's own 119
   `ELEM_*` carriers used as test data for the chemistry/materials claims
   (noble gases, binary anchor nodes, C-H divergence, tax slope).

### 2. Structural battery — exact results

| claim (law) | GLM recomputation | verdict |
|---|---|---|
| 759 magic octads (INT_RESONANCE, LOGIC_FUNCTIONAL) | weight distribution {0:1, 8:759, 12:2576, 16:759, 24:1}; Steiner S(5,8,24) confirmed (all 42 504 five-subsets covered exactly once) | exact |
| 56.76% tether at t=3 (GATEWAY_002) | 4096*(1+24+276+2024)/2^24 = 2325/4096 = 0.567628 | exact |
| 43.24% slack of the 24th bit (GOLAY_UNIQUENESS) | 1 - 2325/4096 = 1771/4096 = 0.432372 | exact |
| 6.8% byte-scale capture (GATEWAY_002) | even-weight tether = 277/4096 = 0.067627 | exact |
| 99.85% tether at t=3 (GATEWAY_001) | refuted — the number is 56.76% | **refuted** |
| G23 perfect code (GOLAY_UNIQUENESS) | 4096 x 2048 = 2^23 — perfect tiling | exact |
| 196 560 = 97 152 + 98 304 + 1 104 (KISSING_EXPANSION) | enumerated: (2^8)=97 152, (3,1^23)=98 304, (4,4)=1 104 | exact |
| d = 8 wall of isolation (RELATION_002) | minimum distance 8; inter-codeword spectrum {8,12,16,24} | exact |
| 759 octad slip (FORCE_004) | 1/759 verified | exact |
| deep hole = equidistant truths (FOURTH_FLIP) | every weight-4 coset has exactly **6** tied leaders | exact |
| Klein any-two-layers (SUBSTRATE_007) | 4 of 6 layer pairs injective; (0,2) and (1,3) fail | partial |
| 32D L24+E8, t=4 (QLH) | a 32D extremal rung exists (kissing 146 880) but Lambda(+)E8 has min 2; t=4 unsupported | partial |
| 68D saturation rung (SUBSTRATE_TENSION) | 68 = 4 (mod 8): even unimodular lattices cannot exist there | **refuted** |
| ARX basin 62.5 bits (ARX_HORIZON) | log2 of sum C(4096,<=6) = 62.505 | exact |
| tax = HW*Y + ||v||^2/8 (LEECH_TAX) | identical to `coherence.tax_shell0` | exact |

### 3. Numeric battery — physics targets (error < 3.5% shown; 47 tests total)

| law | formula | value | target | error |
|---|---|---|---|---|
| LAW_LEPTON_001 | (Y^-1)^4 + 3 - Y^4 | 206.76755240084483 | 206.768283 | 0.0004% |
| LAW_PHYSICS_MUON_002 | 169/w | 206.70754304276642 | 206.768283 | 0.0294% |
| LAW_BARYON_001 | 9*(Y^-1)^4 + (Y^-1 - 1) - Y | 1836.4656755136764 | 1836.15267343 | 0.017% |
| LAW_REF_INVARIANT_001 | 9(1/Y)^4 + (1/Y - 1) - Y | 1836.4656755136764 | 1836.15267343 | 0.017% |
| LAW_NUM_001 | (Y^-1)^2 + (Y^-1 - 1) - Y | 16.78842613121156 | 16.817 | 0.1699% |
| LAW_PARTICLE_RESONANCE_001 | 17*(Y_inv^4) + 2*Y_inv + Y | 3471.952917483219 | 3477.15 | 0.1495% |
| LAW_TAU_RESONANCE_001 | [17Y_inv^4+2Y_inv+Y]+[Y_inv*24/23+8Y] | 3478.0128034578893 | 3477.15 | 0.0248% |
| LAW_MECH_001 | Y^-5.65 (baryon fractional gear) | 1826.703251821396 | 1836.15267343 | 0.5146% |
| LAW_LEPTON_003 | Y^-4 (integer gear) | 203.77245983534706 | 206.768283 | 1.4489% |
| LAW_UBP_mtop | 25/2*U_e - 12Y + L (UBP code) | 172796.88678562184 | 172686.0 | 0.0642% |
| LAW_UBP_mhiggs | U_e*(9+L) (UBP code) | 125285.40223542214 | 125250.0 | 0.0283% |
| LAW_CABIBBO_MIXING_001 | (Y/(1+Y))*(24/23)+(Y/40) | 0.2249994455644717 | 0.2243 | 0.3118% |
| LAW_CABIBBO_ANGLE | arcsin above in degrees | 13.002845560124412 | 13.02 | 0.1318% |
| LAW_WEINBERG_RESONANCE_001 | Y/(1+phi/12) | 0.23322787764211503 | 0.23122 | 0.8684% |
| LAW_FORCE_003 | 21*Y_inv (W) | 79.34246094510486 | 80.377 | 1.2871% |
| LAW_FORCE_003b | 24*Y_inv (Z) | 90.677098222977 | 91.1876 | 0.5598% |
| LAW_FORCE_005 | Y_inv*(33+1/9) | 125.10081143725529 | 125.25 | 0.1191% |
| LAW_HIGGS_TENSION_001 | (1+Y*sqrt2)-(Y/120) [x m_Z] | 125.11868420607172 | 125.25 | 0.1048% |
| LAW_WEAK_ISOSPIN_001 | sqrt(1-sin2thW) on-shell | 0.8815327560561774 | 0.8814466001956406 | 0.0098% |
| LAW_FORCE_002 | (1/Y)^3 + 83 + 1.5*Y^2 | 137.0386431366994 | 137.035999 | 0.0019% |
| LAW_HORIZON_001 | 137 (integer anchor) | 137.0 | 137.035999 | 0.0263% |
| LAW_PHYSICS_001_REFINED_T=Ue | 64*((pi-1) - 8/13824) | 137.02489279270972 | 137.035999 | 0.0081% |
| LAW_PHYSICS_001_REFINED_T=9216 | 64*((pi-1) - 8/9216) | 137.00637427419122 | 137.035999 | 0.0216% |
| LAW_PHYSICS_GRAVITY_001 | (39/29)*(Y^18/w) | 6.683154991969466e-11 | 6.6743e-11 | 0.1327% |
| LAW_COSMOS_001_REFINED | 100*(1-Y)*(11/12) | 67.40475221291835 | 67.36 | 0.0664% |
| LAW_COSMO_002 | Y + Y_inv + sqrt(2) | 5.457101418734997 | 5.364 | 1.7357% |
| LAW_PROTON_GRAVITY_001 | m_p/sqrt(alpha_G) = M_Pl identity | 1.220895121189301 | 1.2209 | 0.0004% |
| LAW_TOP_KISSING_001 | 196560*sqrt3*(1-Y/24) | 336697.3544462667 | 337941.0 | 0.368% |
| LAW_PHYSICS_003_REFINED | 196560^8 * (Y_inv/2) | 4.2093740959344e+42 | 4.17e+42 | 1.0411% |
| LAW_NEUTRINO_SHADOW_001 | m_e(eV) * Y^12 | 0.0603925744776677 | 0.0604 | 0.0123% |
| LAW_NEUTRINO_003 | (1/6)*(1-Y)*(11/12) eV | 0.11234125368819727 | 0.1123 | 0.0367% |
| LAW_CHEM_002 | 83*(1+Y) - Y/2 - Y_inv/10 (water bond angle deg) | 104.45790176577773 | 104.45 | 0.0076% |
| LAW_ABSOLUTE_MASS_001 | 24*Y/(4*pi) (MeV) | 0.5054928367662648 | 0.510999 | 1.0775% |
| LAW_GEAR_G15_001 | U_e/(4*Y_inv*pi) (MeV) | 291.16387397736844 | 293.4 | 0.7621% |
| LAW_GEAR_G13_001 | 13/L = 169/w (muon-ratio scale) | 206.70754304276642 | 206.768 | 0.0292% |
| LAW_MESON_PION_001 | 1000*Y (pion0/m_e?) | 264.675430404527 | 264.153 | 0.1978% |
| LAW_GEAR_G13_001 | (Y_inv*L + Y/2)*(Y_inv - Y) (MeV) | 1.2998416794450607 | 1.29333 | 0.5035% |
| LAW_GEAR_G13b | 13/L = 169/w | 206.70754304276642 | 206.768 | 0.0292% |
| LAW_CKM_SHEAR_001 | Y^3/5 (V_ub) | 0.0037082660031785074 | 0.00368 | 0.7681% |
| LAW_CKM_SHEAR_001b | Y^2*(24/40) (V_cb) | 0.04203185007589297 | 0.041 | 2.5167% |
| LAW_MEASURE_003 | (2.4/196560)*sqrt(pi)*(1+Y/16) | 2.199968452407573e-05 | 2.2e-05 | 0.0014% |
| LAW_NOBLE_SCALING_001c | BP(Rn)*Y^(2/3) (Ar) | 87.18721199774626 | 87.3 | 0.129% |
| LAW_ISOTOPIC_FRICTION_001 | 2 - RG/24 | 1.9824845206203914 | 1.99785 | 0.7691% |

Misses worth recording: noble-gas scalings hit argon to 0.13% but miss
helium/neon by 6-7% (NOBLE_SCALING -> partial); the Lambda formula lands at
10^-121.78 — the right order of magnitude, not a precision result; alpha^-1
from shell capacities depends on reading T = U_e (0.008%).

### 4. NRCI regime battery — the noise-floor refutation

NRCI is weight-deterministic on 0/1 carriers: NRCI(w) = 10/(10 + w(Y+1/8)).

| quantity | GLM exact value |
|---|---|
| vacuum (w=0) | 1.0 |
| octad (w=8) | 0.762346 |
| dodecad (w=12) | 0.681380 |
| weight-24 (minimum over ALL vectors) | **0.516737** |
| mean over the 4096 codewords | 0.684298 |
| mean over random vectors (exact binomial) | 0.684298 |
| refined 5-shell lens, random (min..max) | 0.555 .. 0.825 |

Consequences: **the claimed 0.42 noise floor (ANOMALY_001) is unreachable by
any 24-bit vector** — the minimum possible is 0.5167; the claimed 0.4769
"vacuum resonance mean" (MATH_OPERATIONAL_001) is likewise not any substrate
statistic (both means are 0.6843). The 0.60 anomaly threshold itself behaves
as claimed as a detector rule (1.1% false-positive rate on pure noise). The
0.94 self-healing threshold (MAT_HEAL) is reachable only by w <= 1 vectors —
coherent as a near-vacuum trigger, impossible as a system mean.

### 5. Dynamics + cross-entry findings

- **Snap dynamics verified:** greedy syndrome descent converges to a codeword
  in *exactly* d steps from distance d = 1..4 (200 trials each, always
  minimum-length). COMP_005's "1-bit correction", COMP_006's t=3 relock and
  PATH_LEAST_ACTION's minimal NRCI trajectory are all literally true of the
  decoder. The "restorative force" of FIELD_TOPOLOGY / CONTINUOUS_LIMIT /
  GRAVITY *is* the decoder — retained as a levelled structural analogy.
- **All 119 ELEM carriers are perfect zero-syndrome codewords.** This
  verifies CHEM_NOBLE (all 6 noble gases), CHEM_006 (binary nodes Z = 8, 16,
  32, 64 all codewords) and CHEM_PERIODIC — but **refutes MASK_001 and
  BITTAB_V1**, whose "matter is a noisy projection / S>3 excited state"
  doctrine contradicts the KB's own element data (every syndrome is 0).
- **C-H divergence is 8 bits, not 16** (MAT_ATOMIC, as Hamming distance; only
  the "16 positions not shared by both octads" reading rescues the number).
- **4.6761 = 12(Y+1/8)** — the dodecad tax, exactly (GEOMETRIC_BONDING).
  The "systemic mean at Gd_064" is the binary midpoint of the 1-127 container,
  itself a zero-syndrome octad.
- Element tax slope vs Z measured 0.00590 against VORTEX's claimed 0.0056
  (5% off).

### 6. Verdicts — 426 laws

| verdict | count | meaning |
|---|---|---|
| RETAINED-EXACT | 16 | reproduces exactly under GLM recomputation |
| RETAINED-NUM | 49 | formula verified within claimed precision vs physics target |
| RETAINED-STRUCT | 40 | verified against code / lattice / the KB's own data |
| RETAINED-FACT | 4 | real mathematics/physics, correctly used |
| RETAINED-DEF | 142 | definition/protocol/identity — internally consistent axiom |
| LEVELED | 17 | metaphor re-expressed at GLM resolution; precise form holds |
| **retained total** | **268** | **62.9% of the register** |
| PARTIAL | 24 | some components verified, others failed |
| REFUTED | 10 | GLM computation or the KB's own data contradicts |
| UNRESOLVED-UBP | 106 | lives in a UBP pipeline GLM does not implement (declared gap) |
| EMPTY | 18 | finding text is "No definition" |

#### The refuted (10)

| law | evidence |
|---|---|
| LAW_ANOMALY_001 | claimed noise-floor NRCI 0.42 is unreachable: the minimum shell-0 NRCI over ALL 24-bit vectors is 0.5167 (W24); random mean = 0.6843; refined-lens minimum 0.555. The 0.60 anomaly threshold does function as a detector rule (1.1% fa |
| LAW_BIO_HEMA_002 | 'all blood types occupy Leech Shell 1 (Norm 12)': the Leech lattice has no norm-12 shell (norms are 32,48,64,80,... in the integer model); 'Norm 12' is the dodecad Hamming weight, not a Leech norm. As a Leech-lattice claim it is f |
| LAW_BIO_MANA_SIM_001 | '0.333 NRCI for stable glyphs': NRCI 0.333 is unreachable for any 24-bit vector (minimum 0.5167 shell-0, 0.555 refined); the KB itself flags simulation-only |
| LAW_BITTAB_V1 | 'high syndrome weights (S>3) for physical matter': all 119 ELEM carriers have syndrome weight exactly 0 in the KB |
| LAW_COSMO_005 | '1-bit anchor reconstructs the 12-bit seed beyond the Hamming bound': unique decoding is impossible beyond t=3 (GLM: weight-4 cosets have 6 tied leaders); 1 bit of the 24 leaves 2^11 consistent codewords |
| LAW_GATEWAY_001 | claims 99.85% of states tethered at t=3; exact GLM value is 56.76% (2325/4096). Its sibling GATEWAY_002 carries the correct number |
| LAW_MASK_001 | 'no physical phenomenon is a perfect codeword / matter is a noisy projection': the KB's own data contradicts it — all 119 ELEM carriers are exact zero-syndrome codewords |
| LAW_MATH_OPERATIONAL_001 | '0.4769 mean = native resonance of the Golay vacuum': mean NRCI over the 4096 codewords is 0.6843 (and over random vectors also 0.6843); no substrate statistic equals 0.4769. (As a constants-study score it is UBP-side) |
| LAW_SUBSTRATE_TENSION_001 | claims an n=4 rung at 68D: even unimodular lattices exist only in dimensions divisible by 8 (68 = 4 mod 8 is impossible); the GLM ladder is 8-24-32-48; the 2n^2+10n-4 dimension formula produces non-lattice dimensions |
| LAW_ELEMENTAL_SHELLS_001 | claims Leech shells carry 128 / 2048 / 32768 orientations: the actual Leech shell counts are 196,560 (norm 32) / 16,773,120 (norm 48) / 398,034,000 (norm 64). The 2^7/2^11/2^15 pattern matches no Leech shell |

#### The partial (24)

| law | evidence |
|---|---|
| LAW_BITLUMEN_001 | photon payload split 3b+4b+2b+2b = 11 bits inside a claimed 12-bit message — one bit unaccounted; as an encoding spec it is coherent modulo that gap |
| LAW_COSMO_002 | Y+Y_inv+sqrt(2) = 5.4571 vs Omega_dm/Omega_b = 5.364 -> 1.7% |
| LAW_GEOMETRY_EUCLIDEAN_001 | 'substrate naturally achieves 0.999' is wrong: max non-vacuum NRCI is 0.8651 (W4); the law's own point that NRCI 1.0 needs observer intent is consistent (only vacuum = 1.0) |
| LAW_GHOST_HEALING_001 | d>=4 ambiguity is real (GLM: every weight-4 coset has exactly 6 tied leaders — 'multiple ghost truths' verified); the selection/healing mechanism is UBP-side |
| LAW_HORIZON_003 | vacuum OnBit NRCI 1.0 verified; 1 THz wall is UBP-side |
| LAW_INFORMATIONAL_SATURATION_001 | tax at W16 = 16Y+2 = 6.2348 exact (matches KB); but 'collapse at H=16' is contradicted: 759 weight-16 codewords exist and 77 KB laws carry W16 codewords |
| LAW_LEPTON_002 | integer powers of Y_inv: muon Y^-4 = 203.77 -> 1.45% (the refined LEPTON_001 form is 0.0004%) |
| LAW_LEPTON_003 | phase-rotation reading; Y^-4 -> 1.45% for muon |
| LAW_MAT_ATOMIC_001 | 'C and H diverge by 16 bits': KB vectors give Hamming distance 8 (not 16); only the reading '16 of 24 positions not shared by both octads' (24-8) rescues the number |
| LAW_MAT_HEAL_001 | 0.94 threshold is reachable only by W<=1 vectors (P=1.5e-6 on random); as a global system mean it is impossible (mean 0.684) — coherent only as a near-vacuum trigger |
| LAW_ONTOLOGICAL_FRICTION_001 | Y/96 = 0.00275704 exact; but claimed 'Shaving' 0.06902502 != Y^2 = 0.070053 (1.5% off) — declared-value defect |
| LAW_PERIODIC_SINGULARITY | H and O are both zero-syndrome codewords in the KB (verified); 'syndrome collision invisible to Rune quantification' is UBP-side |
| LAW_QUANTUM_SNAP_001 | snap to nearest anchor verified for dH<=3; at dH=4 the snap target is 6-way ambiguous, so 'forced snap' is not well-defined exactly where the claim applies it |
| LAW_SUBSTRATE_007 | 'any two layers reconstruct the third': 4 of 6 layer pairs are injective on the code; the opposite pairs (0,2) and (1,3) are not — Klein closure holds only for adjacent pairs |
| LAW_UNITY_005 | the components it cites are verified (muon 0.0004%, proton 0.017%, alpha 0.002-0.03%); 'finalized TOE reconciling GR and QM' overstates what was checked |
| LAW_VORTEX_DYNAMICS_001 | tax 3.1174 = 8Y+1 exact; measured KB element tax slope 0.00590 vs claimed 0.0056 (5% off); 2048-bit reset prediction untestable |
| LAW_ALPHA_LAMBDA_HORIZON_001 | (Y/U_e)^24 * alpha^4 = 10^-121.78 vs observed ~10^-122: correct order of magnitude (0.22 dex), not a precision derivation |
| LAW_STATISTICAL_CLOSURE_001 | the Lambda formula it cites is order-of-magnitude correct (10^-121.78); 'definitive proof of the UBP' is not a testable claim |
| LAW_MONSTROUS_MOONSHINE_001 | 196884/196883 ratio exact (j-function dim V_2 = 196884 is real moonshine); neutron-lifetime resolution requires an undeclared 'Corr' factor |
| LAW_BORCHERDS_TAUTOLOGY_001 | 26D Lorentzian lifting is genuine Borcherds mathematics; the wobble-reciprocal identity (1.0000 closure) could not be reconstructed from the tensor fragment |
| LAW_ABSOLUTE_MASS_001 | 24Y/(4pi) = 0.505493 matches KB value exactly, but vs m_e = 0.511 MeV it is 1.08% off |
| LAW_AQUEOUS_AFFINITY_001 | step ratios 1.678/1.597 vs phi = 1.618 (1.9-4.6% off): Fibonacci-scaled only approximately |
| LAW_QLH_LATTICE_001 | a 32D extremal rung does exist (GLM builds it, kissing 146880); but Lambda(+)E8 as a direct sum has minimum 2 (E8 short vectors dominate), and the t=4 radius claim is unsupported in the binary-code sense |
| LAW_PHYSICS_BARKER_001 | 2646/10000 = Y at 4 digits; Barker field physics UBP-side |

### 7. Retained list — the 268 laws that pass

Grouped by verdict class. RETAINED-DEF entries are retained as internally
consistent axioms/specifications of the UBP formalism — they pass a
consistency bar, not an empirical one; the other five classes passed actual
GLM computation.

Machine-readable companion — **`retained_laws_round2.csv`** (268 rows, one
per passing law). Columns: `ubp_id`, `title`, `verdict`, `pass_bar` (what
class of pass), `statement` (the full finding text as shipped in the KB
lexicon), `math_payload` (the mog_tensor formulas, `|`-joined),
`glm_test_and_result` (the GLM test applied and its outcome),
`carrier_round1` (Round-1 Golay carrier facts), `refined_nrci_5shell`,
`kb_hash16` (disambiguates the duplicated `LAW_BOND_TAXONOMY_001` id).
266/268 rows carry a mog_tensor formula; the two that do not
(`LAW_GRAVITY_RESONANCE_001`, `LAW_FORCE_004`) state their math in the
finding text itself. Rows are sorted by pass strength: EXACT > NUM >
STRUCT > FACT > LEVELED > DEF.


#### RETAINED-EXACT (16)
| LAW_ARX_HORIZON_006                | LAW_COMP_005                       | LAW_COMP_009                       | LAW_FOURTH_FLIP_001                |
| LAW_GATEWAY_002                    | LAW_GOLAY_UNIQUENESS_001           | LAW_INTERFACE_CLOSURE_001          | LAW_KISSING_EXPANSION_001          |
| LAW_LEECH_TAX_001                  | LAW_LEECH_TENSION_001              | LAW_LOGIC_GEO_001                  | LAW_METRIC_002                     |
| LAW_PATH_LEAST_ACTION              | LAW_RELATION_002                   | LAW_RELATION_ORTHO_001             | LAW_RESOLUTION_GAP_001             |

#### RETAINED-NUM (49)
| LAW_BARYON_001                     | LAW_BERRY_PHASE_RESONANCE_001      | LAW_BIO_GOLD_001                   | LAW_BIO_GOLD_002                   |
| LAW_CABIBBO_MIXING_001             | LAW_CHEM_002                       | LAW_CKM_SHEAR_001                  | LAW_COSMOS_001_REFINED             |
| LAW_FIELD_CARFE_001                | LAW_FORCE_002                      | LAW_FORCE_003                      | LAW_FORCE_005                      |
| LAW_GEAR_G13_001                   | LAW_GEAR_G15_001                   | LAW_GEO_002                        | LAW_GRAVITY_RESONANCE_001          |
| LAW_HIGGS_TENSION_001              | LAW_HORIZON_001                    | LAW_HORIZON_002                    | LAW_ISOTOPIC_FRICTION_001          |
| LAW_LEPTON_001                     | LAW_MAT_STEEL_001                  | LAW_MEASURE_003                    | LAW_MECH_001                       |
| LAW_MESON_PION_001                 | LAW_MINERAL_001                    | LAW_NEUTRINO_003                   | LAW_NEUTRINO_SHADOW_001            |
| LAW_NOBLE_SCALING_001              | LAW_NSC_THUNDER_001                | LAW_NUM_001                        | LAW_NUM_COLLATZ_002                |
| LAW_PARTICLE_RESONANCE_001         | LAW_PHASE_RESONANCE_001            | LAW_PHYSICS_001_REFINED            | LAW_PHYSICS_003_REFINED            |
| LAW_PHYSICS_GRAVITY_001            | LAW_PHYSICS_MAXWELL_003            | LAW_PHYSICS_MUON_002               | LAW_PROJECTION_DOT_001             |
| LAW_QUANTUM_PROB_002               | LAW_REF_INVARIANT_001              | LAW_STORAGE_HARDENED_001           | LAW_TAU_RESONANCE_001              |
| LAW_TERRESTRIAL_GRID_001           | LAW_TOP_KISSING_001                | LAW_VTE_QUANTIZATION_001           | LAW_WEAK_ISOSPIN_001               |
| LAW_WEINBERG_RESONANCE_001         |                                    |                                    |                                    |

#### RETAINED-STRUCT (40)
| LAW_APP_001                        | LAW_APP_002                        | LAW_BIO_008_VERIFIED               | LAW_BIO_REPELLENT_001              |
| LAW_BITLUMEN_002                   | LAW_BOND_TAXONOMY_001              | LAW_BOND_TAXONOMY_001              | LAW_CARRIER_SHIELDING_001          |
| LAW_CATEGORY_FUNCTOR_001           | LAW_CHEM_006                       | LAW_CHEM_NOBLE_001                 | LAW_CHEM_PERIODIC_001              |
| LAW_CHEM_PHASE_001                 | LAW_COMP_006                       | LAW_COMP_REFLEX_001                | LAW_COMP_VERIFY_001                |
| LAW_COSMO_RFC_001                  | LAW_FORCE_004                      | LAW_GCE_003                        | LAW_GEOMETRIC_BONDING_001          |
| LAW_GEO_FOLD_001                   | LAW_GEO_SEAM_001                   | LAW_GEO_SEAM_002                   | LAW_INT_RESONANCE_001              |
| LAW_KERNEL_DIMENSION_001           | LAW_KERNEL_THRESHOLDS_001          | LAW_LOGIC_FUNCTIONAL_001           | LAW_ONTOLOGY_001                   |
| LAW_PAC_CONSTRUCTION_001           | LAW_PLATONIC_002                   | LAW_PROTO_INF_001                  | LAW_SEMANTIC_RESONANCE_001         |
| LAW_STABILITY_SINK_001             | LAW_SUBSTRATE_001                  | LAW_SUBSTRATE_002                  | LAW_SUBSTRATE_005                  |
| LAW_SYNTH_001                      | LAW_TOPOLOGICAL_FOLD_001           | LAW_TOPOLOGICAL_MULTIPLIERS_001    | LAW_ZONE_001                       |

#### RETAINED-FACT (4)
| LAW_ATOM_HOLOGRAPHIC               | LAW_OMEGA_ASYMMETRY_001            | LAW_PROTON_GRAVITY_001             | LAW_RAINBOW_001                    |

#### LEVELED (17)
| LAW_BARYON_PROTON_001              | LAW_BIO_004                        | LAW_BIO_ANCHOR_001                 | LAW_BIO_METABOLISM_001             |
| LAW_CHEM_KINETICS_001              | LAW_CLASSICAL_BRIDGE_001           | LAW_COMP_002                       | LAW_CONTINUOUS_LIMIT_001           |
| LAW_COSMO_006                      | LAW_DISCRETE_RENORM_001            | LAW_FIELD_TOPOLOGY_001             | LAW_GRAVITY_001                    |
| LAW_INTERFERENCE_SHIELD_001        | LAW_MIND_001                       | LAW_PHYSICS_NEUTRINO_001           | LAW_PHYSICS_STRONG_SNAP_001        |
| LAW_TIME_PULSE_001                 |                                    |                                    |                                    |

#### RETAINED-DEF (142)
| LAW_6D_TENSOR_001                            | LAW_ACOUSTIC_MAPPING_001                     | LAW_BIO_006                                  |
| LAW_BIO_008                                  | LAW_BIO_QUANTUM_001                          | LAW_BIO_REPELLENT_002                        |
| LAW_BRIDGE_CONTRACT_001                      | LAW_BUOYANCY_001                             | LAW_CHEM_003                                 |
| LAW_CHEM_004                                 | LAW_CHEM_ENCODING_V1                         | LAW_CHEM_METHANE_001                         |
| LAW_CHROMO_GEOMETRIC_DUALISM_001             | LAW_CLOSURE_001                              | LAW_COHERENCE_GCI_001                        |
| LAW_COMPLEX_EML_001                          | LAW_COMP_001                                 | LAW_COMP_004                                 |
| LAW_COMP_007                                 | LAW_COMP_010                                 | LAW_COMP_011                                 |
| LAW_COMP_013                                 | LAW_CONST_002                                | LAW_CORTEX_ROUTER_001                        |
| LAW_COSMOS_002                               | LAW_COSMOS_003                               | LAW_COSMO_004                                |
| LAW_COSMO_008                                | LAW_DQI_METRIC_001                           | LAW_DRUG_008                                 |
| LAW_DRUG_009                                 | LAW_ELEMENT_ARCHITECTURE_001                 | LAW_EM_TOGGLE_001                            |
| LAW_ENERGY_SOC_001                           | LAW_ENERGY_SOC_002                           | LAW_ENG_HOLOGRAPHIC_001                      |
| LAW_ENG_SWITCH_001                           | LAW_ENG_TRIADIC_LOCK_001                     | LAW_ENTROPIC_CAPTURE_001                     |
| LAW_ENTROPIC_COMBUSTION_001                  | LAW_FLUX_001                                 | LAW_FRACTAL_001                              |
| LAW_FULCRUM_001                              | LAW_GEOMETRIC_LEVERAGE_001                   | LAW_GEOMETRIC_NRCI                           |
| LAW_GEOMETRY_RGDL_001                        | LAW_GEO_001                                  | LAW_GEO_432_FCC                              |
| LAW_GEO_FAMILY_001                           | LAW_GPGPU_INTEGRITY_001                      | LAW_HEMA_001                                 |
| LAW_HGR_001                                  | LAW_HGR_RESONANCE_001                        | LAW_INFO_DEPTH_001                           |
| LAW_INFO_OID                                 | LAW_INFO_SET_001                             | LAW_INTERACTION_RATIONAL                     |
| LAW_INTERFACE_ADDRESS_001                    | LAW_INTERFACE_MAP_001                        | LAW_INTERFACE_VISUAL_001                     |
| LAW_KERNEL_V2_1_1                            | LAW_KERNEL_V2_1_MOG                          | LAW_KERNEL_V2_FINAL                          |
| LAW_LANG_006                                 | LAW_LANG_007                                 | LAW_LANG_008                                 |
| LAW_LANG_009                                 | LAW_LANG_RECIPE_001                          | LAW_LOGIC_RECIP_001                          |
| LAW_MATH_OPERATIONAL_002                     | LAW_MATH_PHIP_PI                             | LAW_MATH_REGIMES_001                         |
| LAW_MATH_REVERSIBILITY_001                   | LAW_MATH_SEVEN_001                           | LAW_MATH_TRIADIC_SUM                         |
| LAW_META_002                                 | LAW_META_GENESIS_001                         | LAW_MOG_13_LOCK                              |
| LAW_NUM_COLLATZ_001                          | LAW_OBSERVER_OOB_001                         | LAW_OPCODE_DREAM_MIN                         |
| LAW_OPCODE_FOCUS_MIN                         | LAW_OPCODE_GAVEL_MIN                         | LAW_OPCODE_PILOT_MIN                         |
| LAW_OPTICAL_TOGGLE_001                       | LAW_PANTOGRAPH_THERMODYNAMICS_001            | LAW_PATTERN_001                              |
| LAW_PHYSICS_002                              | LAW_PHYSICS_ENERGY_CONVERSION_001            | LAW_PHYSICS_ENERGY_CONVERSION_002            |
| LAW_PHYSICS_HELICITY_002                     | LAW_PHYSICS_MAXWELL_002                      | LAW_PLATONIC_001                             |
| LAW_PLATONIC_003                             | LAW_PRIMITIVE_001                            | LAW_PROTO_001                                |
| LAW_QUANTUM_COLLAPSE_001                     | LAW_REFLEX_001                               | LAW_REFLEX_002                               |
| LAW_RELATIONAL_DECAY_001                     | LAW_RELATIONAL_FREQUENCY_001                 | LAW_RELATION_001                             |
| LAW_RELATIVITY_001                           | LAW_RELATIVITY_002                           | LAW_RGB_XYZ_001                              |
| LAW_SEMANTIC_CHORD_001                       | LAW_SEMANTIC_STACK_001                       | LAW_STEREOSCOPIC_AUDIT_001                   |
| LAW_STORAGE_003                              | LAW_STORAGE_CRYSTAL_001                      | LAW_STORAGE_CRYSTAL_002                      |
| LAW_STRUCT_001                               | LAW_SUBSTRATE_006                            | LAW_SUBSTRATE_010                            |
| LAW_SYMBOLIC_GROUNDING_001                   | LAW_SYMBOL_002                               | LAW_SYMMETRY_001                             |
| LAW_SYNTHESIS_002                            | LAW_SYSTEM_001                               | LAW_SYSTEM_INTEGRATED_V1                     |
| LAW_SYSTEM_KB_SOP_002                        | LAW_TEMP_MOMENTUM                            | LAW_TENSION_001                              |
| LAW_TETHER_001                               | LAW_TGIC_369_GENESIS                         | LAW_TGIC_ROUTING                             |
| LAW_TIME_001                                 | LAW_TIME_002                                 | LAW_TIME_003                                 |
| LAW_TIME_CYCLE_001                           | LAW_TIME_RUNE_001                            | LAW_TOE_VERIFICATION_001                     |
| LAW_TOGGLE_ADVANCED                          | LAW_TOPOLOGICAL_TORQUE_001                   | LAW_TOPOLOGY_001                             |
| LAW_TOPOLOGY_003                             | LAW_TOTAL_EXPERIENCED_RESULT_001             | LAW_TRIAD_001                                |
| LAW_UNIFIED_FIELD_001                        | LAW_UNITY_002                                | LAW_UNIT_001                                 |
| LAW_VECTOR_HARNESS_001                       |                                              |                                              |

### 8. Defects and data-quality notes (new in Round 2)

1. **18 LAW entries ship "No definition"** as their entire finding
   (LAW_CHEM_ACTIVATION, LAW_CHEM_CONSERVATION_MASS, LAW_CHEM_EQUILIBRIUM,
   LAW_CHEM_REDOX, LAW_COHERENCE_GLOBAL_001, LAW_ELECTRON_RESONANCE_001,
   LAW_ENERGY_UBP_001, LAW_HTR_SPATIAL_001, LAW_JUNIOR_LNC_001,
   LAW_LATTICE_NATIVE_CONTROL_001, LAW_NI_LATTICE_001,
   LAW_QUADRATIC_ENTHALPY_001, LAW_RESONANT_PINCH_001,
   LAW_SPECTRAL_RESOLUTION_001, LAW_SUPERCONDUCTING_DIPOLE_001,
   LAW_TEMPORAL_RECURRENCE_001, LAW_UNIVERSAL_COMPASS_001, LAW_ZFR_BUFFER_001).
   Most still carry vectors and tensors — the content was never written.
2. **Internal contradiction:** GATEWAY_001 (99.85%) vs GATEWAY_002 (56.76%)
   state the same statistic; only 002 is correct. DRUG_002/004 and
   MINERAL_002/003 are verbatim duplicates.
3. **Declared-value drift:** ONTOLOGICAL_FRICTION's "Shaving" 0.06902502 does
   not equal its stated definition Y^2 = 0.070053 (1.5% off). The KB's wobble
   constant (PANTOGRAPH 1.81758023) drifts 6.5e-5 from frac(pi*phi*e) = 0.817645.
4. **Doctrine vs data:** "matter is a noisy projection" (MASK, BITTAB_V1) is
   contradicted by the KB's own 119 zero-syndrome element carriers.
5. **Two-tier quality pattern persists at content level:** the physics
   formulas (lepton ratios, alpha^-1, H0, G, weak sector) are mostly sub-1%
   accurate with zero fitted constants, while several *substrate statistics*
   quoted in prose (0.42 noise floor, 0.4769 vacuum mean, 54.56% Hawking bias,
   128/2048/32768 shell counts) match no quantity GLM can compute.

### 9. Round 3 candidates

- Griess-metric clustering of the 411 codeword carriers (carried over).
- The 106 UNRESOLVED-UBP laws: re-test through UBP's own pipelines
  (NoiseALU, 256D bulk) where they exist, and record which survive.
- 24-bit -> 15-bit squeeze (LAW_SQUEEZE): attempt a GLM-side reconstruction.
- V_n = 204.801744 (TRIADIC_GENESIS): no closed form found in the declared
  constant set (pi, phi, e, Y, w, L, U_e) — request the derivation from the
  UBP side.

---

## Round 3 — 2026-09-28 · Griess clustering of the 411 codeword carriers

### 1. Method — the Griess instruments, GLM-native

GLM's declared pipeline is `Golay → Leech lattice → Λ/2Λ (Monster index
space) → Griess algebra → moonshine` (`substrate/leech2.py`,
`reasoning/moonshine.py`). Round 3 clusters the carriers on that ladder with
the exact instruments GLM already implements:

- the **canonical Leech lift** of a codeword `c` with support `S`:
  `x = 2·χ_S` (all-plus sign pattern; membership verified entry by entry —
  the support is a codeword and `Σx = 2w ≡ 0 (mod 8)` for w ∈ {8, 12, 16});
- the **class map** `Λ → Λ/2Λ` with the F₂ forms `q(λ) = λ·λ/16`,
  `B(λ, μ) = λ·μ/8`;
- the **98,280 type-2 classes** (2A axes), exhaustively enumerated
  from the 196,560 minimal vectors (each class hit by exactly ±v);
- the **Co0 pair invariant** `|v·w|/8` on 2A axes — values {4, 2, 1, 0}.

Scope note: GLM implements the Griess layer's *index space* (axes, classes,
shells), not the non-associative algebra product — so "Griess clustering"
here means the geometry of that index space, which is what the 411 carriers
live in.

### 2. The lift ladder — shells, fibers, class types

All 411 canonical lifts are Leech points (verified). They occupy exactly the
first three non-zero shells and the three non-zero class types:

| HW | n | Leech shell (×√8 model) | lift fiber | Λ/2Λ class type |
|---|---|---|---|---|
| 0 | 1 | 0 (origin) | 1 | zero class |
| 8 | 78 | 32 — the minimal vectors | 128 | type 2 — **2A axes** |
| 12 | 255 | 48 — second shell | 2,048 | type 3 — nonsingular (q = 1) |
| 16 | 77 | 64 — third shell | 32,768 | type 4 — frame classes |

**Levelled up.** `LAW_BOND_TAXONOMY_001` ("Octads are anchors, Dodecas are
dynamic, Hexadecas are complex") is exactly the type-2/3/4 trichotomy of the
Monster index space: anchors = 2A axes (minimal vectors — the Griess
algebra's middle piece), dynamic = non-singular classes, complex = frame
classes. The taxonomy survives translation with its structure intact.

**Rehabilitated.** `LAW_ELEMENTAL_SHELLS_001`'s "Shell 2 (Norm 32, 128
orientations), Shell 3 (Norm 48, 2048), Shell 4 (Norm 64, 32768)" was refuted
in Round 2 as shell *totals* (196,560 / 16,773,120 / 398,034,000). Round 3
finds the exact object those numbers count: the **lift fiber of a single
codeword** — the 2^(w−1) sign patterns of the (±2^w) Leech vectors above one
codeword, enumerated here as 128 / 2,048 / 32,768. The numbers are real Leech
quantities at per-codeword resolution — a lower-resolution projection, as
hypothesised. The one factual miss: **Carbon's carrier is a dodecad (HW 12)
→ Shell 3 with 2,048 orientations, not Shell 4 with 32,768.** The actual
Shell-4 elements are Ce (58), W (74), Pb (82), Po (84). Verdict: REFUTED →
**PARTIAL (levelled)**.

### 3. The 2A axes — four mutual positions

All 78 octad carriers are 2A axes. Their pair-invariant census:

| invariant \|v·w\|/8 | 4 (same axis) | 2 | 1 | 0 |
|---|---|---|---|---|
| pairs | 2 | 1092 | 1802 | 107 |

`|v·w|/8 = |S_A ∩ S_B|/2`, so the octad intersection numbers {0, 2, 4, 8}
*are* the four Monster 2A mutual positions {0, 1, 2, 4}. The classical
single-axis distribution {4: 2, 2: 9200, 1: 94208, 0: 93150} reproduces
exactly (validates the enumeration). The two invariant-4 pairs are twin
carriers (§8).

### 4. Fingerprints — every carrier is orbit-generic

Inner products of each carrier lift against all 196,560 minimal vectors,
constant within each type (verified carrier by carrier):

| type | fingerprint (inner → count) |
|---|---|
| type 2 | ±32: 1, ±16: 4,600, ±8: 47,104, 0: 93,150 |
| type 3 | ±24: 552, ±16: 11,178, ±8: 48,600, 0: 75,900 |
| type 4 | ±32: 46, ±24: 2,048, ±16: 16,192, ±8: 47,104, 0: 65,780 |

No carrier occupies a special position in the Griess geometry — each sits in
its class as a generic point of its Co0 orbit.

### 5. Structured or random? — Monte-Carlo (2,000 draws)

z-scores of the intersection censuses against random draws from the code
pools (759 octads / 2,576 dodecads / 759 w16):

| pool | \|S∩S\| | observed | random | z |
|---|---|---|---|---|
| octads, 78 of 759 | 0 | 107 | 118.9 ± 9.8 | -1.22 |
|  | 2 | 1802 | 1775.3 ± 24.1 | 1.11 |
|  | 4 | 1092 | 1108.8 ± 23.5 | -0.72 |
| dodecads, 255 of 2,576 | 0 | 14 | 12.5 ± 3.2 | 0.46 |
|  | 4 | 6237 | 6225.6 ± 65.2 | 0.17 |
|  | 6 | 19930 | 19921.3 ± 79.8 | 0.11 |
|  | 8 | 6192 | 6225.6 ± 63.7 | -0.53 |
| w16, 77 of 759 | 8 | 102 | 115.7 ± 9.7 | -1.42 |
|  | 10 | 1710 | 1729.6 ± 23.5 | -0.83 |
|  | 12 | 1112 | 1080.7 ± 23.3 | 1.35 |

Everything is within ±1.5 σ: **the carrier minting is geometrically
unstructured — a uniform random sample of the code.** Deviations appear only
at \|S∩S\| = max, which is the twin-carrier artefact (§8). Complement
closure: 10 octad→w16 pairs (expected 7.9);
13 dodecad complement pairs (expected 11.5);
6 complete trios of 107 disjoint octad pairs (expected
11.0). All within noise. There are no hidden Griess families in the KB's
carrier set.

### 6. Clustering

- **d ≤ 8 (Golay adjacency):** 96 average-linkage clusters, sizes
  1–8; the d = 8 graph is a single connected
  component; per-carrier degrees 54–97
  (mean 75.94).
- **d ≤ 12:** 7 clusters of 33–86 members, mixed by HW class,
  first-seen cohort and Round-2 verdict — no semantic structure.
- **d ≤ 16:** one component.

### 7. The moonshine ledger (every line recomputed)

- j(q) − 744 = q⁻¹ + 196884q + 21493760q² + …: the exact E₄³/Δ computation
  matches the tabulated graded dimensions — dim V₂ = 196,884 (the Griess
  algebra), dim V₃ = 21,493,760.
- 196,883 = 47 · 59 · 71 (the Monster's smallest faithful rep).
- Co1 module split: 196,884 = 1 + 299 + 98,280 + 98,304, with the 98,280
  type-2 axes computed here from the 196,560 minimal vectors, and
  98,304 = 24 × 4,096 (coordinates × cocode).
- Leech theta (E₄³ − 720Δ): 1, 0, 196,560, 16,773,120, 398,034,000, …;
  class census closes: 1 + 98,280 + 8,386,560 + 8,292,375 = 2²⁴.
- 196,560 = 1,104 (axes) + 97,152 (octads) + 98,304 (frames), enumerated.
- 398,034,000 / 48 = 8,292,375 type-4 classes (frames of 48).

`LAW_MONSTROUS_MOONSHINE_001`'s ratio 196884/196883 is genuine moonshine
arithmetic with both numbers verified in role; the neutron-lifetime
application still needs the undeclared "Corr" factor — verdict stays
PARTIAL, on a strengthened base. `LAW_KISSING_EXPANSION_001`'s
4,096 → 196,560 expansion is confirmed one level higher: the codewords'
canonical lifts generate the full type-2/3/4 trichotomy of Λ/2Λ.

### 8. Defect — twinned carriers

29 of 411 entries (7.1%) share their vector with another
entry — 396 distinct masks among 411 rows (13 pairs + 1 triple), e.g.
LAW_FORCE_002 / LAW_LOGIC_RECIP_001, LAW_BIO_HEMA_003 / LAW_GOLAY_UNIQUENESS_001,
LAW_MATH_SEVEN_001 / LAW_MATH_TRIADIC_SUM / LAW_MAT_ATOMIC_001. Distinct laws
are minted on identical Griess positions; the two "same-axis" pairs of §3
are twins.

### 9. Elements across the shells (ELEMENTAL_SHELLS cross-check)

All 119 element carriers are codewords (Round 2) and they do distribute
across the three shells: 50 in Shell 2 (HW 8: H, He, Li, B, N, F, Ne,
Na, Mg, Si, P, S, …), 65 in Shell 3 (HW 12, including Carbon), 4 in
Shell 4 (HW 16: Ce, W, Pb, Po). The distribution is real; the law's Carbon
sentence attributes the wrong shell to the wrong element.

### 10. Round 4 candidates

- The 106 UNRESOLVED-UBP laws through UBP's own pipelines (carried).
- LAW_SQUEEZE 24 → 15-bit squeeze, GLM-side reconstruction (carried).
- V_n = 204.801744 derivation request (carried; the moonshine ledger above
  is the context it would land in).
- Griess product structure: GLM has the 2A axes but no algebra product;
  implementing the e_f ∘ e_g structure constants would let "axis algebra"
  claims be tested directly.

Machine-readable companions: `griess_clustering_round3.csv` (411 rows × 14
columns — per-carrier shell, class type, 2A status, lift fiber, Golay
adjacency, cluster labels at d ≤ 8 and d ≤ 12, twin group, cohort, verdict)
and `griess_clustering_round3.png` (MDS embedding, class types colored,
twins linked).

---

*Append future rounds below this line.*
