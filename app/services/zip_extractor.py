import time
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple
from app.config import settings
from app.utils.helpers import generate_file_tree

class SafeZipExtractor:
    def __init__(self, zip_path: Path):
        self.zip_path = zip_path
        self.temp_dir: Path = None
        self.extracted_files: List[Path] = []
        self.extraction_time_ms = 0
        self.files_analyzed_count = 0

    def extract(self) -> Tuple[Path, List[Path], int, str]:
        """
        Safely extracts the ZIP file to a temporary directory with checks for:
        - Path traversal (Zip Slip)
        - ZIP Bomb (decompression ratio and absolute limits)
        - Empty or invalid zip format
        
        Returns:
            Tuple[temp_dir_path, list_of_extracted_files, extraction_time_ms, file_tree_str]
        """
        start_time = time.perf_counter()

        if not zipfile.is_zipfile(self.zip_path):
            raise ValueError("The uploaded file is not a valid ZIP file.")

        # Create safe temporary directory in workspace or standard temp path
        self.temp_dir = Path(tempfile.mkdtemp(prefix="projectiq_"))

        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                infolist = zip_ref.infolist()
                
                if not infolist:
                    raise ValueError("The ZIP file is empty.")

                total_uncompressed_size = 0
                total_compressed_size = 0

                # First pass: security checks
                for info in infolist:
                    total_uncompressed_size += info.file_size
                    total_compressed_size += info.compress_size

                    # Prevent Zip Slip / Path Traversal
                    normalized_name = info.filename.replace("\\", "/")
                    target_path = (self.temp_dir / normalized_name).resolve()

                    try:
                        # Verify target is nested under the temporary directory
                        target_path.relative_to(self.temp_dir)
                    except ValueError:
                        raise ValueError(f"Security violation: Path traversal detected in ZIP: {info.filename}")

                # Prevent Zip Bomb (uncompressed size limit)
                if total_uncompressed_size > settings.MAX_UNCOMPRESSED_SIZE_BYTES:
                    raise ValueError(
                        f"Security violation: ZIP decompressed size ({total_uncompressed_size / (1024*1024):.2f}MB) "
                        f"exceeds limit of {settings.MAX_UNCOMPRESSED_SIZE_BYTES / (1024*1024)}MB."
                    )

                # Prevent Zip Bomb (high compression ratio)
                if total_compressed_size > 0:
                    ratio = total_uncompressed_size / total_compressed_size
                    # Apply ratio check for non-trivial size zip files
                    if ratio > settings.MAX_COMPRESSION_RATIO and total_uncompressed_size > 1024 * 1024:
                        raise ValueError(
                            f"Security violation: ZIP compression ratio is too high ({ratio:.1f}x). Possible ZIP bomb."
                        )

                # Second pass: Perform actual extraction
                for info in infolist:
                    normalized_name = info.filename.replace("\\", "/")
                    target_path = (self.temp_dir / normalized_name).resolve()

                    if info.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(info) as source, open(target_path, "wb") as target:
                            while True:
                                chunk = source.read(64 * 1024)
                                if not chunk:
                                    break
                                target.write(chunk)
                        self.extracted_files.append(target_path)

        except Exception as e:
            self.cleanup()
            if isinstance(e, ValueError):
                raise e
            raise ValueError(f"Failed to safely extract ZIP file: {str(e)}")

        self.extraction_time_ms = int((time.perf_counter() - start_time) * 1000)

        # Filter and count files to analyze
        # Allowed source files and config/manifest files
        allowed_extensions = {".py", ".java", ".js", ".ts"}
        allowed_configs = {"requirements.txt", "package.json", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml"}

        self.files_analyzed_count = sum(
            1 for f in self.extracted_files
            if f.suffix in allowed_extensions or f.name in allowed_configs
        )

        file_tree = generate_file_tree(self.temp_dir)
        return self.temp_dir, self.extracted_files, self.extraction_time_ms, file_tree

    def cleanup(self):
        """Cleans up the temporary extraction directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
