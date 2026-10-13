# Testing

## Automated Tests

Location: `backend/tests/test_api.py`, run with `pytest -v` from `backend/`.

Tests run against an isolated in-memory SQLite database (never your real
`campus_resolve.db` or a PostgreSQL instance) via a FastAPI dependency
override, so they are safe to run repeatedly.

Covered:

- Health check endpoint
- Student registration (success + duplicate email rejected)
- Login (success + invalid password rejected)
- `/api/auth/me` requires authentication
- Student can create a complaint and see it in their own list
- A student cannot access another student's complaint (403)
- Notifications endpoint requires authentication

These cover the authentication, authorization, and core-complaint-creation
paths explicitly called out in the project brief. Teams extending this
project should add tests for: staff assignment, status transitions,
resolution + confirmation, reopening, comments, and notification delivery,
following the same pattern (register two role-appropriate users, obtain
tokens, call the relevant endpoints, assert on status codes and payload).

## Manual End-to-End Test Checklist

Use this checklist after any setup or deployment:

1. Register a new student account.
2. Log in as the new student; log out; log back in with the demo student.
3. Submit a complaint with each priority level; confirm the SLA due date
   looks sensible (Critical ≈ 24h out, Low ≈ 7 days out).
4. Log in as Admin; confirm the new complaint appears in "All Complaints".
5. Assign the complaint to the demo staff member; confirm the student
   receives a notification.
6. Log in as Staff; change the complaint's status to In Progress, then to
   Resolved with a resolution note.
7. Log in as the student; confirm the resolution → complaint moves to
   Closed.
8. Submit another complaint, resolve it, then **reopen** it as the student;
   confirm it returns to the staff queue and a notification is sent.
9. Add a comment as the student; confirm staff/admin can see it.
10. Upload a JPG and a PDF as evidence; confirm both appear in the
    complaint's attachment list. Try uploading a `.exe` or an oversized
    file and confirm it is rejected.
11. Search and filter the complaints list by status, priority, and
    keyword; confirm results narrow correctly.
12. As Admin, create a new staff account, deactivate it, then reactivate
    it.
13. As Admin, add a new category and a new department; confirm they
    appear in the student's "Submit Complaint" form and the staff
    assignment dropdown respectively.
14. Confirm each dashboard (Student/Staff/Admin) shows numbers that match
    what you'd expect from the complaints you just created — no fixed or
    placeholder figures.

## Note on This Build

This codebase was authored and syntax-validated (Python `py_compile` on
every backend module and migration; `node --check` on every frontend
script) in an offline sandbox without package-manager or internet access,
so the automated test suite and the manual checklist above could not be
executed end-to-end before packaging. Run `pytest -v` and the manual
checklist yourself after installing dependencies (`docs/INSTALLATION.md`)
and report anything that doesn't match this document.
