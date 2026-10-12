"""Golden vectors copied from external sources, fetched on 2026-10-12 from the URL beside each."""

from __future__ import annotations

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

# https://www.crockford.com/base32.html, the symbol table: value, decode symbols, encode symbol.
SPEC_TABLE = [
    (0, "0 O o", "0"), (1, "1 I i L l", "1"), (2, "2", "2"), (3, "3", "3"), (4, "4", "4"),
    (5, "5", "5"), (6, "6", "6"), (7, "7", "7"), (8, "8", "8"), (9, "9", "9"),
    (10, "A a", "A"), (11, "B b", "B"), (12, "C c", "C"), (13, "D d", "D"), (14, "E e", "E"),
    (15, "F f", "F"), (16, "G g", "G"), (17, "H h", "H"), (18, "J j", "J"), (19, "K k", "K"),
    (20, "M m", "M"), (21, "N n", "N"), (22, "P p", "P"), (23, "Q q", "Q"), (24, "R r", "R"),
    (25, "S s", "S"), (26, "T t", "T"), (27, "V v", "V"), (28, "W w", "W"), (29, "X x", "X"),
    (30, "Y y", "Y"), (31, "Z z", "Z"),
]  # fmt: skip

# Same page, the check symbol table.
SPEC_CHECK_TABLE = [
    (32, "*", "*"),
    (33, "~", "~"),
    (34, "$", "$"),
    (35, "=", "="),
    (36, "U u", "U"),
]

# https://raw.githubusercontent.com/jbittel/base32-crockford/master/test.py
JBITTEL_ENCODE = [(1234, False, None, "16J"), (1234, True, None, "16JD"), (0, True, None, "00")]
JBITTEL_SPLIT = [(123456, 2, "3R-J0"), (123456, 3, "3RJ-0")]

# https://raw.githubusercontent.com/ulid/spec/master/README.md prints the largest ULID and says
# its time part is 281474976710655 (2^48 - 1). Derived: the values 2**128 - 1 for the whole
# string and the 10 symbol time part, read as the first 10 symbols of that string.
ULID_MAX = ("7ZZZZZZZZZZZZZZZZZZZZZZZZZ", 2**128 - 1)
ULID_MAX_TIME = ("7ZZZZZZZZZ", 281474976710655)

# https://www.rfc-editor.org/rfc/rfc4648.txt section 10, the BASE32 vectors as printed.
RFC4648_BASE32 = [
    (b"", ""), (b"f", "MY======"), (b"fo", "MZXQ===="), (b"foo", "MZXW6==="),
    (b"foob", "MZXW6YQ="), (b"fooba", "MZXW6YTB"), (b"foobar", "MZXW6YTBOI======"),
]  # fmt: skip
_RFC_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def _rfc_to_crockford(text: str) -> str:
    # Derived, not fetched: the same 5 bit groups spelled in the other alphabet, padding dropped.
    return "".join(
        "0123456789ABCDEFGHJKMNPQRSTVWXYZ"[_RFC_ALPHABET.index(c)] for c in text if c != "="
    )


@pytest.mark.parametrize(("value", "spellings", "symbol"), SPEC_TABLE)
def test_spec_symbol_table(value: int, spellings: str, symbol: str) -> None:
    assert encode_int(value) == symbol
    for spelling in spellings.split():
        assert decode_int(spelling) == value
        assert normalize(spelling) == symbol


def test_spec_excluded_letter_u_is_not_a_symbol() -> None:
    for spelling in ("U", "u"):
        with pytest.raises(CrockfordError):
            decode_int(spelling)


@pytest.mark.parametrize(("value", "spellings", "symbol"), SPEC_TABLE + SPEC_CHECK_TABLE)
def test_spec_check_symbol_table(value: int, spellings: str, symbol: str) -> None:
    number = 37 * 1000 + value
    assert encode_int(number, check=True)[-1] == symbol
    body = encode_int(number)
    for spelling in spellings.split():
        assert decode_int(body + spelling, check=True) == number


@pytest.mark.parametrize(("n", "check", "group", "expected"), JBITTEL_ENCODE)
def test_jbittel_encode(n: int, check: bool, group: int | None, expected: str) -> None:
    assert encode_int(n, check=check, group=group) == expected
    assert decode_int(expected, check=check) == n


@pytest.mark.parametrize(("n", "group", "expected"), JBITTEL_SPLIT)
def test_jbittel_split(n: int, group: int, expected: str) -> None:
    assert encode_int(n, group=group) == expected
    assert decode_int(expected) == n


def test_jbittel_bad_checksum_and_invalid_symbols() -> None:
    with pytest.raises(CrockfordError):
        decode_int("16JE", check=True)
    for text in ("u", "!"):
        with pytest.raises(CrockfordError):
            decode_int(text)


def test_jbittel_normalize() -> None:
    assert normalize("ix-Lb-Ko") == "1X1BK0"
    with pytest.raises(CrockfordError):
        normalize("ä")
    with pytest.raises(TypeError):
        normalize(1234)  # type: ignore[arg-type]


@pytest.mark.parametrize(("text", "value"), [ULID_MAX, ULID_MAX_TIME])
def test_ulid_extremes(text: str, value: int) -> None:
    assert decode_int(text) == value
    assert encode_int(value, width=len(text)) == text


@pytest.mark.parametrize(("data", "rfc"), RFC4648_BASE32)
def test_rfc4648_vectors_in_the_crockford_alphabet(data: bytes, rfc: str) -> None:
    expected = _rfc_to_crockford(rfc)
    assert encode(data) == expected
    assert decode(expected) == data
