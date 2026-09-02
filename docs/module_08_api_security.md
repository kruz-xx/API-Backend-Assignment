# Module 08 — API Security

## Overview
Defensive engineering for REST APIs: robust input validation as the first line of defense using Pydantic schemas, Cross-Origin Resource Sharing (CORS) architecture and preflight request mechanics, mitigating OWASP Top 10 API security risks including Broken Object Level Authorization (BOLA/IDOR) and Broken Authentication, enforcing the Principle of Least Privilege with scoped API keys and tokens, and implementing enterprise secret management practices (.gitignore, environment variables, secret managers, and automated scanning).

---

## Conceptual Questions & Implementation Notes

### 1. Input Validation as the First Line of Defense
> Explain input validation as your first line of defense — tie back to Module 2's Pydantic validation. Show what could go wrong if you trusted client input blindly (e.g., a negative "quantity" field breaking your business logic).

**Answer:**

#### Why Input Validation is Critical

Input validation ensures that data entering the API conforms strictly to expected data types, formats, constraints, and ranges before it reaches core business logic, database queries, or downstream services. 

Treating client input as inherently untrusted is the foundational principle of defensive API design. Relying solely on client-side frontend validation is dangerous because attackers can easily bypass browser UI validation by using `curl`, Postman, or custom automated HTTP clients.

---

#### What Goes Wrong When Client Input is Trusted Blindly

1. **Negative Quantity Exploit (E-Commerce Inversion Bug):**
   - **Scenario:** A client submits a checkout order with a negative item quantity: `{"product_id": 101, "quantity": -5}`.
   - **Business Impact:**
     * `total_price = quantity * unit_price = -5 * $100 = -$500`.
     * Instead of charging the user $500, the payment processor calculates a negative charge, potentially crediting $500 to the attacker's account or deducting inventory negatively (increasing warehouse stock count out of thin air: `inventory = inventory - (-5) = inventory + 5`).

2. **Integer Overflow & Underflow:**
   - Submitting extreme integer values (e.g., `quantity: 99999999999999999999`) can cause numeric overflows in downstream databases or billing pipelines.

3. **Type Confusion & Null-Byte Injections:**
   - Supplying an array or nested object where a string is expected can trigger uncaught exceptions in backend handlers, crashing worker threads (`HTTP 500`).

4. **Resource Exhaustion (Large Payloads & String Expansion):**
   - Unlimited string lengths in search queries or text fields can trigger Denial of Service via regular expression catastrophe (ReDoS) or memory exhaustion.

---

#### Pydantic Validation Implementation

In FastAPI, Pydantic models intercept, validate, coerce, and sanitize incoming JSON payloads at the routing boundary before route handlers execute.

```python
from decimal import Decimal
from typing import List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

security_app = FastAPI(title="Input Validation Demo")

class OrderItemSchema(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID must be a positive integer")
    quantity: int = Field(..., gt=0, le=100, description="Quantity must be between 1 and 100")
    unit_price: Decimal = Field(..., gt=Decimal("0.00"), description="Unit price must be strictly positive")

    @field_validator("quantity")
    @classmethod
    def validate_nonzero_quantity(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Quantity must be greater than zero. Negative quantities are rejected.")
        return value

class CreateOrderRequest(BaseModel):
    customer_id: int = Field(..., gt=0)
    items: List[OrderItemSchema] = Field(..., min_length=1, description="Order must contain at least one item")

@security_app.post("/api/v1/orders/checkout", status_code=status.HTTP_201_CREATED)
async def checkout_order(order: CreateOrderRequest):
    total = sum(item.quantity * item.unit_price for item in order.items)
    return {
        "status": "success",
        "order_id": 9941,
        "customer_id": order.customer_id,
        "total_amount": float(total),
        "item_count": sum(item.quantity for item in order.items)
    }
```

---

#### Automated Client Test Script & Execution Output

