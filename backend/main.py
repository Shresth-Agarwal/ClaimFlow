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
logger = logging.getLogger("claimflow")

app = FastAPI(title="ClaimFlow API")

# ── CORS ──────────────────────────────────────────────────────────────────────
# allow_origins must be explicit (not "*") when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logger ────────────────────────────────────────────────────────────
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

# ── Catch-all OPTIONS — guarantees preflight always returns 200 ───────────────
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    origin = request.headers.get("origin", "")
    logger.info(f"OPTIONS preflight: /{rest_of_path} from {origin}")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin":      origin,
            "Access-Control-Allow-Methods":     "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers":     "Authorization, Content-Type, Accept",
            "Access-Control-Allow-Credentials": "true",
        },
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)
from backend.api.routes.products import router as products_router
app.include_router(products_router)
from backend.api.routes.advisors import router as advisors_router
app.include_router(advisors_router)
# Uncomment both lines below when claims routes are ready:
# from backend.api.routes.claims import router as claims_router, adjuster_router
# app.include_router(claims_router)
# app.include_router(adjuster_router)

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

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("ClaimFlow started. Ready to handle requests.")
