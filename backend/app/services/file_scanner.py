import os
from typing import List, Dict
from app.config import settings

def scan_project(temp_dir: str) -> List[Dict]:
    """
    Scans the temporary directory, applies include/exclude filters.
    Returns:
        List of dicts: {"path": str, "relative_path": str, "content": str, "extension": str, "filename": str}
    """
    files = []
    
    for root, dirs, filenames in os.walk(temp_dir):
        # Filter directories in-place to avoid descending into them
        dirs[:] = [d for d in dirs if d.lower() not in settings.SKIP_DIRS]
        
        for filename in filenames:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, temp_dir)
            
            ext = os.path.splitext(filename)[1].lower()
            name_lower = filename.lower()
            
            # Filter checks
            is_supported = ext in settings.SUPPORTED_EXTENSIONS
            is_special = name_lower in settings.ALWAYS_INCLUDE_NAMES
            
            if not (is_supported or is_special):
                continue
                
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
                
            if not content.strip():
                continue
                
            files.append({
                "path": full_path,
                "relative_path": relative_path,
                "content": content,
                "extension": ext,
                "filename": filename,
            })
            
    return files
