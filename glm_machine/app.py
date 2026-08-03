#!/usr/bin/env python3
"""
GLM Interactive Platform — Flask Backend
==========================================
A web application for interacting with the Geometric Language Machine.
Provides chat, learning, file upload, visualization, and persistence.

Author: Built for Euan R. A. Craig's UBP/GLM project
"""

import os
import sys
import json
import time
import hashlib
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# ── Path Setup ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
STATE_DIR = BASE_DIR / "glm_state"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure state directory exists
STATE_DIR.mkdir(exist_ok=True)

# Add server dir to Python path so GLM modules can import each other
sys.path.insert(0, str(SERVER_DIR))

# Set environment variable for GLM config to find KB files
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)

# ── Flask App ───────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR))
CORS(app)

# ── GLM Runtime (lazy-loaded singleton) ─────────────────────────────────
_glm_runtime = None
_glm_loading = False
_glm_error = None

def get_glm():
    """Lazy-load the GLM runtime on first request."""
    global _glm_runtime, _glm_loading, _glm_error
    if _glm_runtime is not None:
        return _glm_runtime
    if _glm_error is not None:
        raise RuntimeError(_glm_error)
    if _glm_loading:
        raise RuntimeError("GLM is still loading, please wait...")
    
    _glm_loading = True
    try:
        # Patch the config module to use our data directory
        import GLM00_config
        GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
        GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"
        GLM00_config.UBP_CORE_PATH = DATA_DIR
        
        from GLM11_runtime import GLMRuntimeV37
        
        print("[GLM App] Initializing GLM Runtime...")
        _glm_runtime = GLMRuntimeV37(auto_expand=True)
        print("[GLM App] GLM Runtime ready.")
        
        # Inject persisted knowledge
        _inject_persisted_state(_glm_runtime)
        
    except Exception as e:
        _glm_error = f"GLM initialization failed: {e}\n{traceback.format_exc()}"
        print(f"[GLM App] ERROR: {_glm_error}")
        raise
    finally:
        _glm_loading = False
    
    return _glm_runtime


def _inject_persisted_state(rt):
    """Inject any previously persisted learning into the GLM runtime."""
    try:
        from GLM_persistence import GLMPersistence
        persist = GLMPersistence(str(STATE_DIR))
        vocab_count, edge_count = persist.inject_into_glm(rt)
        if vocab_count or edge_count:
            print(f"[GLM App] Injected {vocab_count} vocab + {edge_count} edges from prior sessions")
    except Exception as e:
        print(f"[GLM App] Note: Could not inject persisted state: {e}")


# ── Conversation History Storage ────────────────────────────────────────
HISTORY_FILE = STATE_DIR / "chat_history.json"

def _load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except:
            pass
    return []

def _save_history(history):
    try:
        HISTORY_FILE.write_text(json.dumps(history[-500:], indent=1))  # Keep last 500 messages
    except:
        pass

def _add_to_history(role, content, metadata=None):
    history = _load_history()
    entry = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
    }
    if metadata:
        entry["metadata"] = metadata
    history.append(entry)
    _save_history(history)
    return entry


# ── Static File Routes ──────────────────────────────────────────────────
@app.route('/')
def index():
    return send_file(str(TEMPLATES_DIR / 'index.html'))

@app.route('/colors')
def color_space():
    return send_file(str(TEMPLATES_DIR / 'color_space.html'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)

# ── API: Chat ───────────────────────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Send a message to the GLM and get a response."""
    data = request.json
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e), "loading": True}), 503
    
    try:
        # Record user message
        _add_to_history("user", message)
        
        # Get GLM response
        start_time = time.time()
        response = rt.chat(message)
        elapsed = time.time() - start_time
        
        # Get diagnostics
        diag = rt.last_diag()
        state = rt.idea_state()
        
        # Persist session
        try:
            from GLM_persistence import GLMPersistence
            persist = GLMPersistence(str(STATE_DIR))
            tools = []
            if diag.get("compute"): tools.append("compute")
            if diag.get("symbolic"): tools.append("symbolic")
            persist.save_session(message, response, tools)
        except:
            pass
        
        # Record assistant response
        _add_to_history("assistant", response, {
            "elapsed_ms": int(elapsed * 1000),
            "diag": diag,
            "state": state,
        })
        
        return jsonify({
            "response": response,
            "elapsed_ms": int(elapsed * 1000),
            "diag": diag,
            "state": state,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"GLM error: {e}"}), 500


