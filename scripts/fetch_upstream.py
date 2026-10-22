"""Fetch the third-party files listed in tests/upstream/MANIFEST.json.

The files (the specification page, RFC 4648, the ULID specification and the base32-crockford
reference implementation with its tests) are not part of the repository. Their tests skip
until this script has fetched them; each download is checked against the size and sha256 in
the manifest. Entries named ``node:<package>`` are npm packages, installed with ``npm`` into
the same folder when ``npm`` is on the path; their tests skip without them.

    python scripts/fetch_upstream.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "tests" / "upstream"
MANIFEST = FOLDER / "MANIFEST.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failed = 0
    packages = []
    for name, entry in manifest.items():
        if name.startswith("node:"):
            packages.append(entry["npm"])
            continue
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "crock-tests"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != entry["size"] or digest != entry["sha256"]:
            print(f"{name}: got {len(body)} bytes, sha256 {digest}; manifest differs")
            failed += 1
            continue
        (FOLDER / name).write_bytes(body)
        print(f"{name}: ok")
    npm = shutil.which("npm")
    if npm is None:
        print("npm not found: the Node.js oracle tests will skip")
    elif packages:
        command = [npm, "install", "--no-save", "--no-package-lock", "--ignore-scripts"]
        done = subprocess.run([*command, "--prefix", str(FOLDER), *packages], check=False)
        failed += done.returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
