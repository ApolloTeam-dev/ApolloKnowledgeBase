#!/usr/bin/env python3
"""Check what ApolloCrossDev emitted for kb:compile snippets that carry
`kb:expect` or `kb:expect-not` lines (see CONTRIBUTING.md section 6).

Run after tools/compile-snippets.sh, which writes <name>.asm (the `-S` output
of a C or C++ snippet) or <name>.bin (the `-Fbin` output of an assembly
snippet) next to each snippet with expectations.

- C, C++: the text after `kb:expect` must occur in the assembly text; for
  `kb:expect-not` it must not. Runs of spaces and tabs count as one space.
- Assembly: the text is hex bytes (spaces allowed, `$` and `0x` ignored) that
  must, or must not, occur in the assembled bytes.

  check_emitted_code.py [dir]   default: build/snippets
"""
import os
import re
import sys

from kblib import ROOT

LINE_RE = re.compile(r"^\s*(?://|;)\s*kb:(expect|expect-not)\s+(.+?)\s*$")


def norm_text(s):
    return re.sub(r"[ \t]+", " ", s)


def norm_hex(s):
    h = re.sub(r"\$|0x|\s", "", s).lower()
    if not re.fullmatch(r"(?:[0-9a-f]{2})+", h):
        return None
    return h


def check(src, out_dir):
    with open(os.path.join(out_dir, src), encoding="utf-8") as f:
        rules = [m.groups() for m in map(LINE_RE.match, f) if m]
    if not rules:
        return 0, 0
    base, ext = os.path.splitext(src)
    is_asm = ext == ".s"
    out = os.path.join(out_dir, base + (".bin" if is_asm else ".asm"))
    if not os.path.exists(out):
        print(f"::error::{src}: no {os.path.basename(out)} (did it compile?)")
        return len(rules), len(rules)
    if is_asm:
        with open(out, "rb") as f:
            hay = f.read().hex()
    else:
        with open(out, encoding="utf-8") as f:
            hay = norm_text(f.read())
    failed = 0
    for kind, text in rules:
        if is_asm:
            needle = norm_hex(text)
            if needle is None:
                print(f"::error::{src}: kb:{kind} '{text}' is not hex bytes")
                failed += 1
                continue
            # Match on byte boundaries only.
            found = any(i % 2 == 0 for i in
                        (m.start() for m in re.finditer(f"(?={needle})", hay)))
        else:
            found = norm_text(text) in hay
        if found != (kind == "expect"):
            what = "missing" if kind == "expect" else "present"
            print(f"::error::{src}: kb:{kind} '{text}': {what} in "
                  f"{os.path.basename(out)}")
            failed += 1
    return len(rules), failed


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "build", "snippets")
    total = failed = files = 0
    for src in sorted(os.listdir(out_dir)):
        if os.path.splitext(src)[1] not in (".c", ".cpp", ".s"):
            continue
        n, bad = check(src, out_dir)
        if n:
            files += 1
            total += n
            failed += bad
    print(f"{total} expectation(s) in {files} snippet(s), {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
