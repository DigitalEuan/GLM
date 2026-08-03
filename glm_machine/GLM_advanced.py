#!/usr/bin/env python3
"""
GLM ADVANCED: Geometric Realignment + Time-Based Dynamics + 3D Visualization
==============================================================================

1. GEOMETRIC REALIGNMENT — Iterative force-directed layout
2. TIME-BASED DYNAMICS — Concepts drift toward semantic neighbors
3. 3D VISUALIZATION — See the knowledge graph as a physical object

Key constraint: Changes must respect Golay codeword structure.
We can't freely move points — we must snap to valid Golay codewords.
"""

import math
import json
from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict

# Golay codeword distance table (precomputed for speed)
_GOLAY_CACHE = {}


class ForceDirectedRealigner:
    """Iterative force-directed layout within Golay codeword constraints.

    Treats the CRG as a physical system:
    - Edges are attractive springs (pull related concepts together)
    - Non-edges are repulsive forces (push unrelated concepts apart)
    - Concepts snap to nearest valid Golay codeword after each iteration

    This is NOT free-form optimization — the Golay code constrains
    where concepts can move. The system seeks a low-energy configuration
    that respects both the semantic relationships AND the code structure.
    """

    def __init__(self, vocab, crg):
        self.vocab = vocab
        self.crg = crg
        self.iteration = 0
        self.energy_history = []

        # Precompute Golay codeword quadrants
        from GLM01_substrate import GOLAY_ENGINE
        self.all_codewords = GOLAY_ENGINE.get_all_codewords()
        self._cw_quadrants = []
        for cw in self.all_codewords:
            q = [sum(cw[0:6]), sum(cw[6:12]), sum(cw[12:18]), sum(cw[18:24])]
            self._cw_quadrants.append((list(cw), q))

    def step(self, pull_strength: float = 0.3) -> float:
        """Run one iteration — PULL related concepts closer only.

        No repulsion. Only attractive forces from CRG edges.
        This ensures concepts only move closer, never apart.
        """
        SKIP = {"auto_proposed", "co_occurs"}
        total_energy = 0.0
        moved = 0

        for edge in self.crg.edges:
            if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                continue
            v1 = self._get_q(edge.src)
            v2 = self._get_q(edge.dst)
            if not v1 or not v2:
                continue

            dist = math.sqrt(sum((a-b)**2 for a, b in zip(v1, v2)))
            if dist < 2.0:  # Already close enough
                continue

            # Pull both toward midpoint
            mid = [(a+b)/2 for a, b in zip(v1, v2)]

            for word, old_q in [(edge.src, v1), (edge.dst, v2)]:
                entry = self.vocab.get(word)
                if not entry or not hasattr(entry, 'vector'):
                    continue

                # Pull toward midpoint
                new_q = [old_q[i] + pull_strength * (mid[i] - old_q[i]) for i in range(4)]
                new_q = [max(0, min(6, int(round(x)))) for x in new_q]

                # Find nearest Golay codeword
                best_cw = None
                best_dist = float('inf')
                for cw, cq in self._cw_quadrants:
                    d = math.sqrt(sum((a-b)**2 for a, b in zip(new_q, cq)))
                    if d < best_dist:
                        best_dist = d
                        best_cw = cw

                if best_cw and list(best_cw) != list(entry.vector):
                    entry.vector = list(best_cw)
                    entry.golay_codeword = list(best_cw)
                    moved += 1

            total_energy += dist

        self.iteration += 1
        self.energy_history.append(total_energy)
        return total_energy

    def run(self, iterations: int = 10, verbose: bool = True) -> List[float]:
        """Run multiple iterations."""
        energies = []
        for i in range(iterations):
            energy = self.step()
            energies.append(energy)
            if verbose:
                print(f"  Iteration {i+1}: energy={energy:.2f}")
        return energies

    def measure_coherence(self) -> Dict[str, float]:
        """Measure the physical coherence of the knowledge graph."""
        SKIP = {"auto_proposed", "co_occurs"}
        distances = []
        for edge in self.crg.edges:
            if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                continue
            v1 = self._get_q(edge.src)
            v2 = self._get_q(edge.dst)
            if v1 and v2:
                dist = math.sqrt(sum((a-b)**2 for a, b in zip(v1, v2)))
                distances.append(dist)
        if not distances:
            return {"avg": 0, "max": 0, "coherence": 1.0, "pairs": 0}
        avg = sum(distances) / len(distances)
        return {
            "avg_distance": avg,
            "max_distance": max(distances),
            "coherence": 1.0 / (1.0 + avg / 5.0),
            "pairs_measured": len(distances),
        }

    def _get_q(self, word: str) -> Optional[List[int]]:
        entry = self.vocab.get(word)
        if not entry or not hasattr(entry, 'vector') or not entry.vector:
            return None
        v = entry.vector
        if sum(v) == 0:
            return None
        return [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]


