"""Small synthetic QIIME 2 archives for failure and GUI lifecycle tests."""

from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

import pytest

ROOT = str(UUID(int=1))
PARENT = str(UUID(int=2))


def make_archive(path: Path, *, missing: bool = False, bad_yaml: bool = False) -> Path:
    """Write a two-step fixture into pytest's temporary directory only."""
    action = (
        f"execution:\n  uuid: {UUID(int=11)}\n"
        "action:\n  type: method\n  plugin: !ref 'environment:plugins:dada2'\n"
        "  action: denoise_paired\n  inputs:\n"
        f"    - demultiplexed_seqs: {PARENT}\n"
        "  parameters:\n    - trunc_len_f: 230\n    - enabled: true\n"
        "    - label: '<script>alert(1)</script>'\n"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr(
            f"{ROOT}/metadata.yaml", f"uuid: {ROOT}\ntype: Test[Data]\nformat: TestFmt\n"
        )
        archive.writestr(f"{ROOT}/VERSION", "QIIME 2\narchive: 7.1\nframework: 2026.4.0\n")
        archive.writestr(f"{ROOT}/provenance/action/action.yaml", "[broken" if bad_yaml else action)
        if not missing:
            archive.writestr(
                f"{ROOT}/provenance/artifacts/{PARENT}/action/action.yaml",
                f"execution:\n  uuid: {UUID(int=12)}\naction:\n  type: import\n",
            )
        archive.writestr(f"{ROOT}/data/DO_NOT_READ", "payload must never be read")
    return path


@pytest.fixture
def archive_path(tmp_path: Path) -> Path:
    """Provide a complete two-action archive."""
    return make_archive(tmp_path / "example.qza")
