# Round 43 — the escalation-boundaries sketch, checked

Input: `../GLM_Escalation_Boundaries_Exploration.md`, the owner's concept sketch. It is left
unchanged.

Output:
* **`RequestProject/GLM/Escalation/MASTER_VIEW.md`** (in the Lean package): the revised master
  view. It checks the sketch statement by statement and rebuilds it on the GLM layer stack that
  actually ships (substrate parity, integer = parity + SI7, exact rational, Griess = exact + 2A
  axes, universal).
* **`RequestProject/GLM/Escalation/*.lean`**: the Lean checks (ledger rows C393–C399). See
  `RequestProject/GLM/Escalation/README.md`.
* **`escalation_checks.py`** (this folder): 15 executable checks, standard library only, about
  5 s. Each check names the Lean theorem that proves it in general. Two checks are script-only:
  8ℤ²⁴ ⊂ √8·Λ₂₄, and the sketch's Niemeier list has 22 entries with E₆⁴ missing.

```
python3 escalation_checks.py
```

## Main corrections to the sketch

1. The 2/4/8/144/256 table does not give the layer order. 8 divides 144, mod 256 does not refine
   mod 144, and no residue view can sit above an exact (identity) layer.
2. No floor-residue filter resolves 1/2 + 1/2. The sketch's mod-4 step has an arithmetic error
   (2 + 2 ≡ 0 ≡ ⌊4·1⌋ mod 4). So its graded escalation fails on its own example. Escalation works
   in the shipped GLM because the Rational layer is exact.
3. A fixed syndrome table makes the snap deterministic, not stable: no complete lattice decoder
   is continuous. At the GLM's Golay substrate, the ambiguity is a six-way tie on the 1,771
   weight-4 cosets; it is not a deep-hole type.
4. "Roll back on TCT failure" deadlocks when the target is fixed. Recommended instead: on
   rejection, escalate.

## Kept and proved

* The state is (carrier, layer), and the snap is the only place the layer changes.
* Escalation is the least resolving layer. It is correct and minimal, and it always succeeds when
  the top layer is lossless.
* **The arrow** (the owner's Observer/direction idea): if the snap only escalates, the layer is
  non-decreasing along every run and eventually constant.

## Rule 30

The parity law, `parity(next row) = parity(row) + #(adjacent 11 pairs)` mod 2, is proved for
every finite row. Rule 30 therefore does not descend to the substrate (parity) layer, and
escalating one rung is not enough either. P1, P2 and P3 remain open.
