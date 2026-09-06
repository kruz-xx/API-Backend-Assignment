"""
Module 11: GraphQL, Properly Practical
Implements:
1. GraphQL Schema using Strawberry GraphQL
2. Strongly-typed Object Types (User, Product, OrderItem, Order)
3. Query resolvers (products, product by ID, orders by user ID)
4. Mutation resolvers (createProduct, createOrder)
5. Over-fetching and under-fetching mitigation via dynamic GraphQL field selection
"""

from typing import List, Optional
from fastapi import FastAPI
from fastapi.testclient import TestClient
import strawberry
from strawberry.fastapi import GraphQLRouter

# ---------------------------------------------------------------------------
# In-Memory Datastores
# ---------------------------------------------------------------------------
GRAPHQL_PRODUCTS = [
    {"id": 1, "name": "Mechanical Keyboard RGB", "price": 89.99, "stock": 25, "category": "Electronics"},
    {"id": 2, "name": "Wireless Ergonomic Mouse", "price": 49.99, "stock": 50, "category": "Electronics"},
    {"id": 3, "name": "Noise Cancelling Headphones", "price": 199.99, "stock": 15, "category": "Audio"}
]

GRAPHQL_ORDERS = [
    {
        "id": 1,
        "user_id": 101,
        "total_amount": 139.98,
        "status": "COMPLETED",
        "items": [
            {"product_id": 1, "quantity": 1, "unit_price": 89.99},
            {"product_id": 2, "quantity": 1, "unit_price": 49.99}
        ]
    }
]


# ---------------------------------------------------------------------------
# GraphQL Types
# ---------------------------------------------------------------------------
@strawberry.type
class ProductType:
    id: int
    name: str
    price: float
    stock: int
    category: str


@strawberry.type
class OrderItemType:
    product_id: int
    quantity: int
    unit_price: float

    @strawberry.field
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)

    @strawberry.field
    def product(self) -> Optional[ProductType]:
        p = next((item for item in GRAPHQL_PRODUCTS if item["id"] == self.product_id), None)
        if p:
            return ProductType(**p)
        return None


@strawberry.type
class OrderType:
    id: int
    user_id: int
    total_amount: float
    status: str
    items: List[OrderItemType]


# ---------------------------------------------------------------------------
# Query Root Resolver
# ---------------------------------------------------------------------------
@strawberry.type
class Query:
    @strawberry.field
    def products(self, category: Optional[str] = None) -> List[ProductType]:
        if category:
            return [ProductType(**p) for p in GRAPHQL_PRODUCTS if p["category"].lower() == category.lower()]
        return [ProductType(**p) for p in GRAPHQL_PRODUCTS]

    @strawberry.field
    def product(self, id: int) -> Optional[ProductType]:
        p = next((item for item in GRAPHQL_PRODUCTS if item["id"] == id), None)
        return ProductType(**p) if p else None

    @strawberry.field
    def orders(self, user_id: Optional[int] = None) -> List[OrderType]:
        records = GRAPHQL_ORDERS
        if user_id:
            records = [o for o in records if o["user_id"] == user_id]

        res = []
        for o in records:
            items_list = [OrderItemType(**item) for item in o["items"]]
            res.append(OrderType(
                id=o["id"],
                user_id=o["user_id"],
                total_amount=o["total_amount"],
                status=o["status"],
                items=items_list
            ))
        return res


# ---------------------------------------------------------------------------
# Mutation Root Resolver
# ---------------------------------------------------------------------------
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_product(self, name: str, price: float, stock: int, category: str) -> ProductType:
        new_id = len(GRAPHQL_PRODUCTS) + 1
        new_product = {
            "id": new_id,
            "name": name,
            "price": price,
            "stock": stock,
            "category": category
        }
        GRAPHQL_PRODUCTS.append(new_product)
        return ProductType(**new_product)

    @strawberry.mutation
    def create_order(self, user_id: int, product_id: int, quantity: int) -> OrderType:
        p = next((item for item in GRAPHQL_PRODUCTS if item["id"] == product_id), None)
        if not p:
            raise ValueError(f"Product with ID {product_id} not found.")

        unit_price = p["price"]
        total = round(unit_price * quantity, 2)
        new_id = len(GRAPHQL_ORDERS) + 1

        order_data = {
            "id": new_id,
            "user_id": user_id,
            "total_amount": total,
            "status": "PENDING",
            "items": [{"product_id": product_id, "quantity": quantity, "unit_price": unit_price}]
        }
        GRAPHQL_ORDERS.append(order_data)

        items_list = [OrderItemType(**item) for item in order_data["items"]]
        return OrderType(
            id=order_data["id"],
            user_id=order_data["user_id"],
            total_amount=order_data["total_amount"],
            status=order_data["status"],
            items=items_list
        )


# ---------------------------------------------------------------------------
# Schema and FastAPI Mounting
# ---------------------------------------------------------------------------
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI(title="GraphQL API Demo")
app.include_router(graphql_app, prefix="/graphql")


# ---------------------------------------------------------------------------
# Runner for CLI Testing
# ---------------------------------------------------------------------------
def run_module_11_demo():
    client = TestClient(app)

    print("=" * 70)
    print("Module 11: GraphQL, Properly Practical Run")
    print("=" * 70)

    # 1. Query with exact field selection (Eliminating over-fetching)
    query_exact_fields = """
    query GetProductsShort {
        products {
            id
            name
            price
        }
    }
    """
    res1 = client.post("/graphql", json={"query": query_exact_fields})
    print(f"\n[1] GraphQL Query (Exact Fields: id, name, price) -> Status: {res1.status_code}")
    print(f"    Response Data: {res1.json()['data']['products']}")

    # 2. Nested Query with Sub-Resources (Eliminating under-fetching)
    query_nested = """
    query GetOrdersWithProductDetails {
        orders {
            id
            totalAmount
            status
            items {
                quantity
                subtotal
                product {
                    name
                    category
                }
            }
        }
    }
    """
    res2 = client.post("/graphql", json={"query": query_nested})
    print(f"\n[2] GraphQL Nested Query (Orders + Items + Products) -> Status: {res2.status_code}")
    print(f"    Nested Response Data: {res2.json()['data']['orders']}")

    # 3. Mutation to create a new product
    mutation_create = """
    mutation AddProduct {
        createProduct(name: "4K Gaming Monitor", price: 349.99, stock: 10, category: "Electronics") {
            id
            name
            price
        }
    }
    """
    res3 = client.post("/graphql", json={"query": mutation_create})
    print(f"\n[3] GraphQL Mutation (createProduct) -> Status: {res3.status_code}")
    print(f"    Created Product Data: {res3.json()['data']['createProduct']}")

    print("\n" + "=" * 70)
    print("Module 11 GraphQL queries and mutations executed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_module_11_demo()
