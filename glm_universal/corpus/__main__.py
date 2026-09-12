"""Command line for the corpus instruments.

::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.corpus
    PYTHONPATH=. python3 -m glm_universal.corpus --check
    PYTHONPATH=. python3 -m glm_universal.corpus --refresh
    PYTHONPATH=. python3 -m glm_universal.corpus --write
    PYTHONPATH=. python3 -m glm_universal.corpus --remeasure
    PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Golay code?"

``--refresh`` is the one to reach for after a change: it rebuilds the two
address books, then the measurements taken from them, then the generated
documents and blocks -- in that order, which is the only order in which one
pass converges.  Doing it by hand in the wrong order is the mistake the
ordering exists to prevent: measuring before the book is rebuilt produces
figures for the previous tree wearing the current tree's digest, and
:class:`glm_universal.corpus.measurements.StaleAddressBook` now refuses it.

Exit codes: ``0`` if what was asked for holds, ``1`` if a check found a defect
or a generated artefact was stale, ``2`` if the arguments were not understood.
"""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from ..reasoning import lean_address as la
from . import address as ad
from . import checks as ck
from . import inventory as inv
from . import measurements as ms
from . import render as rd
from . import report as rp


def _print_report() -> int:
    data = rp.corpus_report()
    inventory = data["inventory"]
    cost = data["reading_cost"]
    checks = data["checks"]
    print(f"documents          {inventory['documents']} "
          f"({inventory['state_documents']} state, "
          f"{inventory['archive_documents']} archive)")
    print(f"lines              {inventory['lines']:,} "
          f"({inventory['state_lines']:,} state)")
    print(f"tier-0 blocks      {inventory['tier0_present']} of "
          f"{checks['tiers']['state_documents']} state documents")
    print(f"reading cost       {cost['words_tier0']:,} words at tier 0 against "
          f"{cost['words_current_state']:,} for the current state")
    print(f"tier contract      "
          f"{'holds' if checks['tiers']['holds'] else 'FAILS'}")
    print(f"coverage claim     "
          f"{'holds' if checks['reachability']['holds'] else 'FAILS'}")
    print(f"address book       {data['address']['cache']['verdict']}, "
          f"{data['address']['units']} units")
    for path, reason in checks["tiers"]["failures"]:
        print(f"  tier: {path} -- {reason}")
    for path in checks["reachability"]["unreachable"]:
        print(f"  unreachable: {path}")
    for source, target in checks["reachability"]["broken_links"]:
        print(f"  broken link: {source} -> {target}")
    return 0 if data["holds"] else 1


