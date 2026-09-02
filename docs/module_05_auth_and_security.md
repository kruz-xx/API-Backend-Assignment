# Module 05 — Authentication & Authorization

## Overview
Authentication ("who you are") vs Authorization ("what you can do"). Implementation of API key validation, HTTP Basic Authentication mechanics, session-based vs token-based stateless authentication, JSON Web Tokens (JWT) signed with HMAC-SHA256, OAuth 2.0 authorization code flow, Role-Based Access Control (RBAC), and token expiration with refresh token rotation.

---

## Conceptual Questions & Answers

### 1. Authentication vs Authorization
> Explain the difference between authentication ("who are you") and authorization ("what are you allowed to do").

**Comparison:**

| Dimension | Authentication (AuthN) | Authorization (AuthZ) |
| :--- | :--- | :--- |
| **Core Question** | "Who are you?" | "What are you allowed to do?" |
| **Execution Order** | Executes first in request pipeline | Executes after identity is established |
| **Input** | Credentials (password, token, API key) | User identity, assigned roles, permissions |
| **Failure HTTP Status** | `401 Unauthorized` | `403 Forbidden` |
| **Analogy** | Passport verifying identity at border control | Boarding pass granting access to a specific seat |

---

### 2. API Key Authentication
> Implement API key auth via `X-API-Key`. Explain when API keys are appropriate vs when they are not.

**When Appropriate:**
- Server-to-server / Machine-to-machine (M2M) communication between trusted backends.
- Tracking developer quotas and rate limits across organization accounts (e.g. Stripe, SendGrid).
- Webhooks and scheduled background cron jobs.

**When NOT Appropriate:**
- Client-side Single Page Applications (SPAs) or mobile apps representing individual human users. Static keys stored on client devices can be easily extracted by attackers.
- Scenarios requiring fine-grained user delegation, password resets, and session management.

---

### 3. HTTP Basic Authentication
> Explain Basic Auth (`username:password` base64-encoded) and why it is rarely used alone in modern APIs.

**Why Basic Auth is Inadequate for Modern APIs:**
1. **Credentials Sent on Every Request**: Plaintext credentials are sent with each HTTP call. If any single request is intercepted, the permanent password is compromised.
2. **No Expiration (TTL)**: Basic Auth credentials remain valid indefinitely until manually changed.
3. **No Granular Scopes**: Basic Auth grants full account access with no scoped permissions.
4. **Reversible Encoding**: Base64 is an encoding scheme, not encryption; anyone who inspects the header can decode `username:password` instantly.

---

### 4. Sessions vs Tokens & HTTP Statelessness
> Explain how sessions work around HTTP statelessness and contrast with stateless token-based auth (JWT).

- **Session-Based (Stateful)**: The server stores session state in an in-memory/Redis store and sets an opaque `session_id` cookie. On each request, the server queries the database/cache to look up user state.
- **Token-Based / JWT (Stateless)**: The token itself contains the user identity, roles, and expiration timestamp (`sub`, `role`, `exp`). The server verifies the cryptographic signature with its secret key without querying a session database on every request.

---

### 5. JWT Anatomy & Cryptographic Signature
> Explain JWT 3 parts (header, payload, signature) and why signature prevents tampering even though payload is just base64 (NOT encrypted).

**Anatomy (`Header.Payload.Signature`):**
1. **Header**: Specifies token type and algorithm (`{"alg": "HS256", "typ": "JWT"}`).
2. **Payload**: JSON claims (`{"sub": "alex@example.com", "role": "admin", "exp": 1772500000}`).
3. **Signature**: Cryptographic hash: `HMAC-SHA256(base64(header) + "." + base64(payload), secret_key)`.

**Anti-Tampering Protection:**
- Base64 is public and human-readable (not encrypted).
- If an attacker modifies the payload (e.g. changing `"role": "customer"` to `"role": "admin"`), the server recalculates the signature using its private `secret_key`. Because the attacker does not have the secret key, the computed signature will not match the token's attached signature, and the server rejects the request with `401 Unauthorized`.

---

### 6. OAuth 2.0 Authorization Code Flow
> Explain the 4-step OAuth2 flow: redirect to provider -> user approves -> provider returns code -> app exchanges code for access token.

1. **Redirect**: Client redirects user browser to Identity Provider (Google, GitHub) with `client_id`, `redirect_uri`, and requested `scopes`.
2. **User Consent**: User enters credentials securely on Google's domain and grants permissions.
3. **Authorization Code**: Provider redirects back to client callback URI with a temporary, one-time `code`.
4. **Token Exchange**: Client backend exchanges the `code` + confidential `client_secret` with the provider's token endpoint to receive an `access_token`.

---

## Practical: Authentication, JWT & RBAC Implementation

### Implementation
**File:** [`src/practicals/module_05_auth_demo.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_05_auth_demo.py)  
**Service:** [`src/services/auth.py`](file:///c:/office%20files/api-backend-assignment/src/services/auth.py)  
**Tests:** [`tests/test_module_05_auth.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_05_auth.py)

Implemented:
1. API Key authentication via `X-API-Key` header with `401` rejection for missing/invalid keys.
2. Cryptographic JWT token issuance and signature verification with HMAC-SHA256.
3. Signature tampering detection and expiration check.
4. Role-Based Access Control (RBAC) dependency (`require_admin`) returning `403 Forbidden` for customers and `200 OK` for administrators.

### How I Ran It
```bash
python -m src.practicals.module_05_auth_demo
```

### Testing
```bash
pytest tests/test_module_05_auth.py -v
```

### Result
```text
======================================================================
Module 05: Authentication & Authorization Practical Run
======================================================================

[1] API Key Auth (Valid): Status 200, Body: {'status': 'success', 'client': 'payment_worker', 'tier': 'enterprise'}
    API Key Auth (Invalid): Status 401, Body: {'error': {'code': 'INVALID_API_KEY', 'message': 'Provided API key is invalid.'}}

[2] Customer Login -> Status: 200
    Generated Token: eyJhbGciOiAiSFMyNTYiLCAidHlwIj...
    Admin Login -> Status: 200

[3] GET /api/users/me (Customer Auth) -> Status: 200, Role: customer

[4] RBAC Protection (Customer calling DELETE /items/42) -> Status: 403 (Expected 403)
    Error Response: {'error': {'code': 'FORBIDDEN_OPERATION', 'message': "Action requires 'admin' privileges. Caller has 'customer'."}}
    RBAC Protection (Admin calling DELETE /items/42) -> Status: 200 (Allowed)

[5] Tampered JWT Test -> Status: 401 (Expected 401)
    Tamper Detection Detail: {'error': {'code': 'SIGNATURE_VERIFICATION_FAILED', 'message': 'Token signature mismatch (tampering detected).'}}

======================================================================
Module 05 authentication, JWT & RBAC tests passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Constant-Time Comparison**: Used `hmac.compare_digest()` for signature comparison to eliminate side-channel timing attacks where an attacker measures response times to guess valid signature bytes.
2. **Base64 URL Padding**: Base64url tokens omit trailing `=` padding in standard headers. Re-padding (`rem = len(b64) % 4`) is required before decoding with Python's standard `base64` library.
3. **Role Enforcement Separation**: Authentication dependencies (`get_current_user`) establish caller identity (401 on failure), while RBAC dependencies (`require_admin`) enforce authorization permissions (403 on failure).

### Issues Encountered & Fixes
- **Issue**: Token decoding failed when payload base64 string had length not divisible by 4.
- **Fix**: Added dynamic padding logic `payload_b64 += "=" * (4 - rem)` prior to decode.
