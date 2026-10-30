# GLM Hypothesis Engine — the portable module

The engine began as a Rule 30 tool (Rounds 38–39, `../Rule30/HYPOTHESIS_ENGINE.md`), but its core
is not specific to Rule 30. This folder holds the parts meant to move into the GLM for other
investigations: the Lean checks of the engine's verdicts on problems other than Rule 30, and this
guide. The Python core is in the study folder `rule30_round39/glm_hypothesis_core.py` and needs
only the standard library.

## Files

| File | Contents |
|---|---|
| `Benchmarks.lean` | kernel-checked verdicts on eight problems with known answers (Euler's polynomial, Fermat numbers, sums of two squares, circle regions, Josephus, the gcd trap) |
| `BenchmarksData.lean` | finite certificates (`native_decide`) and the two bit-blasted midpoint laws (`bv_decide`); these trust Lean's compiler |
| `DialogueChecks.lean` | Round 41: the implications the self-dialogue may state, checked. "Read inside the transient" does not imply aperiodicity (`transient_read_does_not_imply_aperiodic`); aperiodic yet computed by a two-state automaton reading `n` (Thue–Morse, `aperiodic_but_automatic`); a tie between two mined laws that no data can split (`doubling_law_tie_unsplittable`) |
| `TaxChecks.lean` | Round 42: the TAX statements of v13, checked. Conservation is the same for every `Y` and equals `3c² − 2c(a+b) + ab = 0` (`tax_defect_eq`, `tax_conserved_iff_defect_zero`); v13's criterion `c ∈ {0, a, b}` is wrong (`docstring_criterion_wrong`); every doubling of the left-diagonal period is TAX-conserved (`tax_conserved_at_doubling`) |
| `TaxChecksData.lean` | Round 42 certificate (`native_decide`): the 25 TAX-conserved pairs of left diagonals below 400, 15 of them away from any white diagonal (`tax_conserved_pairs_below_400`, `tax_conserved_not_only_white`) |
| `NeedsWheel.lean` | Round 44: the contract of the owner's *needs wheel*. A provision answers some questions and stays silent on others; the engine takes the first provision that speaks. Sound provisions never lose a right answer and never create a wrong one (`answer_right_of_right`, `answer_wrong_of_wrong`, `card_wrong_le`, `card_right_le`); their effect is local (`answer_local`); order does not matter among them (`answer_perm`); one unsound provision can hurt (`unsound_can_hurt`); no finite data decides "infinitely many" (`finite_data_never_forces_infinitely_many`) | FORMAL |
| `WheelChecksData.lean` | Round 44: certificates on the owner's `glm_wheel.json`. H19 (`abs(2L(n) − n) ≤ 10`) is false at n = 11101 (`wheel_H19_false`); ledger C160's "within 6 of n/2 to 20000" is false at n = 19521 (`ledger_C160_overstated`); H16 (no eventual period ≤ 64 with preperiod ≤ 10000) is true (`wheel_H16_true`). Farkas certificates for linear complexity (`le_lcProfile_of_farkas`, FORMAL) checked by `native_decide` | CERT |
| `GateLoop.lean` | Round 45: the contract of engine v17's gate loop. Layered reads on nested domains (`holdsAt_anti`, `holdsAll_iff_top`, `firstFail_spec`, `refuted_stable`; v16's any-layer rule is vacuous: `anyScale_vacuous`, `anyScale_ne_largest`; `exclusive_mono`); escalate before assert (`escalate_eq_some`, `escalate_refutes`, `finite_range_never_proves_forall`, `escalate_append`) and the arrow (`reads_prefix`, `reads_sorted`); typed transitive rollback (`retracted_least`, `retracted_union`, `retracted_idem`, `rollback_sound`, `derived_edge_unsound`, `loop_eq_retracted`, `loop_terminates`); the gate cascade (`cascade_sound`, `cascade_no_wrong`, `survives_as_proved_unsound`) | FORMAL |
| `GateLoopData.lean` | Round 45: v17's full-range H16, no eventual period `p ≤ 64` with preperiod `≤ 30000` (`centre_no_short_period_30000`) | CERT |
| `README.md` | this guide |

Study-folder side (`rule30_round39/`): `glm_hypothesis_core.py` (core v6),
`general_benchmarks.py` (the eight problems), `test_round39.py`.

