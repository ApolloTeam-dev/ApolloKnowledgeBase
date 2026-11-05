# Contributing to ApolloKnowledgeBase

This file is the single source of truth for how ApolloKnowledgeBase files are
structured, written and reviewed. It applies to humans and AI agents alike.
AI agents creating or editing files in this repository MUST follow it.

---

## 1. Golden rules

1. **Document the differences.** Do not re-document classic AmigaOS or AROS
   behavior that is unchanged. Focus on where ApolloOS, the 68080 and the SAGA
   chipset differ, extend, or break expectations. Exception: official
   documents (section 11) are converted in full.
2. **One topic per file.** If a file covers two things, split it.
3. **Be exact.** Give register offsets, bit meanings, cycle counts, return
   values and version numbers. Never write "see the manual".
4. **Every file has an owner.** No owner, no merge.
5. **Claims need evidence.** Performance claims need measurements; hardware
   facts need a source (spec, source code, or a test on real hardware).
6. **Code must compile.** Every code block marked as compilable is built in CI.

---

## 2. Where things go

The knowledge base has four pillars: **core** (the FPGA core: 68080 CPU and
SAGA chipset), **hardware** (the V4 boards), **os** (the operating systems)
and **toolchain** (ApolloCrossDev). Each pillar holds
reference files plus its own `best-practices/` and `pitfalls/`. Knowledge
that spans pillars goes in the cross-cutting folders.

```text
core/                       68080 CPU and SAGA chipset
├── cpu-68080/              ISA, AMMX, pipeline, timing, 68060 differences
├── saga-video-isabelle/    video chip
├── saga-audio-arne/        audio chip
├── saga-dma-anni/          DMA chip
├── saga-3d-maggie/         3D chip
├── best-practices/
└── pitfalls/
hardware/                   the V4 boards
├── v4-generic/             shared by all V4 models: memory map, common connectors
├── v4-standalone/          V4 Standalone (SA)
├── v4-unicorn/             V4 UniCorn (UNI, A6000)
├── v4-icedrake/            V4 IceDrake (ICE)
├── v4-manticore/           V4 Manticore (MC)
├── v4-firebird/            V4 Firebird (FB)
├── best-practices/
└── pitfalls/
os/                         ApolloOS R10, AmigaOS 3.9 and 3.2 on Apollo V4
├── *.md                    running on V4, OS takeover, ApolloOS specifics
├── libraries/ devs/ filesys/ commands/ datatypes/   ApolloOS components
├── best-practices/
└── pitfalls/
toolchain/                  ApolloCrossDev
├── *.md                    components, setup, options, syntax
├── best-practices/
└── pitfalls/
guides/                     step-by-step how-tos
examples/                   small, compiling, tested code
conventions/                team coding style and process
lessons/                    project retrospectives
```

| Folder | `type` |
|---|---|
| `core/`, `hardware/`, `os/`, `toolchain/` and their subfolders | reference |
| `<pillar>/best-practices/` | best-practice |
| `<pillar>/pitfalls/` | pitfall |
| `guides/` | guide |
| `examples/` | example |
| `conventions/` | convention |
| `lessons/` | lesson |

Not content: `templates/` (file, repo and seed templates), `sources/`
(original documents for document intake, section 11), `skills/` (AI agent
skills, step 2), `evals/` (AI benchmarks, step 5), `tools/` (CI scripts).

Each chip folder keeps its register map in `registers.md` inside that folder.
The official SAGA register documentation is generated into
`core/saga-registers/` (document intake, section 11); the chip folders link
to it.

`core/` is the FPGA core, the same on every V4 model. `hardware/` is the
board: connectors, headers, memory and what differs per model. Knowledge that
holds for all models goes in `hardware/v4-generic/`; a model folder holds
only what is specific to that model. Common abbreviations: SA (Standalone),
UNI or A6000 (UniCorn), ICE (IceDrake), MC (Manticore), FB (Firebird).

A best practice or pitfall goes in the pillar it is about. One that spans
pillars goes in the pillar where a developer would look first, with
`related:` links to the others.

Toolchain best practices still need evidence: show the compiler flags or
settings, and compare the generated code or measured speed against a baseline.

### Target OS and OS bugs

Apollo V4 software targets the V4 hardware, running ApolloOS R10, AmigaOS
3.9 or AmigaOS 3.2, often more than one. Hardware knowledge applies whatever
the OS. Guidelines for running well on V4 under each OS go in
`os/apolloos-and-amigaos-on-v4.md`.

