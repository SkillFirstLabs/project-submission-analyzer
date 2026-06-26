"""
Secure ZIP extraction service.

Security protections:
- Path traversal prevention (validates every member path)
- Zip bomb protection (checks uncompressed size + file count before extraction)
- Symlink escape prevention
- Dangerous file extension blocking
- Temp directory isolation with guaranteed cleanup
"""

import zipfile
import tempfile
import os
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Extensions that will never be extracted — executables, scripts, binaries
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".bat", ".cmd", ".sh", ".bash", ".zsh",
    ".ps1", ".psm1", ".psd1",                    # PowerShell
    ".vbs", ".js", ".jse", ".wsf", ".wsh",       # Windows script hosts
    ".msi", ".msp", ".msu", ".cab",              # Installers
    ".scr", ".pif", ".com", ".cpl",              # Windows executables
    ".jar",                                       # Java executables
    ".dmg", ".pkg",                               # macOS installers
    ".bin", ".elf",                               # Linux binaries
}

# Source/config extensions we actually want to analyze
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".scala",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".cs", ".go", ".rs", ".rb",
    ".php", ".swift", ".r", ".m", ".lua", ".pl", ".dart",
    ".html", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
    ".xml", ".gradle", ".pom",
    ".md", ".txt", ".rst",
    ".sql",
    ".ipynb",
    ".tf", ".hcl",                                # Terraform
    ".dockerfile", "",                            # Dockerfile (no extension)
}

# Directories that are ignored entirely (e.g. package/dependency folders)
IGNORED_DIR_NAMES = {
    "node_modules", ".git", ".svn", ".hg", ".venv", "venv", "env", ".env",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "eggs", ".eggs", ".dart_tool", ".gradle", "gradle", "bin", "obj",
    "target", "vendor", "pods", "bower_components", "jspm_packages"
}


class ZipExtractionError(Exception):
    """Raised for any ZIP extraction security or validation failure."""
    def __init__(self, message: str, code: str = "ZIP_ERROR"):
        super().__init__(message)
        self.code = code


