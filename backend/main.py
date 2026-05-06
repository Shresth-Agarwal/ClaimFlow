import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import auth, users, agents
from backend.core.exceptions import AppError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("auth_system")

app = FastAPI(title="ClaimFlow Auth API")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# ── Request logger — logs every incoming request with headers ─────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        f">>> {request.method} {request.url.path} | "
        f"Origin: {request.headers.get('origin', 'none')} | "
        f"Content-Type: {request.headers.get('content-type', 'none')}"
    )
    response = await call_next(request)
    logger.info(
        f"<<< {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"ACAO: {response.headers.get('access-control-allow-origin', 'MISSING')}"
    )
    return response

# ── Catch-all OPTIONS handler — guarantees preflight always returns 200 ───────
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    origin = request.headers.get("origin", "")
    logger.info(f"OPTIONS preflight hit: /{rest_of_path} from origin: {origin}")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            "Access-Control-Allow-Credentials": "true",
        },
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)

# ── Error handlers ────────────────────────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning(f"AppError {exc.status_code}: {exc.message} on {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Application started. Ready to handle requests.")
