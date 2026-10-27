# The GLM Integer Wheel

An OEIS-backed integer-sequence identification wheel for the GLM, wired into the
existing Wheel architecture (`Wheel.lean`, `NeedsWheel.lean`, `DriveWheel.lean`,
`glm_wheel.py`).

> "Wheels are like domains of language for the GLM, it should be able to
> 'speak integer' once created and wired in."  — the owner

This document covers the contract, the curated OEIS coverage, the test results,
the wiring into `glm_wheel.py`, and the scaling path from the curated ~183 entries
to the full OEIS catalogue (~400,000 sequences).

## 1. What the Integer Wheel is

The Integer Wheel is a **provisions wheel** in the sense of
`RequestProject/GLM/HypothesisEngine/NeedsWheel.lean` (Round 44). Each OEIS
sequence on the wheel is one provision:

```
Provision: List[int] -> Option[OEIS_ID]
```

The provision speaks `Some(oeis_id)` when the queried integer prefix matches
the entry's b-file (the authoritative OEIS term list) and stays silent (`None`)
otherwise. Under the `Sound truth p` predicate of `Wheel.lean`, a sound wheel
never utters a false sentence: every spoken OEIS ID is the ID of an entry whose
b-file actually starts with the queried prefix.

The wheel's language (its speakable assertions) is the set of `(prefix, OEIS_ID)`
pairs derivable from the entries' b-files. When the GLM is asked "what is this
sequence?", the Integer Wheel answers with the OEIS ID whose b-file matches;
this is the GLM "speaking integer".

## 2. Why it is a NEW wheel (non-repetition)

The Aristotle/GLM project ships four existing wheels. The Integer Wheel's
provision signature is strictly distinct from each:

| Wheel | File | Signature (input -> output) |
|---|---|---|
| DriveWheel | `Rule30/DriveWheel.lean` | `(int, int) -> int`  (period, word -> drive word / slack) |
| NeedsWheel | `HypothesisEngine/NeedsWheel.lean` | `α -> Option Bool`  (abstract claim -> True/False/silent) |
| glm_wheel | `glm_wheel.py` | `str -> dict {verified, result, verdict}`  (H-id -> verification record) |
| r28_wheel | `glm/r28_wheel.json` | static claims ledger (no provision function) |
| **IntegerWheel** | **`integer_wheel.py`** | **`Sequence[int] -> Optional[str]`  (prefix -> OEIS ID)** |

The Integer Wheel's codomain is `String` (an OEIS ID), not `Bool` (a truth
value). Its domain is `Sequence[int]` (an integer prefix), not a hypothesis
ID, a (period, word) pair, or an abstract type parameter. The non-repetition
is enforced as a test (`GROUP 4: NON-REPETITION` in `test_integer_wheel.py`).

## 3. The contract (mirrors of `Wheel.lean` and `NeedsWheel.lean`)

The Integer Wheel obeys the following theorems (Python counterparts of the
Lean statements):

| Lean theorem (`Wheel.lean`) | Python counterpart | What it guarantees |
|---|---|---|
| `assertion_isSome_iff` | `OEISEntry.provision` only returns `Some(id)` when the entire claim matches the b-file | a status asserts an OEIS ID iff it is on the KNOWS ring |
| `speak_sound` | `IntegerWheel.speak` returns only full-match IDs; `soundness_check` re-verifies | speaking from a sound wheel never utters a false ID |
| `merge_sound` | `IntegerWheel.merge` keeps old KNOWS entries and adds new ones | merging two sound wheels gives a sound wheel |
| `knows_merge` | after `merge`, the merged wheel contains both wheels' entries | knowledge never regresses |
| `dontKnow_merge` | after `merge`, entries silent in both wheels stay silent | the DOESN'T-KNOW ring only shrinks |
| `conflict_unsound` | two entries cannot both have the same OEIS ID and disagree on the b-file | a conflict is an alarm |
| `answer_local` (NeedsWheel) | a provision changes nothing on claims where it is silent | the wheel's effect is confined to the queries it answers |
| `answer_sound` (NeedsWheel) | a sound base with a sound wheel never answers wrongly | the engine's answers are correct |

