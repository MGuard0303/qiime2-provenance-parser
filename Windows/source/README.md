# QIIME 2 Provenance Studio — Windows x64

## English

This is a standalone portable Windows distribution. Its interface, source,
runtime, and build files are stored in the dedicated Windows directory. The app
does not depend on the macOS application. The target is **Windows 10 version
1809 or later / Windows 11 on Intel or AMD 64-bit processors**. Running the x64
app through emulation on Windows ARM64 has not been verified; 32-bit Windows is
not supported.

### Run the portable app

1. Extract the complete `QIIME2-Provenance-Studio-Windows-x64-v1.1.0.zip` into a local folder.
2. Double-click **`Provenance Studio.exe`** in the extracted folder.
3. Drag in `.qza` / `.qzv` files and click “解析全部文件” (Parse all files).

Python, conda, QIIME 2, Qt, and the Visual C++ runtime do not need to be installed;
the required components are bundled. No administrator privileges or internet
connection are required. Keep the adjacent `runtime`, `app`, `licenses`, and
other folders together. Copying only the EXE is insufficient; extract the
archive before running the app instead of using the archive preview window.

The current EXE has no commercial code signature, so Windows may display
“Unknown publisher.” Check the delivery's SHA-256 checksum first and handle
system prompts according to your organization's software policy. Disabling
system security features is unnecessary.

### View parameters with Verbose

Select “Verbose：显示 QIIME 参数” (Verbose: show QIIME parameters) on the left.
The “QIIME 参数” (QIIME parameters) tab opens automatically on the right.
For each step, it lists the parameter names and values recorded in `action.yaml`,
the execution UUID, and the evidence location in provenance-chain order.
Multiple outputs from the same execution are displayed once. Step details in
the provenance chain, the complete report, copied results, and exports also
include parameters. Raw YAML remains complete at all times. Parameter values
retain their original types; unrecorded defaults are not added. Clearing the
checkbox hides parameters from ordinary reports and exports.

### Interface and features

Controls are at the upper left, the file list and drop area are at the lower
left, and parsed results are on the right. The app supports batch loading,
duplicate-path removal, background parsing, parameter display, navigation to
upstream UUIDs, complete-report search, raw YAML inspection, copying results,
and TXT / JSON / HTML export.

- `Ctrl+O` adds files; `Ctrl+S` exports the current report.
- Parsing errors appear under the affected file; processing continues for other files.
- “停止” (Stop) takes effect after the current archive finishes. Closing the window waits for the background thread to exit safely.
- “Verbose：显示 QIIME 参数” affects step details, the complete report, copying, and exports; raw YAML always remains complete.
- Exported JSON includes source paths. Review path information as needed before sharing a report.

### Runtime and technology

- Official CPython **3.13.15** Windows x64 embedded distribution.
- PySide6 Essentials / Qt **6.8.3** and Shiboken6 **6.8.3**.
- PyYAML **6.0.3**.
- A Win32 Unicode GUI launcher of approximately 200 KiB that loads the bundled Python DLL in the same process.

The launcher starts Python in isolated mode. It does not depend on a system
Python installation, user site-packages, `PYTHONPATH`, or conda. Qt plugin paths
point to the application's own files. The app uses the Windows platform plugin
and Segoe UI / Consolas fonts. Required Qt Widgets and Visual C++ DLLs are
included. The original light, simple layout and high-DPI support are retained.

