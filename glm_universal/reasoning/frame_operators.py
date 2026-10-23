"""``glm_universal.reasoning.frame_operators`` -- an operator inferred from
example pairs of 2-vectors, read layer by layer: the invariant layer says
which family it can be, the light-cone or complex layer fits it, and the
agreement gate answers only when every fitting family agrees (Phase 177).

*Created 21 October 2026.*

Where this comes from
---------------------
The owner's document ``source_material/Lorentz boosts.pdf`` reads a Lorentz
boost as a "move" of a puzzle whose invariant core is the rest mass, and the
speed of light as the calibration dial.  Its closing review proposes two
studies: an exact-arithmetic integrity study of rational boosts, and an
operator-inference study -- give the system pairs ``q -> B(u) q`` sharing an
unknown ``u`` and ask it to transform a new state -- with a *mixed* benchmark
of rotations, boosts, permutations and unit conversions, where the machine
must infer which structure applies.  The pipeline kit (Phases 175-176) does
this for 0/1 grids; this module does it for exact rational 2-vectors, and
uses the same gate.

The method, stated once because it is the part that transfers
-------------------------------------------------------------
A task is "worked out" in three stacked layers:

1. **The invariant layer** (classify).  For each pair, read which quadratic
   forms survive: ``E^2 - p^2`` (``inv``), ``E^2 + p^2`` (``euclid``), or
   neither, and whether a surviving ratio is the same across pairs.  Each
   family has a necessary signature (a boost keeps ``inv``; a rotation keeps
   ``euclid``; a change of units multiplies both by one ``s^2``), so a family
   whose signature fails is never fitted.  This is the kit's weight filter
   (``wt_comp_perm``) in another domain.
2. **The diagonal layer** (fit).  Each family is fitted in the coordinates in
   which it acts by scaling: the light-cone pair ``(E+p, E-p)`` for boosts,
   unit changes and their products (``GLM.RationalBoost.boost_plus``,
   ``boost_minus``), the complex number ``E + i p`` for rotations and their
   products.  Parameters are read off as exact ratios; a parameter no pair
   reaches is left *free*, and a family with a free parameter the query
   needs gives no single answer.
3. **The gate** (answer or refuse).  The query is answered only when every
   fitting family gives it the same output, as ``tool induce`` does
   (``GLM.PipelineInduction.solve_sound``); otherwise the refusal names an
   input whose output would separate them (``GLM.PipelineAsk``).

The families
------------
``identity``, ``swap`` (E and p exchanged), ``parity`` (p negated): no
parameter.  ``units`` (every component times ``s > 0``), ``boost`` (Doppler
factor ``k > 0``), ``rotation`` (a rational point ``w`` of the unit circle):
one parameter.  ``boost_units`` (light-cone scalings ``alpha, beta > 0``, a
boost times a change of units), ``rotation_units`` (multiplication by any
non-zero Gaussian rational ``w``): two parameters.

What is proved, and what is measured
------------------------------------
``RequestProject/GLM/RationalBoost.lean`` proves the arithmetic: invariance,
inverse, the composition law, the branch, the light-cone diagonal form,
that every rational boost is in the family, that no integer one is
non-trivial, and the two facts the gate leans on -- on a light-like state a
boost *is* a change of units (``null_confound``), and one state with
``E^2 - p^2 != 0`` fixes both (``timelike_separates``).  Whether the gate is
right on a task family depends on whether the truth is among the families;
``frame_operator_study`` measures it, including two families that are not.

Exactness
---------
``Fraction`` throughout (D7); no float is formed.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "State", "LEAN_FILE", "LEAN_THEOREMS", "FAMILIES", "PARAMS", "USAGE",
    "inv", "euclid", "plus", "minus", "boost", "rot", "scale", "doppler",
    "compose", "signature_ok", "fit", "solve", "separating_input",
    "ask_loop", "linear_fit", "parse_state", "state_text", "frame_text",
    "input_rank",
]

State = Tuple[Fraction, Fraction]
Pairs = Sequence[Tuple[State, State]]

LEAN_FILE = "RequestProject/GLM/RationalBoost.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "ca_sq_sub_sb_sq", "boost_inv", "boost_zero", "boost_neg_boost",
    "compose_abs_lt_one", "boost_boost", "sb_div_ca", "abs_beta_lt_one",
    "inv_eq_plus_mul_minus", "boost_plus", "boost_minus", "doppler_compose",
    "boost_future", "rational_boost_param", "int_boost_trivial", "scale_inv",
    "scale_boost_comm", "null_confound", "null_confound_example",
    "null_confound_opposite", "null_rays_separate",
    "timelike_separates", "boost_determined", "rot_euclid",
    "boost_not_euclid", "rot_not_inv")

FAMILIES: Tuple[str, ...] = ("identity", "swap", "parity", "units", "boost",
                             "rotation", "boost_units", "rotation_units")
#: Number of free parameters of each family (the occam control's tiers).
PARAMS: Dict[str, int] = {"identity": 0, "swap": 0, "parity": 0, "units": 1,
                          "boost": 1, "rotation": 1, "boost_units": 2,
                          "rotation_units": 2}

USAGE = ("tool frame E,p -> E',p' ; E,p -> E',p' ? E,p  (exact rationals, "
         "e.g. tool frame 1,0 -> 5/3,-4/3 ; 2,1 -> 7/3,-2/3 ? 3,1)")

F0, F1 = Fraction(0), Fraction(1)


# ── the arithmetic (mirrors RationalBoost.lean) ───────────────────────────

def inv(q: State) -> Fraction:
    return q[0] * q[0] - q[1] * q[1]


def euclid(q: State) -> Fraction:
    return q[0] * q[0] + q[1] * q[1]


def plus(q: State) -> Fraction:
    return q[0] + q[1]


def minus(q: State) -> Fraction:
    return q[0] - q[1]


def from_lightcone(xp: Fraction, xm: Fraction) -> State:
    return ((xp + xm) / 2, (xp - xm) / 2)


def ca(u: Fraction) -> Fraction:
    return (1 + u * u) / (1 - u * u)


def sb(u: Fraction) -> Fraction:
    return 2 * u / (1 - u * u)


def boost(u: Fraction, q: State) -> State:
    """``B(u)`` by its matrix: ``E' = aE - bp``, ``p' = -bE + ap``."""
    a, b = ca(u), sb(u)
    return (a * q[0] - b * q[1], -b * q[0] + a * q[1])


def doppler(u: Fraction) -> Fraction:
    return (1 + u) / (1 - u)


def u_of_doppler(k: Fraction) -> Fraction:
    return (k - 1) / (k + 1)


def compose(u: Fraction, v: Fraction) -> Fraction:
    return (u + v) / (1 + u * v)


def rot(t: Fraction, q: State) -> State:
    c, s = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
    return (c * q[0] - s * q[1], s * q[0] + c * q[1])


def scale(s: Fraction, q: State) -> State:
    return (s * q[0], s * q[1])


def _cmul(w: State, z: State) -> State:
    return (w[0] * z[0] - w[1] * z[1], w[0] * z[1] + w[1] * z[0])


def _cdiv(z1: State, z0: State) -> State:
    n = euclid(z0)
    return ((z1[0] * z0[0] + z1[1] * z0[1]) / n,
            (z1[1] * z0[0] - z1[0] * z0[1]) / n)


# ── layer 1: the invariant signature ──────────────────────────────────────

def _ratios_constant(pairs: Pairs, form: Callable[[State], Fraction],
                     positive: bool) -> bool:
    """``form(y)/form(x)`` is one value over the pairs with ``form(x) != 0``,
    and ``form(x) = 0`` forces ``form(y) = 0``."""
    r: Optional[Fraction] = None
    for x, y in pairs:
        fx, fy = form(x), form(y)
        if fx == 0:
            if fy != 0:
                return False
            continue
        q = fy / fx
        if positive and q <= 0:
            return False
        if r is None:
            r = q
        elif q != r:
            return False
    return True


def signature_ok(family: str, pairs: Pairs) -> bool:
    """The necessary invariant signature of ``family`` (layer 1)."""
    keeps_inv = all(inv(y) == inv(x) for x, y in pairs)
    keeps_euc = all(euclid(y) == euclid(x) for x, y in pairs)
    if family in ("identity", "parity", "boost"):
        return keeps_inv
    if family == "swap":
        return keeps_euc and all(inv(y) == -inv(x) for x, y in pairs)
    if family == "rotation":
        return keeps_euc
    if family == "units":
        return (_ratios_constant(pairs, euclid, True)
                and all(inv(y) * euclid(x) == euclid(y) * inv(x)
                        for x, y in pairs))
    if family == "boost_units":
        return _ratios_constant(pairs, inv, True)
    if family == "rotation_units":
        return _ratios_constant(pairs, euclid, True)
    raise KeyError(family)


# ── layer 2: fitting each family in its diagonal layer ────────────────────

def _ratio(pairs: Pairs, get_x, get_y) -> Tuple[bool, Optional[Fraction]]:
    """One scale ``y = r x`` on a coordinate: (consistent, r or None if no
    pair reaches it)."""
    r: Optional[Fraction] = None
    for x, y in pairs:
        cx, cy = get_x(x), get_y(y)
        if cx == 0:
            if cy != 0:
                return False, None
            continue
        q = cy / cx
        if r is None:
            r = q
        elif q != r:
            return False, None
    return True, r


Fitted = Dict[str, object]


def fit(family: str, pairs: Pairs) -> Optional[Fitted]:
    """The members of ``family`` consistent with every pair, as parameters
    (``None`` for a parameter no pair reaches), or ``None`` if none fits."""
    if family == "identity":
        return {} if all(y == x for x, y in pairs) else None
    if family == "swap":
        return {} if all(y == (x[1], x[0]) for x, y in pairs) else None
    if family == "parity":
        return {} if all(y == (x[0], -x[1]) for x, y in pairs) else None
    if family == "units":
        ok, s = _ratio(pairs, lambda x: x[0], lambda y: y[0])
        ok2, s2 = _ratio(pairs, lambda x: x[1], lambda y: y[1])
        if not (ok and ok2):
            return None
        if s is not None and s2 is not None and s != s2:
            return None
        s = s if s is not None else s2
        if s is not None and s <= 0:
            return None
        return {"s": s}
    if family in ("boost", "boost_units"):
        ok, alpha = _ratio(pairs, plus, plus)
        ok2, beta = _ratio(pairs, minus, minus)
        if not (ok and ok2):
            return None
        if (alpha is not None and alpha <= 0) or (beta is not None and beta <= 0):
            return None
        if family == "boost_units":
            return {"alpha": alpha, "beta": beta}
        # a boost: alpha = 1/k, beta = k
        if alpha is not None and beta is not None and alpha * beta != 1:
            return None
        k = beta if beta is not None else (1 / alpha if alpha is not None else None)
        return {"k": k}
    if family in ("rotation", "rotation_units"):
        w: Optional[State] = None
        for x, y in pairs:
            if x == (0, 0):
                if y != (0, 0):
                    return None
                continue
            q = _cdiv(y, x)
            if w is None:
                w = q
            elif q != w:
                return None
        if w is not None:
            if w == (0, 0):
                return None
            if family == "rotation" and euclid(w) != 1:
                return None
        return {"w": w}
    raise KeyError(family)


def apply(family: str, params: Fitted, q: State) -> Optional[State]:
    """The fitted family's output on ``q``, or ``None`` when it depends on a
    free parameter (the family gives no single answer)."""
    if family == "identity":
        return q
    if family == "swap":
        return (q[1], q[0])
    if family == "parity":
        return (q[0], -q[1])
    if family == "units":
        s = params["s"]
        if s is None:
            return q if q == (0, 0) else None
        return scale(s, q)
    if family in ("boost", "boost_units"):
        if family == "boost":
            k = params["k"]
            alpha, beta = (None, None) if k is None else (1 / k, k)
        else:
            alpha, beta = params["alpha"], params["beta"]
        xp, xm = plus(q), minus(q)
        if (xp != 0 and alpha is None) or (xm != 0 and beta is None):
            return None
        return from_lightcone(alpha * xp if xp != 0 else F0,
                              beta * xm if xm != 0 else F0)
    if family in ("rotation", "rotation_units"):
        w = params["w"]
        if w is None:
            return q if q == (0, 0) else None
        return _cmul(w, q)
    raise KeyError(family)


def describe(family: str, params: Fitted) -> str:
    """The fitted member in words, with its exact parameters."""
    if family == "boost":
        k = params["k"]
        if k is None:
            return "boost (Doppler factor free)"
        u = u_of_doppler(k)
        return (f"boost B(u) with u = {u} (Doppler factor k = {k}, velocity "
                f"ratio beta = {2 * u / (1 + u * u)})")
    if family == "units":
        s = params["s"]
        return "change of units (scale free)" if s is None else \
            f"change of units by s = {s}"
    if family == "rotation":
        w = params["w"]
        return "rotation (angle free)" if w is None else \
            f"rotation by cos = {w[0]}, sin = {w[1]}"
    if family == "boost_units":
        a, b = params["alpha"], params["beta"]
        if a is None or b is None:
            return "boost times change of units (a scale free)"
        return (f"boost times change of units: E+p times {a}, E-p times {b} "
                f"(units^2 = {a * b}, k^2 = {b / a})")
    if family == "rotation_units":
        w = params["w"]
        return "rotation times change of units (free)" if w is None else \
            f"multiplication by {w[0]} + {w[1]} i"
    return family


# ── layer 3: the gate ─────────────────────────────────────────────────────

def solve(pairs: Pairs, query: State, *, layer_filter: bool = True,
          evidence_guard: bool = True,
          families: Sequence[str] = FAMILIES) -> Dict[str, object]:
    """Fit every family (after the invariant filter, unless switched off);
    answer only if every fitting family gives the query one output and at
    least one of them is *checked* -- it has fewer parameters than the
    pairs give independent equations (two per dimension of the span of the
    inputs), so its fit was tested and not merely solved for.  When every
    fitting family agrees but none is checked the status is ``untested``
    (the evidence guard, added after the first take; see the study, 7.2)."""
    fitted: List[Tuple[str, Fitted]] = []
    tried = skipped = 0
    for fam in families:
        if layer_filter and not signature_ok(fam, pairs):
            skipped += 1
            continue
        tried += 1
        p = fit(fam, pairs)
        if p is not None:
            fitted.append((fam, p))
    outs = {fam: apply(fam, p, query) for fam, p in fitted}
    equations = 2 * input_rank(pairs)
    checked = [f for f, _ in fitted if PARAMS[f] < equations]
    base = {"fitted": [f for f, _ in fitted], "params": dict(fitted),
            "outputs": outs, "tried": tried, "skipped_by_layer": skipped,
            "equations": equations, "checked": checked}
    if not fitted:
        return dict(base, status="unfit")
    if any(o is None for o in outs.values()):
        return dict(base, status="ambiguous",
                    free=[f for f, o in outs.items() if o is None])
    distinct = set(outs.values())
    if len(distinct) > 1:
        return dict(base, status="ambiguous", free=[])
    if evidence_guard and not checked:
        return dict(base, status="untested", free=[])
    return dict(base, status="answered", answer=next(iter(distinct)))


def input_rank(pairs: Pairs) -> int:
    """The dimension of the span of the demonstration inputs (0, 1 or 2)."""
    xs = [x for x, _ in pairs if x != (0, 0)]
    if not xs:
        return 0
    x0 = xs[0]
    return 2 if any(x0[0] * x[1] - x0[1] * x[0] != 0 for x in xs) else 1


#: Inputs the ask may name: timelike first, then the light-like rays, then
#: the axes.  The query and the demonstration inputs are never asked.
POOL: Tuple[State, ...] = tuple(
    (Fraction(a), Fraction(b)) for a, b in
    ((2, 1), (3, 1), (3, 2), (5, 3), (4, 1), (5, 2), (2, -1), (3, -2),
     (1, 1), (1, -1), (1, 0), (0, 1)))


def separating_input(pairs: Pairs, query: State,
                     fitted: Sequence[str]) -> Optional[State]:
    """The first pool input on which the fitting families disagree or one of
    them is not yet determined (its reply then pins a parameter)."""
    seen = {x for x, _ in pairs} | {query}
    params = {f: fit(f, pairs) for f in fitted}
    for x in POOL:
        if x in seen:
            continue
        outs = [apply(f, params[f], x) for f in fitted]
        if any(o is None for o in outs) or len(set(outs)) > 1:
            return x
    if input_rank(pairs) < 2:
        # untested: any input off the line of the inputs adds a check
        for x in POOL:
            if x not in seen and input_rank(list(pairs) + [(x, x)]) == 2:
                return x
    return None


def ask_loop(pairs: Pairs, query: State, oracle: Callable[[State], State],
             max_asks: int = 2) -> Dict[str, object]:
    demos = list(pairs)
    asked: List[State] = []
    r = solve(demos, query)
    while r["status"] in ("ambiguous", "untested") and len(asked) < max_asks:
        x = separating_input(demos, query, r["fitted"])
        if x is None:
            break
        demos.append((x, oracle(x)))
        asked.append(x)
        r = solve(demos, query)
    return dict(r, asks=asked)


# ── the controls ──────────────────────────────────────────────────────────

def first_fit(pairs: Pairs, query: State) -> Optional[State]:
    """The eager control: the first family (in declared order) that fits
    answers; a free parameter is guessed as 1."""
    for fam in FAMILIES:
        p = fit(fam, pairs)
        if p is None:
            continue
        guess = {k: (v if v is not None else
                     ((F1, F0) if k == "w" else F1)) for k, v in p.items()}
        return apply(fam, guess, query)
    return None


def occam(pairs: Pairs, query: State) -> Dict[str, object]:
    """The tiered control: fewest parameters first, the gate within a tier."""
    for n in (0, 1, 2):
        tier = [f for f in FAMILIES if PARAMS[f] == n]
        r = solve(pairs, query, families=tier)
        if r["status"] != "unfit":
            return dict(r, tier=n)
    return {"status": "unfit"}


def linear_fit(pairs: Pairs, query: State) -> Optional[State]:
    """The direct-representation baseline: a general 2x2 matrix, fitted from
    two independent inputs and checked on the rest; ``None`` when the inputs
    do not span the plane or no matrix fits."""
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            (x1, y1), (x2, y2) = pairs[i], pairs[j]
            det = x1[0] * x2[1] - x1[1] * x2[0]
            if det == 0:
                continue
            # M X = Y with X = [x1 x2] columns
            inv_x = ((x2[1] / det, -x2[0] / det), (-x1[1] / det, x1[0] / det))
            m = tuple(tuple(y1[r] * inv_x[0][c] + y2[r] * inv_x[1][c]
                            for c in range(2)) for r in range(2))

            def mv(v: State) -> State:
                return (m[0][0] * v[0] + m[0][1] * v[1],
                        m[1][0] * v[0] + m[1][1] * v[1])
            if all(mv(x) == y for x, y in pairs):
                return mv(query)
            return None
    return None


# ── text ──────────────────────────────────────────────────────────────────

def parse_state(text: str) -> Optional[State]:
    parts = [p.strip() for p in text.strip().strip("()").split(",")]
    if len(parts) != 2:
        return None
    try:
        return (Fraction(parts[0]), Fraction(parts[1]))
    except (ValueError, ZeroDivisionError):
        return None


def state_text(q: State) -> str:
    return f"{q[0]},{q[1]}"


def _layer_reading(pairs: Pairs) -> str:
    keeps_inv = all(inv(y) == inv(x) for x, y in pairs)
    keeps_euc = all(euclid(y) == euclid(x) for x, y in pairs)
    bits = []
    bits.append("E^2-p^2 kept" if keeps_inv else "E^2-p^2 not kept")
    bits.append("E^2+p^2 kept" if keeps_euc else "E^2+p^2 not kept")
    if all(inv(x) == 0 for x, _ in pairs):
        bits.append("every demonstration input is light-like, so a change of "
                    "frame and a change of units look alike "
                    "(GLM.RationalBoost.null_confound)")
    return "; ".join(bits)


def frame_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool frame``: parse, solve, and say what happened in words."""
    if "?" not in arg:
        return False, f"refused: {USAGE}", {}
    left, qtext = arg.rsplit("?", 1)
    query = parse_state(qtext)
    pairs: List[Tuple[State, State]] = []
    for part in [p for p in left.split(";") if p.strip()]:
        if "->" not in part:
            return False, f"refused: {part.strip()!r} is not 'E,p -> E,p'; {USAGE}", {}
        a, b = part.split("->", 1)
        x, y = parse_state(a), parse_state(b)
        if x is None or y is None:
            bad = a if x is None else b
            return False, f"refused: {bad.strip()!r} is not a pair of rationals", {}
        pairs.append((x, y))
    if query is None or not pairs:
        return False, f"refused: {USAGE}", {}
    r = solve(pairs, query)
    layer = _layer_reading(pairs)
    figures: Dict[str, object] = {"status": r["status"],
                                  "fitted": list(r["fitted"]),
                                  "tried": r["tried"],
                                  "skipped_by_layer": r["skipped_by_layer"]}
    if r["status"] == "answered":
        ans = r["answer"]
        figures["answer"] = state_text(ans)
        named = "; ".join(describe(f, r["params"][f]) for f in r["fitted"])
        figures["invariant_after"] = str(inv(ans))
        return True, (f"frame: {state_text(ans)}, given by every family that "
                      f"fits all {len(pairs)} pairs ({named}); invariant layer: "
                      f"{layer}; E^2-p^2 of the answer is {inv(ans)} against "
                      f"{inv(query)} for the query "
                      "(GLM.PipelineInduction.solve_sound: the true operator's "
                      "answer whenever it is among the families)"), figures
    if r["status"] == "unfit":
        return False, (f"frame: refused -- no family fits all {len(pairs)} "
                       f"pairs; invariant layer: {layer}; the operator is "
                       "outside the declared families (identity, swap, parity, "
                       "units, boost, rotation and their products with units)"
                       ), figures
    x = separating_input(pairs, query, r["fitted"])
    outs = r["outputs"]
    if r["status"] == "untested":
        figures["ask"] = None if x is None else state_text(x)
        return False, (f"frame: refused -- every family that fits gives "
                       f"{state_text(next(iter(outs.values())))}, but none is "
                       f"tested: the pairs give {r['equations']} independent "
                       "equations and each fitting family has at least as many "
                       "parameters, so it was solved for, not checked; "
                       f"invariant layer: {layer}"
                       + ("" if x is None else
                          f"; to settle it, give the output for {state_text(x)}")
                       ), figures
    said = "; ".join(f"{f} gives " + ("no single answer (a parameter is free)"
                                      if o is None else state_text(o))
                     for f, o in outs.items())
    figures["ask"] = None if x is None else state_text(x)
    tail = ("" if x is None else
            f"; to settle it, give the output for {state_text(x)}"
            + (" (a massive state: one fixes frame and units together, "
               "GLM.RationalBoost.timelike_separates)" if inv(x) != 0 else ""))
    return False, (f"frame: refused -- the families that fit disagree on "
                   f"{state_text(query)}: {said}; invariant layer: {layer}"
                   f"{tail}"), figures
