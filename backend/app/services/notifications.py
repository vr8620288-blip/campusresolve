from sqlalchemy.orm import Session

from app.models.models import Notification


def notify(db: Session, user_id: int, title: str, message: str, complaint_id: int | None = None):
    if user_id is None:
        return
    n = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title=title,
        message=message,
    )
    db.add(n)
    db.commit()
