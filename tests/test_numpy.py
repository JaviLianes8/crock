"""NumPy scalars: integers are accepted like int, booleans are refused like bool."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import pytest

from crock import encode, encode_int

Make = Callable[[int], object]


def shaped(module: str, name: str) -> Make:
    """A class with ``__index__`` that reports the given module and name, as NumPy scalars do."""

    class Scalar:
        def __init__(self, value: int) -> None:
            self.value = value

        def __index__(self) -> int:
            return int(self.value)

    Scalar.__module__ = module
    Scalar.__name__ = Scalar.__qualname__ = name
    return Scalar


# NumPy 1.x booleans are not bool subclasses, yet have __index__.
NUMPY_ONE_BOOL = shaped("numpy", "bool_")


def numpy_module() -> Any:
    try:
        return importlib.import_module("numpy")
    except ImportError:
        return None


def booleans() -> list[object]:
    found = [NUMPY_ONE_BOOL(True), NUMPY_ONE_BOOL(False)]
    numpy = numpy_module()
    return found if numpy is None else [*found, numpy.True_, numpy.False_]


def integer_types() -> list[Make]:
    found = [shaped("numpy", "int64"), shaped("numpy", "uint8"), shaped("mylib", "bool_")]
    numpy = numpy_module()
    if numpy is None:
        return found
    return [*found, numpy.int64, numpy.int32, numpy.uint16, numpy.uint64]


def name_of(make: Make) -> str:
    return f"{getattr(make, '__module__', '')}.{getattr(make, '__name__', '')}"


@pytest.mark.parametrize("value", booleans())
def test_numpy_booleans_are_refused_like_bool(value: Any) -> None:
    calls: list[Callable[[], object]] = [
        lambda: encode_int(value),
        lambda: encode_int(value, check=True),
        lambda: encode_int(5, width=value),
        lambda: encode(b"abc", group=value),
    ]
    for call in calls:
        with pytest.raises(TypeError, match=r"must be an integer, not bool$"):
            call()


@pytest.mark.parametrize("make", integer_types(), ids=name_of)
def test_numpy_integers_and_other_bool_named_types_are_accepted(make: Make) -> None:
    value: Any = make(234)
    assert encode_int(value) == "7A"
    assert encode_int(value, check=True) == "7AC"
    assert encode_int(5, width=make(3), group=make(2)) == "00-5"  # type: ignore[arg-type]
    assert encode(b"abc", group=make(2)) == encode(b"abc", group=2)  # type: ignore[arg-type]
