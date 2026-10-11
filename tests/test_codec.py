import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int


@pytest.mark.parametrize(
    "data",
    [b"", b"\x00", b"hello", b"\xff\xfe\xfd\x00\x01", bytes(range(32))],
)
def test_bytes_round_trip(data: bytes) -> None:
    assert decode(encode(data)) == data


def test_empty_bytes_encode_to_empty_string() -> None:
    assert encode(b"") == ""
    assert decode("") == b""


def test_encode_uses_the_canonical_alphabet() -> None:
    assert encode(b"foobar") == "CSQPYRK1E8"


@pytest.mark.parametrize("n", [0, 1, 31, 32, 1234567890, 2**64])
def test_int_round_trip(n: int) -> None:
    assert decode_int(encode_int(n)) == n


def test_known_integer_vectors() -> None:
    assert encode_int(0) == "0"
    assert encode_int(1234) == "16J"
    assert decode_int("16J") == 1234


def test_negative_integer_is_rejected() -> None:
    with pytest.raises(CrockfordError):
        encode_int(-1)


def test_decode_is_case_insensitive() -> None:
    assert decode_int("16j") == decode_int("16J")


def test_decode_normalizes_look_alikes() -> None:
    assert decode_int("I") == 1
    assert decode_int("L") == 1
    assert decode_int("O") == 0
    assert decode_int("lIlO") == decode_int("1110")


def test_decode_tolerates_hyphens() -> None:
    encoded = encode(b"hello")
    hyphenated = "-".join([encoded[:2], encoded[2:]])
    assert decode(hyphenated) == b"hello"
    assert decode_int("1-6-J") == 1234


def test_check_symbol_round_trips_for_integers() -> None:
    encoded = encode_int(1234, check=True)
    assert decode_int(encoded, check=True) == 1234


def test_check_symbol_round_trips_for_bytes() -> None:
    encoded = encode(b"payload", check=True)
    assert decode(encoded, check=True) == b"payload"


def test_check_symbol_uses_the_extended_alphabet() -> None:
    assert encode_int(37, check=True)[-1] == "0"
    assert encode_int(32, check=True)[-1] == "*"
    assert encode_int(36, check=True)[-1] == "U"


def test_wrong_check_symbol_is_rejected() -> None:
    encoded = encode_int(1234, check=True)
    tampered = encoded[:-1] + ("*" if encoded[-1] != "*" else "~")
    with pytest.raises(CrockfordError):
        decode_int(tampered, check=True)


def test_missing_check_symbol_is_rejected() -> None:
    with pytest.raises(CrockfordError):
        decode("", check=True)


def test_invalid_symbol_is_rejected() -> None:
    with pytest.raises(CrockfordError):
        decode_int("U")
    with pytest.raises(CrockfordError):
        decode("!")


def test_empty_integer_string_is_rejected() -> None:
    with pytest.raises(CrockfordError):
        decode_int("")
