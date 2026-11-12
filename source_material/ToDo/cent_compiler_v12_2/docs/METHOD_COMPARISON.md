# Cross-route method comparison

`cent compare` is an export layer over the exact declared design solver, not a
new solver. It solves each selected route independently under the same requested
constraints and keeps each route's own Pareto result. It does not invent a
cross-route scalar score, a measured preference or a physical winner.

A blank shared input leaves each route on its declared default input. If `input`
or `range` is supplied, it is applied to every selected route, so the requested
operating point must lie in each route's declared domain.

## Commands

```bash
# All three declared routes, each at its own default input
python3 cent compare

# Shared range and constraints
python3 cent compare --range 1/2:1 --accuracy 1/100

# A chosen subset, JSON export
python3 cent compare sqrt-log delta-sigma --json

# Markdown table export
python3 cent compare --markdown

# Dynamic-aware Pareto profile
python3 cent compare --min-bandwidth 1000 --ranking dynamic-aware
```

`--json` and `--markdown` are mutually exclusive; the default is a human-readable
table. The CLI accepts the same exact-rational constraint syntax as `cent solve`.

## Semantics

Every row is one independent `DesignResult`:

- hard constraints are applied independently per route;
- feasible candidates receive exact Pareto ranks within that route;
- exactly one selected option is reported per solved route;
- the comparison does not select a "best route";
- costs are declared complexity units, not prices, BOM cost or yield;
- profile selection follows the solver: `auto` becomes `dynamic-aware` only when
  a minimum bandwidth is requested.

Comparing all three at their defaults gives three solved rows:

| Route | Selected | Cost | Pareto rank |
|---|---|---:|---:|
| `delta-sigma` | `offset-1/200` | 1 | 1 |
| `sqrt-log` | `precision-8` | 1 | 1 |
| `sqrt-feedback` | `gain-1000000` | 2 | 1 |

Those ranks are within-route ranks. The selected designs are not claimed to be
interchangeable physical implementations.

## JSON payload

The endpoint and `--json` return:

```json
{
  "ok": true,
  "schema": "cent-comparison/1",
  "comparison": {
    "schema": "cent-comparison/1",
    "routes": ["delta-sigma", "sqrt-log", "sqrt-feedback"],
    "profile": "exact-static",
    "solved_count": 3,
    "rows": [],
    "results": {},
    "note": "...",
    "markdown": "# Method comparison\n...",
    "gaps": []
  }
}
```

`rows` contains compact per-route rows: status, selected option and cost,
maximum relative error, Pareto rank, front, constraints and gaps. `results`
contains the full `cent-design/1` result for each route. `markdown` is the
ready-to-save export.

## HTTP API

```text
GET  /api/compare
GET  /api/compare?routes=sqrt-log,delta-sigma&range=1/2:1
GET  /api/compare?min_bandwidth=1000&ranking=dynamic-aware
POST /api/compare  {"routes": "sqrt-feedback,sqrt-log", "min_bandwidth": "1000"}
POST /api/compare  {"routes": ["delta-sigma", "sqrt-log"], "accuracy": "1/500"}
```

`routes` is a comma-separated string or a JSON list. The other fields are
`input`, `range` (`MIN:MAX`), `accuracy`, `max_cost`, `min_bandwidth` and
`ranking`. Unknown routes and malformed ranges return HTTP 400 with the exact
reason.

## Browser

The **Method comparison** card in the Design tab provides route checkboxes,
shared request fields, a results table and two downloads:

- **Download comparison JSON** — the full `cent-comparison/1` payload;
- **Download comparison Markdown** — the `markdown` export from the same result.

Each route name in the table opens that route's declared design card.

## Limits

- No noise, drift, measured-parasitic or reliability objective is added.
- No route is ranked against another by a hidden scalar; costs and ranks remain
  route-scoped.
- The comparison is only as strong as each route's declared design space and
  binding.
- It is not a fabricated or measured method comparison.

## Tests

```bash
python3 tests/test_design.py    # 60/60, including comparison and CLI export
python3 tests/test_webui.py     # 92/92, including /api/compare
python3 tests/run_all.py        # 824/824 across the seventeen-suite gate
```
