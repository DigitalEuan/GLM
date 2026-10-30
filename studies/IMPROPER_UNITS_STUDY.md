# Improper maps times a change of units in `tool frame` — the last improper refusal declared

## Tier 0 — the coarse read

**Question.** Can `tool frame` in 1+2 dimensions answer an improper Lorentz map times a change of units — the one improper case Phase 179 still refused — without a wrong answer and without changing any answer it already gave?

**Verdict.** Declaring the three improper components of the Lorentz group times a change of units as families, completed as the proper `lorentz_units` is, answered 238 of the 480 queries of four scaled improper families right where the Phase 179 family set answered none, with 0 wrong anywhere; each of the 238 answers names the component and the scale and recomposes; and the 717 answers of the Phase 179 family set are unchanged. `LorentzUnits.lean` proves the change of units divides out, that a positive scale keeps the signs the component is read from, that the eight families exhaust the maps keeping the Minkowski form up to a positive square, and that two demonstrations still never fix the component.

**Deciding figure.** 8 of 8 marks; scaled improper queries 238 right, 0 wrong of 480 (Phase 179's families: 0 right); at three demonstrations 118 of 120; Phase 179 answers changed 0 of 717; outside the families 0 wrong of 480.

**Recomputed by.** `glm_universal.reasoning.improper_units_study.improper_units_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 22 October 2026. Pre-registered 22 October 2026: the marks (§5) were
written into `reasoning/improper_units_study.py` and committed before the
first measurement. Measured 22 October 2026, once.*

## 0. What this document is

A study for Phase 181, taken from the To-Do list (`STATUS.md` §2.1 item 10,
*frame operators, the rest*), which named *an improper map times a change of
units (the one improper case still refused)*. Phase 179
([`IMPROPER_FRAME_STUDY.md`](IMPROPER_FRAME_STUDY.md)) declared the four
components of the Lorentz group as families and measured `improper_units` (a
Lorentz map times `py -> -py`, times a scale) as *outside*: 120 queries, all
refused.

## 1. What is proved

**The Lean file** (`glm_lean/RequestProject/GLM/LorentzUnits.lean`,
over `LorentzPlane.lean` and `LorentzImproper.lean`). A map `M` is conformal
with ratio `k` when `Mᵀ η M = k η`.

* `smul_lorentz_conformal` — a Lorentz map times `s` is conformal with ratio
  `s²`; `conformal_ratio` — the ratio is `M₀₀² − M₁₀² − M₂₀²`;
* `conformal_split` — **the change of units divides out**: conformal with
  ratio `s²`, `s ≠ 0`, means `s⁻¹ M` is a Lorentz map and `M = s · (s⁻¹ M)`;
* `det_smul_three`, `conformal_det_sign`, `conformal_time_sign` — with
  `s > 0`, `det M` has the sign of the Lorentz factor's determinant and `M₀₀`
  the sign of its time–time entry: the component is read from `M` itself;
* `conformal_eight` — **every map conformal with a positive square ratio is
  `s · B · P^a · T^b`** with `s > 0` and `B` proper orthochronous;
* `scaled_plane_partner` — `s · M` times the reflection in two inputs' plane
  agrees with `s · M` on both and has the opposite determinant: the span
  guard's reason holds for the new families;
* `two_parity_conformal` — twice the reflection `py -> -py`: ratio 4,
  determinant `−8`, time kept.

## 2. The mechanism

`reasoning/frame_plane.py`: three new families, `lorentz_parity_units`,
`lorentz_time_units`, `lorentz_pt_units`, beside `lorentz_units`
(`UNITS_OF` maps each to its component). Each is completed as
`lorentz_units` always was: the outputs' Minkowski Gram matrix must be `k`
times the inputs' with `k` a positive rational square `s²`; the outputs
divided by `s` are completed in the matching component; the fit is `s`
times that. An answer from a units family reports its scale and component,
split as `B · P^a · T^b` after dividing by `s`; when the scale is 1 the
component family's own reading is kept. `PHASE_179_FAMILIES` is the family
set before this round. The unfit refusal now lists *each also times units*.

`tool frame 1,0,0 -> 2,0,0 ; 2,1,0 -> 4,2,0 ; 2,0,1 -> 4,0,-2 ? 3,1,1`
answers `6,2,-2` from `lorentz_parity_units`, *2 times a Lorentz map, a change
of units (`GLM.LorentzUnits.conformal_split`)*, the reflection `py -> -py`
then the identity. With the first two pairs only it refuses, the query
outside the span of the inputs, and asks for `2,0,1`.

## 3. What is measured

Twenty task families, thirty queries each at one to four demonstrations
(2,400 queries), from the Phase 179 generator. *New, inside*:
`improper_units`, `reflect_units`, `time_units`, `pt_units`. *Regression*:
the twelve in-vocabulary families of Phase 179. *Outside*: `shear`,
`squeeze`, `swap`, and `anisotropic` (`E` doubled, momenta tripled). Solvers:
shipped (thirteen families), Phase 179 (ten), first fit.

## 4. Faculties

**Refusal** narrowed by a theorem: a case refused for want of a family is
answered once the family is declared and its completion proved sound, and
still refused where two demonstrations cannot fix it.

## 5. The marks

| mark | what is met |
|---|---|
| **U1** | shipped: 0 wrong answers on the sixteen in-vocabulary families, every demonstration count |
| **U2** | at three demonstrations, at least 95 % of the four new families' queries answered right |
| **U3** | outside: 0 wrong answers at three or more demonstrations |
| **U4** | when the Phase 179 family set answers, the shipped set gives the same answer, on every query |
| **U5** | every new-family answer at three or more demonstrations names the true component and scale and recomposes as `s · B · P^a · T^b` |
| **U6** | the first-fit control gives at least one wrong in-vocabulary answer |
| **L** | `LorentzUnits.lean` states its nine theorems with no `sorry` |
| **T** | the three-pair task above answers `6,2,-2` naming `lorentz_parity` and scale `2`, citing `conformal_split`; its two-pair version is refused asking about `2,0,1` |

## 6. What is not claimed

The scale must be a rational square root of the Gram ratio; an irrational
scale (ratio 2) is refused, as for `lorentz_units`. A negative scale is not a
separate family: `−1` is time reversal times the rotation by a half turn, so
a negative scale times a Lorentz map is a positive scale times a Lorentz map
of another component.
3+1 dimensions are untouched.

## 7. What came out

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **U1** | new 238 right, 0 wrong, 242 refused of 480; regression 716 right, 0 wrong, 724 refused of 1,440 | yes |
| **U2** | 118 of 120 at three demonstrations (120 of 120 at four) | yes |
| **U3** | outside: 1 right, 0 wrong, 479 refused of 480 | yes |
| **U4** | Phase 179 set answered 717; changed 0 | yes |
| **U5** | 238 of 238 named, scaled and recomposed | yes |
| **U6** | first fit: 91 wrong on the new families, 176 on the regression set | yes |
| **L** | 9 of 9, 0 `sorry`; `AxiomAuditAll` passes | yes |
| **T** | `6,2,-2`, `lorentz_parity`, scale `2`; refused at two pairs, asking for `2,0,1` | yes |

By family (shipped): `improper_units` 60 right of 120, `reflect_units` 60,
`time_units` 58, `pt_units` 60, each 0 wrong; the refusals are the one- and
two-demonstration queries (and two at three).

### 7.2 The earlier studies, re-taken

`frame_plane.py` is a source of the Phase 178 and 179 measurements, so both
were re-taken. Phase 178's `frame-plane`: 8 of 8, unchanged figures. Phase
179's `improper-frame`: 8 of 8; its outside family `improper_units` is now
answered, 60 right and 0 wrong of 120, so its outside line reads 60 right,
0 wrong, 420 refused of 480 where it read 0 right; every inside figure is
unchanged.

### 7.3 What this answers, and what is left

It answers the first remaining line of `STATUS.md` §2.1 item 10 (*an improper
map times a change of units*). Left: holding `tool frame`'s ask open in the
conversation as Phase 173 does; 3+1 dimensions; the TAX refractive-index
test and the κ decisions.

## In one paragraph

`tool frame` refused an improper Lorentz map times a change of units, the one
improper case Phase 179 left. Declaring the three improper components times
units as families, completed exactly as the proper `lorentz_units` is,
answered 238 of 480 scaled improper queries right where the Phase 179 family
set answered none, 0 wrong anywhere, every answer naming its component and
scale, and none of the 717 Phase 179 answers changed. `LorentzUnits.lean`
proves the change of units divides out, the component is read from the
signs a positive scale keeps, the eight families exhaust the maps keeping the
form up to a positive square, and two demonstrations still never fix the
component. 8 of 8 marks.
