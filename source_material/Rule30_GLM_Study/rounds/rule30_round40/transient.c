/* Round 40: exact transients of the Rule 30 left diagonals for a left-edge seed.
 * usage: ./transient W T seedhex
 * prints: D Q white parity bit tau   where tau = least t with s(t'+Q)=s(t') for all t'>=t
 * (Q = least power-of-two eventual period seen in the second half; 0 = not found).
 * bit = value at times t>=tau with t%Q==0.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char**argv){
  int W=atoi(argv[1]); long T=atol(argv[2]); const char*hx=argv[3];
  unsigned char*row=calloc(W,1); int n=strlen(hx);
  for(int i=0;i<n;i++){int c=hx[n-1-i];int v=(c<='9')?c-'0':(c|32)-'a'+10;
    for(int b=0;b<4;b++) if(4*i+b<W) row[4*i+b]=(v>>b)&1;}
  unsigned char*h=malloc((size_t)W*T);
  for(long t=0;t<T;t++){
    for(int D=0;D<W;D++) h[(size_t)D*T+t]=row[D];
    for(int D=W-1;D>=0;D--){int a=D>=2?row[D-2]:0,b=D>=1?row[D-1]:0; row[D]=a^(b|row[D]);}
  }
  for(int D=0;D<W;D++){
    unsigned char*s=h+(size_t)D*T; int Q=0;
    for(int q=1;q<=T/4;q*=2){int ok=1;for(long i=T/2;i+q<T;i++) if(s[i]!=s[i+q]){ok=0;break;} if(ok){Q=q;break;}}
    long tau=-1; int white=0,par=0,bit=-1;
    if(Q){ tau=0; for(long i=T-1-Q;i>=0;i--) if(s[i]!=s[i+Q]){tau=i+1;break;}
      white=1; for(long i=T-Q;i<T;i++){ if(s[i]) white=0; par^=s[i]; }
      for(long i=T-1;i>=0;i--) if(i%Q==0){bit=s[i];break;} }
    printf("%d %d %d %d %d %ld\n",D,Q,white,par,bit,tau);
  }
}
