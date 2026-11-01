"""Tests for the domain wheels (Phase 157, ``studies/DOMAIN_WHEELS_STUDY.md``):
:mod:`glm_universal.engineering.domains` and
:mod:`glm_universal.engineering.domains_study`.

Fast: the split system over the fifteen wheels, the *across domains* frame
on the questions §7.1 names, the comparison of relations, the demand census
and the battery on stand-in inputs, a census over five names, and the
report's shape.  The census of the union (tens of minutes) is not taken and
nothing is written.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_domains.py (named in DOMAIN_WHEELS_STUDY.md §6) was lost in the
October 2026 reorganisation; rebuilt from studies/DOMAIN_WHEELS_STUDY.md
(§§2, 5, 7) and the reconstructed modules.*
"""
from __future__ import annotations

import unittest

from glm_universal.engineering import domains as dmn
from glm_universal.engineering import domains_study as dms
from glm_universal.wheels import wheel_by_id


def ask(text):
    t, ins, where = dmn.read_question(text)
    assert where is None
    return dmn.derive_domains(t, ins)


class TestSplitSystem(unittest.TestCase):

    def test_union_table(self):
        table = dmn.union_junctions()
        self.assertEqual(len(table), 15)
        self.assertEqual(table[("W9", "W13")], ("frequency",))   # Phase 158's B

    def test_names_split_except_across_a_junction(self):
        s = dmn.split_system()
        # the non-identity W13/W14 keeps two angular frequencies
        self.assertEqual(dmn.copies_of("angular_frequency", s),
                         ("angular_frequency@W13", "angular_frequency@W14"))
        # W9/W13 joins frequency only, so the angle stays split
        self.assertEqual(dmn.copies_of("angle", s), ("angle@W13", "angle@W9"))
        self.assertEqual(len(dmn.copies_of("energy", s)), 6)


class TestFrame(unittest.TestCase):

    def test_read_question(self):
        self.assertEqual(
            dmn.read_question("Derive the energy from power, time and charge "
                              "across domains?"),
            ("energy", ("power", "time", "charge"), None))
        self.assertEqual(
            dmn.read_question("derive energy from power and time across "
                              "domains where the energy is delivered over a time"),
            ("energy", ("power", "time"), "the energy is delivered over a time"))
        self.assertIsNone(dmn.read_question("what is the energy"))

    def test_aliases_are_read_and_said(self):
        a = ask("derive speed from distance and time across domains")
        self.assertTrue(a.answered)
        self.assertEqual(a.equation, "velocity = length / time")
        self.assertEqual(len(a.aliases), 2)
        self.assertIn("read speed as velocity", a.text())

    def test_swept_volume_across_three_wheels(self):
        a = ask("derive volume flow rate from volume and time across domains")
        self.assertEqual(a.equation, "volume_flow_rate = volume / time")
        self.assertEqual(a.wheels, ("W6", "W11", "W12"))

    def test_lc_angular_frequency(self):
        a = ask("derive angular frequency from inductance and capacitance "
                "across domains")
        self.assertTrue(dmn.same_relation(
            a.equation, "inductance * capacitance * angular_frequency^2 = 1"))

    def test_which_energy_is_refused_as_ambiguous(self):
        # d16 of §7.1
        a = ask("derive energy from power and time across domains")
        self.assertFalse(a.answered)
        self.assertEqual(a.reason, "ambiguous: the licensed union gives "
                         "energy = power * time (W15); energy = 1/2 * power * "
                         "time (W1+W3+W15)")

    def test_unknown_word_refused(self):
        a = ask("derive frobnication from mass and volume across domains")
        self.assertEqual(a.reason, "no declared wheel names frobnication")

    def test_oscillator_conflation(self):
        # oscillator_naive / oscillator_refused_split of DomainWheels.lean
        w = [wheel_by_id("W13"), wheel_by_id("W14")]
        naive = dmn.derive_relations("spring_constant",
                                     ("mass", "inductance", "capacitance"),
                                     dmn.split_system(split=False, wheels=w))
        self.assertEqual(naive.formula, "mass / inductance / capacitance")
        a = dmn.derive_domains("spring_constant",
                               ("mass", "inductance", "capacitance"), wheels=w)
        self.assertFalse(a.answered)
        self.assertEqual(a.naive, "mass / inductance / capacitance")
        self.assertIn("W13/W14", a.reason)

    def test_ten_wheel_answers_kept(self):
        a = ask("derive momentum from mass and velocity across domains")
        self.assertEqual(a.equation, "momentum = mass * velocity")

    def test_frame_surface(self):
        from glm_universal.engineering.speak import Refusal
        got = dmn.frame_domains("derive density from mass and volume across "
                                "domains")
        self.assertEqual(got.frame, "domains")
        self.assertEqual(got.values["formula"], "mass / volume")
        self.assertIsNone(dmn.frame_domains("derive density from mass"))
        with self.assertRaises(Refusal):
            dmn.frame_domains("derive frobnication from mass across domains")


