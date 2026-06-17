"""Tests for ba_tools/hashing.py shared sha256 helpers (Phase-2 Wave-0 scaffold).

These tests verify the three exported functions:
  _sha256_file(path: Path) -> str   — streaming sha256 of file bytes
  _statement_hash(text: str) -> str — sha256 of stripped/collapsed whitespace text (D-12)
  _sha256_str(text: str) -> str     — sha256 of UTF-8 encoded text

The module is the single source of truth for hashing imported by plan 03's
trace_cmd.py and index_cmd.py, avoiding circular-import risk (OpenCode MEDIUM).
"""

import hashlib
import tempfile
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test _sha256_file
# ---------------------------------------------------------------------------


def test_sha256_file(tmp_path):
    """_sha256_file(path) returns the hex sha256 of the file's bytes."""
    from ba_tools.hashing import _sha256_file

    content = b"The system shall maintain a REQ-ID traceability index.\n"
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    actual = _sha256_file(test_file)

    assert actual == expected, (
        f"_sha256_file mismatch: expected {expected!r}, got {actual!r}"
    )


def test_sha256_file_empty(tmp_path):
    """_sha256_file handles an empty file without error."""
    from ba_tools.hashing import _sha256_file

    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    expected = hashlib.sha256(b"").hexdigest()
    actual = _sha256_file(empty_file)

    assert actual == expected, (
        f"_sha256_file(empty) mismatch: expected {expected!r}, got {actual!r}"
    )


def test_sha256_file_binary_content(tmp_path):
    """_sha256_file handles binary content (non-text bytes)."""
    from ba_tools.hashing import _sha256_file

    binary_content = bytes(range(256))
    test_file = tmp_path / "binary.bin"
    test_file.write_bytes(binary_content)

    expected = hashlib.sha256(binary_content).hexdigest()
    actual = _sha256_file(test_file)

    assert actual == expected


# ---------------------------------------------------------------------------
# Test _statement_hash (D-12: strip + collapse internal whitespace, no case-fold)
# ---------------------------------------------------------------------------


def test_statement_hash_normalization_internal_whitespace():
    """_statement_hash collapses internal whitespace: 'a  b' == ' a b '."""
    from ba_tools.hashing import _statement_hash

    h1 = _statement_hash("a  b")
    h2 = _statement_hash(" a b ")
    assert h1 == h2, (
        f"Expected _statement_hash('a  b') == _statement_hash(' a b '); "
        f"got {h1!r} vs {h2!r}"
    )


def test_statement_hash_no_case_fold():
    """_statement_hash does NOT case-fold: 'a b' != 'A B' (D-12: no case-fold)."""
    from ba_tools.hashing import _statement_hash

    h_lower = _statement_hash("a b")
    h_upper = _statement_hash("A B")
    assert h_lower != h_upper, (
        f"_statement_hash must NOT case-fold: 'a b' and 'A B' should differ; "
        f"both got {h_lower!r}"
    )


def test_statement_hash_material_change_differs():
    """_statement_hash detects material changes: 'a b' != 'a c'."""
    from ba_tools.hashing import _statement_hash

    h1 = _statement_hash("a b")
    h2 = _statement_hash("a c")
    assert h1 != h2, (
        f"Expected _statement_hash('a b') != _statement_hash('a c'); "
        f"both got {h1!r}"
    )


def test_statement_hash_strips_leading_trailing():
    """_statement_hash strips leading/trailing whitespace."""
    from ba_tools.hashing import _statement_hash

    h1 = _statement_hash("  hello world  ")
    h2 = _statement_hash("hello world")
    assert h1 == h2, (
        f"Expected leading/trailing strip: got {h1!r} vs {h2!r}"
    )


def test_statement_hash_collapses_tabs_and_newlines():
    """_statement_hash collapses tabs and newlines as whitespace."""
    from ba_tools.hashing import _statement_hash

    h1 = _statement_hash("a\tb")
    h2 = _statement_hash("a b")
    assert h1 == h2, (
        f"Expected tab == space after normalization; got {h1!r} vs {h2!r}"
    )


# ---------------------------------------------------------------------------
# Test _sha256_str
# ---------------------------------------------------------------------------


def test_sha256_str():
    """_sha256_str(text) returns hex sha256 of the UTF-8 bytes of text."""
    from ba_tools.hashing import _sha256_str

    text = "The system shall maintain a REQ-ID traceability index."
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    actual = _sha256_str(text)

    assert actual == expected, (
        f"_sha256_str mismatch: expected {expected!r}, got {actual!r}"
    )


def test_sha256_str_unicode():
    """_sha256_str handles non-ASCII text using UTF-8 encoding."""
    from ba_tools.hashing import _sha256_str

    text = "Cần đoạn trạc năm 2025"  # Vietnamese
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    actual = _sha256_str(text)

    assert actual == expected


def test_sha256_str_empty():
    """_sha256_str handles empty string without error."""
    from ba_tools.hashing import _sha256_str

    expected = hashlib.sha256(b"").hexdigest()
    actual = _sha256_str("")

    assert actual == expected


# ---------------------------------------------------------------------------
# Module-level export contract
# ---------------------------------------------------------------------------


def test_hashing_module_exports():
    """ba_tools.hashing exports _sha256_file, _statement_hash, _sha256_str."""
    import ba_tools.hashing as hashing_mod

    assert hasattr(hashing_mod, "_sha256_file"), "ba_tools.hashing must export _sha256_file"
    assert hasattr(hashing_mod, "_statement_hash"), "ba_tools.hashing must export _statement_hash"
    assert hasattr(hashing_mod, "_sha256_str"), "ba_tools.hashing must export _sha256_str"
    assert callable(hashing_mod._sha256_file)
    assert callable(hashing_mod._statement_hash)
    assert callable(hashing_mod._sha256_str)


def test_hashing_module_no_llm_imports():
    """ba_tools/hashing.py must not import openai or anthropic (determinism boundary)."""
    import ast
    from pathlib import Path

    hashing_path = Path(__file__).parent.parent / "ba_tools" / "hashing.py"
    assert hashing_path.exists(), f"ba_tools/hashing.py not found at {hashing_path}"

    source = hashing_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    llm_imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                names = [node.module or ""]
            for name in names:
                if name and any(
                    pkg in name for pkg in ("openai", "anthropic", "langchain")
                ):
                    llm_imports.append(name)

    assert llm_imports == [], (
        f"ba_tools/hashing.py must not import LLM packages (determinism boundary); "
        f"found: {llm_imports}"
    )
