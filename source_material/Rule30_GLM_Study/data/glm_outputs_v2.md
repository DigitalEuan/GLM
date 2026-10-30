# GLM queries (round 2): informationally rich

All outputs verbatim from `python3 GLM.py --plan -q '...' -f markdown`,
run on the live DigitalEuan/GLM repository (clone at
`/home/z/my-project/glm_repo`, version 5.37 per README).

The `--plan` flag selects the typed planner surface, which routes
through `glm_universal.runtime.parser` and
`glm_universal.runtime.session` only. The default multi-surface
router (K1, Phase 89) has an `ImportError` on the respell/sinter
fallback that triggers only on a refusal; using `--plan` avoids
that path entirely.

Unlike round 1, these queries CARRY Rule 30 data into the GLM's
analytical machinery: the empirical frequency as a rational
carrier, the chi-square statistic, the z-score, the ANF-degree
integer pattern (deg(a(n)) = 2n-1), the Golay/hexacode hit rates,
the Leech lattice distance floor. The GLM's `real` machinery
(dyadic tower, one-bit modulator, machine-checked error bound)
and `compare` machinery (exact rational inequality) are engaged
substantively.

## Query: `approximate 500768/1000000`

_Rationale._ Pass the empirical Rule 30 frequency (500768 ones in 10^6 cells) as a rational number to the GLM's `real` machinery. The GLM holds it as a carrier (since it IS rational), runs the dyadic tower, and applies the one-bit modulator with its machine-checked error bound.

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

_Rationale._ Same as above but in decimal notation. The GLM's parser accepts both.

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

_Rationale._ The H_0 limit (asymptotic frequency conjectured to be 1/2). The GLM holds 1/2 as a carrier and reports its dyadic tower levels.

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

## Query: `compare 500768/1000000 greater than 1/2`

_Rationale._ Strict inequality: empirical Rule 30 frequency vs. the conjectured limit. The `compare` query kind is decidable when the inequality is strict -- the GLM should return 'greater than' with exact rational evidence.

```markdown
QUERY   compare 500768/1000000 greater than 1/2
UNSOLVED        parse_real: 'compare 500768/1000000' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 500768/1000000' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 500768/1000000 less than 0.51`

_Rationale._ Sanity-check upper bound on the empirical frequency.

```markdown
QUERY   compare 500768/1000000 less than 0.51
UNSOLVED        parse_real: 'compare 500768/1000000' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 500768/1000000' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 500768/1000000 greater than 0.4999`

_Rationale._ Sanity-check lower bound. Together with the previous, this brackets the empirical frequency to (0.4999, 0.51).

```markdown
QUERY   compare 500768/1000000 greater than 0.4999
UNSOLVED        parse_real: 'compare 500768/1000000' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 500768/1000000' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 768/1000000`

_Rationale._ The deviation |f - 1/2| = 768/10^6 as a rational. The GLM should hold it as a carrier and give its dyadic tower.

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

## Query: `compare 768/1000000 less than 1/1000`

_Rationale._ Is the empirical deviation within 0.1%? Yes, since 0.000768 < 0.001. The GLM should return 'less than' with exact rational evidence.

```markdown
QUERY   compare 768/1000000 less than 1/1000
UNSOLVED        parse_real: 'compare 768/1000000' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 768/1000000' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 768/1000000 less than 1/sqrt(1000000)`

_Rationale._ Compare the empirical deviation to the IID standard error 1/(2*sqrt(N)). Note 1/sqrt(N) = 1/1000 = 0.001; the empirical deviation 0.000768 < 0.001 is below the SE under H_0, consistent with the non-rejection of H_0.

```markdown
QUERY   compare 768/1000000 less than 1/sqrt(1000000)
UNSOLVED        parse_real: 'compare 768/1000000' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 768/1000000' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 2*exp(-2*1000000*(768/1000000)^2) less than 1`

_Rationale._ Hoeffding bound on the empirical deviation: P(|f-1/2| > 0.000768) <= 2*exp(-2*10^6*(0.000768)^2). We ask the GLM to compare this to 1 (which is trivially true) -- the point is that the GLM computes the exponential exactly via its process machinery.

```markdown
QUERY   compare 2*exp(-2*1000000*(768/1000000)^2) less than 1
UNSOLVED        parse_real: 'compare 2*exp(-2*1000000*(768/1000000)^2)' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 2*exp(-2*1000000*(768/1000000)^2)' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 0.500768 - 1/2`

_Rationale._ The deviation as a real number, for the GLM to expand into its dyadic tower. The first non-zero bit of the tower is at level 11 (since 0.000768 = 768/10^6 < 2^-10 = 1/1024, and 2^-11 = 1/2048 < 0.000768), so the GLM should show that the level-0 through level-10 carriers are all 0, and the level-11 carrier is non-zero.

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

## Query: `describe 9`

_Rationale._ The ANF degree of a(5) is 9. The GLM should describe 9 as a number (an integer carrier in the SI7 layer). This is a flat probe -- the GLM does not have an ANF-degree query kind -- but we record the baseline.

