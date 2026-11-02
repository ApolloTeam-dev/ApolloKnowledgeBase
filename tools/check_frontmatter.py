#!/usr/bin/env python3
"""Validate frontmatter, file naming and folder placement of all KB files.
Rules: see CONTRIBUTING.md sections 2-4."""
import datetime
import os
import re

import yaml

from kblib import FOLDER_TYPES, HANDLE_RE, ROOT, content_files, frontmatter, read, report

TYPES = {"reference", "guide", "convention", "best-practice", "pitfall",
         "example", "lesson"}
STATUSES = {"draft", "reviewed", "verified", "deprecated"}
ORIGINS = {"human", "ai-assisted"}
COMPONENTS = {"cpu-68080", "saga-video-isabelle", "saga-audio-arne",
              "saga-dma-anni", "saga-3d-maggie", "libraries", "devs",
              "filesys", "commands", "datatypes", "toolchain", "general"}
REQUIRED = ["title", "type", "owner", "status", "origin", "components",
            "applies_to"]
NEEDS_SOURCES = {"reference", "best-practice"}

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")
LESSON_RE = re.compile(r"^\d{4}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$")


def has_placeholder(value):
    if isinstance(value, str):
        return "<" in value and ">" in value
    if isinstance(value, list):
        return any(has_placeholder(v) for v in value)
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    return False


def check(path):
    errs = []
    name = os.path.basename(path)
    top = path.split(os.sep)[0]

    if top not in FOLDER_TYPES:
        return [f"file is outside the known content folders ({top}/)"]

    if top == "lessons":
        if not LESSON_RE.match(name):
            errs.append("lesson file name must be YYYY-MM-project-name.md")
    elif not KEBAB_RE.match(name):
        errs.append("file name must be lowercase kebab-case ending in .md")

    try:
        fm, _ = frontmatter(read(path))
    except yaml.YAMLError as e:
        return errs + [f"invalid YAML frontmatter: {e}"]
    if fm is None:
        return errs + ["missing frontmatter (file must start with ---)"]

    for key in REQUIRED:
        if key not in fm or fm[key] in (None, "", []):
            errs.append(f"missing required field '{key}'")

    if has_placeholder(fm):
        errs.append("frontmatter still contains <placeholder> text")

    t = fm.get("type")
    if t is not None:
        if t not in TYPES:
            errs.append(f"invalid type '{t}'")
        elif t != FOLDER_TYPES[top]:
            errs.append(f"type '{t}' does not belong in {top}/ "
                        f"(expected '{FOLDER_TYPES[top]}')")

    owner = fm.get("owner")
    if owner is not None and not (isinstance(owner, str)
                                  and HANDLE_RE.match(owner)):
        errs.append("owner must be a single GitHub handle")

    status = fm.get("status")
    if status is not None and status not in STATUSES:
        errs.append(f"invalid status '{status}'")

    origin = fm.get("origin")
    if origin is not None and origin not in ORIGINS:
        errs.append(f"invalid origin '{origin}'")

    if t == "lesson" and status not in (None, "draft", "deprecated"):
        errs.append("lessons stay draft (or deprecated)")

    comps = fm.get("components")
    if comps is not None:
        if not isinstance(comps, list):
            errs.append("components must be a list")
        else:
            for c in comps:
                if c not in COMPONENTS:
                    errs.append(f"invalid component '{c}'")

    at = fm.get("applies_to")
    if at is not None:
        if not isinstance(at, dict) or not {"core", "apolloos"} <= set(at):
            errs.append("applies_to must contain 'core' and 'apolloos'")

    lv = fm.get("last_verified")
    if status == "verified" and not lv:
        errs.append("status 'verified' requires last_verified")
    if lv and not isinstance(lv, datetime.date):
        errs.append("last_verified must be a date (YYYY-MM-DD)")

    if t in NEEDS_SOURCES and status in ("reviewed", "verified") \
            and not fm.get("sources"):
        errs.append(f"type '{t}' needs sources before it can be {status}")

    if status == "deprecated":
        sb = fm.get("superseded_by")
        if not sb:
            errs.append("status 'deprecated' requires superseded_by")
        elif not os.path.isfile(os.path.join(ROOT, sb)):
            errs.append(f"superseded_by points to missing file '{sb}'")

    related = fm.get("related") or []
    if not isinstance(related, list):
        errs.append("related must be a list")
    else:
        for r in related:
            if not os.path.isfile(os.path.join(ROOT, str(r))):
                errs.append(f"related points to missing file '{r}'")

    return errs


def main():
    errors = []
    for path in content_files():
        errors += [(path, e) for e in check(path)]
    report(errors)


if __name__ == "__main__":
    main()
