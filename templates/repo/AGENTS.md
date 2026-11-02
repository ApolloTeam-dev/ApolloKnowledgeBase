# AGENTS.md: <repository name>

<!-- Template from ApolloKnowledgeBase/templates/repo/AGENTS.md.
     Replace every <placeholder> and delete these comments. -->

## Read first

This repository targets the Apollo V4 platform. Before doing anything else,
read `ApolloKnowledgeBase/AGENTS.md` and follow it. It explains the platform,
the assumptions you must not make, and which knowledge base files to read for
your task. Paths in that file are relative to `ApolloKnowledgeBase/`.

If `ApolloKnowledgeBase/` is empty, the submodule has not been initialized.
Ask the user to run `git submodule update --init` instead of proceeding
without it.

## This repository

- **What it is:** <one or two sentences, e.g. "the ApolloOS kernel and core
  libraries" or "a 2D platform game">
- **Kind:** <OS component | application | tool | game | library>
- **Target:** core revision <...>
- **Target OS:** <one or more: ApolloOS R10, AmigaOS 3.9, AmigaOS 3.2>
- **Languages:** <one or more: C, C++, 68080 assembly>

## Relevant knowledge base areas

<!-- List the folders most relevant to this repository, so the agent reads
     them without being told each time. -->

- `ApolloKnowledgeBase/<folder>/`
- `ApolloKnowledgeBase/<folder>/`

## Build and test

```sh
<exact build command with ApolloCrossDev>
<exact test command, if any>
```

Build and fix all errors and warnings before presenting code.

## Repository-specific rules

<!-- Only rules that apply to this repository alone. Anything useful for
     other Apollo projects belongs in ApolloKnowledgeBase instead. -->

- <rule>

## Knowledge base feedback

When you find something missing or wrong in ApolloKnowledgeBase while working
here, tell the user and offer to draft a change following
`ApolloKnowledgeBase/CONTRIBUTING.md`.