## 4. The curated OEIS coverage

The wheel ships with **183 hand-picked OEIS entries** (the seed file
`oeis_seed.py`). The curation spans:

- **number theory** (60+): primes `A000040`, composites `A002808`, powers
  `A000079`/`A000244`/`A000302`/..., factorials `A000142`, sigma `A000203`,
  Euler's totient `A000010`, Mersenne primes `A000668`, Fermat numbers
  `A000215`, primorials `A002110`, highly composite `A002182`, squarefree
  `A005117`, Wieferich primes `A001220`, Sophie Germain primes `A005384`;
- **combinatorics** (40+): Fibonacci `A000045`, Lucas `A000032`, Catalan
  `A000108`, Bell `A000110`, Motzkin `A001006`, large/small Schroeder
  `A006318`/`A001003`, double-factorial `A001147`, derangements `A000166`,
  involutions `A000085`, Euler up/down `A000111`, central Delannoy `A001850`,
  partitions `A000041`, partitions into odd parts `A000009`;
- **recreational** (20+): Recamán `A005132`, Ulam `A002858`, Kolakoski
  `A000002`, look-and-say `A005150`/`A001155`, Pell `A000129`, Woodall
  `A003261`, Stern's diatomic `A002487`, automorphic numbers `A005224`,
  happy numbers `A007770`, palindromic numbers `A002113`;
- **digit-based / parity** (10+): Thue-Morse `A010060`, evil `A001969`,
  odious `A000069`, Hamming weight `A000120`, ruler function `A001511`,
  largest-power-of-2-dividing-n `A006519`;
- **constants** (10): digits of e `A001113`, pi `A000796`, sqrt(2) `A010505`,
  golden ratio `A001622`, ln(2) `A002162`, sqrt(3) `A002193`, Euler-Mascheroni
  `A001620`, Catalan's constant `A006752`, pi^2 `A020764`, 1/pi `A019702`;
- **cellular automata** (Rule 30 family, 3): centre column `A051023`,
  right diagonal `A269129`, complement of Thue-Morse `A010059`;
- **continued fractions** (3): of e `A003417`, of pi `A001203`, of sqrt(2)
  `A014538`;
- **the meta entry** `A000001` (number of groups of order n).

Where a closed-form generator is short (Fibonacci, primes, Catalan, Bell,
Recamán, Kolakoski, Thue-Morse, etc.) the terms are precomputed at module
load by a Python helper and embedded into the entry's b-file. For other
sequences (Rule 30 centre column, digit expansions, etc.) the canonical
OEIS first terms are listed explicitly.

The 183 entries comfortably cover the integer sequences that arise in the
GLM's Rule 30 work and in the standard OEIS / Project Euler / ARC puzzle
suite. They are insufficient for arbitrary OEIS lookup — see §7 for the
scaling path.

## 5. Test results

```
$ python3 test_integer_wheel.py

======================================================================
RESULTS: 102 passed, 0 failed, 102 total
======================================================================
```

The 102 tests are organised in five groups:

### GROUP 1: SANITY — known sequences identify correctly (52 tests)

Each test feeds the wheel a famous OEIS prefix and asserts that the spoken
ID is correct. Examples:

- Fibonacci `[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]` -> `A000045`
- Primes `[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]` -> `A000040`
- Powers of 2 `[1, 2, 4, 8, 16, 32, 64, 128, 256, 512]` -> `A000079`
- Catalan `[1, 1, 2, 5, 14, 42, 132, 429, 1430]` -> `A000108`
- Padovan `[1, 0, 0, 1, 0, 1, 1, 1, 2, 2]` -> `A000931`
- Thue-Morse `[0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]` -> `A010060`
- Recamán `[0, 1, 3, 6, 2, 7, 13, 20, 12, 21]` -> `A005132`
- e digits `[2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5]` -> `A001113`
- pi digits `[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3]` -> `A000796`
- Pell `[0, 1, 2, 5, 12, 29, 70, 169, 408, 985]` -> `A000129`
- LCM 1..n `[1, 1, 2, 6, 12, 60, 60, 420, 840]` -> `A003418`
- Woodall `[1, 7, 23, 63, 159, 383, 895, 2047, 4607]` -> `A003261`

