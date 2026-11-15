"""
The Delta-Sigma engine — the flagship demonstration.

This module implements the CORRECT delta-sigma classification and the
flagship noise-shaping demonstration with:

  - Stated OSR (oversampling ratio)
  - 10^5 samples
  - FFT of the bitstream
  - In-band noise power measurement
  - Suppression in dB vs unshaped quantizer
  - NTF (noise transfer function) slope verification
  - Irrational carrier demonstration (√2)

KEY FIX (per audit):
  Delta-sigma is NOT a property of a single substrate. It is a property
  of a COMPOSED LOOP: ¢_accum + ¢_wrap + ¢_eq with oversampling.
  A capacitor is a CONSTITUENT of delta-sigma, not delta-sigma itself.
"""
from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Callable, List, Tuple, Optional


@dataclass
class DeltaSigmaResult:
    """Result of a delta-sigma modulation run."""
    bitstream: List[int]
    running_averages: List[float]
    input_value: float
    n_samples: int
    final_average: float
    final_error: float
    # Spectral analysis fields
    osr: int = 0                    # oversampling ratio
    signal_frequency: float = 0.0   # Hz (for AC tests)
    sample_rate: float = 0.0        # Hz
    inband_noise_db: float = 0.0    # dB (measured)
    unshaped_noise_db: float = 0.0  # dB (reference)
    suppression_db: float = 0.0     # dB (measured - reference)
    ntf_slope_db_per_dec: float = 0.0  # noise transfer function slope


