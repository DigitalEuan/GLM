"""Browser UI for the £ → ¢ → ∆ pipeline.

A single-page front end over the same functions the console UI uses:

* ``POST /api/report`` compiles one target relation and returns the ¢ DAG, the
  primitive census, the ranked ∆ implementations, the SPICE netlist and the
  exact program as JSON.  With ``save`` set it also writes the material bundle
  into the server's output directory and returns download URLs.
* ``POST /api/eval`` runs a material bundle (posted inline, or loaded from the
  output directory by name) in the exact core and returns the tick rows.
* ``GET /files/<name>`` serves a saved bundle member; only plain file names
  inside the output directory are reachable.
* ``GET /api/health`` reports liveness.

The server is stdlib only (``http.server``, ``json``, ``zipfile``), writes
nothing outside its output directory, and defaults to localhost.  Bind
``0.0.0.0`` explicitly when a remote preview needs to reach it.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from functools import lru_cache
import webbrowser
import zipfile
from collections import OrderedDict
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, unquote, urlparse

from . import concepts, design, discovery, dynamics, fabrication, physical, ui, wheels as wheel_engine
from .exact import CentError, ErrorCode, format_q
from .output_certificate import attach_certificate

MAX_BODY = 256 * 1024
MAX_TICKS = 1000
DEFAULT_OUT = "cent_out/web"
_CERTIFICATE_SCHEMAS = frozenset(
    {
        discovery.SCHEMA,
        design.SCHEMA,
        design.COMPARISON_SCHEMA,
        physical.SCHEMA,
        fabrication.SCHEMA,
        dynamics.SCHEMA,
    }
)


def _with_certificate(payload: Any) -> Any:
    """Attach the uniform certificate to compiler payloads, not error replies."""
    if not isinstance(payload, Mapping):
        return payload
    if payload.get("schema") in _CERTIFICATE_SCHEMAS or "material" in payload:
        return attach_certificate(payload)
    return payload

_ASSET = Path(__file__).with_name("web") / "index.html"
_WHEELS = Path(__file__).resolve().parent.parent / "wheels"
_WHEEL_ID = re.compile(r"W\d{1,2}")
_FILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")

#: Materials compiled by the browser are kept in memory so ``/api/eval`` can
#: reference them by a short id.  This keeps the exact runner working even when
#: a preview proxy forwards POST bodies without a Content-Length (the UI itself
#: uses GET).  It is a bounded, process-local cache, not durable storage.
_CACHE: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_CACHE_LIMIT = 32
_CACHE_LOCK = threading.Lock()

_WHEEL_FAMILIES = (
    (1, 10, "Original (Phase 66)"),
    (11, 15, "Domain (Phase 157)"),
    (16, 19, "Expanded (v2.0)"),
    (20, 25, "Computational depth"),
    (26, 27, "Astrophysics & cosmology"),
    (28, 29, "Computational depth"),
    (32, 35, "Computational depth"),
    (36, 37, "Extensions (v12_2.1)"),
    (38, 41, "Transducer extensions"),
)
_CONTENT_TYPES = {
    ".json": "application/json",
    ".zip": "application/zip",
    ".cir": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


# ---------------------------------------------------------------------------
# payloads
# ---------------------------------------------------------------------------

def _message(exc: BaseException) -> str:
    """The human-readable part of a CentError, else the exception text."""
    return getattr(exc, "message", None) or str(exc) or exc.__class__.__name__


def _render_value(value: Any) -> str:
    return ui.format_value(value)


def _first(params: Mapping[str, list[str]], key: str, default: Any = None) -> Any:
    values = params.get(key) or []
    return values[0] if values else default


def _remember(material: Mapping[str, Any]) -> str:
    """Cache a material bundle and return its short content id."""
    blob = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    token = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    with _CACHE_LOCK:
        _CACHE[token] = dict(material)
        _CACHE.move_to_end(token)
        while len(_CACHE) > _CACHE_LIMIT:
            _CACHE.popitem(last=False)
    return token


def _recall(token: str) -> dict[str, Any] | None:
    with _CACHE_LOCK:
        material = _CACHE.get(str(token))
        if material is None:
            return None
        _CACHE.move_to_end(str(token))
        return dict(material)


def _discover_payload(
    query: str,
    *,
    domain: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Validate and run problem-to-method discovery for the HTTP layer."""
    if not query:
        raise CentError(ErrorCode.INVALID_INPUT, "enter a problem statement")
    return discovery.discover(query, domain=domain, limit=limit)


