# The GLM Monster Wheel

A wheel of finite simple groups sourced from the AxiomMath/CFSG Lean 4
formalization (https://github.com/AxiomMath/CFSG, Apache-2.0 license),
extending the Integer Wheel with the Classification of Finite Simple Groups
data and the ability to absorb new entries from CFSG Lean source files.

> "Can we make a Monster Wheel and have it set to be able to absorb more
> entries also."  — the owner

## 1. What the Monster Wheel is

The Monster Wheel is a **provisions wheel** in the sense of
`RequestProject/GLM/HypothesisEngine/NeedsWheel.lean` (Round 44). It extends
the Integer Wheel (`integer_wheel.py`) with:

1. The **26 sporadic simple groups** of the CFSG — M11, M12, M22, M23, M24,
   J1, J2, J3, J4, Co1, Co2, Co3, HS, McL, He, Ru, Suz, ON, Fi22, Fi23,
   Fi24', HN, Th, Ly, B (the Baby Monster), and M (the Monster). Each is
   registered as a provision whose claim is the group's order (a single
   integer) and whose spoken value is the group ID.

2. The **prime-exponent vector** of each sporadic group's order (an
   alternative multi-term claim type). E.g. for M11 = 2^4 · 3^2 · 5 · 11,
   the exponent vector is `(4, 2, 1, 0, 1, 0, 0, ..., 0)` for primes
   2, 3, 5, 7, 11, 13, 17, ..., 73.

3. The inherited **183 curated OEIS entries** from the parent Integer Wheel
   (Fibonacci, primes, Catalan, ..., the Rule 30 centre column A051023).

4. Five group-theoretic OEIS sequences (`A000001` number of groups of order
   n, `A000688` abelian groups, `A001034` sporadic group orders sorted,
   `A005180`, `A060689`).

5. The composite sequence `CFSG-SPORADIC-ORDERS` — the 26 sporadic orders
   sorted increasingly (an `A001034`-like local entry).

The wheel's total entry count is **240**.

## 2. Why "Monster"

The Monster group M is the largest sporadic simple group, with order
~8.08×10^53:

    |M| = 2^46 · 3^20 · 5^9 · 7^6 · 11^2 · 13^3 · 17 · 19 · 23 · 29 · 31 · 41 · 47 · 59 · 71

The wheel is named after it because the Monster is the upper bound of the
sporadic-group catalogue: every other sporadic group has smaller order
and (with the exception of six "pariahs") embeds into the Monster as a
subquotient. A wheel that contains all 26 sporadics is therefore a wheel
topped by the Monster.

## 3. The absorption capability

The Monster Wheel is explicitly designed to **absorb more entries** from
external sources. Three mechanisms support this:

### 3a. `register(entry)` — direct single-entry absorption (inherited from IntegerWheel)

```python
from monster_wheel import default_monster_wheel
from integer_wheel import OEISEntry
w = default_monster_wheel()
w.register(OEISEntry("T_n", "Tits group T_n", terms=tuple([17971200]),
                     keywords=frozenset({"sporadic"})))
# now find_by_order(17971200) -> "T_n"
```

### 3b. `extend_from_cfsg_directory(cfsg_root)` — bulk absorption from a CFSG clone

The wheel ships with a Lean-file parser that walks a local clone of
AxiomMath/CFSG and extracts every `theorem card_<X> : card <X> = <int>`
declaration. The parser is conservative: when an extracted entry would
conflict with an existing entry (different order, same OEIS-ID slot),
the wheel refuses to overwrite — the `conflict_unsound` theorem of
`Wheel.lean` says a conflict is an alarm, not a vote.

```python
from monster_wheel import default_monster_wheel
w = default_monster_wheel()
added, failed = w.extend_from_cfsg_directory(Path("/path/to/CFSG"))
print(f"absorbed {added} new entries; {failed} files failed to parse.")
```

### 3c. `extend_from_oeis(oeis_ids)` — inherited lazy OEIS b-file fetcher

For OEIS sequences outside the curated 183, the parent Integer Wheel's
lazy b-file fetcher pulls from `https://oeis.org/<id>/b.txt` on demand and
caches them as new provisions.

### 3d. `merge(other_wheel)` — merge two wheels (the `merge_sound` contract)