class TimeBasedDynamics:
    """Concepts drift toward their semantic neighbors over time.

    Like atoms settling into a crystal lattice, concepts gradually
    move closer to their CRG neighbors. This is a physical process —
    the knowledge graph seeks its lowest energy state.

    Key constraint: We snap to Golay codewords after each drift step.
    This prevents arbitrary drift and preserves the code structure.
    """

    def __init__(self, vocab, crg):
        self.vocab = vocab
        self.crg = crg
        self.time = 0
        self.drift_log = []

        from GLM01_substrate import GOLAY_ENGINE
        self.all_codewords = GOLAY_ENGINE.get_all_codewords()

    def tick(self, drift_rate: float = 0.1) -> int:
        """Advance one time step. Concepts drift toward neighbors.

        Returns number of concepts that moved.
        """
        SKIP = {"auto_proposed", "co_occurs"}
        moved = 0

        for word, entry in self.vocab.items():
            if not hasattr(entry, 'vector') or not entry.vector:
                continue

            # Find CRG neighbors
            neighbors = []
            for edge in self.crg.out.get(word, []):
                if edge.label not in SKIP and not edge.label.startswith('lattice_adjacent'):
                    n_entry = self.vocab.get(edge.dst)
                    if n_entry and hasattr(n_entry, 'vector') and n_entry.vector:
                        neighbors.append(n_entry.vector)

            if not neighbors:
                continue

            # Compute drift direction (average of neighbor positions)
            v = entry.vector
            drift = [0.0] * 4
            for n_vec in neighbors:
                n_q = [sum(n_vec[0:6]), sum(n_vec[6:12]), sum(n_vec[12:18]), sum(n_vec[18:24])]
                v_q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
                for i in range(4):
                    drift[i] += (n_q[i] - v_q[i]) / len(neighbors)

            # Apply drift
            v_q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
            new_q = [v_q[i] + drift_rate * drift[i] for i in range(4)]
            new_q = [max(0, min(6, int(round(x)))) for x in new_q]

            # Snap to nearest Golay codeword
            best_cw = None
            best_dist = float('inf')
            for cw in self.all_codewords:
                cw_q = [sum(cw[0:6]), sum(cw[6:12]), sum(cw[12:18]), sum(cw[18:24])]
                dist = math.sqrt(sum((a-b)**2 for a, b in zip(new_q, cw_q)))
                if dist < best_dist:
                    best_dist = dist
                    best_cw = list(cw)

            if best_cw and best_cw != list(v):
                entry.vector = best_cw
                entry.golay_codeword = best_cw
                moved += 1
                self.drift_log.append({"word": word, "time": self.time, "drift": drift})

        self.time += 1
        return moved

    def run(self, steps: int = 5, drift_rate: float = 0.1, verbose: bool = True) -> List[int]:
        """Run multiple time steps."""
        movements = []
        for i in range(steps):
            moved = self.tick(drift_rate)
            movements.append(moved)
            if verbose:
                print(f"  Time {i+1}: {moved} concepts drifted")
        return movements


class GraphVisualizer3D:
    """3D visualization of the knowledge graph.

    Each concept maps to a 3D position (quadrant weights).
    Edges are rendered as lines. Colors indicate ontological layers.
    """

    def __init__(self, vocab, crg):
        self.vocab = vocab
        self.crg = crg

    def export_positions(self) -> Dict[str, Dict]:
        """Export concept positions for 3D rendering."""
        positions = {}
        for word, entry in self.vocab.items():
            if not hasattr(entry, 'vector') or not entry.vector or sum(entry.vector) == 0:
                continue
            v = entry.vector
            x = sum(v[0:6])     # Reality
            y = sum(v[6:12])    # Information
            z = sum(v[12:18])   # Activation
            p = sum(v[18:24])   # Potential (color intensity)
            nrci = float(entry.nrci) if hasattr(entry, 'nrci') else 0.5

            # Determine dominant layer
            q = [x, y, z, p]
            dominant = q.index(max(q))
            layer_names = ["Reality", "Information", "Activation", "Potential"]

            positions[word] = {
                "x": x, "y": y, "z": z,
                "potential": p,
                "nrci": nrci,
                "layer": layer_names[dominant],
                "hw": sum(v),
            }
        return positions

    def export_edges(self) -> List[Dict]:
        """Export edges for 3D rendering."""
        SKIP = {"auto_proposed", "co_occurs"}
        edges = []
        for edge in self.crg.edges:
            if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                continue
            edges.append({
                "src": edge.src,
                "dst": edge.dst,
                "label": edge.label,
            })
        return edges

    def export_html(self, filepath: str = "graph3d.html"):
        """Export an interactive 3D visualization as HTML."""
        positions = self.export_positions()
        edges = self.export_edges()

        # Filter to concepts with positions
        valid_concepts = set(positions.keys())
        edges = [e for e in edges if e["src"] in valid_concepts and e["dst"] in valid_concepts]

        # Color map for layers
        colors = {
            "Reality": "#e74c3c",      # Red
            "Information": "#3498db",  # Blue
            "Activation": "#2ecc71",   # Green
            "Potential": "#f39c12",    # Orange
        }

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GLM Knowledge Graph — 3D Visualization</title>
    <style>
        body {{ margin: 0; overflow: hidden; background: #1a1a2e; font-family: monospace; }}
        canvas {{ display: block; }}
        #info {{ position: absolute; top: 10px; left: 10px; color: #eee; background: rgba(0,0,0,0.7); padding: 15px; border-radius: 8px; max-width: 300px; }}
        #info h3 {{ margin: 0 0 10px 0; color: #f39c12; }}
        #legend {{ position: absolute; bottom: 10px; left: 10px; color: #eee; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 8px; }}
        .layer {{ margin: 3px 0; }}
        .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }}
        #stats {{ position: absolute; top: 10px; right: 10px; color: #eee; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 8px; }}
    </style>
