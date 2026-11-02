"""Shared helpers for ApolloKnowledgeBase CI scripts."""
import os
import re
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Top-level files and folders that are not knowledge base content.
SKIP_TOP_FILES = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "CLAUDE.md"}
SKIP_DIRS = {"templates", "seed", "tools", "skills", "evals", ".github", ".git"}

# Expected `type` per top-level content folder.
FOLDER_TYPES = {
    "core": "reference",
    "os": "reference",
    "toolchain": "reference",
    "guides": "guide",
    "conventions": "convention",
    "best-practices": "best-practice",
    "pitfalls": "pitfall",
    "examples": "example",
    "lessons": "lesson",
}

HANDLE_RE = re.compile(r"^@?[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def content_files():
    """Yield repo-relative paths of all knowledge base content files."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        top = rel_dir.split(os.sep)[0]
        if rel_dir == ".":
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        elif top in SKIP_DIRS:
            continue
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