class TestComparison(unittest.TestCase):

    def test_same_relation_positive_multiple(self):
        self.assertTrue(dmn.same_relation("x = y^(1/2)", "x^2 = y"))
        self.assertFalse(dmn.same_relation("y = x", "x = y"))
        self.assertTrue(dmn.same_relation_any("y = x", "x = y"))
        self.assertFalse(dmn.same_relation_any("x = y", "x = 2 * y"))


class TestCensuses(unittest.TestCase):

    def test_demand_census_longest_name_first(self):
        got = dmn.demand_census(
            ["the density of water is high", "a molar mass value here",
             "time and length of the run", "short"],
            ["density", "mass", "molar_mass", "time", "length", "velocity"])
        self.assertEqual(got["strings"], 4)
        # "molar mass" is taken before "mass" (the span is removed)
        self.assertEqual(got["lacking"], [("density", 1), ("length", 1),
                                          ("molar_mass", 1), ("time", 1)])

    def test_axioms(self):
        si7 = dmn.axiom_consistency("si7")
        self.assertEqual((si7["axioms"], si7["consistent"]), (12, 12))
        # at EXT10 the angle is an axis: three axioms carry a residual
        self.assertEqual(dmn.axiom_consistency("ext10")["consistent"], 9)

    def test_battery_on_stand_in_cases(self):
        cases = [("t1", "derive density from mass and volume across domains",
                  "density = mass / volume"),
                 ("t2", "derive frobnication from mass and volume across "
                        "domains", None),
                 ("t3", "derive momentum from mass and velocity across domains",
                  "momentum = mass / velocity"),
                 ("t4", "what is a domain", "x = y")]
        got = dmn.battery(cases)
        t = got["tally"]
        self.assertEqual((t["correct"], t["correct_refusals"], t["wrong"],
                          t["unread"]), (1, 1, 1, 1))

    def test_battery_needs_its_file(self):
        if dmn._domain_cases() is None:
            got = dmn.battery()
            self.assertFalse(got["available"])
            self.assertIn("domain_cases.py", got["reason"])

    def test_small_census(self):
        cen = dmn.census(names=["volume_flow_rate", "volume", "time", "area",
                                "length"],
                         labels=["volume_flow_rate = volume / time"])
        self.assertEqual(cen["questions"], 5 * 6)
        self.assertEqual(cen["in_wheel"], 3)
        rows = {(r["t"], r["formula"]) for r in cen["rows"]}
        self.assertEqual(rows, {("volume_flow_rate", "volume / time"),
                                ("volume", "volume_flow_rate * time"),
                                ("time", "volume / volume_flow_rate")})
        # a rearrangement with the other side as target is a negative
        # multiple: right only under the post-hoc reading (§7.3)
        self.assertEqual(cen["gained_right"], 2)
        self.assertEqual(cen["post_hoc"]["right"], 3)
        from glm_universal.engineering import domains_reread as drr
        rr = drr.reread(cen, labels=["volume_flow_rate = volume / time"])
        self.assertEqual((rr["one_wheel"], rr["reread_gained"], rr["right"]),
                         (0, 3, 3))


class TestReport(unittest.TestCase):

    def test_report(self):
        r = dmn.domains_report(census=True)
        self.assertEqual([w["id"] for w in r["wheels"]],
                         ["W11", "W12", "W13", "W14", "W15"])
        self.assertEqual(len(r["junctions"]), 10)
        self.assertIn("gained", r["census"])
        self.assertTrue(r["marks"]["D4"])
        self.assertFalse(r["marks"]["D2"])               # not measured
        if not dmn.census_state()["present"]:
            self.assertFalse(r["census"]["taken"])
            self.assertFalse(r["marks"]["D3"])
        if not r["battery"]["available"]:
            self.assertFalse(r["marks"]["D1"])

    def test_lean_file(self):
        c = dmn.lean_check(dmn.LEAN_FILE, dmn.LEAN_THEOREMS)
        if c["present"]:
            self.assertEqual((c["theorems"], c["sorry"]), (3, 0))

    def test_study_report(self):
        r = dms.study_report()
        self.assertIn("census_state", r)
        self.assertEqual(r["taken"], 5)


if __name__ == "__main__":
    unittest.main()