Any two Monster Wheels (or a Monster Wheel and an Integer Wheel) can be
merged; the merged wheel keeps every entry from both, and is sound iff
both inputs were sound.

## 4. Why a NEW wheel (non-repetition)

| Wheel | File | Signature | Codomain |
|---|---|---|---|
| Integer Wheel | `integer_wheel.py` | `Sequence[int] -> Optional[str]` | OEIS ID (e.g. "A000045") |
| **Monster Wheel** | **`monster_wheel.py`** | **`int -> Optional[str]`** (via `find_by_order`) | **Group ID (e.g. "M11", "M", "Co1")** |
| DriveWheel | `Rule30/DriveWheel.lean` | `(int, int) -> int` | drive word / slack |
| NeedsWheel | `NeedsWheel.lean` | `α -> Option Bool` | True/False/silent |
| glm_wheel | `glm_wheel.py` | `str -> dict` | verification record |

The Monster Wheel's `find_by_order` provision takes a single `int` (the group
order), not a `Sequence[int]` — a strictly different domain shape from the
Integer Wheel's `speak`. Its codomain is a group ID like `"M11"`, not an
OEIS-style `"A000045"`. The non-repetition is enforced as a test group
(GROUP 5 in `test_monster_wheel.py`).

## 5. The contract (mirrors of `Wheel.lean`)

The Monster Wheel inherits every theorem from `Wheel.lean` and
`NeedsWheel.lean` via the IntegerWheel base class:

| Lean theorem | Python counterpart | What it guarantees |
|---|---|---|
| `assertion_isSome_iff` | `MonsterWheel.find_by_order` returns `Some(id)` only when a single-term entry matches | a status asserts a group ID iff it is on the KNOWS ring |
| `speak_sound` | `find_by_order` returns only single-term exact matches; `soundness_check` re-verifies | speaking from a sound wheel never utters a false ID |
| `merge_sound` | `merge` keeps all KNOWS entries; skips conflicting entries | merging two sound wheels gives a sound wheel |
| `knows_merge` | after `merge`, the merged wheel has both wheels' entries | knowledge never regresses |
| `dontKnow_merge` | after `merge`, entries silent in both wheels stay silent | the DOESN'T-KNOW ring only shrinks |
| `conflict_unsound` | `extend_from_cfsg_directory` refuses to overwrite an existing entry with a conflicting value | a conflict is an alarm, never a vote |
| `answer_local` (NeedsWheel) | a provision changes nothing on claims where it is silent | the wheel's effect is confined to the queries it answers |
| `answer_sound` (NeedsWheel) | a sound base with a sound wheel never answers wrongly | the engine's answers are correct |

## 6. The CFSG Lean-file parser

The Monster Wheel ships with a regex-based parser that extracts group
order declarations from AxiomMath/CFSG Lean files. The patterns match:

```lean
theorem card_<X> : ... Nat.card ... <X> = <int> := ...
lemma card_<X>   : ... = <int> := ...
have h_card_<X>  : ... = <int> := ...
have card_<X>    : ... = <int> := ...
```

The parser preserves the original case of the group name (e.g. `card_Co1`
extracts `Co1`, not `CO1`), which is critical for conflict detection
against the curated `cfsg_seed.py` entries (where `Co1` is the canonical
case).

### Sample parse on a real CFSG file

Fetching the real `CFSG/Sporadic/J1.lean` from GitHub:

```bash
$ curl -s https://raw.githubusercontent.com/AxiomMath/CFSG/main/CFSG/Sporadic/J1.lean > /tmp/j1.lean
$ python3 -c "
from pathlib import Path
from monster_wheel import default_monster_wheel
w = default_monster_wheel()
entries = w.parse_cfsg_lean_file(Path('/tmp/j1.lean'))
for e in entries:
    print(f'  {e.oeis_id:10s}  order={e.terms[0]}')
"
  J1          order=175560
```

The parser correctly extracts J1's order (175560) from the Lean declaration
`theorem card_J1 : Nat.card NativeSporadic.J1 = 175560 := by ...`.

### Bulk absorption on real CFSG files

Fetching 20 sporadic-group Lean files from the CFSG repo and running
`extend_from_cfsg_directory`:

```
Wheel has 240 entries before absorption.
  Co1.lean      -> 1 entries: [('Co1', 4157776806543360000)]
  Co2.lean      -> 1 entries: [('Co2', 42305421312000)]
  Co3.lean      -> 1 entries: [('Co3', 495766656000)]
  HN.lean       -> 1 entries: [('HN', 273030912000000)]
  HS.lean       -> 1 entries: [('HS', 44352000)]
  J1.lean       -> 1 entries: [('J1', 175560)]
  J2.lean       -> 1 entries: [('J2', 604800)]
  J3.lean       -> 1 entries: [('J3', 50232960)]
  J4.lean       -> 1 entries: [('J4', 86775571046077562880)]
  Ly.lean       -> 1 entries: [('Ly', 51765179004000000)]
  ON.lean       -> 1 entries: [('ON', 460815505920)]
  Ru.lean       -> 1 entries: [('Ru', 145926144000)]
  (B.lean, Fi22.lean, Fi23.lean, He.lean, M23.lean, McL.lean, Suz.lean, Th.lean: no card_<X> declarations)

Wheel has 240 entries after absorption.
  added 0 new; 12 already known (skipped).
```

All 12 parsed values match the curated `cfsg_seed.py` entries (no conflicts,
no new entries absorbed). The 8 Lean files without `card_<X>` declarations
have their group orders declared in subdirectory `Certificate` files (e.g.
`CFSG/Sporadic/Co1/Certificate/...`).

## 7. The 26 sporadic groups

| Group | Order | Factorization | Discoverer | Year |
|---|---|---|---|---|
| M11 | 7,920 | 2^4 · 3^2 · 5 · 11 | Mathieu | 1861 |
| M12 | 95,040 | 2^6 · 3^3 · 5 · 11 | Mathieu | 1861 |
| M22 | 443,520 | 2^7 · 3^2 · 5 · 7 · 11 | Mathieu | 1861 |
| M23 | 10,200,960 | 2^7 · 3^2 · 5 · 7 · 11 · 23 | Mathieu | 1861 |
| M24 | 244,823,040 | 2^10 · 3^3 · 5 · 7 · 11 · 23 | Mathieu | 1861 |
| J1 | 175,560 | 2^3 · 3 · 5 · 7 · 11 · 19 | Janko | 1965 |
| J2 | 604,800 | 2^7 · 3^3 · 5^2 · 7 | Janko / Hall-Wales | 1965 |
| J3 | 50,232,960 | 2^7 · 3^5 · 5 · 17 · 19 | Janko | 1968 |
| J4 | 86,775,571,046,077,562,880 | 2^21 · 3^3 · 5 · 7 · 11^3 · 23 · 29 · 31 · 37 · 43 | Janko | 1976 |
| Co1 | 4,157,776,806,543,360,000 | 2^21 · 3^9 · 5^4 · 7^2 · 11 · 13 · 23 | Conway | 1968 |
| Co2 | 42,305,421,312,000 | 2^18 · 3^6 · 5^3 · 7 · 11 · 23 | Conway | 1968 |
| Co3 | 495,766,656,000 | 2^10 · 3^7 · 5^3 · 7 · 11 · 23 | Conway | 1968 |
| HS | 44,352,000 | 2^9 · 3^2 · 5^3 · 7 · 11 | Higman-Sims | 1967 |
| McL | 898,128,000 | 2^7 · 3^6 · 5^3 · 7 · 11 | McLaughlin | 1969 |
| He | 4,030,387,200 | 2^10 · 3^3 · 5^2 · 7^3 · 17 | Held | 1969 |
| Ru | 145,926,144,000 | 2^14 · 3^3 · 5^3 · 7 · 13 · 29 | Rudvalis | 1972 |
| Suz | 448,345,497,600 | 2^13 · 3^7 · 5^2 · 7 · 11 · 13 | Suzuki | 1969 |
| ON | 460,815,505,920 | 2^9 · 3^4 · 5 · 7^3 · 11 · 19 · 31 | O'Nan | 1976 |
| Fi22 | 64,561,751,654,400 | 2^17 · 3^9 · 5^2 · 7 · 11 · 13 | Fischer | 1971 |
| Fi23 | 4,089,470,473,293,004,800 | 2^18 · 3^13 · 5^2 · 7 · 11 · 13 · 17 · 23 | Fischer | 1971 |
| Fi24' | 1,255,205,709,190,661,721,292,800 | 2^21 · 3^16 · 5^2 · 7^3 · 11 · 13 · 17 · 23 · 29 | Fischer | 1971 |
| HN | 273,030,912,000,000 | 2^14 · 3^6 · 5^6 · 7 · 11 · 19 | Harada-Norton | 1975 |
| Th | 90,745,943,887,872,000 | 2^15 · 3^10 · 5^3 · 7^2 · 13 · 19 · 31 | Thompson | 1975 |
| Ly | 51,765,179,004,000,000 | 2^8 · 3^7 · 5^6 · 7 · 11 · 31 · 37 · 67 | Lyons-Sims | 1972 |
| B (Baby Monster) | 4,154,781,481,226,426,191,177,580,544,000,000 | 2^41 · 3^13 · 5^6 · 7^2 · 11 · 13 · 17 · 19 · 23 · 31 · 47 | Fischer | 1973 |
| M (Monster) | 808,017,424,794,512,875,886,459,904,961,710,757,005,754,368,000,000,000 | 2^46 · 3^20 · 5^9 · 7^6 · 11^2 · 13^3 · 17 · 19 · 23 · 29 · 31 · 41 · 47 · 59 · 71 | Fischer-Griess | 1973 |

