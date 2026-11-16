"""``glm_universal.corpus.lean_deliveries`` -- what a supplied Lean delivery
would add to the build tree, measured from the text.

*Created 15 November 2026 (platform round, P4 intake; Phase 189).*

The owner's rule for `source_material/ToDo/lean_to_add` is that it is absorbed
"only if the main Lean folder does not already hold it", and a file name cannot
answer that: the upload of 12 November 2026 placed byte-identical files beside
their own copies and different files under the same names.  :func:`census_report`
answers it with four measurements over every `.lean` file of an intake item,
parsed by :func:`glm_universal.lean_check.parse_file` so that this census and the
tree checker cannot disagree about what a file declares:

* **identity** -- the file's SHA-256 against every built file's, wherever the
  tree's copy sits;
* **name** -- the same basename in the tree with different content, which is a
  pair a reader must diff before a port;
* **declaration names** -- how many of the file's fully qualified names the tree
  already declares (a name comparison, not a semantics comparison: a file whose
  declarations differ only by namespace counts as new);
* **imports** -- the file's own module imports, and whether they resolve against
  the tree's module names as written.  A delivery rooted at `RequestProject.*`
  while the tree's modules are all `RequestProject.GLM.*` resolves none, and
  that is the difference between "copy it in" and "port it".

It also reports the supplied files against *each other*, because the same
delivery was uploaded twice in places.

It reads `source_material/` and `src/lean/` and writes nothing.  The study that
uses it is `studies/LEAN_DELIVERIES_CENSUS_STUDY.md`; the runner is
`studies/scripts/lean_to_add_census.py`.

Command line (from the repository root)::

    PYTHONPATH=src python3 -m glm_universal.corpus.lean_deliveries
    PYTHONPATH=src python3 -m glm_universal.corpus.lean_deliveries --json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ..constants import LEAN_LIBRARY, LEAN_SOURCE_DIR, REPOSITORY_ROOT, SOURCE_MATERIAL_DIR
from ..lean_check import parse_file

__all__ = ["ITEMS", "census_report", "format_report", "main"]

#: The intake items this census was written for.  It works for any folder in
#: `source_material/ToDo/`, and names these two because they are the pair the
#: study measures.
ITEMS = ("lean_to_add", "leechlean")

#: An import is *item-local* when it names a module of the delivery rather than
#: a library (`Mathlib`, `Lean`, `Std`, `Init`, `Aesop`).
LOCAL_ROOTS = ("RequestProject.", "FirstPrinciples.", "Projection.")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree() -> Dict[str, object]:
    """Every built Lean file, by SHA-256, basename, module name and declaration."""
    root = LEAN_SOURCE_DIR / LEAN_LIBRARY
    by_hash: Dict[str, List[Path]] = {}
    by_name: Dict[str, List[Path]] = collections.defaultdict(list)
    decls: set = set()
    modules: set = set()
    for path in sorted(root.rglob("*.lean")):
        parsed = parse_file(path, root=LEAN_SOURCE_DIR)
        by_hash.setdefault(_sha(path), []).append(path)
        by_name[path.name].append(path)
        modules.add(parsed.module)
        decls.update(parsed.declarations)
    return {"by_hash": by_hash, "by_name": by_name, "decls": decls,
            "modules": modules, "count": sum(len(v) for v in by_name.values())}


def _item_local(name: str) -> bool:
    return name.startswith(LOCAL_ROOTS)


def _sub_project(relative: str) -> str:
    parts = Path(relative).parts
    return parts[1] if len(parts) > 2 else "(top)"


def _row(path: Path, base: Path, tree: Dict[str, object]) -> Dict[str, object]:
    parsed = parse_file(path, root=base)
    digest = _sha(path)
    same = tree["by_hash"].get(digest, [])
    named = tree["by_name"].get(path.name, [])
    known = sum(1 for d in parsed.declarations if d in tree["decls"])
    return {
        "item": path.relative_to(SOURCE_MATERIAL_DIR / "ToDo").parts[0],
        "path": str(path.relative_to(SOURCE_MATERIAL_DIR / "ToDo")),
        "sha256": digest,
        "module": parsed.module,
        "declarations": len(parsed.declarations),
        "decls_already_in_tree": known,
        "decls_new": len(parsed.declarations) - known,
        "sorry": len(parsed.sorry_lines),
        "imports": [name for name, _ in parsed.imports],
        "import_roots": sorted({name.split(".")[0] for name, _ in parsed.imports}),
        "identical_to": [str(p.relative_to(REPOSITORY_ROOT)) for p in same],
        "same_name_as": [str(p.relative_to(REPOSITORY_ROOT)) for p in named],
        "verdict": "identical" if same else "name" if named else "new",
    }


def census_report(items: Iterable[str] = ITEMS) -> Dict[str, object]:
    """The census: per file, per sub-project, per item, and against each other."""
    tree = _tree()
    rows: List[Dict[str, object]] = []
    for item in items:
        base = SOURCE_MATERIAL_DIR / "ToDo" / item
        if not base.is_dir():          # absorbed or closed since the study
            continue
        for path in sorted(base.rglob("*.lean")):
            rows.append(_row(path, base, tree))

    by_hash: Dict[str, List[str]] = collections.defaultdict(list)
    for row in rows:
        by_hash[row["sha256"]].append(row["path"])
    for row in rows:
        row["same_as_supplied"] = [p for p in by_hash[row["sha256"]]
                                   if p != row["path"]]

    groups: Dict[Tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter)
    for row in rows:
        group = groups[(row["item"], _sub_project(row["path"]))]
        group["files"] += 1
        group["declarations"] += row["declarations"]
        group["decls_new"] += row["decls_new"]
        group["identical"] += row["verdict"] == "identical"
        group["same_name"] += row["verdict"] == "name"
        group["new"] += row["verdict"] == "new"
        group["sorry"] += row["sorry"]
        group["dup_within"] += bool(row["same_as_supplied"])
        for root in row["import_roots"]:
            group["root:" + root] += 1
        group["local_imports"] += sum(1 for n in row["imports"] if _item_local(n))
        group["local_imports_resolved"] += sum(
            1 for n in row["imports"]
            if _item_local(n) and n in tree["modules"])

    unresolved: collections.Counter = collections.Counter()
    for row in rows:
        for name in row["imports"]:
            if _item_local(name) and name not in tree["modules"]:
                unresolved[name] += 1

    report: Dict[str, object] = {
        "tree_files": tree["count"],
        "tree_declarations": len(tree["decls"]),
        "tree_modules": len(tree["modules"]),
        "rows": rows,
        "groups": [{"item": i, "sub_project": s, **dict(g)}
                   for (i, s), g in sorted(groups.items())],
        "items": {},
        "unresolved_imports": dict(unresolved),
        "item_local_imports": sum(g["local_imports"] for g in groups.values()),
        "item_local_imports_resolved":
            sum(g["local_imports_resolved"] for g in groups.values()),
    }
    for item in items:
        subset = [r for r in rows if r["item"] == item]
        if not subset:
            continue
        report["items"][item] = {
            "files": len(subset),
            "declarations": sum(r["declarations"] for r in subset),
            "identical": sum(r["verdict"] == "identical" for r in subset),
            "same_name": sum(r["verdict"] == "name" for r in subset),
            "new": sum(r["verdict"] == "new" for r in subset),
            "decls_new": sum(r["decls_new"] for r in subset),
            "sorry": sum(r["sorry"] for r in subset),
        }
    return report


def format_report(report: Dict[str, object]) -> str:
    """The census as the study quotes it."""
    out: List[str] = []
    out.append(f"build tree: {report['tree_files']} Lean files, "
               f"{report['tree_declarations']} distinct declaration names")
    out.append("")
    out.append(f"{'item / sub-project':42s} {'files':>5s} {'decls':>6s} {'new':>5s} "
               f"{'ident':>5s} {'name':>4s} {'new':>4s} {'dup':>4s} {'sorry':>5s}  imports")
    for g in report["groups"]:
        roots = []
        for key in g:
            if key.startswith("root:"):
                roots.append(key.split(":", 1)[1])
        out.append(f"{g['item'] + '/' + g['sub_project']:42s} {g['files']:5d} "
                   f"{g['declarations']:6d} {g['decls_new']:5d} {g['identical']:5d} "
                   f"{g['same_name']:4d} {g['new']:4d} {g['dup_within']:4d} "
                   f"{g['sorry']:5d}  {','.join(sorted(roots))}")
    out.append("")
    for item, stats in report["items"].items():
        out.append(
            f"{item}: {stats['files']} files, {stats['declarations']} declarations, "
            f"{stats['decls_new']} names the tree does not declare, "
            f"{stats['identical']} byte-identical to the tree, "
            f"{stats['same_name']} share a name with a different tree file, "
            f"{stats['new']} new names, {stats['sorry']} 'sorry'.")
    out.append("")
    local = report["item_local_imports"]
    resolved = report["item_local_imports_resolved"]
    out.append(f"item-local imports: {local}, resolving against the tree's module "
               f"names as written: {resolved}, not resolving: {local - resolved}")
    if report["unresolved_imports"]:
        names = sorted(report["unresolved_imports"])
        out.append(f"  {len(names)} distinct unresolved module names, "
                   f"e.g. {', '.join(names[:6])}")
    out.append("")
    out.append("supplied files that exist twice in the supplied material:")
    seen: set = set()
    for row in report["rows"]:
        if row["same_as_supplied"] and row["path"] not in seen:
            seen.add(row["path"])
            seen.update(row["same_as_supplied"])
            out.append("  " + "  ==  ".join([row["path"]] + row["same_as_supplied"]))
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--items", nargs="*", default=list(ITEMS),
                        help="intake items under source_material/ToDo/ to census")
    args = parser.parse_args(argv)
    report = census_report(args.items)
    if args.json:
        print(json.dumps(report, indent=1))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
