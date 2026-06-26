# FastAPI entry point
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Project Submission AI Analyzer",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Project Submission AI Analyzer Running"
    }