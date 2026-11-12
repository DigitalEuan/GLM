# I am Y — a clean restatement

### *Difference, loop, observer and coherence in a protected space*

**Original author:** E R A Craig, New Zealand.
**This version:** a rewriting of *"I am Y but I don't know what or where I am,
I feel in the dark with what I haven't"* in which every sentence is intended to
be defensible as written. The structure, the vocabulary and the order of the
original are kept; the section numbers correspond one-to-one. What changed is
the language: each statement now carries a label,

> **[def]** a definition · **[stip]** a stipulated choice · **[thm]** a proved
> statement, with the name of its machine-checked proof ·
> **[open]** a question this document does not settle,

and no sentence claims more than its label allows. The original text is
untouched and remains in the project; the audit that produced these labels is
`Y_OBSERVER_STUDY_REPORT.md`; the proofs are in
`RequestProject/ObserverY.lean`; the arithmetic is reproduced exactly by
`observer_y.py --selftest`.

---

## 0. Position of this document

This document does not claim that reality is this system.

It claims something narrower and checkable:

> Given a stipulated read cost, a stipulated zone cost and a chosen protected
> geometry, there is a consistent accounting of what it costs to distinguish
> something — and that accounting has a small number of provable properties.

The working name for the accounting is the **Universal Binary Principle**
(UBP). "Binary" does not mean twoness; it means *difference as the first
condition of distinction*. That reading is motivational: it does not enter any
formula below, and nothing below depends on it.

---

## 1. The principle in one sentence

> **Distinction becomes possible when primitive difference is given structure,
> protection, embodiment, and read access — and each of those four has a
> price.**

The severe form, with the prices named:

> Where difference is not yet formed there is vacuum (price 0); where difference
> is formed but unlawful there is a syndrome (price up to `4Q`); where difference
> is encoded, protected and read there is measurement (price at least `Q`, and at
> least `8Q` if it is to be protected).

Every number in that sentence is proved below.

---

## 2. Dual terminology, pinned down

Each term now names exactly one mathematical object.

| Structural term | Symbol | Type | Operational meaning |
|---|---|---|---|
| Perfect space | `0` | pattern | no active coordinate |
| Zero vector | `0` | pattern | no disturbance, no information |
| Raw information | `v` | `Fin n → ℤ` | an integer pattern on `n = 24` coordinates |
| Primitive difference "2" | `Δ` | `ℝ` = 2 | the numerator of the read operator |
| Capacity / zone-share | `Z★` | `ℝ` = 1/8 | cost of occupying a permitted zone |
| Body | 24 coordinates | index set | the coordinate space |
| Loop-check (numeric) | `Π` | `ℝ` = π | the argument of the read operator |
| Loop-check (structural) | `σ(v)` | 12 bits | the Golay syndrome |
| Not-quite-closed loop | `σ(v) ≠ 0` | — | history, gap, syndrome |
| MOG | nearest-codeword reading | — | the grammar that turns a pattern into a lawful one |
| Golay | `[24,12,8]` code | — | protection: minimum distance 8 |
| Leech | `Λ₂₄` | — | embodiment: the 24-dimensional geometry |
| Observer / read quantum | `Y` | `ℝ` | `1/(π + 2/π) = 0.2646754…` |
| Activation quantum | `Q` | `ℝ` | `Y + 1/8 = 0.3896754…` |
| TAX | `TAX(v)` | `ℝ` | `HW(v)·Y + ‖v‖²/8` |
| Coherence budget | `B` | `ℝ` = 10 | the unit in which tax is measured |
| NRCI | `NRCI(v)` | `ℝ` | `B/(B + TAX(v))` |
| CoherenceRegime | one of four | — | a band of `NRCI`, equivalently of `TAX` |

**Two symbols that were previously one.** The original uses `π` both for the
numeric loop-check inside `Y` and for the structural closure test. These are
different objects and are now written `Π = π` and `σ(v)` respectively.

---

## 3. The sequence of steps

Each step supplies something the next one uses. The sequence is not claimed to
be forced; it is claimed to be *coherent*, and every arrow in it is a real
dependency in the formal development.

---

### Step I — the perfect space **[def + thm]**

Begin with the vacuum: `v = 0`. No active coordinate, no read event, no
history.