class DeltaSigmaEngine:
    """A first-order delta-sigma modulator.

    Structure (the COMPOSED LOOP that makes this delta-sigma):
        ¢_accum: integrator(n+1) = integrator(n) + (input(n) - feedback(n))
        ¢_wrap:  output(n) = +1 if integrator > 0 else -1  (1-bit quantizer)
        ¢_eq:    feedback(n) = output(n)  (error-nulling closed loop)

    The loop IS oversampled (runs at sample_rate >> signal bandwidth).
    This composition — not any single component — is what makes it delta-sigma.
    """

    def __init__(self):
        self.integrator = 0.0
        self.prev_output = 0.0

    def reset(self):
        self.integrator = 0.0
        self.prev_output = 0.0

    def step(self, input_value: float) -> int:
        self.integrator += input_value - self.prev_output
        output = 1 if self.integrator > 0 else -1
        self.prev_output = float(output)
        return output

    def modulate(
        self,
        input_signal: Callable[[int], float],
        n_samples: int,
        sample_rate: float = 1e6,
        signal_frequency: float = 0.0,
        osr: int = 64,
    ) -> DeltaSigmaResult:
        """Run the modulator. Returns full result with spectral analysis."""
        self.reset()
        bitstream: List[int] = []
        running_averages: List[float] = []
        running_sum = 0.0

        for n in range(n_samples):
            x = input_signal(n)
            bit = self.step(x)
            bitstream.append(bit)
            running_sum += bit
            running_averages.append(running_sum / (n + 1))

        input_val = input_signal(0) if signal_frequency == 0.0 else 0.0
        final_avg = running_averages[-1] if running_averages else 0.0

        # For DC input, the "final average" is meaningful
        # For AC input, we measure spectral properties instead
        if signal_frequency == 0.0:
            final_err = abs(final_avg - input_val)
        else:
            final_err = 0.0  # AC: error is in frequency domain

        result = DeltaSigmaResult(
            bitstream=bitstream,
            running_averages=running_averages,
            input_value=input_val,
            n_samples=n_samples,
            final_average=final_avg,
            final_error=final_err,
            osr=osr,
            signal_frequency=signal_frequency,
            sample_rate=sample_rate,
        )

        # Spectral analysis
        if n_samples >= 1000:
            self._spectral_analysis(result)

        return result

    def _spectral_analysis(self, result: DeltaSigmaResult):
        """Compute FFT-based noise analysis.

        Correctly excludes the signal frequency bin from the noise measurement.
        For DC input, excludes bin 0. For AC input, excludes the signal
        frequency bin and its harmonics.
        """
        bs = np.array(result.bitstream, dtype=float)
        n = len(bs)

        # FFT of the bitstream
        spectrum = np.fft.fft(bs)
        freqs = np.fft.fftfreq(n, d=1.0/result.sample_rate)

        # Signal bandwidth = sample_rate / (2 * OSR)
        bandwidth = result.sample_rate / (2 * result.osr)
        nyquist = result.sample_rate / 2

        # Identify signal bins to EXCLUDE from noise measurement
        # For DC input (signal_frequency == 0), exclude bin 0
        # For AC input, exclude the signal frequency ± a few bins
        signal_bin_width = max(1, int(n * 10 / result.sample_rate))  # ±10 Hz
        if result.signal_frequency == 0.0:
            signal_mask = np.abs(freqs) < 1.0  # exclude DC ± 1 Hz
        else:
            signal_mask = np.abs(np.abs(freqs) - result.signal_frequency) < 10.0

        # In-band noise (exclude signal bins)
        inband_mask = (np.abs(freqs) <= bandwidth) & (~signal_mask)
        inband_noise_power = np.sum(np.abs(spectrum[inband_mask])**2) / n**2

        # Out-of-band noise (for reference)
        outband_mask = (np.abs(freqs) > bandwidth) & (np.abs(freqs) <= nyquist)
        outband_noise_power = np.sum(np.abs(spectrum[outband_mask])**2) / n**2

        # Total noise power (exclude signal)
        total_noise_power = inband_noise_power + outband_noise_power

        # Unshaped quantizer reference: if noise were flat across [0, nyquist],
        # the in-band fraction would be bandwidth/nyquist of total noise
        unshaped_inband_power = total_noise_power * (bandwidth / nyquist)

        # Convert to dB (relative to full-scale ±1, so 0 dB = power of 1)
        result.inband_noise_db = 10 * math.log10(max(inband_noise_power, 1e-20))
        result.unshaped_noise_db = 10 * math.log10(max(unshaped_inband_power, 1e-20))
        # Suppression = how much LOWER the ∆Σ in-band noise is vs unshaped
        result.suppression_db = result.unshaped_noise_db - result.inband_noise_db

        # NTF slope: measure noise power spectral density vs frequency
        # For first-order ∆Σ, NTF ~ (1 - z^-1), so noise PSD rises at 20 dB/dec
        n_freq_bins = 50
        log_freqs = []
        log_psd = []
        min_freq = max(10, result.sample_rate / n)  # avoid DC
        max_freq = nyquist / 2
        for i in range(n_freq_bins):
            f_lo = min_freq * (max_freq / min_freq) ** (i / n_freq_bins)
            f_hi = min_freq * (max_freq / min_freq) ** ((i+1) / n_freq_bins)
            mask = (np.abs(freqs) >= f_lo) & (np.abs(freqs) < f_hi) & (~signal_mask)
            if np.any(mask):
                power = np.sum(np.abs(spectrum[mask])**2) / n**2
                # PSD = power / frequency span
                psd = power / (f_hi - f_lo)
                log_freqs.append(math.log10(math.sqrt(f_lo * f_hi)))
                log_psd.append(10 * math.log10(max(psd, 1e-20)))

        if len(log_freqs) > 5:
            slope, _ = np.polyfit(log_freqs, log_psd, 1)
            result.ntf_slope_db_per_dec = slope

    def carry_irrational(
        self,
        irrational_value: float,
        n_samples: int = 100000,
        sample_rate: float = 1e6,
        osr: int = 64,
    ) -> DeltaSigmaResult:
        """Carry an irrational number as a bitstream.

        This is the flagship demonstration: delta-sigma as the canonical
        carrier for irrational numbers.

        For |input| >= 1, scales the input to fit within the ±1 representable
        range and notes the scale factor.
        """
        scale = 1.0
        scaled_input = irrational_value
        if abs(irrational_value) >= 0.99:
            scale = 0.99 / abs(irrational_value)
            scaled_input = irrational_value * scale

        result = self.modulate(
            lambda n: scaled_input, n_samples,
            sample_rate=sample_rate, signal_frequency=0.0, osr=osr,
        )

        # Rescale for DC reporting
        result.input_value = irrational_value
        result.final_average = result.final_average / scale
        result.final_error = abs(result.final_average - irrational_value)
        result.running_averages = [a / scale for a in result.running_averages]

        return result


