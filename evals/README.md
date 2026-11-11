# Benchmark evals

Step 5 of the AKB plan: measure how much the knowledge base improves AI
answers for Apollo V4 work, and catch regressions when the knowledge base, the
model or the question page changes.

The tasks are in the private repository `ApolloTeam-dev/ApolloKnowledgeBase-Tasks`.
They are private so that future models can't learn the answers from published
text. The runner lives here; the raw results (answers and transcripts) reveal
the tasks, so they stay in the git-ignored `build/evals/` and are never
committed.

## Question page: `question-page.mjs`

Each task's question is answered by Opus 5.5 in two conditions, one per
variant directory:

| Variant | Condition |
|---|---|
| `baseline` | Without the knowledge base: the question alone, with a short system prompt that names the platform and asks the model not to invent facts |
| `v1` | With the knowledge base: the real question page, `ask()` from ApolloKnowledgeBase-Manager `src/ask.js`, with a corpus built from this checkout |

Sonnet 5.5 grades each answer against the task's checklist, using structured
output:

- `pass`: every fact is in the answer and no wrong claim is made;
- `facts`: the share of facts found;
- `no_wrong`: no wrong claim made.

Only tasks with `status: reviewed` count. `--include-drafts` also runs drafts,
for pilots.

### Setup

- `~/ApolloKnowledgeBase-Tasks` and `~/ApolloKnowledgeBase-Manager` cloned, or
  their paths set in `AKB_TASKS` and `AKB_MANAGER`.
- `npm ci` done in the Manager.
- PyYAML installed for `python3`.
- The evals API key in the macOS Keychain. Its workspace has a spend limit.

  ```sh
  security add-generic-password -a akb-evals -s akb-evals-anthropic -w
  ```

### Running

```sh
node evals/question-page.mjs --variant v1 --dry-run        # what would run; no API calls
node evals/question-page.mjs --variant baseline --approve-harness   # first run, or after the runner or ask.js changed
node evals/question-page.mjs --variant v1 --only fpu-m68080-alone,dcache-line
```

- `--approve-harness` records a hash of the runner and the Manager files it
  uses. Pass it only after reviewing a change; without it, a changed harness
  refuses to run.
- A second run resumes: it runs only the (task, rep) pairs that have no
  result yet. `--reps N` runs every task N times.
- Results go to `build/evals/question-page/<variant>/`: `results.jsonl`,
  `traces/`, and `errors.jsonl` for attempts that failed.

The runner is built on the build-eval runner scaffold of Claude Code's
`claude-api` skill. That scaffold provides the resume, backoff, wall-clock
ceiling, served-model check and harness gate.

## Coding agent: `coding-agent.mjs`

Each task asks Claude Code (headless, `claude -p`, Opus 5.5) for a change to
a small Apollo V4 project. Every (task, rep) gets a fresh project folder with
the ApolloCrossDev Makefile template and the task's starting files, in one of
two conditions:

| Variant | Condition |
|---|---|
| `baseline` | Without the knowledge base: an `AGENTS.md` that states the target OS, the execution mode and the build command |
| `v1` | With the knowledge base: this checkout's HEAD as `ApolloKnowledgeBase/` in the project, `AGENTS.md` and `CLAUDE.md` as the apollo-new-project skill writes them, and the `akb` plugin |

Claude Code runs with an empty config folder (no user settings, memory or
plugins), without web tools, with file edits only inside the project and
Bash only for `make` and the ApolloCrossDev compiler tools. Each agent run
stops at $5.

Grading:

- `build`: `make` ends without errors and without warnings;
- `checks`: the task's regular expressions on the project files, or on the
  assembly GCC emits for a C file with the project's own flags;
- `facts` and `no_wrong`: Sonnet 5.5 grades the sources and the agent's
  final message against the task's checklist;
- `pass`: all of the above.

Setup as for the question page, plus ApolloCrossDev in `~/ApolloCrossDev`
(or `APOLLOCROSSDEV`) and Claude Code (`claude` on `PATH`, `AKB_CLAUDE`, or
the VS Code extension's binary). Results go to
`build/evals/coding-agent/<variant>/`, with each finished project in
`projects/`. Working folders are in `$TMPDIR/akb-evals-coding/`.

```sh
node evals/coding-agent.mjs --variant baseline --include-drafts --dry-run
node evals/coding-agent.mjs --variant v1 --only flac-flags,sprintf-32bit
```
