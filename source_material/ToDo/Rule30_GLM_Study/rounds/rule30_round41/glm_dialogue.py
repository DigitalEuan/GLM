#!/usr/bin/env python3
"""GLM self-dialogue, v11 (Round 41) — every answer is an action.

This keeps the idea of `hypothesis_engine_v10.py` (after the hypotheses are generated, the engine
questions itself: state → what would refute it? → what does it imply? → how does it connect? →
what next?) and changes how each question is answered.

In v10 the answers are fixed sentences picked by keywords in the hypothesis text, and some of them
carry numbers and mathematical claims that were true (or believed) when they were written.  Here:

  STATE    is assembled only from the hypothesis record (status, evidence class, the largest
           index actually checked, the witness).
  REFUTE   *runs* the refutation: the statement is checked on fresh, larger ranges (doubling up to
           a per-puzzle budget).  Statements of class Pi2 are not extended: no finite observation
           can refute them, and the dialogue says so.
  IMPLIES  answers only from a knowledge graph of *checked* implications.  Each edge says
           `follows`, `equivalent` or `does-not-follow`, and names the Lean theorem (or ledger
           claim) that backs it.  With no edge, the answer is "nothing on record".
  CONNECT  uses the record: parent/children, statements refuted by the same witness, statements
           about the same invariant.
  NEXT     picks an action by a fixed rule and *executes* it: read a counterexample (mine a law
           for the event "the statement fails" with the puzzle's local predicates), narrow a
           refuted bound, split a junction between two forms, or hand a survivor to the prover.
           New hypotheses created by an action join the queue and are discussed in turn.

Every utterance carries its provenance (`computed`, `record`, `lean:<name>`, `ledger:<id>`), and a
grounding guard checks that every number of 3 or more digits in an utterance was either computed
in this run or appears in the ledger.  `v10_audit.py` applies the same guard to v10's sentences.

Exact arithmetic only.  Needs only the standard library and the Round 39 core
(`../rule30_round39/glm_hypothesis_core.py`).
"""

from __future__ import annotations

import json
import re
import sys
from math import lcm
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rule30_round39"))

from glm_hypothesis_core import Core, Hyp  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════════════════
# knowledge: checked implications and ledger facts
# ════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class Edge:
    premise: str            # a tag carried by hypotheses (h.meta["tags"])
    conclusion: str         # plain statement
    verdict: str            # follows | equivalent | does-not-follow
    backing: str            # "lean:<name>" or "ledger:<id>"
    evidence_class: str     # FORMAL | CERT | EMP
    note: str = ""
    same_as: str = ""       # for ties: a tag whose statement is equivalent to the premise's


@dataclass
class Knowledge:
    edges: list = field(default_factory=list)
    facts: list = field(default_factory=list)   # {"id","text","numbers","class","lean"}

    @staticmethod
    def load(path: Path) -> "Knowledge":
        d = json.loads(path.read_text())
        return Knowledge([Edge(**e) for e in d["edges"]], d["facts"])

    def about(self, tags) -> list:
        return [e for e in self.edges if e.premise in tags and not e.same_as]

    def same(self, tags_a, tags_b) -> Optional[Edge]:
        for e in self.edges:
            if e.same_as and ((e.premise in tags_a and e.same_as in tags_b) or
                              (e.premise in tags_b and e.same_as in tags_a)):
                return e
        return None

    def facts_about(self, tags) -> list:
        return [f for f in self.facts if set(f.get("tags", ())) & set(tags)]

    def numbers(self) -> set:
        out = set()
        for f in self.facts:
            out |= set(int(n) for n in f.get("numbers", []))
        return out


# ════════════════════════════════════════════════════════════════════════════════════════════
# grounding guard
# ════════════════════════════════════════════════════════════════════════════════════════════

_MULT = {"thousand": 10 ** 3, "million": 10 ** 6, "billion": 10 ** 9}
_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\s*(thousand|million|billion))?")


def numbers_in(text: str) -> list:
    """Integers of 3 or more digits in a sentence ("400,000", "275 million" → 275000000)."""
    out = []
    for m in _NUM.finditer(text):
        v = int(m.group(1).replace(",", ""))
        if m.group(2):
            v *= _MULT[m.group(2)]
        if v >= 100:
            out.append(v)
    return out


