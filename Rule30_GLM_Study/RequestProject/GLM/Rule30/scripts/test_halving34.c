/* Round 33, To Do 34 (first step): halving on the observer's clock.

   For a drive word of period p (driveN p k) and a code length d, let A_d(n) be the number of
   codes S with 2^(d-1) <= S < 2^d that do NOT fail within their first n tests (tests = black
   drive times; TestCountLaw.lean, FailsWithinTests).  The halving statement with excess e,

       TestHalving p e :  A_d(n) * 2^n <= 2^(d-1+e)   for every word of period p, every d, n,

   gives A_d(d+e) * 2^(d+e) <= 2^(d-1+e), so A_d(d+e) = 0: every code fails within d + e tests,
   i.e. TestCountLinear p e.  This program measures, per word and d, the least such e
   (e_d = the least e with A_d(n) * 2^n <= 2^(d-1+e) for all n) and the slack c_d (the largest
   failing test number minus d), so that e_d >= c_d always.

   Exact integer arithmetic only (unsigned __int128 states, 64-bit counts); every code of
   length d is run, no sampling.

   Machine (HalfLineMachine.lean): halfStep b S = (S >> 1) ^ (S | (S << 1) | b); at a time t with
   drive(t) = 1 the check is: bit 0 of S differs from drive(t+1).  Bit 0 at time t depends only
   on bits 0..t of the code, and a code of length d <= 24 fails within 128 - d steps on every
   word run here (checked: the program aborts otherwise).

   Compile: gcc -O2 -o test_halving34 test_halving34.c
   Run:     ./test_halving34 PMAX DMAX
   Output:  per word "p k word : d:c_d:e_d ..." then per period the largest c and e.
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef unsigned __int128 u128;

static int P, K;
static int drive(int t) { return (K >> (t % P)) & 1; }

/* the number of the failing test (1-based), or -1 if no failure within maxt steps */
static int fail_test(u128 S, int maxt) {
  int tests = 0;
  for (int t = 0; t < maxt; t++) {
    int b = drive(t);
    if (b) {
      tests++;
      if ((int)(S & 1) == drive(t + 1)) return tests;
    }
    S = (S >> 1) ^ (S | (S << 1) | (u128)b);
  }
  return -1;
}

int main(int argc, char **argv) {
  int PMAX = argc > 1 ? atoi(argv[1]) : 4, DMAX = argc > 2 ? atoi(argv[2]) : 20;
  if (DMAX > 26) { fprintf(stderr, "DMAX <= 26\n"); return 1; }
  int bestc[16] = {0}, beste[16] = {0};
  for (P = 1; P <= PMAX; P++)
    for (K = 1; K < (1 << P); K++) {
      printf("p=%d k=%d word=", P, K);
      for (int i = 0; i < P; i++) printf("%d", (K >> i) & 1);
      printf(" :");
      for (int d = 1; d <= DMAX; d++) {
        static uint64_t hist[256];
        for (int i = 0; i < 256; i++) hist[i] = 0;
        int maxn = 0;
        for (uint64_t S = 1ULL << (d - 1); S < (1ULL << d); S++) {
          int n = fail_test((u128)S, 128 - d);
          if (n < 0) { fprintf(stderr, "no failure: p=%d k=%d S=%llu\n", P, K,
                               (unsigned long long)S); return 2; }
          hist[n]++;
          if (n > maxn) maxn = n;
        }
        /* A(n) = number failing at a test > n; e_d = least e with A(n) 2^n <= 2^(d-1+e) */
        int e = -64;
        uint64_t alive = 1ULL << (d - 1);
        for (int n = 0; n <= maxn; n++) {
          if (n > 0) alive -= hist[n];
          if (alive == 0) break;
          /* least e with alive * 2^n <= 2^(d-1+e): e >= n - (d-1) + ceil(log2 alive) */
          int lg = 0;
          while ((1ULL << lg) < alive) lg++;
          int need = n - (d - 1) + lg;
          if (need > e) e = need;
        }
        int c = maxn - d;
        printf(" %d:%d:%d", d, c, e);
        if (c > bestc[P] || (K == 1 && d == 1)) bestc[P] = c > bestc[P] ? c : bestc[P];
        if (e > beste[P] || (K == 1 && d == 1)) beste[P] = e > beste[P] ? e : beste[P];
      }
      printf("\n");
      fflush(stdout);
    }
  for (int p = 1; p <= PMAX; p++)
    printf("period %d: largest slack c = %d, largest halving excess e = %d (d <= %d)\n", p,
           bestc[p], beste[p], DMAX);
  return 0;
}
