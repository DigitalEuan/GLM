# Pocklington and N+1 certificates — primes whose `p - 1` will not split

## Tier 0 — the coarse read

**Question.** Can primes that Phase 139 refused because their `p - 1` does not factor within the work budget be certified instead, by certificates proved sound in Lean that need only part of `p - 1` (Pocklington) or the factorisation of `p + 1` (N+1), without changing any answer Phase 139 gave?

**Verdict.** Partly, and in two stages. The Pocklington certificate alone certifies `2^521 - 1` but none of the five primes the first held-out set left refused, so the first set's pre-declared mark failed. Those five all have a smooth `p + 1`, so an N+1 certificate was added and scored on a second, fresh held-out set, where it certified 13 of 13 primes with no wrong verdict. Both certificates are proved sound in Lean, and no answer Phase 139 gave moved. 6 of 7 marks were met.

**Deciding figure.** 6 of 7 marks. First held-out set: 0 wrong, but 0 of the 5 primes Phase 139 refused certified (the missed mark; 5 of 5 with the later N+1 certificate, counted post hoc). Second held-out set: 0 wrong, 13 of 13 primes certified (1 without N+1). 9 of 9 chains verified in a fresh interpreter, 36 of 36 mutants and 46 of 46 tampered certificates caught; 0 of 304 previously certified numbers and 0 of 30 stepwise cases changed.

**Recomputed by.** `glm_universal.evaluation.pocklington_certificate_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The study of Phase 140. It takes one sentence of `STATUS.md` §2.2 (*the
connected machine, the rest*), left by Phase 139: *a prime whose `p - 1` will
not factor within the work budget (`2^521 - 1`) is refused: a
partial-factorisation certificate (Pocklington / Brillhart–Lehmer–Selfridge)
with its Lean theorem would certify it.*

**Verdict, as the body states it.** Partly, and in two stages. The Pocklington certificate alone certifies `2^521 - 1` but none of the five primes the first held-out set left refused, so the first set's pre-declared mark failed. Those five all have a smooth `p + 1`, so an N+1 certificate was added and scored on a second, fresh held-out set, where it certified 13 of 13 primes with no wrong verdict. Both certificates are proved sound in Lean, and no answer Phase 139 gave moved. 6 of 7 marks were met.

**Order of work, stated plainly.**

1. **Part A.** The Lean file `RequestProject/GLM/PocklingtonCertificate.lean`
   came first, then the Pocklington search in
   `reasoning/primality_certificate.py`, then the column-3 reader. The first
   held-out set (`HELD_OUT`, 18 numbers, §3.1) was written and committed
   **before** the search ran on any of its numbers. `2^521 - 1`, `2^607 - 1`,
   `2^1279 - 1`, `2^2203 - 1` and `2^2281 - 1` were tried in exploration
   before that set was written; they are declared as `KNOWN`, not held out.
2. **The first run** met 5 of its 6 marks. Mark Q2 failed: the set's five
   refused primes (`33! - 1`, `94! - 1`, `166! - 1`, `317# - 1`,
   `337# - 1`) stayed refused. A diagnosis (§5.1) showed that their `p - 1`
   factored part falls far short of `√p`, and even of `p^(1/3)`, so a
   Brillhart–Lehmer–Selfridge certificate would not have reached them either.
   What they share is that `p + 1` (`n!` or `p#`) is made of small primes.
3. **Part B.** An N+1 certificate was chosen *because of that observation*,
   so the first set cannot score it. A second held-out set (`HELD_OUT_B`, 16
   numbers, §3.2) was written and committed **before** the N+1 certificate
   was written, together with its mark (Q7: no wrong verdict and at least two
   thirds of its primes certified, `Q7_SHARE`). Then came the Lean file
   `RequestProject/GLM/LucasCertificate.lean`, then the search, then the
   reader. Mark Q2 is still scored as registered, with the N+1 certificate
   off; the column showing it on is reported as post hoc.

## 1. What was built

### 1.1 The certificates (`reasoning/primality_certificate.py`)

| kind | entry | why it proves it |
|---|---|---|
| `pocklington` | `[p, [[q, e, a], ...]]`: with `F = prod q^e`, `F` divides `p - 1`, `p < (F + 1)^2`, the `q` distinct and each certified earlier, and for each factor `a^(p-1) mod p == 1` and `gcd((a^((p-1)/q) mod p + p - 1) mod p, p) == 1` | `pocklington_sound` |
| `lucas` | a mixed chain: Pocklington entries as above, and N+1 entries `[p, P, [[q, e], ...]]` with `prod q^e = p + 1`, each `q` certified earlier, `X^(p+1) = 1` in `(Z/p)[X]/(X^2 - P X + 1)`, and for each `q` the norm of `X^((p+1)/q) - 1` coprime to `p` | `lucas_prime`, `mixed_sound` |

