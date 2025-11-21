from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
import traceback
from .logging_utils import setup_logging

logger = setup_logging()

class ServiceError(Exception):
    """Custom exception for known service errors that should be returned to the caller."""
    def __init__(self, message: str, code: str = "SERVICE_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

async def http_exception_handler(request: Request, exc: ServiceError):
    logger.warning("ServiceError: %s", exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": {"code": exc.code, "message": exc.message}},
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Unhandled Exception: %s\n%s", str(exc), tb)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )
