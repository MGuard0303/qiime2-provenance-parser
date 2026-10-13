"""Verify always-visible per-execution parameter evidence and GUI exports."""

import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from conftest import make_archive
from PySide6.QtWidgets import QApplication, QFileDialog
from pytestqt.qtbot import QtBot

from qiime2_provenance.app import MainWindow
from qiime2_provenance.parser import parse_archive
from qiime2_provenance.render import render_parameters


def test_parameter_types_order_and_shared_execution(archive_path: Path) -> None:
    """Preserve Unicode values, escape evidence and group a multi-output execution."""
    report = parse_archive(archive_path)
    parent = replace(report.records[0], parameters={"upstream_label": "<script>中文</script>"})
    main = replace(report.records[-1], parameters={"values": [True, None, "", 0, 2.5]})
    sibling = replace(main, artifact_uuid=str(UUID(int=99)), is_main=False)
    content = render_parameters(replace(report, records=(parent, sibling, main)))
    assert content.index("qiime tools import") < content.index("qiime dada2 denoise-paired")
    assert content.count("qiime dada2 denoise-paired") == 1
    assert "&lt;script&gt;中文&lt;/script&gt;" in content and "<script>" not in content
    assert '[true, null, &quot;&quot;, 0, 2.5]' in content
    assert parent.uuid in content and main.member in content
    assert 'font-size:11pt' in content and 'background' not in content
    assert 'No parameters recorded' in render_parameters(report)


def test_parameters_visible_by_default_without_reloading(
    qtbot: QtBot, archive_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Always expose every step, action details, raw evidence and copied report."""
    window = MainWindow()
    qtbot.addWidget(window)
    assert not hasattr(window, "verbose") and not hasattr(window, "set_verbose")
    assert window.tabs.currentWidget() is window.parameters_view
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))

    def unexpected_parse(path: Path) -> None:
        raise AssertionError(f"Changing evidence views must not reread {path}")

    monkeypatch.setattr("qiime2_provenance.app.parse_archive", unexpected_parse)
    text = window.parameters_view.toPlainText()
    assert "01 · qiime tools import" in text and "02 · qiime dada2 denoise-paired" in text
    assert "trunc_len_f" in text and "230" in text
    assert "trunc_len_f: 230" in window.full_report.toPlainText()
    window.action_list.setCurrentRow(0)
    assert "No parameters recorded" in window.action_detail.toPlainText()
    window.action_list.setCurrentRow(1)
    assert "230" in window.action_detail.toPlainText()
    assert "trunc_len_f" in window.raw_yaml.toPlainText()
    window.copy_report()
    assert "trunc_len_f: 230" in QApplication.clipboard().text()
    window.refresh_display()
    assert "trunc_len_f" in window.parameters_view.toPlainText()
    assert "230" in window.action_detail.toPlainText()
    window.clear_files()
    assert "trunc_len_f" not in window.parameters_view.toPlainText()


def test_parameters_follow_selected_file_and_clear_on_error(
    qtbot: QtBot, archive_path: Path, tmp_path: Path
) -> None:
    """Never leave the preceding file's parameters visible on a failed or different file."""
    second = make_archive(tmp_path / "second.qza")
    broken = tmp_path / "broken.qza"
    broken.write_bytes(b"not a ZIP")
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path, second, broken])
    first_report = parse_archive(archive_path)
    second_report = parse_archive(second)
    second_main = replace(second_report.records[-1], parameters={"second_file": 456})
    window.accept_report(first_report)
    window.accept_report(replace(second_report, records=(*second_report.records[:-1], second_main)))
    window.accept_error(str(broken.resolve()), "bad ZIP")
    assert "trunc_len_f" in window.parameters_view.toPlainText()
    window.file_list.setCurrentRow(1)
    assert "second_file" in window.parameters_view.toPlainText()
    assert "trunc_len_f" not in window.parameters_view.toPlainText()
    window.file_list.setCurrentRow(2)
    assert window.current_report is None
    assert "second_file" not in window.parameters_view.toPlainText()
    assert not window.export_button.isEnabled()


@pytest.mark.parametrize("suffix", ["txt", "json", "html"])
def test_all_exports_include_parameters_by_default(
    qtbot: QtBot, archive_path: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    """TXT, JSON and HTML always include parameter values from the loaded evidence."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))
    target = tmp_path / f"report.{suffix}"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(target), ""))
    window.export_report()
    content = target.read_text(encoding="utf-8")
    assert "trunc_len_f" in content and "230" in content
    if suffix == "json":
        assert json.loads(content)["records"][-1]["parameters"]["enabled"] is True
    if suffix == "html":
        assert "<script>" not in content
