# GLM queries (round 3): the GLM engaged

All outputs verbatim from `python3 GLM.py --plan -q '...' -f markdown`,
run on the live DigitalEuan/GLM repository (clone at
`/home/z/my-project/glm_repo`, version 5.37 per README,
*with the mathematics register extended to include 8 Rule 30
Golay hit carriers* named `r30_golay_hit_<window_idx>`.

Round 2 (`data/glm_outputs_v2.md`) discovered two syntax issues:
the `compare` query kind does not take a `compare` prefix (the
verb `less than` is itself the infix operator), and the `verify`
query kind is for dimensional consistency, not integer arithmetic.
Round 3 fixes both and adds the 8 Rule 30 hit carriers as named
first-class objects in the GLM's mathematics register.

The GLM now engaged substantively: the dyadic tower of the
empirical Rule 30 frequency, the exact rational separation level
for each inequality, the three-column trace on each Rule 30 hit
codeword, and the Lorentzian Pythagorean identity 1^2 + 2^2 + ...
+ 24^2 = 70^2.

## Query: `describe r30_golay_hit_4678`

_Rationale._ Codeword index 3257, weight 12, mask 0x346733. The GLM reports the nearest Leech lattice point at squared distance 3/2.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_4678`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_4678 (mathematics): depth 2, plane-0 mask 0x346733, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_4678 is a carrier of the mathematics register. | r30_golay_hit_4678 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x346733 of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0x346733, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_4678): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_6321`

_Rationale._ Codeword index 3818. The GLM gives the full carrier trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_6321`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_6321 (mathematics): depth 2, plane-0 mask 0x115423, |v|^2 = 2/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_6321 is a carrier of the mathematics register. | r30_golay_hit_6321 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x115423 of weight 8; it is a Golay codeword, and the carrier is integral. | plane0 = 0x115423, wt = 8, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 2/1; the lattice point has norm^2 = 32/1 and IS a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_6321): d^2 = 2/1, \|\|lambda\|\|^2 = 32/1, is_2a_axis = True |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 2/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_8284`

_Rationale._ Codeword index 172, the lowest-index hit. The GLM trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_8284`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_8284 (mathematics): depth 2, plane-0 mask 0xf53d4f, |v|^2 = 1/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_8284 is a carrier of the mathematics register. | r30_golay_hit_8284 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xf53d4f of weight 16; it is a Golay codeword, and the carrier is integral. | plane0 = 0xf53d4f, wt = 16, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 1/1; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_8284): d^2 = 1/1, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 1/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_9272`

_Rationale._ Codeword index 1422. The GLM trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_9272`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_9272 (mathematics): depth 2, plane-0 mask 0xa714cd, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_9272 is a carrier of the mathematics register. | r30_golay_hit_9272 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xa714cd of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0xa714cd, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_9272): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_13341`

_Rationale._ Codeword index 1079. The GLM trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_13341`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_13341 (mathematics): depth 2, plane-0 mask 0xbc825e, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_13341 is a carrier of the mathematics register. | r30_golay_hit_13341 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xbc825e of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0xbc825e, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_13341): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_16816`

_Rationale._ Codeword index 2862. The GLM trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_16816`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_16816 (mathematics): depth 2, plane-0 mask 0x4d1bd8, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_16816 is a carrier of the mathematics register. | r30_golay_hit_16816 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x4d1bd8 of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0x4d1bd8, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_16816): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_28718`

_Rationale._ Codeword index 3, a low-index (high-symmetry) Golay codeword with weight 16. The GLM reports the nearest Leech point at squared distance 1/1 -- anomalously close for a 24-bit binary vector.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_28718`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_28718 (mathematics): depth 2, plane-0 mask 0xffc476, |v|^2 = 1/1`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_28718 is a carrier of the mathematics register. | r30_golay_hit_28718 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0xffc476 of weight 16; it is a Golay codeword, and the carrier is integral. | plane0 = 0xffc476, wt = 16, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 1/1; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_28718): d^2 = 1/1, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 1/1 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe r30_golay_hit_32240`

_Rationale._ Codeword index 2960. The GLM trace.

```markdown
# Three Column Thinking

