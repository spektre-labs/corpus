#!/usr/bin/env python3
"""
corpus_integrity — declared = realized for the Spektre Corpus (stdlib only).

The README is the DECLARATION (a table of |Title|DOI| rows). papers/ is the
REALIZATION (the PDFs). This checker keeps them honest.

HARD errors (fail CI — machine-checkable + objectively wrong):
  · a DOI that is not a well-formed Zenodo DOI (10.5281/zenodo.<digits>)
  · a row whose visible DOI text != its doi.org link target

WARNINGS (surfaced, non-fatal — need a human/Zenodo to resolve, never guessed):
  · the same DOI on two different paper rows (one is mis-attributed)
  · declared paper count != PDF count in papers/  (under/over-declared)
  · stray PDFs at the repo root (should they live in papers/?)

σ-honest: it reports the REAL state. It never invents a DOI or a file.

  corpus_integrity.py          # check the repo (cwd = repo root); exit 1 on hard errors
"""
from __future__ import annotations
import re, sys
from pathlib import Path
from collections import Counter

DOI_RE = re.compile(r"10\.5281/zenodo\.\d+")
LINK_RE = re.compile(r"doi\.org/(10\.5281/zenodo\.\d+)")


def check(root: Path) -> int:
    readme = (root / "README.md").read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    # parse declaration: table rows that carry a DOI
    rows = []  # (title, doi)
    for line in readme.splitlines():
        if line.lstrip().startswith("|") and DOI_RE.search(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            title = cells[0] if cells else "?"
            doi = DOI_RE.search(line).group()
            link = LINK_RE.search(line)
            # HARD: visible DOI must equal the link target
            if link and link.group(1) != doi:
                errors.append(f"DOI text/link mismatch: '{title}' — {doi} vs {link.group(1)}")
            rows.append((title, doi))

    # HARD: every DOI well-formed (regex already guarantees shape; guard empties)
    for title, doi in rows:
        if not DOI_RE.fullmatch(doi):
            errors.append(f"malformed DOI: '{title}' — {doi}")

    # WARN: duplicate DOI across distinct rows
    counts = Counter(d for _, d in rows)
    for doi, n in counts.items():
        if n > 1:
            titles = [t for t, d in rows if d == doi]
            warnings.append(f"duplicate DOI {doi} on {n} rows: {titles} — one is mis-attributed")

    # WARN: declared vs realized count
    pdfs = sorted(p.name for p in (root / "papers").glob("*.pdf"))
    declared = len(set(d for _, d in rows))
    if declared != len(pdfs):
        warnings.append(f"declared papers ({declared} distinct DOIs) != papers/ files ({len(pdfs)})")

    # WARN: stray root PDFs
    stray = [p.name for p in root.glob("*.pdf")]
    if stray:
        warnings.append(f"stray PDF(s) at repo root (move to papers/?): {stray}")

    # report
    print(f"◆ CORPUS INTEGRITY — {len(rows)} declared rows · {len(pdfs)} PDFs in papers/")
    for w in warnings:
        print(f"  ⚠ WARN  {w}")
    for e in errors:
        print(f"  ✗ ERROR {e}")
    if errors:
        print(f"  σ: HALT — {len(errors)} structural error(s)")
        return 1
    print(f"  σ: PASS — structure coherent ({len(warnings)} warning(s) for maintainer review)")
    return 0


if __name__ == "__main__":
    raise SystemExit(check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
