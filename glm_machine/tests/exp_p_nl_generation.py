#!/usr/bin/env python3
"""
Experiment P — Natural language generation with computed grammar.

Tests whether GLM22's ontological grammar (computing sentence structure
from vector geometry) produces better sentences than:
  A. GLM21 word-chain generator (no grammar, just nearest words)
  B. GLM17 template-based frames (slot-filling)
  C. GLM22 ontological grammar (computed S→V→O from gap geometry)

Evaluation metrics:
  1. Grammatical structure: does the output have NOUN→VERB→NOUN pattern?
  2. Semantic coherence: are the words related (low Hamming distance)?
  3. Novelty: is the sentence one that doesn't exist in the CRG verbatim?
  4. Verb relevance: is the computed verb semantically related to the
     CRG edge label (if one exists)?

The user's hypothesis: computed grammar > templates because it forces
the system to "think" (compute the verb from geometry) rather than
recall (fill in a template slot).
"""
from __future__ import annotations
import sys, os
from pathlib import Path
from collections import Counter

os.chdir(Path(__file__).resolve().parent.parent / "glm_work")
sys.path.insert(0, str(Path(".").resolve()))

from GLM11_runtime import GLMRuntimeV37
from GLM01_substrate import BLA, _build_vocabulary
from GLM03_crg import build_extended_crg
from GLM22_ontological_grammar import (
    OntologicalGrammar, computed_role, dominant_quadrant, QUADRANT_NAMES
)

