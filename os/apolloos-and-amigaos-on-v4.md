---
title: Running on Apollo V4 under ApolloOS and AmigaOS
type: reference
owner: WDrijver
status: draft
origin: ai-assisted
components: [general]
applies_to:
  core: "any"
  os: [apolloos-r10, amigaos-3.9, amigaos-3.2]
sources:
  - "Not yet collected"
---

## Summary

Guidelines for programs that run on Apollo V4 hardware under ApolloOS R10,
AmigaOS 3.9 or AmigaOS 3.2. Read this for every Apollo V4 project.

**This file has no content yet.** If your task depends on it, tell the user
that the knowledge base does not cover OS-specific guidelines yet.

## Details

### Detecting Apollo V4 hardware

No content yet.

### OS functions per target OS

No content yet.

### Using SAGA features through the OS

No content yet.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO check the project's target OS list (its AGENTS.md) before using an OS
  function, and use only functions available in every target OS.
- DON'T work around ApolloOS behavior that differs from AmigaOS. Report it as
  an issue in github.com/ApolloTeam-dev/ApolloOS.R10 instead.
