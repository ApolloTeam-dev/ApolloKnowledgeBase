#!/usr/bin/env python3
"""Document intake: convert the SAGA register documentation
(sources/official/saga-registers/, HTML) into core/saga-registers/.

  sagaregs.py           regenerate core/saga-registers/
  sagaregs.py --check   exit 1 if the generated files are out of date

The HTML is leading (CONTRIBUTING.md section 11). Never edit the generated
files: change the original, or this script, and regenerate. Uses only the
Python standard library.

The original is a register table (index.htm) with one page per register or
register group. This script takes only the SAGA-specific registers (the rows
where OCS, ECS and AGA are empty, plus the SAGA addresses listed in
EXTRA_ROWS), skips the Atari section, and applies the corrections in
CORRECTIONS. Facts that the original lacks come from ADDITIONS, each with
its source tag. Both lists are printed in core/saga-registers/index.md.
"""
import html
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRCDIR = "sources/official/saga-registers"
SOURCE = f"{SRCDIR}/index.htm"
OUTDIR = "core/saga-registers"
OWNER = "WDrijver"
CORE = "Core 12000+"
SOURCE_NAME = "SAGA register documentation, sources/official/saga-registers/ (HTML)"
WD = "WDrijver (maintainer), answers on the SAGA register documentation, 2026-11-04"
WDS = "WDrijver, 2026-11-04"
BIGGUN = "Gunnar (core developer, BigGun), Apollo chat, 2026-11-04 (relayed by WDrijver)"
BGS = "G, 2026-11-04"
APOLLOLIB = ("ApolloLib, github.com/WDrijver/ApolloCrossDev Projects/ApolloLib "
             "(ApolloCrossDev_Defines.h, ApolloCrossDev_LibC.c), commit 2dfaa5c (2026-09-02)")
APOLLOLIB_OLD = ("ApolloLib, older copy in ApolloClaude docs/toolchain/_ApolloLib "
                 "(ApolloCrossDev_Defines.h), 2026-11-04")
EX_PIP = ("Example SAGAPiP.c, github.com/WDrijver/ApolloCrossDev Projects/SAGAPiP, "
          "commit 2dfaa5c (2026-09-02)")
EX_POINTER = ("Example ApolloPointer.c, github.com/WDrijver/ApolloCrossDev "
              "Projects/ApolloPointer, commit 2dfaa5c (2026-09-02)")
APOLLOOS = ("ApolloOS source, github.com/ApolloTeam-dev/ApolloOS.R10 "
            "arch/m68k-amiga/hidd/sagagfx/sagagfx_hw.h, commit ca5ef46 (2025-06-10)")
MAGGIE = "maggie.library samples, see os/libraries/maggie-library.md"

ACCESS = {"R": "read", "W": "write", "S": "strobe (a write of any value "
          "triggers the action)", "ER": "early read",
          "R/W": "read and write (used in the original's Atari section, and here "
          "for `$DFF3EE`)"}


# ------------------------------------------------------------ the original

def read(name):
    with open(os.path.join(ROOT, SRCDIR, name), encoding="latin-1") as f:
        return f.read()


def index_rows():
    """The rows of index.htm: (address, name, page, access, flags, description).
    flags is the set of chipsets marked with '*'. Stops at the Atari section."""
    rows = []
    for part in re.split(r"<tr", read("index.htm"))[1:]:
        m = re.match(r"[^>]*>", part)
        body = re.split(r"</tr>|</table>", part[m.end():])[0]
        cells = re.findall(r"<t[dh][^>]*>(.*?)(?=<t[dh]|</t[dh]>|$)", body, re.S)
        if not cells:
            continue
        def text(c):
            c = re.sub(r"<br\s*/?>", "\n", c)
            c = html.unescape(re.sub(r"<[^>]+>", "", c))
            return "\n".join(re.sub(r"\s+", " ", ln).strip()
                             for ln in c.split("\n")).strip()
        first = text(cells[0])
        if "ATARI" in first.upper():
            break
        if not re.match(r"^DF[0-9A-Fa-f]", first) or len(cells) < 8:
            continue
        link = re.search(r'href="([^"]+)"', cells[1])
        flags = {n for n, c in zip(("OCS", "ECS", "AGA", "SAGA"), cells[3:7])
                 if text(c) == "*"}
        rows.append(dict(addr=first, name=text(cells[1]),
                         page=link.group(1) if link else None,
                         access=text(cells[2]), flags=flags,
                         desc=text(cells[7]).replace("\n", " "), notes=[]))
    return rows


