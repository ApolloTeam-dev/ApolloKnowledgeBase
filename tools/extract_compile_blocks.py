#!/usr/bin/env python3
"""Extract all code blocks marked `kb:compile` into build/snippets/ so CI can
compile them with ApolloCrossDev (see tools/compile-snippets.sh).

A block is compiled when its first line is `; kb:compile` (assembly) or
`// kb:compile` (C, C++). Output names: <file-path-with-dashes>-<n>.<ext>"""
import os
import re
import shutil

from kblib import ROOT, content_files, read

BLOCK_RE = re.compile(r"^```(\w+)\n(.*?)^```", re.DOTALL | re.MULTILINE)
EXT = {"c": "c", "cpp": "cpp", "asm": "s"}
OUT = os.path.join(ROOT, "build", "snippets")


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    count = 0
    for path in content_files():
        n = 0
        for lang, code in BLOCK_RE.findall(read(path)):
            first = code.lstrip().split("\n", 1)[0].strip()
            if first not in ("; kb:compile", "// kb:compile"):
                continue
            if lang not in EXT:
                print(f"::warning file={path}::kb:compile on unsupported "
                      f"language '{lang}', skipped")
                continue
            n += 1
            base = path[:-3].replace(os.sep, "-")
            with open(os.path.join(OUT, f"{base}-{n}.{EXT[lang]}"), "w",
                      encoding="utf-8") as f:
                f.write(code)
        count += n
    print(f"Extracted {count} snippet(s) to build/snippets/")


if __name__ == "__main__":
    main()