# ── API: Learn from text ────────────────────────────────────────────────
@app.route('/api/learn', methods=['POST'])
def api_learn():
    """Teach the GLM from text input."""
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400
    
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    
    try:
        # Use the GLM's built-in TextMiner
        from GLM import TextMiner
        miner = TextMiner(rt.vocab_dict, rt.crg)
        stats = miner.ingest(text)
        
        # Persist what was learned
        try:
            from GLM_persistence import GLMPersistence
            persist = GLMPersistence(str(STATE_DIR))
            for word in miner.learned_words:
                entry = rt.vocab_dict.get(word)
                if entry:
                    defn = getattr(entry, 'definition', '')
                    persist.save_vocab(word, defn, list(entry.vector), source="learned")
            for src, label, dst in miner.learned_edges:
                persist.save_edge(src, label, dst, source="learned")
        except:
            pass
        
        return jsonify({
            "stats": stats,
            "learned_words": list(miner.learned_words)[:20],
            "learned_edges": [(s, l, d) for s, l, d in miner.learned_edges[:20]],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Learn error: {e}"}), 500


# ── API: File Upload + Learn ────────────────────────────────────────────
@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Upload a file and have the GLM learn from it."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    
    filename = file.filename
    ext = Path(filename).suffix.lower()
    
    # Read file content
    try:
        if ext in ('.txt', '.md', '.csv', '.json', '.py', '.html', '.xml', '.log'):
            content = file.read().decode('utf-8', errors='replace')
        else:
            return jsonify({"error": f"Unsupported file type: {ext}. Supported: .txt, .md, .csv, .json, .py, .html, .xml, .log"}), 400
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 400
    
    # Learn from the content
    try:
        rt = get_glm()
        from GLM import TextMiner
        miner = TextMiner(rt.vocab_dict, rt.crg)
        stats = miner.ingest(content)
        
        # Persist
        try:
            from GLM_persistence import GLMPersistence
            persist = GLMPersistence(str(STATE_DIR))
            for word in miner.learned_words:
                entry = rt.vocab_dict.get(word)
                if entry:
                    defn = getattr(entry, 'definition', '')
                    persist.save_vocab(word, defn, list(entry.vector), source=f"file:{filename}")
            for src, label, dst in miner.learned_edges:
                persist.save_edge(src, label, dst, source=f"file:{filename}")
        except:
            pass
        
        return jsonify({
            "filename": filename,
            "size_bytes": len(content),
            "stats": stats,
            "learned_words": list(miner.learned_words)[:30],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Processing error: {e}"}), 500


# ── API: System State ──────────────────────────────────────────────────
@app.route('/api/state', methods=['GET'])
def api_state():
    """Get the current GLM state and diagnostics."""
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e), "loading": True}), 503
    
    try:
        state = rt.idea_state()
        diag = rt.last_diag()
        
        # Get persistence stats
        from GLM_persistence import GLMPersistence
        persist = GLMPersistence(str(STATE_DIR))
        persist_stats = persist.get_stats()
        
        return jsonify({
            "state": state,
            "diag": diag,
            "vocab_size": len(rt.vocab_dict),
            "crg_edges": len(rt.crg.edges),
            "persistence": persist_stats,
            "version": "4.0.0",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: CRG Graph Data ────────────────────────────────────────────────
@app.route('/api/graph', methods=['GET'])
def api_graph():
    """Get CRG graph data for visualization."""
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    
    try:
        # Build graph data
        nodes = {}
        links = []
        
        # Collect nodes from edges
        for edge in rt.crg.edges[:500]:  # Limit for performance
            for n in [edge.src, edge.dst]:
                if n not in nodes:
                    entry = rt.vocab_dict.get(n)
                    vector = list(entry.vector) if entry and hasattr(entry, 'vector') else [0]*24
                    nrci = float(entry.nrci) if entry and hasattr(entry, 'nrci') else 0.5
                    mog = getattr(entry, 'mog_category', 'unknown') if entry else 'unknown'
                    nodes[n] = {
                        "id": n,
                        "nrci": nrci,
                        "mog": mog,
                        "vector_sum": sum(vector),
                        "connections": 0,
                    }
            links.append({
                "source": edge.src,
                "target": edge.dst,
                "label": edge.label,
            })
            nodes[edge.src]["connections"] = nodes[edge.src].get("connections", 0) + 1
            nodes[edge.dst]["connections"] = nodes[edge.dst].get("connections", 0) + 1
        
        return jsonify({
            "nodes": list(nodes.values())[:300],
            "links": links[:500],
            "total_nodes": len(nodes),
            "total_links": len(rt.crg.edges),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Idea Zones ────────────────────────────────────────────────────
@app.route('/api/zones', methods=['GET'])
def api_zones():
    """Get idea zone details."""
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    
    try:
        state = rt.idea_state()
        zones_data = []
        
        if hasattr(rt.manager, 'zones'):
            for i, zone in enumerate(rt.manager.zones):
                z = {
                    "index": i,
                    "crystallized": getattr(zone, 'crystallized', False),
                    "thesis": getattr(zone, 'thesis', ''),
                    "coherence": float(zone.coherence()) if hasattr(zone, 'coherence') else 0.0,
                    "topic_nouns": getattr(zone, 'topic_nouns', []),
                    "evidence_count": len(getattr(zone, 'evidence', [])),
                    "contradictions": getattr(zone, 'contradictions', []),
                    "inferred_nouns": getattr(zone, 'inferred_nouns', []),
                }
                zones_data.append(z)
        
        return jsonify({
            "zones": zones_data,
            "active_idx": rt.manager.active_idx if hasattr(rt.manager, 'active_idx') else 0,
            "meta_theses": [
                {"thesis": mt.thesis, "confidence": mt.confidence, "zone_ids": mt.zone_ids}
                for mt in (rt.manager.meta_theses if hasattr(rt.manager, 'meta_theses') else [])
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Vocabulary Search ─────────────────────────────────────────────
@app.route('/api/vocab', methods=['GET'])
def api_vocab():
    """Search or browse the vocabulary."""
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    
    try:
        query = request.args.get('q', '').strip().lower()
        limit = min(int(request.args.get('limit', 50)), 200)
        
        results = []
        for word, entry in rt.vocab_dict.items():
            if query and query not in word.lower():
                continue
            results.append({
                "word": word,
                "nrci": float(entry.nrci) if hasattr(entry, 'nrci') else 0.5,
                "mog": getattr(entry, 'mog_category', 'unknown'),
                "role": getattr(entry, 'role', 'NOUN'),
                "definition": getattr(entry, 'definition', '')[:200] if hasattr(entry, 'definition') else '',
                "vector_sum": sum(entry.vector) if hasattr(entry, 'vector') else 0,
            })
            if len(results) >= limit:
                break
        
        return jsonify({
            "results": results,
            "total_vocab": len(rt.vocab_dict),
            "query": query,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Chat History ──────────────────────────────────────────────────
@app.route('/api/history', methods=['GET'])
def api_history():
    """Get conversation history."""
    limit = min(int(request.args.get('limit', 50)), 500)
    history = _load_history()
    return jsonify({"history": history[-limit:], "total": len(history)})


@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """Clear conversation history."""
    _save_history([])
    return jsonify({"status": "cleared"})


# ── API: Growth / Persistence Stats ────────────────────────────────────
@app.route('/api/growth', methods=['GET'])
def api_growth():
    """Get growth and persistence statistics."""
    try:
        from GLM_persistence import GLMPersistence
        persist = GLMPersistence(str(STATE_DIR))
        return jsonify({
            "stats": persist.get_stats(),
            "recent_growth": persist.growth_log[-20:] if persist.growth_log else [],
            "recent_insights": persist.insights[-10:] if persist.insights else [],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Teach (direct knowledge injection) ────────────────────────────
@app.route('/api/teach', methods=['POST'])
def api_teach():
    """Teach the GLM a specific fact (word + definition + relationships)."""
    data = request.json
    word = data.get('word', '').strip().lower()
    definition = data.get('definition', '').strip()
    relations = data.get('relations', [])  # List of {label, target}
    
    if not word:
        return jsonify({"error": "No word provided"}), 400
    
    try:
        rt = get_glm()
        
        # Create or update vocab entry
        if word not in rt.vocab_dict:
            from GLM import TextMiner
            miner = TextMiner(rt.vocab_dict, rt.crg)
            miner._create_word(word)
        
        if definition and hasattr(rt.vocab_dict.get(word), '__dict__'):
            rt.vocab_dict[word].definition = definition
        
        # Add relations
        edges_added = []
        for rel in relations:
            label = rel.get('label', 'relates_to')
            target = rel.get('target', '').strip().lower()
            if target:
                if target not in rt.vocab_dict:
                    from GLM import TextMiner
                    miner = TextMiner(rt.vocab_dict, rt.crg)
                    miner._create_word(target)
                rt.crg.add_edge(word, label, target)
                edges_added.append((word, label, target))
        
        # Persist
        try:
            from GLM_persistence import GLMPersistence
            persist = GLMPersistence(str(STATE_DIR))
            entry = rt.vocab_dict.get(word)
            if entry:
                persist.save_vocab(word, definition, list(entry.vector), source="taught")
            for s, l, d in edges_added:
                persist.save_edge(s, l, d, source="taught")
        except:
            pass
        
        return jsonify({
            "word": word,
            "definition": definition,
            "edges_added": edges_added,
            "status": "taught",
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Reset Idea State ──────────────────────────────────────────────
@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset the current idea state (but keep learned knowledge)."""
    try:
        rt = get_glm()
        rt.reset_idea()
        return jsonify({"status": "reset"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Health Check ──────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "glm_loaded": _glm_runtime is not None,
        "glm_loading": _glm_loading,
        "glm_error": _glm_error,
    })


# ── API: Run Quick Test ────────────────────────────────────────────────
@app.route('/api/test', methods=['POST'])
def api_test():
    """Run a quick test of GLM capabilities."""
    try:
        rt = get_glm()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    
    tests = [
        {"name": "Computation", "query": "What is gcd(54, 24)?", "expect": "6"},
        {"name": "Sequence", "query": "What comes next: 2, 4, 8, 16, ...?", "expect": "32"},
        {"name": "Definition", "query": "What does ubiquitous mean?", "expect": "everywhere"},
        {"name": "Antonym", "query": "What is the opposite of hot?", "expect": "cold"},
        {"name": "UBP Knowledge", "query": "What is NRCI?", "expect": "coherence"},
        {"name": "Personal Memory", "query": "My name is TestUser. What is my name?", "expect": "testuser"},
    ]
    
    results = []
    for t in tests:
        try:
            rt.reset_idea()
            start = time.time()
            response = rt.chat(t["query"])
            elapsed = int((time.time() - start) * 1000)
            passed = t["expect"].lower() in response.lower()
            results.append({
                "name": t["name"],
                "query": t["query"],
                "passed": passed,
                "elapsed_ms": elapsed,
                "response": response[:300],
            })
        except Exception as e:
            results.append({
                "name": t["name"],
                "query": t["query"],
                "passed": False,
                "error": str(e),
            })
    
    passed = sum(1 for r in results if r.get("passed"))
    return jsonify({
        "results": results,
        "passed": passed,
        "total": len(results),
        "score": f"{passed}/{len(results)}",
    })


# ── Main ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='GLM Interactive Platform')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()
    
    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║  GLM Interactive Platform v4.0.0                            ║")
    print(f"║  Geometric Language Machine — Web Interface                 ║")
    print(f"║  Based on UBP Core Studio by Euan R. A. Craig              ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"")
    print(f"  Starting on http://{args.host}:{args.port}")
    print(f"  GLM will initialize on first request...")
    print(f"")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
