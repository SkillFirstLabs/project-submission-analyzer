import io
import os
import zipfile
import tempfile
import pytest

from utils.safe_zip import safe_extract_zip, UnsafeZipError, EmptyProjectError
from schemas import SuggestedSkill, AnalyzeResponse


def _make_zip(entries: dict) -> str:
    """entries: {path_in_zip: content_str}. Returns path to a temp zip file."""
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return path


def test_path_traversal_is_rejected():
    zpath = _make_zip({
        "../../etc/passwd": "root:x:0:0",
        "main.py": "print('hello')",
    })
    result = safe_extract_zip(zpath)
    # the traversal entry must never appear, the safe file should
    assert all("etc/passwd" not in f.path for f in result.files)
    assert any(f.path == "main.py" for f in result.files)
    os.remove(zpath)


def test_empty_zip_raises():
    zpath = _make_zip({})
    with pytest.raises(EmptyProjectError):
        safe_extract_zip(zpath)
    os.remove(zpath)


def test_blocked_dirs_are_skipped():
    zpath = _make_zip({
        "node_modules/lib/index.js": "module.exports = {}",
        "app/main.py": "import fastapi",
    })
    result = safe_extract_zip(zpath)
    assert all("node_modules" not in f.path for f in result.files)
    assert any(f.path == "app/main.py" for f in result.files)
    os.remove(zpath)


def test_non_zip_file_rejected():
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.write(fd, b"this is not a zip")
    os.close(fd)
    with pytest.raises(UnsafeZipError):
        safe_extract_zip(path)
    os.remove(path)


def test_suggested_skill_schema_bounds():
    with pytest.raises(Exception):
        SuggestedSkill(skill_id="sk-001", skill_name="Python", confidence=1.5, rationale="x")
    s = SuggestedSkill(skill_id="sk-001", skill_name="Python", confidence=0.9, rationale="Used in main.py")
    assert s.confidence == 0.9
