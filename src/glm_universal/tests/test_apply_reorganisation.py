"""``scripts/apply_reorganisation.sh`` never deletes content it does not know.

Created 31 October 2026 (repository check).
Last altered 31 October 2026: the superseded copies of the held-back wheels;
then, the wheels installed back in the package provisionally (the owner's
decision), the copies their staged folders left -- and no live wheel file is
ever listed for removal.
Last altered 1 November 2026 (Phase 186): two items filed in ``done/`` --
their moves end there, the bundle's ``done/`` files are live and no longer
listed for removal (17 superseded paths, not 31), and an empty file at a
move's new place (a retracted placeholder) is replaced by the old copy.

The script brings an older checkout to the tree of the repository check: it
moves files, removes old copies and removes the twelve placeholder Lean files
the check deleted.  A removal is the one irreversible thing it does, so every
removal is decided by exact content:

* a placeholder is deleted only when it is byte for byte the placeholder that
  was deleted (its SHA-256 is written beside its path); a file at that path
  with any other content -- a recovered Lean file with ``public theorem``,
  ``private def`` or anything else -- is kept and reported;
* an old copy of a moved file is removed only when it is byte for byte the new
  file or the file as it stood before the reorganisation; any other old copy is
  kept beside the new one and reported as a conflict, and the script exits 1.

Each case is run on a scratch copy of the script in a temporary directory, so
the real tree is never touched.  The script is skipped, with the reason, where
``bash`` or a SHA-256 tool is not installed.
"""

from __future__ import annotations

import hashlib
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from glm_universal.signoff import ledger as L

REPOSITORY_ROOT = Path(L.REPOSITORY_ROOT)
SCRIPT = REPOSITORY_ROOT / "scripts" / "apply_reorganisation.sh"

_HAVE_TOOLS = shutil.which("bash") is not None and (
    shutil.which("sha256sum") is not None or shutil.which("shasum") is not None)

pytestmark = [pytest.mark.skipif(not _HAVE_TOOLS,
                                 reason="bash and sha256sum/shasum are needed")]

_HASH = re.compile(r"^[0-9a-f]{64}$")


def _known():
    """The script's (path, [hash, ...]) removals of superseded copies."""
    out = []
    for line in SCRIPT.read_text(encoding="utf-8").splitlines():
        if line.startswith("rm_known "):
            words = shlex.split(line)
            assert len(words) >= 3 and all(_HASH.match(w) for w in words[2:]), line
            out.append((words[1], words[2:]))
    return out


def _entries():
    """The script's (path, hash) removals and (old, new, hash) moves."""
    removals, moves = [], []
    for line in SCRIPT.read_text(encoding="utf-8").splitlines():
        if line.startswith("rm_one "):
            words = shlex.split(line)
            assert len(words) == 3 and _HASH.match(words[2]), line
            removals.append((words[1], words[2]))
        elif line.startswith("mv_one "):
            words = shlex.split(line)
            assert len(words) == 4 and _HASH.match(words[3]), line
            moves.append((words[1], words[2], words[3]))
    return removals, moves


