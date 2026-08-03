# DATABASE TIDY-UP DIRECTIVE
Every item below is a confirmed finding from this session — verified by
executing real code against the real repo, not inferred. Ordered by impact.

═══════════════════════════════════════════════════════════════════════
PRIORITY 1 — FIX BEFORE ANYTHING ELSE (actively destroying/losing data)
═══════════════════════════════════════════════════════════════════════

### 1.1 Stop using quadrant-forcing in vector construction
**Confirmed:** GLM23's production method (force top-3-of-6 bits into one
"dominant" quadrant, zero most of the other 18 by percentile) destroys
real semantic signal regardless of whether grammar-role or ontology picks
the quadrant. Decomposition proved it precisely: quadrant-forcing alone →
ρ=−0.0022 (statistically dead, p=0.84). Golay-snap alone → ρ=−0.1859
(mostly alive, p=3.95e-63).
**Directive:** Remove the quadrant-forcing step from vector construction
entirely. Keep median-split + Golay-snap only. This is the single highest-
impact fix available — it currently makes most of your production
vocabulary vectors carry no more semantic signal than random noise.

### 1.2 Fix GLM24's silent data loss (three separate bugs)
**Confirmed, all three, independently:**
- `learned_edges` are written to the persisted state file and the counter
  is correctly restored, but nothing re-applies them to the live `crg.out`
  graph object on reload — edges exist on disk, not in the usable graph.
- `state.save()` only fires at `query_count % 5 == 0` with no flush on
  exit — a session ending on a non-multiple-of-5 count silently loses up
  to 4 queries of real, already-computed learning.
- Content-word extraction lets function words through as if meaningful
  (e.g. "other"/"each" from casual phrasing like "relate to each other"
  get treated as real co-occurrence partners, polluting learned edges).
**Directive:** (a) Add a `_load_learned_edges()` that replays
`state.learned_edges` into `self.crg` on `ContinuousLearner.__init__`.
(b) Add an explicit `state.save()` call wherever a session/process ends,
not just on the modulo boundary. (c) Tighten the stopword list to include
common function words that survive the current filter.

### 1.3 Fix the broken v3.16.0 experiment scripts
**Confirmed:** `exp_l_gray_golay_features.py`, `exp_m_snapped_svd_vocab.py`,
`exp_n_nrci_primality.py`, `exp_o_math_generation.py`,
`exp_p_nl_generation.py`, `exp_g_followup.py` all hardcode
`os.chdir(Path(__file__).resolve().parent.parent / "glm_work")`, and
`glm_work/` was never committed. Immediate `FileNotFoundError` on a fresh
clone.
**Directive:** Replace with `Path(__file__).resolve().parent`, or commit
`glm_work/` if it's meant to hold shared state.

═══════════════════════════════════════════════════════════════════════
PRIORITY 2 — RESOLVE INCONSISTENCIES (same word/quantity, different
answers depending on which code path touches it)
═══════════════════════════════════════════════════════════════════════

### 2.1 Two different NRCI formulas are in simultaneous use
**Confirmed:** `LeechLatticeEngine.calculate_nrci()` (weight+sum-of-squares
based) and `KBArchitect.calculate_metrics()`'s `10/(10+tax)` give
different numbers for the same vector. Both are "real" in the sense of
being exact Fraction arithmetic, but they are not the same metric.
**Directive:** Pick one canonical NRCI definition, document which is
authoritative, and either remove the other or rename it clearly (e.g.
`nrci_kb` vs `nrci_substrate`) so nothing silently mixes them.

### 2.2 A single word can have multiple, unrelated vectors depending on source
**Confirmed, directly:** the same word can get a vector from (a) GLM01's
`_build_vocabulary()`, (b) `KBArchitect.generate_vector()` (Z-based for
ELEM_, SHA256-hash-based for everything else), (c) GLM20's SVD+Golay-snap,
(d) GLM23's grammar-aligned construction — four different, unreconciled
sources of truth for what should be one entity's one vector.
**Directive:** Establish one authoritative vector per `ubp_id`, stored in
one place. If different pipelines need different *views* (e.g. a
grammar-tagged copy for parsing), derive them explicitly from the
canonical vector rather than regenerating independently — right now
regeneration is where the inconsistency enters.

### 2.3 Codeword membership is real for exactly one subsystem, absent everywhere else
**Confirmed:** 311/5,395 vocabulary vectors (5.76%) are exact Golay
codewords — 310 of those 311 are chemical elements (deliberately
encoded), the 311th unrelated. Enrichment vs random chance is real (~236x)
but entirely local to that one subsystem. Everywhere else, syndrome-weight
distribution is statistically indistinguishable from random 24-bit noise.
**Directive:** Decide explicitly whether codeword membership is meant to
be a general property of all vocabulary vectors or a special property of
specific hand-built subsystems (elements, and whatever else you intend).
If general, use the Laplacian-embedding-then-snap method (§3.1) which
achieves ~56% correctable at real scale, rather than assuming
non-element vectors already have this property — they don't.

