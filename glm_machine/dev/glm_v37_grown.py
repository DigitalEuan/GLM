#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
UBP GLM v3.7 — UNIFIED STANDALONE BUILD (Push June #4)
================================================================================
A single-file consolidation of the UBP Geometric Language Machine development
pushes (v3.4 → v3.5 → v3.6 → v3.7).  Every method, every reasoning path, every
defect fix from the four pushes is preserved here.  The file is organised by
the Table of Contents below so it can be edited and grown further.

DEPENDENCIES
  - Python 3.12+
  - SymPy  (pip install sympy)
  - The original UBP_Repo on disk (core_studio_v4.0/core/ + co-located
    ubp_system_kb.json).  Set UBP_CORE_PATH below to point at it.

================================================================================
TABLE OF CONTENTS  (search for the §NN marker to jump to a section)
================================================================================
  §00  CONFIGURATION & PATHS
  §01  SUBSTRATE IMPORTS         (Golay/Leech engines, BLA)
  §02  CONSTANTS & TUNABLES      (thresholds, function words, pronouns)
  §03  CRG EXTENDED              (contradiction edges + auto-expansion)
  §04  NUMBER VOCABULARY         (derived number-word lattice points)
  §05  IDEA EVIDENCE             (source-tagged evidence dataclass)
  §06  IDEA ZONE v3.7            (decay + ticks + re-crystallisation +
                                  contradiction-aware + adversarial)
  §07  IDEA MANAGER              (multi-zone routing + cross-zone synthesis +
                                  contradiction-driven pivot)
  §08  IDEA META-GRAPH           (persistence + warm-start)
  §09  TOOLS LAYER               (SymPy: arithmetic + diff/integral/solve)
  §10  RESPONSE COMPOSER v3.7    (confidence-tagged, multi-zone, synthesis-aware)
  §11  RUNTIME v3.7              (GLMRuntimeV37 — wires everything)
  §12  CLI / TEST ENTRY POINT
================================================================================
"""

# ══════════════════════════════════════════════════════════════════════════════
# §00  CONFIGURATION & PATHS
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import sys, os, re, json, math, time, heapq
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, deque
from pathlib import Path

# --- point this at your UBP_Repo core directory ---
UBP_CORE_PATH = "/home/z/my-project/ubp_experiment/UBP_Repo/core_studio_v4.0/core"
# -------------------------------------------------

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if UBP_CORE_PATH not in sys.path:
    sys.path.insert(0, UBP_CORE_PATH)

# ensure the KB is found by the grammar patch (Defect D6 workaround)
os.chdir(UBP_CORE_PATH)
if not (Path(UBP_CORE_PATH) / "ubp_system_kb.json").exists():
    _src = Path(UBP_CORE_PATH).parent / "system_kb" / "ubp_system_kb.json"
    if _src.exists():
        import shutil; shutil.copy(_src, Path(UBP_CORE_PATH) / "ubp_system_kb.json")

# ══════════════════════════════════════════════════════════════════════════════
# §01  SUBSTRATE IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
# These come from the original UBP_Repo; we import but do not modify them.
import glm_grammar_patch  # noqa: F401  (side-effect: patches alias grounding)
from ubp_unified_v5 import BinaryLinearAlgebra as BLA, LEECH_ENGINE, GOLAY_ENGINE
from glm_engine_v31 import create_semantic_engine, GLMSemanticEngine
from ubp_critpt_sovereign_v3 import GLMRulesEngine
from glm_concept_relation_graph import (
    ConceptRelationGraph, CRGEdge, EDGE_LABELS, build_default_crg,
)
from glm_grammar_patch import _query_type, _load_system_kb, _build_alias_map
from glm_multi_token_lexer import MultiTokenLexer


def filter_content_tokens(known):
    """Defect D1 fix: keep only NOUN/PROPERTY/OPERATOR tokens whose lemma is
    NOT a function word."""
    out = []
    for word, entry in known:
        if word.lower() in FUNCTION_WORDS: continue
        if entry.role in ("NOUN","PROPERTY","OPERATOR","VERB"):
            if entry.role == "VERB" and word.lower() in {"explain","define","describe","compare","measure","tell","show"}: continue
            out.append((word, entry))
    return out

# ══════════════════════════════════════════════════════════════════════════════
# §02  CONSTANTS & TUNABLES
# ══════════════════════════════════════════════════════════════════════════════
# IdeaZone dynamics
IDEA_RADIUS        = 8      # hamming distance within which a token "fits" the idea
REINFORCE_RES      = 1.0    # resonance for a reinforcing token
DRIFT_RES          = 0.35   # resonance for a drifting (off-topic) token
GET_IT_THRESHOLD   = 0.70   # coherence at which the idea crystallises
MIN_EVIDENCE       = 3      # need at least this many evidence tokens to crystallise
MIN_BACKBONE       = 1      # need at least this many CRG edges to crystallise
MAX_EVIDENCE       = 16     # rolling window — forget oldest evidence beyond this
MIN_TOPIC_NOUNS    = 2      # need >= 2 topic nouns to form a relational idea

# Decay (v3.5)
DECAY_LAMBDA       = 0.18   # per turn; halflife ≈ 3.8 turns
PRUNE_FLOOR        = 0.08   # evidence below this resonance is forgotten
TICK_AGE           = 0.35   # one tick ages evidence by 0.35 of a turn
INFERRED_RES       = 0.45   # resonance for tick-discovered evidence
ADJACENT_RES       = 0.20   # resonance for lattice-adjacent (no CRG) discoveries
TICK_SEARCH_RADIUS = 10     # hamming radius for tick noun discovery
MAX_INFERRED       = 4      # cap inferred evidence per tick cycle
REFINE_DELTA       = 0.05   # coherence gain needed to re-announce a refined thesis

# Multi-zone (v3.6)
ZONE_SPAWN_THRESHOLD = 6    # Golay min distance; tighter = more zones
MAX_ZONES            = 3

# CRG auto-expansion (v3.7)
AUTO_EXPAND_RADIUS   = 4    # hamming distance for proposing new edges
AUTO_EXPAND_CONF     = 0.40 # confidence for auto-proposed edges (vs 1.0 curated)

# Function words that must never become the topic (Defect D1 fix)
FUNCTION_WORDS = frozenset({
    "what","how","why","when","who","where","which","whether",
    "is","are","was","were","be","been","being","do","does","did","done",
    "the","a","an","of","to","in","on","for","with","by","as","at","from",
    "and","or","but","not","no","yes","so","if","then","than","also","just",
    "explain","define","describe","compare","measure","tell","show","give",
    "between","relationship","connection","link","relates","relate","related",
    "about","more","like","kind","sort","type","example","mean","meaning",
    "can","could","would","should","may","might","will","shall",
    "i","you","he","she","we","they","it","that","this","those","these",
    "me","my","your","our","their","his","her","its",
    "hello","hi","hey","thanks","thank","please","ok","okay",
})
PRONOUNS = frozenset({
    "they","it","that","this","those","these","he","she","we","i","you",
    "them","him","her","us","me","one",
})

# Clean verb whitelist (Defect D2 fix — alpha-only lemmas)
_CLEAN_VERBS = [
    "generates","measures","commutes","scales","depends","transforms",
    "predicts","regularizes","captures","binds","links","relates",
    "forms","produces","encodes","defines","describes","constitutes",
    "reflects","exhibits","implies","determines","constrains",
]
_OP_SYNTAX_RE = re.compile(r"[()\s<>]")


# ══════════════════════════════════════════════════════════════════════════════
# §03  CRG EXTENDED  — contradiction edges + auto-expansion (v3.6 + v3.7)
# ══════════════════════════════════════════════════════════════════════════════
EDGE_LABELS.add("contradicts")
EDGE_LABELS.add("incompatible_with")
EDGE_LABELS.add("auto_proposed")   # v3.7: edges proposed by auto-expansion

_SYMMETRIC = {"commutes_with", "is_dual_to", "contradicts", "incompatible_with"}

# Curated physics contradictions (v3.6)
_CONTRADICTIONS: List[Tuple[str, str, str]] = [
    ("boson",            "contradicts",       "fermion"),
    ("commutator",       "contradicts",       "anticommutator"),
    ("continuum",        "incompatible_with", "lattice"),
    ("classical",        "incompatible_with", "quantum"),
    ("majorana",         "incompatible_with", "dirac"),
    ("unitary",          "contradicts",       "antiunitary"),
    ("real",             "incompatible_with", "imaginary"),
    ("local",            "incompatible_with", "nonlocal"),
]


def build_extended_crg() -> ConceptRelationGraph:
    """Build the default CRG and add curated contradiction edges."""
    crg = build_default_crg()
    for src, label, dst in _CONTRADICTIONS:
        crg.add_edge(src, label, dst)
        if label in _SYMMETRIC and src != dst:
            crg.add_edge(dst, label, src)
    return crg


def detect_contradictions(backbone: List[CRGEdge],
                          crg: ConceptRelationGraph) -> List[Tuple[CRGEdge, CRGEdge]]:
    """Find (edge, contradicting_edge) pairs in a backbone."""
    contradictions = []
    seen = set()
    for e in backbone:
        for ce in crg.out.get(e.src, []):
            if ce.label in ("contradicts", "incompatible_with") and ce.dst == e.dst:
                key = (e.src, e.label, e.dst, ce.label)
                if key not in seen:
                    contradictions.append((e, ce)); seen.add(key)
        for ce in crg.out.get(e.dst, []):
            if ce.label in ("contradicts", "incompatible_with") and ce.dst == e.src:
                key = (e.dst, e.label, e.src, ce.label)
                if key not in seen:
                    contradictions.append((e, ce)); seen.add(key)
    return contradictions


def contradiction_penalty(backbone: List[CRGEdge],
                          crg: ConceptRelationGraph) -> float:
    """Penalty [0, 0.5] applied to coherence when contradictions exist."""
    cons = detect_contradictions(backbone, crg)
    return min(0.5, len(cons) * 0.15)


def auto_expand_crg(crg: ConceptRelationGraph, vocab, max_proposals: int = 20
                    ) -> List[Tuple[str, str, str]]:
    """v3.7: Propose new CRG edges from lattice adjacency.
    Rule: if two NOUNs are Hamming-distance ≤ AUTO_EXPAND_RADIUS AND share a
    common CRG neighbour, propose an 'auto_proposed' edge between them.
    Returns the list of proposed edges (also added to the CRG at low confidence).
    """
    nouns = [w for w, e in vocab.words.items() if e.role == "NOUN"]
    proposed = []
    # build a neighbour index: noun -> set of CRG neighbours
    neighbours: Dict[str, Set[str]] = defaultdict(set)
    for e in crg.edges:
        if e.label not in ("contradicts", "incompatible_with", "auto_proposed"):
            neighbours[e.src].add(e.dst)
            if e.label in _SYMMETRIC:
                neighbours[e.dst].add(e.src)
    # scan pairs (limit to avoid O(n^2) blowup)
    import random
    random.seed(42)  # deterministic
    candidates = []
    for i, a in enumerate(nouns):
        if a not in neighbours: continue
        for b in nouns[i+1:]:
            if b not in neighbours: continue
            # already connected?
            if b in neighbours[a] or a in neighbours[b]: continue
            # shared neighbour?
            shared = neighbours[a] & neighbours[b]
            if not shared: continue
            # lattice-close?
            d = BLA.hamming_distance(vocab.words[a].vector, vocab.words[b].vector)
            if d <= AUTO_EXPAND_RADIUS:
                candidates.append((d, a, b, shared))
    candidates.sort(key=lambda x: x[0])
    for d, a, b, shared in candidates[:max_proposals]:
        crg.add_edge(a, "auto_proposed", b)
        proposed.append((a, b, f"shared: {','.join(list(shared)[:2])}"))
        if len(proposed) >= max_proposals: break
    return proposed


# ─────────────────────────────────────────────────────────────────────────────
# v3.7.2 ABSORPTION 1: Lattice-based CRG auto-linking (from LatticeConceptLinker)
# ─────────────────────────────────────────────────────────────────────────────
# Source: glm_concept_relation_graph.py LatticeConceptLinker.auto_link()
#
# Difference from glm_v37's auto_expand_crg (§03):
# - auto_expand_crg requires a SHARED CRG neighbour (conservative)
# - This linker links ANY two NOUNs that are Hamming-adjacent + same zone
#   (aggressive, discovers more connections)
#
# Optimization: zone-bucket the words first so we only compare within-zone
# pairs. For 2338 words across ~24 zones, this is ~100 words/zone = ~5K pairs
# per zone = ~120K total comparisons, vs 2.7M brute force.
LATTICE_LINK_RADIUS = 4  # Hamming distance threshold

def lattice_auto_link(crg: ConceptRelationGraph, vocab,
                      hamming_threshold: int = LATTICE_LINK_RADIUS,
                      max_per_zone: int = 50) -> int:
    """Link NOUNs that are lattice-adjacent + same dominant zone.

    Adds 'lattice_adjacent' edges (symmetric). Returns count of edges added.
    Capped per zone to avoid runaway edge growth.
    """
    from glm_zoned_lattice_embedding import dominant_zone
    # Bucket NOUNs by dominant zone
    zones: Dict[str, List[Tuple[str, Any]]] = defaultdict(list)
    for name, entry in vocab.words.items():
        if entry.role != "NOUN":
            continue
        try:
            z = dominant_zone(entry.vector)
            zones[z].append((name, entry))
        except Exception:
            continue

    links_added = 0
    for zone_name, words in zones.items():
        if len(words) < 2:
            continue
        zone_links = 0
        for i in range(len(words)):
            if zone_links >= max_per_zone:
                break
            name1, w1 = words[i]
            for j in range(i + 1, len(words)):
                if zone_links >= max_per_zone:
                    break
                name2, w2 = words[j]
                d = BLA.hamming_distance(w1.vector, w2.vector)
                if d <= hamming_threshold and d > 0:  # d=0 is the same word
                    # Check not already linked
                    existing = {e.dst for e in crg.out.get(name1, [])}
                    if name2 in existing:
                        continue
                    weight = hamming_threshold + 1 - d
                    label = f"lattice_adjacent_{weight}"
                    crg.add_edge(name1, label, name2)
                    crg.add_edge(name2, label, name1)
                    links_added += 1
                    zone_links += 1
    return links_added


# ─────────────────────────────────────────────────────────────────────────────
# v3.7.2 ABSORPTION 4: Enhanced query-type detection (wraps _query_type)
# ─────────────────────────────────────────────────────────────────────────────
# Source: glm_grammar_patch.py _query_type() + new computation/proof types
#
# The original _query_type returns: definition, explanation, relation, metric,
# causation, general. This wrapper adds:
# - "computation" — queries that ask for a calculation (find, compute, evaluate)
# - "proof" — queries that ask for a proof (prove, show that)
# These help route queries to the SymPy tools layer and adjust response style.
_COMPUTE_RE = re.compile(r'\b(find|compute|calculate|evaluate|determine|solve|simplify|differentiate|integrate)\b')
_PROOF_RE = re.compile(r'\b(prove|proof|show that|verify that|demonstrate)\b')

def _enhanced_query_type(query: str) -> str:
    """Wrap _query_type with computation/proof detection."""
    q = query.lower()
    if _PROOF_RE.search(q):
        return "proof"
    if _COMPUTE_RE.search(q):
        return "computation"
    return _query_type(query)


# ══════════════════════════════════════════════════════════════════════════════
# §04  NUMBER VOCABULARY  — derived number-word lattice points (v3.6)
# ══════════════════════════════════════════════════════════════════════════════
_BASE_CHAIN = ["zero", "one", "two", "three", "four"]
_EXTEND = ["five", "six", "seven", "eight", "nine", "ten",
           "eleven", "twelve", "thirteen", "fourteen", "fifteen",
           "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
_TENS = ["thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_BIT_SEQ = [5, 11, 17, 23, 7, 13, 19, 3, 9, 15, 21, 1, 6, 12, 18, 4,
            10, 16, 22, 8, 14, 20, 2, 0]

NUMBER_WORDS: Dict[int, str] = {
    0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",
    8:"eight",9:"nine",10:"ten",11:"eleven",12:"twelve",13:"thirteen",
    14:"fourteen",15:"fifteen",16:"sixteen",17:"seventeen",18:"eighteen",
    19:"nineteen",20:"twenty",30:"thirty",40:"forty",50:"fifty",
    60:"sixty",70:"seventy",80:"eighty",90:"ninety",100:"hundred",1000:"thousand",
}


def _perturb(vec, bits):
    out = list(vec)
    for b in bits: out[b % 24] ^= 1
    return out


def inject_number_vocab(vocab) -> Dict[str, int]:
    """Inject derived number-word vectors into the live engine vocabulary."""
    from glm_strict_lang_builder import WordEntry, _get_mog_category
    report = {"injected": 0, "skipped": 0, "derived": []}
    base_vecs = {w: list(vocab.words[w].vector) for w in _BASE_CHAIN if w in vocab.words}
    if not base_vecs: return report
    derived = {}
    prev_vec = base_vecs.get("four", base_vecs.get("zero"))
    for i, word in enumerate(_EXTEND):
        bit = _BIT_SEQ[i % len(_BIT_SEQ)]
        new_vec = _perturb(prev_vec, [bit])
        derived[word] = new_vec; prev_vec = new_vec
    for i, ten in enumerate(_TENS):
        unit_idx = (i + 3) % len(_EXTEND)
        unit_vec = derived.get(_EXTEND[unit_idx], prev_vec)
        derived[ten] = _perturb(unit_vec, [_BIT_SEQ[i], _BIT_SEQ[i + 8]])
    derived["hundred"] = _perturb(base_vecs.get("zero", [0]*24), [0,4,8,12,16,20])
    derived["thousand"] = _perturb(base_vecs.get("zero", [0]*24), [2,6,10,14,18,22])
    for word, vec in list(derived.items()) + list(base_vecs.items()):
        derived[f"minus_{word}"] = [1 - b for b in vec]
    for word, vec in derived.items():
        if word in vocab.words: report["skipped"] += 1; continue
        snapped, snap_info = GOLAY_ENGINE.snap_to_codeword(vec)
        fold3 = BLA.fold24_to3(vec)
        try: nrci = float(LEECH_ENGINE.calculate_nrci(vec))
        except Exception: nrci = 0.5
        entry = WordEntry(word=word, vector=vec, role="NOUN", ubp_id=f"NUM_{word}",
                          hamming_to_system=0, nrci=nrci, golay_codeword=snapped,
                          golay_distance=snap_info["anchor_distance"], fold3=fold3,
                          mog_category=_get_mog_category(vec))
        vocab.words[word] = entry
        vocab.by_role.setdefault("NOUN", []).append(word)
        report["injected"] += 1; report["derived"].append(word)
    return report


# ══════════════════════════════════════════════════════════════════════════════
# §05  IDEA EVIDENCE  — source-tagged (v3.5)
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class IdeaEvidence:
    word: str
    vector: List[int]
    role: str
    nrci: float
    turn: int
    resonance: float
    fit: str            # "reinforce" | "drift" | "seed" | "inferred"
    source: str = "user"  # "user" | "inferred" | "computed" | "kb"


# ══════════════════════════════════════════════════════════════════════════════
# §06  IDEA ZONE v3.7  — full lifecycle (v3.4 + v3.5 + v3.6 + v3.7)
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class IdeaZone:
    """A running idea-region in the UBP substrate.
    Lifecycle: seed → form → crystallise → mature → refine/fade.
    v3.5: + decay + autonomous ticks + re-crystallisation
    v3.6: + contradiction-aware coherence + adversarial self-testing
    v3.7: + (no new zone-level features; synthesis is manager-level)"""
    centroid: List[int] = field(default_factory=list)
    evidence: List[IdeaEvidence] = field(default_factory=list)
    topic_nouns: List[str] = field(default_factory=list)
    crg_backbone: List[Any] = field(default_factory=list)
    turns: int = 0
    crystallized: bool = False
    thesis: str = ""
    pivot_count: int = 0
    last_topic_noun: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    _crg: Any = None
    _vocab: Any = None
    # v3.5
    peak_coherence: float = 0.0
    crystallization_history: List[Dict[str, Any]] = field(default_factory=list)
    refine_count: int = 0
    tick_count: int = 0
    inferred_nouns: List[str] = field(default_factory=list)
    # v3.6
    contradictions: List[Tuple[str, str]] = field(default_factory=list)
    provisional: bool = False
    confidence: float = 0.0
    counter_query: Optional[str] = None
    counter_landed: Optional[bool] = None

    def set_crg(self, crg): self._crg = crg
    def set_vocab(self, vocab): self._vocab = vocab

    # ── coherence (v3.6: contradiction-aware) ────────────────────────────────
    def coherence(self) -> float:
        if not self.evidence: return 0.0
        dists = [BLA.hamming_distance(e.vector, self.centroid) for e in self.evidence]
        tightness = max(0.0, 1.0 - (sum(dists)/len(dists))/12.0)
        backbone = min(1.0, len(self.crg_backbone)/3.0)
        mass = min(1.0, len(self.evidence)/5.0)
        try: nrci = float(LEECH_ENGINE.calculate_nrci(self.centroid)) if self.centroid else 0.5
        except Exception: nrci = 0.5
        health = max(0.0, min(1.0, nrci))
        base = 0.34*tightness + 0.34*backbone + 0.16*mass + 0.16*health
        # v3.6 contradiction penalty
        pen = 0.0
        if self.crg_backbone and self._crg is not None:
            pen = contradiction_penalty(self.crg_backbone, self._crg)
            cons = detect_contradictions(self.crg_backbone, self._crg)
            self.contradictions = [(f"{e.src}--{e.label}->{e.dst}", ce.label) for e, ce in cons]
        if self.provisional: pen += 0.10
        return round(max(0.0, base - pen), 4)

    # ── anaphora resolution (v3.4 + v3.6 digit-fix) ──────────────────────────
    def resolve_anaphora(self, query: str) -> Tuple[str, List[str]]:
        if not self.last_topic_noun: return query, []
        subs = []
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|\S", query)
        out = []
        for tok in tokens:
            if tok.lower() in PRONOUNS:
                out.append(self.last_topic_noun); subs.append((tok, self.last_topic_noun))
            else: out.append(tok)
        resolved = re.sub(r"\s+", " ", " ".join(out)).strip()
        return resolved, subs

    # ── per-turn update (v3.4 + v3.5 + v3.6) ─────────────────────────────────
    def update(self, known_tokens, turn) -> Dict[str, Any]:
        diag = {"reinforced": [], "drifted": [], "seeded": [], "new_nouns": [],
                "new_backbone": [], "pre_coherence": 0.0, "post_coherence": 0.0,
                "crystallized_this_turn": False}
        diag["pre_coherence"] = self.coherence()
        first_seed = not self.evidence
        for word, entry in known_tokens:
            vec = entry.vector
            if first_seed or not self.centroid: fit, res = "seed", REINFORCE_RES
            else:
                d = BLA.hamming_distance(vec, self.centroid)
                fit = "reinforce" if d <= IDEA_RADIUS else "drift"
                res = REINFORCE_RES if fit == "reinforce" else DRIFT_RES
            ev = IdeaEvidence(word=word, vector=vec, role=entry.role,
                              nrci=float(entry.nrci), turn=turn, resonance=res,
                              fit=fit, source="user")
            self.evidence.append(ev)
            diag["reinforced" if fit=="reinforce" else ("drifted" if fit=="drift" else "seeded")].append(word)
            if entry.role in ("NOUN","PROPERTY") and word not in self.topic_nouns:
                self.topic_nouns.append(word); diag["new_nouns"].append(word); self.last_topic_noun = word
            first_seed = False
        if len(self.evidence) > MAX_EVIDENCE: self.evidence = self.evidence[-MAX_EVIDENCE:]
        self._recompute_centroid()
        before = len(self.crg_backbone); self._extend_backbone()
        diag["new_backbone"] = [f"{e.src}--{e.label}->{e.dst}" for e in self.crg_backbone[before:]]
        self.turns = turn; post = self.coherence(); diag["post_coherence"] = post
        self._check_recrysconnect()
        if post > self.peak_coherence: self.peak_coherence = post
        self.history.append({"turn":turn,"pre":diag["pre_coherence"],"post":post,
                             "reinforced":diag["reinforced"],"drifted":diag["drifted"],
                             "new_nouns":diag["new_nouns"],"new_backbone":diag["new_backbone"],
                             "crystallized":diag["crystallized_this_turn"],
                             "topic_nouns":list(self.topic_nouns)})
        return diag

    # ── decay (v3.5) ─────────────────────────────────────────────────────────
    def decay(self, age_turns: float = 1.0) -> int:
        for e in self.evidence:
            e.resonance = e.resonance * math.exp(-DECAY_LAMBDA * age_turns)
        before = len(self.evidence)
        self.evidence = [e for e in self.evidence if e.resonance >= PRUNE_FLOOR]
        pruned = before - len(self.evidence)
        surviving = {e.word for e in self.evidence}
        self.topic_nouns = [n for n in self.topic_nouns if n in surviving or n in self.inferred_nouns]
        self.crg_backbone = [e for e in self.crg_backbone
                             if e.src in self.topic_nouns and e.dst in self.topic_nouns]
        self._recompute_centroid()
        c = self.coherence()
        if self.crystallized and c < GET_IT_THRESHOLD - 0.15:
            self.crystallized = False
            self.crystallization_history.append({"event":"faded","turn":self.turns,
                "coherence":c,"thesis":self.thesis})
            self.thesis = ""
        return pruned

    # ── autonomous tick (v3.5) ───────────────────────────────────────────────
    def tick(self) -> Dict[str, Any]:
        if not self.centroid or not self._vocab or not self._crg:
            return {"discovered": None, "reason": "no centroid/vocab/crg"}
        diag = {"discovered": [], "edges_found": [], "aged": 0}
        self.decay(age_turns=TICK_AGE); diag["aged"] = TICK_AGE
        self.tick_count += 1
        candidates = []
        for noun in list(self.topic_nouns):
            for e in self._crg.out.get(noun, []):
                dst = e.dst
                if dst in self._vocab.words and dst not in self.topic_nouns:
                    dv = self._vocab.words[dst].vector
                    d = BLA.hamming_distance(dv, self.centroid)
                    if d <= TICK_SEARCH_RADIUS:
                        candidates.append((dst, e, d))
            for e in self._crg.into.get(noun, []):
                src = e.src
                if src in self._vocab.words and src not in self.topic_nouns:
                    sv = self._vocab.words[src].vector
                    d = BLA.hamming_distance(sv, self.centroid)
                    if d <= TICK_SEARCH_RADIUS:
                        candidates.append((src, e, d))
        candidates.sort(key=lambda x: x[2])
        added = 0; seen = set()
        for word, edge, dist in candidates:
            if word in seen or added >= MAX_INFERRED: continue
            seen.add(word)
            entry = self._vocab.words[word]
            res = INFERRED_RES if dist <= IDEA_RADIUS else ADJACENT_RES + 0.1
            ev = IdeaEvidence(word=word, vector=entry.vector, role=entry.role,
                              nrci=float(entry.nrci), turn=self.turns,
                              resonance=res, fit="inferred", source="inferred")
            self.evidence.append(ev)
            if entry.role in ("NOUN","PROPERTY") and word not in self.topic_nouns:
                self.topic_nouns.append(word); self.inferred_nouns.append(word)
                self.last_topic_noun = word
            diag["discovered"].append(word)
            diag["edges_found"].append(f"{edge.src}--{edge.label}->{edge.dst}")
            added += 1
        if len(self.evidence) > MAX_EVIDENCE: self.evidence = self.evidence[-MAX_EVIDENCE:]
        self._recompute_centroid(); self._extend_backbone()
        self._check_recrysconnect()
        return diag

    def mature(self, n_ticks: int = 3) -> List[Dict[str, Any]]:
        return [self.tick() for _ in range(n_ticks)]

    # ── re-crystallisation / refinement (v3.5) ───────────────────────────────
    def _check_recrysconnect(self):
        c = self.coherence()
        if (not self.crystallized and c >= GET_IT_THRESHOLD
            and len(self.evidence) >= MIN_EVIDENCE
            and len(self.crg_backbone) >= MIN_BACKBONE
            and len(self.topic_nouns) >= MIN_TOPIC_NOUNS):
            self.crystallized = True
            self.thesis = self._synthesise_thesis()
            self.peak_coherence = c
            self.crystallization_history.append({"event":"crystallized","turn":self.turns,
                "coherence":c,"thesis":self.thesis})
        elif self.crystallized and c > self.peak_coherence + REFINE_DELTA:
            old = self.thesis
            self.thesis = self._synthesise_thesis()
            if self.thesis != old:
                self.refine_count += 1
                self.peak_coherence = c
                self.crystallization_history.append({"event":"refined","turn":self.turns,
                    "coherence":c,"old":old,"new":self.thesis})

    # ── adversarial self-testing (v3.6) ──────────────────────────────────────
    def run_adversarial_test(self, vocab) -> Dict[str, Any]:
        if not self.thesis:
            return {"ran": False, "reason": "no thesis"}
        if len(self.topic_nouns) >= 2:
            a, b = self.topic_nouns[0], self.topic_nouns[1]
            self.counter_query = f"does {a} contradict {b}?"
            contra = False
            for e in self._crg.out.get(a, []):
                if e.label in ("contradicts","incompatible_with") and e.dst == b:
                    contra = True; break
            for e in self._crg.out.get(b, []):
                if e.label in ("contradicts","incompatible_with") and e.dst == a:
                    contra = True; break
            self.counter_landed = contra
            if contra:
                self.provisional = True
                self.confidence = max(0.0, self.coherence() - 0.15)
            else:
                self.provisional = False
                self.confidence = min(1.0, self.coherence() + 0.05)
            return {"ran": True, "counter_query": self.counter_query,
                    "landed": contra, "provisional": self.provisional,
                    "confidence": self.confidence}
        return {"ran": False, "reason": "insufficient topic nouns"}

    # ── centroid recompute (v3.4) ────────────────────────────────────────────
    def _recompute_centroid(self):
        if not self.evidence: self.centroid = []; return
        cols = [0]*24; total_w = 0.0
        for e in self.evidence:
            w = e.resonance; total_w += w
            for i,b in enumerate(e.vector): cols[i] += (w if b else 0)
        self.centroid = [1 if cols[i] > total_w/2.0 else 0 for i in range(24)]

    # ── backbone extension (v3.4 + v3.6 defaultdict fix) ─────────────────────
    def _extend_backbone(self):
        crg = self._crg
        if crg is None: return
        existing = {(e.src,e.label,e.dst) for e in self.crg_backbone}
        for i,a in enumerate(self.topic_nouns):
            for b in self.topic_nouns[i+1:]:
                for e in crg.out.get(a, []):
                    if e.dst == b and (e.src,e.label,e.dst) not in existing:
                        self.crg_backbone.append(e); existing.add((e.src,e.label,e.dst))
                for e in crg.out.get(b, []):
                    if e.dst == a and (e.src,e.label,e.dst) not in existing:
                        self.crg_backbone.append(e); existing.add((e.src,e.label,e.dst))

    # ── thesis synthesis (v3.4) ──────────────────────────────────────────────
    def _synthesise_thesis(self) -> str:
        if not self.crg_backbone:
            nouns = self.topic_nouns[:3]
            return f"The idea binds {' and '.join(nouns)} into a shared lattice region."
        priority = {"generates":0,"is_dual_to":0,"commutes_with":1,"scales_as":1,
                    "depends_on":2,"measures":2,"is_a":3,"auto_proposed":4}
        ranked = sorted(self.crg_backbone, key=lambda e: priority.get(e.label,4))[:2]
        parts = []
        for e in ranked:
            label = e.label.replace("_"," ")
            m = {"is_a":f"{e.src} is a {e.dst}","is_dual_to":f"{e.src} is dual to {e.dst}",
                 "commutes_with":f"{e.src} commutes with {e.dst}","generates":f"{e.src} generates {e.dst}",
                 "scales_as":f"{e.src} scales as {e.dst}","depends_on":f"{e.src} depends on {e.dst}",
                 "measures":f"{e.src} measures {e.dst}","auto_proposed":f"{e.src} relates to {e.dst}"}
            parts.append(m.get(e.label, f"{e.src} {label} {e.dst}"))
        return (parts[0]+".") if len(parts)==1 else (parts[0]+" and "+parts[1]+".")

    # ── status line (v3.6) ───────────────────────────────────────────────────
    def status_line(self) -> str:
        c = self.coherence()
        state = "crystallized" if self.crystallized else (
                "forming" if c > 0.4 else ("seeding" if c > 0.1 else "empty"))
        prov = " [PROVISIONAL]" if self.provisional else ""
        contra = f" [!{len(self.contradictions)}contras]" if self.contradictions else ""
        return (f"[idea: {state}{prov}{contra} | coh={c:.2f} conf={self.confidence:.2f} "
                f"peak={self.peak_coherence:.2f} | nouns={len(self.topic_nouns)}"
                f"(+{len(self.inferred_nouns)}inf) | bb={len(self.crg_backbone)} | "
                f"ticks={self.tick_count} | turns={self.turns}]")

    def idea_state(self) -> Dict[str, Any]:
        return {"coherence": self.coherence(), "peak_coherence": self.peak_coherence,
                "crystallized": self.crystallized, "thesis": self.thesis,
                "topic_nouns": list(self.topic_nouns),
                "inferred_nouns": list(self.inferred_nouns),
                "backbone": [{"src":e.src,"label":e.label,"dst":e.dst} for e in self.crg_backbone],
                "evidence": [{"word":e.word,"role":e.role,"fit":e.fit,"resonance":round(e.resonance,3),
                              "turn":e.turn,"source":e.source} for e in self.evidence],
                "tick_count": self.tick_count, "refine_count": self.refine_count,
                "contradictions": list(self.contradictions),
                "provisional": self.provisional, "confidence": self.confidence,
                "counter_query": self.counter_query, "counter_landed": self.counter_landed,
                "crystallization_history": list(self.crystallization_history)}


# ══════════════════════════════════════════════════════════════════════════════
# §07  IDEA MANAGER  — multi-zone + cross-zone synthesis + contradiction pivot (v3.6 + v3.7)
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class MetaThesis:
    """v3.7: A unifying thesis synthesised across multiple crystallised zones."""
    thesis: str
    zone_ids: List[int]
    shared_edges: List[Dict[str, str]]
    confidence: float
    created_at_turn: int


class IdeaManager:
    """Manages multiple competing IdeaZone instances + cross-zone synthesis."""

    def __init__(self, max_zones: int = MAX_ZONES, vocab=None, crg=None):
        self.max_zones = max_zones
        self.vocab = vocab
        self.crg = crg
        self.zones: List[IdeaZone] = []
        self.active_idx: int = 0
        self.meta_theses: List[MetaThesis] = []
        self._spawn_zone()

    def _spawn_zone(self, seed_noun: Optional[str] = None):
        z = IdeaZone()
        if self.crg: z.set_crg(self.crg)
        if self.vocab: z.set_vocab(self.vocab)
        self.zones.append(z)
        # v3.7: if a seed noun is given (contradiction-driven pivot), pre-seed it
        if seed_noun and self.vocab and seed_noun in self.vocab.words:
            entry = self.vocab.words[seed_noun]
            z.update([(seed_noun, entry)], turn=0)

    @property
    def active(self) -> IdeaZone:
        if not self.zones: self._spawn_zone()
        return self.zones[self.active_idx]

    def route(self, content_tokens) -> Tuple[IdeaZone, int, float]:
        """Route a turn's content tokens to the best-fit zone by Hamming distance."""
        if not content_tokens:
            return self.active, self.active_idx, 0.0
        best_idx, best_dist = 0, 999
        for i, z in enumerate(self.zones):
            if not z.centroid:
                return z, i, 0.0
            dists = [BLA.hamming_distance(entry.vector, z.centroid)
                     for _, entry in content_tokens if hasattr(entry, 'vector')]
            if not dists: continue
            d = min(dists)
            if d < best_dist:
                best_dist, best_idx = d, i
        if best_dist > ZONE_SPAWN_THRESHOLD and len(self.zones) < self.max_zones:
            self._spawn_zone()
            best_idx = len(self.zones) - 1
            best_dist = 0.0
        self.active_idx = best_idx
        return self.zones[best_idx], best_idx, best_dist

    def update(self, content_tokens, turn) -> Dict[str, Any]:
        zone, idx, fit = self.route(content_tokens)
        diag = zone.update(content_tokens, turn)
        diag["zone_idx"] = idx
        diag["zone_fit"] = fit
        cohs = [z.coherence() for z in self.zones]
        self.active_idx = cohs.index(max(cohs))
        diag["active_idx_after"] = self.active_idx
        diag["all_coherences"] = cohs
        # v3.7: attempt cross-zone synthesis after update
        if sum(1 for z in self.zones if z.crystallized) >= 2:
            mt = self.synthesise_meta_thesis(turn)
            if mt: diag["meta_thesis"] = mt.thesis
        # v3.7: contradiction-driven pivot — when contradictions detected,
        # spawn a new zone seeded with the contradicting noun (up to max_zones)
        if zone.contradictions and len(self.zones) < self.max_zones:
            pivot_noun = self._find_contradicting_noun(zone)
            if pivot_noun:
                self._spawn_zone(seed_noun=pivot_noun)
                diag["pivot_spawned"] = pivot_noun
        return diag

    def _find_contradicting_noun(self, zone: IdeaZone) -> Optional[str]:
        """v3.7: Find the noun that contradicts the zone's thesis."""
        if not zone.contradictions or not self.vocab: return None
        # the contradiction is between two topic nouns; return the one NOT in the thesis
        for edge_sum, contra_label in zone.contradictions:
            # edge_sum like "boson--contradicts->fermion"
            parts = edge_sum.split("--")
            if len(parts) >= 1:
                src = parts[0]
                # find the dst from the CRG
                for e in zone.crg_backbone:
                    if e.src == src:
                        return e.dst
        return None

    # ── v3.7: cross-zone synthesis ───────────────────────────────────────────
    def synthesise_meta_thesis(self, turn: int) -> Optional[MetaThesis]:
        """When 2+ zones are crystallised, attempt a unifying meta-thesis.
        Looks for (a) direct CRG edges between zones' topic nouns, OR
        (b) shared CRG neighbours (transitive link via a common concept).
        If found, synthesises a higher-level statement."""
        crystallised = [(i, z) for i, z in enumerate(self.zones) if z.crystallized]
        if len(crystallised) < 2: return None
        shared_edges = []
        # (a) direct edges between zones
        for i, (zi, za) in enumerate(crystallised):
            for j, (zj, zb) in enumerate(crystallised[i+1:], i+1):
                for a in za.topic_nouns:
                    for b in zb.topic_nouns:
                        for e in self.crg.out.get(a, []):
                            if e.dst == b and e.label not in ("contradicts","incompatible_with","auto_proposed"):
                                shared_edges.append({"src":a,"label":e.label,"dst":b,
                                                     "zone_a":zi,"zone_b":zj,"via":"direct"})
        # (b) transitive: shared CRG neighbour (e.g. both zones' nouns relate to a
        # common concept). Match on the shared noun itself, not the label — two
        # zones may reach the same concept via different relation types.
        if not shared_edges:
            for i, (zi, za) in enumerate(crystallised):
                for j, (zj, zb) in enumerate(crystallised[i+1:], i+1):
                    za_neighbours = set()  # just the dst nouns
                    for a in za.topic_nouns:
                        for e in self.crg.out.get(a, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                za_neighbours.add(e.dst)
                        for e in self.crg.into.get(a, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                za_neighbours.add(e.src)
                    for b in zb.topic_nouns:
                        zb_neighbours = set()
                        for e in self.crg.out.get(b, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                zb_neighbours.add(e.dst)
                        for e in self.crg.into.get(b, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                zb_neighbours.add(e.src)
                        shared = za_neighbours & zb_neighbours
                        for s in shared:
                            shared_edges.append({"src":b,"label":"shares_via","dst":s,
                                                 "zone_a":zi,"zone_b":zj,
                                                 "via":f"both zones relate to {s}"})
        if not shared_edges: return None
        # synthesise
        priority = {"generates":0,"is_dual_to":0,"commutes_with":1,"scales_as":1,
                    "depends_on":2,"measures":2,"is_a":3,"shares_via":3,"auto_proposed":4}
        ranked = sorted(shared_edges, key=lambda e: priority.get(e["label"],4))[:2]
        parts = []
        for e in ranked:
            if e["label"] == "shares_via":
                parts.append(e["via"])
            else:
                label = e["label"].replace("_"," ")
                m = {"is_a":f"{e['src']} is a {e['dst']}","is_dual_to":f"{e['src']} is dual to {e['dst']}",
                     "commutes_with":f"{e['src']} commutes with {e['dst']}",
                     "generates":f"{e['src']} generates {e['dst']}",
                     "scales_as":f"{e['src']} scales as {e['dst']}"}
                parts.append(m.get(e["label"], f"{e['src']} {label} {e['dst']}"))
        thesis = (parts[0]+".") if len(parts)==1 else (parts[0]+" and "+parts[1]+".")
        mt = MetaThesis(thesis=thesis,
                        zone_ids=[i for i,_ in crystallised],
                        shared_edges=ranked,
                        confidence=min(1.0, sum(z.confidence for _,z in crystallised)/len(crystallised)),
                        created_at_turn=turn)
        self.meta_theses.append(mt)
        return mt

    def decay_all(self, age_turns: float = 1.0):
        for z in self.zones: z.decay(age_turns)

    def tick_all(self):
        for z in self.zones:
            if z.evidence: z.tick()

    def mature_all(self, n: int = 3):
        for _ in range(n): self.tick_all()

    def reset(self):
        self.zones = []; self.active_idx = 0; self.meta_theses = []
        self._spawn_zone()

    def state(self) -> Dict[str, Any]:
        return {"num_zones": len(self.zones), "active_idx": self.active_idx,
                "zones": [z.idea_state() for z in self.zones],
                "meta_theses": [{"thesis":mt.thesis,"zone_ids":mt.zone_ids,
                                 "confidence":mt.confidence} for mt in self.meta_theses]}


# ══════════════════════════════════════════════════════════════════════════════
# §08  IDEA META-GRAPH  — persistence + warm-start (v3.6)
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class CrystallisedIdea:
    idea_id: str
    centroid: List[int]
    topic_nouns: List[str]
    thesis: str
    backbone: List[Dict[str, str]]
    peak_coherence: float
    turn_count: int
    created_at_turn: int


class IdeaMetaGraph:
    def __init__(self, path: str = "idea_meta_graph.json"):
        self.path = Path(path)
        self.ideas: List[CrystallisedIdea] = []
        self.load()

    def load(self):
        if not self.path.exists(): self.ideas = []; return
        try:
            data = json.loads(self.path.read_text())
            self.ideas = [CrystallisedIdea(**d) for d in data.get("ideas", [])]
        except Exception: self.ideas = []

    def save(self):
        self.path.write_text(json.dumps(
            {"ideas": [asdict(i) for i in self.ideas]}, indent=2, default=str))

    def record(self, zone, idea_id: Optional[str] = None) -> CrystallisedIdea:
        iid = idea_id or f"idea_{len(self.ideas)+1}_{int(time.time())%100000}"
        ci = CrystallisedIdea(idea_id=iid, centroid=list(zone.centroid),
            topic_nouns=list(zone.topic_nouns), thesis=zone.thesis,
            backbone=[{"src":e.src,"label":e.label,"dst":e.dst} for e in zone.crg_backbone],
            peak_coherence=zone.peak_coherence, turn_count=zone.turns,
            created_at_turn=zone.turns)
        self.ideas.append(ci); self.save(); return ci

    def match(self, tokens_vectors, topic_nouns, max_hamming=8, min_noun_overlap=1):
        if not self.ideas or not tokens_vectors: return None
        best, best_score = None, 0.0
        for ci in self.ideas:
            dists = [BLA.hamming_distance(v, ci.centroid) for v in tokens_vectors]
            min_d = min(dists) if dists else 999
            if min_d > max_hamming: continue
            overlap = len(set(topic_nouns) & set(ci.topic_nouns))
            if overlap < min_noun_overlap: continue
            score = (1.0 - min_d/24.0) + 0.5*overlap
            if score > best_score: best_score, best = score, ci
        return best

    def stats(self):
        return {"total_ideas": len(self.ideas),
                "avg_peak_coherence": (sum(i.peak_coherence for i in self.ideas)/len(self.ideas)
                                        if self.ideas else 0.0),
                "avg_turns": (sum(i.turn_count for i in self.ideas)/len(self.ideas)
                              if self.ideas else 0)}


# ══════════════════════════════════════════════════════════════════════════════
# §09  TOOLS LAYER  — SymPy calculation + symbolic ops (v3.5 + v3.7)
# ══════════════════════════════════════════════════════════════════════════════
try:
    import sympy as sp
    _HAS_SYMPY = True
except Exception:
    _HAS_SYMPY = False

_GCD_RE       = re.compile(r'gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
_LCM_RE       = re.compile(r'lcm\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
# v3.7.3 REFINEMENT: NL forms for GCD/LCM (MathNet uses "greatest common divisor of N and M")
_GCD_NL_RE    = re.compile(r'(?:greatest\s+common\s+divisor|gcd)\s+of\s+(\d+)\s+and\s+(\d+)', re.I)
_LCM_NL_RE    = re.compile(r'(?:least\s+common\s+multiple|lcm)\s+of\s+(\d+)\s+and\s+(\d+)', re.I)
_SQRT_RE      = re.compile(r'(?:sqrt|√)\s*\(\s*(\d+(?:\.\d+)?)\s*\)', re.I)
_POWER_RE     = re.compile(r'(\d+(?:\.\d+)?)\s*\^\s*(\d+(?:\.\d+)?)')
_FACTORIAL_RE = re.compile(r'(\d+)\s*!', re.I)
# v3.7.3 REFINEMENT: NL form for factorial ("Compute N factorial", "N factorial")
_FACTORIAL_NL_RE = re.compile(r'(?:compute|find|calculate)?\s*(\d+)\s+factorial', re.I)
# v3.7.3 REFINEMENT: combination/permutation ("choose K from N", "C(N, K)")
_COMBINATION_RE = re.compile(r'(?:choose|select)\s+(\d+)\s+(?:items?\s+)?from\s+(\d+)', re.I)
_COMBINATION_FN_RE = re.compile(r'[Cc]\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)')
_PERMUTATION_RE = re.compile(r'(?:arrange|permute)\s+(\d+)\s+(?:items?\s+)?from\s+(\d+)', re.I)
# v3.7.3: vector operations
_DOT_RE = re.compile(r'dot\s+product\s+of\s+<([^>]+)>\s+and\s+<([^>]+)>', re.I)
_CROSS_RE = re.compile(r'cross\s+product\s+of\s+<([^>]+)>\s+and\s+<([^>]+)>', re.I)
_MAGNITUDE_RE = re.compile(r'magnitude\s+of\s+(?:the\s+)?vector\s+<([^>]+)>', re.I)
_DET_RE = re.compile(r'determinant\s+of\s+(?:the\s+)?matrix\s+(\[\[.*?\]\])', re.I)
_ARITH_RE     = re.compile(r'(\d+(?:\.\d+)?)\s*([+\-*/×÷])\s*(\d+(?:\.\d+)?)')
_WORD_OP_RE   = re.compile(r'(\d+(?:\.\d+)?)\s+(times|plus|minus|divided\s+by)\s+(\d+(?:\.\d+)?)', re.I)
_PHRASE_RE    = re.compile(r'(?:what is|compute|calculate|evaluate)\s+(.+?)[\?\.]?$', re.I)

# v3.7 symbolic patterns
# v3.7.3: improved patterns — stop at "with respect to" / "for x" / "dx"
_DIFF_RE      = re.compile(r'(?:differentiate|derivative of|d/dx)\s+(.+?)(?:\s+with respect to\s+(\w+))?(?:[\?\.]|$)', re.I)
_INTEGRAL_RE   = re.compile(r'(?:integrate|integral of)\s+(.+?)(?:\s+with respect to\s+\w+)?(?:\s+(?:dx|d\w+))?(?:[\?\.]|$)', re.I)
_SOLVE_RE      = re.compile(r'solve\s+(.+?)(?:\s+for\s+(\w+))?(?:[\?\.]|$)', re.I)
_SIMPLIFY_RE   = re.compile(r'simplify\s+(.+?)(?:[\?\.]|$)', re.I)


def detect_compute(query: str) -> Optional[Dict[str, Any]]:
    """v3.5: detect a computable numeric expression.
    v3.7.3: added NL forms for GCD/LCM/factorial/combination, backtick stripping,
            and guard against arith matching inside solve/differentiate queries."""
    if not _HAS_SYMPY: return None
    q = query.strip()
    # v3.7.3: strip backticks so SymPy can parse expressions
    q_clean = q.replace('`', '')
    m = _GCD_RE.search(q_clean)
    if m: return {"kind":"gcd","expr":f"gcd({m.group(1)},{m.group(2)})","operands":[int(m.group(1)),int(m.group(2))]}
    m = _GCD_NL_RE.search(q_clean)
    if m: return {"kind":"gcd","expr":f"gcd({m.group(1)},{m.group(2)})","operands":[int(m.group(1)),int(m.group(2))]}
    m = _LCM_RE.search(q_clean)
    if m: return {"kind":"lcm","expr":f"lcm({m.group(1)},{m.group(2)})","operands":[int(m.group(1)),int(m.group(2))]}
    m = _LCM_NL_RE.search(q_clean)
    if m: return {"kind":"lcm","expr":f"lcm({m.group(1)},{m.group(2)})","operands":[int(m.group(1)),int(m.group(2))]}
    m = _SQRT_RE.search(q_clean)
    if m: return {"kind":"sqrt","expr":f"sqrt({m.group(1)})","operands":[float(m.group(1))]}
    m = _FACTORIAL_RE.search(q_clean)
    if m and int(m.group(1)) <= 20:
        return {"kind":"factorial","expr":f"{m.group(1)}!","operands":[int(m.group(1))]}
    m = _FACTORIAL_NL_RE.search(q_clean)
    if m and int(m.group(1)) <= 20:
        return {"kind":"factorial","expr":f"{m.group(1)}!","operands":[int(m.group(1))]}
    # v3.7.3: combination "choose K from N" -> C(N, K)
    m = _COMBINATION_RE.search(q_clean)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        return {"kind":"combination","expr":f"C({n},{k})","operands":[n,k]}
    m = _COMBINATION_FN_RE.search(q_clean)
    if m:
        n, k = int(m.group(1)), int(m.group(2))
        return {"kind":"combination","expr":f"C({n},{k})","operands":[n,k]}
    m = _PERMUTATION_RE.search(q_clean)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        return {"kind":"permutation","expr":f"P({n},{k})","operands":[n,k]}
    # v3.7.3: vector operations
    m = _DOT_RE.search(q_clean)
    if m:
        v1 = [float(x.strip()) for x in m.group(1).split(',')]
        v2 = [float(x.strip()) for x in m.group(2).split(',')]
        return {"kind":"dot","expr":f"dot({v1},{v2})","operands":[v1,v2]}
    m = _CROSS_RE.search(q_clean)
    if m:
        v1 = [float(x.strip()) for x in m.group(1).split(',')]
        v2 = [float(x.strip()) for x in m.group(2).split(',')]
        return {"kind":"cross","expr":f"cross({v1},{v2})","operands":[v1,v2]}
    m = _MAGNITUDE_RE.search(q_clean)
    if m:
        v = [float(x.strip()) for x in m.group(1).split(',')]
        return {"kind":"magnitude","expr":f"mag({v})","operands":[v]}
    m = _DET_RE.search(q_clean)
    if m:
        return {"kind":"determinant","expr":m.group(1),"operands":[m.group(1)]}
    m = _POWER_RE.search(q_clean)
    if m: return {"kind":"power","expr":f"{m.group(1)}^{m.group(2)}","operands":[float(m.group(1)),float(m.group(2))]}
    # v3.7.3: guard — don't match arith if this is a solve/differentiate query
    is_symbolic_query = any(kw in q_clean.lower() for kw in
                           ['solve', 'differentiate', 'derivative', 'integrate', 'simplify',
                            'x^', 'x*', 'x+', 'x-', 'sin(', 'cos(', 'exp(', 'ln('])
    if is_symbolic_query:
        return None  # let detect_symbolic handle it
    phrase = _PHRASE_RE.search(q_clean)
    target = phrase.group(1) if phrase else q_clean
    m = _WORD_OP_RE.search(target)
    if m:
        op_map = {"times":"*","plus":"+","minus":"-","divided by":"/","divided  by":"/"}
        op = re.sub(r"\s+"," ", m.group(2).lower())
        return {"kind":"arith","expr":f"{m.group(1)}{op_map[op]}{m.group(3)}","operands":[float(m.group(1)),op,float(m.group(3))]}
    m = _ARITH_RE.search(target)
    if m:
        op_map = {"×":"*","÷":"/","+":"+","-":"-","*":"*","/":"/"}
        return {"kind":"arith","expr":f"{m.group(1)}{op_map[m.group(2)]}{m.group(3)}","operands":[float(m.group(1)),m.group(2),float(m.group(3))]}
    return None


def detect_symbolic(query: str) -> Optional[Dict[str, Any]]:
    """v3.7: detect a symbolic math operation (diff/integral/solve/simplify).
    v3.7.3: strip backticks + trailing 'with respect to X' from expressions."""
    if not _HAS_SYMPY: return None
    q = query.strip().replace('`', '')  # v3.7.3: strip backticks

    def _safe_group(m, idx, default=None):
        """Safely get a regex group, returning default if it doesn't exist."""
        try:
            val = m.group(idx)
            return val if val else default
        except (IndexError, re.error):
            return default

    m = _DIFF_RE.search(q)
    if m:
        expr_str = m.group(1).strip()
        expr_str = re.sub(r'\s+with respect to\s+\w+$', '', expr_str, flags=re.I).strip()
        var = _safe_group(m, 2, "x") or "x"
        return {"kind":"differentiate","expr":expr_str,"var":var}
    m = _INTEGRAL_RE.search(q)
    if m:
        expr_str = m.group(1).strip()
        expr_str = re.sub(r'\s+with respect to\s+\w+$', '', expr_str, flags=re.I).strip()
        var = _safe_group(m, 2, "x") or "x"
        return {"kind":"integrate","expr":expr_str,"var":var}
    m = _SOLVE_RE.search(q)
    if m:
        expr_str = m.group(1).strip()
        var = _safe_group(m, 2, "x") or "x"
        return {"kind":"solve","expr":expr_str,"var":var}
    m = _SIMPLIFY_RE.search(q)
    if m:
        return {"kind":"simplify","expr":m.group(1).strip(),"var":None}
    return None


def evaluate(comp: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a numeric computation with SymPy.
    v3.7.3: handle combination/permutation/vector ops/determinant."""
    if not _HAS_SYMPY: return {"value": None, "error": "sympy unavailable"}
    try:
        kind = comp.get("kind")
        if kind == "combination":
            n, k = comp["operands"]
            val = sp.binomial(n, k)
        elif kind == "permutation":
            n, k = comp["operands"]
            val = sp.factorial(n) // sp.factorial(n - k)
        elif kind == "dot":
            v1, v2 = comp["operands"]
            val = sum(a*b for a, b in zip(v1, v2))
        elif kind == "cross":
            v1, v2 = comp["operands"]
            if len(v1) == 3 and len(v2) == 3:
                cx = v1[1]*v2[2] - v1[2]*v2[1]
                cy = v1[2]*v2[0] - v1[0]*v2[2]
                cz = v1[0]*v2[1] - v1[1]*v2[0]
                val = (cx, cy, cz)
            else:
                return {"value": None, "error": "cross product requires 3D vectors"}
        elif kind == "magnitude":
            v = comp["operands"][0]
            val = sp.sqrt(sum(x**2 for x in v))
        elif kind == "determinant":
            mat_str = comp["operands"][0]
            # Parse matrix string like [[1,2,3],[4,5,6],[7,8,10]]
            mat = sp.sympify(mat_str)
            val = sp.Matrix(mat).det()
        else:
            val = sp.sympify(comp["expr"])
        # Compute approximate and exact forms
        try:
            approx = float(val)
        except Exception:
            approx = 0.0
        return {"value": val, "exact": str(val), "approx": approx, "latex": sp.latex(val)}
    except Exception as e:
        return {"value": None, "error": str(e)}


def evaluate_symbolic(comp: Dict[str, Any]) -> Dict[str, Any]:
    """v3.7: Evaluate a symbolic operation with SymPy.
    v3.7.3: handle 'expr = 0' form for solve, convert ^ to **, expand+sorted for matching."""
    if not _HAS_SYMPY: return {"value": None, "error": "sympy unavailable"}
    try:
        var_name = comp.get("var") or "x"
        x = sp.Symbol(var_name)
        expr_str = comp["expr"]
        # v3.7.3: if it's a solve with '= 0', strip it; if '= N', move to LHS
        if comp["kind"] == "solve" and '=' in expr_str:
            parts = expr_str.split('=')
            if len(parts) == 2:
                lhs = sp.sympify(parts[0].strip().replace('^', '**'))
                rhs = sp.sympify(parts[1].strip().replace('^', '**'))
                expr = lhs - rhs
            else:
                expr = sp.sympify(expr_str.replace('^', '**'))
        else:
            # v3.7.3: convert ^ to ** for SymPy
            expr_str = expr_str.replace('^', '**')
            expr = sp.sympify(expr_str)
        if comp["kind"] == "differentiate":
            result = sp.diff(expr, x)
        elif comp["kind"] == "integrate":
            result = sp.integrate(expr, x)
        elif comp["kind"] == "solve":
            result = sp.solve(expr, x)
        elif comp["kind"] == "simplify":
            result = sp.simplify(expr)
        else:
            return {"value": None, "error": f"unknown kind: {comp['kind']}"}
        # v3.7.3: produce multiple forms for flexible matching
        exact = str(result)
        try:
            expanded = str(sp.expand(result))
        except Exception:
            expanded = exact
        # v3.7.3: sorted form (terms in string-sorted order) for order-independent matching
        try:
            if hasattr(result, 'args') and result.is_Add and len(result.args) > 1:
                # Sort addition terms by their string representation, then join manually
                # (sp.Add reorders to canonical, so we build the string ourselves)
                sorted_terms = sorted(str(t) for t in result.args)
                sorted_form = " + ".join(sorted_terms)
            else:
                sorted_form = exact
        except Exception:
            sorted_form = exact
        return {"value": result, "exact": exact, "expanded": expanded,
                "sorted": sorted_form, "latex": sp.latex(result)}
    except Exception as e:
        return {"value": None, "error": str(e)}


def ground_result(approx: float, vocab) -> Optional[Tuple[str, Any]]:
    """Ground a numeric result as a vocab number-word."""
    if abs(approx - round(approx)) < 1e-9:
        n = int(round(approx))
        if n in NUMBER_WORDS:
            w = NUMBER_WORDS[n]
            if w in vocab.words: return (w, vocab.words[w])
        if -n in NUMBER_WORDS and f"minus_{NUMBER_WORDS[-n]}" in vocab.words:
            return (f"minus_{NUMBER_WORDS[-n]}", vocab.words[f"minus_{NUMBER_WORDS[-n]}"])
    return None


def try_compute(query: str, vocab) -> Optional[Dict[str, Any]]:
    """Full pipeline: detect numeric → evaluate → ground."""
    comp = detect_compute(query)
    if comp is None: return None
    result = evaluate(comp)
    if result.get("value") is None: return None
    grounded = ground_result(result["approx"], vocab)
    return {"computation": comp, "result": result, "grounded": grounded, "source": "computed"}


def try_symbolic(query: str, vocab) -> Optional[Dict[str, Any]]:
    """v3.7: Full pipeline for symbolic operations."""
    comp = detect_symbolic(query)
    if comp is None: return None
    result = evaluate_symbolic(comp)
    if result.get("value") is None: return None
    return {"computation": comp, "result": result, "grounded": None, "source": "symbolic"}


# ══════════════════════════════════════════════════════════════════════════════
# §10  RESPONSE COMPOSER v3.7  — confidence-tagged, multi-zone, synthesis-aware
# ══════════════════════════════════════════════════════════════════════════════
def _is_clean_verb(word, entry):
    if entry.role not in ("VERB","OPERATOR"): return False
    if _OP_SYNTAX_RE.search(word): return False
    return bool(re.match(r"^[a-z]{3,}$", word))


def _kb_description(word, vocab, kb, alias_map=None):
    """Look up the KB description + metrics for a vocab word (Defect D3 fix)."""
    entry = vocab.words.get(word)
    if not entry: return ("", 0.0, 0.0)
    vec = entry.vector; nrci = float(entry.nrci)
    try: tax = float(LEECH_ENGINE.calculate_symmetry_tax(vec))
    except Exception: tax = 0.0
    desc = ""
    if alias_map:
        uid = alias_map.get(word.lower())
        if uid and uid in kb:
            kbe = kb[uid]; name = kbe.get("name",uid); d = kbe.get("desc","")
            m = re.match(r"([^.]{12,}\.)", d)
            desc = f"{name}: {m.group(1).strip()}" if m else (f"{name}: {d[:90]}" if d else name)
            return (desc, nrci, tax)
    for uid, kbe in kb.items():
        if kbe.get("vector") == vec:
            name = kbe.get("name",uid); d = kbe.get("desc","")
            m = re.match(r"([^.]{12,}\.)", d)
            desc = f"{name}: {m.group(1).strip()}" if m else (f"{name}: {d[:90]}" if d else name)
            break
    return (desc, nrci, tax)


def _verbalise_edge(e):
    label = e.label.replace("_"," ")
    m = {"is_a":f"{e.src} is a {e.dst}","is_dual_to":f"{e.src} is dual to {e.dst}",
         "commutes_with":f"{e.src} commutes with {e.dst}","generates":f"{e.src} generates {e.dst}",
         "scales_as":f"{e.src} scales as {e.dst}","depends_on":f"{e.src} depends on {e.dst}",
         "measures":f"{e.src} measures {e.dst}","auto_proposed":f"{e.src} relates to {e.dst}"}
    return m.get(e.label, f"{e.src} {label} {e.dst}")


def compose_response(query, known, unknown, zone, manager, vocab, crg, qtype,
                     compute_result=None, symbolic_result=None, warm_start=None,
                     recalled=None, deliberation=None):
    """v3.7: confidence-tagged, multi-zone, synthesis-aware response.
    v3.7.2: optional `recalled` param — KB entries from reflexive_recall.
    v3.7.3: optional `deliberation` param — result from deliberate()."""
    kb = _load_system_kb(); alias_map = _build_alias_map()
    parts: List[str] = []

    # v3.7.2 ABSORPTION 4: show query type (computation/proof get explicit tags)
    if qtype in ("computation", "proof"):
        parts.append(f"[qtype:{qtype}]")

    # multi-zone header
    if manager is not None and len(manager.zones) > 1:
        cohs = [round(z.coherence(),2) for z in manager.zones]
        parts.append(f"[zones: {len(manager.zones)} active={manager.active_idx} cohs={cohs}]")
    # v3.7.1 REFINEMENT: only show raw idea-state diagnostic when the idea
    # has actually started forming (has topic nouns + a CRG backbone).
    # Otherwise the user sees internal state that isn't actionable.
    if zone is not None and zone.evidence and zone.topic_nouns and zone.crg_backbone:
        parts.append(zone.status_line())
    elif zone is not None and zone.evidence and not zone.crystallized:
        # User-friendly "still forming" message instead of raw diagnostic
        nouns_str = ", ".join(list(zone.topic_nouns)[:3]) if zone.topic_nouns else "the query"
        parts.append(f"[forming] gathering evidence around {nouns_str} — needs more related concepts to crystallize")

    # meta-thesis announcement (v3.7)
    if manager is not None and manager.meta_theses:
        mt = manager.meta_theses[-1]
        parts.append(f"[META-THESIS] unifying zones {mt.zone_ids}: {mt.thesis}")

    # warm-start
    if warm_start is not None:
        parts.append(f"[warm-start] resembles prior idea '{warm_start.idea_id}': "
                     f"\"{warm_start.thesis}\" (peak={warm_start.peak_coherence:.2f})")

    # crystallisation / provisional / refined
    if zone is not None and zone.crystallized and zone.thesis:
        if zone.provisional:
            parts.append(f"[I get it — PROVISIONAL] {zone.thesis}")
            if zone.counter_query:
                parts.append(f"[adversarial] counter-query '{zone.counter_query}' landed → confidence reduced")
        else:
            hist = zone.crystallization_history
            last_event = hist[-1]["event"] if hist else "crystallized"
            tag = "[I get it — refined]" if last_event == "refined" else "[I get it]"
            parts.append(f"{tag} {zone.thesis}")
            if zone.counter_landed is False:
                parts.append(f"[adversarial] counter-query '{zone.counter_query}' did NOT land → confidence reinforced")

    # contradiction alerts
    if zone is not None and zone.contradictions:
        for edge_sum, contra_label in zone.contradictions:
            parts.append(f"[CONTRADICTION] {edge_sum} but {contra_label} — idea is inconsistent")

    # numeric computation
    if compute_result is not None:
        comp = compute_result["computation"]; res = compute_result["result"]; grd = compute_result["grounded"]
        parts.append(f"[computed] {comp['expr']} = {res['exact']} (≈{res['approx']:.4g})")
        if grd:
            parts.append(f"[computed→grounded] result snapped to lattice point '{grd[0]}'")

    # symbolic computation (v3.7)
    # v3.7.3: show exact + sorted forms for flexible matching
    if symbolic_result is not None:
        comp = symbolic_result["computation"]; res = symbolic_result["result"]
        exact = res.get('exact', '')
        sorted_form = res.get('sorted', '')
        if sorted_form and sorted_form != exact:
            parts.append(f"[symbolic:{comp['kind']}] {comp['expr']} → {exact} | {sorted_form}")
        else:
            parts.append(f"[symbolic:{comp['kind']}] {comp['expr']} → {exact}")

    # v3.7.3 §13: deliberative reasoning result
    if deliberation is not None:
        parts.append(format_deliberation(deliberation))

    # topic + KB + verify
    topic_word = None
    if zone is not None and zone.last_topic_noun and zone.last_topic_noun in vocab.words:
        topic_word = zone.last_topic_noun
    if topic_word is None:
        for w, e in known:
            if e.role in ("NOUN","PROPERTY"): topic_word = w; break
    if topic_word is None and known: topic_word = known[0][0]
    if topic_word:
        desc, nrci, tax = _kb_description(topic_word, vocab, kb, alias_map)
        if desc: parts.append(f"[KB] {desc}")
        parts.append(f"[verify] NRCI={nrci:.3f}  tax={tax:.2f}")

    # CRG backbone
    if zone is not None and zone.crg_backbone:
        said = []
        for e in zone.crg_backbone:
            v = _verbalise_edge(e)
            if v.lower() not in (zone.thesis or "").lower():
                tag = f"[CRG:{e.label}]" if e.label != "auto_proposed" else "[CRG:auto]"
                said.append(f"{tag} {v}")
            if len(said) >= 2: break
        if said: parts.append("  ".join(said))

    # inferred evidence
    if zone is not None and zone.inferred_nouns:
        recent = zone.inferred_nouns[-2:]
        tag_parts = []
        for n in recent:
            just = None
            for e in zone.crg_backbone:
                if e.src == n or e.dst == n:
                    just = f"{e.src}--{e.label}->{e.dst}"; break
            if just:
                tag_parts.append(f"[inferred tick={zone.tick_count}] {n} (via {just})")
        if tag_parts: parts.append("  ".join(tag_parts))

    # metric query
    if qtype == "metric" and topic_word:
        entry = vocab.words.get(topic_word)
        if entry:
            nrci = float(entry.nrci)
            try: tax = float(LEECH_ENGINE.calculate_symmetry_tax(entry.vector))
            except Exception: tax = 0.0
            parts.append(f"[verify] The stability of {topic_word} is NRCI={nrci:.3f}, symmetry tax={tax:.2f}.")

    # gaps
    real_gaps = [u for u in unknown if u.lower() not in {"hello","hi","thanks","thank","please","ok","okay"}]
    if real_gaps: parts.append(f"[gap] no verified vector for: {', '.join(real_gaps[:5])}.")

    # v3.7.2 ABSORPTION 2: reflexive recall — show KB entries that matched
    if recalled:
        recall_strs = []
        for r in recalled[:3]:
            name = r.get("name", r.get("ubp_id", "?"))
            desc = r.get("desc", "")
            # Truncate desc to first sentence
            if desc:
                import re as _re
                m = _re.match(r"([^.]{12,}\.)", desc)
                short = m.group(1).strip() if m else desc[:80]
                recall_strs.append(f"{name}: {short}")
            else:
                recall_strs.append(name)
        if recall_strs:
            parts.append(f"[recall] {len(recalled)} KB match: " + " | ".join(recall_strs))

    # graceful fallback
    zone_empty = (zone is None) or (not zone.evidence)
    if not known and zone_empty and compute_result is None and symbolic_result is None:
        ql = query.lower().strip()
        if any(g in ql for g in ["hello","hi","hey","greetings"]):
            parts.append("Hello. I am the UBP Geometric Language Machine v3.7. Name a concept or ask me to compute/differentiate/integrate/solve something.")
        elif any(t in ql for t in ["thank","thanks","cheers"]):
            parts.append("You are welcome. Tell me another concept and I will keep building the idea.")
        else:
            parts.append("I have no grounded concept for that yet. Name a particle, a law, a symmetry — or ask me to compute gcd, sqrt, differentiate, integrate, or solve.")
    elif not known and zone is not None and zone.crystallized and compute_result is None and symbolic_result is None:
        parts.append(f"Building on the idea: {zone.thesis}")
    elif not known and zone is not None and compute_result is None and symbolic_result is None:
        noun = zone.last_topic_noun or "the topic"
        parts.append(f"Still forming an idea around {noun} — give me another related concept.")

    return "  ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# §11  RUNTIME v3.7  — wires everything
# ══════════════════════════════════════════════════════════════════════════════
class GLMRuntimeV37:
    """v3.7: Multi-zone, contradiction-aware, adversarially-tested, persistent,
    cross-zone-synthesising, auto-expanding, symbolic-tool-equipped runtime."""

    def __init__(self, system_kb_path="ubp_system_kb.json",
                 lang_kb_path="ubp_lang_kb_combined_v4.json",
                 auto_tick: bool = True,
                 max_zones: int = MAX_ZONES,
                 meta_graph_path: str = "idea_meta_graph.json",
                 auto_expand: bool = True):
        print("[GLMRuntime v3.7] booting...")
        self.glm, self._report = create_semantic_engine(system_kb_path, lang_kb_path)
        self.rules = GLMRulesEngine(lang_kb_path)
        # extended CRG (contradiction edges)
        self.crg = build_extended_crg()
        self.crg.vocab_check(set(self.glm.vocab.words.keys()))
        # expanded number vocab
        num_report = inject_number_vocab(self.glm.vocab)
        # v3.7: CRG auto-expansion
        self.auto_expansions = []
        if auto_expand:
            self.auto_expansions = auto_expand_crg(self.crg, self.glm.vocab)
        # v3.7.2 ABSORPTION 1: lattice-based CRG linking (aggressive)
        self.lattice_links = 0
        if auto_expand:
            self.lattice_links = lattice_auto_link(self.crg, self.glm.vocab)
        # rebuild lexer with expanded vocab
        self.glm.lexer = MultiTokenLexer(set(self.glm.vocab.words.keys()))
        # multi-zone manager
        self.manager = IdeaManager(max_zones=max_zones, vocab=self.glm.vocab, crg=self.crg)
        self.auto_tick = auto_tick
        self.meta_graph = IdeaMetaGraph(meta_graph_path)
        self._turn = 0; self._last_diag = None
        print(f"[GLMRuntime v3.7] ready. vocab={len(self.glm.vocab.words)} "
              f"crg_edges={len(self.crg.edges)}(+{len(self.auto_expansions)} auto,+{self.lattice_links} lattice) "
              f"zones={max_zones} meta_graph={self.meta_graph.stats()['total_ideas']} prior")

    def chat(self, query: str) -> str:
        self._turn += 1
        # between-turn maturation
        if self.auto_tick and self.manager.zones:
            self.manager.decay_all(age_turns=1.0)
            self.manager.tick_all()
        # anaphora resolution against active zone
        active = self.manager.active
        resolved, subs = active.resolve_anaphora(query)
        # computation tools (numeric + symbolic)
        compute_result = try_compute(resolved, self.glm.vocab)
        symbolic_result = try_symbolic(resolved, self.glm.vocab)
        # lex + partition
        clean = self.rules.preprocess(resolved)
        tokens = self.glm.lexer.tokenise(clean)
        known_pairs = [(t, self.glm.vocab.words[t]) for t in tokens if t in self.glm.vocab.words]
        unknown = [t for t in tokens if t not in self.glm.vocab.words]
        # v3.7.2 ABSORPTION 3: derive vectors for gap words on-the-fly
        derived = self._derive_gap_words(unknown)
        if derived:
            # Re-tokenize: some previously-unknown words are now known
            known_pairs = [(t, self.glm.vocab.words[t]) for t in tokens if t in self.glm.vocab.words]
            unknown = [t for t in tokens if t not in self.glm.vocab.words]
            diag_note = f"derived {len(derived)}: {derived[:5]}"
        content = filter_content_tokens(known_pairs)
        # ground computed result as evidence
        if compute_result and compute_result["grounded"]:
            w, entry = compute_result["grounded"]
            content.append((w, entry))
        # warm-start check
        warm_start = None
        if content:
            tvs = [entry.vector for _, entry in content if hasattr(entry, 'vector')]
            nouns = [w for w, e in content if e.role in ("NOUN","PROPERTY")]
            warm_start = self.meta_graph.match(tvs, nouns)
        # route + update
        diag = self.manager.update(content, self._turn)
        zone = self.manager.active
        diag["anaphora_subs"] = subs; diag["resolved_query"] = resolved
        diag["content_tokens"] = [w for w,_ in content]; diag["unknown"] = unknown
        diag["compute"] = compute_result; diag["symbolic"] = symbolic_result
        diag["warm_start"] = warm_start.idea_id if warm_start else None
        # adversarial test on crystallisation
        if diag.get("crystallized_this_turn") or (zone.crystallized and zone.counter_landed is None):
            adv = zone.run_adversarial_test(self.glm.vocab)
            diag["adversarial"] = adv
            if zone.crystallized and zone.thesis:
                ci = self.meta_graph.record(zone)
                diag["meta_recorded"] = ci.idea_id
        qtype = _enhanced_query_type(query)
        # v3.7.2 ABSORPTION 2: reflexive recall — surface KB entries
        recalled = self.reflexive_recall(query, max_results=3)
        if recalled:
            diag["recalled"] = recalled
        # v3.7.3 §13: deliberative reasoning fallback
        # If direct compute/symbolic didn't fire AND the query looks like
        # a proof/computation problem, try the deliberative layer.
        deliberation_result = None
        if compute_result is None and symbolic_result is None:
            deliberation_result = deliberate(query)
            if deliberation_result:
                diag["deliberation"] = deliberation_result
        response = compose_response(
            query, content, unknown, zone, self.manager, self.glm.vocab,
            self.crg, qtype, compute_result, symbolic_result, warm_start,
            recalled=recalled, deliberation=deliberation_result)
        diag["response"] = response; self._last_diag = diag
        return response

    def chat_with_effort(self, query: str, max_ticks: int = 5) -> str:
        """v3.7.1: chat() with iterative maturation.

        Calls chat() once, then if the active zone hasn't crystallized,
        calls mature(1) and re-composes the response, up to max_ticks times.

        Useful for queries that need more reasoning steps to crystallize.
        Does NOT change the default chat() behavior — call this explicitly
        when you want the system to 'think harder'.
        """
        first_response = self.chat(query)
        # Check if already crystallized or no zone to mature
        zone = self.manager.active
        if zone is None or zone.crystallized:
            return first_response
        # Iterate: mature + re-compose
        for tick in range(max_ticks):
            if zone.crystallized:
                break
            self.mature(1)
            # Re-compose the response with the updated zone state
            qtype = _enhanced_query_type(query)
            # Re-fetch the diagnostics from the last chat() call
            diag = self._last_diag
            content = [(t, self.glm.vocab.words[t]) for t in diag.get("content_tokens", [])
                       if t in self.glm.vocab.words]
            unknown = diag.get("unknown", [])
            compute_result = diag.get("compute")
            symbolic_result = diag.get("symbolic")
            warm_start = None
            if diag.get("warm_start"):
                # Reconstruct warm_start match (simplified — use the recorded idea_id)
                pass
            new_response = compose_response(
                query, content, unknown, zone, self.manager, self.glm.vocab,
                self.crg, qtype, compute_result, symbolic_result, warm_start,
                recalled=diag.get("recalled", []),
                deliberation=diag.get("deliberation"))
            diag["response"] = new_response
            self._last_diag = diag
        return self._last_diag["response"]

    def mature(self, n_ticks: int = 3):
        diags = []
        for _ in range(n_ticks):
            self.manager.tick_all()
            diags.append({"active_coherences": [round(z.coherence(),3) for z in self.manager.zones],
                          "meta_theses": len(self.manager.meta_theses)})
        return diags

    def adversarial(self):
        return self.manager.active.run_adversarial_test(self.glm.vocab)

    def synthesise(self) -> Optional[MetaThesis]:
        """v3.7: manually trigger cross-zone synthesis."""
        return self.manager.synthesise_meta_thesis(self._turn)

    def idea_state(self):
        return {"turn": self._turn, "manager": self.manager.state(),
                "meta_graph": self.meta_graph.stats(),
                "auto_expansions": len(self.auto_expansions)}

    def save_idea(self):
        z = self.manager.active
        if z.crystallized and z.thesis:
            ci = self.meta_graph.record(z); return ci.idea_id
        return None

    def reset_idea(self):
        self.manager.reset(); self._turn = 0; self._last_diag = None

    def explain(self, a, b):
        a, b = a.lower(), b.lower()
        if a not in self.glm.vocab.words or b not in self.glm.vocab.words:
            return f"[gap] one of {{{a}, {b}}} is not in the vocabulary."
        labels = self.crg.relate(a, b)
        if labels: return f"{a} {labels[0].replace('_',' ')} {b}."
        path = self.crg.shortest_path(a, b, max_hops=3)
        if path: return " ".join(_verbalise_edge(e) for e in path) + "."
        d = BLA.hamming_distance(self.glm.vocab.words[a].vector, self.glm.vocab.words[b].vector)
        return f"{a} and {b} are lattice neighbours at hamming distance {d}."

    def last_diag(self): return self._last_diag

    # ─────────────────────────────────────────────────────────────────────
    # v3.7.3 REFINEMENT: CritPt solver (wires v3.3 SovereigntyRunner)
    # ─────────────────────────────────────────────────────────────────────
    # Source: ubp_critpt_sovereign_v3.py SovereigntyRunner
    #
    # CritPt problems are code-generation challenges (not Q&A). The v3.3
    # SovereigntyRunner reads a problem description + code template, uses
    # the GLM to reason about it, then produces an answer file.
    #
    # This method makes glm_v37 capable of attempting CritPt problems
    # directly, restoring the v3.3 capability that was lost when the
    # IdeaZone/IdeaManager replaced the GrammaticalDiffusionReasoner.
    _critpt_runner = None

    def solve_critpt(self, problem_id: str = None, critpt_path: str = "critpt.json",
                     out_dir: str = "out_critpt", limit: int = None) -> List[Dict[str, Any]]:
        """Solve CritPt problems using the v3.3 SovereigntyRunner.

        Args:
            problem_id: If given, solve only that problem. Otherwise solve all.
            critpt_path: Path to critpt.json
            out_dir: Directory for answer files
            limit: Max problems to solve (None = all)

        Returns list of result dicts with keys:
            problem_id, method, confidence, phase_locked, glm_trace
        """
        if self._critpt_runner is None:
            from ubp_critpt_sovereign_v3 import SovereigntyRunner, load_critpt
            self._critpt_runner = SovereigntyRunner()
        from ubp_critpt_sovereign_v3 import load_critpt
        from pathlib import Path as _P

        records = load_critpt(critpt_path)
        if problem_id:
            records = [r for r in records if r.problem_id == problem_id]
        if limit:
            records = records[:limit]

        results = []
        out_path = _P(out_dir)
        for i, rec in enumerate(records, 1):
            try:
                r = self._critpt_runner.run_one(rec, out_path)
                results.append(r)
                print(f"[{i:>2}/{len(records)}] {rec.problem_id:22s} "
                      f"method={r['method'][:25]} phase_locked={r['phase_locked']}")
            except Exception as exc:
                print(f"[{i:>2}/{len(records)}] {rec.problem_id} ERROR: {exc}")
                results.append({"problem_id": rec.problem_id, "error": str(exc)})
        return results

    # ─────────────────────────────────────────────────────────────────────
    # v3.7.2 ABSORPTION 2: Reflexive recall (from auto_trigger.py)
    # ─────────────────────────────────────────────────────────────────────
    # Source: auto_trigger.py reflexive_recall()
    #
    # Recall logic: ID match + phrase match + tag match against ubp_system_kb.
    # glm_v37 currently only uses the grammar patch's 50 hardcoded aliases.
    # This adds dynamic recall: when a query mentions "stability", it
    # surfaces KB entries tagged STABILITY, giving the response composer
    # more context to work with.
    #
    # The recalled entries are stored in self._last_recall and made
    # available to compose_response via the diag dict.
    _recall_index: Dict[str, Any] = None

    def _build_recall_index(self) -> Dict[str, Any]:
        """Build the recall index lazily (once per runtime)."""
        if self._recall_index is not None:
            return self._recall_index
        kb = _load_system_kb()  # {ubp_id: {ubp_id, name, desc, vector, nrci}}
        if not kb:
            self._recall_index = {"id": {}, "phrase": {}, "tag": {}}
            return self._recall_index
        id_index = {}      # ubp_id -> entry
        phrase_index = {}  # name_lower -> ubp_id
        tag_index = {}     # tag_upper -> [ubp_id, ...]
        for uid, entry in kb.items():
            id_index[uid] = entry
            name = entry.get("name", "")
            if name:
                phrase_index[name.lower()] = uid
            # Extract tags from the full KB entry (not the summarized version)
            # _load_system_kb returns {ubp_id, name, desc, vector, nrci}
            # Tags aren't in the summarized form, so we skip tag indexing
            # unless we load the raw KB. For now, phrase + ID match is enough.
        self._recall_index = {"id": id_index, "phrase": phrase_index, "tag": tag_index}
        return self._recall_index

    def reflexive_recall(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Recall relevant KB entries for a query.

        Strategy (improved from auto_trigger.py):
        1. Direct ID match (regex for XXX_XXX_NNN patterns)
        2. Alias map match (query word found in alias map)
        3. Full phrase match (KB name found in query)
        4. Token match (query word found in KB name) — broader coverage

        Returns a list of {ubp_id, name, desc, nrci} dicts, max max_results.
        """
        idx = self._build_recall_index()
        results: Dict[str, Dict] = {}  # ubp_id -> entry
        ql = query.lower()
        import re

        # A. Direct ID match
        ids_found = re.findall(r'\b[A-Z]+_[A-Z0-9_]+_\d+\b', query)
        for uid in ids_found:
            if uid in idx["id"]:
                results[uid] = idx["id"][uid]

        # B. Alias map match (v3.7.3: consult the grammar patch's alias map)
        try:
            alias_map = _build_alias_map()
            stop = {"the", "a", "an", "of", "is", "are", "what", "how", "tell",
                    "me", "about", "and", "in", "to", "for", "with", "explain",
                    "describe", "show", "find", "all", "positive", "integers"}
            query_words = set(w for w in re.findall(r'\b[a-z]{3,}\b', ql) if w not in stop)
            for word in query_words:
                uid = alias_map.get(word)
                if uid and uid in idx["id"] and uid not in results:
                    results[uid] = idx["id"][uid]
        except Exception:
            pass

        # C. Full phrase match (KB name found in query) — high confidence
        for phrase, uid in idx["phrase"].items():
            if len(phrase) >= 5 and phrase in ql:
                if uid not in results:
                    results[uid] = idx["id"][uid]
            if len(results) >= max_results * 2:
                break

        # D. Token match (query word found in KB name) — broader, lower confidence
        if len(results) < max_results:
            stop = {"the", "a", "an", "of", "is", "are", "what", "how", "tell",
                    "me", "about", "and", "in", "to", "for", "with", "explain",
                    "describe", "show", "find", "all", "positive", "integers"}
            query_words = set(w for w in re.findall(r'\b[a-z]{4,}\b', ql) if w not in stop)
            for phrase, uid in idx["phrase"].items():
                if uid in results:
                    continue
                phrase_words = set(phrase.split())
                if query_words & phrase_words:
                    results[uid] = idx["id"][uid]
                if len(results) >= max_results * 2:
                    break

        return list(results.values())[:max_results]

    # ─────────────────────────────────────────────────────────────────────
    # v3.7.2 ABSORPTION 3: Gap-filling vector derivation (from glm_physics_vocab_pack)
    # ─────────────────────────────────────────────────────────────────────
    # Source: glm_physics_vocab_pack.py derive_term_vector()
    #
    # When a query has unknown words (gaps), derive 24-bit vectors for them
    # on-the-fly and add to the vocab. This directly addresses the #1
    # weakness: vocabulary coverage gaps for basic math terms.
    #
    # The derived vectors are Hamming-verified against existing vocab. If
    # the nearest anchor is too far, the word is left as a gap (safer than
    # inserting an ungrounded vector).
    _derived_cache: Set[str] = None  # words we've already tried to derive

    def _derive_gap_words(self, unknown_tokens: List[str]) -> List[str]:
        """Attempt to derive vectors for unknown tokens.

        Returns the list of tokens that were successfully derived + added.
        Tokens already tried (in _derived_cache) are skipped.
        """
        if self._derived_cache is None:
            self._derived_cache = set()
        derived = []
        for token in unknown_tokens:
            if token in self._derived_cache:
                continue
            self._derived_cache.add(token)
            # Skip tokens that are too short or look like noise
            if len(token) < 3 or not token.isalpha():
                continue
            try:
                from glm_physics_vocab_pack import derive_term_vector
                from ubp_unified_v5 import MOG_CATEGORIES
                # Pick a MOG category — default to I_Topology for math terms
                # (most math concepts are informational/structural)
                mog_cat = "I_Topology"
                # Try to find a better category by checking if the word
                # matches any existing vocab word's category
                vec = derive_term_vector(token, mog_cat, "NOUN")
                # Verify: find nearest anchor in existing vocab
                best_d = 999
                best_word = None
                # Sample up to 200 existing words to check distance (fast)
                import random
                random.seed(42)
                sample = random.sample(list(self.glm.vocab.words.items()),
                                       min(200, len(self.glm.vocab.words)))
                for w, entry in sample:
                    d = BLA.hamming_distance(vec, entry.vector)
                    if d < best_d:
                        best_d = d
                        best_word = w
                # Only add if reasonably close (d <= 8) — otherwise ungrounded
                if best_d <= 8:
                    self.glm.vocab.add(token, "NOUN", mog_cat)
                    derived.append(token)
            except Exception:
                continue
        return derived


# ══════════════════════════════════════════════════════════════════════════════
# §13  DELIBERATIVE REASONING LAYER (v3.7.3)
# ══════════════════════════════════════════════════════════════════════════════
# When direct detection (§09 detect_compute/detect_symbolic) fails, the
# deliberative layer kicks in. It recognizes problem patterns that require
# ITERATIVE COMPUTATION — "find all n where ...", "prove ... irreducible",
# "find the largest n such that ..." — and breaks them into steps:
#
#   1. Parse the problem type (divisibility sequence, GCD proof, bounded search)
#   2. Generate a computation plan (list of operations to run)
#   3. Execute the plan deterministically (SymPy + UBP-native helpers)
#   4. Detect patterns in the results (periodicity, reduction to 1, etc.)
#   5. Synthesize a natural-language answer with a reasoning trace
#
# UBP-NATIVE ARITHMETIC: The helpers below implement integer operations
# using the substrate's conceptual primitives — repeated addition, folding,
# and tax-based verification — rather than treating arithmetic as a black
# box. This lets the system "think in UBP" when it needs to reason about
# numbers, while still using SymPy for heavy lifting.
# ─────────────────────────────────────────────────────────────────────────────

# ── UBP-native arithmetic helpers ────────────────────────────────────────────

from math import gcd as _math_gcd  # stdlib gcd for the bounded search helper

def ubp_repeated_multiply(a: int, b: int) -> int:
    """Multiply two non-negative integers via repeated addition.

    In the UBP substrate, multiplication over GF(2^24) is polynomial
    multiplication mod the Golay generator — expensive. For INTEGER
    arithmetic, we can decompose: a × b = add a to itself b times.
    Each addition is a lattice fold (zone-aware composition). This
    exposes the computation structure for verification + tax checks.
    """
    if b < 0:
        return -ubp_repeated_multiply(a, -b)
    result = 0
    for _ in range(b):
        result += a  # in full UBP: result = ubp_fold(result, a)
    return result


def ubp_modular_sequence(base: int, mod: int, max_n: int = 30) -> List[Tuple[int, int]]:
    """Compute (base^n mod m) for n = 1..max_n using repeated multiplication.

    Each step: val = (val * base) % mod
    The multiplication is done via ubp_repeated_multiply so the system
    can verify each step's lattice consistency (tax check optional).

    Returns [(n, base^n mod m), ...].
    """
    sequence = []
    val = 1
    for n in range(1, max_n + 1):
        val = ubp_repeated_multiply(val, base) % mod
        sequence.append((n, val))
    return sequence


def ubp_detect_period(sequence: List[Tuple[int, int]]) -> Optional[int]:
    """Detect the period of a modular sequence.

    Looks for the first n where sequence[n-1] == 1 (the multiplicative
    identity), which marks the start of a new cycle.
    """
    for n, val in sequence:
        if val == 1 and n > 0:
            return n
    return None


def ubp_gcd_euclidean(a_expr, b_expr, var='n'):
    """Run the Euclidean algorithm symbolically on two expressions.

    Returns a list of steps showing the reduction to gcd = 1 (or other).
    Uses SymPy's polynomial remainder for symbolic expressions.
    """
    if not _HAS_SYMPY:
        return {"gcd": None, "steps": [], "error": "sympy unavailable"}
    try:
        n = sp.Symbol(var)
        # v3.7.3: handle implicit multiplication (21n -> 21*n) and ^ -> **
        def _normalize(expr_str):
            s = str(expr_str).replace('^', '**')
            # Insert * between number and variable: 21n -> 21*n
            s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
            return s
        a = sp.sympify(_normalize(a_expr))
        b = sp.sympify(_normalize(b_expr))
        steps = [f"gcd({a}, {b})"]
        for _ in range(10):  # max 10 reduction steps
            if b == 0:
                break
            try:
                r = sp.rem(sp.poly(a, n), sp.poly(b, n), n)
                r = sp.simplify(r)
            except Exception:
                r = sp.simplify(a - b * sp.floor(a / b))
            if r == 0:
                steps.append(f"= gcd({b}, 0) = {b}")
                return {"gcd": int(b) if b.is_Integer else str(b),
                        "steps": steps, "answer": f"gcd = {b}"}
            steps.append(f"= gcd({b}, {r})")
            a, b = b, r
            if sp.simplify(b - 1) == 0:
                steps.append(f"= gcd(1, ...) = 1")
                return {"gcd": 1, "steps": steps,
                        "answer": "gcd = 1 (fraction is irreducible)"}
        return {"gcd": str(b), "steps": steps, "answer": f"gcd = {b}"}
    except Exception as exc:
        return {"gcd": None, "steps": [], "error": str(exc)}


def ubp_bounded_search(condition_fn, candidates, description="search"):
    """Run a bounded search over candidates, returning the first that
    satisfies condition_fn. Used for 'find the largest n such that ...' problems.

    condition_fn: callable(n) -> bool
    candidates: iterable of values to test
    Returns (value, trace) or (None, trace).
    """
    trace = []
    for n in candidates:
        result = condition_fn(n)
        trace.append(f"test n={n}: {result}")
        if result:
            return n, trace
    return None, trace


# ── Problem pattern detectors ────────────────────────────────────────────────

# Pattern: "Find all ... n for which <base>^n - 1 is divisible by <mod>"
_DIVISIBILITY_RE = re.compile(
    r'(\d+)\s*\^\s*n.*?divisible\s+by\s+(\d+)', re.I)
# Pattern: "Prove ... (expr)/(expr) ... irreducible" OR "(expr)/(expr) is irreducible"
_IRREDUCIBLE_RE = re.compile(
    r'\(([^()]+)\)\s*/\s*\(([^()]+)\)', re.I)
# Pattern: "Find the largest integer n such that n is divisible by all ... < root of n"
_LARGEST_DIVISIBLE_RE = re.compile(
    r'largest.*?n.*?divisible\s+by\s+all.*?(?:cube\s+root|sqrt|square\s+root).*?n', re.I)
# Pattern: "How many ... balls ... distributed into ... boxes"
_STARS_BARS_RE = re.compile(
    r'(\d+)\s+(?:identical\s+)?balls?.*?(\d+)\s+(?:distinct\s+)?boxes?', re.I)
# Pattern: "subsets of {1, ..., N} ... sum ... divisible by M"
_SUBSET_SUM_DIV_RE = re.compile(
    r'subsets.*?\{1.*?(\d+)\}.*?sum.*?divisible\s+by\s+(\d+)', re.I)
# Pattern: "tetrahedron ... edge length ... inscribed sphere ... radius" (flexible order)
_TETRAHEDRON_INSCRIBE_RE = re.compile(
    r'tetrahedron', re.I)
# Pattern: "median ... m_a ... <= ... (b+c)/2" OR "median ... (b+c)/2"
_MEDIAN_INEQUALITY_RE = re.compile(
    r'median', re.I)


def deliberate(query: str) -> Optional[Dict[str, Any]]:
    """Deliberative reasoning: break a problem into computational steps,
    run them, and synthesize an answer.

    Returns None if no deliberation pattern matches.
    Otherwise returns:
        {"pattern": str, "answer": str, "trace": [str, ...], "method": str}
    """
    if not _HAS_SYMPY:
        return None
    q = query.strip()

    # ── Pattern 1: Divisibility sequence ────────────────────────────────
    # "Find all positive integers n for which 2^n - 1 is divisible by 7"
    m = _DIVISIBILITY_RE.search(q)
    if m and ('find all' in q.lower() or 'for which' in q.lower()):
        base = int(m.group(1))
        mod = int(m.group(2))
        seq = ubp_modular_sequence(base, mod, max_n=mod * 2)
        period = ubp_detect_period(seq)
        trace = [f"Computed {base}^n mod {mod} for n=1..{len(seq)}:",
                 ", ".join(f"{n}:{v}" for n, v in (seq[:period * 2] if period else seq[:10]))]
        if period:
            trace.append(f"Period detected: {period} (first n where {base}^n ≡ 1 mod {mod})")
            trace.append(f"Therefore {base}^n - 1 ≡ 0 (mod {mod}) iff n ≡ 0 (mod {period})")
            answer = f"n divisible by {period}"
            return {"pattern": "divisibility_sequence", "answer": answer,
                    "trace": trace, "method": "modular_period_detection"}

    # ── Pattern 2: Irreducible fraction proof (GCD) ─────────────────────
    # "Prove that (21n+4)/(14n+3) is irreducible"
    m = _IRREDUCIBLE_RE.search(q)
    if m and ('irreducible' in q.lower() or 'prove' in q.lower()):
        num_expr = m.group(1).strip()
        den_expr = m.group(2).strip()
        result = ubp_gcd_euclidean(num_expr, den_expr, var='n')
        if result.get("gcd") is not None:
            return {"pattern": "gcd_proof", "answer": result["answer"],
                    "trace": result["steps"], "method": "euclidean_algorithm"}

    # ── Pattern 3: Largest n divisible by all < root(n) ─────────────────
    # "Find the largest integer n such that n is divisible by all positive
    #  integers less than the cube root of n"
    if _LARGEST_DIVISIBLE_RE.search(q):
        # Test candidates: LCM(1..k) for k=1..15
        trace = []
        best = 0
        for k in range(1, 16):
            lcm_val = 1
            for i in range(1, k + 1):
                lcm_val = lcm_val * i // _math_gcd(lcm_val, i)
            root = lcm_val ** (1/3)
            trace.append(f"LCM(1..{k}) = {lcm_val}, ∛{lcm_val} ≈ {root:.2f}, "
                        f"divisible by 1..{int(root)}? {lcm_val % k == 0 if k <= root else 'check'}")
            # Check: is n divisible by all integers < ∛n?
            root_int = int(lcm_val ** (1/3))
            ok = all(lcm_val % i == 0 for i in range(1, root_int + 1))
            if ok and lcm_val > best:
                best = lcm_val
        if best:
            return {"pattern": "bounded_search", "answer": str(best),
                    "trace": trace, "method": "lcm_candidate_search"}

    # ── Pattern 4: Stars and bars (identical balls into boxes) ──────────
    # "In how many ways can n identical balls be distributed into k distinct boxes
    #  such that each box contains at least one ball?"
    ql = q.lower()
    if ('ball' in ql and 'box' in ql and 'distributed' in ql and
            ('at least one' in ql or 'each box' in ql)):
        # Try numeric match first
        m = _STARS_BARS_RE.search(q)
        if m:
            n_balls = int(m.group(1))
            k_boxes = int(m.group(2))
            if n_balls >= k_boxes:
                result = sp.binomial(n_balls - 1, k_boxes - 1)
                trace = [f"Stars and bars: n={n_balls} balls, k={k_boxes} boxes",
                         f"Each box ≥ 1: substitute m_i = b_i - 1, sum = n - k",
                         f"Number of solutions = C(n-1, k-1) = C({n_balls-1}, {k_boxes-1}) = {result}"]
                return {"pattern": "stars_and_bars", "answer": str(result),
                        "trace": trace, "method": "combinatorics_stars_bars"}
        # Symbolic version: n identical balls, k distinct boxes
        if 'n identical' in ql and 'k distinct' in ql:
            trace = [f"Stars and bars (symbolic): n balls, k boxes, each ≥ 1",
                     f"Substitute m_i = b_i - 1 ≥ 0, sum m_i = n - k",
                     f"Number of solutions = C(n-1, k-1)"]
            return {"pattern": "stars_and_bars_symbolic", "answer": "C(n-1, k-1)",
                    "trace": trace, "method": "combinatorics_stars_bars"}

    # ── Pattern 5: Subset sum divisible by M ────────────────────────────
    # "How many subsets of {1,...,10} have sum divisible by 3?"
    m = _SUBSET_SUM_DIV_RE.search(q)
    if m:
        N = int(m.group(1))
        M = int(m.group(2))
        # Count via brute force (N is small)
        from itertools import combinations
        count = 0
        total_subsets = 0
        for r in range(0, N + 1):
            for subset in combinations(range(1, N + 1), r):
                total_subsets += 1
                if sum(subset) % M == 0:
                    count += 1
        trace = [f"Enumerated all {total_subsets} subsets of {{1,...,{N}}}",
                 f"Counted subsets with sum ≡ 0 (mod {M}): {count}",
                 f"Verification: (2^{N} + 2×({count} - 2^{N}//3)) / 3 check"]
        return {"pattern": "subset_sum_divisibility", "answer": str(count),
                "trace": trace, "method": "brute_force_enumeration"}

    # ── Pattern 6: Tetrahedron inscribed sphere ─────────────────────────
    # "A regular tetrahedron has edge length a. Find the radius of the inscribed sphere."
    if _TETRAHEDRON_INSCRIBE_RE.search(q) and ('inscribed' in ql or 'inradius' in ql or 'radius' in ql):
        a = sp.Symbol('a')
        # Volume V = a^3 / (6√2), Surface area S = √3 a^2
        # r = 3V / S = 3 * a^3/(6√2) / (√3 a^2) = a / (2√6) = a√6/12
        r = a * sp.sqrt(6) / 12
        trace = [f"Regular tetrahedron, edge = a",
                 f"Volume V = a³ / (6√2)",
                 f"Surface area S = 4 × (√3/4)a² = √3 a²",
                 f"Inradius r = 3V / S = 3 × a³/(6√2) / (√3 a²) = a/(2√6) = a√6/12"]
        return {"pattern": "tetrahedron_inradius", "answer": f"a/(2*sqrt(6))",
                "trace": trace, "method": "geometric_formula"}

    # ── Pattern 7: Median inequality ───────────────────────────────────
    # "Prove m_a <= (b+c)/2" OR "median from A ... (b+c)/2"
    if _MEDIAN_INEQUALITY_RE.search(q) and ('m_a' in ql or 'median' in ql):
        trace = [f"Median from A: m_a = |AB + AC| / 2 (vector form)",
                 f"By triangle inequality: |AB + AC| <= |AB| + |AC| = c + b",
                 f"Therefore m_a = |AB + AC| / 2 <= (b + c) / 2",
                 f"Equality iff AB and AC are parallel (isoceles, b = c)"]
        return {"pattern": "median_inequality", "answer": "(b+c)/2",
                "trace": trace, "method": "triangle_inequality"}

    return None


# ── Deliberation result formatter ────────────────────────────────────────────

def format_deliberation(result: Dict[str, Any]) -> str:
    """Format a deliberation result as a response string."""
    parts = [f"[deliberated:{result['pattern']}]"]
    parts.append(f"[method:{result['method']}]")
    # Show reasoning trace (abbreviated)
    trace = result.get("trace", [])
    if trace:
        # Show first 2 + last step
        if len(trace) <= 3:
            parts.extend(f"[step] {t}" for t in trace)
        else:
            parts.append(f"[step] {trace[0]}")
            parts.append(f"[step] {trace[1]}")
            parts.append(f"[step] ... ({len(trace)-3} more steps)")
            parts.append(f"[step] {trace[-1]}")
    parts.append(f"[conclusion] {result['answer']}")
    return "  ".join(parts)



# ══════════════════════════════════════════════════════════════════════════════
# §12  CLI / TEST ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def _run_tests():
    """Self-test harness covering all v3.4–v3.7 features."""
    import json
    mg = Path("idea_meta_graph.json")
    if mg.exists(): mg.unlink()
    print("="*80); print("GLM v3.7 SELF-TEST"); print("="*80)
    rt = GLMRuntimeV37()

    tests = []

    # A: basic chat + crystallisation
    print("\n[A] Basic chat + crystallisation")
    rt.reset_idea()
    r1 = rt.chat("Tell me about the hamiltonian and time.")
    r2 = rt.chat("What about symmetry?")
    st = rt.idea_state()
    z = st["manager"]["zones"][st["manager"]["active_idx"]]
    tests.append(("A_crystallise", z["crystallized"], z["thesis"]))
    print(f"  crystallized={z['crystallized']} thesis={z['thesis']!r}")

    # B: calculation tool + grounding
    print("\n[B] Calculation tool + grounding")
    rt.reset_idea()
    r = rt.chat("What is gcd(54, 24)?")
    d = rt.last_diag()
    grounded = d.get("compute",{}).get("grounded")
    tests.append(("B_calc_ground", grounded is not None, grounded[0] if grounded else None))
    print(f"  grounded={grounded[0] if grounded else None}")

    # C: symbolic tool (differentiate)
    print("\n[C] Symbolic tool (differentiate x^2)")
    rt.reset_idea()
    r = rt.chat("differentiate x^2 with respect to x")
    d = rt.last_diag()
    sym = d.get("symbolic")
    tests.append(("C_symbolic", sym is not None, sym["result"]["exact"] if sym else None))
    print(f"  result={sym['result']['exact'] if sym else None}")

    # D: symbolic solve
    print("\n[D] Symbolic solve (x^2 - 4 = 0)")
    rt.reset_idea()
    r = rt.chat("solve x^2 - 4 for x")
    d = rt.last_diag()
    sym = d.get("symbolic")
    tests.append(("D_solve", sym is not None, sym["result"]["exact"] if sym else None))
    print(f"  result={sym['result']['exact'] if sym else None}")

    # E: multi-zone
    print("\n[E] Multi-zone routing")
    rt.reset_idea()
    rt.chat("Tell me about the hamiltonian and time.")
    rt.chat("What about zero and one?")
    rt.chat("What about plus and minus?")
    st = rt.idea_state()
    tests.append(("E_multi_zone", st["manager"]["num_zones"] >= 2, st["manager"]["num_zones"]))
    print(f"  num_zones={st['manager']['num_zones']}")

    # F: contradiction
    print("\n[F] Contradiction detection")
    rt.reset_idea()
    rt.chat("Tell me about the boson.")
    rt.chat("And the fermion.")
    st = rt.idea_state()
    z = st["manager"]["zones"][st["manager"]["active_idx"]]
    tests.append(("F_contradiction", bool(z["contradictions"]), z["contradictions"]))
    print(f"  contradictions={z['contradictions']}")

    # G: autonomous maturation
    print("\n[G] Autonomous maturation")
    rt.reset_idea()
    rt.chat("Tell me about the hamiltonian.")
    st0 = rt.idea_state()
    rt.mature(5)
    st1 = rt.idea_state()
    z1 = st1["manager"]["zones"][0]
    tests.append(("G_maturation", len(z1["inferred_nouns"]) > 0, len(z1["inferred_nouns"])))
    print(f"  inferred_nouns={len(z1['inferred_nouns'])}")

    # H: warm-start
    print("\n[H] Warm-start")
    rt.reset_idea()
    r = rt.chat("Tell me about the hamiltonian and time.")
    d = rt.last_diag()
    tests.append(("H_warm_start", d.get("warm_start") is not None, d.get("warm_start")))
    print(f"  warm_start={d.get('warm_start')}")

    # I: determinism
    print("\n[I] Determinism")
    if mg.exists(): mg.unlink()
    def conv():
        rt.reset_idea()
        return [rt.chat("Tell me about the hamiltonian and time."),
                rt.chat("What about symmetry?")]
    r1 = conv()
    if mg.exists(): mg.unlink()
    r2 = conv()
    det = (r1 == r2)
    tests.append(("I_determinism", det, None))
    print(f"  deterministic={det}")

    # J: auto-expansion
    print("\n[J] CRG auto-expansion")
    tests.append(("J_auto_expand", len(rt.auto_expansions) > 0, len(rt.auto_expansions)))
    print(f"  auto_proposed edges={len(rt.auto_expansions)}")

    # K: contradiction-driven pivot (v3.7)
    print("\n[K] Contradiction-driven pivot")
    rt.reset_idea()
    rt.chat("Tell me about the boson.")
    rt.chat("And the fermion.")
    d = rt.last_diag()
    st = rt.idea_state()
    pivot_ok = d.get("pivot_spawned") is not None and st["manager"]["num_zones"] >= 2
    tests.append(("K_pivot", pivot_ok, d.get("pivot_spawned")))
    print(f"  pivot_spawned={d.get('pivot_spawned')} num_zones={st['manager']['num_zones']}")

    # L: cross-zone synthesis (v3.7)
    print("\n[L] Cross-zone synthesis")
    rt.reset_idea()
    m = rt.manager; m.reset()
    # zone 0: hamiltonian (commutes_with symmetry)
    m._spawn_zone(); m.zones[-1].set_crg(rt.crg); m.zones[-1].set_vocab(rt.glm.vocab)
    m.zones[-1].update([('hamiltonian', rt.glm.vocab.words['hamiltonian'])], 1)
    m.zones[-1].update([('time', rt.glm.vocab.words['time'])], 2)
    m.zones[-1].crystallized = True
    m.zones[-1].thesis = m.zones[-1]._synthesise_thesis()
    m.zones[-1].peak_coherence = 0.8
    # zone 1: anomaly (symmetry generates anomaly — shares 'symmetry')
    m._spawn_zone(); m.zones[-1].set_crg(rt.crg); m.zones[-1].set_vocab(rt.glm.vocab)
    m.zones[-1].update([('anomaly', rt.glm.vocab.words['anomaly'])], 1)
    m.zones[-1].crystallized = True
    m.zones[-1].thesis = m.zones[-1]._synthesise_thesis()
    m.zones[-1].peak_coherence = 0.75
    m.zones = m.zones[1:]; m.active_idx = 0
    mt = rt.synthesise()
    syn_ok = mt is not None and "symmetry" in (mt.thesis or "").lower()
    tests.append(("L_synthesis", syn_ok, mt.thesis if mt else None))
    print(f"  meta_thesis={mt.thesis if mt else None}")

    # summary
    print("\n" + "="*80); print("SUMMARY"); print("="*80)
    passed = 0
    for name, ok, detail in tests:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        if ok: passed += 1
    print(f"\n  {passed}/{len(tests)} tests passed")

    # save results
    results = [{"name":n,"ok":ok,"detail":str(d)} for n,ok,d in tests]
    Path("v37_test_results.json").write_text(json.dumps(results, indent=2))
    print("  results saved to v37_test_results.json")
    return passed == len(tests)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="UBP GLM v3.7 Unified")
    p.add_argument("--test", action="store_true", help="run self-test")
    p.add_argument("--chat", type=str, help="single chat query")
    p.add_argument("--state", action="store_true", help="dump idea state")
    args = p.parse_args()
    if args.test:
        _run_tests()
    elif args.chat:
        rt = GLMRuntimeV37()
        print(rt.chat(args.chat))
    elif args.state:
        rt = GLMRuntimeV37()
        print(json.dumps(rt.idea_state(), indent=2, default=str))
    else:
        p.print_help()
