#!/usr/bin/env python3
"""
Experiment O — Mathematical sentence generation (the bridge rung).

User's testing philosophy: math first (validation), then harder math
(complexity), then natural language (hard push).  This experiment is the
bridge between the math-validation rungs (Exp H, J, L, N) and the language-
generation rung (Exp P).

THE QUESTION: Can GLM GENERATE valid mathematical statements it has never
seen — not just recall them from the CRG or compute them via SymPy?

Tests:
  1. Generate a chain of math concepts connected by CRG edges
     (e.g. "hamiltonian generates time" → "time measures dimension" → ...)
  2. Check if the generated chain is mathematically coherent (each edge
     is a real CRG relation, not a random jump)
  3. Compare against random-walk baseline

If GLM can generate coherent mathematical concept chains, the generation
loop works for the validation domain.  Then Exp P tests natural language.
"""
from __future__ import annotations
import sys, os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from GLM11_runtime import GLMRuntimeV37
from GLM01_substrate import _build_vocabulary, BLA
from GLM03_crg import build_extended_crg

def test_math_chain_generation():
    """Test 1: Generate chains of math concepts connected by CRG edges."""
    print("=" * 80)
    print("TEST 1: Mathematical concept chain generation")
    print("=" * 80)

    rt = GLMRuntimeV37()
    crg = rt.crg
    vocab = rt.vocab

    # Pick seed concepts that have rich CRG connectivity
    seeds = ["hamiltonian", "symmetry", "anomaly", "propagator", "entropy",
             "renormalization", "beta", "coupling"]

    print("\nGenerating concept chains from seeds:")
    chains = []
    for seed in seeds:
        if seed not in vocab.words:
            continue
        # Generate a chain: seed → CRG neighbour → CRG neighbour → ...
        chain = [seed]
        current = seed
        for _ in range(5):  # 5 hops
            edges = crg.out.get(current, [])
            # Filter to "meaningful" edges (not contradictions)
            valid = [e for e in edges
                     if e.label not in ("contradicts", "incompatible_with",
                                        "lattice_adjacent", "auto_proposed")]
            if not valid:
                break
            # Pick the first valid edge (deterministic)
            next_word = valid[0].dst
            if next_word in vocab.words and next_word not in chain:
                chain.append(f"--{valid[0].label}-->")
                chain.append(next_word)
                current = next_word
            else:
                break
        chains.append(chain)
        chain_str = " ".join(chain)
        print(f"  {chain_str}")

    # Score: how many chains have >= 3 hops (6 elements: word, edge, word, edge, word, edge, word)
    long_chains = sum(1 for c in chains if len(c) >= 7)
    print(f"\n  Chains with >= 3 hops: {long_chains}/{len(chains)}")

    return long_chains, len(chains)

def test_generation_coherence():
    """Test 2: Is the generated text coherent (low Hamming distance between
    consecutive words, indicating semantic closeness)?"""
    print("\n" + "=" * 80)
    print("TEST 2: Generation coherence (Hamming distance between consecutive words)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    gen_text = rt.generate("hamiltonian", n_words=10, max_sentences=2)
    print(f"\n  Generated: {gen_text}")

    words = gen_text.replace(".", "").split()
    if len(words) < 2:
        print("  (Too few words to evaluate)")
        return 0, 0

    # Compute Hamming distances between consecutive words
    dists = []
    for i in range(len(words) - 1):
        w1, w2 = words[i].lower(), words[i+1].lower()
        e1 = rt.vocab.words.get(w1)
        e2 = rt.vocab.words.get(w2)
        if e1 and e2 and e1.vector and e2.vector:
            d = BLA.hamming_distance(e1.vector, e2.vector)
            dists.append(d)

    if dists:
        mean_dist = sum(dists) / len(dists)
        print(f"  Mean Hamming distance between consecutive words: {mean_dist:.2f}")
        print(f"  (Lower = more coherent. Random pairs average ~12.0)")
        return mean_dist, len(dists)
    return 0, 0

def test_crg_coverage():
    """Test 3: What fraction of generated word transitions are real CRG edges?"""
    print("\n" + "=" * 80)
    print("TEST 3: CRG coverage (fraction of transitions that are real edges)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    crg = rt.crg

    # Generate from several seeds
    seeds = ["hamiltonian", "energy", "symmetry", "anomaly"]
    all_transitions = 0
    crg_transitions = 0

    for seed in seeds:
        text = rt.generate(seed, n_words=8, max_sentences=1)
        words = text.replace(".", "").split()
        for i in range(len(words) - 1):
            w1, w2 = words[i].lower(), words[i+1].lower()
            # Check if there's a CRG edge between w1 and w2
            edges = crg.out.get(w1, [])
            has_edge = any(e.dst == w2 for e in edges)
            all_transitions += 1
            if has_edge:
                crg_transitions += 1

    if all_transitions > 0:
        coverage = crg_transitions / all_transitions
        print(f"  CRG-covered transitions: {crg_transitions}/{all_transitions} ({coverage*100:.1f}%)")
        print(f"  (Higher = more grammatically structured. Random baseline: ~0.1%)")
        return coverage, all_transitions
    return 0, 0

def test_random_walk_baseline():
    """Test 4: Compare against random walk (no CRG constraint, no centroid)."""
    print("\n" + "=" * 80)
    print("TEST 4: Random walk baseline (no CRG, no centroid)")
    print("=" * 80)

    import random
    random.seed(42)
    rt = GLMRuntimeV37()
    vocab_words = list(rt.vocab.words.keys())

    # Generate 3 random walks
    for i in range(3):
        walk = random.sample(vocab_words, 8)
        print(f"  Random walk {i+1}: {' '.join(walk)}")

    # Compute CRG coverage for random walks
    crg = rt.crg
    crg_count = 0
    total = 0
    for _ in range(100):
        walk = random.sample(vocab_words, 8)
        for j in range(len(walk) - 1):
            edges = crg.out.get(walk[j], [])
            if any(e.dst == walk[j+1] for e in edges):
                crg_count += 1
            total += 1
    baseline = crg_count / total if total > 0 else 0
    print(f"\n  Random walk CRG coverage: {crg_count}/{total} ({baseline*100:.2f}%)")
    return baseline

def main():
    print("=" * 80)
    print("EXPERIMENT O: Mathematical sentence generation (the bridge rung)")
    print("=" * 80)

    long_chains, total_chains = test_math_chain_generation()
    mean_dist, n_pairs = test_generation_coherence()
    coverage, n_trans = test_crg_coverage()
    baseline = test_random_walk_baseline()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  CRG concept chains (>=3 hops):  {long_chains}/{total_chains}")
    print(f"  Generation coherence (mean HD): {mean_dist:.2f} (random ~12.0)")
    print(f"  CRG coverage (generated):       {coverage*100:.1f}%")
    print(f"  CRG coverage (random walk):     {baseline*100:.2f}%")
    print(f"  Improvement over random:        {coverage/max(baseline, 0.001):.1f}x")

    print("\nVerdict:")
    if coverage > baseline * 10:
        print("  ✅ Generation is significantly more structured than random walk.")
        print("  The CRG transition grammar is working — generated sequences")
        print("  follow real concept relations, not random jumps.")
    elif coverage > baseline * 2:
        print("  ⚠️ Generation is somewhat structured, but CRG coverage is low.")
    else:
        print("  ❌ Generation is not significantly better than random walk.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