> **[thm]** `TAX(0) = 0` and `NRCI(0) = 1`; and the vacuum is the **only**
> pattern with either property. `tax_eq_zero_iff`, `nrci_eq_one_iff`

Coherence is complete and knowledge is absent — and now in the strong sense:
perfect coherence is not merely *compatible* with the absence of distinction, it
is *equivalent* to it.

---

### Step II — the first difference **[stip]**

The next condition is not a quantity but the possibility of difference. In the
arithmetic it appears as a single stipulated constant:

    Δ = 2

> **[stip]** `Δ = 2` enters only as the numerator of the read operator of Step IX.
> Any other positive value gives a consistent system with a different `Y`.
> Nothing in this document tests it.

The motivational reading ("`2` is a difference-state, not a number") is retained
as motivation and is not used.

---

### Step III — the disturbance `v` **[def]**

A pattern of difference is an integer vector `v`. Two summaries of it are used
throughout, and *only* these two:

    HW(v)  = #{i : v i ≠ 0}      the active distinctions
    ‖v‖²   = ∑ᵢ (v i)²           the geometric extent

> **[thm]** `HW(v) ≤ ‖v‖²`, with equality exactly when every coordinate is
> `−1`, `0` or `1`. `hw_le_normSq`, `normSq_eq_hw_iff`

At this stage `v` is not yet meaningful: it is detectable in principle and
nothing more.

---

### Step IV — capacity, zones, and the activation quantum **[def + thm]**

Placing `v` in a zoned body of 24 coordinates gives difference *location*,
*limitation* and *addressability*. Entering a zone costs `Z★ = 1/8` **[stip]**;
reading a coordinate costs `Y`; so activating one coordinate costs

    Q = Y + 1/8 = 0.3896754…

The original states this as an accounting identity. It is more than that:

> **[thm]** For every nonzero pattern, `TAX(v) ≥ Q`; and `TAX(v) = Q` exactly
> when `v` has a single nonzero coordinate, equal to `±1`.
> `Q_le_tax`, `tax_eq_Q_iff`

So `Q` earns the name *quantum* in the strict sense: nothing can be read for
less, and the price `Q` is actually attained.

---

### Step V — the loop and the gap **[thm]**

For a disturbance to be detected there must be a check, and the check must be
able to *fail informatively*. A closed loop leaves no history; a not-quite-closed
loop leaves a remainder, and the remainder is the record.

Operationally the loop-check is the syndrome `σ(v)`, and the image becomes three
exact statements:

> **[thm]** `σ(v) = 0` ⟺ `v` is lawful (a Golay codeword). `loop_closes_iff_lawful`
> **[thm]** `σ(a ⊕ b) = σ(a) ⊕ σ(b)`: the record is additive. `history_additive`
> **[thm]** `σ(a) = σ(b)` ⟺ `a ⊕ b` is lawful. `same_history_iff`

The third is what entitles us to call the gap *the* history rather than *a*
trace of it: the syndrome forgets precisely the lawful content and nothing else.

A measurement is therefore a state **plus** its record of closure failure — and
the record is complete.

---

### Step VI — MOG as distinction grammar **[thm]**

MOG is the rule that reads a raw pattern as a lawful one: choose the lawful
pattern nearest to it. Its three operative facts:

> **[thm]** every pattern lies within distance 4 of a lawful one (covering
> radius 4). `golay_covering_radius`
> **[thm]** distinct lawful patterns differ in at least 8 coordinates (minimum
> distance 8), so a pattern with at most 3 errors has a *unique* reading.
> `golay_min_dist`
> **[thm]** at distance exactly 4 the reading is genuinely ambiguous: there are
> patterns with two lawful neighbours at distance 4. `decoding_not_unique`

So the grammar answers "is this closed / lawful / correctable / where is the
gap", with the honest boundary: **correctable to 3, decodable to 4, ambiguous at
4**.

MOG does not create difference. It makes difference usable.

---

### Step VII — Golay protection, and its price **[thm]**

Protection means that lawful distinctions survive disturbance: within the
correction capacity, error can be healed and distinction survives; beyond it,
distinction becomes fragile. The environment is not perfect everywhere — it is
perfect within its correction capacity.

