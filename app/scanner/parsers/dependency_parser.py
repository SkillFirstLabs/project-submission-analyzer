"""
Dependency Parser: detects and parses project dependency manifest files.

Supports:
- requirements.txt  (Python pip)
- package.json      (Node.js npm/yarn)
- pom.xml           (Java Maven)
- go.mod            (Go modules)
- Pipfile           (Python pipenv)
- pyproject.toml    (Python poetry / PEP 517)
- Cargo.toml        (Rust cargo)
- Gemfile           (Ruby bundler)
- composer.json     (PHP composer)
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from app.config import get_logger
from app.models.evidence import DependencyEvidence
from app.scanner import constants

logger = get_logger("app.scanner.parsers.dependency_parser")


class DependencyParser:
    """
    Scans the workspace for known dependency manifest files and extracts
    package names + optional version strings.
    """

    def parse(self, workspace_dir: Path) -> List[DependencyEvidence]:
        """
        Walk the workspace, find any known manifest files, and parse them.

        Args:
            workspace_dir: Root of the extracted project workspace.

        Returns:
            Deduplicated list of DependencyEvidence objects.
        """
        seen: set = set()
        results: List[DependencyEvidence] = []

        import os

        file_paths = []
        for root, dirs, files in os.walk(workspace_dir):
            # Prune ignored directories in-place so os.walk doesn't traverse them
            dirs[:] = [d for d in dirs if d not in constants.IGNORED_DIRECTORIES]
            root_path = Path(root)
            for f in files:
                file_paths.append(root_path / f)

        for file_path in file_paths:
            relative = file_path.relative_to(workspace_dir)

            strategy = constants.DEPENDENCY_MANIFESTS.get(file_path.name)
            if not strategy:
                continue

            logger.info("Parsing dependency manifest: %s", relative)
            try:
                parsed = self._dispatch(strategy, file_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse %s: %s", relative, exc)
                parsed = []

            for dep in parsed:
                key = dep.name.lower()
                if key not in seen:
                    seen.add(key)
                    results.append(dep)

        logger.info("Dependency scan complete: %d unique dependencies found", len(results))
        return results

    # ------------------------------------------------------------------
    # Strategy dispatcher
    # ------------------------------------------------------------------

    def _dispatch(self, strategy: str, file_path: Path) -> List[DependencyEvidence]:
        dispatch_map = {
            "requirements_txt": self._parse_requirements_txt,
            "package_json": self._parse_package_json,
            "pom_xml": self._parse_pom_xml,
            "go_mod": self._parse_go_mod,
            "pipfile": self._parse_pipfile,
            "pyproject_toml": self._parse_pyproject_toml,
            "cargo_toml": self._parse_cargo_toml,
            "gemfile": self._parse_gemfile,
            "composer_json": self._parse_composer_json,
            "gradle": self._parse_gradle,
        }
        parser_fn = dispatch_map.get(strategy)
        if parser_fn:
            return parser_fn(file_path)
        return []

    # ------------------------------------------------------------------
    # Individual parsers
    # ------------------------------------------------------------------

    def _parse_requirements_txt(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse pip requirements.txt format."""
        deps = []
        version_re = re.compile(r"([a-zA-Z0-9_\-\.]+)\s*[=><!~^]+\s*([^\s;#,]+)")
        plain_re = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*$")

        for raw_line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            # Skip comments, blank lines, options, and extras
            if not line or line.startswith(("#", "-", "http://", "https://", "git+")):
                continue
            # Strip inline comments
            line = line.split("#")[0].strip()

            m = version_re.match(line)
            if m:
                deps.append(DependencyEvidence(name=m.group(1), version=m.group(2)))
                continue

            # No version specifier — package name only
            m2 = plain_re.match(line)
            if m2:
                deps.append(DependencyEvidence(name=m2.group(1), version=None))

        return deps

    def _parse_package_json(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Node.js package.json dependencies."""
        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        deps = []
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for name, version in data.get(section, {}).items():
                # Strip semver range specifiers (^, ~, >=, etc.)
                clean_version = re.sub(r"^[^0-9a-zA-Z]*", "", version) if version else None
                deps.append(DependencyEvidence(name=name, version=clean_version or None))
        return deps

    def _parse_pom_xml(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Maven pom.xml <dependency> blocks."""
        deps = []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Handle default Maven namespace
            ns_match = re.match(r"\{(.+?)\}", root.tag)
            ns = f"{{{ns_match.group(1)}}}" if ns_match else ""

            for dep in root.iter(f"{ns}dependency"):
                artifact_id = dep.findtext(f"{ns}artifactId")
                version = dep.findtext(f"{ns}version")
                if artifact_id:
                    deps.append(DependencyEvidence(name=artifact_id, version=version or None))
        except ET.ParseError as e:
            logger.warning("Failed to parse pom.xml: %s", e)
        return deps

    def _parse_go_mod(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Go go.mod require block."""
        deps = []
        in_require_block = False

        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()

            if stripped.startswith("require ("):
                in_require_block = True
                continue
            if in_require_block and stripped == ")":
                in_require_block = False
                continue

            # Single-line require
            if stripped.startswith("require ") and not stripped.endswith("("):
                parts = stripped[len("require "):].split()
                if parts:
                    deps.append(DependencyEvidence(name=parts[0], version=parts[1] if len(parts) > 1 else None))
                continue

            if in_require_block and stripped and not stripped.startswith("//"):
                parts = stripped.split()
                if len(parts) >= 2:
                    deps.append(DependencyEvidence(name=parts[0], version=parts[1]))

        return deps

    def _parse_pipfile(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Pipfile [packages] and [dev-packages] sections."""
        deps = []
        in_section = False
        version_re = re.compile(r'["\']?([^"\']+)["\']?\s*=\s*["\']?([^"\']+)["\']?')

        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped in ("[packages]", "[dev-packages]"):
                in_section = True
                continue
            if stripped.startswith("[") and stripped not in ("[packages]", "[dev-packages]"):
                in_section = False
                continue
            if in_section and stripped and not stripped.startswith("#"):
                m = version_re.match(stripped)
                if m:
                    name = m.group(1).strip()
                    version = m.group(2).strip() if m.group(2).strip() not in ("*", "") else None
                    deps.append(DependencyEvidence(name=name, version=version))

        return deps

    def _parse_pyproject_toml(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse pyproject.toml dependencies (PEP 517 and Poetry)."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                logger.warning("No TOML parser available; skipping pyproject.toml")
                return []

        deps = []
        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        version_re = re.compile(r"([a-zA-Z0-9_\-\.]+)")

        # PEP 517 / PEP 621 style
        for dep_str in data.get("project", {}).get("dependencies", []):
            m = version_re.match(dep_str.strip())
            if m:
                deps.append(DependencyEvidence(name=m.group(1), version=None))

        # Poetry style
        for name, spec in data.get("tool", {}).get("poetry", {}).get("dependencies", {}).items():
            if name.lower() == "python":
                continue
            version = spec if isinstance(spec, str) else None
            deps.append(DependencyEvidence(name=name, version=version))

        for name, spec in data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {}).items():
            version = spec if isinstance(spec, str) else None
            deps.append(DependencyEvidence(name=name, version=version))

        return deps

    def _parse_cargo_toml(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Rust Cargo.toml [dependencies] section."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                logger.warning("No TOML parser available; skipping Cargo.toml")
                return []

        deps = []
        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        for name, spec in data.get("dependencies", {}).items():
            if isinstance(spec, str):
                deps.append(DependencyEvidence(name=name, version=spec))
            elif isinstance(spec, dict):
                version = spec.get("version")
                deps.append(DependencyEvidence(name=name, version=version))

        return deps

    def _parse_gemfile(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Ruby Gemfile gem declarations."""
        deps = []
        gem_re = re.compile(r"""gem\s+['"]([^'"]+)['"]\s*(?:,\s*['"]([^'"]+)['"])?""")
        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = gem_re.search(line)
            if m:
                deps.append(DependencyEvidence(name=m.group(1), version=m.group(2) or None))
        return deps

    def _parse_composer_json(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse PHP composer.json require sections."""
        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        deps = []
        for section in ("require", "require-dev"):
            for name, version in data.get(section, {}).items():
                if name.lower() == "php":
                    continue
                deps.append(DependencyEvidence(name=name, version=version or None))
        return deps

    def _parse_gradle(self, file_path: Path) -> List[DependencyEvidence]:
        """Parse Gradle build.gradle dependency declarations (basic)."""
        deps = []
        dep_re = re.compile(
            r"""(?:implementation|api|compile|testImplementation|runtimeOnly)\s+['"]([^'"]+)['"]"""
        )
        for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = dep_re.search(line)
            if m:
                # Gradle notation: group:artifact:version
                parts = m.group(1).split(":")
                name = f"{parts[0]}:{parts[1]}" if len(parts) >= 2 else parts[0]
                version = parts[2] if len(parts) >= 3 else None
                deps.append(DependencyEvidence(name=name, version=version))
        return deps
