#!/usr/bin/env python3
"""
ONE test. Validates the core: encode → snap → measure → commit.

The snap IS the base operation. This test validates it works.
"""

import sys
from pathlib import Path

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/download/arc_agi_17')

from glm_clean import Mind, Body, DataObject, encode, Snap


def test_encode():
    """Test that encoding produces DataObjects."""
    print("=== ENCODE ===")
    for inp in ['cat', 'dog', 'red', 7, 'father']:
        obj = encode(inp)
        assert isinstance(obj, DataObject)
        assert len(obj.bits) == 24
        print(f"  {str(inp):<10} → int={obj.to_int():<10} OK")
    print()


def test_snap():
    """Test that the snap (base operation) works for all patterns."""
    print("=== SNAP (the base operation) ===")
    mind = Mind(state_path=Path('/tmp/glm_snap_test.json'))
    for word in ['cat', 'dog', 'red', 'father', 'mother']:
        snap_result = mind.perceive(word)
        # Every pattern should snap (weight ≤ 4 now covered)
        assert snap_result.correctable, f"{word} not correctable!"
        # After snap, syndrome should be 0 (lawful)
        assert snap_result.after_syndrome_weight == 0, f"{word} after snap has nonzero syndrome!"
        print(f"  {word}: {snap_result.before_int} → {snap_result.after_int} "
              f"(tax={snap_result.syndrome_tax}, dist={snap_result.correction_distance})")
    print()


def test_measure():
    """Test that measure produces NRCI and regime."""
    print("=== MEASURE ===")
    mind = Mind(state_path=Path('/tmp/glm_snap_test.json'))
    for word in ['cat', 'dog', 'red', 'blue', 'father']:
        obj = encode(word)
        nrci = mind.measure.nrci(obj)
        regime = mind.measure.regime(obj)
        shells = mind.measure.describe(obj)
        assert 0 < nrci <= 1
        print(f"  {word:<10} NRCI={nrci:.4f} regime={regime.name} s0={shells.shell0_golay:.3f}")
    print()


def test_cycle():
    """Test the full mind cycle (snap-based)."""
    print("=== CYCLE (snap-based) ===")
    mind = Mind(state_path=Path('/tmp/glm_snap_test.json'))
    for w in ['cat', 'dog', 'father', 'mother']:
        mind.state.add_node(w, encode(w), domain='language')
    result = mind.cycle('cat', context='test')
    assert 'before_int' in result
    assert 'after_int' in result
    assert 'syndrome_tax' in result
    print(f"  cycle('cat'): {result['before_int']} → {result['after_int']} "
          f"(tax={result['syndrome_tax']})")
    print(f"  NRCI={result['nrci']:.4f} regime={result['regime']} "
          f"proposals={result['n_proposals']}")
    print()


def test_tct_method():
    """Test that TCT is a method on the mind (using snap results)."""
    print("=== TCT (method, on snap result) ===")
    mind = Mind(state_path=Path('/tmp/glm_snap_test.json'))
    snap_result = mind.perceive('cat')
    tct = mind.think_three_column(snap_result)
    assert 'language' in tct
    assert 'math' in tct
    assert 'script' in tct
    print(f"  language: {tct['language']}")
    print(f"  math: {tct['math']}")
    print(f"  script: {tct['script']}")
    print()


def test_body_grows():
    """Test that the body grows by learning."""
    print("=== BODY GROWS ===")
    mind = Mind(state_path=Path('/tmp/glm_snap_test.json'))
    before = mind.state.stats()['n_nodes']
    for w in ['red', 'blue', 'hot', 'cold', 'big', 'small']:
        mind.state.add_node(w, encode(w), domain='language')
    after = mind.state.stats()['n_nodes']
    assert after > before
    print(f"  Body grew: {before} → {after} nodes")
    print()


def main():
    print("=" * 60)
    print("GLM Clean — Core Validation (snap-based)")
    print("=" * 60)
    print()

    test_encode()
    test_snap()
    test_measure()
    test_cycle()
    test_tct_method()
    test_body_grows()

    print("=" * 60)
    print("ALL TESTS PASSED — the snap is the base operation.")
    print("=" * 60)
    print()
    print("The system:")
    print("  - 6 files (body, data_object, snap, measure, body_state, mind)")
    print("  - ONE encoder (encode())")
    print("  - ONE snap (the base operation — weight ≤ 4, full covering radius)")
    print("  - ONE measure (TAX + NRCI + 5 shells)")
    print("  - ONE state (body_state.json)")
    print("  - ONE mind (perceive=snap → imagine → propose → commit → learn)")
    print()
    print("The snap IS the base operation. Information = (before, after, tax).")


if __name__ == "__main__":
    main()
