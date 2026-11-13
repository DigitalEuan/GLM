"""``tests/test_leech_lean.py`` -- the leechlean engine adapter, against the
substrate, the codebook and the repository's own Lean tree.

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22; the item's own battery ``tests/test_leechlean_in_glm.py``
cross-checks the item's numpy engine against the same substrate facts).*

The engine is pure Python over the substrate's exact machinery; every check
here is exact (integers and fractions, no float ever).
"""
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal import constants as C
from glm_universal.reasoning import leech_lean as LL
from glm_universal.substrate import leech2


def _no_float(value) -> None:
    """The engine's figures never carry a float."""
    if isinstance(value, float):
        raise AssertionError(f"a float reached the figures: {value!r}")
    if isinstance(value, dict):
        for v in value.values():
            _no_float(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _no_float(v)


class TestCodebook(unittest.TestCase):
    """The item's codebook, as the port loads it."""

    def test_injective_and_on_lattice(self):
        cb = LL.codebook_state()
        self.assertEqual(len(cb), 39992)
        self.assertEqual(len(cb.cells), 39992)      # injective: no collisions
        # every address is a true Leech lattice point (the substrate's
        # predicate, not the item's)
        for key, p in list(cb.parts.items())[:400]:
            self.assertTrue(LL.is_lattice_point(p.address), key)

    def test_energy_law_anchors(self):
        cb = LL.codebook_state()
        # one bit of surprisal = four units of lattice energy: the commonest
        # part sits on the one-bit sphere, a rare import word far out
        self.assertEqual(cb.parts["ws: "].energy, 8)
        self.assertEqual(cb.parts["ws: "].count, 526563)
        self.assertEqual(cb.parts["ident:Mathlib"].energy, 76)
        self.assertEqual(cb.parts["ident:Mathlib"].count, 201)

    def test_granularity_counts(self):
        g = LL.granularity_counts()
        self.assertEqual(g, {"token": 29422, "bigram": 10421,
                             "frame": 63, "tactic": 86})

    def test_class_types_through_the_substrate(self):
        # kw:theorem's class is type 2 (a minimal-vector class, one of the
        # 98,280): the item's own machinery and the substrate's agree
        addr = LL.address_of_part("kw:theorem")
        self.assertEqual(LL.class_type_of(addr), 2)
        self.assertEqual(len(leech2.type2_classes()), 98280)


class TestCodec(unittest.TestCase):
    """A file is a tick stream of addresses, and back, byte-exactly."""

    def setUp(self):
        self.code = (C.REPOSITORY_ROOT / "src" / "lean" /
                     "RequestProject" / "GLM" / "Golay" / "Code.lean")

    def test_lexer_round_trip(self):
        text = self.code.read_text(encoding="utf-8", errors="replace")
        toks = LL.tokenize(text)
        self.assertEqual("".join(t.text for t in toks), text)

    def test_round_trip_and_report(self):
        rep = LL.file_report(self.code)
        self.assertTrue(rep.round_trip)
        self.assertEqual(rep.on_lattice, rep.ticks)
        self.assertGreater(rep.ticks, 500)
        self.assertGreaterEqual(rep.ctx + rep.part_known + rep.new_ticks,
                                rep.ticks)
        _no_float(rep.__dict__)

    def test_unknown_part_refused(self):
        with self.assertRaises(KeyError):
            LL.encode_text("theorem zzz_never_seen_xyz : True := by decide")

    def test_unknown_path_refused(self):
        with self.assertRaises(FileNotFoundError):
            LL.resolve_lean_path("No/Such/File.lean")


class TestMoves(unittest.TestCase):
    """The happening between addresses: d = B - A and its class law."""

    def test_move_report_of_a_file(self):
        code = (C.REPOSITORY_ROOT / "src" / "lean" / "RequestProject" /
                "GLM" / "Golay" / "Code.lean")
        _, addrs = LL.encode_text(
            code.read_text(encoding="utf-8", errors="replace"))
        rep = LL.move_report(addrs)
        self.assertTrue(rep.class_law)       # kappa(d1)(*)kappa(d2)=kappa(d1+d2)
        self.assertGreater(rep.moves, 500)
        self.assertGreater(rep.distinct, 50)
        self.assertGreater(rep.known_moves, 0)
        _no_float(rep.__dict__)

    def test_repertoire_matches_the_recorded_experiment(self):
        rep = LL.repertoire()
        self.assertEqual(len(rep), 80361)     # the recorded distinct moves
        self.assertEqual(sum(rep.values()), 1487183)

    def test_class_law_is_linear(self):
        # the substrate's class map is linear: classes compose by XOR
        d1 = (4, 4) + (0,) * 22
        d2 = (0, 0, 4, 4) + (0,) * 20
        self.assertEqual(LL.class_of(tuple(a + b for a, b in zip(d1, d2))),
                         LL.class_of(d1) ^ LL.class_of(d2))


class TestCorrection(unittest.TestCase):
    """The sieve and the class-assisted repair."""

    def setUp(self):
        code = (C.REPOSITORY_ROOT / "src" / "lean" / "RequestProject" /
                "GLM" / "Golay" / "Code.lean")
        _, addrs = LL.encode_text(
            code.read_text(encoding="utf-8", errors="replace"))
        self.addrs = addrs[:20]

    def test_clean_stream_zero_false_alarms(self):
        report = LL.sieve_report(self.addrs)
        self.assertEqual(report["clean"], len(self.addrs))

    def test_flip_caught_by_parity_and_repaired(self):
        corrupted = LL.corrupt_stream(self.addrs, "flip", 7, k=1)
        report = LL.sieve_report(corrupted)
        self.assertEqual(sum(v for k, v in report.items() if k != "clean"),
                         len(self.addrs))
        self.assertEqual(report["mod2"], len(self.addrs))   # parity breaks first
        repaired, stats = LL.repair_stream(corrupted)
        self.assertEqual(sum(1 for r in repaired if r is not None),
                         len(self.addrs))
        cb = LL.codebook_state()
        true = [cb.cells[a] for a in self.addrs]
        self.assertEqual(repaired, true)

    def test_slip_on_lattice_caught_by_the_class_syndrome(self):
        corrupted = LL.corrupt_stream(self.addrs, "slip", 7)
        report = LL.sieve_report(corrupted)
        self.assertEqual(report["clean"], len(self.addrs))  # invisible to sieve
        changed = sum(1 for a, x in zip(self.addrs, corrupted)
                      if LL.class_of(x) != LL.class_of(a))
        self.assertEqual(changed, len(self.addrs))          # syndrome sees all
        repaired, _ = LL.repair_stream(corrupted)
        cb = LL.codebook_state()
        true = [cb.cells[a] for a in self.addrs]
        self.assertEqual(repaired, true)


class TestStitching(unittest.TestCase):
    """Authoring against the library: new parts addressed on the fly."""

    def test_stitch_new_part(self):
        res = LL.stitch_text(
            "theorem glm_fresh_9c4d : True := by decide\n")
        self.assertTrue(res["byte_exact"])
        self.assertEqual(res["n_new"], 1)
        key, addr, e, j = res["new_parts"][0]
        self.assertEqual(key, "ident:glm_fresh_9c4d")
        self.assertTrue(LL.is_lattice_point(addr))       # a true lattice point
        cb = LL.codebook_state()
        self.assertNotIn(addr, {p.address for p in cb.parts.values()
                                if p.key != key})        # not an old address
        # the integer-surprisal energy law: E = least e with 2^e >= 1487625
        self.assertEqual(e, 21)
        self.assertGreaterEqual(LL.energy_of(addr), 4 * e)
        # and the second stitch of the same part is idempotent
        again = LL.stitch_text(
            "theorem glm_fresh_9c4d : True := by decide\n")
        self.assertEqual(again["n_new"], 0)

    def test_new_address_is_exact_rational(self):
        # the target of a new part is a rational ray point; the decoder is
        # the substrate's exact one -- no float anywhere in the choice
        addr, e, j = LL.address_new_part("ident:glm_fresh_probe_1")
        self.assertIsInstance(addr, tuple)
        for v in addr:
            self.assertIsInstance(v, int)


class TestLibrary(unittest.TestCase):
    """The library graph as the port reads it."""

    def test_totals_match_the_recorded_experiment(self):
        core = LL.library_state()
        self.assertEqual(len(core.part_files), 29422)
        self.assertEqual(len(core.edge_count), 80375)
        self.assertEqual(len(core.ctx_files), 55269)
        self.assertEqual(core.n_files, 442)
        self.assertEqual(core.n_tokens, 1487625)

    def test_continuations_of_theorem(self):
        cont = LL.continuations("kw:theorem")
        self.assertEqual(cont[0], ("ws: ", 6725))

    def test_universal_core(self):
        core = LL.universal_core(400)
        self.assertEqual(len(core), 18)
        self.assertIn("kw:theorem", core)
        self.assertIn("ws: ", core)


if __name__ == "__main__":
    unittest.main()
