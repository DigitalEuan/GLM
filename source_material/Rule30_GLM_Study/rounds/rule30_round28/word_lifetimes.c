/* Round 28 (EMP, outside Lean): To Do 2 -- longest life Lmax(d) of the half-line machine for one
   periodic drive word, by brute force over all codes of length d (top bit d-1 set).
   Usage: gcc -O2 -o word_lifetimes word_lifetimes.c && ./word_lifetimes P WORD DMAX
   WORD is written cell-time 0 first, e.g. 1110 = black at times 0,1,2 and white at 3 (mod 4).
   Output: word_lifetimes_output.txt (words 10, 110, 1110, 11110, 111110). */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
int main(int argc,char**argv){
  int p=atoi(argv[1]); unsigned w=strtoul(argv[2],0,2); int D=atoi(argv[3]);
  /* argv[2] given as bit string read with bit i = char i */
  w=0; for(int i=0;i<p;i++) if(argv[2][i]=='1') w|=1u<<i;
  for(int d=1; d<=D; d++){
    int best=-1; uint64_t arg=0;
    for(uint64_t S=1ull<<(d-1); S < (1ull<<d); S++){
      u128 X=S; int t=0;
      while(t<400){
        int b=(w>>(t%p))&1, b1=(w>>((t+1)%p))&1;
        if(b && (int)(X&1)==b1) break;
        X=(X>>1)^(X|((X<<1)|b)); t++;
      }
      if(t>best){best=t;arg=S;}
    }
    printf("d=%d Lmax=%d L-d=%d witness=%llu\n",d,best,best-d,(unsigned long long)arg); fflush(stdout);
  }
}
