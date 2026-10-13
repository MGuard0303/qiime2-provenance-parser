# QIIME 2 Provenance Studio

## English

A desktop application built around the existing `qiime2_provenance_parser.py`.
It reads only metadata and provenance action YAML from local QZA/QZV archives.
It does not need to import QIIME 2 or extract sequencing data.

### Using the application

The current distribution is an **Apple Silicon / arm64 macOS `.app`**. Double-click
the application, drag QZA/QZV files into the window, and click “解析全部文件”
(Parse all files). Python, Qt, and PyYAML are included, so running the application
requires no installation of conda, Python, or QIIME 2, and no network connection.
You can copy the entire `.app` into Applications.

The layout follows the original sketch: the upper-left B area contains controls,
the lower-left A area contains the drop zone and file list, and the right-hand C
area displays results. Select files on the left. On the right, execution steps
appear in dependency order, followed by the selected step's detailed evidence.
Click an upstream UUID to jump to its step. “原始 YAML” (Raw YAML) shows the complete
source text for the selected step.

- Add files individually or in a batch by dragging them in; duplicates are removed. Remove selected files or clear the list.
- Parsing runs in a background thread. A failure in one file does not interrupt the remaining files.
- “停止” (Stop) takes effect after the current file finishes. Closing the window during parsing also waits for that file to finish safely.
- “Verbose：显示 QIIME 参数” (Verbose: show QIIME parameters) controls step details, the full report, copying, and exports. Raw YAML is always complete.
- Export the current file's report as TXT, JSON, or offline HTML. The full report supports keyword search.
- Use `⌘O` to add files and `⌘S` to export the current report. Finder's “Open With” can also send files to the application.

The original delivery was verified on macOS 26.6.2 / arm64. The application declares
macOS 13 as its minimum version; other macOS versions have not been tested on
physical machines. The distribution uses a local ad-hoc signature and has no
Apple Developer ID signature or notarization. After transfer through download,
email, or similar channels, another Mac may show a system security prompt; use
the macOS “Privacy & Security” process to allow opening it. Windows, Linux, and
Intel Mac distributions require separate builds and verification.

### Why a separate environment is used

The original script depends only on the Python standard library and PyYAML.
Adding the GUI to a complete QIIME 2 environment would introduce many unrelated
dependencies and could affect the existing analysis environment. This project
uses a separate Python 3.12 conda environment. Its runtime dependencies are
**PySide6 Essentials (Qt Widgets) and PyYAML**.

```bash
cd /path/to/qiime2-provenance-gui
conda env create -f environment.yml
conda activate qiime2-provenance-gui
qiime2-provenance
```

`environment.yml` supports development installation. `requirements-lock.txt`
records the exact Python package versions used for verification and packaging.
To reproduce the locked environment:

```bash
conda create -n qiime2-provenance-gui python=3.12.14 pip
conda activate qiime2-provenance-gui
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

The CLI retains `--file-path` and `--verbose`:

```bash
qiime2-provenance-cli --file-path ./example.qza --verbose
```

### Code structure and type checking

- `src/qiime2_provenance/parser.py`: safe YAML loader, ZIP reading, TypedDict interfaces, `ActionRecord` / `Report` models, reachability, and topological sorting.
- `src/qiime2_provenance/app.py`: Qt window, file queue, background thread, and interactions.
- `src/qiime2_provenance/render.py`: formatting for GUI details, CLI/TXT output, and offline HTML.
- `src/qiime2_provenance/style.py`: white panels, a light-gray background, and a muted teal theme.
- `scripts/build_app.py`: packaging with the current platform's Python and PyInstaller.
- `scripts/validate_real.py`: exhaustive reading of real QZA/QZV archives, comparing every record with the specified legacy parser.
- `tests/`: temporary test archives for graph structure, invalid input, exports, and the GUI lifecycle.

The original script remains separate. The new core preserves its logic and adds
types and necessary validation. `load_zipfile()`, `close_zipfile()`,
`get_action_files()`, and `parse_yaml()` retain their names, dictionary shapes,
and convention of returning exceptions as values. `parse_archive()` provides a
typed report to the GUI and raises exceptions on failure; the worker boundary
isolates those failures. All application code and build/validation scripts pass
`mypy --strict`, without `type: ignore` or disabled missing-import checks.

```bash
python -m mypy
python -m ruff check src scripts launcher.py
QT_QPA_PLATFORM=offscreen python -m pytest -q
python scripts/validate_real.py /path/to/ds-20200228 \
  --legacy /path/to/code/qiime2_provenance_parser.py \
  --output /path/to/validation.json
