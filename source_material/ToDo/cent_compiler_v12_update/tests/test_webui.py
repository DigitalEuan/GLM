"""Tests for the browser UI server (cent_compiler.webui).

Runs a real ThreadingHTTPServer on an ephemeral port against a temporary
output directory, so routing, JSON, file safety and exact evaluation are
exercised end to end without a browser.
"""
from __future__ import annotations

import http.client
import io
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import webui  # noqa: E402

PASS = 0
FAIL = 0


def expect(condition, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def chunked_request(url: str, payload: dict):
    """POST with Transfer-Encoding: chunked (as a preview proxy may forward)."""
    parsed = urllib.parse.urlparse(url)
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=60)
    connection.putrequest("POST", parsed.path)
    connection.putheader("Content-Type", "application/json")
    connection.putheader("Transfer-Encoding", "chunked")
    connection.endheaders()
    data = json.dumps(payload).encode("utf-8")
    connection.send(b"%x\r\n" % len(data) + data + b"\r\n0\r\n\r\n")
    response = connection.getresponse()
    body = response.read()
    status = response.status
    connection.close()
    return status, body


def request(url: str, payload: dict | None = None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main() -> int:
    print("=" * 78)
    print("BROWSER UI")
    print("=" * 78)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "web"
        httpd = webui.make_server("127.0.0.1", 0, out)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{httpd.server_port}"
        try:
            # -- page and health ------------------------------------------
            status, body = request(base + "/")
            html = body.decode("utf-8")
            expect(status == 200, "GET / returns 200")
            expect("£" in html and "/api/report" in html, "page carries the £ input and report endpoint")
            expect(
                "panel-wheels" in html and "panel-concepts" in html and "panel-methods" in html,
                "page carries the wheel, concept and method-discovery panels",
            )
            expect(
                "panel-design" in html and "/api/design" in html and "/api/solve" in html
                and "/api/physical" in html and "/api/fabricate" in html
                and "/api/dynamics" in html,
                "page carries the live design, geometry, netlist and dynamic panel",
            )
            expect(
                "min bandwidth" in html and "min_bandwidth" in html,
                "design cards expose the declared-pole bandwidth constraint",
            )
            expect(
                "Method comparison" in html and "/api/compare" in html
                and "compareGo" in html
                and "Download comparison Markdown" in html,
                "page carries cross-route comparison and export controls",
            )
            expect(
                "method.contract_status_label" in html,
                "method cards render the selected contract capability status",
            )
            expect(
                'showPanel("wheels")' in html and "openWheel(item.wheel)" in html,
                "method cards link wheel candidates to the wheel view",
            )
            expect(
                "data.steps" in html and "step.index" in html,
                "method discovery renders ordered goal steps",
            )

            status, body = request(base + "/api/health")
            health = json.loads(body)
            expect(status == 200 and health.get("ok") is True, "health endpoint is live")

            # -- report ---------------------------------------------------
            status, body = request(
                base + "/api/report",
                {
                    "relation": "velocity = (2 * energy / mass)^(1/2)",
                    "top": 6,
                    "save": True,
                },
            )
            report = json.loads(body)
            expect(status == 200 and report.get("ok") is True, "report request succeeds")
            expect(len(report["dag"]) == 3, "velocity £ decomposes into 3 ¢ steps")
            expect(
                [(row["op"], row["output"]) for row in report["dag"]]
                == [("scale", "_scale1"), ("div", "_div2"), ("sqrt", "velocity")],
                "DAG ops and wires are reported in order",
            )
            expect(report["atomic"] == 1 and report["composite"] == 2, "primitive census splits atomic/composite")
            expect(report["implementations"] > 0 and len(report["top"]) == 6, "∆ implementations are ranked")
            expect(
                report["template"] == "opamp_sqrt" and "Op-amp" in (report["netlist"] or ""),
                "SPICE netlist generated",
            )
            expect(report["program"] is not None and len(report["program"]["instructions"]) == 3, "exact program generated")
            expect(report["notes"] == [], "clean compile has no notes")
            certificate = report.get("output_certificate") or {}
            expect(
                certificate.get("schema") == "cent-output-certificate/1"
                and certificate.get("subject_schema") == "cent-material/1"
                and certificate.get("status") == "partial"
                and bool(certificate.get("checks")),
                f"report carries an output certificate: {certificate}",
            )

            # -- saved material ------------------------------------------
            names = {item["name"] for item in report["files"]}
            expect(
                names == {"velocity.material.json", "velocity.opamp_sqrt.cir", "velocity.report.txt"},
                "three material files are saved",
            )
            expect(report["bundle"] is not None, "a zip bundle is offered")

            status, body = request(base + "/files/velocity.material.json")
            material = json.loads(body)
            expect(
                status == 200 and material.get("schema") == "cent-material/1",
                "saved material downloads and parses",
            )

            status, body = request(base + "/files/" + report["bundle"]["name"])
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                zipped = set(archive.namelist())
            expect(status == 200 and zipped == names, "bundle zip contains the three files")

            # -- file safety ---------------------------------------------
            status, _ = request(base + "/files/..%2Fsecret.txt")
            expect(status == 404, "path traversal is refused")
            status, _ = request(base + "/files/nope.material.json")
            expect(status == 404, "unknown file is 404")

            # -- exact evaluation ----------------------------------------
            status, body = request(
                base + "/api/eval",
                {
                    "material": material,
                    "ticks": 1,
                    "sets": {"energy": "8", "mass": "1"},
                },
            )
            run = json.loads(body)
            expect(status == 200 and run.get("ok") is True, "eval request succeeds")
            expect(
                run["rows"][0]["values"].get("velocity") == "[4]",
                "energy=8, mass=1 runs to exactly [4]",
            )
            expect("velocity = [4]" in run["lines"][0], "text tick line mirrors the exact value")

            status, body = request(
                base + "/api/eval",
                {"material": material, "sets": {"energy": "1/2", "mass": "1"}},
            )
            run = json.loads(body)
            expect(
                status == 200 and run["rows"][0]["values"]["velocity"] == "[1]",
                "rational input stays exact (energy=1/2 → √1 = [1])",
            )

            status, body = request(
                base + "/api/eval",
                {"material": material, "sets": {"energy": "banana"}},
            )
            bad = json.loads(body)
            expect(
                status == 400 and bad.get("ok") is False and "exact rational" in bad.get("error", ""),
                "non-rational input is rejected with a message",
            )

            # -- report without saving -----------------------------------
            status, body = request(
                base + "/api/report",
                {"relation": "force = mass * acceleration", "save": False},
            )
            plain = json.loads(body)
            expect(
                status == 200 and plain["files"] == [] and plain["bundle"] is None,
                "save=false writes nothing",
            )

            # -- failure paths -------------------------------------------
            status, body = request(base + "/api/report", {"relation": "velocity = ("})
            bad = json.loads(body)
            expect(status == 400 and bad.get("ok") is False, "broken £ returns a 400 with ok=false")

            status, _ = request(base + "/api/report", {"relation": ""})
            expect(status == 400, "empty relation is rejected")

            status, body = request(base + "/api/nope", {})
            expect(status == 404, "unknown API route is 404")

            # -- GET API (used by the page through the preview proxy) ----
            status, body = request(
                base + "/api/report?" + urllib.parse.urlencode({
                    "relation": "velocity = (2 * energy / mass)^(1/2)",
                    "top": 3,
                    "save": 0,
                })
            )
            get_report = json.loads(body)
            expect(
                status == 200 and bool(get_report.get("id")) and get_report["files"] == [],
                "GET report returns a cached id without writing files",
            )

            status, body = request(
                base + "/api/eval?" + urllib.parse.urlencode([
                    ("id", get_report["id"]),
                    ("ticks", 1),
                    ("set", "energy:8"),
                    ("set", "mass:1"),
                ])
            )
            get_run = json.loads(body)
            expect(
                status == 200 and get_run["rows"][0]["values"].get("velocity") == "[4]",
                "GET eval runs the cached material exactly",
            )

            status, body = chunked_request(
                base + "/api/report",
                {"relation": "force = mass * acceleration", "save": False},
            )
            chunked = json.loads(body)
            expect(
                status == 200 and chunked.get("ok") is True and len(chunked["dag"]) == 1,
                "chunked POST body is decoded",
            )

            # -- wheel browser -------------------------------------------
            status, body = request(base + "/api/wheels")
            wheel_index = json.loads(body)
            expect(
                status == 200 and wheel_index["total_wheels"] == 39
                and len(wheel_index["wheels"]) == 39
                and wheel_index["total_axioms"] == 98
                and wheel_index["total_cases"] == 153
                and wheel_index["total_spokes"] == 366,
                "wheel index lists the full substrate with derived spokes",
            )
            expect(
                wheel_index["reserved"] == ["W30", "W31"],
                "reserved wheel numbers are explicit",
            )
            status, body = request(base + "/api/wheels/W1")
            wheel = json.loads(body)["wheel"]
            expect(
                status == 200 and wheel["title"] == "DC Ohm and power"
                and len(wheel["axioms"]) == 2
                and len(wheel["spokes"]) == 12,
                "wheel detail loads W1 axioms and spokes",
            )
            status, body = request(base + "/api/wheels/W38")
            new_wheel = json.loads(body)["wheel"]
            expect(
                status == 200 and new_wheel["title"] == "Gears & Mechanical Transmissions"
                and len(new_wheel["axioms"]) == 4
                and new_wheel["spoke_count"] == 28
                and any(spoke["target"] == "output_power" for spoke in new_wheel["spokes"]),
                "new transducer wheel loads with its derived spokes",
            )
            status, body = request(base + "/api/wheels/W36")
            w36 = json.loads(body)["wheel"]
            expect(
                status == 200 and len(w36["axioms"]) == 2 and len(w36["cases"]) == 4,
                "W36 detail matches its file, not stale index counts",
            )
            w39 = next(item for item in wheel_index["wheels"] if item["id"] == "W39")
            expect(
                "permeance" in w39["keywords"] and w39["n_spokes"] > 0,
                "wheel listings carry searchable axiom text and spoke counts",
            )
            status, body = request(base + "/api/wheels/W41")
            w41 = json.loads(body)["wheel"]
            expect(
                status == 200 and len(w41["axioms"]) == 3 and w41["spoke_count"] == 9,
                "thermoelectric wheel derives its spoke table",
            )
            status, body = request(base + "/api/wheels/W26")
            w26 = json.loads(body)["wheel"]
            status27, body27 = request(base + "/api/wheels/W27")
            w27 = json.loads(body27)["wheel"]
            expect(
                status == 200
                and status27 == 200
                and w26["title"] == "Astrophysics & Stellar Structure"
                and w26["family"] == "Astrophysics & cosmology"
                and len(w26["axioms"]) == 4
                and len(w26["cases"]) == 5
                and w27["title"] == "Cosmology & Cosmic Expansion"
                and w27["family"] == "Astrophysics & cosmology"
                and w27["spoke_count"] == 30,
                "astrophysics and cosmology wheels load in the browser",
            )
            status, _ = request(base + "/api/wheels/W99")
            expect(status == 400, "unknown wheel is rejected")

            # -- concept map ---------------------------------------------
            status, body = request(base + "/api/concepts")
            catalogue = json.loads(body)["catalogue"]
            expect(
                status == 200 and catalogue["total"] == 41
                and catalogue["composite"] == 12,
                "concept catalogue lists 41 contracts",
            )
            status, body = request(base + "/api/concepts?q=delta-sigma")
            concept = json.loads(body)
            expect(
                status == 200 and concept["matched"]
                and concept["method"]["id"] == "delta_sigma_modulator",
                "delta-sigma maps to its exact contract",
            )
            physical = next(
                branch for branch in concept["branches"] if branch["key"] == "physical"
            )
            expect(
                any(child["status"] == "pass" for child in physical["children"]),
                "delta-sigma tree records simulation evidence",
            )
            status, body = request(base + "/api/concepts?q=zzzz")
            unknown = json.loads(body)
            expect(
                status == 200 and unknown["matched"] is False,
                "unknown concept is not invented",
            )

            # -- method discovery ------------------------------------------
            query = urllib.parse.quote(
                "compute an irrational value with an analog method"
            )
            status, body = request(base + "/api/discover?q=" + query)
            found = json.loads(body)
            primitives = {method["primitive"] for method in found.get("methods", [])}
            expect(
                status == 200 and found.get("schema") == "cent-discovery/1"
                and "delta_sigma_modulator" in primitives and "sqrt" in primitives,
                "discovery endpoint returns delta-sigma and square-root methods",
            )
            delta = next(
                (method for method in found.get("methods", [])
                 if method.get("primitive") == "delta_sigma_modulator"),
                {},
            )
            expect(
                (delta.get("route_model") or {}).get("schema") == "cent-route/1"
                and (delta.get("route_simulation") or {}).get("passed") is True,
                "discovery API carries the exact typed route and simulation",
            )
            sqrt = next(
                (method for method in found.get("methods", [])
                 if method.get("primitive") == "sqrt"
                 and method.get("route_simulation") is not None),
                {},
            )
            expect(
                (sqrt.get("route_simulation") or {}).get("passed") is True,
                "discovery API carries the certified sqrt route",
            )
            sequence_query = urllib.parse.quote(
                "compute a square root, then carry the result as a bitstream"
            )
            status, body = request(
                base + "/api/discover?q=" + sequence_query + "&limit=50"
            )
            sequence = json.loads(body)
            expect(
                status == 200 and sequence.get("multi_step") is True
                and len(sequence.get("steps", [])) == 2,
                "discovery API returns the ordered multi-step goal",
            )
            expect(
                all(
                    step.get("status") == "pass" and step.get("method_count", 0) > 0
                    for step in sequence.get("steps", [])
                ),
                "both discovery steps return candidate methods",
            )
            expect(
                any("no declared handoff" in gap for gap in sequence.get("gaps", [])),
                "discovery API keeps the step handoff gap explicit",
            )
            status, _ = request(base + "/api/discover")
            expect(status == 400, "discovery requires a problem statement")

            # -- constrained design API -----------------------------------
            status, body = request(base + "/api/design")
            catalog = json.loads(body)
            spaces = {item["route"]: item for item in catalog.get("spaces", [])}
            expect(
                status == 200 and catalog.get("schema") == "cent-design/1"
                and set(spaces) == {"delta-sigma", "sqrt-log", "sqrt-feedback"}
                and len(spaces["delta-sigma"]["options"]) == 4
                and len(spaces["sqrt-log"]["options"]) == 4
                and len(spaces["sqrt-feedback"]["options"]) == 3,
                "design endpoint exposes all declared alternatives",
            )

            status, body = request(
                base + "/api/solve?" + urllib.parse.urlencode({
                    "route": "sqrt-log",
                    "range": "1/2:1",
                })
            )
            solved = json.loads(body)
            solving = solved.get("design") or {}
            expect(
                status == 200 and solving.get("status") == "solved"
                and (solving.get("selected") or {}).get("option", {}).get("name")
                == "precision-20"
                and len(solving.get("candidates", ())) == 4,
                "GET solve selects the range-safe declared design",
            )
            expect(
                (solving.get("ranking") or {}).get("profile") == "exact-static"
                and (solving.get("ranking") or {}).get("front")
                == ["precision-20", "precision-32", "precision-64"]
                and (solving.get("selected") or {}).get("pareto_rank") == 1,
                "GET solve carries the exact Pareto front and candidate rank",
            )
            expect(
                any(
                    step.get("name") == "Reference netlist / floorplan"
                    and step.get("status") == "pass"
                    and "physical" in (step.get("command") or "")
                    for step in solving.get("verification_plan", ())
                ),
                "design API points at the reference netlist/floorplan emitter",
            )

            status, body = request(
                base + "/api/solve?" + urllib.parse.urlencode({
                    "route": "sqrt-feedback",
                    "min_bandwidth": "100000",
                })
            )
            bandwidth_solved = json.loads(body).get("design") or {}
            expect(
                status == 200
                and bandwidth_solved.get("status") == "solved"
                and (bandwidth_solved.get("constraints") or {})
                .get("min_bandwidth")
                == {"num": "100000", "den": "1"}
                and (bandwidth_solved.get("selected") or {})
                .get("bandwidth", {})
                .get("slowest", {})
                .get("symbol")
                == "tau_cl",
                "GET solve applies the exact declared-pole bandwidth constraint",
            )
            expect(
                (bandwidth_solved.get("ranking") or {}).get("profile")
                == "dynamic-aware"
                and [
                    item.get("name")
                    for item in (bandwidth_solved.get("ranking") or {}).get(
                        "objectives", ()
                    )
                ]
                == ["cost", "max_relative_error", "certified_bandwidth"],
                "a bandwidth request selects the dynamic-aware Pareto profile",
            )
            status, body = request(
                base + "/api/solve?route=sqrt-log&ranking=weighted"
            )
            expect(
                status == 400 and json.loads(body).get("ok") is False,
                "design API rejects an unknown ranking profile",
            )

            status, body = request(base + "/api/compare")
            compared = json.loads(body).get("comparison") or {}
            expect(
                status == 200
                and compared.get("schema") == "cent-comparison/1"
                and compared.get("routes")
                == ["delta-sigma", "sqrt-log", "sqrt-feedback"]
                and compared.get("solved_count") == 3
                and len(compared.get("rows", ())) == 3,
                "comparison API solves all declared routes independently",
            )
            expect(
                compared.get("profile") == "exact-static"
                and compared.get("markdown", "").startswith("# Method comparison")
                and "cross-route scalar" in compared.get("note", ""),
                "comparison API carries per-route ranks and export text",
            )
            status, body = request(
                base + "/api/compare?" + urllib.parse.urlencode({
                    "routes": "sqrt-log,delta-sigma",
                    "range": "1/2:1",
                })
            )
            shared_compare = json.loads(body).get("comparison") or {}
            expect(
                status == 200
                and shared_compare.get("routes") == ["sqrt-log", "delta-sigma"]
                and all(
                    row.get("constraints", {}).get("input_range")
                    == {"min": {"num": "1", "den": "2"},
                        "max": {"num": "1", "den": "1"}}
                    for row in shared_compare.get("rows", ())
                ),
                "comparison API applies shared range constraints in route order",
            )
            status, body = request(
                base + "/api/compare",
                {"routes": "sqrt-feedback,sqrt-log", "min_bandwidth": "1000"},
            )
            bandwidth_compare = json.loads(body).get("comparison") or {}
            expect(
                status == 200
                and bandwidth_compare.get("profile") == "dynamic-aware"
                and [
                    item.get("name")
                    for item in bandwidth_compare.get("results", {})
                    .get("sqrt-feedback", {})
                    .get("ranking", {})
                    .get("objectives", ())
                ]
                == [
                    "cost",
                    "max_relative_error",
                    "certified_bandwidth",
                ],
                "comparison API exposes the dynamic-aware profile per route",
            )
            status, body = request(
                base + "/api/compare?routes=sqrt-log,unknown-route"
            )
            expect(
                status == 400 and json.loads(body).get("ok") is False,
                "comparison API rejects an unknown route",
            )

            status, body = request(
                base + "/api/solve",
                {"route": "sqrt-log", "min_bandwidth": "100000"},
            )
            bandwidth_gap = json.loads(body).get("design") or {}
            expect(
                status == 200
                and bandwidth_gap.get("status") == "gap"
                and bandwidth_gap.get("selected") is None
                and any(
                    "bandwidth:" in failure
                    for candidate in bandwidth_gap.get("candidates", ())
                    for failure in candidate.get("failures", ())
                ),
                "design API rejects the slower log pole with its exact reason",
            )

            status, body = request(
                base + "/api/physical?route=sqrt-feedback&min_bandwidth=100000"
            )
            bandwidth_physical = (json.loads(body).get("physical") or {})
            expect(
                status == 200
                and bandwidth_physical.get("selected", {}).get("option")
                == "gain-1000000"
                and (bandwidth_physical.get("constraints") or {})
                .get("min_bandwidth")
                == {"num": "100000", "den": "1"},
                "physical API propagates the declared-pole bandwidth constraint",
            )

            status, body = request(
                base
                + "/api/dynamics?route=sqrt-feedback&min_bandwidth=100000&samples=8"
            )
            bandwidth_dynamic = (json.loads(body).get("dynamics") or {})
            expect(
                status == 200
                and bandwidth_dynamic.get("selected_option") == "gain-1000000"
                and len(bandwidth_dynamic.get("trace", ())) == 8,
                "dynamics API propagates the declared-pole bandwidth constraint",
            )

            status, body = request(base + "/api/physical?route=delta-sigma")
            emitted = json.loads(body)
            expect(
                status == 200 and emitted.get("schema") == "cent-physical/1"
                and len(emitted.get("physical", {}).get("parts", [])) == 10
                and "NOT A FABRICATION NETLIST" in emitted["physical"]["spice"],
                "GET physical emits the delta-sigma reference deck",
            )
            status, body = request(
                base + "/api/physical",
                {"route": "sqrt-log", "range": "1/2:1"},
            )
            emitted_log = json.loads(body)
            expect(
                status == 200
                and emitted_log["physical"]["selected"]["option"] == "precision-20"
                and len(emitted_log["physical"]["layout"]["blocks"]) == 4,
                "POST physical carries the selected design and schematic floorplan",
            )
            status, body = request(
                base + "/api/physical",
                {"route": "sqrt-feedback", "max_cost": "1"},
            )
            expect(
                status == 400 and json.loads(body).get("ok") is False,
                "physical refuses a constraint set with no selected design",
            )
            status, _ = request(base + "/api/physical")
            expect(status == 400, "physical requires a declared route")

            status, body = request(
                base + "/api/fabricate?route=sqrt-log&range=1/2:1"
            )
            fabricated = json.loads(body)
            expect(
                status == 200 and fabricated.get("schema") == "cent-fabrication/1"
                and fabricated.get("fabrication", {}).get("passed") is True
                and len(fabricated["fabrication"].get("footprints", [])) == 6,
                "GET fabricate derives declared geometry from the reference topology",
            )
            status, body = request(
                base + "/api/fabricate", {"route": "delta-sigma"}
            )
            fabricated_delta = json.loads(body).get("fabrication") or {}
            expect(
                status == 200
                and fabricated_delta.get("unrouted_nets")
                == ["level", "off", "ref", "thr"]
                and any(
                    "control label" in check.get("detail", "")
                    for check in fabricated_delta.get("checks", ())
                ),
                "fabrication reports single-pin behavioral control labels explicitly",
            )
            status, body = request(
                base + "/api/fabricate", {"route": "sqrt-feedback", "max_cost": "1"}
            )
            expect(
                status == 400 and json.loads(body).get("ok") is False,
                "fabricate refuses a constraint set with no selected design",
            )
            status, _ = request(base + "/api/fabricate")
            expect(status == 400, "fabricate requires a declared route")

            status, body = request(
                base + "/api/dynamics?route=delta-sigma&samples=32"
            )
            sampled = json.loads(body)
            dynamic = sampled.get("dynamics") or {}
            expect(
                status == 200 and sampled.get("schema") == "cent-dynamics/1"
                and dynamic.get("status") == "partial"
                and len(dynamic.get("trace", ())) == 32
                and dynamic.get("metrics", {}).get("mean")
                == {"num": "15", "den": "32"},
                "GET dynamics runs the sampled RC/clock model",
            )
            status, body = request(
                base + "/api/dynamics",
                {"route": "sqrt-log", "samples": "8"},
            )
            log_dynamic = (json.loads(body).get("dynamics") or {})
            expect(
                status == 200 and log_dynamic.get("status") == "partial"
                and len(log_dynamic.get("trace", ())) == 8
                and "nonlinear large-signal" in log_dynamic.get("model", "")
                and log_dynamic.get("trace", [{}])[0].get("time") is not None
                and log_dynamic.get("trace", [{}])[0].get("aux") is not None
                and (log_dynamic.get("certificates") or {})
                .get("bounded_state", {}).get("status") == "pass"
                and (log_dynamic.get("certificates") or {})
                .get("global_error", {}).get("status") == "gap",
                "dynamics runs the log-domain nonlinear transient and carries its certificates",
            )
            status, body = request(
                base + "/api/dynamics",
                {
                    "route": "sqrt-log",
                    "samples": "8",
                    "certificate_box": {
                        "v_log_hi": "1/10",
                        "v_out_hi": "1/10",
                    },
                },
            )
            boxed_log = (json.loads(body).get("dynamics") or {})
            expect(
                status == 200
                and boxed_log.get("status") == "gap"
                and (boxed_log.get("certificates") or {})
                .get("bounded_state", {})
                .get("source")
                == "caller-supplied box"
                and not (boxed_log.get("certificates") or {})
                .get("bounded_state", {})
                .get("trace_contained"),
                "POST dynamics exposes a too-small log certificate box as a gap",
            )
            status, body = request(
                base + "/api/dynamics?route=sqrt-feedback&samples=8"
            )
            feedback_dynamic = (json.loads(body).get("dynamics") or {})
            expect(
                status == 200 and feedback_dynamic.get("status") == "partial"
                and len(feedback_dynamic.get("trace", ())) == 8
                and feedback_dynamic.get("trace", [{}])[0].get("output") is not None,
                "dynamics runs the feedback-route nonlinear transient",
            )
            status, body = request(
                base + "/api/dynamics?route=sqrt-feedback&samples=8&v_hi=0.5"
            )
            boxed_feedback = (json.loads(body).get("dynamics") or {})
            expect(
                status == 200
                and boxed_feedback.get("status") == "gap"
                and (boxed_feedback.get("certificates") or {})
                .get("bounded_state", {})
                .get("source")
                == "caller-supplied box"
                and not (boxed_feedback.get("certificates") or {})
                .get("bounded_state", {})
                .get("trace_contained"),
                "GET dynamics exposes a too-small feedback certificate box as a gap",
            )
            status, _ = request(
                base + "/api/dynamics",
                {"route": "delta-sigma", "samples": "0"},
            )
            expect(status == 400, "dynamics rejects an out-of-range sample count")
            status, _ = request(base + "/api/dynamics")
            expect(status == 400, "dynamics requires a declared route")

            status, body = request(
                base + "/api/solve",
                {"route": "delta-sigma", "accuracy": "1/500"},
            )
            tight = json.loads(body).get("design") or {}
            expect(
                status == 200 and tight.get("status") == "solved"
                and (tight.get("selected") or {}).get("option", {}).get("name")
                == "offset-1/1000",
                "POST solve applies an exact accuracy constraint",
            )

            status, body = request(
                base + "/api/solve",
                {"route": "sqrt-feedback", "max_cost": "1"},
            )
            no_budget = json.loads(body).get("design") or {}
            expect(
                status == 200 and no_budget.get("status") == "gap"
                and no_budget.get("selected") is None
                and any(
                    "cost 2 exceeds" in failure
                    for candidate in no_budget.get("candidates", ())
                    for failure in candidate.get("failures", ())
                ),
                "design API returns no-solution with the exact cost rejection",
            )

            status, body = request(base + "/api/solve?route=not-a-route")
            expect(
                status == 400 and json.loads(body).get("ok") is False,
                "unknown design route is rejected",
            )
            status, _ = request(base + "/api/solve?route=sqrt-log&range=1")
            expect(status == 400, "malformed design range is rejected")
            status, _ = request(
                base + "/api/solve",
                {"route": "delta-sigma", "accuracy": 0.01},
            )
            expect(status == 400, "binary float constraints are rejected")

            status, _ = request(base + "/api/eval?id=deadbeef")
            expect(status == 400, "expired eval id is rejected")
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)

    total = PASS + FAIL
    print()
    print("=" * 78)
    print(f"BROWSER UI: {PASS}/{total} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
