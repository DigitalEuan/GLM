# Exact Verification of the Table — 875/1000 Rows

`download/exact_snap.json` records, for every row of the table, an
attempt to verify its geometry **exactly**: the container fit and the
pairwise square non-overlap are re-checked as closed predicates over
`Fraction` (Python `fractions`), using the algebraic number field
certificate issued for that row.

## Current state (run 15 refresh)

The whole-table census (`exact_snap.py`, ~40 min, field-certificate
methodology) on the run-15 frontier:

| Class | Rows | Meaning |
| --- | --- | --- |
| `exact_verified` | **853** | container + non-overlap verified in exact rational arithmetic over the certificate field |
| `no_cert` | 140 | level-0/1 rows: manual survey records **plus the 76 atlas imports** (see below) |
| `angle_out_of_scope` | 7 | certificate exists but involves angles outside the supported scope |

Two verification tracks, stated honestly:

1. **Field-certificate track** (whole-table census): rows whose
   construction has a minimal-polynomial certificate in
   `galois_certificates.json` verify exactly at their certificate
   field — 853 rows, every certifiable row passes.
2. **Rational-replay track** (`atlas_exact_replay.json`): the 76
   community imports carry no *field* certificate (they are finalize
   states, 12-dp), but their atlas certificates are fully
   rational-geometric — rotation (c, s) = ((1−t²)/(1+t²), 2t/(1+t²))
   with t rational. Replayed in pure `Fraction` arithmetic
   (container: corners in [0, side]²; non-overlap: pairwise SAT on
   the 4 edge-normal axes): **76/76 verify exactly**, max
   |L − side_exact| = 1.889e-09 (the finalize gap + 12-dp rounding).

Combined: **929/1000 rows carry an exact verification** on one of the
two tracks; the census records them under the track that matches the
certificate the row actually has. The remaining 71 rows (140 − 76 = 64
genuine no-cert survey records + 7 angle-out) are the honest boundary.

By family (census): grid 546 (all exact) · chain3 96 · gobel2 53 ·
closure 54 · gobelS 18 · removal 22 · gobel3 9 · aux 5 · exact 50 —
all certifiable rows at 100%; atlas 76 (exact via the replay track).

## What broke in v1 and how it was fixed (run 13)

v1 verified only 554 rows and reported 321 `snap_failed`. Both failure
causes were bugs in the verifier, not in the table:

1. **Sign comparison under radicals** — fixed by square comparison
   (sign-safe).
2. **Snap anchoring** — fixed by scanning the full −240..240 window
   (same convention as the Leech-map cross-check).

With both fixed, every row holding a certificate and in-scope angles
verifies.

## The honest boundary

- **64 no-cert survey rows** (level-0/1 manual records): no
  certification route exists today.
- **7 angle-out rows**: certificates exist but involve angles the
  current verifier does not support.
- **76 atlas rows**: exact via the replay track (not the census's
  field-certificate track) — recorded there, not in `exact_snap`.

## Verification method

Field-certificate track (census): per row, take the certificate
(minimal polynomial + sample point + field invariants), reconstruct
exact coordinates, check container fit and pairwise non-overlap as
closed predicates over `Fraction`; snap scan −240..240; comparisons by
squares, never floats.

Rational-replay track (imports): see `scripts/atlas_exact_replay.py`;
the method is in the ledger's `method` field.
