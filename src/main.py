from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.middlewares.error_handler import register_exception_handlers
from src.routers.orders import router as orders_router
from src.routers.products import router as products_router
from src.routers.users import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Scalable, Production-Ready FastAPI backend assignment implementation covering Modules 00 through 12.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized exception handlers for standardized error responses
register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Health Check Endpoint (Module 02 requirement)
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["System"],
    summary="Health check probe"
)
async def health_check():
    """
    Returns server operational health status.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# ---------------------------------------------------------------------------
# Include API Routers
# ---------------------------------------------------------------------------
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
