# The Perception-Layer Lattice — Lean Formalisation

The layer theory models *what each level of the pipeline can and
cannot see* about a packing configuration. Each layer is strictly
coarser than the one below it; certification lives at the top,
error-correction at the bottom.

```
Certificate    minimal-polynomial identity        (exact algebraic status)
    ▲
Conway         Griess + Co₀-orbit label           (Leech-symmetry type)
    ▲
Griess         Rational + algebraic axis label    (octad cluster type)
    ▲
Scan           12-decimal rounding                (value-space perception)
    ▲
Rational       identity                          (exact carrier)
    ▲
Integer        floor                              (integral part)
    ▲
Substrate      floor parity mod 2 + G24 decode   (Golay error correction)
```

## Source files (`workspace/lean/tct_squares/TCT/`)

| File | Content |
| --- | --- |
| `GolayData.lean` | The extended binary Golay code G24 as *computed data*: 12 generator rows packed as 24-bit ℕ masks (`golayRows`), codewords by XOR-folding over `testBit` (`golayWord`), plus the 12×24 parity-check matrix (`Hdata`/`golayH`) |
| `Octads.lean` | The 759 octads **computed** from `golayWord` (filter over the 4096 messages by weight), with `native_decide` facts |
| `Layers.lean` | The lattice itself: carriers, perceptions, the `MOG` class, the lawful instance `golayMOG`, the decoder `golayDecode`, boundary theorems |
| `Basic.lean` | Competition-side facts (cascade counts, verification-margin soundness, improvement arithmetic) — compiled; one deliberate `sorry` marking the s(11) wall |

## The Golay substrate (runs 13–14)

The code is real, not a sketch. Construction and verification
(`scripts/golay_build.py`, record in `download/golay_build.json`):

- cyclic G23 from the classic generator polynomial
  (exponent set {0, 1, 5, 6, 7, 9, 11}), extended by an overall
  parity bit to G24;
- **[24, 12, 8]** verified by exhaustive enumeration of all 4,096
  codewords;
- **759 octads** (weight-8 codewords) — computed in Lean, and
  cross-checked against the Python enumeration;
- **2,325 error patterns of weight ≤ 3** (1 + 24 + 276 + 2024), all
  with **distinct syndromes** — unique decoding of every channel
  error of weight ≤ 3; 200/200 random decode tests;
- covering-radius 4, with exactly six codewords at distance 4 on the
  1,771 weight-4 cosets (mirrors the GLM repository's
  `GolayTies.lean` coset census).

### The heartbeat fix (run 14)

Run 13 emitted the 759 octads as a 24 KB data literal; Lean's
`decide` hit the 200,000-heartbeat `isDefEq` limit and
`native_decide` could not evaluate the literal either. The fix —
taken from the GLM repository's own idiom
(`src/lean/RequestProject/GLM/Rule30/ShortcutNetworkData.lean`,
which natively verifies a 735,471-element family) — was to **compute
the data instead of writing it down**:

```lean
def golayRows : List ℕ := [11415553, 14442498, ...]        -- 12 packed rows

def golayWord (m : ℕ) : ℕ :=
  (List.range 12).foldl (fun acc j =>
    if m.testBit j then acc ^^^ golayRows.getD j 0 else acc) 0

def octadIdx : List (List ℕ) :=
  ((List.range 4096).filter (fun m => (codeIdx m).length = 8)).map codeIdx

@[simp] theorem octadIdx_length : octadIdx.length = 759 := by
  unfold octadIdx codeIdx golayWord; native_decide
```

Membership facts ("every octad has 8 indices") become **by
construction** — the filter predicate *is* the length condition —
instead of data checks. The 759-element count is `native_decide`.

## The decoder

`golayDecode w` computes the syndrome of `w` against the verified
parity-check matrix, then searches the weight-≤3 pattern list (zero
word first) for a matching syndrome. Properties proved in
`Layers.lean`:

- `syn24_zero` — the zero word is a codeword;
- `syn24_add` — the syndrome is linear: `syn(w ⊕ e) = syn w + syn e`;
- `zmod2_self_add` — char 2: `x + x = 0`, so a matched pattern means
  the *corrected* word has zero syndrome;
- `synSearch_sound` / `synSearch_mem` — soundness and completeness of
  the pattern search (list induction);
- `MOG.correct_idempotent` (for the `golayMOG` instance) — the second
  decode corrects by the zero word at the head of the list, which is
  the identity;
- `golay_decode_succeeds_of_mem` — every pattern in the list decodes
  successfully (its own syndrome witnesses the match).

## Boundary theorems (what each layer cannot see)

| Theorem | Statement |
| --- | --- |
| `substrate_indist_zero_two` | Substrate is blind to 0 vs 2 (same parity word) |
| `integer_distinguishes_zero_two` | Integer sees 0 vs 2 |
| `integer_indist_zero_half` | Integer is blind to 0 vs ½ |
| `rational_distinguishes_zero_half` | Rational sees 0 vs ½ |
| `scan_blind_to_clearance` | Scan (12-dp rounding) differs by at most one step below 2.5·10⁻¹³ (a quarter of a grid step). Corrected in run 14: the run-11 "equality" form was FALSE — v = 0.49·10⁻¹² vs w = 0.51·10⁻¹² has |v−w| within budget yet round(0.49) = 0 ≠ 1 = round(0.51); the values straddle a rounding boundary. The provable sharp statement is |Δscan| ≤ 1 |

The Griess/Conway labels (`griessAxisOfWord`, `conwayOrbitOfWord`)
take their values from octad membership: axis 1 / orbit 1 iff the
carrier's parity word is an octad, with labels 2, 3 reserved for
further Co₀ orbits (dodecads).
