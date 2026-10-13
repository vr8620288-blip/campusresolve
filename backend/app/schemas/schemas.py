from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.models import PriorityEnum, RoleEnum, StatusEnum


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    full_name: str
    student_id: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[int] = None
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    full_name: str


# ---------- Users ----------
class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    student_id: Optional[str] = None
    role: RoleEnum
    department_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class StaffCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[int] = None
    password: str = Field(min_length=6)


# ---------- Departments / Categories ----------
class DepartmentOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class DepartmentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class CategoryCreateRequest(BaseModel):
    name: str


# ---------- Complaints ----------
class ComplaintCreateRequest(BaseModel):
    title: str
    description: str
    location: str
    category_id: int
    priority: PriorityEnum = PriorityEnum.MEDIUM


class ComplaintAssignRequest(BaseModel):
    staff_id: int


class ComplaintStatusUpdateRequest(BaseModel):
    status: StatusEnum
    note: Optional[str] = None
    resolution_note: Optional[str] = None


class CommentCreateRequest(BaseModel):
    message: str


class CommentOut(BaseModel):
    id: int
    author_id: int
    author_name: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class AttachmentOut(BaseModel):
    id: int
    file_name: str
    content_type: str
    size_bytes: int
    kind: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryOut(BaseModel):
    id: int
    from_status: Optional[str]
    to_status: str
    note: Optional[str]
    created_at: datetime
    changed_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class ComplaintOut(BaseModel):
    id: int
    reference_code: str
    title: str
    description: str
    location: str
    category_id: int
    category_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    priority: PriorityEnum
    status: StatusEnum
    student_id: int
    student_name: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    assigned_staff_name: Optional[str] = None
    resolution_note: Optional[str] = None
    student_confirmed: bool
    created_at: datetime
    updated_at: datetime
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True


class ComplaintDetailOut(ComplaintOut):
    comments: List[CommentOut] = []
    attachments: List[AttachmentOut] = []
    history: List[HistoryOut] = []


class ComplaintListResponse(BaseModel):
    total: int
    items: List[ComplaintOut]


# ---------- Notifications ----------
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    complaint_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    unread_count: int
    items: List[NotificationOut]


# ---------- Dashboard ----------
class StatusBreakdown(BaseModel):
    status: str
    count: int


class CategoryBreakdown(BaseModel):
    category: str
    count: int


class PriorityBreakdown(BaseModel):
    priority: str
    count: int


class DepartmentBreakdown(BaseModel):
    department: str
    count: int


class MonthlyTrendPoint(BaseModel):
    month: str
    count: int


class StaffWorkloadPoint(BaseModel):
    staff_name: str
    open_count: int
    resolved_count: int


class StudentDashboardOut(BaseModel):
    total: int
    submitted: int
    in_progress: int
    resolved: int
    closed: int
    reopened: int
    recent: List[ComplaintOut]


class StaffDashboardOut(BaseModel):
    assigned: int
    pending: int
    in_progress: int
    resolved: int
    critical: int
    overdue: int
    recent: List[ComplaintOut]


class AdminDashboardOut(BaseModel):
    total: int
    pending: int
    assigned: int
    in_progress: int
    resolved: int
    closed: int
    reopened: int
    critical: int
    overdue: int
    by_category: List[CategoryBreakdown]
    by_status: List[StatusBreakdown]
    by_priority: List[PriorityBreakdown]
    by_department: List[DepartmentBreakdown]
    monthly_trend: List[MonthlyTrendPoint]
    staff_workload: List[StaffWorkloadPoint]
