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

# Configure CORS with restricted origins for production
raw_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

# If no origins configured, we intentionally keep the list empty (no cross-origin allowed).
# In production you MUST set the `CORS_ORIGINS` environment variable (comma-separated).
if not raw_origins:
    print("⚠️  No CORS origins configured (CORS_ORIGINS empty). Cross-origin requests will be blocked by default.")

# Support wildcard '*' explicitly (use only in controlled environments)
allow_all = any(origin == "*" for origin in raw_origins)

if allow_all:
    allowed_origins = ["*"]
else:
    allowed_origins = raw_origins

# Decide whether to allow credentials. Prefer explicit config via settings.cors_allow_credentials.
# If allow_all is enabled and credentials would be allowed, Starlette/ browsers cannot use '*' with credentials,
# so force credentials off and warn.
allow_credentials = bool(settings.cors_allow_credentials)
if allow_all and allow_credentials:
    print("⚠️  CORS configured with allow_origins='*' and allow_credentials=True: this is incompatible. Forcing allow_credentials=False for safety.")
    allow_credentials = False

print(f"🔒 CORS configured with allowed origins: {allowed_origins} allow_credentials={allow_credentials}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    # Expose a minimal safe set of headers to the browser. Avoid exposing sensitive headers unnecessarily.
    expose_headers=["Content-Type", "Content-Length", "X-Request-ID", "Location"],
    max_age=3600,
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
