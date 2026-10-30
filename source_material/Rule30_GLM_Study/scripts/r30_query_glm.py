"""Query the live GLM (Geometric Language Machine) on Rule-30-relevant
carriers, and save the verbatim three-column traces to a markdown file for
quotation in the study.

Each query is run through `python3 GLM.py --plan` (the typed planner surface)
so we avoid the multi-surface router, which currently has an `ImportError`
in the respell fallback path when a query refuses. The typed planner is
sufficient for describing known carriers and answering verifications on
them.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/glm_repo")
OUT = Path("/home/z/my-project/data/glm_outputs.md")

QUERIES = [
    # Substrate-level carriers the GLM actually knows about. These are the
    # names registered in glm_universal/data_objects/mathematics.py.
    ("describe golay_codeword_0",
     "The all-ones Golay-24 codeword; the GLM places it at the origin of the "
     "Leech lattice and notes it is not a 2A axis of the Monster."),
    ("describe golay_codeword_1",
     "The weight-1 'basis' Golay codeword; useful as a window template "
     "against the Rule 30 center column."),
    ("describe golay_codeword_4095",
     "The all-zeros Golay-24 codeword, the additive identity."),
    ("describe leech_minimal_root",
     "The shortest nonzero vector in the Leech lattice Lambda_24. A 24-dim "
     "carrier whose projection is computed exactly in Fraction arithmetic."),
    ("describe axis_root_e0",
     "The unit basis vector e_0 in Q^24; a reflection root in the Co3 "
     "stabiliser."),
    ("describe rational_root_thirds",
     "A 24-dim root filled with 1/3 in every coordinate; the GLM computes "
     "its Griess norm <v,v> = (1/8) sum v_i^2 = 24/8 / 9 = ... exactly."),
    ("describe hexacode_word_0",
     "The first hexacode word over GF(4); the hexacode is the GF(4) "
     "construction spine of the Golay code and MOG."),
    # A verify query the planner can answer with the substrate.
    ("verify force = mass * acceleration",
     "A sanity-check dimensional verification. The GLM should confirm "
     "Newton's second law is dimensionally consistent."),
    # A puzzle query: the GLM has a 'task' / 'puzzle' verb.
    ("puzzle rule 30 center column periodicity",
     "Direct probe: does the GLM know about Rule 30? Expected behaviour: "
     "the parser returns 'unknown' or 'refusal' because Rule 30 is not in "
     "the GLM's registers. This is honest evidence the GLM does not have "
     "Rule 30 as a carrier."),
    ("describe rule 30",
     "Direct probe: does the GLM have 'rule 30' as a carrier?"),
    ("describe center column",
     "Direct probe: does the GLM have 'center column' as a carrier?"),
    # Real value query — the GLM treats irrational processes as carriers.
    ("approximate sqrt(2)",
     "The GLM's `real` query kind: an irrational number treated as a "
     "process, with a precise 2-adic / Stern-Brocot digit-stack computation "
     "underneath. Useful for Problem 2's comparison to digits of pi."),
    ("irrational pi",
     "Same `real` query kind, for pi. Useful for Problem 2's comparison "
     "between the Rule 30 center column and digits of pi (Wolfram's analogy)."),
    ("compare sqrt(2) bigger than 1.414",
     "The `compare` query kind: order two real values exactly. Decidable "
     "when the inequality is strict."),
    # Spatial query — the MOG grid the GLM uses for Golay decoding.
    ("spatial mog grid",
     "The `spatial` query kind: the GLM's Miracle Octad Generator grid, "
     "the GF(4) construction of the Golay-24 code."),
]


def run_glm(query: str, mode: str = "--plan") -> str:
    """Run a single GLM query, return stdout (incl. syntax warnings + trace)."""
    cmd = ["python3", "GLM.py", "--no-banner", mode, "-q", query, "-f", "markdown"]
    try:
        out = subprocess.run(
            cmd, cwd=str(REPO), capture_output=True, text=True, timeout=60
        )
        return out.stdout + out.stderr
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after 60s on: {query!r}]"
    except Exception as e:
        return f"[ERROR {e!r} on: {query!r}]"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# GLM queries on Rule-30-relevant carriers",
                        "",
                        "All outputs verbatim from `python3 GLM.py --plan -q "
                        "'...' -f markdown`, run on the live DigitalEuan/GLM "
                        "repository (clone at `/home/z/my-project/glm_repo`, "
                        "version 5.37 per README).",
                        "",
                        "The `--plan` flag selects the typed planner surface, "
                        "which routes through `glm_universal.runtime.parser` "
                        "and `glm_universal.runtime.session` only. The default "
                        "multi-surface router (K1, Phase 89) has an `ImportError` "
                        "on the respell/sinter fallback that triggers only on a "
                        "refusal; using `--plan` avoids that path entirely.",
                        ""]
    for q, rationale in QUERIES:
        print(f"[glm] querying: {q!r}", flush=True)
        out = run_glm(q)
        lines.append(f"## Query: `{q}`")
        lines.append("")
        lines.append(f"_Rationale._ {rationale}")
        lines.append("")
        lines.append("```markdown")
        lines.append(out.rstrip())
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"[glm] wrote {len(QUERIES)} queries to {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
