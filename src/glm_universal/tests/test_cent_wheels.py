"""The cent wheels (``glm_universal.wheels.cent_wheels``), pinned.

*Created 31 October 2026 (intake of ``source_material/ToDo/cent_compiler_v12``,
directive D22; ``studies/CENT_WHEELS_STUDY.md``).*

What is checked:

* the rational-power engine -- fractional powers read exactly, the integer
  engine of ``engineering/wheels.py`` reproduced wherever it reads (mark E1),
  certificates and separating functionals that really certify;
* the absorbed wheels -- every axiom balanced at SI7 on its table (and on all
  eight axes: no absorbed axiom carries an angle residual), every case's flag
  equal to span membership, every negative control refused, no hidden
  dimensionless relation in any span (S5), the corrections and drops recorded
  and applied, the fifteen registry wheels untouched;
* the supplied item (when present) -- the absorbed data is the supplied data
  except where ``CORRECTIONS`` / ``DROPPED`` say otherwise, and the supplied
  axioms that fail at SI7 are exactly the ten the Lean file states;
* ``Wheels/CentWheels.lean`` -- in the build tree, audited, dated, free of
  ``sorry`` / ``native_decide``; every vector, table, certificate and verdict
  it states re-checked in exact arithmetic against the Python
  (:func:`glm_universal.wheels.lean_cent_data.agreement`), a tampered copy
  rejected, and the file exactly the text the round's generator writes;
* the query surface :func:`glm_universal.wheels.answer_derivability`;
* the study's measurement (:mod:`glm_universal.wheels.cent_wheels_study`):
  the battery's composition and bars, and the marks §8 reports.
"""

from __future__ import annotations

import re
import unittest
from fractions import Fraction

from glm_universal import constants as C
from glm_universal import lean_check
from glm_universal.engineering import wheels as EW
from glm_universal.wheels import (
    ALL_WHEELS, CENT_LEAN, CENT_STUDY, CENT_WHEEL_IDS, DOMAIN_WHEELS, answer_derivability,
    cent_family,
)
from glm_universal.wheels import cent_wheels as CW
from glm_universal.wheels import cent_wheels_study as S
from glm_universal.wheels import lean_cent_data as L

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = S.cent_wheels_report(lean=True)
    return _REPORT


def _supplied():
    sup = S.supplied_wheels()
    return sup if sup else None


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------

class TestRationalPowerEngine(unittest.TestCase):

    def test_fractional_powers_are_read_exactly(self):
        v = CW.relation_vector_q("fracture_toughness = (2 * youngs_modulus * surface_energy / crack_length)^(1/2)")
        self.assertEqual(v["fracture_toughness"], 1)
        self.assertEqual(v["youngs_modulus"], Fraction(-1, 2))
        self.assertEqual(v["crack_length"], Fraction(1, 2))
        self.assertEqual(v["#2"], Fraction(-1, 2))
        for x in v.values():
            self.assertIsInstance(x, Fraction)

    def test_the_integer_engine_refuses_what_this_one_reads(self):
        with self.assertRaises(ValueError):
            EW.relation_vector("spin_diffusion_length = (diffusion_coefficient * time)^(1/2)")
        self.assertTrue(CW.is_derivable_q("time = spin_diffusion_length^2 / diffusion_coefficient",
                                          CW.cent_wheel("W29").axioms))

    def test_agrees_with_the_integer_engine_on_the_registry(self):
        for w in ALL_WHEELS:
            for text in list(w.axioms) + [c.equation for c in w.cases]:
                try:
                    iv = EW.relation_vector(text)
                except ValueError:
                    continue
                qv = CW.relation_vector_q(text)
                self.assertEqual({k: Fraction(x) for k, x in iv.items() if x},
                                 {k: x for k, x in qv.items() if x}, text)
            for c in w.cases:
                try:
                    want = EW.is_derivable(c.equation, w.axioms)
                except ValueError:
                    continue
                self.assertEqual(CW.is_derivable_q(c.equation, w.axioms), want, c.id)

    def test_mark_e1(self):
        e1 = report()["e1"]
        self.assertTrue(e1["met"], e1)
        self.assertEqual(e1["disagreements"], [])

    def test_certificates_certify(self):
        for w in CW.CENT_WHEELS:
            rels = [CW.relation_vector_q(a) for a in w.axioms]
            for c in w.cases:
                v = CW.relation_vector_q(c.equation)
                keys = CW.columns(*rels, v)
                x = CW.certificate(c.equation, w.axioms)
                if x is not None:
                    for k in keys:
                        self.assertEqual(sum((xi * r.get(k, 0) for xi, r in zip(x, rels)), Fraction(0)),
                                         v.get(k, 0), (c.id, k))
                else:
                    f = CW.separating_functional(c.equation, w.axioms)
                    self.assertIsNotNone(f, c.id)
                    for r in rels:
                        self.assertEqual(sum(f.get(k, 0) * r.get(k, 0) for k in keys), 0, c.id)
                    self.assertNotEqual(sum(f.get(k, 0) * v.get(k, 0) for k in keys), 0, c.id)

    def test_unreadable_is_an_error(self):
        with self.assertRaises(ValueError):
            CW.relation_vector_q("membrane_voltage = log(temperature)")


