"""``glm_universal.corpus.report`` -- the whole corpus measurement, in one call.

Everything the corpus study quotes is a key of :func:`corpus_report`, and every
table in that study is rendered from this payload by
:mod:`glm_universal.corpus.render`.  That is the discipline the rest of the
package already keeps for its registers, applied to the documentation itself:
the write-up holds the argument, and the numbers are emitted by the function
that measured them.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict

from ..derived import memo
from . import address as ad
from . import checks as ck
from . import inventory as inv
from . import render as rd

__all__ = ["corpus_report", "reading_cost"]


def reading_cost() -> Dict[str, object]:
    """What a session pays to read the corpus, at each resolution.

    Three numbers and the ratios between them: the whole corpus, the
    current-state half of it, and the tier-0 read of that half.  This is the
    figure the optimisation is judged by, and it is a count of words rather
    than an impression.
    """
    data = inv.inventory_report()
    total = int(data["words"])
    state = int(data["state_words"])
    tier0 = int(data["tier0_words"])
    return {
        "words_whole_corpus": total,
        "words_current_state": state,
        "words_tier0": tier0,
        "archive_fraction": (Fraction(total - state, total) if total
                             else Fraction(0)),
        "tier0_fraction_of_state": (Fraction(tier0, state) if state
                                    else Fraction(0)),
        "tier0_fraction_of_corpus": (Fraction(tier0, total) if total
                                     else Fraction(0)),
    }


@memo
def corpus_report() -> Dict[str, object]:
    """Every figure the corpus study quotes, recomputed."""
    checks = ck.corpus_checks()
    return {
        "inventory": inv.inventory_report(),
        "reading_cost": reading_cost(),
        "checks": checks,
        "generation": rd.generation_report(),
        "address": ad.address_report(),
        "holds": bool(checks["holds"]),
        "study": "studies/CORPUS_ADDRESS_STUDY.md",
    }
