# test_orders.py — Unit tests for order-service
# Run with: python -m pytest tests/test_orders.py -v
# Part of OrderFlow CI/CD pipeline (Settimana 4, Giorno 3)

import pytest
from fastapi.testclient import TestClient


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def client():
    """Create a test client for the order-service app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_order():
    """Sample order payload for testing."""
    return {
        "customer_name": "Mario Rossi",
        "items": [
            {"product_id": "PROD-001", "quantity": 2},
            {"product_id": "PROD-003", "quantity": 1}
        ]
    }


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_includes_service_name(self, client):
        response = client.get("/health")
        data = response.json()
        assert "service" in data
        assert data["service"] == "order-service"


# ========================================
# Order CRUD Tests
# ========================================

class TestCreateOrder:
    """Tests for POST /api/orders."""

    def test_create_order_success(self, client, sample_order):
        response = client.post("/api/orders", json=sample_order)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "Mario Rossi"
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_order_returns_id(self, client, sample_order):
        response = client.post("/api/orders", json=sample_order)
        data = response.json()
        assert data["id"] is not None
        assert len(str(data["id"])) > 0

    def test_create_order_invalid_data(self, client):
        response = client.post("/api/orders", json={})
        assert response.status_code == 422

    def test_create_order_missing_items(self, client):
        response = client.post("/api/orders", json={"customer_name": "Test"})
        assert response.status_code == 422

    def test_create_order_empty_items(self, client):
        response = client.post("/api/orders", json={
            "customer_name": "Test",
            "items": []
        })
        # Depending on validation, this could be 422 or 400
        assert response.status_code in [400, 422]


class TestListOrders:
    """Tests for GET /api/orders."""

    def test_list_orders_returns_list(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_orders_after_create(self, client, sample_order):
        # Create an order first
        client.post("/api/orders", json=sample_order)
        # Then list
        response = client.get("/api/orders")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) >= 1


class TestGetOrder:
    """Tests for GET /api/orders/{id}."""

    def test_get_order_by_id(self, client, sample_order):
        # Create an order
        create_response = client.post("/api/orders", json=sample_order)
        order_id = create_response.json()["id"]

        # Retrieve it
        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customer_name"] == "Mario Rossi"

    def test_get_order_not_found(self, client):
        response = client.get("/api/orders/nonexistent-id-999")
        assert response.status_code == 404
