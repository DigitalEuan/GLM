# The drive wheel (Round 36)

## Tier 0 — the coarse read

**Question.** Do the periodic drives of the half-line machine form one wheel, and can the wheel skip the slow iterations?

**Verdict.** Partly yes, and it is proved: the periodic drives form a wheel for every period at once and the wheel removes the repetition exactly; no finite computation settles the problem along the code length d.

**Deciding figure.** (an equivalence for every period p, no figure to count: HalfLineDies p holds exactly when the hubs of the divisors of p kill every non-empty half-line)

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `tools/tier0_check.py` (or the GLM's corpus check, after a merge) fails if they stop being.*

**Your question:** *many of these experiments look like parts of one wheel — could we have the
full wheel of this family of operations and skip the slow iterations?*

**Short answer:** partly yes, and it is now proved. The periodic drives of the half-line machine
form a wheel. Most of the per-period and per-word work of Rounds 21–35 was the same wheel looked
at from different phases. The wheel removes that repetition exactly, and it is proved for every
period at once (`DriveWheel.lean`, standard axioms only). What the wheel **cannot** remove is the
other direction, the code length `d`. No finite computation settles the problem along `d`
(`no_finite_certificate_problem1`), so a uniform proof is still needed there.

---

## 1. What the wheel is

A periodic column of period `p` gives a drive word `k` of `p` bits (time `0` is bit `0`). The
family of operations that kept coming back in the earlier rounds is:

| operation | what it does to the drive | earlier rounds where it appeared separately |
|---|---|---|
| **turn** by `s` (`wheelTurn p k s`) | read the same column from phase `s`: the old drive started `s` steps later (`driveN_wheelTurn`) | Round 26 `halfLineDies_two_iff`, `halfLineDies_three_iff` (one case each); Round 34 the observer's phase (`testSlack_of_shift`) |
| **inner wheel** (period `g ∣ p`) | a word that repeats after `g` steps *is* a word of period `g` (`driveN_eq_of_period`); periods combine by `gcd` (`period_gcd`) | Round 34 divisor rule (`halfLineDies_of_dvd`, `testCountLinear_of_dvd`) |
| **composition** | turns compose (`wheelTurn_add`) and `p` turns are the identity (`wheelTurn_mod`) | — |

These operations form the full wheel. Each orbit (a necklace) has one **hub**: the least of its
turns, taken only for *primitive* words (no smaller period). This is `WheelRep p k`. In word
language these are the Lyndon words, read as binary numbers.

## 2. What is proved (FORMAL, every period)

* `wordDies_wheelTurn_iff`: a word kills every non-empty half-line iff each of its turns does.
* `exists_wheelRep`: every non-white word of period `p` is a turn of a hub of some period
  `q ∣ p`.
* **`halfLineDies_iff_wheel`**: `HalfLineDies p` ⟺ the hubs of the divisors of `p` kill every
  non-empty half-line.
* **`WheelDies`** ("every hub kills every non-empty half-line") is equivalent to `HalfLineDies p`
  for every `p` (`wheelDies_iff`). It implies Problem 1 (`problem1_of_wheelDies`). It is the same
  as "every periodic drive with a black cell kills every non-empty half-line"
  (`wheelDies_iff_periodic`), a form that mentions no words, periods or phases.
* On the observer's clock, a turn costs at most `2` slack per step (`testSlack_wheelTurn`). So a
  slack `c` for the hubs gives the per-period law `TestCountLinear p (c + 2(p − 1))`
  (`testCountLinear_of_wheel`). The same holds on a finite range, where the hubs need code lengths
  up to `D + p − 1` (`testSlackUpTo_of_wheel`).

## 3. How much it saves

Hubs per period (`wheelReps_count`, checked):

| period `p` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| non-white words `2^p − 1` | 1 | 3 | 7 | 15 | 31 | 63 | 127 | 255 | 511 | 1023 | 2047 | 4095 |
| hubs | 1 | 1 | 2 | 3 | 6 | 9 | 18 | 30 | 56 | 99 | 186 | 335 |

Up to period 8, **70 hubs replace 502 words**. Up to period 12 the counts are 746 against 8178.

## 4. The full wheel to period 8 in one certificate (CERT, `DriveWheelData.lean`)

One table `wheelTable` lists every hub of period `≤ 8` with a slack. One diagonal-search check
(`wheelTable_check`, about 6½ minutes to build) certifies that every code of length `d ≤ 24` fails
within `d + c` tests of that hub. A completeness check confirms the table has every hub. Through
the wheel this gives, for **every** period `1 ≤ p ≤ 8`:

* the per-period law on `d ≤ 25 − p` with slack `wheelSlack p + 2(p − 1)`
  (`testCountLinearUpTo_wheel`);
* run bounds in every left-white row of Rule 30: a non-white column of period 7 (resp. 8) at
  distance `d ≤ 18` (resp. `d ≤ 17`) from the left edge keeps its pattern for at most `7(d + 20)`
  (resp. `8(d + 25)`) steps (`runBound_wheel_seven`, `runBound_wheel_eight`). Periods 7 and 8
  had no run bound before. (For periods 5 and 6 this route is weaker than the Round 22 bounds.)

The hub slacks on `d ≤ 24` are mostly `2`–`5`. The largest are `11` (period 8, hub `91`, the
word `11011010`) and `9` (period 8, hub `11`, the word `11010000`). Next come four hubs with
`8`: period 3 hub `1`, period 7 hubs `13` and `27`, and period 8 hub `47`.

## 5. What the wheel does not do

* **It does not make anything uniform in `d`.** Every certificate is about its stated range. The
  open targets (`HalfLineDies 2`, `TestCountLinear p c`) are still open.
* **Turns are exact for dying, not for slack.** A turn can raise the slack by up to `2(p − 1)`.
  For example, period 4 needs slack 7 at `d = 30` in the phase `0111`
  (`not_testCountLinear_four_six`), while its hub `1110` stays within 5 on `d ≤ 24`. The exact
  least slacks per period (5, 8, 7 for periods 2, 3, 4) therefore still need per-phase checks. The
  wheel only bounds them.
* A finite-range transfer loses `p − 1` in the code length, because a turn of `m` steps lengthens
  every code by exactly `m` cells (`halfStep_length`).

## 6. For the GLM

* The half-line family should be indexed by **hubs**: a spoke is `(q, hub)`. Only these need a
  proof or a certificate. Periods are unions of the hubs of their divisors, and phases are turns.
* The ledger rows are C338–C342. The theorem wheel can read `halfLineDies_iff_wheel` as an
  instantiation rule: proving a hub fills in every word of its orbit and every multiple period.
* A uniform proof for an **infinite family of hubs** would be the first result that skips
  iteration along `d` as well. One example is the hubs `1^(p−1)0`, one black run per period, where
  `BlackRunWindow.lean` already reads each run as one window. This is To Do 39.

## 7. Round 37 follow-up (`TURN_COST.md`)

* To Do 40: the price of a turn is now exact, `m` + (tests skipped) (`testSlack_phase_transfer`).
  A slack at the **best phase** of each wheel suffices (`testCountLinear_of_phases`).
* To Do 39: the hubs `1^(q−1)0` are settled on the band `d ≤ q − 4` for every `q` (`oneRun_band`).
* To Do 41: the GLM is indexed by hubs (study folder `rule30_round37/`).
