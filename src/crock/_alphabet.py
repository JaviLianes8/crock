"""Crockford base32 symbol tables, decode normalization, and the check alphabet."""

from __future__ import annotations

from ._errors import CrockfordError

# The canonical alphabet: digits plus upper-case letters, excluding I, L, O and U.
ENCODE = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Five extra symbols used only for the check value, giving a prime modulus of 37.
CHECK_EXTRA = "*~$=U"
CHECK_ALPHABET = ENCODE + CHECK_EXTRA
CHECK_MODULUS = len(CHECK_ALPHABET)

_DECODE: dict[str, int] = {}
for _index, _symbol in enumerate(ENCODE):
    _DECODE[_symbol] = _index
    _DECODE[_symbol.lower()] = _index

# Decode-time normalization of look-alikes: I and L read as 1, O reads as 0.
for _alias, _value in (("I", 1), ("i", 1), ("L", 1), ("l", 1), ("O", 0), ("o", 0)):
    _DECODE[_alias] = _value

_DECODE_CHECK: dict[str, int] = dict(_DECODE)
for _index, _symbol in enumerate(CHECK_EXTRA, start=len(ENCODE)):
    _DECODE_CHECK[_symbol] = _index
    _DECODE_CHECK[_symbol.lower()] = _index


def decode_value(char: str, *, check: bool = False) -> int:
    """Map a single symbol to its value, applying normalization, or raise."""
    table = _DECODE_CHECK if check else _DECODE
    try:
        return table[char]
    except KeyError:
        raise CrockfordError(f"invalid symbol: {char!r}") from None
