# Rule 30 / GLM — Project Directive (Round 37)

## Tier 0 — the coarse read

**Question.** What is the project's goal, what are its rules of evidence, and what counts as progress?

**Verdict.** Answer Wolfram's three Rule 30 questions as clearly and fully as possible, with the GLM as the instrument and Lean 4 to check every claim; every claim has an evidence class, open targets are Lean Props, never an axiom, and no finite range decides P1 or P2.

**Deciding figure.** 3 questions; 5 evidence classes FORMAL, CERT/EXH, EMP, DEF, OPEN.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `tools/tier0_check.py` (or the GLM's corpus check, after a merge) fails if they stop being.*

This is the one-page brief for anyone continuing the project. It replaces the study's original
`VERIFICATION_DIRECTIVE.md` as the working directive. That file is still in the study folder;
§7 below records what became of each of its targets. The status details are in `AUDIT.md`, and
the full record is in `HISTORY.md`.

---

## 1. Purpose

Answer Wolfram's three Rule 30 questions as clearly and fully as possible. Use the Geometric
Language Machine (GLM) as the instrument and frame, and use Lean 4 to check every claim. The
results go back into GLM development: its general reasoning (stating, deriving and refusing
claims) and its puzzle solving (ARC). So each round has two outputs: **mathematics** (the Lean
package) and **GLM capability** (overlays in the study folder, with measured effects).

## 2. The three questions, exactly as stated in Lean

| | Question | Lean `Prop` (never an `axiom`) | Status |
|---|---|---|---|
| P1 | Is the centre column never eventually periodic? | `Problem1` (`Prizes.lean`) | open; period 1 proved |
| P2 | Does the frequency of black cells tend to 1/2? | `Problem2` (`Prizes.lean`) | open |
| P3 | Does computing `a(n)` need time that grows with `n`? | `Problem3`, `Problem3Eventual` (`MachineModel.lean`, `Problem3Quantifiers.lean`) | open |

## 3. Rules of evidence (non-negotiable)

1. **Every claim has a class**: `FORMAL`, `CERT`/`EXH`, `EMP`, `DEF`, `OPEN` (`claims.csv`), and it is
   reported at that class only. An `EMP` finding is never called proved.
2. **The open status lives in the `Prop`.** Targets are `def Target : Prop`. A round proves
   `Target → known rung`, certifies `Target` on a range, or refutes it. Never add an `axiom`.
3. **No finite range decides P1 or P2** (`no_finite_certificate_problem1/2`). A `CERT` is about its
   stated range only.
4. **Seed, not map** (error E2). Facts true of the `n`-step map for every row are shared by the
   all-white row, whose centre column is periodic, so they cannot by themselves give P1. A proof
   must use the seed or a class of rows such as the left-white rows.
5. **A blocked implication blocks only that implication.** Later bridges from the same facts stay
   allowed (`AUDIT.md` §5.4).
6. **Credit honestly.** Candidates the developers supply are tagged and do not count as
   GLM-generated (`scripts/candidate_benchmark.py`). GLM benchmarks report right, wrong and refused,
   and they keep development sets separate from held-out sets.
7. **Exact arithmetic only** (owner's rule, Round 31). Every computed value — in Lean and in the
   scripts — uses integers, exact rationals or bit vectors. No floating point inside a
   computation (it drifts), no random operators and no hashing (they disrupt the fidelity of the
   run). Hashes may fingerprint files for bookkeeping only; floats may only measure wall-clock time.

## 4. Current focus (in order)

| # | Focus | Precise target | Where it stands |
|---|---|---|---|
| F1 | P1, period 2, one-sided | `HalfLineDies 2`. The narrowest sufficient form is `AmortizedHalving 2 4 1` (`Round27Open`) | certified for `d ≤ 12`; the linear form is certified for `d ≤ 36`; 4 proof routes are stated, with each route's key lemma open; Round 31: exact sideways form `halfLineDies_iff_sideways` (To Do 29), finite-window quotients ruled out; Round 33: on the observer's clock, `TestCountLinear 2 5` / `TestHalving 2 6` each give the rung (certified on `d ≤ 22` / `d ≤ 18`; slack 4 and excess 5 refuted); Round 37: from the observer's best phase, `TestSlack (driveN 2 2) 3` (phase `01`) gives the optimal `TestCountLinear 2 5` (`testCountLinear_two_of_phase`); it is certified on `d ≤ 40`, and slack 2 is false (To Do 42) |
| F2 | P1, all periods | `HalfLineDies p` for every `p` (`problem1_of_halfLineDies`) | `p = 1` proved (twice: forwards and sideways); `p = 2…6` certified on ranges; exact `Lmax` for five more words to `d = 20`; Round 33: no uniform test-count slack (`not_testCountBound`); per period it suffices (`problem1_of_testCountLinear`); period 4 needs slack ≥ 7 (To Do 35); Round 34: least period-4 slack on `d ≤ 30` is exactly 7 (`frontier_round34`), per-period laws pass to divisors and refutations to multiples (`testCountLinear_of_dvd`, `halfLineDies_of_dvd`), the observer's phase moves the slack by ≤ 2 per step (`testSlack_of_shift`); Round 35: least slacks 5, 8, 7 (periods 2, 3, 4) on `d ≤ 42, 32, 32` with a verified checker twice as fast (`frontier_round35`, `DiagonalSearch`), run bounds for periodic columns in every left-white row, and a black run of the drive is one window read with an explicit word (`blackRun_word`, `dDiesBy_of_long_blackRun`); Round 36: the **drive wheel** (`WHEEL.md`) — only hubs (primitive least turns, Lyndon words) need treating, `HalfLineDies p` ⟺ hubs of the divisors of `p` kill (`halfLineDies_iff_wheel`), `WheelDies` ⟺ every `HalfLineDies p`; one certificate for all 70 hubs of period `≤ 8` (`frontier_round36`); Round 37 (`TURN_COST.md`): the exact cost of a turn, `m` + (tests skipped) (`testSlack_phase_transfer`; some phase pair attains it in 66 of 69 wheels); one phase per wheel suffices (`testCountLinear_of_phases`); best-phase slacks `≤ 6` up to period 8 (EMP); the hub family `1^(q−1)0` is settled on `d ≤ q − 4` uniformly (`oneRun_band`) and contains period 2 (To Do 39, 43) |
| F3 | P2 | `SeedAPBalanced` (every arithmetic progression has frequency 1/2); even one stride is open | `CERT` tables to `10⁶`; `EMP` to `10⁷` |
| F4 | P3 | keep the statement exact; the light-cone circuit bound is a different function | stated only |
| F5 | GLM track | the theorem wheel reads the ledger (`glm/`); puzzles are solved by a **stepwise planner** with a sound refusal (`PlanSearch`, `LocalRuleInduction`); each round reruns `rule30_round28/r28_benchmark.py` and the Round 30 pipeline (`rule30_round30/pipeline.py`: plan, ask, gate, statements; `Pipeline`, `PipelineData`) | planner operational since Round 29; pipeline since Round 30 (fresh held-out 96/132 right, 4 wrong; 106 with ≤ 5 questions); Round 33: `tool next` ranks the To Do list, `tool clock` reads the machine on the observer's clock, the wheel has an instantiation rule (`rule30_round33/`); Round 34: `tool slack` (exact excess search), the divisor rule in the wheel, consultation 1/7 → 7/7 (`rule30_round34/`); Round 37: indexed by **hubs** — `tool hub`, `tool hubs`, `tool requirements`, hub-first `tool next`, the hub rule in the wheel; consultation 0/11 → 11/11; hub index exact on 8178 words (`rule30_round37/`); Round 38: the **hypothesis engine** generates, tests and refutes conjectures on held-out data and hands survivors to Lean (`rule30_round38/`, `HYPOTHESIS_ENGINE.md`) |

## 5. What counts as progress

* a proved implication between targets (a new spoke), or a proved non-implication (a negative
  control);
* a target proved, refuted, or certified on a range that **separates competing candidates**;
* a new equivalent form of a problem that is exact (`↔`), with both directions proved;
* for the GLM: a capability that is measured on a held-out set, with no new wrong answers and no
  regression on the earlier suites.

**Not progress:** extending a certificate range for its own sake; restating a target in new words;
an analogy without a proof; facts about the `n`-step map offered as facts about the seed; a
benchmark tuned on its own test set.

## 6. The observer `Y`, the wobble and "perspective" (your idea, where it stands)

* **The arrow** `−sign D(N)` is exactly the local direction towards frequency 1/2
  (`deviation_decreases_iff`). It carries **no** information about the limit
  (`arrow_independent_of_frequency`). Use it to steer a run, never as a success criterion.
* **The compass.** Rule 30's chirality fixes the read angle off the axis, but the centre column
  cannot tell 30 from its mirror 86 (`centre_column_class`).
* **The refutation side.** A periodicity proposal for a column can be refuted only by facing left
  (`col_black_forces_left`). This choice of side is what drives the whole half-line programme.
* **The read direction in puzzles (Round 28).** Readers that look along a direction ("the first
  colour seen to the north") are part of the ARC reader ladder. The Rule 30 row neighbourhood
  `(west, centre, east)` as a reader solves one stored ARC task that the earlier readers refused.
* **Plans, not single steps (Round 29).** A puzzle is answered by a chain of steps, chosen by the
  GLM's own planning rule (every step licensed; answer only when every cheapest consistent chain
  agrees). The direction of a run is the plan's direction: the last step can be read backwards
  from the goal (`run_concat_eq_some`), and when chains disagree the GLM names the one observation
  that would decide between them (`separating_example_refutes`).
* **One pipeline (Round 30).** Plan → ask → gate → statements run as one loop with one hard gate
  and one refusal rule. The GLM asks for the deciding observation instead of refusing
  (`askLoop_correct`), applies the Occam gate when demonstrations are few (`gate_can_fix`,
  `gate_can_drop_truth`), and runs the same planner over Rule 30 statements, which Lean certifies
  (`frontier_round30`).
* **The best phase (Round 37).** Each periodic column can be read from any of its phases, and
  the price of changing the read phase is exact: `m` + (tests skipped) (`testSlack_phase_transfer`).
  So the observer chooses the phase from which the column is cheapest to refute
  (`testCountLinear_of_phases`). For period 2 that is the phase `01`, which needs slack 3 where the
  phase `10` needs 5. This is your perspective idea as an exact rule: the read position changes
  the measured cost by a known amount, and there is a best read position for each wheel.
* **The law tells the engine where to look (Round 38).** Left-diagonal periods change only just
  after a white diagonal (`ldiag_doubles`, `first_difference_after_white`). So the direction of
  convergence is set by the white diagonals: the engine reads there, and nowhere else, to find the
  next change (it predicted `D = 87867`, confirmed in Lean).
* **Symmetry of seeds (Round 32).** `M₂₄` (the automorphisms of the GLM's Golay code) enumerates
  the symmetry types of seed patterns exactly (`MathieuOrbitsData`, `M24_ORBITS.md`). For the
  dynamics only the rotations of the ring count (`commutes_iff_rot`). At most 12 of them can lie in
  `M₂₄` under any labelling (`shared_card_le_twelve`), and in the GLM's labelling only the half-turn
  does. So the read position `j` and the opposite position `j + 12` are equivalent both for the
  code and for the dynamics, and no other pair is. Use `M₂₄` orbits to enumerate candidates, never
  as evidence that two seeds behave alike (`octad_cycles`).

## 7. What became of the original `VERIFICATION_DIRECTIVE.md` targets

| Original target | Outcome | Lean |
|---|---|---|
| T1 cone separation preserved | **proved** for every `n`, row and cell | `ConeSeparation.lean` |
| T2 wobble bound ⇒ normality | the implication is **proved**; the exact equivalent is `D(n) = o(n)`. The bound itself is **open**, and `C = 2` is **refuted** | `Wobble.lean`, `WobbleCertificate.lean` |
| T3 right-cone weight `+2` per step | **proved** (unique top monomial, weight `2n − 2`) | `WeightGrowth.lean`, `TopMonomial.lean` |
| "T3 unlocks P1 and P3" | **not valid**: it is a property of the map (error E2) | `map_properties_cannot_decide_periodicity` |
| the problems stated as axioms | replaced by `Prop`s; two of the original axioms were inconsistent | `Prizes.lean` |

## 8. Where everything lives

| Place | Contents |
|---|---|
| `RequestProject/GLM/Rule30/` (this package) | Lean files, `claims.csv`, `scripts/`, `glm/`, the documents listed in `README.md` |
| study folder `rule30_round10/` … `rule30_round16/` | GLM overlays and probes of Rounds 10–16 (Rounds 17–27 were Lean-only) |
| study folder `rule30_round28/` | Round 28 GLM side: `setup_round28.sh`, the local-rule solver, the Round 28 theorem wheel, benchmarks and outputs |
| study folder `rule30_round29/` | Round 29 GLM side: `setup_round29.sh`, the stepwise grid planner, benchmarks by plan depth and outputs |
| study folder `rule30_round33/`, `rule30_round34/` | Rounds 33–34 GLM side: `tool clock`, `tool next`, `tool slack`, the divisor rule |
| study folder `rule30_round37/` | Round 37 GLM side: `setup_round37.sh`, the hub index (`tool hub`, `tool hubs`), hub-first `tool next`, `tool requirements`, the per-phase and family measurements, `hub_benchmark37.py`, the consultation before and after |
| study folder `rule30_round30/` | Round 30 GLM side: `setup_round30.sh`, the pipeline (`glm_pipeline.py`, `statement_planner.py`), `pipeline.py` (one command), the fresh held-out set, benchmarks and outputs |
| study folder root | the user's original study (Rounds 1–7: `README.md`, `VERIFICATION_DIRECTIVE.md`, `pdfs/`, `scripts/`, `lean/`) and `glm_repo.zip` |

## 9. Checklist for closing a round

Build the touched modules and then the root. Search for `sorry`. Check `#print axioms` for the
headline theorems. Run `scripts/ledger_check.py` (it must report `missing: 0`). Add rows to
`claims.csv`, a section to `HISTORY.md`, and status marks to the `AUDIT.md` §4 To Do list. Rerun
`ledger_check.py --wheel glm/r28_wheel.json` and the GLM benchmark. The details are in
`DEVELOPMENT.md`.
