# Viva Questions & Answers

Prepared for a B.Sc. Computer Science third-year project viva covering
CampusResolve's stack and design choices.

## Python & General

**1. Why Python for the backend?**
Readable syntax, a mature async-capable web ecosystem (FastAPI/Uvicorn),
strong ORM support (SQLAlchemy), and wide library availability for things
like password hashing and JWT handling.

**2. What is a virtual environment and why use one?**
An isolated Python installation per project (`python -m venv .venv`) so
each project's dependencies and versions don't conflict with other
projects or the system Python.

**3. What's the difference between a list and a tuple in Python?**
Lists are mutable and use `[]`; tuples are immutable and use `()`. The
project mostly uses lists (query results) and dict-like Pydantic models.

**4. What are Python decorators, and where are they used here?**
Functions that wrap other functions to add behavior. FastAPI's
`@router.get(...)`, `@router.post(...)` etc. are decorators that register
a function as the handler for a route.

**5. What is a context manager?**
An object usable in a `with` block that guarantees setup/teardown
(`__enter__`/`__exit__`). `get_db()` is a generator-based dependency that
plays the same role for request-scoped database sessions.

## FastAPI

**6. What is FastAPI?**
A modern Python web framework built on Starlette and Pydantic, offering
automatic request validation, dependency injection, and interactive API
docs (Swagger UI at `/docs`).

**7. How does FastAPI validate incoming requests?**
Through Pydantic models declared as the type hint of a route's parameter
(e.g. `payload: ComplaintCreateRequest`); FastAPI parses and validates the
JSON body against that model automatically, returning HTTP 422 on failure.

**8. What is dependency injection in FastAPI?**
Route handlers declare dependencies (like `db: Session = Depends(get_db)`
or `user: User = Depends(get_current_user)`) that FastAPI resolves and
injects automatically before the handler runs.

**9. How are role-based permissions enforced?**
Via a `require_roles(*roles)` dependency factory that checks the current
authenticated user's role and raises HTTP 403 if it isn't in the allowed
set — used on routes like staff creation or complaint assignment.

**10. Where does CORS configuration live?**
`CORSMiddleware` in `app/main.py`, configured from `CORS_ORIGINS` in
`.env`, so only approved frontend origins can call the API from a browser.

**11. How does the project expose API documentation?**
FastAPI auto-generates OpenAPI/Swagger docs at `/docs` from the route
and Pydantic model definitions — no extra documentation code needed.

## PostgreSQL / SQLAlchemy

**12. Why PostgreSQL over a NoSQL store here?**
The data is inherently relational (users, complaints, categories,
departments with foreign keys), and PostgreSQL offers strong consistency,
constraints, and mature tooling for exactly that shape of data.

**13. What is an ORM, and why use SQLAlchemy?**
An Object-Relational Mapper maps database rows to Python objects. It lets
the backend express queries in Python (`db.query(Complaint).filter(...)`)
instead of hand-written SQL, and centralizes schema definition in model
classes.

**14. How are foreign keys represented in the models?**
With `Column(Integer, ForeignKey("table.id"))`, e.g.
`Complaint.student_id` references `users.id`, paired with an SQLAlchemy
`relationship()` for convenient object navigation.

**15. What is database normalization, and is this schema normalized?**
Organizing tables to minimize redundancy. This schema is in 3rd Normal
Form: entities like category and department names are stored once and
referenced by foreign key, not duplicated on every complaint row.

**16. What are database indexes, and where are they used?**
Structures that speed up lookups on specific columns. Indexes are defined
on `users.email`, `complaints.reference_code`, `complaints.student_id`,
`complaints.assigned_staff_id`, `complaints.status`, and
`notifications.user_id` — the columns most frequently filtered/joined on.

**17. How does the project prevent SQL injection?**
By using SQLAlchemy's parameterized query API exclusively — no raw SQL
string concatenation with user input anywhere in the codebase.

**18. What is Alembic and why use it alongside SQLAlchemy?**
A migration tool that tracks incremental, reviewable schema changes as
versioned Python scripts (`backend/alembic/versions/`), rather than
dropping and recreating tables, which matters once real data exists.

