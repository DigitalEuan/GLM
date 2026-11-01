#!/usr/bin/env python3
"""
Run ALL tests: 7 core simulations + 7 application proposals + delta-sigma showcase.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cent_compiler.simulator import (
    test_delta_sigma_integration, test_opamp_sqrt, test_pll_wrap,
)
from cent_compiler.scaled_simulator import (
    test_capacitor_differentiator, test_kcl_summer,
    test_search_coil, test_thermal_relaxation,
)
from cent_compiler.delta_sigma import flagship_demonstration

print("=" * 78)
print("CENT_COMPILER v1.0 — FULL TEST SUITE")
print("=" * 78)

print("\n### PART 1: 7 Core Simulations ###\n")
core_results = []
core_results.append(("delta-sigma integrator (£_accum)",   test_delta_sigma_integration()))
core_results.append(("op-amp sqrt (£_sqrt)",                test_opamp_sqrt()))
core_results.append(("PLL phase tracker (£_wrap)",          test_pll_wrap()))
core_results.append(("capacitor differentiator (£_rate)",   test_capacitor_differentiator()))
core_results.append(("KCL summer (£_sum)",                  test_kcl_summer()))
core_results.append(("search coil (£_spatial)",             test_search_coil()))
core_results.append(("thermal relaxation (£_eq)",           test_thermal_relaxation()))

print("\n### PART 2: Delta-Sigma Showcase ###\n")
ds_result = flagship_demonstration()
ds_pass = (ds_result.get("irrational_carrier_pass", False) and
           ds_result.get("noise_suppression_pass", False) and
           ds_result.get("ntf_slope_pass", False))

print("\n### PART 3: 7 Application Proposals ###\n")
# Import and run the application tests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
from test_applications import test_01, test_02, test_03, test_04, test_05, test_06, test_07
app_results = []
test_01(); test_02(); test_03(); test_04(); test_05(); test_06(); test_07()

from test_applications import results as app_results_raw
app_results = app_results_raw

print("\n" + "=" * 78)
print("FINAL SUMMARY")
print("=" * 78)

print(f"\nCore simulations: {sum(1 for _, p in core_results if p)}/{len(core_results)} passed")
for name, p in core_results:
    print(f"  [{'PASS' if p else 'FAIL'}] {name}")

print(f"\nDelta-Sigma showcase:")
print(f"  Irrational carrier (√2): {'PASS' if ds_result.get('irrational_carrier_pass') else 'FAIL'}")
print(f"  Noise suppression: {'PASS' if ds_result.get('noise_suppression_pass') else 'FAIL'} "
      f"({ds_result.get('suppression_db', 0):.1f} dB)")
print(f"  NTF slope: {'PASS' if ds_result.get('ntf_slope_pass') else 'FAIL'} "
      f"({ds_result.get('ntf_slope', 0):.1f} dB/dec)")

print(f"\nApplication proposals: {sum(1 for _, _, _, p in app_results if p == 'PASS')}/{len(app_results)} passed")
for name, criteria, measured, status in app_results:
    print(f"  [{status}] {name} ({measured})")

total_pass = (sum(1 for _, p in core_results if p) +
              (1 if ds_pass else 0) +
              sum(1 for _, _, _, p in app_results if p == "PASS"))
total = len(core_results) + 1 + len(app_results)
print(f"\nTOTAL: {total_pass}/{total} tests passed")
sys.exit(0 if total_pass == total else 1)
