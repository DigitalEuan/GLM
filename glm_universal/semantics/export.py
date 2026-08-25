"""Writing the grounded graph out, and writing the purge down.

Why this module exists
----------------------
The audit in :mod:`.audit` measures what the inherited concept graph
contains; :mod:`.graph` builds the graph that replaces it.  Neither writes
anything to disk, because a measurement that quietly rewrites its subject is
not a measurement.  This module does the writing, and it does it under two
rules:

* **Nothing inherited is edited.**  ``glm_state.json`` is read and never
  written.  The purge is expressed as a *document* -- which edges survive an
  audit, which do not, and the reason for each -- rather than as a mutation.
  A dump you can read is a result; a dump you cannot see is data loss.
* **Everything written is reconstructible.**  Every document carries the
  provenance needed to rebuild it from the registers alone: no document is a
  source of truth, all of them are views.

The two documents
-----------------
``semantic_graph.json``
    The replacement: meanings, their exact 24-coordinate carriers, the
    notations that denote each one, and every derived relation with the
    arithmetic that re-checks it.

``semantic_purge_plan.json``
    The audit of the inherited graph: how many of its concepts denote
    anything, how its edges classify, what the stored carriers turn out to
    measure, and -- edge by edge for the survivors -- what is kept.

Both are exact: every rational is written as ``"n/d"``, never as a float.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import audit as sau
from .graph import SemanticGraph, build_graph, graph_report
from .meaning import Meaning, encode

__all__ = [
    "carrier_strings", "meaning_document", "graph_document",
    "purge_document", "write_documents", "DEFAULT_RESULTS",
]

#: Where the ARC-era pipeline kept its state, and where these documents go
#: beside it -- beside, not over.
DEFAULT_RESULTS = (Path(__file__).resolve().parents[2]
                   / "arc_agi_17" / "results")


def carrier_strings(meaning: Meaning) -> List[str]:
    """The 24 coordinates as exact ``"n/d"`` strings."""
    out: List[str] = []
    for coordinate in encode(meaning):
        value = Fraction(coordinate)
        out.append(f"{value.numerator}/{value.denominator}")
    return out


def meaning_document(meaning: Meaning,
                     notations: Sequence[str] = ()) -> Dict[str, object]:
    """One node: what it is, what it is called, and its exact carrier."""
    document = dict(meaning.as_dict())
    document["carrier"] = carrier_strings(meaning)
    document["notations"] = list(notations)
    return document


def graph_document(graph: Optional[SemanticGraph] = None) -> Dict[str, object]:
    """The replacement graph, in full, as a JSON-serialisable document."""
    graph = graph if graph is not None else build_graph()
    report = graph_report(graph)
    return {
        "kind": "glm.semantics.graph",
        "provenance": {
            "built_by": "glm_universal.semantics.graph.build_graph",
            "sources": ["glm_universal/data_objects/_data",
                        "glm_universal/reasoning/_data"],
            "notation_free_carriers": True,
            "rebuildable": "every field here is recomputed by build_graph()",
        },
        "counts": {key: report[key] for key in
                   ("notations", "meanings", "refused_terms", "binary_edges",
                    "ternary_edges", "isolated_meanings",
                    "collapsed_meanings")},
        "nodes_by_kind": report["nodes_by_kind"],
        "edges_by_relation": report["edges_by_relation"],
        "verification": report["verification"],
        "nodes": [meaning_document(m, graph.names_for(m))
                  for m in graph.meanings],
        "binary_edges": [claim.as_dict() for claim in graph.binary],
        "ternary_edges": [claim.as_dict() for claim in graph.ternary],
        "refused": [{"term": r.term, "reason": r.reason}
                    for r in graph.refused],
    }


def purge_document() -> Dict[str, object]:
    """The audit of the inherited graph and the plan that follows from it."""
    plan = sau.purge_plan()
    report = sau.audit_report()
    return {
        "kind": "glm.semantics.purge_plan",
        "provenance": {
            "measured_by": "glm_universal.semantics.audit.audit_report",
            "reads": "arc_agi_17/results/glm_state.json",
            "writes_to_that_file": False,
        },
        "concept_grounding": report["concept_grounding"],
        "edge_grounding": report["edge_grounding"],
        "carrier_information": report["carrier_information"],
        "notational_variants": report["notational_variants"],
        "plan": {
            "edges": plan["edges"],
            "retained": plan["retained"],
            "dumped": plan["dumped"],
            "dumped_by_reason": plan["dumped_by_reason"],
            "reasons": plan["reasons"],
            "retained_edges": plan["retained_edges"],
        },
        "replacement": report["replacement"],
    }


def write_documents(directory: Optional[Path] = None,
                    graph: Optional[SemanticGraph] = None
                    ) -> Dict[str, Path]:
    """Write both documents beside the inherited state, and return the paths.

    The inherited state file is not touched.
    """
    target = Path(directory) if directory is not None else DEFAULT_RESULTS
    target.mkdir(parents=True, exist_ok=True)
    paths = {
        "graph": target / "semantic_graph.json",
        "purge_plan": target / "semantic_purge_plan.json",
    }
    paths["graph"].write_text(
        json.dumps(graph_document(graph), indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    paths["purge_plan"].write_text(
        json.dumps(purge_document(), indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    return paths
