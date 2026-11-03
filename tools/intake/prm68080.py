#!/usr/bin/env python3
"""Document intake: convert the Apollo 68080 Programmer's Reference Manual
(sources/official/AC68080PRM.odt) into core/cpu-68080/prm/.

  prm68080.py           regenerate core/cpu-68080/prm/
  prm68080.py --check   exit 1 if the generated files are out of date

The ODT is leading (CONTRIBUTING.md section 11). Never edit the generated
files: change the ODT, or this script, and regenerate. Uses only the Python
standard library.

The ODT has no semantic headings; its layout is visual. This script relies on
the manual's fixed page structure: one page per instruction with a
"MNEMONIC     MNEMONIC" title line, followed by Operation, Syntax, Short,
Description, condition codes, encoding tables, an example and notes.
Diagrams and drawings are described in text by the renderers below.
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = "sources/official/AC68080PRM.odt"
OUTDIR = "core/cpu-68080/prm"
OWNER = "WDrijver"
SOURCE_NAME = ("Apollo 68080 Programmer's Reference Manual, "
               "AC68080PRM.odt (update okt 2026)")

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "chart": "urn:oasis:names:tc:opendocument:xmlns:chart:1.0",
}
O, T, TB, D, S, FO = (f"{{{NS[k]}}}" for k in
                      ("office", "text", "table", "draw", "style", "fo"))

# Text colors and cell backgrounds the manual uses to gray things out.
GRAY_TEXT = {"#b2b2b2", "#999999", "#808080"}
GRAY_CELL = {"#dddddd", "#b2b2b2"}


# ---------------------------------------------------------------- parsing

class Para:
    def __init__(self, style, text, gray, frames, gray_any=False):
        self.style, self.text, self.gray, self.frames = \
            style, text, gray, frames
        self.gray_any = gray_any

    def __repr__(self):
        return f"Para({self.text!r})"


class Cell:
    def __init__(self, text, span=1, covered=False, shaded=None):
        self.text, self.span, self.covered, self.shaded = \
            text, span, covered, shaded


class Table:
    def __init__(self, name, rows):
        self.name, self.rows = name, rows

    def texts(self):
        return [[c.text for c in r] for r in self.rows]


class Frame:
    def __init__(self, name, blocks, obj=None):
        self.name, self.blocks, self.obj = name, blocks, obj


class Parser:
    def __init__(self, odt):
        self.zip = zipfile.ZipFile(odt)
        root = ET.fromstring(self.zip.read("content.xml"))
        self.color, self.bg = {}, {}
        for st in root.iter(S + "style"):
            name = st.get(S + "name")
            tp = st.find(S + "text-properties")
            if tp is not None and tp.get(FO + "color"):
                self.color[name] = tp.get(FO + "color").lower()
            cp = st.find(S + "table-cell-properties")
            if cp is not None and cp.get(FO + "background-color"):
                self.bg[name] = cp.get(FO + "background-color").lower()
        self.blocks = self.walk(root.find(O + "body").find(O + "text"))

    def is_gray(self, e):
        return self.color.get(e.get(T + "style-name")) in GRAY_TEXT

    def inline(self, e, gray, frames, runs):
        """Collect text runs (text, gray) of a paragraph."""
        g = gray or self.is_gray(e)
        if e.text:
            runs.append((e.text, g))
        for c in e:
            if c.tag == T + "s":
                runs.append((" " * int(c.get(T + "c", "1")), g))
            elif c.tag == T + "tab":
                runs.append(("\t", g))
            elif c.tag == T + "line-break":
                runs.append(("\n", g))
            elif c.tag == D + "frame":
                frames.append(self.frame(c))
            elif c.tag.startswith(D):
                pass  # shapes without text
            else:
                self.inline(c, g, frames, runs)
            if c.tail:
                runs.append((c.tail, g))

    def frame(self, f):
        box = f.find(D + "text-box")
        obj = f.find(D + "object")
        blocks = self.walk(box) if box is not None else []
        href = obj.get("{http://www.w3.org/1999/xlink}href") if obj is not None else None
        return Frame(f.get(D + "name"), blocks, href)

    def para(self, p):
        runs, frames = [], []
        self.inline(p, False, frames, runs)
        text = "".join(t for t, _ in runs)
        visible = [g for t, g in runs if t.strip()]
        gray = bool(visible) and all(visible)
        para = Para(p.get(T + "style-name"), text, gray, frames, any(visible))
        para.runs = runs
        return para

    def table(self, t):
        rows = []
        for r in t.iter(TB + "table-row"):
            row = []
            for c in r:
                rep = int(c.get(TB + "number-columns-repeated", "1"))
                if c.tag == TB + "table-cell":
                    paras = [self.para(p) for p in c.iter(T + "p")]
                    text = " / ".join(p.text.strip() for p in paras
                                      if p.text.strip())
                    span = int(c.get(TB + "number-columns-spanned", "1"))
                    shaded = self.bg.get(c.get(TB + "style-name"))
                    for _ in range(min(rep, 64)):
                        row.append(Cell(text, span, False, shaded))
                elif c.tag == TB + "covered-table-cell":
                    for _ in range(min(rep, 64)):
                        row.append(Cell("", 1, True))
            rows.append(row)
        return Table(t.get(TB + "name"), rows)

    def walk(self, e):
        out = []
        for c in e:
            if c.tag in (T + "p", T + "h"):
                out.append(self.para(c))
            elif c.tag == TB + "table":
                out.append(self.table(c))
            elif c.tag in (T + "list", T + "list-item", T + "list-header",
                           T + "section"):
                out += self.walk(c)
        return out

    def chart_rows(self, href):
        """Data table of an embedded chart object."""
        path = href.lstrip("./") + "/content.xml"
        root = ET.fromstring(self.zip.read(path))
        rows = []
        for r in root.iter(TB + "table-row"):
            rows.append(["".join(c.itertext()).strip() for c in r
                         if c.tag == TB + "table-cell"])
        return rows


# ------------------------------------------------------------ text helpers

def clean(s):
    """Collapse layout whitespace (tabs, runs of spaces) to single spaces."""
    return re.sub(r"[ \t ]+", " ", s.replace("\n", " ")).strip()


def md(s):
    """Escape text for Markdown prose: keep <ea> and friends visible."""
    s = clean(s)
    s = s.replace("(next page)", "(next page in the original)")
    s = s.replace("see next page.", "see the next page in the original.")
    s = s.replace("<", "&lt;").replace(">", "&gt;").replace("*", "\\*")
    return s.replace("_", "\\_").replace("|", "\\|")


def code(s):
    s = clean(s)
    return f"`` {s} ``" if "`" in s else f"`{s}`"


def cell_md(s):
    return md(s) if s else ""


TITLE_RE = re.compile(r"^\s*([A-Za-z0-9]+(?: sr)?)\s{4,}([A-Za-z0-9]+(?: sr)?)\s*$")


def entry_title(p):
    if not isinstance(p, Para):
        return None
    m = TITLE_RE.match(p.text.replace("\t", "    "))
    return m.group(1) if m else None


def is_bit_header(row):
    vals = [c.text for c in row if not c.covered]
    return vals and all(v.isdigit() for v in vals) and \
        [int(v) for v in vals] == list(range(len(vals) - 1, -1, -1))


def is_encoding(t):
    first = t.rows[0]
    if is_bit_header(first):
        return True
    # A few encoding tables lack the bit-number header row.
    return len(first) == 16 and any(c.span > 1 for c in first) and \
        all(c.covered or len(c.text) <= 12 for c in first)


def is_cc(t):
    head = [c.text for c in t.rows[0]]
    return head[:5] == ["X", "N", "Z", "V", "C"] or head[:4] == ["N", "Z", "I", "nan"]


def is_value(t):
    """Register or memory content drawn as boxes of one hex digit each."""
    for r in t.rows:
        cells = [c.text for c in r]
        while cells and cells[-1] == "":
            cells.pop()
        if not cells:
            continue
        body = cells[:-1] if len(cells[-1]) > 1 else cells
        if any(len(v) > 1 for v in body):
            return False
    return True


def hex_row(cells):
    """'.. .. 00 12' from one row of digit boxes, plus a trailing label."""
    vals = [c.text for c in cells if not c.covered]
    label = ""
    if vals and len(vals[-1]) > 1:
        label = vals.pop()
    while len(vals) > 16 and vals[-1] == "":
        vals.pop()
    while vals and vals[-1] == "" and len(vals) % 2:
        vals.pop()
    digits = [v if v else "." for v in vals]
    groups = ["".join(digits[i:i + 2]) for i in range(0, len(digits), 2)]
    text = " ".join(groups)
    return text + (f"   {clean(label)}" if label else "")


def encoding_rows(t, word_offset=0):
    """Render an encoding table as (word, bits, content) rows."""
    rows = t.rows
    width = 16
    if is_bit_header(rows[0]):
        width = len([c for c in rows[0] if not c.covered])
        rows = rows[1:]
    out = []
    for w, row in enumerate(rows, start=1 + word_offset):
        cols = row[:width] + [Cell("")] * (width - len(row[:width]))
        segs, pos = [], 0
        while pos < width:
            c = cols[pos]
            hi = width - 1 - pos
            if c.covered:
                pos += 1
                continue
            if c.span > 1:
                segs.append([hi, hi - c.span + 1, c.text, False, False])
                pos += c.span
                continue
            v = c.text
            const = v in ("0", "1")
            last = segs[-1] if segs else None
            if last and last[3] and const:
                last[1] = hi
                last[2] += v
            elif last and not const and not last[3] and last[2] == v \
                    and last[1] == hi + 1 and last[4]:
                # One field drawn as several one-bit boxes (c c c, S S).
                last[1] = hi
            else:
                segs.append([hi, hi, v, const, True])
            pos += 1
        for hi, lo, v, const, _ in segs:
            bits = f"{hi}" if hi == lo else f"{hi}–{lo}"
            if const:
                content = f"`{v}`"
            elif v == "":
                content = "(empty in the original)"
            else:
                content = md(v)
            out.append((w, bits, content))
    return out


def render_encoding(t, label=None):
    lines = []
    if label:
        lines += [f"{md(label.rstrip(':'))}:", ""]
    lines += ["| Word | Bits | Content |", "|---|---|---|"]
    for w, bits, content in encoding_rows(t):
        lines.append(f"| {w} | {bits} | {content} |")
    return lines + [""]


def render_cc(t, label="Condition codes"):
    head = [c.text for c in t.rows[0]]
    vals = [c.text for c in t.rows[1]] if len(t.rows) > 1 else [""] * len(head)
    n = len([h for h in head if h])
    head, vals = head[:n], vals[:n]
    return [f"| {' | '.join(head)} |", "|" + "---|" * n,
            "| " + " | ".join(v or " " for v in vals) + " |", ""]


def render_grid(t):
    """Fallback: a Markdown table with the first row as header. A header cell
    spanning several columns becomes one column; the cells below it are
    joined (digits without a separator: '0 1 0' becomes '010')."""
    head = t.rows[0]
    groups, pos = [], 0     # (first column, last column, title)
    for c in head:
        if c.covered:
            continue
        groups.append((pos, pos + c.span - 1, c.text))
        pos += c.span
    out = ["| " + " | ".join(cell_md(g[2]) for g in groups) + " |",
           "|" + "---|" * len(groups)]
    for r in t.rows[1:]:
        cols = [[] for _ in groups]
        for k, c in enumerate(r):
            if c.covered or not c.text:
                continue
            for gi, (lo, hi, _) in enumerate(groups):
                if lo <= k <= hi:
                    cols[gi].append(c.text)
                    break
            else:
                cols[-1].append(c.text)
        vals = ["".join(v) if all(len(x) == 1 and x.isdigit() for x in v)
                else " ".join(v) for v in cols]
        if any(vals):
            out.append("| " + " | ".join(cell_md(v) for v in vals) + " |")
    return out + [""]


def render_format(t, label=None):
    """A 32-bit memory format table (FMOVEM): bit 31 first, one row per
    long word. Runs of the same letter, of empty boxes, and of consecutive
    numbers become one row."""
    lines = []
    if label:
        lines += [f"{md(label.rstrip(':'))}:", ""]
    lines += ["| Long word | Bits | Content |", "|---|---|---|"]
    for w, row in enumerate(t.rows[1:], start=1):
        vals = [c.text for c in row if not c.covered][:32]
        vals += [""] * (32 - len(vals))
        runs = []
        for k, v in enumerate(vals):
            bit = 31 - k
            last = runs[-1] if runs else None
            num = v.isdigit()
            if last and ((num and last[3] and int(v) == last[4] + 1) or
                         (not num and not last[3] and v == last[2])):
                last[1] = bit
                if num:
                    last[4] = int(v)
                continue
            runs.append([bit, bit, v, num, int(v) if num else None])
        for hi, lo, v, num, end in runs:
            bits = f"{hi}" if hi == lo else f"{hi}–{lo}"
            if num:
                content = (f"box numbered {v}" if hi == lo else
                           f"boxes numbered {v}–{end}")
            elif v == "":
                content = "(empty in the original)"
            else:
                content = md(v) if hi == lo else f"{md(v)} ({hi - lo + 1} bits)"
            lines.append(f"| {w} | {bits} | {content} |")
    return lines + [""]


def is_format(t):
    return is_bit_header(t.rows[0]) and \
        len([c for c in t.rows[0] if not c.covered]) == 32


# ------------------------------------------------------------- segmenting

BACK_SECTIONS = {
    "SUPERSCALAR": "superscalar",
    "INSTRUCTION FUSING": "instruction-fusing",
    "INSTRUCTION EFFICIENTCY": "instruction-efficiency",
    "PIPELINE STAGE": "pipeline",
    "INSTRUCTION TIMING": "instruction-timing",
    "OPTIMIZING": "optimizing",
    "TRACE": "trace",
    "SPECS": "specs",
}
FRONT_SECTIONS = {
    "68080 user programming model.": "programming-model",
    "THE 080 INTEGER UNIT.": "integer-unit",
    "THE 080 FLOATING POINT UNIT.": "fpu-unit",
    "THE 080 AMMX UNIT.": "ammx-unit",
    "B registers.": "b-registers",
    "Apollo bit.": "apollo-bit",
    "Ammx vector handling by type, source or destination match:": "vector-types",
}


def segment(blocks):
    """Split the document into front sections, instruction entries and back
    sections. Returns (front, entries, back), each a list of
    (key, [blocks])."""
    front, entries, back = [("cover", [])], [], []
    unit = None  # integer, ammx, fpu
    cur = front[-1][1]
    for b in blocks:
        if isinstance(b, Para):
            head = clean(b.text)
            title = entry_title(b)
            if head in ("INTEGER INSTRUCTIONS", "AMMX INSTRUCTIONS",
                        "FLOATING POINT INSTRUCTIONS"):
                # The front pages list all three units; the integer pages
                # follow without a heading of their own.
                unit = {"I": "integer", "A": "ammx", "F": "fpu"}[head[0]] \
                    if entries else "integer"
                cur = []  # the instruction lists are rendered in the index
            elif head in FRONT_SECTIONS and not entries:
                front.append((FRONT_SECTIONS[head], []))
                cur = front[-1][1]
            elif head.split(" ")[0] in ("SUPERSCALAR",) or head in BACK_SECTIONS:
                key = BACK_SECTIONS[head.split(" ")[0] if head.startswith("SUPERSCALAR") else head]
                back.append((key, []))
                cur = back[-1][1]
                unit = None
            elif title and unit and not back:
                entries.append(((unit, title, b), []))
                cur = entries[-1][1]
            else:
                cur.append(b)
        else:
            cur.append(b)
    return front, entries, back


# ------------------------------------------------------- instruction pages

FIELD_RE = re.compile(r"^(Operation|Syntax|Short|Description|Constraints|"
                      r"(?:FP )?Condition Codes):\s*(.*)$", re.DOTALL)
CONT_RE = re.compile(r"^\t+\S")


class Entry:
    """One instruction page (or two pages with the same mnemonic)."""

    def __init__(self, unit, mnemonic):
        self.unit, self.mnemonic = unit, mnemonic
        self.pages = []


def next_block(blocks, i):
    """The next block after i that is not an empty paragraph."""
    for b in blocks[i + 1:]:
        if isinstance(b, Table) or b.text.strip() or b.frames:
            return b
    return None


def is_label(b, nxt):
    """A short paragraph that names the table right after it."""
    s = clean(b.text)
    return isinstance(nxt, Table) and len(s) < 40 and not s.endswith(".")


def parse_page(title_para, blocks):
    page = {"gray_title": title_para.gray, "name": [], "fields": [],
            "cc": None, "cc_text": None, "body": []}
    i = 0
    # Full instruction name: the bold title lines right after the heading.
    while i < len(blocks) and isinstance(blocks[i], Para) and \
            blocks[i].style in ("P14", "P33") and \
            not FIELD_RE.match(blocks[i].text.strip()):
        page["name"].append(clean(blocks[i].text))
        i += 1
    state = "fields"
    while i < len(blocks):
        b = blocks[i]
        if isinstance(b, Table):
            if is_cc(b) and page["cc"] is None:
                page["cc"] = b
            else:
                state = "body"
                page["body"].append(b)
            i += 1
            continue
        t = b.text.strip("\n")
        s = t.strip()
        m = FIELD_RE.match(s)
        if m and m.group(1).endswith("Condition Codes") \
                and page["cc_text"] is None:
            page["cc_text"] = clean(m.group(2))
            i += 1
            continue
        if state == "fields":
            if not s:
                i += 1
                continue
            if m:
                page["fields"].append([m.group(1), [m.group(2)]])
                i += 1
                continue
            if page["fields"] and (CONT_RE.match(t) or t.startswith(" \t")):
                page["fields"][-1][1].append(t)
                i += 1
                continue
            if page["fields"] and not s.endswith(":") and \
                    not re.match(r"^(Note|Example)\b", s) and \
                    not is_label(b, next_block(blocks, i)):
                if s.lower().startswith("where"):
                    target = [f for f in page["fields"] if f[0] == "Syntax"]
                else:
                    target = [page["fields"][-1]]
                (target or [page["fields"][-1]])[0][1].append(t)
                i += 1
                continue
            state = "body"
        page["body"].append(b)
        i += 1
    return page


def field_text(lines):
    vals = [clean(v) for v in lines if clean(v)]
    return vals


def split_cols(raw):
    """Tab-separated columns of one original line."""
    return [clean(p) for p in re.split(r"\t+", raw.strip()) if clean(p)]


def render_fields(page):
    out = ["| Field | Value |", "|---|---|"]
    for key, lines in page["fields"]:
        if key in ("Operation", "Syntax"):
            shown = []
            for raw in lines:
                cols = split_cols(raw)
                if not cols:
                    continue
                first, rest = cols[0], cols[1:]
                linea = "*LineA" in rest
                rest = [r for r in rest if r != "*LineA"]
                comment = " ".join(rest)
                if first.lower().startswith("where") or (
                        key == "Operation" and not re.search(r"[→=?]", first)):
                    cell = md(first)
                else:
                    cell = code(first)
                if comment:
                    cell += f" {md(comment)}"
                if linea:
                    cell += " (LineA instruction)"
                shown.append(cell)
            out.append(f"| {key} | {'<br>'.join(shown)} |")
        else:
            out.append(f"| {key} | {md(' '.join(field_text(lines)))} |")
    if page["cc_text"] is not None:
        txt = page["cc_text"] or "see table"
        label = "FP condition codes" if page.get("fp") else "Condition codes"
        out.append(f"| {label} | {md(txt)} |")
    return out + [""]


NOTE_RE = re.compile(r"^Note:?\s*(.*)$")
EXAMPLE_RE = re.compile(r"^\s*Examples?\b[^.]*:?\s*$")
RESULT_RE = re.compile(r"^\s*Result\b:?\s*(.*)$")
CODE_RE = re.compile(r"^(?: {2,}|\t)\s*[a-z][a-z0-9.]*(?:\s|$)")
ASM_RE = re.compile(r"^[a-z][a-z0-9.]*\s+[^\s]*[,(][^\s]*\s*$")


def is_code_line(t):
    return bool(CODE_RE.match(t)) and not re.match(r"^\s+\d", t)


def is_pre_line(t):
    """Indented text whose alignment matters (tables drawn with spaces)."""
    return bool(re.match(r"^ {2,}\S", t)) and not is_code_line(t)


class Body:
    """Renders the body of an instruction page into three sections."""

    def __init__(self):
        self.sec = {"encoding": [], "example": [], "notes": []}
        self.state = "encoding"
        self.has_encoding = False
        self.has_format = False
        self.buf_kind, self.buf = None, []

    def flush(self):
        if self.buf:
            self.out.extend([f"```{self.buf_kind}"] + self.buf + ["```", ""])
        self.buf_kind, self.buf = None, []

    def add(self, kind, line):
        if self.buf_kind != kind:
            self.flush()
            self.buf_kind = kind
        self.buf.append(line)

    @property
    def out(self):
        return self.sec[self.state]

    def text(self, line):
        self.flush()
        self.out.append(f"- {line}")

    def switch(self, state):
        self.flush()
        self.state = state


def bank_pseudocode(blocks, i):
    """BANK: the 'If CCccc <> 0 ... endif' lines form one block of pseudo
    code. Returns the lines and the index after them."""
    lines = []
    while i < len(blocks) and isinstance(blocks[i], Para):
        s = blocks[i].text.rstrip()
        lines.append(s.replace("\t", "    "))
        i += 1
        if s.strip() == "endif":
            break
    return lines, i


def bank_modes(blocks, i):
    """BANK: the two-column table of AA/BB/DD values drawn with tabs."""
    head = split_cols(blocks[i].text)
    rows = []
    i += 1
    while i < len(blocks) and isinstance(blocks[i], Para) and \
            re.match(r"^\d\d = ", blocks[i].text):
        b = blocks[i]
        parts = re.split(r"\t+", b.text.strip(), maxsplit=1)
        left = clean(parts[0])
        right = clean(parts[1]) if len(parts) > 1 else ""
        m = re.match(r"^(\d\d) = (.*)$", left)
        m2 = re.match(r"^(\d\d) = (.*)$", right)
        rows.append((m.group(1), m.group(2), m2.group(2) if m2 else right))
        i += 1
    out = [f"| Value | {md(head[0])} | {md(' '.join(head[1:]))} |",
           "|---|---|---|"]
    out += [f"| `{v}` | {md(a)} | {md(b)} |" for v, a, b in rows]
    return out + [""], i


def render_body(blocks, special=None):
    """Render the part of a page after the fields and condition codes.
    Returns (sections, has_encoding)."""
    r = Body()
    pending = None   # paragraph that labels the next table
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if isinstance(b, Table):
            label = clean(pending) if pending else ""
            pending = None
            if is_format(b):
                r.flush()
                r.has_format = True
                r.out.extend(render_format(b, label))
            elif is_encoding(b) and r.state == "encoding":
                r.flush()
                r.has_encoding = True
                r.out.extend(render_encoding(b, label))
            elif is_cc(b):
                r.flush()
                r.out.extend(render_cc(b))
            elif is_value(b):
                rows = [row for row in b.rows if any(c.text for c in row)]
                if not rows:
                    r.add("text", f"{label}: (all boxes empty in the original)")
                for k, row in enumerate(rows):
                    if not label:
                        r.add("text", hex_row(row))
                    else:
                        prefix = f"{label}: " if k == 0 else " " * (len(label) + 2)
                        r.add("text", prefix + hex_row(row))
            else:
                r.flush()
                if label:
                    r.out.extend([f"{md(label.rstrip(':'))}:", ""])
                r.out.extend(render_grid(b))
            i += 1
            continue
        for f in b.frames:
            if special and f.name in special:
                r.flush()
                r.out.extend(special[f.name](f, blocks, i))
        t = b.text
        s = t.strip()
        if not s or re.fullmatch(r"(\[F\d+\])+", s):
            i += 1
            continue
        if pending:
            # The label was not followed by a table after all.
            r.text(md(pending))
            pending = None
        if s.startswith("If CCccc"):
            lines, i = bank_pseudocode(blocks, i)
            r.flush()
            r.out.extend(["```text"] + lines + ["```", ""])
            continue
        if s.startswith("Data & Float"):
            rows, i = bank_modes(blocks, i)
            r.flush()
            r.out.extend(rows)
            continue
        m = NOTE_RE.match(s)
        if m:
            r.switch("notes")
            if m.group(1):
                r.text(md(m.group(1)))
            i += 1
            continue
        if EXAMPLE_RE.match(s) and len(s) < 40:
            r.switch("example")
            i += 1
            continue
        m = RESULT_RE.match(s)
        if m and r.state in ("example", "encoding"):
            if r.state != "example":
                r.switch("example")
            rest = clean(m.group(1))
            r.add("text", f"Result of {rest}:" if rest else "Result:")
            i += 1
            continue
        nxt = next_block(blocks, i)
        if is_label(b, nxt) and not is_code_line(t):
            pending = s
            i += 1
            continue
        if is_code_line(t) or (r.state == "example" and ASM_RE.match(s)):
            line = t.replace("\n", " ").rstrip()
            if not t[0].isspace():
                line = "    " + line
            if s == "or":
                line = "    ; or"
            if r.state == "encoding" and r.has_encoding:
                r.switch("example")
            r.add("asm", line)
            i += 1
            continue
        if is_pre_line(t):
            r.add("text", t.rstrip().replace("\t", "    "))
            i += 1
            continue
        for part in t.split("\n"):
            if part.strip():
                line = md(part)
                if b.gray:
                    line += " *(grayed out in the original)*"
                r.text(line)
        i += 1
    if pending:
        r.text(md(pending))
    r.flush()
    for k in r.sec:
        fixed = []
        lines = r.sec[k]
        for j, ln in enumerate(lines):
            fixed.append(ln)
            if ln.startswith("- ") and j + 1 < len(lines) and \
                    lines[j + 1] and not lines[j + 1].startswith("- "):
                fixed.append("")
        r.sec[k] = fixed
    heading = "Encoding" if r.has_encoding else \
        ("Memory formats" if r.has_format else "More details")
    return r.sec, heading


# ----------------------------------------------- per-instruction metadata

# slug, kind ("new" or the 68k mnemonic it extends), and the 68080 addition
# in one line. Facts restated from the manual's own pages.
META = {
    # integer
    "ADDIW": ("addiw", "new", None),
    "ADDQ": ("addq-bn", "ADDQ", "ADDQ with a B address register as destination"),
    "BANK": ("bank", "new", None),
    "Bcc": ("bcc-s-plus", "Bcc", "the .S+ short form with an odd displacement byte that doubles the short range"),
    "BRA": ("bra-s-plus", "BRA", "the .S+ short form with an odd displacement byte that doubles the short range"),
    "BSR": ("bsr-s-plus", "BSR", "the .S+ short form with an odd displacement byte that doubles the short range"),
    "CLR": ("clr-q", "CLR", "the quad size CLR.Q (LineA encoding)"),
    "CMP": ("cmp-bn", "CMP", "CMP with a B address register as source"),
    "CMPIW": ("cmpiw", "new", None),
    "DBcc": ("dbcc-l", "DBcc", "DBcc.L with a 32-bit loop counter"),
    "EXTUB": ("extub-extuw", "new", None),
    "LEA": ("lea-bn", "LEA", "LEA with a B address register as destination, and LEA (Bn),An"),
    "MOV3Q": ("mov3q", "new", None),
    "MOVE": ("move-bn", "MOVE", "MOVE with a B address register as source"),
    "MOVEA": ("movea-bn", "MOVEA", "MOVEA with a B address register as destination"),
    "MOVE sr": ("move-sr", "MOVE from SR", "reading SR in user mode, and setting or clearing SR bit 11 in user mode"),
    "MOVE16": ("move16", "MOVE16", "no 16-byte alignment restriction"),
    "MOVE2": ("move2", "new", None),
    "MOVEC": ("movec", "MOVEC", "new control registers (event counters, PCR) that user mode may read"),
    "MOVEH": ("moveh", "new", None),
    "MOVEX": ("movex", "new", None),
    "MOVIW": ("moviw", "new", None),
    "MOVS": ("movs", "new", None),
    "MOVZ": ("movz", "new", None),
    "MOVZ2": ("movz2", "new", None),
    "PERM": ("perm", "new", None),
    "SUBQ": ("subq-bn", "SUBQ", "SUBQ with a B address register as destination"),
    "TOUCH": ("touch", "new", None),
    # ammx
    "AMMX": ("ammx-format", "new", None),
    "BFLY": ("bfly", "new", None),
    "BSEL": ("bsel", "new", None),
    "C2P": ("c2p", "new", None),
    "LOAD": ("load", "new", None),
    "LOADI": ("loadi", "new", None),
    "LSdQ": ("lsdq", "new", None),
    "MINTERM": ("minterm", "new", None),
    "PACK3216": ("pack3216", "new", None),
    "PACKUSWB": ("packuswb", "new", None),
    "PADD": ("padd", "new", None),
    "PAND": ("pand", "new", None),
    "PANDN": ("pandn", "new", None),
    "PAVGB": ("pavgb", "new", None),
    "PCMPccB": ("pcmpccb", "new", None),
    "PCMPccW": ("pcmpccw", "new", None),
    "PEOR": ("peor", "new", None),
    "PMAXxB": ("pmaxb", "new", None),
    "PMAXxW": ("pmaxw", "new", None),
    "PMINxB": ("pminb", "new", None),
    "PMINxW": ("pminw", "new", None),
    "PMUL": ("pmul", "new", None),
    "PMULA": ("pmula", "new", None),
    "POR": ("por", "new", None),
    "PSUB": ("psub", "new", None),
    "REX": ("rex", "new", None),
    "STORE": ("store", "new", None),
    "STOREC": ("storec", "new", None),
    "STOREI": ("storei", "new", None),
    "STOREILM": ("storeilm", "new", None),
    "STOREM": ("storem", "new", None),
    "STOREM3": ("storem3", "new", None),
    "TEX": ("tex", "new", None),
    "TRANS": ("trans", "new", None),
    "UNPACK1632": ("unpack1632", "new", None),
    "VPERM": ("vperm", "new", None),
    # fpu
    "FDBcc": ("fdbcc-l", "FDBcc", "FDBcc.L with a 32-bit loop counter"),
    "FMOVE": ("fmove-dn", "FMOVE", "double and extended format to and from data registers, and FSTOREI/FLOADI for E registers"),
    "FMOVERZ": ("fmoverz", "new", None),
    "FMOVEM": ("fmovem", "FMOVEM", "a different extended format layout in memory"),
    "FPU": ("fpu-format", "new", None),
    "FADD": ("fadd-3op", "FADD", "a 3-operand form (Apollo FPU, line-F id 6)"),
    "FDIV": ("fdiv-3op", "FDIV", "a 3-operand form (Apollo FPU, line-F id 6)"),
    "FMUL": ("fmul-3op", "FMUL", "a 3-operand form (Apollo FPU, line-F id 6)"),
    "FSUB": ("fsub-3op", "FSUB", "a 3-operand form (Apollo FPU, line-F id 6)"),
    "FSQRT": ("fsqrt-3op", "FSQRT", "a 3-operand form (Apollo FPU, line-F id 6)"),
}

# Rules the manual states explicitly, as DO / DON'T.
RULES = {
    "CLR": ["DON'T use CLR.Q: the manual says it is only available on cores 10280 to 10904.",
            "DO set the Apollo bit (SR bit 11, `ori #$800,sr`) before any LineA instruction."],
    "MOV3Q": ["DON'T use MOV3Q: the manual says it is only available on cores 10280 to 10904.",
              "DO set the Apollo bit (SR bit 11, `ori #$800,sr`) before any LineA instruction."],
    "MOVS": ["DON'T use MOVS: the manual says it is only available on cores 10280 to 10904.",
             "DO set the Apollo bit (SR bit 11, `ori #$800,sr`) before any LineA instruction."],
    "MOVZ": ["DON'T use MOVZ: the manual says it is only available on cores 10280 to 10904.",
             "DO set the Apollo bit (SR bit 11, `ori #$800,sr`) before any LineA instruction."],
    "MOVIW": ["DON'T use the LineA encoding of MOVIW.L: the manual says it is only available on cores 10280 to 10904. The other encoding has no such note."],
    "ADDIW": ["DON'T look for SUBIW.L: it does not exist. Use ADDIW.L with a negative value."],
    "CMPIW": ["DON'T look for SUBIW.L: it does not exist."],
    "LEA": ["DON'T write LEA (Bn),Bm or MOVEA.L Bn,Bm: B to B is not supported."],
    "MOVEA": ["DON'T write LEA (Bn),Bm or MOVEA.L Bn,Bm: B to B is not supported.",
              "DON'T use An or Bn as the source <ea>."],
    "MOVE": ["DON'T use An or Bn as the destination <ea>."],
    "MOVE2": ["DO use a memory <ea>: other modes give unexpected results.",
              "DON'T rely on MOVE2 on V2 cores: the manual says it is not correct there."],
    "MOVZ2": ["DO use a memory <ea>: other modes give unexpected results.",
              "DON'T use MOVZ2 on V2 cores: it is not in V2."],
    "TOUCH": ["DO issue TOUCH 12 to 15 cycles before the data is needed.",
              "DO use only mode 6 (address register indirect with index, brief extension, no multiplier)."],
    "BFLY": ["DO use a consecutive destination pair starting at an even register (for example E0:E1).",
             "DON'T expect saturation: BFLY does not limit results."],
    "MINTERM": ["DO use four consecutive source registers starting at a multiple of 4 (D0-D3, D4-D7, E0-E3, ...).",
                "DON'T use memory operands."],
    "TRANS": ["DO use four consecutive source registers starting at a multiple of 4, and a destination pair starting at an even register.",
              "DON'T use memory operands: data registers only."],
    "UNPACK1632": ["DO use a destination pair starting at an even register (D0:D1, D2:D3, ...)."],
    "VPERM": ["DO use data registers for a, b and d."],
    "PACK3216": ["DON'T use an immediate <vea>."],
    "PACKUSWB": ["DON'T use an immediate <vea>."],
    "STORE": ["DON'T use an immediate <vea>."],
    "STOREC": ["DON'T use an immediate <vea>."],
    "STOREI": ["DON'T use an immediate <vea>."],
    "STOREILM": ["DON'T use an immediate <vea>."],
    "STOREM": ["DON'T use an immediate <vea>."],
    "STOREM3": ["DON'T use an immediate <vea>."],
    "PCMPccB": ["DON'T use PCMPHS/PCMPLO: unsigned higher-or-same is not implemented. Combine PCMPEQ and PCMPHI with POR (see PCMPccW)."],
    "PCMPccW": ["DON'T use PCMPHSW: it is not implemented. Combine PCMPEQW and PCMPHIW with POR."],
    "REX": ["DON'T use B registers.", "DO check the core: REX is available from core 12540."],
    "TEX": ["DON'T use B registers with TEX (An,Ax,Ay*Dm),Dn; it needs core 12540 or later.",
            "DON'T rely on the TEX8.512/TEX16.256/TEX24.64 form beyond tex8.256 and tex16.256: the manual says it seems broken in current cores."],
    "MOVE sr": ["DO use `ori #$800,sr` / `andi #$f7ff,sr` to set or clear the Apollo bit in user mode; other SR bits stay privileged."],
    "MOVEC": ["DON'T write control registers in user mode: MOVEC Rn,Rc is supervisor only. Reading is allowed."],
    "FMOVERZ": ["DON'T use FMOVERZ/FMOVEURZ on V2 cores."],
    "FMOVE": ["DO use FLOADI (D to FP) and FSTOREI (FP to D) when an E register is both operands, so the direction is unambiguous."],
    "FMOVEM": ["DON'T depend on the Motorola extended layout in memory: the 68080 layout differs. Use FMOVE.D to get all bits of a value."],
    "BANK": ["DON'T use banked address modes (AA/BB = 10 or 11 for the ea): the manual marks them not implemented yet."],
    "PERM": ["DON'T bank address registers in PERM: they show up as En."],
}


def entry_meta(m):
    return META.get(m) or META[m.split()[0]]


# Differences the pages state themselves, beyond "new" or "extended".
EXTRA_DIFF = {
    "ADDIW": "ADDIW.L takes the place of the 68020 CALLM instruction (the "
             "original: \"Replaces CALLM\").",
    "MOVE16": "On the 68040, MOVE16 needs 16-byte aligned addresses. The "
              "68080 has no alignment restriction.",
    "MOVE sr": "On the 68010–68060, MOVE from SR is privileged. On the "
               "68000 and the 68080, user mode may read SR.",
    "FMOVEM": "The 68080 stores extended precision in memory in its own "
              "layout (see the formats above). Code that reads the stored "
              "bytes directly may be affected.",
}


def describe_diff(m):
    slug, kind, addition = entry_meta(m)
    if kind == "new":
        out = [f"- The 68000–68060 have no {m}. It is new on the 68080."]
    else:
        out = [f"- The 68000–68060 have {kind}. This page covers only the "
               f"68080 addition: {addition}. For the classic forms, the "
               "Motorola manual applies."]
    if m in EXTRA_DIFF:
        out.append(f"- {EXTRA_DIFF[m]}")
    return out


# Special renderers for content the generic body renderer cannot handle.

def render_movec(pages):
    """MOVEC: two pages. The first lists the control registers, the second
    the PCR bits; both are drawn with tabs in the original."""
    p1, p2 = pages
    lines = ["### Encoding", ""]
    regs, notes = [], []
    for b in p1["body"]:
        if isinstance(b, Table):
            lines += render_encoding(b)
            continue
        s = b.text.strip()
        m = re.match(r"^(\*?)\s*\$([0-9A-Fa-f]{3})\s+(\S+)\s+(.*)$", s)
        if m:
            star, num, name, desc = m.groups()
            gray = "yes" if b.gray else ("partly" if b.gray_any else "no")
            regs.append((star, "$" + num.upper(), name, clean(desc), gray))
        elif s.startswith("Event counters"):
            notes.append(md(s))
        elif s in ("Note:", "PRIVILEGED INSTRUCTION.") or "reading a control" in s:
            continue
        elif s:
            lines.append(f"- {md(s)}")
    lines += ["", "### Control registers", ""] + notes + ["",
              "| Rc | Name | Meaning | Marked * in the original | Grayed out in the original |",
              "|---|---|---|---|---|"]
    for star, num, name, desc, gray in regs:
        lines.append(f"| {num} | {name} | {md(desc)} | "
                     f"{'yes' if star else 'no'} | {gray} |")
    lines += ["", "### PCR: Processor Configuration Register ($808)", ""]
    pcr, speed, extra, mode = [], [], [], None
    for b in p2["body"]:
        if isinstance(b, Table):
            lines += ["Bit layout as drawn in the original:", "",
                      "| Bits | Content |", "|---|---|"]
            for w, bits, content in encoding_rows(b):
                hi_lo = [int(x) + (16 if w == 1 else 0) for x in bits.split("–")]
                lines.append(f"| {'–'.join(str(x) for x in hi_lo)} | {content} |")
            lines.append("")
            continue
        s = b.text.strip()
        cols = split_cols(b.text)
        if not s or s.startswith("808"):
            continue
        if s.startswith("bit(s)"):
            mode = "pcr"
        elif s.startswith("bits 7-0"):
            mode = "speed"
        elif s in ("Note:", "PRIVILEGED INSTRUCTION.") or "reading a control" in s:
            continue
        elif mode == "pcr" and re.match(r"^\d", s):
            pcr.append(cols + [""] * (4 - len(cols)))
        elif mode == "speed" and s.startswith("$"):
            speed.append(cols + [""] * (3 - len(cols)))
        else:
            extra.append(f"- {md(s)}")
    lines += ["| Bits | Name | Default | Comment |", "|---|---|---|---|"]
    lines += [f"| {a} | {md(b)} | {md(c)} | {md(d)} |" for a, b, c, d in pcr]
    lines += ["", "Speed table for bits 7–0, slow to fast:", "",
              "| Bits 7–0 | Mode | Apollopad back+ |", "|---|---|---|"]
    lines += [f"| {a} | {md(b)} | {md(c)} |" for a, b, c in speed]
    lines += [""] + extra
    lines += ["", "### Notes", "", "- PRIVILEGED INSTRUCTION.",
              "- On 68080 reading a control register may be done in user mode.",
              ""]
    return lines


def storem3_frame(f, blocks, i):
    """STOREM3: the frame holds the four result rows; the four paragraphs
    after it name the instruction for each row."""
    t = [b for b in f.blocks if isinstance(b, Table)][0]
    labels = [b.text for b in blocks[i + 1:i + 5]]
    out = ["```text"]
    for lab, row in zip(labels, t.rows):
        parts = [p for p in re.split(r"\t+", lab) if p.strip()]
        out.append(f"{clean(parts[0]):<22} mode {parts[1].strip()}  (a0): {hex_row(row)}")
    out += ["```", ""]
    for b in blocks[i + 1:i + 5]:
        b.text = ""
    return out


# ------------------------------------------------------------ rendering

def frontmatter(title, tags, related, extra_sources=()):
    quoted = '"' + title.replace('\\', '\\\\').replace('"', '\\"') + '"'
    lines = ["---", f"title: {quoted}", "type: reference", f"owner: {OWNER}",
             "status: draft", "origin: official", "components: [cpu-68080]",
             "applies_to:", '  core: "any"', "  os: [any]",
             f"tags: [{', '.join(tags)}]"]
    if related:
        lines.append("related:")
        lines += [f"  - {r}" for r in related]
    lines += ["sources:", f'  - "{SOURCE_NAME}"']
    lines += [f'  - "{s}"' for s in extra_sources]
    lines += [f"generated_from: {SOURCE}", "---", "",
              "<!-- GENERATED by tools/intake/prm68080.py from "
              f"{SOURCE}. Do not edit: change the original and regenerate. -->",
              ""]
    return lines


def pmula_tables(blocks):
    """PMULA: the byte-layout tables (vea, b, Result d) become two tables:
    the layout and the example. Returns (lines, remaining blocks)."""
    rows, keep = {"layout": [], "example": []}, []
    part, result, label = "layout", False, None
    for b in blocks:
        if isinstance(b, Para):
            s = b.text.strip()
            if s in ("vea", "b", "d"):
                label = s
                continue
            if s.startswith("Result"):
                result = True
                continue
            if s.startswith("Example"):
                part, result = "example", False
                continue
            keep.append(b)
            continue
        if is_encoding(b):
            keep.append(b)
            continue
        cells = [c.text for c in b.rows[0] if not c.covered]
        op = f"{label} (result)" if result else label
        rows[part].append([op] + cells)
    out = []
    for part, title in (("layout", "Operand layout"), ("example", "Example")):
        out += [f"**{title}** (one 32-bit pixel; the original names the "
                "bytes alfa, red, green, blue)", "",
                "| Operand | Alfa | Red | Green | Blue | Role |",
                "|---|---|---|---|---|---|"]
        out += ["| " + " | ".join(md(c) for c in r) + " |" for r in rows[part]]
        out.append("")
    return out, keep


def rule_md(rule):
    """Show <ea>-style operands in rules as code."""
    return re.sub(r"(?<!`)(<[a-z]+>)(?!`)", r"`\1`", rule)


def render_entry(unit, mnemonic, pages):
    slug = entry_meta(mnemonic)[0]
    main = pages[0]
    name = " ".join(main["name"])
    title = f"{mnemonic}: {name}" if name else mnemonic
    tags = ["68080", unit, mnemonic.lower().replace(" ", "-")]
    related = [f"{OUTDIR}/index.md"]
    if unit == "ammx" and mnemonic != "AMMX":
        related.append(f"{OUTDIR}/ammx/ammx-format.md")
    if unit == "fpu" and mnemonic in ("FADD", "FDIV", "FMUL", "FSUB", "FSQRT"):
        related.append(f"{OUTDIR}/fpu/fpu-format.md")
    lines = frontmatter(title, tags, related)
    short = ""
    for key, vals in main["fields"]:
        if key == "Short":
            short = " ".join(field_text(vals))
    summary = f"**{md(mnemonic)}** ({md(name)})"
    lines += ["## Summary", "",
              f"{summary}: {md(short).rstrip('.')}." if short else f"{summary}.", ""]
    if any(p["gray_title"] for p in pages):
        lines += ["The original shows the title of one of these pages grayed "
                  "out; see the variants below.", ""]
    lines += ["## Details", ""]
    if mnemonic == "MOVEC":
        lines += render_fields(main)
        lines += render_movec(pages)
    else:
        h = "#### " if len(pages) > 1 else "### "
        for n, page in enumerate(pages):
            page["fp"] = unit == "fpu"
            if len(pages) > 1:
                head = " ".join(page["name"])
                linea = any("*LineA" in "".join(v) for _, v in page["fields"])
                variant = "LineA encoding" if linea else \
                    ("title grayed out in the original" if page["gray_title"] else "")
                lines += [f"### Variant {n + 1}: {md(head)}"
                          + (f" ({variant})" if variant else ""), ""]
            lines += render_fields(page)
            if page["cc"] is not None:
                lines += [h + ("FP condition codes" if unit == "fpu"
                               else "Condition codes"), ""]
                lines += render_cc(page["cc"])
            body_blocks, extra = page["body"], []
            if mnemonic == "PMULA":
                extra, body_blocks = pmula_tables(body_blocks)
            special = {"Frame18": storem3_frame} if mnemonic == "STOREM3" else None
            body, enc_head = render_body(body_blocks, special)
            if extra:
                body["encoding"] += [""] + extra
            for key, head in (("encoding", enc_head), ("example", "Example"),
                              ("notes", "Notes")):
                if body[key]:
                    lines += [h + head, ""] + body[key] + [""]
    lines += ["## Differences from AmigaOS / AROS / 68060", ""]
    lines += describe_diff(mnemonic) + [""]
    lines += ["## Do / Don't", ""]
    rules = RULES.get(mnemonic) or ["No rules beyond the details above."]
    lines += [f"- {rule_md(r)}" for r in rules]
    return f"{unit}/{slug}.md", tidy(lines)


def tidy(lines):
    out = []
    for ln in lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln.rstrip())
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


# ------------------------------------------------- front and back sections

# Page references in the original, and the file that has that page now.
PAGE_LINKS = {
    "5": "fpu-unit.md",
    "42": "ammx/ammx-format.md",
    "56": "ammx/pcmpccb.md",
    "83": "fpu/fmovem.md",
    "92": "instruction-fusing.md",
    "96": "instruction-timing.md",
}


def link_pages(line):
    """'page 56' becomes 'page 56 of the original, see [file](file)'."""
    def sub(m):
        f = PAGE_LINKS.get(m.group(2))
        if not f:
            return m.group(0)
        return f"{m.group(1)}{m.group(2)} of the original ([{f}]({f}))"
    return re.sub(r"\b(page )(\d+)", sub, line)


def looks_like_asm(lines):
    return all(re.match(r"^\s*([a-z][a-z0-9.]*(\s|$)|[a-z_]+$|<\w+>|;)", ln)
               for ln in lines)


def prose(blocks, code_styles=("P47",)):
    """Generic renderer for overview pages: paragraphs become bullets, code
    lines become code blocks."""
    out, buf = [], []

    def flush():
        if buf:
            lang = "asm" if looks_like_asm(buf) else "text"
            out.extend(["", f"```{lang}"] + buf + ["```", ""])
            buf.clear()
    for b in blocks:
        if isinstance(b, Table):
            flush()
            out.extend([""] + render_grid(b))
            continue
        s = re.sub(r"\[F\d+\]", "", b.text).strip()
        if not s:
            continue
        if b.style in code_styles or is_code_line(b.text) \
                or re.match(r"^\s{3,}(bcc|move|<)", b.text):
            buf.append(b.text.rstrip())
            continue
        flush()
        if b.style in ("P13",) and s.endswith(":"):
            out.extend(["", f"### {md(s.rstrip(':'))}", ""])
            continue
        line = link_pages(md(re.sub(r"^[–-]\s+", "", s)))
        if b.gray:
            line += " *(grayed out in the original)*"
        out.append(f"- {line}")
    flush()
    return out


def build_section(slug, title, tags, summary, body, diff, rules, related=()):
    lines = frontmatter(title, ["68080"] + tags,
                        [f"{OUTDIR}/index.md"] + list(related))
    lines += ["## Summary", "", summary, "", "## Details", ""] + body
    lines += ["", "## Differences from AmigaOS / AROS / 68060", ""] + diff
    lines += ["", "## Do / Don't", ""] + rules
    return f"{slug}.md", tidy(lines)


def render_front(front, parser):
    files = {}
    sec = dict(front)

    # Programming model: the register drawing is described in text.
    body = [
        "The original draws the user programming model as register boxes, "
        "with the caption \"Legacy model in gray.\" Widths follow the "
        "drawing's column labels (64, 32, 16 and 8 bit). This is the drawing "
        "in text:", "",
        "| Registers | Count | Drawn width | Gray (legacy) part in the drawing |",
        "|---|---|---|---|",
        "| D0–D7 data registers | 8 | 64 bits (columns 64, 32, 16, 8 bit) | lower 32 bits |",
        "| A0–A7 address registers (A7 = SP) | 8 | 64 bits (columns 64, 32 bit) | lower 32 bits |",
        "| PC | 1 | 64 bits | lower 32 bits |",
        "| CC | 1 | 64 bits | lower 16 bits |",
        "| FP0–FP7 floating point registers | 8 | 64 bits | all |",
        "| B0–B7 address registers | 8 | 64 bits | none (new) |",
        "| E0–E23 general purpose registers for integer and float | 24 | 64 bits (three columns: E0–E7, E8–E15, E16–E23) | none (new) |",
        "",
    ]
    files.update([build_section(
        "programming-model", "68080 user programming model",
        ["registers", "programming-model"],
        "The 68080 has 64-bit D0–D7, A0–A7, FP0–FP7, plus new B0–B7 address "
        "registers and E0–E23 general purpose registers.",
        body,
        ["- The 68000–68060 have only D0–D7, A0–A7 (32 bit) and FP0–FP7. "
         "B0–B7 and E0–E23 are new on the 68080."],
        ["- DO set the Apollo bit (SR bit 11) when your program uses E "
         "registers on a ROM-patched AmigaOS, so they survive task switches. "
         "ApolloOS always saves them. See [Apollo bit](apollo-bit.md)."],
        related=[f"{OUTDIR}/b-registers.md", f"{OUTDIR}/apollo-bit.md"])])

    files.update([build_section(
        "integer-unit", "68080 integer unit", ["integer", "bank", "superscalar"],
        "The 68080 integer unit is a 3-operand unit with access to D0–D7 and "
        "E0–E23 through the BANK prefix, B0–B7 address registers, superscalar "
        "execution and instruction fusing.",
        prose(sec["integer-unit"]),
        ["- 68000–68060 integer instructions are 2-operand. The 68080 adds a "
         "third operand (through BANK), E and B registers, fusing, and "
         "conditional execution of a single instruction after BCC.S."],
        ["- DON'T rely on banking for: pack, unpk, mul, div, abcd, sbcd, "
         "movex, add, sub, and, or, cmp, addx, subx, exg, bfextu, bfexts, "
         "bfffo, bfins. The manual says banking is not handled correctly yet "
         "for these."],
        related=[f"{OUTDIR}/integer/bank.md", f"{OUTDIR}/superscalar.md",
                 f"{OUTDIR}/instruction-fusing.md"])])

    files.update([build_section(
        "fpu-unit", "68080 floating point unit", ["fpu", "float"],
        "The 68080 FPU is a fully pipelined 3-operand unit with 64-bit floats "
        "and access to FP0–FP7 and E0–E23 through the BANK prefix.",
        prose(sec["fpu-unit"]),
        ["- The 6888x uses 80-bit floats and is not pipelined. The 68080 uses "
         "64-bit floats and is fully pipelined.",
         "- Packed BCD real is not implemented (as on the 68040 and 68060).",
         "- The microcoded transcendental instructions overwrite E23."],
        ["- DON'T keep data in E23 across a slow microcode float instruction "
         "(facos, fsin, fetox, ...): it gets overwritten.",
         "- DO schedule independent instructions while waiting for an FPU "
         "result (mostly 6 cycles or more).",
         "- DON'T use B address registers in FPU `<ea>`."],
        related=[f"{OUTDIR}/fpu/fpu-format.md", f"{OUTDIR}/instruction-timing.md"])])

    ammx_body = prose(sec["ammx-unit"])
    # Vector types: each list frame belongs to the heading before it.
    vt = sec["vector-types"]
    headings, lists = [], []
    for b in vt:
        if not isinstance(b, Para):
            continue
        h = re.sub(r"\[F\d+\]", "", b.text).strip()
        if h.startswith("Vector"):
            headings.append(h)
        for f in b.frames:
            lists.append([clean(x.text) for x in f.blocks
                          if isinstance(x, Para) and clean(x.text)])
    note = [clean(b.text) for b in vt if isinstance(b, Para) and b.text.startswith("Note")]
    ammx_body += ["", "### Vector handling by type", "",
                  "Which element type each instruction uses, source or "
                  "destination match. The original shows each list next to "
                  "its heading.", "",
                  "| Vector type | Instructions |", "|---|---|"]
    for h, lst in zip(headings, lists):
        ammx_body.append(f"| {md(h)} | {', '.join(lst)} |")
    ammx_body += [""] + [f"- {md(n)}" for n in note]
    files.update([build_section(
        "ammx-unit", "68080 AMMX unit", ["ammx", "simd", "vector"],
        "AMMX is the 68080's 64-bit SIMD unit: a line-F coprocessor with id 7, "
        "3-operand, using D0–D7, E0–E23, A0–A7 and B0–B7, without changing "
        "the condition codes.",
        ammx_body,
        ["- The 68000–68060 have no SIMD unit. AMMX instructions do not "
         "change the condition codes; PCMPcc writes its result to a register."],
        ["- DON'T branch on condition codes after AMMX instructions: use "
         "PCMPcc with BSEL, PAND/PANDN or STOREILM."],
        related=[f"{OUTDIR}/ammx/ammx-format.md"])])

    files.update([build_section(
        "b-registers", "68080 B address registers", ["registers", "b-registers"],
        "B0–B7 are extra address registers, restricted to long data and AMMX "
        "addressing.",
        prose(sec["b-registers"]),
        ["- B registers do not exist on the 68000–68060."],
        ["- DON'T move or exchange a B register with another B register.",
         "- DON'T use An or Bn as `<ea>` in `MOVEA.L <ea>,Bn` or `MOVE.L Bn,<ea>`."],
        related=[f"{OUTDIR}/integer/lea-bn.md", f"{OUTDIR}/integer/movea-bn.md"])])

    files.update([build_section(
        "apollo-bit", "68080 Apollo bit (SR bit 11)", ["sr", "linea", "multitasking"],
        "SR bit 11, the Apollo bit, keeps E registers intact across task "
        "switches on a ROM-patched AmigaOS and enables the LineA instructions. "
        "User mode may set and clear it.",
        prose(sec["apollo-bit"]),
        ["- On the 68000–68060, writing SR in user mode causes a privilege "
         "exception. On the 68080, `ori #$800,sr` and `andi #$f7ff,sr` are "
         "allowed in user mode."],
        ["- DO set the Apollo bit in your own program when you need it; it "
         "only affects the program that sets it.",
         "- DON'T expect the Apollo bit set by one program to affect another."],
        related=[f"{OUTDIR}/integer/move-sr.md"])])
    return files


def render_back(back, parser):
    files = {}
    sec = dict(back)

    # Superscalar: prose plus the Bruno yes/no frame.
    ss = sec["superscalar"]
    body = prose([b for b in ss if isinstance(b, Para)])
    for b in ss:
        for f in getattr(b, "frames", []):
            items = [clean(x.text) for x in f.blocks
                     if isinstance(x, Para) and clean(x.text)]
            if "No:" in items and "Yes:" in items:
                k = items.index("Yes:")
                no, yes = items[1:k], items[k + 1:]
                body += ["", "### Bruno (second pipe) examples", "",
                         "| Bruno accepts | Instructions |", "|---|---|",
                         f"| No | {md(', '.join(no))} |",
                         f"| Yes | {md(', '.join(yes))} |", ""]
    body = [ln for ln in body if ln != "- Bruno (second pipe) examples"]
    files.update([build_section(
        "superscalar", "68080 superscalar execution", ["superscalar", "pipes", "pairing"],
        "From about core 11350 the 68080 has three pipes (Anton, Bruno, Cesar). "
        "The cache learns pairing on the second pass of the code.",
        body,
        ["- The 68060 has two pipes. The 68080 has three, with different "
         "rules per pipe, and only pairs code after the first pass."],
        ["- DON'T expect multicycle instructions (mul, div, (f)movem) in "
         "Bruno or Cesar.",
         "- DO keep instruction groups within the 32-byte instruction-cache "
         "feed and one data-cache access (8 bytes) per cycle."],
        related=[f"{OUTDIR}/instruction-fusing.md", f"{OUTDIR}/pipeline.md"])])

    # Fusing: two tab tables.
    fu = [b for b in sec["instruction-fusing"] if isinstance(b, Para)]
    body, rows2, rows3 = [], [], []
    mode = None
    for b in fu:
        s = b.text.strip()
        if not s:
            continue
        cols = [clean(c) for c in re.split(r"\t+", b.text.strip()) if clean(c)]
        if re.match(r"^1\s+2\s+3", clean(s)):
            mode = 3
            continue
        if re.match(r"^1\s+2\s+comment", clean(s)):
            mode = 2
            continue
        if mode == 2 and len(cols) >= 2:
            rows2.append(cols + [""] * (3 - len(cols)))
        elif mode == 3 and len(cols) >= 3:
            rows3.append(cols + [""] * (4 - len(cols)))
        elif mode == 2 and len(cols) == 1:
            # A continuation line of the comment of the next row.
            rows2.append(["", "", cols[0]])
        else:
            body.append(f"- {md(s)}")
    body += ["", "### Two-instruction fuses", "",
             "| Instruction 1 | Instruction 2 | Comment |", "|---|---|---|"]
    body += [f"| {code(a) if a else ''} | {code(b) if b else ''} | {md(c)} |"
             for a, b, c in rows2]
    body += ["", "### Three-instruction fuses", "",
             "| Instruction 1 | Instruction 2 | Instruction 3 | Comment |",
             "|---|---|---|---|"]
    body += [f"| {code(a)} | {code(b)} | {code(c)} | {md(d)} |" for a, b, c, d in rows3]
    files.update([build_section(
        "instruction-fusing", "68080 instruction fusing", ["fusing", "optimizing"],
        "The 68080 fuses certain pairs (and one triple) of instructions into a "
        "single 64-bit or 3-operand instruction.",
        body,
        ["- The 68000–68060 do not fuse instructions."],
        ["- DO write fusable pairs back to back, for example two "
         "`move.l (an)+,(am)+` for a quad move."],
        related=[f"{OUTDIR}/superscalar.md"])])

    # Efficiency: the chart's data table.
    eff = sec["instruction-efficiency"]
    chart = None
    for b in eff:
        for f in getattr(b, "frames", []):
            if f.obj:
                chart = parser.chart_rows(f.obj)
    body = ["The original shows a line chart \"Most used instructions - "
            "benchmark test\". Its data:", ""]
    head = chart[0]
    body += ["| Instruction | " + " | ".join(head[1:]) + " |",
             "|---" * len(head) + "|"]
    for r in chart[1:]:
        body.append(f"| {code(r[0])} | " + " | ".join(r[1:]) + " |")
    body += [""] + [f"- {md(b.text)}" + (" *(grayed out in the original)*" if b.gray else "")
                    for b in eff if isinstance(b, Para)
                    and re.sub(r"\[F\d+\]", "", b.text).strip()
                    and not b.text.startswith("[F")]
    body = [ln for ln in body if "benchmark test." not in ln or ln.startswith("The original")]
    files.update([build_section(
        "instruction-efficiency", "68080 instruction efficiency benchmark",
        ["benchmark", "timing", "68030", "68040", "68060"],
        "Benchmark of common instructions on the 68030, 68040, 68060 and "
        "68080. 100 means one instruction per clock cycle.",
        body,
        ["- Most simple instructions reach about 296 on the 68080 (close to "
         "3 per cycle) against at most about 196 on the 68060."],
        ["- DON'T assume 68060 relative costs: MULU.L Dn,Da:Db scores 0.4 on "
         "the 68060 and 33 on the 68080; BFEXTU (a0),Dn scores 1 on the "
         "68060 and 100 on the 68080."],
        related=[f"{OUTDIR}/instruction-timing.md"])])

    files.update([build_section(
        "pipeline", "68080 pipeline stages", ["pipeline", "latency"],
        "The 68080 has a 7-stage pipeline. ALU results feeding the EA stage "
        "cost a 2-cycle bubble.",
        prose(sec["pipeline"]),
        ["- Which instructions run in the EA unit, and the ALU-to-EA bubble, "
         "are 68080 specific."],
        ["- DON'T use an ALU result as an address in the next instructions: "
         "ALU result to EA input costs a 2-cycle bubble.",
         "- DO compute addresses with EA-unit instructions (ADDQ/ADDA/SUBQ/"
         "SUBA/MOVE.L/LEA to An)."],
        related=[f"{OUTDIR}/instruction-timing.md"])])

    # Timing: prose plus the FPU pipeline table.
    tm = sec["instruction-timing"]
    body = prose([b for b in tm if isinstance(b, Para)])
    table = [b for b in tm if isinstance(b, Table)][0]
    body += ["", "### FPU pipeline example", "",
             "The original shows a timing chart. Columns 0–7 are FP0–FP7; a "
             "shaded box means the register is waiting for a result, a dark "
             "box means the result is finished in that cycle. In text:", "",
             "| Cycle | Instruction | Registers waiting | Finished |",
             "|---|---|---|---|"]
    for r in table.rows[1:]:
        cells = [c for c in r if not c.covered]
        if not cells or not cells[0].text:
            continue
        cyc, instr = cells[0].text, cells[1].text
        regs = cells[2:10]
        busy = [f"fp{k}" for k, c in enumerate(regs) if c.shaded == "#dddddd"]
        done = [f"fp{k}" for k, c in enumerate(regs) if c.shaded == "#b2b2b2"]
        body.append(f"| {cyc} | {code(instr) if instr else ''} | "
                    f"{', '.join(busy)} | {', '.join(done)} |")
    files.update([build_section(
        "instruction-timing", "68080 instruction timing", ["timing", "cycles", "fpu"],
        "Integer and AMMX instructions normally take 1 cycle. FPU add takes 6 "
        "cycles, multiply 5, divide 10 and square root 22, all fully pipelined.",
        body,
        ["- The 68080's cycle counts differ from the 68060's; do not reuse "
         "68060 timing tables."],
        ["- DO issue independent instructions while an FPU result is pending.",
         "- DON'T use JMP/JSR with a calculated <ea> in hot code when avoidable: "
         "it costs 4 cycles instead of 1."],
        related=[f"{OUTDIR}/pipeline.md", f"{OUTDIR}/instruction-efficiency.md"])])

    files.update([build_section(
        "optimizing", "68080 optimizing tips", ["optimizing", "cache", "ccc"],
        "Measure with the clock cycle counter (MOVEC CCC), align writes, "
        "prefer long and quad register updates, and do not unroll loops.",
        prose(sec["optimizing"]),
        ["- Unrolling loops, a common 68000–68060 optimization, is "
         "discouraged on the 68080: stay in the cache."],
        ["- DO measure with `movec ccc,Rn` before and after your code.",
         "- DO align writes: quad writes to quad-aligned addresses.",
         "- DON'T unroll loops."],
        related=[f"{OUTDIR}/integer/movec.md", f"{OUTDIR}/integer/touch.md"])])

    files.update([build_section(
        "trace", "68080 trace support", ["trace", "debugging", "monam"],
        "The 68080 supports SR bit 15 (trace on any instruction). A few "
        "instructions do not trace as expected.",
        prose(sec["trace"]),
        ["- SR bit 14 (trace on change of flow) is not mentioned as "
         "supported; the manual only names bit 15."],
        ["- DON'T expect a trace exception after the special cases listed "
         "above; execution continues to the next traceable instruction."],
        related=[f"{OUTDIR}/apollo-bit.md"])])

    files.update([build_section(
        "specs", "68080 specifications", ["specs", "cache", "memory"],
        "64-bit data bus, 32 KB instruction cache, 128 KB 3-ported data "
        "cache, 64-byte memory bursts, a 1024-entry branch target cache.",
        prose(sec["specs"]),
        ["- The cache sizes, the 64-bit data bus and the automatic prefetch "
         "are 68080 specific; don't reuse 68060 cache assumptions."],
        ["- DO rely on the automatic prefetch for sequential memory access; "
         "use TOUCH for non-sequential access."],
        related=[f"{OUTDIR}/optimizing.md"])])
    return files


# ---------------------------------------------------------------- index

def instruction_lists(blocks):
    """The manual's instruction lists per unit, with flags. The longest list
    per unit wins (the AMMX list appears three times). Each item is a list of
    (word, grayed out) pairs."""
    lists = {}
    unit = None
    for b in blocks:
        if not isinstance(b, Para):
            continue
        head = clean(b.text)
        if head in ("INTEGER INSTRUCTIONS", "AMMX INSTRUCTIONS",
                    "FLOATING POINT INSTRUCTIONS"):
            unit = head
        for f in b.frames:
            if not unit:
                continue
            items = []
            for x in f.blocks:
                if not isinstance(x, Para) or not clean(x.text):
                    continue
                words = []
                for text, gray in x.runs:
                    for w in re.split(r"[\t ]+", text):
                        if w and not w.isdigit():
                            words.append((w, gray))
                items.append(words)
            if len(items) > len(lists.get(unit, [])):
                lists[unit] = items
        if head.startswith("SUPERSCALAR"):
            break
    return lists


def render_index(entries, cover, lists):
    lines = frontmatter("Apollo 68080 Programmer's Reference Manual",
                        ["68080", "prm", "instructions", "index"],
                        ["core/cpu-68080/index.md"])
    tools, update = [], []
    for b in cover:
        if isinstance(b, Para) and b.style == "P19":
            cols = split_cols(b.text)
            tools.append(f"{cols[0]}: {cols[1]}")
            update += cols[2:]
    lines += [
        "## Summary", "",
        "The Apollo 68080 Programmer's Reference Manual (PRM), converted for "
        "AI agents. It covers only what the 68080 adds to the 68000 family: "
        "new instructions, new forms of existing instructions, the extra "
        "registers, the AMMX and FPU extensions, and performance. For "
        "everything else the Motorola manuals apply.", "",
        "## Details", "",
        "### About the original", "",
        "- Title: 68080 Programmer's Reference Manual, \"The New "
        "Instructions\". Concept by Tommo. Based on the original hardcopy "
        "PRM from Motorola, but simplified.",
        f"- Original: [`{SOURCE}`](../../../{SOURCE}). It is leading; these "
        "files are generated from it by `tools/intake/prm68080.py`.",
    ]
    lines.append(f"- Tools named in the original: {md('; '.join(tools))}.")
    if update:
        lines.append(f"- {md(' '.join(update))}")
    lines += [
        "", "### How to read an instruction file", "",
        "- **Field table**: Operation, Syntax, Short, Description, "
        "Constraints and condition codes, as on the original page.",
        "- **Condition codes**: as in the Motorola manuals: `*` = set "
        "according to the result, `–` = not affected, `0`/`1` = always "
        "cleared/set.",
        "- **Encoding**: one row per bit field. Word 1 is the opcode word; "
        "words 2 and up are extension words. Constant bits are in backticks.",
        "- **Example**: register and memory contents are written as bytes, "
        "most significant first, as the original draws them in boxes of one "
        "hex digit. `.` is a box left empty in the original. The prefix "
        "names the operand role (`ea`, `vea`, `a`, `b`, `d`) and register.",
        "- Every file ends with the differences from the 68000–68060 and "
        "DO/DON'T rules taken from the page.", "",
        "### Overview files", "",
        "| Topic | File |", "|---|---|",
        "| Registers (D, A, B, E, FP) | [programming-model.md](programming-model.md) |",
        "| Integer unit, BANK, 3 operands | [integer-unit.md](integer-unit.md) |",
        "| Floating point unit | [fpu-unit.md](fpu-unit.md) |",
        "| AMMX unit and vector types | [ammx-unit.md](ammx-unit.md) |",
        "| B registers | [b-registers.md](b-registers.md) |",
        "| Apollo bit (SR bit 11), LineA | [apollo-bit.md](apollo-bit.md) |",
        "| AMMX instruction format, <vea> modes | [ammx/ammx-format.md](ammx/ammx-format.md) |",
        "| Apollo FPU 3-operand format | [fpu/fpu-format.md](fpu/fpu-format.md) |",
        "| Superscalar pipes | [superscalar.md](superscalar.md) |",
        "| Instruction fusing | [instruction-fusing.md](instruction-fusing.md) |",
        "| Efficiency benchmark vs 68030/040/060 | [instruction-efficiency.md](instruction-efficiency.md) |",
        "| Pipeline stages | [pipeline.md](pipeline.md) |",
        "| Instruction timing | [instruction-timing.md](instruction-timing.md) |",
        "| Optimizing | [optimizing.md](optimizing.md) |",
        "| Trace | [trace.md](trace.md) |",
        "| Specifications | [specs.md](specs.md) |", "",
    ]
    by_unit = {"integer": [], "ammx": [], "fpu": []}
    for (unit, m, _), pages in entries:
        by_unit[unit].append((m, pages))
    titles = {"integer": "Integer instructions", "ammx": "AMMX instructions",
              "fpu": "Floating point instructions"}
    for unit in ("integer", "ammx", "fpu"):
        lines += [f"### {titles[unit]}", "",
                  "| Mnemonic | Name | Short | File |", "|---|---|---|---|"]
        for m, pages in by_unit[unit]:
            slug = entry_meta(m)[0]
            name = " ".join(pages[0]["name"])
            short = ""
            for key, vals in pages[0]["fields"]:
                if key == "Short":
                    short = " ".join(field_text(vals))
            lines.append(f"| {md(m)} | {md(name)} | {md(short)} | "
                         f"[{unit}/{slug}.md]({unit}/{slug}.md) |")
        lines.append("")
    lines += ["### Instruction lists of the original", "",
              "The original lists the instructions per unit with flags:", "",
              "- `la`: LineA instruction, valid only when the Apollo bit "
              "(SR bit 11) is set. The legend under the lists adds: \"Do "
              "not use, only available on cores 10280 to 10904\".",
              "- `p`: reading is not privileged on the 68080.", ""]
    for unit, items in lists.items():
        shown = []
        for words in items:
            shown.append(" ".join(f"{w} (grayed out)" if g else w
                                  for w, g in words))
        lines.append(f"- {unit.title()}: {md(', '.join(shown))}")
    lines += ["", "## Differences from AmigaOS / AROS / 68060", "",
              "- This manual documents only 68080 additions and differences. "
              "Each file states its difference from the 68000–68060.", "",
              "## Do / Don't", "",
              "- DO look up a mnemonic in the tables above before writing "
              "68080-specific code.",
              "- DON'T assume a 68060 instruction behaves the same on the "
              "68080 when it has a file here."]
    return "index.md", tidy(lines)


# ----------------------------------------------------------------- main

def build():
    parser = Parser(os.path.join(ROOT, SOURCE))
    front, raw_entries, back = segment(parser.blocks)
    # Group pages with the same mnemonic (MOVEC, MOVIW, TEX).
    entries, seen = [], {}
    for (unit, title, para), blocks in raw_entries:
        key = title.split()[0] if title.startswith("EXTUB") else title
        page = parse_page(para, blocks)
        if key in seen:
            seen[key][1].append(page)
        else:
            seen[key] = ((unit, key, para), [page])
            entries.append(seen[key])
    files = {}
    for (unit, m, _), pages in entries:
        path, text = render_entry(unit, m, pages)
        files[path] = text
    files.update(render_front(front, parser))
    files.update(render_back(back, parser))
    path, text = render_index(entries, dict(front)["cover"],
                              instruction_lists(parser.blocks))
    files[path] = text
    return files


def without_status(text):
    """The text without the status fields a maintainer may set."""
    return re.sub(r"^(status|last_verified):.*\n", "", text, flags=re.M)


def main():
    files = build()
    out = os.path.join(ROOT, OUTDIR)
    stale = []
    existing = set()
    for dirpath, _, names in os.walk(out):
        for n in names:
            existing.add(os.path.relpath(os.path.join(dirpath, n), out))
    for rel, text in files.items():
        p = os.path.join(out, rel)
        old = open(p, encoding="utf-8").read() if os.path.isfile(p) else None
        # A file keeps the status a maintainer gave it until its content
        # changes; then it is generated as draft again.
        if old is None or without_status(old) != without_status(text):
            stale.append(rel)
    extra = sorted(existing - set(files))
    if "--check" in sys.argv:
        if stale or extra:
            for s in stale + extra:
                print(f"out of date: {OUTDIR}/{s}", file=sys.stderr)
            sys.exit(1)
        print("OK")
        return
    for rel in stale:
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(files[rel])
    for rel in extra:
        print(f"not generated any more, remove by hand: {OUTDIR}/{rel}")
    print(f"Wrote {len(stale)} of {len(files)} file(s) in {OUTDIR}/")


if __name__ == "__main__":
    main()
