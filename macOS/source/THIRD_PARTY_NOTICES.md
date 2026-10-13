# Third-party components

## English

This application uses unmodified, dynamically linked Python/Qt components.
The application sources and reproducible build scripts accompany the app.

- PySide6 Essentials / Shiboken6 6.11.2: Qt for Python, LGPL-3.0 or GPL-3.0 or commercial licensing. Source: https://code.qt.io/pyside/pyside-setup.git/
- Qt 6.11.2 (Core, Gui, Widgets, DBus and supporting platform/image plugins): LGPL-3.0/GPL-3.0/commercial, depending on component. Source: https://download.qt.io/official_releases/qt/6.11/6.11.2/submodules/
- PyYAML 6.0.3: MIT. Source: https://github.com/yaml/pyyaml
- CPython 3.12.14: PSF License Agreement. Source: https://www.python.org/downloads/source/
- PyInstaller 6.22.3 bootloader: GPL-2.0-or-later with the PyInstaller exception. Source: https://github.com/pyinstaller/pyinstaller

Qt libraries are distributed as separate shared libraries inside the macOS app bundle.
Replacement or debugging of those libraries is permitted under their applicable licenses;
rebuilding or replacing bundle contents may require a fresh local code signature.
Third-party license files are included under `licenses/` in the source distribution
and under `Contents/Resources/licenses/` in the app.

---

## 中文

本应用使用未经修改、动态链接的 Python/Qt 组件。
应用交付包含源码和可复现的构建脚本。

- PySide6 Essentials / Shiboken6 6.11.2：Qt for Python，采用 LGPL-3.0、GPL-3.0 或商业许可证。源码：https://code.qt.io/pyside/pyside-setup.git/
- Qt 6.11.2（Core、Gui、Widgets、DBus 以及配套的平台和图像插件）：根据组件采用 LGPL-3.0、GPL-3.0 或商业许可证。源码：https://download.qt.io/official_releases/qt/6.11/6.11.2/submodules/
- PyYAML 6.0.3：MIT 许可证。源码：https://github.com/yaml/pyyaml
- CPython 3.12.14：PSF License Agreement。源码：https://www.python.org/downloads/source/
- PyInstaller 6.22.3 bootloader：GPL-2.0-or-later，并附带 PyInstaller 例外条款。源码：https://github.com/pyinstaller/pyinstaller

Qt 库以独立共享库形式随 macOS 应用包分发。
各组件的适用许可证允许替换或调试这些库；重新构建或替换应用包内容后，
可能需要重新进行本地代码签名。
第三方许可证文件位于源码交付的 `licenses/` 目录，以及应用内的
`Contents/Resources/licenses/` 目录。