Round 41 (`rule30_round41/`): `glm_dialogue.py`, the v11 self-dialogue layer on top of core v6.
Every answer is an executed action, or a citation of a checked edge in `knowledge.json`, and every
number it utters is checked against the run and the ledger. `run_round41.py` runs it on Rule 30
and on the eight benchmarks. `v10_audit.py` is the audit of the owner's v10 script.

Round 42 (`rule30_round42/`): `glm_guards.py`, five portable reasoning guards that check a run's
sentences rather than its numbers. *identity* brute-forces a stated criterion. *explained-away*
checks whether a known law's premise forces a "finding". *coincidence* is an exact hypergeometric
tail. *exclusivity* tests "only at S" claims. *consistency* catches any claim still asserted after
its hypothesis was refuted. `make_v14.py` builds the owner's v13 into v14 with the guards running
inside the engine. `v13_audit.py` is the audit of v13.

### The dialogue contract (v11)

A puzzle adds a `PuzzleConfig`, which contains no sentences: a budget per invariant, local
predicates for reading counterexamples, the event to explain for each invariant, and a tagger that
attaches knowledge-graph tags to hypotheses from their metadata. The dialogue then runs
state → refute (executed) → implies (checked edges only) → connects → next (executed) on each
hypothesis, and puts the new hypotheses its actions create at the front of the queue.

## The contract

A puzzle supplies an **indexed family of exact invariants**: `observe(hi) -> {k: {name: value}}`,
where each value is an int, a `Fraction` or a bool. The core never sees the answer, and it never
uses floats.

| step | what it does | Lean contract (`../Rule30/ConjectureLoop.lean`) |
|---|---|---|
| lift | uniform statements from a development range (always-true, finite set, divides, bound) | — |
| check / escalate | development range, then held-out ranges the proposer never saw | `refuted_of_fail`, `SurvivesTo.of_holds` |
| cut / narrow | the range where a refuted lift holds; the sharpest parameter the data allow | `narrow_eventually_eq`, `narrow_le_of_holds` |
| mine | local predicates (and pairs of them) matching an event exactly | — |
| mine_residue | `event ⟺ k mod m ∈ S` for the smallest `m` | — |
| mine_formula | polynomial, linear recurrence, template `a·k + b·g(k) + c` | — |
| junction | two fits tie: observe the first index where they differ | `junction_split` |
| classify | FINITE / Pi1 / Pi2 — what kind of evidence could ever settle it | — |

Statuses are `survives` (on a stated range), `refuted-dev`, `refuted-heldout`, `law-holds`,
`form-holds`, `implied` and `open`. The engine never says "proved"; only the prover does.

## A playbook for GLM bottlenecks

These are the moves that produced results in Rounds 38–39, stated so that they carry over to
other investigations.

1. **Make the question an indexed family.** Rule 30's left diagonals, the primes, `n` points on a
   circle, the inputs of a function under test: pick an index `k` and exact invariants of each
   instance.
2. **Lift cheaply, then hold out.** A statement that passes the development range is a candidate,
   not a result. Across the two rounds, 17 false statements passed development data and were
   caught later (4 in Round 38; 13 in Round 39: 9 in the benchmarks, 4 on Rule 30). Examples:
   * Rule 30: period ≤ 8, the right-diagonal closed form;
   * Euler's polynomial;
   * `2^(n−1)` regions;
   * the random-permutation model of the Rule 30 regimes.
3. **Read the counterexample.** Do not just narrow the parameter; ask what is special about the
   failing instance, then mine a law that predicts all failures.
   * Rule 30: diagonal 399 is white, which gave the period law.
   * Euler's polynomial: the value at 40 is `41²`, which gave the residue law mod 41.
   * The midpoint: the failing inputs overflow.
4. **Split junctions with one observation.** When two laws fit, compute where they differ and look
   there. Examples: the white diagonal 53207 split the Rule 30 white-diagonal laws; `n = 6` split
   the circle-region laws.
5. **Know when sampling cannot help.** A Pi1 statement ("for every `k`") can survive every range
   and still be false. In the gcd trap the first counterexample has 52 digits.
   * Switch to a **structural reader**: an invariant that any counterexample must satisfy. Here it
     is the resultant; any common factor must divide it.
   * That turns an infinite search into a finite computation, and it found the counterexample.
6. **Look for injectivity plus finiteness.** If the dynamics between two events is an injective
   map on a finite set, every orbit either reaches the event or is a cycle. Pigeonhole then turns
   "never" into a finite check.
   * This is the move that proved Rule 30 has infinitely many white left diagonals
     (`white_after_white`).
   * It applies to any reversible finite-state process.
