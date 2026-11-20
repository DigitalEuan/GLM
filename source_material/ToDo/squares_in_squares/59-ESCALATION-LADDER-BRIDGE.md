# Run 96 — the honest score, the window above 1000, and the 7-rung bridge

Run 95 closed the census's own row. This run asks the three questions that closing leaves
behind, and answers them the same way it answers everything else: exactly where the object is
exact, measured where it is not, and never by moving a row.

1. **The honest score.** Spin every exact grammatical family now on `glm_wheels.py` against the
   delivered table at the same `N`: does *any* generated sentence achieve `L` strictly smaller
   than the row it shares a count with? **No — 0 of 364.**
2. **The window above.** Spin the same families past `n = 1000`, where the delivered table has no
   row and no float table reaches: exact, zero-drift container sides, voids and contact counts.
3. **The bridge.** Map what we hold onto the seven-rung perception-and-escalation ladder, name
   the blindnesses with the numbers that measure them, and say which grammatical move is next.

Nothing here changes a row, touches `submission.csv`, or claims a score. The Lean files named in
§6 are conceptual anchors only, never a build dependency.

## 1. The family spin against the delivered table: 0 of 364

`scripts/family_spin.py --calibrate` spins five families — Ridge, Strip, Diamond
(Product-minus-collision), Ring and Staircase — over Q(√2), Q(√5), Q(√7) and three rational-t
words, and compares each member with the delivered row at the *same* `N`:

* the member's side `L` is exact `Quad` arithmetic, no float and no tolerance;
* the table's side is recomputed from the delivered 12-dp pose as an exact rational input —
  every centre a `Fraction`, each square's extent `(|cos| + |sin|)/2` with the cosine and sine of
  the row's exact rational angle at 70 digits — so both sides of the comparison carry ~1e-69 of
  error and every gap below is decisive;
* a gap under `1e-6` is **parity**, not a win: the table is a 12-decimal pose held at ~2e-9
  clearance, and that is its own tolerance, not a packing difference.

| | |
|---|---:|
| exact members with a delivered row at the same `N` | **364** |
| members whose `L` is strictly smaller (gap > 1e-6) | **0** |
| parity (the delivered row *is* this sentence, to ≤ 1.7e-9) | **6** |
| behind | **358** |

The six parity rows are the ones the grammar was built from: `n = 5` (the 45° ridge, which is also
Strip `S(1,1)`), the three diamond atoms `n = 10, 19, 40`, and the ring at `n = 18`. They do not
*beat* the table — they agree with it to the table's own pose tolerance (`+1.26e-9` at `n = 5`,
`+1.59e-9` at `n = 18`, `+1.71e-9` at `n = 40`), which is the honest reading of "the grammar
reproduces this row".

Every other member is behind, and the shortfall **grows** with the count:

| word | field | `N = 5` | `N = 257` (k = 8) | `N = 901` (k = 15) |
|---|---|---:|---:|---:|
| 45° | Q(√2) | parity | −0.171573 | −0.186291 |
| Seventh `(√7/4, 3/4)` | Q(√7) | **−0.001391** | −0.172963 | −0.187682 |
| `t = 1/2`, `t = 1/3` | Q (rational) | −0.007179 | −0.178752 | −0.193470 |
| Slope 2:1 | Q(√5) | −0.038249 | −0.209822 | −0.224541 |
| census `((1+√7)/4, (√7−1)/4)` | Q(√7) | −0.048822 | −0.220395 | −0.235114 |
| `t = 1/5` | Q (rational) | −0.057599 | −0.229172 | −0.243891 |

(columns are the `m = 1` rungs; `table − L`, exact `Decimal`. The closest single member anywhere
is the Seventh at `n = 5`, behind by **0.001391**; the largest shortfall is `t = 1/5` at `N = 903`,
behind by `1.758584`.)

And the score arithmetic says the same thing in the units the leaderboard uses. At `N = 901` the
45° ridge is `L = 30 + ½√2 = 30.70711` against the delivered `30.52082`: row scores
`+0.023002` against `+0.016796`, i.e. **splicing it in would raise the total by 0.0062**
(`N = 902`: `+0.0293`; `N = 903`: `+0.0528`). So the answer to "is there any generated exact
sentence strictly smaller than a delivered row at the same `N`" is *no*, and it is not a near
miss: the gap is a systematic term, not noise.

