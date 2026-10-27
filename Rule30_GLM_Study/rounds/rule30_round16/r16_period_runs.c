/* Round 16: exact longest p-periodic run of the column at distance d from the black edge of a
   left-white row (cells < 0 white, cell 0 black, cells 1.. free).
   Anti-diagonal recursion: diag[m][t] = cell (t, m - t);
   diag[m][t] = diag[m-2][t-1] XOR (diag[m-1][t-1] OR diag[m][t-1]), diag[m][0] = x_m.
   The column cell (t, d) is diag[d + t][t].  A run of length L means a(t + p) = a(t) for all
   t + p <= L.  DFS over x_1, x_2, ... ; at depth m the new column value a(m - d) is checked.
   Usage: ./r16_period_runs p dmax Tcap                                                     */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXM 256
#define MAXT 200
static unsigned char diag[MAXM][MAXT];
static int P, D, T, best, hitcap;
static long long nodes;
static unsigned long long path, bestpath;
static unsigned char colv(int t) { return diag[D + t][t]; }
static void fill(int m, int x) {
  diag[m][0] = x;
  for (int t = 1; t < T; t++) {
    int a = (m >= 2) ? diag[m-2][t-1] : 0;
    int b = (m >= 1) ? diag[m-1][t-1] : 0;
    diag[m][t] = a ^ (b | diag[m][t-1]);
  }
}
static void dfs(int m) {           /* cells 0..m-1 assigned; assign cell m */
  for (int x = 0; x < 2; x++) {
    nodes++;
    fill(m, x);
    if (x) path |= 1ULL << m; else path &= ~(1ULL << m);
    int t = m - D;                 /* newly known column time */
    if (t >= P) { if (colv(t) != colv(t - P)) continue; }
    if (t > best) { best = t; bestpath = path & ((m >= 63) ? ~0ULL : ((1ULL << (m + 1)) - 1)); }
    if (t >= T - 1) { hitcap = 1; continue; }
    dfs(m + 1);
  }
}
int main(int argc, char **argv) {
  P = atoi(argv[1]); int dmax = atoi(argv[2]); T = atoi(argv[3]);
  for (D = 0; D <= dmax; D++) {
    memset(diag, 0, sizeof diag);
    best = -1; hitcap = 0; nodes = 0;
    fill(0, 1);                    /* the black edge */
    path = 1; bestpath = 1;
    if (D == 0) best = 0;
    dfs(1);
    printf("p=%d d=%d longest_run=%d%s d+run=%d nodes=%lld witness=%llu\n", P, D, best, hitcap ? "(cap)" : "",
           D + best, nodes, bestpath);
    fflush(stdout);
  }
  return 0;
}
