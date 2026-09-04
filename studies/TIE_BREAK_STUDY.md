# The tie-break: the part of an address that geometry does not decide

*Most of this development's Leech addresses are not unique. The scaled feature
vector sits exactly equidistant from several lattice points, and which of them
becomes the address is settled by the decoder's tie-break — an implementation
detail that had never been written down, never proved well defined, and never
measured. This study writes it down, proves what can be proved about it, and
measures what depends on it. The answer is sharper than either hope: a third
of the addresses move under a different rule, every figure computed from a
single address is provably unchanged, and the pairwise figures of the address
study move by one declaration in two thousand.*

Code:
[`overlay/glm_universal/reasoning/tie_break.py`](../overlay/glm_universal/reasoning/tie_break.py).
Query: `report tiebreak`.
Formal development:
[`RequestProject/GLM/TieBreak.lean`](../RequestProject/GLM/TieBreak.lean).
Tests: `overlay/glm_universal/tests/test_tie_break.py`.
The decoder it describes:
[`overlay/glm_universal/reasoning/analogy.py`](../overlay/glm_universal/reasoning/analogy.py)
`nearest_lattice_point`, on the hot path through
[`llvq_table.py`](../overlay/glm_universal/reasoning/llvq_table.py).

---

## 1. The question, and where it came from

[`STABILITY_STUDY.md`](STABILITY_STUDY.md) asked how far an input may move
before its address does, and got an answer nobody had asked for: for most of
the corpus the answer is **zero**. The input lies exactly on a bisector, two
lattice points are equally near, and the exact stability radius is 0 not
because the address is fragile but because it was never determined in the
first place.

`MASTER_PLAN.md` Phase 27 named the consequence as one of three candidates for
the next round, in a falsifiable form:

> The tie-break is nowhere documented as a *choice*; `scale_tie_sweep` shows
> scale 8 and 16 produce no ties at all; and the object worth addressing may
> be the class of tied points rather than one representative of it. The
> falsifiable form: if a tie-free scale leaves every measured figure of
> `LEAN_ADDRESS_STUDY.md` unchanged then the ties were never carrying
> anything, and if it does not then the address book has been reading the
> tie-break all along.

Two things had to be built before that could be tested. The first is the
**tie class** itself: `stability.py` could tell that a rival was equally near
(one pass over the 196,560 minimal vectors), but it could not say how many
rivals there were, or list them, or name the least of them. The second is a
statement of the rule the decoder follows, which existed only as three
unremarked lines of code.

The question was also reframed by the first measurement. A tie-free scale
turns out to be a *degenerate* scale (§6), so the comparison worth making is
not "scale 9 against scale 8" but "the decoder's tie-break against a stated
canonical one, at the same scale".

---

## 2. The tie class, enumerated exactly

The decoder searches Λ as `2 × 4096` **congruence branches**: a parity
`m ∈ {0, 1}` and a Golay codeword `w` fix, for each coordinate, which class
mod 4 the coordinate must lie in, and the branch is then the set of integer
points in those classes whose coordinate sum is `4m` mod 8. Inside a branch
the coordinates decouple except for that one sum condition, and that is what
makes the tie class computable in closed form.

Write `S_i` for the set of integers in coordinate `i`'s residue class nearest
to the input, and `k` for the number of coordinates with `|S_i| = 2`. Then:

| case | branch minimum | number of minimisers |
|---|---|---|
| `k ≥ 1` | the unrestricted minimum | `2 ^ (k − 1)` |
| `k = 0`, sum condition already holds | the unrestricted minimum | 1 |
| `k = 0`, sum condition fails | plus the least `±4` penalty | one per cheapest `(coordinate, direction)` |

The `2 ^ (k − 1)` is the whole content. Two integers in the same class mod 4
that are equally near differ by **exactly 4** — proved as
`nearest_in_residue_class_differ_by_four` — so raising a tied coordinate moves
the coordinate sum by 4, which is *half* the lattice's modulus and therefore
flips the sum condition. Exactly half of the `2 ^ k` choices satisfy it, and
`card_odd_subsets` / `card_even_subsets` prove that the halves are
equinumerous. No enumeration is performed to get the size of a tie class;
`tie_record` returns it from the branch data.

