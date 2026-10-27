/* Round 23 (EMP): GF(2) rank of the N x N Hankel matrix (a(i+j)) of the Rule 30 centre column.
 *
 * Used to choose N for the Lean certificate `hankel_centerCol_det_ne_zero` (N = 10000) in
 * `PowerSeriesLadderData.lean`; the Lean side re-checks the result independently (a proposed
 * inverse is verified bitwise), so nothing here is trusted.
 *
 * Build: gcc -O2 -o hankel_rank hankel_rank.c
 * Usage: ./hankel_rank N1 N2 ...   (prints "N rank"; N <= 10000; N = 10000 takes about 2 s)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define M 20000
unsigned char a[M];
int main(int argc, char **argv) {
  int W = 2 * M + 10;
  unsigned char *r = calloc(W, 1), *s = calloc(W, 1);
  r[M + 5] = 1;
  for (int t = 0; t < M; t++) {
    a[t] = r[M + 5];
    for (int i = 1; i < W - 1; i++) s[i] = r[i - 1] ^ (r[i] | r[i + 1]);
    memcpy(r, s, W);
  }
  for (int ai = 1; ai < argc; ai++) {
    int N = atoi(argv[ai]);
    int w = (N + 63) / 64;
    uint64_t *A = calloc((size_t)N * w, 8);
    for (int i = 0; i < N; i++)
      for (int j = 0; j < N; j++)
        if (a[i + j]) A[(size_t)i * w + j / 64] |= 1ULL << (j % 64);
    int rk = 0;
    for (int c = 0; c < N && rk < N; c++) {
      int piv = -1;
      for (int i = rk; i < N; i++)
        if (A[(size_t)i * w + c / 64] >> (c % 64) & 1) { piv = i; break; }
      if (piv < 0) continue;
      if (piv != rk)
        for (int k = 0; k < w; k++) {
          uint64_t t = A[(size_t)piv * w + k];
          A[(size_t)piv * w + k] = A[(size_t)rk * w + k];
          A[(size_t)rk * w + k] = t;
        }
      for (int i = rk + 1; i < N; i++)
        if (A[(size_t)i * w + c / 64] >> (c % 64) & 1)
          for (int k = c / 64; k < w; k++) A[(size_t)i * w + k] ^= A[(size_t)rk * w + k];
      rk++;
    }
    printf("%d %d\n", N, rk);
    fflush(stdout);
    free(A);
  }
  return 0;
}
