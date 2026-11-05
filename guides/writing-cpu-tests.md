---
title: Write CPU tests for the 68080 core
type: guide
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured]
components: [cpu-68080]
applies_to:
  core: "any"
  os: [any]
tags: [testing, cpu-tests, assert, emulator, core]
related:
  - core/cpu-68080/core-bugs-by-revision.md
  - core/cpu-68080/performance-counters.md
  - guides/generators-and-verification.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 14"
---

## Goal

Tests of the 68080 core whose failures point at the core, not at the test:
each check is unambiguous, reproducible and traceable to one instruction.

## Prerequisites

- The test harness's `assert_zero` address, `$00D8000C`.
- An 080-aware disassembler and a 68k emulator.

## Steps

1. **One check, one write.** Write (result − expected) to `assert_zero`
   (`$00D8000C`), in the size the result was computed in.
2. **Plain code:** no macros, one instruction per line. MRI assemblers
   silently take a second instruction on a line as a comment.
3. **Number the checks.** Put the check number in a register
   (`movea.w #n,a5`) so a failure is easy to find.
4. **Loop each test about 5 times.** Cold and trained passes must give the
   same result.
5. **Hand-trace every expected value** from the bytes actually written.
6. **Run everything that is not 080-specific on a 68k emulator first.** A
   check that fails on any CPU is a bug in the test.
7. **Decode every hand-encoded `dc.w` back** with an 080-aware disassembler,
   and check its length.

Mistakes TuKo1982 made, so you don't:

- the element size of a fill against the size of its address;
- indexing with `.l` after `divu` + `swap` (the quotient is in the high
  word);
- expecting IEP2 to move on a cold pass;
- comparing equal operands in an operand-order test;
- using a register as scratch that was still to be checked.

## Verification

- The generic part passes on the emulator.
- All passes of the loop give the same result on the V4.
- A deliberately wrong expected value makes exactly the right check fail,
  with its number in a5.
