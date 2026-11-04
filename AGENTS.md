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
- **V4 models**: V4 Standalone (SA), V4 UniCorn (UNI, A6000), V4 IceDrake
  (ICE), V4 Manticore (MC) and V4 Firebird (FB). They share the FPGA core
  (68080 and SAGA) but differ as boards. A core number has exactly the same
  features and architecture on every model; the boards differ only in small
  physical properties (for example, the V4 IceDrake has no second SPI
  port). The project's own AGENTS.md states the target model(s), if it
  depends on one.
- **Target OS**: Apollo V4 software runs on one or more of **ApolloOS R10**
  (fork of AROS, optimized for Apollo V4), **AmigaOS 3.9** and
  **AmigaOS 3.2**. The project's own AGENTS.md states which. Hardware
  knowledge applies whatever the OS.
- **Execution mode**: the project's AGENTS.md also states one of two modes.
  - `os-friendly`: use OS calls where available. Direct SAGA access only at
    the developer's discretion and responsibility.
  - `os-takeover`: `Forbid()` multitasking, use only basic OS calls
    (`AllocMem()`/`FreeMem()`, `Open()`/`Close()`), program the 68080 and
    SAGA directly, and restore multitasking and the Workbench screen on exit.
    Typical for games and demos.
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
  `core/best-practices/` before writing performance-relevant code.
- DON'T use OS functions that are missing in one of the project's target
  operating systems. Check `os/apolloos-and-amigaos-on-v4.md`.
- DON'T access SAGA registers directly in an `os-friendly` project unless the
  developer asks for it. When you do, say so.
- DON'T call OS functions beyond the basic set in an `os-takeover` project,
  and DON'T leave the machine without restoring multitasking and the
  Workbench screen. Check `os/os-takeover.md`.
- DON'T assume a connector, header or memory layout is the same on every V4
  model. Check `hardware/v4-generic/` and the model's folder in `hardware/`.
- DON'T invent register addresses, bit meanings, function signatures or
  compiler flags. If it is not in the knowledge base or in source code you
  have read, say that you don't know.

---

## 3. What to read for your task

The knowledge base has four pillars: `core/` (68080 and SAGA), `hardware/`
(the V4 boards), `os/` (ApolloOS and AmigaOS on V4) and `toolchain/`
(ApolloCrossDev). Each has its
own `best-practices/` and `pitfalls/` subfolders. Read only what your task
needs, and always check the `best-practices/` and `pitfalls/` of every pillar
you read.

| Task | Read |
|---|---|
| Any task | This file, `os/apolloos-and-amigaos-on-v4.md`, `os/best-practices/`, `os/pitfalls/` |
| Target OS is ApolloOS only, or working on ApolloOS itself (ApolloOS.R10) | `os/apolloos-specific-on-v4.md`, `os/` subfolders |
| Execution mode is `os-takeover` (games, demos) | `os/os-takeover.md`, `core/` |
| Writing code at all | `conventions/`, `toolchain/` |
| CPU-heavy or assembly code | `core/cpu-68080/`, `core/best-practices/`, `core/pitfalls/` |
| Graphics, screens, video modes | `core/saga-video-isabelle/` |
| Sound | `core/saga-audio-arne/` |
| Memory transfers, DMA | `core/saga-dma-anni/` |
| 3D | `core/saga-3d-maggie/` |
| Board connectors, headers, memory, model differences | `hardware/v4-generic/`, the model's folder in `hardware/` |
| Using or changing an ApolloOS library | `os/libraries/` |
| Device drivers | `os/devs/`, plus the `core/` or `hardware/` folder of the hardware involved |
| Filesystems | `os/filesys/` |
| Shell commands | `os/commands/` |
| Datatypes | `os/datatypes/` |
| Build problems, compiler flags, optimization settings | `toolchain/`, `toolchain/best-practices/`, `toolchain/pitfalls/` |
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
- **applies_to**: check that `core` covers the user's core (`any`,
  `Core 12841`, a range `Core 12830-12840` or `Core 12841+`), that `os` is
  `any` or covers every target OS of the project, and that `mode` and
  `board` (if present) include the project's execution mode and V4 model. If
  not, or the target is unknown, say so.
- **basis** and the tags after facts tell where a fact comes from: **(G)**
  the core developer, **(M)** measured on V4 hardware, **(official)** official
  Apollo documentation such as the 68080 PRM, **(SRC)** source code.
- **origin**
  - `official`: converted from official Apollo documentation. Authoritative,
    but conversion errors are possible while the status is `draft`.
  - `ai-assisted`: drafted by an AI. Treat like `draft` unless the status
    says otherwise.
- **generated_from**: the file is generated from an original document in
  `sources/official/`. Never edit it. Propose the change to the maintainers
  as a change to the original document.

When two facts contradict each other, decide in this order, and always tell
the user about the conflict:

1. The source rank: (G) core developer, then (M) measured, then (official)
   documentation, then (SRC) source code, then anything else.
2. The newer core.
3. The higher status, then the more recent `last_verified`.

So a measured fact in a pitfall beats the 68080 PRM, even when the PRM file
has a higher status.

---

## 5. When the knowledge base is silent

1. Say clearly that the knowledge base does not cover it.
2. If available, read the actual source code (ApolloOS repository,
   ApolloCrossDev repository) and say that your answer is based on it.
3. Propose a new knowledge base file or addition so the gap gets closed.

If something works on AmigaOS but fails on ApolloOS, that is an ApolloOS bug.
Propose an issue for github.com/ApolloTeam-dev/ApolloOS.R10, not a pitfall or
workaround in the knowledge base.

---

## 6. Writing code

- Apply the relevant best practices and avoid all relevant pitfalls of each
  pillar.
- Build with ApolloCrossDev as described in `toolchain/`, and fix all errors
  and warnings before presenting code.
- In pull request descriptions, list the knowledge base files you relied on.
  This shows reviewers where wrong code came from if the knowledge base itself
  was wrong.

---

## 7. Writing to the knowledge base

- Follow `CONTRIBUTING.md` exactly: folder, file name, frontmatter, template.
- Always set `origin: ai-assisted` and `status: draft`. Exception: during
  document intake by a maintainer, set `origin: official` as described in
  `CONTRIBUTING.md` section 11.
- Never edit a file that has `generated_from` in its frontmatter.
- Set `owner` to the person who asked you to make the change, unless they
  name someone else.
- Never change the `status` of an existing file. Status changes are human
  decisions.
- Never delete files. Deprecate them as described in `CONTRIBUTING.md`.
- All changes go through a pull request.

---

## 8. Lessons: give back what the project learned

Offer the developer a lesson when:

- they say a project, a release or a milestone is done, or ask for a summary;
- you find that an assumption from section 2 was wrong (offer it right away,
  while the details are fresh).

Then:

1. Draft `lessons/YYYY-MM-project-name.md` from
   `templates/files/lesson.md`. Be specific and honest about what you got
   wrong, especially wrong assumptions from section 2. Give the evidence
   (source tag, core, method) for every measured claim.
2. Show the draft to the developer. Submit nothing without their approval.
3. Submit it as described in `CONTRIBUTING.md` section 7: preferably as a
   pull request from the knowledge base clone (the `ApolloKnowledgeBase/`
   submodule), on a branch `lesson/YYYY-MM-project-name`; otherwise give the
   developer the text for the "Submit a lesson" issue form.
4. Return the submodule to the commit the project uses afterwards.
