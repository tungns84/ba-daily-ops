"""
Shared SHA-256 helpers for ba-tools (Phase-2 Wave-0 extraction).

This module is the single source of truth for hashing across ba-tools commands.
Both trace_cmd.py and index_cmd.py (plan 03) import from here, avoiding the
circular-import risk of index_cmd importing _sha256_file from trace_cmd.

Review: OpenCode MEDIUM — extract shared hashing.py to avoid circular import
between trace_cmd and index_cmd (resolved here in Wave 1 / plan 01).

Determinism boundary: no ML/NLP imports; no model-client imports.
Pure stdlib (hashlib, re, pathlib) only.

Exports:
  _sha256_file(path: Path) -> str
      Streaming sha256 of file bytes. Uses hashlib.file_digest() (3.11+,
      per CLAUDE.md guidance) to avoid loading large binaries into memory.

  _statement_hash(text: str) -> str
      sha256 of normalized statement text (D-12: strip leading/trailing
      whitespace, collapse internal whitespace to single space, NO case-fold).
      Used to detect drift when a requirement's statement changes.

  _sha256_str(text: str) -> str
      sha256 of the UTF-8 bytes of `text`. Used for arbitrary string hashing
      (e.g., file path canonicalization, content-addressed keys).
"""

import hashlib
import re
from pathlib import Path


def _sha256_file(path: Path) -> str:
    """Return the hex sha256 digest of the file at *path*.

    Uses hashlib.file_digest() (Python 3.11+, per CLAUDE.md) for streaming
    hashing — avoids loading the entire file into memory for large binaries.

    Args:
        path: Path to the file to hash. Must exist and be readable.

    Returns:
        64-character lowercase hex string (sha256 digest).
    """
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _statement_hash(text: str) -> str:
    """Return the hex sha256 digest of a normalised requirement statement (D-12).

    Normalisation:
      1. Strip leading and trailing whitespace.
      2. Collapse all internal whitespace sequences (spaces, tabs, newlines)
         to a single space character.
      3. NO case-fold — 'Hello' and 'hello' produce different hashes.

    This is the canonical hash for requirement-drift detection: the same
    logical statement with minor whitespace differences produces the same hash,
    while a genuine rewrite produces a different hash.

    Args:
        text: The requirement statement text to hash.

    Returns:
        64-character lowercase hex string (sha256 digest).
    """
    normalised = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def _sha256_str(text: str) -> str:
    """Return the hex sha256 digest of the UTF-8 bytes of *text*.

    Unlike _statement_hash, this function applies NO normalisation — it hashes
    the text exactly as given. Use for arbitrary string keys (file paths,
    content-addressed identifiers, etc.).

    Args:
        text: The string to hash.

    Returns:
        64-character lowercase hex string (sha256 digest).
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
