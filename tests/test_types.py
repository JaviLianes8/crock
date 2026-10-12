"""Argument types: what each function accepts and the TypeError or ValueError for the rest."""

from __future__ import annotations

import array
from typing import Any

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize


class Index:
    """An integer-like object, the way NumPy integers present themselves."""

    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


def test_crockford_error_is_a_value_error() -> None:
    assert issubclass(CrockfordError, ValueError)


@pytest.mark.parametrize(
    "data",
    [bytearray(b"hello"), memoryview(b"hello"), memoryview(b"xhellox")[1:-1]],
)
def test_encode_accepts_bytes_like_objects(data: Any) -> None:
    assert encode(data) == encode(b"hello")


def test_encode_accepts_a_strided_memoryview() -> None:
    assert encode(memoryview(b"hxexlxlxo")[::2]) == encode(b"hello")


def test_encode_reads_other_buffers_as_raw_bytes() -> None:
    numbers = array.array("H", [1, 2])
    assert encode(numbers) == encode(numbers.tobytes())  # type: ignore[arg-type]


@pytest.mark.parametrize("data", ["hello", 5, [1, 2], None])
def test_encode_refuses_non_bytes(data: Any) -> None:
    with pytest.raises(TypeError):
        encode(data)


def test_encode_of_str_says_to_encode_first() -> None:
    with pytest.raises(TypeError, match="encode it first"):
        encode("hello")  # type: ignore[arg-type]


@pytest.mark.parametrize("function", [decode, decode_int, normalize])
@pytest.mark.parametrize("text", [b"16J", 1234, None, ["16J"]])
def test_decoders_refuse_non_str(function: Any, text: Any) -> None:
    with pytest.raises(TypeError, match="expected str"):
        function(text)
    with pytest.raises(TypeError, match="expected str"):
        function(text, check=True)


def test_encode_int_accepts_index_objects() -> None:
    assert encode_int(Index(1234)) == "16J"
    assert encode_int(1234, width=Index(5), group=Index(2)) == "00-16-J"


@pytest.mark.parametrize("n", [True, False, 1.0, 1.5, "1", None])
def test_encode_int_refuses_bool_float_and_text(n: Any) -> None:
    with pytest.raises(TypeError):
        encode_int(n)


@pytest.mark.parametrize("option", ["width", "group"])
@pytest.mark.parametrize("value", [True, 2.0, "2"])
def test_width_and_group_refuse_non_integers(option: str, value: Any) -> None:
    with pytest.raises(TypeError, match=option):
        encode_int(5, **{option: value})


def test_negative_width_and_non_positive_group_are_refused() -> None:
    with pytest.raises(ValueError, match="width"):
        encode_int(5, width=-1)
    with pytest.raises(ValueError, match="group"):
        encode_int(5, group=0)
    with pytest.raises(ValueError, match="group"):
        encode(b"x", group=-3)


def test_parameter_errors_are_not_crockford_errors() -> None:
    with pytest.raises(ValueError) as caught:
        encode_int(5, group=0)
    assert not isinstance(caught.value, CrockfordError)


def test_non_ascii_input_is_rejected_with_the_offending_character() -> None:
    for text in (chr(0x212A), "1" + chr(0x0661), chr(0xFF11)):
        with pytest.raises(CrockfordError, match="invalid symbol"):
            decode_int(text)
    with pytest.raises(CrockfordError, match=repr(chr(0xE4))):
        normalize("AB" + chr(0xE4))
