# The Observer/Read Quantum **Y** — verification report and clean restatement

**Subject.** *"I am Y but I don't know what or where I am, I feel in the dark
with what I haven't"* — An Investigation into the Universal Binary Principle:
Difference, Loop, Observer, and Coherence in a Protected Space (E R A Craig).

**What this document is.** A stage-by-stage audit of that study. For every
stage it states, in one line of unambiguous mathematics, what the stage asserts;
it labels that assertion **definition**, **stipulation**, **theorem** or
**corrected**; and where it is a theorem, it gives the name of a machine-checked
proof. Nothing here is asserted on the strength of a plausible reading: every
statement marked *theorem* is proved in `RequestProject/ObserverY.lean`, which
compiles under Lean 4 with Mathlib, contains no `sorry`, and uses only the
standard axioms. Every number is reproduced in exact rational arithmetic by
`observer_y.py --selftest` (46 checks, all pass), whose constants are the
substrate's own 50-term continued-fraction values, verified to agree with
`ubp_unified_v5.py` function by function.

**Your original text is unmodified.** This is a companion document. A second
companion, `Y_STUDY_CLEAN_RESTATEMENT.md`, rewrites the study itself in the same
structure and vocabulary, with every sentence labelled and written so that it is
defensible as stated.

**Headline.** The chain is sound and, in two places, stronger than the study
claims. Three things need correcting, all of them in the *language* rather than
in the arithmetic:

1. `Y` is **not** derived as a minimum. The operator `Y[Π] = 1/(Π + Δ/Π)` has no
   positive minimum at all, and its *maximum* sits at `Π = √Δ`, not at `Π = π`.
   `Y` is the read cost **at the stipulated loop-check** `Π = π`.
2. `Q = Y + 1/8` **is** a genuine minimum, and this is provable — the study
   understates its own best result. `Q` is exactly the least tax any nonzero
   pattern can pay, attained precisely by a single `±1` activation.
3. The four-regime ladder is **degenerate on 24 coordinates**: two of the four
   regimes are unreachable, and every nonzero Golay codeword lands in one and
   the same regime. A one-line change of the coherence budget repairs it and
   makes all four regimes carry information (§7.3).

---

## 0. How to read this report

| Label | Meaning |
|---|---|
| **Definition** | A symbol is being introduced. Nothing is claimed; nothing can be wrong. |
| **Stipulation** | A choice the study makes (a constant, a threshold, an identification). Legitimate, but it is an input, not a result, and it cannot be confirmed by the system that uses it. |
| **Theorem** | A statement that follows from the definitions. Proved, with the Lean name given. |
| **Corrected** | The study's wording asserts more than follows. The corrected statement, and a suggested rewording, are given. |

The distinction between the first three labels is the single most valuable
piece of hygiene available to this study, because its central risk is that a
stipulation reads like a discovery.

---

## 1. Verdicts at a glance