AmigaOS is the leading reference. When something works on AmigaOS but fails
on ApolloOS, that is an ApolloOS bug: report it as an issue in
github.com/ApolloTeam-dev/ApolloOS.R10 so it gets fixed in the source. Do not
document a workaround in this knowledge base.

Everything else is welcome in `os/best-practices/` and `os/pitfalls/`, with
`applies_to.os` set accordingly:

- valid on both ApolloOS and AmigaOS on V4: `os: [any]`
- a trap in AmigaOS 3.9 or 3.2 itself: for example `os: [amigaos-3.2]`
- about an ApolloOS-only feature: `os: [apolloos-r10]`

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

How to enter and leave a takeover goes in `os/os-takeover.md`, with its best
practices and pitfalls in `os/best-practices/` and `os/pitfalls/`. Direct
hardware programming during a takeover goes in `core/`. Both use
`mode: [os-takeover]` in their frontmatter.

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
origin: human                             # required, see allowed values
basis: [measured, core-developer]         # optional, kinds of source used
components: [cpu-68080, saga-video-isabelle]  # required, see allowed values
applies_to:                               # required
  core: "Core 12841+"                     # required, see allowed values
  os: [any]                               # see allowed values
  mode: [os-takeover]                     # optional, see allowed values
  board: [v4-standalone]                  # optional, see allowed values
last_verified: 2026-10-31                 # required once status is verified
tags: [ammx, graphics, blitting]          # optional, free keywords for search
related:                                  # optional, paths to related files
  - core/pitfalls/ammx-alignment.md
sources:                                  # required for reference, best-practice
  - "Apollo core spec, section X"
