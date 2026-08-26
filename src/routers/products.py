from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from src.middlewares.error_handler import AppError
from src.models.schemas import ProductCreate, ProductResponse, ProductUpdate, UserResponse
from src.services.auth import require_admin

router = APIRouter(prefix="/products", tags=["Products Catalog"])

# In-memory product database store
products_db: Dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Mechanical Keyboard",
        "description": "RGB Backlit mechanical keyboard with tactile brown switches.",
        "price": 89.99,
        "stock": 25,
        "category": "Electronics",
        "created_at": datetime.now(timezone.utc)
    },
    2: {
        "id": 2,
        "name": "Wireless Ergonomic Mouse",
        "description": "High precision wireless mouse with rechargeable battery.",
        "price": 49.99,
        "stock": 50,
        "category": "Electronics",
        "created_at": datetime.now(timezone.utc)
    },
    3: {
        "id": 3,
        "name": "Noise Cancelling Headphones",
        "description": "Over-ear active noise cancelling Bluetooth headphones.",
        "price": 199.99,
        "stock": 15,
        "category": "Audio",
        "created_at": datetime.now(timezone.utc)
    }
}
product_id_counter = 4


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List products with filtering and pagination"
)
async def list_products(
    category: Optional[str] = Query(None, description="Filter products by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Retrieve products catalog with optional category, price bounds, and pagination.
    """
    items = list(products_db.values())

    if category:
        items = [p for p in items if p["category"].lower() == category.lower()]
    if min_price is not None:
        items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]

    start_idx = (page - 1) * limit
    paginated_items = items[start_idx : start_idx + limit]
    return [ProductResponse(**p) for p in paginated_items]


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Retrieve a single product by ID"
)
async def get_product(product_id: int):
    """
    Fetch specific product details.
    """
    product = products_db.get(product_id)
    if not product:
        raise AppError(
            code="PRODUCT_NOT_FOUND",
            message=f"Product with ID {product_id} does not exist.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return ProductResponse(**product)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)"
)
async def create_product(
    product_in: ProductCreate,
    _: UserResponse = Depends(require_admin)
):
    """
    Create a new product catalog entry.
    """
    global product_id_counter
    new_product = {
        "id": product_id_counter,
        "name": product_in.name,
        "description": product_in.description,
        "price": product_in.price,
        "stock": product_in.stock,
        "category": product_in.category,
        "created_at": datetime.now(timezone.utc)
    }
    products_db[product_id_counter] = new_product
    product_id_counter += 1

    return ProductResponse(**new_product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details (Admin only)"
)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    _: UserResponse = Depends(require_admin)
):
    """
    Partially update product details such as price, stock, or description.
    """
    product = products_db.get(product_id)
    if not product:
        raise AppError(
            code="PRODUCT_NOT_FOUND",
            message=f"Product with ID {product_id} was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

    update_data = product_update.model_dump(exclude_unset=True)
    product.update(update_data)
    return ProductResponse(**product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product (Admin only)"
)
async def delete_product(
    product_id: int,
    _: UserResponse = Depends(require_admin)
):
    """
    Remove a product item from the catalog.
    """
    if product_id not in products_db:
        raise AppError(
            code="PRODUCT_NOT_FOUND",
            message=f"Product with ID {product_id} was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

    del products_db[product_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
