"""
The ¢ (cent) intermediate representation — v2.0 (Computational Depth expansion).

Decomposes a £ (abstract operation) into a normalized DAG of ¢ primitives.

=== v1.0: 8 atomic + 4 composite ===
  ¢_sum, ¢_neg, ¢_mult, ¢_scale, ¢_accum, ¢_rate, ¢_wrap, ¢_spatial
  ¢_recip, ¢_div, ¢_sqrt, ¢_eq

=== v2.0: 8 new atomic + 2 new composite (Computational Depth) ===
  ¢_exp         y = e^a           (diode I-V, Nernst, Arrhenius)
  ¢_log         y = ln(a)         (log compression, dB)
  ¢_sat         y = tanh(a)       (saturation, clipping)
  ¢_hysteresis  y = H(a, state)   (B-H loop, backlash, ferroelectric)
  ¢_grad        y = ∇ψ            (thermal/field gradient)
  ¢_div_spatial y = ∇·A           (divergence, flux conservation)
  ¢_curl        y = ∇×A           (Maxwell, vorticity)
  ¢_delay       y(t) = a(t-τ)     (acoustic/optical delay, transport)
  ¢_translinear y = a^b           = ¢_log → ¢_mult → ¢_exp
  ¢_state_space ẋ = Ax + Bu       = coupled ¢_accum + ¢_scale + ¢_sum
"""
from __future__ import annotations
import ast
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Set, Tuple, FrozenSet

# ---------------------------------------------------------------------------
# 0. Vocabulary constants (v2.0 — expanded)
# ---------------------------------------------------------------------------

# All recognized ¢ primitive names
ATOMIC_PRIMITIVES = frozenset({
    "sum", "neg", "mult", "scale", "accum", "rate", "wrap", "spatial",
    # v2.0 expansions:
    "exp", "log", "sat", "hysteresis", "grad", "div_spatial", "curl", "delay",
})

COMPOSITE_PRIMITIVES = frozenset({
    "recip", "div", "sqrt", "eq",
    # v2.0 expansions:
    "translinear", "state_space",
})

ALL_PRIMITIVES = ATOMIC_PRIMITIVES | COMPOSITE_PRIMITIVES

# Function-call preprocessing: convert standard math functions to ¢ ops
FUNCTION_PREPROCESSING = {
    "exp": "exp",       # exp(x) → ¢_exp(x)
    "log": "log",       # log(x) → ¢_log(x)
    "ln": "log",        # ln(x) → ¢_log(x)
    "tanh": "sat",      # tanh(x) → ¢_sat(x)
    "sqrt": "sqrt",     # sqrt(x) → x**(1/2) (existing, handled in Pow)
}


def preprocess_formula(expr: str) -> str:
    """Preprocess a formula string: convert function calls to ¢-compatible form.

    exp(x) → _exp(x)  (parsed as a Call node, handled by the decomposer)
    log(x) → _log(x)
    tanh(x) → _sat(x)
    sqrt(x) → (x)**(1/2)  (existing preprocessing)
    """
    import re
    # sqrt → power
    expr = re.sub(r'\bsqrt\s*\(([^)]+)\)', r'(\1)**(1/2)', expr)
    # exp/log/tanh → prefixed function calls (handled by decomposer's Call visitor)
    # (These are left as-is; the decomposer recognizes them)
    return expr


# ---------------------------------------------------------------------------
# 1. The ¢ graph data structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class COp:
    """One node in the ¢ DAG."""
    op: str                      # one of the 8 atomic + 4 composite ops
    inputs: Tuple[str, ...]      # input variable names (or 'const:k' for constants)
    output: str                  # output variable name
    const: Optional[Fraction] = None  # for ¢_scale; the constant k

    def signature(self) -> Tuple:
        """A hashable signature ignoring variable names — just the op shape."""
        if self.op == "scale":
            return ("scale", self.const)
        return (self.op, len(self.inputs))


