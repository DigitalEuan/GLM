# Register junctions — the address read over carriers that share coordinates

## Tier 0 — the coarse read

**Question.** Can Phase 66's junction rule — a name two wheels share is one quantity only where a declared junction says so, and is split otherwise — let the address read answer the carriers it refuses because another carrier has exactly their coordinates, without changing any answer it already gives?

**Verdict.** The junction method carries over from names to coordinates where a cell of the ladder holds one junction. The `locate` read now answers a set of carriers that share exact coordinates as a **junction** — certified strictly nearer than every other carrier, exactly the scan's least-distance set, with its declaration (identity or distinct) reported beside it — from a junction table kept beside its digests. Every Phase 143 answer is unchanged on all six sets; 193 queries it refused are now answered as junctions, each one holding the carrier the query came from. 13 of the 15 duplicate carriers are read; the junction of the zero word (Golay and hexacode) is not, because every cell that holds it also holds two carriers outside it, so three marks that counted it were missed.

**Deciding figure.** 6 of 9 marks (L1, J1, J2, J3, T1, F1 met; J4, J5, Q1 missed on the zero junction); 0 answers changed and 0 wrong on six sets; 193 new junction answers (42, 34, 34, 36, 34 on the five moved sets, 13 clean); 13 of 15 duplicates read; 10 of 10 tamperings refused; census 104 junctions over 387 of 1,094 register carriers, 0 crossing a register.

**Recomputed by.** `glm_universal.reasoning.coordinate_junction_study.junction_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 144, committed with its Lean file and before
the module that takes the measurement exists. §§0–6 are as they were
committed; §7 is what came out.

It takes the line *the address read, the rest* of [`STATUS.md`](../STATUS.md)
§2.2 (left by Phase 143,
[`ADDRESS_READ_STUDY.md`](ADDRESS_READ_STUDY.md) §7.2): of the 17 clean
carriers the `locate` read refuses, 15 have exactly the coordinates of another
carrier, so their cell is shared at every rung and their placement radius is
0. Phase 143 left the choice open — merge them in the registers, or let the
read answer with the set of duplicates. The owner proposed the **junction**
method for it, and that is what this round tests.

**The junction method, as it already stands.** Phase 66
([`CONNECTED_MACHINE_STUDY.md`](CONNECTED_MACHINE_STUDY.md) §2.1) solved the
ten formula wheels together under one rule: a quantity name two wheels share
is the same variable only where a declared **junction** says both wheels mean
the same measurand of the same object; every other shared name is split
(`energy@W5`, `energy@W10`), and a relation across a declared non-identity is
a *conversion* with its own law (Phase 87's motor efficiency), never an
identity. Naive composition licensed 161 cross-wheel formulas of which 158
were wrong; the junction table kept the 3 laws and refused the 158.

**The same rule, for coordinates.** A shared *coordinate* is the substrate's
version of a shared name: two register rows whose 24 exact coordinates are
equal. The read cannot tell them apart — no function of the coordinates can
(`no_read_separates`, §1) — so what it can certify is the **junction**, the set
of carriers at those coordinates. Whether the members of a junction are *one
object filed twice* (an identity) or *distinct objects the encoding does not
separate* (a non-identity) is not something the coordinates can decide; it is
a declaration, argued per junction like Phase 66's table, and an undeclared
junction is read as distinct — the default Phase 66 gives a shared name no
junction identifies.

**Order of work, stated plainly.**

1. *What was known before this was written.* Everything in
   [`ADDRESS_READ_STUDY.md`](ADDRESS_READ_STUDY.md) §7: the 17 refused clean
   carriers by name, and that 15 of them fall in four groups of equal
   coordinates — `absorptance`/`albedo` (physics),
   `acoustic_absorption`/`acoustic_intensity_level`/`acoustic_power_level`
   (physics), the eight `filled_*` matrices (mathematics) and
   `golay_codeword_0`/`hexacode_word_0` (mathematics). While planning, the
   rows' attributes were read (which attributes differ inside each group), and
   one census was taken over the six registers in full rather than the
   142-carrier sample: **1,094** carriers, **811** distinct coordinate
   vectors, **104** groups of two or more covering **387** carriers, **0** of
   them crossing a register (102 groups in physics, 2 in mathematics). That
   census is reported in §7 again as a measurement, not a mark.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/CoordinateJunction.lean` was written and built first
   (§1).
