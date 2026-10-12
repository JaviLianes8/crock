"""The check symbol: one rule for bytes and integers, and the errors it is proven to catch."""

from __future__ import annotations

import itertools
import random

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CHECKS = SYMBOLS + "*~$=U"


def _accepts(code: str) -> bool:
    try:
        decode_int(code, check=True)
    except CrockfordError:
        return False
    return True


def test_check_symbol_round_trips_for_integers() -> None:
    assert decode_int(encode_int(1234, check=True), check=True) == 1234


def test_check_symbol_round_trips_for_bytes() -> None:
    assert decode(encode(b"payload", check=True), check=True) == b"payload"
    assert encode(b"", check=True) == "0"
    assert decode("0", check=True) == b""


def test_check_symbol_uses_the_extended_alphabet() -> None:
    assert encode_int(37, check=True)[-1] == "0"
    assert encode_int(32, check=True)[-1] == "*"
    assert encode_int(36, check=True)[-1] == "U"


def test_bytes_check_is_the_value_of_the_symbols() -> None:
    rng = random.Random(5)
    for length in range(1, 30):
        data = rng.randbytes(length)
        code = encode(data, check=True)
        assert code[-1] == encode_int(decode_int(code[:-1]), check=True)[-1]
        assert decode_int(code, check=True) == decode_int(code[:-1])


@pytest.mark.parametrize("data", [b"\x01", b"\x00\x07", b"\xff" * 3])
def test_bytes_check_differs_from_the_raw_byte_value_when_padded(data: bytes) -> None:
    pad = -8 * len(data) % 5
    value = int.from_bytes(data, "big") << pad
    assert encode(data, check=True)[-1] == CHECKS[value % 37]


def test_every_wrong_check_symbol_is_rejected() -> None:
    for n in (0, 1, 1234, 2**70 + 3):
        body = encode_int(n)
        right = encode_int(n, check=True)[-1]
        for symbol in CHECKS:
            assert _accepts(body + symbol) == (symbol == right)


def test_wrong_check_symbol_on_bytes_is_rejected() -> None:
    code = encode(b"hello", check=True)
    tampered = code[:-1] + ("*" if code[-1] != "*" else "~")
    with pytest.raises(CrockfordError, match="does not match"):
        decode(tampered, check=True)


def test_every_single_substitution_is_caught_on_short_codes() -> None:
    for body in map("".join, itertools.product(SYMBOLS, repeat=2)):
        code = body + encode_int(decode_int(body), check=True)[-1]
        for position, symbol in itertools.product(range(2), SYMBOLS):
            if symbol != body[position]:
                assert not _accepts(code[:position] + symbol + code[position + 1 :])


def test_every_adjacent_transposition_is_caught_on_short_codes() -> None:
    for body in map("".join, itertools.product(SYMBOLS, repeat=3)):
        code = body + encode_int(decode_int(body), check=True)[-1]
        for position in range(2):
            a, b = body[position], body[position + 1]
            if a != b:
                swapped = body[:position] + b + a + body[position + 2 :]
                assert not _accepts(swapped + code[-1])


def test_substitutions_and_transpositions_are_caught_on_long_codes() -> None:
    rng = random.Random(9)
    for _ in range(300):
        data = rng.randbytes(rng.randrange(1, 40))
        code = encode(data, check=True)
        body = code[:-1]
        position = rng.randrange(len(body))
        symbol = rng.choice(SYMBOLS.replace(body[position], ""))
        with pytest.raises(CrockfordError):
            decode(body[:position] + symbol + body[position + 1 :] + code[-1], check=True)
        if position + 1 < len(body) and body[position] != body[position + 1]:
            swapped = body[:position] + body[position + 1] + body[position] + body[position + 2 :]
            with pytest.raises(CrockfordError):
                decode(swapped + code[-1], check=True)


def test_check_symbol_accepts_lower_case_and_aliases() -> None:
    assert decode_int(encode_int(36) + "u", check=True) == 36
    assert decode_int(encode_int(37) + "o", check=True) == 37
    assert decode_int(encode_int(38) + "l", check=True) == 38
    assert decode_int("16J-D", check=True) == 1234


def test_check_symbols_are_refused_in_the_body() -> None:
    for symbol in "*~$=U":
        with pytest.raises(CrockfordError):
            decode_int(symbol + "0", check=True)
        with pytest.raises(CrockfordError):
            decode_int("1" + symbol)


def test_missing_or_invalid_check_symbol_is_rejected() -> None:
    for text in ("", "-", "--"):
        with pytest.raises(CrockfordError, match="missing"):
            decode(text, check=True)
    with pytest.raises(CrockfordError, match="invalid check symbol"):
        decode_int("16J!", check=True)


def test_normalize_with_check_verifies_and_canonicalizes() -> None:
    assert normalize("16j-d", check=True) == "16JD"
    assert normalize("14u", check=True) == "14U"
    with pytest.raises(CrockfordError):
        normalize("16JE", check=True)
