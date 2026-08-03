# ══════════════════════════════════════════════════════════════════════════════
# §26  CRG-TRAVERSAL ALU (v3.17.0 — Word-Level NoiseALU Equivalent)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   Provide the word-relation analogue of `NoiseALU` — a step-by-step traversal
#   engine for the Concept Relation Graph (CRG) that produces a real execution
#   trace and a substrate fingerprint of the *destination vector*. This is the
#   "stage-1 algorithm for words" the SESSION_SUMMARY (§10) explicitly identifies
#   as missing: every vector-space method tried so far (SVD, MOG-grounding, Tilt,
#   quadrant-forcing) was doing stage-1 work (meaning-discovery from raw
#   statistics) when the codebase's own working pattern is stage-1 (explicit
#   algorithm/fact) → stage-2 (substrate fingerprint of the outcome).
#
# WHAT THIS MODULE DOES (and what it deliberately doesn't)
#
#   DOES:
#   * `traverse(src, label, dst)` — walk a single CRG edge. Returns the
#     destination vector + a 2-line trace + a fingerprint.
#   * `shortest_path(a, b, max_hops=3)` — BFS a path of CRG edges between two
#     concepts. Returns the path + a step-by-step trace + a fingerprint of the
#     final destination vector. THIS is the word-level analogue of `gcd(a,b)`
#     — explicit, traceable, deterministic.
#   * `relate(a, b)` — list all CRG labels connecting a and b (direct + 2-hop).
#   * `chain(*words)` — walk a sequence of words as a chain of edges; produces
#     a "sentence backbone" trace + fingerprint of the endpoint.
#   * `compose_path_fingerprint(path)` — fingerprint an entire backbone as a
#     single substrate classification, so two backbones can be compared.
#
#   DOES NOT:
#   * Replace SVD / distributional vectors. The vector at each CRG node is
#     still the existing vocab entry's vector. This module is *only* about
#     traversal and the resulting fingerprint — it doesn't construct new
#     vectors.
#   * Force quadrants. The destination vector is fingerprinted as-is.
#   * Invent new edges. If no path exists, the result is None — no hallucinated
#     relation. (Contrast with `generate_grammatical`, which falls back to
#     nearest-neighbour walks when no CRG path exists.)
#
# ARCHITECTURE — the two-stage "sovereign computation" pattern, applied to words:
#   Stage-1: BFS / direct edge walk over the CRG. Each hop appends a trace line
#            of the form `"{src} --{label}--> {dst}"`. This is the explicit
#            algorithm — exactly as Euclid's algorithm walks `(a,b) → (b, a mod b)`,
#            CRG traversal walks `(concept, relation, concept)` step by step.
#   Stage-2: `AdaptiveManifold.fingerprint(destination_hex_int)` classifies the
#            outcome vector. This is the same `fingerprint()` call that
#            `NoiseALU.gcd` uses on its integer result — the mechanism is
#            domain-agnostic once fed a real relational outcome.
#
# AUTHOR
#   Z.ai levelling-up pass — 2026-07-06
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from collections import deque

# ── Substrate imports ───────────────────────────────────────────────────────
try:
    from ubp_unified_v5 import AdaptiveManifold, GOLAY_ENGINE
    _HAS_NATIVE = True
except Exception as _e:
    _HAS_NATIVE = False
    _NATIVE_IMPORT_ERR = str(_e)

# ── GLM imports ─────────────────────────────────────────────────────────────
try:
    from GLM01_substrate import (
        ConceptRelationGraph, CRGEdge, BLA,
        vector_to_hex_int, fast_hamming,
    )
    _HAS_GLM = True
except Exception as _e:
    _HAS_GLM = False
    _GLM_IMPORT_ERR = str(_e)


# ── Module-level singleton ──────────────────────────────────────────────────
_MANIFOLD: Optional[AdaptiveManifold] = None


