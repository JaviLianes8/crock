"""The ULID specification, read from the fetched README of https://github.com/ulid/spec.

A ULID is a 128 bit number written as 26 Crockford symbols: ``encode_int(n, width=26)``.
The alphabet, the largest ULID and its time part, and the example are cut from the text.
"""

from __future__ import annotations

import re

from conftest import upstream_text

from crock import decode_int, encode_int, normalize

README = "ulid-spec-README.md"


def test_the_ulid_alphabet_is_the_crockford_alphabet() -> None:
    text = upstream_text(README)
    block = text[text.index("Crockford's Base32 is used as shown.") :]
    alphabet = re.search(r"```\n([0-9A-Z]{32})\n```", block)
    assert alphabet is not None
    for value, symbol in enumerate(alphabet.group(1)):
        assert encode_int(value) == symbol
        assert decode_int(symbol) == value


def test_the_largest_ulid_and_its_time_part() -> None:
    match = re.search(
        r"the largest valid ULID encoded in Base32 is `([0-9A-Z]{26})`, which corresponds to "
        r"an epoch time of `(\d+)` or `2 \^ 48 - 1`",
        upstream_text(README),
    )
    assert match is not None
    largest, time = match.group(1), int(match.group(2))
    assert time == 2**48 - 1
    # Derived: the largest ULID is 2**128 - 1, its first 10 symbols the 48 bit time.
    assert decode_int(largest) == 2**128 - 1
    assert encode_int(2**128 - 1, width=26) == largest
    assert decode_int(largest[:10]) == time
    assert encode_int(time, width=10) == largest[:10]


def test_the_example_splits_into_time_and_randomness() -> None:
    match = re.search(r"\n ([0-9A-Z]{10}) +([0-9A-Z]{16})\n", upstream_text(README))
    assert match is not None
    time, randomness = match.groups()
    value = decode_int(time + randomness)
    assert value >> 80 == decode_int(time)
    assert value & (2**80 - 1) == decode_int(randomness)
    assert encode_int(value, width=26) == time + randomness
    assert normalize((time + randomness).lower()) == time + randomness
