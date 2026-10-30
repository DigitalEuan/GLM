"""Stand-in for ``glm_universal/reasoning/frozen_path.py`` (not in glm_repo.zip).

``reports/lattice_geometry.py`` imports ``reasoning/lattice_completion.py``, which imports
``reasoning/frozen_path.py`` at module load.  That file is absent from the archive, so without a
stand-in the whole session fails to import.  This stand-in only lets the import succeed: the one
function ``lattice_completion`` calls refuses with a message naming the missing file.
Replace it with the real module from your GLM repository.
"""
from __future__ import annotations


def frozen_path_report(*args, **kwargs):
    raise RuntimeError(
        "report subject unavailable: glm_universal/reasoning/frozen_path.py is not in this "
        "checkout (stand-in from rule30_round9/frozen_path_standin.py)")
