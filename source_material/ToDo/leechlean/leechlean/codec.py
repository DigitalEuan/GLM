"""leechlean.codec -- a Lean file is a bunch of Leech addresses.

Encode: file bytes -> token stream -> one lattice address per token.
Decode: address stream -> part -> exact token text -> file bytes.

The codebook from :mod:`leechlean.addressing` is injective (every address
names exactly one part), so decoding is exact and needs no side information:
**the address stream is the file**.  The address stream is not meant to be
compact -- it is meant to carry geometry; the report measures both its size
and its information content (which equals the token stream's entropy).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from .addressing import Addressing
from .lean_parts import Tok, tokenize

Addr = Tuple[int, ...]


def encode_text(text: str, addr: Addressing) -> List[Addr]:
    toks = tokenize(text)
    return [addr.addresses[t.key] for t in toks]


def decode_stream(stream: Sequence[Addr], addr: Addressing) -> str:
    out = []
    for a in stream:
        key = addr.cells[tuple(a)][0]
        out.append(key.split(":", 1)[1])
    return "".join(out)


def encode_file(path: Path, addr: Addressing) -> List[Addr]:
    return encode_text(path.read_text(encoding="utf-8", errors="replace"), addr)


def verify_corpus(addr: Addressing) -> Dict[str, object]:
    """Encode and decode every corpus file; report byte-exactness and sizes."""
    ok = 0
    fails: List[str] = []
    raw_bytes = 0
    stream_bytes = 0
    n_tokens = 0
    n_files = 0
    max_coord = 0
    for rec in addr.inv.files:
        n_files += 1
        stream = [addr.addresses[t.key] for t in rec.toks]
        back = decode_stream(stream, addr)
        text = rec.path.read_text(encoding="utf-8", errors="replace")
        if back == text:
            ok += 1
        else:
            fails.append(rec.rel)
        raw_bytes += len(text.encode("utf-8"))
        # address stream size: 24 int8 coordinates + a varint cell id would be
        # smaller, but the honest measure is 24 coordinates as they stand
        stream_bytes += 24 * len(stream)
        n_tokens += len(stream)
        max_coord = max([max_coord] + [max(abs(c) for c in a) for a in stream[:50]])
    return {
        "files": n_files,
        "exact_round_trips": ok,
        "failures": fails[:10],
        "n_failures": len(fails),
        "raw_bytes": raw_bytes,
        "address_stream_bytes_int8": stream_bytes,
        "expansion_factor": stream_bytes / raw_bytes,
        "n_tokens": n_tokens,
        "max_abs_coordinate_seen_sample": max_coord,
    }
