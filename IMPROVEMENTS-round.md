# crock improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Strict, canonical bytes decoding (impossible lengths and non-zero pad bits rejected)
- [x] Check symbol over the value of the symbols, shared by bytes and integers
- [x] Linear time codecs for large inputs
- [x] Input types: bytes-like in, `TypeError` for wrong types, `bool` and floats refused
- [x] `normalize`, `width` and `group`
- [x] Contracts: fetched golden vectors, reference model, error detection proof, typing, README examples, installed wheel e2e
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` (not yet on PyPI) ships `encode`, `decode`, `encode_int`, `decode_int` and
`CrockfordError`. The alphabet, the aliases and the check alphabet are right, but reading it
as a user who stores IDs or prints codes for people to type back turns up these gaps:

- `decode` accepts strings no encoder produces. `decode("0")` returns `b""`, and
  `decode("CSQPYRK1E9")` returns the same bytes as `"CSQPYRK1E8"`, because the length is not
  checked and the pad bits of the last symbol are ignored. Two different codes for one value
  break any lookup that compares codes.
- The bytes check symbol is taken over `int.from_bytes(data)`, not over the number the
  symbols spell (the data zero-extended to a multiple of 5 bits). An integer-only decoder
  computes a different check for the same string.
- The bit buffer is never masked and `decode_int` multiplies digit by digit, so large inputs
  pay more than linear time.
- Wrong types fail deep inside with unrelated messages: `encode("text")`,
  `decode(b"16J")`, `encode_int(1.5)`; `encode_int(True)` returns `"1"`.
- No way to get the canonical form of what a person typed, to pad an integer to a fixed width
  (ULIDs are 26 symbols), or to emit the hyphen groups the spec describes.
- Packaging: no Python version classifiers, no wheel test, README examples never run.

## Sources (fetched 2026-10-12)

- Crockford, "Base 32", https://www.crockford.com/base32.html (page dated 2019-03-04): the
  32 symbol table with decode aliases (`0 O o`, `1 I i L l`), I L O U excluded, upper case on
  encode, both cases on decode; "If the bit-length of the number to be encoded is not a
  multiple of 5 bits, then zero-extend the number"; hyphens may be inserted and are ignored
  on decode; the optional check symbol "encodes the number modulo 37" with the extra symbols
  `* ~ $ = U` (`u` accepted on decode) and is meant to catch wrong-symbol and
  transposed-symbol errors.
- `base32-crockford` test file,
  https://raw.githubusercontent.com/jbittel/base32-crockford/master/test.py: `1234` is
  `16J`, with check `16JD`; `0` with check is `00`; `123456` split by 2 is `3R-J0` and by 3
  is `3RJ-0`; `16JE` fails the check; `ix-Lb-Ko` normalizes to `1X1BK0`.
- ULID spec, https://raw.githubusercontent.com/ulid/spec/master/README.md: the largest ULID is
  `7ZZZZZZZZZZZZZZZZZZZZZZZZZ` (2^128 - 1) and its time part `7ZZZZZZZZZ` is
  `281474976710655` (2^48 - 1).
- RFC 4648 section 10, https://www.rfc-editor.org/rfc/rfc4648.txt: the base32 vectors for
  `""` to `"foobar"`. Crockford's bytes form uses the same bit grouping with another
  alphabet and no `=` padding, so these become Crockford vectors by a symbol for symbol
  swap (derived, and labelled so in the tests).

Consequences for the design: integers are zero-extended on the left (the number keeps its
value), bytes on the right (the RFC 4648 bit order, so leading zero bytes survive). The
check symbol is the value of the symbol string mod 37 in both cases, so
`decode_int(code, check=True)` accepts any checked code. A strict decoder is the only way
for "one value, one code" to hold.

## Ranked improvements

1. **Canonical bytes decoding.** Reject lengths that no byte string encodes to (1, 3 or 6
   symbols mod 8) and a last symbol with non-zero pad bits, with a `CrockfordError` that says
   which. Every accepted string then re-encodes to its normalized self.
2. **One check symbol definition.** The check is the number the symbols spell, mod 37, for
   bytes and integers alike. Proven to catch every single wrong symbol and every adjacent
   transposition in the body, exhaustively on short codes and at random on long ones.
3. **Linear time.** Bytes go through the C base32 codec with a translated alphabet;
   integers through `int.to_bytes` and `int(text, 32)` after validation (power-of-two bases
   are exempt from the int string conversion limit). A test pins megabyte inputs.
4. **Honest types.** `encode` takes any bytes-like object; `encode_int` takes anything with
   `__index__` but not `bool`; non-`str` input to the decoders raises `TypeError`.
5. **`normalize(text, check=False)`.** The canonical upper-case, hyphen-free form of what
   someone typed, validated, so stored codes compare equal.
6. **`width` and `group`.** `encode_int(n, width=26)` left-pads with `0`;
   `group=4` inserts a hyphen every four symbols counted from the left, check symbol
   included (matches the fetched `base32-crockford` vectors).
7. **Contracts that bite.** Fetched golden vectors with their URLs, a bit-string reference
   model written from the spec text compared on seeded random inputs, the error detection
   proof, mypy on a snippet, README examples executed, installed wheel e2e, mutation runs.
8. **Docs and packaging.** README with runnable examples and the exact rules, CHANGELOG,
   classifiers, sdist without this file.

Left out on purpose: a command line tool (`python -c` covers one-offs and the library has
nothing to configure), a lenient mode that accepts non-zero pad bits, whitespace stripping
(callers decide what surrounds a code), and ULID generation (a different library).
