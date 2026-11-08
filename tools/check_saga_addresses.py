#!/usr/bin/env python3
"""Every SAGA chipset address ($DFExxx, $DFFxxx) named in a content file must
be documented in core/saga-registers/, the files generated from the SAGA
register documentation, or be listed in tools/saga_addresses_allowed.yml.

This catches typos and invented addresses. An address that is real but not
documented yet goes in the allowlist with its source, until document intake
adds it to core/saga-registers/.

Read-back addresses $DFE000-$DFE1FF count as their $DFFxxx write address
(core/saga-registers/pointer.md)."""
import os
import re

import yaml

from kblib import ROOT, content_files, frontmatter, read, report

ADDR_RE = re.compile(r"(?:\$|0x)(?:00)?(DF[EF][0-9A-F]{3})\b", re.IGNORECASE)
REGISTERS = "core" + os.sep + "saga-registers" + os.sep
ALLOWLIST = os.path.join(ROOT, "tools", "saga_addresses_allowed.yml")


def canonical(addr):
    addr = addr.upper()
    if addr.startswith("DFE") and int(addr[3:], 16) <= 0x1FF:
        return "DFF" + addr[3:]
    return addr


def generated(text):
    try:
        data, _ = frontmatter(text)
    except yaml.YAMLError:
        return False
    return bool(data and data.get("generated_from"))


def main():
    files = [(p, read(p)) for p in content_files()]
    known = {canonical(a) for p, t in files
             if p.startswith(REGISTERS) and generated(t)
             for a in ADDR_RE.findall(t)}
    with open(ALLOWLIST, encoding="utf-8") as f:
        allowed = {canonical(str(a)) for a in (yaml.safe_load(f) or {})}
    errors = []
    for path, text in files:
        if generated(text):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in ADDR_RE.finditer(line):
                a = canonical(m.group(1))
                if a not in known and a not in allowed:
                    errors.append((path, f"line {n}: ${m.group(1).upper()} "
                                   "is not in core/saga-registers/ or "
                                   "tools/saga_addresses_allowed.yml"))
    report(errors)


if __name__ == "__main__":
    main()
