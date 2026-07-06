from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import analyze, viva, auth, export, dashboard, mentor
from app.config import settings
from app.db.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Project Submission AI Analyzer with Proctored Live Viva",
    description="Backend API for safe ZIP code extraction, LLM evaluations, and real-time proctoring telemetry logs.",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(export.router)
app.include_router(dashboard.router)
app.include_router(mentor.router)
app.include_router(analyze.router, tags=["Submission Analysis"])
app.include_router(viva.router, tags=["Live Viva Proctoring"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "project-submission-analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)