```python
from fastapi.testclient import TestClient

client = TestClient(security_app)

def run_input_validation_tests():
    endpoint = "/api/v1/orders/checkout"
    
    print("--- TEST 1: Malicious Negative Quantity Payload ---")
    malicious_payload = {
        "customer_id": 42,
        "items": [
            {"product_id": 101, "quantity": -5, "unit_price": 100.00}
        ]
    }
    res1 = client.post(endpoint, json=malicious_payload)
    print(f"Status Code: {res1.status_code} Unprocessable Entity")
    print(f"Response Error Body: {res1.json()}\n")

    print("--- TEST 2: Valid Order Payload ---")
    valid_payload = {
        "customer_id": 42,
        "items": [
            {"product_id": 101, "quantity": 2, "unit_price": 49.99}
        ]
    }
    res2 = client.post(endpoint, json=valid_payload)
    print(f"Status Code: {res2.status_code} Created")
    print(f"Response Body: {res2.json()}")

if __name__ == "__main__":
    run_input_validation_tests()
```

#### Terminal Execution Output

```text
--- TEST 1: Malicious Negative Quantity Payload ---
Status Code: 422 Unprocessable Entity
Response Error Body: {'detail': [{'type': 'greater_than', 'loc': ['body', 'items', 0, 'quantity'], 'msg': 'Input should be greater than 0', 'input': -5, 'ctx': {'gt': 0}}]}

--- TEST 2: Valid Order Payload ---
Status Code: 201 Created
Response Body: {'status': 'success', 'order_id': 9941, 'customer_id': 42, 'total_amount': 99.98, 'item_count': 2}
```

---

#### Verification via curl

**1. Attack Attempt (Negative Quantity Rejected with HTTP 422):**
```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/orders/checkout" \
     -H "Content-Type: application/json" \
     -d '{"customer_id": 42, "items": [{"product_id": 101, "quantity": -5, "unit_price": 100.00}]}'
```

*Raw HTTP Response:*
```http
HTTP/1.1 422 Unprocessable Entity
content-type: application/json
content-length: 139

{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "items", 0, "quantity"],
      "msg": "Input should be greater than 0",
      "input": -5,
      "ctx": {"gt": 0}
    }
  ]
}
```

---

### 2. CORS (Cross-Origin Resource Sharing)
> Explain CORS (Cross-Origin Resource Sharing): why does a browser block a frontend on `example.com` from calling an API on `api.otherdomain.com` by default, and what response headers does the server need to send to explicitly allow it? Configure CORS on your FastAPI/Flask app to allow requests only from a specific origin. Why is `allow_origins=["*"]` dangerous with cookies or credentials?

**Answer:**

#### Why Browsers Enforce the Same-Origin Policy (SOP)

The **Same-Origin Policy (SOP)** is a foundational security mechanism implemented by web browsers. Two URLs share the same origin only if their **protocol (scheme)**, **hostname (domain)**, and **port** are identical.

- **Origin A:** `https://example.com:443`
- **Origin B:** `https://api.otherdomain.com:443` (Different domain -> Cross-origin)

**The Threat without SOP:**
If user `Alice` logs into `bank.com`, the browser stores her authentication session cookie. If Alice navigates to `evil-site.com`, JavaScript running on `evil-site.com` could make an asynchronous `fetch("https://bank.com/api/transfer", {credentials: "include"})`. Without SOP, the browser would automatically attach Alice's `bank.com` session cookies, executing unauthorized wire transfers on her behalf.

By default, browsers block cross-origin HTTP requests initiated from JavaScript scripts unless the target API explicitly grants permission using **CORS headers**.

---

#### CORS Preflight (`OPTIONS`) Request Mechanics

When a browser makes a "non-simple" cross-origin request (e.g., methods other than `GET`/`POST`/`HEAD`, or requests containing custom headers like `Authorization` or `Content-Type: application/json`), the browser automatically sends an HTTP `OPTIONS` preflight request prior to sending the actual request.

```
+-----------------------------------------------------------------------------------+
|                            CORS PREFLIGHT WORKFLOW                                |
+-----------------------------------------------------------------------------------+

1. Browser sends Preflight:
   Browser ----------------- OPTIONS /api/v1/data -----------------> Server
   Origin: https://app.trusted-client.com
   Access-Control-Request-Method: POST
   Access-Control-Request-Headers: Authorization, Content-Type

2. Server checks origin and responds with permissions:
   Server ------------------ HTTP/1.1 200 OK ----------------------> Browser
   Access-Control-Allow-Origin: https://app.trusted-client.com
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: Authorization, Content-Type
   Access-Control-Allow-Credentials: true
   Access-Control-Max-Age: 86400

3. Browser verifies headers and transmits actual request:
   Browser ------------------ POST /api/v1/data -------------------> Server
   Authorization: Bearer <token>
   Content-Type: application/json
```

