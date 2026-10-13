"""
Automated backend tests for CampusResolve.

Uses an isolated in-memory SQLite database (not the dev campus_resolve.db)
so tests never touch real/demo data. Run with:

    pytest -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.database.database import Base, get_db
from app.main import app
from app.models.models import Category, RoleEnum

# Shared in-memory SQLite engine across the whole test session
engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def seed_category():
    db = TestingSessionLocal()
    if not db.query(Category).filter(Category.name == "Projector / Smart Board").first():
        db.add(Category(name="Projector / Smart Board"))
        db.commit()
    db.close()


def register_student(email="student1@campus.edu"):
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Student",
            "student_id": f"STU-{email}",
            "email": email,
            "phone": "9999999999",
            "password": "Student@123",
            "confirm_password": "Student@123",
        },
    )
    return resp


def login(email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_student():
    resp = register_student("newstudent@campus.edu")
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "STUDENT"
    assert "access_token" in data


def test_register_duplicate_email_fails():
    register_student("dupe@campus.edu")
    resp = register_student("dupe@campus.edu")
    assert resp.status_code == 409


def test_login_success():
    register_student("loginuser@campus.edu")
    resp = login("loginuser@campus.edu", "Student@123")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid_password():
    register_student("badpass@campus.edu")
    resp = login("badpass@campus.edu", "WrongPassword1")
    assert resp.status_code == 401


def test_get_current_user_requires_auth():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_student_can_create_and_view_own_complaint():
    register_student("complaint1@campus.edu")
    token = login("complaint1@campus.edu", "Student@123").json()["access_token"]
    headers = auth_headers(token)

    cat_resp = client.get("/api/categories", headers=headers)
    category_id = cat_resp.json()[0]["id"]

    create_resp = client.post(
        "/api/complaints",
        headers=headers,
        json={
            "title": "Projector not working in Lab 3",
            "description": "No signal from the ceiling projector.",
            "location": "Lab 3",
            "category_id": category_id,
            "priority": "HIGH",
        },
    )
    assert create_resp.status_code == 201
    complaint = create_resp.json()
    assert complaint["status"] == "SUBMITTED"
    assert complaint["reference_code"].startswith("CR-")

    list_resp = client.get("/api/complaints", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


def test_student_cannot_access_others_complaint():
    register_student("owner@campus.edu")
    token_owner = login("owner@campus.edu", "Student@123").json()["access_token"]
    headers_owner = auth_headers(token_owner)
    category_id = client.get("/api/categories", headers=headers_owner).json()[0]["id"]

    complaint = client.post(
        "/api/complaints",
        headers=headers_owner,
        json={
            "title": "Wi-Fi issue",
            "description": "Slow Wi-Fi",
            "location": "Library",
            "category_id": category_id,
            "priority": "LOW",
        },
    ).json()

    register_student("stranger@campus.edu")
    token_stranger = login("stranger@campus.edu", "Student@123").json()["access_token"]
    headers_stranger = auth_headers(token_stranger)

    resp = client.get(f"/api/complaints/{complaint['id']}", headers=headers_stranger)
    assert resp.status_code == 403


def test_notifications_endpoint_requires_auth():
    resp = client.get("/api/notifications")
    assert resp.status_code == 401