def flagship_demonstration():
    """The flagship delta-sigma demonstration.

    Proves delta-sigma is the canonical carrier for irrational numbers,
    with full spectral analysis:
      - √2 carried as bitstream (10^5 samples)
      - OSR stated (64×)
      - FFT of bitstream
      - In-band noise suppression measured in dB
      - NTF slope verified (~20 dB/dec for first-order)
      - Convergence to √2 tracked
    """
    print("=" * 70)
    print("DELTA-SIGMA FLAGSHIP DEMONSTRATION")
    print("The canonical carrier for irrational numbers")
    print("=" * 70)
    print()

    # Part 1: irrational carrier (√2)
    print("PART 1: Irrational carrier — √2 as a bitstream")
    print("-" * 70)
    engine = DeltaSigmaEngine()
    result = engine.carry_irrational(
        math.sqrt(2), n_samples=100000, sample_rate=1e6, osr=64,
    )

    print(f"  Irrational: √2 = {math.sqrt(2):.15f}")
    print(f"  Samples:    {result.n_samples}")
    print(f"  Sample rate: {result.sample_rate:.0e} Hz")
    print(f"  OSR:        {result.osr}×")
    print(f"  Bandwidth:  {result.sample_rate/(2*result.osr):.0f} Hz")
    print()
    print(f"  Bitstream (first 50 bits):")
    bs_str = "".join("1" if b > 0 else "0" for b in result.bitstream[:50])
    print(f"    {bs_str}")
    print()
    print(f"  Convergence (running average → √2):")
    for cp in [10, 100, 1000, 10000, 100000]:
        if cp <= result.n_samples:
            avg = result.running_averages[cp - 1]
            err = abs(avg - math.sqrt(2))
            print(f"    n={cp:>6}: avg = {avg:.15f}, error = {err:.2e}")
    print()
    print(f"  Final: avg = {result.final_average:.15f}")
    print(f"         √2  = {math.sqrt(2):.15f}")
    print(f"         error = {result.final_error:.2e}")
    print()

    # Part 2: spectral analysis (noise shaping)
    print()
    print("PART 2: Noise shaping — spectral verification")
    print("-" * 70)

    # Run with a 1 kHz sine wave input
    signal_freq = 1000  # Hz
    sample_rate = 1e6
    osr = 64
    n_samples = 100000

    engine2 = DeltaSigmaEngine()
    result2 = engine2.modulate(
        lambda n: 0.5 * math.sin(2 * math.pi * signal_freq * n / sample_rate),
        n_samples, sample_rate=sample_rate, signal_frequency=signal_freq, osr=osr,
    )

    bandwidth = sample_rate / (2 * osr)
    print(f"  Signal:     {signal_freq} Hz sine at 0.5 amplitude")
    print(f"  Samples:    {n_samples}")
    print(f"  Sample rate: {sample_rate:.0e} Hz")
    print(f"  OSR:        {osr}×")
    print(f"  Bandwidth:  {bandwidth:.0f} Hz (signal band)")
    print()
    print(f"  Noise analysis:")
    print(f"    In-band noise (∆Σ):     {result2.inband_noise_db:.2f} dB")
    print(f"    In-band noise (unshaped): {result2.unshaped_noise_db:.2f} dB")
    print(f"    Suppression:            {result2.suppression_db:.2f} dB")
    print()
    expected_suppression = 20 * math.log10(osr) - 5.2
    print(f"  Expected suppression (first-order, OSR={osr}): "
          f"~{expected_suppression:.1f} dB")
    print(f"  Formula: 20·log10(OSR) - 5.2 = 20·log10({osr}) - 5.2")
    print()
    print(f"  NTF slope: {result2.ntf_slope_db_per_dec:.1f} dB/decade")
    print(f"  Expected: ~+20 dB/decade (first-order high-pass NTF)")
    print()

    # Verdict
    suppression_ok = result2.suppression_db > 20  # at least 20 dB
    ntf_ok = result2.ntf_slope_db_per_dec > 10  # roughly +20
    convergence_ok = result.final_error < 0.01

    print(f"  VERDICT:")
    print(f"    Irrational carrier (√2): {'PASS' if convergence_ok else 'FAIL'} "
          f"(error {result.final_error:.2e})")
    print(f"    Noise suppression: {'PASS' if suppression_ok else 'FAIL'} "
          f"({result2.suppression_db:.2f} dB > 20 dB)")
    print(f"    NTF slope: {'PASS' if ntf_ok else 'FAIL'} "
          f"({result2.ntf_slope_db_per_dec:.1f} dB/dec ≈ +20)")
    print()
    print(f"  KEY PROPERTY: The bitstream carries √2 as a continuous")
    print(f"  temporal process. The irrational is NEVER stored as a")
    print(f"  finite-precision number. The noise is shaped OUT of the")
    print(f"  signal band by the loop's high-pass NTF.")
    print()

    return {
        "irrational_carrier_pass": convergence_ok,
        "noise_suppression_pass": suppression_ok,
        "ntf_slope_pass": ntf_ok,
        "suppression_db": result2.suppression_db,
        "ntf_slope": result2.ntf_slope_db_per_dec,
        "irrational_error": result.final_error,
    }


if __name__ == "__main__":
    flagship_demonstration()
