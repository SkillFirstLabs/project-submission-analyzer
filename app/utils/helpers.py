from pathlib import Path
from typing import Set

def generate_file_tree(path: Path, max_depth: int = 5, current_depth: int = 1) -> str:
    """Generates a text representation of the directory structure."""
    if not path.exists():
        return ""
    if current_depth > max_depth:
        return "  " * (current_depth - 1) + "... (max depth reached)\n"
    
    tree_str = ""
    try:
        # Sort so directories appear first, then files alphabetically
        items = sorted(list(path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
    except OSError:
        return "  " * (current_depth - 1) + "[Permission Denied]\n"
        
    for item in items:
        # Skip common folders and junk files to keep the context clean
        if item.name in (".git", "__pycache__", "node_modules", ".pytest_cache", ".venv", "venv", ".DS_Store", "target", "build", ".gradle", ".idea"):
            continue
            
        indent = "  " * (current_depth - 1)
        if item.is_dir():
            tree_str += f"{indent}📁 {item.name}/\n"
            tree_str += generate_file_tree(item, max_depth, current_depth + 1)
        else:
            tree_str += f"{indent}📄 {item.name}\n"
            
    return tree_str
