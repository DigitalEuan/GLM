# GLM queries on Rule-30-relevant carriers

All outputs verbatim from `python3 GLM.py --plan -q '...' -f markdown`, run on the live DigitalEuan/GLM repository (clone at `/home/z/my-project/glm_repo`, version 5.37 per README).

The `--plan` flag selects the typed planner surface, which routes through `glm_universal.runtime.parser` and `glm_universal.runtime.session` only. The default multi-surface router (K1, Phase 89) has an `ImportError` on the respell/sinter fallback that triggers only on a refusal; using `--plan` avoids that path entirely.

## Query: `describe golay_codeword_0`

_Rationale._ The all-ones Golay-24 codeword; the GLM places it at the origin of the Leech lattice and notes it is not a 2A axis of the Monster.

```markdown
# Three Column Thinking

**Query.** `describe golay_codeword_0`  
**Kind.** `describe`  
**Answer.** `golay_codeword_0 (mathematics): depth 1, plane-0 mask 0xffffff, |v|^2 = 0/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | golay_codeword_0 is a carrier of the mathematics register. | golay_codeword_0 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 1 at offset 1; nothing is hardcoded. | depth = 1, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xffffff of weight 24; it is a Golay codeword, and the carrier is integral. | plane0 = 0xffffff, wt = 24, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 0/1; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(golay_codeword_0): d^2 = 0/1, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 0/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe golay_codeword_1`

_Rationale._ The weight-1 'basis' Golay codeword; useful as a window template against the Rule 30 center column.

```markdown
# Three Column Thinking

**Query.** `describe golay_codeword_1`  
**Kind.** `describe`  
**Answer.** `golay_codeword_1 (mathematics): depth 2, plane-0 mask 0xffe001, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | golay_codeword_1 is a carrier of the mathematics register. | golay_codeword_1 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xffe001 of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0xffe001, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(golay_codeword_1): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe golay_codeword_4095`

_Rationale._ The all-zeros Golay-24 codeword, the additive identity.

```markdown
# Three Column Thinking

**Query.** `describe golay_codeword_4095`  
**Kind.** `describe`  
**Answer.** `golay_codeword_4095 (mathematics): depth 2, plane-0 mask 0x000000, |v|^2 = 3/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | golay_codeword_4095 is a carrier of the mathematics register. | golay_codeword_4095 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x000000 of weight 0; it is a Golay codeword, and the carrier is integral. | plane0 = 0x000000, wt = 0, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 2/1; the lattice point has norm^2 = 48/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(golay_codeword_4095): d^2 = 2/1, \|\|lambda\|\|^2 = 48/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe leech_minimal_root`

_Rationale._ The shortest nonzero vector in the Leech lattice Lambda_24. A 24-dim carrier whose projection is computed exactly in Fraction arithmetic.

```markdown
# Three Column Thinking

**Query.** `describe leech_minimal_root`  
**Kind.** `describe`  
**Answer.** `leech_minimal_root (mathematics): depth 4, plane-0 mask 0x000000, |v|^2 = 4/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | leech_minimal_root is a carrier of the mathematics register. | leech_minimal_root in Q^24, layout = ['root00', 'root01', 'root02', 'root03', 'root04', 'root05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 4 at offset 4; nothing is hardcoded. | depth = 4, offset = 4, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x000000 of weight 0; it is a Golay codeword, and the carrier is integral. | plane0 = 0x000000, wt = 0, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 0/1; the lattice point has norm^2 = 32/1 and IS a 2A axis of the Monster. | nearest_lattice_point(leech_minimal_root): d^2 = 0/1, \|\|lambda\|\|^2 = 32/1, is_2a_axis = True |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 4/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe axis_root_e0`

_Rationale._ The unit basis vector e_0 in Q^24; a reflection root in the Co3 stabiliser.

```markdown
# Three Column Thinking

**Query.** `describe axis_root_e0`  
**Kind.** `describe`  
**Answer.** `axis_root_e0 (mathematics): depth 2, plane-0 mask 0xfffffe, |v|^2 = 1/8`  

| # | Step | Mathematics |
|---|---|---|
| 1 | axis_root_e0 is a carrier of the mathematics register. | axis_root_e0 in Q^24, layout = ['root00', 'root01', 'root02', 'root03', 'root04', 'root05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xfffffe of weight 23; it is not a Golay codeword, and the carrier is integral. | plane0 = 0xfffffe, wt = 23, golay = False |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 1/8; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(axis_root_e0): d^2 = 1/8, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 1/8 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe rational_root_thirds`

_Rationale._ A 24-dim root filled with 1/3 in every coordinate; the GLM computes its Griess norm <v,v> = (1/8) sum v_i^2 = 24/8 / 9 = ... exactly.

```markdown
# Three Column Thinking

**Query.** `describe rational_root_thirds`  
**Kind.** `describe`  
**Answer.** `rational_root_thirds (mathematics): depth 2, plane-0 mask 0x000000, |v|^2 = 1/3`  

| # | Step | Mathematics |
|---|---|---|
| 1 | rational_root_thirds is a carrier of the mathematics register. | rational_root_thirds in Q^24, layout = ['root00', 'root01', 'root02', 'root03', 'root04', 'root05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 3 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x000000 of weight 0; it is a Golay codeword, and the carrier is not integral. | plane0 = 0x000000, wt = 0, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 1/3; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(rational_root_thirds): d^2 = 1/3, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 1/3 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe hexacode_word_0`

