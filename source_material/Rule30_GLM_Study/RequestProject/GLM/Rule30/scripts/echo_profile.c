// Round 26 (EMP): the echo profile of the Rule 30 centre column to large n.
//
// Purpose: the tuning excess n - tuneCost(n) of Round 25 equals the length of the longest suffix
// of the first n centre bits that occurred earlier (EchoBound.lean, excess_le_iff_not_echo).
// This program computes the centre column (bit-packed Rule 30) and that "longest echo" for every
// prefix with a suffix automaton (linear time), and reports the records and the largest value of
// echo(n) - (2 log2 n + 2), i.e. whether TuneExcessLog holds up to N.
//
// Usage: gcc -O2 -o echo_profile echo_profile.c && ./echo_profile 1000000 > echo_profile_output.txt
// (about 20 s for N = 10^6). Output is EMP: the certified range is n <= 131072
// (ConjectureLoopData.lean, tuneExcessLog_upto_131072).
// centre column of Rule 30 (bit-packed), then longest-repeated-suffix profile via suffix automaton
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long long u64;
int main(int argc,char**argv){
  long N=atol(argv[1]);
  long W=(2*N+130)/64+2; // cells span
  u64*a=calloc(W,8),*b=calloc(W,8);
  long C=W*32; // centre bit index
  a[C/64]|=1ULL<<(C%64);
  char*s=malloc(N);
  for(long t=0;t<N;t++){
    s[t]=(a[C/64]>>(C%64))&1;
    // new = L xor (C or R) ; bit i = cell i, L = cell i-1, R=cell i+1
    long lo=(C-t-2)/64-1, hi=(C+t+2)/64+1; if(lo<1)lo=1; if(hi>W-2)hi=W-2;
    for(long w=lo;w<=hi;w++){
      u64 x=a[w]; u64 L=(x<<1)|(a[w-1]>>63); u64 R=(x>>1)|(a[w+1]<<63);
      b[w]=L^(x|R);
    }
    u64*tmp=a;a=b;b=tmp;
  }
  // suffix automaton over binary alphabet
  long M=2*N+2; int *len=malloc(M*4),*link=malloc(M*4),*nx=malloc(M*2*4);
  long sz=1,last=0; len[0]=0;link[0]=-1;nx[0]=nx[1]=-1;
  int best=0; long bestn=0; int worstslack=-1000; long worstn=0;
  int okA=1;
  for(long n=0;n<N;n++){
    int c=s[n]; long cur=sz++; len[cur]=len[last]+1; nx[2*cur]=nx[2*cur+1]=-1;
    long p=last; while(p!=-1 && nx[2*p+c]==-1){nx[2*p+c]=cur;p=link[p];}
    if(p==-1) link[cur]=0; else { long q=nx[2*p+c]; if(len[p]+1==len[q]) link[cur]=q; else {
      long cl=sz++; len[cl]=len[p]+1; nx[2*cl]=nx[2*q]; nx[2*cl+1]=nx[2*q+1]; link[cl]=link[q];
      while(p!=-1 && nx[2*p+c]==q){nx[2*p+c]=cl;p=link[p];} link[q]=link[cur]=cl; } }
    last=cur;
    long m=n+1; int ex=len[link[cur]]; // excess at prefix length m
    int lg=0; while((1L<<(lg+1))<=m) lg++;
    int slack=ex-(2*lg+2);
    if(ex>best){best=ex;bestn=m; printf("new max excess %d at n=%ld (2log2+2=%d)\n",ex,m,2*lg+2);}
    if(slack>worstslack){worstslack=slack;worstn=m;}
  }
  printf("N=%ld max excess %d at %ld; max(excess-(2log2n+2))=%d at n=%ld\n",N,best,bestn,worstslack,worstn);
}