---

#### Key Server CORS Response Headers

1. **`Access-Control-Allow-Origin`:** Specifies which origins are permitted to read the response (e.g., `https://app.mydomain.com`).
2. **`Access-Control-Allow-Methods`:** Comma-separated list of allowed HTTP methods (e.g., `GET, POST, PUT, DELETE, OPTIONS`).
3. **`Access-Control-Allow-Headers`:** Comma-separated list of permitted request headers (e.g., `Authorization, Content-Type, X-API-Key`).
4. **`Access-Control-Allow-Credentials`:** When set to `true`, indicates that the browser is permitted to expose the response to frontend JavaScript when the request was made with credentials (cookies or HTTP Authorization headers).
5. **`Access-Control-Max-Age`:** The duration in seconds that preflight results can be cached by the browser (avoiding repetitive `OPTIONS` requests).

---

#### Why `allow_origins=["*"]` is Dangerous with Credentials

1. **Information Leakage & CSRF Exploitation:**
   - Setting `allow_origins=["*"]` allows any website on the internet (including `malicious-phishing.com`) to execute requests against your API and read the responses.
2. **Browser Security Restriction:**
   - The W3C/WHATWG CORS specification strictly forbids the combination of `Access-Control-Allow-Origin: *` and `Access-Control-Allow-Credentials: true`. Browsers automatically reject and block such responses to prevent global credential exposure.

---

#### Production-Ready CORS Configuration in FastAPI

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

cors_app = FastAPI(title="Secure CORS Configured API")

# Explicitly whitelist only trusted frontend origins
ALLOWED_ORIGINS = [
    "https://dashboard.example.com",
    "https://admin.example.com",
    "http://localhost:3000"  # Local development frontend
]

cors_app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    max_age=86400  # Cache preflight response for 24 hours
)

@cors_app.get("/api/v1/secure-data")
async def get_secure_data():
    return {"message": "Access granted from authorized origin."}
```

---

#### Automated Preflight Test Script & Execution Output

```python
from fastapi.testclient import TestClient

cors_client = TestClient(cors_app)

def run_cors_tests():
    endpoint = "/api/v1/secure-data"
    
    print("--- TEST 1: Preflight from Whitelisted Origin ---")
    headers_valid = {
        "Origin": "https://dashboard.example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"
    }
    res1 = cors_client.options(endpoint, headers=headers_valid)
    print(f"Status: {res1.status_code} OK")
    print(f"Access-Control-Allow-Origin: {res1.headers.get('access-control-allow-origin')}")
    print(f"Access-Control-Allow-Credentials: {res1.headers.get('access-control-allow-credentials')}")
    print(f"Access-Control-Allow-Methods: {res1.headers.get('access-control-allow-methods')}\n")

    print("--- TEST 2: Preflight from Unauthorized Origin ---")
    headers_invalid = {
        "Origin": "https://evil-untrusted-site.com",
        "Access-Control-Request-Method": "GET"
    }
    res2 = cors_client.options(endpoint, headers=headers_invalid)
    print(f"Status: {res2.status_code}")
    print(f"Access-Control-Allow-Origin: {res2.headers.get('access-control-allow-origin')} (Not reflected - blocked by browser)")

if __name__ == "__main__":
    run_cors_tests()
```

#### Terminal Execution Output

```text
--- TEST 1: Preflight from Whitelisted Origin ---
Status: 200 OK
Access-Control-Allow-Origin: https://dashboard.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS

--- TEST 2: Preflight from Unauthorized Origin ---
Status: 400
Access-Control-Allow-Origin: None (Not reflected - blocked by browser)
```

---

#### Verification via curl

**1. Preflight Request from Authorized Origin:**
```bash
curl -i -X OPTIONS "http://127.0.0.1:8000/api/v1/secure-data" \
     -H "Origin: https://dashboard.example.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization"
