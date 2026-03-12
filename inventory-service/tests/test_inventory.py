# test_inventory.py — Unit tests for inventory-service
# Run with: python -m pytest tests/test_inventory.py -v
# Part of OrderFlow CI/CD pipeline (Settimana 4, Giorno 3)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the inventory-service app."""
    from main import app
    return TestClient(app)


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"


# ========================================
# Product Tests
# ========================================

class TestListProducts:
    def test_list_products_returns_list(self, client):
        response = client.get("/api/products")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_products_have_required_fields(self, client):
        response = client.get("/api/products")
        products = response.json()
        if len(products) > 0:
            product = products[0]
            assert "id" in product
            assert "name" in product
            assert "price" in product
            assert "stock" in product


class TestGetProduct:
    def test_get_product_by_id(self, client):
        # First, get a product ID from the list
        products = client.get("/api/products").json()
        if len(products) > 0:
            product_id = products[0]["id"]
            response = client.get(f"/api/products/{product_id}")
            assert response.status_code == 200

    def test_get_product_not_found(self, client):
        response = client.get("/api/products/99999")
        assert response.status_code == 404


class TestCheckStock:
    def test_check_stock_available(self, client):
        products = client.get("/api/products").json()
        if len(products) > 0:
            product_id = products[0]["id"]
            response = client.get(
                f"/api/products/{product_id}/check-stock",
                params={"quantity": 1}
            )
            assert response.status_code == 200
            data = response.json()
            assert "available" in data

    def test_check_stock_not_found(self, client):
        response = client.get(
            "/api/products/99999/check-stock",
            params={"quantity": 1}
        )
        assert response.status_code == 404