_Rationale._ The first hexacode word over GF(4); the hexacode is the GF(4) construction spine of the Golay code and MOG.

```markdown
# Three Column Thinking

**Query.** `describe hexacode_word_0`  
**Kind.** `describe`  
**Answer.** `hexacode_word_0 (mathematics): depth 1, plane-0 mask 0xffffff, |v|^2 = 0/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | hexacode_word_0 is a carrier of the mathematics register. | hexacode_word_0 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 1 at offset 1; nothing is hardcoded. | depth = 1, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xffffff of weight 24; it is a Golay codeword, and the carrier is integral. | plane0 = 0xffffff, wt = 24, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 0/1; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(hexacode_word_0): d^2 = 0/1, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 0/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `verify force = mass * acceleration`

_Rationale._ A sanity-check dimensional verification. The GLM should confirm Newton's second law is dimensionally consistent.

```markdown
# Three Column Thinking

**Query.** `verify force = mass * acceleration`  
**Kind.** `verify`  
**Answer.** `force = mass * acceleration holds under scalar semantics`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Read both sides as expressions over the physics register and give each one a dimensional sense. | lhs = force rhs = mass * acceleration |
| 2 | The left side has EXT10 dimension 'L M T^-2'; the right side has 'L M T^-2'. | dim(lhs) = L M T^-2 dim(rhs) = L M T^-2 |
| 3 | Tensor rank is 1 on the left and 1 on the right. | rank(lhs) = 1, rank(rhs) = 1 |
| 4 | Under 'scalar' semantics the comparison uses 18 of the 24 relation coordinates. | compared coordinates = ['ext10.L', 'ext10.M', 'ext10.T', 'ext10.I', 'ext10.H', 'ext10.N', 'ext10.J', 'ext10.A', 'ext10.S', 'ext10.B', 'si7.L', 'si7.M', 'si7.T', 'si7.I', 'si7.H', 'si7.N', 'si7.J', 'scale'] |
| 5 | Both senses are lifted to a 2-adic digit stack of depth 3 at offset 2 and compared plane by plane. | depth = 3, offset = 2 planes compared = 0..2 |
| 6 | Every digit plane agrees, so the relation holds exactly under these semantics. | for all planes p: lhs_p - rhs_p = 0 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `puzzle rule 30 center column periodicity`

_Rationale._ Direct probe: does the GLM know about Rule 30? Expected behaviour: the parser returns 'unknown' or 'refusal' because Rule 30 is not in the GLM's registers. This is honest evidence the GLM does not have Rule 30 as a carrier.

```markdown
QUERY   puzzle rule 30 center column periodicity
UNSOLVED        task: unknown task 'rule 30 center column periodicity'
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `describe rule 30`

_Rationale._ Direct probe: does the GLM have 'rule 30' as a carrier?

```markdown
QUERY   describe rule 30
UNSOLVED        resolve: 'rule 30' names no carrier in any enabled domain; did you mean ['al2o3', 'alp_ct', 'alp_i', 'alp_o', 'c_0']?
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe center column`

_Rationale._ Direct probe: does the GLM have 'center column' as a carrier?

```markdown
QUERY   describe center column
UNSOLVED        resolve: 'center column' names no carrier in any enabled domain
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `approximate sqrt(2)`

_Rationale._ The GLM's `real` query kind: an irrational number treated as a process, with a precise 2-adic / Stern-Brocot digit-stack computation underneath. Useful for Problem 2's comparison to digits of pi.

```markdown
# Three Column Thinking

**Query.** `approximate sqrt(2)`  
**Kind.** `real`  
**Answer.** `sqrt(2) = 1.41421356237309504880 (to 20 places); no carrier holds it`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  sqrt(2) is not rational, so no carrier holds it and no level of the tower ever will.  What the machine holds is the process that converges to it. | rational: False |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | sqrt(2) = 1.41421356237309504880 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 1, 1, 5/4, 11/8, 11/8, 45/32; exposed at 0->2, 1->2, 2->3, 3->5, 4->5 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 53/128, \|average - target\| = 348326116956449/2305843009213693952 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `irrational pi`

_Rationale._ Same `real` query kind, for pi. Useful for Problem 2's comparison between the Rule 30 center column and digits of pi (Wolfram's analogy).

```markdown
# Three Column Thinking

**Query.** `irrational pi`  
**Kind.** `real`  
**Answer.** `pi = 3.14159265358979323846 (to 20 places); no carrier holds it`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  pi is not rational, so no carrier holds it and no level of the tower ever will.  What the machine holds is the process that converges to it. | rational: False |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | pi = 3.14159265358979323846 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 3, 3, 3, 25/8, 25/8, 25/8; exposed at 0->3, 1->3, 2->3, 3->6, 4->6 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 9/64, \|average - target\| = 4126705813298350745217514646167138043578859/4264651996155066979770210742950439453125000000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare sqrt(2) bigger than 1.414`

_Rationale._ The `compare` query kind: order two real values exactly. Decidable when the inequality is strict.

```markdown
QUERY   compare sqrt(2) bigger than 1.414
UNSOLVED        parse_real: 'compare sqrt(2)' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare sqrt(2)' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `spatial mog grid`

_Rationale._ The `spatial` query kind: the GLM's Miracle Octad Generator grid, the GF(4) construction of the Golay-24 code.

```markdown
QUERY   spatial mog grid
UNSOLVED        resolve: 'mog grid' names no carrier in any enabled domain, and does not parse as a chemical formula either
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---
