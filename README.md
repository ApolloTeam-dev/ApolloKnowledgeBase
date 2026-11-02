# ApolloKnowledgeBase

The curated knowledge base for software development on the Apollo V4
platform: the 68080 CPU, the SAGA chipset, ApolloOS and the ApolloCrossDev
toolchain.

It is written for two audiences at once: developers, and the AI coding agents
they work with. AI models know classic AmigaOS, AROS and the 68000–68060 well,
but not Apollo V4. This knowledge base fills that gap so AI-assisted code uses
the platform correctly and to its full potential.

---

## What's inside

| Folder | Contents |
|---|---|
| `core/` | 68080 CPU and the SAGA chips: Isabelle (video), Arne (audio), Anni (DMA), Maggie (3D) |
| `os/` | Running on V4 under ApolloOS R10, AmigaOS 3.9 and 3.2; ApolloOS internals (differences from AROS, libraries, devs, filesys, commands, datatypes) |
| `toolchain/` | ApolloCrossDev setup, options and syntax |
| `best-practices/` | How to write optimal code using all Apollo V4 features |
| `pitfalls/` | Known traps and how to avoid them |
| `guides/` | Step-by-step how-tos |
| `examples/` | Small, compiling, tested code |
| `conventions/` | Team coding style and process |
| `lessons/` | Project retrospectives |
| `templates/` | Templates for new knowledge base files, for code repositories, and for collecting seed content |
| `skills/`, `evals/`, `tools/` | AI agent skills, AI benchmarks, CI scripts |

Each file shows its owner, its status (`draft`, `reviewed`, `verified`,
`deprecated`) and which core revision, target OS and execution mode
(`os-friendly` or `os-takeover`) it applies to.

---

## Using it in a code repository

1. Add the knowledge base as a submodule in the repository root:

   ```sh
   git submodule add https://github.com/ApolloTeam-dev/ApolloKnowledgeBase.git ApolloKnowledgeBase
   ```

2. Copy `templates/repo/AGENTS.md` and `templates/repo/CLAUDE.md` to the
   repository root and fill in the placeholders.

3. To pick up the latest knowledge base changes:

   ```sh
   git submodule update --remote ApolloKnowledgeBase
   ```

AI agents working in that repository then find and follow the knowledge base
automatically.

---

## Contributing

Everyone in the Apollo community can contribute. Read `CONTRIBUTING.md` for
the file format and review process. The most valuable contributions are:

- Places where ApolloOS, the 68080 or SAGA differ from what developers (and
  AI models) expect
- Measured optimization techniques for `best-practices/`
- Bugs you hit and how you fixed them, for `pitfalls/`

AI agents: start with `AGENTS.md`.
