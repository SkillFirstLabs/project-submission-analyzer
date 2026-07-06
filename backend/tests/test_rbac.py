import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_student_cannot_access_mentor_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First, register a student
        student_data = {
            "name": "Test Student",
            "email": "student@test.com",
            "password": "password123",
            "role": "student"
        }
        await ac.post("/auth/register", json=student_data)
        
        # Login as student
        login_res = await ac.post("/auth/login", data={"username": "student@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        # Try accessing mentor dashboard
        res = await ac.get("/mentor/submissions", headers={"Authorization": f"Bearer {token}"})
        
        # Should be forbidden
        assert res.status_code == 403
        assert "Operation requires mentor role" in res.text

@pytest.mark.asyncio
async def test_student_cannot_export_reports():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First, register a student
        student_data = {
            "name": "Test Student",
            "email": "student@test.com",
            "password": "password123",
            "role": "student"
        }
        await ac.post("/auth/register", json=student_data)
        
        login_res = await ac.post("/auth/login", data={"username": "student@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        # Try exporting a report
        res = await ac.get("/reports/some_dummy_id/export?format=json", headers={"Authorization": f"Bearer {token}"})
        
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_student_cannot_leak_sensitive_report_on_end_session(db_session):
    from app.db.models import User, Submission, EvaluationReport, VivaSession
    from app.services.auth import get_password_hash
    import uuid
    import time
    
    student_id = str(uuid.uuid4())
    student_user = User(
        id=student_id,
        email="student_test@test.com",
        password_hash=get_password_hash("password123"),
        role="student",
        name="Test Student"
    )
    db_session.add(student_user)
    
    submission_id = str(uuid.uuid4())
    submission = Submission(
        id=submission_id,
        student_id=student_id,
        project_title="Test Project Title",
        description="Test Desc",
        outcomes="Test Outcomes",
        zip_path="dummy.zip"
    )
    db_session.add(submission)
    
    eval_report = EvaluationReport(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        suggested_skills=[],
        evaluation_report={}
    )
    db_session.add(eval_report)
    
    viva_session = VivaSession(
        id=submission_id,
        submission_id=submission_id,
        status="in_progress",
        id_check="id_verified",
        started_at=time.time(),
        last_event_at=time.time(),
        events=[],
        flags=[]
    )
    db_session.add(viva_session)
    await db_session.commit()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", data={"username": "student_test@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        response = await ac.post(
            "/viva-session/end",
            json={
                "session_id": submission_id,
                "questions": [{"text": "What is Python?", "skill_name": "Python", "type": "conceptual"}],
                "answers": {"0": "Python is a programming language"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        response_json = response.json()
        
        assert "proctoring_report" not in response_json
        assert "viva_grading" not in response_json
        assert "integrity_score" not in response_json
        assert "risk_level" not in response_json
        assert "flags" not in response_json
        
        assert response_json["status"] == "viva_completed"
        assert response_json["session_id"] == submission_id

@pytest.mark.asyncio
async def test_fresh_session_contains_interview_started(db_session):
    from app.db.models import User, Submission, EvaluationReport, VivaSession
    from app.services.auth import get_password_hash
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    import uuid
    
    student_id = str(uuid.uuid4())
    student_user = User(
        id=student_id,
        email="student_start@test.com",
        password_hash=get_password_hash("password123"),
        role="student",
        name="Test Student"
    )
    db_session.add(student_user)
    
    submission_id = str(uuid.uuid4())
    submission = Submission(
        id=submission_id,
        student_id=student_id,
        project_title="Test Project Title",
        description="Test Desc",
        outcomes="Test Outcomes",
        zip_path="dummy.zip"
    )
    db_session.add(submission)
    
    eval_report = EvaluationReport(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        suggested_skills=[],
        evaluation_report={}
    )
    db_session.add(eval_report)
    await db_session.commit()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", data={"username": "student_start@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        response = await ac.post(
            "/viva-session/start",
            json={
                "session_id": submission_id,
                "consent_acknowledged": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Verify from database
        result = await db_session.execute(
            select(VivaSession)
            .options(selectinload(VivaSession.events))
            .where(VivaSession.id == submission_id)
        )
        viva_session = result.scalars().first()
        
        assert len(viva_session.events) > 0
        assert viva_session.events[0].event_type == "interview_started"

@pytest.mark.asyncio
async def test_session_start_requires_consent(db_session):
    from app.db.models import User, Submission, EvaluationReport, VivaSession
    from app.services.auth import get_password_hash
    from sqlalchemy.future import select
    import uuid
    
    student_id = str(uuid.uuid4())
    student_user = User(
        id=student_id,
        email="student_consent@test.com",
        password_hash=get_password_hash("password123"),
        role="student",
        name="Test Student"
    )
    db_session.add(student_user)
    
    submission_id = str(uuid.uuid4())
    submission = Submission(
        id=submission_id,
        student_id=student_id,
        project_title="Test Project Title",
        description="Test Desc",
        outcomes="Test Outcomes",
        zip_path="dummy.zip"
    )
    db_session.add(submission)
    
    eval_report = EvaluationReport(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        suggested_skills=[],
        evaluation_report={}
    )
    db_session.add(eval_report)
    await db_session.commit()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", data={"username": "student_consent@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        # 1. Call with consent_acknowledged=False
        response = await ac.post(
            "/viva-session/start",
            json={
                "session_id": submission_id,
                "consent_acknowledged": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Consent must be acknowledged" in response.text
        
        # 2. Call with consent_acknowledged omitted
        response_omitted = await ac.post(
            "/viva-session/start",
            json={
                "session_id": submission_id
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_omitted.status_code == 422
        
        # Verify from database that no VivaSession was created
        result = await db_session.execute(select(VivaSession).where(VivaSession.id == submission_id))
        viva_session = result.scalars().first()
        assert viva_session is None

@pytest.mark.asyncio
async def test_identity_check_required_before_proctoring_events(db_session):
    from app.db.models import User, Submission, EvaluationReport, VivaSession
    from app.services.auth import get_password_hash
    import uuid
    import time
    
    student_id = str(uuid.uuid4())
    student_user = User(
        id=student_id,
        email="student_order@test.com",
        password_hash=get_password_hash("password123"),
        role="student",
        name="Test Student"
    )
    db_session.add(student_user)
    
    submission_id = str(uuid.uuid4())
    submission = Submission(
        id=submission_id,
        student_id=student_id,
        project_title="Test Project Title",
        description="Test Desc",
        outcomes="Test Outcomes",
        zip_path="dummy.zip"
    )
    db_session.add(submission)
    
    eval_report = EvaluationReport(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        suggested_skills=[],
        evaluation_report={}
    )
    db_session.add(eval_report)
    
    viva_session = VivaSession(
        id=submission_id,
        submission_id=submission_id,
        status="in_progress",
        id_check="pending",
        started_at=time.time(),
        last_event_at=time.time(),
        events=[],
        flags=[]
    )
    db_session.add(viva_session)
    await db_session.commit()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", data={"username": "student_order@test.com", "password": "password123"})
        token = login_res.json()["access_token"]
        
        # 1. Post a gaze_off_screen event before id_verified (should fail with 409)
        response_fail = await ac.post(
            "/viva-session/event",
            json={
                "session_id": submission_id,
                "event_type": "gaze_off_screen",
                "timestamp": "2026-07-05T12:00:00Z",
                "duration_ms": 3000.0,
                "confidence": 1.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_fail.status_code == 409
        assert "Identity verification must complete" in response_fail.text
        
        # 2. Post id_verified event (should succeed)
        response_id = await ac.post(
            "/viva-session/event",
            json={
                "session_id": submission_id,
                "event_type": "id_verified",
                "timestamp": "2026-07-05T12:00:02Z",
                "duration_ms": 0.0,
                "confidence": 1.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_id.status_code == 200
        
        # 3. Post gaze_off_screen event again (should succeed now)
        response_success = await ac.post(
            "/viva-session/event",
            json={
                "session_id": submission_id,
                "event_type": "gaze_off_screen",
                "timestamp": "2026-07-05T12:00:05Z",
                "duration_ms": 3000.0,
                "confidence": 1.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_success.status_code == 200
