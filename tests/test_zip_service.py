import os
import pytest
import shutil
from app.models.project_context import ProjectContext
from app.services.zip_service import ZipService

def test_valid_zip_extraction():
    zip_path = "sample_project.zip"
    assert os.path.exists(zip_path), "sample_project.zip must exist"
    
    context = ProjectContext(
        project_title="Test Valid",
        project_outcomes="Outcome 1",
        zip_path=zip_path
    )
    
    zip_service = ZipService()
    context = zip_service.process(context)
    
    assert context.project_id != ""
    assert context.extract_path != ""
    assert os.path.exists(context.extract_path)
    
    extracted_main = os.path.join(context.extract_path, "main.py")
    assert os.path.exists(extracted_main)
    
    # Clean up
    shutil.rmtree(context.extract_path, ignore_errors=True)

def test_path_traversal_rejection():
    zip_path = "path_traversal_project.zip"
    assert os.path.exists(zip_path), "path_traversal_project.zip must exist"
    
    context = ProjectContext(
        project_title="Test Bad Traversal",
        project_outcomes="Outcome 1",
        zip_path=zip_path
    )
    
    zip_service = ZipService()
    with pytest.raises(ValueError) as excinfo:
        zip_service.process(context)
        
    assert "Path traversal attempt detected" in str(excinfo.value)

def test_empty_zip_rejection():
    zip_path = "empty_project.zip"
    assert os.path.exists(zip_path), "empty_project.zip must exist"
    
    context = ProjectContext(
        project_title="Test Empty",
        project_outcomes="Outcome 1",
        zip_path=zip_path
    )
    
    zip_service = ZipService()
    with pytest.raises(ValueError) as excinfo:
        zip_service.process(context)
        
    assert "empty" in str(excinfo.value).lower() or "no files found" in str(excinfo.value).lower()
