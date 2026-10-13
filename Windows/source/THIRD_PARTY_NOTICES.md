# Windows distribution: third-party components

## English

The app includes unmodified runtime binaries and matching application source.
The Qt package is reduced to Qt Widgets and the plugins used by this application.

- CPython 3.13.15 Windows x64 embedded distribution: PSF License Agreement.
  Source: https://www.python.org/downloads/source/
- PySide6 Essentials, Shiboken6 and Qt 6.8.3: LGPL-3.0/GPL-3.0/commercial as applicable.
  Sources: https://code.qt.io/pyside/pyside-setup.git/ and https://download.qt.io/official_releases/qt/6.8/6.8.3/submodules/
- PyYAML 6.0.3 and libyaml: MIT. Sources: https://github.com/yaml/pyyaml and https://github.com/yaml/libyaml
- Microsoft Visual C++ runtime DLLs: shipped with the official Python/Qt distributions;
  applicable Microsoft runtime redistribution terms apply.
- The native launcher is built using Zig 0.16.0 and its mingw-w64/MinGW runtime.
  Toolchain sources: https://ziglang.org/download/0.16.0/release-notes.html and https://www.mingw-w64.org/

License texts are in `licenses/`. The application source, C launcher and build scripts
are provided alongside the binary. Qt/Python shared libraries remain separate files;
replacement and debugging permitted by the corresponding licenses are not restricted.

Wine is used only for validation and is not included in the Windows application.
Zig and the test framework are development tools and are not included in the portable app.

---

## 中文

应用包含未修改的运行库二进制文件，并提供与之匹配的应用源码。
Qt 包仅保留 Qt Widgets 及本应用使用的插件。

- CPython 3.13.15 Windows x64 嵌入式发行包：PSF License Agreement。
  源码：https://www.python.org/downloads/source/
- PySide6 Essentials、Shiboken6 和 Qt 6.8.3：按适用情况采用 LGPL-3.0、GPL-3.0 或商业许可。
  源码：https://code.qt.io/pyside/pyside-setup.git/ 和 https://download.qt.io/official_releases/qt/6.8/6.8.3/submodules/
- PyYAML 6.0.3 和 libyaml：MIT 许可证。源码：https://github.com/yaml/pyyaml 和 https://github.com/yaml/libyaml
- Microsoft Visual C++ 运行库 DLL：随官方 Python/Qt 发行包提供；适用 Microsoft 运行库再分发条款。
- 原生启动器使用 Zig 0.16.0 及其 mingw-w64/MinGW 运行库构建。
  工具链来源：https://ziglang.org/download/0.16.0/release-notes.html 和 https://www.mingw-w64.org/

许可证全文位于 `licenses/`。应用源码、C 启动器和构建脚本与二进制程序一同提供。
Qt/Python 共享库保持为独立文件；相应许可证允许的替换与调试不受限制。

Wine 仅用于验证，不包含在 Windows 应用中。
Zig 和测试框架属于开发工具，不包含在便携应用中。
