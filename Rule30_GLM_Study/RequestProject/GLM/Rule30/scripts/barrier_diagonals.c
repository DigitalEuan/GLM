/* Round 31, To Do 3: which left diagonal ends the longest run of the driven half-line machine,
   and does it depend on the drive word?

   Exact integer arithmetic only (unsigned __int128 bit vectors); no floating point, no random
   numbers, no hashing.

   Machine (HalfLineMachine.lean): state S, bit i = cell c-1-i;
     halfStep b S = (S >> 1) ^ (S | (S << 1) | b);
   check at time t when the drive is black: bit 0 of the state must differ from drive(t+1).
   Drive driveN p k t = bit (t mod p) of k.

   For each word (p, k) and each length d (codes 2^(d-1) <= S < 2^d) we report
     Lmax(d) = the largest first-failure time over all codes of length d   (failure at time t
               means the check at time t fails; dDiesBy S (t+1) = true, dDiesBy S t = false),
   and the diagonal index  d + Lmax(d)  (distance from the moving left edge at the moment of
   failure).  Compile: gcc -O2 -o barrier_diagonals barrier_diagonals.c
*/
#include <stdio.h>
#include <stdlib.h>

typedef unsigned __int128 u128;

static int drive(int p, int k, int t) { return (k >> (t % p)) & 1; }

/* first failure time of code S (or -1 if none before maxT) */
static int first_fail(int p, int k, u128 S, int maxT) {
  for (int t = 0; t < maxT; t++) {
    int b = drive(p, k, t);
    if (b && (int)(S & 1) == drive(p, k, t + 1)) return t;
    S = (S >> 1) ^ (S | (S << 1) | (u128)b);
  }
  return -1;
}

int main(int argc, char **argv) {
  int D = argc > 1 ? atoi(argv[1]) : 22;
  int words[][2] = {{2, 1}, {3, 1}, {3, 3}, {4, 1}, {4, 3}, {4, 7}};
  int nw = sizeof(words) / sizeof(words[0]);
  printf("# d  then for each word (p,k): Lmax(d):diagonal d+Lmax(d):first code attaining Lmax(d)\n# words:");
  for (int w = 0; w < nw; w++) printf(" (%d,%d)", words[w][0], words[w][1]);
  printf("\n");
  for (int d = 1; d <= D; d++) {
    printf("%2d", d);
    for (int w = 0; w < nw; w++) {
      int p = words[w][0], k = words[w][1];
      int best = -1; unsigned long long wit = 0;
      u128 lo = (u128)1 << (d - 1), hi = (u128)1 << d;
      for (u128 S = lo; S < hi; S++) {
        int f = first_fail(p, k, S, 8 * d + 64);
        if (f < 0) { printf("  NOFAIL"); best = -2; break; }
        if (f > best) { best = f; wit = (unsigned long long)S; }
      }
      printf("  %3d:%3d:%llu", best, d + best, wit);
    }
    printf("\n");
    fflush(stdout);
  }
  return 0;
}
