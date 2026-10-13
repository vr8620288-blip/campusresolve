-- CampusResolve — PostgreSQL schema reference
--
-- This file documents the schema in plain SQL for reviewers and the
-- database design document. In normal operation the backend creates
-- these same tables automatically on first run via SQLAlchemy
-- (see backend/app/database/database.py), so you do NOT need to run
-- this file by hand unless you want to provision the schema manually
-- ahead of time.

CREATE TYPE role_enum AS ENUM ('STUDENT', 'STAFF', 'ADMIN');
CREATE TYPE priority_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE status_enum AS ENUM ('SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REOPENED');

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    public_id VARCHAR(36) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    student_id VARCHAR(50) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role role_enum NOT NULL DEFAULT 'STUDENT',
    department_id INTEGER REFERENCES departments(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    reference_code VARCHAR(20) UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(200) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    department_id INTEGER REFERENCES departments(id),
    priority priority_enum NOT NULL DEFAULT 'MEDIUM',
    status status_enum NOT NULL DEFAULT 'SUBMITTED',
    student_id INTEGER NOT NULL REFERENCES users(id),
    assigned_staff_id INTEGER REFERENCES users(id),
    resolution_note TEXT,
    student_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    assigned_at TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    due_at TIMESTAMP
);
CREATE INDEX idx_complaints_reference ON complaints(reference_code);
CREATE INDEX idx_complaints_student ON complaints(student_id);
CREATE INDEX idx_complaints_staff ON complaints(assigned_staff_id);
CREATE INDEX idx_complaints_status ON complaints(status);

CREATE TABLE complaint_history (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    changed_by_id INTEGER REFERENCES users(id),
    from_status VARCHAR(30),
    to_status VARCHAR(30) NOT NULL,
    note VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE complaint_comments (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE complaint_attachments (
    id SERIAL PRIMARY KEY,
    complaint_id INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),
    file_name VARCHAR(255) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    kind VARCHAR(20) DEFAULT 'evidence',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    complaint_id INTEGER REFERENCES complaints(id),
    title VARCHAR(200) NOT NULL,
    message VARCHAR(500) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_notifications_user ON notifications(user_id);
