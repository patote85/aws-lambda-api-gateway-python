"""ADR template check: status line, required sections, exemptions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_adr

MIN_TEMPLATE = """\
# ADR-NNN — Título

- **Status:** Proposed

## Contexto (obrigatória)

## Decisão (obrigatória)

## Notas
"""

REAL_TEMPLATE = ROOT / "docs" / "adr" / "TEMPLATE.md"


def _repo(
    tmp_path: Path,
    files: dict[str, str] | None = None,
    *,
    template: str | None = None,
) -> Path:
    adr = tmp_path / "docs" / "adr"
    adr.mkdir(parents=True)
    text = MIN_TEMPLATE if template is None else template
    (adr / "TEMPLATE.md").write_text(text, encoding="utf-8")
    for name, body in (files or {}).items():
        (adr / name).write_text(body, encoding="utf-8")
    return tmp_path


def _complete(required: list[str], *, status: bool = True, drop: set[str] | None = None) -> str:
    skipped = drop or set()
    parts = ["# ADR-005 — Exemplo", ""]
    if status:
        parts.extend(["- **Status:** Proposed", ""])
    for label in required:
        if label in skipped:
            continue
        parts.extend([f"## {label}", "", "texto", ""])
    return "\n".join(parts)


def test_required_sections_come_from_template_marker():
    labels = check_adr.required_sections(
        "## Alpha (obrigatória)\n## Beta\n## Gamma ( OBRIGATÓRIA )\n"
    )
    assert labels == ["Alpha", "Gamma"]


def test_real_template_marks_only_obrigatoria_sections():
    labels = check_adr.required_sections(REAL_TEMPLATE.read_text(encoding="utf-8"))
    assert labels == [
        "Contexto",
        "Decisão",
        "Efeitos colaterais",
        "Consequências / trade-offs",
        "Alternativas descartadas",
    ]


def test_missing_status_fails(tmp_path, capsys):
    required = check_adr.required_sections(MIN_TEMPLATE)
    root = _repo(tmp_path, {"ADR-005-sem-status.md": _complete(required, status=False)})
    assert check_adr.main(["--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "docs/adr/ADR-005-sem-status.md: missing **Status:** line" in err
    assert 'section "' not in err


def test_missing_required_section_fails(tmp_path, capsys):
    required = check_adr.required_sections(MIN_TEMPLATE)
    body = _complete(required, drop={"Decisão"})
    root = _repo(tmp_path, {"ADR-005-sem-decisao.md": body})
    assert check_adr.main(["--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert 'docs/adr/ADR-005-sem-decisao.md: missing section "Decisão"' in err
    assert "**Status:**" not in err


def test_complete_adr_passes(tmp_path, capsys):
    template = REAL_TEMPLATE.read_text(encoding="utf-8")
    required = check_adr.required_sections(template)
    root = _repo(
        tmp_path,
        {"ADR-005-completa.md": _complete(required)},
        template=template,
    )
    assert check_adr.main(["--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "1 checked" in out
    assert "ADR check passed" in out


def test_heading_match_is_case_and_whitespace_tolerant(tmp_path, capsys):
    body = """\
# ADR-006 — Ok

- **Status:** Accepted

##   CONTEXTO

## decisão (obrigatória)
"""
    root = _repo(tmp_path, {"ADR-006-ok.md": body})
    assert check_adr.main(["--root", str(root)]) == 0
    assert capsys.readouterr().err == ""


def test_exempt_adrs_are_skipped(tmp_path, capsys):
    broken = "# ADR-001 — Antiga\n\nSem status e sem seções.\n"
    root = _repo(
        tmp_path,
        {
            "ADR-001-unificar-exclusao-pix.md": broken,
            "ADR-004-bend-jev-gate-nao-runtime.md": broken,
        },
    )
    assert check_adr.main(["--root", str(root)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "ADR-001" in captured.out
    assert "ADR-004" in captured.out
    assert "0 checked" in captured.out


def test_exempt_allowlist_does_not_hide_other_adrs(tmp_path, capsys):
    required = check_adr.required_sections(MIN_TEMPLATE)
    root = _repo(
        tmp_path,
        {
            "ADR-002-auth.md": "# ADR-002\n\nAntiga.\n",
            "ADR-009-nova.md": _complete(required, status=False),
        },
    )
    assert check_adr.main(["--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "ADR-009-nova.md: missing **Status:** line" in err
    assert "ADR-002" not in err


def test_allowlist_boundaries():
    assert check_adr.is_exempt("ADR-001-unificar-exclusao-pix.md")
    assert check_adr.is_exempt("ADR-003-httpapi-lambda-cdk-python.md")
    assert check_adr.is_exempt("adr-004-bend-jev-gate-nao-runtime.md")
    assert not check_adr.is_exempt("ADR-005-nova.md")
    assert not check_adr.is_exempt("ADR-0010-nova.md")
    assert not check_adr.is_exempt("TEMPLATE.md")
    assert not check_adr.is_exempt("README.md")


def test_template_md_is_not_checked(tmp_path, capsys):
    template = MIN_TEMPLATE.replace("- **Status:** Proposed\n", "")
    required = check_adr.required_sections(template)
    root = _repo(
        tmp_path,
        {"ADR-008-ok.md": _complete(required), "README.md": "# notas\n"},
        template=template,
    )
    checked, exempt = check_adr.classify_adrs(root / "docs" / "adr")
    assert [path.name for path in checked] == ["ADR-008-ok.md"]
    assert exempt == []
    assert check_adr.main(["--root", str(root)]) == 0
    captured = capsys.readouterr()
    assert "TEMPLATE.md" not in captured.err
    assert "TEMPLATE.md" not in captured.out


def test_template_without_required_headings_fails(tmp_path, capsys):
    root = _repo(tmp_path, template="# Title\n\n- **Status:** Proposed\n")
    assert check_adr.main(["--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert 'docs/adr/TEMPLATE.md: no heading contains "(obrigatória)"' in err


def test_real_repo_passes(capsys):
    assert check_adr.main([]) == 0
    out = capsys.readouterr().out
    assert "ADR check passed" in out
    for ident in ("ADR-001", "ADR-002", "ADR-003", "ADR-004"):
        assert ident in out
