# crock

Typed Crockford base32 for bytes and ints, with normalization and an optional check symbol.

## Install

```
pip install crock
```

## Usage

```python
import crock

# Bytes round-trip.
text = crock.encode(b"hello")          # "D1JPRV3F"
crock.decode(text)                     # b"hello"

# Integers round-trip.
crock.encode_int(1234)                 # "16J"
crock.decode_int("16J")                # 1234

# Decoding is case-insensitive, normalizes look-alikes (I/L to 1, O to 0),
# and tolerates hyphens used for grouping.
crock.decode_int("16-j")               # 1234
crock.decode_int("IO")                 # same value as "10"

# Optional check symbol (mod 37) guards against transcription errors.
code = crock.encode_int(1234, check=True)
crock.decode_int(code, check=True)     # 1234, or raises CrockfordError if wrong

try:
    crock.decode("not valid!")
except crock.CrockfordError:
    ...
```

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