7. **Hand statements, not scores, to the prover.** Every survivor goes out as a precise statement:
   * a Lean theorem if it is proved;
   * a `sorry`-guarded statement in the hand-off file if it is open;
   * labelled `EMP` if it rests on unverified computation.

## Results of the eight benchmarks

| problem | engine's final statement | checked in Lean |
|---|---|---|
| Euler `n² + n + 41` | 41 divides the value ⟺ `n mod 41 ∈ {0, 40}` | `euler_dvd_iff`, `euler_composite_of_mod` (every `n`) |
| Fermat numbers | not always prime (`F₅`); pairwise coprime survives | `fermat_five_not_prime`, `fermat_pairwise_coprime` |
| primes as `a² + b²` | ⟺ `p mod 4 ∈ {1, 2}` | `two_squares_law` (every prime) |
| circle regions | `C(n,4) + C(n,2) + 1`, after splitting the `2^(n−1)` junction at `n = 6` | `moser_junction`, `moser_split` |
| Josephus | `J(n) = 2(n − 2^⌊log₂ n⌋)` | `josephus_closed_form` (every `n ≥ 1`), `josephus_eq_sim` (`n ≤ 64`) |
| Collatz | "reaches 1" survives but is Pi2 (open); stopping times are unbounded | `collatz_reaches_one_below` (`n < 10⁴`), `collatz_27_slow` |
| gcd trap | false; counterexample found by the resultant | `gcd_trap_survives` (`n < 1000`), `gcd_trap_refuted` (kernel) |
| 16-bit midpoint | fails ⟺ `lo + hi` overflows; the fix is correct | `midpoint_bug_iff_overflow`, `midpoint_fixed_correct` (every input) |


Round 44 (`rule30_round44/`): `glm_needs.py`, the portable needs-wheel protocol (needs, provisions,
wheel, first-speaker answer, honesty guard, scoring right / wrong / overclaim / abstain, random
and leave-one-out controls). `needs_rule30.py` applies it to the 40 statements of the owner's
`glm_wheel.json`; `needs_arc.py` to synthetic ARC families (held-out) and to the ARC tasks in
`glm_repo.zip`; `run_round44.py` runs everything and writes `out/`. `V16_WHEEL_REVIEW.md` is the
review of v16 and the wheel, with the results.

Round 45 (`rule30_round45/`): engine v17, `hypothesis_engine_v17.py` with `glm_layers.py`. It runs
the TCT gate cascade after every stage: claim class → recompute → refutation audit → escalation →
implication → Lean ledger. Its layers have real scales and a verdict rule per kind of claim.
Rollback follows dependency edges only and is computed as a fixpoint. Every hypothesis carries its
read trajectory (the arrow). It speaks only backed claims. `run_round45.py` scores v15/v16/v17,
`test_round45.py` holds the tests, and `V17_REPORT.md` is the report. Registries are separate
from the gates: a new domain adds entries to `CLAIM_CLASS`, `ESCALATIONS`, `RECOMPUTE`,
`IMPLICATIONS` and `LEDGER`.

Round 46: engine v18 (`glm_engine/hypothesis_engine.py` in the user deliverables), one
self-contained standard-library script. `Wheel.lean` (namespace `GLM.Wheel`) is the contract of
its wheel: only the KNOWS ring asserts (`assertion_isSome_iff`, `thinksTrue_asserts_nothing`);
speaking from a sound wheel is correct (`speak_sound`); merging two sound wheels in a turn stays
sound (`merge_sound`, `knows_merge`, `dontKnow_merge`); two KNOWS entries that disagree prove one
wheel unsound (`conflict_unsound`). For the Rule 30 conjecture loop, `lift f s` is the running
maximum of `f` up to `s`: it bounds `f` there (`lift_holds`), is monotone (`lift_mono`), a failure
above `s` forces a strictly higher re-lift (`lift_lt_of_fail`, `fail_above`) and a re-lift holds
again (`relift_holds`). Builds with no `sorry`; axioms `propext`, `Classical.choice`, `Quot.sound`.

Round 47: all the Lean files of this module are imported by `../HypothesisEngine.lean`
(`lake build RequestProject.GLM.HypothesisEngine`). `GateLoopData.centre_no_short_period_30000` is
now also read through the 2-adic layer ↔ period dictionary (`../Rule30/AdicTowerData.lean`,
`centerCol_not_fraction_64`).
