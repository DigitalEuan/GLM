"""Tests for ``glm_universal.corpus.dates`` -- directive D17, the date stamps.

D17: every file a round creates carries a ``Created`` stamp and every file it
alters a ``Last altered`` stamp, in the file itself; generated documents,
stored measurements and everything under ``source_material/`` are exempt.
``python3 -m glm_universal.tools dates`` lists every stamp and fails on a
stamp that is not a date, lies after today, or says a file was altered before
it was made.  These tests pin

* the tree as it is: every stamp a date, none after today, none altered
  before made, and ``tools dates`` returning 0;
* each defect on a synthetic tree with a fixed, injected "today" (so the
  outcome does not depend on the day the suite runs), and ``tools dates``
  returning 1 on it;
* the exemptions: nothing under ``source_material/``, no generated document
  and no stored measurement is read.

The synthetic bad stamps are assembled from pieces at run time, so this file
itself carries no defective stamp for the tree check to find.

*Created 31 October 2026 (repository check: the test file D17 names was
missing; rebuilt with the reconstructed instrument).*
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from glm_universal.corpus import dates as dts
from glm_universal import tools

#: The fixed day the synthetic checks are made on.
TODAY = datetime.date(2026, 10, 31)

#: The two keywords, assembled so this file holds no literal bad stamp.
CREATED = "Crea" + "ted"
ALTERED = "Last" + " altered"


def _tree(tmp_path: Path, files: dict) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------
# the parser
# --------------------------------------------------------------------------

def test_a_date_is_read_in_the_rules_form_only():
    assert dts.parse_date("31 October 2026") == TODAY
    assert dts.parse_date("1 January 2027") == datetime.date(2027, 1, 1)
    for bad in ("31 Octember 2026", "30 February 2026", "2026-10-31",
                "October 31 2026", "31 october 2026", "32 October 2026"):
        assert dts.parse_date(bad) is None, bad
    assert dts.format_date(TODAY) == "31 October 2026"


def test_stamps_are_found_with_their_kind_and_line():
    text = "\n".join([
        "x",
        f"*{CREATED} 20 October 2026.*",
        f"{ALTERED} 29 October 2026 (Phase 172).",
        "last_" + "altered: 23 October 2026",
        "the marks were pre-registered 21 October 2026 and measured "
        "22 October 2026",
        f"{CREATED} <day Month year> is the form, not a stamp",
    ])
    got = dts.stamps_in_text("f.md", text)
    rows = [(s.line, s.kind, s.text) for s in got]
    assert (2, "created", "20 October 2026") in rows
    assert (3, "last altered", "29 October 2026") in rows
    assert (4, "last altered", "23 October 2026") in rows
    assert (5, "pre-registered", "21 October 2026") in rows
    assert (5, "measured", "22 October 2026") in rows
    assert all(line != 6 for line, _, _ in rows)
    assert all(s.date is not None for s in got)


# --------------------------------------------------------------------------
# the tree as it is
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tree_report():
    return dts.dates_report()


def test_every_stamp_of_the_tree_is_a_date(tree_report):
    bad = [d for d in tree_report["defects"] if d["reason"] == "not a date"]
    assert not bad, bad
    assert tree_report["stamps"] > 0 and tree_report["stamped"] > 0


def test_no_stamp_of_the_tree_lies_after_today(tree_report):
    # "today" for the tree is the day of the run (a stamp written today is
    # never a defect); the after-today rule itself is pinned with a fixed day
    # on the synthetic tree below.
    bad = [d for d in tree_report["defects"] if d["reason"] == "after today"]
    assert not bad, bad


def test_no_file_of_the_tree_is_altered_before_it_was_made(tree_report):
    bad = [d for d in tree_report["defects"]
           if str(d["reason"]).startswith("altered before")]
    assert not bad, bad
    assert tree_report["sound"], tree_report["defects"]


def test_the_exempt_places_are_not_read():
    paths = dts.checked_paths()
    assert paths
    assert not any(p.startswith("source_material/") for p in paths)
    assert "DIGEST.md" not in paths and "FIGURES.md" not in paths
    assert not any("/_data/" in p or p.endswith((".json", ".csv"))
                   for p in paths)
    assert "src/glm_universal/corpus/dates.py" in paths


def test_tools_dates_returns_0_on_the_tree(capsys):
    assert tools.run(["dates", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["sound"] is True
    assert tools.run(["dates"]) == 0


# --------------------------------------------------------------------------
# each defect, on a synthetic tree and a fixed day
# --------------------------------------------------------------------------

def test_a_stamp_that_is_not_a_date_fails(tmp_path):
    root = _tree(tmp_path, {
        "a.md": f"{CREATED} 31 Octember 2026\n",
        "b.py": f"# {ALTERED} 30 February 2026\n",
        "c.yaml": f"{CREATED} 2026-10-31\n",
        "ok.md": f"{CREATED} 30 October 2026\n",
    })
    r = dts.dates_report(root=root, today=TODAY)
    assert not r["sound"]
    assert sorted(d["path"] for d in r["defects"]) == ["a.md", "b.py", "c.yaml"]
    assert {d["reason"] for d in r["defects"]} == {"not a date"}


def test_a_stamp_after_today_fails(tmp_path):
    root = _tree(tmp_path, {
        "a.md": f"{CREATED} 1 November 2026\n",
        "b.md": f"{CREATED} 31 October 2026\n",
    })
    r = dts.dates_report(root=root, today=TODAY)
    assert [(d["path"], d["reason"]) for d in r["defects"]] == \
        [("a.md", "after today")]
    later = dts.dates_report(root=root, today=datetime.date(2026, 11, 1))
    assert later["sound"]


def test_altered_before_made_fails(tmp_path):
    root = _tree(tmp_path, {
        "a.md": f"{CREATED} 20 October 2026\n{ALTERED} 19 October 2026\n",
        "b.md": f"{CREATED} 20 October 2026\n{ALTERED} 20 October 2026\n",
    })
    r = dts.dates_report(root=root, today=TODAY)
    assert len(r["defects"]) == 1
    d = r["defects"][0]
    assert d["path"] == "a.md" and d["reason"].startswith("altered before")


def test_source_material_generated_and_stored_files_are_exempt(tmp_path):
    root = _tree(tmp_path, {
        "source_material/x.md": f"{CREATED} 99 October 2026\n",
        "DIGEST.md": f"{CREATED} 99 October 2026\n",
        "FIGURES.md": f"{CREATED} 99 October 2026\n",
        "pkg/_data/m.json": f"\"{CREATED} 99 October 2026\"\n",
        "pkg/_data/notes.md": f"{CREATED} 99 October 2026\n",
        "pkg/m.py": f"# {CREATED} 30 October 2026\n",
    })
    paths = dts.checked_paths(root)
    assert paths == ("pkg/m.py",)
    r = dts.dates_report(root=root, today=TODAY)
    assert r["sound"] and r["stamps"] == 1 and r["files"] == 1


def test_tools_dates_fails_on_a_bad_stamp(tmp_path, monkeypatch, capsys):
    root = _tree(tmp_path, {"a.md": f"{CREATED} 31 Octember 2026\n"})
    monkeypatch.setattr(dts, "REPOSITORY_ROOT", root)
    assert tools.run(["dates"]) == 1
    assert "DEFECT a.md:1" in capsys.readouterr().out
    assert tools.run(["dates", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["sound"] is False and out["defects"][0]["path"] == "a.md"
