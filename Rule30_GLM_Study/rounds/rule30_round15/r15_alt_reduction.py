"""Round 15, period-2 forcing (illustration; the exact statements are proved in Lean, TileLeads.lean).

If column c alternates 1010..., the Lean theorems show:
  column c-1 = 1 at even times and = not u(k) at time 2k+1,
  column c-2 = u(k) at times 2k and 2k+1 (one free bit per two steps),
  column c-3 = complement of column c-2 one step later,
and every column further left follows by solving Rule 30 for its left input.
This script takes a random half-speed sequence u and prints columns c, c-1, ..., c-11.
Row j of the output is column c-j; character t is time t.
"""
import random
# column c alternating a(t)=1 for even t; columns c-1, c-2 from u; solve leftwards
T=200
def build(u,J):
    # cols[j][t] = x_t(c-j)
    a=[1 if t%2==0 else 0 for t in range(T+J+2)]
    c1=[1 if t%2==0 else 1-u[t//2] for t in range(T+J+2)]
    c2=[u[t//2] for t in range(T+J+2)]
    cols=[a,c1,c2]
    for j in range(3,J):
        R=cols[j-2];C=cols[j-1]
        L=[C[t+1]^(C[t]|R[t]) for t in range(len(C)-1)]
        cols.append(L)
    return cols
random.seed(1)
u=[random.randint(0,1) for _ in range(400)]
cols=build(u,12)
for j,col in enumerate(cols):
    print(j,''.join(map(str,col[:80])))
# check consistency of col c-1 and c-2 with rule from col c-3
