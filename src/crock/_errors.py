"""The error raised for input that crock cannot decode, and for a negative integer."""

from __future__ import annotations


class CrockfordError(ValueError):
    """Raised for invalid symbols, a failed check symbol, malformed input, or a negative integer.

    The negative integer case is ``encode_int(n)`` with ``n < 0``; every other case is a
    decoder refusing its input.

    It is a ``ValueError``, so existing ``except ValueError`` handlers keep working. The
    message names the problem and at most one offending symbol, never the whole input.

    >>> import crock
    >>> try:
    ...     crock.decode_int("16!")
    ... except crock.CrockfordError as error:
    ...     print(error)
    invalid symbol: '!'
    >>> crock.encode_int(-1)
    Traceback (most recent call last):
    ...
    crock.CrockfordError: cannot encode a negative integer
    >>> issubclass(crock.CrockfordError, ValueError)
    True
    """

    # Reported, pickled and printed as part of the package, not of this private module.
    __module__ = "crock"
