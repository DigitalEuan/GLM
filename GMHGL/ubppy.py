"""
UBP-Py v2.3 (Standard) - Signature Alignment
============================================
Fixed TypeError by strictly matching the UBPPyVM signature 
defined in ubp_py_runtime.py.
"""

import argparse
import os
import json
from fractions import Fraction

from ubp_py_runtime import UBPPyVM
from ubp_py_lang import execute_program
from ubp_viz import save_scene_3d

def load_program_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, 'r') as f:
        return f.read()

def run_demo(vm: UBPPyVM) -> None:
    """Demonstration of VM usage."""
    print("--- INITIALIZING UBP-PY v2.3 STANDARD (DEMO) ---")

    # 1. Create a starting value
    vm.let("START_VAL", "1/1", tier=0, category="QUANTITY")
    
    # 2. Run a manual synthesis
    vm.synth("STEP_1", "2xSTART_VAL", u_score=1.0)
    
    # 3. Audit the result
    vm.audit("STEP_1")

    # 4. Save results
    vm.commit()
    
    # 5. Update Visualization
    if hasattr(vm, 'to_scene_3d'):
        save_scene_3d(vm.to_scene_3d())
        print("[Visual] Scene updated.")
    else:
        print("[Visual] Warning: to_scene_3d() method missing in runtime.")

def main() -> None:
    ap = argparse.ArgumentParser(prog="ubp_py_v2_standard")
    ap.add_argument("--program", type=str, default=None, help="Path to .ubp text program")
    ap.add_argument("--lattice", type=str, default="ubp_py_lattice.json")
    args = ap.parse_args()

    # Initialize VM - STRICT MATCH for ubp_py_runtime.py
    vm = UBPPyVM(
        kb_path='ubp_system_kb.json',
        lattice_path=args.lattice
    )

    if args.program is None:
        run_demo(vm)
        return

    # Execute from file
    text = load_program_file(args.program)
    if text:
        execute_program(vm, text)
        vm.commit()
        if hasattr(vm, 'to_scene_3d'):
            save_scene_3d(vm.to_scene_3d())
        print("--- UBP-Py Program Complete ---")
    else:
        print(f"Error: Program file '{args.program}' is empty or not found.")

if __name__ == "__main__":
    main()