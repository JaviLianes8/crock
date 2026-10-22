"""The rules of https://www.crockford.com/base32.html, read from the page as fetched.

The page is fetched by scripts/fetch_upstream.py (URL, date and sha256 in
tests/upstream/MANIFEST.json); these tests skip without it. Its two tables (value, decode
symbols, encode symbol) and its sentences are cut from the HTML, never retyped.
"""

from __future__ import annotations

import html
import itertools
import re

import pytest
from conftest import upstream_prose, upstream_text

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

PAGE = "crockford-base32.html"


def _rows() -> list[tuple[int, list[str], str]]:
    rows = []
    for row in re.findall(r"<tr>(.*?)</tr>", upstream_text(PAGE), flags=re.DOTALL):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(
            r"<td>(.*?)</td>", row, flags=re.DOTALL)]  # fmt: skip
        if len(cells) == 3:
            rows.append((int(cells[0]), cells[1].split(), cells[2]))
    return rows


def test_the_page_has_both_tables_complete() -> None:
    assert [value for value, _, _ in _rows()] == list(range(37))


def test_every_symbol_of_the_table_encodes_and_decodes() -> None:
    for value, spellings, symbol in _rows()[:32]:
        assert encode_int(value) == symbol
        for spelling in spellings:
            assert decode_int(spelling) == value
            assert normalize(spelling) == symbol


def test_the_table_lists_every_accepted_spelling_and_nothing_else() -> None:
    table = {spelling for _, spellings, _ in _rows()[:32] for spelling in spellings}
    for code in range(0x80):
        char = chr(code)
        if char in table:
            assert decode_int(char) >= 0
        elif char != "-":
            with pytest.raises(CrockfordError):
                decode_int(char)


def test_every_check_symbol_of_the_page_is_written_and_read() -> None:
    for value, spellings, symbol in _rows():
        number = 37 * 12345 + value
        assert encode_int(number, check=True) == encode_int(number) + symbol
        for spelling in spellings:
            assert decode_int(encode_int(number) + spelling, check=True) == number


def test_check_only_symbols_are_refused_outside_the_check_position() -> None:
    for _, spellings, _ in _rows()[32:]:
        for spelling in spellings:
            with pytest.raises(CrockfordError):
                decode_int("1" + spelling)
            with pytest.raises(CrockfordError):
                decode_int(spelling + "1", check=True)


def test_the_excluded_letters_are_the_ones_the_page_names() -> None:
    prose = upstream_prose(PAGE)
    match = re.search(r"We exclude 4 of the 26 letters: ([A-Z ]+?) \.", prose)
    assert match is not None
    excluded = match.group(1).split()
    assert excluded == ["I", "L", "O", "U"]
    symbols = "".join(symbol for _, _, symbol in _rows()[:32])
    assert set(symbols) == set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") - set(excluded)


def test_encoding_uses_upper_case_only_as_the_page_says() -> None:
    assert "When encoding, only upper case letters are used." in upstream_prose(PAGE)
    assert encode(bytes(range(256))).isupper()
    assert encode_int(2**200 - 1).isupper()


def test_numbers_are_zero_extended_to_a_multiple_of_five_bits() -> None:
    sentence = "zero-extend the number to make its bit-length a multiple of 5"
    assert sentence in upstream_prose(PAGE)
    for bits in range(1, 41):
        n = 1 << (bits - 1)
        assert len(encode_int(n)) == -(-bits // 5)
        assert decode_int(encode_int(n)) == n


def test_hyphens_are_ignored_during_decoding() -> None:
    assert "Hyphens are ignored during decoding." in upstream_prose(PAGE)
    for text in ("16J", "1-6-J", "-16J-", "1--6J"):
        assert decode_int(text) == 1234
        assert normalize(text) == "16J"
    assert decode("C-S-Q-P-Y-R-K-1-E-8") == b"foobar"


def test_the_check_symbol_is_the_number_modulo_37() -> None:
    assert "The check symbol encodes the number modulo 37" in upstream_prose(PAGE)
    checks = "".join(symbol for _, _, symbol in _rows())
    for n in itertools.chain(range(200), (2**64, 3**100, 37**20 - 1)):
        assert encode_int(n, check=True)[-1] == checks[n % 37]


def test_check_detects_wrong_symbol_and_transposed_symbol_errors() -> None:
    sentence = "This check symbol can be used to detect wrong-symbol and transposed-symbol errors."
    assert sentence in upstream_prose(PAGE)
    symbols = "".join(symbol for _, _, symbol in _rows()[:32])
    for body in map("".join, itertools.product(symbols, repeat=2)):
        code = encode_int(decode_int(body), check=True)[-1]
        swapped = body[::-1]
        if swapped != body:
            with pytest.raises(CrockfordError):
                decode_int(swapped + code, check=True)


def test_the_inline_copy_in_test_vectors_matches_the_page() -> None:
    from test_vectors import SPEC_CHECK_TABLE, SPEC_TABLE

    inline = [(value, spellings.split(), symbol) for value, spellings, symbol in SPEC_TABLE]
    inline += [(value, spellings.split(), symbol) for value, spellings, symbol in SPEC_CHECK_TABLE]
    assert inline == _rows()
