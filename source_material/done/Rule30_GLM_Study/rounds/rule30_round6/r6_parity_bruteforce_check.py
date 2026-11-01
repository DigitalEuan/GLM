import itertools
def rule(L,C,R): return L^(C|R)
def wdc(n):
    lo,hi=2-n,n-1; cnt=0
    for bits in itertools.product([0,1],repeat=hi-lo+1):
        x={lo+i:b for i,b in enumerate(bits)}
        row=lambda c: x.get(c,0)
        cur={c:row(c) for c in range(lo-n-2,hi+n+3)}
        ok=True
        for k in range(n):
            if cur[n-1-k]: ok=False;break
            cur={c:rule(cur.get(c-1,0),cur.get(c,0),cur.get(c+1,0)) for c in range(lo-n-2,hi+n+3)}
        cnt+=ok
    return cnt
for n in range(2,8): print(n,wdc(n))
