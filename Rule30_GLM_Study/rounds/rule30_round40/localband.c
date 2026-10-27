/* Round 40: a stretch of left diagonals driven by known eventual patterns at its outer edge.
 * usage: ./localband Q Ahex Bhex L fillseed [P=128]
 *   cells j = 0..L+1 stand for diagonals w0-2 .. w0+L-1; cells 0,1 are forced to the Q-periodic
 *   patterns A, B (bit t mod Q at time t); cells 2.. start from random bits (fillseed; 0 = white).
 *   Runs until row(t) == row(t-P); prints, for every eventually white cell j >= 2:
 *   "WHITE off parity_outer Qouter PATNEXT hex" with off = j - 2 (offset from w0), and the
 *   eventual pattern of the next cell (phase t mod P) as 128-bit hex (two words).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint64_t u64;
static u64 rng=88172645463325252ULL; static u64 xr(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;}
int main(int argc,char**argv){
  int Q=atoi(argv[1]); u64 A=strtoull(argv[2],0,16),B=strtoull(argv[3],0,16);
  long L=atol(argv[4]); long fs=atol(argv[5]); int P=argc>6?atoi(argv[6]):128;
  long N=L+2; int NW=(N+63)/64+1; int lastw=(N-1)/64; u64 lastmask=(N%64)?((1ULL<<(N%64))-1):~0ULL;
  int R=P+1; u64*ring=calloc((size_t)R*NW,8);
  if(fs){ rng+=fs*0x9E3779B97F4A7C15ULL; for(int w=0;w<=lastw;w++) ring[w]=xr(); ring[lastw]&=lastmask; }
  long t=0;
  for(;;){
    u64*cur=ring+(size_t)(t%R)*NW,*nxt=ring+(size_t)((t+1)%R)*NW;
    cur[0]=(cur[0]&~3ULL)|((A>>(t%Q))&1)|(((B>>(t%Q))&1)<<1);
    u64 c1=0,c2=0;
    for(int w=0;w<=lastw;w++){u64 x=cur[w];u64 s1=(x<<1)|c1,s2=(x<<2)|c2;c1=x>>63;c2=x>>62;nxt[w]=s2^(s1|x);}
    nxt[lastw]&=lastmask;
    t++;
    nxt[0]=(nxt[0]&~3ULL)|((A>>(t%Q))&1)|(((B>>(t%Q))&1)<<1);
    if(t>=P){u64*old=ring+(size_t)((t-P)%R)*NW; if(memcmp(old,nxt,(size_t)(lastw+1)*8)==0) break;}
    if(t>50L*N+100000){printf("NOTSETTLED\n");return 1;}
  }
  long ts=t-P;
  printf("SETTLED %ld\n",ts);
  #define BIT(tt,j) ((ring[(size_t)((tt)%R)*NW+(j)/64]>>((j)%64))&1ULL)
  for(long j=2;j<N-1;j++){
    int white=1; for(int i=0;i<P;i++) if(BIT(ts+i,j)){white=0;break;}
    if(!white) continue;
    long jm=j-1; int q=P;
    while(q>1){int ok=1;int h=q/2;for(int i=0;i<P;i++) if(BIT(ts+i,jm)!=BIT(ts+(i+h)%P,jm)){ok=0;break;} if(!ok)break; q=h;}
    int par=0; for(int i=0;i<q;i++) par^=BIT(ts+i,jm);
    u64 w0=0,w1=0; for(long tt=ts;tt<ts+P;tt++){int ph=tt%P; if(BIT(tt,j+1)){ if(ph<64) w0|=1ULL<<ph; else w1|=1ULL<<(ph-64);} }
    printf("WHITE %ld parity %d Qouter %d PATNEXT %016llx%016llx\n",j-2,par,q,(unsigned long long)w1,(unsigned long long)w0);
  }
  return 0;
}
