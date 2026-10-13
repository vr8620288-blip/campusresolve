import random
import string
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.models import (
    Category,
    Complaint,
    ComplaintAttachment,
    ComplaintComment,
    ComplaintHistory,
    Department,
    Notification,
    PriorityEnum,
    RoleEnum,
    StatusEnum,
    User,
)
from app.schemas.schemas import (
    AttachmentOut,
    CommentCreateRequest,
    CommentOut,
    ComplaintAssignRequest,
    ComplaintCreateRequest,
    ComplaintDetailOut,
    ComplaintListResponse,
    ComplaintOut,
    ComplaintStatusUpdateRequest,
    HistoryOut,
)
from app.services.notifications import notify
from app.services.sla import calculate_due_date, is_overdue
from app.utils.files import save_upload

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _reference_code() -> str:
    suffix = "".join(random.choices(string.digits, k=5))
    return f"CR-{datetime.utcnow().strftime('%y%m')}-{suffix}"


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


def _record_history(db: Session, complaint: Complaint, from_status, to_status, user: User, note=None):
    db.add(
        ComplaintHistory(
            complaint_id=complaint.id,
            changed_by_id=user.id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            note=note,
        )
    )


def _get_owned_or_403(db: Session, complaint_id: int, current_user: User) -> Complaint:
    complaint = db.query(Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.role == RoleEnum.STUDENT and complaint.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own complaints")
    if current_user.role == RoleEnum.STAFF and complaint.assigned_staff_id != current_user.id:
        raise HTTPException(status_code=403, detail="This complaint is not assigned to you")
    return complaint


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(
    payload: ComplaintCreateRequest,
    current_user: User = Depends(require_roles(RoleEnum.STUDENT)),
    db: Session = Depends(get_db),
):
    category = db.query(Category).get(payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    complaint = Complaint(
        reference_code=_reference_code(),
        title=payload.title,
        description=payload.description,
        location=payload.location,
        category_id=payload.category_id,
        priority=payload.priority,
        status=StatusEnum.SUBMITTED,
        student_id=current_user.id,
        due_at=calculate_due_date(payload.priority),
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    _record_history(db, complaint, None, StatusEnum.SUBMITTED, current_user, "Complaint submitted")
    db.commit()

    # Notify all admins of a new (especially critical) complaint
    admins = db.query(User).filter(User.role == RoleEnum.ADMIN, User.is_active == True).all()  # noqa: E712
    for admin in admins:
        notify(
            db,
            admin.id,
            "New complaint submitted",
            f"{complaint.reference_code}: {complaint.title}",
            complaint.id,
        )

    return _to_out(complaint)


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    search: str | None = None,
    status_filter: StatusEnum | None = Query(None, alias="status"),
    priority: PriorityEnum | None = None,
    category_id: int | None = None,
    department_id: int | None = None,
    assigned_staff_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = Query("newest", description="newest|oldest|priority|updated"),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Complaint)

    # Role-based scoping
    if current_user.role == RoleEnum.STUDENT:
        q = q.filter(Complaint.student_id == current_user.id)
    elif current_user.role == RoleEnum.STAFF:
        q = q.filter(Complaint.assigned_staff_id == current_user.id)
    # ADMIN sees everything

    if search:
        like = f"%{search}%"
        q = q.join(User, Complaint.student_id == User.id).filter(
            or_(
                Complaint.reference_code.ilike(like) if hasattr(Complaint.reference_code, "ilike") else Complaint.reference_code.like(like),
                Complaint.title.ilike(like),
                Complaint.location.ilike(like),
                User.full_name.ilike(like),
            )
        )

    if status_filter:
        q = q.filter(Complaint.status == status_filter)
    if priority:
        q = q.filter(Complaint.priority == priority)
    if category_id:
        q = q.filter(Complaint.category_id == category_id)
    if department_id:
        q = q.filter(Complaint.department_id == department_id)
    if assigned_staff_id:
        q = q.filter(Complaint.assigned_staff_id == assigned_staff_id)
    if date_from:
        q = q.filter(Complaint.created_at >= date_from)
    if date_to:
        q = q.filter(Complaint.created_at <= date_to)

    priority_rank = {
        PriorityEnum.CRITICAL: 0,
        PriorityEnum.HIGH: 1,
        PriorityEnum.MEDIUM: 2,
        PriorityEnum.LOW: 3,
    }

    total = q.count()

    if sort == "oldest":
        q = q.order_by(Complaint.created_at.asc())
    elif sort == "updated":
        q = q.order_by(Complaint.updated_at.desc())
    elif sort == "priority":
        # fetch then sort in python for cross-db enum ordering safety
        items = q.all()
        items.sort(key=lambda c: priority_rank.get(c.priority, 9))
        start = (page - 1) * page_size
        items = items[start : start + page_size]
        return ComplaintListResponse(total=total, items=[_to_out(c) for c in items])
    else:  # newest (default)
        q = q.order_by(Complaint.created_at.desc())

    start = (page - 1) * page_size
    items = q.offset(start).limit(page_size).all()
    return ComplaintListResponse(total=total, items=[_to_out(c) for c in items])


@router.get("/{complaint_id}", response_model=ComplaintDetailOut)
def get_complaint(
    complaint_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    out = _to_out(complaint).model_dump()
    out["comments"] = [
        CommentOut(
            id=c.id,
            author_id=c.author_id,
            author_name=c.author.full_name if c.author else None,
            message=c.message,
            created_at=c.created_at,
        )
        for c in sorted(complaint.comments, key=lambda x: x.created_at)
    ]
    out["attachments"] = [AttachmentOut.model_validate(a) for a in complaint.attachments]
    out["history"] = [
        HistoryOut(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            note=h.note,
            created_at=h.created_at,
            changed_by_name=h.changed_by.full_name if h.changed_by else None,
        )
        for h in sorted(complaint.history, key=lambda x: x.created_at)
    ]
    return ComplaintDetailOut(**out)


@router.put("/{complaint_id}/assign", response_model=ComplaintOut)
def assign_complaint(
    complaint_id: int,
    payload: ComplaintAssignRequest,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    staff = db.query(User).get(payload.staff_id)
    if not staff or staff.role != RoleEnum.STAFF:
        raise HTTPException(status_code=404, detail="Staff member not found")

    was_reassignment = complaint.assigned_staff_id is not None
    complaint.assigned_staff_id = staff.id
    complaint.department_id = staff.department_id
    if complaint.status == StatusEnum.SUBMITTED:
        old_status = complaint.status
        complaint.status = StatusEnum.ASSIGNED
        _record_history(db, complaint, old_status, StatusEnum.ASSIGNED, admin, "Assigned to staff")
    complaint.assigned_at = datetime.utcnow()
    db.commit()
    db.refresh(complaint)

    title = "Complaint reassigned" if was_reassignment else "Complaint assigned"
    notify(db, staff.id, title, f"{complaint.reference_code}: {complaint.title}", complaint.id)
    notify(
        db,
        complaint.student_id,
        "Your complaint has been assigned",
        f"{complaint.reference_code} was assigned to {staff.full_name}",
        complaint.id,
    )
    return _to_out(complaint)


@router.put("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: int,
    payload: ComplaintStatusUpdateRequest,
    current_user: User = Depends(require_roles(RoleEnum.STAFF, RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    old_status = complaint.status
    complaint.status = payload.status

    if payload.status == StatusEnum.RESOLVED:
        complaint.resolved_at = datetime.utcnow()
        if payload.resolution_note:
            complaint.resolution_note = payload.resolution_note
    if payload.status == StatusEnum.CLOSED:
        complaint.closed_at = datetime.utcnow()

    _record_history(db, complaint, old_status, payload.status, current_user, payload.note)
    db.commit()
    db.refresh(complaint)

    notify(
        db,
        complaint.student_id,
        f"Complaint status: {payload.status.value.replace('_', ' ').title()}",
        f"{complaint.reference_code}: {complaint.title}",
        complaint.id,
    )
    return _to_out(complaint)


@router.put("/{complaint_id}/confirm", response_model=ComplaintOut)
def confirm_resolution(
    complaint_id: int,
    current_user: User = Depends(require_roles(RoleEnum.STUDENT)),
    db: Session = Depends(get_db),
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    if complaint.status != StatusEnum.RESOLVED:
        raise HTTPException(status_code=400, detail="Only resolved complaints can be confirmed")

    old_status = complaint.status
    complaint.status = StatusEnum.CLOSED
    complaint.student_confirmed = True
    complaint.closed_at = datetime.utcnow()
    _record_history(db, complaint, old_status, StatusEnum.CLOSED, current_user, "Student confirmed resolution")
    db.commit()
    db.refresh(complaint)

    if complaint.assigned_staff_id:
        notify(
            db,
            complaint.assigned_staff_id,
            "Resolution confirmed",
            f"Student confirmed {complaint.reference_code} is resolved",
            complaint.id,
        )
    return _to_out(complaint)


@router.put("/{complaint_id}/reopen", response_model=ComplaintOut)
def reopen_complaint(
    complaint_id: int,
    payload: ComplaintStatusUpdateRequest | None = None,
    current_user: User = Depends(require_roles(RoleEnum.STUDENT)),
    db: Session = Depends(get_db),
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    if complaint.status not in (StatusEnum.RESOLVED, StatusEnum.CLOSED):
        raise HTTPException(status_code=400, detail="Only resolved/closed complaints can be reopened")

    old_status = complaint.status
    complaint.status = StatusEnum.REOPENED
    complaint.student_confirmed = False
    note = payload.note if payload else "Student reopened complaint"
    _record_history(db, complaint, old_status, StatusEnum.REOPENED, current_user, note)
    db.commit()
    db.refresh(complaint)

    if complaint.assigned_staff_id:
        notify(
            db,
            complaint.assigned_staff_id,
            "Complaint reopened",
            f"{complaint.reference_code}: {complaint.title} was reopened by the student",
            complaint.id,
        )
    return _to_out(complaint)


@router.post("/{complaint_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    complaint_id: int,
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    comment = ComplaintComment(complaint_id=complaint.id, author_id=current_user.id, message=payload.message)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # notify the other party
    recipients = set()
    if current_user.id != complaint.student_id:
        recipients.add(complaint.student_id)
    if complaint.assigned_staff_id and current_user.id != complaint.assigned_staff_id:
        recipients.add(complaint.assigned_staff_id)
    for uid in recipients:
        notify(db, uid, "New comment", f"New comment on {complaint.reference_code}", complaint.id)

    return CommentOut(
        id=comment.id,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        message=comment.message,
        created_at=comment.created_at,
    )


@router.post("/{complaint_id}/attachments", response_model=AttachmentOut, status_code=201)
def upload_attachment(
    complaint_id: int,
    kind: str = "evidence",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = _get_owned_or_403(db, complaint_id, current_user)
    stored_path, size = save_upload(file)

    attachment = ComplaintAttachment(
        complaint_id=complaint.id,
        uploaded_by_id=current_user.id,
        file_name=file.filename,
        stored_path=stored_path,
        content_type=file.content_type,
        size_bytes=size,
        kind=kind,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment
