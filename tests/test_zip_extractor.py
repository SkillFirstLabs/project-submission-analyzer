"""
Tests for secure ZIP extraction.
Covers: path traversal, zip bomb, blocked extensions, symlinks, valid extraction.
"""

import io
import zipfile
import pytest
from app.services.zip_extractor import extract_zip, ZipExtractionError


def _make_zip(files: dict[str, bytes]) -> bytes:
    """Helper: create an in-memory ZIP with given {filename: content} pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_zip_extracts_python_files():
    zb = _make_zip({
        "main.py": b"print('hello')",
        "utils/helper.py": b"def add(a, b): return a + b",
        "README.md": b"# My Project",
    })
    result = extract_zip(zb)
    try:
        assert "main.py" in result.extracted_files
        assert any("helper.py" in f for f in result.extracted_files)
        assert len(result.skipped_files) == 0
    finally:
        result.cleanup()


# ---------------------------------------------------------------------------
# Security: path traversal
# ---------------------------------------------------------------------------

def test_path_traversal_blocked():
    zb = _make_zip({
        "../../../etc/passwd": b"root:x:0:0:root",
        "safe_file.py": b"x = 1",
    })
    result = extract_zip(zb)
    try:
        # The traversal file should be skipped, safe file extracted
        traversal_skipped = any(
            "../" in s["path"] or "passwd" in s["path"]
            for s in result.skipped_files
        )
        assert traversal_skipped
        assert "safe_file.py" in result.extracted_files
    finally:
        result.cleanup()


# ---------------------------------------------------------------------------
# Security: blocked extensions
# ---------------------------------------------------------------------------

def test_blocked_extension_skipped():
    zb = _make_zip({
        "malware.exe": b"MZ\x90\x00",
        "script.sh": b"#!/bin/bash\nrm -rf /",
        "app.py": b"import os",
    })
    result = extract_zip(zb)
    try:
        skipped_names = [s["path"] for s in result.skipped_files]
        assert any("malware.exe" in p for p in skipped_names)
        assert any("script.sh" in p for p in skipped_names)
        assert "app.py" in result.extracted_files
    finally:
        result.cleanup()


# ---------------------------------------------------------------------------
# Security: invalid ZIP
# ---------------------------------------------------------------------------

def test_invalid_zip_raises():
    with pytest.raises(ZipExtractionError) as exc_info:
        extract_zip(b"this is not a zip file at all")
    assert exc_info.value.code == "INVALID_ZIP"


def test_empty_bytes_raises():
    with pytest.raises(ZipExtractionError):
        extract_zip(b"")


# ---------------------------------------------------------------------------
# Security: zip bomb (metadata check)
# ---------------------------------------------------------------------------

def test_zip_bomb_too_many_files(monkeypatch):
    """Patch _check_zip_bomb directly to bypass lru_cache on get_settings."""
    from app.services import zip_extractor

    class MockSettings:
        max_file_count = 3
        max_uncompressed_size_mb = 500
        max_uncompressed_size_bytes = 500 * 1024 * 1024
        max_single_file_size_mb = 1
        max_single_file_size_bytes = 1 * 1024 * 1024

    # Patch get_settings inside the zip_extractor module
    monkeypatch.setattr(zip_extractor, "get_settings", lambda: MockSettings())

    # Create a zip with more than 3 files
    zb = _make_zip({f"file{i}.py": b"x = 1" for i in range(5)})

    with pytest.raises(ZipExtractionError) as exc_info:
        extract_zip(zb)
    assert exc_info.value.code == "ZIP_TOO_MANY_FILES"


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def test_cleanup_removes_temp_dir(tmp_path):
    zb = _make_zip({"hello.py": b"print('hi')"})
    result = extract_zip(zb)
    temp_dir = result.temp_dir
    import os
    assert os.path.exists(temp_dir)
    result.cleanup()
    assert not os.path.exists(temp_dir)


def test_package_directories_ignored():
    zb = _make_zip({
        "app.py": b"print('app')",
        "node_modules/express/index.js": b"// express code",
        "venv/bin/activate": b"# virtualenv activate",
        "package.json": b"{}",
    })
    result = extract_zip(zb)
    try:
        assert "app.py" in result.extracted_files
        assert "package.json" in result.extracted_files
        # The files inside node_modules and venv should be ignored
        assert not any("node_modules" in f for f in result.extracted_files)
        assert not any("venv" in f for f in result.extracted_files)
        # Verify they are logged in skipped files
        skipped_names = [s["path"] for s in result.skipped_files]
        assert any("node_modules/express/index.js" in p for p in skipped_names)
        assert any("venv/bin/activate" in p for p in skipped_names)
    finally:
        result.cleanup()
