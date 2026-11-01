/* Round 6: the reduced parity count (EMP evidence beyond the Lean range).
 *
 * whiteDiagonalCount(n) counts rows supported on [2-n, n-1] that are white along the
 * diagonal (k, n-1-k), k < n.  Lean (`ParityReduction.lean`, `whiteDiagonalCount_eq_reduced`)
 * proves that scanning right to left, the cells n-1, n-3, ..., 3-n are FORCED and only the
 * n-1 cells n-2, n-4, ..., 2-n are free; the count is the number of free patterns whose
 * forced value at the outside cell 1-n is white.
 *
 * This program runs that scan with left-moving diagonals packed into 64-bit words:
 *   e_{j-1}(k) = x_{j-1} XOR (XOR_{i<k} (e_j(i) OR e_{j+1}(i)))
 * (diagonal j holds the cells (k, j+k)), forcing x_{j-1} when j-1 = n-1-2k.
 * Usage: ./a.out LO HI   prints "n count parity".  Valid for n <= 63.
 * Cross-checked against brute force for n <= 7 (r6_parity_bruteforce_check.py) and, for
 * n <= 21, against values of the Lean function `fastReducedCount` (its parity is proved odd
 * in Lean for n <= 20).
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
typedef uint64_t u64;
static int n; static u64 mask; static long long cnt;
static inline u64 pxor(u64 y){ y^=y<<1; y^=y<<2; y^=y<<4; y^=y<<8; y^=y<<16; y^=y<<32; return y;}
// j = current diagonal index already computed (e_j=a, e_{j+1}=b); compute e_{j-1}
static void rec(int j, u64 a, u64 b){
  int jm=j-1;
  u64 P = (pxor(a|b)<<1) & mask;
  int d = n-1-jm; // forced iff d even, k=d/2
  if (d%2==0){ int k=d/2; int x=(P>>k)&1;
    if (jm==1-n){ if(!x) cnt++; return; }
    u64 e = P ^ (x?mask:0); rec(jm,e,a);
  } else {
    rec(jm,P,a); rec(jm,P^mask,a);
  }
}
int main(int argc,char**argv){ int lo=atoi(argv[1]),hi=atoi(argv[2]);
 for(n=lo;n<=hi;n++){ mask = (n>=64)?~0ULL:((1ULL<<n)-1); cnt=0;
   // e_n=e_{n+1}=0; compute e_{n-1}: forced, d=0,k=0, P=0 => x=0, e=0
   rec(n,0,0);
   printf("%d %lld %lld\n",n,cnt,cnt%2); fflush(stdout);}
}
