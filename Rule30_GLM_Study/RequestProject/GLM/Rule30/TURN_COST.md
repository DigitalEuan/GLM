# Round 37: the cost of a turn, the observer's best phase, and the GLM indexed by hubs

This round took **To Do 39, 40 and 41**, with To Do 41 first: measurable results and exact
improvement requirements. None of the three prize problems is settled.

| To Do | Short answer | Where |
|---|---|---|
| 40 — the cost of a turn | **Exact, proved for all `d`**: starting the clock `m` steps later costs `m` + (tests skipped). In 66 of the 69 wheels with more than one phase (periods 2–8, `d ≤ 28`) some pair of phases attains this bound exactly. So, as a general rule, it cannot be lowered. Each wheel has a **best phase**. A slack at that one phase is enough. | `TurnCost.lean`, `TurnCostData.lean` |
| 39 — an infinite family of hubs | **Partly.** The hubs `1^(q−1)0` (one black run per period) are hubs for every `q ≥ 2`. For every `q` and every code length `d ≤ q − 4`, every code fails within `d + 2` tests, uniformly in `q` and `d`. What remains is exactly the codes of length `d ≥ q − 3`. The whole family contains the open period-2 rung. | `OneRunFamily.lean` |
| 41 — the GLM indexed by hubs | **Done, measured.** `tool hub`, `tool hubs` and `tool requirements` are new. `tool next` now proposes hubs first, and the theorem wheel has the hub rule. Consultation went from 0/11 to 11/11 on questions frozen before the overlay was written. The hub index is exact on all 8178 words of period `≤ 12`. | study folder `rule30_round37/` |

---

## 1. The exact cost of a turn (To Do 40) — FORMAL

Round 36 bounded a turn by `2` slack per step of phase (`testSlack_wheelTurn`). The exact price is:

* one step over a **white** time costs `1`, and one step over a **black** time (a test) costs `2`
  (`testSlack_of_shift_exact`);
* `m` steps cost `m + testsBefore bd m` (`testSlack_of_shift_count`), and the same holds on finite
  ranges (`testSlackUpTo_of_shift_count`: a certificate on `d ≤ D + m` gives one on `d ≤ D`);
* between two phases `a`, `b` of one wheel, with `a + m ≡ b (mod p)`:

  `slack(a) ≤ slack(b) + m + testsBefore (phase a) m`  (`testSlack_phase_transfer`,
  `testSlack_wheelTurn_transfer`, finite-range forms `…UpTo…`).

**The observer's best phase** (your *perspective* idea, in exact form). Every phase of a wheel
controls every other phase. So the observer may read each wheel from the phase where it is
cheapest:

* `wordDies_of_phase`: a slack at any one phase kills every half-line under every phase;
* `testCountLinear_of_phases`: one phase per wheel with slack `c` gives `TestCountLinear p (c + 2(p − 1))`;
* `wheelDies_of_phases`: one phase per wheel with some slack gives `WheelDies` (hence Problem 1);
* **period 2** (`testCountLinear_two_of_phase`): `TestSlack (driveN 2 2) 3 → TestCountLinear 2 5`.
  The phase `01` (black at odd times) with slack 3 gives the *optimal* period-2 law for all `d`;
* **period 3** (`testCountLinear_three_of_phases`): the phases `010` (slack 5) and `101` (slack 2)
  give the optimal `TestCountLinear 3 8`.

### Certified (CERT, `TurnCostData.lean`, `frontier_round37`)

| period | best phase | least slack, certified range | the hub phase needs | gap = proved turn cost |
|---|---|---|---|---|
| 2 | `01` (word 2) | **3** on `d ≤ 40`; 2 is false for all `d` (`not_phaseTwo01_two`) | `10`: 5 (`not_phaseTwo10_four`) | 2 = 1 step + 1 test |
| 3 | `010` (word 2) | **5** on `d ≤ 32`; 4 is false for all `d` | `100`: 8 (`not_phaseThree100_seven`) | 3 = 2 steps + 1 test |
| 3 | `101` (word 5) | **2** on `d ≤ 32`; 1 is false for all `d` | — | — |

Through the exact cost, the phase-`01` certificate gives the hub phase `10` with slack 5 on
`d ≤ 39` (`phaseTwo10_slack`).

### Measured (EMP, `scripts/wheel_phases37.py`; outputs in the study folder `rule30_round37/`)

The exact excess search, run on every phase of every wheel of period `≤ 8`:

| period | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| range of `d` | 34 | 34 | 34 | 34 | 30 | 30 | 28 | 28 |
| per-period slack (worst phase) | 2 | 5 | 8 | 7 | 6 | 11 | 12 | 14 |
| best-phase slack (worst wheel) | 2 | 3 | 5 | 4 | 3 | 5 | 5 | 6 |
| Round 36 route (hub slack + 2(p − 1)) | 2 | 7 | 12 | 12 | 12 | 18 | 20 | 25 |
| Round 37 route (best phase + exact cost) | 2 | 5 | 8 | 9 | 10 | 13 | 14 | 17 |

* The proved cost has no violation on 2876 ordered phase pairs. In 66 of the 69 wheels with more
  than one phase, some pair of phases attains it exactly.
* From the best phase alone, the exact cost predicts 84 of the 401 other phases exactly. For
  periods 1–3 it predicts the per-period slack exactly. From period 4 on it overestimates by 2–4.