superseded_by:                            # only when status is deprecated
generated_from:                           # only for document intake, section 11
---
```

### Allowed values

The machine-readable form of these rules is `tools/schema.json`: CI and the
ApolloKnowledgeBase-Manager wizard both read it. Change a rule there and here
together.

- **type:** `reference`, `guide`, `convention`, `best-practice`, `pitfall`,
  `example`, `lesson`
- **status:**
  - `draft`: not yet reviewed; AI agents treat with caution
  - `reviewed`: owner has reviewed content
  - `verified`: tested on real Apollo V4 hardware on the stated core revision
  - `deprecated`: no longer valid; must name `superseded_by`
- **origin:**
  - `human`: written by a person
  - `ai-assisted`: any AI-drafted content; can only move beyond `draft`
    after a human review
  - `official`: from official Apollo documentation through document intake
    (section 11); maintainers only, CI checks that the owner is a maintainer
- **basis:** optional list of the kinds of source the file relies on, from
  the highest rank to the lowest (see "Sources and their rank" below):
  `core-developer`, `measured`, `official`, `source-code`, `other`
- **components:** `cpu-68080`, `saga-video-isabelle`, `saga-audio-arne`,
  `saga-dma-anni`, `saga-3d-maggie`, `libraries`, `devs`, `filesys`,
  `commands`, `datatypes`, `toolchain`, `hardware`, `general`
- **applies_to.core:** the core revisions the file is valid for:
  - `any`: valid on every core
  - `Core 12841`: one core
  - `Core 12830-12840`: a range, both ends included
  - `Core 12841+`: this core and later
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
- **applies_to.board:** optional list of V4 models the file is valid for.
  Leaving it out means `any`.
  - `any`: all models; not combined with others
  - `v4-standalone`, `v4-unicorn`, `v4-icedrake`, `v4-manticore`,
    `v4-firebird`

### Sources and their rank

Mark where each fact comes from with a tag right after it, and list the kinds
in `basis`. When sources disagree, the higher rank wins:

| Rank | Tag | `basis` | Source |
|---|---|---|---|
| 1 | **(G)** | `core-developer` | Gunnar, the core developer. Name the date: "(G, 2026-10-29)" |
| 2 | **(M)** | `measured` | Measured on real V4 hardware. State the core and the method (counters, test program) |
| 3 | **(official)** | `official` | The 68080 PRM and other official Apollo documents |
| 4 | **(SRC)** | `source-code` | Read from source code (ApolloOS, a library, ApolloCrossDev) |
| 5 | | `other` | Anything else, such as forum posts or apollo-core.com |

Within the same rank, the newer core wins. Facts tied to a core say so in the
text ("on Core 12841") and in `applies_to.core`. A later core can change
them: measure again on yours.

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

Lessons carry what a project learned back into the knowledge base.

1. **Offer.** AI agents offer a lesson when the developer says a project, a
   release or a milestone is done, or asks for a summary, and right away when
   they find that an assumption from AGENTS.md section 2 was wrong.
2. **Draft.** The agent writes `lessons/YYYY-MM-project-name.md` from
   `templates/files/lesson.md`, with the evidence (source, core, method) for
   every measured claim, and shows it to the developer. Nothing is submitted
   without the developer's approval.
3. **Submit.** Either way works:
   - **Pull request (preferred):** in the knowledge base clone (the
     `ApolloKnowledgeBase/` submodule of the project), on a new branch
     `lesson/YYYY-MM-project-name`, commit the lesson and open a PR with
     `gh pr create`. Without write access, `gh` offers to use a fork. Then
     return the submodule to the commit the project uses
     (`git submodule update ApolloKnowledgeBase` in the project).
   - **Issue form:** open an issue with the "Submit a lesson" form on
     github.com/ApolloTeam-dev/ApolloKnowledgeBase and paste the lesson. A
     maintainer turns it into a file.
4. **Review.** CI checks the file; a maintainer merges it. Lessons stay
   `draft` and are not read by AI agents by default: one project's experience
   is not yet a rule.
5. **Distill.** The team turns the lesson's "Candidates for distillation"
   into files in the pillars' `best-practices/` or `pitfalls/`, or into
   `guides/`, and links the lesson in their `sources`. From then on every
   agent finds it.
6. Distilled lessons stay in place as history.

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

- `check_frontmatter.py`: required fields, allowed values (including the
  `applies_to.core` notation and `basis`), file naming,
  type matches folder, no leftover `<placeholder>` text, `related`,
  `superseded_by` and `generated_from` paths exist, `official` files are
  owned by a maintainer
- `check_links.py`: internal markdown links point to existing files
- `check_owners.py`: every owner is an existing GitHub account
- Markdown lint (rules in `.markdownlint.jsonc`)
- `intake/*.py --check`: files generated by document intake match their
  original in `sources/official/` (section 11)
- Compilation of all `kb:compile` code blocks with ApolloCrossDev
  (GCC-6.50-Dev, flags as in its Makefile template; see
  `tools/compile-snippets.sh`)

On every merge to `main`, `generate_codeowners.py` regenerates
`.github/CODEOWNERS`. Fixed owners for files without frontmatter go in
`.github/CODEOWNERS.base`.

The `seed/`, `sources/` and `templates/` folders are excluded from content
checks.

Run the checks locally before opening a pull request:

```sh
pip install pyyaml
python tools/check_frontmatter.py
python tools/check_links.py
```

---

## 11. Document intake (maintainers only)

Official Apollo documentation, such as the Apollo 68080 Programmer's
Reference Manual, enters the knowledge base through document intake. Only
the maintainers (WDrijver and TuKo1982, the default owners in
`.github/CODEOWNERS.base`) use this route.

**The original document is leading**, unless the intake PR states otherwise.
Updates to the original are expected, and each one goes through the intake
steps again. Never edit generated files by hand: change the original and
regenerate.

### Steps

1. Add or update the original in `sources/official/`, in an editable format
   such as ODT. PDF is a last resort.
2. Convert it with a converter script in `tools/intake/`, one per document
   (for example `tools/intake/prm68080.py`). The script does the conversion,
   the optimization for AI and the split, so an update of the original is
   regenerated the same way. Use only the Python standard library.
3. The script splits the result into knowledge base files in the right
   pillar (see "Optimized for AI" below). Every generated file gets:
   - `origin: official`
   - `owner`: a maintainer
   - `status: draft`
   - `generated_from: sources/official/<file>`
4. Open a PR. The maintainer checks the conversion against the original and
   sets `status: reviewed` in a generated file when it is correct. The
   converter keeps that status as long as the file's content stays the same,
   and generates the file as `draft` again when its content changes.
5. On an update of the original: replace it in `sources/official/`, run the
   converter, and review the diff of the generated files in the PR. CI fails
   when the generated files do not match the original
   (`tools/intake/<script> --check`).

When the PR states that the Markdown becomes leading instead, leave out
`generated_from` and remove the original from `sources/official/`. From then
on, the files are edited like any other file.

### Optimized for AI

- Markdown files of at most ~400 lines, one topic per file. A large manual
  becomes a folder with an `index.md` that maps topics (for example
  mnemonics) to files.
- The same structure for every entry of the same kind, for example every
  instruction with syntax, operation, sizes, condition codes, encoding and
  cycles.
- Facts in tables: registers, opcodes, timing.
- No facts only in images. Describe every diagram or timing chart in text.
- Code blocks with a language tag, cross-references as `related:` links.
- Differences from the 68000/68060 or AmigaOS called out explicitly.
- Anything that did not convert cleanly is listed in the PR, not silently
  dropped.
