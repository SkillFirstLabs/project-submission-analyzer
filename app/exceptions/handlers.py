from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger("ai_project_analyzer")


# =========================
# 1. GENERIC EXCEPTION
# =========================
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_type": "internal_server_error",
            "message": "Something went wrong while processing the request.",
            "detail": str(exc)
        }
    )


# =========================
# 2. VALIDATION ERROR (FASTAPI)
# =========================
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    logger.warning(f"Validation Error: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid input provided.",
            "detail": exc.errors()
        }
    )


# =========================
# 3. VALUE ERROR (YOUR SERVICES)
# =========================
async def value_error_handler(request: Request, exc: ValueError):

    logger.warning(f"Value Error: {str(exc)}")

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error_type": "bad_request",
            "message": "Invalid request or processing error.",
            "detail": str(exc)
        }
    )


# =========================
# 4. FILE / ZIP ERRORS
# =========================
async def file_not_found_handler(request: Request, exc: FileNotFoundError):

    logger.warning(f"File Error: {str(exc)}")

    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error_type": "file_not_found",
            "message": "Required file not found.",
            "detail": str(exc)
        }
    )


# =========================
# 5. GEMINI / LLM ERRORS
# =========================
async def llm_exception_handler(request: Request, exc: Exception):

    error_message = str(exc)

    # Detect quota error
    if "credit balance is too low" in error_message.lower():
        status_code = 402
        error_type = "llm_billing_required"
        message = "LLM provider billing or credits are required."
    elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
        status_code = 429
        error_type = "llm_quota_exceeded"
        message = "LLM quota exceeded. Please try again later or upgrade plan."
    else:
        status_code = 502
        error_type = "llm_error"
        message = "AI model failed to process request."

    logger.error(f"LLM Error: {error_message}")

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error_type": error_type,
            "message": message,
            "detail": error_message
        }
    )


# =========================
# 6. REGISTER ALL HANDLERS
# =========================
def register_exception_handlers(app):

    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(FileNotFoundError, file_not_found_handler)
    app.add_exception_handler(RuntimeError, llm_exception_handler)
