# Run 159 — the landscape: what is proved, what is open, and where 22.217 actually sits

Two questions were asked: close the last factor of two at `n = 118`, and then say whether we are aiming at
the right rows. The first has a hard answer — `n = 118` at `11 - 1e-4` is **impossible**, not hard — and the
second has a measured one: the ten-row list of runs 154–158 was aimed entirely at rows whose side is
**proved** to be `k`, while the leader's advantage over us is not in those rows at all.

Nothing was promoted and `submission.csv` is untouched; the score stands at **22.217428576** (554 beats,
446 ties). But three stale facts were found and fixed, and the targeting instrument that stops this from
happening again is now in the repo.

## 1. The brief, and the four measurements that answer it

### 1.1 `n = 118` at `11 - 1e-4` cannot exist

`s(k^2 - 3) = k` **for every integer `k >= 6`** is proved (Daniel 2026, `evand/square-packing`, Lean
development reduced to one finite covering statement `Valid7`, rebuilt by the Squares Project on 2–3 October
2026 with two exact checkers). The catalogue records `n = 118` with `status: proved`, verified upper bound
**11**, verified lower bound **11**. So `s(118) = 11` exactly, and no pose with 118 unit squares in a square
of side `10.9999` exists — at any budget, by any method.

The same family sentence settles **`n = 141, 166, 193, 222`** (the `k = 12, 13, 14, 15` cases of `k^2 - 3`).

### 1.2 `n = 117` at `11 - 1e-4` is reported proved too

`s(k^2 - 4) = k` for every `k >= 5` is Daniel's companion result (3 October 2026), Lean-conditional on
`ValidTilt9`, which Hosono reported independently with a separately written exact checker. The catalogue
keeps `n = 117` at `status: open` only because that premise has not been replayed *by the catalogue*; its
verified lower bound is Karakuş's general `10.856157...`. So `117, 140, 165, 192, 221` are **reported
optimal at `k`**, i.e. the whole ten-row list of runs 154–158 was a list of rows that cannot be promoted.

### 1.3 An *open* row at the target side is still 2× out of reach

`n = 111` (`k = 11`, `r = 10`, a genuinely open tie — catalogue best known is the grid) at `L = 10.9999`:

```
  n=111 k=11 r=10 tier=A: pen=2.151e-05 at L=10.999900 (6.2s) qualifies=False
```

`2.151e-05` against the `1e-5` pass line, and the same `2.07e-05` shape as `n = 118` in run 158. The reason
is structural, not budgetary: `k - 1e-4` on an open tie means **beating the best packing known to anyone**
by `1e-4`, and a 97.5 %-dense pose has no slack to give. The solver's best attempt lands at a pose which
still overlaps by a fifth of the target margin.

### 1.4 Two real defects in `--run`, found by using it

* `--run --budget 6` took **80.1 s** on one row: `--budget` was checked only *between* passes, and each
  pass gave every seed its own 15 s default cap. `solve_best` now divides the remaining budget across the
  seeds still untried, and `struct_ladder` scales its (uncapped) quench to the time left. The same row now
  costs **6.2 s**.
* The seed order is wired as measured in run 158: **`defect` first**, then `strip`, `lattice`, `random`
  (`defect` reaches `2.069e-05` at n = 118 where `strip` is `9.11e-2` and `seed_bridge` `1.35e-1`).

So: no re-cut of the `n = 39` calibration case, and **no ten-row run** — it could not have produced a
candidate. The gate itself is unchanged by this run: `n = 5` PASS `-7.2e-05`, `n = 10` PASS `-4.6e-05`,
`n = 39` FAIL `+2.556e-02`.

## 2. The score, decomposed exactly

`sqscore`'s metric is `sum over n of (L_n / sqrt(n) - 1)`, recomputed here to `22.217428576459` (matching
the recorded `22.217428576`). Every point of it is a *side excess over the zero-waste side*, so a row's
worth is `delta_L / sqrt(n)`.

| class | rows | score |
| --- | ---: | ---: |
| beaten (side below `k`) | 554 | **15.076155** |
| tied at `k` | 446 | **7.141273** |
| — of which **locked by proof** (`r <= 4`, or a catalogue case marked proved) | 152 | 2.5008 |
| — of which **open ties** (a beat would be a new result) | 293 | 4.6029 |

