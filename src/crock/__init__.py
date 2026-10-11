"""Typed Crockford base32 for bytes and ints, with normalization and an optional check symbol."""

from __future__ import annotations

from ._codec import decode, decode_int, encode, encode_int
from ._errors import CrockfordError

__version__ = "0.1.0"

__all__ = ["CrockfordError", "decode", "decode_int", "encode", "encode_int"]