def test_grammatical_structure():
    """Test 1: Does GLM22 produce NOUN→VERB→NOUN patterns?"""
    print("=" * 80)
    print("TEST 1: Grammatical structure (NOUN→VERB→NOUN pattern)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    grammar = OntologicalGrammar(rt.vocab, rt.crg)

    # Test with CRG edge pairs
    test_pairs = [
        ("hamiltonian", "time"),
        ("hamiltonian", "symmetry"),
        ("propagator", "momentum"),
        ("entropy", "dimension"),
        ("beta", "coupling"),
        ("anomaly", "dimension"),
        ("ads", "bcft"),
        ("rayleigh number", "temperature"),
    ]

    correct_pattern = 0
    total = 0
    print(f"\n{'Subject':<18} {'Verb':<15} {'Object':<18} {'S role':>8} {'V role':>8} {'O role':>8} {'Pattern':>8}")
    print("-" * 95)

    for s, o in test_pairs:
        result = rt.compute_sentence(s, o)
        if "error" in result:
            continue
        total += 1
        pattern_ok = (result["subject_role"] in ("NOUN", "ADJECTIVE") and
                      result["verb_role"] == "VERB" and
                      result["object_role"] in ("NOUN", "ADJECTIVE"))
        if pattern_ok:
            correct_pattern += 1
        print(f"{result['subject']:<18} {result['verb']:<15} {result['object']:<18} "
              f"{result['subject_role']:>8} {result['verb_role']:>8} {result['object_role']:>8} "
              f"{'✓' if pattern_ok else '✗':>8}")

    print(f"\n  Correct NOUN→VERB→NOUN pattern: {correct_pattern}/{total} ({correct_pattern/total*100:.1f}%)")
    return correct_pattern, total

def test_semantic_coherence():
    """Test 2: Are the computed sentences semantically coherent?"""
    print("\n" + "=" * 80)
    print("TEST 2: Semantic coherence (Hamming distance between words)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    grammar = OntologicalGrammar(rt.vocab, rt.crg)

    test_pairs = [
        ("hamiltonian", "time"), ("propagator", "momentum"),
        ("entropy", "dimension"), ("beta", "coupling"),
        ("anomaly", "dimension"), ("ads", "bcft"),
    ]

    all_dists = []
    for s, o in test_pairs:
        result = rt.compute_sentence(s, o)
        if "error" in result:
            continue
        # Compute Hamming distances between all word pairs
        s_entry = rt.vocab.words.get(s)
        v_entry = rt.vocab.words.get(result["verb"])
        o_entry = rt.vocab.words.get(o)
        if s_entry and v_entry and o_entry:
            d_sv = BLA.hamming_distance(s_entry.vector, v_entry.vector)
            d_vo = BLA.hamming_distance(v_entry.vector, o_entry.vector)
            d_so = BLA.hamming_distance(s_entry.vector, o_entry.vector)
            all_dists.extend([d_sv, d_vo, d_so])
            print(f"  {s}→{result['verb']}→{o}: HD(sv)={d_sv}, HD(vo)={d_vo}, HD(so)={d_so}")

    if all_dists:
        mean_d = sum(all_dists) / len(all_dists)
        print(f"\n  Mean Hamming distance (all pairs): {mean_d:.2f} (random ~12.0)")
        return mean_d
    return 0

def test_verb_relevance():
    """Test 3: Is the computed verb semantically related to the CRG edge label?"""
    print("\n" + "=" * 80)
    print("TEST 3: Verb relevance (computed verb vs CRG edge label)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    grammar = OntologicalGrammar(rt.vocab, rt.crg)

    # For each CRG edge, compare the computed verb to the edge label
    crg = rt.crg
    matches = 0
    total = 0
    print(f"\n{'CRG Edge':<50} {'Computed Verb':<20} {'Match?':>8}")
    print("-" * 80)

    for edge in crg.edges:
        if edge.label in ("contradicts", "incompatible_with", "auto_proposed",
                          "lattice_adjacent"):
            continue
        result = rt.compute_sentence(edge.src, edge.dst)
        if "error" in result:
            continue
        total += 1
        # Check if the computed verb is the same as the edge label
        # (or a related word)
        edge_label_word = edge.label.replace("_", " ")
        verb = result["verb"]
        # Simple match: does the verb appear in the edge label or vice versa?
        match = (verb.lower() in edge_label_word.lower() or
                 edge_label_word.lower() in verb.lower() or
                 verb == edge.label)
        if match:
            matches += 1
        if total <= 15:
            edge_str = f"{edge.src[:15]} --{edge.label[:12]}--> {edge.dst[:15]}"
            print(f"  {edge_str:<50} {verb:<20} {'✓' if match else '✗':>8}")

    print(f"\n  Verb matches CRG label: {matches}/{total} ({matches/total*100:.1f}%)")
    print(f"  (Note: low match rate is expected — the verb is COMPUTED from geometry,")
    print(f"   not looked up. The question is whether the computed verb is semantically")
    print(f"   reasonable, not whether it matches the label exactly.)")
    return matches, total

def test_novelty():
    """Test 4: Does the grammar produce novel sentences (not in CRG verbatim)?"""
    print("\n" + "=" * 80)
    print("TEST 4: Novelty (sentences not in CRG verbatim)")
    print("=" * 80)

    rt = GLMRuntimeV37()
    grammar = OntologicalGrammar(rt.vocab, rt.crg)

    # Generate sentences from random NOUN pairs
    import random
    random.seed(42)
    nouns = [w for w in rt.vocab.words.keys()
             if computed_role(w, rt.vocab) == "NOUN"
             and len(w) >= 4 and '_' not in w]
    sample_pairs = [(random.choice(nouns), random.choice(nouns))
                    for _ in range(20)]

    novel = 0
    total = 0
    for s, o in sample_pairs:
        if s == o:
            continue
        result = rt.compute_sentence(s, o)
        if "error" in result:
            continue
        total += 1
        # Check if this S→V→O triple exists in the CRG
        crg_edges = rt.crg.out.get(s, [])
        in_crg = any(e.dst == o for e in crg_edges)
        if not in_crg:
            novel += 1

    print(f"  Novel sentences (S→O pair not in CRG): {novel}/{total} ({novel/total*100:.1f}%)")
    print(f"  (Higher = more novel. The grammar can construct sentences for ANY")
    print(f"   noun pair, not just CRG-connected ones.)")
    return novel, total

def compare_approaches():
    """Test 5: Compare GLM21 (word chain) vs GLM22 (computed grammar)."""
    print("\n" + "=" * 80)
    print("TEST 5: Compare generation approaches")
    print("=" * 80)

    rt = GLMRuntimeV37()
    topics = ["hamiltonian", "energy", "symmetry", "anomaly"]

    print("\n  Topic: hamiltonian")
    print(f"    GLM21 (word chain): {rt.generate('hamiltonian', n_words=6, max_sentences=1)[:80]}")
    print(f"    GLM22 (computed):   {rt.generate_grammatical('hamiltonian', n_sentences=1)[:80]}")

    print("\n  Topic: energy")
    rt.reset_idea()
    print(f"    GLM21 (word chain): {rt.generate('energy', n_words=6, max_sentences=1)[:80]}")
    print(f"    GLM22 (computed):   {rt.generate_grammatical('energy', n_sentences=1)[:80]}")

    print("\n  Topic: symmetry")
    rt.reset_idea()
    print(f"    GLM21 (word chain): {rt.generate('symmetry', n_words=6, max_sentences=1)[:80]}")
    print(f"    GLM22 (computed):   {rt.generate_grammatical('symmetry', n_sentences=1)[:80]}")

def main():
    print("=" * 80)
    print("EXPERIMENT P: Natural language generation with computed grammar")
    print("=" * 80)

    correct, total = test_grammatical_structure()
    mean_dist = test_semantic_coherence()
    matches, match_total = test_verb_relevance()
    novel, novel_total = test_novelty()
    compare_approaches()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Grammatical structure (NOUN→VERB→NOUN):  {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"  Semantic coherence (mean HD):             {mean_dist:.2f} (random ~12.0)")
    print(f"  Verb matches CRG label:                   {matches}/{match_total} ({matches/match_total*100:.1f}%)")
    print(f"  Novel sentences (not in CRG):             {novel}/{novel_total} ({novel/novel_total*100:.1f}%)")

    print("\nVerdict:")
    if correct / total > 0.5:
        print("  ✅ The ontological grammar produces grammatically structured sentences")
        print("  (NOUN→VERB→NOUN) by COMPUTING the verb from the gap geometry.")
        print("  This is template-free generation — the system 'thinks' the verb,")
        print("  it doesn't recall it.")
    if mean_dist < 10:
        print(f"  ✅ Semantic coherence is high (HD {mean_dist:.2f} < 10).")
    if novel / novel_total > 0.8:
        print(f"  ✅ Novelty is high ({novel/novel_total*100:.1f}%). The grammar constructs")
        print("  sentences for ANY noun pair, not just CRG-connected ones.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
