"""The Lean-delivery census: what a supplied delivery would add, measured.

*Created 15 November 2026 (platform round, P4 intake; Phase 189).*

These tests hold the census's own contract, not the numbers of one delivery:
the counts move as soon as an item is absorbed, filed in `done/` or edited,
which is exactly what the census is for.  What must not move is that every
supplied file is classified, that a classification is never invented, that the
import count cannot resolve more imports than it counted, and that taking the
census writes nothing.

The study is `studies/LEAN_DELIVERIES_CENSUS_STUDY.md`.
"""
from __future__ import annotations

import pytest

from glm_universal.constants import SOURCE_MATERIAL_DIR
from glm_universal.corpus import lean_deliveries as ld

VERDICTS = {"identical", "name", "new"}


class TestTheCensus:
    def test_every_supplied_file_is_classified(self):
        report = ld.census_report()
        assert report["rows"], "no supplied Lean file was found to classify"
        for row in report["rows"]:
            assert row["verdict"] in VERDICTS, row["path"]
            assert row["declarations"] >= row["decls_already_in_tree"], row["path"]
            assert row["decls_new"] >= 0, row["path"]
            assert row["sorry"] >= 0, row["path"]

    def test_a_byte_identical_copy_names_the_tree_file_it_duplicates(self):
        for row in ld.census_report()["rows"]:
            if row["verdict"] == "identical":
                assert row["identical_to"], row["path"]
            else:
                assert not row["identical_to"], row["path"]

    def test_the_import_count_cannot_resolve_more_than_it_counted(self):
        report = ld.census_report()
        assert 0 <= report["item_local_imports_resolved"] <= report["item_local_imports"]

    def test_the_items_add_up_to_the_rows(self):
        report = ld.census_report()
        for item, stats in report["items"].items():
            rows = [r for r in report["rows"] if r["item"] == item]
            assert stats["files"] == len(rows)
            assert stats["identical"] + stats["same_name"] + stats["new"] == len(rows)

    def test_the_tree_it_reads_is_the_build_tree(self):
        report = ld.census_report()
        assert report["tree_files"] > 400
        assert report["tree_declarations"] > 5000

    def test_taking_the_census_writes_nothing(self):
        before = sorted(p.name for p in SOURCE_MATERIAL_DIR.rglob("*") if p.is_file())
        first = ld.census_report()
        second = ld.census_report()
        after = sorted(p.name for p in SOURCE_MATERIAL_DIR.rglob("*") if p.is_file())
        assert before == after
        assert first["tree_files"] == second["tree_files"]
        assert len(first["rows"]) == len(second["rows"])

    def test_format_report_quotes_the_counts(self):
        report = ld.census_report()
        text = ld.format_report(report)
        assert f"build tree: {report['tree_files']} Lean files" in text
        assert "item-local imports:" in text

    @pytest.mark.parametrize("item", ld.ITEMS)
    def test_the_two_named_items_are_an_item_or_already_filed(self, item):
        report = ld.census_report([item])
        in_todo = (SOURCE_MATERIAL_DIR / "ToDo" / item).is_dir()
        in_done = (SOURCE_MATERIAL_DIR / "done" / item).is_dir()
        assert in_todo or in_done, f"{item} is neither in ToDo/ nor in done/"
        if not in_todo:
            assert item not in report["items"] or report["items"][item]["files"] == 0
