# Module 01 — HTTP Fundamentals

## Overview
Deep dive into the HTTP protocol, the URL request lifecycle (DNS, TCP, TLS handshake), HTTP methods, headers, status codes, and inspecting live HTTP traffic.

---

## Conceptual Questions & Answers

### 1. Journey of a URL in browser
> Explain what happens, step by step, when you type a URL into a browser and hit enter — DNS lookup, TCP connection, TLS handshake (if HTTPS), HTTP request sent, server processing, HTTP response received, rendering.

**Answer:**

When we enter a URL into the browser and hit enter, a sequence of events occurs:

A. **DNS Lookup**: The browser translates the human-readable domain name (e.g. `example.com`) into an IP address via a DNS server query (checking browser cache, OS cache, router cache, and recursive DNS resolvers).

B. **TCP Connection**: Once the IP address is known, the client establishes a reliable TCP connection using the **three-way handshake** (`SYN` -> `SYN-ACK` -> `ACK`). This guarantees reliable, ordered packet delivery.

C. **TLS Handshake (HTTPS)**: For HTTPS connections over port 443, the client and server negotiate cryptographic parameters (ciphers, TLS version), verify the server's SSL certificate, and generate symmetric session keys.

D. **HTTP Request**: The browser sends a formatted text-based HTTP request containing the request line (Method, Path, Protocol), headers, and optional payload (e.g., `GET /index.html HTTP/1.1`).

E. **Server Processing & HTTP Response**: The server processes the request, queries databases or runs application logic, and returns an HTTP response consisting of a status line (e.g., `HTTP/1.1 200 OK`), response headers (`Content-Type`, `Cache-Control`), and the payload.

F. **Rendering**: The browser parses the HTML, builds the DOM and CSSOM trees, executes JavaScript, and sends subsequent requests for external assets (stylesheets, scripts, images).

---

### 2. Anatomy of an HTTP Request & Response
> Explain an HTTP request in detail including: Request Line (Method, Path, Protocol version), Headers, and the Body (payload), with examples for each. Also the anatomy of a response: status lines, headers, body.

**Answer:**

**Anatomy of an HTTP Request:**
- **Request Line**: `GET /api/v1/items?category=books HTTP/1.1` (Verb + Path/Query + Protocol)
- **Request Headers**: Key-value pairs with metadata (`Host: api.example.com`, `User-Agent: curl/8.4`, `Authorization: Bearer token123`, `Accept: application/json`)
- **Request Body**: Optional data payload (e.g., JSON string sent with `POST`, `PUT`, or `PATCH`).

**Anatomy of an HTTP Response:**
- **Status Line**: `HTTP/1.1 200 OK` (Protocol + Numeric Status Code + Reason Phrase)
- **Response Headers**: Metadata describing response state (`Content-Type: application/json`, `Content-Length: 128`, `ETag: "w/123"`, `Cache-Control: max-age=60`)
- **Response Body**: Data payload returned to the client (e.g., JSON object, HTML text, or binary stream).

---

