/* Round 12 (EMP, exact): reading the Rule 30 seed pattern along lines parallel to the edges.
 * Left diagonal D at time t is the cell D - t (D cells inside the always-black left edge);
 * right diagonal D at time t is the cell t - D.  For each D, the least eventual period p (checked
 * on t in [T/2, T)) and the preperiod: the first time from which the diagonal repeats with period p
 * up to T.  The centre column reads diagonal D (on either side) at time t = D.
 * Lean: ldiag_eventually_periodic (ReadAngle.lean), rdiag_periodic (Diagonals.lean) prove that
 * every diagonal is eventually periodic; the values below are computed, not proved.
 * Build: gcc -O2 -o r12_read_angle r12_read_angle.c ; Run: ./r12_read_angle > r12_read_angle_output.txt */
#include <stdio.h>
#include <stdlib.h>
#define T 60000
#define DM 201
static unsigned char L[DM][T], R[DM][T];
static int period(unsigned char *s) {
  for (int p = 1; p < T / 4; p++) { int ok = 1;
    for (int i = T / 2; i < T - p; i++) if (s[i] != s[i + p]) { ok = 0; break; }
    if (ok) return p; }
  return -1;
}
static int preperiod(unsigned char *s, int p) {
  int pre = T / 2; while (pre > 0 && s[pre - 1] == s[pre - 1 + p]) pre--; return pre;
}
int main(void) {
  int size = 2 * T + 8, off = T + 4;
  unsigned char *x = calloc(size, 1), *y = calloc(size, 1); x[off] = 1;
  for (int t = 0; t < T; t++) {
    for (int D = 0; D < DM; D++) { L[D][t] = (D <= 2 * t) ? x[off - t + D] : 0;
                                   R[D][t] = (D <= 2 * t) ? x[off + t - D] : 0; }
    for (int c = off - t - 1; c <= off + t + 1; c++) y[c] = x[c - 1] ^ (x[c] | x[c + 1]);
    unsigned char *tmp = x; x = y; y = tmp;
  }
  printf("# T = %d steps; D, left period, left preperiod, right period, right preperiod\n", T);
  for (int D = 0; D < DM; D++) {
    int pl = period(L[D]), pr = period(R[D]);
    printf("%d %d %d %d %d\n", D, pl, pl > 0 ? preperiod(L[D], pl) : -1, pr,
           pr > 0 ? preperiod(R[D], pr) : -1);
  }
  return 0;
}
