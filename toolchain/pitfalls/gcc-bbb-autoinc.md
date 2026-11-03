---
title: GCC 6.5 bbb pass counts a post-increment twice
type: pitfall
owner: TuKo1982
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [toolchain]
applies_to:
  core: "any"
  os: [any]
tags: [gcc, bbb, optimizer, autoincrement, miscompile]
related:
  - toolchain/compiler-variants.md
  - toolchain/c-compiler-options.md
sources:
  - "TuKo1982, 68080 compilation and optimisation guide (2026-10-30), section 9.2"
  - "github.com/WDrijver/ApolloCrossDev pull request #5 (merged on 2026-11-03)"
  - "github.com/WDrijver/ApolloCrossDev GCC-6.50-Dev-Linux.sh, GCC-6.50-Stable-Linux.sh (2026-11-03)"
---

## Symptom

C code like `p + (p[0] == 'f' ? 3 : 2)` returns a pointer one byte too far,
at `-O2`.

## Cause

Bebbo's bbb optimizer pass (`-fbbb=i`, auto-increment) turns it into
`cmp.b #N,(a0)+` / Scc / `pea (3,a0,d0.w)`, which counts the post-increment
twice. The bug is in GCC 6.5 as built by ApolloCrossDev. The fix,
ApolloCrossDev pull request #5, was merged on 2026-11-03. GCC-6.50-Dev and
GCC-6.50-Stable apply it; GCC-6.50-Base does not.

## Wrong

```c
const char *skip(const char *p)
{
    return p + (p[0] == 'f' ? 3 : 2);   /* may be miscompiled at -O2 */
}
```

## Right

Use GCC-6.50-Dev or GCC-6.50-Stable installed on or after 2026-11-03. With
GCC-6.50-Base or an older install:

- check the generated code (see Detection), and
- rewrite the expression so the test and the addition are separate, and
  check the generated code again.

```c
const char *skip(const char *p)
{
    int n = 2;
    if (p[0] == 'f')
        n = 3;
    return p + n;
}
```

## Detection

Compile with `-S` and grep the assembly for `cmp.b #N,(aN)+` followed by an
Scc.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| Miscompile as described | (M) | any | Real project code, `-S` output |
| Fix in ApolloCrossDev PR #5, applied by the Dev and Stable scripts | (SRC) | any | Pull request, install scripts |
