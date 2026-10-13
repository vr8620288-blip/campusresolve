# CampusResolve — Smart Campus Complaint & Issue Tracking System

CampusResolve is a full-stack web platform that lets students report campus
problems (broken equipment, Wi-Fi outages, plumbing issues, etc.) and lets
staff and administrators track, assign, resolve, and close those complaints
through a complete workflow with statuses, SLAs, notifications and a
reopen-if-unresolved loop.

## Features

- **Role-based access** for Students, Staff and Admins (JWT authentication)
- **Full complaint lifecycle**: Submitted → Assigned → In Progress → Resolved → Closed, with Reopen support
- **Search, filter and sort** across complaints (status, priority, category, department, date range, staff, keyword)
- **File attachments** (JPG/PNG/PDF, 5MB limit) for evidence and resolution proof
- **In-app notifications** with unread counts and mark-as-read
- **Role-specific dashboards** with live Chart.js visualizations computed from real database data (no mock numbers)
- **SLA / overdue tracking** with priority-based deadlines
- **Admin console** for managing staff accounts, categories and departments
- **Comment threads** on every complaint for student/staff/admin collaboration
- **Automated backend tests** (pytest) covering auth, authorization and the core workflow

## Technology Stack

| Layer     | Technology |
|-----------|------------|
| Frontend  | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| Backend   | Python 3.12+, FastAPI, Uvicorn, Pydantic |
| ORM       | SQLAlchemy 2.x + Alembic migrations |
| Database  | PostgreSQL 15+ (SQLite supported out of the box for quick local testing) |
| Auth      | JWT (python-jose) + bcrypt password hashing (passlib) |
| Deploy    | Docker + docker-compose |

## Project Structure

```
campusresolve/
├── backend/            FastAPI application, models, routers, tests, Alembic migrations
├── frontend/            Static HTML/CSS/JS client (no build step required)
├── database/             Reference schema.sql / seed.sql
├── docs/                    Installation, API and client handover documentation
├── docker-compose.yml
└── Dockerfile
```

See `docs/INSTALLATION.md` for exact step-by-step setup, `docs/CLIENT_SETUP.md`
for a non-developer walkthrough, and `docs/API_DOCUMENTATION.md` for the full
API reference. FastAPI also serves interactive, always-up-to-date docs at
`/docs` once the backend is running.

## Quick Start (local, no Docker)

```bash
# 1. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # defaults to SQLite — no PostgreSQL required to try it out
python seed.py                   # creates demo users, departments, categories, sample complaints
uvicorn app.main:app --reload    # http://localhost:8000  (docs at /docs)

# 2. Frontend (separate terminal)
cd frontend
python -m http.server 5500       # http://localhost:5500
```

Open `http://localhost:5500/login.html` and sign in with one of the demo
accounts below.

## Quick Start (Docker, PostgreSQL)

```bash
docker compose up --build
# backend:  http://localhost:8000/docs
# frontend: http://localhost:5500
```

Then, in a separate terminal, seed the Dockerized database once:

```bash
docker compose exec backend python seed.py
```

## Demo Accounts

| Role    | Email                       | Password    |
|---------|------------------------------|-------------|
| Admin   | admin@smartcampus.edu      | Admin@123   |
| Staff   | staff@smartcampus.edu      | Staff@123   |
| Student | student@smartcampus.edu    | Student@123 |

**These are DEVELOPMENT/DEMO credentials. Change or remove them before any
production deployment.**

## Running Tests

```bash
cd backend
pytest -v
```

Tests run against an isolated in-memory SQLite database and never touch
your real/demo data.

## Switching to PostgreSQL (without Docker)

1. Install PostgreSQL 15+ and create a database and user (see `docs/INSTALLATION.md`).
2. In `backend/.env`, set:
   ```
   DATABASE_URL=postgresql+psycopg2://campus_user:campus_pass@localhost:5432/campus_resolve
   ```
3. Run `alembic upgrade head` (or just start the app — it will create tables automatically on first run).
4. Run `python seed.py`.

## Troubleshooting

See the **Troubleshooting** sections in `docs/INSTALLATION.md` and
`docs/CLIENT_SETUP.md` for common issues (CORS errors, port conflicts,
PostgreSQL connection errors, file upload failures).

## Known Limitations

- This build ships with SQLite as the zero-setup default; PostgreSQL is
  fully supported (see above) but requires installing PostgreSQL yourself.
- SLA rules are defined in `backend/app/services/sla.py` as code constants
  rather than an admin-editable database table, to keep the scope
  manageable for a third-year project. They are easy to move into a
  settings table later.
- File storage is local disk (`UPLOAD_DIRECTORY`), not cloud object storage.
- The frontend is intentionally framework-free (vanilla JS) per the project
  brief, so state management is simple page-by-page logic rather than a SPA
  router.

## License

See `LICENSE`.
