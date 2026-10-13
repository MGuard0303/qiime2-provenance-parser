"""Start the portable Windows app and expose startup failures as a local dialog."""

from __future__ import annotations

import ctypes
import os
import sys
import traceback
from pathlib import Path


def main() -> int:
    """Configure bundled plugins before Qt loads, then enter the desktop app."""
    root = Path(__file__).resolve().parent.parent
    # Keep Qt plugin discovery independent of other Qt/Python installations.
    os.environ["QT_PLUGIN_PATH"] = str(root / "runtime/site-packages/PySide6/plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(
        root / "runtime/site-packages/PySide6/plugins/platforms"
    )
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
            from qiime2_provenance.windows_check import main as check

            return check(sys.argv[2:])
        from qiime2_provenance.app import main as start

        return start()
    except Exception:
        message = traceback.format_exc()
        try:
            destination = (
                Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "QIIME2ProvenanceStudio"
            )
            destination.mkdir(parents=True, exist_ok=True)
            log = destination / "startup-error.log"
            log.write_text(message, encoding="utf-8")
            message += f"\nError log: {log}"
        except OSError:
            pass
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(
                None, message, "Provenance Studio · Startup error", 0x10
            )
        else:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
