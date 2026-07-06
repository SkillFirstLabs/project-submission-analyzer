import pytest
from app.services.extractor import extract_and_analyze_zip, ZipSafetyError
from app.services.proctoring_engine import finalize_proctoring_report, process_event
from app.store.session_store import session_store
import os
import zipfile
import tempfile

def test_zip_safety_check():
    # Test path traversal injection
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        zip_path = tmp.name
        
    try:
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../../malicious.py", "print('hack')")
            
        with pytest.raises(ZipSafetyError) as exc_info:
            extract_and_analyze_zip(zip_path)
            
        assert "Path traversal" in str(exc_info.value)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

def test_proctoring_scoring():
    # Setup state
    session_id = "test-session-123"
    analysis_data = {
        "project_title": "Test project",
        "suggested_skills": [],
        "evaluation_report": {},
        "metadata": {"processing_time_ms": 100.0}
    }
    session_store.create_session(session_id, analysis_data)
    
    # Send ID verification event
    process_event(session_id, {
        "session_id": session_id,
        "event_type": "id_verified",
        "timestamp": "2026-07-05T12:00:00Z"
    })
    
    # Send tab switched event (immediate medium severity flag)
    process_event(session_id, {
        "session_id": session_id,
        "event_type": "tab_switched",
        "timestamp": "2026-07-05T12:00:05Z"
    })
    
    # Finalize report
    report = finalize_proctoring_report(session_id)
    
    assert report["session_id"] == session_id
    assert report["id_check"] == "id_verified"
    assert report["flag_summary"]["tab_switched"] == 1
    # Integrity score should be 1.0 - tab_switched_penalty (0.1) = 0.9
    assert report["integrity_score"] == 0.9
    assert report["risk_level"] == "low"
