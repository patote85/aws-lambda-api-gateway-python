"""Mechanical ban: CDK sources must not contain CORS origin wildcard *."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CDK_DIR = ROOT / "cdk"

# Literal "*" / '*' as a Python string (CORS AllowOrigins wildcard).
_STAR_STRING = re.compile(r"""(['"])\*\1""")


def test_cdk_no_cors_allow_origins_star():
    """Fail if cdk/ contains AllowOrigins / origin list wildcard '*'."""
    offenders: list[str] = []
    for path in sorted(CDK_DIR.rglob("*.py")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Skip pure comments
            code = line.split("#", 1)[0]
            if _STAR_STRING.search(code):
                offenders.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()}")

    assert not offenders, (
        "CDK must not use CORS AllowOrigins '*'. Offenders:\n"
        + "\n".join(offenders)
    )
