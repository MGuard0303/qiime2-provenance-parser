"""Build a native PyInstaller distribution using the current OS and architecture."""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Build a relocatable app without QIIME 2; macOS builds use an .app bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--work", type=Path, default=Path("build"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination: Path = args.dist.resolve()
    work: Path = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    icon = root / "assets" / "app.icns"
    if sys.platform == "darwin" and not icon.exists():
        environment = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        subprocess.run(
            [sys.executable, str(root / "scripts" / "make_icon.py")], env=environment, check=True
        )
    icon_argument = repr(str(icon)) if sys.platform == "darwin" else "None"
    spec = work / "provenance.spec"
    # Explicitly bundle only the Qt Widgets modules used by the application.
    content = f"""
from PyInstaller.utils.hooks import copy_metadata
a = Analysis([{str(root / "launcher.py")!r}], pathex=[{str(root / "src")!r}],
    binaries=[], datas=[({str(root / "THIRD_PARTY_NOTICES.md")!r}, "."),
                       ({str(root / "licenses")!r}, "licenses")]
    + copy_metadata("PySide6_Essentials") + copy_metadata("shiboken6") + copy_metadata("PyYAML"),
    hiddenimports=[], hookspath=[], hooksconfig={{}}, runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtNetwork"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Provenance Studio",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    icon={icon_argument}, target_arch={platform.machine()!r}, codesign_identity=None)
collection = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Provenance Studio")
"""
    if sys.platform == "darwin":
        content += f"""
app = BUNDLE(collection, name="QIIME 2 Provenance Studio.app", icon={icon_argument},
    bundle_identifier="org.provenance-studio.qiime2", info_plist={{
        "CFBundleShortVersionString": "1.1.0", "CFBundleVersion": "1.1.0",
        "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "13.0",
        "CFBundleDocumentTypes": [{{"CFBundleTypeName": "QIIME 2 archive",
            "CFBundleTypeExtensions": ["qza", "qzv"], "CFBundleTypeRole": "Viewer",
            "LSHandlerRank": "Alternate"}}]
    }})
"""
    spec.write_text(content, encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(destination),
            "--workpath",
            str(work / "cache"),
            str(spec),
        ],
        check=True,
    )
    print(f"Built {platform.system()} {platform.machine()} application in {destination}")


if __name__ == "__main__":
    main()
