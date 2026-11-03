# sources

Original documents for document intake (see `CONTRIBUTING.md` section 11).
Maintainers only.

- `official/`: official Apollo documentation in an editable format, such as
  ODT. The original is leading: knowledge base files generated from it carry
  `generated_from: sources/official/<file>` and are never edited by hand.
  Each original has a converter in `tools/intake/`.

| Original | Converter | Generated files |
|---|---|---|
| `official/AC68080PRM.odt` (68080 Programmer's Reference Manual) | `tools/intake/prm68080.py` | `core/cpu-68080/prm/` |

This folder is not knowledge base content. AI agents read the generated
files, not these originals.
