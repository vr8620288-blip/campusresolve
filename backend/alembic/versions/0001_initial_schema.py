"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

role_enum = sa.Enum("STUDENT", "STAFF", "ADMIN", name="roleenum")
priority_enum = sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="priorityenum")
status_enum = sa.Enum("SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED", "REOPENED", name="statusenum")


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("is_active", sa.Boolean, default=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("public_id", sa.String(36), unique=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False, unique=True),
        sa.Column("phone", sa.String(30)),
        sa.Column("student_id", sa.String(50), unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False, server_default="STUDENT"),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("reference_code", sa.String(20), unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
        sa.Column("priority", priority_enum, nullable=False, server_default="MEDIUM"),
        sa.Column("status", status_enum, nullable=False, server_default="SUBMITTED"),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_staff_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("resolution_note", sa.Text),
        sa.Column("student_confirmed", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("assigned_at", sa.DateTime),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("closed_at", sa.DateTime),
        sa.Column("due_at", sa.DateTime),
    )
    op.create_index("idx_complaints_reference", "complaints", ["reference_code"])
    op.create_index("idx_complaints_student", "complaints", ["student_id"])
    op.create_index("idx_complaints_staff", "complaints", ["assigned_staff_id"])
    op.create_index("idx_complaints_status", "complaints", ["status"])

    op.create_table(
        "complaint_history",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("changed_by_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("from_status", sa.String(30)),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("note", sa.String(255)),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "complaint_comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "complaint_attachments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(20), default="evidence"),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("is_read", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("complaint_attachments")
    op.drop_table("complaint_comments")
    op.drop_table("complaint_history")
    op.drop_table("complaints")
    op.drop_table("users")
    op.drop_table("categories")
    op.drop_table("departments")
    status_enum.drop(op.get_bind(), checkfirst=True)
    priority_enum.drop(op.get_bind(), checkfirst=True)
    role_enum.drop(op.get_bind(), checkfirst=True)
