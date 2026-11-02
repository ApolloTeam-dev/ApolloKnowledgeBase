# Contributing to ApolloKnowledgeBase

This file is the single source of truth for how ApolloKnowledgeBase files are
structured, written and reviewed. It applies to humans and AI agents alike.
AI agents creating or editing files in this repository MUST follow it.

---

## 1. Golden rules

1. **Document the differences.** Do not re-document classic AmigaOS or AROS
   behavior that is unchanged. Focus on where ApolloOS, the 68080 and the SAGA
   chipset differ, extend, or break expectations.
2. **One topic per file.** If a file covers two things, split it.
3. **Be exact.** Give register offsets, bit meanings, cycle counts, return
   values and version numbers. Never write "see the manual".
4. **Every file has an owner.** No owner, no merge.
5. **Claims need evidence.** Performance claims need measurements; hardware
   facts need a source (spec, source code, or a test on real hardware).
6. **Code must compile.** Every code block marked as compilable is built in CI.

---

## 2. Where things go

| Folder | Contains | Typical `type` |
|---|---|---|
| `core/cpu-68080/` | ISA, AMMX, pipeline, timing, 68060 differences | reference |
| `core/saga-video-isabelle/` | Video chip: modes, registers, features | reference |
| `core/saga-audio-arne/` | Audio chip | reference |
| `core/saga-dma-anni/` | DMA chip | reference |
| `core/saga-3d-maggie/` | 3D chip | reference |
| `os/` | `apolloos-and-amigaos-on-v4.md` (running on V4 under any target OS), `os-takeover.md` (entering and leaving a takeover), `apolloos-specific-on-v4.md` (ApolloOS only: ApolloOS features and differences from AROS) | reference |
| `os/libraries/` | ApolloOS API routines (Libs:) | reference |
| `os/devs/` | ApolloOS device drivers (Devs:) | reference |
| `os/filesys/` | ApolloOS filesystem handlers (L:) | reference |
| `os/commands/` | ApolloOS shell commands (C:) | reference |
| `os/datatypes/` | ApolloOS datatypes (Classes:) | reference |
| `toolchain/` | ApolloCrossDev (github.com/WDrijver/ApolloCrossDev), the single toolchain for all Apollo development: components, setup, compiler and assembler options, syntax | reference |
| `guides/` | Step-by-step how-tos for common tasks | guide |
| `conventions/` | Coding style, toolchain, build, testing, PRs | convention |
| `best-practices/` | How to write optimal code using all V4 features | best-practice |
| `pitfalls/` | Known traps and how to avoid them | pitfall |
| `examples/` | Small, compiling, tested code snippets | example |
| `lessons/` | Raw project retrospectives | lesson |
| `templates/` | File templates per type (`files/`), code-repo templates (`repo/`), seed collection template (`seed/`) | — |
| `skills/` | AI agent skills (see step 2) | — |
| `evals/` | Benchmark tasks for AI evaluation (see step 5) | — |
| `tools/` | CI scripts and generators | — |

Each chip folder keeps its register map in `registers.md` inside that folder.

`best-practices/` and `pitfalls/` are split into subfolders that mirror the
reference areas, so related knowledge is easy to find:

```text
best-practices/
├── core/           # CPU and chipset-level optimization
└── toolchain/      # ApolloCrossDev: flags and settings for optimal output
pitfalls/
├── core/
└── toolchain/
```

Toolchain best practices still need evidence: show the compiler flags or
settings, and compare the generated code or measured speed against a baseline.

### Target OS and OS bugs

Apollo V4 software targets the V4 hardware, running ApolloOS R10, AmigaOS
3.9 or AmigaOS 3.2, often more than one. Hardware knowledge applies whatever
the OS. Guidelines for running well on V4 under each OS go in
`os/apolloos-and-amigaos-on-v4.md`.

There are no `best-practices/os/` or `pitfalls/os/` folders. Where ApolloOS
behaves differently from AmigaOS in a way that breaks programs, that is an
ApolloOS bug: report it as an issue in
github.com/ApolloTeam-dev/ApolloOS.R10 so it gets fixed in the source. Do not
document a workaround in this knowledge base.

### Execution mode

Every Apollo V4 program starts from an OS and returns to it, in one of two
execution modes:

- **os-friendly:** uses AmigaOS/ApolloOS calls where available. Direct SAGA
  access is allowed at the discretion and responsibility of the developer.
  Typical for applications, tools and OS components.
- **os-takeover:** disables multitasking with `Forbid()`, uses only basic OS
  calls such as `AllocMem()`/`FreeMem()` and `Open()`/`Close()`, and focuses
  on direct hardware access to the 68080 and the SAGA chipset. On exit it
  restores multitasking and the Workbench screen. Typical for games and
  demos.

How to enter and leave a takeover goes in `os/os-takeover.md`. Takeover best
practices and pitfalls go in `best-practices/core/` and `pitfalls/core/`,
with `mode: [os-takeover]` in their frontmatter.

---

## 3. File naming

- Lowercase kebab-case, `.md` extension: `ammx-pixel-blending.md`
- Name by topic, not by author or date (exception: `lessons/`, see section 7)
- Keep files under ~400 lines. Larger topics become a folder with an
  `index.md` and one file per subtopic.

---

## 4. Frontmatter

Every file starts with YAML frontmatter. CI rejects files with missing
required fields or invalid values.

