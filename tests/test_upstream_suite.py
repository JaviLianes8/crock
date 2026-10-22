"""Every assertion of the base32-crockford test file, run against crock.

The file is fetched by scripts/fetch_upstream.py from a pinned commit of
https://github.com/jbittel/base32-crockford (URL, date and sha256 in the manifest). Each
``assertEqual`` and ``assertRaises`` line is read from it and translated to the crock call
with the same meaning. The inline copies in test_vectors.py are checked against it too.
"""

from __future__ import annotations

import ast
import re
from typing import Any

import pytest
from conftest import upstream_text
from test_vectors import JBITTEL_ENCODE, JBITTEL_SPLIT

from crock import CrockfordError, decode_int, encode_int, normalize

# Where crock deliberately differs from the reference, by the source line of the assertion.
DIFFERENT = {
    # A float is refused with TypeError instead of being truncated.
    "self.assertEqual(b32.encode(4.2), '4')",
    # There is no strict mode: decoding always normalizes.
    "self.assertRaises(ValueError, b32.decode, '16j', strict=True)",
    "self.assertEqual(b32.decode('16J', strict=True), 1234)",
    "self.assertRaises(ValueError, b32.normalize, 'ix-Lb-Ko', strict=True)",
    "self.assertEqual(b32.normalize('1X1BK0', strict=True), '1X1BK0')",
}


def _assertions() -> list[str]:
    lines = upstream_text("jbittel-test.py").splitlines()
    return [line.strip() for line in lines if line.strip().startswith("self.assert")]


def _call(name: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
    if name == "encode":
        split = kwargs.pop("split", 0)
        check = kwargs.pop("checksum", False)
        assert not kwargs
        return encode_int(*args, check=check, group=split or None)
    if name == "decode":
        check = kwargs.pop("checksum", False)
        assert not kwargs
        return decode_int(*args, check=check)
    assert name == "normalize" and not kwargs
    return normalize(*args)


def _parse(line: str) -> tuple[str, str, list[Any], dict[str, Any], Any]:
    call = ast.parse(line).body[0]
    assert isinstance(call, ast.Expr) and isinstance(call.value, ast.Call)
    outer = call.value
    assert isinstance(outer.func, ast.Attribute)
    if outer.func.attr == "assertEqual":
        inner, expected = outer.args
        assert isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
        args = [ast.literal_eval(arg) for arg in inner.args]
        kwargs = {kw.arg or "": ast.literal_eval(kw.value) for kw in inner.keywords}
        return "equal", inner.func.attr, args, kwargs, ast.literal_eval(expected)
    assert outer.func.attr == "assertRaises"
    error, function, *rest = outer.args
    assert isinstance(error, ast.Name) and isinstance(function, ast.Attribute)
    kwargs = {kw.arg or "": ast.literal_eval(kw.value) for kw in outer.keywords}
    return "raises", function.attr, [ast.literal_eval(arg) for arg in rest], kwargs, error.id


def test_the_file_has_the_expected_number_of_assertions() -> None:
    assert len(_assertions()) == 21


def test_every_assertion_holds_for_crock() -> None:
    checked = 0
    for line in _assertions():
        if line in DIFFERENT:
            continue
        kind, name, args, kwargs, expected = _parse(line)
        if kind == "equal":
            assert _call(name, args, kwargs) == expected, line
        else:
            raised = {"ValueError": ValueError, "TypeError": TypeError}[expected]
            with pytest.raises(raised):
                _call(name, args, kwargs)
        checked += 1
    assert checked == 21 - len(DIFFERENT)


def test_the_differences_are_the_documented_ones() -> None:
    assert set(_assertions()) >= DIFFERENT
    with pytest.raises(TypeError):
        encode_int(4.2)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        decode_int("16J", strict=True)  # type: ignore[call-arg]
    assert decode_int("16j") == 1234
    assert normalize("ix-Lb-Ko") == "1X1BK0"


def test_value_errors_are_crockford_errors() -> None:
    for text in ("u", "!", "\xe4"):
        with pytest.raises(CrockfordError):
            normalize(text)


def test_the_inline_copies_are_in_the_fetched_file() -> None:
    text = upstream_text("jbittel-test.py")
    for n, check, _, expected in JBITTEL_ENCODE:
        suffix = ", checksum=True" if check else ""
        assert f"b32.encode({n}{suffix}), '{expected}')" in text
    for n, group, expected in JBITTEL_SPLIT:
        assert re.search(rf"b32\.encode\({n}, split={group}\), '{expected}'\)", text)
