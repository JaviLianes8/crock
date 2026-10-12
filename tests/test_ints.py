"""Integer encoding: round trips, width, groups, and very large values."""

from __future__ import annotations

import random

import pytest

from crock import CrockfordError, decode_int, encode_int


@pytest.mark.parametrize("n", [0, 1, 31, 32, 1023, 1024, 1234567890, 2**64, 2**130 + 5])
def test_int_round_trip(n: int) -> None:
    assert decode_int(encode_int(n)) == n


def test_random_ints_round_trip_without_leading_zeros() -> None:
    rng = random.Random(3)
    for bits in range(1, 300):
        n = rng.getrandbits(bits) | 1 << (bits - 1)
        text = encode_int(n)
        assert decode_int(text) == n
        assert len(text) == -(-bits // 5)
        assert text[0] != "0"


def test_known_integer_vectors() -> None:
    assert encode_int(0) == "0"
    assert encode_int(32) == "10"
    assert encode_int(1234) == "16J"


def test_negative_integer_is_rejected() -> None:
    with pytest.raises(CrockfordError):
        encode_int(-1)


def test_leading_zeros_do_not_change_the_value() -> None:
    assert decode_int("00016J") == 1234
    assert decode_int("0") == 0


def test_decode_is_case_insensitive_and_reads_aliases() -> None:
    assert decode_int("16j") == 1234
    assert decode_int("I") == decode_int("i") == decode_int("L") == decode_int("l") == 1
    assert decode_int("O") == decode_int("o") == 0
    assert decode_int("lIlO") == decode_int("1110")


def test_decode_tolerates_hyphens() -> None:
    assert decode_int("1-6-J") == 1234
    assert decode_int("-16J-") == 1234


def test_empty_or_hyphen_only_string_is_rejected() -> None:
    for text in ("", "-", "---"):
        with pytest.raises(CrockfordError, match="empty"):
            decode_int(text)


def test_width_pads_on_the_left() -> None:
    assert encode_int(1234, width=6) == "00016J"
    assert encode_int(1234, width=2) == "16J"
    assert encode_int(0, width=0) == "0"
    assert encode_int(1234, width=6, check=True) == "00016JD"


def test_group_counts_the_check_symbol() -> None:
    assert encode_int(1234, check=True, group=2) == "16-JD"
    assert encode_int(1234, width=8, group=4) == "0000-016J"
    assert decode_int("16-JD", check=True) == 1234


def test_values_beyond_the_int_string_limit_round_trip() -> None:
    n = 3**200000
    text = encode_int(n)
    assert len(text) > 50000
    assert decode_int(text) == n
    assert decode_int("Z" * 100000) == 32**100000 - 1


def test_invalid_symbol_is_rejected() -> None:
    for text in ("U", "1 2", "+1", "1_0", " 1", "1\n"):
        with pytest.raises(CrockfordError):
            decode_int(text)