class Guard:
    """A number may be uttered only if it was computed in this run or is in the ledger."""

    def __init__(self, ledger_numbers: set):
        self.ledger = set(ledger_numbers)
        self.computed: set = set()

    def note(self, *values):
        for v in values:
            if isinstance(v, int) and not isinstance(v, bool):
                self.computed.add(v)

    def ungrounded(self, text: str) -> list:
        return [v for v in numbers_in(text) if v not in self.computed and v not in self.ledger]


# ════════════════════════════════════════════════════════════════════════════════════════════
# puzzle-side configuration
# ════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class PuzzleConfig:
    """What the dialogue may do on one puzzle.  Nothing here is a sentence."""
    name: str
    budget: int                                   # largest index REFUTE may observe
    caps: dict = field(default_factory=dict)      # invariant -> smaller budget (costly ones)
    domain: Optional[Callable] = None             # (lo, hi) -> indices to check (default range)
    predicates: dict = field(default_factory=dict)  # local predicates for reading counterexamples
    events: dict = field(default_factory=dict)    # invariant -> (label, event) to explain on refutation
    tagger: Optional[Callable] = None             # Hyp -> set of tags (structural, from meta)
    mine_from: int = 0                            # first index the local predicates make sense at
    max_turns: int = 40


# ════════════════════════════════════════════════════════════════════════════════════════════
# the dialogue
# ════════════════════════════════════════════════════════════════════════════════════════════

_RANK = {"law-holds": 0, "form-holds": 1, "survives": 2, "open": 3, "refuted-heldout": 4,
         "refuted-structural": 4, "refuted-dev": 6, "junction-split": 5}
_NEXT_STAGE = re.compile(r"(\d+)\s*$")


def checked_upto(h: Hyp) -> int:
    """Largest index actually checked, read from the evidence stage names ('dev 0..399')."""
    best = -1
    for stage, ok, detail in h.evidence:
        for m in re.finditer(r"\.\.(\d+)", stage):
            best = max(best, int(m.group(1)))
        for m in re.finditer(r"[<≤]\s*(\d+)", stage):
            best = max(best, int(m.group(1)) - 1)
    return best


