#!/usr/bin/env python3
"""Check that relative markdown links in all .md files point to existing
files. External links (http, https, mailto) and pure anchors are skipped."""
import os
import re

from kblib import ROOT, report

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.DOTALL | re.MULTILINE)
SKIP_DIRS = {".git", "node_modules", "seed"}


def md_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.relpath(os.path.join(dirpath, name), ROOT)


def main():
    errors = []
    for path in sorted(md_files()):
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            text = FENCE_RE.sub("", f.read())
        for target in LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target) or "<" in target:
                continue
            target = target.split("#")[0]
            full = os.path.normpath(
                os.path.join(ROOT, os.path.dirname(path), target))
            if not os.path.exists(full):
                errors.append((path, f"broken link '{target}'"))
    report(errors)


if __name__ == "__main__":
    main()
