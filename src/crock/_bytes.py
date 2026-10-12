"""Bytes to Crockford symbols and back, through the standard base32 codec with another alphabet."""

from __future__ import annotations

import base64
import binascii

from ._alphabet import CHECK_MODULUS, ENCODE
from ._errors import CrockfordError

_RFC4648 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_FROM_RFC = bytes.maketrans(_RFC4648, ENCODE.encode("ascii"))
_TO_RFC = bytes.maketrans(ENCODE.encode("ascii"), _RFC4648)

# Symbol counts mod 8 that no byte string encodes to: they would leave 5 or more pad bits.
_IMPOSSIBLE_LENGTHS = {1, 3, 6}


def as_bytes(data: object) -> bytes:
    """Accept any bytes-like object; refuse ``str`` and everything else with ``TypeError``."""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        raise TypeError("expected a bytes-like object, got str (encode it first)")
    try:
        return bytes(memoryview(data))  # type: ignore[arg-type]
    except TypeError:
        raise TypeError(f"expected a bytes-like object, got {type(data).__name__}") from None


def pad_bits(byte_count: int) -> int:
    """Zero bits appended so that ``byte_count`` bytes fill whole symbols."""
    return -8 * byte_count % 5


def check_value(data: bytes) -> int:
    """The number the encoded symbols spell, reduced mod 37."""
    shift = pow(2, pad_bits(len(data)), CHECK_MODULUS)
    return int.from_bytes(data, "big") % CHECK_MODULUS * shift % CHECK_MODULUS


def encode_bytes(data: bytes) -> str:
    """Encode bytes to canonical symbols, without check symbol or padding."""
    return base64.b32encode(data).rstrip(b"=").translate(_FROM_RFC).decode("ascii")


def decode_bytes(symbols: str) -> bytes:
    """Decode canonical symbols, rejecting lengths and pad bits no encoder produces."""
    length = len(symbols)
    if length % 8 in _IMPOSSIBLE_LENGTHS:
        raise CrockfordError(f"a length of {length} cannot encode a whole number of bytes")
    extra = 5 * length % 8
    if extra and ENCODE.index(symbols[-1]) & ((1 << extra) - 1):
        raise CrockfordError(f"non-zero pad bits in the last symbol {symbols[-1]!r}")
    padded = symbols.encode("ascii").translate(_TO_RFC) + b"=" * (-length % 8)
    try:
        return base64.b32decode(padded)
    except binascii.Error as error:  # pragma: no cover - the checks above leave no bad input
        raise CrockfordError(str(error)) from None
