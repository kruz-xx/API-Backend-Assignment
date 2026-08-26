from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="User role in the system")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128, description="Plaintext password")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(UserBase):
    id: int = Field(..., description="Unique user ID")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


# ---------------------------------------------------------------------------
# Product Schemas
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed product description")
    price: float = Field(..., gt=0, description="Product unit price in USD")
    stock: int = Field(..., ge=0, description="Available stock quantity")
    category: str = Field(..., min_length=2, max_length=50, description="Product category")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=2, max_length=50)


class ProductResponse(ProductBase):
    id: int = Field(..., description="Unique product ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Order Schemas
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    product_id: int = Field(..., description="Target product ID")
    quantity: int = Field(..., gt=0, description="Quantity to purchase")


class OrderItemDetail(OrderItem):
    unit_price: float = Field(..., description="Unit price at time of purchase")
    subtotal: float = Field(..., description="Line item subtotal")


class OrderCreate(BaseModel):
    items: List[OrderItem] = Field(..., min_length=1, description="List of items in order")


class OrderResponse(BaseModel):
    id: int = Field(..., description="Unique order ID")
    user_id: int = Field(..., description="ID of the user who placed the order")
    items: List[OrderItemDetail] = Field(..., description="Purchased items")
    total_amount: float = Field(..., description="Total order amount in USD")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Standard Error Responses
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[List[Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorBody
