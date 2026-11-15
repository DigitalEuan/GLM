# 04 — The established systems map

What the field already has (and what a Kaggle submission must respect).

## The trivial baseline — grid

Side ⌈√n⌉; score contribution ⌈√n⌉/√n − 1; exact total over the 1,000
puzzles: **28.9376699165…** (script 01). Grid is *proven optimal* for
perfect squares (area bound tight) — 31 puzzles cannot be improved at all.

## Proven values (the closed cases)

| n | s(n) | source |
|---|---|---|
| 1 | 1 | trivial |
| 2, 3 | 2 | classic |
| 5 | 2+1/√2 ≈ 2.7071 | classic proof |
| 6 | 3 | Kearney–Shiu 2002 |
| 7, 8 | 3 | Bajmóóczy (via Göbel); El Moumni |
| 10 | 3+1/√2 ≈ 3.7071 | Stromquist 2003 |
| 14, 15 | 4 | El Moumni; Friedman |
| 24 | 5 | Friedman |
| 35 | 6 | Friedman |
| k², k²−1, k²−2 | k | trivial; Nagamochi 2005 |

These are the *only* puzzles with proven optima; everything else is open —
which is what makes the competition possible.

## Pattern families (best-known packings, Friedman survey)

1. **Göbel diagonal strips** (45°): count(a) = ⌊a²+a+3+(a−1)√2⌋ squares in
   side a+1+1/√2 — beats grid for all a (verified exactly, script 02).
2. **Göbel central square**: 2a²+2a+b² squares in side a+1+b/√2 (s(28),
   s(40), s(65), s(89)).
3. **Diagonal strips of width 2/3/4** (Cottingham, Stenlund, Cantrell):
   s(19), s(66), s(87), …
4. **L-extension closure**: m-in-L → m+⌊L+1⌋+⌊L⌋ in L+1 ("primitive"
   packings vs. L-wrapped ones in the survey's taxonomy).
5. **Tilted non-45° packings** (Trump's 11 ≈ 40.18°; Hämäläinen/Gustafson's
   18 ≈ 24.29°; Gensane–Ryckelynck's 29 with 6 angles) — the hard frontier.

## Search methods (the computational literature)

- **Nurmela–Östergård (1997)**: simulated annealing with penalty functions,
  packings to n = 50.
- **Gensane–Ryckelynck (2005)**: *inflation algorithm* — start dense, shrink
  gradually (our engine's continuation follows this family); first computer
  packings that might be optimal.
- **Graham–Lubachevsky** double-lattice/billiard methods (circles → squares
  adaptations), dense-pattern families.
- Modern: gradient/penalty descent, RL proposals (competition description).

## What this means for a leaderboard

The top of the leaderboard will hold rediscoveries of the best-known
packings (Göbel/Cantrell/Trump families) plus genuinely new ones in the open
n > 100 range. Every valid improvement over grid scores; partial submissions
allowed. Our verified standing: 30 puzzles improved (docs/01) with the
k²+1 family at k+0.8 — strictly above grid, strictly below the historical
best-knowns (e.g., our 5@2.8 vs. proven s(5) = 2.7071).
