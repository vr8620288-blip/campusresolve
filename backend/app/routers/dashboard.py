from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_roles
from app.models.models import Category, Complaint, Department, PriorityEnum, RoleEnum, StatusEnum, User
from app.schemas.schemas import (
    AdminDashboardOut,
    CategoryBreakdown,
    ComplaintOut,
    DepartmentBreakdown,
    MonthlyTrendPoint,
    PriorityBreakdown,
    StaffDashboardOut,
    StaffWorkloadPoint,
    StatusBreakdown,
    StudentDashboardOut,
)
from app.services.sla import is_overdue

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _to_out(c: Complaint) -> ComplaintOut:
    return ComplaintOut(
        id=c.id,
        reference_code=c.reference_code,
        title=c.title,
        description=c.description,
        location=c.location,
        category_id=c.category_id,
        category_name=c.category.name if c.category else None,
        department_id=c.department_id,
        department_name=c.department.name if c.department else None,
        priority=c.priority,
        status=c.status,
        student_id=c.student_id,
        student_name=c.student.full_name if c.student else None,
        assigned_staff_id=c.assigned_staff_id,
        assigned_staff_name=c.assigned_staff.full_name if c.assigned_staff else None,
        resolution_note=c.resolution_note,
        student_confirmed=c.student_confirmed,
        created_at=c.created_at,
        updated_at=c.updated_at,
        assigned_at=c.assigned_at,
        resolved_at=c.resolved_at,
        closed_at=c.closed_at,
        due_at=c.due_at,
        is_overdue=is_overdue(c.due_at, c.status.value),
    )


@router.get("/student", response_model=StudentDashboardOut)
def student_dashboard(
    current_user: User = Depends(require_roles(RoleEnum.STUDENT)), db: Session = Depends(get_db)
):
    q = db.query(Complaint).filter(Complaint.student_id == current_user.id)
    all_complaints = q.all()
    counts = Counter(c.status for c in all_complaints)

    recent = (
        db.query(Complaint)
        .filter(Complaint.student_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )

    return StudentDashboardOut(
        total=len(all_complaints),
        submitted=counts.get(StatusEnum.SUBMITTED, 0) + counts.get(StatusEnum.ASSIGNED, 0),
        in_progress=counts.get(StatusEnum.IN_PROGRESS, 0),
        resolved=counts.get(StatusEnum.RESOLVED, 0),
        closed=counts.get(StatusEnum.CLOSED, 0),
        reopened=counts.get(StatusEnum.REOPENED, 0),
        recent=[_to_out(c) for c in recent],
    )


@router.get("/staff", response_model=StaffDashboardOut)
def staff_dashboard(
    current_user: User = Depends(require_roles(RoleEnum.STAFF)), db: Session = Depends(get_db)
):
    all_complaints = db.query(Complaint).filter(Complaint.assigned_staff_id == current_user.id).all()
    counts = Counter(c.status for c in all_complaints)
    overdue = sum(1 for c in all_complaints if is_overdue(c.due_at, c.status.value))
    critical = sum(1 for c in all_complaints if c.priority == PriorityEnum.CRITICAL and c.status not in (StatusEnum.RESOLVED, StatusEnum.CLOSED))

    recent = (
        db.query(Complaint)
        .filter(Complaint.assigned_staff_id == current_user.id)
        .order_by(Complaint.updated_at.desc())
        .limit(5)
        .all()
    )

    return StaffDashboardOut(
        assigned=len(all_complaints),
        pending=counts.get(StatusEnum.ASSIGNED, 0),
        in_progress=counts.get(StatusEnum.IN_PROGRESS, 0),
        resolved=counts.get(StatusEnum.RESOLVED, 0) + counts.get(StatusEnum.CLOSED, 0),
        critical=critical,
        overdue=overdue,
        recent=[_to_out(c) for c in recent],
    )


@router.get("/admin", response_model=AdminDashboardOut)
def admin_dashboard(
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)), db: Session = Depends(get_db)
):
    all_complaints = db.query(Complaint).all()
    counts = Counter(c.status for c in all_complaints)
    overdue = sum(1 for c in all_complaints if is_overdue(c.due_at, c.status.value))
    critical = sum(
        1
        for c in all_complaints
        if c.priority == PriorityEnum.CRITICAL and c.status not in (StatusEnum.RESOLVED, StatusEnum.CLOSED)
    )

    by_category = Counter(c.category.name if c.category else "Uncategorized" for c in all_complaints)
    by_status = Counter(c.status.value for c in all_complaints)
    by_priority = Counter(c.priority.value for c in all_complaints)
    by_department = Counter(c.department.name if c.department else "Unassigned" for c in all_complaints)

    monthly = Counter(c.created_at.strftime("%Y-%m") for c in all_complaints)
    monthly_sorted = sorted(monthly.items())

    staff_members = db.query(User).filter(User.role == RoleEnum.STAFF).all()
    workload = []
    for s in staff_members:
        assigned = [c for c in all_complaints if c.assigned_staff_id == s.id]
        open_count = sum(1 for c in assigned if c.status not in (StatusEnum.RESOLVED, StatusEnum.CLOSED))
        resolved_count = sum(1 for c in assigned if c.status in (StatusEnum.RESOLVED, StatusEnum.CLOSED))
        if assigned:
            workload.append(StaffWorkloadPoint(staff_name=s.full_name, open_count=open_count, resolved_count=resolved_count))

    return AdminDashboardOut(
        total=len(all_complaints),
        pending=counts.get(StatusEnum.SUBMITTED, 0),
        assigned=counts.get(StatusEnum.ASSIGNED, 0),
        in_progress=counts.get(StatusEnum.IN_PROGRESS, 0),
        resolved=counts.get(StatusEnum.RESOLVED, 0),
        closed=counts.get(StatusEnum.CLOSED, 0),
        reopened=counts.get(StatusEnum.REOPENED, 0),
        critical=critical,
        overdue=overdue,
        by_category=[CategoryBreakdown(category=k, count=v) for k, v in by_category.items()],
        by_status=[StatusBreakdown(status=k, count=v) for k, v in by_status.items()],
        by_priority=[PriorityBreakdown(priority=k, count=v) for k, v in by_priority.items()],
        by_department=[DepartmentBreakdown(department=k, count=v) for k, v in by_department.items()],
        monthly_trend=[MonthlyTrendPoint(month=k, count=v) for k, v in monthly_sorted],
        staff_workload=workload,
    )