The ring arithmetic is on pairs `(a, b) = a + bX` of residues; `X^2 = P X - 1`,
and `-bd` is computed as `bd (p - 1)` modulo `p`, so the checker uses only
natural numbers, exactly as the Lean definitions `qmul`, `qpow`, `qsubOne`
and `qnorm` do. The norm of `u + vX` is `u^2 + P u v + v^2`.

**The order of the searches.** `certify` runs the Pratt search first, exactly
as in Phase 139. Only when its budget runs out (and the strong
probable-prime test says the number is prime, which only steers) does it run
the Pocklington search with a fresh budget, and only if that runs out the
mixed search with a third. The mixed search certifies a number by an N+1
entry when `p + 1` splits completely within the budget, and otherwise by a
Pocklington entry; the primes inside either entry are certified the same
way. So every number Phase 139 certified keeps its Pratt certificate (mark
Q6), and a refusal still names the cofactor the Pratt search could not split.

Two controls, `POCKLINGTON` and `LUCAS`, switch the stages off; with both off
the certifier is Phase 139's (mark Q4).

### 1.2 The step and column 3

Nothing in the step changed: the `prime` step calls `verdict` and the step
gate calls `check`, so the new kinds arrive through those two functions.
Column 3's own reader (`certified_verdict`, in the generated script) gained a
branch for each new kind, written apart from the runtime's checker, with its
own pair arithmetic.

## 2. What is proved

Standard axioms only; no `sorry`.

### 2.1 `RequestProject/GLM/PocklingtonCertificate.lean`

* `prime_pow_dvd_of_witness` — if a factor `(q, e, a)` passes for `p >= 2`,
  `q` is prime and `q^e` divides `p - 1`, then `q^e` divides `r - 1` for
  every prime `r` dividing `p` (the order of `a^((p-1)/q^e)` modulo `r` is
  exactly `q^e`).
* `prod_dvd_of_pow_dvd` — for distinct primes, the product of the prime
  powers divides whatever each divides.
* `prime_of_factor_bound` — if every prime factor `r` of `p >= 2` has
  `F | r - 1` and `p < (F + 1)^2`, then `p` is prime.
* `checkPEntry_sound`, `checkPChain_sound`, `pocklington_sound` — **the
  check the tool runs**.
* `prime_2_521_sub_one` — `2^521 - 1` is prime, by the 33-entry certificate
  the run-time search produces, checked by the kernel.

### 2.2 `RequestProject/GLM/LucasCertificate.lean`

* `toQuad_qmul`, `toQuad_qpow`, `toQuad_qsubOne` — the pair arithmetic modulo
  `p` is the arithmetic of `R = (ZMod r)[X]/(X^2 - P X + 1)` for every prime
  `r` dividing `p`.
* `isUnit_of_qnorm` — a pair whose norm is nonzero modulo `r` is a unit of
  `R`.
* `card_quadRing` — `R` has `r^2` elements.
* `lucas_prime` — **the N+1 test**: an accepted N+1 entry is about a prime.
  Take `r` the least prime factor of `p`; `X` is a unit of `R` of order
  exactly `p + 1`, so `p + 1 <= #R^x < r^2`; a composite `p` has `r^2 <= p`.
  No quadratic non-residue enters the proof: a `P` that does not give order
  `p + 1` simply fails the check.
* `checkMChain_sound`, `mixed_sound` — **the check the tool runs** for the
  mixed chain.
* `prime_33_factorial_sub_one` — `33! - 1` is prime, by the 12-entry mixed
  certificate the run-time search produces (eleven Pocklington entries and
  one N+1 entry), checked by the kernel.

To let the kernel evaluate the checkers across modules, `powModF` and
`powMod` in `PrimalityCertificate.lean` and the Pocklington definitions are
now marked `@[expose]`; nothing else in that file changed.

## 3. The held-out sets (`evaluation/pocklington_certificate_cases.py`)

### 3.1 `HELD_OUT` (part A, 18 numbers)