**Query.** `describe r30_golay_hit_32240`  
**Kind.** `describe`  
**Answer.** `r30_golay_hit_32240 (mathematics): depth 2, plane-0 mask 0x46fb90, |v|^2 = 3/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | r30_golay_hit_32240 is a carrier of the mathematics register. | r30_golay_hit_32240 in Q^24, layout = ['symbol00', 'symbol01', 'symbol02', 'symbol03', 'symbol04', 'symbol05'] ... |
| 2 | Fitting a 2-adic digit stack to this carrier's actual range needs depth 2 at offset 1; nothing is hardcoded. | depth = 2, offset = 1, denominator = 1 |
| 3 | The carrier is reconstructed exactly from its digit stack, so the stack is a lossless encoding of it. | class_stack_rebuild(class_stack(v)) == v is True |
| 4 | Digit plane 0 is the 24-bit mask 0x46fb90 of weight 12; it is a Golay codeword, and the carrier is integral. | plane0 = 0x46fb90, wt = 12, golay = True |
| 5 | The nearest point of the Leech lattice Lambda to this carrier is at squared distance 3/2; the lattice point has norm^2 = 0/1 and is NOT a 2A axis of the Monster. | nearest_lattice_point(r30_golay_hit_32240): d^2 = 3/2, \|\|lambda\|\|^2 = 0/1, is_2a_axis = False |
| 6 | Its squared Griess norm places it at an exact rational distance from the origin. | <v, v> = (1/8) sum_i v_i^2 = 3/2 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `approximate 500768/1000000`

_Rationale._ The empirical Rule 30 frequency as a rational. The GLM holds it as a carrier (since it IS rational), runs the dyadic tower (levels 0..5 = 0, 1/2, 1/2, 1/2, 1/2, 1/2; exposed at 0->1, 1->11, 2->11, 3->11, 4->11), and the one-bit modulator gives N=512, average=1/2, |average-target| = 12/15625 <= 1/512.

```markdown
# Three Column Thinking

**Query.** `approximate 500768/1000000`  
**Kind.** `real`  
**Answer.** `500768/1000000 = 0.50076800000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  500768/1000000 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 500768/1000000 = 0.50076800000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 1/2, 1/2, 1/2, 1/2, 1/2; exposed at 0->1, 1->11, 2->11, 3->11, 4->11 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 1/2, \|average - target\| = 12/15625 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 0.500768`

_Rationale._ Same as above in decimal notation -- the GLM's parser accepts both.

```markdown
# Three Column Thinking

**Query.** `real value 0.500768`  
**Kind.** `real`  
**Answer.** `0.500768 = 0.50076800000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  0.500768 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 0.500768 = 0.50076800000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 1/2, 1/2, 1/2, 1/2, 1/2; exposed at 0->1, 1->11, 2->11, 3->11, 4->11 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 1/2, \|average - target\| = 12/15625 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 1/2`

_Rationale._ The H_0 limit. The GLM correctly reports exposure as '0->1, 1->never, 2->never, ...' -- the dyadic tower never has to refine past level 1, because 1/2 IS the level-1 carrier.

```markdown
# Three Column Thinking

**Query.** `real value 1/2`  
**Kind.** `real`  
**Answer.** `1/2 = 0.50000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  1/2 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 1/2 = 0.50000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 1/2, 1/2, 1/2, 1/2, 1/2; exposed at 0->1, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 1/2, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 0.500768 - 1/2`

_Rationale._ The deviation |f - 1/2| = 0.000768 as a real value. The GLM expands it into its dyadic tower -- the first non-zero bit is at level 11 (since 2^-11 = 1/2048 < 0.000768 < 2^-10 = 1/1024).

```markdown
# Three Column Thinking

**Query.** `real value 0.500768 - 1/2`  
**Kind.** `real`  
**Answer.** `0.500768 - 1/2 = 0.00076800000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  0.500768 - 1/2 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 0.500768 - 1/2 = 0.00076800000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->11, 1->11, 2->11, 3->11, 4->11 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 12/15625 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 768/1000000`

_Rationale._ The deviation as a rational. The GLM treats it as a carrier and expands its dyadic tower.

```markdown
# Three Column Thinking

**Query.** `approximate 768/1000000`  
**Kind.** `real`  
**Answer.** `768/1000000 = 0.00076800000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  768/1000000 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 768/1000000 = 0.00076800000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->11, 1->11, 2->11, 3->11, 4->11 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 12/15625 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 1/1000`

