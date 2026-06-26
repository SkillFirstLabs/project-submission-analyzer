from fastapi import FastAPI
from dotenv import load_dotenv
from app.exceptions.handlers import register_exception_handlers
# Load environment variables FIRST
load_dotenv()

from app.api.analyze import router as analyze_router


app = FastAPI(
    title="AI Project Evaluation API",
    version="1.0.0",
    description="Analyze student project submissions using AI."
)
register_exception_handlers(app)
# Include routes
app.include_router(analyze_router)


@app.get("/")
async def root():
    return {
        "message": "AI Project Evaluation API",
        "status": "Running",
        "docs": "/docs"
    }