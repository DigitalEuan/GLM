"""
The ∆ simulator.

Actually runs three ∆ implementations in Python and verifies they produce
correct outputs for their respective £:

  1. Delta-sigma modulator (digital ∆) for £_accum (temporal integration)
     - Feed a current waveform I(t); the bitstream's running sum should
       converge to ∫I(t)dt.

  2. Op-amp feedback loop (analog ∆) for £_sqrt (square-root extraction)
     - Iterate y(n+1) = y(n) + k·(x - y(n)²); verify y → √x.

  3. PLL (electrical ∆) for £_wrap (phase tracking)
     - Simulate VCO phase tracking a reference; verify lock.

Each simulation is exact (uses Fraction or float with explicit tolerance).
"""
from __future__ import annotations
import math
from fractions import Fraction
from typing import Callable, List, Tuple


# ---------------------------------------------------------------------------
# 1. Delta-sigma modulator (for £_accum)
# ---------------------------------------------------------------------------

def simulate_delta_sigma_integrator(
    input_signal: Callable[[int], float],
    n_samples: int,
) -> Tuple[List[int], List[float]]:
    """
    Simulate a first-order delta-sigma modulator as an integrator.

    Structure:
      integrator(n+1) = integrator(n) + (input(n) - feedback(n))
      output(n) = +1 if integrator(n) > 0 else -1
      feedback(n) = output(n)

    The bitstream `output` has the property:
      running_average(output[0:n]) ≈ running_average(input[0:n])
    Therefore:
      running_sum(output[0:n]) ≈ running_sum(input[0:n]) ≈ ∫input dt

    Returns (bitstream, running_sums).
    """
    integrator = 0.0
    bitstream: List[int] = []
    running_sums: List[float] = []
    running_sum = 0.0
    prev_output = 0.0

    for n in range(n_samples):
        x = input_signal(n)
        integrator += x - prev_output
        output = 1.0 if integrator > 0 else -1.0
        prev_output = output
        bitstream.append(int(output))
        running_sum += output
        running_sums.append(running_sum)

    return bitstream, running_sums


def test_delta_sigma_integration():
    """Test: integrate a constant I = 0.7 for 1000 samples.
    Expected: ∫I dt = 0.7 × 1000 = 700.
    The bitstream's running sum should converge to 700.
    """
    print("=" * 70)
    print("TEST 1: Delta-sigma modulator as integrator for £_accum")
    print("=" * 70)
    print("£: Q(t) = ∫I(t)dt, with I(t) = 0.7 (constant)")
    print("∆: first-order delta-sigma modulator (digital)")
    print("Expected: running_sum(bitstream) → 700")
    print()

    I_const = 0.7
    n_samples = 1000
    input_signal = lambda n: I_const
    bitstream, running_sums = simulate_delta_sigma_integrator(input_signal, n_samples)

    final_sum = running_sums[-1]
    expected = I_const * n_samples
    error = abs(final_sum - expected)
    rel_error = error / expected

    print(f"  samples:        {n_samples}")
    print(f"  input:          I = {I_const} (constant)")
    print(f"  expected sum:   {expected}")
    print(f"  actual sum:     {final_sum}")
    print(f"  abs error:      {error:.4f}")
    print(f"  rel error:      {rel_error:.6f} ({rel_error*100:.3f}%)")
    print(f"  bitstream:      first 20 bits = {bitstream[:20]}")
    print(f"  bitstream avg:  {sum(bitstream)/len(bitstream):.6f} (should → {I_const})")
    print()
    print(f"  PASS: {'YES' if rel_error < 0.01 else 'no'} (tolerance 1%)")
    print()
    return rel_error < 0.01


# ---------------------------------------------------------------------------
# 2. Op-amp feedback loop (for £_sqrt)
# ---------------------------------------------------------------------------

def simulate_opamp_sqrt(
    x: float,
    n_iterations: int = 100,
    gain: float = 0.1,
    y_init: float = 1.0,
) -> Tuple[float, List[float]]:
    """
    Simulate an op-amp feedback loop extracting √x.

    The op-amp drives y until y² = x. Discrete approximation:
      y(n+1) = y(n) + k·(x - y(n)²)
    This is gradient descent on (y² - x)², converging to y = √x.

    Returns (final_y, history).
    """
    y = y_init
    history = [y]
    for _ in range(n_iterations):
        error = x - y * y
        y += gain * error
        history.append(y)
    return y, history


def test_opamp_sqrt():
    """Test: extract √5 via op-amp feedback.
    Expected: √5 ≈ 2.2360679...
    """
    print("=" * 70)
    print("TEST 2: Op-amp feedback loop for £_sqrt")
    print("=" * 70)
    print("£: y = √x, with x = 5")
    print("∆: op-amp + multiplier in feedback (analog)")
    print("Expected: y → √5 ≈ 2.236068")
    print()

    x = 5.0
    n_iter = 100
    y_final, history = simulate_opamp_sqrt(x, n_iterations=n_iter, gain=0.1)
    expected = math.sqrt(x)
    error = abs(y_final - expected)
    rel_error = error / expected

    print(f"  iterations:     {n_iter}")
    print(f"  input:          x = {x}")
    print(f"  expected:       √x = {expected:.9f}")
    print(f"  actual:         y  = {y_final:.9f}")
    print(f"  abs error:      {error:.2e}")
    print(f"  rel error:      {rel_error:.2e}")
    print(f"  convergence:    y(1)={history[1]:.4f}, y(10)={history[10]:.4f}, "
          f"y(50)={history[50]:.6f}, y(100)={history[100]:.9f}")
    print()
    print(f"  PASS: {'YES' if rel_error < 1e-4 else 'no'} (tolerance 0.01%)")
    print()
    return rel_error < 1e-4


