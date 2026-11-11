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
