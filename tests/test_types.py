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
    assert encode(numbers) == encode(numbers.tobytes())


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
    message = f"^expected str, got {type(text).__name__}$"
    with pytest.raises(TypeError, match=message):
        function(text)
    with pytest.raises(TypeError, match=message):
        function(text, check=True)


def test_encode_int_accepts_index_objects() -> None:
    assert encode_int(Index(1234)) == "16J"
    assert encode_int(1234, width=Index(5), group=Index(2)) == "00-16-J"


@pytest.mark.parametrize(
    ("n", "message"),
    [
        (True, "n must be an integer, not bool"),
        (False, "n must be an integer, not bool"),
        (1.0, "n must be an integer, not float"),
        (1.5, "n must be an integer, not float"),
        ("1", "n must be an integer, not str"),
        (None, "n must be an integer, not NoneType"),
    ],
)
def test_encode_int_refuses_bool_float_and_text(n: Any, message: str) -> None:
    with pytest.raises(TypeError, match=f"^{message}$"):
        encode_int(n)


@pytest.mark.parametrize("option", ["width", "group"])
@pytest.mark.parametrize("value", [True, 2.0, "2"])
def test_width_and_group_refuse_non_integers(option: str, value: Any) -> None:
    kind = type(value).__name__
    with pytest.raises(TypeError, match=f"^{option} must be an integer, not {kind}$"):
        encode_int(5, **{option: value})


def test_negative_width_is_refused() -> None:
    with pytest.raises(ValueError, match=r"^width must not be negative$"):
        encode_int(5, width=-1)


@pytest.mark.parametrize("data", [b"", b"x"])
@pytest.mark.parametrize("check", [False, True])
def test_group_is_validated_even_for_empty_data(data: bytes, check: bool) -> None:
    with pytest.raises(ValueError, match=r"^group must be positive$"):
        encode(data, check=check, group=0)
    with pytest.raises(ValueError, match=r"^group must not be negative$"):
        encode(data, check=check, group=-3)
    with pytest.raises(TypeError, match=r"^group must be an integer, not str$"):
        encode(data, check=check, group="2")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"^group must be positive$"):
        encode_int(5, check=check, group=0)


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