# ---------------------------------------------------------------------------
# The absorbed wheels
# ---------------------------------------------------------------------------

class TestAbsorbedWheels(unittest.TestCase):

    def test_the_family(self):
        self.assertEqual(tuple(w.id for w in cent_family()), CENT_WHEEL_IDS)
        self.assertEqual(tuple(w.id for w in CW.CENT_WHEELS), CENT_WHEEL_IDS)
        self.assertEqual(CENT_STUDY, "studies/CENT_WHEELS_STUDY.md")
        self.assertEqual(CENT_LEAN, ("Wheels/CentWheels.lean",))
        self.assertNotIn("W35", CENT_WHEEL_IDS)
        self.assertIn("W35", CW.NOT_ABSORBED)

    def test_the_fifteen_are_untouched(self):
        self.assertEqual([w.id for w in ALL_WHEELS], [f"W{i}" for i in range(1, 16)])
        for w in EW.WHEELS:
            self.assertIs(w, EW.wheel_named(w.id))
        self.assertEqual(len(EW.wheel_named("W4").axioms), 3)
        self.assertEqual(len(EW.wheel_named("W6").axioms), 3)
        for w in ALL_WHEELS:
            self.assertNotIn(w.id, CENT_WHEEL_IDS)

    def test_every_axiom_balances(self):
        for w in CW.CENT_WHEELS:
            t = CW.CENT_TABLES[w.id]
            for a in w.axioms:
                r = CW.residual(a, t)
                self.assertIsNotNone(r, a)
                self.assertTrue(CW.balanced_si7(a, t), (w.id, a, r))
                self.assertFalse(any(r), (w.id, a, r))  # no angle residual either

    def test_every_flag_is_span_membership(self):
        for w in CW.CENT_WHEELS:
            self.assertTrue(w.axioms, w.id)
            for c in w.cases:
                self.assertEqual(CW.is_derivable_q(c.equation, w.axioms), c.expected_derivable,
                                 c.id)

    def test_every_control_is_refused(self):
        n = 0
        for w in CW.CENT_WHEELS:
            for c in w.cases:
                if c.physical_status == CW.NEGATIVE:
                    n += 1
                    self.assertFalse(CW.is_derivable_q(c.equation, w.axioms), c.id)
        self.assertEqual(n, 15)

    def test_no_hidden_relations(self):
        for w in CW.CENT_WHEELS:
            self.assertEqual(S.hidden_relations(w.axioms, CW.CENT_TABLES[w.id]), [], w.id)

    def test_corrections_and_drops_are_applied(self):
        for corr in CW.CORRECTIONS:
            if corr.what == "axiom":
                axioms = CW.cent_wheel(corr.wheel).axioms
                self.assertIn(corr.absorbed, axioms, corr)
                self.assertNotIn(corr.supplied, axioms, corr)
            elif corr.what == "case":
                eqs = {c.id: c.equation for c in CW.cent_wheel(corr.wheel).cases}
                self.assertEqual(eqs[corr.item], corr.absorbed, corr)
            self.assertIn(corr.rule, ("a", "b", "c", "d", "span", "table"), corr)
            self.assertTrue(corr.reason, corr)
        for d in CW.DROPPED:
            if d.wheel in CENT_WHEEL_IDS:
                self.assertNotIn(d.supplied, CW.cent_wheel(d.wheel).axioms, d)
            self.assertTrue(d.reason, d)
        self.assertEqual(sorted((d.wheel for d in CW.DROPPED)), ["W22", "W32", "W33", "W35", "W35"])

    def test_w22_03_is_settled_not_derivable(self):
        s4 = report()["s4"]
        self.assertTrue(s4["met"], s4)
        self.assertFalse(s4["derivable_supplied_axioms"])
        self.assertFalse(s4["derivable_absorbed_axioms"])
        case = {c.id: c for c in CW.cent_wheel("W22").cases}["W22-03"]
        self.assertFalse(case.expected_derivable)

    def test_the_additions_and_the_domain_cases(self):
        w4, w6 = CW.extended_wheel("W4"), CW.extended_wheel("W6")
        self.assertEqual(w4.axioms[:3], EW.wheel_named("W4").axioms)
        self.assertEqual(w6.axioms[:3], EW.wheel_named("W6").axioms)
        for ext, wid in ((w4, "W4"), (w6, "W6")):
            for c in ext.cases:
                self.assertEqual(CW.is_derivable_q(c.equation, ext.axioms), c.expected_derivable, c.id)
            for a in ext.axioms:
                self.assertTrue(CW.balanced_si7(a, CW.ADDITION_TABLES[wid]), a)
        self.assertFalse(CW.is_derivable_q("power = pressure * volume_flow_rate",
                                           EW.wheel_named("W6").axioms))
        self.assertEqual(sum(len(v) for v in CW.DOMAIN_CASES.values()), 14)
        for base in DOMAIN_WHEELS:
            for c in CW.DOMAIN_CASES[base.id]:
                self.assertTrue(CW.is_derivable_q(c.equation, base.axioms), c.id)
            for a in base.axioms:
                self.assertTrue(CW.balanced_si7(a, CW.DOMAIN_TABLES[base.id]), a)

    def test_the_three_angle_axioms(self):
        a1 = report()["a1"]
        self.assertEqual(a1["count"], 3)
        self.assertEqual(sorted((w, i, r) for w, i, _, r in a1["angle_only"]),
                         [("W13", 3, "-2"), ("W14", 1, "-1"), ("W14", 2, "2")])

    def test_exact_and_no_hashlib(self):
        for mod in (CW, S, L):
            src = open(mod.__file__, encoding="utf-8").read()
            self.assertIsNone(re.search(r"\bfloat\(|\bimport hashlib|\bmath\.", src), mod.__name__)


