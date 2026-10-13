"""Qt desktop shell: B controls above A files; C evidence fills the right pane."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFileOpenEvent,
    QFont,
    QKeySequence,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
from .style import STYLESHEET


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
    widget.setWordWrap(True)
    return widget


class MainWindow(QMainWindow):
    """File queue, asynchronous parsing and an inspectable provenance workspace."""

    def __init__(self) -> None:
        """Construct a responsive two-column layout and explicit result state."""
        super().__init__()
        self.setWindowTitle("QIIME 2 · Provenance Studio")
        self.resize(1220, 850)
        self.setMinimumSize(940, 670)
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
        title.addWidget(label("QIIME 2  /  方法与证据", "brand"))
        header.addLayout(title)
        header.addStretch()
        header.addWidget(label(f"本地解析   ·   v{__version__}", "muted"))
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        sidebar = QWidget()
        sidebar.setMinimumWidth(285)
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(14)

        controls = QFrame()
        controls.setObjectName("panel")
        box = QVBoxLayout(controls)
        box.setContentsMargins(18, 18, 18, 18)
        box.setSpacing(10)
        box.addWidget(label("工作区", "heading"))
        box.addWidget(label("加载文件，追溯分析过程。"))
        self.add_button = QPushButton("＋  添加文件")
        self.add_button.clicked.connect(self.choose_files)
        box.addWidget(self.add_button)
        self.parse_button = QPushButton("解析全部文件")
        self.parse_button.setObjectName("primary")
        self.parse_button.clicked.connect(self.start_parsing)
        box.addWidget(self.parse_button)
        self.verbose = QCheckBox("Verbose：显示 QIIME 参数")
        self.verbose.setToolTip("查看每一步记录的参数；复制和导出也包含参数。")
        self.verbose.toggled.connect(self.set_verbose)
        box.addWidget(self.verbose)
        row = QHBoxLayout()
        self.export_button = QPushButton("导出报告")
        self.export_button.clicked.connect(self.export_report)
        self.copy_button = QPushButton("复制结果")
        self.copy_button.clicked.connect(self.copy_report)
        row.addWidget(self.export_button)
        row.addWidget(self.copy_button)
        box.addLayout(row)
        self.cancel_button = QPushButton("停止（完成当前文件后）")
        self.cancel_button.clicked.connect(self.cancel_parsing)
        self.cancel_button.hide()
        box.addWidget(self.cancel_button)
        left.addWidget(controls)

        files_panel = QFrame()
        files_panel.setObjectName("panel")
        files_box = QVBoxLayout(files_panel)
        files_box.setContentsMargins(18, 18, 18, 14)
        files_box.addWidget(label("文件", "heading"))
        files_box.addWidget(label("将 .qza / .qzv 拖到窗口\n支持多选，原文件以只读方式打开。"))
        self.file_list = QListWidget()
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.setWordWrap(False)
        self.file_list.setAccessibleName("已加载的 QIIME 2 文件")
        self.file_list.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.file_list.currentRowChanged.connect(self.select_file)
        files_box.addWidget(self.file_list, 1)
        self.file_count = label("0 个文件")
        files_box.addWidget(self.file_count)
        file_tools = QHBoxLayout()
        self.remove_button = QPushButton("移除所选")
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button = QPushButton("清空列表")
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
        right.addWidget(label("解析结果", "eyebrow"))
        self.result_title = label("从一个文件，读懂整个分析过程", "heading")
        self.result_title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right.addWidget(self.result_title)
        self.result_type = label("添加 QIIME 2 文件后，点击左侧解析按钮。")
        right.addWidget(self.result_type)
        metrics = QHBoxLayout()
        metrics.setSpacing(28)
        self.action_count = label("—", "metric")
        self.artifact_count = label("—", "metric")
        self.evidence_status = label("等待文件", "muted")
        for value, caption in [
            (self.action_count, "次方法执行"),
            (self.artifact_count, "个 Artifact"),
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
        chain_layout.addWidget(label("按依赖顺序排列 · 分支流程可并行 · 点击步骤查看证据"))
        chain_split = QSplitter(Qt.Orientation.Vertical)
        chain_split.setChildrenCollapsible(False)
        self.action_list = QListWidget()
        self.action_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.action_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.action_list.setMinimumHeight(100)
        self.action_list.setAccessibleName("方法证据链")
        self.action_list.currentRowChanged.connect(self.select_action)
        self.action_detail = QTextBrowser()
        self.action_detail.setOpenLinks(False)
        self.action_detail.anchorClicked.connect(self.follow_artifact)
        self.action_detail.document().setDefaultFont(QFont(".AppleSystemUIFont", 11))
        self.action_detail.setHtml(
            "<h3>每一步都有来源</h3><p>这里将显示方法、输入依赖、UUID 与参数。</p>"
        )
        chain_split.addWidget(self.action_list)
        chain_split.addWidget(self.action_detail)
        chain_split.setSizes([255, 280])
        chain_layout.addWidget(chain_split, 1)
        self.tabs.addTab(chain, "证据链")

        self.parameters_view = QTextBrowser()
        self.parameters_view.setOpenLinks(False)
        self.parameters_view.setAccessibleName("每一步的 QIIME 参数")
        self.parameters_view.document().setDefaultFont(QFont(".AppleSystemUIFont", 11))
        self.parameters_view.setPlainText("勾选左侧 Verbose，查看每一步的 QIIME 参数。")
        self.tabs.addTab(self.parameters_view, "QIIME 参数")

        report_page = QWidget()
        report_layout = QVBoxLayout(report_page)
        report_layout.setContentsMargins(0, 10, 0, 0)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("在完整报告中搜索方法、UUID 或参数…")
        self.search.returnPressed.connect(self.find_text)
        search_row.addWidget(self.search)
        next_button = QPushButton("查找下一个")
        next_button.clicked.connect(self.find_text)
        search_row.addWidget(next_button)
        report_layout.addLayout(search_row)
        self.full_report = QPlainTextEdit()
        self.full_report.setReadOnly(True)
        self.full_report.setFont(QFont("Menlo", 11))
        report_layout.addWidget(self.full_report)
        self.tabs.addTab(report_page, "完整报告")
        self.raw_yaml = QPlainTextEdit()
        self.raw_yaml.setReadOnly(True)
        self.raw_yaml.setFont(QFont("Menlo", 11))
        self.tabs.addTab(self.raw_yaml, "原始 YAML")
        right.addWidget(self.tabs, 1)
        right.addWidget(label("仅解析 provenance；不校验数据区的完整性，也不执行分析命令。"))
        splitter.addWidget(sidebar)
        splitter.addWidget(results)
        splitter.setSizes([310, 840])
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        outer.addWidget(self.progress_bar)
        self.status = label("就绪 · 可拖拽多个 QIIME 2 文件", "status")
        outer.addWidget(self.status)

    def _build_menu(self) -> None:
        """Expose standard keyboard shortcuts and application information."""
        menu = self.menuBar().addMenu("文件")
        open_action = QAction("添加文件…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_files)
        menu.addAction(open_action)
        export_action = QAction("导出报告…", self)
        export_action.setShortcut(QKeySequence.StandardKey.Save)
        export_action.triggered.connect(self.export_report)
        menu.addAction(export_action)
        help_menu = self.menuBar().addMenu("帮助")
        about = QAction("关于 Provenance Studio", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

    @Slot()
    def show_about(self) -> None:
        """Explain the local-only evidence scope and underlying components."""
        QMessageBox.about(
            self,
            "Provenance Studio",
            f"QIIME 2 Provenance Studio {__version__}\n\n"
            "使用 PySide6 / Qt 和 PyYAML。\n无需安装 QIIME 2 或 conda。\n"
            "仅读取本地 provenance，不上传文件。\n"
            "原始 YAML 可核对完整证据；数据区未做完整性校验。",
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
        self.file_count.setText(f"{len(self.paths)} 个文件 · {len(self.reports)} 个已解析")

    @Slot()
    def choose_files(self) -> None:
        """Load local QZA/QZV paths from the native file dialog."""
        if self.worker is not None:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "添加 QIIME 2 文件", "", "QIIME 2 (*.qza *.qzv)"
        )
        self.add_paths([Path(path) for path in paths])

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Normalize paths, reject unavailable files and avoid duplicate queue entries."""
        if self.worker is not None:
            self.status.setText("正在解析；请完成后再添加文件。")
            return
        added = 0
        rejected: list[str] = []
        for path in paths:
            try:
                resolved = path.expanduser().resolve(strict=True)
                if not resolved.is_file() or resolved.suffix.lower() not in {".qza", ".qzv"}:
                    raise ValueError("需要 .qza / .qzv 文件")
            except (OSError, ValueError) as error:
                rejected.append(f"{path.name}: {error}")
                continue
            if resolved in self.paths:
                continue
            self.paths.append(resolved)
            item = QListWidgetItem(f"{resolved.name}\n待解析")
            item.setToolTip(str(resolved))
            self.file_list.addItem(item)
            added += 1
        if self.file_list.currentRow() < 0 and self.paths:
            self.file_list.setCurrentRow(0)
        self.status.setText(
            f"添加 {added} 个文件" + (" · 跳过：" + "; ".join(rejected) if rejected else "")
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
                item.setText(f"{path.name}\n等待解析")
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
                f"{value.path.name}\n已解析 · {len(value.executions)} 个步骤"
                + (" · 有缺失" if value.missing_inputs else "")
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
            item.setText(f"{Path(path).name}\n解析失败 · 点击查看原因")
            item.setToolTip(message)
        if self.file_list.currentRow() == index:
            self.select_file(index)

    @Slot(int, int, str)
    def update_progress(self, done: int, total: int, name: str) -> None:
        """Display bounded batch progress without estimating a file's parse time."""
        self.progress_bar.setValue(done)
        self.status.setText(f"解析 {done}/{total} · {name}")

    @Slot()
    def cancel_parsing(self) -> None:
        """Request cooperative cancellation after the current archive finishes."""
        if self.worker is not None:
            self.worker.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status.setText("正在完成当前文件，随后停止。")

    @Slot()
    def parsing_finished(self) -> None:
        """Release the stopped worker and honor a deferred window-close request."""
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None
        self.progress_bar.hide()
        pending = len(self.paths) - len(self.reports) - len(self.errors)
        self.status.setText(
            f"完成 · 成功 {len(self.reports)} · 失败 {len(self.errors)} · 未处理 {pending}"
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
        self.parameters_view.setPlainText(
            "等待解析结果。" if self.verbose.isChecked()
            else "勾选左侧 Verbose，查看每一步的 QIIME 参数。"
        )
        self.action_count.setText("—")
        self.artifact_count.setText("—")
        self.evidence_status.setText("等待解析")
        if not 0 <= index < len(self.paths):
            self.result_title.setText("从一个文件，读懂整个分析过程")
            self.result_type.setText("添加 QIIME 2 文件后，点击左侧解析按钮。")
            self.action_detail.setPlainText("等待文件。")
            self._update_buttons()
            return
        path = self.paths[index]
        self.result_title.setText(path.name)
        self.result_title.setToolTip(str(path))
        report = self.reports.get(str(path))
        if report is None:
            error = self.errors.get(str(path))
            self.result_type.setText("解析失败" if error else "文件已加载，等待解析。")
            self.action_detail.setPlainText(error or "点击「解析全部文件」查看证据链。")
            self.evidence_status.setText("无法读取证据" if error else "等待解析")
        else:
            self.current_report = report
            self.current_actions = report.executions
            self.result_type.setText(report.semantic_type)
            self.action_count.setText(str(len(report.executions)))
            self.artifact_count.setText(str(len(report.records)))
            self.evidence_status.setText(
                f"缺少 {len(report.missing_inputs)} 个上游记录"
                if report.missing_inputs
                else "上游引用齐全"
            )
            for position, record in enumerate(self.current_actions, 1):
                item = QListWidgetItem(
                    f"{position:02d}   {record.command}"
                    + ("   ·   当前文件" if record.is_main else "")
                    + f"\n        {len(record.inputs)} 个输入  ·  {record.uuid[:8]}"
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
        """Render cached evidence; changing verbosity never reopens the source archive."""
        self.parameters_view.setPlainText(
            "等待解析结果。" if self.verbose.isChecked()
            else "勾选左侧 Verbose，查看每一步的 QIIME 参数。"
        )
        if self.current_report is not None:
            if self.verbose.isChecked():
                self.parameters_view.setHtml(render_parameters(self.current_report))
            self.full_report.setPlainText(
                render_text(self.current_report, self.verbose.isChecked())
            )
            self.select_action(self.action_list.currentRow())

    @Slot(bool)
    def set_verbose(self, enabled: bool) -> None:
        """Reveal all execution parameters immediately and synchronize report views."""
        self.refresh_display()
        if enabled:
            self.tabs.setCurrentWidget(self.parameters_view)
        elif self.tabs.currentWidget() is self.parameters_view:
            self.tabs.setCurrentIndex(0)

    @Slot(int)
    def select_action(self, index: int) -> None:
        """Show the selected execution and its original action YAML text."""
        if self.current_report is None or not 0 <= index < len(self.current_actions):
            return
        record = self.current_actions[index]
        self.action_detail.setHtml(
            render_action(record, self.current_report, self.verbose.isChecked())
        )
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
                self.status.setText(f"未找到：{term}")

    @Slot()
    def copy_report(self) -> None:
        """Copy the current report using the active parameter-display setting."""
        if self.current_report is not None:
            QApplication.clipboard().setText(
                render_text(self.current_report, self.verbose.isChecked())
            )
            self.status.setText("当前报告已复制到剪贴板。")

    @Slot()
    def export_report(self) -> None:
        """Export the selected report to TXT/JSON/HTML; never overwrite an input archive."""
        report = self.current_report
        if report is None:
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出当前报告",
            report.path.stem + "-provenance.txt",
            "文本报告 (*.txt);;JSON 数据 (*.json);;HTML 报告 (*.html)",
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
                raise ValueError("请使用 .txt、.json 或 .html 文件名；不可覆盖输入文件。")
            verbose = self.verbose.isChecked()
            content = (
                report.to_json(verbose)
                if target.suffix.lower() == ".json"
                else (
                    render_html(report, verbose)
                    if target.suffix.lower() == ".html"
                    else render_text(report, verbose)
                )
            )
            target.write_text(content, encoding="utf-8")
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "导出失败", str(error))
            return
        self.status.setText(f"已导出：{target}")

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
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f3f5f6"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#233c48"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#233c48"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#087d79"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
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
