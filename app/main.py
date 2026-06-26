from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.analyzer import router as analyzer_router

app = FastAPI(
    title="ProjectIQ",
    description="AI-Powered Project Submission Analyzer API",
    version="1.0.0"
)

# CORS middleware for cross-origin client support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints router
app.include_router(analyzer_router)

from fastapi.responses import HTMLResponse
import os

@app.get("/", response_class=HTMLResponse, tags=["UI"])
def read_root():
    static_file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file_path):
        with open(static_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return "<h1>ProjectIQ Service is Running</h1>"
