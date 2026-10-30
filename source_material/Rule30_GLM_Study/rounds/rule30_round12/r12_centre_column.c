/* Round 12 (EMP, exact): the Rule 30 centre column from one black cell, bit-packed, to T steps.
 * Writes one byte per bit (0/1) to the output file, so it can be checked against
 * data/cc_1M.npy (first 10^6 bits) and the Lean certificate wobble_1e6 = 1536.
 * Build: gcc -O3 -march=native -o r12_centre_column r12_centre_column.c
 * Run:   ./r12_centre_column 4000000 cc_4M.bin                                          */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(int argc, char **argv) {
  long T = argc > 1 ? atol(argv[1]) : 1000000;
  const char *out = argc > 2 ? argv[2] : "cc.bin";
  long W = (2 * T + 256) / 64 + 2, off = W * 32;           /* cell c lives at bit off + c */
  uint64_t *x = calloc(W, 8), *y = calloc(W, 8);
  x[off / 64] |= 1ULL << (off % 64);
  unsigned char *col = malloc(T);
  for (long t = 0; t < T; t++) {
    col[t] = (x[off / 64] >> (off % 64)) & 1;
    long lo = (off - t - 2) / 64, hi = (off + t + 2) / 64;   /* active words */
    if (lo < 1) lo = 1; if (hi > W - 2) hi = W - 2;
    for (long i = lo; i <= hi; i++) {
      uint64_t c = x[i];
      uint64_t L = (c << 1) | (x[i - 1] >> 63);              /* cell to the left = lower bit */
      uint64_t R = (c >> 1) | (x[i + 1] << 63);
      y[i] = L ^ (c | R);
    }
    uint64_t *tmp = x; x = y; y = tmp;
  }
  FILE *f = fopen(out, "wb"); fwrite(col, 1, T, f); fclose(f);
  long s = 0; for (long t = 0; t < T; t++) s += col[t];
  printf("T=%ld wobble=%ld\n", T, 2 * s - T);
  return 0;
}
