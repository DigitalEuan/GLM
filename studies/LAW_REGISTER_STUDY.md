# The UBP law register, re-read through the GLM

## Tier 0 — the coarse read

**Question.** Do the sixty-five laws the earlier GLM-lens review retained hold up when each claim is re-read at GLM resolution, and does anything in them make the GLM reason better?

**Verdict.** The structural half holds and is now proved or cited in Lean, with three decoder laws made exact and two overclaims refuted; of the numeric half, only the two muon formulas survive the look-elsewhere test, and the GLM now refuses the rest by name.

**Deciding figure.** 10 of 16 exact rows are structural or overclaimed, each citing Lean; 2 of 21 external formulas admitted at p < 1/100 (both m_mu/m_e, 158 and 13204 standard deviations from the measurement); refusing a six-way tie withholds 5 wrong answers per right answer given up; 9 of 9 marks met.

**Recomputed by.** `glm_universal.reasoning.law_register.law_register_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner supplied two files from an older study of the UBP knowledge base,
now kept in `source_material/`:

* `source_material/UBP_LAW_GLM_REVIEW.md` — a three-round review of the 426
  `LAW_*` entries of the UBP knowledge base, read through GLM instruments
  (Round 1: carriers and NRCI; Round 2: content; Round 3: Griess clustering).
* `source_material/retained_laws_verified_65.csv` — the 65 laws of Round 2's
  two strongest pass classes: 16 `RETAINED-EXACT` ("reproduces exactly under
  GLM recomputation") and 49 `RETAINED-NUM` ("numeric formula verified against
  measured value").

The owner's question: do these hold up, can they be improved, and are they
useful to the GLM in a measurable way? The particle-physics formulas are
experimental; they are audited once, uniformly, and not pursued.

## 1. Declarations — written before any measuring code

Everything is exact: integers and `Fraction` (D7). Reals (π, φ, e, square
roots, logarithms) are read through `reasoning.real_expr`, which returns an
exact rational within a stated precision; nothing is a float.

### 1.1 The sixteen `RETAINED-EXACT` rows

Each row is re-graded into exactly one class:

| class | meaning |
|---|---|
| **structural** | a theorem of the code or lattice; must cite a Lean theorem that builds |
| **definitional** | the "law" is a definition GLM already uses; true by construction |
| **arithmetic** | the arithmetic reproduces, but the reading placed on it is not a statement GLM can test |
| **near-miss** | a numeric coincidence (a value close to, not equal to, a substrate number) |
| **overclaimed** | the precise part holds and a stated generalisation fails; the failure is proved |

**R1.** Every arithmetic figure quoted in the sixteen rows reproduces under
exact recomputation.
**R2.** Every row gets exactly one class, and every *structural* or
*overclaimed* row cites at least one Lean theorem that builds without `sorry`.

### 1.2 Three structural laws made precise

The register states three things about the decoder in words: "1-bit
correction" (`LAW_COMP_005`), "at 4 bits of noise a vector enters a deep hole,
equidistant to multiple truths" (`LAW_FOURTH_FLIP_001`), and "hardened storage
guarantees 100% data integrity when environmental noise is ≤ 3%"
(`LAW_STORAGE_HARDENED_001`, filed as numeric).

**R3.** The exact outcome of complete decoding for every error weight
`k = 0 … 24` — right, refused (a six-way tie), or wrong (a unique but
different codeword) — is computed from the coset weight enumerators and checked
to sum to `C(24, k)`; and the three statements behind it are proved in Lean:
the decoder is right exactly when `k ≤ 3`, weight 4 is always refused, weight 5
is always miscorrected. `LAW_STORAGE_HARDENED_001` is then decided at noise
3%: held if the probability of anything but a right answer is 0, refuted
otherwise, with the exact figure.
**R4.** The price of refusal, per bit-flip rate `p ∈ {1/100, 3/100, 5/100}`:
against the retired "snap" (which picks one of the six tied codewords), the
wrong answers the complete decoder withholds and the right answers it gives up,
both exact.

### 1.3 Two statistics of Round 2

**R5.** Round 2 reports the mean shell-0 NRCI "over the 4096 codewords" and
"over random vectors (exact binomial)" as the same number, 0.684298. Decided:
equal or not, as exact rationals, with the reason proved in Lean.
**R6.** Round 2 reports that "greedy syndrome descent converges to a codeword
in *exactly* d steps from distance d = 1..4 (always minimum-length)", and
retains `LAW_PATH_LEAST_ACTION` and `LAW_COMP_005` on it. Decided against the
exhaustive descent census of `reasoning.deep_dive` and `Relaxation.lean`.

### 1.4 The forty-nine `RETAINED-NUM` rows

**R7.** Every row gets exactly one category, decided by reading the row's own
target, not by recomputing it:

| category | meaning | admissible as a derived number? |
|---|---|---|
| **external** | a dimensionless measured quantity | only through R8 |
| **unit-dependent** | a dimensional quantity matched as a pure number in a chosen unit (GeV, MeV, eV, km/s/Mpc, SI, degrees, seconds); changing the unit changes the number and not the physics | no |
| **not-a-measurement** | the target is a bound, a range, or an experimental uncertainty | no |
| **KB-internal** | the formula reproduces a number the knowledge base itself states; nothing outside is predicted | no |
| **restatement** | a standard textbook identity | no (true, not UBP's) |
| **duplicate** | the same formula and target as another row | counted once |

**R8.** The look-elsewhere test. For each *external* formula, the **template**
is the formula with its small integers turned into slots over declared ranges
(the table in §1.5; named constants — `Y`, π, φ, e, `w`, 196560, 13824 — stay
fixed). The law's own relative error `ε = |value − target| / target` is
computed. The **chance coverage** `p` is the fraction of the window
`[T/2, 2T]` (linear measure, `T` the target) lying within relative error `ε`
of some member of the template. `p` is the probability that a target drawn
uniformly from the window would be hit at least as well by the template — the
within-template look-elsewhere effect. It is a lower bound on the true trial
factor, because the choice of template is itself free. A formula is
**admitted** when `p < 1/100`, **refused** otherwise. Targets are the values
quoted in Round 2's numeric battery; this round does not re-audit them.

**R9.** The re-graded register, the decoder outcome table and the admission
test are callable from the GLM (`tools law-register`, and a toolbox tool
`law register` taking a law id), and the admission test refuses every
non-external row with its category named.

### 1.5 The templates of R8

| row | template | slots |
|---|---|---|
| `LAW_LEPTON_001` | `(1/Y)^a + b − Y^c` | a 1–6, b 0–24, c 1–6 |
| `LAW_PHYSICS_MUON_002` | `a²/w` | a 1–24 |
| `LAW_BARYON_001` | `a·(1/Y)^b + (1/Y − c) − Y` | a 1–24, b 1–6, c 0–24 |
| `LAW_NUM_001` | `(1/Y)^a + (1/Y − c) − Y` | a 1–6, c 0–24 |
| `LAW_PARTICLE_RESONANCE_001` | `a·(1/Y)^b + c/Y + Y` | a 1–24, b 1–6, c 0–24 |
| `LAW_TAU_RESONANCE_001` | `[17/Y⁴ + 2/Y + Y] + (1/Y)·a/b + c·Y` | a 1–24, b 1–24, c 0–24 |
| `LAW_CABIBBO_MIXING_001` | `(Y/(1+Y))·a/b + Y/c` | a 1–24, b 1–24, c 1–48 |
| `LAW_CKM_SHEAR_001` (V_ub) | `Y^a / b` | a 1–6, b 1–24 |
| `LAW_CKM_SHEAR_001` (V_cb) | `Y^a · b / c` | a 1–6, b 1–24, c 1–48 |
| `LAW_WEINBERG_RESONANCE_001` | `Y / (1 + φ/a)` | a 1–24 |
| `LAW_HIGGS_TENSION_001` | `(1 + Y·√a) − Y/b` | a 1–24, b 1–240 |
| `LAW_FORCE_002` | `(1/Y)^a + b + c·Y^d/2` | a 1–6, b 0–100, c 1–24, d 1–6 |
| `LAW_HORIZON_001` | `a` | a 1–200 |
| `LAW_PHYSICS_001_REFINED` | `a·((π − 1) − b/13824)` | a 1–128, b 1–24 |
| `LAW_PHYSICS_003_REFINED` | `196560^a · (1/Y) / b` | a 1–12, b 1–24 |
| `LAW_MECH_001` (baryon) | `Y^(−a/100)` | a 100–800 |
| `LAW_MECH_001` (lepton) | `Y^(−a)` | a 1–12 |
| `LAW_MESON_PION_001` | `a · 10^b · Y` | a 1–24, b 0–4 |
| `LAW_ISOTOPIC_FRICTION_001` | `2 − RG/a`, `RG = ln φ / ln π` | a 1–48 |
| `LAW_TOP_KISSING_001` | `196560 · √a · (1 − Y/b)` | a 1–24, b 1–48 |
| `LAW_NOBLE_SCALING_001` (Ar) | `Y^(a/b)` | a 1–6, b 1–6 |

The ranges are the ones the register's own formulas draw from: coefficients
and denominators up to 24 (the word length), exponents up to 6, and the
register's larger literals (40, 83, 120, 64, 5.65) inside their ranges.

---

## 2. Results

Recomputed by `glm_universal.reasoning.law_register.law_register_report`
(`PYTHONPATH=. python3 -m glm_universal.tools law-register`); pinned by
`tests/test_law_register.py`; the decoder and moment facts are theorems of
`RequestProject/GLM/LawRegister.lean`. All 9 of 9 marks met.

### 2.1 The sixteen exact rows (R1, R2)

Every arithmetic figure the rows quote reproduces (R1). One defect of the
supplied file first: its evidence column is **one identical sentence for all
sixteen rows** — a list of structural facts, not a test of each law. The
re-grade replaces it with per-row evidence.

| class | n | rows |
|---|---|---|
| structural | 8 | `COMP_005`, `COMP_009`, `FOURTH_FLIP_001`, `GATEWAY_002`, `GOLAY_UNIQUENESS_001`, `KISSING_EXPANSION_001`, `RELATION_002`, `RELATION_ORTHO_001` |
| overclaimed | 2 | `LOGIC_GEO_001`, `PATH_LEAST_ACTION` |
| definitional | 3 | `LEECH_TAX_001`, `METRIC_002`, `RESOLUTION_GAP_001` |
| arithmetic | 2 | `ARX_HORIZON_006`, `LEECH_TENSION_001` |
| near-miss | 1 | `INTERFACE_CLOSURE_001` (φ³/RG² = 23.97156, 0.12% short of 24) |

Every structural and overclaimed row is cited to a Lean theorem that builds (R2):
`unique_leader_iff`, `covering_radius_eq_four`, `tetrad_class_card`,
`unique_vs_ambiguous`, `golay23_perfect_arithmetic`,
`leechMinimalClass_counts`, `golay_min_distance_eight`,
`golay_weight_enumerator`, `card_codewords`, and for the overclaims
`and_not_closed`, `or_not_closed` and `relaxation_is_not_decoding`. Most were
already in the tree: the register's structural content was, in large part,
already GLM mathematics.

**The two overclaims.** `LAW_LOGIC_GEO_001` ("Boolean logic is isomorphic to
vector arithmetic in the Golay substrate"): exclusive-or of codewords is a
codeword, but of the 287,661 pairs of distinct octads only the 11,385 disjoint
pairs have a codeword AND (15/379), and the same fraction a codeword OR;
`and_not_closed` and `or_not_closed` exhibit two generator rows whose AND has
weight 4 and whose OR has weight 12 and is not in the code. Only XOR is a code
operation. `LAW_PATH_LEAST_ACTION` and `LAW_COMP_005`'s "snap" reading: see
§2.4.

### 2.2 The decoder laws, exact (R3, R4)

For an error of weight `k`, complete decoding is **right** when the error is
the unique lightest word of its coset, **refused** when the coset has weight 4
(six nearest codewords tie), and **wrong** otherwise. The coset weight
enumerators agree between two leaders of each weight and close to `C(24, k)`
for every `k`, so the table is exact:

| error weight | right | refused | wrong |
|---|---|---|---|
| 0–3 | all | 0 | 0 |
| 4 | 0 | all 10,626 | 0 |
| 5 | 0 | 0 | all 42,504 |
| 6 and up | 0 | some | some |

The three facts behind it are proved: `unique_leader_iff` (right exactly when
`k ≤ 3`), `wt_four_refused`, and `wt_five_coset_three` (a weight-5 error lies
in a weight-3 coset through the unique octad on its five points, so the decoder
answers and is wrong).

**`LAW_STORAGE_HARDENED_001` is refuted.** At noise 3% a complete decoder is
not right with probability 0.005321 and silently wrong with probability
0.0005925. "100% integrity at noise ≤ 3%" holds at no positive noise rate.

**The price of refusal (R4).** Against the retired snap, which picks one of the
six tied codewords (right one time in six on a weight-4 error, never right on a
heavier one):

| bit-flip rate | right | refused | wrong | wrong withheld by refusing | right given up |
|---|---|---|---|---|---|
| 1/100 | 0.999909 | 0.000087 | 0.0000035 | 0.0000725 | 0.0000144 |
| 3/100 | 0.994678 | 0.004728 | 0.0005925 | 0.0039484 | 0.0007800 |
| 5/100 | 0.970217 | 0.024522 | 0.0052600 | 0.0205544 | 0.0039679 |

Refusing withholds 5 wrong answers per right answer given up at every rate (5.00,
5.06, 5.18). This is the register's "deep hole requires external bias" made
into a price, and it is a measurement of the GLM's refusal rule, not of the
register: the complete decoder already refuses.

### 2.3 The two statistics (R5)

Round 2 reports the mean shell-0 NRCI over the codewords and over all words as
one number, 0.684298. As exact rationals they are **not equal**: 0.684298208
against 0.684298185, a difference of 0.000000023478. The six decimals agree
because the first seven weight moments of the code equal the binomial ones and
the eighth does not (`moment_agree`, `moment_eight_differs`; the codewords form
an orthogonal array of strength 7, the dual distance being 8). The NRCI is not a
polynomial in the weight, so the agreement is approximate
(`nrci_means_differ`). The noise-floor refutation stands and is now proved:
the lowest NRCI of any 0/1 carrier is 0.516736, above 1/2 (`nrci_floor`).

### 2.4 The descent claim (R6)

Round 2 retained `LAW_PATH_LEAST_ACTION` and `LAW_COMP_005` on "greedy syndrome
descent converges to a codeword in *exactly* d steps (always minimum-length)".
The exhaustive census of `reasoning.deep_dive` contradicts it: 792 of the 4,096
cosets have no improving-flip descent as short as their distance (66 of
distance 2 need six flips, 726 of distance 3 need five), and greedy descent is
not optimal (`relaxation_is_not_decoding`). The 200 random trials per distance
of Round 2 did not find what the exhaustive census finds. What holds is the
trivial reading — flipping the coset leader's own bits reaches the nearest
codeword in `d` steps — which *is* the decoder, not a dynamics. Both rows are
filed overclaimed.

### 2.5 The forty-nine numeric rows (R7, R8)

| category | n |
|---|---|
| external | 19 |
| unit-dependent | 7 |
| not-a-measurement | 3 |
| KB-internal | 14 |
| restatement | 1 |
| duplicate | 4 |
| structural (`STORAGE_HARDENED`, decided in §2.2) | 1 |

Thirty of the forty-nine "numeric formula verified against measured value"
rows are not predictions of a measured dimensionless number: seven match a
dimensional quantity as a pure number in a chosen unit (G in SI, H0 in
km/s/Mpc, boson masses in GeV, an angle in degrees), three match a bound, a
range or an experimental uncertainty, fourteen reproduce a number the
knowledge base itself states, one is the textbook identity `m_W/m_Z = cos θ_W`,
and four repeat another row.

The look-elsewhere test on the 21 external formulas (the template table is in
§1.5):

| formula | quantity | error | template members | chance coverage p | verdict |
|---|---|---|---|---|---|
| `LEPTON_001` | m_μ/m_e | 0.0003% | 900 | 0.0006 | admitted |
| `PHYSICS_MUON_002` | m_μ/m_e | 0.0293% | 24 | 0.0042 | admitted |
| `TAU_RESONANCE_001` | m_τ/m_e | 0.0248% | 14,400 | 0.0189 | refused |
| `MECH_001` (lepton) | m_μ/m_e | 1.4488% | 12 | 0.0190 | refused |
| `NUM_001` | m_τ/m_μ | 0.1699% | 150 | 0.0224 | refused |
| `NOBLE_SCALING_001` (Ar) | BP ratio | 0.1291% | 36 | 0.0258 | refused |
| `PHYSICS_003_REFINED` | EM/gravity | 0.9442% | 288 | 0.0276 | refused |
| `HORIZON_001` | 1/α as 137 | 0.0262% | 200 | 0.0453 | refused |
| `MESON_PION_001` | m_π0/m_e | 0.1977% | 120 | 0.0475 | refused |
| `ISOTOPIC_FRICTION_001` | m_D/m_H | 0.7691% | 48 | 0.0689 | refused |
| `PHYSICS_001_REFINED` | 1/α | 0.0081% | 3,072 | 0.0753 | refused |
| `BARYON_001` | m_p/m_e | 0.0170% | 3,600 | 0.1478 | refused |
| `WEINBERG_RESONANCE_001` | sin²θ_W | 0.8683% | 24 | 0.1475 | refused |
| `CKM_SHEAR_001` (V_ub) | V_ub | 0.7680% | 144 | 0.2652 | refused |
| `FORCE_002` | 1/α | 0.0019% | 87,264 | 0.3858 | refused |
| `PARTICLE_RESONANCE_001` | m_τ/m_e | 0.1494% | 3,600 | 0.4237 | refused |
| `HIGGS_TENSION_001` | m_H/m_Z | 0.1048% | 5,760 | 0.4544 | refused |
| `TOP_KISSING_001` | m_top/m_e | 0.3680% | 1,152 | 0.6870 | refused |
| `MECH_001` (baryon) | m_p/m_e | 0.5146% | 701 | 0.7736 | refused |
| `CABIBBO_MIXING_001` | V_us | 0.3118% | 27,648 | 1.0000 | refused |
| `CKM_SHEAR_001` (V_cb) | V_cb | 2.5167% | 6,912 | 1.0000 | refused |

2 of 21 admitted, against 21/100 expected false admissions at the declared
threshold. The best-known formula of the set, `FORCE_002`'s
`(1/Y)³ + 83 + 1.5·Y²` for 1/α at 0.0019%, is refused: its own template hits a
random target in the window that closely 39% of the time.

**Not declared, recorded.** Two checks were added after R8 was read, and are
not counted as marks:

* *Decoy control.* For each admitted template, 100 decoy targets evenly spaced
  across `[T/2, 2T]`, each fitted by the template's best member as a search
  would fit it: the test admits 1 of 100 (lepton) and 2 of 100 (muon). The
  threshold is calibrated where it matters.
* *Against the measurement.* m_μ/m_e = 206.7682830(46). `LEPTON_001` misses it
  by 158 standard deviations and `PHYSICS_MUON_002` by 13204. Both survive
  chance at their templates and both are approximations, not laws — "not
  numerology" and "true" are different verdicts, and the GLM's answer now says
  which one it is giving.

### 2.6 Into the GLM (R9)

* `reasoning.law_register.admit(law_id)` answers any of the 65 rows:
  admitted, admitted in part, or refused with its class named; every
  non-external numeric row is refused by name.
* `reasoning.law_register.look_elsewhere(value, ranges, instance, target)` is
  the same test on a new claim: a formula, its slot ranges, the claimed
  instance and the target. An exact claim has coverage 0 and is admitted.
* `GLM.py --ask "tool law register LAW_FORCE_002"` (toolbox, faculty
  *refusal*) and `tools law-register [--law ID] [--json]`.

## 3. What this round moved

Against the standing target (`PROJECT_DIRECTIVES.md`): **refusal**. Before the
round the GLM had no way to decline a numeric coincidence; it now refuses 47 of
the 49 "verified" numeric laws with a named, checkable reason, admits 2, and
says of those 2 that they miss the measurement. The decoder table prices the
refusal the GLM already makes at a six-way tie (5 wrong answers withheld per
right answer given up). Nothing here is *derivation*: the structural laws were
already GLM mathematics, and the round's Lean adds four theorems about them
rather than a new capability.

**Negative results kept.** The numeric half of the register does not survive
at the resolution the GLM reads it (19 of 21 external formulas refused, 30 of
49 rows not predictions); `LAW_STORAGE_HARDENED_001`, `LAW_LOGIC_GEO_001` and
the descent reading of `LAW_PATH_LEAST_ACTION` are refuted; and the review's
own statistics needed two corrections (the two means, the descent).

**Not done.** The 106 `UNRESOLVED-UBP` laws, the Round-3 Griess clustering and
the Round-1 carrier vectors were not re-tested: the supplied files carry the 65
retained rows only, not the vectors or the knowledge base.
