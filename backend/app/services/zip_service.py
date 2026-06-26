import os
import zipfile
import tempfile

def validate_zip(zip_file_path: str):
    if not zipfile.is_zipfile(zip_file_path):
        raise ValueError("Invalid zip file.")

def extract_zip_safe(zip_file_path: str) -> str:
    """
    Extracts ZIP file and returns the temp directory path.
    Prevents Zip Slip vulnerability by verifying resolved target path.
    """
    validate_zip(zip_file_path)
    temp_dir = tempfile.mkdtemp(prefix="project_scan_")
    
    with zipfile.ZipFile(zip_file_path, 'r') as zf:
        for member in zf.infolist():
            # Zip Slip check
            target_path = os.path.abspath(os.path.join(temp_dir, member.filename))
            if not target_path.startswith(os.path.abspath(temp_dir)):
                raise ValueError(f"Malicious ZIP entry detected: {member.filename}")
            zf.extract(member, temp_dir)
            
    return temp_dir

