from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from app.api import router
from app.config import configure_logging, get_logger, get_settings

# Load settings
settings = get_settings()

# Initialize logging configuration
configure_logging()
logger = get_logger("app.main")
logger.info("Starting %s version %s", settings.app.name, settings.app.version)

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.app.debug,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Format HTTPExceptions into the standard structured error schema."""
    # If detail is already formatted with an "error" key, return it directly
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    # Otherwise format it as standard error schema
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_EXCEPTION",
                "message": str(exc.detail),
                "details": None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Format RequestValidationErrors into the standard structured error schema."""
    errors = exc.errors()
    messages = []
    details = []

    for err in errors:
        # Loc represents path of invalid field (e.g. ['body', 'project_title'])
        # Strip first element if it's 'body' or 'query' or 'form' to make it cleaner
        loc_path = [str(x) for x in err.get("loc", [])]
        if loc_path and loc_path[0] in {"body", "query", "form"}:
            loc_path = loc_path[1:]

        field = " -> ".join(loc_path) if loc_path else "request"
        msg = f"Field '{field}': {err.get('msg')}"
        messages.append(msg)
        details.append(
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "; ".join(messages),
                "details": details,
            }
        },
    )


# Include the API router
app.include_router(router)

# Mount frontend static files
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/")
async def root():
    """Minimal root endpoint returning application API status."""
    return {
        "message": "AI Analyzer API",
        "status": "running",
    }