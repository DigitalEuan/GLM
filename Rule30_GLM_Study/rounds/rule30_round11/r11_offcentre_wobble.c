/* Round 11 (EMP, exact): wobble D_c(N) of columns c = -5..5 of Rule 30 from one black cell, to N = 10^6,
 * and the chirality gap D_c(N) - D_-c(N).  Build: gcc -O2 -o r11_offcentre_wobble r11_offcentre_wobble.c */
#include <stdio.h>
#include <stdlib.h>
#define T 1000000
int main(){ int size=2*T+8, off=T+4; unsigned char *x=calloc(size,1),*y=calloc(size,1); x[off]=1;
 long W[11]={0}; int first[6]={-1,-1,-1,-1,-1,-1}; long maxgap[6]={0};
 for(long t=0;t<T;t++){
   for(int c=-5;c<=5;c++) W[c+5]+= x[off+c]?1:-1;
   for(int c=1;c<=5;c++){ long g=W[c+5]-W[5-c]; if(g!=0&&first[c]<0) first[c]=t+1; if(labs(g)>maxgap[c]) maxgap[c]=labs(g);}
   long N=t+1; if(N==100||N==1000||N==10000||N==100000||N==1000000){ printf("N=%ld",N); for(int c=-5;c<=5;c++) printf(" D%d=%ld",c,W[c+5]); printf("\n");}
   int lo=off-t-2, hi=off+t+2; for(int j=lo;j<=hi;j++) y[j]=x[j-1]^(x[j]|x[j+1]); unsigned char*tmp=x;x=y;y=tmp; }
 for(int c=1;c<=5;c++) printf("c=%d first N with D_c != D_-c : %d ; max|gap| to 1e6: %ld\n",c,first[c],maxgap[c]); }
