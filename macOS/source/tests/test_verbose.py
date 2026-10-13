"""Verify per-execution parameter evidence and verbose GUI/export behavior."""

import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog
from pytestqt.qtbot import QtBot

from conftest import make_archive
from qiime2_provenance.app import MainWindow
from qiime2_provenance.parser import parse_archive
from qiime2_provenance.render import render_parameters


def test_parameter_types_order_and_shared_execution(archive_path: Path) -> None:
    """Preserve values, escape evidence and collapse a multi-output execution."""
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
    assert '未记录 parameters' in render_parameters(report)


def test_verbose_before_loading_and_cached_toggle(
    qtbot: QtBot, archive_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reveal all steps immediately, without parsing again; disable parameters everywhere."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.verbose.setChecked(True)
    assert window.tabs.currentWidget() is window.parameters_view
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))

    def unexpected_parse(path: Path) -> None:
        raise AssertionError(f"Verbose must not reread {path}")

    monkeypatch.setattr("qiime2_provenance.app.parse_archive", unexpected_parse)
    text = window.parameters_view.toPlainText()
    assert "01 · qiime tools import" in text and "02 · qiime dada2 denoise-paired" in text
    assert "trunc_len_f" in text and "230" in text
    window.action_list.setCurrentRow(0)
    assert "未记录 parameters" in window.action_detail.toPlainText()
    window.action_list.setCurrentRow(1)
    assert "230" in window.action_detail.toPlainText()
    window.copy_report()
    assert "trunc_len_f: 230" in QApplication.clipboard().text()
    window.verbose.setChecked(False)
    assert "trunc_len_f" not in window.parameters_view.toPlainText()
    assert "trunc_len_f" not in window.full_report.toPlainText()
    assert "trunc_len_f" not in window.action_detail.toPlainText()
    assert "trunc_len_f" in window.raw_yaml.toPlainText()
    window.copy_report()
    assert "trunc_len_f" not in QApplication.clipboard().text()
    window.verbose.setChecked(True)
    assert "trunc_len_f" in window.parameters_view.toPlainText()
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
    window.verbose.setChecked(True)
    assert "trunc_len_f" in window.parameters_view.toPlainText()
    window.file_list.setCurrentRow(1)
    assert "second_file" in window.parameters_view.toPlainText()
    assert "trunc_len_f" not in window.parameters_view.toPlainText()
    window.file_list.setCurrentRow(2)
    assert window.current_report is None
    assert "second_file" not in window.parameters_view.toPlainText()
    assert not window.export_button.isEnabled()


@pytest.mark.parametrize("suffix", ["txt", "json", "html"])
def test_verbose_exports_both_modes(
    qtbot: QtBot, archive_path: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, suffix: str,
) -> None:
    """TXT, JSON and HTML follow the same checkbox state as the parameter view."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))
    target = tmp_path / f"report.{suffix}"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(target), ""))
    for enabled in [True, False]:
        window.verbose.setChecked(enabled)
        window.export_report()
        content = target.read_text(encoding="utf-8")
        assert ("trunc_len_f" in content) is enabled
        if suffix == "json" and enabled:
            assert json.loads(content)["records"][-1]["parameters"]["enabled"] is True
        if suffix == "html":
            assert "<script>" not in content