# ---------------------------------------------------------------------------
# Against the supplied item
# ---------------------------------------------------------------------------

class TestAgainstTheSuppliedItem(unittest.TestCase):

    def setUp(self):
        self.sup = _supplied()
        if self.sup is None:
            self.skipTest("the supplied item is not in this checkout")

    def test_the_absorbed_data_is_the_supplied_data_up_to_the_record(self):
        corr_axioms = {(c.wheel, c.supplied): c.absorbed for c in CW.CORRECTIONS if c.what == "axiom"}
        corr_cases = {(c.wheel, c.item): c.absorbed for c in CW.CORRECTIONS if c.what == "case"}
        corr_tables = {(c.wheel, c.item) for c in CW.CORRECTIONS if c.what == "table"}
        dropped = {(d.wheel, d.supplied) for d in CW.DROPPED}
        for w in CW.CENT_WHEELS:
            s = self.sup[w.id]
            want = tuple(corr_axioms.get((w.id, a), a) for a in s["axioms"]
                         if (w.id, a) not in dropped)
            self.assertEqual(w.axioms, want, w.id)
            got = {c.id: c.equation for c in w.cases}
            for c in s["cases"]:
                self.assertEqual(got[c["id"]], corr_cases.get((w.id, c["id"]), c["equation"]), c["id"])
            self.assertEqual(set(got), {c["id"] for c in s["cases"]}, w.id)
            table = S.supplied_table(s)
            for q, row in table.items():
                if (w.id, q) not in corr_tables:
                    self.assertEqual(CW.CENT_TABLES[w.id][q], row, (w.id, q))

    def test_marks_d1_d2_s1_s2_s3_s5_absorption(self):
        rep = report()
        for k in ("d1", "d2", "s1", "s2", "s3", "s5", "absorption"):
            self.assertTrue(rep[k]["met"], (k, rep[k]))
        self.assertEqual(rep["d1"]["axioms"], 72)
        self.assertEqual(rep["d1"]["unknown"], 0)
        self.assertEqual(len(rep["d1"]["failing_si7"]), 10)
        self.assertEqual(rep["s2"]["supplied_controls"], 26)
        self.assertEqual(rep["s2"]["licensed"], [])

    def test_mark_e2_finds_the_w4_case_the_item_omits(self):
        e2 = report()["e2"]
        self.assertFalse(e2["met"])
        self.assertEqual(e2["problems"], ["W4 cases differ"])
        self.assertEqual(e2["case_differences"],
                         [{"wheel": "W4", "only_supplied": [], "only_repository": ["W4-M1"]}])

    def test_the_lean_file_states_exactly_the_failing_axioms(self):
        failing = [(w, i, t) for w, i, t, _ in report()["d1"]["failing_si7"]]
        self.assertEqual(sorted(L.agreement()["supplied"]), sorted(failing))


