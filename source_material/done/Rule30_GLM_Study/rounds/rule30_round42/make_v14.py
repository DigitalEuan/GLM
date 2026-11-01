#!/usr/bin/env python3
"""Build `hypothesis_engine_v14.py` from the owner's `hypothesis_engine_v13.py` (Round 42).

v13 is left untouched.  Every change is a named patch below; each must match exactly once, so
the build fails loudly if v13 changes.  `v14_patches.md` lists the patches.

v14 = v13 + (1) corrected TAX statements, (2) the Round 42 guards run inside the engine
(`glm_guards.py`, `tax_guards.py`): after the TAX stage and again after the dialogue, so that no
refuted claim, unexplained "finding" or false "only at" sentence reaches the report.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "hypothesis_engine_v13.py"
DST = HERE / "hypothesis_engine_v14.py"

V14_HEADER = '''"""GLM Hypothesis Engine v14 — v13 plus reasoning guards (Round 42).

Built by rule30_round42/make_v14.py from hypothesis_engine_v13.py; the patches are listed in
rule30_round42/v14_patches.md.  Needs glm_guards.py and tax_guards.py from the same folder
(standard library only).

What v14 changes:
  * TAX statements corrected.  Conservation does not need Y to be irrational (the linear part
    always cancels), and it holds iff 3c^2 - 2c(a+b) + ab = 0 for the weights a, b and the
    overlap c -- not iff c in {0, a, b}.  Lean: TaxChecks.lean (tax_defect_eq,
    tax_conserved_iff_defect_zero, docstring_criterion_wrong).
  * Guards run inside the engine (glm_guards.py):
      identity      -- a stated criterion is brute-forced against the truth;
      explained-away-- a "finding" at the events is checked against known law premises
                       (here: every doubling has white(D-1), and white(D-1) forces TAX
                       conservation -- Lean tax_conserved_at_doubling);
      coincidence   -- the exact hypergeometric test v13's header promised;
      exclusivity   -- "only at S" claims are checked against all feature points
                       (Lean tax_conserved_not_only_white);
      consistency   -- no sentence may assert a claim whose hypothesis was refuted.
  * The fixed TAX conclusions of the dialogue are replaced by the guard sentences.
  * "NEW TO THE LEDGER" is no longer printed for refuted hypotheses.

The v13 description follows.

