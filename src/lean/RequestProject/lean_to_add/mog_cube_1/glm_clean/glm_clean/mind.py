"""
The Mind — ONE class. The cycle: perceive → imagine → propose → commit → learn.

The snap IS the base operation. The Mind perceives by snapping the input
to the nearest codeword. The information is the (before, after, tax) triple.

No subclasses. No separate TCT system. No separate analogy system.
The system GROWS by learning, not by loading.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time

from .body import Body
from .data_object import DataObject, encode
from .measure import Measure, CoherenceRegime
from .body_state import BodyState
from .snap import Snap, SnapResult


@dataclass
class MindState:
    """Transient state (not persisted — body_state persists)."""
    current_subject: str = "default"
    n_snaps: int = 0
    n_proposals: int = 0
    n_commits: int = 0
    last_syndrome_tax: int = 0
    last_nrci: float = 0.0
    last_regime: str = "OnBit"


@dataclass
class Proposal:
    """A candidate concept proposed by the Mind."""
    name: str
    data_object: DataObject
    source: str
    nrci: float
    distance: int


class Mind:
    """The ONE Mind. perceive → imagine → propose → commit → learn.

    The snap is the base operation. perceive() snaps the input and returns
    the SnapResult (before, after, tax). Everything else builds on the snap.
    """

    def __init__(self, body: Optional[Body] = None,
                 state_path: Optional[Path] = None):
        self.body = body or Body()
        self.measure = Measure(self.body)
        self.snap_op = Snap(self.body)
        self.state = BodyState(self.body, state_path or Path("body_state.json"))
        self.mind_state = MindState()

    # ═════════════════════════════════════════════════════════════════════
    # SUBJECT MANAGEMENT
    # ═════════════════════════════════════════════════════════════════════

    def set_subject(self, subject: str):
        self.mind_state.current_subject = subject

    def new_topic(self):
        self.mind_state.current_subject = "default"

    @property
    def current_subject(self) -> str:
        return self.mind_state.current_subject

    # ═════════════════════════════════════════════════════════════════════
    # THE CYCLE
    # ═════════════════════════════════════════════════════════════════════

    def perceive(self, raw_input: Any) -> SnapResult:
        """Encode the input AND snap it. The snap IS the perception.

        Returns the SnapResult (before, after, tax) — the information triple.
        """
        v = encode(raw_input)
        result = self.snap_op.snap(v)
        self.mind_state.n_snaps += 1
        self.mind_state.last_syndrome_tax = result.syndrome_tax
        self.mind_state.last_nrci = result.after_nrci
        self.mind_state.last_regime = self.measure.regime(result.after).name
        return result

    def imagine(self, snap_result: SnapResult) -> Tuple[DataObject, float, str]:
        """Read the snapped concept: compute NRCI and regime of the AFTER state."""
        nrci = snap_result.after_nrci
        regime = self.measure.regime(snap_result.after).name
        return snap_result.after, nrci, regime

    def propose(self, v: DataObject, max_proposals: int = 5) -> List[Proposal]:
        """Find similar concepts in the body state (by Hamming distance)."""
        proposals = []
        for name, node in self.state.nodes.items():
            d = v.hamming_distance(node.data_object)
            if d <= 8:
                proposals.append(Proposal(
                    name=name, data_object=node.data_object,
                    source="body_lookup", nrci=self.measure.nrci(node.data_object),
                    distance=d,
                ))
            if len(proposals) >= max_proposals:
                break
        proposals.sort(key=lambda p: p.distance)
        self.mind_state.n_proposals += len(proposals)
        return proposals

    def commit(self, concept_names: List[str], task_type: str,
               transformation: str, success: bool):
        """Commit to the body state. Record face (success) or anti-face (failure)."""
        if success:
            self.state.record_face(concept_names, task_type, transformation)
            self.state.clear_anti_face(concept_names)
        else:
            self.state.record_anti_face(concept_names, task_type, transformation)
        self.mind_state.n_commits += 1

    def learn(self):
        """Persist the body state."""
        self.state.save()

    # ═════════════════════════════════════════════════════════════════════
    # THE FULL CYCLE
    # ═════════════════════════════════════════════════════════════════════

    def cycle(self, raw_input: Any, context: str = "") -> Dict[str, Any]:
        """Run the full cycle: perceive (snap) → imagine → propose → commit → learn.

        The snap IS the perception. The information is the (before, after, tax) triple.
        """
        # 1. Perceive (SNAP — the base operation)
        snap_result = self.perceive(raw_input)

        # 2. Imagine (read the snapped concept)
        v, nrci, regime = self.imagine(snap_result)

        # 3. Propose (find similar concepts)
        proposals = self.propose(v)

        # 4. Commit (if proposals found)
        committed = None
        if proposals:
            best = proposals[0]
            self.commit(
                [context or "input", best.name, "result"],
                task_type=context or "general",
                transformation=best.source, success=True
            )
            committed = best

        # 5. Learn
        self.learn()

        return {
            "input": raw_input,
            "before_int": snap_result.before_int,
            "after_int": snap_result.after_int,
            "syndrome_tax": snap_result.syndrome_tax,
            "correction_distance": snap_result.correction_distance,
            "nrci": nrci,
            "regime": regime,
            "n_proposals": len(proposals),
            "committed": committed.name if committed else None,
            "body_state": self.state.stats(),
        }

    # ═════════════════════════════════════════════════════════════════════
    # THE TRIPLE PRODUCT — the full snap triple comparison
    # ═════════════════════════════════════════════════════════════════════

    def triple_distance(self, snap1: SnapResult, snap2: SnapResult) -> float:
        """The full snap triple distance: tax × before × after.

        This is the WINNING strategy from the experiments. It combines all
        three signals multiplicatively:
          - tax: syndrome weight difference (cost of interpretation)
          - before: raw pattern Hamming distance (category signal)
          - after: snapped codeword Hamming distance (pair signal)

        For two concepts to be SIMILAR, ALL THREE must be small.
        For two concepts to be DIFFERENT, ANY ONE being large makes the product large.
        This is an AND-like combination — the right behavior for the GLM.

        Per the experiments: 5/6 categories cluster, +20.5 pair separation.
        """
        tax_d = abs(snap1.syndrome_tax - snap2.syndrome_tax)
        before_d = snap1.before.hamming_distance(snap2.before)
        after_d = snap1.after.hamming_distance(snap2.after)
        return float(tax_d * before_d * after_d)

    def triple_compare(self, snap1: SnapResult, snap2: SnapResult) -> Dict[str, float]:
        """Full triple comparison breakdown."""
        return {
            "tax_diff": float(abs(snap1.syndrome_tax - snap2.syndrome_tax)),
            "before_dist": float(snap1.before.hamming_distance(snap2.before)),
            "after_dist": float(snap1.after.hamming_distance(snap2.after)),
            "triple_product": self.triple_distance(snap1, snap2),
        }

    # ═════════════════════════════════════════════════════════════════════
    # THREE COLUMN THINKING (a METHOD, not a system)
    # ═════════════════════════════════════════════════════════════════════

    def think_three_column(self, snap_result: SnapResult) -> Dict[str, str]:
        """Three Column Thinking on a snap result.

        The columns are:
          Language: describe the snap (before → after)
          Math: the syndrome tax and NRCI delta
          Script: the executable check
        """
        language = (f"Snap: {snap_result.before_int} → {snap_result.after_int} "
                    f"(tax={snap_result.syndrome_tax}, distance={snap_result.correction_distance})")
        math = (f"σ(before)={snap_result.before_syndrome_weight} → σ(after)={snap_result.after_syndrome_weight}, "
                f"NRCI: {snap_result.before_nrci:.4f} → {snap_result.after_nrci:.4f} (Δ={snap_result.nrci_delta:.4f})")
        script = (f"before={snap_result.before_int}; after={snap_result.after_int}; "
                  f"tax={snap_result.syndrome_tax}; correctable={snap_result.correctable}")

        return {"language": language, "math": math, "script": script}

    # ═════════════════════════════════════════════════════════════════════
    # ANALOGY (a METHOD — uses the triple product)
    # ═════════════════════════════════════════════════════════════════════

    def analogy(self, a: str, b: str, c: str, max_candidates: int = 500) -> Dict[str, Any]:
        """Analogy using the full snap triple: a:b :: c:?

        Per user: "extremely powerful and sometimes completely incorrect."

        Uses the triple product (tax × before × after) to find d such that
        the relation c→d best matches a→b. NO XOR — only lattice structure.
        """
        # Snap all three inputs
        snap_a = self.perceive(a)
        snap_b = self.perceive(b)
        snap_c = self.perceive(c)

        # The relation a→b as a triple-distance profile
        rel_ab = self.triple_compare(snap_a, snap_b)

        # Find d such that c→d has the most similar triple profile
        candidates = []
        for name, node in list(self.state.nodes.items())[:max_candidates]:
            if name in [a, b, c]:
                continue
            # Snap the candidate
            snap_d = self.snap_op.snap(node.data_object)
            rel_cd = self.triple_compare(snap_c, snap_d)

            # How similar are the two relations? (smaller diff = better match)
            # Compare each dimension of the profile
            tax_diff = abs(rel_ab["tax_diff"] - rel_cd["tax_diff"])
            before_diff = abs(rel_ab["before_dist"] - rel_cd["before_dist"])
            after_diff = abs(rel_ab["after_dist"] - rel_cd["after_dist"])
            total_profile_diff = tax_diff + before_diff + after_diff

            candidates.append({
                "name": name,
                "total_profile_diff": total_profile_diff,
                "triple_dist_cd": rel_cd["triple_product"],
                "rel_cd": rel_cd,
            })

        candidates.sort(key=lambda x: x["total_profile_diff"])

        return {
            "analogy": (a, b, c), "found": True,
            "relation_ab": rel_ab,
            "top_candidates": candidates[:5],
        }

    # ═════════════════════════════════════════════════════════════════════
    # STATUS
    # ═════════════════════════════════════════════════════════════════════

    def status(self) -> Dict[str, Any]:
        return {
            "mind_state": {
                "current_subject": self.mind_state.current_subject,
                "n_snaps": self.mind_state.n_snaps,
                "n_proposals": self.mind_state.n_proposals,
                "n_commits": self.mind_state.n_commits,
                "last_syndrome_tax": self.mind_state.last_syndrome_tax,
                "last_nrci": self.mind_state.last_nrci,
                "last_regime": self.mind_state.last_regime,
            },
            "body_state": self.state.stats(),
        }
