#!/usr/bin/env python3
"""run19_docs.py — run 19 ledger + docs refresh (post-recycle edition).

Run 19 in two chapters: (a) the original session — oracle study, engine
v3, selftest PASS, wheel expansion, campaign lost to a sandbox recycle
at n~73; (b) the continuation — state restored from the GitHub repo
(frontier table rebuilt from submission.csv: 891 rows kept full
precision + 109 improved rows from the csv states; score 22.823536
exact; round-trip 0 issues), every run-19 script re-created and
re-validated, campaign re-launched with a new feasibility control.
Appends the campaign outcome from the ledger when present.
"""
import json
import os
import shutil

ROOT = "/home/z/my-project"
DL = os.path.join(ROOT, "download")
LED = os.path.join(ROOT, "workspace/push/cent_campaign19_results.json")

def main():
    led = {"run": 19,
     "date": "2026-11-05",
     "user_asks": [
       "1. GitHub repository updated with new and previously missing files",
       "2. updated cent_compiler now at squares_in_squares/workspace/"
       "cent_compiler_v12_2_ext (two together in the same repository)",
       "3. push harder on the cent_compiler — it is built to DISCOVER, not "
       "polish; wheels slim/light -> richer, more robust wheels -> better "
       "engine options"],
     "state_in": "frontier 22.823536 / 454 (repo synced; certs extracted)",
     "chapter_a_original_session": {
       "oracle_study": {
         "E1_basin": "0/10 at ALL noise levels — the settle-in channel cannot "
                     "even hold a known solution; explains why v2 failed "
                     "feasible containers",
         "E2_cold": "1/40 restarts found the n=5 pinwheel from cold random "
                    "seeds — DISCOVERY POWER CONFIRMED; v2's failure was "
                    "LATTICE SEEDING, not the channel",
         "E3_torsion": "0/40 strict; but a 1.8e-13 terminal state under the "
                       "finalize gate — the collective channel contributes "
                       "comparable jammed states",
         "precision_lessons": [
           "L-BFGS-B stalls at ~1e-8; the TRUE gate is packlib.finalize "
           "(scale+round absorbs terminal imprecision up to ~1e-5 — verified "
           "on stalled seeds: both became finds L 2.70711/2.70714 while "
           "non-solutions fail)",
           "LM hinge-form residuals (W41 complementarity): kept as "
           "best-effort quality pass; over-constraint avoided"]},
       "engine_v3": "RSA diverse seed (W45, W38/W39/W40 angle library) -> "
                    "pressure ramp with exact analytic gradient (W36/W37) "
                    "-> best-effort LM exactification -> packlib.finalize IS "
                    "THE GATE.  Selftest PASS (pinwheel rediscovered from "
                    "cold seeds without ever being shown it)",
       "wheel_expansion": "W38-W45; corpus 41 wheels / 100 axioms / 159 "
                          "cases; case_table 0 mismatches; 2 corpus bugs "
                          "fixed (W39 dependent axiom forcing cut_ratio=1; "
                          "W43 dimless temperature vs native H=1)"},
     "chapter_b_continuation": {
       "incident": "sandbox recycled mid-campaign (n~73/23 roots, honest 0s "
                   "so far) to a stale fork-era snapshot; run-19 files lost",
       "recovery": "GitHub repo (user-maintained) is the source of truth: "
                   "workspace/scripts/json/docs restored; certs.zip "
                   "extracted (324); frontier table REBUILT from "
                   "submission.csv — 891 rows kept at full precision with "
                   "original src (L matches the repo table), 109 improved "
                   "rows took the 12-dp csv states (src run18-frontier); "
                   "final_assembly round-trip: 0 issues, score 22.823536 "
                   "exact, 454/1000 beat grid",
       "substrate_reconstruction": "pressure_settle.py was sandbox-only; "
           "rebuilt from the packlib SAT contract.  Three real bugs found "
           "and fixed by the FD selftest: (1) binding axis selection used "
           "argmax (must be argmin — the binding axis is the SMALLEST "
           "margin); (2) angle cross-term signs in the four axis cases "
           "(owner-angle piece and v-axis variants); (3) NumPy fancy-index "
           "+= silently drops contributions for squares in several active "
           "pairs — replaced with np.add.at (a square in multiple "
           "overlapping pairs lost most of its gradient at n>=5; n=2 tests "
           "cannot catch this — no duplicate indices).  Final state: "
           "uniform total-derivative form; FD-vs-analytic <= 8e-8 at "
           "n=5/12/30; the pinwheel is an exact zero (f=2e-31)",
       "revalidation": "engine selftest PASS again (2/30 cold restarts, "
           "best L 2.707106782162); NEW feasibility control: n=12 at the "
           "exact grid size 4.0 redisCOVERED 4/12 (the engine finds the "
           "known grid packing at the exact size — validating campaign "
           "zeroes in advance; the first campaign lacked this control)",
       "wheel_expansion": "re-applied on the restored compiler: 41 wheels "
           "/ 100 axioms / 159 cases, case_table 0 mismatches; ext zip "
           "rebuilt (233KB)"},
     "revalidation_extra": {
       "n=10 @3.72": "1/24 rediscoveries, best L 3.719999566183 — the "
           "svg-record class (8 aligned + 2 at 45) found from cold seeds",
       "n=40 @6.84": "0/24 — the gobel a3b4 family (16 squares at 45) not "
           "found at this pressure; honest"},
     "deliverables": [
       "download/cent_compiler_v12_2_ext.zip — the extended compiler "
       "(41 wheels); sync to repo workspace/cent_compiler_v12_2_ext",
       "download/table.json + submission.csv — the frontier states",
       "download/run19_outcomes.json — this ledger",
       "scripts/: pressure_settle, oracle_basin, lm_exactify, "
       "cent_discovery, cent_campaign19, apply_campaign19, wheel_expand, "
       "restore_from_repo"]}
    
    # campaign outcome, if the ledger has finished
    if os.path.exists(LED):
        cl = json.load(open(LED))
        if cl.get("finished"):
            led["campaign19"] = {
                "roots": len(cl.get("roots", {})),
                "finds": cl.get("finds", []),
                "seconds": cl.get("total_seconds"),
                "selftest": cl.get("selftest"),
                "feasibility_control": cl.get("feasibility_control"),
                "verdict": ("applicable finds — see finds list" if cl.get("finds")
                            else "no applicable finds — the 23 gap-0 roots "
                                 "remain open; honest zeroes")}
        else:
            led["campaign19"] = {"status": "in progress or interrupted",
                                 "roots_done": len(cl.get("roots", {}))}
    
    json.dump(led, open(os.path.join(DL, "run19_outcomes.json"), "w"), indent=1)
    print("run19_outcomes.json saved")
    
    with open(os.path.join(DL, "README.md"), "a") as f:
        f.write("""
    
    # Run 19 (2026-11-05): the cent_compiler pushes on DISCOVERY
    
    User's diagnosis, confirmed by experiment: the Pressure-Settling Engine
    (v2) was born too fast to be the only/optimal one, and the wheels were
    too slim to compile better engines from.
    
    ## The oracle study — decisive
    
    - **E1**: perturb-and-settle fails 0/10 at every noise level — the
      local channel cannot even HOLD a known solution. This is why v2
      failed its feasible-container self-tests.
    - **E2**: cold random diverse seeds — a restart FOUND the n=5 pinwheel
      (terminal objective 6e-15). **The engine class has discovery power;
      v2's failure was its lattice seeding, not the channel.**
    - **E3**: collective torsion: strict 0/40, but a 1.8e-13 terminal state
      under the finalize gate — comparable jammed states.
    
    ## Engine v3
    
    RSA diverse seeding (W45 + W38/W39/W40 angle library) -> pressure ramp
    with exact analytic gradient (W36/W37) -> best-effort LM exactification
    (W41 complementarity hinge) -> **packlib.finalize as the gate**
    (scale+round absorbs ~1e-5 terminal imprecision).
    **Self-test PASS**: the pinwheel is REDISCOVERED from cold seeds
    without ever being shown the solution.
    
    ## The wheels (8 new; corpus 41 wheels / 100 axioms / 159 cases)
    
    W38 crystallography, W39 quasicrystal cut-project, W40 phyllotaxis,
    W41 jamming/isostaticity, W42 soft-core MD, W43 simulated annealing
    (real SI dims; temperature=H aligns with native), W44 Voronoi, W45 RSA.
    `case_table` validates all 159 rows with 0 mismatches.
    
    ## Continuation chapter (sandbox recycle mid-campaign)
    
    The sandbox was recycled to a stale snapshot at n~73/23 roots.  The
    GitHub repository (user-maintained) proved to be the source of truth:
    full state restored, the frontier table rebuilt from submission.csv
    (891 rows at full precision + 109 improved rows; score 22.823536 exact,
    round-trip 0 issues), every run-19 script re-created and re-validated.
    The substrate reconstruction surfaced and fixed three real bugs
    (argmax->argmin on the binding axis; angle cross-term signs; NumPy
    fancy-index += dropping multi-pair contributions — replaced with
    np.add.at).  Re-validation passed: engine selftest PASS (2/30, best L
    2.707106782162) plus a NEW feasibility control (n=12 at exact grid
    4.0: 4/12 rediscoveries) that the first campaign lacked.
    """)
    print("README updated")
    
    with open(os.path.join(ROOT, "REPRODUCE.md"), "a") as f:
        f.write("""
    
    ## A11. Run 19: discovery engines + the 8 discovery wheels
    
    ```bash
    # restore from the GitHub repo after a recycle (idempotent):
    python3 scripts/restore_from_repo.py
    # the discovery stack:
    python3 scripts/pressure_settle.py     # substrate selftest (FD + pinwheel)
    python3 scripts/oracle_basin.py        # the E1/E2/E3 oracle study
    python3 scripts/lm_exactify.py         # exactification selftest
    python3 scripts/cent_discovery.py      # engine v3 selftest (rediscovery)
    python3 scripts/cent_campaign19.py     # 23-root campaign (bg OK)
    python3 scripts/wheel_expand.py        # W38-W45 into the compiler
    python3 scripts/apply_campaign19.py    # apply finds (no-op if none)
    ```
    """)
    shutil.copy(os.path.join(ROOT, "REPRODUCE.md"),
                os.path.join(DL, "REPRODUCE.md"))
    print("REPRODUCE updated")


if __name__ == "__main__":
    main()
