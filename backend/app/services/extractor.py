import os
import zipfile
import tempfile
import pathlib
from typing import Dict, Any

MAX_UNCOMPRESSED_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB limit
MAX_SNIPPET_LENGTH_CHARS = 1500  # Cap per file to avoid token bloat
MAX_TOTAL_FILES_TO_READ = 25

class ZipSafetyError(Exception):
    pass

def extract_and_analyze_zip(zip_path: str) -> Dict[str, Any]:
    # 1. Inspect zip file safely
    if not zipfile.is_zipfile(zip_path):
        raise ZipSafetyError("Uploaded file is not a valid zip archive.")

    file_tree = []
    dependencies = {}
    snippets = {}
    total_uncompressed_size = 0
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Check size first (Zip Bomb guard)
        for info in zf.infolist():
            total_uncompressed_size += info.file_size
            if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE_BYTES:
                raise ZipSafetyError("Zip file uncompressed size exceeds safety limit of 100MB.")
        
        # Safe extraction to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir).resolve()
            
            for member in zf.namelist():
                # Path traversal check
                target_path = (temp_path / member).resolve()
                try:
                    # check if target_path is relative to temp_path
                    target_path.relative_to(temp_path)
                except ValueError:
                    raise ZipSafetyError(f"Path traversal attempt detected in zip member: {member}")
                
                # Check for symlinks
                info = zf.getinfo(member)
                if (info.external_attr >> 16) & 0o120000 == 0o120000:  # Check if symlink
                    raise ZipSafetyError(f"Symlinks are not allowed: {member}")
            
            # If all safe, extract
            zf.extractall(path=temp_dir)
            
            # Scan files
            read_files_count = 0
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    full_path = (pathlib.Path(root) / file).resolve()
                    try:
                        rel_path = full_path.relative_to(temp_path).as_posix()
                    except ValueError:
                        continue # Skip if somehow not relative
                    file_size = full_path.stat().st_size
                    file_tree.append({"path": rel_path, "size": file_size})
                    
                    # Read dependencies
                    if file in ["requirements.txt", "package.json", "pyproject.toml"]:
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                dependencies[file] = f.read(5000)
                        except Exception:
                            pass
                    
                    # Get snippets for code files (limited count and size)
                    ext = full_path.suffix.lower()
                    if ext in [".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".go", ".rs", ".java", ".cpp", ".json"] and read_files_count < MAX_TOTAL_FILES_TO_READ:
                        # Exclude common bundle/dependency folders
                        if "node_modules" not in rel_path and ".git" not in rel_path and "venv" not in rel_path and "env" not in rel_path:
                            try:
                                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read(MAX_SNIPPET_LENGTH_CHARS)
                                    if content.strip():
                                        snippets[rel_path] = content
                                        read_files_count += 1
                            except Exception:
                                pass
            
    return {
        "file_tree": file_tree,
        "dependencies": dependencies,
        "snippets": snippets
    }
