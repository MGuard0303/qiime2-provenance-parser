"""Test English presentation, parameter visibility and real Qt worker lifecycle."""

import re
from pathlib import Path
from threading import Event

from conftest import make_archive
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QFileDialog,
    QLabel,
    QLineEdit,
)

from qiime2_provenance.app import MainWindow
from qiime2_provenance.parser import parse_archive
from qiime2_provenance.style import configure_application


def test_batch_failure_selection_and_parameters(qtbot, archive_path: Path, tmp_path: Path) -> None:
    """Expose all parameters immediately and isolate failed files in a batch."""
    broken = tmp_path / "broken.qza"
    broken.write_text("bad ZIP")
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path, broken, archive_path])
    assert window.file_list.count() == 2
    qtbot.mouseClick(window.parse_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert len(window.reports) == 1 and len(window.errors) == 1
    assert window.action_list.count() == 2
    assert "trunc_len_f" in window.full_report.toPlainText()
    assert "230" in window.action_detail.toPlainText()
    assert "trunc_len_f" in window.parameters_view.toPlainText()
    window.follow_artifact(QUrl("artifact:" + window.current_report.records[0].artifact_uuid))
    assert window.action_list.currentRow() == 0
    window.file_list.setCurrentRow(1)
    assert window.current_report is None
    assert not window.export_button.isEnabled()
    assert "zip" in window.action_detail.toPlainText().lower()
    assert "trunc_len_f" not in window.parameters_view.toPlainText()
    window.remove_selected()
    assert window.current_report is not None
    window.clear_files()
    assert not window.parse_button.isEnabled()


def test_native_drop_events(qtbot, archive_path: Path) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(archive_path))])
    enter = QDragEnterEvent(
        QPoint(60, 500),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, enter)
    assert enter.isAccepted()
    drop = QDropEvent(
        QPointF(60, 500),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, drop)
    assert window.paths == [archive_path]


def test_export_and_search(qtbot, archive_path: Path, tmp_path: Path, monkeypatch) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))
    target = tmp_path / "report.json"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *a, **kw: (str(target), "JSON data (*.json)")
    )
    window.export_report()
    assert '\"trunc_len_f\": 230' in target.read_text(encoding="utf-8")
    window.search.setText("trunc_len_f")
    window.find_text()
    assert window.full_report.textCursor().selectedText() == "trunc_len_f"


def test_english_controls_and_grayscale_presentation(qtbot, qapp, archive_path: Path) -> None:
    """Check application-owned English text and readable neutral presentation.

    Only this English synthetic archive is inspected for UI language. Unicode
    paths and evidence values remain supported and are tested independently.
    """
    configure_application(qapp)
    window = MainWindow()
    qtbot.addWidget(window)
    window.add_paths([archive_path])
    window.accept_report(parse_archive(archive_path))
    texts = [window.windowTitle()]
    for widget in window.findChildren(QLabel):
        texts.append(widget.text())
    for widget in window.findChildren(QAbstractButton):
        texts.append(widget.text())
    for widget in window.findChildren(QLineEdit):
        texts.append(widget.placeholderText())
    for widget in window.findChildren(QAbstractButton):
        texts.extend([widget.toolTip(), widget.accessibleName()])
    texts.extend(window.tabs.tabText(index) for index in range(window.tabs.count()))
    texts.extend([
        window.action_detail.toPlainText(),
        window.parameters_view.toPlainText(),
        window.full_report.toPlainText(),
    ])
    assert not any(re.search(r"[\u3400-\u9fff]", text) for text in texts)
    assert not window.findChildren(QCheckBox)
    assert not hasattr(window, "verbose") and not hasattr(window, "set_verbose")
    assert window.tabs.currentWidget() is window.parameters_view
    assert qapp.font().pointSize() == 11
    assert qapp.font().family()
    for role in (
        QPalette.ColorRole.Window,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Base,
        QPalette.ColorRole.AlternateBase,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.Button,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.Highlight,
        QPalette.ColorRole.HighlightedText,
        QPalette.ColorRole.ToolTipBase,
        QPalette.ColorRole.ToolTipText,
        QPalette.ColorRole.Link,
        QPalette.ColorRole.LinkVisited,
    ):
        color = qapp.palette().color(role)
        assert color.red() == color.green() == color.blue(), (role, color.name())
    for value in re.findall(r"#[0-9a-fA-F]{6}\b", qapp.styleSheet()):
        assert value[1:3].lower() == value[3:5].lower() == value[5:7].lower(), value


def test_cancel_and_close_keeps_thread_alive_until_finish(
    qtbot, archive_path: Path, tmp_path: Path, monkeypatch
) -> None:
    started = []
    release = Event()

    def slow_parse(path):
        started.append(path)
        assert release.wait(timeout=10), "The GUI did not release the test worker."
        return parse_archive(path)

    monkeypatch.setattr("qiime2_provenance.app.parse_archive", slow_parse)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.add_paths([archive_path, make_archive(tmp_path / "second.qza")])
    window.start_parsing()
    try:
        qtbot.waitUntil(lambda: bool(started))
        window.close()
        assert window.close_pending
    finally:
        # Synchronize explicitly; emulation can delay GUI scheduling past a sleep.
        release.set()
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert len(started) == 1
    assert not window.isVisible()
