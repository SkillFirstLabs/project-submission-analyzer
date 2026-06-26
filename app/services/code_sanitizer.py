"""
Static security scanner for uploaded source code.

This module NEVER executes code. It reads files as plain text and
pattern-matches against known dangerous constructs. Results are
surfaced in the report so mentors are aware of suspicious code.

Severity levels:
  high   — direct system access, code execution, network exfiltration
  medium — potentially dangerous but context-dependent
  low    — worth noting but commonly used legitimately
"""

import re
import os
from pathlib import Path
from dataclasses import dataclass, field

from app.models.schemas import SecurityFlag, SecurityScanResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class _Pattern:
    regex: str
    description: str
    severity: str  # "high" | "medium" | "low"


# ---------------------------------------------------------------------------
# Pattern catalog
# ---------------------------------------------------------------------------

# Python-specific dangerous patterns
_PYTHON_PATTERNS: list[_Pattern] = [
    _Pattern(r"\beval\s*\(", "eval() executes arbitrary code", "high"),
    _Pattern(r"\bexec\s*\(", "exec() executes arbitrary code", "high"),
    _Pattern(r"\b__import__\s*\(", "__import__() dynamic import", "high"),
    _Pattern(r"\bcompile\s*\(.*exec", "compile()+exec pattern", "high"),
    _Pattern(r"subprocess\.(run|call|Popen|check_output|getoutput)",
             "subprocess spawns OS processes", "high"),
    _Pattern(r"os\.(system|popen|execv|execve|execvp|spawnl|spawnle|fork)",
             "os module executing system commands", "high"),
    _Pattern(r"os\.remove|os\.unlink|shutil\.(rmtree|move|copy)",
             "File system modification", "medium"),
    _Pattern(r"open\s*\(\s*['\"]\/",
             "Opening file at absolute path (potential FS access)", "medium"),
    _Pattern(r"open\s*\(\s*['\"]\.\.\/",
             "Opening file with path traversal (../)", "high"),
    _Pattern(r"\bsocket\b", "Raw socket usage (possible network access)", "medium"),
    _Pattern(r"(urllib|requests|httpx|aiohttp)\.(get|post|put|delete|request|urlopen)",
             "Outbound HTTP request", "low"),
    _Pattern(r"pickle\.(loads|load)\s*\(",
             "pickle.loads() can execute arbitrary code", "high"),
    _Pattern(r"marshal\.loads\s*\(",
             "marshal.loads() unsafe deserialization", "high"),
    _Pattern(r"yaml\.load\s*\([^,)]*\)",
             "yaml.load() without Loader is unsafe", "medium"),
    _Pattern(r"ctypes\.(cdll|windll|CDLL)",
             "ctypes loads native libraries", "high"),
    _Pattern(r"importlib\.import_module\s*\(",
             "Dynamic module import", "medium"),
    _Pattern(r"__builtins__\[", "Direct builtins access", "high"),
    _Pattern(r"(\/etc\/passwd|\/etc\/shadow|\/etc\/hosts)",
             "Accessing sensitive system files", "high"),
    _Pattern(r"(PRIVATE KEY|BEGIN RSA|BEGIN EC)",
             "Hardcoded private key detected", "high"),
    _Pattern(r"(password|passwd|secret|api_key|token)\s*=\s*['\"][^'\"]{4,}['\"]",
             "Hardcoded credential", "high"),
]

# JavaScript/TypeScript dangerous patterns
_JS_PATTERNS: list[_Pattern] = [
    _Pattern(r"\beval\s*\(", "eval() executes arbitrary code", "high"),
    _Pattern(r"new\s+Function\s*\(", "new Function() executes arbitrary code", "high"),
    _Pattern(r"child_process\.(exec|spawn|execSync|spawnSync)",
             "child_process spawns OS commands", "high"),
    _Pattern(r"require\s*\(\s*['\"]child_process['\"]",
             "child_process module import", "high"),
    _Pattern(r"fs\.(unlink|rmdir|rm|writeFile|appendFile)\s*\(",
             "File system write/delete", "medium"),
    _Pattern(r"process\.env\b", "Accessing environment variables", "low"),
    _Pattern(r"__dirname|__filename",
             "Accessing filesystem paths", "low"),
    _Pattern(r"(\/etc\/passwd|\/etc\/shadow)",
             "Accessing sensitive system files", "high"),
]