def _refresh(reuse: bool = True) -> int:
    """Every cache and every generated artefact, rebuilt in dependency order.

    The order is forced by what reads what, and each step is skipped when the
    thing it would rebuild is already a description of its inputs:

    1. the **Lean address book**, which the measurements read;
    2. the **document address book**, which the corpus blocks quote;
    3. the **measurements**, which are taken from the Lean book;
    4. the **generated documents and blocks**, which quote all three.

    Nothing later in that list can move anything earlier -- the corpus digest
    is taken over the written text with generated bodies blanked -- so one
    pass is a fixed point, and the check at the end says so rather than
    assuming it.
    """
    lean = la.cache_state()
    if lean["fresh"]:
        print("lean address book:     fresh")
    else:
        report = la.rebuild_address_book(reuse=reuse, audit=16)
        la.address_book(refresh=True)
        audit = report["audit"]
        print(f"lean address book:     rebuilt "
              f"({report['decoded']:,} decoded, {report['reused']:,} reused, "
              f"{audit['audited']} re-decoded as a check, "
              f"{'no drift' if audit['holds'] else 'DRIFT'})")

    document = ad.cache_state()
    if document["fresh"]:
        print("document address book: fresh")
    else:
        report = ad.rebuild_address_book(reuse=reuse, audit=16)
        ad.address_book(refresh=True)
        ad._address_cache.clear()
        audit = report["audit"]
        print(f"document address book: rebuilt "
              f"({report['decoded']:,} decoded, {report['reused']:,} reused, "
              f"{audit['audited']} re-decoded as a check, "
              f"{'no drift' if audit['holds'] else 'DRIFT'})")

    lean_measurements = ms.state()
    if lean_measurements["fresh"]:
        print("measurements:          fresh")
    else:
        try:
            target = ms.write_measurements()
        except ms.StaleAddressBook as refusal:  # pragma: no cover - defensive
            print(f"refused: {refusal}")
            return 1
        ms.measurements(refresh=True)
        print(f"measurements:          rebuilt ({target.name})")

    #  The render pass is repeated until it settles.  One pass is a fixed
    #  point when only values move; adding or removing a *document* is the
    #  case where it is not, because the counts a block quotes include the
    #  document the block is in.  Three passes is the cap: a fourth would mean
    #  something oscillates, and that is a defect to report, not to iterate
    #  around.
    for attempt in range(3):
        outcome = rd.refresh(write=True)
        for path in outcome["documents_written"]:
            print(f"wrote                  {path}")
        for path in outcome["blocks_changed"]:
            print(f"refreshed blocks in    {path}")
        if outcome["current"]:
            if attempt == 0:
                print("generated artefacts:   already current")
            break

    #  And the fixed point, checked rather than asserted.
    settled = rd.refresh(write=False)
    checks = ck.corpus_checks()
    inline = rd.figure_report()
    for path, name in inline["unknown"]:
        print(f"unknown figure:        {name} in {path}")
    for path, name in inline["in_history"]:
        print(f"figure in a record:    {name} in {path}")
    print(f"inline figures         {inline['fresh']} fresh of "
          f"{inline['figures']}")
    ok = (settled["current"] and la.cache_state()["fresh"]
          and ad.cache_state()["fresh"] and ms.state()["fresh"]
          and inline["holds"])
    for path in settled["documents_written"]:
        print(f"still stale:           {path}")
    for path in settled["blocks_changed"]:
        print(f"still stale blocks:    {path}")
    print(f"corpus digest          {inv.corpus_digest()}")
    print(f"document checks        {'hold' if checks['holds'] else 'FAIL'}")
    print("current" if ok and checks["holds"] else "not current")
    return 0 if ok and checks["holds"] else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m glm_universal.corpus",
        description="The project's prose, held the way its data is.")
    parser.add_argument("--write", action="store_true",
                        help="regenerate DIGEST.md, every generated block, "
                             "and the document address book")
    parser.add_argument("--refresh", action="store_true",
                        help="rebuild every cache and every generated "
                             "artefact, in dependency order: address books, "
                             "measurements, documents and blocks")
    parser.add_argument("--force", action="store_true",
                        help="with --remeasure, measure the stored address "
                             "book even when it is stale (normally refused)")
    parser.add_argument("--full", action="store_true",
                        help="with --refresh, decode every address from "
                             "nothing instead of reusing the unchanged ones")
    parser.add_argument("--remeasure", action="store_true",
                        help="re-take the measurements of the formal "
                             "development that the study blocks are emitted "
                             "from (slow: quadratic in the declarations)")
    parser.add_argument("--check", action="store_true",
                        help="fail if any generated artefact is stale or any "
                             "document check does not hold")
    parser.add_argument("--ask", metavar="QUESTION", default=None,
                        help="a certified shortlist of the sections within "
                             "the stated radius of a question")
    parser.add_argument("--radius", type=int, default=2,
                        help="feature radius for --ask (default 2)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of text")
    args = parser.parse_args(argv)

    if args.ask is not None:
        answer = ad.retrieve(args.ask, feature_radius=args.radius)
        if args.json:
            print(json.dumps(answer, indent=2, default=str, sort_keys=True))
            return 0
        certified = answer["shortlist"]
        if not certified["answered"]:
            print(f"cannot answer: {certified['reason']}")
            return 1
        print(f"{len(certified['units'])} of {certified['corpus_units']} "
              f"sections are within feature radius "
              f"{certified['feature_radius']} "
              f"(address ball {certified['address_radius_squared']}), "
              f"complete by {certified['guarantee']}")
        if certified["proof_of_absence"]:
            print("nothing in the corpus is within that radius -- "
                  "that is a proof of absence, not an empty result")
        for item in answer["ranked"]:
            print(f"  {item.name}  (overlap {item.overlap})")
        return 0

    if args.refresh:
        return _refresh(reuse=not args.full)

    if args.remeasure:
        try:
            target = ms.write_measurements(force=args.force)
        except ms.StaleAddressBook as refusal:
            print(f"refused: {refusal}")
            return 1
        ms.measurements(refresh=True)
        print(f"wrote {target}")
        print(f"lean measurements: {ms.state()['verdict']}")
        if not args.write:
            return 0

    if args.write:
        #  The address book first: the blocks quote it, and a block rendered
        #  against a stale book would report the staleness rather than the
        #  measurement.  Refreshing a block cannot move the book in turn --
        #  the corpus digest is taken over the *written* text, with generated
        #  bodies blanked -- so one pass in this order is a fixed point.
        state = ad.cache_state()
        if not state["fresh"]:
            target = ad.write_address_book()
            print(f"wrote {target}")
            ad.address_book(refresh=True)
            ad._address_cache.clear()
        print(f"address book: {ad.cache_state()['verdict']}")
        outcome = rd.refresh(write=True)
        for path in outcome["documents_written"]:
            print(f"wrote {path}")
        for path in outcome["blocks_changed"]:
            print(f"refreshed blocks in {path}")
        print(f"corpus digest: {inv.corpus_digest()}")
        return 0

    if args.check:
        outcome = rd.refresh(write=False)
        checks = ck.corpus_checks()
        state = ad.cache_state()
        lean = ms.state()
        inline = rd.figure_report()
        for path, name in inline["unknown"]:
            print(f"unknown figure: {name} in {path}")
        for path, name in inline["in_history"]:
            print(f"figure in a record of a past round: {name} in {path}")
        ok = (outcome["current"] and checks["holds"] and state["fresh"]
              and lean["fresh"] and inline["holds"])
        if not lean["fresh"]:
            print(f"lean measurements: {lean['verdict']} -- run --remeasure")
        for path in outcome["documents_written"]:
            print(f"stale: {path}")
        for path in outcome["blocks_changed"]:
            print(f"stale blocks: {path}")
        if not state["fresh"]:
            print(f"address book: {state['verdict']}")
        if not checks["holds"]:
            _print_report()
        print("current" if ok else "run --write")
        return 0 if ok else 1

    if args.json:
        print(json.dumps(rp.corpus_report(), indent=2, default=str,
                         sort_keys=True))
        return 0
    return _print_report()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
