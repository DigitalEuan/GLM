/* Round 13 (EMP): how long can a column of a LEFT-WHITE Rule 30 row stay periodic?
 *
 * A left-white row is white on (-inf, l) and black at l.  The column at distance d from the
 * edge, over times 0..L, depends only on the d+L+1 cells l..l+d+L, so the longest p-periodic
 * run (a(t+p) = a(t) for all t+p <= L) is a finite search.
 *
 *   mode "exact"  p D       : exhaustive search over all rows, exact longest run, d = 0..D
 *                             (the Lean file RunBoundData.lean re-checks d <= 7 for p = 2 and
 *                             d <= 4 for p = 3..6 with native_decide).
 *   mode "dfs"    D0 D1 lim : period 2 only.  A depth-first search over the column to the right
 *                             (u = column d+1), computing every column to the left sideways
 *                             (x_{j-1}(t) = x_j(t+1) xor (x_j(t) or x_{j+1}(t))) and pruning as
 *                             soon as the white region or the black edge is violated.  It is a
 *                             relaxation (it keeps only constraints from the left), so the
 *                             depth at which it dies is an UPPER bound on the alternating run
 *                             (non-constant period 2) at that distance.
 *
 * gcc -O2 -o r13_periodic_runs r13_periodic_runs.c
 * ./r13_periodic_runs exact 2 9 ; ./r13_periodic_runs dfs 1 26 0
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int exact_run(int p, int d) {
  for (int L = p;; L++) {
    int K = d + L + 1;
    if (K > 40) return -1;
    int found = 0;
    for (uint64_t m = 1; m < (1ULL << K); m += 2) {
      uint64_t r = m; unsigned char col[64];
      for (int t = 0; t <= L; t++) { col[t] = (r >> (d + t)) & 1; r = (r << 2) ^ ((r << 1) | r); }
      int ok = 1;
      for (int t = 0; t + p <= L; t++) if (col[t + p] != col[t]) { ok = 0; break; }
      if (ok) { found = 1; break; }
    }
    if (!found) return L - 1;
  }
}

#define MAXT 400
static unsigned char g[MAXT + 3][MAXT + 3];
static int N, ph, best;
static long nodes, nodelim;
static int ok_add(int T) {
  if (T > N && g[0][T - 1] == 1 && g[0][T] != (1 ^ g[1][T - 1])) return 0;  /* column d+1's own rule */
  for (int k = 2;; k++) {
    int t = T - (k - 1); if (t < N) break;
    int j = 1 - k;
    unsigned char v = g[k - 1][t + 1] ^ (g[k - 1][t] | g[k - 2][t]);
    g[k][t] = v;
    int s = -j;
    if ((t < s && v) || (t == s && !v)) return 0;
  }
  return 1;
}
static int dfs(int T) {
  nodes++; if (nodelim && nodes > nodelim) return 1;
  if (T - N > best) best = T - N;
  if (T - N >= MAXT - N - 5) return 1;
  for (int b = 0; b < 2; b++) {
    g[0][T] = b; g[1][T] = (T + ph) & 1;
    if (ok_add(T) && dfs(T + 1)) return 1;
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc >= 4 && !strcmp(argv[1], "exact")) {
    int p = atoi(argv[2]), D = atoi(argv[3]);
    for (int d = 0; d <= D; d++) { printf("exact p=%d d=%d longest_run=%d\n", p, d, exact_run(p, d)); fflush(stdout); }
    return 0;
  }
  if (argc >= 5 && !strcmp(argv[1], "dfs")) {
    int D0 = atoi(argv[2]), D1 = atoi(argv[3]); nodelim = atol(argv[4]);
    for (N = D0; N <= D1; N++) {
      int worst = 0, surv = 0;
      for (ph = 0; ph < 2; ph++) { memset(g, 0, sizeof g); best = 0; nodes = 0; if (dfs(N)) surv = 1; if (best > worst) worst = best; }
      printf("dfs alternating d=%d search_dies_after=%d%s\n", N, worst, surv ? " (node limit reached)" : "");
      fflush(stdout);
    }
    return 0;
  }
  fprintf(stderr, "usage: exact p D | dfs D0 D1 nodelimit\n");
  return 1;
}