Protection is not free, and its price is exact:

> **[thm]** the cheapest unprotected distinction costs `Q = 0.3897`;
> the cheapest **protected** one costs `8Q = 3.1174` (an octad).
> `tax_eq_Q_iff`, `protection_costs_eight_quanta`

Protection multiplies the minimum cost of being read by exactly 8 — the minimum
distance of the code. That factor is the whole content of "protection costs
something".

---

### Step VIII — Leech embodiment **[def + thm]**

The Leech lattice gives the protected code a body: 24 dimensions, high symmetry,
dense relational structure, no cheap local mirrors. Observation therefore cannot
rely on local reflection; it needs a loop, a history and an observer.

In the substrate's integer scaling every minimal (kissing-sphere) vector has
`‖v‖² = 32`, so its tax is `HW·Y + 4` and the three shape classes are separated
by weight alone:

| Class | Shape | `HW` | `TAX` | `NRCI` | Regime |
|---|---|---:|---:|---:|---|
| A | `(∓4², 0²²)` | 2 | 4.529351 | 0.688262 | Coherent |
| B | `(∓2⁸, 0¹⁶)` | 8 | 6.117403 | 0.620447 | Coherent |
| C | `(∓3, ±1²³)` | 24 | 10.352210 | 0.491347 | **Transitional** |

> **[thm]** classes A and B are Coherent; class C is Transitional.
> `minimalVector_classAB_coherent`, `minimalVector_classC_transitional`

This is the first genuinely falsifiable consequence of the accounting: the
*deepest* shell of the geometry falls out of the Coherent band. Either density
is expensive — a defensible reading — or the thresholds are mis-scaled (§8).

---

### Step IX — the observer/read quantum `Y` **[def + stip + thm]**

`Y` is not an observer as a being. It is the price of a read: what it costs to
turn a protected distinction into an observed event.

    Y[Π] = 1/(Π + Δ/Π)            the read-cost operator      [def]
    Y    = Y[π]  with  Δ = 2  =  1/(π + 2/π)  =  0.2646754…   [stip: Π = π]

The original calls `Y` "the minimum cost of reading a reflected difference".
That is the one claim in the study that does not survive checking, and the
correction is worth stating plainly, because what remains is still exactly what
the rest of the document needs:

> **[thm]** the operator is *capped*: `Y[Π] ≤ 1/(2√Δ)` for every `Π > 0`, with
> equality only at `Π = √Δ`. `readCost_le_amgm`
> **[thm]** it has *no positive lower bound*: `Y[Π] ≤ 1/Π`. `readCost_le_inv`
> **[thm]** hence `Y < 1/(2√2) = 0.3536`: `π` is not the extremal loop-check.
> `Y_lt_amgm`

So the honest statement is:

> **`Y` is the observer/read quantum at loop-check `π`** — the reciprocal of the
> loop cost `π + 2/π`. The operator bounds any read cost by `1/(2√Δ)`; the choice
> `Π = π` is a stipulation of this investigation, not a consequence of it.

**[open]** Is there a functional of the loop that `π` extremises? The obvious
candidate — `Y[Π]` itself — is not one.

Without `Y` there is structure, code, geometry and difference, but no
observation. That claim is untouched by the correction: it is about the role of
`Y`, not about its value.

---

## 4. The activation quantum

    Q = Y + Z★ = Y + 1/8

To activate a coordinate the observer pays both the read cost and the
zone-entry cost:

    activation = read + zone entry

> **[thm]** and `Q` is exactly the minimum tax of a nonzero pattern, attained by
> the single `±1` activations. `Q_le_tax`, `tax_eq_Q_iff`

---

## 5. TAX — the symmetry tax

    TAX(v) = HW(v)·Y  +  ‖v‖²/8
             ───────     ──────
             read cost   embodiment cost

The first term is topological: the observer pays `Y` per active distinction. The
second is geometric: the displacement of the pattern, normalised by the zone
scale 8.

For a pattern whose coordinates are all `−1`, `0` or `1` we have `‖v‖² = HW`,
hence

    TAX = HW·(Y + 1/8) = HW·Q

