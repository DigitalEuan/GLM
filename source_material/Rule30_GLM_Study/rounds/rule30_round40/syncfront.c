/* Round 40: the synchronisation front of two left-edge rows.
 * usage: ./syncfront W T seedA seedB
 * For each D: shift k (|k| <= 64) with A_D(t+k) = B_D(t) on the last 512 steps, and
 * A(D) = least t from which A_D(t'+k) = B_D(t') for all t' >= t; also tau(D) of row A.
 * prints: D k A(D) tauA(D)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char* sim(int W,long T,const char*hx){
  unsigned char*row=calloc(W,1); int n=strlen(hx);
  for(int i=0;i<n;i++){int c=hx[n-1-i];int v=(c<='9')?c-'0':(c|32)-'a'+10;
    for(int b=0;b<4;b++) if(4*i+b<W) row[4*i+b]=(v>>b)&1;}
  unsigned char*h=malloc((size_t)W*T);
  for(long t=0;t<T;t++){ for(int D=0;D<W;D++) h[(size_t)D*T+t]=row[D];
    for(int D=W-1;D>=0;D--){int a=D>=2?row[D-2]:0,b=D>=1?row[D-1]:0; row[D]=a^(b|row[D]);} }
  return h;
}
int main(int argc,char**argv){
  int W=atoi(argv[1]); long T=atol(argv[2]);
  unsigned char*A=sim(W,T,argv[3]),*B=sim(W,T,argv[4]);
  for(int D=0;D<W;D++){
    unsigned char*a=A+(size_t)D*T,*b=B+(size_t)D*T;
    int kk=999;
    for(int k=-64;k<=64&&kk==999;k++){int ok=1;for(long t=T-600;t<T-64;t++) if(a[t+k]!=b[t]){ok=0;break;} if(ok) kk=k;}
    long Ad=-1;
    if(kk!=999){ Ad=0; for(long t=T-65;t>=64;t--) if(a[t+kk]!=b[t]){Ad=t+1;break;} }
    int q=1; while(q<=64){int ok=1;for(long t=T-600;t<T-64;t++) if(a[t]!=a[t+q]){ok=0;break;} if(ok)break; q*=2;}
    long tau=0; for(long t=T-65;t>=0;t--) if(a[t]!=a[t+q]){tau=t+1;break;}
    printf("%d %d %ld %ld\n",D,kk,Ad,tau);
  }
}
