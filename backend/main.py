import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import auth, users, agents
from backend.core.exceptions import AppError

# Configure centralized logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("auth_system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

app = FastAPI(title="Role-Based Auth System (DynamoDB Ready)")

# Include all modular routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)

# Custom Application Error Handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning(f"Application Error: {exc.message} on path {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

# Standard HTTP Exception Handler Logging
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception {exc.status_code}: {exc.detail} on path {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Fallback Global Exception Handler (Catches 500s)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on path {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Application started successfully. Ready to handle requests.")