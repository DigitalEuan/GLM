"""Executable cross-checks of the kit against the facts proved in the Lean library GLMKit.

Run:  python3 -m unittest discover -s tests -v      (from GLM_Pipeline_Kit/python)
"""
import random
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from glm_kit import analogy, fields, golay, lattices, leech, pipeline, tasks  # noqa: E402

RNG = random.Random(2026)


class TestGolay(unittest.TestCase):          # GLMKit/Golay.lean
    def test_size_and_enumerator(self):
        self.assertEqual(len(golay.codeword_set()), 4096)
        self.assertEqual(golay.weight_enumerator(), {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})

    def test_all_ones_and_syndrome(self):
        self.assertTrue(golay.is_codeword(golay.ALL_ONES))
        self.assertTrue(all(golay.syndrome(c) == 0 for c in golay.codewords()))
        self.assertEqual(sum(1 for w in (RNG.getrandbits(24) for _ in range(2000))
                             if golay.is_codeword(w) != (w in golay.codeword_set())), 0)

    def test_decoder(self):
        self.assertEqual(len(golay.leader_table()), 4096)
        for _ in range(300):
            c = RNG.choice(golay.codewords())
            e = 0
            for p in RNG.sample(range(24), RNG.randint(0, 3)):
                e |= 1 << p
            self.assertEqual(golay.decode(c ^ e), (c, e))

    def test_steiner_sample(self):
        octs = golay.octads()
        self.assertEqual(len(octs), 759)
        for _ in range(300):
            s = 0
            for p in RNG.sample(range(24), 5):
                s |= 1 << p
            self.assertEqual(sum(1 for o in octs if o & s == s), 1)


class TestLeech(unittest.TestCase):          # GLMKit/Leech.lean
    def test_minimal_vectors(self):
        self.assertTrue(leech.in_leech(leech.GLUE24))
        self.assertTrue(leech.in_leech((4, 4) + (0,) * 22))
        o = golay.octads()[0]
        self.assertTrue(leech.in_leech(tuple(2 * b for b in leech.word_to_bits(o))))
        self.assertFalse(leech.in_leech((4,) + (0,) * 23))

    def test_parity_wall_and_fix(self):
        for _ in range(3000):
            w = RNG.getrandbits(24)
            even = golay.popcount(w) % 2 == 0
            self.assertEqual(leech.in_leech(leech.embed4(w)), even)
            self.assertEqual(leech.in_leech(leech.embed4_glue(w)), even)
            self.assertTrue(leech.in_leech(leech.embed8(w)))
            self.assertEqual(leech.hits_parity_wall(w), not even)

    def test_junction_label_is_exact_class(self):
        for _ in range(3000):
            a = RNG.getrandbits(24)
            b = a ^ RNG.choice(golay.codewords()) if RNG.random() < 0.5 else RNG.getrandbits(24)
            same = leech.same_class(leech.embed4(a), leech.embed4(b))
            self.assertEqual(same, leech.junction_label(a) == leech.junction_label(b))
            if same:
                self.assertEqual(golay.popcount(a) % 2, golay.popcount(b) % 2)


class TestLattices(unittest.TestCase):       # GLMKit/Lattices.lean, GLMKit/Pless.lean
    def test_pless(self):
        S = lattices.pless_S()
        SSt = [[sum(S[i][k] * S[j][k] for k in range(24)) % 3 for j in range(24)] for i in range(24)]
        self.assertTrue(all(SSt[i][j] == (2 if i == j else 0) for i in range(24) for j in range(24)))
        self.assertTrue(all((S[i][j] + S[j][i]) % 3 == 0 for i in range(24) for j in range(24)))
        G = lattices.pless_generator()
        self.assertTrue(all(sum(G[i][k] * G[j][k] for k in range(48)) % 3 == 0
                            for i in range(24) for j in range(24)))

    def test_trivial_embeddings_and_noop_snap(self):
        for _ in range(200):
            w = RNG.getrandbits(24)
            x = []
            for b in leech.word_to_bits(w):
                x += [3 * b, 0]
            self.assertTrue(lattices.in_lambda48(x))
            perm = list(range(48)); RNG.shuffle(perm)
            self.assertTrue(lattices.in_lambda48([2 * x[p] for p in perm]))  # "spin" artifact
        G = lattices.pless_generator()
        def rnd_point():
            coeffs = [RNG.randrange(3) for _ in range(24)]
            c = [sum(coeffs[i] * G[i][j] for i in range(24)) % 3 for j in range(48)]
            return [v + 3 * RNG.randint(-2, 2) for v in c]
        for _ in range(50):
            A, B, C = rnd_point(), rnd_point(), rnd_point()
            D = [c + b - a for a, b, c in zip(A, B, C)]
            self.assertTrue(lattices.in_lambda48(D))      # snap is a no-op on D*


