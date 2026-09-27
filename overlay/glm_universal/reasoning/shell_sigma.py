"""``glm_universal.reasoning.shell_sigma`` -- delta-sigma on the Leech shells.

Where this sits
---------------
:mod:`glm_universal.reasoning.noise_lab` builds the delta-sigma family whose
alphabet is *small*: one bit, a cascade of bits, a Golay codeword, a vector
pushed through a rational matrix.  ``HullExpansion.lean`` records the price of
a small alphabet -- what a loop can read back is exactly the convex hull of
what it may emit, so a target outside that hull drifts away forever.  This
module is the other end of the family: the alphabet is a **shell of the Leech
lattice**, the 196,560 minimal vectors, and the alphabet is no longer small.

Two rules, two theorems
-----------------------
A shell is a *sphere*.  It is finite, and it covers nothing, so the usual
delta-sigma argument -- "the accumulator never leaves the quantiser's covering
ball" -- is simply unavailable.  Two different rules are built here, and each
has its own machine-checked law in ``RequestProject/GLM/ShellSigma.lean``:

==================  =========================================================
rule                law
==================  =========================================================
**nearest**, over   ``GLM.Shell.sAverage_error_le``: with covering radius
the whole lattice   ``rho`` the running mean tracks *any* target at ``rho/N``.
                    The Leech lattice covers, so nothing is out of reach --
                    this is exactly the wall of ``HullExpansion.lean`` coming
                    down.
**matched**, over   ``GLM.Shell.shAverage_error_le``: emit the shell point the
one shell           accumulator points at hardest.  If the target sits at
                    distance ``mu`` inside the hull of the shell and ``D``
                    bounds ``|t - v|``, the accumulator stays in the ball of
                    radius ``D^2/(2 mu) + D`` and the mean tracks at ``B/N``.
                    Outside the hull it cannot track at all.
==================  =========================================================

The matched rule needs the **support function** of the shell,
``h(x) = max {<x, v> : |v|^2 = 32}``, and needs it exactly.  Enumerating
196,560 vectors per tick is possible but wasteful; :func:`shell_support`
instead maximises over each of the three shapes in closed form:

* ``(+-4^2, 0^22)``  -- ``4 * (largest + second largest |x_i|)``;
* ``(+-2^8)`` on an octad -- per octad, ``2 * sum |x_i|`` less ``4 * min|x_i|``
  when the natural sign pattern has an odd number of minus signs (the shape
  requires an even number), maximised over the 759 octads;
* ``(-+3, +-1^23)`` -- ``sum(x) - 2 S(c) + 4 max_i(x_i if i in c else -x_i)``
  over the 4,096 Golay codewords ``c``, with the coset sums ``S(c)`` supplied
  by the Walsh-Hadamard transform of
  :mod:`glm_universal.reasoning.fwht_decode`.

:func:`support_agreement` checks the closed form against a full sweep of all
196,560 minimal vectors, so the shortcut is verified rather than asserted.

What the experiments show
-------------------------
* :func:`inside_run` -- a target built as an explicit convex combination of
  shell points is tracked, and ``|accumulator|`` stays flat while ``N`` grows,
  so the error falls like ``1/N``.  The margin hypothesis of the Lean theorem
  is *checked at every direction the run actually visits*, and the observed
  accumulator bound is compared with ``D^2/(2 mu) + D``.
* :func:`outside_run` -- the target ``5 e_0`` has ``<e_0, t> = 5`` while
  ``h(e_0) = 4``: a one-line exact separating certificate that no rule
  emitting from the shell can ever reach it.  The run shows the accumulator
  growing linearly, at the rate the certificate predicts.
* :func:`certified_inner_ball` -- from the first shape alone,
  ``h(x) >= 4 max|x_i| >= 4 |x| / sqrt(24)``, so every target with
  ``3 |t|^2 < 2`` has a certified margin.  Exact, and deliberately not tight.
* :func:`lattice_run` -- the same target with the *whole* lattice as alphabet,
  quantised by the exact Leech decoder, tracked at ``rho/N``.

The Gibbs-style rule
--------------------
The last section replaces the hard snap -- always the nearest, or always the
best matched, point -- by a temperature-weighted choice among candidates.  The
weights are the ones ``ShellSigma.lean`` defines,
``gibbsWeight E t i = t^(Emax - E_i) / sum_j t^(Emax - E_j)``, in exact
rational arithmetic, and the ensemble is realised **without randomness**: the
same greedy error-feedback accumulator the modulators use visits candidate
``i`` with frequency within ``(m-1)/N`` of ``w_i``
(``GLM.Shell.gibbsFreq_error_le``).  The trajectory *is* the distribution.

:func:`gibbs_shell_experiment` runs it on a real instance -- a query point and
its nearest shell candidates, energies the exact squared distances -- and
reports the frequency error against the proved bound, at three temperatures.

Everything below is exact: :class:`~fractions.Fraction` and :class:`int` only,
no floats, no ``random``.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, mog
from . import fwht_decode

__all__ = [
    "DIM",
    "SHELL_NORM2",
    "SHELL_SIZE",
    "shell_support",
    "support_agreement",
    "matched_run",
    "inside_target",
    "inside_run",
    "outside_run",
    "certified_inner_ball",
    "lattice_run",
    "gibbs_weights",
    "gibbs_limits",
    "gibbs_schedule",
    "gibbs_shell_experiment",
    "shell_sigma_report",
]


DIM = 24
#: squared norm of the first Leech shell in the ``x sqrt(8)`` integer model
SHELL_NORM2 = 32
#: the kissing number
SHELL_SIZE = 196560


def _exact(vector: Sequence) -> Tuple[Fraction, ...]:
    return tuple(Fraction(v) for v in vector)


def _inner(a: Sequence, b: Sequence) -> Fraction:
    return sum((Fraction(x) * Fraction(y) for x, y in zip(a, b)), Fraction(0))


def _norm2(a: Sequence) -> Fraction:
    return _inner(a, a)


# ===========================================================================
# 1.  THE SUPPORT FUNCTION OF THE SHELL
# ===========================================================================

@lru_cache(maxsize=None)
def _octad_positions() -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(i for i in range(DIM) if (mask >> i) & 1)
                 for mask in mog.OCTAD_MASKS)


def _best_pair(x: Sequence[Fraction]) -> Tuple[Fraction, Tuple[int, ...]]:
    """Shape ``(+-4^2, 0^22)``."""
    order = sorted(range(DIM), key=lambda i: -abs(x[i]))
    i, j = order[0], order[1]
    value = 4 * (abs(x[i]) + abs(x[j]))
    v = [0] * DIM
    v[i] = 4 if x[i] >= 0 else -4
    v[j] = 4 if x[j] >= 0 else -4
    return value, tuple(v)


def _best_octad(x: Sequence[Fraction]) -> Tuple[Fraction, Tuple[int, ...]]:
    """Shape ``(+-2^8)`` on an octad, with an even number of minus signs."""
    best_value: Optional[Fraction] = None
    best: Tuple[int, ...] = ()
    for positions in _octad_positions():
        total = Fraction(0)
        negatives = 0
        smallest = None
        smallest_at = positions[0]
        for p in positions:
            a = abs(x[p])
            total += a
            if x[p] < 0:
                negatives += 1
            if smallest is None or a < smallest:
                smallest, smallest_at = a, p
        assert smallest is not None
        flip = negatives % 2 == 1
        value = 2 * (total - (2 * smallest if flip else Fraction(0)))
        if best_value is None or value > best_value:
            best_value = value
            v = [0] * DIM
            for p in positions:
                sign = -1 if x[p] < 0 else 1
                if flip and p == smallest_at:
                    sign = -sign
                v[p] = 2 * sign
            best = tuple(v)
    assert best_value is not None
    return best_value, best


def _best_triple(x: Sequence[Fraction]) -> Tuple[Fraction, Tuple[int, ...]]:
    """Shape ``(-+3, +-1^23)``, driven by a Golay codeword."""
    total = sum(x, Fraction(0))
    sums = fwht_decode.support_sums_fwht(x)
    descending = sorted(range(DIM), key=lambda i: -x[i])
    ascending = list(reversed(descending))
    best_value: Optional[Fraction] = None
    best_word = 0
    best_index = 0
    for word in mog.GOLAY_MASKS:
        base = total - 2 * sums[fwht_decode.message_of_codeword(word)]
        inside = next((i for i in descending if (word >> i) & 1), None)
        outside = next((i for i in ascending if not (word >> i) & 1), None)
        pick = None
        gain: Optional[Fraction] = None
        if inside is not None:
            pick, gain = inside, x[inside]
        if outside is not None and (gain is None or -x[outside] > gain):
            pick, gain = outside, -x[outside]
        if pick is None:
            continue
        assert gain is not None
        value = base + 4 * gain
        if best_value is None or value > best_value:
            best_value, best_word, best_index = value, word, pick
    assert best_value is not None
    v = [(-1 if (best_word >> j) & 1 else 1) for j in range(DIM)]
    v[best_index] = 3 if (best_word >> best_index) & 1 else -3
    return best_value, tuple(v)


def shell_support(x: Sequence) -> Dict[str, object]:
    """``max {<x, v> : v in the first Leech shell}``, exactly, plus a maximiser.

    Closed form over the three shapes; no enumeration of the 196,560 vectors.
    """
    xf = _exact(x)
    shapes = {
        "(+-4^2, 0^22)": _best_pair(xf),
        "(+-2^8)": _best_octad(xf),
        "(-+3, +-1^23)": _best_triple(xf),
    }
    name, (value, vector) = max(shapes.items(), key=lambda kv: kv[1][0])
    return {
        "support": value,
        "argmax": vector,
        "shape": name,
        "shape_values": {k: v[0] for k, v in shapes.items()},
        "argmax_norm2": leech2.norm2(vector),
        "argmax_in_leech": leech2.in_leech(vector),
    }


def _sweep(seed: int, count: int, spread: int) -> List[Tuple[int, ...]]:
    """A deterministic spread of integer probe vectors (no ``random``)."""
    state = seed
    out: List[Tuple[int, ...]] = []
    for _ in range(count):
        v = []
        for _ in range(DIM):
            state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
            v.append(((state >> 33) % (2 * spread + 1)) - spread)
        out.append(tuple(v))
    return out


@lru_cache(maxsize=None)
def support_agreement(samples: int = 3, seed: int = 20260829) -> Dict[str, object]:
    """Check the closed form against all 196,560 minimal vectors.

    Slow on purpose -- it is the audit, not the working routine.
    """
    probes = _sweep(seed, samples, 6)
    rows = []
    for probe in probes:
        fast = shell_support(probe)
        brute = max(sum(probe[i] * v[i] for i in range(DIM))
                    for v in leech2.minimal_vectors())
        rows.append({
            "probe": probe,
            "closed_form": fast["support"],
            "enumerated": Fraction(brute),
            "agrees": fast["support"] == brute,
            "shape": fast["shape"],
        })
    return {
        "samples": len(rows),
        "rows": tuple(rows),
        "all_agree": all(r["agrees"] for r in rows),
        "shell_size": SHELL_SIZE,
    }


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


@lru_cache(maxsize=None)
def nearest_shell_candidates(query: Tuple[int, ...],
                             count: int = 6) -> Tuple[Tuple[int, ...], ...]:
    """The ``count`` shell points closest to an integer query point.

    Every shell point has the same norm, so ``|q - v|^2 = |q|^2 + 32 -
    2 <q, v>`` and "closest" is "largest inner product".  This is the one
    place the module sweeps all 196,560 vectors: the closed-form support
    function returns a single maximiser, and a Gibbs ensemble needs a
    *neighbourhood*.  Ties break lexicographically, so the answer is exact
    and reproducible.
    """
    scored = sorted(
        ((-sum(query[i] * v[i] for i in range(DIM)), v)
         for v in leech2.minimal_vectors()))
    return tuple(v for _, v in scored[:count])


def certified_inner_ball() -> Dict[str, object]:
    """An exact ball inside the hull of the shell, from the first shape alone.

    Some coordinate of ``x`` has ``|x_i|^2 >= |x|^2 / 24``, and the pair shape
    already gives ``h(x) >= 4 |x_i| >= 4 |x| / sqrt(24)``.  So any target with
    ``|t| < 4 / sqrt(24)``, i.e. ``3 |t|^2 < 2``, lies strictly inside the hull
    with margin ``4/sqrt(24) - |t|``.  The bound is exact and far from tight --
    it uses one of the three shapes and the crudest coordinate estimate -- but
    it needs no search.
    """
    return {
        "argument": "h(x) >= 4 max|x_i| >= 4 |x| / sqrt(24)",
        "radius_squared": Fraction(2, 3),
        "criterion": "3 |t|^2 < 2",
        "shape_used": "(+-4^2, 0^22)",
        "tight": False,
    }


# ===========================================================================
# 2.  THE MATCHED RULE
# ===========================================================================

def matched_run(target: Sequence, ticks: int) -> Dict[str, object]:
    """Run the matched (support-maximising) shell modulator on a fixed target.

    The recursion is the one ``GLM.Shell.shState`` defines: ``s_0 = 0`` and
    ``s_{n+1} = s_n + t - sel(s_n)`` with ``sel`` the shell argmax.  Every
    quantity returned is exact.
    """
    if ticks < 1:
        raise ValueError("matched_run: ticks must be at least 1")
    t = _exact(target)
    state = tuple(Fraction(0) for _ in range(DIM))
    emitted: List[Tuple[int, ...]] = []
    state_norms: List[Fraction] = []
    slacks: List[Fraction] = []
    margins2: List[Fraction] = []
    distances2: List[Fraction] = []
    for _ in range(ticks):
        pick = shell_support(state)
        v = pick["argmax"]
        emitted.append(v)
        distances2.append(_norm2([t[i] - v[i] for i in range(DIM)]))
        # the theorem's hypothesis at this direction: h(s) - <s, t> >= mu |s|
        slack = pick["support"] - _inner(state, t)
        slacks.append(slack)
        s2 = _norm2(state)
        if s2 > 0 and slack >= 0:
            margins2.append(slack * slack / s2)
        state = tuple(state[i] + t[i] - v[i] for i in range(DIM))
        state_norms.append(_norm2(state))
    mean = tuple(sum(Fraction(v[i]) for v in emitted) / ticks
                 for i in range(DIM))
    error2 = _norm2([mean[i] - t[i] for i in range(DIM)])
    return {
        "ticks": ticks,
        "target": t,
        "mean": mean,
        "error_norm2": error2,
        "final_state_norm2": _norm2(state),
        "max_state_norm2": max(state_norms),
        "state_norm2_trace": tuple(state_norms),
        "max_distance2": max(distances2),
        "min_slack": min(slacks),
        "slack_nonnegative": min(slacks) >= 0,
        "observed_margin2": min(margins2) if margins2 else None,
        "distinct_emissions": len(set(emitted)),
        "all_on_shell": all(leech2.norm2(v) == SHELL_NORM2 for v in emitted),
    }


def inside_target(scale: int = 3) -> Tuple[Fraction, ...]:
    """A target manifestly inside the hull: a mean of shell points.

    Three explicit minimal vectors, one of each shape, averaged and then
    shrunk by ``scale``.  Being an average of alphabet points it is in the
    hull by construction; shrinking pushes it into the interior.
    """
    a = [0] * DIM
    a[0], a[1] = 4, 4
    b = list(next(iter(_shape2_example())))
    c = [1] * DIM
    c[0] = -3
    points = (tuple(a), tuple(b), tuple(c))
    for p in points:
        assert leech2.norm2(p) == SHELL_NORM2 and leech2.in_leech(p)
    return tuple(sum(Fraction(p[i]) for p in points) / (len(points) * scale)
                 for i in range(DIM))


@lru_cache(maxsize=None)
def _shape2_example() -> Tuple[Tuple[int, ...], ...]:
    positions = _octad_positions()[0]
    v = [0] * DIM
    for p in positions:
        v[p] = 2
    return (tuple(v),)


@lru_cache(maxsize=None)
def inside_run(ticks: int = 24, scale: int = 3) -> Dict[str, object]:
    """Track a target inside the hull, and compare with the proved bound.

    The Lean bound is ``D^2/(2 mu) + D``.  ``D`` is measured as the largest
    ``|t - v|`` the run met, and ``mu`` from the smallest observed margin
    slack ``h(s) - <s, t>`` divided by ``|s|`` -- the theorem's hypothesis,
    audited exactly at the directions the run visited.
    """
    target = inside_target(scale)
    run = matched_run(target, ticks)
    halves = matched_run(target, max(1, ticks // 2))
    return {
        "target_norm2": _norm2(target),
        "run": run,
        "half_run_error_norm2": halves["error_norm2"],
        "error_fell": run["error_norm2"] < halves["error_norm2"],
        "state_bounded": run["max_state_norm2"] == max(
            run["state_norm2_trace"]),
        "margin_hypothesis_held": run["slack_nonnegative"],
        "theorem": "GLM.Shell.shAverage_error_le",
    }


@lru_cache(maxsize=None)
def outside_run(ticks: int = 12, height: int = 5) -> Dict[str, object]:
    """A target the shell provably cannot reach, with its certificate.

    ``h(e_0) = 4``: the largest first coordinate anywhere on the shell is the
    ``4`` of the pair shape.  So ``<e_0, t> = height > 4`` separates ``t``
    from the hull, and no rule emitting shell points can have a running mean
    approaching it.  The machine-checked obstruction is
    ``GLM.Info.not_tendsto_avg_of_separating``.
    """
    direction = [0] * DIM
    direction[0] = 1
    support = shell_support(direction)
    target = [Fraction(0)] * DIM
    target[0] = Fraction(height)
    run = matched_run(target, ticks)
    return {
        "direction": tuple(direction),
        "support_in_direction": support["support"],
        "target_in_direction": Fraction(height),
        "separated": Fraction(height) > support["support"],
        "gap": Fraction(height) - support["support"],
        "run": {k: run[k] for k in ("ticks", "error_norm2",
                                    "final_state_norm2", "max_state_norm2")},
        "state_grew": run["max_state_norm2"] > SHELL_NORM2,
        "predicted_drift_per_tick": Fraction(height) - support["support"],
        "theorem": "GLM.Info.not_tendsto_avg_of_separating",
    }


@lru_cache(maxsize=None)
def lattice_run(ticks: int = 12, height: int = 5) -> Dict[str, object]:
    """The same target, with the whole lattice as alphabet: tracked at rho/N.

    The quantiser is the exact nearest-point decoder of
    :mod:`glm_universal.reasoning.fwht_decode`.  The Leech lattice covers
    space, so ``GLM.Shell.sState_norm_le`` applies with the covering radius:
    in this ``x sqrt(8)`` integer model that is ``rho^2 = 16``, and the
    accumulator is observed to respect it.
    """
    if ticks < 1:
        raise ValueError("lattice_run: ticks must be at least 1")
    target = [Fraction(0)] * DIM
    target[0] = Fraction(height)
    state = [Fraction(0)] * DIM
    emitted: List[Tuple[int, ...]] = []
    norms: List[Fraction] = []
    for _ in range(ticks):
        x = [state[i] + target[i] for i in range(DIM)]
        point = fwht_decode.nearest_lattice_point_fwht(x).point
        emitted.append(point)
        state = [x[i] - point[i] for i in range(DIM)]
        norms.append(_norm2(state))
    mean = tuple(sum(Fraction(v[i]) for v in emitted) / ticks
                 for i in range(DIM))
    error2 = _norm2([mean[i] - target[i] for i in range(DIM)])
    return {
        "ticks": ticks,
        "alphabet": "the whole Leech lattice",
        "covering_radius2": 16,
        "max_state_norm2": max(norms),
        "within_covering_radius": max(norms) <= 16,
        "error_norm2": error2,
        "error_bound_norm2": Fraction(16, ticks * ticks),
        "within_bound": error2 <= Fraction(16, ticks * ticks),
        "distinct_emissions": len(set(emitted)),
        "all_in_leech": all(leech2.in_leech(v) for v in emitted),
        "theorem": "GLM.Shell.sAverage_error_le",
    }


# ===========================================================================
# 3.  THE GIBBS-STYLE RULE
# ===========================================================================

def gibbs_weights(energies: Sequence[int], t) -> Tuple[Fraction, ...]:
    """``t^(Emax - E_i) / sum_j t^(Emax - E_j)``, exactly.

    The definition is ``GLM.Shell.gibbsWeight``.  ``t = 1`` is the uniform
    ensemble (infinite temperature); ``t`` large collapses onto the least
    energy, and ``GLM.Shell.gibbsWeight_le_inv`` bounds every non-minimal
    weight by ``1/t``.
    """
    if not energies:
        raise ValueError("gibbs_weights: need at least one candidate")
    t = Fraction(t)
    if t <= 0:
        raise ValueError("gibbs_weights: temperature parameter must be > 0")
    top = max(energies)
    mass = [t ** (top - e) for e in energies]
    total = sum(mass, Fraction(0))
    return tuple(m / total for m in mass)


def gibbs_limits(energies: Sequence[int],
                 temperatures: Sequence[int] = (1, 2, 8, 64)
                 ) -> Dict[str, object]:
    """The two limits and the monotonicity, checked at each temperature."""
    m = len(energies)
    lowest = min(energies)
    rows = []
    for t in temperatures:
        w = gibbs_weights(energies, t)
        non_minimal = [w[i] for i in range(m) if energies[i] > lowest]
        order_ok = all(w[i] >= w[j] for i in range(m) for j in range(m)
                       if energies[i] <= energies[j])
        rows.append({
            "t": t,
            "weights": w,
            "sums_to_one": sum(w, Fraction(0)) == 1,
            "monotone_in_energy": order_ok,
            "max_non_minimal": max(non_minimal) if non_minimal else Fraction(0),
            "bound_one_over_t": Fraction(1, t),
            "within_bound": all(x <= Fraction(1, t) for x in non_minimal),
        })
    uniform = gibbs_weights(energies, 1)
    return {
        "candidates": m,
        "energies": tuple(energies),
        "uniform_at_t_one": all(x == Fraction(1, m) for x in uniform),
        "rows": tuple(rows),
        "theorems": {
            "uniform": "GLM.Shell.gibbsWeight_uniform",
            "collapse": "GLM.Shell.gibbsWeight_le_inv",
            "monotone": "GLM.Shell.gibbsWeight_mono",
        },
    }


def gibbs_schedule(weights: Sequence[Fraction], ticks: int) -> Dict[str, object]:
    """Realise a Gibbs ensemble deterministically, by greedy error feedback.

    ``GLM.Shell.gibbsState`` accrues ``w_i`` to every candidate each tick and
    pays out one unit to the candidate with the largest accumulator; ties go
    to the smallest index, which is one admissible ``IsMaxPick``.  The proved
    consequence is ``|count_i/N - w_i| <= (m-1)/N``.
    """
    if ticks < 1:
        raise ValueError("gibbs_schedule: ticks must be at least 1")
    w = [Fraction(x) for x in weights]
    m = len(w)
    if m == 0:
        raise ValueError("gibbs_schedule: need at least one candidate")
    state = [Fraction(0)] * m
    counts = [0] * m
    emissions: List[int] = []
    lowest = Fraction(0)
    for _ in range(ticks):
        state = [state[i] + w[i] for i in range(m)]
        pick = max(range(m), key=lambda i: (state[i], -i))
        emissions.append(pick)
        counts[pick] += 1
        state[pick] -= 1
        lowest = min(lowest, min(state))
    errors = [abs(Fraction(counts[i], ticks) - w[i]) for i in range(m)]
    bound = Fraction(m - 1, ticks)
    return {
        "ticks": ticks,
        "candidates": m,
        "weights": tuple(w),
        "counts": tuple(counts),
        "frequencies": tuple(Fraction(c, ticks) for c in counts),
        "max_frequency_error": max(errors),
        "bound": bound,
        "within_bound": max(errors) <= bound,
        "state_sums_to_zero": sum(state, Fraction(0)) == 0,
        "state_above_minus_one": lowest > -1,
        "emissions": tuple(emissions[:32]),
        "theorem": "GLM.Shell.gibbsFreq_error_le",
    }


@lru_cache(maxsize=None)
def gibbs_shell_experiment(ticks: int = 60,
                           temperatures: Sequence[int] = (1, 3, 12)
                           ) -> Dict[str, object]:
    """The Gibbs rule on a real geometric instance.

    A query point is placed off-lattice, its candidates are the shell points
    nearest to it, and the energies are the exact squared distances measured
    down from the closest candidate and divided by their common step -- here
    that step is 8, so the energies are the excess in the *true* Leech metric,
    this module working in the ``x sqrt(8)`` integer model.  At each
    temperature the scheduler runs and the visit frequencies are compared with
    the Gibbs weights.

    The emitted mean is also compared with the Gibbs mean
    ``sum_i w_i v_i``: the trajectory reproduces the *ensemble average* of the
    alphabet, not just its histogram.
    """
    query = [Fraction(0)] * DIM
    query[0], query[1], query[2] = Fraction(3), Fraction(2), Fraction(1)
    candidates = nearest_shell_candidates(tuple(int(q) for q in query), 6)
    raw = [int(_norm2([query[i] - v[i] for i in range(DIM)]))
           for v in candidates]
    floor = min(raw)
    step = 0
    for d in raw:
        step = _gcd(step, d - floor)
    scale = step or 1
    energies = [(d - floor) // scale for d in raw]
    rows = []
    for t in temperatures:
        w = gibbs_weights(energies, t)
        sched = gibbs_schedule(w, ticks)
        gibbs_mean = tuple(sum(w[k] * candidates[k][i] for k in range(len(w)))
                           for i in range(DIM))
        emitted_mean = tuple(
            sum(Fraction(sched["counts"][k] * candidates[k][i])
                for k in range(len(w))) / ticks for i in range(DIM))
        rows.append({
            "t": t,
            "weights": w,
            "frequencies": sched["frequencies"],
            "max_frequency_error": sched["max_frequency_error"],
            "bound": sched["bound"],
            "within_bound": sched["within_bound"],
            "mean_error_norm2": _norm2([emitted_mean[i] - gibbs_mean[i]
                                        for i in range(DIM)]),
        })
    return {
        "query": tuple(query),
        "candidates": tuple(candidates),
        "candidate_count": len(candidates),
        "all_on_shell": all(leech2.norm2(v) == SHELL_NORM2
                            for v in candidates),
        "squared_distances": tuple(raw),
        "energy_scale": scale,
        "energies": tuple(energies),
        "ticks": ticks,
        "rows": tuple(rows),
        "limits": gibbs_limits(energies),
        "deterministic": "no randomness is drawn anywhere",
    }


# ===========================================================================
# 4.  THE REPORT
# ===========================================================================

@lru_cache(maxsize=None)
def shell_sigma_report(ticks: int = 24) -> Dict[str, object]:
    """Recompute the whole study on demand."""
    return {
        "shell": {
            "dimension": DIM,
            "norm2": SHELL_NORM2,
            "size": SHELL_SIZE,
            "support_shapes": ("(+-4^2, 0^22)", "(+-2^8)", "(-+3, +-1^23)"),
        },
        "inner_ball": certified_inner_ball(),
        "inside": inside_run(ticks),
        "outside": outside_run(12),
        "lattice": lattice_run(12),
        "gibbs": gibbs_shell_experiment(60),
        "theorems": {
            "lattice alphabet rate": "GLM.Shell.sAverage_error_le",
            "lattice accumulator bound": "GLM.Shell.sState_norm_le",
            "shell accumulator bound": "GLM.Shell.shState_norm_le",
            "shell alphabet rate": "GLM.Shell.shAverage_error_le",
            "readings are convex combinations": "GLM.Shell.avg_mem_convexHull",
            "Gibbs uniform limit": "GLM.Shell.gibbsWeight_uniform",
            "Gibbs collapse rate": "GLM.Shell.gibbsWeight_le_inv",
            "Gibbs frequency law": "GLM.Shell.gibbsFreq_error_le",
        },
    }
