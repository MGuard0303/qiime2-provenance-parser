"""Compare all real archives with the original parser, without modifying inputs."""

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Protocol, cast
from zipfile import ZipFile

from qiime2_provenance.parser import get_action_files, parse_archive, parse_yaml


class LegacyParser(Protocol):
    """Typed boundary for dynamically importing the user's original module."""

    def get_action_files(self, zipfile: ZipFile) -> object: ...
    def parse_yaml(self, action_files: object, zipfile: ZipFile, verbose: bool) -> object: ...


def main() -> None:
    """Validate every QZA/QZV and emit an auditable JSON comparison manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--legacy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root.resolve(strict=True)
    legacy_path: Path = args.legacy.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("legacy_parser", legacy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the legacy parser.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    legacy = cast(LegacyParser, module)
    results: list[dict[str, object]] = []
    paths = sorted(
        path for path in root.rglob("*")
        if path.suffix.lower() in {".qza", ".qzv"}
        and not path.name.startswith("._") and path.is_file()
    )
    for path in paths:
        before = path.stat()
        started = time.perf_counter()
        report = parse_archive(path)
        with ZipFile(path) as archive:
            files = get_action_files(archive)
            if isinstance(files, ValueError):
                raise files
            current = parse_yaml(files, archive, True)
            previous = legacy.parse_yaml(legacy.get_action_files(archive), archive, True)
        if not isinstance(current, list) or not isinstance(previous, list):
            raise AssertionError(f"Parser failed: {path}: {current!r}, {previous!r}")
        # Sort serializations to compare all records regardless of ZIP member order.
        original_set = sorted(json.dumps(r, sort_keys=True, default=str) for r in previous)
        current_set = sorted(json.dumps(r, sort_keys=True, default=str) for r in current)
        if original_set != current_set:
            raise AssertionError(f"Legacy compatibility failed: {path}")
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        results.append(
            {
                "file": str(path.relative_to(root)),
                "bytes": before.st_size,
                "all_action_records": len(current),
                "reachable_artifacts": len(report.records),
                "unique_executions": len(report.executions),
                "missing_inputs": list(report.missing_inputs),
                "legacy_equal": True,
                "elapsed_seconds": round(time.perf_counter() - started, 4),
                "source_size_and_mtime_unchanged": True,
            }
        )
    args.output.write_text(
        json.dumps(
            {"root": str(root), "files": results, "count": len(results)},
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"Validated {len(results)} archives; all legacy records match; source stats unchanged.")


if __name__ == "__main__":
    main()
