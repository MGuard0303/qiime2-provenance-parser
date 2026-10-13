"""Run deterministic acceptance checks inside the shipped Windows executable."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
import traceback
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile

from PySide6.QtCore import QCoreApplication, QMimeData, QPoint, QPointF, Qt, QUrl, qVersion
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette
from PySide6.QtWidgets import QApplication, QCheckBox

from . import __version__
from .app import MainWindow
from .parser import parse_archive
from .render import render_html, render_text
from .style import configure_application


def make_fixture(path: Path) -> None:
    """Create a small Unicode-path archive inside a temporary test directory."""
    root, upstream = str(UUID(int=1)), str(UUID(int=2))
    with ZipFile(path, "w") as archive:
        archive.writestr(
            f"{root}/metadata.yaml", f"uuid: {root}\ntype: SampleData[Test]\nformat: TestFmt\n"
        )
        archive.writestr(f"{root}/VERSION", "QIIME 2\narchive: 7.1\nframework: 2026.4.0\n")
        archive.writestr(
            f"{root}/provenance/action/action.yaml",
            f"execution:\n  uuid: {UUID(int=3)}\naction:\n  type: method\n"
            "  plugin: !ref 'environment:plugins:dada2'\n  action: denoise_paired\n"
            f"  inputs:\n    - seqs: {upstream}\n"
            "  parameters:\n    - trunc_len_f: 230\n    - name: 中文测试\n",
        )
        archive.writestr(
            f"{root}/provenance/artifacts/{upstream}/action/action.yaml",
            f"execution:\n  uuid: {UUID(int=4)}\naction:\n  type: import\n",
        )


def main(arguments: list[str]) -> int:
    """Exercise the actual EXE, native DLLs, worker and read-only real archives.

    The output explicitly records the execution environment. Wine results must
    not be presented as validation on a native Windows installation.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--environment", default="unspecified")
    args = parser.parse_args(arguments)
    result: dict[str, object] = {
        "app_version": __version__,
        "execution_environment": args.environment,
        "sys_platform": sys.platform,
        "machine": platform.machine(),
        "python": platform.python_version(),
        "executable": sys.executable,
        "isolated": sys.flags.isolated,
        "qt_version": qVersion(),
    }
    application = QApplication([sys.argv[0]])
    configure_application(application)
    window = MainWindow()
    result["qt_platform_plugin"] = application.platformName()
    result["font_family"] = application.font().family()
    result["font_point_size"] = application.font().pointSize()
    try:
        assert sys.platform == "win32", "This check must run inside the Windows distribution."
        assert sys.flags.isolated == 1
        with tempfile.TemporaryDirectory(prefix="qiime2-check-") as directory:
            temp = Path(directory) / "中文 路径"
            temp.mkdir()
            fixture = temp / "证据 文件.qza"
            make_fixture(fixture)
            bad = temp / "broken.qza"
            bad.write_bytes(b"not a zip")
            window.show()
            application.processEvents()
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(fixture))])
            enter = QDragEnterEvent(
                QPoint(50, 500),
                Qt.DropAction.CopyAction,
                mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            QCoreApplication.sendEvent(window, enter)
            assert enter.isAccepted()
            drop = QDropEvent(
                QPointF(50, 500),
                Qt.DropAction.CopyAction,
                mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            QCoreApplication.sendEvent(window, drop)
            assert window.paths == [fixture.resolve()]
            window.add_paths([fixture, bad])
            assert len(window.paths) == 2
            window.start_parsing()
            deadline = time.monotonic() + 90
            while window.worker is not None and time.monotonic() < deadline:
                application.processEvents()
                time.sleep(0.01)
            assert window.worker is None, "Worker timed out."
            assert len(window.reports) == 1 and len(window.errors) == 1
            assert window.action_list.count() == 2
            assert not hasattr(window, "verbose") and not hasattr(window, "set_verbose")
            assert not window.findChildren(QCheckBox)
            assert "trunc_len_f: 230" in window.full_report.toPlainText()
            assert "230" in window.action_detail.toPlainText()
            assert window.tabs.currentWidget() is window.parameters_view
            assert application.font().pointSize() == 11
            assert application.font().family()
            for role in (
                QPalette.ColorRole.Window,
                QPalette.ColorRole.Base,
                QPalette.ColorRole.Text,
                QPalette.ColorRole.Highlight,
                QPalette.ColorRole.HighlightedText,
            ):
                color = application.palette().color(role)
                assert color.red() == color.green() == color.blue()
            assert [window.tabs.tabText(index) for index in range(window.tabs.count())] == [
                "Evidence Chain", "QIIME Parameters", "Full Report", "Raw YAML",
            ]
            parameters = window.parameters_view.toPlainText()
            assert "01 · qiime tools import" in parameters
            assert "02 · qiime dada2 denoise-paired" in parameters
            assert "trunc_len_f" in parameters and "230" in parameters
            assert "中文测试" in parameters
            window.copy_report()
            assert "trunc_len_f: 230" in application.clipboard().text()
            report = window.current_report
            assert report is not None
            (temp / "结果.json").write_text(report.to_json(True), encoding="utf-8")
            (temp / "结果.html").write_text(render_html(report, True), encoding="utf-8")
            (temp / "结果.txt").write_text(render_text(report, True), encoding="utf-8")
            exported = json.loads((temp / "结果.json").read_text(encoding="utf-8"))
            assert exported["records"][-1]["parameters"]["trunc_len_f"] == 230
            assert exported["records"][-1]["parameters"]["name"] == "中文测试"
            window.search.setText("trunc_len_f")
            window.find_text()
            assert window.full_report.textCursor().selectedText() == "trunc_len_f"
            window.file_list.setCurrentRow(1)
            assert window.current_report is None and not window.export_button.isEnabled()
            assert "trunc_len_f" not in window.parameters_view.toPlainText()
            window.remove_selected()
            assert window.current_report is not None
            window.clear_files()
            result["gui_checks"] = [
                "Unicode paths",
                "drop events",
                "duplicate suppression",
                "background parsing",
                "error isolation",
                "always-on parameters for every execution",
                "parameter copy and details",
                "English controls",
                "readable default font",
                "neutral grayscale palette",
                "UTF-8 exports",
                "search",
                "file switching",
                "remove and clear",
            ]
        files: list[dict[str, object]] = []
        if args.data_root is not None:
            paths = sorted(
                path for path in args.data_root.rglob("*")
                if path.suffix.lower() in {".qza", ".qzv"}
                and not path.name.startswith("._") and path.is_file()
            )
            for path in paths:
                before = path.stat()
                report = parse_archive(path)
                after = path.stat()
                assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
                files.append(
                    {
                        "file": str(path.relative_to(args.data_root)),
                        "records": len(report.records),
                        "executions": len(report.executions),
                        "missing": list(report.missing_inputs),
                    }
                )
            result["real_archives"] = files
            example = args.data_root / "denoising-stats-cutadapt.qza"
            if example.is_file():
                window.add_paths([example])
                window.accept_report(parse_archive(example))
        if args.screenshot is not None:
            window.status.setText("Validation environment · " + args.environment)
            application.processEvents()
            window.action_list.scrollToTop()
            assert window.grab().save(str(args.screenshot))
        result["passed"] = True
        status = 0
    except Exception:
        result["passed"] = False
        result["error"] = traceback.format_exc()
        status = 1
    finally:
        if window.worker is not None:
            window.worker.requestInterruption()
            window.worker.wait()
            application.processEvents()
        window.close()
        application.processEvents()
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return status
