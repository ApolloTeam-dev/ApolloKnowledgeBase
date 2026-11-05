---
name: apollo-new-project
description: Set up a new Apollo V4 software project (game, demo, tool, application, library, driver) as its own git repository with ApolloKnowledgeBase as submodule, a filled-in AGENTS.md, the ApolloCrossDev Makefile and a starting program for os-friendly or os-takeover mode that builds without warnings. Checks ApolloCrossDev first and offers updates. Use when the user wants to start, create, scaffold or set up a new program or project for the Apollo V4, Vampire V4, 68080 or SAGA, or wants an existing folder of Apollo code prepared for AI-assisted work.
---

# apollo-new-project

Create a project that every AI agent can work in correctly from the first
prompt: it knows its target, finds ApolloKnowledgeBase, and builds.

**The knowledge base (KB):** before the project exists, the repository this
skill is in (two folders above this file). KB paths below are relative to
its root. This skill's own files are in `assets/` next to this file.

## 1. Ask what the project is

Ask in one go, and suggest the defaults in brackets. Don't continue without
answers to the first five.

1. **Name** (becomes the folder, the program and `PROJECT_NAME`): letters,
   digits, `-` or `_`, no spaces.
2. **What it is**, in one sentence, and its **kind**: game, demo, tool,
   application, library or OS component.
3. **Target OS**, one or more: ApolloOS R10, AmigaOS 3.9, AmigaOS 3.2.
4. **Execution mode**: `os-takeover` (games and demos: multitasking off,
   direct 68080 and SAGA access, OS restored on exit) or `os-friendly`
   (applications and tools: OS calls). Explain the difference if asked; it
   is in `KB AGENTS.md` section 1 and `KB os/os-takeover.md`.
5. **Where**: the parent folder for the project [the current folder].
6. **Target core** [`Core 12500+`, the core with the current SAGA features
   such as the pointer sprite] and **V4 model** [any V4 model].
7. **Languages**: C, C++, 68080 assembly [C, with assembly where needed].
8. **ApolloLib** for SAGA sound, pictures, PIP, pointer and input [yes]. See
   `KB core/best-practices/prefer-library-calls-for-saga-chips.md`.

## 2. Check the toolchain, offer updates

Before creating anything, run the apollo-build skill's check:
`sh <skills folder>/apollo-build/scripts/find-acd.sh`. Then tell the user
what you found and let them choose:

| Finding | Offer |
|---|---|
| `PROBLEM=` ApolloCrossDev not found or incomplete | Install it first (`KB toolchain/index.md`, section Install; needs `sudo`, about 30 minutes). Stop until it is done. |
| `UPDATE=checkout` | `git pull` in the ApolloCrossDev folder: quick, brings new Makefile templates, ApolloLib and scripts. If `LOCAL_CHANGES=` is reported, the user decides about those first. Run the pull only with their consent. |
| `UPDATE=compiler` | Reinstall GCC-6.50-Dev (the command is in the line; needs `sudo`, about 30 minutes; the user runs it). Say what the newer build changes: the bug table in `KB toolchain/compiler-variants.md`. The user may also continue now and reinstall later. |
| `TEMPLATE=` older than v1.2 | `git pull` is required: the project needs `make compile` and builds outside ApolloCrossDev. |
| `UPDATES=none` | Nothing to offer; say the toolchain is up to date. |

Run the check again after an update. The project also needs
`APOLLOCROSSDEV`, because it lives outside `ApolloCrossDev/Projects/`. If
the check notes it is unset, ask the user to add
`export APOLLOCROSSDEV="<ACD_ROOT>"` to `~/.zshrc` (macOS) or `~/.bashrc`
(Linux), next to `AMIGAHOST`. For this session, pass it on the command
line: `APOLLOCROSSDEV=<ACD_ROOT> make compile`.

## 3. Create the repository

In `<where>/<name>`, which must not exist yet or be empty:

```sh
git init
git submodule add https://github.com/ApolloTeam-dev/ApolloKnowledgeBase ApolloKnowledgeBase
```

If the folder already holds code, don't overwrite anything: add only what is
missing and show the user what you would change.

## 4. AGENTS.md and CLAUDE.md

- `AGENTS.md`: from `KB templates/repo/AGENTS.md`. Fill in every
  `<placeholder>` from step 1, remove the template's HTML comments.
  - **Build and test:** `make compile` to build, `make` to build and upload
    to the V4 at `$AMIGAHOST`.
  - **Relevant knowledge base areas:** pick from the table in
    `KB AGENTS.md` section 3. Always `toolchain/`; `os/os-takeover.md` and
    `core/` for os-takeover; the SAGA folders that the program will use;
    `toolchain/apollolib/` with ApolloLib.
  - **Repository-specific rules:** leave one `- <rule>` line only if the user
    gives none; better, remove the section's placeholder.
- `CLAUDE.md`: copy `KB templates/repo/CLAUDE.md` as it is (it loads both
  AGENTS.md files for Claude Code).

## 5. Makefile

Copy `$APOLLOCROSSDEV/Projects/_makefiles/Makefile` and change only:

| Line | Set to |
|---|---|
| `PROJECT_NAME` | the name |
| `C_INCL_NDK` | NDK 3.2 (default), or the `ndk39-include` line when AmigaOS 3.9 is a target (`KB toolchain/target-os-headers.md`) |
| `APOLLOLIB` | keep it, or put `#` before it without ApolloLib |
| `C_COMPILER` | the `m68k-amigaos-g++` line for C++; the template does not collect `.cpp` files, so add them as `KB toolchain/project-makefile.md` says |

Keep `C_OPTIONS` and `S_FLAGS` as they are.

## 6. The starting program

Copy one file from `assets/` to `main.c` and replace `@PROJECT@`, `@WHAT@`
and `@TARGETS@` (core, model, target OS):

| Mode | ApolloLib | File |
|---|---|---|
| os-friendly | either | `assets/main-os-friendly.c` |
| os-takeover | yes | `assets/main-os-takeover.c` |
| os-takeover | no | `assets/main-os-takeover-nolib.c` |

The takeover programs leave the display takeover open on purpose: the KB
doesn't document it yet (`KB os/os-takeover.md`). Tell the user, and don't
fill it in from general Amiga knowledge.

Copy `assets/gitignore` to `.gitignore`.

## 7. Build it

Build with the apollo-build skill (`make compile`). It must end with no
errors and no warnings before you continue.

## 8. Hand over

- Show the user the files you made and the build result.
- Offer a first commit; commit only when they agree.
- Tell them how to work from here: open the project folder in their agent;
  `git submodule update --remote ApolloKnowledgeBase` brings in newer KB
  content when they want it.
