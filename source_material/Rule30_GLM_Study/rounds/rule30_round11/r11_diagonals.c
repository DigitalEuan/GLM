/* Round 11 (EMP, exact): the right diagonals rdiag D t = a(t)(t - D) of Rule 30 from one black
 * cell, D = 0..39, t < 2^17.  For each diagonal: least period (a power of two dividing 2^D,
 * Lean rdiag_periodic), black cells per period, and whether it is ANTI-periodic
 * (rdiag D (t + P/2) = not rdiag D t for every t checked).
 * Build: gcc -O2 -o r11_diagonals r11_diagonals.c && ./r11_diagonals > r11_diagonals_output.txt */
#include <stdio.h>
#include <stdlib.h>
#define T (1 << 17)
#define ND 40
int main(void) {
  int size = 2 * T + 8, off = T + 4;
  unsigned char *x = calloc(size, 1), *y = calloc(size, 1);
  unsigned char *d = calloc((size_t)ND * T, 1);
  x[off] = 1;
  for (int t = 0; t < T; t++) {
    for (int D = 0; D < ND; D++) d[(size_t)D * T + t] = x[off + t - D];
    int lo = off - t - 2, hi = off + t + 2;
    for (int j = lo; j <= hi; j++) y[j] = x[j - 1] ^ (x[j] | x[j + 1]);
    unsigned char *tmp = x; x = y; y = tmp;
  }
  printf("D least_period ones_per_period anti_periodic\n");
  for (int D = 0; D < ND; D++) {
    unsigned char *s = d + (size_t)D * T;
    int p;
    for (p = 1; p < T; p *= 2) {
      int ok = 1;
      for (int i = 0; i + p < T; i++) if (s[i] != s[i + p]) { ok = 0; break; }
      if (ok) break;
    }
    long ones = 0;
    for (int i = 0; i < p; i++) ones += s[i];
    int anti = 0;
    if (p >= 2) {
      anti = 1;
      for (int i = 0; i + p / 2 < T; i++) if (s[i + p / 2] == s[i]) { anti = 0; break; }
    }
    printf("%d %d %ld %s\n", D, p, ones, anti ? "yes" : "no");
  }
  return 0;
}
