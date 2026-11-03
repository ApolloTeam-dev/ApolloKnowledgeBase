"""Shared helpers for ApolloKnowledgeBase CI scripts."""
import os
import re
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Top-level files and folders that are not knowledge base content.
SKIP_TOP_FILES = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "CLAUDE.md"}
SKIP_DIRS = {"templates", "seed", "sources", "tools", "skills", "evals",
             ".github", ".git"}

# The four knowledge pillars. Files in a pillar are references, except in
# its best-practices/ and pitfalls/ subfolders.
PILLARS = {"core", "hardware", "os", "toolchain"}
PILLAR_SUBFOLDER_TYPES = {"best-practices": "best-practice",
                          "pitfalls": "pitfall"}

# Expected `type` per cross-cutting top-level folder.
FOLDER_TYPES = {
    "guides": "guide",
    "conventions": "convention",
    "examples": "example",
    "lessons": "lesson",
}

MAINTAINERS_FILE = os.path.join(ROOT, ".github", "CODEOWNERS.base")


def expected_type(path):
    """Return the `type` a content file must have, from its folder, or None
    if the file is outside the known content folders."""
    parts = path.split(os.sep)
    if parts[0] in PILLARS:
        if len(parts) > 2 and parts[1] in PILLAR_SUBFOLDER_TYPES:
            return PILLAR_SUBFOLDER_TYPES[parts[1]]
        return "reference"
    return FOLDER_TYPES.get(parts[0])


def maintainers():
    """Return the maintainer handles: the owners of `*` in CODEOWNERS.base."""
    with open(MAINTAINERS_FILE, encoding="utf-8") as f:
        for line in f:
            fields = line.split()
            if fields and fields[0] == "*":
                return {h.lstrip("@") for h in fields[1:]}
    return set()


HANDLE_RE = re.compile(r"^@?[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def content_files():
    """Yield repo-relative paths of all knowledge base content files, in the
    same order on every platform."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        top = rel_dir.split(os.sep)[0]
        if rel_dir == ".":
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        elif top in SKIP_DIRS:
            continue
        else:
            dirnames.sort()
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            if rel_dir == "." and name in SKIP_TOP_FILES:
                continue
            yield os.path.normpath(os.path.join(rel_dir, name))


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    """Return (dict, body) or (None, text) if there is no frontmatter.
    Raises yaml.YAMLError on invalid YAML."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    data = yaml.safe_load(m.group(1)) or {}
    return data, text[m.end():]


def report(errors):
    """Print errors in GitHub annotation format and exit accordingly."""
    for path, msg in errors:
        print(f"::error file={path}::{msg}")
        print(f"{path}: {msg}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} error(s).", file=sys.stderr)
        sys.exit(1)
    print("OK")
