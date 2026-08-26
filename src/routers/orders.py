from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, Depends, status
from src.middlewares.error_handler import AppError
from src.models.schemas import (
    OrderCreate,
    OrderItemDetail,
    OrderResponse,
    OrderStatus,
    UserResponse
)
from src.routers.products import products_db
from src.services.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders & Transactions"])

# In-memory orders database store
orders_db: Dict[int, dict] = {}
order_id_counter = 1


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order"
)
async def place_order(
    order_in: OrderCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Creates an order, validates inventory availability, deducts stock,
    calculates subtotals, and returns confirmed order receipt.
    """
    global order_id_counter

    processed_items: List[OrderItemDetail] = []
    total_amount = 0.0

    for item in order_in.items:
        product = products_db.get(item.product_id)
        if not product:
            raise AppError(
                code="PRODUCT_NOT_FOUND",
                message=f"Product with ID {item.product_id} in order does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if product["stock"] < item.quantity:
            raise AppError(
                code="INSUFFICIENT_STOCK",
                message=f"Product '{product['name']}' has only {product['stock']} units left in stock.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        subtotal = round(product["price"] * item.quantity, 2)
        total_amount += subtotal

        # Deduct inventory stock
        product["stock"] -= item.quantity

        processed_items.append(
            OrderItemDetail(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=product["price"],
                subtotal=subtotal
            )
        )

    order_record = {
        "id": order_id_counter,
        "user_id": current_user.id,
        "items": [item.model_dump() for item in processed_items],
        "total_amount": round(total_amount, 2),
        "status": OrderStatus.PENDING,
        "created_at": datetime.now(timezone.utc)
    }

    orders_db[order_id_counter] = order_record
    order_id_counter += 1

    return OrderResponse(**order_record)


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List current user orders"
)
async def list_orders(current_user: UserResponse = Depends(get_current_user)):
    """
    Retrieves all orders placed by the current authenticated user.
    """
    user_orders = [o for o in orders_db.values() if o["user_id"] == current_user.id]
    return [OrderResponse(**o) for o in user_orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details by ID"
)
async def get_order(
    order_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retrieves a specific order. Enforces BOLA protection by ensuring
    the caller owns the order or is an admin.
    """
    order = orders_db.get(order_id)
    if not order:
        raise AppError(
            code="ORDER_NOT_FOUND",
            message=f"Order with ID {order_id} does not exist.",
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Broken Object Level Authorization (BOLA) check
    if order["user_id"] != current_user.id and current_user.role != "admin":
        raise AppError(
            code="FORBIDDEN_RESOURCE",
            message="You do not have permission to view this order.",
            status_code=status.HTTP_403_FORBIDDEN
        )

    return OrderResponse(**order)
