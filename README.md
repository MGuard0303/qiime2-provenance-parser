# QIIME 2 Provenance Studio v1.2.0

## English

### Purpose and maintenance location

This project reads provenance from local QIIME 2 `.qza` and `.qzv` archives. It
shows method evidence, input dependencies, execution UUIDs, original action YAML
and the recorded QIIME parameters for each step. The macOS desktop application
and the Windows portable application include their own runtime dependencies.
The source repository contains development files; executable packages and their
release evidence can be distributed through GitHub Releases. A source-only clone
requires a separate release download or a local build to run a packaged app.

**Since 2026-10-09, all maintenance takes place in this project root:**

```text
/Users/lixuanmu/projects/qiime2-provenance-parser/
```

Edit source, maintain documentation, build applications and save new validation
records here. Use `macOS/source/` for macOS and `Windows/source/` for the current
Windows version. Keep the two platform deliveries separate. Changes to shared
parsing or GUI behavior require checking the corresponding implementation on
both platforms. The previous Codex outputs and Storage3 directories are
historical sources; future updates are not synchronized back to those locations.
The project owner manages Git manually. Application updates, builds and
validation never run Git commands automatically, including status, diff, add,
commit, tag, fetch, pull, push, initialization or remote changes.

### Complete local project layout

```text
qiime2-provenance-parser/
├── README.md                       Project overview and maintenance entry
├── AGENTS.md                       Instructions for future coding agents
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

### Versions, migration and documentation history

The following describes migration history, before the v1.2.0 update.
The 2026-10-09 migration copied the original content, including hidden files,
development caches and internal macOS application symlinks:

1. `macOS/` came from `outputs/macOS-arm64-v1.1.0/`, containing v1.1.0 at migration.
2. `Windows/archive/v1.0.0/` came from the explicitly requested
   `outputs/Windows-x64/` and retained the v1.0.0 source, application, ZIPs and
   original delivery evidence.
3. `Windows/` additionally came from `outputs/Windows-x64-v1.1.0/`. That
   historical v1.1.0 release introduced the optional Verbose parameter page.

Current macOS and Windows maintenance uses v1.2.0, whose detailed parameters are
always enabled. The v1.1.0 ZIPs and their validation records remain historical;
`Windows/archive/v1.0.0/` is unchanged. Current source packages are
`macOS/QIIME2-Provenance-Studio-macOS-source-v1.2.0.zip` and
`Windows/QIIME2-Provenance-Studio-Windows-source-v1.2.0.zip`.

On **2026-10-13**, all 19 filesystem Markdown files were normalized to English
filenames and complete bilingual text, with English first and Chinese second.
This includes ignored archives and bundled documentation. At that documentation-only step, application behavior
and version numbers were unchanged; affected packaging, resource
signatures and checksums are refreshed to reflect the documentation changes.
Markdown files inside the release ZIPs are synchronized with the revised copies.

Current `macOS/build-validation.json` and `Windows/build-validation.json`
summarize v1.2.0. Detailed platform-root records cover current source tests,
standalone runtime acceptance, real-archive comparison and interface checks.
`macOS/archive/v1.1.0-validation/` and
`Windows/archive/v1.1.0-validation/` retain snapshots of older JSON/XML evidence,
which may contain historical absolute paths. Older hashes and ZIP sizes describe
their original build, rather than this release. The local
`docs/copy-verification.json` records the migration-time copy. Documentation and
package checks remain separate from functional results. This README and
AGENTS.md define the current maintenance entry points.

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

### Minimal source repository for GitHub

The root `.gitignore` now uses an allowlist. The maintained GitHub repository
contains the root guidance and the two current platform source trees. The full
local directory retains release packages and maintenance records separately.

Keep these files in Git:

- Root `README.md`, `AGENTS.md` and `.gitignore`. A project-owned root `LICENSE`
  or `LICENSE.*` file is also allowed if one is added later.
- The two source packages, launchers, Windows native launcher/manifest, build and
  validation scripts, and the existing automated tests.
- Both `pyproject.toml` files, environment definitions, requirements and lock
  files, and Windows `runtime-inputs.json`. These retain reproducible dependency
  and runtime-download configuration.
- Each source README, `THIRD_PARTY_NOTICES.md` and all source license texts.
- `Windows/source/assets/app.png`, required by the GUI and Windows icon builder.

Keep these local and ignored:

- Platform-root `USER_GUIDE.md` files, which duplicate the source READMEs;
  release-specific `CHANGELOG.md` files and interface previews.
- Packaged applications, embedded runtimes, ZIPs, historical archives, release
  checksums and generated validation records.
- The local `tools/` file-inventory helper and generated `docs/` reports. They
  describe a complete local delivery and are not required to run, build or test
  the application from its source-only repository.
- `macOS/source/assets/app.icns` and `assets/app.iconset/`. On macOS,
  `build_app.py` automatically calls `make_icon.py` when the ICNS is absent; the
  generator creates the missing directories and complete icon set.
- `Windows/source/assets/app.ico`. The Windows builder recreates it from the
  tracked `app.png` on every build.
- Caches, local environments, generated/downloaded build inputs, operating-system
  metadata and external scientific datasets.

Add a new required root area or CI workflow to the allowlist explicitly before
committing it. Tests and third-party license notices remain in the minimal set
so the two platforms can continue to be maintained and built independently.
The rules do not delete local files. Git initialization, commits and uploads
remain under the project owner's control. Ignore rules do not remove files
already tracked by Git; see the [Git documentation](https://git-scm.com/docs/gitignore).

Executable ZIPs and their matching validation/checksum assets can be distributed
through [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
Future version history belongs in source commits and tags.

The complete local checkout still provides `tools/update_file_report.py` and
`docs/file-report.html`. Run the report generator when the local tool exists;
a source-only clone does not include or depend on it. The local report covers
all files and symlinks, including ignored deliveries, without expanding ZIP
members. Source-only users can follow the retained platform source READMEs for
running, building and testing instructions.

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

The platform-root `build-validation.json` summarizes current v1.2.0 acceptance.
Individual runtime, native-interface, real-archive and source-test records keep
the detailed evidence. `archive/v1.1.0-validation/` contains snapshots of earlier
records; its results are historical and do not describe this new build.

The historical v1.1.0 delivery records show 23 tests per platform and comparisons
against 36 real QZA/QZV archives, with GUI checks covering 115 steps and 894
recorded parameters. These figures describe v1.1.0 and are not claims of
v1.2.0 acceptance; current validation is stored independently in each platform
delivery directory. Windows runtime acceptance used Wine 11.0 on
macOS arm64; native Windows hardware testing remains pending. The migration
verified copied content, symlinks and the macOS signature. Documentation checks
and archive checks are kept separate from those historical functional results.

The tool reads provenance only. It does not execute QIIME 2 analyses or verify
the actual archives' data-payload integrity. Each platform retains third-party
component notices and license texts in `THIRD_PARTY_NOTICES.md` and `licenses/`.
Embedded dependencies also retain their own distribution metadata and licenses.

---

## 中文

本项目用于只读解析 QIIME 2 `.qza` / `.qzv` 文件中的 provenance，展示方法证据链、
输入关系、执行 UUID、原始 action YAML，以及各步骤记录的 QIIME 参数。
提供 macOS 桌面应用和 Windows 独立便携应用，均内置运行库。
源码仓库保留开发所需内容，可执行程序及配套验证证据通过 GitHub Releases 分发；
本地已有应用的路径如下，直接克隆源码仓库后需要另行下载发布包或自行构建。

**从 2026-10-09 起，本程序的维护根目录为：**

```text
/Users/lixuanmu/projects/qiime2-provenance-parser/
```

以后在本目录下修改源码、维护说明、构建和保存验证结果。日常开发入口为
`macOS/source/` 与 `Windows/source/`。两者分别构建和交付；公共解析逻辑发生修改时，
应同步检查两平台对应实现。旧 Codex outputs 和 Storage3 项目目录作为历史来源，
后续不再向这些旧位置同步更新。Git 由项目所有者手动管理。应用更新、构建和验证
均不自动执行任何 Git 命令，包括状态、差异、暂存、提交、标签、拉取、推送、
初始化仓库或修改远程。

### 完整本地目录布局

```text
qiime2-provenance-parser/
├── README.md                       项目整体说明与维护入口
├── AGENTS.md                       后续维护位置与项目约定
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

