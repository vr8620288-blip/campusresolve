from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import RoleEnum, User
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    if db.query(User).filter(User.student_id == payload.student_id).first():
        raise HTTPException(status_code=409, detail="Student ID already registered")

    user = User(
        full_name=payload.full_name,
        student_id=payload.student_id,
        email=payload.email,
        phone=payload.phone,
        department_id=payload.department_id,
        hashed_password=hash_password(payload.password),
        role=RoleEnum.STUDENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated")

    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


# Also expose an OAuth2-compatible form login so /docs "Authorize" works out of the box.
@router.post("/token", response_model=TokenResponse, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
