---
name: apollo-new-project
description: Set up a new Apollo V4 software project (game, demo, tool, application, library, driver) as its own git repository in which every AI agent uses ApolloKnowledgeBase as its central source of Apollo V4 knowledge, then check, install or update ApolloCrossDev, and create the Makefile and a starting program for os-friendly or os-takeover mode that builds without warnings. Use when the user wants to start, create, scaffold or set up a new program or project for the Apollo V4, Vampire V4, 68080 or SAGA, pastes the "Start Apollo V4 Project" prompt from apolloknowledgebase.com, or wants an existing folder of Apollo code prepared for AI-assisted work.
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

## 2. Create the repository with AKB

In `<where>/<name>`, which must not exist yet or be empty:

```sh
git init
git submodule add https://github.com/ApolloTeam-dev/ApolloKnowledgeBase ApolloKnowledgeBase
```

If the folder already holds code, don't overwrite anything: add only what is
missing and show the user what you would change.

## 3. Make AKB the agents' central source

These files make every agent that opens the project read AKB first.

- **`AGENTS.md`** (read by most agents): from `KB templates/repo/AGENTS.md`.
  Fill in every `<placeholder>` from step 1, remove the template's HTML
  comments.
  - **Build and test:** `make compile` to build, `make` to build and upload
    to the V4 at `$AMIGAHOST`.
  - **Relevant knowledge base areas:** pick from the table in
    `KB AGENTS.md` section 3. Always `toolchain/`; `os/os-takeover.md` and
    `core/` for os-takeover; the SAGA folders that the program will use;
    `toolchain/apollolib/` with ApolloLib.
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

## 4. ApolloCrossDev: check, install or update

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

## 5. Makefile

Copy `<ACD_ROOT>/Projects/_makefiles/Makefile` and change only:

| Line | Set to |
|---|---|
| `PROJECT_NAME` | the name |
| `C_INCL_NDK` | NDK 3.2 (default), or the `ndk39-include` line when AmigaOS 3.9 is a target (`KB toolchain/target-os-headers.md`) |
| `APOLLOLIB` | keep it, or put `#` before it without ApolloLib |
| `C_COMPILER` | the `m68k-amigaos-g++` line for C++; the template does not collect `.cpp` files, so add them as `KB toolchain/project-makefile.md` says |

Keep `C_OPTIONS` and `S_FLAGS` as they are.

## 6. The starting program

Copy one file from this skill's `assets/` to `main.c` and replace
`@PROJECT@`, `@WHAT@` and `@TARGETS@` (core, model, target OS):

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

Build as the apollo-build skill describes (`KB skills/apollo-build/SKILL.md`):
`make compile`. It must end with no errors and no warnings before you
continue.

## 8. Hand over

- Show the user the files you made and the build result.
- Offer a first commit; commit only when they agree.
- Tell them how to work from here: open the project folder in their agent,
  which now reads AKB first; `git submodule update --remote ApolloKnowledgeBase`
  brings in newer AKB content when they want it.
