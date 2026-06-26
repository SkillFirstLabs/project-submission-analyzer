"""
Secure ZIP extraction service with validations for file sizes, counts, and path traversal (Zip Slip).
"""

import zipfile
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

from app.config import get_settings, get_logger
from app.scanner import constants

logger = get_logger("app.scanner.zip_extractor")


class ZipExtractor:
    """
    Secure ZIP extraction service that validates files before and during extraction.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_zip(self, upload_file: UploadFile, target_dir: Path) -> Path:
        """
        Securely validate and extract the uploaded ZIP file to a target workspace.
        
        Args:
            upload_file: FastAPI UploadFile object containing the uploaded ZIP.
            target_dir: Target directory path where the ZIP contents should be extracted.
            
        Returns:
            The absolute Path to the extraction directory.
            
        Raises:
            HTTPException: If the ZIP violates file constraints, has traversal paths, or is corrupt.
        """
        # 1. Validate total archive upload size
        try:
            # Seek to end to determine file size
            upload_file.file.seek(0, 2)
            file_size_bytes = upload_file.file.tell()
            upload_file.file.seek(0)
        except Exception as e:
            logger.error("Failed to determine upload file size: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_ZIP",
                        "message": "Failed to read the upload file size.",
                        "details": None,
                    }
                },
            )

        max_upload_size_bytes = self.settings.upload.max_upload_size_mb * 1024 * 1024
        if file_size_bytes > max_upload_size_bytes:
            logger.warning(
                "Upload ZIP size %d bytes exceeds maximum limit of %d MB",
                file_size_bytes,
                self.settings.upload.max_upload_size_mb,
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"Upload file exceeds maximum limit of {self.settings.upload.max_upload_size_mb} MB.",
                        "details": None,
                    }
                },
            )

        # 2. Parse ZIP archive headers
        try:
            zip_ref = zipfile.ZipFile(upload_file.file)
        except zipfile.BadZipFile as e:
            logger.warning("Corrupt or invalid ZIP archive uploaded: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_ZIP",
                        "message": "Uploaded file is not a valid or corrupt ZIP archive.",
                        "details": None,
                    }
                },
            )

        # 3. Perform pre-extraction ZIP bomb and limit checks
        try:
            # Filter info_list to ignore dependency/temporary directories/extensions early
            raw_info_list = zip_ref.infolist()
            info_list = [
                member for member in raw_info_list
                if not any(part in constants.IGNORED_DIRECTORIES for part in Path(member.filename).parts)
                and Path(member.filename).suffix.lower() not in constants.IGNORED_EXTENSIONS
            ]
            file_count = len(info_list)

            if file_count > self.settings.upload.max_extraction_files:
                logger.warning(
                    "Archive file count %d exceeds maximum limit of %d",
                    file_count,
                    self.settings.upload.max_extraction_files,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_ZIP",
                            "message": f"Archive contains {file_count} files, exceeding limit of {self.settings.upload.max_extraction_files}.",
                            "details": None,
                        }
                    },
                )

            total_uncompressed_bytes = 0
            max_file_size_bytes = self.settings.upload.max_file_size_mb * 1024 * 1024

            for member in info_list:
                total_uncompressed_bytes += member.file_size
                
                # Check individual uncompressed file size
                if member.file_size > max_file_size_bytes:
                    logger.warning(
                        "File %s uncompressed size exceeds limit of %d MB",
                        member.filename,
                        self.settings.upload.max_file_size_mb,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": {
                                "code": "INVALID_ZIP",
                                "message": (
                                    f"File '{member.filename}' in archive exceeds maximum "
                                    f"individual size limit of {self.settings.upload.max_file_size_mb} MB."
                                ),
                                "details": None,
                            }
                        },
                    )

            # Prevent uncompressed ZIP size expansion exceeding 5 times maximum upload limit
            max_uncompressed_bytes = max_upload_size_bytes * 5
            if total_uncompressed_bytes > max_uncompressed_bytes:
                logger.warning(
                    "Archive total uncompressed size %d bytes exceeds safety limit",
                    total_uncompressed_bytes,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_ZIP",
                            "message": "Archive total uncompressed size exceeds maximum safety limit.",
                            "details": None,
                        }
                    },
                )

            # 4. Safe member-by-member extraction (Zip Slip Prevention)
            resolved_target_dir = target_dir.resolve()

            for member in info_list:
                # Construct target path and resolve it to clean '../' segments
                target_path = Path(resolved_target_dir).joinpath(member.filename).resolve()

                # Ensure target path lies strictly within the target extraction workspace
                if not target_path.is_relative_to(resolved_target_dir):
                    logger.critical(
                        "Security Exception: Path traversal attempt blocked for file: %s",
                        member.filename,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": {
                                "code": "INVALID_ZIP",
                                "message": f"Path traversal attempt detected in ZIP file: {member.filename}",
                                "details": None,
                            }
                        },
                    )

                # Extract directory or file
                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    # Create parent folder structure if missing
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zip_ref.open(member) as source_stream, open(target_path, "wb") as target_file:
                        shutil.copyfileobj(source_stream, target_file)

            logger.info("Successfully extracted ZIP archive to %s", target_dir)
            return target_dir

        finally:
            zip_ref.close()
