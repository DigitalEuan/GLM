"""
Layer 4 — RELATION: the unified body state.

ONE state file. Holds nodes, edges, faces, anti-faces, and per-subject
history pointers. This replaces:
  - glm_state.json (CRG edges)
  - geometric_body.json (faces)
  - anti_crg.json (anti-faces)
  - hexcolour_addresses.json (node properties)
  - ltm_state.json (face strengths)

All unified into ONE body_state.json.

The body is NOT a separate system from the CRG. The CRG IS the body's
edge structure. Anti-CRG IS the body's anti-face structure. LTM IS the
body's face-strength accumulation. HexColour addresses ARE node properties.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

from .body import Body
from .data_object import DataObject


@dataclass
class Node:
    """A node in the body = a concept = a data_object with metadata."""
    name: str
    data_object: DataObject
    role: str = "unknown"          # NOUN, ADJECTIVE, VERB, OPERATOR
    definition: str = ""
    domain: str = "general"        # language, chemistry, math, script, etc.
    address: int = 0               # hexcolour address (lattice position)
    crg_degree: int = 0            # how many edges touch this node
    created_at: float = field(default_factory=time.time)


@dataclass
class Edge:
    """An edge in the body = a CRG edge (d²=8 minimal vector)."""
    src: str        # node name
    label: str      # relation type
    dst: str        # node name
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)


@dataclass
class Face:
    """A face in the body = a successful triad (a, b, c).

    The face normal is a ⊕ b ⊕ c (24-bit). A face is 'closed' if the normal
    is itself a Golay codeword (syndrome weight 0).
    """
    triple: Tuple[str, str, str]   # sorted node names
    normal: int                    # int(a ⊕ b ⊕ c)
    closed: bool                   # is normal a Golay codeword?
    strength: int = 1
    task_types: Set[str] = field(default_factory=set)
    transformations: Set[str] = field(default_factory=set)
    last_used: float = field(default_factory=time.time)


@dataclass
class AntiFace:
    """An anti-face = a triad that FAILED together.

    The anti-face normal is the COMPLEMENT of (a ⊕ b ⊕ c) — geometrically
    the opposite plane. After threshold failures, the triad is blacklisted.
    """
    triple: Tuple[str, str, str]
    normal: int                    # complement of a ⊕ b ⊕ c
    original_normal: int           # the actual a ⊕ b ⊕ c
    strength: int = 1
    task_types: Set[str] = field(default_factory=set)
    transformations: Set[str] = field(default_factory=set)


class BodyState:
    """The unified body state. ONE file. All structure.

    Nodes + Edges + Faces + AntiFaces + per-subject history pointers.
    """

    def __init__(self, body: Body, state_path: Optional[Path] = None):
        self.body = body
        self.state_path = state_path or Path("body_state.json")
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.faces: Dict[Tuple[str, str, str], Face] = {}
        self.anti_faces: Dict[Tuple[str, str, str], AntiFace] = {}
        self.blacklist_threshold = 2
        self._load()

    # ═════════════════════════════════════════════════════════════════════
    # NODES
    # ═════════════════════════════════════════════════════════════════════

    def add_node(self, name: str, data_object: DataObject, role: str = "unknown",
                 definition: str = "", domain: str = "general") -> Node:
        """Add or update a node."""
        if name in self.nodes:
            # Update metadata if node already exists
            n = self.nodes[name]
            if role != "unknown": n.role = role
            if definition: n.definition = definition
            if domain != "general": n.domain = domain
            return n
        # Compute hexcolour address (the lattice position)
        address = data_object.to_int()
        node = Node(
            name=name, data_object=data_object, role=role,
            definition=definition, domain=domain, address=address,
        )
        self.nodes[name] = node
        return node

    def get_node(self, name: str) -> Optional[Node]:
        return self.nodes.get(name)

    def find_similar_nodes(self, v: DataObject, max_hamming: int = 6) -> List[Tuple[str, int]]:
        """Find nodes with data_objects similar to v (by Hamming distance)."""
        results = []
        for name, node in self.nodes.items():
            d = v.hamming_distance(node.data_object)
            if d <= max_hamming:
                results.append((name, d))
        results.sort(key=lambda x: x[1])
        return results

    # ═════════════════════════════════════════════════════════════════════
    # EDGES
    # ═════════════════════════════════════════════════════════════════════

    def add_edge(self, src: str, label: str, dst: str, weight: float = 1.0):
        """Add an edge (CRG edge)."""
        # Avoid duplicates
        for e in self.edges:
            if e.src == src and e.label == label and e.dst == dst:
                e.weight = max(e.weight, weight)
                return
        self.edges.append(Edge(src=src, label=label, dst=dst, weight=weight))
        # Update CRG degrees
        if src in self.nodes: self.nodes[src].crg_degree += 1
        if dst in self.nodes: self.nodes[dst].crg_degree += 1

    def get_edges(self, node_name: str) -> List[Edge]:
        """Get all edges touching a node."""
        return [e for e in self.edges if e.src == node_name or e.dst == node_name]

    def get_neighbors(self, node_name: str) -> List[str]:
        """Get all neighbor node names."""
        neighbors = set()
        for e in self.edges:
            if e.src == node_name: neighbors.add(e.dst)
            if e.dst == node_name: neighbors.add(e.src)
        return list(neighbors)

    # ═════════════════════════════════════════════════════════════════════
    # FACES (positive knowledge — successful triads)
    # ═════════════════════════════════════════════════════════════════════

    def record_face(self, concept_names: List[str], task_type: str,
                    transformation: str):
        """Record a successful triad as a face."""
        if len(concept_names) < 3:
            return
        triple = tuple(sorted(concept_names[:3]))
        # Compute normal = a ⊕ b ⊕ c
        vs = [self.nodes[n].data_object for n in triple if n in self.nodes]
        if len(vs) < 3:
            return
        normal_bits = [a ^ b ^ c for a, b, c in zip(vs[0].bits, vs[1].bits, vs[2].bits)]
        normal = DataObject(bits=normal_bits).to_int()
        # Closed if normal is a Golay codeword (syndrome weight 0)
        closed = self.body.syndrome_weight(normal_bits) == 0

        if triple in self.faces:
            f = self.faces[triple]
            f.strength += 2 if closed else 1
            f.task_types.add(task_type)
            f.transformations.add(transformation)
            f.last_used = time.time()
        else:
            self.faces[triple] = Face(
                triple=triple, normal=normal, closed=closed,
                strength=2 if closed else 1,
                task_types={task_type},
                transformations={transformation},
            )

    def find_similar_faces(self, concept_names: List[str],
                            max_hamming: int = 6) -> List[Tuple[Tuple[str, str, str], int, int]]:
        """Find faces with similar normals to the given concept triad."""
        if len(concept_names) < 3:
            return []
        triple = tuple(sorted(concept_names[:3]))
        vs = [self.nodes[n].data_object for n in triple if n in self.nodes]
        if len(vs) < 3:
            return []
        target_normal = DataObject(bits=[a ^ b ^ c for a, b, c in zip(vs[0].bits, vs[1].bits, vs[2].bits)]).to_int()

        results = []
        for face_triple, face in self.faces.items():
            xor = face.normal ^ target_normal
            hamming = bin(xor).count("1")
            if hamming <= max_hamming:
                results.append((face_triple, hamming, face.strength))
        results.sort(key=lambda x: (x[1], -x[2]))
        return results

    # ═════════════════════════════════════════════════════════════════════
    # ANTI-FACES (negative knowledge — failed triads)
    # ═════════════════════════════════════════════════════════════════════

    def record_anti_face(self, concept_names: List[str], task_type: str,
                          transformation: str):
        """Record a failed triad as an anti-face."""
        if len(concept_names) < 3:
            return
        triple = tuple(sorted(concept_names[:3]))
        vs = [self.nodes[n].data_object for n in triple if n in self.nodes]
        if len(vs) < 3:
            return
        normal_bits = [a ^ b ^ c for a, b, c in zip(vs[0].bits, vs[1].bits, vs[2].bits)]
        normal = DataObject(bits=normal_bits).to_int()
        anti_normal = normal ^ ((1 << 24) - 1)  # complement

        if triple in self.anti_faces:
            af = self.anti_faces[triple]
            af.strength += 1
            af.task_types.add(task_type)
            af.transformations.add(transformation)
        else:
            self.anti_faces[triple] = AntiFace(
                triple=triple, normal=anti_normal, original_normal=normal,
                strength=1, task_types={task_type}, transformations={transformation},
            )

    def is_blacklisted(self, concept_names: List[str], task_type: str) -> bool:
        """Check if a triad is blacklisted for a task type."""
        if len(concept_names) < 3:
            return False
        triple = tuple(sorted(concept_names[:3]))
        af = self.anti_faces.get(triple)
        if af is None:
            return False
        if af.strength >= self.blacklist_threshold:
            return task_type in af.task_types or len(af.task_types) >= 2
        return False

    def clear_anti_face(self, concept_names: List[str]):
        """Clear anti-faces for a triad (when it later succeeds)."""
        if len(concept_names) < 3:
            return
        triple = tuple(sorted(concept_names[:3]))
        self.anti_faces.pop(triple, None)

    # ═════════════════════════════════════════════════════════════════════
    # PERSISTENCE (ONE file)
    # ═════════════════════════════════════════════════════════════════════

    def save(self):
        """Save the unified body state to ONE JSON file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "nodes": {
                name: {
                    "bits": n.data_object.bits,
                    "role": n.role,
                    "definition": n.definition,
                    "domain": n.domain,
                    "address": n.address,
                    "crg_degree": n.crg_degree,
                    "created_at": n.created_at,
                }
                for name, n in self.nodes.items()
            },
            "edges": [
                {"src": e.src, "label": e.label, "dst": e.dst, "weight": e.weight}
                for e in self.edges
            ],
            "faces": {
                "|".join(triple): {
                    "normal": f.normal,
                    "closed": f.closed,
                    "strength": f.strength,
                    "task_types": list(f.task_types),
                    "transformations": list(f.transformations),
                    "last_used": f.last_used,
                }
                for triple, f in self.faces.items()
            },
            "anti_faces": {
                "|".join(triple): {
                    "normal": af.normal,
                    "original_normal": af.original_normal,
                    "strength": af.strength,
                    "task_types": list(af.task_types),
                    "transformations": list(af.transformations),
                }
                for triple, af in self.anti_faces.items()
            },
            "blacklist_threshold": self.blacklist_threshold,
        }
        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from the unified state file."""
        if not self.state_path.exists():
            return
        try:
            with open(self.state_path) as f:
                data = json.load(f)
            # Nodes
            for name, nd in data.get("nodes", {}).items():
                self.nodes[name] = Node(
                    name=name,
                    data_object=DataObject(bits=nd["bits"]),
                    role=nd.get("role", "unknown"),
                    definition=nd.get("definition", ""),
                    domain=nd.get("domain", "general"),
                    address=nd.get("address", 0),
                    crg_degree=nd.get("crg_degree", 0),
                    created_at=nd.get("created_at", time.time()),
                )
            # Edges
            for ed in data.get("edges", []):
                self.edges.append(Edge(
                    src=ed["src"], label=ed["label"], dst=ed["dst"],
                    weight=ed.get("weight", 1.0),
                ))
            # Faces
            for k, fd in data.get("faces", {}).items():
                triple = tuple(k.split("|"))
                self.faces[triple] = Face(
                    triple=triple, normal=fd["normal"], closed=fd["closed"],
                    strength=fd["strength"],
                    task_types=set(fd.get("task_types", [])),
                    transformations=set(fd.get("transformations", [])),
                    last_used=fd.get("last_used", time.time()),
                )
            # Anti-faces
            for k, fd in data.get("anti_faces", {}).items():
                triple = tuple(k.split("|"))
                self.anti_faces[triple] = AntiFace(
                    triple=triple, normal=fd["normal"],
                    original_normal=fd.get("original_normal", fd["normal"]),
                    strength=fd["strength"],
                    task_types=set(fd.get("task_types", [])),
                    transformations=set(fd.get("transformations", [])),
                )
            self.blacklist_threshold = data.get("blacklist_threshold", 2)
        except Exception as e:
            print(f"[BodyState] Load error: {e}")

    # ═════════════════════════════════════════════════════════════════════
    # STATS
    # ═════════════════════════════════════════════════════════════════════

    def stats(self) -> Dict[str, Any]:
        """Summary statistics."""
        closed_faces = sum(1 for f in self.faces.values() if f.closed)
        blacklisted = sum(1 for af in self.anti_faces.values()
                         if af.strength >= self.blacklist_threshold)
        return {
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "n_faces": len(self.faces),
            "n_closed_faces": closed_faces,
            "n_anti_faces": len(self.anti_faces),
            "n_blacklisted": blacklisted,
        }
