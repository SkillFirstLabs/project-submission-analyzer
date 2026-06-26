import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title="AIPSA Lab API",
    description="Precision Diagnostic Engine Backend for AI Project Submission Analyzer",
    version="0.1.0"
)

# CORS Heuristics for React Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow broad access; scopes can narrow for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(router, prefix="/api")

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "engine": "AIPSA Precision Diagnostic Engine",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
