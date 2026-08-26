# Module 01 — HTTP Fundamentals

## Overview
Deep dive into the HTTP protocol, the URL request lifecycle (DNS, TCP, TLS handshake), HTTP methods, headers, status codes, and inspecting live HTTP traffic.

---

## Conceptual Questions & Answers

### 1. Journey of a URL in browser
> Explain what happens, step by step, when you type a URL into a browser and hit enter — DNS lookup, TCP connection, TLS handshake (if HTTPS), HTTP request sent, server processing, HTTP response received, rendering.

**Answer:**

When we enter a URL into the browser and hit enter, a certain chain reaction happens. This reaction creates a request from the browser to the web server hosting that particular website. Each step can be described as followed:

A. DNS Lookup: The browser requires an IP Address to connect with the server, so the URL is translated into the IP Address attached to it via a DNS server. This translation is similar to looking up a number of a person via their name in a phonebook. 

B. TCP connection: After the IP Address is obtained, the browser reaches out to it and then establishes a reliable connection with it (sort of like a handshake).The handshake is named TCP "three-way handshake". This connection ensures that the data sent and received is not lost or corrupted. 

Reach out >> confirmation of receiving the message >> browser acknowledges the message.

C. HTTP Request: The browser sends a text based request over this connection, this request asks for the webpage to be displayed. Usually in .html format. (E.G.: GET /index.html)

D. HTTP Response After the server has processed the request and it sends back the response containing a status code like (200 OK) and the actual HTML file on the page. The response is also broken down into smaller packages so as to ensure smooth transmission of data.

E. Rendering: Lastly, the browser reads the HTML, realises the need for stylesheets, javascript files and images and hereby sends requests to the server for each of them. And as it receives each file, it renders the webpage on the screen.

---

### 2. Anatomy of an HTTP request
> Explain an HTTP request in detail including: Request Line (Method, Path, Protocol version), Headers, and the Body (payload), with examples for each. Also the anatomy of a response: status lines, headers, body.

**Answer:**

The Anatomy of an HTTP request:

Method and Path:
GET / HTTP/2 
- What action you want and where you want it.

Headers:
- Host: example.com 
- User-Agent: curl/8.x.x 
The metadata describing the request.

Body:
- Optional, usually for POST/PUT requests to send data. (E.G.: JSON Payload)

The Anatomy of an HTTP response:

Status Line:
- HTTP/2 200 OK 
- Protocol version + Status code + Human-readable message

Headers:
- Content-Type: text/html
- Content-Length: 1234
- Set-Cookie: sessionID=xyz
Metadata about the response

Body:
- (E.G.: HTML/JSON payload)
- The actual content requested, printed at the end.

---

### 3. HTTP Methods 
> Detail the differences between `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`. 

**Answer:**

GET:
- Used to retrieve data from a server.
- Reads data. E.g.: fetches a user's profile page.

POST:
- Creates new data.
- Sends new data to server and expects a response.

PUT:
- Updates data by replacing the old data entirely.
- Example: updating a user profile entirely.

PATCH:
- Partially updates data. 
- Changing only one item like example: just updating your password.

DELETE:
- Removes data completely.
- Example: removing a user profile.

HEAD:
- Similar to GET, but only asks for headers and no body.
- Example: Checking if a file exists on server.

OPTIONS:
- Retrieves information about the communication.
- Checking allowed methods on a resource.

TRACE:
- Request is echoed back to client.
- For diagnostics and debugging, trace message loop.
- E.G.: Checking for "middle-man" proxies in path to server.

---

### 4. Idempotency and Safe Methods
> Define HTTP idempotency. Which methods are safe? Which are idempotent? Explain how PUT, DELETE, and PATCH differ in this regard.

**Answer:**

HTTP idempotency:
A request method is said to be idempotent if the result of the request is the same regardless of how many times it is repeated. 

Idempotent methods:
- GET
- PUT
- DELETE
- HEAD
- OPTIONS
- TRACE

Safe methods:
- POST

Why it matters:
Idempotency and safety are important for reliable HTTP communication, especially for APIs that process payments and manage sensitive data. 

Example: You're on a train and your connection drops right after hitting the submit button, your phone doesn't know if the server got it. If the request was a GET, the app can safely retry automatically. If it was POST, the app shouldn't retry automatically without asking for your permission else it risks duplicating the action. E.g.: charging you twice for the same order.

---

### 5. PUT Vs. PATCH
> Explain the difference between PUT and PATCH precisely. 

**Answer:**

PUT:
- Replaces an existing resource with the new data entirely.
- Example: updating a user profile entirely, replacing the old data with new data.

