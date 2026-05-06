"""
Compile the methodology document.

Reads the master template `methodology/methodology.md` plus the 18 section
files under `methodology/sections/`, splices each section into the template,
and produces:

    methodology/build/methodology-v1.0.0.md     (composed source)
    methodology/build/methodology-v1.0.0.docx   (Word-format deliverable)
    methodology/build/methodology-v1.0.0.pdf    (Zenodo deposit artifact)

The body of each section file is inlined verbatim. Section headings come from
the master template only; section files start with the prose immediately, no
heading. The template strips the section header lines from each section file
to avoid double headings.

Usage:
    python3 bin/build_methodology.py [--no-pdf] [--no-docx]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METH = ROOT / "methodology"
SECTIONS = METH / "sections"
TEMPLATE = METH / "methodology.md"
BUILD = METH / "build"

VERSION = "1.0.0"


def strip_top_heading(text: str) -> str:
    """Drop the first '# ...' heading from a section file (master supplies it)."""
    lines = text.splitlines()
    out = []
    seen_first_h1 = False
    for line in lines:
        if not seen_first_h1 and re.match(r"^#\s+\S", line):
            seen_first_h1 = True
            continue
        out.append(line)
    return "\n".join(out).lstrip("\n")


def compose() -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    section_files = sorted(SECTIONS.glob("*.md"))
    if len(section_files) != 18:
        raise SystemExit(
            f"expected 18 section files, found {len(section_files)} in {SECTIONS}"
        )
    for path in section_files:
        m = re.match(r"^(\d{2})-", path.name)
        if not m:
            raise SystemExit(f"section file does not start with NN-: {path.name}")
        n = int(m.group(1))
        body = strip_top_heading(path.read_text(encoding="utf-8"))
        marker = f"::SECTION_{n:02d}::"
        if marker not in template:
            raise SystemExit(f"marker {marker} missing in template")
        template = template.replace(marker, body)
    return template


def have_engine(name: str) -> bool:
    return shutil.which(name) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--no-docx", action="store_true")
    args = parser.parse_args()

    BUILD.mkdir(parents=True, exist_ok=True)
    composed_md = compose()

    md_path = BUILD / f"methodology-v{VERSION}.md"
    md_path.write_text(composed_md, encoding="utf-8")
    print(f"wrote {md_path}  ({len(composed_md):,} chars)")

    if not have_engine("pandoc"):
        print("pandoc not found; skipping docx/pdf", file=sys.stderr)
        return 0

    if not args.no_docx:
        docx_path = BUILD / f"methodology-v{VERSION}.docx"
        cmd = [
            "pandoc",
            str(md_path),
            "-o",
            str(docx_path),
            "--from=markdown+yaml_metadata_block+raw_tex+raw_attribute",
            "--standalone",
            "--toc",
            "--toc-depth=2",
            "--metadata=lang:en-US",
        ]
        print(f"pandoc -> docx: {' '.join(cmd[:3])} ...")
        subprocess.run(cmd, check=True)
        print(f"wrote {docx_path}")

    if not args.no_pdf:
        pdf_path = BUILD / f"methodology-v{VERSION}.pdf"
        engine = "xelatex" if have_engine("xelatex") else "pdflatex"

        # Locate the IBM Plex Sans Thai font file. Bundled in the repo at
        # methodology/fonts/ for reproducibility; falls back to the parent
        # TLI design-system copy when this script runs inside the TLI
        # workspace (private dev environment).
        candidates = [
            METH / "fonts" / "IBMPlexSansThai-Regular.ttf",
            ROOT.parent / "04-phase-4-design/01-claude-design-handoff/project/fonts/IBMPlexSansThai-Regular.ttf",
        ]
        thai_font = next((c for c in candidates if c.exists()), None)

        # Pre-process the composed markdown: every Thai-script token gets
        # wrapped in a raw-LaTeX `{\thaifont ...}` group so xelatex switches
        # to the Thai font for those codepoints only. Also strip backtick
        # code-span markers around Thai-only content so the mono font (which
        # has no Thai glyphs) does not get reached.
        md_for_pdf = composed_md
        if thai_font:
            # First: drop backticks around code spans that are entirely Thai
            # script (or Thai with whitespace and ASCII punctuation), so the
            # following regex wraps the bare token in raw LaTeX rather than
            # producing raw LaTeX inside a code span. Constrain the inner
            # content to a single line to avoid matching across paragraphs
            # and accidentally pairing unrelated backticks.
            md_for_pdf = re.sub(
                r"`([^`\n]*[฀-๿][^`\n]*)`",
                lambda m: m.group(1) if re.fullmatch(r"[฀-๿\s\w_=\.\-]+", m.group(1)) else m.group(0),
                md_for_pdf,
            )
            # Then wrap any remaining Thai-script run in raw LaTeX. Use the
            # bare-command form (relying on the +raw_tex extension) rather
            # than the `code`{=latex} raw-attribute form, because pandoc 2.9
            # garbles paragraphs with multiple raw-attribute spans.
            md_for_pdf = re.sub(
                r"([฀-๿]+)",
                r"\\thaifont{\1}",
                md_for_pdf,
            )
        pdf_md_path = BUILD / f"methodology-v{VERSION}-pdf.md"
        pdf_md_path.write_text(md_for_pdf, encoding="utf-8")

        # Header: load the Thai font by absolute path, no ucharclasses, plus
        # a battery of long-table fixes so URLs, snake_case identifiers, and
        # long file paths break cleanly inside columns instead of overflowing.
        if thai_font:
            thai_part = (
                "\\usepackage{fontspec}\n"
                f"\\newfontfamily{{\\thaifont}}{{{thai_font.name}}}"
                f"[Path={thai_font.parent}/, Script=Thai]\n"
            )
        else:
            thai_part = "\\newcommand{\\thaifont}[1]{#1}\n"
        # xurl: allow URL break at any character.
        # seqsplit: allow long alphabetic runs to break.
        # emergencystretch + sloppy: reduce line overruns.
        # AtBeginEnvironment{longtable}: shrink font and tighten padding for
        # all longtable instances generated by pandoc.
        # Redefine \texttt inside longtable to allow breaks inside code spans.
        table_fixes = (
            "\\usepackage{xurl}\n"
            "\\usepackage{etoolbox}\n"
            "\\setlength{\\emergencystretch}{3em}\n"
            "% Inside longtable: small font, tight padding, sloppy line breaking,\n"
            "% and break-friendly underscore so snake_case identifiers wrap.\n"
            "\\AtBeginEnvironment{longtable}{%\n"
            "  \\scriptsize\n"
            "  \\setlength{\\tabcolsep}{3pt}\n"
            "  \\renewcommand{\\arraystretch}{1.10}\n"
            "  \\sloppy\n"
            "  \\hbadness=10000\n"
            "  \\hfuzz=20pt\n"
            "}\n"
            "% Break-friendly underscore globally — snake_case identifiers can wrap.\n"
            "\\renewcommand{\\_}{\\textunderscore\\hskip 0pt plus 0.01pt minus 0pt}\n"
        )
        thai_header = thai_part + table_fixes
        header_path = BUILD / "_thai_header.tex"
        header_path.write_text(thai_header, encoding="utf-8")

        cmd = [
            "pandoc",
            str(pdf_md_path),
            "-o",
            str(pdf_path),
            "--from=markdown+yaml_metadata_block+raw_tex+raw_attribute",
            "--toc",
            "--toc-depth=2",
            f"--pdf-engine={engine}",
            "-V",
            "linkcolor=MidnightBlue",
            "-V",
            "urlcolor=MidnightBlue",
            "-V",
            "geometry:margin=1in",
            "-V",
            "mainfont=DejaVu Serif",
            "-V",
            "sansfont=DejaVu Sans",
            "-V",
            "monofont=DejaVu Sans Mono",
            "--include-in-header",
            str(header_path),
        ]
        print(f"pandoc -> pdf via {engine} (thai font: {thai_font.name if thai_font else 'none'})")
        try:
            subprocess.run(cmd, check=True)
            print(f"wrote {pdf_path}")
        except subprocess.CalledProcessError as exc:
            print(
                f"pdf compile failed (exit {exc.returncode}); docx still ok",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
