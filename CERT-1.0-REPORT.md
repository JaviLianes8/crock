# crock 1.0.0 certification report

The 1.0.0 certification bar applied to crock. Nothing named `crock` is on PyPI (checked
2026-10-22: https://pypi.org/pypi/crock/json answers 404), so 1.0.0 is the first release
there and there is no upgrade path to check. Every change against 0.2.0 (the `main` branch)
is listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (7a1f090, version 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: sources fetched live, reference implementations run (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [x] Gates (item 15), final run
- [x] PR #3 and trace guard CLEAN; merge and publish left to the maintainer
- [x] QA round 1 findings fixed (lenses c and e), gates, matrix and mutations rerun at b4f8a3c
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: six names kept; first arguments made positional-only, signatures pinned; every change in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS: the package exposes exactly the six names (the stray `annotations` is gone) |
| 3 | Docstrings with runnable examples, doctests | PASS: every public name and the package docstring, 7 doctest items, README (4 blocks) and GUIDE (5 blocks) executed; the GUIDE shows each signature exactly as installed (pinned by a test) |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, typed consumer of the installed wheel; `typing.get_type_hints` resolves every public name at run time |
| 5 | Typed, documented, bounded errors | PASS: `CrockfordError` (a `ValueError`, reported as `crock.CrockfordError`), `TypeError`, plain `ValueError` for options; messages name at most one symbol |
| 6 | Contract tests of every public name | PASS: including NumPy booleans refused and non-ASCII lookalikes refused by every decoder, with and without `check` |
| 7 | Real ground truth | PASS: 5 files fetched with a hash manifest, 3 independent implementations run |
| 8 | Real e2e from the wheel | PASS: wheel and sdist built and inspected, wheel driven from an empty folder, typed consumer; no CLI; not on PyPI, so no upgrade |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12 (each with NumPy 1.26.4), 3.13.2, 3.14.2, 3.14.2 free-threaded |
| 11 | README and `twine check` | PASS: `twine check --strict`, absolute links, problem, verified comparison, GUIDE and CHANGELOG links |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-22 |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author rounds, 52 mutants at b4f8a3c, 51 killed, 1 equivalent |
| 19 | Five independent QA lenses | pending |

## Baseline on 0.2.0 (before any change)

Fresh clone of `main` at 7a1f090 on another machine, CPython 3.14.2: `ruff format --check .`,
`ruff check .` and `mypy --strict src tests` exit 0; `pytest` 235 passed, 1 skipped (the
installed-wheel test, which needs `CROCK_E2E=1`).

Defects found in 0.2.0 by reading and then reproducing:

- `encode_int(5, width=-10**5000)` raised `ValueError` from building its own message (the
  value is past the integer string conversion limit) instead of the intended message.
- `encode_int(5, width=10**20)` raised `OverflowError`, which is neither of the documented
  exception types.
- `CrockfordError` was reported and pickled as `crock._errors.CrockfordError`, a private
  module path.
- The package exposed a public `annotations` name (from a `__future__` import).
- No public docstring had a runnable example; there was no GUIDE; golden vectors were
  inline copies whose sources were not fetched in the run that checks them.

## API review (item 1)

Kept: the six public names, their option names, defaults and keyword-only options, the
symbols written and accepted, the check symbol rule and the exception types. Changed, all in
the CHANGELOG: the first argument of each function is positional-only (its name was never
documented and is now not a promise); the two option error defects above; the error class
reports as `crock.CrockfordError`; no stray `annotations`. Signatures are pinned by
`tests/test_contract.py`. Considered and left out: a `position` attribute on
`CrockfordError` (the message already names the symbol), a lenient decoding mode, whitespace
stripping and a command line tool (nothing to configure; `python -c` covers one-offs).

## Ground truth (item 7)

Fetched on 2026-10-22 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence, and
the tests check the hash before reading. Nothing fetched is committed or shipped.

- https://www.crockford.com/base32.html (`tests/test_spec_crockford.py`): both tables (37
  rows: value, decode spellings, encode symbol) are cut from the HTML and every row is
  checked in both directions; every ASCII character outside the table is refused; the
  excluded letters, the upper-case rule, zero-extension, hyphens, modulo 37 and the
  detection claim are each located as a sentence in the page and exercised.
- RFC 4648, https://www.rfc-editor.org/rfc/rfc4648.txt (`tests/test_spec_rfc4648.py`): the
  7 BASE32 and 7 BASE32-HEX vectors of section 10 and the alphabets of tables 3 and 4 are
  read from the text; the vectors are respelled in the Crockford alphabet (a derived
  mapping, labelled) and encoded and decoded.
- ULID specification at commit d0c7170 (`tests/test_spec_ulid.py`): the alphabet block, the
  largest ULID with its time value, and the example are cut from the README.
- base32-crockford at commit 1ffb602 (the module is byte for byte the one in the PyPI 0.3.0
  wheel): its test file is parsed with `ast` and all 21 assertions are translated to crock
  calls (`tests/test_upstream_suite.py`): 16 hold, 5 are deliberate differences (float
  truncation and the `strict` flag), asserted exactly. Its code, loaded from the fetched
  file, is compared on 9,000 seeded integers and 18,000 typed strings for decoding and
  12,000 for `normalize` (`tests/test_oracles.py`); the only differences are the ones listed
  in the GUIDE.
- python-ulid 4.0.1 (its own bit-twiddling base32): 9,000 random ULIDs, time parts and 80 bit
  randomness parts agree in both directions.
- base32-encode 2.0.0 and base32-decode 1.0.0 from npm, run with Node.js 24: 12,000 random
  byte strings encode identically; on 18,000 random typed strings, crock accepts exactly
  those whose npm-decoded bytes encode back to the normalized text, with the same bytes.
- The inline vectors of `tests/test_vectors.py` (kept so the suite has vectors without the
  fetched files) are checked against the fetched page, RFC and test file.

## Fuzz and hostile input (item 9)

`tests/test_fuzz.py`: four seeds of 5,000 hostile strings (near-alphabet, all ASCII, any code
point including lone surrogates, a valid code with one foreign character) through the three
decoders with and without `check`: only `CrockfordError`, messages under 80 characters;
normalization is idempotent and decoding a text equals decoding its normal form; bytes and
integers round trip with random `check`, `group` and `width` and the group sizes hold; one
changed symbol never passes the check. Eight hostile shapes (hyphens only, invalid first or
last symbol, non-ASCII, lone surrogates, aliases, hyphen pairs, a missing check symbol) at
32,768 and 524,288 characters through every decoder in both modes: cost grows linearly and
messages stay short. `tests/test_scaling.py` keeps the linear-time checks of the codecs.

## Author mutation round (item 18)

40 mutants, each applied alone to a copy of the tree at d66914f on another machine, the full
suite (fetched sources and all three reference implementations present) run with `-x`, a 300 s
per-test limit and bytecode caching disabled. 39 killed; M27 is equivalent. The first pass
(at 7da9662) left M13 and M30 alive; the contracts added in b389a01 kill them.

| Id | Mutation | Killed by |
| --- | --- | --- |
| M1 | two neighbouring symbols swapped in the alphabet | doctest `encode` |
| M2 | two check-only symbols swapped | `test_model::test_integers_match_the_model` |
| M3 | lower-case `l` alias dropped | `test_docs` (GUIDE example 0) |
| M4 | lower case not accepted in the body | package doctest |
| M5 | hyphens not removed | package doctest |
| M6 | symbol validation skipped | doctest `CrockfordError` |
| M7 | trailing hyphens kept before the check symbol | `test_check::test_missing_or_invalid_check_symbol_is_rejected` |
| M8 | lower-case check symbols refused | package doctest |
| M9 | check alias `o` read as 1 | `test_check::test_check_symbol_accepts_lower_case_and_aliases` |
| M10 | check verified mod 32 | package doctest |
| M11 | check symbol off by one | package doctest |
| M12 | modulus 36 instead of 37 | package doctest |
| M13 | error names a hyphen as the invalid symbol | `test_contract::test_the_message_names_the_first_invalid_symbol_never_a_hyphen` |
| M14 | length 6 mod 8 accepted | `test_bytes::test_lengths_no_byte_string_encodes_to_are_rejected` |
| M15 | pad bit mask one bit short | `test_bytes::test_every_last_symbol_with_non_zero_pad_bits_is_rejected` |
| M16 | one pad bit not checked | `test_bytes::test_every_last_symbol_with_non_zero_pad_bits_is_rejected` |
| M17 | wrong pad bit count in the bytes check value | doctest `decode` |
| M18 | little-endian bytes check value | doctest `decode` |
| M19 | bytes check over the raw value, padding ignored | doctest `decode` |
| M20 | `str` refusal message lost | `test_types::test_encode_of_str_says_to_encode_first` |
| M21 | `=` padding written | package doctest |
| M22 | wrong padding before the standard library decoder | package doctest |
| M23 | `bool` accepted as an integer | `test_types::test_encode_int_refuses_bool_float_and_text` |
| M24 | minus one accepted by `encode_int` | `test_contract::test_bad_input_raises_crockford_error` |
| M25 | leading zeros written | package doctest |
| M26 | empty integer code reaches `int()` | `test_check::test_empty_bytes_code_is_not_an_integer_code` |
| M27 | five extra zero bytes before stripping leading zeros | survived: equivalent (the extra symbols are all `0` and are stripped) |
| M28 | bytes check over the raw byte value (the 0.1.0 rule) | doctest `encode` |
| M29 | `width` pads on the right | doctest `encode_int` |
| M30 | width limit doubled | `test_contract::test_a_width_one_past_the_largest_string_length_is_refused` |
| M31 | `normalize` keeps the check symbol as typed | doctest `normalize` |
| M32 | `normalize` does not verify the check | `test_check::test_normalize_with_check_verifies_and_canonicalizes` |
| M33 | `group=0` reaches `range()` | `test_types::test_negative_width_and_non_positive_group_are_refused` |
| M34 | `width=-1` accepted | `test_contract::test_bad_options_raise_a_plain_value_error_with_a_short_message` |
| M35 | bytes decoder verifies the raw value | doctest `decode` |
| M36 | `decode_int` does not verify the check | doctest `decode_int` |
| M37 | first argument of `decode_int` accepted by name | `test_contract::test_function_signatures_are_pinned` |
| M38 | groups counted from the right | doctest `encode` |
| M39 | error reported from the private module | doctest `decode` |
| M40 | negative option quoted in the message | `test_contract::test_bad_options_raise_a_plain_value_error_with_a_short_message` |

Second round at b4f8a3c, after the QA round 1 fixes, same method on another machine with
CPython 3.14.2 and NumPy 2.5.4: M1 to M40 rerun (M23 adapted to the new boolean check,
still killed by `test_types::test_encode_int_refuses_bool_float_and_text`; every kill
above held, M27 still equivalent) plus twelve new mutants, all killed. M44 only changes
code that runs on Python 3.10 and 3.11, so it was run on CPython 3.10.19.

| Id | Mutation | Killed by |
| --- | --- | --- |
| M41 | NumPy 1.x booleans accepted as integers | `test_types::test_numpy_booleans_are_refused_like_bool` |
| M42 | NumPy boolean type name misspelt | `test_types::test_numpy_booleans_are_refused_like_bool` |
| M43 | `Buffer` defined only for the type checker (3.12 and later) | `test_contract::test_annotations_resolve_at_run_time[encode]` |
| M44 | run-time `Buffer` stand-in registers nothing (3.10 and 3.11) | `test_contract::test_annotations_resolve_at_run_time[encode]` on 3.10.19 |
| M45 | `decode` with `check` upper-cases with Unicode rules first | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode-True]` |
| M46 | `decode_int` with `check` lower-cases with Unicode rules first | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode_int-True]` |
| M47 | `normalize` with `check` upper-cases with Unicode rules first | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[normalize-True]` |
| M48 | `decode` keeps a Unicode case mapping that yields ASCII | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode-False]` |
| M49 | NFKC folding before every check split | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode-True]` |
| M50 | `decode` folds with NFKC | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode-False]` |
| M51 | `normalize` folds with NFKC | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[normalize-False]` |
| M52 | `decode_int` folds with NFKC | `test_lookalikes::test_a_lookalike_anywhere_is_refused_by_name[decode_int-False]` |

## QA round 1 findings and fixes (item 19)

Round 1 ran the five lenses at db158db. Findings fixed in b4f8a3c, each with a test:

- Robustness: under NumPy 1.x, `numpy.bool_` (not a `bool` subclass, but with `__index__`)
  was accepted as 0 or 1 for `n`, `width` and `group`, against the guide. It is now refused
  with the same `TypeError` as `bool`; tested with a stand-in of that type everywhere and
  with the real NumPy 1.26.4 and 2.5.4 scalars where installed.
- Robustness: `typing.get_type_hints(crock.encode)` raised `NameError` because `Buffer` only
  existed for the type checker. It now exists at run time (`collections.abc.Buffer` on 3.12
  and later, a small registered stand-in on 3.10 and 3.11); every public name is tested.
- Contract strength: nothing pinned that characters which fold to an accepted symbol under
  Unicode case mapping or NFKC (dotless i, long s, the Kelvin sign, superscript one, the
  fullwidth forms) are refused; the library refused them, but folding could be added
  without a test failing. `tests/test_lookalikes.py` now checks every decoder, with and
  without `check`, with the lookalike in every body and check position, in upper case,
  lower case and grouped codes, and that the message names the character.
- Docs: the guide wrote the signatures without the positional-only marker. They now match
  the installed signatures, which a test compares.

Both changes in behaviour are in the CHANGELOG.

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- Built from a fresh clone at b4f8a3c: `crock-1.0.0-py3-none-any.whl` (10,767 bytes, sha256
  ad77c4fa...) and `crock-1.0.0.tar.gz` (37,047 bytes, dea3de6e...); `twine check --strict`
  passes both. The wheel holds
  the six modules, `py.typed`, METADATA (Production/Stable, every requirement a `dev`
  extra), WHEEL, RECORD and `licenses/LICENSE`. The sdist holds the sources, tests, scripts,
  README, GUIDE, CHANGELOG, CONTRIBUTING, LICENSE and the upstream manifest only (no
  IMPROVEMENTS, no CERT files, no fetched files).
- `tests/test_e2e_wheel.py` (`CROCK_E2E=1`) builds both, checks those contents, installs the
  wheel in a fresh venv, runs a consumer program from an empty folder with `-I` (results,
  errors, pickling, positional-only, `7**100000` round trip) and type-checks a consumer
  with `mypy --strict` against the installed package. crock has no command line tool.
- Every interpreter version on this PC from `requires-python` up, at b4f8a3c on the build
  machine (the same CPython releases, installed there for the run), each installing the
  built wheel in a fresh venv and running the sdist's own suite with `src` removed (fetched
  files and all references present): CPython 3.10.19, 3.11.5 and 3.12.12 with NumPy 1.26.4,
  372 passed each; 3.13.2, 3.14.2 and 3.14.2 free-threaded without NumPy, 370 passed each;
  2 skipped everywhere (the two e2e tests, which need the source tree and ran with the
  gates). 3.8 and 3.9 are below `requires-python`.

## Gates (item 15)

At b4f8a3c on another machine, CPython 3.14.2 with NumPy 2.5.4, from a fresh clone with the
fetched sources, Node.js references and `CROCK_E2E=1`, each command on its own:
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests` and
`pytest` (381 passed, no skips) all exit 0.
