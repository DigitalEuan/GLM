/* Round 40: iterate the eventual-pattern map F (no white in between) and dump patterns.
 * usage: ./fscan Q Ahex Bhex D_A D1 [D2 ...]   (A at diagonal D_A, B at D_A+1; prints PAT D hex
 * for each requested D, which must be increasing; stops with WHITE D if a white appears first) */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static inline uint64_t F(uint64_t A, uint64_t B, int Q) {
    int phi = __builtin_ctzll(B);
    uint64_t x = 1 ^ ((A >> phi) & 1);
    int ph = (phi + 1) % Q;
    uint64_t C = 0;
    for (int i = 0; i < Q; i++) {
        C |= x << ph;
        x = ((A >> ph) & 1) ^ (((B >> ph) & 1) | x);
        ph = (ph + 1 == Q) ? 0 : ph + 1;
    }
    return C;
}
int main(int argc,char**argv){
  int Q=atoi(argv[1]); uint64_t mask=(Q==64)?~0ULL:((1ULL<<Q)-1);
  uint64_t a=strtoull(argv[2],0,16)&mask,b=strtoull(argv[3],0,16)&mask;
  unsigned long long D=strtoull(argv[4],0,10); /* D = index of a */
  int r=5;
  while(r<argc){
    unsigned long long want=strtoull(argv[r],0,10);
    while(D<want){ if(b==0){printf("WHITE %llu\n",D+1);return 0;} uint64_t c=F(a,b,Q); a=b;b=c;D++; }
    if(D==want){printf("PAT %llu %0*llx\n",D,(Q+3)/4,(unsigned long long)a); r++;}
    else {printf("PAT %llu %0*llx\n",D,(Q+3)/4,(unsigned long long)b); r++;}
  }
  return 0;
}
