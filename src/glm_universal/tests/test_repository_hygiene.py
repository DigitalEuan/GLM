"""Repository hygiene: derived caches stay out of version control.

On 22 October 2026 pushes began to fail: the git server rejected them as too
large.  The cause was the counted-knowledge cache
(``knowledge/_knowledge_cache/knowledge.pickle``, about 135 MB), which was
tracked by git and rewritten whenever any corpus file moved, so every round
committed another full copy.  It was untracked and listed in ``.gitignore``.

Three things are pinned here so that it cannot happen again unnoticed.

* **Nothing in the cache directory is tracked**, and every file the cache
  writes is ignored by git -- the knowledge model and both word-address books.
* **No tracked file is larger than** :data:`MAX_TRACKED_BYTES`.  The largest
  tracked file is a few megabytes of JSON; a file past the bound is almost
  certainly a derived artefact that belongs beside the cache instead.
* **An absent cache is rebuilt, not an error.**  A clone starts without the
  cache; :func:`glm_universal.knowledge.model.load` counts the corpus, writes
  the cache, and the next load answers from it without re-reading a file.
  Checked on a three-document corpus in a temporary directory, so the test
  costs a fraction of a second and never touches the real cache.

The git checks are skipped, with the reason, when the tree is not a git
checkout or git is not installed.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import word_address as wa
from glm_universal.signoff import ledger as L

REPOSITORY_ROOT = Path(L.REPOSITORY_ROOT)

#: The bound on a tracked file.  The git server's rejection came from a
#: 135 MB file; the largest legitimately tracked file is under 6 MB.
MAX_TRACKED_BYTES = 10 * 1024 * 1024


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPOSITORY_ROOT, capture_output=True,
                          text=True, check=False)


def _require_git() -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    if _git("rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        pytest.skip("not a git checkout")


def _cache_relative(name: str) -> str:
    path = mdl.DEFAULT_CACHE_DIRECTORY / name
    return path.relative_to(REPOSITORY_ROOT).as_posix()


# ===========================================================================
# 1.  THE CACHE IS NOT VERSION CONTROLLED
# ===========================================================================

CACHE_FILES = (mdl.CACHE_FILE, "word_addresses_window.pickle",
               "word_addresses_positional.pickle")


def test_word_address_books_live_in_the_cache_directory():
    for scheme in ("window", "positional"):
        assert wa._cache_path(scheme).parent == mdl.CACHE_DIRECTORY
        assert wa._cache_path(scheme).name in CACHE_FILES


def test_nothing_in_the_cache_directory_is_tracked():
    _require_git()
    directory = mdl.DEFAULT_CACHE_DIRECTORY.relative_to(REPOSITORY_ROOT).as_posix()
    tracked = _git("ls-files", "--", directory).stdout.split()
    assert tracked == [], f"tracked derived cache files: {tracked}"


@pytest.mark.parametrize("name", CACHE_FILES)
def test_every_cache_file_is_ignored(name):
    _require_git()
    # ``--no-index`` asks about the ignore rules alone, whether or not the
    # file exists in this checkout.
    result = _git("check-ignore", "--no-index", "-q", _cache_relative(name))
    assert result.returncode == 0, f"{name} is not ignored by .gitignore"


def test_no_tracked_file_exceeds_the_bound():
    _require_git()
    oversized = []
    for relative in _git("ls-files", "-z").stdout.split("\0"):
        if not relative:
            continue
        path = REPOSITORY_ROOT / relative
        if path.is_file() and path.stat().st_size > MAX_TRACKED_BYTES:
            oversized.append((relative, path.stat().st_size))
    assert oversized == [], (
        f"tracked files over {MAX_TRACKED_BYTES} bytes (a derived artefact? "
        f"add it to .gitignore and rebuild it on demand): {oversized}")


# ===========================================================================
# 2.  AN ABSENT CACHE IS REBUILT
# ===========================================================================

TINY_CORPUS = {
    "studies/A.md": b"The golay code corrects three errors in every word.\n\n"
                    b"A syndrome names the error pattern of a received word.\n",
    "studies/B.md": b"The leech lattice is built from the golay code.\n\n"
                    b"Every syndrome is read by the decoder in exact arithmetic.\n",
    "notes/C.txt": b"The decoder reads the golay code and names the syndrome.\n",
}


@pytest.fixture
def tiny(monkeypatch, tmp_path):
    corpus = dict(TINY_CORPUS)
    monkeypatch.setattr(mdl.rd, "iter_sources",
                        lambda root=None: iter(sorted(corpus.items())))
    monkeypatch.setattr(mdl, "CACHE_DIRECTORY", tmp_path / "cache")
    monkeypatch.setattr(mdl, "_LOADED", {})
    return corpus, tmp_path / "cache" / mdl.CACHE_FILE


def test_an_absent_cache_is_counted_and_written(tiny):
    _, path = tiny
    assert not path.exists()
    assert mdl.cache_state()["present"] is False
    knowledge = mdl.load()
    assert path.exists()
    assert knowledge.reread == len(TINY_CORPUS)
    assert mdl.cache_state()["present"] is True
    assert mdl.cache_state()["bytes"] == path.stat().st_size


def test_the_rebuilt_cache_equals_a_fresh_count(tiny):
    knowledge = mdl.load()
    fresh = mdl.build(knowledge.documents, knowledge.digest)
    assert knowledge.model == fresh.model
    assert knowledge.contexts == fresh.contexts
    assert knowledge.postings == fresh.postings


def test_the_second_load_reads_no_file(tiny):
    first = mdl.load()
    mdl._LOADED.clear()
    second = mdl.load()
    assert second.reread == 0
    assert second.digest == first.digest
    assert second.model == first.model


def test_a_changed_file_is_the_only_file_read_again(tiny):
    corpus, _ = tiny
    mdl.load()
    mdl._LOADED.clear()
    corpus["notes/C.txt"] = b"The decoder reads the leech lattice and names the shell.\n"
    again = mdl.load()
    assert again.reread == 1


def test_a_deleted_cache_is_rebuilt_to_the_same_knowledge(tiny):
    _, path = tiny
    first = mdl.load()
    path.unlink()
    mdl._LOADED.clear()
    again = mdl.load()
    assert path.exists()
    assert again.reread == len(TINY_CORPUS)
    assert again.digest == first.digest
    assert again.model == first.model


def test_a_corrupt_cache_is_rebuilt(tiny):
    _, path = tiny
    first = mdl.load()
    path.write_bytes(b"not a pickle")
    mdl._LOADED.clear()
    again = mdl.load()
    assert again.digest == first.digest
    assert again.reread == len(TINY_CORPUS)


def test_the_cold_start_notice_never_reaches_captured_output(tiny, capsys):
    mdl.load()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_the_cache_directory_may_be_relocated(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    assert mdl.cache_directory({mdl.CACHE_ENVIRONMENT: str(elsewhere)}) == elsewhere.resolve()
    assert mdl.cache_directory({}) == mdl.DEFAULT_CACHE_DIRECTORY
    assert mdl.cache_directory({mdl.CACHE_ENVIRONMENT: ""}) == mdl.DEFAULT_CACHE_DIRECTORY


def test_a_relocated_cache_reports_itself(tiny):
    assert mdl.cache_state()["relocated"] is True
