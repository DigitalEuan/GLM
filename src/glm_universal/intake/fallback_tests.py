"""``python3 -m glm_universal.intake.fallback_tests <test file>`` -- run one
package test file where pytest is not installed, without ever passing a test
that did not run.

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 31 October 2026: ``teardown_class`` is run once after its
class's tests, the module and function hooks are honoured, inherited test
methods are collected, and a failing setup or teardown hook fails the file.*

The intake runs a named package test (``tests/test_x.py``, ``staged:...``)
with pytest when pytest is installed.  Without it, ``python3 -m unittest``
would be wrong for most of the package's test files: it collects only
``unittest.TestCase`` methods, so a file of pytest-style test functions
"passes" having run nothing.  This runner collects what it can run faithfully
and refuses the rest:

* ``unittest.TestCase`` classes, through the standard loader;
* module-level ``test*`` functions defined in the file, called with no
  argument;
* pytest-style ``Test*`` classes (not ``TestCase``) defined in the file: each
  ``test*`` method (inherited ones included) called on a fresh instance, with
  ``setup_class`` once before the first, ``setup_method`` /
  ``teardown_method`` around each and ``teardown_class`` once after the last;
* the module hooks ``setup_module`` / ``teardown_module`` and
  ``setup_function`` / ``teardown_function`` around the plain tests.

A setup or teardown hook that raises fails the file, exactly as a failing
test does (a failing ``setup_class`` fails every test of its class, a
failing ``setup_module`` every plain test): a check placed in a teardown is
never skipped and never passed over.

A test function or method that takes an argument (a pytest fixture or a
``parametrize`` value) cannot be run without pytest: the file is then an
**error** (exit 2), never a pass, and the message says to install pytest.  A
file that imports pytest fails to import here and is an error too.  A file
in which nothing is collected exits 5 (pytest's "no tests collected"), and a
file with any failing or erroring test exits 1, and one whose every
collected test was skipped exits 5 (nothing was checked).  A file exits 0
only when every collected test ran and passed or was skipped, and at least
one ran.  The closing line gives the counts; the intake reads the exit code
and those counts and records them in its own words (it never copies output).
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
import unittest
from pathlib import Path
from typing import Callable, List, Tuple

__all__ = ["collect", "run_file", "main"]

#: Exit codes (pytest's where they mean the same thing).
EXIT_OK, EXIT_FAILED, EXIT_ERROR, EXIT_NO_TESTS = 0, 1, 2, 5


def _load(path: Path):
    """Import the test file as a module of its own (its folder on the path)."""
    folder = str(path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location(f"_glm_fallback_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _needs_arguments(fn: Callable, bound: bool) -> List[str]:
    """The parameters a test would need from pytest (``self`` excluded)."""
    params = list(inspect.signature(fn).parameters.values())
    if bound and params:
        params = params[1:]
    return [p.name for p in params
            if p.default is inspect.Parameter.empty
            and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)]


class _Group:
    """The ``test*`` methods of one pytest-style ``Test*`` class, run as pytest
    runs them: ``setup_class`` once before the first, a fresh instance with
    ``setup_method`` / ``teardown_method`` around each, ``teardown_class``
    once after the last."""

    def __init__(self, cls, methods: List[str]) -> None:
        self.cls = cls
        self.methods = methods

    def names(self) -> List[str]:
        return [f"{self.cls.__name__}.{m}" for m in self.methods]


def _test_methods(cls) -> List[str]:
    """``test*`` methods of ``cls``, inherited ones included (as pytest
    collects them), in name order."""
    return sorted(name for name, _ in inspect.getmembers(cls, inspect.isfunction)
                  if name.startswith("test"))


def collect(module) -> Tuple[unittest.TestSuite, List[Tuple[str, Callable[[], None]]],
                             List[str], List[_Group]]:
    """``(suite, plain, unrunnable, groups)``: the ``TestCase`` tests, the
    module-level test functions (name, function), the names of tests that
    need pytest, and the pytest-style classes with their test methods."""
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    plain: List[Tuple[str, Callable[[], None]]] = []
    unrunnable: List[str] = []
    groups: List[_Group] = []
    for name, obj in sorted(vars(module).items()):
        if getattr(obj, "__module__", None) != module.__name__:
            continue  # imported, not defined here
        if getattr(obj, "__test__", True) is False:
            continue  # pytest's opt-out
        if inspect.isfunction(obj) and name.startswith("test"):
            need = _needs_arguments(obj, bound=False)
            if need:
                unrunnable.append(f"{name}({', '.join(need)})")
            else:
                plain.append((name, obj))
        elif (inspect.isclass(obj) and name.startswith("Test")
              and not issubclass(obj, unittest.TestCase)):
            runnable: List[str] = []
            for m in _test_methods(obj):
                need = _needs_arguments(getattr(obj, m), bound=True)
                if need:
                    unrunnable.append(f"{name}.{m}({', '.join(need)})")
                else:
                    runnable.append(m)
            if runnable:
                groups.append(_Group(obj, runnable))
    return suite, plain, unrunnable, groups


def _call_hook(target, hook: str, *args) -> None:
    """Call ``target.<hook>`` if it exists, with ``args`` when it takes them.
    Whatever the hook raises propagates: a failing setup or teardown is a
    failure of the file, never a pass."""
    fn = getattr(target, hook, None)
    if fn is None:
        return
    try:
        params = [p for p in inspect.signature(fn).parameters.values()
                  if p.default is inspect.Parameter.empty
                  and p.kind not in (inspect.Parameter.VAR_POSITIONAL,
                                     inspect.Parameter.VAR_KEYWORD)]
    except (TypeError, ValueError):
        params = list(args)
    fn(*args[:len(params)])


class _Tally:
    def __init__(self, out) -> None:
        self.out = out
        self.passed = self.failed = self.skipped = self.hook_failures = 0

    def run(self, name: str, thunk: Callable[[], None]) -> None:
        try:
            thunk()
        except unittest.SkipTest:
            self.skipped += 1
        except Exception:
            self.failed += 1
            print(f"FAIL: {name}", file=self.out)
            traceback.print_exc(file=self.out)
        else:
            self.passed += 1

    def hook(self, label: str, target, hook: str, *args) -> bool:
        """Run a setup or teardown hook; a failure is counted against the file."""
        try:
            _call_hook(target, hook, *args)
        except unittest.SkipTest:
            raise
        except Exception:
            self.failed += 1
            self.hook_failures += 1
            print(f"ERROR: {label}", file=self.out)
            traceback.print_exc(file=self.out)
            return False
        return True


def _run_function(tally: _Tally, module, name: str, fn: Callable[[], None]) -> None:
    def thunk() -> None:
        _call_hook(module, "setup_function", fn)
        try:
            fn()
        finally:
            _call_hook(module, "teardown_function", fn)
    tally.run(name, thunk)


def _run_group(tally: _Tally, group: _Group) -> None:
    cls = group.cls
    try:
        set_up = tally.hook(f"{cls.__name__}.setup_class", cls, "setup_class", cls)
    except unittest.SkipTest:
        tally.skipped += len(group.methods)
        return
    if not set_up:
        # pytest reports every test of the class as an error; none ran.
        tally.failed += len(group.methods)
        return
    for method, name in zip(group.methods, group.names()):
        def thunk(method: str = method) -> None:
            inst = cls()
            bound = getattr(inst, method)
            _call_hook(inst, "setup_method", bound)
            try:
                bound()
            finally:
                _call_hook(inst, "teardown_method", bound)
        tally.run(name, thunk)
    tally.hook(f"{cls.__name__}.teardown_class", cls, "teardown_class", cls)


def run_file(path: Path, stream=None) -> int:
    """Run one test file; print the outcome; return the exit code."""
    out = stream or sys.stdout
    try:
        module = _load(path)
    except Exception as exc:  # the file does not import (pytest among the causes)
        traceback.print_exc(file=out)
        hint = " (install pytest)" if "pytest" in str(exc) else ""
        print(f"error: {path.name} does not import here: {exc}{hint}", file=out)
        return EXIT_ERROR
    suite, plain, unrunnable, groups = collect(module)
    if unrunnable:
        print(f"error: {len(unrunnable)} test(s) in {path.name} need pytest (fixtures or "
              f"parameters): {', '.join(unrunnable[:5])}" + (" ..." if len(unrunnable) > 5 else "")
              + " -- install pytest; nothing is counted as passed", file=out)
        return EXIT_ERROR
    total = suite.countTestCases() + len(plain) + sum(len(g.methods) for g in groups)
    if total == 0:
        print(f"no tests collected in {path.name}", file=out)
        return EXIT_NO_TESTS
    tally = _Tally(out)
    if suite.countTestCases():
        result = unittest.TextTestRunner(stream=out, verbosity=1).run(suite)
        # unittest counts a failing setUpClass / tearDownClass / module hook
        # among its errors, so it fails the file here as well.
        failed = len(result.failures) + len(result.errors)
        tally.failed += failed
        tally.skipped += len(result.skipped)
        tally.passed += max(result.testsRun - failed - len(result.skipped), 0)
    if plain or groups:
        try:
            module_set_up = tally.hook("setup_module", module, "setup_module", module)
        except unittest.SkipTest:
            tally.skipped += len(plain) + sum(len(g.methods) for g in groups)
            module_set_up = None
        if module_set_up:
            for name, fn in plain:
                _run_function(tally, module, name, fn)
            for group in groups:
                _run_group(tally, group)
            tally.hook("teardown_module", module, "teardown_module", module)
        elif module_set_up is False:
            tally.failed += len(plain) + sum(len(g.methods) for g in groups)
    hooks = (f" (including {tally.hook_failures} failing setup/teardown hook(s))"
             if tally.hook_failures else "")
    print(f"{tally.passed} passed, {tally.failed} failed{hooks}, {tally.skipped} skipped "
          f"of {total} collected in {path.name} (without pytest)", file=out)
    if tally.failed:
        return EXIT_FAILED
    if tally.passed == 0:
        print(f"no test ran in {path.name}: every collected test was skipped", file=out)
        return EXIT_NO_TESTS
    return EXIT_OK


def main(argv: List[str] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python3 -m glm_universal.intake.fallback_tests <test file>", file=sys.stderr)
        return EXIT_ERROR
    path = Path(args[0]).resolve()
    if not path.is_file():
        print(f"error: {path} does not exist", file=sys.stderr)
        return EXIT_ERROR
    return run_file(path)


if __name__ == "__main__":
    sys.exit(main())
