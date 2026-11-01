/* Round 16 (EMP): shape of the influence (damage) cone of Rule 30.
   Two rows that differ in one cell are evolved side by side; the leftmost and rightmost
   differing cells are recorded.  Proved in Lean (ConeGeometry.lean): the right edge moves at
   exactly speed 1 on every row; the left edge can move at speed 1 (white row) or 0 (a wall).
   Here: the left-edge speed on random rows (fair coin) and on the rows of the seed's own run.
   Usage: ./r16_damage_cone T trials                                                        */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
static uint64_t s = 88172645463325252ULL;
static int rnd(void) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return s & 1; }
static void step(unsigned char *a, unsigned char *b, int n) {
  b[0] = b[n - 1] = 0;
  for (int i = 1; i < n - 1; i++) b[i] = a[i - 1] ^ (a[i] | a[i + 1]);
}
int main(int argc, char **argv) {
  int T = atoi(argv[1]), trials = atoi(argv[2]);
  int n = 2 * T + 8, c = T + 4;
  unsigned char *x = malloc(n), *y = malloc(n), *x2 = malloc(n), *y2 = malloc(n);
  double sumL[8] = {0}, sumR[8] = {0}; int cnt = 0, rightExact = 1;
  int marks[8]; for (int k = 0; k < 8; k++) marks[k] = T >> (7 - k);
  for (int tr = 0; tr < trials; tr++) {
    for (int i = 0; i < n; i++) x[i] = rnd();
    memcpy(y, x, n); y[c] ^= 1;
    int k = 0;
    for (int t = 1; t <= T; t++) {
      step(x, x2, n); step(y, y2, n);
      unsigned char *tmp; tmp = x; x = x2; x2 = tmp; tmp = y; y = y2; y2 = tmp;
      int lo = -1, hi = -1;
      for (int i = c - t - 1; i <= c + t + 1; i++) if (x[i] != y[i]) { if (lo < 0) lo = i; hi = i; }
      if (hi != c + t) rightExact = 0;
      if (k < 8 && t == marks[k]) { sumL[k] += (lo < 0 ? 0 : c - lo) / (double)t; sumR[k] += (hi - c) / (double)t; k++; }
    }
    cnt++;
  }
  printf("random rows, %d trials, T=%d\n", trials, T);
  printf("right edge equal to +t at every step in every trial: %s\n", rightExact ? "yes" : "NO");
  for (int k = 0; k < 8; k++)
    printf("  t=%6d  mean left speed %.4f   mean right speed %.4f\n", marks[k], sumL[k] / cnt, sumR[k] / cnt);
  return 0;
}
