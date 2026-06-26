import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any
import tempfile

def get_tmp_base() -> Path:
    """
    Get the base temporary directory. Fallback to system temp directory
    if the root '/tmp' is not writable (e.g. on Windows).
    """
    try:
        p = Path("/tmp")
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        return Path(tempfile.gettempdir())

def extract_zip(zip_path: str, job_id: str) -> List[str]:
    """
    Extract a ZIP file safely, validating uncompressed size and preventing path traversal.
    Skips node_modules, .git, __pycache__, and venv folders.
    Returns a list of all extracted absolute file paths.
    """
    path_zip = Path(zip_path)
    if not path_zip.exists():
        raise ValueError("ZIP file not found")
        
    extracted_paths = []
    tmp_base = get_tmp_base()
    extracted_dir = tmp_base / "extracted" / job_id
    extracted_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            infolist = zip_ref.infolist()
            if not infolist:
                raise ValueError("ZIP file is empty")
                
            # Validate total size and path safety
            total_size = 0
            max_size = 50 * 1024 * 1024  # 50 MB
            
            for info in infolist:
                # Path traversal validation
                if ".." in info.filename or info.filename.startswith("/") or info.filename.startswith("\\"):
                    raise ValueError("Unsafe ZIP: path traversal detected")
                    
                total_size += info.file_size
                if total_size > max_size:
                    raise ValueError("ZIP exceeds 50MB limit")
            
            # Extract files selectively
            skip_dirs = {"node_modules", ".git", "__pycache__", "venv"}
            
            for info in infolist:
                # Skip directories themselves, or files inside skipped folders
                parts = Path(info.filename).parts
                if any(p in skip_dirs for p in parts):
                    continue
                    
                if info.is_dir():
                    continue
                    
                # Extract file
                target_path = extracted_dir / info.filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zip_ref.open(info) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                    
                extracted_paths.append(str(target_path))
                
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")
        
    return extracted_paths

def get_file_tree(extracted_path: str) -> Dict[str, Any]:
    """
    Walk the extracted folder and return files, extensions count, readme flag, and concatenated source code.
    """
    ext_dir = Path(extracted_path)
    all_files = []
    extensions = {}
    has_readme = False
    source_code_parts = []
    
    allowed_source_exts = {".py", ".js", ".ts", ".html", ".css", ".java", ".cpp"}
    skip_dirs = {"node_modules", ".git", "__pycache__", "venv"}
    
    for root, dirs, files in os.walk(ext_dir):
        # Modify dirs in-place to skip walking skipped directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(ext_dir)
            all_files.append(str(relative_path))
            
            ext = file_path.suffix.lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
                
            if file.lower().startswith("readme"):
                has_readme = True
                
            # Concatenate source code content
            if ext in allowed_source_exts:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if content.strip():
                            source_code_parts.append(f"=== {relative_path} ===\n{content}")
                except Exception:
                    pass
                    
    # Combine and limit total source_code to 8000 characters
    source_code = "\n\n".join(source_code_parts)
    if len(source_code) > 8000:
        source_code = source_code[:8000]
        
    return {
        "all_files": all_files,
        "extensions": extensions,
        "has_readme": has_readme,
        "total_files": len(all_files),
        "source_code": source_code
    }

def cleanup(extracted_path: str):
    """
    Recursively delete the extracted folder.
    """
    try:
        p = Path(extracted_path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
    except Exception as e:
        print(f"Cleanup warning: {e}")