def page(name):
    """The text of a register page, including any text after its <pre> block,
    without empty edge lines."""
    if not name or not os.path.isfile(os.path.join(ROOT, SRCDIR, name)):
        return None
    t = re.sub(r"<br\s*/?>", "\n", read(name), flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    lines = [ln.rstrip().expandtabs() for ln in t.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def box_table(lines):
    """The bit table of a page drawn with +---+ and | characters, as rows of
    (bits, function, description). A row with empty bits continues the row
    above it."""
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells[0].upper().startswith("BIT"):
            continue
        cells = (cells + ["", ""])[:3] if len(cells) < 3 else \
            [cells[0], cells[1], " ".join(c for c in cells[2:] if c)]
        if not cells[0] and rows:
            extra = " ".join(c for c in cells[1:] if c)
            rows[-1][2] = (rows[-1][2] + " " + extra).strip()
            continue
        rows.append(cells)
    return rows


def prose(lines, skip=0):
    """Page text after the table header lines, joined into paragraphs."""
    paras, cur = [], []
    for ln in lines[skip:]:
        s = ln.strip()
        if not s or s.startswith("+-") or s.startswith("-----"):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(re.sub(r"\s+", " ", s))
    if cur:
        paras.append(" ".join(cur))
    return paras


def md(s):
    return s.replace("|", "\\|").replace("*", "\\*").replace("_", "\\_")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(md(str(c)) if not str(c).startswith("`") else str(c)
                              for c in r) + " |" for r in rows]
    return out


def bits_md(rows):
    return table(["Bits", "Function", "Description"],
                 [[bitrange(b), f, d] for b, f, d in rows])


def bitrange(b):
    """'15.08', '15 ..8' and '31-24' all become '15–8' style ranges."""
    parts = [p for p in re.split(r"[\s.\-]+", b.strip()) if p]
    return "–".join(str(int(p)) if p.isdigit() else p for p in parts)


# ------------------------------------------------------------ corrections

# Each correction: (address, field, original value, corrected value, source).
# They are printed in index.md, so the original can be fixed.
CORRECTIONS = [
    ("DFFAA0", "addr", "DFFAA0", "DFF4A0",
     "typo in the original: the AUD10 block is at $DFF4A0, as the channel layout requires"),
    ("DFF4C4C", "addr", "DFF4C4C", "DFF4CC",
     "typo in the original: AUD12PER is at $DFF4CC, as the channel layout requires"),
    ("DFF21c", "addr", "DFF21c", "DFF21C", "upper case, as everywhere else"),
    ("DFF430", "desc", "Audio channel 1 location (32bit PTR)",
     "Audio channel 3 location (32bit PTR)", "typo in the original: this is channel 3"),
    ("DFF1EC", "desc", "Chunky plane pointer (hi 15 bits)",
     "Chunky plane pointer (hi 16 bits)",
     "the high word of a 32-bit pointer has 16 bits"),
    ("DFF3EC", "access", "R", "W", f"$DFF3EC is write-only ({WDS})"),
    ("DFF3EC", "desc", "Reserved",
     "SAGA Control 1: OCS mode, PAL zoom, zoom mode, scanlines",
     f"the register's function ({WDS})"),
    ("DFF3EE", "access", "R", "R/W", f"$DFF3EE is read and write ({WDS})"),
    ("DFF3EE", "desc", "Reserved",
     "SAGA Control 2: zoom shift X and Y in pixels",
     f"the register's function ({WDS})"),
    ("DFF1EE", "desc", "Chunky plane pointer (lo 15 bits)",
     "Chunky plane pointer (lo 16 bits)",
     "the low word of a 32-bit pointer has 16 bits"),
    ("DFF20C", "desc", "Vaniall DB9 Joystick-mouse 1 data (vert, horiz)",
     "Vanilla DB9 Joystick-mouse 1 data (vert, horiz)", "typo in the original"),
]

# SAGA-specific rows that the original marks as OCS/ECS/AGA too: new SAGA
# addresses or a classic address with a SAGA meaning.
EXTRA_ROWS = {
    "DFF20A": "a SAGA address; the original also marks OCS, ECS and AGA",
    "DFF20C": "a SAGA address; the original also marks OCS, ECS and AGA",
    "DFF1D0": "on SAGA this is the pointer X position; "
              "the original also marks ECS and AGA",
    "DFF1D2": "on SAGA this is the pointer Y position; "
              "the original also marks ECS and AGA",
}

# Pages the original links wrongly or not at all, by register name pattern.
PAGE_FIX = [
    (r"^AUD\d+L$", "audxl.htm"),
    (r"^AUD\d+LEN$", "audxlen.htm"),
    (r"^AUD\d+VOL$", "audnvol.htm"),
    (r"^AUD\d+CTRL$", "audxctrl.htm"),
    (r"^AUD\d+PER$", "audxper.htm"),
]


def apply_corrections(rows):
    applied = []
    for addr, field, old, new, why in CORRECTIONS:
        hit = [r for r in rows if r["addr"] == addr and r[field] == old] if field != "addr" \
            else [r for r in rows if r["addr"] == old]
        if not hit:
            raise SystemExit(f"correction does not match the original: {addr} {field}")
        for r in hit:
            r[field] = new
            r["notes"].append(f"corrected: {why}")
        applied.append((addr, field, old, new, why))
    return applied


def saga_rows():
    rows = index_rows()
    applied = apply_corrections(rows)
    keep = [r for r in rows if "SAGA" in r["flags"] and
            (not r["flags"] - {"SAGA"} or r["addr"] in EXTRA_ROWS)]
    for r in keep:
        if r["addr"] in EXTRA_ROWS:
            r["notes"].append(EXTRA_ROWS[r["addr"]])
    return rows, keep, applied


def addr(a):
    return int(a.split("/")[0], 16)


def row_md(r, with_page=False):
    a = r["addr"]
    a = f"`${a}`" if "/" not in a else \
        f"`${a.split('/')[0]}`, `${a.split('/')[0][:-2]}{a.split('/')[1]}`"
    cells = [a, md(r["name"]), md(r["access"]), md(r["desc"]) or "–"]
    return "| " + " | ".join(cells) + " |"


def reg_table(rows):
    out = ["| Address | Name | Access | Description (original) |", "|---|---|---|---|"]
    out += [row_md(r) for r in rows]
    notes = [(r["addr"], n) for r in rows for n in r["notes"]]
    if notes:
        out += [""] + [f"- `${a}`: {n}." for a, n in notes]
    return out


# ------------------------------------------------------------ output files

def frontmatter(title, components, tags, related, sources, basis):
    lines = ["---", f'title: "{title}"', "type: reference", f"owner: {OWNER}",
             "status: draft", "origin: official", f"basis: [{', '.join(basis)}]",
             f"components: [{', '.join(components)}]",
             "applies_to:", f'  core: "{CORE}"', "  os: [any]",
             f"tags: [{', '.join(tags)}]"]
    if related:
        lines.append("related:")
        lines += [f"  - {r}" for r in related]
    lines += ["sources:"] + [f'  - "{s}"' for s in [SOURCE_NAME] + sources]
    lines += [f"generated_from: {SOURCE}", "---", "",
              "<!-- GENERATED by tools/intake/sagaregs.py from "
              f"{SRCDIR}/. Do not edit: change the original or the script's "
              "CORRECTIONS/ADDITIONS, and regenerate. -->", ""]
    return lines


def tidy(lines):
    out = []
    for ln in lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln.rstrip())
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def doc(name, title, components, tags, summary, details, diff, rules,
        sources=(), basis=("official",), related=()):
    rel = ([] if name == "index.md" else [f"{OUTDIR}/index.md"]) + list(related)
    lines = frontmatter(title, components, tags, rel, list(sources), basis)
    lines += ["## Summary", "", summary, "", "## Details", ""] + details
    lines += ["", "## Differences from AmigaOS / AROS / 68060", ""] + diff
    lines += ["", "## Do / Don't", ""] + [f"- {r}" for r in rules]
    return name, tidy(lines)


def pick(rows, lo, hi):
    return [r for r in rows if lo <= addr(r["addr"]) <= hi]


def by_addr(rows, a):
    return next(r for r in rows if r["addr"] == a)