_Rationale._ The IID two-tailed standard-error threshold 2 * 1/(2 sqrt(N)) = 1/sqrt(N) = 0.001 for N = 10^6. The GLM treats it as a carrier.

```markdown
# Three Column Thinking

**Query.** `approximate 1/1000`  
**Kind.** `real`  
**Answer.** `1/1000 = 0.00100000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  1/1000 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 1/1000 = 0.00100000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->10, 1->10, 2->10, 3->10, 4->10 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 1/1000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 1/2000`

_Rationale._ The IID one-tailed standard error 1/(2 sqrt(N)) = 1/2000 for N = 10^6.

```markdown
# Three Column Thinking

**Query.** `approximate 1/2000`  
**Kind.** `real`  
**Answer.** `1/2000 = 0.00050000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  1/2000 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 1/2000 = 0.00050000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->11, 1->11, 2->11, 3->11, 4->11 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 1/2000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `0.500768 greater than 1/2`

_Rationale._ Strict inequality: empirical Rule 30 frequency vs. the H_0 limit. The GLM correctly returns 'true: 0.500768 > 1/2', separated at dyadic level 2^-16. The first level at which the inequality is decidable is reported explicitly.

```markdown
# Three Column Thinking

**Query.** `0.500768 greater than 1/2`  
**Kind.** `compare`  
**Answer.** `true: 0.500768 > 1/2`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 0.500768 = 0.50076800000000000000..., 1/2 = 0.50000000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `0.500768 less than 0.51`

_Rationale._ Upper bound on the empirical frequency.

```markdown
# Three Column Thinking

**Query.** `0.500768 less than 0.51`  
**Kind.** `compare`  
**Answer.** `true: 0.500768 < 0.51`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 0.500768 = 0.50076800000000000000..., 0.51 = 0.51000000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-8 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `0.500768 greater than 0.4999`

_Rationale._ Lower bound. Together with the previous, brackets (0.4999, 0.51).

```markdown
# Three Column Thinking

**Query.** `0.500768 greater than 0.4999`  
**Kind.** `compare`  
**Answer.** `true: 0.500768 > 0.4999`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 0.500768 = 0.50076800000000000000..., 0.4999 = 0.49990000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `768/1000000 less than 1/1000`

_Rationale._ Is the empirical deviation below 0.001? Yes -- and the GLM reports the exact dyadic level at which the inequality separates.

```markdown
# Three Column Thinking

**Query.** `768/1000000 less than 1/1000`  
**Kind.** `compare`  
**Answer.** `true: 768/1000000 < 1/1000`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 768/1000000 = 0.00076800000000000000..., 1/1000 = 0.00100000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `768/1000000 less than 1/2000`

_Rationale._ Is the empirical deviation below the IID standard error 1/(2 sqrt(N))? Yes (0.000768 < 0.0005 -- wait, NO: 0.000768 > 0.0005). The GLM should return 'false: 768/1000000 > 1/2000', which is consistent with the z-score being 1.54 (above 0 but below 1.96).

```markdown
# Three Column Thinking

**Query.** `768/1000000 less than 1/2000`  
**Kind.** `compare`  
**Answer.** `false: 768/1000000 > 1/2000`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 768/1000000 = 0.00076800000000000000..., 1/2000 = 0.00050000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: False |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `768/1000000 greater than 1/4096`

_Rationale._ Compare the deviation to 1/4096 = 0.000244. Since 0.000768 > 0.000244, the GLM should return 'true'. This is interesting because 1/4096 is the Golay codeword rate -- the deviation is exactly 3.15x the Golay rate.

```markdown
# Three Column Thinking

**Query.** `768/1000000 greater than 1/4096`  
**Kind.** `compare`  
**Answer.** `true: 768/1000000 > 1/4096`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 768/1000000 = 0.00076800000000000000..., 1/4096 = 0.00024414062500000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `768/1000000 less than 1/256`

_Rationale._ Compare the deviation to 1/256 = 0.0039. Trivially true. The point is the GLM gives the exact dyadic separation level.

```markdown
# Three Column Thinking

**Query.** `768/1000000 less than 1/256`  
**Kind.** `compare`  
**Answer.** `true: 768/1000000 < 1/256`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 768/1000000 = 0.00076800000000000000..., 1/256 = 0.00390625000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `2.3593 less than 3.841`

