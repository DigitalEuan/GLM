/* Round 40: record the time series of a few left diagonals (bit-packed band).
 * usage: ./probe W T seedhex D1 D2 ...   -> for each D: line "D <string of T bits>" */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char**argv){
  int W=atoi(argv[1]); long T=atol(argv[2]); const char*hx=argv[3];
  int nd=argc-4; int*Ds=malloc(nd*sizeof(int)); for(int i=0;i<nd;i++) Ds[i]=atoi(argv[4+i]);
  char**out=malloc(nd*sizeof(char*)); for(int i=0;i<nd;i++){out[i]=malloc(T+1); out[i][T]=0;}
  int NW=(W+63)/64+1; uint64_t*a=calloc(NW,8),*b=calloc(NW,8);
  int n=strlen(hx);
  for(int i=0;i<n;i++){int c=hx[n-1-i];int v=(c<='9')?c-'0':(c|32)-'a'+10;
    for(int k=0;k<4;k++){int d=4*i+k; if(d<W && ((v>>k)&1)) a[d/64]|=1ULL<<(d%64);}}
  int lastw=(W-1)/64; uint64_t lastmask=(W%64)?((1ULL<<(W%64))-1):~0ULL;
  for(long t=0;t<T;t++){
    for(int i=0;i<nd;i++) out[i][t]='0'+((a[Ds[i]/64]>>(Ds[i]%64))&1);
    uint64_t c1=0,c2=0;
    for(int w=0;w<=lastw;w++){uint64_t x=a[w];uint64_t s1=(x<<1)|c1,s2=(x<<2)|c2;c1=x>>63;c2=x>>62;b[w]=s2^(s1|x);}
    b[lastw]&=lastmask; uint64_t*tmp=a;a=b;b=tmp;
  }
  for(int i=0;i<nd;i++) printf("%d %s\n",Ds[i],out[i]);
}