def chunky_plane(rows):
    gm = page("gfxmode.htm")
    modes, fmts, part = [], [], None
    for ln in gm:
        if "Resolution" in ln:
            part = modes
        elif "Pixelformat" in ln:
            part = fmts
        m = re.search(r"\$([0-9A-F]{2})\s*=\s*(.*?)\s*\|?\s*$", ln)
        if m and part is not None:
            part.append((m.group(1), m.group(2).rstrip("| ").strip()))
    res = []
    for code, rest in modes:
        m = re.match(r"(\d+x\d+)\s+(\d+Hz)\s+(\d+M[Hh]z)\s*(x2 x2)?", rest)
        res.append([f"`${code}`", m.group(1), m.group(2), m.group(3).replace("Mhz", "MHz"),
                    "2x2" if m.group(4) else "–"])
    fm = [[f"`${c}`", d or "(empty in the original)"] for c, d in fmts]
    mod = page("bplhmod.htm")
    ptr = page("bplhpth.htm")
    details = ["### Registers", ""] + reg_table(pick(rows, 0xDFF1E6, 0xDFF1F4))
    details += ["", "### GFXMODE (`$DFF1F4`)", "",
                prose(gm, 1)[0] if prose(gm, 1) else "", "",
                "Bits 15–8 select the resolution, bits 7–0 the pixel format. "
                "Write it as one word: `(resolution << 8) | format`.", "",
                "#### Resolution (bits 15–8)", ""]
    details += table(["Value", "Resolution", "Refresh", "Pixel clock", "Pixel doubling"], res)
    details += ["", "`$00` has no description in the original. The original writes "
                "84 MHz for `$13` and 85 MHz for the other high-resolution modes.", "",
                "#### Pixel format (bits 7–0)", ""]
    details += table(["Value", "Format"], fm)
    details += ["", "Values `$08`–`$0B` are Atari planar formats (ApolloLib names them "
                "APOLLO_ATARI_1BIT to _8BIT) (SRC).", "",
                "### Chunky plane pointer and modulo", "",
                f"- BPLHPTH/BPLHPTL (`$DFF1EC`): {' '.join(prose(ptr, 1))}",
                f"- BPLHMOD (`$DFF1E6`): {' '.join(prose(mod, 1))} The original's "
                "text says \"UHRES bitplane pointer\"; on SAGA it is the chunky plane: "
                "the number of bytes skipped after each row (ApolloLib, SRC).", "",
                "### Reading the current mode back", "",
                "Every write-only register at `$DFF000`–`$DFF1FF` reads back at the "
                f"same offset in `$DFE000`–`$DFE1FF` ({WDS}): GFXMODE at `$DFE1F4`, "
                "the chunky pointer at `$DFE1EC`, the modulo at `$DFE1E6`. "
                "maggie.library's samples save the mode and frame pointer this way "
                "(SRC, see [maggie-library.md](../../os/libraries/maggie-library.md))."]
    return doc("chunky-plane.md", "SAGA chunky plane: GFXMODE, pointer and modulo",
               ["saga-video-isabelle"], ["saga", "isabelle", "gfxmode", "chunky", "registers"],
               "The SAGA chunky plane is a linear framebuffer in any RAM. GFXMODE "
               "(`$DFF1F4`) selects resolution and pixel format, BPLHPT (`$DFF1EC`) "
               "points to the pixels and BPLHMOD (`$DFF1E6`) sets the row modulo.",
               details,
               ["- Classic Amiga chipsets have only planar bitplanes in Chip RAM. "
                "The chunky plane has 8- to 32-bit pixels and can be in Fast RAM.",
                "- On ECS, `$DFF1E6`/`$DFF1EC` were BPLHMOD/BPLHPT for UHRES "
                "bitplanes; SAGA reuses the names for the chunky plane."],
               ["DO write GFXMODE as one word, resolution in the high byte.",
                "DO set the pointer and modulo before you switch the mode.",
                "DON'T rely on GFXMODE `$00` or pixel format `$07`: the original "
                "describes neither."],
               sources=[APOLLOLIB, MAGGIE], basis=["official", "source-code"])


def colour_ports(rows):
    ports = [("planarcol.htm", "DFF380"), ("spritecol.htm", "DFF384"),
             ("chunkycol.htm", "DFF388"), ("pipcol.htm", "DFF38C")]
    bits = box_table(page("planarcol.htm"))
    details = ["### Registers", ""] + reg_table(pick(rows, 0xDFF380, 0xDFF38E))
    details += ["", "Each port is one 32-bit register (the original lists its high "
                "and low word, H and L). A 32-bit write sets one entry of a "
                "256-colour table:", ""] + bits_md(bits)
    details += ["", "| Port | Address | Table |", "|---|---|---|",
                "| Planar | `$DFF380` | Bitplane colours (256) |",
                "| Sprite | `$DFF384` | Sprite colours (256) |",
                "| Chunky | `$DFF388` | Chunky plane in 8-bit mode (256) |",
                "| PIP 1 | `$DFF38C` | PIP 1 in 8-bit mode (256) |",
                "| PIP 2 | `$DFF37C` | PIP 2 in 8-bit mode (256) (SRC, not in the original) |",
                "", "### Example (original)", "", "```asm",
                "    move.l  #$00FF0000,$DFF380   ; colour 0 = red",
                "    move.l  #$01FFFF00,$DFF380   ; colour 1 = yellow",
                "```", "",
                "### Copper: 32-bit MOVE", "", "```asm",
                "    dc.w    $8380,$00FF,$0000    ; colour 0 = red (original)",
                "```", "",
                f"- The SAGA Copper can do 32-bit moves ({BGS}).",
                f"- A 32-bit MOVE has the high bit of its first word set ({BGS}): "
                "`$8380` = bit 15 + register `$380`. The two words after it are the "
                "32-bit value, high word first, as in the original's example.",
                f"- It needs SAGA mode: set the SAGA bit in FMODE (`$DFF1FC` bit 4) "
                f"first ({BGS}).",
                f"- Without the SAGA bit, the Copper can write only `$DFF0xx` and "
                f"`$DFF1xx` ({BGS}), so it can't reach the colour ports at `$DFF3xx`.", "",
                "A classic Copper MOVE is two words (register, 16-bit value). Read the "
                "classic way, `$8380` would be COLOR00 (`$180`), and the third word the "
                "start of the next instruction."]
    return doc("colour-ports.md", "SAGA colour ports (24-bit palettes)",
               ["saga-video-isabelle"], ["saga", "isabelle", "palette", "colour", "registers"],
               "SAGA sets 24-bit palette entries through 32-bit colour ports: one "
               "write gives the entry number and its red, green and blue. There is one "
               "port each for the planar, sprite, chunky and PIP palettes.",
               details,
               ["- Classic COLORxx registers (`$DFF180`–`$DFF1BE`) hold 32 entries; AGA "
                "reaches 256 through banks and BPLCON3. A SAGA port writes any of 256 "
                "entries in one 32-bit write."],
               ["DO write the port with one `move.l`.",
                "DO set FMODE bit 4 (SAGA) before a Copper list writes a colour port.",
                "DO set bit 15 in the first word of a 32-bit Copper MOVE."],
               sources=[APOLLOLIB, BIGGUN], basis=["core-developer", "official", "source-code"])


PIP2 = [("DFF3B0", "PIP2 X start"), ("DFF3B2", "PIP2 Y start"),
        ("DFF3B4", "PIP2 X stop"), ("DFF3B6", "PIP2 Y stop"),
        ("DFF3B8", "PIP2 pointer (32-bit)"), ("DFF3BC", "PIP2 format"),
        ("DFF3BE", "PIP2 modulo"), ("DFF3C0", "PIP2 colour key"),
        ("DFF3C2", "PIP2 DMA row length")]


