# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
