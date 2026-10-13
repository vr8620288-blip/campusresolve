# Client Setup Guide (Non-Developer)

This guide is written for someone running CampusResolve for the first time
without a software development background. Follow the steps in order.

## 1. Required Software

- **Python 3.12 or newer** — download from python.org and run the
  installer. On Windows, tick **"Add Python to PATH"** during install.
- *(Optional, for a production-grade database)* **PostgreSQL 15+** — if
  skipped, the system will use a built-in file-based database (SQLite)
  which works fine for evaluation and small deployments.

## 2. Getting the Project Files

Unzip the file you received (`CampusResolve-Final.zip`) to a folder of your
choice, e.g. `C:\CampusResolve` or `~/CampusResolve`.

## 3. (Optional) PostgreSQL Installation & Database Creation

If you want PostgreSQL instead of the default SQLite:

1. Install PostgreSQL and remember the password you set for the `postgres` user.
2. Open the "SQL Shell (psql)" app (Windows) or a terminal with `psql` (Mac/Linux).
3. Run:
   ```sql
   CREATE USER campus_user WITH PASSWORD 'campus_pass';
   CREATE DATABASE campus_resolve OWNER campus_user;
   ```

## 4. Python Installation Check

Open a terminal (Command Prompt on Windows, Terminal on Mac) and run:

```bash
python --version
```

You should see `Python 3.12.x` or newer. If not, revisit step 1.

## 5. Environment Setup

In the terminal, navigate into the project's `backend` folder:

```bash
cd CampusResolve/backend
```

Copy the example settings file:

```bash
copy .env.example .env      REM Windows
cp .env.example .env        # Mac/Linux
```

If you set up PostgreSQL in step 3, open `.env` in Notepad/TextEdit and
replace the `DATABASE_URL` line with:

```
DATABASE_URL=postgresql+psycopg2://campus_user:campus_pass@localhost:5432/campus_resolve
```

Otherwise, leave `.env` as-is (it will use the built-in SQLite database).

## 6. Dependency Installation

Still inside `backend`:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```
Mac/Linux:
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## 7. Database Migration & Demo Data

```bash
alembic upgrade head
python seed.py
```

(If you're using SQLite, the first command is optional — the app creates
tables automatically — but it doesn't hurt to run it.)

## 8. Starting the Backend

```bash
uvicorn app.main:app --reload
```

Leave this window open. You should see a message that Uvicorn is running
on `http://127.0.0.1:8000`.

## 9. Opening the Application

Open a **second** terminal window, navigate to the project's `frontend`
folder, and run:

```bash
cd CampusResolve/frontend
python -m http.server 5500
```

Then open your web browser to:

```
http://localhost:5500/login.html
```

## 10. Demo Login

| Role    | Email                       | Password    |
|---------|------------------------------|-------------|
| Admin   | admin@smartcampus.edu      | Admin@123   |
| Staff   | staff@smartcampus.edu      | Staff@123   |
| Student | student@smartcampus.edu    | Student@123 |

**Change these passwords (or delete the accounts and create your own)
before giving real students and staff access to the system.**

## 11. Backup Instructions (PostgreSQL)

To back up:

```bash
pg_dump -U campus_user -d campus_resolve -F c -f campus_resolve_backup.dump
```

To restore into a fresh database:

```bash
pg_restore -U campus_user -d campus_resolve -c campus_resolve_backup.dump
```

If using SQLite instead, simply copy the `campus_resolve.db` file from the
`backend` folder somewhere safe — that *is* your backup.

## 12. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Browser shows a network/connection error | Backend terminal isn't running | Re-run step 8 |
| Login page loads but login fails | Wrong email/password, or demo data not seeded | Re-run `python seed.py` (step 7) |
| "Port already in use" | Something else is using 8000 or 5500 | Close that program, or use a different port and update `frontend/js/config.js` |
| Blank dashboard / errors in browser | CORS misconfiguration | Confirm `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5500`, restart backend |
| File upload rejected | Wrong file type or over 5MB | Only JPG, PNG, PDF up to 5MB are accepted |

For anything not covered here, see `docs/INSTALLATION.md` or contact your
development team with the exact error message shown.
