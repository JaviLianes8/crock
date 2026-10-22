# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-22

First release on PyPI. The public API is stable: the six names `encode`, `decode`,
`encode_int`, `decode_int`, `normalize` and `CrockfordError`, their signatures and
defaults, the symbols they write and accept, the check symbol rule, and the exception types
listed in the guide. Changes after 1.0.0 follow Semantic Versioning.

### Changed

- The first argument of every function is positional-only (`encode(data, /, ...)`,
  `decode(text, /, ...)`, `encode_int(n, /, ...)` and so on); passing it by name raises
  `TypeError`. The options stay keyword-only.
- A negative `width` or `group` raises `ValueError` with a fixed message
  (`width must not be negative`) instead of quoting the value, which could fail to print
  for very large integers.
- A `width` larger than `sys.maxsize` raises `ValueError("width is too large")` instead of
  `OverflowError`.
- `CrockfordError` reports, prints and pickles as `crock.CrockfordError`.
- The package no longer exposes a stray `annotations` name.
- NumPy booleans are refused as an integer, `width` or `group` with the same `TypeError` as
  `bool`; up to NumPy 2.2 (`numpy.bool_` in 1.x, `numpy.bool` from 2.0) they were accepted
  as 0 or 1.
- The annotations of every public function resolve at run time
  (`typing.get_type_hints(crock.encode)` used to raise `NameError`), so runtime validators
  and documentation tools can read them. On Python 3.12 and later `data` is annotated with
  `collections.abc.Buffer`; on 3.10 and 3.11 the annotation is a stand-in that matches
  `bytes`, `bytearray`, `memoryview`, `array.array` and `mmap.mmap` (where available) only,
  so a runtime type checker there refuses other buffers that `encode` accepts (the guide
  has the details).

### Added

- Docstrings with runnable examples on every public name, checked as doctests.
- A guide (`GUIDE.md`) with the exact rules, the error table and the differences from
  `base32-crockford`.
- Python 3.14 support (tested on CPython 3.10 to 3.14, and 3.14 free-threaded).
- Tests against the specification page, RFC 4648, the ULID specification, the
  `base32-crockford` test file and code, `python-ulid` and the `base32-encode` and
  `base32-decode` npm packages, all fetched or installed by `scripts/fetch_upstream.py`
  and never shipped. Seeded fuzz tests for hostile input.

## [0.2.0]

### Added

- `normalize(text, check=False)` returns the canonical spelling of a code: upper case,
  aliases resolved, hyphens removed, the check symbol verified when asked.
- `encode_int(..., width=)` left-pads with `0`; `group=` on `encode` and `encode_int`
  inserts a hyphen every so many symbols, counted from the left, check symbol included.
- `encode` accepts `bytearray`, `memoryview` and any other buffer; `encode_int` accepts any
  object with `__index__`.

### Changed

- `decode` is strict: a length that no byte string encodes to, or a last symbol with
  non-zero pad bits, raises `CrockfordError`. Every value has exactly one code.
- The bytes check symbol is the value of the symbols mod 37 (the bytes zero-extended to
  whole symbols), the same rule as for integers, so `decode_int(code, check=True)` verifies
  a checked bytes code too.
- Encoding and decoding run in linear time, also for integers past the decimal string
  conversion limit.
- Wrong argument types raise `TypeError` with a clear message: `str` to `encode`, non-`str`
  to the decoders, `bool` or `float` to `encode_int`.

## [0.1.0]

- First release.
- `encode` and `decode` for arbitrary bytes, and `encode_int` and `decode_int`
  for non-negative integers, using the canonical Crockford alphabet.
- Case-insensitive decoding with look-alike normalization (I and L to 1, O to 0)
  and tolerance for hyphens used as grouping separators.
- Optional check symbol (mod 37) on both the bytes and the integer codecs, with
  `CrockfordError` raised on a mismatch or an invalid symbol.
- Closes the gap left by the integer-only, unmaintained `base32-crockford`:
  bytes support, the check symbol, and full type information.
