"""
paths.py — Centralized path configuration for arc_agi_17
=========================================================
Replaces all hardcoded /home/z/my-project/scripts references.
All paths are derived from this file's location.

Usage:
    from paths import GMHGL_DIR, ARC_17_DIR, RESULTS_DIR, REPORTS_DIR, DATA_DIR
"""

from pathlib import Path

# This file lives in arc_agi_17/scripts/
SCRIPT_DIR = Path(__file__).resolve().parent

# arc_agi_17/ (the mission root)
ARC_17_DIR = SCRIPT_DIR.parent

# Repository root (GLM/)
REPO_ROOT = ARC_17_DIR.parent

# Key directories
GMHGL_DIR = REPO_ROOT / "GMHGL"
GLM_MACHINE_DIR = REPO_ROOT / "glm_machine"
LONG_TERM_MEMORY_DIR = REPO_ROOT / "long_term_memory"
DATA_OBJECT_DIR = REPO_ROOT / "data_object"

# arc_agi_17 subdirectories
DATA_DIR = ARC_17_DIR / "data"
TRAINING_DIR = DATA_DIR / "training"
RESULTS_DIR = ARC_17_DIR / "results"
REPORTS_DIR = ARC_17_DIR / "reports"

# Diverse puzzles directory (v27+)
PUZZLES_DIR = DATA_DIR / "puzzles"

# Key files
UBP_ENGINE = GMHGL_DIR / "ubp_unified_v5.py"
GLM_VOCAB = DATA_DIR / "glm_unified_vocab_compact.json"
CRG_EXPANDED = DATA_DIR / "glm_crg_expanded_edges.json"
CRG_MASSIVE = DATA_DIR / "glm_crg_massive_edges.json"
UNIFIED_RELATIONS = DATA_DIR / "glm_unified_relations.json"
GLM_STATE = RESULTS_DIR / "glm_state.json"
HEXCOLOUR_STATE = RESULTS_DIR / "hexcolour_addresses.json"
LTM_STATE = RESULTS_DIR / "ltm_state.json"

def setup_paths():
    """Add all necessary directories to sys.path. Call once at startup."""
    import sys
    for d in [str(GMHGL_DIR), str(GLM_MACHINE_DIR), str(SCRIPT_DIR)]:
        if d not in sys.path:
            sys.path.insert(0, d)
    # Create directories if they don't exist
    for d in [RESULTS_DIR, REPORTS_DIR, PUZZLES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def verify_paths():
    """Check that critical paths exist. Returns list of missing paths."""
    missing = []
    for name, path in [
        ("UBP Engine", UBP_ENGINE),
        ("GLM Vocab", GLM_VOCAB),
        ("Training Dir", TRAINING_DIR),
    ]:
        if not path.exists():
            missing.append(f"  {name}: {path}")
    return missing