### 3. HTTP Methods
> Detail the differences between `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, and `TRACE`.

**Answer:**

- `GET`: Safe & idempotent retrieval of resource representations without server state mutation.
- `POST`: Non-idempotent creation of new subordinate resources or arbitrary processing.
- `PUT`: Idempotent complete replacement/creation of a resource at the target URI.
- `PATCH`: Non-idempotent partial modification of an existing resource.
- `DELETE`: Idempotent removal of the specified resource.
- `HEAD`: Identical to `GET` but returns headers only without the message body (used for checking resource existence or headers).
- `OPTIONS`: Describes communication options and permitted HTTP verbs for the target resource (essential for CORS preflight).
- `TRACE`: Diagnostic loopback performing a message echo test.

---

### 4. Idempotency and Safe Methods
> Define HTTP idempotency. Which methods are safe? Which are idempotent? Explain how PUT, DELETE, and PATCH differ in this regard.

**Answer:**

- **Safe Methods** (`GET`, `HEAD`, `OPTIONS`): Read-only operations that do not modify server state.
- **Idempotent Methods** (`GET`, `HEAD`, `PUT`, `DELETE`, `OPTIONS`): Making $N > 1$ identical requests produces the exact same server side effect as making a single request.
- **PUT vs PATCH vs DELETE**:
  - `PUT` is idempotent because replacing a resource with state $X$ multiple times leaves the resource in state $X$.
  - `DELETE` is idempotent because deleting resource #42 once removes it; subsequent deletes continue to result in the resource being absent.
  - `PATCH` is generally not idempotent by default because operations like `{"increment": 1}` compound changes on each execution.

---

### 5. PUT vs. PATCH
> Explain the difference between PUT and PATCH precisely.

**Answer:**

- **`PUT` (Full Replacement)**: The client sends a complete representation. Any omitted optional fields are either reset to default null values or overwritten.
- **`PATCH` (Partial Update)**: The client transmits only the delta / modified attributes (e.g. updating solely the `price` field), leaving all other fields intact.

---

### 6. HTTP Status Codes
> Explain the 5 status code categories (1xx, 2xx, 3xx, 4xx, 5xx) with specific examples.

**Answer:**

- **1xx (Informational)**: Protocol negotiation (`100 Continue`, `101 Switching Protocols`).
- **2xx (Success)**: `200 OK` (Standard success), `201 Created` (Resource created via POST), `204 No Content` (Success with empty body, common for DELETE).
- **3xx (Redirection)**: `301 Moved Permanently`, `304 Not Modified` (Cache revalidation match).
- **4xx (Client Error)**: `400 Bad Request` (Malformed syntax), `401 Unauthorized` (Unauthenticated), `403 Forbidden` (Authenticated but lacking permission), `404 Not Found`, `409 Conflict` (Duplicate record), `422 Unprocessable Entity` (Schema validation failure), `429 Too Many Requests` (Rate limit exceeded).
- **5xx (Server Error)**: `500 Internal Server Error` (Unhandled exception), `502 Bad Gateway` (Upstream proxy error), `503 Service Unavailable` (Server overloaded/maintenance).

---

### 7. 401 Unauthorized vs. 403 Forbidden
> Explain the precise difference between `401 Unauthorized` and `403 Forbidden`.

**Answer:**

- `401 Unauthorized`: "Authentication required" — the caller has not provided valid credentials or authentication token.
- `403 Forbidden`: "Permission denied" — the caller's identity is authenticated, but their role/permissions do not authorize this specific operation.

---

### 8. HTTP Headers
> Explain common request and response headers (`Content-Type`, `Authorization`, `Accept`, `User-Agent`, `Cache-Control`, `Set-Cookie`).

**Answer:**

- `Content-Type`: MIME type of the payload body (e.g., `application/json`).
- `Authorization`: Credentials for authenticating the client (e.g., `Bearer <JWT>`).
- `Accept`: Content types the client is capable of parsing (e.g., `application/json, text/html`).
- `User-Agent`: String identifying client software, operating system, and version.
- `Cache-Control`: Directives governing browser and CDN caching policies (e.g., `public, max-age=300`).
- `Set-Cookie`: Transmits cookie data from server to client browser.

---

### 9. HTTPS vs. HTTP
> Explain the differences between HTTP and HTTPS. What TLS/SSL actually protects against.

**Answer:**

HTTPS encrypts traffic over TLS (port 443) preventing:
1. **Eavesdropping (Confidentiality)**: Packets are encrypted; attackers on public Wi-Fi cannot inspect passwords or payloads.
2. **Tampering (Integrity)**: Cryptographic checksums detect any payload manipulation in transit.
3. **Impersonation (Authentication)**: Public key infrastructure (PKI) certificates verify server identity.

---

## Practical: HTTP Protocol & Methods Inspector

### Implementation
**File:** [`src/practicals/module_01_http_client.py`](file:///c:/office%20files/api-backend-assignment/src/practicals/module_01_http_client.py)  
**Tests:** [`tests/test_module_01_http.py`](file:///c:/office%20files/api-backend-assignment/tests/test_module_01_http.py)

Implemented an HTTP protocol inspector client and target server demonstrating all standard verbs (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`), custom headers (`User-Agent`, `Authorization`, `Accept`), query parameter handling, and status code verification.

### How I Ran It
```bash
python -m src.practicals.module_01_http_client
```

### Testing
```bash
pytest tests/test_module_01_http.py -v
```

### Result
```text
======================================================================
Module 01: HTTP Protocol & Methods Demonstration
======================================================================

[1] GET /items/1 -> Status: 200
    Response JSON: {'status': 'success', 'data': {'id': 1, 'name': 'Mechanical Keyboard', 'price': 89.99, 'category': 'electronics'}, 'received_headers': {'User-Agent': 'CustomAppInspector/1.0', 'Accept': 'application/json'}}

[2] POST /items -> Status: 201
    Response JSON: {'status': 'created', 'data': {'id': 2, 'name': 'Gaming Mouse', 'price': 49.99, 'category': 'electronics'}, 'auth_received': True}

[3] PUT /items/2 -> Status: 200
    Response JSON: {'status': 'replaced', 'data': {'id': 2, 'name': 'Wireless Ergonomic Mouse', 'price': 59.99, 'category': 'accessories'}}

[4] PATCH /items/2 -> Status: 200
    Response JSON: {'status': 'updated', 'data': {'id': 2, 'name': 'Wireless Ergonomic Mouse', 'price': 54.99, 'category': 'accessories'}}

[5] HEAD /items/1 -> Status: 200
    Header X-Item-Exists: true
    Body Length: 0 bytes (Empty body expected)

[6] OPTIONS /items -> Status: 200
    Allow Header: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD

[7] DELETE /items/2 -> Status: 204

[8] GET /items/2 (After Deletion) -> Status: 404
    Response JSON: {'error': 'Item not found', 'item_id': 2}
```

### Observations / Learnings
1. **HEAD vs GET**: Verified that `HEAD` returns identical headers to `GET` without transmitting any body payload, making it ideal for checking resource existence with zero bandwidth overhead.
2. **OPTIONS Preflight**: The `OPTIONS` verb returns the `Allow` header advertising permitted methods without triggering state changes.
3. **DELETE 204**: Verified that `204 No Content` produces a response with zero bytes in the body while indicating successful completion.

### Issues Encountered & Fixes
- **Issue**: Standardizing header inspection across ASGI test client and live server.
- **Fix**: Used FastAPI header dependency extraction with case-insensitive normalization.