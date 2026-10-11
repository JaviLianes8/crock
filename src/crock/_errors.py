"""Error raised when input cannot be decoded as Crockford base32."""

from __future__ import annotations


class CrockfordError(ValueError):
    """Raised for invalid symbols, a failed check symbol, or malformed input."""
