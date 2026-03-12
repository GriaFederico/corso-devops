# OrderFlow - Inventory Service
# Provides product catalog and stock availability checks.
# Run: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, HTTPException
from typing import Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("inventory-service")

app = FastAPI(title="OrderFlow - Inventory Service", version="1.0.0")

# In-memory product catalog (PostgreSQL in production)
products_db = {
    1: {"id": 1, "name": "Laptop Pro 15", "price": 1299.99, "stock": 50, "category": "electronics"},
    2: {"id": 2, "name": "Wireless Mouse", "price": 29.99, "stock": 200, "category": "accessories"},
    3: {"id": 3, "name": "USB-C Hub", "price": 49.99, "stock": 150, "category": "accessories"},
    4: {"id": 4, "name": "Monitor 27 4K", "price": 449.99, "stock": 30, "category": "electronics"},
    5: {"id": 5, "name": "Mechanical Keyboard", "price": 89.99, "stock": 100, "category": "accessories"},
}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "inventory-service", "version": "1.0.0"}


@app.get("/api/products")
def list_products():
    """List all products in the catalog."""
    return list(products_db.values())


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    """Get a specific product by ID."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return products_db[product_id]


@app.get("/api/products/{product_id}/check-stock")
def check_stock(product_id: int, quantity: int = 1):
    """Check if the requested quantity is available in stock."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    product = products_db[product_id]
    available = product["stock"] >= quantity

    return {
        "product_id": product_id,
        "product_name": product["name"],
        "requested": quantity,
        "current_stock": product["stock"],
        "available": available
    }
