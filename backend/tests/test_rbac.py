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