</head>
<body>
    <div id="info">
        <h3>GLM Knowledge Graph</h3>
        <p>Drag to rotate. Scroll to zoom.</p>
        <p>Hover over nodes for details.</p>
    </div>
    <div id="legend">
        <div class="layer"><span class="dot" style="background:#e74c3c"></span>Reality (Nouns)</div>
        <div class="layer"><span class="dot" style="background:#3498db"></span>Information (Adjectives)</div>
        <div class="layer"><span class="dot" style="background:#2ecc71"></span>Activation (Verbs)</div>
        <div class="layer"><span class="dot" style="background:#f39c12"></span>Potential (Operators)</div>
    </div>
    <div id="stats">
        <div>Concepts: {len(positions)}</div>
        <div>Edges: {len(edges)}</div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        const positions = {json.dumps(positions)};
        const edges = {json.dumps(edges)};
        const colors = {json.dumps(colors)};

        // Setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        // Center of mass
        let cx=0, cy=0, cz=0, count=0;
        for (const [word, pos] of Object.entries(positions)) {{
            cx += pos.x; cy += pos.y; cz += pos.z; count++;
        }}
        cx /= count; cy /= count; cz /= count;

        // Create nodes
        const nodeMap = {{}};
        for (const [word, pos] of Object.entries(positions)) {{
            const geo = new THREE.SphereGeometry(0.15 + pos.nrci * 0.15, 8, 8);
            const color = colors[pos.layer] || '#ffffff';
            const mat = new THREE.MeshBasicMaterial({{ color: color }});
            const mesh = new THREE.Mesh(geo, mat);
            mesh.position.set(pos.x - cx, pos.y - cy, pos.z - cz);
            mesh.userData = {{ word: word, ...pos }};
            scene.add(mesh);
            nodeMap[word] = mesh;
        }}

        // Create edges
        for (const edge of edges) {{
            const src = nodeMap[edge.src];
            const dst = nodeMap[edge.dst];
            if (!src || !dst) continue;
            const points = [src.position.clone(), dst.position.clone()];
            const geo = new THREE.BufferGeometry().setFromPoints(points);
            const mat = new THREE.LineBasicMaterial({{ color: 0x444466, transparent: true, opacity: 0.3 }});
            const line = new THREE.Line(geo, mat);
            scene.add(line);
        }}

        // Camera
        camera.position.set(10, 10, 10);
        camera.lookAt(0, 0, 0);

        // Mouse controls
        let isDragging = false;
        let prevMouse = {{ x: 0, y: 0 }};
        let rotX = 0, rotY = 0;

        document.addEventListener('mousedown', (e) => {{ isDragging = true; prevMouse = {{ x: e.clientX, y: e.clientY }}; }});
        document.addEventListener('mouseup', () => isDragging = false);
        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            rotY += (e.clientX - prevMouse.x) * 0.005;
            rotX += (e.clientY - prevMouse.y) * 0.005;
            prevMouse = {{ x: e.clientX, y: e.clientY }};
        }});
        document.addEventListener('wheel', (e) => {{
            camera.position.multiplyScalar(e.deltaY > 0 ? 1.05 : 0.95);
        }});

        // Raycaster for hover
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        document.addEventListener('mousemove', (e) => {{
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        }});

        // Animate
        function animate() {{
            requestAnimationFrame(animate);

            // Auto-rotate slowly
            if (!isDragging) rotY += 0.002;

            // Apply rotation to all objects
            scene.rotation.x = rotX;
            scene.rotation.y = rotY;

            // Hover detection
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(scene.children.filter(c => c.isMesh));
            const infoDiv = document.getElementById('info');
            if (intersects.length > 0) {{
                const data = intersects[0].object.userData;
                infoDiv.innerHTML = `<h3>${{data.word}}</h3>
                    <p>Layer: ${{data.layer}}</p>
                    <p>NRCI: ${{data.nrci.toFixed(3)}}</p>
                    <p>Position: (${{data.x}}, ${{data.y}}, ${{data.z}})</p>`;
            }} else {{
                infoDiv.innerHTML = '<h3>GLM Knowledge Graph</h3><p>Drag to rotate. Scroll to zoom.</p><p>Hover over nodes for details.</p>';
            }}

            renderer.render(scene, camera);
        }}
        animate();

        // Resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>"""

        with open(filepath, 'w') as f:
            f.write(html)
        print(f"Exported 3D visualization to {filepath}")
        print(f"  Concepts: {len(positions)}")
        print(f"  Edges: {len(edges)}")
        return filepath


if __name__ == "__main__":
    print("=== GLM Advanced: Realignment + Dynamics + Visualization ===")