PATCH:
- Partially updates an existing resource with the new data.
- Example: just updating your password, changing only one item.

PUT vs PATCH:
- PUT is idempotent, PATCH is not.

---

### 6. HTTP Status Codes
> Explain the 5 status code categories (1xx, 2xx, 3xx, 4xx, 5xx) with specific examples for `200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`, and `503`.

**Answer:**

1xx (Informational):
 "Hold on, I'm processing." (Rarely seen in daily dev).

2xx (Success): 
 "It worked."

- 200 OK:
 Standard success.

- 201 Created:
 Success, and a new resource was made (standard for POST).

- 204 No Content:
 Success, but I have no data to send back (common for DELETE).

3xx (Redirection):
 "Go look over there."

- 301 Moved Permanently:
 The URL changed forever, update your bookmarks.

- 302 Found:
 Temporarily moved somewhere else.

- 304 Not Modified:
 Your cached version is still good, I'm not resending the data.

4xx (Client Error): 
 "You messed up."

- 400 Bad Request: Your JSON is malformed or invalid.

- 401 Unauthorized: You didn't log in.

- 404 Not Found: That URL doesn't exist.

5xx (Server Error):
 "I (the server) messed up."

- 500 Internal Server Error: The backend code crashed.

- 502 Bad Gateway: The proxy (like Nginx) couldn't reach the actual app server.

- 503 Service Unavailable: The server is overloaded or down for maintenance.

---

### 7. 401 Unauthorized Vs. 403 Forbidden
> Explain the precise difference between `401 Unauthorized` and `403 Forbidden` in the context of authentication and authorization.

**Answer:**

401 Unauthorized:
- You didn't log in (missing or invalid credentials).
- Example: Trying to access /admin without a valid token.

403 Forbidden:
- You are logged in, but you don't have permission.
- Example: A regular user trying to access /admin.

---

### 8. HTTP Headers
> Explain common request and response headers (`Content-Type`, `Authorization`, `Accept`, `User-Agent`, `Cache-Control`, `Set-Cookie`).

**Answer:**

Content type:
Tells the receiver the format the body is in. E.g.: JSON.

Authorization:
Holds your credentials. E.g.: JWT tokens.

Accept:
Tells the sender(server) the format you(the client) want the response in. E.g.: JSON, HTML.

User-agent:
Identifies the client making the request. 
Like chrome, postman or curl.

Cache Control:
Dictates how long the browser is allowed to cache the response.

ETag:
A unique hash of the response content, used to check if the data has changed since the last request.

curl -X POST "https://httpbin.org/post" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -H "Accept: application/json" \
  -H "User-Agent: CustomClient/1.0" \
  -H "Cache-Control: no-cache" \
  -d '{"test": "data"}'

---

### 9. HTTPS Vs. HTTP
> Explain the differences between HTTP and HTTPS. What TLS/SSL actually protects against.

**Answer:**

HTTP:
- Transmits data in plain text (unencrypted)
- Vulnerable to eavesdropping (packet sniffers)
- No authentication
- No data integrity
- Uses port 80

HTTPS:
- Transmits data in encrypted format (TLS/SSL)
- Protected from eavesdropping
- Provides authentication
- Ensures data integrity
- Uses port 443

What TLS/SSL actually protects against:

1. Eavesdropping (Confidentiality):
   - Protects data from being intercepted and read by unauthorized parties (e.g., hackers on public Wi-Fi)

2. Data Tampering (Integrity):
   - Ensures data hasn't been modified during transit
   - Detects unauthorized modifications with checksums and digital signatures

3. Impersonation (Authentication):
   - Verifies the identity of the server you're connecting to
   - Prevents man-in-the-middle attacks where an attacker pretends to be the server
---

## Screenshots & Execution Proof

HTTP/2 200 
date: Mon, 31 Aug 2026 01:05:00 GMT
content-type: application/json
content-length: 456
server: gunicorn/19.9.0
access-control-allow-origin: *
access-control-allow-credentials: true

{
  "args": {}, 
  "data": "{\"test\": \"data\"}", 
  "files": {}, 
  "form": {}, 
  "headers": {
    "Accept": "application/json", 
    "Authorization": "Bearer token123", 
    "Cache-Control": "no-cache", 
    "Content-Length": "17", 
    "Content-Type": "application/json", 
    "Host": "httpbin.org", 
    "User-Agent": "CustomClient/1.0"
  }, 
  "json": {
    "test": "data"
  }, 
  "url": "https://httpbin.org/post"
}