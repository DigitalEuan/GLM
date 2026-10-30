# Improper maps in `tool frame` — reflections, time reversal, and the four components of the Lorentz group

## Tier 0 — the coarse read

**Question.** Can `tool frame` in 1+2 dimensions answer a reflection, a time reversal or their compositions with Lorentz maps, which Phase 178 refused as outside its families, without a single wrong answer and without changing any answer it already gave?

**Verdict.** Declaring the three improper components of the Lorentz group as families, beside the proper orthochronous one, and the spatial reflection beside the rotation, turned 361 of the 720 improper queries into right answers where Phase 178 answered 3, with 0 wrong; every improper answer names its component and splits exactly into a proper map after a reflection or time reversal; and on all 1,920 queries the 361 answers the Phase 178 family set gives are unchanged. `LorentzImproper.lean` proves the four components exhaust the group and that two demonstrations never fix the component (any Lorentz map has a partner in another component agreeing with it on both), so the span guard's refusals stay.

**Deciding figure.** 8 of 8 marks; improper queries 361 right, 0 wrong of 720 (Phase 178: 3 right); at three demonstrations 179 of 180; Phase 178 answers changed 0 of 361; outside the families 0 wrong of 480.

**Recomputed by.** `glm_universal.reasoning.improper_frame_study.improper_frame_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 22 October 2026. Pre-registered 22 October 2026: the marks (§5) were
written into `reasoning/improper_frame_study.py` before the first
measurement. Measured 22 October 2026, once.*

## 0. What this document is

A study for Phase 179, taken from the To-Do list (`STATUS.md` §2.1 item 10,
*frame operators, the rest*), which asked for *improper maps (reflections,
time reversal) as declared families rather than refusals*. Phase 178
([`COLOUR_INDUCTION_STUDY.md`](COLOUR_INDUCTION_STUDY.md), part B) made
`tool frame` work on states `(E, px, py)` with six families — identity,
units, rotation, pure boost, proper orthochronous Lorentz, Lorentz times units
— and measured the reflection `py -> -py` and time reversal `E -> -E` as
*outside* families: refused, every one of 240 queries.

## 1. What is proved

`glm_lean/RequestProject/GLM/LorentzImproper.lean`, over `ℚ`, with the
definitions of `LorentzPlane.lean`:

* `parity_lorentz`, `det_parity`, `timeRev_lorentz`, `det_timeRev`,
  `timeRev_flips_time` — the reflection `py -> -py` and time reversal keep
  the Minkowski form and have determinant `−1`; time reversal sends the rest
  state into the past;
* `reflect_eq`, `reflect_lorentz`, `det_reflect` — the reflection of the
  spatial plane in a line, `rot c s * parity`, is a Lorentz map of
  determinant `−1`;
* `det_eta`, `lorentz_det_sq` — every Lorentz map has determinant `±1`;
  `lorentz_time_sq`, `lorentz_time_ne_zero` — its time–time entry satisfies
  `A₀₀² − A₁₀² − A₂₀² = 1`, so it is never `0`: a Lorentz map keeps or
  reverses the direction of time;
* `lorentz_four_components` — every Lorentz map is a proper orthochronous
  one times `1`, `parity`, `timeRev` or `parity * timeRev`. The four
  families exhaust the group, and the split the tool prints is always there;
* `householder_lorentz`, `householder_det`, `householder_fixes`,
  `householder_flips` — the reflection in the Minkowski-orthogonal complement
  of a non-null `n`, `x ↦ x − 2⟨n,x⟩n/⟨n,n⟩`, is a Lorentz map of
  determinant `−1` that fixes every state orthogonal to `n` and reverses `n`;
* `plane_partner` — **two demonstrations never fix the component**: for any
  Lorentz map `M` and any two inputs whose Minkowski cross product is not
  null, `M` times the reflection in their plane is a Lorentz map of the
  opposite determinant that sends both inputs where `M` does and differs
  from `M` off their plane. Phase 178 added the span guard after a
  measurement and argued for it; this is the argument as a theorem;
* `reflection_agrees_on_plane` — a concrete instance: the identity and
  `parity` agree on `(1,0,0)` and `(2,1,0)` and disagree on `(2,0,1)`.

19 theorems, 0 `sorry`; the whole-development axiom audit
(`AxiomAuditAll.lean`) imports the file and passes on the standard axioms.

## 2. The mechanism

`reasoning/frame_plane.py` gains four families, after the six of Phase 178
so the first-fit control's order is unchanged:

* `reflection` — `E` kept, the spatial Gram matrix kept, the spatial plane
  reflected in a line; one pair with a spatial part fixes it (the improper
  counterpart of `rotation`);
* `lorentz_parity` (determinant `−1`, time kept), `lorentz_time`
  (determinant `−1`, time reversed), `lorentz_pt` (determinant `1`, time
  reversed) — with `lorentz`, the four components (`COMPONENTS`).

Each component is completed from the pairs as `lorentz` was: three
independent inputs fix the linear map; two fix it too, because a Lorentz map
`M` sends the Minkowski cross product `n` of two inputs to `det(M)` times
that of their outputs, so the third column is `±fn` by component. A
component whose completion is not in it is ruled out; an undetermined one is
ruled out when a future-pointing timelike input goes the wrong way in time.
Everything else — the Gram invariant layer, leave-one-out testing, the
agreement gate, the span guard — is Phase 178's, unchanged.

An answer from an improper component is split by `improper_split` as
`B · P^a · T^b` with `B` proper orthochronous, and `B` by Wigner, so the
tool says, for example, *time reversal E -> -E, then the reflection py ->
-py, then the proper map taking rest to … with rotation (15/17, −8/17)*. A
refusal at rank 2 where a proper and an improper family both survive now says
so and cites `reflection_agrees_on_plane`.

`solve` takes the family set as a parameter; `PHASE_178_FAMILIES` is the set
before this round. On all 1,920 queries of §3 the restricted solver gives the
same verdict and answer as the Phase 178 file as committed (a hand check
against the file from version control, 1,920 of 1,920; the mark I4 then
compares the shipped set with the restricted one).

## 3. What is measured

Sixteen families, thirty queries each at one, two, three and four
demonstrations (1,920 queries), drawn by the Phase 178 study's generator so
the two are comparable: six **improper** (`reflect`, `reflect_line`,
`time_reverse`, `lorentz_parity`, `lorentz_time`, `lorentz_pt`), six
**proper** kept as a regression set (`identity`, `rotation`, `boost_x`,
`lorentz`, `thomas`, `lorentz_units`), and four **outside**: `shear`,
`squeeze` (determinant 1, not Lorentz), `improper_units` (an improper map
times a change of units, which no family declares) and `swap` (`E` and `px`
exchanged). Three solvers: shipped, the Phase 178 family set, first fit.

## 4. Faculties

Inference of an operator from examples, with the invariant reading and the
gate; reading the result back in words (component and split); the theorem
behind a refusal named in the refusal.

## 5. The marks

Declared before the first measurement (`improper_frame_study.py`):

* **I1** shipped: 0 wrong on the twelve in-vocabulary families, every
  demonstration count;
* **I2** at three demonstrations, at least 95 % of the improper queries right;
* **I3** outside: 0 wrong at three or more demonstrations;
* **I4** nothing the Phase 178 family set answers changes;
* **I5** every improper answer at three or more demonstrations names the true
  component and its split recomposes, `B` proper orthochronous;
* **I6** the first-fit control gives at least one wrong in-vocabulary answer;
* **L** `LorentzImproper.lean` states its theorems with no `sorry`;
* **T** `tool frame` answers the three-pair reflection task with `3,1,-1`
  naming `lorentz_parity`, and refuses the two-pair version citing
  `reflection_agrees_on_plane` and asking about `2,0,1`.

## 6. What is not claimed

Only 1+2 dimensions. A change of units times an improper map is not a family
(`improper_units` is refused, 120 of 120). The families are the Lorentz group
and its scalings; a shear, a squeeze or a swap is refused, never fitted.
The improper families do not widen what one or two demonstrations can settle:
at rank 2 a query off the inputs' plane is refused exactly as before, and
`plane_partner` shows a refusal is needed there whenever the inputs' cross
product is not null (a null one, a lightlike plane, is not covered by the
theorem; the tool refuses it as undetermined).

## 7. What came out

### 7.1 The marks

8 of 8 at the first take.

| solver | improper right / wrong / refused | proper right / wrong / refused | outside right / wrong / refused |
|---|---|---|---|
| shipped | 361 / 0 / 359 | 358 / 0 / 362 | 0 / 0 / 480 |
| Phase 178 families | 3 / 0 / 717 | 358 / 0 / 362 | 0 / 0 / 480 |
| first fit | 430 / 170 / 120 | 600 / 1 / 119 | 2 / 34 / 444 |

By demonstrations, improper queries, shipped: 0 of 180 right at one, 2 of
180 at two, 179 of 180 at three, 180 of 180 at four, 0 wrong anywhere. Of
the 359 improper answers at three or more demonstrations, 359 name the true
component and 359 splits recompose. The Phase 178 family set answered 361 of
the 1,920 queries; the widening changed 0 of them. The 3 improper queries
Phase 178 already answered are rank-2 queries inside the span of their
inputs, where linearity alone forces the output.

One change after the first take, disclosed: the mark **T** first required
the rank-2 refusal to cite `reflection_agrees_on_plane`; when the general
theorem `plane_partner` was proved later the same day, the refusal was made
to cite it and the mark to ask for that name instead. Nothing else in the
mark, the solver's verdicts or the figures moved; the measurement was
re-taken (§7.3).

### 7.2 The Phase 178 study, re-taken

`tools frame-plane` re-taken over the widened tool: still 8 of 8, inside its
families unchanged (536 right, 0 wrong of 1,080), and outside its families
119 right, 0 wrong, 241 refused of 360 where Phase 178 had 0 right — its
`reflect` and `time_reverse` families are inside now; `shear` is still
refused, every query.

### 7.3 The re-take

Re-taken after `plane_partner` was proved and cited: 8 of 8 again, every
figure of §7.1 the same (the solver is deterministic and its verdicts did not
move; only the refusal's wording and the Lean theorem list changed). The
other stored measurements that digest `runtime/toolbox.py` or
`reasoning/frame_plane.py` were re-taken in the same close with their marks
as before: `tool-machine` 8 of 9 (F1 missed as since Phase 163, F1′ met),
`colour-induction` 8 of 12, `budget-reading` 8 of 8, `nearest-address` 7
of 7, and `address-read` re-written over the same sources.

### 7.4 What this answers, and what is left

It answers the first half of `STATUS.md` §2.1 item 10's *improper maps … as
declared families rather than refusals*. Left: an improper map times a change
of units as a family (it is the one improper case still refused); 3+1
dimensions, where the same four components hold and the split is the same;
holding `tool frame`'s ask open in the conversation as Phase 173 does; and
the TAX refractive-index test and the κ decisions of item 10, untouched.

## In one paragraph

Declaring the three improper components of the Lorentz group as families,
beside the proper orthochronous one, and the spatial reflection beside the
rotation, turned 361 of the 720 improper queries into right answers where
Phase 178 answered 3, with 0 wrong; every improper answer names its component
and splits exactly into a proper map after a reflection or time reversal; and
on all 1,920 queries the 361 answers the Phase 178 family set gives are
unchanged. `LorentzImproper.lean` proves the four components exhaust the
group and that two demonstrations never fix the component (any Lorentz map
has a partner in another component agreeing with it on both), so the span
guard's refusals stay. 8 of 8 marks; at three
demonstrations 179 of 180; outside the families 0 wrong of 480.
