---
name: akb-lesson
description: Write down what an Apollo V4 project learned as a lesson for ApolloKnowledgeBase, show it to the developer and, with their approval, submit it as a pull request or issue. Use when the developer says a project, release or milestone is done, asks for a summary or retrospective, or when something the agent assumed about the 68080, SAGA, ApolloOS, AmigaOS on V4 or ApolloCrossDev turned out wrong (offer it right away then, while the details are fresh).
---

# akb-lesson

Carry what a project learned back into ApolloKnowledgeBase, where every
later agent finds it once it is distilled.

**The knowledge base (KB):** the project's `ApolloKnowledgeBase/`
submodule, or the repository this skill is in (two folders above this
file). KB paths below are relative to its root. The rules behind this skill
are `KB AGENTS.md` section 8 and `KB CONTRIBUTING.md` section 7.

## 1. Offer, don't impose

Offer the lesson in one or two sentences and say what it would contain.
Write it only when the developer wants it. Nothing is submitted without
their approval of the final text.

## 2. Gather

- The project's `AGENTS.md`: name, target core, model, OS, mode.
- `git log` since the start or the last release, and the conversation.
- Above all: **what the agent got wrong**, especially the assumptions from
  `KB AGENTS.md` section 2 (68060 habits on the 68080, classic chipset
  habits on SAGA, generic GCC habits on ApolloCrossDev), and what fixed it.
- Measurements, with how they were made: core, test program, counters,
  before and after numbers.
- Which KB files helped, and which were wrong or missing.

## 3. Draft

Create `lessons/YYYY-MM-<project-name>.md` (year and month of today,
kebab-case project name) from `KB templates/files/lesson.md`:

| Field | Value |
|---|---|
| `type`, `status` | `lesson`, `draft` (a lesson stays draft) |
| `owner` | the developer's GitHub login (`gh api user -q .login`, or ask) |
| `origin` | `ai-assisted` |
| `basis` | only what the evidence is: `measured`, `core-developer`, `source-code`, `official`, `other` |
| `applies_to` | from the project's `AGENTS.md`; the core in the KB notation (`"Core 12841"`, `"Core 12500+"`) |
| `sources` | the project repository and commits, test programs, people and dates |

Fill every section of the template; remove every `<placeholder>`. Be
specific and honest in "What the AI got wrong": concrete mistakes with
examples. Every claim in "Evidence" names its source tag ((G), (M),
(official), (SRC)), the core and the method; a claim without evidence goes
under "What went wrong" as an observation, not as a fact. Under
"Candidates for distillation", name the KB file to create or change
(`core/pitfalls/...`, `toolchain/best-practices/...`).

## 4. Check

In the KB clone, with Python and `pyyaml`:

```sh
python tools/check_frontmatter.py
python tools/check_links.py
```

Fix what they report.

## 5. Show and approve

Show the complete lesson to the developer. Change it until they approve it.

## 6. Submit, in one of three ways

**Pull request (preferred).** In the project's `ApolloKnowledgeBase/`
submodule:

```sh
used=$(git rev-parse HEAD)                # the commit the project uses
git fetch origin main
git switch -c lesson/YYYY-MM-<project-name> origin/main
# add the lesson file, then:
git add lessons/YYYY-MM-<project-name>.md
git commit -m "Lesson: <project name>"
gh pr create --repo ApolloTeam-dev/ApolloKnowledgeBase --base main \
  --title "Lesson: <project name>" --body "<two lines on what it covers>"
git switch --detach "$used"               # back to the project's commit
```

Without write access, `gh pr create` offers to push to a fork; accept.
Afterwards `git status` in the project must not show the submodule as
changed.

**The ApolloKnowledgeBase-Manager.** At
https://apolloknowledgebase.com/manager/ the developer signs in with GitHub
and uses "Submit a lesson"; paste the approved text there.

**Issue form.** Open an issue with the "Submit a lesson" form on
github.com/ApolloTeam-dev/ApolloKnowledgeBase and paste the lesson.

Tell the developer the pull request or issue link. A maintainer merges it;
the team later distills it into best practices, pitfalls or guides.
