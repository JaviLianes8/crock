"""Compare the codecs with a reference model written by hand from the spec text.

The model works on strings of bits, the slowest and most literal reading of
https://www.crockford.com/base32.html: 5 bits per symbol, numbers zero-extended to a multiple
of 5 bits, the check symbol being the number mod 37. Bytes are read as a big-endian bit
string and zero-extended on the right, as RFC 4648 groups them.
"""

from __future__ import annotations

import random

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CHECKS = SYMBOLS + "*~$=U"
ALIASES = {"O": "0", "I": "1", "L": "1"}


def model_symbols(bits: str) -> str:
    return "".join(SYMBOLS[int(bits[i : i + 5], 2)] for i in range(0, len(bits), 5))


def model_encode_int(n: int, check: bool) -> str:
    bits = format(n, "b")
    text = model_symbols(bits.zfill(-(-len(bits) // 5) * 5))
    return text + (CHECKS[n % 37] if check else "")


def model_encode(data: bytes, check: bool) -> str:
    bits = "".join(format(byte, "08b") for byte in data)
    text = model_symbols(bits.ljust(-(-len(bits) // 5) * 5, "0"))
    value = int(bits.ljust(len(text) * 5, "0") or "0", 2)
    return text + (CHECKS[value % 37] if check else "")


def model_normalize(text: str) -> str:
    out = ""
    for char in text.replace("-", ""):
        char = ALIASES.get(char.upper(), char.upper())
        if char not in SYMBOLS:
            raise ValueError(char)
        out += char
    return out


def model_decode(text: str) -> bytes | None:
    bits = "".join(format(SYMBOLS.index(c), "05b") for c in model_normalize(text))
    whole, extra = divmod(len(bits), 8)
    if extra >= 5 or "1" in bits[8 * whole :]:
        return None
    return bytes(int(bits[i : i + 8], 2) for i in range(0, 8 * whole, 8))


@pytest.mark.parametrize("seed", range(4))
def test_integers_match_the_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(500):
        n = rng.getrandbits(rng.randrange(1, 200))
        check = rng.random() < 0.5
        expected = model_encode_int(n, check)
        assert encode_int(n, check=check) == expected
        assert decode_int(expected, check=check) == n


@pytest.mark.parametrize("seed", range(4))
def test_bytes_match_the_model(seed: int) -> None:
    rng = random.Random(100 + seed)
    for _ in range(500):
        data = rng.randbytes(rng.randrange(0, 40))
        check = rng.random() < 0.5
        expected = model_encode(data, check)
        assert encode(data, check=check) == expected
        assert decode(expected, check=check) == data


@pytest.mark.parametrize("seed", range(4))
def test_decoding_arbitrary_text_matches_the_model(seed: int) -> None:
    rng = random.Random(200 + seed)
    alphabet = SYMBOLS + SYMBOLS.lower() + "IiLlOo-uU!"
    for _ in range(2000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 14)))
        try:
            canonical = model_normalize(text)
        except ValueError:
            for function in (decode, decode_int, normalize):
                with pytest.raises(CrockfordError):
                    function(text)
            continue
        assert normalize(text) == canonical
        expected = model_decode(text)
        if expected is None:
            with pytest.raises(CrockfordError):
                decode(text)
        else:
            assert decode(text) == expected
        if canonical:
            assert decode_int(text) == int(
                "".join(format(SYMBOLS.index(c), "05b") for c in canonical), 2
            )