Packaging uses the official embedded Python distribution, official Windows
wheels, and a native launcher compiled with Zig 0.16.0. This approach can assemble
a genuine Windows PE executable on macOS. This delivery does not use
cross-platform PyInstaller. See the [official embedded-distribution documentation](https://docs.python.org/3.13/using/windows.html#the-embeddable-package).

### Source and build

`src/qiime2_provenance/` contains the application and parser core,
`native/launcher.c` is the native launcher, and `bootstrap.py` configures plugin
paths and handles startup errors. All Python application files and helper
scripts have type annotations and use `mypy --strict`. The C launcher is
compiled with `-Wall -Wextra -Werror`.

Running the delivered EXE requires no new environment. For development, create
an independent environment with `environment.yml`, or install
`requirements-dev.txt` in a Python 3.13 environment and run
`pip install --no-deps -e .`.

For a reproducible build, install official Zig 0.16.0 beforehand and replace
the placeholder below with its actual path:

```text
python scripts/download_runtime.py downloads
python scripts/build_windows.py --downloads downloads --wheels downloads/wheels --zig /path/to/zig --destination dist/Provenance-Studio-Windows-x64
```

`runtime-inputs.json` pins all runtime URLs, filenames, and SHA-256 hashes.
Both the downloader and builder verify hashes. The build destination must be a
new directory to avoid overwriting an existing delivery. The builder keeps only
the Qt Widgets components and image plugins needed by the app; third-party
binaries themselves are not modified.

```text
python -m mypy src scripts bootstrap.py
python -m ruff check src scripts bootstrap.py
python -m pytest -q
```

The app provides an explicitly enabled acceptance-test entry point. A normal
double-click does not run tests:

```text
"Provenance Studio.exe" --self-test "C:\Temp\validation.json" --environment "Windows 11 x64"
```

Add `--data-root "D:\data\ds-20200228"` to scan real QZA/QZV files, or add
`--screenshot "C:\Temp\preview.png"` to save the acceptance-test interface.
The output path's parent directory must already exist.

### Completed validation and limits

At the original delivery, the Windows EXE passed runtime validation under Wine 11.0 on macOS Apple Silicon,
loading Windows Python, Windows Qt DLLs, and the `windows` platform plugin.
Acceptance checks covered Chinese characters and spaces in paths, drag-and-drop
events, background parsing, error isolation, parameter toggling, UTF-8 exports,
search, and file removal. All **22 QZA and 14 QZV** files in the provided data
directory were parsed successfully.

Detailed results are in the delivery's validation JSON files. **There are
currently no test results from a native Windows computer.** Wine acceptance
does not establish certification on physical Windows 10/11 machines. The
interface preview also explicitly identifies the Wine environment.

The parser retains evidence for every artifact and topologically sorts the
reachable input graph. Multiple outputs from the same execution are merged in
the step list; the complete report still retains each artifact and its input
relationships. Missing ancestor records produce UUID warnings. Cycles,
duplicate ZIP members, duplicate YAML keys, and invalid structures produce
errors. Each metadata YAML file is limited to 8 MiB; action YAML files are
limited to 64 MiB in total.

The tool only reads provenance. It does not execute QIIME 2 commands or verify
checksums in the archive's `data` area. The original parser and macOS delivery
remain independent. Component information and license texts are in
`THIRD_PARTY_NOTICES.md` and `licenses/`.

---

## 中文

Windows 独立便携版。界面、源码、运行库与构建文件全部位于 Windows 专用目录，
不依赖 macOS 应用。目标为 **Windows 10 1809 及以上 / Windows 11，Intel 或 AMD 64 位**。
Windows ARM64 的 x64 模拟运行未验证，32 位 Windows 不支持。

### 开箱即用

1. 将 `QIIME2-Provenance-Studio-Windows-x64-v1.1.0.zip` 完整解压到本地文件夹。
2. 双击解压目录中的 **`Provenance Studio.exe`**。
3. 拖入 `.qza` / `.qzv`，点击「解析全部文件」。

无需安装 Python、conda、QIIME 2、Qt 或 Visual C++ 运行库；程序内置所需组件。
无需管理员权限，也无需联网。请保留 `runtime`、`app`、`licenses` 等相邻目录，
不要只拷贝 EXE，也不要在压缩包预览窗口里直接运行。

当前 EXE 未做商业代码签名，Windows 可能显示“未知发布者”。应先核对本交付的
SHA-256，按所在单位的软件使用规则处理系统提示，无需关闭系统安全功能。

### Verbose 参数查看

勾选左侧「Verbose：显示 QIIME 参数」，右侧自动打开「QIIME 参数」页。
每一步按证据链顺序列出 action.yaml 中的参数名、值、执行 UUID 和证据位置；
同一次执行的多个输出只展示一次。证据链中的步骤详情、完整报告、复制和导出
也同步显示参数。原始 YAML 始终完整。参数值保留原类型，不补写未记录的默认值。
取消勾选后，普通报告及导出隐藏参数。

### 界面与功能

左上为控制区，左下为文件列表及拖拽区，右侧为解析结果。
支持批量加载、重复路径去重、后台解析、参数显示、上游 UUID 跳转、完整报告搜索、
原始 YAML 查看、复制结果，以及 TXT / JSON / HTML 导出。

- `Ctrl+O` 添加文件，`Ctrl+S` 导出当前报告。
- 解析失败会显示在对应文件下，其他文件继续处理。
- 「停止」在当前归档完成后生效；关闭窗口会等待后台线程安全退出。
- 「Verbose：显示 QIIME 参数」影响步骤详情、完整报告、复制与导出；原始 YAML 始终完整。
- 导出 JSON 包含源路径，请在分享报告前按实际需要处理路径信息。

### 运行时与技术栈

- CPython **3.13.15** 官方 Windows x64 嵌入式发行包。
- PySide6 Essentials / Qt **6.8.3** 和 Shiboken6 **6.8.3**。
- PyYAML **6.0.3**。
- 一个约 200 KiB 的 Win32 Unicode GUI 启动器，在同一进程加载内置 Python DLL。

启动器以 Python 隔离模式启动，不依赖电脑已有 Python、用户 site-packages、
`PYTHONPATH` 或 conda。Qt 插件路径指向应用自身，使用 Windows 平台插件和
Segoe UI / Consolas 字体。Qt Widgets 所需 DLL 和 Visual C++ DLL 随包提供。
保留了原版浅色、简洁布局与高 DPI 支持。

打包采用官方嵌入式 Python、官方 Windows wheel 和 Zig 0.16.0 编译的原生启动器。
该方法可在 macOS 组装真正的 Windows PE 可执行程序；本交付未使用跨平台 PyInstaller。
[官方嵌入式发行包说明](https://docs.python.org/3.13/using/windows.html#the-embeddable-package)。

### 源码与构建

`src/qiime2_provenance/` 为应用及解析内核，`native/launcher.c` 为原生启动器，
`bootstrap.py` 设置插件路径并处理启动错误。所有 Python 应用和辅助脚本均有
类型标注，使用 `mypy --strict`；C 启动器使用 `-Wall -Wextra -Werror` 编译。

只运行交付 EXE 时无需创建环境。开发时可以使用 `environment.yml` 创建独立环境，
或在 Python 3.13 环境安装 `requirements-dev.txt` 后执行 `pip install --no-deps -e .`。

可复现构建（预先安装官方 Zig 0.16.0，并将下方路径改为其实际位置）：

```text
python scripts/download_runtime.py downloads
python scripts/build_windows.py --downloads downloads --wheels downloads/wheels --zig /path/to/zig --destination dist/Provenance-Studio-Windows-x64
```

`runtime-inputs.json` 锁定全部运行库 URL、文件名与 SHA-256。
下载器和构建器都会校验哈希。构建目标必须是新目录，避免覆盖已有交付。
构建器仅保留应用所需的 Qt Widgets 组件和图像插件，第三方二进制本身不做修改。

```text
python -m mypy src scripts bootstrap.py
python -m ruff check src scripts bootstrap.py
python -m pytest -q
```

应用内置一个显式启用的验收入口，平时双击不会运行测试：

```text
"Provenance Studio.exe" --self-test "C:\Temp\validation.json" --environment "Windows 11 x64"
```

可追加 `--data-root "D:\data\ds-20200228"` 扫描真实 QZA/QZV，或追加
`--screenshot "C:\Temp\preview.png"` 保存验收界面。输出路径的父文件夹需存在。

### 已执行的验证与边界

原交付验收时，Windows EXE 已通过 Wine 11.0 / macOS Apple Silicon 下的运行验证，实际加载
Windows Python、Windows Qt DLL 与 `windows` 平台插件。验收覆盖中文及空格路径、
拖拽事件、后台解析、错误隔离、参数切换、UTF-8 导出、搜索与文件移除。
已成功解析提供的数据目录中全部 **22 个 QZA 和 14 个 QZV**。

详细测试结果见交付目录的验证 JSON。**当前没有原生 Windows 电脑实机测试结果**；
Wine 验收不能等同于 Windows 10/11 实机认证。界面预览也明确标为 Wine 环境。

解析内核保留每个 artifact 的证据，按可达输入图拓扑排序；同一次 execution 的多个
输出在步骤列表合并，完整报告仍保留各 artifact 和输入关系。缺失祖先记录会提示 UUID，
循环依赖、重复 ZIP 成员、重复 YAML 键和非法结构会报错。单个元数据 YAML 上限 8 MiB，
action YAML 总量上限 64 MiB。

工具仅读取 provenance；不执行 QIIME 2 命令，也不验证归档 data 区校验和。
原始解析器和 macOS 交付保持独立。组件说明与许可证见 `THIRD_PARTY_NOTICES.md`
和 `licenses/`。
