"""The base32 and base32hex test vectors of RFC 4648 section 10, cut from the fetched text.

Crockford's bytes form uses the RFC 4648 bit grouping (big-endian, zero bits appended to the
last symbol) with its own alphabet and no ``=`` padding. The RFC vectors therefore become
Crockford vectors by spelling each 5 bit value in the Crockford alphabet: that mapping is
derived, the vectors themselves are read from https://www.rfc-editor.org/rfc/rfc4648.txt.
"""

from __future__ import annotations

import re

from conftest import upstream_text

from crock import decode, encode

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _vectors(name: str) -> list[tuple[bytes, str]]:
    found = re.findall(rf'^   {name}\("([a-z]*)"\) = "([A-Z0-9=]*)"$', upstream_text("rfc4648.txt"),
                       flags=re.MULTILINE)  # fmt: skip
    return [(data.encode("ascii"), code) for data, code in found]


def _alphabet(name: str) -> str:
    # Tables 3 and 4: rows of value and symbol pairs, "(pad) =" inside the last full row.
    text = upstream_text("rfc4648.txt")
    start = text.index(f"Table {3 if name == 'BASE32' else 4}: The ")
    pad = text.index("(pad)", start)
    table = text[start : text.index("\n\n", pad)]
    pairs = re.findall(r"(\d+) ([A-Z0-9])\b", table)
    return "".join(symbol for _, symbol in sorted(pairs, key=lambda pair: int(pair[0])))


def _crockford(code: str, alphabet: str) -> str:
    return "".join(CROCKFORD[alphabet.index(char)] for char in code.rstrip("="))


def test_the_rfc_tables_have_32_symbols() -> None:
    assert _alphabet("BASE32") == "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    assert _alphabet("BASE32-HEX") == "0123456789ABCDEFGHIJKLMNOPQRSTUV"


def test_base32_vectors_in_the_crockford_alphabet() -> None:
    vectors = _vectors("BASE32")
    assert [data for data, _ in vectors] == [b"", b"f", b"fo", b"foo", b"foob", b"fooba", b"foobar"]
    for data, code in vectors:
        expected = _crockford(code, _alphabet("BASE32"))
        assert encode(data) == expected
        assert decode(expected) == data
        assert decode(expected.lower()) == data


def test_base32hex_vectors_in_the_crockford_alphabet() -> None:
    vectors = _vectors("BASE32-HEX")
    assert len(vectors) == 7
    for data, code in vectors:
        expected = _crockford(code, _alphabet("BASE32-HEX"))
        assert encode(data) == expected
        assert decode(expected) == data


def test_the_padding_rules_of_the_rfc_match_the_lengths_crock_accepts() -> None:
    # Section 6: the final quantum is 8, 16, 24 or 32 bits, giving 2, 4, 5 or 7 symbols
    # followed by 6, 4, 3 or 1 "=" signs. Every other remainder is not an encoding.
    text = upstream_text("rfc4648.txt")
    assert "final unit of encoded output will be two characters followed by" in text
    lengths = {len(code.rstrip("=")) % 8 for _, code in _vectors("BASE32")}
    assert lengths == {0, 2, 4, 5, 7}
    for remainder in (1, 3, 6):
        try:
            decode("0" * remainder)
        except ValueError:
            continue
        raise AssertionError(remainder)


def test_the_inline_copy_in_test_vectors_matches_the_rfc() -> None:
    from test_vectors import RFC4648_BASE32

    assert _vectors("BASE32") == RFC4648_BASE32