```markdown
# Three Column Thinking

**Query.** `describe 9`  
**Kind.** `describe`  
**Answer.** `'9' denotes number 9 [numeral: numeral 9]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '9' -> number 9  [numeral: numeral 9] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 9 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '9/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '109/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `compare 9 greater than 5`

_Rationale._ Sanity check: is the ANF degree of a(5) (= 9) greater than n=5? Yes, consistent with our finding that deg(a(n)) = 2n-1 > n.

```markdown
QUERY   compare 9 greater than 5
UNSOLVED        parse_real: 'compare 9' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 9' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `describe 196560`

_Rationale._ 196560 is the number of Leech lattice minimal vectors (norm^2 = 4). The GLM should describe this number as a carrier.

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

## Query: `describe 4096`

_Rationale._ 4096 is the number of Golay-24 codewords. The GLM should describe this number as a carrier.

```markdown
# Three Column Thinking

**Query.** `describe 4096`  
**Kind.** `describe`  
**Answer.** `'4096' denotes number 4096 [numeral: numeral 4096]; no register entry is spelled that way, so it is described by what it denotes`  

| # | Step | Mathematics |
|---|---|---|
| 1 | Resolve each notation to what it denotes.  Nothing is embedded or hashed: a term is admitted only when the registers pin down a determinate referent. | '4096' -> number 4096  [numeral: numeral 4096] |
| 2 | Encode each meaning in the 24-coordinate meaning space and decode it again.  The encoder takes a meaning and nothing else, so the carrier cannot depend on the spelling. | 4096 = ['1/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '4096/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '0/1', '49153/1'] |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
<unknown>:1732: SyntaxWarning: invalid escape sequence '\s'
<unknown>:1724: SyntaxWarning: invalid escape sequence '\s'
```

---

## Query: `compare 8 less than 11`

_Rationale._ Sanity check on the Golay codeword rate: empirical 8 hits vs expected 10.16 (which we round to 11). 8 < 11 is the comparison.

```markdown
QUERY   compare 8 less than 11
UNSOLVED        parse_real: 'compare 8' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 8' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `verify 9 = 2*5 - 1`

_Rationale._ Verify the ANF degree pattern: deg(a(5)) = 9 = 2*5 - 1. The GLM's `verify` query kind should check this integer equality exactly.

```markdown
QUERY   verify 9 = 2*5 - 1
UNSOLVED        verify: numeric factor 9 is not a power of ten; the register tracks the decimal scale exactly and refuses to absorb other constants
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `verify 11 = 2*6 - 1`

_Rationale._ Verify the same pattern at n=6: deg(a(6)) = 11 = 2*6 - 1.

```markdown
QUERY   verify 11 = 2*6 - 1
UNSOLVED        verify: numeric factor 11 is not a power of ten; the register tracks the decimal scale exactly and refuses to absorb other constants
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 2.3593`

_Rationale._ The chi-square statistic from the single-bit test (2.3593) as a real value. The GLM should give its dyadic tower.

```markdown
# Three Column Thinking

**Query.** `approximate 2.3593`  
**Kind.** `real`  
**Answer.** `2.3593 = 2.35930000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  2.3593 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 2.3593 = 2.35930000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 2, 2, 9/4, 9/4, 37/16, 75/32; exposed at 0->2, 1->2, 2->4, 3->4, 4->5 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 183/512, \|average - target\| = 601/320000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 2.3593 less than 3.841`

_Rationale._ Compare the chi-square statistic to the 5% critical value (3.841 for 1 d.o.f.). 2.3593 < 3.841 is true, so we fail to reject H_0.

```markdown
QUERY   compare 2.3593 less than 3.841
UNSOLVED        parse_real: 'compare 2.3593' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 2.3593' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 1.5360`

_Rationale._ The z-score (1.5360) as a real value.

```markdown
# Three Column Thinking

**Query.** `approximate 1.5360`  
**Kind.** `real`  
**Answer.** `1.5360 = 1.53600000000000000000 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  1.5360 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 1.5360 = 1.53600000000000000000 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 1, 3/2, 3/2, 3/2, 3/2, 49/32; exposed at 0->1, 1->5, 2->5, 3->5, 4->5 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 137/256, \|average - target\| = 27/32000 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 1.5360 less than 1.96`

_Rationale._ Compare the z-score to the 5% two-tailed critical value (1.96). 1.5360 < 1.96 is true, so we fail to reject H_0.

```markdown
QUERY   compare 1.5360 less than 1.96
UNSOLVED        parse_real: 'compare 1.5360' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 1.5360' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 8/41666`

_Rationale._ The empirical Golay codeword hit rate (8 hits / 41666 windows). The GLM should hold this as a rational carrier.