python scripts/build_app.py --dist dist --work build
```

### Evidence semantics and limits

Each artifact retains an independent record. The application recursively follows
the current artifact's inputs to obtain the reachable subgraph and orders it
topologically. When multiple outputs share an execution UUID, the step list shows
that execution once; the detailed report retains every artifact record and input
edge. Parallel steps may belong to different branches, so adjacent entries in the
list do not establish a direct input relationship. The main artifact remains
marked after executions are merged.

Missing ancestor provenance is reported with its UUID. Dependency cycles,
duplicate ZIP members, duplicate YAML keys, invalid UUIDs, and structural errors
raise errors to prevent silent overwriting of evidence. Each metadata/action YAML
is limited to 8 MiB, and the total action YAML size is limited to 64 MiB; archives
exceeding these limits are rejected. Custom tags such as `!ref` and `!cite` retain
their underlying values; inspect the original tags on the YAML page. Dates become
ISO strings, and YAML sets become stable lists.

This tool **does not verify checksums in the data area, execute QIIME 2 analyses,
or establish that an analysis method is scientifically valid**. The current JSON
export `schema_version` is 1. Exports include the source path, type, UUID, input
relationships, member locations, runtime, and optional parameters. The complete
original action YAML is available in the GUI.

### Historical verification of the original delivery

The 2026-10-13 bilingual documentation update does not claim new functional test
runs. Documentation, archive integrity and resource signature checks are recorded
separately from the original acceptance results.

For the original delivery, all 22 QZA and 14 QZV archives in the real-data directory passed verification.
Every action record matched the original parser, including those from the
approximately 2.96 GB `demux-cutadapt.qza`, multi-branch taxonomy, and a classifier
with multiple outputs. Source file sizes and modification times were compared
before and after parsing. No full hash or CRC scan of the data area was performed.
See `real-artifact-validation.json` in the delivery directory for the complete
file list, statistics, and comparison results.

Technical documentation: [Qt for Python](https://doc.qt.io/qtforpython-6/) and
[PyInstaller](https://pyinstaller.org/en/stable/usage.html). Third-party component
information and licenses are provided in `THIRD_PARTY_NOTICES.md` and `licenses/`.

### Viewing Verbose parameters

Select “Verbose：显示 QIIME 参数” (Verbose: show QIIME parameters) on the left. The
“QIIME 参数” (QIIME parameters) tab opens automatically on the right and displays
each step's recorded parameters, execution UUID, and evidence location inside the
ZIP archive in evidence-chain order. Multiple outputs of one execution are
merged. Steps without recorded parameters are explicitly marked. Parameter names
are shown unchanged, values retain their types, and unrecorded defaults are not
inferred. Step details, the full report, copying, and TXT / JSON / HTML exports
all use this switch.

---

## 中文

为现有 `qiime2_provenance_parser.py` 增加的桌面应用。仅读取本地 QZA/QZV 的
metadata 与 provenance action YAML；无需导入 QIIME 2，也无需解压测序数据。

### 使用应用

当前交付为 **Apple Silicon / arm64 macOS `.app`**。双击应用打开，将 QZA/QZV
拖入窗口，点击「解析全部文件」。应用包含 Python、Qt 和 PyYAML，运行时无需安装
conda、Python 或 QIIME 2，也无需联网。可将整个 `.app` 拷贝到 Applications。

布局遵循草图：左上 B 为控制区，左下 A 为拖拽与文件列表，右侧 C 为解析结果。
左侧可切换文件；右侧先显示按依赖排序的执行步骤，再显示该步骤的详细证据。
点击上游 UUID 可跳转到对应步骤。「原始 YAML」显示当前步骤的完整源文本。

- 支持批量拖入、添加文件、去重、移除所选、清空列表。
- 后台线程解析，单个文件失败不会中断其余文件。
- 「停止」在当前文件完成后生效；解析时关闭窗口也会等待当前文件安全退出。
- 「Verbose：显示 QIIME 参数」同步影响步骤详情、完整报告、复制与导出；原始 YAML 始终完整。
- 导出当前文件的 TXT、JSON 或离线 HTML 报告。完整报告支持关键词搜索。
- `⌘O` 添加文件，`⌘S` 导出当前报告。Finder「打开方式」也可将文件发送给应用。

原交付在 macOS 26.6.2 / arm64 上完成验证。应用声明最低 macOS 13，其他 macOS 版本
尚未实机验证。交付使用本地 ad-hoc 签名，未使用 Apple Developer ID 签名或公证；
经下载、邮件等渠道传输后，另一台 Mac 可能显示系统安全提示，可按 macOS 的
「隐私与安全性」流程允许打开。Windows、Linux 和 Intel Mac 需要分别构建与验证。

### 为什么新建环境

原脚本实际仅依赖 Python 标准库与 PyYAML。将 GUI 加入完整 QIIME 2 环境会引入
大量无关依赖，也可能影响既有分析环境。本项目使用单独的 Python 3.12 conda 环境，
运行依赖只有 **PySide6 Essentials（Qt Widgets）与 PyYAML**。

```bash
cd /path/to/qiime2-provenance-gui
conda env create -f environment.yml
conda activate qiime2-provenance-gui
qiime2-provenance
```

`environment.yml` 用于开发安装，`requirements-lock.txt` 记录本次验证和打包的
精确 Python 包版本。按锁定版本复现时：

```bash
conda create -n qiime2-provenance-gui python=3.12.14 pip
conda activate qiime2-provenance-gui
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

