from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, Base, engine
from app.api import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health_check():
    return {"status": "saudável", "service": "Zeni API"}


# Global exception handlers to normalize error format for the frontend
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # If detail is already a dict with 'detail', treat it as the final shape
    if isinstance(exc.detail, dict):
        payload = exc.detail
        # Ensure top-level has 'detail'; if not, wrap
        if 'detail' not in payload:
            payload = {"detail": str(exc.detail)}
    else:
        payload = {"detail": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=payload, headers=getattr(exc, 'headers', None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Provide a concise detail and include errors in meta
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "meta": {"errors": exc.errors()}
        },
    )