def pip(rows):
    p1 = pick(rows, 0xDFF3D0, 0xDFF3E2)
    details = ["### PIP 1 registers (original)", ""] + reg_table(p1)
    details += ["", "The original links these rows to a page that doesn't exist; the "
                "facts below come from ApolloLib and the SAGAPiP example (SRC).", "",
                "### PIP 2 registers (SRC, not in the original)", "",
                "PIP 2 has the same layout as PIP 1, `$20` lower (ApolloLib):", "",
                "| Address | Register | Same as PIP 1 |", "|---|---|---|"]
    details += [f"| `${a}` | {n} | `${addr(a) + 0x20:06X}` |" for a, n in PIP2]
    details += ["", "Its colour port is `$DFF37C` (see [colour-ports.md](colour-ports.md)). "
                "The SAGAPiP example says two PIPs exist from Core 11900 (SRC).", "",
                "### Register meanings (SRC)", "",
                "| Register | Meaning |", "|---|---|",
                "| X/Y start, X/Y stop | Window position in screen pixels. The example "
                "writes X + 16 and Y − 1 to place the PIP exactly over a window. |",
                "| Pointer | 32-bit address of the PIP bitmap |",
                "| Format | Bits 7–0: pixel format; bit 8: transparency on. See the "
                "table below. |",
                "| Modulo | Bytes skipped after each row |",
                "| Colour key | Bit 15 = enable, bits 11–8 red, 7–4 green, 3–0 blue |",
                "| DMA row length | Bytes fetched per row = width × bytes per pixel. "
                "**0 switches the PIP off.** |",
                "", "### Pixel formats and transparency", "",
                "| Format | Value | On PIP | Transparent colour (bit 8 set) |",
                "|---|---|---|---|",
                "| 8-bit indexed | `$01` | Yes | Index `$FF` |",
                "| 16-bit R5G6B5 | `$02` | Yes | `$F81F`: red and blue at maximum (purple) |",
                "| 15-bit 1R5G5B5 | `$03` | Yes | `$7C1F`: red and blue at maximum (purple) |",
                "| 24-bit R8G8B8 | `$04` | No | – |",
                "| 32-bit A8R8G8B8 | `$05` | No | – |",
                "| YUV888 | `$06` | Yes | Not documented |",
                "| YUV444 | `$0E` | Yes | Not documented |",
                "",
                f"Formats and transparent colours: {WDS}. The transparent colour is "
                "fixed per format. ApolloLib still marks YUV as not supported on PIP; "
                "that is an error in ApolloLib, not in the hardware.", "",
                "### Two modes (SAGAPiP example, SRC)", "",
                "- **Overlay:** colour key 0. The PIP is in front of the main screen; "
                "with format bit 8 set, pixels in the transparent colour of the "
                "format are transparent.",
                "- **Chroma key:** colour key with bit 15 set, for example `$8F0F` "
                "(purple). The PIP is behind the main screen and shows only where the "
                "main screen has the key colour."]
    return doc("pip.md", "SAGA picture in picture (PIP 1 and PIP 2)",
               ["saga-video-isabelle"], ["saga", "isabelle", "pip", "overlay", "registers"],
               "SAGA overlays up to two picture-in-picture windows (PIP) on the main "
               "screen, each with its own bitmap, format, position and colour key. The "
               "original documents PIP 1 only; PIP 2 and the register meanings come "
               "from ApolloLib.",
               details,
               ["- Classic Amiga chipsets have no PIP. Dual playfield is the nearest "
                "classic feature, and it is limited to planar bitmaps in Chip RAM."],
               ["DO set the DMA row length last: it switches the PIP on.",
                "DO write 0 to the DMA row length to switch a PIP off.",
                "DON'T use the 24- or 32-bit formats (`$04`, `$05`) for a PIP.",
                "DO keep the transparent colour (`$FF` in 8-bit, purple in 15- and "
                "16-bit) out of the PIP image, except where it should be transparent."],
               sources=[APOLLOLIB, EX_PIP, WD], basis=["official", "source-code"],
               related=[f"{OUTDIR}/colour-ports.md", f"{OUTDIR}/chunky-plane.md"])


def pointer(rows):
    pos = [by_addr(rows, "DFF1D0"), by_addr(rows, "DFF1D2")]
    cols = pick(rows, 0xDFF3A2, 0xDFF3A6)
    details = ["### Two pointer generations", "",
               "| Cores | Pointer |", "|---|---|",
               "| Core 12500 and later | 32x32, 8-bit colour index, 256-colour palette, "
               "50 % semi-transparency |",
               "| Before Core 12500 | 16x16 planar, 12-bit colours |", "",
               f"From Core 12500 the 32x32 sprite replaces the 16x16 pointer ({WDS}). The "
               "position registers are the same for both.", "",
               "### Position (original and SRC)", ""] + reg_table(pos)
    details += ["", "- Write X to `$DFF1D0` and Y to `$DFF1D2`; read them back at "
                f"`$DFE1D0` and `$DFE1D2`, as every write-only register up to `$DFF1FF` "
                f"({WDS}; ApolloLib does this, SRC).",
                "- ApolloLib writes the mouse position + 16 (X) and + 8 (Y) (SRC).", "",
                "### 32x32 pointer sprite, Core 12500 and later (SRC, not in the original)", "",
                "From the current ApolloLib and the ApolloPointer example:", "",
                "| Address | Use |", "|---|---|",
                "| `$DFD000` | Image: 32 x 32 pixels, 2 bytes per pixel (colour index, "
                "transparency byte), 2048 bytes, row by row |",
                "| `$DFF3A8` | Palette index (word): write the entry number first |",
                "| `$DFF3AA` | Palette colour (long, R8G8B8) for the entry selected at "
                "`$DFF3A8` |", "",
                "- Colour index 0 is fully transparent.",
                f"- The second byte is not a real alpha: a pixel is either opaque or 50 % "
                f"semi-transparent ({WDS}). ApolloLib writes `$FF` for opaque and `$00` for "
                "semi-transparent (SRC).",
                "- To set the palette, write the index to `$DFF3A8`, then the colour to "
                "`$DFF3AA`, for each of the 256 entries.", "",
                "### 16x16 pointer, before Core 12500", "",
                "The original lists three 12-bit colours of this pointer:", ""] + reg_table(cols)
    details += ["", "These rows have no page in the original. An older ApolloLib copy "
                "adds colour 0 at `$DFF3A0` and the 16x16 planar image at `$DFF800` (SRC)."]
    return doc("pointer.md", "SAGA hardware sprite pointer",
               ["saga-video-isabelle"], ["saga", "isabelle", "pointer", "sprite", "registers"],
               "SAGA has a hardware mouse pointer, positioned through `$DFF1D0`/`$DFF1D2`. "
               "From Core 12500 it is a 32x32 sprite with an 8-bit colour index, a "
               "256-colour palette and 50 % semi-transparency; before that it was a "
               "16x16 planar pointer. The original documents only the position and the "
               "old pointer's colours; the 32x32 sprite comes from ApolloLib.",
               details,
               ["- On ECS, `$DFF1D0`/`$DFF1D2` are SPRHSTRT/SPRHSTOP (UHRES sprite "
                "vertical start and stop). On SAGA they position the pointer.",
                "- Classic sprites are 16 pixels wide with 3 colours, fetched by DMA "
                "from Chip RAM. The SAGA pointer sprite is written directly to `$DFD000`."],
               ["DO write the palette through `$DFF3A8` (index) and `$DFF3AA` (colour).",
                "DO keep colour index 0 for transparent pixels.",
                "DON'T expect real alpha blending: a pixel is opaque or 50 % "
                "semi-transparent.",
                "DON'T use `$DFF800` or `$DFF3A0`–`$DFF3A6` on Core 12500 and later: "
                "they belong to the old 16x16 pointer."],
               sources=[APOLLOLIB, APOLLOLIB_OLD, EX_POINTER, WD],
               basis=["official", "source-code"])


