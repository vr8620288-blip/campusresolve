# API Documentation

The authoritative, always-current API reference is the interactive Swagger
UI served by the backend itself at:

```
http://localhost:8000/docs
```

(and the raw OpenAPI schema at `http://localhost:8000/openapi.json`). This
file summarizes the endpoints for quick reference.

All endpoints except `/api/auth/register`, `/api/auth/login` and
`/api/health` require a `Authorization: Bearer <token>` header, obtained
from login/register.

## Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a new student account |
| POST | `/api/auth/login` | Log in, returns a JWT |
| GET  | `/api/auth/me` | Current user's profile |

## Users

| Method | Path | Description |
|---|---|---|
| GET | `/api/users/me` | Get my profile |
| PUT | `/api/users/me` | Update my profile |
| PUT | `/api/users/me/password` | Change my password |
| GET | `/api/users?role=` | (Admin) list users, optional role filter |
| POST | `/api/users/staff` | (Admin) create a staff account |
| PUT | `/api/users/{id}/deactivate` | (Admin) deactivate a user |
| PUT | `/api/users/{id}/activate` | (Admin) reactivate a user |

## Categories & Departments

| Method | Path | Description |
|---|---|---|
| GET | `/api/categories` | List complaint categories |
| POST | `/api/categories` | (Admin) add a category |
| PUT | `/api/categories/{id}/deactivate` | (Admin) deactivate a category |
| GET | `/api/departments` | List departments |
| POST | `/api/departments` | (Admin) add a department |
| PUT | `/api/departments/{id}/deactivate` | (Admin) deactivate a department |
| GET | `/api/staff` | List active staff (for assignment dropdowns) |

## Complaints

| Method | Path | Description |
|---|---|---|
| POST | `/api/complaints` | (Student) submit a complaint |
| GET  | `/api/complaints` | List complaints, scoped by role, with search/filter/sort/pagination |
| GET  | `/api/complaints/{id}` | Full complaint detail: history, comments, attachments |
| PUT  | `/api/complaints/{id}/assign` | (Admin) assign/reassign to a staff member |
| PUT  | `/api/complaints/{id}/status` | (Staff/Admin) change status, optionally with a resolution note |
| PUT  | `/api/complaints/{id}/confirm` | (Student) confirm a resolved complaint → closes it |
| PUT  | `/api/complaints/{id}/reopen` | (Student) reopen a resolved/closed complaint |
| POST | `/api/complaints/{id}/comments` | Add a comment |
| POST | `/api/complaints/{id}/attachments` | Upload a file (multipart/form-data, field name `file`) |

### `GET /api/complaints` query parameters

`search`, `status`, `priority`, `category_id`, `department_id`,
`assigned_staff_id`, `date_from`, `date_to`, `sort`
(`newest`\|`oldest`\|`priority`\|`updated`), `page`, `page_size`.

## Notifications

| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` | List my notifications + unread count |
| PUT | `/api/notifications/{id}/read` | Mark one as read |
| PUT | `/api/notifications/read-all` | Mark all as read |

## Dashboards

| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/student` | Student's own stats + recent complaints |
| GET | `/api/dashboard/staff` | Staff's assigned-complaint stats |
| GET | `/api/dashboard/admin` | Full org-wide stats, breakdowns and staff workload |

All dashboard numbers are computed live from the database on each request —
nothing is hardcoded.

## Error format

Errors return the standard FastAPI shape:

```json
{ "detail": "Human-readable message" }
```

with the appropriate HTTP status code (400, 401, 403, 404, 409, 413, 422, 500).
