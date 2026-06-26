from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from database.repositories import get_db
from database.repositories.queries import get_recent_notifications, create_notification
from backend.config import settings
from notifications.telegram import send_telegram_message, format_deal_message

router = APIRouter(tags=["notifications"])


class NotificationBody(BaseModel):
    car_id: Optional[str] = None
    notification_type: str = "alert"
    title: Optional[str] = None
    message: Optional[str] = None
    score: Optional[int] = None
    channel: str = "telegram"


@router.get("/notifications")
async def list_notifications(
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    notifications = await get_recent_notifications(db, limit=limit)
    return [
        {
            "id": str(n.id),
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "score": n.score,
            "channel": n.channel,
            "sent": n.sent,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


@router.post("/notifications/test")
async def test_notification(channel: str = "telegram", db: AsyncSession = Depends(get_db)):
    msg = "🚗 *Test Notification*\n\nCar Hunter AI is working correctly!"
    sent = False
    if channel == "telegram":
        sent = await send_telegram_message(msg)
    if sent:
        await create_notification(db, {
            "notification_type": "test",
            "title": "Test Notification",
            "message": msg,
            "channel": channel,
            "sent": True,
        })
        await db.commit()
        return {"status": "sent"}
    raise HTTPException(500, f"Failed to send {channel} notification")
