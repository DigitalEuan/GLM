#include <stdio.h>
#include <stdlib.h>
#include <math.h>
// H(target | centre window of 2k+1), for target = col+1, col-1, and control = col+1 delayed by 100003
int main(){
  long T=4194304; unsigned char*d=malloc(3*T); FILE*f=fopen("big.bin","rb"); /* produced by: ./r15_columns 4194304 > big.bin */; fread(d,1,3*T,f); fclose(f);
  unsigned char *cm=malloc(T),*c0=malloc(T),*c1=malloc(T);
  for(long t=0;t<T;t++){cm[t]=d[3*t];c0[t]=d[3*t+1];c1[t]=d[3*t+2];}
  long D=100003;
  for(int k=0;k<=9;k++){
    int n=2*k+1; long M=1L<<n;
    long *a=calloc(2*M,8),*b=calloc(2*M,8),*cc=calloc(2*M,8);
    long tot=0;
    for(long t=k+1000;t<T-k-D;t++){unsigned w=0;for(int j=-k;j<=k;j++)w=(w<<1)|c0[t+j];
      a[2*w+c1[t]]++; b[2*w+cm[t]]++; cc[2*w+c1[t+D]]++; tot++;}
    double H[3]; long *arr[3]={a,b,cc};
    for(int q=0;q<3;q++){double h=0; for(long w=0;w<M;w++){long x=arr[q][2*w],y=arr[q][2*w+1],s=x+y; if(x)h-=x*log2((double)x/s); if(y)h-=y*log2((double)y/s);} H[q]=h/tot;}
    printf("k=%d window=%2d  H(col+1|w)=%.4f  H(col-1|w)=%.4f  control(col+1 delayed)=%.4f  [bias-corrected: %.4f %.4f]\n",k,n,H[0],H[1],H[2],H[0]+(1-H[2]),H[1]+(1-H[2]));
    free(a);free(b);free(cc);
  }
}
