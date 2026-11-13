#!/usr/bin/env python3
"""
Extract all 19 wheels' data into individual JSON files in wheels/.

Each file contains:
  - id
  - title
  - axioms (list of strings)
  - cases (list of {id, equation, expected_dimensional, expected_derivable,
                    physical_status, note})
  - quantities (list of names appearing in axioms)
  - dimensions (per-quantity SI exponent vectors over the 8 reference axes)
  - junctions (which declared junctions involve this wheel)
  - non_identities (which declared non-identities involve this wheel)
"""
import sys, os, json
from fractions import Fraction

# Add the cent_compiler package to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cent_compiler.wheels import WHEELS as WHEELS_10, REFERENCE_DIMENSIONS, REFERENCE_AXES
from cent_compiler.wheels_extended import JUNCTIONS, NON_IDENTITIES
from cent_compiler.wheels_19 import WHEELS_19

WHEELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wheels")
os.makedirs(WHEELS_DIR, exist_ok=True)


def fraction_to_str(v):
    """Convert Fraction to a JSON-serializable string."""
    if isinstance(v, Fraction):
        return str(v)
    return v


def extract_wheel_data(wheel):
    """Extract all data for one wheel into a dict."""
    # Quantities appearing in axioms
    quantities = set()
    for axiom in wheel.axioms:
        # Parse the axiom to get names
        import ast
        for side in axiom.split("="):
            try:
                tree = ast.parse(side.strip().replace("^", "**"), mode="eval")
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        quantities.add(node.id)
            except Exception:
                pass
    quantities = sorted(quantities)

    # Dimensions for each quantity
    dims = {}
    for q in quantities:
        vec = REFERENCE_DIMENSIONS.get(q)
        if vec is not None:
            dims[q] = {
                "axes": list(REFERENCE_AXES),
                "exponents": [int(x) for x in vec],
            }
        else:
            dims[q] = None

    # Cases
    cases = []
    for c in wheel.cases:
        cases.append({
            "id": c.id,
            "equation": c.equation,
            "expected_dimensional": c.expected_dimensional,
            "expected_derivable": c.expected_derivable,
            "physical_status": c.physical_status,
            "expected_dimensional_explicit": c.expected_dimensional_explicit,
            "note": c.note,
        })

    # Junctions involving this wheel
    wheel_junctions = []
    for j in JUNCTIONS:
        if j.wheel_a == wheel.id or j.wheel_b == wheel.id:
            other = j.wheel_b if j.wheel_a == wheel.id else j.wheel_a
            name_b = j.name_b if j.name_b is not None else j.name
            wheel_junctions.append({
                "other_wheel": other,
                "name_in_this_wheel": j.name if j.wheel_a == wheel.id else name_b,
                "name_in_other_wheel": name_b if j.wheel_a == wheel.id else j.name,
                "reason": j.reason,
            })

    # Non-identities involving this wheel
    wheel_nonident = []
    for n in NON_IDENTITIES:
        if n.wheel_a == wheel.id or n.wheel_b == wheel.id:
            other = n.wheel_b if n.wheel_a == wheel.id else n.wheel_a
            wheel_nonident.append({
                "other_wheel": other,
                "name": n.name,
                "reason": n.reason,
            })

    return {
        "id": wheel.id,
        "title": wheel.title,
        "axioms": list(wheel.axioms),
        "cases": cases,
        "quantities": quantities,
        "dimensions": dims,
        "junctions": wheel_junctions,
        "non_identities": wheel_nonident,
    }


def main():
    print(f"Extracting {len(WHEELS_19)} wheels to {WHEELS_DIR}/")

    all_wheels = {}
    for wheel in WHEELS_19:
        data = extract_wheel_data(wheel)
        filepath = os.path.join(WHEELS_DIR, f"{wheel.id}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=fraction_to_str)
        all_wheels[wheel.id] = {
            "title": wheel.title,
            "n_axioms": len(wheel.axioms),
            "n_cases": len(wheel.cases),
            "n_quantities": len(data["quantities"]),
            "file": f"{wheel.id}.json",
        }
        print(f"  {wheel.id}.json  ({len(wheel.axioms)} axioms, "
              f"{len(wheel.cases)} cases, {len(data['quantities'])} quantities)")

    # Write index.json
    index = {
        "description": "The 19 engineering formula wheels (W1-W19) that form the data substrate for the cent compiler.",
        "total_wheels": len(WHEELS_19),
        "total_axioms": sum(len(w.axioms) for w in WHEELS_19),
        "total_cases": sum(len(w.cases) for w in WHEELS_19),
        "axes": list(REFERENCE_AXES),
        "wheels": all_wheels,
        "junctions": [
            {
                "wheel_a": j.wheel_a,
                "wheel_b": j.wheel_b,
                "name_a": j.name,
                "name_b": j.name_b if j.name_b is not None else j.name,
                "reason": j.reason,
            }
            for j in JUNCTIONS
        ],
        "non_identities": [
            {
                "wheel_a": n.wheel_a,
                "wheel_b": n.wheel_b,
                "name": n.name,
                "reason": n.reason,
            }
            for n in NON_IDENTITIES
        ],
    }
    index_path = os.path.join(WHEELS_DIR, "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, default=fraction_to_str)
    print(f"\n  index.json  (summary of all {len(WHEELS_19)} wheels, "
          f"{len(JUNCTIONS)} junctions, {len(NON_IDENTITIES)} non-identities)")
    print(f"\nDone. {len(WHEELS_19) + 1} files written to {WHEELS_DIR}/")


if __name__ == "__main__":
    main()
