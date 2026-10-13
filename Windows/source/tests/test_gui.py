"""Test user-visible state and worker lifecycle using real Qt events."""

from pathlib import Path
from threading import Event

from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QFileDialog

from qiime2_provenance.app import MainWindow
from qiime2_provenance.parser import parse_archive
from conftest import make_archive


def test_batch_failure_selection_and_parameters(qtbot, archive_path: Path, tmp_path: Path) -> None:
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
    assert "trunc_len_f" not in window.full_report.toPlainText()
    window.verbose.setChecked(True)
    assert "trunc_len_f" in window.full_report.toPlainText()
    assert "230" in window.action_detail.toPlainText()
    window.follow_artifact(QUrl("artifact:" + window.current_report.records[0].artifact_uuid))
    assert window.action_list.currentRow() == 0
    window.file_list.setCurrentRow(1)
    assert window.current_report is None
    assert not window.export_button.isEnabled()
    assert "zip" in window.action_detail.toPlainText().lower()
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
    window.verbose.setChecked(True)
    target = tmp_path / "report.json"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *a: (str(target), "JSON 数据 (*.json)")
    )
    window.export_report()
    assert '"trunc_len_f": 230' in target.read_text()
    window.search.setText("trunc_len_f")
    window.find_text()
    assert window.full_report.textCursor().selectedText() == "trunc_len_f"


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
