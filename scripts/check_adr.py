#!/usr/bin/env python3
"""Fail when an ADR is missing the **Status:** line or a required section.

Required sections are the ATX headings in ``docs/adr/TEMPLATE.md`` that contain
the marker ``(obrigatória)``. The template is the only source of that list.

An ADR heading satisfies a required section when the titles match after:

- removing every ``(obrigatória)`` marker (case-insensitive; spaces just
  inside the parentheses are ignored);
- collapsing whitespace to a single space;
- Unicode case-folding.

The heading level (``#`` through ``######``) is ignored. The ADR may keep the
marker or drop it. Only ``ADR-*.md`` files are checked.

The status line is a line that, after optional leading whitespace and an
optional markdown bullet (``-``, ``*``, or ``+``), starts with the literal
``**Status:**`` from the template (colon inside the bold).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Accepted before TEMPLATE.md existed (ADR-001 on CAB 2026-09-20, ADR-002 through
# ADR-004 on CAB 2026-10-18). They keep their original outline; do not edit them
# to satisfy this check. ADR-005 and later are checked.
EXEMPT_ADR_IDS = frozenset({"ADR-001", "ADR-002", "ADR-003", "ADR-004"})

REPO_ROOT = Path(__file__).resolve().parents[1]

_MARKER_RE = re.compile(r"\(\s*obrigatória\s*\)", re.IGNORECASE)
_HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_STATUS_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?\*\*Status:\*\*", re.MULTILINE)
_ADR_ID_RE = re.compile(r"^(ADR-\d{3})(?=-|\.md$)", re.IGNORECASE)


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _display_heading(text: str) -> str:
    without_marker = _MARKER_RE.sub(" ", text)
    return re.sub(r"\s+", " ", without_marker).strip()


def _heading_key(text: str) -> str:
    return _display_heading(text).casefold()


def required_sections(template_text: str) -> list[str]:
    """Return required heading labels, in template order, without the marker."""
    seen: set[str] = set()
    labels: list[str] = []
    for match in _HEADING_RE.finditer(_normalize_newlines(template_text)):
        raw = match.group(1)
        if _MARKER_RE.search(raw) is None:
            continue
        label = _display_heading(raw)
        key = label.casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        labels.append(label)
    return labels


def find_problems(adr_text: str, required: list[str]) -> list[str]:
    """Return human-readable gaps: status line and any required section."""
    visible = _normalize_newlines(adr_text)
    missing: list[str] = []
    if _STATUS_RE.search(visible) is None:
        missing.append("**Status:** line")
    present = {_heading_key(match.group(1)) for match in _HEADING_RE.finditer(visible)}
    for label in required:
        if _heading_key(label) not in present:
            missing.append(f'section "{label}"')
    return missing


def adr_id(filename: str) -> str | None:
    match = _ADR_ID_RE.match(filename)
    if match is None:
        return None
    return match.group(1).upper()


def is_exempt(filename: str) -> bool:
    ident = adr_id(filename)
    return ident in EXEMPT_ADR_IDS


def classify_adrs(adr_dir: Path) -> tuple[list[Path], list[Path]]:
    """Split ``ADR-*.md`` into (checked, exempt). Other files are ignored."""
    checked: list[Path] = []
    exempt: list[Path] = []
    for path in sorted(adr_dir.glob("ADR-*.md")):
        if is_exempt(path.name):
            exempt.append(path)
        else:
            checked.append(path)
    return checked, exempt


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run(root: Path) -> int:
    root = root.resolve()
    adr_dir = root / "docs" / "adr"
    template_path = adr_dir / "TEMPLATE.md"
    template_display = _display_path(template_path, root)
    if not template_path.is_file():
        print(f"{template_display}: file not found", file=sys.stderr)
        return 1

    template_text = template_path.read_text(encoding="utf-8-sig")
    required = required_sections(template_text)
    if not required:
        print(
            f'{template_display}: no heading contains "(obrigatória)"',
            file=sys.stderr,
        )
        return 1

    checked, exempt = classify_adrs(adr_dir)
    failure_count = 0
    for path in checked:
        rel = _display_path(path, root)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            print(f"{rel}: file is not valid UTF-8", file=sys.stderr)
            failure_count += 1
            continue
        for item in find_problems(text, required):
            failure_count += 1
            print(f"{rel}: missing {item}", file=sys.stderr)

    if failure_count:
        print(f"ADR check failed: {failure_count} problem(s).", file=sys.stderr)
        return 1

    exempt_ids = [adr_id(path.name) or path.name for path in exempt]
    exempt_note = f" ({', '.join(exempt_ids)})" if exempt_ids else ""
    print(
        f"ADR check passed: {len(checked)} checked, {len(exempt)} exempt{exempt_note}."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check ADR files against docs/adr/TEMPLATE.md."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root that contains docs/adr/ (default: this repo).",
    )
    args = parser.parse_args(argv)
    return run(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