# ---------------------------------------------------------------------------
# The Lean file
# ---------------------------------------------------------------------------

class TestLeanAgreement(unittest.TestCase):

    def setUp(self):
        self.text = L.lean_text()
        if not self.text:
            self.fail(f"{L.CENT_WHEELS_LEAN} is missing")

    def test_in_the_build_tree_and_audited(self):
        self.assertTrue(C.lean_file(L.CENT_WHEELS_LEAN).is_file())
        self.assertTrue(lean_check.audited_or_held(L.CENT_WHEELS_LEAN))

    def test_header(self):
        self.assertTrue(self.text.startswith("module\n"))
        self.assertIn("public import Mathlib", self.text)
        self.assertIn("public import RequestProject.GLM.ConnectedMachine", self.text)
        self.assertIn("@[expose] public section", self.text)
        self.assertIn("namespace GLM.CentWheels", self.text)
        self.assertIn("Created 31 October 2026 (repository check; the intake of cent_compiler_v12, "
                      "directive D22)", self.text)
        code = L._code_only(self.text)
        for bad in ("sorry", "admit", "native_decide"):
            self.assertNotIn(bad, code)
        self.assertIsNone(re.search(r"^\s*axiom\b", code, re.MULTILINE))

    def test_agreement(self):
        a = L.agreement(self.text)
        self.assertTrue(a["ok"], a["problems"])
        self.assertEqual(a["wheels"], 22)
        self.assertEqual(a["axioms"], 48)
        self.assertEqual(a["derivable"] + a["refused"],
                         sum(len(L.parse_block(b)["questions"]) for n, b in L.blocks(self.text).items()
                             if n != "Supplied") + 1)

    def test_every_case_and_question_has_a_theorem(self):
        names = set(L.theorem_names(self.text))
        for w in CW.CENT_WHEELS:
            for qid, _ in S.wheel_questions(w):
                self.assertIn(S.lean_name(qid), names, qid)
        for base in DOMAIN_WHEELS:
            for c in CW.DOMAIN_CASES[base.id]:
                self.assertIn(S.lean_name(c.id), names, c.id)
        for n in ("derivable_of_combo", "not_derivable_of_dot", "q_W6_03_without_addition",
                  "q_W4_04", "q_W22_03", "W34_axiom_1_unbalanced"):
            self.assertIn(n, names)

    def test_a_tampered_certificate_is_caught(self):
        bad = self.text.replace("derivable_of_combo ax ![-1, 0, 0] _", "derivable_of_combo ax ![-2, 0, 0] _", 1)
        self.assertNotEqual(bad, self.text)
        self.assertFalse(L.agreement(bad)["ok"])
        bad = self.text.replace("theorem q_W22_03 : ¬ Derivable", "theorem q_W22_03 : Derivable", 1)
        self.assertFalse(L.agreement(bad)["ok"] if bad != self.text else False)

    def test_the_file_is_the_generators_text(self):
        self.assertEqual(self.text, S.lean_source())