```yaml
---
title: AMMX pixel blending                # required, human-readable
type: best-practice                       # required, see allowed values
owner: github-handle                      # required, one GitHub handle
status: draft                             # required, see allowed values
origin: human                             # required: human | ai-assisted
components: [cpu-68080, saga-video-isabelle]  # required, see allowed values
applies_to:                               # required
  core: "<core revision or range>"        # use the team's revision notation
  os: [any]                               # see allowed values
  mode: [os-takeover]                     # optional, see allowed values
last_verified: 2026-10-31                 # required once status is verified
tags: [ammx, graphics, blitting]          # optional, free keywords for search
related:                                  # optional, paths to related files
  - pitfalls/ammx-alignment.md
sources:                                  # required for reference, best-practice
  - "Apollo core spec, section X"
superseded_by:                            # only when status is deprecated
---
```

### Allowed values

- **type:** `reference`, `guide`, `convention`, `best-practice`, `pitfall`,
  `example`, `lesson`
- **status:**
  - `draft`: not yet reviewed; AI agents treat with caution
  - `reviewed`: owner has reviewed content
  - `verified`: tested on real Apollo V4 hardware on the stated core revision
  - `deprecated`: no longer valid; must name `superseded_by`
- **origin:** `human`, or `ai-assisted` (any AI-drafted content). AI-assisted
  files can only move beyond `draft` after a human review.
- **components:** `cpu-68080`, `saga-video-isabelle`, `saga-audio-arne`,
  `saga-dma-anni`, `saga-3d-maggie`, `libraries`, `devs`, `filesys`,
  `commands`, `datatypes`, `toolchain`, `general`
- **applies_to.os:** a list of target operating systems the file is valid for:
  - `any`: valid whatever the OS (all hardware facts); not combined with others
  - `apolloos-r10`: ApolloOS R10, the current 10.x versions from ApolloTeam-dev
  - `amigaos-3.9`: AmigaOS 3.9 (Haage & Partner)
  - `amigaos-3.2`: AmigaOS 3.2, the current 3.2.x versions from Hyperion

  When a fact depends on a specific version (for example "fixed in 10.2"),
  state that in the body.
- **applies_to.mode:** optional list of execution modes the file is valid
  for (see section 2). Leaving it out means `any`.
  - `any`: valid in both modes; not combined with others
  - `os-friendly`: only for programs that keep the OS running
  - `os-takeover`: only for programs that take over the machine

---

## 5. Templates per type

Start every new file from a template in `templates/files/`. Each one has the
frontmatter and the required sections for its type:

| Type | Template |
|---|---|
| reference | `templates/files/reference.md` |
| guide | `templates/files/guide.md` |
| convention | `templates/files/convention.md` |
| best-practice | `templates/files/best-practice.md` |
| pitfall | `templates/files/pitfall.md` |
| example | `templates/files/example.md` |
| lesson | `templates/files/lesson.md` |

Keep the section headings exactly as in the template. AI agents and CI rely
on them. Remove placeholder text and any optional frontmatter field you
don't use.

---

## 6. Writing style

- Write for a reader who knows classic Amiga programming well but knows
  nothing about Apollo V4. That describes most AI models.
- Short sentences. Exact numbers. Units always stated.
- Put the most important fact first.
- Use "DO" / "DON'T" for rules; AI agents follow these reliably.
- Code blocks always carry a language tag (`asm`, `c`, `cpp`, `sh`). The
  assembler syntax and build settings are documented once in
  `toolchain/`, not repeated in every file.
- Code blocks that should compile in CI are tagged with a comment on the
  first line: `; kb:compile` (assembly) or `// kb:compile` (C, C++).
  CI compiles each block on its own to an object file (no linking), so a
  `kb:compile` block must be a complete source file with its own includes.

---

## 7. Lessons lifecycle

1. After a project, write `lessons/YYYY-MM-project-name.md` (AI may draft).
2. Lessons stay `draft` and are not read by AI agents by default.
3. Periodically, the team distills recurring points into `best-practices/`,
   `pitfalls/` or `guides/`, and links the lesson in their `sources`.
4. Distilled lessons stay in place as history.

---

## 8. Ownership and review

- The `owner` field is the source of truth for ownership.
- `tools/` contains a script that generates `.github/CODEOWNERS` from all
  `owner` fields, so GitHub requests the owner's review automatically.
  Do not edit CODEOWNERS by hand.
- New files have no owner entry in CODEOWNERS until they are merged. Until
  then, the repository maintainers are the default reviewers.
- All changes go through pull requests, including AI-drafted ones.
- Status changes (`draft` → `reviewed` → `verified`) require owner approval.
- To transfer ownership, change the `owner` field in a PR approved by both
  the old and the new owner.

---

## 9. Deprecation

Do not delete outdated files. Set `status: deprecated`, fill in
`superseded_by`, and add one line at the top of the body explaining why.

---

## 10. CI checks

Every pull request runs (scripts in `tools/`):

- `check_frontmatter.py`: required fields, allowed values, file naming,
  type matches folder, no leftover `<placeholder>` text, `related` and
  `superseded_by` paths exist
- `check_links.py`: internal markdown links point to existing files
- `check_owners.py`: every owner is an existing GitHub account
- Markdown lint (rules in `.markdownlint.jsonc`)
- Compilation of all `kb:compile` code blocks with ApolloCrossDev
  (GCC-6.50-Dev, flags as in its Makefile template; see
  `tools/compile-snippets.sh`)

On every merge to `main`, `generate_codeowners.py` regenerates
`.github/CODEOWNERS`. Fixed owners for files without frontmatter go in
`.github/CODEOWNERS.base`.

The `seed/` and `templates/` folders are excluded from content checks.

Run the checks locally before opening a pull request:

```sh
pip install pyyaml
python tools/check_frontmatter.py
python tools/check_links.py
```
