from src.routers.users import router as users_router
from src.routers.products import router as products_router
from src.routers.orders import router as orders_router

__all__ = ["users_router", "products_router", "orders_router"]