**Why, in algebra.** Every family here is *single-word*: all its tilted squares share one word
`(c, s)`. The ridge's side is `L = 2k + w` with `w = m·min(1/(c+s), c+s)`, and at `m = 1` that is
`min(x, 1/x)` for `x = c + s`, which is minimised at `x = 1` — the 45° word, `w = ½√2 = 0.707107`.
So the best any single-word, four-block sentence can do at `N = 4k² + 1` is `2k + 0.707107`, while
the delivered rows at those counts sit at `2k + O(1/k)` (0.186 at `k = 15`). The table does not pay
a seam; a single-word sentence must. `m = 2` and `m = 3` widen the seam by exactly `m·w₁` — 1.414
and 2.121 of side for one and two extra squares — so they are strictly worse in density, which the
table above shows at `N = 6, 7` and `N = 258, 259`.

That is the whole honest score question, answered: **the 1000-row table is not reproducible by this
alphabet.** 553 of its rows beat the grid and, by run 76/77, the 553 are exactly the rows that
contain a rotated square; 447 axis rows sit at `⌈√n⌉`. Our grammar explains the *sides* of 576 of
the 1000 rows (447 grid, 99 Q(√2)-pose, 18 Q(√2)-side, 5 Q(√7)-side, 3 Q(√5)-side, 4 rational-t)
and constructs six of them as sentences. The other **424** rows have no field class at all — 42.4 %
of the table lives outside the alphabet (§5).

## 2. The window above 1000: exact rows where the table has none

`scripts/family_spin.py --beyond …` runs the families past `n = 1000`, gated exactly — no float, no
polish, no drift (`gate_L == L` on every rung below). These are the rows the 12-decimal table
cannot express at all.

**Strip / 45° ridge**, `N = 4k² + m`, `L = 2k + m√2/2`:

| `k` | `m` | `N` | `L` | void `L² − N` | contacts | `L/√N − 1` |
|---:|---:|---:|---|---:|---:|---:|
| 16 | 1 | 1025 | `32 + ½√2` = 32.707107 | `−½ + 32√2` = 44.754834 | 3724 | 0.021598 |
| 16 | 2 | 1026 | `32 + √2` = 33.414214 | `64√2` = 90.509668 | 3723 | 0.043176 |
| 16 | 3 | 1027 | `32 + 3/2√2` = 34.121320 | `3/2 + 96√2` = 137.264502 | 3724 | 0.064733 |
| 22 | 1 | 1937 | `44 + ½√2` = 44.707107 | `−½ + 44√2` = 61.724834 | 7228 | 0.015808 |
| 22 | 2 | 1938 | `44 + √2` = 45.414214 | `88√2` = 124.450793 | 7227 | 0.031608 |
| 22 | 3 | 1939 | `44 + 3/2√2` = 46.121320 | `3/2 + 132√2` = 188.205452 | 7228 | 0.047401 |

At `N = 1025` the grid is `⌈√1025⌉ = 33`, so the exact sentence at `32.707107` **beats the grid by
0.292893** — the same one-diamond trade as `n = 5`, now at a count where the table has nothing. The
contact counts are the gate's own, exact: `3724` at `k = 16` and `7228` at `k = 22`, and the void
is the exact `Quad` `−½ + 4k√2`.

**The same rung over every field** (`k = 16`, so `N = 1025` for all of them; `m = 1`):

| word | field | `L` | `L` (dec) | contacts |
|---|---|---|---:|---:|
| 45° | Q(√2) | `32 + ½√2` | 32.707107 | 3724 |
| Seventh | Q(√7) | `38 − 2√7` | 32.708497 | 3724 |
| `t = 1/2`, `t = 1/3` | Q | `229/7` | 32.714286 | 3724 |
| Slope 2:1 | Q(√5) | `32 + ⅓√5` | 32.745356 | 3724 |
| census | Q(√7) | `32 + 2/7√7` | 32.755929 | 3724 |
| `t = 1/5` | Q | `557/17` | 32.764706 | 3724 |

The ordering is not a coincidence and not a search: `w = min(x, 1/x)` with `x = c + s`, so the 45°
word is the *field-theoretic optimum of the whole ridge family* (`x = 1`), and every other word
pays `x + 1/x − 2` of extra side. `t = 1/2` and `t = 1/3` are the same square (mirror words), so
they give the same side to the last digit — an honest duplicate, not a second rung.

**The staircase does not scale.** This is the sharpest negative of the run, and it is a *structure*
result, not a search failure. The 149-square sentence exists at `k = 5` and at no other `k`: the
brick wall's column count grows at ≈ `8k/3` while the box's `u`-window grows at `2k`, so from
`k = 6` the wall is longer than the seam it fills, and the bricks cut into the frame itself:

| `k` | columns | `N` | gate violations | worst clearance | bbox `L` | law `2k + 1 + 2c` |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 12 | 149 | **0** | **0** | 12.822875 | 12.822875 |
| 6 | 15 | 203 | 38 | −0.812193 | 14.822875 | 14.822875 |
| 7 | 17 | 263 | 56 | −1.000000 | 16.957880 | 16.822875 |
| 8 | 20 | 333 | 94 | −0.822876 | 20.486524 | 18.822875 |
| 10 | 25 | 495 | 179 | −1.065861 | 26.632309 | 22.822875 |
| 12 | 31 | 691 | 212 | −1.065861 | 33.689520 | 26.822875 |
| 15 | 39 | 1043 | 236 | −0.968627 | 43.363826 | 34.822875 |
| 18 | 47 | 1467 | 256 | −1.031373 | 53.038171 | 38.822875 |
| 21 | 55 | 1963 | 297 | −1.114378 | 62.712517 | 44.822875 |

At `k = 6` no slide of the wall helps: of 25 gauges `u₀ + i/4`, `i = −12 … 12`, **none** gates. So
the staircase is a *reading of one row* — the census's 151 — and not a family that scales; its
`N(k)` law is real, its side law is k = 5 only. (The honest consequence for §6: the 151 that this
grammar reproduces is a point, and the table's own 151 is a 12-dp pose that overlaps at 1e-9.)

**Ring and Diamond, for completeness.** The ring closes at `k = 1` only (`N = 18`, `L = 7/2 + ½√7`,
26 contacts) and refuses at `k = 2, 3` by `ring_chain_adrift` (the pinwheel's closure slack
`−13/4 + (4k−1)/4·√7`), which is the run-94 result reproduced through the spin. The diamond atoms
are `n = 10` (`3 + ½√2`, 11 contacts), `n = 19` (`3 + 4/3√2`, 31) and `n = 40` (`4 + 2√2`, 98);
they are atoms, not a `k`-law, so they contribute no rung above 1000.

**What this is and is not.** It is exact: six rows above 1000 with `n` up to 1939, zero drift,
`L` and void and contacts in the field. It is **not** a score: the delivered table is scored on
`n ≤ 1000` only, and nothing here is spliced. Its depth `L/√N − 1` is 0.0158–0.0216, an order of
magnitude worse than the table's rows below 1000 — because it is a seam construction, not a
relaxation (§1, §5).

## 3. The board, in one table

| question | answer |
|---|---|
| Any exact sentence with `L` below the delivered row at the same `N`? | **No. 0 of 364.** 6 at parity (the known atoms), 358 behind, shortfall growing with `N`. |
| Splicing them would change the score? | It would **raise** it: `+0.0062` at `N = 901`, `+0.0528` at `N = 903`. No row claimed. |
| Best single-word side at `N = 4k²+1` | `2k + ½√2`, and the 45° word is provably optimal inside the family (`min(x,1/x)` at `x=1`). |
| Exact rows above 1000 | Six, `N = 1025 … 1939`, zero drift, contacts 3723–7228, and they beat the grid by 0.293 at `N = 1025`. |
| Does the staircase scale? | **No.** k = 5 only: at k ≥ 6 the wall is longer than the seam and the sentence collides (38–297 violations, no gauge in 25 tested). |
| The 66-class chord check | **66 of 66** classes `no-pair`; free spans ≤ 0.822876 < 1 (doc 58 §7.2). |

## 4. The 7-rung bridge

The attached ladder is seven rungs of *representation* — what each layer can perceive, and what it
is structurally blind to. Mapping our instruments onto it is the useful reality check, because a
rung we cannot reach is a kind of blindness we can name instead of guessing at.

| rung | what it is | what we hold here | what it cannot see for us |
|---|---|---|---|
| **1. Substrate** | 24-bit Golay parity, weight-3 syndrome | the leech 24-pocket address (PL-25…PL-34): 1000 rows → 50 addresses, entropy 2.811 of 12 bits, snapped to codewords; and the measured retraction that **87 % of its "signal" was the rotation flag** | `0` vs `2` share a parity word, and the address is a *shadow* of the row: after the run-33 instrument audit, the mutual information of the decisiveness gap with "beats" **given** rotation is 0.0000 — nothing beyond rotation |
| **2. Integer** | `⌊q⌋`, integer lattices | the axis layer: **447 rows certified at clearance 0 with side exactly `⌈√n⌉`** (419,281 contacts), and the staircase's odd grid on two lattices offset by `2c` | `0` vs `1/2`, and every tilted packing: 87/87 rotated Q(√2) poses are illegal lattice points, so an integer view cannot even *see* the 553 rows that beat the grid |
| **3. Rational / algebraic** | exact `Fraction`, `Quad(d)`, t-basis words | **our home**: Q(√2), Q(√5), Q(√7), rational-t; the gate, the cage, the chord union, 1169 algebraic certificates, and the lossless ceiling — nothing written in the field is lost (`entryResolution_rational`) | the field is *closed* under our constructions: it can only ever produce the words we name. A pose whose cosine is not in `Q(√d)` is not a state the rung can hold (§5) |
| **4. Scan / value** | 12-dp storage, float SAT, `finalize` +2e-9 | the delivered table itself, and the exact statement that its `n = 5, 10, 18, 19, 40` rows agree with our sentences to 1.3–1.7e-9 — the rung's own noise floor | tangency: `scan_blind_to_clearance`. The mixed 151 is exactly this failure — the table's own pose overlaps our exact 149 by **−2.365e-9** |
| **5. Combinatorial topology** | WL signatures, contact graphs, Laman counts | contact counts (26 / 98 / 449 / 451 / 3724 / 7228), declared tangencies, the 24-brick walk, `|E|/n ≈ 0.86` thin graphs | rigidity: our graphs are too sparse for `2n−3`, so topology *classifies* a sentence we already have and cannot *propose* the next one |
| **6. Griess & Conway** | 2A axial algebra, Co₀ orbit labels | **nothing.** The 24-pocket address is a Golay shadow, not a Co₀ label on an exact carrier | everything: we have no exact carrier to label, so this rung is empty for us rather than blindness |
| **7. Certificate & proof** | minimal polynomials, the sequential climb | **our strongest rung**: exact gate + four witnesses; the cage as a proof of *infeasibility*; the chord union as a proof that no pair is 1 apart; refusals that name the rung that failed (`staircase_layer_gap`, `ring_chain_adrift`, `ring_side_mismatch`) | it can only certify what a lower rung could name. `climb_answers_least` is the discipline we keep; `climb_principled` is what our refusals do — but a principled refusal is still a refusal |

**What we have genuinely obtained** (the list I would defend):

* exact, zero-drift, multi-witness sentences for the table's atoms (`n = 5, 10, 18, 19, 40`) and
  for **149 and 150** squares at `L = 23/2 + ½√7` — with 451 contacts and clearance exactly 0;
* a *refusal* of the 151st square that is a proof inside `Q(√7) ∪ Q_Pyth`, uniform over all 66
  rotation classes, with no scan and no tolerance;
* the *reason* the table's 151 exists anyway: two squares at 0.6148 rad, a word outside the field;
* a family law `L = 2k + w` over four fields, with the 45° word optimal *by proof*;
* six exact rows above 1000 where the table has none, `L`, void and contacts all in the field;
* the honest score: 0 of 364, and the algebra of why (the seam width `w ≥ ½√2`).

## 5. Where we are still blind, with the numbers

**(i) Non-field transcendentals — the table's own escape.** The census's last two squares sit at
`19211307153/31250000000` rad = 0.614761828896. Recovering `cos` and `sin` in Q(√7) at heights up
to 4096 gives `868927/1024 − 656073/2048√7 ≠ 1`, and no `t` with denominator ≤ 1024 makes it
Pythagorean. So it is *not a word of any field we hold*, and everything about those two squares is
a measurement, never a certificate. This is the honest limit of the "151 is impossible" statement:
it is a proof that no `Q(√7) ∪ Q_Pyth` word places the 151st square at that side, plus the measured
fact that the table's own pose overlaps by `−2.365e-9`. It is **not** a proof that 151 is
impossible for squares. The difference matters and is stated everywhere.

**(ii) One word per family — the structural blindness.** Every family we have fixes a single word
for all its tilted squares. That is what makes the side a field element, and it is also what caps
it: `L = 2k + w` with `w ≥ ½√2`, so a single-word sentence can never reach the table's `2k +
O(1/k)`. The table's rows are *relaxed*: 424 of 1000 sides have no field class at all, and the 553
beating rows are exactly the ones carrying a rotated square at some angle of their own. We can
explain 576 rows' sides and construct 6 of them. The 424 are the measure of the blindness.

**(iii) Multi-angle coupling.** The ring's refusal is the cleanest example: its pinwheel closure has
`u`-separation exactly 1 at every `k` while its `v`-offset is `2·p5·v + 2`, which grows by `√7` per
`k` — so the sentence closes at `k = 1` and refuses at `k ≥ 2` by a slack `−13/4 + (4k−1)/4·√7`.
The drift is *not* a bug: it is the coupling of two different contact directions in one word. The
staircase's wall has the same shape (its columns fit `k = 5` and not `k = 6`). And the census's own
151 has **two distinct tilt angles** among its 26 tilted squares. Every one of those is a sentence
whose closure needs *two* words.

**(iv) Why exact sentences have not beaten the table.** Three reasons, in order of weight: the
seam (§1 — a single-word sentence pays `w ≥ ½√2`); the alphabet (§5(ii) — 42.4 % of the table's
sides are not in a field); and the rung (§4 — the table is a rung-4 object held at 2e-9, so its
"poses" are not exact sentences at all, as the `−2.365e-9` overlap shows).

## 6. The exact grammatical move next: the two-word closure

The move is not a bigger search. It is one production in the grammar: **a second word in the same
sentence**, declared by tangency, whose closure condition is a polynomial identity in both words.

The template already exists in the ring. Its pinwheel closes when the closure contact's `v`-offset
vanishes, and that offset is affine in `√7` with a `k`-term:
`2·p5·v + 2 = 5/4 − (4k−1)/4·√7`. One word cannot cancel that. A second word `(c₂, s₂)` can, if the
tilted square that carries the `v`-offset is allowed its own word and the contact is *mixed*
(tilted₁ against tilted₂ along tilted₁'s axis, `|(q − p)·u₁| = 1`) instead of same-word
(`= 1` in both). The closure then reads

    s₁ · (2(c₁ − s₁) − 1)  +  s₂ · λ(c₁, s₁, c₂, s₂)  =  0

— a two-variable identity whose solutions are a *finite* set of field word-pairs, not a scan. The
concrete first target is the ridge: keep the 45° blocks (`k = 16`, `N = 1025`, `L = 32 + ½√2`,
3724 contacts) and put the bar at a **second** word `θ₂` in the seam, then a third square at `θ₁`
in the void the bar leaves. If a pair closes at `L < 2k + w(θ₁)` for the same `N`, the seam
ceilings of §1 break; if no pair closes below it for every `k ≤ 8` and every word pair in
`Q(√2) ∪ Q(√5) ∪ Q(√7) ∪ Q_Pyth`, then the single-word ceiling is a theorem of the family's
topology and the next move is the *relaxed* rung (the table) rather than grammar.

That is the falsifier, and it is decidable with what is already here: `staircase_cage` and
`staircase_chords` answer feasibility questions for **any** word pair in one field, exactly, and
`Q.gate` is the arbiter of a two-word sentence already (the ring and the staircase are both
two-word sentences: axis + one tilted). What is missing is the *builder* — a sentence whose tilted
squares carry two different words — and that is one production, not a new engine.

The other half of the move is honesty about rung 4: the 424 continuous rows are not grammar's
failure to try harder, they are a *different object*. Naming them as the relaxed rung, and
measuring any two-word sentence against them at the same `N`, is the only comparison that can
settle whether grammar can ever reach the table's frontier.

## 7. Verification

* `glm_wheels.py --selftest` — **27 controls, exit 0** in **1 m 48.7 s** (run 95: 1 m 50 s), i.e.
  the chord change and the 66-class check cost the suite nothing; control 27 now also asserts that
  the union span exceeds the largest single-block chord, which is the quantity the verdict rests
  on; controls 25 and 26 are unchanged.
* `glm_wheels.py --audit` — the bytecode float audit of every decision function.
* `glm_wheels.py --chord-spin` — **66 classes, 66 `no-pair`**, 2 m 02 s as its own run, ledger
  `workspace/push/chord_spin.json`; deliberately outside the selftest.
* `family_spin.py --calibrate` — 364 members, 0 beats, 6 parity, 358 behind, ledger
  `workspace/push/family_spin.json`; `--beyond strip|words|stair` — the six rungs above 1000 and
  the staircase's refusal, all gated.
* `glm_wheels.py` — spin: spatial **48/48 certified** (`Ring k=1`, `Staircase k=5`).
* `grammar_induction.py --selftest`, `qsqrt2.py --selftest`, `field_triage.py --selftest`,
  `scripts/record_guard.py` — all OK.

Nothing touches `submission.csv`; no row changed; no score is claimed. The Lean references
(`RequestProject/GLM/Escalation.lean`, `EscalationLoop.lean`) are conceptual anchors named for the
ladder's rungs — `entryResolution_mono`, `entryResolution_rational`, `climb_answers_least`,
`climb_principled` — and are never a build dependency of this run.