3. **No code of the junction read or its table existed** when the marks of §4
   were written, and no query had been read through it.

## 1. What is proved before any code

`RequestProject/GLM/CoordinateJunction.lean`, on Phase 143's read
(`GLM.AddressRead.read`, unchanged) with a weaker soundness condition on the
stored entries. With `junction c i = {k | c k = c i}`:

| theorem | statement |
|---|---|
| `no_read_separates` | if `c i = c j` and `i ≠ j`, no function `f` of the coordinates has both `f (c i) = i` and `f (c j) = j` |
| `jsound_of_sound`, `JTableSound.of_tableSound` | every Phase 143 entry, and so every sound Phase 143 table, is junction-sound: the junction table contains the old one unchanged |
| `entry_junction_in_ball` | on a junction-sound entry, a carrier within `radius - dist q centre` of the query has the entry's coordinates |
| `jread_junction_nearest` | an answer `i` is strictly nearer the query than every carrier whose coordinates differ from `i`'s |
| `jread_members_tie` | every member of the answered junction is exactly as near |
| `jread_scan` | a carrier is at the least distance from the query exactly when it is in the answer's junction |
| `jread_order_independent` | two visiting orders that answer name the same junction |
| `jread_unique_in_ball` | within the margin lie the answer's junction and nothing else |
| `jread_origin` | a query that is carrier `t` moved by at most `δ`, with `δ` inside the margin, has `t` in the answered junction |
| `jread_strict_nearest_of_injective` | where no two carriers share coordinates, the junction read answers the strictly nearest carrier, as Phase 143's does |

A junction entry is junction-sound (`JSound`) when every carrier whose
coordinates differ from the entry's is at least the stored radius from the
cell centre — Phase 143's condition with "every other carrier" weakened to
"every carrier off these coordinates".

## 2. The rule

### 2.1 The junction table

A new stored table, kept beside its own digests exactly as Phase 143's is
(directive D4), and **added to** that table rather than replacing it: the
Phase 143 table, its digests and its measurement are untouched. For every rung
and every cell the address table lists as *shared*, if all the carriers in it
have equal coordinates the junction table holds that junction's members, a
representative (the first member) and the junction radius

    rho_p^2 = min over carriers k whose coordinates differ of |c_k - p|^2.

Its digests: the sources it depends on; the carriers' names and exact
coordinates; the junction declarations (§2.3); the address table's content
digest; and its own content. Any one failing makes the junction table
unusable, and the read then refuses junction cells exactly as Phase 143 does.

### 2.2 The read

The Phase 143 read, with one change: at a shared cell whose junction entry
exists, the placement guard `|q - c_rep| + |q - p| < rho_p` is decided exactly
and, if it holds, the read answers **the junction**. A single-carrier cell is
read exactly as before. The junction read is reached only by the `locate`
kind; `address_read.read_point` keeps Phase 143's behaviour by default, so the
Phase 143 measurement is unchanged.

### 2.3 The declarations

One row per junction of the declared sample, argued here, before any read:

| junction | declared | why — what the coordinates do not carry | relation |
|---|---|---|---|
| `physics:absorptance`, `physics:albedo` | distinct | both are dimensionless ratios of the same domain code; absorptance is the absorbed fraction of incident radiation, albedo the reflected fraction | for an opaque surface, absorptance = 1 − albedo (a conversion, not an identity) |
| `physics:acoustic_absorption`, `physics:acoustic_intensity_level`, `physics:acoustic_power_level` | distinct | the encoding holds the dimension (all three are dimensionless) and the domain; a coefficient and two levels in decibels against different references (1 pW/m², 1 pW) | power level = intensity level + 10 log10(S / 1 m²) over a surface S |
| the eight `filled_RxC` matrices | distinct | the carrier holds the 24 entries in row order; the shape (`rows`, `cols`) is not a coordinate | a reshape: the same entries, different matrices |
| `mathematics:golay_codeword_0`, `mathematics:hexacode_word_0` | distinct | the all-zero vector in both; the field (2 against 4) and the length (24 against 6 symbols) are not coordinates | the zero word of each code |

No junction of the sample is declared an identity: each pair is two
measurands or two objects that the encoding does not separate. An *identity*
row (one object filed under two names) is the other declaration the table
accepts; the census of §7 will say whether the full registers hold any
candidates. A junction with no row is answered and reported **undeclared,
read as distinct**; a declaration whose members are not a junction of the
live carriers makes the table stale.

