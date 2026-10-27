/* Round 40: law-driven left side of Rule 30 with settling times (hypothesis H7).
 * State per diagonal: eventual pattern p (Q-periodic, absolute phase t mod Q) and a certified
 * settling time sigma (the diagonal is Q-periodic from sigma).
 *   non-white D-1: M = max(sigma[D-2], sigma[D-1]); s = first t >= M with p[D-1](t) = 1;
 *                  sigma[D] = s + 1; p[D] from the reset value u(s+1) = !p[D-2](s).
 *   white D-1 = w:  s = first t >= max(sigma[w-2], sigma[w-1]) with a(t) = 1, a = p[w-2];
 *                  H7: u_w(s) = 1, so d(s+1) = 0; then d(t+1) = a(t) xor d(t).
 * usage: ./recur Dmax  -> prints WHITE D Qouter parity BIT p[D+1](0) sigma[D]
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned long long u64;
static int Q=1;
static inline int bit(u64 p,long t){return (p>>(t%Q))&1;}
static u64 dbl(u64 p){return p|(p<<Q);} /* re-express with period 2Q (Q<=32) */
int main(int argc,char**argv){
  long Dmax=atol(argv[1]);
  u64 p2=1,p1=1; long s2=0,s1=1; /* diagonals 0 and 1: all black; settle 0 and 1 */
  for(long D=2;D<=Dmax;D++){
    u64 pD=0; long sD;
    long M=s2>s1?s2:s1;
    if(p1!=0){
      long s=M; while(!bit(p1,s)) s++;
      sD=s+1; int x=!bit(p2,s);
      for(long t=s+1;t<s+1+Q;t++){ if(x) pD|=1ULL<<(t%Q); x=bit(p2,t)^(bit(p1,t)|x); }
    } else {
      /* p1 white: D-1 = w; a = p2 */
      long s=M; while(!bit(p2,s)) s++;   /* a has a black (w-2 = w-1 not white) */
      int par=__builtin_popcountll(p2)&1;
      if(par){ if(Q==64){printf("Q overflow at %ld\n",D);return 1;} p2=dbl(p2); Q*=2; }
      sD=s+1; int x=0;
      for(long t=s+1;t<s+1+Q;t++){ if(x) pD|=1ULL<<(t%Q); x=bit(p2,t)^x; }
      if(par) p1=0; /* white stays white */
    }
    if(pD==0){
      int par=__builtin_popcountll(p1)&1;
      /* bit of D+1 reported at the next step; print now pattern-level info */
      printf("WHITE %ld Q %d parity %d sigma %ld\n",D,Q,par,sD);
    }
    if(p2!=0 && p1==0 && pD!=0){ printf("  BIT after white %ld: p(0)=%d\n",D-1,(int)(pD&1)); }
    p2=p1; p1=pD; s2=s1; s1=sD;
    if(D%100000000==0){fprintf(stderr,"D=%ld Q=%d\n",D,Q);}
  }
  return 0;
}
