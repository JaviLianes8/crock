"""The complete public promise: names, signatures, error types, docs and packaging facts."""

from __future__ import annotations

import doctest
import importlib.resources
import inspect
import pickle

import pytest

import crock
from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

# The public API. This list is the contract: the test below fails if the module disagrees.
PUBLIC_API: list[str] = [
    "CrockfordError",
    "decode",
    "decode_int",
    "encode",
    "encode_int",
    "normalize",
]

SIGNATURES = {
    "encode": "(data: 'Buffer', /, *, check: 'bool' = False, "
    "group: 'SupportsIndex | None' = None) -> 'str'",
    "decode": "(text: 'str', /, *, check: 'bool' = False) -> 'bytes'",
    "encode_int": "(n: 'SupportsIndex', /, *, check: 'bool' = False, "
    "width: 'SupportsIndex | None' = None, group: 'SupportsIndex | None' = None) -> 'str'",
    "decode_int": "(text: 'str', /, *, check: 'bool' = False) -> 'int'",
    "normalize": "(text: 'str', /, *, check: 'bool' = False) -> 'str'",
}


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(crock.__all__) == sorted(PUBLIC_API)
    public = sorted(name for name in vars(crock) if not name.startswith("_"))
    assert public == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in crock.__all__:
        assert hasattr(crock, name)


def test_version_is_one_zero_zero() -> None:
    assert crock.__version__ == "1.0.0"


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("crock").joinpath("py.typed").is_file()


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_function_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(crock, name))) == SIGNATURES[name]


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_the_first_argument_is_positional_only(name: str) -> None:
    first = next(iter(inspect.signature(getattr(crock, name)).parameters.values()))
    assert first.kind is inspect.Parameter.POSITIONAL_ONLY
    with pytest.raises(TypeError):
        getattr(crock, name)(**{first.name: "16J" if name != "encode_int" else 5})


@pytest.mark.parametrize("name", PUBLIC_API)
def test_every_public_name_has_a_docstring_with_examples_that_pass(name: str) -> None:
    obj = getattr(crock, name)
    tests = doctest.DocTestFinder(recurse=False).find(obj, name, globs=dict(vars(crock)))
    examples = sum(len(test.examples) for test in tests)
    assert examples >= 2, name
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    for test in tests:
        runner.run(test)
    assert runner.failures == 0, name


def test_the_module_docstring_has_passing_examples() -> None:
    result = doctest.testmod(crock)
    assert result.attempted >= 3
    assert result.failed == 0


def test_crockford_error_is_a_value_error_of_the_package() -> None:
    assert issubclass(CrockfordError, ValueError)
    assert CrockfordError.__module__ == "crock"
    assert repr(CrockfordError) == "<class 'crock.CrockfordError'>"
    error = CrockfordError("check symbol does not match")
    again = pickle.loads(pickle.dumps(error))
    assert (type(again), str(again)) == (CrockfordError, "check symbol does not match")
    assert b"_errors" not in pickle.dumps(error)


@pytest.mark.parametrize(
    "call",
    [
        lambda: decode("U"),
        lambda: decode("0"),
        lambda: decode("01"),
        lambda: decode("", check=True),
        lambda: decode("D1MGK", check=True),
        lambda: decode_int(""),
        lambda: decode_int("16JE", check=True),
        lambda: decode_int("16J!", check=True),
        lambda: encode_int(-1),
        lambda: normalize("a b"),
        lambda: normalize("16JE", check=True),
    ],
)
def test_bad_input_raises_crockford_error(call: object) -> None:
    with pytest.raises(CrockfordError):
        call()  # type: ignore[operator]


@pytest.mark.parametrize(
    "call",
    [
        lambda: encode_int(1, width=-1),
        lambda: encode_int(1, width=-(10**5000)),
        lambda: encode_int(1, width=10**30),
        lambda: encode_int(1, group=0),
        lambda: encode(b"x", group=-(10**5000)),
    ],
)
def test_bad_options_raise_a_plain_value_error_with_a_short_message(call: object) -> None:
    with pytest.raises(ValueError) as caught:
        call()  # type: ignore[operator]
    assert type(caught.value) is ValueError
    assert len(str(caught.value)) < 40


def test_every_function_returns_the_promised_type() -> None:
    assert type(encode(bytearray(b"a"), check=True, group=2)) is str
    assert type(decode("C4", check=False)) is bytes
    assert type(encode_int(7, check=True, width=3, group=1)) is str
    assert type(decode_int("7")) is int
    assert type(normalize("o")) is str

    class Text(str):
        pass

    assert type(normalize(Text("ab"))) is str
    assert type(normalize(Text("16jd"), check=True)) is str
    assert type(decode_int(Text("ab"))) is int
