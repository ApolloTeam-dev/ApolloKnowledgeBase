---
name: apollo-new-project
description: Set up a new Apollo V4 software project (game, demo, tool, application, library, device, datatype) as its own git repository in which every AI agent uses ApolloKnowledgeBase as its central source of Apollo V4 knowledge, then check, install or update ApolloCrossDev, and create the Makefile and a starting program for os-friendly or os-takeover mode that builds without warnings (guided setup), or only the AKB setup for the agent (basic setup). Use when the user wants to start, create, scaffold or set up a new program or project for the Apollo V4, Vampire V4, 68080 or SAGA, pastes the "Start Apollo V4 Project" prompt from apolloknowledgebase.com, or wants an existing folder of Apollo code prepared for AI-assisted work.
---

# apollo-new-project

Create a project that every AI agent can work in correctly from the first
prompt: it treats ApolloKnowledgeBase (AKB) as the central source of Apollo
V4 knowledge, knows its target, and builds with ApolloCrossDev.

**Where the files are.** You may have this skill as a local copy (an AKB
clone, the Claude Code plugin `akb`) or only from its URL on GitHub. Either
way, from step 2 on use the project's own `ApolloKnowledgeBase/` submodule:
**KB** paths below are relative to it, and this skill's files are in
`ApolloKnowledgeBase/skills/apollo-new-project/assets/`, and the toolchain
check is `ApolloKnowledgeBase/skills/apollo-build/scripts/find-acd.sh`. In step
1, before the submodule exists, read KB files on GitHub if you need them:
`https://raw.githubusercontent.com/ApolloTeam-dev/ApolloKnowledgeBase/main/<path>`.

## 0. Guided or basic setup

The project is the folder this session was started in: don't ask where.
First ask which setup the developer wants:

- **Guided setup:** the full procedure, steps 1 to 8: a few questions, AKB,
  ApolloCrossDev checked, installed or updated, Makefile, a starting
  program, and a build without warnings.
- **Basic setup:** only what an agent needs to use AKB correctly: steps 2
  and 3, without questions. The developer does the rest (toolchain,
  Makefile, code).

