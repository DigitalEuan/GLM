# Primality certificates — the primality step without a ceiling

## Tier 0 — the coarse read

**Question.** Can the stepwise planner's primality step drop its ceiling of 10^12 by checking a certificate proved sound in Lean instead of running trial division, with every answer re-checked in a fresh interpreter and no answer below the old ceiling changed?

**Verdict.** Yes. Above 10^12 a primality step now carries a certificate — a factor, a Fermat witness or a Pratt certificate — whose check costs a few modular exponentiations at any size and is proved sound in Lean; below it nothing changed. The only refusal left is a work budget on factoring, never a size ceiling. All 6 marks were met.

**Deciding figure.** 6 of 6 marks; 17 of 17 held-out questions as expected (16 answered, 1 refused by the work budget as expected); 14 of 14 chains verified in a fresh interpreter, 56 of 56 mutants and 41 of 41 tampered certificates caught; 300 of 300 numbers above 10^12 agree with trial division; 0 of 30 stepwise cases moved; 9 of 11 large cases certified, 2 refused by the work budget, 0 wrong.

**Recomputed by.** `glm_universal.evaluation.primality_certificate_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The study of Phase 139. It takes one line of `STATUS.md` §2.2 (*the connected
machine, the rest*): **the primality step keeps a ceiling of 10^12.** The
stepwise planner's `prime` step decided primality by trial division, and the
step is computed three times per chain (the builder, the step gate and the
chain's column-3 script). At 10^12 trial division is up to a million divisions
per check, so the step refused everything above it.

The owner's standing preference, restated: avoid limits where they can be
avoided, because in a deterministic system a cap decides answers for reasons
that have nothing to do with the question.

**Verdict, as the body states it.** Yes. Above 10^12 a primality step now carries a certificate — a factor, a Fermat witness or a Pratt certificate — whose check costs a few modular exponentiations at any size and is proved sound in Lean; below it nothing changed. The only refusal left is a work budget on factoring, never a size ceiling. All 6 marks were met.

**Order of work, stated plainly.** The Lean file came first
(`RequestProject/GLM/PrimalityCertificate.lean`), then the run-time certifier
(`reasoning/primality_certificate.py`), then the step's wiring. The held-out
set (§3) was written and committed on its own after the wiring was written
but **before** the certified step was run on any of its questions; its
expected verdicts come from published facts and constructions, not from the
new code. Two fixes followed the first run and are recorded in §5.1.

## 1. What was built

### 1.1 The certificates (`reasoning/primality_certificate.py`)

| kind | what it says | why it proves it |
|---|---|---|
| `small` | `n < 2` | not prime by definition |
| `factor` | `1 < f < n` and `f` divides `n` | `factor_witness` |
| `fermat` | `1 <= a < n` and `a^(n-1) mod n != 1` | `fermat_witness` (Fermat's little theorem); no factor named |
| `pratt` | a list of entries `(p, a, [(q, e), ...])`, the last about `n` | `pratt_sound` (Lucas's theorem) |

A Pratt entry is accepted when `p >= 2`, `prod q^e = p - 1`, every `q` was
certified by an earlier entry, `a^(p-1) mod p == 1` and
`a^((p-1)/q) mod p != 1` for every `q`. The list is flat (no nested
structure), so `check` mirrors the Lean definitions `checkEntry`,
`checkChain` and `certifies` line for line.

**Finding** a certificate is separate from checking one. For a composite, the
certifier tries the small primes below 2000, then a strong-probable-prime
test to thirteen fixed bases: a base that fails Fermat becomes a `fermat`
certificate, and a nontrivial square root of 1 becomes a `factor`
certificate through a gcd — that is how Carmichael numbers, for which no
coprime base is a Fermat witness, are caught. For a prime, it builds a Pratt
certificate, factoring `p - 1` recursively by trial division and Brent's
variant of Pollard's rho.

**The work budget.** Factoring has no size ceiling but it is bounded by work:
two million rho iterations per certification (`BUDGET`). When the budget runs
out the step is refused `NO_CERTIFICATE`, naming the cofactor that was not
split. The probable-prime test only *steers* the search (which cofactor to
split next, which to certify); no verdict rests on it, and a wrong steer can
only cost a refusal.

### 1.2 The step (`runtime/stepwise.py`, `reasoning/stepwise_script.py`)

* **The builder.** For `n` above `stepwise_script.TRIAL_LIMIT` (10^12) the
  `prime` step calls `primality_certificate.verdict` and stores the
  certificate in the step's detail (and the factor, for a `factor`
  certificate, so column 2 still writes `n = f x n/f`). At or below 10^12 the
  step is exactly as before.
* **The step gate** (`recompute`) checks the certificate with the runtime's
  checker; a certificate that proves nothing recomputes as nothing, and the
  step is rejected.
* **Column 3.** The chain's script carries its own reader of certificates
  (`certified_verdict`), written apart from the runtime's checker, so a
  certificate is checked twice by two independent pieces of code, in two
  processes.
* `NO_CERTIFICATE` joins the refusal precedence just before
  `TOO_MANY_READINGS`, so a budget refusal names its cofactor instead of
  being reported as *no reading*.
* `CERTIFIED_PRIMALITY` switches the whole change off; it exists only for
  the round's own control (mark P5), which restores the old refusal.

### 1.3 A reader fix

The stepwise reader's pattern `is (.+) (?:a )?prime` captured *is N a prime*
greedily as the expression *N a*, so the question was refused. The pattern is
now non-greedy. This was seen in exploration before the held-out set was
written, so the two held-out questions that use the phrasing (`h11`, `h12`)
are declared as known, not held out.

## 2. What is proved (`RequestProject/GLM/PrimalityCertificate.lean`)

Standard axioms only; no `sorry`.

* `powMod_eq` — the square-and-multiply function `powMod m b e` equals
  `b ^ e % m` for every input. It runs on fuel, and when the fuel runs out the
  fallback is the definition itself, so no precondition is needed.
* `factor_witness` — a divisor `f` with `1 < f < n` shows `n` is not prime.
* `fermat_witness` — a base `a` with `1 <= a < n` and
  `powMod n a (n - 1) != 1` shows `n` is not prime.
* `prime_dvd_prod_pow` — a prime dividing a product of prime powers is one of
  the primes (the step that makes the listed factors of `p - 1` complete).
* `checkEntry_sound` — an accepted entry is about a prime (Mathlib's
  `lucas_primality`).
* `checkChain_sound` — every entry of an accepted list is about a prime.
* `pratt_sound` — **the check the tool runs**: `certifies n c = true` implies
  `n` is prime.
* Two instances above the old ceiling, checked by the kernel:
  `prime_10_12_39` (`10^12 + 39` is prime, with the certificate the run-time
  certifier produces, copied verbatim; a test checks that it still is the one
  the certifier produces) and `not_prime_10_12_1` (`10^12 + 1` is not prime,
  by the Fermat witness `2`, no factor named).

## 3. The held-out set (`evaluation/primality_certificate_cases.py`, `HELD_OUT`, 17)

Expected verdicts come from outside the new code: the published list of
Mersenne prime exponents (`2^p - 1` prime for `p = 61, 89, 107, 127, 521`;
`2^67 - 1 = 193707721 x 761838257287`, Cole); `2^32 + 1 = 641 x 6700417`
(Euler); the least primes above 10^12, 10^15 and 10^18 (`+39`, `+37`, `+3`)
and the greatest below 10^12 (`999999999989`) from published tables;
`10^12 + 1` and `10^18 + 1` divisible by `101`; the Carmichael number
`1042789205881 = 5581 x 11161 x 16741` (Chernick's form with `k = 930`); and
a stated product. One question (`h17`, *is 2 to the power 521 minus 1
prime*) is expected to be **refused**: the number is prime, but certifying it
means splitting a 55-digit cofactor of `2^520 - 1`, which the declared budget
does not reach, and the right answer under the budget is a refusal that
names that cofactor.

## 4. The marks

| mark | requirement |
|---|---|
| P1 | the Lean file holds the eight theorems, with no `sorry` |
| P2 | every held-out question is answered or refused as expected |
| P3 | every answered chain that holds a certificate verifies in a fresh `python3 -I`; every declared mutation is caught; every tampered certificate (a factor of 1, a base of 1, a dropped factor of `p - 1`, a chain with no earlier entries, a chain about another number) is rejected by both the step gate and the script |
| P4 | on 300 numbers above 10^12 (the 200 after 10^12 and 100 drawn from `[10^12, 10^13)` with seed 139), the certified verdict equals trial division run without a ceiling, and the certificate checks |
| P5 | the 30 stepwise composition cases answer exactly as with `CERTIFIED_PRIMALITY` off |
| P6 | on Mersenne primes `2^p - 1` (`p = 61, 89, 107, 127, 521, 607`) and five large composites, no verdict is wrong; those up to `2^127 - 1` and every composite are certified |

## 5. The measurement

`PYTHONPATH=. python3 -m glm_universal.tools primality-certificates`
(from `overlay/`):

```
P1 Lean           RequestProject/GLM/PrimalityCertificate.lean: missing [], sorry False
P2 held out       17 of 17 as expected, 0 wrong
P3 column 3       14 of 14 chains verified; 56 of 56 mutants caught; tampered certificates caught by the gate 41 and the script 41 of 41
P4 agreement      300 of 300 numbers above 10^12 agree with trial division (12 primes)
P5 interference   0 of 30 stepwise cases moved
P6 scale          9 of 11 certified, 2 refused by the work budget, 0 wrong
marks met         6 of 6
```

### 5.1 Fixes after the first run

* **The measurement's reader.** On the first run `h14` (*is 999999999989
  prime*, below the old ceiling) was answered correctly by the typed planner,
  whose answer is a sentence (*yes, 999999999989 is prime: no integer from 2
  to its square root divides it*); the reader borrowed from Phase 137 reads
  only chains, so it scored the right answer as a miss. `answer_of` now reads
  the typed planner's sentence too. The GLM's answer did not change.
* **A float in the core.** The certifier first built its table of small
  primes with `int(p ** 0.5)`, a floating-point construction inside
  `reasoning/`, one of the six sub-packages the no-float discipline is claimed
  for. `report blueprint` caught it (its section-1 claim turned from
  reproduced to refuted, 26 -> 25 of 39); the table now uses the exact
  `math.isqrt`, and the report reads 26 of 39 again.
* **The refusal's name.** The budget refusal first surfaced as
  `UNKNOWN_STEP: no reading`, because `NO_CERTIFICATE` was not in the
  refusal precedence. It now is, and the refusal names its cofactor.

### 5.2 Scale (mark P6)

| number | verdict | certificate | seconds |
|---|---|---|---|
| `2^61 - 1` | prime | Pratt, 13 entries | 0.002 |
| `2^89 - 1` | prime | Pratt, 20 entries | 0.001 |
| `2^107 - 1` | prime | Pratt, 18 entries | 0.004 |
| `2^127 - 1` | prime | Pratt, 19 entries | 0.005 |
| `2^521 - 1` | refused | a 55-digit cofactor not split | 1.965 |
| `2^607 - 1` | refused | a 170-digit cofactor not split | 5.889 |
| `(2^89 - 1)(2^107 - 1)` | not prime | Fermat | 0.000 |
| `(2^127 - 1)^2` | not prime | Fermat | 0.000 |
| `2^128 + 1` | not prime | Fermat | 0.000 |
| `10^60` | not prime | factor | 0.000 |
| `(10^18 + 3)(10^18 + 9)` | not prime | Fermat | 0.000 |

Timings are from one run and are not pinned. A composite is cheap at any size
(one modular exponentiation in the common case). A prime is as hard as
factoring `p - 1`; the two refusals are both primes whose `p - 1` has a large
cofactor that rho does not split within the budget.

### 5.3 Unchanged

* Below 10^12 the step is byte-for-byte the old one, and the typed planner's
  own primality frame (trial division to 10^12) is untouched; a question it
  refuses above 10^12 falls through to the stepwise planner as before, which
  now answers it.
* The full end-to-end evaluation is reported in `MASTER_PLAN.md`, Phase 139.

## 6. What this round does not do

* **Primes whose `p - 1` will not factor.** Pratt certificates need `p - 1`
  fully factored. A certificate that needs only a partial factorisation
  (Pocklington, or the Brillhart–Lehmer–Selfridge theorem with a factored part
  above the cube root) would certify `2^521 - 1` and its neighbours; so would
  elliptic-curve certificates. Each would need its own Lean soundness theorem
  first.
* **Other trial-division ceilings.** The typed planner's primality frame keeps
  its own limit of 10^12 (`semantic_plan.PRIME_LIMIT`); it is reached first
  and refuses, and the stepwise planner answers. Giving it certificates would
  change which surface answers, so it needs a frozen-path comparison.
* **The work budget is a number.** Two million rho iterations is a declared
  constant. It bounds time, not the size of the question, and a refusal under
  it always names the cofactor; but it is a constant all the same.

## 7. Files

* `overlay/glm_lean/RequestProject/GLM/PrimalityCertificate.lean` — the
  theorems of §2.
* `overlay/glm_universal/reasoning/primality_certificate.py` — the certifier
  and the checker.
* `overlay/glm_universal/runtime/stepwise.py` — the step, the control and the
  refusal precedence; `reasoning/stepwise_script.py` — the step gate and
  column 3's own certificate reader.
* `overlay/glm_universal/evaluation/primality_certificate_cases.py` — the
  held-out set and the measurement; `tools primality-certificates` prints it.
* `overlay/glm_universal/tests/test_primality_certificate.py` — 15 tests.

### 7.1 What this round leaves

* A partial-factorisation certificate (Pocklington / BLS) with its Lean
  theorem, so that primes like `2^521 - 1` are certified rather than refused.
* Certificates in the typed planner's primality frame, under a frozen-path
  comparison.
