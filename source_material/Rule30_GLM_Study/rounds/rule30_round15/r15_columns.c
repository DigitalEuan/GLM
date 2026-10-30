#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
// bit-packed rule 30 from single seed; output columns -1,0,1 for T steps
int main(int argc,char**argv){
  long T=atol(argv[1]);
  long nbits=2*T+256; long nw=nbits/64+2;
  uint64_t *a=calloc(nw,8),*b=calloc(nw,8);
  long c=T+128; a[c>>6]|=1ULL<<(c&63);
  unsigned char *out=malloc(3*T);
  for(long t=0;t<T;t++){
    for(int j=-1;j<=1;j++){long p=c+j; out[3*t+j+1]=(a[p>>6]>>(p&63))&1;}
    long lo=(c-t-2)>>6, hi=(c+t+2)>>6; if(lo<1)lo=1; if(hi>nw-2)hi=nw-2;
    for(long w=lo;w<=hi;w++){
      uint64_t C=a[w];
      uint64_t L=(C<<1)|(a[w-1]>>63);   // bit i gets bit i-1
      uint64_t R=(C>>1)|(a[w+1]<<63);   // bit i gets bit i+1
      b[w]=L^(C|R);
    }
    uint64_t*tmp=a;a=b;b=tmp;
  }
  fwrite(out,1,3*T,stdout);
}