```

*Raw HTTP Response:*
```http
HTTP/1.1 200 OK
access-control-allow-origin: https://dashboard.example.com
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
access-control-allow-headers: authorization
access-control-max-age: 86400
content-length: 0
```

---

### 3. The Principle of Least Privilege in API Authorization
> Explain the principle of least privilege applied to APIs: why an API key/token should only have access to what it strictly needs, not blanket admin access, even if it's "just for testing."

**Answer:**

#### Principle of Least Privilege (PoLP)

The **Principle of Least Privilege (PoLP)** dictates that every identity (end-user, background worker, external service, or API consumer) must be granted only the minimum set of permissions strictly necessary to perform its intended business function, and nothing more.

---

#### Why Blanket Admin Access is Dangerous ("Just for Testing" Anti-Pattern)

1. **Blast Radius Minimization:**
   - If an API key with blanket administrative privileges (`*.*` or `admin:all`) is compromised through log leakage, source code exposure, or man-in-the-middle interception, the attacker gains full control over the entire system (dropping tables, downloading customer PII, changing payment credentials).
   - If a narrowly scoped API key (`reports:read`) is leaked, the blast radius is strictly confined to reading reports for that specific service.

2. **Accidental Operational Catastrophes:**
   - A developer or automated script running with blanket admin access can execute destructive commands by mistake (e.g., running `DELETE /api/v1/users` instead of a local test database cleanup).

3. **Insider Threats & Audit Non-Repudiation:**
   - When all services and developers share master admin credentials, audit logs cannot attribute actions to specific individuals or sub-services, violating compliance frameworks (SOC 2, ISO 27001, HIPAA, PCI-DSS).

---

#### Scoped Authorization Architecture

```
+-----------------------------------------------------------------------------------+
|                        SCOPED AUTHORIZATION MATRIX                                |
+-----------------------------------------------------------------------------------+

Token / Identity           Permitted Scopes                    Rejected Actions
-------------------------------------------------------------------------------------
Payment Worker Token       ["orders:charge", "orders:read"]   Cannot delete products (403)
Analytics Ingest Token     ["analytics:write"]                Cannot view user PII (403)
Customer Support Token     ["users:read", "orders:read"]      Cannot modify billing (403)
Super Admin (MFA Only)     ["*"]                              Restricted by IP & MFA
```

---

#### Implementation of Scoped Token Verification in FastAPI

```python
from typing import List, Set
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

auth_app = FastAPI(title="Scoped Least Privilege API")
security = HTTPBearer()

# Simulated token database with assigned scopes
TOKEN_SCOPES_DB = {
    "token_analytics_123": {"client_id": "analytics_bot", "scopes": {"analytics:read"}},
    "token_payment_456": {"client_id": "payment_service", "scopes": {"orders:read", "orders:write"}},
}

def require_scopes(required_scopes: List[str]):
    """
    Dependency factory enforcing least-privilege scope checks.
    """
    def scope_checker(credentials: HTTPAuthorizationCredentials = Security(security)):
        token = credentials.credentials
        client_data = TOKEN_SCOPES_DB.get(token)
        
        if not client_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "message": "Authentication token is invalid or expired."}}
            )
            
        token_scopes: Set[str] = client_data["scopes"]
        for scope in required_scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "INSUFFICIENT_PERMISSIONS",
                            "message": f"Token lacks required scope: '{scope}'. Granted scopes: {list(token_scopes)}"
                        }
                    }
                )
        return client_data
    return scope_checker

@auth_app.post("/api/v1/orders/{order_id}/charge", dependencies=[Depends(require_scopes(["orders:write"]))])
async def charge_order(order_id: int):
    return {"status": "success", "message": f"Order {order_id} charged successfully."}

@auth_app.get("/api/v1/analytics/metrics", dependencies=[Depends(require_scopes(["analytics:read"]))])
async def get_metrics():
    return {"status": "success", "metric": "cpu_utilization", "value": "42%"}
```

---

#### Automated Scope Verification Test Script & Execution Output

```python
from fastapi.testclient import TestClient