Factorial primes `n! - 1` for `n = 30, 32, 33, 38, 94, 166` (OEIS A002982),
with `31! - 1` and `34! - 1` composite; primorial primes `p# - 1` for
`p = 41, 89, 317, 337` (OEIS A006794), with `43# - 1` composite; repunits
`R19`, `R23` prime and `R21` composite (OEIS A004023); `2^523 - 1` and
`2^541 - 1` composite. The questions state the numbers as decimal literals,
because the stepwise reader has no factorial or primorial.

### 3.2 `HELD_OUT_B` (part B, 16 numbers)

`3 * 2^n - 1` prime for `n = 143, 206, 216, 306, 324, 391, 458, 470, 827`
(OEIS A002235) and composite for `n = 144, 207`; `991# - 1` and `1873# - 1`
prime (OEIS A006794); `324! - 1` and `379! - 1` prime (OEIS A002982), and
`325! - 1` composite. Every family has `p + 1` made of small primes, the
property part B was chosen for, but no number in it had been tried.

## 4. The marks

| mark | requirement |
|---|---|
| Q1 | both Lean files hold their theorems (seven each), with no `sorry` |
| Q2 | on `HELD_OUT`, with the N+1 certificate off: no wrong verdict (Phase 139's certifier, the Pocklington certifier and the router); the router agrees with the certifier on every number; at least half of the primes Phase 139 refuses are certified |
| Q3 | every answered chain holding a Pocklington or mixed certificate verifies in a fresh `python3 -I`; every declared mutation is caught; every tampered certificate is rejected by both the step gate and the script |
| Q4 | with both controls off, Phase 139's 17 held-out questions answer as Phase 139 recorded; with them on, only `h17` (`2^521 - 1`) moves, to its published verdict |
| Q5 | the kernel-checked certificates for `2^521 - 1` and `33! - 1` are the ones the run-time search produces |
| Q6 | the 300 numbers of Phase 139's mark P4 and the Mersenne primes up to `2^127 - 1` get the same verdict and certificate; the 30 stepwise composition cases answer as with both controls off |
| Q7 | on `HELD_OUT_B`, every control on: no wrong verdict, and at least two thirds of its primes certified (declared before part B was written) |

The tampered certificates are: a Pocklington part cut to one factor, a base
of 1, a repeated factor, an exponent raised, a chain with no earlier entries,
a chain about another number; for an N+1 entry, a dropped factor of `p + 1`,
an exponent raised, `P = 2` (where `X - 1` is nilpotent), no earlier entries,
another number.

## 5. The measurement

`PYTHONPATH=. python3 -m glm_universal.tools pocklington-certificates`
(from `overlay/`), the final run:

```
Q1 Lean           RequestProject/GLM/PocklingtonCertificate.lean, RequestProject/GLM/LucasCertificate.lean: missing [], sorry False
Q2 held out       18 numbers, 0 wrong; 0 of the 5 primes Phase 139 refused are now certified; the router agrees on 18 of 18 (N+1 off, as registered; with N+1, post hoc: 5 of 5)
Q3 column 3       9 of 9 chains verified; 36 of 36 mutants caught; tampered certificates caught by the gate 46 and the script 46 of 46
Q4 control        off: 0 of 17 Phase 139 questions moved; on: [('h17', 'prime')]
Q5 kernel         the 33-entry pocklington certificate for 2^521-1 is the Lean instance: True; the 12-entry lucas certificate for 33!-1 is the Lean instance: True
Q6 interference   0 of 304 certified numbers changed; 0 of 30 stepwise cases moved
Q7 held out B     16 numbers, 0 wrong; 13 of 13 primes certified (1 without N+1); the router agrees on 16 of 16
marks met         6 of 7
```

The first run (part A only) printed the same Q1–Q6 lines for part A's
content: 5 of 6, with Q2 failing as above.

### 5.1 Why Q2 failed

For each of the five refused primes, the Pocklington search was run to the
end of its budget and the factored part `F` of `p - 1` recorded (digits):

| number | digits | `F` found | needed (`√p`) | `p^(1/3)` |
|---|---|---|---|---|
| `33! - 1` | 37 | 1 | 18.5 | 12.3 |
| `94! - 1` | 147 | 20 | 73.5 | 49 |
| `166! - 1` | 298 | 6 | 149 | 99.3 |
| `317# - 1` | 131 | 12 | 65.5 | 43.7 |
| `337# - 1` | 136 | 7 | 68 | 45.3 |

`p - 1 = n! - 2` (or `p# - 2`) is twice a number with no special structure,
and Pollard's rho within the budget finds only its small factors. The
Mersenne prime `2^521 - 1` is different: `2^520 - 1` splits along its
cyclotomic factors. So the gap was the factoring, not the theorem, and a
cube-root (BLS) certificate would not have closed it.

### 5.2 Part B's held-out set

| number | without N+1 | with N+1 | certificate | seconds |
|---|---|---|---|---|
| `3*2^143-1` | prime | prime | Pratt | 0.6 |
| `3*2^206-1` … `3*2^827-1` (8 numbers) | refused | prime | mixed | 5.8–34.5 |
| `3*2^144-1`, `3*2^207-1` | not prime | not prime | Fermat | 0.3–0.4 |
| `991# - 1` | refused | prime | mixed | 154 |
| `1873# - 1` | refused | prime | mixed | 897 |
| `324! - 1` | refused | prime | mixed | 440 |
| `379! - 1` | refused | prime | mixed | 778 |
| `325! - 1` | not prime | not prime | factor | 4.3 |

The seconds are for the whole row: the certifier without N+1, with it, and
the routed question (which certifies again and checks twice), from one run,
not pinned. Most of the time is the Pratt and Pocklington searches running
their budgets out on the large numbers before the mixed search starts. For
`991# - 1` alone, the Pratt search took 25 s, the Pocklington search 3 s,
the mixed search 21 s (168 entries), and one check 6 s.

### 5.3 Seen before the sets (reported, not marked)

`2^521 - 1` is certified by Pocklington (2.3 s); `2^607 - 1` (6.8 s) and
`2^1279 - 1` (23 s) by the mixed chain, since `p + 1 = 2^k`: a single N+1
entry with the one factor 2, which is in effect the Lucas–Lehmer test.

### 5.4 Unchanged

* Phase 139's own measurement (`tools primality-certificates`) still meets
  6 of 6; its mark P2 now scores `h17` against the published verdict
  (`primality_certificate_cases.SUPERSEDED`), and with `POCKLINGTON` off its
  held-out set holds exactly as written. Re-run this round: 17 of 17 as
  expected, 15 of 15 chains verified (the answered `h17` adds one), 60 of 60
  mutants and 41 of 41 tampered certificates caught, 300 of 300 agreeing with
  trial division, 0 of 30 moved, and on its scale mark 11 of 11 certified
  where it was 9 of 11 (`2^521 - 1` by Pocklington, `2^607 - 1` by the mixed
  chain), 0 wrong.
* The full end-to-end evaluation is reported in `MASTER_PLAN.md`, Phase 140.

## 6. What this round does not do

* **The cost of a refusal grew.** A prime that none of the three searches
  reaches now spends three budgets before it is refused, and the large
  certified primes of §5.2 take minutes. Running the N+1 search before the
  Pocklington search when `p + 1` is visibly smooth would cut most of that,
  but it would change which certificate some numbers get (`2^521 - 1` would
  get a mixed one), so it is left for a round that re-pins the instance.
* **The check of a large N+1 entry costs seconds** (one ring exponentiation
  per prime of `p + 1`; 168 of them for `991# - 1`), and the step is checked
  twice.
* **Neither side splits.** A prime whose `p - 1` and `p + 1` both resist the
  budget is still refused; elliptic-curve certificates would be the next
  kind, each with its own Lean theorem.
* **The typed planner's primality frame** keeps its limit of 10^12 (as in
  Phase 139; giving it certificates needs a frozen-path comparison).

## 7. Files

* `overlay/glm_lean/RequestProject/GLM/PocklingtonCertificate.lean`,
  `overlay/glm_lean/RequestProject/GLM/LucasCertificate.lean` — §2.
* `overlay/glm_universal/reasoning/primality_certificate.py` — the searches,
  the checkers and the controls; `reasoning/stepwise_script.py` — column 3's
  readers for the new kinds.
* `overlay/glm_universal/evaluation/pocklington_certificate_cases.py` — both
  held-out sets and the measurement; `tools pocklington-certificates` prints
  it. `evaluation/primality_certificate_cases.py` — `SUPERSEDED`.
* `overlay/glm_universal/tests/test_pocklington_certificate.py` — 19 tests;
  `tests/test_primality_certificate.py` — two tests now run Phase 139's
  budget refusal under the control.

### 7.1 What this round leaves

* The N+1 search ahead of the Pocklington search when `p + 1` is smooth,
  with the `2^521 - 1` instance re-pinned (§6).
* Elliptic-curve certificates, for primes neither side reaches.
* Certificates in the typed planner's primality frame, under a frozen-path
  comparison.