def display_control(rows):
    sc = box_table(page("sagacontrol.htm"))
    sh = box_table(page("shiftdown.htm"))
    adj = box_table(page("screenadjust.htm"))
    ex = [re.sub(r"\s+", " ", ln.replace("Examples:", "")).strip()
          for ln in page("sagacontrol.htm") if "apoke" in ln]
    details = ["### Registers", ""] + reg_table(pick(rows, 0xDFF390, 0xDFF392) +
                                                pick(rows, 0xDFF3EC, 0xDFF3EE))
    details += ["", "### SAGA CONTROL (`$DFF3EC`, write-only)", "",
                f"SAGA Control 1: OCS mode, PAL zoom, zoom mode and scanlines ({WDS}).", "",
                "Bit 15 is SET/CLR, as in DMACON: bits written as 1 are set when bit "
                "15 is 1, and cleared when it is 0.", ""] + bits_md(sc)
    details += ["", "Examples from the original (`apoke address size value`):", "", "```text"]
    details += ex + ["```", "",
                "### SCREEN SHIFT (`$DFF3EE`, read and write)", "",
                "The original's page has the title \"SAGA CONTROL Register\"; its "
                "content is the screen shift:", ""] + bits_md(sh)
    details += ["", f"SAGA Control 2: the zoom shift. Read and write; X and Y are in "
                f"pixels, positive integers ({WDS}). The original marks it R.", "",
                "### SCREENMODE ADJUST (`$DFF390`)", ""] + bits_md(adj)
    details += ["", "The original's example on this page is the one of the planar "
                "colour port (it sets colour 0 to red) and is left out."]
    return doc("display-control.md", "SAGA display control, screen shift and screen mode adjust",
               ["saga-video-isabelle"], ["saga", "isabelle", "scanlines", "zoom", "registers"],
               "SAGA CONTROL (`$DFF3EC`, write-only) switches scanlines, zoom and a "
               "forced OCS mode; SCREEN SHIFT (`$DFF3EE`, read and write) shifts the "
               "zoomed screen in pixels; SCREENMODE ADJUST (`$DFF390`) enlarges the "
               "SAGA screen modes.",
               details,
               ["- Classic Amiga chipsets have none of these registers: scanlines and "
                "zoom are features of the SAGA video output."],
               ["DO set bit 15 to set bits and clear it to clear them.",
                "DON'T read `$DFF3EC`: it is write-only, although the original's "
                "Access column says R.",
                "DO give the zoom shift in `$DFF3EE` as positive pixel counts."],
               sources=[WD])


def collisions(rows):
    c = pick(rows, 0xDFF230, 0xDFF23E)
    details = ["### Registers", ""] + reg_table(c)
    details += ["", "Bit layout (one register per sprite):", ""] + \
        bits_md(box_table(page("clxdatx.htm")))
    details += ["", f"SAGA has the 8 classic sprites, as on the classic Amiga ({WDS}). "
                "The original's bit table names sprites 0 to F; since sprites 8–F "
                "don't exist, only bits 0–7 refer to real sprites."]
    return doc("sprite-collision.md", "SAGA detailed sprite collision",
               ["saga-video-isabelle"], ["saga", "isabelle", "sprites", "collision", "registers"],
               "SAGA reports, per sprite, which other sprites it touches, in one "
               "register per sprite at `$DFF230`–`$DFF23E`.",
               details,
               ["- Classic CLXDAT (`$DFF00E`) reports collisions only between sprite "
                "pairs and playfields, and clears on read."],
               ["DO read the register of the sprite you are interested in.",
                "DON'T use bits 8–15: SAGA has 8 sprites."],
               sources=[WD])


ARNE_LAYOUT = [("+0", "AUDxL", "L", "W", "Pointer to the sample data (32-bit, any RAM)"),
               ("+4", "AUDxLEN", "L", "W", "Length in sample pairs (32-bit)"),
               ("+8", "AUDxVOL", "W", "W", "Volume: bits 15–8 left, 7–0 right"),
               ("+A", "AUDxCTRL", "W", "W", "Control (see below)"),
               ("+C", "AUDxPER", "W", "W", "Period (16-bit)")]


def arne_channels(rows):
    ch = pick(rows, 0xDFF400, 0xDFF4FF)
    # Check the layout: channel n at $DFF400 + n*$10.
    off = {"L": 0, "LEN": 4, "VOL": 8, "CTRL": 0xA, "PER": 0xC}
    bad = []
    for r in ch:
        m = re.match(r"^AUD(\d+)(L|LEN|VOL|CTRL|PER)$", r["name"])
        if not m:
            bad.append(r["addr"])
            continue
        want = 0xDFF400 + int(m.group(1)) * 0x10 + off[m.group(2)]
        if addr(r["addr"]) not in (want, want + 2):
            bad.append(r["addr"])
    if bad:
        raise SystemExit(f"Arne layout does not match the original: {bad}")
    ctrl = box_table(page("audxctrl.htm"))
    fmt = [ln.strip() for ln in page("audxctrl.htm")
           if "signed" in ln]
    per = prose(page("audxper.htm"), 1)
    notes = [(r["addr"], n) for r in ch for n in r["notes"]]
    details = ["### Channel layout", "",
               "16 channels, channel n at `$DFF400 + n × $10` (n = 0–15). The converter "
               "checks every row of the original against this layout.", ""]
    details += table(["Offset", "Register", "Size", "Access", "Meaning"], ARNE_LAYOUT)
    if notes:
        details += [""] + [f"- `${a}`: {n}." for a, n in notes]
    details += ["", "### Channels 0–3 and Paula", "",
                "Arne channels 0–3 are the four Paula channels: the same voices, with "
                "the classic registers at `$DFF0A0`–`$DFF0DF` and the Arne registers "
                f"at `$DFF400`–`$DFF43F` ({WDS}). ApolloLib "
                "starts and stops channels 0–3 with DMACON bits 0–3 (`$DFF096`) and "
                "checks them in DMACONR (`$DFF002`); channels 4–15 use DMACON2 (SRC, "
                "see [arne-dma-and-interrupts.md](arne-dma-and-interrupts.md)).", "",
                "### AUDxCTRL", ""] + bits_md(ctrl)
    details += ["", "Sample formats (original):", ""] + [f"- {f}" for f in fmt]
    details += ["", "ApolloLib writes `$0005` (16-bit stereo, looping) and `$0007` "
                "(16-bit stereo, one-shot) (SRC). The other bits are not described.", "",
                "### AUDxLEN", "",
                "The count is in pairs of samples (original). For 16-bit stereo, "
                "ApolloLib writes the size in bytes / 8: one count is two stereo frames "
                "of 2 × 16 bits (SRC).", "",
                "### AUDxVOL", "",
                "Bits 15–8 left volume, bits 7–0 right volume (original). Each side "
                "ranges from `$00` to `$FF` (ApolloLib, SRC).", "",
                "### AUDxPER", ""] + [" ".join(per)]
    details += ["", "With the PAL clock of 3546895 Hz (ApolloLib), period 65 gives "
                "3546895 / 65 = 54.6 kHz, not the 56 kHz in the original."]
    return doc("arne-channels.md", "SAGA Arne audio channel registers",
               ["saga-audio-arne"], ["saga", "arne", "audio", "registers"],
               "Arne, the SAGA audio unit, has 16 channels of 8- or 16-bit mono or "
               "16-bit stereo samples from any RAM, each with a 32-bit pointer and "
               "length at `$DFF400 + n × $10`. Channels 0–3 are the Paula channels.",
               details,
               ["- Paula has 4 channels, 8-bit samples, 6-bit volume and Chip RAM only. "
                "Arne channels 0–3 are those same channels, with the extra registers at "
                "`$DFF400`.",
                "- Classic AUDxLEN counts words; Arne AUDxLEN counts sample pairs and "
                "is 32 bits."],
               ["DO keep the period at 65 or higher.",
                "DO give AUDxLEN in sample pairs.",
                "DO start channels 0–3 with DMACON and channels 4–15 with DMACON2.",
                "DON'T program channel 0–3 through both register sets at the same time."],
               sources=[APOLLOLIB, WD], basis=["official", "source-code"],
               related=["core/saga-audio-arne/registers.md",
                        f"{OUTDIR}/arne-dma-and-interrupts.md"])


