"""Typed Crockford base32 for bytes and ints, with normalization and an optional check symbol.

>>> import crock
>>> crock.encode_int(1234, check=True)
'16JD'
>>> crock.decode_int("16j-d", check=True)
1234
>>> crock.decode(crock.encode(b"\\x00key"))
b'\\x00key'
"""

# No "from __future__ import annotations" here: it would add a public "annotations" name.
from ._codec import decode, decode_int, encode, encode_int, normalize
from ._errors import CrockfordError

__version__ = "1.0.0"

__all__ = ["CrockfordError", "decode", "decode_int", "encode", "encode_int", "normalize"]
