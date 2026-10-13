"""Assemble verified Windows wheels plus CPython's official embedded distribution.

This build runs on macOS/Linux/Windows with Zig. It does not cross-run PyInstaller.
Use the exact wheel/runtime hashes recorded alongside the distributed package.
"""

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path


def unpack(archive_path: Path, destination: Path) -> None:
    """Extract only safe relative members from a previously downloaded ZIP/wheel."""
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            target = destination / name
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError(f"Unsafe member: {name}")
        archive.extractall(destination)


def trim_qt(qt: Path) -> None:
    """Keep Qt Widgets and raster plugins; exclude unrelated optional modules.

    The Essentials wheel includes plugins referencing optional Addons libraries.
    None are needed for this application. Keeping an explicit module set avoids
    loading broken optional PDF/SVG plugins and reduces the portable package.
    """
    modules = {"QtCore.pyd", "QtGui.pyd", "QtWidgets.pyd", "QtTest.pyd"}
    libraries = {"Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll", "Qt6Test.dll"}
    for path in qt.iterdir():
        if path.suffix == ".pyd" and path.name not in modules:
            path.unlink()
        elif path.name.startswith("Qt6") and path.suffix == ".dll" and path.name not in libraries:
            path.unlink()
        elif path.suffix in {".exe", ".lib", ".pyi"}:
            path.unlink()
        elif path.name == "pyside6qml.abi3.dll":
            path.unlink()
    for name in ["qml", "include", "typesystems", "metatypes", "glue", "scripts", "doc"]:
        path = qt / name
        if path.is_dir():
            shutil.rmtree(path)
    plugins = qt / "plugins"
    for path in plugins.iterdir():
        if path.is_dir() and path.name not in {"platforms", "styles", "imageformats"}:
            shutil.rmtree(path)
    for path in (plugins / "imageformats").glob("*.dll"):
        if path.name not in {"qgif.dll", "qico.dll", "qjpeg.dll", "qwebp.dll"}:
            path.unlink()


def main() -> None:
    """Create a new Windows-x64 folder and compile its native GUI launcher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", required=True, type=Path)
    parser.add_argument("--wheels", required=True, type=Path)
    parser.add_argument("--zig", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    downloads: Path = args.downloads.resolve(strict=True)
    destination: Path = args.destination.resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite: {destination}")
    runtime = destination / "runtime"
    runtime.mkdir(parents=True)
    unpack(downloads / "python-embed-amd64.zip", runtime)
    wheels = sorted(args.wheels.resolve(strict=True).glob("*.whl"))
    if len(wheels) != 3 or any("win_amd64" not in wheel.name for wheel in wheels):
        raise ValueError("Expected three pinned Windows AMD64 runtime wheels.")
    expected: dict[str, str] = json.loads((source / "runtime-inputs.json").read_text())["sha256"]
    inputs = [downloads / "python-embed-amd64.zip", *wheels]
    for item in inputs:
        if hashlib.sha256(item.read_bytes()).hexdigest() != expected.get(item.name):
            raise ValueError(f"Runtime input hash mismatch: {item.name}")
    for wheel in wheels:
        unpack(wheel, runtime / "site-packages")
    trim_qt(runtime / "site-packages/PySide6")
    (runtime / "python313._pth").write_text(
        "python313.zip\n.\nsite-packages\n../app\nimport site\n", encoding="utf-8"
    )
    app = destination / "app"
    shutil.copytree(
        source / "src/qiime2_provenance",
        app / "qiime2_provenance",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy2(source / "bootstrap.py", app / "bootstrap.py")
    shutil.copytree(source / "assets", app / "assets")
    shutil.copytree(source / "licenses", destination / "licenses")
    shutil.copy2(runtime / "LICENSE.txt", destination / "licenses/CPython-LICENSE.txt")
    shutil.copy2(source / "THIRD_PARTY_NOTICES.md", destination / "THIRD_PARTY_NOTICES.md")

    # PNG-in-ICO is supported by Windows Vista and later; preserve the artwork.
    png = (source / "assets/app.png").read_bytes()
    icon = app / "assets/app.ico"
    icon.write_bytes(
        struct.pack("<HHH", 0, 1, 1)
        + struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
        + png
    )
    resources = destination.parent / "launcher.rc"
    resource_output = destination.parent / "launcher.res"
    resources.write_text(
        f'1 ICON "{icon.as_posix()}"\n'
        f'1 24 "{(source / "native/app.manifest").as_posix()}"\n'
        "1 VERSIONINFO\nFILEVERSION 1,2,0,0\nPRODUCTVERSION 1,2,0,0\n"
        'FILEOS 0x40004\nFILETYPE 1\nBEGIN\nBLOCK "StringFileInfo"\nBEGIN\n'
        'BLOCK "040904B0"\nBEGIN\n'
        'VALUE "FileDescription", "QIIME 2 Provenance Studio\\0"\n'
        'VALUE "ProductName", "QIIME 2 Provenance Studio\\0"\n'
        'VALUE "FileVersion", "1.2.0\\0"\nEND\nEND\n'
        'BLOCK "VarFileInfo"\nBEGIN\nVALUE "Translation", 0x0409, 1200\nEND\nEND\n',
        encoding="utf-8",
    )
    subprocess.run([str(args.zig), "rc", "/fo", str(resource_output), str(resources)], check=True)
    subprocess.run(
        [
            str(args.zig),
            "cc",
            "-target",
            "x86_64-windows-gnu",
            "-O2",
            "-municode",
            "-Wl,--subsystem,windows",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(source / "native/launcher.c"),
            str(resource_output),
            "-lshell32",
            "-luser32",
            "-o",
            str(destination / "Provenance Studio.exe"),
        ],
        check=True,
    )
    manifest = {
        "platform": "Windows-x64",
        "app_version": "1.2.0",
        "python": (downloads / "python-version.txt").read_text().strip(),
        "method": "Official embedded CPython + Windows wheels + native Unicode GUI launcher",
        "inputs": [
            {"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in [downloads / "python-embed-amd64.zip", *wheels]
        ],
    }
    (destination / "BUILD.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built: {destination}")


if __name__ == "__main__":
    main()
