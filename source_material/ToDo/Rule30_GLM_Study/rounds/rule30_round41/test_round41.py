#!/usr/bin/env python3
"""Round 41 tests (about 15 s): python3 test_round41.py"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from glm_dialogue import Guard, Knowledge, numbers_in  # noqa: E402
import run_round41 as r41  # noqa: E402


def test_numbers_and_guard():
    assert numbers_in("found nothing below D=400,000; next at D >= 275 million") == \
        [400000, 275000000]
    assert numbers_in("k = 40, 12 and 7") == []           # fewer than 3 digits: not checked
    g = Guard({53207})
    g.note(87867)
    assert g.ungrounded("whites at 53207 and 87867, and 275 million") == [275000000]


def test_knowledge_edges_are_backed():
    k = Knowledge.load(HERE / "knowledge.json")
    for e in k.edges:
        assert e.verdict in ("follows", "equivalent", "does-not-follow"), e
        assert e.backing.startswith(("lean:", "ledger:")) or e.backing == "definition", e
    # the two v10 implications that do not follow are recorded as such
    bad = {e.premise for e in k.edges if e.verdict == "does-not-follow"}
    assert {"rule30.transient_at_read", "rule30.centre_aperiodic"} <= bad


def test_rule30_dialogue_rediscovers_laws():
    core, d = r41.rule30(budget=65536)
    white = next(h for h in core.hyps if h.meta.get("key") == "white" and h.origin == "lift")
    assert white.status == "refuted-heldout" and white.witness == 53207
    lp = next(h for h in core.hyps if h.meta.get("key") == "lp" and h.origin == "lift"
              and h.meta["kind"] == "divides")
    assert lp.status == "refuted-heldout" and lp.witness == 400
    laws = {" ∧ ".join(h.meta["conj"]): h.status for h in core.hyps if "conj" in h.meta}
    assert laws.get("pattern(D-2) = pattern(D-1)") == "law-holds"       # the white criterion
    assert laws.get("white(D-1) ∧ odd(D-2)") == "law-holds"             # the doubling law
    assert laws.get("white(D-1)") == "refuted-heldout"                  # split at 53208
    assert all(not t["ungrounded_numbers"] for t in d.turns)
    assert any("does NOT by itself imply" in t["text"] and "Problem 1" in t["text"]
               for t in d.turns)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
