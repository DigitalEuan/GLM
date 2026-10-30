/* Round 22 (EMP, outside Lean): do the checks keep halving the survivors after the edge?
 *
 * For a drive word W of period P and codes of length D (top bit D-1), count the codes that pass
 * every check before time k.  Up to k = D-1 the count is exactly 2^(D-1-blacks(k)) (Lean:
 * survivors_card).  The last column prints survivors(k) * 2^blacks(k) / 2^(D-1): it is exactly 1
 * at k = D-1 by the theorem and stays near 1 afterwards if the later tests still halve.
 * Codes that fail before D-1 are pruned (prefix search), so the column is < 1 before D-1.
 * Build: gcc -O2 -o post_edge_halving post_edge_halving.c
 * Round 31: the ratio is printed exactly as a reduced fraction a/2^e (integer arithmetic only).
 * Usage: ./post_edge_halving P W D     e.g. ./post_edge_halving 2 1 36 */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned __int128 u128;
int P=2; unsigned W; int D; long cnt[400];
static inline int bd(long t){return (W>>(t%P))&1;}
static inline u128 step(int b,u128 S){return (S>>1)^(S|((S<<1)|(u128)b));}
int pfail(u128 Pf,int k){for(int t=0;t<k;t++){int b=bd(t);if(b&&(int)(Pf&1)==bd(t+1))return 1;Pf=step(b,Pf);}return 0;}
void leaf(u128 S){for(int t=0;t<400;t++){cnt[t]++;int b=bd(t);if(b&&(int)(S&1)==bd(t+1))return;S=step(b,S);}}
void dfs(int k,u128 Pf){ if(pfail(Pf,k))return; if(k==D-1){leaf(Pf|((u128)1<<k));return;} dfs(k+1,Pf); dfs(k+1,Pf|((u128)1<<k));}
int main(int c,char**v){P=atoi(v[1]);W=atoi(v[2]);D=atoi(v[3]);dfs(0,0);
 int bl=0; printf("p=%d word=%u d=%d\n k  blacks(k)  survivors(k)  survivors*2^blacks/2^(d-1)\n",P,W,D);
 for(int k=0;k<400&&cnt[k];k++){
   /* exact ratio cnt*2^bl / 2^(D-1), printed as a reduced fraction (Round 31: no floating point) */
   unsigned long long num=(unsigned long long)cnt[k]; int e=(D-1)-bl;
   while(e>0 && !(num&1ULL)){num>>=1;e--;}
   if(e>0) printf("%3d %3d %10ld %llu/2^%d\n",k,bl,cnt[k],num,e);
   else { u128 v=(u128)num<<(-e); printf("%3d %3d %10ld %llu\n",k,bl,cnt[k],(unsigned long long)v); }
   if(bd(k))bl++; if(bl>60)break;} }