| # | Stage | Assertion, made precise | Verdict | Lean |
|---|---|---|---|---|
| I | Perfect space | `v = 0 ⟹ TAX = 0, NRCI = 1`, and the vacuum is the **only** such state | **Theorem** (stronger than claimed) | `tax_eq_zero_iff`, `nrci_eq_one_iff` |
| II | Primitive difference "2" | `Δ = 2` enters only as the numerator of the read operator | **Stipulation** | `readCost (d := 2)` |
| III | Disturbance `v` | a pattern is an integer vector; `HW` and `‖v‖²` are its only two summaries used | **Definition** | `hw`, `normSq` |
| IV | Zones, activation | `Q = Y + 1/8` is the **least** tax of a nonzero pattern, attained at a single `±1` | **Theorem** (upgrade) | `Q_le_tax`, `tax_eq_Q_iff` |
| V | Loop-check `Π` | "the loop closes" = "the syndrome vanishes" = "the pattern is lawful"; the gap is additive and forgets exactly the lawful part | **Theorem** (new) | `loop_closes_iff_lawful`, `history_additive`, `same_history_iff` |
| VI | MOG grammar | reading = choosing a coset representative; correction is unique to radius 3, decoding possible to radius 4, ambiguous at 4 | **Theorem** | `golay_covering_radius`, `decoding_not_unique` |
| VII | Golay protection | the cheapest *protected* distinction costs `8Q`; protection multiplies the minimum read cost by exactly 8 | **Theorem** (new) | `protection_costs_eight_quanta` |
| VIII | Leech embodiment | minimal vectors have weights 2, 8, 24 and taxes 4.529, 6.117, 10.352 | **Theorem** | `minimalVector_classAB_coherent`, `minimalVector_classC_transitional` |
| IX | Observer `Y` | `Y = 1/(π + 2/π) = 0.2646754…` | **Definition** + **stipulation** (`Π = π`) | `Y`, `Y_bounds` |
| — | `Y` as "minimum read cost" | false as stated: the operator is *capped*, has no positive minimum, and is maximal at `Π = √2` | **Corrected** | `readCost_le_amgm`, `readCost_le_inv`, `Y_lt_amgm` |
| X | TAX | `TAX = HW·Q` holds **exactly** on patterns with entries in `{-1,0,1}` — and not otherwise | **Theorem** (sharpened) | `tax_eq_hw_mul_Q_iff` |
| XI | NRCI | strictly decreasing in TAX, values in `(0,1]`; the budget `B` is a pure scale | **Theorem** | `coh_strictAnti`, `nrciB_eq_coh` |
| XII | Coherence regimes | the four NRCI thresholds are four tax bands `2.5 / 10 / 23.33`; on 24 signed coordinates only two bands are reachable, and all nonzero codewords fall in one | **Corrected** | `regime_eq_*_iff`, `signed24_regime`, `golay_regime_coherent` |
| §14 A | MOG-aware TAX | a syndrome penalty is *necessary* (the current TAX cannot see lawfulness) and there is a canonical one, vanishing exactly on codewords and bounded by `4Q` | **Theorem** (new) | `tax_eq_of_hw_eq`, `syndromePenalty_eq_zero_iff`, `taxMOG_eq_bitTax_iff` |
| §14 D | Budget `B = Z + Δ` | arithmetically consistent (`8 + 2 = 10`), but untestable as it stands: `B` only sets a scale | **Stipulation** | `nrciB_eq_coh` |

---

## 2. Notation, fixed once

The study uses two vocabularies in parallel. They are kept, but each term is
now pinned to exactly one mathematical object, and the *type* of that object is
given. This is what makes the later stages checkable.

| Study term | Symbol | Type | Meaning fixed here |
|---|---|---|---|
| Perfect space, vacuum | `0` | the zero pattern | the pattern with no active coordinate |
| Raw information, disturbance | `v` | `Fin n → ℤ` | an integer vector on `n` coordinates (`n = 24` for the instrument) |
| Primitive difference "2" | `Δ` | `ℝ`, value `2` | the numerator of the read operator; **not** a count |
| Active distinction count | `HW(v)` | `ℕ` | `#{i : v i ≠ 0}` |
| Geometric extent | `‖v‖²` | `ℤ` | `∑ᵢ (v i)²` |
| Loop-check | `Π` | `ℝ`, value `π` | the argument of the read operator |
| Loop-check, operationally | `syn(v)` | `ℕ` (12 bits) | the Golay syndrome: the residue of the failure to close |
| Gap, history, syndrome | `syn(v) ≠ 0` | — | the pattern is not lawful; the record is nonzero |
| Observer / read quantum | `Y` | `ℝ` | `1/(π + 2/π) = 0.264675430404…` |
| Zone-share | `Z★` | `ℝ`, value `1/8` | cost of occupying a permitted zone |
| Activation quantum | `Q` | `ℝ` | `Y + 1/8 = 0.389675430404…` |
| Symmetry tax | `TAX(v)` | `ℝ` | `HW(v)·Y + ‖v‖²/8` |
| Coherence budget | `B` | `ℝ`, value `10` | the scale against which tax is measured |
| Coherence after tax | `NRCI(v)` | `ℝ` | `B/(B + TAX(v))` |
| Regime | — | one of four | a band of `NRCI`, equivalently a band of `TAX` |

