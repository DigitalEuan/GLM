# Elliptic-curve certificates — primes where neither `p - 1` nor `p + 1` splits

## Tier 0 — the coarse read

**Question.** Can primes that Phase 140 refused, because neither `p - 1` (Pratt, Pocklington) nor `p + 1` (N+1) splits within the work budget, be certified instead by elliptic-curve certificates proved sound in Lean, without changing any answer Phase 139 or Phase 140 gave?

**Verdict.** Yes, on the held-out set. An elliptic-curve entry, proved sound in Lean from the trivial bound on the number of points of a curve and found at run time by complex multiplication, certified all 6 of the 6 held-out primes Phase 140 refused, with no wrong verdict, and moved no earlier answer. 5 of 6 marks were met. The missed mark is a tampered certificate that was wrongly declared invalid: on the secp256k1 prime the search found a curve of prime order, so raising its cofactor to 2 still gives a valid certificate, and the checker was right to accept it.

**Deciding figure.** 5 of 6 marks. Held-out set: 17 numbers, 0 wrong, 6 of 6 refused primes certified, and the router agrees on 17 of 17. 6 of 6 chains verified in a fresh interpreter, 24 of 24 mutants caught, 40 of 42 tampered certificates rejected by both the step gate and the script (the 2 accepted are valid; §5.1). 0 of 35 earlier held-out cases, 0 of 304 previously certified numbers and 0 of 30 stepwise cases changed. `2^255 - 19` is checked by the kernel.

