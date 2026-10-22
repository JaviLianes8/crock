"""The run-time annotation of encode's data matches the buffers encode accepts."""

from __future__ import annotations

import array
import collections.abc
import mmap
import subprocess
import sys
import typing
from pathlib import Path

import pytest

import crock


def data_hint() -> typing.Any:
    return typing.get_type_hints(crock.encode)["data"]


def test_the_data_hint_is_the_standard_buffer_from_python_3_12() -> None:
    if sys.version_info < (3, 12):
        pytest.skip("collections.abc.Buffer is new in Python 3.12")
    assert data_hint() is collections.abc.Buffer


@pytest.mark.parametrize(
    "data",
    [b"ab", bytearray(b"ab"), memoryview(b"ab"), array.array("B", b"ab")],
    ids=["bytes", "bytearray", "memoryview", "array"],
)
def test_every_standard_buffer_is_an_instance_of_the_hint(data: typing.Any) -> None:
    assert isinstance(data, data_hint())
    assert crock.encode(data) == "C5H0"


def test_a_memory_map_is_an_instance_of_the_hint() -> None:
    mapped = mmap.mmap(-1, 2)
    try:
        mapped.write(b"ab")
        assert isinstance(mapped, data_hint())
        assert crock.encode(mapped) == "C5H0"
    finally:
        mapped.close()


@pytest.mark.parametrize("data", ["ab", 5, None, [1, 2]])
def test_what_encode_refuses_is_not_an_instance_of_the_hint(data: object) -> None:
    assert not isinstance(data, data_hint())
    with pytest.raises(TypeError):
        crock.encode(data)  # type: ignore[arg-type]


def test_crock_imports_and_encodes_without_mmap() -> None:
    # WASI and Emscripten builds of CPython have no mmap module.
    code = (
        "import sys, typing; sys.path.insert(0, sys.argv[1]); sys.modules['mmap'] = None; "
        "import crock; hint = typing.get_type_hints(crock.encode)['data']; "
        "print(crock.encode(b'foobar'), isinstance(b'', hint), isinstance(bytearray(), hint))"
    )
    root = str(Path(crock.__file__).parent.parent)
    done = subprocess.run(
        [sys.executable, "-I", "-c", code, root], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["CSQPYRK1E8", "True", "True"]


# A finder that makes the mmap module present but failing to load, as a broken extension
# module does. It only raises where crock imports mmap (Python 3.10 and 3.11).
FAILING_MMAP = """
import sys, typing
sys.path.insert(0, sys.argv[1])
asked = []
class Broken:
    def find_spec(self, name, path=None, target=None):
        if name == "mmap":
            asked.append(name)
            raise ImportError("DLL load failed while importing mmap")
        return None
sys.modules.pop("mmap", None)
sys.meta_path.insert(0, Broken())
import crock
hint = typing.get_type_hints(crock.encode)["data"]
print(crock.encode(b"foobar"), isinstance(bytearray(), hint), bool(asked))
"""


def test_crock_imports_and_encodes_when_mmap_fails_to_load() -> None:
    root = str(Path(crock.__file__).parent.parent)
    done = subprocess.run(
        [sys.executable, "-I", "-c", FAILING_MMAP, root],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    tried = "True" if sys.version_info < (3, 12) else "False"
    assert done.stdout.split() == ["CSQPYRK1E8", "True", tried]
