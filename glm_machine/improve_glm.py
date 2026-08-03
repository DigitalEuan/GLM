#!/usr/bin/env python3
"""
GLM Improvement Engine
=======================
Systematically improves the GLM's abilities:
1. Ingests elemental chromatic data
2. Ingests study findings (gravity, rainbow)
3. Improves response quality
4. Adds UBP-specific reasoning patterns
5. Enhances Three Column Thinking
"""

import json
import sys
import os
import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
UBP_DIR = BASE_DIR / "ubp_repo"
sys.path.insert(0, str(SERVER_DIR))
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)

def load_kb():
    kb = json.loads((DATA_DIR / "ubp_system_kb.json").read_text())
    fields = kb['_fields']
    entries = kb['entries']
    indexed = {}
    for h, entry_list in entries.items():
        if isinstance(entry_list, list) and len(entry_list) >= 1:
            indexed[entry_list[0]] = dict(zip(fields, entry_list))
    return indexed

def improve_glm():
    print("=" * 60)
    print("GLM Improvement Engine")
    print("=" * 60)
    
    # Initialize GLM
    print("\n[1] Initializing GLM...")
    from GLM00_config import KB_SYSTEM_PATH, KB_LANG_PATH
    GLM00_config = __import__('GLM00_config')
    GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
    GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"
    
    from GLM11_runtime import GLMRuntimeV37
    from GLM01_substrate import WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
    rt = GLMRuntimeV37(auto_expand=True)
    print(f"    Vocab: {len(rt.vocab_dict)}, Edges: {len(rt.crg.edges)}")
    
    # Load KB
    print("\n[2] Loading knowledge bases...")
    indexed = load_kb()
    
    # ── PHASE 1: Ingest Elemental Chromatic Data ──────────────────────
    print("\n[3] Ingesting elemental chromatic data...")
    elem_file = UBP_DIR / "elemental_chromatic" / "01" / "data" / "elemental_chromatic_data.json"
    if elem_file.exists():
        elements = json.loads(elem_file.read_text())
        for elem in elements:
            name = elem.get('name', '').split('(')[0].strip().lower()
            if not name: continue
            vector = elem.get('vector', [0]*24)
            nrci = elem.get('nrci', 0.5)
            ubp_id = elem.get('ubp_id', '')
            z = elem.get('z', 0)
            
            if name not in rt.vocab_dict:
                try:
                    snapped, _ = GOLAY_ENGINE.snap_to_codeword(vector)
                except:
                    snapped = vector
                nrci_val = float(LEECH_ENGINE.calculate_nrci(snapped))
                
                entry = WordEntry(
                    word=name, vector=snapped, role="NOUN",
                    ubp_id=ubp_id, nrci=nrci_val,
                    golay_codeword=snapped,
                    fold3=BLA.fold24_to3(snapped),
                    mog_category=_get_mog_category(snapped)
                )
                entry.definition = f"Element {z} ({name}), atomic number {z}, NRCI={nrci:.4f}"
                rt.vocab_dict[name] = entry
                
                # Connect to periodic table
                rt.crg.add_edge(name, "is_a", "element")
                rt.crg.add_edge(name, "has_property", "atomic")
                if z > 1:
                    rt.crg.add_edge(name, "follows", f"element_{z-1}")
        
        print(f"    Ingested {len(elements)} elements")
    
    # ── PHASE 2: Ingest Study Findings ────────────────────────────────
    print("\n[4] Ingesting study findings...")
    
    # Rainbow study findings
    rainbow_findings = [
        ("rainbow", "is_a", "optical phenomenon"),
        ("rainbow", "depends_on", "refraction"),
        ("rainbow", "depends_on", "dispersion"),
        ("rainbow", "has_property", "geometric"),
        ("primary rainbow", "is_a", "rainbow"),
        ("secondary rainbow", "is_a", "rainbow"),
        ("primary rainbow", "occurs_at", "42 degrees"),
        ("secondary rainbow", "occurs_at", "51.8 degrees"),
        ("golden ratio", "appears_in", "rainbow"),
        ("golden ratio", "is_a", "irrational"),
        ("golden ratio", "approximates", "1.618"),
        ("dodecahedron", "is_a", "platonic solid"),
        ("dodecahedron", "relates_to", "golden ratio"),
        ("refraction", "is_a", "optical process"),
        ("refraction", "depends_on", "refractive index"),
        ("dispersion", "is_a", "optical process"),
        ("dispersion", "depends_on", "wavelength"),
    ]
    
    # Gravity study findings
    gravity_findings = [
        ("gravity", "is_a", "fundamental force"),
        ("gravity", "depends_on", "curvature"),
        ("gravitational constant", "measures", "gravity"),
        ("gravitational constant", "is_a", "physical constant"),
        ("leech lattice", "encodes", "gravity"),
        ("substrate", "generates", "gravity"),
        ("mass", "curves", "spacetime"),
        ("einstein", "formulated", "general relativity"),
        ("general relativity", "describes", "gravity"),
        ("spacetime", "curved_by", "mass"),
    ]
    
    # UBP core principles
    ubp_principles = [
        ("universal binary principle", "is_a", "framework"),
        ("universal binary principle", "describes", "reality"),
        ("universal binary principle", "uses", "24-bit substrate"),
        ("24-bit substrate", "is_a", "computational structure"),
        ("24-bit substrate", "contains", "golay code"),
        ("24-bit substrate", "contains", "leech lattice"),
        ("golay code", "provides", "error correction"),
        ("golay code", "is_a", "algebraic code"),
        ("golay code", "corrects", "3-bit errors"),
        ("leech lattice", "is_a", "sphere packing"),
        ("leech lattice", "has_dimension", "24"),
        ("leech lattice", "achieves", "optimal packing"),
        ("nrci", "stands_for", "normalized root coherence index"),
        ("nrci", "measures", "coherence"),
        ("nrci", "ranges_from", "0 to 1"),
        ("observer constant", "is_a", "fundamental constant"),
        ("observer constant", "derived_from", "pi"),
        ("observer constant", "formula", "1/(pi+2/pi)"),
        ("triadic monad", "is_a", "mathematical structure"),
        ("triadic monad", "equals", "pi * phi * e"),
        ("entropic wobble", "is_a", "noise"),
        ("entropic wobble", "measures", "disorder"),
        ("coherence snap", "is_a", "process"),
        ("coherence snap", "stabilizes", "information"),
        ("symmetry tax", "measures", "geometric cost"),
        ("symmetry tax", "depends_on", "lattice structure"),
        ("barnes-wall lattice", "is_a", "lattice"),
        ("barnes-wall lattice", "has_dimension", "256"),
        ("barnes-wall lattice", "extends", "leech lattice"),
        ("error correction", "preserves", "information"),
        ("error correction", "uses", "golay code"),
        ("hamming distance", "measures", "bit differences"),
        ("hamming distance", "used_by", "error correction"),
        ("octad", "is_a", "code structure"),
        ("octad", "has_size", "8"),
        ("octad", "part_of", "golay code"),
        ("sextet", "is_a", "code structure"),
        ("sextet", "has_size", "6"),
        ("sextet", "divides", "24-bit vector"),
        ("mog", "stands_for", "miracle octad generator"),
        ("mog", "generates", "golay codewords"),
        ("gray code", "is_a", "encoding"),
        ("gray code", "minimizes", "bit changes"),
    ]
    
    all_findings = rainbow_findings + gravity_findings + ubp_principles
    edges_added = 0
    for src, label, dst in all_findings:
        for w in [src, dst]:
            if w not in rt.vocab_dict:
                from GLM import TextMiner
                miner = TextMiner(rt.vocab_dict, rt.crg)
                miner._create_word(w)
        rt.crg.add_edge(src, label, dst)
        edges_added += 1
    
    print(f"    Added {edges_added} curated edges")
    
    # ── PHASE 3: Enrich Definitions from KB ────────────────────────────
    print("\n[5] Enriching definitions from KB...")
    definitions_added = 0
    
    # Map KB entries to vocab words
    for uid, entry in indexed.items():
        lexicon = str(entry.get('lexicon', ''))
        name_match = re.match(r'\[?(?:Law|Element|Molecule|Particle|Math|Reaction|Tool|Algo|Crystal)?:?\s*(.+?)\]?', lexicon)
        if not name_match: continue
        name = name_match.group(1).strip()
        name = re.sub(r'^\[', '', name).strip()
        name = re.sub(r'\]$', '', name).strip()
        
        # Clean for vocab key
        word_key = name.lower().strip()
        word_key = re.sub(r'[^\w\s-]', '', word_key).strip()
        if not word_key or len(word_key) < 3: continue
        
        # Extract definition
        defn_match = re.search(r'\]?\s*,?\s*(.{20,})', lexicon)
        if defn_match:
            defn = defn_match.group(1).strip()
            defn = re.sub(r'^\[', '', defn)
            defn = re.sub(r'\]$', '', defn)
            defn = defn[:300]
            
            # Update if word exists and has no definition
            if word_key in rt.vocab_dict:
                if not getattr(rt.vocab_dict[word_key], 'definition', None):
                    rt.vocab_dict[word_key].definition = defn
                    definitions_added += 1
    
    print(f"    Enriched {definitions_added} definitions")
    
    # ── PHASE 4: Add Element-Law Connections ──────────────────────────
    print("\n[6] Building element-law connections...")
    element_law_edges = 0
    
    # Connect elements to their related laws
    elem_law_map = {
        "hydrogen": ["LAW_BIO_AQUEOUS_LENS_001", "LAW_AQUEOUS_BOND_001"],
        "oxygen": ["LAW_BIO_AQUEOUS_LENS_001", "LAW_AQUEOUS_BOND_001"],
        "carbon": ["LAW_BIO_007", "LAW_BIO_008"],
        "iron": ["LAW_BIO_HEMA_002"],
        "calcium": ["LAW_BIO_GOLD_001"],
        "gold": ["LAW_BIO_GOLD_001"],
    }
    
    for elem, law_uids in elem_law_map.items():
        if elem not in rt.vocab_dict: continue
        for law_uid in law_uids:
            if law_uid in indexed:
                lex = str(indexed[law_uid].get('lexicon', ''))
                law_name_match = re.match(r'\[?(?:Law)?:?\s*(.+?)\]?', lex)
                if law_name_match:
                    law_name = law_name_match.group(1).strip().lower()
                    law_name = re.sub(r'[^\w\s-]', '', law_name).strip()
                    if law_name and law_name not in rt.vocab_dict:
                        from GLM import TextMiner
                        miner = TextMiner(rt.vocab_dict, rt.crg)
                        miner._create_word(law_name)
                    if law_name:
                        rt.crg.add_edge(elem, "governed_by", law_name)
                        element_law_edges += 1
    
    print(f"    Added {element_law_edges} element-law connections")
    
    # ── PHASE 5: Persist Everything ───────────────────────────────────
    print("\n[7] Persisting improvements...")
    from GLM_persistence import GLMPersistence
    persist = GLMPersistence(str(BASE_DIR / "glm_state"))
    
    for word, entry in rt.vocab_dict.items():
        defn = getattr(entry, 'definition', '')
        if defn:
            persist.save_vocab(word, defn, list(entry.vector), source="improvement")
    
    for edge in rt.crg.edges:
        persist.save_edge(edge.src, edge.label, edge.dst, source="improvement")
    
    # Final stats
    print("\n" + "=" * 60)
    print("IMPROVEMENT COMPLETE")
    print("=" * 60)
    print(f"  Final vocabulary: {len(rt.vocab_dict)}")
    print(f"  Final CRG edges: {len(rt.crg.edges)}")
    print(f"  New edges added: {edges_added}")
    print(f"  Definitions enriched: {definitions_added}")
    print(f"  Element-law connections: {element_law_edges}")
    print("=" * 60)
    
    return rt

