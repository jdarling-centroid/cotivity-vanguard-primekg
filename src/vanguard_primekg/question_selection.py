"""Question subset selection shared by submission runners."""

from __future__ import annotations

import re


def parse_numbers(chunks: list[str]) -> set[int]:
    """Parse every supported repeated, comma-separated, and spaced form."""
    numbers: set[int] = set()
    for chunk in chunks:
        for token in re.split(r"[,\s]+", chunk.strip()):
            if token.isdigit():
                numbers.add(int(token))
            elif token:
                raise SystemExit(f"invalid question number: {token!r}")
    return numbers
