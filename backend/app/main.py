from fastapi import FastAPI
from .api.v1.routes_claims import router as claims_router
from .utils.logging_utils import setup_logging
from .utils import exception_handlers
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = setup_logging()

app = FastAPI(title="Plum Claims Adjudicator - Backend", version="0.1")

# include routes
app.include_router(claims_router)

# register custom exception handlers
app.add_exception_handler(exception_handlers.ServiceError, exception_handlers.http_exception_handler)
app.add_exception_handler(Exception, exception_handlers.unhandled_exception_handler)

# validation error to return JSON
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(status_code=422, content={"status": "error", "error": "Validation error", "details": exc.errors()})
