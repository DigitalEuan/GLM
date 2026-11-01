"""Tests for contextual domain frames (Phase 170,
``studies/CONTEXT_FRAMES_STUDY.md``):
:mod:`glm_universal.engineering.context_frames` and
:mod:`glm_universal.engineering.context_frames_study`.

Fast: the six declared contexts, the four declared refusals, the probes of
X3, X4, X5 and X8 (seconds of exact linear algebra), the pin census on a
handful of names, and the report's shape.  The full pin census of X6 (a
quarter of an hour) is not taken and nothing is written.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_context_frames.py was lost in the October 2026 reorganisation;
rebuilt from studies/CONTEXT_FRAMES_STUDY.md (§§1, 4, 7) and the
reconstructed modules.*
"""
from __future__ import annotations

import unittest

from glm_universal.engineering import context_frames as cf
from glm_universal.engineering import context_frames_study as cfs
from glm_universal.engineering import domains as dmn


def ask(text):
    return cfs.ask(text)


class TestContexts(unittest.TestCase):

    def test_six_declared(self):
        self.assertEqual(set(cf.CONTEXTS), {
            "energy-delivered", "energy-stored-capacitor",
            "energy-stored-inductor", "oscillator-spring", "oscillator-lc",
            "rotating-drive"})
        self.assertEqual(cf.CONTEXTS["energy-delivered"].pin, ("energy", "W15"))
        self.assertEqual(cf.CONTEXTS["energy-stored-capacitor"].pin,
                         ("energy", "W3"))
        self.assertEqual(cf.CONTEXTS["oscillator-lc"].pin,
                         ("angular_frequency", "W14"))
        self.assertEqual(cf.CONTEXTS["rotating-drive"].join,
                         (("W9", "W13"), ("angle",)))

    def test_read_where(self):
        got = cf.read_where("The energy is delivered over a time.")
        self.assertEqual([c.key for c in got], ["energy-delivered"])
        two = cf.read_where("a rotating body drives the wave and the "
                            "oscillator is a mass on a spring")
        self.assertEqual([c.key for c in two],
                         ["rotating-drive", "oscillator-spring"])
        with self.assertRaises(cf.ContextRefusal):
            cf.read_where("the energy is warm")

    def test_join_is_for_the_question_only(self):
        before = dmn.union_junctions()
        pins, table = cf.frame_of([cf.CONTEXTS["rotating-drive"]],
                                  "angular_frequency", ("angular_velocity",))
        self.assertEqual(pins, {})
        self.assertEqual(table[("W9", "W13")], ("frequency", "angle"))
        self.assertEqual(dmn.union_junctions(), before)      # union untouched


class TestFrames(unittest.TestCase):

    def test_which_energy(self):
        d = ask("derive energy from power and time across domains where the "
                "energy is delivered over a time")
        self.assertEqual(d.equation, "energy = power * time")
        c = ask("derive energy from power and time across domains where the "
                "energy is stored in a capacitor")
        self.assertEqual(c.equation, "energy = 1/2 * power * time")
        self.assertIn("W3", c.wheels)
        i = ask("derive energy from power and time across domains where the "
                "energy is stored in an inductor")
        self.assertFalse(i.answered)
        self.assertIn("no derivation remains", i.reason)

    def test_source_energy_against_stored(self):
        self.assertEqual(
            ask("derive energy from charge and voltage across domains where "
                "the energy is delivered over a time").equation,
            "energy = charge * voltage")
        self.assertEqual(
            ask("derive energy from charge and voltage across domains where "
                "the energy is stored in a capacitor").equation,
            "energy = 1/2 * charge * voltage")

    def test_rotating_drive(self):
        a = ask("derive angular frequency from power and torque across domains "
                "where a rotating body drives the wave")
        self.assertEqual(a.equation, "angular_frequency = power / torque")
        self.assertFalse(ask("derive angular frequency from power and torque "
                             "across domains").answered)

    def test_declared_refusals(self):
        cases = {
            "derive energy from power and time across domains where the "
            "energy is warm": "is not declared",
            "derive density from mass and volume across domains where the "
            "energy is delivered over a time": "does not ask about",
            "derive energy from power and time across domains where the "
            "energy is delivered over a time and the energy is stored in a "
            "capacitor": "say different things",
            "derive spring constant from mass and angular frequency across "
            "domains where the oscillator is an lc circuit":
                "no derivation remains",
        }
        for q, words in cases.items():
            a = ask(q)
            self.assertFalse(a.answered, q)
            self.assertIn(words, a.reason, q)

    def test_frame_surface_reads_the_where_clause(self):
        got = dmn.frame_domains("derive power from energy and time across "
                                "domains where the energy is delivered over "
                                "a time")
        self.assertEqual(got.values["formula"], "energy / time")


class TestStudy(unittest.TestCase):

    def test_probes(self):
        written = {p["key"]: p["grade"] for p in cfs.probes(False)}
        self.assertEqual(written["x5b"], "wrong")      # X5 missed as written
        self.assertTrue(all(g in ("correct", "correct refusal")
                            for k, g in written.items() if k != "x5b"))
        amended = {p["key"]: p["grade"] for p in cfs.probes(True)}
        self.assertEqual(amended["x5b"], "correct")    # X5' met

    def test_pin_questions(self):
        self.assertEqual(len(cfs.pin_questions("energy")), 3243)
        self.assertEqual(len(cfs.pin_questions("a", ["a", "b", "c", "d"])),
                         3 + 3 * 2)

    def test_pin_census_on_a_few_names(self):
        names = ["energy", "power", "time", "charge", "voltage",
                 "angular_frequency"]
        c = cfs.pin_census(names=names)
        self.assertEqual(c["changed_count"], 0)        # a pin never changes
        resolved = {(r["t"], tuple(r["inputs"])) for r in c["resolved"]}
        self.assertIn(("energy", ("power", "time")), resolved)
        self.assertIn(("energy", ("charge", "voltage")), resolved)
        per_name = len(cfs.pin_questions("energy", names))
        self.assertEqual(per_name, 10 + 5 * 4)
        self.assertEqual(c["questions"], 3 * per_name + 2 * per_name)

    def test_marks_without_the_lost_evidence(self):
        got = cfs.compute(census=False)
        self.assertEqual(got["taken"], 9)
        for k in ("X3", "X4", "X8", "X5′"):
            self.assertTrue(got["marks"][k], k)
        self.assertFalse(got["marks"]["X5"])
        self.assertFalse(got["marks"]["X6"])           # not taken here
        if not got["lean"]["present"]:
            self.assertFalse(got["marks"]["X1"])

    def test_report(self):
        r = cfs.context_frames_report()
        if not r["available"]:
            self.assertIn("--write", r["reason"])
        else:
            self.assertIn("census", r)


if __name__ == "__main__":
    unittest.main()
