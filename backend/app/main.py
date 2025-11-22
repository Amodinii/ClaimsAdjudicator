from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.v1.routes_claims import router as claims_router
from .utils.logging_utils import setup_logging
from .utils import exception_handlers
from .core.database import engine, Base
from .models import sql_models 

logger = setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plum Claims Adjudicator - Backend", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Gotta change to ["http://localhost:5173"] in prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router)

app.add_exception_handler(exception_handlers.ServiceError, exception_handlers.http_exception_handler)
app.add_exception_handler(Exception, exception_handlers.unhandled_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(status_code=422, content={"status": "error", "error": "Validation error", "details": exc.errors()})