**A wording note that removes most of the ambiguity in the original.** The
study says "`2` is not a number, it is a difference-state". That is a helpful
intuition but it cannot survive into the formulas, because `Δ` is divided by
`Π` and `‖v‖²` is divided by `8`. The clean way to say it is:

> `Δ` is a *parameter* of the read operator whose value happens to be 2. The
> claim "difference is prior to number" belongs to the motivation, not to the
> arithmetic; in the arithmetic, `Δ = 2` is a stipulated constant.

Keeping those two statements apart costs nothing and protects the study from
the charge of numerological drift.

---

## 3. The constants, exactly

Computed in exact rational arithmetic from the substrate's own 50-term
continued-fraction `π`, and confirmed to be bit-identical to
`ubp_unified_v5.py` (`observer_y.py --selftest`, checks *substrate agreement*).

| Symbol | Definition | Value (exact, truncated to 20 places) |
|---|---|---|
| `Y` | `1/(π + 2/π)` | `0.26467543040452694254` |
| `Z★` | zone-share | `0.12500000000000000000` |
| `Q` | `Y + 1/8` | `0.38967543040452694254` |
| `8Q` | octad tax `= 8Y + 1` | `3.11740344323621554036` |
| `24Q` | maximum signed tax | `9.35221032970864662109` |
| `Y_CONST` | `1/(Y⁻¹ + 2/Y⁻¹)` | `0.23214981032830582465` |

`Y_CONST` deserves a note. The substrate computes it (`get_constants`) and it is
*not* the same number as `Y`; it is the read operator applied a second time, to
`Y⁻¹`. The symmetry tax uses `Y`, not `Y_CONST`. If the study intends the
operator `Y[Π]` to be iterated, it should say to what and how often; at present
the second application is unused in the tax and should not be presented as part
of the observer chain. (`Yconst_bounds`.)

---

## 4. Stage by stage

### Stage I — the perfect space

**The study says.** With `v = 0` there is no disturbance, no cost, no history;
`NRCI = 1` is perfect coherence and zero information.

**Precisely.** `TAX(0) = 0` and `NRCI(0) = 1`; and conversely `TAX(v) = 0`
implies `v = 0`, and `NRCI(v) = 1` implies `v = 0`.

**Verdict: theorem, and stronger than the study claims** — the vacuum is not
merely *a* state of perfect coherence, it is the *only* one.
(`tax_eq_zero_iff`, `nrci_eq_one_iff`.)

**Language.** The slogan "information = coherence cost" can be made exact
rather than poetic: with `info(v) := 1 − NRCI(v) = TAX/(B + TAX)`, we have
`NRCI + info = 1` identically (`coh_add_info`). Recommended wording:

> Coherence and information are complementary fractions of one budget:
> `NRCI + info = 1`, with `info = 0` exactly at the vacuum.

### Stage II — the first difference

**The study says.** "2" is the possibility of difference, not a quantity.

**Verdict: stipulation.** `Δ = 2` enters the mathematics only as the numerator
of the read operator. Nothing downstream tests it: replacing `2` by any other
positive `Δ` gives a consistent system with a different `Y`. Say so
explicitly; it costs the study nothing and pre-empts the obvious objection.

### Stage III — the disturbance `v`

**The study says.** `v` is a patterned disturbance, raw information, measurable
in principle.

**Verdict: definition.** In the arithmetic that follows, `v` is used through
exactly two summaries: its Hamming weight `HW(v)` and its squared norm `‖v‖²`.
Everything else about `v` — which coordinates, in what arrangement — is
invisible to `TAX` and `NRCI`. This is worth stating in the document as a
limitation of the current instrument, because it is precisely what refinement
§14 A proposes to fix (see §7.4 below).

### Stage IV — capacity, zones, activation

**The study says.** `Q = Y + 1/8`: to activate a coordinate the observer pays
the read cost and the zone-entry cost.