CLI 保留 `--file-path` 和 `--verbose`：

```bash
qiime2-provenance-cli --file-path ./example.qza --verbose
```

### 代码结构与类型检查

- `src/qiime2_provenance/parser.py`：安全 YAML loader、ZIP 读取、TypedDict 接口、
  `ActionRecord` / `Report` 数据模型、可达性及拓扑排序。
- `src/qiime2_provenance/app.py`：Qt 窗口、文件队列、后台线程及交互。
- `src/qiime2_provenance/render.py`：GUI 详情、CLI/TXT 和离线 HTML 的格式化。
- `src/qiime2_provenance/style.py`：白色面板、浅灰背景与低饱和青绿色主题。
- `scripts/build_app.py`：使用当前平台的 Python 和 PyInstaller 打包。
- `scripts/validate_real.py`：全量读取真实 QZA/QZV，与指定的旧解析器逐条比较。
- `tests/`：构造临时测试归档，验证图结构、错误输入、导出与 GUI 生命周期。

原脚本保持独立；新内核继承其逻辑并补齐类型与必要校验。`load_zipfile()`、
`close_zipfile()`、`get_action_files()`、`parse_yaml()` 保留命名、字典形状与
异常作为返回值的接口习惯；`parse_archive()` 为 GUI 提供类型明确的报告，
失败时抛出异常，由线程边界统一隔离。所有应用代码与构建/验证脚本通过
`mypy --strict`，没有 `type: ignore` 或关闭缺失依赖检查。

```bash
python -m mypy
python -m ruff check src scripts launcher.py
QT_QPA_PLATFORM=offscreen python -m pytest -q
python scripts/validate_real.py /path/to/ds-20200228 \
  --legacy /path/to/code/qiime2_provenance_parser.py \
  --output /path/to/validation.json
python scripts/build_app.py --dist dist --work build
```

### 证据语义与边界

每个 artifact 保留独立记录；从当前 artifact 的输入递归求出可达子图，按拓扑顺序
排列。多个输出共享 execution UUID 时，步骤列表显示一次执行；详细报告保留所有
artifact 记录与输入边。并列步骤可能来自不同分支，列表相邻位置不表示两者存在
直接输入关系。主 artifact 标记在执行合并后仍保留。

缺少祖先 provenance 会明确提示 UUID；循环依赖、重复 ZIP 成员、重复 YAML 键、
UUID 或结构错误会报错，避免静默覆盖证据。单个 metadata/action YAML 上限 8 MiB，
action YAML 总量上限 64 MiB；超限会拒绝解析。自定义 `!ref`、`!cite` 等标签保留
基础值，原始标签可在 YAML 页核对。日期转为 ISO 字符串，YAML 集合转为稳定列表。

本工具**不验证 data 区校验和，不执行 QIIME 2 分析，不证明分析方法科学有效**。
JSON 导出的 `schema_version` 当前为 1，包含源路径、类型、UUID、输入关系、成员位置、
运行时间以及可选参数。原始 action YAML 的完整内容在 GUI 中查看。

### 原交付历史验证

2026-10-13 的双语文档更新不代表重新执行了功能测试。文档、压缩包完整性和资源签名
检查与原交付验收结果分开记录。

原交付的真实数据目录中 22 个 QZA 与 14 个 QZV 全量通过，所有 action 记录与原解析器一致，
包括约 2.96 GB 的 demux-cutadapt.qza、多分支 taxonomy 和多输出 classifier。
校验采用源文件大小与修改时间的前后对照；未对数据区执行完整哈希或 CRC 扫描。
详细文件清单、统计与比较结果见交付目录的 `real-artifact-validation.json`。

技术文档：[Qt for Python](https://doc.qt.io/qtforpython-6/)、
[PyInstaller](https://pyinstaller.org/en/stable/usage.html)。第三方组件信息和许可证
见 `THIRD_PARTY_NOTICES.md` 与 `licenses/`。

### Verbose 参数查看

勾选左侧「Verbose：显示 QIIME 参数」，右侧自动打开「QIIME 参数」页，
按证据链顺序展示每一步记录的参数、执行 UUID 和 ZIP 内证据位置。
同一次执行的多个输出合并显示，未记录参数的步骤会明确标注。
参数名原样展示，值保留类型，不推断未记录的默认值。
步骤详情、完整报告、复制和 TXT / JSON / HTML 导出同步使用此开关。
