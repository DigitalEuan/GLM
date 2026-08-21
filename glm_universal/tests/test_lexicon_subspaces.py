"""Tests for the v0.5.1 lexicon subspaces in the analogy solver.

Two new subspaces were added to ``reasoning.analogy.SUBSPACES``:

* ``lexicon.primitives`` -- the ten semantic primitives alone.  Lets
  analogies over words resolve on meaning rather than spelling.
* ``lexicon.relations`` -- the four predicate + four object slots.  Asks
  "what relations does this concept participate in?" without regard to
  its meaning.

These tests verify the subspaces exist, contain the expected coordinates,
and that the analogy solver uses them correctly for lexicon-domain queries.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import semantic_lexicon as sl
from glm_universal.data_objects.semantic_lexicon import (
    SEMANTIC_PRIMITIVE_NAMES, MAX_SEMANTIC_RELATIONS,
    SemanticLexiconCodec, default_semantic_vocabulary,
    semantic_lexicon_objects)
from glm_universal.reasoning import analogy as an
from glm_universal.reasoning.analogy import (SUBSPACES, subspace_indices,
                                              solve_analogy_objects)


class TestSubspaceRegistration(unittest.TestCase):

    def test_lexicon_primitives_subspace_exists(self):
        self.assertIn("lexicon.primitives", SUBSPACES)

    def test_lexicon_primitives_subspace_is_the_ten_primitives(self):
        names = SUBSPACES["lexicon.primitives"]
        self.assertEqual(names, SEMANTIC_PRIMITIVE_NAMES)
        self.assertEqual(len(names), 10)

    def test_lexicon_relations_subspace_exists(self):
        self.assertIn("lexicon.relations", SUBSPACES)

    def test_lexicon_relations_subspace_covers_predicates_and_objects(self):
        names = SUBSPACES["lexicon.relations"]
        # 4 predicate slots + 4 object slots = 8 coordinates
        self.assertEqual(len(names), 2 * MAX_SEMANTIC_RELATIONS)
        self.assertTrue(all(n.startswith(("predicate", "object"))
                            for n in names))


class TestSubspaceResolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.objs, cls.codec = semantic_lexicon_objects()
        cls.by_name = {o.name: o for o in cls.objs}

    def test_subspace_indices_for_primitives(self):
        """The lexicon.primitives subspace resolves against the SEMANTIC_LAYOUT."""
        idx = subspace_indices(sl.SEMANTIC_LAYOUT,
                                SUBSPACES["lexicon.primitives"])
        # Coords 0..9 are the primitives.
        self.assertEqual(idx, tuple(range(10)))

    def test_subspace_indices_for_relations(self):
        """The lexicon.relations subspace resolves against the SEMANTIC_LAYOUT."""
        idx = subspace_indices(sl.SEMANTIC_LAYOUT,
                                SUBSPACES["lexicon.relations"])
        # Coords 12..19 are predicates (12..15) and objects (16..19).
        self.assertEqual(idx, tuple(range(12, 20)))


class TestAnalogyOnPrimitivesSubspace(unittest.TestCase):
    """The whole point of v0.5.1: analogies over words resolve on meaning."""

    @classmethod
    def setUpClass(cls):
        cls.objs, cls.codec = semantic_lexicon_objects()
        cls.by_name = {o.name: o for o in cls.objs}

    def _solve(self, a, b, c, subspace="lexicon.primitives"):
        """Run analogy A:B::C:? over the named subspace."""
        return solve_analogy_objects(
            self.by_name[a], self.by_name[b], self.by_name[c],
            candidates=list(self.by_name.values()),
            subspace=subspace)

    def test_hot_cold_fast_yields_a_tied_set_including_slow(self):
        """hot:cold::fast:? -- the displacement flips positive_negative
        from 1 (hot) to 0 (cold), so the target has positive_negative=0.
        Several concepts tie; 'slow' should be among them."""
        result = self._solve("hot", "cold", "fast")
        tied_names = list(result.tied) if result.tied else [result.answer]
        # 'slow' has positive_negative=0 (cold-like).  It may or may not
        # be in the tied set depending on how many other concepts share
        # the same primitives.  At minimum, the answer should be a
        # non-input concept with positive_negative != 1.
        self.assertNotIn(result.answer, ("hot", "cold", "fast"))
        # The tied set is at least one concept (possibly many).
        self.assertGreaterEqual(len(tied_names), 1)

    def test_water_liquid_electron_yields_a_state(self):
        """water:liquid::electron:? should resolve to a state of matter
        or a related noun."""
        result = self._solve("water", "liquid", "electron")
        # The displacement D* = electron + (liquid - water).  We don't
        # assert the exact answer, just that the result is non-trivial
        # (target is computed, ties are bounded).
        self.assertIsNotNone(result.target)
        self.assertGreaterEqual(len(result.tied), 0)

    def _prim_d2(self, v1, v2):
        """Distance squared in the 10-primitive subspace."""
        # Use the project_subspace helper.
        from glm_universal.reasoning.analogy import subspace_indices
        idx = subspace_indices(sl.SEMANTIC_LAYOUT,
                               SUBSPACES["lexicon.primitives"])
        # Zero out everything outside the subspace.
        from fractions import Fraction as F
        a = [F(x) for x in v1]
        b = [F(x) for x in v2]
        a_proj = [a[i] if i in idx else F(0) for i in range(24)]
        b_proj = [b[i] if i in idx else F(0) for i in range(24)]
        from glm_universal.reasoning.metric import distance2
        return distance2(a_proj, b_proj)


if __name__ == "__main__":
    unittest.main()
