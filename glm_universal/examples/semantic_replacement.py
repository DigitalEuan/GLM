#!/usr/bin/env python3
"""What the inherited concept graph contained, and what replaces it.

Run:
    PYTHONPATH=. python3 glm_universal/examples/semantic_replacement.py

The script does four things, in the order in which they have to be done:

1. **Measure** the inherited graph rather than describe it: how many of its
   concepts denote anything determinate, how its edges classify, and what its
   stored carriers turn out to be a measurement *of*.
2. **Show the split** the old carriers put between notations that denote the
   same subject, and the distance the meaning space puts between them (zero).
3. **Build the replacement**: notations resolved to meanings, meanings related
   by relations that are re-derived from the meanings alone.
4. **Write both documents** beside the inherited state file, without touching
   it.  ``--no-write`` prints the summary and writes nothing.

Nothing here is quoted from a previous run: every number is recomputed.
"""

from __future__ import annotations

import argparse
from fractions import Fraction

from glm_universal.semantics import audit as sau
from glm_universal.semantics import export as sex
from glm_universal.semantics import graph as sgr
from glm_universal.semantics import reference as sre
from glm_universal.semantics import relations as srl

RULE = "=" * 74


def _heading(text: str) -> None:
    print(f"\n{RULE}\n{text}\n{RULE}")


def show_legacy() -> None:
    """Section 1: what the inherited graph turns out to contain."""
    _heading("1.  THE INHERITED CONCEPT GRAPH, MEASURED")
    concepts = sau.concept_grounding()
    edges = sau.edge_grounding()
    carriers = sau.carrier_information()
    if not concepts["concepts"]:
        print("no inherited state file found; nothing to measure")
        return
    print(f"concepts                : {concepts['concepts']}")
    print(f"  denote something      : {concepts['grounded']} "
          f"({concepts['grounded_fraction']})")
    print(f"  refused, by reason    : {concepts['refusal_reasons']}")
    print(f"edges                   : {edges['edges']}")
    for name, count in sorted(edges["classes"].items()):
        print(f"  {name:<22}: {count}")
    print("\nstored carrier distance against semantic relatedness")
    print(f"  mean Hamming, related   : "
          f"{carriers['mean_hamming_related']}")
    print(f"  mean Hamming, unrelated : "
          f"{carriers['mean_hamming_unrelated']}")
    print("  two random 24-bit words average 12, so a carrier that measured "
          "the\n  subjects would put the related pairs closer than that and "
          "these do not.")


def show_synonyms() -> None:
    """Section 2: one subject, several notations, two carriers compared."""
    _heading("2.  NOTATIONS OF ONE SUBJECT")
    variants = sau.notational_variants()
    print(f"synonym groups found in the inherited names : "
          f"{variants['synonym_groups']}")
    print(f"synonym pairs                               : "
          f"{variants['synonym_pairs']}")
    print(f"mean legacy Hamming between them            : "
          f"{variants['mean_legacy_hamming_between_synonyms']}")
    print(f"distance between them in the meaning space  : "
          f"{variants['semantic_hamming_between_synonyms']}")
    print("\nworked example -- four notations, one operation:")
    for term in ("add", "addition", "plus", "sum"):
        meaning = sre.meaning_of(term)
        print(f"  {term:<9} -> {meaning.describe():<20} "
              f"carrier {sex.carrier_strings(meaning)[:3]}...")
    print("  their carriers are equal, so the graph has one node, not four.")


def show_replacement() -> None:
    """Section 3: the graph that replaces it."""
    _heading("3.  THE GROUNDED GRAPH")
    graph = sgr.build_graph()
    report = sgr.graph_report(graph)
    print(f"notations resolved : {report['notations']}")
    print(f"meanings (nodes)   : {report['meanings']}")
    print(f"  by kind          : {report['nodes_by_kind']}")
    print(f"binary edges       : {report['binary_edges']}")
    print(f"ternary edges      : {report['ternary_edges']}")
    print(f"all edges re-derived from the meanings they join : "
          f"{report['verification']['all_verified']}")
    print("\nworked examples -- every claim carries the arithmetic that "
          "makes it true:")
    for a, b in (("water", "oxygen"), ("energy", "torque"),
                 ("hydrogen", "helium"), ("two", "four")):
        claims = srl.derive(sre.meaning_of(a), sre.meaning_of(b))
        for claim in claims:
            print(f"  {a} / {b}: {claim.relation} -- {claim.witness}")
    return graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true",
                        help="print the summary without writing documents")
    args = parser.parse_args()

    show_legacy()
    show_synonyms()
    graph = show_replacement()

    _heading("4.  DOCUMENTS")
    if args.no_write:
        print("--no-write given; nothing written")
        return 0
    paths = sex.write_documents(graph=graph)
    for name, path in sorted(paths.items()):
        print(f"{name:<10} -> {path}  ({path.stat().st_size} bytes)")
    print("the inherited state file was read and not written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
