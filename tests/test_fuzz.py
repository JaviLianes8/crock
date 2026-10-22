"""Seeded fuzz and property tests: no crash, only documented errors, short messages, round trips."""

from __future__ import annotations

import random
import time
from collections.abc import Callable

import pytest

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
NEAR = SYMBOLS + SYMBOLS.lower() + "IiLlOoUu-*~$=" + " \t\n_+!.\x00\x7f"
DECODERS: list[Callable[..., object]] = [decode, decode_int, normalize]


def _hostile(rng: random.Random) -> str:
    shape = rng.randrange(4)
    length = rng.randrange(0, 40)
    if shape == 0:
        return "".join(rng.choice(NEAR) for _ in range(length))
    if shape == 1:
        return "".join(chr(rng.randrange(0x80)) for _ in range(length))
    if shape == 2:
        # Any code point, lone surrogates included.
        return "".join(chr(rng.randrange(0x110000)) for _ in range(length))
    text = list(encode_int(rng.getrandbits(80), check=rng.random() < 0.5))
    text.insert(rng.randrange(len(text) + 1), chr(rng.randrange(0x80, 0x3000)))
    return "".join(text)


@pytest.mark.parametrize("seed", range(4))
def test_hostile_text_raises_only_crockford_error_with_a_short_message(seed: int) -> None:
    rng = random.Random(1000 + seed)
    for _ in range(5000):
        text = _hostile(rng)
        for function in DECODERS:
            for check in (False, True):
                try:
                    result = function(text, check=check)
                except CrockfordError as error:
                    assert len(str(error)) < 80, (text, str(error))
                    continue
                assert isinstance(result, (bytes, int, str))


@pytest.mark.parametrize("seed", range(4))
def test_accepted_text_normalizes_idempotently_and_decodes_the_same(seed: int) -> None:
    rng = random.Random(2000 + seed)
    for _ in range(5000):
        text = "".join(rng.choice(SYMBOLS + "ilo-ILO" + SYMBOLS.lower()) for _ in range(20))
        canonical = normalize(text)
        assert normalize(canonical) == canonical
        assert set(canonical) <= set(SYMBOLS)
        if canonical:
            assert decode_int(text) == decode_int(canonical)
        try:
            data = decode(text)
        except CrockfordError:
            with pytest.raises(CrockfordError):
                decode(canonical)
        else:
            assert decode(canonical) == data
            assert encode(data) == canonical


@pytest.mark.parametrize("seed", range(4))
def test_bytes_round_trip_with_every_option(seed: int) -> None:
    rng = random.Random(3000 + seed)
    for _ in range(3000):
        data = rng.randbytes(rng.randrange(0, 64))
        check = rng.random() < 0.5
        group = rng.choice([None, 1, 2, 3, 4, 5, 8, 100])
        code = encode(data, check=check, group=group)
        assert decode(code, check=check) == data
        assert decode(code.lower(), check=check) == data
        plain = code.replace("-", "")
        assert plain == encode(data, check=check)
        if group is not None:
            parts = code.split("-")
            assert all(len(part) == group for part in parts[:-1])
            assert 0 < len(parts[-1]) <= group or code == ""


@pytest.mark.parametrize("seed", range(4))
def test_integers_round_trip_with_every_option(seed: int) -> None:
    rng = random.Random(4000 + seed)
    for _ in range(3000):
        n = rng.getrandbits(rng.randrange(0, 400))
        check = rng.random() < 0.5
        width = rng.choice([None, 0, 1, 10, 26, 100])
        group = rng.choice([None, 1, 3, 4, 6])
        code = encode_int(n, check=check, width=width, group=group)
        assert decode_int(code, check=check) == n
        body = code.replace("-", "")[: -1 if check else None]
        assert len(body) == max(len(encode_int(n)), width or 0)


@pytest.mark.parametrize("seed", range(2))
def test_one_changed_or_swapped_symbol_never_passes_the_check(seed: int) -> None:
    rng = random.Random(5000 + seed)
    for _ in range(3000):
        n = rng.getrandbits(rng.randrange(1, 300))
        code = encode_int(n, check=True, width=rng.randrange(1, 12))
        body, symbol = code[:-1], code[-1]
        position = rng.randrange(len(body))
        other = rng.choice(SYMBOLS.replace(body[position], ""))
        with pytest.raises(CrockfordError):
            decode_int(body[:position] + other + body[position + 1 :] + symbol, check=True)


SHAPES: dict[str, Callable[[int], str]] = {
    "hyphens": lambda n: "-" * n,
    "invalid last": lambda n: "0" * n + "!",
    "invalid first": lambda n: "!" + "0" * n,
    "non-ascii last": lambda n: "a" * n + "\xe9",
    "lone surrogates": lambda n: "\ud800" * n,
    "aliases": lambda n: "iLoO" * (n // 4),
    "hyphen pairs": lambda n: "0-" * (n // 2),
    "check missing": lambda n: "-" * n + "!",
}


def _seconds(run: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        run()
        best = min(best, time.perf_counter() - start)
    return max(best, 1e-4)


def _attempt(function: Callable[..., object], text: str, check: bool) -> None:
    try:
        function(text, check=check)
    except CrockfordError as error:
        assert len(str(error)) < 80


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_hostile_shapes_cost_linear_time_and_keep_messages_short(shape: str) -> None:
    small, factor = 1 << 15, 16
    texts = [SHAPES[shape](small), SHAPES[shape](small * factor)]
    for function in DECODERS:
        for check in (False, True):
            short, long = (_seconds(_bound(function, text, check)) for text in texts)
            assert long / short < 4 * factor, (shape, function.__name__, check, long / short)


def _bound(function: Callable[..., object], text: str, check: bool) -> Callable[[], None]:
    return lambda: _attempt(function, text, check)
