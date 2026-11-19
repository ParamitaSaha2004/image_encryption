"""
HICE Main Application Entrypoint
Initializes FastAPI, configures CORS, registers API routers, and health checks.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from app.config import settings

# Import Route Handlers
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.system import router as system_router
from app.routes.images import router as images_router
from app.routes.crypto import router as crypto_router
from app.routes.shares import router as shares_router
from app.routes.audit import router as audit_router
from app.routes.ai_monitoring import router as ai_router
from app.routes.evaluation import router as evaluation_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Hybrid Intelligent Image Encryption and Secure Sharing System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Register Application Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(system_router)
app.include_router(images_router)
app.include_router(crypto_router)
app.include_router(shares_router)
app.include_router(audit_router)
app.include_router(ai_router)
app.include_router(evaluation_router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "system": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "docs": "/docs"
    }

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "vault_ready": True
    }
