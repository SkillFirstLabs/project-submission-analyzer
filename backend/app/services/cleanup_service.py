import os
import shutil
from app.utils.logger import logger

def cleanup_project(temp_dir: str, temp_zip_path: str = None):
    """
    Deletes the extracted ZIP directory and the temporary ZIP file.
    """
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Successfully deleted temp directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error deleting temp directory {temp_dir}: {str(e)}")
            
    if temp_zip_path and os.path.exists(temp_zip_path):
        try:
            os.unlink(temp_zip_path)
            logger.info(f"Successfully deleted temp ZIP file: {temp_zip_path}")
        except Exception as e:
            logger.error(f"Error deleting temp ZIP file {temp_zip_path}: {str(e)}")
