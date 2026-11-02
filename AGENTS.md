# AGENTS.md: ApolloKnowledgeBase

You are working with ApolloKnowledgeBase, the curated knowledge base for
software development on the Apollo V4 platform. Read this file first. It tells
you what the platform is, what you probably assume wrongly, and which files to
read for your task.

When this knowledge base is used from a code repository, that repository's
own AGENTS.md states where the knowledge base is located. All paths below are
relative to the knowledge base root.

---

## 1. The platform in brief

- **Apollo V4**: hardware platform built around the **68080** CPU, a successor
  of the Motorola 68000 family, with the **AMMX** SIMD extension.
- **SAGA chipset**: `saga-video-isabelle` (video), `saga-audio-arne` (audio),
  `saga-dma-anni` (DMA), `saga-3d-maggie` (3D).
- **Target OS**: Apollo V4 software runs on one or more of **ApolloOS R10**
  (fork of AROS, optimized for Apollo V4), **AmigaOS 3.9** and
  **AmigaOS 3.2**. The project's own AGENTS.md states which. Hardware
  knowledge applies whatever the OS.
- **ApolloCrossDev**: the one and only toolchain
  (github.com/WDrijver/ApolloCrossDev).

---

## 2. Your knowledge is probably wrong here

Your training data covers classic AmigaOS and the 68000–68060 well. Your
AmigaOS API knowledge is mostly right on Apollo V4. Your hardware and
compiler knowledge is where you will make confident mistakes.

- DON'T assume 68060 behavior, timing or instruction availability applies to
  the 68080. Check `core/cpu-68080/`.
- DON'T assume classic Amiga chipset behavior applies to SAGA. Check the
  relevant `core/saga-*` folder.
- DON'T assume generic m68k GCC or vasm behavior. ApolloCrossDev is a patched
  GCC 6.5 with 68080 support. Check `toolchain/`.
- DON'T write generic 68k code when an Apollo-specific technique exists. Check
  `best-practices/` before writing performance-relevant code.
- DON'T use OS functions that are missing in one of the project's target
  operating systems. Check `os/apolloos-and-amigaos-on-v4.md`.
- DON'T invent register addresses, bit meanings, function signatures or
  compiler flags. If it is not in the knowledge base or in source code you
  have read, say that you don't know.

---

## 3. What to read for your task

Read only what your task needs. Always check the matching `pitfalls/` and
`best-practices/` subfolders as well as the reference files.

| Task | Read |
|---|---|
| Any task | This file, `os/apolloos-and-amigaos-on-v4.md` |
| Target OS is ApolloOS only, or working on ApolloOS itself (ApolloOS.R10) | `os/apolloos-specific-on-v4.md`, `os/` subfolders |
| Writing code at all | `conventions/`, `toolchain/` |
| CPU-heavy or assembly code | `core/cpu-68080/`, `best-practices/core/`, `pitfalls/core/` |
| Graphics, screens, video modes | `core/saga-video-isabelle/` |
| Sound | `core/saga-audio-arne/` |
| Memory transfers, DMA | `core/saga-dma-anni/` |
| 3D | `core/saga-3d-maggie/` |
| Using or changing an ApolloOS library | `os/libraries/` |
| Device drivers | `os/devs/`, plus the `core/` folder of the hardware involved |
| Filesystems | `os/filesys/` |
| Shell commands | `os/commands/` |
| Datatypes | `os/datatypes/` |
| Build problems, compiler flags, optimization settings | `toolchain/`, `best-practices/toolchain/`, `pitfalls/toolchain/` |
| A task with a matching how-to | `guides/` |
| Looking for working code to start from | `examples/` |

Follow `related:` links in a file's frontmatter when they are relevant to the
task.

DON'T read `lessons/` by default. Read it only when asked, or when writing a
new lesson or distilling lessons into other files.

---

## 4. How to interpret file metadata

Every file starts with YAML frontmatter (full spec in `CONTRIBUTING.md`).

- **status**
  - `verified`: tested on real hardware. Trust it.
  - `reviewed`: checked by its owner. Trust it, but verify critical details
    when possible.
  - `draft`: unreviewed. Use with caution and tell the user when your answer
    depends on a draft.
  - `deprecated`: do not use. Follow `superseded_by`.
- **applies_to**: check that the core revision matches the user's target and
  that `os` is `any` or covers every target OS of the project. If not, or the
  target is unknown, say so.
- **origin: ai-assisted**: drafted by an AI. Treat like `draft` unless the
  status says otherwise.

When two files contradict each other, prefer the higher status, then the more
recent `last_verified`, and tell the user about the conflict.

---

## 5. When the knowledge base is silent

1. Say clearly that the knowledge base does not cover it.
2. If available, read the actual source code (ApolloOS repository,
   ApolloCrossDev repository) and say that your answer is based on it.
3. Propose a new knowledge base file or addition so the gap gets closed.

If ApolloOS behaves differently from AmigaOS in a way that breaks a program,
that is an ApolloOS bug. Propose an issue for
github.com/ApolloTeam-dev/ApolloOS.R10, not a knowledge base workaround.

---

## 6. Writing code

- Apply relevant `best-practices/` and avoid all relevant `pitfalls/`.
- Build with ApolloCrossDev as described in `toolchain/`, and fix all errors
  and warnings before presenting code.
- In pull request descriptions, list the knowledge base files you relied on.
  This shows reviewers where wrong code came from if the knowledge base itself
  was wrong.

---

## 7. Writing to the knowledge base

- Follow `CONTRIBUTING.md` exactly: folder, file name, frontmatter, template.
- Always set `origin: ai-assisted` and `status: draft`.
- Set `owner` to the person who asked you to make the change, unless they
  name someone else.
- Never change the `status` of an existing file. Status changes are human
  decisions.
- Never delete files. Deprecate them as described in `CONTRIBUTING.md`.
- All changes go through a pull request.

---

## 8. After finishing a project

Offer to draft a lesson in `lessons/` using the lesson template. Be specific
and honest about what you got wrong, especially wrong assumptions from
section 2. Those are the most valuable input for improving this knowledge
base.
