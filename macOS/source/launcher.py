"""Absolute-import entry point used by PyInstaller on each target platform."""

from qiime2_provenance.app import main

if __name__ == "__main__":
    raise SystemExit(main())