### 2.4 The answer

`locate albedo` answers, for example: *physics:albedo reads as the junction
{physics:absorptance, physics:albedo} at rung …: these 2 carriers have the same
coordinates, so no read can separate them; the point is certified strictly
nearer to their coordinates than to any other carrier; declared distinct
(…); the request names physics:albedo, which is in the junction.* Column 3
re-checks it by a full scan: the scan's least-distance set must be exactly the
claimed junction, and its members' coordinates equal.

## 3. The questions, declared here

| id | question | declared |
|---|---|---|
| J-B1 | `locate albedo` | answered, junction {absorptance, albedo}, origin `physics:albedo` in it |
| J-B2 | `locate physics:absorptance` | answered, the same junction |
| J-B3 | `locate filled_4x6` | answered, the junction of the eight `filled_*` |
| J-B4 | `locate golay_codeword_0` | answered, junction {golay_codeword_0, hexacode_word_0} |
| J-B5 | `locate acoustic_power_level` | answered, the three-member acoustic junction |
| J-B6 | `locate` the all-zero point (Phase 143's B9) | answered, the golay/hexacode junction |
| J-B7 | `locate albedo moved 1 by 1/4` | read (no prediction) |
| J-B8 | `locate filled_2x12 moved 4 by 1/2` | read (no prediction) |
| J-B9 | `locate high_denominator_2x3` | refused `no-certified-rung` (not a duplicate) |
| J-B10 | `locate C` | answered `chemistry:C`, as in Phase 143 |

## 4. The marks, declared before the code

* **L1** — `RequestProject/GLM/CoordinateJunction.lean` builds with no
  `sorry` and the standard axioms only.
* **J1 — the junction table is sound.** Recomputed from scratch, the stored
  junction table equals the recomputation, and every entry is junction-sound
  by an exact scan of all 142 carriers: 0 unsound entries.
* **J2 — no regression.** On all six query sets of Phase 143 (the four of
  Phase 129, the fifth, the clean set), every query the Phase 143 read answers
  is answered by the junction read with the same carrier at the same rung, as
  a one-member junction: **0** changed. Every query the Phase 143 read refuses
  is either still refused or answered with a junction of two or more members.
* **J3 — every junction answer is sound.** For every junction answer on every
  set: the scan's least-distance set is exactly the junction, no carrier off
  the junction lies within the reported margin, the three visiting orders
  answer the same junction, and when the origin is certified the query's own
  carrier is in the junction: **0** violations of any kind.
* **J4 — the duplicates are read.** On the clean set, **15 of 15** duplicate
  carriers are answered with their own junction, and the 2 other refused
  carriers (`high_denominator_2x3`, `rational_root_thirds`) are still refused.
* **J5 — the declarations.** Every junction a read can answer on the sample
  has a declaration (4 of 4); with each declaration removed in turn, the
  answer reports the junction *undeclared, read as distinct* and never as one
  object; a declaration naming members that are not a junction of the live
  carriers makes the table stale.
* **T1 — the digests.** Ten tamperings of the junction table (radius raised,
  radius lowered, member dropped, member added, representative swapped,
  entry deleted, live carrier moved, declaration altered, address table
  altered, file absent) each leave the read refusing junction cells as
  Phase 143 does, and none produces a junction answer from a tampered table.
* **Q1 — the questions.** The ten questions of §3 come out as declared where
  declared; every answer's column-3 script passes; three mutations of every
  junction answer (a member dropped, a stranger added, the margin raised) are
  each rejected.
* **F1 — the frozen path.** The end-to-end evaluation's earlier 195 cases keep
  their verdicts, and the new cases pass.

## 5. What this round does not do

* It does not merge, rename or re-encode any register row: the registers keep
  every carrier they hold. Whether the encoding should carry the attributes
  that separate a junction (§2.3's third column) is a decision for the
  registers, and §7 reports what the census says it would take.
* It does not declare the 100 junctions of the full registers outside the
  142-carrier sample; it measures them.
* It does not let any other reading of the ladder answer a junction (the
  escalation reports, `nearest`): that is item 1 of §2.1 and needs a
  frozen-path comparison of its own.

## 6. Files

* `glm_lean/RequestProject/GLM/CoordinateJunction.lean` — §1.
* `glm_universal/reasoning/coordinate_junction.py` — the declarations,
  the junction table and its digests, the junction read and the census.
* `glm_universal/reasoning/coordinate_junction_study.py` — the marks.
* `glm_universal/runtime/session.py`, `runtime/tct_engine.py` — the
  `locate` answer and its column-3 script.
* `glm_universal/tests/test_coordinate_junction.py` — the tests.
* `tools junction-table [--write]`, `tools junction-read [--write]`.

## 7. What came out

Measured by `PYTHONPATH=. python3 -m glm_universal.tools junction-read`
(cache `reasoning/_data/coordinate_junction_study.json`, kept beside the
digest of its sources and of both stored tables); the junction table is
`tools junction-table`. **6 of 9 marks met.** The three missed marks miss for
one reason, stated in §7.3.

| mark | result |
|---|---|
| L1 | met — `CoordinateJunction.lean` builds, no `sorry`, standard axioms |
| J1 | met — 21 junction entries on the eleven rungs; equal to a recomputation from fresh cells; 0 unsound by exact scan |
| J2 | met — 0 Phase 143 answers changed on six sets; every new answer is a junction of two or more |
| J3 | met — 0 junction answers off the scan's least-distance set, 0 margin violations, 0 order disagreements, 0 origin violations |
| J4 | **missed** — 13 of 15 duplicates read (declared 15 of 15); the 2 non-duplicates still refused, as declared |
| J5 | **missed** — 3 of 3 answerable junctions declared, removals observed on 3; the fourth declared junction is never answered, so its removal cannot be seen (declared 4 of 4); a stale declaration makes the table stale, as declared |
| T1 | met — 10 of 10 tamperings refused, none producing a junction answer |
| Q1 | **missed** — 6 of 8 declared questions as declared (J-B4, J-B6 refused); 7 of 7 answers' scripts pass; 18 of 18 mutations rejected |
| F1 | met — the end-to-end evaluation (§7.6) |

### 7.1 The six sets (J2, J3)

| set | queries | Phase 143 answered | junction read: single | junction | refused | wrong |
|---|---|---|---|---|---|---|
| standard | 568 | 445 | 445 | 42 | 81 | 0 |
| held-out | 568 | 402 | 402 | 34 | 132 | 0 |
| third | 568 | 393 | 393 | 34 | 141 | 0 |
| fourth | 568 | 402 | 402 | 36 | 130 | 0 |
| fifth | 568 | 402 | 402 | 34 | 132 | 0 |
| clean | 142 | 125 | 125 | 13 | 4 | 0 |

Every single-carrier answer is the Phase 143 answer, carrier and rung, query
by query: the junction table only adds entries at cells Phase 143 left shared,
and `jsound_of_sound` is why nothing else can move. A junction answer is
counted *wrong* if the query's own carrier is not in it; there are none, and
every one of the 193 is the exact least-distance set of a full scan
(`jread_scan`), its margin honest, the three visiting orders answering the
same junction and the origin certified in it (`jread_origin`). On the moved
sets the answers are the `filled_*` junction and the `absorptance`/`albedo`
junction; the acoustic junction is answered on the standard and clean sets
only (its margin, 0.732, is the smallest of the three).

### 7.2 The digests (T1) and the declarations (J5)

Each tampering fails the digest it should: the six edits of an entry fail
`content`; a moved live carrier fails `carriers` and `address` (the address
table goes stale with it); an altered declaration fails `declarations`; an
altered address table fails `address`; an absent file loads nothing. In every
case the read falls back to Phase 143's — the junction cells are read as
shared — and no junction answer comes out.

With each declaration removed and the table re-taken under the remaining
three, the three answerable junctions are reported *undeclared, read as
distinct*, never as one object. A declaration naming `physics:absorptance`
and `chemistry:C` (not a junction) makes the table stale.

### 7.3 The zero junction, and the three missed marks (J4, J5, Q1)

`golay_codeword_0` and `hexacode_word_0` are both the all-zero vector. At
every rung of the ladder the cell holding the origin also holds
`high_denominator_2x3` and `rational_root_thirds` — the two clean carriers
Phase 143 refused for crowding, not for duplication — and at the finest rungs
(D12², Z) it holds exactly those four. So the zero junction's cell is never
one junction, there is no junction entry for it, and the read refuses it with
`no-certified-rung` as Phase 143 did. That is the declared behaviour of the
read; the marks that counted the zero junction as readable (J4's 15 of 15,
J5's fourth removal, Q1's J-B4 and J-B6) were predictions the measurement did
not bear out, and they stay recorded as missed rather than restated. The
zero junction is a crowding problem of the same kind as the two carriers that
crowd it: a junction reading does not touch it.

### 7.4 The census of the full registers

Over the six registers in full (1,094 carriers, not the 142 of the sample):
811 distinct coordinate vectors; **104 junctions** of two or more members
covering **387** carriers; **0** crossing a register (102 in physics, 2 in
mathematics); the largest has 78 members (the dimensionless physics ratios).
Which attributes would separate the members of a junction — the attributes
the coordinates do not carry: `gloss` and `symbol` separate every member of
all 102 physics junctions; `unit` separates only 8; in **87** of the 104 the
members differ in nothing but name, symbol and gloss. The physics carrier is a
dimension vector with a domain code, so two quantities of the same dimension
and domain coincide; carrying the unit would split 8 junctions, and the rest
would need a coordinate for the measurand itself. Whether the registers should
carry one is the owner's decision (§7.7).

### 7.5 The questions (Q1)

| id | question | came out |
|---|---|---|
| J-B1 | `locate albedo` | junction {absorptance, albedo}, rung C, margin 3.605, origin in it — as declared |
| J-B2 | `locate physics:absorptance` | the same junction — as declared |
| J-B3 | `locate filled_4x6` | the eight `filled_*`, rung C, margin 26.104 — as declared |
| J-B4 | `locate golay_codeword_0` | refused `no-certified-rung` — **declared a junction** |
| J-B5 | `locate acoustic_power_level` | the acoustic junction, rung A/2, margin 0.732 — as declared |
| J-B6 | `locate` the all-zero point | refused `no-certified-rung` — **declared a junction** |
| J-B7 | `locate albedo moved 1 by 1/4` | the absorptance/albedo junction, origin certified (read) |
| J-B8 | `locate filled_2x12 moved 4 by 1/2` | the `filled_*` junction at rung 2A, origin certified (read) |
| J-B9 | `locate high_denominator_2x3` | refused `no-certified-rung` — as declared |
| J-B10 | `locate C` | `chemistry:C`, unchanged — as declared |

Column 3 re-checks a junction answer by a full scan: the least-distance set
must be exactly the claimed junction with its members at one coordinate
vector, the margin must hold for every carrier off the junction, and a claimed
origin must be in the junction with nothing off it inside the move. Dropping a
member, adding the nearest stranger, or raising the margin past the nearest
stranger is each rejected (18 of 18 over six junction answers).

### 7.6 The frozen path (F1)

The evaluation holds three new `locate` cases (`locate-junction`,
`locate-junction-moved`, `locate-junction-crowded`), and the full run passed
196 of 198. The earlier 195 keep their verdicts (answered or refused); two of
them, `report-relay` and `report-anonymous`, failed only on pinned figures
that count queries drawn from the Lean declarations, which the new Lean file
moved from 813 to 817. Both were re-pinned with their claims unchanged and
pass on their own, as do the three new cases. The frozen-path comparison
(`tools frozen-path`, 178 of 178 baseline cases with the same status) and
the query-escalation cache were re-taken.

### 7.7 Verdict, and what it leaves

The junction method carries over from names to coordinates as it stands: a
shared coordinate is answered as one junction, certified as Phase 143's
answers are, and what its members *are* is a declaration, never inferred.
193 queries are answered that were refused, and nothing that was answered
moves. What it leaves:

* **The zero junction** is crowded by `high_denominator_2x3` and
  `rational_root_thirds`; reading those three needs a finer cell near the
  origin than the ladder has, not a junction.
* **The full registers' 104 junctions** are measured, not declared: a
  register larger than the sample must re-take both tables, and each new
  junction a read can answer should get a declaration (until then it is read
  as distinct, which is never wrong, only less informative).
* **The registers' decision.** 87 of the 104 junctions differ only in name,
  symbol and gloss: either the encoding gains a coordinate for the measurand,
  or the junctions stay as the honest answer. No row was merged or re-encoded
  in this round.
* **The other readings of the ladder** (escalation reports, `nearest`) do not
  read junctions yet; that rides with item 1 of `STATUS.md` §2.1.
