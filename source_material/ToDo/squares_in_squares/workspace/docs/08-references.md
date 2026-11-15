# 08 — References

## The competition

- Reade, W., Oldacre, A. (2026). *Squares in Squares*. Kaggle.
  https://www.kaggle.com/competitions/squares-in-squares — 1,000 puzzles,
  score = Σ(L/√n − 1), partial submissions allowed.

## The problem and its literature

- **Friedman, E.** (2009). "Packing Unit Squares in Squares: A Survey and
  New Results." *Electronic Journal of Combinatorics*, Dynamic Survey DS#7.
  — best-known packings/bounds for n ≤ 100; proven values; Göbel strips,
  central-square family, L-extension; lower-bound technique.
- **Göbel, F.** — first published packings (diagonal strips at 45°).
- **Nagamochi, H.** (2005). — s(k²−2) = s(k²−1) = k.
- **Kearney, M., Shiu, W.** (2002). — proof of s(6) = 3.
- **Stromquist, W.** (2003). — proof of s(10) = 3+1/√2.
- **Gensane, T., Ryckelynck, P.** (2005). "Packing unit squares in a square."
  — inflation algorithm; first computer packings that might be optimal.
- **Nurmela, K.-J., Östergård, P. R. J.** (1997). — SA packings to n = 50.
- **Graham, R. L., Lubachevsky, B. D.** — dense/double-lattice packing
  methods.
- Cottingham; Stenlund (1980); Trump (1979); Hämäläinen (1980); Gustafson
  (1981); Bidwell (1998); Cantrell, D. (2002, 2005); Morandi; Hajba (2009) —
  the individual best-known packings catalogued in the survey.
- **Erdős, P., Graham, R.** — W(s) wasted-area problem; Montgomery; Roth &
  Vaughan bounds.

## Methodology

- **Craig, E. R. A. (DigitalEuan).** *Geometric Language Machine (GLM)*,
  §§2.2–2.3, 12, 17, 19.3, 24. https://github.com/DigitalEuan/GLM — Three
  Column Thinking, UBP discipline, cent_compiler, optimization loop.

## Premise note

Established values are carried as literature premises (axiom-class); our
verified claims are strictly (a) exact accounting identities, (b) certified
upper-bound packings, and (c) the improvement over the grid ceiling.
Optimality of any packing is never claimed (refused, `WOULD_BE_GUESS`;
formal record `s11_optimal_value`, deliberate sorry). Search results are
measured with declared margins; certificates are double-scanned SAT checks.
