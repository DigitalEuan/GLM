/* Round 17 (EMP, outside Lean): longest period-2 run of the column at distance d from the
   black edge of a left-white Rule 30 row.  Depth-first search over the row, cell by cell,
   pruning as soon as the column stops being 2-periodic.  Usage: ./period_two_search d
   Prints B(d) and a witness row (bit i = cell i).  The Lean certificates for d <= 18 are in
   RunBoundSearch.lean and RunBoundEighteen.lean; this program is an independent cross-check.
   Rows are 128-bit, which is enough for d <= 30. */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
static int d, col[400], best = -1, CAP = 110;
static u128 W;
static int colAt(u128 r, int t) {
  for (int i = 0; i < t; i++) r = (r << 2) ^ ((r << 1) | r);
  return (int)((r >> (d + t)) & 1);
}
static void dfs(int c, u128 r) {
  for (int b = 0; b < 2; b++) {
    if (c == 0 && b == 0) continue;           /* the edge cell is black */
    u128 r2 = r | ((u128)b << c);
    if (c >= d) {
      int t = c - d;                          /* cell d+t fixes the column at time t */
      col[t] = colAt(r2, t);
      if (t >= 2 && col[t] != col[t - 2]) continue;
      if (t > best) { best = t; W = r2; }
      if (c >= CAP) continue;
    }
    dfs(c + 1, r2);
  }
}
int main(int argc, char **argv) {
  if (argc < 2) return 1;
  d = atoi(argv[1]);
  dfs(0, 0);
  printf("d=%d B=%d d+B=%d witness_lo=%llu\n", d, best, d + best, (unsigned long long)W);
  return 0;
}
