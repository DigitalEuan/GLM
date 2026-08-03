"""
UBP Visual Bridge v2.0
======================
Handles the export of 3D geometric data from the Python Kernel to the 
React/Three.js Visualizer.

FEATURES:
1. Fraction-Aware: Automatically converts UBP Fractions to floats for rendering.
2. Primitives: Helpers for Points, Spheres, and Lines.
3. Auto-Sync: Writes to 'scene_3d.json' which triggers the frontend update.

USAGE:
    from ubp_viz import save_scene_3d, sphere, line
    
    scene = {
        "spheres": [sphere(0, 0, 0, r=1, color="#ff0000")],
        "lines": [line([0,0,0], [5,5,5], color="#00ff00")]
    }
    save_scene_3d(scene)

Author: Euan R A Craig, New Zealand
Date: 20 Feb 2026
"""

import json
import os
from fractions import Fraction

# The file watched by the React Frontend
SCENE_FILE = 'scene_3d.json'

class UBPJSONEncoder(json.JSONEncoder):
    """
    Custom encoder to handle UBP specific types (Fractions) 
    converting them to floats for WebGL rendering.
    """
    def default(self, obj):
        if isinstance(obj, Fraction):
            return float(obj)
        return super().default(obj)

def point(x, y, z, color="#ffffff", size=0.1, label=""):
    """Constructs a Point dictionary."""
    return {
        "x": x, 
        "y": y, 
        "z": z, 
        "color": color, 
        "size": size, 
        "label": str(label)
    }

def sphere(x, y, z, r=0.5, color="#00ffff", label=""):
    """Constructs a Sphere dictionary."""
    return {
        "x": x, 
        "y": y, 
        "z": z, 
        "r": r, 
        "color": color, 
        "label": str(label)
    }

def line(start, end, color="#888888", width=1.0):
    """
    Constructs a Line dictionary.
    start: [x, y, z]
    end: [x, y, z]
    """
    return {
        "start": start, 
        "end": end, 
        "color": color, 
        "width": width
    }

def save_scene_3d(data, filename=SCENE_FILE):
    """
    Serializes the scene dictionary to JSON.
    
    Args:
        data (dict): Must contain keys 'points', 'spheres', or 'lines'.
        filename (str): Output filename (default: scene_3d.json).
    """
    if not isinstance(data, dict):
        print(f"[UBP Viz] Error: Data must be a dictionary, got {type(data)}")
        return

    try:
        with open(filename, 'w') as f:
            json.dump(data, f, cls=UBPJSONEncoder, indent=2)
        
        # Calculate stats for feedback
        counts = []
        if 'spheres' in data: counts.append(f"{len(data['spheres'])} Spheres")
        if 'lines' in data: counts.append(f"{len(data['lines'])} Lines")
        if 'points' in data: counts.append(f"{len(data['points'])} Points")
        
        summary = ", ".join(counts) if counts else "Empty Scene"
        print(f"[UBP Viz] 👁️  Scene rendered to '{filename}' ({summary})")
        
    except Exception as e:
        print(f"[UBP Viz] ❌ Error saving scene: {e}")

def demo():
    """Generates a test pattern to verify the bridge."""
    print("Running UBP Viz Demo...")
    
    # Create a spiral
    import math
    spheres = []
    lines = []
    
    # Central Anchor
    spheres.append(sphere(0, 0, 0, r=1.0, color="#ffd700", label="Origin"))
    
    prev_pos = [0, 0, 0]
    
    for i in range(1, 25):
        t = i * 0.5
        r = i * 0.2
        x = r * math.cos(t)
        y = i * 0.3
        z = r * math.sin(t)
        
        curr_pos = [x, y, z]
        
        # Color gradient based on height
        g = int((i / 25) * 255)
        color = f"#00{g:02x}ff"
        
        spheres.append(sphere(x, y, z, r=0.3, color=color, label=f"Node_{i}"))
        lines.append(line(prev_pos, curr_pos, color="#444444"))
        
        prev_pos = curr_pos

    scene = {
        "spheres": spheres,
        "lines": lines
    }
    
    save_scene_3d(scene)

if __name__ == "__main__":
    demo()