`tie_class` lists the members when there are few enough to list (and raises
rather than truncating when there are not), and the listing is required to
have exactly the length the closed form predicts — as an assertion inside the
function and as a test over the corpus.

Cost: one tie class is about a fifteenth of a second, so the whole corpus is
about half a minute. The readable per-branch statement, `branch_minimum`, is
kept and is what the second pass calls; the first pass runs the same
arithmetic with the denominators cleared so that it is integer arithmetic, and
`test_the_integer_pass_agrees_with_the_reference_branch_minimum` runs the
reference over all 8,192 branches and requires the same cost, the same size
and the same least member (directive D2).

---

## 3. The census

Whole development, scale 9, nothing sampled:

```bash
cd overlay
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import tie_break as tb
import json; print(json.dumps(tb.tie_census(), default=str, indent=1))"
```

| | measured |
|---|---|
| declarations | **2,135** |
| addresses decided by geometry alone (class size 1) | 547 |
| addresses decided by the tie-break (class size > 1) | **1,588** |
| the decoder's answer is a member of its tie class | **2,135 / 2,135** |
| the decoder's answer is the *least* member | 1,392 |
| addresses that move under the canonical rule | **743** |
| the read-back agrees between the two rules | **2,135 / 2,135** |
| largest tie class | **48**, at `GLM.Info.CompClass.magnitude` |
| worst squared distance to the lattice | **16** |

The class-size distribution, which is the closed form of §2 made visible:

| size | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 9 | 12 | 16 | 32 | 48 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| declarations | 547 | 670 | 15 | 246 | 4 | 178 | 142 | 3 | 93 | 141 | 94 | 2 |

The powers of two are the `k`-tied branches of §2; the sizes 3, 5, 6, 12 and
48 are what happens when several branches attain the minimum at once, or when
a sum repair is available in more than one place.

The last row of the table is worth its own line. **16** is exactly the square
of the covering radius, so the worst-placed declaration in the development
sits as far from the Leech lattice as any point in ℝ²⁴ can. That is the
condition under which ties are unavoidable, and it is the corpus's normal
state rather than an outlier.

---

## 4. The rule, stated clause by clause

`tie_break.RULE` transcribes what `nearest_lattice_point` does. Each clause is
a *choice*, in the strict sense that the objective is already attained by
every option it discards.

1. **Round half down, per coordinate** (`analogy._round_to_residue`). Of the
   two nearest integers in a residue class, take the smaller.
2. **Repair the sum at the earliest free coordinate, upwards.** When a coset
   representative fails the sum-mod-8 condition, move one coordinate by `±4`:
   the one with the least penalty, the earliest of those, upwards on a tie. A
   coordinate that was itself tied has penalty **0**, so the repair is free and
   lands on the *earliest tied coordinate*.
3. **Lexicographically least, across cosets.** Among the `2 × 4096` coset
   representatives of equal cost, keep the lexicographically least.

Clause 3 alone would be a canonical rule. What clauses 1 and 2 do is resolve
each coordinate *before* whole points are compared, so clause 3 ranges over
the representatives they produced and not over the tie class. `TieBreak.lean`
makes the gap exact: among the admissible choices, the lexicographically least
raises the **last** tied coordinate (`lexLeast_of_odd`), while clause 2 raises
the **first**, so as soon as two coordinates are tied the decoder's answer is
strictly larger than the least member (`decoder_not_lexLeast`).

The stated alternative is the obvious one: **take the least member of the tie
class**. It is well defined for the reason clause 3 is not enough on its own —
it is quantified over the *set*, so no enumeration order can appear in it
(`isLexLeast_unique`, `exists_isLexLeast`).

A worked pair, from the corpus. `GLM.Address.Quantiser.ne_of_far` has a tie
class of six points at squared distance 14. The decoder returns

```
(0, 0, 0, 0, 0, 0, 8, 0, 8, 0, 0, 8, 20, 0, 0, 0, 0, 0, 0, 52, 44, 0, 28, 8)
```

