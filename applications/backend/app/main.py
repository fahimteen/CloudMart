from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import database, models

app = FastAPI(title="CloudMart")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/health")
async def health():
    try:
        products = await database.get_products()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e.__class__.__name__}"
    return {"status": "ok", "db": db_status}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    products = await database.get_products()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products},
    )


@app.get("/api/v1/products")
async def list_products(category: str | None = None):
    return await database.get_products(category=category)


@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: str):
    return await database.get_product(product_id)


@app.get("/api/v1/cart")
async def get_cart(user_id: str = "demo"):
    return await database.get_cart(user_id)


@app.post("/api/v1/cart/items")
async def add_cart_item(item: models.CartItemCreate, user_id: str = "demo"):
    return await database.add_cart_item(user_id, item)


@app.delete("/api/v1/cart/items/{item_id}")
async def remove_cart_item(item_id: str, user_id: str = "demo"):
    return await database.remove_cart_item(user_id, item_id)


@app.post("/api/v1/orders")
async def create_order(order: models.OrderCreate, user_id: str = "demo"):
    return await database.create_order(user_id, order)


@app.get("/api/v1/orders")
async def list_orders(user_id: str = "demo"):
    return await database.list_orders(user_id)
