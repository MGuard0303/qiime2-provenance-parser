"""Qt desktop shell: B controls above A files; C evidence fills the right pane."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QDragEnterEvent,
    QDropEvent,
    QFileOpenEvent,
    QIcon,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .parser import ActionRecord, Report, parse_archive
from .render import render_action, render_html, render_parameters, render_text
from .style import configure_application, monospace_font


class ParseWorker(QThread):
    """Parse sequentially off the UI thread and cancel safely between archives."""

    succeeded = Signal(object)
    failed = Signal(str, str)
    progress = Signal(int, int, str)

    def __init__(self, paths: Sequence[Path], parent: QWidget) -> None:
        """Snapshot the work queue so GUI changes cannot mutate active work."""
        super().__init__(parent)
        self.paths = tuple(paths)

    def run(self) -> None:
        """Emit independent results; one bad file does not abort the remaining queue."""
        for index, path in enumerate(self.paths):
            if self.isInterruptionRequested():
                break
            self.progress.emit(index, len(self.paths), path.name)
            try:
                report = parse_archive(path)
            except Exception as error:
                # A worker boundary must also contain unexpected parser failures.
                self.failed.emit(str(path), f"{type(error).__name__}: {error}")
            else:
                self.succeeded.emit(report)
            self.progress.emit(index + 1, len(self.paths), path.name)


def label(text: str, name: str = "muted") -> QLabel:
    """Create a wrapping text label with a semantic theme role."""
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(name != "brand")
    return widget


class MainWindow(QMainWindow):
    """File queue, asynchronous parsing and an inspectable provenance workspace."""

    def __init__(self) -> None:
        """Construct a responsive two-column layout and explicit result state."""
        super().__init__()
        self.setWindowTitle("QIIME 2 · Provenance Studio")
        self.resize(1220, 850)
        self.setMinimumSize(980, 740)
        self.setAcceptDrops(True)
        self.paths: list[Path] = []
        self.reports: dict[str, Report] = {}
        self.errors: dict[str, str] = {}
        self.worker: ParseWorker | None = None
        self.close_pending = False
        self.current_report: Report | None = None
        self.current_actions: tuple[ActionRecord, ...] = ()
        self._build_ui()
        self._build_menu()
        self._update_buttons()

    def _build_ui(self) -> None:
        """Place controls above files on the left and evidence on the right."""
        canvas = QWidget()
        canvas.setObjectName("canvas")
        self.setCentralWidget(canvas)
        outer = QVBoxLayout(canvas)
        outer.setContentsMargins(24, 20, 24, 14)
        outer.setSpacing(18)
        header = QHBoxLayout()
        title = QVBoxLayout()
        title.addWidget(label("PROVENANCE STUDIO", "eyebrow"))
        title.addWidget(label("QIIME 2  /  Methods & Evidence", "brand"))
        header.addLayout(title)
        header.addStretch()
        header.addWidget(label(f"Local analysis   ·   v{__version__}", "muted"))
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        sidebar = QWidget()
        sidebar.setMinimumWidth(300)
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(14)

        controls = QFrame()
        controls.setObjectName("panel")
        box = QVBoxLayout(controls)
        box.setContentsMargins(18, 18, 18, 18)
        box.setSpacing(10)
        box.addWidget(label("Workspace", "heading"))
        box.addWidget(label("Load files and trace their analysis history."))
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self.choose_files)
        box.addWidget(self.add_button)
        self.parse_button = QPushButton("Parse All Files")
        self.parse_button.setObjectName("primary")
        self.parse_button.clicked.connect(self.start_parsing)
        box.addWidget(self.parse_button)
        row = QHBoxLayout()
        self.export_button = QPushButton("Export Report")
        self.export_button.clicked.connect(self.export_report)
        self.copy_button = QPushButton("Copy Report")
        self.copy_button.clicked.connect(self.copy_report)
        row.addWidget(self.export_button)
        row.addWidget(self.copy_button)
        box.addLayout(row)
        self.cancel_button = QPushButton("Stop After Current File")
        self.cancel_button.clicked.connect(self.cancel_parsing)
        self.cancel_button.hide()
        box.addWidget(self.cancel_button)
        left.addWidget(controls)

        files_panel = QFrame()
        files_panel.setObjectName("panel")
        files_box = QVBoxLayout(files_panel)
        files_box.setContentsMargins(18, 18, 18, 14)
        files_box.addWidget(label("Files", "heading"))
        files_box.addWidget(
            label(
                "Drop .qza / .qzv files here.\nMultiple files supported; originals stay read-only."
            )
        )
        self.file_list = QListWidget()
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.setWordWrap(False)
        self.file_list.setAccessibleName("Loaded QIIME 2 files")
        self.file_list.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.file_list.currentRowChanged.connect(self.select_file)
        files_box.addWidget(self.file_list, 1)
        self.file_count = label("0 files")
        files_box.addWidget(self.file_count)
        file_tools = QHBoxLayout()
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_files)
        file_tools.addWidget(self.remove_button)
        file_tools.addWidget(self.clear_button)
        files_box.addLayout(file_tools)
        left.addWidget(files_panel, 1)

        results = QFrame()
        results.setObjectName("panel")
        right = QVBoxLayout(results)
        right.setContentsMargins(24, 20, 24, 18)
        right.setSpacing(10)
        right.addWidget(label("ANALYSIS RESULTS", "eyebrow"))
        self.result_title = label("Trace the analysis behind each file", "heading")
        self.result_title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right.addWidget(self.result_title)
        self.result_type = label("Add QIIME 2 files, then select Parse All Files.")
        right.addWidget(self.result_type)
        metrics = QHBoxLayout()
        metrics.setSpacing(28)
        self.action_count = label("—", "metric")
        self.artifact_count = label("—", "metric")
        self.evidence_status = label("Waiting for files", "muted")
        for value, caption in [
            (self.action_count, "method executions"),
            (self.artifact_count, "artifacts"),
        ]:
            metric = QVBoxLayout()
            metric.addWidget(value)
            metric.addWidget(label(caption))
            metrics.addLayout(metric)
        metrics.addStretch()
        metrics.addWidget(self.evidence_status)
        right.addLayout(metrics)

        self.tabs = QTabWidget()
        chain = QWidget()
        chain_layout = QVBoxLayout(chain)
        chain_layout.setContentsMargins(0, 12, 0, 0)
        chain_layout.addWidget(
            label(
                "Dependency order · Branches may run in parallel · "
                "Select a step to inspect its evidence"
            )
        )
        chain_split = QSplitter(Qt.Orientation.Vertical)
        chain_split.setChildrenCollapsible(False)
        self.action_list = QListWidget()
        self.action_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.action_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.action_list.setMinimumHeight(100)
        self.action_list.setAccessibleName("Method evidence chain")
        self.action_list.currentRowChanged.connect(self.select_action)
        self.action_detail = QTextBrowser()
        self.action_detail.setOpenLinks(False)
        self.action_detail.anchorClicked.connect(self.follow_artifact)
        self.action_detail.document().setDefaultFont(QApplication.font())
        self.action_detail.setHtml(
            "<h3>Evidence for every step</h3>"
            "<p>Inspect methods, input dependencies, UUIDs and recorded parameters.</p>"
        )
        chain_split.addWidget(self.action_list)
        chain_split.addWidget(self.action_detail)
        chain_split.setSizes([255, 280])
        chain_layout.addWidget(chain_split, 1)
        self.tabs.addTab(chain, "Evidence Chain")

        self.parameters_view = QTextBrowser()
        self.parameters_view.setOpenLinks(False)
        self.parameters_view.setAccessibleName("QIIME parameters for every step")
        self.parameters_view.document().setDefaultFont(QApplication.font())
        self.parameters_view.setPlainText("Parse a file to inspect every recorded QIIME parameter.")
        self.tabs.addTab(self.parameters_view, "QIIME Parameters")

        report_page = QWidget()
        report_layout = QVBoxLayout(report_page)
        report_layout.setContentsMargins(0, 10, 0, 0)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search methods, UUIDs or parameters in the full report…")
        self.search.returnPressed.connect(self.find_text)
        search_row.addWidget(self.search)
        next_button = QPushButton("Find Next")
        next_button.clicked.connect(self.find_text)
        search_row.addWidget(next_button)
        report_layout.addLayout(search_row)
        self.full_report = QPlainTextEdit()
        self.full_report.setReadOnly(True)
        self.full_report.setFont(monospace_font())
        report_layout.addWidget(self.full_report)
        self.tabs.addTab(report_page, "Full Report")
        self.raw_yaml = QPlainTextEdit()
        self.raw_yaml.setReadOnly(True)
        self.raw_yaml.setFont(monospace_font())
        self.tabs.addTab(self.raw_yaml, "Raw YAML")
        self.tabs.setCurrentWidget(self.parameters_view)
        right.addWidget(self.tabs, 1)
        right.addWidget(
            label(
                "Reads provenance only. Data payload integrity is not checked; "
                "analysis commands are not executed."
            )
        )
        splitter.addWidget(sidebar)
        splitter.addWidget(results)
        splitter.setSizes([325, 825])
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        outer.addWidget(self.progress_bar)
        self.status = label("Ready · Drop QIIME 2 files to begin", "status")
        outer.addWidget(self.status)

    def _build_menu(self) -> None:
        """Expose standard keyboard shortcuts and application information."""
        menu = self.menuBar().addMenu("File")
        open_action = QAction("Add Files…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_files)
        menu.addAction(open_action)
        export_action = QAction("Export Report…", self)
        export_action.setShortcut(QKeySequence.StandardKey.Save)
        export_action.triggered.connect(self.export_report)
        menu.addAction(export_action)
        help_menu = self.menuBar().addMenu("Help")
        about = QAction("About Provenance Studio", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

    @Slot()
    def show_about(self) -> None:
        """Explain the local-only evidence scope and underlying components."""
        QMessageBox.about(
            self,
            "Provenance Studio",
            f"QIIME 2 Provenance Studio {__version__}\n\n"
            "Built with PySide6 / Qt and PyYAML.\nQIIME 2 and conda are not required.\n"
            "Reads local provenance. Files are not uploaded.\n"
            "Use Raw YAML to inspect the complete evidence. Data payload integrity is not checked.",
        )

    def _update_buttons(self) -> None:
        """Keep actions consistent with the queue and active worker lifetime."""
        busy = self.worker is not None
        self.parse_button.setEnabled(bool(self.paths) and not busy)
        self.add_button.setEnabled(not busy)
        self.remove_button.setEnabled(bool(self.paths) and not busy)
        self.clear_button.setEnabled(bool(self.paths) and not busy)
        self.export_button.setEnabled(self.current_report is not None)
        self.copy_button.setEnabled(self.current_report is not None)
        self.cancel_button.setVisible(busy)
        self.file_count.setText(f"{len(self.paths)} files · {len(self.reports)} parsed")

    @Slot()
    def choose_files(self) -> None:
        """Load local QZA/QZV paths from an application-owned English file dialog."""
        if self.worker is not None:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add QIIME 2 Files",
            "",
            "QIIME 2 (*.qza *.qzv)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        self.add_paths([Path(path) for path in paths])

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Normalize paths, reject unavailable files and avoid duplicate queue entries."""
        if self.worker is not None:
            self.status.setText(
                "Parsing is in progress. Add more files after the current batch finishes."
            )
            return
        added = 0
        rejected: list[str] = []
        for path in paths:
            try:
                resolved = path.expanduser().resolve(strict=True)
                if not resolved.is_file() or resolved.suffix.lower() not in {".qza", ".qzv"}:
                    raise ValueError("A .qza or .qzv file is required")
            except (OSError, ValueError) as error:
                rejected.append(f"{path.name}: {error}")
                continue
            if resolved in self.paths:
                continue
            self.paths.append(resolved)
            item = QListWidgetItem(f"{resolved.name}\nReady to parse")
            item.setToolTip(str(resolved))
            self.file_list.addItem(item)
            added += 1
        if self.file_list.currentRow() < 0 and self.paths:
            self.file_list.setCurrentRow(0)
        self.status.setText(
            f"Added {added} files" + (" · Skipped: " + "; ".join(rejected) if rejected else "")
        )
        self._update_buttons()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept local file drops while the work queue is idle."""
        mime = event.mimeData()
        if mime is not None and mime.hasUrls() and self.worker is None:
            if any(url.isLocalFile() for url in mime.urls()):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Route Finder drops through the same validation as the open dialog."""
        mime = event.mimeData()
        if mime is not None:
            self.add_paths([Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()])
            event.acceptProposedAction()

    @Slot()
    def start_parsing(self) -> None:
        """Invalidate stale results and start a fresh read of every queued file."""
        if not self.paths or self.worker is not None:
            return
        self.reports.clear()
        self.errors.clear()
        for index, path in enumerate(self.paths):
            item = self.file_list.item(index)
            if item is not None:
                item.setText(f"{path.name}\nWaiting to parse")
        self.select_file(self.file_list.currentRow())
        self.worker = ParseWorker(self.paths, self)
        self.worker.succeeded.connect(self.accept_report)
        self.worker.failed.connect(self.accept_error)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.parsing_finished)
        self.progress_bar.setRange(0, len(self.paths))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.cancel_button.setEnabled(True)
        self._update_buttons()
        self.worker.start()

    @Slot(object)
    def accept_report(self, value: object) -> None:
        """Validate the cross-thread payload before updating GUI-owned state."""
        if not isinstance(value, Report):
            return
        self.reports[str(value.path)] = value
        index = self.paths.index(value.path)
        item = self.file_list.item(index)
        if item is not None:
            item.setText(
                f"{value.path.name}\nParsed · {len(value.executions)} steps"
                + (" · Missing evidence" if value.missing_inputs else "")
            )
        if self.file_list.currentRow() == index:
            self.select_file(index)
        self._update_buttons()

    @Slot(str, str)
    def accept_error(self, path: str, message: str) -> None:
        """Keep failures attached to their files so a batch remains inspectable."""
        self.errors[path] = message
        index = self.paths.index(Path(path))
        item = self.file_list.item(index)
        if item is not None:
            item.setText(f"{Path(path).name}\nParse failed · Select to inspect the error")
            item.setToolTip(message)
        if self.file_list.currentRow() == index:
            self.select_file(index)

    @Slot(int, int, str)
    def update_progress(self, done: int, total: int, name: str) -> None:
        """Display bounded batch progress without estimating a file's parse time."""
        self.progress_bar.setValue(done)
        self.status.setText(f"Parsing {done}/{total} · {name}")

    @Slot()
    def cancel_parsing(self) -> None:
        """Request cooperative cancellation after the current archive finishes."""
        if self.worker is not None:
            self.worker.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status.setText("Finishing the current file, then stopping.")

    @Slot()
    def parsing_finished(self) -> None:
        """Release the stopped worker and honor a deferred window-close request."""
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None
        self.progress_bar.hide()
        pending = len(self.paths) - len(self.reports) - len(self.errors)
        self.status.setText(
            f"Complete · Parsed {len(self.reports)} · Failed {len(self.errors)} · Pending {pending}"
        )
        self._update_buttons()
        if self.close_pending:
            self.close()

    @Slot(int)
    def select_file(self, index: int) -> None:
        """Display only results associated with the selected file."""
        self.current_report = None
        self.current_actions = ()
        self.action_list.clear()
        self.raw_yaml.clear()
        self.full_report.clear()
        self.parameters_view.setPlainText("Parse a file to inspect every recorded QIIME parameter.")
        self.action_count.setText("—")
        self.artifact_count.setText("—")
        self.evidence_status.setText("Waiting to parse")
        if not 0 <= index < len(self.paths):
            self.result_title.setText("Trace the analysis behind each file")
            self.result_type.setText("Add QIIME 2 files, then select Parse All Files.")
            self.action_detail.setPlainText("Waiting for files.")
            self._update_buttons()
            return
        path = self.paths[index]
        self.result_title.setText(path.name)
        self.result_title.setToolTip(str(path))
        report = self.reports.get(str(path))
        if report is None:
            error = self.errors.get(str(path))
            self.result_type.setText("Parse failed" if error else "File loaded and ready to parse.")
            self.action_detail.setPlainText(
                error or "Select Parse All Files to inspect the evidence chain."
            )
            self.evidence_status.setText("Evidence unavailable" if error else "Waiting to parse")
        else:
            self.current_report = report
            self.current_actions = report.executions
            self.result_type.setText(report.semantic_type)
            self.action_count.setText(str(len(report.executions)))
            self.artifact_count.setText(str(len(report.records)))
            self.evidence_status.setText(
                f"Missing {len(report.missing_inputs)} upstream records"
                if report.missing_inputs
                else "All upstream references present"
            )
            for position, record in enumerate(self.current_actions, 1):
                item = QListWidgetItem(
                    f"{position:02d}   {record.command}"
                    + ("   ·   Current file" if record.is_main else "")
                    + f"\n        {len(record.inputs)} inputs  ·  {record.uuid[:8]}"
                )
                item.setToolTip(record.uuid)
                self.action_list.addItem(item)
            self.action_list.setCurrentRow(len(self.current_actions) - 1)
            if len(self.current_actions) <= 3:
                self.action_list.scrollToTop()
            self.refresh_display()
        self._update_buttons()

    @Slot()
    def refresh_display(self) -> None:
        """Render cached evidence with recorded parameters in every report view."""
        self.parameters_view.setPlainText("Parse a file to inspect every recorded QIIME parameter.")
        if self.current_report is not None:
            self.parameters_view.setHtml(render_parameters(self.current_report))
            self.full_report.setPlainText(render_text(self.current_report, True))
            self.select_action(self.action_list.currentRow())

    @Slot(int)
    def select_action(self, index: int) -> None:
        """Show the selected execution and its original action YAML text."""
        if self.current_report is None or not 0 <= index < len(self.current_actions):
            return
        record = self.current_actions[index]
        self.action_detail.setHtml(render_action(record, self.current_report, True))
        self.raw_yaml.setPlainText(f"# {record.member}\n\n{record.raw_yaml}")

    @Slot(QUrl)
    def follow_artifact(self, url: QUrl) -> None:
        """Resolve an input UUID to its producing execution within this report."""
        if url.scheme() != "artifact" or self.current_report is None:
            return
        uid = url.path()
        target = next((r for r in self.current_report.records if r.artifact_uuid == uid), None)
        if target is not None:
            for index, record in enumerate(self.current_actions):
                if record.uuid == target.uuid:
                    self.action_list.setCurrentRow(index)
                    break

    @Slot()
    def find_text(self) -> None:
        """Find the next literal string, wrapping to the beginning of the report."""
        term = self.search.text()
        if term and not self.full_report.find(term):
            cursor = self.full_report.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.full_report.setTextCursor(cursor)
            if not self.full_report.find(term):
                self.status.setText(f"No match found: {term}")

    @Slot()
    def copy_report(self) -> None:
        """Copy the complete current report, including every recorded parameter."""
        if self.current_report is not None:
            QApplication.clipboard().setText(render_text(self.current_report, True))
            self.status.setText("The current report has been copied to the clipboard.")

    @Slot()
    def export_report(self) -> None:
        """Export the selected report to TXT/JSON/HTML; never overwrite an input archive."""
        report = self.current_report
        if report is None:
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Current Report",
            report.path.stem + "-provenance.txt",
            "Text report (*.txt);;JSON data (*.json);;HTML report (*.html)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not path:
            return
        target = Path(path).expanduser()
        expected = (
            ".json"
            if "JSON" in selected_filter
            else ".html"
            if "HTML" in selected_filter
            else ".txt"
        )
        if not target.suffix:
            target = target.with_suffix(expected)
        try:
            if target.resolve() in self.paths or target.suffix.lower() not in {
                ".txt",
                ".json",
                ".html",
            }:
                raise ValueError(
                    "Use a .txt, .json or .html filename. Input archives cannot be overwritten."
                )
            content = (
                report.to_json(True)
                if target.suffix.lower() == ".json"
                else (
                    render_html(report, True)
                    if target.suffix.lower() == ".html"
                    else render_text(report, True)
                )
            )
            target.write_text(content, encoding="utf-8")
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Export Failed", str(error))
            return
        self.status.setText(f"Exported: {target}")

    @Slot()
    def remove_selected(self) -> None:
        """Remove a queue entry and its cached result; leave the source file untouched."""
        index = self.file_list.currentRow()
        if self.worker is not None or not 0 <= index < len(self.paths):
            return
        path = self.paths.pop(index)
        self.reports.pop(str(path), None)
        self.errors.pop(str(path), None)
        self.file_list.takeItem(index)
        self.select_file(self.file_list.currentRow())
        self._update_buttons()

    @Slot()
    def clear_files(self) -> None:
        """Clear the workspace queue and in-memory results."""
        if self.worker is not None:
            return
        self.paths.clear()
        self.reports.clear()
        self.errors.clear()
        self.file_list.clear()
        self.select_file(-1)
        self._update_buttons()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Defer shutdown until the worker exits to avoid destroying a live QThread."""
        if self.worker is not None:
            self.close_pending = True
            self.cancel_parsing()
            event.ignore()
        else:
            event.accept()


class Application(QApplication):
    """Receive macOS Finder open-file events, including events during startup."""

    def __init__(self, argv: list[str]) -> None:
        """Initialize pending paths before Qt can deliver native startup events."""
        self.window: MainWindow | None = None
        self.pending_paths: list[Path] = []
        super().__init__(argv)

    def event(self, event: QEvent) -> bool:
        """Forward Finder-selected files into the application queue."""
        if isinstance(event, QFileOpenEvent):
            path = Path(event.file())
            if self.window is None:
                self.pending_paths.append(path)
            else:
                self.window.add_paths([path])
                self.window.raise_()
            return True
        return super().event(event)


def main() -> int:
    """Launch the standalone desktop application with optional input file paths."""
    app = Application(sys.argv)
    app.setApplicationName("QIIME 2 Provenance Studio")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Provenance Studio")
    for parent in list(Path(__file__).resolve().parents)[1:3]:
        icon = parent / "assets/app.png"
        if icon.is_file():
            app.setWindowIcon(QIcon(str(icon)))
            break
    configure_application(app)
    window = MainWindow()
    app.window = window
    window.show()
    paths = [Path(arg) for arg in sys.argv[1:] if not arg.startswith("-")] + app.pending_paths
    if paths:
        window.add_paths(paths)
        QTimer.singleShot(0, window.start_parsing)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