**Verdict: theorem, and the study's strongest result.** Not only is `Q` a sum of
two costs by definition; it *is* the minimum:

> For every nonzero integer pattern `v`, `TAX(v) ≥ Q`, with equality **iff** `v`
> has exactly one nonzero coordinate and that coordinate is `±1`.

(`Q_le_tax`, `tax_eq_Q_iff`.) So "activation quantum" is a fully earned name:
`Q` is the indivisible least cost of any observation whatsoever. Recommended
wording:

> `Q` is the activation quantum in the strict sense: no pattern can be read for
> less, and the price `Q` is realised by exactly the single-coordinate `±1`
> activations.

### Stage V — the loop, `Π`, and the gap

**The study says.** A closed loop leaves no history; a not-quite-closed loop
leaves a remainder, and that remainder is history/syndrome.

**Verdict: theorem, once the loop-check is identified with the syndrome map.**
This identification is the single largest gain in precision available to the
study, because it turns an evocative image into three checkable facts:

| Study's phrase | Exact statement | Lean |
|---|---|---|
| "the loop closes" | `syn(v) = 0` ⟺ `v` is a Golay codeword | `loop_closes_iff_lawful` |
| "gap adds up" | `syn(a ⊕ b) = syn(a) ⊕ syn(b)` | `history_additive` |
| "gap **is** the history" | `syn(a) = syn(b)` ⟺ `a ⊕ b` is lawful | `same_history_iff` |

The third is the important one: the syndrome forgets *precisely* the protected
content and nothing else, which is what entitles one to call it a complete
record. Recommended wording:

> The loop-check is the syndrome. It vanishes exactly on lawful patterns, it is
> additive, and two disturbances leave the same record exactly when they differ
> by a lawful distinction.

**One caution.** `π` plays no role in this stage. The document uses the same
symbol `Π` for the numerical loop-check inside `Y` and for the structural
closure test; these are two different objects and should be given two names.
Suggested: keep `Π = π` inside the read operator, and write `σ(v)` (or
`syn(v)`) for the closure test.

### Stage VI — MOG as distinction grammar

**The study says.** MOG turns raw disturbance into structured distinction; it
answers *is this closed / lawful / correctable / where is the gap*.

**Verdict: theorem, in the following exact form.** Reading a disturbance means
choosing the lawful pattern nearest to it. For the Golay code:

* every 24-bit pattern is within Hamming distance 4 of a codeword
  (covering radius 4) — `golay_covering_radius`;
* correction is *unique* for at most 3 active errors, because the minimum
  distance is 8 — `golay_min_dist`;
* at distance exactly 4 the answer is genuinely ambiguous: there are patterns
  with two codewords at distance 4 — `decoding_not_unique`.

So "correctable" has a sharp meaning (`≤ 3`), "decodable" has a wider one
(`≤ 4`, with a tie-break convention), and the study's Stage VII sentence
"perfect within its correction capacity" is exactly right if "capacity" is read
as 3.

### Stage VII — Golay protection

**The study says.** Golay protects distinction from collapse; some differences
are not merely present, they are stable.

**Verdict: theorem, with a price attached.** Protection is not free, and its
price is exactly computable:

> The cheapest unprotected distinction costs `Q = 0.3897`.
> The cheapest **protected** distinction costs `8Q = 3.1174` — an octad.
> Protection multiplies the minimum cost of being read by exactly 8.

(`tax_eq_Q_iff` versus `protection_costs_eight_quanta`.) The factor 8 is the
minimum distance of the code; that is the whole content of "protection costs
something".

### Stage VIII — Leech embodiment

**The study says.** The Leech lattice gives the protected code a body; the space
is dark, so observation needs a loop and an observer.

**Verdict: definition plus a measurable consequence.** In the substrate's
integer scaling every Leech minimal vector has `‖v‖² = 32`, so its tax is
`HW·Y + 4`, and the three shape classes are distinguished by weight alone:

| Class | Shape | `HW` | `TAX` | `NRCI` | Regime |
|---|---|---:|---:|---:|---|
| A | `(∓4², 0²²)` | 2 | `4.529351` | `0.688262` | Coherent |
| B | `(∓2⁸, 0¹⁶)` | 8 | `6.117403` | `0.620447` | Coherent |
| C | `(∓3, ±1²³)` | 24 | `10.352210` | `0.491347` | **Transitional** |

(`minimalVector_classAB_coherent`, `minimalVector_classC_transitional`,
`minimalVector_classC_nrci`.) This is a genuine and slightly surprising
consequence of the study's own definitions: the deepest shell of the lattice —
every vector of which is a kissing-sphere vector, i.e. maximally "embodied" —
falls **out** of the Coherent band. Either that is a feature (density is
expensive) or the thresholds are miscalibrated (§7.3). It is the study's first
falsifiable prediction and it deserves a paragraph of its own in the document.

### Stage IX — the observer `Y`

**The study says.** `Y = 1/(π + 2/π)` is "the minimum cost of reading a
reflected distinction"; operationally `Y[Π] = Reciprocal(Π + Δ/Π)`.

**Verdict: corrected.** Taking the operator literally and asking what it
determines:

* it is **capped**: `Y[Π] ≤ 1/(2√Δ)` for every `Π > 0`, with equality only at
  `Π = √Δ` (`readCost_le_amgm`). For `Δ = 2` the cap is `0.353553…`.
* it has **no positive minimum**: `Y[Π] ≤ 1/Π`, so the read cost tends to 0 as
  the loop-check grows (`readCost_le_inv`).
* at `Π = π` the value is `0.264675…`, strictly below the cap (`Y_lt_amgm`).

Therefore `Y` is neither a maximum nor a minimum of anything in the study. It
is the value of the operator at the stipulated point `Π = π`. Recommended
wording, which keeps everything the study actually needs:

> `Y` is the observer/read quantum **at loop-check `π`**: the reciprocal of the
> loop cost `π + 2/π`. The operator caps any read cost at `1/(2√Δ)`; the choice
> `Π = π` is a stipulation of this investigation, not a consequence of it.

If a variational justification of `π` is wanted later, this report has made the
target precise: one must exhibit a functional that `π` extremises. The obvious
candidate (`Y[Π]` itself) does not work.

### Stage X — TAX

**The study says.** `TAX = HW·Y + ‖v‖²/8`; for a binary vector `‖v‖² = HW`, so
`TAX = HW·(Y + 1/8) = HW·Q`.

**Verdict: theorem, and the converse holds too.**

> `TAX(v) = HW(v)·Q` **iff** every coordinate of `v` lies in `{-1, 0, 1}`.

(`tax_eq_hw_mul_Q_iff`.) Two consequences worth stating in the document:

* the identity is a property of `{-1,0,1}` patterns, not of "binary" in the
  vague sense; it holds for signed patterns too, and fails for every pattern
  with a coordinate of size `≥ 2`;
* in particular it **fails at the Leech layer**, where minimal vectors have
  entries `±2, ±3, ∓4`. So the "beautiful result" `TAX = HW·Q` is a Golay-layer
  statement. The Leech-layer analogue is `TAX = HW·Y + 4`.

### Stage XI — NRCI

**The study says.** `NRCI = 10/(10 + TAX)`; and §14 D suggests `B = Z + Δ`, i.e.
`8 + 2 = 10`.

**Verdict: theorem for the properties, stipulation for the budget.**

* `NRCI` is a strictly decreasing function of `TAX` alone, with values in
  `(0, 1]`, equal to 1 only at the vacuum, never 0 (`coh_strictAnti`,
  `coh_pos`, `coh_le_one`, `nrci_eq_one_iff`);
* the budget is a **pure scale**: `nrciB B t = coh(10t/B)` (`nrciB_eq_coh`).
  Changing `B` rescales the tax axis and nothing else.

The last point settles the status of `B = Z + Δ = 8 + 2 = 10`. Arithmetically it
is consistent. But because `B` only sets a scale, *no measurement inside the
system can confirm or refute the identification* unless the thresholds are
derived from something independent. As written, the identification is a
mnemonic. Recommended wording:

> The budget `B` fixes the unit in which tax is measured; `NRCI` depends only on
> `TAX/B`. The reading `B = Z + Δ = 10` is an interpretation of that unit, not a
> testable claim, unless the regime thresholds are derived independently.

That is not a weakness — §7.3 below turns exactly this freedom into a
constructive improvement.

### Stage XII — the coherence regimes

**The study says.** OnBit `≥ 0.8`, Coherent `≥ 0.5`, Transitional `≥ 0.3`,
Subcoherent below.

**Precisely.** Since `NRCI` is strictly decreasing in `TAX`, each threshold is a
tax ceiling `B/c − B`:

| Regime | `NRCI` | `TAX` band | signed weight `HW` | reachable on 24 coordinates? |
|---|---:|---|---|---|
| OnBit | `≥ 0.8` | `0 … 2.5` | `≤ 6` | yes |
| Coherent | `≥ 0.5` | `2.5 … 10` | `≤ 25` | yes |
| Transitional | `≥ 0.3` | `10 … 23.33` | `≤ 59` | **no** |
| Subcoherent | `< 0.3` | `> 23.33` | — | **no** |

(`regime_eq_onBit_iff`, `regime_eq_coherent_iff`, `regime_eq_transitional_iff`,
`regime_eq_subcoherent_iff`, `signed_onBit_iff`, `signed24_regime`.)

**Verdict: corrected.** A signed 24-coordinate pattern has `TAX ≤ 24Q = 9.3522
< 10`, so **only two of the four regimes can ever occur** there. Worse, on the
Golay layer the ladder is completely flat:

| Codeword weight | `TAX` | `NRCI` | Regime |
|---:|---:|---:|---|
| 0 | `0.000000` | `1.000000` | OnBit |
| 8 | `3.117403` | `0.762346` | Coherent |
| 12 | `4.676105` | `0.681380` | Coherent |
| 16 | `6.234807` | `0.615961` | Coherent |
| 24 | `9.352210` | `0.516737` | Coherent |

(`golay_regime_coherent`, `octad_nrci_bounds`.) The vacuum is OnBit and *every*
nonzero codeword is Coherent: as calibrated, the regime table carries no
information about the code at all. §7.3 fixes this.

---

## 5. What the study gets exactly right

1. **The chain of dependencies** (`Δ → v → grammar → protection → embodiment →
   read → tax → coherence`) is not decoration: each stage supplies something the
   next one uses, and every arrow in it corresponds to a real mathematical
   dependency in the formalisation.
2. **`TAX = HW·Q` for binary patterns** — right, and now known to be exactly
   characteristic of `{-1,0,1}` patterns.
3. **The vacuum principle** ("perfect coherence contains no distinction") — right,
   and in the strong form: the vacuum is the *unique* zero-tax, unit-coherence
   state.
4. **`Q` as an activation quantum** — right, and provably a realised minimum. The
   study is more correct here than it claims to be.
5. **The refinement horizon §14 A–D** identifies real gaps, and two of them
   (A and D) are resolved in this report.

---

## 6. Three corrections, in the order of importance

### C1 — `Y` is not a minimum

Stated in Stage IX above. The phrase to retire is "the minimum cost of reading a
reflected distinction"; the phrase to use is "the read cost at loop-check `π`".
The mathematics is unchanged; only the epistemic claim shrinks, and it shrinks
to something defensible.

### C2 — "binary" is the wrong word for the scope of `TAX = HW·Q`

The identity characterises patterns with entries in `{-1,0,1}`. Saying "binary"
invites the reader to apply it at the Leech layer, where it is false. Suggested
sentence: *"On the code layer, where every coordinate is `0` or `1`, the tax
collapses to `HW·Q`. This is exactly the class of patterns for which it does:
`TAX = HW·Q` iff every coordinate is `−1`, `0` or `1`."*

### C3 — the regime ladder is mis-scaled

Stated in Stage XII. Two of the four regimes are unreachable and the code layer
is monochrome. This is a calibration problem, not a conceptual one, and §7.3
gives a one-symbol fix.

