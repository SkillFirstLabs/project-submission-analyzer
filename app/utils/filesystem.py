"""
Filesystem helper utilities for temporary directory creation and safe deletion.
"""

import shutil
import uuid
from pathlib import Path
from typing import Union

from app.config import get_logger

logger = get_logger("app.utils.filesystem")

# Define the root temp directory relative to the project root
TEMP_ROOT = Path("temp")


def create_temp_directory(prefix: str = "workspace_") -> Path:
    """
    Create a unique temporary workspace directory inside the root temp folder.
    
    Args:
        prefix: Prefix for the unique directory name.
        
    Returns:
        Path object pointing to the newly created directory.
    """
    unique_id = uuid.uuid4().hex
    workspace_dir = TEMP_ROOT / f"{prefix}{unique_id}"
    
    # Ensure the parent temp/ directory and the unique workspace exist
    workspace_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Created temporary workspace: %s", workspace_dir)
    return workspace_dir


def safe_delete_directory(path: Union[str, Path]) -> None:
    """
    Safely delete a directory and all of its contents.
    
    Args:
        path: Path to the directory to delete.
    """
    p = Path(path).resolve()
    
    # Ensure we are deleting something under our TEMP_ROOT for safety
    resolved_temp_root = TEMP_ROOT.resolve()
    
    if not p.exists():
        return
        
    if not p.is_dir():
        logger.warning("Attempted to delete path %s which is not a directory.", p)
        return

    # Security check: Ensure we only delete folders within the temp directory
    if not p.is_relative_to(resolved_temp_root):
        logger.warning(
            "Security Warning: Blocked recursive deletion of directory outside of temp root: %s", p
        )
        return

    try:
        shutil.rmtree(p)
        logger.info("Successfully deleted temporary workspace: %s", p)
    except Exception as e:
        logger.error("Failed to delete directory %s: %s", p, str(e))