**Recomputed by.** `glm_universal.evaluation.elliptic_certificate_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

This is the study of Phase 141. It takes one clause of `STATUS.md` §2.2 (*the
connected machine, the rest*), left by Phase 140: *a prime that neither side
reaches within the budget is still refused (elliptic-curve certificates would
be the next kind)*.

**Verdict, as the body states it.** Yes, on the held-out set. An elliptic-curve entry, proved sound in Lean from the trivial bound on the number of points of a curve and found at run time by complex multiplication, certified all 6 of the 6 held-out primes Phase 140 refused, with no wrong verdict, and moved no earlier answer. 5 of 6 marks were met. The missed mark is a tampered certificate that was wrongly declared invalid: on the secp256k1 prime the search found a curve of prime order, so raising its cofactor to 2 still gives a valid certificate, and the checker was right to accept it.

**Order of work, stated plainly.**

1. The Lean file `RequestProject/GLM/EllipticCertificate.lean` came first,
   with the soundness theorem and without an instance.
2. The held-out set (`HELD_OUT`, 17 numbers, §3) and its mark (E2: no wrong
   verdict, and at least half of the primes Phase 140 refuses certified,
   `E2_SHARE`) were written and committed **before** the elliptic search
   existed, and before Phase 140's certifier had been run on any of their
   numbers. Every verdict in the set comes from a published source.
   Exploration before the set was written used only primes drawn by a seeded
   generator (`KNOWN` is empty).
3. Then came the search (`reasoning/elliptic_certificate.py`), the checker in
   `reasoning/primality_certificate.py`, and column 3's own reader.
4. **The first run** met 3 of 6 marks. E1 and E5 failed because the
   kernel-checked instance was named before any certificate existed:
   `e08` (`2^130 - 5`). The Pratt search certifies `e08`, so it carries no
   elliptic entry. **The instance was re-chosen after that run**, as the
   held-out prime with the fewest elliptic entries, `e01` (`2^255 - 19`,
   5 elliptic entries out of 29). This choice is post hoc and recorded as
   such in the cases module. E3 failed as described in §5.1.
5. **The second run**, with the instance in Lean, met 5 of 6 marks (§5).

## 1. What was built

### 1.1 The entry

An elliptic entry is `[p, a, b, x, y, k, q]`. It is accepted when all of the
following hold:

* `p` is odd and at least 3;
* `4a^3 + 27b^2` is coprime to `p`;
* `(x, y)` lies on `y^2 = x^3 + a x + b` modulo `p`;
* `q` was certified by an earlier entry, and `4p < (q - 1)^2`;
* `Q = k (x, y)` is computed as an affine point, and `q Q` is computed as the
  point at infinity.

The arithmetic works on natural numbers modulo `p`. Each division is a
multiplication by an inverse found with the extended Euclidean algorithm, and
the inverse is **checked**. Any step the group law cannot take modulo `p`
makes the whole check fail. The runtime checker `_check_eentry` mirrors the
Lean `checkEEntry` line by line.

A chain may mix elliptic entries (length 7) with Pocklington entries
(length 3) and N+1 entries (length 3 with a leading `P`) from Phase 140, and
with the base entries of length 2. The certificate kind is `elliptic`.

### 1.2 The search (`reasoning/elliptic_certificate.py`)

The search uses complex multiplication (Atkin–Morain):

1. For a discriminant `D` (with `-3 >= D >= -3000` and class number at most
   10), Cornacchia's algorithm solves `4p = t^2 + |D| s^2`. Square roots
   modulo `p` use Cipolla's method.
2. The candidate orders are `p + 1 -+ t`, or four or six orders when `D` is
   -4 or -3. Each order is cleared of primes below 100,000 by trial division,
   then of further small factors by rho, until a cofactor `q` with
   `4p < (q - 1)^2` remains that is a probable prime.
3. The class polynomial `H_D` is computed from the `q`-expansion of `j` at the
   reduced forms, using **fixed-point integer arithmetic** (no float is
   constructed), and then rounded. All 582 discriminants in range round
   cleanly. A wrong coefficient could only make a curve fail the check, never
   make a wrong entry pass.
4. A root of `H_D` modulo `p` gives `j`, and from it a curve and its twist.
   A point is found, and the entry is kept if it passes the checker.
5. The entry's own `q` is certified by the same descent. Below `10^30` it is
   certified by Phase 140's mixed search instead.

The work is bounded by a budget of 400 descent nodes and 20,000,000 rho
iterations. When either budget runs out, the step stays refused.

**The order of the searches.** `certify` runs the Pratt, Pocklington and mixed
searches exactly as in Phase 140, and tries the elliptic search only when all
three have refused. So every number Phase 140 certified keeps its certificate
(mark E6). A control, `ELLIPTIC`, switches the new stage off; with it off the
certifier is Phase 140's (mark E4).
`evaluation/pocklington_certificate_cases.flags` now sets `ELLIPTIC` off by
default, so Phase 140's own measurement is taken exactly as before.

### 1.3 The step and column 3

Nothing in the step changed: the new kind arrives through `verdict` and
`check`. Column 3's reader (`certified_verdict`, in the generated script)
gained a branch for `elliptic`. It is written apart from the runtime's
checker, with its own curve arithmetic.

## 2. What is proved

Standard axioms only; no `sorry`. File:
`RequestProject/GLM/EllipticCertificate.lean`.

* `natCast_mod_of_dvd`: reduction modulo `p` commutes with the cast to
  `ZMod r` for every `r` dividing `p`.
* `rep_ecAdd`, `rep_ecMulF`: every step the law takes modulo `p` is a step of
  the group law of the curve over `ZMod r`, for each prime `r` dividing `p`.
  Mathlib's `WeierstrassCurve` points are used for that group law. An inverse
  checked modulo `p` is an inverse modulo `r`.
* `card_point_le`: a curve over `ZMod r` has at most `2r + 1` points (for each
  `x`, at most `y` and `-y`, plus the point at infinity).
* `elliptic_prime` — **the elliptic test**: an accepted entry is about a
  prime. Take `r` to be the least prime factor of `p`. Then `Q` reduces to a
  nonzero point killed by the prime `q`, so its order is `q`, and
  `q <= 2r + 1`. A composite `p` has `r^2 <= p`, so `(q - 1)^2 <= 4p`, which
  the entry excludes. No point counting, no Hasse bound and no complex
  multiplication enter the proof.
* `checkEAnyEntry_sound`, `checkEChain_sound`, `elliptic_sound` — **the check
  the tool runs**, for the mixed chain with elliptic entries.
* `prime_2_255_sub_19`: `2^255 - 19` is prime, by the 29-entry certificate the
  run-time search produces (5 elliptic entries). The kernel checks it in about
  42 s.

## 3. The held-out set (`evaluation/elliptic_certificate_cases.py`)

`HELD_OUT` holds 17 numbers.

* **Field primes of published curve standards:** `2^255 - 19` (RFC 7748),
  `2^448 - 2^224 - 1` (RFC 7748), P-192, P-224, P-256 and P-384 (FIPS 186-4),
  the secp256k1 prime `2^256 - 2^32 - 977` (SEC 2), and `2^130 - 5`
  (RFC 8439).
* **Other published primes:** `10^100 + 267`, `10^100 - 797`, `2^64 - 59`,
  `2^128 - 159`, and the repunit `R317` (OEIS A004023).
* **Composites by construction:** `10^100 + 1`, `R319`, `P-224 x (2^130 - 5)`
  and `(2^255 - 19)(2^64 - 59)`.

## 4. The marks

| mark | requirement |
|---|---|
| E1 | the Lean file holds its theorems and the instance, with no `sorry` |
| E2 | on `HELD_OUT`: no wrong verdict (Phase 140's certifier, Phase 141's certifier and the router); the router agrees with the certifier on every number; at least half of the primes Phase 140 refuses are certified |
| E3 | every answered chain holding an elliptic certificate verifies in a fresh `python3 -I`; every declared mutation is caught; every tampered certificate is rejected by both the step gate and the script |
| E4 | with `ELLIPTIC` on and off, Phase 139's held-out questions and Phase 140's first held-out set answer the same |
| E5 | the kernel-checked certificate is the one the run-time search produces |
| E6 | Phase 140's 304 non-interference numbers keep their verdict and certificate; the 30 stepwise composition cases answer as with `ELLIPTIC` off |

The tampered certificates change the last elliptic entry of a chain in seven
ways:

* a point off the curve;
* the cofactor `k + 1`;
* another curve;
* a smaller `q`;
* the singular curve `y^2 = x^3`;
* `q` left unproved;
* the chain cut before the entry.

## 5. The measurement

The command is `PYTHONPATH=. python3 -m glm_universal.tools elliptic-certificates`,
run from `overlay/`. Final run, with the per-number rows abbreviated:

```
E1 Lean           RequestProject/GLM/EllipticCertificate.lean: missing [], sorry False
E2 held out       17 numbers, 0 wrong; 6 of the 6 primes Phase 140 refused are now certified; the router agrees on 17 of 17
E3 column 3       6 of 6 chains verified; 24 of 24 mutants caught; tampered certificates caught by the gate 40 and the script 40 of 42
E4 control        0 of 35 Phase 139 and Phase 140 cases moved: []
E5 kernel         the 29-entry elliptic certificate for e01 is the Lean instance prime_2_255_sub_19: True
E6 interference   0 of 304 certified numbers changed; 0 of 30 stepwise cases moved
marks met         5 of 6
```

| number | Phase 140 | Phase 141 | certificate | entries (elliptic) | seconds, Phase 141 |
|---|---|---|---|---|---|
| `2^255 - 19` | refused | prime | elliptic | 29 (5) | 3.2 |
| `2^448 - 2^224 - 1` | refused | prime | elliptic | 34 (13) | 9.0 |
| `2^256 - 2^32 - 977` | refused | prime | elliptic | 31 (8) | 4.6 |
| `10^100 + 267` | refused | prime | elliptic | 30 (12) | 7.3 |
| `10^100 - 797` | refused | prime | elliptic | 25 (8) | 4.6 |
| `R317` | refused | prime | elliptic | 50 (34) | 135.6 |
| P-192, P-256, P-384 | prime | prime | mixed (N+1) | 32–63 | 1.3–4.0 |
| P-224, `2^130 - 5`, `2^64 - 59`, `2^128 - 159` | prime | prime | Pratt | 18–32 | 0.0 |
| the four composites | not prime | not prime | factor / Fermat | — | 0.0 |

The seconds are from one run and are not pinned. Phase 140's certifier took
2.4–20.5 s to refuse each of the six numbers.

### 5.1 Why E3 missed

The 2 accepted tampered certificates are both `cert-k`, on the two chains
whose last elliptic entry has `k = 1`. One of them is `2^256 - 2^32 - 977`.
There the search found the curve `y^2 = x^3 + 7`, which is secp256k1's own
curve and has prime order `q`. Raising `k` to 2 gives `Q = 2P`, still a point
of order `q`, so the entry is still valid and the checker is right to accept
it. The same holds on the other chain: with `k = 1` the point itself has the
prime order `q`, and since `q` is odd, twice the point has order `q` too.
The tampered certificate was declared invalid when it is not: the
mutation was mis-stated, not the checker. The mark is kept as missed, as
registered. A correct form of the mutation would choose a `k` that is a
multiple of `q`.

### 5.2 Seen outside the set (reported, not marked)

On random primes from the exploration generator, a certificate is found in
about:

| digits | seconds |
|---|---|
| 50 | 0.3 |
| 100 | 2 |
| 200 | 20 |
| 320 | 100 |

A 100-digit certificate is checked by the kernel in about 1.5 minutes. The
test prime `EXPLORED` (60 digits) is refused by Phase 140's certifier in
2.4 s and certified by the elliptic search; the GLM answers *is it prime* in
about 4 s.

### 5.3 Unchanged

* Phase 140's measurement is taken with `ELLIPTIC` off. Phase 139's held-out
  questions and Phase 140's first held-out set answer the same with it on
  (E4).
* The full end-to-end evaluation is reported in `MASTER_PLAN.md`, Phase 141.

## 6. What this round does not do

* **The cost of a refusal grew again.** A prime that no search reaches now
  spends four budgets before it is refused. Running the N+1 search ahead of
  Pocklington when `p + 1` is smooth, and trying the elliptic search earlier
  on large numbers, would cut most of that. Either change would alter which
  certificate some numbers get, so it needs the instances re-pinned.
* **The search is bounded by class number 10 and `|D| <= 3000`.** Primes for
  which no such discriminant gives a usable order within the budget are still
  refused. None of the held-out primes was.
* **The typed planner's primality frame** keeps its limit of 10^12. Giving it
  certificates changes which surface answers, so it needs a frozen-path
  comparison.
* **The `cert-k` mutation** should be restated so that it is invalid by
  construction (§5.1).

## 7. Files

* `overlay/glm_lean/RequestProject/GLM/EllipticCertificate.lean` — §2.
* `overlay/glm_universal/reasoning/elliptic_certificate.py` — the search.
* `overlay/glm_universal/reasoning/primality_certificate.py` — the checker,
  the `ELLIPTIC` control and the stage in `certify`.
* `overlay/glm_universal/reasoning/stepwise_script.py` — column 3's reader.
* `overlay/glm_universal/evaluation/elliptic_certificate_cases.py` — the
  held-out set and the measurement, printed by `tools elliptic-certificates`.
  `evaluation/pocklington_certificate_cases.py` — `flags` sets `ELLIPTIC` off.
* `overlay/glm_universal/tests/test_elliptic_certificate.py` — 13 tests.

### 7.1 What this round leaves

* The order of the searches: N+1 ahead of Pocklington when `p + 1` is smooth,
  and the elliptic search earlier on large numbers, with the instances
  re-pinned (§6).
* Certificates in the typed planner's primality frame, under a frozen-path
  comparison.
* The `cert-k` mutation, restated (§5.1).
