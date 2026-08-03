#!/usr/bin/env python3
"""Master test runner — runs all v3.17 + v3.18 test suites (75 tests total)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

exit_codes = []
print("############################################################")
print("#  GLM v3.17 + v3.18 — FULL TEST SUITE (75 tests)          #")
print("############################################################")

print("\n>>> SUITE 1: test_v317_levelling.py (30 tests)")
import test_v317_levelling as s1
exit_codes.append(s1.main())

print("\n>>> SUITE 2: test_v317_signal_and_sovereign.py (16 tests)")
import test_v317_signal_and_sovereign as s2
exit_codes.append(s2.main())

print("\n>>> SUITE 3: test_v318_levelling.py (29 tests)")
import test_v318_levelling as s3
exit_codes.append(s3.main())

print("\n############################################################")
print("#  OVERALL                                                  #")
print("############################################################")
total_pass = sum(1 for e in exit_codes if e == 0)
print(f"  {total_pass}/{len(exit_codes)} suites passed")
sys.exit(0 if all(e == 0 for e in exit_codes) else 1)
