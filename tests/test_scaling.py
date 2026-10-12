"""Cost grows linearly with input size: 16 times the input must not cost anywhere near 256 times."""

from __future__ import annotations

import time
from collections.abc import Callable

import pytest

from crock import decode, decode_int, encode, encode_int

SMALL = 1 << 13
FACTOR = 16
# Linear is FACTOR; quadratic would be FACTOR squared. The bound sits well between the two so
# a loaded machine does not fail it and a quadratic regression cannot pass it.
LIMIT = 4 * FACTOR


def _best(run: Callable[[], object]) -> float:
    timings = []
    for _ in range(3):
        start = time.perf_counter()
        run()
        timings.append(time.perf_counter() - start)
    return max(min(timings), 1e-4)


def _ratio(make: Callable[[int], Callable[[], object]]) -> float:
    return _best(make(SMALL * FACTOR)) / _best(make(SMALL))


@pytest.mark.parametrize(
    "make",
    [
        lambda size: lambda: encode(bytes(size), check=True),
        lambda size: lambda: decode("0" * (size // 5 * 8), check=False),
        lambda size: lambda: encode_int(1 << (8 * size), check=True),
        lambda size: lambda: decode_int("Z" * size, check=False),
    ],
    ids=["encode", "decode", "encode_int", "decode_int"],
)
def test_cost_is_linear(make: Callable[[int], Callable[[], object]]) -> None:
    assert _ratio(make) < LIMIT
