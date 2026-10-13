from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.models import RoleEnum, User
from app.schemas.schemas import (
    ChangePasswordRequest,
    StaffCreateRequest,
    UserOut,
    UserUpdateRequest,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_my_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.department_id is not None:
        current_user.department_id = payload.department_id
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}


# ---------- Admin: manage students & staff ----------
@router.get("", response_model=list[UserOut])
def list_users(
    role: RoleEnum | None = None,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.order_by(User.full_name).all()


@router.post("/staff", response_model=UserOut, status_code=201)
def create_staff(
    payload: StaffCreateRequest,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    staff = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        department_id=payload.department_id,
        hashed_password=hash_password(payload.password),
        role=RoleEnum.STAFF,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.put("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/activate", response_model=UserOut)
def activate_user(
    user_id: int,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user
