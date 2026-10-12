"""The public encode, decode and normalize functions for bytes and integers."""

from __future__ import annotations

from ._alphabet import canonical, check_symbol, require_str, split_check, verify_check
from ._bytes import as_bytes, check_value, decode_bytes, encode_bytes
from ._ints import as_int, decode_number, encode_number

BytesLike = bytes | bytearray | memoryview


def encode(data: BytesLike, *, check: bool = False, group: int | None = None) -> str:
    """Encode bytes as upper-case symbols, zero-extending the last symbol on the right.

    ``check`` appends the check symbol (the value of the symbols mod 37). ``group`` inserts a
    hyphen every ``group`` symbols, counted from the left, check symbol included.
    """
    raw = as_bytes(data)
    text = encode_bytes(raw)
    if check:
        text += check_symbol(check_value(raw))
    return _grouped(text, group)


def decode(text: str, *, check: bool = False) -> bytes:
    """Decode symbols to bytes, accepting any case, the I/L/O aliases and hyphens.

    Raises ``CrockfordError`` for an invalid symbol, a length or last symbol that no byte
    string encodes to, or (with ``check``) a missing or wrong check symbol.
    """
    require_str(text)
    if not check:
        return decode_bytes(canonical(text))
    body, expected = split_check(text)
    data = decode_bytes(body)
    verify_check(check_value(data), expected)
    return data


def encode_int(
    n: int, *, check: bool = False, width: int | None = None, group: int | None = None
) -> str:
    """Encode a non-negative integer, zero-extended on the left.

    ``width`` left-pads with ``0`` to at least that many symbols (the check symbol is not
    counted). ``check`` and ``group`` work as in :func:`encode`.
    """
    value = as_int(n)
    text = encode_number(value)
    if width is not None:
        text = text.rjust(_non_negative(width, "width"), "0")
    if check:
        text += check_symbol(value)
    return _grouped(text, group)


def decode_int(text: str, *, check: bool = False) -> int:
    """Decode symbols to a non-negative integer, accepting case, aliases and hyphens.

    Raises ``CrockfordError`` for an empty string, an invalid symbol, or (with ``check``) a
    missing or wrong check symbol.
    """
    require_str(text)
    if not check:
        return decode_number(canonical(text))
    body, expected = split_check(text)
    value = decode_number(body)
    verify_check(value, expected)
    return value


def normalize(text: str, *, check: bool = False) -> str:
    """The canonical spelling of ``text``: upper case, aliases resolved, hyphens removed.

    With ``check`` the last symbol is read as a check symbol and verified. Two codes for the
    same value normalize to the same string only if they have the same length.
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
        raise ValueError(f"{name} must not be negative, got {number}")
    return number


def _grouped(text: str, group: int | None) -> str:
    if group is None:
        return text
    size = _non_negative(group, "group")
    if size == 0:
        raise ValueError("group must be positive")
    return "-".join(text[start : start + size] for start in range(0, len(text), size))
