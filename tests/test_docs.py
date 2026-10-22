"""The README and GUIDE examples run and print what their comments say; metadata agrees."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import crock

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["README.md", "GUIDE.md"]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _blocks(name: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", _text(name), flags=re.DOTALL)


def _expected(block: str) -> list[str]:
    # Every line that prints carries the printed text as its comment.
    return [m.group(1) for m in re.finditer(r"print\(.*\)  # (.*)$", block, flags=re.MULTILINE)]


EXAMPLES = [(name, index) for name in DOCS for index in range(len(_blocks(name)))]


def test_each_document_has_examples() -> None:
    assert len(_blocks("README.md")) == 4
    assert len(_blocks("GUIDE.md")) >= 5


@pytest.mark.parametrize(("name", "index"), EXAMPLES)
def test_each_example_prints_its_comments(
    name: str, index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks(name)[index]
    expected = _expected(block)
    assert expected, block
    assert block.count("print(") == len(expected), block
    exec(compile(block, name, "exec"), {"__name__": "docs"})
    assert capsys.readouterr().out.splitlines() == expected


def test_every_public_name_appears_in_the_readme_and_the_guide() -> None:
    for name in crock.__all__:
        assert f"`{name}`" in _text("README.md"), name
        assert f"`{name}" in _text("GUIDE.md"), name


def _plain_signature(name: str) -> str:
    signature = inspect.signature(getattr(crock, name))
    bare = [param.replace(annotation=param.empty) for param in signature.parameters.values()]
    return str(signature.replace(parameters=bare, return_annotation=signature.empty))


@pytest.mark.parametrize("name", [name for name in crock.__all__ if name != "CrockfordError"])
def test_the_guide_shows_each_signature_as_installed(name: str) -> None:
    assert f"`{name}{_plain_signature(name)}`" in _text("GUIDE.md"), _plain_signature(name)


def test_links_in_the_readme_are_absolute() -> None:
    for target in re.findall(r"\]\(([^)]+)\)", _text("README.md")):
        assert target.startswith("https://"), target


def test_version_matches_pyproject() -> None:
    match = re.search(r'^version = "([^"]+)"$', _text("pyproject.toml"), flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == crock.__version__


def test_changelog_has_a_dated_entry_for_this_version() -> None:
    assert re.search(rf"^## \[{crock.__version__}\] - \d{{4}}-\d\d-\d\d$", _text("CHANGELOG.md"),
                     flags=re.MULTILINE)  # fmt: skip


def test_no_em_dash_in_any_shipped_text() -> None:
    files = [*ROOT.glob("*.md"), *ROOT.glob("src/**/*.py"), *ROOT.glob("tests/*.py")]
    files += [*ROOT.glob("scripts/*"), ROOT / "pyproject.toml"]
    for path in files:
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_every_source_file_stays_under_two_hundred_lines() -> None:
    for path in [*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/*")]:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path
