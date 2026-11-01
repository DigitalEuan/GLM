"""``glm_universal.engineering.domains_study`` -- the domain-wheels study.

The study surface for ``studies/DOMAIN_WHEELS_STUDY.md`` (Phase 157): the
report of :func:`glm_universal.engineering.domains.domains_report` read with
the stored census of the union (``engineering/_data/domains.json``) when
there is one.  The :mod:`glm_universal.tools` ``domains`` subcommand calls
:func:`study_report` when ``--census`` is not passed.

The marks (D1 battery, D2 frozen path, D3 census, D4 coverage, D5 proved)
are derived in :mod:`glm_universal.engineering.domains`; a mark whose
evidence is not present (the battery file ``evaluation/domain_cases.py``,
the stored census, the frozen-path evaluation) is reported missed and named
in ``unmeasured``, never assumed.

*Created 29 October 2026 (Iteration 6, Phase R2) as a stub.*
*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/DOMAIN_WHEELS_STUDY.md
§§1, 7 and the CLI handler ``_domains`` in glm_universal/tools.py.*
"""
from __future__ import annotations

from typing import Any, Dict

from . import domains as dmn

__all__ = ["study_report", "census_state", "DATA_PATH"]

#: Where the census of the union is stored (by ``domains --write``).
DATA_PATH = dmn._CENSUS_PATH


def census_state() -> Dict[str, Any]:
    """``{"present", "fresh", "verdict"}`` for the stored census."""
    return dmn.census_state()


def study_report() -> Dict[str, Any]:
    """The study report: the wheels, junctions, battery, axioms, Lean file,
    the stored census (if any, with ``census_fresh``) and the marks D1-D5,
    plus ``census_state``."""
    report = dmn.domains_report(census=False)
    report["census_state"] = dmn.census_state()
    return report
