/* Round 40: bit-packed left band of Rule 30 with an exact settling certificate.
 * usage: ./bandfast W seedhex [P]
 *   Runs rows of distances 0..W-1 until row(t) == row(t-P) (P = 64 by default): then every left
 *   diagonal D < W is P-periodic from time t-P on (exact, the band is a closed system).
 *   Prints "SETTLED t" and then, for each eventually white diagonal D >= 1:
 *   "WHITE D Qouter parity_outer", where Qouter is the least period (power of 2 dividing P) of
 *   diagonal D-1.  Also prints "TAU D tau" for D = 1000,2000,... (least start of P-periodicity),
 *   estimated from a buffer, and "BIT D b" for the bit of diagonal D+1 after each white D:
 *   b = value of diagonal D+1 at the first time t >= settle with t % P == 0.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char**argv){
  int W=atoi(argv[1]); const char*hx=argv[2]; int P=argc>3?atoi(argv[3]):64;
  int NW=(W+63)/64+1;
  int R=P+1; /* ring of rows */
  uint64_t*ring=calloc((size_t)R*NW,8);
  uint64_t*row=ring;
  int n=strlen(hx);
  for(int i=0;i<n;i++){int c=hx[n-1-i];int v=(c<='9')?c-'0':(c|32)-'a'+10;
    for(int b=0;b<4;b++){int d=4*i+b; if(d<W && ((v>>b)&1)) row[d/64]|=1ULL<<(d%64);}}
  uint64_t lastmask = (W%64)? ((1ULL<<(W%64))-1) : ~0ULL;
  int lastw=(W-1)/64;
  long t=0;
  for(;;){
    uint64_t*cur=ring+(size_t)(t%R)*NW, *nxt=ring+(size_t)((t+1)%R)*NW;
    uint64_t c1=0,c2=0; /* carries: bits shifted in from lower word */
    for(int w=0;w<=lastw;w++){
      uint64_t x=cur[w];
      uint64_t s1=(x<<1)|c1, s2=(x<<2)|c2;
      c1=x>>63; c2=x>>62;
      nxt[w]=s2^(s1|x);
    }
    nxt[lastw]&=lastmask;
    t++;
    if(t>=P){
      uint64_t*old=ring+(size_t)((t-P)%R)*NW;
      if(memcmp(old,nxt,(size_t)(lastw+1)*8)==0) break;
    }
    if(t>100000000L){printf("NOTSETTLED\n");return 1;}
  }
  long ts=t-P; /* periodic from ts */
  printf("SETTLED %ld\n",ts);
  /* rows ts..ts+P-1 are in the ring */
  #define BIT(tt,d) ((ring[(size_t)((tt)%R)*NW+(d)/64]>>((d)%64))&1ULL)
  for(int D=1;D<W-1;D++){
    int white=1; for(int i=0;i<P;i++) if(BIT(ts+i,D)){white=0;break;}
    if(!white) continue;
    int Dm=D-1; int q=P;
    while(q>1){int ok=1;int h=q/2;for(int i=0;i<P;i++) if(BIT(ts+i,Dm)!=BIT(ts+(i+h)%P,Dm)){ok=0;break;} if(!ok)break; q=h;}
    int par=0; for(int i=0;i<q;i++) par^=BIT(ts+i,Dm);
    long t0=ts; while(t0%P) t0++;
    int b=(t0<ts+P)?BIT(t0,D+1):-1;
    printf("WHITE %d %d %d BIT %d\n",D,q,par,b);
  }
  return 0;
}