def arne_dma(rows):
    regs = [r for r in rows if r["addr"] in ("DFF202", "DFF21C", "DFF21E",
                                             "DFF296", "DFF29A", "DFF29C")]
    d = box_table(page("dmacon2.htm"))
    i = box_table(page("intena2.htm"))
    irq = [ln.strip() for ln in page("intena2.htm") if "IRQ" in ln]
    details = ["### Registers", ""] + reg_table(regs)
    details += ["", "### DMACON2", ""] + bits_md(d)
    details += ["", "### INTENA2 and INTREQ2", "",
                "Both use the same bits. INTREQ2 needs a set and a clear write to load "
                "arbitrary data, as INTREQ (original).", ""] + bits_md(i)
    details += ["", "The original adds:", ""] + [f"- \"{x}\"" for x in irq]
    details += ["", "Whether `$48` and `$50` are vector offsets or vector numbers, and "
                "at which interrupt level they arrive, is an open question (see "
                "[index.md](index.md))."]
    return doc("arne-dma-and-interrupts.md", "SAGA DMACON2, INTENA2 and INTREQ2",
               ["saga-audio-arne"], ["saga", "arne", "audio", "dma", "interrupts",
                                     "ethernet", "registers"],
               "DMACON2, INTENA2 and INTREQ2 control DMA and interrupts of Arne audio "
               "channels 4–15 and of the Ethernet. Bit n is channel n + 4; bit 13 is "
               "Ethernet.",
               details,
               ["- Classic DMACON/INTENA/INTREQ cover audio channels 0–3 only. "
                "Channels 0–3 stay there on SAGA; the second set adds 4–15 and "
                "Ethernet."],
               ["DO use bit 15 as SET/CLR, as in the classic registers.",
                "DO map channel n (4–15) to bit n − 4."],
               related=[f"{OUTDIR}/arne-channels.md"])


def maggie(rows):
    t = pick(rows, 0xDFF250, 0xDFF28C)
    details = ["### Registers", ""] + reg_table(t)
    details += ["", "Offsets from `$DFF250`, for comparison with the measured layout "
                "in [registers.md](../saga-3d-maggie/registers.md):", "",
                "| Offset | Name (original) |", "|---|---|"]
    details += [f"| {addr(r['addr']) - 0xDFF250} | {md(r['name'])} |" for r in t]
    return doc("maggie-3d.md", "SAGA Maggie 3D registers (official names)",
               ["saga-3d-maggie"], ["saga", "maggie", "3d", "texture", "registers"],
               "Maggie, the SAGA texture-mapping unit, is programmed through registers at "
               "`$DFF250`–`$DFF28F`. This file gives the official names; the measured "
               "behaviour is in core/saga-3d-maggie/registers.md.",
               details,
               ["- Classic Amiga chipsets have no texture-mapping unit."],
               ["DO write TEXSTRT (`$DFF25E`) last: it starts the span.",
                "DO check core/saga-3d-maggie/registers.md and its pitfalls for the "
                "measured behaviour."],
               related=["core/saga-3d-maggie/registers.md"])


def inputs(rows):
    regs = [r for r in rows if r["addr"] in ("DFF20A", "DFF20C", "DFF212")] + \
        pick(rows, 0xDFF220, 0xDFF226)
    wheel = page("mousewheel.htm")
    jb = box_table(page("joybuttons.htm"))
    potgo = [ln.strip() for ln in page("potgo.htm") if ln.strip().startswith("Bit ")]
    details = ["### Registers", ""] + reg_table(regs)
    details += ["", "### USB joypads (`$DFF220`–`$DFF226`)", "",
                "One register per joypad. The index describes them as \"16bit USB Joy "
                "Buttons (0)=active\"; ApolloLib reads a set bit as pressed and bit 0 "
                "as connected (SRC). ApolloLib's names are in the last column.", ""]
    names = {"08": "TR", "07": "TL", "06": "BR", "05": "BL", "04": "Y", "03": "X",
             "02": "B", "01": "A", "00": "Connected"}
    details += table(["Bits", "Function", "Description", "ApolloLib"],
                     [[b, f, d, names.get(b, "")] for b, f, d in jb])
    details += ["", "ApolloLib also reads bits 2/3 as right stick X and bits 1/4 as "
                "right stick Y (SRC).", "",
                "### Mouse wheel (`$DFF212`)", "",
                "| Bits | Use |", "|---|---|"]
    for ln in wheel:
        m = re.match(r"\s*BIT\s+(\d+(?:-\d+)?)\s+(.*\S)", ln)
        if m:
            details.append(f"| {bitrange(m.group(1))} | {md(m.group(2))} |")
    counter = next(ln.strip() for ln in wheel if "counter" in ln)
    details += [f"| 7–0 | {md(counter)} |", "",
                "### DB9 joysticks (`$DFF20A`, `$DFF20C`)", "",
                "The \"vanilla\" DB9 ports, with the layout of JOY0DAT/JOY1DAT. The "
                "original's index marks them OCS, ECS and AGA too, but these addresses "
                "are SAGA's.", "",
                "### Extra fire buttons in POTGO (classic register)", ""]
    details += [f"- {p}" for p in potgo]
    return doc("input.md", "SAGA input registers: USB joypads, mouse wheel, DB9",
               ["general"], ["saga", "input", "joypad", "usb", "mouse", "registers"],
               "SAGA reads USB joypads (`$DFF220`–`$DFF226`) and the USB mouse wheel "
               "(`$DFF212`) through registers, and adds the DB9 ports at `$DFF20A`/`$DFF20C`.",
               details,
               ["- Classic Amiga input is JOYxDAT, POTGO/POTINP and CIA bits, without "
                "USB, wheel or more than 3 buttons."],
               ["DO test bit 0 (connected) before you trust a joypad register.",
                "DO treat the wheel counter as signed and use the difference between "
                "two reads."],
               sources=[APOLLOLIB], basis=["official", "source-code"])


