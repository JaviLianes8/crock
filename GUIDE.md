# crock guide

The exact rules behind the six public names of `crock`. Every example below runs as part of
the test suite and prints what its comments show.

## Symbols and spellings

The 32 symbols are `0123456789ABCDEFGHJKMNPQRSTVWXYZ`, the table of
[Crockford's page](https://www.crockford.com/base32.html). Encoders write upper-case
symbols only. Decoders (`decode`, `decode_int` and `normalize`) accept both cases, the
aliases `I`, `i`, `L`, `l` for 1 and `O`, `o` for 0, and hyphens anywhere. Anything else,
including spaces, other punctuation, non-ASCII look-alikes and `U` outside the check
position, raises `CrockfordError`.

```python
import crock

print(crock.normalize("ix-Lb-Ko"))  # 1X1BK0
print(crock.decode_int("O-l-I"))  # 33
try:
    crock.decode_int("16 J")
except crock.CrockfordError as error:
    print(error)  # invalid symbol: ' '
```

Whitespace is never stripped: trim user input yourself if your forms allow it.

## Integers

`encode_int(n, /, *, check=False, width=None, group=None)` writes a non-negative integer with
the most significant symbol first. The number is zero-extended on the left to a multiple of
5 bits, so there are no leading zeros unless `width` asks for them. `width` pads with `0` to
at least that many symbols and never truncates. `n` may be any object with `__index__`
(NumPy integers included) but not `bool` (NumPy booleans included) or `float`. A negative `n` raises
`CrockfordError`.

`decode_int(text, /, *, check=False)` reads leading zeros as zero, so `"00016J"` and `"16J"`
are the same number. An empty string (or one made only of hyphens) raises `CrockfordError`.

```python
import crock

print(crock.encode_int(0))  # 0
print(crock.encode_int(2**128 - 1, width=26))  # 7ZZZZZZZZZZZZZZZZZZZZZZZZZ
print(crock.encode_int(1234, width=6))  # 00016J
print(crock.decode_int("00016J"))  # 1234
```

A ULID is a 128 bit number written as `encode_int(n, width=26)`; its first 10 symbols are
the 48 bit millisecond time.

## Bytes

`encode(data, /, *, check=False, group=None)` reads `data` (any bytes-like object) as one
big-endian bit string and zero-extends it on the right to a multiple of 5 bits: the bit
order of RFC 4648 base32, without the `=` padding. Leading zero bytes are therefore kept,
and `n` bytes always give `ceil(8 * n / 5)` symbols.

`decode(text, /, *, check=False)` is strict. A symbol count that no byte string encodes to
(1, 3 or 6 more than a multiple of 8), or a last symbol whose padding bits are not zero, is
refused. Every byte string has exactly one code, up to case, aliases and hyphens.

```python
import crock

print(crock.encode(b"foobar"))  # CSQPYRK1E8
print(crock.decode("CSQPYRK1E8"))  # b'foobar'
print(len(crock.encode(bytes(16))))  # 26
try:
    crock.decode("CSQPYRK1E9")
except crock.CrockfordError as error:
    print(error)  # non-zero pad bits in the last symbol '9'
```

The two forms differ for the same 16 bytes: `encode` pads on the right, a ULID (an integer)
on the left. Use `encode_int(int.from_bytes(data, "big"), width=26)` for ULIDs.

## The check symbol

With `check=True` the encoders append one symbol: the value of the symbols before it,
modulo 37, written with the 32 symbols plus `*`, `~`, `$`, `=` and `U` for 32 to 36. The
decoders read the last symbol (any case, aliases included) as that check and verify it.
The rule is the same for bytes and integers: for bytes, the value is the number the
symbols spell, padding bits included. `decode_int(code, check=True)` therefore verifies any
checked bytes code too, except the code of empty bytes (`"0"`), whose number is empty.

```python
import crock

print(crock.encode_int(1234, check=True))  # 16JD
print(crock.encode_int(36, check=True))  # 14U
print(crock.decode_int("14u", check=True))  # 36
print(crock.encode(b"hi", check=True))  # D1MGJ
print(crock.decode_int("D1MGJ", check=True) == crock.decode_int("D1MG"))  # True
```

The specification defines the check symbol for numbers only, so the bytes rule is a choice,
made so that one rule covers both kinds of code. Other packages choose differently:
`crockford32` uses the value of the bytes, without the padding bits. Its check symbols for
bytes are therefore not interchangeable with those of `crock`: for `b"H\t"` it writes
`904GF` where `crock` writes `904GJ`, and `crock` refuses `904GF`.

The check catches every single wrong symbol and every swap of two neighbouring symbols. It
does not catch an inserted or a dropped symbol, and a leading `0` adds nothing to the
value, so dropping it still passes the check (and, for a bytes code, can decode to other
bytes). `width` never counts the check symbol; `group` does.

## Groups and normalize

`group=n` inserts a hyphen every `n` symbols, counted from the left, check symbol included.
`normalize(text, /, *, check=False)` returns the canonical spelling: upper case, aliases
resolved, hyphens removed, and with `check=True` the check symbol verified and written in
its canonical form. Two codes for the same value normalize to the same string only if they
have the same length (leading zeros are kept).

```python
import crock

print(crock.encode_int(123456, group=2))  # 3R-J0
print(crock.encode_int(1234, check=True, group=2))  # 16-JD
print(crock.normalize("16j-d", check=True))  # 16JD
print(crock.normalize("15o", check=True))  # 150
```

## Errors and types

| Situation | Exception |
| --- | --- |
| Invalid symbol, impossible length, non-zero pad bits, missing or wrong check symbol, empty integer code, negative integer | `CrockfordError` (a `ValueError`) |
| `str` given to `encode`, non-`str` given to a decoder, `bool` (NumPy booleans too), `float` or text as an integer, width or group | `TypeError` |
| Negative `width`, `width` larger than `sys.maxsize`, `group` below 1 | plain `ValueError` |

Messages name the problem and at most one offending symbol, never the whole input. The
first argument of every function is positional-only and the options are keyword-only.
The package ships `py.typed`; results are typed `str`, `bytes` and `int`.

The annotations also resolve at run time, for validators and documentation tools. On
Python 3.12 and later `data` is annotated with `collections.abc.Buffer`, which every buffer
matches. Python 3.10 and 3.11 have no such type, so there it is a stand-in that matches
`bytes`, `bytearray`, `memoryview`, `array.array` and `mmap.mmap` only: `encode` still
accepts any other buffer, such as a NumPy array, but a runtime type checker that reads the
annotation refuses it.

## Size and speed

Encoding and decoding run in linear time, including integers far past the limit Python
puts on decimal string conversion: both directions go through power-of-two conversions.
`width` is honoured as given, so a huge width builds a huge string.

## Differences from base32-crockford

`crock` runs the test file of [`base32-crockford`](https://github.com/jbittel/base32-crockford)
and compares with its code on seeded random input. The differences, all deliberate:

- `crock` refuses floats (`TypeError`) where the reference truncates them.
- There is no `strict` mode: decoding always normalizes.
- Without `check=True`, the reference reads a trailing check-only symbol (`*~$=U`) as a
  digit; `crock` refuses it.
- With `check=True`, the reference reads `"0"` as the number zero with an empty body;
  `crock` refuses an empty number.
- `normalize("")` returns `""`; the reference raises.
- `encode_int(0, check=True, group=1)` gives `"0-0"`; the reference skips grouping for zero.
