---
title: OS takeover on Apollo V4
type: reference
owner: WDrijver
status: reviewed
origin: ai-assisted
components: [general]
applies_to:
  core: "any"
  os: [apolloos-r10, amigaos-3.9, amigaos-3.2]
  mode: [os-takeover]
tags: [takeover, forbid, games, demos]
related:
  - os/apolloos-and-amigaos-on-v4.md
sources:
  - "WDrijver, definition of the os-takeover execution mode, 2026-11-02"
  - "exec.library autodocs: Forbid(), Permit()"
---

## Summary

An `os-takeover` program starts from the OS, stops multitasking with
`Forbid()`, programs the 68080 and the SAGA chipset directly, and on exit
restores multitasking and the Workbench screen. Typical for games and demos.

## Details

### The mode

- Disable multitasking with `Forbid()`.
- Use only basic OS calls: `AllocMem()`/`FreeMem()` for memory and
  `Open()`/`Close()` for files.
- Focus on direct hardware access, using the 68080 and SAGA chipset
  features.
- On exit: restore multitasking with `Permit()` and restore the Workbench
  screen.

### What Forbid() does and does not do

- `Forbid()` stops other tasks from being scheduled. It does not disable
  interrupts: OS interrupt handlers keep running.
- When the program calls a function that waits, such as `Open()` or a read
  from disk, the `Forbid()` state is suspended until the call returns. Other
  tasks run during that time. This is why file I/O still works in takeover
  mode.
- `Forbid()` and `Permit()` nest: every `Forbid()` needs exactly one
  `Permit()`.

### Interrupts during takeover

No content yet.

### Taking over the display

No content yet.

### Restoring the Workbench screen

No content yet.

### Differences per target OS

No content yet. Where entering or leaving a takeover differs between
ApolloOS R10, AmigaOS 3.9 and AmigaOS 3.2, document it here.

## Differences from AmigaOS / AROS / 68060

No content yet.

## Do / Don't

- DO allocate memory and load files before relying on exclusive hardware
  access, and free and close everything before exit.
- DO pair every `Forbid()` with one `Permit()`, on every exit path,
  including error paths.
- DO restore the Workbench screen before returning to the OS.
- DON'T call OS functions beyond the basic set while in takeover mode.
- DON'T assume `Forbid()` stops interrupts.
