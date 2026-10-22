"""The run-time annotation of encode's data matches the buffers encode accepts."""

from __future__ import annotations

import array
import collections.abc
import mmap
import sys
import typing

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