> **[thm]** and this identity characterises exactly those patterns:
> `TAX(v) = HW(v)·Q` **iff** every coordinate lies in `{−1, 0, 1}`.
> `tax_eq_hw_mul_Q_iff`

Two consequences of the sharpened form:

* the identity is about `{−1,0,1}` patterns, not about "binary" loosely
  understood; it holds for signed patterns and fails for any coordinate of size
  `≥ 2`;
* it therefore holds on the **code** layer and fails on the **Leech** layer,
  where the analogue is `TAX = HW·Y + 4`.

So, on the code layer: *the symmetry tax is the number of active distinctions
times the activation quantum.* That is the result the original calls beautiful,
now with its exact domain of validity attached.

**A limitation to state openly.**

> **[thm]** on signed patterns `TAX` depends on `HW` alone, so a lawful codeword
> and a random error pattern of the same weight are taxed identically.
> `tax_eq_of_hw_eq`

The tax, as defined, cannot see lawfulness. §14 A repairs this.

---

## 6. NRCI — coherence after tax

    NRCI(v) = B / (B + TAX(v)),     B = 10

> **[thm]** `NRCI` is a strictly decreasing function of the tax alone, with
> values in `(0, 1]`; it equals 1 only at the vacuum and is never 0.
> `coh_strictAnti`, `coh_pos`, `coh_le_one`, `nrci_eq_one_iff`
> **[thm]** the budget is a **pure scale**: `NRCI` depends only on `TAX/B`.
> `nrciB_eq_coh`

The original proposes reading the budget as `B = Z + Δ = 8 + 2 = 10`. That
arithmetic is consistent, but the scaling theorem shows what its status is:

> **[stip]** `B` fixes the unit in which tax is measured. The reading
> `B = Z + Δ` is an interpretation of that unit. Because `NRCI` depends only on
> `TAX/B`, no measurement inside the system can confirm or refute the reading
> unless the regime thresholds are fixed independently.

This is not a weakness. It is a degree of freedom, and §8 uses it.

---

## 7. The zero vector

For `v = 0`: `HW = 0`, `‖v‖² = 0`, `TAX = 0`, `NRCI = 1`.

Perfect coherence, and zero information. Not a flaw but the central principle,
now with an exact form:

> **[thm]** with `info(v) := 1 − NRCI(v) = TAX/(B + TAX)`, we have
> `NRCI + info = 1` identically, and `info = 0` exactly at the vacuum.
> `coh_add_info`, `nrci_eq_one_iff`

To know something, coherence must be spent. Coherence and information are
complementary fractions of one budget.

---

## 8. Coherence regimes

The four regimes are thresholds on `NRCI`. Because `NRCI` decreases strictly in
the tax, each threshold is a tax ceiling `B/c − B`:

| Regime | `NRCI` | `TAX` band | signed weight | reachable on 24 coordinates? |
|---|---:|---|---|---|
| OnBit | `≥ 0.8` | `0 … 2.5` | `HW ≤ 6` | yes |
| Coherent | `≥ 0.5` | `2.5 … 10` | `HW ≤ 25` | yes |
| Transitional | `≥ 0.3` | `10 … 23.33` | `HW ≤ 59` | **no** |
| Subcoherent | `< 0.3` | `> 23.33` | — | **no** |

> **[thm]** the four regimes are exactly these four bands.
> `regime_eq_onBit_iff`, `regime_eq_coherent_iff`, `regime_eq_transitional_iff`,
> `regime_eq_subcoherent_iff`
> **[thm]** on 24 coordinates a signed pattern has `TAX ≤ 24Q = 9.3522 < 10`, so
> only OnBit and Coherent can occur. `signed24_regime`
> **[thm]** `OnBit` means exactly "at most six active distinctions".
> `signed_onBit_iff`
> **[thm]** every nonzero Golay codeword is Coherent — never OnBit.
> `golay_regime_coherent`

So, as calibrated with `B = 10`, the ladder is flat where it matters: the vacuum
is OnBit and *every* protected distinction is Coherent. The table distinguishes
nothing on the code layer.

**The repair, using the freedom identified in §6.** Take the cheapest protected
distinction as the unit, `B = 8Q`. Then for a codeword of weight `w`

    NRCI(w) = 8Q/(8Q + wQ) = 8/(8 + w)

