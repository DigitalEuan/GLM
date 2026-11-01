"""Re-formulated GLM queries that CARRY Rule 30 data into the GLM's
analytical machinery.

The previous round of queries (data/glm_outputs.md) was informationally
flat: "describe rule 30" gives a refusal because Rule 30 is not a carrier.
This round engages the GLM's actual machinery -- the `real` query kind
(dyadic tower, one-bit modulator), the `compare` query kind (exact
rational inequality), the `verify` query kind (dimensional consistency),
and the `describe` query on the GLM's actual mathematics carriers --
by passing concrete Rule 30 numbers and bit patterns as operands.

The Lorentzian lift study (uploaded by the user) shows the principle:
a query that carries information gets a substantive three-column trace;
a query that asks for information the GLM does not have gets a flat
refusal. Round 2 fixes the flat queries.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/z/my-project/glm_repo")
OUT = Path("/home/z/my-project/data/glm_outputs_v2.md")

# Load the analysis JSONs to splice concrete numbers into the queries
import json
DATA = Path("/home/z/my-project/data")
P2 = json.loads((DATA / "p2_frequency.json").read_text())
P3 = json.loads((DATA / "p3_complexity.json").read_text())
GLM_SUB = json.loads((DATA / "glm_substrate.json").read_text())

# Concrete numbers to pass to the GLM
FREQ = P2["running_frequency"]["final_freq"]           # 0.500768
FREQ_DEV = P2["running_frequency"]["deviation_from_half"]  # 0.000768
N = P2["running_frequency"]["final_N"]                  # 1,000,000
Z = P2["running_frequency"]["z_score"]                  # 1.54
N_ONES = P2["single_bit_chi_square"]["n_ones"]          # 500768
GOLAY_HITS = GLM_SUB["golay_codeword_rate"]["n_hits"]  # 8
GOLAY_WINDOWS = GLM_SUB["golay_codeword_rate"]["n_windows"]  # 41666
GOLAY_EXP = GLM_SUB["golay_codeword_rate"]["expected_rate_per_window"]  # 0.000244
HEXACODE_HITS = GLM_SUB["hexacode_rate"]["n_hits"]     # 1296
HEXACODE_EXP = GLM_SUB["hexacode_rate"]["expected_rate_per_window"]  # 0.015625
ANF_DEG_5 = P3["anf_degree"]["table"][4]["anf_degree"]  # = 9 for n=5
LEECH_MIN = GLM_SUB["leech_distance"]["min_distance_sq"]  # 13

QUERIES = [
    # --- The empirical Rule 30 frequency, treated as a rational carrier ---
    ("approximate 500768/1000000",
     "Pass the empirical Rule 30 frequency (500768 ones in 10^6 cells) as a "
     "rational number to the GLM's `real` machinery. The GLM holds it as a "
     "carrier (since it IS rational), runs the dyadic tower, and applies the "
     "one-bit modulator with its machine-checked error bound."),
    ("real value 0.500768",
     "Same as above but in decimal notation. The GLM's parser accepts both."),
    ("real value 1/2",
     "The H_0 limit (asymptotic frequency conjectured to be 1/2). The GLM "
     "holds 1/2 as a carrier and reports its dyadic tower levels."),
    ("compare 500768/1000000 greater than 1/2",
     "Strict inequality: empirical Rule 30 frequency vs. the conjectured "
     "limit. The `compare` query kind is decidable when the inequality is "
     "strict -- the GLM should return 'greater than' with exact rational "
     "evidence."),
    ("compare 500768/1000000 less than 0.51",
     "Sanity-check upper bound on the empirical frequency."),
    ("compare 500768/1000000 greater than 0.4999",
     "Sanity-check lower bound. Together with the previous, this brackets "
     "the empirical frequency to (0.4999, 0.51)."),

    # --- The deviation from 1/2, as a process ---
    ("approximate 768/1000000",
     "The deviation |f - 1/2| = 768/10^6 as a rational. The GLM should hold "
     "it as a carrier and give its dyadic tower."),
    ("compare 768/1000000 less than 1/1000",
     "Is the empirical deviation within 0.1%? Yes, since 0.000768 < 0.001. "
     "The GLM should return 'less than' with exact rational evidence."),
    ("compare 768/1000000 less than 1/sqrt(1000000)",
     "Compare the empirical deviation to the IID standard error 1/(2*sqrt(N)). "
     "Note 1/sqrt(N) = 1/1000 = 0.001; the empirical deviation 0.000768 < 0.001 "
     "is below the SE under H_0, consistent with the non-rejection of H_0."),

    # --- Concentration bounds ---
    ("compare 2*exp(-2*1000000*(768/1000000)^2) less than 1",
     "Hoeffding bound on the empirical deviation: P(|f-1/2| > 0.000768) <= "
     "2*exp(-2*10^6*(0.000768)^2). We ask the GLM to compare this to 1 "
     "(which is trivially true) -- the point is that the GLM computes the "
     "exponential exactly via its process machinery."),

    # --- The dyadic tower of the empirical frequency ---
    ("real value 0.500768 - 1/2",
     "The deviation as a real number, for the GLM to expand into its dyadic "
     "tower. The first non-zero bit of the tower is at level 11 (since "
     "0.000768 = 768/10^6 < 2^-10 = 1/1024, and 2^-11 = 1/2048 < 0.000768), "
     "so the GLM should show that the level-0 through level-10 carriers are "
     "all 0, and the level-11 carrier is non-zero."),

    # --- ANF degree as an integer carrier ---
    ("describe 9",
     "The ANF degree of a(5) is 9. The GLM should describe 9 as a number "
     "(an integer carrier in the SI7 layer). This is a flat probe -- the "
     "GLM does not have an ANF-degree query kind -- but we record the "
     "baseline."),
    ("compare 9 greater than 5",
     "Sanity check: is the ANF degree of a(5) (= 9) greater than n=5? Yes, "
     "consistent with our finding that deg(a(n)) = 2n-1 > n."),

    # --- The Leech minimal vector count as a carrier ---
    ("describe 196560",
     "196560 is the number of Leech lattice minimal vectors (norm^2 = 4). "
     "The GLM should describe this number as a carrier."),
    ("describe 4096",
     "4096 is the number of Golay-24 codewords. The GLM should describe "
     "this number as a carrier."),
    ("compare 8 less than 11",
     "Sanity check on the Golay codeword rate: empirical 8 hits vs expected "
     "10.16 (which we round to 11). 8 < 11 is the comparison."),

    # --- The Rule 30 ANF degree pattern: 2n-1 ---
    ("verify 9 = 2*5 - 1",
     "Verify the ANF degree pattern: deg(a(5)) = 9 = 2*5 - 1. The GLM's "
     "`verify` query kind should check this integer equality exactly."),
    ("verify 11 = 2*6 - 1",
     "Verify the same pattern at n=6: deg(a(6)) = 11 = 2*6 - 1."),

    # --- The empirical chi-square statistic ---
    ("approximate 2.3593",
     "The chi-square statistic from the single-bit test (2.3593) as a real "
     "value. The GLM should give its dyadic tower."),
    ("compare 2.3593 less than 3.841",
     "Compare the chi-square statistic to the 5% critical value (3.841 for "
     "1 d.o.f.). 2.3593 < 3.841 is true, so we fail to reject H_0."),

    # --- The z-score ---
    ("approximate 1.5360",
     "The z-score (1.5360) as a real value."),
    ("compare 1.5360 less than 1.96",
     "Compare the z-score to the 5% two-tailed critical value (1.96). "
     "1.5360 < 1.96 is true, so we fail to reject H_0."),

    # --- Golay codeword hit count ---
    ("real value 8/41666",
     "The empirical Golay codeword hit rate (8 hits / 41666 windows). "
     "The GLM should hold this as a rational carrier."),
    ("compare 8/41666 less than 1/4096",
     "Is the empirical hit rate below the expected uniform rate? "
     "8/41666 = 0.00019199 < 1/4096 = 0.00024414 -- yes, the empirical "
     "Golay codeword rate is slightly below the random expectation (8 vs "
     "10.16 expected), well within Poisson fluctuation."),

    # --- Hexacode hit rate ---
    ("real value 1296/83333",
     "The empirical hexacode hit rate."),
    ("compare 1296/83333 less than 1/64",
     "Compare the empirical hexacode rate to the expected 1/64 = 0.015625. "
     "1296/83333 = 0.015552 < 0.015625 -- slightly below, within 0.5%."),

    # --- The Leech distance floor ---
    ("compare 13 greater than 4",
     "The minimum squared distance from a Rule 30 binary window to a Leech "
     "minimal vector is 13. The Leech lattice's own minimal squared norm is "
     "4. 13 > 4 confirms Rule 30 windows are NOT Leech lattice points."),

    # --- The Lorentzian lift idea ---
    # The user's attachment proposes lifting the GLM's ambiguous 24-bit
    # space to II_{25,1}. The key identity is <L(x), r_lambda> = 1 - |x-lambda|^2/2.
    # We probe whether the GLM has any existing awareness of this.
    ("describe 25",
     "25 is the spatial dimension of the Lorentzian lift II_{25,1}. The "
     "GLM should describe this number as a carrier."),
    ("describe 70",
     "70 is the time-norm of the Weyl vector (0,1,...,24|70) of II_{25,1}. "
     "The GLM's substrate_cognition has lorentzian_experiment which verifies "
     "1^2+2^2+...+24^2 = 70^2 (a Pythagorean identity). We probe whether the "
     "GLM has 70 as a carrier."),

    # --- Pi (analogue for Problem 2) ---
    ("irrational pi",
     "The direct analogue to Rule 30's center column: the binary digits of "
     "pi are also conjectured normal but no proof exists. The GLM's `real` "
     "query treats pi as a process (a converging sequence of rational "
     "carriers), exactly the substrate-native distinction."),
    ("approximate pi/4",
     "The first BBP-spigot-friendly sub-expression. The GLM should compute "
     "pi/4 to 20 places as a process."),

    # --- The Rule 30 ANF degree sequence ---
    ("verify 3 = 2*2 - 1",
     "deg(a(2)) = 3 = 2*2-1."),
    ("verify 5 = 2*3 - 1",
     "deg(a(3)) = 5 = 2*3-1."),
    ("verify 7 = 2*4 - 1",
     "deg(a(4)) = 7 = 2*4-1."),

    # --- The engine's empirical bit-ops rate ---
    ("approximate 6.5e9",
     "The engine's measured throughput: 6.5 * 10^9 bit-operations per second "
     "at n = 10^5. We ask the GLM to treat this as a real value."),
]


def run_glm(query: str, mode: str = "--plan") -> str:
    cmd = ["python3", "GLM.py", "--no-banner", mode, "-q", query, "-f", "markdown"]
    try:
        out = subprocess.run(cmd, cwd=str(REPO), capture_output=True,
                              text=True, timeout=60)
        return out.stdout + out.stderr
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after 60s on: {query!r}]"
    except Exception as e:
        return f"[ERROR {e!r} on: {query!r}]"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# GLM queries (round 2): informationally rich",
             "",
             "All outputs verbatim from `python3 GLM.py --plan -q '...' -f markdown`,",
             "run on the live DigitalEuan/GLM repository (clone at",
             "`/home/z/my-project/glm_repo`, version 5.37 per README).",
             "",
             "The `--plan` flag selects the typed planner surface, which routes",
             "through `glm_universal.runtime.parser` and",
             "`glm_universal.runtime.session` only. The default multi-surface",
             "router (K1, Phase 89) has an `ImportError` on the respell/sinter",
             "fallback that triggers only on a refusal; using `--plan` avoids",
             "that path entirely.",
             "",
             "Unlike round 1, these queries CARRY Rule 30 data into the GLM's",
             "analytical machinery: the empirical frequency as a rational",
             "carrier, the chi-square statistic, the z-score, the ANF-degree",
             "integer pattern (deg(a(n)) = 2n-1), the Golay/hexacode hit rates,",
             "the Leech lattice distance floor. The GLM's `real` machinery",
             "(dyadic tower, one-bit modulator, machine-checked error bound)",
             "and `compare` machinery (exact rational inequality) are engaged",
             "substantively.",
             ""]
    t0 = time.time()
    for q, rationale in QUERIES:
        print(f"[glm-v2] querying ({len(q)} chars): {q!r}", flush=True)
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
    print(f"[glm-v2] wrote {len(QUERIES)} queries to {OUT} "
          f"({OUT.stat().st_size} bytes) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
