---
title: Prefer library calls over direct SAGA register access
type: best-practice
owner: WDrijver
status: draft
origin: ai-assisted
basis: [other]
components: [saga-audio-arne, saga-video-isabelle, saga-3d-maggie]
applies_to:
  core: "any"
  os: [any]
tags: [saga, arne, isabelle, maggie, library, apollolib, maggie-library, registers]
related:
  - core/saga-registers/index.md
  - os/libraries/maggie-library.md
  - toolchain/apollolib/index.md
  - core/saga-audio-arne/index.md
  - core/saga-video-isabelle/index.md
  - core/saga-3d-maggie/index.md
sources:
  - "WDrijver (maintainer), library calls for the SAGA chips, 2026-11-04"
  - "maggie.library, github.com/RMortenB/MaggieLibrary (the author's source, golden source)"
  - "ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib"
---

## Goal

Code that keeps working when the SAGA hardware or its use changes. A library
call hides register layouts, core differences and setup order, so the
program doesn't depend on them.

## Technique

For the SAGA chips, prefer the library calls to direct register access
(WDrijver, 2026-11-04):

| Chip | Use | Source |
|---|---|---|
| Arne (SAGA audio) | ApolloLib | github.com/WDrijver/ApolloCrossDev, `Projects/ApolloLib` |
| Isabelle (SAGA video) | ApolloLib | github.com/WDrijver/ApolloCrossDev, `Projects/ApolloLib` |
| Maggie (SAGA 3D) | maggie.library | github.com/RMortenB/MaggieLibrary (the author's source, golden source) |

- An official library for Arne and Isabelle is in development. Until it is
  released, ApolloLib is the best choice for library calls to Arne and
  Isabelle. It is described in
  [toolchain/apollolib/](../../toolchain/apollolib/index.md); check its
  [known bugs](../../toolchain/pitfalls/apollolib-known-bugs.md) first.
- maggie.library is described in
  [os/libraries/maggie-library.md](../../os/libraries/maggie-library.md).
  When you need more than that file covers, the author's repository is the
  golden source.
- The registers are documented in
  [core/saga-registers/](../saga-registers/index.md), for library work and
  for code that must access them directly.

## Evidence

| Variant | Measurement | Core | Test setup |
|---|---|---|---|
| Library calls instead of direct register access | Preferred: a best practice, not a forced rule | any | Statement (WDrijver, 2026-11-04) |

## When not to use

- This is a best practice, not a rule. Direct register access stays
  allowed, for example in `os-takeover` code (games, demos) or where a
  library has no call for what you need.
- When you write to SAGA registers directly, say so, as AGENTS.md section 2
  asks.
