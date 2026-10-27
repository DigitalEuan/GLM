/* Round 33, To Do 30 and the observer-clock law: exact longest lives Lmax_w(d) of the driven
   half-line machine, for drive words w of period p.

   Exact integer arithmetic only (multi-word unsigned bit vectors); no floating point, no random
   numbers, no hashing.

   Machine (HalfLineMachine.lean): state S, bit i = cell c-1-i;
     halfStep b S = (S >> 1) ^ (S | (S << 1) | b);
   check at time t when drive(t) = 1: bit 0 of the state must differ from drive(t+1);
   drive(t) = bit (t mod p) of k  (driveN p k).

   Lmax_w(d) = the largest first-failure time over all codes 2^(d-1) <= S < 2^d.  The failing
   test is test number testsBefore(Lmax) + 1 (TestCountLaw.lean); the observer-clock excess is
   that number minus d.

   Method: depth-first search over the bits of S, lowest bit first.  Bit 0 of the state at time t
   depends only on bits 0..t of S (light cone), so after bits 0..j are chosen the check at time j
   is decided; a branch failing at time j <= d-1 is closed with first-failure time j.  When all d
   bits are chosen the machine is run to its first failure.  This is the sound prefix search of
   PrefixSearch.lean, used here to find exact maxima.

   Compile: gcc -O2 -o word_lifetimes33 word_lifetimes33.c
   Run:     ./word_lifetimes33 PMAX DMAX [PMIN [ALL]]
            ALL = 0 (default): one word per rotation class (the smallest k), primitive words only;
            ALL = 1: every non-white word k < 2^p.
   Output:  one line per word: "word p=P k=K blacks=B : d:Lmax(d):witness ..." (witness = the
            first code found attaining Lmax(d), low 64 bits; d <= 64).
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define W 12 /* 12 * 64 = 768 bits of state; a code of length d is followed for < 768 - d steps */
typedef struct { uint64_t w[W]; } bits;

static int P, K, D, ALL;
static int best; static bits bestS;

static int drive(int t) { return (K >> (t % P)) & 1; }

static void step_exact(bits *s, int b) {
  bits r;
  for (int i = 0; i < W; i++) {
    uint64_t sh = s->w[i] >> 1 | (i + 1 < W ? s->w[i + 1] << 63 : 0);   /* S >> 1 */
    uint64_t sl = s->w[i] << 1 | (i > 0 ? s->w[i - 1] >> 63 : 0);        /* S << 1 */
    uint64_t t = s->w[i] | sl;
    if (i == 0 && b) t |= 1;                                              /* | b */
    r.w[i] = sh ^ t;
  }
  *s = r;
}

static int bit0(const bits *s) { return (int)(s->w[0] & 1); }
static void setbit(bits *s, int i) { s->w[i / 64] |= (uint64_t)1 << (i % 64); }
static void clrbit(bits *s, int i) { s->w[i / 64] &= ~((uint64_t)1 << (i % 64)); }

/* first failure time of code S, scanning times from t0 (all earlier checks known to pass) */
static int first_fail_from(const bits *S0, int t0, int maxT) {
  bits s = *S0;
  for (int t = 0; t < maxT; t++) {
    int b = drive(t);
    if (t >= t0 && b && bit0(&s) == drive(t + 1)) return t;
    step_exact(&s, b);
  }
  return -1;
}

/* check at time t only, for the partial code S (bits > t irrelevant) */
static int fails_at(const bits *S0, int t) {
  int b = drive(t);
  if (!b) return 0;
  bits s = *S0;
  for (int u = 0; u < t; u++) step_exact(&s, drive(u));
  return bit0(&s) == drive(t + 1);
}

static void dfs(bits *S, int j) { /* bits 0..j-1 chosen */
  if (j == D) {
    int f = first_fail_from(S, D, 64 * W - D - 2); /* stay inside the 768-bit state */
    if (f < 0) { fprintf(stderr, "NOFAIL within the state width: p=%d k=%d d=%d\n", P, K, D); exit(1); }
    if (f > best) { best = f; bestS = *S; }
    return;
  }
  for (int v = 0; v <= 1; v++) {
    if (j == D - 1 && v == 0) continue; /* top bit is 1 */
    if (v) setbit(S, j); else clrbit(S, j);
    if (fails_at(S, j)) {
      if (j > best) { best = j; bestS = *S; }
    } else dfs(S, j + 1);
  }
  clrbit(S, j);
}

static int canonical(int p, int k) { /* smallest rotation */
  int m = k;
  for (int r = 1; r < p; r++) {
    int kr = ((k >> r) | (k << (p - r))) & ((1 << p) - 1);
    if (kr < m) m = kr;
  }
  return m == k;
}
static int primitive(int p, int k) { /* not a repetition of a shorter word */
  for (int q = 1; q < p; q++) {
    if (p % q) continue;
    int ok = 1;
    for (int t = 0; t < p; t++) if (((k >> t) & 1) != ((k >> (t % q)) & 1)) { ok = 0; break; }
    if (ok) return 0;
  }
  return 1;
}

int main(int argc, char **argv) {
  int PMAX = argc > 1 ? atoi(argv[1]) : 5;
  int DMAX = argc > 2 ? atoi(argv[2]) : 24;
  int PMIN = argc > 3 ? atoi(argv[3]) : 1;
  ALL = argc > 4 ? atoi(argv[4]) : 0;
  printf("# word = (p,k)%s; blacks b; per d: Lmax(d) and witness code\n",
         ALL ? " (every non-white word)" : " primitive, smallest rotation");
  for (P = PMIN; P <= PMAX; P++) for (K = 1; K < (1 << P); K++) {
    if (!ALL && (!canonical(P, K) || !primitive(P, K))) continue;
    int b = __builtin_popcount(K);
    printf("word p=%d k=%d blacks=%d :", P, K, b);
    for (D = 1; D <= DMAX; D++) {
      bits S; memset(&S, 0, sizeof S);
      best = -1;
      dfs(&S, 0);
      unsigned long long wit = bestS.w[0];
      printf(" %d:%d:%llu", D, best, wit);
      fflush(stdout);
    }
    printf("\n");
  }
  return 0;
}
