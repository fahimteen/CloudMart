import os
from typing import List, Optional

from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from .models import CartItemCreate, OrderCreate

# Load env vars from .env when running locally
load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "cloudmart")
COSMOS_PRODUCTS_CONTAINER = os.getenv("COSMOS_PRODUCTS_CONTAINER", "products")
COSMOS_CART_CONTAINER = os.getenv("COSMOS_CART_CONTAINER", "cart")
COSMOS_ORDERS_CONTAINER = os.getenv("COSMOS_ORDERS_CONTAINER", "orders")

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    # This will make health endpoint show an error if not configured
    client = None
    database = None
    products_container = None
    cart_container = None
    orders_container = None
else:
    client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = client.get_database_client(COSMOS_DATABASE)
    products_container = database.get_container_client(COSMOS_PRODUCTS_CONTAINER)
    cart_container = database.get_container_client(COSMOS_CART_CONTAINER)
    orders_container = database.get_container_client(COSMOS_ORDERS_CONTAINER)


async def get_products(category: Optional[str] = None) -> List[dict]:
    if products_container is None:
        return []

    if category:
        query = "SELECT * FROM c WHERE c.category = @category"
        params = [{"name": "@category", "value": category}]
    else:
        query = "SELECT * FROM c"
        params = []

    items = list(
        products_container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=True,
        )
    )
    return items


async def get_product(product_id: str) -> Optional[dict]:
    if products_container is None:
        return None

    query = "SELECT * FROM c WHERE c.id = @id"
    items = list(
        products_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": product_id}],
            enable_cross_partition_query=True,
        )
    )
    return items[0] if items else None


async def get_cart(user_id: str) -> List[dict]:
    if cart_container is None:
        return []

    items = list(
        cart_container.query_items(
            query="SELECT * FROM c WHERE c.user_id = @uid",
            parameters=[{"name": "@uid", "value": user_id}],
            enable_cross_partition_query=True,
        )
    )
    return items


async def add_cart_item(user_id: str, item: CartItemCreate) -> dict:
    if cart_container is None:
        return {}

    # ID unique per user + product
    doc = {
        "id": f"{user_id}-{item.product_id}",
        "user_id": user_id,
        "product_id": item.product_id,
        "quantity": item.quantity,
    }
    cart_container.upsert_item(doc)
    return doc


async def remove_cart_item(user_id: str, item_id: str) -> dict:
    if cart_container is None:
        return {"status": "db-not-configured"}

    # Partition key is user_id
    cart_container.delete_item(item=item_id, partition_key=user_id)
    return {"status": "removed"}


async def create_order(user_id: str, order: OrderCreate) -> dict:
    if orders_container is None:
        return {"status": "db-not-configured"}

    items = [i.dict() for i in order.items]

    doc = {
        "id": f"order-{user_id}",
        "user_id": user_id,
        "items": items,
        "status": "confirmed",
    }
    orders_container.upsert_item(doc)

    # Optionally clear cart
    if cart_container is not None:
        cart_items = await get_cart(user_id)
        for ci in cart_items:
            cart_container.delete_item(item=ci["id"], partition_key=user_id)

    return doc


async def list_orders(user_id: str) -> List[dict]:
    if orders_container is None:
        return []

    items = list(
        orders_container.query_items(
            query="SELECT * FROM c WHERE c.user_id = @uid",
            parameters=[{"name": "@uid", "value": user_id}],
            enable_cross_partition_query=True,
        )
    )
    return items
