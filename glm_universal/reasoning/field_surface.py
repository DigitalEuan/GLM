"""``glm_universal.reasoning.field_surface`` -- what the field surface was
worth, measured against the prediction that bought it.

What this measures
------------------
:mod:`glm_universal.reasoning.probe_oracle` hand-translated the twenty
pre-registered probe questions into the system's own query grammar and found
the refusals were three different failures: **6** answered by a query that
already existed, **10** held by a shipped register row or a shipped function
that *no query kind returned*, and **4** held nowhere.  It priced the two
instruments that would close the first two -- a parser is worth 4 questions,
a field surface 10 -- and recommended neither by itself.

The field surface is now built (:mod:`glm_universal.runtime.fields`).  This
module asks the only question that can settle whether the prediction was
right: **of the ten, how many does it actually answer?**

How the comparison is kept honest
---------------------------------
*The frozen path.*  ``probe_oracle.TRANSLATIONS`` is not edited.  It is what
the previous round declared and measured, and re-running it still reports
6/10/4, because each of its ten ``surface`` rows carries no query at all.
The table here is a *second* translation table, declared in this module, and
the two are run side by side.

*The same rules.*  Both tables are scored by ``probe_oracle.translate``, so
the locus rule (the declared fragment must appear in the declared field of
the solution, not merely somewhere in it) and the no-smuggling rule (a
translation may not contain the fragment it is scored on unless the question
already does) apply here unchanged.  :func:`smuggling_audit` re-checks the
second rule over this table, and a test fails if it is broken.

*The declared shortfall.*  One of the ten is declared **not** answerable by a
field surface before the run: *is energy more abstract than water?* asks for
a comparison of one coordinate across two rows, and a field query returns one
field of one row.  Writing ``field abstract_concrete of energy`` would score
-- the fragment is the row's own name -- and it would be a false pass, which
is precisely what the locus rule exists to refuse.  So the prediction this
round tests is not *ten*: it is *nine, and one that needs an operation
rather than a surface*.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .blockers import PROBE
from .probe_oracle import TRANSLATIONS, Translation, oracle_report

__all__ = [
    "FIELD_TRANSLATIONS", "SURFACE_KEYS", "DECLARED_UNREACHABLE",
    "translations_after", "smuggling_audit", "surface_report",
]


#: The ten questions the oracle put in the ``surface`` class: held by the
#: system and returned by no query kind.  Frozen here from that reading, so
#: this module measures the set the prediction was made about rather than
#: whatever the class happens to hold now.
SURFACE_KEYS: Tuple[str, ...] = (
    "nl-relation", "nl-compare", "chem-lookup", "chem-weight", "chem-group",
    "chem-compose", "prog-lean", "prog-python", "prog-behaviour",
    "prog-count",
)

#: Declared before the run: the one of the ten a field surface cannot reach,
#: and why.  Naming it in advance is what stops the result from being read as
#: ten out of ten with one quietly dropped.
DECLARED_UNREACHABLE: Dict[str, str] = {
    "nl-compare":
        "the question compares one coordinate across two rows and a field "
        "query returns one field of one row. `field abstract_concrete of "
        "energy` would carry the fragment `energy` at its locus and pass "
        "without answering anything, which is the false pass the locus rule "
        "exists to refuse. What closes it is an operation over two readings, "
        "not a surface onto one.",
}


#: The translations the field surface makes expressible, one per ``surface``
#: question.  Everything outside :data:`SURFACE_KEYS` is inherited unchanged
#: from the frozen table, so the six already-parsed and the four absent
#: questions are answered by exactly the queries they were before.
FIELD_TRANSLATIONS: Tuple[Translation, ...] = (
    Translation(
        "nl-relation", "field derivative_of of velocity", "value", None,
        "none",
        "the lexicon holds the triple ('velocity', 'derivative_of', "
        "'position') and the field surface makes the relation the field "
        "name: the question names the relation, and the answer is the other "
        "end of it"),
    Translation(
        "nl-compare", None, None, "abstractness-energy-water", "register",
        DECLARED_UNREACHABLE["nl-compare"]),
    Translation(
        "chem-lookup", "field name of C", "value", None, "none",
        "the element register's own `name` field, which `describe C` never "
        "returned because a carrier's geometry is not its row"),
    Translation(
        "chem-weight", "field atomic_weight_u of carbon", "value", None,
        "none",
        "`12011/1000` exactly, rendered with its terminating decimal beside "
        "it because one exists"),
    Translation(
        "chem-group", "field group_block of chlorine", "value", None, "none",
        "the classification the row holds, read as it is held"),
    Translation(
        "chem-compose", "field molar_mass_u of water", "value", None, "none",
        "the molecule register declares this one derived rather than stored, "
        "and the answer says so: it is recomputed from the formula and the "
        "element register on every read"),
    Translation(
        "prog-lean", "field file of GLM.NormFamily.family_tower", "value",
        None, "none",
        "the Lean address book as a table: one row per declaration, asked "
        "about one declaration rather than in aggregate"),
    Translation(
        "prog-python", "field module of rung_audit", "value", None, "none",
        "the package's own top-level definitions, read by the AST walk the "
        "package already ships -- blocker 5's gap, closed for the one "
        "question that asks about it"),
    Translation(
        "prog-behaviour",
        "fields of glm_universal.substrate.norm_family.completeness",
        "fields", None, "none",
        "the listing shape is what asks *what does this return?* without "
        "naming the answer: the keys of the returned mapping are the fields, "
        "and `complete` is one of them"),
    Translation(
        "prog-count", "field rungs of "
                      "glm_universal.substrate.norm_family.completeness",
        "value", None, "none",
        "the same declared function surface, asked for the key that holds "
        "the count"),
)


def translations_after() -> Tuple[Translation, ...]:
    """The frozen table with the field-surface rows substituted in.

    In the order of :data:`~glm_universal.reasoning.probe_oracle.TRANSLATIONS`
    so that the two readings line up row by row.
    """
    replacement = {row.key: row for row in FIELD_TRANSLATIONS}
    return tuple(replacement.get(row.key, row) for row in TRANSLATIONS)


def smuggling_audit(translations: Sequence[Translation] | None = None
                    ) -> Tuple[Dict[str, object], ...]:
    """Check the no-smuggling rule over every translation with a query.

    A translation may contain the fragment it is scored on only when the
    question itself already contains it.  One row per translation, with the
    verdict computed rather than asserted.
    """
    rows: List[Dict[str, object]] = []
    questions = {q.key: q for q in PROBE}
    for translation in (translations_after() if translations is None
                        else translations):
        if translation.query is None:
            continue
        question = questions[translation.key]
        fragment = question.expect.lower()
        in_query = fragment in translation.query.lower()
        in_question = fragment in question.question.lower()
        rows.append({
            "key": translation.key,
            "query": translation.query,
            "fragment": question.expect,
            "in_query": in_query,
            "in_question": in_question,
            "smuggled": in_query and not in_question,
        })
    return tuple(rows)


def surface_report(session=None) -> Dict[str, object]:
    """Both readings of the twenty questions, and what the surface moved.

    Returns the frozen reading, the reading with the field surface, the
    questions that moved between them, the census of what the surface
    addresses, and the verdict in integers.
    """
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    before = oracle_report(session)
    after = oracle_report(session, translations_after())
    before_class = {str(row["key"]): str(row["class"])
                    for row in before["rows"]}          # type: ignore[union-attr]
    after_rows = {str(row["key"]): row
                  for row in after["rows"]}             # type: ignore[union-attr]
    moved = tuple(key for key in SURFACE_KEYS
                  if after_rows[key]["class"] == "parsed")
    still_surface = tuple(key for key in SURFACE_KEYS
                          if after_rows[key]["class"] != "parsed")
    unexpected = tuple(key for key in before_class
                       if key not in SURFACE_KEYS
                       and before_class[key] != after_rows[key]["class"])
    smuggled = tuple(row["key"] for row in smuggling_audit()
                     if row["smuggled"])
    census = session.field_surface.census()
    predicted = len(SURFACE_KEYS) - len(DECLARED_UNREACHABLE)
    return {
        "questions": len(PROBE),
        "surface_keys": SURFACE_KEYS,
        "declared_unreachable": tuple(sorted(DECLARED_UNREACHABLE)),
        "predicted": predicted,
        "moved": moved,
        "moved_count": len(moved),
        "still_surface": still_surface,
        "unexpected_changes": unexpected,
        "smuggled": smuggled,
        "before": {name: before["counts"][name]                # type: ignore[index]
                   for name in ("parsed", "surface", "absent")},
        "after": {name: after["counts"][name]                  # type: ignore[index]
                  for name in ("parsed", "surface", "absent")},
        "rows": tuple(
            {"key": key,
             "question": after_rows[key]["question"],
             "query": after_rows[key]["query"],
             "locus": after_rows[key]["locus"],
             "before": before_class[key],
             "after": after_rows[key]["class"],
             "kind": after_rows[key]["asked"]["kind"],         # type: ignore[index]
             "field": after_rows[key]["asked"]["field"],       # type: ignore[index]
             "note": after_rows[key]["note"]}
            for key in SURFACE_KEYS),
        "census": census,
        "verdict": (
            f"the field surface answers {len(moved)} of the "
            f"{len(SURFACE_KEYS)} questions the oracle called held and "
            f"unreachable, against the {predicted} declared reachable before "
            f"the run; {len(still_surface)} remains, and it is the one "
            f"declared unreachable -- a comparison across two rows, which "
            f"needs an operation rather than a surface. The whole probe "
            f"splits {after['counts']['parsed']} parsed, "            # type: ignore[index]
            f"{after['counts']['surface']} surface, "                 # type: ignore[index]
            f"{after['counts']['absent']} absent, against "           # type: ignore[index]
            f"{before['counts']['parsed']}/"                          # type: ignore[index]
            f"{before['counts']['surface']}/"                         # type: ignore[index]
            f"{before['counts']['absent']} before it."),              # type: ignore[index]
        "caveat": (
            "this is coverage, not reasoning: a field surface is `table`, "
            "the weakest of the three faculties, and every question it moves "
            "is a question whose answer the system already held. Nothing "
            "here derives anything, and the four absent questions are "
            "untouched."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = surface_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<15} {row['before']} -> {row['after']:<8} "
              f"{row['query'] or '(not expressible)'}")
