"""SHA-256, kept outside the core, for integrity only.

Directive **D3** of ``PROJECT_DIRECTIVES.md`` says a digest addresses
*integrity*, never *meaning*.  This module is where the project keeps the
consequence of that rule in the code layout itself:

* the six core sub-packages -- ``substrate``, ``data_objects``, ``reasoning``,
  ``semantics``, ``runtime`` and ``migration`` -- may not import
  :mod:`hashlib` at all, and :func:`glm_universal.reasoning.blueprint.
  ubp_source_audit` enforces that;
* everything the project genuinely needs a digest for is an integrity
  question -- has this file changed since it was checked? -- and those
  questions are answered here, one module above the core, next to
  :mod:`glm_universal.figures`;
* one further use is a deliberately labelled *control*: the ``hash_control``
  scheme of :mod:`glm_universal.reasoning.lean_address` addresses each Lean
  declaration by the digest of its name, and is measured against the
  structural encoding precisely to show that the digest knows nothing.  A
  control belongs outside the core for the same reason the thing it controls
  belongs inside it.

Nothing here interprets a digest.  :func:`stream_words` is a reproducible
pseudo-random source used for null models; it is seeded by a fixed string, so
two runs of the project agree, and no meaning is claimed for its output.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple

__all__ = [
    "sha256_hex",
    "sha256_bytes",
    "file_digest",
    "tree_digest",
    "byte_vector",
    "stream_words",
    "seeded_permutation",
]


def sha256_hex(data: bytes) -> str:
    """The SHA-256 of ``data``, as a hexadecimal string."""
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> bytes:
    """The SHA-256 of ``data``, as the raw 32 bytes."""
    return hashlib.sha256(data).digest()


def file_digest(path: Path) -> str:
    """The SHA-256 of one file's bytes."""
    return sha256_hex(Path(path).read_bytes())


def tree_digest(paths: Iterable[Path], root: Optional[Path] = None) -> str:
    """One digest over a set of files: their names *and* their contents.

    The canonical form is the same everywhere in the project -- for each path
    in the order supplied, the path relative to ``root`` (or the bare name),
    a NUL, the SHA-256 of the bytes, a NUL -- so a rename is as visible as an
    edit, and two callers that agree on the file list agree on the digest.
    """
    outer = hashlib.sha256()
    for path in paths:
        path = Path(path)
        label = str(path.relative_to(root)) if root else path.name
        outer.update(label.encode("utf-8"))
        outer.update(b"\0")
        outer.update(file_digest(path).encode("ascii"))
        outer.update(b"\0")
    return outer.hexdigest()


def byte_vector(text: str, length: int, modulus: int) -> Tuple[int, ...]:
    """``length`` coordinates read out of ``SHA-256(text)``, modulo ``modulus``.

    The control encoding: deterministic, uniform, and -- by construction --
    carrying nothing about the subject but its name.
    """
    digest = sha256_bytes(text.encode("utf-8"))
    return tuple(digest[i % len(digest)] % modulus for i in range(length))


def stream_words(seed: str, count: int) -> Iterator[int]:
    """A reproducible stream of ``count`` 32-bit words, seeded by ``seed``.

    Used for null models, where the point is that the ordering carries no
    information; :mod:`random` is banned by the UBP and would in any case not
    be reproducible across interpreters.
    """
    produced = 0
    counter = 0
    while produced < count:
        block = sha256_bytes(f"{seed}-{counter}".encode("utf-8"))
        counter += 1
        for i in range(0, len(block), 4):
            if produced >= count:
                return
            word = 0
            for byte in block[i:i + 4]:
                word = (word << 8) | byte
            produced += 1
            yield word


def seeded_permutation(n: int, seed: str = "glm-null-model") -> List[int]:
    """A deterministic permutation of ``range(n)``.

    A Fisher-Yates shuffle driven by :func:`stream_words`, with rejection
    sampling so that the result is unbiased for any ``n`` below ``2**32``.
    """
    order = list(range(n))
    if n < 2:
        return order
    counter = 0
    buffer: List[int] = []

    def next_word() -> int:
        nonlocal counter, buffer
        if not buffer:
            block = sha256_bytes(f"{seed}-{counter}".encode("utf-8"))
            counter += 1
            for i in range(0, len(block), 4):
                word = 0
                for byte in block[i:i + 4]:
                    word = (word << 8) | byte
                buffer.append(word)
            buffer.reverse()
        return buffer.pop()

    for i in range(n - 1, 0, -1):
        bound = i + 1
        limit = (1 << 32) - ((1 << 32) % bound)
        while True:
            word = next_word()
            if word < limit:
                break
        j = word % bound
        order[i], order[j] = order[j], order[i]
    return order
