"""Characters that fold to a symbol under case mapping or NFKC are refused, never folded."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

DECODERS: dict[str, Callable[..., object]] = {
    "decode": decode,
    "decode_int": decode_int,
    "normalize": normalize,
}

# Hand-picked: each turns into an accepted spelling under str.upper(), str.lower() or NFKC.
EXTRA = {
    "1": ["\u0131", "\u00b9"],  # dotless i (upper: I), superscript one (NFKC: 1)
    "S": ["\u017f"],  # long s (upper: S)
    "K": ["\u212a"],  # Kelvin sign (lower: k)
}

# Check values whose symbols are 1, K, S and the five check-only symbols.
CHECK_VALUES = [1, 19, 25, 32, 33, 34, 35, 36]


def _lookalikes(symbol: str) -> list[str]:
    # The fullwidth forms (U+FF01 to U+FF5E) fold back to ASCII under NFKC.
    found = [chr(ord(symbol) + 0xFEE0)]
    if symbol.isalpha():
        found.append(chr(ord(symbol.lower()) + 0xFEE0))
    return found + EXTRA.get(symbol, [])


def _folds_to(lookalike: str, symbol: str) -> bool:
    folded = {lookalike.upper(), lookalike.lower(), unicodedata.normalize("NFKC", lookalike)}
    spellings = {symbol, "I", "L"} if symbol == "1" else {symbol}
    return any(text.upper() in spellings for text in folded)


def _codes(name: str, check: bool) -> list[str]:
    if name == "decode":
        body = "1SKA1SKA"  # 40 bits: a valid bytes code
        if not check:
            return [body]
        return [encode(decode(body), check=True)] + [
            encode(value.to_bytes(5, "big"), check=True) for value in CHECK_VALUES
        ]
    if not check:
        return ["1SK9"]
    return [encode_int(value, check=True) for value in (decode_int("1SK"), *CHECK_VALUES)]


def _variants(code: str, lower: bool = False, hyphens: bool = False) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for index, symbol in enumerate(code):
        for lookalike in _lookalikes(symbol):
            # Spell the rest first: lower() would turn the Kelvin sign into a valid k.
            chars = [char.lower() if lower else char for char in code]
            chars[index] = lookalike
            found.append((("-" if hyphens else "").join(chars), lookalike))
    return found


def test_every_lookalike_folds_to_its_symbol() -> None:
    for name in DECODERS:
        for check in (False, True):
            for code in _codes(name, check):
                for symbol in code:
                    for lookalike in _lookalikes(symbol):
                        assert not lookalike.isascii(), lookalike
                        assert _folds_to(lookalike, symbol), (lookalike, symbol)


def test_the_codes_cover_body_and_check_positions() -> None:
    checked = _codes("decode", True) + _codes("decode_int", True)
    assert {code[-1] for code in checked} >= set("1KS*~$=U")
    for name in DECODERS:
        for check in (False, True):
            bodies = "".join(code[:-1] if check else code for code in _codes(name, check))
            assert set(bodies) >= set("1SK"), (name, check)


@pytest.mark.parametrize("check", [False, True])
@pytest.mark.parametrize("name", sorted(DECODERS))
def test_a_lookalike_anywhere_is_refused_by_name(name: str, check: bool) -> None:
    function = DECODERS[name]
    for code in _codes(name, check):
        function(code, check=check)  # the genuine code is accepted
        for text, lookalike in _variants(code):
            with pytest.raises(CrockfordError, match=re.escape(repr(lookalike))):
                function(text, check=check)


@pytest.mark.parametrize("check", [False, True])
@pytest.mark.parametrize("name", sorted(DECODERS))
def test_a_lookalike_is_refused_in_lower_case_and_grouped_codes(name: str, check: bool) -> None:
    function = DECODERS[name]
    for code in _codes(name, check):
        function(code.lower(), check=check)
        function("-".join(code), check=check)
        variants = _variants(code, lower=True) + _variants(code, hyphens=True)
        for text, lookalike in variants:
            with pytest.raises(CrockfordError, match=re.escape(repr(lookalike))):
                function(text, check=check)
