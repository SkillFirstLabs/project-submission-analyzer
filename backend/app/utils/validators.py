import os
import zipfile

def validate_zip_file(file_path: str):
    if not os.path.exists(file_path):
        raise ValueError("File does not exist.")
    
    if not zipfile.is_zipfile(file_path):
        raise ValueError("Uploaded file is not a valid ZIP archive.")

def validate_file_size(file_path: str):
    from app.config import settings
    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise ValueError(
            f"File exceeds maximum upload limit of {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB."
        )
