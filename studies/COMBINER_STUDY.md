# XOR: what it is doing here, what it costs, and what could replace it

**The question.** XOR keeps turning up in this system, and the objection is a
fair one. `a ^ b` throws away which of the two operands supplied each bit: from
the result you cannot recover the pair. If the substrate is meant to be exact,
an operation that loses information is exactly the sort of thing that should be
justified rather than assumed. So: is XOR a *choice*, and could something else
be used?

This document is the answer. It has three parts, and each is a theorem in
[`RequestProject/GLM/Combiner.lean`](../RequestProject/GLM/Combiner.lean)
rather than an argument here. The computational half is
`glm_universal.reasoning.combiner`, the test that pins it is
`overlay/glm_universal/tests/test_combiner.py`, and the whole thing prints with

```
PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession; \
print(GeometricSession().ask('report combiner').answer)"
```

**The short answer.** XOR is not a choice where the system uses it: on the
carrier the substrate actually runs on it is the only coordinatewise combiner
available, up to a constant. What it loses is real, exactly measurable, and
unavoidable at that output width — every map from pairs of 24-bit words to
single 24-bit words loses at least as much. Where more was wanted, the system
already stopped using XOR: two sites, both replaced, both kept only so they can
report their own loss. And if the loss is not wanted anywhere else, the fix is
not a different Boolean operation but a **wider output**, which is the integer
layer of §4.

---

## 1. On the code, XOR is forced

Restrict to *coordinatewise binary Boolean* combiners: a function
`f : Bool → Bool → Bool` applied bit by bit. There are exactly sixteen. Ask
which of them carry a pair of Golay codewords to a Golay codeword.

`GLM.Combiner.closed_iff_affine` answers it: **the code is closed under `f` if
and only if `f` is affine over `F₂`**, that is `f x y = c₀ ⊕ c₁x ⊕ c₂y`. There
are eight of those, and every one of them is a symmetric difference of the
operands with a constant:

| `(c₀,c₁,c₂)` | operation | value |
| --- | --- | --- |
| `(0,0,0)` | `false` | `0` |
| `(0,1,0)` | `a` | `a` |
| `(0,0,1)` | `b` | `b` |
| `(0,1,1)` | `xor` | `a Δ b` |
| `(1,0,0)` | `true` | all-ones |
| `(1,1,0)` | `not-a` | complement of `a` |
| `(1,0,1)` | `not-b` | complement of `b` |
| `(1,1,1)` | `xnor` | complement of `a Δ b` |

The other eight — `and`, `or`, `nand`, `nor`, both implications and both
negated implications — all leave the code. The witness in the Lean file is
explicit and minimal: `octadA = {0,1,2,4,5,6,10,13}` and
`octadB = {0,1,3,4,5,9,11,14}` are both codewords, their intersection has
weight 4, and the code has minimum weight 8, so the intersection cannot be a
codeword (`inter_not_codeword`). Every non-affine operation is `and` plus an
affine part (`affine_or_inter`), so that single witness kills all eight.

So the honest statement is: *there is nothing to swap XOR for.* Among
coordinatewise combiners, "combine two words and stay in the code" and "take a
symmetric difference, possibly complemented" are the same instruction. XOR is
the group law of `F₂²⁴`, and the code is a subgroup; that is the whole content.

The reason the closure argument works in the affine direction is worth stating
because it is the reusable half: an affine `f` builds
`c₀·1 ⊕ c₁·a ⊕ c₂·b`, the code is linear, and it contains the all-ones word
(`isCodeword_univ`), so the result is a codeword for every pair. Closure under
complement is a fact about *this* code — a linear code that did not contain
all-ones would be closed only under the four non-constant affine operations.

`combiner.closure_report()` recomputes the table and finds a witness for each
of the eight non-affine operations, so the classification and the failure are
both exhibited rather than asserted.

---

## 2. What XOR loses, exactly

XOR is **uniformly `2²⁴`-to-one**. Fixing the first operand determines the
second, so the fibre over every target word is a copy of the whole carrier:
`GLM.Combiner.xor_fibre_card` proves
`#{(a,b) : a Δ b = t} = 2²⁴ = 16,777,216` for every `t`, via an explicit
bijection `xorFibreEquiv`. There is no target that is easier or harder to hit;
the loss is the same everywhere.

