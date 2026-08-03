#!/usr/bin/env python3
"""
GLM KB Ingestion Engine
========================
Ingests the UBP system KB into the GLM's vocabulary and CRG.
This dramatically expands the GLM's knowledge base and coherence.
"""

import json
import sys
import os
import hashlib
import re
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(SERVER_DIR))
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)

def load_kb():
    """Load and index the system KB."""
    kb = json.loads((DATA_DIR / "ubp_system_kb.json").read_text())
    fields = kb['_fields']
    entries = kb['entries']
    indexed = {}
    for h, entry_list in entries.items():
        if isinstance(entry_list, list) and len(entry_list) >= 1:
            uid = entry_list[0]
            indexed[uid] = dict(zip(fields, entry_list))
    return indexed

def extract_definition(lexicon_str):
    """Extract clean definition from lexicon string."""
    if not lexicon_str:
        return ""
    # Remove brackets and clean up
    s = lexicon_str.strip()
    s = re.sub(r'^\[+', '', s)
    s = re.sub(r'\]+$', '', s)
    s = s.strip()
    # Take first sentence or first 200 chars
    m = re.match(r'([^.]{20,}\.)', s)
    if m:
        return m.group(1).strip()
    return s[:200].strip()

def extract_name(lexicon_str):
    """Extract the name/title from lexicon string."""
    if not lexicon_str:
        return ""
    # Look for [Name] pattern
    m = re.match(r'\[?(?:Law|Element|Molecule|Particle|Math|Reaction|Tool|Algo|Crystal)?:?\s*(.+?)\]?', lexicon_str)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'^\[', '', name)
        name = re.sub(r'\]$', '', name)
        return name.strip()
    return lexicon_str[:50].strip()

