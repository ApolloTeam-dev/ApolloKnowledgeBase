---
title: OpenLibrary by path returns the version already in memory
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [libraries]
applies_to:
  core: "any"
  os: [amigaos-3.9, amigaos-3.2]
tags: [ramlib, openlibrary, benchmark, testing, libraries]
related:
  - core/cpu-68080/performance-counters.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 8.2"
---

## Symptom

You benchmark or test two builds of a library, but both runs give the same
results: the second build is never used.

## Cause

AmigaOS `ramlib` matches libraries by name. Opening a second build by its
path returns the library that is already in memory with that name.

## Wrong

```c
base1 = OpenLibrary("work:old/mylib.library", 0);
CloseLibrary(base1);
base2 = OpenLibrary("work:new/mylib.library", 0);   /* still the old one */
```

## Right

Give each variant a unique name, or flush the old one from memory between
runs. When a test name changes the code layout, keep it the same length as
the real name (the name string shifts the code).

## Detection

Print the library's version string or a build marker after opening it.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| A second build opened by path returned the one in memory | (M) | any | Library benchmarks on AmigaOS 3.9 |
