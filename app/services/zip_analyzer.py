import io
import zipfile
from pathlib import Path

from fastapi import HTTPException


# --------------------------------------------------
# ALLOWED SOURCE FILE TYPES
# --------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".json",
    ".txt",
    ".md",
    ".java",
    ".c",
    ".cpp"
}

SPECIAL_FILES = {
    "requirements.txt",
    "package.json",
    "readme.md"
}


# --------------------------------------------------
# ZIP SECURITY LIMITS
# --------------------------------------------------

MAX_FILES_IN_ZIP = 500
MAX_SINGLE_FILE_SIZE = (
    2 * 1024 * 1024
)
MAX_TOTAL_UNCOMPRESSED_SIZE = (
    50 * 1024 * 1024
)
MAX_COMPRESSION_RATIO = 100


# --------------------------------------------------
# ANALYZE ZIP
# --------------------------------------------------

def analyze_zip(zip_content: bytes):
    """
    Safely analyzes an uploaded ZIP file.

    Security checks:
    - Valid ZIP validation
    - Path traversal protection
    - Maximum file count
    - Maximum single file size
    - Maximum total uncompressed size
    - Suspicious compression ratio detection
    - Encrypted file rejection
    - Supported source file filtering

    Returns:
    - file_tree
    - source_files
    - files_analyzed
    """

    try:
        zip_buffer = io.BytesIO(
            zip_content
        )

        # -------------------------------------------
        # VALIDATE ZIP FORMAT
        # -------------------------------------------
        if not zipfile.is_zipfile(
            zip_buffer
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file is not "
                    "a valid ZIP file"
                )
            )

        zip_buffer.seek(0)

        file_tree = []
        source_files = {}

        # -------------------------------------------
        # OPEN ZIP FILE
        # -------------------------------------------
        with zipfile.ZipFile(
            zip_buffer,
            "r"
        ) as zip_file:
            zip_entries = (
                zip_file.infolist()
            )

            # ---------------------------------------
            # FILE COUNT PROTECTION
            # ---------------------------------------
            if (
                len(zip_entries)
                >
                MAX_FILES_IN_ZIP
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "ZIP file contains too "
                        "many files"
                    )
                )

            total_uncompressed_size = 0

            # ---------------------------------------
            # PROCESS FILES
            # ---------------------------------------
            for file_info in zip_entries:
                file_path = Path(
                    file_info.filename
                )

                # -----------------------------------
                # PATH TRAVERSAL PROTECTION
                # -----------------------------------
                if (
                    file_path.is_absolute()
                    or
                    ".." in file_path.parts
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Unsafe file path "
                            "detected: "
                            f"{file_info.filename}"
                        )
                    )

                # -----------------------------------
                # IGNORE DIRECTORIES
                # -----------------------------------
                if file_info.is_dir():
                    continue

                # -----------------------------------
                # ENCRYPTED FILE PROTECTION
                # -----------------------------------
                if file_info.flag_bits & 0x1:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Encrypted ZIP files "
                            "are not supported"
                        )
                    )

                # -----------------------------------
                # SINGLE FILE SIZE LIMIT
                # -----------------------------------
                if (
                    file_info.file_size
                    >
                    MAX_SINGLE_FILE_SIZE
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "File exceeds maximum "
                            "allowed size: "
                            f"{file_info.filename}"
                        )
                    )

                # -----------------------------------
                # TOTAL UNCOMPRESSED SIZE
                # -----------------------------------
                total_uncompressed_size += (
                    file_info.file_size
                )
                if (
                    total_uncompressed_size
                    >
                    MAX_TOTAL_UNCOMPRESSED_SIZE
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "ZIP extracted content "
                            "is too large"
                        )
                    )

                # -----------------------------------
                # COMPRESSION RATIO CHECK
                # -----------------------------------
                if (
                    file_info.compress_size > 0
                    and
                    file_info.file_size > 0
                ):
                    compression_ratio = (
                        file_info.file_size
                        /
                        file_info.compress_size
                    )
                    if (
                        compression_ratio
                        >
                        MAX_COMPRESSION_RATIO
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "Suspicious compression "
                                "ratio detected: "
                                f"{file_info.filename}"
                            )
                        )

                # -----------------------------------
                # ADD TO FILE TREE
                # -----------------------------------
                file_tree.append(
                    file_info.filename
                )

                extension = (
                    file_path.suffix.lower()
                )

                filename = (
                    file_path.name.lower()
                )

                # -----------------------------------
                # FILTER SOURCE FILES
                # -----------------------------------
                if (
                    extension
                    not in ALLOWED_EXTENSIONS
                    and
                    filename
                    not in SPECIAL_FILES
                ):
                    continue

                # -----------------------------------
                # READ FILE SAFELY
                # -----------------------------------
                try:
                    raw_content = zip_file.read(
                        file_info
                    )
                    content = raw_content.decode(
                        "utf-8",
                        errors="ignore"
                    )
                    source_files[
                        file_info.filename
                    ] = content
                except (
                    RuntimeError,
                    OSError,
                    UnicodeError
                ):
                    continue

        # -------------------------------------------
        # VALIDATE ZIP CONTENT
        # -------------------------------------------
        if not file_tree:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded ZIP file "
                    "is empty"
                )
            )

        if not source_files:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No supported source files "
                    "were found in the ZIP"
                )
            )

        # -------------------------------------------
        # RETURN ANALYSIS
        # -------------------------------------------
        return {
            "file_tree":
                file_tree,
            "source_files":
                source_files,
            "files_analyzed":
                len(source_files)
        }
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or corrupted ZIP file"
            )
        )