class Dialogue:
    def __init__(self, core: Core, cfg: PuzzleConfig, know: Knowledge):
        self.core, self.cfg, self.know = core, cfg, know
        self.guard = Guard(know.numbers())
        self.turns: list = []
        self.discussed: set = set()
        self.read: dict = {}
        self.actions = 0

    # -- utterances ---------------------------------------------------------------------------
    def say(self, kind: str, hid: str, text: str, prov: str):
        bad = self.guard.ungrounded(text)
        self.turns.append({"hyp": hid, "kind": kind, "text": text, "provenance": prov,
                           "ungrounded_numbers": bad})

    def tags(self, h: Hyp) -> set:
        t = set(h.meta.get("tags", ()))
        if self.cfg.tagger:
            t |= set(self.cfg.tagger(h))
        if h.status.startswith("refuted"):
            t |= {x + ":refuted" for x in t}
        return t

    def key(self, h: Hyp) -> Optional[str]:
        if "key" in h.meta:
            return h.meta["key"]
        if "conj" in h.meta:  # a mined law: its key is the event it explains
            return "law:" + h.text.split(" ⟺ ")[0]
        return None

    # -- STATE --------------------------------------------------------------------------------
    def state(self, h: Hyp):
        top = checked_upto(h)
        self.guard.note(top, h.witness if isinstance(h.witness, int) else None)
        self.guard.note(*numbers_in(h.text))  # the text was produced by this run's computation
        for _, _, detail in h.evidence:
            self.guard.note(*numbers_in(detail))
        parts = [f"{h.hid}: {h.text}.", f"Status {h.status}, evidence class {h.evidence_class}."]
        if h.status.startswith("refuted"):
            parts.append(f"Refuted at k = {h.witness}.")
        elif top >= 0:
            parts.append(f"Checked up to index {top}; nothing beyond is claimed.")
        if h.lean:
            parts.append(f"Lean statement handed over: {h.lean}.")
        self.say("state", h.hid, " ".join(parts), "record")

    # -- REFUTE -------------------------------------------------------------------------------
    def refute(self, h: Hyp):
        if h.status.startswith("refuted"):
            last = next((e for e in reversed(h.evidence) if not e[1]), None)
            self.say("refute", h.hid, f"Already refuted: {last[0]}: {last[2]}." if last else
                     "Already refuted.", "record")
            return
        if h.evidence_class == "Pi2":
            self.say("refute", h.hid, "Class Pi2 (for all k there exists ...): no finite set of "
                     "observations can refute it, so I do not extend the range. A proof or a "
                     "structural argument is needed.", "record")
            return
        if h.status == "open":
            self.say("refute", h.hid, "Status open: I hold no finite test for it.", "record")
            return
        if h.evidence_class == "FINITE":
            self.say("refute", h.hid, "Class FINITE: it speaks about finitely many indices, all "
                     "already checked, so there is nothing further to refute.", "record")
            return
        key = self.key(h)
        budget = min(self.cfg.budget, self.cfg.caps.get(key, self.cfg.budget))
        top = checked_upto(h)
        lo = self.core.fam.lo
        hi = max(top + 1, lo + 1)
        if hi >= budget:
            self.say("refute", h.hid, f"It would be refuted by one index where it fails. The "
                     f"budget for this invariant ({budget}) is already used up.", "record")
            return
        reached = hi
        while hi < budget:
            nxt = min(2 * hi, budget)
            dom = self.cfg.domain(hi, nxt) if self.cfg.domain else range(hi, nxt)
            R = self.core.records(nxt)
            self.actions += 1
            fail = next((k for k in dom if not h.test(R, k)), None)
            stage = f"dialogue held-out {hi}..{nxt - 1}"
            if fail is not None:
                h.status = "refuted-heldout"
                h.witness = fail
                h.evidence.append((stage, False, f"fails at k={fail}"))
                self.guard.note(fail, hi, nxt - 1)
                self.say("refute", h.hid, f"It is refuted by one failing index. I checked "
                         f"{hi}..{nxt - 1} and it fails at k = {fail}.", "computed")
                return
            h.evidence.append((stage, True, "passes"))
            reached = nxt
            hi = nxt
        self.guard.note(reached - 1)
        self.say("refute", h.hid, f"It would be refuted by one failing index. I extended the "
                 f"check to every index up to {reached - 1} and found none. Still class "
                 f"{h.evidence_class}: surviving a range is not a proof.", "computed")

    # -- IMPLIES ------------------------------------------------------------------------------
    def implies(self, h: Hyp):
        tags = self.tags(h)
        edges = [e for e in self.know.about(tags) if not e.premise.startswith("proved:")]
        if h.status.startswith("refuted"):
            edges = [e for e in edges if e.verdict == "does-not-follow" or
                     e.premise.endswith(":refuted")]
        if not edges:
            self.say("implies", h.hid, "No checked implication on record for this statement; I "
                     "do not state one.", "record")
            return
        for e in edges:
            word = {"follows": "implies", "equivalent": "is equivalent to",
                    "does-not-follow": "does NOT by itself imply"}[e.verdict]
            self.say("implies", h.hid, f"It {word}: {e.conclusion} [{e.evidence_class}]"
                     + (f" ({e.note})" if e.note else ""), e.backing)

    # -- CONNECT ------------------------------------------------------------------------------
    def connect(self, h: Hyp):
        hyps = self.core.hyps
        out = []
        if h.parent:
            p = next((x for x in hyps if x.hid == h.parent), None)
            if p:
                out.append(f"derived from {p.hid} ({p.status})")
        kids = [x.hid for x in hyps if x.parent == h.hid]
        if kids:
            out.append(f"parent of {', '.join(kids)}")
        if isinstance(h.witness, int):
            same = [x.hid for x in hyps if x is not h and x.witness == h.witness]
            if same:
                out.append(f"refuted by the same index k = {h.witness} as {', '.join(same)}")
        key = self.key(h)
        if key:
            sib = [x.hid for x in hyps if x is not h and x.meta.get("key") == key]
            if sib:
                out.append(f"about the same invariant `{key}` as {', '.join(sib)}")
        self.say("connect", h.hid, ("; ".join(out) + ".") if out else
                 "No recorded connection to other statements.", "record")

    # -- NEXT ---------------------------------------------------------------------------------
    def next_step(self, h: Hyp) -> list:
        """Choose and run one action.  Returns new hypotheses to discuss."""
        core, cfg = self.core, self.cfg
        key = self.key(h)
        before = len(core.hyps)
        if h.status == "refuted-heldout" and isinstance(h.witness, int) and (
                key in cfg.events or h.meta.get("kind") in ("bound", "divides")):
            if key in cfg.events:
                self._read_counterexample(h, key)
            if h.meta.get("kind") in ("bound", "divides"):
                self._narrow_and_watch(h, key)
        elif h.status == "form-holds":
            rivals = [x for x in core.hyps if x is not h and x.status == "form-holds"
                      and x.meta.get("key") == key and "eval" in x.meta and "eval" in h.meta]
            if rivals:
                r = rivals[0]
                self.actions += 1
                lo = checked_upto(h) + 1
                k = core.junction(h, r, range(lo, lo + 200),
                                  lambda x, k: x.meta["eval"](k))
                self.guard.note(k)
                self.say("next", h.hid, f"Next: split the junction with {r.hid}. "
                         + (f"They first disagree at k = {k}; after observing it: {h.hid} "
                            f"{h.status}, {r.hid} {r.status}." if k is not None else
                            "They agree on the next 200 indices."), "computed")
            else:
                self.say("next", h.hid, "Next: hand the form to the prover"
                         + (f" ({h.lean})." if h.lean else "; no Lean statement is attached "
                            "yet, so stating one is the next step."), "record")
        elif h.status in ("survives", "law-holds"):
            tags = self.tags(h)
            backed = [e for e in self.know.edges if e.premise.startswith("proved:")
                      and (e.premise in tags or e.premise[len("proved:"):] in tags)]
            rivals = [x for x in core.hyps if x is not h and x.status == "law-holds"
                      and key and self.key(x) == key]
            same = [(x, self.know.same(tags, self.tags(x))) for x in rivals]
            for x, e in same:
                if e is not None:
                    self.say("next", h.hid, f"Tied with {x.hid}, and no observation can split "
                             f"the tie: the two statements are equivalent ({e.note}).",
                             e.backing)
            open_ties = [x.hid for x, e in same if e is None]
            if open_ties:
                top = checked_upto(h)
                self.say("next", h.hid, f"Still tied with {', '.join(open_ties)} on every index "
                         f"up to {top}: the separating observation is beyond the budget, so the "
                         f"tie is reported, not resolved.", "computed")
            for f in self.know.facts_about(tags):
                self.say("next", h.hid, f"Ledger {f['id']} [{f['class']}]: {f['text']}.",
                         f"ledger:{f['id']}")
            if h.evidence_class == "FINITE":
                self.say("next", h.hid, "Next: it is finite and fully checked, so a finite "
                         "certificate (a decision procedure in the prover) can close it.",
                         "record")
            elif backed:
                self.say("next", h.hid, f"Next: nothing to compute — the prover already has "
                         f"it ({backed[0].backing.split(':', 1)[1]}).", backed[0].backing)
            else:
                self.say("next", h.hid, f"Next: state it in Lean and try to prove it; meanwhile "
                         f"it is only '{h.status}' on the checked range.", "record")
        elif h.status == "open" or h.evidence_class == "Pi2":
            self.say("next", h.hid, "Next: look for a finite surrogate (a statement with a "
                     "certificate) or a structural argument; more sampling cannot settle it.",
                     "record")
        else:
            self.say("next", h.hid, "Next: nothing — " + (
                "refuted, and no event to explain is registered for this invariant."
                if h.status.startswith("refuted") else "no rule applies to this status."), "record")
        return core.hyps[before:]

    def _read_counterexample(self, h: Hyp, key: str):
        """Explain the event that made `h` fail, with the puzzle's local predicates."""
        core, cfg = self.core, self.cfg
        label, event = cfg.events[key]
        top = checked_upto(h) + 1
        self.guard.note(top)
        done = self.read.get(label)
        if done is not None and done[0] >= top:
            self.say("next", h.hid, f"Next: read the counterexample. Already done for "
                     f"'{label}' (below {done[0]}): {', '.join(done[1]) or 'no law'}.", "record")
            return
        self.actions += 1
        laws = core.mine(event, cfg.predicates, range(max(core.fam.lo, cfg.mine_from), top),
                         label=label) if cfg.predicates else []
        for l in laws:
            l.parent = h.hid
            l.meta["key"] = f"law:{key}"
            l.meta.setdefault("tags", set()).update(
                {f"law:{key}", f"law:{key}:{' ∧ '.join(l.meta['conj'])}"})
        self.read[label] = (top, [l.hid for l in laws])
        if laws:
            self.say("next", h.hid, f"Next: read the counterexample. I mined {len(laws)} exact "
                     f"law(s) for '{label}' on indices below {top}: "
                     + "; ".join(f"{l.hid} {l.text}" for l in laws) + ".", "computed")
        else:
            self.say("next", h.hid, f"Next: read the counterexample. No conjunction of the "
                     f"{len(cfg.predicates)} local predicates explains '{label}' below {top}; "
                     f"a new predicate is needed.", "computed")

    def _narrow_and_watch(self, h: Hyp, key: str):
        core = self.core
        before = len(core.hyps)
        top = checked_upto(h) + 1
        self.actions += 1
        self._narrow(h, top)
        new = core.hyps[before:]
        self.say("next", h.hid, f"Next: narrow. {len(new)} refined statement(s): "
                 + "; ".join(f"{x.hid} {x.text} ({x.status})" for x in new) + ".", "computed")
        # a pattern of refutations: every bound on this invariant has failed so far
        fails = [x for x in core.hyps if x.meta.get("key") == key and
                 x.meta.get("kind") == h.meta["kind"] and x.status == "refuted-heldout"]
        self.guard.note(*[x.witness for x in fails])
        if len(fails) >= 3 and not any(x.meta.get("unbounded") == key for x in core.hyps):
            u = core.new(text=f"{key}(k) is unbounded (every bound is eventually exceeded)",
                         test=lambda r, k: True, origin="pattern-of-refutations",
                         parent=h.hid, evidence_class="Pi2",
                         meta={"unbounded": key, "tags": {f"unbounded:{key}"}})
            u.status = "open"
            u.evidence.append(("refutations", True, "bounds refuted at "
                               + ", ".join(str(x.witness) for x in fails)))
            self.say("next", h.hid, f"{len(fails)} successive bounds on `{key}` were refuted "
                     f"(at {', '.join(str(x.witness) for x in fails)}); I propose {u.hid}: "
                     f"{u.text}. It is class Pi2, so it goes to the prover, not to sampling.",
                     "computed")

    def _narrow(self, h: Hyp, top: int):
        """The core's `refine`, for this one statement: cut it to where it holds, and narrow
        its parameter on all data below `top`."""
        core = self.core
        lo, w = core.fam.lo, h.witness
        c = core.new(text=f"[{h.text}] for k < {w}", origin="cut", parent=h.hid,
                     test=lambda r, k, t=h.test, w=w: k >= w or t(r, k),
                     evidence_class="FINITE", meta={"tags": set()})
        c.status = "survives"
        c.evidence.append(("cut", True, f"holds on every k < {w}"))
        kind, key = h.meta["kind"], h.meta["key"]
        R = core.records(top)
        vals = [R[k][key] for k in range(lo, top)]
        tags = set(h.meta.get("tags", ())) - {t for t in h.meta.get("tags", ())
                                              if t.endswith(":refuted")}
        if kind == "divides":
            L = lcm(*vals)
            self.guard.note(L)
            n = core.new(text=f"{key}(k) divides {L} for every k", origin="narrow",
                         parent=h.hid, test=lambda r, k, key=key, L=L: L % r[k][key] == 0,
                         meta={"key": key, "kind": "divides", "param": L, "tags": tags})
        else:
            M = max(vals)
            self.guard.note(M)
            n = core.new(text=f"{key}(k) ≤ {M} for every k", origin="narrow", parent=h.hid,
                         test=lambda r, k, key=key, M=M: r[k][key] <= M,
                         meta={"key": key, "kind": "bound", "param": M, "tags": tags})
        core.check(n, range(lo, top), f"all data <{top}")
        self.guard.note(top)

    # -- loop ---------------------------------------------------------------------------------
    def run(self, focus: Optional[list] = None) -> list:
        queue = list(focus) if focus is not None else sorted(
            self.core.hyps, key=lambda h: (_RANK.get(h.status, 9), h.hid))
        turns = 0
        while queue and turns < self.cfg.max_turns:
            h = queue.pop(0)
            if h.hid in self.discussed:
                continue
            self.discussed.add(h.hid)
            turns += 1
            self.state(h)
            self.refute(h)
            self.implies(h)
            self.connect(h)
            new = self.next_step(h)
            queue = new + queue  # follow the thread the action opened
        return self.turns

    # -- report -------------------------------------------------------------------------------
    def markdown(self, title: str) -> str:
        lines = [f"## {title}", ""]
        cur = None
        for t in self.turns:
            if t["hyp"] != cur:
                cur = t["hyp"]
                lines.append("")
            flag = f" **UNGROUNDED {t['ungrounded_numbers']}**" if t["ungrounded_numbers"] else ""
            lines.append(f"* *{t['kind']}* — {t['text']} `[{t['provenance']}]`{flag}")
        return "\n".join(lines) + "\n"