# ---------------------------------------------------------------------------
# The query surface
# ---------------------------------------------------------------------------

class TestAnswerDerivability(unittest.TestCase):

    def test_registry_first(self):
        a = answer_derivability("force = mass * acceleration")
        self.assertEqual((a["verdict"], a["wheel"]), ("derivable", "W5"))

    def test_a_new_domain(self):
        a = answer_derivability("emf = magnetic_field * area / time")
        self.assertEqual((a["verdict"], a["wheel"]), ("derivable", "W16"))
        self.assertTrue(all(isinstance(x, Fraction) for _, x in a["certificate"]))
        a = answer_derivability("emf = magnetic_field * area / time", with_registry=False)
        self.assertEqual(a["wheel"], "W16")

    def test_fractional(self):
        a = answer_derivability("crack_length = (stress_intensity_factor / (dimensionless_factor * stress))^2")
        self.assertEqual((a["verdict"], a["wheel"]), ("derivable", "W21"))

    def test_refusals(self):
        a = answer_derivability("flux = 2 * magnetic_field * area")
        self.assertEqual(a["verdict"], "not derivable")
        a = answer_derivability("diffusion_coefficient = diffusion_flux / concentration_gradient", "W22")
        self.assertEqual(a["verdict"], "not derivable")
        self.assertEqual(a["functional"], {"concentration_gradient": 1})
        self.assertEqual(answer_derivability("membrane_voltage = log(temperature)")["verdict"],
                         "unreadable")

    def test_a_registry_wheel_by_id(self):
        a = answer_derivability("power = voltage * current", "W1")
        self.assertEqual(a["verdict"], "derivable")


# ---------------------------------------------------------------------------
# The study's measurement
# ---------------------------------------------------------------------------

class TestStudyMeasurement(unittest.TestCase):

    def test_the_battery(self):
        qs = S.MEASURE_BATTERY
        self.assertEqual(len(qs), 115)
        self.assertEqual(sum(q[3] == S.LAW for q in qs), 64)
        self.assertEqual(sum(q[3] == S.NOT_A_LAW for q in qs), 51)
        by = {}
        for q in qs:
            by[q[4]] = by.get(q[4], 0) + 1
        self.assertEqual(by, {S.CASE: 48, S.CONTROL: 16, S.SUPPLIED_FORM: 13, S.HELD_OUT: 38})
        self.assertEqual(len({q[0] for q in qs}), 115)
        self.assertEqual((S.BAR_WRONG_MAX, S.BAR_LAWS_LICENSED_MIN, S.BAR_BASELINE_LAWS_MAX), (0, 56, 4))

    def test_m1_m2_m3(self):
        b = report()["battery"]
        self.assertTrue(b["m1_met"] and b["m2_met"] and b["m3_met"], b)
        self.assertEqual(b["cent_wrong"], [])
        self.assertEqual(b["baseline_wrong"], [])
        self.assertEqual(b["cent_laws_licensed"], 63)
        self.assertEqual(b["cent_misses"], ["W22-03"])
        self.assertEqual(b["baseline_laws_licensed"], ["W23-03"])
        self.assertEqual(b["new_laws"], 62)

    def test_m4_the_union_conflates(self):
        b = report()["battery"]
        self.assertEqual(b["union_wrong"], ["H16-F", "H17-F", "H18-F", "H23-F"])
        for c in report()["union_conflations"]:
            self.assertTrue({"W1", "W3", "W15"} <= set(c["wheels_used"]), c)

    def test_l1(self):
        self.assertTrue(report()["l1"]["met"], report()["l1"])


if __name__ == "__main__":
    unittest.main()
