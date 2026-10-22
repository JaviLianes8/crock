"""Non-negative integers to Crockford symbols and back, in linear time."""

from __future__ import annotations

import operator

from ._alphabet import ENCODE
from ._bytes import encode_bytes
from ._errors import CrockfordError

# Python's own base 32 digits, so ``int(text, 32)`` does the work after validation.
_TO_PYTHON = bytes.maketrans(ENCODE.encode("ascii"), b"0123456789abcdefghijklmnopqrstuv")
_NUMPY_BOOLS = ("bool_", "bool")


def as_int(n: object, name: str = "n") -> int:
    """Accept anything with ``__index__`` except ``bool``; refuse the rest with ``TypeError``."""
    kind = type(n)
    # NumPy booleans are not bool subclasses, yet up to NumPy 2.2 they have __index__. The
    # type is named bool_ in NumPy 1.x and bool from NumPy 2.0.
    if isinstance(n, bool) or (kind.__module__ == "numpy" and kind.__name__ in _NUMPY_BOOLS):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        return operator.index(n)  # type: ignore[arg-type]
    except TypeError:
        raise TypeError(f"{name} must be an integer, not {type(n).__name__}") from None


def encode_number(n: int) -> str:
    """Canonical symbols for ``n >= 0``, zero-extended on the left, no leading zeros."""
    if n < 0:
        raise CrockfordError("cannot encode a negative integer")
    if n == 0:
        return ENCODE[0]
    # Whole groups of 40 bits are both whole bytes and whole symbols, so the bytes codec
    # yields the symbols of n with only leading zeros to strip.
    byte_count = -(-n.bit_length() // 40) * 5
    return encode_bytes(n.to_bytes(byte_count, "big")).lstrip(ENCODE[0])


def decode_number(symbols: str) -> int:
    """The value of canonical symbols; power-of-two bases skip the int string size limit."""
    if not symbols:
        raise CrockfordError("cannot decode an empty string")
    return int(symbols.encode("ascii").translate(_TO_PYTHON), 32)
