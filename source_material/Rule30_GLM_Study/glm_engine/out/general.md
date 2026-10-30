# General reasoning benchmarks — GLM Hypothesis Engine v18

Lean ledger gate: on

Score against the ground truth fixed in advance (right / wrong / overclaim / abstain): **10 / 0 / 0 / 0** of 10.

| id | claim | class | status | arrow | backing |
|---|---|---|---|---|---|
| H01 | n² + n + 41 is prime for every n ≥ 0 | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | FORMAL Benchmarks.euler_not_prime_40 |
| H02 | n² + n + 41 is prime for every n < 40 | finite | **proved** |  | FORMAL Benchmarks.euler_prime_below_40 |
| H03 | every Fermat number 2^(2^n) + 1 is prime | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | FORMAL Benchmarks.fermat_five_not_prime |
| H04 | distinct Fermat numbers are coprime | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL Benchmarks.fermat_pairwise_coprime |
| H05 | an odd prime p is a sum of two squares exactly when p ≡ 1 (mod 4) | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL Benchmarks.two_squares_law |
| H06 | n points in general position on a circle cut the disc into 2^(n−1) regions | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | FORMAL Benchmarks.moser_split |
| H07 | in the Josephus problem with every second person removed, the survivor is 2(n − 2^⌊log₂ n⌋) + 1 | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL Benchmarks.josephus_closed_form |
| H08 | every positive integer reaches 1 within 100 Collatz steps | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | FORMAL Benchmarks.collatz_27_slow |
| H09 | every positive integer eventually reaches 1 under the Collatz map | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 100000 |
| H10 | gcd(n^17 + 9, (n + 1)^17 + 9) = 1 for every n ≥ 0 | Pi1 | **refuted-by-ledger** | converging (substrate → integer → rational → griess → universal) | EXACT the cited witness n = 8424432925592889329288197322308900672459420460792433 is recomputed here: gcd = 8936582237915716659950962253358945635793453256935559  |

## Layer reads (five nested scales) and arrows

* H01: substrate=10:T, integer=20:T, rational=30:T, griess=40:T, universal=100:F — flipped at universal
* H03: substrate=1:T, integer=2:T, rational=3:T, griess=4:T, universal=6:F — flipped at universal
* H04: substrate=2:T, integer=3:T, rational=4:T, griess=6:T, universal=9:T — converging
* H05: substrate=100:T, integer=1000:T, rational=5000:T, griess=20000:T, universal=50000:T — converging
* H06: substrate=3:T, integer=4:T, rational=5:T, griess=6:F, universal=10:- — flipped at griess
* H07: substrate=16:T, integer=64:T, rational=256:T, griess=1024:T, universal=4096:T — converging
* H08: substrate=10:T, integer=20:T, rational=26:T, griess=50:F, universal=100:- — flipped at griess
* H09: substrate=100:T, integer=1000:T, rational=10000:T, griess=30000:T, universal=100000:T — converging
* H10: substrate=100:T, integer=1000:T, rational=3000:T, griess=10000:T, universal=20000:T — converging

## Rollback

* none

Conflicts (gate vs ledger, layer shape): none
Dialogue consistency: {'spoken': 5, 'spoken_without_backing_or_unspeakable': [], 'ok': True}

## Dialogue

> I hold 10 claims: 9 known (proved, verified, measured or refuted), 0 surviving every read, 1 not known.
> Proved in Lean (4):
>   H02: n² + n + 41 is prime for every n < 40 — FORMAL Benchmarks.euler_prime_below_40
>   H04: distinct Fermat numbers are coprime — FORMAL Benchmarks.fermat_pairwise_coprime
>   H05: an odd prime p is a sum of two squares exactly when p ≡ 1 (mod 4) — FORMAL Benchmarks.two_squares_law
>   H07: in the Josephus problem with every second person removed, the survivor is 2(n − 2^⌊log₂ n⌋) + 1 — FORMAL Benchmarks.josephus_closed_form
> Open (no finite data decides these) (1):
>   H09: every positive integer eventually reaches 1 under the Collatz map — escalation: survives every read, up to 100000
> Refuted — do not say these (5):
>   H01: NOT 'n² + n + 41 is prime for every n ≥ 0' — FORMAL Benchmarks.euler_not_prime_40
>   H03: NOT 'every Fermat number 2^(2^n) + 1 is prime' — FORMAL Benchmarks.fermat_five_not_prime
>   H06: NOT 'n points in general position on a circle cut the disc into 2^(n−1) regions' — FORMAL Benchmarks.moser_split
>   H08: NOT 'every positive integer reaches 1 within 100 Collatz steps' — FORMAL Benchmarks.collatz_27_slow
>   H10: NOT 'gcd(n^17 + 9, (n + 1)^17 + 9) = 1 for every n ≥ 0' — EXACT the cited witness n = 8424432925592889329288197322308900672459420460792433 is recomputed here: gcd = 8936582237915716659950962253358945635793453256935559 ≠ 1
> Arrows that flipped (refuted only by reading higher):
>   H01: read substrate → integer → rational → griess → universal; flipped at universal
>   H03: read substrate → integer → rational → griess → universal; flipped at universal
>   H06: read substrate → integer → rational → griess; flipped at griess
>   H08: read substrate → integer → rational → griess; flipped at griess

## Wheel

Rings: {'knows': 9, 'thinks-true': 0, "doesn't-know": 1}

Needs:
* `proof:GEN.collatz` (proof): open: no finite data decides it — blocks H09