* **Answer to "is a per-wheel law more natural than a per-period one?"**
  - The per-period slack grows with the period: 14 at period 8.
  - The best-phase slack stays small: at most 6 up to period 8.
  - The hub (the Lyndon representative) is often the *worst* phase: 7 of the 18 wheels of period 7.
  - So the natural unit is **a wheel read from its best phase, plus the exact turn cost**. That is
    what the GLM now proposes (§3).

## 2. An infinite family of hubs (To Do 39) — FORMAL, partly

* `wheelRep_oneRun`: every word `1^(q−1)0` (`oneRunWord q = 2^(q−1) − 1`), `q ≥ 2`, is a hub.
* `failsWithinTests_of_initial_blackRun`: this holds for **every** drive whose first `r` times are
  black. Every code of length `d ≤ r − 3` fails within `d + 2` tests, because before failing the
  machine cannot tell the drive from the constant one.
* **`oneRun_band`**: for every `q` and every `1 ≤ d ≤ q − 4`, every code fails within `d + 2`
  tests of `1^(q−1)0`.
  - This is the first result that covers infinitely many hubs at once, with a band of code
    lengths that grows with the period.
  - No finite certificate gives it.
* **The exact remaining requirement** (`oneRunDies_iff_long`): the hub kills every half-line iff it
  kills every code of length `d ≥ q − 3`.
* `halfLineDies_two_of_oneRunFamily`: the whole family (`OneRunFamilyDies`) contains `HalfLineDies 2`
  (the case `q = 2`, word `10`). So a proof for the whole family is at least as hard as the open
  period-2 rung. The honest family target is `OneRunFamilyDiesFrom q₀`.
* Measured (EMP, `scripts/one_run_family37.py`): slack at most 7 for `q = 2..20` on `d ≤ 30`. The
  band bound (excess `≤ 2`) holds on the range. Every excess above 2 lies outside the band.

## 3. The GLM indexed by hubs (To Do 41) — measured

Install: `STUDY=/path/to/study sh $STUDY/rule30_round37/setup_round37.sh` from the directory
holding `GLM.py`. It reruns every earlier setup and ends with `round 37: all checks pass`.

| ability | what it does |
|---|---|
| `tool hub P K` | the hub `(q, j)` and phase of any word, exactly as `exists_wheelRep`; what one proof there fills (its wheel and every multiple period); its certified slack (`d ≤ 24`), the measured slack of each phase, and the exact turn cost from the best phase |
| `tool hubs P` | the hubs of a period, against the number of words |
| `tool next` | proposes **hubs first**: smallest open period, then cheapest best phase. Each pick gives the Lean target, the proved implication it feeds and the script. Then come the To Do items. |
| `tool requirements` | the exact improvement requirements (§4) |
| theorem wheel | the **hub rule**: `HubsOfDivisors<p> ⇔ HalfLineDies<p>` (`halfLineDies_iff_wheel`), `WheelDies ⇒ HubsOfDivisors<p>`, and the Round 37 spokes (`testCountLinear_two_of_phase`, `testCountLinear_three_of_phases`, `halfLineDies_two_of_oneRunFamily`, `oneRunFamilyDiesFrom_of_wheelDies`) |

**Measured results:**

* **Consultation:** 0/11 before the overlay, 11/11 after. The 11 questions and their expected
  strings were frozen before the overlay was written. They are development questions, not held
  out.
* **Hub index:** 8178/8178 non-white words of period `≤ 12` map to a hub, with the drive identity
  checked.
* **Work:** to cover every word of periods 1..8, 70 hubs replace 502 words. For periods 1..12, 746
  hubs replace 8178 words. The exact search over periods 1–7 on `d ≤ 20` took 5.19 s for all 247
  words and 0.64 s for the 40 hubs (wall clock).
* **Bounds:** on the measured range, the best-phase route gives the true per-period slack for
  periods 1–3. It is never worse than the Round 36 route, and closer for every period `≥ 2`
  (table in §1).
* **No regression:** the self-tests of Rounds 11–34 pass in the fresh install.

## 4. Exact improvement requirements

| # | needed | already in hand | gap |
|---|---|---|---|
| R1 | `WheelDies` (every hub kills), for all `d` | `⇔` every `HalfLineDies p`, `⇒` P1; period 1 proved; every hub of period `≤ 8` on `d ≤ 24` | no finite range decides it; a proof uniform in `d` is needed for every hub of period `≥ 2` |
| R2 | narrowest: `TestSlack (driveN 2 2) 3` for all `d` | `⇒ TestCountLinear 2 5 ⇒ HalfLineDies 2`; CERT `d ≤ 40`; slack 2 false | a per-test mechanism at the phase `01` (each test is one window read; To Do 42) |
| R2′ | period 3: `TestSlack (driveN 3 2) 5` and `TestSlack (driveN 3 5) 2` | `⇒ TestCountLinear 3 8`; CERT `d ≤ 32` | as R2 |
| R3 | `OneRunFamilyDiesFrom q₀` | hubs for all `q`; band `d ≤ q − 4` uniform; only `d ≥ q − 3` remains | a uniform slack for `q − 3 ≤ d ≤ 2q` would be the next uniform step (To Do 43); `q₀ = 2` contains period 2 |
| R4 | the GLM proposing spokes | it reads and chains proved spokes, indexes by hubs, and states requirements | it proposes none (To Do 44); its consultation sets are not held out |

## 5. What this round does not do

* Nothing here holds for all `d` except the FORMAL statements. The best-phase targets in R2 are
  open.
* The per-period slack laws for periods `≥ 4` are not recovered exactly by the best phase. The
  exact cost overestimates there by 2–4.
* The family result covers a growing band of code lengths, not all of them.
