import pytest
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_app.db"

@pytest.fixture
def test_engine():
    # Make sure old test db is removed
    if os.path.exists("./test_app.db"):
        try:
            os.remove("./test_app.db")
        except Exception:
            pass
            
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    # Run the setup synchronously
    loop = asyncio.new_event_loop()
    loop.run_until_complete(create_tables())
    loop.close()
    
    yield engine
    
    # Run the teardown synchronously
    loop = asyncio.new_event_loop()
    loop.run_until_complete(drop_tables())
    loop.run_until_complete(engine.dispose())
    loop.close()
    
    # Cleanup file
    if os.path.exists("./test_app.db"):
        try:
            os.remove("./test_app.db")
        except Exception:
            pass

@pytest.fixture(autouse=True)
def override_get_db(test_engine):
    AsyncSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    async def _get_db():
        async with AsyncSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()