_Rationale._ Compare the empirical chi-square statistic to the 5% critical value for 1 d.o.f. (3.841). The GLM correctly returns 'true: 2.3593 < 3.841', separated at dyadic level 2^-8.

```markdown
# Three Column Thinking

**Query.** `2.3593 less than 3.841`  
**Kind.** `compare`  
**Answer.** `true: 2.3593 < 3.841`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 2.3593 = 2.35930000000000000000..., 3.841 = 3.84100000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-8 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `1.5360 less than 1.96`

_Rationale._ Compare the z-score to the 5% two-tailed critical value. The GLM returns 'true'.

```markdown
# Three Column Thinking

**Query.** `1.5360 less than 1.96`  
**Kind.** `compare`  
**Answer.** `true: 1.5360 < 1.96`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 1.5360 = 1.53600000000000000000..., 1.96 = 1.96000000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-8 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `13 greater than 4`

_Rationale._ The minimum squared distance from a Rule 30 binary window to a Leech minimal vector is 13. The Leech lattice's own minimal squared norm is 4. 13 > 4 is trivially true but establishes that Rule 30 windows are far from being Leech lattice points.

```markdown
# Three Column Thinking

**Query.** `13 greater than 4`  
**Kind.** `compare`  
**Answer.** `true: 13 > 4`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 13 = 13.00000000000000000000..., 4 = 4.00000000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-8 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `1296/83333 less than 1/64`

_Rationale._ Compare the empirical hexacode hit rate to the expected 1/64 = 0.015625. Empirical is 1296/83333 = 0.015552 < 0.015625 -- slightly below expectation.

```markdown
# Three Column Thinking

**Query.** `1296/83333 less than 1/64`  
**Kind.** `compare`  
**Answer.** `true: 1296/83333 < 1/64`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | 1296/83333 = 0.01555206220824883299..., 1/64 = 0.01562500000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 9`

_Rationale._ The ANF degree of a(5) is 9. We probe it via the GLM's real-value machinery (not `verify`, which is for dimensional consistency).

```markdown
# Three Column Thinking

**Query.** `real value 9`  
**Kind.** `real`  
**Answer.** `9 = 9.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  9 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 9 = 9.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 9, 9, 9, 9, 9, 9; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*5 - 1`

_Rationale._ The closed-form ANF degree pattern 2n-1 evaluated at n=5, giving 9. The GLM should compute this exact arithmetic expression.

```markdown
# Three Column Thinking

**Query.** `real value 2*5 - 1`  
**Kind.** `real`  
**Answer.** `2*5 - 1 = 9.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*5 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*5 - 1 = 9.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 9, 9, 9, 9, 9, 9; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*6 - 1`

_Rationale._ Same pattern at n=6, giving 11.

```markdown
# Three Column Thinking

**Query.** `real value 2*6 - 1`  
**Kind.** `real`  
**Answer.** `2*6 - 1 = 11.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*6 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*6 - 1 = 11.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 11, 11, 11, 11, 11, 11; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `describe 196560`

_Rationale._ The number of Leech lattice minimal vectors. The GLM describes it as a numeral (no register entry is spelled '196560').

```markdown
# Three Column Thinking

**Query.** `describe 196560`  
**Kind.** `describe`  
**Answer.** `'196560' denotes number 196560 [numeral: numeral 196560]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '196560' -> number 196560  [numeral: numeral 196560] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 196560 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '196560/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '2358721/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe 25`

_Rationale._ The spatial dimension of the Lorentzian lift II_{25,1}. The GLM describes it as a numeral.

```markdown
# Three Column Thinking

**Query.** `describe 25`  
**Kind.** `describe`  
**Answer.** `'25' denotes number 25 [numeral: numeral 25]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '25' -> number 25  [numeral: numeral 25] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 25 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '25/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '301/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe 70`

_Rationale._ The time-norm of the Weyl vector (0,1,...,24|70) of II_{25,1}. The GLM has a substrate_cognition experiment verifying that 1^2 + 2^2 + ... + 24^2 = 70^2 = 4900, which is the Pythagorean identity that makes the Weyl vector null.

```markdown
# Three Column Thinking

