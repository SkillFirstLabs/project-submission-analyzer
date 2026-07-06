from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze, viva
from app.config import settings

app = FastAPI(
    title="Project Submission AI Analyzer with Proctored Live Viva",
    description="Backend API for safe ZIP code extraction, LLM evaluations, and real-time proctoring telemetry logs.",
    version="1.0.0"
)

# Set up CORS middleware for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual client domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(analyze.router, tags=["Submission Analysis"])
app.include_router(viva.router, tags=["Live Viva Proctoring"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "project-submission-analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