### 版本与迁入来源

以下为 v1.2.0 更新之前的迁入历史。2026-10-09 的迁入保持了来源文件原内容，包含隐藏文件、开发缓存和 macOS 应用内部符号链接。

2026-10-13 对项目全部 19 个文件系统 Markdown 文件统一采用英文命名和英文在前、
中文在后的完整双语内容，包含旧版归档及应用内说明副本。当时的文档整理保持程序行为和版本号；
受影响的交付压缩包、资源签名及校验清单同步更新，ZIP 内 Markdown 与修订后的副本一致。

1. `macOS/` 完整复制自原 `outputs/macOS-arm64-v1.1.0/`，迁入时版本为 v1.1.0。
2. `Windows/archive/v1.0.0/` 完整复制自本次指定的 `outputs/Windows-x64/`。
   该目录为 v1.0.0，保留其原源码、应用、压缩包和说明。
3. `Windows/` 另外收录原 `outputs/Windows-x64-v1.1.0/`，该历史版本新增
   可选择开启的 Verbose 参数页。

当前两平台维护版本为 v1.2.0，完整参数默认常开。v1.1.0 ZIP 及对应验证记录
继续作为历史材料，`Windows/archive/v1.0.0/` 不变。当前源码包为
`macOS/QIIME2-Provenance-Studio-macOS-source-v1.2.0.zip` 和
`Windows/QIIME2-Provenance-Studio-Windows-source-v1.2.0.zip`。

