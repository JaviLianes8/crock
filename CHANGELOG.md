# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
