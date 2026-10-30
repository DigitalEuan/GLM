"""Small statistics helpers (no scipy): chi-square p-values via the regularised gamma function."""
import math
import numpy as np

def gammaincc(a, x):
    """Regularised upper incomplete gamma Q(a, x)."""
    if x <= 0:
        return 1.0
    if x < a + 1:  # series for P
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(100000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15:
                break
        return max(0.0, 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a)))
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d   # continued fraction for Q
    for i in range(1, 100000):
        an = -i * (i - a); b += 2
        d = an * d + b; d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c; c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d; delta = d * c; h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return h * math.exp(-x + a * math.log(x) - math.lgamma(a))

def chi2_test(observed, expected_prob, min_expected=5.0):
    """Pearson chi-square of counts against probabilities; cells with small expectation pooled."""
    obs = np.asarray(observed, dtype=float); p = np.asarray(expected_prob, dtype=float)
    n = obs.sum(); exp = p * n
    keep = exp >= min_expected
    o2 = list(obs[keep]); e2 = list(exp[keep])
    if (~keep).any() and exp[~keep].sum() > 0:
        o2.append(obs[~keep].sum()); e2.append(exp[~keep].sum())
    o2 = np.array(o2); e2 = np.array(e2)
    nz = e2 > 0
    if (obs[exp == 0] > 0).any():
        return float("inf"), len(o2) - 1, 0.0
    stat = float(((o2[nz] - e2[nz]) ** 2 / e2[nz]).sum()); dof = int(nz.sum()) - 1
    return stat, dof, gammaincc(dof / 2.0, stat / 2.0) if dof > 0 else 1.0

def verdict(p):
    return "consistent with the no-pattern prediction" if p > 1e-3 else "PATTERN DETECTED"
