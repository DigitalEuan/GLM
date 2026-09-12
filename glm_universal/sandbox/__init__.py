"""``glm_universal.sandbox`` -- work that is not part of the shipped runtime yet.

A module lives here when it is worth running and not yet worth relying on.  The
rule of the directory is the whole of it:

* nothing the shipped package *computes with* may import from
  ``glm_universal.sandbox`` -- no runtime, reasoning, semantics or data module
  may depend on anything here, so removing this directory cannot change a
  single answer the system gives.  The one declared exception is the
  documentation layer: :mod:`glm_universal.corpus.render` imports the planner,
  lazily and inside the block that reports on it, because a study of the
  sandbox has to be able to recompute what it says about it.  That exception is
  checked in ``tests/test_sandbox_planner.py`` rather than trusted;
* everything here obeys the project's exactness rules anyway -- integers and
  :class:`~fractions.Fraction`, no random source, no digest that carries
  meaning -- because a sandbox that is allowed to cheat teaches nothing;
* each module here carries a **promotion checklist**, computed rather than
  asserted, saying exactly what would have to hold for it to be moved into the
  package proper.

The current occupant is :mod:`glm_universal.sandbox.planner`, the reverse-call
planner: a problem-driven front end that inspects a problem and selects tools,
rather than dispatching on a query kind decided before the problem is read.
"""

from __future__ import annotations

__all__ = ["planner"]
