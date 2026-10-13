# Installation Guide

This guide walks through running CampusResolve locally, step by step, with
exact commands. Windows commands are shown first in each block; macOS/Linux
equivalents follow where they differ.

## 1. Prerequisites

Install these first:

- **Python 3.12+** — https://www.python.org/downloads/ (check "Add Python to PATH" during install on Windows)
- **PostgreSQL 15+** — https://www.postgresql.org/download/ (optional — the project runs on SQLite with zero setup; install this only if you want PostgreSQL)
- **Git** (optional, if you're cloning instead of unzipping) — https://git-scm.com/downloads

Verify installs:

```bash
python --version
pip --version
psql --version      # only if you installed PostgreSQL
```

## 2. Unzip / clone the project

Unzip `CampusResolve-Final.zip` (or clone the repo) and open a terminal in
the project's root folder — the one containing `backend/`, `frontend/`,
`docs/`, etc.

## 3. Backend setup

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS / Linux:
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
copy .env.example .env      REM Windows
cp .env.example .env        # macOS/Linux
```

The default `.env` uses SQLite (`sqlite:///./campus_resolve.db`), so you can
run the whole project **without installing PostgreSQL**. Skip to section 5
if that's all you need for now.

## 4. (Optional) Switch to PostgreSQL

Create the database and user (run in `psql` or pgAdmin):

```sql
CREATE USER campus_user WITH PASSWORD 'campus_pass';
CREATE DATABASE campus_resolve OWNER campus_user;
```

Edit `backend/.env` and set:

```
DATABASE_URL=postgresql+psycopg2://campus_user:campus_pass@localhost:5432/campus_resolve
```

Run migrations:

```bash
alembic upgrade head
```

(If you skip this, the backend will still auto-create tables on first
start — Alembic is there for tracked, reviewable schema changes going
forward.)

## 5. Seed demo data

```bash
python seed.py
```

This creates demo departments, categories, one Admin/Staff/Student account
each, and several realistic sample complaints across different statuses.
**These are development credentials only — see the table in README.md.**

## 6. Start the backend

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Interactive API docs
(Swagger UI) are at `http://localhost:8000/docs`.

## 7. Start the frontend

Open a **new terminal** (leave the backend running) in the project root:

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500/login.html` in your browser.

If your backend runs somewhere other than `localhost:8000`, edit
`frontend/js/config.js` and change `CAMPUS_RESOLVE_API_BASE`.

## 8. Log in

Use one of the demo accounts from the README, or register a new student
account from the login page.

## 9. Run automated tests

```bash
cd backend
pytest -v
```

## Troubleshooting

- **"uvicorn: command not found"** — make sure the virtual environment is
  activated (step 3) before running backend commands.
- **CORS errors in the browser console** — check that `CORS_ORIGINS` in
  `backend/.env` includes the exact origin the frontend is served from
  (e.g. `http://localhost:5500`), then restart the backend.
- **Port already in use** — stop whatever else is using port 8000 or 5500,
  or run `uvicorn app.main:app --reload --port 8001` (and update
  `frontend/js/config.js` to match).
- **PostgreSQL connection refused** — confirm PostgreSQL is running and the
  credentials/host/port in `DATABASE_URL` are correct.
- **File upload fails with 422** — only JPG, PNG and PDF files up to 5MB
  are accepted; anything else is rejected by design.
- **Login works but dashboard is blank / errors** — open the browser
  console; most issues are either CORS (see above) or the backend not
  running.