Twenty-four bits in each operand, forty-eight bits in, twenty-four bits out:
**twenty-four bits discarded**. That is not a small number and there is no point
pretending otherwise.

But it is also not XOR's fault. There are `2⁴⁸` ordered pairs and only `2²⁴`
words, so by pigeonhole *any* function from pairs to words has a fibre of size
at least `2⁴⁸/2²⁴ = 2²⁴`. `GLM.Combiner.exists_large_fibre` proves it for an
arbitrary `f : Word × Word → Word`, using `Equiv.sigmaFiberEquiv` and
`Fintype.card_sigma`. XOR attains that bound and does so uniformly, which is the
best behaviour available: no clever combiner into a 24-bit word loses less, and
any that is not uniform loses *more* somewhere.

`combiner.fibre_report()` records the counts, and `small_fibre_census()` runs
the same statement outright at width 4, where all `256` pairs fit in memory and
every fibre is found to have size `16`.

**So the finding is: the loss belongs to the width of the output, not to the
operation.** Complaining about XOR is complaining about asking two words to
become one word.

---

## 3. Where XOR actually occurs in the runtime

`combiner.XOR_SITES` is the inventory: every module of the package that
contains a Python `^`, found by parsing the syntax tree — a `^` inside a
docstring or a regular expression is not a XOR site — with the role it plays
there. `combiner.xor_inventory()` re-runs the scan and **fails if a module has
started using XOR without being classified**, so the inventory cannot silently
go stale.

As the tree stands there are 31 non-test modules and 117 uses, in four roles:

| role | modules | meaning |
| --- | --- | --- |
| group law | 26 | addition in `F₂ⁿ`: the code's own operation. One operand plus the result gives the other back, so nothing is lost that was not already a choice of basepoint |
| metric | 11 | inside `popcount(a ^ b)`, i.e. a Hamming distance. A metric is *supposed* to forget which point was which |
| digest | 1 | an integrity checksum (`migration/state.py`). D3: addresses integrity, not meaning |
| retired | 2 | a place where XOR *was* a lossy combiner and no longer is |

(The role counts sum to more than 31 because several modules do two of these.
The totals move as the tree moves; what the test pins is that the inventory is
complete and that the retired class still has exactly two members.)

The two retired sites are the ones the objection was really about, and both
were already replaced before this study:

* **`substrate/superposition.py: bundle_f2`.** Bundling a hypothesis space by
  XOR-ing its candidates. For a complete six-fold tie the result is *always*
  the all-ones word, whatever was received — the bundle carries no information
  about the input at all. Replaced by `bundle_rational`, the coordinatewise
  mean as an exact `Fraction`, which is invertible on the tie. The XOR version
  is kept because its degeneracy is the reported result
  (`RequestProject/GLM/Superposition.lean`).
* **`reasoning/monster_stack.py: compose_xor`.** Plane-wise XOR of two Monster
  addresses. For a `2A` pair `(u,v)` the Sakuma product is
  `(1/8)(a_u + a_v − a_{u^v})`; the shortcut keeps the label `u ^ v` and drops
  the other two terms, the sign and the coefficient. Replaced by
  `product.axis_product`; the shortcut is kept so that `shortcut_loss_report`
  can count exactly what it discarded, and `terms_discarded_by_xor` is that
  count.

Everything else is one of the first three roles, where XOR is either forced (it
is the group operation) or intended (it is inside a distance) or irrelevant to
meaning (it is a checksum).

---

## 4. If the loss is not wanted, widen the output

The constructive half. XOR loses the *overlap*: `a Δ b` cannot tell
`{0,1} , {0,2}` from `{2} , {1}`. Keep the overlap by refusing to reduce mod 2.

The **coordinatewise integer sum** `tsum(a,b) ∈ {0,1,2}²⁴` does exactly that,
and both classical operations come back out of it:

