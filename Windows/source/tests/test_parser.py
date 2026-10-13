"""Exercise evidence correctness and malformed/untrusted input boundaries."""

import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

import pytest
import yaml
from conftest import PARENT, ROOT, make_archive

from qiime2_provenance.parser import (
    MAX_MEMBER_BYTES,
    ProvenanceError,
    QIIME2Loader,
    get_action_files,
    json_value,
    order_records,
    parse_archive,
    parse_yaml,
)
from qiime2_provenance.render import render_action, render_html, render_text


def test_graph_parameters_and_legacy_api(archive_path: Path) -> None:
    report = parse_archive(archive_path)
    assert [r.action for r in report.records] == ["import", "denoise_paired"]
    assert report.records[-1].parameters["trunc_len_f"] == 230
    assert report.records[-1].parameters["enabled"] is True
    assert not report.missing_inputs
    with ZipFile(archive_path) as archive:
        members = get_action_files(archive)
        assert not isinstance(members, ValueError)
        records = parse_yaml(members, archive, True)
        assert isinstance(records, list)
        assert {r["artifact_uuid"] for r in records} == {ROOT, PARENT}


def test_missing_inputs_remain_explicit(tmp_path: Path) -> None:
    report = parse_archive(make_archive(tmp_path / "missing.qza", missing=True))
    assert report.missing_inputs == (PARENT,)
    assert "WARNING" in render_text(report)


def test_payload_is_never_opened(archive_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = ZipFile.open

    def guard(self, name, *args, **kwargs):
        member = name if isinstance(name, str) else name.filename
        assert "/data/" not in member
        return original(self, name, *args, **kwargs)

    monkeypatch.setattr(ZipFile, "open", guard)
    assert parse_archive(archive_path).artifact_uuid == ROOT


def test_cycle_rejected(archive_path: Path) -> None:
    records = list(parse_archive(archive_path).records)
    records[0] = replace(records[0], inputs=(ROOT,))
    with pytest.raises(ProvenanceError, match="cycle"):
        order_records(records)


def test_multioutput_execution_main_marker(archive_path: Path) -> None:
    report = parse_archive(archive_path)
    main = report.records[-1]
    sibling = replace(main, artifact_uuid=str(UUID(int=7)), is_main=False)
    grouped = replace(report, records=(report.records[0], sibling, main))
    assert len(grouped.executions) == 2
    assert grouped.executions[-1].is_main


@pytest.mark.parametrize("value", ["[broken", "!!python/object/apply:os.system ['echo UNSAFE']"])
def test_unsafe_or_invalid_yaml_is_rejected(value: str) -> None:
    with pytest.raises(yaml.YAMLError):
        yaml.load(value, Loader=QIIME2Loader)


def test_duplicate_mapping_and_recursive_alias() -> None:
    with pytest.raises(ProvenanceError, match="Duplicate"):
        yaml.load("action: 1\naction: 2", Loader=QIIME2Loader)
    with pytest.raises(ProvenanceError, match="nesting"):
        json_value(yaml.load("&a [*a]", Loader=QIIME2Loader))


def test_corrupt_archives_fail_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.qza"
    path.write_bytes(b"not a ZIP")
    with pytest.raises(ProvenanceError):
        parse_archive(path)
    with pytest.raises(ProvenanceError):
        parse_archive(make_archive(path, bad_yaml=True))


def test_duplicate_zip_members_rejected(archive_path: Path) -> None:
    with ZipFile(archive_path, "a") as archive, pytest.warns(UserWarning):
        archive.writestr(f"{ROOT}/metadata.yaml", "duplicate")
    with pytest.raises(ProvenanceError, match="Duplicate ZIP"):
        parse_archive(archive_path)


def test_member_limit(tmp_path: Path) -> None:
    path = make_archive(tmp_path / "oversized.qza", missing=True)
    with ZipFile(path, "a") as archive:
        archive.writestr(
            f"{ROOT}/provenance/artifacts/{PARENT}/action/action.yaml", " " * (MAX_MEMBER_BYTES + 1)
        )
    with pytest.raises(ProvenanceError, match="8 MiB"):
        parse_archive(path)


def test_export_escaping_and_verbose(archive_path: Path) -> None:
    report = parse_archive(archive_path)
    assert "trunc_len_f" not in render_text(report, False)
    assert "trunc_len_f" in render_text(report, True)
    assert "<script>" not in render_html(report, True)
    assert "&lt;script&gt;" in render_action(report.records[-1], report, True)
    assert "parameters" not in json.loads(report.to_json(False))["records"][-1]
    assert json.loads(report.to_json(True))["records"][-1]["parameters"]["trunc_len_f"] == 230


def test_nested_inputs_and_custom_tags() -> None:
    values = yaml.load("a: !ref abc\nb: !set [x, y]\nc: !metadata {one: 1}", Loader=QIIME2Loader)
    assert json_value(values) == {"a": "abc", "b": ["x", "y"], "c": {"one": 1}}
