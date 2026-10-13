"""Command-line companion for scripts and reproducible inspections."""

import argparse
import sys
from pathlib import Path

from .parser import ProvenanceError, parse_archive
from .render import render_text


def main() -> int:
    """Parse one archive; return zero on success and one for an unreadable input."""
    parser = argparse.ArgumentParser(description="Read QIIME 2 provenance without QIIME 2.")
    parser.add_argument("--file-path", required=True, type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    try:
        print(render_text(parse_archive(args.file_path), args.verbose))
        return 0
    except (OSError, ProvenanceError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
