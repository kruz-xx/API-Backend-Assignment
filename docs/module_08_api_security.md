# Module 08 — API Security

## Overview
Defensive engineering for REST APIs: robust input validation as the first line of defense using Pydantic schemas, Cross-Origin Resource Sharing (CORS) architecture and preflight request mechanics, mitigating OWASP Top 10 API security risks including Broken Object Level Authorization (BOLA/IDOR) and Broken Authentication, enforcing the Principle of Least Privilege with scoped API keys and tokens, and implementing enterprise secret management practices.

---

## Conceptual Questions & Answers

### 1. Input Validation as the First Line of Defense
> Explain input validation as your first line of defense. Show what could go wrong if client input is trusted blindly (e.g., negative quantity breaking business logic).

**Risks of Trusting Client Input Blindly:**
1. **Negative Quantity Exploit (E-Commerce Inversion Bug)**:
   - Client sends `{"product_id": 101, "quantity": -5}`.
   - `total_price = -5 * $100 = -$500`. Payment processor credits attacker $500 or inventory arithmetic increases warehouse stock out of thin air (`stock - (-5) = stock + 5`).
2. **Integer Overflow & Underflow**:
   - Submitting extreme integers (e.g. $10^{20}$) can trigger database type overflow crashes.
3. **Resource Exhaustion (ReDoS & String Floods)**:
   - Unbounded string lengths in search queries trigger regular expression denial of service.

---

### 2. CORS (Cross-Origin Resource Sharing)
> Explain CORS: why browsers enforce Same-Origin Policy (SOP), what preflight OPTIONS requests do, and why `allow_origins=["*"]` is dangerous with credentials.

**Same-Origin Policy (SOP):**
Browsers block cross-origin HTTP requests initiated from JavaScript scripts unless the target API explicitly permits the origin via CORS headers.

**Why `allow_origins=["*"]` is Dangerous with Credentials:**
1. **Universal Exposure**: Allows any malicious website on the internet to read responses from your API.
2. **Browser Rejection**: The W3C CORS specification forbids combining `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`. Browsers automatically reject such responses to protect user sessions.

---

### 3. The Principle of Least Privilege in API Authorization
> Explain why API keys/tokens should only have access to what they strictly need (scoped authorization).

**Why Blanket Admin Access is Dangerous ("Just for Testing"):**
1. **Minimizing Blast Radius**: If a token scoped only to `analytics:read` is leaked, attackers cannot alter product prices or delete customer records.
2. **Preventing Accidental Operational Damage**: Restricts automated scripts from executing destructive operations.
3. **Audit Compliance**: Enforces non-repudiation and fine-grained attribution for compliance standards (SOC 2, ISO 27001).

---

### 4. Secret Management & Source Control Hygiene
> Explain why secrets must never be committed to git, and how tools prevent leaks (`.gitignore`, secret scanners, Vault).

1. **Git Commit Permanence**: Secrets committed to git remain in historical commit graphs even after file deletion.
2. **Defensive Layers**:
   - **Layer 1 (Local)**: `.gitignore` containing `.env`, `*.pem`, `credentials.json`. Commit `.env.example` with dummy values.
   - **Layer 2 (Pre-Commit)**: Gitleaks / TruffleHog git hooks scanning for high-entropy tokens.
   - **Layer 3 (Runtime)**: Dynamic environment variable injection (`pydantic-settings`).
   - **Layer 4 (Cloud)**: AWS Secrets Manager / HashiCorp Vault for centralized encryption and automatic credential rotation.

---

### 5. OWASP Top 10 API Vulnerabilities: BOLA & Broken Authentication
> Explain Broken Object Level Authorization (BOLA/IDOR) and Broken Authentication.

**BOLA / IDOR (OWASP API Security #1):**
- Occurs when an API accepts an object ID directly from the client (`GET /api/v1/invoices/{id}`) without verifying that the authenticated caller owns or has permission to view that specific record.
- **Remediation**: Always enforce tenancy/ownership validation at the database query level (`db.query(Invoice).filter(Invoice.id == id, Invoice.user_id == current_user.id)`).

---

## Practical: API Security, Input Boundary & BOLA Protection Implementation

### Implementation
**File:** [`src/practicals/module_08_security_demo.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_08_security_demo.py)  
**Tests:** [`tests/test_module_08_security.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_08_security.py)

Implemented:
1. Pydantic input security with custom field validators preventing negative quantities (`quantity > 0` and `unit_price > 0.00`).
2. CORS middleware configured with origin whitelisting (`https://trusted-dashboard.example.com`) and preflight `OPTIONS` support.
3. Least privilege scoped authorization dependencies (`orders:write` vs `analytics:read`) returning `403 Forbidden` for scope mismatches.
4. OWASP BOLA/IDOR protection checking resource ownership against authenticated user identity.

### How I Ran It
```bash
python -m src.practicals.module_08_security_demo
```

### Testing
```bash
pytest tests/test_module_08_security.py -v
```

### Result
```text
======================================================================
Module 08: API Security Practical Run
======================================================================

[1] Testing Negative Quantity Attack:
    Attack Status: 422 Unprocessable Entity (Expected 422)
    Validation Error Details: [{'type': 'greater_than', 'loc': ['body', 'items', 0, 'quantity'], 'msg': 'Input should be greater than 0', 'input': -5, 'ctx': {'gt': 0}}]

[2] Testing CORS Preflight Requests:
    Whitelisted Origin Preflight -> Status: 200, Allow-Origin: https://trusted-dashboard.example.com

[3] Testing Scoped Authorization (Least Privilege):
    Analytics Token on Charge Endpoint -> Status: 403 (Expected 403)
    Detail: {'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': "Token lacks required scope 'orders:write'. Granted: ['analytics:read']"}}
    Payment Token on Charge Endpoint -> Status: 200 (Allowed)

[4] Testing BOLA / IDOR Ownership Verification:
    User 101 reading Invoice #1 -> Status: 200 OK
    User 101 reading Invoice #2 -> Status: 403 Forbidden (Expected 403)
    Detail: {'error': {'code': 'BOLA_VIOLATION', 'message': "Access denied: You do not have permission to access another user's invoice."}}

======================================================================
Module 08 API security verification passed cleanly!
======================================================================
```

### Observations / Learnings
1. **Schema-Level Exploit Blocking**: Setting strict validation constraints (`gt=0`, `le=100`) in Pydantic models automatically blocks inventory manipulation attacks before request payloads ever reach application business logic.
2. **CORS Verification**: Preflight `OPTIONS` requests from whitelisted origins receive explicit `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers.
3. **BOLA Mitigation**: Returning `403 Forbidden` (or `404 Not Found`) when an authenticated caller requests another user's invoice ID cleanly neutralizes horizontal privilege escalation attacks.

### Issues Encountered & Fixes
- **Issue**: Preflight OPTIONS requests were failing when custom authorization headers were missing from `allow_headers`.
- **Fix**: Explicitly added `Authorization`, `Content-Type`, and `X-API-Key` to the CORS middleware header whitelist.
