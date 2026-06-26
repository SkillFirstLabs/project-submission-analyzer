import io
import zipfile
from pathlib import Path
import pytest
from fastapi import HTTPException, UploadFile

from app.scanner.zip_extractor import ZipExtractor
from app.utils.filesystem import create_temp_directory, safe_delete_directory


def create_mock_zip(files_dict: dict) -> io.BytesIO:
    """Helper to create a ZIP archive in memory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            zip_file.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


def test_valid_zip_extraction():
    """Verify that a valid ZIP file is successfully extracted and verified."""
    zip_data = create_mock_zip({
        "main.py": "print('hello')",
        "utils/helper.py": "def help(): pass",
    })
    
    upload_file = UploadFile(file=zip_data, filename="project.zip")
    
    # Create target temp workspace
    target_dir = create_temp_directory(prefix="test_extract_")
    
    try:
        extractor = ZipExtractor()
        extracted_path = extractor.extract_zip(upload_file, target_dir)
        
        assert extracted_path == target_dir
        assert (target_dir / "main.py").exists()
        assert (target_dir / "utils" / "helper.py").exists()
        
        with open(target_dir / "main.py", "r") as f:
            assert f.read() == "print('hello')"
    finally:
        safe_delete_directory(target_dir)
        assert not target_dir.exists()


def test_zip_slip_rejection():
    """Verify that a ZIP file containing a path traversal member is rejected."""
    zip_data = create_mock_zip({
        "main.py": "print('hello')",
        "../outside.py": "malicious code",
    })
    
    upload_file = UploadFile(file=zip_data, filename="malicious.zip")
    target_dir = create_temp_directory(prefix="test_zip_slip_")
    
    try:
        extractor = ZipExtractor()
        with pytest.raises(HTTPException) as exc_info:
            extractor.extract_zip(upload_file, target_dir)
            
        assert exc_info.value.status_code == 400
        assert "Path traversal attempt detected" in exc_info.value.detail["error"]["message"]
        
        # Verify that the malicious file was NOT extracted outside target_dir
        outside_file = target_dir.parent / "outside.py"
        assert not outside_file.exists()
    finally:
        safe_delete_directory(target_dir)


def test_zip_file_count_limit(monkeypatch):
    """Verify that a ZIP with too many files is rejected."""
    zip_data = create_mock_zip({
        f"file_{i}.py": "pass" for i in range(10)
    })
    
    upload_file = UploadFile(file=zip_data, filename="many_files.zip")
    target_dir = create_temp_directory(prefix="test_count_limit_")
    
    # Lower the extraction limit for testing
    extractor = ZipExtractor()
    monkeypatch.setattr(extractor.settings.upload, "max_extraction_files", 5)
    
    try:
        with pytest.raises(HTTPException) as exc_info:
            extractor.extract_zip(upload_file, target_dir)
            
        assert exc_info.value.status_code == 400
        assert "exceeding limit of 5" in exc_info.value.detail["error"]["message"]
    finally:
        safe_delete_directory(target_dir)


def test_zip_file_size_limit(monkeypatch):
    """Verify that a ZIP with an oversized uncompressed file is rejected."""
    zip_data = create_mock_zip({
        "large_file.py": "x" * 2000,
    })
    
    upload_file = UploadFile(file=zip_data, filename="large_file.zip")
    target_dir = create_temp_directory(prefix="test_size_limit_")
    
    extractor = ZipExtractor()
    # Lower individual file size limit to 1 KB (0.00097 MB)
    monkeypatch.setattr(extractor.settings.upload, "max_file_size_mb", 0.00097)
    
    try:
        with pytest.raises(HTTPException) as exc_info:
            extractor.extract_zip(upload_file, target_dir)
            
        assert exc_info.value.status_code == 400
        assert "exceeds maximum individual size limit" in exc_info.value.detail["error"]["message"]
    finally:
        safe_delete_directory(target_dir)


def test_zip_extraction_ignores_directories_and_extensions():
    """Verify that ignored folders (node_modules, .venv) and ignored extensions are not extracted."""
    zip_data = create_mock_zip({
        "main.py": "print('hello')",
        "node_modules/express/index.js": "const express = require('express')",
        ".venv/bin/activate": "bash script",
        "nested/venv/file.txt": "some text",
        "archive.tmp": "temporary file",
        "bytecode.pyc": "bytecode",
    })
    
    upload_file = UploadFile(file=zip_data, filename="project_with_ignored.zip")
    target_dir = create_temp_directory(prefix="test_ignored_extract_")
    
    try:
        extractor = ZipExtractor()
        extracted_path = extractor.extract_zip(upload_file, target_dir)
        
        assert extracted_path == target_dir
        assert (target_dir / "main.py").exists()
        
        # Verify ignored paths/extensions do NOT exist on disk
        assert not (target_dir / "node_modules").exists()
        assert not (target_dir / ".venv").exists()
        assert not (target_dir / "nested" / "venv").exists()
        assert not (target_dir / "archive.tmp").exists()
        assert not (target_dir / "bytecode.pyc").exists()
    finally:
        safe_delete_directory(target_dir)
