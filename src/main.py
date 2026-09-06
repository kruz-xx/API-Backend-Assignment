from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.middlewares.error_handler import register_exception_handlers
from src.routers.graphql_router import graphql_router
from src.routers.orders import router as orders_router
from src.routers.products import router as products_router
from src.routers.users import router as users_router

tags_metadata = [
    {
        "name": "System",
        "description": "Health checks and service availability probes.",
    },
    {
        "name": "Users & Authentication",
        "description": "User registration, password hashing, JWT issuance, and RBAC authentication.",
    },
    {
        "name": "Products Catalog",
        "description": "Product catalog with filtering, category search, and inventory management.",
    },
    {
        "name": "Orders & Transactions",
        "description": "Order placement, inventory reservation, and BOLA-protected order queries.",
    },
    {
        "name": "GraphQL",
        "description": "Interactive Strawberry GraphQL schema and query execution endpoint.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    summary="Modular, Production-Ready FastAPI & GraphQL Backend Assignment",
    description="""
## Overview
Production-grade backend service demonstrating RESTful principles, security, and GraphQL:
- **Authentication & RBAC**: JWT Bearer tokens, password hashing, role enforcement
- **Catalog Management**: In-memory catalog with pagination and query filtering
- **Order Processing**: Inventory checks, subtotal calculations, and BOLA protection
- **Resilience**: Centralized error responses, rate limiting, and caching
- **GraphQL**: Type-safe queries, mutations, and sub-resource resolution
    """,
    contact={
        "name": "Backend Assignment Developer",
        "email": "developer@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
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
app.include_router(graphql_router, prefix="/graphql")