which is the **third** of the six in lexicographic order; the canonical rule
returns

```
(0, −2, 0, 0, 0, 0, 10, 2, 10, 0, 0, 10, 18, 0, 0, 0, 0, 0, 0, 54, 44, 0, 28, 10)
```

Both read back to the same feature vector, which is §5.

---

## 5. What the tie-break provably cannot touch

Every member of a tie class is a nearest lattice point, so it is within the
covering radius 4 of `9 ·` the feature vector in every coordinate. Since
`2 × 4 < 9`, `Address.readback_unique` applies, and
`TieBreak.lean`'s **`readback_of_tie_class`** concludes: two members of the
same tie class read back to the same feature vector. Not usually — always,
and for reasons that do not mention this corpus.

So *every sentence the machine speaks off an address is invariant under the
tie-break*, and so is everything derived from a single address alone. Measured
against the corpus rather than assumed: the read-back agrees for 2,135 of
2,135, and the conflation figures are identical under the two rules.

| figure | decoder's rule | canonical rule |
|---|---|---|
| distinct addresses | 1,995 | 1,995 |
| collision classes | 103 | 103 |
| declarations conflated | 243 | 243 |

That the *conflation* figures agree exactly is not a theorem — two
declarations could in principle share an address under one rule and not the
other — but it follows from the read-back result on this corpus, because
declarations with different feature vectors are separated by more than twice
the covering radius here.

---

## 6. What it can touch, and by how much

The figures the address study computes from **pairs** of addresses have no
such protection, and they do move.

```bash
cd overlay
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import tie_break as tb
import json; print(json.dumps(tb.canonical_separation(), default=str, indent=1))"
```

743 of 2,135 addresses are different under the two rules — 34.8 % of the
corpus — and this is what changes:

| figure | decoder's rule | canonical rule | difference |
|---|---|---|---|
| nearest neighbour shares a file | **525** | 524 | 1 |
| nearest neighbour is cited, either way | **102** | 101 | 1 |
| mean d² within a file | `221467408/38159` ≈ 5804.19 | `221460928/38159` ≈ 5804.02 | ≈ 0.003 % |
| mean d² across files | `7356109944/1119943` ≈ 6568.29 | `7355577656/1119943` ≈ 6567.82 | ≈ 0.007 % |

So the falsifiable claim of Phase 27 comes out **almost, but not exactly, in
favour of the ties carrying nothing**. A third of the addresses are chosen by
an implementation detail; not one conclusion of
[`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md) depends on which choice is
made, because the two separation counts move by one declaration each out of
2,135 and the mean squared distances by three parts in a hundred thousand —
against a same-file rate that beats its controls by a factor of about fifteen.
But the figures are not *literally* invariant, and a study that quoted them to
the last unit would be quoting the tie-break. They are quoted with that
caveat now.

---

## 7. Why not simply avoid the ties?

Because the only tie-free scales are the ones at which the lattice does
nothing. `scale_tie_table` runs the census at every scale from 1 to 24 on the
first 40 declarations and reports, beside the tie count, how often the decoder
moved the point at all:

| scale | tied of 40 | moved by the decoder | largest class | worst d² |
|---|---|---|---|---|
| 1, 3, 5, 7, **9**, 11, 13, 15, 17, 19, 21, 23 | 28 | 40 | 32 | 16 |
| 2, 6, 10, 14, 18, 22 | 40 | 40 | 48 | 16 |
| 4, 12, 20 | 18 | 18 | 48 | 16 |
| **8, 16, 24** | **0** | **0** | 1 | 0 |

The tie-free scales are exactly `{8, 16, 24}` and the degenerate ones are
exactly `{8, 16, 24}`; `tie_free_and_working` is **0**. The reason is a
theorem the development already had: `Address.eightZ_mem_leech` says
`8ℤ²⁴ ⊆ Λ`, so at a multiple of 8 the input is *already* a lattice point,
`Quantiser.fixed` returns it unchanged, and the "Leech address" is the feature
vector relabelled. Ties disappear because the decoder has stopped deciding
anything.

The other rows are structure rather than noise. A scale `≡ 4 (mod 8)` ties
less often than an odd scale, and a scale `≡ 2 (mod 4)` ties for every
declaration in the sample; what an odd scale buys is that the input is never
congruent to the lattice in a way that removes the decoder's work. Scale 9 is
the smallest odd scale clearing `2ρ < scale`, which is why
[`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md) §4 chose it, and this table
says that choice cost nothing in tie rate that a different odd scale would
have saved.

