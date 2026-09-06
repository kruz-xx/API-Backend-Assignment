from typing import List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter
from src.routers.orders import orders_db
from src.routers.products import products_db


@strawberry.type
class GraphQLProduct:
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    category: str


@strawberry.type
class GraphQLOrderItem:
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float

    @strawberry.field
    def product(self) -> Optional[GraphQLProduct]:
        p = products_db.get(self.product_id)
        if p:
            return GraphQLProduct(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                price=p["price"],
                stock=p["stock"],
                category=p["category"]
            )
        return None


@strawberry.type
class GraphQLOrder:
    id: int
    user_id: int
    total_amount: float
    status: str
    items: List[GraphQLOrderItem]


@strawberry.type
class Query:
    @strawberry.field
    def products(self, category: Optional[str] = None) -> List[GraphQLProduct]:
        items = list(products_db.values())
        if category:
            items = [p for p in items if p["category"].lower() == category.lower()]
        return [
            GraphQLProduct(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                price=p["price"],
                stock=p["stock"],
                category=p["category"]
            )
            for p in items
        ]

    @strawberry.field
    def product(self, id: int) -> Optional[GraphQLProduct]:
        p = products_db.get(id)
        if not p:
            return None
        return GraphQLProduct(
            id=p["id"],
            name=p["name"],
            description=p.get("description"),
            price=p["price"],
            stock=p["stock"],
            category=p["category"]
        )

    @strawberry.field
    def orders(self, user_id: Optional[int] = None) -> List[GraphQLOrder]:
        orders = list(orders_db.values())
        if user_id:
            orders = [o for o in orders if o["user_id"] == user_id]

        res = []
        for o in orders:
            items = [
                GraphQLOrderItem(
                    product_id=i["product_id"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                    subtotal=i["subtotal"]
                )
                for i in o.get("items", [])
            ]
            res.append(
                GraphQLOrder(
                    id=o["id"],
                    user_id=o["user_id"],
                    total_amount=o["total_amount"],
                    status=o["status"],
                    items=items
                )
            )
        return res


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_product(
        self,
        name: str,
        price: float,
        stock: int,
        category: str,
        description: Optional[str] = None
    ) -> GraphQLProduct:
        new_id = max(products_db.keys(), default=0) + 1
        product_record = {
            "id": new_id,
            "name": name,
            "description": description or f"Description for {name}",
            "price": price,
            "stock": stock,
            "category": category
        }
        products_db[new_id] = product_record
        return GraphQLProduct(**product_record)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, tags=["GraphQL"])
