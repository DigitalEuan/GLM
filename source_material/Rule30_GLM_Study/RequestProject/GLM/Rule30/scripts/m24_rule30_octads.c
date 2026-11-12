/* Round 32 (EMP tool): Rule 30 futures of the 759 octads on the ring of 24 cells.
 *
 * The 759 octads of the GLM Golay code form ONE orbit of M24 (MathieuOrbitsData.orbit_octads).
 * This program runs Rule 30 on the 24-cell ring (cell j reads j-1, j, j+1, indices mod 24;
 * new = L xor (C or R)) from each octad and reports the transient length mu and the cycle
 * length lambda (Brent's algorithm), and the weight after one step.
 * Exact integer arithmetic only; no floating point, no randomness, no hashing.
 *
 * The octads are generated from the 12 generator rows (ShortcutNetworkData.golayRows).
 * Build and run:  gcc -O2 m24_rule30_octads.c -o m24_rule30_octads && ./m24_rule30_octads
 */
#include <stdio.h>
#include <stdint.h>

#define MASK 0xFFFFFFu
static const uint32_t rows[12] = {16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
                                  14299200, 15536256, 7770368, 3887616, 1946624, 9361408};

static uint32_t r30(uint32_t x) {
  uint32_t L = ((x << 1) | (x >> 23)) & MASK; /* bit j holds cell j-1 */
  uint32_t R = ((x >> 1) | (x << 23)) & MASK; /* bit j holds cell j+1 */
  return (L ^ (x | R)) & MASK;
}

int main(void) {
  uint32_t oct[759];
  int n = 0;
  for (uint32_t m = 0; m < 4096; m++) {
    uint32_t x = 0;
    for (int j = 0; j < 12; j++)
      if (m >> j & 1) x ^= rows[j];
    if (__builtin_popcount(x) == 8) oct[n++] = x;
  }
  /* sort octads */
  for (int i = 1; i < n; i++)
    for (int j = i; j > 0 && oct[j - 1] > oct[j]; j--) { uint32_t t = oct[j]; oct[j] = oct[j - 1]; oct[j - 1] = t; }
  uint32_t lams[64]; int lamcount[64]; int nl = 0;
  long w1[25] = {0};
  printf("octads: %d\n", n);
  printf("octad  weight_after_1_step  transient_mu  cycle_lambda\n");
  for (int i = 0; i < n; i++) {
    uint32_t x = oct[i];
    uint32_t power = 1, lam = 1, t = x, h = r30(x);
    while (t != h) { if (power == lam) { t = h; power *= 2; lam = 0; } h = r30(h); lam++; }
    uint32_t a = x, b = x;
    for (uint32_t k = 0; k < lam; k++) b = r30(b);
    uint32_t mu = 0;
    while (a != b) { a = r30(a); b = r30(b); mu++; }
    int w = __builtin_popcount(r30(x));
    w1[w]++;
    printf("%u %d %u %u\n", x, w, mu, lam);
    int f = 0;
    for (int k = 0; k < nl; k++) if (lams[k] == lam) { lamcount[k]++; f = 1; }
    if (!f) { lams[nl] = lam; lamcount[nl++] = 1; }
  }
  printf("cycle lengths reached (lambda: number of octads):");
  for (int k = 0; k < nl; k++) printf(" %u:%d", lams[k], lamcount[k]);
  printf("\nweights after one step (w: number of octads):");
  for (int w = 0; w <= 24; w++) if (w1[w]) printf(" %d:%ld", w, w1[w]);
  printf("\n");
  return 0;
}