# ---------------------------------------------------------------------------
# 3. PLL phase tracking (for £_wrap)
# ---------------------------------------------------------------------------

def simulate_pll(
    ref_frequency: float,
    n_samples: int,
    sample_rate: float = 1000.0,
    kvco: float = 10.0,
    kpd: float = 1.0,
    loop_gain: float = 0.3,
    ki: float = 0.01,
    f0: float = 0.0,
) -> Tuple[List[float], List[float], List[float]]:
    """
    Simulate a type-2 PLL (PI loop filter) tracking a reference frequency.

    Structure:
      - Reference: φ_ref(n) = 2π·f_ref·n/sample_rate
      - Phase detector: pd_out = sin(φ_ref - φ_vco)
      - PI loop filter: integral += ki·pd_out; control = loop_gain·pd_out + integral
      - VCO: f_vco = f0 + kvco·control
             φ_vco(n+1) = φ_vco(n) + 2π·f_vco/sample_rate

    Type-2 PLL drives BOTH frequency error AND phase error to zero.
    """
    phi_vco = 0.0
    integral = 0.0

    phi_ref_history = []
    phi_vco_history = []
    phase_error_history = []

    for n in range(n_samples):
        phi_ref = 2 * math.pi * ref_frequency * n / sample_rate
        pd_out = kpd * math.sin(phi_ref - phi_vco)
        integral += ki * pd_out
        control = loop_gain * pd_out + integral
        f_vco = f0 + kvco * control
        phi_vco += 2 * math.pi * f_vco / sample_rate

        phi_ref_wrapped = phi_ref % (2 * math.pi)
        phi_vco_wrapped = phi_vco % (2 * math.pi)
        phi_ref_history.append(phi_ref_wrapped)
        phi_vco_history.append(phi_vco_wrapped)
        phase_error_history.append(phi_ref - phi_vco)

    return phi_ref_history, phi_vco_history, phase_error_history


def test_pll_wrap():
    """Test: PLL tracks a 5 Hz reference frequency.
    Expected: after lock, phase error → 0 (or small constant).
    """
    print("=" * 70)
    print("TEST 3: PLL phase tracking for £_wrap")
    print("=" * 70)
    print("£: θ(t) = (∫ω dt) mod 2π, with ω = 2π·5 rad/s (5 Hz)")
    print("∆: PLL with VCO + phase detector + loop filter")
    print("Expected: phase error → 0 after lock")
    print()

    ref_freq = 5.0  # Hz
    n_samples = 5000
    sample_rate = 1000.0

    phi_ref, phi_vco, phase_err = simulate_pll(
        ref_freq, n_samples, sample_rate,
        kvco=10.0, kpd=1.0, loop_gain=0.3, ki=0.01,
    )

    # Check lock: last 200 samples' phase error should be small
    final_errors = phase_err[-200:]
    # Normalize to [-π, π]
    final_errors_norm = []
    for e in final_errors:
        while e > math.pi:
            e -= 2 * math.pi
        while e < -math.pi:
            e += 2 * math.pi
        final_errors_norm.append(e)

    avg_err = sum(abs(e) for e in final_errors_norm) / len(final_errors_norm)
    max_err = max(abs(e) for e in final_errors_norm)

    # Also check VCO frequency converges to reference
    # Compute VCO freq from phase differences in last 200 samples
    vco_freqs = []
    for i in range(-200, -1):
        dphi = phi_vco[i+1] - phi_vco[i]
        if dphi < 0:
            dphi += 2 * math.pi
        vco_freqs.append(dphi * sample_rate / (2 * math.pi))
    avg_vco_freq = sum(vco_freqs) / len(vco_freqs)
    freq_error = abs(avg_vco_freq - ref_freq)

    print(f"  samples:        {n_samples}")
    print(f"  sample rate:    {sample_rate} Hz")
    print(f"  ref frequency:  {ref_freq} Hz")
    print(f"  avg VCO freq:   {avg_vco_freq:.4f} Hz (last 200 samples)")
    print(f"  freq error:     {freq_error:.6f} Hz")
    print(f"  avg phase err:  {avg_err:.6f} rad (last 200 samples)")
    print(f"  max phase err:  {max_err:.6f} rad")
    print()
    print(f"  PASS: {'YES' if freq_error < 0.1 and avg_err < 0.1 else 'no'} "
          f"(freq tol 0.1 Hz, phase tol 0.1 rad)")
    print()
    return freq_error < 0.1 and avg_err < 0.1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = []
    print()
    results.append(("delta-sigma integrator (£_accum)", test_delta_sigma_integration()))
    results.append(("op-amp sqrt (£_sqrt)",              test_opamp_sqrt()))
    results.append(("PLL phase tracker (£_wrap)",        test_pll_wrap()))

    print("=" * 70)
    print("SIMULATION SUMMARY")
    print("=" * 70)
    for name, passed in results:
        flag = "PASS" if passed else "FAIL"
        print(f"  [{flag}] {name}")
    n_pass = sum(1 for _, p in results if p)
    print(f"\n  {n_pass}/{len(results)} simulations passed")