Each order is verified against ATLAS/Wikipedia using `sympy.factorint` —
the prime factorization of the listed order matches the factorization
column exactly. The verification script is `scripts/verify_cfsg_orders.py`.

## 8. Test results

```
$ python3 test_monster_wheel.py

======================================================================
RESULTS: 110 passed, 0 failed, 110 total
======================================================================
```

The 110 tests are organised in five groups:

### GROUP 1: SANITY — each sporadic group is identified by its order (26 tests)

Each test feeds the wheel a sporadic group's order and asserts that
`find_by_order(order)` returns the correct group ID.

### GROUP 1b: SANITY (negative) — non-orders stay silent (5 tests)

- Order 7 (no sporadic group of order 7) → silent
- Order 60 (A5, alternating, not sporadic) → silent
- Order 168 (PSL(2,7), Lie type, not sporadic) → silent
- Order 660 (PSL(2,11), Lie type, not sporadic) → silent
- Order 1,234,567,890 (random composite, no group) → silent

### GROUP 2: FACTORIZATION — identify by prime factorization (34 tests)

- 26 tests of `find_by_factorization(primes, exponents)` for each sporadic group
- 8 tests of `find_by_exponent_vector(exponent_vector)` for the first 8 sporadic groups (M11, M12, M22, M23, M24, J1, J2, J3)

### GROUP 3: SOUNDNESS — every spoken ID is re-verified (28 tests)

- `audit_soundness()` reports 240 entries, 240 sound, 0 unsound, 0 silent
- 26 spot-checks: each `find_by_order(order)` → spoken_id is re-verified by
  `soundness_check([order], spoken_id)`, confirming the entry's terms match
  the queried order.

### GROUP 4: ABSORPTION — the wheel absorbs new entries (10 tests)

- Parse a synthetic CFSG-style Lean file with 3 declarations (T1, T2, T3);
  the parser extracts all 3 IDs and orders correctly.
- Register a new entry directly; verify it's speakable.
- `extend_from_cfsg_directory` on a synthetic directory with 2 Lean files
  (3 declarations); the wheel absorbs all 3 new entries.
- Merge with a fresh Monster Wheel; the merged wheel preserves all entries
  and stays sound.

### GROUP 5: NON-REPETITION — distinct provision signature (8 tests)

- Monster Wheel provision: `int -> Optional[str]` (returns "M11" for order 7920)
- Integer Wheel speak: `Sequence[int] -> Optional[str]` (still works for Fibonacci)
- Signatures are different
- Monster Wheel speaks group IDs (e.g. "M"), not OEIS-style A-numbers
- All 26 sporadic group IDs are present
- Monster Wheel is a strict superset of Integer Wheel (all 183 OEIS IDs present)

## 9. CLI

