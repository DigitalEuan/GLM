# The LLVQ table: the quantiser's search, replaced by a lookup

*The Leech quantiser is the hot path of every address, and it was a scan: for
each of the two congruence classes of Λ, form the cost of all 4,096 Golay
codewords and keep the cheapest. This study replaces the scan by the MOG's own
structure — a 16-entry column table, the 64 hexacode words, 128 classes of 32
— and measures what that costs, what it saves, and whether a single answer
anywhere moved. None did.*

Code:
[`overlay/glm_universal/reasoning/llvq_table.py`](../overlay/glm_universal/reasoning/llvq_table.py).
Query: `report llvq`.
Formal development:
[`RequestProject/GLM/LLVQTable.lean`](../RequestProject/GLM/LLVQTable.lean).
Tests: `overlay/glm_universal/tests/test_llvq_table.py`.
The reference it must agree with:
[`overlay/glm_universal/reasoning/analogy.py`](../overlay/glm_universal/reasoning/analogy.py)
`nearest_lattice_point`.

---

## 1. The question, and why it was still open

`MASTER_PLAN.md` Phase 24 named this first among the candidates for the next
round, and the original to-do list had asked for it in the form

> **`O(1)` LLVQ Lookup Table:** the Leech Lattice Vector Quantization module
> currently classifies coordinates by shell, but the constant-time `O(1)`
> lookup table utilizing the first few binary digits remains unbuilt.

[`reasoning/llvq.py`](../overlay/glm_universal/reasoning/llvq.py) said the same
thing about itself, in its own docstring: it classifies a vector by *shell*
without a codebook, and it does not build the table.

Two earlier rounds had already been at the same wall from other sides.
[`reasoning/fwht_decode.py`](../overlay/glm_universal/reasoning/fwht_decode.py)
showed that the 4,096 coset costs are one Walsh–Hadamard transform — and
measured that this is *not* a speed-up for this code, because `n = 2k` makes
the transform cost exactly what the direct summation costs (49,152 either
way). Its constant-time tier, `certified_lookup`, is a genuine `O(1)` route
but a *conditional* one: it fires when the reliability profile is flat enough
for the code's minimum distance to settle the question, and the profile the
Leech decoder actually produces is not. Measured here, on the deltas the Leech
step generates rather than on synthetic profiles, that certificate fires on
**0 of 200** sampled vectors. A tier that never fires on the real input is not
the table.

So the question this round asks is the narrow one: *is there a route that
opens only a small part of the code on every input, and returns exactly what
the scan returns?*

---

## 2. The table

Under the MOG alignment the package already carries
([`substrate/mog.py`](../overlay/glm_universal/substrate/mog.py)), a 24-bit
word is a 4 × 6 grid. Each column is a 4-bit value, and a column has three
readings: its **GF(4) label** (the XOR of the row labels of its set cells), its
**parity**, and its **top bit**. Three facts, all checked over all 4,096
codewords by `characterisation_report()`:

1. the six column labels of a Golay codeword form a **hexacode word**;
2. the six column parities are **all equal**, to one bit `p`;
3. the **top row's parity** is that same `p`.

| checked over all 4,096 codewords | failures |
|---|---|
| the column labels form a hexacode word | 0 |
| the six column parities agree | 0 |
| the top row carries the column parity | 0 |
| a class rebuilt from the table is the class the code has | 0 |

and the count is what turns those three necessary conditions into a
*characterisation*: 64 hexacode words × 2 parities = **128 classes**, each of
**32 codewords**, and 128 × 32 = 4,096 with nothing left over. There is no room
for a word that satisfies the three conditions without being a codeword.

Inside a column, `(label, parity, top bit)` determines the 4-bit pattern
uniquely — 4 × 2 × 2 = 16 keys for 16 patterns — so the lookup table is
`PATTERN_TABLE`, **16 entries**, and a class is six of its entries plus one
parity constraint on the top bits. That is the whole of the "first few binary
digits" the to-do list asked for, made precise: the label and the parity say
*which* patterns a column may use, and the top bit is the one remaining
digit.

---

## 3. The class minimum is six comparisons

The reference decoder minimises, over the code,

```
cost(w) = base_cost + Σ_{i ∈ w} delta_i        (+ a ±4 repair, ≥ 0, when the
                                                 sum-mod-8 condition fails)
```

which is linear in the word plus a nonnegative repair. Inside a class the
choice is one top bit per column, so the linear part is a six-term min-sum
under one parity constraint, and the answer is the classical one: take the
cheaper pattern in every column, and if the resulting parity is wrong, pay the
**smallest of the six differences**.

That is not asserted here — it is
[`LLVQTable.lean`](../RequestProject/GLM/LLVQTable.lean):