# General patterns applied to all files
_GENERAL_PATTERNS: list[_Pattern] = [
    _Pattern(r"(password|passwd|secret|api_key|token)\s*[:=]\s*['\"][^'\"]{4,}['\"]",
             "Hardcoded credential", "high"),
    _Pattern(r"(PRIVATE KEY|BEGIN RSA|BEGIN EC|BEGIN CERTIFICATE)",
             "Hardcoded private key or certificate", "high"),
    _Pattern(r"\b(127\.0\.0\.1|localhost)\b",
             "Localhost reference (informational)", "low"),
]

_EXTENSION_PATTERN_MAP: dict[str, list[_Pattern]] = {
    ".py": _PYTHON_PATTERNS + _GENERAL_PATTERNS,
    ".js": _JS_PATTERNS + _GENERAL_PATTERNS,
    ".ts": _JS_PATTERNS + _GENERAL_PATTERNS,
    ".jsx": _JS_PATTERNS + _GENERAL_PATTERNS,
    ".tsx": _JS_PATTERNS + _GENERAL_PATTERNS,
}

_COMPILED_CACHE: dict[str, re.Pattern] = {}


def _get_compiled(pattern_str: str) -> re.Pattern:
    if pattern_str not in _COMPILED_CACHE:
        _COMPILED_CACHE[pattern_str] = re.compile(pattern_str, re.IGNORECASE)
    return _COMPILED_CACHE[pattern_str]


def scan_file(file_path: str, content: str) -> list[SecurityFlag]:
    """
    Scan a single file's content for dangerous patterns.
    Returns a list of SecurityFlag instances.
    Never raises — returns empty list on any error.
    """
    flags: list[SecurityFlag] = []
    ext = Path(file_path).suffix.lower()

    patterns = _EXTENSION_PATTERN_MAP.get(ext, _GENERAL_PATTERNS)

    try:
        lines = content.splitlines()
        for pattern_def in patterns:
            compiled = _get_compiled(pattern_def.regex)
            for line_no, line in enumerate(lines, start=1):
                if compiled.search(line):
                    flags.append(SecurityFlag(
                        file_path=file_path,
                        line_number=line_no,
                        pattern=pattern_def.regex,
                        severity=pattern_def.severity,
                        description=pattern_def.description,
                    ))
    except Exception as exc:
        logger.warning(f"Security scan failed for {file_path}: {exc}")

    return flags


def scan_project(
    file_contents: dict[str, str]
) -> SecurityScanResult:
    """
    Scan all files in the project.

    Args:
        file_contents: mapping of relative file path → file content string

    Returns:
        SecurityScanResult with all flags and summary.
    """
    all_flags: list[SecurityFlag] = []

    for file_path, content in file_contents.items():
        flags = scan_file(file_path, content)
        all_flags.extend(flags)

    has_high = any(f.severity == "high" for f in all_flags)
    high_count = sum(1 for f in all_flags if f.severity == "high")
    medium_count = sum(1 for f in all_flags if f.severity == "medium")
    low_count = sum(1 for f in all_flags if f.severity == "low")

    if not all_flags:
        summary = "No security concerns detected."
    else:
        summary = (
            f"{len(all_flags)} security pattern(s) found: "
            f"{high_count} high, {medium_count} medium, {low_count} low severity. "
            "Review flagged items before using this code in production."
        )

    logger.info("Security scan complete", extra={
        "total_flags": len(all_flags),
        "high": high_count,
        "medium": medium_count,
        "low": low_count,
    })

    return SecurityScanResult(
        flags=all_flags,
        has_high_severity=has_high,
        summary=summary,
    )
