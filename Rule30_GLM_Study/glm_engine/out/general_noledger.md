# General reasoning benchmarks — GLM Hypothesis Engine v18

Lean ledger gate: OFF (ablation)

Score against the ground truth fixed in advance (right / wrong / overclaim / abstain): **6 / 0 / 0 / 4** of 10.

| id | claim | class | status | arrow | backing |
|---|---|---|---|---|---|
| H01 | n² + n + 41 is prime for every n ≥ 0 | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | EXACT counterexample: n = 40: 1681 is not prime |
| H02 | n² + n + 41 is prime for every n < 40 | finite | **verified-exact** |  | EXACT whole range: all n in [0, 40) |
| H03 | every Fermat number 2^(2^n) + 1 is prime | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | EXACT counterexample: n = 5: 2^(2^5) + 1 = 4294967297 is divisible by 641 |
| H04 | distinct Fermat numbers are coprime | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 9 |
| H05 | an odd prime p is a sum of two squares exactly when p ≡ 1 (mod 4) | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 50000 |
| H06 | n points in general position on a circle cut the disc into 2^(n−1) regions | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | EXACT counterexample: n = 6: 31 regions, not 32 |
| H07 | in the Josephus problem with every second person removed, the survivor is 2(n − 2^⌊log₂ n⌋) + 1 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 4096 |
| H08 | every positive integer reaches 1 within 100 Collatz steps | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | EXACT counterexample: n = 27 needs 111 steps |
| H09 | every positive integer eventually reaches 1 under the Collatz map | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 100000 |
| H10 | gcd(n^17 + 9, (n + 1)^17 + 9) = 1 for every n ≥ 0 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 20000 |

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
Dialogue consistency: {'spoken': 6, 'spoken_without_backing_or_unspeakable': [], 'ok': True}

## Dialogue

> I hold 10 claims: 5 known (proved, verified, measured or refuted), 4 surviving every read, 1 not known.
> Verified exactly (finite claim, whole range) (1):
>   H02: n² + n + 41 is prime for every n < 40 — EXACT whole range: all n in [0, 40)
> Survive every read (universal claims: open beyond the largest read) (4):
>   H04: distinct Fermat numbers are coprime — escalation: survives every read, up to 9
>   H05: an odd prime p is a sum of two squares exactly when p ≡ 1 (mod 4) — escalation: survives every read, up to 50000
>   H07: in the Josephus problem with every second person removed, the survivor is 2(n − 2^⌊log₂ n⌋) + 1 — escalation: survives every read, up to 4096
>   H10: gcd(n^17 + 9, (n + 1)^17 + 9) = 1 for every n ≥ 0 — escalation: survives every read, up to 20000
> Open (no finite data decides these) (1):
>   H09: every positive integer eventually reaches 1 under the Collatz map — escalation: survives every read, up to 100000
> Refuted — do not say these (4):
>   H01: NOT 'n² + n + 41 is prime for every n ≥ 0' — EXACT counterexample: n = 40: 1681 is not prime
>   H03: NOT 'every Fermat number 2^(2^n) + 1 is prime' — EXACT counterexample: n = 5: 2^(2^5) + 1 = 4294967297 is divisible by 641
>   H06: NOT 'n points in general position on a circle cut the disc into 2^(n−1) regions' — EXACT counterexample: n = 6: 31 regions, not 32
>   H08: NOT 'every positive integer reaches 1 within 100 Collatz steps' — EXACT counterexample: n = 27 needs 111 steps
> Arrows that flipped (refuted only by reading higher):
>   H01: read substrate → integer → rational → griess → universal; flipped at universal
>   H03: read substrate → integer → rational → griess → universal; flipped at universal
>   H06: read substrate → integer → rational → griess; flipped at griess
>   H08: read substrate → integer → rational → griess; flipped at griess

## Wheel

Rings: {'knows': 5, 'thinks-true': 4, "doesn't-know": 1}

Needs:
* `proof:GEN.fermat.coprime` (proof): survives every read (to 9); data cannot prove a universal claim — blocks H04
* `proof:GEN.two.squares` (proof): survives every read (to 50000); data cannot prove a universal claim — blocks H05
* `proof:GEN.josephus` (proof): survives every read (to 4096); data cannot prove a universal claim — blocks H07
* `proof:GEN.collatz` (proof): open: no finite data decides it — blocks H09
* `proof:GEN.gcd.trap` (proof): survives every read (to 20000); data cannot prove a universal claim — blocks H10
