/* Round 22 (EMP, outside Lean): exact machine bounds by the prefix search.
 *
 * Same algorithm as the Lean certificate `prefixSearch` (PrefixSearch.lean): build the code of the
 * d cells left of the column bit by bit from the column outward, drop a prefix as soon as it fails a
 * check (by the light cone its extensions fail too), and simulate each complete code (top bit d-1)
 * to its first failure.  Prints, for every d, the largest first-failure time over all non-zero
 * drive words of period P (the machine bound) and the number of search nodes.
 * It agrees with the Round 21 Lean tables (halfBound d <= 24, machineBound p d) on their ranges.
 * Build: gcc -O2 -o prefix_search prefix_search.c
 * Usage: ./prefix_search P D0 D1      e.g. ./prefix_search 2 1 46 */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned long long u64;
typedef unsigned __int128 u128;
int P; unsigned W;
static inline int bd(long t){return (W>>(t%P))&1;}
static inline u128 step(int b,u128 S){return (S>>1)^(S|((S<<1)|(u128)b));}
/* first failure time of S, cap */
long death(u128 S,long cap){for(long t=0;t<cap;t++){int b=bd(t);if(b && (int)(S&1)==bd(t+1))return t;S=step(b,S);}return -1;}
/* does prefix P (length k) fail before k */
int pfail(u128 Pf,int k){for(int t=0;t<k;t++){int b=bd(t);if(b&&(int)(Pf&1)==bd(t+1))return 1;Pf=step(b,Pf);}return 0;}
long best; long nodes; int D;
void dfs(int k,u128 Pf){nodes++; if(pfail(Pf,k))return; if(k==D-1){long x=death(Pf|((u128)1<<k),100000); if(x<0){printf("SURVIVE\n");exit(1);} if(x>best)best=x;return;}
 dfs(k+1,Pf); dfs(k+1,Pf|((u128)1<<k));}
int main(int c,char**v){P=atoi(v[1]);int D0=atoi(v[2]),D1=atoi(v[3]);
 for(D=D0;D<=D1;D++){long tot=0,mx=0; long nn=0;
  for(W=1;W<(1u<<P);W++){best=-1;nodes=0;dfs(0,0);if(best>mx)mx=best;nn+=nodes;}
  printf("p=%d d=%d bound=%ld nodes=%ld\n",P,D,mx,nn);fflush(stdout);} }
