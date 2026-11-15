# GLM Hypothesis Engine v18 — self-contained

One Python file, standard library only, exact integer and `Fraction` arithmetic only. It needs
nothing else to run. In particular it does not need any earlier engine (v4–v17), the guard modules,
or a Lean installation.

    python3 hypothesis_engine.py                 # everything, about 30 s  -> out/
    python3 hypothesis_engine.py --quick         # smaller ranges, about 15 s
    python3 hypothesis_engine.py rule30 --no-ledger      # ablation: no Lean provisions
    python3 hypothesis_engine.py general --claims example_claims.json
    python3 hypothesis_engine.py arc --arc-dir path/to/arc/tasks     # or --arc-zip ../glm_repo.zip
    python3 hypothesis_engine.py turn ../glm_wheel.json  # turn a previous wheel (owner or v18 format)
    python3 hypothesis_engine.py --selftest      # a few seconds
    python3 test_hypothesis_engine.py            # 16 tests, about 20 s

| File | What it is |
|---|---|
| `hypothesis_engine.py` | Engine v18. Sections: exact tools, layers and the arrow, hypotheses, the Lean ledger, the gate cascade and rollback, wheels, dialogue, domains (Rule 30, general reasoning, ARC), reports, CLI |
| `test_hypothesis_engine.py` | Tests |
| `example_claims.json` | How the GLM (or a person) submits its own claims to the general domain |
| `out/` | Results of the full run (see below). `glm_wheel_v18.json` is the wheel to pass to the next run |

The Lean side is `RequestProject/GLM/HypothesisEngine/Wheel.lean` (Round 46) in the Lean package,
together with the earlier contracts `GateLoop.lean` (gates, layers, rollback) and
`NeedsWheel.lean` (provisions). The engine checks no Lean itself. It cites Lean theorem names from
an embedded ledger, and every name it cites was checked to exist in the package (Round 46).

## What changed from v17

* **Self-contained.** v17 imported v14 (2,866 lines), v15, v16, `glm_guards`, `tax_guards`,
  `glm_layers` and `needs_rule30`. v18 imports none of them. The engine makes its own hypotheses.
  It no longer relabels v14's.
* **It proposes its own conjectures (the conjecture loop).** Each Rule 30 family (period divides `m`,
  white diagonals are exactly `S`, `|D(N)| ≤ c·√N`, `|2L(n) − n| ≤ b`, word coverage, …) is
  *lifted* from the development range, the first of five scales. It is then read at the other four
  scales. When a read refutes it, the loop does two things:
  * it states the narrowed finite claim that the data do support (a *derived* edge);
  * it re-lifts from the data up to the refuting read.

  For example `|2L(n) − n| ≤ 10` flips at n = 11101 (griess). The re-lift `≤ 11` flips at n = 19521
  (universal). The re-lift `≤ 13` survives to 20000. Lean (`Wheel.lift_lt_of_fail`): each flip
  strictly raises the lifted parameter.
* **The ledger reads structured parameters, not sentences.** Every hypothesis carries `params`, for
  example `{"m": 8}` or `{"p": 64, "tau": 30000}`, so a ledger entry applies only to the exact claim
  it certifies.
* **Recognisers** turn sentences the engine did not write back into executable families. This is
  how the owner's `glm_wheel.json` is re-gated. A sentence no recogniser matches is classified
  (analogy / proposal / meta / trend / estimate / implication / Pi1 / Pi2). It stays on the wheel
  as UNTESTED, with a stated need.
* **Wheels made executable.** See below.
* **Two more domains in the same gate loop:** general reasoning and ARC.

## The gate cascade (unchanged in spirit from v17, simplified)

class → recompute → exact (finite claims) → escalate (five reads, stop at the first failure) →
implication (checked edges only) → ledger (the only gate that can say *proved*) → typed rollback
(along *uses* edges only, to a fixpoint).

Lean: `GateLoop.cascade_sound`, `cascade_no_wrong`, `escalate_eq_some`,
`finite_range_never_proves_forall`, `retracted_least`, `rollback_sound`, `derived_edge_unsound`.

## The arrow (the owner's Wobble / Observer idea)

There are two exact readings of it in v18.

1. **The read arrow of every claim.** Each universal claim is read at the five layer scales in
   order, and the reads stop at the first counterexample. The trajectory therefore only moves up
   (`GateLoop.reads_sorted`). Its *direction* is either `converging` or `flipped at <layer>`. In the
   full run 8 lifts flip: H01, H04, H16, H19, H21, H22, H26 and H29. Each flip is a recomputable
   counterexample found only by reading higher.
2. **The observer's arrow on the centre column.** The arrow is `−sign D(n)`, where `D(n)` is the
   Wobble. The running frequency moves towards 1/2 exactly when the next bit follows this arrow
   (`Perspective.deviation_decreases_iff`, FORMAL). On 160,000 bits the arrow is followed at
   79955/159703 ≈ 0.50065 of the steps (exact count). The lifted claim "the run follows the arrow
   less than half the time" survived the development range. It flipped at N = 4672.

The layer names (substrate … universal) are **scale labels only**. They are not moduli (see the
corrected `GLM_Escalation_Boundaries_Exploration.md`).

## Wheels

