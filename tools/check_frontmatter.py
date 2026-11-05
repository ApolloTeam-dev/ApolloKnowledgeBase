#!/usr/bin/env python3
"""Validate frontmatter, file naming and folder placement of all KB files.
Rules: see CONTRIBUTING.md sections 2-4."""
import datetime
import os
import re

import yaml

from kblib import (HANDLE_RE, ROOT, SCHEMA, content_files, expected_type,
                   frontmatter, maintainers, read, report)

# The allowed values and patterns come from tools/schema.json, which the
# ApolloKnowledgeBase-Manager wizard reads too.
TYPES = set(SCHEMA["types"])
STATUSES = set(SCHEMA["statuses"])
ORIGINS = set(SCHEMA["origins"])
COMPONENTS = set(SCHEMA["components"])
OSES = set(SCHEMA["oses"])
MODES = set(SCHEMA["modes"])
BOARDS = set(SCHEMA["boards"])
# Kinds of source, highest rank first (CONTRIBUTING.md section 4).
BASES = list(SCHEMA["bases"])
# "any", one core ("Core 12841"), a range ("Core 12830-12840") or a minimum
# ("Core 12841+").
CORE_RE = re.compile(SCHEMA["core_pattern"])
REQUIRED = list(SCHEMA["required"])
NEEDS_SOURCES = set(SCHEMA["needs_sources"])

KEBAB_RE = re.compile(SCHEMA["kebab_pattern"])
LESSON_RE = re.compile(SCHEMA["lesson_pattern"])


def check_values(at, key, allowed):
    """Check applies_to.<key>: a non-empty list of allowed values, where
    'any' stands alone."""
    values = at[key]
    if not isinstance(values, list) or not values:
        return [f"applies_to.{key} must be a non-empty list"]
    errs = [f"invalid {key} '{v}'" for v in values if v not in allowed]
    if "any" in values and len(values) > 1:
        errs.append(f"applies_to.{key} 'any' cannot be combined with other "
                    "values")
    return errs


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
    expected = expected_type(path)

    if expected is None:
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
        elif t != expected:
            errs.append(f"type '{t}' does not belong in "
                        f"{os.path.dirname(path)}/ (expected '{expected}')")

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

    # Document intake (CONTRIBUTING.md section 11) is for maintainers only.
    if origin == "official" and isinstance(owner, str) \
            and owner.lstrip("@") not in maintainers():
        errs.append("origin 'official' requires a maintainer as owner")
    gf = fm.get("generated_from")
    if gf is not None:
        if origin != "official":
            errs.append("generated_from requires origin 'official'")
        if not (isinstance(gf, str) and gf.startswith("sources/official/")):
            errs.append("generated_from must be a path in sources/official/")
        elif not os.path.isfile(os.path.join(ROOT, gf)):
            errs.append(f"generated_from points to missing file '{gf}'")

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
        if not isinstance(at, dict) or not {"core", "os"} <= set(at):
            errs.append("applies_to must contain 'core' and 'os'")
        else:
            errs += check_values(at, "os", OSES)
            if "mode" in at:
                errs += check_values(at, "mode", MODES)
            if "board" in at:
                errs += check_values(at, "board", BOARDS)
            core = at.get("core")
            if not (isinstance(core, str) and CORE_RE.match(core)):
                errs.append(f"invalid core '{core}': use \"any\", "
                            "\"Core 12841\", \"Core 12830-12840\" or "
                            "\"Core 12841+\"")
            else:
                m = re.match(r"^Core (\d+)-(\d+)$", core)
                if m and int(m.group(1)) >= int(m.group(2)):
                    errs.append(f"core range '{core}' must go from low to high")

    basis = fm.get("basis")
    if basis is not None:
        if not isinstance(basis, list) or not basis:
            errs.append("basis must be a non-empty list")
        else:
            errs += [f"invalid basis '{b}'" for b in basis if b not in BASES]

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
