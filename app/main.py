from fastapi import FastAPI
from app.routes.analyze import router as analyze_router

app = FastAPI(
    title="Project Submission AI Analyzer",
    version="1.0.0"
)

app.include_router(analyze_router)

@app.get("/")
def home():
    return {
        "message": "Project Submission AI Analyzer is Running!"
    }