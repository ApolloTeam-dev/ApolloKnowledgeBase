---
title: A pooled realloc that copies the old size overwrites the pool when shrinking
type: pitfall
owner: WDrijver
status: draft
origin: ai-assisted
basis: [measured, source-code]
components: [libraries]
applies_to:
  core: "any"
  os: [apolloos-r10, amigaos-3.9, amigaos-3.2]
tags: [memory, pools, realloc, freepooled, alert, freetype, porting]
related:
  - os/pitfalls/library-globals-shared-between-tasks.md
sources:
  - "ApolloOS-Port commit aac8859 (2026-11-18): external/freetype-2.10.0/builds/aros/src/base/ftsystem.c"
  - "Hardware test on a V4 (DEV card, ApolloOS R10 ROM), 2026-11-18"
---

## Symptom

A program that uses a library with its own memory functions on top of an
exec pool fails some time after the real error, in an unrelated `FreePooled`:
Recoverable Alert `0x0100000F` "Memory header not located", with the PC in
exec's pool manager (`PoolManagerAlert`). The task that shows the alert is
often a helper task, and its parent then waits forever for it.

On ApolloOS R10 before the fix, System/FTManager raised this alert within
5 seconds of every start, in the task that scans `Fonts:TrueType` with
freetype2.library.

## Cause

Ported code often maps a C library's `realloc` callback onto exec memory as
"allocate the new size, copy, free the old block". The AROS port of FreeType
2.10 (`builds/aros/src/base/ftsystem.c`, `ft_realloc`) copied `cur_size`
bytes, the size of the *old* block. FreeType also calls realloc to make a
block smaller. Then the copy writes past the end of the new, smaller block
and overwrites the header of the next chunk in the same puddle.
`AllocPooled` gives no padding that would hide this. Nothing fails at the
moment of the overwrite; the alert comes when the damaged chunk is freed.

## Wrong

```c
void *my_realloc(APTR pool, void *block, ULONG cur_size, ULONG new_size)
{
    void *n = my_alloc(pool, new_size);
    if (n) {
        CopyMem(block, n, cur_size);     /* too much when new_size < cur_size */
        my_free(pool, block);
    }
    return n;
}
```

## Right

```c
void *my_realloc(APTR pool, void *block, ULONG cur_size, ULONG new_size)
{
    void *n = my_alloc(pool, new_size);
    if (n) {
        CopyMem(block, n, cur_size < new_size ? cur_size : new_size);
        my_free(pool, block);
    }
    return n;
}
```

Also check the result of `AllocPooled` before writing a size header into it;
the same FreeType wrapper wrote to address 0 when the pool was empty.

## Detection

- Review every realloc-style wrapper over `AllocPooled`, `AllocVec` or
  `AllocMem` in imported code: the copy length must be the smaller of the two
  sizes.
- An alert `0x0100000F` from `PoolManagerAlert` means "look for the code that
  wrote into this pool earlier", not "this `FreePooled` is wrong".
- A test that grows and then shrinks one block, followed by a `FreePooled` of
  its neighbour, reproduces it at once.

## Evidence

| Claim | Source | Core | Method |
|---|---|---|---|
| FTManager raised alert 0x0100000F (PC in PoolManagerAlert) within 5 s of every start | (M) 2026-11-18 | Core 12856 | V4 DEV card, R10 ROM, freetype2.library 2.10.0 AROS port; started over rxnet, 2 of 2 starts |
| `ft_realloc` copied `cur_size` bytes into the new block | (SRC) `builds/aros/src/base/ftsystem.c`, FreeType 2.10.0 AROS port | any | source reading |
| With the copy limited to `min(cur_size, new_size)` the alert is gone, FTManager lists the 74 TrueType fonts, quits cleanly, and the library expunges | (M) 2026-11-18 | Core 12856 | same test, ApolloOS-Port commit aac8859 |