client = TestClient(auth_app)

def run_least_privilege_tests():
    print("--- TEST 1: Analytics token calling charge endpoint (Scope Mismatch) ---")
    headers_analytics = {"Authorization": "Bearer token_analytics_123"}
    res1 = client.post("/api/v1/orders/101/charge", headers=headers_analytics)
    print(f"Status: {res1.status_code} Forbidden")
    print(f"Response: {res1.json()}\n")

    print("--- TEST 2: Payment token calling charge endpoint (Scope Match) ---")
    headers_payment = {"Authorization": "Bearer token_payment_456"}
    res2 = client.post("/api/v1/orders/101/charge", headers=headers_payment)
    print(f"Status: {res2.status_code} OK")
    print(f"Response: {res2.json()}")

if __name__ == "__main__":
    run_least_privilege_tests()
```

#### Terminal Execution Output

```text
--- TEST 1: Analytics token calling charge endpoint (Scope Mismatch) ---
Status: 403 Forbidden
Response: {'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': "Token lacks required scope: 'orders:write'. Granted scopes: ['analytics:read']"}}

--- TEST 2: Payment token calling charge endpoint (Scope Match) ---
Status: 200 OK
Response: {'status': 'success', 'message': 'Order 101 charged successfully.'}
```

---

### 4. Secret Management and Source Control Hygiene
> Explain why secrets (API keys, DB passwords, JWT signing secrets) should never be committed to source control, and what tools/practices prevent it (`.gitignore`, environment variables, secret managers like AWS Secrets Manager/Vault — conceptual awareness is enough).

**Answer:**

#### Why Secrets Must Never Be Committed to Source Control

1. **Git History is Permanent:**
   - When a commit containing a secret is pushed to a remote repository (e.g., GitHub or GitLab), the secret becomes permanently etched into the repository's `.git` commit graph.
   - Simply deleting the secret in a subsequent commit does **not** remove it from the historical git object log; anyone can inspect older revisions (`git log`, `git checkout`) to extract the credential.

2. **Automated Threat Scrapers:**
   - Public code repositories are actively monitored by automated botnets that scan new commits within seconds of publication to harvest AWS keys, Stripe tokens, and database credentials for crypto-mining and data theft.

3. **Environment Segregation Breakdown:**
   - Hardcoded secrets make it impossible to maintain distinct credentials for Development, Staging, and Production environments, leading to accidental testing against production databases.

---

#### Defensive Layers: Tools and Best Practices

```
+-----------------------------------------------------------------------------------+
|                        SECRET MANAGEMENT DEFENSE LAYERS                           |
+-----------------------------------------------------------------------------------+