**Query.** `describe 70`  
**Kind.** `describe`  
**Answer.** `'70' denotes number 70 [numeral: numeral 70]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '70' -> number 70  [numeral: numeral 70] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 70 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '70/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '841/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `real value 70*70 - (1*1 + 2*2 + 3*3 + 4*4 + 5*5 + 6*6 + 7*7 + 8*8 + 9*9 + 10*10 + 11*11 + 12*12 + 13*13 + 14*14 + 15*15 + 16*16 + 17*17 + 18*18 + 19*19 + 20*20 + 21*21 + 22*22 + 23*23 + 24*24)`

_Rationale._ The exact arithmetic expression that verifies the Weyl vector of II_{25,1} is null: 70^2 = 4900 = sum_{i=1}^{24} i^2 = 4900. The GLM computes this exact rational expression.

```markdown
# Three Column Thinking

**Query.** `real value 70*70 - (1*1 + 2*2 + 3*3 + 4*4 + 5*5 + 6*6 + 7*7 + 8*8 + 9*9 + 10*10 + 11*11 + 12*12 + 13*13 + 14*14 + 15*15 + 16*16 + 17*17 + 18*18 + 19*19 + 20*20 + 21*21 + 22*22 + 23*23 + 24*24)`  
**Kind.** `real`  
**Answer.** `70*70 - (1*1 + 2*2 + 3*3 + 4*4 + 5*5 + 6*6 + 7*7 + 8*8 + 9*9 + 10*10 + 11*11 + 12*12 + 13*13 + 14*14 + 15*15 + 16*16 + 17*17 + 18*18 + 19*19 + 20*20 + 21*21 + 22*22 + 23*23 + 24*24) = 0.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  70*70 - (1*1 + 2*2 + 3*3 + 4*4 + 5*5 + 6*6 + 7*7 + 8*8 + 9*9 + 10*10 + 11*11 + 12*12 + 13*13 + 14*14 + 15*15 + 16*16 + 17*17 + 18*18 + 19*19 + 20*20 + 21*21 + 22*22 + 23*23 + 24*24) is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 70*70 - (1*1 + 2*2 + 3*3 + 4*4 + 5*5 + 6*6 + 7*7 + 8*8 + 9*9 + 10*10 + 11*11 + 12*12 + 13*13 + 14*14 + 15*15 + 16*16 + 17*17 + 18*18 + 19*19 + 20*20 + 21*21 + 22*22 + 23*23 + 24*24) = 0.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `irrational pi`

_Rationale._ The GLM treats pi as a process (a converging sequence of rational carriers) -- exactly the substrate-native distinction relevant to Problem 2's comparison between the Rule 30 center column and the binary digits of pi.

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

## Query: `approximate pi/4`

_Rationale._ Pi/4 -- the BBP-spigot-friendly sub-expression. The GLM computes it to 20 decimal places as a process.

```markdown
# Three Column Thinking

**Query.** `approximate pi/4`  
**Kind.** `real`  
**Answer.** `pi/4 = 0.78539816339744830961 (to 20 places); no carrier holds it`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  pi/4 is not rational, so no carrier holds it and no level of the tower ever will.  What the machine holds is the process that converges to it. | rational: False |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | pi/4 = 0.78539816339744830961 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 1/2, 3/4, 3/4, 3/4, 25/32; exposed at 0->1, 1->2, 2->5, 3->5, 4->5 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 201/256, \|average - target\| = 4126705813298350745217514646167138043578859/17058607984620267919080842971801757812500000000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `pi greater than 3`

_Rationale._ Trivial inequality -- but the GLM reports the exact dyadic separation level, demonstrating the substrate-native way of comparing an irrational process to a rational.

```markdown
# Three Column Thinking

**Query.** `pi greater than 3`  
**Kind.** `compare`  
**Answer.** `true: pi > 3`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | pi = 3.14159265358979323846..., 3 = 3.00000000000000000000... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-8 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `pi less than 22/7`

_Rationale._ Archimedean upper bound on pi. The GLM should return 'true'.

```markdown
# Three Column Thinking

**Query.** `pi less than 22/7`  
**Kind.** `compare`  
**Answer.** `true: pi < 22/7`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | pi = 3.14159265358979323846..., 22/7 = 3.14285714285714285714... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: less; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `pi greater than 223/71`

_Rationale._ Archimedean lower bound on pi (the famous 223/71 < pi < 22/7 from Archimedes). The GLM should return 'true'.

```markdown
# Three Column Thinking

**Query.** `pi greater than 223/71`  
**Kind.** `compare`  
**Answer.** `true: pi > 223/71`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Each side is read as a process: a rule that returns an exact rational within any precision asked of it.  Nothing is rounded and no float is built. | pi = 3.14159265358979323846..., 223/71 = 3.14084507042253521126... |
| 2 | The two are compared at increasing precision until their intervals come apart.  The first precision at which they do is the cost of the answer. | ladder [8, 16, 32, 64, 128, 256]; separated at 2**-16 |
| 3 | Two unequal processes always separate at some finite precision, and this one is found.  Two equal processes never separate, and no amount of refinement turns that into a proof of equality -- so 'not distinguished' is the only honest answer there. | relation asked: greater; verdict: True |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*1 - 1`

_Rationale._ ANF degree at n=1: 2*1-1 = 1 (the GLM computes the closed form).

```markdown
# Three Column Thinking

**Query.** `real value 2*1 - 1`  
**Kind.** `real`  
**Answer.** `2*1 - 1 = 1.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*1 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*1 - 1 = 1.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 1, 1, 1, 1, 1, 1; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*2 - 1`

_Rationale._ ANF degree at n=2: 2*2-1 = 3.

```markdown
# Three Column Thinking

**Query.** `real value 2*2 - 1`  
**Kind.** `real`  
**Answer.** `2*2 - 1 = 3.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*2 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*2 - 1 = 3.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 3, 3, 3, 3, 3, 3; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*3 - 1`

_Rationale._ ANF degree at n=3: 2*3-1 = 5.

```markdown
# Three Column Thinking

**Query.** `real value 2*3 - 1`  
**Kind.** `real`  
**Answer.** `2*3 - 1 = 5.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*3 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*3 - 1 = 5.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 5, 5, 5, 5, 5, 5; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 2*4 - 1`

_Rationale._ ANF degree at n=4: 2*4-1 = 7.

```markdown
# Three Column Thinking

**Query.** `real value 2*4 - 1`  
**Kind.** `real`  
**Answer.** `2*4 - 1 = 7.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2*4 - 1 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2*4 - 1 = 7.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 7, 7, 7, 7, 7, 7; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 6.5e9`

_Rationale._ The engine's measured throughput at n=10^5: 6.5 * 10^9 bit-operations per second. The GLM treats it as a real value.

```markdown
# Three Column Thinking

**Query.** `real value 6.5e9`  
**Kind.** `real`  
**Answer.** `6.5e9 = 6500000000.00000000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  6.5e9 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 6.5e9 = 6500000000.00000000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 6500000000, 6500000000, 6500000000, 6500000000, 6500000000, 6500000000; exposed at 0->never, 1->never, 2->never, 3->never, 4->never |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 0 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `describe 0`

_Rationale._ Zero -- the additive identity of the Leech lattice and the weight of the all-zero Golay codeword.

```markdown
# Three Column Thinking

**Query.** `describe 0`  
**Kind.** `describe`  
**Answer.** `'0' denotes number 0 [numeral: numeral 0]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '0' -> number 0  [numeral: numeral 0] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 0 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '1/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe 1`

_Rationale._ One -- the additive identity's successor, the smallest positive integer.

```markdown
# Three Column Thinking

**Query.** `describe 1`  
**Kind.** `describe`  
**Answer.** `'1' denotes number 1 [numeral: numeral 1]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '1' -> number 1  [numeral: numeral 1] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 1 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '13/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe 24`

_Rationale._ The dimension of the GLM's substrate (the Leech lattice Lambda_24).

```markdown
# Three Column Thinking

**Query.** `describe 24`  
**Kind.** `describe`  
**Answer.** `'24' denotes number 24 [numeral: numeral 24]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '24' -> number 24  [numeral: numeral 24] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 24 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '24/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '289/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `describe 30`

_Rationale._ The Rule 30 number itself. The GLM describes it as a numeral.

```markdown
# Three Column Thinking

**Query.** `describe 30`  
**Kind.** `describe`  
**Answer.** `'30' denotes number 30 [numeral: numeral 30]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '30' -> number 30  [numeral: numeral 30] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 30 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '30/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '361/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---
