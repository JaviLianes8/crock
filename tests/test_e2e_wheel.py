"""Build the wheel and sdist, inspect them, install the wheel in a throwaway venv and use it.

Slow and needs the build backend, so it runs only with CROCK_E2E=1. crock has no command
line tool, so the installed package is driven by a consumer program run as a subprocess.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("CROCK_E2E") != "1", reason="set CROCK_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources, pickle
import crock
from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

assert "site-packages" in crock.__file__, crock.__file__
assert crock.__version__ == "1.0.0"
assert importlib.metadata.version("crock") == crock.__version__
assert importlib.resources.files("crock").joinpath("py.typed").is_file()
public = sorted(name for name in vars(crock) if not name.startswith("_"))
assert public == sorted(crock.__all__) == sorted(
    ["CrockfordError", "decode", "decode_int", "encode", "encode_int", "normalize"]
), public

assert encode_int(1234, check=True) == "16JD"
assert decode_int("16j-d", check=True) == 1234
assert encode_int(2**128 - 1) == "7ZZZZZZZZZZZZZZZZZZZZZZZZZ"
assert encode_int(1234, width=8, group=4) == "0000-016J"
assert encode(b"foobar") == "CSQPYRK1E8"
assert decode("csqpyrk1e8") == b"foobar"
assert decode(encode(bytearray(b"\x00\x01"), check=True), check=True) == b"\x00\x01"
assert normalize("ix-Lb-Ko") == "1X1BK0"
for bad, kwargs in [("CSQPYRK1E9", {}), ("0", {}), ("16JE", {"check": True})]:
    try:
        (decode_int if kwargs else decode)(bad, **kwargs)
    except CrockfordError as error:
        assert isinstance(error, ValueError)
        again = pickle.loads(pickle.dumps(error))
        assert type(again) is CrockfordError and str(again) == str(error)
    else:
        raise AssertionError(bad)
for call in (lambda: encode("text"), lambda: decode(text="16J"), lambda: encode_int(True)):
    try:
        call()
    except TypeError:
        pass
    else:
        raise AssertionError("accepted")
try:
    encode_int(1, width=-(10**5000))
except ValueError as error:
    assert str(error) == "width must not be negative"
else:
    raise AssertionError("negative width accepted")
big = 7**100000
assert decode_int(encode_int(big)) == big
print("e2e ok")
"""

CONSUMER = """
import crock
code: str = crock.encode_int(5, check=True)
data: bytes = crock.decode(crock.encode(memoryview(b"x")))
number: int = crock.decode_int(code, check=True)
crock.decode(b"00")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True)


@pytest.fixture(scope="module")
def dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    built = _run(sys.executable, "-m", "build", "--outdir", out, ROOT)
    assert built.returncode == 0, built.stderr
    return out


def test_wheel_and_sdist_contents(dist: Path) -> None:
    (wheel,) = dist.glob("crock-1.0.0-py3-none-any.whl")
    (sdist,) = dist.glob("crock-1.0.0.tar.gz")
    names = sorted(zipfile.ZipFile(wheel).namelist())
    package = [name for name in names if not name.startswith("crock-1.0.0.dist-info/")]
    assert package == [
        "crock/__init__.py",
        "crock/_alphabet.py",
        "crock/_bytes.py",
        "crock/_codec.py",
        "crock/_errors.py",
        "crock/_ints.py",
        "crock/py.typed",
    ]
    assert "crock-1.0.0.dist-info/licenses/LICENSE" in names
    metadata = zipfile.ZipFile(wheel).read("crock-1.0.0.dist-info/METADATA").decode()
    assert "Classifier: Development Status :: 5 - Production/Stable" in metadata
    assert "Requires-Dist" not in metadata.replace("extra == 'dev'", "")
    with tarfile.open(sdist) as archive:
        listing = [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]
    for absent in ("IMPROVEMENTS-round", "CERT-1.0-", "upstream/rfc", "node_modules", ".venv"):
        assert not any(absent in name for name in listing), absent
    for present in ("LICENSE", "README.md", "GUIDE.md", "CHANGELOG.md", "tests/test_contract.py"):
        assert present in listing, present
    assert "tests/upstream/MANIFEST.json" in listing


def test_installed_wheel_end_to_end(dist: Path, tmp_path: Path) -> None:
    (wheel,) = dist.glob("crock-*.whl")
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    python = env_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["e2e ok"]

    # A typed consumer: mypy reads the installed package's annotations through py.typed.
    (work / "consumer.py").write_text(CONSUMER, encoding="utf-8")
    mypy = _run(python, "-m", "pip", "install", "-q", "mypy")
    if mypy.returncode != 0:
        pytest.skip("mypy could not be installed in the throwaway venv")
    checked = _run(python, "-m", "mypy", "--strict", "--no-incremental", "consumer.py", cwd=work)
    assert checked.stdout.count("error:") == 1, checked.stdout
    assert 'consumer.py:6: error: Argument 1 to "decode" has incompatible type' in checked.stdout
