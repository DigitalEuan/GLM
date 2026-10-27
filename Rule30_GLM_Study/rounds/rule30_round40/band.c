/* Round 40: simulate the left band of Rule 30 (distances 0..W-1 from the left edge).
 * usage: ./band W T seedhex   (seed bits: bit i = cell at distance i at time 0; bit 0 must be 1)
 * For each diagonal D, records the last L values and prints:
 *   D  Q(eventual period, power of 2, 0 if > L/4)  white  parity  bit  transient_end
 * bit = value at the latest time t with t % Q == 0 (absolute phase).
 * transient_end = last time t (within recorded window) with s[t+Q] != s[t].
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define L 8192
int main(int argc,char**argv){
  int W=atoi(argv[1]); long T=atol(argv[2]); const char*hx=argv[3];
  unsigned char*row=calloc(W,1);
  int n=strlen(hx);
  for(int i=0;i<n;i++){int c=hx[n-1-i];int v=(c<='9')?c-'0':(c|32)-'a'+10;
    for(int b=0;b<4;b++) if(4*i+b<W) row[4*i+b]=(v>>b)&1;}
  unsigned char*hist=calloc((size_t)W*L,1);
  for(long t=0;t<T;t++){
    if(t>=T-L) for(int D=0;D<W;D++) hist[(size_t)D*L+(t-(T-L))]=row[D];
    for(int D=W-1;D>=0;D--){
      int a=D>=2?row[D-2]:0, b=D>=1?row[D-1]:0;
      row[D]=a^(b|row[D]);
    }
  }
  long t0=T-L;
  for(int D=0;D<W;D++){
    unsigned char*s=hist+(size_t)D*L;
    int Q=0;
    for(int q=1;q<=L/4;q*=2){int ok=1;for(int i=L/2;i+q<L;i++) if(s[i]!=s[i+q]){ok=0;break;}
      if(ok){Q=q;break;}}
    int white=1;for(int i=L/2;i<L;i++) if(s[i]){white=0;break;}
    int par=0,bit=-1;long tend=-1;
    if(Q){ for(int i=L-Q;i<L;i++) par^=s[i];
      for(int i=L-1;i>=0;i--) if((t0+i)%Q==0){bit=s[i];break;}
      for(int i=L-1-Q;i>=0;i--) if(s[i]!=s[i+Q]){tend=t0+i;break;}
    }
    printf("%d %d %d %d %d %ld\n",D,Q,white,par,bit,tend);
  }
  return 0;
}
