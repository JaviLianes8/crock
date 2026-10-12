"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with CROCK_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("CROCK_E2E") != "1", reason="set CROCK_E2E=1 to build and install"
)

PROGRAM = """
import importlib.metadata, importlib.resources
import crock
from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

assert "site-packages" in crock.__file__, crock.__file__
assert importlib.metadata.version("crock") == crock.__version__
assert importlib.resources.files("crock").joinpath("py.typed").is_file()
assert sorted(crock.__all__) == sorted(
    ["CrockfordError", "decode", "decode_int", "encode", "encode_int", "normalize"]
)

assert encode_int(1234, check=True) == "16JD"
assert decode_int("16j-d", check=True) == 1234
assert encode_int(2**128 - 1) == "7ZZZZZZZZZZZZZZZZZZZZZZZZZ"
assert encode_int(1234, width=8, group=4) == "0000-016J"
assert encode(b"foobar") == "CSQPYRK1E8"
assert decode("csqpyrk1e8") == b"foobar"
assert decode(encode(bytearray(b"\\x00\\x01"), check=True), check=True) == b"\\x00\\x01"
assert normalize("ix-Lb-Ko") == "1X1BK0"
for bad, kwargs in [("CSQPYRK1E9", {}), ("0", {}), ("16JE", {"check": True})]:
    try:
        (decode_int if kwargs else decode)(bad, **kwargs)
    except CrockfordError as error:
        assert isinstance(error, ValueError)
    else:
        raise AssertionError(bad)
try:
    encode("text")
except TypeError:
    pass
else:
    raise AssertionError("str accepted")
big = 7**100000
assert decode_int(encode_int(big)) == big
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("crock-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["e2e ok"]