def ingest_kb_to_glm():
    """Ingest the full KB into the GLM runtime."""
    print("=" * 60)
    print("GLM KB Ingestion Engine")
    print("=" * 60)
    
    # Load KB
    print("\n[1] Loading system KB...")
    indexed = load_kb()
    print(f"    Total entries: {len(indexed)}")
    
    # Initialize GLM
    print("\n[2] Initializing GLM Runtime...")
    from GLM00_config import KB_SYSTEM_PATH, KB_LANG_PATH
    GLM00_config = __import__('GLM00_config')
    GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
    GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"
    
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37(auto_expand=True)
    print(f"    Initial vocab: {len(rt.vocab_dict)}")
    print(f"    Initial CRG edges: {len(rt.crg.edges)}")
    
    # Ingest KB entries
    print("\n[3] Ingesting KB entries into vocabulary...")
    from GLM01_substrate import WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
    
    ingested = 0
    definitions_added = 0
    edges_added = 0
    
    for uid, entry in indexed.items():
        lexicon = str(entry.get('lexicon', ''))
        name = extract_name(lexicon)
        definition = extract_definition(lexicon)
        vector = entry.get('vector', [0]*24)
        nrci_str = str(entry.get('nrci_str', '0.5'))
        tags = str(entry.get('tags', ''))
        
        # Parse NRCI
        try:
            nrci = float(nrci_str)
        except:
            nrci = 0.5
        
        # Ensure vector is 24-bit
        if isinstance(vector, list) and len(vector) == 24:
            vec = [int(b) for b in vector]
        else:
            # Generate from hash
            h = hashlib.sha256(uid.lower().encode()).digest()
            vec = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
        
        # Create vocab word from the name
        word_key = name.lower().strip()
        if not word_key or len(word_key) < 2:
            continue
            
        # Clean the word key
        word_key = re.sub(r'[^\w\s-]', '', word_key).strip()
        if not word_key:
            continue
        
        # Add to vocabulary if not present
        if word_key not in rt.vocab_dict:
            try:
                snapped, _ = GOLAY_ENGINE.snap_to_codeword(vec)
            except:
                snapped = vec
            nrci_val = float(LEECH_ENGINE.calculate_nrci(snapped))
            
            entry_obj = WordEntry(
                word=word_key,
                vector=snapped,
                role="NOUN",
                ubp_id=uid,
                nrci=nrci_val,
                golay_codeword=snapped,
                fold3=BLA.fold24_to3(snapped),
                mog_category=_get_mog_category(snapped)
            )
            entry_obj.definition = definition
            rt.vocab_dict[word_key] = entry_obj
            ingested += 1
        else:
            # Update definition if missing
            if not getattr(rt.vocab_dict[word_key], 'definition', None):
                rt.vocab_dict[word_key].definition = definition
                definitions_added += 1
        
        # Create edges from tags
        if tags:
            tag_list = [t.strip().lower() for t in re.split(r'[,;|]', tags) if t.strip()]
            for tag in tag_list[:3]:
                tag_clean = re.sub(r'[^\w\s-]', '', tag).strip()
                if tag_clean and tag_clean != word_key and len(tag_clean) >= 2:
                    if tag_clean not in rt.vocab_dict:
                        # Create tag word
                        h = hashlib.sha256(tag_clean.encode()).digest()
                        tvec = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
                        try:
                            tsnap, _ = GOLAY_ENGINE.snap_to_codeword(tvec)
                        except:
                            tsnap = tvec
                        tnrci = float(LEECH_ENGINE.calculate_nrci(tsnap))
                        rt.vocab_dict[tag_clean] = WordEntry(
                            word=tag_clean,
                            vector=tsnap,
                            role="NOUN",
                            ubp_id=f"TAG_{tag_clean.upper()}",
                            nrci=tnrci,
                            golay_codeword=tsnap,
                            fold3=BLA.fold24_to3(tsnap),
                            mog_category=_get_mog_category(tsnap)
                        )
                    # Add edge
                    rt.crg.add_edge(word_key, "is_a", tag_clean)
                    edges_added += 1
        
        # Create cross-references from the uid pattern
        # e.g., LAW_BIO_001 -> connects to "biology", "bio"
        uid_parts = uid.split('_')
        if len(uid_parts) >= 2:
            category = uid_parts[1].lower()
            if category and category != word_key and len(category) >= 2:
                if category not in rt.vocab_dict:
                    h = hashlib.sha256(category.encode()).digest()
                    cvec = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
                    try:
                        csnap, _ = GOLAY_ENGINE.snap_to_codeword(cvec)
                    except:
                        csnap = cvec
                    cnrci = float(LEECH_ENGINE.calculate_nrci(csnap))
                    rt.vocab_dict[category] = WordEntry(
                        word=category,
                        vector=csnap,
                        role="NOUN",
                        ubp_id=f"CAT_{category.upper()}",
                        nrci=cnrci,
                        golay_codeword=csnap,
                        fold3=BLA.fold24_to3(csnap),
                        mog_category=_get_mog_category(csnap)
                    )
    
    # Add curated UBP-specific CRG edges
    print("\n[4] Adding UBP-specific CRG edges...")
    ubp_edges = [
        # Core substrate relationships
        ("substrate", "is_a", "computational framework"),
        ("substrate", "contains", "golay code"),
        ("substrate", "contains", "leech lattice"),
        ("golay code", "is_a", "error correction"),
        ("leech lattice", "is_a", "geometric structure"),
        ("leech lattice", "depends_on", "golay code"),
        ("nrci", "measures", "coherence"),
        ("nrci", "depends_on", "substrate"),
        ("coherence", "depends_on", "nrci"),
        ("observer", "is_a", "constant"),
        ("observer", "measures", "coherence"),
        ("wobble", "is_a", "entropy"),
        ("wobble", "depends_on", "substrate"),
        ("triadic", "is_a", "structure"),
        ("triadic", "contains", "monad"),
        ("monad", "is_a", "mathematical constant"),
        ("monad", "contains", "pi"),
        ("monad", "contains", "phi"),
        ("monad", "contains", "e"),
        ("coherence snap", "is_a", "process"),
        ("coherence snap", "resets", "drift"),
        ("ontological health", "depends_on", "coherence"),
        ("ontological health", "measures", "system integrity"),
        ("symmetry tax", "measures", "geometric cost"),
        ("symmetry tax", "depends_on", "leech lattice"),
        ("barnes-wall", "is_a", "lattice"),
        ("barnes-wall", "extends", "leech lattice"),
        ("error correction", "preserves", "information"),
        ("error correction", "depends_on", "golay code"),
        # Physics relationships
        ("gravity", "is_a", "force"),
        ("gravity", "depends_on", "mass"),
        ("gravity", "curves", "spacetime"),
        ("mass", "is_a", "property"),
        ("mass", "depends_on", "substrate"),
        ("energy", "is_a", "conserved quantity"),
        ("energy", "conserved_with", "momentum"),
        ("momentum", "is_a", "conserved quantity"),
        ("momentum", "generates", "motion"),
        ("time", "is_a", "dimension"),
        ("time", "emerges_from", "substrate"),
        ("space", "is_a", "dimension"),
        ("spacetime", "contains", "time"),
        ("spacetime", "contains", "space"),
        ("entropy", "measures", "disorder"),
        ("entropy", "increases_with", "time"),
        ("temperature", "measures", "energy"),
        ("temperature", "depends_on", "entropy"),
        # Particle relationships
        ("boson", "is_a", "particle"),
        ("fermion", "is_a", "particle"),
        ("boson", "contradicts", "fermion"),
        ("photon", "is_a", "boson"),
        ("photon", "carries", "electromagnetic force"),
        ("quark", "is_a", "fermion"),
        ("quark", "forms", "proton"),
        ("quark", "forms", "neutron"),
        ("proton", "is_a", "baryon"),
        ("neutron", "is_a", "baryon"),
        ("electron", "is_a", "lepton"),
        ("gluon", "is_a", "boson"),
        ("gluon", "carries", "strong force"),
        # Mathematical relationships
        ("pi", "is_a", "transcendental"),
        ("phi", "is_a", "irrational"),
        ("e", "is_a", "transcendental"),
        ("symmetry", "is_a", "property"),
        ("symmetry", "preserves", "structure"),
        ("hamiltonian", "is_a", "operator"),
        ("hamiltonian", "generates", "time"),
        ("lagrangian", "is_a", "functional"),
        ("entropy", "measures", "information"),
        # Biological
        ("biology", "depends_on", "substrate"),
        ("genetic code", "is_a", "codec"),
        ("genetic code", "encodes", "information"),
        ("life", "depends_on", "coherence"),
        # Chemical
        ("hydrogen", "is_a", "element"),
        ("oxygen", "is_a", "element"),
        ("water", "contains", "hydrogen"),
        ("water", "contains", "oxygen"),
        ("atom", "contains", "proton"),
        ("atom", "contains", "neutron"),
        ("atom", "contains", "electron"),
        ("molecule", "contains", "atom"),
    ]
    
    for src, label, dst in ubp_edges:
        if src not in rt.vocab_dict:
            from GLM import TextMiner
            miner = TextMiner(rt.vocab_dict, rt.crg)
            miner._create_word(src)
        if dst not in rt.vocab_dict:
            from GLM import TextMiner
            miner = TextMiner(rt.vocab_dict, rt.crg)
            miner._create_word(dst)
        rt.crg.add_edge(src, label, dst)
        edges_added += 1
    
    # Add LAW-to-LAW connections based on shared concepts
    print("\n[5] Building LAW cross-references...")
    law_concepts = {}
    for uid, entry in indexed.items():
        if not uid.startswith('LAW'): continue
        lexicon = str(entry.get('lexicon', '')).lower()
        # Extract key concepts from the law
        concepts = set()
        for word in re.findall(r'\b[a-z]{4,}\b', lexicon):
            if word not in {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'has', 'have', 'been', 'which', 'their', 'into', 'such', 'than', 'when', 'where', 'what', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'any', 'no', 'not', 'only', 'own', 'same', 'so', 'very', 'just', 'because', 'but', 'and', 'or', 'if', 'while', 'about', 'above', 'after', 'before', 'between', 'during', 'through', 'until', 'again', 'further', 'then', 'once', 'here', 'there', 'why', 'also', 'still', 'however', 'thus', 'hence', 'therefore', 'moreover', 'furthermore', 'nevertheless', 'nonetheless', 'although', 'though', 'even', 'whether', 'while', 'whereas', 'unless', 'since', 'because', 'provided', 'except', 'besides', 'instead', 'regardless', 'despite', 'although', 'whereas', 'while', 'unless', 'until', 'since', 'once', 'though', 'although', 'even', 'whereas', 'while', 'unless', 'until', 'since', 'once', 'though', 'although', 'even'}:
                concepts.add(word)
        law_concepts[uid] = concepts
    
    # Connect laws that share 3+ concepts
    law_uids = list(law_concepts.keys())
    cross_refs = 0
    for i, uid1 in enumerate(law_uids):
        if cross_refs >= 200: break
        for uid2 in law_uids[i+1:]:
            if cross_refs >= 200: break
            shared = law_concepts[uid1] & law_concepts[uid2]
            if len(shared) >= 3:
                name1 = extract_name(str(indexed[uid1].get('lexicon', ''))).lower()
                name2 = extract_name(str(indexed[uid2].get('lexicon', ''))).lower()
                if name1 and name2 and name1 != name2:
                    rt.crg.add_edge(name1, "relates_to", name2)
                    cross_refs += 1
    
    edges_added += cross_refs
    
    # Persist everything
    print("\n[6] Persisting learned knowledge...")
    from GLM_persistence import GLMPersistence
    persist = GLMPersistence(str(BASE_DIR / "glm_state"))
    
    for word, entry in rt.vocab_dict.items():
        defn = getattr(entry, 'definition', '')
        if defn:
            persist.save_vocab(word, defn, list(entry.vector), source="kb_ingest")
    
    for edge in rt.crg.edges:
        persist.save_edge(edge.src, edge.label, edge.dst, source="kb_ingest")
    
    # Final stats
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Vocabulary: {len(rt.vocab_dict)} words")
    print(f"  CRG Edges: {len(rt.crg.edges)}")
    print(f"  New vocab: {ingested}")
    print(f"  New definitions: {definitions_added}")
    print(f"  New edges: {edges_added}")
    print(f"  Cross-references: {cross_refs}")
    print("=" * 60)
    
    return rt

if __name__ == "__main__":
    rt = ingest_kb_to_glm()
    
    # Test with UBP-specific queries
    print("\n" + "=" * 60)
    print("POST-INGESTION TESTS")
    print("=" * 60)
    
    test_queries = [
        "What is the Universal Binary Principle?",
        "Tell me about the Golay code.",
        "What is NRCI?",
        "How does error correction work in the substrate?",
        "What is the Observer Constant?",
        "Explain coherence in the UBP framework.",
        "What is the relationship between gravity and mass?",
        "How do bosons and fermions differ?",
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        try:
            response = rt.chat(query)
            print(f"A: {response[:300]}")
        except Exception as e:
            print(f"ERROR: {e}")