* the coordinates where it is `2` are `a ∩ b` (`GLM.Combiner.tsum_inter`);
* the coordinates where it is `1` are `a Δ b` (`tsum_symmDiff`).

So `tsum` strictly refines XOR. Its image is all of `{0,1,2}²⁴`
(`tsum_surjective`), which is `3²⁴ = 282,429,536,481` states — and
`2³⁸ < 3²⁴ < 2³⁹` (`three_pow_bounds`), so the integer layer carries about
**fourteen more bits** than the binary one, for the price of a carrier that is
ternary rather than binary.

Fourteen extra bits is not twenty-four, and it cannot be: `3²⁴ < 2⁴⁸`, so the
integer sum is still not injective on pairs (`{0} , {1}` and `{1} , {0}` have
the same sum). If nothing at all is to be lost, carry the **signed difference**
`tdiff(a,b) ∈ {−1,0,1}²⁴` as well. Then
`a = (tsum + tdiff)/2` and `b = (tsum − tdiff)/2`, and the map
`(a,b) ↦ (tsum, tdiff)` is injective (`tsum_tdiff_injective`). Nothing at all
need be lost — at the cost of a carrier twice as wide, which is the honest
price of not losing anything.

`combiner.integer_layer_report()` checks all of this on the code's own words:
XOR and the intersection are recovered from `tsum`, and the pair is recovered
from `(tsum, tdiff)`, on every pair drawn from a deterministic sample.

**One caveat, recorded rather than buried.** The code is *not* closed under
`tsum` — the sum of two codewords is a ternary vector and the notion of
codeword does not apply to it. That is the trade. Staying inside the code
forces the affine operations of §1; leaving the code buys the overlap back. A
combiner cannot do both, and the choice is a choice about which layer the
answer is wanted at.

---

## 5. What this settles

1. **XOR is not creeping in.** Of the 31 modules that use it, 26 use it as the
   group law of a code or lattice, 11 use it inside a Hamming distance, one
   uses it as a checksum, and the only two that ever used it as a combiner have
   already been replaced. The inventory is machine-checked against the tree.
2. **Where it is used as the group law, no alternative exists.** Of the sixteen
   coordinatewise Boolean combiners the code is closed under exactly the eight
   affine ones, and all eight are symmetric difference with a constant.
3. **The loss is `2²⁴`-to-one, uniformly, and is a lower bound for any
   combiner of the same output width.** The right complaint is not about XOR
   but about the width.
4. **A wider output recovers what was lost.** `tsum` recovers the overlap for
   `3²⁴` states; `(tsum, tdiff)` recovers the pair outright. Both are available
   and neither is currently on a hot path, because nothing in the runtime
   currently needs the overlap.
5. **This is a layer question, which is the general point of the positioning
   note.** XOR is exact at the layer it lives on and lossy as a map between
   layers; the loss is a property of the projection, and the way to see past it
   is to read one layer up, not to look for a better Boolean operation.

---

## 6. Where each claim lives

| claim | Lean | Python |
| --- | --- | --- |
| the code is closed under exactly the affine combiners | `closed_iff_affine` | `closure_report` |
| an affine combiner is a symmetric difference with a constant | `apply2_affine` | `affine_coefficients` |
| a non-affine combiner is affine plus `and` | `affine_or_inter` | — |
| the witness: two octads meeting in four cells | `inter_not_codeword` | `closure_witness` |
| XOR is uniformly `2²⁴`-to-one | `xor_fibre_card` | `xor_fibre_size`, `small_fibre_census` |
| no combiner into the carrier does better | `exists_large_fibre` | `fibre_report` |
| the intersection is where the integer sum is 2 | `tsum_inter` | `tsum_inter` |
| the symmetric difference is where it is 1 | `tsum_symmDiff` | `tsum_symm_diff` |
| the integer layer has `3²⁴` states, between `2³⁸` and `2³⁹` | `card_ternary`, `three_pow_bounds` | `integer_layer_report` |
| the pair is recovered from `(tsum, tdiff)` | `tsum_tdiff_injective` | `recover_pair` |
| every XOR site in the runtime is classified | — | `xor_inventory` |
