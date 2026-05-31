"""create evidence table

Revision ID: 20260531_0009
Revises: 20260530_0008
Create Date: 2026-05-31 00:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260531_0009"
down_revision = "20260530_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("decision_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_decision_id", "evidence", ["decision_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_decision_id", table_name="evidence")
    op.drop_table("evidence")
