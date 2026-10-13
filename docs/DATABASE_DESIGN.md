# Database Design

CampusResolve uses a normalized relational schema (3NF) on PostgreSQL (or
SQLite for local development). See `database/schema.sql` for the full DDL
and `backend/app/models/models.py` for the SQLAlchemy source of truth.

## Entity-Relationship Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ USERS : "has"
    DEPARTMENTS ||--o{ COMPLAINTS : "routes"
    CATEGORIES ||--o{ COMPLAINTS : "classifies"
    USERS ||--o{ COMPLAINTS : "files (student)"
    USERS ||--o{ COMPLAINTS : "resolves (staff)"
    COMPLAINTS ||--o{ COMPLAINT_HISTORY : "has"
    COMPLAINTS ||--o{ COMPLAINT_COMMENTS : "has"
    COMPLAINTS ||--o{ COMPLAINT_ATTACHMENTS : "has"
    USERS ||--o{ NOTIFICATIONS : "receives"
    COMPLAINTS ||--o{ NOTIFICATIONS : "triggers"

    USERS {
        int id PK
        string full_name
        string email UK
        string student_id UK
        string hashed_password
        enum role
        int department_id FK
        bool is_active
    }
    COMPLAINTS {
        int id PK
        string reference_code UK
        string title
        text description
        string location
        int category_id FK
        int department_id FK
        enum priority
        enum status
        int student_id FK
        int assigned_staff_id FK
        text resolution_note
        bool student_confirmed
        datetime due_at
    }
    COMPLAINT_HISTORY {
        int id PK
        int complaint_id FK
        int changed_by_id FK
        string from_status
        string to_status
        string note
    }
    COMPLAINT_COMMENTS {
        int id PK
        int complaint_id FK
        int author_id FK
        text message
    }
    COMPLAINT_ATTACHMENTS {
        int id PK
        int complaint_id FK
        int uploaded_by_id FK
        string file_name
        string stored_path
        string kind
    }
    NOTIFICATIONS {
        int id PK
        int user_id FK
        int complaint_id FK
        string title
        string message
        bool is_read
    }
    DEPARTMENTS {
        int id PK
        string name UK
    }
    CATEGORIES {
        int id PK
        string name UK
    }
```

## Normalization Notes

- **1NF**: every column holds a single atomic value; no repeating groups.
- **2NF**: all non-key attributes depend on the whole primary key (all
  tables use single-column surrogate `id` keys, so this is automatic).
- **3NF**: non-key attributes depend only on the key, not on each other —
  e.g. `department_id` is stored on `users` and `complaints` as a foreign
  key rather than duplicating the department name as a string.

## Key Design Decisions

- `complaints.reference_code` is a short, human-friendly identifier
  (e.g. `CR-2601-04821`) shown to users, separate from the internal
  auto-increment `id` used for joins.
- `complaint_history` is append-only: every status transition is recorded,
  giving a full audit trail without mutating prior rows.
- `due_at` is computed once at creation/assignment time from the SLA rules
  in `app/services/sla.py`, rather than recalculated on every request.
- Attachments store a `kind` (`evidence` vs `resolution`) so the UI can
  distinguish what the student submitted from what staff uploaded as proof
  of the fix.