def _get_manifold() -> AdaptiveManifold:
    global _MANIFOLD
    if _MANIFOLD is None:
        if not _HAS_NATIVE:
            raise RuntimeError(f"Native UBP engines unavailable: {_NATIVE_IMPORT_ERR!r}")
        _MANIFOLD = AdaptiveManifold(max_bits=64)
    return _MANIFOLD


# ══════════════════════════════════════════════════════════════════════════════
#  CRGTraversalALU
# ══════════════════════════════════════════════════════════════════════════════
class CRGTraversalALU:
    """Word-level analogue of NoiseALU.

    Traverses the Concept Relation Graph step by step, recording a trace and
    fingerprinting the destination vector via `AdaptiveManifold`. This is the
    stage-1 algorithm for word relations, mirroring `NoiseALU.gcd` for numbers.

    Construction
    ------------
    CRGTraversalALU(crg, vocab)
        crg   : ConceptRelationGraph (from GLM01_substrate.build_default_crg
                or build_extended_crg)
        vocab : the GLM vocab object (must expose `.words` dict with entries
                that have `.vector` attribute, OR be a dict word→entry)
    """

    def __init__(self, crg: Any, vocab: Any):
        if not _HAS_NATIVE:
            raise RuntimeError(f"Native engines unavailable: {_NATIVE_IMPORT_ERR!r}")
        if not _HAS_GLM:
            raise RuntimeError(f"GLM substrate unavailable: {_GLM_IMPORT_ERR!r}")
        self.crg = crg
        # Normalise vocab: if it has .words, use that; else assume it's a dict
        if hasattr(vocab, 'words'):
            self._vocab = vocab.words
        else:
            self._vocab = vocab
        self.manifold = _get_manifold()

    # ── Helpers ───────────────────────────────────────────────────────────
    def _entry(self, word: str):
        return self._vocab.get(word)

    def _vector_of(self, word: str) -> Optional[List[int]]:
        e = self._entry(word)
        if e is None:
            return None
        v = getattr(e, 'vector', None)
        if v and len(v) == 24:
            return v
        return None

    def _hex_int(self, vec: List[int]) -> int:
        return vector_to_hex_int(vec)

    def _fingerprint(self, vec: List[int]) -> Dict[str, Any]:
        """Run AdaptiveManifold.fingerprint on a 24-bit vector's hex int form."""
        try:
            return self.manifold.fingerprint(self._hex_int(vec))
        except Exception as e:
            return {"error": str(e)}

    # ── Single-edge traversal ─────────────────────────────────────────────
    def traverse(self, src: str, label: str, dst: str) -> Dict[str, Any]:
        """Walk a single CRG edge.

        Returns a dict with:
            src, label, dst, dst_vector, dst_hex, trace, fingerprint,
            verified (bool — True iff the edge exists in the CRG),
            elapsed_us.
        """
        t0 = time.perf_counter()
        trace: List[str] = []
        # Verify the edge exists
        existing = [e for e in self.crg.out.get(src, []) if e.label == label and e.dst == dst]
        verified = bool(existing)
        if verified:
            trace.append(f"traverse: {src} --{label}--> {dst}  [edge verified]")
        else:
            trace.append(f"traverse: {src} --{label}--> {dst}  [edge NOT in CRG]")

        dst_vec = self._vector_of(dst)
        if dst_vec is None:
            return {
                "operation": "traverse",
                "src": src, "label": label, "dst": dst,
                "dst_vector": None, "dst_hex": None,
                "trace": trace,
                "fingerprint": {"error": f"no vector for {dst!r}"},
                "verified": verified,
                "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
            }
        fp = self._fingerprint(dst_vec)
        trace.append(f"  fingerprint {dst} -> nrci={fp.get('nrci')} "
                     f"lattice={fp.get('lattice')!r} sw={fp.get('sw')}")
        return {
            "operation": "traverse",
            "src": src, "label": label, "dst": dst,
            "dst_vector": dst_vec,
            "dst_hex": self._hex_int(dst_vec),
            "trace": trace,
            "fingerprint": fp,
            "verified": verified,
            "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        }

    # ── BFS shortest path ────────────────────────────────────────────────
    def shortest_path(self, a: str, b: str,
                      max_hops: int = 3,
                      label_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """BFS the CRG from `a` to `b` and fingerprint the endpoint.

        This is the word-level analogue of `NoiseALU.gcd`: an explicit,
        step-by-step algorithm that produces a traceable, deterministic answer.

        Parameters
        ----------
        a, b : str
            Source / destination concepts. Both must be in the vocab.
        max_hops : int
            Maximum BFS depth. Default 3 (matches `crg.shortest_path`).
        label_filter : Optional[List[str]]
            If given, only traverse edges with these labels.

        Returns
        -------
        Dict with: operation, src, dst, path (List[CRGEdge]), path_str,
        dst_vector, dst_hex, trace, fingerprint, elapsed_us.
        If no path is found within `max_hops`, path is None and fingerprint
        is the empty dict.
        """
        t0 = time.perf_counter()
        trace: List[str] = [f"shortest_path: BFS from {a!r} to {b!r} (max_hops={max_hops})"]

        if a not in self._vocab:
            trace.append(f"  [abort] {a!r} not in vocab")
            return self._no_path(a, b, trace, t0)
        if b not in self._vocab:
            trace.append(f"  [abort] {b!r} not in vocab")
            return self._no_path(a, b, trace, t0)

        # BFS
        visited = {a}
        queue = deque([(a, [])])
        path: Optional[List[CRGEdge]] = None
        while queue:
            node, path_so_far = queue.popleft()
            if len(path_so_far) >= max_hops:
                continue
            for edge in self.crg.out.get(node, []):
                if label_filter and edge.label not in label_filter:
                    continue
                if edge.dst in visited:
                    continue
                new_path = path_so_far + [edge]
                if edge.dst == b:
                    path = new_path
                    queue.clear()
                    break
                visited.add(edge.dst)
                queue.append((edge.dst, new_path))

        if path is None:
            trace.append(f"  [no path] {a!r} → {b!r} within {max_hops} hops")
            return self._no_path(a, b, trace, t0)

        # Build the trace
        for i, edge in enumerate(path):
            trace.append(f"  hop {i+1}: {edge.src} --{edge.label}--> {edge.dst}")
        path_str = " → ".join(
            f"{e.src} --{e.label}--> {e.dst}" for e in path
        )

        # Fingerprint the destination vector
        dst_vec = self._vector_of(b)
        if dst_vec is None:
            trace.append(f"  [warn] {b!r} has no vector — cannot fingerprint")
            fp: Dict[str, Any] = {"error": "no destination vector"}
        else:
            fp = self._fingerprint(dst_vec)
            trace.append(f"  fingerprint {b!r} -> nrci={fp.get('nrci')} "
                         f"lattice={fp.get('lattice')!r} sw={fp.get('sw')}")

        return {
            "operation": "shortest_path",
            "src": a, "dst": b,
            "path": path,
            "path_str": path_str,
            "n_hops": len(path),
            "dst_vector": dst_vec,
            "dst_hex": self._hex_int(dst_vec) if dst_vec else None,
            "trace": trace,
            "fingerprint": fp,
            "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        }

    def _no_path(self, a: str, b: str, trace: List[str], t0: float) -> Dict[str, Any]:
        return {
            "operation": "shortest_path",
            "src": a, "dst": b,
            "path": None, "path_str": "", "n_hops": 0,
            "dst_vector": None, "dst_hex": None,
            "trace": trace,
            "fingerprint": {},
            "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        }

    # ── Direct relations between two concepts ────────────────────────────
    def relate(self, a: str, b: str, max_hops: int = 2) -> Dict[str, Any]:
        """List all CRG relations connecting `a` and `b` (direct + 2-hop).

        Returns a dict with: operation, a, b, direct_labels (List[str]),
        via (List[{via, label}]), trace, fingerprint, elapsed_us.
        """
        t0 = time.perf_counter()
        trace: List[str] = [f"relate: {a!r} ↔ {b!r}"]

        direct: List[str] = []
        for e in self.crg.out.get(a, []):
            if e.dst == b:
                direct.append(e.label)
                trace.append(f"  direct: {a} --{e.label}--> {b}")
        for e in self.crg.into.get(a, []):
            if e.src == b:
                direct.append(f"reverse:{e.label}")
                trace.append(f"  direct (reverse): {b} --{e.label}--> {a}")

        via_list: List[Dict[str, str]] = []
        if not direct and max_hops >= 2:
            a_out = {e.dst: e.label for e in self.crg.out.get(a, [])}
            b_in = {e.src: e.label for e in self.crg.into.get(b, [])}
            shared = set(a_out.keys()) & set(b_in.keys())
            for mid in shared:
                via_list.append({"via": mid, "label": f"{a_out[mid]}+{b_in[mid]}"})
                trace.append(f"  via {mid}: {a} --{a_out[mid]}--> {mid} --{b_in[mid]}--> {b}")

        # Fingerprint of `b`'s vector (the destination of any relation)
        b_vec = self._vector_of(b)
        fp = self._fingerprint(b_vec) if b_vec else {"error": "no vector"}

        return {
            "operation": "relate",
            "a": a, "b": b,
            "direct_labels": direct,
            "via": via_list,
            "trace": trace,
            "fingerprint": fp,
            "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        }

    # ── Chain traversal (multi-hop) ──────────────────────────────────────
    def chain(self, *words: str,
              label_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Walk a sequence of words as a chain of CRG edges.

        For each consecutive pair (w_i, w_{i+1}), find the shortest CRG path
        (up to 2 hops) connecting them. Concatenate the traces.

        Returns a dict with: operation, words, all_paths (List[List[CRGEdge]]),
        full_trace, end_vector, end_fingerprint, total_hops, elapsed_us.
        """
        t0 = time.perf_counter()
        full_trace: List[str] = [f"chain: {' -> '.join(words)}"]
        all_paths: List[List[CRGEdge]] = []
        total_hops = 0

        for i in range(len(words) - 1):
            seg = self.shortest_path(words[i], words[i+1], max_hops=2,
                                     label_filter=label_filter)
            if seg["path"] is None:
                full_trace.append(f"  [{i+1}] NO PATH {words[i]!r} → {words[i+1]!r}")
                # Stop the chain at the first break
                break
            all_paths.append(seg["path"])
            total_hops += len(seg["path"])
            full_trace.append(f"  [{i+1}] {seg['path_str']}")

        # Fingerprint the last reached word
        last_word = words[0]
        for path in all_paths:
            if path:
                last_word = path[-1].dst
        last_vec = self._vector_of(last_word)
        fp = self._fingerprint(last_vec) if last_vec else {"error": "no vector"}
        full_trace.append(f"  fingerprint {last_word!r} -> nrci={fp.get('nrci')} "
                          f"lattice={fp.get('lattice')!r}")

        return {
            "operation": "chain",
            "words": list(words),
            "all_paths": all_paths,
            "total_hops": total_hops,
            "end_word": last_word,
            "end_vector": last_vec,
            "end_fingerprint": fp,
            "full_trace": full_trace,
            "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        }

    # ── Path-level fingerprint (compare two backbones) ───────────────────
    def compose_path_fingerprint(self, path: List[CRGEdge]) -> Dict[str, Any]:
        """Fingerprint an entire CRG backbone as a single substrate classification.

        Hashes the canonical path string and feeds the hash to
        `AdaptiveManifold.fingerprint`. Two isomorphic backbones produce the
        same hash → the same fingerprint. This lets the meta-graph detect
        when two zones have equivalent relation structures.
        """
        if not path:
            return {"error": "empty path"}
        canonical = "|".join(f"{e.src}:{e.label}:{e.dst}" for e in path)
        # Stable hash: SHA-256 → int
        import hashlib
        h = hashlib.sha256(canonical.encode("utf-8")).digest()
        n = int.from_bytes(h, "big")
        try:
            fp = self.manifold.fingerprint(n)
        except Exception as e:
            fp = {"error": str(e)}
        return {
            "operation": "compose_path_fingerprint",
            "canonical": canonical,
            "hash": hex(n),
            "n_edges": len(path),
            "fingerprint": fp,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM26_crg_alu",
        "version": "3.17.0",
        "native_available": _HAS_NATIVE,
        "glm_available": _HAS_GLM,
        "operations": [
            "traverse", "shortest_path", "relate", "chain",
            "compose_path_fingerprint",
        ],
        "architecture": "stage-1 (BFS over CRG) + stage-2 (AdaptiveManifold.fingerprint)",
    }


if __name__ == "__main__":
    print("=== GLM26 CRG-Traversal ALU v3.17.0 — self-test ===")
    print(status())
    print()

    if not (_HAS_NATIVE and _HAS_GLM):
        print("Dependencies unavailable. Cannot run demo.")
        raise SystemExit(1)

    from GLM01_substrate import build_default_crg
    from GLM03_crg import build_extended_crg

    # Build a runtime vocab so we have real vectors to fingerprint
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37(auto_expand=False)
    crg = rt.crg
    alu = CRGTraversalALU(crg, rt.vocab)

    print(f"CRG stats: {crg.stats()}")
    print(f"Vocab size: {len(rt.vocab.words)}")
    print()

    # Demo 1: direct traversal
    print("--- traverse(hamiltonian, generates, time) ---")
    r = alu.traverse("hamiltonian", "generates", "time")
    print(f"  verified={r['verified']}")
    print(f"  dst_hex={r['dst_hex']}")
    print(f"  fingerprint: nrci={r['fingerprint'].get('nrci')} "
          f"lattice={r['fingerprint'].get('lattice')!r}")
    for line in r["trace"]:
        print(f"  | {line}")
    print()

    # Demo 2: shortest path
    print("--- shortest_path(hamiltonian, time, max_hops=3) ---")
    r = alu.shortest_path("hamiltonian", "time", max_hops=3)
    print(f"  path: {r['path_str']}")
    print(f"  n_hops: {r['n_hops']}")
    print(f"  fingerprint: nrci={r['fingerprint'].get('nrci')} "
          f"lattice={r['fingerprint'].get('lattice')!r}")
    for line in r["trace"]:
        print(f"  | {line}")
    print()

    # Demo 3: relate
    print("--- relate(boson, fermion) ---")
    r = alu.relate("boson", "fermion")
    print(f"  direct: {r['direct_labels']}")
    print(f"  via: {r['via']}")
    for line in r["trace"]:
        print(f"  | {line}")
    print()

    # Demo 4: chain
    print("--- chain(hamiltonian, time, energy) ---")
    r = alu.chain("hamiltonian", "time", "energy")
    print(f"  total_hops: {r['total_hops']}")
    print(f"  end_word: {r['end_word']}")
    print(f"  end_fingerprint: nrci={r['end_fingerprint'].get('nrci')} "
          f"lattice={r['end_fingerprint'].get('lattice')!r}")
    for line in r["full_trace"]:
        print(f"  | {line}")
    print()

    # Demo 5: path fingerprint
    print("--- compose_path_fingerprint ---")
    if r["all_paths"]:
        full_path = [e for p in r["all_paths"] for e in p]
        pf = alu.compose_path_fingerprint(full_path)
        print(f"  canonical: {pf['canonical']}")
        print(f"  hash: {pf['hash'][:32]}...")
        print(f"  fingerprint: nrci={pf['fingerprint'].get('nrci')} "
              f"lattice={pf['fingerprint'].get('lattice')!r}")
