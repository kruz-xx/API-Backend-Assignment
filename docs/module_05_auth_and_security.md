# Module 05 — Authentication & Authorization

## Overview
Authentication ("who you are") vs Authorization ("what you can do"). Implementation of API key validation, HTTP Basic Authentication mechanics, session-based vs token-based stateless authentication, JSON Web Tokens (JWT) signed with HMAC-SHA256, OAuth 2.0 authorization code flow, Role-Based Access Control (RBAC), and token expiration with refresh token rotation.

---

## Conceptual Questions & Implementation Notes

### 1. Authentication vs Authorization
> Explain the difference between **authentication** ("who are you") and **authorization** ("what are you allowed to do") — these get confused constantly.

**Answer:**

**Authentication (AuthN) — "Who are you?"**
- Definition: The process of verifying the identity of a client, user, or system.
- Verification Mechanism: Validating credentials such as username/password, cryptographic signatures, biometric data, API keys, or multi-factor authentication (MFA) tokens.
- Failure HTTP Status Code: `401 Unauthorized` (indicating missing or invalid authentication credentials).
- Example: A user submits their email and password to `/api/v1/auth/login`. The server verifies the password hash and confirms identity.

**Authorization (AuthZ) — "What are you allowed to do?"**
- Definition: The process of determining whether an authenticated identity has permission to perform a specific action on a specific resource.
- Verification Mechanism: Checking user roles (e.g., admin, editor, viewer), access control lists (ACLs), scopes, or fine-grained policies.
- Failure HTTP Status Code: `403 Forbidden` (the server understands who you are, but you lack sufficient permissions).
- Example: An authenticated regular user with `role: "user"` attempts to delete a product via `DELETE /api/v1/products/42`. The server rejects the request with `403 Forbidden` because only `role: "admin"` possesses delete privileges.

**Comparison Table:**

| Dimension | Authentication (AuthN) | Authorization (AuthZ) |
| :--- | :--- | :--- |
| Core Question | "Who are you?" | "What are you allowed to do?" |
| Execution Order | Executes first in the request pipeline | Executes after identity is confirmed |
| Input | Credentials (password, token, API key) | User identity, assigned roles, permissions |
| HTTP Status on Failure | `401 Unauthorized` | `403 Forbidden` |
| Real-World Analogy | Passport verifying citizenship at border control | Boarding pass granting access to a specific seat/cabin |

---

