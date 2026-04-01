from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings, Base, engine
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events — create tables once, dispose pool on exit."""
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    # Disable docs in production to reduce cold-start import overhead
    # Uncomment the lines below if you want to hide docs on Render:
    # docs_url=None,
    # redoc_url=None,
)

# --- Middleware stack (order matters: last added = first executed) ---

# 1. GZip — compresses responses >500 bytes (~60-80% smaller payloads)
# Crucial on Render where bandwidth and latency are limited
app.add_middleware(GZipMiddleware, minimum_size=500)

# 2. CORS — configure from environment
raw_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

if not raw_origins:
    print("⚠️  No CORS origins configured. Cross-origin requests will be blocked.")

allow_all = any(origin == "*" for origin in raw_origins)
allowed_origins = ["*"] if allow_all else raw_origins

allow_credentials = bool(settings.cors_allow_credentials)
if allow_all and allow_credentials:
    print("⚠️  CORS '*' + credentials=True is incompatible. Forcing credentials=False.")
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Type", "Content-Length"],
    # Cache preflight for 24h — reduces OPTIONS round-trips on Render
    max_age=86400,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Global exception handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        payload = exc.detail
        if 'detail' not in payload:
            payload = {"detail": str(exc.detail)}
    else:
        payload = {"detail": str(exc.detail)}
    return ORJSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers=getattr(exc, 'headers', None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return ORJSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "meta": {"errors": exc.errors()},
        },
    )
