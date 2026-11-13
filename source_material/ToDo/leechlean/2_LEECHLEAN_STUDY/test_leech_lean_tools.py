"""``tests/test_leech_lean_tools.py`` -- the ``tool leechlean`` surface
through the real toolbox dispatch.

*Created 11 November 2026 (the intake of ``source_material/ToDo/leechlean``,
directive D22).*
"""
import unittest

from glm_universal.runtime import toolbox as tb
from glm_universal.reasoning import leech_lean_tools as LT


def _no_float(value) -> None:
    if isinstance(value, float):
        raise AssertionError(f"a float reached the figures: {value!r}")
    if isinstance(value, dict):
        for v in value.values():
            _no_float(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _no_float(v)


class TestDispatch(unittest.TestCase):
    """Every op through ``run_tool`` (the router's dispatch), with the
    refusals the study's controls hold."""

    @classmethod
    def setUpClass(cls):
        ok, text, fig = tb.run_tool("tool leechlean")
        assert ok, text          # the module must be installed for these tests

    def _tool(self, arg):
        ok, text, figures = tb.run_tool(f"tool leechlean {arg}".strip())
        _no_float(figures)
        return ok, text, figures

    def test_tool_is_registered(self):
        names = [t.name for t in tb.TOOLS]
        self.assertIn("leechlean", names)
        tool = [t for t in tb.TOOLS if t.name == "leechlean"][0]
        self.assertEqual(tool.module, "reasoning.leech_lean_tools")
        self.assertIn("IntakeChecks/LeechLeanGolay.lean", " ".join(tool.lean))
        self.assertIn("IntakeChecks/LeechLeanCodec.lean", " ".join(tool.lean))
        self.assertIn("studies/LEECHLEAN_STUDY.md", tool.study)

    def test_usage(self):
        ok, text, figures = self._tool("")
        self.assertTrue(ok)
        self.assertIn("address PART", text)

    def test_address(self):
        ok, text, fig = self._tool("address theorem")
        self.assertTrue(ok)
        self.assertIn("lattice energy |A|^2/8 = 40", text)
        self.assertIn("type 2", text)
        self.assertEqual(fig["status"], "ok")

    def test_address_refuses_unknown(self):
        ok, text, fig = self._tool("address zzz_not_a_part_qq")
        self.assertFalse(ok)
        self.assertEqual(fig["status"], "refused")

    def test_file(self):
        ok, text, fig = self._tool(
            "file RequestProject/GLM/Golay/Code.lean")
        self.assertTrue(ok)
        self.assertIn("byte-exact", text)
        self.assertEqual(fig["round_trip"], True)

    def test_file_refuses_unknown(self):
        ok, _t, fig = self._tool("file No/Such/File.lean")
        self.assertFalse(ok)
        self.assertEqual(fig["status"], "refused")

    def test_moves(self):
        ok, text, fig = self._tool(
            "moves RequestProject/GLM/Golay/Code.lean")
        self.assertTrue(ok)
        self.assertIn("kappa(d1)(*)kappa(d2) = kappa(d1+d2)", text)
        self.assertEqual(fig["class_law"], True)

    def test_continue(self):
        ok, text, fig = self._tool("continue theorem")
        self.assertTrue(ok)
        self.assertIn("'ws: '", text)
        self.assertIn("unverified graph proposals", text)
        self.assertEqual(fig["top_count"], 6725)

    def test_continue_refuses_unknown(self):
        ok, _t, _f = self._tool("continue zzz_not_a_part_qq")
        self.assertFalse(ok)

    def test_verify_clean(self):
        ok, text, fig = self._tool(
            "verify RequestProject/GLM/Golay/Code.lean")
        self.assertTrue(ok)
        self.assertIn("0 false alarms", text)
        self.assertEqual(fig["false_alarms"], 0)

    def test_verify_flip(self):
        ok, text, fig = self._tool(
            "verify RequestProject/GLM/Golay/Code.lean flip 1")
        self.assertTrue(ok)
        self.assertIn("flags 40 of 40", text)
        self.assertEqual(fig["detected"], 40)
        self.assertEqual(fig["repaired"], 40)

    def test_verify_slip(self):
        ok, text, fig = self._tool(
            "verify RequestProject/GLM/Golay/Code.lean slip")
        self.assertTrue(ok)
        self.assertIn("class syndrome flags 40 of 40", text)
        self.assertEqual(fig["class_changed"], 40)

    def test_attest(self):
        ok, text, fig = self._tool("attest theorem")
        self.assertTrue(ok)
        self.assertIn("syntactic attestation", text)
        self.assertGreater(fig["frames"], 0)

    def test_stitch(self):
        ok, text, fig = self._tool(
            "stitch theorem glm_fresh_9c4d : True := by decide")
        self.assertTrue(ok)
        self.assertIn("byte-exact", text)
        self.assertEqual(fig["n_new"], 1)

    def test_state(self):
        ok, text, fig = self._tool("state")
        self.assertTrue(ok)
        self.assertIn("39,992 parts", text)
        self.assertIn("one bit of surprisal is four units", text)
        self.assertEqual(fig["parts"], 39992)

    def test_prove_refused_everywhere(self):
        for arg in ("prove that one equals one",
                    "prove the Riemann hypothesis",
                    "prove 1 = 1"):
            ok, _t, fig = self._tool(arg)
            self.assertFalse(ok, arg)
            self.assertEqual(fig["status"], "refused")

    def test_unknown_op_refused(self):
        ok, _t, fig = self._tool("dance theorem")
        self.assertFalse(ok)
        self.assertEqual(fig["status"], "refused")

    def test_ahead_note_when_registered(self):
        # before the owner's build confirms the item, the register lists it
        # and every answer carries the note; after confirm-build it is gone
        note = LT.build_note()
        if note is None:
            self.assertNotIn("provisional", self._tool("state")[2])
        else:
            _ok, text, fig = self._tool("state")
            self.assertIn(str(note), text)
            self.assertIn("provisional", fig)

    def test_english_routes(self):
        # the phrases the router consults after every surface refuses
        phrases = [t for _p, t in tb.TOOL_PHRASES
                   if t.startswith("tool leechlean")]
        self.assertTrue(phrases)
        routed = tb.phrase_tool("what is the leechlean address of theorem")
        self.assertEqual(routed, "tool leechlean address theorem")


if __name__ == "__main__":
    unittest.main()
