/* Round 34, To Do 35: exact observer-clock excess of the driven half-line machine.

   Exact integer arithmetic only.  Machine as in HalfLineMachine.lean:
     state S, bit i = cell c-1-i;  halfStep b S = (S >> 1) ^ (S | (S << 1) | b);
     check at time t when drive(t) = 1: bit 0 of the state must differ from drive(t+1).
   For a code S of length d (2^(d-1) <= S < 2^d) the failing test number is
     n(S) = testsBefore(f) + 1, f = first failure time;
   the excess is E(d) = max_S n(S) - d  (TestCountLinear p c holds at d iff E(d) <= c).

   Method: depth-first search over the bits of S, lowest bit first, with the light cone kept
   incrementally: choosing bit j adds the diagonal u + i = j of the space-time triangle, which
   decides the check at time j.  A branch failing at time j <= d-1 is closed.  When all bits are
   chosen the machine is run to its first failure.  No other pruning is used, so the maxima are
   exact (every code of length d is accounted for).

   Compile: gcc -O2 -o test_slack34 test_slack34.c

   Run: ./test_slack34 P K DMIN DMAX      (word = bits of K, period P)
   Output per d: d E(d) n_max witness (hex)
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define MAXD 400
#define W 40
typedef struct { uint64_t w[W]; } bits;

static int P, K, D;
static unsigned char V[MAXD + 2][MAXD + 2]; /* V[u][i], u + i <= j */
static int tb[4096];                        /* testsBefore */
static int best; static bits bestS;
static bits curS;

static int drive(int t) { return (K >> (t % P)) & 1; }

static void step_exact(bits *s, int b) {
  bits r;
  for (int i = 0; i < W; i++) {
    uint64_t sh = s->w[i] >> 1 | (i + 1 < W ? s->w[i + 1] << 63 : 0);
    uint64_t sl = s->w[i] << 1 | (i > 0 ? s->w[i - 1] >> 63 : 0);
    uint64_t t = s->w[i] | sl;
    if (i == 0 && b) t |= 1;
    r.w[i] = sh ^ t;
  }
  *s = r;
}

static int full_fail(const bits *S) {
  bits s = *S;
  for (int t = 0; t < 64 * W - 70; t++) {
    int b = drive(t);
    if (b && (int)(s.w[0] & 1) == drive(t + 1)) return t;
    step_exact(&s, b);
  }
  fprintf(stderr, "NOFAIL p=%d k=%d d=%d\n", P, K, D);
  exit(1);
}

static void print_hex(const bits *s) {
  int top = W - 1; while (top > 0 && !s->w[top]) top--;
  printf("0x%llx", (unsigned long long)s->w[top]);
  for (int i = top - 1; i >= 0; i--) printf("%016llx", (unsigned long long)s->w[i]);
}

/* fill diagonal j given bit value v = S bit j */
static void diag(int j, int v) {
  V[0][j] = (unsigned char)v;
  for (int u = 1; u <= j; u++) {
    int i = j - u;
    int l = V[u - 1][i + 1];
    int c = V[u - 1][i];
    int r = i == 0 ? drive(u - 1) : V[u - 1][i - 1];
    V[u][i] = (unsigned char)(l ^ (c | r));
  }
}

static void dfs(int j) {
  if (j == D) {
    int f = full_fail(&curS);
    int n = tb[f] + 1;
    if (n > best) { best = n; bestS = curS; }
    return;
  }
  for (int v = 0; v <= 1; v++) {
    if (j == D - 1 && v == 0) continue;
    if (v) curS.w[j/64] |= (uint64_t)1 << (j%64); else curS.w[j/64] &= ~((uint64_t)1 << (j%64));
    diag(j, v);
    if (drive(j) && V[j][0] == drive(j + 1)) {
      int n = tb[j] + 1;
      if (n > best) { best = n; bestS = curS; }
    } else dfs(j + 1);
  }
  curS.w[j/64] &= ~((uint64_t)1 << (j%64));
}

int main(int argc, char **argv) {
  if (argc < 5) { fprintf(stderr, "usage: P K DMIN DMAX\n"); return 1; }
  P = atoi(argv[1]); K = atoi(argv[2]);
  int dmin = atoi(argv[3]), dmax = atoi(argv[4]);
  tb[0] = 0;
  for (int t = 0; t + 1 < 4096; t++) tb[t + 1] = tb[t] + drive(t);
  printf("# p=%d k=%d : d E(d) nmax witness\n", P, K);
  for (D = dmin; D <= dmax && D <= MAXD; D++) {
    best = -1; memset(&curS, 0, sizeof curS);
    dfs(0);
    printf("%d %d %d ", D, best - D, best); print_hex(&bestS); printf("\n");
    fflush(stdout);
  }
  return 0;
}