def _run(root: Path, *args: str):
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(SCRIPT, root / "scripts" / SCRIPT.name)
    p = subprocess.run(["bash", str(root / "scripts" / SCRIPT.name), *args],
                       capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestTheList:

    def test_every_removal_and_move_carries_a_content_hash(self):
        removals, moves = _entries()
        text = SCRIPT.read_text(encoding="utf-8")
        assert len(removals) == text.count("\nrm_one ")
        assert len(moves) == text.count("\nmv_one ")
        assert removals and moves

    def test_no_path_is_both_removed_and_a_move_target(self):
        removals, moves = _entries()
        targets = {new for _, new, _ in moves}
        assert not targets & {path for path, _ in removals}


class TestRemovalsKeepUnknownContent:

    def test_a_recovered_lean_file_at_a_deleted_path_is_kept(self, tmp_path):
        removals, _ = _entries()
        rel = removals[0][0]
        for body in ("public theorem recovered : True := trivial\n",
                     "private def kept : Nat := 1\n",
                     "noncomputable def also : Nat := 2\n"):
            path = _write(tmp_path, rel, "import Mathlib\n" + body)
            code, out = _run(tmp_path)
            assert path.is_file(), body
            assert path.read_text(encoding="utf-8").endswith(body)
            assert "kept (not the deleted placeholder" in out
            assert code == 1

    def test_the_known_placeholder_hash_is_what_decides(self, tmp_path):
        removals, _ = _entries()
        rel, digest = removals[0]
        path = _write(tmp_path, rel, "-- anything at all\n")
        assert hashlib.sha256(path.read_bytes()).hexdigest() != digest
        _run(tmp_path)
        assert path.is_file()


class TestMoves:

    def test_a_lone_old_file_is_moved(self, tmp_path):
        _, moves = _entries()
        old, new, _ = moves[0]
        _write(tmp_path, old, "the old text\n")
        _run(tmp_path)
        assert not (tmp_path / old).exists()
        assert (tmp_path / new).read_text(encoding="utf-8") == "the old text\n"

    def test_an_old_copy_equal_to_the_new_file_is_removed(self, tmp_path):
        _, moves = _entries()
        old, new, _ = moves[0]
        _write(tmp_path, old, "same\n")
        _write(tmp_path, new, "same\n")
        _, out = _run(tmp_path)
        assert not (tmp_path / old).exists()
        assert (tmp_path / new).is_file()
        assert "conflict, both kept" not in out

    def test_a_differing_old_copy_is_kept_beside_the_new_file(self, tmp_path):
        _, moves = _entries()
        old, new, _ = moves[0]
        _write(tmp_path, old, "an edit made in the older checkout\n")
        _write(tmp_path, new, "the delivered file\n")
        code, out = _run(tmp_path)
        assert (tmp_path / old).read_text(encoding="utf-8") == \
            "an edit made in the older checkout\n"
        assert (tmp_path / new).read_text(encoding="utf-8") == \
            "the delivered file\n"
        assert "conflict, both kept" in out and old in out
        assert code == 1

    def test_an_empty_placeholder_at_the_new_place_is_replaced(self, tmp_path):
        _, moves = _entries()
        old, new, _ = moves[0]
        _write(tmp_path, old, "the old text\n")
        _write(tmp_path, new, "")
        code, out = _run(tmp_path)
        assert not (tmp_path / old).exists()
        assert (tmp_path / new).read_text(encoding="utf-8") == "the old text\n"
        assert "conflict, both kept" not in out

    def test_a_todo_copy_of_an_item_filed_in_done_is_removed(self, tmp_path):
        _, moves = _entries()
        old, new, digest = next(m for m in moves if m[0].startswith("source_material/ToDo/")
                                and m[1].startswith("source_material/done/"))
        live = REPOSITORY_ROOT / new
        assert live.is_file() and hashlib.sha256(live.read_bytes()).hexdigest() == digest
        (tmp_path / old).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / new).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(live, tmp_path / old)
        shutil.copy(live, tmp_path / new)
        _run(tmp_path)
        assert not (tmp_path / old).exists() and (tmp_path / new).is_file()

    def test_dry_run_changes_nothing(self, tmp_path):
        _, moves = _entries()
        old, new, _ = moves[0]
        _write(tmp_path, old, "x\n")
        _, out = _run(tmp_path, "--dry-run")
        assert (tmp_path / old).is_file() and not (tmp_path / new).exists()
        assert f"move: {old} -> {new}" in out


class TestSupersededCopies:
    """The paths the new wheels left (``rm_known``): removed only when empty (a
    retracted file) or byte for byte a version delivered there."""

    def test_every_entry_lists_the_empty_file_first(self):
        known = _known()
        assert len(known) == 17
        empty = hashlib.sha256(b"").hexdigest()
        assert all(hashes[0] == empty and len(hashes) >= 2 for _, hashes in known)

    def test_no_live_file_is_listed(self):
        # The wheels are back in the package (provisionally): nothing below
        # src/ may be removed, and every listed path is absent from the tree.
        for path, _ in _known():
            assert not path.startswith("src/"), path
            assert not (REPOSITORY_ROOT / path).exists(), path
        live = REPOSITORY_ROOT / "src" / "glm_universal" / "wheels" / "integer_wheel.py"
        assert live.is_file()

    def test_an_empty_file_is_removed_and_an_edited_one_kept(self, tmp_path):
        known = _known()
        wheel = next(p for p, _ in known if p.endswith("staged/src/glm_universal/wheels/integer_wheel.py"))
        test = next(p for p, _ in known if p.endswith("staged/src/glm_universal/tests/test_cent_wheels.py"))
        _write(tmp_path, wheel, "")
        _write(tmp_path, test, "# an edit made by hand\n")
        code, out = _run(tmp_path)
        assert not (tmp_path / wheel).exists()
        assert (tmp_path / test).read_text(encoding="utf-8") == "# an edit made by hand\n"
        assert "kept (not a version this check delivered" in out and test in out
        assert code == 1

    def test_a_delivered_staged_copy_is_removed(self, tmp_path):
        # The staged copy of oeis_seed.py was delivered byte for byte as the
        # module now standing in the package.
        live = REPOSITORY_ROOT / "src" / "glm_universal" / "wheels" / "oeis_seed.py"
        rel = "source_material/ToDo/glm_wheels_bundle/staged/src/glm_universal/wheels/oeis_seed.py"
        if hashlib.sha256(live.read_bytes()).hexdigest() not in dict(_known())[rel]:
            pytest.skip("the live module has changed since its staged copy was delivered")
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(live, tmp_path / rel)
        _run(tmp_path)
        assert not (tmp_path / rel).exists()