@dataclass
class CGraph:
    """A normalized ¢ DAG."""
    ops: List[COp] = field(default_factory=list)
    inputs: Set[str] = field(default_factory=set)   # declared inputs (leaves)
    outputs: Set[str] = field(default_factory=set)  # declared outputs (roots)

    def signature(self) -> Tuple:
        """A canonical signature for isomorphism testing.

        Two CGraphs with the same signature are ¢-isomorphic under some name
        bijection. The signature is the sorted multiset of op signatures.
        """
        return tuple(sorted(op.signature() for op in self.ops))

    def name_multiset(self) -> FrozenSet[str]:
        """All variable names appearing in the graph."""
        names: Set[str] = set()
        for op in self.ops:
            for i in op.inputs:
                if not i.startswith("const:"):
                    names.add(i)
            names.add(op.output)
        return frozenset(names)

    def render(self) -> str:
        lines = []
        for n in sorted(self.inputs):
            lines.append(f"  input  {n}")
        for op in self.ops:
            ins = ", ".join(op.inputs)
            if op.op == "scale":
                lines.append(f"  {op.output:<14s} = {op.const} * ({ins})")
            else:
                lines.append(f"  {op.output:<14s} = {op.op}({ins})")
        for n in sorted(self.outputs):
            lines.append(f"  output {n}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. The decomposer: parse a formula AST and build a normalized ¢ DAG
# ---------------------------------------------------------------------------

class Decomposer:
    """Walks a parsed monomial AST and emits ¢ ops. Each subexpression gets
    a fresh intermediate variable name."""

    def __init__(self):
        self.ops: List[COp] = []
        self.inputs: Set[str] = set()
        self.outputs: Set[str] = set()
        self._counter = 0

    def _fresh(self, hint: str = "t") -> str:
        self._counter += 1
        return f"_{hint}{self._counter}"

    def visit(self, node) -> str:
        """Return the variable name holding this node's value."""
        if isinstance(node, ast.Name):
            # an input variable
            self.inputs.add(node.id)
            return node.id

        # v2.0: handle function calls (exp, log, tanh, etc.)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ("exp",):
                arg = self.visit(node.args[0])
                out = self._fresh("exp")
                self.ops.append(COp("exp", (arg,), out))
                return out
            elif func_name in ("log", "ln"):
                arg = self.visit(node.args[0])
                out = self._fresh("log")
                self.ops.append(COp("log", (arg,), out))
                return out
            elif func_name in ("tanh",):
                arg = self.visit(node.args[0])
                out = self._fresh("sat")
                self.ops.append(COp("sat", (arg,), out))
                return out
            else:
                raise ValueError(f"unsupported function call: {func_name}()")

        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            # an integer literal — emit as a constant input
            name = f"const:{node.value}"
            return name

        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            # a float literal — convert to Fraction via str
            name = f"const:{node.value}"
            return name

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            l = self.visit(node.left)
            r = self.visit(node.right)
            # If one side is a constant, this is ¢_scale not ¢_mult
            if l.startswith("const:") and not r.startswith("const:"):
                k = Fraction(l.split(":", 1)[1])
                out = self._fresh("scale")
                self.ops.append(COp("scale", (r,), out, const=k))
                return out
            if r.startswith("const:") and not l.startswith("const:"):
                k = Fraction(r.split(":", 1)[1])
                out = self._fresh("scale")
                self.ops.append(COp("scale", (l,), out, const=k))
                return out
            # both variables or both constants — true ¢_mult
            out = self._fresh("mult")
            self.ops.append(COp("mult", (l, r), out))
            return out

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            l = self.visit(node.left)
            r = self.visit(node.right)
            # If divisor is a constant, this is ¢_scale by 1/k
            if r.startswith("const:") and not l.startswith("const:"):
                k = Fraction(r.split(":", 1)[1])
                out = self._fresh("scale")
                self.ops.append(COp("scale", (l,), out, const=Fraction(1)/k))
                return out
            # otherwise: ¢_div (composite, but we record it as one op for clarity)
            out = self._fresh("div")
            self.ops.append(COp("div", (l, r), out))
            return out

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base = self.visit(node.left)
            exp_node = node.right
            # parse exponent (must be numeric)
            if isinstance(exp_node, ast.Constant) and isinstance(exp_node.value, int):
                exp = exp_node.value
            elif (isinstance(exp_node, ast.BinOp) and isinstance(exp_node.op, ast.Div)
                  and isinstance(exp_node.left, ast.Constant)
                  and isinstance(exp_node.right, ast.Constant)):
                # fractional exponent like 1/2
                num = exp_node.left.value
                den = exp_node.right.value
                if num == 1 and den == 2:
                    # square root
                    out = self._fresh("sqrt")
                    self.ops.append(COp("sqrt", (base,), out))
                    return out
                elif num == -1 and den == 2:
                    # 1/sqrt(x) = recip(sqrt(x))
                    sq = self._fresh("sqrt")
                    self.ops.append(COp("sqrt", (base,), sq))
                    out = self._fresh("recip")
                    self.ops.append(COp("recip", (sq,), out))
                    return out
                else:
                    raise ValueError(f"unsupported fractional exponent {num}/{den}")
            else:
                raise ValueError(f"unsupported exponent: {ast.dump(exp_node)}")
            # integer power
            if exp == 2:
                out = self._fresh("mult")
                self.ops.append(COp("mult", (base, base), out))
                return out
            if exp == 3:
                sq = self._fresh("mult")
                self.ops.append(COp("mult", (base, base), sq))
                out = self._fresh("mult")
                self.ops.append(COp("mult", (sq, base), out))
                return out
            if exp == -1:
                out = self._fresh("recip")
                self.ops.append(COp("recip", (base,), out))
                return out
            if exp == -2:
                sq = self._fresh("mult")
                self.ops.append(COp("mult", (base, base), sq))
                out = self._fresh("recip")
                self.ops.append(COp("recip", (sq,), out))
                return out
            raise ValueError(f"unsupported integer exponent {exp}")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = self.visit(node.operand)
            out = self._fresh("neg")
            self.ops.append(COp("neg", (inner,), out))
            return out

        raise ValueError(f"unsupported AST node: {ast.dump(node)}")


def decompose_formula(formula: str, output_name: str) -> CGraph:
    """Parse `formula` (a Python expression string) and build a ¢ DAG
    whose output is `output_name`."""
    # Replace ^ with ** for Python parsing
    expr = formula.replace("^", "**")
    tree = ast.parse(expr, mode="eval")
    d = Decomposer()
    result = d.visit(tree.body)
    # If the result is already named output_name, no need for an extra op.
    # Otherwise, add a passthrough (treat as identity).
    # For matching purposes, we just rename the result variable.
    # Simplest: re-target the last op's output, OR add an alias.
    if result != output_name:
        # Find the op that produced `result` and rename its output
        renamed = False
        for i, op in enumerate(d.ops):
            if op.output == result:
                d.ops[i] = COp(op.op, op.inputs, output_name, op.const)
                renamed = True
                break
        if not renamed:
            # `result` was an input; add nothing, just declare it as output too
            pass
    d.outputs.add(output_name)
    return CGraph(ops=d.ops, inputs=d.inputs, outputs=d.outputs)


# ---------------------------------------------------------------------------
# 3. Spoke-formula normalization: from wheel axioms to canonical ¢ graphs
# ---------------------------------------------------------------------------

def spoke_formula_from_axiom(axiom: str, target: str) -> Optional[str]:
    """Given an axiom like 'spring_constant = mass * angular_frequency^2' and
    a target like 'angular_frequency', produce the spoke formula
    'angular_frequency = (spring_constant / mass)^(1/2)'.

    Returns None if the target cannot be isolated (e.g. appears linearly in
    a multi-term axiom).
    """
    from glm_wheels import parse_equation, relation_vector
    lhs, rhs = parse_equation(axiom)
    # We want target = (some expression of the other variables).
    # The relation vector tells us the exponents.
    rel = relation_vector(axiom)
    if target not in rel:
        return None
    target_exp = rel[target]
    if target_exp == 0:
        return None
    # If target_exp != 1, we need to divide all other exponents by -target_exp
    # and take a root of degree |target_exp|.
    # Build the formula: target = (prod(other^(-exp/target_exp)))^(1/target_exp)
    # Actually simpler: rearrange as target^|target_exp| = prod(others^(-exp/target_exp_sign))
    # then take the |target_exp|-th root.
    other_terms = []
    for k, v in rel.items():
        if k == target or k.startswith("#"):
            continue
        # we want target^target_exp * prod(other^v) = 1
        # => target^target_exp = prod(other^(-v))
        # => target = prod(other^(-v/target_exp)) ... if target_exp divides
        new_exp = -v / target_exp
        other_terms.append((k, new_exp))

    # Check that all new exponents are integers (otherwise we'd need fractional
    # powers of products, which is fine but messier)
    # For now, allow fractional exponents.

    # Build numerator and denominator
    num_terms = []
    den_terms = []
    for k, e in other_terms:
        if e > 0:
            if e == 1:
                num_terms.append(k)
            else:
                num_terms.append(k + "^" + str(e))
        elif e < 0:
            if e == -1:
                den_terms.append(k)
            else:
                den_terms.append(k + "^" + str(-e))

    # Constants (scalar primes)
    const_terms = []
    for k, v in rel.items():
        if k.startswith("#"):
            new_exp = -v / target_exp
            p = int(k[1:])
            if new_exp > 0:
                if new_exp == 1:
                    const_terms.append(str(p))
                else:
                    const_terms.append(str(p) + "^" + str(new_exp))
            elif new_exp < 0:
                if new_exp == -1:
                    const_terms.append("1/" + str(p))
                else:
                    const_terms.append("1/" + str(p) + "^" + str(-new_exp))

    # Assemble formula
    body_parts = []
    # Constants into numerator
    for c in const_terms:
        if "/" in c:
            p, d = c.split("/")
            den_terms.append(d)
        else:
            num_terms.append(c)

    body = " * ".join(num_terms) if num_terms else "1"
    for d in den_terms:
        body = f"({body}) / {d}"

    # If target_exp != 1, wrap in power
    if target_exp != 1:
        # target = body^(1/target_exp)
        # If 1/target_exp is fractional, write as ^(num/den)
        inv = Fraction(1) / target_exp
        if inv.denominator == 1:
            formula = f"({body})^{inv.numerator}" if inv.numerator != 1 else body
        else:
            formula = f"({body})^({inv.numerator}/{inv.denominator})"
    else:
        formula = body

    return formula


# ---------------------------------------------------------------------------
# 4. The ¢-graph isomorphism matcher
# ---------------------------------------------------------------------------

def find_cent_isomorphism(g_a: CGraph, g_b: CGraph) -> Optional[Dict[str, str]]:
    """Find a name bijection f: names(A) → names(B) such that applying f to
    A's ops yields B's ops (as a multiset).

    Returns the mapping dict, or None if no isomorphism exists.
    """
    # Fast signature check first
    if g_a.signature() != g_b.signature():
        return None

    names_a = sorted(g_a.name_multiset())
    names_b = sorted(g_b.name_multiset())
    if len(names_a) != len(names_b):
        return None

    # For each op in A, find candidate ops in B with the same signature
    # AND the same multiset of input "kinds" (constant vs variable).
    from itertools import permutations

    def op_kind(op: COp) -> Tuple:
        """Distinguish const inputs from variable inputs."""
        kinds = tuple(sorted("c" if i.startswith("const:") else "v" for i in op.inputs))
        if op.op == "scale":
            return ("scale", op.const, kinds)
        return (op.op, kinds, len(op.inputs))

    def op_full_sig(op: COp) -> Tuple:
        """Full signature including the multiset of input exponents (treating
        each input as occurring once per appearance)."""
        return (op_kind(op), tuple(sorted(op.inputs)))

    # Group ops by kind-sig; for each group, we need a bijection on the
    # variable names that appears consistently across all ops in the group.
    from collections import defaultdict
    groups_a = defaultdict(list)
    groups_b = defaultdict(list)
    for op in g_a.ops:
        groups_a[op_kind(op)].append(op)
    for op in g_b.ops:
        groups_b[op_kind(op)].append(op)

    if set(groups_a.keys()) != set(groups_b.keys()):
        return None
    for k in groups_a:
        if len(groups_a[k]) != len(groups_b[k]):
            return None

    # Backtracking: try to find a name bijection consistent across all groups.
    # For each group, the ops must be paired off such that the multiset of
    # input names (under the bijection) matches.
    mapping: Dict[str, str] = {}
    used_b: Set[str] = set()

    def consistent(op_a: COp, op_b: COp, mp: Dict[str, str]) -> bool:
        """Can op_a map to op_b under mp (and a consistent extension)?"""
        if op_kind(op_a) != op_kind(op_b):
            return False
        # For each input pair, check consistency
        # (constants must match exactly; variables must map consistently)
        for ia, ib in zip(op_a.inputs, op_b.inputs):
            if ia.startswith("const:") and ib.startswith("const:"):
                if ia != ib:
                    return False
            elif ia.startswith("const:") or ib.startswith("const:"):
                return False
            else:
                if ia in mp:
                    if mp[ia] != ib:
                        return False
                else:
                    if ib in used_b:
                        return False
        # Also check output
        oa, ob = op_a.output, op_b.output
        if oa.startswith("const:") or ob.startswith("const:"):
            if oa != ob:
                return False
        else:
            if oa in mp:
                if mp[oa] != ob:
                    return False
            else:
                if ob in used_b:
                    return False
        return True

    def commit(op_a: COp, op_b: COp, mp: Dict[str, str], used: Set[str]):
        """Add the bindings implied by pairing op_a with op_b."""
        for ia, ib in zip(op_a.inputs, op_b.inputs):
            if not ia.startswith("const:") and not ib.startswith("const:"):
                mp[ia] = ib
                used.add(ib)
        oa, ob = op_a.output, op_b.output
        if not oa.startswith("const:") and not ob.startswith("const:"):
            mp[oa] = ob
            used.add(ob)

    def revert(op_a: COp, op_b: COp, mp: Dict[str, str], used: Set[str],
               snapshot_mp: Dict[str, str], snapshot_used: Set[str]):
        mp.clear(); mp.update(snapshot_mp)
        used.clear(); used.update(snapshot_used)

    # Order groups by descending size (most-constrained-first)
    sorted_groups = sorted(groups_a.keys(), key=lambda k: -len(groups_a[k]))

    def backtrack(gi: int) -> bool:
        if gi == len(sorted_groups):
            return True
        kind = sorted_groups[gi]
        ops_a = groups_a[kind]
        ops_b = groups_b[kind]
        # Try every permutation of ops_b
        for perm in permutations(range(len(ops_b))):
            snapshot_mp = dict(mapping)
            snapshot_used = set(used_b)
            ok = True
            for ai, bi in enumerate(perm):
                if not consistent(ops_a[ai], ops_b[bi], mapping):
                    ok = False
                    break
                commit(ops_a[ai], ops_b[bi], mapping, used_b)
            if ok:
                if backtrack(gi + 1):
                    return True
            revert(None, None, mapping, used_b, snapshot_mp, snapshot_used)
        return False

    if backtrack(0):
        return mapping
    return None


# ---------------------------------------------------------------------------
# 5. Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("¢ IR self-test")
    print("=" * 70)

    # Test 1: W5-03 spoke  velocity = (2 * energy / mass)^(1/2)
    g1 = decompose_formula("(2 * energy / mass)^(1/2)", "velocity")
    print("\nW5-03 spoke: velocity = (2 * energy / mass)^(1/2)")
    print(g1.render())
    print(f"signature: {g1.signature()}")

    # Test 2: W13 derived  ω = (spring_constant / mass)^(1/2)
    g2 = decompose_formula("(spring_constant / mass)^(1/2)", "angular_frequency")
    print("\nW13 derived: angular_frequency = (spring_constant / mass)^(1/2)")
    print(g2.render())
    print(f"signature: {g2.signature()}")

    # Test 3: W14 derived  ω = (1 / (inductance * capacitance))^(1/2)
    g3 = decompose_formula("(1 / (inductance * capacitance))^(1/2)",
                           "angular_frequency")
    print("\nW14 derived: angular_frequency = (1 / (inductance * capacitance))^(1/2)")
    print(g3.render())
    print(f"signature: {g3.signature()}")

    # Test 4: W19 derived  c = (1 / (permittivity * permeability))^(1/2)
    g4 = decompose_formula("(1 / (permittivity * permeability))^(1/2)",
                           "speed_of_light")
    print("\nW19 derived: speed_of_light = (1 / (permittivity * permeability))^(1/2)")
    print(g4.render())
    print(f"signature: {g4.signature()}")

    # Test 5: W17 derived  T = (distance^3 / (gravitational_constant * source_mass))^(1/2)
    g5 = decompose_formula(
        "(distance^3 / (gravitational_constant * source_mass))^(1/2)",
        "period")
    print("\nW17 derived: period = (distance^3 / (G*M))^(1/2)")
    print(g5.render())
    print(f"signature: {g5.signature()}")

    # Isomorphism tests
    print("\n" + "=" * 70)
    print("¢-isomorphism tests (square-root carriers)")
    print("=" * 70)

    pairs = [
        ("W5-03", g1, "W13", g2),
        ("W5-03", g1, "W14", g3),
        ("W5-03", g1, "W19", g4),
        ("W5-03", g1, "W17", g5),
        ("W13", g2, "W14", g3),
        ("W13", g2, "W19", g4),
        ("W13", g2, "W17", g5),
        ("W14", g3, "W19", g4),
        ("W14", g3, "W17", g5),
        ("W19", g4, "W17", g5),
    ]
    print(f"\n{'pair':<14}{'same sig?':<12}{'mapping found?':<18}mapping")
    print("-" * 90)
    for n1, ga, n2, gb in pairs:
        same_sig = ga.signature() == gb.signature()
        mp = find_cent_isomorphism(ga, gb)
        found = "YES" if mp else "no"
        mp_str = ""
        if mp:
            mp_str = ", ".join(f"{k}→{v}" for k, v in sorted(mp.items()))
            if len(mp_str) > 50:
                mp_str = mp_str[:47] + "..."
        print(f"{n1}-{n2:<8}{'yes' if same_sig else 'no':<12}{found:<18}{mp_str}")