def _design_spaces_payload() -> dict[str, Any]:
    """Return the exact declared design spaces for the browser solver."""
    payload: dict[str, Any] = {"ok": True}
    payload.update(design.design_space_catalog())
    return payload


def _text_parameter(source: Mapping[str, Any], key: str) -> str | None:
    """Read a string parameter without accepting a binary float."""
    value = source.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise CentError(ErrorCode.TYPE_ERROR, f"{key} must be a string")
    value = value.strip()
    return value or None


def _solve_params(source: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the HTTP-facing constraint shape for the design solver."""
    route = _text_parameter(source, "route")
    if not route:
        raise CentError(ErrorCode.INVALID_INPUT, "solve needs a declared route")
    raw_range = _text_parameter(source, "range")
    input_min = input_max = None
    if raw_range is not None:
        low, separator, high = raw_range.partition(":")
        low, high = low.strip(), high.strip()
        if not separator or not low or not high:
            raise CentError(ErrorCode.INVALID_INPUT, "range expects MIN:MAX")
        input_min, input_max = low, high
    return {
        "route_name": route,
        "input_value": _text_parameter(source, "input"),
        "input_min": input_min,
        "input_max": input_max,
        "accuracy": _text_parameter(source, "accuracy")
        or str(design.DEFAULT_ERROR_LIMIT),
        "max_cost": _text_parameter(source, "max_cost"),
        "min_bandwidth": _text_parameter(source, "min_bandwidth"),
    }


def _solve_payload(
    route_name: str,
    *,
    input_value: str | None = None,
    input_min: str | None = None,
    input_max: str | None = None,
    accuracy: str = str(design.DEFAULT_ERROR_LIMIT),
    max_cost: str | None = None,
    min_bandwidth: str | None = None,
    ranking: str = "auto",
) -> dict[str, Any]:
    """Select a declared design point for the browser/API caller."""
    result = design.solve_route(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
        ranking=ranking,
    )
    return {
        "ok": True,
        "schema": design.SCHEMA,
        "design": result.as_dict(),
    }


def _compare_params(source: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the HTTP-facing cross-route comparison request."""
    raw_routes = source.get("routes")
    if raw_routes is None:
        routes = None
    elif isinstance(raw_routes, str):
        routes = raw_routes
    elif isinstance(raw_routes, (list, tuple)):
        if not all(isinstance(item, str) for item in raw_routes):
            raise CentError(
                ErrorCode.TYPE_ERROR, "routes must contain declared route names"
            )
        routes = list(raw_routes)
    else:
        raise CentError(
            ErrorCode.TYPE_ERROR, "routes must be a comma-separated string or list"
        )
    raw_range = _text_parameter(source, "range")
    input_min = input_max = None
    if raw_range is not None:
        low, separator, high = raw_range.partition(":")
        low, high = low.strip(), high.strip()
        if not separator or not low or not high:
            raise CentError(ErrorCode.INVALID_INPUT, "range expects MIN:MAX")
        input_min, input_max = low, high
    return {
        "routes": routes,
        "input_value": _text_parameter(source, "input"),
        "input_min": input_min,
        "input_max": input_max,
        "accuracy": _text_parameter(source, "accuracy")
        or str(design.DEFAULT_ERROR_LIMIT),
        "max_cost": _text_parameter(source, "max_cost"),
        "min_bandwidth": _text_parameter(source, "min_bandwidth"),
    }


def _compare_payload(
    *,
    routes: str | list[str] | None = None,
    input_value: str | None = None,
    input_min: str | None = None,
    input_max: str | None = None,
    accuracy: str = str(design.DEFAULT_ERROR_LIMIT),
    max_cost: str | None = None,
    min_bandwidth: str | None = None,
    ranking: str = "auto",
) -> dict[str, Any]:
    """Solve the selected declared routes independently for comparison."""
    comparison = design.compare_routes(
        routes,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
        ranking=ranking,
    )
    return {
        "ok": True,
        "schema": design.COMPARISON_SCHEMA,
        "comparison": comparison.as_dict(),
    }


def _physical_payload(
    route_name: str,
    *,
    input_value: str | None = None,
    input_min: str | None = None,
    input_max: str | None = None,
    accuracy: str = str(design.DEFAULT_ERROR_LIMIT),
    max_cost: str | None = None,
    min_bandwidth: str | None = None,
) -> dict[str, Any]:
    """Emit a reference netlist and floorplan for the browser/API caller."""
    plan = physical.emit_physical(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    return {
        "ok": True,
        "schema": physical.SCHEMA,
        "physical": plan.as_dict(),
    }


def _fabricate_payload(
    route_name: str,
    *,
    input_value: str | None = None,
    input_min: str | None = None,
    input_max: str | None = None,
    accuracy: str = str(design.DEFAULT_ERROR_LIMIT),
    max_cost: str | None = None,
    min_bandwidth: str | None = None,
) -> dict[str, Any]:
    """Emit declared geometry, DRC, parasitics and thermal rows for the API."""
    plan = fabrication.emit_fabrication(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    return {
        "ok": True,
        "schema": fabrication.SCHEMA,
        "fabrication": plan.as_dict(),
    }


def _dynamics_payload(
    route_name: str,
    *,
    input_value: str | None = None,
    input_min: str | None = None,
    input_max: str | None = None,
    accuracy: str = str(design.DEFAULT_ERROR_LIMIT),
    max_cost: str | None = None,
    min_bandwidth: str | None = None,
    samples: int = dynamics.DEFAULT_SAMPLES,
    certificate_box: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Solve the declared design and return its sampled-data dynamic report."""
    result = design.solve_route(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    return {
        "ok": True,
        "schema": dynamics.SCHEMA,
        "dynamics": dynamics.analyze_design(
            result, samples=samples, certificate_box=certificate_box
        ).as_dict(),
    }


def _certificate_box_params(
    source: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Read a nested or flat certificate box without coercing its values."""
    nested = source.get("certificate_box")
    if nested is not None:
        if not isinstance(nested, Mapping):
            raise CentError(
                ErrorCode.TYPE_ERROR, "certificate_box must be an object"
            )
        return dict(nested)
    flat = {
        key: source[key]
        for key in ("v_log_hi", "v_out_hi", "v_hi")
        if source.get(key) is not None
    }
    return flat or None


def _dynamics_params(source: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the dynamic-model request shape."""
    params = _solve_params(source)
    raw = source.get("samples", dynamics.DEFAULT_SAMPLES)
    if isinstance(raw, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "samples must be an integer")
    try:
        samples = int(raw)
    except (TypeError, ValueError) as exc:
        raise CentError(ErrorCode.TYPE_ERROR, "samples must be an integer") from exc
    if not 1 <= samples <= dynamics.MAX_SAMPLES:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"samples must be in 1..{dynamics.MAX_SAMPLES}",
        )
    params["samples"] = samples
    certificate_box = _certificate_box_params(source)
    if certificate_box is not None:
        params["certificate_box"] = certificate_box
    return params


def _report_payload(
    relation: str,
    *,
    top_n: int = 6,
    save: bool = False,
    out_dir: str | Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Compile one £ and return everything the browser UI renders."""
    report = ui.build_report(relation, top_n=top_n)

    payload: dict[str, Any] = {
        "ok": True,
        "relation": report.relation,
        "target": report.target,
        "expression": report.expression,
        "dag": [
            {
                "output": op.output,
                "op": op.op,
                "inputs": list(op.inputs),
                "const": None if op.const is None else format_q(op.const),
            }
            for op in report.ops
        ],
        "primitives": [
            {"name": name, "count": count}
            for name, count in sorted(report.primitive_counts.items())
        ],
        "atomic": report.atomic_count,
        "composite": report.composite_count,
        "implementations": report.impl_count,
        "delta_sigma": report.delta_sigma_count,
        "top": [
            {
                "rank": index,
                "cost": cost.total,
                "domain": impl.substrate_domain,
                "carrier": impl.carrier_type,
                "delta_sigma": bool(impl.is_delta_sigma),
                "components": list(impl.components),
            }
            for index, (impl, cost) in enumerate(report.top, 1)
        ],
        "template": report.template,
        "template_status": report.template_status,
        "template_detail": report.template_detail,
        "netlist": report.netlist,
        "program": None,
        "notes": list(report.notes),
        "report_text": ui.render_report(report),
        "material": report.material(),
        "files": [],
        "bundle": None,
    }
    payload["id"] = _remember(payload["material"])

    if report.program is not None:
        payload["program"] = {
            "instructions": [
                {
                    "op": ins.op,
                    "inputs": list(ins.inputs),
                    "output": ins.out,
                    "params": {
                        name: format_q(value) if isinstance(value, Fraction) else str(value)
                        for name, value in ins.params.items()
                    },
                }
                for ins in report.program.instructions
            ],
            "inputs": [
                {
                    "name": wire,
                    "kind": kind,
                    "binding": (
                        format_q(report.bindings[wire]) if wire in report.bindings else None
                    ),
                }
                for wire, kind in sorted(report.program.inputs.items())
            ],
            "outputs": sorted(report.program.outputs),
        }

    if save:
        written = ui.save_material(report, out_dir)
        bundle_path = None
        if written:
            bundle_path = Path(out_dir) / (
                written[0].name[: -len(".material.json")] + ".bundle.zip"
            )
            with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in written:
                    archive.write(path, arcname=path.name)
        payload["files"] = [
            {"name": path.name, "bytes": path.stat().st_size, "url": f"/files/{path.name}"}
            for path in written
        ]
        if bundle_path is not None:
            payload["bundle"] = {
                "name": bundle_path.name,
                "bytes": bundle_path.stat().st_size,
                "url": f"/files/{bundle_path.name}",
            }
    return payload


def _eval_payload(
    material: Mapping[str, Any] | None,
    *,
    ticks: int = 1,
    sets: Mapping[str, Any] | None = None,
    seed: int = 0,
) -> dict[str, Any]:
    """Run a posted material bundle in the exact core."""
    if not isinstance(material, Mapping):
        raise CentError(ErrorCode.INVALID_INPUT, "eval needs a material bundle")
    overrides: dict[str, Fraction] = {}
    for name, raw in dict(sets or {}).items():
        text = str(raw).strip()
        if not text:
            continue
        try:
            overrides[str(name)] = Fraction(text)
        except (ValueError, ZeroDivisionError):
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"{name}: {raw!r} is not an exact rational",
            ) from None

    ticks = max(1, min(int(ticks), MAX_TICKS))
    rows = ui.run_material(material, ticks=ticks, overrides=overrides, seed=seed)
    wires = sorted({wire for row in rows for wire in row})
    return {
        "ok": True,
        "ticks": len(rows),
        "wires": wires,
        "rows": [
            {
                "t": index,
                "values": {wire: _render_value(row[wire]) for wire in sorted(row)},
            }
            for index, row in enumerate(rows)
        ],
        "lines": [
            f"t={index}  "
            + ", ".join(f"{wire} = {_render_value(row[wire])}" for wire in sorted(row))
            for index, row in enumerate(rows)
        ],
    }


def _wheel_family(wheel_id: str) -> str:
    number = int(wheel_id[1:])
    for low, high, label in _WHEEL_FAMILIES:
        if low <= number <= high:
            return label
    return "Other"


def _load_index() -> dict[str, Any]:
    path = _WHEELS / "index.json"
    if not path.is_file():
        raise CentError(ErrorCode.INVALID_INPUT, "wheel index is missing")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _wheel_doc(wheel_id: str) -> dict[str, Any] | None:
    """Read one wheel file once; every request uses the same immutable copy."""
    path = _WHEELS / f"{wheel_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _spokes_for(wheel_id: str) -> tuple[dict[str, Any], ...]:
    """Every two-input derivation the exact wheel algebra can produce.

    The wheel files store the axioms and cases; the spokes are computed, not
    authored, so a wheel's full content cannot drift away from its laws.
    """
    wheel = wheel_engine.wheel_named(wheel_id)
    seen: set[tuple[Any, ...]] = set()
    spokes: list[dict[str, Any]] = []
    for target in wheel_engine.wheel_quantities(wheel):
        for spoke in wheel_engine.wheel_spokes(wheel, target):
            key = (spoke.target, spoke.inputs, spoke.formula)
            if key in seen:
                continue
            seen.add(key)
            spokes.append({
                "target": spoke.target,
                "inputs": list(spoke.inputs),
                "formula": spoke.formula,
                "equation": spoke.text(),
                "certificate": [
                    {"axiom": axiom, "weight": str(weight)}
                    for axiom, weight in spoke.certificate.weights if weight
                ],
            })
    spokes.sort(key=lambda item: (item["target"], item["inputs"], item["formula"]))
    return tuple(spokes)


def _wheel_keywords(doc: Mapping[str, Any]) -> str:
    parts = [str(doc.get("title", ""))]
    parts.extend(str(item) for item in doc.get("axioms", []))
    parts.extend(str(item.get("equation", "")) for item in doc.get("cases", []))
    parts.extend(str(item) for item in doc.get("quantities", []))
    return " ".join(parts)


def _wheels_payload() -> dict[str, Any]:
    """The index plus per-wheel counts, family, spokes and searchable text."""
    index = _load_index()
    junctions = index.get("junctions", [])
    non_identities = index.get("non_identities", [])
    wheels = []
    for wheel_id, meta in index.get("wheels", {}).items():
        doc = _wheel_doc(wheel_id) or {}
        partners = {
            link.get("wheel_b") if link.get("wheel_a") == wheel_id else link.get("wheel_a")
            for link in junctions
            if wheel_id in (link.get("wheel_a"), link.get("wheel_b"))
        }
        spokes = _spokes_for(wheel_id)
        wheels.append({
            "id": wheel_id,
            "title": doc.get("title", meta.get("title", wheel_id)),
            "n_axioms": len(doc.get("axioms", [])) or meta.get("n_axioms", 0),
            "n_cases": len(doc.get("cases", [])) or meta.get("n_cases", 0),
            "n_quantities": len(doc.get("quantities", [])) or meta.get("n_quantities", 0),
            "n_spokes": len(spokes),
            "file": meta.get("file", f"{wheel_id}.json"),
            "family": _wheel_family(wheel_id),
            "keywords": _wheel_keywords(doc),
            "junctions": len(partners),
            "non_identities": sum(
                1 for link in non_identities
                if wheel_id in (link.get("wheel_a"), link.get("wheel_b"))
            ),
        })
    wheels.sort(key=lambda item: int(item["id"][1:]))
    return {
        "ok": True,
        "description": index.get("description", ""),
        "total_wheels": len(wheels),
        "total_axioms": sum(w["n_axioms"] for w in wheels),
        "total_cases": sum(w["n_cases"] for w in wheels),
        "total_spokes": sum(w["n_spokes"] for w in wheels),
        "reserved": ["W30", "W31"],
        "axes": index.get("axes", []),
        "families": [
            {"label": label, "from": low, "to": high}
            for low, high, label in _WHEEL_FAMILIES
        ],
        "wheels": wheels,
    }


def _wheel_payload(raw_id: str) -> dict[str, Any]:
    wheel_id = unquote(str(raw_id))
    if not _WHEEL_ID.fullmatch(wheel_id):
        raise CentError(ErrorCode.INVALID_INPUT, "invalid wheel id")
    index = _load_index()
    if wheel_id not in index.get("wheels", {}):
        raise CentError(ErrorCode.INVALID_INPUT, f"no such wheel: {wheel_id}")
    doc = _wheel_doc(wheel_id)
    if doc is None:
        raise CentError(ErrorCode.INVALID_INPUT, f"wheel file is missing: {wheel_id}")
    data = dict(doc)
    data["family"] = _wheel_family(wheel_id)
    data["junctions"] = [
        link for link in index.get("junctions", [])
        if wheel_id in (link.get("wheel_a"), link.get("wheel_b"))
    ]
    data["non_identities"] = [
        link for link in index.get("non_identities", [])
        if wheel_id in (link.get("wheel_a"), link.get("wheel_b"))
    ]
    spokes = _spokes_for(wheel_id)
    data["spokes"] = list(spokes)
    data["spoke_count"] = len(spokes)
    return {"ok": True, "wheel": data}


def _safe_file(out_dir: str | Path, name: str) -> Path:
    """Resolve a download name inside ``out_dir``, refusing anything else."""
    name = unquote(str(name))
    if not _FILE_NAME.fullmatch(name):
        raise CentError(ErrorCode.INVALID_INPUT, "invalid file name")
    root = Path(out_dir).resolve()
    path = (root / name).resolve()
    if path.parent != root or not path.is_file():
        raise CentError(ErrorCode.INVALID_INPUT, f"no such file: {name}")
    return path


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    """One request handler; ``out_dir`` is set per server by :func:`make_server`."""

    server_version = "cent-web/1"
    protocol_version = "HTTP/1.1"
    out_dir: Path = Path(DEFAULT_OUT)

    # -- plumbing ---------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str, *, download: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _asset(self) -> None:
        if not _ASSET.is_file():
            self._json(500, {"ok": False, "error": "UI asset is missing"})
            return
        self._send(200, _ASSET.read_bytes(), "text/html; charset=utf-8")

    def _file(self, raw_name: str) -> None:
        try:
            path = _safe_file(self.out_dir, raw_name)
        except CentError as exc:
            self._json(404, {"ok": False, "error": _message(exc)})
            return
        content_type = _CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self._send(200, path.read_bytes(), content_type, download=path.name)

    def _respond(self, producer: Any) -> None:
        """Run a payload producer, mapping user errors to 400 and bugs to 500."""
        try:
            payload = producer()
        except (CentError, SyntaxError, ValueError, ZeroDivisionError) as exc:
            self._json(400, {"ok": False, "error": _message(exc)})
            return
        except Exception as exc:  # noqa: BLE001 - reported to the caller
            self._json(500, {"ok": False, "error": f"internal error: {_message(exc)}"})
            return
        self._json(200, _with_certificate(payload))

    def _read_body(self) -> bytes:
        """Read a request body, including chunked bodies from a proxy."""
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            chunks: list[bytes] = []
            total = 0
            while True:
                line = self.rfile.readline(65536)
                if not line:
                    break
                size_text = line.split(b";", 1)[0].strip()
                if not size_text:
                    break
                try:
                    size = int(size_text, 16)
                except ValueError:
                    raise ValueError("bad chunk size") from None
                if size == 0:
                    while True:
                        trailer = self.rfile.readline(65536)
                        if trailer in (b"\r\n", b"\n", b""):
                            break
                    break
                total += size
                if total > MAX_BODY:
                    raise ValueError("request too large")
                chunk = self.rfile.read(size)
                if len(chunk) != size:
                    raise ValueError("truncated chunk")
                chunks.append(chunk)
                self.rfile.read(2)  # trailing CRLF
            return b"".join(chunks)
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ValueError("bad Content-Length") from None
        if length > MAX_BODY:
            raise ValueError("request too large")
        return self.rfile.read(length) if length else b""

    def _report_get(self, params: Mapping[str, list[str]]) -> dict[str, Any]:
        relation = str(_first(params, "relation", "")).strip()
        if not relation:
            raise CentError(ErrorCode.INVALID_INPUT, "enter a £ relation")
        top_n = max(1, min(int(_first(params, "top", 6)), 200))
        save = str(_first(params, "save", "0")).lower() in ("1", "true", "yes", "on")
        return _report_payload(
            relation,
            top_n=top_n,
            save=save,
            out_dir=self.out_dir,
        )

    def _eval_get(self, params: Mapping[str, list[str]]) -> dict[str, Any]:
        material = None
        token = _first(params, "id", "")
        if token:
            material = _recall(str(token))
            if material is None:
                raise CentError(ErrorCode.INVALID_INPUT, "cached material expired; compile again")
        elif _first(params, "file"):
            material = ui.load_material(_safe_file(self.out_dir, str(_first(params, "file"))))
        if material is None:
            raise CentError(ErrorCode.INVALID_INPUT, "eval needs a cached report id or file")

        sets: dict[str, str] = {}
        for item in params.get("set", []):
            name, sep, value = str(item).partition(":")
            if not sep:
                name, sep, value = str(item).partition("=")
            if not sep:
                raise CentError(ErrorCode.INVALID_INPUT, f"set {item!r} is not name:value")
            sets[name] = value
        return _eval_payload(
            material,
            ticks=int(_first(params, "ticks", 1)),
            sets=sets,
            seed=int(_first(params, "seed", 0)),
        )

    # -- routes -----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        if path in ("/", "/index.html"):
            self._asset()
        elif path == "/api/health":
            self._json(200, {"ok": True, "service": "cent-web"})
        elif path == "/api/wheels":
            self._respond(_wheels_payload)
        elif path.startswith("/api/wheels/"):
            self._respond(lambda: _wheel_payload(path[len("/api/wheels/"):]))
        elif path == "/api/concepts":
            query = str(_first(params, "q", ""))
            self._respond(lambda: concepts.explore(query))
        elif path == "/api/discover":
            query = str(_first(params, "q", "")).strip()
            domain = str(_first(params, "domain", "")).strip() or None
            limit = max(1, min(int(_first(params, "limit", 20)), 100))
            self._respond(lambda: _discover_payload(query, domain=domain, limit=limit))
        elif path == "/api/design":
            self._respond(_design_spaces_payload)
        elif path == "/api/solve":
            self._respond(lambda: _solve_payload(**_solve_params({
                "route": _first(params, "route"),
                "input": _first(params, "input"),
                "range": _first(params, "range"),
                "accuracy": _first(params, "accuracy"),
                "max_cost": _first(params, "max_cost"),
                "min_bandwidth": _first(params, "min_bandwidth"),
            }), ranking=str(_first(params, "ranking") or "auto")))
        elif path == "/api/compare":
            self._respond(lambda: _compare_payload(**_compare_params({
                "routes": _first(params, "routes"),
                "input": _first(params, "input"),
                "range": _first(params, "range"),
                "accuracy": _first(params, "accuracy"),
                "max_cost": _first(params, "max_cost"),
                "min_bandwidth": _first(params, "min_bandwidth"),
            }), ranking=str(_first(params, "ranking") or "auto")))
        elif path == "/api/physical":
            self._respond(lambda: _physical_payload(**_solve_params({
                "route": _first(params, "route"),
                "input": _first(params, "input"),
                "range": _first(params, "range"),
                "accuracy": _first(params, "accuracy"),
                "max_cost": _first(params, "max_cost"),
                "min_bandwidth": _first(params, "min_bandwidth"),
            })))
        elif path == "/api/fabricate":
            self._respond(lambda: _fabricate_payload(**_solve_params({
                "route": _first(params, "route"),
                "input": _first(params, "input"),
                "range": _first(params, "range"),
                "accuracy": _first(params, "accuracy"),
                "max_cost": _first(params, "max_cost"),
                "min_bandwidth": _first(params, "min_bandwidth"),
            })))
        elif path == "/api/dynamics":
            self._respond(lambda: _dynamics_payload(**_dynamics_params({
                "route": _first(params, "route"),
                "input": _first(params, "input"),
                "range": _first(params, "range"),
                "accuracy": _first(params, "accuracy"),
                "max_cost": _first(params, "max_cost"),
                "min_bandwidth": _first(params, "min_bandwidth"),
                "samples": _first(params, "samples", dynamics.DEFAULT_SAMPLES),
                "v_log_hi": _first(params, "v_log_hi"),
                "v_out_hi": _first(params, "v_out_hi"),
                "v_hi": _first(params, "v_hi"),
            })))
        elif path == "/api/report":
            self._respond(lambda: self._report_get(params))
        elif path == "/api/eval":
            self._respond(lambda: self._eval_get(params))
        elif path.startswith("/files/"):
            self._file(path[len("/files/"):])
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        path = urlparse(self.path).path
        if path not in ("/api/report", "/api/eval", "/api/solve", "/api/compare", "/api/physical", "/api/fabricate", "/api/dynamics"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            raw = self._read_body() or b"{}"
        except ValueError as exc:
            self._json(413 if "too large" in str(exc) else 400, {"ok": False, "error": str(exc)})
            return
        try:
            data = json.loads(raw or b"{}")
            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
        except (ValueError, UnicodeDecodeError) as exc:
            self._json(400, {"ok": False, "error": f"invalid JSON: {exc}"})
            return

        try:
            if path == "/api/report":
                params = parse_qs(urlparse(self.path).query)
                relation = str(data.get("relation") or _first(params, "relation", "")).strip()
                if not relation:
                    raise CentError(ErrorCode.INVALID_INPUT, "enter a £ relation")
                top_n = max(1, min(int(data.get("top", 6)), 200))
                payload = _report_payload(
                    relation,
                    top_n=top_n,
                    save=bool(data.get("save", False)),
                    out_dir=self.out_dir,
                )
            elif path == "/api/eval":
                material = data.get("material")
                if material is None and data.get("id"):
                    material = _recall(str(data["id"]))
                if material is None and data.get("file"):
                    material = ui.load_material(
                        _safe_file(self.out_dir, str(data["file"]))
                    )
                payload = _eval_payload(
                    material,
                    ticks=int(data.get("ticks", 1)),
                    sets=data.get("sets") or {},
                    seed=int(data.get("seed", 0)),
                )
            elif path == "/api/compare":
                payload = _compare_payload(
                    **_compare_params(data),
                    ranking=_text_parameter(data, "ranking") or "auto",
                )
            elif path == "/api/physical":
                payload = _physical_payload(**_solve_params(data))
            elif path == "/api/fabricate":
                payload = _fabricate_payload(**_solve_params(data))
            elif path == "/api/dynamics":
                payload = _dynamics_payload(**_dynamics_params(data))
            else:
                payload = _solve_payload(
                    **_solve_params(data),
                    ranking=_text_parameter(data, "ranking") or "auto",
                )
        except (CentError, SyntaxError, ValueError, ZeroDivisionError) as exc:
            self._json(400, {"ok": False, "error": _message(exc)})
            return
        except Exception as exc:  # noqa: BLE001 - reported to the caller
            self._json(500, {"ok": False, "error": f"internal error: {_message(exc)}"})
            return
        self._json(200, _with_certificate(payload))

    def log_message(self, fmt: str, *args: Any) -> None:  # keep the terminal quiet
        return


def make_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    out_dir: str | Path = DEFAULT_OUT,
) -> ThreadingHTTPServer:
    """Bind an HTTP server without starting it (tests use port 0)."""
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    class BoundHandler(Handler):
        pass

    BoundHandler.out_dir = root.resolve()
    return ThreadingHTTPServer((host, int(port)), BoundHandler)


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    out_dir: str | Path = DEFAULT_OUT,
    *,
    open_browser: bool = False,
) -> int:
    """Serve the UI until interrupted."""
    httpd = make_server(host, port, out_dir)
    shown = "127.0.0.1" if host in ("", "0.0.0.0", "::") else host
    url = f"http://{shown}:{httpd.server_port}/"
    print(f"cent web — {url}")
    print(f"materials — {Path(out_dir)}")
    print("Ctrl+C to stop")
    if open_browser:
        threading.Timer(0.4, webbrowser.open, [url]).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()
    return 0