---

## 8. What is proved, and what is only measured

Proved, in [`RequestProject/GLM/TieBreak.lean`](../RequestProject/GLM/TieBreak.lean),
against no assumption about this corpus:

| Lean name | what it says | what it licenses here |
|---|---|---|
| `Nearest` | the tie class of a nearest-point map | §2: the object being chosen from |
| `mem_nearest` | a quantiser's answer lies in it | §3: the check the census runs |
| `dist_eq_of_mem_nearest` | its members are equidistant | §2: nothing in the definition separates them |
| `quantiserOfChoice` | *any* selection from it is a quantiser | §4: the tie-break is data, not a consequence |
| `isLexLeast_unique` | a set has at most one least member | §4: the stated rule is well defined |
| `exists_isLexLeast` | a finite nonempty set has one | §4: and total |
| `sum_raise_mod_eight` | raising a coordinate flips the sum mod 8 | §2: admissibility is a parity |
| `card_odd_subsets`, `card_even_subsets` | the parities split a power set evenly | §2: the `2 ^ (k − 1)` |
| `lexLeast_of_odd` | the least admissible choice raises the *last* tied coordinate | §4: what the decoder should do |
| `decoder_not_lexLeast` | raising the *first* is strictly larger | §4: what it does instead |
| `nearest_in_residue_class_differ_by_four` | two nearest integers in a class mod 4 differ by 4 | §2: a coordinate tie has exactly two options |
| `readback_of_tie_class` | a tie class reads back to one feature vector | §5: the invariance |

Measured, and true of this corpus only: every count in §3, §5 and §6, and the
sweep of §7. In particular "the conflation figures are identical" is a
measurement, not a corollary, and "the tie-free scales are the multiples of 8"
is proved only in the direction that matters (`eightZ_mem_leech` forces
degeneracy at a multiple of 8); that no *other* scale in 1–24 is tie-free is a
measurement on 40 declarations.

---

## 9. What this licenses, and what it does not

It licenses saying that the address book is **not** reading an implementation
detail in any way that changes a conclusion, and saying exactly how far that
holds: completely for anything read off one address, to within one declaration
in 2,135 for the neighbour tests.

It does not license calling the address canonical. It is not: 743 of 2,135
addresses would be different under a rule that is no worse and is better
specified. The honest description of the current address book is *the tie
class, plus the decoder's inherited selection from it*, and the class is now
the computable object it should always have been — so a future round that
wants a canonical address book can have one for the cost of one pass, and
knows in advance which four figures it would have to restate.

It also does not license the tempting simplification of addressing the
*class* instead of a member. `tie_class` shows why: the classes run to 48
members here, they are not all the same size, and a set-valued address would
have to define its own equality before any of the pairwise statistics could be
computed at all.

---

## 10. Reproducing every number here

```bash
cd overlay

# the report, at the size a report can afford
PYTHONPATH=. python3 GLM.py -q "report tiebreak" --verify-tct

# §3, the whole corpus
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import tie_break as tb
import json; print(json.dumps(tb.tie_census(), default=str, indent=1))"

# §5 and §6, both address books, figure by figure
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import tie_break as tb
import json; print(json.dumps(tb.canonical_separation(), default=str, indent=1))"

# §7, every scale from 1 to 24
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import tie_break as tb
import json; print(json.dumps(
    tb.scale_tie_table(scales=tuple(range(1, 25)), sample=40),
    default=str, indent=1))"

# the tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_tie_break.py -q
```

The Lean file builds with the rest of the development:

```bash
cd .. && lake build
```