| ring | what goes there | what it asserts |
|---|---|---|
| KNOWS | proved (Lean), verified-exact, measured, refuted | its truth value, with the evidence |
| THINKS-TRUE | survives every read (to a stated scale) | **nothing**: it is a need for a proof (`Wheel.thinksTrue_asserts_nothing`) |
| DOESN'T-KNOW | open, estimate, untested, unchecked implication, retracted | nothing |
| NEEDS | one machine-readable need per non-KNOWS entry: `proof:`, `test:`, `edge:`, `range:`, `restate:` | — |
| LANGUAGE | the KNOWS entries, true and false ("do not say this"), with backing | speaking from it is sound (`Wheel.speak_sound`) |

**A wheel turn** (`turn <file>`) imports every entry of a previous wheel and re-gates it. It then
reports, with the reason, which entries moved ring. Entries the previous wheel *knew* are kept even
if this run reads smaller ranges; Lean `Wheel.merge_sound` and `knows_merge` say this is safe and
that KNOWS only grows. A disagreement between the two wheels is reported as a conflict, because one
of the two is then unsound (`Wheel.conflict_unsound`). Turning a v18 wheel is a fixpoint (tested).

## Results of the full run (`out/`)

| domain | claims | right / wrong / overclaim / abstain | without the Lean ledger |
|---|---|---|---|
| Rule 30 | 39 | 39 / 0 / 0 / 0 | 24 / 0 / 0 / 15 |
| general reasoning (8 classic traps + Collatz) | 10 | 10 / 0 / 0 / 0 | 6 / 0 / 0 / 4 |

Caveats:
* The answer key is fixed in advance. Its sources overlap with the ledger (Lean theorems) and with
  exact computation, so the column *with* the ledger measures routing to checked sources, not
  discovery.
* The column *without* the ledger is the honest one: no wrong answer and no overclaim, and every
  universal claim that survived is reported as "survives to N", never as true.
* The gcd trap is the example: \(\gcd(n^{17}+9, (n+1)^{17}+9) = 1\) survives every read to 20000.
  Only the ledger refutes it. The engine then recomputes the cited 52-digit witness itself.

**Rule 30 rings:** 29 KNOWS, 6 THINKS-TRUE, 4 DOESN'T-KNOW. The DOESN'T-KNOW entries are the three
prize problems and "left-diagonal periods are unbounded".

**All three Rule 30 prize problems remain open.** The engine reports them as OPEN with their proved
reductions, for example `Prizes.problem2_of_sqrt_bound` and
`WobbleCertificate.no_finite_certificate_problem1`.

**ARC** (`out/arc.md`):

| set | base (symmetries + colour map) | on demand (wheel serves stated needs) | random provisions, same number |
|---|---|---|---|
| synthetic held-out, 60 puzzles, 10 families | 6 right | 55 right, 0 wrong | 13–18 right |
| real ARC, the 53 test grids shipped in `glm_repo.zip` | 0 right | **9 right, 0 wrong** (Round 44: 2) | 1–3 right |

* The synthetic families are built from steps that the library contains, so that row measures need
  routing, not discovery.
* The real tasks solved are `1e0a9b12` (gravity), `45737921` (swap colours in objects), `484b58aa`
  (periodic fill), `662c240a` (select the odd block), `7953d61e` and `bc4146bd` (tilings of
  symmetries), `ae58858e` (recolour by size), `b91ae062` (scale by number of colours) and `d631b094`
  (count to a row).
* The solver answers only when every consistent program of least depth agrees
  (`PlanSearch.agree_correct`).
* The most frequent unmet needs on real ARC are `primitive:fill` (19), `primitive:recolour` (13)
  and `primitive:unknown` (10). These are what to add next.

**Wheel turn of the owner's `glm_wheel.json`** (`out/wheel_turn.md`), 27 distinct entries:
* 8 moved THINKS-TRUE → KNOWS:
  * H16 proved;
  * H19, H32, H33, H36, H39 and H47 refuted;
  * H44 proved.
* 12 moved THINKS-TRUE → DOESN'T-KNOW: analogies, a trend, an estimate, an unchecked implication,
  and the R-calculus measurement that no tool here can recompute.
* 3 stay THINKS-TRUE (H02, H03, H17).
* Of the 7 stated needs:
  * 3 are met (NEEDED-3, 5, 6);
  * 1 is partly met (NEEDED-7);
  * 1 is answered negatively (NEEDED-1: `DialogueChecks.doubling_law_tie_unsplittable`);
  * 2 are unmet (R-calculus, the range past D = 87867).
* 12 of the 13 language-wheel entries are kept; the gap estimate is dropped.

## Extending it (for the GLM)

* **A new Rule 30 family:** add a branch to `Rule30Domain.build` (text, class, `check(scale)` or
  `exact()`, five scales), a lift function in `propose`, and (optionally) a recogniser and a
  ledger entry keyed by the family name that reads `params`.
* **A new Lean result:** add one line to `LEDGER` or `IMPLICATIONS` with the theorem name. That is
  the only way to make the engine say *proved*.
* **A new domain:** write a class with `build`, `propose(engine)` and `truth(h)`. The gate loop,
  the wheel and the dialogue are domain-free.
* **GLM general reasoning:** submit claims as JSON (`example_claims.json`). A `test` is a Python
  expression in `n` over a small whitelist of functions. A claims file can never produce *proved*.
* **ARC:** add a `Step` (with `fit` if it has parameters) and give it a `family`. The family is the
  need it serves. `diagnose_arc` states needs from the demonstrations alone.