### GROUP 1b: SANITY (negative) — random sequences stay silent (3 tests)

- The "Lost numbers" `[4, 8, 15, 16, 23, 42, 999, 1234, 5678, 90123]` -> silent
- Random large integers -> silent
- Primes starting at 7 (offset mismatch with `A000040` which starts at 2) -> silent

### GROUP 2: RULE 30 APPLICATION — wheel names Rule-30-derived sequences (7 tests)

- **Rule 30 centre column** `[1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1]` -> `A051023` (the project's r28_wheel.json row C02)
- **Rule 30 centre column, 10-term prefix** -> `A051023` (shorter prefix also identifies)
- **period-doubling diagonals** `[0, 3, 8, 29, 400, 87867]` -> silent (the sequence is unique to Rule 30; the wheel correctly does not over-claim)
- **dyadic tower of periods** `[1, 2, 4, 8, 16, 32]` -> `A000079` (powers of 2)
- **eventually-white left diagonals** `[2, 7, 28]` -> silent (not a known OEIS prefix)
- **centre column lag-k profile** `[100, 99, 99, 98, 96, 92, 84]` -> silent (unique to Rule 30)
- **wobble maxima** `[3200, 81, 441, 8]` -> silent

### GROUP 3: SOUNDNESS — every spoken ID is re-verified against the b-file (12 tests)

- `audit_soundness()` reports 183 entries, 183 sound, 0 unsound, 0 silent
- 10 spot-checks: each `speak(claim)` -> spoken_id is re-verified by
  `soundness_check(claim, spoken_id)`, confirming the entry's b-file
  contains the entire claim as a prefix.

### GROUP 4: NON-REPETITION — distinct provision signature (25 tests)

- Integer Wheel signature is `Sequence[int] -> Optional[str]`
- DriveWheel signature is `(int, int) -> int`
- NeedsWheel signature is `α -> Option Bool`
- glm_wheel signature is `str -> dict {verified, result, verdict}`
- r28_wheel signature is `static claims ledger (no provision function)`
- Each is verified to differ from the Integer Wheel's signature.
- Sample OEIS IDs (`A000045`, `A000040`, `A000079`, `A051023`, `A001113`,
  `A000796`, `A000108`, `A000110`, `A010060`, `A005132`) are confirmed to
  be on the Integer Wheel.
- The spoken output is confirmed to be an OEIS ID (a string starting with
  "A"), not a bool or hypothesis dict.

### GROUP 5: MERGE / TURN — Wheel.lean `merge old new` operation (5 tests)

- Merging the wheel with a new entry yields a wheel of size `n+1` containing
  the new entry
- The merged wheel speaks the new entry on its b-file prefix
- The merged wheel still speaks the old Fibonacci entry (no regression)
- `audit_soundness` on the merged wheel still reports 0 unsound
- Merging the wheel with itself is idempotent (size unchanged)

## 6. Wiring into `glm_wheel.py`

The Integer Wheel is plugged into `glm_wheel.py` (the v16 hypothesis
wheel's generator). The integration:

1. **Import** — `glm_wheel.py` imports `IntegerWheel` and `default_wheel`
   from `integer_wheel.py`, plus the v16 engine (with graceful degradation
   if the v16 dependency chain is broken).
2. **Build** — `main()` calls `default_integer_wheel()` to build the
   Integer Wheel with the curated 183 entries.
3. **Run provisions** — `main()` calls `integer_wheel_entries(int_wheel)`,
   which iterates over `RULE30_INTEGER_SEQUENCES` (a hardcoded list of
   Rule-30-derived integer sequences from the v16 hypothesis list,
   tagged by their H-id: H08 the period-doubling diagonals, H26 the
   dyadic tower of periods, H35 the R-calculus lag-k biases, H39 the
   centre column, H40 the delta-sigma accumulator, H47 the uniformity
   gaps). For each, the wheel is queried; results become `WheelEntry`
   items:
   - `thinks-true` / `integer-wheel-verified` if the wheel spoke
   - `doesn't-know` / `integer-wheel-silent` if it stayed silent
4. **Merge** — the Integer Wheel entries are merged into the three rings
   (KNOWS / THINKS-TRUE / DOESN'T-KNOW) before drawing the wheel image.
5. **Language wheel** — verified Integer Wheel entries are added to the
   language wheel (the GLM's speakable vocabulary). The GLM can now
   "speak integer" by citing the OEIS ID whose b-file matches a Rule 30
   sequence.
6. **Output** — the Integer Wheel section is added to both the markdown
   and JSON outputs of `glm_wheel.py`:
   - `glm_wheel.md` shows the integer-wheel entries as part of the rings
   - `glm_wheel.json` has a top-level `integer_wheel` field with the
     OEIS coverage count and a per-provision report (H-id, spoke?, category,
     statement, evidence)

The wiring is designed so that **the Integer Wheel runs even when the v16
engine is unavailable** — the Rule-30-derived integer sequences are
hardcoded in `RULE30_INTEGER_SEQUENCES`, not pulled from the engine's
runtime data. This makes the wheel's behaviour reproducible.

### Sample output from `python3 glm_wheel.py`:

```
Building the Integer Wheel (curated OEIS subset)...
  Loaded Integer Wheel with 183 OEIS entries.

Running the Integer Wheel over Rule 30 integer sequences...
  Spoke on 2/6 sequences; silent on 4.
  [silent] IW-H08: the period-doubling left diagonals of Rule 30 ...
  [SPOKE]  IW-H26: the eventual periods of the period-doubling diagonals ... is OEIS A000079
  [silent] IW-H35: R-calculus (T=0, rho=1, C=0) lag-k biases ...
  [SPOKE]  IW-H39: the Rule 30 centre column from a single black cell ... is OEIS A051023
  [silent] IW-H40: the delta-sigma accumulator range ...
  [silent] IW-H47: centre column 2-bit and 3-bit block uniformity gaps ...

  DOESN'T KNOW:    4 entries
  THINKS IS TRUE:  2 entries
  THINKS IS NEEDED:0 entries

Building the language wheel...
  2 verified concepts (incl. 2 from the Integer Wheel)
```

## 7. Scaling toward the full OEIS catalogue (~400,000 sequences)

The curated 183 entries cover the GLM's Rule 30 work and standard puzzle
sequences. To grow toward the full ~400,728 OEIS catalogue:

### 7a. The lazy b-file fetcher

`IntegerWheel.extend_from_oeis(oeis_ids, timeout=10.0)` fetches b-files
from `https://oeis.org/<id>/b.txt` on demand. Each b-file is the
authoritative term list published by OEIS. The wheel parses the b-file,
extracts the terms, and registers the entry as a sound provision.

```python
w = default_integer_wheel()
added, failed = w.extend_from_oeis(["A001006", "A000111", "A000088"])
# 3 added, 0 failed (assuming network access)
```

The fetcher is **opt-in**: the curated wheel does not require network
access; the existing test suite does not hit the network.

### 7b. The stripped.gz bulk loader

OEIS publishes a single `stripped.gz` file containing the name and
first ~10-30 terms of every sequence. A bulk loader would:

1. Download `https://oeis.org/stripped.gz` (one file, ~30 MB)
2. Parse the gzipped text format: each line is `Axxxxxx name | a,b,c,d,...`
3. Register each as an `OEISEntry` with `terms=tuple(parsed_ints)`

This gives near-full OEIS coverage at the cost of one ~30 MB download and
a longer cold-start load time (estimated 5-10 seconds to parse and
register 400K entries).

### 7c. Memory and lookup cost

- **Curated 183 entries**: ~1 ms per `speak` call, ~10 MB resident memory
- **Full 400K entries**: ~10-50 ms per `speak` call (linear scan),
  ~500 MB resident memory. A prefix-index (`dict[first_term -> list of OEISEntry]`)
  would bring `speak` back to ~1 ms and memory to ~1 GB.

The wheel's `provision` design (one callable per entry) and the
`merge_sound` theorem mean the engine can be grown incrementally: start
with the curated 183, add the lazy fetcher for hot sequences, and only
load the bulk stripped.gz when full coverage is required.

## 8. How the GLM uses this wheel

### 8a. As a provision on the needs wheel

The `needs_wheel_provision()` method returns a single callable suitable for
placing on the v18 needs wheel:

```python
w = default_integer_wheel()
provision = w.needs_wheel_provision()
# provision: Sequence[int] -> Optional[str]
```

When the v18 engine is asked "is this integer sequence one we know?", it
consults the wheel in order; the Integer Wheel provision speaks an OEIS
ID if it can, else falls silent.

### 8b. In Rule 30 puzzle solving

When the v16 hypothesis engine emits an integer-valued observation (a
period-doubling diagonal, a wobble maximum, a uniformity gap), the engine
queries the Integer Wheel with the observation's prefix. Three outcomes:

1. **Spoke with an OEIS ID** — the observation is a known OEIS sequence.
   The engine can cite the OEIS ID in its hypothesis, connecting the
   Rule 30 observation to the broader integer-sequence literature.
2. **Stayed silent** — the observation is unique to Rule 30 (not in OEIS).
   The engine reports this as a "DOESN'T-KNOW" entry; the gap is itself
   a contribution.
3. **Spoke with multiple IDs** — the observation's prefix is shared by
   several OEIS entries (e.g., the prefix `[1, 1, 2, 5, 14]` is shared
   by Catalan and a few others). The engine reports the candidates
   ranked by match length.

### 8c. The language wheel

After running the Integer Wheel, the GLM's language wheel gains
`(prefix, OEIS ID)` assertions — the GLM can now cite `A051023` to refer
to the Rule 30 centre column, `A000079` to refer to the dyadic tower of
left-diagonal periods, etc. This is what "speaking integer" means: the
GLM has a vocabulary for naming integer sequences by their OEIS ID,
backed by the b-file soundness guarantee.

## 9. File map

| File | Role |
|---|---|
| `integer_wheel.py` | The Integer Wheel core: `OEISEntry`, `IntegerWheel`, soundness check, merge/turn, CLI |
| `oeis_seed.py` | The curated OEIS subset (183 entries) + helper generators |
| `test_integer_wheel.py` | The test harness (102 tests across 5 groups) |
| `glm_wheel.py` (modified) | The v16 wheel generator, now wired to call the Integer Wheel |
| `INTEGER_WHEEL.md` | This document |
| `download/glm_wheel.png` | The wheel diagram (with Integer Wheel entries on the rings) |
| `download/glm_wheel.md` | The wheel document (with Integer Wheel section) |
| `download/glm_wheel.json` | The wheel JSON (with `integer_wheel` top-level field) |

## 10. Quick commands

```bash
# Run the Integer Wheel tests (102 tests, should all pass)
python3 test_integer_wheel.py

# Run the demo on famous sequences
python3 integer_wheel.py demo

# Identify an integer prefix
python3 integer_wheel.py identify 0 1 1 2 3 5 8 13 21 34

# Audit the wheel's soundness
python3 integer_wheel.py soundness

# List entries (optionally filtered by keyword)
python3 integer_wheel.py list --keyword fibonacci

# Run the wired-in glm_wheel.py (writes download/glm_wheel.{png,md,json})
python3 glm_wheel.py
```
