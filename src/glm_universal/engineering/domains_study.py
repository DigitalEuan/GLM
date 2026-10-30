"""``glm_universal.engineering.domains_study`` -- the domain-wheels study.

The study surface for ``studies/DOMAIN_WHEELS_STUDY.md``: reads the
stored census and returns the report.  The :mod:`glm_universal.tools`
``domains`` subcommand calls ``study_report()`` when ``--census`` is not
passed.

*Created 29 October 2026 (Iteration 6, Phase R2).*
"""
from __future__ import annotations

from typing import Any, Dict

from . import domains as dmn

__all__ = ["study_report"]


def study_report() -> Dict[str, Any]:
    """The study report: the stored census (if fresh) with the marks.

    *Stub:* delegates to :func:`glm_universal.engineering.domains.domains_report`
    with ``census=False``.
    """
    return dmn.domains_report(census=False)
