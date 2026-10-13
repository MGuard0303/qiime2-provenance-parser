"""Download the exact official runtime files pinned in runtime-inputs.json."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def main() -> None:
    """Fetch pinned files over HTTPS and verify each SHA-256 before use."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / "runtime-inputs.json").read_text(encoding="utf-8"))
    hashes: dict[str, str] = metadata["sha256"]
    urls: dict[str, str] = metadata["urls"]
    destination: Path = args.destination.resolve()
    (destination / "wheels").mkdir(parents=True, exist_ok=True)
    for name, expected in hashes.items():
        target = destination / "wheels" / name if name.endswith(".whl") else destination / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            continue
        with urlopen(urls[name], timeout=120) as response:
            data: bytes = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Download checksum mismatch: {name}")
        target.write_bytes(data)
        print(f"Verified: {name}")
    (destination / "python-version.txt").write_text(metadata["python_version"], encoding="utf-8")


if __name__ == "__main__":
    main()
