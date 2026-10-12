"""Crockford base32 symbol tables, input normalization, and the check alphabet."""

from __future__ import annotations

from ._errors import CrockfordError

# The canonical alphabet: digits plus upper-case letters, excluding I, L, O and U.
ENCODE = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Five extra symbols used only for the check value, giving a prime modulus of 37.
CHECK_EXTRA = "*~$=U"
CHECK_ALPHABET = ENCODE + CHECK_EXTRA
CHECK_MODULUS = len(CHECK_ALPHABET)

# Every accepted spelling of a symbol, mapped to its canonical form.
_SPELLINGS: dict[str, str] = {}
for _symbol in ENCODE:
    _SPELLINGS[_symbol] = _SPELLINGS[_symbol.lower()] = _symbol
for _alias, _symbol in (("I", "1"), ("i", "1"), ("L", "1"), ("l", "1"), ("O", "0"), ("o", "0")):
    _SPELLINGS[_alias] = _symbol

# The spellings as a byte table: other bytes map to themselves, so anything that is not a
# canonical symbol after translation was invalid input.
_ASCII_TABLE = bytes(ord(_SPELLINGS.get(chr(code), chr(code))) for code in range(256))
_VALID_BYTES = ENCODE.encode("ascii")

_CHECK_VALUE: dict[str, int] = {}
for _index, _symbol in enumerate(CHECK_ALPHABET):
    _CHECK_VALUE[_symbol] = _index
    _CHECK_VALUE[_symbol.lower()] = _index
for _alias, _value in (("I", 1), ("i", 1), ("L", 1), ("l", 1), ("O", 0), ("o", 0)):
    _CHECK_VALUE[_alias] = _value


def require_str(text: object) -> str:
    """Return ``text`` if it is a ``str``, else raise ``TypeError``."""
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    return text


def canonical(text: str) -> str:
    """Upper-case, alias-free, hyphen-free form of ``text``, or raise on a bad symbol."""
    if text.isascii():
        result = text.encode("ascii").translate(_ASCII_TABLE, b"-")
        if not result.translate(None, _VALID_BYTES):
            return result.decode("ascii")
    raise CrockfordError(f"invalid symbol: {_first_invalid(text)!r}")


def _first_invalid(text: str) -> str:
    return next(char for char in text if char != "-" and char not in _SPELLINGS)


def split_check(text: str) -> tuple[str, int]:
    """Split off the trailing check symbol, returning the canonical body and its value."""
    stripped = text.rstrip("-")
    if not stripped:
        raise CrockfordError("check symbol missing")
    try:
        value = _CHECK_VALUE[stripped[-1]]
    except KeyError:
        raise CrockfordError(f"invalid check symbol: {stripped[-1]!r}") from None
    return canonical(stripped[:-1]), value


def check_symbol(value: int) -> str:
    """The check symbol for a non-negative number."""
    return CHECK_ALPHABET[value % CHECK_MODULUS]


def verify_check(value: int, expected: int) -> None:
    """Raise unless ``expected`` is the check value of ``value``."""
    if value % CHECK_MODULUS != expected:
        raise CrockfordError("check symbol does not match")