---

## 7. Four results that strengthen the study

### 7.1 The price of protection is exactly eight quanta

`Q` for an unprotected distinction, `8Q` for the cheapest protected one; the
factor is the minimum distance of the Golay code
(`protection_costs_eight_quanta`). This gives Stage VII a number, and it
connects to the lightspeed study, where `8Y + 1 = 3.1174` is the minimum nonzero
symmetry tax and the origin of its "+3 TAX" (see `SUBSTRATE_LIGHTSPEED_REPORT.md`).

### 7.2 The loop is the syndrome

Three exact statements replacing an image (Stage V). In particular the
"not-quite-closed loop" is not merely *a* record of failure but a *complete* one:
same syndrome ⟺ differ by a lawful pattern.

### 7.3 A calibrated budget makes the regime ladder informative

Because `B` only sets a scale, one may choose it. Choosing the cheapest
protected distinction as the unit, `B = 8Q`, gives for a codeword of weight `w`

    NRCI(w) = 8Q / (8Q + wQ) = 8 / (8 + w)

— the read cost cancels entirely, leaving a scale-free ratio of the weight to
the minimum distance (`nrciB_calibrated`). The four regimes then separate the
code:

| Weight | `NRCI = 8/(8+w)` | Regime |
|---:|---:|---|
| 0 | `1.000` | OnBit |
| 8 | `0.500` | Coherent |
| 12 | `0.400` | Transitional |
| 16 | `0.333` | Transitional |
| 24 | `0.250` | Subcoherent |

(`calibrated_regime_separates`.) All four regimes are used, the ordering is
monotone in weight, and the octad — the minimum-weight protected distinction —
sits exactly on the Coherent boundary at `NRCI = 1/2`. No definition of the
study changes; only the unit does.

### 7.4 A MOG-aware tax, as §14 A asks for

First, the gap is real and provable: on signed patterns `TAX` depends only on
`HW`, so **a codeword and a random error pattern of the same weight are charged
identically** (`tax_eq_of_hw_eq`). Any tax that is to see lawfulness must add a
term that reads the syndrome.

There is a canonical such term: charge the pattern for the correction it needs,

    syndromePenalty(v) = HW(leader(syn v)) · Q,     TAX_MOG(v) = HW(v)·Q + syndromePenalty(v)

with these properties, all proved:

* `syndromePenalty(v) = 0` **iff** `v` is lawful (`syndromePenalty_eq_zero_iff`);
* `syndromePenalty(v) ≤ 4Q` always, the covering radius of the code measured in
  activation cost (`syndromePenalty_le`);
* hence `TAX_MOG(v) = TAX(v)` **iff** `v` is lawful (`taxMOG_eq_bitTax_iff`), and
  the surcharge never exceeds `4Q = 1.5587`.

This is the study's "syndrome penalty" and "closure credit" unified into one
well-defined term, with the credit being simply the absence of a penalty.

---

## 8. The refinement horizon (§14), restated as precise questions

| § | The study's proposal | Status after this report | The precise open question |
|---|---|---|---|
| A | MOG-aware TAX | **Resolved** (§7.4) | Should the penalty be `HW(leader)·Q`, or weighted by syndrome *class*? Both are now expressible. |
| B | Shell-version NRCI | Open | Fix the shell invariant: `‖v‖²` alone is constant (32) on the minimal shell, so a shell-aware NRCI must use `HW` or the shape class, not the norm. |
| C | Codeword vs error pattern | **Diagnosed and resolved** (§7.4) — the current TAX provably cannot distinguish them | — |
| D | Origin of the budget | **Clarified**: `B` is a scale, so `B = Z + Δ` is untestable as it stands | Derive the *thresholds* independently, or adopt a calibrated `B` (§7.3), which makes `B` a derived quantity (`8Q`) rather than a stipulated one. |

---

## 9. Reproducing everything