| theorem | what it says |
|---|---|
| `cost_eq` | a choice costs the greedy choice plus the gaps of exactly the columns where the two differ |
| `isLeast_cost_of_parity_eq` | greedy parity right: the class minimum is `∑ lo`, and the greedy choice attains it |
| `isLeast_cost_of_parity_ne` | greedy parity wrong: the class minimum is `∑ lo + gap i₀` at a least-gap column, attained by flipping that one top bit |
| `card_parity_class` | the choices of `n` top bits with a fixed parity number `2^(n−1)` — 32 at `n = 6` |
| `isLeast_of_bounded_search` | branch and bound is exact: with `f ≤ g`, an incumbent best in the expanded part and every unexpanded member already at `g w` under `f`, the incumbent is best in the whole set |

Both minimum statements are `IsLeast`, so each carries the attainment and the
bound at once. The last one is why the decoder may stop: `g` is the cost with
the repair, `f` the cost without it, and the repair is nonnegative, so a class
whose minimum already exceeds the best total found so far contains nothing
better and is never opened.

`test_llvq_table.py` checks the formula against brute force on **all 128
classes** for two profiles, and the least class minimum against the true soft
decoding of the code.

---

## 4. What it costs, measured

The scan's cost is a constant of the code: `∑_w |supp(w)| = 24 · 2^11 =`
**49,152** additions per congruence class, so **98,304** and **8,192** codeword
costs per call. The table route's cost is data-dependent — its worst case is
the whole code — so the honest figure is the measured one, and
`search_cost_report()` counts it inside the run.

Over 40 deterministic rational 24-vectors (`seed 20260901`; the package draws
no random numbers):

| figure | table route | the scan |
|---|---|---|
| codeword costs formed, per call | `484/5` = **96.8** | 8,192 |
| classes opened, per call | `121/40` = **3.025** | (256 available) |
| additions, per call, table build included | `27579/20` ≈ **1,379** | 98,304 |
| worst call in the sample | 448 words, 14 classes | 8,192 words |
| ratio | **84.6×** fewer words, **71.3×** fewer additions | — |

---

## 5. Every address in the corpus, unchanged

The subtractive test Phase 24 asks for: the address book is what the quantiser
is the hot path *of*, so the table earns the hot path only if the corpus comes
out unchanged. `corpus_report()` decodes every declaration of the Lean
development both ways and compares the points.

| figure | value |
|---|---|
| declarations decoded both ways | **1,270** |
| addresses unchanged | **1,270** |
| addresses changed | **0** |
| codeword costs formed per call, on this population | `9600/127` ≈ **75.6** |
| classes opened per call | `300/127` ≈ **2.36** |

Beside it, `agreement_report()` compares the two routes point for point —
point, squared distance, Leech class, norm, `exact_hit` and `is_2a_axis` — over
three populations: the deterministic sweep, the carriers the physics and
element registers actually hold, and seven boundary vectors (the origin, all
halves, all ones, all twos, a ramp, one large coordinate, a lattice point).
**107 vectors, 0 mismatches.**

`reasoning/lean_address.py::quantise` now decodes through the table. The scan
is **not** deleted: it stays in `analogy.py` as the thing to agree with, which
is what makes the agreement figure a comparison rather than a tautology.

### One bug the agreement test found

The first version of the table route disagreed with the scan on exactly one
vector out of 97 — the physics carrier `bekenstein_hawking_entropy`, where two
distinct Leech points sit at the same squared distance 13 and the tie is broken
by the repair. The scan picks the cheapest `±4` repair by `(penalty, coordinate
index)`; the column-wise version was picking by penalty alone and keeping the
first coordinate it met inside a column, which is coordinate 19 where the scan
takes coordinate 12. Both answers are nearest points; only one is *the* answer
the address book already contains. The fix is one comparison, and the reason it
was caught is that the agreement is required to be exact rather than
approximate.

---

## 6. Is it `O(1)`?

Honestly: **constant-bounded, not constant.** The table work is fixed — 96
column costs, 128 class minima, none of it growing with the lattice — and the
expansion is data-dependent with a worst case of the whole code. What the
measurement says is that on every population tried here the expansion opens two
or three classes of 128 and forms fewer than a hundred of 8,192 codeword costs,
and that the answer is the scan's answer every time.

Quoting "`O(1)`" without that measurement would be exactly the kind of claim
directive D6 exists to prevent, so the module's docstring, the report and this
document all say the same thing: the figure is measured, and the worst case is
named.

---

## 7. What recomputes each figure

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report llvq" --verify-tct
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_llvq_table.py -q
PYTHONPATH=. python3 -c "from glm_universal.reasoning import llvq_table as lt; \
    print(lt.corpus_report())"          # §5, the whole corpus, ~3 minutes
PYTHONPATH=. python3 -c "from glm_universal.reasoning import llvq_table as lt; \
    print(lt.search_cost_report(samples=40))"     # §4
PYTHONPATH=. python3 -c "from glm_universal.reasoning import llvq_table as lt; \
    print(lt.agreement_report(samples=40))"       # §5, the 107 vectors
cd .. && lake build RequestProject.GLM.LLVQTable  # §3
```
