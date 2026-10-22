# crock

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Typed Crockford base32 for bytes and ints, with normalization and an optional check symbol.

## The problem

Order numbers, invite codes, licence keys and short IDs get read aloud, copied by hand and
typed back. Decimal is long, hexadecimal is not much shorter, and base64 mixes cases and
punctuation. [Crockford's base32](https://www.crockford.com/base32.html) spells numbers
with 32 symbols chosen for people: digits and upper-case letters without I, L, O and U.
Decoding forgives case, reads I and L as 1 and O as 0, and ignores hyphens, and an optional
check symbol catches a mistyped symbol or two swapped neighbours before the code reaches
your database.

`crock` implements the whole scheme for integers and for arbitrary bytes, strictly: every
byte string has exactly one code (up to case, aliases and hyphens), integer codes differ
only by leading zeros, which decode as zero, and anything else is refused with a clear
error.

## Install

```
pip install crock
```

Python 3.10 or newer, no dependencies.

## Quick start

Integers, for IDs, order numbers and short codes:

```python
import crock

print(crock.encode_int(1234))  # 16J
print(crock.decode_int("16j"))  # 1234
print(crock.encode_int(1234, width=8, group=4))  # 0000-016J
print(crock.decode_int("0000-016J"))  # 1234
```

Bytes, for keys, hashes and tokens. Leading zero bytes are kept:

```python
import crock

code = crock.encode(b"\x00hello", group=4)
print(code)  # 01M6-AV3C-DW
print(crock.decode(code))  # b'\x00hello'
```

The check symbol, for codes that people copy by hand:

```python
import crock

code = crock.encode_int(1234, check=True)
print(code)  # 16JD
print(crock.decode_int(code, check=True))  # 1234
try:
    crock.decode_int("1J6D", check=True)
except crock.CrockfordError as error:
    print(error)  # check symbol does not match
```

`normalize` gives the canonical spelling of what someone typed, so stored codes compare
equal:

```python
import crock

print(crock.normalize("ix-Lb-Ko"))  # 1X1BK0
print(crock.normalize("16j-d", check=True))  # 16JD
```

The public API is six names: `encode`, `decode`, `encode_int`, `decode_int`, `normalize`
and `CrockfordError` (a `ValueError`). The [guide](https://github.com/JaviLianes8/crock/blob/main/GUIDE.md)
has the exact rules for each.

## Why crock

These are the other Crockford base32 packages on PyPI, as published on 2026-10-22:

- [`base32-crockford`](https://pypi.org/project/base32-crockford/) 0.3.0, last released in
  March 2015: integers only, no type hints, and a float is truncated (`encode(4.2)` gives
  `"4"`). Without `checksum=True`, `decode("1U")` reads the check-only symbol `U` as a digit
  and returns 68. Its own test file and seeded comparisons with its code run against
  `crock` in this repository; the guide lists the few places where the two differ.
- [`base32-lib`](https://pypi.org/project/base32-lib/) 1.1.1: integers only, lower-case
  output, and a two digit ISO 7064 checksum instead of Crockford's check symbol.
- [`crockford32`](https://pypi.org/project/crockford32/) 1.0.2: a compiled extension
  published only as a Linux x86-64 wheel for CPython 3.10, and its decoder does not apply
  the I, L and O conversions. Its check symbol for bytes is the value of the bytes mod 37,
  where `crock` uses the value of the symbols (padding bits included), so the two write
  different check symbols for most byte strings; the guide explains the choice.
- [`python-ulid`](https://pypi.org/project/python-ulid/): Crockford base32 for 16 byte
  ULIDs only.

The standard library's `base64.b32hexencode` (Python 3.10 and newer) uses the RFC 4648
"extended hex" alphabet, which includes I, L, O and U and pads with `=`.

`crock` covers both integers and arbitrary bytes, writes and verifies the check symbol for
both, normalizes look-alikes and hyphens, runs in linear time on megabyte inputs, ships
type information checked with `mypy --strict`, and has no dependencies.

## Documentation

- [Guide](https://github.com/JaviLianes8/crock/blob/main/GUIDE.md): the rules for integers,
  bytes, the check symbol, errors and types.
- [Changelog](https://github.com/JaviLianes8/crock/blob/main/CHANGELOG.md)

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/crock/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
