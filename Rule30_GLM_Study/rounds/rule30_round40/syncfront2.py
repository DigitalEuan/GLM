import subprocess, random
random.seed(3)
W=2000; T=3200
seedB = format(random.getrandbits(1999) | 1, "x")
Ds=list(range(0,W,97))
def get(seed):
    out = subprocess.run(["./probe", str(W), str(T), seed] + [str(d) for d in Ds], capture_output=True, text=True).stdout.split("\n")
    return {int(l.split()[0]): l.split()[1] for l in out if l}
A=get("1"); B=get(seedB)
for D in Ds:
    a,b=A[D],B[D]
    best=None
    for k in range(-300,301):
        # b(t) = a(t-k) on the tail
        ok=all(b[t]==a[t-k] for t in range(T-400,T) if 0<=t-k<T)
        if ok:
            # agreement start
            st=0
            for t in range(T-1,-1,-1):
                if 0<=t-k<T and b[t]!=a[t-k]: st=t+1;break
            if best is None or st<best[1]: best=(k,st)
    print(D, best)