```bash
# exact-rational audit: 46 checks, including agreement with ubp_unified_v5.py
python3 observer_y.py --selftest

python3 observer_y.py --constants     # the constants, exactly
python3 observer_y.py --stages        # the stage ledger of §1
python3 observer_y.py --tables        # Golay, calibrated-Golay and Leech tables
python3 observer_y.py --regimes       # the regime bands and their reachability
python3 observer_y.py --vector 1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
python3 observer_y.py --json          # machine-readable dump

lake build                            # check every proof cited in this report
```

---

## 10. Index of machine-checked statements

All in `RequestProject/ObserverY.lean` unless noted. The file compiles with no
`sorry` and depends only on `propext`, `Classical.choice` and `Quot.sound`.

| Name | Statement |
|---|---|
| `readCost_eq` | `Y[Π] = Π/(Π² + Δ)` |
| `readCost_le_amgm` | `Y[Π] ≤ 1/(2√Δ)` |
| `readCost_le_inv` | `Y[Π] ≤ 1/Π`; no positive lower bound |
| `Y_bounds` | `0.264675 < Y < 0.264676` |
| `Y_lt_amgm` | `Y < 1/(2√2)`: `π` is not the extremal loop-check |
| `Yconst_bounds` | `0.232149 < Y_CONST < 0.232150`, distinct from `Y` |
| `Q_bounds` | `0.389675 < Q < 0.389676` |
| `hw_le_normSq` | each active coordinate contributes `≥ 1` to the extent |
| `normSq_eq_hw_iff` | `‖v‖² = HW(v)` iff every entry is in `{-1,0,1}` |
| `tax_nonneg`, `tax_eq_zero_iff` | tax is nonnegative and vanishes only at the vacuum |
| `tax_eq_hw_mul_Q_iff` | `TAX = HW·Q` iff every entry is in `{-1,0,1}` |
| `Q_le_tax`, `tax_eq_Q_iff` | `Q` is the realised minimum tax of a nonzero pattern |
| `tax_eq_of_hw_eq` | TAX cannot distinguish equal-weight signed patterns |
| `coh_zero`, `coh_pos`, `coh_le_one`, `coh_strictAnti` | NRCI is a strictly decreasing map into `(0,1]` |
| `coh_add_info` | `NRCI + info = 1` |
| `nrci_eq_one_iff` | perfect coherence exactly at the vacuum |
| `nrciB_eq_coh` | the budget is a pure scale |
| `coh_ge_iff` | a coherence threshold `c` is the tax ceiling `B/c − B` |
| `regime_eq_onBit_iff` … `regime_eq_subcoherent_iff` | the four regimes are four tax bands |
| `signed24_tax_le`, `signed24_regime` | signed 24-patterns never leave OnBit/Coherent |
| `signed_onBit_iff` | OnBit ⟺ at most six active distinctions |
| `codewordTax_eq` | a codeword of weight `w` is taxed `w·Q` |
| `golay_regime_coherent` | every nonzero codeword is Coherent |
| `octad_nrci_bounds` | octad `NRCI = 0.76234…` |
| `protection_costs_eight_quanta` | the cheapest protected distinction costs `8Q` |
| `loop_closes_iff_lawful`, `history_additive`, `same_history_iff` | the loop-check is the syndrome |
| `leader_eq_zero_iff` | the coset leader vanishes only for the zero syndrome |
| `syndromePenalty_eq_zero_iff`, `syndromePenalty_le`, `taxMOG_eq_bitTax_iff`, `taxMOG_le` | the MOG-aware tax |
| `minimalVectorTax_eq` | a Leech minimal vector of weight `w` is taxed `w·Y + 4` |
| `minimalVector_classAB_coherent`, `minimalVector_classC_transitional`, `minimalVector_classC_nrci` | the three minimal-vector classes and their regimes |
| `nrciB_calibrated`, `calibrated_regime_separates` | the calibrated budget `B = 8Q` |
| `golay_min_dist` (`GolayWeights.lean`) | minimum distance 8 |
| `golay_covering_radius`, `decoding_not_unique` (`Decoder.lean`) | covering radius 4; ties at distance 4 |
