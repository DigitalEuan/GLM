"""``glm_universal.semantics`` -- meaning as the thing that gets encoded.

The proposition
---------------
What a subject *is* can be recorded exactly; what a subject is *called* can
only be recorded exactly as a string.  Every layer of this repository already
honours that for physics and chemistry -- a quantity is its EXT10 exponent
vector, an element is its atomic number -- and it is honoured nowhere for
words.  This package closes the gap: a word is admitted only when it denotes
something determinate, and then it is encoded *as that thing*.

Four modules
------------
=================  ==========================================================
:mod:`.meaning`    the meaning space: six kinds of determinate content, and
                   an injective 24-coordinate carrier with an exact round
                   trip.  ``encode`` takes a meaning and nothing else, so a
                   spelling cannot reach the carrier
:mod:`.reference`  notation -> meaning, or a refusal with a reason: numerals,
                   number words, Roman numerals, arithmetic, SI defining
                   constants, elements, formulae, named species, the 726
                   register quantities, operator signs
:mod:`.relations`  relations *derived* from meanings and re-checkable from
                   them, each with the arithmetic that makes it true
:mod:`.graph`      the grounded graph: nodes are meanings, notations hang off
                   them, edges are derivations, and every edge is re-derived
                   on demand
:mod:`.audit`      what the inherited concept graph turns out to contain,
                   measured rather than asserted, and what to dump
:mod:`.export`     the graph and the purge plan written out as documents,
                   beside the inherited state file and never over it
=================  ==========================================================

The result in one line
----------------------
``"water"``, ``"H2O"`` and ``"dihydrogen monoxide"`` are one node; ``"two"``,
``"2"``, ``"4/2"`` and ``"1+1"`` are one node; ``"energy"``,
``"work"`` and ``"heat"`` are one node -- and ``"beautiful"`` is not a node at
all, because the repository cannot say what it would be a node *of*.
"""

from __future__ import annotations

from . import audit, export, graph, meaning, reference, relations  # noqa: F401
from .export import graph_document, purge_document, write_documents
from .graph import SemanticGraph, build_graph, graph_report
from .meaning import Meaning, MeaningCodec, decode, encode
from .reference import Resolution, meaning_of, resolve
from .relations import Claim, derive, derive_ternary, verify

__all__ = [
    "meaning", "reference", "relations", "graph", "audit", "export",
    "graph_document", "purge_document", "write_documents",
    "Meaning", "MeaningCodec", "encode", "decode",
    "Resolution", "resolve", "meaning_of",
    "Claim", "derive", "derive_ternary", "verify",
    "SemanticGraph", "build_graph", "graph_report",
]