### 2. API Key Authentication
> Implement API key auth: require a header like `X-API-Key`, reject requests without a valid one with `401`. Explain when API keys are appropriate (service-to-service, simple use cases) vs not (never for representing an individual end user's identity in a user-facing app).

**Answer & Implementation:**

**When API Keys Are Appropriate:**
- Server-to-server / Machine-to-machine (M2M) communication where two trusted backends communicate without user interaction.
- Developer API platforms (e.g., Stripe, SendGrid, weather APIs) to track usage quotas and rate limits per organization.
- Webhooks and scheduled background cron jobs.

**When API Keys Are NOT Appropriate:**
- Client-side single-page applications (SPAs) or mobile apps representing individual user sessions. Hardcoding or storing static API keys on client devices allows attackers to decompile or extract the key.
- User identity tracking with fine-grained access delegation, password resets, and dynamic permission lifecycles.

**FastAPI Implementation:**

```python
from fastapi import Header, HTTPException, Security, status
from typing import Optional

API_KEYS_DB = {
    "secret-backend-key-12345": {"client_id": "service_payment_worker", "tier": "enterprise"},
    "partner-api-key-67890": {"client_id": "service_analytics_collector", "tier": "standard"}
}

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> dict:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "MISSING_API_KEY", "message": "X-API-Key header is required."}}
        )
    if x_api_key not in API_KEYS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_API_KEY", "message": "Provided API key is invalid or revoked."}}
        )
    return API_KEYS_DB[x_api_key]
```

---

### 3. HTTP Basic Authentication
> Explain Basic Auth (`username:password` base64-encoded in a header) and why it's rarely used alone in modern APIs (credentials sent on every request, no expiry).

**Answer:**

**Mechanism:**
HTTP Basic Authentication transmits credentials in the standard HTTP `Authorization` header using the format:
```http
Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
```
Where `dXNlcm5hbWU6cGFzc3dvcmQ=` is the Base64 encoding of `username:password`.

**Why Basic Auth is Rarely Used Alone in Modern APIs:**
1. **Credentials Sent on Every Request:** The client must send raw user credentials (username and plaintext password) with every single HTTP request. If any request is intercepted, the permanent password is compromised.
2. **No Built-in Expiration (TTL):** Unlike tokens (JWTs) which expire automatically after minutes or hours, Basic Auth credentials remain valid indefinitely until the user manually changes their password.
3. **No Granular Scopes or Delegation:** Basic Auth cannot grant scoped permissions (e.g., read-only access to specific resources). It provides full account access.
4. **Revocation Requires Global Password Invalidation:** You cannot revoke a single client device or session without resetting the master user password, which terminates all access across all devices.
5. **Reversible Encoding:** Base64 is an encoding format, not encryption. Anyone with access to the raw header can decode `username:password` instantly.

---

### 4. Sessions vs Tokens & HTTP Statelessness
> Explain sessions vs tokens: session-based auth stores state on the server (a session ID in a cookie mapping to server-side data) — but wait, didn't we say HTTP is stateless? Explain how sessions work *around* statelessness. Contrast with token-based auth (JWT), which is stateless — the token itself carries the claims.

**Answer:**

**How Sessions Work Around HTTP Statelessness:**
HTTP is inherently stateless: each request/response cycle is independent, and the server retains no memory between transactions.
Session-based authentication works around this by introducing stateful server-side storage:
1. When a user logs in, the server generates a cryptographically random `Session ID` (e.g., UUID `a1b2-c3d4`).
2. The server stores user session data in a stateful datastore (in-memory, Redis, or SQL database) indexed by the Session ID.
3. The server sends the Session ID to the client browser via the `Set-Cookie: session_id=a1b2-c3d4; HttpOnly; Secure` header.
4. On every subsequent request, the client browser automatically attaches the cookie (`Cookie: session_id=a1b2-c3d4`).
5. The server performs a database/cache lookup for `session_id` to retrieve user data, manually reconstructing state.

**Contrast with Token-Based Auth (JWT):**
Token-based authentication (such as JWT) is truly stateless:
- **Self-Contained Claims:** The token itself contains the user identity, roles, and expiration timestamp inside its payload (`sub`, `role`, `exp`).
- **Cryptographic Verification:** Instead of looking up a session database on every request, the server verifies the cryptographic signature of the token using a secret or public key.
- **Horizontal Scalability:** Any backend instance in a distributed cluster can validate the token independently without sharing a centralized session cache.

**Architecture Comparison:**

```text
Session-Based (Stateful):
Client ──[Cookie: session_id]──> Server ──[Cache Lookup: session_id]──> Redis/DB Store

Token-Based / JWT (Stateless):
Client ──[Authorization: Bearer <JWT>]──> Server ──[Verify Signature via Secret Key]──> Authenticated
```

---

### 5. JWT-Based Authentication Implementation & Anatomy
> Implement JWT-based auth: a `POST /login` endpoint that checks credentials and returns a signed JWT, and a protected endpoint that requires a valid `Authorization: Bearer <token>` header. Decode a JWT (e.g. on jwt.io or in code) and explain its 3 parts (header, payload, signature) and why the signature prevents tampering, even though the payload itself is just base64 (NOT encrypted — explain that distinction clearly, it's a common misconception).

**Answer & Implementation:**

**Anatomy of a JWT (`Header.Payload.Signature`):**
A JSON Web Token consists of three base64url-encoded strings separated by dots:
1. **Header:** Identifies the token type and hashing algorithm.
   ```json
   {"alg": "HS256", "typ": "JWT"}
   ```
2. **Payload (Claims):** Contains the data claims about the entity and metadata.
   ```json
   {"sub": "alex@example.com", "role": "admin", "exp": 1772500000}
   ```
3. **Signature:** Generated by taking the encoded header, encoded payload, and signing them using a secret key:
   ```text
   HMACSHA256(
     base64UrlEncode(header) + "." + base64UrlEncode(payload),
     secret_key
   )
   ```

**Base64 Encoding vs Encryption (Anti-Tampering):**
- **Base64 is NOT Encryption:** The payload is simply base64url encoded. Anyone can decode it and read the data (e.g., on jwt.io). Never store sensitive secrets (passwords, social security numbers) in a standard JWT payload.
- **Why the Signature Prevents Tampering:** If an attacker modifies the payload (for instance, changing `"role": "user"` to `"role": "admin"`), the server recalculates the signature using its private `secret_key`. The newly calculated signature will not match the token's attached signature, and the server immediately rejects the request with `401 Unauthorized`.

**FastAPI Implementation:**

```python
import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

SECRET_KEY = "super-secret-production-key-change-in-prod"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_seconds: int

def generate_jwt(payload_data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    
    payload = payload_data.copy()
    payload["exp"] = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode().rstrip("=")
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Malformed JWT structure.")
    
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
    
    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise HTTPException(status_code=401, detail="Invalid token signature (tampered token).")
    
    rem = len(payload_b64) % 4
    if rem:
        payload_b64 += "=" * (4 - rem)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    
    if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
        raise HTTPException(status_code=401, detail="Token has expired.")
    
    return payload
```

---

### 6. OAuth 2.0 Authorization Code Flow
> Explain OAuth2 at a conceptual level (you likely won't implement a full provider, but should understand the flow): why does "Sign in with Google" not give the app your Google password? Explain the rough flow: redirect to provider -> user approves -> provider sends back an authorization code -> app exchanges it for an access token.

**Answer:**

**Why "Sign in with Google" Protects User Passwords:**
In traditional authentication, giving an application your credentials means giving full, unrestricted access to your entire account. OAuth 2.0 solves this by acting as a delegated authorization framework:
- The user authenticates directly on Google's own login page (Google domain).
- The client application never receives, intercepts, or stores the user's password.
- Google provides the application with a scoped access token (e.g., read email and profile only) that can be revoked at any time by the user.

**The 4-Step Authorization Code Flow:**

```text
User                  Client App                     Google Identity Provider
 │                         │                                     │
 ├─ 1. Click "Login" ─────>│                                     │
 │                         ├─ Redirect with client_id & scope ──>│
 ├─ 2. Enter Password & Consent Form on Google Domain ──────────>│
 │                         │<─ 3. Redirect back with auth_code ──┤
 │                         │                                     │
 │                         ├─ 4. POST /token (auth_code + secret)─>│
 │                         │<─ Returns access_token & id_token ──┤
```

1. **Redirect to Provider:** The client app redirects the user's browser to the Identity Provider (Google):
   ```text
   GET https://accounts.google.com/o/oauth2/v2/auth?
       response_type=code&
       client_id=APP_CLIENT_ID&
       redirect_uri=https://myapp.com/oauth/callback&
       scope=openid%20profile%20email
   ```
2. **User Approves:** The user logs in on Google's domain and grants the requested permissions.
3. **Provider Returns Authorization Code:** Google redirects the user's browser back to the application's callback URL with a temporary, one-time authorization code:
   ```text
   GET https://myapp.com/oauth/callback?code=4/0AX4XfWh...
   ```
4. **App Server Exchanges Code for Access Token:** The application's backend server sends a secure POST request to Google's token endpoint containing the authorization code and its confidential `client_secret`. Google validates the code and returns an `access_token` (and optional `refresh_token`).

---

### 7. Role-Based Access Control (RBAC) Implementation
> Implement basic role-based authorization: add a `role` field to your users (e.g. `admin`, `user`), and make one endpoint (`DELETE /items/{id}`) return `403 Forbidden` for non-admins even though they're validly authenticated.

**Answer & Implementation:**

**FastAPI Role-Based Access Control Pattern:**

```python
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class CurrentUser(BaseModel):
    id: int
    email: str
    role: UserRole

# Simulated authenticated user resolver
async def get_authenticated_user(authorization: str = Header(...)) -> CurrentUser:
    token_data = verify_jwt(authorization.replace("Bearer ", ""))
    return CurrentUser(
        id=token_data.get("user_id", 1),
        email=token_data.get("sub"),
        role=UserRole(token_data.get("role", "user"))
    )

# Role verification dependency
def require_role(required_role: UserRole):
    def role_checker(current_user: CurrentUser = Depends(get_authenticated_user)) -> CurrentUser:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN_OPERATION",
                        "message": f"Action requires '{required_role.value}' role. Caller possesses '{current_user.role.value}'."
                    }
                }
            )
        return current_user
    return role_checker

router = APIRouter(prefix="/items", tags=["Items"])

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    admin_user: CurrentUser = Depends(require_role(UserRole.ADMIN))
):
    # Only callers with role="admin" execute this block
    return None
```

**HTTP Verification Output:**
- User with role `user` calling `DELETE /items/10`:
  ```http
  HTTP/1.1 403 Forbidden
  Content-Type: application/json

  {
    "error": {
      "code": "FORBIDDEN_OPERATION",
      "message": "Action requires 'admin' role. Caller possesses 'user'."
    }
  }
  ```

---

### 8. Token Expiration and Refresh Tokens
> Explain token expiry and refresh tokens: why should access tokens be short-lived, and what's the purpose of a separate longer-lived refresh token?

**Answer:**

**Why Access Tokens Should Be Short-Lived (e.g., 5 to 15 minutes):**
1. **Minimizing Window of Vulnerability:** Because JWTs are stateless, they cannot be instantly revoked without maintaining a centralized blacklist. If an access token is intercepted over an unsecure network, stored insecurely on client storage, or leaked via logs, the attacker's window of opportunity is strictly limited to the short lifespan of the token.
2. **Mitigating Stale Claims:** If a user's permissions change (e.g., role downgraded from admin to user) or their account is suspended, the changes take effect as soon as the short-lived access token expires.

**Purpose of Longer-Lived Refresh Tokens (e.g., 7 to 30 days):**
1. **Silent Session Renewal:** Refresh tokens allow the client application to obtain a new short-lived access token behind the scenes without forcing the user to repeatedly re-enter their password.
2. **Revocation Control:** Refresh tokens are typically stateful (stored in a database or Redis). When a user logs out, changes their password, or detects suspicious activity, the server immediately revokes the refresh token record.
3. **Restricted Usage:** Refresh tokens are only transmitted to a single dedicated endpoint (`POST /auth/refresh`), minimizing exposure compared to access tokens sent on every API request.
4. **Refresh Token Rotation (RTR):** Every time a refresh token is used, the server invalidates it and issues a brand new refresh token alongside the new access token. If a previously used refresh token is presented again, the server detects potential token theft and invalidates the entire token family.

---

## Execution Proof

```bash
# Register User
curl -X POST http://127.0.0.1:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "securepassword123", "full_name": "Alex Smith", "role": "user"}'

# Login to retrieve JWT Access Token
curl -X POST http://127.0.0.1:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "securepassword123"}'

# Access Protected Endpoint with Bearer Token
curl -X GET http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer <TOKEN>"
```