当前 `macOS/build-validation.json` 和 `Windows/build-validation.json` 汇总 v1.2.0。
平台根目录详细记录覆盖当前源码测试、独立运行库验收、真实归档核对和界面检查。
`macOS/archive/v1.1.0-validation/` 与 `Windows/archive/v1.1.0-validation/`
保留旧 JSON/XML 证据快照，可能含历史绝对路径；旧哈希和 ZIP 大小描述原构建，
不描述当前发布。本地 `docs/copy-verification.json` 记录迁入时的复制关系。
文档与包检查和功能结果分别记录，本 README 与 AGENTS.md 定义当前维护入口。

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

### GitHub 最小源码集合

项目根目录的 `.gitignore` 采用白名单：GitHub 保留根目录维护说明和两平台当前源码，
完整本地目录继续保存发布包及维护记录。

保留在 Git 中：

- 根目录 `README.md`、`AGENTS.md` 和 `.gitignore`。以后新增自有源码的根目录
  `LICENSE` 或 `LICENSE.*` 文件时，也允许提交。
- 两平台源码包、启动入口、Windows 原生启动器及 manifest、构建与验证脚本、现有自动测试。
- 两套 `pyproject.toml`、环境定义、requirements 及锁定文件，以及 Windows 的
  `runtime-inputs.json`，保证依赖和运行库下载配置可复现。
- 两平台源码 README、`THIRD_PARTY_NOTICES.md` 和全部源码许可证文本。
- `Windows/source/assets/app.png`，GUI 和 Windows 图标生成依赖该文件。

留在本地并忽略：

- 与源码 README 重复的平台外层 `USER_GUIDE.md`、版本发布说明 `CHANGELOG.md` 和预览截图。
- 应用包、内置运行库、ZIP、历史版本、发布校验清单及生成的验证记录。
- 本地 `tools/` 文件清单工具和 `docs/` 生成报告。这些材料描述完整本地交付，
  不属于从纯源码仓库运行、构建和测试程序的必要文件。
- `macOS/source/assets/app.icns` 及 `assets/app.iconset/`。macOS 的 `build_app.py`
  在 ICNS 缺失时自动调用 `make_icon.py`，后者会创建缺失目录及完整图标集。
- `Windows/source/assets/app.ico`。Windows 构建器每次都从保留的 `app.png` 重新生成。
- 缓存、本地环境、构建或下载产物、系统元数据及外部科学数据。

新增必需的根目录区域或 CI 工作流时，应先明确扩展白名单。保留测试和第三方许可说明，
使两个平台仍可独立维护和构建。规则不会删除本地文件，Git 初始化、提交及上传继续由
项目所有者管理。忽略规则不会自动移除已被 Git 跟踪的文件，参见
[Git 官方说明](https://git-scm.com/docs/gitignore)。

可执行 ZIP 与配套验证、校验文件可通过
[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
分发，后续版本历史由源码提交和标签记录。

完整本地项目仍保留 `tools/update_file_report.py` 和 `docs/file-report.html`。
本地工具存在时可以运行它刷新报告；纯源码克隆不包含也不依赖该工具。报告覆盖全部本地
文件和符号链接，包括被忽略的交付物，并按容器说明 ZIP。纯源码使用者可依照保留的
两平台源码 README 运行、构建和测试程序。

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

平台根目录 `build-validation.json` 汇总当前 v1.2.0 验收结果，各运行库、原生界面、
真实归档及源码测试记录保留详细证据。`archive/v1.1.0-validation/` 存放旧记录快照，
这些材料属于历史结果，不描述当前构建。

历史 v1.1.0 交付记录两平台各通过 23 项测试，并核对 36 个真实 QZA/QZV，
GUI 检查覆盖 115 个步骤及 894 项记录参数。以上数字描述 v1.1.0，
不作为 v1.2.0 已完成验收的结论；当前验证记录在各平台交付目录独立保存。
Windows 的运行验收环境为 Wine 11.0 / macOS arm64，原生 Windows 实机验证仍待完成。
本次迁移的核验是复制内容、符号链接和 macOS 签名完整性的检查，不将历史测试
表述为在新目录重新执行的测试。

本工具读取 provenance，不执行 QIIME 2 分析，也不校验真实归档数据区的完整性。
第三方组件声明与许可证分别保存在各平台的 `THIRD_PARTY_NOTICES.md` 和 `licenses/`
中；运行库还带有各依赖包的元数据与许可证文件。