**19. What's the difference between `db.commit()` and `db.flush()`?**
`flush()` sends pending changes to the database within the current
transaction (so they're queryable) without ending it; `commit()` ends the
transaction, making changes permanent.

## Authentication & Security

**20. How does JWT authentication work here?**
On login, the backend verifies the password and issues a signed JWT
(`python-jose`) containing the user's email and role with an expiry. The
frontend stores it and sends it as `Authorization: Bearer <token>` on
every request; the backend decodes and verifies it to identify the user.

**21. Why hash passwords instead of storing them in plaintext?**
If the database is ever compromised, plaintext passwords would
immediately expose every account. Hashing (bcrypt, via passlib) makes
reversing a password from its stored hash computationally infeasible.

**22. Why bcrypt specifically?**
It's a deliberately slow, salted hashing algorithm designed to resist
brute-force and rainbow-table attacks, and is industry-standard for
password storage.

**23. What is role-based access control (RBAC)?**
Restricting actions based on a user's assigned role (Student/Staff/Admin)
rather than per-user permissions — simpler to reason about and enforce
consistently via the `require_roles` dependency.

**24. How is a student prevented from viewing another student's complaint?**
The complaints router checks, on every fetch/update, that
`complaint.student_id == current_user.id` for Student-role callers (and
the equivalent assigned-staff check for Staff), raising 403 otherwise.

**25. What HTTP status codes does the API use, and why?**
400 (bad request/validation logic), 401 (not authenticated), 403 (
authenticated but not permitted), 404 (not found), 409 (conflict, e.g.
duplicate email), 413 (file too large), 422 (schema validation failure),
500 (unexpected server error) — each signaling a distinct failure mode to
the frontend.

**26. How are file uploads validated?**
By checking the declared content type against an allow-list (JPG, PNG,
PDF only) and streaming the file to disk while counting bytes, aborting
and deleting the partial file if it exceeds the configured size limit.

**27. Why is `.env` excluded from the repository/zip but `.env.example` included?**
`.env` holds real secrets (JWT signing key, DB credentials) for a given
deployment and must never be committed or shared; `.env.example`
documents the required variables without exposing any actual secret.

## REST API Design

**28. What makes this API "RESTful"?**
Resources (complaints, users, notifications) are addressed by URL, and
standard HTTP verbs express the action: GET to read, POST to create, PUT
to update. Responses use JSON and standard status codes.

**29. Why use PUT instead of PATCH for status updates?**
PUT is used here to represent a full, well-defined state transition
(assign, update-status, confirm, reopen) via dedicated endpoints rather
than freeform partial updates — simpler to validate and reason about for
a workflow with a fixed state machine.

**30. How does pagination work on the complaints list?**
`page` and `page_size` query parameters control an `OFFSET`/`LIMIT`-style
query; the response includes a `total` count so the frontend can compute
page counts.

**31. How is search implemented?**
A case-insensitive `ILIKE` match across reference code, title, location,
and the complaint's student name, combined with `OR` logic, applied only
within whatever role-based scope already applies to the requester.

## Frontend / Backend Communication

**32. How does the frontend talk to the backend?**
Via the browser's Fetch API, wrapped in a small `Api` client
(`frontend/js/api.js`) that attaches the JWT, serializes JSON bodies, and
normalizes error handling into a single `ApiError` type.

**33. Why vanilla JavaScript instead of a framework like React?**
Per the project brief, to keep the codebase approachable for a student/
client audience without a build step — the frontend is plain HTML/CSS/JS
files that run directly in a browser or simple static file server.

**34. How are role-specific pages/actions shown or hidden?**
`Session.role()` (read from the JWT payload at login time, cached in
`localStorage`) drives both navigation rendering (`layout.js`) and which
action buttons are rendered on the complaint detail page.

**35. How does the dashboard get its charts?**
Chart.js renders canvases populated with data returned live from
`/api/dashboard/{role}` — nothing is hardcoded in the frontend.

## Complaint Workflow & Business Logic

**36. What are the complaint status values and their order?**
SUBMITTED → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED, with REOPENED as
a branch from RESOLVED/CLOSED back into the active workflow.

**37. What triggers the REOPENED status?**
A student confirming via `PUT /api/complaints/{id}/reopen` on a complaint
currently RESOLVED or CLOSED, when they find the issue still isn't fixed.

**38. How is SLA/due date calculated?**
`calculate_due_date()` adds a priority-based number of hours (Critical:
24h, High: 3 days, Medium: 5 days, Low: 7 days) to the complaint's
creation time, stored as `due_at`.

**39. How is "overdue" determined?**
`is_overdue()` compares `datetime.utcnow()` against `due_at`, returning
False automatically once a complaint is RESOLVED or CLOSED (a fixed issue
isn't "overdue" even past its original deadline).

**40. Why record every status change in `complaint_history` instead of
just updating the `status` column?**
To preserve a full audit trail — who changed what, when, and why (via the
optional note) — which the status column alone can't retain once
overwritten.

**41. How are notifications generated?**
A small `notify()` service function is called at each workflow event
(submission, assignment, status change, comment, confirmation, reopen),
inserting a `Notification` row for the relevant user(s).

**42. Why are dashboard statistics computed on every request rather than
cached?**
To guarantee the numbers always reflect the current database state — no
stale cached dashboard that disagrees with the underlying complaint list,
at the cost of recomputing aggregates per request (acceptable at this
scale).

## Testing

**43. What testing approach does the backend use?**
`pytest` with FastAPI's `TestClient`, overriding the `get_db` dependency
to point at an isolated in-memory SQLite database so tests never touch
real data.

**44. Why an in-memory database for tests instead of the real one?**
Tests should be fast, repeatable, and side-effect-free; an in-memory
SQLite database is created fresh, used, and discarded per test run.

**45. Give an example of an authorization test in this project.**
`test_student_cannot_access_others_complaint` registers two students,
has one create a complaint, and asserts the other receives HTTP 403 when
fetching it.

## Deployment

**46. What does the Dockerfile do?**
Builds a Python 3.12 image, installs backend dependencies from
`requirements.txt`, copies the backend source, and runs it with Uvicorn
on port 8000.

**47. What services does `docker-compose.yml` define?**
`db` (PostgreSQL 15), `backend` (the FastAPI app, depending on `db`
being healthy), and `frontend` (an nginx container serving the static
frontend files).

**48. How would you deploy this to a real server?**
Run `docker compose up --build -d` on the server, point DNS at it,
terminate TLS with a reverse proxy (e.g. nginx or Caddy) in front of
ports 8000/80, and set strong, unique values for `JWT_SECRET_KEY` and
database credentials in the environment — never the development defaults.

**49. How do you back up the database?**
`pg_dump` for PostgreSQL (see `docs/CLIENT_SETUP.md` for exact commands);
for the SQLite fallback, copying the `.db` file is sufficient.

**50. What would you change before a production launch?**
Rotate `JWT_SECRET_KEY` to a long random value, remove/change the demo
accounts, switch to PostgreSQL, serve the frontend over HTTPS behind a
reverse proxy, restrict `CORS_ORIGINS` to the real domain, and move file
uploads to durable storage with backups.
