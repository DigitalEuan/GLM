"""grammar package — public re-exports."""
from .phi_grammar_arc import (
    PhiGrammar, generate_candidates, grammar_size,
    PhiTuple, N_VALUES, K_SPATIAL, K_SCALAR, ARMS, LAYERS, C_PREFIXES, CORRECTIONS,
)
from .direct_candidates import generate_direct_candidates

__all__ = [
    "PhiGrammar", "generate_candidates", "grammar_size",
    "PhiTuple", "N_VALUES", "K_SPATIAL", "K_SCALAR", "ARMS", "LAYERS",
    "C_PREFIXES", "CORRECTIONS",
    "generate_direct_candidates",
]