For a basic setup, skip step 1. In `AGENTS.md` (step 3), fill in the project
name (the folder's name) and the defaults from the table in step 1, and
write `not set yet` for what it is, kind, execution mode and languages,
with this line under the list: "Fields marked `not set yet`: ask the
developer before relying on them, and fill them in." Leave out the build
commands and write "Not set up yet: use the apollo-build skill when the
project gets a Makefile." Then go to step 8: show the files, offer a first
commit, and mention that the guided setup can still check ApolloCrossDev
and add a Makefile and a starting program later.

## 1. Ask what the project is (guided setup)

Ask these four in one go, and suggest the defaults in brackets:

1. **Project name** [the current folder's name]: becomes `PROJECT_NAME` and
   the program's name. Letters, digits, `-` or `_`, no spaces.
2. **What it is**, in one sentence, and its **kind**: game, demo, tool,
   application, library, device or datatype.
3. **Execution mode**: `os-takeover` (games and demos: multitasking off,
   direct 68080 and SAGA access, OS restored on exit) or `os-friendly`
   (applications and tools: OS calls). Explain the difference if asked; it
   is in `KB AGENTS.md` section 1 and `KB os/os-takeover.md`.
4. **Which language(s)**: C, C++ and/or assembler [C].

Don't ask about the rest; every new project gets these, and the developer
can change them later in `AGENTS.md`:

| Setting | Value |
|---|---|
| Target OS | ApolloOS R10, AmigaOS 3.9 and AmigaOS 3.2 |
| Target core | the latest core release. When code uses something that a knowledge base file limits to a minimum core (its `applies_to.core`), tell the developer. |
| V4 model | any V4 model |
| ApolloLib | yes, for SAGA sound, pictures, PIP, pointer and input (`KB core/best-practices/prefer-library-calls-for-saga-chips.md`) |

## 2. Create the repository with AKB

In the current folder:

```sh
git init
git submodule add https://github.com/ApolloTeam-dev/ApolloKnowledgeBase ApolloKnowledgeBase
```

If the folder already holds code, don't overwrite anything: add only what is
missing and show the user what you would change. If it is already a git
repository, skip `git init`.

## 3. Make AKB the agents' central source

These files make every agent that opens the project read AKB first.

- **`AGENTS.md`** (read by most agents): from `KB templates/repo/AGENTS.md`.
  Fill in every `<placeholder>` from step 1 and its defaults, remove the
  template's HTML comments.
  - **Build and test:** `make compile` to build, `make` to build and upload
    to the V4 at `$AMIGAHOST`.
  - **Relevant knowledge base areas:** pick from the table in
    `KB AGENTS.md` section 3. Always `toolchain/`; `os/os-takeover.md` and
    `core/` for os-takeover; the SAGA folders that the program will use;
    `toolchain/apollolib/`.
  - **Repository-specific rules:** the user's rules, or remove the section's
    placeholder line.
- **`CLAUDE.md`** (Claude Code): copy `KB templates/repo/CLAUDE.md` as it is.
  It loads both AGENTS.md files.
- **`.claude/settings.json`** (Claude Code): offers the AKB skills to
  everyone who opens the project. Each person installs the plugin once with
  `/plugin install akb@apolloknowledgebase`; Claude Code reminds them.

  ```json
  {
    "extraKnownMarketplaces": {
      "apolloknowledgebase": {
        "source": { "source": "github", "repo": "ApolloTeam-dev/ApolloKnowledgeBase" }
      }
    },
    "enabledPlugins": {
      "akb@apolloknowledgebase": true
    }
  }
  ```

Other agents reach the AKB skills through `KB AGENTS.md` section 9, which
the project's AGENTS.md sends them to.

## 4. ApolloCrossDev: check, install or update (guided setup)

Run the check from the submodule:

```sh
sh ApolloKnowledgeBase/skills/apollo-build/scripts/find-acd.sh
```

Tell the user what you found and let them choose:

| Finding | Offer |
|---|---|
| `PROBLEM=` ApolloCrossDev not found | Install it (`KB toolchain/index.md`, sections Host requirements and Install). With the user's consent, clone it: `git clone https://github.com/WDrijver/ApolloCrossDev ~/ApolloCrossDev`. The install script needs `sudo` and takes about 30 minutes, so the user runs it in their terminal: `cd ~/ApolloCrossDev && ./GCC-6.50-Dev-MacOS.sh` (or `-Linux.sh`). Wait until it is done. |
| `PROBLEM=` a binary is missing | The install failed: point the user to `Compilers/GCC-6.50-Dev/_logs/*_err.log` and the reinstall command. Wait until it is fixed. |
| `UPDATE=checkout` | `git pull` in the ApolloCrossDev folder: quick, brings new Makefile templates, ApolloLib and scripts. If `LOCAL_CHANGES=` is reported, the user decides about those first. Run the pull only with their consent. |
| `UPDATE=compiler` | Reinstall GCC-6.50-Dev (the command is in the line; `sudo`, about 30 minutes; the user runs it). Say what the newer build changes: the bug table in `KB toolchain/compiler-variants.md`. The user may also continue now and reinstall later. |
| `TEMPLATE=` older than v1.2 | `git pull` is required: the project needs `make compile` and builds outside ApolloCrossDev. |
| `UPDATES=none` | Say the toolchain is up to date. |

Run the check again after an install or update, until it reports no
`PROBLEM=` line.

**`APOLLOCROSSDEV`:** the project lives outside `ApolloCrossDev/Projects/`,
so the Makefile needs it. If the check notes it is unset, offer to add
`export APOLLOCROSSDEV="<ACD_ROOT>"` to `~/.zshrc` (macOS) or `~/.bashrc`
(Linux), next to `AMIGAHOST` (the V4's IP address, needed for upload; ask
for it if that is missing too). Change the file only with the user's
consent. For this session, pass it on the command line:
`APOLLOCROSSDEV=<ACD_ROOT> make compile`.

## 5. Makefile (guided setup)

Copy `<ACD_ROOT>/Projects/_makefiles/Makefile` and change only:

| Line | Set to |
|---|---|
| `PROJECT_NAME` | the name |
| `C_INCL_NDK` | the `ndk39-include` line: AmigaOS 3.9 is a target, so a function that 3.9 lacks gives a compile error instead of a crash on 3.9 (`KB toolchain/target-os-headers.md`) |
| `C_COMPILER` | the `m68k-amigaos-g++` line for C++; the template does not collect `.cpp` files, so add them as `KB toolchain/project-makefile.md` says |

Keep `APOLLOLIB`, `C_OPTIONS` and `S_FLAGS` as they are.

## 6. The starting program (guided setup)

Copy one file from this skill's `assets/` to `main.c` and replace
`@PROJECT@`, `@WHAT@` and `@TARGETS@` (core, model, target OS):

| Mode | File |
|---|---|
| os-friendly | `assets/main-os-friendly.c` |
| os-takeover | `assets/main-os-takeover.c` |

The takeover programs leave the display takeover open on purpose: the KB
doesn't document it yet (`KB os/os-takeover.md`). Tell the user, and don't
fill it in from general Amiga knowledge.

Copy `assets/gitignore` to `.gitignore`.

## 7. Build it (guided setup)

Build as the apollo-build skill describes (`KB skills/apollo-build/SKILL.md`):
`make compile`. It must end with no errors and no warnings before you
continue.

## 8. Hand over

- Show the user the files you made and, for a guided setup, the build
  result.
- Offer a first commit; commit only when they agree.
- Tell them how to work from here: open the project folder in their agent,
  which now reads AKB first; `git submodule update --remote ApolloKnowledgeBase`
  brings in newer AKB content when they want it.
