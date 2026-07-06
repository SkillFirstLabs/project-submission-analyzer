import asyncio, httpx
from app.main import app
from app.db.database import AsyncSessionLocal
from sqlalchemy import text

async def run_test():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as ac:
        login_res = await ac.post('/auth/login', data={'username': 'student@test.com', 'password': '123'})
        if login_res.status_code != 200:
            print('Login failed:', login_res.text)
            return
        token = login_res.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(text('SELECT id FROM submissions LIMIT 1'))
            submission_id = result.scalar()
            
            if not submission_id:
                print('No submissions found in DB to test.')
                return
            
            await db.execute(text(f'DELETE FROM viva_sessions WHERE submission_id = "{submission_id}"'))
            await db.commit()
            
        print('Using submission ID:', submission_id)
        
        data = {
            'session_id': submission_id,
            'consent_acknowledged': True,
            'analysis_data': {'hello': 'world'}
        }
        
        try:
            res = await ac.post('/viva-session/start', json=data, headers=headers)
            print('Start session:', res.status_code)
            print(res.text)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(run_test())
