"""
SLA (Service Level Agreement) rules.

Configurable resolution windows per priority. In a production deployment
these could be moved into a database-backed settings table so admins can
edit them from the UI; they are kept here as a single source of truth to
keep the third-year project scope manageable.
"""
from datetime import datetime, timedelta

from app.models.models import PriorityEnum

SLA_HOURS = {
    PriorityEnum.LOW: 7 * 24,
    PriorityEnum.MEDIUM: 5 * 24,
    PriorityEnum.HIGH: 3 * 24,
    PriorityEnum.CRITICAL: 24,
}


def calculate_due_date(priority: PriorityEnum, from_time: datetime | None = None) -> datetime:
    base = from_time or datetime.utcnow()
    return base + timedelta(hours=SLA_HOURS[priority])


def is_overdue(due_at: datetime | None, status: str) -> bool:
    if due_at is None:
        return False
    if status in ("RESOLVED", "CLOSED"):
        return False
    return datetime.utcnow() > due_at
