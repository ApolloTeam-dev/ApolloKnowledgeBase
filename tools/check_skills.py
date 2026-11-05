#!/usr/bin/env python3
"""Check the AI agent skills in skills/ (CONTRIBUTING.md section 12).

For every skills/<name>/SKILL.md:
  - frontmatter with exactly the fields name and description;
  - name equals the folder name: lowercase letters, digits, single hyphens,
    at most 64 characters;
  - description not empty, at most 1024 characters;
  - body at most 500 lines;
  - every path in backticks that names a knowledge base file (`KB <path>`, or
    a path starting with a knowledge base folder) exists, and every file of
    the skill it names (assets/..., scripts/...) exists;
  - the skill is listed in AGENTS.md section 9.
Exit code 1 when something is wrong.
"""
import os
import re
import sys

import yaml

from kblib import ROOT

SKILLS = os.path.join(ROOT, "skills")
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KB_TOP = ("core/", "hardware/", "os/", "toolchain/", "guides/", "examples/",
          "conventions/", "lessons/", "templates/", "tools/", "skills/")
KB_FILES = ("AGENTS.md", "CONTRIBUTING.md", "README.md")
OWN = ("assets/", "scripts/", "references/")


def paths_in(body):
    """(kind, path) for every path-like text in backticks."""
    for m in re.finditer(r"`([^`\n]+)`", body):
        text = m.group(1).strip()
        kb = text.startswith("KB ")
        if kb:
            text = text[3:].strip()
        text = text.split()[0] if text else text
        if not text or any(c in text for c in "<>$*{}") or "YYYY" in text or "..." in text:
            continue
        if text.startswith(OWN):
            yield "skill", text
        elif kb or text.startswith(KB_TOP) or text in KB_FILES:
            if kb or "/" in text or text in KB_FILES:
                yield "kb", text


def check(name, errors):
    folder = os.path.join(SKILLS, name)
    path = os.path.join(folder, "SKILL.md")
    rel = os.path.relpath(path, ROOT)
    if not os.path.isfile(path):
        errors.append(f"{rel}: missing")
        return
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        errors.append(f"{rel}: must start with --- frontmatter")
        return
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        errors.append(f"{rel}: frontmatter is not valid YAML: {e}")
        return
    body = m.group(2)

    extra = sorted(set(fm) - {"name", "description"})
    if extra:
        errors.append(f"{rel}: only name and description belong in the frontmatter, not {', '.join(extra)}")
    if fm.get("name") != name:
        errors.append(f"{rel}: name must be the folder name '{name}'")
    if not NAME.match(name) or len(name) > 64:
        errors.append(f"{rel}: the name must be lowercase letters, digits and single hyphens, at most 64 characters")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{rel}: description is missing")
    elif len(desc) > 1024:
        errors.append(f"{rel}: description is {len(desc)} characters, at most 1024")
    lines = body.count("\n") + 1
    if lines > 500:
        errors.append(f"{rel}: body is {lines} lines, at most 500")

    for kind, p in paths_in(body):
        base = folder if kind == "skill" else ROOT
        if not os.path.exists(os.path.join(base, p.rstrip("/"))):
            where = "this skill's folder" if kind == "skill" else "the knowledge base"
            errors.append(f"{rel}: `{p}` does not exist in {where}")


def main():
    errors = []
    names = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d))) if os.path.isdir(SKILLS) else []
    agents = open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8").read()
    for name in names:
        check(name, errors)
        if f"skills/{name}/" not in agents:
            errors.append(f"skills/{name}: not listed in AGENTS.md section 9")
    for e in errors:
        print(e)
    print(f"{len(names)} skills checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