if __name__ == "__main__":
    rt = improve_glm()
    
    # Comprehensive test suite
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tests = [
        # UBP Core
        ("What is the Universal Binary Principle?", "ubp"),
        ("Explain the 24-bit substrate.", "substrate"),
        ("What is the Golay code?", "golay"),
        ("What is NRCI?", "nrci"),
        ("What is the Observer Constant?", "observer"),
        ("What is the Triadic Monad?", "monad"),
        ("What is the Entropic Wobble?", "wobble"),
        
        # Physics
        ("What is gravity?", "gravity"),
        ("How does mass curve spacetime?", "spacetime"),
        ("What is a boson?", "boson"),
        ("What is a fermion?", "fermion"),
        ("How do photons work?", "photon"),
        
        # Chemistry
        ("What is hydrogen?", "hydrogen"),
        ("What is oxygen?", "oxygen"),
        ("What is water?", "water"),
        
        # Mathematics
        ("What is symmetry?", "symmetry"),
        ("What is the golden ratio?", "golden ratio"),
        ("What is pi?", "pi"),
        
        # Cross-domain
        ("How does error correction relate to biology?", "error correction + biology"),
        ("What is the relationship between gravity and the substrate?", "gravity + substrate"),
        ("How does coherence relate to life?", "coherence + life"),
    ]
    
    for query, topic in tests:
        print(f"\n{'─'*40}")
        print(f"Q: {query}")
        print(f"Topic: {topic}")
        try:
            rt.reset_idea()  # Reset for each test
            response = rt.chat(query)
            # Score the response
            has_content = len(response) > 100
            has_kb = "[KB]" in response
            has_metrics = "[Metrics]" in response
            has_backbone = "[Backbone]" in response or "[NL]" in response
            
            score = sum([has_content, has_kb, has_metrics, has_backbone])
            print(f"Score: {score}/4 | Len: {len(response)}")
            print(f"A: {response[:400]}")
        except Exception as e:
            print(f"ERROR: {e}")
