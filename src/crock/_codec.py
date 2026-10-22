"""The public encode, decode and normalize functions for bytes and integers."""

from __future__ import annotations

import abc
import sys
from typing import TYPE_CHECKING, SupportsIndex

from ._alphabet import canonical, check_symbol, require_str, split_check, verify_check
from ._bytes import as_bytes, check_value, decode_bytes, encode_bytes
from ._ints import as_int, decode_number, encode_number

# Any object with the buffer protocol. The name must also exist at run time, because tools
# such as validators and documentation generators evaluate the annotations.
if sys.version_info >= (3, 12):
    from collections.abc import Buffer
elif TYPE_CHECKING:
    from typing_extensions import Buffer
else:
    # The typing_extensions stand-in, without the dependency; it has no abstract methods.
    class Buffer(abc.ABC):  # noqa: B024
        """Objects that support the buffer protocol."""

        __slots__ = ()

    for _kind in (bytes, bytearray, memoryview):
        Buffer.register(_kind)


def encode(data: Buffer, /, *, check: bool = False, group: SupportsIndex | None = None) -> str:
    """Encode bytes as upper-case symbols, zero-extending the last symbol on the right.

    ``data`` is any bytes-like object (``bytes``, ``bytearray``, ``memoryview``, ...).
    ``check`` appends the check symbol (the value of the symbols mod 37). ``group`` inserts a
    hyphen every ``group`` symbols, counted from the left, check symbol included. Leading zero
    bytes are kept.

    >>> encode(b"foobar")
    'CSQPYRK1E8'
    >>> encode(b"\\x00hello", group=4)
    '01M6-AV3C-DW'
    >>> encode(b"hi", check=True)
    'D1MGJ'
    """
    raw = as_bytes(data)
    text = encode_bytes(raw)
    if check:
        text += check_symbol(check_value(raw))
    return _grouped(text, group)


def decode(text: str, /, *, check: bool = False) -> bytes:
    """Decode symbols to bytes, accepting any case, the I/L/O aliases and hyphens.

    Raises ``CrockfordError`` for an invalid symbol, a length or last symbol that no byte
    string encodes to, or (with ``check``) a missing or wrong check symbol.

    >>> decode("csqp-yrk1-e8")
    b'foobar'
    >>> decode("D1MGJ", check=True)
    b'hi'
    >>> decode("CSQPYRK1E9")
    Traceback (most recent call last):
    ...
    crock.CrockfordError: non-zero pad bits in the last symbol '9'
    """
    require_str(text)
    if not check:
        return decode_bytes(canonical(text))
    body, expected = split_check(text)
    data = decode_bytes(body)
    verify_check(check_value(data), expected)
    return data


def encode_int(
    n: SupportsIndex,
    /,
    *,
    check: bool = False,
    width: SupportsIndex | None = None,
    group: SupportsIndex | None = None,
) -> str:
    """Encode a non-negative integer, zero-extended on the left.

    ``width`` left-pads with ``0`` to at least that many symbols (the check symbol is not
    counted). ``check`` and ``group`` work as in :func:`encode`. A negative ``n`` raises
    ``CrockfordError``.

    >>> encode_int(1234)
    '16J'
    >>> encode_int(1234, check=True)
    '16JD'
    >>> encode_int(1234, width=8, group=4)
    '0000-016J'
    """
    value = as_int(n)
    text = encode_number(value)
    if width is not None:
        size = _non_negative(width, "width")
        if size > sys.maxsize:
            raise ValueError("width is too large")
        text = text.rjust(size, "0")
    if check:
        text += check_symbol(value)
    return _grouped(text, group)


def decode_int(text: str, /, *, check: bool = False) -> int:
    """Decode symbols to a non-negative integer, accepting case, aliases and hyphens.

    Raises ``CrockfordError`` for an empty string, an invalid symbol, or (with ``check``) a
    missing or wrong check symbol.

    >>> decode_int("16j")
    1234
    >>> decode_int("0000-016J")
    1234
    >>> decode_int("16JE", check=True)
    Traceback (most recent call last):
    ...
    crock.CrockfordError: check symbol does not match
    """
    require_str(text)
    if not check:
        return decode_number(canonical(text))
    body, expected = split_check(text)
    value = decode_number(body)
    verify_check(value, expected)
    return value


def normalize(text: str, /, *, check: bool = False) -> str:
    """The canonical spelling of ``text``: upper case, aliases resolved, hyphens removed.

    With ``check`` the last symbol is read as a check symbol and verified. Two codes for the
    same value normalize to the same string only if they have the same length.

    >>> normalize("ix-Lb-Ko")
    '1X1BK0'
    >>> normalize("16j-d", check=True)
    '16JD'
    """
    require_str(text)
    if not check:
        return canonical(text)
    body, expected = split_check(text)
    verify_check(decode_number(body) if body else 0, expected)
    return body + check_symbol(expected)


def _non_negative(value: object, name: str) -> int:
    number = as_int(value, name)
    if number < 0:
        # The value itself is left out: it can be too long to print.
        raise ValueError(f"{name} must not be negative")
    return number


def _grouped(text: str, group: SupportsIndex | None) -> str:
    if group is None:
        return text
    size = _non_negative(group, "group")
    if size == 0:
        raise ValueError("group must be positive")
    return "-".join(text[start : start + size] for start in range(0, len(text), size))