`target_audit.py` prints this decomposition for any table, and writes `workspace/push/target_audit.json`.

## 3. The catalogue audit: we are behind on 30 rows, and nobody had noticed

`workspace/catalogue/frontier.json` is a dated snapshot of all 324 Squares Project case records (verified
upper bound, verified lower bound, status). Against it:

| position | rows |
| --- | ---: |
| ahead of the catalogue's verified upper bound | 21 |
| tied with it | 273 |
| **behind it** | **30** |

The campaign's card says "303 tied / 21 ahead / 0 behind". It was true when it was written; the catalogue has
moved since. The 30 rows are score we can take **today, with no search**, because the catalogue's pose is
already certified:

| n | ours | catalogue | gain |
| ---: | ---: | ---: | ---: |
| 127 | 11.810878789 | 11.800793727 | +0.00089 |
| 132 | 11.985680201 | 11.976048384 | +0.00084 |
| 269 | 16.901513584 | 16.889730074 | +0.00072 |
| 237 | 15.902603640 | 15.893805581 | +0.00057 |
| 228 | 15.604601478 | 15.596043117 | +0.00057 |
| 262 | 16.707106783 | 16.698115019 | +0.00056 |
| 263 | 16.733166010 | 16.724372709 | +0.00054 |
| 157 | 13.000000002 | 12.993302611 | +0.00053 |
| 147 | 12.656854251 | 12.651043553 | +0.00048 |
| 299 | 17.801004436 | 17.793636992 | +0.00043 |
| ... 20 more | | | |

**Total import gain: +0.008891.** Our `n = 127` side `11.810878789` is *exactly* the catalogue's previous
ceiling ("house 11.81087878758917984 ... ceiling from 17 October 2026 until 16 November 2026"), so these are
rows where the world improved after our last intake — a stale snapshot, not a failed method.

## 4. The frontier, measured by `r = k^2 - n`

For every row, `r` is how far below the next perfect square the count sits. Beaten / total rows:

```
r=0:0/31  r=1:0/30  r=2:0/30  r=3:0/29  r=4:1/29  r=5:1/28  r=6:2/28  r=7:2/27  r=8:3/27
r=9:3/26  r=10:5/26 r=11:5/25 r=12:6/25 r=13:7/24 r=14:8/24 r=15:8/23 r=16:10/23 r=17:10/22
r=18:12/22 r=19:12/21 r=20:14/21 r=21:15/20 r=22:16/20 r=23:17/19 r=24:18/20 r=25:18/19
r=26:19/19 r=27:18/18 r=28:18/18 ... r=62:1/1
```

Three clean readings:

1. **`r <= 4` is dead** — `0/120` beaten at `r <= 3`, and the single `r = 4` "beat" is the `1e-9` rendering
   pad on `n = 12`, not a packing. This is the proof in §1.1–§1.2 showing up as data.
2. **`r >= 27` is finished** — every row is already beaten.
3. **The frontier is `r = 5..26`**, and the beat rate climbs monotonically from `1/28` to `19/19`. That band
   is where every open tie lives, and it is exactly where the world is stuck.

## 5. Why no known family reaches the tie band

The October 2026 preprint *Packing Unit Squares in a Square of Side Just Below an Integer* proves, with an
L-shaped packing (a grid with two tilted bands along adjacent walls), that for every `K >= 16` the wasted
area is at most `8 sqrt(K) + 19` at **every** side in `[K - 1/K, K)`. That construction holds
`n >= K^2 - 8 sqrt(K) - 21` cells, i.e. it beats the grid only for `r >= 8 sqrt(K) + 21` — at `K = 32` that
is `r >= 66`, far outside the band where our ties sit (`r <= 25`). The scalable families, the carrier, the
composite family and the L-shaped bands all live at **large `r`**, which is precisely the region this table
has already beaten (see §4, `r >= 27` = 100 %).

So the 293 open ties are not "rows we have not tried": they are rows where **no construction in the
literature reaches**, and a beat there is a genuine world record. That is why every previous attempt produced
`2e-5`-scale negatives: the solver is being asked for records, not for improvements.

## 6. Where the leader's 0.163635 is

`0.163635` of score is, in this metric, `sum(delta_L / sqrt(n)) = 0.1636`. Equivalent descriptions:

* a **1 % side reduction across the 554 beaten rows** (`0.15076` by the card's own arithmetic), i.e. **1.1 %
  of the 15.076 headroom** those rows carry;
* or `0.01` of side on ~160 rows of moderate `n`;
* or `0.1636 / 0.0009 ≈ 180` catalogue-scale imports (there are only 30 available).

None of it requires a world record. All of it requires **lower sides on rows that are already beaten**,
which is a *polish* problem — and it is the one capability this campaign has not built: the float solver
cannot reduce a side at all right now (its best is `2e-5` of *overlap* at a target side), because it was
built to find structures, not to shrink poses.

## 7. The way forward, ranked by expected gain

1. **Import the 30 stale rows (+0.008891, certain).** The path exists and is precedented (run 140 imported a
   published certificate for `n = 90`): fetch the catalogue's witness pose, replay it through
   `snap_certify`/`verify_certificates` exactly, promote with C1–C4, update `sqscore`'s recorded constants
   and the ledgers. No search, no research, no risk.
2. **Never let the snapshot go stale again.** `scripts/target_audit.py` + `workspace/catalogue/frontier.json`
   do the diff in one command; make it the first thing every run prints. The card's "0 behind" was true when
   written and false for eleven days.
3. **Stop targeting `r <= 4`.** Fixed in code: `PROVED_R` is now `(0, 1, 2, 3, 4)` and the `r <= 12` cap is
   gone, so `--rank` returns the open frontier band (`r = 6..12` at `k = 11..15`; n = 111, 133, 112, 157, 134,
   113, 158, 135, 184, 159, ...) instead of the proved rows.
4. **Build the polish capability, and test it on the biggest-headroom beaten rows.** This is the only pool
   with enough score to matter (15.076). The decisive experiment is one row: take a beaten pose, ask for
   `L - 0.5 %`, and measure whether anything survives exact snapping. If it does, the same loop applied to
   the top 100 rows by `1/sqrt(n)` is worth more than every tie-chasing run so far.
5. **Open ties: only as record attempts, and only at small `k`.** The score at stake is real (`n = 20` alone
   is `0.118` if it could reach `sqrt 20`; `n = 30` `0.095`; `n = 42` `0.080`), but each one is a new world
   result and the machinery for it is not the annealer — it is a *constructive* two-domain pose with exact
   angles, certified exactly, which is what this project is actually good at.

## 8. Methods and tests: what holds, what was stale

**Holds.** The exact side computation (`true_geom`, `Decimal`) reproduces the recorded score to 12 digits;
the guards are independent and loud (`sqscore` 22.217428576 / 554 / 446, `record_guard`, `glm_wheels
--audit` 708 functions / 0 offenders, `snap_certify` 8/8 with 24 float-free decision functions); the
certificate pipeline and the C1–C4 rule are unchanged and were not bypassed.

**Was stale.** Three separate facts, all fixed here: (a) the *proved list* used by the target filter stopped
at Nagamochi (`r = 1, 2`) and never picked up Daniel's `r = 3, 4`; (b) the *catalogue snapshot* was eleven
days old, hiding 30 rows; (c) the *budget* in `--run` was not honoured (80.1 s for a 6 s request). Each was a
bookkeeping failure with a measurable cost, and each now has an instrument or a test: `target_audit.py`,
`workspace/catalogue/frontier.json` with its retrieval date, and the `solve_best` budget split.

**Added.** `scripts/target_audit.py` (classifies all 1000 rows into import / beaten / open tie / locked, with
the score at stake and the frontier table, and writes `workspace/push/target_audit.json`);
`workspace/catalogue/frontier.json` (324 case records, retrieved 2026-11-27).

## 9. Guards

`sqscore.py` **22.217428576** (554 beats, 446 grid); `record_guard.py` clean; `glm_wheels.py --audit`
**708 functions, 0 offenders**; `snap_certify.py --selftest` **8/8** (24 decision functions, 0 float);
`proposal_anneal.py --selftest` gate unchanged: gradient `2.46e-09` PASS, seat control PASS, `n = 5` PASS
`-7.215e-05`, `n = 10` PASS `-4.632e-05`, `n = 39` FAIL `+2.556e-02`. `submission.csv` and root
`WHITEBOARD.md` untouched.
