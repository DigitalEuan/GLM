import json
from ubp_unified_v5 import BinaryLinearAlgebra

def simplify_manifold():
    # Load the current state (simulated from your JSON or use existing scene_3d.json if available)
    # For this script, we generate a synthetic test set to demonstrate the simplification logic.
    nodes = [
        {"name": "Spatial", "vec": [1,0,1,0,0,0,0,1,0,0,0,1,1,0,0,1,1,1,1,1,1,1,0,0], "pos": [4, -4, 0]},
        {"name": "Geometry", "vec": [0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], "pos": [-2, 0, 2]},
        {"name": "Concept", "vec": [1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0], "pos": [0, -2, 2]},
        {"name": "Belief", "vec": [0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1], "pos": [2, 0, -2]},
        {"name": "Memory", "vec": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], "pos": [4, 2, 2]},
        {"name": "Interference", "vec": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "pos": [0, 0, 0]}
    ]
    
    simplified_lines = []
    
    print("--- SPATIAL FACE ANALYSIS (v5.3 Core) ---")
    # Rule: Only draw lines that form a "Face" with the Interference Node (0,0,0)
    # This creates a "Pyramid" structure instead of a "Web"
    origin = nodes[5]
    for i in range(5):
        node = nodes[i]
        # 1. Draw the "Spine" (Edge to Origin)
        simplified_lines.append({
            "start": node["pos"], "end": origin["pos"], "color": "#ffd700" # Gold
        })
        
        # 2. Check for "Face" neighbors (Nodes within distance 10)
        for j in range(i + 1, 5):
            neighbor = nodes[j]
            dist = BinaryLinearAlgebra.hamming_distance(node["vec"], neighbor["vec"])
            if dist <= 10:
                # This edge forms a stable Face with the Origin
                simplified_lines.append({
                    "start": node["pos"], "end": neighbor["pos"], "color": "#00ff00" # Green
                })
                print(f"Face Found: {node['name']} <-> {neighbor['name']} <-> Interference")

    # Export the simplified scene
    scene = {
        "spheres": [{"x": n["pos"][0], "y": n["pos"][1], "z": n["pos"][2], "r": 0.3, "color": "#00ffff"} for n in nodes],
        "lines": simplified_lines
    }
    
    with open('scene_3d.json', 'w') as f:
        json.dump(scene, f)
    print("\n[RESULT] Complexity Dialed Back. Manifold simplified to Stable Faces.")

if __name__ == "__main__":
    simplify_manifold()