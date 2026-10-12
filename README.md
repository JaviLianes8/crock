# crock

Typed Crockford base32 for bytes and ints, with normalization and an optional check symbol.

[Crockford's base32](https://www.crockford.com/base32.html) spells numbers with 32 symbols
that people can read aloud and type back: digits and upper-case letters without I, L, O and
U. Decoding forgives case, reads I and L as 1 and O as 0, and ignores hyphens. An optional
check symbol catches a mistyped or swapped symbol before it reaches your database.

## Install

```
pip install crock
```

Python 3.10 or newer, no dependencies.

## Usage

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

## The rules

- `encode` and `encode_int` write upper-case canonical symbols only. `decode`,
  `decode_int` and `normalize` accept both cases, the aliases `I`, `i`, `L`, `l` (1) and
  `O`, `o` (0), and hyphens anywhere. Anything else, including spaces and `U` outside the
  check position, raises `CrockfordError`, which is a `ValueError`.
- An integer is zero-extended on the left, so `encode_int` never writes leading zeros unless
  you ask for a `width`, and `decode_int` reads leading zeros as zero. `encode_int` takes any
  non-negative integer, including objects with `__index__` such as NumPy integers, but not
  `bool` or `float`.
- Bytes are a big-endian bit string zero-extended on the right, the bit order of RFC 4648
  base32 without the `=` padding. `decode` is strict: a length that no byte string encodes
  to, or a last symbol with non-zero pad bits, is rejected, so every value has exactly one
  code (up to case, aliases and hyphens). `encode` takes `bytes`, `bytearray`,
  `memoryview` or any other buffer.
- The check symbol is the number the symbols spell, mod 37, written with the extra symbols
  `*`, `~`, `$`, `=` and `U` for 32 to 36. It is the same rule for bytes and integers, so
  `decode_int(code, check=True)` also verifies a checked bytes code. It catches every single
  wrong symbol and every swap of two neighbouring symbols. The check symbol is never part of
  `width`, but `group` counts it.
- Decoders take `str` only and raise `TypeError` for anything else; `encode` raises
  `TypeError` for `str`. Bad `width` or `group` values raise `TypeError` or a plain
  `ValueError`, never `CrockfordError`.
- Encoding and decoding run in linear time, including integers far past the limit Python puts
  on decimal string conversion.

## Why

Crockford base32 is a human-friendly encoding: no ambiguous characters, forgiving
on input, with an optional check symbol. On PyPI the only dedicated option,
`base32-crockford`, encodes integers only, has no type hints, and has not seen a
release since 2015. `crock` is a clean, zero-dependency, `mypy --strict` take that
handles both arbitrary bytes and integers, ships the check symbol for both, and
normalizes look-alikes and hyphens on decode.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
