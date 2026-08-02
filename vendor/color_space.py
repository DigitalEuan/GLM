#!/usr/bin/env python3
"""
GLM Color Space Projection
============================
Projects the entire GLM knowledge substrate into hex color space.
Every 24-bit concept vector IS an RGB color (#RRGGBB).
This reveals the geometric structure of knowledge as visual patterns.

Outputs:
- Color map of all concepts
- MOG category color clusters
- NRCI-brightness mapping
- Idea zone color signatures
- CRG edge color gradients
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(SERVER_DIR))
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)


def vector_to_rgb(vec):
    """Convert 24-bit vector to RGB tuple."""
    if not vec or len(vec) != 24:
        return (0, 0, 0)
    r = sum(vec[i] << (7 - i) for i in range(8))
    g = sum(vec[8 + i] << (7 - i) for i in range(8))
    b = sum(vec[16 + i] << (7 - i) for i in range(8))
    return (r, g, b)


def vector_to_hex(vec):
    """Convert 24-bit vector to hex color string."""
    r, g, b = vector_to_rgb(vec)
    return f"#{r:02x}{g:02x}{b:02x}"


def nrci_to_brightness(nrci):
    """Map NRCI (0-1) to brightness multiplier."""
    return 0.3 + 0.7 * nrci  # Range: 0.3 to 1.0


def adjust_brightness(rgb, factor):
    """Adjust brightness of an RGB color."""
    return tuple(min(255, int(c * factor)) for c in rgb)


def main():
    # Load GLM
    from GLM00_config import KB_SYSTEM_PATH, KB_LANG_PATH
    GLM00_config = __import__('GLM00_config')
    GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
    GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"

    from GLM11_runtime import GLMRuntimeV37
    print("[1] Loading GLM...")
    rt = GLMRuntimeV37(auto_expand=False)
    print(f"    Vocab: {len(rt.vocab_dict)}, Edges: {len(rt.crg.edges)}")

    # ── Project all concepts into color space ──────────────────────────
    print("\n[2] Projecting concepts into color space...")
    concepts = []
    mog_colors = defaultdict(list)

    for word, entry in rt.vocab_dict.items():
        if not hasattr(entry, 'vector') or not entry.vector:
            continue
        vec = list(entry.vector)
        hex_color = vector_to_hex(vec)
        rgb = vector_to_rgb(vec)
        nrci = float(entry.nrci) if hasattr(entry, 'nrci') else 0.5
        mog = getattr(entry, 'mog_category', 'unknown')
        defn = getattr(entry, 'definition', '')[:100]

        # NRCI-adjusted color (brighter = higher coherence)
        brightness = nrci_to_brightness(nrci)
        adj_rgb = adjust_brightness(rgb, brightness)
        adj_hex = f"#{adj_rgb[0]:02x}{adj_rgb[1]:02x}{adj_rgb[2]:02x}"

        concepts.append({
            "word": word,
            "hex": hex_color,
            "rgb": list(rgb),
            "adj_hex": adj_hex,
            "adj_rgb": list(adj_rgb),
            "nrci": round(nrci, 4),
            "mog": mog,
            "definition": defn,
            "hamming_weight": sum(vec),
            "quadrants": [sum(vec[i:i+6]) for i in range(0, 24, 6)],
        })
        mog_colors[mog].append({
            "word": word,
            "hex": hex_color,
            "nrci": nrci,
        })

    print(f"    Projected {len(concepts)} concepts")

    # ── MOG Category Analysis ──────────────────────────────────────────
    print("\n[3] MOG Category Color Analysis:")
    mog_summary = {}
    for mog, items in sorted(mog_colors.items()):
        if not items:
            continue
        # Average color for this MOG category
        avg_r = sum(int(item['hex'][1:3], 16) for item in items) / len(items)
        avg_g = sum(int(item['hex'][3:5], 16) for item in items) / len(items)
        avg_b = sum(int(item['hex'][5:7], 16) for item in items) / len(items)
        avg_hex = f"#{int(avg_r):02x}{int(avg_g):02x}{int(avg_b):02x}"
        avg_nrci = sum(item['nrci'] for item in items) / len(items)

        mog_summary[mog] = {
            "count": len(items),
            "avg_color": avg_hex,
            "avg_nrci": round(avg_nrci, 4),
            "sample_words": [item['word'] for item in items[:5]],
        }
        print(f"    {mog:20s} → {avg_hex} (avg NRCI: {avg_nrci:.3f}, {len(items)} concepts)")

    # ── CRG Edge Color Gradients ───────────────────────────────────────
    print("\n[4] CRG Edge Color Gradients:")
    edge_gradients = []
    for edge in rt.crg.edges[:200]:
        src_entry = rt.vocab_dict.get(edge.src)
        dst_entry = rt.vocab_dict.get(edge.dst)
        if src_entry and dst_entry and hasattr(src_entry, 'vector') and hasattr(dst_entry, 'vector'):
            src_hex = vector_to_hex(list(src_entry.vector))
            dst_hex = vector_to_hex(list(dst_entry.vector))
            edge_gradients.append({
                "src": edge.src,
                "dst": edge.dst,
                "label": edge.label,
                "src_color": src_hex,
                "dst_color": dst_hex,
            })

    print(f"    {len(edge_gradients)} edges with color gradients")

    # ── Color Clusters (concepts with similar colors) ──────────────────
    print("\n[5] Color Clusters (similar concepts):")
    # Group by hex prefix (first 4 bits of each channel = 64 color bins)
    color_bins = defaultdict(list)
    for c in concepts:
        r, g, b = c['rgb']
        # Reduce to 4 bits per channel (16 levels)
        bin_key = f"{r>>4:01x}{g>>4:01x}{b>>4:01x}"
        color_bins[bin_key].append(c['word'])

    # Show largest clusters
    sorted_bins = sorted(color_bins.items(), key=lambda x: -len(x[1]))
    for bin_key, words in sorted_bins[:10]:
        print(f"    Color bin #{bin_key}: {len(words)} concepts — {', '.join(words[:5])}")

    # ── Idea Zone Colors ───────────────────────────────────────────────
    print("\n[6] Idea Zone Color Signatures:")
    if hasattr(rt.manager, 'zones'):
        for i, zone in enumerate(rt.manager.zones):
            if hasattr(zone, 'topic_nouns') and zone.topic_nouns:
                colors = []
                for noun in zone.topic_nouns:
                    entry = rt.vocab_dict.get(noun)
                    if entry and hasattr(entry, 'vector'):
                        colors.append(vector_to_hex(list(entry.vector)))
                if colors:
                    print(f"    Zone {i}: {', '.join(zone.topic_nouns[:3])} → {', '.join(colors)}")

    # ── Generate HTML Visualization ────────────────────────────────────
    print("\n[7] Generating color space visualization...")
    generate_html(concepts, mog_summary, edge_gradients)

    # ── Save data ──────────────────────────────────────────────────────
    output = {
        "total_concepts": len(concepts),
        "concepts": concepts[:500],  # Limit for file size
        "mog_summary": mog_summary,
        "edge_gradients": edge_gradients[:200],
        "color_clusters": {k: v[:10] for k, v in sorted_bins[:20]},
    }
    output_file = BASE_DIR / "color_space_data.json"
    output_file.write_text(json.dumps(output, indent=1))
    print(f"    Data saved to {output_file}")

    print("\n" + "=" * 60)
    print("COLOR SPACE PROJECTION COMPLETE")
    print("=" * 60)
    print(f"  Concepts projected: {len(concepts)}")
    print(f"  MOG categories: {len(mog_summary)}")
    print(f"  Edge gradients: {len(edge_gradients)}")
    print(f"  HTML visualization: color_space.html")
    print("=" * 60)


def generate_html(concepts, mog_summary, edge_gradients):
    """Generate an interactive HTML visualization of the color space."""

    # Sort concepts by MOG category then NRCI
    concepts_sorted = sorted(concepts, key=lambda c: (c['mog'], -c['nrci']))

    # Build concept data for JS
    concepts_json = json.dumps(concepts_sorted[:500])
    mog_json = json.dumps(mog_summary)
    edges_json = json.dumps(edge_gradients[:100])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GLM Color Space — Knowledge Substrate Visualization</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0f; color: #e0e0e8; font-family: 'Inter', -apple-system, sans-serif; }}
.header {{
    padding: 20px 30px;
    background: linear-gradient(135deg, #12121a, #1a1a28);
    border-bottom: 1px solid #2a2a3a;
}}
.header h1 {{
    font-size: 24px;
    background: linear-gradient(135deg, #6366f1, #22d3ee);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.header p {{ color: #8888a0; font-size: 13px; margin-top: 4px; }}
.controls {{
    padding: 15px 30px;
    background: #12121a;
    border-bottom: 1px solid #2a2a3a;
    display: flex; gap: 15px; align-items: center; flex-wrap: wrap;
}}
.controls label {{ font-size: 12px; color: #8888a0; }}
.controls select, .controls input {{
    background: #0a0a0f; border: 1px solid #2a2a3a; border-radius: 6px;
    padding: 6px 10px; color: #e0e0e8; font-size: 12px;
}}
.controls button {{
    background: #6366f1; color: white; border: none; padding: 6px 14px;
    border-radius: 6px; font-size: 12px; cursor: pointer;
}}
.controls button:hover {{ background: #818cf8; }}
.main {{ display: flex; height: calc(100vh - 130px); }}
.canvas-area {{ flex: 1; position: relative; overflow: hidden; }}
canvas {{ width: 100%; height: 100%; }}
.sidebar {{
    width: 320px; background: #12121a; border-left: 1px solid #2a2a3a;
    overflow-y: auto; padding: 15px;
}}
.sidebar h3 {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px;
    color: #8888a0; margin-bottom: 10px; padding-bottom: 4px;
    border-bottom: 1px solid #2a2a3a;
}}
.color-card {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px; border-radius: 6px; margin-bottom: 4px;
    cursor: pointer; transition: background 0.2s;
}}
.color-card:hover {{ background: #1a1a28; }}
.color-swatch {{
    width: 32px; height: 32px; border-radius: 6px;
    border: 1px solid #2a2a3a; flex-shrink: 0;
}}
.color-info {{ flex: 1; min-width: 0; }}
.color-info .word {{ font-size: 13px; font-weight: 600; }}
.color-info .meta {{ font-size: 10px; color: #8888a0; }}
.mog-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;
    margin-bottom: 15px;
}}
.mog-card {{
    background: #1a1a28; border-radius: 6px; padding: 8px; text-align: center;
}}
.mog-card .swatch {{
    width: 100%; height: 24px; border-radius: 4px; margin-bottom: 4px;
}}
.mog-card .label {{ font-size: 9px; color: #8888a0; }}
.mog-card .count {{ font-size: 14px; font-weight: 700; }}
.stats-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;
}}
.stat {{ background: #1a1a28; border-radius: 6px; padding: 10px; text-align: center; }}
.stat .value {{ font-size: 20px; font-weight: 700; color: #818cf8; }}
.stat .label {{ font-size: 10px; color: #8888a0; }}
.tooltip {{
    position: absolute; background: #1a1a28; border: 1px solid #2a2a3a;
    border-radius: 8px; padding: 10px; pointer-events: none;
    font-size: 12px; max-width: 250px; z-index: 10;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    display: none;
}}
.legend {{
    display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px;
}}
.legend-item {{
    display: flex; align-items: center; gap: 5px; font-size: 11px;
}}
.legend-swatch {{
    width: 12px; height: 12px; border-radius: 3px;
}}
</style>
</head>
<body>
<div class="header">
    <h1>◆ GLM Color Space</h1>
    <p>Every concept in the Geometric Language Machine is a 24-bit vector — which IS an RGB color. This is the knowledge substrate rendered as light.</p>
</div>
<div class="controls">
    <label>View:</label>
    <select id="viewMode" onchange="render()">
        <option value="scatter">Scatter Plot</option>
        <option value="grid">Color Grid</option>
        <option value="spectrum">Spectrum Strip</option>
        <option value="clusters">MOG Clusters</option>
    </select>
    <label>Color:</label>
    <select id="colorMode" onchange="render()">
        <option value="raw">Raw Vector Color</option>
        <option value="nrci">NRCI Brightness</option>
        <option value="mog">MOG Category</option>
    </select>
    <label>Filter:</label>
    <select id="mogFilter" onchange="render()">
        <option value="all">All Categories</option>
    </select>
    <label>Min NRCI:</label>
    <input type="range" id="nrciFilter" min="0" max="1" step="0.05" value="0" onchange="render()">
    <span id="nrciValue" style="font-size:11px;color:#8888a0">0.0</span>
    <button onclick="resetView()">Reset</button>
</div>
<div class="main">
    <div class="canvas-area">
        <canvas id="canvas"></canvas>
        <div class="tooltip" id="tooltip"></div>
    </div>
    <div class="sidebar">
        <div class="stats-grid">
            <div class="stat"><div class="value" id="totalConcepts">0</div><div class="label">Concepts</div></div>
            <div class="stat"><div class="value" id="totalColors">0</div><div class="label">Unique Colors</div></div>
            <div class="stat"><div class="value" id="avgNrci">0</div><div class="label">Avg NRCI</div></div>
            <div class="stat"><div class="value" id="totalEdges">0</div><div class="label">CRG Edges</div></div>
        </div>

        <h3>MOG Category Colors</h3>
        <div class="mog-grid" id="mogGrid"></div>

        <h3>Color Legend</h3>
        <div class="legend" id="legend"></div>

        <h3>Concepts</h3>
        <input type="text" id="searchBox" placeholder="Search concepts..."
               style="width:100%;background:#0a0a0f;border:1px solid #2a2a3a;border-radius:6px;padding:6px 10px;color:#e0e0e8;font-size:12px;margin-bottom:10px"
               oninput="filterConcepts()">
        <div id="conceptList"></div>
    </div>
</div>

<script>
const concepts = {concepts_json};
const mogSummary = {mog_json};
const edges = {edges_json};

const mogColors = {{
    'M_': '#6366f1', 'I_': '#22d3ee', 'A_': '#fb923c', 'P_': '#f472b6',
}};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
let hoveredConcept = null;
let conceptPositions = [];

// ── Initialize ────────────────────────────────────────────
function init() {{
    // Populate MOG filter
    const filter = document.getElementById('mogFilter');
    const mogs = [...new Set(concepts.map(c => c.mog))].sort();
    mogs.forEach(mog => {{
        const opt = document.createElement('option');
        opt.value = mog; opt.textContent = mog;
        filter.appendChild(opt);
    }});

    // Stats
    document.getElementById('totalConcepts').textContent = concepts.length;
    const uniqueColors = new Set(concepts.map(c => c.hex)).size;
    document.getElementById('totalColors').textContent = uniqueColors;
    const avgNrci = concepts.reduce((s, c) => s + c.nrci, 0) / concepts.length;
    document.getElementById('avgNrci').textContent = avgNrci.toFixed(3);
    document.getElementById('totalEdges').textContent = edges.length;

    // MOG grid
    const mogGrid = document.getElementById('mogGrid');
    Object.entries(mogSummary).forEach(([mog, info]) => {{
        const card = document.createElement('div');
        card.className = 'mog-card';
        card.innerHTML = `<div class="swatch" style="background:${{info.avg_color}}"></div>
            <div class="count">${{info.count}}</div>
            <div class="label">${{mog}}</div>`;
        mogGrid.appendChild(card);
    }});

    // Legend
    const legend = document.getElementById('legend');
    Object.entries(mogColors).forEach(([prefix, color]) => {{
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `<div class="legend-swatch" style="background:${{color}}"></div>${{prefix}}`;
        legend.appendChild(item);
    }});

    // NRCI slider
    document.getElementById('nrciFilter').addEventListener('input', e => {{
        document.getElementById('nrciValue').textContent = parseFloat(e.target.value).toFixed(2);
    }});

    render();
    renderConceptList();
}}

// ── Render ────────────────────────────────────────────────
function render() {{
    const mode = document.getElementById('viewMode').value;
    const colorMode = document.getElementById('colorMode').value;
    const mogFilter = document.getElementById('mogFilter').value;
    const minNrci = parseFloat(document.getElementById('nrciFilter').value);

    const filtered = concepts.filter(c => {{
        if (mogFilter !== 'all' && c.mog !== mogFilter) return false;
        if (c.nrci < minNrci) return false;
        return true;
    }});

    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;

    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    conceptPositions = [];

    if (mode === 'scatter') renderScatter(filtered, colorMode);
    else if (mode === 'grid') renderGrid(filtered, colorMode);
    else if (mode === 'spectrum') renderSpectrum(filtered, colorMode);
    else if (mode === 'clusters') renderClusters(filtered, colorMode);
}}

function getColor(concept, mode) {{
    if (mode === 'raw') return concept.hex;
    if (mode === 'nrci') return concept.adj_hex;
    if (mode === 'mog') {{
        for (const [prefix, color] of Object.entries(mogColors)) {{
            if (concept.mog.startsWith(prefix)) return color;
        }}
        return '#555';
    }}
    return concept.hex;
}}

function renderScatter(items, colorMode) {{
    const W = canvas.width, H = canvas.height;
    const padding = 40;

    // Map quadrants to x, y position
    // X = Reality - Potential, Y = Information - Activation
    items.forEach(c => {{
        const q = c.quadrants;
        const x = padding + ((q[0] - q[3] + 6) / 12) * (W - 2 * padding);
        const y = padding + ((q[1] - q[2] + 6) / 12) * (H - 2 * padding);
        const color = getColor(c, colorMode);
        const r = 3 + c.nrci * 5;

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.5 + c.nrci * 0.5;
        ctx.fill();
        ctx.globalAlpha = 1;

        conceptPositions.push({{ x, y, r, concept: c }});

        // Label high-NRCI concepts
        if (c.nrci > 0.7 && r > 5) {{
            ctx.fillStyle = '#8888a0';
            ctx.font = '9px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(c.word, x, y - r - 4);
        }}
    }});

    // Axes
    ctx.strokeStyle = '#2a2a3a';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(W / 2, padding); ctx.lineTo(W / 2, H - padding);
    ctx.moveTo(padding, H / 2); ctx.lineTo(W - padding, H / 2);
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#8888a0';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Reality →', W - padding, H / 2 + 15);
    ctx.fillText('← Potential', padding, H / 2 + 15);
    ctx.fillText('Information ↑', W / 2, padding - 10);
    ctx.fillText('↓ Activation', W / 2, H - padding + 15);
}}

function renderGrid(items, colorMode) {{
    const W = canvas.width, H = canvas.height;
    const cols = Math.ceil(Math.sqrt(items.length));
    const cellSize = Math.min((W - 40) / cols, (H - 40) / cols, 20);

    items.forEach((c, i) => {{
        const col = i % cols;
        const row = Math.floor(i / cols);
        const x = 20 + col * cellSize;
        const y = 20 + row * cellSize;
        const color = getColor(c, colorMode);

        ctx.fillStyle = color;
        ctx.fillRect(x, y, cellSize - 1, cellSize - 1);

        conceptPositions.push({{ x, y, r: cellSize / 2, concept: c }});
    }});
}}

function renderSpectrum(items, colorMode) {{
    const W = canvas.width, H = canvas.height;
    const sorted = [...items].sort((a, b) => {{
        const ah = parseInt(a.hex.slice(1), 16);
        const bh = parseInt(b.hex.slice(1), 16);
        return ah - bh;
    }});

    const stripH = H / 4;
    sorted.forEach((c, i) => {{
        const x = (i / sorted.length) * W;
        const color = getColor(c, colorMode);
        ctx.fillStyle = color;
        ctx.fillRect(x, stripH, Math.max(1, W / sorted.length), stripH * 2);

        conceptPositions.push({{ x, y: stripH, r: 5, concept: c }});
    }});
}}

function renderClusters(items, colorMode) {{
    const W = canvas.width, H = canvas.height;
    const mogs = [...new Set(items.map(c => c.mog))].sort();
    const clusterW = W / Math.ceil(mogs.length / 2);
    const clusterH = H / 2;

    mogs.forEach((mog, mi) => {{
        const cx = (mi % 2) * clusterW + clusterW / 2;
        const cy = Math.floor(mi / 2) * clusterH + clusterH / 2;
        const mogItems = items.filter(c => c.mog === mog);

        // Draw cluster label
        ctx.fillStyle = '#8888a0';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(mog, cx, cy - clusterH / 2 + 15);

        // Draw concepts in circle
        mogItems.forEach((c, ci) => {{
            const angle = (ci / mogItems.length) * Math.PI * 2;
            const radius = 30 + ci * 2;
            const x = cx + Math.cos(angle) * radius;
            const y = cy + Math.sin(angle) * radius;
            const color = getColor(c, colorMode);
            const r = 3 + c.nrci * 4;

            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.6 + c.nrci * 0.4;
            ctx.fill();
            ctx.globalAlpha = 1;

            conceptPositions.push({{ x, y, r, concept: c }});
        }});
    }});
}}

// ── Interaction ───────────────────────────────────────────
canvas.addEventListener('mousemove', e => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let found = null;
    for (const pos of conceptPositions) {{
        const dx = mx - pos.x, dy = my - pos.y;
        if (dx * dx + dy * dy < pos.r * pos.r * 2) {{
            found = pos.concept;
            break;
        }}
    }}

    if (found) {{
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX + 15) + 'px';
        tooltip.style.top = (e.clientY + 15) + 'px';
        tooltip.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <div style="width:20px;height:20px;border-radius:4px;background:${{found.hex}};border:1px solid #2a2a3a"></div>
                <strong>${{found.word}}</strong>
            </div>
            <div style="color:#8888a0;font-size:11px">
                Color: ${{found.hex}}<br>
                NRCI: ${{found.nrci}}<br>
                MOG: ${{found.mog}}<br>
                Quadrants: ${{JSON.stringify(found.quadrants)}}<br>
                HW: ${{found.hamming_weight}}/24
                ${{found.definition ? '<br>Def: ' + found.definition : ''}}
            </div>
        `;
    }} else {{
        tooltip.style.display = 'none';
    }}
}});

canvas.addEventListener('click', e => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    for (const pos of conceptPositions) {{
        const dx = mx - pos.x, dy = my - pos.y;
        if (dx * dx + dy * dy < pos.r * pos.r * 2) {{
            const searchBox = document.getElementById('searchBox');
            searchBox.value = pos.concept.word;
            filterConcepts();
            break;
        }}
    }}
}});

function resetView() {{
    document.getElementById('viewMode').value = 'scatter';
    document.getElementById('colorMode').value = 'raw';
    document.getElementById('mogFilter').value = 'all';
    document.getElementById('nrciFilter').value = 0;
    document.getElementById('nrciValue').textContent = '0.0';
    render();
}}

// ── Concept List ──────────────────────────────────────────
function renderConceptList() {{
    filterConcepts();
}}

function filterConcepts() {{
    const search = document.getElementById('searchBox').value.toLowerCase();
    const list = document.getElementById('conceptList');
    const filtered = concepts
        .filter(c => !search || c.word.includes(search))
        .sort((a, b) => b.nrci - a.nrci)
        .slice(0, 50);

    list.innerHTML = filtered.map(c => `
        <div class="color-card">
            <div class="color-swatch" style="background:${{c.hex}}"></div>
            <div class="color-info">
                <div class="word">${{c.word}}</div>
                <div class="meta">${{c.hex}} | NRCI ${{c.nrci}} | ${{c.mog}}</div>
            </div>
        </div>
    `).join('');
}}

window.addEventListener('resize', render);
init();
</script>
</body>
</html>"""

    output_file = BASE_DIR / "templates" / "color_space.html"
    output_file.write_text(html)
    print(f"    HTML saved to {output_file}")


if __name__ == "__main__":
    main()
