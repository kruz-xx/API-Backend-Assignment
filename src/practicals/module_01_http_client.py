"""
Module 01: HTTP Fundamentals - Live Client & Protocol Inspector
Demonstrates HTTP request lifecycles, HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS),
custom request headers, status codes, query parameters, and response inspection.
"""

from typing import Any, Dict
from fastapi import FastAPI, Header, Response, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Simulated Target Server for Protocol Demonstration
# ---------------------------------------------------------------------------
demo_app = FastAPI(title="HTTP Protocol Inspector Target")

ITEM_STORE = {
    1: {"id": 1, "name": "Mechanical Keyboard", "price": 89.99, "category": "electronics"}
}


@demo_app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    user_agent: str = Header(default="UnknownClient"),
    accept: str = Header(default="application/json")
):
    if item_id not in ITEM_STORE:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Item not found", "item_id": item_id}
        )
    return {
        "status": "success",
        "data": ITEM_STORE[item_id],
        "received_headers": {"User-Agent": user_agent, "Accept": accept}
    }


@demo_app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(payload: Dict[str, Any], authorization: str = Header(None)):
    new_id = len(ITEM_STORE) + 1
    new_item = {"id": new_id, **payload}
    ITEM_STORE[new_id] = new_item
    return {
        "status": "created",
        "data": new_item,
        "auth_received": bool(authorization)
    }


@demo_app.put("/items/{item_id}")
async def replace_item(item_id: int, payload: Dict[str, Any]):
    if item_id not in ITEM_STORE:
        return JSONResponse(status_code=404, content={"error": "Not Found"})
    ITEM_STORE[item_id] = {"id": item_id, **payload}
    return {"status": "replaced", "data": ITEM_STORE[item_id]}


@demo_app.patch("/items/{item_id}")
async def update_item_partial(item_id: int, payload: Dict[str, Any]):
    if item_id not in ITEM_STORE:
        return JSONResponse(status_code=404, content={"error": "Not Found"})
    ITEM_STORE[item_id].update(payload)
    return {"status": "updated", "data": ITEM_STORE[item_id]}


@demo_app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    if item_id not in ITEM_STORE:
        return JSONResponse(status_code=404, content={"error": "Not Found"})
    del ITEM_STORE[item_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@demo_app.options("/items")
async def options_items(response: Response):
    response.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    return {"allowed_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]}


@demo_app.head("/items/{item_id}")
async def head_item(item_id: int, response: Response):
    if item_id not in ITEM_STORE:
        response.status_code = status.HTTP_404_NOT_FOUND
        return response
    response.status_code = status.HTTP_200_OK
    response.headers["Content-Type"] = "application/json"
    response.headers["X-Item-Exists"] = "true"
    return response


# ---------------------------------------------------------------------------
# Client Implementation
# ---------------------------------------------------------------------------
def run_http_demonstration() -> Dict[str, Any]:
    """
    Executes a comprehensive sequence of HTTP requests demonstrating:
    1. GET with custom headers (User-Agent, Accept) -> 200 OK
    2. POST with JSON body and Authorization header -> 201 Created
    3. PUT (Full update) -> 200 OK
    4. PATCH (Partial update) -> 200 OK
    5. HEAD (Headers only verification) -> 200 OK
    6. OPTIONS (Check allowed verbs) -> 200 OK
    7. DELETE -> 204 No Content
    8. GET Deleted Item -> 404 Not Found (error handling)
    """
    client = TestClient(demo_app)
    results = {}

    print("=" * 70)
    print("Module 01: HTTP Protocol & Methods Demonstration")
    print("=" * 70)

    # 1. GET Request
    res_get = client.get(
        "/items/1",
        headers={"User-Agent": "CustomAppInspector/1.0", "Accept": "application/json"}
    )
    print(f"\n[1] GET /items/1 -> Status: {res_get.status_code}")
    print(f"    Response JSON: {res_get.json()}")
    results["get_status"] = res_get.status_code

    # 2. POST Request
    res_post = client.post(
        "/items",
        json={"name": "Gaming Mouse", "price": 49.99, "category": "electronics"},
        headers={"Authorization": "Bearer sample_token_123"}
    )
    print(f"\n[2] POST /items -> Status: {res_post.status_code}")
    print(f"    Response JSON: {res_post.json()}")
    results["post_status"] = res_post.status_code

    # 3. PUT Request (Replace full item)
    res_put = client.put(
        "/items/2",
        json={"name": "Wireless Ergonomic Mouse", "price": 59.99, "category": "accessories"}
    )
    print(f"\n[3] PUT /items/2 -> Status: {res_put.status_code}")
    print(f"    Response JSON: {res_put.json()}")
    results["put_status"] = res_put.status_code

    # 4. PATCH Request (Partial update: price only)
    res_patch = client.patch(
        "/items/2",
        json={"price": 54.99}
    )
    print(f"\n[4] PATCH /items/2 -> Status: {res_patch.status_code}")
    print(f"    Response JSON: {res_patch.json()}")
    results["patch_status"] = res_patch.status_code

    # 5. HEAD Request
    res_head = client.head("/items/1")
    print(f"\n[5] HEAD /items/1 -> Status: {res_head.status_code}")
    print(f"    Header X-Item-Exists: {res_head.headers.get('x-item-exists')}")
    print(f"    Body Length: {len(res_head.content)} bytes (Empty body expected)")
    results["head_status"] = res_head.status_code

    # 6. OPTIONS Request
    res_options = client.options("/items")
    print(f"\n[6] OPTIONS /items -> Status: {res_options.status_code}")
    print(f"    Allow Header: {res_options.headers.get('allow')}")
    results["options_status"] = res_options.status_code

    # 7. DELETE Request
    res_delete = client.delete("/items/2")
    print(f"\n[7] DELETE /items/2 -> Status: {res_delete.status_code}")
    results["delete_status"] = res_delete.status_code

    # 8. GET Deleted Item (Verify 404)
    res_verify = client.get("/items/2")
    print(f"\n[8] GET /items/2 (After Deletion) -> Status: {res_verify.status_code}")
    print(f"    Response JSON: {res_verify.json()}")
    results["deleted_get_status"] = res_verify.status_code

    print("\n" + "=" * 70)
    print("All HTTP Protocol checks completed successfully!")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_http_demonstration()
