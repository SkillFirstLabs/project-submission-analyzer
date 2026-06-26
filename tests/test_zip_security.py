import os
import zipfile
import tempfile
import pytest
from pathlib import Path
from app.services.zip_extractor import SafeZipExtractor
from app.config import settings

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_valid_zip_extraction(temp_dir):
    # Create a valid zip file
    zip_path = temp_dir / "valid.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("app/main.py", "print('hello')")
        z.writestr("requirements.txt", "fastapi\n")
        
    extractor = SafeZipExtractor(zip_path)
    extracted_dir, files, extract_time, tree = extractor.extract()
    
    try:
        assert extracted_dir.exists()
        assert len(files) == 2
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "requirements.txt" for f in files)
        assert extractor.files_analyzed_count == 2
        assert "main.py" in tree
        assert "requirements.txt" in tree
    finally:
        extractor.cleanup()

def test_invalid_zip_format(temp_dir):
    # Write some garbage to a file
    garbage_path = temp_dir / "garbage.zip"
    garbage_path.write_text("not a zip file at all")
    
    extractor = SafeZipExtractor(garbage_path)
    with pytest.raises(ValueError, match="not a valid ZIP file"):
        extractor.extract()

def test_empty_zip_rejection(temp_dir):
    zip_path = temp_dir / "empty.zip"
    # Create an empty zip file
    with zipfile.ZipFile(zip_path, "w") as z:
        pass
        
    extractor = SafeZipExtractor(zip_path)
    with pytest.raises(ValueError, match="The ZIP file is empty"):
        extractor.extract()

def test_zip_slip_path_traversal(temp_dir):
    zip_path = temp_dir / "path_traversal.zip"
    
    # Create a zip containing a path traversal entry
    # Note: zipfile.write normally cleans up leading path traversals,
    # but we can write custom file headers or use zipfile.ZipInfo
    with zipfile.ZipFile(zip_path, "w") as z:
        info = zipfile.ZipInfo("../traversal.py")
        z.writestr(info, "print('malicious')")
        
    extractor = SafeZipExtractor(zip_path)
    with pytest.raises(ValueError, match="Security violation: Path traversal detected"):
        extractor.extract()

def test_zip_bomb_uncompressed_limit(temp_dir, monkeypatch):
    zip_path = temp_dir / "bomb_size.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("huge.txt", "x" * 100)  # 100 bytes
        
    # Mock settings size limit to 50 bytes
    monkeypatch.setattr(settings, "MAX_UNCOMPRESSED_SIZE_BYTES", 50)
    
    extractor = SafeZipExtractor(zip_path)
    with pytest.raises(ValueError, match="exceeds limit"):
        extractor.extract()

def test_zip_bomb_compression_ratio(temp_dir, monkeypatch):
    zip_path = temp_dir / "bomb_ratio.zip"
    
    # Writing a highly repetitive string makes it extremely compressed
    content = "a" * 2000000  # ~2 MB uncompressed
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("large_repeating.txt", content)
        
    # Mock settings compression ratio to 10.0x and trigger limit for size (>1MB)
    monkeypatch.setattr(settings, "MAX_COMPRESSION_RATIO", 10.0)
    
    extractor = SafeZipExtractor(zip_path)
    # The compression ratio will be huge (e.g. >1000x)
    with pytest.raises(ValueError, match="compression ratio is too high"):
        extractor.extract()
