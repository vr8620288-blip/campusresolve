from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.models import Category, Department, RoleEnum, User
from app.schemas.schemas import (
    CategoryCreateRequest,
    CategoryOut,
    DepartmentCreateRequest,
    DepartmentOut,
)

router = APIRouter(prefix="/api", tags=["catalog"])


# ---------- Departments ----------
@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).order_by(Department.name).all()


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreateRequest,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    if db.query(Department).filter(Department.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Department already exists")
    dept = Department(name=payload.name, description=payload.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/departments/{dept_id}/deactivate", response_model=DepartmentOut)
def deactivate_department(
    dept_id: int, admin: User = Depends(require_roles(RoleEnum.ADMIN)), db: Session = Depends(get_db)
):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    dept.is_active = False
    db.commit()
    db.refresh(dept)
    return dept


# ---------- Categories ----------
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreateRequest,
    admin: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    if db.query(Category).filter(Category.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Category already exists")
    cat = Category(name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{cat_id}/deactivate", response_model=CategoryOut)
def deactivate_category(
    cat_id: int, admin: User = Depends(require_roles(RoleEnum.ADMIN)), db: Session = Depends(get_db)
):
    cat = db.query(Category).get(cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/staff", tags=["catalog"])
def list_staff(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    staff = db.query(User).filter(User.role == RoleEnum.STAFF, User.is_active == True).all()  # noqa: E712
    return [
        {"id": s.id, "full_name": s.full_name, "department_id": s.department_id}
        for s in staff
    ]
