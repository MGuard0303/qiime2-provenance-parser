# QIIME 2 Provenance Studio v1.2.0

## English

### Purpose and maintenance location

This project reads provenance from local QIIME 2 `.qza` and `.qzv` archives. It
shows method evidence, input dependencies, execution UUIDs, original action YAML
and the recorded QIIME parameters for each step. The macOS desktop application
and the Windows portable application include their own runtime dependencies.
The source repository contains development files; executable packages and their
release evidence can be distributed through GitHub Releases.

### Complete local project layout

```text
qiime2-provenance-parser/
├── README.md                       Project overview and maintenance entry
├── AGENTS.md                       Instructions for future coding agents
├── LICENSE                         MIT license for project-owned code
├── .gitignore                      Source and generated-artifact boundaries
├── macOS/                          Current macOS arm64 v1.2.0 delivery
│   ├── source/                     Source, build scripts, tests and licenses
│   ├── QIIME 2 Provenance Studio.app
│   ├── QIIME2-Provenance-Studio-macOS-arm64-v1.2.0.zip
│   ├── USER_GUIDE.md
│   └── CHANGELOG.md
├── Windows/                        Current Windows x64 v1.2.0 delivery
│   ├── source/                     Source, native launcher and build scripts
│   ├── Provenance-Studio-Windows-x64/
│   ├── QIIME2-Provenance-Studio-Windows-x64-v1.2.0.zip
│   ├── USER_GUIDE.md
│   ├── CHANGELOG.md
│   └── archive/v1.0.0/             Original Windows delivery kept locally
├── docs/                           Generated local file inventory and audits
│   ├── file-inventory.json
│   └── copy-verification.json
└── tools/
    └── update_file_report.py        Regenerate the complete file-purpose report
```

The platform roots also retain source ZIPs, previews and historical validation
records. The local HTML file-purpose report is linked in the documentation section.

### Running the application

- On Apple Silicon macOS, open `macOS/QIIME 2 Provenance Studio.app`.
- On Windows, fully extract
  `Windows/QIIME2-Provenance-Studio-Windows-x64-v1.2.0.zip` and run
  `Provenance Studio.exe`. Keep its adjacent `app`, `runtime` and `licenses`
  directories together.
- Add or drop QZA/QZV files, then click **Parse All Files**. **QIIME Parameters**
  is the default tab and shows each execution's recorded names, JSON values, UUID
  and evidence ZIP member. Detailed mode is always enabled, with no Verbose
  toggle. **Evidence Chain**, **Full Report**, copying and all GUI exports include
  recorded parameters. Raw YAML remains complete.
- The interface is fully English, with white panels, dark-gray controls and
  grayscale selections and focus indicators. General text uses the native
  system font at 11 pt (Segoe UI on Windows); fixed-width evidence uses 11 pt
  Menlo on macOS or Consolas on Windows, with system fallbacks. Parameter-table
  headings are bold and have no custom fills or colors. Evidence values and
  original filenames retain their language.
- Packaged applications need no installed Python, conda or QIIME 2 environment.
  See the [macOS source guide](macOS/source/README.md) and
  [Windows source guide](Windows/source/README.md).

### Development and builds

Each platform's `source/` directory is editable source. The `.app`, portable
application, embedded runtimes and ZIPs are generated delivery artifacts. Start
with source changes, then rebuild the corresponding application and regenerate
its package and current checksums. Preserve third-party notices and licenses.

For macOS development, use a separate Python 3.12 environment. In
`macOS/source/`, use `environment.yml` or install the locked dependencies into
an appropriate independent environment:

```text
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m mypy src scripts launcher.py
python -m ruff check src scripts launcher.py
QT_QPA_PLATFORM=offscreen python -m pytest -q
python scripts/build_app.py --dist ../dist --work ../build
```

For Windows development, use a separate Python 3.13 environment. In
`Windows/source/`:

```text
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m mypy src scripts bootstrap.py
python -m ruff check src scripts bootstrap.py
python -m pytest -q
```

