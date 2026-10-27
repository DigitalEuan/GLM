/* Round 14: the Rule 30 centre column c(0..N-1) from the single black cell, written as one
 * byte (0/1) per step.  Bit-parallel (64 cells per word); only cells inside both the forward
 * light cone of the seed and the backward light cone of the last centre cell are updated.
 *   gcc -O3 -o r14_centre r14_centre.c && ./r14_centre 1048576 centre.bin [offset]
 * The optional offset k writes column k instead of the centre column (|k| small).         */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(int argc, char **argv) {
  long N = atol(argv[1]);
  long k = argc > 3 ? atol(argv[3]) : 0;
  long W = (2 * N + 2) / 64 + 3;           /* words; cell i lives at bit position i + N + 64 */
  uint64_t *a = calloc(W, 8), *b = calloc(W, 8);
  long off = N + 64;
  a[off / 64] |= 1ULL << (off % 64);
  unsigned char *out = malloc(N);
  for (long t = 0; t < N; t++) {
    out[t] = (a[(off + k) / 64] >> ((off + k) % 64)) & 1;
    long r = t < N - 1 - t ? t + 1 : N - 1 - t;  /* cells needed at time t+1 */
    r += (k < 0 ? -k : k) + 1;
    long lo = (off - r) / 64 - 1, hi = (off + r) / 64 + 1;
    if (lo < 1) lo = 1; if (hi > W - 2) hi = W - 2;
    for (long w = lo; w <= hi; w++) {
      uint64_t c = a[w];
      uint64_t L = (c << 1) | (a[w - 1] >> 63);  /* bit k of L = cell k-1 */
      uint64_t R = (c >> 1) | (a[w + 1] << 63);  /* bit k of R = cell k+1 */
      b[w] = L ^ (c | R);
    }
    uint64_t *tmp = a; a = b; b = tmp;
    /* clear words outside the updated range in the new a (b may hold stale data) */
    a[lo - 1] = 0; a[hi + 1] = 0;
  }
  FILE *f = fopen(argv[2], "wb"); fwrite(out, 1, N, f); fclose(f);
  return 0;
}
