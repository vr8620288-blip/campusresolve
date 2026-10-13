"""
Seed the database with demo data: departments, categories, one user per role,
and a handful of realistic sample complaints across different statuses.

Run with:
    python seed.py

These are DEVELOPMENT/DEMO credentials only. Change or remove them before
any production deployment.
"""
import random
from datetime import datetime, timedelta

from app.core.security import hash_password
from app.database.database import Base, SessionLocal, engine
from app.models.models import (
    Category,
    Complaint,
    ComplaintHistory,
    Department,
    RoleEnum,
    StatusEnum,
    PriorityEnum,
    User,
)
from app.services.sla import calculate_due_date

Base.metadata.create_all(bind=engine)
db = SessionLocal()

DEPARTMENTS = [
    ("IT Services", "Computer labs, network and Wi-Fi"),
    ("Facilities & Maintenance", "Electricity, plumbing, furniture, civil work"),
    ("Administration", "General administration and campus operations"),
    ("Library", "Library services and resources"),
    ("Security", "Campus security and safety"),
]

CATEGORIES = [
    "Classroom", "Laboratory", "Computer / IT", "Wi-Fi / Network", "Electricity",
    "Water / Plumbing", "Cleanliness", "Furniture", "Projector / Smart Board",
    "Library", "Security", "Canteen", "Washroom", "Parking", "Other",
]

SAMPLE_COMPLAINTS = [
    ("Projector not working in Lab 3", "The ceiling projector shows no signal and won't power on.", "Lab 3, CS Block", "Projector / Smart Board", PriorityEnum.HIGH, StatusEnum.SUBMITTED),
    ("Wi-Fi extremely slow in Library", "Wi-Fi drops every few minutes on the 2nd floor reading area.", "Library, 2nd Floor", "Wi-Fi / Network", PriorityEnum.MEDIUM, StatusEnum.ASSIGNED),
    ("Leaking tap in washroom", "Continuous leaking wasting water near the boys' washroom, Block A.", "Block A Washroom", "Water / Plumbing", PriorityEnum.MEDIUM, StatusEnum.IN_PROGRESS),
    ("Broken chair in Classroom 204", "Two chairs have broken legs and are unsafe to use.", "Classroom 204", "Furniture", PriorityEnum.LOW, StatusEnum.IN_PROGRESS),
    ("Power socket sparking in Lab 1", "One of the power sockets sparks when a plug is inserted, safety risk.", "Lab 1, Electronics Block", "Electricity", PriorityEnum.CRITICAL, StatusEnum.RESOLVED),
    ("Canteen area not cleaned", "Tables were left uncleaned for most of the day.", "Main Canteen", "Cleanliness", PriorityEnum.LOW, StatusEnum.CLOSED),
    ("No parking space near Block C", "Parking area is full by 9am, students park on the road.", "Block C Parking", "Parking", PriorityEnum.LOW, StatusEnum.SUBMITTED),
    ("Library computer won't boot", "PC #12 in the library computer section doesn't power on.", "Library Computer Section", "Computer / IT", PriorityEnum.MEDIUM, StatusEnum.REOPENED),
]


def get_or_create_dept(name, desc):
    d = db.query(Department).filter(Department.name == name).first()
    if not d:
        d = Department(name=name, description=desc)
        db.add(d)
        db.commit()
        db.refresh(d)
    return d


def get_or_create_category(name):
    c = db.query(Category).filter(Category.name == name).first()
    if not c:
        c = Category(name=name)
        db.add(c)
        db.commit()
        db.refresh(c)
    return c


def get_or_create_user(**kwargs):
    existing = db.query(User).filter(User.email == kwargs["email"]).first()
    if existing:
        return existing
    user = User(**kwargs)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main():
    print("Seeding departments...")
    depts = {name: get_or_create_dept(name, desc) for name, desc in DEPARTMENTS}

    print("Seeding categories...")
    cats = {name: get_or_create_category(name) for name in CATEGORIES}

    print("Seeding demo users...")
    admin = get_or_create_user(
        full_name="Campus Administrator",
        email="admin@smartcampus.edu",
        phone="9000000001",
        hashed_password=hash_password("Admin@123"),
        role=RoleEnum.ADMIN,
        department_id=depts["Administration"].id,
    )
    staff = get_or_create_user(
        full_name="Ravi Kumar",
        email="staff@smartcampus.edu",
        phone="9000000002",
        hashed_password=hash_password("Staff@123"),
        role=RoleEnum.STAFF,
        department_id=depts["IT Services"].id,
    )
    staff2 = get_or_create_user(
        full_name="Priya Sharma",
        email="priya.staff@smartcampus.edu",
        phone="9000000003",
        hashed_password=hash_password("Staff@123"),
        role=RoleEnum.STAFF,
        department_id=depts["Facilities & Maintenance"].id,
    )
    student = get_or_create_user(
        full_name="Aisha Verma",
        email="student@smartcampus.edu",
        phone="9000000004",
        student_id="STU2024001",
        hashed_password=hash_password("Student@123"),
        role=RoleEnum.STUDENT,
        department_id=depts["IT Services"].id,
    )

    print("Seeding sample complaints...")
    staff_cycle = [staff, staff2]
    for i, (title, desc, location, cat_name, priority, status) in enumerate(SAMPLE_COMPLAINTS):
        existing = db.query(Complaint).filter(Complaint.title == title).first()
        if existing:
            continue
        created = datetime.utcnow() - timedelta(days=random.randint(1, 20))
        complaint = Complaint(
            reference_code=f"CR-DEMO-{1000 + i}",
            title=title,
            description=desc,
            location=location,
            category_id=cats[cat_name].id,
            priority=priority,
            status=status,
            student_id=student.id,
            created_at=created,
            updated_at=created,
            due_at=calculate_due_date(priority, created),
        )
        if status != StatusEnum.SUBMITTED:
            assigned_staff = staff_cycle[i % 2]
            complaint.assigned_staff_id = assigned_staff.id
            complaint.department_id = assigned_staff.department_id
            complaint.assigned_at = created + timedelta(hours=2)
        if status in (StatusEnum.RESOLVED, StatusEnum.CLOSED):
            complaint.resolved_at = created + timedelta(days=1)
            complaint.resolution_note = "Issue inspected and fixed by maintenance staff."
        if status == StatusEnum.CLOSED:
            complaint.closed_at = created + timedelta(days=2)
            complaint.student_confirmed = True

        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        db.add(ComplaintHistory(complaint_id=complaint.id, to_status=status.value, note="Seeded demo record"))
        db.commit()

    print("\nSeed complete.")
    print("Demo accounts (DEVELOPMENT ONLY — change before production):")
    print("  Admin:   admin@smartcampus.edu   / Admin@123")
    print("  Staff:   staff@smartcampus.edu   / Staff@123")
    print("  Student: student@smartcampus.edu / Student@123")


if __name__ == "__main__":
    main()
    db.close()