Windows packaging requires official embedded CPython, pinned Windows wheels and
Zig 0.16.0. `runtime-inputs.json` fixes the input URLs and SHA-256 values. Use a
new output directory that does not already exist:

```text
python scripts/download_runtime.py ../build-inputs
python scripts/build_windows.py --downloads ../build-inputs --wheels ../build-inputs/wheels --zig /path/to/zig --destination ../dist/Provenance-Studio-Windows-x64
```

These commands are maintenance instructions. Actual validation results are
recorded separately for each release; historical figures do not establish
acceptance of a newer application build. `scripts/validate_real.py` can compare external QZA/QZV
files against a separately supplied original parser. The scientific test archives
and the original single-file parser were not included in the migrated deliveries.

In the complete local checkout, when `tools/update_file_report.py` exists,
regenerate the local file-purpose guide using only the Python standard library.
This optional local tool is excluded from the minimal source repository:

```text
python tools/update_file_report.py
```

### Verification scope and licenses

#### Current v1.2.0 validation

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

Project-owned code is licensed under the [MIT License](LICENSE), with copyright
`Copyright (c) 2026 Lixuan Mu`. Third-party components retain their own licenses.

The tool reads provenance only. It does not execute QIIME 2 analyses or verify
the actual archives' data-payload integrity. Each platform retains third-party
component notices and license texts in `THIRD_PARTY_NOTICES.md` and `licenses/`.
Embedded dependencies also retain their own distribution metadata and licenses.

---

## 中文

本项目用于只读解析 QIIME 2 `.qza` / `.qzv` 文件中的 provenance，展示方法证据链、
输入关系、执行 UUID、原始 action YAML，以及各步骤记录的 QIIME 参数。
提供 macOS 桌面应用和 Windows 独立便携应用，均内置运行库。
源码仓库保留开发所需内容，可执行程序及配套验证证据通过 GitHub Releases 分发。

### 完整本地目录布局

```text
qiime2-provenance-parser/
├── README.md                       项目整体说明与维护入口
├── AGENTS.md                       后续维护位置与项目约定
├── LICENSE                         项目自有源码的 MIT 许可证
├── .gitignore                      源码仓库与本地生成产物的边界
├── macOS/                          macOS arm64 v1.2.0 的完整交付
│   ├── source/                     macOS 开发源码、构建脚本、测试及许可证
│   ├── QIIME 2 Provenance Studio.app
│   ├── QIIME2-Provenance-Studio-macOS-arm64-v1.2.0.zip
│   └── …                           源码 ZIP、使用说明、截图和历史验证记录
├── Windows/                        Windows x64 当前版本 v1.2.0
│   ├── source/                     Windows 开发源码、原生启动器和构建脚本
│   ├── Provenance-Studio-Windows-x64/
│   ├── QIIME2-Provenance-Studio-Windows-x64-v1.2.0.zip
│   ├── …                           源码 ZIP、使用说明、截图和历史验证记录
│   └── archive/v1.0.0/             指定 Windows-x64 旧目录的完整副本
├── docs/
│   ├── file-report.html            可搜索的逐文件用途报告
│   ├── file-inventory.json          与报告对应的全量文件及符号链接清单
│   └── copy-verification.json       迁入来源、逐项 SHA-256 / 链接目标核对
└── tools/
    └── update_file_report.py        重新生成逐文件报告与文件清单
```

### 使用程序

- macOS：打开 `macOS/QIIME 2 Provenance Studio.app`，适用于 Apple Silicon Mac。
- Windows：完整解压 `Windows/QIIME2-Provenance-Studio-Windows-x64-v1.2.0.zip`，
  双击其中的 `Provenance Studio.exe`。保留相邻的 `app`、`runtime` 和 `licenses` 目录。