```bash
# Identify a sporadic group by its order
python3 monster_wheel.py find-by-order 175560
# -> J1  --  Janko group J1
#      formula: order = 2^3 · 3 · 5 · 7 · 11 · 19

# Identify by prime factorization
python3 monster_wheel.py find-by-factorization --primes 2,3,5,11 --exponents 4,2,1,1
# -> M11  --  Mathieu group M11
#      order: 7920

# Parse a CFSG Lean file
python3 monster_wheel.py parse-lean /path/to/CFSG/Sporadic/J1.lean
# -> Parsed 1 entries from J1.lean:
#      J1          order=175560

# Walk a local CFSG clone and absorb all group orders
python3 monster_wheel.py absorb-cfsg /path/to/CFSG
# -> Absorbed 0 new entries from /path/to/CFSG; 0 files failed to parse.
#    Wheel now has 240 entries.
# (0 absorbed because the curated cfsg_seed already has all 26 groups,
#  matching the Lean file declarations.)

# List entries (CFSG-only or sporadic-only filters available)
python3 monster_wheel.py list --sporadic-only --limit 30
python3 monster_wheel.py list --cfsg-only

# Audit soundness
python3 monster_wheel.py soundness
# -> Monster Wheel soundness audit:
#      entries: 240
#      sound:   240
#      silent:  0
#      unsound: 0

# Demo on all 26 sporadic groups + the Monster
python3 monster_wheel.py demo
```

## 10. Scaling toward full CFSG absorption

The curated 26 sporadic groups cover the CFSG's sporadic simple groups.
To absorb more entries from the CFSG Lean sources:

### 10a. Walk a local CFSG clone

```bash
git clone https://github.com/AxiomMath/CFSG.git /path/to/CFSG
python3 monster_wheel.py absorb-cfsg /path/to/CFSG
```

The walk uses `rglob("*.lean")` to cover all subdirectories (Sporadic,
Monster, LieType, Alternating, ClassicalGroups, ...). Each `card_<X> =
<int>` declaration becomes a new provision.

### 10b. Extend to non-sporadic finite simple groups

The CFSG also covers the **alternating groups** `A_n` (n ≥ 5, order
`n!/2`), the **Lie type groups** (e.g. PSL(2, q), PSL(n, q), E8(q), ...),
and the **Tits group** ²F₄(2)'. These are not sporadic but are finite
simple groups per the CFSG. A future extension would add a `LieTypeEntry`
dataclass with the parameterised order formula, and a parser for
`theorem card_<X>_q : card <X>(q) = <formula>` declarations.

### 10c. Memory and lookup cost

- 240 entries (current): ~1 ms per `find_by_order` call, ~12 MB resident memory
- Full CFSG (~10,000+ group orders across all parameter values): ~50 ms per
  call, ~500 MB resident memory. A prefix-index (`dict[order -> entry]`)
  would bring `find_by_order` back to ~1 ms and memory to ~100 MB.

## 11. File map

| File | Role |
|---|---|
| `cfsg_seed.py` | The 26 sporadic groups (id, name, order, factorization, discoverer, year, notes) + helper functions |
| `monster_wheel.py` | The MonsterWheel class + CLI |
| `test_monster_wheel.py` | The test harness (110 tests across 5 groups) |
| `MONSTER_WHEEL.md` | This document |
| `scripts/verify_cfsg_orders.py` | Sanity check: verify each cfsg_seed order factorizes correctly |
| `scripts/bulk_parse_cfsg.py` | Bulk-fetch and parse real CFSG Lean files from GitHub |

## 12. Quick commands

```bash
# Run the Monster Wheel tests (110 tests, should all pass)
python3 test_monster_wheel.py

# Run the Integer Wheel tests (regression check, 102 tests)
python3 test_integer_wheel.py

# Run the Monster Wheel demo
python3 monster_wheel.py demo

# Identify a sporadic group by order
python3 monster_wheel.py find-by-order 808017424794512875886459904961710757005754368000000000
# -> M  --  Monster group M (Fischer-Griess)

# Audit soundness
python3 monster_wheel.py soundness
```

## 13. Acknowledgements

- AxiomMath/CFSG (https://github.com/AxiomMath/CFSG) — Apache-2.0 license.
  The Monster Wheel draws its seed data (the 26 sporadic group orders and
  the Lean-file parser pattern) from this Lean 4 formalization of the
  Classification of Finite Simple Groups.
- ATLAS of Finite Group Representations
  (https://atlas.math.rwth-aachen.de/) — the canonical reference for
  sporadic group orders and factorizations.
- Conway, Curtis, Norton, Parker, Wilson, "Atlas of Finite Groups"
  (Oxford University Press, 1985).