— the read cost cancels, leaving the weight measured against the minimum
distance:

| Weight | `NRCI = 8/(8+w)` | Regime |
|---:|---:|---|
| 0 | 1.000 | OnBit |
| 8 | 0.500 | Coherent |
| 12 | 0.400 | Transitional |
| 16 | 0.333 | Transitional |
| 24 | 0.250 | Subcoherent |

> **[thm]** `NRCI(w) = 8/(8+w)` on the calibrated budget, and the five weight
> classes then occupy all four regimes.
> `nrciB_calibrated`, `calibrated_regime_separates`

All four regimes are used, the order is monotone in weight, and the octad — the
minimum-weight protected distinction — sits exactly on the Coherent boundary at
`NRCI = 1/2`. No definition changes; only the unit does.

---

## 9. MOG, Golay and Leech as one instrument

    MOG    gives distinction grammar          reading is nearest-codeword choice
      ↓                                        (unique to 3, decodable to 4)
    Golay  gives protection and correction     minimum distance 8; price 8Q
      ↓
    Leech  gives embodied geometry             ‖v‖² = 32 on the minimal shell
      ↓
    Y      pays the read                       Q per activation
      ↓
    TAX, NRCI                                  the cost, and what remains

> **MOG reads, Golay protects, Leech embodies, Y observes** — and each of the
> four now has a number attached: 3/4, 8, 32, `Q`.

---

## 10. What `v` is

`v` is not the possibility of difference; it is a pattern of difference — raw
information as a disturbance of the perfect space. It becomes a measurement by
passing through the instrument:

```
v  →  zoned body        location, limitation            [def]
   →  loop-check σ(v)   syndrome / history              [thm: complete record]
   →  MOG               lawful vs unlawful reading      [thm: unique to 3]
   →  Golay             correctable distinction         [thm: price 8Q]
   →  Leech             geometric distinction           [def]
   →  Y                 measurement                     [thm: price ≥ Q]
```

---

## 11. What `Y` is

**As formula.** `Y = 1/(π + 2/π)`, the read operator `Y[Π] = 1/(Π + Δ/Π)` at
`Δ = 2`, `Π = π`.

**As operation.** The observer/read quantum: the cost of one read.

**As measurement principle.** The per-distinction term of the tax. *Not* a
minimum of the operator — the operator has no positive minimum (§ Step IX).

**As activation component.** `Q = Y + Z★`, and `Q` *is* a minimum
(`tax_eq_Q_iff`).

**As "why".** Without `Y` there is structure, code, geometry and difference, but
no observation. `Y` is the principle by which the system becomes known to
itself. This is a statement about the *role* of `Y` and it is unaffected by the
correction to its extremal status.

---

## 12. Why the shape is convincing

Not because it is pretty, but because several independent requirements resolve
into one accounting, and each link is checkable:

| Requirement | Supplied by | Checkable content |
|---|---|---|
| measurement requires distinction | `Δ` | stipulated |
| distinction requires structure | MOG | unique reading to radius 3 |
| structure requires protection | Golay | minimum distance 8 |
| protection requires embodiment | Leech | `‖v‖² = 32` minimal shell |
| embodiment requires observation | `Y` | `Q` per activation |
| observation requires cost | TAX | `TAX ≥ Q`, `= HW·Q` on signed patterns |
| cost requires accounting | NRCI | strictly decreasing, `(0,1]`, scale-free in `TAX/B` |

    Δ → v → MOG → Golay → Leech → Y → TAX → NRCI

---

## 13. The complete map

```
                     PERFECT SPACE                  TAX = 0, NRCI = 1  [thm: unique]
                          |
                 primitive difference Δ = 2         [stip]
                          |
                 disturbance v arises               HW, ‖v‖²           [def]
                          |
                  zoned embodied body               24 coordinates, Z★ = 1/8
                          |
                 loop-check σ(v)                    σ = 0 ⟺ lawful     [thm]
                          |
                  syndrome / history                complete record    [thm]
                          |
                    MOG reading                     unique to 3        [thm]
                          |
                 Golay protection                   d = 8, price 8Q    [thm]
                          |
                 Leech embodiment                   ‖v‖² = 32          [def]
                          |
                Observer / read Y                   Y = Y[π]           [stip: Π = π]
                          |
                 activation Q = Y + 1/8             min tax            [thm]
                          |
                       TAX                          HW·Q on signed     [thm]
                          |
                      NRCI                          B/(B+TAX)          [thm]
                          |
                 CoherenceRegime                    four tax bands     [thm]
```

