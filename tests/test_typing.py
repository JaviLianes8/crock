"""The public API is typed: mypy infers results and rejects bad calls."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
import crock
reveal_type(crock.encode(b"x"))
reveal_type(crock.decode("00"))
reveal_type(crock.encode_int(5, width=2, group=1))
reveal_type(crock.decode_int("5"))
reveal_type(crock.normalize("5"))
crock.encode("text")
crock.decode(b"00")
crock.encode_int("5")
crock.encode_int(5, True)
crock.decode_int("5", check="yes")
crock.encode(bytearray(b"x"), group=2)
crock.encode(memoryview(b"x"), check=True)
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


@pytest.mark.parametrize(
    ("line", "expected"),
    [(3, "str"), (4, "bytes"), (5, "str"), (6, "int"), (7, "str")],
)
def test_results_are_typed(mypy_output: str, line: int, expected: str) -> None:
    # Older mypy releases print the builtins prefix, newer ones do not.
    pattern = rf"snippet\.py:{line}: note: Revealed type is \"(builtins\.)?{expected}\""
    assert re.search(pattern, mypy_output), mypy_output


@pytest.mark.parametrize(
    ("line", "code"),
    [(8, "arg-type"), (9, "arg-type"), (10, "arg-type"), (11, "call-arg"), (12, "arg-type")],
)
def test_wrong_calls_are_rejected(mypy_output: str, line: int, code: str) -> None:
    assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def test_bytes_like_calls_are_accepted(mypy_output: str) -> None:
    assert not re.search(r"snippet\.py:1[34]: error", mypy_output), mypy_output
