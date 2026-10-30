"""``glm_universal.corpus`` -- the project's own prose, held the way its data is.

The problem this sub-package solves is the one the repository created for
itself by measuring everything it claims: there are now dozens of documents,
and no session can read them all.  The conventional answer is an index, and an
index is exactly the artefact this project spends its time eliminating -- a
stored table, maintained by hand, drifting from what it describes.

So the corpus is treated as the substrate treats anything else.

``inventory``
    The documents as objects, enumerated by a rule, split into *state* and
    *archive* by their paths, and reduced to a digest.

``render``
    What can be emitted is emitted: ``DIGEST.md`` in full, and any section of
    any document that is a measurement rather than an argument, marked
    ``<!-- generated: NAME -->`` and rewritten by the function that measures it.

``checks``
    The three claims made about the prose, as tests: the tier contract (a
    truncated read is coarse, never wrong), the archive rule, and the coverage
    claim of ``ENTRY.md``.

``address``
    A Leech address for every section, so "what in this project bears on X?"
    is answered by a shortlist that is complete up to a stated radius -- and an
    empty shortlist is a proof that the corpus holds nothing within it.  The
    completeness bound is the one already proved in
    ``RequestProject/GLM/Retrieval.lean``; extending it from declarations to
    documents costs one feature map and no new principle.

``report``
    The whole measurement in one payload, which is what the study and the
    generated blocks are rendered from.

Command line::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.corpus            # report
    PYTHONPATH=. python3 -m glm_universal.corpus --check    # fail if stale
    PYTHONPATH=. python3 -m glm_universal.corpus --write    # regenerate
    PYTHONPATH=. python3 -m glm_universal.corpus --ask "..."  # certified shortlist
"""

from __future__ import annotations

__all__ = ["inventory", "render", "checks", "address", "report",
           "corpus_report"]

from . import inventory  # noqa: E402
from . import render  # noqa: E402
from . import checks  # noqa: E402
from . import address  # noqa: E402
from . import report  # noqa: E402

from .report import corpus_report  # noqa: E402