- 拖入 QZA/QZV 后点击 **Parse All Files**。默认 **QIIME Parameters** 页按步骤
  显示参数名、JSON 值、执行 UUID 和 ZIP 内证据位置。完整详细模式始终启用，
  已移除 Verbose 切换控件。**Evidence Chain**、**Full Report**、复制和所有
  GUI 导出均包含记录参数，原始 YAML 保持完整。
- 界面全部采用英文，配色为白色面板、深灰控件及灰阶选中和焦点反馈。界面文本
  使用 11 pt 系统字体，Windows 优先 Segoe UI；等宽证据文本使用 11 pt macOS
  Menlo 或 Windows Consolas，不可用时使用系统字体。参数表列标题加粗，不设置
  自定义底纹或颜色；证据值与原始文件名保留原来的语言。
- 运行交付应用无需安装 Python、conda 或 QIIME 2。具体使用方法见
  [macOS 源码说明](macOS/source/README.md) 与 [Windows 源码说明](Windows/source/README.md)。

### 开发与构建

每个平台的 `source/` 是可修改源码；`.app`、便携目录、运行库和 ZIP 属于生成的交付物。
更新应从源码开始，随后重新构建相应平台的应用、压缩包和验证结果。

macOS 开发使用独立 Python 3.12 环境。进入 `macOS/source/` 后，可按其
`environment.yml` 创建环境，或在合适的独立环境执行：

```text
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m mypy src scripts launcher.py
python -m ruff check src scripts launcher.py
QT_QPA_PLATFORM=offscreen python -m pytest -q
python scripts/build_app.py --dist ../dist --work ../build
```

Windows 开发使用独立 Python 3.13 环境。进入 `Windows/source/` 后：

```text
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m mypy src scripts bootstrap.py
python -m ruff check src scripts bootstrap.py
python -m pytest -q
```

Windows 构建需要官方嵌入式 CPython、锁定的 Windows wheel 和 Zig 0.16.0。
构建输入由 `runtime-inputs.json` 锁定，构建目标使用尚不存在的新目录：

```text
python scripts/download_runtime.py ../build-inputs
python scripts/build_windows.py --downloads ../build-inputs --wheels ../build-inputs/wheels --zig /path/to/zig --destination ../dist/Provenance-Studio-Windows-x64
```

上述命令为维护参考；实际验证结果按发布版本单独记录，历史数字不作为新构建
已通过验收的结论。
`scripts/validate_real.py` 可用外部测试数据和指定的旧解析器进行兼容性比较；
QZA/QZV 测试数据与原始单文件解析器未随这两个交付目录迁入。

在完整本地项目中，`tools/update_file_report.py` 存在时可执行下面的命令刷新逐文件说明。
该可选本地工具只使用 Python 标准库，不纳入最小源码仓库：

```text
python tools/update_file_report.py
```

### 验证范围与许可证

#### 当前 v1.2.0 验证

- 两套当前源码测试各通过 **24 项**；两平台实现及辅助脚本的严格 mypy 和 Ruff
  检查均通过。
- Windows 交付运行库在 **Wine 11.0 / macOS arm64** 中使用 Windows Python 和 Qt，
  同样通过 **24 项测试**。尚未进行原生 Windows 电脑实机验证。
- 两平台解析器分别与旧解析器核对全部 **36 个真实 QZA/QZV 归档**。macOS GUI
  检查覆盖 **115 次执行及 894 项记录参数**，核对了界面显示与导出。
- 已在原生 macOS 检查独立应用窗口及英文文件选择对话框，核对默认参数显示、
  英文控件、字体可读性及灰阶外观。

项目自有源码采用 [MIT 许可证](LICENSE)，版权署名为 `Copyright (c) 2026 Lixuan Mu`。
第三方组件继续适用各自许可证。

本工具读取 provenance，不执行 QIIME 2 分析，也不校验真实归档数据区的完整性。
第三方组件声明与许可证分别保存在各平台的 `THIRD_PARTY_NOTICES.md` 和 `licenses/`
中；运行库还带有各依赖包的元数据与许可证文件。