### 2.4 `mog_tensor`'s schema is global and must be regenerated on new entries
**Confirmed from source** (`ubp_mog_mapper.py`): `MASTER_PARAMS` is built
by scanning every entry's `math` field for `key=value` pairs, ONE TIME,
across the whole KB. Adding a new entry with a genuinely new key (not
already in some existing entry's `math` string) gives that key no slot in
the current tensor schema until migration re-runs.
**Directive:** After adding new entries (e.g. the `MATH_NUMBER_*` series
extension built this session), re-run the migration step, or the new
keys' data has nowhere to live in `mog_tensor`.

═══════════════════════════════════════════════════════════════════════
PRIORITY 3 — STRUCTURAL GAPS (not bugs, but confirmed under-built
relative to what the system needs)
═══════════════════════════════════════════════════════════════════════

### 3.1 CRG is 60.7 words per edge (70 edges, 4,248 words)
**Confirmed:** CRG traversal is the only word-level mechanism that behaves
like your math tools do (explicit fact → exact lookup, not statistical
inference) — directly demonstrated via `AdaptiveManifold.fingerprint()`
accepting a real CRG-traversal outcome the same way it accepts a `gcd`
result. It's real and it works; there's just very little of it.
**Directive:** Growing the CRG (hand-authored or extracted from real text)
is the one lever in this whole session with a proven mechanism behind it.
Prioritize this over further vector-construction tuning.

### 3.2 GLM09 never calls your own native computation engines
**Confirmed live, side by side:** every numeric operation in
`GLM09_tools.py` calls stdlib `math` or SymPy. Zero calls anywhere to
`ExactMath`, `ExactRoot`, `BinaryLinearAlgebra`, `NoiseALU`, `PhysicsALU`,
`LinearAlgebraALU` — all fully implemented and working in
`ubp_unified_v5.py`, just never invoked.
**Directive:** If SymPy is meant to be verification-only, GLM09 currently
has this backwards. Route numeric/symbolic operations through the native
ALU classes first; use SymPy (if at all) as an optional cross-check, not
the primary path.

### 3.3 Protected `ubp_id` prefixes silently block refinement
**Confirmed:** words with `ubp_id` prefixed `ELEM_/LAW_/PARTICLE_/
MOLECULE_/MATH_/PVE_` are silently excluded from `_refine_vectors()`. This
may be intentional (protecting hand-curated entries), but it's currently
undocumented and invisible — it cost real debugging time this session
(invalidated a test target without any error or log message).
**Directive:** Keep the exclusion if intentional, but log it explicitly
(e.g. `"skipped refinement: {ubp_id} is protected"`) rather than silently
no-op.

═══════════════════════════════════════════════════════════════════════
PRIORITY 4 — WHAT TO ADOPT GOING FORWARD (confirmed to work)
═══════════════════════════════════════════════════════════════════════

### 4.1 Graph Laplacian spectral embedding, then Golay-snap
**Confirmed best-performing construction this session:** real
co-occurrence counts as edge weights → real eigendecomposition (a genuine
joint solve, not sequential/greedy) → Golay-snap. ρ=−0.1704 after
snapping, vs ρ=−0.1689 before — essentially **lossless** through
discretization, unlike every other method tried. No XOR anywhere, built
from physically-measured quantities (real co-occurrence frequency)
throughout.
**Directive:** Use this as the default construction method for any word
lacking a hand-curated vector, in place of GLM20/23's current SVD+
quadrant-forced pipeline.

### 4.2 MOG-category real scoring, if hand-authoring is preferred over spectral
**Confirmed:** scoring real word definitions against the 24 actually-
existing MOG category names (not inventing new ones), kept as full
24-dimensional data with no forced quadrant, gives ρ=−0.0814 (p=3.16e-13)
— weaker than §4.1 but more interpretable/inspectable, and closes further
with better keyword coverage (currently only 42% of words had any
keyword signal; expand the keyword lists to close this gap).

### 4.3 Naming convention already exists and should be followed exactly
**Confirmed real, existing convention:** `MATH_NUMBER_ZERO_001`,
`MATH_NUMBER_ONE_001` already establish `MATH_NUMBER_<WORD>_001`. This
session extended it (TWO through TWELVE) using the exact real pipeline
(`generate_vector` → `calculate_metrics` → `calculate_tilt` →
`create_entry`), saved in `new_number_entries.json`. Continue this pattern
rather than introducing a parallel convention.

═══════════════════════════════════════════════════════════════════════
WHAT NOT TO DO (confirmed dead ends, tested not assumed)
═══════════════════════════════════════════════════════════════════════
- Do not force vectors into a "dominant quadrant" by any labeling scheme
  (grammar role, ontology, anything else) — confirmed destructive
  regardless of the label.
- Do not rely on sequential/greedy local updates (single-bit-flip walks,
  average-then-snap refinement) for building semantic structure — both
  tested, both failed to converge to meaningful global structure. Use a
  genuine joint solve instead (§4.1, or GF(2) Gaussian elimination for
  genuinely linear structure like the Golay code itself).
- Do not assume SHA256-hash-based vector generation (the current default
  for non-ELEM entries) carries semantic meaning — confirmed it's an
  arbitrary but deterministic mapping (tested prime vs. composite hash
  weights: 12.52 vs 12.38, no real difference). Fine for abstract
  identity-only entries; not a substitute for §4.1/§4.2 where real-world
  meaning should be captured.
