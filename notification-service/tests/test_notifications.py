# test_notifications.py — Unit tests for notification-service
# Run with: python -m pytest tests/test_notifications.py -v
# Part of OrderFlow CI/CD pipeline (Settimana 4, Giorno 3)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the notification-service app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_notification():
    """Sample notification payload for testing."""
    return {
        "order_id": 1,
        "customer_name": "Mario Rossi",
        "event_type": "order.created"
    }


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
        assert data["service"] == "notification-service"


# ========================================
# Create Notification Tests
# ========================================

class TestCreateNotification:
    def test_create_notification_returns_201(self, client, sample_notification):
        response = client.post("/api/notifications", json=sample_notification)
        assert response.status_code == 201

    def test_create_notification_returns_data(self, client, sample_notification):
        response = client.post("/api/notifications", json=sample_notification)
        data = response.json()
        assert data["order_id"] == sample_notification["order_id"]
        assert data["customer_name"] == sample_notification["customer_name"]
        assert data["event_type"] == sample_notification["event_type"]
        assert data["status"] == "sent"
        assert "id" in data
        assert "message" in data

    def test_create_notification_generates_message(self, client):
        payload = {
            "order_id": 42,
            "customer_name": "Luigi Verdi",
            "event_type": "order.shipped"
        }
        response = client.post("/api/notifications", json=payload)
        data = response.json()
        assert "42" in data["message"]
        assert data["event_type"] == "order.shipped"


# ========================================
# List Notifications Tests
# ========================================

class TestListNotifications:
    def test_list_notifications_returns_200(self, client):
        response = client.get("/api/notifications")
        assert response.status_code == 200

    def test_list_notifications_structure(self, client):
        response = client.get("/api/notifications")
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert isinstance(data["notifications"], list)

    def test_filter_by_order_id(self, client, sample_notification):
        # Create a notification first
        client.post("/api/notifications", json=sample_notification)
        # Filter by order_id
        response = client.get(
            "/api/notifications",
            params={"order_id": sample_notification["order_id"]}
        )
        data = response.json()
        assert data["total"] >= 1
        for n in data["notifications"]:
            assert n["order_id"] == sample_notification["order_id"]


# ========================================
# Get Notification Tests
# ========================================

class TestGetNotification:
    def test_get_notification_by_id(self, client, sample_notification):
        # Create a notification and get its ID
        created = client.post("/api/notifications", json=sample_notification).json()
        notification_id = created["id"]
        # Retrieve it
        response = client.get(f"/api/notifications/{notification_id}")
        assert response.status_code == 200
        assert response.json()["id"] == notification_id

    def test_get_notification_not_found(self, client):
        response = client.get("/api/notifications/99999")
        assert response.status_code == 404