BOARDS = [("$01", "V2-V600 (legacy)", "ApolloOS"), ("$02", "V2-V500 (legacy)", "ApolloOS"),
          ("$03", "V4 Firebird (A500); also Salamander (Firebird on an A2000 adapter) "
           "and Phoenix (Firebird on an A1000 adapter)", "WDrijver, original"),
          ("$04", "V4 IceDrake (A1200)", "WDrijver, original"),
          ("$05", "V4 Standalone", "WDrijver, original"),
          ("$06", "V2-V1200 (legacy)", "ApolloOS"),
          ("$07", "V4 Manticore (A600)", "WDrijver, original"),
          ("$08", "V4 UniCorn (A6000)", "WDrijver, ApolloOS")]


def system(rows):
    regs = pick(rows, 0xDFF3EA, 0xDFF3EA) + pick(rows, 0xDFF3F0, 0xDFF3FC)
    details = ["### Registers", ""] + reg_table(regs)
    details += ["", "### VAMPIRE VERSION / board ID (`$DFF3FC`)", "",
                "Bits 15–8: board (card) ID. Bits 7–0: CPU clock multiplier.", ""]
    details += table(["ID", "Board", "Source"], BOARDS)
    details += ["", "The original's list says 1 = V600, 2 = V500, 6 = V1200 without "
                "\"V2\", and lacks `$08`. ApolloOS marks `$09` as future.", "",
                "All V4 boards run the same core: the board ID tells the board, not "
                "different SAGA features (see [hardware/index.md](../../hardware/index.md)).",
                "", "### Other registers", "",
                "CORE REVISION, CHIP ID and the SPI registers have no description in "
                "the original. SPI WRITE (`$DFF3F8`) is marked R there, which is "
                "unlikely for a write register."]
    return doc("system.md", "SAGA system registers: board ID, core revision, chip ID, SPI",
               ["general"], ["saga", "board-id", "version", "registers"],
               "`$DFF3FC` gives the V4 board ID and the CPU clock multiplier. Core "
               "revision, chip ID and SPI registers sit at `$DFF3EA`–`$DFF3FA`.",
               details,
               ["- Classic Amiga chipsets have DENISEID (`$DFF07C`) for the video chip "
                "only; there is no board or clock register."],
               ["DO read the board ID with `move.w $DFF3FC` and use the high byte.",
                "DON'T use the board ID to decide which SAGA features exist: they are "
                "the same on every V4 board with the same core."],
               sources=[APOLLOOS, WD], basis=["official", "source-code"],
               related=["hardware/index.md"])


FILES = [("chunky-plane.md", "Chunky plane: GFXMODE, pointer, modulo"),
         ("colour-ports.md", "24-bit colour ports"),
         ("pip.md", "Picture in picture (PIP 1 and 2)"),
         ("pointer.md", "Hardware sprite pointer"),
         ("display-control.md", "SAGA control, screen shift, screen mode adjust"),
         ("sprite-collision.md", "Detailed sprite collision"),
         ("arne-channels.md", "Arne audio channels"),
         ("arne-dma-and-interrupts.md", "DMACON2, INTENA2, INTREQ2"),
         ("maggie-3d.md", "Maggie 3D registers"),
         ("input.md", "USB joypads, mouse wheel, DB9"),
         ("system.md", "Board ID, core revision, chip ID, SPI")]

OPEN = [
    "Copper in SAGA mode: does it reach every SAGA register, including Arne at "
    "`$DFF400`–`$DFF4FF` (that needs register bit 10)? Can it also do 16-bit moves "
    "above `$DFF1FF`, and does COPCON's danger bit still apply?",
    "\"IRQ $48\" (Ethernet) and \"IRQ $50\" (Arne channels 4–15): vector offsets or "
    "vector numbers, and at which interrupt level.",
    "Read-back above `$DFF1FF`: write-only registers at `$DFF000`–`$DFF1FF` read "
    "back at `$DFE000`–`$DFE1FF`. Is there a read-back for the write-only registers "
    "from `$DFF200` up (Maggie, DMACON2, colour ports, PIP, Arne)?",
]


