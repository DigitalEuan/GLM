"""Optional respelling implementation boundary.

The owner-supplied sintering module is not present in this reorganized
checkout.  The feature gate in :mod:`respell` is therefore disabled, but this
module keeps the public fallback interface importable and fails explicitly if
called directly.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Sintered:
    text: str
    changed: bool = False
    _note: str = ""

    def note(self) -> str:
        return self._note


def respell_sintered(text: str) -> Sintered:
    raise NotImplementedError(
        "runtime.sinter.py is unavailable in this checkout; respelling is disabled"
    )
