---
title: Text files for the Amiga are ISO-8859-1, not UTF-8
type: convention
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [other]
components: [general]
applies_to:
  core: "any"
  os: [any]
tags: [convention, text, encoding, iso-8859-1, utf-8, catalog, readme]
related:
  - os/apolloos-and-amigaos-on-v4.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 13"
---

## Rule

Every text file meant to be read on the Amiga (readme files, `.guide`
documents, catalog sources, scripts, strings in program sources) is
written in ISO-8859-1 (Latin-1), not UTF-8.

## Rationale

AmigaOS and ApolloOS display text as ISO-8859-1. UTF-8 characters outside
ASCII show up there as two or three wrong characters. Files for the host
side only, such as this knowledge base, can stay UTF-8.

## Examples

- DO save an Amiga `ReadMe` with an `é` as the single byte `$E9`.
- DO check a file with `file` or `iconv -f ISO-8859-1` before packaging it.
- DON'T put typographic quotes, dashes or emoji in Amiga text files: most
  have no ISO-8859-1 code.
- DON'T convert a file that already mixes encodings blindly: fix it by hand.