def index(rows, keep, applied):
    where = {}
    for name, lo, hi in [("chunky-plane.md", 0xDFF1E6, 0xDFF1F4),
                         ("arne-dma-and-interrupts.md", 0xDFF202, 0xDFF202),
                         ("input.md", 0xDFF20A, 0xDFF226),
                         ("arne-dma-and-interrupts.md", 0xDFF21C, 0xDFF21E),
                         ("sprite-collision.md", 0xDFF230, 0xDFF23E),
                         ("maggie-3d.md", 0xDFF250, 0xDFF28C),
                         ("arne-dma-and-interrupts.md", 0xDFF296, 0xDFF29C),
                         ("colour-ports.md", 0xDFF380, 0xDFF38E),
                         ("display-control.md", 0xDFF390, 0xDFF392),
                         ("pointer.md", 0xDFF3A2, 0xDFF3A6),
                         ("pip.md", 0xDFF3D0, 0xDFF3E2),
                         ("system.md", 0xDFF3EA, 0xDFF3EA),
                         ("display-control.md", 0xDFF3EC, 0xDFF3EE),
                         ("system.md", 0xDFF3F0, 0xDFF3FC),
                         ("arne-channels.md", 0xDFF400, 0xDFF4FF),
                         ("pointer.md", 0xDFF1D0, 0xDFF1D2)]:
        for r in keep:
            if lo <= addr(r["addr"]) <= hi:
                where[r["addr"]] = name
    missing = [r["addr"] for r in keep if r["addr"] not in where]
    if missing:
        raise SystemExit(f"rows without a file: {missing}")
    groups = {}
    for r in sorted(keep, key=lambda r: addr(r["addr"])):
        groups.setdefault(where[r["addr"]], []).append(r)
    details = ["### About the original", "",
               f"- Original: [`{SRCDIR}/`](../../{SRCDIR}/), an HTML register table "
               "(`index.htm`) with one page per register. It is leading; these files "
               "are generated from it by `tools/intake/sagaregs.py`.",
               f"- Valid for {CORE} ({WDS}).",
               "- `index.htm` is the current table. `saga.htm` is an older table with "
               "another audio and sprite layout; it is not used.",
               "- The Atari section of `index.htm` is skipped.", "",
               "### Scope: SAGA-specific registers only", "",
               f"Every one of the {len(rows)} rows of the original is marked SAGA, "
               "because SAGA contains the classic chipset. These files cover the "
               f"{len(keep)} SAGA-specific rows: the rows where OCS, ECS and AGA are "
               "empty, plus the SAGA addresses that the original also marks as classic.",
               "", "For every other register, the Amiga Hardware Reference Manual "
               "applies, with one difference: **on SAGA, all classic pointer registers "
               "(BPLxPT, SPRxPT, COPxLC, BLTxPT, AUDxLC, DSKPT) are 32 bits wide and "
               f"reach all RAM** ({WDS}). Their pages in the "
               "original still say 18 bits. FMODE (`$DFF1FC`) bit 4 \"SAGA\" enables "
               "the SAGA features (original); among them, it lets the Copper write "
               f"above `$DFF1FF` and do 32-bit moves ({BGS}, see "
               "[colour-ports.md](colour-ports.md)).", "",
               "### Reading back write-only registers", "",
               "Every write-only register at `$DFF000`–`$DFF1FF` reads back at the "
               f"same offset in `$DFE000`–`$DFE1FF` ({WDS}). This holds for the "
               "classic and the SAGA registers in that range, for example DMACON "
               "`$DFF096` at `$DFE096`, GFXMODE `$DFF1F4` at `$DFE1F4` and the pointer "
               "position `$DFF1D0` at `$DFE1D0`. The original doesn't mention it.", "",
               "### Access codes (original)", "",
               "| Code | Meaning |", "|---|---|"]
    details += [f"| {k} | {v} |" for k, v in ACCESS.items()]
    details += ["", "### Files", "", "| Topic | File |", "|---|---|"]
    details += [f"| {t} | [{f}]({f}) |" for f, t in FILES]
    details += ["", "### Register map", "",
                "| Address | Name | Access | File |", "|---|---|---|---|"]
    for f, _ in FILES:
        if f == "arne-channels.md":
            n = len(groups.get(f, []))
            details.append(f"| `$DFF400`–`$DFF4FF` | AUD0–AUD15: L, LEN, VOL, CTRL, PER "
                           f"({n} rows) | W | [{f}]({f}) |")
            continue
        for r in groups.get(f, []):
            details.append(f"| `${r['addr']}` | {md(r['name'])} | {md(r['access'])} | "
                           f"[{f}]({f}) |")
    details += ["", "Not in the original, added from ApolloLib (SRC): PIP 2 at "
                "`$DFF3B0`–`$DFF3C2` and its colour port `$DFF37C` ([pip.md](pip.md)); "
                "the pointer sprite at `$DFD000`, `$DFF3A8` and `$DFF3AA` "
                "([pointer.md](pointer.md)).", "",
                "### Corrections to the original", "",
                "Applied by the converter; the original should be fixed the same way.", "",
                "| Address | Field | Original | Corrected | Why |", "|---|---|---|---|---|"]
    details += [f"| `${a}` | {f} | {md(o)} | {md(n)} | {md(w)} |" for a, f, o, n, w in applied]
    details += ["", "Wrong or missing page links in the original: the 32-bit Arne "
                "rows link to the classic Paula pages (`audxlch.htm`, `audxvol.htm`, "
                "`audxdat.htm`), the PIP rows to a page that doesn't exist. The "
                "converter uses `audxl.htm`, `audxlen.htm`, `audnvol.htm`, "
                "`audxctrl.htm` and `audxper.htm` for Arne.", "",
                "### Open questions", ""]
    details += [f"{n}. {q}" for n, q in enumerate(OPEN, 1)]
    return doc("index.md", "SAGA registers (SAGA-specific)",
               ["saga-video-isabelle", "saga-audio-arne", "saga-3d-maggie", "general"],
               ["saga", "registers", "index"],
               "The SAGA-specific chipset registers of the Apollo V4, converted from the "
               "official SAGA register documentation: video (chunky plane, colour "
               "ports, PIP, pointer), Arne audio, Maggie 3D, input and system "
               "registers. Classic OCS/ECS/AGA registers are not repeated here.",
               details,
               ["- SAGA contains the classic chipset at its classic addresses. The "
                "registers here are added on top of it, mostly at `$DFF1E6`–`$DFF1F4`, "
                "`$DFF200`–`$DFF29F` and `$DFF380`–`$DFF4FF`.",
                "- Classic pointers are 18 (OCS) or 21 (ECS/AGA) bits; on SAGA they "
                "are 32 bits."],
               ["DO look up a classic register in the HRM, and its SAGA-specific "
                "registers here.",
                "DON'T use a register listed under the open questions without checking "
                "it on real hardware."],
               sources=[APOLLOLIB, WD, BIGGUN],
               basis=["core-developer", "official", "source-code"])


def build():
    rows, keep, applied = saga_rows()
    parts = [index(rows, keep, applied), chunky_plane(keep), colour_ports(keep),
             pip(keep), pointer(keep), display_control(keep), collisions(keep),
             arne_channels(keep), arne_dma(keep), maggie(keep), inputs(keep),
             system(keep)]
    return dict(parts)


# ------------------------------------------------------------ status, check

STATUS_RE = re.compile(r"^(status|last_verified):.*\n", re.M)


def body(text):
    return text.split("\n---\n", 1)[-1]


def keep_status(old, new):
    """Keep the status a maintainer gave a file while its body is unchanged."""
    if old is None or body(old) != body(new):
        return new
    fields = "".join(m.group(0) for m in STATUS_RE.finditer(old))
    return STATUS_RE.sub("", new, count=1).replace(
        "origin: ", fields + "origin: ", 1) if fields else new


def main():
    files = build()
    out = os.path.join(ROOT, OUTDIR)
    existing = set(os.listdir(out)) if os.path.isdir(out) else set()
    stale = []
    for rel, text in files.items():
        p = os.path.join(out, rel)
        old = open(p, encoding="utf-8").read() if os.path.isfile(p) else None
        files[rel] = text = keep_status(old, text)
        if old != text:
            stale.append(rel)
    extra = sorted(existing - set(files))
    if "--check" in sys.argv:
        if stale or extra:
            for s in stale + extra:
                print(f"out of date: {OUTDIR}/{s}", file=sys.stderr)
            sys.exit(1)
        print("OK")
        return
    os.makedirs(out, exist_ok=True)
    for rel in stale:
        with open(os.path.join(out, rel), "w", encoding="utf-8") as f:
            f.write(files[rel])
    for rel in extra:
        print(f"not generated any more, remove by hand: {OUTDIR}/{rel}")
    print(f"Wrote {len(stale)} of {len(files)} file(s) in {OUTDIR}/")


if __name__ == "__main__":
    main()
