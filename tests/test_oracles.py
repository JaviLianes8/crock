"""Independent implementations, run live, agree with crock on seeded random input.

- base32-crockford (jbittel), the reference integer codec: its source at a pinned commit is
  fetched by scripts/fetch_upstream.py (the same module as the PyPI 0.3.0 wheel) and loaded
  from tests/upstream after its sha256 is checked.
- python-ulid: its own bit-twiddling base32 for 16, 6 and 10 byte values.
- base32-encode and base32-decode from npm (Crockford variant), run with Node.js.

Each skips when its implementation is not present. Known differences are asserted exactly.
"""

from __future__ import annotations

import importlib.util
import json
import random
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from conftest import UPSTREAM, upstream_bytes

from crock import CrockfordError, decode, decode_int, encode, encode_int, normalize

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CHECK_ONLY = "*~$=U"
TYPED = SYMBOLS + SYMBOLS.lower() + "IiLlOo"


@pytest.fixture(scope="module")
def jbittel() -> ModuleType:
    upstream_bytes("jbittel-base32_crockford.py")
    spec = importlib.util.spec_from_file_location(
        "jbittel_base32_crockford", UPSTREAM / "jbittel-base32_crockford.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _outcome(function: Any, *args: object, **kwargs: object) -> object:
    try:
        result: object = function(*args, **kwargs)
    except ValueError:
        return ValueError
    return result


@pytest.mark.parametrize("seed", range(3))
def test_integers_encode_like_the_reference(jbittel: ModuleType, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(3000):
        n = rng.getrandbits(rng.randrange(1, 300)) or 1
        check = rng.random() < 0.5
        split = rng.choice([0, 0, 1, 2, 3, 4, 5, 8])
        expected = jbittel.encode(n, checksum=check, split=split)
        assert encode_int(n, check=check, group=split or None) == expected
        assert decode_int(expected, check=check) == n


def test_zero_differs_from_the_reference_only_when_split_into_groups_of_one(
    jbittel: ModuleType,
) -> None:
    for split in range(6):
        for check in (False, True):
            ours = encode_int(0, check=check, group=split or None)
            theirs = jbittel.encode(0, checksum=check, split=split)
            # The reference returns before splitting when the number is zero.
            assert ours == (theirs if (split, check) != (1, True) else "0-0")


@pytest.mark.parametrize("seed", range(3))
def test_typed_text_decodes_like_the_reference(jbittel: ModuleType, seed: int) -> None:
    rng = random.Random(10 + seed)
    alphabet = TYPED + "--" + CHECK_ONLY + "u!_ "
    for _ in range(6000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 12)))
        check = rng.random() < 0.5
        ours = _outcome(decode_int, text, check=check)
        theirs = _outcome(jbittel.decode, text, checksum=check)
        if ours is not ValueError:
            assert ours == theirs, text
        elif theirs is not ValueError:
            # Where the reference is more lenient: a check-only symbol read as a digit without
            # check=True, and an empty number before the check symbol.
            normal = jbittel.normalize(text)
            if check:
                assert len(normal) == 1, text
            else:
                assert normal[-1] in CHECK_ONLY, text


@pytest.mark.parametrize("seed", range(2))
def test_normalize_like_the_reference(jbittel: ModuleType, seed: int) -> None:
    rng = random.Random(20 + seed)
    for _ in range(6000):
        text = "".join(rng.choice(TYPED + "-" + CHECK_ONLY + "!") for _ in range(rng.randrange(9)))
        ours = _outcome(normalize, text)
        theirs = _outcome(jbittel.normalize, text)
        if ours is not ValueError and theirs is not ValueError:
            assert ours == theirs
        elif ours is not ValueError:
            assert ours == "", text  # the reference refuses an empty string
        elif theirs is not ValueError:
            assert isinstance(theirs, str) and theirs[-1] in CHECK_ONLY, text


@pytest.mark.parametrize("seed", range(3))
def test_ulids_match_python_ulid(seed: int) -> None:
    base32: Any = pytest.importorskip("ulid.base32")
    rng = random.Random(30 + seed)
    for _ in range(3000):
        raw = rng.randbytes(16)
        code = base32.encode(raw)
        assert encode_int(int.from_bytes(raw, "big"), width=26) == code
        assert decode_int(code.lower()).to_bytes(16, "big") == base32.decode(code) == raw
        assert encode_int(int.from_bytes(raw[:6], "big"), width=10) == code[:10]
        assert base32.encode_timestamp(raw[:6]) == code[:10]
        # 80 bits are 16 whole symbols, so the bytes form and the number form agree.
        assert encode(raw[6:]) == base32.encode_randomness(raw[6:]) == code[10:]
        assert decode(code[10:]) == raw[6:]


def _node(request: dict[str, list[str]]) -> dict[str, list[str | None]]:
    node = shutil.which("node")
    folder = UPSTREAM / "node_modules"
    if node is None or not (folder / "base32-encode").is_dir():
        pytest.skip("node or the base32-encode and base32-decode packages are missing")
    script = str(ROOT / "scripts" / "crockford_oracle.mjs")
    done = subprocess.run(
        [node, script, str(UPSTREAM)], input=json.dumps(request).encode(), capture_output=True
    )
    assert done.returncode == 0, done.stderr
    result: dict[str, list[str | None]] = json.loads(done.stdout)
    return result


@pytest.mark.parametrize("seed", range(3))
def test_bytes_encode_like_the_npm_packages(seed: int) -> None:
    rng = random.Random(40 + seed)
    data = [rng.randbytes(rng.randrange(0, 70)) for _ in range(4000)]
    answer = _node({"encode": [item.hex() for item in data], "decode": []})
    for item, code in zip(data, answer["encode"], strict=True):
        assert encode(item) == code
        assert decode(code or "") == item


@pytest.mark.parametrize("seed", range(3))
def test_crock_accepts_exactly_the_canonical_codes_the_npm_decoder_reads(seed: int) -> None:
    # The npm decoder ignores leftover bits; crock refuses any text whose bytes would not
    # encode back to it, so the two agree exactly on the texts crock accepts.
    rng = random.Random(50 + seed)
    texts = ["".join(rng.choice(TYPED) for _ in range(rng.randrange(0, 20))) for _ in range(6000)]
    answer = _node({"encode": [], "decode": texts})
    accepted = 0
    for text, hex_bytes in zip(texts, answer["decode"], strict=True):
        assert hex_bytes is not None, text
        theirs = bytes.fromhex(hex_bytes)
        if encode(theirs) == normalize(text):
            assert decode(text) == theirs
            accepted += 1
        else:
            with pytest.raises(CrockfordError):
                decode(text)
    assert accepted > 1000
