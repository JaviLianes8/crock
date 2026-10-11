"""Encode and decode bytes and integers in Crockford base32."""

from __future__ import annotations

from ._alphabet import CHECK_ALPHABET, CHECK_MODULUS, ENCODE, decode_value
from ._errors import CrockfordError


def encode(data: bytes, *, check: bool = False) -> str:
    """Encode bytes, appending a check symbol when ``check`` is set."""
    text = _encode_bytes(data)
    if check:
        text += CHECK_ALPHABET[int.from_bytes(data, "big") % CHECK_MODULUS]
    return text


def decode(s: str, *, check: bool = False) -> bytes:
    """Decode bytes, tolerating hyphens and case, verifying the check symbol."""
    symbols = s.replace("-", "")
    if check:
        body, expected = _split_check(symbols)
        data = _decode_bytes(body)
        if int.from_bytes(data, "big") % CHECK_MODULUS != expected:
            raise CrockfordError("check symbol does not match")
        return data
    return _decode_bytes(symbols)


def encode_int(n: int, *, check: bool = False) -> str:
    """Encode a non-negative integer, appending a check symbol when set."""
    if n < 0:
        raise CrockfordError("cannot encode a negative integer")
    text = _encode_int(n)
    if check:
        text += CHECK_ALPHABET[n % CHECK_MODULUS]
    return text


def decode_int(s: str, *, check: bool = False) -> int:
    """Decode an integer, tolerating hyphens and case, verifying the check symbol."""
    symbols = s.replace("-", "")
    if check:
        body, expected = _split_check(symbols)
        value = _decode_int(body)
        if value % CHECK_MODULUS != expected:
            raise CrockfordError("check symbol does not match")
        return value
    return _decode_int(symbols)


def _split_check(symbols: str) -> tuple[str, int]:
    if not symbols:
        raise CrockfordError("check symbol missing")
    return symbols[:-1], decode_value(symbols[-1], check=True)


def _encode_bytes(data: bytes) -> str:
    bits = accumulated = 0
    out: list[str] = []
    for byte in data:
        bits = (bits << 8) | byte
        accumulated += 8
        while accumulated >= 5:
            accumulated -= 5
            out.append(ENCODE[(bits >> accumulated) & 0x1F])
    if accumulated:
        out.append(ENCODE[(bits << (5 - accumulated)) & 0x1F])
    return "".join(out)


def _decode_bytes(symbols: str) -> bytes:
    bits = accumulated = 0
    out = bytearray()
    for char in symbols:
        bits = (bits << 5) | decode_value(char)
        accumulated += 5
        if accumulated >= 8:
            accumulated -= 8
            out.append((bits >> accumulated) & 0xFF)
    return bytes(out)


def _encode_int(n: int) -> str:
    if n == 0:
        return ENCODE[0]
    out: list[str] = []
    while n:
        n, remainder = divmod(n, 32)
        out.append(ENCODE[remainder])
    return "".join(reversed(out))


def _decode_int(symbols: str) -> int:
    if not symbols:
        raise CrockfordError("cannot decode an empty string")
    value = 0
    for char in symbols:
        value = value * 32 + decode_value(char)
    return value
