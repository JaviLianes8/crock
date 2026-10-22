"""Error raised when input cannot be decoded as Crockford base32."""

from __future__ import annotations


class CrockfordError(ValueError):
    """Raised for invalid symbols, a failed check symbol, or malformed input.

    It is a ``ValueError``, so existing ``except ValueError`` handlers keep working. The
    message names the problem and at most one offending symbol, never the whole input.

    >>> import crock
    >>> try:
    ...     crock.decode_int("16!")
    ... except crock.CrockfordError as error:
    ...     print(error)
    invalid symbol: '!'
    >>> issubclass(crock.CrockfordError, ValueError)
    True
    """

    # Reported, pickled and printed as part of the package, not of this private module.
    __module__ = "crock"