---

## 14. Refinement horizon

### A. MOG-aware TAX — **resolved**

The gap is real: the present tax cannot distinguish a lawful pattern from a
random one of the same weight (`tax_eq_of_hw_eq`). A term that reads the
syndrome is therefore necessary, and there is a canonical one — charge the
pattern for the correction it needs:

    syndromePenalty(v) = HW(leader(σ(v)))·Q
    TAX_MOG(v)         = HW(v)·Q + syndromePenalty(v)

> **[thm]** the penalty vanishes **iff** `v` is lawful; it never exceeds `4Q`
> (the covering radius, priced in activation quanta); hence
> `TAX_MOG = TAX` **iff** `v` is lawful.
> `syndromePenalty_eq_zero_iff`, `syndromePenalty_le`, `taxMOG_eq_bitTax_iff`

The original's "syndrome penalty" and "closure credit" are the same term seen
from two sides: the credit is the absence of the penalty.

### B. Shell-version NRCI — **open, with the obstruction identified**

A shell-aware coherence must not use `‖v‖²`: on the Leech minimal shell that
quantity is constant (32) and so carries no information. It must use `HW`, or
the shape class, or the distance to the shell.

### C. Codeword versus error pattern — **resolved by A**

### D. Origin of the coherence budget — **clarified**

`B` is a scale (`nrciB_eq_coh`), so `B = Z + Δ` is untestable as it stands.
The constructive alternative is to *derive* `B` rather than stipulate it: taking
`B = 8Q`, the cheapest protected distinction, makes the budget a consequence of
the code and makes all four regimes informative (§8).

---

## 15. What this system is not

It is not claimed that this is the only possible system; that this is what
reality is; that Golay or Leech are ultimate physical structures; that the
numbers are magic; or that `Y` has been established as a physical constant. Two
further disclaimers are added by this restatement:

* `Y` is not derived; it is the read operator evaluated at the stipulated
  `Π = π`;
* the coherence budget and the four thresholds are stipulated together; only
  their ratio has meaning.

The claim that remains is narrow and defensible:

> Given the stipulated constants and the chosen protected geometry, a coherent
> measurement accounting appears. It has an exact minimum (`Q`), an exact price
> of protection (`8Q`), a complete record of failure (the syndrome), and a
> coherence measure with the properties one would want. Whether it maps onto
> anything deeper remains open.

---

## 16. Final statement

The UBP, as seen here, is not a theory of everything. It is a dark-space
instrument, and each part of it now has a number:

* it begins with perfect coherence — the unique zero-tax state;
* it allows difference — at a stipulated `Δ = 2`;
* it gives difference form through `v` — summarised by `HW` and `‖v‖²`;
* it gives `v` zones and body — at `1/8` per zone;
* it checks the loop through the syndrome — which records exactly the unlawful
  part;
* it encodes distinction through MOG — uniquely up to 3 errors;
* it protects distinction through Golay — at a price of `8Q`;
* it embodies distinction through Leech — on a shell of norm 32;
* it reads distinction through `Y` — at `Q` per activation, `Q` being the least
  possible;
* it prices distinction through TAX — `HW·Q` on the code layer;
* it measures what remains through NRCI — a strictly decreasing, scale-free
  function of the tax.

And in this way the system sees itself just enough to know that it has been
read — and now, to know what that reading cost.

---

## 17. The core in one breath

> **The vacuum is perfect coherence, and nothing else is.**
> **Difference disturbs it, at a price no smaller than `Q`.**
> **The loop gives the disturbance a history, and the history is complete.**
> **MOG gives the history grammar, uniquely up to three errors.**
> **Golay gives the grammar protection, at eight quanta.**
> **Leech gives the protection a body, on a shell of norm thirty-two.**
> **`Y` gives the body a reader, at the loop-check `π` we chose.**
> **TAX measures the cost of being read.**
> **NRCI tells how much coherence remains — in whatever unit we fix.**