class TestFields(unittest.TestCase):         # GLMKit/Fields.lean
    def test_table(self):
        t = {r["field"]: r for r in fields.table()}
        self.assertEqual(t["F_2"]["spin_order"], 0)
        self.assertEqual(t["F_3"]["spin_order"], 2)
        self.assertEqual(t["F_4"]["spin_order"], 3)
        self.assertEqual(t["F_5"]["spin_order"], 4)
        self.assertEqual(t["F_7"]["spin_order"], 3)
        self.assertEqual(t["F_7"]["max_unit_order"], 6)
        self.assertEqual(t["F_8"]["spin_order"], 7)
        self.assertEqual(t["F_9"]["spin_order"], 4)       # alpha^2 = -1 has order 4 ...
        self.assertEqual(t["F_9"]["max_unit_order"], 8)   # ... the full group C_8 needs another generator
        self.assertIn((2, 3), fields.zmod6_zero_divisors())


class TestAnalogyAndOperators(unittest.TestCase):   # GLMKit/Analogy.lean, Permutation.lean
    def test_xor_vs_threshold_on_toggle(self):
        for s in range(200):
            a, _, _ = tasks.sample("toggle", s)
            c, _, _ = tasks.sample("toggle", s + 1000)
            A, C = tasks.flatten(a), tasks.flatten(c)
            B = [1 - v for v in A]
            expect = [1 - v for v in C]
            self.assertEqual(analogy.parity_analogy(A, B, C), expect)
            self.assertEqual(analogy.threshold_analogy(A, B, C) == expect, A == C)
            wa, wb, wc = (leech.vec_to_mask(v) for v in (A, B, C))
            self.assertEqual(analogy.xor_analogy(wa, wb, wc), leech.vec_to_mask(expect))

    def test_permute_op_reflect(self):
        perm = analogy.reflect_v_perm(4, 6)
        for s in range(100):
            x, y, _ = tasks.sample("reflect_v", s)
            out = analogy.permute_op(tasks.flatten(x), perm)
            self.assertEqual(out, tasks.flatten(y))
            self.assertEqual(sum(out), sum(tasks.flatten(x)))

    def test_traces(self):
        for name in tasks.TASKS:
            for s in range(50):
                x, y, tr = tasks.sample(name, s)
                self.assertTrue(tasks.verify_trace(x, y, tr), (name, s))

    def test_solver(self):
        for s in range(30):
            demos = [tasks.sample("toggle", 10 * s + k)[:2] for k in range(3)]
            q, a, _ = tasks.sample("toggle", 10 * s + 9)
            pred, rule = pipeline.solve(demos, q)
            self.assertEqual((pred, rule), (a, "xor_displacement"))
        for name in ("reflect_v", "translate"):
            solved = 0
            for s in range(30):
                demos = [tasks.sample(name, 100 * s + k)[:2] for k in range(4)]
                q, a, _ = tasks.sample(name, 100 * s + 99)
                pred, rule = pipeline.solve(demos, q)
                if pred is not None:
                    self.assertIn("permutation:", rule)
                    self.assertEqual(pred, a)      # never a wrong answer
                    solved += 1
            self.assertGreaterEqual(solved, 25, name)


if __name__ == "__main__":
    unittest.main()
