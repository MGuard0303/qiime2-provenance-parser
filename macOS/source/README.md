# QIIME 2 Provenance Studio v1.2.0 — macOS arm64

## English

A desktop application built around the existing `qiime2_provenance_parser.py`.
It reads only metadata and provenance action YAML from local QZA/QZV archives.
It does not need to import QIIME 2 or extract sequencing data.

### Using the application

The current distribution is an **Apple Silicon / arm64 macOS `.app`**. Double-click
the application, drag QZA/QZV files into the window, and click **Parse All Files**. Python, Qt, and PyYAML are included, so running the application
requires no installation of conda, Python, or QIIME 2, and no network connection.
You can copy the entire `.app` into Applications.

The layout follows the original sketch: the upper-left B area contains controls,
the lower-left A area contains the drop zone and file list, and the right-hand C
area displays results. Select files on the left. On the right, execution steps
are available under **Evidence Chain**, followed by the selected step's detailed
evidence. **QIIME Parameters** is the default tab and always shows each step's
recorded parameters. Click an upstream UUID in the step details to jump to its
step. **Raw YAML** shows the complete source text for the selected step.

- Add files individually or in a batch by dragging them in; duplicates are removed. Remove selected files or clear the list.
- Parsing runs in a background thread. A failure in one file does not interrupt the remaining files.
- **Stop After Current File** takes effect after the current file finishes. Closing the window during parsing also waits for that file to finish safely.
- Detailed parameter display is always enabled in the GUI. Step details, **Full Report**, **Copy Report**, and TXT / JSON / HTML exports include every recorded parameter; there is no Verbose toggle. Raw YAML is always complete.
- Export the current file's report as TXT, JSON, or offline HTML. The full report supports keyword search.
- Use `⌘O` to add files and `⌘S` to export the current report. Finder's “Open With” can also send files to the application.

The historical v1.1.0 delivery was verified on macOS 26.6.2 / arm64. The application declares
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
cd /path/to/qiime2-provenance-parser/macOS/source
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

The GUI always includes parameters. The separate CLI retains its existing
`--file-path` and opt-in `--verbose` behavior:

```bash
qiime2-provenance-cli --file-path ./example.qza --verbose
```

### Code structure and type checking

- `src/qiime2_provenance/parser.py`: safe YAML loader, ZIP reading, TypedDict interfaces, `ActionRecord` / `Report` models, reachability, and topological sorting.
- `src/qiime2_provenance/app.py`: Qt window, file queue, background thread, and interactions.
- `src/qiime2_provenance/render.py`: formatting for GUI details, CLI/TXT output, and offline HTML.
- `src/qiime2_provenance/style.py`: white panels, dark-gray controls, a grayscale palette, readable native 11 pt interface fonts, and 11 pt fixed-width evidence text.
- `scripts/build_app.py`: packaging with the current platform's Python and PyInstaller.
- `scripts/validate_real.py`: exhaustive reading of real QZA/QZV archives, comparing every record with the specified legacy parser.
- `tests/`: temporary test archives for graph structure, invalid input, exports, and the GUI lifecycle.

The original script remains separate. The new core preserves its logic and adds
types and necessary validation. `load_zipfile()`, `close_zipfile()`,
`get_action_files()`, and `parse_yaml()` retain their names, dictionary shapes,
and convention of returning exceptions as values. `parse_archive()` provides a
typed report to the GUI and raises exceptions on failure; the worker boundary
isolates those failures. Application code and build/validation scripts use
`mypy --strict`, without `type: ignore` or disabled missing-import checks.
Run the checks below after changes; release-specific results are recorded separately.

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
relationships, member locations, runtime, and recorded parameters. GUI exports
always include parameters; the legacy CLI retains its verbosity option. The complete
original action YAML is available in the GUI.

### Current v1.2.0 validation

- Both current source test suites passed **24 tests each**. Strict mypy and Ruff
  checks passed for both platform implementations and their helper scripts.
- The packaged Windows runtime passed the same **24 tests** under **Wine 11.0
  on macOS arm64**, using Windows Python and Qt. Native Windows testing has
  not been performed.
- Each platform's parser matched the legacy parser across all **36 real QZA/QZV
  archives**. The macOS GUI check covered **115 executions and 894 recorded
  parameters**, verifying their display and exports.
- The standalone macOS window and its English file chooser were inspected in
  native macOS. Default parameter display, English controls, readable fonts and
  neutral grayscale appearance were checked.

The platform-root `build-validation.json` summarizes current v1.2.0 acceptance.
Individual runtime, native-interface, real-archive and source-test records keep
the detailed evidence. `archive/v1.1.0-validation/` contains snapshots of earlier
records; its results are historical and do not describe this new build.

### Historical v1.1.0 verification

The figures below describe the historical v1.1.0 delivery. They do not establish
acceptance of v1.2.0. Each new release stores its own validation records in the
platform delivery directory; documentation and package checks are recorded
separately from functional results. Historical v1.1.0 source tests covered
23 cases per platform; its GUI evidence checks covered 115 steps and 894
recorded parameters.

