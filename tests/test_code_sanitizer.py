"""
Tests for the static security scanner.
"""

import pytest
from app.services.code_sanitizer import scan_file, scan_project


def test_detects_eval():
    flags = scan_file("app.py", "result = eval(user_input)")
    assert any(f.severity == "high" for f in flags)
    assert any("eval" in f.description.lower() for f in flags)


def test_detects_exec():
    flags = scan_file("run.py", "exec(compile(code, '<string>', 'exec'))")
    assert len(flags) >= 1
    assert any(f.severity == "high" for f in flags)


def test_detects_subprocess():
    flags = scan_file("shell.py", "subprocess.run(['ls', '-la'])")
    assert any(f.severity == "high" for f in flags)


def test_detects_hardcoded_password():
    flags = scan_file("config.py", "password = 'super_secret_123'")
    assert any(f.severity == "high" for f in flags)


def test_detects_etc_passwd():
    flags = scan_file("hack.py", "open('/etc/passwd').read()")
    assert any(f.severity == "high" for f in flags)


def test_clean_file_has_no_high_flags():
    clean_code = """
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
"""
    flags = scan_file("calculator.py", clean_code)
    high_flags = [f for f in flags if f.severity == "high"]
    assert len(high_flags) == 0


def test_scan_project_summary():
    files = {
        "safe.py": "def hello(): return 'world'",
        "dangerous.py": "import subprocess\nsubprocess.run(['rm', '-rf', '/'])",
    }
    result = scan_project(files)
    assert result.has_high_severity
    assert "high" in result.summary.lower()


def test_scan_project_all_clean():
    files = {
        "main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "models.py": "from pydantic import BaseModel\nclass User(BaseModel): name: str",
    }
    result = scan_project(files)
    assert not result.has_high_severity
    assert "No security concerns" in result.summary


def test_line_number_captured():
    code = "x = 1\ny = eval(input())\nz = 3"
    flags = scan_file("test.py", code)
    eval_flags = [f for f in flags if "eval" in f.description.lower()]
    assert len(eval_flags) > 0
    assert eval_flags[0].line_number == 2


def test_scan_never_raises_on_bad_input():
    """Scanner must not raise exceptions on any input."""
    flags = scan_file("x.py", "\x00\xff\xfe binary garbage \x00")
    assert isinstance(flags, list)
