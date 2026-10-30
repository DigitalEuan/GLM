/* Round 34, To Do 36 (the GLM's pick after Round 34): exact alive counts on the observer's clock.

   For the drive word K of period P and code length d, A_d(n) = number of codes S of length d
   (2^(d-1) <= S < 2^d) that do not fail within their first n tests.  Every code is run (no
   sampling); exact integer arithmetic (unsigned __int128 states, d <= 26).

   Before the edge each test halves A exactly (survivors_card), so A_d(n) = 2^(d-1-n) while the
   n-th test lies before time d - 1.  Printed per d: n_edge = tests before time d - 1, then for each
   n >= n_edge the count A_d(n), until it reaches 0, and the post-edge "bits per test"
     rate = (log2 A_d(n_edge) - 0) / (n_last - n_edge)   as the exact pair (n_last - n_edge, n_edge)
   so that rate > 1 means the deterministic tests after the edge remove more than half on average.

   Run: ./alive_decay34 P K DMIN DMAX
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned __int128 u128;
static int P, K;
static int drive(int t) { return (K >> (t % P)) & 1; }

int main(int argc, char **argv) {
  if (argc < 5) { fprintf(stderr, "usage: P K DMIN DMAX\n"); return 1; }
  P = atoi(argv[1]); K = atoi(argv[2]);
  int dmin = atoi(argv[3]), dmax = atoi(argv[4]);
  printf("# p=%d k=%d: d n_edge A(n_edge) | A(n) for n = n_edge.. until 0 | post-edge tests\n", P, K);
  for (int d = dmin; d <= dmax && d <= 26; d++) {
    static uint64_t cnt[200];  /* cnt[n] = number of codes whose failing test number is n */
    memset(cnt, 0, sizeof cnt);
    int tb[256]; tb[0] = 0;
    for (int t = 0; t < 255; t++) tb[t + 1] = tb[t] + drive(t);
    for (uint64_t S0 = (uint64_t)1 << (d - 1); S0 < ((uint64_t)1 << d); S0++) {
      u128 s = S0; int t;
      for (t = 0; t < 120 - d; t++) {
        int b = drive(t);
        if (b && (int)(s & 1) == drive(t + 1)) break;
        s = (s >> 1) ^ (s | (s << 1) | (u128)b);
      }
      if (t >= 120 - d) { fprintf(stderr, "NOFAIL d=%d\n", d); return 1; }
      cnt[tb[t] + 1]++;
    }
    int ne = tb[d - 1];          /* tests strictly before time d - 1 */
    /* A(n) = number of codes with failing test number > n */
    uint64_t A[200]; uint64_t tot = 0;
    for (int n = 199; n >= 0; n--) { A[n] = tot; tot += cnt[n]; }
    /* note A[n] counts failing test number > n, i.e. alive after n tests */
    int last = ne; while (A[last] > 0) last++;
    printf("%d %d %llu |", d, ne, (unsigned long long)A[ne]);
    for (int n = ne; n <= last; n++) printf(" %llu", (unsigned long long)A[n]);
    printf(" | %d\n", last - ne);
  }
  return 0;
}