GLM Hypothesis Engine v13 — self-contained, with the TAX-period-doubling correlation.'''

PATCHES = [
    ("header", '"""GLM Hypothesis Engine v13 — self-contained, with the TAX-period-doubling correlation.',
     V14_HEADER),
    ("import guards", 'HERE = Path(__file__).resolve().parent\n',
     'HERE = Path(__file__).resolve().parent\n'
     'sys.path.insert(0, str(HERE))\n'
     'from tax_guards import guard_tax_section, corrected_sentences  # noqa: E402  (v14)\n'),
    ("tax docstring: Y", "Y = 1/(π + 2/π) an irrational the GLM treats as a process.  Because Y is irrational, the\n    conservation identity",
     "Y = 1/(π + 2/π).  For EVERY real Y (v14: irrationality is not needed, the linear part\n    cancels because w(a XOR b) = w(a) + w(b) - 2 w(a AND b) always holds) the\n    conservation identity"),
    ("tax docstring: criterion",
     "This in turn holds iff w(a AND b) ∈ {0, w(a), w(b)} (the patterns do not partially\n    overlap).  A \"TAX defect\" is the integer-layer violation: a partial overlap.",
     "v14 correction: with a = w(a), b = w(b), c = w(a AND b) the defect equals\n"
     "    -2 (3c^2 - 2c(a+b) + ab), so conservation holds iff 3c^2 - 2c(a+b) + ab = 0.  This is NOT\n"
     "    'c in {0, a, b}': disjoint single cells (c = 0) have defect -2, and a = 5, b = 8, c = 2 is\n"
     "    conserved (Lean: tax_defect_eq, docstring_criterion_wrong)."),
    ("novelty label",
     "            if h.key not in self.LEDGER and h.key not in self.LEAN:\n"
     "                self.log(f\"    {h.hid}: NEW TO THE LEDGER — {h.text[:60]}...\")",
     "            if h.status.startswith(\"refuted\"):  # v14: refuted is never 'new to the ledger'\n"
     "                self.log(f\"    {h.hid}: refuted ({h.status}) — not a ledger candidate\")\n"
     "                h.novelty = f\"refuted ({h.status})\"\n"
     "            elif h.key not in self.LEDGER and h.key not in self.LEAN:\n"
     "                self.log(f\"    {h.hid}: NEW TO THE LEDGER — {h.text[:60]}...\")"),
    ("h_mech text",
     "CONFIRM that the jumps share bits (necessary, from v12), but the tool does \"\n"
     "                f\"NOT distinguish jumps from non-jumps — TAX defects are nearly ubiquitous.\"",
     "test the jumps; every jump has TAX defect 0 (forced by white(D-1)), so a \"\n"
     "                f\"defect is not necessary for a jump, and defects are nearly ubiquitous.\""),
    ("lift text",
     "is NECESSARY (v12: every jump has a defect) but not SUFFICIENT (v13: defects \"\n"
     "                \"are everywhere)",
     "is NOT necessary (every jump has defect 0, forced by white(D-1)) and not \"\n"
     "                \"sufficient (defects are everywhere)"),
    ("h_pos text",
     "the law H08 says a jump occurs exactly when \"\n                        \"the (D-1) pattern is eventually white (w(D-1) = 0).",
     "the law H08 requires (with odd parity of D-2) \"\n                        \"the (D-1) pattern to be eventually white (w(D-1) = 0)."),
    ("report name",
     'rep = {"engine": "GLM Hypothesis Engine v13 (self-contained; TAX-period-doubling correlation)",',
     'rep = {"engine": "GLM Hypothesis Engine v14 (v13 + reasoning guards)",\n'
     '               "guards": [g.as_dict() for g in getattr(self, "guard_results", [])],'),
    ("run guards after dialogue",
     "        self.tool_dialogue.run(self.hyps, centre_bits, big)\n        self.credit()",
     "        self.tool_dialogue.run(self.hyps, centre_bits, big)\n"
     "        # v14: guards over the whole run (hypotheses, evidence and every utterance)\n"
     "        self.guard_results = guard_tax_section(self, self.tool_dialogue.utterances, mutate=True)\n"
     "        self.log(\"== Guards (v14) ==\")\n"
     "        for g in self.guard_results:\n"
     "            self.log(f\"  [{'ok  ' if g.ok else 'FLAG'}] {g.sentence}\")\n"
     "        self.credit()"),
    ("md title", '"# GLM Hypothesis Engine v13 — run report"', '"# GLM Hypothesis Engine v14 — run report"'),
    ("lean title", '"-- Proposals emitted by the GLM Hypothesis Engine v13."',
     '"-- Proposals emitted by the GLM Hypothesis Engine v14."'),
    ("lean file", '(HERE / "r38_conjectures_v13.lean.txt")', '(HERE / "r42_conjectures_v14.lean.txt")'),
    ("stems", 'stem = "r38_engine_report_v13_quick" if quick else "r38_engine_report_v13"',
     'stem = "r42_engine_report_v14_quick" if quick else "r42_engine_report_v14"'),
    ("default stem", 'def write_outputs(rep: dict, stem: str = "r38_engine_report_v13"):',
     'def write_outputs(rep: dict, stem: str = "r42_engine_report_v14"):'),
    ("print guards", "    write_outputs(rep, stem)\n",
     "    write_outputs(rep, stem)\n"
     "    print()\n"
     "    print(\"Guards (v14):\")\n"
     "    for g in rep.get(\"guards\", []):\n"
     "        print(f\"  [{'ok  ' if g['ok'] else 'FLAG'}] {g['sentence']}\")\n"),
]

# span patches: replace from a start marker up to and including an end marker
SPANS = [
    ("what next 1",
     '        self.speak("1. Extend the TAX-period-doubling correlation to D > 87867. The current test "',
     '"should cluster around the next predicted jump.")\n',
     '        self.speak("1. (v14) Do not extend the TAX clustering test: every doubling has defect 0 "\n'
     '                   "because it needs white(D-1), so a jump itself never carries a TAX defect at any "\n'
     '                   "range. Spend the budget on the predicted period-64 doubling at "\n'
     '                   "2107985255 (ledger C381, EMP) instead.")\n'),
    ("dialogue TAX conclusions",
     '                self.speak("The mechanism for period doubling is the deeper structural fact "',
     '"structure, not its defect structure.")\n',
     "                # v14: the fixed conclusions of v13 are replaced by the guard sentences\n"
     "                for s in corrected_sentences(guard_tax_section(self.engine, self.utterances)):\n"
     "                    self.speak(s)\n"),
    ("what next 2",
     '        self.speak("2. Formalise the TAX-mechanism conjecture in Lean. The statement is: "',
     '"second half is empirical.")\n',
     '        self.speak("2. (v14) The Lean side is done: PeriodJump(D) -> TAXDefect(D-1, D) is "\n'
     '                   "FALSE at every doubling (tax_conserved_at_doubling); the TAX defect is "\n'
     '                   "-2(3c^2 - 2c(a+b) + ab) (tax_defect_eq). Next: look for an invariant that "\n'
     '                   "is not forced by white(D-1), e.g. the parity of D-2 read two out "\n'
     '                   "(doubling_read_two_out).")\n'),
]


def build() -> str:
    s = SRC.read_text()
    log = []
    for name, old, new in PATCHES:
        n = s.count(old)
        if name == "print guards":
            assert n >= 1, name
            i = s.rindex(old)            # the call in main()
            s = s[:i] + new + s[i + len(old):]
        else:
            assert n == 1, f"patch '{name}' matched {n} times"
            s = s.replace(old, new)
        log.append(name)
    for name, start, end, new in SPANS:
        i = s.index(start)
        j = s.index(end, i) + len(end)
        assert s.count(start) == 1, f"span '{name}' start matched {s.count(start)} times"
        s = s[:i] + new + s[j:]
        log.append(name)
    DST.write_text(s)
    md = ["# Patches applied by `make_v14.py` (v13 → v14)", "",
          "| # | patch |", "|---|---|"] + [f"| {k + 1} | {n} |" for k, n in enumerate(log)]
    (HERE / "v14_patches.md").write_text("\n".join(md) + "\n")
    return s


if __name__ == "__main__":
    build()
    print(f"wrote {DST.name} ({len(DST.read_text().splitlines())} lines)")
