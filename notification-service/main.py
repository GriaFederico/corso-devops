# OrderFlow - Notification Service
# Receives order events and maintains a notification log.
# Run: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("notification-service")

app = FastAPI(title="OrderFlow - Notification Service", version="1.0.0")

# In-memory notification log
notifications_db: list = []
notification_counter = 0


class NotificationCreate(BaseModel):
    order_id: int
    customer_name: str
    event_type: str
    timestamp: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "notification-service", "version": "1.0.0"}


@app.post("/api/notifications", status_code=201)
def create_notification(notification: NotificationCreate):
    """Receive an order event and log the notification."""
    global notification_counter
    notification_counter += 1

    messages = {
        "order.created": f"Ordine #{notification.order_id} creato per {notification.customer_name}",
        "order.confirmed": f"Ordine #{notification.order_id} confermato",
        "order.shipped": f"Ordine #{notification.order_id} spedito",
        "order.delivered": f"Ordine #{notification.order_id} consegnato",
        "order.cancelled": f"Ordine #{notification.order_id} annullato",
    }

    new_notification = {
        "id": notification_counter,
        "order_id": notification.order_id,
        "customer_name": notification.customer_name,
        "event_type": notification.event_type,
        "message": messages.get(notification.event_type, f"Event: {notification.event_type}"),
        "channel": "log",
        "status": "sent",
        "created_at": datetime.utcnow().isoformat()
    }
    notifications_db.append(new_notification)

    logger.info(f"Notification created: order={notification.order_id}, event={notification.event_type}")
    return new_notification


@app.get("/api/notifications")
def list_notifications(order_id: Optional[int] = None):
    """List notifications, optionally filtered by order_id."""
    if order_id:
        filtered = [n for n in notifications_db if n["order_id"] == order_id]
        return {"notifications": filtered, "total": len(filtered)}
    return {"notifications": notifications_db, "total": len(notifications_db)}


@app.get("/api/notifications/{notification_id}")
def get_notification(notification_id: int):
    """Get a specific notification by ID."""
    for n in notifications_db:
        if n["id"] == notification_id:
            return n
    raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
