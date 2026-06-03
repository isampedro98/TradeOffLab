"""extend evidence for web research traceability

Revision ID: 20260603_0011
Revises: 20260601_0010
Create Date: 2026-06-03 12:00:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260603_0011"
down_revision: str | None = "20260601_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("evidence"):
        return

    columns = {column["name"] for column in inspector.get_columns("evidence")}
    if "source_type" not in columns:
        op.add_column(
            "evidence",
            sa.Column(
                "source_type",
                sa.String(length=50),
                nullable=False,
                server_default="manual",
            ),
        )
    if "source_url" not in columns:
        op.add_column("evidence", sa.Column("source_url", sa.String(length=2000), nullable=True))
    if "source_query" not in columns:
        op.add_column("evidence", sa.Column("source_query", sa.String(length=500), nullable=True))
    if "excerpt" not in columns:
        op.add_column("evidence", sa.Column("excerpt", sa.Text(), nullable=True))
    if "retrieved_at" not in columns:
        op.add_column(
            "evidence",
            sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "retrieval_agent" not in columns:
        op.add_column(
            "evidence",
            sa.Column("retrieval_agent", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("evidence"):
        return

    columns = {column["name"] for column in inspector.get_columns("evidence")}
    if "retrieval_agent" in columns:
        op.drop_column("evidence", "retrieval_agent")
    if "retrieved_at" in columns:
        op.drop_column("evidence", "retrieved_at")
    if "excerpt" in columns:
        op.drop_column("evidence", "excerpt")
    if "source_query" in columns:
        op.drop_column("evidence", "source_query")
    if "source_url" in columns:
        op.drop_column("evidence", "source_url")
    if "source_type" in columns:
        op.drop_column("evidence", "source_type")