Layer 1: Local Prevention        -> .gitignore, .env.example
Layer 2: Pre-Commit Scanning     -> Gitleaks, Git-secrets, TruffleHog hooks
Layer 3: CI/CD Secret Scanning   -> GitHub Secret Scanning, Push Protection
Layer 4: Runtime Injection       -> Environment variables, Pydantic-Settings
Layer 5: Enterprise Secrets Mgmt -> AWS Secrets Manager, HashiCorp Vault, Azure Key Vault
```

1. **`.gitignore` Configuration:**
   - Ensures local configuration files containing plaintext credentials are never tracked by Git.
   - Example `.gitignore` entries:
     ```gitignore
     .env
     .env.local
     .env.*.local
     *.pem
     *.key
     credentials.json
     secrets/
     ```

2. **Environment Variables & Configuration Schemas:**
   - Applications should load configuration dynamically at runtime from environment variables using tools like `pydantic-settings` or `os.environ`.
   - Provide a sanitized `.env.example` template without real secrets:
     ```bash
     # .env.example (Safe to commit)
     DATABASE_URL=postgresql://user:password@localhost:5432/app_db
     JWT_SECRET_KEY=change_me_in_production
     STRIPE_API_KEY=sk_test_placeholder
     ```

3. **Automated Secret Scanners & Pre-Commit Hooks:**
   - **Gitleaks / TruffleHog / Git-secrets:** Run automatically as local git pre-commit hooks to inspect staged files for high-entropy strings, regex patterns matching known provider tokens (e.g., AWS `AKIA...`, GitHub `ghp_...`, Stripe `sk_live_...`), rejecting commits containing secrets.
   - **GitHub Secret Scanning & Push Protection:** Blocks commits containing leaked secrets at the git-push phase.

4. **Dedicated Cloud Secret Managers:**
   - **AWS Secrets Manager / HashiCorp Vault / Azure Key Vault / GCP Secret Manager:**
     * Centralized, encrypted secret storage with strict IAM access policies.
     * Support **Dynamic Secret Generation** and **Automated Secret Rotation** (e.g., rotating database passwords every 30 days without application downtime).
     * Secrets are fetched securely into memory at runtime via IAM instance profiles, completely eliminating static credentials from filesystem disks.

---

#### Incident Response: What to Do If a Secret is Leaked

If a credential is accidentally committed to source control:
1. **Immediate Revocation and Rotation:** Revoke the exposed credential immediately in the provider dashboard (Stripe, AWS, database). Do not wait to clean up git history first.
2. **Audit Access Logs:** Inspect access logs for the leaked key to identify any unauthorized operations executed during the exposure window.
3. **Scrub Git History:** Use tools like `git-filter-repo` or BFG Repo-Cleaner to completely purge the commit and historical objects containing the credential across all branches and tags.

---

### 5. OWASP Top 10 API Vulnerabilities: BOLA & Broken Authentication
> Detail Broken Object Level Authorization (BOLA/IDOR) and Broken Authentication. How do we prevent a user from accessing another user's resources?

**Answer:**

#### 1. Broken Object Level Authorization (BOLA / IDOR)

- **Definition:** BOLA (also known as Insecure Direct Object Reference or IDOR) is the #1 vulnerability on the OWASP API Security Top 10. It occurs when an API endpoint accepts an object identifier (e.g., `/api/v1/documents/{doc_id}`) directly from the client and retrieves the object from the database **without verifying that the authenticated user owns or has permission to view that specific record**.

- **Vulnerable Code Example:**
  ```python
  # VULNERABLE: Direct lookup by ID without tenancy/ownership verification
  @app.get("/api/v1/invoices/{invoice_id}")
  async def get_invoice(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
      invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
      if not invoice:
          raise HTTPException(status_code=404, detail="Invoice not found")
      # Bug: User 5 can read User 99's private invoice simply by guessing the ID!
      return invoice
  ```

- **Remediation / Secure Implementation:**
  ```python
  # SECURE: Scope database query strictly to current_user.id
  @app.get("/api/v1/invoices/{invoice_id}")
  async def get_invoice_secure(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
      invoice = db.query(Invoice).filter(
          Invoice.id == invoice_id,
          Invoice.owner_id == current_user.id  # Ownership validation enforced at DB query level
      ).first()
      
      if not invoice:
          # Return 404 to avoid leaking existence of other users' records
          raise HTTPException(status_code=404, detail="Invoice not found")
          
      return invoice
  ```

---

#### 2. Broken Authentication

- **Definition:** Flaws in authentication mechanisms that allow attackers to compromise passwords, keys, or session tokens, or exploit implementation bugs to assume other users' identities.
- **Common Vulnerabilities:**
  * Lack of rate limiting on password reset and login endpoints (enabling brute-force and credential stuffing).
  * Accepting weak passwords or missing multi-factor authentication (MFA).
  * Exposing sensitive session tokens in URLs or query strings.
  * Failing to validate JWT cryptographic signatures (e.g., accepting `alg: none` or unsigned tokens).
- **Remediation:**
  * Enforce strict password hashing with modern memory-hard algorithms (`Argon2id` or `bcrypt` with work factor >= 12).
  * Implement sliding window rate limiting on all authentication routes.
  * Always verify JWT signature algorithm (`HS256`/`RS256`), issuer (`iss`), audience (`aud`), and expiration (`exp`).

---

## Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_08/` and link them below)*

```markdown
<!-- Example screenshot embed:
![CORS Preflight Response Headers](../screenshots/module_08/cors_headers.png)
![Security Validation Rejection](../screenshots/module_08/security_injection_blocked.png)
-->
```
