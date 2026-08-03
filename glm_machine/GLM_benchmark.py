#!/usr/bin/env python3
"""
GLM BENCHMARK SUITE
====================
Proper testing against multiple dimensions:
1. Definition quality — Does it define concepts correctly?
2. Relation quality — Does it find real relationships?
3. Math accuracy — Does it compute correctly?
4. Coherence — Does the response flow logically?
5. Length — Is it adequately detailed?
6. Learning — Does it improve from text?
7. Context — Does it maintain multi-turn coherence?
"""

import time
import re
from typing import List, Dict, Tuple, Any


class GLMBenchmark:
    """Benchmark suite for the GLM system."""

    def __init__(self, runtime):
        self.rt = runtime
        self.results = []

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark suite."""
        results = {
            "definition_quality": self.benchmark_definitions(),
            "relation_quality": self.benchmark_relations(),
            "math_accuracy": self.benchmark_math(),
            "coherence": self.benchmark_coherence(),
            "length": self.benchmark_length(),
            "learning": self.benchmark_learning(),
            "context": self.benchmark_context(),
            "response_time": self.benchmark_speed(),
        }

        # Overall score
        scores = [v.get("score", 0) for v in results.values() if isinstance(v, dict)]
        results["overall_score"] = sum(scores) / max(1, len(scores))

        return results

    def benchmark_definitions(self) -> Dict[str, Any]:
        """Test definition quality."""
        test_cases = [
            ("What is gravity?", ["gravity", "force", "spacetime", "curvature"]),
            ("What is entropy?", ["entropy", "disorder", "information", "measure"]),
            ("What is a quark?", ["quark", "particle", "fermion"]),
            ("What is the hamiltonian?", ["hamiltonian", "operator", "time", "evolution"]),
            ("What is a photon?", ["photon", "quantum", "electromagnetic", "massless"]),
            ("What is symmetry?", ["symmetry", "transformation", "invariant"]),
            ("What is energy?", ["energy", "work", "capacity"]),
            ("What is momentum?", ["momentum", "mass", "velocity"]),
        ]

        correct = 0
        total = len(test_cases)
        details = []

        for query, expected_words in test_cases:
            result = self.rt.chat(query, fresh=True)
            result_lower = result.lower()
            found = [w for w in expected_words if w in result_lower]
            score = len(found) / len(expected_words)
            correct += score
            details.append({
                "query": query,
                "expected": expected_words,
                "found": found,
                "score": score,
                "words": len(result.split()),
            })

        return {
            "score": correct / total,
            "total": total,
            "details": details,
        }

    def benchmark_relations(self) -> Dict[str, Any]:
        """Test relation quality — does it find real relationships?"""
        test_cases = [
            ("How does entropy relate to dimension?", ["entropy", "dimension", "measures"]),
            ("What is the connection between energy and mass?", ["energy", "mass"]),
            ("How does gravity affect light?", ["gravity", "light"]),
            ("What is the relationship between symmetry and conservation?", ["symmetry", "conservation"]),
        ]

        correct = 0
        total = len(test_cases)
        details = []

        for query, expected_concepts in test_cases:
            result = self.rt.chat(query, fresh=True)
            result_lower = result.lower()
            found = [c for c in expected_concepts if c in result_lower]
            score = len(found) / len(expected_concepts)
            correct += score
            details.append({
                "query": query,
                "expected": expected_concepts,
                "found": found,
                "score": score,
            })

        return {
            "score": correct / total,
            "total": total,
            "details": details,
        }

    def benchmark_math(self) -> Dict[str, Any]:
        """Test math accuracy."""
        test_cases = [
            ("What is 7 + 5?", "12"),
            ("What is 100 mod 7?", "2"),
            ("What is 3!", "6"),
            ("What is sqrt(144)?", "12"),
            ("What is 2 + 3?", "5"),
            ("What is 10 * 5?", "50"),
        ]

        correct = 0
        total = len(test_cases)
        details = []

        for query, expected in test_cases:
            result = self.rt.chat(query, fresh=True)
            # Check if the answer appears in the result
            has_answer = expected in result or f"= {expected}" in result or f"gives us {expected}" in result
            if has_answer:
                correct += 1
            details.append({
                "query": query,
                "expected": expected,
                "found": has_answer,
                "result": result[:100],
            })

        return {
            "score": correct / total,
            "total": total,
            "correct": correct,
            "details": details,
        }

    def benchmark_coherence(self) -> Dict[str, Any]:
        """Test response coherence — do responses flow logically?"""
        queries = [
            "What is the hamiltonian?",
            "What is gravity?",
            "What is entropy?",
        ]

        total_score = 0
        details = []

        for query in queries:
            result = self.rt.chat(query, fresh=True)
            paragraphs = [p.strip() for p in result.split('\n\n') if p.strip()]
            sentences = [s.strip() for s in re.split(r'[.!?]+', result) if s.strip()]

            # Coherence metrics
            has_connectives = any(
                w in result.lower()
                for w in ['however', 'moreover', 'furthermore', 'therefore',
                          'consequently', 'thus', 'additionally', 'meanwhile',
                          'notably', 'importantly', 'what makes', 'the deeper',
                          'the implications', 'looking at', 'from the']
            )

            # Topic consistency — same topic words across paragraphs
            if len(paragraphs) >= 2:
                first_words = set(w.lower() for w in paragraphs[0].split() if len(w) > 4)
                consistency = []
                for p in paragraphs[1:]:
                    p_words = set(w.lower() for w in p.split() if len(w) > 4)
                    if first_words and p_words:
                        overlap = len(first_words & p_words) / min(len(first_words), len(p_words))
                        consistency.append(overlap)
                avg_consistency = sum(consistency) / max(1, len(consistency))
            else:
                avg_consistency = 0.5

            # Sentence length variety
            sent_lengths = [len(s.split()) for s in sentences]
            if sent_lengths:
                avg_len = sum(sent_lengths) / len(sent_lengths)
                length_variety = max(0, 1.0 - abs(avg_len - 15) / 15)
            else:
                length_variety = 0.0

            score = (
                (0.3 if has_connectives else 0.0) +
                avg_consistency * 0.4 +
                length_variety * 0.3
            )
            total_score += score
            details.append({
                "query": query,
                "paragraphs": len(paragraphs),
                "sentences": len(sentences),
                "has_connectives": has_connectives,
                "consistency": avg_consistency,
                "length_variety": length_variety,
                "score": score,
            })

        return {
            "score": total_score / len(queries),
            "total": len(queries),
            "details": details,
        }

    def benchmark_length(self) -> Dict[str, Any]:
        """Test response length — are responses adequately detailed?"""
        queries = [
            "What is gravity?",
            "What is a quark?",
            "What is entropy?",
            "What is the hamiltonian?",
        ]

        total_words = 0
        details = []

        for query in queries:
            result = self.rt.chat(query, fresh=True)
            words = len(result.split())
            total_words += words
            # Score: 100+ words = 1.0, 50 words = 0.5, etc.
            score = min(1.0, words / 100)
            details.append({"query": query, "words": words, "score": score})

        avg_words = total_words / len(queries)
        return {
            "score": min(1.0, avg_words / 100),
            "avg_words": avg_words,
            "total": len(queries),
            "details": details,
        }

    def benchmark_learning(self) -> Dict[str, Any]:
        """Test learning — does it improve from text?"""
        # Before learning
        before_result = self.rt.chat("What is mitosis?", fresh=True)
        before_words = len(before_result.split())
        before_has_def = "is a" in before_result.lower() or "is the" in before_result.lower()

        # Learn
        text = "Mitosis is the process of cell division where one cell divides into two identical daughter cells. The chromosomes are duplicated and separated into two nuclei. The cell then divides its cytoplasm to form two new cells."
        stats = self.rt.learn(text)

        # After learning
        after_result = self.rt.chat("What is mitosis?", fresh=True)
        after_words = len(after_result.split())
        after_has_def = "is a" in after_result.lower() or "is the" in after_result.lower() or "mitosis" in after_result.lower()

        improvement = (
            (1 if after_words > before_words else 0) +
            (1 if after_has_def and not before_has_def else 0) +
            (1 if stats.get("definitions_learned", 0) > 0 else 0)
        ) / 3

        return {
            "score": improvement,
            "before_words": before_words,
            "after_words": after_words,
            "before_has_def": before_has_def,
            "after_has_def": after_has_def,
            "learning_stats": stats,
        }

    def benchmark_context(self) -> Dict[str, Any]:
        """Test multi-turn context maintenance."""
        # First turn
        r1 = self.rt.chat("What is the hamiltonian?", fresh=True)

        # Second turn — uses "it" (should resolve to hamiltonian)
        r2 = self.rt.chat("How does it relate to symmetry?")

        # Check if "it" was resolved
        r2_lower = r2.lower()
        resolved = "hamiltonian" in r2_lower

        # Third turn — topic shift
        r3 = self.rt.chat("What about energy?")
        r3_lower = r3.lower()
        topic_shifted = "energy" in r3_lower

        score = (1 if resolved else 0) * 0.5 + (1 if topic_shifted else 0) * 0.5

        return {
            "score": score,
            "anaphora_resolved": resolved,
            "topic_shifted": topic_shifted,
            "turn1_words": len(r1.split()),
            "turn2_words": len(r2.split()),
            "turn3_words": len(r3.split()),
        }

    def benchmark_speed(self) -> Dict[str, Any]:
        """Test response time."""
        queries = [
            "What is gravity?",
            "What is a quark?",
            "What is 7 + 5?",
        ]

        times = []
        for q in queries:
            t0 = time.time()
            self.rt.chat(q, fresh=True)
            times.append(time.time() - t0)

        avg_time = sum(times) / len(times)
        return {
            "score": max(0, 1.0 - avg_time),  # 1s = 0 score, 0s = 1 score
            "avg_time": avg_time,
            "times": times,
        }

    def print_report(self, results: Dict[str, Any]):
        """Print a formatted benchmark report."""
        print("=" * 70)
        print("GLM BENCHMARK REPORT")
        print("=" * 70)

        for category, data in results.items():
            if category == "overall_score":
                continue
            if isinstance(data, dict) and "score" in data:
                score = data["score"]
                bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
                print(f"\n{category:25s} [{bar}] {score:.2f}")
                if "details" in data:
                    for d in data["details"][:3]:
                        if isinstance(d, dict):
                            q = d.get("query", "")
                            s = d.get("score", 0)
                            print(f"  {q:50s} → {s:.2f}")

        print(f"\n{'='*70}")
        overall = results.get("overall_score", 0)
        bar = "█" * int(overall * 20) + "░" * (20 - int(overall * 20))
        print(f"OVERALL SCORE: [{bar}] {overall:.2f}")
        print(f"{'='*70}")


if __name__ == "__main__":
    print("=== GLM Benchmark Suite ===")
