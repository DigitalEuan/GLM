#!/usr/bin/env python3
"""Verify a Column-3 re-derivation script by running it in an isolated subprocess.
Usage: python3 verify_column3.py SCRIPT.py [--expect EXPECTED] [--timeout N] [--key K]
       python3 verify_column3.py --code "print(2+2)" [--expect 4]
Exit: 0=VERIFIED, 1=MISMATCH, 2=error/timeout.
"""
import argparse, subprocess, sys, tempfile, os

def last_meaningful_line(text):
    for line in reversed(text.splitlines()):
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("--code")
    ap.add_argument("--expect")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--key")
    args = ap.parse_args()
    if not args.script and not args.code:
        ap.error("provide a script path or --code")
    if args.code:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
        tmp.write(args.code); tmp.close()
        path, cleanup = tmp.name, True
    else:
        path, cleanup = os.path.abspath(args.script), False
    try:
        cwd = os.path.dirname(path) if not args.code else tempfile.gettempdir()
        proc = subprocess.run([sys.executable, path], capture_output=True,
                              text=True, timeout=args.timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        print(f"ERROR: timed out after {args.timeout}s"); return 2
    except OSError as e:
        print(f"ERROR: could not run: {e}"); return 2
    finally:
        if cleanup:
            try: os.unlink(path)
            except OSError: pass
    if proc.returncode != 0:
        print(f"ERROR: exit code {proc.returncode}")
        if proc.stderr: print(proc.stderr.strip())
        return 2
    out = proc.stdout.strip()
    if args.key:
        actual = None
        for line in out.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                if k.strip() == args.key:
                    actual = v.strip(); break
        if actual is None:
            print(f"ERROR: no key '{args.key}'"); print(out); return 2
    else:
        actual = last_meaningful_line(out)
    if args.expect is None:
        print("OUTPUT:"); print(out); print(f"FINAL: {actual!r}"); return 0
    expected = args.expect.strip()
    if actual == expected:
        print(f"VERIFIED: {actual!r} == {expected!r}"); return 0
    print(f"MISMATCH: {actual!r} != {expected!r}"); print(out); return 1

if __name__ == "__main__":
    sys.exit(main())
