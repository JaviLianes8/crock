"""Bytes encoding: round trips, leading zeros, and the strict, canonical decoder."""

from __future__ import annotations

import random

import pytest

from crock import CrockfordError, decode, encode, normalize

SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


@pytest.mark.parametrize(
    "data", [b"", b"\x00", b"hello", b"\xff\xfe\xfd\x00\x01", bytes(range(256))]
)
def test_bytes_round_trip(data: bytes) -> None:
    assert decode(encode(data)) == data


def test_every_length_up_to_forty_round_trips() -> None:
    rng = random.Random(7)
    for length in range(41):
        data = rng.randbytes(length)
        assert decode(encode(data)) == data
        assert len(encode(data)) == -(-8 * length // 5)


def test_empty_bytes_encode_to_empty_string() -> None:
    assert encode(b"") == ""
    assert decode("") == b""


def test_leading_zero_bytes_survive() -> None:
    assert encode(b"\x00\x00\x01") == "00002"
    assert decode("00002") == b"\x00\x00\x01"


def test_output_is_upper_case_canonical_symbols_only() -> None:
    text = encode(bytes(range(256)))
    assert set(text) <= set(SYMBOLS)


@pytest.mark.parametrize("length", [1, 3, 6, 9, 11, 14])
def test_lengths_no_byte_string_encodes_to_are_rejected(length: int) -> None:
    with pytest.raises(CrockfordError, match="whole number of bytes"):
        decode("0" * length)


@pytest.mark.parametrize("length", [2, 4, 5, 7])
def test_every_last_symbol_with_non_zero_pad_bits_is_rejected(length: int) -> None:
    pad = 5 * length % 8
    for value, symbol in enumerate(SYMBOLS):
        text = "0" * (length - 1) + symbol
        if value & ((1 << pad) - 1):
            with pytest.raises(CrockfordError, match="pad bits"):
                decode(text)
        else:
            assert encode(decode(text)) == text


def test_only_one_code_per_value() -> None:
    assert decode("CSQPYRK1E8") == b"foobar"
    with pytest.raises(CrockfordError):
        decode("CSQPYRK1E9")


def test_every_accepted_string_re_encodes_to_its_normalized_form() -> None:
    rng = random.Random(11)
    accepted = 0
    for _ in range(3000):
        text = "".join(rng.choice(SYMBOLS + "ilo-") for _ in range(rng.randrange(12)))
        try:
            data = decode(text)
        except CrockfordError:
            continue
        accepted += 1
        assert encode(data) == normalize(text)
    assert accepted > 500


def test_decode_is_case_insensitive_and_reads_aliases() -> None:
    text = encode(b"\x01\x10\xa0")
    assert decode(text.lower()) == b"\x01\x10\xa0"
    assert decode("o4") == decode("04")


def test_decode_tolerates_hyphens_anywhere() -> None:
    encoded = encode(b"hello")
    assert decode("-".join(encoded)) == b"hello"
    assert decode("--" + encoded + "--") == b"hello"


def test_group_inserts_hyphens_from_the_left() -> None:
    assert encode(b"hello", group=3) == "D1J-PRV-3F"
    assert encode(b"hello", group=8) == "D1JPRV3F"
    assert decode(encode(b"hello", group=3)) == b"hello"


def test_invalid_symbol_is_rejected() -> None:
    with pytest.raises(CrockfordError, match="'!'"):
        decode("00!0")
    with pytest.raises(CrockfordError):
        decode("UU")
