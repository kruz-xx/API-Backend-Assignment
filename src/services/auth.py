import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import Depends, Header, status
from src.config import settings
from src.middlewares.error_handler import AppError
from src.models.schemas import UserResponse, UserRole


# In-memory user database store for demo/assignment purposes
users_db: Dict[str, dict] = {}
user_id_counter = 1


def hash_password(password: str) -> str:
    """
    Generate SHA256 hashed password with salt for deterministic local testing.
    """
    salt = settings.SECRET_KEY[:8]
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password.
    """
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT-like Bearer token with expiration.
    Uses standard base64/hash encoding for portable demo compatibility.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": int(expire.timestamp())})
    
    # We create a simple signed token string
    import json
    import base64
    import hmac
    
    payload_str = json.dumps(to_encode, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip("=")
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"


def decode_token(token: str) -> dict:
    """
    Decodes and verifies token signature and expiration.
    """
    import json
    import base64
    import hmac

    parts = token.split(".")
    if len(parts) != 2:
        raise AppError(
            code="INVALID_TOKEN",
            message="Malformed authentication token.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    payload_b64, signature = parts
    
    # Re-calculate signature
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise AppError(
            code="INVALID_TOKEN",
            message="Invalid token signature.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Pad base64
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)

    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
    except Exception:
        raise AppError(
            code="INVALID_TOKEN",
            message="Could not decode authentication payload.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    exp = payload.get("exp")
    if exp and datetime.now(timezone.utc).timestamp() > exp:
        raise AppError(
            code="TOKEN_EXPIRED",
            message="Authentication token has expired.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    return payload


async def get_current_user(authorization: Optional[str] = Header(None)) -> UserResponse:
    """
    FastAPI dependency to extract and authenticate current user from Bearer header.
    """
    if not authorization:
        raise AppError(
            code="MISSING_CREDENTIALS",
            message="Authorization header is required (e.g. 'Bearer <token>').",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not authorization.startswith("Bearer "):
        raise AppError(
            code="INVALID_AUTH_HEADER",
            message="Authorization scheme must be 'Bearer'.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    email = payload.get("sub")

    if not email or email not in users_db:
        raise AppError(
            code="USER_NOT_FOUND",
            message="Authenticated user record no longer exists.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_data = users_db[email]
    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        role=user_data["role"],
        is_active=user_data.get("is_active", True),
        created_at=user_data.get("created_at", datetime.now(timezone.utc))
    )


async def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    RBAC dependency ensuring the caller has the ADMIN role.
    """
    if current_user.role != UserRole.ADMIN:
        raise AppError(
            code="FORBIDDEN_OPERATION",
            message="Administrative privileges are required for this action.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user