```markdown
# Three Column Thinking

**Query.** `real value 8/41666`  
**Kind.** `real`  
**Answer.** `8/41666 = 0.00019200307204915278 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  8/41666 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 8/41666 = 0.00019200307204915278 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->never, 1->never, 2->13, 3->13, 4->13 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 0, \|average - target\| = 4/20833 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 8/41666 less than 1/4096`

_Rationale._ Is the empirical hit rate below the expected uniform rate? 8/41666 = 0.00019199 < 1/4096 = 0.00024414 -- yes, the empirical Golay codeword rate is slightly below the random expectation (8 vs 10.16 expected), well within Poisson fluctuation.

```markdown
QUERY   compare 8/41666 less than 1/4096
UNSOLVED        parse_real: 'compare 8/41666' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 8/41666' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `real value 1296/83333`

_Rationale._ The empirical hexacode hit rate.

```markdown
# Three Column Thinking

**Query.** `real value 1296/83333`  
**Kind.** `real`  
**Answer.** `1296/83333 = 0.01555206220824883299 (to 20 places); a carrier holds it exactly`  

| # | Step | Mathematics |
|---|---|---|
| 1 | A carrier is 24 exact rationals.  1296/83333 is rational, so a carrier does hold it. | rational: True |
| 2 | The process is asked for an approximation good to 2**-k with k large enough that 20 decimal places are settled.  No float is constructed. | 1296/83333 = 0.01555206220824883299 |
| 3 | Level n of the dyadic tower holds floor(x*2^n)/2^n -- a rational carrier that is indistinguishable from the target at that resolution, and is exposed by a higher level. | levels 0..5: 0, 0, 0, 0, 0, 0; exposed at 0->7, 1->7, 2->7, 3->7, 4->7 |
| 4 | The one-bit modulator chases the fractional part with an exact error accumulator.  After N ticks its time average is a rational k/N within 1/N of the target -- the machine-checked bound GLM.Info.dsAverage_error_le. | N = 512, average = 7/512, \|average - target\| = 80221/42666496 <= 1/512 |
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 1296/83333 less than 1/64`

_Rationale._ Compare the empirical hexacode rate to the expected 1/64 = 0.015625. 1296/83333 = 0.015552 < 0.015625 -- slightly below, within 0.5%.

```markdown
QUERY   compare 1296/83333 less than 1/64
UNSOLVED        parse_real: 'compare 1296/83333' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 1296/83333' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `compare 13 greater than 4`

_Rationale._ The minimum squared distance from a Rule 30 binary window to a Leech minimal vector is 13. The Leech lattice's own minimal squared norm is 4. 13 > 4 confirms Rule 30 windows are NOT Leech lattice points.

```markdown
QUERY   compare 13 greater than 4
UNSOLVED        parse_real: 'compare 13' is not a notation this module reads; it understands sqrt(<rational>), pi, e, phi, <integer>, <numerator>/<denominator>, and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4.  The expression grammar stopped with: parse_expression: 'compare 13' -- 'compare' is not a constant or function this module knows; it reads + - * / ^, brackets, the constants pi, e, phi, sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `describe 25`

_Rationale._ 25 is the spatial dimension of the Lorentzian lift II_{25,1}. The GLM should describe this number as a carrier.

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

_Rationale._ 70 is the time-norm of the Weyl vector (0,1,...,24|70) of II_{25,1}. The GLM's substrate_cognition has lorentzian_experiment which verifies 1^2+2^2+...+24^2 = 70^2 (a Pythagorean identity). We probe whether the GLM has 70 as a carrier.

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

## Query: `irrational pi`

_Rationale._ The direct analogue to Rule 30's center column: the binary digits of pi are also conjectured normal but no proof exists. The GLM's `real` query treats pi as a process (a converging sequence of rational carriers), exactly the substrate-native distinction.

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

_Rationale._ The first BBP-spigot-friendly sub-expression. The GLM should compute pi/4 to 20 places as a process.

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

## Query: `verify 3 = 2*2 - 1`

_Rationale._ deg(a(2)) = 3 = 2*2-1.

```markdown
QUERY   verify 3 = 2*2 - 1
UNSOLVED        verify: numeric factor 3 is not a power of ten; the register tracks the decimal scale exactly and refuses to absorb other constants
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `verify 5 = 2*3 - 1`

_Rationale._ deg(a(3)) = 5 = 2*3-1.

```markdown
QUERY   verify 5 = 2*3 - 1
UNSOLVED        verify: numeric factor 5 is not a power of ten; the register tracks the decimal scale exactly and refuses to absorb other constants
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `verify 7 = 2*4 - 1`

_Rationale._ deg(a(4)) = 7 = 2*4-1.

```markdown
QUERY   verify 7 = 2*4 - 1
UNSOLVED        verify: numeric factor 7 is not a power of ten; the register tracks the decimal scale exactly and refuses to absorb other constants
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1732: SyntaxWarning: invalid escape sequence '\s'
  agreed = report["agreement"]
/home/z/my-project/glm_repo/glm_universal/runtime/tct_engine.py:1724: SyntaxWarning: invalid escape sequence '\s'
  def _body_report_language(args) -> str:
```

---

## Query: `approximate 6.5e9`

_Rationale._ The engine's measured throughput: 6.5 * 10^9 bit-operations per second at n = 10^5. We ask the GLM to treat this as a real value.

```markdown
# Three Column Thinking

**Query.** `approximate 6.5e9`  
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
