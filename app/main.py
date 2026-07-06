from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.analyze import router as analyze_router
from app.routes.ui import router as ui_router

from app.services.database_service import initialize_database
from app.routes.interview import router as interview_router

app = FastAPI(
    title="AI Project Submission Analyzer",
    version="1.0"
)

initialize_database()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui_router)

app.include_router(analyze_router)
app.include_router(interview_router)