import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class PriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StatusEnum(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    users = relationship("User", back_populates="department")
    complaints = relationship("Complaint", back_populates="department")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    complaints = relationship("Complaint", back_populates="category")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(36), unique=True, default=gen_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    student_id = Column(String(50), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.STUDENT)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="users")
    complaints_filed = relationship(
        "Complaint", back_populates="student", foreign_keys="Complaint.student_id"
    )
    complaints_assigned = relationship(
        "Complaint", back_populates="assigned_staff", foreign_keys="Complaint.assigned_staff_id"
    )


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    reference_code = Column(String(20), unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(200), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.SUBMITTED)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    resolution_note = Column(Text, nullable=True)
    student_confirmed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)  # SLA deadline

    category = relationship("Category", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    student = relationship("User", back_populates="complaints_filed", foreign_keys=[student_id])
    assigned_staff = relationship(
        "User", back_populates="complaints_assigned", foreign_keys=[assigned_staff_id]
    )
    history = relationship(
        "ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan"
    )
    comments = relationship(
        "ComplaintComment", back_populates="complaint", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "ComplaintAttachment", back_populates="complaint", cascade="all, delete-orphan"
    )


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="history")
    changed_by = relationship("User")


class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="comments")
    author = relationship("User")


class ComplaintAttachment(Base):
    __tablename__ = "complaint_attachments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    kind = Column(String(20), default="evidence")  # evidence | resolution
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="attachments")
    uploaded_by = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    complaint = relationship("Complaint")