class ExtractionResult:
    """Holds the temp directory and metadata after successful extraction."""

    def __init__(self, temp_dir: str, extracted_files: list[str],
                 skipped_files: list[dict]):
        self.temp_dir = temp_dir
        self.extracted_files = extracted_files   # relative paths
        self.skipped_files = skipped_files       # list of {path, reason}

    def cleanup(self) -> None:
        """Remove the temp directory and all its contents."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info("Cleaned up temp dir", extra={"temp_dir": self.temp_dir})
        except Exception as exc:
            logger.warning(f"Failed to clean up temp dir: {exc}",
                           extra={"temp_dir": self.temp_dir})


def _is_safe_path(base: Path, target: Path) -> bool:
    """Return True if target resolves to a path inside base."""
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _check_zip_bomb(zf: zipfile.ZipFile, settings=None) -> None:
    """
    Inspect ZIP metadata for zip bomb characteristics.
    Raises ZipExtractionError if limits exceeded.
    """
    if settings is None:
        settings = get_settings()
    total_uncompressed = 0
    file_count = 0

    for info in zf.infolist():
        # Skip directories
        if info.filename.endswith("/"):
            continue

        file_count += 1
        total_uncompressed += info.file_size

        if file_count > settings.max_file_count:
            raise ZipExtractionError(
                f"ZIP contains more than {settings.max_file_count} files. "
                "Possible zip bomb or oversized archive.",
                code="ZIP_TOO_MANY_FILES"
            )

        if total_uncompressed > settings.max_uncompressed_size_bytes:
            raise ZipExtractionError(
                f"ZIP uncompressed size exceeds "
                f"{settings.max_uncompressed_size_mb}MB limit. "
                "Possible zip bomb.",
                code="ZIP_BOMB_DETECTED"
            )


def extract_zip(zip_bytes: bytes) -> ExtractionResult:
    """
    Safely extract a ZIP archive to a temporary directory.

    Steps:
    1. Validate it is a real ZIP
    2. Check for zip bomb via metadata
    3. Create isolated temp directory
    4. Validate every member path (path traversal + symlink check)
    5. Extract only allowed file types
    6. Return ExtractionResult — caller MUST call .cleanup()

    Raises ZipExtractionError on any security or validation failure.
    """
    settings = get_settings()

    # --- Step 1: Validate ZIP magic bytes ---
    if not zip_bytes[:4] == b"PK\x03\x04":
        raise ZipExtractionError(
            "Uploaded file is not a valid ZIP archive.",
            code="INVALID_ZIP"
        )

    import io
    try:
        zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ZipExtractionError(
            f"Corrupted or invalid ZIP archive: {exc}",
            code="INVALID_ZIP"
        ) from exc

    # --- Step 2: Zip bomb check (metadata only, nothing extracted yet) ---
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf_meta:
        _check_zip_bomb(zf_meta, settings)

    # --- Step 3: Create isolated temp directory ---
    temp_dir = tempfile.mkdtemp(prefix="submission_")
    base_path = Path(temp_dir).resolve()
    extracted_files: list[str] = []
    skipped_files: list[dict] = []

    logger.info("Starting ZIP extraction", extra={
        "temp_dir": temp_dir,
        "zip_size_bytes": len(zip_bytes)
    })

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for member in zf.infolist():
                member_path = member.filename

                # Skip directory entries
                if member_path.endswith("/"):
                    continue

                # --- Step 4a: Path traversal check ---
                # Normalize and resolve the target path
                target = (base_path / member_path).resolve()
                if not _is_safe_path(base_path, target):
                    logger.warning("Path traversal attempt blocked", extra={
                        "member": member_path,
                        "resolved": str(target)
                    })
                    skipped_files.append({
                        "path": member_path,
                        "reason": "Path traversal attempt blocked"
                    })
                    continue

                # --- Step 4b: Symlink check ---
                # zipfile.ZipInfo.external_attr encodes Unix file attributes
                # in upper 16 bits; 0xA000 mask = symlink
                unix_attrs = (member.external_attr >> 16) & 0xFFFF
                if unix_attrs & 0xA000 == 0xA000:
                    logger.warning("Symlink blocked in ZIP", extra={
                        "member": member_path
                    })
                    skipped_files.append({
                        "path": member_path,
                        "reason": "Symlink not allowed"
                    })
                    continue

                # --- Step 4bb: Ignored directory check ---
                path_parts = Path(member_path).parts
                if any(part.lower() in IGNORED_DIR_NAMES or part.endswith(".egg-info") for part in path_parts):
                    skipped_files.append({
                        "path": member_path,
                        "reason": "Ignored package/dependency directory"
                    })
                    continue

                # --- Step 4c: Extension check ---
                suffix = Path(member_path).suffix.lower()
                filename = Path(member_path).name.lower()

                if suffix in BLOCKED_EXTENSIONS:
                    logger.warning("Blocked extension skipped", extra={
                        "member": member_path,
                        "extension": suffix
                    })
                    skipped_files.append({
                        "path": member_path,
                        "reason": f"Blocked file extension: {suffix}"
                    })
                    continue

                # Only extract known source/config files
                # (Dockerfile has no extension, match by name)
                is_dockerfile = filename in {"dockerfile", "docker-compose.yml",
                                             "docker-compose.yaml"}
                if suffix not in ALLOWED_EXTENSIONS and not is_dockerfile:
                    skipped_files.append({
                        "path": member_path,
                        "reason": f"Unrecognized extension skipped: {suffix}"
                    })
                    continue

                # --- Step 4d: Per-file size check ---
                if member.file_size > settings.max_single_file_size_bytes:
                    skipped_files.append({
                        "path": member_path,
                        "reason": (
                            f"File too large: {member.file_size} bytes "
                            f"(limit {settings.max_single_file_size_mb}MB)"
                        )
                    })
                    continue

                # --- Step 5: Safe extraction ---
                # Ensure parent directory exists
                target.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member) as src, open(target, "wb") as dst:
                    # Stream in chunks to avoid large memory allocation
                    bytes_written = 0
                    for chunk in iter(lambda: src.read(65536), b""):
                        bytes_written += len(chunk)
                        # Double-check size during actual extraction
                        if bytes_written > settings.max_single_file_size_bytes:
                            dst.close()
                            os.remove(target)
                            skipped_files.append({
                                "path": member_path,
                                "reason": "File exceeded size limit during extraction"
                            })
                            break
                        dst.write(chunk)
                    else:
                        extracted_files.append(
                            str(Path(member_path))
                        )

        logger.info("ZIP extraction complete", extra={
            "extracted": len(extracted_files),
            "skipped": len(skipped_files),
            "temp_dir": temp_dir
        })

        return ExtractionResult(
            temp_dir=temp_dir,
            extracted_files=extracted_files,
            skipped_files=skipped_files
        )

    except ZipExtractionError:
        # Clean up before re-raising security errors
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Unexpected extraction error: {exc}")
        raise ZipExtractionError(
            f"Failed to extract ZIP: {exc}",
            code="EXTRACTION_FAILED"
        ) from exc
