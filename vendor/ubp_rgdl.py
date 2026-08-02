#!/usr/bin/env python3
"""
UBP RGDL Engine v5.1 (Resonance Geometry Definition Language)
=============================================================
The Standard Visualization Engine for the UBP System.
Upgraded to use ExactMath and True Leech Lattice NRCI coloring.

"Geometry is the macroscopic manifestation of synchronized binary toggles."

Author: E R A Craig & UBP Research Cortex
"""
import sys
from fractions import Fraction

# Import the hardened unified backbone
from ubp_unified_v5 import ExactMath, GOLAY_ENGINE, LEECH_ENGINE

try:
    import ubp_viz
    VIZ_ACTIVE = True
except ImportError:
    VIZ_ACTIVE = False
    print("[RGDL] Warning: 'ubp_viz' not found. Visual output disabled.")

def to_gray_code(n: int, bits: int) -> list:
    """Converts an integer coordinate to a Gray code bit array."""
    # Handle negative coordinates by shifting into positive space
    val = (int(n) + 128) % 256 
    gray = val ^ (val >> 1)
    return [(gray >> i) & 1 for i in range(bits - 1, -1, -1)]

class RGDLEngine:
    def __init__(self):
        self.palette = {
            "stable": (0, 255, 255),   # Cyan (NRCI >= 0.7)
            "unstable": (139, 0, 139), # Dark Magenta (NRCI < 0.7)
            "void": (0, 0, 136)        # Deep Blue (Low NRCI)
        }

    def _get_nrci_color(self, x: int, y: int, z: int) -> str:
        """
        Maps a 3D coordinate to a 24-bit vector, snaps it to the lattice,
        and returns a color based on its true NRCI stability.
        """
        # 1. Map spatial coordinates to 24-bit vector (8 bits per axis)
        vec = to_gray_code(x, 8) + to_gray_code(y, 8) + to_gray_code(z, 8)

        # 2. Snap to Leech Lattice
        snapped, _ = GOLAY_ENGINE.snap_to_codeword(vec)
        tax = LEECH_ENGINE.calculate_symmetry_tax(snapped)
        nrci = float(Fraction(10, 1) / (Fraction(10, 1) + tax))

        # 3. Color by Coherence Pressure
        if nrci >= 0.70:
            return f"#{self.palette['stable'][0]:02x}{self.palette['stable'][1]:02x}{self.palette['stable'][2]:02x}"
        elif nrci >= 0.50:
            return f"#{self.palette['unstable'][0]:02x}{self.palette['unstable'][1]:02x}{self.palette['unstable'][2]:02x}"
        else:
            return f"#{self.palette['void'][0]:02x}{self.palette['void'][1]:02x}{self.palette['void'][2]:02x}"

    def generate_sphere(self, radius: int) -> list:
        """Generates a Voxelized Sphere (The Monad) colored by NRCI."""
        voxels = []
        r_sq = radius * radius

        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                for z in range(-radius, radius + 1):
                    dist_sq = x*x + y*y + z*z
                    if dist_sq <= r_sq:
                        voxels.append({
                            "x": x, "y": y, "z": z,
                            "r": 0.4, 
                            "color": self._get_nrci_color(x, y, z)
                        })
        return voxels

    def generate_cube(self, size: int) -> list:
        """Generates a Voxelized Cube (The Matrix) colored by NRCI."""
        voxels = []
        half = size // 2

        for x in range(-half, half + 1):
            for y in range(-half, half + 1):
                for z in range(-half, half + 1):
                    voxels.append({
                        "x": x, "y": y, "z": z,
                        "r": 0.4,
                        "color": self._get_nrci_color(x, y, z)
                    })
        return voxels

    def render(self, voxels: list, label: str = "Geometry"):
        """Injects the geometry into the Visual Cortex."""
        count = len(voxels)
        print(f"--- MANIFESTING {label} ---")
        print(f"Active Toggles: {count}")

        if VIZ_ACTIVE:
            scene = {"spheres": voxels}
            ubp_viz.save_scene_3d(scene)
            print("✅ Scene sent to Visual Cortex.")
        else:
            print("❌ Visualization skipped (No Bridge).")

# --- CONVENIENCE FUNCTIONS ---

def manifest_sphere(radius=10):
    engine = RGDLEngine()
    voxels = engine.generate_sphere(radius)
    engine.render(voxels, f"RGDL SPHERE (r={radius})")

def manifest_cube(size=10):
    engine = RGDLEngine()
    voxels = engine.generate_cube(size)
    engine.render(voxels, f"RGDL CUBE (s={size})")

if __name__ == "__main__":
    # Default behavior: Manifest a Sphere
    manifest_sphere(8)