For v1.1.0, all 22 QZA and 14 QZV archives in the real-data directory passed verification.
Every action record matched the original parser, including those from the
approximately 2.96 GB `demux-cutadapt.qza`, multi-branch taxonomy, and a classifier
with multiple outputs. Source file sizes and modification times were compared
before and after parsing. No full hash or CRC scan of the data area was performed.
See `archive/v1.1.0-validation/real-artifact-validation.json` for the historical
file list, statistics, and comparison results.

Technical documentation: [Qt for Python](https://doc.qt.io/qtforpython-6/) and
[PyInstaller](https://pyinstaller.org/en/stable/usage.html). Third-party component
information and licenses are provided in `THIRD_PARTY_NOTICES.md` and `licenses/`.

### Always-on parameters and readable English interface

The interface is fully English. **QIIME Parameters** is selected when the window
opens. Detailed mode is always active, with no Verbose button or checkbox. Each step shows the parameter names and JSON values
recorded in `action.yaml`, its execution UUID, and its evidence ZIP member in
dependency order. Multiple outputs of one execution are grouped once. Empty
parameter records are explicitly identified. Original names and value types are
preserved; unrecorded defaults are not inferred. **Evidence Chain** step details,
**Full Report**, copying, and all GUI exports include the recorded parameters.

The appearance uses white and dark gray throughout, with a visible grayscale
selection and keyboard focus. Interface and parameter text use the native macOS
system font at 11 pt. Plain-text reports and YAML use Menlo, or the system
fixed-width font if unavailable, at 11 pt. Parameter tables have bold headings
and no custom fill colors. The exported HTML uses English language metadata and
readable neutral typography. Source values, filenames, and raw YAML retain their
original language.

The executable package is `QIIME2-Provenance-Studio-macOS-arm64-v1.2.0.zip`;
editable source is also provided as
`QIIME2-Provenance-Studio-macOS-source-v1.2.0.zip`. Earlier v1.1.0 packages and
validation records remain historical. Git operations are performed manually by
the project owner; updating or building the app does not run Git automatically.

---

## 中文

为现有 `qiime2_provenance_parser.py` 增加的桌面应用。仅读取本地 QZA/QZV 的
metadata 与 provenance action YAML；无需导入 QIIME 2，也无需解压测序数据。

### 使用应用

当前版本为 **v1.2.0，Apple Silicon / arm64 macOS `.app`**。双击应用打开，将 QZA/QZV
拖入窗口，点击 **Parse All Files**。应用包含 Python、Qt 和 PyYAML，运行时无需安装
conda、Python 或 QIIME 2，也无需联网。可将整个 `.app` 拷贝到 Applications。

布局遵循草图：左上 B 为控制区，左下 A 为拖拽与文件列表，右侧 C 为解析结果。
左侧可切换文件；右侧默认打开 **QIIME Parameters** 页，始终展示各步骤记录的参数。
**Evidence Chain** 页按依赖顺序显示步骤及详情，点击详情中的上游 UUID 可跳转。
**Raw YAML** 页显示当前步骤的完整源文本。

- 支持批量拖入、添加文件、去重、移除所选、清空列表。
- 后台线程解析，单个文件失败不会中断其余文件。
- **Stop After Current File** 在当前文件完成后生效；解析时关闭窗口也会等待当前文件安全退出。
- GUI 默认启用完整参数显示，步骤详情、**Full Report**、复制及 TXT / JSON / HTML 导出始终包含记录参数；已移除 Verbose 切换控件。原始 YAML 始终完整。
- 导出当前文件的 TXT、JSON 或离线 HTML 报告。完整报告支持关键词搜索。
- `⌘O` 添加文件，`⌘S` 导出当前报告。Finder「打开方式」也可将文件发送给应用。

历史 v1.1.0 交付在 macOS 26.6.2 / arm64 上完成验证。应用声明最低 macOS 13，其他 macOS 版本
尚未实机验证。交付使用本地 ad-hoc 签名，未使用 Apple Developer ID 签名或公证；
经下载、邮件等渠道传输后，另一台 Mac 可能显示系统安全提示，可按 macOS 的
「隐私与安全性」流程允许打开。Windows、Linux 和 Intel Mac 需要分别构建与验证。

### 为什么新建环境

原脚本实际仅依赖 Python 标准库与 PyYAML。将 GUI 加入完整 QIIME 2 环境会引入
大量无关依赖，也可能影响既有分析环境。本项目使用单独的 Python 3.12 conda 环境，
运行依赖只有 **PySide6 Essentials（Qt Widgets）与 PyYAML**。

```bash
cd /path/to/qiime2-provenance-parser/macOS/source
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

GUI 始终包含参数；独立 CLI 保留 `--file-path` 和通过 `--verbose` 显示参数的原有行为：

```bash
qiime2-provenance-cli --file-path ./example.qza --verbose
```

### 代码结构与类型检查

- `src/qiime2_provenance/parser.py`：安全 YAML loader、ZIP 读取、TypedDict 接口、
  `ActionRecord` / `Report` 数据模型、可达性及拓扑排序。
- `src/qiime2_provenance/app.py`：Qt 窗口、文件队列、后台线程及交互。
- `src/qiime2_provenance/render.py`：GUI 详情、CLI/TXT 和离线 HTML 的格式化。
- `src/qiime2_provenance/style.py`：白色面板、深灰控件、灰阶配色、11 pt 系统界面字体及 11 pt 等宽证据文本。
- `scripts/build_app.py`：使用当前平台的 Python 和 PyInstaller 打包。
- `scripts/validate_real.py`：全量读取真实 QZA/QZV，与指定的旧解析器逐条比较。
- `tests/`：构造临时测试归档，验证图结构、错误输入、导出与 GUI 生命周期。

原脚本保持独立；新内核继承其逻辑并补齐类型与必要校验。`load_zipfile()`、
`close_zipfile()`、`get_action_files()`、`parse_yaml()` 保留命名、字典形状与
异常作为返回值的接口习惯；`parse_archive()` 为 GUI 提供类型明确的报告，
失败时抛出异常，由线程边界统一隔离。应用代码与构建/验证脚本采用
`mypy --strict`，没有 `type: ignore` 或关闭缺失依赖检查。修改后执行下列检查，
每次发布的实际结果单独记录。

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
运行时间与记录参数。GUI 导出始终包含参数，历史 CLI 保留自己的详细模式选项。
原始 action YAML 的完整内容在 GUI 中查看。

### 当前 v1.2.0 验证

- 两套当前源码测试各通过 **24 项**；两平台实现及辅助脚本的严格 mypy 和 Ruff
  检查均通过。
- Windows 交付运行库在 **Wine 11.0 / macOS arm64** 中使用 Windows Python 和 Qt，
  同样通过 **24 项测试**。尚未进行原生 Windows 电脑实机验证。
- 两平台解析器分别与旧解析器核对全部 **36 个真实 QZA/QZV 归档**。macOS GUI
  检查覆盖 **115 次执行及 894 项记录参数**，核对了界面显示与导出。
- 已在原生 macOS 检查独立应用窗口及英文文件选择对话框，核对默认参数显示、
  英文控件、字体可读性及灰阶外观。

平台根目录 `build-validation.json` 汇总当前 v1.2.0 验收结果，各运行库、原生界面、
真实归档及源码测试记录保留详细证据。`archive/v1.1.0-validation/` 存放旧记录快照，
这些材料属于历史结果，不描述当前构建。

### 历史 v1.1.0 验证

以下数字描述历史 v1.1.0 交付，不作为 v1.2.0 已通过验收的结论。
每次新发布均在平台交付目录保存独立验证记录；文档与包检查和功能结果分别记录。
v1.1.0 两平台各有 23 项源码测试，GUI 证据检查覆盖 115 个步骤及 894 项记录参数。

v1.1.0 的真实数据目录中 22 个 QZA 与 14 个 QZV 全量通过，所有 action 记录与原解析器一致，
包括约 2.96 GB 的 demux-cutadapt.qza、多分支 taxonomy 和多输出 classifier。
校验采用源文件大小与修改时间的前后对照；未对数据区执行完整哈希或 CRC 扫描。
历史详细文件清单、统计与比较结果见
`archive/v1.1.0-validation/real-artifact-validation.json`。

技术文档：[Qt for Python](https://doc.qt.io/qtforpython-6/)、
[PyInstaller](https://pyinstaller.org/en/stable/usage.html)。第三方组件信息和许可证
见 `THIRD_PARTY_NOTICES.md` 与 `licenses/`。

### 默认完整参数与易读英文界面

界面全部采用英文。窗口启动时默认打开 **QIIME Parameters** 页。
详细模式始终启用，已移除 Verbose 按钮及复选框。每一步按依赖顺序显示
`action.yaml` 中的参数名与 JSON 值、执行 UUID 和 ZIP 内证据位置；
同一次执行的多个输出合并展示，空参数记录会明确说明。参数名与值保留原类型，
不推断未记录的默认值。**Evidence Chain** 步骤详情、**Full Report**、复制和
所有 GUI 导出均包含记录参数。

整体使用白色与深灰配色，选中状态及键盘焦点均有清晰灰阶反馈。
界面与参数文本采用 11 pt macOS 系统字体，纯文本报告及 YAML 采用
11 pt Menlo；不可用时使用系统等宽字体。参数表列标题加粗，不设置自定义底纹颜色。
离线 HTML 使用英文语言标记及易读的中性字体；证据值、文件名和原始 YAML
保留原来的语言。

应用包为 `QIIME2-Provenance-Studio-macOS-arm64-v1.2.0.zip`，
源码包为 `QIIME2-Provenance-Studio-macOS-source-v1.2.0.zip`。
原 v1.1.0 包及验证记录继续作为历史材料。Git 由项目所有者手动管理，
更新或构建应用后不会自动执行 Git 操作。
